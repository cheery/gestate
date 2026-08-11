//! How long a frame takes.  Not a benchmark harness — a number.
use std::time::Instant;
use gestate_editor::document::Document;
use gestate_editor::font::LARGE;
use gestate_editor::view::{frame, View};

fn main() {
    let text: String = (0..200_000).map(|i| format!("line {i} of a long file\n")).collect();
    let t0 = Instant::now();
    let mut d = Document::new(&text);
    println!("load {} chars, {} rows: {:?}", d.len(), d.rows(), t0.elapsed());

    let mut v = View { top: 0, left: 0, w: 1200, h: 50 * LARGE.h, gutter: true, scale: 1 };
    for top in [0usize, 100, 100_000, 199_000] {
        v.top = top;
        let t = Instant::now();
        let f = frame(&d, &v, &LARGE);
        println!("  frame at row {top:>6}: {:>10?}  ({} items)", t.elapsed(), f.items.len());
    }
    let t = Instant::now();
    d.seek_rowcol(150_000, 4);
    println!("  seek to row 150000: {:?}", t.elapsed());
    let t = Instant::now();
    d.insert("x").unwrap();
    println!("  one keystroke:      {:?}", t.elapsed());
    let t = Instant::now();
    for _ in 0..100 { d.insert("y").unwrap(); }
    println!("  100 keystrokes:     {:?}", t.elapsed());
    v.top = 150_000;
    let t = Instant::now();
    let f = frame(&d, &v, &LARGE);
    println!("  frame after edits:  {:?} ({} items)", t.elapsed(), f.items.len());
}
