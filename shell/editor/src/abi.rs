//! The C ABI — **Rust owns the rope and the window, Python
//! orchestrates.**
//!
//! The same shape `gestate/crust.py` already drives `libcrust.so` with:
//! a handful of `extern "C"` functions, hand-declared on the Python
//! side, no build-time coupling and no binding generator.
//! `shell/clap/src/abi.rs` makes the same move about CLAP, and states
//! the reason — declaring the subset you need and owning every line of
//! it is cheaper than a dependency that declares all of them.
//!
//! **Why the rope lives here.**  A keystroke never crosses the
//! boundary: it arrives in the window's own loop, the rope takes it and
//! the frame is redrawn, all in Rust, in microseconds.  Were Python to
//! own the text, every character typed would be a round trip and a
//! re-render of the document — which is the arrangement the editor was
//! moved out of.
//!
//! **What crosses instead is a version.**  Python polls `ged_version`,
//! which is one atomic read, and only asks for the text when it has
//! changed.  `audioeditor.Workbench` stays the model: it decides when a
//! rebuild is worth doing, what the file is, and when to save — the
//! editor never learns any of that, and by construction cannot.
//!
//! ## The thread
//!
//! `baseview`'s loop blocks, so `ged_open` puts it on a thread of its
//! own and hands back a handle.  Everything the two sides share is in
//! `Shared`, behind atomics and short mutexes; nothing in the drawing
//! path takes a lock the other side can hold.

use std::ffi::{c_char, CStr, CString};
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};

use crate::document::Document;
use crate::window::{self, Host};

/// What the two sides pass between them.
pub struct Shared {
    /// The text as of the last edit.
    ///
    /// **Written by the window thread, read by whoever asks.**  A
    /// quarter-megabyte file is a quarter-megabyte copy per edit —
    /// measured at 0.28 ms — which is affordable at typing speed and is
    /// the price of the other side not being able to reach the rope.
    /// The alternative, handing out a pointer into a living tree, is a
    /// use-after-free waiting for a rebuild.
    text: Mutex<String>,
    /// Bumped on every edit.  **One atomic read is the whole polling
    /// protocol**, so a host can ask "did anything happen" sixty times
    /// a second for nothing.
    version: AtomicU64,
    pos: AtomicUsize,
    open: AtomicBool,
    /// Text the host wants loaded, picked up on the next frame.  The
    /// flag says whether the histories go with it: `true` is a file
    /// switch (`ged_load_text` — a different file is a different past),
    /// `false` is a replacement (`ged_set_text` — what `fmt` uses, one
    /// undo away from the text you had).
    incoming: Mutex<Option<(String, bool)>>,
    /// The host has asked the window to shut.
    closing: AtomicBool,
    /// The chrome, as the model last described it.
    ///
    /// **A whole description each time, not a diff.**  A diff would be
    /// a second state to keep in step across a boundary, which is the
    /// thing this design keeps refusing; the description is a few
    /// hundred bytes and is pushed only when something changed.
    furniture: Mutex<String>,
    /// Bumped when it does, so the window redraws without comparing.
    furnished: AtomicU64,
    /// What the window has to say back, oldest first.
    gestures: Mutex<Vec<String>>,
    /// The canvas, as shapes to draw.
    ///
    /// **Its own channel, not part of the furniture.**  A substrate
    /// animates — a meter, a spectrum, anything reading `peak` — so its
    /// display list changes every frame while the furniture beside it
    /// changes when a command runs. Sending them together would make
    /// every knob and command line cross the boundary sixty times a
    /// second to carry a moving dot, which is the churn the beat's
    /// rounding already had to be fixed for once.
    picture: Mutex<String>,
    drawn: AtomicU64,
    /// What the model has asked the window to *do*, oldest first.
    ///
    /// **The other direction, and it needs one.**  The furniture says
    /// what things are; this says what to do about them.  Undo, zoom
    /// and the caret live on the window's thread and nothing off it may
    /// touch the rope — so a command like `zoomIn` cannot reach in, it
    /// leaves a name and its arguments here and the window collects
    /// them when it is next drawing anyway.  Same shape as `incoming`
    /// and `furniture`, same reason.
    orders: Mutex<Vec<String>>,
    initial: Mutex<String>,
}

impl Shared {
    fn new(initial: String) -> Arc<Shared> {
        Arc::new(Shared {
            text: Mutex::new(initial.clone()),
            version: AtomicU64::new(0),
            pos: AtomicUsize::new(0),
            open: AtomicBool::new(true),
            incoming: Mutex::new(None),
            closing: AtomicBool::new(false),
            furniture: Mutex::new(String::new()),
            furnished: AtomicU64::new(0),
            gestures: Mutex::new(Vec::new()),
            orders: Mutex::new(Vec::new()),
            picture: Mutex::new(String::new()),
            drawn: AtomicU64::new(0),
            initial: Mutex::new(initial),
        })
    }

    /// Text the host asked to load, if any — the window thread's side
    /// of `ged_set_text` and `ged_load_text`.
    pub fn take_incoming(&self) -> Option<(String, bool)> {
        self.incoming.lock().ok().and_then(|mut t| t.take())
    }

    /// The window thread saying the document changed.
    pub fn published(&self, text: String) {
        if let Ok(mut held) = self.text.lock() {
            *held = text;
        }
        self.version.fetch_add(1, Ordering::Release);
    }

    fn furniture_now(&self) -> Option<(u64, String)> {
        let at = self.furnished.load(Ordering::Acquire);
        if at == 0 {
            return None;
        }
        self.furniture.lock().ok().map(|t| (at, t.clone()))
    }

    fn gesture_now(&self, line: String) {
        if let Ok(mut q) = self.gestures.lock() {
            // **Bounded.**  A host that stops draining — because it is
            // rebuilding, or has gone away — must not let a dragged
            // knob grow this without limit.  The newest are the ones
            // that matter, so the oldest go.
            if q.len() >= 4096 {
                q.drain(..1024);
            }
            q.push(line);
        }
    }
}

impl Host for Shared {
    fn edited(&self, doc: &Document) {
        self.published(doc.text());
        self.pos.store(doc.pos(), Ordering::Relaxed);
    }

    fn moved(&self, pos: usize) {
        self.pos.store(pos, Ordering::Relaxed);
    }

    fn initial(&self) -> String {
        self.initial.lock().map(|t| t.clone()).unwrap_or_default()
    }

    fn incoming(&self) -> Option<(String, bool)> {
        self.take_incoming()
    }

    fn furniture(&self) -> Option<(u64, String)> {
        self.furniture_now()
    }

    fn picture(&self) -> Option<(u64, String)> {
        let at = self.drawn.load(Ordering::Acquire);
        if at == 0 {
            return None;
        }
        self.picture.lock().ok().map(|t| (at, t.clone()))
    }

    fn orders(&self) -> Vec<String> {
        match self.orders.lock() {
            Err(_) => Vec::new(),
            Ok(mut q) => std::mem::take(&mut *q),
        }
    }

    fn gesture(&self, line: String) {
        self.gesture_now(line)
    }

    fn should_close(&self) -> bool {
        self.closing.load(Ordering::Acquire)
    }
}

/// The handle Python holds — the shared state and the thread running
/// the window.
pub struct Editor {
    shared: Arc<Shared>,
    thread: Option<std::thread::JoinHandle<()>>,
}

fn text_of(p: *const c_char) -> String {
    if p.is_null() {
        return String::new();
    }
    // SAFETY: the caller's promise that this is a NUL-terminated
    // string, which is the whole of the contract on this side.
    unsafe { CStr::from_ptr(p) }.to_string_lossy().into_owned()
}

/// Open an editor window with this text.  Returns a handle, or null.
///
/// # Safety
/// `text` must be NUL-terminated or null.
#[no_mangle]
pub unsafe extern "C" fn ged_open(text: *const c_char, w: i32, h: i32)
    -> *mut Editor
{
    let shared = Shared::new(text_of(text));
    let mine = shared.clone();
    let thread = std::thread::Builder::new()
        .name("gestate-editor".into())
        .spawn(move || {
            let host: Arc<dyn Host> = mine.clone();
            let _ = window::open_blocking(host, w.max(160), h.max(120));
            // The window closed: say so, so a host polling `ged_is_open`
            // stops rather than waiting for an event that will not come.
            mine.open.store(false, Ordering::Release);
        })
        .ok();
    match thread {
        None => std::ptr::null_mut(),
        Some(t) => Box::into_raw(Box::new(Editor { shared, thread: Some(t) })),
    }
}

macro_rules! editor {
    ($e:expr, $default:expr) => {
        match unsafe { $e.as_ref() } {
            None => return $default,
            Some(e) => e,
        }
    };
}

/// Whether the window is still there.
///
/// # Safety
/// `e` must be a handle from `ged_open` that has not been closed.
#[no_mangle]
pub unsafe extern "C" fn ged_is_open(e: *const Editor) -> bool {
    editor!(e, false).shared.open.load(Ordering::Acquire)
}

/// How many edits have happened.  **One atomic read** — poll it.
///
/// # Safety
/// As `ged_is_open`.
#[no_mangle]
pub unsafe extern "C" fn ged_version(e: *const Editor) -> u64 {
    editor!(e, 0).shared.version.load(Ordering::Acquire)
}

/// Where the caret is, as a character offset.
///
/// # Safety
/// As `ged_is_open`.
#[no_mangle]
pub unsafe extern "C" fn ged_pos(e: *const Editor) -> usize {
    editor!(e, 0).shared.pos.load(Ordering::Relaxed)
}

/// The text, as a fresh C string the caller must free with
/// `ged_free_str`.
///
/// # Safety
/// As `ged_is_open`.  The returned pointer is the caller's to free and
/// must not be freed any other way.
#[no_mangle]
pub unsafe extern "C" fn ged_text(e: *const Editor) -> *mut c_char {
    let ed = editor!(e, std::ptr::null_mut());
    let held = match ed.shared.text.lock() {
        Ok(t) => t.clone(),
        Err(_) => return std::ptr::null_mut(),
    };
    // A document holding a NUL is not representable as a C string, and
    // silently truncating one would hand back half a file.  Refusing is
    // the honest answer; nothing that compiles has one.
    match CString::new(held) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Load text into the editor.  Picked up on its next frame.
///
/// # Safety
/// As `ged_is_open`; `text` must be NUL-terminated or null.
#[no_mangle]
pub unsafe extern "C" fn ged_set_text(e: *const Editor, text: *const c_char) {
    let ed = editor!(e, ());
    if let Ok(mut slot) = ed.shared.incoming.lock() {
        *slot = Some((text_of(text), false));
    }
}

/// Load text into the editor *and clear its histories* — what opening
/// a different file does, and the only thing that may.
///
/// **A different file is a different past** (`fixme.md` F113):
/// `ged_set_text` commits, which keeps `fmt` one undo away from the
/// text you had, and which put the old file's whole content on the new
/// file's undo stack at a switch — undo, and A's text stood under B's
/// name, one save from overwriting B with A.
///
/// # Safety
/// As `ged_is_open`; `text` must be NUL-terminated or null.
#[no_mangle]
pub unsafe extern "C" fn ged_load_text(e: *const Editor, text: *const c_char) {
    let ed = editor!(e, ());
    if let Ok(mut slot) = ed.shared.incoming.lock() {
        *slot = Some((text_of(text), true));
    }
}

/// Describe the chrome — status, knobs, banks, transport, commands.
///
/// See `furniture.rs` for the format.  Pushed whole, and only when
/// something changed.
///
/// # Safety
/// As `ged_is_open`; `text` must be NUL-terminated or null.
#[no_mangle]
pub unsafe extern "C" fn ged_set_furniture(e: *const Editor,
                                           text: *const c_char) {
    let ed = editor!(e, ());
    if let Ok(mut held) = ed.shared.furniture.lock() {
        *held = text_of(text);
    }
    ed.shared.furnished.fetch_add(1, Ordering::Release);
}

/// Take everything the window has said since this was last called, one
/// gesture a line.  A fresh C string, freed with `ged_free_str`.
///
/// **Drained rather than read**, so a host cannot see one twice: a
/// command run because the queue was polled again is the sort of bug
/// that plays a note nobody asked for.
///
/// # Safety
/// As `ged_text`.
#[no_mangle]
pub unsafe extern "C" fn ged_gestures(e: *const Editor) -> *mut c_char {
    let ed = editor!(e, std::ptr::null_mut());
    let taken = match ed.shared.gestures.lock() {
        Ok(mut q) => std::mem::take(&mut *q),
        Err(_) => return std::ptr::null_mut(),
    };
    match CString::new(taken.join("\n")) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Free a string `ged_text` handed out.
///
/// # Safety
/// `p` must have come from `ged_text` and not been freed.
/// The canvas, as shapes to draw — see `shapes::read`.
///
/// # Safety
/// `e` must be a live editor and `text` a NUL-terminated string.
#[no_mangle]
pub unsafe extern "C" fn ged_set_picture(e: *const Editor,
                                         text: *const c_char) {
    let ed = editor!(e, ());
    if let Ok(mut held) = ed.shared.picture.lock() {
        *held = text_of(text);
    }
    ed.shared.drawn.fetch_add(1, Ordering::Release);
}

/// Ask the window to do something — see `furniture::Order`.
///
/// Queued and obeyed on the window's next frame, because the document
/// belongs to the window's thread.
///
/// # Safety
/// `e` must be a live editor and `line` a NUL-terminated string.
#[no_mangle]
pub unsafe extern "C" fn ged_order(e: *const Editor, line: *const c_char) {
    let ed = editor!(e, ());
    if let Ok(mut q) = ed.shared.orders.lock() {
        if q.len() >= 1024 {
            q.drain(..256);
        }
        q.push(text_of(line));
    }
}

#[no_mangle]
pub unsafe extern "C" fn ged_free_str(p: *mut c_char) {
    if !p.is_null() {
        drop(unsafe { CString::from_raw(p) });
    }
}

/// Ask the window to shut.  Returns at once; poll `ged_is_open`.
///
/// # Safety
/// As `ged_is_open`.
#[no_mangle]
pub unsafe extern "C" fn ged_request_close(e: *const Editor) {
    editor!(e, ()).shared.closing.store(true, Ordering::Release);
}

/// Close the window and release the handle.
///
/// # Safety
/// `e` must be a handle from `ged_open`, and must not be used again.
#[no_mangle]
pub unsafe extern "C" fn ged_close(e: *mut Editor) {
    if e.is_null() {
        return;
    }
    let mut ed = unsafe { Box::from_raw(e) };
    ed.shared.closing.store(true, Ordering::Release);
    // **The thread is joined, not abandoned.**  A window still drawing
    // into a surface whose process is tearing down is the sort of crash
    // that gets blamed on the host — so the close is *asked for* above
    // (the window does it to itself, on its own thread, between frames)
    // and this waits for the loop to come back.
    if let Some(t) = ed.thread.take() {
        let _ = t.join();
    }
}
