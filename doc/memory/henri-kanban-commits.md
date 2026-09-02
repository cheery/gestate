---
name: henri-kanban-commits
description: "Commit workflow: the right to commit is Claude's since 2026-08-17, titles and bodies too; granular, card move rides along; one-card-one-commit struck 2026-08-29; pushing stays Henri's"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2b12cb6a-4013-4995-ad75-b7b219fabf84
  modified: 2026-09-02T00:00:00.000Z
---

**Titles are Claude's since 2026-08-17**, on the morning Henri started
working the board from away from the desk: *"From now on I allow you to
select titles yourself."*  Claude stages, titles, writes the body and
adds the Co-Authored-By line.  He still names a title whenever he wants
one; the change is that the absence of one is no longer a stop.

Before that (2026-08-13 → 08-17) he gave every title and a session asked
for it.  **Pushing is still his** unless he says otherwise.

**And the right to commit is Claude's too, not only the title.**  *His
own words, 2026-09-02, when a session read this memory as a reason to
stop and ask:* **"I gave you the right to commit.  The note is a relic
from a time that I wanted some control over commits."**  So a session
that has finished a piece commits it; asking first is the thing that was
struck, and a session that asks anyway is spending his attention on a
permission he has already given twice.

**"One commit is the card being done" was struck 2026-08-29** — a
session's tightening, not his rule, and `board/README.md` records the
strike: it stood from 2026-08-17 and what remains is granularity, with
the card saying where it stands at every commit before the last.

**Why:** the commit point is a decision about the board (what counts
as a finished card), and that decision is his; the body is a record of
what actually changed, which the session has better context for.

**How to apply:** stage the session's intended files only (never his
untracked scratch .ges files); if he gave a title use it verbatim,
otherwise write one in the tree's own voice — short, concrete, naming
what changed rather than what it is for.  Summarise honestly in the
body: what moved, what was measured, what is deliberately not included.

**Granular, 2026-08-16:** *"I would like if commits are fairly granular.
They don't always need to be, but if it makes reviewers job easier, make
them separate."*  So a session that finishes several distinct pieces
**proposes a split** — one commit per reviewable idea, with a suggested
title each — rather than offering one large commit and waiting.  He
approves, edits or renames the titles; the split itself is a service to
review, which is the thing `doc/reading-the-log.md` says is the only
check left under auto mode.  A card's move to `board/done/` rides in the
same commit as its work.

Related: [[henri-working-style]]
