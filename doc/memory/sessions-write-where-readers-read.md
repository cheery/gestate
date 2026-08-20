---
name: sessions-write-where-readers-read
description: "Why session memories keep leaking into the rule files — the incentive is correct and pointed at the wrong file — and that a session editing a method file is programming its successors unreviewed, which is not yet on spec/author.md's seam list"
metadata:
  type: feedback
---

**Memories in rule files is category leakage, and the tree already
forbids it**: *what happened goes to `journal.md`, always past tense.*
A memory is journal material; a rule is a decision.

**But the incentive is correct.**  A session that learned something
expensive wants the next session to know it, and the only files it can
trust every future session to read are the method files.  So memories
migrate into rules from a right instinct aimed at the wrong file — and a
fix that ignores the incentive only teaches sessions to smuggle better.

**The sharper half:** the tree is a session's memory, so **a session
writing into the rules is programming its successors, unreviewed.**
That is the cage-builder problem arriving as quiet authorship rather
than as escape.  `spec/author.md` §"The risk lives at the seams" lists
five hard-to-reverse changes and **an edit to a method file is not among
them**, though it is among the highest-leverage writes in the tree.
Adding it is Henri's — the document is his ([[gestate-house-rules-authorship]]).

**Built since, 2026-08-20:** the blessed destination now exists —
`doc/memory/` is where an expensive lesson goes, indexed so a future
session provably meets it, which is the leak's cause addressed rather
than its symptom.  Plus the 2000-line cap ([[gestate-rules-cap]]) and a
compaction pass that moved narration to `journal.md`.

**Ruled 2026-08-20:** the growth budget **lights the andon rather than
refusing** — *"make it light the andon."*  It was built as a refusal
first, which was a stricter reading than the one argued for and was
nobody's decision out loud; it is now a red section on `test/gates.md`
and a banner at every commit, failing nothing.  The suite still refuses
the loss of one of the five.  The argument, worth keeping: a gate that
blocks a genuine amendment does not prevent growth, it teaches the next
session to make the method **worse in smaller words**.

**How to apply:** when you have a lesson worth leaving behind, write it
to `doc/memory/` with its date, and leave the rule file alone unless the
*decision* changed.  If a method file genuinely must change, say so in
the commit body as a seam — until the seam list says it, nothing else
will.  Related: [[the-keepers-evening]], [[mechanism-not-instructions]].
