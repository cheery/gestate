//! The window — `baseview` for the frame, `softbuffer` for the pixels.
//!
//! **The only module that knows either crate exists**, and the only one
//! that knows `keyboard_types` does.  Everything above it is a pure
//! function from a document to a list of items, and from a list of
//! items to a buffer; this is where that buffer meets a window.
//!
//! It is the same shape as `gestate-panel`'s window and deliberately so
//! — one application, one way of putting pixels on a screen.  The two
//! differ in exactly one place: the panel draws the language's own
//! pictures in a 3×5 chrome font, and this draws text in a bitmap font
//! big enough to read code in.
//!
//! **Rust owns the loop.**  A keystroke never crosses a language
//! boundary: it arrives here, `keys::press` decides what it means, the
//! rope takes the edit, and the frame is redrawn — measured at sixteen
//! microseconds a keystroke and a hundred and eighteen for a frame,
//! which is why the window is never the thing that is slow.

use std::cell::{Cell, RefCell};
use std::num::NonZeroU32;
use std::time::Instant;

use baseview::{
    Event, EventStatus, MouseButton, MouseEvent, PlatformHandle,
    WindowContext, WindowHandler, WindowSettings, WindowSize,
};
use gestate_panel::list::Colour;
use gestate_panel::paint::Canvas;
use keyboard_types::{Key as Kt, KeyState, Modifiers, NamedKey};
use raw_window_handle::{
    HandleError, HasWindowHandle, RawWindowHandle, WindowHandle,
};

use crate::document::Document;
use crate::font::Font;
use crate::keys::{self, Did, Key, Memory, Mods};
use crate::view::{self, View};

/// The handle a host holds onto.  A thin wrapper, so nothing above
/// this file ever names `baseview`.
pub struct Handle(baseview::Window);

pub type Error = baseview::Error;

impl Handle {
    pub fn show(&self) -> bool {
        self.0.show().is_ok()
    }

    pub fn hide(&self) -> bool {
        self.0.hide().is_ok()
    }

    pub fn resize(&self, w: i32, h: i32) -> bool {
        self.0.resize(baseview::dpi::PhysicalSize::new(
            w.max(1) as u32, h.max(1) as u32)).is_ok()
    }

    pub fn close(self) {
        self.0.close();
    }
}

/// What the window tells whoever asked for it.
///
/// The editor cannot reach the thing that owns the file, by
/// construction — the same discipline `spec/panel.md` §"Threads" states
/// for the plugin panel: a view that cannot name the model cannot
/// corrupt it.  What crosses is *that the text changed*, and the host
/// reads it back when it wants to.
pub trait Host: Send + Sync + 'static {
    /// The text moved.  Called after the edit, on the window's thread.
    ///
    /// **The document, not its text.**  Materialising the whole file
    /// into a `String` on every keystroke is work the host may not
    /// want — `Alone` never looks at it — and at a megabyte a
    /// keystroke it is the difference between an editor and a form.
    /// The host asks for what it needs.
    fn edited(&self, _doc: &Document) {}
    /// The caret moved, as a character offset.
    fn moved(&self, _pos: usize) {}
    /// Text to open with, asked once when the window is made.
    fn initial(&self) -> String {
        String::new()
    }

    /// Text the host wants loaded, checked once a frame.
    ///
    /// **A pull rather than a push**, because the document lives on the
    /// window's thread and nothing off it may touch the rope.  The host
    /// leaves the text somewhere; the window collects it when it is
    /// next drawing anyway.
    fn incoming(&self) -> Option<String> {
        None
    }

    /// Whether the host has asked the window to shut.
    ///
    /// Checked once a frame, for the same reason: closing is the
    /// window's own to do, and a host reaching in to do it would be
    /// tearing down a surface that is possibly mid-frame.
    fn should_close(&self) -> bool {
        false
    }
}

/// A host that does nothing, for a window with no owner.
pub struct Alone(pub String);

impl Host for Alone {
    fn initial(&self) -> String {
        self.0.clone()
    }
}

pub struct ParentWindow(RawWindowHandle);

impl ParentWindow {
    /// # Safety
    /// `handle` must be a live window of the running platform's kind,
    /// valid until the editor is destroyed.
    pub unsafe fn new(handle: RawWindowHandle) -> Self {
        ParentWindow(handle)
    }
}

impl HasWindowHandle for ParentWindow {
    fn window_handle(&self) -> Result<WindowHandle<'_>, HandleError> {
        Ok(unsafe { WindowHandle::borrow_raw(self.0) })
    }
}

struct EditorWindow {
    doc: RefCell<Document>,
    view: RefCell<View>,
    /// Where on the zoom ladder this window is sitting.
    zoom: Cell<usize>,
    /// Whether the left button is down, so motion means drag-select.
    dragging: Cell<bool>,
    /// Cut and copy go here.  In-process; see `keys::Clipboard` for why
    /// the system one is somebody else's to provide.
    clip: RefCell<Memory>,
    surface: RefCell<softbuffer::Surface<PlatformHandle, PlatformHandle>>,
    /// The last cursor position — `baseview` reports it on motion only,
    /// and a press carries a button and no point.
    cursor: Cell<(i32, i32)>,
    /// The buffer, kept between frames.
    ///
    /// **Allocated once rather than per frame**: a thousand by seven
    /// hundred is nearly three megabytes, and asking the allocator for
    /// it sixty times a second is a cost with nothing to show for it.
    canvas: RefCell<Canvas>,
    /// Whether the picture is stale.  **A frame is only drawn when
    /// something happened**: an editor that redrew sixty times a second
    /// to show a document nobody was touching would be a battery
    /// costing nothing.
    dirty: Cell<bool>,
    /// Never let the picture go clean — a measuring aid, see the
    /// constructor.
    stress: bool,
    /// The size the surface was last told about, so it is not told
    /// again every frame.
    sized: Cell<(u32, u32)>,
    /// Where the time goes, when `GESTATE_EDITOR_TIME` asks.
    ///
    /// **Because "it feels slow" is not a measurement, and the parts of
    /// a frame have very different owners.**  Drawing is this crate's;
    /// presenting is the platform's — a buffer handed to X11 without
    /// shared memory is megabytes through a socket, and no amount of
    /// tuning the rasterizer would touch it.  Timing them apart is what
    /// says which.
    clock: RefCell<Timing>,
    host: std::sync::Arc<dyn Host>,
    #[allow(dead_code)]
    ctx: WindowContext,
}

#[derive(Default)]
struct Timing {
    on: bool,
    /// Frames where nothing had changed — the cost of merely being
    /// asked, which is what says whether the loop is spinning.
    idle: u64,
    drawn: u64,
    paint_us: u64,
    copy_us: u64,
    present_us: u64,
    resize_us: u64,
    last: Option<Instant>,
    /// Wall time between the last two frames the loop asked for.
    gap_us: u64,
}

impl Timing {
    fn report(&mut self) {
        let n = self.drawn.max(1);
        eprintln!("[editor] {} drawn, {} idle | paint {:.2}ms  copy {:.2}ms  \
present {:.2}ms  resize {:.2}ms | loop asks every {:.2}ms",
                  self.drawn, self.idle,
                  self.paint_us as f64 / n as f64 / 1000.0,
                  self.copy_us as f64 / n as f64 / 1000.0,
                  self.present_us as f64 / n as f64 / 1000.0,
                  self.resize_us as f64 / n as f64 / 1000.0,
                  self.gap_us as f64 / (self.drawn + self.idle).max(1) as f64
                      / 1000.0);
        *self = Timing { on: true, last: self.last, ..Default::default() };
    }
}

impl EditorWindow {
    fn font(&self) -> &'static Font {
        crate::font::LADDER[self.zoom.get()].0
    }

    fn scale(&self) -> i32 {
        crate::font::LADDER[self.zoom.get()].1
    }

    /// Step up or down the ladder, keeping the caret where it is.
    ///
    /// **The view follows afterwards**, because changing the size
    /// changes how many rows fit — zooming in on line four hundred and
    /// finding yourself at line one is the thing that makes a zoom
    /// unusable.
    fn zoom_by(&self, by: i32) -> bool {
        let n = crate::font::LADDER.len() as i32;
        let next = (self.zoom.get() as i32 + by).clamp(0, n - 1) as usize;
        if next == self.zoom.get() {
            return false;
        }
        self.zoom.set(next);
        let doc = self.doc.borrow();
        let mut v = self.view.borrow_mut();
        v.scale = self.scale();
        v.clamp(&doc, self.font());
        v.follow(&doc, self.font());
        self.dirty.set(true);
        true
    }

    fn new(ctx: WindowContext, host: std::sync::Arc<dyn Host>, w: i32, h: i32)
        -> Result<Self, softbuffer::SoftBufferError>
    {
        let handle = ctx.platform_handle();
        let context = softbuffer::Context::new(handle.clone())?;
        let surface = softbuffer::Surface::new(&context, handle)?;
        Ok(EditorWindow {
            doc: RefCell::new(Document::new(&host.initial())),
            view: RefCell::new(View {
                top: 0, left: 0, w, h, gutter: true,
                scale: crate::font::LADDER[crate::font::LADDER_DEFAULT].1,
            }),
            zoom: Cell::new(crate::font::LADDER_DEFAULT),
            dragging: Cell::new(false),
            clip: RefCell::new(Memory::default()),
            canvas: RefCell::new(Canvas::opaque(w, h, view::BG)),
            surface: RefCell::new(surface),
            cursor: Cell::new((0, 0)),
            dirty: Cell::new(true),
            // **`GESTATE_EDITOR_STRESS` never goes clean**, so every
            // frame draws and presents.  It is how the *platform's*
            // half of a frame gets measured without a hand on the
            // keyboard — an idle editor presents nothing, and the cost
            // of presenting is the number in question.
            stress: std::env::var("GESTATE_EDITOR_STRESS").is_ok(),
            sized: Cell::new((0, 0)),
            clock: RefCell::new(Timing {
                on: std::env::var("GESTATE_EDITOR_TIME").is_ok(),
                ..Default::default()
            }),
            host,
            ctx,
        })
    }

    fn after(&self, did: Did) -> EventStatus {
        if did.drew {
            self.dirty.set(true);
        }
        let doc = self.doc.borrow();
        if did.edited {
            self.host.edited(&doc);
        }
        if did.drew {
            self.host.moved(doc.pos());
        }
        EventStatus::Captured
    }
}

/// `keyboard_types` to the editor's own alphabet.
///
/// **Control characters never become `Char`.**  A `Ctrl-A` arrives as
/// `Character("a")` with a modifier, and typing an `a` into the
/// document because of it is the classic way an editor eats your file.
fn translate(k: &keyboard_types::KeyboardEvent) -> Option<Key> {
    let ctrl = k.modifiers.contains(Modifiers::CONTROL);
    match &k.key {
        Kt::Character(s) => {
            let c = s.chars().next()?;
            if ctrl {
                return match c.to_ascii_lowercase() {
                    'z' if k.modifiers.contains(Modifiers::SHIFT) => Some(Key::Redo),
                    'z' => Some(Key::Undo),
                    'y' => Some(Key::Redo),
                    'c' => Some(Key::Copy),
                    'x' => Some(Key::Cut),
                    'v' => Some(Key::Paste),
                    'a' => Some(Key::SelectAll),
                    'h' => Some(Key::Top),
                    'e' => Some(Key::Bottom),
                    _ => None,
                };
            }
            // A control code that arrived as a character is not text.
            if c.is_control() {
                return None;
            }
            Some(Key::Char(c))
        }
        Kt::Named(n) => Some(match n {
            NamedKey::Enter => Key::Enter,
            NamedKey::Tab => Key::Tab,
            NamedKey::Escape => Key::Escape,
            NamedKey::Backspace => Key::Backspace,
            NamedKey::Delete => Key::Delete,
            NamedKey::ArrowLeft => Key::Left,
            NamedKey::ArrowRight => Key::Right,
            NamedKey::ArrowUp => Key::Up,
            NamedKey::ArrowDown => Key::Down,
            NamedKey::Home => if ctrl { Key::Top } else { Key::Home },
            NamedKey::End => if ctrl { Key::Bottom } else { Key::End },
            NamedKey::PageUp => Key::PageUp,
            NamedKey::PageDown => Key::PageDown,
            // Everything else is a key the editor has no meaning for
            // — a function key, a modifier on its own — and it goes
            // back to whoever else is listening.
            _ => return None,
        }),
    }
}

impl WindowHandler for EditorWindow {
    fn on_frame(&self) -> Result<(), baseview::HandlerError> {
        if self.host.should_close() {
            self.ctx.request_close();
            return Ok(());
        }
        if let Some(text) = self.host.incoming() {
            let doc = {
                let mut doc = self.doc.borrow_mut();
                doc.set_text(&text);
                let mut v = self.view.borrow_mut();
                v.clamp(&doc, self.font());
                v.follow(&doc, self.font());
                self.dirty.set(true);
                doc.clone()
            };
            // **And say so.**  The window is the authority on what the
            // document holds, so a load is an edit like any other —
            // without this the host's own copy stays at whatever it was
            // before, and `ged_text` hands back the text the *caller*
            // replaced.  Circular-looking (the host is told what it
            // asked for) and correct: anything else would make the two
            // sides disagree the moment a load is clamped, rejected, or
            // arrives while something else is happening.
            self.host.edited(&doc);
        }
        let timing = self.clock.borrow().on;
        if timing {
            let mut c = self.clock.borrow_mut();
            let now = Instant::now();
            if let Some(was) = c.last {
                c.gap_us += now.duration_since(was).as_micros() as u64;
            }
            c.last = Some(now);
        }
        if !self.dirty.get() {
            if timing {
                let mut c = self.clock.borrow_mut();
                c.idle += 1;
                if c.idle + c.drawn >= 240 {
                    c.report();
                }
            }
            return Ok(());
        }
        self.dirty.set(self.stress);

        let view = *self.view.borrow();
        let (Some(w), Some(h)) = (NonZeroU32::new(view.w.max(1) as u32),
                                  NonZeroU32::new(view.h.max(1) as u32))
        else {
            return Ok(());
        };
        let t0 = Instant::now();
        let mut surface = self.surface.borrow_mut();
        // **Only when it actually changed.**  `resize` on some backends
        // reallocates, and asking for the same size sixty times a
        // second is three megabytes of allocator traffic for nothing.
        if self.sized.get() != (w.get(), h.get()) {
            if surface.resize(w, h).is_err() {
                return Ok(());
            }
            self.sized.set((w.get(), h.get()));
        }
        let t1 = Instant::now();
        let Ok(mut buffer) = surface.buffer_mut() else {
            return Ok(());
        };

        let font = self.font();
        let doc = self.doc.borrow();
        let mut canvas = self.canvas.borrow_mut();
        if canvas.w != view.w || canvas.h != view.h {
            *canvas = Canvas::opaque(view.w, view.h, view::BG);
        }
        view::paint(&mut canvas, &view::frame(&doc, &view, font), font,
                    self.scale());
        let t_paint = Instant::now();

        // **A memcpy, because the alpha is already there.**  The canvas
        // is `opaque`, so every write carried the top byte; this used to
        // be a second sweep of the whole screen OR-ing it in, and that
        // sweep was four milliseconds of a thirteen-millisecond frame.
        let n = buffer.len().min(canvas.px.len());
        buffer[..n].copy_from_slice(&canvas.px[..n]);
        let t2 = Instant::now();
        let _ = buffer.present();
        if timing {
            let t3 = Instant::now();
            let mut c = self.clock.borrow_mut();
            c.drawn += 1;
            c.resize_us += t1.duration_since(t0).as_micros() as u64;
            c.paint_us += t_paint.duration_since(t1).as_micros() as u64;
            c.copy_us += t2.duration_since(t_paint).as_micros() as u64;
            c.present_us += t3.duration_since(t2).as_micros() as u64;
            if c.idle + c.drawn >= 240 {
                c.report();
            }
        }
        Ok(())
    }

    fn resized(&self, size: WindowSize) -> Result<(), baseview::HandlerError> {
        let p = size.physical;
        {
            let mut v = self.view.borrow_mut();
            v.w = p.width as i32;
            v.h = p.height as i32;
        }
        let doc = self.doc.borrow();
        let mut v = self.view.borrow_mut();
        v.clamp(&doc, self.font());
        v.follow(&doc, self.font());
        self.dirty.set(true);
        Ok(())
    }

    fn on_event(&self, event: Event) -> EventStatus {
        match event {
            Event::Keyboard(k) => {
                if k.state != KeyState::Down {
                    return EventStatus::Ignored;
                }
                // **The zoom, which the editor keeps for itself.**
                // `+`/`-` step the ladder and `0` goes back to where it
                // started, which is what every application means by
                // those three and therefore the only spelling worth
                // having.
                if k.modifiers.contains(Modifiers::CONTROL) {
                    if let Kt::Character(s) = &k.key {
                        match s.as_str() {
                            "+" | "=" => { self.zoom_by(1); }
                            "-" | "_" => { self.zoom_by(-1); }
                            "0" => {
                                let home = crate::font::LADDER_DEFAULT as i32;
                                self.zoom_by(home - self.zoom.get() as i32);
                            }
                            _ => return EventStatus::Ignored,
                        }
                        return EventStatus::Captured;
                    }
                }
                let Some(key) = translate(&k) else {
                    return EventStatus::Ignored;
                };
                let mods = Mods {
                    ctrl: k.modifiers.contains(Modifiers::CONTROL),
                    shift: k.modifiers.contains(Modifiers::SHIFT),
                };
                let did = {
                    let mut doc = self.doc.borrow_mut();
                    let mut view = self.view.borrow_mut();
                    let mut clip = self.clip.borrow_mut();
                    keys::press_with(&mut doc, &mut view, self.font(), key,
                                     mods, &mut *clip)
                };
                self.after(did)
            }
            Event::Mouse(MouseEvent::CursorMoved { position, .. }) => {
                let (x, y) = (position.x as i32, position.y as i32);
                self.cursor.set((x, y));
                if !self.dragging.get() {
                    return EventStatus::Captured;
                }
                // **A drag extends from where the button went down**,
                // and keeps extending past the window's edge — which is
                // what selecting more than a screenful means.  The view
                // follows, so the text scrolls under the pointer.
                let did = {
                    let mut doc = self.doc.borrow_mut();
                    let mut view = self.view.borrow_mut();
                    let d = keys::drag(&mut doc, &view, self.font(), x, y);
                    if d.drew {
                        view.follow(&doc, self.font());
                    }
                    d
                };
                self.after(did)
            }
            Event::Mouse(MouseEvent::ButtonPressed {
                button: MouseButton::Left, modifiers, ..
            }) => {
                self.dragging.set(true);
                let (x, y) = self.cursor.get();
                let did = {
                    let mut doc = self.doc.borrow_mut();
                    let view = self.view.borrow();
                    // Shift-click extends rather than starts over, which
                    // is how a selection is adjusted without redoing it.
                    if modifiers.contains(Modifiers::SHIFT) {
                        keys::drag(&mut doc, &view, self.font(), x, y)
                    } else {
                        keys::click(&mut doc, &view, self.font(), x, y)
                    }
                };
                self.after(did)
            }
            Event::Mouse(MouseEvent::ButtonReleased {
                button: MouseButton::Left, ..
            }) => {
                self.dragging.set(false);
                EventStatus::Captured
            }
            Event::Mouse(MouseEvent::WheelScrolled { delta, modifiers }) => {
                // Three lines a notch, which is what a wheel means
                // everywhere; pixels are turned into lines rather than
                // scrolled directly, so the grid never lands half a
                // line off.
                // Ctrl and the wheel zooms, which is the other spelling
                // everybody knows.
                if modifiers.contains(Modifiers::CONTROL) {
                    let up = matches!(delta,
                        baseview::ScrollDelta::Lines { y, .. } if y > 0.0)
                        || matches!(delta,
                        baseview::ScrollDelta::Pixels { y, .. } if y > 0.0);
                    self.zoom_by(if up { 1 } else { -1 });
                    return EventStatus::Captured;
                }
                let step = self.view.borrow().ch(self.font()).max(1);
                let lines = match delta {
                    baseview::ScrollDelta::Lines { y, .. } => -(y * 3.0) as i32,
                    baseview::ScrollDelta::Pixels { y, .. } =>
                        -(y as i32) / step,
                };
                let did = {
                    let doc = self.doc.borrow();
                    let mut view = self.view.borrow_mut();
                    keys::scroll(&doc, &mut view, self.font(), lines)
                };
                self.after(did)
            }
            _ => EventStatus::Ignored,
        }
    }
}

/// Open the editor as a window of its own and run until it closes.
pub fn open_blocking(host: std::sync::Arc<dyn Host>, w: i32, h: i32)
    -> Result<(), Error>
{
    let settings = WindowSettings::new()
        .with_title("gestate")
        .with_size(baseview::dpi::PhysicalSize::new(w as u32, h as u32));
    let window = baseview::Window::create(settings, move |ctx| {
        EditorWindow::new(ctx, host, w, h)
            .map_err(|e| baseview::HandlerError::from_boxed(Box::new(e)))
    })?;
    window.run_until_closed()
}

/// Open it inside somebody else's window.
///
/// # Safety
/// `parent` must be a live platform window that outlives the handle.
pub unsafe fn open_parented(parent: RawWindowHandle,
                            host: std::sync::Arc<dyn Host>,
                            w: i32, h: i32) -> Result<Handle, Error> {
    let parent = ParentWindow::new(parent);
    let settings = WindowSettings::new()
        .with_title("gestate")
        .with_size(baseview::dpi::PhysicalSize::new(w as u32, h as u32))
        .with_parent(&parent);
    baseview::Window::create(settings, move |ctx| {
        EditorWindow::new(ctx, host, w, h)
            .map_err(|e| baseview::HandlerError::from_boxed(Box::new(e)))
    })
    .map(Handle)
}

/// The background, so a host can match it.
pub const BACKGROUND: Colour = view::BG;
