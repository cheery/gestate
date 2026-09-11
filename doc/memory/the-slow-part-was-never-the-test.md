---
name: the-slow-part-was-never-the-test
description: "Henri, 2026-09-11: a slice takes a minute and its testing takes thirty. The instruments that find defects here run in 15–60 seconds; the multi-minute suite runs found nothing a commit hook would not have caught. Targeted -k runs while working, never wait on a background run, one full pass per shift."
metadata:
  type: feedback
---

**Henri, 2026-09-11**, watching a day of it: *"The progress we do is
very, very slow.  You go and implement one slice at a time, it takes a
minute and then you spend +30 minutes to test it."*

Counted the same hour, on that day's own record:

| | wall |
|---|---|
| the driven run that found the blind oracles | **17 s** |
| the probes that found F222 and the frozen score | **20–60 s** |
| fifteen `tools/suite.py <file>` runs | **4–10 min each** |

**The expensive ones found nothing** except two stale counts in
`doc/method.md` and `doc/complaints.md`, which the pre-commit hook
catches for free at commit time.  Every real defect that day came from
a fast instrument or from Henri at the window.

**And the tree already said the cadence**, in `board/README.md`:
*"Targeted runs per card while working; one full run per shift."*  What
was actually happening was a near-full run per *slice*, each one
prepending the twenty gates, and then **polling it** — turns spent
waiting on a run that would have notified on its own, with the work
uncommitted the whole time.

**Why:** a suite run *feels* like diligence, and it is the one form of
diligence that can be performed without thinking about what would
falsify the change.  The cheap instruments require deciding what the
oracle is; the expensive one does not, which is exactly why it is the
one that gets reached for and the one that finds nothing.

**How to apply:**

1. `python -m pytest -k "<the two or three tests just written>"` while
   working — seconds.  Not `tools/suite.py <whole file>`.
2. **Never wait on a background run.**  Commit or keep working; it
   notifies.  If the tree must change under it, kill it by pid
   ([[a-measurement-in-flight-outlives-the-sitting]]).
3. Commit per slice.  The gates ride the pre-commit hook, so a commit
   *is* the structural check.
4. One full pass per shift, at the end.
5. Before writing a line of a slice that has a design choice in it,
   put the choice to him.  Three of that day's four repairs were wrong
   *designs*, not wrong code, and each cost a whole cycle; his answer
   took one sentence and made the code smaller.

Related: [[a-build-is-not-an-instrument-until-it-has-failed]],
[[dont-conclude-from-a-shallow-check]], [[gestate-instruments]],
[[decisions-arrive-shaped]].
