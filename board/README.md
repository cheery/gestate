# board/ — the live board, and how to work it

**This is the first thing to read when picking the project up.**
`roadmap.md` is the argument — why the project is what it is, what it
will not do, and what stands unfinished in each part of it.  This
directory is what is actually being worked, in order, one file per task.

Henri fills the board.  A session works down it.

`spec/author.md` is the companion to this one: this file is how a *task*
is worked, that one is what the author spends attention on when there is
more work than there is reading time.

And `vision.md` is what any of it is **for** — the author's own document,
short on purpose, dated because it changes.  A card's `because` should be
traceable to something in it; when it is not, either the vision is
incomplete or the card is drift, and both are worth saying out loud.

---

## The order

Work them in this order unless one blocks another.  **This list is the
only place the order lives** — a card never says where it stands, which
is what keeps a card's name stable while priorities move.

1. **[timer](timer.md)** — see in gestate when the day has been too
   long.  *Moved to the front 2026-08-16, at Henri's ask, after reading
   `spec/summary.md` through: nine days, no rest day, no hour of the
   clock without a commit in it — and a daily count that was still
   **accelerating** when it was measured.*
2. **[older-features](older-features.md)** — `using`/`given` and the
   Datafun surface have never been used through the window; find out
   where they work.
3. **[open-path-bug](open-path-bug.md)** — `open ../../hello.ges` from
   `minute.ges` lands in the wrong directory.
4. **[gemba](gemba.md)** — walk the factory floor: Claude presents into
   the workbench while the work is happening.
5. **[command-categories](command-categories.md)** — the command list
   is long enough to want categories, and gemba's second idea waits on
   it.
6. **[git-viewer](git-viewer.md)** — a git viewer in the workbench,
   encoding the workflow the lesson teaches.  *Blocked on
   command-categories.*
7. **[git-lesson](git-lesson.md)** — teach git, well enough to follow
   the changes Claude makes.

Finished cards are in [done/](done/), newest work last.  `ls board/*.md`
is the live board; nothing has to be trimmed by hand for that to stay
true.

---

## Who writes what

**Henri creates new cards.  He does not edit existing ones.**  His own
rule, 2026-08-16, and it is a good one for a reason beyond tidiness:
**two writers never touch the same file.**  Today the board grew two
items *while a session was working down it* — the session had read the
list an hour earlier and nearly missed them.  A new card is a new file,
so it shows up in `git status` as an addition, collides with nothing,
and cannot silently change work already in flight.

So:

| | writes |
|---|---|
| **Henri** | new cards, and nothing else |
| **the session** | everything in an existing card — the elaboration, the questions, *his answers transcribed into them*, `status`, `## Done` — and this file's order |

A card Henri writes may be one line.  A title and the ask are enough;
the session normalises the header, and **asks for the `because` if it
is not obvious** rather than guessing one.  Guessing it is how a card
comes to name a fix instead of a problem.

A new card arrives **unplaced**: the session puts it at the end of the
order and asks whether it belongs further up.  He can say so in a
sentence — he does not have to edit this file to move it.

His answers arrive in conversation and the session writes them into the
card, dated, in his words.  That transcription is not bookkeeping: an
answer that lives only in a chat is a decision that will be made again.

## What a card is

One file, named for the task.  **The filename is the id**: it never
renumbers, so a comment in the source or a test may cite
`board/done/peep-window.md` the way they cite `fixme.md`'s F-numbers, and the
citation still resolves a year later.  Positional numbering is what this
replaced — the old board had two numbering schemes and both went stale
the moment an item left the middle of the list.

Every card opens with the same block:

```
    status   open | doing | blocked | done — <date>
    because  the problem, in the asker's own words
    asked    who, when
    blocked  what it waits on            (only when blocked)
    see      specs, journal entries, defect numbers
```

**`because` is mandatory and is a problem, never a fix.**  This is the
board's most expensive lesson so far.  The card that read *"name
datatypes eg. `type Duration = Float`"* named a solution; the actual
need was *"I do not figure out quickly enough which argument in lowpass
filters are which"*, and the answer turned out to have nothing to do
with types — the argument **names** were what carried the information,
and they were missing from every place a signature was shown.  A card
that names the fix hides the problem, and the problem is the part a
reader can solve differently.

Then the body, in whatever depth the task needs:

```
## The ask            — verbatim, so the asker's words survive editing
## Found by looking   — the elaboration (see below)
## Questions          — each with its answer inline, dated
## Done               — what landed, and the journal entry
```

## Elaborate before taking

**The practice that has paid for itself most.**  Before a card is
worked, spend the time to look and write down what you found: which
parts already exist and where, what the work actually is, and — this is
the valuable half — the question that has to be answered before it can
be finished.  A task whose shape is unknown cannot be estimated or
ordered.

Doing this for seven cards at once meant the peep window arrived with
its parts already located (`palette.rs:1175` had the placement rule
built), and with its one real question already asked and answered.

**Collect the questions and ask them in one sitting**, not one
interruption per card.  The answer is written *into the card it belongs
to*, dated, with Henri's words kept as his.  An answer that lives only
in a chat is a decision that will be made again.

## Taking one

- Read the card, then `roadmap.md` for the argument around it — a card
  is a task, not a rationale.
- Say at the start what you take it to mean, and negotiate.  Ask freely.
- Set `status doing` if it will take a while and someone else might look.
- If it turns out to be blocked, say so in `status` **and** in
  `blocked`, and move on to the next card rather than stalling.
- Work it as far as it goes.  Finish the whole task; if part of it is
  blocked, finish the rest and say plainly what was left and why.

## Finishing one

1. The `## Done` section says what landed, in a few lines, with a
   pointer to the `journal.md` entry that tells the story.  **The
   paragraphs belong to the journal, not to the card.**
2. `status` becomes `done — <date>`.
3. Move the card to `board/done/` and take it out of the order above.
4. The commit title is Henri's to give.  Ask for it; never commit
   unprompted.

**Steps 1–3 ride in the same commit as the work**, which is Henri's own
rule read forward: *"You take each out from this section once the commit
has landed."*  The card leaves the board and the work arrives in one
step, so there is never a commit where the board disagrees with the
tree.

If the work changes the argument — a rule earned, a design closed, a
thing refused with a number — that belongs in `roadmap.md` or a `spec/`
file, in one line pointing at the journal.  A closure written at length
in the future-tense file is what made the old roadmap unskimmable.

## What the suite enforces

**The rules are executable.**  `test/test_board.py` holds the board to
its own contract, and `test/test_citations.py` holds the tree to its
references.  Between them:

- **No two cards wear the same name** — Henri's ask, and the id property
  depends on it.  Across `done/` too, because a finished card keeps its
  name forever and the citation that breaks is the *old* one, in a
  comment nobody is looking at.
- Every card has `status`, `because` and `asked`, and `status` says one
  of the four words.  Presence, not wisdom: no test can tell a problem
  from a solution, but it can refuse a card that answers neither.
- A `done` card is in `done/` and an open one is not, so `ls board/*.md`
  stays true.
- A blocked card names what it waits on, and that card exists.  (The
  case this is for really happened: a card sat marked *"the one item I
  cannot start without an answer"* for the rest of a day, sixty lines
  above the answer.)
- Every open card is in the order above — which is where a card Henri
  creates lands, since it arrives unplaced.
- Every `board/…md` cited anywhere in the tree exists, and every `§"…"`
  citation's words are still in the file they name.

**Why the suite and not the editor.**  A rule that lives in the window
holds only for people using the window — not for a collaborator with a
different editor, and not for a session that writes files with tools.
It is also the mistake this project has twice designed against: the
window never tokenizes and never invents furniture, because a second
source of truth is one that can disagree.  What the workbench would add
is *timing* — saying it beside the card as you type, the way a knob is
drawn beside its own declaration — and that becomes worth building when
editing cards in the workbench is a thing somebody does.  Today `.md`
opens inert.

## What does not go here

- **Defects** go to `fixme.md` with an F-number.  A card may cite one; a
  card is work to do, an F-number is something that is wrong.
- **The argument** — why a thing is worth doing, what was measured and
  rejected, what will deliberately not be built — stays in `roadmap.md`.
- **What happened** goes to `journal.md`, always past tense.
- **The standing backlog** stays as prose in `roadmap.md` §"What is left
  after stage 10" and its neighbours.  **A backlog item becomes a card
  the moment it is taken up**, which is when its elaboration is written.
  Minting thirty cards for work nobody will touch for months is
  ceremony, not clarity.

## The rules, as Henri wrote them

> Work them in the order given, unless one blocks the other.
> Negotiate at the start and ask questions freely.
> Collect up the questions that appear, wherever they belong, and pass
> me the info.
> Try to continue the work as far as you can.
>
> These rules may change.  I'm trying things out here at first.  You are
> welcome to give me feedback.
>
> It's okay, do these at your own pace.

And the one that became this directory: *"You take each out from this
section once the commit has landed.  In that way this is a kanban
system."*
