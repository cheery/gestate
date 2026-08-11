//! What the panel draws — **the descriptor, restated without the
//! descriptor.**
//!
//! `shell/clap` owns `Descriptor`, `Control`, `Bank` and `NoteTable`; it
//! also owns the plugin, so it is the crate that depends on this one.
//! The dependency cannot point back, so the panel names what it needs in
//! its own types and the shell fills them in.
//!
//! That is not a workaround for the cycle, it is the interface working:
//! everything here is *what a player looks at*, and nothing here is a
//! function pointer, a slot index or a state buffer.  A panel that
//! cannot reach the engine cannot make a sound wrong (`spec/panel.md`
//! §"Threads").

/// One knob — a `Control` whose `knob` flag is set, already resolved to
/// the parameter index the host knows it by.
#[derive(Clone, PartialEq, Debug)]
pub struct Knob {
    /// The channel's own name, as the program spelled it.
    pub name: String,
    /// The CLAP parameter id.  Panel one writes parameters, never
    /// slots — `spec/panel.md` §"Knobs".
    pub param: u32,
    pub value: f64,
    pub min: f64,
    pub max: f64,
    /// `Kind::Int` — drawn without a fraction, and stepped when dragged.
    pub integer: bool,
}

impl Knob {
    /// Where this value sits in its own range, 0.0 to 1.0.
    pub fn fraction(&self) -> f64 {
        let span = self.max - self.min;
        if span.abs() < f64::EPSILON {
            0.0
        } else {
            ((self.value - self.min) / span).clamp(0.0, 1.0)
        }
    }

    /// A fraction back to a value, stepped if this knob is an integer.
    pub fn value_at(&self, f: f64) -> f64 {
        let v = self.min + f.clamp(0.0, 1.0) * (self.max - self.min);
        if self.integer {
            v.round()
        } else {
            v
        }
    }

    /// The value as the panel prints it.
    ///
    /// Three decimals for a float: enough to see a knob move, few
    /// enough that the column does not reflow while dragging.  A
    /// reflowing number is the sort of thing that reads as a glitch.
    pub fn label(&self) -> String {
        if self.integer {
            format!("{}", self.value.round() as i64)
        } else {
            format!("{:.3}", self.value)
        }
    }
}

/// Which notes a bank answers.
#[derive(Clone, PartialEq, Debug)]
pub enum Accepts {
    /// `Bank.table` is `None`: the structural `(key, velocity)` payload
    /// the live path defaults to, which declines nothing.
    Everything,
    /// The program's own `FromMIDI` instance, tabled at export.
    /// `ok[key * levels + level]`, 128 keys.
    Table { levels: usize, ok: Vec<bool> },
}

impl Accepts {
    /// How many velocity levels of `key` this bank accepts, and how many
    /// there are — `(accepted, total)`.
    pub fn at(&self, key: usize) -> (usize, usize) {
        match self {
            Accepts::Everything => (1, 1),
            Accepts::Table { levels, ok } => {
                let lo = key * levels;
                let hi = (lo + levels).min(ok.len());
                if lo >= ok.len() {
                    (0, *levels)
                } else {
                    (ok[lo..hi].iter().filter(|b| **b).count(), *levels)
                }
            }
        }
    }

    /// Whether the bank declines this key at every velocity — the fact
    /// the panel exists to make visible.
    pub fn silent_at(&self, key: usize) -> bool {
        self.at(key).0 == 0
    }
}

/// One `voices` bank as a player needs to see it.
#[derive(Clone, PartialEq, Debug)]
pub struct BankView {
    pub name: String,
    pub voices: usize,
    pub accepts: Accepts,
}

/// Everything panel one draws.
#[derive(Clone, PartialEq, Debug, Default)]
pub struct Model {
    pub title: String,
    pub knobs: Vec<Knob>,
    pub banks: Vec<BankView>,
}
