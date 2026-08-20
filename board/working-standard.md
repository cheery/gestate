# working-standard — the way we work exists only as prose that grew around a music program

    status   doing — 2026-08-20
    because  "standardization effort of our work here" — the method that
             runs this project is spread over five documents and some
             1,550 lines, with one rule stated three times inside a single
             file, and nothing states it apart from gestate; a second
             project would re-derive it by hand or copy this repository
             and delete the parts that do not apply
    asked    Henri, 2026-08-18 (Claude wrote the card at his ask)
    see      card:project-seed.md — what this exists for
             board/README.md — the largest single piece of the method
             spec/author.md — what the author spends attention on
             doc/instruments.md — what a session already has to work with
             manifesto.md — how an instrument fails
             vision.md — what any of it is for
             card:interface-oracle.md, card:carried-state.md,
             card:driven-runs.md, card:cheap-gates.md — the four
             workflow cards; the raw material, not absorbed
             spec/rules.md — the cap, and what may not be done to meet it
             tools/rulecount.py — the number, and test/test_rules.py the gate

**Picking this up?  §"Back on the board, 2026-08-20 — the cap" is the live
half**; everything above it is how the card was argued into shape while
it was shelved, and none of it has changed.

## The ask

> We need two cards that are interrelated. standardization effort of our
> work here, and a template for new projects.

And, once the scope had been argued:

> I wonder if working-standard also involves fixing all the issues we
> have right now, and reorganizing our current resources into that
> living standard it needs to be, which then lives with us.

## Shelved, 2026-08-18

*Henri:* **"I want the cards made for this to go directly into the
board/later/ because they aren't current."**

And a second reason, found while elaborating and worth more than the
first: **the method is still moving.**  In the three days before this
card was written, the board changed its own rules three times — a
session may mint a card (2026-08-18), `later/` was invented for
displaced cards (2026-08-17), and commit titles stopped being Henri's to
give (2026-08-17).  Writing the standard this week would standardize a
draft, and a standard is expensive to change precisely because other
things start depending on it.

It comes back when the method stops changing, or when
`card:project-seed.md` forces the question — whichever happens
first.

## Found by looking

**Five documents, 1,554 lines** *(measured 2026-08-18)*, not counting
`roadmap.md`, which is the argument rather than the method:

| file | lines |
|---|---|
| `board/README.md` | 483 |
| `manifesto.md` | 408 |
| `spec/author.md` | 379 |
| `doc/instruments.md` | 210 |
| `vision.md` | 74 |

**And the duplication is real, not aesthetic.**  The two-writers rule —
*two writers never touch the same file* — is stated three times inside
`board/README.md` alone — deliberately, each time arguing for a
different rule, which is exactly how three statements of one rule come
to exist and is why no line numbers are given here: they rot, and this
paragraph rotted its own within the hour it was written.  The andon is
explained in five separate documents.  A rule stated three times is
three things that can drift apart, and nothing in the suite compares
them.

That is the concrete target behind *"reorganizing our current
resources"*: one rule, one place, and the other places citing it.

## The scope, as far as it was settled

Three readings were put to Henri with what would kill each; he took the
second.

1. **Consolidate and make executable.**  One rule, one place, enforced
   by the suite the way `test/test_board.py` already enforces the
   board's own contract.  Bounded and finishable.
2. **Consolidate, plus fix the method's known defects.**  Chosen.  The
   four workflow cards above *are* the issues in how the work is made,
   and they were already on the board when this was written.
3. **Fix all the issues.**  Rejected: twenty open F-numbers and the
   whole live board.  A card that contains the board is the board, and
   it could never be finished, so it could never leave `later/`.

**The four cards are named, not absorbed.**  Merging them into this one
would save four lines on the board and cost four ids that are already
cited from tests and other cards — and `board/README.md` is explicit
that the filename is the id and a citation must keep resolving.  So they
stay as the units of work; this card is what they add up to.  Reversing
that is one line, and it is Henri's line to write.

## The word doing the most work

*"which then lives with us."*

A standard that is written and not enforced becomes the sixth document,
which is the failure this project already knows and has already
designed against: a rule that lives in the window holds only for people
using the window — not for a collaborator with a different editor, and
not for a session that writes files with tools.  So whatever this card
ends up covering, **the test of it is that the suite can fail on it.**

## Questions

*Open, for whenever it is unshelved.*

**1. Is the standard a document, or a directory?**  A document is read
once and drifts.  A directory a new project copies — a `board/` skeleton,
a `test_board.py`, an empty `fixme.md` with its legend, a `vision.md`
with nothing but its own instructions — is a thing that starts working
on day one.  This is the question `card:project-seed.md` is
really about, which is why the two cards are one decision.

**2. Does it absorb the four workflow cards?**  Written as *no*, above.

**3. Does the questioning survive the move?**  `board/README.md`
§"Question it into existence" was added on 2026-08-18 at Henri's ask —
*every* card questioned before it is written — and it is the piece of
this method most likely to be dropped when somebody is in a hurry in a
new repository, because it costs a conversation and produces nothing
visible until the card is better than it would have been.  It is also
the piece that most changed what got built here.  Whatever a seeded
project inherits, this is the part to check for.

**4. What is deliberately gestate-shaped and must not travel?**  The
music, obviously.  But also, probably, the F-number scheme's history,
the specific instruments in `doc/instruments.md`, and the parts of the
manifesto that argue about audio oracles.  Separating those is most of
the work, and it cannot be done by a session guessing.

## What the standard has to carry, collected as it arrives

*Written into this card as Henri says them, so that unshelving it does
not start from a blank page.  None of these is being worked.*

### `fixme.md` wants the treatment `roadmap.md` got — 2026-08-18

> *"I'm reading the ungated-fixes and thinking the fixme is really good
> practice although it started as a list I had to fix remaining things
> and I were just lazy and did forget it on the disk.  It tells us
> immediately information that we otherwise would not know, such as, how
> many were fixed without a test checking that it never comes back.
> Though, it might need same treatment as the roadmap.md got and change
> into a directory.  I refrain from doing that though.  it belongs into
> a standard practice as a directory."*

**And the origin is worth keeping rather than tidying into a design.**
It began as a list of leftovers on the disk and became the instrument
that told this project how much of its own repair work leaves nothing
behind.  That is the same shape as `card:gemba.md` and the andon: the
practice arrived before the reason for it.

The concrete argument, from the day it was said: the 79-of-161
measurement in `card:ungated-fixes.md` had to be made by **parsing
prose**, and it is a proxy the card had to label *suspected* rather than
shown.  One file per entry with a `gate:` field turns it into a lookup —
and turns that card's third question, *does the suite enforce it*, from
an open design problem into a test that reads a field.  A `[resolved]`
entry with an empty `gate:` would fail the way a card with no `because`
fails now.

What the single file gives that a directory would not is the thing that
prompted this: **somebody read it end to end and noticed something.**
Nobody reads a board that way.  Worth answering rather than assuming
away.

### The recipe is four documents, found by running it — 2026-08-20

> *"if I take doc/author.md, manifesto.md vision.md board/README.md they
> form the basic recipe that reproduces something in a claude chat. (the
> talk with fable happened that way)"*

**Those four are the five capped documents minus `doc/instruments.md`** —
the one document he had already ruled untransferable on 2026-08-18
(*"some specific instruments that belong to this project are not
transferable, but they can be examples"*).  He dropped it by experiment,
without consulting that answer.  A replication rather than a
coincidence, and it is the first evidence this card has about its own
scope that was not an argument.

**And it is a measurement of the seed, not of the standard.**  What it
shows is that four documents are enough to reproduce the method *inside
one conversation*.  His own doubt is the whole open question: *"I'm not
sure I have all the pieces for long living version yet.  Maybe we should
research this."*

The gap is nameable already, and it is this card's §"The word doing the
most work": a chat can carry the rules and **cannot fail on them.**  No
board that persists, no suite, no `doc/memory/`, no hook at the commit.
Four documents transmit the method; nothing in them enforces it once the
window closes.  So the research question is *what survives the end of a
conversation*, and the candidates are all in this tree and all younger
than the documents: `board/` as files, the gates, `doc/memory/` (which
arrived 2026-08-20), `tools/pre-commit.sh`.

*Not being worked.  Recorded here because it arrived, per this section's
own rule.*

### And the board's own shape was questioned the same afternoon

Answered rather than deferred — `card:` notation, above — but the
question generalises and belongs here: *which of these records wants to
be a directory, which wants to be a file, and what decides it?*  Three
have been through it now (`roadmap.md` → `board/`, and `fixme.md`
proposed), and nobody has written down the rule they were each following.

## The questions, answered — 2026-08-18

*Henri read the card while it was being written and answered all four.
Kept in his words; the card stays shelved, and he said how long for.*

**1. A document, or a directory?**

> *"it must be a directory.  I used the spec/ for a long time.  see at it
> now.  It's a mess but it's full of critical information.  We would
> perish without it."*

**And the evidence he points at is the strong form of the argument.**
`spec/` is twenty-odd files, unevenly maintained, and indispensable — a
directory *tolerates* mess without losing its value, because nobody has
to read it end to end to use one file of it.  A single document with the
same mess in it becomes unreadable, which is precisely what happened to
the old `roadmap.md` and what `board/` was carved out of.

So the standard is a directory, and that answers the shape of
`card:project-seed.md`'s first question too: what a new project inherits
is **something it copies**, not something it reads.

**2. Does it absorb the four workflow cards?**

> *"Nope.  And it will take time until we can done/ this card."*

Which the card already assumed, and now has behind it.  The second
sentence is the more useful one: **this is not a card that gets
finished soon**, so anything urgent inside it does not belong to it.
That is the test to apply to every note collected above — if it cannot
wait, it is not part of this card.

**3. Does the questioning survive the move?**

> *"Question into existence is critical if if prevents us to accumulate
> cards like crazy."*

**Note the condition — he did not say it is critical, he said it is
critical *if* it works.**  So the rule travels with a measurement
attached rather than as doctrine, and the measurement is the arrivals
rate: nineteen cards in two days is what made `later/` necessary; three
cards in a day where two arrived shelved is what it looks like when the
filter holds.  A seeded project should carry the number, not just the
practice.

**4. What is gestate-shaped and must not travel?**

> *"music, the F-number scheme is good.  Some specific instruments that
> belong to this project are not transferable, but they can be
> examples."*

Three separations in one line:

* **The music does not travel.**  Which is the whole domain half —
  `spec/` on scores, the audio oracles, the golden `.samples`.
* **The F-number scheme does.**  Numbering-as-addresses, entries that
  are never renumbered and never deleted, `[resolved]` as what closing
  looks like — that is a mechanism with nothing musical in it.
* **The instruments travel as examples, not as code.**  `tools/andon.sh`
  rings a sound card because this project has one; a project without
  audio needs a cord, not that cord.  What transfers is *that a session
  must be able to reach the author*, and this one is the worked example
  of it.

## Back on the board, 2026-08-20 — the cap

*Henri, 04:52, after a few minutes with another model:* **"We need a cap
for rules here.  2000 lines, for now, and rules must be still written
cleanly, and marked by dates, no cheating there.  without this, the
context needed grows too large for context window to hold it."**

And, once the count was on the table: **"we have to take the
working-standard into WIP.  Now it's time."**

So this card is `doing`.  The contract is `spec/rules.md`; it is a spec
rather than a sixth rule document, at his call — *"spec/ is ok.  I
think… it tells about contracts written in software.  This thing should
be specced as well."*

**What unshelved it is a number.**  The card's own measurement on
2026-08-18 was 1,554 lines across four documents.  Measured the night
the cap was set, the same four are 1,976 and the five are **2,050** —
**+422 lines in two days**, with `doc/instruments.md` more than doubled,
210 → 457.  The cap was breached before it was written.

The shelving reason on 2026-08-18 was that *the method is still moving*,
and it still is.  That argument has been overtaken rather than refuted:
the method may keep moving, but it may not keep **growing**, and the
second is now measured while the first is not.

### What the trim is

**Session narration** — Henri, 2026-08-20: *"The rules have gotten
narration from sessions that belongs into the journal."*

Which names the fat precisely, and it is fat this card had already found
from the other end: a rule stated three times in one file, the andon
explained in five documents.  The test for a line is whether a stranger
who never saw the incident needs it in order to **follow** the rule; if
they need it only to **believe** the rule, it is `journal.md`.

The three cheats are settled and written into `spec/rules.md`: a sixth
document, dropping dates, and moving text from one rule into another.
Two of them are Henri's words from tonight.

### First steps, in order

1. ~~**Get under 2000**~~ — **done 2026-08-20, at 1,983**, 17 lines of
   room.  `doc/instruments.md` 457 → 404, `board/README.md` 704 → 686.
   What the trim found first is that it was not only a trim: the blind
   three-model test of 2026-08-19 had **no journal entry**, so the
   instruments page was carrying an entire morning as the price of
   stating four rules about spawning agents.  A transfer, not a
   deletion — `journal.md` §"The morning that lived in nobody's file".
2. ~~**Wire `tools/rulecount.py` into `tools/suite.py`'s `GATES`**~~ —
   **done the same morning**, as `test/test_rules.py`.  Eleven gates,
   twelve seconds.  **And then made an andon rather than a refusal**, at
   his ruling: *"make it light the andon."*  Going over the cap is now a
   red section on `test/gates.md` and a banner at every commit, and it
   fails nothing.  The suite still refuses the *loss* of one of the five.
   The reason is in `spec/rules.md` §"The proof": a gate that blocks a
   genuine amendment teaches the next session to make the method worse
   in smaller words.
2b. **And the memory corpus came into the tree** the same morning, at
   his ask — `doc/memory/`, split by kind, gated by
   `test/test_memory.py`.  It is question 1 of this card answered by
   example: the standard is a directory, and this is the first piece of
   it that a second project would copy.
3. Then the card's original scope — reading 2, consolidate and fix the
   method's known defects — resumes, now with a ceiling it has to work
   under rather than an argument about size.

*Nothing here is committed.  Written at five in the morning, at his ask,
so that it was not his to carry back to bed.*
