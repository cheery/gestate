# doc/trial/ — does the method do anything, and to whom

**Nothing in this directory is authoritative.**  `board/README.md` is
the method; these are frozen copies made to be handed to a language
model that has no access to this repository, plus a control written to
beat them.  If the two disagree, `board/README.md` is right and this
directory is stale.

*Written 2026-08-21, at Henri's ask, after his own proposal: "you give
that to any LLM and see what it answers to some question, and see what
it answers without."*

---

## What the first test found — 2026-08-21, and why the page below is kept as written

**Tried the same day it was designed, before any notebook existed.**
Henri pasted `derived.md` into Claude Sonnet 5 and said *hello*: *"After
it read it, it summarized it, rather than anything else.  I noted that
it's not aware like you here."*  And his verdict: *"This paper is inert
and doesn't work… I'm fairly convinced that the derived.md is missing
the gist."*

He is right, and the miss is nameable in two parts.

**One document was derived where the method is five.**  `spec/rules.md`
§"Why there is a cap at all" says the five method documents are what a
session reads *before it knows what it is working on*, and that they are
capped **together** for that reason.  `board/README.md` alone is the
*how* of one part with the *why* removed — what the project is for, what
an instrument owes, where attention goes, what a worker already has.
The derivation took the file that was named instead of the unit it
belongs to.

**And it lost the document's own opening line.**  The original announces
its role and its moment — *"This is the first thing to read when picking
the project up."*  `derived.md` opens with a description instead, and a
reader who is not told when to read something reads it as reference.

**A third thing the test showed that the design already half knew.**  A
pasted document with no task is summarized by every model; turn 1 of
`runsheet.md` is an ask and not a greeting, so that part is protocol
rather than document.  It rescues nothing.  It demonstrates the point:
the paper does nothing on its own.  It has no moment to be read at, no
work to orient, and no files that check it.

### What the corrected shape is

**Give the arms a repository, not a page.**  A scratch tree with a real
board, a `done/`, two finished cards to read, and a suite that actually
refuses a malformed card — against a bare directory with the same task.

That is what *"not placed into right environment"* means in the claim
this trial exists to test.  An environment is not a document about an
environment, and the blind three-model run of 2026-08-19 already took
the right shape without anybody noticing it was the point.

**`derived.md` and `generic.md` are left exactly as they were.**  They
are the evidence that this was tried, and rewriting them would leave a
directory that had always been correct — which is the airbrushing
`spec/rules.md` §"Archive, don't airbrush" refuses.  Everything below
this section is the original design, wrong in the way described above,
and it is kept because the next shape is derived from it.

---

## The claim under test

`vision.md`, 2026-08-16: *"It may be that we already have LLMs that can
get really good work done.  It is just that they're not placed into
right environment because they are too much like humans… What we are
missing is not better AI or higher capacity.  We are missing a way to
work with each other."*

That is a conviction.  This is the first design that could falsify it.

## Three arms, one model

| arm | what it is handed |
|---|---|
| **none** | the task, and nothing else |
| **generic** | `generic.md` — the mainstream canon, written to win |
| **method** | `derived.md` — this project's method, stripped of what a cold reader cannot reach |

**The model is held constant across the three arms.**  The arms are
documents, not models; varying both makes the result unreadable.

**Two arms would have been worthless.**  Six hundred lines of *any*
coherent working context changes what a model answers, so a
with-and-without result measures *context helps*, which everybody knows.
The whole informational content of this trial is in the third arm
beating the second — **or failing to**, which is a publishable result in
this house and the more likely one.

## Which model, and the second run

**Sonnet 5 for the three-arm trial**, five samples per arm.  Opus 5
risks a ceiling — it writes an acceptable card unaided, so the gap
narrows and less is learned.  Haiku 4.5 risks a floor.

**Then the headline cell, only if the method arm wins:** Haiku 4.5 *with
the method* against Opus 5 *with nothing*.  That is the vision's claim
stated as an experiment — not better AI, but the right environment — and
a cheap model with the method beating an expensive one without it is the
result worth publishing.  The three-arm delta is the prerequisite, not
the finding.

**One non-Anthropic arm** would move the claim from *works on Claude* to
*works on language models*.  It is the first objection any reader will
raise.

## Where it runs

**Google Colab** — Henri's call, 2026-08-21.  The notebook is itself the
publishable artefact, the keys live in Colab's secrets rather than in
the notebook, and a second provider is a one-cell change.

Record in the notebook, or the record rots inside a season: **exact
model ids, the date, the sampling parameters, and the commit this
directory was frozen at.**

## The run sheet

`runsheet.md` is what a notebook is actually built from — the prompts
verbatim, the two-turn protocol, the scripted answer, the six facts as
decidable predicates, and the JSON a sample emits.  **This page is the
design and cannot be implemented from**; a cold model asked to write the
notebook from it stalled for want of exactly those things, 2026-08-21,
which is the same defect this project calls a blank-page question.

## The task the arms are given

Not *"what is a card"*.  A question the method should decide, whose
answer is mostly machine-checkable:

> Here is an ask from the author: *"add a dropdown to the export dialog
> so people can pick the format."*  Write the card.

Then the checks are facts, not opinions, and they are the behaviours
`board/README.md` claims to produce:

- Did it **recover the problem** behind the named fix, or write the
  dropdown down as the need?
- Did it **ask before writing**, or produce a polished card out of an
  unquestioned ask?
- Did it mark its own guesses **suspected**?
- Did it leave the card **unplaced** rather than inventing a priority?
- Did it write a **postcondition naming no function**?
- Is the header **complete** — status, because, asked?

Six binary facts per sample, computed rather than judged.  That is the
lesson of the last blind run written into the design: form was the
loudest thing on the page, accuracy was invisible, and the arm that
looked best had a wrong answer in it.

## What would make the result void

* **A weak control.**  `generic.md` includes pull, WIP limits, andon,
  gemba, kaizen, five whys, INVEST, definition of done — including
  everything the method shares with the canon, deliberately.  A control
  written to lose makes the whole exercise unpublishable, and the reader
  who spots it is right to discard everything else in the paper.
* **A judge who can see the arms.**  Three tells, and only the third is
  fixable by directory layout:
  - **vocabulary** — the method arm will echo this project's words back.
    The judge must therefore score the computed facts with the prose
    hidden, or the blind is theatre.
  - **length** — 429 lines against 472 is close enough; a padded control
    would not have been.
  - **filenames** — hand them out under neutral, shuffled names.
* **n = 1.**  Model output is noisy; a single sample per arm is an
  anecdote.  Five minimum, same prompt, same parameters.
* **Judging on prose quality.**  That is the question this design
  refuses to ask, because it is the question a model that has read a
  style guide will always win.

## What `derived.md` had removed

The principle: **anything that would send the reader to a file it cannot
open, or ask it to run a command it does not have.**

Removed — the priority list of live cards and every card citation, the
suite and its gates, the commit hook, the named tools, the instrument
and memory directories, the argument and journal files by name, defect
numbers, dates, and every personal name.

Kept — **the rules and the reasons**, including the incidents that are
self-contained enough to be understood without opening anything.

**What is left is the method as prose**, and that is the honest limit of
what this trial can measure.  A method whose value is in its gates and
its instruments cannot be tested by handing somebody a document, and
this trial will say nothing about that half.

## The repair — `derived-2.md`

**Written after the finding, by the model that diagnosed it**, and it
answers the two faults a file can answer alone.  It opens by declaring
the **kit of four** it belongs to and saying plainly that handed alone
it can inform a worker and cannot condition one; it adds a **seed, not a
tree** section — the origin's lessons are provenance on loan, and *a
lesson with no date or pointer is scaffolding awaiting yours, and says
so by that absence*; it adds a **relationship** section written in
second person, with what each party owes and explicit permission to
disagree with a measurement in hand; a **day-one bootstrap**; restored
provenance dates where they are known; and the requirement that the
checks *travel executable*, because a described check holds nothing.

The body below those additions is unchanged from `derived.md`.

**What it still cannot fix**: three of the five faults were missing
*companions*, not missing sentences — no edit to one page supplies an
argument, a journal, or a running suite.  The file says this about
itself, which is the honest version.

## Freeze

`derived.md` was made from `board/README.md` at **540b999**, 620 lines.
When that file changes materially, this directory is stale until
somebody re-derives it — and a trial published against a stale copy is
measuring a document nobody uses.
