//! What the panel promises, checked without a window.
//!
//! `spec/panel.md`'s acceptance list, minus the two clauses that need a
//! host (1 and 6 live in `test_export.py`, where the plugin is already
//! driven by a miniature CLAP host).

use crate::interact::Change;
use crate::list::{Axis, Colour, Kind};
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
            routing: 0b0000_0000_0000_0001,
            routing_param0: 100,
                       plays_score: true, score_writes: true,
                       score_param: 1000,
        }],
    }
}

// ── Acceptance 2: the display list is a pure function of the model ──

#[test]
fn the_same_model_draws_the_same_list() {
    let m = model();
    assert_eq!(panels::view(&m, 600, None, 100, 0), panels::view(&m, 600, None, 100, 0));
}

#[test]
fn a_model_with_no_knobs_offers_no_parameters() {
    let m = Model { title: "T".into(), knobs: vec![], banks: vec![] };
    let d = panels::view(&m, 600, None, 100, 0);
    assert!(d.hits.iter().all(|h| matches!(h.kind, Kind::Button(_))),
            "an empty descriptor still has its own text-size buttons, \
             and nothing else");
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
    let h = p.display().hits.iter()
        .find(|h| h.param == param && matches!(h.kind, Kind::Fader(_)))
        .unwrap();
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
    let hx = Hit { kind: Kind::Fader(Axis::X), param: 0,
                   region: (0, 0, 100, 20) };
    assert!(hx.fraction(10, 10) < hx.fraction(90, 10));
    let hy = Hit { kind: Kind::Fader(Axis::Y), param: 0,
                   region: (0, 0, 20, 100) };
    assert!(hy.fraction(10, 90) < hy.fraction(10, 10),
            "a fader grows upward where screen y grows downward");
}

#[test]
fn a_point_outside_the_track_clamps() {
    use crate::list::Hit;
    let h = Hit { kind: Kind::Fader(Axis::X), param: 0,
                  region: (0, 0, 100, 20) };
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
    let d = panels::view(&m, 600, None, 100, 0);
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
                               accepts: Accepts::Everything, routing: 0b0000_0000_0000_0010,
                       routing_param0: 100, plays_score: true, score_writes: true,
                       score_param: 1000 }],
    };
    let d = panels::view(&m, 600, None, 100, 0);
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


// ── The routing matrix reacts ───────────────────────────────────────

/// The centre of one routing cell, from the layout.
fn cell_point(p: &Panel, param: u32) -> (i32, i32) {
    let h = p.display().hits.iter()
        .find(|h| h.param == param && h.kind == Kind::Toggle).unwrap();
    let (x0, y0, x1, y1) = h.region;
    ((x0 + x1) / 2, (y0 + y1) / 2)
}

#[test]
fn every_bank_offers_sixteen_channels_and_a_score_switch() {
    let p = Panel::new(model());
    let toggles = p.display().hits.iter()
        .filter(|h| h.kind == Kind::Toggle).count();
    assert_eq!(toggles, 17, "sixteen channels and one score switch");
}

#[test]
fn the_score_switch_toggles_and_is_its_own_parameter() {
    let mut p = Panel::new(model());
    let id = p.model.banks[0].score_param;
    let h = p.display().hits.iter()
        .find(|h| h.param == id && h.kind == Kind::Toggle)
        .expect("the score switch is on the panel");
    let (x0, y0, x1, y1) = h.region;
    let out = p.press((x0 + x1) / 2, (y0 + y1) / 2);
    assert!(out.contains(&Change::Value(id, 0.0)),
            "on must turn off: {out:?}");
    assert!(!p.model.banks[0].plays_score);
    // And it is *not* a routing cell — the two must not share an id.
    assert!(id < p.model.banks[0].routing_param0
            || id >= p.model.banks[0].routing_param0 + 16);
}

#[test]
fn clicking_a_routing_cell_is_one_whole_gesture() {
    let mut p = Panel::new(model());
    // Channel 2 (param 101) starts off; the model routes channel 1.
    let (x, y) = cell_point(&p, 101);
    let out = p.press(x, y);
    assert_eq!(out, vec![Change::Begin(101), Change::Value(101, 1.0),
                         Change::End(101)],
               "a click opens and closes its own gesture");
    assert!(p.release().is_empty(), "the release has nothing left to close");
}

#[test]
fn a_routing_cell_toggles_rather_than_setting() {
    let mut p = Panel::new(model());
    // Channel 1 (param 100) is on in the fixture.
    let (x, y) = cell_point(&p, 100);
    let out = p.press(x, y);
    assert!(out.contains(&Change::Value(100, 0.0)), "on must turn off");
    assert!(!p.model.banks[0].listens_on(0), "and the model must follow");
    let out = p.press(x, y);
    assert!(out.contains(&Change::Value(100, 1.0)), "off must turn back on");
    assert!(p.model.banks[0].listens_on(0));
}

#[test]
fn the_cell_redraws_when_it_flips() {
    let mut p = Panel::new(model());
    let before = p.render().px;
    let (x, y) = cell_point(&p, 100);
    p.press(x, y);
    assert_ne!(p.render().px, before,
               "a toggled cell that looks the same is a dead control");
}

#[test]
fn a_host_routing_value_reaches_the_model() {
    let mut p = Panel::new(model());
    p.sync_values(&[(103, 1.0)]);
    assert!(p.model.banks[0].listens_on(3), "channel 4 came from the host");
    p.sync_values(&[(103, 0.0)]);
    assert!(!p.model.banks[0].listens_on(3));
}

// ── Resizing ────────────────────────────────────────────────────────

#[test]
fn a_wider_window_gives_the_faders_a_longer_throw() {
    let mut p = Panel::new(model());
    let narrow = p.display().hits.iter()
        .find(|h| h.param == 0 && matches!(h.kind, Kind::Fader(_)))
        .unwrap().region;
    p.resize(p.width + 200, p.height);
    let wide = p.display().hits.iter()
        .find(|h| h.param == 0 && matches!(h.kind, Kind::Fader(_)))
        .unwrap().region;
    assert!(wide.2 - wide.0 > narrow.2 - narrow.0,
            "the track must follow the window");
}


// ── The strip fits, at every width ──────────────────────────────────

/// The rightmost pixel any item reaches.
fn right_edge(d: &crate::Display) -> i32 {
    d.items.iter().map(|i| match i {
        crate::list::Item::Rect { x, w, .. } => x + w,
        crate::list::Item::Dot { cx, r, .. } => cx + r,
        crate::list::Item::Text { x, s, scale, .. } =>
            x + crate::font::width(s, *scale),
    }).max().unwrap_or(0)
}

#[test]
fn nothing_is_drawn_past_the_window_at_any_width() {
    let m = model();
    for w in [900, 1000, 1200, 1600] {
        let d = panels::view(&m, w, None, 100, 0);
        assert!(right_edge(&d) <= w,
                "at width {w} something reached {}", right_edge(&d));
    }
}

#[test]
fn the_key_strip_scales_with_the_window() {
    let m = model();
    let width_of = |w: i32| {
        let d = panels::view(&m, w, None, 100, 0);
        d.items.iter().filter_map(|i| match i {
            crate::list::Item::Rect { c, w, .. }
                if *c == panels::NOTE_ALL => Some(*w),
            _ => None,
        }).max().unwrap_or(0)
    };
    assert!(width_of(1600) > width_of(900),
            "a wider window must give each key more room");
}

#[test]
fn the_strip_fills_its_column_exactly() {
    // No crumbs: the last key must end where the pane's margin begins,
    // whatever the width divides into.
    let m = model();
    for w in [903, 1001, 1277, 1523] {
        let d = panels::view(&m, w, None, 100, 0);
        let far = d.items.iter().filter_map(|i| match i {
            crate::list::Item::Rect { x, w: rw, c, .. }
                if *c == panels::NOTE_ALL || *c == panels::NOTE_NONE
                   || *c == panels::NOTE_SOME => Some(x + rw),
            _ => None,
        }).max().unwrap();
            let k = panels::Metrics::new(100);
        assert_eq!(far, w - k.pad() - k.bar_w(),
                   "at width {w} the band stopped at {far}");
    }
}

#[test]
fn a_bank_window_opens_wide_enough_to_read() {
    let p = Panel::new(model());
    let k = panels::Metrics::new(p.scale());
    let name_w = panels::name_column(&p.model, &k);
    let (_sx, avail) = k.strip_span(p.width, name_w);
    assert!(avail / 128 >= 5, "a fresh window wants ~5px a key, got {}",
            avail / 128);
}

// ── Text size ───────────────────────────────────────────────────────

fn button_point(p: &Panel, act: u32) -> (i32, i32) {
    let h = p.display().hits.iter()
        .find(|h| h.kind == Kind::Button(act)).expect("no such button");
    let (x0, y0, x1, y1) = h.region;
    ((x0 + x1) / 2, (y0 + y1) / 2)
}

#[test]
fn the_size_buttons_never_reach_the_host() {
    let mut p = Panel::new(model());
    let (x, y) = button_point(&p, panels::ACT_LARGER);
    assert!(p.press(x, y).is_empty(),
            "how big the text is is not the instrument's business");
    assert!(p.release().is_empty());
}

#[test]
fn the_plus_button_makes_the_text_bigger() {
    let mut p = Panel::new(model());
    let before = p.scale();
    let (x, y) = button_point(&p, panels::ACT_LARGER);
    p.press(x, y);
    assert_eq!(p.scale(), before + panels::SCALE_STEP);
    assert!(p.wanted_size().0 > panels::size(&p.model, before).0,
            "bigger text wants a bigger window");
}

#[test]
fn the_scale_stops_at_both_ends() {
    let mut p = Panel::with_scale(model(), panels::SCALE_MAX);
    assert!(p.display().hits.iter()
            .all(|h| h.kind != Kind::Button(panels::ACT_LARGER)),
            "a button that cannot do anything must not be offered");
    assert!(!p.set_scale(panels::SCALE_MAX + 100));
    let mut p = Panel::with_scale(model(), panels::SCALE_MIN);
    assert!(p.display().hits.iter()
            .all(|h| h.kind != Kind::Button(panels::ACT_SMALLER)));
    assert!(!p.set_scale(0));
}

#[test]
fn bigger_text_is_actually_bigger() {
    let small = Panel::with_scale(model(), panels::SCALE_MIN);
    let large = Panel::with_scale(model(), panels::SCALE_MAX);
    let tallest = |p: &Panel| p.display().items.iter().filter_map(|i| {
        match i { crate::list::Item::Text { scale, .. } => Some(*scale),
                  _ => None }
    }).max().unwrap();
    assert!(tallest(&large) > tallest(&small));
}

// ── Scrolling ───────────────────────────────────────────────────────

#[test]
fn a_window_that_fits_does_not_scroll() {
    let mut p = Panel::new(model());
    assert_eq!(p.max_scroll(), 0, "the default window shows everything");
    assert!(!p.scroll_by(200), "there is nowhere to go");
}

#[test]
fn a_short_window_scrolls_and_stops() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    assert!(p.max_scroll() > 0, "a short window has more below");
    assert!(p.scroll_by(50));
    assert_eq!(p.scroll(), 50);
    assert!(p.scroll_by(100_000));
    assert_eq!(p.scroll(), p.max_scroll(), "it stops at the end");
    assert!(!p.scroll_by(10), "and does not go past it");
    assert!(p.scroll_by(-100_000));
    assert_eq!(p.scroll(), 0, "and back to the top");
}

#[test]
fn scrolling_moves_the_hit_regions_with_the_picture() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    let fader = |p: &Panel| p.display().hits.iter()
        .find(|h| h.param == 0 && matches!(h.kind, Kind::Fader(_)))
        .unwrap().region;
    let before = fader(&p);
    p.scroll_by(40);
    let after = fader(&p);
    assert_eq!(after.1, before.1 - 40,
               "a region that stayed put would write the wrong parameter");
}

#[test]
fn shrinking_the_text_cannot_strand_the_view() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    p.scroll_by(100_000);
    p.set_scale(panels::SCALE_MIN);
    assert!(p.scroll() <= p.max_scroll(),
            "a blank pane with content above it reads as a crash");
}


#[test]
fn the_bar_appears_only_when_there_is_more_than_fits() {
    let mut p = Panel::new(model());
    assert!(p.bar_rect().is_none(), "a window that fits has no bar");
    p.resize(p.width, 160);
    assert!(p.bar_rect().is_some(), "a short window has one");
}

#[test]
fn dragging_the_bar_scrolls() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    let (bx0, _, bx1, by1) = p.bar_rect().unwrap();
    let x = (bx0 + bx1) / 2;

    // Press at the top of the channel: the view goes to the top.
    p.press(x, 0);
    assert_eq!(p.scroll(), 0);
    // Drag to the bottom: the view goes to the end.
    p.motion(x, by1);
    assert_eq!(p.scroll(), p.max_scroll(), "the bar must reach the end");
    // Half way back.
    p.motion(x, by1 / 2);
    assert!(p.scroll() > 0 && p.scroll() < p.max_scroll());
    p.release();
    // And the drag is over — a later move must not keep scrolling.
    let held = p.scroll();
    p.motion(x, 0);
    assert_eq!(p.scroll(), held, "release must end the drag");
}

#[test]
fn a_press_on_the_bar_is_not_a_parameter() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    let (bx0, _, bx1, _) = p.bar_rect().unwrap();
    assert!(p.press((bx0 + bx1) / 2, 40).is_empty(),
            "the bar lies over the content and must not click through");
}

#[test]
fn the_bar_is_wide_enough_to_hit() {
    let mut p = Panel::new(model());
    p.resize(p.width, 160);
    let (x0, _, x1, _) = p.bar_rect().unwrap();
    assert!(x1 - x0 >= 10, "a bar you have to aim at is not a control");
}
