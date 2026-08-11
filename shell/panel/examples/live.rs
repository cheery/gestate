//! The panel in a real window, with nothing behind it.
//!
//! `cargo run -p gestate-panel --features window --example live`
//!
//! A standalone `baseview` window with the same model `shot` renders,
//! and a sink that prints what a host would have been told.  This is
//! how the windowing half gets looked at without a DAW: drag a fader
//! and the gesture that would have reached the host is on stdout,
//! `BEGIN` and `END` included.
//!
//! **And a real canvas, if you point it at one.**
//!
//! ```text
//! cargo run -p gestate-panel --features window,substrate --example live \
//!     -- tests/substrate.program tests/substrate.tags cutoff peak
//! ```
//!
//! The two fixtures beside `substrate_parity.rs` are exactly what the
//! export sends a plugin, so this draws and touches the same canvas a
//! DAW would — and the `Printer` shows the parameter changes a bridged
//! channel produces.  The channel names after them are the file's
//! declarations, in the order it wrote them.

use std::sync::Arc;

use gestate_panel::model::{Accepts, BankView, Knob, Model, SeedView};
use gestate_panel::window::{open_blocking, Sink};
use gestate_panel::Change;

struct Printer;

impl Sink for Printer {
    fn push(&self, change: Change) {
        match change {
            Change::Begin(p) => println!("GESTURE_BEGIN  param {p}"),
            Change::Value(p, v) => println!("PARAM_VALUE    param {p} = {v:.4}"),
            Change::End(p) => println!("GESTURE_END    param {p}"),
        }
    }

    /// A meter to watch, since there is no engine here to make one.
    #[cfg(feature = "substrate")]
    fn peak(&self) -> Option<f64> {
        use std::time::{SystemTime, UNIX_EPOCH};
        let ms = SystemTime::now().duration_since(UNIX_EPOCH).ok()?.as_millis();
        Some(((ms as f64 / 700.0).sin() * 0.5 + 0.5).abs())
    }
}

/// The canvas named on the command line, if one was.
#[cfg(feature = "substrate")]
fn canvas_from_args() -> Option<gestate_panel::canvas::CanvasProgram> {
    use gestate_panel::canvas::CanvasProgram;
    use gestate_panel::substrate::SubTags;

    let args: Vec<String> = std::env::args().skip(1).collect();
    let (program, tags) = (args.first()?, args.get(1)?);
    let text = std::fs::read_to_string(program).ok()?;
    let raw: Vec<i64> = std::fs::read_to_string(tags).ok()?
        .split_whitespace().filter_map(|w| w.parse().ok()).collect();
    if raw.len() < 11 {
        eprintln!("{tags}: expected eleven `Sub` tags, got {}", raw.len());
        return None;
    }
    let chans: Vec<String> = args[2..].to_vec();
    // Everything named is treated as bridged to a parameter of its own
    // index, so the `Printer` shows what a plugin would have been told.
    let bridge = chans.iter().enumerate()
        .map(|(i, n)| (n.clone(), i as u32)).collect();
    Some(CanvasProgram {
        text,
        entry: "main".into(),
        tags: SubTags {
            rect: raw[0], circle: raw[1], gap: raw[2], over: raw[3],
            row: raw[4], column: raw[5], shift: raw[6], sized: raw[7],
            pad: raw[8], touch_x: raw[9], touch_y: raw[10],
            label: raw[11], cons: raw[12], nil: raw[13],
        },
        chans,
        bridge,
    })
}

fn knob(name: &str, param: u32, value: f64, min: f64, max: f64) -> Knob {
    Knob { name: name.into(), param, value, min, max, integer: false }
}

fn main() {
    let model = Model {
        title: "FMPOLY".into(), notice: None, has_canvas: false,
        seed: Some(SeedView { param: 900, value: 1234, max: 99_999 }),
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

    #[cfg(feature = "substrate")]
    let opened = open_blocking(model, Arc::new(Printer), canvas_from_args());
    #[cfg(not(feature = "substrate"))]
    let opened = open_blocking(model, Arc::new(Printer));
    if let Err(e) = opened {
        eprintln!("could not open a window: {e:?}");
        std::process::exit(1);
    }
}
