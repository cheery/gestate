//! The canvas, running — `spec/substrate.md`'s other half, driven.
//!
//! `substrate.rs` is the walk: a `Sub` tree to a display list, once.
//! This is the thing that keeps asking for one — the loop a frame
//! turns:
//!
//! ```text
//!   arrivals  ──→  reactive_step  ──→  main's cell  ──→  walk  ──→  Display
//! ```
//!
//! and the loop a hand turns, which is the same loop from the other
//! end: a press finds the deepest attachment it lands on, writes the
//! **channel that attachment carries**, and the next frame draws the
//! consequence.  Nothing is routed by name and nothing is registered;
//! the channel was in the structure, put there by the program.
//!
//! **Two things leave here, and only one of them is a picture.**  A
//! channel the canvas writes may be a channel the compiled graph reads
//! — `spec/substrate.md`'s "one fold, two readers" — and where the
//! export found such a pair it sent the slot along.  So a touch
//! produces a display the window paints *and* a parameter change the
//! host applies, and the sound follows the picture without this module
//! ever naming the engine.  That is the same discipline `spec/panel.md`
//! §"Threads" states for the knobs, kept for the canvas: a panel that
//! cannot reach the engine cannot make a sound wrong.

use std::collections::HashMap;
use std::panic::{catch_unwind, AssertUnwindSafe};

use crust::reactive::Arrivals;
use crust::{Machine, Node, Num, SigId};

use crate::interact::Change;
use crate::list::{Axis, Display, Kind};
use crate::substrate::{view_at, SubTags};

/// A canvas as the export sends it.
///
/// **Restated here rather than imported**, for the reason `model.rs`
/// gives: `shell/clap` owns the plugin and therefore depends on this
/// crate, so the dependency cannot point back.  Everything in it is a
/// fact about the program, and none of it is a pointer into a host.
#[derive(Clone, Debug)]
pub struct CanvasProgram {
    /// `gestate.crust.serialize`'s flat program text.
    pub text: String,
    /// The global to force — `main`, which `gestate.gui` binds to the
    /// file's `substrate`.
    pub entry: String,
    pub tags: SubTags,
    /// Every `name : Chan …` the file declares, **in the order
    /// written** — names, not ids.
    ///
    /// A channel's id is allocated when its declaration is first
    /// forced, so it is a fact about what the host does rather than
    /// about the program: forcing the declarations first gives
    /// `cutoff` id 0, letting the program reach it gives id 2, and
    /// both are correct readings of one file.  So these are forced
    /// here, in this order, before the program runs, and whatever ids
    /// come back are the ids.  Two languages that agree by not
    /// guessing.
    pub chans: Vec<String>,
    /// Channel **name** → the parameter that channel also is.
    ///
    /// Not a slot and not a pointer: the id the host already knows the
    /// control by, so a touch on the canvas travels the same road a
    /// drag on a fader does — one gesture, undoable, automatable, and
    /// visible in the DAW.
    pub bridge: Vec<(String, u32)>,
}

/// What the canvas could not do.  A refusal is a sentence for the
/// notice bar, never a panic that takes the window down.
pub type Fault = String;

fn guard<T>(what: impl FnOnce() -> T) -> Result<T, Fault> {
    catch_unwind(AssertUnwindSafe(what)).map_err(|e| {
        if let Some(s) = e.downcast_ref::<String>() {
            s.clone()
        } else if let Some(s) = e.downcast_ref::<&str>() {
            (*s).to_string()
        } else {
            "the canvas refused".to_string()
        }
    })
}

/// One program, drawn and touched.
pub struct Canvas {
    program: CanvasProgram,
    machine: Machine,
    /// `main`'s own cell.
    ///
    /// **Held by identity, not re-read.**  A signal *is* the cell, and
    /// an instant advancing overwrites it in place — that is the whole
    /// design, there is nowhere for an old value to live — so one id
    /// stays current for the life of the program.  `gui.py`'s
    /// `_entry_signal` says the same thing in Python.
    root: SigId,
    by_name: HashMap<String, i64>,
    bridge: HashMap<i64, u32>,
    display: Display,
    /// The attachment a press grabbed.
    ///
    /// **A press grabs**, so a drag that leaves the element still
    /// reaches it.  That is what a fader is, and doing it any other way
    /// makes one that stops following your hand at its own edge.
    held: Option<(Axis, i64, (i32, i32, i32, i32))>,
    failed: Option<Fault>,
}

impl Canvas {
    /// Load the program and force `main` to the signal it is.
    ///
    /// Forcing runs the program's initial term, and every `SigCons` on
    /// the way registers its cell on the now heap — which is what the
    /// sweep will afterwards walk.
    pub fn open(program: CanvasProgram) -> Result<Canvas, Fault> {
        let (machine, root, by_name) = guard(|| {
            let (mut m, _e) = Machine::from_text(&program.text);
            // **The declarations first, in the order they were
            // written.**  A channel is allocated when its declaration
            // is forced, and a global is memoised once forced — so
            // doing it here gives every declared channel an id *and*
            // makes that id the one the program itself will see.
            // `gui.Substrate.__init__` does exactly this, for exactly
            // this reason.
            let mut by_name = HashMap::new();
            for name in &program.chans {
                let Some(g) = m.globals_get(name).copied() else { continue };
                let forced = m.force_node(g);
                if let Node::Chan(id) = m.heap_at(forced) {
                    by_name.insert(name.clone(), *id);
                }
            }
            let g = *m.globals_get(&program.entry)
                .ok_or_else(|| format!("no global `{}`", program.entry))?;
            let forced = m.force_node(g);
            let id = match m.heap_at(forced) {
                Node::Sig(id) => *id,
                other => return Err(format!(
                    "`{}` is not a signal ({other:?})", program.entry)),
            };
            Ok::<_, Fault>((m, id, by_name))
        })??;
        // The bridge, resolved against the ids this machine handed out
        // rather than against any the export imagined.
        let bridge = program.bridge.iter()
            .filter_map(|(name, param)| Some((*by_name.get(name)?, *param)))
            .collect();
        Ok(Canvas { program, machine, root, by_name, bridge,
                    display: Display::new(), held: None, failed: None })
    }

    pub fn fault(&self) -> Option<&str> {
        self.failed.as_deref()
    }

    pub fn display(&self) -> &Display {
        &self.display
    }

    /// The channel id a declared name has, if the program declared it.
    pub fn channel(&self, name: &str) -> Option<i64> {
        self.by_name.get(name).copied()
    }

    /// One instant, then one picture.
    ///
    /// **The two are one call because they have to be in step.**
    /// Drawing a fold that a later arrival has already moved past is
    /// how a canvas comes to lag its own sound by a frame, and the
    /// only defence is that nothing else may run between them.
    ///
    /// `writes` are the arrivals for this instant, as `(channel,
    /// value)`.  An empty list still steps: `⃝∃` frontiers advance on
    /// time passing, not only on something arriving.
    ///
    /// `(cx, cy)` is where the picture's own origin lands, in
    /// **window** coordinates — so the regions this produces are the
    /// ones a press can be tested against without a second transform.
    /// A program's centre sits there, and the program places itself
    /// from it; see `Panel::canvas_origin` for why that rather than
    /// the middle of the pane.
    pub fn tick(&mut self, writes: &[(i64, f64)], cx: i32, cy: i32) {
        if self.failed.is_some() {
            return;
        }
        let Canvas { machine, root, program, display, .. } = self;
        let root = *root;
        let outcome = guard(|| {
            let mut arrivals = Arrivals::new();
            for (chan, value) in writes {
                let node = machine.alloc(Node::Num(Num::F(*value)));
                arrivals.insert(*chan, node);
            }
            machine.reactive_step(&arrivals);
            let value = machine.sig_value(root)
                .ok_or_else(|| "the canvas has no current value".to_string())?;
            view_at(machine, &program.tags, value, cx, cy)
                .map_err(|e| e.0)
        });
        match outcome {
            Ok(Ok(d)) => *display = d,
            Ok(Err(e)) | Err(e) => {
                // **The last good picture stays on screen.**  A canvas
                // that blanked on its first bad frame would take the
                // notice bar with it, and the notice is the only thing
                // that can say what happened.
                self.failed = Some(e);
            }
        }
    }

    /// A press.  Grabs the deepest attachment it lands on.
    pub fn press(&mut self, x: i32, y: i32) -> Vec<(i64, f64)> {
        self.held = self.display.pick(x, y).and_then(|hit| match hit.kind {
            Kind::Chan(axis, chan) => Some((axis, chan, hit.region)),
            _ => None,
        });
        self.value_at(x, y)
    }

    pub fn motion(&mut self, x: i32, y: i32) -> Vec<(i64, f64)> {
        self.value_at(x, y)
    }

    /// A release writes nothing — **a fader stays where it was let
    /// go** — and lets go of the grab.
    pub fn release(&mut self) {
        self.held = None;
    }

    pub fn is_grabbing(&self) -> bool {
        self.held.is_some()
    }

    /// What the grabbed element hears from a pointer here.
    ///
    /// **A fraction of the element's own extent**, 0 at the left or top
    /// edge and 1 at the right or bottom, and clamped there — `gui.py`'s
    /// `_gesture_value`, and its two consequences hold for the same
    /// reasons.  Motion is constrained by construction, because the
    /// bound is the extent the element declared and no program has to
    /// restate it; and the number means something without knowing the
    /// size, so the same signal drives a synth parameter directly.
    fn value_at(&self, x: i32, y: i32) -> Vec<(i64, f64)> {
        let Some((axis, chan, (x0, y0, x1, y1))) = self.held else {
            return Vec::new();
        };
        let (here, low, span) = match axis {
            Axis::X => (x, x0, x1 - x0),
            Axis::Y => (y, y0, y1 - y0),
        };
        // An element with no extent on the axis it listens to has no
        // fraction to report; 0 is the honest answer and the
        // alternative is a division by zero on a `Gap`.
        let f = if span <= 0 {
            0.0
        } else {
            (((here - low) as f64) / span as f64).clamp(0.0, 1.0)
        };
        vec![(chan, f)]
    }

    /// The parameter a channel also is, if the export found one.
    pub fn param_of(&self, chan: i64) -> Option<u32> {
        self.bridge.get(&chan).copied()
    }

    /// And the other way — **the direction that makes automation
    /// visible.**  A host moving a bridged parameter (a lane playing
    /// back, a knob turned in the DAW's own panel, another controller)
    /// must move the picture too, or the canvas becomes a display that
    /// is right only while you are the one touching it.
    pub fn chan_of_param(&self, param: u32) -> Option<i64> {
        self.bridge.iter().find(|(_, p)| **p == param).map(|(c, _)| *c)
    }

    /// A gesture's writes as the host must hear them.
    ///
    /// One `Begin`, the values, one `End` — acceptance 4's shape, and
    /// the reason a canvas drag is one undo step in the DAW rather
    /// than four hundred.  Only bridged channels produce anything: a
    /// channel the compiled graph never reads has no parameter to be.
    pub fn changes(&self, writes: &[(i64, f64)], opening: bool)
        -> Vec<Change>
    {
        let mut out = Vec::new();
        for (chan, value) in writes {
            let Some(param) = self.param_of(*chan) else { continue };
            if opening {
                out.push(Change::Begin(param));
            }
            out.push(Change::Value(param, *value));
        }
        out
    }

    /// Close whatever gesture the bridged channels have open.
    pub fn closing(&self, writes: &[(i64, f64)]) -> Vec<Change> {
        writes.iter()
            .filter_map(|(c, _)| self.param_of(*c))
            .map(Change::End)
            .collect()
    }

    /// What the grab is writing, for the caller that has to close it.
    pub fn grabbed(&self) -> Option<i64> {
        self.held.map(|(_, c, _)| c)
    }
}
