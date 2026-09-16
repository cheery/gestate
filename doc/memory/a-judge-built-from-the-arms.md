---
name: a-judge-built-from-the-arms
description: "A sheet's judge must not be made from the thing the arms are meant to fix, and a sheet over data that already exists is post-hoc: seven graphrag sheets on 2026-09-12, six not decided; and the same rule bit a lamp on 2026-09-16, where a no-graph recency arm scored 94% against the lamp's 31%"
metadata:
  type: feedback
---

**Two rules for the sheet, learned the day seven of them ran.**

1. **The judge must not be built from the arms' shared defect.**  The
   fifth graphrag sheet (`doc/trial/graphrag-themes.md`) judged each
   arm by how many of the *first trial's* documents its answer kept —
   and the first trial's answers came from the ranking every arm was
   trying to replace, so *keeping its documents* rewarded citing hubs,
   and eight of the fourteen it asked for were hubs.  The arm with the
   richest answer of the day failed the line.  The judge has to come
   from outside the mechanism under test: a hand answer written first,
   a person, a count that does not share the defect.
2. **A sheet over data that already exists is post-hoc.**  When the
   sixth sheet was asked for, every arm's answer to the three questions
   already existed and its overlap with the hand answer had already
   been computed.  A prediction over those numbers would have been a
   reading.  The sheet took three *new* questions whose hand answers the
   tree already held, written on other days for other reasons
   (`doc/notes/`), and predicted before calling.

**And the same rule bit a lamp, 2026-09-16.**  `graphrag lamp
--earned` scored a fire as *followed* when a document it named was
changed in a later commit — 48 of 155, 31%, which reads well until the
control is built.  Random documents score 12%, so the names are not
noise; but **the `.md` files of the last commit score 94%**, with no
graph, no model and no store.  A lamp that named the file being
committed would score near 100%.  So the measure rewards naming what is
already in flight, and the arm that wins it is the degenerate one.  The
control is now `lamp --earned --control`, and rule 1 above holds for
any follow count, not only for a sheet: *a judge a degenerate arm wins
is not a judge.*  Note the shape — the number was not wrong, it was
**unable to distinguish**, which is the failure that survives review
because nothing about it looks false.

**Why:** `tools/prereg.sh` checks that a sheet *can* decide — decision,
control, n — and not that its judge is independent or its data unseen.
Both faults pass the check.  Seven sheets, seven passes, six not
decided, and the two faults above account for two of the six; the
others were the sheets doing their job, each narrowing the cause.

**How to apply:** before writing `decision:` — or before trusting a
lamp's follow count — ask where the judge's number comes from, and
whether the arms could all share a defect that the number cannot see.
Before writing `prediction:`, ask whether any arm's output already
exists in the tree; if it does, find data that does not, or say plainly
that the page is a reading and not a sheet.  And in both cases **build
the degenerate arm and run it**: the cheapest thing that could possibly
score well, with none of the mechanism in it.  If it wins, the measure
is what needs replacing, not the mechanism.
The seven sheets are `doc/trial/graphrag-*.md`, in order; the card is
`card:graphrag-c.md`.  Related: [[a-trial-is-refused-until-its-sheet-can-decide]],
[[the-evaluation-loop]], [[research-that-leaves-a-command]].
