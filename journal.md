# journal.md — what was built, in order, and what it taught

**Past tense, and that is the whole distinction.**  `roadmap.md` says what
is left and why in that order; this says what happened.  The two were three
files for a while — Part I, Part II, and the completed
two thirds of `roadmap.md` — which were the same artifact written at three
different moments, and telling them apart cost more than reading them did.

**What is *not* here.**  Two registers, and they stay where they are because
their numbers are addresses that `gestate/*.py` cites:

* `fixme.md` — where the implementation disagrees with the specs.  Fifty-six
  distinct `F` numbers appear in source comments.
* `spec/errata.md` — where the specs disagree with the papers.  `D` numbers,
  cited the same way.

An entry in either is closed by marking it resolved, never by deleting it.
This file has no such contract: it is a narrative, and the way to use it is
to search it.

**The three parts are chronological, and they are in the archive.**
`journal/2026-08.md` opens with them: **I** is the language, built as
increments; **II** is making it usable by a person, built as phases; **III**
is the staged plan the roadmap carried until each stage was done.  Item
numbers are kept exactly as they were written, because `roadmap 2.1`,
`roadmap 2.3` and `stage 3` are cited from the test suite and from
`gestate/audiovoices.py`.

## The archive — the closed months, one line each

`journal/` holds the closed months.  A closed month is **append-only**:
a cut is added at the bottom and nothing above it is ever edited, because
git already remembers and a journal that is retroactively edited becomes a
second source of truth about the past.  Archive, don't airbrush.

**A citation says `journal.md` whatever month it landed in.**  The file is
the journal's name and the archive is where its closed months live — the
same separation as a card's id and its shelf, and for the same reason: a
citation must not rot because time passed.  `test/test_citations.py`
resolves a `journal.md §"…"` against the archive too.

| month | lines | what it was about |
|---|---|---|
| [2026-08](journal/2026-08.md) | 13,091 | the language built out to a running query; the editor and canvas rebuilt in Rust; the compile, save cycle and audio measured; the instruments — gemba, the andon, the gates, the atlas; the method itself capped, given a memory in the tree, and met by its first outside readers; and then the method's second half — the fire adopted and the journal rotating, fourteen sections moved out of the rules, the third stranger run, the sitting and the leash, four seeded agents and a stranger's AI building a host around it, the conditioning trials, gestate in a browser tab, and the ungated sweep's batches 6-9 |

*The open month is 2026-09.*  `python tools/journalroll.py` says where the
lines are and whether the rotation is due; `spec/rules.md` §"The journal
rotates" is the contract, and the rotation is an act of the fire, not of a
gate.

---

## The provenance moved to the journal — 2026-09-01

*`spec/author.md` was thinned at Henri's ask — **"I give you the
permission to do the change on author.md, move provenance into the
journal"** — after the month's rotation left the five method documents
at 2,000 of 2,000 with no room for the next promotion.  The test is
`spec/rules.md` §"What the fat is", run forwards: a sentence stays in a
rule document only when a stranger needs it in order to **follow** the
rule.  What follows is what needed only to be **believed**, kept
verbatim.*

**The heading stays where the body left.**  `journal/2026-08.md`
§"The fourteen, moved out of the rules — 2026-08-23" cites
`spec/author.md` §"Where this method came from" by name, and a closed
month is append-only — so that heading can never be renamed or removed
without the citation gate going red.  The same constraint blocked
today's other promotion from becoming a fourth item under
`manifesto.md` §"The three ways an instrument fails".  **A heading
cited from a closed month is frozen**, and that is worth knowing before
the next tidy-up reaches for one.

### From §"Review is three jobs" — the day that measured it

The evidence is a single ordinary day.  Five mistakes were made on
2026-08-16.  Three were caught by machines within minutes — `doc/ref/`
gone stale, three rotted citations, a broken card link.  Two were caught
by Henri, and both were *judgement* rather than defect: a full suite run
started outside `tools/suite.py`, and a task referred to by a number that
meant two different things.  A person who had been asked to catch all
five would have been exhausted and would have caught the wrong three.

### From §"Five practices", 5 — why a kaizen has to land in a file

**And it must land in `journal.md`**, or it does not survive the
session.  This is the gap it exists to close: a day's *findings* are
committed as they happen — an F-number, a card, a gate — and a day's
*reflections* live only in the conversation that produced them.  On
2026-08-18 five process changes came out of one afternoon (levelling the
sweep, one sheet then depth, the `card:` notation, questioning a card
into existence, and *briefness is my failure mode*), and not one of them
had a home until it was written into a document deliberately.  A session's
context is summarised as it fills, and **verbatim fidelity is what
degrades first** — which is precisely what this project runs on.

### From §"Five practices", 5 — jidoka or retrospective, left open

**One open question, worth answering rather than assuming.**  Everything
that changed on 08-18 was triggered by something going wrong in front of
us, not by a scheduled review — which is *jidoka*, stopping the line at
the fault, and not a retrospective.  So it may be that the practice is
**stop and write it down when something breaks**, and the evening is
only for what a whole day makes visible that no single fault does: the
pace, the load, the drift.

### §"What was got right here, and why it is not luck", whole

*One line survived into `spec/author.md` §"The thing that will actually
get you": **go as fast as your oracles allow, and no faster.**  The rest
is the argument for it.*

## What was got right here, and why it is not luck

Worth writing down because it is short, and because the same speed
without it would have buried this project months ago:

1. **The model imports no toolkit.**  Everything is testable with no
   window in the room, which is why there are tests at all.
2. **Every action returns a sentence.**  What the status line shows is
   what a test asserts on — *"an action that reports nothing is one
   nobody can check"*.
3. **One arithmetic for drawing and for hit-testing.**  A control that
   answers where it is drawn cannot drift from itself.
4. **The journal explains *why*.**  A session arriving with no memory
   reconstructs the reasoning by reading, not by asking — which is what
   makes a cold start cost twenty minutes instead of a day.
5. **`manifesto.md`'s rule**, §"costs, and where it is not paid": being
   wrong has to be visible to something that is not a person's
   attention, *because attention is what runs out*.

None of those is an accident; each was written down before it paid off.

**The honest caveat**, because it belongs beside the list: had it gone
south instead, there would have been no way to know these were the
load-bearing ones.  The diagnosis would have read *"too fast"* rather
than *"unverifiable"*, and the wrong lesson — slow down — would have
been learned.  The lesson that is actually true is: **go as fast as
your oracles allow, and no faster.**

---

### §"Where this method came from", and §"Go and see"

*Moved whole.  Seventy lines of provenance: where the method came from,
who brought it, and the epistemological claim under `card:gemba.md`.
The heading is still in `spec/author.md` as a pointer, for the reason
given above.*

## Where this method came from

*Added the same evening, at Henri's ask.  He read the Toyota Production
System carefully about a month ago, taking notes — Janne is the reason
it is in this project at all — and said that before that, AI had been
"all cool demos and nothing else".*

**The fingerprints are in this repository, in his vocabulary rather than
an assistant's.**  *Jidoka* is "free the people from machines", his
phrase, and the heading it sits under in `journal.md` §"The day the
machines learned to stop themselves".  *Poka-yoke* he asked for by name,
the moment he caught a suite run that left no record.  *Gemba* is a
card.  *Kanban* is what he called the board before it was one.  "Make
problems visible" is `manifesto.md`'s rule.

**Why that frame in particular unlocks this kind of work.**  A model is
a high-throughput process step of variable quality.  That is exactly
what TPS was built to manage, and exactly what the demo framing gets
wrong: a demo treats the model as a *product* — look what it can do —
when the useful question is what it is *in a line*.  Without jidoka
around it, throughput only produces defects faster, which is the
mass-production trap TPS was a reaction against: build a lot, inspect at
the end, rework.

The sharpest transfer is the one this whole file is about.  TPS's answer
to *the machine is faster than the inspector* is not **inspect harder**.
It is: make the machine stop itself, and make the defect visible at the
source, immediately, to something that is not a person's attention.

**The scorecard is in the journal.**  This project was scored against
Liker's fourteen, and the two principles it was missing — *pull* and
*heijunka* — were argued out at length; both were closed by
`card:timer.md` and `card:ungated-fixes.md`, and the argument is
`journal.md` §"The fourteen, moved out of the rules".  It is kept
because it is why anybody should believe the frame, and it is not here
because believing the frame is not how you follow a rule.

### Go and see

The book's other instruction, in Henri's words: *go out and do things —
that's the fastest way to learn and become self-reliant.*  Principle 12,
and it is not advice about diligence.  It is an epistemological claim:
the knowledge that matters is not in the report, and a person who only
reads reports will be confidently wrong in ways they cannot detect.

It holds on both sides of this collaboration:

- **For the author.**  Tests were not adopted here because someone
  argued for them; they were adopted because they *caught things*, and
  the conviction arrived through use.  The same is true of the fence,
  the transcript, and `rocks.md`'s marks.  Reading about any of them
  would have persuaded nobody.
- **For the assistant.**  On the day this file was written, a defect had
  survived a two-thousand-test suite: a press on a note scrolled the box
  out from under the hand that was pressing it.  Nothing found it until
  a real window was driven, under a real display, with a real press, and
  the pixels were looked at.  Every unit test passed through that bug.
  **Going to the actual place is not a slower substitute for reasoning;
  it is the only instrument that sees what reasoning has already assumed
  away.**

The honest note on the assistant's side of this: knowing the literature
is not knowing the work.  An assistant can map these fourteen onto a
repository in a minute and has never stood on a line, waited for a part,
or pulled an andon cord with a shift watching.  The book's own point is
that this second kind of knowledge is the one that decides, which is
precisely why `card:gemba.md` is a card and not a paragraph.

---

## When you disagree with something that was built

Say so plainly and early; it is cheap.  `git revert` exists, the work is
in granular commits so that a single idea can be taken back without
taking back four others, and a card can be reopened by moving it out of
`board/done/`.  **The expensive thing is not the wrong build — it is the
wrong build left standing because nobody said anything**, until three
other things depend on it.

An assistant that only agrees is worth less than one that argues, and
the same is true in the other direction: this project is better when you
push back, and today's two catches are the proof.

## The claim that outlived its file — batch 10, 2026-09-01

Batch 10 of `card:ungated-fixes.md` — **F40 F39 F31 F25 F23**, the Tuesday it
was due — measured by mutation against a targeted set of 37 language test
files, 780 tests, about three minutes a run, on the live tree.

**F40 is what the batch is about, and the finding is the rotation's.**  The
entry closed on a pipeline diagram rewritten against the real `pipeline.py`.
That diagram was in `journal.md` Part I; **this morning's rotation moved it into
`journal/2026-08.md`, and a closed month is append-only.**  Its own defect put
back — the ϕ/δ line swapped after the Datafun-desugar line, exactly what
`spec/data.md` §0 forbids, with the line count unchanged — leaves 298 of 298
doc and pipeline tests green.  The only thing in the tree that notices the file
at all is its *length*: delete a line rather than move one and two gates go
red, because the archive's line count is quoted in the index row and in
`doc/method.md`.  A page can be wrong in every sentence and right in its
line count, and only the second is held.

And the gate is not missing, it is **unwritable**.  One holding the diagram
against `pipeline.py` would be red the day it was written — `_analyse` runs
`envexpand.expand` and `specialise`, and the diagram has neither, so it has
drifted again since F40 closed it — and it could never be made green, because
the file may not be corrected.  *The claim outlived the file's editability.*
That is a cost of rotating a journal that nobody had priced, and it is the
third time today the archive's append-only rule decided something: it also
froze `manifesto.md` §"The three ways an instrument fails" out of gaining a
fourth item, and kept `spec/author.md` §"Where this method came from" as a
pointer when its body moved out.

**F23 and F25 were repairs to a page nothing read.**  Both are edits to
`spec/syntax.md` — `Box` and `deriving` into the reserved-word list, `..` into
the fixity table — and no suite can see an edit to a page.  Two tests now pull
both lists off the page and hold them against `tokenize._RESERVED` and
`descend.DEFAULT_INFIX` in both directions, the shape `test_syntax_spec.py`
already had for F63.  Four mutations, four reds.

Their reverse direction is the batch's second new number.  **F193**: `do` is
reserved by the tokenizer and is not on the page's list, though `spec/monad.md`
prices its whole feature at *"one reserved word"*; `internal` likewise, and
`gestate/signal.ges` uses it, so every reactive program compiles through a
keyword the syntax page does not name; and `%` has `infixl 8` in the parser and
no row in the page's table, which is F25's defect exactly.  All three were
carried as a **shrink-only baseline** in the two new tests — question 3's shape
from the card, an accepted baseline that may shrink and never grow — and then
struck the same afternoon at Henri's *"do the three edits"*.  Both sets are
empty, each name red on its own when put back, and the baseline that was
supposed to document a gap lasted about two hours.

**And the batch's own instrument was wrong once.**  `_UNOVERRIDABLE` — F25's
third half, which refuses `infixl 9 ->` — measured 780 green, and the verdict
*ungated* was two minutes from being written.  It is gated:
`test_music_syntax.py::test_the_function_arrow_cannot_be_given_a_fixity`, red
on the mutation, naming neither F24 nor F25.  The file was not in the batch's
37.  **A targeted set is a claim about coverage**, and this one was false; what
caught it was reading the code around the repair rather than trusting the
number the run returned.

**And the batch destroyed three of its own edits.**  The three `spec/syntax.md`
lines had just been written and not committed when a mutation loop put a defect
back into that same file and restored with `git checkout -- spec/syntax.md`.
That restores from HEAD, so it took the three edits with it, and the loop moved
on.  It surfaced because the next run failed *two* tests where one was expected
and the second made no sense — a number that did not add up, not a check
watching for it.  The rule the sweep had been following all along — the tree is
clean before and after every mutation — stops holding the moment a batch starts
*writing* into a file it also wants to mutate, which is what a batch does as
soon as it finds something.  Written down as
[[restore-a-mutation-from-memory]]; the measurement was redone with the
original held in the process that made it.

**F31 is held by nothing and cannot cheaply be gated either.**  The span
dropped from `TApp` in `Subst.apply`: 780 green.  `apply` returns `t` itself
when neither part changed, so the repaired line runs only on a rebuild, and no
program could be constructed in which it decides a message — not even with the
upstream cut repaired.  That cut is **F192**: `_apply_subst_map` rebuilds
`TFun` carrying its span and `TApp` carrying nothing, three lines apart.  A
type the author wrote loses its position at instantiation, which is the
severance F31 was opened for, in the sibling its fix did not reach.  Left
unrepaired on purpose: the position it recovers is in the *callee's* signature,
so a complaint about one definition would be drawn under another's line, and
that is a design question rather than a typo.

**F39 was half a gate and is whole.**  `ExL` struck from the kind table takes
136 of 780 down — `gestate/signal.ges` opens with `mkSig : ExL a -> ExL (Sig
a)`.  `FaL` struck takes nothing, because the kind table is consulted only for
a type somebody *wrote*, and inference builds a `FaL` for every `delay` while
no source in the tree ever names one.  Four lines now do.

**And one more instrument reporting success from behind a wall.**
`python tools/memoryindex.py && python -m pytest …` — one ordinary command —
prints *"no index … nothing to do here"* and exits 0, because
`tools/fence-hook.sh` fences the whole line and the fence puts a tmpfs over
`$HOME`.  The same command on its own writes 71 hooks.  `test_memoryindex.py`
skips under exactly the same conditions, so it has never run where tests run.
**F194**, and it is F185's shape a second time: a green that has only ever been
unfenced, with the tool and its gate going quiet in the same direction.  Not
fixed — the three candidate fixes each break something, and naming them is what
the entry hands on.

No uncertain verdict; the trip-wire did not fire.

## The window a page carries, and the three pieces with no hands — 2026-09-01

*`card:online.md`, piece B2.  Henri: "could we work on the card:online.md
to get more of gestate online?" — and, given four readings of what
*more* meant, **the pieces left out**.*

Forty-five of the tree's fifty-three examples had pages; eight were
refused with one sentence — *a page carries a score baked to its end*.
That sentence was one word too wide.  The terminal does not refuse an
endless score: `unfolding_names` routes it to `audioperform.dynamic`
and it asks *how long*, which is what `--seconds` is for.  A page has
nobody to ask, so it answers itself — **thirty seconds**, the number
`online._control` already gave a synth with no score at all — and
forces the performer quantum by quantum for that long, writing down
the changes it made.  Nothing new computes the sound; the same bake
loop reads a `from_performer` source instead of a `from_schedule` one.

**The measurement came before the build**, which is what made the
answer small.  All eight bake in 2.0–3.8 s of Python per twenty
seconds of audio.  Two independent forcings at one seed agree
change-for-change on every one — the property the whole gate rests on,
because the page's changes are forced at generate time and the
comparison forces them again for `run_native`.  `test_online.py` now
carries `lantern.ges` beside `twinkle`, bit-identical through the
page's own worklet in a headless Chrome; the other four
(`moods`, `nightdrive`, `spiral`, `undertow`) were walked once by hand
through the same helper, identical in 9 to 31 seconds each, and left
out of the suite rather than paying two minutes a run for a property
one endless piece already holds.

**And three of the eight were never about unfolding.**  Baking twenty
seconds of `arpeggiator.ges` gave forty changes for forty slots —
every one an initial value, nothing after t=0.  It is a `hear
holds.keys` piece, and *empty hands are silence* is its own design
decision, written into its header at every level: no idle figure, no
fallback pitch.  So the page was about to serve thirty seconds of
nothing and call it a piece.  `jazz` and `ladder` are the same shape.
They stay out, with the true reason in the refusal — and the detector
is `audioscore.heard_banks`, `assigned_banks` read the other way
round: parsed declarations reachable from `score`, never text.  It
names exactly the three the silent bakes found, which is the same
claim arriving from two directions.

The number is **50 pages** where there were 45, 2.9 MB, 3 m 34 s to
generate the site.  What a person meets is one line of the page's own
face: *this score unfolds forever (cycle); the page carries the first
30.0 s of it.*  Without that, a piece that stops at thirty seconds
reads as a bug rather than as a window — and the window is the
honest thing, since the piece really does go on.

**What was not done, and by whose call.**  Four readings of "more
online" were offered with what would kill each; he picked the pieces.
Saving to a file the person chooses (question 5, answered and unbuilt),
the second emitter (C1, measured and his to weigh) and a keyboard in
the tab — the thing the three refused pieces actually want — are all
still where they were.


## The tail of the sweep is unreconstructable — batch 11, 2026-09-02

Batch 11 of `card:ungated-fixes.md` — F21 F20 F19 F18 F17, the FRP
scheduler, the Wednesday it was due — took the five entries as **13
mutations**, because three of them repaired more than one site and one
mutation per entry would have hidden which half was held.  542 tests
across 16 files behind each `none`.

**The thing that turned up first was not about any entry.**  All five
repairs are already present at `b049e0c`, the initial commit: they were
fixed before this repository existed, so git cannot return the original
defective code for any of them, and every mutation in this batch is a
**reconstruction from the entry's own prose**.  F15, in Thursday's
batch, is the same.  The card had predicted the tail would be *easier*
— older entries, early compiler era.  What it actually is, is
unreconstructable, which is a weaker kind of evidence and had to be
written into every `gate:` line rather than discovered again on Friday.

**F20 had been read past on a parenthetical that expired.**  The entry
says its branch is *"dead code today (F14)"* — and F14 has been
`[resolved]` since before the file was split, its own text listing
`map`, `mkSig`, `sample`, `switch` and `filter` coming back into reach.
Making `_apply` raise on entry takes **61 of 281** reactive tests red.
It is one of the hottest paths in the suite, and a fortnight of sessions
had read *dead code* and moved on.  Corrected in place and struck rather
than deleted, so the reason it went ungated stays readable.

Reaching for its gate produced **F195**.  The narrow claim is true and
is now held: a `GmError` in the sub-evaluation leaves `code`, `stack`
and `dump` exactly as they were — the scratch state doing its job.  One
level up nothing holds.  `reactive_step` empties `gm.now` and refills it
as the sweep goes, so an injected failure leaves `now = 0`, and **every
instant after that runs, raises nothing and does nothing**.  A host
would see silence and no error.  `spec/frp.md` models the step as a
function and `react = scanl reactiveStep`; a fold that raises does not
destroy its input.  Second time this sweep that hunting one entry's gate
found its sibling — F31 gave F192 the same way.

**Two `partial`s, and both are one rule with several readers, only one
of them held.**  F18's ✓ frontier is read by `head`, `watch` and `tail`;
only `head` had a test.  F17's invariant has a comparison and a snapshot
that feeds it, and
`test_ticked_cl_invariant_is_checked_every_step` **injects
`reactive.clocks` by hand** and calls `_update_one` directly — so it
holds the comparison and never walks the snapshot.  Stop taking the
snapshot and the invariant silently stops being asked, with all 542
green including that test.  Its own docstring says the other traces
*"therefore all assert the fig. 10 invariant as a side effect"*, true
exactly as long as the snapshot runs, and held by nothing.  A check
starved of its input is F189's shape, arriving in the language instead
of the tooling.  Four gates written; F19 was gated all along and had
never said so, the fourth of that shape in this sweep.

**And the batch cost a near miss that became the instrument.**  A helper
script `import`ed the sweep script, whose body ran at module level, so
the whole thirteen-mutation run started a second time; killing it left
`gestate/reactive.py` holding F21c's defect in the working tree, caught
by the next `git status`.  A `git commit -a` in that window would have
put a deliberate bug in the tree under an innocent message.  The restore
was in a `finally`, which covers an exception and does not cover a
signal.

Henri: *"card worthy issue, or even a defect."*  It was neither — no
implementation disagrees with a spec, and the decision it belongs to
already had a home in the card's own §"Live tree or a copy", where he
chose the live tree on 2026-08-26 without this failure mode on the
table.  What it was, was a missing instrument that nine batches had each
rebuilt by hand.  So `tools/mutate.py`, per the standing rule that a
missing capability is built the moment the need arises: the restore made
four ways and **verified by hash**, an occurrence count on every edit so
a missed anchor is refused rather than passing green, and a refusal to
start on a file somebody else has modified.  Tested by being killed —
mutation on disk, `kill -TERM`, exit 143, file back byte-for-byte.  Its
`--check` caught a live mutation the first time it ran.

## The sweep closes, and the last entry it read was lying — batch 13, 2026-09-04

**F6 and F1, the two oldest entries in `fixme.md`, on the Friday the schedule
gave them, and that is all sixty-two.**  Thirteen batches, 19 August to 4
September, five a session capped, no day doubled to make up a miss.  Every
repair in the working set now carries a `gate:` line saying either the
instrument that fires if the defect comes back or the honest reason there
isn't one.

Both of today's are gated.  The batch's finding is not in a verdict.

**F6 said it had been fixed in the spec, and it had not.**  The entry opened
*"Fixed in both spec and implementation"*; `spec/data.md` §I.5 still
prescribed `eq dx' ⊥`, the convergence test the thesis says loops forever on
the shape every Datalog query has.  And `errata.md` D2, under a **resolved**
heading, still ended with the sentence that gives the game away: *"`spec/data.md`
§I.5 should be amended to the thesis's test."*  Both had stood a fortnight.

Batch 9 found this shape once at F43 and batch 12 twice at F10 and F13 — a
`[resolved]` marker over a body describing an open defect.  Today is its
sharpest form: **a resolution that names its own outstanding half.**  Nothing
was hidden, nothing was wrong in the prose, and the file still told a reader
the work was done, because the marker is what a reader trusts and the body is
what a reader acts on.  §I.5 is amended with the original kept below it, D2
and F6 are corrected in place and dated, and the two texts are now held
against each other by a test — a citation check, and its gate line says so.

**And the measurement had to be built twice, which is the other lesson.**
The first reconstruction of F6's defect — the convergence test written back
as `eq dx ⊥` by hand — produced 13 red.  They were the wrong 13: at
`Set (Cyclic 8)` the generated `eq_` takes the modulus, so the hand-built term
was under-applied, and the failures were an arity artefact with nothing to say
about convergence.  Rebuilt through the helper the loop already calls
(`subset dx ⊥`), it is 6 red; with change minimization taken out as well — the
loop exactly as it stood the day the first Datalog query hung — 10 red, one of
them `test_a_datalog_fixed_point_terminates`.  Batch 12 earned *a green is not
yet a gap*; this is its other face.  **A red is not yet a gate.**  Thirteen
confident failures are as easy to produce as a tautological green, and neither
is read correctly without asking what the mutation actually did.

**F1 is `partial`, and its bare half cannot be reached.**  The unbound `_box`
is 38 red.  The per-variable temporary that stops nested unboxes shadowing is
484 green — and a probe raising whenever an unbox is compiled inside another
one never fired across 471 tests.  No program in this tree nests them.  The
entry says that, rather than sending somebody to write a test that can never
go red.

**The sweep also found a canary it had been misreading all along.**
`test_complaints.py::test_the_page_is_not_behind_the_source` renders
`doc/complaints.md` from the sources and compares, and the page carries line
numbers — so **every mutation that changed a file's line count has gone red
for that reason alone, in every batch since the first.**  F1a's 38 is 37.  It
never changed a verdict, because a `none` rests on a green and a green is
unaffected; but it inflated every red this card ever counted, and
`tools/mutate.py` is the place to say so.

## A green is not yet a gap — batch 12, 2026-09-03

Batch 12 of `card:ungated-fixes.md` — F15 F13 F12 F10 F8, the Datafun
back end and the last of the FRP scheduler, the Thursday it was due —
took the five entries as nine mutations and then went back and added
**four probes**, because three of the nine came back green and the
greens turned out not to mean the same thing as each other.

**The rule the sweep has kept since batch 2 is that a named test is not
yet a gate.**  This batch is its mirror.  A `none` verdict rests on a
mutation nothing noticed, and *nothing noticed* has two readings: the
branch ran and no test looked, or the branch never ran at all.  The
first is a gap worth an afternoon; the second is a tautology, and
written down as a `none` it sends the next person to write a test that
can never go red.

F15 is the second kind.  Both halves of its repair put back — the
`TAG_DELAY` case in `ticked`, and `_update_one`'s `gfix cycle` re-mark —
left **396 tests across 16 files** green.  Two probes that *raised* on
entry instead of returning `True` were also 396 green: nothing in the
tree ever puts a delay node where either branch looks.  What makes that
safe is not a gate on the repair at all but a gate on its **premise** —
`test_delay_is_universal_and_a_tail_is_existential`, the `errata.md` R3
rejection, which passes happily with the defect back.  F8's bare half is
the first kind: `_is_user_sc` narrowed to a hardcoded `Set_Int` list is
429 green, and a probe raising on entry took five tests down, so the
line runs and no test asks anything of it.  **Two probes changed a
verdict, and neither entry could have been read correctly without one.**

**F10 is the finding, and it is a whole compiler stage with no
observer.**  `test_seminaive_opt.py` tests every rewrite of the thesis's
fig. 4.1 on a hand-built term, and nothing anywhere asked whether the
pipeline *calls* the pass.  `propagate_bottoms(scs)` taken out of
`pipeline.py`: **429 of 429 green**.  A probe raising whenever the pass
changed anything: **52 red**.  So it fires on a fifth of the set and its
absence is invisible — batch 11's F17 shape, a check starved of its
input, arriving here as a stage nobody watches.  The gate written is a
G-machine step count, 8,966 with the pass against 12,130 without, which
is roughly the 26% thesis §4.2.3 says ϕ/δ alone does not buy.  A step
count is a number that drifts, and the docstring says so: re-measure the
bound, do not raise it, because a bound above 12,130 is this gate
switched off.

**Two entries were marked `[resolved]` over bodies describing open
defects** — F10 and F13, both saying the pass "is absent from the spec
*and* the implementation" while `spec/errata.md` has had D3 down as
resolved and D4 as implemented for months.  Batch 9 found the same shape
at F43 and called it once; twice in one batch says it is a class.  A
`[resolved]` marker and an unedited body is the cheapest way for this
file to lie, because the marker is what a reader trusts and the body is
what a reader acts on.  Corrected in place, dated, the original
diagnosis kept underneath.

**And F12 is a `nothing can` that was worth measuring anyway.**  A stale
copy of the helper generator put back beside the live one: 429 green, as
it must be, because nothing calls it.  The interesting half is what the
nearest instrument does — `tools/covercount.py` moves
`gestate/helpers.py` from 51% to 48%, in a page regenerated by hand that
returns 0 on purpose.  A coverage floor would catch the copy.  Nothing
would catch what the entry actually names, which was an edit landing in
the wrong one of two copies.

## The instrument had no test, and rejected its own documented use

`tools/mutate.py` was written at the end of batch 11, as the answer to a
near miss: a killed harness had left a deliberate bug in the working
tree, and the tool's whole promise is that the tree always comes back.
Batch 12 is the first to use it, and the first thing it did was refuse
the invocation the module's own docstring gives —
`mutate.py spec.json --only F8a -- pytest …`, which argparse cannot
place, an option sitting between an optional positional and an
open-ended one.  **F196.**  Fixed by splitting the command off at the
first bare `--` before argparse sees anything.

The larger half is that the tool had **no test at all**.  Nine batches
of verdicts rest on it now, and the restore was checked once, by hand,
by a session killing it.  That is this card's subject arriving at this
card's instrument, so `test/test_mutate.py` was written the same
morning: the documented invocation, the mutation visible to the command
and gone after it, `--only` selecting one, each mutation starting from
the original rather than from the last, an occurrence count refusing a
missed anchor, a modified file refused outright — and the restore
surviving a `SIGTERM`, checked the way the near miss happened: mutate,
`kill -TERM`, exit −15, file back byte-for-byte.

Verifying F196's own gate needed a copy of the tool, because the live
one refuses to mutate a file that is already modified and the fix had
just modified it.  The refusal working is why the verification was
awkward, which is the right way round.

## The picture crosses — the gallery's day one, 2026-09-03

`card:audiovisual-gallery.md` came off the shelf yesterday on a
condition Henri set in advance, and its day one was named for it: *a
small Rust shim exposing advance one frame, hand me the shapes.*  That
shim is `shell/web`, and it turned out to be smaller than the card
expected, because the thing it wraps was already written.

**Nothing new walks a `Sub`.**  `gestate_panel::canvas::Canvas` is the
loop — arrivals, `reactive_step`, `main`'s cell, walk, display — and
the plugin's window has been turning it since the substrate landed.
Under `--features substrate` the panel's only dependency is `crust`, so
the whole stack crosses to `wasm32` untouched; what a page lacks is not
the walk but a way to *call* it.  So the crate is a seam and not an
implementation: ten C functions and one flat `i32` buffer, and its own
tests read that buffer the way JavaScript will — one cursor, record
lengths implied by kind — because a reader written from the writer's
structs would not catch a layout the page cannot parse.

**All six pieces draw in wasm exactly what `gui.py` draws.**  221 KB,
no imports, and a frame for the heaviest of them — `envelope`, 43
records — is **1.98 ms** against the 8.74 ms the card measured in the
CPython reference it was estimating from.  The card had marked the wasm
number as a bound rather than a measurement and said so; the
measurement came in four times better than the bound.

`test/test_gallery.py` is deliberately end to end: the module built for
the browser's own target, driven under `wasmtime` through nothing but
pointers into its linear memory, and the picture compared with the
reference line for line.  Not against a fixture — `shell/panel/tests/`
already holds those and `test_panel_fixtures.py` pins them to today's
exporter — because a shell checked against a recording of itself agrees
with itself.

**The one thing that went wrong is worth more than the twelve that did
not.**  The first run had four pieces matching and two disagreeing, and
the disagreement was entirely in *channel ids*: every rectangle agreed
and every `hit` line did not.  Both readings were correct.  A channel is
allocated when its declaration is first forced, so forcing the
declarations first gives `cutoff` id 0 and letting the program reach it
gives id 2 — the two-readings problem `export.substrate_of`'s docstring
was written about, arriving in a *test* this time rather than in a
shell.  The test's reference had been assembled beside `gui.py` instead
of being `gui.py`, and the fix was to use `gui.Substrate` itself.  A
reference built by hand from the same parts is not the reference; it is
a second implementation with the same bug available to it.

## The frame clock does not cross — F197

Found reaching for the pulse argument.  `gui._crossing` sends `Tick`'s
tag and the `wallclock` channel, so the editor's canvas has a frame
clock; `export.substrate_of` sends neither, so no canvas abroad has
one.  And no host outside `gui.py` pulses in any case —
`Panel::tick_canvas` calls `Canvas::tick`, which passes `None`, and
`Canvas::step`'s own docstring states the price: *"a host that never
pulses shows a canvas whose faders work and whose animation stands
still."*

**Then the measurement refused to demonstrate it**, which is the part
to keep.  `lantern.ges` folds over `events` and `envelope.ges` reads
`now`, so both were expected to stand still abroad and move at home.
They stand still in **both** — thirty frames of the reference host's own
`tick` and the picture does not change.  So what is broken is the seam,
and its cost is not shown on today's example set; the entry says so, and
says that the first thing to write is a substrate that moves on `Tick`
alone.  A defect with a stated victim that turns out to have none is a
defect written from reading, and this one was three sentences from being
filed that way.


## A card opened from a conversation about Xanadu — 2026-09-04

Henri brought two pages on Project Xanadu, gwern.net/xanadu and
zed.dev/blog/agentic-xanadu, and asked what in the design space could
change how a session works, given that retrieval over embeddings does
not pay.  The answer measured this tree against Nelson's data model
and found it already runs most of it by hand — permanent ids,
never-overwrite, provenance in prose — and lacks one piece: nothing
tells a reader who cites what they are reading.  He opened
`card:backlinks.md` on that sentence.

**Two measurements, both with their command.**  How much of the graph
exists and how many targets no one cites, from a throwaway script over
the citation walker's file set — 258 passage citations over 108
targets, 13 of 72 memory bodies reachable only through the index.  And
the churn a generated foot would cost, which decided Q1: of the
commits since the board began, how many added a citation to a memory
or card, and to how many targets.

```sh
since=2026-08-05
git log --since=$since --format='%h' | while read h; do
  n=$(git show $h --format= --unified=0 -- . ':!doc/memory/README.md' \
      | grep -E '^\+' | grep -vE '^\+\+\+' \
      | grep -oE '\[\[[a-z0-9-]+\]\]|card:[a-z0-9-]+\.md|doc/memory/[a-z0-9-]+\.md' \
      | sort -u | wc -l)
  [ "$n" -gt 0 ] && echo "$h $n"
done | awk '{c++; a[c]=$2} END{print c " commits; median targets " a[int((c+1)/2)]}'
```

128 of 556, median two.  A foot generated into target files would have
been rewritten in a quarter of all commits, in files the work did not
touch, and that number moved the card's default from a generated block
to a hook on the reader's `Read` — the reasoning is on the card under
§"Q1, reasoned", and the part worth keeping is that the default had
been chosen by precedent and reversed on being asked *why*.

**And the size table caught its own case.**  Five lines added to
`board/README.md` for the new card put `doc/method.md` behind by
five, and the gate refused the commit until the number was fixed —
the third time that check has fired on the day it was needed.

## Backlinks, day one — the check came back yes, and the known answers found three defects — 2026-09-04

`card:backlinks.md`'s day one, the same sitting the card was opened in.
The first thing it owed was the check that decided its default: can a
`PostToolUse` hook hand text back into a session's context.  Claude
Code's hook reference says yes for exactly that event —
`hookSpecificOutput.additionalContext` becomes a system message after
the tool response — and says plain stdout is *not* shown there, which
settled the output shape before a line was written.

**Built:** `tools/backlinks.py`, the inverse of `test_citations.py`'s
walk over five citer kinds, cached by size and mtime; `--hook`,
`--check`, `--install`, `--time`.  `test/test_backlinks.py` validates
it the way `tools/dangling.py` is validated, against cases whose answer
is known before the tool runs, and that found three defects in an hour
that reading the code had not: a card counted as its own citer when it
named its own id, one line naming a card by id and by basename came
back twice, and a symlinked directory did not resolve.  The budget was
missed first — the walk ran twice and warmed at up to 179 ms against a
tenth of a second — and met at 20 ms with one scandir pass.

```sh
python tools/backlinks.py --time card:ungated-fixes.md      # cold 2.2 s, warm 20 ms
time (echo '{"tool_name":"Read","tool_input":{"file_path":"'$PWD'/gestate/host.c"}}' \
      | python tools/backlinks.py --hook >/dev/null)         # 76 ms wall
```

**What a session may not do, and did not.**  The install line goes in
`.claude/settings.json`, which the leash denies, so the hook is built,
tested and documented and not installed.  `tools/pre-commit.sh` prints
its state as a lamp — the memory index check beside it is a gate, and
this one is deliberately not, because a red that only Henri can clear
is a red that gets muted.  Three lines, printed by `--install`, are
his.

**And it fired, the same sitting.**  Henri ran the `jq` line, said
*"installed, check it works"*, and the next `Read` — five lines of
`gestate/host.c` — arrived with 58 citers behind it, the card and the
memory the `because` named among the first twenty.  Opened, reasoned,
built, installed and seen working between one breakfast and the next
coffee; the card is in `done/`.  Note the count: 53 when the card was
written that morning, 58 by the time it fired, and the five between are
the card, the instrument section, the memory line and this journal
naming the file — the graph grew while it was being indexed, which is
what a hook computed at read time is for.

## The hook ranks, logs and can trip — 2026-09-04, afternoon

Henri asked three things of the two-hour-old hook: write the potential
fix somewhere, write something that *ensures* the fix happens if the
noise becomes real, and sort the citations, because *"not all
citations are equal."*

**The ranking** is a table, `TIERS`: live cards and memory, the
standing documents, code and tests, shelved cards, the ledger, the
journal — and within a tier a card's header `see` line, then an
explicit citation, then a file named in passing.  Reading `host.c`
now opens with `card:unseen-flare.md`'s `see` line and closes with the
journal, and the cut at twenty falls on the journal.

**The ensuring** is not a note.  Every fire appends epoch, file,
citers and shown to `~/.local/state/gestate/backlinks.log`, the sitting
log's shape; `--check`, which the pre-commit prints at every commit,
trips at thirty fires in fourteen days with a third of them cut, and
when it trips it prints the id of `card:backlinks-ranges.md` and exits
2 without refusing the commit.  So the session that next commits after
the noise arrives is handed the card, and the card is the design.
Nothing depends on anyone remembering — which is the only shape of
*ensure* this tree has ever trusted.

**The fix**, on that card in `later/`: index the cited heading, resolve
it to a line, read the range from the hook's input, and put a citer of
a heading inside the range ahead of every tier.  Shelved on arrival
because building it now would be a session guessing its twenty lines
were noise, and the three lamp numbers are marked as the session's
guess, nobody's measurement.

```sh
python tools/backlinks.py --report          # fires, cut share, most-read files
python tools/backlinks.py --check; echo $?  # 0 quiet, 1 not installed, 2 tripped
```

## The board's flow, made visible — and the seven-day lamp — 2026-09-04, evening

The lean assessment Henri asked for named flow measurement as the
biggest gap, and he answered *"virtauksen mittaaminen todella
voitaisiin tehdä nyt näkyväksi."*  A throwaway script over `git log`
did it in five minutes, and the numbers went into `~/gestate-lean.md`,
his paper outside the tree.

**Two populations.**  Of 22 finished cards, 13 finished the day they
were written and the median lead time is half a day; of 8 open cards,
six had stood past seventeen days.  When arrivals fell after week 33
— his *four fewer, none new* — the drain fell with them, 16 to 2 to
1.  Work comes from what arrives, not from the queue.  And it is the
same shape as his other sentence that evening, about `keeper.md`: *"se
ei motivoi minua tekemään, toisin kuin arkinen pöhinä session kanssa."*
The list pulls nobody; the conversation pulls both.

**The lamp is his, chosen in one line:** *"se voisi olla kortit joihin
ei ole koskettu 7 päivään, niiden pitäisi mennä later/ hyllyyn meidän
kauttamme."*  So `tools/flow.py --check` names every live card whose
own file has not changed in a commit for seven days, exits 2, and the
pre-commit prints it beside the other lamps and refuses nothing —
*through us* means a session brings the cards to him, he says why each
waits, and the session shelves it with his sentence.  The rule is in
`board/README.md` beside the paragraph it makes happen on a clock.

```sh
python tools/flow.py            # lead times, open cards by age and last touch, weekly flow
python tools/flow.py --check    # the lamp; 2 when it trips
```

**It tripped on its first run**, naming five: `git-lesson`,
`reviewing-by-running`, `stranger-test`, `unseen-flare`, `git-viewer`
— nine to nineteen days untouched.  Their sentences are his and the
next thing this sitting asks.  Two memories went in earlier the same
evening: the customer is Henri, and keeper.md does not pull him.

**The five went to the shelf the same evening**, each with his line:
git-lesson *"taitaa olla tarpeeton"* — the board's first card that may
be unneeded rather than waiting, and whether it is deleted is his;
reviewing-by-running *"ehkä se on tend-projektin aluetta"* — a
decision, so debt on the shelf; stranger-test, unseen-flare and
git-viewer wait on events, a person and a crackle.  The live board is
three cards.  And the lamp, asked again, said every open card was
touched within seven days — which is the first time a number on this
board has gone green by somebody answering it rather than by work.

**And the backlinks log answered the question he asked next** —
whether the hook has worked — with one line: it fired once all
evening.  Every other read this session made went through `cat` and
`sed` in the shell, which the hook does not see.  The mechanism works;
the reader it was built for reads another way.  That goes on the
closed card as its first measurement.

## `idiom-or-load` refused, and the fence that could not be built — 2026-09-05

*Written here because `board/README.md` recorded it and should not
have: a card leaving the list is an event, and events are this file's.*

The card asked whether a **loose** brief lands better than a
**constrained** one, and its control was that neither arm may read
`board/`.  The loose arm ran — `examples/audio/hollow.ges`, B locrian,
one pass — and **Henri: *"I think that this unconstrained was better
than constrained version."*** Then he closed the card: *"it's too hard
for me to isolate and restrict everything down to make a good test
here."*  And before that: *"I noticed that asking to not look into
`board/` was insufficient.  You still figured it out this was a test
setting."*

**Neither the arm nor the fence was at fault — the tree reads `board/`
for you.**  `tools/backlinks.py`'s Read hook fires on every file open
and quotes the citing cards back, so opening the log the work required
printed two lines of the card into the arm's context on its second tool
call, one of them containing the words *the two arms*.  Citing a file
is precisely what makes the hook read its cards aloud, so the fence was
unbuildable here without three pieces of setup nobody had budgeted:
`board/` absent from the arm's clone, the hook silenced, and the log's
own leaking section split out.

`board/refused/idiom-or-load.md` keeps the whole argument, and
`doc/notes/notes-on-writing-a-piece.md`'s entry for the next day
carries the measurement — a heading this file cannot cite by §, because
it quotes a section of its own.  The
rule that was missing and is now written: **two arms never in one
working tree.**

## The letter the rule could not guess — 2026-09-06

*Henri, opening the sitting:* **"We could look into implementing the
card:drawn-scores.md but recall what I shown yesterday (oscillseq,
beet, mide) to take some lessons from there."*

The lessons were shown on 2026-09-05 and written down as
`doc/memory/henri-prior-tools.md` — three of his own tools, and four
things in them that answer questions open here.  **Item 1 answered one
outright**, and the tree turned out to have the case for it already.

`spec/drawnscores.md` §"The three spellings" had a trigger written into
it: where two spellings cost one accidental each, the rule takes the
flat, and *"a piece that needs the other is the case that would put
names in the file"*.  Nobody had looked for one.  Looking took a
minute:

    python -c "from gestate import notes; print(notes.spell(73,'D','phrygian'), notes.degree_of(73,'D','phrygian'))"
    des5 7

That is `arc.notes`' **last bar** — `73 → 69 → 62` in D phrygian, a
leading tone resolving up to the tonic, which is a C♯ and cannot be a
D♭.  The report had been printing both columns side by side and they
disagreed about that note, at the cadence, on the only `.notes` file
there is.  Three notes of 291 are in that position; the other two are a
held C♯ under bar 7 resolving the same way, and a bass walking A–E–B–F♯
where G♭ would break the chain of fifths.

**And the answer was his, from before this project.**  In `oscillseq` a
musical pitch is a `(pitch, accidental)` pair held *beside* the MIDI
number rather than derived from it, because a rule cannot know where the
line is going and a stored accidental does not have to.  So the note
record gained an optional `spell`, written only where the rule has to
guess and guesses wrong: 3 lines of 291 carry one, 288 are derived
exactly as before, and the rule is untouched.

**What made it safe to store a thing that can disagree** — which is what
this project has twice designed against, so it is worth the three
sentences.  A file may choose the **letter** and may not choose the
**note**: `spell des5` beside `key 60` will not load, by one rule that
the parser and the record both call.  It is per note and not per file,
which the shipped file proves in its own bytes — key 61 is `des4` in
section B and `cis4` in section C, G locrian's flattened fifth and D
phrygian's leading tone, one pitch and two notes.  And a drag in pitch
**drops** it and says so, because the letter was an intention about the
pitch that was; a drag in time, velocity or manner keeps it.

**What the other three tools say, recorded rather than acted on**, since
the rest of this card is rung 5 and that is a decision:

* `oscillseq` is driven by a command language in a textbox, and
  **everything has a command under it** — a mouse gesture *associates
  to* a command rather than being a second path beside them.  That is a
  requirement on rung 5 rather than an argument against it: a view is a
  set of bindings.  *(This paragraph first said "mouse gestures in the
  minority", which Henri corrected the same day — that is a claim about
  how much the mouse is used, and the property is about what a gesture
  is made of.  The wrong version had been used here as an argument
  against building rung 5 at all.)*
* `mide` writes its UI as datalog — `draggable (note K) :- order K
  Onset 1.` — which is a wholly different answer to the problem
  `furniture.rs` solves, and rung 5's named cost is exactly that file
  plus `window.rs` plus the verb table.
* `xylem`'s Knuth–Plass line breaker is rung 5's other hard half:
  stacking sections and voices into a window is line breaking.
* And **playback as states** — OFFLINE / ONLINE / FABRIC / PLAYING — is
  the missing name for the decision `spec/drawnscores.md` says rung 5
  will owe: a preview tone with the transport stopped.

*The card is `card:drawn-scores.md`; the contract is
`spec/drawnscores.md` §"The spelling a rule cannot guess".*

## The prose the format could not hold — F200, and the tonic it could not spell — 2026-09-06

*Henri, after the spelling slice:* **"F200 could be tackled."**

**F200 was that `notes.write()` deleted every comment in a `.notes`
file.**  It had been filed rather than fixed, with two candidate repairs
and a preference between them: *"a `#` line owned by the (section, bar)
it precedes, or a trailing field on the note record itself — and the
second is the one that survives reflow, which is gate three."*

**The count refused the preferred one.**  `arc.ges` — the piece this
format replaces, and the reason the defect matters — carries **169
whole-line comments and 0 trailing ones**.  A trailing field would have
survived reflow and held none of the prose the defect is about.  The
preference had been reasoned from a property, and one command said what
was actually there.

**What landed is one rule covering both shapes.**  A comment belongs to
the **record below it**, or to the record it shares a line with — which
is how a doc comment attaches in every language, and it means the prose
names its owner instead of depending on a position.  F200's other worry
— *a section comment jumps when a note is dragged* — does not arise,
because a remark about a section belongs to the `section` record and
that record never moves.

**The limit is stated rather than discovered**, and tested: a remark
written above the first note of a *bar* belongs to that note, and a drag
takes it along.  There is no bar record for it to belong to, and the
spec refuses to invent one.

### And it could not be written until F203 was found

Deciding where a comment *starts* turned up a defect that had been
there since the parser was written.  `#` opened a comment anywhere, and
five of the seventeen tonics `_PITCH_CLASS` offers end in a sharp:

    section A  key C#  mode lydian  bars 8  beats 4  voices melody
    -> sharp.notes:1: missing `bars`, `beats`, `voices`

**C♯, D♯, F♯, G♯ and A♯ were unwritable**, and the refusal blamed the
author for the three fields it had just swallowed — the worst shape an
error message can have, in the one file whose whole discipline is that
a complaint names a place a person can look at.

Nothing caught it because the only `.notes` file in the tree is in D, G
and D, and every handwritten fixture omits `key` or uses a natural.
`doc/memory/a-targeted-set-is-a-claim.md` again, and it turned up the
same way twice in one day.

The rule now: **a `#` opens a comment where a token could start** — line
start, or after whitespace.  Every value in this format is one `\S+`
token, so `key C#  # a real comment` reads as both and nothing is lost.

### And the fixture was given the thing the property is about

`arc.notes` was generated and carried no comment, which is *why* F200
went unnoticed: the only file in the tree had nothing to lose.  It
carries seven now — a header, and a remark beside each of the three
notes whose letter the spelling rule could not guess, each saying why
that letter.  A round trip gives all seven back, and that is a gate.

*`fixme.md` F200 and F203; the contract is `spec/drawnscores.md` §"The
prose belongs to the record below it".*

## Standing questions, and what the memories rest on — 2026-09-06

Two projects out of one Sunday-morning page.  `doc/notes/notes-on-cues.md`
had ended with three things that could be built and four questions to
be asking; Henri's instruction on reading it was *"initiate some
projects today"*, then *"Do cards for these, and implement standing
questions immediately, but come up with some good standing questions
and let me choose among them"*, then, mid-turn, *"and do the
measurement as well."*

### The three buildable things, measured before any card

The page's coverage map mostly existed: a walk from `CLAUDE.md` over
every `.md` reference reaches 191 of 241 pages, and the 50 it misses
are the three shelves (reached by `ls` on purpose), seven driven-run
reports, and four READMEs nothing links.  The retrieval index existed
too — `tools/backlinks.py --report`, 172 fires in fourteen days.  The
third, a stored question that lands at a moment, existed nowhere.  So
one card, not three.

### `tools/standing.py`, and the questions Henri has not chosen yet

The third hook of the backlinks shape: `--hook` on `Read|Bash`,
borrowing `read_targets` outright, once per card per sitting, three
questions at most.  The questions are `board/standing.md`, a heading
per shelf; twelve candidates sit under `## proposed`, each with the
lesson it was turned around from, and nothing fires until he moves
one up.  `test/test_standing.py`, sixteen cases on a small tree, and
the one that reads this tree's file is gate nineteen.  The install
line is his, as for the two hooks before.

### `doc/testimony.md` — eighty memories, four kinds

The inventory the cues page called *still unrun*: of each memory,
what does its load-bearing claim rest on?  Read in one morning, one
row each: **22 harness, 38 henri, 14 session, 6 argument.**  Sixty of
eighty rest on something a reader can check without trusting a
session.  The fourteen that rest on a session's word are the product —
a second table names the measurement or the sentence that would move
each — and the classifier is inside the count, said on the page.
`tools/testimony.py` holds the table to the directory; a memory with
no row is printed, not refused, which was the card's own default.

### And the grep that said *in neither tree*

The cues page quotes a SimpleQA run.  A grep of both trees for the
word returned nothing, and the closing section said so; Henri pointed
at `~/tend/doc/benchmark-simpleqa-2026-08-31.md` within the hour, and
the same grep re-run found it.  Why the first returned nothing is not
known.  `doc/memory/dont-conclude-from-a-shallow-check.md`, on the
page whose subject is retrieval, and it is now the first candidate
standing question's own example.

### The source, corrected within the hour

Henri chose — *"Your proposals are good, pick those"* — and brought a
guest session's reading of the design: a session inventing its own
cue invents it from the context that produced its answer, so it asks
what it can already answer and calls that diligence.  Keep the idea,
change the source: questions come from him or are harvested in
hindsight at the close of a card, and answering is never mandatory.
Taken the same morning — the hook line carries *consider; act if it
changes anything; say nothing if it does not*, and `standing --check`
at every commit that moves a card to `done/` asks *what question
would have helped at the start of this?*  Five questions stand; the
seven not chosen wait for the fire, which is the guest's other note:
this is fire material, and it was built at 07:11.  The hook was
installed on his side before the choosing was reported.

*Cards: `card:standing-questions.md` (doing — live, and judged by its
log from here), `card:testimony-inventory.md` (done).*

## Rung 5, the seam that did not move, and the rail — 2026-09-06

`card:drawn-scores.md` had one thing left, the view that takes the
window, priced as a new furniture kind across the three seams that
lost `touch`.  Henri chose it over the cheaper box-beside-the-line,
on the condition that the seam be talked through first.

### The ping-pong

One round each.  The session's: coordinates never cross the wire and
meanings do, the roll already crosses as a picture the window
hit-tests off its own walk, `Ctrl-Tab` already shows a file's own
picture whole, and `onTouchX` stands beside `onTouchY` — so none of
the three seams needs to move, and the one real fork is height.  His,
verbatim on the card: plugin-like and reusable, commands generated for
mouse gestures, a vertical scroll, a `selected` channel, grid snap, a
piano-like default voice.  *Plugin-like* was the word that scoped it,
and it went back as three readings with a default; he took the first —
a file kind is a registration, not a branch.

### The pad that was not there

The first slice was to be the same code under every reading: the
selection, `onTouchX` on each note, the snap, `move`.  Measured before
building: a press writes exactly one attachment, the deepest containing
it, in both machines.  `spec/substrate.md` says *a pad is two on one
element*; a program written that way writes `cy` and never `cx`.
**F204.**  The walk is the parity seam and the day's contract was that
no seam moves, so the roll grew a rail instead — one `TouchX` strip
along its top, recorded before the columns so it wins where they reach
over it.  Press a note, drag the rail.

### The number

On `arc.notes`, `A.melody`: grid 96, a drag of one step changes one
line, its `at` field, and the transcript says `move`.  Ten tests.
Nothing sounds yet with the transport stopped; that is the next slice,
with the piano-like voice.

### The second slice — heard, and a piano lent

Henri took (a) for the voice: chopin's hammer carried verbatim by a
generated wrapper, no library word.  A committing drag with the
transport stopped now plays from the note, the road the mark gesture
opened, and `move` plays from where the note went.  `notes.wrapper`
plays every one of `arc.notes`' 291 notes through five hammer banks,
held by four tests, and is not yet what the window opens — the file
kind is the next slice, and it is a registration.

### The third slice — a registration, not a branch

`audioeditor.KINDS`: a row per suffix saying how the file builds and
what its page is, `.notes` the first.  Opening `arc.notes` alone now
builds the wrapper over the window's own buffer, stacks the three
sections into the file's own picture for `Ctrl-Tab`, and routes a drag
into the buffer rather than the disk, so the note file is edited the
way a `.ges` is — undo, `Ctrl-S`.  Four tests.  Rung 5 has one thing
left, the scroll.

### The fourth slice — the scroll, and the window driven

One number in the window and a wheel that moves it; the pure
arithmetic in `view.rs` with four tests.  Then the real window on
`Xvfb :99`, `arc.notes` opened alone, the window shrunk under the
page.  The first photograph showed no page at all: the status bar
said *`env` is not a record* at line 7 of `arc.notes` — the wrapper
had been handed back in as the file and expanded twice.  The second
showed the text still: the canvas command's guard asked the program
for a `substrate` and a `.notes` declares none.  The third showed the
page centred with its first section cut, so a page opens at its top
now.  The last shows it opening at the top, moving under the wheel,
and coming back to the pixel.  Six runs, four kept as evidence, two
defects fixed and one filed (F205: 88 s to a page in two runs, 2 s in
two others, the same script — and the first suspected cause falsified
by the last run before it was an hour old).  `doc/memory/test-what-a-person-would-do.md`
again, and the harness it names is the one that found all three.

## A different league — `card:notes-editor.md` — 2026-09-06

Henri put three screenshots side by side, Reaper's MIDI editor, this
roll, Reaper's score view: *"There's visual differences and that's
okay, but they're in different league.  Reaper note movement reacts
immediately and I can hear the change immediately."*  Measured within
the hour: a moved note took 5.0 s to redraw and 5.3 s to hear here,
and the file itself parses in 10 ms.  The league is structural — the
format made the notes data on disk and the expansion handed them back
to the compiler as source.  He answered the three questions in one
line — the data path first; his list of tools; the score view later,
*"pie in the sky"* — and the card was written from his sentences.

### Slice 1 the same hour

The roll read off the parsed file: 93 ms for the page against 6.2 s,
the same `Roll` leaf for leaf.  The parity test disagreed with the
compiled road on every velocity and manner, and the file settled it:
the compiled road reads a note-file note as a bare key, so an accent
written in `arc.notes` never drew its mark — F206.  What is left of a
redraw is the picture's own compile, 3.0 s, and that is the next
slice's number.

### Slice 2 — the engine once, the notes as records

The breakdown of a one-note audition was the answer: the language
front end ran twice over the nine hundred generated lines, four
seconds each, and the instrument was a few dozen of them.  So the
engine now compiles the wrapper's synth half — byte-identical across
note edits, kept rather than rebuilt — and the notes reach the
performer as records baked off the parsed file, held to
`perform_voices` event for event.  The score is loaded before the
picture.  Measured with the instrument running on a muted card: the
moved note's score installed **0.6 s** after the audition, from 6.3.
The picture's own compile is what remains, 3 s, and it is the next
slice.  On the way: F207, the expander declares `Voice` from the banks
a score assigns to, so a score that assigns none fails at a prelude
line — the engine half rests on every bank instead.

### Slice 3 — the roll compiled once

The last of the day, at Henri's *"still one slice, then I declare
done for today."*  The picture's program names no note now: the rows
arrive as a `List Float` reading, the way a scope's trace does, so the
text holds still while notes move and the front end's cache answers
it.  The columns tile the roll whether or not a note is under them,
and the scale is the file's.  Rectangle for rectangle the same picture
as the baked road.  Measured with the instrument running: one moved
note, the audition done in 1.1 s, from 6.3 s this morning and 3.6 s
after slice 2; the note audible at 0.6 s.  What remains is
bookkeeping in Python, not a compile.

## The editing scale — the second sitting, 2026-09-06

Henri came back for a second sitting: *"continue the drawn-scores..
make it more like what it's supposed to be."*  Short on purpose, so the
session went and looked before asking: the notes-editor card says what
it is supposed to be, and the two photographs beside each other said
where the gap was — his roll a 384 by 116 box in the middle of the
window with three-pixel notes, Reaper's filling the window with keys,
a ruler and a grid.

### Two scales, one arithmetic

The postcondition first, naming no function: *a person opening a
`.notes` sees each section at a size where a note can be taken by the
hand, with the keys named down the side and the bars numbered along
the top.*  Then a `Geometry` on the `Roll` — the box, three margins,
how tall a note is — read by the same `y_of`/`x_of` that draw and the
same `key_at`/`tick_at` that read back.  The compact box was
snapshotted on four files before a line changed and held item-identical
after, hands included, which is how the `.ges` score box got through
the day untouched.  The `.notes` page got eight pixels a semitone,
thirty-two a beat, a keyboard, a ruler that is the rail, beat and bar
lines, stripes, and its section's name for a caption.

### What was found on the way

The hands were a chain of `Over`s bounded at 48 because chopin's notes
had once overflowed the parser; a page at editing scale wants 128
columns.  Folded balanced, the same order, depth eight — and a test
that presses every note's own rectangle on the reference walk and gets
that note back.  And a roll asked for two sections had been drawing
both from tick 0 while summing the span; the page never showed it
because it asks one section a roll.  Fixed with the bars.

### Driven

The real window on `Xvfb :99`, 27 s wall: the page 2 s after
`Ctrl-Tab`, a whole-bar `upper` note found by reading the reference
walk and the page's ground off the photograph, carried three semitones
with the picture following, dropped — the piano played from there
through the sound card — and `Ctrl-S` changed one line of the copy,
`key 57` to `key 60`.  The photograph also showed the status row
painting two fields over each other, F208.  One decision went to Henri
at the start with a default and is still his: F204, both axes in one
drag, by repairing the walk.

## One hand, both axes — F204 repaired, 2026-09-06

*"go with the default, repair the walk."*  The walk in both machines:
a press grabs the deepest attachment containing the point and every
attachment around it, innermost first, read off the hit table as a
later attachment whose region holds the grabbed one's.  Four cases in
Rust, the six-line pad in Python writing `cy` and `cx` from one press.
The roll's columns went inside a body-wide `TouchX`, so the press that
takes a note also takes the body, and the rail became a ruler.  The
model holds two grabs and commits both at the first `released`.

### The window said no, twice

Headless, every test was green.  Driven, the key moved and the tick
did not — twice, the second run confounded by a palette left open.
Not the walk: the door.  A replacement through `ged_set_text` lands on
the window's next frame and `ged_text` reads what the window last
published, so `move` wrote, `transpose` read the text from before it,
and the last write won.  No headless view can show that, because every
one of them is synchronous.  The view answers its own replacement now
until the document has taken it, held by a test whose editor lands a
frame late — and the third run changed one line in both fields.

Two lessons paid for.  A timing test in the suite failed while a cargo
build ran beside it and passed alone in six seconds: the machine is
shared, and I was the load.  And a session log is written by the
`transcript` command, not on quit — two runs went to learning that,
and the transcript never did come; the bench reproduced the drop
instead, with the real audition wired in, and it was green there too,
which is what pointed at the door.

## Select several, carry them as one — 2026-09-06

*"take the next slice, multi-select and move as a group."*  Two
commands, `select` and `carry`, and two list readings the picture
folds over, the group and the band; nothing new on the wire.  The
first headless sweep selected nothing, because it never started: a
column is the roll's whole height and a press anywhere in one took the
nearest note, so empty roll existed only where a column was empty —
almost nowhere on a page of five voices.  `BAND_REACH`, three
semitones, is the rule that was missing.  The second sweep took six
notes; the first carry was refused whole because the melody's last
note would have landed on bar 2's first, which is the file's rule
arriving at the gesture, and the third carried six lines by two
semitones in one rewrite.  On the window, first time: a band swept over bar 1, six
outlines, the group carried up two, six lines changed by two.  The
compact box's own tests had pressed mid-column and meant the nearest
note at any distance; they press on a note now, which is what a hand
does.

## A note resized by its end — 2026-09-06

*"take the next slice, resize a note and the selection."*  The hands
were already there: a press in a note's last column means its end,
the body's hand carries the end along, and the release runs `resize`
or, for a group, `stretch`.  The picture grows the held selection
from its start by a reading in pixels.  Headless first time: the
whole-bar note back a beat, six lines of a group along a beat.  On the window, first time too: shorter before the
drop, `384` to `288`; six ends along a beat, seven lines.  The
lookup test's bound tripped again inside the full-file run, 1.5 s
against a lookup measured in a process that had just run 180 tests;
still left as it is.

## The section resized on its ruler — 2026-09-06

*"take the next slice, resize the section."*  The ruler had been a
drawing since the sixth slice retired the rail; it is the section's
handle now, a `TouchX` recorded before the body so it wins where the
columns reach under it, and a hand on it carries the section's end by
whole bars.  `bars` rewrites the section record's one field; a
section grows freely and shrinks only past empty bars.  The compact
box stays item-identical, having no section.  On the window, first time: one line, `bars 8` to
`bars 9` — and, six seconds after the drop, a blank canvas saying
*8.8 s to open*: a grown section is a new program text, and the page
was not photographed rebuilt.  I first wrote that the photograph
showed the nine-bar section cut at the window's edge; it did not, and
the cut is arithmetic — 1182 pixels in 1100 — until a longer run
looks.  The horizontal scroll the editing scale deferred is what that
arithmetic asks for.

## The tapped tempo — 2026-09-06

*"take the next slice, the tapped tempo."*  The format gained its
one file-level record, `bpm`, exactly as Henri had answered Q2 on the
card two sittings ago — read by the wrapper and the records road for a
`.notes` played alone, ignored by an including `.ges`.  `tap` on
`Ctrl-T` averages a run of taps; `tempo` writes the number, into the
`.ges` literal or the `.notes` record, and is the half a transcript
replays exactly.  The bench had been playing a lone `.notes` at a
constant since slice 2 of this card; it plays at the file's tempo
now.  Slice 4 of `card:notes-editor.md` — his list of tools — is
built whole.  On the window, the first run read four taps at 120 as
102 — the write auditioned synchronously, and a changed `bpm` is a
changed engine, so the rebuild held the model's thread through the
next tap's stamp.  The typing road's coalesced audition, on its own
thread after the hand stops, is the door; through it the same taps
read 121.  A clock is only as honest as the thread it is read on.

## The picture computed, not written — 2026-09-06, evening

Henri asked how the GUI work had gone, and whether it was laborious,
and the honest answer named the page's text at eighty thousand
characters.  He asked for an abstraction, took the evening's list, and
said the G-machine computing the furniture would be a little better
than Python writing it.  It was: the furniture, ruler and columns are
recursion over a few numbers now, held item-for-item to the unrolled
picture and hit table, the text down to fifty-one thousand and the
compile from 4.4 to 1.75 s.  Two things learned on the way: a constant
subexpression inside the picture function is rebuilt at every
application, so the ground and the hands went to the top level; and
the drag's frame was never the furniture — it is the reference walk
over the items, the same eighty milliseconds before and after.

## The roll's vocabulary is a library — 2026-09-06, evening

*"Tehdään sitten se idea 2, moduuli."*  `roll.ges`, in front of a
page's program after `gui.ges` whenever the program declares a
`Body`; the staged front end caches it as one more head.  The page's
text went from fifty-one thousand characters to thirty-two, the warm
compile to one second, and the picture and the hit table stayed
item-identical to the morning's unrolled program — held by the same
harness that held the first halving.  What remains in the text is
the channels, one a column, and that is the evening's third idea,
which touches the wire's rule and is Henri's to decide.

## The body is one pad — 2026-09-06, evening

*"Tehdään myös idea 3, yksi käsi koko rungon yli.  Jos se yhä
kuulostaa järkevältä sinun mielestäsi."*  It did: the substrate spec
had said a pad was two touches on one element since before the roll
existed, and the columns were the workaround for its not being true.
The body is that pad now, the rail inner so its press is read first
and the pitch hand's press finds the note at the tick it holds.  Three
hands a box where there were a hundred and thirty, the page's program
at eight thousand characters from the morning's eighty-five, and the
three commands that named a note by its column name it by its tick.
Both pictures item-identical.  The tests were where the columns
lived: every press in them had aimed at a column, and every one aims
at a place now.

## The model before the code — `card:transport-modes.md`, 2026-09-07

Henri asked, before reading the GUI card, whether there is a taxonomy
or a modelling language for models, and what gestate's model is aside
the rope; the answer became a section of `card:gui-is-difficult.md`
and a recommendation — sentences to say it, a type to write it,
invariants to check it, a statechart for the gestures — that he
accepted on condition it was tried somewhere small first.  The
somewhere was the transport, whose card he had written the same hour:
*"we need separate modes for synthetizer being on, and for when it's
playing score."*  Measured, neither mode existed; a program file takes
the card on open and stopped is silence for the keyboard too.

So the trial: `spec/transport.md`, the three modes in four spellings,
`gestate/transportmode.py` the type, and a test that walks all thirty
steps and holds the spec's constructors to the enum's.  The languages
earned their keep in one way I had not expected: writing the eight
sentences forced five decisions the two-state transport never had to
make — where `stop` lands from silent, whether `play` from silent is
one word, what `audition` means without an engine, that the keyboard
is a conjunction of two axes, that `inert` is a fixed mode and not a
fourth.  None of them was in the `because`.  What the languages did
not do is say whether *sounding* is the right name.  His concern that
the transport is not an isolated case turned into the spec's own
section: the model names the engine, the card, the clock, the
keyboard's switch and the rebuild, and owns none of them.  Alloy
itself was not run and will not be; the enumeration is the check.

## The three modes, landed — 2026-09-07

*"This looks good.  do the next slice."*  The model went into the
transport the same afternoon it was written, and the one thing the
model had not said turned out to be the whole of the engineering: a
key is stamped against the engine's own clock, the first word of its
state, and a *sounding* transport holds the score's position while
that clock runs on — so the two numbers that had always been one had
to be two, in C and in Python, and re-synced by a seek when play
resumes.  Without that a key pressed while sounding arrived with its
attack already spent.  The first test subject, the arpeggiator, was
the wrong one — its lead is played by the performer, which reads the
held position, so *sounding* rightly plays nothing on it; duet's lead
handed to the keyboard is the case the card meant.

Two corrections along the way.  The model had said a file opens
*sounding*; it opens *playing*, as it always has and as a test already
said in words, and the spec now says the session misread the card.
And the atlas's wire check read my Rust `match` on the mode's name as
three verbs the window receives, which was fair: it reads readers, and
a `"sounding" =>` at the start of a line is what a reader looks like.
The editor's library, too, was built into the wrong `target/` once
more, exactly as the memory warned.

Five photographs on the virtual display, the bar reading ▶ 1.2,
‖ 2.1, ■ 2.1, ▶ 3.3, ‖ 4.2 — the square faint and the readout kept
through *silent*.  Twelve model tests, three new bench tests, 233
Rust tests, the gates.  Transport in one commit, the model in the two
before it; the card is on the done shelf the day it arrived.

## The chart runs — 2026-09-07, evening

*"okay, do the chart library slice, and the measurement."*  The
four-line library from the afternoon's draft became six declarations
in `chart.ges`, and the transport became the first chart the editor
runs.  The mechanics were the interesting part: a `.ges` program
compiled once by the reference G-machine, then its `advance` global
applied to fresh constructor nodes built from Python, twenty
microseconds an event — so a chart costs nothing a keystroke would
notice, and the compile is paid where `command.ges`'s is.  The
language pushed back three times, each a minute: `Score` belongs to
the music library, a type is declared before the type that names it,
and there is no `where`.  The Python `step` I wrote at noon is now
four lines that ask the chart, and every test that held it holds the
chart instead; three more hold what the Python never had — the entry
action, the parked position riding on the event, two charts beside
each other sharing nothing.  Q2 came out concrete: the framework
provides structure and no verbs; a subsystem's verbs are its own
action type, and the palette's commands are its events.

And the measurement, the same hour.  `tools/retraction.py`: the
tree's Datafun does not retract — every evaluation is whole and ϕ/δ
lives inside `fix` — and that was the smaller finding.  The larger is
the constant: a picture-shaped `for` over a hundred rows costs 665 ms
and grows quadratically, which puts *the picture as a query over the
model's relations* out of reach in the reference machine as it stands,
while the same machine walks a roll of hundreds of notes in 80 ms.  So
the mix of types and relations stands as the model, and the relational
half is data and lookup, not a query language for drawing, until a set
unions faster or `crust` runs it.  The number is on the card, with the
command that made it.

## Reading 1 — 2026-09-07, evening, with Henri at the desk

*"lets check the two questions together"*, then *"okay, do reading
1."*  The two questions took a reading and a run: the seminaive
transform keeps a `for` as a node and never looks inside it, and
crust runs the helpers as the ordinary supercombinators they are,
thirteen times the constant and the same growth.  Then the fold:
`for_X` was `join (f h) (for_X t f)`, n merges into a growing
accumulator, and became a balanced merge in log n rounds; the set
literal, which folded the same way, uses the same merge.  The Datafun
suites did not notice, which is the point.

The measuring taught more than the fix.  The first table had barely
moved after the change, because the benchmark's own `rows`, built by
repeated union, was quadratic too and inside the number; and the
reference machine is lazy, so a relation timed to weak head normal
form had built one cell and handed the rest to the query — a second
table that lied the other way.  Told apart by forcing whole values on
the pipeline's deep stack, which deadlocked once when nested inside
`compile`'s own.  The query alone: 665 ms to 33 ms over a hundred
rows, 6.2 s to 123 ms over three hundred, 27 s to 627 ms over six
hundred, and on crust 8, 20 and 14 ms — a picture can be a query on
the Rust machine today, and on the reference machine for a hundred
rows.  What stays quadratic is a program's own recursion over unions,
and the closure's output, which is its size.

Closed the same hour.  *"ok.  I think the card is done.  Planning to
run on crust everything that can run there."*  The machine the window
runs is crust, then, and the picture as a query over the model's
relations is back on the GUI card's table.

## The probe, and the second chart — 2026-09-07, late

*"schedule gesture as a chart for 2026-09-08 (tomorrow morning), lets
do the 1. and 2. today."*  The probe first: `probe x y`, every
attachment a press there would take, innermost first, with channel,
axis and region, and for a note the tick, the key and the line that
wrote it — read off the substrate's own hit table, nothing written.
It is idea 7 as a command, and it is what tomorrow's walk uses.

Then the piano's off/on/step as `hands.ges`, beside the transport, to
settle the last corner of Q2 by building it.  A second file cannot
share the first's action type, so `beside` was wrong to demand one:
it tags each side's actions with `Or` now, and the framework owns the
seams and no verbs.  The composition caught a mistake in the library
itself — the product ran both sides' entry cues on every step, so
stopping the transport re-said what the piano does — and Harel's rule,
the side that moved, is in `beside` now.  Two small rules for a chart
file: its functions carry its name, and its constructors are global
and must not repeat the library's or another chart's — `Step` and
`Playing` were both taken, which is how a played note's third state
came to be called `Noting`.

## The ruler is a chart — 2026-09-08, morning

*"schedule gesture as a chart for 2026-09-08 (tomorrow morning)."*
The roll has four hands written as `if` ladders on the `Session`, and
the ruler is the smallest: one channel, one axis, one command when it
lets go.  So it went first.  `gesture.ges` is the `hand` the card drew
on Sunday, three states and nine arrows, and it compiled on the first
try — the language had already said its three things to the transport.
The ruler's press, drag and release now go through it, and every
drawn-scores test that fed a real press through the hit table passed
without an edit.

The rule that made it fit is the one worth keeping: the chart holds
the time and the host holds the geometry.  The chart knows that a
touch after a touch is a drag and a release after a drag is a commit;
it does not know what a bar is, so the place rides on the event as an
integer and the snap to whole bars stays in the host.  That is also
why *let go where it took hold* is decided twice, once in ticks and
once in bars, and why the same chart will serve any hand on one thing.
The draft's `Down | Move | Up` became `Touched | Released | Cancel`,
because the window does not know which touch is the press — that is
the chart's to decide, and `Up` was the transport's constructor
anyway.

The count is honest: twelve lines of chart and sixty of host, so the
ruler did not get smaller.  What it got is a skeleton the checker
walks — every state and touch, no hand held forever — and the next
hand gets the same skeleton for free.  The next hand is the question:
the note hand decides three things at the press by looking, and
whether that look rides on the event or picks the chart is Henri's
call, written on the card.

## Identity, measured four ways — 2026-09-08, late morning

*"Olin skimmannut paperin läpi ja minulla ei ollut ideaakaan että se
voisi vastata tähän ongelmaan."*  Kale had, and its source said more
than the paper: the hidden row id is the grid's own object, kept for
the session and never written, and every formula's text is regenerated
from it after each change — the position a person sees is a projection
of a thing the system holds.  That is reading E, and the file stays
values.

Then the tree.  The key (voice, tick, key) is measured on one real
piece, because there is one: seven unison doublings a hand cannot
transpose, no chord within a voice.  And E against F on every note:
identical bytes for a pitch or a length, and for a move in time the
same lines in a different order — because `retune` leaves the line
where it was and `write` sorts it to where it sounds, and nothing live
has ever called `write`.  So the choice between the two is not a
mechanism, it is what the file looks like after the first drag along
the rail: the line you put there, or a table.  His question now, and
sharper than it was at breakfast.

## The file is a table — 2026-09-08, midday

*"ota se."*  The identity slice, built on the decision of an hour
before.  The seam turned out to be one function and one call: every
gesture already wrote through `_write_included`, so `notes.canonical`
there made the buffer a table after every commit and nothing else in
the commit paths moved.  The selection was the real work.  It had been
an index into a roll that every rebuild renumbers, patched by spending
it at each commit; now it is a set of keys — tick, key, and the voice
only where the key is two notes — that a press or a `select` writes,
a commit sends ahead to where the notes will be, and the bench's new
`rebuilt` hooks let the session find again in the new roll.  A group
carried twice without a second sweep, on his piece, is the number.

One mistake worth the sentence: I compared rolls by `id()` and a
rebuilt roll landed at the freed address, so a settled selection
looked unsettled on the second move and not the first.  Held the
object instead.  And one thing left half-open on purpose: the typed
`transpose` still has no voice in its address — the press that
selected the note is the tiebreak — because the fix is an arity
change to four verbs and the transcript, and that is his to ask for.

## The voice in the address — 2026-09-08, afternoon

*"laita transkription transpose-osoitteeseen ääni."*  Three verbs
share the note's address and all three took the voice, second, so a
line reads box, voice, tick, key.  The interesting line was the
refusal: a wrong voice on a doubling now names who does sound there,
because a refusal that only says *no* sends the person back to the
picture to find out what the command already knew.  The test caught
me naming the wrong voice for arc.notes's first chord — melody and
middle double the D, not melody and upper — which is the kind of
mistake the address exists to make impossible.

## The full run, and what it owed — 2026-09-08, afternoon

The shift's one full pass: 4136 tests, 32 minutes, seven red.  Four
were mine from an hour before — `mark` took the voice and its tests
had not been told.  One was the testimony page a memory behind.  Two
were the formatter on the chart files, which no full run had seen
since they were written: a constructor's field printed without its
parentheses, which is either a different program or none, and F209's
two shapes — prose between two type declarations sent to the end of
the file, a nested `case` flattened into its parent's column.  Three
repairs of a few lines each, and the ratchets asked for their due:
five files out of one allowance and nine out of the other, which is
the most satisfying kind of red.

## The note hand is a chart — 2026-09-08, evening

*"A."*  The roll's hand, the one the morning called the hard one:
three recognisers deciding at the press by looking, and two channels
for one press.  The chart takes the look as a payload on the pitch's
touch and the rail's touch as a state of its own, and after that it is
eight states and thirty-two arrows, compiled on the first try.  The
host was the afternoon: two hundred lines that had been sorted by
channel are sorted by act now, and the four tuples the ladders kept in
step became readings of the chart's state, so a dozen tests that asked
a fact of the hand got the same answer from a different place.

What the chart gave back was a defect of my own from breakfast.  A
diagonal drag was two commands, and once the file wrote itself in its
own order the second command's address was stale.  I found it by
doing the naive thing on the one note the existing test had not
chosen, and the chart had already decided the shape of the fix: a
`Carry` is one act, so it is one command.  Twelve hours from the
first chart to the fourth; the ruler, then the roll.

## The window inspects itself — 2026-09-08, evening

*"Lets go for the Idea 7, should we?"* — after *"the inspection tools
should probably go higher."*  `card:gui-is-difficult.md` §"Landed —
2026-09-08, evening" is the record; three things worth the journal.

**The first seam test returned an empty string**, and that was the
day's best catch: the verb I had chosen, `asked`, was already the
palette's word for *done asking*, so `act` swallowed it silently.  A
word added to one end of a wire that the other end already means
something else by is exactly the defect the atlas's wire gate exists
for, and the gate would not have caught this one — both ends knew the
word.  The test did, because it asked for an answer and got none.  The
verb is `pointed`.

**The wire gate refused the model half alone.**  I meant to commit the
model side first, F101's order, spec then seam tests then Rust — and
`test_the_two_ends_of_the_wire_agree` said *`pointed` is read and
nothing sends it; `told` is sent and nothing reads it*.  Right: F101
is about the order of *writing*, and a commit is a publication of a
whole.  So the two halves landed together, and the order of writing
was still spec, tests, Rust.

**The photograph found an older defect in two minutes.**  The first
Ctrl-press in the real window said *written at line 246* for a file of
158 lines, and a plain press on the same note said the same bare
number — `fixme.md` F212, in the click path since the roll learned to
say a line, and invisible to every test because the tests' benches
carry an `origins` table the live bench does not answer from.  Which is
the postcondition of the card in miniature: the mechanical work was a
session's, and the finding came from hands on the picture.  Nobody has
timed the two minutes yet; this slice is the one to time them on.

## The picture as a query, measured before it was built — 2026-09-08, night

*"lets try the query-as-picture on the notes."*  Q1 had his yes an hour
earlier, with four kill conditions written beside it, and the first of
them had a command's worth of work in it — so the evening went to the
number and not to the generator.  `python tools/queryframe.py`: 22 ms a
frame on crust at the page's 152 rows, 11.8 for the stacked roll alone,
against today's walk at 5.8 and 3.4 ms on the reference machine, which
is the slower of the two by a factor the earlier card put at thirteen.
The kill condition fired for *a query every frame* and left standing *a
query on change, with the hand's preview per frame* — which is what
the generated program already does with its channels, so the slice
that survives is the notes layer alone.  Three things worth keeping:

**An hour went to two deadlocks that printed nothing.**  The compiler
takes the pipeline's deep stack itself; I called it inside
`_deep_stack` twice — once wrapping the whole run, once for a second
compile inside the timing — and each time the run sat silent past a
ten-minute timeout, the output buffered behind a `tail`.  The
retraction tool's own comment names this trap.  The lesson that is not
in the comment: **a measurement that has printed nothing in a minute
has told you something about the harness, not the subject** — go and
look at what is running before waiting on it, and never pipe a slow
run through `tail`.

**The join cost as much as the roll.**  A five-row selection joined by
a nested `for` was 102 ms of the reference's 339: n·k singletons
merged.  Membership is a lookup, and the query must be written so, or
given a `member` the language provides.  That is a shape the number
found and no argument would have.

**The postcondition's number moved to where it bites.**  *The frame is
no slower* is now measured on the drag — the hand's per-frame layer —
and not on the whole picture, because the whole picture is allowed to
cost twenty milliseconds at a press.  His two minutes, when they come,
are on a moving note.

## The notes as a relation, built — 2026-09-08, night

*"can you create those things you need, and then write the generator?"*
`card:gui-is-difficult.md` §"Landed — 2026-09-08, night" has the
numbers; two things for the journal.

**The name clash was the compiler's catch, not mine.**  `rollRows` and
`rollLeft` already existed in `roll.ges` — the staff's lines, the body's
edge — and I wrote both again for the relation and the merge's other
half.  The compiler refused a duplicate signature and the score-box
tests had passed anyway, because the compact box did not load the
library then.  A library one writes into without reading its index
first is a library one collides with; the fix took a minute and the
lesson is the reading.

**Two tests encoded the painter's order without saying so.**  They
paired the first four heads of the picture with the first four rows of
the file, which held only while notes were drawn in file order.  The
two layers draw the standing notes first and the carried on top, and the
tests failed on order, not on the picture.  Rewriting them found a
second unsaid thing: a grown bar keeps its left edge, so its key stays
while its width changes, and a set of positions cannot see a bar that
shares a corner with a wider one.  The tests count whole heads now.
What they hold is the same claim, said in a way that does not depend on
which note is drawn first.

## The reviewer role, run once — and the corpus nobody had read, 2026-09-08

*"I ran the reviewer role for the first time."*  It was invoked the day
it landed, and what it found was not in the tree at all: `~/.claude/history.jsonl`,
**2,943 prompts Henri typed at gestate over 37 days and 106 sessions**,
first line 2026-08-03, which is **five days before git's initial
commit**.  A handoff was written outside the tree because another
session held it that afternoon — `board/README.md`'s rule that two
writers never touch one file, kept by a session that could not write
anyway.  This sitting landed it.  `doc/memory/the-prompt-log.md` is the
record; four memories were corrected from it, each with the line and
its timestamp:

- **[[day-one-was-not-day-one]]'s central hedge narrows.**  It said no
  artefact *in this repository* can attribute the spine, and that stays
  true; the log is not in the repository and it attributes one piece —
  *"Let's add a rule into the specification: Do not create things that
  are not needed"*, 2026-08-04, four days before the commit that memory
  called the earliest evidence.
- **[[gui-command-language-first]] was 27 days late**, and he had marked
  it joint at the time: *"I didn't come up with that alone.  It was
  result of this discussion."*  A memory written later gave him whole
  what he had already split.
- **[[gestate-testing-standard]] got its sentence and its cause** —
  *"now I've seen testing.. Definitely lets test things from now on and
  properly"*, and five days before it, Ariadne: *"a string out from a
  maze."*  The name in `test_ariadne.py` is the same thread.
- **[[henri-pushback-on-unsafe-asks]] had two moments written as one.**
  The concession is 09:39, the approval 09:56 — he agreed, worked
  seventeen minutes, and came back to say it.  Read as one exchange it
  was politeness; it was not.

**And the transcripts beside the log were expiring.**  `cleanupPeriodDays`
unset, cleanup daily, 31 days present and one leaving every morning:
**19 sessions had already gone** before anyone looked.  Stopped and
copied out the same day, outside the tree.

**What the role is worth, on one run.**  It found a corpus, four dated
corrections and a silent data loss — none of which the building
sessions had looked for, because none of them was asked *what is
missing*.  That is one run and not a measurement, and the reviewer was
inside the tree, so `spec/roles/reviewer.md`'s own ceiling holds: it
could not have said the tree is pointed the wrong way, and it did not.

**Two things it left open, and both are his.**

*The count he has now asked for twice.*  2026-08-28, with people in the
room: *"show me an example of where you have pushed against me.  I need
it to illustrate to my friend at platform 6, what you are."*  And again
as this session's opening question.  Neither could be answered, and the
reason is structural: **a session refusing him, or catching an error
before it reached him, is not an event class here** — no shelf, no
field, no stamp, while a card, a defect, a tool and a memory each get
one.  `board/refused/` counts *his* refusals of cards, not the
sessions' of asks.  Whether that earns a mark is his; what the log
added is that the need is standing and dated, not passing.

*A measurement that failed on its own terms.*  A vocabulary counter run
over all 37 days was **language-blind** — every regex English, while
Finnish went 0 → 1 → 22 → 33 → 8 percent across the five weeks, and
2026-08-29 is 46 Finnish prompts and no English — so a week that read
as a collapse was a change of language.  The `board`/`rule` share peaks
in the week the board was *built* and falls after, so it measured
construction and not adoption.  The metric that survived was chosen
after seeing the data, which
[[a-trial-is-refused-until-its-sheet-can-decide]] forbids outright.
**So the reading is weaker than before the test, not stronger**, and it
is recorded here rather than quietly dropped.  Redoing it means
pre-registering in both languages, naming the null in advance, and
handing the pass to a session that has not read this page.

## He read the tic-tac-toe and called it heavy — 2026-09-08, night

*"The program does work, but it's something I would never leave from my
hand, because it's doing very complicated things to get there… This tic
tac toe demonstration is complicated for what it is.  I don't know if
this should be optimized, but it's worth saying."*

He was right, and agreeing would have been the wrong answer: the useful
one was to find out **whose** complexity it was.  Measured, it splits
three ways, and only one of the three is the framework's.

**A quarter of it was mine.**  132 lines of code became **99** with no
change of behaviour and the same 34 tests: `deriving Eq` instead of
twelve lines of nested `case`; a tuple pattern in an argument —
`step (seen, b) (x, (n, y))` — instead of four nested `case`s taking
one tuple apart; `filter`, `all`, `length`, `clamp` instead of four
hand-rolled recursions.  All of them in scope, all of them on a
generated reference page, none of them reached for.  I wrote the
general form I can always write rather than the specific one the
language already had.

**What caught it was a person's eye, and nothing else could have.**  The
program compiled, the tests were green, the game played under a real
mouse, and the driven run photographed it working.  Every instrument
this tree has said yes.  The defect was that it was *heavy*, and heavy
is not in the suite — `manifesto.md`'s table has the row for it: a
picture that looks right for the wrong reason still looks right, and
here the code was right and still wrong.  That is the postcondition of
`card:gui-is-difficult.md` doing exactly what it promises: a session did
the mechanical work, and the keeper's hands found the thing the
mechanical work could not.

**And of the 99 that remain, 81 are not about gestate** — 41 model, 40
picture, both of which you would write in any language.  The hand is
18, and about seven of those exist only because a press arrives as two
instants and a program cannot hear the release.  So the fair sentence
is not *the framework is complicated*: it is that the framework taxes
this program about seven lines, and the session added thirty-three of
its own on top and did not notice.

**No memory for it.**  The lesson — check what is in scope before
writing the helper — is `why-models-hallucinate`'s *fluency is no
evidence* and `henri-working-style`'s *reuse existing machinery*,
already carried.  What is new is the number, and the number belongs to
the card.

## The clean board, and what it turned into — 2026-09-09

*A whole day on `card:gui-is-difficult.md`, which he had taken the
evening before as a clean-board sitting.  It began as design and ended
with four things built, and the turn in the middle was his.*

**The morning was the design he asked for.**  A target source for
`examples/gui/tic-tac-toe.ges` — the same game written as if the
framework had been designed for it — put the difference at 99 lines
against 66, the hand at 22 against 3.  Then the roll, because he said
*ristinolla on loppuen lopuksi vain demo*, and the roll said it
harder: nothing visible on it is pressable (a `Gap 0 0` over the whole
body), one straight line is written five times in two languages, and
the clamp had deformed the picture — the pad is drawn 24 semitones
taller than the roll so a hand can carry a note off the top, and the
box's clip hides it.  `tools/pressable.py` measured the one thing that
could not be read off the tree: a pressable element per note costs
6–14 %, and today's only mechanism costs 80 % and quadruples the
source.

**Then he struck the framing, and that is the day's hinge.**  *"Mikä on
malli, mikä on komento, ja mikä on näkymä?  ristinolla-esimerkissä
malli oli gestate:n tietotyyppi… Mielestäni tämä vie metsään ja
kovaa."*  The tree agreed with him twice, unasked: `gui.ges` says of
itself that it is *not a drawing library*, and `desk.py` says a knob's
value has to live outside the program because a declaration is not a
value.  A gestate value lives inside one evaluation; a rebuild ends it.

**What replaced it was already in the tree, written twice and never
named.**  `.notes` and `.desk` are one grammar — a text of record
lines, a kind word and its fields, one to a line.  The roll's seven
verbs turned out to be three shapes, and the record algebra's *add* and
*remove* turned out to be **typing**, in the buffer, outside the
command language, which is exactly why they were the two edits a
selection could not survive.  He named it: **facts**, *"etenkin jos
tästä jatketaan logiikkakieliin myöhemmin"* — and the name paid for
itself in the same minute, because assert and retract are two
operations and `set` is the pair.

**And then his conclusion, which is his own rule of two days earlier
with its content filled in:** *"Näen tässä yhtenäisen mallin,
itseasiassa!  Miten GUI-ongelmat ratkotaan on kenties se, että luodaan
selkeä malli, ja selkeä komentokieli.  Ja sitten GUI on mitä siitä
putoaa."*  Scored against the card's own four hard things, it removes
*two machines must agree* outright, makes *a gesture is state over
time* testable as a chart, and leaves *geometry is continuous* and *the
oracle is an eye* standing.  So the deliverable is a method and a
substrate, not a toolkit — which is also the line a guest session had
handed him that morning (`doc/notes/notes-on-the-model.md`), and the
sitting here is **not** a second witness, because his questions in it
came after that conversation.

**Four things were then built, in one order that repeated itself.**

1. **`gestate/facts.ges` and `gestate/notes.ges`** — what a `.notes`
   *is*, said in the language, a kind being a value the way a chart is.
2. **`notes.py` reading it** — the four hand-written field sets gone,
   the kind list, the at-most-one rule, the bare arity and the
   canonical order all derived.
3. **`assert` and `retract`** — the two primitive edits as commands
   taking the document's own syntax.
4. **`Meaning`/`onPress`** — an element that says what it *is*, wired
   in both machines, with tic-tac-toe rewritten on it and every note of
   a score box carrying its own number.

**The order that repeated is the lesson.**  *Declare, hold to parity,
derive.*  Each time: write the second statement, hold it to the working
one by a test, and only then let the working one obey it.  Its value
showed the first time it was used — deriving the canonical writer from
the declaration exposed that `By "section"` was wrong where the parser
had always sorted by *where the section stands in the file*, an error
that agrees with the truth on `arc.notes` and nowhere else, and that
nine parity tests had just passed over.  **The defect appeared the
moment the implementation was made to obey rather than to be compared
with.**

**Two defects found by looking, not by testing.**  `Display::grabbed`
in the panel took hold only of a `Kind::Chan`, so a meaning would have
been walked, drawn, hit-tested and then dropped at the grab — the
window silent and the reference machine right, which is F213's shape
exactly.  And the `Meaning` around a note had to go **inside** the
`Shift` and **around the bar**: outside it the region is the parent's
centre, and around the whole note it reaches from the note to the top
of the box.

**What the day did not settle**, and both are his: whether `note_under`
can be deleted, which is a question about how near a press has to be
rather than one a test can answer; and which note a press means where
two are drawn over each other, which the measurement put at 8 pairs on
his own piece, all of them across voices.

## Seven copies of one number — 2026-09-09

*Henri, at the desk: "when I try to start gestate workbench, it throws
an error on build."  It did, and the error was the shallowest of six
things wrong, all of them the same edit half-finished.*

**What he saw.**  `python -m gestate.workbench examples/super/dubgate.ges`
builds the editor on its first run; `cargo` returned four errors from
`shell/panel/src/canvas.rs` and `editor.py` re-raised them as an
`EditorError`.  No window.  `Grab` had arrived the day before with
`onPress` — `taken`, `motion` and `fractions` all converted to it — and
the field they read, `held`, plus `grabbed()`'s destructuring, had kept
the tuple it replaced (F217).  Two lines.

**Then the rest of it.**  With the build going, `cargo test` was red in
two crates and `pytest` red in thirteen more places, and every one of
them was the same fact written down twice: `export._SUB_CONS` gained a
fifteenth constructor and seven other copies of *how long that table
is* stayed at fourteen (F216).  `walk.rs`'s `TAGS`, three `.walk`
fixtures, four panel fixtures, the CLAP plugin's `[i64; 14]`, the page's
`web_alloc(14 * 8)`, and a `== 14` in each of `test_export.py` and
`test_online.py` — the two that should have said so first.  Four
languages.

**Two of them are worth keeping.**  The page's copy (F218) threw a
`RangeError` inside `.set` where nothing was catching, so thirteen tests
reported *"no picture on the page"* and none of them reported why; the
repair is `spec.tags.length`, because the table is right there.  And an
attachment record had separately grown an eighth word, `means`, while
two readers still strode seven (F219) — which only shows from the
*second* record on, so six of seven gallery pieces were green and
`lantern.ges`, the one with two channels, was not.  An off-by-one that
hides behind arity is worse than one that does not.

**`TAGS` is the one that taught something.**  `Walk::read` refuses a
payload whose table is the wrong length, deliberately: *a table of
another size is another program's idea of `Sub`*.  So the stale constant
did not crash and did not draw wrong — the window simply stopped walking
anything and the model kept drawing the canvas itself.  Photographed
both ways on Xvfb: the picture is there either way.  A poka-yoke that
fails safe is a poka-yoke whose failure nobody notices, and that is the
argument for the gate rather than against the refusal.

**Nothing in this tree compiles Rust before a commit.**  The pre-commit
hook runs the gates and the gates are document checks; `cargo test`
lives in the full pass, once a shift.  So a commit touching four Rust
crates landed red and stayed red for three commits, and the thing that
found it was Henri trying to start the program.  `test_panel_fixtures.py`
already pins the panel's half of this seam and says at length why an
unregenerated fixture is the F101 shape; the editor's half had no such
pin, which is also how `ticker.walk` came to drift from its own source
long before this week — 600 program lines today against the committed
293, with nothing to say so.  `test/test_walk_fixtures.py` is that pin
now, mutation-checked against both defects it would have caught.

*Left open for him: whether `cargo build --workspace` belongs in the
gates, and whether the two fixture-pinning tests do.  Both are seconds;
neither is a session's call to make.*

## The sweep closes on its schedule and not on its postcondition — 2026-09-10

`card:ungated-fixes.md` is done, thirteen batches from 2026-08-19 to
2026-09-04, and it leaves **92 `gate:` lines** in `fixme.md` where it
found none.  The card's `## Done` is the ledger.  This entry is the one
thing worth carrying out of it.

**The tail shrank and the head refilled.**  The card opened on a proxy
count — 62 repairs named by no test — and swept them five a session.
Counted the card's own way six days after the last batch, with a gate
line naming an instrument counting as held and a gate line saying
`none` counting as not:

    python tools/gatecount.py
    220 entries — 41 that nothing would catch
      25 from before card:ungated-fixes.md, 16 since
      of them 15 were read and marked `none` by the sweep

So the sweep worked and the file grew under it.  **Sixteen of the
forty-one arrived after the card was written**, which is after the rule
was settled: bind every new closure, an instrument counts, not only a
test.  The rule was answered in August and enforced by nothing since, so
every entry written since has been free to close without one.  That is
not a failure of the sweep; it is the difference between doing a thing
and installing it, and this file is where the difference shows up as a
number.

**And fifteen of the forty-one are not a backlog.**  They were read and
marked *nothing in the tree would say so* — the sweep's fourth verdict,
written after looking.  An honest `none` is worth more than silence
because it tells the next person where an afternoon would pay, and
counting it as a failure would teach a sweep to write tests that pass
rather than tests that would have caught the defect.  The real
remainder is 26 never looked at.

**What was left undone was question 3 of the card**, *does the suite
enforce it?*, answered in shape — an accepted baseline that may shrink
and never grow — and never built.  He read the close and said *"build
the gate then"*, so it was built the same hour: `test/test_fixme.py`,
gate twenty, a baseline of fifteen that may shrink and never grow.

**And building it found two ways for a gate to make its own subject
disappear.**  The baseline lists the F-numbers nothing catches, and the
rule for *held* is *some file under `test/` names this number* — so the
first run read its own list as fifteen tests naming fifteen entries and
the whole set vanished.  Excluding the file by name left
`__pycache__/test_fixme.cpython-*.pyc`, which holds the same strings,
and the count came back as 27 where the truth was 41 — **worse than the
first failure, because a partial answer looks like an answer.**  Both
were caught by the number disagreeing with a measurement taken twenty
minutes earlier, which is the only reason either was visible.

**And the proxy is a proxy in both directions.**  Mutating in a new
`[resolved]` entry numbered F999 did *not* go red: `test_blind.py` uses
F999 as a fixture, so mentioning a number holds it as far as this gate
can see.  Renumbered to F400 it went red by name.  A stricter regex is
not the fix; naming the instrument in the entry is, and that is what the
`gate:` line is for and what this gate asks for.


## The page carries sideways, and two oracles said it did not — 2026-09-11

`card:notes-editor.md`'s ninth slice had written its own debt down in
arithmetic: *a nine-bar section is 1182 pixels wide in a window 1100
wide*, so the section-resize tool built that afternoon dead-ended the
first time anybody used it past eight bars.  Four days later the
sideways carry is built, and it added **no arithmetic at all** —
`view::canvas_scroll` is a clamp that does not know which way it runs,
so the second axis is that same function called with the window's
width.  What is new is one reader, `span_across`, and one number in the
origin.

**The part worth carrying is not the scroll.**  It is that the first
two oracles written for the driven run both answered *no, it did not
move* about a page that had, and both answered confidently.

The first asked whether the **page's ground** had moved between two
photographs.  The ground is 2078 pixels wide in a 1100-pixel window at
every scroll, so it is cut at both edges and its bounding box reads
`(0, 192, 1098, 566)` whatever the page does.  The oracle could not
see the thing it was pointed at, and what came back was not *I cannot
tell* but a clean negative.

The second asked whether the **whole window** differed after forty more
tilts, to check that the carry stops at the last bar.  It does stop;
the status bar carries a clock, so the window always differs, and the
report said the page had run past its own end.

What answers honestly is the roll's band differenced — the status row
cropped off — and the keyboard down the page's left edge, 25 rects of a
colour nothing else in the roll wears: present at x 1 when the page is
at bar one, gone entirely when it has carried.  With those, seven
observations in seventeen seconds, and the strong one is the file: a
press at the computed place took the note at **bar 14** — the only note
past the fold, which nothing in the run could reach unless the page had
carried — and `Ctrl-S` changed `key 64` to `key 67`, one line, nothing
else.

**The shape is `doc/memory/dont-conclude-from-a-shallow-check.md`, one
floor down.**  That memory is about a search: an empty result from a
guessed-at search is evidence about the search.  This is the same thing
where the instrument is a photograph, and it is worse, because a
photographic oracle *looks* like the real world.  Three runs of the
same scenario cost fifty seconds between them; believing the first
would have cost the slice.

**And a build that compiles nothing reports success.**  `window.rs` is
behind `#[cfg(feature = "window")]`, off by default, so
`cargo build -p gestate-editor` prints *Compiling gestate-editor* and
*Finished* having compiled none of the file just edited.  Twenty
minutes went into whether cargo's freshness tracking had broken — it
had not — and the thing that settled it was appending
`fn __probe() { let _: i32 = "no"; }` to the file and watching the
build stay green.  A build is not an instrument until a deliberate
error has failed it.  `--features capi` is the honest spelling, and it
is the one `tools/driven.py` already names for the other reason.

**Found and not fixed:** `fixme.md` **F221**, a section's caption
anchored to the body's centre, which only becomes wrong once a page is
bigger than the window.  Left as an entry because where a caption
belongs on a scrolling page is a picture decision and the spec has
never said.

## The seam that was priced out of reach was a method — 2026-09-11

*Henri, after the sideways carry landed: "I think I still do not hear
the note preview when I press and modify a single note."*  True, and
the tree could say exactly why: every `.notes` gesture sounds when it
**lets go**, and nothing at all while a hand holds a note.

`spec/annotations.md` §"The three paths, priced" had settled this on
2026-09-04 and settled it against building anything.  Path 1, through
the keyboard: *"`noteOn` takes channel, pitch, velocity — there is no
manner in it and there cannot be, because a keyboard has no marks"*, so
a note marked staccato would preview long.  **Cheap and wrong.**  Path
2, render the note in isolation: it *"needs a compile per gesture and a
seam that does not exist: a way to sound one payload, with its fields,
through its bank"*.  **Right and expensive**, and left as a card of its
own.

**That last sentence is two claims and only one of them was true.**
The compile is for rendering a note *in isolation, both ways* — still
unbuilt, still wanted.  The **door** was never missing:
`Allocator.note_on` has always taken a payload tuple.  What stood in
front of it was `Notes.feed`, which builds one from a MIDI message —
and a message is the thing that cannot carry a manner.  A caller that
knows the bank knows the fields.  `Notes.sound(bank, note, payload)` is
twenty lines, and the preview now hands over the three values the score
itself schedules: key, level, manners.

So the page's own objection to path 1 does not apply to what was built.
What is heard under the finger is the note the piece would play.

**A whole design decision had been taken against a door nobody had
tried**, and the sentence that closed it read as a measurement because
it stood beside two real ones.  *Right and expensive* was half right;
the half that was wrong is the half that stopped the work.

**And the test that mattered was the one the stub could not be.**  A
bench recording `sound` calls proved the sequence — a press starts one
note, a drag stops the old pitch before starting the new, a motion
inside one semitone does not retrigger, the commit ends it — and would
have shipped two defects:

* **Every voice of a `.notes` file is a bank the score writes**, and a
  scored bank starts with its listening switch *off* (`_allocators`:
  *two writers on one set of channels is still a fight*).  A preview
  that consulted that switch would have been silent on exactly the
  notes being edited.  The switch guards the routed door against a
  keyboard that might be played at any moment; the named door's real
  question is the transport, and that is where the guard went — the
  same *only from a standing start* rule `_hear_from` already keeps.
* **A `.notes` voice takes a three-value payload.**  The two a MIDI
  message can build are refused by `Allocator`'s own arithmetic — the
  spec's objection to path 1 arriving as an `AllocError` rather than as
  a wrong sound.  It is the best kind of refusal: the machine saying
  the thing the prose had said, in a place nobody could route around.

Both came out of one test that builds the real allocators for
`arc.notes` and asks the allocator what is sounding.  It was written
because the stub felt too comfortable, not because anything was known
to be wrong.

**F221 closed the same sitting**, his call between two readings: a
section's caption is drawn at its own start now rather than at the
body's centre, so it scrolls away with the bars it names.  The repair
is a label exactly as wide as its own letters — `gui.py`'s `_fit` takes
the scale from declared numbers alone, so the box's centre is the
text's centre and half a width in from the left edge puts the first
letter on it.

## And the window said the guard was upside down — 2026-09-11

*Henri, running `untitled.notes` within the hour of the preview
landing:* *"I do still do not hear the note play review.  I try to
play it from 'playing' and 'sounding' -states… and if I try it from
'stopped' -state, it ends up gunking the 'play' and I'm no longer able
to play the note."*

**The guard read `Workbench.playing`, which is `self._audio.is_alive()`
— the engine being up, not the clock moving.**  Against
`spec/transport.md`'s three states it was inverted in both directions:
*silent* is engine down and it previewed there, *sounding* is engine up
with the clock held and it refused — and *sounding* is precisely the
state a hand edits in.

The *silent* half is the worse one and it is not simply inaudible.
`Notes.values` holds the control values the engine reads, so a gate
written while the engine is down is picked up as an **initial value**
when it comes up: the piece starts with a note stuck on, one of four
voices gone, and after a few presses the bank has none left.  That is
his *"gunking the play"*, exactly, and the word for it is better than
the one a session would have written.

**`session._state_of` had already written the warning** — *"Not
`Workbench.playing`, which asks whether the audio thread is alive — a
different question wearing the same word"* — for this trap, three
screens from the code that fell in.  It did not help, because the new
code never called it.  **A warning is worth what the path through it is
worth**, and the repair is not a better sentence but that every reader
of the transport goes through the one function.

**And the tests were green over all of it.**  They were green because
the bench is a stub, the stub answered `playing = False`, and
`playing = False` is what the wrong reading needed to be true.  A stub
answers what it was built to answer, and it was built by the same
reading that was wrong — which is the shape of
`doc/memory/test-what-a-person-would-do.md`, arriving from the other
side: a harness built from the implementation cannot find a missing
affordance, and one built from a misreading agrees with it.  What found
it was a person opening a file.  Nine minutes of use against a green
suite, and use won.

The third report is a different thing and was simply missing: *"when I
press Ctrl+space, the currently playing note ends up sounding to the
background."*  A preview is held for as long as the hand is; `play`
does not pass through the hand.  Every transport verb hushes first now.

## The state a person is actually in — 2026-09-11

*Henri, an hour after the guard was repaired:* *"I restarted the
editor, and it still shows the old behavior.  now I tried the desktop
icon and direct command `python -m gestate.workbench untitled.ges` and
navigated to the untitled.notes -file."*

**The suspicion he offered was staleness, and it was worth ruling out
properly rather than answering from memory.**  Three things could have
been old and each was checked: the loaded library
(`editor._stale` said no — built 13:46, newer than every `.rs` it
watches), the launcher (`tools/gestate-editor` `cd`s to the tree and
uses its venv, so the Python is the working tree's), and an installed
copy shadowing it (there is none; `import gestate` from outside the
tree fails).  Nothing was stale.

**What answered it was a measurement, not a reading of the code.**  A
real `Workbench` over a two-note `.notes`, no sound card, the press
driven through the session in each of the transport's three states:

    silent    press -> 'line 3'   sounding_on(melody)=[]
    sounding  press -> 'line 3'   sounding_on(melody)=[62]
    playing   press -> 'line 3'   sounding_on(melody)=[62]

The repair worked.  **And a freshly opened editor is *silent*** — which
was the one state it refused in.  So the answer to *"it still shows the
old behavior"* is that the new behaviour was correct in the two states
he was not in.

**That is a worse failure than the one it replaced**, and worth naming
as its own kind: not a wrong mechanism but a right one *scoped to the
wrong occasion*.  It passes every test, reads correctly in review, and
is invisible to the person it was built for.  The first version failed
because it read `playing` as the wrong word; the second failed because
nobody asked **which state is a person in when they do this**.  One is
a misreading, the other is never having gone and looked — and the
tree's own instrument for the second is `tools/dragcheck.py`'s whole
argument: *nothing in the window says so; you have to look*.

**And the design had an asymmetry that should have given it away.**
`_hear_from` has started the piece from a **dropped** note since
2026-09-06, engine up and all — so in *silent* the release already took
the sound card, and only the press refused to.  A press that is silent
beside a release that starts the whole piece is not a rule anybody
would write down; it was the residue of two decisions taken five days
apart, and it survived because no single reader ever saw both.

His call, given three readings: **bring the engine up and sound it**.
A press is a request to hear, which is what `audition` does from
silence — `spec/transport.md` sentence 4 — so it is the spec's own move
rather than a new one.  A bench that will not come up is still left
alone and not written into, which is the *gunking* guard kept intact.

**The probe lied once on the way**, and it is the third oracle to do so
in one day: it pinned `bench.state` to a constant property, so the
wake-up could not take and the silent case read as a refusal *after*
being repaired.  An oracle that fixes the thing it is watching answers
about itself — `doc/memory/dont-conclude-from-a-shallow-check.md`
§"The third failure mode", which had been written that morning.

## The author named the mechanism and the mechanism was the bug — 2026-09-11

*Henri, after two repairs that had not worked:* *"I think there's
something else going on.  You recall that the voice banks are layered?
That is, the MIDI-note fed into the bank does not play along the main
note.  However.  The mechanism is blocked because the voice bank doesn't
have FromMIDI -class.  That might be tripping and causing the behavior I
note."*

He was right, and it is `fixme.md` **F222**.  `Workbench.control` is the
one function the render loop reads.  Its precedence was: a channel in
`_midi_channels` reads `Notes.values`, otherwise the schedule wins.
`_midi_channels` is filled only through `listen`, gated on `takes_midi`,
gated on the program having a `FromMIDI` instance — and a `.notes`
wrapper's voices take `(key, level, manners)`, which no MIDI message can
build, so there is no instance and **there never will be**.  Every
channel the preview wrote was answered from the score, every block.

    _midi_channels: []          takes_midi('melody'): False
    sound() took: True          allocator says: [70]
    notes.values written:  gate 1, pitch 70, level 6
    channels the engine READS that changed:  NONE

**Four oracles today, and every one of them blind in the same way: each
asked something upstream of the thing that decides.**

| the question asked | what it could not see |
|---|---|
| did the page's *ground* move? | the ground is wider than the window at every scroll |
| did the *window* differ? | the status bar has a clock |
| does `bench.state` move? | the probe had pinned it to a constant |
| did `sound` take, does `sounding_on` list it? | whether `control` ever reads it |

The first three cost minutes.  The fourth shipped, twice, and was
believed both times — because it is the one where the upstream answer is
*genuinely true*: the session did call it, it did return `True`, the
allocator did hold the note.  Nothing was lying.  The reading was just
not about sound.

**The rule that comes out of it is sharper than "verify".**  For
anything with a consumer, ask **what reads this, and did *that* change**
— not *did I write it*.  A write, a return value and a data structure
are three ways of asking the same too-early question.  `control` is the
consumer here; the file is the consumer of an edit, and that is why the
file oracle in the morning's driven run was the one that held.

**And it took the author to find it**, which is the part worth keeping.
He did not report a symptom a fourth time; he named a mechanism —
*layered banks, no `FromMIDI`, the mechanism is blocked* — and the
session's job was to go and measure it.  Nine minutes of his use against
a suite that has been green through all three versions of this
(`doc/memory/test-what-a-person-would-do.md`, and its sentence *a
harness built from the implementation cannot find a missing
affordance*).  Three sessions of mine could not have found it, because
all three would have written the same upstream assertion.

The repair is a third precedence, narrow: `Notes.previewing` holds the
channels of the **voice** a preview allocated, and `control` reads them
ahead of the schedule.  What it costs is named rather than hidden — in
*playing* the allocator may pick a voice the schedule is using, and that
scored note is shadowed while the hand is down, because the allocator
and the schedule assign voices independently.

## The gallery's last two rows, and one of them was not the row — 2026-09-11

`card:audiovisual-gallery.md` is done, and the way it closed is worth
more than the closing.

**Henri, on the flow lamp's seven days:** *"I think the
audiovisual-gallery.md could be stated to be completed, or if it's not,
it could be worked on enough to become done."*  Three readings with
their prices; he took the largest — the fader **and** MIDI.

**The fader row was a fault rather than a feature**, which is why it
went first.  He had met it on the live site: *"I tried it in lantern and
the knobs appear to work.  Not certain if they do anything there."*
`warmth` is one declaration and the page had made it two controls, a
slider reaching the sound and a fader reaching the picture, neither
moving the other.  On the desk they are one thing because
`Workbench.control` resolves a channel **by name**, so the name is the
bridge on the page too.  Both directions, deliberately: fixing only the
fader would have swapped which half of the fault a person meets.

**Then the MIDI row turned out not to be the row.**  Counted before
building — thirty-four pieces declare a bank and **three** have a score
that reads `hear holds`.  Those three are the ones the page refuses,
and the card had written *"the three refused pieces are the test set
either way"*.  They are the one set that cannot be: the page **bakes**
its score offline and ships the control changes, and a score whose
content depends on what a hand holds now cannot be baked.

**And then a session got the reason wrong, confidently, in a card.**
It wrote that this was `card:online.md`'s C row — *struck with Pyodide
at his word* — and Henri did not believe it: **"I'm a bit surprised
that pyodide would be needed there.. I thought that clap plugins work
same way now, and it doesn't require python to work, or does it?"**

They do, and it does not.  `shell/clap/src/dynscore.rs` carries the
compiled program and forces it on `crust` with no Python at run time;
`descriptor.rs` is written at **build** time, which is exactly what
`online.generate` is to a page.  And `shell/web` already depends on
`crust` and already builds for `wasm32` — its own header says *"only a
G-machine could run it and the tab had none"*, past tense.  **The
G-machine has been in the tab since day two of this card.**

The mistake was reading C1 as *any score running in the browser*.  C1
is **compiling `.ges` text** in the browser, which needs the front end.
Forcing an already-compiled stream needs a machine and a program, and
both were there.  What is actually missing is a seam — `crust` is in
the canvas module, the sound is in the worklet — and that is
`card:hands-in-the-tab.md` now, with the obstacle measured and this
paragraph in it.

**Two things about how the day went, and they point the same way.**

The session asked before building, twice, and both times the answer
changed the work: the scope question turned one row into two, and the
design question for the preview earlier had already deleted more code
than it added.  That habit is a day old — Henri installed it an hour
before by saying the progress was very slow and that a slice takes a
minute and its testing thirty (`doc/memory/the-slow-part-was-never-the-test.md`).
It paid on its first use.

And the question that saved the most went the **other** way: he asked
the session whether Pyodide was really needed.  A session that had just
been praised for asking would not have caught it, because it had
already written the wrong answer down as a finding.  What caught it was
someone who knew the plugin and did not believe the sentence.

**The gallery's rows, as they stand:** audio-ports, gui, params and
note-ports built; `clap.state` refused here and left with
`card:online.md` question 5, which is where its answer already lives.

## The playhead cost nothing the card had budgeted for — 2026-09-11

*"I also think I didn't see the playback head moving in the score."*
The last of his asks on `card:notes-editor.md`, and the card had priced
it as the expensive one: **the first thing here that needs a number
crossing the wire every frame rather than one per rebuild.**

That sentence was wrong, and it had stood since 2026-09-06.
`audioeditor.observe` is called once a *frame* by the view and writes
named readings into every canvas, returning them so the window's own
walk is fed from the same reading — `peak`, the spectrum bands, and the
hand's own preview have ridden it the whole time.  The playhead is one
more `put`.  Nothing about the seam changed, and the slice that was
going to be the hard one was the shortest of the day.

**Twice today a card's own sentence about its subject was false**, at
opposite ends of the board.  `card:audiovisual-gallery.md` said the
three refused pieces were its test set and one `grep` disproved it;
this card said the playhead needed a new wire and one `grep` disproved
that.  Both sentences were written by a session at a moment when they
were the best guess available, and both then sat being read as
findings.  The question harvested from the first — *which of the things
this card is about can actually take the change, and how many are
there?* — would have caught the second as well, an hour before it was
harvested.

**What was actually hard was the one thing nobody had written down.**  A
page's rolls each begin at tick zero and the transport counts from the
start of the piece, so at tick 4000 the hand is in section B and
nowhere in A or C.  Each box carries where its section starts now, and
draws at `tick - offset` only inside its own span.  A tick outside is
nothing at all — three sections showing three playheads, two of them
lying, is a picture that would have been *believed*, which is worse than
one that is plainly missing.

**And the compact box got none, by his call**, which kept the
item-identical snapshots intact and cost one decision asked before
anything was built.  The program keeps one shape either way: a box the
page gave no offset lifts over a channel nobody writes, whose initial
value is in no span.  Two shapes would have been a second thing to keep
in step, which is how this file's oldest entries all start.

`card:notes-editor.md` now has every ask he has made on it built.

## The score view was a question about knowing, not about drawing — 2026-09-11

*Henri:* **"We could try make that score view."**  The thing
`card:notes-editor.md` had held back since 2026-09-06 as *"something
unique there that doesn't exist yet … kind of a pie in the sky"*, his
to open.

**Day one was a dialogue and it took two questions.**  The first —
what is it *for* — came with three readings drawn from what the tree
already computes, and one finding put in front of them: `tools/bars.py`
has an `outside` column, and it can have one because a `.notes` section
**declares** its key and mode.  Notation software infers a key from the
notes and can then only draw an accidental; it cannot tell you that bar
3 stepped outside D lydian, because nobody told it the mode.  He took
that reading.  The second — where to draw it — he answered *a band
under each section's roll, bar-aligned*, and the alignment is what
makes it a view rather than `bars.py` on screen.

**The unique thing was never the picture.**  Every ingredient had been
in the tree for days: `sounding`, `outside`, `spell`, `degree_of`, the
mode per section in the format itself.  What was missing was somewhere
to put them, and the reason nobody else has this is upstream of any
drawing — *the file says what key it is in*.  A format decision made
for other reasons turned out to be the whole of it.

**And the sharper half was not in the question.**  Building it, the
degrees came out read against the **mode** rather than against the
tonic — in D lydian the ♯4 *is* the fourth degree and reads `4`, while
the G natural reads `-4` and lights up.  `bars.py` calls those two `♯4`
and `4`: true of the tonic, silent about the section.  The band says
the thing a player wants and the report does not, and nobody designed
that; it fell out of asking the mode rather than the key.

**The suite then caught a design error, which is the part worth
keeping.**  The band went in as generated text — 2,283 characters — and
`test_the_page_after_a_moved_note_is_a_lookup_not_a_compile` went red
at 1.58 s against a 1.5 s bound.  Not a typo: a bar's degrees change
when a note moves, so as text the band would recompile on every drag,
which is exactly what slice 3 spent a day removing for the notes.  The
band rides the notes' road now and costs the compile nothing.

That test was written on 2026-09-06 for a different reason and has now
refused a wrong design nobody was looking for.  It is the clearest
case this tree has of a bound doing what a review would not: it did not
know what the band was, and it did not need to.

**Two small decisions said out loud** rather than buried: `+` and `-`
for raised and lowered, because the canvas font has neither `♯` nor `♭`
nor any lowercase and `b7` would draw as `B7`; and a degree encoded as
one integer so the band crosses as numbers.

## The scroll stopped where the window ends, not where a person can see — 2026-09-11

*Henri, on the window, minutes after the score view landed:* **"The
vertical scroll doesn't scroll all the way down.  The status bar
appears to cover what would be shown otherwise."**

`fixme.md` **F223**, and it is the fourth of the day with one shape:
`view::canvas_scroll`'s range runs to `bottom - h`, and `h` was
`View::h`, the **window's** height.  The status row is painted over the
canvas's foot, so the picture's last rows could be brought to the
window's bottom and no further — which is underneath the bar.

**A number that means one thing, used where another was meant.**  Today
that was `Workbench.playing` (the audio thread, read as the clock),
`sounding_on` (the allocator, read as the engine), a card's own price
(a guess, read as a finding), and now `View::h` (the window, read as
what is visible).  Four defects, one habit: **taking the nearest
number that has the right name.**

And each was found the same way — not by review and not by a test, but
by somebody looking at the thing.  The suite has 763 gates and a
thousand behaviour tests and none of them could see any of it, because
every one of those numbers is *correct*; what was wrong was which
question it answered.  A test can hold a number to a value.  It cannot
hold it to a meaning, and that is what `doc/memory/test-what-a-person-would-do.md`
is for.

**What made it cheap this time** is that the fix has a name.
`View::canvas_h` — the window less the chrome painted over it — is the
sentence the clamp wanted, and it is the foot alone because the canvas
view has no piano band.  The next reader of that clamp reads a name
rather than an arithmetic, which is the only durable form the repair
has.

Driven and photographed: scrolled to the bottom, the page's last ground
row sits at y 735 of 760, and section C's caption and its harmony band
— the page's last two rows, and the newest thing in the tree — are read
for the first time.

## The canvas did not zoom, and the obvious anchor was the wrong one — 2026-09-11

*Henri:* **"I think it'd be neat if the note view would zoom along the
rest of the interface.  This isn't 'extras' but something I just
noticed that doesn't happen."**

It did not.  `font::LADDER` is a list of `(font, scale)` and its second
column is an integer the text view and the chrome have always obeyed;
the canvas walked at one size whatever the ladder said.  So the reading
his sentence takes is a **magnification** — the same thing the ladder
does to the editor's own bitmap font — and not a re-layout, which would
have meant `scorebox.editing` taking the zoom, a page rebuild a step,
and a number crossing the wire that never has.

**The interesting part is the anchor, and the obvious choice was
wrong.**  Magnifying about the window's *centre* is what everything
does and it was written first.  Two things broke.  The page's left edge
— the keyboard and bar one — was pushed off screen, which a photograph
showed at once.  And `canvas_scroll` quietly stopped being right:
its whole model is that the visible region is `[0, h]` in the span's
own units, and about the centre it is `[C - C/s, C + (W - C)/s]`, an
offset window.  The scroll's ends would have been wrong by that offset
at every zoom — a defect nobody would have found for weeks, because it
is a *limit* being slightly wrong rather than a picture being visibly
so.

About the **corner**, screen `[0, W]` is walk `[0, W/s]` exactly.  One
division, no new rule, and a score page keeps its keys and its first
bar pinned while it grows, which is the anchor a reader wants anyway.
The centre would have been defensible, correct-looking, and wrong in a
way only arithmetic finds.

**And the fifth blind oracle of the day, identical in shape to the
other four.**  The driven run measured a *keyboard* key's height, and
centre-magnification had pushed the keyboard off the left edge — so it
read `0 px` and reported a working zoom as broken.  Each of today's
five looked for the thing where it used to be rather than where the
change puts it: the page's ground, the window's pixels, a pinned state,
the allocator's list, and now the keys.  The repair every time was to
measure the thing the change is *about* — here a note, which stays on
screen by construction because the notes are what zoom.

The run also photographed `fixme.md` F208 again: at scale 2 the status
row's fields overlap plainly, which is the cheapest reproduction that
defect has had and is now written on it.

## A bound written twice is a bound that disagrees with itself — 2026-09-11

*Henri, within the hour the zoom landed:* **"The horizontal scrolling
scrolls back, rather than letting me scroll.  Noticed after zooming
it."**

`fixme.md` **F224**, and mine: the zoom converted the vertical axis to
walk units and left the horizontal alone.  The wheel clamped the
sideways scroll against `view.w / zoom`; the **paint** re-clamped it
every frame against `view.w`.  So a wheel event moved the picture and
the frame after pulled it back to the narrower limit.

**At zoom 1 the two agree**, which is the whole of why it hid — and why
the zoom's own two driven runs did not catch it.  They photographed the
frame *after the wheel*.  The defect is in the frame after **that**, so
a run that shot immediately saw a working scroll.  A picture taken at
the right moment is still the wrong measurement if the thing being
measured happens later; the fix in the harness was two seconds of
waiting.

**The repair is a name and not an arithmetic**, which is the second
time today.  `EditorWindow::canvas_seen` answers *what the canvas shows,
in the walk's own units*, and both clamps ask it — `View::canvas_h`
took the same shape for F223 an hour earlier.  Twice in one evening a
derived bound had been written out in two places and the two drifted;
twice the durable fix was one function with a sentence for a name.

**And the harness lied a sixth time.**  Its first version compared two
shots two seconds apart with the piece playing, read the *playhead*
moving as a spring-back, and reported a working scroll broken.  Six
today, one shape: an oracle answering about something other than its
subject.  The remedy has been the same every time and is worth stating
once — **make the thing you are measuring the only thing that can
move**: stop the transport, crop to the roll's band, choose a signal
that is present in one state and absent in the other.

## Two asks, and the third correction came from a photograph — 2026-09-11

*Henri:* **"I'd want the view to show notes outside of scale/mode as
yellow, and tonic note as deeper blue.  Also, I'd want a method to
create new notes by clicking."**

**The colour was a fact the page already had and was not spending.**  A
`.ges` take's note is coloured by the bank it plays through; a note-file
note has no bank the descent can see, so every one came out tone 0.
What the page knows instead is where a note sits in the mode its
section **declares** — the same thing the harmony band draws, and the
yellow is deliberately the band's own ink, because it is the band's own
fact said twice rather than two facts that happen to agree.

**The note took three corrections, and none came from reading the
code.**

`Select` never fires for a click: `hand.ges` reaches `Swept` — and so
`Select` — only through a motion, and a click is `Clear` on the press
and `Drop` on the lift.  I wrote the hook on `Select`, and a headless
test said *no note* in under a second.

The fixture built the **compiled** road, whose rolls carry no sections,
while the window draws the data road.  The guard I had written refused
correctly and the test read as a bug in the feature.  `_rolled_page`
takes `page=True` now, which is worth more than the fix: the fixture
can be the road the window actually shows.

And the first driven run made a note at tick **123**.  `_snapped` moves
an onset *by* an amount and answers the tick unchanged when the amount
is nothing — so the name was right and the call was wrong, which is the
day's whole theme in one line.  Every other gesture here snaps.  A
person would have found that one in about four seconds, and a
photograph found it in twenty.

**Where the clock went, and why it is not in the chart.**  A
double-click is a time, and `hand.ges` is a chart over touches with no
time in it.  `transport.ges` had already written the rule for this —
*a chart never asks the world; the event brings it* — so the host holds
`Session.clicked` and the chart stays what it is.  That is the second
time today an existing sentence in the tree decided a design question
that looked new.

## Four readings, four theories, and a tap that answered in one run — 2026-09-11

*Henri, the minute the first note was made by clicking:* **"The first
double-click and refresh makes the notes in the roll to disappear."**

`fixme.md` **F225**, and it is older than the gesture that showed it.
A `.notes` page's notes *are* a trace — slice 3's whole purchase, the
roll compiled once and the notes arriving as a reading — so a walker
built without them draws furniture, keys, bar lines and no music.  The
window replaces its walkers whenever the payload changes and **nothing
re-seeded them**.  `self.traces` was kept the whole time, for painting
the scope boxes.

The host does re-send on a rebuild, but it sends the **walk** and the
**reading** as two messages: a frame that takes the reading before the
queued walk hands the trace to the walker being discarded, and nothing
sends it again, because the host only speaks when the rows *change*.

**Why a drag never showed it** is the pleasing part: a drag leaves the
program text alone, which is exactly what slice 3 bought — so the
walker is never replaced and the race cannot start.  An `assert` that
puts a note **above the file's range** changes the scale, which changes
every roll's program.  The feature that made the bug reachable is the
feature slice 3 built to stop rebuilding.

**And I read the code four times and had four theories.**  The wire was
capped; it was not.  The band's recursion; emptying it changed nothing.
The second `readings` caller overwriting the first; traces are only
applied when present.  The tones; the Python walk drew all 88.  Each
was plausible, each cost minutes, and none was checkable by reading,
because **the defect was an ordering between two messages and no amount
of reading shows an order.**

So `workbench._tap` was written — eight lines, a line per message,
behind `GESTATE_WIRE` — and one run settled it: the last walk at
3000.827 and its rows six milliseconds later, both correct, both
delivered, and the roll blank.  `doc/instruments.md`'s first rule is
that a missing capability is built the moment the need arises, and the
cost of not having built it earlier was about forty minutes of theories.

**The other thing to keep.**  The driven run that *made* this feature
photographed the empty roll two seconds after the click and passed,
because it asserted on the file.  The evidence was in a picture I had
taken and not looked at.  The repair to the harness is the same one the
day has asked for seven times now: shoot **over time**, and assert on
the thing the change is about — here the notes, not the note.

## The specimen, the find, and the name — 2026-09-11

Henri asked, with the reviewer's role on, what he had found here, if
anything, and whether it was unique against what the session itself
remembered.  The conversation is `doc/notes/notes-on-the-find.md`, his
words verbatim; this is what it settled, short enough to keep.

**The tree is the specimen, not the find.**  The find, if there is one,
is a sentence of `vision.md` from 2026-08-16 — *we are missing a way to
work with each other* — and the days since on which it has not been
shown false.  Three claims branch from it and each can fall: that
continuity lives in the tree and judgment in one person's dated
corrections (`doc/method.md` §"The tree withers if it is not treated
well"); that mechanisms transfer on the first morning and judgment does
not (`doc/memory/the-third-explanation-is-a-mechanism.md`); and that
the dialogue conditions where the document alone does not
(`doc/memory/conditioning-shows-under-work.md`, one run, confound open).

**The inventor is the author, and the verb is *recognised and kept*.**
Not because he wrote the text — its authorship is shared and the record
cannot split it (`doc/memory/day-one-was-not-day-one.md`).  Because the
ingredients came from him before any session wrote them
(`doc/memory/the-prompt-log.md`, 2026-08-04; TPS, July 2026), every
dated correction in the five rule documents is his, and the tree
withers without him.  A session cannot hold a claim across a sitting,
so this is also the only name that can carry it.  *discovered, not
designed* claims what the penicillin case claims for its discoverer:
the noticing and the keeping, no more.

**Its ingredients have names, and this tree had not cited them until
today:** fitness functions (Ford, Parsons, Kua 2017), ADRs (Nygard
2011), *Living Documentation* (Martraire 2019), *Toyota Kata* (Rother
2009), Poppendieck (2003), Anderson (2010).  Grep before the page went
in: zero files for each.  What is not in any of them, as far as one
model's memory reaches, is the assembly running with a forgetting
collaborator and a ledger a stranger can check — and that claim is
unmeasured until a stranger has.  The years and names above are from
that memory too, unchecked against a search.

**What it did not settle**, and where it went: this was offered for
`spec/author.md` and he said it was too much to write there — *"Kirjoita
se journaliin suorilta"* — so it is here, and `author.md` stays as it
was.  Uniqueness is still waiting on one outsider under work
(`card:project-seed.md`, `card:stranger-test.md`), the same event
`journal.md`'s 2026-08-19 close named.  And it was a Claude session
saying most of this about a tree Claude sessions wrote;
`doc/memory/the-evaluation-loop.md` was said out loud at the start and
applies to every sentence above.

## The citations cluster by subject, and the directories are sorted by kind — 2026-09-11

`card:GraphRAG.md`, day one, run the afternoon it was minted.  The
sheet is `doc/trial/graphrag.md` and it passed `tools/prereg.sh`
before a line of the tool existed; the tool is `tools/communities.py`,
broken on purpose once (the gain's sign flipped: two cliques came back
as twelve singletons) before it was trusted.

    .venv/bin/python tools/communities.py --json          # 6 s
    .venv/bin/python tools/communities.py --written-only  # robustness

**The graph:** 776 files with a citation, 5,518 edges from 15,142
citations; 417 files cite nothing and are cited by nothing.  Louvain,
seed 0: 40 communities, the largest 127, modularity 0.454; over twenty
seeds 0.412–0.517, and the partition's own stability against seed 0 is
NMI 0.719 mean, 0.654 minimum — a loose partition, which the
written-only run tightens to 0.883.

**The decision line, as the sheet wrote it:** NMI against the
top-level directories **0.311** (seeds 0.262–0.327; ARI 0.124).  The
null — the same degree sequence rewired, twenty draws — gives 0.150
mean and **0.180 maximum**.  So: above chance, well below 0.8, and the
sheet's second branch applies: the disagreement list goes to Henri as
a lamp, and the card's query-instrument trigger stays as written.

**Three predictions, two right.**  Between the null and 0.8: yes.
Under twenty disagreements: yes, eleven.  The atlas lanes weaker than
the directories: **no** — over the 60 modules of `gestate/*.py` that
cite each other, the lanes score NMI **0.503** against the directories'
0.311, though ARI 0.086 says the match is in the broad strokes and not
in the pairs.  The hand map that matches the citations best is the one
a session drew for the atlas, not the one the filesystem gives.

**What the list says, and it is one sentence.**  Every one of the
eleven disagreements is a community that *straddles* directories, and
they straddle the same way each time: a spec, its module, its tests
and its examples together — `test 42, gestate 30, examples 30, spec
11` is the largest.  **The citations cluster by subject; the
directories sort by kind.**  There is no community that is *a
directory*, and no directory that is a community.  That is not a
defect in either: `spec/` is where a spec goes, and a spec cites the
module that keeps it.  But it says exactly what a GraphRAG-shaped
summary would be here — a page per *subject* across kinds — and the
tree has one hand-made map of that shape already, the atlas, which is
why the atlas matched best.

**Two candidate pairs**, from the written-only run only: memories that
sit alone together in one community — `gui-command-language-first` +
`identity-is-the-models-key`, and `gestate-salvage-week` +
`henri-prior-tools`.  Each pair is one subject in two files.  Whether
either is a rule stated twice is Henri's to read, not the tool's; both
are named on the card.

**Not Leiden.**  A community here may be disconnected; a Leiden run on
the same edge list (`--edges out.tsv`, then `python-igraph` +
`leidenalg` through `tools/toolbox.sh --graphrag`) is the check on
that, and the numbers above are the ones it would have to move.

## Ten files, two models, and the harness scored the first run — 2026-09-11

`card:graphrag-c.md` day one: the pilot for the subject graph.  Henri
decided C the same evening `card:GraphRAG.md` closed — *"Tehdään C, ja
järjestetään se siten että graafi on toistaiseksi vain itseviittaava"*
— so the first thing built was the door and not the graph:
`test/test_graphrag.py` refuses any citation from outside `doc/graph/`
into it, checked on a made-up index where it fails and on the tree
where it passes, before a page exists to protect.

The sheet, `doc/trial/graphrag-pilot.md`, passed `tools/prereg.sh` and
predicted five things.  Four held.  Haiku grounds 1.000 against
Sonnet's 0.975, finds 20 % fewer entities, overlaps 0.625, and costs a
sixth rather than the predicted third, because Sonnet writes twice the
output for the same file.  **The extraction pass runs on Haiku.**

**The one that failed was the cost, and the reason is the finding
worth keeping.**  The first run scored Sonnet at *0 entities* on seven
of ten files.  The model had not failed; the output ceiling of 4,096
tokens had cut its JSON in half, and a half JSON parses as nothing.
The harness reported the model's verbosity as the model's incompetence
— `doc/memory/a-run-silent-for-a-minute.md`'s lesson from the other
side: a zero is telling you about the harness first.  The ceiling is
16,384 now, the stop reason is recorded, and a cut reply says
TRUNCATED instead of counting as empty.  The thrown-away run cost
about sixty cents.

**And the judge was wrong once before the model was.**  A name that is
exactly a stripped prefix — `doc/memory/` — normalised to the empty
string and was scored as invented for both arms.  Fixed, rerun from
the cache for nothing, and the six names still ungrounded are all
Sonnet's: three re-spellings of numbers the text writes with a comma,
the card naming itself by path, and two labels coined for items of
`card:the-first-jam.md` that the card does not contain.  Haiku coined
none.  The judge found the thing it was built to find, on the dearer
model.

And one thing the API said that the sheet had assumed away: Sonnet 5
refuses `temperature`, so the two arms did not run at the same
setting.  The sheet's control said *the same parameters*; the after-run
section says where that was not true.

    python tools/graphrag.py pilot         # cached now, free
    python tools/graphrag.py check         # the door

## The sitting limit stopped a batch job, and the tool cached the stop — 2026-09-11

The extraction for `card:graphrag-c.md` was started at 20:31, four
headless `claude -p` at a time, from a session's shell in this
checkout.  At 20:48 `tools/limit.sh --hook` — the sitting limit, a
UserPromptSubmit hook in `.claude/settings.json` — decided the
sitting that began at 20:17 was over and refused every prompt after
it, the headless ones included.  Each refusal came back in 1.5 s with
zero tokens and the hook's own message as the result.  `_call_cli`
accepted it as a reply and cached it.  By 21:01 the log said 342 of
533 chunks done and `check` said 341 extracted; **276 of those were
the hook's message**.

**What found it was arithmetic.**  32 chunks at 20:44 and 342 at
21:01 is 18 a minute, and a call takes 93 s with four workers.  A run
that fast is telling you about the harness — the mirror of
`doc/memory/a-run-silent-for-a-minute.md`.  One cached reply read
confirmed it.

**Three defects, all the tool's, all repaired the same hour.**  It ran
the subprocess inside the project, so the project's hooks applied; it
took any exit-0 JSON envelope for an answer, so a refusal with no
tokens was cached as an extraction; and its pid file held `$!` of a
`nohup` line, which was the shell, so the scheduled kill at 21:00
stopped the shell and left the run going until it was killed by hand.
Now the subprocess's working directory is the cache directory, a
reply without output tokens or an object in it is retried and then
fails out loud and is never cached, and the tool writes its own pid.
The 276 were purged; 71 real extractions stand.

**The sitting limit was right.**  It stopped a session nobody had
told it was not a person, at the minute it was built to, and the
mechanism held against a batch job that its author had not imagined.
`doc/memory/headless-claude-inherits-the-hooks.md` carries the rule;
the memory's own wording is that the defect was the tool's, not the
limit's.
