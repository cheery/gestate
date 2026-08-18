//! **One frame, written down.**  `board/done/interface-oracle.md`'s second
//! question, answered by Henri on 2026-08-18: *"golden frame, where
//! else it could fit other than this tree?"*
//!
//! The assertions beside this one each pin a claim somebody thought to
//! make.  This pins **everything at once**: every run, every rectangle,
//! its place and its colour, for one window at one size.  A change to
//! what the window says shows up here as a diff a person can read,
//! whether or not anybody predicted it.
//!
//! `doc/atlas/*.png` is the standing argument against committed
//! renderings and it does not carry here, which is why the question was
//! worth asking: a raster is opaque and differs between rasterisers,
//! and this is text produced by this crate alone.
//!
//! **Its blind spot is the whole of F155** and belongs in the same
//! breath as the file: it records what was *emitted*, never what it
//! looked like.  The glyph it replaced passed every assertion anybody
//! would have written — emitted, in the colour it was asked for, and
//! unreadable at 24 lit pixels.
//!
//! Regenerate with `GESTATE_BLESS=1 cargo test --test golden`, and read
//! the diff before keeping it: blessing without reading is how a golden
//! file stops being an oracle and becomes a record of whatever the code
//! does today.

use gestate_editor::document::Document;
use gestate_editor::font::LARGE;
use gestate_editor::furniture::Furniture;
use gestate_editor::view::{frame_with, Item, View};
use gestate_panel::list::Colour;

/// The names, so a diff says `FAINT` and not `#4a5260`.  Anything
/// unnamed prints as hex rather than failing — a new colour should show
/// up in the diff as a change, not as a broken test.
fn name(c: Colour) -> String {
    use gestate_editor::view::*;
    for (n, v) in [("BG", BG), ("INK", INK), ("FAINT", FAINT),
                   ("CURRENT", CURRENT), ("CARET", CARET),
                   ("SELECT", SELECT), ("TROUGH", TROUGH), ("FILL", FILL),
                   ("HANDLE", HANDLE), ("LIVE", LIVE), ("ANGRY", ANGRY),
                   ("SPENT", SPENT), ("AWAY", AWAY), ("CHROME", CHROME)] {
        if c == v {
            return n.to_string();
        }
    }
    format!("#{:02x}{:02x}{:02x}", c.r, c.g, c.b)
}

fn written(f: &gestate_editor::view::Frame) -> String {
    let mut out = String::new();
    for item in &f.items {
        match item {
            Item::Rect { x, y, w, h, c } => out.push_str(
                &format!("rect  {x:5} {y:5}  {w:5}x{h:<5}  {}\n", name(*c))),
            Item::Run { x, y, s, c } => out.push_str(
                &format!("run   {x:5} {y:5}  {:<12}  {s:?}\n", name(*c))),
        }
    }
    out
}

/// A window with something in it: a file with unsaved changes, a
/// transport running, a complaint standing, and the key still being
/// taught.  Chosen so the bar has every readout in it at once, since
/// the bar is where the three changes of 2026-08-17 landed.
fn the_window() -> String {
    let doc = Document::new("volume = 0.4\nstab = lowpassSvf 800 0.7\n");
    let chrome = Furniture::read(
        "status\tapplied\nfile\tdubgate.ges\t1\nplay\t1\t8.0\nbehind\taudition Ctrl-Return");
    let view = View { gutter: true, ..View::fresh(600, 240, 1) };
    written(&frame_with(&doc, &view, &LARGE, &chrome))
}

#[test]
fn the_window_says_what_it_said_yesterday() {
    let here = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests").join("frame.golden");
    let now = the_window();
    if std::env::var("GESTATE_BLESS").is_ok() {
        std::fs::write(&here, &now).expect("write the golden frame");
        return;
    }
    let was = std::fs::read_to_string(&here).unwrap_or_default();
    if was != now {
        let mut said = String::from(
            "the window no longer says what tests/frame.golden records.\n\
             Read the difference; bless it with GESTATE_BLESS=1 only if \
             it is what you meant.\n\n");
        for (n, (a, b)) in was.lines().zip(now.lines()).enumerate() {
            if a != b {
                said.push_str(&format!("line {}:\n  was  {a}\n  now  {b}\n",
                                       n + 1));
            }
        }
        let (wl, nl) = (was.lines().count(), now.lines().count());
        if wl != nl {
            said.push_str(&format!("\nand it draws {nl} things now, not {wl}\n"));
        }
        panic!("{said}");
    }
}
