---
name: a-driven-wait-that-watches-itself
description: "pgrep -f / pkill -f match the shell that runs them — a wait on a process pattern never ends and a kill takes the caller; anchor on the pid, or exclude your own"
metadata:
  type: project
---

2026-08-26, twice in one afternoon: `pkill -f "pytest -q …"` killed the
shell it was typed into (exit 144) before its relaunch line ran, and a
monitor doing `while pgrep -f "tools/suite.py"; do sleep; done` waited
an hour on a suite that had finished in twenty-five minutes — the
pattern was in the monitor's own command line, so it matched itself.

**Why:** `-f` matches the whole command line of every process, and the
process that most reliably carries the pattern is the one running the
`pgrep`.  Both failures are silent: a kill that hits the caller looks
like the command "did nothing", and a wait that never ends looks like
the thing being waited on.

**How to apply:** wait on a *pid* (`kill -0 $pid`) captured at launch,
or on the artefact the run leaves (`test/report.md`'s mtime, a log's
last line), never on a `-f` pattern; and when a pattern is the only
handle, exclude the caller — `pgrep -f pat | grep -v $$`, or `pkill -x`
on the binary's name.  Related: [[gestate-instruments]] (the suite
leaves `test/report.md`; watch that), [[dont-conclude-from-a-shallow-check]].
