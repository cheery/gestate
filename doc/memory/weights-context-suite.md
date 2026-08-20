---
name: weights-context-suite
description: "Weights for what the model must know, context for what it must currently obey, suite for what must be guaranteed — why the house rules must never be trained into a model, even when it would work"
metadata:
  type: feedback
---

> **Weights for what the model must know, context for what it must
> currently obey, suite for what must be guaranteed.**

The answer, 2026-08-19, to *could the tree be trained into an open model
that then always follows it?*  Possible; but **never "always"**, and the
"never" is the load-bearing half.

**Training does not install a rule, it shifts a probability.**  A
fine-tuned model holds rule-shaped behaviour in-distribution and drops
it under novelty, which is exactly when the rule was needed.
`manifesto.md`'s second rule already settles it: *what is built must be
able to say when it is wrong.*  Weights cannot say when they are wrong.
A suite can.  Training might carry compliance from 80% to 98%; the
suite handles the 2% and has to exist either way.

**A trained small model is worse than a naive one in one specific way.**
The norms train — format, workflow order, *never a `because` that names
a fix*.  The judgment does not, because fine-tuning redirects capability
rather than adding it.  What you get is a model wearing the vocabulary
perfectly — *suspected*, seams, callers — over judgment that is not
happening, which counterfeits the exact signals used to decide whether
to trust a session.

**And the decisive argument is not performance.**  The rules are plain
files: inspectable, diffable, **dated because they change**, editable in
a minute, with the model swappable underneath.  Weights are opaque and
frozen at training time, so a trained model is a snapshot of August
disagreeing silently with the tree in November — a second source of
truth, which is the mistake the window design refuses twice by name.

*One constraint, stated because it is real and is not a session's to
resolve: training an open model on Claude transcripts is governed by
Anthropic's usage terms.  If it ever comes up, it is Henri's question to
answer, in writing — see [[henri-cofounder-separation]] for why the
answer is sharper for him than for most people.*

**How to apply:** enforcement stays outside the model, in checks the
model cannot write to.  If a fine-tune is ever worth doing, tune on the
**domain** — the gestate language, the codebase idioms — never on the
rules: domain knowledge is what context carries badly and weights carry
well, and rules are the reverse.  Related:
[[smaller-models-and-the-tree]], [[mechanism-not-instructions]].
