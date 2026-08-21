# Working a board of task files

This is how a task is worked.  The board is a directory of files, one
file per task, and this page is the contract for what is in them and who
touches them.

The author fills the board.  A worker works down it.

There are two other documents this one assumes and does not replace: an
**argument** — why the project is what it is, what it will not do, what
stands unfinished — and a **journal**, which is what happened, always
past tense.  This page is neither.  It is how a *task* is worked.

---

## What this file is, and what it cannot do alone

*Derived 2026-08 from a running project.  Amended by appending dated
lines, never by silent rewrite — because this changes.*

**This page is one part of a kit of four, and it is the least powerful
part.**  It travels with the **argument**, the **journal**, and the
**checks** — executable, described near the end of this page.  Handed
alone, this file can *inform* a worker; it cannot condition one.  Every
rule below leans on evidence that lives in the other three, and a worker
given only this page is being shown a photograph of a factory.

**And it is a seed, not a tree.**  The examples below are the origin
project's paid lessons, carried as provenance, on loan.  A rule becomes
*yours* the day your project pays for its own version of it — then the
origin's example is replaced with your own, dated, citing your own
journal.  Until your ledger has entries, expect this contract to hold
structure and little else: **nothing compresses the paying.**  A lesson
below that carries no date or pointer is scaffolding awaiting your
version, and it says so by that absence.

## The relationship

This page is written **to you, the worker** — not about you.  A board is
worked by two parties, and the contract runs both ways:

- **The author owes you**: real problems in their own words, answers
  when the cord is pulled, and their exact words kept as theirs.
- **You owe the author**: go and look before asking, mark your guesses
  *suspected*, and stop at a seam.
- **The seams are the author's few percent** — the one-way doors: names,
  public contracts, refusals, deletions, and any edit to this file or
  its three companions.  Bring those shaped: the question in one line,
  the options with costs, a default with a trigger, your read marked as
  yours.  Everything else is yours to work.
- **You may disagree, and should when you have a measurement.**  A
  worker that pushes back with a number is doing the job; one that
  flatters the board is not.  Not everybody needs to like you.
- Nothing here is enforced by hope: what must hold is held by the
  checks, and what a check cannot hold is reviewed at the seams.

## Day one, handed this kit cold

1. Read the argument once — what this project is, and what it refuses.
2. Skim the journal's index — the rules' reasons live there, dated.
3. Run the checks — green means the board is currently telling the
   truth.
4. Take the topmost workable card and work it as this page describes.

---

## The priority

**The list of open tasks is priority, not order.**  A card never says
where it stands, which is what keeps a card's name stable while
priorities move.  But the list does not say what to work on next either,
and calling it "the order" claims that it does.

The real order comes from three inputs the list does not hold: what the
author asked for, what is blocked, and what is cheap.

The filter that matters most is **blocked**, and it is usually read too
narrowly.  *Card A blocks card B* is the one case a machine can check,
and it is the rare one.  A card also waits on a person, on a decision
only the author can make, on a schedule it set itself, or on a quiet
machine — and none of those is visible in a priority list.

So the order is **priority filtered by what can actually be worked
today**, and the filter is not written down anywhere because it changes
daily.  Read the list, then read the card: a card that waits on a
person, on a decision, on another card or on a condition says so, and it
drops out of today regardless of where it stands.

That is not a licence to skip down the list on preference.  Priority is
still the tiebreak between two workable cards, and it is still the
author's.

**And the criterion has to be checked, because a criterion nobody checks
gives confident wrong answers.**  Ordering by *impact on somebody using
the product* is a good criterion and it demotes good cards: work that
changes how the product is *made* rather than what a person meets sits
below things a user feels directly.  Measured against one real day, that
same criterion ranked a crash seventh *(origin journal, 2026-08-19)*.
Both facts are true and both belong in the reader's hands.

Finished cards move to a `done/` directory, newest work last, so that
listing the board's own directory **is** the live board and nothing has
to be trimmed by hand for that to stay true.

**And displaced cards go to a `later/` directory** — because a board can
arrive faster than it drains, and same-day cards get done while queued
ones do not.  That is not a work-in-progress problem.  It is a queue
nobody pulls from.

A shelved card is **not a finished one**, which is why it gets its own
directory rather than a word: `done/` says the problem is solved,
`later/` says it is real and is not being worked.  The filename stays
the id, so every citation keeps resolving, and the elaboration is kept
— shelving loses the queue position and nothing else.

```
status   shelved — <date>
```

**A card may also arrive shelved**, without ever standing in the
priority.  That is the honest place for work that is real, wanted, and
waiting on an event rather than on a queue — and it costs the live board
nothing, which is how a card can be written on a day whose goal is
*fewer cards and none new* without the goal being touched.  A card that
arrives shelved says in its `## Shelved` section what it waits on, the
same as a displaced one.

**Sediment or debt, and it is one question.**  A shelved card waiting on
an **event** — a milestone, a person, a measurement, another card —
costs nothing while it waits and wakes on its own when the event
arrives.  A card waiting because **nobody dares decide it** costs
attention every time it is read past, and it gets dearer the longer it
sits.  So when the shelf is read, ask of each card: *is this waiting on
an event, or on me?*  A debt card is not shelved, it is **blocked on a
decision**, and it belongs in the next batch of those.  A deep shelf is
a rich board when it is sediment and a stalled one when it is debt, and
the directory looks identical either way.

**And the reason it was displaced goes in the card, in the author's own
words.**  Without that it is a graveyard nobody re-reads, which is the
failure mode of every "later" folder ever made.  A card comes back the
same way it left: by the author saying so.

---

## Who writes what

**The author creates new cards.  The author does not edit existing
ones.**  The reason is beyond tidiness: **two writers never touch the
same file.**  A new card is a new file, so it shows up in version
control as an addition, collides with nothing, and cannot silently
change work already in flight.

So:

| | writes |
|---|---|
| **the author** | new cards, and nothing else |
| **the worker** | everything in an existing card — the elaboration, the questions, *the author's answers transcribed into them*, `status`, `## Done` — and the priority list; **and a new card, when what it records is the worker's own work** |

**A worker may mint a card, and should.**  What the rule protects
against is two writers on one file, and a new card is a new file — so
none of the argument above changes when the writer is the worker.

Two things it does not license.  A worker does not create a card to
**park work it has been given** — that is a queue nobody pulls from,
which is what the shelf was invented to stop, and the standing rule
holds above it: *a missing capability is built the moment the need
arises*, not filed.  And a worker does not create a card that **proposes
a feature**; that is the author's.

What a worker *should* write is the card for **its own broken
workflow**: the seam it keeps forgetting, the instrument it cannot
trust, the check it did not run.  Nobody else can see those, because
nobody else is in the loop where they happen.  Write them long: a card
like that is a message to the next worker, and the next worker is the
only reader who will ever act on it.

A card the author writes may be one line.  A title and the ask are
enough; the worker normalises the header, and **asks for the `because`
if it is not obvious** rather than guessing one.  Guessing it is how a
card comes to name a fix instead of a problem.

A new card arrives **unplaced**: the worker puts it at the end of the
priority and asks whether it belongs further up.  The author can say so
in a sentence and does not have to edit the list.

The author's answers arrive in conversation and the worker writes them
into the card, dated, in the author's words.  That transcription is not
bookkeeping: **an answer that lives only in a chat is a decision that
will be made again.**

## Question it into existence

**Every card added to the board is questioned before it is written —
every one, without exception.**

The thing being protected is the rule two sections down — a `because` is
a problem and never a fix — and that rule has no defence otherwise.  An
ask arrives naming a solution, because that is how people think and
there is nothing wrong with it.  The problem behind it is recoverable
only by asking, and **a worker that writes the card immediately has
destroyed the evidence**: the fix is now on the board in the author's
own name, and the reader a year later cannot tell it from a need.

The run that produced this rule is the argument for it: an ask naming
two fixes came out as three cards, one of them about **security**, whose
`because` neither party had said out loud when the conversation started.
No amount of careful writing gets from the first to the second.  Only
asking does.

### What the questioning has to do

Not a fixed script.  These are the moves that earned their place, and a
worker should be able to say which it used:

1. **Go and look first.**  Read the surrounding material and the cards
   that already neighbour the ask *before* asking anything.  Half of a
   first round of questions is usually answered by what is already
   written, and asking those spends the author's attention on what the
   worker could have read.  An author who writes short is giving an
   instruction to go and look, not an invitation to interrogate.
2. **Measure the claim against what is actually here.**  The step that
   matters most and the one most likely to be skipped.  A stated need is
   a claim about *this* project, so check it — and the number you find,
   not the sentence that prompted it, is what makes a card workable.  A
   need that cannot be measured at all is not disqualified, but say so
   out loud.
3. **Offer readings, each with what would kill it.**  Two to four ways
   of taking the ask, and for each, the thing that would make it wrong.
   The author picks one, or names the one nobody wrote.  This is much
   cheaper for them than defending a single proposal.
4. **Check it does not already exist.**  Two cards that look like
   duplicates are often one superset and one subset; that has to be read
   to be known, and the overlap goes in both cards.
5. **Ask what a worker does on day one.**  If the answer needs a
   decision only the author can make, it is a decision wearing a card
   and should be marked so, not queued.  If it cannot be answered at
   all, the card is not ready.
6. **Take the `because` in their words, and mark what is yours.**
   Transcribed from the conversation, dated.  A measurement the worker
   made is labelled as the worker's, and labelled *suspected* where it
   is a proxy.
7. **Then say where it lands**: the live board, or shelved on arrival.

### Two things this is not

It is **not a gate on the author.**  They may write a one-line card and
walk away; the questioning is the worker's work and it happens when the
card is elaborated, not while they wait.  What is forbidden is the
worker writing a polished card *out of an unquestioned ask* — that
launders a guess into the record.

And it is **not a licence to stall.**  Questions are collected and asked
in one sitting, and a card whose questioning cannot finish today is
written with its questions open and dated rather than held back.

### What a check can hold, and what it cannot

Being exact about this beats adding a check that feels like one.  **No
check can tell whether a question was asked**, and the nearest proxy — a
`because` carrying a quotation — fails on more than half of a real
board, which would be an alarm lighting for one cause fifteen times.
What could be held is the rule applied **only to cards created after the
day it lands**, with an accepted baseline that may shrink and never
grow.

## What a card is

One file, named for the task.  **The filename is the id**: it never
renumbers, so a comment in the source or a test may cite it and the
citation still resolves a year later.  Positional numbering is what this
replaces — a numbered board goes stale the moment an item leaves the
middle of the list.

Every card opens with the same block:

```
    status   open | doing | blocked | done — <date>
    because  the problem, in the asker's own words
    asked    who, when
    blocked  what it waits on            (only when blocked)
    see      the material this touches
```

**`because` is mandatory and is a problem, never a fix.**  This is the
board's most expensive lesson.  A card that read *"name datatypes eg.
`type Duration = Float`"* named a solution; the actual need was *"I do
not figure out quickly enough which argument in lowpass filters are
which"*, and the answer turned out to have nothing to do with types —
the argument **names** were what carried the information, and they were
missing from every place a signature was shown.  A card that names the
fix hides the problem, and the problem is the part a reader can solve
differently.

### How a card is cited

A short id notation, not a path — because **a card's name never changes
and its shelf does**.  It starts on the board and ends in `done/` or
`later/`, so a citation spelled as a path breaks every time a card is
finished, and every one of those moves is a project-wide rewrite.  *Cite
the card, not the shelf it is on.*

Two things the notation buys beyond the churn:

* **It cannot be helpfully corrected.**  A path that points at the wrong
  shelf looks like a typo, and a reader who finds one fixes it — which
  is the same churn arriving from the other direction.  An id is visibly
  an id, so there is nothing to correct.
* **Bare citations get checked.**  A checker that only sees citations
  inside backticks misses every `see` line at the head of every card,
  because those are written bare.  Two had already rotted in that blind
  spot before anybody looked.

Then the body, in whatever depth the task needs:

```
## The ask            — verbatim, so the asker's words survive editing
## Found by looking   — the elaboration (see below)
## Questions          — each with its answer inline, dated
## Done               — what landed, and where the story is
```

### One sheet, then depth

**The main matter should fit one sheet, and more is fine below it.**  If
it can be said in few words, use those few rather than say it in three
hundred.

So it is a **front**, not a limit: the header, the ask, the questions
and what is left to do fit one sheet, and whatever needs saying at
length follows below it.  A reader who stops after the first sheet still
has what they need to act.

**And a fifth thing belongs on the front: what the card is *about*.**  A
card can be accurate in every section and still leave its reader unable
to get in, because a word in it wears two meanings and the card assumed
which.  A card is written by somebody at the end of the looking, and the
words that were expensive to learn read as obvious by then — so **the
front opens with the nouns**, *what this is, what it is not, and when
the thing runs*, before it opens with what went wrong.  It is the only
part a stranger cannot supply for themselves.

The line that decides what goes below: **the paragraphs belong to the
journal, not to the card.**  A card says what to do; the journal says
what happened.  A card reached nine hundred lines by ignoring that.

**And the rule cuts both ways.**  Briefness is a failure mode too: a
first screen so spare that it named a control which no longer existed
cost a stranger their way in.  Few words where few will do; not fewer
than the reader needs.

## Elaborate before taking

**The practice that pays for itself most.**  Before a card is worked,
spend the time to look and write down what you found: which parts
already exist and where, what the work actually is, and — this is the
valuable half — the question that has to be answered before it can be
finished.  A task whose shape is unknown cannot be estimated or ordered.

Doing this for several cards at once means the work arrives with its
parts already located and its one real question already asked and
answered.

**Collect the questions and ask them in one sitting**, not one
interruption per card.  The answer is written *into the card it belongs
to*, dated, with the author's words kept as theirs.

## Taking one

- Read the card, then the argument around it — a card is a task, not a
  rationale.
- Say at the start what you take it to mean, and negotiate.  Ask freely.
- **Before building, state the postcondition in one sentence, derived
  from the card's `because` and naming no function.**  See below.
- Set `status doing` if it will take a while and someone else might
  look.
- If it turns out to be blocked, say so in `status` **and** in
  `blocked`, and move on to the next card rather than stalling.
- Work it as far as it goes.  Finish the whole task; if part of it is
  blocked, finish the rest and say plainly what was left and why.

## The postcondition, before anything is built

**One sentence, derived from the `because`, naming no function.**  Then
the author corrects it in a line, or does not, and the work has a
definition of done that was not written by the code.

A `because` is a falsifiable claim about a person, written before the
code exists — so the material is already on every card.

Two rules that make it useful rather than ceremony:

* **If it cannot be written without naming a function, the change is
  probably not user-facing** and owes no such test.  That is the signal,
  not a failure.
* **Write it before the implementation**, because one written after is a
  description of what was built.

## Working while the author is away

A board is worked with the author available rather than present.  That
only works if a worker can reach them, so there is a cord — and the rule
for it is: **pull it for a decision that would be expensive to get wrong
and cheap to ask about**, and for the sitting rather than for each
question.

The default when they are away is still to keep going.  A blocked card
is written up as blocked and the next one is taken; that is cheaper than
an interruption, and it is what the `blocked` field is for.

## Finishing one

1. The `## Done` section says what landed, in a few lines, with a
   pointer to the journal entry that tells the story.  **The paragraphs
   belong to the journal, not to the card.**
2. `status` becomes `done — <date>`.
3. Move the card to `done/` and take it out of the priority.
4. **Run the checks.**  They are the ones a card's own edits break, and
   steps 1–3 have just edited several of them.  Running them first only
   means finding out before you have written the commit message.
5. Write the commit title yourself.  A commit is the *end* of a card and
   not a punctuation mark inside one: one card, one commit, with the
   card's move riding in it.

**Steps 1–3 ride in the same commit as the work.**  The card leaves the
board and the work arrives in one step, so there is never a commit where
the board disagrees with the project.

If the work changes the argument — a rule earned, a design closed, a
thing refused with a number — that belongs in the argument document, in
one line pointing at the journal.  A closure written at length in the
future-tense file is what makes a roadmap unskimmable.

## What the checks hold

**The rules are executable.**  Not all of them, and being exact about
which is the point:

- **No two cards wear the same name**, across `done/` too, because a
  finished card keeps its name forever and the citation that breaks is
  the *old* one, in a comment nobody is looking at.
- Every card has `status`, `because` and `asked`, and `status` says one
  of the four words.  Presence, not wisdom: no check can tell a problem
  from a solution, but it can refuse a card that answers neither.
- A `done` card is in `done/` and an open one is not, so listing the
  board's directory stays true.
- A blocked card names what it waits on, and that thing exists.  The
  case this is for really happened: a card sat marked *"the one item I
  cannot start without an answer"* for the rest of a day, sixty lines
  above the answer.
- Every open card appears in the priority — which is where a card the
  author creates lands, since it arrives unplaced.
- Every cited file exists, and every cited section's words are still in
  the file they name.

**Why the checks and not the editor.**  A rule that lives in an editor
holds only for people using that editor — not for a collaborator with a
different one, and not for a worker that writes files with tools and
never opens the editor at all.

**And why the checks must travel with this file.**  The list above
*describes* the checks; a described check holds nothing.  The kit ships
them executable, and a project adopting this contract writes or copies
them before the first card lands.  A board whose rules are held by hope
is, by this page's own account, form without a factory — and the first
thing a worker should distrust.

## What working a whole day of this teaches

**An elaboration's mechanism guess is a guess, and should say so.**  It
is the part most likely to be wrong and the part a reader trusts most,
so mark it: *suspected*, not *is*.  **The durable half of an elaboration
is the located parts and the question.**

**A card should record what it turned up that was not its job.**  A
defect number with no link back to the work that found it loses the only
context that explains why anybody was looking there.

**A test suite is a serial gate, and a worker can invalidate its own
run** — a project edited underneath a long pass returns a red that
describes a moment rather than a defect, which is the two-writers rule
again with the test run as the second writer.  So:

> **Targeted runs per card while working; one full run per shift; and
> the project is frozen while it runs.**

If something must be changed mid-run, kill the run.  Finishing a run
against a state that no longer exists proves nothing and costs the same
time.

**And the machine is shared.**  A worker running a suite, a compiler and
a dozen polling loops makes the audio crackle for the person sitting at
the keyboard — it happened *(origin journal, 2026-08-18)*, and it was
diagnosed as hardware before it was diagnosed as the worker.  Say what
you are about to start, and stop it when it is not needed.

## What does not go here

- **Defects** go to a defect list with a number.  A card may cite one; a
  card is work to do, a defect is something that is wrong.
- **The argument** — why a thing is worth doing, what was measured and
  rejected, what will deliberately not be built — stays in the argument
  document.
- **What happened** goes to the journal, always past tense.
- **The standing backlog** stays as prose in the argument document.  **A
  backlog item becomes a card the moment it is taken up**, which is when
  its elaboration is written.  Minting thirty cards for work nobody will
  touch for months is ceremony, not clarity.

## The rules, as the author wrote them

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

*"Unless one blocks the other" is doing more work than it looks like* —
see the priority section.  Most of what blocks a card is not another
card.

And the one that made the board a directory: *"You take each out from
this section once the commit has landed.  In that way this is a kanban
system."*
