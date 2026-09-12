---
name: a-judge-built-from-the-arms
description: "A sheet's judge must not be made from the thing the arms are meant to fix, and a sheet over data that already exists is post-hoc: seven graphrag sheets on 2026-09-12, six not decided, and the one that decided used hand answers written first"
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

**Why:** `tools/prereg.sh` checks that a sheet *can* decide — decision,
control, n — and not that its judge is independent or its data unseen.
Both faults pass the check.  Seven sheets, seven passes, six not
decided, and the two faults above account for two of the six; the
others were the sheets doing their job, each narrowing the cause.

**How to apply:** before writing `decision:`, ask where the judge's
number comes from, and whether the arms could all share a defect that
the number cannot see.  Before writing `prediction:`, ask whether any
arm's output already exists in the tree; if it does, find data that
does not, or say plainly that the page is a reading and not a sheet.
The seven sheets are `doc/trial/graphrag-*.md`, in order; the card is
`card:graphrag-c.md`.  Related: [[a-trial-is-refused-until-its-sheet-can-decide]],
[[the-evaluation-loop]], [[research-that-leaves-a-command]].
