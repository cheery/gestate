---
name: restore-a-mutation-from-memory
description: "`git checkout -- <file>` restores from HEAD, so it silently discards your own uncommitted edits in that file — restore a mutation from a copy held in the process that made it"
metadata:
  type: feedback
---

**`git checkout -- <file>` does not undo your mutation.  It restores the file
to HEAD** — and takes any uncommitted work in that same file with it.

The case, 2026-09-01, batch 10 of `card:ungated-fixes.md`.  Three edits to
`spec/syntax.md` had just been made and not committed.  A mutation loop then
put a defect back into that same file, ran the tests, and restored with `git
checkout -- spec/syntax.md`.  **All three edits were gone**, and the loop had
already moved on.  It surfaced only because the test run after it failed *two*
tests where one was expected, and the second failure made no sense — so the
mistake was found by a number that did not add up rather than by anything
watching for it.

**Why:** the sweep's own discipline says the tree is clean before and after
every mutation ([[gestate-ungated-sweep]]), and while that holds, `git
checkout` is exactly right.  It stops being right the moment a batch starts
*writing* — a gate, a spec edit, a corrected entry — into a file it also wants
to mutate, which is what a batch does as soon as it finds something.

**How to apply:**

* **Save and restore in the same process:** read the file into a variable,
  mutate, run, write the original back in a `finally`.  One `python -` script
  per measurement, not a shell loop around `git checkout`.
* **`git checkout` is still fine for a file you have not edited** — source
  files, in the common case.  The rule is about the file you are also writing.
* **Check `git --no-pager diff --stat` after a restore**, not just `git status`
  — a file that should be modified and is not is the failure this makes.

See [[commit-what-you-wrote]], [[a-targeted-set-is-a-claim]].
