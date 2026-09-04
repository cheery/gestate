//! The browser's shell for the picture — `card:audiovisual-gallery.md`.
//!
//! Six pieces on the site declare a `substrate` and the tab drops it on
//! the floor.  A substrate is a **second program**
//! (`spec/substrate.md`): serialized by `gestate.crust.serialize`,
//! interpreted at frame rate, and until now it stayed at home because
//! only a G-machine could run it and the tab had none.  `crust` builds
//! for `wasm32` — 164 KB, no imports — so it has one.
//!
//! **Nothing here decides what a substrate means.**  The driver is
//! `gestate_panel::canvas::Canvas`, the same one the CLAP plugin's
//! window turns, and the walk under it is `gestate_panel::substrate`,
//! held against `gestate/gui.py` tree for tree.  This module is the
//! *seam*: a page cannot call a Rust method, so the loop it already
//! runs — one instant, one picture, one press — is offered as a
//! handful of C functions and one flat buffer of `i32`.
//!
//! That is the whole reason it is thin.  A second walk in JavaScript
//! would be a second implementation kept, which is the cost
//! `card:online.md` C1 was stood down for.
//!
//! # The seam, in order
//!
//! ```text
//!   web_alloc            → bytes the page writes the program into
//!   web_open             → a canvas, or null and web_error
//!   web_list             → a whole window staged for the next tick
//!   web_tick             → one instant, then one picture
//!   web_display          → the wire: items, then attachments
//!   web_press/motion/release → a hand, and the writes it produced
//!   web_close
//! ```
//!
//! # The wire
//!
//! One `i32` array, rebuilt each `web_display` and owned by the canvas
//! until the next call.  It is a *flat* format rather than a struct
//! layout because a page reads it with `new Int32Array(memory.buffer)`
//! and nothing on the far side should have to know Rust's padding.
//!
//! ```text
//!   [0] items      how many drawing records follow the header
//!   [1] hits       how many attachment records follow those
//!   then `items` records, each led by its kind:
//!       0 RECT   x y w h rgb
//!       1 DOT    cx cy r rgb
//!       2 TEXT   x y scale rgb len  then `len` code points
//!   then `hits` records, each seven words:
//!       kind axis extra x0 y0 x1 y1
//!   where kind is 0 fader, 1 toggle, 2 button, 3 channel, and `extra`
//!   is the parameter, the button's action, or the channel id.
//! ```
//!
//! A record's length is implied by its kind, so the reader walks with a
//! cursor.  Colours are the `0x00RRGGBB` word `Colour::word` already
//! produces — the painter's own spelling, not a new one.

use std::ffi::c_char;

use gestate_panel::canvas::{Canvas, CanvasProgram};
use gestate_panel::list::{Axis, Item, Kind};
use gestate_panel::substrate::SubTags;

/// A canvas, plus the buffers the page reads it through.
///
/// The wire and the writes are kept **on the handle** rather than
/// returned as fresh allocations: a page that had to free every frame's
/// display list would leak the first time it forgot, and at 60 Hz it
/// would forget.  Each is valid until the next call that rebuilds it,
/// which is the same promise `crust_stream_pull` makes.
pub struct Web {
    canvas: Canvas,
    wire: Vec<i32>,
    writes: Vec<f64>,
    error: Vec<u8>,
    /// Whole windows staged for the next `web_tick` — see `web_list`.
    lists: Vec<(i64, Vec<f64>)>,
}

impl Web {
    fn say(&mut self, what: &str) {
        self.error.clear();
        self.error.extend_from_slice(what.as_bytes());
        self.error.push(0);
    }
}

/// The last failure, for a handle that could not be made.
///
/// A `web_open` that returns null has nowhere to put its sentence, so
/// there is one slot here for exactly that case.  Single-threaded on
/// purpose: a page has one main thread and a worklet does not open
/// canvases.
static mut OPENING: Vec<u8> = Vec::new();

fn park_opening(what: &str) {
    unsafe {
        let slot = &mut *std::ptr::addr_of_mut!(OPENING);
        slot.clear();
        slot.extend_from_slice(what.as_bytes());
        slot.push(0);
    }
}

/// Bytes for the page to write into — a program, an entry, a name.
///
/// # Safety
/// Free with `web_free` and the same length.
#[no_mangle]
pub extern "C" fn web_alloc(n: usize) -> *mut u8 {
    let mut v = vec![0u8; n];
    let p = v.as_mut_ptr();
    std::mem::forget(v);
    p
}

/// # Safety
/// `p` and `n` as they came from `web_alloc`, once.
#[no_mangle]
pub unsafe extern "C" fn web_free(p: *mut u8, n: usize) {
    if !p.is_null() {
        drop(Vec::from_raw_parts(p, n, n));
    }
}

unsafe fn text_at(p: *const u8, n: usize) -> String {
    if p.is_null() || n == 0 {
        return String::new();
    }
    String::from_utf8_lossy(std::slice::from_raw_parts(p, n)).into_owned()
}

/// Open one piece's canvas.
///
/// `tags` is the fourteen-word table `gestate.export.substrate_of`
/// writes — the twelve `Sub` constructors in `SubTags` order, then
/// `Cons` and `Nil`.  **A tag is a position in this program's own
/// table**, so a page cannot derive one and must carry it; guessing
/// would draw a `Row` as whatever happened to share its number.
///
/// `chans` is the declared channel names, NUL-separated, **in the order
/// written**.  Names rather than ids, for the reason
/// `CanvasProgram::chans` gives at length: an id is allocated when a
/// declaration is first forced, so it is a fact about the host's order
/// and not about the program.
///
/// Returns null on refusal, with the sentence in `web_error(null)`.
///
/// # Safety
/// Every pointer must be readable for its stated length; `tags` must
/// hold fourteen `i64`.
#[no_mangle]
pub unsafe extern "C" fn web_open(text: *const u8, text_len: usize,
                                  entry: *const u8, entry_len: usize,
                                  tags: *const i64,
                                  chans: *const u8, chans_len: usize)
                                  -> *mut Web {
    if text.is_null() || tags.is_null() {
        park_opening("web: open without a program");
        return std::ptr::null_mut();
    }
    let t = std::slice::from_raw_parts(tags, 14);
    let program = CanvasProgram {
        text: text_at(text, text_len),
        entry: {
            let e = text_at(entry, entry_len);
            if e.is_empty() { "main".to_string() } else { e }
        },
        tags: SubTags {
            rect: t[0], circle: t[1], gap: t[2], over: t[3],
            row: t[4], column: t[5], shift: t[6], sized: t[7],
            pad: t[8], touch_x: t[9], touch_y: t[10], label: t[11],
            cons: t[12], nil: t[13],
        },
        chans: text_at(chans, chans_len)
            .split('\0')
            .filter(|s| !s.is_empty())
            .map(str::to_string)
            .collect(),
        // **Empty, and that is not a stub.**  The bridge pairs a
        // channel with the *host parameter* it also is, and a page has
        // no host and no parameters — the sound in a tab is the same
        // wasm module the canvas writes its channel into directly.
        // `card:audiovisual-gallery.md`'s remaining rows are where that
        // seam gets built.
        bridge: Vec::new(),
    };
    match Canvas::open(program) {
        Ok(canvas) => Box::into_raw(Box::new(Web {
            canvas,
            wire: Vec::new(),
            writes: Vec::new(),
            error: Vec::new(),
            lists: Vec::new(),
        })),
        Err(why) => {
            park_opening(&why);
            std::ptr::null_mut()
        }
    }
}

/// # Safety
/// `w` from `web_open`, once.
#[no_mangle]
pub unsafe extern "C" fn web_close(w: *mut Web) {
    if !w.is_null() {
        drop(Box::from_raw(w));
    }
}

/// The last sentence — this canvas's, or the last failed `web_open`'s
/// when `w` is null.  Borrowed, NUL-terminated, valid until the next
/// failing call.
///
/// # Safety
/// `w` from `web_open`, or null.
#[no_mangle]
pub unsafe extern "C" fn web_error(w: *mut Web) -> *const c_char {
    static EMPTY: &[u8] = b"\0";
    if w.is_null() {
        let slot = &*std::ptr::addr_of!(OPENING);
        return if slot.is_empty() { EMPTY.as_ptr() as *const c_char }
               else { slot.as_ptr() as *const c_char };
    }
    let web = &mut *w;
    // **Copied, not borrowed.**  The canvas keeps its fault as a Rust
    // `String`, which has no NUL, and handing a page the bytes of one
    // is how a reader runs off the end of a message.  So it is copied
    // into this handle's own slot, terminated.
    if let Some(f) = web.canvas.fault() {
        let owned = f.to_string();
        web.say(&owned);
    }
    if web.error.is_empty() { EMPTY.as_ptr() as *const c_char }
    else { web.error.as_ptr() as *const c_char }
}

/// The channel id a declared name was given, or `-1`.
///
/// # Safety
/// `w` from `web_open`; `name` readable for `n` bytes.
#[no_mangle]
pub unsafe extern "C" fn web_channel(w: *mut Web, name: *const u8,
                                     n: usize) -> i64 {
    if w.is_null() {
        return -1;
    }
    (*w).canvas.channel(&text_at(name, n)).unwrap_or(-1)
}

/// One instant, then one picture.
///
/// `writes` is `[chan, value, chan, value, …]` as `f64` — the channel
/// id in the even slots, which is exact for every id a program can
/// allocate.  `pairs` is how many pairs, not how many words.
///
/// `(cx, cy)` is where the picture's own origin lands in the page's
/// coordinates, so the regions `web_display` reports are the ones a
/// pointer event can be tested against with no second transform.
///
/// **The instant and the picture are one call** because they must be in
/// step: drawing a fold a later arrival has moved past is how a canvas
/// comes to lag its own sound by a frame.
///
/// `pulse` is `Tick`'s constructor tag, or negative for none.  It is a
/// tag rather than a flag for the reason every tag here is carried: a
/// tag is a position in *this* program's table.  **A page that never
/// pulses shows a canvas whose faders work and whose animation stands
/// still** — `events` in `gui.ges` folds over `input`, and nothing else
/// advances it.  A program that reads `now` also wants real seconds
/// written to its `wallclock` channel in the same call, as one of the
/// `writes` (`fixme.md` F134): one instant, two arrivals.
///
/// # Safety
/// `w` from `web_open`; `writes` readable for `2 * pairs` doubles.
#[no_mangle]
pub unsafe extern "C" fn web_tick(w: *mut Web, writes: *const f64,
                                  pairs: usize, pulse: i64,
                                  cx: i32, cy: i32) {
    if w.is_null() {
        return;
    }
    let web = &mut *w;
    let arrivals = read_writes(writes, pairs);
    let pulse = if pulse < 0 { None } else { Some(pulse) };
    // Taken, so the staged windows are spent by exactly one instant —
    // a trace left on the pile would be redrawn as if it had arrived
    // again, which is a scope that lies about when it looked.
    let lists = std::mem::take(&mut web.lists);
    web.canvas.advance(&arrivals, &lists, pulse, cx, cy);
}

/// Stage a whole window for the next `web_tick` — a scope's trace.
///
/// A `List Float` on a channel (`spec/scope.md`), which the scalar wire
/// cannot carry: `web_tick` speaks `(chan, value)` doubles and a trace
/// is 128 of them under one name.  So it is **staged rather than
/// passed**, which keeps `web_tick`'s signature as it was and costs a
/// page one extra call per scope per frame.
///
/// The list is built with the program's own `Cons` and `Nil` on the far
/// side — `Canvas::advance` does it, from the tags `web_open` was given
/// — so nothing here decides what a list is.
///
/// Staged windows are spent by the next `web_tick` and are gone whether
/// or not the program read them.
///
/// # Safety
/// `w` from `web_open`; `points` readable for `n` doubles.
#[no_mangle]
pub unsafe extern "C" fn web_list(w: *mut Web, chan: i64,
                                  points: *const f64, n: usize) {
    if w.is_null() || points.is_null() {
        return;
    }
    let got = std::slice::from_raw_parts(points, n).to_vec();
    (*w).lists.push((chan, got));
}

unsafe fn read_writes(p: *const f64, pairs: usize) -> Vec<(i64, f64)> {
    if p.is_null() || pairs == 0 {
        return Vec::new();
    }
    std::slice::from_raw_parts(p, pairs * 2)
        .chunks_exact(2)
        .map(|c| (c[0] as i64, c[1]))
        .collect()
}

/// Rebuild the wire and hand it over.  See the module header for the
/// format.  Owned by the canvas, valid until the next `web_display`.
///
/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_display(w: *mut Web) -> *const i32 {
    if w.is_null() {
        return std::ptr::null();
    }
    let web = &mut *w;
    let display = web.canvas.display();
    let mut wire = vec![display.items.len() as i32,
                        display.hits.len() as i32];
    for item in &display.items {
        match item {
            Item::Rect { x, y, w: iw, h, c } =>
                wire.extend_from_slice(&[0, *x, *y, *iw, *h, c.word() as i32]),
            Item::Dot { cx, cy, r, c } =>
                wire.extend_from_slice(&[1, *cx, *cy, *r, c.word() as i32]),
            Item::Text { x, y, s, c, scale } => {
                wire.extend_from_slice(
                    &[2, *x, *y, *scale, c.word() as i32,
                      s.chars().count() as i32]);
                wire.extend(s.chars().map(|ch| ch as i32));
            }
        }
    }
    for hit in &display.hits {
        let (kind, axis, extra) = match hit.kind {
            Kind::Fader(a) => (0, axis_of(a), hit.param as i32),
            Kind::Toggle => (1, 0, hit.param as i32),
            Kind::Button(code) => (2, 0, code as i32),
            Kind::Chan(a, chan) => (3, axis_of(a), chan as i32),
        };
        let (x0, y0, x1, y1) = hit.region;
        wire.extend_from_slice(&[kind, axis, extra, x0, y0, x1, y1]);
    }
    web.wire = wire;
    web.wire.as_ptr()
}

fn axis_of(a: Axis) -> i32 {
    match a {
        Axis::X => 0,
        Axis::Y => 1,
    }
}

/// A press at `(x, y)`, in the same coordinates `web_tick` was given.
///
/// Returns the number of `(chan, value)` pairs the gesture produced;
/// read them from `web_writes`.  **A press grabs**, so a drag that
/// leaves the element still reaches it — which is what a fader is.
///
/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_press(w: *mut Web, x: i32, y: i32) -> usize {
    hand(w, |c| c.press(x, y))
}

/// A move to `(x, y)` — writes only while something is grabbed.
///
/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_motion(w: *mut Web, x: i32, y: i32) -> usize {
    hand(w, |c| c.motion(x, y))
}

/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_release(w: *mut Web) {
    if !w.is_null() {
        (*w).canvas.release();
    }
}

/// Is a gesture in progress?  A page uses this to decide whether to
/// keep following the pointer outside the canvas element.
///
/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_grabbing(w: *const Web) -> i32 {
    if w.is_null() { 0 } else { (*w).canvas.is_grabbing() as i32 }
}

/// The writes the last gesture produced — `[chan, value, …]`, owned by
/// the canvas and valid until the next gesture.
///
/// # Safety
/// `w` from `web_open`.
#[no_mangle]
pub unsafe extern "C" fn web_writes(w: *const Web) -> *const f64 {
    if w.is_null() { std::ptr::null() } else { (*w).writes.as_ptr() }
}

unsafe fn hand(w: *mut Web, act: impl FnOnce(&mut Canvas) -> Vec<(i64, f64)>)
               -> usize {
    if w.is_null() {
        return 0;
    }
    let web = &mut *w;
    let out = act(&mut web.canvas);
    web.writes.clear();
    for (chan, value) in &out {
        web.writes.push(*chan as f64);
        web.writes.push(*value);
    }
    out.len()
}

#[cfg(test)]
mod tests;
