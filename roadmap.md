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

**The most recent work is the north star** — a note in a score box
that a hand can drag, byte-exactly, and hear — closed out in
`journal.md` §"The evening the picture learned to be dragged", with
`spec/north_star.md` as the contract it was built from.  It is the
first gesture in this project that writes text, and §"Content boxes"
below keeps only what waits behind it.

**Before it was the workbench**, closed out in `journal.md` §"The
editor becomes the editor".  `python -m
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

- **The `i64` hazard is met** and is `journal.md` §"The day the oracles
  arrived".  What is *left* of it: the check lives in the reference, so
  it is an oracle and not a guarantee — a program nobody renders
  through `audioengine` is not looked at.
- **The FTZ/subnormal choice from 7.0**, which `-O2` has not made
  necessary and which was never recorded as made either way.
- **The host layer's oracles — the audio half is built**, and the story
  is `journal.md` §"The day the oracles arrived".  This entry asked for
  one: *"there is no obvious oracle for 'a key was pressed and a sound
  came out'; finding one is worth more than more care."*
  `test_playedsound.py` is it — the real workbench, a fake player, and
  `audioperform.heard_note` asking which note came out, against equal
  temperament rather than against `keyHz`.  With it: the schedule and
  the hand agree as *sound* (`duet.ges`'s own prose, checked), and a key
  played through the C host renders what the Python driver renders.
  Beside it stand `tools/lagcheck.py` and `tools/dialoglag.py` for the
  window, `--report`'s peak and per-bar RMS for a mix, and the session
  transcript, which is still the working oracle for the editor.

  **What is left**, in order:

  * The ear hears **pitch**.  Timbre, level and timing are blessed by
    the goldens and by `--report` and by nothing external — a mix that
    got quietly duller would pass everything this project has.
  * The played tests are wall-clock except the C-host section, so none
    of them can assert *when* a key lands.  A press that arrived a
    block late would pass.
  * MIDI in from a real port is still nobody's: the oracle plays the
    on-screen keyboard, which is the same `Notes.feed`, but a port is
    another wire.
- **Take the older language features through the workbench.**  Datafun's
  surface, comprehension guards, `fix` at a product, `deriving Ord`,
  change structures, the typeclass machinery: every one of them has
  tests, and none of them has been *used* since the environment they
  were built before became the only way anyone touches this language.
  A feature that only its own tests exercise is a feature nobody has
  run in a year, and this project has already learned twice what that
  hides — the `Guard Bool` bottom that the F64 check found, and the
  canvas whose callers the editor's withdrawal had quietly orphaned.

  The exercise is to write something small in each of them *in the
  workbench*, the way a person picking the project up would: through
  the command list, the save cycle, the completion, a content box.
  The oracle is the environment itself — anything that cannot be typed
  there, or that the sidebar cannot infer, or that the fragment refuses
  in a way no message explains, is the finding.  What it produces is
  `fixme.md` entries; if it produces none, that is worth knowing too
  and costs an afternoon.
- **Three comments standing on a dead constraint.**  F95 is fixed, so
  `signal.ges`'s `Both` (`signal.ges:56`), a `voices` bank's generated
  `Part` records, and `audio.ges`'s `LowpassIn` (`audio.ges:302` — "a zip
  needs a carrier and a tuple has no layout in the fragment") each cite a
  refusal the extractor no longer makes.  None of them is *wrong* — a named
  record documents what its fields mean and a tuple does not — but the
  necessity is gone and only the taste remains, so the comments should say
  that.  `Stereo` is the same question with an answer available:
  `sound : Sig (Float, Float)` could now replace it.
- **Name the datatypes** — `type Duration = Float`, `type Pitch = Int`,
  and whatever else the preludes are passing around as bare numbers.
  The machinery is built and already used where it was missed most:
  `type Tempo = Envelope` and `type Port = Int` in `music.ges`,
  `type Seed = Int` in `synth.ges`, eight aliases in `command.ges`.
  What is missing is the pass over the rest, and the argument for it is
  the same one those eight make — a signature that reads
  `Float -> Float -> Sig Float` says nothing, and the same signature
  spelled in named aliases is documentation the compiler carries.  It is
  taste with a caller: every one of these is read by a person deciding
  what to pass.

  **Sequence it with F138.**  An alias is a name the window is handed
  *instead of* what it aliases to, which is exactly the defect F138
  names; minting more aliases before that fix spreads the bug rather
  than the documentation.  After it — the model sending `Pitch:Int`,
  the shown name and the base — naming things is free.
- **What a third substrate element turns up.**  The substrate is built
  (S1–S5) and the *second* element has now arrived: `Label`, written up
  in `journal.md` §"Words in a declared box".  It turned up the rule that
  a drawn word is placed by its own box and carries where the glyphs go,
  so a painter needs no second rule — and it did not move hit-testing,
  which is still a bounding box.  Which events a host delivers — wheel,
  key, hover — remains a vocabulary question to be settled by programs
  wanting them rather than in advance.  This is the same discipline that
  extracted `signal.ges` at the third combinator.
- **Examine the grammar of graphics** — the reading that stands beside
  the substrate the way `spec/frp_lesson.md` stands beside the signal
  half: Wilkinson's grammar, and Wickham's reading of it, set next to
  what `Sig Sub` actually is.  The question they answer is the one this
  project is about to meet twice — once for the substrate's own
  vocabulary and once for the score box's — *what is the smallest set of
  parts that draws data, and where is the seam between the data, the
  mapping and the mark?*  `Label` already turned up one such rule (a
  drawn word is placed by its own box), and turning up rules one element
  at a time is slower than reading what somebody else paid for.

  The output is a `spec/` reading, not a feature: what the grammar
  claims, what it costs, which of its parts this language already has
  under other names, and which of the four the substrate is missing.
  Its worth is measured the way `frp_lesson.md`'s was — by the gaps it
  names.
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

    **Spend `spec/rocks.md` on it.**  That spec is already the answer to
    "a number a person has to read is a number a person will not read":
    weigh *by kind*, three marks and no more, the ink growing with the
    quantity.  A node count in a margin is the same problem — every line
    carries one, so a bare number is noise, and what the eye wants first
    is *this line is heavy for what it is*.  The thresholds would be by
    kind again (a voice body is not a `scan` is not a constant), each
    carrying the sentence that justifies it, exactly as the file weights
    do.  Doing it this way also tests the claim rocks.md makes: that the
    mark is a general vocabulary and not a trick that worked once on
    bytes.
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
- **A drawing of the whole project — built, and it draws itself.**
  `python -m gestate.atlas` writes `doc/atlas/whole.svg`, one A3 sheet:
  what you write, the surface, the type layer, the core, the three
  backends, and the live environment around the audio one.  The story is
  `journal.md` §"The sheet that draws itself".

  **Both answers this entry weighed turned out to be one answer.**  The
  modules, libraries and crates are read from the tree and every drawn
  arrow names the import that proves it, so the machine supplies the
  nouns *and* checks the verbs; what a person writes is which lane a
  module is in and what each lane is for, which is the half no machine
  knows.  `test_atlas.py` fails when a module has no lane, when a lane
  names something gone, when an arrow has nothing behind it, and when
  the committed sheet is not what today's source renders.

  **The second sheet is built too**: `language.svg`, the front end pass
  by pass, whose order is not written down but read out of
  `pipeline._analyse` — with each pass's home resolved through its
  aliases, the refusals it can make followed two hops through the
  calls, and the G-machine's instruction set read from its own dispatch
  table.

  **What is left, in the order the value falls:**

  * **The wire is built** (`wire.svg`), and it verifies rather than
    describes: the seventeen `ged_*` calls with their arities and
    types, seventeen furniture rows, fifteen orders and thirteen
    gestures, each read from *both* ends and compared.  They agree
    today; `test_atlas.py` fails the day they do not, and a second test
    asserts the check itself could still fail.
  * **The sound path is built** (`sound.svg`) — the formers, the
    primitives, the IR's kinds, the score half beside the compiled one,
    and the C host's seam checked the same way the editor's is: Python
    naming a `host.c` function that is not there fails the test, while
    the C having its own internals does not.
  * **The score algebra is built** (`score.svg`) — every signature
    `music.ges`'s own line, sorted into what a person is doing when
    they reach for it, with *what the host asks a score* as a group of
    its own so that "not for you" is an answer.

  **All five carry the commit they were drawn at**, because the sheets
  are shared outside the repository; the stamp is the one thing the
  staleness check ignores, or every commit anywhere would demand a
  redraw.

  **The set is closed at five** — Henri, 2026-08-16, after reading
  them: *"This is enough and what helps.  The remaining could turn out
  noise."*  Which is the project's own rule arriving where it always
  does: a sixth sheet needs a caller, and "the set would be complete"
  is not one.  The generator takes another page whenever a question
  turns up that none of the five answers.

  And the limit, so nobody chases it: everything above is a fact in the
  source.  Why a pass exists, which arrow matters, what a lane is *for*
  and which words are yours are not, and stay written by hand.

- **Product safety wants a process, not a promise.**  This project can
  now hand a person a full-scale blast in their headphones, overwrite a
  file they wanted, or spend an hour rendering something nobody asked
  for.  Each of those has *a* guard — `--report`'s peak, the overwrite
  question, rocks.md's marks — and no one has ever written down the list
  or when it is checked.  A named process (what is verified, and before
  which act) is the thing that makes the guards a promise rather than a
  set of habits that happen to hold today.  The newest of them is the
  pre-flight weighing below, which asks before a heavy render rather
  than reporting after it; it is also the pattern the rest would follow.
  **Scope is Henri's to set**: the smallest useful version is a
  checklist run before a release; the largest is a test suite that
  asserts each guard fires.

- **A sixth synth, when there is a reason for one.**  Five have now failed
  to find a fragment boundary; the rule says the next one needs a purpose
  of its own rather than a hope of turning something up.

---

## What to build next

**The star is behind us**, so this section is the pair it had before:
one thing that finishes something the workbench made cheap, and one
new capability that most of the parts for already exist.  The save
cycle is closed out and moved to `journal.md` §"The day the save cycle
was measured"; what is left *of it* is measured and listed below,
under the heading it kept.

Read `§"Content boxes"` first if the question is what to do with the
editor — it now carries the shorter list, tier two at its head.

### The save cycle — closed out, and what is left of it

A save of `examples/audio/quartet.ges` was **twelve seconds** and is
about three; a start of `noted.ges` was fourteen and is under five.
The journal has the arc: the hole scan and the sidebar that re-inferred
every prelude, the seam that one shadowed name turned off for nine of
the forty-five examples, `GESTATE_BUILD_TIME` and the two ways it was
itself wrong, the analysis cache that was evicting the file it cached,
and the two merges — one program for a page of rolls, one for their
pictures.  `clang -O1` is written up there as measured and rejected.

What is **not** done, in the order the value falls:

- **`examples/long/sauna.ges`'s start** — Henri's own observation, six
  seconds of it in the score.  Looked into on 2026-08-15 and it came
  apart into three; the story is `journal.md` §"The day the oracles
  arrived", and the quadratic in the G-machine's environment is fixed
  (`pipeline.compile` on sauna 0.49 s → 0.25).  **What is left:**

  * **The same assembly is compiled twice a rebuild**, because
    `pipeline.compile` has no cache the way `analyse` does — the
    score's stream and the `FromMIDI` interpreter each ask and neither
    knows about the other.  Sharing wants the distinction
    `Substrate.several` makes on the canvas side: a `GmState` is a
    machine with a heap the caller runs, so what two readers can share
    is the compiled code and the constructor table, not the state.
  * **The start's concurrency was mostly illusory, and the decision
    is made.**  The loaders run inline; `GESTATE_SIDE_THREAD=1` puts
    the thread back for a machine that answers differently, and
    `doc/switches.md` carries the measurements both ways.  Asked again
    for the *rebuild* on 2026-08-15 and answered no: an apply of
    `Real_World_One.ges` is 3.15 s, of which `clang` is 1.28 s of
    subprocess holding no GIL and the loaders that could overlap it
    come to about half a second — a ceiling of a seventh, bought out
    of the one stretch in which the audio thread has Python to itself.
    A rebuild that stutters is worse than a rebuild that is slow.
  * **`_bump_env`'s single-bump callers**, still 0.24 s of a
    `stream_root`.  The standard fix is a reference held as an offset
    from a base depth, so bumping is an integer rather than a
    dictionary — a change to how `compile_c` threads its environment,
    and its own sitting.

- **The whole-module tail — about 0.2 s a front end.**  Everything
  after the seam still runs over all 232 k assembled characters:
  `_discharge` 0.21 (elaborate 0.15, specialise 0.04),
  `desugar_program` 0.13, exhaustiveness 0.06, `expand_envelopes` 0.04,
  `resolve_static_methods` 0.04, kind check 0.03 — over library SCs
  that cannot have changed.  The largest single piece is desugaring,
  and the front already holds the answer: `_analyse_staged` desugars
  the whole module and throws the library half away.  **It is not a
  free deletion.**  `match.fresh_name` runs off a global counter that
  `desugar_program` resets, so skipping the library half moves every
  generated binder; the fix is a `names_end` in `StackFront` beside
  `fresh_end`.  Exhaustiveness and the kind check are already run over
  the head when the front is built.  Elaborate and specialise cannot
  skip library SCs at all — a program call site specialises a library
  body — unless the SCs no constraint touches are identified first.
  Worth doing deliberately: every piece of it is silent when wrong.
- **A file with a canvas is analysed twice a save.**  The sound and the
  picture are different assemblies of the same file — different
  preludes, different entry — so both halves pay the tail above.
  Unifying them is a language question (one prelude for both, or a
  synth paying for `gui.ges`), not a caching one.
- **The tuning half is spent.**  `expr._field_names` was worth 5%, not
  the 10% guessed here; what is left of that idea is `types.apply`, at
  843,000 calls per analysis.

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

### The pre-flight weighing — closed out, and moved to `journal.md`

An export weighs itself before it renders, at `▲` and nothing lighter;
the story is `journal.md` §"The morning the messages arrived in time"
and the contract is `spec/rocks.md` §"Before it is written, too".
**What is left of that spec** is its other two omissions — a sound's
honest measure is its duration, and nothing weighs the repository —
and neither has a caller.

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
and everything after it decisions.  All of it is built now: the
mechanism, B1 through B3, B4's reading half and, on 2026-08-15, its
editing half.  What is left below is what waits *behind* that, and it
is a shorter list than the questions this section used to carry.

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

### B4's editing half — closed out, and moved to `journal.md`

The star, built on 2026-08-15: a hand takes hold of a note in a score
box, carries it, lets go, and **one atom's characters change** — no
reflow, no reprint, one text undo, and the piece plays a third higher.
`spec/north_star.md` is the contract, refined against the building
twice: the hands tile the picture in columns rather than sitting on
written places (measured — seventeen of chopin's twenty-eight regions
would have been unpressable), and the drag is relative because a
column is the whole height of the roll.  `transpose` is in
`command.ges`, so a drag records in a transcript as a command and
replays as one; the journal entry has the story, including the note
that follows the hand through a *reading* rather than a rebuild.

### What waits behind it

- **Tier two** — a gesture that changes the *shape* of the expression:
  splitting a `++`, inserting a rest, moving a note in time.  Gated on
  the declaration already being formatter-clean (`fmt(decl) == decl`),
  which turns "is every musical gesture a span rewrite?" from a
  question of philosophy into a per-declaration predicate the box can
  answer before it offers the handle.  `spec/north_star.md` §"What is
  decided" settles the shape; nothing is built.
- **Typing a pitch** rather than dragging to it, which is the thing
  that will force the keyboard question the pointer-only rule has been
  deferring.
- **Horizontal movement**, which is tier two wearing a costume.
- **F138**, filed with its repro: a space in a filler field runs the
  completion on half the answer, because the window is told what an
  argument's type is *called* and `Filler` is a `Text` alias.
- **A small window for a cursor that is off screen.**  Henri's note:
  *make a small window that shows where the cursor is when it is off
  screen, and edit through it.*  The occasion is that this editor moves
  the cursor by itself now — a completion walks to the next hole, a
  drag rewrites an atom, an apply lands somewhere — and the rule the
  completion keeps (*near, and not anywhere*, `session.py`) is a rule
  about **where the change is**, not about whether you can see it.  When
  the place is off screen there is nothing between "it happened" and
  scrolling to find out what.

  A peep window is the cheap answer: a band showing the lines around
  the cursor wherever it actually is, and — this is the part to settle
  with him — the edit made *in* that window, so the automatic edit and
  the sight of it are one thing rather than two.  The parts exist: rows
  of varying height, a walk clipped to a band, and a box whose touches
  are ordinary `touched` events.  It is a third reading of the same
  machinery B2 and B4 are built from.
- **The alias half of F141.**  `foo : int` is caught (the story is
  `journal.md` §"The morning the messages arrived in time"); a
  lowercase name matching a type *alias* is not, because aliases are
  expanded before the kind environment exists.  It belongs with the
  naming pass above — `type Duration = Float` is precisely what would
  make such a collision likely — and until then the gap is recorded in
  F141 rather than guessed at.

### Later, and blocked on the language

Visualisation boxes want **sample buffers** — audio-rate arrays, which
collide with the fragment's "no lists at audio rate" rule and are a
language decision, not an editor one.  Sequence that on its own merits;
the boxes will be waiting as B2 canvases the day it lands.

### The questions this section carried, all answered

Four were open before the editing half and none is now.  What a chancy
score shows and who says how tall were answered when the read-only box
shipped (`journal.md` §"The notes arc").  The other two were answered
by `spec/north_star.md` before a line was written, which is what that
document was for:

- **Whether every musical gesture is a span rewrite** — no, and the
  tiers say which are.  Tier one replaces one atom's byte range with a
  literal of the same kind and is what shipped; tier two is gated as
  above; tier three is refused *by name*, with a sentence.
- **The third focus** — there is none.  Text and the piano own the
  keyboard; a box is pointer-only, every gesture is a `touched` a
  transcript can hold, and the vocabulary rule is satisfied by naming
  the gesture as a command.  The first gesture that genuinely wants
  typing is the one that should reopen this.

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
