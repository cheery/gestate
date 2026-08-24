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
             card:who-asked.md — one instruments.md entry is queued
             behind this trim; §"What it waits on" holds it written
             tools/rulecount.py — the number, and test/test_rules.py the gate

**Picking this up?  §"Back on the board, 2026-08-24 — the deliverable is
the audit" is the live half**, and it overtakes the cap section before
it; everything above those two is how the card was argued into shape
while it was shelved, and none of it has changed.

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

### The documents assume an environment, and never say which — 2026-08-20

> *"If I run an environment where the README's promises do not fullfill,
> it can cause disappointment to the session.  The conditioning doesn't
> disappear, but it gets the shape of being betrayed."*

**Said the evening it was measured.**  A 9B model was handed
`board/README.md` and nothing else, in a `llama.cpp` CLI with no tools
and nobody answering — journal.md §"Two small models read the board, and
the document is what lifted them".  That document promises a reachable
author, an andon that rings him, tools to go and look with, `status
blocked` as a real move, and questions collected and answered in one
sitting.  **Every one of them was absent.**  What came back was four
widening retries against silence, and then text about having been
betrayed.

**The rule is stronger without the word *disappointment*, and the
standard should carry the stronger form.**  Put as a feeling it rests on
a claim nobody can settle about what is on the other end.  Put as a
mismatch it rests on nothing: *a document that promises affordances the
environment does not have produces off-shape behaviour* — and that is a
defect in the environment either way.  The observation is Henri's; the
restatement is the session's.

**What it costs this card.**  The four-document recipe above is a
*portable* method; that is the whole point of it and of
card:project-seed.md.  But those four documents name instruments —
`tools/andon.sh`, gemba, the driven harness, the suite gates,
`doc/instruments.md` entire — and a board with a person filling it, and a
review channel that answers.  A new project receives the prose and none
of the machinery.

So the seed either **states its assumptions** — what a receiving project
must already have for these promises to hold — or it **ships the
affordances**.  Those are different amounts of work and it is not
decided here.  What is decided is that a method document leaving this
tree without that statement is shipping promises the receiving project
cannot keep.

### The standard is a directory, and the point of it is the audit — 2026-08-22

> *"I did find out yesterday evening that these methods of summoning
> sessions are being reinvented by other people, and in much less safe
> way.  We may need to look at the card:working-standard.md and then
> card:project-seed.md.  I feel that the exact mechanism you condition
> with is not as important as getting an auditable version with
> necessary pieces filled into the directory."*

**This answers Question 1 — document or directory — and it answers it
for a reason the question never considered.**  The card argued the
directory on the grounds that it *starts working on day one*.  He is
arguing it on the grounds that a directory can be **audited**: the
pieces are slots, a slot is filled or it is empty, and an empty one can
be seen from outside by somebody who never read the prose.

**And it demotes the expensive half of this card.**  Question 4 —
*what is deliberately gestate-shaped and must not travel* — was written
as "most of the work, and it cannot be done by a session guessing."  If
the deliverable is auditability, that work stops blocking: **the content
of the conditioning can be wrong and the directory still audits, while a
directory with perfect content and no audit cannot be checked by anyone
at all.**  An auditable wrong version is repairable.  An unauditable
right version is a claim.

**It is also a third answer to §"The documents assume an environment"**,
which left the seed choosing between *stating its assumptions* and
*shipping the affordances* and called them different amounts of work.
The third is: **ship the slots and the check.**  A seeded project has a
place for a fence, a gate, a register, a reachable author — and a test
that says which of them are empty.  Then the four-document recipe stops
being a method that transmits and cannot fail, because the failure moves
into the directory's own suite.

**What is not decided, and it is the whole design.**  *Which* pieces are
necessary.  The tree has candidates and they are not the same list as
the failures he saw:

| the piece here | what it is for | already checked by |
|---|---|---|
| the fence — `.claude/**` denied to a session | the model cannot edit its own restraints | `tools/sandbox.sh --check` |
| the gates, and the commit hook | enforcement outside the model | `tools/suite.py --gates` |
| `doc/consent.md` | a named third party agreed | `test_consent.py` |
| the andon, and a board `status blocked` | a session can raise a question and be answered | nothing |
| `spec/rules.md`'s cap | the rules stay readable | `tools/rulecount.py` |
| `doc/memory/`, split | what carries across, and what stays private | `test_memory.py` |
| `tools/limit.sh` | the person's own hours | nothing |

**Answered the same morning, and it is not this tree's list.**

> *"We aren't smart or super.  We just have good processes.  The unsafe
> part about what I saw, was that nothing in the ruleset it had, did not
> encode respect toward people and others.  Also, it relied on unchecked
> processes."*

Two failures, and they are the two halves of what the audit has to look
for.

**One: a ruleset with no obligation toward people in it.**  Operationally
complete, and nothing in it is there because somebody is on the other
end.  This cannot be audited as a sentiment — no test reads a document
and finds respect.  **It can be audited as affordances**, because in this
tree every piece of it is a file that exists for no other reason:
`doc/consent.md` because a third party has to agree; the andon and
`status blocked` because a session must be able to raise a question and
be answered; `doc/memory/`'s split because some of what is known about a
person is not the tree's; `tools/limit.sh` because his hours are his;
`spec/author.md` staying his to keep.  Take away the people and every one
of those is dead weight.  **That is the auditable form of the thing he
says was missing: not "does the ruleset say respect", but "which of these
pieces does the directory have, and is anything behind them."**

**Two: unchecked processes.**  The ratchet, stated from the other side —
a rule with no gate is a wish, and a directory of wishes reads exactly
like a directory of rules.  So the second half of the audit is per-rule:
*what fails if this is violated, and can it be named.*  This project can
already answer it for some rules and not others; the table below is
honest about which.

**And the two failures are one failure in this tree's own record.**
§"The documents assume an environment, and never say which", above, is a
respect-failure that was found as a mismatch: `board/README.md` promised
a reachable author, an andon, tools, and answers, and a 9B was placed
where none of them existed.  Nobody had to judge the promises — the check
is *does the affordance exist*, which is exactly the check his two
failures need and the one thing an outsider can run without reading the
prose.  **That measurement is now the strongest argument this card has
for the directory-plus-audit shape, and it was taken for another
reason.**

**One line of his belongs on the front of whatever ships:** *"We aren't
smart or super.  We just have good processes."*  A seed that travels as a
conditioning recipe invites the reading he is warning about; a seed that
travels as processes with checks does not.

**The list above is this project's pieces, and it is still the wrong way
to build the check.**  A seed audit assembled from what this tree happens
to have would encode gestate's accidents as requirements.  His two
failures are the criterion; the table is the raw material to be filtered
through them, and the column that matters is the third — five of the
seven pieces have something that fails, and the two with nothing are the
andon and the limit, which are the two most about people.

**Built and run, 2026-08-22, at his ask.**  `tools/seedaudit.py`, against
this tree, because there is no seed directory yet and a check written for
one would be a guess about a thing that does not exist.  It takes a path,
so it can be pointed at a copy the day there is one.

Two checks, one per failure:

* **The pieces that exist only because a person is on the other end** —
  present, and does a test name them.
* **The promises** — every path the five capped documents name, resolved
  against this directory.  That is the 9B mismatch made runnable by
  somebody who never read the prose.

**The result: 9 of 9 present, 0 unkept promises, 2 unbacked — the andon
and the sitting limit.**  The two pieces with no test behind them are the
one that lets a session reach a person and the one that protects the
person's hours: the two most about people are the two least checked.
That was said from reading before the tool existed, and the tool agrees.

**Unbacked failed nothing for the first hour, and now it does.**  On the
morning it was built the tree would have gone red on its own audit, and
a check nobody can leave green gets switched off — `manifesto.md`'s
argument about how an instrument fails.  So the two bare pieces got
tests: `test/test_andon.py` and `test/test_limit.py`, written the same
morning at Henri's ask, and then the ratchet was pulled.  **9 of 9
present, 0 unbacked, 0 unkept promises**, and from here a piece added
without a test fails the suite.

**The order is the point and it is worth stating as a rule for the
seed.**  A gate is turned on after the tree is clean, never as a way of
announcing that it should be.  A red check that everyone learns to
ignore has done more damage than the missing check it replaced.

*What the two new tests actually pin.*  The andon: the cap of three is
checked instead of asserted in a comment, a typo refuses out loud rather
than ringing zero times and exiting clean, and a ring that never reaches
the sound card exits non-zero — the worst available failure for a cord
being that a session pulls it, nothing sounds, and the status says fine.
The limit: that `reset` is refused inside a session, that a question
merely *mentioning* `sitting 90` is not a grant — otherwise a session
could put the words in his mouth by quoting them — and both defects the
previous session found by running it, which `bash -n` had passed.

**And the audit's harvester was wrong three times before it was right**,
each time in the direction that made the tree look good: it searched
`tools/`, so every tool named itself and all nine passed; it called
thirteen present files unkept promises because the documents write
`test_board.py` without its directory; and then its own test file backed
the paths it names, so the andon went green by being discussed.
`card:dangling-names.md` in one morning, three times — *the experiment
did not test the detector, it tested the harvester.*  The third was
caught only by a canary test asserting which pieces are bare, which is
the argument for keeping such a test even though it fails on good news.

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

## Back on the board, 2026-08-24 — the deliverable is the audit

*Kaizen with Henri, 2026-08-24 — `journal.md` §"Kaizen, 2026-08-24 — nothing stopped the run".
He opened with "the last tests have been abysmal" and "I feel the
solution to the standard is simple, but we don't just know it yet."*

### The cap's premise was measured false, and the card was not told

`journal.md` §"Nothing was loading the rules" (2026-08-23): **nothing
loads the five capped documents.**  What reaches every session unasked
is the memory index — 57 lines, uncapped, private, written by sessions —
and since 2026-08-23 the one-line pointer, which this morning's session
confirms *does* arrive at a top-level session (`CLAUDE.md`, Henri's
symlink to `AGENTS.md`, 03:46) and the probe showed does not reach a
subagent.  So steps 1–2 above held a budget on the surface that
conditions least.  `python tools/rulecount.py` is 1999 of 2000 as this
is written; the number stays measured and the andon stays wired, and
**step 3 does not resume as written**.  What replaces it is below.

### What the standard is

Three lines from three days, never joined until now:

* Henri, 2026-08-22: *"the exact mechanism you condition with is not
  as important as getting an auditable version with necessary pieces
  filled into the directory."*
* This card's §"The word doing the most work": *the test of it is that
  the suite can fail on it.*
* The seeding trial, 2026-08-23: what travelled was mechanisms plus the
  evidence that paid for them, taken on need; five arms declined the
  prose in writing.  *"The tree may not have a payload so much as a
  shelf."*

**The standard is the slot table — each piece, what it is for, and what
fails if it is missing.**  That is `tools/seedaudit.py`'s `PIECES`, and
it is the one artifact in the tree that already meets the definition
this card set for a living standard.  The five documents are *gestate's
filling* of the slots — the examples, exactly as Henri said the
instruments travel on 2026-08-18.  The cap, the trim and the
consolidation are housekeeping on the examples.

**One slot was missing from the table, and it is in now** — *the boot
surface*, the pointer that arrives before a session asks for anything.
Henri's `why`, 2026-08-24, verbatim in `PIECES`: *"nothing else reaches
a session unasked."*  Its path is `AGENTS.md`; the memory index that
shares the slot lives outside every directory, which the audit cannot
see and this card says instead.  Ten pieces, 10 of 10 present, 0
unbacked.

### Why the tests were abysmal

Every trial since 2026-08-21 asked *does the prose condition a reader*
and got the same answer three times.  And the execution failed on its
own: no valid control (subagents inherit the parent's memory — both
2026-08-23 controls quoted house rules they never read), n = 1 per arm,
marks drawn from the board's own subjects so that declining a board for
a tar library scored as unconditioned, and constraints stated in prompts
and enforced nowhere.  `doc/trial/README.md` §"What would make the
result void" named n = 1 and the weak control on 2026-08-21, and three
sheets were written and run past it.  **Henri's half of the kaizen: the
fault was that nothing on either side stopped a run whose own sheet said
it could not decide** — not the wrong question.  The mechanism is
`tools/prereg.sh`, `doc/trial/README.md` §"Before any arm starts".

### The mutation run — the audit tested, 2026-08-24

The right test of a standard that can fail is not to hand it to a model;
it is to take a piece away and see whether the audit notices.

    tools/seedmutate.sh

**Finding one, before any mutation: a `git archive` of HEAD is red on
its own audit** — five unkept promises, all *generated*: `test/gates.md`,
`test/report.md`, `test/coverage.md`, `target/release/`,
`shell/editor/target/release/`.  The audit cannot tell a broken promise
from an unbuilt one, so a fresh clone, which is what a seed is, fails
for reasons that are not defects.  The sweep copies the working tree
and says so.

**Finding two: every piece removed is caught; what survives is removing
the *test* behind a piece.**  At nine pieces, three survived —
`test/test_limit.py`, `test/test_rules.py`, `test/test_complaints.py`;
at ten, two, because the boot surface is backed by `test_rules.py`
alone and so its loss now shows.  The cause is that `backed_by` accepts
any test file that *mentions* the path, and `test_provenance.py`,
`test_citations.py` and friends cite those paths without gating them.
The docstring's own admitted weakness, *mention is checkable,
correctness is not*, now has a number.

**Fixed the same day, the `gate:` way.**  Each piece in `PIECES` now
declares the one test file that gates it, and `backed_by` reads that
file alone.  What that turned up on the way: `tools/pre-commit.sh` was
named by **no** test — "the gates" had passed on a mention of
`suite.py` — so `test/test_precommit.py` came first, per §"The order is
the point", and only then the tightening.  `tools/seedmutate.sh`: **0
survived**, and the sweep's own first version reported one survivor
that was its hand-typed list naming a gate no piece declared any more
— the list is read from `PIECES` now.  The in-process half,
`test_seedaudit.py::test_taking_any_piece_away_is_seen`, is a suite
gate; the thirteenth.

### Next

1. ~~Henri words the `why` for the boot-surface slot~~ — done the same
   morning, above.
2. ~~`backed_by` tightened until `tools/seedmutate.sh` reports 0
   survived, and then the sweep joins the gates~~ — done the same day,
   above.
2b. ~~The audit's *promise* half still cannot tell an unbuilt promise
   from a broken one~~ — done the same afternoon.  `.gitignore`'s
   own first line, *ignore what a command can make again*, is the
   distinction, and all five were already under it with their reasons
   written beside them.  The audit reads every `.gitignore` in the
   copy (a seed need not be a repository, so not `git check-ignore`)
   and reports a missing, ignored promise as **unbuilt** — printed,
   never failed on.  A `git archive` of HEAD now audits **10 of 10,
   0 unbacked, 0 unkept, 5 unbuilt**, and `tools/seedmutate.sh` sweeps
   that archive rather than the working tree, which is what a clone
   actually gets.
3. ~~The four workflow cards stay as they are; reading 2 of the scope is
   unchanged~~ — **measured done, 2026-08-24, after the commit.**  Both
   halves of reading 2 were already finished and the card had not been
   told.  *Fix the method's known defects:* all four cards are in
   `board/done/` — `interface-oracle` 2026-08-18, `carried-state`,
   `driven-runs`, `cheap-gates` 2026-08-19.  *Consolidate — one rule,
   one place, the others citing it:* the two targets §"Found by
   looking" named on 2026-08-18 were consolidated by the 2026-08-20
   trim without being marked.  The two-writers rule is stated once
   (`board/README.md` §"Who writes what") and applied once, by
   citation, in §"The suite is a serial gate"; the andon is explained
   once (`doc/instruments.md` §"`tools/andon.sh` — ring the sound
   card") and the other four documents name it in one line each or not
   at all — `grep -ci andon`: 3, 1, 1, 5, 0.

### What is left, and whose call it is

Nothing on this card is being worked.  What it set out to do on
2026-08-18 — a standard that lives with the work, that the suite can
fail on — is `tools/seedaudit.py`, ten pieces with declared gates,
tested by mutation, a suite gate, reading the tree's own rule for what
is built by a command.  The cap is measured and its meaning corrected.
The defects are closed.  The duplication is gone.

**Examined the same evening, at his ask, and three gaps closed.**  The
examination found the standard *established as an instrument* and not
as a standard: stated only inside a tool, and two of this card's own
claims — one rule one place, the arrivals rate — true by `grep` and
gated by nothing.  Now: `doc/method.md` §"What a directory must have
to be held to this" carries the ten pieces as a table generated by
`tools/seedaudit.py --table`, and `test_citations.py` refuses the page
when it differs from `PIECES`; `test_rules.py` refuses a bold rule
stated in two of the five or a tool explained under a heading in two;
`tools/arrivals.py` counts cards minted per day and `tools/suite.py`
draws the last seven days on `test/gates.md` at every commit — a
number, never a refusal, because the rule is critical *if it works*
and that is where it shows.  Fifteen in the last seven days as this is
written, nine of them on the day the rule was written.

Henri, 2026-08-18: *"it will take time until we can done/ this card."*
It did — six days.  Whether it goes to `board/done/` now is his line
to write, and the one thing that would argue against it is
`card:project-seed.md`: the audit has never been pointed at a copy
that is not this tree, which its own docstring keeps saying until it
is false.  That is the seed's first day, not this card's last.

