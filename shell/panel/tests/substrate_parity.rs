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
use gestate_panel::substrate::{view_at, SubTags};

const W: i32 = 400;
const H: i32 = 300;

/// **The reference's own origin.**
///
/// `gui.py`'s `_flatten` walks from `cx = cy = 0`: a substrate's centre
/// sits at the window's corner and the program places itself from
/// there — `substrate.ges` opens with `moveXY 120 140` for exactly
/// that reason.  The fixture beside this file is that walk, so
/// comparing against it pins the convention rather than only the
/// arithmetic.  A host that centred instead would add half a window to
/// an offset the program had already applied, and every canvas would
/// come out down and to the right of where its author put it.
fn reference(m: &mut Machine, t: &SubTags, root: usize)
    -> Result<Display, gestate_panel::substrate::SubError>
{
    view_at(m, t, root, 0, 0)
}

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
    let got = reference(&mut m, &tags(), value).expect("the walk");
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
    let d = reference(&mut m, &tags(), value).expect("the walk");
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

/// Nothing runs away.  A walk that lost its transform draws at
/// coordinates no window could hold, and a bound this loose still
/// catches that while leaving the program free to compose where it
/// likes.
#[test]
fn every_item_lands_somewhere_a_window_could_show() {
    let (mut m, value) = open();
    let d = reference(&mut m, &tags(), value).expect("the walk");
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
    let before = reference(&mut m, &t, first).expect("the first frame");

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
    let after = reference(&mut m, &t, after_value).expect("the next frame");

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
    let d0 = reference(&mut m, &t, first).expect("frame");
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
        frames.push(reference(&mut m, &t, value).expect("frame").items);
    }
    assert_ne!(frames[0], frames[1], "0.1 and 0.5 must draw differently");
    assert_ne!(frames[1], frames[2], "0.5 and 0.9 must draw differently");
    // And the composition is stable: the same elements, in the same
    // order, at every instant.
    assert_eq!(frames[0].len(), frames[2].len());
}

// ── The canvas, live in a panel ──────────────────────────────────────────

use gestate_panel::canvas::{Canvas, CanvasProgram};
use gestate_panel::interact::Change;
use gestate_panel::model::{Model, Tab};
use gestate_panel::Panel;

/// The program as the export sends it.
///
/// `cutoff` is channel 0 and control slot 0 in `substrate.ges`, so the
/// bridge is `(0, 0)` — which `test_export.py` derives from the graph
/// rather than asserting, and which is restated here as the fixture
/// this side is written against.
fn program() -> CanvasProgram {
    CanvasProgram {
        text: include_str!("substrate.program").to_string(),
        entry: "main".to_string(),
        tags: tags(),
        chans: vec!["cutoff".into(), "peak".into()],
        bridge: vec![("cutoff".into(), 0)],
    }
}

fn panel() -> Panel {
    let mut p = Panel::with_scale(
        Model { title: "SUBSTRATE".into(), ..Default::default() }, 100);
    p.resize(400, 340);
    p.attach_canvas(Canvas::open(program()).expect("the canvas opened"));
    assert!(p.set_tab(Tab::Canvas));
    p.tick_canvas(&[]);
    p
}

/// **A frame draws, and the next frame draws what changed.**
///
/// The loop this whole stack exists for: a hand writes a channel, the
/// sweep advances the fold, the walk redraws it.  Everything before
/// this was a test of one half at a time.
#[test]
fn the_panel_draws_the_programs_own_picture() {
    let p = panel();
    let d = p.canvas().expect("attached").display();
    assert!(!d.items.is_empty(), "the canvas drew nothing");
    assert_eq!(d.hits.len(), 1, "one fader, one attachment");
}

/// A press on the fader moves the picture **and** tells the host.
///
/// The two halves of "one fold, two readers": the channel write is
/// what the canvas sees, the `Change` is what the synth will hear —
/// and they are one gesture, so the DAW gets one undo step.
#[test]
fn a_touch_moves_the_picture_and_the_parameter_together() {
    let mut p = panel();
    let hit = p.canvas().unwrap().display().hits[0];
    let (x0, y0, x1, y1) = hit.region;
    let before = p.canvas().unwrap().display().items.clone();

    // Press near the bottom of the fader's travel.
    let out = p.press((x0 + x1) / 2, y0 + (y1 - y0) * 4 / 5);
    let after = p.canvas().unwrap().display().items.clone();

    assert_ne!(before, after, "the picture did not follow the hand");
    assert!(matches!(out.first(), Some(Change::Begin(0))),
            "expected a gesture on parameter 0, got {out:?}");
    let Some(Change::Value(0, v)) = out.get(1) else {
        panic!("no value in {out:?}");
    };
    assert!((0.7..=0.9).contains(v), "the fraction was {v}");

    let end = p.release();
    assert_eq!(end, vec![Change::End(0)], "one gesture, closed once");
}

/// A drag that leaves the element still reaches it — **a press
/// grabs**, which is what a fader is.
#[test]
fn a_drag_off_the_fader_still_moves_it() {
    let mut p = panel();
    let (x0, y0, x1, y1) = p.canvas().unwrap().display().hits[0].region;
    p.press((x0 + x1) / 2, (y0 + y1) / 2);
    // Well outside the element, in both axes.
    let out = p.motion(x1 + 300, y0 + 4);
    let Some(Change::Value(0, v)) = out.first() else {
        panic!("the grab was dropped: {out:?}");
    };
    assert!(*v <= 0.1, "clamped to the top of its own travel, got {v}");
}

/// The instrument reaching the canvas, rather than a hand: `peak` is
/// written by the host and the meter follows.
#[test]
fn the_host_can_write_a_channel_the_program_declared() {
    let mut p = panel();
    let peak = p.canvas_channel("peak").expect("`peak` is declared");
    let quiet = p.canvas().unwrap().display().items.clone();
    p.tick_canvas(&[(peak, 0.9)]);
    let loud = p.canvas().unwrap().display().items.clone();
    assert_ne!(quiet, loud, "the meter ignored the level");
}

/// A channel with no control behind it produces no parameter change.
///
/// `peak` is the counter-example that keeps the bridge honest: it is
/// as real a channel as `cutoff`, and it is the *host's* to write.
#[test]
fn an_unbridged_channel_tells_the_host_nothing() {
    let c = Canvas::open(program()).expect("opened");
    let cutoff = c.channel("cutoff").expect("declared");
    let peak = c.channel("peak").expect("declared");
    assert_eq!(c.param_of(cutoff), Some(0), "`cutoff` is a control");
    assert_eq!(c.param_of(peak), None, "`peak` is not");
}

/// Switching tabs does not disturb the fold.
///
/// A substrate is a fold over time; one that stopped folding while
/// hidden would come back showing a stale world and then jump.
#[test]
fn the_canvas_keeps_folding_on_the_other_tab() {
    let mut p = panel();
    let peak = p.canvas_channel("peak").unwrap();
    p.set_tab(Tab::Controls);
    let before = p.canvas().unwrap().display().items.clone();
    p.tick_canvas(&[(peak, 0.8)]);
    let after = p.canvas().unwrap().display().items.clone();
    assert_ne!(before, after, "the hidden canvas stopped folding");
}

/// The picture sits under the toolbar, not behind it.
#[test]
fn the_canvas_is_drawn_under_the_toolbar_rather_than_behind_it() {
    let p = panel();
    let top = gestate_panel::panels::toolbar_h(&p.model, p.scale());
    assert!(top > 0, "a canvas gives the window a toolbar");
    for item in &p.canvas().unwrap().display().items {
        if let Item::Rect { y, h, .. } = item {
            assert!(y + h > top,
                    "{item:?} is drawn entirely under the toolbar");
        }
    }
}
