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

#[cfg(feature = "engine")]
mod linked {
    include!("descriptor.rs");

    extern "C" {
        pub fn render_block_f32(state: *mut u8, out: *mut f32,
                                frames: i64, control: *const i64);
    }
}

#[cfg(feature = "engine")]
pub use linked::render_block_f32;

#[cfg(feature = "engine")]
pub static DESCRIPTOR: Option<&Descriptor> = Some(&linked::DESCRIPTOR);

#[cfg(not(feature = "engine"))]
pub static DESCRIPTOR: Option<&Descriptor> = None;

#[cfg(feature = "engine")]
pub static BANK: Option<&Bank> = linked::BANK;

#[cfg(not(feature = "engine"))]
pub static BANK: Option<&Bank> = None;

/// The render call, with the no-engine build honest about itself: a
/// shell with no graph linked writes silence and could never be asked
/// to, because its factory offers no plugin.
#[allow(unused_variables)]
pub unsafe fn render(state: *mut u8, out: *mut f32, frames: i64,
                     control: *const i64) {
    #[cfg(feature = "engine")]
    render_block_f32(state, out, frames, control);
    #[cfg(not(feature = "engine"))]
    std::ptr::write_bytes(out, 0, frames as usize);
}
