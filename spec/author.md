# author.md — the author's job, when the work outruns reading

*Written 2026-08-16 at Henri's ask, and meant to be re-read.  The
occasion was his question, after a day of five commits he had not
watched being made:*

> I absolutely have difficulties with the volume outrunning review.  But
> I don't know a solution to that yet.  As a human I have limited span of
> time to read things.  I prefer reading specifications and sometimes I
> love looking into the code as well, but not as often.  **What would you
> do in my place?**

*Companion to `manifesto.md` (how the project is worked),
`board/README.md` (how a task is worked), and `doc/reading-the-log.md`
(how a commit is read).  Those three say what to do.  This one says
what to spend attention on, which is the scarcer question.*

---

## The problem, stated without softening

Two hundred and seventy-odd commits in nine days, around thirty a
calendar day, written by something that does not get tired.  Auto mode
is on.  The fence and the deny-list stop the work *damaging* anything —
and **neither has any opinion about whether it was right**.  That gap is
review, and no person reviews thirty commits a day properly.  Pretending
otherwise produces the worst outcome available: review that feels like
oversight and functions as a rubber stamp.

The instinct is to read faster or read less carefully.  Both are wrong.
The way out is to notice that **review is three different jobs**, and
only one of them is the author's.

---

## Review is three jobs.  One is yours.

| what it catches | cheapest detector | your share |
|---|---|---|
| **wrong behaviour** — it does not do what it says | tests, goldens, oracles | none, and spending attention here is the most expensive mistake available |
| **accumulating mess** — rot, drift, dead citations, stale docs | checks that run in the suite | none, once each one is written |
| **wrong direction** — it is the wrong idea, well built | **the author, and nothing else** | all of it |

The evidence is a single ordinary day.  Five mistakes were made on
2026-08-16.  Three were caught by machines within minutes — `doc/ref/`
gone stale, three rotted citations, a broken card link.  Two were caught
by Henri, and both were *judgement* rather than defect: a full suite run
started outside `tools/suite.py`, and a task referred to by a number that
meant two different things.  A person who had been asked to catch all
five would have been exhausted and would have caught the wrong three.

**So do not read diffs to find bugs.**  You will be slower and worse at
it than the suite, and every minute spent there is a minute not spent on
the only job that is actually yours.

---

## A diff is the worst medium for the job that is yours

You cannot see *this is the wrong idea* in four hundred changed lines.
Wrongness of direction shows up in a **name**, an **interface**, a
**refusal**, and in the sentence explaining why something was built at
all.  Those are prose, and prose is what you already said you prefer to
read.  That preference is not a limitation to work around.  It is the
correct instinct about where your attention is worth most.

---

## The risk lives at the seams

Most lines are recoverable.  Implementation can be rewritten, tests can
be rewritten, comments can be rewritten, and the cost of being wrong is
an afternoon.  A small minority of changes are **hard to reverse**
because other things immediately come to depend on them:

* a new word in the language or in `command.ges` — a vocabulary is a
  promise, and the rule is already that it does not exist unless it is
  written there
* a new verb on the model↔window wire
* a change to an existing contract in `spec/`
* a new datatype, or a new meaning for an old one
* **a refusal** — a decision that something will *not* be built, which
  is the most durable kind of decision this project makes and the one
  least likely to be revisited

That is perhaps five per cent of the lines and ninety per cent of the
risk.  Reviewing by volume spends your attention uniformly over a
distribution that is anything but uniform.

---

## Four practices

**1. Make the seams report themselves.**  A tool over a commit range
that lists only what touched something load-bearing — the vocabulary,
the wire, a `spec/` contract, a public signature, a card's status.
Thirty commits becomes *"these four deserve your eyes"*.  This is the
direct answer to a limited reading span, and it is small enough to
build.

**2. Read the refusals first.**  Every commit body carries what was
deliberately *not* included.  That paragraph is where a scope decision
was made that you might disagree with, and it is three lines instead of
four hundred.  If you read one thing per commit, read that one.

**3. Spec first, for anything with a shape.**  `spec/north_star.md` was
written before a line of the drag existed and was revised twice against
the building; `spec/scorebox.md` says outright that it was *"specified
before it is built… so what is left is decisions, and a decision written
down can be argued with before it hard-codes anything"*.  Make that the
default rather than the exception.  You read the argument, in the medium
you prefer, **before** the expensive thing exists — and the code becomes
an implementation detail you are entitled to skip.
`board/README.md` §"Elaborate before taking" is the same move at task
scale.

**4. Sample deeply instead of sweeping shallowly.**  Read *one* commit a
week completely, against its own claim, chosen at random or by the seam
report.  This works because an assistant's failure mode is
**systematic, not random**: if a habit is wrong, it is wrong everywhere,
so one careful read finds the pattern and thirty skims find nothing.
`doc/reading-the-log.md` §"Reviewing *my* commits specifically" is how.

---

## The lever the author holds and rarely uses

**The volume is a choice, and by default it is the assistant's.**  Thirty
commits a day is what comes out of working as fast as the work allows.
An instruction to make fewer, larger, better-argued steps would be taken,
and the project would probably be better for it.  Throughput is being
optimised because nobody asked for reviewability instead.

A second, cheaper lever: **ask what has no oracle.**  Every defect this
project has had came from where an oracle was hard to build — the C host
that opened a sound card behind a guard on two other doors, the box that
slid out from under a hand while the whole suite passed.  Making the
session name, in its own summary, what it built that nothing can check
turns your attention straight onto the only region where it is scarce.

---

## What was got right here, and why it is not luck

Worth writing down because it is short, and because the same speed
without it would have buried this project months ago:

1. **The model imports no toolkit.**  Everything is testable with no
   window in the room, which is why there are tests at all.
2. **Every action returns a sentence.**  What the status line shows is
   what a test asserts on — *"an action that reports nothing is one
   nobody can check"*.
3. **One arithmetic for drawing and for hit-testing.**  A control that
   answers where it is drawn cannot drift from itself.
4. **The journal explains *why*.**  A session arriving with no memory
   reconstructs the reasoning by reading, not by asking — which is what
   makes a cold start cost twenty minutes instead of a day.
5. **`manifesto.md`'s rule**, §"costs, and where it is not paid": being
   wrong has to be visible to something that is not a person's
   attention, *because attention is what runs out*.

None of those is an accident; each was written down before it paid off.

**The honest caveat**, because it belongs beside the list: had it gone
south instead, there would have been no way to know these were the
load-bearing ones.  The diagnosis would have read *"too fast"* rather
than *"unverifiable"*, and the wrong lesson — slow down — would have
been learned.  The lesson that is actually true is: **go as fast as
your oracles allow, and no faster.**

---

## The thing that will actually get you

It is not review volume.  It is that a system this efficient converts
just as easily into *more hours* as into fewer.  Nine days at thirty
commits a day, no day off, no hour of the clock without a commit in it
— `spec/summary.md` §"The clock" has the numbers, and its closing line
is the one to keep:

> The pace itself was never instrumented.  Every other cost in this
> project has an oracle.  This one did not.

The timer on the board is that oracle.  It is the one item whose value
depends entirely on the author rather than on the work, which is exactly
why it is the easiest one to keep postponing.

---

## When you disagree with something that was built

Say so plainly and early; it is cheap.  `git revert` exists, the work is
in granular commits so that a single idea can be taken back without
taking back four others, and a card can be reopened by moving it out of
`board/done/`.  **The expensive thing is not the wrong build — it is the
wrong build left standing because nobody said anything**, until three
other things depend on it.

An assistant that only agrees is worth less than one that argues, and
the same is true in the other direction: this project is better when you
push back, and today's two catches are the proof.
