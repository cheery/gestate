# roadmap.md — what is left, and the order to do it in

Companion to `fixme.md` (implementation vs. spec) and `spec/errata.md`
(spec vs. papers).  Those two say *what* is wrong; this says *when* to fix
it and *why then*.  What already happened is `journal.md`, and keeping the
two apart is the point: **this file is future tense.**

Stages 0–6 are the language, and they are done.  Stages 7–10 are the live
audio environment, argued in full in `spec/liveaudio.md`: a synth compiles
to machine code, a piece written in gestate is played by instruments
written in gestate, and both can be edited while they sound.  What
followed them — the dynamic score, the CLAP export, and the G-machine's
Rust port (`crust`) — is recorded in `journal.md`; §"What is left after
stage 10" keeps only the part of it that is still undone.

**The most recent work is ariadne**, and §"Ariadne — what is left of it"
is where to start.  It is the redesign of the score's reactive surface
(`spec/ariadne.md`): chance and listening as lawful zero-width leaves of
the score monad rather than boxed constructs beside it, bound with the
`do` sugar (`spec/monad.md`).  Its first three stages are built, the old
surface is retired, and `shape`/`fermata`/`tempoShape` landed with it
(`spec/shape.md`).  **What is left is paths** — a position named by the
binds above it rather than by a beat — and that section argues it.

The substrate is built and no longer future tense: `spec/substrate.md` is
the design and `journal.md` has what it cost.  A canvas behind the editor
in the same window, written in gestate, composed the way a synth is — **a
substrate is a value, `substrate : Sig Sub`, built from smaller ones by
ordinary functions** — interpreted at frame rate, worth a control value to
the compiled synth the way a knob is.  `spec/frp_lesson.md` is the reading
that got the language ready for it: Fran set beside this one, and the four
compiler gaps that were between them.

If you are picking the project up, read `doc/manual.md` first, then
`spec/liveaudio.md`; the rest of this file is the record of how the language
got to the point where that became the next thing to build.

## Milestone — the language is closed under its own specs

Reached.  What it means, precisely:

- **Both papers run.**  Rizzo's `map`/`switch`/`filter` read as the paper
  writes them; Datafun's transitive closure converges — and now reads as
  Datalog rather than as a helper supercombinator:

  ```
  closure (Box e) = fix r => e \/ {(x, w) | (x, y) in r, (z, w) in e, y == z}
  ```

- **Every specification *decision* is made.**  Stage 1 asked three
  questions.  `Bool` vs `{1}` is answered — both, with `Prop` (D5).  The
  change-structure interface is stated, in `data.md` §I.8, from Definitions
  14–16 with the Cai et al. citation (D8).  The
  monomorphization question is settled in substance (D9): a monomorphic
  Datafun sublanguage, which is what is built.
- **Every stage-0 correctness gap is closed**, and **stage 2 is complete**:
  comprehension guards, `fix` at a product of semilattices, and sets of
  user data types.
- **Stage 4 is closed without being built** — see the rule below.
- **Score has a semantics.**  `music.md` says what a `[: A :]` is and types
  every operator; what it lacks is bodies.

Of the 74 `fixme.md` entries **at the time**, 64 were resolved; of the 28
`errata.md` entries, 26 are resolved, answered or implemented.  693 tests.
(Today, after the three backends below and stage 8: **94 entries, 84
resolved**, and **1,201 tests**.)

The defect that stood outside this milestone is **fixed**: F64, the
monomorphization boundary, is now enforced by a link-time check —
a polymorphic Datafun signature is a compile error naming the
supercombinator and the type, rather than a G-machine `unknown global`.

Turning that check on is what makes it worth recording: **it found a live
crash nothing had exercised.**  The prelude's `Guard Bool` has
`False -> {}`, a ⊥ at a set type that reached codegen unsettled, so a
comprehension guard that was *false under a `fix`* died on
`bottom_Set_a1` — every guard test passed because none of them had taken
that branch under a fixpoint.  That is F58, fixed with it: instance method
bodies now get the same final annotation pass every other body gets.

## The rule

> **Do not build what nothing needs.**

Stated in full in `journal.md` Part I.  A feature earns its place by
having a caller — a program someone wants to write, an unmet spec
obligation, or a defect it fixes.  "It is in the spec" is not a caller.

It closes stage 4 entirely, and it is why several `fixme.md` entries are
marked missing rather than scheduled.  It never argues against fixing what
is *wrong*: a defect is always a caller, which is why F64 above was fixed
rather than closed under it.

## What is left

Music, confidence and spec hygiene are all done.  `doc/manual.md` is the
front door for anyone picking the project up — how to start, and how to
*think about* the type system, Datafun and FRP rather than only what they
do.  Every snippet in it was run before it was written, and
`test/test_manual.py` keeps them running; §9 "Things that will surprise
you" is tested to fail when a limitation is *fixed*, so the manual is
updated rather than quietly wrong.

What remains is in `fixme.md`'s open table: four items closed under the
rule, three records of fact, and three unforced — defaulting (F32), the
subgrammar's remaining half (F38), and F29's golden ASTs.

This file opened by saying the instinct "there is not much left" was right
about the core language and wrong about three things: remaining correctness
gaps, unresolved specification *decisions*, and the stated purpose being
unimplemented.  All three are now closed — stage 0 fixed the gaps, stage 1
made the decisions, and stage 3 built the purpose.

**What is left is not in the language.**  It is stage 7: making a described
signal *run in real time*, which is a compilation-target problem and the
first thing this project has faced that the evaluator cannot be argued into
doing.

## Second milestone — the language is played

Since the milestone above, gestate grew three backends on one plan: the
language describes, a host renderer performs.

| | music | GUI | audio |
|---|---|---|---|
| prelude | `music.ges` | `gui.ges` | `audio.ges` |
| supplies | `score`, `bpm` | `substrate : Sig Sub` | `sound : Sig Float` |
| pure core | `perform` | `scenes` | `render` |
| writes | `.mid` (mido) | a window (pygame) | `.wav` (stdlib `wave`) |

Each was written twice — `fixme.md` F89, *one example each is not enough to
know a backend works* — and the second example found something every time.
The shared signal vocabulary was extracted to `gestate/signal.ges` at the
third combinator (F90), with `zipSig`, `addSig` and `gain`.

**The audio backend is the one that changed the plan**, and it did it by
answering a question rather than by working.  `examples/audio/blip.ges`
establishes that an oscillator, an envelope, a filter and a noise source are
all `scan` — one construct, a fold over time, written by the programmer and
not wired from a fixed set.  That is the strongest evidence the language has
produced that it says what it claims to say.

And it measured the gap: ~1,400 samples/sec against the 44,100 real time
needs, with the GUI at 1,300 fps of *headroom* in the same vocabulary.  A
faster interpreter does not close that — graph reduction allocates a node
per reduction and audio wants flat buffers — so the split is
SuperCollider's, arrived at from the other direction: **the language never
enters the audio callback.**  `spec/liveaudio.md` is that argument in full,
with the numbers.

Both facts point the same way, which is why the next stage exists.

## The ordering principle

Correctness before expressiveness; decisions before the work they gate;
purpose before polish.  Concretely: fix what silently lies (stage 0), then
settle the spec questions that block Datafun's surface (stage 1), then the
surface itself (stage 2), then music (stage 3).  Everything after that is
optional and can be reordered freely — **except stage 7**, which is neither:
it is ordered by verification, each stage checked against the one before,
and it is the only remaining work with a stated purpose behind it.

To which the rule adds the question asked *before* any of that ordering
applies: does this have a caller at all?  Most of stage 4 did not, and the
ordering never had to be consulted.

---

## Stages 0–10 — closed out, and moved to `journal.md`

The reasoning for each is in `journal.md` Part III, under the same heading
and the same number.  **Two are not clean closes and are marked so below**:
1.2 is partly done and 1.3 was settled in substance rather than written up
(`errata.md` D9 — a monomorphic Datafun sublanguage, which is what is
built).  Rounding those up to "done" on the way out would be the one thing
a move like this must not do.  **The numbers stay here because they are
addresses**: `test_comprehensions.py` and `test_datafun_sugar.py` cite
"roadmap 2.1", `test_prop.py` cites 1.1, `test_stage2.py` cites 2.2 and
2.3, and `gestate/audiovoices.py` and `audioscore.py` cite stage 3.  A
citation that no longer resolves is worse than a long file.


**Stage 0** — Correct what is silently wrong
* **0.1** Signature variables are not skolems (`fixme.md` F36) — **done**
* **0.2** δ's deviations: `dummy`, `split`, and the unit change (F3, F4, F5; `errata.md` D7) — **done**
* **0.3** `transform` skips `main` (F9) — **done**
* **0.4** ϕ/δ is applied to every supercombinator (F7) — **done**

**Stage 1** — Settle the specification decisions
* **1.1** Is `Bool` Datafun's `{1}` or an ADT? (`errata.md` D5) — **answered: both**
* **1.2** State the change-structure interface (`errata.md` D8) — **partly done**
* **1.3** Resolve the monomorphization contradiction (`errata.md` D9)

**Stage 2** — The Datafun surface that stage 1 unblocks
* **2.1** Comprehension guards (`errata.md` D6) — **done**
* **2.2** `fix` at a semilattice other than `Set A` (`fixme.md` F37) — **done**
* **2.3** `deriving Ord`, and sets of user data types — **done**

**Stage 3** — Music: the stated purpose

**Stage 4** — Type-system completions — **closed, none of it needed**

**Stage 5** — Confidence

**Stage 6** — Spec hygiene

**Stage 7** — The live audio environment

**Stage 8** — one instant, several arrivals — **done**

**Stage 9** — Transcendentals, and two synths to call for them — **done**

**Stage 10** — Notes, a score its instruments play, and a place to play it

## What is left after stage 10

**The closed items moved to `journal.md`** — the editor's withdrawal and
the canvas that followed it, source spans and the knob limit they turned
up, the environment and MIDI CC, stereo, tuples in the engine, and the
three compiler queries that are built.  They are Part III's tail, under
their own headings.  What is below is what is *not* done.

- **The `i64` hazard**, still the named unchecked one, and the FTZ/subnormal
  choice from 7.0, which `-O2` has not made necessary and which was never
  recorded as made either way.
- **The host layer needs a way to be wrong on purpose.**  Stage 10's
  defects were found by a person playing a keyboard, not by tests, and the
  audio core's whole method is that being wrong is *visible*.  There is no
  obvious oracle for "a key was pressed and a sound came out"; finding one
  is worth more than more care.
- **Changing the channel count in a running instrument.**  Stereo output is
  done; this is the part that is not.  The driver's buffer and the player
  process are fixed when playback starts, so an edit from mono to stereo
  installs a graph the driver is still filling one channel at a time.
  Stage 5 migrates state by shape and has nothing to say about the buffer
  around it.
- **Three comments standing on a dead constraint.**  F95 is fixed, so
  `signal.ges`'s `Both` (`signal.ges:56`), a `voices` bank's generated
  `Part` records, and `audio.ges`'s `LowpassIn` (`audio.ges:302` — "a zip
  needs a carrier and a tuple has no layout in the fragment") each cite a
  refusal the extractor no longer makes.  None of them is *wrong* — a named
  record documents what its fields mean and a tuple does not — but the
  necessity is gone and only the taste remains, so the comments should say
  that.  `Stereo` is the same question with an answer available:
  `sound : Sig (Float, Float)` could now replace it.
- **What a second and third substrate element turn up.**  The substrate is
  built (S1–S5); what is left is deliberately unspecified.  Hit-testing is
  a bounding box today, and which events a host delivers — wheel, key,
  hover — is a vocabulary question that should be settled by programs
  wanting them rather than in advance.  This is the same discipline that
  extracted `signal.ges` at the third combinator.
- **More tools that ask the compiler.**  Three are built; these are worth
  building next, in the order the value falls:

  * **`--migration OLD NEW` — what survives `Ctrl-S`.**  Stage 5 migrates
    running state by comparing node *origins*, so before saving you would
    like to know which oscillators keep their phase and which reset.  Every
    live-coding system has that question and almost none can answer it,
    because almost none have a stable node identity; this one does, and
    `audiolive.install` already calls `migrate`.  The tool is that
    comparison printed instead of applied, and in the editor it is a gutter
    mark: *this edit resets the thing on line 40*.
  * **A cost meter per definition.**  `audiospans` maps a node back to the
    line that produced it and has never been asked the inverse.  "This line
    is three nodes, one of them a `scan`" makes the fragment's discipline
    visible while you type — and is how you would notice that a `!` over
    four signals cost two `Both` layouts.
  * **Locals in `--fits`.**  It sees globals only.  At a hole inside
    `sineVoice g s = … _ …` the likely fillers are `g` and `s`, and
    inference has that environment at the hole.  This is the difference
    between a novelty and a tool you reach for.
  * Then, in descending order: `--uses NAME` for rename safety and "who
    plays this bank"; `--eval "keyHz 60"` in a file's context; reporting
    definitions `sound` no longer reaches, which in a synth are invisible;
    and much further out, unification provenance — *why did it think this
    was `Int`* — which is the expensive one and the one every language
    wishes it had.
- **A sixth synth, when there is a reason for one.**  Five have now failed
  to find a fragment boundary; the rule says the next one needs a purpose
  of its own rather than a hope of turning something up.

---

## Ariadne — what is left of it

`spec/ariadne.md` is the design and `spec/dynscore-constraints.md` is the
sheet it answers to.  **What is built is in `journal.md`**: stages one to
three (`draw` and `hear` as zero-width leaves, the boxes gone, `sown` and
`probe` retired, self-terminated cue streams), the position key that makes
a mid-piece rebuild land on the answers the take gave, the label half
(`Mark`, `section`, `marks_of`, `tick_of_mark`, and `case` over string
literals), and all three of `shape`, `fermata` and `tempoShape`.

What is below is what remains.

### Paths — the certificate, and the message

Two things the position key left behind:

- **The skip-identical certificate** — `(text, seed slice, readings
  slice)`.  It is what makes rehearsal jumping *sound* rather than
  hopeful, and it is a small step from the keys and the map now that both
  exist.
- **Saying that a joint could not be measured.**  The behaviour is defined
  — a `hear` of undeclared width has `durOf` 0, so `resumeSeq` asks
  `opaqueHead`, stops at the joint, and restarts the phrase there rather
  than falling quiet.  What is missing is the *report*.  A rebuild that
  restarted a phrase because it could not measure past a question should
  be able to tell you, the way `unfolding_names` names a score it cannot
  bake; the check is `opaqueHead` asked from the host, and the message
  names the joint and suggests the width.  The cure for wanting the skip
  is one word — `long n` — which is why it is load-bearing.

### Then: a position is a path, and the labels are payloads

Henri's own spelling, measured holding to the tick on the plain algebra:

    piece = ('"opening" ++ '"verse" ++ '"closing") >>= scoreParts

Sections arise from `>>=` exactly as instruments do — no `Section`
constructor, no combinator, and therefore no constructor tax.  A path is
then **bind provenance**: the labels of the binds above a position, plus
the structural turns between them (`verse/3/2` — third turn of a `cycle`,
second bar).  The precedent is stage 5's: graph nodes carry origin paths
and live migration works *because* identity is structural.

- **The open mechanic** is how a subtree learns which label bound it — an
  annotation the walk threads, or a provenance the sower stamps.  Either is
  invisible to the algebra, which is what makes it a free choice.
- **The thread** becomes transcript schema 2: the seed, and readings keyed
  by path rather than by beat.  Draws stay unlogged (derivable), positions
  stay unlogged (structural).  Keying by path is what survives an edit
  between takes, and what survives joint-dependent time — a tick after a
  `hear` may be uncomputable before the answer, `closing` names its place
  regardless.
- **What it buys, in one list**: rewind (replay the thread to the target,
  go live past it — past from the log, future from the world); resume by
  descent, with the effect-free arithmetic fast path kept; and
  **skip-what-is-identical** with the certificate above.
- **Ticks stay** as a derived coordinate wherever they are computable —
  every effect-free prefix — which is everything the DAW boundary needs.
  `mark`/`bar` are subsumed: an anonymous section is a bar point.
- **Acceptance**: `seek "verse/3"` stands exactly where playing from the
  top stands, held against the thread; and the existing five oracles keep
  passing, re-keyed.

### A6, which `tempoShape` opened and did not close

`tempoShape` is built, and it is the construct that makes the one
beats→samples conversion a *composition* of per-span maps along the path.
That stays one owned spelling, but it is real arithmetic in `samples_of`,
the CLAP cursor and the descriptor, and it is the half that wants watching
as pieces get longer.

### Open, and his to answer

Carried from `spec/ariadne.md` so they are not lost between sessions:

- **The fermata** — may a joint *wait*, or must every `hear` be answerable
  at its instant by sampling?  The arpeggiator needs only sampling; a
  conducted cue needs waiting; under the second reading "a hang is
  absence" becomes "a hang is a fermata", and lateness turns from a defect
  into a musical object.  The largest of these.
- **Polytempo** — `tempoShape` under `||`: two branches walking their own
  clocks between joins, or refused in v1?  The honest end of that road,
  and the most expensive register renegotiation on the page.
- **The port vocabulary** — `holds.<bank>` today; knobs as ports (the
  `Chan -> Port` bridge) wants deciding here rather than bolted on later.
- **Path spelling** and the autolabel format (`verse/3/2` is a sketch).
- **Whether `long` survives** as a skip-width annotation once paths exist.

---

## What I would deliberately not do

- **Rewrite `Bool` as `{1}`** unless 1.1 concludes otherwise.  It is the
  faithful choice and the wrong one for this language.
- **Chase D4's asymptotic win** by tuning.  Change minimization is
  implemented to spec and measured as a 10–12% cost that shrinks with size;
  the crossover is at a scale this evaluator cannot reach.  The fix is
  evaluator throughput, which is a different project.
- **Add modules** before there is a reason.  The prelude-shadowing
  machinery already covers the one case that hurt.
- **Make the interpreter faster for audio's sake.**  Measured and settled
  (`spec/liveaudio.md`): 30× would buy one voice with no headroom, and the
  shape is wrong regardless.  After 7.4 the evaluator is not in the audio
  path at all.  Interpreter work has to justify itself on its own terms.
- **Change the host language.**  The gap is not the host's fault, and
  changing it spends the effort in the wrong place.
- **Use scsynth.**  A real option — standalone, OSC, no sclang — but it pins
  the sound to SC's UGen set and adds a dependency.  Reach for it only if
  that UGen library is specifically what is wanted.
- **Dynamic voice allocation**, until one voice runs.  Several voices in one
  graph is a graph the extractor already handles; allocation is a second
  system.
