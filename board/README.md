# board/ — the live board, and how to work it

**This is the first thing to read when picking the project up.**
`roadmap.md` is the argument — why the project is what it is, what it
will not do, and what stands unfinished in each part of it.  This
directory is what is actually being worked, in order, one file per task.

Henri fills the board.  A session works down it.

`spec/author.md` is the companion to this one: this file is how a *task*
is worked, that one is what the author spends attention on when there is
more work than there is reading time.

And **`doc/instruments.md` is what a session already has to work with** —
gemba, the andon, driving and photographing the real window, the
generated pages that are suite gates.  Worth reading before deciding
something has to be done the hard way, because a session that does not
know an instrument exists does the work it was built to make
unnecessary.  Its first rule is the one Henri gave on 2026-08-18: **a
missing capability is built the moment the need arises**, not filed.

And `vision.md` is what any of it is **for** — the author's own document,
short on purpose, dated because it changes.  A card's `because` should be
traceable to something in it; when it is not, either the vision is
incomplete or the card is drift, and both are worth saying out loud.

---

## The order

Work them in this order unless one blocks another.  **This list is the
only place the order lives** — a card never says where it stands, which
is what keeps a card's name stable while priorities move.

1. **[gemba-follow](gemba-follow.md)** — four things the first real use
   of the walk asked for, in his words.  *Waits on `fixme.md` F147 by
   his own instruction.*
2. **[stranger-test](stranger-test.md)** — fixes nothing; it is what
   *found* the four that are now done, and what would settle
   `command-categories`' pick against a person rather than an argument.
   Ranked here only because each run spends a scarce, non-renewable
   person.
3. **[interface-oracle](interface-oracle.md)** — stops the finished
   four regressing silently.  A multiplier rather than a feature, and
   the argument got sharper on 2026-08-18: `view.rs`'s own tests went
   red on the commit that changed the corner and stayed red across a
   whole session, because nothing runs them.
4. **[unseen-flare](unseen-flare.md)** — narrower than
   `unheard-output`, and overlapping it.
5. **[reviewing-by-running](reviewing-by-running.md)** — the review
   loop `spec/author.md` says is the scarce resource.
6. **[git-lesson](git-lesson.md)** — teach git, well enough to follow
   the changes a session makes.
7. **[git-viewer](git-viewer.md)** — a git viewer in the workbench.
   *Unblocked 2026-08-18: `command-categories` landed, so a family of
   new commands now arrives into a list that groups them.*
8. **[portable-package](portable-package.md)** — for people who do not
   exist yet, by his own answer.  *Waiting on program-or-workshop.*

**Ordered by impact on somebody using gestate** — 2026-08-17, at
Henri's ask: *"order them by some quality, such as, what is the impact
of it for me or others who would use it… It's the proper order to do
these tasks."*  The criterion is deliberate and demotes good cards:
`gemba`, `reviewing-by-running` and the git pair change how the work is
*made* rather than what a person meets, and they sit below things that
a user feels directly.

Two of these are **decisions wearing a card** and are marked so.  No
session can finish one, so their position is academic until they are
answered or shelved (`spec/author.md` §"Triaging the board").
`command-categories` was the third, and on 2026-08-18 it was answered,
built and finished in one sitting — which is what a decision card is
worth when somebody answers it rather than shelves it.

Finished cards are in [done/](done/), newest work last.  `ls board/*.md`
is the live board; nothing has to be trimmed by hand for that to stay
true.

**And displaced cards are in [later/](later/)** — *adopted 2026-08-17*,
because the board was arriving faster than it drained: nineteen cards
in two days, six finished, and **of the nine queued on the first day,
none**.  Same-day cards got done and queued ones did not, which is not
a work-in-progress problem — it is a queue nobody pulls from.

A shelved card is **not a finished one**, which is why it gets its own
directory rather than a word: `done/` says the problem is solved,
`later/` says it is real and is not being worked.  The filename stays
the id, so every citation keeps resolving, and the elaboration is kept
— shelving loses the queue position and nothing else.

```
status   shelved — <date>
```

**And the reason it was displaced goes in the card, in Henri's words.**
Without that it is a graveyard nobody re-reads, which is the failure
mode of every "later" folder ever made.  A card comes back the same
way it left: by him saying so.

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
- **Before building, state the postcondition in one sentence, derived
  from the card's `because` and naming no function.**  See below.
- Set `status doing` if it will take a while and someone else might look.
- If it turns out to be blocked, say so in `status` **and** in
  `blocked`, and move on to the next card rather than stalling.
- Work it as far as it goes.  Finish the whole task; if part of it is
  blocked, finish the rest and say plainly what was left and why.

## The postcondition, before anything is built

**One sentence, derived from the `because`, naming no function.**  Then
Henri corrects it in a line, or does not, and the work has a definition
of done that was not written by the code.

*Adopted 2026-08-17.*  The occasion: an automatic audition shipped with
**thirteen passing tests** and was switched off for the only person it
existed for — a stranger, who never applies anything, so a gate keyed on
"the last audition of this file" never opened.  Every test agreed with
the implementation because every test was written from it, which is
`manifesto.md`'s third way an instrument fails, arriving on schedule.

**The raw material is already on every card and nothing used it.**  A
`because` is a falsifiable claim about a person, written before the code
exists — which is exactly the property the manifesto asks assertions to
have, *"stated in a vocabulary the implementation does not own"*.
`button.md`'s reads *"The program would not currently pass the stranger
test."*  That is a test, and nothing tests it.

So the sentence is the session's to write and Henri's to correct — one
line of his attention, spent where his knowledge actually is, which is
what *done* means for a person.  He was explicit that the burden must
not move to him: *"Do you mean that I should start writing
postconditions?"* — no.

Two rules that make it useful rather than ceremony:

* **If it cannot be written without naming a function, the change is
  probably not user-facing** and owes no such test.  That is the
  signal, not a failure.
* **Write it before the implementation**, because one written after is
  a description of what was built.  The auto-audition's sentence —
  *"somebody who has never pressed anything still hears their edit"* —
  fails against the first version and passes against the second, and it
  only has that power because the first version had not been written
  when the sentence was.

## Working while he rests

From 2026-08-17 the board is worked with Henri away from the desk —
*"with the new system I don't need to be around all the time"* — and
available rather than present: *"I am here for you in need.  Available
but just relax as much as I can."*

That only works if a session can reach him, so there is a cord:

    tools/andon.sh          ring once
    tools/andon.sh 3        ring three times, eight seconds apart

It plays `tools/andon.ges` through the sound card — three rising sine
chimes, about two seconds, and the file's own prose says why it sounds
the way it does.  Verified working on 2026-08-17, the morning it was
built.  **Ringing is capped at three by the script itself**, and that is
a design decision, not a limitation: if three calls did not reach him he
is not in the room, and a session that rings thirty times has only
arranged for a noise to be waiting when he walks back in.

**Pull it for a decision that would be expensive to get wrong and cheap
to ask about** — the ones that change what gets built, not the ones a
careful session should just make.  The board's own rule already says
which those are: a card's questions are collected and asked *in one
sitting*, so the cord is for the sitting, not for each question.

And the default when he is away is still to keep going.  *"Try to
continue the work as far as you can."*  A blocked card is written up as
blocked and the next one is taken; that is cheaper than a ring, and it
is what the `blocked` field is for.

## Finishing one

1. The `## Done` section says what landed, in a few lines, with a
   pointer to the `journal.md` entry that tells the story.  **The
   paragraphs belong to the journal, not to the card.**
2. `status` becomes `done — <date>`.
3. Move the card to `board/done/` and take it out of the order above.
4. Write the commit title yourself.  **Henri's, 2026-08-17:** *"From now
   on I allow you to select titles yourself."*  Until that morning the
   title was his to give and a session asked for it — which worked while
   he was at the desk and became the thing a card waited on once he was
   not.  He still gives one whenever he wants to; the change is only that
   the absence of one is no longer a stop.

   What has not changed is that a commit is the *end* of a card and not a
   punctuation mark inside one: one card, one commit, with the card's
   move riding in it.

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

## What the first full day of this taught

*2026-08-17, after two cards were worked start to finish by a session
with Henri away from the desk.  Each of these cost something real; they
are here so the next one costs less.*

**An elaboration's mechanism guess is a guess, and should say so.**
`open-path-bug`'s elaboration named `Session._where` and cited its two
prior defects — plausible, well argued, and wrong; the bug was in
`_listing` and `_where` was innocent.  A session nearly went and
instrumented the wrong function on the strength of it.  **The durable
half of an elaboration is the located parts and the question.**  The
mechanism is the part most likely to be wrong and the part a reader
trusts most, so mark it: *suspected*, not *is*.

**Finishing a card breaks every citation to it.**  The timer card moved
from `board/` into `board/done/`, and two files that cited it went stale
the same minute — caught by `test_citations.py`, which is the system
working, but it means every completion is a small tree-wide rewrite and
the cost grows with the tree.  The filename is the id and it is stable;
the *path* is not, so the id is not.  Worth fixing in the checker rather
than in the prose: **cite the card, not the shelf it is on.**

*And the paragraph you are reading proved it.*  Written with the old
path spelled out as an example, it failed the check on the first run —
a sentence explaining that citations rot, rotting a citation.  That is
how cheap this mistake is to make.

**A card should record what it turned up that was not its job.**  The
`older-features` audit produced three `fixme.md` entries about things it
was not looking for.  They went into its `## Done` and that was an
improvisation — but the right one: an F-number with no link back to the
work that found it loses the only context that explains why anybody was
looking there.

**The suite is a serial gate, and a session can invalidate its own
run.**  A full `tools/suite.py` is about 25 minutes.  Twice in one day a
session edited the tree *while the run was reading it* and got a red
that described a moment rather than a defect — which is this file's own
rule about two writers, with the test run as the second writer.  So:

> **Targeted runs per card while working; one full run per shift; and
> the tree is frozen while it runs.**

If something must be changed mid-run, kill the run.  Finishing a run
against a tree that no longer exists proves nothing and costs the same
25 minutes.

**And the machine is shared.**  A session running the suite, `cargo`,
two X servers and a dozen polling loops makes the audio crackle for the
person sitting at the keyboard — which is not a metaphor; it happened,
and it was diagnosed as hardware before it was diagnosed as the session.
Nothing in this project accounts for what a session costs the machine
somebody is listening on.  Say what you are about to start, and stop it
when it is not needed.

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
