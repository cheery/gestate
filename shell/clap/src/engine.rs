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

/// One control channel, in buffer order — a `mkKnob`, or a channel a
/// score writes.  `init_bits` is the slot's value before anyone moves
/// it: the program's own declared default, already reinterpreted.
pub struct Control {
    pub chan: &'static str,
    pub kind: Kind,
    pub init_bits: i64,
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
