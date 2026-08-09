# Export — the instrument leaves the workshop

*Written as a design; the CLAP shell's skeleton is built now
(`shell/clap/`, in **Rust** rather than the C this file first assumed —
CLAP is a stable C ABI, so Rust reaches it with no runtime and better
honesty about null and lifetime than a shim deserves to need).  The
crate hand-declares the CLAP subset it uses (`src/abi.rs`, no
dependencies, builds offline), exports `clap_entry`, and is an *empty*
factory until `python -m gestate.export` — **written now** — emits
`src/descriptor.rs` and the graph's static archive beside it and
builds with `--features engine`.  `test/test_export.py` is the parity
this file demands, as a miniature ctypes CLAP host: the exported
artifact renders what `run_native` renders, refuses the wrong sample
rate, advances state across blocks, and answers for
`clap.audio-ports` — the extension a real DAW configures buffers
from, whose absence is a plugin that loads and sits silent.  Two
facts found on the way in: the engine's state buffer starts
**zeroed** (the generated code's first-instant branch seeds every
`init` itself, so no state image travels), and the whole engine
contract is one symbol plus that buffer and the control slots.
Self-playing synths export today (`dubgate.clap`, `violin.clap`),
and they **follow the transport, stop meaning rewind**: silence while
the timeline is stopped, and the rising edge zeroes the state — which
is the rewind, since the generated code reseeds everything at `t = 0`
— so two plays are the same performance, proven by the replay block
being byte-identical to the first (`test_export.py`).  A null
transport is a free-running host and the instrument simply plays.
Still to come, in order of need: the **params** extension from the
`mkKnob` table the descriptor already carries; **note ports**, which
is the big one — the live note-to-channel assignment lives in
Python's allocator and the shell needs its own; `clap.state`
save/load as a `State` snapshot; more than one compiled rate.*

Everything gestate produces is audible only to someone holding this
repository, a Python, and an LLVM.  The synths cannot be handed to
anyone: not as a plugin in a host, not as a page in a browser, not as
a binary on a desk.  The courses teach an audience that has no way to
arrive.

The whole of this design rests on one observation:

> **The static fragment is already the contract every plugin host and
> browser demands — fixed memory, bounded work per block, no
> allocation after the first instant.**

Other languages fight for that property with subsets, annotations and
prayer.  Here it is the admission test the compiler already runs, so
an exported synth cannot be built that violates the host's rules.
Export is not a new backend; it is the existing one meeting a smaller
host.

## What the host surface actually is

The engine's whole interface is four things, and `audioengine.py`
names them all:

* `State.initial(graph)` — the memory, sized once.
* `render_block(graph, state, n, control)` — fill a buffer.
* `control(node_id, t)` — one scalar per control channel per block,
  which is what a knob is (`mkKnob`) and what a DAW automation lane
  is.
* `migrate(old, state, new)` — carry the running state across a
  recompile.

Notes arrive as the `voices` channels (`gateAt`, `offAt`, payload),
which is what MIDI already is by the time `FromMIDI` has spoken.
Nothing else crosses the boundary.  A host shim — in C for a plugin,
in JavaScript for a worklet — has four functions to wrap.

## Target one: the browser playground

`audiollvm` drives LLVM at the native triple; the same IR at
`wasm32-unknown-unknown` is the same synth in an `AudioWorklet`.  The
block loop and the knob bindings are a page of JavaScript; the
compiler itself stays home — **the playground ships compiled graphs,
not the compiler**, in its first cut.  That is enough for every course
lesson to be *playable where it is read*, knobs included, which is the
audience door this project does not have.

The second cut — the compiler in the browser, editing live — is a
larger question because the compiler is Python.  It is deliberately
out of scope here: a playground of precompiled lessons is most of the
value at a fraction of the weight, and stage-5 live editing over a
websocket to a host-side compiler is a respectable bridge (the editor
already speaks exactly that protocol to its own engine).

## Target two: a CLAP plugin

CLAP over VST for the usual reasons: open, sane threading, first-class
parameter events.  The mapping is nearly mechanical:

* plugin parameters ⇄ the program's `mkKnob` declarations — name,
  default, and the clamping the knob already declares;
* `process()` ⇄ `render_block`, with the parameter events delivered
  as the block's `control` values;
* note events ⇄ the bank channels, through the same assignment the
  live host uses;
* plugin state save/load ⇄ the `State` snapshot — and **preset
  loading under a running transport is `migrate`**, which is a thing
  commercial synths do not have: a preset that changes the filter
  without resetting the oscillator's phase.

The shim is C calling a static library the LLVM backend emits.  No
Python at runtime, because there is no runtime: the graph's memory is
a struct and its step is a function.

## What export must refuse

A program is exportable exactly when it is in the static fragment
*and* names no renderer capability the target lacks — today that is
nothing, since `ticks`, `sampleRate`, the channels and the delay lines
all compile to the same IR everywhere.  When `spec/sampling.md` lands,
a sample is a preloaded buffer and travels with the export; a live
*input* is a host capability the plugin has and the first-cut
playground does not, and the check must say so by name, the way
`internals.py` says what to reach for.

## Costs, stated

* A C shim and a JS worklet host — two small foreign-language
  surfaces in a repo that has none.  They are hosts, not features:
  the rule that the graph is exactly what the source says keeps them
  from growing opinions.
* The LLVM backend gains a second triple and loses the assumption
  that `tmpdir` is a place programs run from.
* Versioning: an exported `State` outlives the session that made it,
  so a snapshot needs the graph's shape hash beside it — `migrate`
  already refuses on shape, this writes the refusal down.
* Offline `.samples` goldens gain a sibling: the exported artifact
  must render the same bits as the engine that made it, which is one
  more parity test in a project that already lives by them.
