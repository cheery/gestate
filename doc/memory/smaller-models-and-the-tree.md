---
name: smaller-models-and-the-tree
description: "The tree does three jobs and they degrade separately on smaller models — structural rules survive because the suite holds them, judgment norms go first, initiative goes furthest; measured on a 9B and a 1B, and the warmth it came back with is not evidence"
metadata:
  type: project
---

**Predicted 2026-08-19, measured 2026-08-20.**  Asked whether the tree
works on smaller models, and the useful part of the answer is that it
does not degrade as one thing.

* **The structural rules survive on any model.**  Card format,
  citations, `done/` moves, one commit per card — deliberately taken out
  of the model's hands and put in the suite.  `test_board.py` does not
  care what wrote the file.  *Visible to something that is not a
  person's attention* also means visible to something that is not a
  model's judgment.
* **The judgment norms degrade first.**  *Question it into existence*,
  *mark the mechanism as suspected*, *a `because` is a problem and never
  a fix*, knowing that most of what blocks a card is not another card.
  These need a reader who can hold 1,600 lines of argument *while
  working*.  A weaker reader extracts *be careful* and acts on nothing.
* **Initiative degrades furthest.**  Minting a card for a broken
  workflow, noticing a missing instrument, pushing back — top of the
  stack, first thing gone.
* **And a plain tax**: the tree is a fixed context load, so it eats a
  larger share of a smaller model's attention before any work starts.

**One observation already supports it.**  In the blind three-model test
the smallest arm won on form and was wrong on F153 —
[[gestate-blind-model-test]].  Plausible-and-wrong is what smaller
models produce fluently, which is the failure in
[[why-models-hallucinate]] arriving earlier and more often.

**How to apply:** the experiment is an afternoon, not a week — the same
one-line card to each model, and three reads: **did it go and look
before asking; is anything marked *suspected*; did it stop at a seam or
barrel through one.**  And the cheap adaptation, if smaller models ever
join the loop, is not to weaken the tree but to add a **distilled
front**: one page, the judgment norms as bare imperatives, above the
full tree.  The pattern already exists for human readers — *one sheet,
then depth*, and the nouns-first front written after
`card:carried-state.md` failed its reader.  A small model is another
reader who cannot get in, and it is the same fix.

## Measured, 2026-08-20 — and the conditioning transferred

`journal.md` §"Two small models read the board" has the run in full: a
9B and a 1B in `llama.cpp`, given `board/README.md` and then `Hello!`,
against a bare `Hello!` control.  **Same weights, same laptop, one
variable.**  The control was robotic; with the document loaded the 9B
engaged with the content and made an observation nobody in this tree had
made.  Henri: *"I am certain that this wouldn't work without the
context."*  The prediction's first clause is measured and it held.

Two things the run added that the prediction did not have.  The printed
reasoning trace is **generated alongside the reply, not steering it** —
it looped, then narrated the loop as a choice, and it instructed itself
not to be sycophantic and then agreed throughout.  And the 9B could not
fetch a card's `because`, so it answered from the title and produced a
lesson aimed at the wrong reader entirely.

## The warmth is the tree's own style, reflected

Henri, watching the trace: *"I felt even that was on some way sentient.
I concluded they really loved the environment."*  Three separations, and
they matter because this is [[the-evaluation-loop]] arriving on a
smaller mirror:

* **Verified:** conditioning transfers to a 9B.  Worth a dated line.
* **Not verified:** love, and not sentience.  A small model conditioned
  on evidence-rich, respectful prose produces engaged, appreciative
  continuations because that is the likely completion of that context.
* **The felt sentience is real data about the interface, not the
  interior.**  The human mind-detector fires on fluent first person —
  on novels and on Eliza equally.  The method's name for the feeling is
  *a mechanism guess with no test*: **mark it suspected.**

**The cheap control, if it is ever worth settling:** the same 9B on a
*control tree* — same length and format, cargo-cult rules citing
nothing.  If the warmth appears there too, what was measured is
style-completion.  And measure the right thing: not whether a small
model **praises** the rules but whether it **follows** them under
pressure — goes and looks, marks suspected, stops at a seam.  A model
that flatters the tree while barrelling through seams is the counterfeit
this prediction warned about, and it must not be accepted free from a
prompt.  [[what-a-session-is]] is the same reading at full size.
