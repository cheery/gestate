---
name: gestate-ungated-sweep
description: "The 62-entry fixme audit: five a session capped, 13 batches, 19 Aug – 4 Sep 2026, with a trip-wire and a weekly review by Henri"
metadata:
  type: project
---

A levelled sweep of `fixme.md` runs from **2026-08-19 to 2026-09-04**:
62 repairs that no test names, five a session, thirteen batches. The
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

See [[gestate-board-goal]] and [[test-what-a-person-would-do]].
