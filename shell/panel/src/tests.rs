//! What the panel promises, checked without a window.
//!
//! `spec/panel.md`'s acceptance list, minus the two clauses that need a
//! host (1 and 6 live in `test_export.py`, where the plugin is already
//! driven by a miniature CLAP host).

use crate::interact::Change;
use crate::list::{Axis, Colour};
use crate::model::{Accepts, BankView, Knob, Model};
use crate::{paint, panels, Panel};

fn knob(name: &str, param: u32, value: f64) -> Knob {
    Knob { name: name.into(), param, value, min: 0.0, max: 1.0,
           integer: false }
}

fn model() -> Model {
    Model {
        title: "TESTSYNTH".into(),
        knobs: vec![knob("cutoff", 0, 0.25), knob("drive", 1, 0.5)],
        banks: vec![BankView {
            name: "lead".into(),
            voices: 6,
            accepts: Accepts::Table {
                levels: 2,
                // Keys 60..72 accepted at both levels, 48..60 at one,
                // everything else declined.
                ok: (0..128 * 2)
                    .map(|i| {
                        let (k, l) = (i / 2, i % 2);
                        (60..72).contains(&k) || ((48..60).contains(&k) && l == 0)
                    })
                    .collect(),
            },
        }],
    }
}

// ── Acceptance 2: the display list is a pure function of the model ──

#[test]
fn the_same_model_draws_the_same_list() {
    let m = model();
    assert_eq!(panels::view(&m, 600, None), panels::view(&m, 600, None));
}

#[test]
fn a_model_with_no_knobs_draws_no_hits() {
    let m = Model { title: "T".into(), knobs: vec![], banks: vec![] };
    assert!(panels::view(&m, 600, None).hits.is_empty());
}

#[test]
fn the_window_size_follows_the_descriptor() {
    let two = Panel::new(model());
    let mut big = model();
    for i in 2..10 {
        big.knobs.push(knob("extra", i, 0.0));
    }
    assert!(Panel::new(big).height > two.height,
            "more knobs must want a taller window");
}

// ── Acceptance 4: one BEGIN, values, one END ────────────────────────

/// The centre of the first knob's track, from the layout itself rather
/// than from a guess about the constants.
fn track_point(p: &Panel, param: u32, frac: f64) -> (i32, i32) {
    let h = p.display().hits.iter().find(|h| h.param == param).unwrap();
    let (x0, y0, x1, y1) = h.region;
    (x0 + ((x1 - x0) as f64 * frac) as i32, (y0 + y1) / 2)
}

#[test]
fn a_drag_is_one_gesture() {
    let mut p = Panel::new(model());
    let (x, y) = track_point(&p, 0, 0.25);

    let mut all = p.press(x, y);
    for step in 1..6 {
        let (mx, _) = track_point(&p, 0, 0.25 + step as f64 * 0.1);
        all.extend(p.motion(mx, y));
    }
    all.extend(p.release());

    assert_eq!(all.iter().filter(|c| matches!(c, Change::Begin(0))).count(), 1);
    assert_eq!(all.iter().filter(|c| matches!(c, Change::End(0))).count(), 1);
    assert!(matches!(all.first(), Some(Change::Begin(0))));
    assert!(matches!(all.last(), Some(Change::End(0))));
    assert!(all.iter().any(|c| matches!(c, Change::Value(0, _))));
}

#[test]
fn motion_without_a_press_says_nothing() {
    let mut p = Panel::new(model());
    let (x, y) = track_point(&p, 0, 0.5);
    assert!(p.motion(x, y).is_empty());
    assert!(p.release().is_empty());
}

#[test]
fn a_press_off_every_track_says_nothing() {
    let mut p = Panel::new(model());
    assert!(p.press(2, 2).is_empty(), "the title bar is not a knob");
}

#[test]
fn a_drag_that_wanders_keeps_its_own_knob() {
    let mut p = Panel::new(model());
    let (x0, y0) = track_point(&p, 0, 0.1);
    p.press(x0, y0);
    // Straight down onto the second knob's row, far right.
    let (x1, y1) = track_point(&p, 1, 0.9);
    let out = p.motion(x1, y1);
    assert!(out.iter().all(|c| matches!(c, Change::Value(0, _))),
            "a drag must not hand itself to the knob it wandered over");
}

#[test]
fn a_value_that_did_not_move_is_not_resent() {
    let mut p = Panel::new(model());
    let (x, y) = track_point(&p, 0, 0.4);
    p.press(x, y);
    assert!(p.motion(x, y).is_empty(), "the same point is not a change");
}

#[test]
fn an_integer_knob_steps() {
    let mut m = model();
    m.knobs[0] = Knob { name: "mode".into(), param: 0, value: 0.0, min: 0.0,
                        max: 4.0, integer: true };
    let mut p = Panel::new(m);
    let (x, y) = track_point(&p, 0, 0.55);
    let out = p.press(x, y);
    let Some(Change::Value(_, v)) = out.get(1) else {
        panic!("expected a value, got {out:?}")
    };
    assert_eq!(*v, v.round(), "an Int control must not land between steps");
}

// ── The fader must not run backwards ────────────────────────────────

#[test]
fn x_grows_rightward_and_y_grows_upward() {
    use crate::list::Hit;
    let hx = Hit { axis: Axis::X, param: 0, region: (0, 0, 100, 20) };
    assert!(hx.fraction(10, 10) < hx.fraction(90, 10));
    let hy = Hit { axis: Axis::Y, param: 0, region: (0, 0, 20, 100) };
    assert!(hy.fraction(10, 90) < hy.fraction(10, 10),
            "a fader grows upward where screen y grows downward");
}

#[test]
fn a_point_outside_the_track_clamps() {
    use crate::list::Hit;
    let h = Hit { axis: Axis::X, param: 0, region: (0, 0, 100, 20) };
    assert_eq!(h.fraction(-50, 10), 0.0);
    assert_eq!(h.fraction(500, 10), 1.0);
}

// ── Acceptance 3: the painter is deterministic and clipped ──────────

#[test]
fn the_same_list_paints_the_same_pixels() {
    let p = Panel::new(model());
    assert_eq!(p.render().px, p.render().px);
}

#[test]
fn painting_off_the_edge_touches_no_other_row() {
    let mut c = paint::Canvas::new(10, 10, Colour::rgb(0, 0, 0));
    let white = Colour::rgb(0xff, 0xff, 0xff);
    // A rect starting past the right edge must not wrap onto row + 1.
    c.fill_rect(9, 0, 40, 1, white);
    assert_eq!(c.get(9, 0), Some(white.word()));
    assert_eq!(c.get(0, 1), Some(0), "a clipped span wrapped into the next row");
}

#[test]
fn a_dot_stays_inside_its_radius() {
    let mut c = paint::Canvas::new(21, 21, Colour::rgb(0, 0, 0));
    let white = Colour::rgb(0xff, 0xff, 0xff);
    c.fill_dot(10, 10, 5, white);
    assert_eq!(c.get(10, 10), Some(white.word()));
    assert_eq!(c.get(10, 5), Some(white.word()), "the top of the circle");
    assert_eq!(c.get(10, 4), Some(0), "one past it");
    assert_eq!(c.get(0, 0), Some(0), "the corner is outside");
}

#[test]
fn a_negative_radius_draws_nothing() {
    let mut c = paint::Canvas::new(5, 5, Colour::rgb(0, 0, 0));
    c.fill_dot(2, 2, -3, Colour::rgb(0xff, 0xff, 0xff));
    assert!(c.px.iter().all(|w| *w == 0));
}

#[test]
fn text_lands_where_the_font_says_it_is_wide() {
    use crate::font;
    let mut c = paint::Canvas::new(80, 20, Colour::rgb(0, 0, 0));
    let white = Colour::rgb(0xff, 0xff, 0xff);
    c.text(0, 0, "AB", white, 2);
    let w = font::width("AB", 2);
    assert!((0..w).any(|x| (0..10).any(|y| c.get(x, y) == Some(white.word()))),
            "something inside the declared width");
    assert!((w..80).all(|x| (0..20).all(|y| c.get(x, y) == Some(0))),
            "nothing past it");
}

// ── Acceptance 5: a declined key is visibly declined ────────────────

#[test]
fn the_note_strip_distinguishes_three_states() {
    let m = model();
    let d = panels::view(&m, 600, None);
    let colours: Vec<Colour> = d.items.iter().filter_map(|i| match i {
        crate::list::Item::Rect { c, .. } => Some(*c),
        _ => None,
    }).collect();
    assert!(colours.contains(&panels::NOTE_ALL), "keys 60..72 accept fully");
    assert!(colours.contains(&panels::NOTE_SOME), "keys 48..60 accept partly");
    assert!(colours.contains(&panels::NOTE_NONE), "the rest are declined");
}

#[test]
fn a_declined_key_reads_as_silent() {
    let m = model();
    assert!(m.banks[0].accepts.silent_at(0));
    assert!(!m.banks[0].accepts.silent_at(64));
    assert_eq!(m.banks[0].accepts.at(50), (1, 2), "one of two velocities");
}

#[test]
fn a_structural_bank_says_so_in_words() {
    let m = Model {
        title: "T".into(),
        knobs: vec![],
        banks: vec![BankView { name: "keys".into(), voices: 4,
                               accepts: Accepts::Everything }],
    };
    let d = panels::view(&m, 600, None);
    let said = d.items.iter().any(|i| matches!(i,
        crate::list::Item::Text { s, .. } if s.contains("ALL KEYS")));
    assert!(said, "a wall of one colour must be words instead");
}

// ── The host's echo must not fight the hand ─────────────────────────

#[test]
fn a_host_value_mid_drag_does_not_move_the_dragged_knob() {
    let mut p = Panel::new(model());
    let (x, y) = track_point(&p, 0, 0.75);
    p.press(x, y);
    let held = p.model.knobs[0].value;
    p.sync_values(&[(0, 0.0), (1, 0.125)]);
    assert_eq!(p.model.knobs[0].value, held, "the drag owns its own knob");
    assert_eq!(p.model.knobs[1].value, 0.125, "the others follow the host");
}
