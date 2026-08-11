//! The window — `baseview` for the frame, `softbuffer` for the pixels.
//!
//! **The only module that knows either crate exists.**  Everything
//! above is pure functions from a descriptor to a display list to a
//! buffer; this is where that buffer meets a window a DAW owns.
//!
//! `baseview` gives a child window parented into an `HWND`, an `NSView`
//! or an X11 window, and events.  It draws nothing — `WindowHandler` is
//! `on_frame`/`resized`/`on_event` and no surface — so the pixels get
//! there through `softbuffer`, which takes the same raw-window-handle
//! the context already implements and presents a CPU buffer.
//!
//! One shape to note: **`WindowHandler` takes `&self`.**  baseview owns
//! the handler and calls it from the platform's event loop, so the
//! panel and the surface live behind `RefCell` and every borrow here is
//! short and non-reentrant — a frame, or one event.

use std::cell::{Cell, RefCell};
use std::num::NonZeroU32;
use std::sync::Arc;

use baseview::{
    Event, EventStatus, MouseButton, MouseEvent, PlatformHandle,
    WindowContext, WindowHandler, WindowSettings, WindowSize,
};
use raw_window_handle::{
    HandleError, HasWindowHandle, RawWindowHandle, WindowHandle,
};

use crate::model::Model;
use crate::{panels, Change, Panel};

/// The handle a host holds onto.
///
/// A thin wrapper rather than a re-export, so the shell never names
/// `baseview` — the same reason the display list is a type instead of
/// calls into the painter.  Every method here is main-thread, which is
/// what CLAP promises for `clap.gui`.
pub struct Handle(baseview::Window);

impl Handle {
    pub fn show(&self) -> bool {
        self.0.show().is_ok()
    }

    pub fn hide(&self) -> bool {
        self.0.hide().is_ok()
    }

    pub fn resize(&self, w: i32, h: i32) -> bool {
        self.0
            .resize(baseview::dpi::PhysicalSize::new(w.max(1) as u32,
                                                     h.max(1) as u32))
            .is_ok()
    }

    pub fn close(self) {
        self.0.close();
    }
}


/// Where a panel's changes go, and where its values come from.
///
/// The shell implements this over a lock-protected queue; the panel
/// never learns what is on the other side.  That is what keeps
/// `spec/panel.md` §"Threads" true by construction: a panel that cannot
/// name the engine cannot touch it.
pub trait Sink: Send + Sync + 'static {
    /// A parameter change the host must be told about.
    fn push(&self, change: Change);
    /// Values the host has reported since the last frame, if any.
    fn values(&self) -> Vec<(u32, f64)> {
        Vec::new()
    }

    /// The panel resized itself — a host that frames this window needs
    /// to be told, or the frame and the content disagree.
    fn resized(&self, _w: i32, _h: i32) {}
}

/// A parent window handle CLAP handed us, wrapped so `baseview` can
/// take it.
///
/// CLAP passes a raw platform id in a union — an X11 `Window`, an
/// `HWND`, an `NSView *` — and `baseview` wants something that
/// implements `HasWindowHandle`.  This is that adapter and nothing
/// else.
///
/// **Unsafe for one stated reason**: the handle's validity is the
/// host's promise, not something this process can check.  CLAP's
/// contract is that the parent outlives `gui.destroy`, and the shell
/// destroys the window there.
pub struct ParentWindow(RawWindowHandle);

impl ParentWindow {
    /// # Safety
    /// `handle` must be a live window of the running platform's kind,
    /// valid until the panel is destroyed.
    pub unsafe fn new(handle: RawWindowHandle) -> Self {
        ParentWindow(handle)
    }
}

impl HasWindowHandle for ParentWindow {
    fn window_handle(&self) -> Result<WindowHandle<'_>, HandleError> {
        // SAFETY: the constructor's contract.
        Ok(unsafe { WindowHandle::borrow_raw(self.0) })
    }
}

struct PanelWindow {
    panel: RefCell<Panel>,
    surface: RefCell<
        softbuffer::Surface<PlatformHandle, PlatformHandle>,
    >,
    /// The last cursor position.  baseview reports position on
    /// `CursorMoved` only — a press carries a button and modifiers and
    /// no point — so a press uses the last motion, which is what every
    /// platform actually delivers first.
    cursor: Cell<(i32, i32)>,
    sink: Arc<dyn Sink>,
    /// Kept for the platform bits the handler may need to ask about
    /// (the cursor, the scale factor) without going through baseview's
    /// own window handle.
    #[allow(dead_code)]
    ctx: WindowContext,
}

impl PanelWindow {
    fn new(ctx: WindowContext, model: Model, sink: Arc<dyn Sink>,
           w: i32, h: i32)
        -> Result<Self, softbuffer::SoftBufferError>
    {
        let handle = ctx.platform_handle();
        let context = softbuffer::Context::new(handle.clone())?;
        let surface = softbuffer::Surface::new(&context, handle)?;
        let mut panel = Panel::new(model);
        panel.resize(w, h);
        Ok(PanelWindow {
            panel: RefCell::new(panel),
            surface: RefCell::new(surface),
            cursor: Cell::new((0, 0)),
            sink,
            ctx,
        })
    }

    fn emit(&self, changes: Vec<Change>) {
        for c in changes {
            self.sink.push(c);
        }
    }
}

impl WindowHandler for PanelWindow {
    fn on_frame(&self) -> Result<(), baseview::HandlerError> {
        let values = self.sink.values();
        let mut panel = self.panel.borrow_mut();
        if !values.is_empty() {
            panel.sync_values(&values);
        }

        let (w, h) = (panel.width.max(1) as u32, panel.height.max(1) as u32);
        let (Some(nw), Some(nh)) = (NonZeroU32::new(w), NonZeroU32::new(h))
        else {
            return Ok(());
        };

        let mut surface = self.surface.borrow_mut();
        if surface.resize(nw, nh).is_err() {
            return Ok(());
        }
        let Ok(mut buffer) = surface.buffer_mut() else {
            return Ok(());
        };

        // **Through `render`, not around it.**  The scrollbar is drawn
        // over the display list rather than in it, so painting the list
        // directly here is exactly how a window ends up with no
        // scrollbar while every unit test says there is one.
        let canvas = panel.render();
        // **The alpha byte, and why it is set here.**  The painter's
        // words are `0x00RRGGBB` — `gui.ges`'s `Colour` is three
        // components and the substrate has no transparency — but an X11
        // window on a compositor may hold a 32-bit visual, where a zero
        // top byte means *fully transparent* and the panel comes out
        // see-through.  Opacity is the platform's requirement, not the
        // display list's, so it is applied on the way to the surface
        // and the canvas keeps meaning what `gui.py` means.
        let n = buffer.len().min(canvas.px.len());
        for (dst, src) in buffer[..n].iter_mut().zip(&canvas.px[..n]) {
            *dst = *src | 0xFF00_0000;
        }
        let _ = buffer.present();
        Ok(())
    }

    fn resized(&self, size: WindowSize) -> Result<(), baseview::HandlerError> {
        let p = size.physical;
        self.panel.borrow_mut().resize(p.width as i32, p.height as i32);
        Ok(())
    }

    fn on_event(&self, event: Event) -> EventStatus {
        match event {
            Event::Mouse(MouseEvent::CursorMoved { position, .. }) => {
                let (x, y) = (position.x as i32, position.y as i32);
                self.cursor.set((x, y));
                let changes = self.panel.borrow_mut().motion(x, y);
                self.emit(changes);
                EventStatus::Captured
            }
            Event::Mouse(MouseEvent::ButtonPressed {
                button: MouseButton::Left, ..
            }) => {
                let (x, y) = self.cursor.get();
                let changes = self.panel.borrow_mut().press(x, y);
                self.emit(changes);
                EventStatus::Captured
            }
            Event::Mouse(MouseEvent::ButtonReleased {
                button: MouseButton::Left, ..
            }) => {
                let changes = self.panel.borrow_mut().release();
                self.emit(changes);
                EventStatus::Captured
            }
            Event::Mouse(MouseEvent::WheelScrolled { delta, .. }) => {
                // Lines and pixels both arrive here depending on the
                // platform; a line is worth about three text rows,
                // which is the pace a list this dense reads at.
                let dy = match delta {
                    baseview::ScrollDelta::Lines { y, .. } => -y * 30.0,
                    baseview::ScrollDelta::Pixels { y, .. } => -y,
                };
                self.panel.borrow_mut().scroll_by(dy as i32);
                EventStatus::Captured
            }
            // **Keyboard events are passed back deliberately.**  A DAW
            // lets you play the piano keys while a plugin window has
            // focus, and a panel that captured them would take the
            // instrument's own keyboard away.
            _ => EventStatus::Ignored,
        }
    }
}

/// Open the panel as a child of a host window.
///
/// # Safety
/// `parent` must be a live platform window that outlives the returned
/// `Window` — CLAP's `gui.set_parent` contract.
pub unsafe fn open_parented(
    parent: RawWindowHandle,
    model: Model,
    sink: Arc<dyn Sink>,
    size: Option<(i32, i32)>,
) -> Result<Handle, baseview::Error> {
    let (w, h) = size.unwrap_or_else(
        || panels::size(&model, panels::SCALE_DEFAULT));
    let parent = ParentWindow::new(parent);
    let settings = WindowSettings::new()
        .with_title("gestate")
        .with_size(baseview::dpi::PhysicalSize::new(w as u32, h as u32))
        .with_parent(&parent);
    baseview::Window::create(settings, move |ctx| {
        PanelWindow::new(ctx, model, sink, w, h)
            .map_err(|e| baseview::HandlerError::from_boxed(Box::new(e)))
    })
    .map(Handle)
}

/// Open the panel as its own window and run until it closes — the
/// standalone view, for looking at a panel without a DAW.
pub fn open_blocking(model: Model, sink: Arc<dyn Sink>)
    -> Result<(), baseview::Error>
{
    let (w, h) = panels::size(&model, panels::SCALE_DEFAULT);
    let settings = WindowSettings::new()
        .with_title("gestate panel")
        .with_size(baseview::dpi::PhysicalSize::new(w as u32, h as u32));
    let window = baseview::Window::create(settings, move |ctx| {
        PanelWindow::new(ctx, model, sink, w, h)
            .map_err(|e| baseview::HandlerError::from_boxed(Box::new(e)))
    })?;
    window.run_until_closed()
}
