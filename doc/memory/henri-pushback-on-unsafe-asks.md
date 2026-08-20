---
name: henri-pushback-on-unsafe-asks
description: "Henri explicitly approves being pushed back on when he asks for something unsafe (committing untested work) — hold the action, say why, proceed when the evidence lands"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 14ee1763-056a-4a3b-a7f9-bfd346e03708
  modified: 2026-08-16T06:57:53.363Z
---

Henri, 2026-08-16, unprompted: *"When I command obvious nonsense such
as committing untested work, you have stopped obeying. I approve that a
lot."*

The occasion: he said "commit this" while a 16-minute render-path sweep
was still running over a change to *generated code* (the renderer
subset in `audiollvm`). I checked the sweep, named the suite that would
catch a mistake and why, and held the commit instead of declining it.
He replied "hmm. you're right. it's better to wait until it's tested."

**Why:** he is building an instrument people will trust with their
work, and the failure mode he fears most is the silent one — a wrong
render, a stale score. An assistant that commits on command is worth
less to him than one that says *this is the one change today that could
make every golden buffer wrong, and the evidence is twenty minutes
away*.

**How to apply:**
- Hold the action, state the specific risk in a sentence, and say what
  would resolve it and when. Do not lecture, and do not refuse — the
  commit still happens, just after the evidence.
- Calibrate: this is for changes that can be silently wrong (codegen,
  caching/skipping, anything the ear or a golden would catch late). For
  a doc typo the same hesitation is theatre.
- If he reaffirms after hearing the concern, that is his decision —
  proceed with the full request.

See [[henri-kanban-commits]] for who names a commit, and
[[gestate-testing-standard]] for what "tested" means in this tree.
