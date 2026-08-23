# The method — for someone who was shown this tree

*One page, and it is the whole tour.  If somebody handed you this
repository and you want to know what you are looking at before deciding
whether to look further, read this and stop.  Nothing here is a rule you
have to follow, and nothing asks you to believe anything you cannot check
in the tree yourself.*

---

## What this is

gestate is a programming language for sound and moving pictures.  That
is [`README.md`](../README.md), and you can hear it in about ten
minutes.

This page is about the **other** thing in the repository, which is
usually what a visitor was actually being shown: the project is run as a
manufacturing line, and the method that runs it is written down, kept in
files, and checked by the test suite alongside the code.

It started 2026-08-08.  Thirteen days later it was 413 commits, written
by one person and a succession of AI sessions that remember nothing
between conversations.

**That constraint is the whole design premise.**  A collaborator who
forgets everything cannot be told anything — so everything it needs has
to be *in the tree*, and anything in the tree that is wrong will be
believed.  Which turns out to be the same problem the author has with
his own memory a month later, and the same problem you have right now,
reading this cold.  One fix serves all three.

## What it is for

Not productivity.  The measurable goal is that **a claim in this
repository can be checked**, and that the checking is somebody's job in
software rather than somebody's intention.

Three habits follow, and they are most of it:

* **A claim with no file, test or number is unfinished.**  "It is fast"
  is not a statement here; a millisecond count with the command that
  produced it is.
* **A defect is a caller.**  When something breaks, the deliverable is
  not a fix and an apology — it is the *mechanism* that makes the same
  class of mistake fail loudly and early next time.  Usually a test that
  takes under a second.
* **Go and look.**  Before explaining why something behaves as it does,
  describe what it actually did.  Most confident explanations here have
  been wrong, and there is a register of them.

## What it is not

* **Not a framework, and not advice.** It is one project's working
  arrangement, and the parts that transfer are the mechanisms, not the
  prose. A copy of the sentences without the suite is the cargo cult
  this method spends most of its time trying not to be.
* **Not finished, and not claimed to be.** The open defects are listed,
  the unbuilt parts are in [`roadmap.md`](../roadmap.md) with reasons,
  and the entries that turned out to be wrong were corrected in place
  with the correction dated rather than quietly edited away.
* **Not for sale, and not asking for anything.** No stars, no adoption,
  no belief. The tortoise shows the shell to whoever knocks and walks on
  either way.

## What is actually enforced

Twelve structural checks run at every commit, through a git hook, in
about fourteen seconds. They test nothing about whether the program
works — that is a separate twenty-five-minute suite. They test that the
tree still agrees with itself, which is the property that editing the
tree breaks:

| the gate refuses | because |
|---|---|
| a `§"…"` citation pointing at a heading that no longer exists | three had already rotted silently before anything checked |
| a person's words quoted who is not in [`consent.md`](consent.md) | the repository is public and other people's speech is in it |
| a generated page behind the source it describes | five A3 sheets, the API reference, the complaints register |
| a register whose own header miscounts its entries | the defect ledger said 130 when it held 155 |
| the five method documents growing past 2,000 lines | they are read before a session knows what it is working on |
| the journal's month index falling behind its archive | the index is the only way into a closed month |

The last two are lamps rather than refusals. Growth in the method is
allowed to happen and is not allowed to happen *quietly* — a gate that
refuses a genuine amendment does not prevent the growth, it teaches the
next writer to make the method worse in smaller words.

## Where the depth lives

Nothing here is required reading, and the sizes are given so you can
decline honestly:

| | lines | who it is for |
|---|---|---|
| [`README.md`](../README.md) | 254 | you, if you want to hear it |
| [`vision.md`](../vision.md) | 77 | what any of this is for; the author's own, dated |
| [`manifesto.md`](../manifesto.md) | 377 | how an instrument fails, and the two standing rules |
| [`board/README.md`](../board/README.md) | 623 | how a task is worked — written for sessions |
| [`spec/`](../spec/) | ~16,000 | how each part is designed, and what it cost |
| [`fixme.md`](../fixme.md) | 180 entries, 151 resolved | where the implementation disagrees with the specs |
| [`journal.md`](../journal.md) + `journal/` | the current month, plus one line per closed month | what happened, past tense |
| [`doc/memory/`](memory/) | one fact per file | what a session that forgets everything carries across |
| [`keeper.md`](../keeper.md) | 206 | standard work for the one person who keeps all of the above |

Two of those are worth a word. `fixme.md` is a **register, not a
backlog**: an entry is closed by being marked resolved, never by being
deleted, so the twenty-nine open ones are visible on purpose. And the
journal is long — 10,433 lines for its first month — which is why it
rotates into `journal/YYYY-MM.md` behind an index. Read the index line,
open the one month you wanted.

**The journal has people in it.** People other than the author are
quoted by name, and each was asked before a word of theirs entered the
tree —
[`consent.md`](consent.md) is the register, with what each person agreed
to and what they declined. If you find yourself in this tree and would
rather not be, that register is where it gets fixed.

---

*That is the sheet.  One story at length follows, because the method is
easier to believe from a defect it actually caught than from a
description of itself.*

## One paid lesson

The way in to a program is the part its author cannot read.

On 2026-08-17 the author installed gestate from nothing on a fresh
laptop, walking his own instructions, and found three defects in them.
The next day a friend who had never seen the repository was asked to try
it over chat. He cloned it at 13:22 and heard his own edit at 13:52 —
thirty minutes, and half of them were spent getting in.

The first instruction in the front door read:

```sh
git clone <this-repo>
```

He asked what he was supposed to put there.

**It had survived the author's own fresh-laptop walk the day before,
because the author knows what goes in the blank.** Not carelessness: the
missing information was in his head, so his own reading could not be the
instrument. It is in the ledger as F162.

The second one is better. The step that made `cargo` available lived as
a *trailing comment* on the end of a long `curl … | sh` line — the
weakest position a required step can hold — so a reader who stayed in
the same shell had it installed and invisible. It failed several steps
later, in a different tool, as a Python traceback, by which point he had
done six things correctly and had no reason to look back at step two.
And the error he reached told him to run `cargo build` — **an
instruction that cannot be carried out by definition, since the reason
it printed is that cargo does not exist.** Worse than saying nothing,
because he spent his time obeying it.

What the method does with that is the part worth showing. Neither defect
got a careful edit and a promise. Both got a mechanism:

* a test that refuses any `<placeholder>` inside a shell block in the
  two files that are the way in, so the front door can never again ask a
  stranger to fill in a blank only the author can fill;
* every error message the program can print is now in
  [`complaints.md`](complaints.md) with a verdict on whether a person
  who hit it could act on it, and the suite refuses a message that is
  not in the register.

The friend's report also carried the more interesting finding, and it
came from one neutral question. Asked how long the build took, he said
*ten to fifteen seconds* — and had already volunteered, unasked, that it
was a fairly long delay. **Ten seconds is nothing by build standards, so
the defect was never the duration.** The wait said nothing while it
happened. That is a different bug than the one anybody would have filed
from the transcript.

