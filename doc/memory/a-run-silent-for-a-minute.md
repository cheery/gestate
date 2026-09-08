---
name: a-run-silent-for-a-minute
description: A measurement that has printed nothing in a minute is telling you about the harness, not the subject — the compiler takes the deep stack itself and deadlocks silently when nested; never pipe a slow run through tail
metadata:
  type: feedback
---

**A run silent for a minute is a fact about the harness.**  On
2026-09-08 an hour went to two measurements that printed nothing for ten
minutes each and were killed at a timeout.  Both had called
`pipeline.compile` from inside `_deep_stack`: the compiler takes the
pipeline's deep stack itself, and nested, the two deadlock with no
message — `tools/retraction.py`'s own comment names the trap, and
`tools/queryframe.py`'s docstring now names it again.  The second hour
was lost because the run was piped through `tail`, so even the lines
it had printed were invisible until it ended.

**Why:** waiting is the wrong response to silence.  A compile that takes
0.14 s does not become ten minutes by having more rows; a run that has
said nothing has either deadlocked or is buffering, and both are
diagnosed by looking at what is running (`pgrep -x python -a`) and at
what the process has written so far, not by extending the timeout.
[[a-driven-wait-that-watches-itself]] is the same lesson from the other
side: the wait must watch the run, not the clock.

**How to apply:** before a long measurement, print a line at each stage
with `flush=True` and write to a file, never through `tail`; if nothing
has appeared in a minute, look at the process before waiting further;
and never call `compile` inside `_deep_stack` — force values there,
compile outside.  The retraction tool's `_tables` is the shape to copy:
compile once at the top, deep-stack only the forcing.
