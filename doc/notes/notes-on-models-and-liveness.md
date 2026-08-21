# notes-on-models-and-liveness.md — a conversation, continued, 2026-08-19

*Whether the tree works on smaller models, whether the rules can be
trained into weights, and how live rules are kept from degrading.
Henri's words are verbatim; the answers are condensed and not
softened. `README.md` in this directory says what the set is.*

---

## Does the tree work on smaller models?

**Henri:**

> there is one thing you could tell me that spares an experiment. your
> current model is titled fable. does the tree I gave you work on
> smaller models such as haiku and sonnet?

**The session:**

The experiment cannot be fully spared — predicting across models is
informed guesswork, not introspection — but it can be shrunk from a
week to an afternoon, because the tree does three jobs and they
degrade separately.

**The structural rules survive on any model.**  Card format,
citations, `done/` moves, one-commit-one-card: deliberately taken out
of the model's hands and put in the suite.  `test/test_board.py` does not
care what wrote the file.  "Visible to something that is not a
person's attention" also means visible to something that is not a
*model's* judgment.  That half of the jewel transfers for free.

**The judgment norms degrade first.**  "Question it into existence,"
"mark the mechanism as suspected," "a `because` is a problem, never a
fix," knowing that most of what blocks a card is not another card —
these live in the model's ability to read 1,600 lines of argument and
*hold* it while working.  The tree teaches by evidence and narrative,
which is precisely the style that needs a strong reader.  A smaller
model reads `spec/author.md` and extracts "be careful"; it does not
extract the three-jobs-of-review distinction and act on it forty
minutes later.  Sonnet holds most of it, with more literal readings
and more missed stop-and-ask moments.  Haiku follows whatever is
stated as a rule near the top and loses the rest — and the
elaboration failure already documented (`card:open-path-bug.md`'s confident
wrong mechanism guess) grows *more* frequent as models shrink,
because plausible-and-wrong is what smaller models produce fluently.

**Initiative degrades most.**  Minting a card for a broken workflow,
noticing a missing instrument, pushing back — top of the capability
stack, first thing gone downmarket.

So: the tree works on Sonnet for well-scoped cards, with the author
catching more direction errors; on Haiku only for narrow,
fully-specified tasks, and the questioning culture mostly will not
instantiate.  Plus a plain tax: the tree is a fixed context load and
eats a larger share of a small model's effective attention.

**The afternoon experiment:** same one-line card to each model, three
reads — did it go and look before asking; is anything marked
*suspected*; did it stop at a seam or barrel through one.

**Cheap adaptation if smaller models join the loop:** a distilled
front — one page, the judgment norms as bare imperatives, above the
full tree.  The pattern already exists for humans ("one sheet, then
depth"; the nouns-first front after `card:carried-state.md` failed
its reader).  A small model is another reader who cannot get in.
Same fix.

---

## Can the rules be trained into an open model?

**Henri:**

> how about open models? would it be possible to Train The tree/house
> rules into a model that would then always follow them? yet fit
> running on a laptop?

**The session:**

Possible, yes.  "Always," no — and the no is load-bearing.

**Training does not install rules; it shifts probabilities.**  A
fine-tuned model has a strong prior toward rule-shaped behavior that
holds in-distribution and fails under novelty, which is when it is
needed.  No amount of fine-tuning turns "usually" into "always."  The
manifesto's second rule already contains the answer: *what is built
must be able to say when it is wrong.*  Weights cannot say when they
are wrong; the suite can.  Enforcement stays outside the model, in
checks the model cannot write to — the cage-builder principle.
Training raises compliance from 80% to 98%; the suite handles the 2%
and has to exist anyway.

**The tree is not training data.**  Fine-tuning on 1,600 lines of
prose yields a model that can *recite* the manifesto.  Behavior needs
demonstrations — (situation → correct action) pairs, hundreds to
thousands: a card arrives and gets questioned; a mechanism guess gets
marked *suspected*; a seam appears and the session stops.  The
transcripts, commits and board history are already this dataset in
the raw.  Caveat stated plainly: distilling Claude transcripts into
an open model runs into Anthropic's usage terms on training competing
models; where the line sits for a personal lab tool is a real
question, and it exists.

**The norms train; the judgment does not.**  Format compliance,
workflow order, "never a `because` that names a fix" — pattern-shaped,
fine-tunes beautifully into 7–14B.  The three-jobs distinction,
knowing *when* to stop at a seam, telling a real blocker from a paper
one — capability, and fine-tuning redirects capability rather than
adding it.  A trained small model will wear the vocabulary perfectly
— *suspected*, seams, callers — draped over judgment that is not
happening.  Arguably worse than a naive model, because it
counterfeits the signals used to trust a session.

**The decisive argument is the philosophical one.**  Baking the tree
into weights trades away the crown-jewel property.  The rules are
plain files: inspectable, diffable, dated *because they change*,
editable in a minute, model swappable underneath.  Weights are
opaque, meaningfully undiffable, frozen at training time.  The vision
changes; `vision.md` is dated for that reason.  A trained model is a
snapshot of the rules as of August disagreeing silently with the tree
as of November — a second source of truth, the mistake the window
design refuses twice by name.

**Mechanics, the cheap part:** laptop means roughly 7–14B
comfortably, up to ~30B quantized on 32–64 GB (Qwen, Llama, Mistral,
Gemma lineages).  QLoRA at that size is a rented-GPU afternoon, tens
of euros, repeatable.  The obstacle is everything above, not this.

**What the same effort buys instead:** small open model, distilled
front in context (context is free to update; weights are not), suite
enforcing structure; fine-tune only against a specific measured
failure — most plausibly format/protocol compliance, the one layer
that trains well and that a small model fumbles.  And if fine-tuning
at all: tune on the *domain* — the gestate language, the codebase
idioms — not on the rules.  Domain knowledge is what context carries
badly and weights carry well; rules are the reverse.

> **Weights for what the model must know, context for what it must
> currently obey, suite for what must be guaranteed.**  The
> architecture already had the third part right; do not move the
> second into the first.

---

## Live rules, and what keeps them from degrading

**Henri:**

> I see that today a session worried My rules would grow too large.
> examining I found they are writing into them. memories. I wonder
> what would ensure that they do not degrade while live? I like that
> liveness.

**The session:**

**Diagnosis: memories in rule files is category leakage, and the
tree's own taxonomy already forbids it** — "what happened goes to
`journal.md`, always past tense."  A memory is journal material; a
rule is a decision.  Sessions violate this for a rational reason:
**writers write where readers read.**  A session that learned
something expensive wants the next session to know it, and the only
files it can trust every future session to read are the method files.
Memories migrate into rules from correct incentive pointed at the
wrong file; a fix that ignores the incentive teaches sessions to
smuggle better.

What is at stake, carried over from the file about the workers, which was not kept: the tree
is the session's memory, so **a session writing into the rules is
programming its successors, unreviewed** — the cage-builder problem
arriving as quiet authorship rather than escape.  `spec/author.md` already
lists a change to a `spec/` contract among the load-bearing seams;
edits to the method files belong on that list, as the highest-leverage
writes in the tree.

The mechanisms, in order of cheapness:

**1. A budget, held by the suite.**  Each method file gets a line
budget on its front — the A3 rule, applied to the method itself.  The
gate is twelve-second-class: count lines, light the andon past
budget.  **Andon, not refusal** — a genuine amendment should not be
blocked, it should be *seen*.  Growth becomes a visible event; the
fourth vision line applied to the tree.

**2. The earning test, per line.**  `vision.md` opens with it: *a
line earns its place by having already decided something*; the
manifesto adds: *a claim with no file, test or number after it is
unfinished.*  Together, an audit a session can run: a line in a rule
file that decides nothing and cites nothing is a memory wearing a
rule's clothes, and it moves to the journal.  Judgment work — a
periodic card, not a gate.

**3. Metabolism, not accretion.**  The liveness is intake; what the
tree lacks is *excretion*.  A living system that only ingests is not
alive, it is swelling.  The pattern is proven in the tree's own
history: append while live, compact at intervals — narrative sediment
to the journal, the decision line stays, and **git makes deletion
lossless**.  "Compact file X back under budget" is a recurring card
triggered by the andon from mechanism 1.  The stranger-test lesson
(900 lines; "the paragraphs belong to the journal") shows sessions
can do the work; the trigger was what was missing.

**4. Falsifiability on a schedule.**  The correction of 2026-08-19 —
"this list is the order" measured against a single day, found false
three times over, corrected — is rule maintenance done right, and it
happened once, by accident.  Institutionalized: each week a session
measures one rule against what actually happened.  A survivor gets
its date refreshed; a failure gets corrected or deleted.  **A rule
nobody has measured in months is suspected**, same as a mechanism
guess.

**5. Route the incentive.**  Give expensive lessons a blessed
destination future sessions provably read: the budgeted *front* of
each method file — one line, one citation — with depth in the
journal.  The lesson reaches its reader; the rules stop being the
only channel.

**And one defense: do not sterilize it.**  The dated amendments, the
corrections quoting the old wrong text — that layering is why the
tree teaches instead of commands, and it is the property that
conditions sessions so strongly.  The goal is not a frozen document.
It is a document whose growth is *seen*, whose lines *earn*, and
whose edits by sessions are *seams the author reviews*.  Liveness
with a metabolism and a witness.
