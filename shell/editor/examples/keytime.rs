//! What one keystroke costs, on the path the window actually takes.
use std::time::Instant;
use gestate_editor::document::Document;
use gestate_editor::font::LARGE;
use gestate_editor::keys::{press, Key, Mods};
use gestate_editor::view::{frame, paint, View, BG};
use gestate_panel::paint::Canvas;

fn main() {
    let path = std::env::args().nth(1);
    let text = match &path {
        Some(p) => std::fs::read_to_string(p).unwrap(),
        None => "sound : Sig Float\nsound = sine 220.0\n".repeat(4),
    };
    let mut d = Document::new(&text);
    let mut v = View { top: 0, left: 0, w: 1000, h: 700, gutter: true, aside: 0, scale: 1 };
    println!("{} chars, {} rows, {} visible", d.len(), d.rows(), v.rows(&LARGE));

    let t = Instant::now();
    for c in "hello world".chars() {
        press(&mut d, &mut v, &LARGE, Key::Char(c), Mods::default());
    }
    println!("  11 keys, keys::press only : {:?}", t.elapsed());

    // What `after()` does on every edit.
    let t = Instant::now();
    for _ in 0..11 { std::hint::black_box(d.text()); }
    println!("  11 × doc.text()           : {:?}   <-- the host callback", t.elapsed());

    let t = Instant::now();
    let mut n = 0usize;
    for _ in 0..11 {
        let f = frame(&d, &v, &LARGE);
        n += f.items.len();
    }
    println!("  11 × frame()              : {:?}  ({n} items)", t.elapsed());

    let t = Instant::now();
    for _ in 0..11 {
        let mut c = Canvas::new(v.w, v.h, BG);
        paint(&mut c, &frame(&d, &v, &LARGE), &LARGE, 1);
        std::hint::black_box(&c.px[0]);
    }
    println!("  11 × full repaint         : {:?}", t.elapsed());
}
