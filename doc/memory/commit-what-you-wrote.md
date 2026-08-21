---
name: commit-what-you-wrote
description: "Never `git add -A` — a file the author dropped into the working tree is not work, and a blind add publishes it; stage named paths only, and ask about anything untracked you did not write"
metadata:
  type: feedback
---

**Henri, 2026-08-21:** *"I probably should not include files this way..
it can flow in as commit too easily.  That's a behavior change from
me."*  He had put `derived-2.md` into `doc/trial/` so a session could
read it.

**Why:** the risk is real and it is not his to carry alone.  An
untracked file inside the tree is indistinguishable from work in
progress, and `git add -A` cannot tell them apart — so a file handed
over for *reading* becomes a file published to a public repository, in
one command, with no moment where anybody decided to publish it.  It did
not happen; on the evening it nearly could have, five commits were clean
and the only reason was timing.

**How to apply:**

* **Stage named paths.  Never `git add -A` or `git add .`** — not even
  when `git status` looks like exactly what you meant to commit, because
  the check and the commit are two moments and a file can arrive between
  them.
* **Run `git status` before every commit and read the untracked list.**
  Anything there you did not write is a question, not a candidate.
* **Files for reading arrive outside the tree.**  `~/` or an export
  directory, with the path said out loud — which is how
  `notes-on-the-trial.md` arrived, and it worked.  A session copies in
  only what it was asked to copy in.
* **The same rule protects him in the other direction**: it is what lets
  him drop anything anywhere without having to remember whether the tree
  is watching.

The general form is this house's own: **fix the task, not the person.**
A rule that depends on the author remembering where he saves a file is a
rule that will fail on a tired evening; a session that stages only what
it wrote cannot fail that way at all.

See [[henri-kanban-commits]] for who asks for a commit and who writes
it, and [[gestate-house-rules-authorship]] for what is his to keep.
