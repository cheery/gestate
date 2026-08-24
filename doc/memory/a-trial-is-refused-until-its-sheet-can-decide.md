---
name: a-trial-is-refused-until-its-sheet-can-decide
description: "Run tools/prereg.sh on a trial's pre-registration before spawning any arm; a blank decision, control or n means the run cannot decide, and on 2026-08-23 three such sheets were run anyway — Henri's kaizen: nothing on either side stopped them"
metadata:
  type: feedback
---

**Before any arm of a trial is spawned, run `tools/prereg.sh` on its
pre-registration and stop on red.**  The sheet needs three lines,
non-empty: `decision:` (what changes if the result comes out either
way), `control:` (what isolates the variable — *told not to look* is
not a control, a subagent inherits the spawning session's memory), and
`n:` (samples per arm, a number).  `doc/trial/README.md` §"Before any
arm starts" is the rule; `test/test_prereg.py` pins the tool.

**Why.**  Kaizen of 2026-08-24, `journal.md` §"Kaizen, 2026-08-24 —
nothing stopped the run".  Three trials on 2026-08-23 were each
pre-registered by a session that *named* the invalidating fault in its
own sheet — n = 1, no clean control — and ran anyway.  Pushed on
whether the expensive part was his question or the missing stop, Henri:
*"It's the second issue."*  And what he asked for was a mechanism that
reaches how *he* presents an ask, without a nagger — so the refusal sits
at the input: the ask arrives with its decision attached or it comes
back, the way a card with no `because` comes back.  A doubt written into
a sheet is a stop, not a licence.

**How to apply.**  Write the sheet first, with the three lines; run the
tool; if it is red, say so and do not spawn — the sheet has said in its
own words that the run cannot decide.  A control is a separate clone and
a session with no memory directory, or it is a second treated arm.  See
[[research-that-leaves-a-command]] (the companion rule, his,
2026-08-23), [[conditioning-shows-under-work]] and
[[henri-subagents]].
