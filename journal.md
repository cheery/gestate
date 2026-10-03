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

**The weekly account** — *adopted 2026-09-23, at Henri's ask:* *"jatketaan
notes-editoria, mutta ensin me tarvitaan se kronologinen kertomus joka
kirjoitetaan journaliin sitä mukaan kun edetään.  Viikko kerrallaan."*
One `## Week NN — <monday> to <sunday>` section per ISO week, at the
bottom of the open month, written as the work goes and not after it.
*His, the same day:* *"Jokaisella viikolla tästä lähtien kuuluisi olla
rakenne, joka mm. alkaa tavoitteella ja teemalla."*  So:

* **Theme.** — what the week is about, one line.
* **Goal.** — one sentence, written before the work, that the week's
  end can be read against.  His to set or correct.
* **The days**, in order, a few lines each, pointing at the commit or
  the card section that holds the detail.
* **Outcome.** — once the week is over: the goal met or not, with the
  number where there is one, and what carries into the next week.

`test/test_journal.py` holds the shape: theme and goal before any day,
and a finished week has its outcome.  The entries named for what they
taught stay beside it; the weekly account is what happened, in order.

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
| [2026-09](journal/2026-09.md) | 3,830 | the ungated sweep closed (batches 10–13); backlinks, the flow lamp, the ledger a directory; the notes editor from editing scale to 117 ms; transport and the hands as charts; the GUI card — identity, facts declared, the notes as a relation; graphrag's sheets; types and staging in the language; the signals trial; one card at a time and the weekly account; snap-grid |

*The open month is 2026-10.*  `python tools/journalroll.py` says where the
lines are and whether the rotation is due; `spec/rules.md` §"The journal
rotates" is the contract, and the rotation is an act of the fire, not of a
gate.

---

## Week 40 — 2026-09-28 to 2026-10-04

**Theme.**  When a value is read — the reactor model and graded types
read against the tree, and `card:snap-grid.md` brought to its close.
*The session's proposal, his to correct.*

**Goal.**  *The session's proposal, written Friday with the week half
gone:* `card:snap-grid.md` closed against its postcondition at his
word, or its remaining gap named as a number — so that the next card is
chosen by the board's filter and not by the morning's conversation.

**Monday 28.9 to Thursday 1.10.**  No work.

**Friday 2.10.**  He brought the reactor paper (Lohstroh et al.) and
asked two things: where it would shine here, and whether gestate could
already be tend's systems language.  The place he had in mind was the
GUI.  Then his hunch — graded modal types giving the reactor's
guarantees inside an effect monad — and the two grading papers fetched
(Orchard, Liepelt and Eades; Gaboardi et al.).  Twoknobs graded by
hand: reads as coeffects, writes as effects, one synchronous rule; both
wrong drafts rebuilt from the record, 1 and 64 of 800
(`python tools/signalcase.py drafts`, `5833b59`).  Then, at his word,
the grader — `tools/grades.py`, every `scanE` step run symbolically —
which found bounce's explicit Euler as a stale read the hand grading
had missed, and merged the hand's *refused* and *unwritable* into one
class (`b38fb8f`, `doc/trial/signals.md` §"The grader, built").  Week
39 closed *met* at his word and September rotated; the rotation found
two defects in `tools/journalroll.py` — earlier months' themes lost,
and the weekly account's contract inside the generated block — both
fixed and held (`9bfcfeb`).  And his remark at the end: *"finding out
about the reactor model probably changes things here."*  Then his hands on
`card:snap-grid.md` — *"it holds, close snap-grid"* — and the card to
`done/`; the week's goal met the same day it was written.  Then, at his word, the reading behind the GUI card: Lingua Franca
(Lohstroh's thesis), relational lenses, modal reactors — and the first
slice built from it, two checkboxes as `reactor` blocks desugared into
signals (`e5cd33e`, `card:gui-is-difficult.md` §"Built — two checkboxes
as reactors").  It works, every check refuses what it should, and the
measure is honest: no reduction for checkboxes, which the tree's facts
and `Does` already composed.

**Saturday 3.10.**  The seven-day lamp first: `strict-forms`,
`relational-model` and `gex-sheet` to `later/` at his *"defaults are
fine"*.  Then the small things before the next slice, at his word —
F243's half-open edge in both walkers (and a second copy of it in the
roll's probe), F244's one-line `case`, and the formatter reading
`reactor` blocks and `include` lines, which made five files readable and
showed a comprehension guard written back unparseable; repaired, three
files off F191 (`715ecab`).  Then the slice he chose, (a): a drag, as a
reactor with a stored mode.  Before any code it found the substrate
could not commit on a release, and he took the new attachment —
*"(1) sounds right, go ahead"* — so `Holds` went into both walkers and
every shell's table, stored modes into the reactor desugaring with a
hold channel and a mode per instance, and `examples/gui/drag.ges` drags
three dots over a file it writes only on the release.  On the way, the
host's `Retract` was made to take a key as the library already said it
did, and F246 ledgered.  The measure moved this time: 3 places against
6 to add a fourth dot, 7 composition lines against 17
(`card:gui-is-difficult.md` §"Built — a drag, as a reactor with a stored
mode").  Then his hands on it: *"the drag works."*  Then, at his *"go with the notes editor"*, the first real port
of a piece of it — expectation 14's trigger.  The note hand (363 code
lines today, `hand.ges` and eleven `session.py` methods) went into
`examples/gui/carry.ges`: a bank of `Note` reactors over `tune.notes`,
`Holds` given the key a press lands on, `MoveTo` and `Reveal` acts the
host performs by retuning the note's own line, and a `.notes` read as
rows rather than expanded as a score.  On the way it found F247 — a
canvas with a score and no bank could not compile `Voice` in either
half — and four names the library already owned.  It carries, clicks,
refuses what the file cannot say, and follows a hand edit.  **The
measure: 0.25, not under 0.10** — 50 lines of hand against the 202 it
covers (`python doc/trial/reactors/notehand.py`), about 0.19 if the
port's own drawing is left out as the baseline's is.  A fourfold
reduction; the order of magnitude was not there on this piece
(`card:gui-is-difficult.md` §"Built — the notes editor's note hand").  His
reading: *"fourfold reduction is nothing to sneer at"*; and his hands on
it, *"it worked."*
