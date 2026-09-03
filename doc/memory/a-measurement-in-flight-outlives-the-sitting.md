---
name: a-measurement-in-flight-outlives-the-sitting
description: "Henri, 2026-09-03: closing a sitting ends the work, not a run already going — a killed suite at 38% threw away the only evidence the shift owed"
metadata:
  type: feedback
---

**Henri, 2026-09-03**, after a session killed a full `tools/suite.py`
run at 38% because he had said *"I see we're done here now"*:
**"Well.. the suite could have been run. I run the full suite
separately now. There's plenty of time."**

**Why:** a sitting is a body constraint on *him*
([[a-sitting-is-a-body-constraint]]) and it bounds what a session asks
of him and starts next. It does not bound a process already running
with nobody watching it. The full pass is the one thing
`board/README.md` says a shift owes — *one full run per shift* — and it
costs the session nothing to finish. Stopping it bought tidiness and
paid with the evidence, and then the shift closed on gates plus a
partial run, which is a weaker claim than the tree had already earned.

**How to apply:**

* **Do not kill a measurement because the sitting closed.** Let it
  finish and report the result when it lands; if the session is really
  over, say the run is still going and where its output is.
* **Kill it for the reasons that were always the reasons** — the tree
  must change under it ([[restore-a-mutation-from-memory]]'s neighbour
  rule: a run against a tree that no longer exists proves nothing), or
  he needs the machine and says so. Not for tidiness.
* **Freeze the tree while *he* runs one.** He may take the full pass
  himself; a session editing files under it invalidates his run the
  same way it would invalidate its own.
* And the mechanical trap, hit the same evening: `pkill -f
  'tools/suite.py'` matched its own shell and took the caller —
  [[a-driven-wait-that-watches-itself]]. Kill by pid.
