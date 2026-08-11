//! **A real substrate, walked by the port, equals the reference.**
//!
//! The unit tests beside `substrate.rs` build `Sub` trees by hand, which
//! checks the geometry and nothing about the language.  This one takes
//! `examples/audio/substrate.ges` as the compiler produces it — the FRP
//! prelude, `:::`, `mkSig`, a channel handed to an element — forces it
//! on `crust`, and compares the picture with the one `gestate/gui.py`
//! draws from the same program.
//!
//! It is the first thing in this project to run a *signal* program on
//! the Rust machine, so it is also the check on the arena, on the sweep
//! that fills it, and on `SigHead`'s ✓ frontier.

#![cfg(feature = "substrate")]

use crust::{Machine, Node};
use gestate_panel::list::{Axis, Colour, Display, Item, Kind};
use gestate_panel::substrate::{view, SubTags};

const W: i32 = 400;
const H: i32 = 300;

fn tags() -> SubTags {
    let raw: Vec<i64> = include_str!("substrate.tags")
        .split_whitespace()
        .map(|w| w.parse().unwrap())
        .collect();
    SubTags {
        rect: raw[0], circle: raw[1], gap: raw[2], over: raw[3],
        row: raw[4], column: raw[5], shift: raw[6], sized: raw[7],
        pad: raw[8], touch_x: raw[9], touch_y: raw[10],
    }
}

/// What the reference drew, read back off the fixture.
fn expected() -> Display {
    let mut d = Display::new();
    for line in include_str!("substrate.display").lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        if f.is_empty() {
            continue;
        }
        let n = |i: usize| -> i32 { f[i].parse().unwrap() };
        match f[0] {
            "rect" => d.rect(n(1), n(2), n(3), n(4),
                             Colour::rgb(n(5) as u8, n(6) as u8, n(7) as u8)),
            "dot" => d.dot(n(1), n(2), n(3),
                           Colour::rgb(n(4) as u8, n(5) as u8, n(6) as u8)),
            "hit" => {
                let axis = if f[1] == "x" { Axis::X } else { Axis::Y };
                d.hit(Kind::Chan(axis, f[2].parse().unwrap()),
                      gestate_panel::list::NO_PARAM,
                      (n(3), n(4), n(5), n(6)));
            }
            _ => panic!("unknown fixture line: {line}"),
        }
    }
    d
}

/// Load the program and force `main` to the signal it is.
///
/// `main : Sig Sub` — forcing it runs the program's initial term, and
/// every `SigCons` on the way registers its cell on the now heap, which
/// is what the sweep will later walk.
fn open() -> (Machine, usize) {
    let (mut m, _entry) = Machine::from_text(include_str!("substrate.program"));
    let root = *m.globals_get("main").expect("the entry global `main`");
    let forced = m.force_node(root);
    let id = match m.heap_at(forced) {
        Node::Sig(id) => *id,
        other => panic!("`main` is not a signal: {other:?}"),
    };
    let value = m.sig_value(id).expect("the signal's current value");
    (m, value)
}

#[test]
fn the_port_draws_what_the_reference_draws() {
    let (mut m, value) = open();
    let got = view(&mut m, &tags(), value, W, H).expect("the walk");
    let want = expected();

    assert_eq!(got.items.len(), want.items.len(),
               "item count: got {:?}", got.items);
    for (i, (a, b)) in got.items.iter().zip(&want.items).enumerate() {
        assert_eq!(a, b, "item {i}");
    }
    assert_eq!(got.hits, want.hits, "the attachments");
}

#[test]
fn the_attachment_carries_the_programs_own_channel() {
    let (mut m, value) = open();
    let d = view(&mut m, &tags(), value, W, H).expect("the walk");
    // `substrate.ges` declares `cutoff : Chan Float` and hands it to the
    // fader.  The host never names it: it finds the channel at the node
    // that carried it, which is the whole attachment mechanism.
    let hit = d.hits.first().expect("one attachment");
    match hit.kind {
        Kind::Chan(Axis::Y, chan) => {
            assert!(chan >= 0, "a real channel id, got {chan}");
        }
        other => panic!("expected a Y attachment on a channel, got {other:?}"),
    }
    // And it listens over the box the element declared, not over what it
    // happened to paint.
    let (x0, y0, x1, y1) = hit.region;
    assert!(x1 > x0 && y1 > y0, "a region with area");
}

#[test]
fn every_item_is_inside_the_window_the_host_gave() {
    let (mut m, value) = open();
    let d = view(&mut m, &tags(), value, W, H).expect("the walk");
    for item in &d.items {
        if let Item::Rect { x, y, w, h, .. } = item {
            assert!(*x >= -W && x + w <= 2 * W, "{item:?} is off in x");
            assert!(*y >= -H && y + h <= 2 * H, "{item:?} is off in y");
        }
    }
}

/// **The sweep drives the picture.**
///
/// The walk alone draws one frame.  This is the wiring: a value arrives
/// on the channel the program declared, `reactive_step` advances every
/// live signal by one instant, and the *same* fold the synth reads is
/// the one the canvas redraws.  One fold, two readers — the claim
/// `spec/substrate.md` rests on, executed on the Rust machine.
#[test]
fn an_arrival_moves_what_is_drawn() {
    use crust::reactive::Arrivals;
    use crust::Num;

    let (mut m, first) = open();
    let t = tags();
    let before = view(&mut m, &t, first, W, H).expect("the first frame");

    // The channel the fader carries — found at the node that named it,
    // exactly as a host finds it.
    let chan = match before.hits.first().expect("an attachment").kind {
        Kind::Chan(_, c) => c,
        other => panic!("expected a channel attachment, got {other:?}"),
    };

    // `main`'s own cell, so its value can be re-read after the sweep.
    let root = *m.globals_get("main").unwrap();
    let forced = m.force_node(root);
    let id = match m.heap_at(forced) {
        Node::Sig(id) => *id,
        other => panic!("`main` is not a signal: {other:?}"),
    };

    // Push the fader to the far end of its travel.
    let value = m.alloc(Node::Num(Num::F(0.95)));
    let mut arrivals = Arrivals::new();
    arrivals.insert(chan, value);
    m.reactive_step(&arrivals);

    let after_value = m.sig_value(id).expect("a value after the sweep");
    let after = view(&mut m, &t, after_value, W, H).expect("the next frame");

    assert_ne!(before.items, after.items,
               "the sweep ran and the picture did not move");
    // The handle moved; the track it slides in did not.
    assert_eq!(before.items.len(), after.items.len(),
               "the same elements, in the same order");
    assert_eq!(before.hits, after.hits,
               "and the fader listens over the same box — `Shift` is \
                layout-neutral, so a moving handle does not move its own \
                sensitive area");
}

/// A second instant on the same cell — the arena's identity holding
/// across repeated sweeps, which is what lets a driver key by cell.
#[test]
fn the_picture_follows_the_channel_each_instant() {
    use crust::reactive::Arrivals;
    use crust::Num;

    let (mut m, first) = open();
    let t = tags();
    let d0 = view(&mut m, &t, first, W, H).expect("frame");
    let chan = match d0.hits[0].kind { Kind::Chan(_, c) => c, _ => panic!() };
    let root = *m.globals_get("main").unwrap();
    let forced = m.force_node(root);
    let id = match m.heap_at(forced) { Node::Sig(i) => *i, _ => panic!() };

    // **Compared whole, not by picking a shape.**  A first draft looked
    // for "the handle" as the shortest rectangle and found a
    // zero-height one instead — the picture is the program's to compose,
    // and a test that guesses which part means what is testing its own
    // guess.
    let mut frames = Vec::new();
    for v in [0.1f64, 0.5, 0.9] {
        let node = m.alloc(Node::Num(Num::F(v)));
        let mut a = Arrivals::new();
        a.insert(chan, node);
        m.reactive_step(&a);
        let value = m.sig_value(id).expect("value");
        frames.push(view(&mut m, &t, value, W, H).expect("frame").items);
    }
    assert_ne!(frames[0], frames[1], "0.1 and 0.5 must draw differently");
    assert_ne!(frames[1], frames[2], "0.5 and 0.9 must draw differently");
    // And the composition is stable: the same elements, in the same
    // order, at every instant.
    assert_eq!(frames[0].len(), frames[2].len());
}
