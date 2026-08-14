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

**The most recent work is the workbench**, and it is closed out in
`journal.md` §"The editor becomes the editor".  `python -m
gestate.workbench` is the only window now: a command list derived from
`gestate/command.ges`, margin knobs and bank boxes, a piano, the
substrate drawn by `gestate-panel`'s own painter, and a file dialog.
The `tkinter` editor and `audiopygame` are retired.  §"What to build
next" argues what that makes cheap.

**Before it was ariadne**, the redesign of the score's reactive surface
(`spec/ariadne.md`): chance and listening as lawful zero-width leaves of
the score monad rather than boxed constructs beside it, bound with the
`do` sugar (`spec/monad.md`).  Its first three stages are built, the old
surface is retired, and `shape`/`fermata`/`tempoShape` landed with it
(`spec/shape.md`).  **What is left of it is paths** — a position named
by the binds above it rather than by a beat — and §"Ariadne" argues it.

The substrate is built and no longer future tense: `spec/substrate.md` is
the design and `journal.md` has what it cost.  A canvas behind the editor
in the same window, written in gestate, composed the way a synth is — **a
substrate is a value, `substrate : Sig Sub`, built from smaller ones by
ordinary functions** — interpreted at frame rate, worth a control value to
the compiled synth the way a knob is.  **And it travels**: a file that
declares one exports it, and the plugin draws it on the second tab of its
own window beside the knobs, forced at frame rate on the window's thread
while the score is forced on the audio thread.  A touch on a canvas fader
is a parameter change the host sees, because the export pairs a drawn
channel with the control slot the graph reads it from — one fold, two
readers, delivered.  The plugin's **seed** is a parameter too, so a
chancy piece is a family of takes you can roll rather than the one night
it was exported with.  `spec/frp_lesson.md` is the reading
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

  **This got worse before it got better, and there are now two
  instruments.**  The workbench's twelve defects were every one of them
  found by a person using it while two thousand tests passed
  (`journal.md`).  `tools/lagcheck.py` drives the real window with real
  X events through XTEST and reads the result off the screen;
  `tools/dialoglag.py` reads the window's own `GESTATE_EDITOR_TIME`
  stopwatch the same way.  And **the session transcript became the
  working oracle in practice**: 2026-08-13's two dozen defects were
  nearly all pinned by one (`journal.md` §"The day the transcripts
  earned their keep").  What is still missing is the *audio* half — a
  played key against the sound that comes out — and it is not a
  feature, which is why it keeps losing to features.  A piece of it
  arrived by way of `spec/firstpiece.md` (2026-08-14): `audioperform
  --report` says the peak and each bar's RMS after an `-o` render —
  the numbers undertow's mix was iterated against, and ears enough
  for a CI to hear a render change loudness.  The *live* half, a
  played key against the sound that comes out, is still the missing
  piece.
- **Three comments standing on a dead constraint.**  F95 is fixed, so
  `signal.ges`'s `Both` (`signal.ges:56`), a `voices` bank's generated
  `Part` records, and `audio.ges`'s `LowpassIn` (`audio.ges:302` — "a zip
  needs a carrier and a tuple has no layout in the fragment") each cite a
  refusal the extractor no longer makes.  None of them is *wrong* — a named
  record documents what its fields mean and a tuple does not — but the
  necessity is gone and only the taste remains, so the comments should say
  that.  `Stereo` is the same question with an answer available:
  `sound : Sig (Float, Float)` could now replace it.
- **What a third substrate element turns up.**  The substrate is built
  (S1–S5) and the *second* element has now arrived: `Label`, written up
  in `journal.md` §"Words in a declared box".  It turned up the rule that
  a drawn word is placed by its own box and carries where the glyphs go,
  so a painter needs no second rule — and it did not move hit-testing,
  which is still a bounding box.  Which events a host delivers — wheel,
  key, hover — remains a vocabulary question to be settled by programs
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

## What to build next

Three now, and the first one is not a feature at all: it is the save
cycle everything else is edited through, measured and found to be
twelve seconds.  The other two are the pair this section has always
had — one finishes something the workbench made cheap, the other is a
new capability Henri wants and that most of the parts for already
exist.

**The save is twelve seconds, and that is the thing to fix first.**

`journal.md` records a rebuild at 400 ms when 7.5 shipped.  That number
was `blip.ges`, and it is still about right for it — 1.3 s today.  The
pieces got fifteen times bigger and nobody measured again.  One save of
`examples/audio/quartet.ges` in the workbench, every cache warm:

| phase | cost |
|---|---|
| `graph_of` → `pipeline.analyse` | **4.6 s** |
| `graph_of` → assemble and extract | 1.1 s |
| `_place` → `_find_holes` | **2.4 s** |
| `_load_substrate` | 0.5 s |
| `_load_from_midi` | 0.3 s |
| `clang -O2`, when the IR changed | ~3 s |
| **one save** | **~12 s** |

The first measure below is built and that is **8 s** now.  The rest of
this section is what is still true.

Nothing here is scheduled by the rule as a *feature* — it is scheduled
because a twelve-second save on the piece being written is a defect, and
a defect is always a caller.  And it is not the thing this file forbids:
"make the interpreter faster for audio's sake" is about the audio path,
which the evaluator left at 7.4.  This is the *edit* path.

Three measures, in the order the value falls:

1. **Stop paying for holes nobody wrote — 2.4 s.  Done, 2026-08-15.**
   `typecheck.holes_in_source` ran its own `_merge_prelude`,
   `desugar_program` and `infer_program`, so it missed the analysis
   cache *and* the staged path and re-inferred every prelude from
   scratch — and `_place` called it on every rebuild whether or not the
   file contained a single `_`.  It asks `pipeline.analysed` now: a new
   door beside `analyse` that recalls and **never computes**, for a
   caller that wants the answer only if it is free and has a cheaper
   path otherwise.  What lets it read that answer is that a hole
   survives elaboration and specialisation *carrying its type*, which
   the old path — stopping at inference — never had to rely on, so
   `test_pipeline.py` holds it two ways: the cached answer equals the
   cold one, and `_analyse` replaced by something that raises leaves
   the scan passing.  `_find_holes` 2.37 s → 0.07 s, `_place` 2.56 →
   0.28, **the save 12.0 s → 8.0 s**.  `_load_substrate` and
   `_load_from_midi` are the same shape, smaller, and still to do —
   as are `fits_in_source` and `signatures_in_source`, which have the
   identical defect on the `?`/`Tab` path rather than the rebuild one
   (and which `analyse`'s own docstring already claims are answered
   from the cache).
2. **Then the front end is the whole of the rest — 4.6 s.**  It is
   already staged: the stack front holds the libraries' parse and
   inference.  What still runs over all 232 k assembled characters
   every time is everything *after* that seam — `infer_program` 45%,
   `_discharge` (elaborate and specialise) 15%, `desugar_program` 12%
   over the whole module, `lower_fields` 9%.  Two different jobs live
   in that list.  *Tuning*: `expr.subexprs` and `map_children` ask
   `dataclasses.fields()` 170,000 times per analysis and `is_dataclass`
   as often, so caching the field tuple per class is ~10% across every
   pass for a few lines, and `types.apply` runs 843,000 times.
   *Structural*: desugaring a library item is a pure function of the
   stack text and could join the pickled front, and elaborate and
   specialise could skip the SCs no program constraint touches — that
   is a question about where the seam sits, not tuning, and it is the
   one to think about rather than measure.
3. **`GESTATE_BUILD_TIME`, the compile-side twin of
   `GESTATE_EDITOR_TIME`.**  The frame side has instrumentation and two
   lag tools and consequently does not rot; the build side has neither,
   which is exactly how 400 ms became twelve seconds with two thousand
   tests passing.  The table above, printed per rebuild, is the whole
   feature.  This project's own sentence: *"it feels slow" is not a
   measurement.*

**Measured and rejected: `clang -O1` for interactive builds.**  It
looked like a free 1.3 s of the three, and the objects are *bit
identical* to `-O2` — verified on `blip` and on `quartet`, and expected,
since the emitter writes no fast-math flags and LLVM will not
reassociate without them.  It costs render speed instead: `lead.ges`
goes 30× realtime → 16×, and `quartet` already renders at under 2×, so
it would spend most of the remaining headroom to save nothing on
`lead`, where `-O1` was not even faster to compile.  The content
addressed `.so` store is already the right answer on that side.

**`--migration OLD NEW` — what survives `Ctrl-S`.**

It is already first in "more tools that ask the compiler, in the order
the value falls".  What changed is that the sentence written there —
*"in the editor it is a gutter mark: this edit resets the thing on line
40"* — was future tense about an editor that did not exist.  It does
now, and it has exactly the parts that line needs: a margin that draws
per-line marks, a description keyed by line that already carries `knob`
and `trouble`, and `apply` as a command you press deliberately.

Both ends are built.  `audioengine.migrate(old, state, new)` exists and
`audiolive.install` already calls it; **the tool is that comparison
printed instead of applied**, and the gutter mark is the same comparison
drawn instead of printed.

The reason to do it before the others is not that it is cheap, though it
is.  It is that it answers the question this whole environment's premise
raises.  The sound does not stop when you save — so *which oscillators
keep their phase, and which start over?*  Every live-coding system has
that question and almost none can answer it, because almost none have a
stable node identity.  This one does, by origin, and has since stage 5.
Being able to see before you save that line 40 will reset is the
difference between editing a running instrument and poking it.

It also has the right shape for this project: it invents nothing, it
makes an existing fact *visible*, and it is a third reading of the same
node-origin map that `audiospans` and the knob column already read.

**After it, in the order the value still falls**: a cost meter per
definition, then locals in `--fits`, then `--uses NAME`.  All three are
argued above and none of them changed.

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

## Content boxes — the editor grows a vertical dimension

The margin proved the idea sideways: a knob drawn **beside its own
declaration** is content anchored to source, and it changed what the
editor is.  This grows the same idea downward — **content that
interleaves with the text**, occupying room *between* lines: the
compiler's complaint under the line it is about, then small
between-line editors for musical score content, and eventually audio
visualisation, once sound sample buffers exist for them to show.

It read tall and was mostly design: the window already drew from a
display list with one painter, the model already described furniture
per row, and `audiospans` already anchored things to declarations.
There was **one real implementation lump** — rows of varying height —
and everything after it decisions.  The lump is built and so are the
first three stages and B4's reading half; what is left below is the
editing one, and the decisions it still owes.

### The mechanism and B1–B3 — closed out, and moved to `journal.md`

The row table, the complaint's box, the picture and its hands all
shipped — the mechanism and B1 on the days the scopes arrived, B2 and
B3 together on 2026-08-14, landed on the walked floor and simpler
than designed here: no display list crosses, because the box is the
window's own walk clipped to a band, and a touch in a box is a
`touched` like any other.  The ask is a `canvas` line with `sink`'s
manners — bare for the substrate, `canvas <expr>` for any
expression's own box, several at once.  `spec/workbench.md`
§"Content boxes" is the contract as built; the journal entry has the
story, including the three revisions a day of Henri using it forced.

### B4's read-only half — closed out, and moved to `journal.md`

A `notes <expr>` line stands a roll of that expression on it, showing
the take the session's seed names, with span ink and take ink and a
press that reveals where a note is written.  `spec/scorebox.md` is
the contract, `gestate/scorebox.py` the box's mind, `Notable`
(`audio.ges`) how a payload is read, `spreadTo`/`tagAll`
(`music.ges`) the bounded walk and its labels, and
`test/test_scorebox.py` the acceptance; `noted.ges` and `minute.ges`
show it at four bars and at a minute.  The journal entry has the
story, including the four traps the building found and F136 with it.

### B4 — the editing half, which is the point

The star: a between-lines editor for score content.  The principle is
already on the wall (`spec/workbench.md`): **a widget is a view over a
span of source, and dragging it is a text edit** — the knob rewrites
its declaration byte-exactly, and the score box must keep that same
faith.  It renders the score expression under it; every gesture on it
is a rewrite of the span it views; undo stays text undo; the file
stays the single truth.  A box that kept its own document would be a
second editor to keep honest, and the answer to it is no.

### Later, and blocked on the language

Visualisation boxes want **sample buffers** — audio-rate arrays, which
collide with the fragment's "no lists at audio rate" rule and are a
language decision, not an editor one.  Sequence that on its own merits;
the boxes will be waiting as B2 canvases the day it lands.

### Open, and to be answered before the editing half

**Two of the four are answered and gone** (`journal.md` §"The notes
arc"): what a chancy score shows — the take, labelled with its seed,
which is the lean this list already had and is now built and lived
with — and who says how tall, which `spec/workbench.md` decided when
the row table shipped and this list was never told.  The two left
belong to *editing*, and the read-only box needed neither: its one
gesture is a press that moves the caret, and it writes nothing.

- **Whether every musical gesture is a span rewrite.**  Dragging a note
  up a third is a clean rewrite; gestures that change the *shape* of
  the expression (splitting a `++`, introducing a `draw`) need a rule
  for what text they produce and how it is formatted — `fmt` exists and
  is idempotent, which may be the whole answer.
- **The third focus.**  Text, piano, and now a box may own the
  keyboard; the click-to-focus rule extends, but the vocabulary rule
  must too — a box's capabilities appear in `command.ges` or they do
  not exist.  Worth settling with the transcript in mind: a gesture
  that desugars to a command *records* as one, which is how nearly
  every editor defect has actually been pinned.

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
