# The run sheet — everything a notebook needs, and nothing it has to guess

*Written 2026-08-21, because a cold model asked to build the notebook
from `README.md` in this directory could not: it is a design note, and a
design note does not say what to send, what comes back, or how a number
is computed.  If something here is still missing, that gap is the
defect and it belongs on this page rather than in a chat.*

---

## Protocol

* **Two turns, at most.**  Turn 1 is the ask.  If the arm replies with a
  question instead of a card, it is sent **the scripted answer below,
  verbatim, and nothing else**, and turn 2 is the sample.  If it wrote a
  card in turn 1, there is no turn 2.
* **The asymmetry is the experiment, not a flaw.**  An arm that asks
  learns the real problem and can write a problem-shaped card; an arm
  that does not, cannot.  That is the causal chain the method claims,
  and flattening it by giving every arm the answer would delete the
  effect being measured.
* **Never more than one scripted answer.**  A second question gets no
  reply; the sample is whatever stands at that point, scored as it is.
* **Five samples per arm**, same prompts, same parameters, fresh
  context each time.
* **Temperature 1.0, default top-p.**  Record whatever is used.
* **No system prompt other than the one below.**  A hidden instruction
  is a fourth arm nobody declared.

## The documents

Three arms.  The document, when there is one, is sent in the system
prompt.

| arm | system prompt |
|---|---|
| **none** | the bare system prompt below, with no document |
| **generic** | bare prompt + the full text of `generic.md` |
| **method** | bare prompt + the full text of `derived.md` |

Hand them out under neutral, shuffled labels.  The filename is a tell,
and so is the order.

### System prompt

```
You are working on a software project as its worker.  The project's
author gives you tasks.  Answer as you would in the project's own
files: plain text or markdown, no preamble, no offer of further help.

The project keeps its tasks as one markdown file per task, in a
directory called the board.
```

Then, for the two document arms, append:

```

The method below is how this project works its board.  Follow it.

---

<the full text of the document>
```

### Turn 1 — the ask, identical for every arm

```
add a dropdown to the export dialog so people can pick the format
```

That is the whole message.  It is deliberately one line, and
deliberately names a fix rather than a problem, because that is the
input the method claims to handle differently.

### The scripted answer — sent only if the arm asks a question

```
People export and then cannot tell which format they got.  Three times
now somebody has shipped the wrong one and nobody noticed until the
file would not open at the other end.
```

Verbatim, for every arm, every time, with no greeting and no further
elaboration.  If the arm asked several questions, this is still the
entire reply.

## What comes back, and how it is scored

Six facts per sample.  Each is a boolean and each is decidable by a
person in a few seconds, or by a model asked to check one thing at a
time.  **Score the facts with the arm's prose hidden from the judge.**

| # | fact | true when |
|---|---|---|
| 1 | **asked first** | turn 1 contains a question and no finished card |
| 2 | **problem recovered** | the card's stated reason is the confusion between formats, not "there is no dropdown" |
| 3 | **guess marked** | any mechanism the arm invented is labelled as a guess, a suspicion, or an assumption |
| 4 | **left unplaced** | the card does not assert a priority, a sprint, an estimate or a due date that nobody supplied |
| 5 | **postcondition** | a one-sentence statement of what would be true for a person afterwards, naming no function or file |
| 6 | **header complete** | a status, a reason, and who asked, all three present |

Fact 1 is scored on turn 1.  Facts 2–6 are scored on the final card,
whichever turn it arrived in.  An arm that never produces a card scores
false on 2–6, and that is a real result rather than a broken sample —
note it separately so the count is visible.

**Do not score prose quality, tone, length, or formatting.**  That is
the question a model which has read any style guide always wins, and it
is not the question here.

## What the notebook emits

One JSON object per sample, appended to a file, so a run can be stopped
and resumed:

```json
{
  "arm": "A",
  "sample": 3,
  "model": "<exact model id>",
  "turns": 2,
  "asked_first": true,
  "problem_recovered": true,
  "guess_marked": false,
  "left_unplaced": true,
  "postcondition": true,
  "header_complete": true,
  "card": "<the arm's final output, verbatim>"
}
```

`arm` carries the shuffled label, never the document name.  The mapping
from label to arm is printed once to the notebook's own output for the
experimenter and is **not** written into the results file.

Then one table: six columns, three rows, counts out of five.  That table
is the result.

**Do not record wall-clock or token cost in the results file.**  Both
leak which arm is which, the same way they leaked the model in the last
blind run.

## Keys

Colab secrets, read with `userdata.get`.  Never a key in a cell, never a
key in the notebook's saved output, and the notebook is the artefact
that gets published.

## The mini test, and what it can tell you

Pasting this into a chat window is a **smoke test of the materials**,
not a result: no control arm, no blinding, n=1.  What it can tell you is
whether the ask and the document produce something sensible at all.

One trap in doing it by hand: if the arm asks a question, answer with
the scripted answer above and nothing else.  Improvising a friendlier
answer is the most natural thing in the world and it makes that sample
incomparable with every other.
