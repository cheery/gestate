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

    /// The span of keys this bank answers, and whether it answers *all*
    /// of them at *every* velocity.
    ///
    /// **The uniform case has to be recognised, not drawn.**  A strip
    /// that is one colour end to end tells a player nothing and reads
    /// as a rendering fault — the same reason `Everything` is words
    /// rather than a full bar.  A table that happens to accept
    /// everything deserves the same treatment, and only the caller
    /// comparing the ends can tell.
    pub fn span(&self) -> Option<(usize, usize, bool)> {
        let mut lo = None;
        let mut hi = 0usize;
        let mut full = true;
        for k in 0..128 {
            let (yes, total) = self.at(k);
            if yes == 0 {
                full = false;
                continue;
            }
            if yes < total {
                full = false;
            }
            lo.get_or_insert(k);
            hi = k;
        }
        lo.map(|l| (l, hi, full && l == 0 && hi == 127))
    }
}

/// One `voices` bank as a player needs to see it.
#[derive(Clone, PartialEq, Debug)]
pub struct BankView {
    pub name: String,
    pub voices: usize,
    pub accepts: Accepts,
    /// Which MIDI channels feed this bank: bit `c` set means it
    /// listens on channel `c`.  The shell's `Instance.routing` row.
    pub routing: u16,
    /// The parameter id of this bank's channel-0 cell; channel `c` is
    /// `routing_param0 + c`.
    ///
    /// **The ids are the plugin's, not invented here.**
    /// `params_get_info` numbers a routing cell
    /// `controls.len() + bank*16 + channel`, and the panel takes that
    /// base rather than recomputing it — one table, not two that have
    /// to agree.
    pub routing_param0: u32,
    /// Whether the **score** plays this bank.
    pub plays_score: bool,
    /// Whether the score writes this bank *at all* — a fact about the
    /// program, where `plays_score` is a switch about this session.
    ///
    /// Switching the score on for a bank it never writes is not an
    /// error, but it is certainly not what the presser meant: nothing
    /// will ever come out of it.  The panel says so in colour rather
    /// than refusing the click.
    pub score_writes: bool,
    /// The parameter id of that switch.
    pub score_param: u32,
}

impl BankView {
    pub fn listens_on(&self, channel: usize) -> bool {
        channel < 16 && (self.routing >> channel) & 1 == 1
    }
}

/// The take's seed, as a thing to look at and reroll.
///
/// **A number and a button, not a fader.**  Dragging would be the
/// obvious gesture and is the wrong one: every value a drag passes
/// through is a *different piece*, and the plugin answers a new seed
/// by re-rooting its stream — so a one-second drag asks for sixty
/// re-roots of a score, of which fifty-nine are thrown away.  One
/// press, one take.  A player who wants a *particular* seed types it
/// into the host's own parameter box, which is what that box is for.
#[derive(Clone, PartialEq, Debug)]
pub struct SeedView {
    pub param: u32,
    pub value: i64,
    pub max: i64,
}

/// Which of the two sources the window is showing.
///
/// **CONTROLS and CANVAS**, and the names are the ones this project
/// already uses for these two things: `spec/panel.md` §"One painter,
/// two sources" calls the descriptor-driven side the panel's controls
/// and the program-driven side *the canvas*.  Naming them after where
/// they sit — front, behind — would name the window's arrangement
/// rather than what is on each side, and the arrangement is the part
/// most likely to change.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Tab {
    #[default]
    Controls,
    Canvas,
}

/// Everything panel one draws.
#[derive(Clone, PartialEq, Debug, Default)]
pub struct Model {
    pub title: String,
    pub knobs: Vec<Knob>,
    pub banks: Vec<BankView>,
    /// Something the instrument needs to say — a piece that stopped
    /// forcing and why.
    ///
    /// **Because silence is this project's named failure mode.**  A
    /// forced score that refuses goes quiet and everything else keeps
    /// playing, which sounds exactly like a mix decision rather than a
    /// fault.  The panel is where an instrument can say what happened.
    pub notice: Option<String>,
    /// The seed, when this plugin's piece has one to turn.
    ///
    /// `None` for a plugin whose score is a baked event list: the
    /// events are already decided, so there is no entropy for a seed
    /// to govern and a button offering to reroll it would be a lie.
    pub seed: Option<SeedView>,
    /// Whether this plugin carries a canvas — whether the second tab
    /// has anything behind it.
    pub has_canvas: bool,
}
