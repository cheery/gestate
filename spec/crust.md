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
workbench.  **The plugin carries the machine now**: `shell/clap` takes `crust`
as an rlib under a `dynscore` feature — no FFI, the workspace's stated
purpose finally paid — and an exported plugin forces its own unfolding
score (`spec/dynamicscore.md`).

**And the reactive half has its foundation**, which turned out to rest
on one decision.  A signal cell is a *place*: it is mutated where it
stands and the driver keys its clocks by where it stands, so a
semispace copy that relocated it would break every table keyed by cell.
So the cells do **not** live in the heap.  `Machine::sigs` is a stable
arena with a free list; `Node::Sig(SigId)` is how the heap points at
one; and the collector marks rather than moves them, rewriting only the
fields *inside* each live cell.

**Refcount for the host, tracing for the heap** — the two answer
different questions and the design needs both.  A copying collector
cannot maintain a true refcount, because dead nodes are never visited
and so never decrement; but it *can* mark what it reaches.  What it
cannot see is a cell the driver holds between steps while the program
has momentarily dropped it — and that is exactly a signal's life.  So
`sig_retain`/`sig_release` pin what the host is holding, the trace
keeps what the program can still reach, and a cell dies when neither
wants it.  `sig_release` deliberately frees nothing on its own: a cell
at zero is only one the *host* has finished with.

`SigCons` and `SigHead` are in, with the ✓ frontier checked at the
read (Rizzo §4.1) — a premature read refuses rather than quietly
answering last step's value, which with in-place update is the only
thing standing between a scheduler-ordering bug and silent staleness.
**`MkDelayAp` is deliberately absent**: its only interpreter-side
caller is the audio *oracle*, and the oracle is the meaning the
compiled engines are checked against, so porting it would delete the
thing doing the checking.

**And the substrate crosses now.**  The sweep is ported
(`crust/src/reactive.rs` — `ticked`, `advance`, `update_one`,
`reactive_step`, all six ⃝∃ forms, the `Sync` packing), the `Sub` walk
with it (`shell/panel/src/substrate.rs`), and
`shell/panel/tests/substrate_parity.rs` runs
`examples/audio/substrate.ges` as the compiler produces it: forced on
`crust`, walked, and drawing what `gui.py` draws item for item —
then advanced by `reactive_step`, with the picture following the
channel each instant.  That is the first *signal* program this machine
has run, so it is also the check on the arena, on the now heap as a
GC root, and on `SigHead`'s ✓ frontier.

**`MkDelayAp` had to come after all**, and the reasoning that left it
home was wrong: `compile_c` emits it for every delayed application, so
`:::` and `mkSig` are built from it and no substrate crosses without
it.  What must not move is the *oracle* — the Python render that says
what a graph means — and that is a question of which implementation is
authoritative, not of which instructions this one knows.

**And text crosses on the tags it already had.**  `Label w h s c` puts
a `String` in a `Sub`, and a `String` is `List Char` with a `Char` its
code point — so a caption on the wire is a cons list of `Num(I)`, which
this machine has carried since the score did.  No new node kind, no new
instruction; the substrate's tag table grew by `Cons` and `Nil`, which
is the entire cost.  Worth stating because the obvious fear about text
was a string node, an interning table and a comparison primitive, and
none of it was needed: the language had already answered what a string
is.

**And a host drives both at frame rate.**  `shell/panel/src/canvas.rs`
turns the loop — arrivals, `reactive_step`, `main`'s cell, walk, paint
— once a frame on the plugin window's own thread, while the score is
forced on the audio thread.  Two programs on two machines in one
plugin, neither waiting on the other.

Not yet: the offline CLI's dynamic path.  The reference driver's
`cl`/`ticked` cross-check is deliberately not ported: it checks
`reactive.py` against itself, and crust is checked against
`reactive.py`.*

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
