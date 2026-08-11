//! The panel in a real window, with nothing behind it.
//!
//! `cargo run -p gestate-panel --features window --example live`
//!
//! A standalone `baseview` window with the same model `shot` renders,
//! and a sink that prints what a host would have been told.  This is
//! how the windowing half gets looked at without a DAW: drag a fader
//! and the gesture that would have reached the host is on stdout,
//! `BEGIN` and `END` included.

use std::sync::Arc;

use gestate_panel::model::{Accepts, BankView, Knob, Model};
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
}

fn knob(name: &str, param: u32, value: f64, min: f64, max: f64) -> Knob {
    Knob { name: name.into(), param, value, min, max, integer: false }
}

fn main() {
    let model = Model {
        title: "FMPOLY".into(),
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
            },
            BankView { name: "keys".into(), voices: 4,
                       accepts: Accepts::Everything },
        ],
    };

    if let Err(e) = open_blocking(model, Arc::new(Printer)) {
        eprintln!("could not open a window: {e:?}");
        std::process::exit(1);
    }
}
