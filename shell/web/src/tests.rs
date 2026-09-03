//! The wire, held to the picture the reference draws.
//!
//! `shell/panel/tests/substrate_parity.rs` is the port's own check:
//! `examples/audio/substrate.ges` as the compiler produces it, walked
//! on `crust`, equal tree for tree to what `gestate/gui.py` draws.
//! **This file reuses that fixture rather than making a second one**,
//! because there is only one correct picture and a shell that invented
//! its own reference could agree with itself while disagreeing with the
//! program.
//!
//! So what is checked here is the *seam*: that the flat `i32` buffer a
//! page reads is the same display list, record for record, and that the
//! things a page does — open, tick, press, drag, let go — reach the
//! canvas through pointers without losing anything on the way.
//!
//! These run on this machine, not in a browser.  What a browser adds is
//! the wasm target, and `test/test_gallery.py` is where that is
//! measured; nothing about the wire changes between them.

use super::*;

const PROGRAM: &str = include_str!("../../panel/tests/substrate.program");
const TAGS: &str = include_str!("../../panel/tests/substrate.tags");
const DISPLAY: &str = include_str!("../../panel/tests/substrate.display");

/// `substrate.ges` declares these two, in this order — the same
/// literals `substrate_parity.rs` carries, held to the exporter by
/// `test_panel_fixtures.py`.
const CHANS: &str = "cutoff\0peak\0";

fn tags() -> Vec<i64> {
    TAGS.split_whitespace().map(|w| w.parse().unwrap()).collect()
}

/// Open the way a page does: bytes and lengths, nothing borrowed from
/// Rust's own types.
fn open() -> *mut Web {
    let t = tags();
    let w = unsafe {
        web_open(PROGRAM.as_ptr(), PROGRAM.len(),
                 "main".as_ptr(), 4,
                 t.as_ptr(),
                 CHANS.as_ptr(), CHANS.len())
    };
    assert!(!w.is_null(), "web_open refused: {}", said(w));
    w
}

fn said(w: *mut Web) -> String {
    unsafe {
        let p = web_error(w) as *const u8;
        let mut n = 0;
        while *p.add(n) != 0 {
            n += 1;
        }
        String::from_utf8_lossy(std::slice::from_raw_parts(p, n)).into_owned()
    }
}

/// The wire, read the way a page reads it: one cursor, lengths implied
/// by each record's kind.
#[derive(Debug, PartialEq)]
enum Read {
    Rect(i32, i32, i32, i32, i32),
    Dot(i32, i32, i32, i32),
    Text(i32, i32, i32, i32, String),
}

fn wire(w: *mut Web) -> (Vec<Read>, Vec<[i32; 7]>) {
    let p = unsafe { web_display(w) };
    assert!(!p.is_null(), "no wire");
    let at = |i: usize| unsafe { *p.add(i) };
    let (items, hits) = (at(0) as usize, at(1) as usize);
    let mut c = 2;
    let mut drawn = Vec::new();
    for _ in 0..items {
        match at(c) {
            0 => {
                drawn.push(Read::Rect(at(c + 1), at(c + 2), at(c + 3),
                                      at(c + 4), at(c + 5)));
                c += 6;
            }
            1 => {
                drawn.push(Read::Dot(at(c + 1), at(c + 2), at(c + 3),
                                     at(c + 4)));
                c += 5;
            }
            2 => {
                let n = at(c + 5) as usize;
                let s: String = (0..n)
                    .map(|i| char::from_u32(at(c + 6 + i) as u32).unwrap())
                    .collect();
                drawn.push(Read::Text(at(c + 1), at(c + 2), at(c + 3),
                                      at(c + 4), s));
                c += 6 + n;
            }
            other => panic!("unknown record kind {other}"),
        }
    }
    let mut listening = Vec::new();
    for _ in 0..hits {
        let mut h = [0i32; 7];
        for (i, slot) in h.iter_mut().enumerate() {
            *slot = at(c + i);
        }
        listening.push(h);
        c += 7;
    }
    (drawn, listening)
}

/// The reference fixture, in the same shape — `rect x y w h r g b`,
/// `dot cx cy r r g b`, `hit axis chan x0 y0 x1 y1`.
fn reference() -> (Vec<Read>, usize) {
    let mut drawn = Vec::new();
    let mut hits = 0;
    for line in DISPLAY.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        if f.is_empty() {
            continue;
        }
        let n = |i: usize| -> i32 { f[i].parse().unwrap() };
        let rgb = |i: usize| -> i32 { (n(i) << 16) | (n(i + 1) << 8) | n(i + 2) };
        match f[0] {
            "rect" => drawn.push(Read::Rect(n(1), n(2), n(3), n(4), rgb(5))),
            "dot" => drawn.push(Read::Dot(n(1), n(2), n(3), rgb(4))),
            "text" => drawn.push(
                Read::Text(n(1), n(2), n(3), rgb(4), f[7..].join(" "))),
            "hit" => hits += 1,
            other => panic!("unknown fixture line kind {other}"),
        }
    }
    (drawn, hits)
}

#[test]
fn the_wire_carries_the_picture_the_reference_draws() {
    let w = open();
    // The origin at (0, 0), which is where the fixture's walk starts —
    // items straddle it, because a program placed by its centre has not
    // yet been told where the centre is.
    unsafe { web_tick(w, std::ptr::null(), 0, -1, 0, 0) };
    let (drawn, hits) = wire(w);
    let (want, want_hits) = reference();

    assert_eq!(drawn.len(), want.len(), "record count: got {drawn:?}");
    for (i, (a, b)) in drawn.iter().zip(&want).enumerate() {
        assert_eq!(a, b, "record {i}");
    }
    assert_eq!(hits.len(), want_hits, "the attachments");
    unsafe { web_close(w) };
}

#[test]
fn an_attachment_arrives_as_its_own_channel() {
    let w = open();
    unsafe { web_tick(w, std::ptr::null(), 0, -1, 0, 0) };
    let (_, hits) = wire(w);
    let h = hits.first().expect("one attachment");
    assert_eq!(h[0], 3, "kind: a channel, not a parameter");
    assert_eq!(h[1], 1, "axis: y — `substrate.ges` hands a TouchY");
    let chan = unsafe { web_channel(w, "cutoff".as_ptr(), 6) };
    assert!(chan >= 0, "`cutoff` was declared and got an id");
    assert_eq!(h[2] as i64, chan,
               "the region listens on the channel the program named");
    assert!(h[5] > h[3] && h[6] > h[4], "a region with area");
    unsafe { web_close(w) };
}

#[test]
fn an_arrival_moves_the_picture_and_not_the_region() {
    let w = open();
    unsafe { web_tick(w, std::ptr::null(), 0, -1, 0, 0) };
    let (before, hits_before) = wire(w);
    let chan = unsafe { web_channel(w, "cutoff".as_ptr(), 6) };

    let writes = [chan as f64, 0.95];
    unsafe { web_tick(w, writes.as_ptr(), 1, -1, 0, 0) };
    let (after, hits_after) = wire(w);

    assert_ne!(before, after, "the sweep ran and the picture stood still");
    assert_eq!(before.len(), after.len(),
               "the same elements, in the same order");
    assert_eq!(hits_before, hits_after,
               "and the fader listens over the box it declared");
    unsafe { web_close(w) };
}

#[test]
fn a_press_grabs_and_a_release_lets_go() {
    let w = open();
    unsafe { web_tick(w, std::ptr::null(), 0, -1, 0, 0) };
    let (_, hits) = wire(w);
    let h = hits[0];
    // The middle of the attachment's own region.
    let (x, y) = ((h[3] + h[5]) / 2, (h[4] + h[6]) / 2);

    assert_eq!(unsafe { web_grabbing(w) }, 0, "nothing held yet");
    let n = unsafe { web_press(w, x, y) };
    assert_eq!(n, 1, "a press on an attachment writes its channel");
    assert_eq!(unsafe { web_grabbing(w) }, 1, "and it grabs");

    let out = unsafe { std::slice::from_raw_parts(web_writes(w), 2) };
    let chan = unsafe { web_channel(w, "cutoff".as_ptr(), 6) };
    assert_eq!(out[0] as i64, chan, "on the channel the element carries");
    assert!((0.0..=1.0).contains(&out[1]),
            "a fraction of the element's own extent, got {}", out[1]);

    // **A drag that leaves the element still reaches it** — that is what
    // a fader is, and the grab is what makes it true.
    let far = unsafe { web_motion(w, x + 500, y + 500) };
    assert_eq!(far, 1, "the grabbed element still hears the hand");

    unsafe { web_release(w) };
    assert_eq!(unsafe { web_grabbing(w) }, 0, "and a release lets go");
    assert_eq!(unsafe { web_motion(w, x, y) }, 0,
               "after which a bare move writes nothing");
    unsafe { web_close(w) };
}

#[test]
fn a_press_on_empty_ground_writes_nothing() {
    let w = open();
    unsafe { web_tick(w, std::ptr::null(), 0, -1, 0, 0) };
    assert_eq!(unsafe { web_press(w, 10_000, 10_000) }, 0);
    assert_eq!(unsafe { web_grabbing(w) }, 0);
    unsafe { web_close(w) };
}

#[test]
fn a_program_that_is_not_a_picture_is_refused_with_a_sentence() {
    let t = tags();
    let text = "crust 1\nblock\nI PushInt 1\nI Update 0\nI Unwind\n\
                global main 0 0\nentry main\n";
    let w = unsafe {
        web_open(text.as_ptr(), text.len(), "main".as_ptr(), 4,
                 t.as_ptr(), std::ptr::null(), 0)
    };
    assert!(w.is_null(), "a number is not a canvas");
    let why = said(std::ptr::null_mut());
    assert!(!why.is_empty(), "and it says so");
    assert!(why.contains("main"), "naming the entry it tried: {why}");
}

#[test]
fn an_open_with_no_program_refuses_rather_than_faulting() {
    let t = tags();
    let w = unsafe {
        web_open(std::ptr::null(), 0, std::ptr::null(), 0,
                 t.as_ptr(), std::ptr::null(), 0)
    };
    assert!(w.is_null());
    assert!(said(std::ptr::null_mut()).contains("program"));
}

/// **Every entry point survives a null handle.**
///
/// A page's own bug — a canvas used after it was closed, a handle that
/// never opened — must come back as nothing rather than as a trap that
/// takes the tab down.  `crust`'s C surface makes the same promise and
/// this is the same check.
#[test]
fn nothing_traps_on_a_null_handle() {
    unsafe {
        let n = std::ptr::null_mut::<Web>();
        web_tick(n, std::ptr::null(), 0, -1, 0, 0);
        web_release(n);
        web_close(n);
        assert!(web_display(n).is_null());
        assert!(web_writes(n).is_null());
        assert_eq!(web_press(n, 0, 0), 0);
        assert_eq!(web_motion(n, 0, 0), 0);
        assert_eq!(web_grabbing(n), 0);
        assert_eq!(web_channel(n, "cutoff".as_ptr(), 6), -1);
    }
}

#[test]
fn the_page_can_take_bytes_and_give_them_back() {
    unsafe {
        let p = web_alloc(64);
        assert!(!p.is_null());
        std::ptr::write_bytes(p, 0x41, 64);
        assert_eq!(*p, 0x41);
        web_free(p, 64);
        web_free(std::ptr::null_mut(), 0);
    }
}
