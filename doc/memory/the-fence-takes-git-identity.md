---
name: the-fence-takes-git-identity
description: "A shell command containing pytest or cargo is wrapped by the fence, which swaps HOME and mounts a fresh tmpfs over /tmp — so git has no author, and anything written to a scratch directory under /tmp in that same command is gone when it ends"
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

**And the fence mounts a fresh `/tmp` over the real one**
(`tools/sandbox.sh`: `--tmpfs /tmp`).  So a session's scratch directory
under `/tmp` **does not exist** inside a fenced command: a backup
written there in the same line as the build it protects against is gone
the moment the command ends, and reading one back fails with *no such
file*.  Found 2026-09-11, appending a deliberate type error to
`window.rs` to test whether a build was honest — the `cp` that was to
restore the file ran in the same command as `cargo build`, so the
backup was never there and the file was left holding the error.

**And a *backgrounded* fenced command's output is unreadable for the
same reason.**  The harness writes a background command's stdout to a
file under `/tmp`, and a fenced command cannot write there — so the
task notification arrives saying *completed* and the file it names does
not exist.  Twice on 2026-09-11, and the second time it was the one
oracle for a JavaScript change on a machine with no `node`.  The fix is
to redirect into the **project**, which the fence does bind:
`pytest … > test/.jsrun.log 2>&1`, then read that.  `tools/suite.py`
has always done this — `test/report.md` is inside the tree and that is
why.

**How to apply:** run the gates, then commit in a separate command.
If a commit fails with that message, the command that ran it was
fenced; do not touch `git config`, which the leash denies anyway.
Keep any scratch file a fenced command needs — a backup, an output to
read back — **outside** that command, or inside the project where the
fence does bind.  Related: [[gestate-hardening]],
[[commit-what-you-wrote]], [[restore-a-mutation-from-memory]],
[[a-build-is-not-an-instrument-until-it-has-failed]].
