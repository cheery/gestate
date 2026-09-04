---
name: the-fence-takes-git-identity
description: "A shell command containing pytest is wrapped by the fence, and inside the fence git has no author — so a commit in the same command fails with 'unable to auto-detect email address'; commit in its own command"
metadata:
  type: project
---

**Never put `git commit` in the same shell command as `pytest`.**
`tools/fence-hook.sh` rewrites any command that runs dependency code —
`pytest`, `cargo` — to run under `tools/sandbox.sh`, and the sandbox
has a different `HOME`: no `~/.gitconfig`, so `git commit` says
*"unable to auto-detect email address"*, and `tools/memoryindex.py`
says *"no index at …MEMORY.md"* for the same reason.  Nothing else in
the command is wrong.

**Why:** three commits failed this way on 2026-09-04, each after a
green test run in the same line, and the first two were misread as a
`cd` problem.  The fence is doing its job — a test run must not see
the desk's credentials — and the symptom is far from the cause.

**How to apply:** run the gates, then commit in a separate command.
If a commit fails with that message, the command that ran it was
fenced; do not touch `git config`, which the leash denies anyway.
Related: [[gestate-hardening]], [[commit-what-you-wrote]].
