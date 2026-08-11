//! The gestate side of the shell — two symbols and a zeroed buffer.
//!
//! An exported graph is a static library with one entry point the shell
//! calls per block:
//!
//! ```c
//! void render_block_f32(void *state, float *out, int64_t frames,
//!                       const int64_t *control);
//! ```
//!
//! and one fact worth stating because it makes the whole shell thin:
//! **the state starts as zeroes.**  `audiolive.Engine.compile` allocates
//! `8 * (1 + Σ slots)` zeroed bytes and nothing more — the generated
//! code's own first-instant branch seeds every node's `init` when `t`
//! is 0.  So a plugin instance is: zero the buffer, hand out blocks.
//!
//! `descriptor.rs` is written by `python -m gestate.export` beside the
//! graph's object file; without the `engine` feature this shell is an
//! empty factory that loads cleanly in a host, which is what a build
//! with no instrument in it should be.

/// How one control slot is reinterpreted — mirrors
/// `audiohost.Host.set_control` and `audiollvm.pack_control`: a Float
/// is its bit pattern in the i64 slot, everything else is the integer.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Float,
    Int,
}

/// One control channel, in buffer order — a knob, or a channel a
/// score writes.  `init_bits` is the slot's value before anyone moves
/// it: the program's own declared default, already reinterpreted.
///
/// `knob` is what separates a parameter a DAW may draw and automate
/// from a channel the `voices` expansion generated for notes —
/// automation writing into a bank's payload field would be a note
/// nobody played, so only knobs are advertised.  `min`/`max` are the
/// exporter's stated heuristic (`export._range_of`) until the language
/// declares ranges of its own.
pub struct Control {
    pub chan: &'static str,
    pub kind: Kind,
    pub init_bits: i64,
    pub knob: bool,
    pub min: f64,
    pub max: f64,
}

impl Control {
    /// The slot's default as the double a CLAP parameter speaks.
    pub fn init_value(&self) -> f64 {
        match self.kind {
            Kind::Float => f64::from_bits(self.init_bits as u64),
            Kind::Int => self.init_bits as f64,
        }
    }

    /// A parameter value into slot bits — the same reinterpretation
    /// `Host.set_control` and `pack_control` make.
    pub fn bits_of(&self, value: f64) -> i64 {
        match self.kind {
            Kind::Float => value.to_bits() as i64,
            Kind::Int => value.round() as i64,
        }
    }

    /// A slot's bits back to the double a host reads.
    pub fn value_of(&self, bits: i64) -> f64 {
        match self.kind {
            Kind::Float => f64::from_bits(bits as u64),
            Kind::Int => bits as f64,
        }
    }
}

/// One `voices` bank's shape, as slot indices: per voice, `gateAt`,
/// `offAt`, then the author's payload fields — `audioalloc`'s layout,
/// resolved to control-buffer positions at export.
pub struct Bank {
    pub name: &'static str,
    pub voices: &'static [&'static [usize]],
    /// `None`: the structural payload the live path defaults to —
    /// `(key, velocity)` truncated to the field count.  `Some`: the
    /// program's own `FromMIDI` instance, run through the G-machine at
    /// export time and tabled.
    pub table: Option<&'static NoteTable>,
}

/// `noteOn ch p v`, memoised over 128 keys × `levels` velocity steps
/// (channel 0).  `ok[k*levels + l]` is whether the instance accepted;
/// `data[(k*levels + l)*fields ..]` the payload's slot bits.
pub struct NoteTable {
    pub levels: usize,
    pub fields: usize,
    pub ok: &'static [bool],
    pub data: &'static [i64],
}

/// Everything `python -m gestate.export` knows that the shell needs.
pub struct Descriptor {
    pub id: &'static str,
    pub name: &'static str,
    pub version: &'static str,
    /// The rate the graph was compiled at.  `sampleRate` is a constant
    /// folded through the program, so the first cut refuses activation
    /// at any other rate rather than resampling behind the host's back.
    pub rate: u32,
    /// Interleaved f32s per frame — `audiollvm.out_channels`.
    pub channels: u32,
    /// `8 * (1 + Σ slots)`, zeroed at activate.
    pub state_bytes: usize,
    pub controls: &'static [Control],
}

/// One compiled rate of the graph.  `sampleRate` is a constant folded
/// through the program, so a plugin honest at several rates carries
/// several *graphs* — same nodes, different constants, different
/// delay-line lengths (hence `state_bytes` per case) — and `activate`
/// picks the one the host's rate names.
pub struct RateCase {
    pub rate: u32,
    pub state_bytes: usize,
    pub render: unsafe extern "C" fn(state: *mut u8, out: *mut f32,
                                     frames: i64, control: *const i64),
}

/// One event of the piece's own score, in *beats* — `spec/
/// dynamicscore.md` stage one's descriptor half.  `tick` is the beat
/// position × `SCORE_TPB`, exact where a float would drift; `key` is
/// the event's own index, `timed_events`' note identity; `payload` is
/// the author's record already reinterpreted to slot bits, empty on a
/// release.  The exporter writes the list in the performance's one
/// true order — `(tick, releases-first)` — and the cursor
/// (`score.rs`) preserves it.
pub struct ScoreEvent {
    pub tick: i64,
    pub key: u32,
    pub bank: usize,
    pub is_off: bool,
    pub payload: &'static [i64],
}

// (`tempoChan`, the nominal convention that briefly lived here, is
// retired: the host clock now arrives through descriptor-declared
// slots — `BEAT_SLOTS` — never through a channel's spelling.
// `spec/substrate.md`'s context contract is why.)

#[cfg(feature = "engine")]
mod linked {
    include!("descriptor.rs");
}

#[cfg(feature = "engine")]
pub static DESCRIPTOR: Option<&Descriptor> = Some(&linked::DESCRIPTOR);

#[cfg(not(feature = "engine"))]
pub static DESCRIPTOR: Option<&Descriptor> = None;

#[cfg(feature = "engine")]
pub static BANKS: &[Bank] = linked::BANKS;

#[cfg(not(feature = "engine"))]
pub static BANKS: &[Bank] = &[];

/// Per bank, whether the **score** writes it
/// (`export.scored_banks`).
///
/// The routing default reads this: a bank the piece plays is not also
/// the keyboard's, because MIDI landing in it fills the voices the
/// piece needs and the piece goes quiet.  That is the two-bank law the
/// listening pieces are built on, made the default rather than left to
/// a player to discover.
#[cfg(feature = "engine")]
pub static SCORED: &[bool] = linked::SCORED;

#[cfg(not(feature = "engine"))]
pub static SCORED: &[bool] = &[];

#[cfg(feature = "engine")]
pub static RATES: &[RateCase] = linked::RATES;

#[cfg(not(feature = "engine"))]
pub static RATES: &[RateCase] = &[];

/// The host clock's slots — `(base, beats-per-second, anchor tick)`,
/// a *line* the program's `beat` evaluates at `ticks`.  `None` when
/// the program never reaches `beat` and reachability pruned it.
#[cfg(feature = "engine")]
pub static BEAT_SLOTS: Option<(usize, usize, usize)> = linked::BEAT_SLOTS;

#[cfg(not(feature = "engine"))]
pub static BEAT_SLOTS: Option<(usize, usize, usize)> = None;

/// The piece's own events in beats — empty for a plugin that is an
/// instrument without a piece, which is every scoreless export and,
/// until the G-machine travels (`spec/crust.md`), every unfolding one.
#[cfg(feature = "engine")]
pub static SCORE: &[ScoreEvent] = linked::SCORE;

#[cfg(not(feature = "engine"))]
pub static SCORE: &[ScoreEvent] = &[];

/// The piece as a **program**, when no event list can hold it.
///
/// `SCORE` above is empty for an unfolding piece; this is what travels
/// instead.  `None` for every finite score (which bakes) and for every
/// build without the `dynscore` feature — the interpreter is carried
/// only by the plugins that need it.
/// A reference, not a copy: `Program` holds a `&'static str` the size
/// of the whole interpreter's input, and a static that moved would be
/// a second one in the binary.
#[cfg(all(feature = "engine", feature = "dynscore"))]
pub fn program() -> Option<&'static Program> {
    linked::PROGRAM.as_ref()
}

#[cfg(not(all(feature = "engine", feature = "dynscore")))]
pub fn program() -> Option<&'static Program> {
    None
}

/// `midi.TICKS_PER_BEAT`, written by the exporter so the two never
/// spell it separately.
#[cfg(feature = "engine")]
pub static SCORE_TPB: i64 = linked::SCORE_TPB;

#[cfg(not(feature = "engine"))]
pub static SCORE_TPB: i64 = 96;

/// The piece's own tempo, for a host with no transport at all: a
/// free-running host plays the score at its declared pace, the same
/// convention as the untouched beat slots.
#[cfg(feature = "engine")]
pub static SCORE_BPM: f64 = linked::SCORE_BPM;

#[cfg(not(feature = "engine"))]
pub static SCORE_BPM: f64 = 120.0;

/// The piece as a **program**, for a score no event list can hold.
///
/// `spec/dynamicscore.md` stage two, abroad.  A finite score exports as
/// `SCORE` — a list of instants, already decided.  An *unfolding* one
/// (`cycle`, `unfold`, anything that answers a channel) has no such
/// list, and until now `export.score_events` discarded it and said so:
/// "the plugin is the instrument without its piece."
///
/// This is the piece.  The text is `crust`'s flat program format,
/// written by `gestate.crust.serialize`; the tags are the compiled
/// constructor numbers the stream decodes cells with, and they travel
/// because a tag is a *position* in the program's own constructor
/// table — the shell cannot derive one.
pub struct Program {
    /// The serialized G-machine program.
    pub text: &'static str,
    /// The entry to force — `liveMain`, which is resume-aware in its
    /// own second argument.
    pub entry: &'static str,
    /// The piece's seed.  One integer replays the whole night.
    pub seed: i64,
    pub cons_tag: i64,
    pub nil_tag: i64,
    /// `CueEv`, `CueAsk`, `CueEnd` — ariadne's self-terminated cues.
    pub cue_ev_tag: i64,
    pub cue_ask_tag: i64,
    pub cue_end_tag: i64,
    /// A voice constructor's tag to the bank it belongs to —
    /// `audiodynamic`'s `by_tag`, which the wire's third word is
    /// looked up in.
    pub voice_banks: &'static [(i64, usize)],
    /// A `holds.<bank>` channel id to the bank it names —
    /// `audioscore.ports_of`.  This is the world a listening piece
    /// asks: `hear holds.keys` reaches here, and the answer is the
    /// keys the player is holding on that bank.
    pub holds: &'static [(i64, usize)],
}

impl Program {
    pub fn bank_of(&self, tag: i64) -> Option<usize> {
        self.voice_banks.iter().find(|(t, _)| *t == tag).map(|(_, b)| *b)
    }

    /// Which bank a question is about, if any.  A channel the program
    /// never declared as a port reads as silence rather than as an
    /// error — an unplugged port holds nothing, which is exactly what
    /// the Python reader answers.
    pub fn port_bank(&self, chan: i64) -> Option<usize> {
        self.holds.iter().find(|(c, _)| *c == chan).map(|(_, b)| *b)
    }
}
