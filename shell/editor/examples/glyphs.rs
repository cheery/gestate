//! Look at the font.  `cargo run -p gestate-editor --example glyphs -- 10x20 "text"`
//!
//! The letters are the one thing in this crate a test cannot really
//! check — `an_a_looks_like_an_a` pins that an `A` has stems and a
//! crossbar, and whether it is *legible* is a thing a person has to see.

use gestate_editor::font::{Font, LARGE, SMALL};

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let f: &Font = match args.first().map(|s| s.as_str()) {
        Some("6x13") => &SMALL,
        _ => &LARGE,
    };
    let text = args.get(1).cloned()
        .unwrap_or_else(|| "gestate — sound ✓ δϕκ åäö 日本".into());
    println!("{}x{}, ascent {}, {} glyphs", f.w, f.h, f.ascent, f.count());
    for y in 0..f.h {
        let line: String = text.chars().map(|ch| {
            let g = f.glyph(ch);
            (0..f.w).map(|x| if g.on(x, y) { '#' } else { '.' })
                .collect::<String>()
        }).collect::<Vec<_>>().join("");
        println!("{}{line}", if y == f.ascent { "" } else { "" });
    }
}
