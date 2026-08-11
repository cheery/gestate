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
* **`panel/`** — the plugin's own window (`spec/panel.md`): a display
  list, a software painter and the two panels the descriptor already
  knows about (knobs, note routing).  It is where the dependencies
  live, which is what lets the sentence above stay true — `clap/`
  takes it only under its `gui` feature, and without that feature
  `cargo tree -p gestate-clap` is still one line.  The pure half
  builds and tests with no dependencies at all; `--features window`
  adds `baseview` and `softbuffer`.
* A `worklet/` for the browser playground belongs here when its day
  comes.

## When a plugin misbehaves in a DAW and not in a test

Record the host's own boundary and replay it here — the transcript is
`spec/verification.md` §"Recording a host", and it exists because a
harness is a guess about the host:

    GESTATE_TRACE=/tmp/nd.trace reaper        # provoke it, then quit
    python test/replay_trace.py /tmp/nd.trace ~/.clap/nightdrive.clap 48000

The rate argument must be the rate the recording was made at.  Off
unless `GESTATE_TRACE` is set, and real-time safe when it is.
