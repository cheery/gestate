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
use gestate_panel::list::{Colour, Item};
use gestate_panel::paint::Canvas;
use keyboard_types::{Key as Kt, KeyState, Modifiers, NamedKey};
use raw_window_handle::{
    HandleError, HasWindowHandle, RawWindowHandle, WindowHandle,
};

use crate::document::Document;
use crate::font::Font;
use crate::furniture::{Furniture, Gesture, Order};
use crate::keys::{self, Clipboard, Did, Key, Memory, Mods};
use crate::palette::{Asks, Entry, Palette};
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

    /// Text the host wants loaded, checked once a frame — `(text,
    /// fresh)`, where `fresh` means the histories go too: a file
    /// switch, rather than a replacement that stays one undo away.
    ///
    /// **A pull rather than a push**, because the document lives on the
    /// window's thread and nothing off it may touch the rope.  The host
    /// leaves the text somewhere; the window collects it when it is
    /// next drawing anyway.
    fn incoming(&self) -> Option<(String, bool, bool)> {
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

    /// The canvas, when the model has redrawn it since it was last
    /// asked — `(version, shapes)`.
    fn picture(&self) -> Option<(u64, String)> {
        None
    }

    /// A canvas to walk for ourselves, when the model has handed one
    /// since it was last asked — `(version, payload)`, the payload
    /// being `spec/workbench.md` §"The canvas walks over crust"'s:
    /// entry, tags, channels, then the serialized program.  Empty
    /// means nothing to walk.  A pull, for the reason `picture` is
    /// one — and rarer: it moves on rebuild, never on keystrokes.
    fn walk(&self) -> Option<(u64, String)> {
        None
    }

    /// The instrument's facts for the walked canvas, when the model
    /// has read them since this was last asked — `(version, reading
    /// lines)`.  The other direction from `touched`, and together the
    /// whole of what still crosses per frame once the window walks.
    fn readings(&self) -> Option<(u64, String)> {
        None
    }

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
    /// Whether the left button went down on the canvas, so motion means
    /// a hand moving on the picture rather than a selection growing.
    /// The press grabs — the model's substrate holds the element, this
    /// only remembers that a touch is in progress — so the drag follows
    /// even when the pointer leaves the element, which is what a fader
    /// is.
    touching: Cell<bool>,
    /// Where the canvas *box*'s grab was taken: the band's inner
    /// origin at press time, subtracted from every drag so the walk
    /// hears the coordinates it drew in.  `None` for a grab taken in
    /// the full canvas view, whose walk draws in window coordinates.
    box_grab: RefCell<Option<(String, i32, i32)>>,
    /// The canvas this window walks for itself, when the model has
    /// handed one — `spec/workbench.md` §"The canvas walks over
    /// crust".  Empty, the shapes the model sends draw exactly as
    /// before the door existed.
    /// One walker per canvas the model handed over, keyed as the
    /// payload's `box` sections are (B2, multiple canvas):
    /// `substrate` for the file's own picture, `__canvas_<k>__` for
    /// an expression ask's.  The canvas *view* walks `substrate`;
    /// each content box walks its key.
    walkers: RefCell<std::collections::HashMap<String,
                                               crate::walk::Walker>>,
    /// The payload version the walkers were built from.
    walking: Cell<u64>,
    /// The readings version last fed to it.
    heard: Cell<u64>,
    /// The newest trace per scope label, for the boxes beside their
    /// declarations — kept by the window because traces arrive at the
    /// reading cadence and the boxes draw at the frame's
    /// (`spec/scope.md`).
    traces: RefCell<std::collections::HashMap<String, Vec<f64>>>,
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
    told: Cell<(usize, usize, usize, usize, usize, usize, usize, bool, bool)>,
    /// The note the pointer is holding down, if any.
    playing: Cell<Option<i32>>,
    /// Whether the canvas is what the window is showing.
    ///
    /// **A view, not a mode.**  The text is still there and still
    /// yours; this is which of the two the window is pointed at, the
    /// way a second tab in the plugin panel is.
    on_canvas: Cell<bool>,
    /// The canvas, as the model last drew it, and which version.
    picture: RefCell<Vec<gestate_panel::list::Item>>,
    drawn: Cell<u64>,
    /// **Whether the keyboard is the piano's.**
    ///
    /// `spec/commands.md` settled this when the piano was still an
    /// idea: *"the letters go on typing, so this is a setting on the
    /// input road rather than a mode of the editor, and where the
    /// keyboard goes is **focus**: click the drawn piano and it has it,
    /// click the text and the text does."*  A focus is not a mode
    /// because it is visible and you point at it.
    at_piano: Cell<bool>,
    /// Which physical keys the piano is holding, so they can be let go
    /// when it loses the keyboard — a note held while you click away is
    /// held for ever otherwise.
    fingers: RefCell<std::collections::HashSet<String>>,
    /// Whether the list was open last frame — the edge that decides
    /// the panel's half: the equator rule runs at the opening, not per
    /// keystroke, so the panel does not dance under a typing hand.
    was_open: Cell<bool>,
    /// A warning being shown: the words, when they arrived, and
    /// whether the list was up when they did.  One said into the list
    /// stays **as long as the user is there** — until the list closes
    /// — because a warning that fades while its question is still open
    /// is a warning that expects to be read on a deadline; one said
    /// with no list up keeps a short fade.  The window's clock either
    /// way, because frames are the window's and the model has none.
    warned: RefCell<Option<(String, Instant, bool)>>,
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
        // A zoom changes the bar's columns, so it re-grants like a
        // resize does.
        v.grant(&self.chrome.borrow(), self.font());
        v.clamp(&doc, self.font());
        v.follow(&doc, self.font());
        self.dirty.set(true);
        true
    }

    fn new(ctx: WindowContext, host: std::sync::Arc<dyn Host>, w: i32, h: i32)
        -> Result<Self, softbuffer::SoftBufferError>
    {
        // See `detectable_autorepeat`: without this, a held piano key
        // retriggers on every autorepeat, because the server's default
        // is to fake a release before each repeated press.
        //
        // **Asked of the `WindowContext`, not the platform handle.**
        // baseview answers this question twice on X11 and differently:
        // the context's display handle is the Xlib `Display*` and the
        // platform handle's is the XCB connection.  The first draft
        // asked the platform handle, matched on `Xlib`, and the arm
        // silently never fired — the piano machine-gunned with the fix
        // "in".
        #[cfg(target_os = "linux")]
        {
            // The clock floor, claimed on the thread that will paint
            // every frame — see `clock_floor`.  Half the scale asks
            // for roughly the clock a busy thread earns by burning
            // for it.
            let floored = clock_floor::claim(512);
            if std::env::var_os("GESTATE_EDITOR_TIME").is_some() {
                eprintln!("[editor] clock floor: {}",
                          if floored { "claimed (uclamp_min 512)" }
                          else { "refused — kernel or limit said no" });
            }
            use raw_window_handle::{HasDisplayHandle, RawDisplayHandle,
                                    RawWindowHandle};
            let said = match ctx.display_handle().map(|d| d.as_raw()) {
                Ok(RawDisplayHandle::Xlib(x)) => match x.display {
                    Some(d) => {
                        // The icon rides the same display: the window
                        // id is in the window handle, and a taskbar
                        // reads `_NET_WM_ICON` off the pair.
                        if let Ok(wh) = ctx.window_handle() {
                            if let RawWindowHandle::Xlib(w) = wh.as_raw() {
                                unsafe {
                                    window_icon::set(d.as_ptr(),
                                                     w.window as _);
                                }
                            }
                        }
                        if unsafe { detectable_autorepeat::enable(d.as_ptr()) }
                        {
                            "on"
                        } else {
                            "the server does not support it"
                        }
                    }
                    None => "no Xlib display in the handle",
                },
                Ok(_) => "the display handle is not Xlib",
                Err(_) => "no display handle",
            };
            if std::env::var_os("GESTATE_EDITOR_KEYS").is_some() {
                eprintln!("[keys] detectable autorepeat: {said}");
            }
        }
        let handle = ctx.platform_handle();
        let context = softbuffer::Context::new(handle.clone())?;
        let surface = softbuffer::Surface::new(&context, handle)?;
        Ok(EditorWindow {
            doc: RefCell::new(Document::new(&host.initial())),
            view: RefCell::new(View {
                top: 0, left: 0, w, h, gutter: true, aside: 0, piano: 0, focused: false,
                scale: crate::font::LADDER[crate::font::LADDER_DEFAULT].1,
                boxes: Vec::new(), foot_rows: 1,
                warning: String::new(), plus_hidden: false,
                hint: false,
            }),
            zoom: Cell::new(crate::font::LADDER_DEFAULT),
            dragging: Cell::new(false),
            touching: Cell::new(false),
            box_grab: RefCell::new(None),
            walkers: RefCell::new(std::collections::HashMap::new()),
            walking: Cell::new(0),
            heard: Cell::new(0),
            traces: RefCell::new(std::collections::HashMap::new()),
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
            told: Cell::new((usize::MAX, 0, 0, 0, 0, 0, 0, false, false)),
            turning: RefCell::new(None),
            playing: Cell::new(None),
            at_piano: Cell::new(false),
            on_canvas: Cell::new(false),
            picture: RefCell::new(Vec::new()),
            drawn: Cell::new(0),
            fingers: RefCell::new(std::collections::HashSet::new()),
            warned: RefCell::new(None),
            was_open: Cell::new(false),
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
        let (top, rows) = {
            let v = self.view.borrow();
            // Through the row table: a content box costs visible rows,
            // and the model colours exactly the lines the window shows.
            (v.top, v.slots(&doc, self.font()).len())
        };
        // Whether a selection and a clipboard exist ride along, so the
        // model can answer `copy` over nothing with "nothing selected"
        // instead of a sentence that lies — the same honesty `undo`'s
        // counts bought.
        let held = !self.clip.borrow().get().is_empty();
        let now = (self.zoom.get(), crate::font::LADDER.len(),
                   doc.undo_depth(), doc.redo_depth(),
                   doc.is_saved() as usize, top, rows,
                   doc.selection().is_some(), held);
        if now != self.told.get() {
            self.told.set(now);
            self.host.gesture(Gesture::State {
                sel: now.7, clip: now.8,
                zoom: now.0, rungs: now.1, undos: now.2, redos: now.3,
                saved: now.4 == 1, top: now.5, rows: now.6,
            }.line());
        }
    }

    /// The command this chord claims, if any advertises it.
    ///
    /// Spelled the way the model spells it — `Ctrl-S`, `Ctrl-Return`,
    /// `Ctrl-+` — because that string is what the list shows, and a
    /// second spelling would be a second table to keep in step.
    fn shortcut(&self, k: &keyboard_types::KeyboardEvent) -> Option<Entry> {
        let ctrl = k.modifiers.contains(Modifiers::CONTROL);
        let tail = match &k.key {
            Kt::Character(s) if s == " " => "Space".to_string(),
            Kt::Character(s) => s.to_uppercase(),
            Kt::Named(NamedKey::Enter) => "Return".to_string(),
            Kt::Named(NamedKey::Tab) => "Tab".to_string(),
            _ => return None,
        };
        // Every shortcut this editor has takes Control, with **one
        // exemption, and `Tab` is it.**  A bare key is text and an
        // editor that stole one would be an editor you cannot type in —
        // which is what `play` on `Space` was.  A tab is not text here:
        // the layout rule counts columns and a tab's width is the
        // *renderer's* choice, so a tab-indented file means something
        // other than it looks, and no `.ges` in the tree contains one.
        // So the key is spent on the question every other editor spends
        // it on, and `keys.rs` no longer inserts one.
        if !ctrl && tail != "Tab" {
            return None;
        }
        let chord = if ctrl { format!("Ctrl-{tail}") } else { tail };
        let chrome = self.chrome.borrow();
        chrome.commands.iter()
            .find(|e| !e.key.is_empty()
                  && e.key.eq_ignore_ascii_case(&chord))
            .cloned()
    }

    /// The arguments the box is already holding — what rides with a
    /// `wants`, so the model can rank one argument against another.
    fn given(&self) -> Vec<String> {
        self.palette.borrow().asking()
            .map(|a| a.got.clone()).unwrap_or_default()
    }

    /// Say out loud what the list just asked for.
    ///
    /// **One place**, because three things reach it now — a key, a
    /// shortcut and a click — and three copies of "which gestures does
    /// this `Asks` mean" is three chances for them to disagree about
    /// what picking a command does.
    fn speak(&self, asks: Asks) {
        match asks {
            Asks::Filter(q) => self.host.gesture(Gesture::Filter(q).line()),
            Asks::Run(name, args) => {
                self.host.gesture(Gesture::Command(name, args).line());
                // **The question outlives the run exactly as long as
                // the list does.**  `Asked` used to fire here
                // unconditionally, so the model forgot its walk the
                // moment the command ran — while the palette still
                // showed the finished call — and Return-again resolved
                // the same words from a different directory than the
                // first press (`fixme.md` F123: refused rightly, then
                // "no file" for the same pick).  Both sides now forget
                // together, when the list closes; a command that takes
                // nothing closed it already, and says so here.
                if self.palette.borrow().asking().is_none() {
                    self.host.gesture(Gesture::Asked.line());
                    self.host.gesture(Gesture::Filter(String::new()).line());
                }
            }
            // A command that takes something turns the list into a
            // question about its first argument.
            Asks::Wants(name, at, q) => {
                self.host.gesture(
                    Gesture::Wants(name, at, q, self.given()).line())
            }
            Asks::Closed => {
                self.host.gesture("shut".to_string());
                self.host.gesture(Gesture::Asked.line());
                self.host.gesture(Gesture::Filter(String::new()).line());
            }
            Asks::Nothing => {}
        }
    }

    /// A key, while the piano has the keyboard.
    ///
    /// `None` for anything that is not a letter to play — Escape hands
    /// the keyboard back, and everything else falls through to the
    /// editor, so the command list is still one Ctrl-K away.
    fn finger(&self, k: &keyboard_types::KeyboardEvent)
        -> Option<EventStatus>
    {
        if matches!(k.key, Kt::Named(NamedKey::Escape)) {
            if k.state == KeyState::Down {
                self.hands_off();
                self.at_piano.set(false);
                self.view.borrow_mut().focused = false;
                self.dirty.set(true);
            }
            return Some(EventStatus::Captured);
        }
        let Kt::Character(c) = &k.key else { return None };
        if c.chars().next().is_some_and(char::is_control) {
            return None;
        }
        let code = format!("{:?}", k.code);
        let down = k.state == KeyState::Down;
        {
            let mut held = self.fingers.borrow_mut();
            if down {
                // **Auto-repeat is not a second press.**  X11 sends a
                // stream of them while a key is held, and each one
                // would be another note on a voice that is already
                // sounding.
                if !held.insert(code.clone()) {
                    return Some(EventStatus::Captured);
                }
            } else if !held.remove(&code) {
                return Some(EventStatus::Captured);
            }
        }
        self.host.gesture(Gesture::Struck(c.clone(), code, down).line());
        Some(EventStatus::Captured)
    }

    /// Open the list — from `Ctrl-K` or from the burger.
    ///
    /// **One door**, so the key and the button cannot come to mean
    /// different things: whichever one is pressed, the same gestures
    /// cross the wire in the same order.
    fn summon_list(&self) {
        self.to_the_list();
        let asks = self.palette.borrow_mut().show();
        // **Opening it ends whatever it was asking.**  `hide` clears
        // every scrap of the last question and `show` cleared none of
        // it on the model's side — so a list reopened after walking
        // into a directory was handed that directory's rows, and
        // `open` did not start where you are.  The same asymmetry the
        // palette had internally, across the wire.
        self.host.gesture(Gesture::Asked.line());
        if let Asks::Filter(q) = asks {
            self.host.gesture(Gesture::Filter(q).line());
        }
        self.dirty.set(true);
    }

    /// The list is opening, so it takes the keyboard.
    ///
    /// **Opening it is asking to type into it.**  `Ctrl-K` reaches
    /// past the piano because it holds Control, and without this the
    /// list opened while the piano still owned every letter — so you
    /// typed a command name and played a chord.
    fn to_the_list(&self) {
        if self.at_piano.get() {
            self.hands_off();
            self.at_piano.set(false);
            self.view.borrow_mut().focused = false;
        }
    }

    /// Where the canvas origin sits, in window pixels.
    ///
    /// **One number, two directions.**  The paint adds this to every
    /// shape and the mouse handlers subtract it from every touch, so
    /// the picture and the hand cannot disagree about where an element
    /// is.  The middle of the window, because the walk is
    /// origin-relative and a bare `rect` should draw where a first
    /// program expects it.
    /// The scopes' boxes: each trace drawn under its own declaration
    /// — `spec/scope.md`'s margin half.  The band comes from the same
    /// slots walk everything else reads, so a click beside the trace
    /// lands on the line that wrote it; the points are the newest
    /// `trace` the wire carried, and a scope that has not spoken yet
    /// draws its midline rather than nothing, because an empty box
    /// reads as a layout bug and a flat line reads as silence.
    fn paint_scopes(&self, canvas: &mut gestate_panel::paint::Canvas,
                    doc: &Document, view: &View, font: &Font,
                    chrome: &crate::furniture::Furniture) {
        if chrome.scopes.is_empty() {
            return;
        }
        let slots = view.slots(doc, font);
        let traces = self.traces.borrow();
        let (cw, ch) = (view.cw(font), view.ch(font));
        // The fold (F132): a band may hang past it in the layout, but
        // nothing paints there — past it is the bar's ground.
        let tall = view.h - view.status_h(font) - view.piano;
        let gutter = view.gutter_cols(doc) as i32 * cw;
        let wide = view.text_cols(font, doc) as i32 * cw - 4;
        let mut f = view::Frame::default();
        for (label, line, flavor) in &chrome.scopes {
            let Some(slot) = slots.iter().find(|s| s.row + 1 == *line)
            else { continue };
            if slot.box_h <= 0 {
                continue;
            }
            // Scopes sharing a line split the box evenly, each band
            // its own — the second tenant used to paint its panel
            // over the first's bars.
            let mates: Vec<&String> = chrome.scopes.iter()
                .filter(|(_, l, _)| l == line)
                .map(|(n, _, _)| n)
                .collect();
            let n_mates = mates.len().max(1) as i32;
            let k = mates.iter().position(|n| *n == label)
                .unwrap_or(0) as i32;
            let band = slot.box_h / n_mates;
            let top = slot.y + ch + k * band;
            if top >= tall {
                continue;
            }
            let high = (band - 2).min(tall - top - 1);
            if high <= 2 {
                continue;
            }
            f.items.push(view::Item::Rect {
                x: gutter + 2, y: top, w: wide, h: high,
                c: view::CHROME });
            let mid = top + high / 2;
            match traces.get(label) {
                Some(points) if !points.is_empty()
                    && flavor == "spectro" =>
                {
                    // Bars from the floor, in the sound's green: a
                    // spectrum is magnitudes, and a magnitude grows
                    // up the way a meter does.
                    let n = points.len() as i32;
                    let bar = ((wide - 4) / n.max(1)).max(2);
                    for (i, p) in points.iter().enumerate() {
                        let x = gutter + 2
                            + (i as i32) * (wide - 4) / n.max(1);
                        let v = p.clamp(0.0, 1.0);
                        let h = (v * ((high - 4) as f64)) as i32;
                        if h > 0 {
                            f.items.push(view::Item::Rect {
                                x, y: top + high - 2 - h,
                                w: bar - 1, h, c: view::LIVE });
                        }
                    }
                }
                Some(points) if !points.is_empty() => {
                    let n = points.len() as i32;
                    for (i, p) in points.iter().enumerate() {
                        let x = gutter + 2
                            + (i as i32) * (wide - 4) / n.max(1);
                        let v = p.clamp(-1.0, 1.0);
                        let y = mid
                            - (v * ((high / 2 - 2) as f64)) as i32;
                        f.items.push(view::Item::Rect {
                            x, y: y - 1, w: 2, h: 2, c: view::CARET });
                    }
                }
                _ => f.items.push(view::Item::Rect {
                    x: gutter + 2, y: mid, w: wide, h: 1,
                    c: view::FAINT }),
            }
            f.items.push(view::Item::Run {
                x: gutter + 6, y: top + 2, s: label.clone(),
                c: view::FAINT });
        }
        view::paint(canvas, &f, font, self.scale());
    }

    /// The walked canvas as a content box (B2) — the picture under
    /// the `substrate` declaration, still animating, clipped by the
    /// band's own edges.
    ///
    /// **The same walk the full view animates**, handed the band's
    /// centre instead of the window's: painted into a band-sized
    /// canvas and blitted, so the clip is stated once by the band's
    /// bounds — the fold (F132) and the window edge included.
    /// Answers whether it drew a live band, which keeps the frame
    /// pump honest: a box scrolled off screen stops asking for
    /// frames, and the walk goes still the way an unshown canvas
    /// does.
    /// Where a canvas box's *inner* band sits — the inset the walk
    /// draws in — as `(x, y, w, visible_h, full_h)`, or `None` while
    /// that box is not on screen.  One function, read by the painter
    /// and by the press, because layout arithmetic shared by drawing
    /// and hit-testing is the rule this window keeps everywhere else.
    ///
    /// **Two heights, deliberately.**  The walk is laid out in
    /// `full_h` — the box's granted room — and the fold only crops
    /// what is *blitted* (`visible_h`).  Centring the walk in the
    /// visible remainder instead moved the whole picture up as the
    /// fold ate the band: Henri watched chopin's disc slide off its
    /// place while scrolling.
    fn canvas_box_rect(&self, doc: &Document, view: &View, font: &Font,
                       chrome: &crate::furniture::Furniture, line: usize)
                       -> Option<(i32, i32, i32, i32, i32)> {
        // A scope sharing the ask's line owns the box — the cap
        // already squeezed the two grants together, and the full
        // view is one word away.
        if chrome.scopes.iter().any(|(_, l, _)| *l == line) {
            return None;
        }
        let slots = view.slots(doc, font);
        let slot = slots.iter().find(|s| s.row + 1 == line)?;
        if slot.box_h <= 0 {
            return None;
        }
        let ch = view.ch(font);
        let tall = view.h - view.status_h(font) - view.piano;
        let top = slot.y + ch;
        if top >= tall {
            return None;
        }
        let full = slot.box_h - 2;
        let high = full.min(tall - top - 1);
        if high <= 2 {
            return None;
        }
        // **The picture gets air** — Henri's sad_lantern.png: a walk
        // designed for a pane, cut flush against the text above and
        // below, read as damage.  The band paints its own ground and
        // the walk lives in an inset, so whatever the crop takes, the
        // edge it takes it at is visibly the box's and not the text's.
        // The scopes stay flush: a trace draws *itself* inside its
        // panel, a walk cannot know it is in one.
        //
        // **The full band's width, not the text area's.**  The view
        // grounds a box band from the window's own left edge — "a
        // complaint is not code" — and a picture centred in the text
        // area sat visibly off the centre of the band the eye
        // actually sees (Henri: "the boundaries of the canvas is
        // off").  A picture is not code either.
        let pad = (ch / 2).max(4);
        let (iw, fh) = (view.w - 2 * pad, full - 2 * pad);
        let vh = fh.min(high - pad);
        if iw <= 2 || vh <= 2 {
            return None;
        }
        Some((pad, top + pad, iw, vh, fh))
    }

    fn paint_canvas_boxes(&self, canvas: &mut gestate_panel::paint::Canvas,
                          doc: &Document, view: &View, font: &Font,
                          chrome: &crate::furniture::Furniture) -> bool {
        let mut live = false;
        let mut walkers = self.walkers.borrow_mut();
        for (line, key) in &chrome.canvases {
            let Some((ix, iy, iw, vh, fh)) =
                self.canvas_box_rect(doc, view, font, chrome, *line)
            else { continue };
            let Some(w) = walkers.get_mut(key) else { continue };
            let pad = (view.ch(font) / 2).max(4);
            let mut band = gestate_panel::paint::Canvas::opaque(
                iw, fh, view::CHROME);
            gestate_panel::paint::paint(&mut band,
                                        w.frame(iw / 2, fh / 2));
            canvas.fill_rect(ix - pad, iy - pad,
                             iw + 2 * pad,
                             vh + pad + (vh == fh) as i32 * pad,
                             view::CHROME);
            for yy in 0..vh {
                for xx in 0..iw {
                    if let Some(px) = band.get(xx, yy) {
                        canvas.put(ix + xx, iy + yy, px);
                    }
                }
            }
            live = true;
        }
        live
    }

    fn canvas_centre(&self) -> (i32, i32) {
        let view = self.view.borrow();
        (view.w / 2, view.h / 2)
    }

    /// Let go of every key the piano is holding.
    ///
    /// **Called whenever it loses the keyboard.**  A note held while
    /// you click away is held for ever: the release goes wherever the
    /// focus went, and the voice is never handed back.
    fn hands_off(&self) {
        for code in self.fingers.borrow_mut().drain() {
            self.host.gesture(
                Gesture::Struck(String::new(), code, false).line());
        }
    }

    /// The note under the pointer, if the keyboard is showing.
    fn struck_key(&self, x: i32, y: i32) -> Option<i32> {
        let view = self.view.borrow();
        let chrome = self.chrome.borrow();
        // **The octave the model is on**, so the drawn keys and
        // `octave` agree; `+ 1` because MIDI's octave four starts at
        // sixty, which is what the keyboard calls middle C.
        let base = (chrome.octave + 1) * 12;
        view.key_at(self.font(), base, x, y)
    }

    /// Turn a bank's listening on or off, if its box was pressed.
    fn tick(&self, x: i32, y: i32) -> Option<String> {
        let (name, listening) = {
            let view = self.view.borrow();
            let chrome = self.chrome.borrow();
            view.bank_hit(self.font(), &chrome, x, y)?
        };
        let verb = if listening { "deafen" } else { "listen" };
        Some(Gesture::Command(verb.into(), vec![name]).line())
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

    /// Take the text the model sent, if it sent any.
    ///
    /// Its own step so that it can happen *before* the orders — see
    /// the call site.  Everything else about it is unchanged.
    fn take_text(&self) {
        let Some((text, fresh, written)) = self.host.incoming() else {
            return;
        };
        let doc = {
            let mut doc = self.doc.borrow_mut();
            if fresh {
                // A file switch: the histories go with the text —
                // undo must not resurrect the old file under the
                // new file's name (fixme.md F113).  A warning still
                // up was about the *old* document, and dies with it.
                doc.load_written(&text, written);
                *self.warned.borrow_mut() = None;
            } else {
                doc.set_text(&text);
            }
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

    /// One thing the model asked for.
    fn obey(&self, order: Order) {
        // An ordered insert's span — `(first row, last row)` of what it
        // put in — for the placement rule below.
        let mut span: Option<(usize, usize)> = None;
        // Whether this order moved the caret without writing anything
        // — a jump, which the placement rule below answers to.
        let mut jumped = false;
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
            Order::Col(col) => {
                jumped = true;
                let mut doc = self.doc.borrow_mut();
                let mut view = self.view.borrow_mut();
                let (row, _) = doc.cursor();
                doc.clear_anchor();
                doc.seek_rowcol(row, col);
                view.reveal(&doc, self.font());
                Did { drew: true, edited: false }
            }
            Order::Goto(line) => {
                jumped = true;
                let mut doc = self.doc.borrow_mut();
                let mut view = self.view.borrow_mut();
                doc.clear_anchor();
                doc.seek_rowcol(line.saturating_sub(1), 0);
                // A jump reveals, a keystroke follows: the target
                // lands with air past it, not pinned at the fold.
                view.reveal(&doc, self.font());
                Did { drew: true, edited: false }
            }
            Order::Show(what) => {
                let want = what == "canvas";
                if self.on_canvas.get() != want {
                    self.on_canvas.set(want);
                    self.dirty.set(true);
                }
                Did::nothing()
            }
            Order::Saved => {
                self.doc.borrow_mut().mark_saved();
                Did::nothing()
            }
            Order::Warn(text) => {
                let at_list = self.palette.borrow().is_open();
                *self.warned.borrow_mut() =
                    Some((text, Instant::now(), at_list));
                self.dirty.set(true);
                Did::nothing()
            }
            Order::Close => {
                if self.palette.borrow().is_open() {
                    let asks = self.palette.borrow_mut().hide();
                    self.speak(asks);
                    self.dirty.set(true);
                }
                Did::nothing()
            }
            Order::Fill(text) => {
                let asks = self.palette.borrow_mut().fill(&text);
                if let Asks::Wants(name, at, q) = asks {
                    // Say it back, so the model's choices are about what
                    // the box now holds — the same round trip a typed
                    // letter makes, which is what keeps one path.
                    self.host.gesture(
                    Gesture::Wants(name, at, q, self.given()).line());
                    self.dirty.set(true);
                }
                Did::nothing()
            }
            Order::Ask(verb, args) => {
                // **Looked up in the table the shortcuts read**, so a
                // command the list never advertised cannot be asked
                // for — the vocabulary rule, from the model's side.
                let found = self.chrome.borrow().commands.iter()
                    .find(|e| e.name == verb).cloned();
                if let Some(e) = found {
                    let asks = self.palette.borrow_mut().ask(&e, args);
                    self.to_the_list();
                    self.speak(asks);
                    self.dirty.set(true);
                }
                Did::nothing()
            }
            Order::Insert(text) => {
                let mut doc = self.doc.borrow_mut();
                let grew = text.matches('\n').count();
                match doc.insert(&text) {
                    Ok(true) => {
                        // The caret ends after what was inserted, so
                        // the span reaches back over the newlines.
                        let (end, _) = doc.cursor();
                        span = Some((end.saturating_sub(grew), end));
                        Did { drew: true, edited: true }
                    }
                    _ => Did::nothing(),
                }
            }
            // **The same door the chords use.**  A `copy` command and a
            // `Ctrl-C` must be one act — two implementations of "what
            // copying means" is how they come to mean different things,
            // which is the rule the bank boxes already keep.
            Order::Copy | Order::Cut | Order::Paste => {
                let key = match order {
                    Order::Copy => Key::Copy,
                    Order::Cut => Key::Cut,
                    _ => Key::Paste,
                };
                let mut doc = self.doc.borrow_mut();
                let mut view = self.view.borrow_mut();
                let mut clip = self.clip.borrow_mut();
                keys::press_with(&mut doc, &mut view, self.font(), key,
                                 Mods { ctrl: false, shift: false },
                                 &mut *clip)
            }
        };
        if did.drew {
            self.dirty.set(true);
            // **The span decides the scroll, and the panel takes the
            // other half** (F121, the rule is Henri's).  An ordered
            // insert pasted above the equator sends the panel low and
            // puts the span's *first* line on the screen's first row;
            // one pasted below keeps the panel high and puts the
            // span's *last* line on the screen's last row — either
            // way the person reads what the command just did, on the
            // half the panel is not.  Everything else drawn by an
            // order keeps the ordinary follow, past the panel's
            // shadow so a caret is never parked behind the list.
            let font = self.font();
            let list_open = self.palette.borrow().is_open();
            let doc = self.doc.borrow();
            let mut v = self.view.borrow_mut();
            v.clamp(&doc, font);
            match span {
                Some((start, end)) if list_open => {
                    let above = self.palette.borrow_mut()
                        .place(start, v.top, v.rows(font));
                    if above {
                        v.top = start;
                    } else {
                        v.top = v.top_showing(font, end);
                    }
                    v.clamp(&doc, font);
                }
                _ => {
                    // **A jump moves the panel, the same way an insert
                    // does** — F121's rule is about the caret and the
                    // equator, and `goto` crosses the equator as
                    // surely as a paste does.  Decided at the opening
                    // and never per keystroke (see the frame), but a
                    // caret the *model* moved is not a keystroke: the
                    // panel had picked its half against where you used
                    // to be, and staying there is how it ends up
                    // sitting on the line it just sent you to.  The
                    // panel moves so the text does not have to.
                    if jumped && list_open {
                        let (row, _) = doc.cursor();
                        self.palette.borrow_mut()
                            .place(row, v.top, v.rows(font));
                    }
                    let clear = {
                        let p = self.palette.borrow();
                        p.shadow_rows(v.w, v.h, v.cw(font), v.ch(font))
                    };
                    v.follow_past(&doc, font, clear);
                }
            }
        }
        if did.edited {
            let doc = self.doc.borrow();
            self.host.edited(&doc);
            self.host.gesture(Gesture::Edited.line());
        }
        if did.drew {
            // **An order moves the caret too.**  `after` reports this
            // for keys and clicks; without the same line here the
            // model's idea of where the caret is survives a `goto`
            // unchanged, and every command that reads it — anything
            // about "here" — answers about where you used to be.
            let doc = self.doc.borrow();
            self.host.moved(doc.pos());
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
                {
                    let mut pal = self.palette.borrow_mut();
                    pal.offer(f.commands.clone());
                    pal.offer_choices(f.choices.clone());
                    pal.offer_page(f.page.clone());
                }
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
                // **The margin appears when something declares a
                // knob or a bank**, so a synth with neither loses no
                // width to the possibility of them.
                self.view.borrow_mut().aside =
                    if f.knobs.is_empty() && f.banks.is_empty() {
                        0
                    } else {
                        10
                    };
                // **The content boxes get their heights here** — the
                // same moment `aside` and `piano` are set, because it
                // is the same kind of fact: furniture-derived layout,
                // owned by the view.  And the caret is followed
                // through a *reflow*, so a box appearing above you
                // cannot push the line you are typing on off screen —
                // **but only through a reflow** (`fixme.md` F119).
                // Following on every arrival made the caret an anchor
                // for the scroll: descriptions arrive whenever the
                // model has news — the transport readout, while a
                // piece plays, has news every beat — so a view wheeled
                // away from the caret snapped back to it mid-read.  A
                // scroll is not a request to be returned; only a
                // caret move, an edit or a changed layout is.
                {
                    let doc = self.doc.borrow();
                    let mut v = self.view.borrow_mut();
                    let was = (v.foot_rows, v.boxes.clone());
                    v.grant(&f, self.font());
                    v.clamp(&doc, self.font());
                    if (v.foot_rows, &v.boxes) != (was.0, &was.1) {
                        v.follow(&doc, self.font());
                    }
                }
                // **And the keyboard takes its room from the document**,
                // only while a played note would do something — so a
                // file you are reading rather than playing keeps every
                // row of it.
                // **Drawing the piano hands it the keyboard**, which is
                // what `pianoOn` means to somebody who just asked for a
                // piano; putting it away hands it back.
                if f.performing() != self.chrome.borrow().performing() {
                    self.hands_off();
                    self.at_piano.set(f.performing());
                }
                self.view.borrow_mut().focused = self.at_piano.get();
                self.view.borrow_mut().piano = if f.performing() {
                    // Three rows of keys, and one for what a played
                    // note would do — which is not guessable from a
                    // picture of a piano.
                    self.font().h * self.scale() * 4
                } else {
                    0
                };
                *self.chrome.borrow_mut() = f;
                self.dirty.set(true);
            }
        }
        if let Some((at, text)) = self.host.picture() {
            if at != self.drawn.get() {
                self.drawn.set(at);
                *self.picture.borrow_mut() = crate::shapes::read(&text);
                if self.on_canvas.get() {
                    self.dirty.set(true);
                }
            }
        }
        if let Some((at, text)) = self.host.walk() {
            if at != self.walking.get() {
                self.walking.set(at);
                // **A refusal leaves the shapes drawing.**  A payload
                // this build cannot read or a program the machine will
                // not load leaves that walker unbuilt, and the picture
                // the model sends draws exactly as before the door
                // existed — the canvas is somebody's artwork, and
                // wrong is worse than slow.  One walker per `box`
                // section; a section that refuses is dropped alone.
                *self.walkers.borrow_mut() =
                    crate::walk::Walk::read_all(&text)
                        .into_iter()
                        .filter_map(|(key, w)| {
                            crate::walk::Walker::open(&w).ok()
                                .map(|walker| (key, walker))
                        })
                        .collect();
                if self.on_canvas.get() {
                    self.dirty.set(true);
                }
            }
        }
        if let Some((at, text)) = self.host.readings() {
            if at != self.heard.get() {
                self.heard.set(at);
                // A reading is one instrument's fact, broadcast to
                // every walker — the boxes are readings of one
                // program's channels.
                let mut mine = false;
                for (name, value) in crate::walk::readings(&text) {
                    for w in self.walkers.borrow_mut().values_mut() {
                        mine |= w.hear(&name, value);
                    }
                    // The walked canvas already re-dirties per frame
                    // while it shows.
                }
                // **A box in the source view draws from readings too.**
                // The rule above was written when a reading only ever
                // fed the canvas *view* — a meter, a lamp — and it
                // stopped being true the day boxes stood in the text:
                // a meter in a band, and now a note under a hand,
                // which moves by a reading and by nothing else.  Left
                // waiting for "the next look", the picture froze the
                // moment the hand stopped moving, because a motion
                // event was the only thing still dirtying the frame.
                //
                // **Only for a reading a box actually reads.**  `peak`
                // and `position` move every frame a piece plays, and
                // dirtying on those repainted the source view
                // continuously for any file with a box in it — sixty
                // walks a second of every picture, competing with the
                // driver for a machine that is also compiling.  A
                // score box does not know `peak`; it knows the two
                // channels a hand writes, and those move only while a
                // hand is moving.
                if mine && !self.on_canvas.get() {
                    self.dirty.set(true);
                }
                let arrived = crate::walk::traces(&text);
                if !arrived.is_empty() {
                    let mut held = self.traces.borrow_mut();
                    for (name, points) in arrived {
                        for w in self.walkers.borrow_mut().values_mut() {
                            w.hear_trace(&name, points.clone());
                        }
                        held.insert(name, points);
                    }
                    // A scope's box redraws at the trace's own cadence
                    // — the source view has no other reason to.
                    if !self.on_canvas.get()
                        && !self.chrome.borrow().scopes.is_empty()
                    {
                        self.dirty.set(true);
                    }
                }
            }
        }
        // **The mirror is re-synced every poll, not only after input.**
        // `tell` used to fire only from `after` and the order path, so
        // a window nobody had touched never volunteered its state — the
        // model's mirror sat at its `0/1` initials and refused every
        // zoom in both directions at once — and a mirror corrupted by
        // anything (F110 recorded one twelve rungs up a nine-rung
        // ladder) stayed corrupted until the next keystroke happened to
        // heal it.  The `told` guard makes this free when nothing
        // moved, and it means no drift can outlive one frame.
        self.tell();
        // **The text the model sent lands before the orders that talk
        // about it.**  A command that rewrites the document and then
        // moves the caret into what it wrote — `complete` filling a
        // hole and standing on the next one — sends the text through
        // `ged_set_text` and the caret through an order, and this
        // frame is where both arrive.  Read the other way round the
        // caret is placed in the *old* document: a column past the end
        // of the line it used to be clamps back to the end of it, and
        // the new text then keeps that wrong place.  The model's own
        // order is: text first.
        self.take_text();
        for line in self.host.orders() {
            if let Some(order) = Order::read(&line) {
                self.obey(order);
            }
        }
        // **The equator decides the panel, when the list opens** —
        // `Palette::place` holds the rule, and `obey` asks it again for
        // an ordered insert or a jump.
        {
            let open = self.palette.borrow().is_open();
            if open && !self.was_open.get() {
                let (row, top, rows) = {
                    let doc = self.doc.borrow();
                    let v = self.view.borrow();
                    let (row, _) = doc.cursor();
                    (row, v.top, v.rows(self.font()))
                };
                let was = self.palette.borrow().low;
                if self.palette.borrow_mut().place(row, top, rows) != was {
                    self.dirty.set(true);
                }
            }
            self.was_open.set(open);
        }
        // **The warning's clock.**  One said into the list stays as
        // long as the list does; one said with no list up fades after
        // 2.4 seconds.  The `[+]` flashes for its first moments and
        // then holds either way — a blink that never ends is a blink
        // nobody can read past.  The frame only dirties when a fact
        // *changes*, so a held warning costs its eight blink-redraws
        // and then nothing.
        {
            let mut over = false;
            let list_open = self.palette.borrow().is_open();
            let (text, hide) = match self.warned.borrow().as_ref() {
                Some((s, since, at_list)) => {
                    let ms = since.elapsed().as_millis();
                    let gone = if *at_list { !list_open }
                               else { ms >= 2400 };
                    if gone {
                        over = true;
                        (String::new(), false)
                    } else {
                        (s.clone(), ms < 2400 && (ms / 300) % 2 == 1)
                    }
                }
                None => (String::new(), false),
            };
            if over {
                *self.warned.borrow_mut() = None;
            }
            // The words go beside the caret that is *active*: the
            // palette's query box while the list is up (its frame draws
            // them), the document's caret otherwise.  The `[+]` flash
            // is the bar's either way.
            let text = if self.palette.borrow().is_open() {
                String::new()
            } else {
                text
            };
            let mut v = self.view.borrow_mut();
            if v.warning != text || v.plus_hidden != hide {
                v.warning = text;
                v.plus_hidden = hide;
                self.dirty.set(true);
            }
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

        // The hint dies with the list, however the list went — Escape,
        // a click away, a command that closes it.  Read here rather
        // than at every door out, because every close redirties and
        // the next frame passes this way.
        if self.view.borrow().hint && !self.palette.borrow().is_open() {
            self.view.borrow_mut().hint = false;
        }
        let view = self.view.borrow().clone();
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
        // Whether a canvas box drew a live band this frame — the
        // source view's share of the walked animation (B2).
        let mut box_live = false;
        if painting {
            if self.on_canvas.get()
                && self.walkers.borrow().contains_key("substrate")
            {
                // **The window animates its own canvas** — the walk,
                // the machine and the frame clock all live here now
                // (`spec/workbench.md` §"The canvas walks over
                // crust"), so the picture moves at this window's own
                // frame rate instead of the gesture loop's, and the
                // wire carries a payload per rebuild instead of a
                // display list per frame.  Same painter, same origin
                // rule as the shapes path below — the walk is handed
                // the centre and produces window coordinates, so a
                // press needs no second transform.
                canvas.clear(view::BG);
                let (dx, dy) = (view.w / 2, view.h / 2);
                if let Some(w) =
                    self.walkers.borrow_mut().get_mut("substrate")
                {
                    gestate_panel::paint::paint(&mut canvas,
                                                w.frame(dx, dy));
                }
                view::paint(&mut canvas,
                            &view::chrome_only(&view, font, &chrome), font,
                            self.scale());
            } else if self.on_canvas.get() {
                // **The same painter the plugin panel uses.**  A second
                // one would be a second set of rounding decisions, and
                // the two windows would disagree about somebody's
                // artwork.
                // **The origin lands in the middle of the window, like
                // the plugin pane.**  `gui.py`'s walk is origin-relative
                // (`cx = cy = 0`) and where the origin lands is the
                // host's to say — so a bare `rect` draws centred, and
                // `moveXY` is an offset *from the centre*.  The offset
                // added here is the one every canvas pointer coordinate
                // subtracts below: one number, two directions, or the
                // picture and the hand disagree.
                canvas.clear(view::BG);
                let (dx, dy) = (view.w / 2, view.h / 2);
                let items = self.picture.borrow().iter()
                    .map(|i| match i.clone() {
                        Item::Rect { x, y, w, h, c } =>
                            Item::Rect { x: x + dx, y: y + dy, w, h, c },
                        Item::Dot { cx, cy, r, c } =>
                            Item::Dot { cx: cx + dx, cy: cy + dy, r, c },
                        Item::Text { x, y, s, c, scale } =>
                            Item::Text { x: x + dx, y: y + dy, s, c, scale },
                    })
                    .collect();
                let show = gestate_panel::list::Display {
                    items,
                    hits: Vec::new(),
                };
                gestate_panel::paint::paint(&mut canvas, &show);
                view::paint(&mut canvas,
                            &view::chrome_only(&view, font, &chrome), font,
                            self.scale());
            } else {
                view::paint(&mut canvas,
                            &view::frame_with(&doc, &view, font, &chrome),
                            font, self.scale());
                self.paint_scopes(&mut canvas, &doc, &view, font, &chrome);
                box_live = self.paint_canvas_boxes(&mut canvas, &doc,
                                                   &view, font, &chrome);
            }
        }
        // The palette over the text, in its own frame — chrome over a
        // document, so the document's layout cannot depend on whether a
        // list happens to be open.
        let palette = self.palette.borrow();
        if painting && palette.is_open() {
            let (cw, ch) = (view.cw(font), view.ch(font));
            // The warning belongs to the caret that is active: while
            // the list is up, that is the query box's, so the words go
            // to the palette's frame and `on_frame` keeps them out of
            // the document's.
            let warning = self.warned.borrow().as_ref()
                .map(|(s, _, _)| s.clone()).unwrap_or_default();
            view::paint(&mut canvas,
                        &palette.frame(view.w, view.h, cw, ch, &warning),
                        font, self.scale());
        }
        // **The burger, painted last** — above the palette, because
        // the press tests it first: what is drawn on top must answer
        // on top, or the corner is haunted.
        if painting {
            view::paint(&mut canvas,
                        &view::burger_frame(&view, font, palette.is_open()),
                        font, self.scale());
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
        // **A walked canvas re-dirties itself**: the animation lives on
        // this thread now, so every presented frame asks for the next
        // one, at the window's own rate — the `SHARE=1` argument one
        // floor up: the canvas is the thing being looked at.  A live
        // canvas *box* counts the same way, and only while it actually
        // drew — scrolled away, the pump stops and the walk goes still.
        self.dirty.set(self.stress
            || (self.on_canvas.get()
                && self.walkers.borrow().contains_key("substrate"))
            || box_live);
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
        // The bar wraps to the width, so a resize re-grants before the
        // view is clamped against the new geometry.
        v.grant(&self.chrome.borrow(), self.font());
        v.clamp(&doc, self.font());
        v.follow(&doc, self.font());
        self.dirty.set(true);
        Ok(())
    }

    fn on_event(&self, event: Event) -> EventStatus {
        match event {
            Event::Keyboard(k) => {
                // **While the piano has the keyboard, the keys are
                // notes.**  Releases matter here and nowhere else — a
                // note has a length — so this is above the guard that
                // drops them.
                // Never while the list is open — it is being typed
                // into, and a letter cannot be both a command's name
                // and a note.
                if self.at_piano.get()
                    && !self.palette.borrow().is_open()
                    && !k.modifiers.contains(Modifiers::CONTROL)
                {
                    if let Some(status) = self.finger(&k) {
                        return status;
                    }
                }
                if k.state != KeyState::Down {
                    return EventStatus::Ignored;
                }
                // **A shortcut is looked up in the list that
                // advertises it.**  Every command travels with the key
                // it claims, so matching the chord against *that* keeps
                // one table: a key cannot do something the list did not
                // offer, and — the half that was missing — the list
                // cannot advertise a key that does nothing.  `Ctrl-F`
                // said `find` for as long as it took somebody to press
                // it.
                //
                // A command that takes arguments opens the list already
                // asking for the first, which is what `Ctrl-F` means to
                // anyone who has pressed it anywhere else.
                if self.palette.borrow().is_open() == false {
                    if let Some(e) = self.shortcut(&k) {
                        self.to_the_list();
                        self.host.gesture(Gesture::Asked.line());
                        let asks = self.palette.borrow_mut().begin(&e);
                        match asks {
                            Asks::Run(name, args) => {
                                self.host.gesture(
                                    Gesture::Command(name, args).line());
                            }
                            Asks::Wants(name, at, q) => {
                                self.dirty.set(true);
                                self.host.gesture(
                                    Gesture::Wants(name, at, q,
                                                   self.given()).line());
                            }
                            _ => {}
                        }
                        return EventStatus::Captured;
                    }
                }
                // Ctrl-K opens the list.  One key, and the answer to
                // "what can this do" is complete by construction.
                if k.modifiers.contains(Modifiers::CONTROL) {
                    if let Kt::Character(s) = &k.key {
                        if s.eq_ignore_ascii_case("k") {
                            self.summon_list();
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
                // **What the platform actually handed us**, when asked.
                // A layout complaint is unanswerable without this: the
                // character, the physical key it came from and the
                // modifiers are three different things and only one of
                // them is wrong at a time.
                if std::env::var_os("GESTATE_EDITOR_KEYS").is_some() {
                    eprintln!("[keys] key={:?} code={:?} mods={:?}",
                              k.key, k.code, k.modifiers);
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
                    self.speak(asks);
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
                // A touch keeps the pointer for the same reason a knob
                // does: the substrate grabbed an element on the press,
                // and a fader that lost your hand at its own edge would
                // not be a fader.
                if self.touching.get() {
                    // The grab is the walker's; a drag with no grab
                    // writes nothing, same as the model's.  A grab
                    // taken in a canvas *box* was made in that band's
                    // coordinates and names its walker, and the drag
                    // speaks the frame it was grabbed in.
                    let (key, ox, oy) = self.box_grab.borrow().clone()
                        .unwrap_or_else(|| ("substrate".into(), 0, 0));
                    if let Some(w) =
                        self.walkers.borrow_mut().get_mut(&key)
                    {
                        for (name, value) in w.motion(x - ox, y - oy) {
                            self.host.gesture(
                                Gesture::Touched(name, value).line());
                        }
                        self.dirty.set(true);
                        return EventStatus::Captured;
                    }
                    let (dx, dy) = self.canvas_centre();
                    self.host.gesture(
                        Gesture::Touch("drag", x - dx, y - dy).line());
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
                // **The burger owns its corner, above everything** —
                // it is painted after the palette, so it answers
                // before it: the F116 rule, that the pointer belongs
                // to what is drawn where it is drawn.  A second press
                // is the same finger changing its mind, so it closes
                // what the first one opened.
                let (bx, by, bw, bh) =
                    self.view.borrow().burger_box(self.font());
                if x >= bx && x < bx + bw && y >= by && y < by + bh {
                    if self.palette.borrow().is_open() {
                        let asks = self.palette.borrow_mut().hide();
                        self.speak(asks);
                    } else {
                        // The bar says `Ctrl-K` while this list is up
                        // — the button teaching the key it stands for.
                        self.view.borrow_mut().hint = true;
                        self.summon_list();
                    }
                    self.dirty.set(true);
                    return EventStatus::Captured;
                }
                // **The list takes the pointer while it covers it.**
                // It is a panel over the document, so a click in it is
                // aimed at it — and a click that fell through to the
                // text would move a caret you cannot see.  A click the
                // panel does *not* cover is the pointer saying "not
                // this list": the list closes as Escape closes it, and
                // the press goes on to land on the knob, key or line
                // it was aimed at — which used to be eaten, leaving
                // the whole window dead to the mouse while the list
                // was open.
                if self.palette.borrow().is_open() {
                    let (covered, picked) = {
                        let view = self.view.borrow();
                        let font = self.font();
                        let (cw, ch) = (view.cw(font), view.ch(font));
                        let p = self.palette.borrow();
                        (p.covers(view.w, view.h, cw, ch, x, y),
                         p.row_at(view.w, view.h, cw, ch, x, y))
                    };
                    if let Some(row) = picked {
                        let asks = self.palette.borrow_mut().click(row);
                        self.speak(asks);
                        self.dirty.set(true);
                        return EventStatus::Captured;
                    }
                    if covered {
                        // The padding or the query row: aimed at the
                        // panel, answered by nothing.
                        self.dirty.set(true);
                        return EventStatus::Captured;
                    }
                    let asks = self.palette.borrow_mut().hide();
                    self.speak(asks);
                    self.dirty.set(true);
                    // No return: the press falls through to the chrome
                    // and the text below, exactly as if the list had
                    // been closed a moment earlier.
                }
                // **The margin belongs to the knobs.**  A press there is
                // a fader being taken hold of, not a caret being placed
                // — and answering to the press rather than only to the
                // drag is what makes a fader clickable at a value
                // instead of only draggable towards one.
                // A bank's box is a button: pressing it is the same act
                // as running `listen` or `deafen` on that name, and it
                // goes out as exactly that — so the widget and the
                // command cannot come to mean different things.
                // The drawn keyboard, which is a keyboard: pressing a
                // key sends the note, releasing it ends the note.
                if let Some(note) = self.struck_key(x, y) {
                    self.at_piano.set(true);
                    self.view.borrow_mut().focused = true;
                    self.dirty.set(true);
                    self.playing.set(Some(note));
                    self.host.gesture(Gesture::Note(note, true).line());
                    return EventStatus::Captured;
                }
                if self.at_piano.get() {
                    // Clicking anything else is clicking away from it.
                    self.hands_off();
                    self.at_piano.set(false);
                    self.view.borrow_mut().focused = false;
                    self.dirty.set(true);
                }
                if let Some(line) = self.tick(x, y) {
                    self.host.gesture(line);
                    return EventStatus::Captured;
                }
                if let Some(turn) = self.grab(x, y) {
                    self.host.gesture(turn);
                    return EventStatus::Captured;
                }
                // **The canvas box gets the hand** (B3 — and the
                // retired vocabulary earning its keep: a touch in a
                // box is a `touched` like any other, no id, no second
                // verb).  The walk's hit-boxes live in the band's own
                // coordinates, so the press is translated in and the
                // grab remembers the translation for the drag.  The
                // whole band is the picture's: a press that lands on
                // none of its elements crosses as nothing, the canvas
                // view's own rule.
                if !self.on_canvas.get() {
                    let hit = {
                        let doc = self.doc.borrow();
                        let view = self.view.borrow();
                        let chrome = self.chrome.borrow();
                        chrome.canvases.iter().find_map(|(line, key)| {
                            let (ix, iy, iw, vh, _fh) =
                                self.canvas_box_rect(&doc, &view,
                                                     self.font(),
                                                     &chrome, *line)?;
                            (x >= ix && x < ix + iw
                             && y >= iy && y < iy + vh)
                                .then(|| (key.clone(), ix, iy))
                        })
                    };
                    if let Some((key, ix, iy)) = hit {
                        if let Some(w) =
                            self.walkers.borrow_mut().get_mut(&key)
                        {
                            self.touching.set(true);
                            *self.box_grab.borrow_mut() =
                                Some((key.clone(), ix, iy));
                            for (name, value) in
                                w.press(x - ix, y - iy)
                            {
                                self.host.gesture(
                                    Gesture::Touched(name, value)
                                        .line());
                            }
                            self.dirty.set(true);
                            return EventStatus::Captured;
                        }
                    }
                }
                // **The canvas gets the hand the chrome refused.**  In
                // canvas mode a press that no button, key or knob
                // claimed is aimed at the picture; which element it
                // lands on is the model's to say (`spec/workbench.md`:
                // the canvas is an input device), so the window reports
                // the place and holds nothing itself.  Without this
                // branch the press falls through to `keys::click` and
                // moves a caret behind the picture — fixme.md F101.
                // The place is in canvas coordinates: origin at the
                // window's centre, where the paint put it.
                if self.on_canvas.get() {
                    self.touching.set(true);
                    // **The walk is here, so the hit-testing is too.**
                    // What crosses is what the gesture meant: the
                    // channel's name and the clamped fraction —
                    // coordinates never do (`spec/workbench.md` §"The
                    // canvas walks over crust").  A press that lands
                    // on nothing crosses as nothing.
                    if let Some(w) =
                        self.walkers.borrow_mut().get_mut("substrate")
                    {
                        for (name, value) in w.press(x, y) {
                            self.host.gesture(
                                Gesture::Touched(name, value).line());
                        }
                        self.dirty.set(true);
                        return EventStatus::Captured;
                    }
                    let (dx, dy) = self.canvas_centre();
                    self.host.gesture(
                        Gesture::Touch("press", x - dx, y - dy).line());
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
                let boxed = self.box_grab.borrow_mut().take();
                if self.touching.take() {
                    let key = boxed.map(|(k, _, _)| k)
                        .unwrap_or_else(|| "substrate".into());
                    if let Some(w) =
                        self.walkers.borrow_mut().get_mut(&key)
                    {
                        // A release writes nothing — a fader stays
                        // where it was let go — but it *says* so: a
                        // slide coalesces to where the hand ended, and
                        // a gesture that has to commit needs the full
                        // stop (`spec/workbench.md`, and the score
                        // box's drag is the caller).
                        if let Some(name) = w.release() {
                            self.host.gesture(
                                Gesture::Released(name).line());
                        }
                    } else {
                        // The release says where the hand was let go,
                        // so a program watching for it sees the same
                        // point the last drag reported.
                        let (x, y) = self.cursor.get();
                        let (dx, dy) = self.canvas_centre();
                        self.host.gesture(
                            Gesture::Touch("release",
                                           x - dx, y - dy).line());
                    }
                }
                if let Some(note) = self.playing.take() {
                    self.host.gesture(Gesture::Note(note, false).line());
                }
                EventStatus::Captured
            }
            Event::Mouse(MouseEvent::WheelScrolled { delta, modifiers })
                if self.palette.borrow().is_open() =>
            {
                // The list scrolls, not the document behind it — see the
                // click above for why an open list owns the pointer.
                let by = match delta {
                    baseview::ScrollDelta::Lines { y, .. } => -y as i32,
                    baseview::ScrollDelta::Pixels { y, .. } => {
                        let ch = self.view.borrow().ch(self.font()).max(1);
                        -(y as i32) / ch
                    }
                };
                let _ = modifiers;
                if by != 0 {
                    self.palette.borrow_mut().scroll(by);
                    self.dirty.set(true);
                }
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

/// X11's autorepeat, made detectable — `fixme.md` F106.
///
/// By default the server synthesizes a *release+press pair* for every
/// repeat of a held key.  Both autorepeat guards — the window's
/// `fingers` set and the model's `Keyboard.press` — were standing when
/// the piano retriggered, because a synthetic release re-arms them
/// both.  `XkbSetDetectableAutoRepeat` is the per-client flag that
/// makes the server send press, press, …, release instead, which is
/// the stream the guards were written for.  Per-client is why this is
/// called on *baseview's* display rather than a connection of our own,
/// and why it costs nothing anywhere else: a held arrow in the text
/// still repeats, because repeats still arrive — only the fake
/// releases stop.
/// The window's icon — drawn, not shipped.
///
/// A sine in the caret's blue on the editor's own ground, generated at
/// three sizes and set as `_NET_WM_ICON`, which is what a taskbar and
/// an alt-tab read.  Drawn in code because an asset is a file that can
/// go missing and a decoder is a dependency, while a sine is eight
/// lines — and because the palette constants are right here, so the
/// icon and the window cannot drift apart.
#[cfg(target_os = "linux")]
mod window_icon {
    use std::os::raw::{c_char, c_int, c_ulong, c_void};

    #[link(name = "X11")]
    extern "C" {
        fn XInternAtom(d: *mut c_void, name: *const c_char,
                       only_if_exists: c_int) -> c_ulong;
        fn XChangeProperty(d: *mut c_void, w: c_ulong, prop: c_ulong,
                           kind: c_ulong, format: c_int, mode: c_int,
                           data: *const u8, n: c_int) -> c_int;
        fn XFlush(d: *mut c_void) -> c_int;
    }

    /// One size, as `_NET_WM_ICON` wants it: width, height, then ARGB
    /// pixels — each packed in a C `long`, because that is what X11's
    /// format-32 property data means on a 64-bit machine.
    fn drawn(side: usize) -> Vec<c_ulong> {
        let s = side as f64;
        let mut out = Vec::with_capacity(2 + side * side);
        out.push(side as c_ulong);
        out.push(side as c_ulong);
        for y in 0..side {
            for x in 0..side {
                let (fx, fy) = (x as f64 + 0.5, y as f64 + 0.5);
                // Rounded corners: transparent outside the corner
                // radius, so the icon reads as a tile and not a chip.
                let r = s * 0.2;
                let (cx, cy) = (fx.clamp(r, s - r), fy.clamp(r, s - r));
                if ((fx - cx).powi(2) + (fy - cy).powi(2)).sqrt() > r {
                    out.push(0);
                    continue;
                }
                // One period of a sine, `CARET` blue on `BG`.
                let t = (fx / s) * std::f64::consts::TAU;
                let mid = s * 0.5 - t.sin() * s * 0.26;
                let argb: u32 = if (fy - mid).abs() < (s * 0.08).max(1.0) {
                    0xff5c_a8d8
                } else {
                    0xff14_161a
                };
                out.push(argb as c_ulong);
            }
        }
        out
    }

    pub unsafe fn set(display: *mut c_void, window: c_ulong) {
        let mut data: Vec<c_ulong> = Vec::new();
        for side in [16usize, 32, 48] {
            data.extend(drawn(side));
        }
        let atom = unsafe {
            XInternAtom(display, b"_NET_WM_ICON\0".as_ptr().cast(), 0)
        };
        const XA_CARDINAL: c_ulong = 6;
        const XA_STRING: c_ulong = 31;
        const PROP_MODE_REPLACE: c_int = 0;
        unsafe {
            XChangeProperty(display, window, atom, XA_CARDINAL, 32,
                            PROP_MODE_REPLACE, data.as_ptr().cast(),
                            data.len() as c_int);
            // **`WM_CLASS`, which baseview never sets.**  It is how a
            // desktop matches a window to its `.desktop` file — GNOME's
            // dock ignores `_NET_WM_ICON` and shows a gear for a window
            // it cannot name — so without this line the icon above is
            // only ever seen by alt-tab.  `python -m gestate.workbench
            // --desktop` writes the file this name matches.
            let class = b"gestate\0gestate\0";
            let wm_class =
                XInternAtom(display, b"WM_CLASS\0".as_ptr().cast(), 0);
            XChangeProperty(display, window, wm_class, XA_STRING, 8,
                            PROP_MODE_REPLACE, class.as_ptr(),
                            class.len() as c_int);
            XFlush(display);
        }
    }
}

#[cfg(target_os = "linux")]
/// The clock floor — `uclamp_min` on the window's own thread.
///
/// `spec/performance.md` §4 "The third mask": on a `powersave`
/// governor, retiring the model's per-frame walk left this process so
/// light that the cores parked at 500–600 MHz — below the idle
/// baseline — and the window's 2 ms frame became 7, so a canvas in
/// continuous motion juddered at ~43 Hz with three cores asleep.
/// `uclamp_min` names exactly that mechanism: it tells the scheduler
/// this thread is worth at least mid capacity — per-thread,
/// unprivileged for one's own threads, and costing nothing when the
/// machine is genuinely busy, which is everything a governor change
/// or a spin-to-stay-warm is not.
///
/// **What it can and cannot reach** (measured on the m3, same day):
/// the claim succeeds and the frequency does not move, because
/// `intel_pstate` in *active* mode lets the hardware pick P-states
/// guided by EPP and never consults the scheduler's utilisation —
/// uclamp moves the clock only under `schedutil` (most AMD boxes,
/// or `intel_pstate=passive`).  On an active-mode Intel machine the
/// knob is EPP itself (`energy_performance_preference`, root's to
/// write — this one idled on `balance_power`), which is a system
/// setting and deliberately not this program's to change.  The claim
/// stays because it is correct where it works and inert where it
/// does not.
#[cfg(target_os = "linux")]
mod clock_floor {
    /// `struct sched_attr` through the uclamp generation's fields —
    /// the syscall carries a size so the struct may grow, and 56 is
    /// this shape's.
    #[repr(C)]
    struct SchedAttr {
        size: u32,
        sched_policy: u32,
        sched_flags: u64,
        sched_nice: i32,
        sched_priority: u32,
        sched_runtime: u64,
        sched_deadline: u64,
        sched_period: u64,
        sched_util_min: u32,
        sched_util_max: u32,
    }

    /// Keep the policy and parameters as they stand; only the floor
    /// moves.
    const KEEP_ALL: u64 = 0x08 | 0x10;
    const UTIL_CLAMP_MIN: u64 = 0x20;

    /// Ask for a utilisation floor on the calling thread, 0..=1024.
    /// `false` when the kernel lacks uclamp or a limit refuses — the
    /// window then runs exactly as it did before this existed.
    pub fn claim(util_min: u32) -> bool {
        let attr = SchedAttr {
            size: 56,
            sched_policy: 0,
            sched_flags: KEEP_ALL | UTIL_CLAMP_MIN,
            sched_nice: 0,
            sched_priority: 0,
            sched_runtime: 0,
            sched_deadline: 0,
            sched_period: 0,
            sched_util_min: util_min,
            sched_util_max: 1024,
        };
        // SAFETY: a syscall over a repr(C) struct of the size it
        // declares; pid 0 is the calling thread.
        unsafe {
            libc::syscall(libc::SYS_sched_setattr,
                          0i32, &attr as *const SchedAttr, 0u32) == 0
        }
    }
}

mod detectable_autorepeat {
    #[link(name = "X11")]
    extern "C" {
        // Display *, Bool detectable, Bool *supported → Bool
        fn XkbSetDetectableAutoRepeat(
            display: *mut core::ffi::c_void,
            detectable: i32,
            supported: *mut i32,
        ) -> i32;
    }

    /// `true` when the server agreed.  A server that cannot is left as
    /// it was, and the piano keeps F106 there — documented, not masked.
    pub unsafe fn enable(display: *mut core::ffi::c_void) -> bool {
        let mut supported = 0;
        unsafe {
            XkbSetDetectableAutoRepeat(display, 1, &mut supported) != 0
                && supported != 0
        }
    }
}
