# rules.md — the method is capped at 2000 lines, and the cap is measured

*Written as a contract, 2026-08-20, at Henri's ask, at five in the
morning.  The cap is stated here and nowhere else; the count is
`tools/rulecount.py`; the gate that fails a commit over the cap goes in
when the count is first under it, and `card:working-standard.md` owns
getting it there.*

`spec/` is where this belongs.  A spec in this tree tells about a
contract written in software, and this is one: the method that runs the
project has a size, the size is finite for a reason that is not taste,
and a number that nobody measures is a mood.

---

## The rule

**The rules set is five documents and it may not exceed 2000 lines
total.**

| file | what it is |
|---|---|
| `board/README.md` | how a task is worked |
| `manifesto.md` | how an instrument fails |
| `spec/author.md` | what the author spends attention on |
| `doc/instruments.md` | what a session already has to work with |
| `vision.md` | what any of it is for |

*2000 for now* — Henri, 2026-08-20.  The number is allowed to move,
by him, in writing, with the date.  It is not allowed to move because a
session found it inconvenient on a Tuesday.

## Why there is a cap at all

Because a session reads **all five, every time**, before it knows what
it is working on.  That is what makes them rules rather than reference.
`spec/` is 16,000 lines and costs nothing until you touch the part it
describes; the rules cost their full size on every single shift, and
they come out of the same window the work has to fit in.  Past some
size the method stops being what makes a session effective and starts
being what crowds out the thing it was supposed to help with.

Growth is not hypothetical.  Measured the night the cap was set:

| | 2026-08-18 | 2026-08-20 |
|---|---|---|
| `board/README.md` | 483 | 700 |
| `doc/instruments.md` | 210 | 457 |
| `spec/author.md` | 379 | 410 |
| `manifesto.md` | 408 | 409 |
| `vision.md` | — | 74 |
| **total** | **1,554** *(four files)* | **2,050** |

**+422 lines in two days**, and `doc/instruments.md` more than doubled.
The cap was over the moment it was written.  That is the finding, not a
detail: it was set as a guardrail and it landed as a debt.

## What the fat is

**Session narration.**  Henri, 2026-08-20: *"The rules have gotten
narration from sessions that belongs into the journal."*

A rule document accumulates the story of how each rule was arrived at,
because the session that arrived at it was proud of the arriving.  The
story is worth keeping — it is why `journal.md` exists — but it is not
the rule, and it is charged to every future session at full price.  The
test is whether a stranger who never saw the incident needs the
sentence in order to *follow* the rule.  If they only need it to
*believe* the rule, it is journal.

The other known fat is restatement: one rule stated three times inside a
single file, recorded in `card:working-standard.md` on 2026-08-18 and
still true.

## The three cheats

Named because they are the ways the cap gets met without the context
getting smaller, and all three are easier than trimming.

**A sixth document is a cheat.** *(Henri, 2026-08-20: "Agreed, sixth
document is cheat.")*  Splitting `board/README.md` in two gets the
per-file numbers down and leaves the reading identical — worse than
identical, because now a session must find both halves.  The cap is on
the **set**, and the set is closed at five.  A sixth needs a caller,
the same rule the atlas closed at five sheets under.

**Dropping dates is a cheat.** *(Henri, 2026-08-20: "Dates are not the
fat, agreed.")*  A rule without its date cannot be argued with later —
you cannot tell a standing decision from a leftover, and the thing that
makes this method work is that a rule can be taken back by the person
who set it.  Dates are the cheapest lines in the corpus and the last
ones to go.

**Pushing text into another rule is a cheat.**  Moving narration out of
`doc/instruments.md` and into `board/README.md` changes no total.  The
only honest destinations are `journal.md`, a card, or deletion.

## The proof

A cap that is not measured is a mood — `manifesto.md`'s rule, the same
one `spec/sandbox.md` applies to the fence.

    python tools/rulecount.py

prints the five files, the total, and the room left, and exits non-zero
over the cap.  It was held out of `tools/suite.py`'s `GATES` at first,
because a gate that is red the day it arrives blocks every commit for
work that has nothing to do with it — **it joined the first time the
count came in under 2000**, which was the same morning, at 1,983.

It is now `test/test_rules.py`, and from here it is the ordinary defect
class that set lives on: a structural check that a session doing
ordinary work breaks.  The script stays alongside it, because it prints
the **room left** and a green gate does not.
