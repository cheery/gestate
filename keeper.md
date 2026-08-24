# keeper.md — standard work for the fire

*Written 2026-08-21, at Henri's ask, and the reason is his own sentence
from the same morning: "I am really uncertain that I am up for this
task."*

**The doubt is measuring the task as it looks from inside a tired week**
— half a megabyte of journal, a board, a queue of decisions, a set of
lamps nobody is watching.  Held in the head, where it inflates, that is
a fog.  Written on a page it is five acts, thirty to sixty minutes, and
every one of them was already designed and most of them are already
automated.

That is the same cure the sessions get.  This tree is a prosthetic for
two readers who forget — the sessions between conversations, the author
between weeks — and until now only one of them had been given a page.
**Fix the task, not the person**; Toyota never asked for heroic
operators, it wrote standard work so the job could be done on a tired
Tuesday.

---

## Who this is for, and what it is not

**Henri.**  A session does not read this file, and that is what keeps it
from being a sixth rule: the five capped documents are what a session
reads *before it knows what it is working on* (`spec/rules.md`), and
this is not read before the work — it **is** the work, once a week, by
the one person who does it.

**And it must never become a demand.**  `vision.md`: *won't demand your
presence.*  A missed evening is not a red gate, nothing on this page can
fail a commit, and there is no streak to keep.  A metabolism that
punishes an absence breaks the line that makes the tree safe to own.
Skipping three weeks and doing one act on the fourth is the ritual
working, not the ritual failing.

## The cadence

| | when | about |
|---|---|---|
| 1. Read the lamps | every fire | 1 min |
| 2. Open the decisions batch | every fire | 10–20 min |
| 3. Measure one rule | every fire | 10 min |
| 4. One pass over the pile | every fire | 10 min |
| 5. Rotate the journal | when the lamp says so — about monthly | 30 min |

Weekly is the shape it was proposed at.  The cadence is yours to move;
what is not yours to move is doing them in the head instead of on the
page.

---

## 1. Read the lamps

One command, and it is the same one the commit hook runs:

```sh
python3 tools/suite.py --gates
```

Twelve structural checks, about fourteen seconds, and then a page at
`test/gates.md` with two rows that are the whole of this act:

* **Rules** — the five method documents against 2,000 lines.
* **Journal** — the open month against its budget.

Green on both and this act is over.  A lamp lit is **not** a failure and
does not want fixing now; it wants act 5, or a decision, and it will
still be lit next week.  The pull versions, when you want to see where
the lines are: `python3 tools/rulecount.py` and `python3
tools/journalroll.py`.

## 2. Open the decisions batch

The cards blocked on a decision, opened **together** rather than one at
a time across a week — five in one sitting cost less than five arriving
separately, which is the same reason the andon batches its questions.

Each one should arrive already shaped, and if it did not, that is a
defect in the session that wrote it, not work for you:

* the question in **one line**;
* two or three **named options with their costs**;
* **a default with a trigger** — *"if undecided by Friday, X"*;
* **reversibility stated**, so you know which kind of door it is;
* the recommendation marked as the session's, and *suspected*.

**Approving a default is about ten times cheaper than composing an
answer**, and it is the move this act is built around.  Most of these
take a minute.  `doc/memory/decisions-arrive-shaped.md` is the contract
the sessions are held to; a blank-page question is one of them skipping
a gate.

## 3. Measure one rule against the week that happened

One rule.  Not an audit — the tree is 16,000 lines of spec and the point
of picking one is that picking one is finishable.

**Closed book first.**  Before opening it, write what the rule says from
memory, in a sentence — then open it.  The gap is a reading on your
recall *and* on the rule: one you cannot approximate from memory is one
nobody could have followed, which is the third outcome below arriving
early.  (`card:memory-atrophy.md`, move 1 — 2026-08-24.)

Then ask of the week you actually had: **did this rule decide
anything?**  Three honest outcomes, and two of them are findings:

* **It held** — it was followed and it changed an outcome.  Nothing to
  do; note the date if the rule carries one.
* **It was broken and nothing noticed** — then the rule is prose, and
  the deliverable is the mechanism, not the resolution.  A defect is a
  caller.
* **Nobody could have followed it** — it was unclear, unreachable, or
  contradicted by another rule.  Then it is fat or it is wrong, and
  either way it is a line the cap gets back — `python tools/rulecount.py` says how many are left.

*A number nobody asked for is a number nobody checks* is the standing
version of this act.  Doing it to one rule a week is what keeps it from
being a resolution to be more careful.

**One rule already has its meter**, so it is the cheapest week to pick:

```sh
python3 tools/sittings.py --days 7
```

The sitting limit you set on 2026-08-21, against the week that actually
happened — how many sittings, how long, how often the limit was reached,
and **how many of those were followed straight by sitting down again**.
That last column is the act's three outcomes already sorted: kept means
it held, and reached-then-granted every time means either the number is
wrong or the rule is prose.  A meter and not a nagger — it says nothing
unless you run it, which is the only register a number about a person
survives in.  *`tools/gapcheck.py` reads the same ledger for the other
open number, the 30-minute silence nobody chose.*

## 4. One pass over the pile

`board/later/`, one question per card, and it is the only question:

> **Is this waiting on an event, or on me?**

* **On an event** — a milestone, a person, a measurement, another card.
  That is *sediment*, it costs nothing while it waits, and it wakes up
  on its own.  Leave it.
* **On you** — that is *debt*.  It is not shelved, it is **blocked on a
  decision**, and it costs attention every time it is read past.  Move
  it into next fire's act 2.

Do not tidy a debt card by re-shelving it with a better sentence.  A
deep `later/` is a rich board, not a fat one — but only half the time,
and this pass is which half.

## 5. Rotate the journal

When the Journal lamp says the rotation is due.  Four steps, in order,
and the full contract is `spec/rules.md` §"The rotation is an act of the
fire":

1. **Skim the closing month once.**  At heading level.  Not a read.
2. **Promote the two or three lines that pass the earning test** into
   the method files.  The test: would a stranger who never saw the
   incident need this sentence in order to *follow* the rule?  If they
   only need it to *believe* the rule, it stays journal.  **Most months
   promote nothing, and that is the expected result.**
3. **Write the index line** — one line naming the month's themes, so a
   session looking for June's audio work opens June and nothing else.
   Leave the heat out; a month is not owed a theme it would rather not
   have.
4. **Close the file:**

```sh
python3 tools/journalroll.py --roll --themes "…"
```

Nothing is rewritten.  Git already remembers, and a journal that is
retroactively edited becomes a second source of truth about the past —
`spec/rules.md` §"Archive, don't airbrush".

**Steps 1, 3 and 4 a session may draft for you.  Step 2 is yours**, and
not out of ceremony: it edits the five documents, and `spec/author.md`
is the author's.

---

## If the doubt turns up while you are doing this

Do not introspect.  **Go and look** — the same rule, pointed inward.
`board/done/`, the journal and `doc/memory/` record the allegedly
too-hard parts already being done, with dates: seventeen cards finished,
the whole method written and capped inside two weeks, a session caught
writing into the rules and the seam named for it, a flattering claim
declined rather than banked, a stranger test run on a real person, and
consent asked before anybody's words entered a public tree.

The feeling says maybe not.  The ledger says already, repeatedly, with
dates.  In this house it is written down which one of those wins.

**And the precedent is yours, not the tree's.**  A weekly blog, kept for
years, is this ritual's exact shape — recurring, reflective, written,
survives tired Tuesdays.  This is not a new habit to build.  It is an
existing one to repoint.

## What this page cannot do

Procedure and memory, yes.  **Conviction, no.**  What gestate is for,
which door to go through, when to stop — that five per cent is
structurally the author's and cannot be delegated to a file or to
something that reads one.  A tree that tells its keeper it can carry
that part is a mirror, and the standing caveat applies to comfort too:
keep the anchors that are not this repository.
