# G-machine implementation in Rust

*Status, 2026-08-10, second wave: the pure core is built and floats
are in.  `crust/` at the repo root carries the score-forcing
instruction set — i128 arithmetic refusing wider, Python's floor
division exactly, and now `f64` beside the integers in one `Num` the
way `NNum` holds either, with CPython's own float `%` and `//`
transcribed and literals crossing the seam as IEEE bits (canonical
floats print as bits too: float parity is bit parity).  The whole
SplitMix64 block crosses now, `unit`'s uniform draw included — and
porting it found a real ceiling: a 64×64 product overflows a signed
128-bit machine by one bit, which Python's widthless integers never
noticed, so `music.ges` gained `mulWrap` (the multiply split at 2³²,
bit-identical mod 2⁶⁴, no draw moved).  The workspace exists: a
root `Cargo.toml` joins `crust` and `shell/clap`, with `--target-dir`
pinned at both call sites so no artifact path moved.  **The machine is
in-process now**: the crate builds a `cdylib` beside the binary, five
`extern "C"` functions (`src/lib.rs` `ffi`, panics caught at the
boundary, errors as messages), and `gestate.crust.Native` loads it
over ctypes — the `audiollvm` pattern, zero new dependencies on
either side, PyO3 considered and declined for exactly that reason.
Loading a compiled program costs ~3 ms, one eager score layout ~0.3 ms
against ~3 ms interpreted — 14× on the layout benchmark, bit-identical
answers, the heap persisting across forces.  **The forcing protocol and the
collector are built, together, as the rule demanded**: `Stream` in
`src/lib.rs` is `audiodynamic.ScoreStream`'s twin — resumable fueled
pulls to a tick horizon, the frontier/stall facts kept across calls,
a parked forcing living in the machine's own registers — and the
Cheney semispace copy runs between pulls, the pull-to-pull window
being exactly the workload that justifies it (800 bars of an endless
seeded cycle hold under two million heap nodes, events identical to
the reference throughout).  The wire is rung one as decided: flat
i64s over ctypes — `[onset, offset, voice_tag, nfields,
(kind, value)…]` per event, floats as bits — read by
`gestate.crust.NativeStream`, with `native_stream` as `stream_root`'s
twin.  And the host machinery needed *no change*: `LazyPerformer`
drives a `NativeStream` as it drives the reference, change for
change, because `getattr(stream, "ask")` was already its only
probe-shaped assumption.  **The live extension is in and the
editor is plumbed**: cue cells decode beside the plain triples
(`CueAsk` parks as a question, not a stall; `crust_stream_answer`
splices the reading into the continuation, `NAp(k, list)`, and the
spine walks on), the wire carries payload *structure* (kind 2 opens a
constructor; `history` is an interface the editor indexes into, so an
event off the wire is the reference's event, nesting and all), and
`audioeditor` routes every dynamic piece through the twin — the state
already compiled, the seam costing one serialization and a ~3 ms
load — falling back to the reference machine on any `CrustError`,
which is never wrong, only slower.  The arpeggiator scenario runs
change-for-change identical over either machine, readings included,
and the pygame bench inherits the routing by riding the same
workbench.  Not yet: the reactive half (the substrate's, when the
panel moves in), and the offline CLI's dynamic path, which could take
the same route whenever someone wants the render sooner.*

For now this is a proposal.

By now it has become necessary that various facets of gestate
would run lazily in wherever it gets deployed.

I think it's time for porting the G-machine to rust,
and running the programs on it.

Compiler remains written in Python, but the G-machine,
if it's faster than python implementation,
may be imported as a python module.

Proposal that the g-machine would be named "crust" or "grust" and placed
in the main directory, unless there's a reason to do otherwise.

---

*(Claude, chiming in — 2026-08-10, while stage one's parity tests run.)*

**Yes — and the codebase has already said so twice.**  `spec/substrate.md`
draws the line at its end: a `clap.gui` panel is a substrate, a substrate
is interpreted by design, so the panel needs the G-machine inside the
shell and the playground's second cut needs it in WASM — one Rust port
serves both landlords, `gmachine.py` stays the reference it is held
against.  And `spec/dynamicscore.md` stage two is where the port "stops
being about the GUI and starts being about the music": an exported plugin
cannot force `cycle (bar >>= voices.kit)` without a machine to force it
on, and until then its descriptor carries a finite prefix, honestly
truncated.  So the port has two paying customers before a line of it
exists, and each brings its own oracle — the `Sub` tree for the canvas,
the score's event list for the music.

**The inventory is bigger than the textbook machine, and the excess is
where the design work is.**  `gmachine.py` is ~1500 lines: the seven
classic instructions, then some forty in all — `Pack`/`CaseJump`/`Proj`
for data, the arithmetic pairs — and then the part no textbook chapter
covers: `SigCons`, `SigHead`, `NewChan`, `MkDelayAp`, with `NSig` and
`NChan` beside `NNum`/`NAp`/`NCon`/`NInd` on the heap.  The pure core is
a known walk; the decision that wants care is whether the reactive half
crosses in the first cut.  I would say no: stage two's performer needs
exactly "force a cons list to a beat horizon" — `Unwind`, `Mkap`,
`Update`, `Pack`, `CaseJump` and friends — and it is the customer with a
deadline (a beat-horizon *budget*, per dynamicscore's stall rule).  The
channels can stay home until the panel forces the issue.

**What crosses the boundary is a compiled program, not Python.**  The
compiler stays where it is, so the interface is a serialization:
instruction list, globals, the constructor table.  The CLAP descriptor
already proves this pattern — tables written by Python, read by Rust,
no Python at run time — and one format serves three masters at once: a
PyO3 module for the parity harness (and for `python -m` paths that want
the speed), an rlib for `shell/clap`, a `wasm32` target for the
playground.  The Python-importable module is the *harness* more than the
deployment; the deployments are the shell and the browser.

**The Rust-specific question is the heap.**  Python got graph reduction's
mutation for free — `Update` overwrites a node, the GC sweeps up.  The
natural Rust shape is an index heap: `Vec<Node>`, `u32` indices, `NInd`
as the redirect — laziness *is* mutation, and indices make it safe
without `Rc<RefCell>` ceremony.  Collection can start embarrassingly
simple, because the performer's working set is a window: force to the
horizon, play what appeared, drop what the cursor passed.  A semispace
copy between blocks — off the audio thread, like every note-deciding
thing already runs — likely covers the music for a long time; the panel
can pay for something better when it moves in.

**Parity, the house way.**  Same compiled instructions in, same forced
values out: `perform_voices`' event list for a piece, the `Sub` tree for
a substrate, and stage two's own clause when it lands — a lazy score
forced by crust equals the same score forced by `gmachine.py`, event for
event, seed for seed.  The speed goal has a number already on record:
five seconds of interpreter to lay out `quartet.ges` (`audioscore`'s
cache docstring).  The port should make that a rounding error, or it has
not paid its way in.

**Name and place.**  `crust` reads well — the Rust crust around a Python
core is literally the architecture, and `grust` says the same thing less
kindly.  On placement, the main directory is right, but for a reason
worth writing down: `shell/README.md` defines that directory as *shims
with no opinions*, and the G-machine is the opposite — it is the
interpreted core, traveling.  So: `crust/` at the root as its own crate,
and a workspace `Cargo.toml` beside it so `shell/clap` and `crust` build
as one tree and the shell can take the machine as a dependency the day
the panel needs it.
