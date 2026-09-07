# standing.md — the questions a session is asked when it opens a card

    asked    Henri, 2026-09-06 — "implement standing questions immediately,
             but come up with some good standing questions and let me
             choose among them"; and, on the candidates: "Your proposals
             are good, pick those."
    see      card:standing-questions.md — why, where the questions come
             from, and how it is judged
             tools/standing.py — the hook that asks them, and the harvest lamp
             doc/notes/notes-on-cues.md §"Can an introspective index be built?"

**How this file works.**  A heading names the shelf a card sits on —
`live` is `board/`, `shelved` is `board/later/`, `done` and `refused`
their directories — and every `- ` line under it is asked, in order,
when a session opens a card on that shelf, up to three per card per
sitting.  A line under `proposed` is never asked.  **Henri chooses what
stands under a firing heading**; a session does not promote.

**Where a question comes from, and where it may not.**  From outside
the session's current context: written by Henri, or **harvested in
hindsight at the close of a card** — *what question would have helped
at the start of this?* — which is the one moment a session may propose
one, because hindsight has the evidence and the present has only the
train of thought that produced the answer.  A question a session
invents while working is one it can already answer, and asking and
answering it reads as diligence while retrieving nothing.  *A guest
session, relayed by Henri, 2026-09-06 — `card:standing-questions.md`
Q4 has it whole.*  The lamp at every commit that finishes a card asks
the harvest question; the answer goes under `proposed`.

**Consider it; act if it changes anything; say nothing if it does
not.**  There is no box to tick and nothing checks that a question was
answered — answering on demand turns a cue into a chore and grows a
paragraph of self-interrogation nobody reads.

**Each question names where it was paid for**, in the line after it,
so that a reader who wants to strike one can see what it cost the last
time nobody asked it.

## live

- What would a professional in this domain check that we have not?
  *— the cues page's own; `doc/memory/why-models-hallucinate.md` is why
  a session cannot supply the missing professional on its own*
- What in the tree already does this, and where?
  *— `board/README.md` §"Question it into existence", move 4:
  `card:ungated-fixes.md` was nearly a duplicate of a card it turned
  out to contain*
- What number would say this card is done, and what command produces it?
  *— `doc/memory/research-that-leaves-a-command.md`: a measurement
  carries a command and a recommendation carries nothing*

## shelved

- Is this waiting on an event, or on Henri?
  *— `doc/memory/sediment-versus-debt.md`: sediment costs nothing and
  debt compounds, and the directory looks the same either way*

## done

## refused

- Is the work about to be proposed the work this card refused?
  *— `board/README.md` §"The priority": the shelf is read the moment
  somebody is about to propose work a card here covers, which C1 of
  `card:online.md` failed to do*

## proposed

*Chosen above by Henri on 2026-09-06 from twelve a session wrote that
morning, each turned around from a lesson the tree had paid for.  The
seven below were not chosen and are not struck: they wait for the
fire, per the guest's own note that this is fire material — draft it,
let it sit, see whether it still looks right when not an hour
downstream of the idea.  Anything harvested at a card's close goes
here too, dated, with the card it came from.*

**For a live card:**

- What is the naive thing a person would do here, and has anyone tried it?
  *— `doc/memory/test-what-a-person-would-do.md`: a harness built from
  the implementation cannot find a missing affordance; F150*
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
- Which clock is this stamped against, and is it the one the card is about?
  *— harvested 2026-09-07 at the close of `card:transport-modes.md`:
  the model said "the clock is held" and the engineering was that a
  note is stamped against the engine's clock, not the score's, so
  *sounding* needed two numbers where there had been one; a card that
  names a clock, a position or a time owes this question on day one*
- What is inside this number besides the thing it claims to measure?
  *— harvested 2026-09-07 at the close of `card:relations-at-frame-rate.md`:
  the first table timed a query and its input's construction as one
  evaluation, and the second timed a lazy value to its outer
  constructor, so the fix landed and the number barely moved, then
  moved the wrong way; a card whose `because` is a measurement owes
  this question before its first slice*

**For a shelved card:**

- What was the trigger written into it, and has it fired?
  *— `board/README.md` §"The priority": a card comes back the same way
  it left, by him saying so — and a trigger nobody re-reads never fires*

**For a done card:**

- Does the test it names still exist, and does it still fail without the fix?
  *— `card:ungated-fixes.md`: a defect closed on a photograph can come
  back without anybody being told; `doc/memory/a-targeted-set-is-a-claim.md`*
