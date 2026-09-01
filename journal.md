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
