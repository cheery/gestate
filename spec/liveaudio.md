Live audio: from a described signal to a running engine
========================================================

The end goal is a **live audio programming environment**: you edit a synth
while it is sounding, and the sound changes.

This document records what the offline audio experiment established, what it
ruled out, and the architecture and plan that follow. It is written now,
while the evidence is fresh, so that the next person to pick it up — very
possibly the same person, later — does not have to re-derive any of it.

**All six stages are built. A gestate synth can be heard, and edited while
it sounds, in a window.**

    python -m gestate.audioeditor examples/audio/knob.ges

The golden buffers, the fragment and its checker, graph extraction, block
rendering, LLVM code generation, a driver that plays the result out of a
sound card in real time, and live update that carries a running
oscillator's phase across a recompile, and an editor to do it from. A
synth compiles to machine code that runs at **593× real time** and is
bit-identical to the interpreter that described it.

What is left is not another stage but two things this found: the
control-clock disagreement in open question 3, and an editor written in
gestate rather than hosting it — §"The plan" says where each stage stands
and what it found.

    gestate/audio.py       the offline renderer — the oracle
    gestate/audiograph.py  is this synth in the fragment?
    gestate/audioir.py     the flat graph, and the IR in its nodes
    gestate/audioextract.py  a Sig Float becomes that graph
    gestate/audioengine.py   runs a graph; render_block
    gestate/audiollvm.py     the graph becomes LLVM IR
    gestate/audiolive.py     …reaches a sound card, and reloads on edit
    gestate/audioeditor.py   a window to edit it in while it plays

See `fixme.md` F88, F90 and F91 for how the audio backend came about.


What the experiment established
--------------------------------

The question the offline renderer was built to answer was **not** "is this
fast enough". It was: *does this language say what a synth is, well?*

The answer is yes, and more strongly than expected.

**An oscillator, an envelope, a filter and a noise source are all the same
construct.** They are `scan` — a fold over time. That is not a coincidence
of how `examples/audio/blip.ges` was written; it is what those things *are*,
and the language obliged the writer to notice:

    lowpass k s = scan (y x => y + k * (x - y)) 0.0 s

A signal in, a signal out, memory held by the fold. Chaining those is a
signal graph expressed as ordinary function composition — no wiring
vocabulary, no separate graph language.

**The type system already guarantees the two things that kill audio code.**
Guarded recursion — the recursive call under a `delay` — means every signal
is *productive*: it always has a next sample and cannot deadlock waiting for
its own. And a signal is a heap cell overwritten in place, so nothing
accumulates; a synth's memory is its state and not one byte more. In most
FRP systems those are disciplines the programmer follows. Here they are
conditions for the program to compile.

**Determinism falls out.** `examples/audio/drums.ges` has no random source:
its noise is a fold over an LCG seed, so the same program renders the same
file every time. That is a property worth having in a sound you intend to
keep, and it was not designed in — it is what "a fold over time" forces.

**Multiple voices needed `zipSig`, and getting it right taught the clock
lesson.** Two signals need not tick together, so combining them is not
pairing their tails but asking `sync` which arrived and carrying the other
over. That carrying is sound *because* signals are cells overwritten in
place. The multi-clock structure is already in the language, honestly, and
§"Two clocks" below is where it becomes the engine's control rate.


What it ruled out
------------------

Measured on this machine, after the performance work of `fixme.md`
F75–F79:

| what | rate |
|---|---|
| G-machine, raw | 1.1–1.3 M instructions/sec |
| a reactive tick (`map` over a channel) | ~8,600 instants/sec |
| `blip.ges`, per sample | ~1,400 samples/sec |
| a GUI frame (`bounce.ges`) | 0.77 ms — ~1,300 fps of headroom |
| **what real-time audio needs** | **44,100–48,000 samples/sec** |

So audio is roughly **30× short for one voice**, before polyphony, and the
GUI has two orders of magnitude to spare. Those two facts together are the
whole architecture.

**A faster interpreter does not close the audio gap**, and this is the point
to be firm about. Thirty times faster would buy one voice with no headroom.
More fundamentally, a G-machine allocates a graph node and chases pointers
per reduction; audio DSP wants flat buffers, no allocation and no collector
pause. Making graph reduction fast is optimising the wrong shape. **This is
a compilation-target problem, not a host-language problem**, and changing
the host would spend the effort in the wrong place.

**The GUI needs nothing.** It runs today, in the same signal vocabulary, at
1,300 fps of headroom. Whatever the live environment's front end becomes, it
does not need a faster evaluator either.


The architecture
-----------------

SuperCollider's split, arrived at from the other direction: **sclang
describes an instrument, scsynth runs it.** sclang is garbage-collected and
not real-time; scsynth is C++ and is. The language never enters the audio
callback.

gestate is already on the describing side. What is missing is the crossing.

    source .ges
        │  gestate compiler (exists)
        ▼
    Sig Float  ── graph extraction ──►  flat node list
        │                                    │
        │ gestate/audio.py (exists)          │  codegen
        ▼                                    ▼
    samples ──► .wav                    engine: render_block()
                                             │
                                             ▼
                                        audio callback
                    ▲                        │
                    └──── must agree ────────┘

The offline renderer stops being the product and becomes **the oracle**. Any
graph, any engine, any code generator is checked by rendering the same
program both ways and comparing samples. That is a far better position to
build an engine from than most projects get, and it is the reason to keep
`render()` and the committed `.wav` files forever.


The static signal fragment
---------------------------

This is the real design work, and the rest is mechanical.

A flat graph can only be extracted if the graph is **static**: known at
compile time and unchanging while it runs. Nothing in `blip.ges` or
`drums.ges` needs otherwise, but the *language* allows more — `chan`,
higher-order signals, `sync` between arbitrary clocks. So the audio compiler
must accept a **sublanguage**, and the type checker must enforce it.

There is precedent for exactly this move, twice: the monomorphic Datafun
sublanguage (`spec/errata.md` D9) and `[: Void :]` as "the scores the MIDI
backend will accept". This is the third, and it should look like
`gestate/subgrammar.py` — a check that runs after inference and reports
*why*, not merely *that*.

This section is **normative**: it is what `gestate/audiograph.py` enforces,
and the two are meant to be read against each other.

### The flat types

    flat  A, B ::= Int | Float | Bool | Char | 1 | Cyclic n | Bounded lo hi
                 | A × B
                 | a non-recursive data type whose fields are flat

A fifth subgrammar, and it is worth saying plainly that **none of Datafun's
four is the one wanted**, because reaching for `is_finite_eqtype` is the
obvious move and it is wrong twice over: the finite eqtypes exclude `Float`
and `Int`, which is most of what a synth is made of, and every eqtype admits
`Set A`, which is a heap structure of unbounded size. The purpose is
different. Those grammars ask whether values can be compared or iterated to
a fixed point; this one asks whether a value has a **known, fixed size in a
state struct**.

One consequence follows from that purpose and is the opposite of the other
four: **an unknown type is a rejection.** Datafun's grammars answer
"allowed" for a type variable, because refusing would make every polymorphic
set function unwritable. Here a variable is exactly what cannot be laid out,
so `a` is rejected and the fragment is monomorphic by construction rather
than by a separate rule.

`Voice Float Int` and `Kit Float Int Int` are flat. `List a` is not, and
neither is `Set`, `Sig`, `Chan`, `Box`, `Score` or any arrow.

### The signal grammar

A signal is **audio-rate** if it is built only from:

    S ::= v ::: mkSig (wait c)          -- a source, for a clock c
        | map f S                       -- one node each
        | scan f z S
        | zipSig f S S
        | g A…                          -- a definition whose body is an S
        | x                             -- a signal-typed parameter

`map` is `Functor Sig`'s method and reaches the grammar as the global
`elaborate.resolve_static_methods` leaves it in; `mapSig`, which
`signal.ges` keeps internal and the desugaring of `!` writes directly, is
the same rule under the other name. `gain`, `addSig` and `lowpass` are the
fourth case and need no rule of their own. Nothing else is admitted — in particular a bare `:::`, which is how a
signal is built by hand, and which is precisely the freedom that would make
the graph unknowable before it runs.

### Step functions

`f` in the rules above is a **definition** or a lambda written at the call
site; `z` is a flat constant expression. A step function and everything it
calls must be:

* **First-order.** No function is passed, returned, stored in a
  constructor, or reached through a dictionary. A step function may close
  over flat values from around it — `gain g s = map (x => g * x) s` is
  admitted, because `g` becomes a constant in the emitted node — but not
  over a function.
* **Over flat types.** Every parameter and every result, by the grammar
  above.
* **Non-allocating.** No set, no `fix`, no `for`, no box, no constructor of
  a non-flat type.
* **Signal-free.** No `:::`, `head`, `tail`, `delay`, `wait`, `sync`,
  `gfix` or a signal combinator. The signal structure *around* a step
  function is the graph; the step function computes a value.
* **Bounded.** No recursion, direct or mutual. A step function runs once
  per sample inside a callback with a deadline, so it has to finish in a
  number of steps the compiler can count. Structural recursion over a flat
  type would be admissible — it unrolls, a flat type being non-recursive —
  but nothing has wanted it, and admitting it means *proving* the unrolling
  terminates rather than assuming it.

### Where the check runs, and why there

After elaboration and static method resolution, before lambda lifting —
`pipeline.analyse()` is that point, and it is the only one that works.
Earlier, a class method is still a projection out of a dictionary, so all
arithmetic looks higher-order and every synth is rejected. Later, a step
lambda has become a supercombinator with a generated integer name, and the
message cannot say which definition the reader should look at.

Two things fall out of checking there, and both are load-bearing:

* A **statically resolved class method** (`__Num_Float_+__`) is a direct
  call to machine arithmetic and is admitted. One still reached through a
  dictionary is not — and since `elaborate` prepends one parameter per
  constraint, "this supercombinator is wider than its own type" *is* the
  test for polymorphism. It needs no separate rule and cannot be fooled by
  a name.

  **A constrained *definition* is now admitted too, and the rule above is
  why it can be.** `gestate/specialise.py` gives a call whose dictionary
  arguments are all constant globals a copy with them substituted in, so
  the copy is not wider than its own type and the test passes it without
  being weakened. That is what lets `synth.ges` write
  `clamp : (Ord a) => a -> a -> a -> a` and use it at `Int` and at `Float`
  in one synth; before it, the vocabulary carried `clampF` and the `F` was
  this paragraph showing through into a name. A dictionary that is *built*
  — `__dict_Eq_List__ __dict_Eq_Int__` — or passed through from the
  caller's own context is still refused, and correctly: neither has one
  answer at the call site.
* The check is over the definitions reachable from `sound`, so the rest of
  the prelude is irrelevant however it is written.

### The transformation the fragment forces

This section predicted that `blip.ges` would need one transformation and
that `drums.ges` would be "accepted as written". **The second half was
wrong**, and how it was wrong is the most useful thing stage 1 produced.

`blip.ges` was as predicted:

    notes : List Float
    noteAt n = nth (…) notes

`nth` walks a cons list *per sample* — a heap structure of unbounded size,
traversed 22,050 times a second, in code that must run in bounded time and
allocate nothing.

`drums.ges` fails **for the same reason and harder**:

    kickSteps : List Int
    kickOut  = … gate (elem (stepAt n) kickSteps) …

`elem` is polymorphic, so after elaboration it takes an `Eq Int` dictionary
— a record of functions — and is recursive over a cons list besides. So the
fragment rejects three definitions in `drums.ges` and the constant lists
they read.

**What this changes.** Lifting a constant list to an array was described
above as something "the extractor has to perform". For `nth` that is
plausible; for `elem` it means specialising a polymorphic recursive function
and erasing its dictionary, which is a great deal more than emitting a
constant array. Both examples are therefore written with the table spelled
out:

*(Half of that has since happened: `specialise.py` does erase the
dictionary, so `elem`'s remaining objection is the cons list it walks, not
its polymorphism. The tables below stay because the list is the harder
half and nothing has touched it.)*

    noteOf : Int -> Float
    noteOf i = case i of
        0 -> 220.0
        1 -> 261.63
        …
        _ -> 293.66

This is not a workaround. An integer `case` is flat, first-order,
non-allocating and total; it is the table, written down. **And the rewrite
is verified**: both examples render bit-identically to the stage-0 golden
buffers after it, which is the oracle earning its keep one stage after it
was built.

Two things to carry into stage 2:

* **An integer `case` desugars to a chain of `prim_eq_int` tests**, not to a
  jump table, so what stage 2 sees is a comparison cascade and what it emits
  will be an if-chain — eight comparisons per sample for `blip`'s tune.
  Correct and cheap, but it is not the constant array this section pictured.
  Recovering an array from the cascade is a known compiler move and is
  worth doing only if a measurement asks for it.
* **Automatic list lifting is a convenience with no caller**, and it is
  recorded rather than scheduled. If it is ever built, the natural way is
  source-to-source into exactly the `case` above, which is what the examples
  now write by hand — so nothing here forecloses it.

Expect one or two more of these. Finding them is what stage 1 is for, and it
found this one by rejecting a program the plan promised would pass.

### The fork worth deciding early

Step functions are arbitrary gestate code. To run them outside the
interpreter, either:

**(a) Compile them.** After monomorphisation and lambda lifting, a flat step
function is a first-order strict expression over `Float`/`Int`/`Bool` with
no allocation — which is a straightforward translation to C, to LLVM, or to
a vectorised kernel. More work, and the standard kind.

**(b) Do not compile them — restrict to a fixed set of primitives.** The
graph becomes a UGen DAG, wired rather than written, and no code generation
is needed. This is what SuperCollider does, and it is much less work.

**Take (a).** Option (b) reduces gestate to a wiring DSL and throws away the
one thing the experiment established: that a synth is a fold *you write*,
and that oscillator, envelope and filter come out as the same construct. If
the answer is a fixed UGen set, the language has stopped earning its place
in the design. The restriction that makes (a) tractable — flat state,
first-order, non-allocating — is checkable and is the same shape of
restriction this project already imposes twice.


Two clocks
-----------

`sync` means a graph can hold nodes on different clocks. In an engine that
is not an obstacle; it is **control rate versus audio rate**, which
SuperCollider spells `.kr` and `.ar` — arrived at here honestly rather than
by imitation.

**Stage 2 handles one clock and refuses two**, which is not a retreat from
this section but a consequence of it: "updates once per block" needs blocks,
and blocks arrive in stage 3. The other half of the reason is that the
oracle cannot drive a second clock either — see open question 3.

The rule for the engine: a **control-rate** node updates once per block, and
an audio-rate node reading it sees a value held constant across the block
(or linearly interpolated, which is a later refinement). A `zipSig` whose
two sides are on different clocks is precisely the `.kr → .ar` boundary, and
its `SyncLeft`/`SyncRight` cases are precisely "the control side did not
tick this sample; keep what it held".

The fragment must therefore admit **exactly two** clocks and reject a third,
and the extractor must partition the graph between them. A parameter driven
by the GUI — a slider, a knob, an edited constant — is a control-rate source
and is how the environment reaches into the running sound.


The plan
---------

Six stages. Each has a deliverable and, more importantly, **a way to be
wrong that is caught immediately**. No stage begins before the previous one
verifies.

### Stage 0 — the oracle (done)

`gestate/audio.py`'s `render()`, and the committed `blip.wav` and
`drums.wav`. **This never goes away.** Every later stage is verified against
it sample-for-sample.

The golden buffers are **done**: `examples/audio/blip.samples` and
`drums.samples`, one `float64` per line, checked by
`test/test_audio.py`. The committed `.wav` is the artifact you can listen
to and is 16-bit; a bit-identical comparison needs the doubles, so the two
files are not redundant.

Four decisions in it are worth knowing before stage 2 relies on them.

**The comparison is exact, and is allowed to be.** A gestate synth is
`+ - * /` on doubles and integer arithmetic, all correctly rounded, so a
render is reproducible bit for bit rather than closely. That is the same
fact open question 2 turns on, spent here first.

*(Transcendentals arrived later and the comparison stayed exact, for a
different reason: not that `sin` is correctly rounded — it is not — but
that both sides call the **same** `sin`. See open question 2.)*

**Each file carries the settings it was made at** — rate, duration, count,
in its own header — so the test re-renders at those and regenerating cannot
quietly move them. `python -m gestate.audio examples/audio/drums.ges
--golden` reads them back out of the file it is about to overwrite; only the
numbers can change.

**The windows are short and chosen, not arbitrary.** `blip` is 600 samples
at 2 kHz, which is longer than one note at `speed = 4` and therefore
contains a note change — the phase continuity the example exists to show.
`drums` is 800 at 1 kHz: five sixteenths at 96 bpm, so kick, hat and the
noise fold are all inside it. Both are asserted, because a golden
regenerated a little shorter would lose the coverage silently and still
pass.

**And it found the first concrete stage-4 hazard.** `lowpass k` is
`scan (y x => y + k * (x - y))`, so a gate that shuts leaves the state
multiplied by `1 - k` every sample: a geometric tail that approaches zero
without arriving. At `drums.ges`'s `lowpass 0.8` that reaches the subnormal
range after ~440 silent samples and exact zero after ~463 — and a silent
sixteenth at the default 22,050 Hz is 3,445 samples, so **the oracle emits
subnormals routinely**, on every gap in the pattern. See stage 4's risk.

### Stage 1 — the fragment, defined and checked (done)

**Deliverable.** `gestate/audiograph.py` (or an extension of
`subgrammar.py`) with a single entry point: given a compiled program, either
report that `sound` is in the fragment, or say precisely which definition
leaves it and why. The fragment itself is specified above, and that section
is normative.

**Done.** `gestate/audiograph.py`, with `check(source)` and
`check_analysis(analysis)`; `is_flat`/`why_not_flat` in `types.py`;
`pipeline.analyse()` for the tree it runs on; `test/test_audiofragment.py`.
Both examples are in the fragment, and eight programs that must be refused
are refused with a message naming the definition — a `List` in the state, a
function-typed step parameter, a third clock, unbounded recursion, a
polymorphic helper, a set in a step function, a signal built by hand, and a
list read per sample. A checker that accepts everything passes no test.

What it established, beyond the checker:

* **`drums.ges` was not in the fragment**, though this document said it
  would be. See "the transformation the fragment forces" above — that
  section is rewritten around what actually happened.
* **The flat types are a fifth subgrammar**, and reusing one of Datafun's
  four would have been wrong in both directions.
* **Polymorphism needs no rule of its own.** `elaborate` prepends one
  parameter per constraint, so "wider than its own type" is the test, and
  it cannot be fooled by a name.
* **The examples were rewritten and the sound did not change** — verified
  against the stage-0 goldens *and* the committed `.wav` files, byte for
  byte. That is the first time a later stage has been checked by an
  earlier one, which is the whole method of this plan working as intended.

**Risk, and what is left of it.** The fragment is drawn too tight and
rejects reasonable synths, or too loose and stage 2 cannot extract. Two
examples is not enough evidence either way — writing more synths is what
answers open question 1, and it has found something every single time in
this project. What is known already is that the fragment rejects the
*natural* spelling of a tune (a list) and admits the explicit one (a
table), which is a real cost and is recorded rather than hidden.

### Stage 2 — graph extraction (done)

**Deliverable.** A function from a compiled `Sig Float` to a flat,
serialisable structure: an ordered list of nodes, each with an id, a kind
(`source`, `map`, `scan`, `zip`), its inputs, its state layout (offsets and
types), and its step function as a small first-order expression tree. Plus
the constant tables the fragment forced out.

**Built**: `gestate/audioir.py` (the graph and its IR),
`gestate/audioextract.py` (the extractor), `gestate/audioengine.py` (the
reference interpreter), `test/test_audiograph.py`. `blip.ges` is five
nodes:

    0  source                                  : Int    [sound/raw/ticks/source#0]
    1  scan    <- 0  step stepVoice  init Voice 0.0 0  : Voice
    2  map     <- 1  step voiceOut             : Float
    3  scan    <- 2  step …/lowpass  init 0.0   : Float
    4  map     <- 3  step …/gain                : Float

`gain` and `lowpass` are not nodes; they *become* the last two, with their
arguments folded in as literals. The IR has eight forms — `Const`, `Var`,
`Prim`, `Call`, `Con`, `Field`, `Case`, `Let` — chosen so that stage 4 is a
transliteration rather than a compiler.

**How it is caught being wrong.** Interpret the extracted graph in Python —
naively, one sample at a time — and assert the output is **bit-identical**
to `render()` on the same program. This is the single most valuable test in
the whole plan, because it fixes the meaning of the graph before anything
depends on it.

**And it caught the thing it was built to catch, on the first run.** The
risk this stage names is "`scan`'s initial value is placed an instant off",
and the first engine was off — not in the initial value but in the input:

    out[t] = f(out[t-1], in[t])

`scan`'s own state comes from the previous instant and **its input comes
from this one**. The obvious reading, written first, was `in[t-1]`. The
reason the obvious reading is wrong is the property this project keeps
coming back to: `f z (head s)` sits inside `scan`'s `delay`, so it runs one
instant later, and by then `s` has been *overwritten in place* with its next
value. A signal is a cell and not a stream, so `head s` under a `delay`
reads the new sample. Bounded memory and the arithmetic turn out to be the
same fact.

Nothing but a sample-for-sample comparison would have found this. The sound
was plausible either way.

**`zipSig` on one clock survives extraction**, as a DAG: two oscillators
built from one `ticks` share the source node and keep their own `scan`s.
**Two clocks are refused**, and that is where open question 3 now stands —
see below.

**Risk.** The clock partition is wrong, or `scan`'s initial value is placed
an instant off. Both show as an exact mismatch, immediately, which is why
this stage is worth doing before any code generation.

### Stage 3 — block rendering, still in Python (done)

**Deliverable.** `render_block(graph, state, n)` filling a buffer of `n`
samples, with control-rate nodes updated once per block.

**Built**: `audioengine.render_block` and a `State` — the values a graph
carries between blocks, which is the shape stage 5 migrates and stage 4
emits as a struct.

**How it is caught being wrong.** Identical output to stage 2 for every
block size — 1, 2, 64, 1024 — and to `render()`. Block size must not be
audible; if it is, the control/audio partition is wrong.

That holds, for both examples, over the whole committed golden window, at
every block size including 1 and a size larger than the buffer, and across
an uneven sequence of blocks (5, 1, 17, 3, 64) driven the way a callback
drives one.

**The invariant needed one correction, and it is the interesting part.**
"Block size must not be audible" is right for an audio-rate graph and
exactly backwards for a control-rate one. A control-rate node is *defined*
as updating once per block, so changing the block size changes when it
updates, and the sound changes with it. Both facts are now asserted, so
neither can later be mistaken for the other: with no control node, every
block size agrees; with one, block 8 and block 16 differ. **Block size is
not an implementation detail once a parameter exists** — it is part of the
instrument, the way it is in every other audio system.

**Open question 3 is answered here**, as stage 2 predicted it would have to
be. The control clock is now real:

* **The clocks are partitioned by name.** `audio.ges` declares `clock` and
  it advances every sample; any *other* channel a program declares is
  control rate. By name, because ids are handed out in evaluation order and
  are not the order anything was written in.
* **The oracle learned to drive it.** `render(control_every=n)` advances
  every other channel once every `n` samples, feeding both channels in one
  arrival on a boundary so `sync` reports `SyncBoth`. Without this there
  was nothing offline for a two-clock graph to be identical *to*.
* **They agree — for the case that was tested, and that turned out to be
  the easy half.** A `zipSig` across the two clocks is bit-identical to the
  oracle at block sizes 4, 8 and 16. Writing a *third* example in stage 6
  showed that this holds only when nothing downstream of the control clock
  has state; see open question 3, which is **reopened**. What is claimed
  here is exactly what is tested and no more.
* The control value is **held**, not interpolated, and there is a test
  saying so, since the spec names interpolation as a later refinement and a
  refinement should be a decision rather than a drift.

**And it found a bug in the oracle** (`fixme.md` F91). `render()` chose the
audio clock as `min(reactive.chans)`; the first two-clock program written
had `clock` at id 1 and the new channel at id 0, so the renderer advanced
the user's channel every sample and never ticked the clock. Every sample
would have been the value the signal started at. No single-clock program
can reach it, which is why it sat there.

**Why this stage exists at all**: it is where the state layout stops being a
diagram and becomes a thing that has to work, and doing that in Python
rather than in C costs an afternoon instead of a week.

### Stage 4 — the engine (done)

**Deliverable.** Code generation from the graph to a state struct and a
`render_block` of straight-line arithmetic, no allocation, no branching
beyond what the step functions contain. Driven by a real callback
(PortAudio, JACK, or `sounddevice`).

### The target: LLVM IR, emitted as text

**Take LLVM, and emit textual `.ll` from pure Python.** C was the other
candidate and loses on the one criterion this plan is built around.

**Bit-identity is a floating-point argument, and C makes it harder.** A C
compiler may contract `a * b + c` into an `fma` — `-ffp-contract=fast` is
the *default* in GCC and in clang — which changes the result of exactly the
expressions a synth is made of. Getting bit-identity out of C therefore
depends on remembering a flag, on every compiler, forever. In LLVM IR the
question does not arise: `fmul` then `fadd` is two instructions and stays
two unless the emitter writes `llvm.fmuladd`. The same applies to the
subnormal hazard stage 0 found — `-ffast-math` implies flush-to-zero, and
there is no way to write `-ffast-math` by accident in an IR file. **What is
generated is what runs**, and `-O2` over IR without fast-math flags will not
reassociate float arithmetic.

**The hard parts of compiling a functional language are already gone.** The
fragment removed closures, allocation, laziness, polymorphism and recursion;
stage 2 reduced what is left to eight IR forms. The mapping is direct:

| gestate | LLVM |
|---|---|
| `Float` / `Int` / `Bool` | `double` / `i64` / `i1` |
| a flat constructor | a literal struct, tag first |
| `Case` | `switch` on the tag, one block per alternative |
| `Prim` | one instruction each |
| `Call` | `call` to a `fastcc` function |
| `Let` | an SSA name — no `alloca` needed |
| a node's state | one field of the state struct |
| `render_block` | a loop over `n`, nodes in id order |

**Two layers, so the dependency stays optional.** `gestate/audiollvm.py`
emits IR *text* and imports nothing — testable by reading the `.ll`, and
runnable through `clang` or `llc` where a toolchain exists. Running it in
process for the live case wants `llvmlite`'s MCJIT, and that is where stage
5 gets its millisecond recompile: build the new function, swap the pointer,
carry the state across. A backend needing a package it is the only user of
is the pattern `mido` and `pygame` already set, and the tests that *run*
generated code skip without it the way the MIDI tests skip without `mido`.

### Three decisions codegen has to make, and one is a hazard

**`Int` becomes `i64`, and that is a narrowing.** gestate's `Int` is a
Python integer — arbitrary precision — and the oracle computes with it. The
engine will not. Measured on the examples: `blip` never exceeds 22,050, and
**`drums` reaches 2,368,169,630,722,025,925 — 25.7% of `i64`'s range** — in
its LCG, `1103515245 * seed + 12345`. Comfortable, but a wider seed or a
larger multiplier overflows, and the failure is silent: Python keeps
counting and the engine wraps, so the noise diverges and only the
bit-identical comparison says so. Either state that the fragment's `Int` is
64-bit and mean it, or check the range. Do not discover it from a synth
that sounds subtly wrong.

**Division floors.** `prim_div_int` and `prim_mod_int` are Python's `//`
and `%`, which floor toward negative infinity; LLVM's `sdiv`/`srem`
truncate toward zero. They differ for negative operands, which a phase
wrapped with `mod` can easily produce. Emit the floor correction, and test
it at negative inputs specifically.

**No fast-math, no contraction, no FTZ** — the stage-0 finding, now a
codegen instruction rather than a warning.

**Built**: `gestate/audiollvm.py` — `emit(graph)` produces `.ll` text and
imports nothing; `build`/`run_native` shell out to `clang` where there is
one. `test/test_audiollvm.py` skips the building half without a toolchain,
the way the MIDI tests skip without `mido`.

**How it is caught being wrong.** The generated code, run offline over the
same number of samples, is bit-identical to stage 3. Only once that holds
does it go near a callback.

**It holds** — both examples, over the whole committed golden window, at
block sizes 1, 7 and 64, with a control clock, and at `-O0` as well as
`-O2`. The oracle, the graph interpreter, the block renderer and the
generated engine are the same numbers all the way down.

**And the gap is closed, which was the point of all of it.** The
interpreter renders ~1,400 samples a second against the 44,100 real time
needs. Measured on the same machine, the generated engine:

| | samples/sec | at 48 kHz |
|---|---|---|
| `blip.ges` | 28.4 M | 593× real time, 0.17% of one core |
| `drums.ges` | 17.2 M | 359× real time, 0.28% of one core |

Four orders of magnitude, from the same source text, with the language
never entering the callback.

### What code generation found

Both of these were **invisible at `-O2` and fatal at `-O0`**, which is the
argument for building both.

**A generated function collided with libm.** `audio.ges` defines `floor`,
which was emitted as `@floor`; at `-O0` LLVM lowers `llvm.floor.f64` to a
*call* to `floor`, and it bound to the generated one. `wrap` recursed half
a million frames and segfaulted. At `-O2` the intrinsic becomes an SSE
instruction and nothing happens at all. Every generated symbol is now
`gestate.`-prefixed; a synth may reasonably define `sin`, `abs` or `pow`.

**A primitive's name is not its type.** The G-machine shares one
instruction between `Int` and `Float` wherever Python's operator is already
right on both, so `helpers.py` and `elaborate.py` generate `prim_lt_int`
for a **`Float`** comparison *on purpose* — `drums.ges` arrives there
through `decay`'s `t > len`. A generator that trusted the name emits `icmp`
on `double`. The instruction is chosen from the operand type as emitted,
never from the name. (This one at least fails at the assembler; the point
is that the name was never the type it looked like.)

Of the three decisions named above, **the floor-division correction was
needed and is tested at negative operands specifically** — an example that
only ever divided positive numbers would pass without it. The `i64`
narrowing has not bitten and is not checked; that remains the open hazard.

### The callback — it can be heard

`gestate/audiolive.py`. **A synth written in gestate now plays.**

    python -m gestate.audiolive examples/audio/drums.ges --seconds 5

**Python is not in the audio path**, which is the architecture's one rule
made concrete. The driver makes exactly one call per block —
`render_block_f32`, a second entry point the code generator emits — and
that call fills the device's buffer *in the device's format*, clamping the
way `audio.write()` clamps. No arithmetic, no allocation, no per-sample
work in the interpreter. Putting the conversion in Python would have been
easier and would have put a garbage collector between the engine and a
deadline.

Two backends. **`sounddevice`** is a real PortAudio callback and is used
when installed; it is not installed on the machine this was written on, so
it is short and honestly untested. **A pipe to `pw-play`, `paplay` or
`aplay`** fed raw `float32` needs no third-party package at all, and is
what was actually heard — the pipe's back-pressure *is* the clock, so the
engine advances exactly in step with the sound and nothing has to sleep or
measure time. 3 seconds of audio costs 0.7 s of CPU including compilation.

**How it is caught being wrong**, given that a sound card cannot be
asserted on: a test puts `cat` where the player goes and compares **the
bytes that would reach the card** against the oracle's samples. Source
text → fragment → graph → IR → machine code → the pipe, checked in one
line. It found a real defect immediately — a `memoryview` of a ctypes
array is *typed*, so slicing it by bytes re-sent whatever the buffer still
held, putting a stutter at the end of every finite render.

**Compilation is 400 ms**, which is what stage 5 has to work with:

| | |
|---|---|
| gestate front end + extraction | 206 ms |
| emitting the IR (586 lines) | 2 ms |
| `clang -O2` | 190 ms |

That is one synth, once.  A *performance* is bigger and is read by more
than one reader: `examples/audio/quartet.ges` took 23.7 s to start, of
which 13 s was the same front end run again by the knob placement, the
`FromMIDI` loader and the assemblies underneath them.  Those answers are
now kept — `pipeline.analyse` and `audiovoices.expand`, keyed on the exact
text — which halves it, and the editor's own questions (`?`, `Tab`, the
sidebar) became instant rather than a front end each.  `fixme.md` F99 has
the measurements and what makes sharing an `Analysis` sound.

Fast enough to be interactive, slow enough that stage 5 should keep the
old engine sounding while the new one builds rather than pausing for it —
which is what crossfade-or-migrate was always going to require anyway.

**Risk.** Floating-point differences between Python and C. Expect them; use
`float64` throughout, or accept a tolerance and say so explicitly rather
than letting it drift silently.

**One of them is already known, and it is not a rounding difference.**
Stage 0 established that the oracle emits **subnormals** wherever a filter's
tail decays under silence — routinely, on every gap in `drums.ges`. An
audio engine typically sets FTZ/DAZ, or is built with `-ffast-math`, for the
good reason that subnormal arithmetic stalls badly on some hardware; either
one turns those samples into exact zero. The generated code would then
differ from the oracle **at samples nobody can hear**, and a bit-identical
comparison would fail on all of them.

Decide it deliberately rather than at the point the comparison fails. The
options are: build the offline comparison target with subnormals *on* and
flush only in the live callback, keeping the check exact and the two builds
different in one stated way; or compare with subnormals flushed on both
sides, which means the oracle must flush too and Python does not do that for
free. What is not acceptable is discovering it as an unexplained mismatch
and reaching for a tolerance, because a tolerance hides the mismatches that
do matter along with this one.

### Stage 5 — live update (done)

**Deliverable.** Recompile a changed source, extract a new graph, hand it to
the running engine.

    python -m gestate.audiolive examples/audio/blip.ges --watch

Edit the file in any editor, save, and the sound changes without stopping.
`audioengine.migrate` is the state carry, `audiolive.Live` is the running
instrument, `audiolive.SourceWatcher` notices the save;
`test/test_liveupdate.py` is the evidence.

Compilation is linear (`fixme.md` F78) and a synth is a small program, so
this is milliseconds — the loop is genuinely interactive.

Not quite: it is **400 ms**, and that is the number the design turns on.
Two things happen at very different rates and are kept apart:

* **Building** — the gestate front end, extraction, `clang -O2` — runs on
  a worker thread while the old engine keeps sounding. A rebuild never
  interrupts the audio, and a *failed* rebuild never interrupts it either:
  a typo mid-phrase is the ordinary case, not an exceptional one, so the
  error is reported and the instrument plays on.
* **Installing** — read the running state out, migrate it, write it into
  the new engine, swap the reference — takes microseconds and happens
  *between blocks*, on the thread that fills them.

**How it is caught being wrong.** Swapping to a graph extracted from the
*same text* must be **bit-identical to never having swapped**. That is the
whole of migration's correctness in one comparison: any state dropped or
misplaced shows up immediately instead of as a click someone notices later.
The mid-stream swap is checked the same way — two blocks of the original,
then the new engine carrying the old state, against a reference computed
independently through the Python engine.

**The design question here is state.** Two options, and the second is
harder but better:

* **Crossfade.** Instantiate the new graph fresh, run both for a few
  milliseconds, fade across. Simple, always safe, but every edit restarts
  envelopes and resets phases.
* **Migrate.** Nodes that are structurally unchanged keep their state; only
  new or altered nodes start fresh. This is what makes live coding feel like
  editing rather than restarting, and it needs stable node identity across
  compilations — which the extractor must be designed to provide from stage
  2, not retrofitted.

**Decided in stage 2**, as required, because it constrains how nodes are
named. **Migrate**, and the identity is a **path of the definitions a node
was inlined through**, plus which former and which occurrence:

    sound/raw/ticks/source#0
    sound/raw/scan#0
    sound/lowpass/scan#0
    sound/gain/map#0

Not a source position and not an index into the node list. A position moves
when a line is added above it; an index moves when a node is inserted
anywhere earlier. Either would reset state on an edit that changed nothing
about the node — and "the phase survived my edit" is the entire point.

What this buys, and it is tested:

* **Editing a step function moves nothing.** Rewrite `decay`, and every
  origin is what it was. This is the case live coding exists for: change
  the sound, keep the phase.
* **Editing a folded-in constant moves nothing.** Turning a knob is an edit
  to a literal inside a step function, not to the graph.
* **Inserting a node leaves the ones before it alone.** Adding a stage to
  the chain does not restart the oscillator feeding it.

What it does not buy, stated rather than hidden: **a second call to the
same definition on the same path renumbers the first.** Adding a `lowpass`
in front of a `lowpass` makes the original `#1`, so it starts fresh. The
alternative is to put the arguments in the identity — `lowpass(0.25)` —
and that is worse, because then *tuning* a filter would reset it, and
tuning is much the commoner edit. Losing a one-pole's memory is inaudible;
losing an oscillator's phase is not, so the residual risk is an inserted
duplicate upstream of a phase.

Migration also needs the state to still fit — and **the type's name is not
enough**, which is what building it found. Editing

    Voice := Voice Float Int   →   Voice := Voice Float Float

leaves the name `Voice` alone and changes what a value of it *is*. Carrying
the old slot across would reinterpret an integer as a double: silent, and
audible only as a wrong noise. A node keeps its state when its origin, its
kind and the **shape** of its type all match, where a shape is the
constructors and their field types resolved through — a name is what a
reader wants and a layout is what a state struct is.

Two more things the implementation settled:

* **A new node must be *written* with its initial state**, not left empty.
  `t` carries across the swap, so the engine's "first instant" branch never
  fires again, and a fresh `scan` starting from a zeroed slot rather than
  its `z` is a different instrument.
* **The watcher's baseline is taken before the first build, not after.**
  A build takes 400 ms, and a save inside that window was folded into the
  starting stamp and lost — save twice quickly and the second one vanished.
  Taking the stamp early can instead cost one redundant rebuild, which is
  the right way round: never miss an edit, occasionally repeat one.

### Stage 6 — the environment (built; its second half **withdrawn**)

**Deliverable, as originally written.** A GUI whose state includes the
source text and whose events include "the user edited this, *written in the
signal vocabulary that already exists*". Control-rate parameters are the
bridge: a slider is a control-rate source in the running graph.

**The italicised half is withdrawn.** The environment is a Python program
that hosts a gestate synth, and that is now the design rather than a
shortfall against it. The argument is in §"Why the editor is not written in
gestate" below; the short form is that the language cannot measure text, so
it cannot lay text out, and an editor written in it would spend its life
asking the host where the glyphs went.

Nothing about this stage needs a faster evaluator. It runs at 1,300 fps of
headroom today.

**Built**: `gestate/audioeditor.py`.

    python -m gestate.audioeditor examples/audio/knob.ges

A window with the synth in it, playing. Edit, Ctrl-S, and the sound changes
without stopping; a broken edit is reported in the status line and the
instrument plays on. The slider drives the control-rate parameter, so
`examples/audio/knob.ges` is a tone you can bend with the mouse while
rewriting the code underneath it — which is what this whole document was
for.

**Two halves, and the split is the point.** `Workbench` owns the playing
instrument, the rebuild worker and the knob, imports no toolkit, and is
what the tests drive. `Editor` is a `tkinter` view: a text widget, a
line-number gutter, a status line, a slider. Everything that can go quietly
wrong lives in the tested half.

### What the environment does now

    python -m gestate.audioeditor examples/audio/twoknobs.ges --midi

A window with the source in it, playing, and **a knob beside every line
that declares one** — placed by `audiospans`, not listed in a panel, which
is what the placement was built for and what several control channels made
worth having.

    Ctrl-S       save and apply
    Ctrl-Return  audition — apply *without* writing the file
    right-click  MIDI learn on that knob; again to cancel

**Audition is not a convenience.** Trying a filter coefficient you may not
keep is the ordinary act in live coding, and an environment whose only verb
is "save and apply" makes every experiment a commitment. The status line
says which of the two happened, because the failure mode of having both is
not knowing which one you did.

**MIDI learn, because nobody knows their CC numbers.** Right-click a knob,
move the control you mean, and they are bound; the same gesture cancels,
which is the only part anyone has to remember. A controller already bound
elsewhere is *taken*, not shared — one physical knob driving two parameters
is never meant and is hard to notice afterwards. Bindings follow a
parameter's **name** across a rebuild, since an edit renumbers nodes and a
binding held by id would follow whatever node inherited the number.

The knob column uses `dlineinfo` — the same call the line-number gutter
uses — and places nothing *into* the document: a widget embedded with
`window_create` would become part of the text, so editing would move it and
undo would delete it. A parameter whose declaration is scrolled off screen
is hidden rather than parked at the edge; a knob that stays put while its
definition leaves has stopped meaning anything.

**It is a scaffold, and what it is a scaffold *for* changed.** It was
written as a placeholder for an editor whose document is a `Sig` and whose
keystrokes are gestate values, driven by `gui.py` like any other GUI
program. That editor is no longer wanted; see below. What the split still
buys is the same thing it always did — `Editor` is replaceable without
touching anything that can go quietly wrong.


### Why the editor is not written in gestate

The goal was dogfooding: prove the language expresses its own tool. It is
withdrawn, and recorded here rather than deleted because the reasoning is
what a future proposal has to answer.

**1. The language cannot measure text.** `gui.ges` supplies `Rect` and
`Dot`, and says why it supplies no more — *"the point is to see the
reactive half working, not to be a drawing library."* `gui.py` has no font
and no text at all. A `Text` shape would be an afternoon; glyph metrics are
not. An editor needs to know where the caret sits, which character a click
landed on, and where a line wraps, and every one of those is a question
about a font the language has no access to. An editor written in gestate
would be a `Sig Scene` that asks the host for every position it draws —
which is not the language expressing the tool, it is the language
subcontracting it.

**2. The rope is already the right thing in the right language.**
`gestate/balanced.py` is a Python AVL rope with `insert`, `erase`, and
`row`/`rowpos` for line ↔ offset — exactly an editor's document interface.
Rebuilding it in gestate would rebuild it on `String = List Char`, which is
a worse substrate for the same structure. Nothing is gained by moving it.

**3. The features actually wanted pull the other way.** A knob rendered
beside the line that introduces it needs a map from a control-rate node
back to a source span — compiler information, held on the Python side, and
deliberately *not* on the node: `audioir.Node.origin` is a path of
definitions rather than a position, because stable identity across edits is
what state migration needs (stage 5). An editor in gestate would put a
language boundary between itself and precisely the information such a
feature is made of.

**4. The dogfooding evidence was already collected, and from a better
source.** `blip.ges` establishes that an oscillator, an envelope and a
filter are one construct. An editor would establish that `scan` folds
keystrokes into a buffer, which is true and was never in question — while
exercising the parts of the language that deliberately do not exist and
none of the parts that make it interesting.

**What is not being said.** This is not "gestate should not describe user
interfaces". It is that *this particular interface, specified in advance,
in a vocabulary chosen before anything was built*, is the wrong way to find
out what such a vocabulary should be. `Rect`-and-`Dot` was enough to prove
the reactive half; what comes after it should be grown from programs that
want it, the way `signal.ges` was extracted at the third combinator rather
than designed at the first. Withdrawing the goal is what leaves room for
that.


### Placing a node in the file it was written in

`gestate/audiospans.py`, and the one piece of an environment that was worth
building ahead of the environment: a knob is only useful beside the line
that declares it, and nothing joined a graph node to a source position.

    python -m gestate.audiospans examples/audio/knob.ges --source

The join is not a lookup, for two reasons. `Node.origin` is a *path* of
definitions and mostly names code the author did not write — a node
resolves to the innermost component that can be placed at all, which is
`knob` for the control source and `sound` for a `lowpass` the author only
called. And a running synth is **four files**, combined two different ways:
`signal.ges` and `audio.ges` are prepended as text, so their spans are in
assembled coordinates and a line range identifies them exactly, while
`prelude.ges` is merged as a *module* and its spans start again at 1. Names
decide that one, because arithmetic cannot.

Every `Site` therefore names its file, and carries a path for the ones a
person could open. That is deliberate rather than incidental: `lowpass` is
as editable as `sound` is, and an environment that could only place the
author's own definitions would be unable to show what half a synth is made
of.

**Two things it turned up.**

* **`Node.clock` is not inherited** (`fixme.md` F93). The field said it
  was; the extractor sets it on a source and never again, and both the
  engine and the code generator consult it only inside their
  `kind == "source"` branch. Believing the docstring means offering a knob
  for a `map` over a knob — a node the host has no way to supply.
* **A synth had at most one control-rate source.** That is **fixed** — see
  §"Several control channels" below. It was a conflation of two *rates*
  with two *channels*, and it was costing an environment its knobs.

**And it found the thing stage 3 had got away with.** Writing a third
example to have something for the slider to turn is what exposed the
control-clock disagreement in open question 3 — the third example finding
what the first two could not, for the fourth time in this project
(`fixme.md` F89).


What must not change
---------------------

* **The offline renderer**, as the oracle. It is the only thing that makes
  the later stages checkable.
* **Guarded recursion and in-place signals.** Productivity and bounded
  memory are the properties that make a signal safe to run in an audio
  callback at all. If a future convenience weakens either, the engine loses
  its guarantee and gains a class of bug that is very hard to hear and
  impossible to reproduce.
* **`scan` as the way state is written.** Everything in this document rests
  on a synth being a fold the programmer writes.


Non-goals
----------

* **A faster interpreter for audio's sake.** Measured, argued above, and
  settled. Interpreter work should be justified on its own terms if at all.
* **Changing the host language.** The gap is not the host's fault, and
  after stage 4 the evaluator is not in the audio path at all.
* **Using scsynth.** It is a real option — a standalone server with an OSC
  protocol and a documented SynthDef format, requiring no sclang — but it
  pins the sound to SC's UGen set and adds a dependency. Reach for it only
  if that UGen library is specifically what is wanted.
* **Polyphony as a language feature, for now.** Several voices in one graph
  is a graph the extractor already handles; *dynamic* voice allocation is a
  second system and should wait until one voice runs.


### Several control channels

**Two rates is the ceiling; two channels never was.** The fragment used to
reject a third *clock*, which conflated them: N control channels all tick
at the same rate, at the same block boundary, and a synth with three knobs
needs no third rate. What the check should have been asking is narrower and
is now where it belongs — in the extractor, and about the *value*: a control
value occupies **one slot** of the buffer the host fills, so a channel
carrying a constructor with fields is refused. It used to extract and then
die inside the engine as `case on a non-constructor`.

**Separate channels rather than one record, and the reason is live coding.**
A record makes the knobs one value of one type; adding a third changes that
type, and stage 5 migrates by *shape*, so declaring a new parameter would
snap the two you were already turning back to their initial values. Separate
channels are separate nodes with separate origins: add one and the others
keep both their value and the phase downstream of them. It is also what
gives an environment one `Site` per knob, at the line that declares it.

The ABI moved with it: `render_block`'s fourth argument is a **pointer** to
one 8-byte slot per control source, in `Graph.control_sources()` order,
rather than a single `i64`. `examples/audio/twoknobs.ges` is the example,
bit-identical across oracle, block renderer and generated code at `-O0` and
`-O2`, with each knob checked to move only its own parameter.

One thing it turned up, unrelated and older: a former nested *directly*
inside another former lost its element type, because only a named signal
definition ever computed one (`fixme.md` F94). A step function's type says
what its signal's elements are, which is where the answer already was.

### MIDI, and why controllers but not notes

`gestate/audiomidi.py` binds a synth's control channels to CC numbers, in
declaration order, and a reader thread writes the latest value per
controller into a dict that the block callback reads. Nothing MIDI is in
the audio path.

**A controller sends a value, and a value survives coalescing.** The engine
samples control sources once per block and holds them, so a knob that moved
fifty times inside one block is heard where it ended up — nothing is lost
that anyone could hear. That is what makes "never faster than the control
clock" a discipline rather than a compromise: the device's own rate never
reaches the graph, and no third clock is needed.

**A note is not a value, and coalescing drops it.** Two note-ons in a block
become one; a note-on with its note-off in the same block cancels to
silence. That reasoning stood, and the conclusion drawn from it — that
notes need a per-block event *list* with sample offsets, and therefore
allocation the fragment forbids — **was wrong**, in a way worth recording.

**Notes do not have to be coalesced, because they can be turned into
values.** A note becomes `gateAt`, `offAt` and `pitch` on control channels,
and `gateAt` *names the sample the note begins at* rather than saying "on
now". The voice compares it against its own `ticks`, per sample, in its own
step function — so a note delivered at a block boundary still begins
partway through the block. No event list, no allocation, no change to the
fragment. See §"Notes, without an event list" below.

An untouched controller reads the **source's own declared initial value**,
not zero. `cutoff = 70 ::: mkSig (wait c)` is the synth saying what it
sounds like before anything is plugged in, and a host answering 0 at the
first block boundary would override it silently.

### Notes, without an event list

Four pieces, and only the first is new syntax.

**`voices lead 8 plucked : Sig Float`** (`audiovoices.py`) — a bank of N
copies of one voice, expanded to ordinary declarations *before* `classify`.
The declaration names the **voice** and the type the bank's own name gets,
which is where a frame type belongs: `: Sig Stereo` is a bank of stereo
voices, and the expander generates a componentwise adder for it because
`addSig` is `Sig Float` only. The payload is *not* written here — it is
read off the voice's signature, `plucked : Sig Gate -> Sig Note -> Sig Float`,
so a bank's notes are described once and in the definition that reads them.
It may be a record or a bare `Int`/`Float`, since every field is one
control value and a note number is one. An earlier spelling —
`voices lead 8 : Note -> Sig Float` with a separate `lead = plucked`
equation — is still accepted and should not be written: it looks like a
supercombinator while being neither, and its "equation" admits only a bare
name (`spec/frp_lesson.md`). Polyphony is
the one thing the static fragment cannot express, because allocating a
voice when a note arrives is exactly the dynamic graph it forbids; a
*fixed* bank is not. The program declares the size, each bank declares its
own record, `N = 1` is a monophonic bank, and the bank's name is bound to
the **sum**, so shaping it further is ordinary signal code. Nothing with a
bit-identity obligation changes.

**`Schedule`** (`audioschedule.py`) — control changes over time, keyed by
channel name, which is what makes a note *checkable*: the same schedule
drives `render()` and the engine, so a performance is compared sample for
sample like everything else here. `Node.chan` was added for it — the
interpreter drives channels and the engine drives nodes, and there was no
name both could resolve.

**`Allocator`** (`audioalloc.py`) — which note goes to which voice. Host
policy, outside the language, and it emits `(channel, value)` changes
rather than sound. That is what lets one allocator serve both callers: live
MIDI applies them now, a `Score` writes them into a `Schedule`. Oldest-voice
stealing by default, and the policy is a function the caller may replace.

**`Score`** (`audioscore.py`) — `midi.perform` gives `(onset, offset,
program, key, velocity)` in ticks; this converts to samples, maps a program
number to a bank, and runs the allocator in time order. **A piece written in
gestate is performed by an instrument written in gestate**, and the
interpreter, the block renderer and the generated code agree about the
result.

**`gateAt` is 1-based**, and that is load-bearing rather than a detail: zero
means *no note*, so a bank whose channels have never been written reads as
"nothing has played" instead of "every voice started at sample 0". Eight
silent voices at start-up fall out of the channels' own defaults rather than
from anything a host must remember to send.

**What this found, and it was silent.** A voice's parameters arrive on
*control* channels, so a record built from those alone updates once per
block — and a `scan` inside the voice would advance its oscillator once per
block too. The synth still plays; it plays at a small fraction of the right
frequency, with nothing reported anywhere. The expander zips `ticks` into
the record, which makes it audio-rate while the control values stay held.
It surfaced only because a channel came out missing: with nothing reading
`ticks`, `clock` was never allocated and `_channels` promoted a *note*
channel to the audio clock.

### Both at once

`examples/audio/duet.ges` declares two banks; `examples/music/duetline.ges`
is an ordinary music program that knows nothing about any of this.

    python -m gestate.audioperform examples/audio/duet.ges \
        examples/music/duetline.ges --midi

`audioscore` drives one bank from the layout, `audiomidi.Notes` drives the
other from a keyboard, and `audioperform.Performance` merges them — which is
a dictionary lookup rather than a design, because the two banks touch
**disjoint channels** and the engine cannot tell which of its values came
from which. That is the example's whole claim: a note is the same thing
whether a composer decided it in advance or a player decided it just now.

The scored half stays checkable. It is a `Schedule`, so it renders
identically through the interpreter, the block renderer and the generated
code even though the other half is improvised.

### A piece in the program's own payload

`music.ges` has always had `Play Rendered`: a note committed to a MIDI
program, carrying (program, key, velocity) and nothing else. **`Assigned
Voice` is its twin** — a note committed to a `voices` bank, carrying the
author's own payload.

    Custom := Custom Float Int

    voices lead 3 myVoice : Sig Float

    myVoice : Sig Gate -> Sig Custom -> Sig Float

    tune  : [: Custom :]
    score : [: Void :]
    score = tune >>= voices.lead

**`Score` needs no second type parameter**, which was the first design and
was wrong. `Assigned` is parametric in `a` exactly as `Play` is — it carries
no payload of type `a` — so a bound score still unifies with `Void` and
`[: Void :]` goes on proving every note was assigned, while the payload the
*bank* receives is the program's own type. `Voice` is the opaque existential
that makes it work: a generated sum, one constructor per declared bank, each
carrying that bank's record.

**And the guarantee is stronger than the one it preserves.** `[: Void :]`
proved that a note got *an* instrument. A payload type ties a note to a bank
that takes it, so sending a `Pitched` to a bank declared for `Custom` is a
type error rather than a note that plays wrong.

`Rendered` and `Voice` are the same construct at different ages: a sum over
the targets a backend offers. They are kept **side by side** rather than
merged, because merging would make `Rendered` — and therefore this file's
own subject — partly generated, and two is not yet a pattern.

**Timing is not payload, and they arrive apart.** A bank hands each voice
**two signals**: `Sig Gate` — `Gate := Gate Int Int` in `audio.ges`, the
`gateAt` and `offAt` of the note — and `Sig <payload>`, the author's own
record or a bare `Int`/`Float`. The timing comes from the layout that
placed the note or the moment a key went down, and asking an author to
carry it inside their own record was asking them to model MIDI rather than
their instrument.

They were one record, `Played a := Played Int Int a`, until
`spec/frp_lesson.md`: a pitch wants the payload, an envelope wants the
timing, and almost nothing wants both, so every voice began by opening a
record to find its half. The bank had them apart already — `gateAt` and
`offAt` are channels of their own — and the bundling was work it did on the
way out. A voice that genuinely folds over both pairs them itself, with
`!Both g s`.

**Opening a `Voice` is a tag lookup**, and nothing in gestate ever does it:
the constructor's position is the bank and its arguments are the payload,
exactly as `midi.py` reads `Midi`/`Perc`. That is what lets the type be
opaque.

Two consequences worth stating. A synth that assigns nothing gets neither
`Voice` nor `music.ges`, because nine constructors and their compile time
are not something a program that plays no score should pay. And a synth and
the piece it plays are **one program**: `voices.lead` names a bank
lexically, and only then can the type checker say whether the piece fits the
instrument.

### `FromMIDI` — a key becomes a payload, or does not

    class FromMIDI a where
        noteOn : Int -> Int -> Int -> Maybe a      -- channel, pitch, velocity

**Three things doing three jobs.** The *instance* says a payload can come
from MIDI and how; `Nothing` lets it **decline** a particular note, so a
bank that wants one channel or half a keyboard says so in ordinary gestate
rather than in a routing table beside the program; and a *switch per bank*
says which banks listen. All three are needed, and the third is not a
convenience: `duet.ges`'s `lead` and `bass` both carry `Pitched`, so they
share one instance and **nothing in the type can tell them apart**.

Every listening bank that accepts gets the note. Layering a piano under
strings is one key on two instruments, and declining is what `Nothing` is
for.

**The host runs the instance**, which means an interpreter beside the
native engine — the engine is machine code and knows nothing about
instances. It costs ~0.6 s of a rebuild (1.84 → 2.40 s on `duet.ges`) and
**nothing at all** for a program declaring no instance, which is skipped
before compiling. At play time it is a G-machine run per key press, cached,
off the audio thread.

Three things this found, each invisible in a different way:

* **The method is never compiled.** Only reachable definitions are, and
  nothing in a synth calls `noteOn` — the caller is a keyboard. The
  expander emits a `<bank>FromMidi` forwarder as a root, and only when the
  program declares the instance: emitting it regardless would turn a
  *missing* instance, which should grey a switch out, into a type error
  that stops the synth compiling.
* **A switch needs something behind it.** A bank the score drives was left
  out of the allocators entirely, so ticking it set a flag on a bank that
  was not there. Every bank gets an allocator; a scored one starts
  *switched off*, which is a default you can change.
* **Two writers, and the switch picks.** The score used to win always, so a
  note played on a scored bank was taken by the allocator, shown in its
  row, and never heard. Ticking hands the bank to the keyboard and the
  score stops driving it; unticking hands it back and releases whatever was
  held, because those channels stop answering and a note left down could
  never be released.

Open questions
---------------

1. **How much does the fragment reject?** Only writing more synths answers
   it. Every time in this project a real program was written against a new
   part of the language, it found something.

   **Five synths in now**, and the fourth and fifth rejected nothing. Both
   `fm.ges` and `pluck.ges` extract to five nodes and are bit-identical
   through the block renderer and generated code at both optimisation
   levels, first time. That is the honest result and it is worth as much as
   a finding would have been: the fragment was drawn in stage 1 against two
   examples, and two more written *for a different purpose* — to be the
   caller for transcendentals — fit inside it without adjustment.

   `pluck.ges` also settles the half-claim this document made elsewhere:
   **several oscillators in one graph is a graph the extractor already
   handles.** It says so under Non-goals, to argue that dynamic voice
   allocation should wait; nothing had tested it until three phase
   accumulators in one `scan` did.

   The one thing that did bite is not the fragment and not a defect: a
   continuation line inside a `case` alternative may not begin with a bare
   identifier, so a constructor application broken across lines with a
   trailing plain argument is rejected. `syntax.md` §"Continuation lines"
   states exactly that rule and the implementation matches it, so this is a
   documented limitation meeting a real program rather than a disagreement.
   Naming a helper is the fix at the call site, and it read better.

2. **Where do transcendentals come from?** — **answered: from libm, on both
   sides, and the comparison stays exact.**

   `sin`, `cos`, `exp`, `log` and `sqrt` are `Float -> Float` primitives.
   The interpreter calls Python's `math`, which calls libm; generated code
   calls `llvm.<fn>.f64`, which lowers to a call to libm; LLVM's constant
   folder evaluates them with the host libm too. Same function, same
   machine, same bits.

   **The question was never accuracy.** These are not correctly-rounded
   functions — two libraries may differ in the last bits and both be right —
   so no amount of care about *precision* would have made the comparison
   exact. Only being the same implementation does. That reframing is the
   whole answer, and it is why "add them as primitives is easy" was the
   right instinct for the wrong reason.

   Measured rather than assumed: `test/test_transcendental.py` puts each
   function through the real pipeline over a 400-point ramp and compares to
   Python bit for bit, at `-O0` and `-O2`, and separately checks the
   **constant-folded** case — which a runtime comparison cannot see, and
   which is a shape the extractor really produces, since a synth folds
   constants into its nodes. It also asserts the fold happened, so the test
   cannot pass vacuously.

   **What this is an assumption about.** The platform, not the language: a
   build machine whose libm differs from the run machine's would break it,
   and so would a `-ffast-math` build, which is already forbidden and
   checked. The committed golden buffers are the detector — which is why
   both new synths have one. `sqrt` is the exception and is safe anywhere,
   IEEE 754 requiring it to be correctly rounded.

   **`tan` and `pow` are written in gestate**, not added as a sixth and
   seventh primitive: an identity in the language is the same expression on
   both sides, so it is bit-identical by construction rather than by libm
   agreeing about one more function. It also costs nothing that
   `llvm.tan.f64` needs LLVM 19.
3. **Does `zipSig` across two clocks survive extraction?** — **answered:
   yes, and it took a change to the FRP driver to make the question
   well-posed.** One clock was always settled: `zipSig` extracts as a `zip`
   node, two oscillators over one `ticks` share the source node,
   bit-identical. Two clocks are settled now, and stage 6's
   `examples/audio/knob.ges` is what showed they were not — the third
   example finding something the first two could not, again (`fixme.md`
   F89).

   **The fix, built.** An instant is a *set* of arrivals rather than one:
   `reactive.py` threads `Arrivals = {channel id: value}` through `ticked`,
   `advance`, `updateOne` and `reactiveStep`, and `react_instant` runs a
   block boundary as **one** instant on both clocks. `spec/frp.md`
   §"Several arrivals in one instant" states the extension and why it is
   conservative: every rule asked exactly two questions of κ, and both have
   per-channel answers. `react` is unchanged — one arrival, one instant,
   which is the paper's rule and what every FRP test exercises.

   **`sync` reports `SyncBoth` from the driver now**, which it could not
   before: `packBoth` was reachable only when both sides watched the same
   channel. Two clocks ticking together is the ordinary way to reach it,
   and it is what a `.kr → .ar` boundary *is*.

   **What it buys.** The interpreter and the engine compute the same sound,
   so `knob.ges` has a golden buffer like the other two — 600 samples at
   2 kHz with `control_every: 64` in its header, since a control-rate
   buffer is only defined against the block schedule it was rendered at.
   The whole chain is bit-identical on it: oracle, graph, block renderer at
   its own block size, and generated LLVM through `clang`. The oracle is
   the oracle for *every* program again, not only for audio-rate ones.

   `test_audiograph.py` keeps the number that found it: a `scan` under the
   control clock accumulates **8** per boundary in both, where the
   interpreter used to add 48 — the arriving 8 on top of the held 40, in a
   single instant.

   The one thing this does not do is interpolate. A control value is held
   across the block, as this document's "Two clocks" says, and linear
   interpolation remains the later refinement it was always described as.

   The original question:

   Two clocks are *not* settled, and stage 6's `examples/audio/knob.ges` is
   what showed it — the third example finding something the first two could
   not, again (`fixme.md` F89).

   **The interpreter and the engine do not mean the same thing by a control
   tick.** `react(reactive, inputs)` runs a full instant *per input*, so
   feeding two channels is two instants: `sync` never reports `SyncBoth`
   from the driver at all, and every signal downstream of the control clock
   takes an **extra step that produces no sample**. The engine instead
   *holds* a control value across the block, with no extra instant
   anywhere.

   For a graph of maps and zips the two agree, because the extra instant
   leaves no state behind — which is exactly why stage 3's test passed and
   why the claim there had to be narrowed. Put a `scan` under the control
   clock and the interpreter accumulates twice at every boundary: with a
   knob at 40 and a new value of 8 arriving, it adds 48 in one sample.
   `test_audiograph.py` pins that number so it cannot quietly change.

   **Which is right?** The engine's, for an audio engine: a parameter is
   sampled once per block and held, and turning a knob should not advance
   an oscillator's phase by an extra sample. But it is the *interpreter*
   that is the oracle, so the honest position is that the language cannot
   currently express what the engine does.

   **The fix** is to let the driver take several arrivals as **one**
   instant — which is what `sync`'s `SyncBoth` is for, and which is
   currently only reachable when two signals share a channel. The change is
   contained: `ticked` compares `chan_node.chan_id == k`, and `k` would
   become a set with the arrived value looked up per channel. It touches
   `ticked`, `advance`, `_update_one`, `reactive_step` and `react`, which
   is the FRP core, so it wants its own stage and its own verification
   against `frp.md` §4.3's clock discipline — not a patch at the end of an
   audio one.

   Until then: `knob.ges` deliberately has **no golden buffer**, because a
   golden would freeze one of the two answers; the engine's semantics is
   what plays, and the interpreter remains the oracle for audio-rate
   programs, which is every program that does not declare a second channel.
4. **Stable node identity across recompiles** — **answered in stage 2**: an
   origin path, `sound/lowpass/scan#0`. See stage 5 for what it buys and
   the one case it does not.
