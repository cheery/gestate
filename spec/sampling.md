# Sampling and audio input — the world enters the graph

*Written as a design; none of it is built.  Companion to
`spec/delaylines.md`, whose machinery this mostly reuses.*

Every signal in gestate today is conjured: oscillators, noise, the
score.  Sound goes out and nothing comes in — no recorded material, no
microphone.  The two features are one design because they are the same
node with different lifetimes: **a sample is a buffer filled before
the program starts; an input is a buffer the host fills as it runs.**
Both are reads; neither is allocation.

## Samples: the preloaded line

`spec/delaylines.md` built four static-length buffer nodes and one
whose read head is a signal (`slide`).  A sampler is that read head
over a buffer that arrives loaded — a **sixth node kind**, `wave`: a
read-only line whose contents and length come from a file at assembly
time.  The fragment's theorem is untouched, because the length is
known the moment the file is: fixed memory, decided before the first
instant, exactly as a delay line's is.

Surface form, following the renderer-supplies-what-it-owns rule:

    kickWave : Wave
    kickWave = sample "samples/kick.wav"

`sample` is assembly syntax the way `voices` is: the path is resolved
against the program's own directory, the file is read *then*, and its
length and rate become facts of the graph.  `Wave` is a value naming
the buffer — an ordinary thing to pass to functions, sized like a
`Score` is scheduled: entirely at compile time.

Reading is where the reuse pays.  `slide` already implements a
fractionally-positioned, interpolated read over a line — a sampler's
read head *is* that read, minus the write half:

    playAt : Wave -> Sig Float -> Sig Float      -- position in samples
    rate   : Wave -> Sig Float -> Sig Float      -- a position ramp: pitch

`playAt w pos` is the primitive — the tape machines of `dubgate.ges`
are evidence the fun cases (warble, scrub, reverse) fall out of the
position being a signal.  `rate w r` is the derived spelling a
sampler wants: a phase ramp at `r` times natural speed, wrapped or
one-shot from a gate's `onset`.  Resampling across source rates is a
multiplication on the ramp, done once at assembly where both rates
are known.

**Offline determinism is free**: a sample is program text plus a file
the assembly hashed, so golden `.samples` tests cover sampled
programs with nothing added.

## Input: the channel that carries a block

A control channel (`chan`) already lets the host write **one scalar
per block** into the graph.  Input is the audio-rate sibling: a
channel whose slot is a block's worth of samples, filled by the host
before each `render_block`.  In the graph it is a source node like
`ticks` — no state, no feedback question, in the fragment by
construction.

Surface form, the renderer's own (beside `ticks` and `sampleRate`,
supplied not declared, because which microphone exists is the
renderer's fact):

    input : Sig Float

* **Live** (`audiolive`, a future plugin): the host copies its input
  buffer in; latency is the block, which is the same honesty the
  control channels already have.
* **Offline** (`audio`, `audioperform`): `input` is silence unless
  the render names a file — `--input take.wav` — which turns an
  offline render into deterministic reprocessing, and makes input
  programs *testable*: a golden with a `.wav` beside it.
* A program that names `input` where the renderer has none gets a
  refusal naming the flag, `internals.py`-style, not a silent zero.

`gateOn` was built for this half without knowing it: an envelope
follower over a threshold (`follow`, then `gateOn`) turns the
microphone into notes, and every envelope in the library reads the
result as if a keyboard had sent it.

## What is deliberately not here

* **No streaming from disk.**  A `Wave` is resident; the fragment
  admits no buffer whose size the program discovers.  A sample too
  large to be resident is an arrangement problem, not a node kind.
* **No recording into a `Wave`.**  Writing into a named buffer at
  runtime is a looper — a real instrument, and a different spec,
  because it reopens the read-only claim that makes `wave` shareable
  between voices for free.
* **No automatic pitch detection, slicing, or time-stretch.**  Those
  are programs, and the library can write them out of `playAt` the
  day someone wants one.

## Costs, stated

* A sixth node kind through the whole vertical: extract, both
  engines, `zero`/`migrate` (a `wave` migrates by *identity* — the
  buffer is immutable, so the state is only the graph's, which is the
  cheapest kind), and the LLVM layout for a read-only blob.
* Assembly grows file IO and therefore a failure mode it never had —
  a missing sample file is a compile error with a path in it, and the
  error must carry the author's line the way `audiospans` already
  moves positions.
* `audiollvm`'s artifact is no longer pure code: the blob rides in
  the module as a constant, which `spec/export.md` inherits — an
  exported synth carries its samples.
* The reference engine and the compiled one must interpolate
  *identically* — `slide` already holds that line, and `wave` reads
  must sit on the same arithmetic or the parity tests will say so.
