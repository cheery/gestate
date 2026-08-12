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
/// `gui.py`'s `_flatten` walks from `cx = cy = 0` — the walk is
/// origin-relative, and *where the origin lands is the host's to say*
/// (both hosts say the middle of their pane; `Panel::canvas_origin`
/// tells that story).  The fixture beside this file is the bare walk,
/// so comparing against it pins the tree's own geometry with no host
/// in the room: items straddle the origin, which is what a program
/// placed by its centre looks like before a host has said where the
/// centre is.
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
        pad: raw[8], touch_x: raw[9], touch_y: raw[10], label: raw[11],
        cons: raw[12], nil: raw[13],
    }
}

/// What the reference drew, read back off a fixture.
fn drawn(fixture: &str) -> Display {
    let mut d = Display::new();
    for line in fixture.lines() {
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
            // `text x y scale r g b WORDS` — the words run to the end of
            // the line, so a caption may hold spaces.
            "text" => d.text(n(1), n(2), &f[7..].join(" "),
                             Colour::rgb(n(4) as u8, n(5) as u8, n(6) as u8),
                             n(3)),
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

fn expected() -> Display {
    drawn(include_str!("substrate.display"))
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

// ── A file with both halves ──────────────────────────────────────────────

/// `examples/audio/lantern.ges`: an unfolding score *and* a canvas, in
/// one plugin.  Two faders, both bridged to knobs the synth reads.
fn lantern() -> CanvasProgram {
    let raw: Vec<i64> = include_str!("lantern.tags")
        .split_whitespace().map(|w| w.parse().unwrap()).collect();
    CanvasProgram {
        text: include_str!("lantern.program").to_string(),
        entry: "main".to_string(),
        tags: SubTags {
            rect: raw[0], circle: raw[1], gap: raw[2], over: raw[3],
            row: raw[4], column: raw[5], shift: raw[6], sized: raw[7],
            pad: raw[8], touch_x: raw[9], touch_y: raw[10],
            label: raw[11], cons: raw[12], nil: raw[13],
        },
        chans: vec!["warmthChan".into(), "glowChan".into(), "peak".into()],
        // The slots `export.substrate_of` reports for this file.
        bridge: vec![("warmthChan".into(), 4), ("glowChan".into(), 29)],
    }
}

fn lantern_panel() -> Panel {
    let mut p = Panel::with_scale(
        Model { title: "LANTERN".into(), ..Default::default() }, 100);
    p.resize(440, 380);
    p.attach_canvas(Canvas::open(lantern()).expect("the canvas opened"));
    p.set_tab(Tab::Canvas);
    p.tick_canvas(&[]);
    p
}

#[test]
fn one_file_can_carry_two_faders_and_a_meter() {
    let p = lantern_panel();
    let d = p.canvas().expect("attached").display();
    assert_eq!(d.hits.len(), 2, "two faders, two attachments");
    // Two faders, eight meter segments, and the fills behind them.
    assert!(d.items.len() >= 14, "drew {} items", d.items.len());
}

/// **The handle follows the finger.**
///
/// `onTouchY` reports 0 at the *top* edge and 1 at the bottom — that is
/// what the host measures and there is nowhere else for it to come
/// from.  A fader drawn the other way round looks perfectly fine
/// standing still and runs backwards the moment you drag it, which is
/// exactly how this shipped for an afternoon.  So: press near the top,
/// get a low value; press near the bottom, get a high one.
#[test]
fn pressing_low_on_a_fader_gives_a_high_value() {
    let mut p = lantern_panel();
    let hit = p.canvas().unwrap().display().hits[0];
    let (x0, y0, x1, y1) = hit.region;
    let x = (x0 + x1) / 2;

    let at = |p: &mut Panel, y: i32| -> f64 {
        let out = p.press(x, y);
        p.release();
        out.iter().find_map(|c| match c {
            Change::Value(_, v) => Some(*v),
            _ => None,
        }).expect("a value")
    };
    let top = at(&mut p, y0 + 2);
    let mid = at(&mut p, (y0 + y1) / 2);
    let low = at(&mut p, y1 - 2);
    assert!(top < 0.1, "the top of the travel read {top}");
    assert!((0.45..0.55).contains(&mid), "the middle read {mid}");
    assert!(low > 0.9, "the bottom of the travel read {low}");
}

/// And the picture goes the same way as the number.
///
/// The two could disagree — the fill is drawn by the *program* and the
/// value is measured by the *host* — and when they do, the handle
/// crosses the pointer.  Checked by where the bright handle lands, not
/// by the value that produced it.
#[test]
fn the_handle_is_drawn_where_the_finger_pressed() {
    let mut p = lantern_panel();
    let hit = p.canvas().unwrap().display().hits[0];
    let (x0, y0, x1, y1) = hit.region;
    let x = (x0 + x1) / 2;

    // The handle is the one bone-coloured rectangle inside this fader.
    let handle_y = |p: &Panel| -> i32 {
        p.canvas().unwrap().display().items.iter().find_map(|i| match i {
            Item::Rect { x: rx, y, w, c, .. }
                if *c == Colour::rgb(232, 236, 244)
                    && *rx < x && rx + w > x => Some(*y),
            _ => None,
        }).expect("a handle")
    };
    p.press(x, y0 + 6);
    p.release();
    let high = handle_y(&p);
    p.press(x, y1 - 6);
    p.release();
    let low = handle_y(&p);
    assert!(low > high,
            "pressing lower drew the handle higher ({high} then {low})");
}

/// Both faders reach the host, on the parameters the export paired them
/// with — and a press on one does not move the other.
#[test]
fn each_fader_writes_its_own_parameter() {
    let mut p = lantern_panel();
    let hits = p.canvas().unwrap().display().hits.clone();
    let mut params = Vec::new();
    for hit in &hits {
        let (x0, y0, x1, y1) = hit.region;
        let out = p.press((x0 + x1) / 2, (y0 + y1) / 2);
        p.release();
        let ids: Vec<u32> = out.iter().filter_map(|c| match c {
            Change::Value(id, _) => Some(*id),
            _ => None,
        }).collect();
        assert_eq!(ids.len(), 1, "one press, one parameter: {out:?}");
        params.push(ids[0]);
    }
    params.sort_unstable();
    assert_eq!(params, vec![4, 29], "the knobs `warmth` and `glow`");
}

/// **The port fits letters into a box exactly as the reference does.**
///
/// A label is the first thing in this vocabulary whose *appearance* is
/// computed rather than declared: the box is the program's, but how big
/// the glyphs come out is arithmetic, and two hosts with different
/// fonts have to reach the same answer without either measuring one.
/// `gui.ges` states the rule beside the constructor; `gui.py::_fit` and
/// `substrate::fit` are the two implementations, and this is what holds
/// them equal on a real file.
#[test]
fn the_port_fits_a_label_the_way_the_reference_fits_it() {
    let (mut m, _e) = Machine::from_text(include_str!("lantern.program"));
    let root = *m.globals_get("main").expect("`main`");
    let forced = m.force_node(root);
    let id = match m.heap_at(forced) {
        Node::Sig(id) => *id,
        other => panic!("`main` is not a signal: {other:?}"),
    };
    let value = m.sig_value(id).expect("a value");
    let t = lantern_tags();
    let got = reference(&mut m, &t, value).expect("the walk");
    let want = drawn(include_str!("lantern.display"));

    assert_eq!(got.items.len(), want.items.len(),
               "item count: got {:?}", got.items);
    for (i, (a, b)) in got.items.iter().zip(&want.items).enumerate() {
        assert_eq!(a, b, "item {i}");
    }
    assert_eq!(got.hits, want.hits, "the attachments");

    // And there really are labels in it, or the test above is checking
    // that two pictures with no text agree about text.
    let texts: Vec<&Item> = got.items.iter()
        .filter(|i| matches!(i, Item::Text { .. })).collect();
    assert_eq!(texts.len(), 3, "WARMTH, GLOW and PEAK");
}

fn lantern_tags() -> SubTags {
    let raw: Vec<i64> = include_str!("lantern.tags")
        .split_whitespace().map(|w| w.parse().unwrap()).collect();
    SubTags {
        rect: raw[0], circle: raw[1], gap: raw[2], over: raw[3],
        row: raw[4], column: raw[5], shift: raw[6], sized: raw[7],
        pad: raw[8], touch_x: raw[9], touch_y: raw[10], label: raw[11],
        cons: raw[12], nil: raw[13],
    }
}

/// **A label reserves the box it declared, not the box it filled.**
///
/// This is the whole reason a label is admissible where a text editor
/// was not (`spec/editor.md`): the language cannot measure text, so
/// nothing in a layout may depend on what a font did.  A caption that
/// grew its own extent when its string got longer would put measuring
/// back in the middle of layout by the back door — and the neighbour in
/// the `row` would shuffle when a word changed.
#[test]
fn a_labels_extent_is_its_box_whatever_it_says() {
    use gestate_panel::substrate::{extent, fit};
    let (mut m, _e) = Machine::from_text(include_str!("lantern.program"));
    let root = *m.globals_get("main").unwrap();
    let forced = m.force_node(root);
    let id = match m.heap_at(forced) { Node::Sig(i) => *i, _ => panic!() };
    let value = m.sig_value(id).unwrap();
    let t = lantern_tags();
    let whole = extent(&mut m, &t, value).expect("an extent");

    // `WARMTH` is six characters and `GLOW` is four, in boxes of the
    // same declared width — so the picture is the same size either way.
    assert_eq!(fit(44, 9, 6), fit(44, 9, 4),
               "a longer caption changed how big the letters came out                 in the same box");
    assert!(whole.0 > 0 && whole.1 > 0);
}

/// The failure an author can see: a box too small still draws, at one,
/// and overflows.  Silence would be the wrong answer — a caption that
/// vanished when its box was a pixel short is a bug you cannot find.
#[test]
fn a_label_too_big_for_its_box_is_drawn_anyway() {
    use gestate_panel::substrate::fit;
    assert_eq!(fit(4, 4, 12), 1);
    assert_eq!(fit(0, 0, 3), 1);
    assert_eq!(fit(100, 100, 0), 1, "an empty caption has no width to fit");
}

/// **A caption reaches the window a plugin opens.**
///
/// The parity test above compares two walks; this checks the whole
/// path a DAW takes — the program as the export sends it, opened
/// through `Canvas`, ticked by the panel, and drawn on the tab.  A
/// label that crossed but did not survive `CanvasProgram`'s tag
/// translation would pass every test before this one.
#[test]
fn the_panel_shows_the_captions_the_program_wrote() {
    let p = lantern_panel();
    let words: Vec<String> = p.canvas().expect("attached").display()
        .items.iter().filter_map(|i| match i {
            Item::Text { s, .. } => Some(s.clone()),
            _ => None,
        }).collect();
    assert_eq!(words, vec!["WARMTH", "GLOW", "PEAK"]);
}

/// And a caption is drawn, not merely listed.
///
/// The painter is the one thing a display-list comparison cannot check,
/// and a `Text` item whose glyphs never reached the buffer would look
/// identical in every assertion above.
#[test]
fn a_caption_puts_ink_on_the_canvas() {
    let mut p = lantern_panel();
    let lit = |p: &Panel| -> usize {
        p.render().px.iter()
            .filter(|w| **w == gestate_panel::list::Colour::rgb(122, 130, 142)
                             .word())
            .count()
    };
    let with = lit(&p);
    assert!(with > 40, "only {with} caption pixels — the words are not drawn");
    // Nothing else on this canvas uses the caption's grey, so removing
    // the labels must remove exactly those pixels.
    p.set_tab(Tab::Controls);
    assert_eq!(lit(&p), 0, "the caption's ink is on the other tab too");
}
