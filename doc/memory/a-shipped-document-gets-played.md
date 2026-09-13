---
name: a-shipped-document-gets-played
description: "An example whose state is a file beside it — tic-tac-toe-facts.board — is written by anyone who runs the example, Henri included, and a commit an hour later takes the game with it; diff the document before committing, and every test and driven run copies both files"
metadata:
  type: feedback
---

**A program whose state is a document writes that document wherever
the program is, and the shipped example is somewhere.**  On
2026-09-13 `examples/gui/tic-tac-toe-facts.ges` landed with its board
beside it as a plain file of facts (`card:gui-is-difficult.md`
§"Built — 2026-09-13: tic-tac-toe, its board a document").  Henri
opened the example from the tree and pressed the middle cell at 19:09;
the door did what it is for and wrote `mark  cell 4  mark X` into the
repository's own `.board`; the session's commit at 19:10 took it, and
the driven run afterwards read its first two observations wrong
because the copy it made was a copy of his game — *"oh.  is it me?  I
tried it already."*

**This is not the harness-saves-into-the-tree hazard `tools/driven.py`'s
`a_copy_of` already guards** — that one is a typed `Ctrl-S`; this one
is the program working exactly as designed, with no chord, on a file
`git status` shows as modified only if somebody looks.  A `.notes`
never had it because no shipped example writes its notes on a press.

**How to apply:** before committing a slice that ships a document
beside a program, `git diff` the document — a mark in it is a game,
not a fixture.  A test or a driven run that opens such an example
copies **both** files into a scratch directory, never the program
alone (`test/test_documents.py` `_copy`, the driven script's second
`copyfile`).  And when the working tree shows the shipped document
changed and no session wrote it, the first question is whether he has
his hands on it — which is the postcondition met, and worth a line on
the card rather than a hunt for the test that did it.  Related:
[[commit-what-you-wrote]], [[test-what-a-person-would-do]],
[[a-sessions-time-sense-is-not-realtime]].
