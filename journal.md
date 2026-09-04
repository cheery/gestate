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
