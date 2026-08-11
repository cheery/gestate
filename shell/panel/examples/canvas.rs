//! A `Sub` tree walked and painted — the canvas half, without a program.
//!
//! `cargo run -p gestate-panel --features substrate --example canvas > c.ppm`
//!
//! The tree is built by hand at the tags a compiled `gui.ges` would
//! give it, so this shows the *walk* rather than the compiler: two
//! faders and an XY pad, which is the pair `spec/substrate.md` says
//! should be written before the combinator set is fixed.

use gestate_panel::paint::{self, Canvas};
use gestate_panel::substrate::{view, SubTags};
use gestate_panel::{list::Colour, panels};
use crust::{Machine, Node, Num};
use std::io::Write;

const T: SubTags = SubTags {
    rect: 10, circle: 11, gap: 12, over: 13, row: 14, column: 15,
    shift: 16, sized: 17, pad: 18, touch_x: 19, touch_y: 20,
    label: 21, cons: 1, nil: 0,
};

fn int(m: &mut Machine, v: i32) -> usize { m.alloc(Node::Num(Num::I(v as i128))) }

fn colour(m: &mut Machine, r: i32, g: i32, b: i32) -> usize {
    let a = vec![int(m, r), int(m, g), int(m, b)];
    m.alloc(Node::Con(99, a))
}

fn rect(m: &mut Machine, w: i32, h: i32, c: (i32, i32, i32)) -> usize {
    let col = colour(m, c.0, c.1, c.2);
    let a = vec![int(m, w), int(m, h), col];
    m.alloc(Node::Con(T.rect, a))
}

fn con(m: &mut Machine, tag: i64, args: Vec<usize>) -> usize {
    m.alloc(Node::Con(tag, args))
}

/// A fader: a track with a handle shifted along it, in a declared box,
/// listening on its own channel.
fn fader(m: &mut Machine, chan: i64, at: i32) -> usize {
    let track = rect(m, 16, 120, (0x24, 0x28, 0x30));
    let handle = rect(m, 24, 10, (0x5c, 0xa8, 0xd8));
    let (zx, zy) = (int(m, 0), int(m, at));
    let moved = con(m, T.shift, vec![zx, zy, handle]);
    let stack = con(m, T.over, vec![track, moved]);
    let (bw, bh) = (int(m, 40), int(m, 130));
    let boxed = con(m, T.sized, vec![bw, bh, stack]);
    let ch = m.alloc(Node::Chan(chan));
    con(m, T.touch_y, vec![ch, boxed])
}

fn main() {
    let (mut m, _e) = Machine::from_text(
        "crust 1\nblock\nI Unwind\nglobal main 0 0\nentry main\n");

    let a = fader(&mut m, 1, 30);
    let b = fader(&mut m, 2, -20);
    let pad_bg = rect(&mut m, 130, 130, (0x1e, 0x21, 0x27));
    let dot_c = colour(&mut m, 0x5c, 0xd8, 0x9a);
    let r7 = int(&mut m, 7);
    let dot = con(&mut m, T.circle, vec![r7, dot_c]);
    let (dx, dy) = (int(&mut m, 28), int(&mut m, -34));
    let moved_dot = con(&mut m, T.shift, vec![dx, dy, dot]);
    let padded = con(&mut m, T.over, vec![pad_bg, moved_dot]);
    let ch3 = m.alloc(Node::Chan(3));
    let xy = con(&mut m, T.touch_x, vec![ch3, padded]);

    let g = int(&mut m, 24);
    let gap = con(&mut m, T.gap, vec![g, g]);
    let left = con(&mut m, T.row, vec![a, b]);
    let with_gap = con(&mut m, T.row, vec![left, gap]);
    let root = con(&mut m, T.row, vec![with_gap, xy]);

    let (w, h) = (420, 180);
    let d = view(&mut m, &T, root, w, h).expect("the walk");
    eprintln!("{} items, {} attachments:", d.items.len(), d.hits.len());
    for hit in &d.hits {
        eprintln!("   {:?} over {:?}", hit.kind, hit.region);
    }

    let mut c = Canvas::new(w, h, panels::BG);
    paint::paint(&mut c, &d);
    let mut out = Vec::new();
    write!(out, "P6\n{} {}\n255\n", c.w, c.h).unwrap();
    for word in &c.px {
        out.push((word >> 16) as u8);
        out.push((word >> 8) as u8);
        out.push(*word as u8);
    }
    let _ = Colour::rgb(0, 0, 0);
    std::io::stdout().write_all(&out).unwrap();
}
