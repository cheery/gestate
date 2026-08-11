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
use crate::furniture::{Furniture, Gesture, Order};
use crate::keys::{self, Did, Key, Memory, Mods};
use crate::palette::{Asks, Palette};
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

    /// The chrome, when the model has described it since it was last
    /// asked — `(version, description)`.
    ///
    /// A pull rather than a push, for the reason `incoming` is one: the
    /// window's state belongs to the window's thread, and the model
    /// leaves things where the window will collect them.
    fn furniture(&self) -> Option<(u64, String)> {
        None
    }

    /// Something the window has to say.  Called on the window's thread.
    fn gesture(&self, _line: String) {}

    /// Things the model has asked the window to do, drained once a
    /// frame — see `furniture::Order`.
    ///
    /// A pull rather than a push, for the reason `incoming` is one.
    fn orders(&self) -> Vec<String> {
        Vec::new()
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
    /// The chrome, as the model last described it, and which version.
    chrome: RefCell<Furniture>,
    furnished: Cell<u64>,
    /// The command list — `spec/workbench.md`'s answer to modes.
    palette: RefCell<Palette>,
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
    /// When the oldest key still waiting for a repaint arrived.
    struck: Cell<Option<Instant>>,
    /// When the oldest unanswered `filter` went out to the model.
    asked: Cell<Option<Instant>>,
    /// The last `State` gesture sent, so it goes out only when it moves.
    told: Cell<(usize, usize, usize, usize)>,
    /// The knob being dragged, and the value last sent for it.
    ///
    /// **The value, so the same one is not sent twice.**  A pointer
    /// moving along a fader crosses many pixels per step of an `Int`
    /// parameter, and every repeat would be a round trip and a rebuild
    /// for a number that did not change.
    turning: RefCell<Option<(String, f64)>>,
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
    /// **Key to pixels** — from the event that changed something to the
    /// `present` that put it on screen.  The only latency a typist can
    /// actually feel, and the one number that says whether a character
    /// appears under the finger that typed it.
    strikes: u64,
    strike_us: u64,
    strike_max: u64,
    /// **Query to list** — a letter typed into the command list, out to
    /// the model that decides what it means, and back.  The window
    /// draws what it was typed at once; *this* is what can trail your
    /// hand, and it is a different number from `key->pixels` because it
    /// crosses into another runtime and comes back.
    answers: u64,
    answer_us: u64,
    answer_max: u64,
}

impl Timing {
    fn report(&mut self) {
        // **Two denominators, because there are two kinds of frame.**
        // Laying the document out and rasterising it happens only when
        // something changed; the copy and the present happen every
        // frame, because presenting is also what drains the X
        // connection.  Dividing all four by `drawn` would quietly
        // inflate the two that ran more often than that.
        let drew = self.drawn.max(1);
        let all = (self.drawn + self.idle).max(1);
        eprintln!("[editor] {} drawn, {} idle | paint {:.2}ms  copy {:.2}ms  \
present {:.2}ms  resize {:.2}ms | loop asks every {:.2}ms",
                  self.drawn, self.idle,
                  self.paint_us as f64 / drew as f64 / 1000.0,
                  self.copy_us as f64 / all as f64 / 1000.0,
                  self.present_us as f64 / all as f64 / 1000.0,
                  self.resize_us as f64 / all as f64 / 1000.0,
                  self.gap_us as f64 / all as f64 / 1000.0);
        if self.answers > 0 {
            eprintln!("[editor] query->list: {} answers, avg {:.2}ms, \
worst {:.2}ms",
                      self.answers,
                      self.answer_us as f64 / self.answers as f64 / 1000.0,
                      self.answer_max as f64 / 1000.0);
        }
        if self.strikes > 0 {
            eprintln!("[editor] key->pixels: {} strikes, avg {:.2}ms, \
worst {:.2}ms",
                      self.strikes,
                      self.strike_us as f64 / self.strikes as f64 / 1000.0,
                      self.strike_max as f64 / 1000.0);
        }
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
                top: 0, left: 0, w, h, gutter: true, aside: 0,
                scale: crate::font::LADDER[crate::font::LADDER_DEFAULT].1,
            }),
            zoom: Cell::new(crate::font::LADDER_DEFAULT),
            dragging: Cell::new(false),
            clip: RefCell::new(Memory::default()),
            chrome: RefCell::new(Furniture::default()),
            furnished: Cell::new(0),
            palette: RefCell::new(Palette::default()),
            canvas: RefCell::new(Canvas::opaque(w, h, view::BG)),
            surface: RefCell::new(surface),
            cursor: Cell::new((0, 0)),
            dirty: Cell::new(true),
            struck: Cell::new(None),
            asked: Cell::new(None),
            told: Cell::new((usize::MAX, 0, 0, 0)),
            turning: RefCell::new(None),
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

    /// Tell the model where the window's own state stands, if it moved.
    ///
    /// Called after anything that could have moved it.  Cheap when
    /// nothing did, which is why it can be called that liberally.
    fn tell(&self) {
        let doc = self.doc.borrow();
        let now = (self.zoom.get(), crate::font::LADDER.len(),
                   doc.undo_depth(), doc.redo_depth());
        if now != self.told.get() {
            self.told.set(now);
            self.host.gesture(Gesture::State {
                zoom: now.0, rungs: now.1, undos: now.2, redos: now.3,
            }.line());
        }
    }

    /// Take hold of the knob under the pointer, if there is one.
    ///
    /// Returns the gesture to send, so the caller decides whether the
    /// press was the knobs' or the text's.
    fn grab(&self, x: i32, y: i32) -> Option<String> {
        let (name, value) = {
            let view = self.view.borrow();
            let chrome = self.chrome.borrow();
            view.knob_hit(self.font(), &chrome, x, y)?
        };
        *self.turning.borrow_mut() = Some((name.clone(), value));
        Some(Gesture::Turn(name, value).line())
    }

    /// Keep turning the knob already held, from a point.
    ///
    /// **Only the value moves, never which knob** — the row under the
    /// pointer is irrelevant once a fader is held, or dragging one
    /// would rewrite its neighbours on the way past.
    fn twist(&self, x: i32, y: i32) -> Option<String> {
        let held = self.turning.borrow().clone()?;
        let (name, was) = held;
        let value = {
            let view = self.view.borrow();
            let chrome = self.chrome.borrow();
            let row = chrome.knobs.iter().position(|k| k.name == name)?;
            let k = &chrome.knobs[row];
            let (cw, _ch) = (view.cw(self.font()), 0);
            let left = view.w - view.aside as i32 * cw;
            let wide = (view.aside as i32 * cw - cw).max(1);
            let along = ((x - left) as f64 / wide as f64).clamp(0.0, 1.0);
            let _ = y;
            k.lo + along * (k.hi - k.lo)
        };
        if (value - was).abs() < f64::EPSILON {
            return None;
        }
        *self.turning.borrow_mut() = Some((name.clone(), value));
        Some(Gesture::Turn(name, value).line())
    }

    /// One thing the model asked for.
    fn obey(&self, order: Order) {
        let did = match order {
            Order::Zoom(0) => {
                let home = crate::font::LADDER_DEFAULT as i32;
                self.zoom_by(home - self.zoom.get() as i32);
                Did::nothing()
            }
            Order::Zoom(by) => {
                self.zoom_by(by);
                Did::nothing()
            }
            Order::Undo => self.rework(true),
            Order::Redo => self.rework(false),
            Order::Goto(line) => {
                let mut doc = self.doc.borrow_mut();
                let mut view = self.view.borrow_mut();
                doc.clear_anchor();
                doc.seek_rowcol(line.saturating_sub(1), 0);
                view.follow(&doc, self.font());
                Did { drew: true, edited: false }
            }
            Order::Insert(text) => {
                let mut doc = self.doc.borrow_mut();
                match doc.insert(&text) {
                    Ok(true) => Did { drew: true, edited: true },
                    _ => Did::nothing(),
                }
            }
        };
        if did.drew {
            self.dirty.set(true);
            let doc = self.doc.borrow();
            let mut v = self.view.borrow_mut();
            v.clamp(&doc, self.font());
            v.follow(&doc, self.font());
        }
        if did.edited {
            let doc = self.doc.borrow();
            self.host.edited(&doc);
            self.host.gesture(Gesture::Edited.line());
        }
        self.tell();
    }

    /// Undo or redo, and say whether anything moved.
    fn rework(&self, back: bool) -> Did {
        let moved = {
            let mut doc = self.doc.borrow_mut();
            if back { doc.undo() } else { doc.redo() }
        };
        if !moved {
            return Did::nothing();
        }
        Did { drew: true, edited: true }
    }

    fn after(&self, did: Did) -> EventStatus {
        if did.drew {
            self.dirty.set(true);
            if self.clock.borrow().on && self.struck.get().is_none() {
                self.struck.set(Some(Instant::now()));
            }
        }
        let doc = self.doc.borrow();
        if did.edited {
            self.host.edited(&doc);
            self.host.gesture(Gesture::Edited.line());
        }
        if did.drew {
            self.host.moved(doc.pos());
        }
        drop(doc);
        // Typing deepens undo, and `Ctrl -` moves the zoom; the model's
        // mirror has to hear about both or its answers go stale.
        self.tell();
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
        // The model's description, when it has changed.
        if let Some((at, text)) = self.host.furniture() {
            if at != self.furnished.get() {
                self.furnished.set(at);
                let f = Furniture::read(&text);
                self.palette.borrow_mut().offer(f.commands.clone());
                if let Some(sent) = self.asked.take() {
                    let us = Instant::now().duration_since(sent)
                        .as_micros() as u64;
                    let mut c = self.clock.borrow_mut();
                    c.answers += 1;
                    c.answer_us += us;
                    c.answer_max = c.answer_max.max(us);
                }
                // **The margin appears only when something declares a
                // knob**, so a synth with none loses no width to the
                // possibility of them.
                self.view.borrow_mut().aside =
                    if f.knobs.is_empty() { 0 } else { 10 };
                *self.chrome.borrow_mut() = f;
                self.dirty.set(true);
            }
        }
        for line in self.host.orders() {
            if let Some(order) = Order::read(&line) {
                self.obey(order);
            }
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
        // **A clean frame is still presented, and that is not waste.**
        //
        // `baseview` waits on the X connection's file descriptor to know
        // a key has arrived.  `softbuffer` was handed the *same*
        // connection, and its round trips read from that socket — which
        // moves any events waiting there into XCB's own queue, where
        // they are no longer bytes on a descriptor and no longer wake
        // the loop.  A keystroke that lands in that queue sits in it
        // until the next keystroke's bytes arrive, so the letter you see
        // is the letter before the one you typed.
        //
        // While the transport runs it is invisible: the beat changes the
        // description sixty times a second, every frame presents, and
        // every present drains the queue.  Press `stop` and the window
        // goes idle — and then the queue is only drained by typing, one
        // letter late, for as long as the file is open.  That is the bug
        // Henri could reproduce and no measurement could: the *editor*
        // was always fast, and the keystroke had not arrived yet.
        //
        // So the frame is presented either way.  What a clean frame
        // skips is the expensive half — laying out the document and
        // rasterising it, two to four milliseconds — and what it keeps
        // is the copy and the present, half a millisecond, which is the
        // price of the connection being drained on a schedule instead of
        // whenever somebody happens to type.
        let painting = self.dirty.get();
        if timing && !painting {
            let mut c = self.clock.borrow_mut();
            c.idle += 1;
        }
        // **The picture goes clean only once it has been presented**,
        // which is at the bottom of this function and not here.
        //
        // Clearing it up front looks equivalent and is not: every step
        // between here and `present` can bail out — a zero-sized
        // window, a surface that will not resize, a buffer that is not
        // available this instant — and a frame dropped after the flag
        // was cleared is a change that nothing will ever come back for.
        // The next repaint waits for the *next* thing to happen, so the
        // character you just typed appears when you type the one after
        // it.  While the transport runs that is invisible, because the
        // beat redirties the window sixty times a second and paints the
        // arrears; stop the transport and it is the only thing you can
        // see.

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
        let chrome = self.chrome.borrow();
        if painting {
            view::paint(&mut canvas,
                        &view::frame_with(&doc, &view, font, &chrome), font,
                        self.scale());
        }
        // The palette over the text, in its own frame — chrome over a
        // document, so the document's layout cannot depend on whether a
        // list happens to be open.
        let palette = self.palette.borrow();
        if painting && palette.is_open() {
            let (cw, ch) = (view.cw(font), view.ch(font));
            view::paint(&mut canvas,
                        &palette.frame(view.w, view.h, cw, ch), font,
                        self.scale());
        }
        let t_paint = Instant::now();

        // **A memcpy, because the alpha is already there.**  The canvas
        // is `opaque`, so every write carried the top byte; this used to
        // be a second sweep of the whole screen OR-ing it in, and that
        // sweep was four milliseconds of a thirteen-millisecond frame.
        let n = buffer.len().min(canvas.px.len());
        buffer[..n].copy_from_slice(&canvas.px[..n]);
        let t2 = Instant::now();
        let _ = buffer.present();
        self.dirty.set(self.stress);
        if timing {
            let t3 = Instant::now();
            let mut c = self.clock.borrow_mut();
            if let Some(hit) = self.struck.take() {
                let us = t3.duration_since(hit).as_micros() as u64;
                c.strikes += 1;
                c.strike_us += us;
                c.strike_max = c.strike_max.max(us);
            }
            if painting {
                c.drawn += 1;
            }
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
                // Ctrl-K opens the list.  One key, and the answer to
                // "what can this do" is complete by construction.
                if k.modifiers.contains(Modifiers::CONTROL) {
                    if let Kt::Character(s) = &k.key {
                        if s.eq_ignore_ascii_case("k") {
                            let asks = self.palette.borrow_mut().show();
                            if let Asks::Filter(q) = asks {
                                self.host.gesture(Gesture::Filter(q).line());
                            }
                            self.dirty.set(true);
                            return EventStatus::Captured;
                        }
                    }
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
                // **The palette sees keys first, and only while it is
                // open.**  That is the whole of its claim on the
                // keyboard: nothing is taken from the text at any other
                // time, which is what keeps "there is one mode, you are
                // typing" true.
                let asks = self.palette.borrow_mut().key(key.clone());
                if asks != Asks::Nothing || self.palette.borrow().is_open() {
                    // **The palette's keys are keys too.**  They do not
                    // go through `after`, so without this the one place
                    // a letter can visibly trail a hand is the one place
                    // the timing report could not see.
                    if self.clock.borrow().on {
                        if self.struck.get().is_none() {
                            self.struck.set(Some(Instant::now()));
                        }
                        if matches!(asks, Asks::Filter(_))
                            && self.asked.get().is_none()
                        {
                            self.asked.set(Some(Instant::now()));
                        }
                    }
                    match asks {
                        Asks::Filter(q) => self.host.gesture(
                            Gesture::Filter(q).line()),
                        // **Closing is a filter of nothing.**  The model
                        // holds which commands the last query meant, and
                        // a list that is shut has no query — without
                        // saying so, the description goes on carrying
                        // three commands out of twenty-nine for the rest
                        // of the session, and the next Ctrl-K opens onto
                        // the answer to a question nobody asked.  An
                        // empty query already means "no filter", so this
                        // needs no new verb.
                        Asks::Run(name) => {
                            self.host.gesture(Gesture::Command(name).line());
                            self.host.gesture(
                                Gesture::Filter(String::new()).line());
                        }
                        Asks::Closed => self.host.gesture(
                            Gesture::Filter(String::new()).line()),
                        Asks::Nothing => {}
                    }
                    self.dirty.set(true);
                    return EventStatus::Captured;
                }
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
                // A knob, once taken hold of, keeps the pointer even
                // when it wanders off its own row — which is what makes
                // a fader usable, and what a caret drag does too.
                if self.turning.borrow().is_some() {
                    if let Some(turn) = self.twist(x, y) {
                        self.host.gesture(turn);
                    }
                    return EventStatus::Captured;
                }
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
                let (x, y) = self.cursor.get();
                // **The margin belongs to the knobs.**  A press there is
                // a fader being taken hold of, not a caret being placed
                // — and answering to the press rather than only to the
                // drag is what makes a fader clickable at a value
                // instead of only draggable towards one.
                if let Some(turn) = self.grab(x, y) {
                    self.host.gesture(turn);
                    return EventStatus::Captured;
                }
                self.dragging.set(true);
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
                *self.turning.borrow_mut() = None;
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
