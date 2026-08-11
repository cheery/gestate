//! Render a panel to a PPM on stdout — the panel, without a window.
//!
//! `cargo run -p gestate-panel --example shot > panel.ppm`
//!
//! This exists because a layout is the one thing in this crate that a
//! unit test cannot really check: the tests pin that a fader's region
//! matches its track and that a declined key is a different colour, but
//! whether a label collides with a number is a thing a person has to
//! look at.  It is also `spec/panel.md` acceptance 3's mechanism — the
//! same display list must give the same pixels, and this is how those
//! pixels get somewhere they can be compared.

use gestate_panel::model::{Accepts, BankView, Knob, Model};
use gestate_panel::Panel;
use std::io::Write;

fn knob(name: &str, param: u32, value: f64, min: f64, max: f64) -> Knob {
    Knob { name: name.into(), param, value, min, max, integer: false }
}

fn main() {
    let model = Model {
        title: "FMPOLY".into(), notice: None,
        knobs: vec![
            knob("cutoff", 0, 0.42, 0.0, 1.0),
            knob("resonance", 1, 0.2, 0.0, 1.0),
            knob("drive", 2, 0.75, 0.0, 4.0),
            Knob { name: "mode".into(), param: 3, value: 2.0, min: 0.0,
                   max: 4.0, integer: true },
        ],
        banks: vec![
            BankView {
                name: "lead".into(),
                voices: 6,
                accepts: Accepts::Table {
                    levels: 4,
                    ok: (0..128 * 4).map(|i| {
                        let (k, l) = (i / 4, i % 4);
                        // A instrument that answers two octaves fully
                        // and the octave below only when struck hard.
                        (60..84).contains(&k)
                            || ((48..60).contains(&k) && l >= 2)
                    }).collect(),
                },
                routing: 0b0000_0000_0000_0001,
                routing_param0: 100,
                       plays_score: true, score_writes: true,
                       score_param: 1000,
            },
            BankView { name: "keys".into(), voices: 4,
                       accepts: Accepts::Everything,
                       routing: 0b0000_0000_0000_0010,
                       routing_param0: 116, plays_score: true, score_writes: true,
                       score_param: 1016 },
        ],
    };

    // A window shorter than its content, so the scrollbar is in shot.
    let mut p = Panel::new(model);
    if let Ok(h) = std::env::var("SHOT_H") {
        if let Ok(h) = h.parse::<i32>() { p.resize(p.width, h); }
    }
    if std::env::var("SHOT_SCROLL").is_ok() { p.scroll_by(120); }
    let c = p.render();
    let mut out = Vec::new();
    write!(out, "P6\n{} {}\n255\n", c.w, c.h).unwrap();
    for word in &c.px {
        out.push((word >> 16) as u8);
        out.push((word >> 8) as u8);
        out.push(*word as u8);
    }
    std::io::stdout().write_all(&out).unwrap();
}
