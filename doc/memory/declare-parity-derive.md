---
name: declare-parity-derive
description: "How a load-bearing mechanism is replaced here: write the second statement, hold it to the working one by a test on a real piece, and only then let the working one obey it — the derivation is what finds the defect"
metadata:
  type: feedback
---

**Declare, hold to parity, derive.**  When something the tree already
does by hand is to be said a second way — a schema, a picture that
names what it drew, a model beside a model — the order is always:

1. **Declare it** beside the working thing, changing nothing.
2. **Hold the two to each other** by a test, on a real piece rather
   than a fixture.
3. **Derive** — make the working thing *obey* the declaration — and
   only then delete what it replaced.

**Why the third step is not the same as the second, and this is the
whole of it.**  On 2026-09-09 `gestate/notes.ges` was written to say
what a `.notes` is, and nine tests held it to `gestate/notes.py`; all
nine passed.  Making the canonical writer *obey* it exposed that its
order term was wrong — `By "section"` where the parser had always
sorted by **where the section stands in the file** — an error that
agrees with the truth on `arc.notes` and nowhere else, because that
file happens to name its sections A, B, C.  A declaration derived from
a working implementation is checked against the one file that exists,
and **the one file is a witness to the rule and not to its boundary.**
The parity step cannot find that; the derivation does, immediately.

**And the second step is not ceremony either.**  It is what makes the
third safe on a load-bearing path: the roll's press is the tree's
most-used gesture, so the note's own number was wired, delivered, and
*counted against* `note_under` on every note of `arc.notes` before
anything was deleted — 86 of 88 agreeing, the two that part being the
overlap already measured.  Deleting the old road then becomes a small,
decided step instead of a leap.

**How to apply:** never replace a working mechanism in one commit.
Land the declaration first and say in the card that there are now two
statements of one truth and a test holding them together — *which is
one more than there should be*, and say that too, so the next session
knows the state is deliberate and unfinished.  Where the derivation
would change *feel* rather than behaviour — how near a press has to be,
which of two overlapping things is meant — stop and ask, because a test
cannot answer it and a session guessing is how a tolerance disappears
([[decisions-arrive-shaped]], [[test-what-a-person-would-do]]).

Related: [[a-targeted-set-is-a-claim]] — a chosen set of tests is a
claim about coverage and can be false; this is the same lesson met from
the other end.  The day is `journal.md` §"The clean board, and what it
turned into — 2026-09-09" and the card is `card:gui-is-difficult.md`.
