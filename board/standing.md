# standing.md — the questions a session is asked when it opens a card

    asked    Henri, 2026-09-06 — "implement standing questions immediately,
             but come up with some good standing questions and let me
             choose among them"
    see      card:standing-questions.md — why, and how it is judged
             tools/standing.py — the hook that asks them
             doc/notes/notes-on-cues.md §"Can an introspective index be built?"

**How this file works.**  A heading names the shelf a card sits on —
`live` is `board/`, `shelved` is `board/later/`, `done` and `refused`
their directories — and every `- ` line under it is asked, in order,
when a session opens a card on that shelf, up to three per card per
sitting.  A line under `proposed` is never asked; that is where a
session puts a candidate, and it stands there until Henri moves it up
or strikes it.  **Henri chooses what stands under a firing heading.**
A session may propose, and may strike its own proposal, and does not
promote.

**A question here is a stored cue, not a checklist item.**  It is asked
so that a session goes and looks for something it would not have
known to look for; there is no box to tick and nothing checks that it
was answered.  What is measured is whether the card changed after it
was asked — `card:standing-questions.md` says how.

**Each question names where it was paid for**, in the line after it,
so that a reader who wants to strike one can see what it cost the last
time nobody asked it.

## live

## shelved

## done

## refused

## proposed

*The candidates, as of 2026-09-06, a session's.  Each one is a lesson this tree
paid for once, turned around into the question that would have caught
it.  Ordered by the session's own estimate of which would have fired
most often this month.  Not one of these is asked until it is moved
above.*

**For a live card, at the moment it is opened:**

- What would a professional in this domain check that we have not?
  *— the cues page's own; `doc/memory/why-models-hallucinate.md` is why
  a session cannot supply the missing professional on its own*
- What is the naive thing a person would do here, and has anyone tried it?
  *— `doc/memory/test-what-a-person-would-do.md`: a harness built from
  the implementation cannot find a missing affordance; F150*
- What in the tree already does this, and where?
  *— `board/README.md` §"Question it into existence", move 4:
  `card:ungated-fixes.md` was nearly a duplicate of a card it turned
  out to contain*
- What number would say this card is done, and what command produces it?
  *— `doc/memory/research-that-leaves-a-command.md`: a measurement
  carries a command and a recommendation carries nothing*
- Which sentence on this card is a session's report, and which is a harness output?
  *— `card:testimony-inventory.md`, the count that says how often the
  two are confused*
- Is the `because` a problem, or a fix wearing one?
  *— `board/README.md` §"What a card is": the board's most expensive
  lesson, a card that named `type Duration = Float` when the need was
  the argument names*
- What would kill the reading you are about to take?
  *— move 3 of the questioning, and the pre-registration rule in
  `doc/memory/a-trial-is-refused-until-its-sheet-can-decide.md`*
- What did the last session leave here that it did not finish, and does the card still say so?
  *— `doc/memory/gestate-canvas-unwired.md`: callers lost in a deletion
  and nobody told; the `blocked` field is for this and is the one most
  often left stale*

**For a shelved card:**

- Is this waiting on an event, or on Henri?
  *— `doc/memory/sediment-versus-debt.md`: sediment costs nothing and
  debt compounds, and the directory looks the same either way*
- What was the trigger written into it, and has it fired?
  *— `board/README.md` §"The priority": a card comes back the same way
  it left, by him saying so — and a trigger nobody re-reads never fires*

**For a done card:**

- Does the test it names still exist, and does it still fail without the fix?
  *— `card:ungated-fixes.md`: a defect closed on a photograph can come
  back without anybody being told; `doc/memory/a-targeted-set-is-a-claim.md`*

**For a refused card:**

- Is the work about to be proposed the work this card refused?
  *— `board/README.md` §"The priority": the shelf is read the moment
  somebody is about to propose work a card here covers, which C1 of
  `card:online.md` failed to do*
