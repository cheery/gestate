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
under one transport rule for every plugin: **it plays while the
transport runs, or while a note does.**  Self-playing material is
silent while the timeline is stopped, and the rising edge rewinds to
the piece's top (two plays are the same performance, proven by the
replay block being byte-identical to the first) — but the knobs
survive the rewind, because a knob's value is the host's belief; and
a held or ringing voice keeps the render alive regardless, ten
seconds of tail after release, so a keyboard is auditionable with the
timeline stopped and a hybrid gets both halves of the rule at once.
The transport is handled before the events drain — learned the hard
way, when the first note of every play shared a block with the play
edge and was rewound away.  A null transport is a free-running host
and everything simply plays.
**Knobs are DAW parameters now** (`clap.params`): a control channel is
a parameter unless the `voices` expansion generated it — automation
into a bank's payload field would be a note nobody played — with the
author's own names (`cutoffChan` shows as `cutoff`), the program's own
defaults, `Int` knobs stepped, and events applied at block start
because control rate in gestate *is* once per block.  The range is the
exporter's stated heuristic (`export._range_of`) until the language
declares ranges.  Proven the strong way: a `PARAM_VALUE` event into
the plugin and a `control` answer into `run_native` are the same fact
through two doors, and the samples must not know which
(`test_the_knobs_are_the_daws_parameters`).  **Note ports are in**: a
keyboard plays the first declared bank through a Rust mirror of
`audioalloc` (released-longest-ago first, oldest stolen, oldest
released per key), payloads come from the program's own `FromMIDI`
instance run through the G-machine *at export time* and tabled — 128
keys × 32 velocity levels, full velocity exact — with the live path's
structural `(key, velocity)` fallback for banks without an instance,
and onsets stamped `t + event.time` so a mid-block note begins at its
own sample.  The parity is the strictest yet: a NOTE_ON through the
plugin's port equals the same note through Python's allocator and
schedule, sample for sample (`test_a_played_note_is_the_scheduled_note`)
— both halves are second implementations, which is where bugs live,
so both are held to the first.  **Every bank exports, routed by a
matrix**: one stepped 0/1 parameter per (bank × MIDI channel), module
`routing`, so a DAW's generic parameter view *is* the checkbox matrix
— no GUI extension needed.  The default is the diagonal
(`audiomidi.by_midi_channel`'s rule, channel *n* plays bank *n*), a
ticked cell layers banks on one channel, releases search every bank
so a matrix change mid-note cannot strand a voice, and the matrix
survives the rewind (host belief, like the knobs).  Parity:
`test_the_routing_matrix_layers_banks` holds the layered notes
against one Python allocator per bank.  **The session remembers**
(`clap.state`): knob slots and routing rows save behind a magic, a
version, and a shape hash of the exported program — a preset from a
different export refuses to load rather than pouring bits into the
wrong slots, and engine state deliberately does not save: a note
mid-decay belongs to the take, not the project.  Both roundtrips are
tested into fresh instances.  **Multi-rate**: a plugin carries one
whole compiled graph per rate (default 44100 and 48000 — `sampleRate`
is folded through the program, so honesty at two rates is two
graphs), the entry symbols renamed per rate in the IR text and
`objcopy` localising everything else so the objects link side by
side; `activate` picks the case the host names and still refuses the
rest.  **`beat` and `beatRate` are the renderer's own, and in a DAW the
renderer is the transport** — the context contract in force, and
`tempoChan` retired the same day it was confessed.  The exporter
assembles with a host-fed clock in the derived `beat`'s place
(`export.host_clock`, through the `clock_text` seam both assemblies
now carry): three descriptor-declared slots carry a *line* — beat at
a recent block start, beats per second, the anchor sample — and the
program's `beat` evaluates it at `ticks`, audio-rate smooth however
coarsely the host updates it.  `beatRate` is the middle channel bare:
how fast the piece is going, in beats a second.  Nothing is spelled
in the shell — the slots travel as `BEAT_SLOTS` in the descriptor —
and nothing is advertised as a parameter.  A timeline host pins the
position; a tempo-only host gets the shell's accumulation; a stopped
transport freezes the clock by zeroing the slope; and a free-running
host leaves the channels at their defaults, where the program
conducts itself at its declared `bpm` exactly as it does offline.
The program's own `bpm` and `tempo` are not discarded in a DAW; they
are how gestate-as-its-own-renderer answers the same name, and the
free-running default besides.  Still to come: the
velocity table's 32 levels, the day somebody hears them; a `clap.gui`
panel is *deliberately deferred* — it is the one extension that is a
project rather than an evening, and gestate's GUI energy belongs to
`spec/editor.md`'s type-derived widgets first.  When it comes, the
routing matrix drawn from the descriptor is its first panel — and it
brings the real dependency with it: a substrate is interpreted, so
the panel (and the playground's editing cut) eventually needs **the
G-machine ported to Rust**, held against `gmachine.py` the way the
engines are held against each other.  `spec/substrate.md` draws that
line; the tabled `noteOn` is the export dodging it for notes, and it
dodges no further.*

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
