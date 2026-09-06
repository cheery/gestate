---
name: a-traceback-quotes-the-file-not-the-run
description: "A test file edited while its run is in flight fails with a traceback that prints the NEW source over the OLD assertion — pytest collected the old bytecode, the traceback reads the file from disk; re-run before believing the failure"
metadata:
  type: feedback
---

**A traceback prints the file as it is on disk, not the code that ran.**
Start a `pytest` run in the background, edit one of its test files while
it runs, and a failure in that file arrives with your new lines under the
`>` marker and the *old* assertion's message under `E` — because
collection imported the old bytecode and the traceback renderer opens
the file afresh.

The case, 2026-09-06, `card:notes-editor.md`'s editing scale: the
page test was changed from counting `NOTES` captions to counting section
titles while the run was on; the failure showed the new comprehension
with the old message *one roll per section, stacked*, and ten minutes
went to debugging a test that had already been fixed.

**How to apply:** if a test you edited during a run fails, look at the
`E` line's message against the file's; when they disagree the run was
the old code — re-run, do not debug.  Better, `board/README.md`'s own
rule: *the tree is frozen while it runs* — a targeted run is short
enough to wait for.  Related: [[a-targeted-set-is-a-claim]],
[[restore-a-mutation-from-memory]].
