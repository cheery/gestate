---
name: gestate-ungated-sweep
description: "The 62-entry fixme audit — complete 2026-09-04, run to the day: five a session capped, 13 batches, and the three rules the batches earned"
metadata:
  type: project
---

A levelled sweep of `fixme.md` ran from **2026-08-19 to 2026-09-04** and
**finished on the day the schedule gave**: 62 repairs that no test
named, five a session, thirteen batches, no day doubled to make up a
miss.  All 62 carry a `gate:` line.  What the card still owes is
Henri's — the third Friday review, and the ratchet question (an
accepted baseline that may shrink and never grow). The
whole plan — dates, the F-numbers in each batch, the rules — is in
`card:ungated-fixes.md`. **Read it there; this note only says the sweep
exists**, because a session picking the work up cold will not know to
look.

**Why:** Henri called it heijunka — *"This fixme is not this week's only
problem and focusing on it would causes tremendous context rot issues."*
The risk is not fatigue. It is judgement degrading across a long uniform
task while confidence stays flat, which is why five is a **cap and not a
target**, zero is a legitimate session, and **two uncertain verdicts in a
row ends the session**.

**How to apply:** one commit per batch, so `git log` shows where the last
session stopped — thirteen sessions is more than any context holds. Each
entry gets a `gate:` line, and *`none — nothing can`* and *`none — not a
repair`* are honourable verdicts; a quota answered by inventing tests is
the failure this is designed against. Henri picks three verdicts at
random each Friday and disagrees with them.

**Three rules the batches earned.** *A named test is
not yet a gate* (batch 2): read the entry against the test's name and you
get it wrong two times in five, so put the defect back and watch the test
go red. *A green is not yet a gap* (batch 12): a mutation nothing noticed
has two readings — the branch ran and no test looked, or **the branch
never ran at all** — so before writing `none`, mutate the branch to
*raise* and see whether anything reaches it. That probe changed two of
five verdicts in one batch: F15's greens were tautologies, F8's was a
real gap.  *A red is not yet a gate* (batch 13): a reconstruction that
breaks the program produces confident failures about nothing — F6's first
mutation gave 13 red that were an **arity artefact**, because the
hand-built term under-applied a generated helper.  Mutate **through the
call the code already makes**, and read what the reds are named after.

**And one red in every batch was never real.**
`test_complaints.py::test_the_page_is_not_behind_the_source` renders a
page carrying line numbers and compares it, so **any mutation that
changes a file's line count goes red for that alone**.  It never
changed a verdict — a `none` rests on a green — but it inflated every
red the sweep counted.  Prefer line-count-preserving edits.

See [[gestate-board-goal]] and [[test-what-a-person-would-do]].
