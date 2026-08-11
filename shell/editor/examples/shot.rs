//! A frame to a PPM — the editor, without a window.
//!
//! `cargo run -p gestate-editor --example shot -- FILE ROW > f.ppm`
use std::io::Write;
use gestate_editor::document::Document;
use gestate_editor::font::{LARGE, SMALL};
use gestate_editor::view::{frame, paint, View, BG};
use gestate_panel::paint::Canvas;

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let text = a.first().map(|p| std::fs::read_to_string(p).unwrap())
        .unwrap_or_else(|| "sound : Sig Float\nsound = sine 220.0\n".into());
    let row: usize = a.get(1).and_then(|s| s.parse().ok()).unwrap_or(0);
    let font = if a.get(2).map(|s| s == "6x13").unwrap_or(false)
        { &SMALL } else { &LARGE };

    let mut d = Document::new(&text);
    let mut v = View { top: 0, left: 0, w: 860, h: 520, gutter: true, scale: 1 };
    d.seek_rowcol(row + 6, 14);
    // A selection to look at, if asked for: three lines and a bit.
    if std::env::var("SHOT_SELECT").is_ok() {
        let a = d.rope().rowpos(row + 4).unwrap() + 6;
        let b = d.rope().rowpos(row + 6).unwrap() + 22;
        d.select(a, b);
    }
    v.top = row;
    let mut c = Canvas::new(v.w, v.h, BG);
    paint(&mut c, &frame(&d, &v, font), font, 1);

    let mut out = Vec::new();
    write!(out, "P6\n{} {}\n255\n", c.w, c.h).unwrap();
    for w in &c.px {
        out.extend([(w >> 16) as u8, (w >> 8) as u8, *w as u8]);
    }
    std::io::stdout().write_all(&out).unwrap();
}
