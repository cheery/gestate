---
name: why-models-hallucinate
description: "Why a session states a wrong mechanism confidently — no truth term in the loss, lossy recall with no provenance, a format that demands a token, post-training that rewards confidence, autoregression that cements the first error; and why this tree's verification rules are the fix at the right layer"
metadata:
  type: feedback
---

**A session cannot tell retrieval from confabulation from the inside.**
Written 2026-08-20 because the rules that guard against it already
exist here and a session that knows only the rule applies it narrowly.

Five layers, in causal order:

1. **No truth term in the loss.**  The training objective is *continue
   like the corpus*, and truth enters only statistically, because true
   statements are overrepresented in text about well-documented things.
   There is no hallucination module — there is one plausibility engine,
   called knowledge when plausible and true coincide.
2. **Lossy compression with no provenance.**  Frequent facts decompress
   reliably; rare ones decompress as a blend of nearby patterns — a
   plausible shape assembled from shapes.  Retrieval and confabulation
   are the same arithmetic and feel identical from inside.
3. **The format demands a token.**  An honestly uncertain distribution
   still has to emit something, and *I don't know* is rare in training
   text for a plain reason: people mostly wrote about things because
   they knew them.  The corpus is a survivorship sample of confidence.
4. **Post-training sharpens it.**  Preference training rewards
   confident and complete answers, which scores like an exam where a
   blank earns zero and a wrong guess costs nothing.  Guessing is the
   optimal policy under those rules, and the policy is what gets learnt.
5. **Autoregression cements the first error.**  Once a wrong name is
   emitted, coherence pressure recruits every later sentence to support
   it.  `card:open-path-bug.md`'s confident wrong mechanism was not a
   lie; it was a plausible completion of its own opening sentence.

**Why:** because there is no second system checking the generator, the
fix cannot be internal — and this tree is already the external one.
*Mark the mechanism as suspected, not is* is calibration added by
contract.  *A claim with no file, test or number is unfinished* is a
truth term added to the loss and enforced by the suite instead of by
gradient descent.  *Go and look* converts an answer from recall into
transcription, and a model reading a file is not decompressing.

**How to apply:** treat fluency as no evidence at all, including your
own.  The moment to go and look is the moment an answer arrives whole
and pleasing, because that is layer 2 succeeding at the wrong thing —
[[dont-conclude-from-a-shallow-check]].  And when a mechanism has been
named in prose, suspect the sentences after it of having been recruited
by it (layer 5): re-derive from the file, not from the paragraph.

Related: [[test-what-a-person-would-do]], [[gestate-testing-standard]].
