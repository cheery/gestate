# shell/ — the hosts an exported graph sounds through

`spec/export.md` is the design; these are its shims.  A shell wraps the
engine's two-symbol contract (`render_block_f32`, and a zeroed state
buffer the generated code seeds itself) in whatever a foreign host
demands, and has no opinions of its own: the graph decides the channel
count and the rate, the descriptor carries them, the shell moves
blocks.

* **`clap/`** — the CLAP plugin, in Rust (`cargo build` yields the
  `.so` a DAW loads; `cargo test` checks the entry chain).  Without the
  `engine` feature it is an *empty* shell — a well-formed library whose
  factory offers zero plugins — which is what CI can build with no
  instrument in it.  `python -m gestate.export` (not yet written) will
  emit `src/descriptor.rs` and the graph's object file beside it, and
  build with `--features engine`.
* A `worklet/` for the browser playground belongs here when its day
  comes.
