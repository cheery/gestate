---
name: a-targeted-set-is-a-claim
description: "A batch's targeted test set is a claim about coverage, and it can be false — before writing a `none` verdict, grep the tree for the repair's own vocabulary rather than trusting the run's number"
metadata:
  type: feedback
---

**A targeted test set is a claim about coverage.**  `card:ungated-fixes.md`'s
batches measure by mutation against a chosen set of files, and the number that
comes back — *780 green* — is only as good as the choosing.

The case, 2026-09-01, batch 10.  F25's `_UNOVERRIDABLE` half — the check that
refuses `infixl 9 ->` — was mutated to `if False` and the run returned **780
of 780 green**.  The verdict *ungated* was two minutes from being written into
`fixme.md`.  It is gated:
`test/test_music_syntax.py::test_the_function_arrow_cannot_be_given_a_fixity`,
red on that exact mutation, naming neither F24 nor F25.  The file was not among
the batch's 37.

**Why:** an absence measured against an incomplete set is evidence about the
set, not about the tree — the same shape as [[dont-conclude-from-a-shallow-check]],
arriving through a *green* run instead of an empty grep.  And it fails in the
expensive direction: a `none — not yet built` verdict tells the next person to
go and spend an afternoon building a gate that already exists, and
`manifesto.md` §"A gate's name is not its coverage" says why a wrongly believed
gap is not the cheap kind of error.

**How to apply:**

* **Before writing any `none` verdict, grep the tree for the repair's own
  vocabulary** — the error message, the identifier, the constant — and read
  what comes back.  `grep -rn "cannot be given\|_UNOVERRIDABLE" test/` is what
  would have caught this one, and it costs a second.
* **Read the code around the repair**, not only the entry's text.  That is what
  found it here, and it is the same move that made batch 6's F80 and batch 7's
  F56 come out right.
* **When the set is widened, say so in the gate line**, so the number in the
  record is the number that was actually run.
* A red verdict needs no such check: a mutation that reddens something has
  proved the gate exists.  The asymmetry is the whole rule.

See [[gestate-ungated-sweep]], [[why-models-hallucinate]].
