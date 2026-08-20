---
name: gestate-verify-workflow
description: "How to verify gestate synth examples fast (LLVM path, not the slow reference renderer)"
metadata: 
  node_type: memory
  type: project
  originSessionId: a1462242-2c42-465a-b030-147d44823d59
  modified: 2026-08-14T15:59:59.201Z
---

Verifying gestate `.ges` synths (learned 2026-08-09):

- `python -m gestate.audio` is the **slow reference engine** (correctness
  oracle); the user wants the **fast LLVM path** for iteration.
- Fast offline render: `gestate.audioextract.extract(source, rate=…)` +
  `gestate.audiollvm.run_native(graph, tmpdir, samples, block=…)` — a
  scratchpad script wrapping these reports peak / writes wav in seconds.
- Scored/voices synths: `python -m gestate.audioperform file.ges -o out.wav
  --seconds N` (offline through the compiled engine).
- Music-only programs (`score` + `bpm`, no `sound`): `python -m gestate.midi
  file.ges --events`; programmatic: `gestate.midi.perform(source)`.
- Everything must run from the repo root or with
  `PYTHONPATH=/home/cheery/gestate` (the venv doesn't install the package).
- Offline rendering drives every control channel/knob with the **sample
  index**, so unclamped controls render as `inf` — clamp at the boundary.
- `test/test_courses.py` builds all of `examples/{beginner,intermediate,
  advanced,super}` via `audioperform.graph_of`; `test_examples.py` sweeps
  compile all of `examples/audio` + `contrib`, draw every canvas example,
  and (2026-08-14) *play* `examples/long/*` headless the whole way —
  `audioperform.dynamic` at rate 4000, walk the `--seconds N` the header
  states, fail on the first `("stall", beat)` transcript confession,
  assert `record.confessions() == {}` and the last event lands in the
  final tenth.  ~11s per 20-min piece; catches the sauna specimen in 3s.
- **Checking a mix** (2026-08-14): `audioperform … --report` prints peak
  + per-bar RMS after an `-o` render.  For a long piece, profile faster
  with `graph_of` + `dynamic` + `native_blocks` straight (scratchpad
  `mixstat.py`), per chapter: peak, RMS, and **share of samples at the
  ceiling**.  Compare against the same source with `brickwall X`
  replaced by `gain 1.0` — that shows what the limiter is hiding.  A
  mix whose chapters all measure the same RMS has been flattened by
  its own limiter.  `test_examples.py::test_every_long_piece_keeps_headroom`
  now guards this (first 60 s, <1% at the ceiling).
- **Checking what a dynamic score actually plays** (2026-08-10): drive the
  performer headless — `stream_root(src, "", RATE, seed, 0, True)` (synth
  and piece are two texts; self-contained file goes in the first slot),
  allocators `{b.name: Allocator(channels_of(src, b)) for b in
  banks_of(src)}` (audiovoices), then `LazyPerformer(LiveStream(...),
  tempo, RATE, allocs, block=BLOCK, reader=lambda port: [...])` and read
  `.history` tuples `(tick, ?, bank, ((vel, key), ...))`.  `reader`
  simulates held keys for `probe`/`holds` pieces; import BLOCK/RATE from
  test/test_dynamicscore.py.  Probe pieces render SILENT offline without
  --midi (empty hands by design) — silence there is not a bug.

- **Rust shell builds (2026-08-14): plain `cargo build` in shell/editor
  DOES NOT compile `window.rs`** — it's behind `#[cfg(feature =
  "window")]` (implied by `capi`).  A featureless build finishing in
  0.05s after a window.rs edit is not stale fingerprints; it built a
  library without the window.  Verify with `cargo build --features
  capi`; the workbench loads
  `shell/editor/target/release/libgestate_editor.so`, rebuilt by
  `editor.py` when stale or by hand with `cargo build --release
  --features capi --target-dir shell/editor/target`.
- **Screenshot verification of the live editor**: tools/lagcheck.py has
  `find_window`, `shot`, `tap`, `chord`, `click_into`; XTEST drags via
  `XTestFakeMotionEvent`/`XTestFakeButtonEvent`.  Compare frames with
  `compare -metric AE a.png b.png null:` for is-it-animating.

Related: [[gestate-language-pitfalls]]
