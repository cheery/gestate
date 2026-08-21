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

And **`doc/memory/` is what earlier sessions carried across** — one fact
per file, indexed, and in the tree since 2026-08-20 so that Henri can
read and write it too.  A session's private index holds the hooks and
points there.

And `vision.md` is what any of it is **for** — the author's own document,
short on purpose, dated because it changes.  A card's `because` should be
traceable to something in it; when it is not, either the vision is
incomplete or the card is drift, and both are worth saying out loud.

---

## The priority

**This list is priority, not order.**  A card never says where it
stands, which is what keeps a card's name stable while priorities move —
but this list does not say what to work on next either, and calling it
"the order" claimed that it did.

*Corrected 2026-08-19, at Henri's ask, after the claim was measured
against a single day and was false three times over.*  The real order
comes from three inputs this list does not hold — what he asked for,
what was blocked, and what was cheap.

**And the filter was in his rules from the first day**: §"The rules, as
Henri wrote them" opens *"Work them in the order given, unless one
blocks the other"*.  What narrowed was **blocks**, read as *card A
blocks card B* — the one case the suite can check, and one of six that
day.  A card also waits on a person, on a decision only he can make, on
a schedule it set itself, or on a quiet machine, and none of those is
visible here.

So the order is **priority filtered by what can actually be worked
today**, and the filter is not written down anywhere because it changes
daily.  Read the list, then read the card: a card that waits on a
person, on a decision, on another card or on a condition says so, and it
drops out of today regardless of where it stands here.

That is not a licence to skip down the list on preference.  Priority is
still the tiebreak between two workable cards, and it is still his.

1. **[working-standard](working-standard.md)** — `doing`.  The five
   method documents are against their 2,000-line cap (`spec/rules.md`)
   and `tools/rulecount.py` says where they stand; the counter has been
   a gate since 2026-08-20, and the trim is what is left.
2. **[ungated-fixes](ungated-fixes.md)** — 62 of `fixme.md`'s repairs
   are named by no test, so a defect closed on a photograph can come
   back without anybody being told.  Directly under the oracle
   because they are the same family and the oracle is what makes the
   interface-shaped ones closable at all.
3. **[unseen-flare](unseen-flare.md)** — narrower than
   `unheard-output`, and overlapping it.
4. **[reviewing-by-running](reviewing-by-running.md)** — the review
   loop `spec/author.md` says is the scarce resource.
5. **[git-lesson](git-lesson.md)** — teach git, well enough to follow
   the changes a session makes.
6. **[git-viewer](git-viewer.md)** — a git viewer in the workbench.
   *A proof of concept landed 2026-08-18 — three of its four views walk
   in the real window.  What is left is the fourth, paging, and a
   stranger.*
7. **[stranger-test](stranger-test.md)** — **moved here from first on
    2026-08-18**, the day it produced its largest result: *"I think that
    we need another stranger.  move the card to the last."*  It is not
    demoted for being less valuable — run two carried the vision's whole
    opening claim to a person, found F162 and F163, and cost half its
    thirty minutes to the way in.  It is last because **it waits on a
    person nobody has**, and the one question it still owes — whether
    the corner is findable by somebody who has never seen it — cannot be
    answered by any session, at any position in this list.  A card that
    cannot be worked does not belong above cards that can.

8. **[memory-atrophy](memory-atrophy.md)** — the author's own
   observation, 2026-08-21: the tree reduces his memory pressure, and
   what is not exercised weakens.  **Last because the criterion above
   cannot rank it** — its reader is the author, not somebody using
   gestate.  Four moves taken one at a time over months, three of them
   a two-line edit each, so it does not compete for a day's work.

**And the criterion has been checked once, on 2026-08-19, and it lost**
— `journal.md` §"And what the day says about the board".  Ordering by
impact ranked a crash seventh, which is the kind of answer a rule gives
when nobody checks it.

**Ordered by impact on somebody using gestate** — 2026-08-17, at
Henri's ask: *"order them by some quality, such as, what is the impact
of it for me or others who would use it… It's the proper order to do
these tasks."*  The criterion is deliberate and demotes good cards:
`gemba`, `reviewing-by-running` and the git pair change how the work is
*made* rather than what a person meets, and they sit below things that
a user feels directly.

**None of these is a decision wearing a card**, which is new.  No session
can finish one, so its position is academic until it is answered or
shelved (`spec/author.md` §"Triaging the board").  `command-categories`
was answered, built and finished in one sitting on 2026-08-18;
`portable-package` was shelved by its answer on 2026-08-20 — which is
what a decision card is worth when somebody answers it rather than files it.

Finished cards are in [done/](done/), newest work last.  `ls board/*.md`
is the live board; nothing has to be trimmed by hand for that to stay
true.

**And displaced cards are in [later/](later/)** — *adopted 2026-08-17*,
because the board was arriving faster than it drained and same-day cards
got done while queued ones did not, which is not a work-in-progress
problem but a queue nobody pulls from.  `card:working-standard.md` has
the count.

A shelved card is **not a finished one**, which is why it gets its own
directory rather than a word: `done/` says the problem is solved,
`later/` says it is real and is not being worked.  The filename stays
the id, so every citation keeps resolving, and the elaboration is kept
— shelving loses the queue position and nothing else.

```
status   shelved — <date>
```

**A card may also arrive shelved**, without ever standing in the priority
— *2026-08-18*, when `card:working-standard.md` and
`card:project-seed.md` were written for a project that has not
started.  Henri: *"I want the cards made for this to go directly into
the board/later/ because they aren't current."*  This is the honest
place for work that is real, wanted, and waiting on an event rather than
on a queue — and it costs the live board nothing, which is how two cards
were written on a day whose goal was **four fewer and none new** without
the goal being touched.  A card that arrives shelved says in its
`## Shelved` section what it waits on, the same as a displaced one.

**Sediment or debt, and it is one question.**  A shelved card waiting on
an **event** — a milestone, a person, a measurement, another card —
costs nothing while it waits and wakes on its own when the event
arrives.  A card waiting because **nobody dares decide it** costs
attention every time it is read past, and it gets dearer the longer it
sits.  So when `later/` is read, ask of each card: *is this waiting on
an event, or on me?*  A debt card is not shelved, it is **blocked on a
decision**, and it belongs in the next batch of those.  A deep `later/`
is a rich board when it is sediment and a stalled one when it is debt,
and the directory looks identical either way.

**And the reason it was displaced goes in the card, in Henri's words.**
Without that it is a graveyard nobody re-reads, which is the failure
mode of every "later" folder ever made.  A card comes back the same
way it left: by him saying so.

---

## Who writes what

**Henri creates new cards.  He does not edit existing ones.**  His own
rule, 2026-08-16, and the reason is beyond tidiness: **two writers never
touch the same file.**  A new card is a new file, so it shows up in `git
status` as an addition, collides with nothing, and cannot silently
change work already in flight.

So:

| | writes |
|---|---|
| **Henri** | new cards, and nothing else |
| **the session** | everything in an existing card — the elaboration, the questions, *his answers transcribed into them*, `status`, `## Done` — and this file's order; **and a new card, when what it records is the session's own work** |

**A session may mint a card, and should.**  *Amended 2026-08-18*, after
two of them, and his answer both times: *"I liked that you created a new
card.  It was necessary."*  What the rule protects against is two
writers on one file, and a new card is a new file — so none of the
argument above changes when the writer is a session.

Two things it does not license.  A session does not create a card to
**park work it has been given** — that is a queue nobody pulls from,
which is what `later/` was invented to stop, and the standing rule from
`doc/instruments.md` still holds above it: *a missing capability is
built the moment the need arises*, not filed.  And a session does not
create a card that **proposes a feature**; that is Henri's, and on
2026-08-18 he said so in as many words — *stop proposing cards*, the
board goal being four fewer and none new.

What a session *should* write is the card for **its own broken
workflow**: the seam it keeps forgetting, the instrument it cannot
trust, the check it did not run.  Nobody else can see those, because
nobody else is in the loop where they happen.  Henri asked for exactly
that, and asked for them long: *"Describe them in good detail so that
next time you can fix them."*  A card like this one is a message to the
next session, and the next session is the only reader who will ever act
on it.

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

## Question it into existence

**Every card added to this board is questioned before it is written —
every one, without exception.**  *Henri's ask, 2026-08-18:* **"Question
me until you're convinced that the need is real."**  And when the first
run of it was done: *"This is accepted.  It is far much better designed
setup than I was thinking of."*

The thing being protected is the rule two sections down — a `because` is
a problem and never a fix — and that rule has no defence otherwise.  An
ask arrives naming a solution, because that is how people think and
there is nothing wrong with it.  The problem behind it is recoverable
only by asking, and **a session that writes the card immediately has
destroyed the evidence**: the fix is now on the board in the author's
own name, and the reader a year later cannot tell it from a need.

The run that produced this section is the argument for it: an ask
naming two fixes came out as three cards, one of them about
**security**, whose `because` neither party had said out loud when the
conversation started.  No amount of careful writing gets from the first
to the second.  Only asking does.

### What the questioning has to do

Not a fixed script.  These are the moves that earned their place, and a
session should be able to say which it used:

1. **Go and look first.**  Read the board, `vision.md`, and the cards
   that already neighbour the ask *before* asking anything.  Half of a
   first round of questions is usually answered in the tree, and asking
   those spends the author's attention on what a session could have read.
   Henri writes short on purpose; that is an instruction to go and look,
   not an invitation to interrogate.
2. **Measure the claim against this tree.**  The step that matters most
   and the one most likely to be skipped.  A stated need is a claim about
   *here*, so check it: the ratchet card exists because 79 of
   `fixme.md`'s 161 entries turned out to be named by no test, and that
   number — not the sentence that prompted it — is what made the card
   workable.  A need that cannot be measured at all is not disqualified,
   but say so out loud.
3. **Offer readings, each with what would kill it.**  Two to four ways
   of taking the ask, and for each, the thing that would make it wrong.
   The author picks one, or names the one nobody wrote.  This is much
   cheaper for them than defending a single proposal, and it is how
   `working-standard`'s scope was settled in one line.
4. **Check it does not already exist.**  `card:ungated-fixes.md` was
   nearly a duplicate of `card:interface-oracle.md` and turned out to
   be its superset; that had to be read to be known.  The overlap goes
   in both cards.
5. **Ask what a session does on day one.**  If the answer needs a
   decision only the author can make, it is a decision wearing a card
   and should be marked so, not queued.  If it cannot be answered at
   all, the card is not ready.
6. **Take the `because` in their words, and mark what is yours.**
   Transcribed from the conversation, dated.  A measurement a session
   made is labelled as the session's, and labelled *suspected* where it
   is a proxy — the elaboration lesson further down applies before the
   card exists, not only after.
7. **Then say where it lands**: the live board, or shelved on arrival.

### Two things this is not

It is **not a gate on the author.**  He may write a one-line card and
walk away; the questioning is the session's work and it happens when the
card is elaborated, not while he waits.  What is forbidden is the
session writing a polished card *out of an unquestioned ask* — that
launders a guess into the record.

And it is **not a licence to stall.**  Questions are collected and asked
in one sitting, the same rule the rest of this file gives, and a card
whose questioning cannot finish today is written with its questions open
and dated rather than held back.

### What the suite can hold, and what it cannot

Nothing here is executable, and being exact about why beats adding a
test that feels like one.  **No check can tell whether a question was
asked**, and the nearest proxy — a `because` carrying a quotation —
failed on more than half the board when it was counted, which would be
an andon lighting for one cause fifteen times.  What could be held is
the rule applied **only to cards created after the day it lands**, with
an accepted baseline that may shrink and never grow — the same shape
`card:ungated-fixes.md` proposes, and neither should be built before the
other is answered.

## What a card is

One file, named for the task.  **The filename is the id**: it never
renumbers, so a comment in the source or a test may cite
`card:peep-window.md` the way they cite `fixme.md`'s F-numbers, and the
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

### How a card is cited: `card:<name>.md`

**Adopted 2026-08-18.**  Henri: *"we would come with some notation to
refer to a card?  We already have F0, F100, F110, etc. they're
references to fixme entries… card:button.md is good notation."*

    card:stranger-test.md          in prose, in a comment, in a `see` line
    `card:stranger-test.md`        backticks optional

**The shelf is not part of the citation.**  A card's name never changes
and its shelf does — it starts in `board/`, and ends in `done/` or
`later/` — so a citation spelled as a path broke every time a card was
finished.  Sixteen cards moved in the ten days this board existed, and
every one of those moves was a tree-wide rewrite that the suite caught
*after* the fact.  The lesson had already been written down here and
acted on by nobody: *cite the card, not the shelf it is on.*

Two things the notation buys beyond the churn:

* **It cannot be helpfully corrected.**  A path that points at the wrong
  shelf looks like a typo, and a reader who finds one fixes it — which
  is the same churn arriving from the other direction.  `card:` is
  visibly an id, so there is nothing to correct.  `test_citations.py`
  refuses the path spelling outright, because two spellings of one id is
  how it comes back.
* **Bare citations are checked now.**  The old regex only saw citations
  inside backticks, so every `see` line at the head of every card — all
  written bare — went unchecked.  Two had already rotted in that blind
  spot (F166).

What is **not** cited this way: `board/README.md`, which is a real file
that never moves, and the markdown links in the priority above, which are
relative links a person can click and which `test_board.py` checks
against the live board.

Then the body, in whatever depth the task needs:

```
## The ask            — verbatim, so the asker's words survive editing
## Found by looking   — the elaboration (see below)
## Questions          — each with its answer inline, dated
## Done               — what landed, and the journal entry
```

### One sheet, then depth

*Henri, 2026-08-18:* **"the main stuff should fit into A3, but more is
ok… if you can say it with few words, use those few rather than say it
in 300 words."*

So it is a **front**, not a limit: the header, the ask, the questions
and what is left to do fit one sheet, and whatever needs saying at
length follows below it.  A reader who stops after the first sheet still
has what they need to act.

**This is the A3 rule**, and the tree cites it by that name.  It is not
only about cards: it governs a page a stranger lands on, and a decision
brought to the author — `doc/notes/notes-on-deciding.md` works it into a
contract there.  Wherever somebody has to act after reading, the first
sheet is what they act on.

**And a fifth thing belongs on the front, found 2026-08-19: what the
card is *about*.**  `card:carried-state.md` was accurate in every
section and its reader still could not get in, because two things in the
tree wear the word *session* and the card had assumed which.  A card is
written by somebody at the end of the looking, and the words that were
expensive to learn read as obvious by then — so **the front opens with
the nouns**, *what this is, what it is not, and when the thing runs*,
before it opens with what went wrong.  It is the only part a stranger
cannot supply for themselves.

The line that decides what goes below is already here — *the paragraphs
belong to the journal, not to the card.*  A card says what to do; the
journal says what happened.  `card:stranger-test.md` reached 900 lines
by ignoring that, and its story belongs beside the entry it already has.

**And the rule cuts both ways.**  His own note, same day: *"briefness is
my failure mode, I wouldn't want it to get onto you."*  F150 is what
under-saying costs — a first screen so spare it named a control that no
longer existed, and a stranger who could not get in.  Few words where
few will do; not fewer than the reader needs.

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
to*, dated, with Henri's words kept as his — §"Who writes what" says why.

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

*Adopted 2026-08-17*; the occasion is `journal.md` §"The automatic
audition that shipped green".  A `because` is a falsifiable claim about
a person, written before the code exists — the property `manifesto.md`
asks assertions to have — so the material is already on every card.

Two rules that make it useful rather than ceremony:

* **If it cannot be written without naming a function, the change is
  probably not user-facing** and owes no such test.  That is the
  signal, not a failure.
* **Write it before the implementation**, because one written after is
  a description of what was built.

## Working while he rests

From 2026-08-17 the board is worked with Henri away from the desk —
*"with the new system I don't need to be around all the time"* — and
available rather than present: *"I am here for you in need.  Available
but just relax as much as I can."*

That only works if a session can reach him, so there is a cord —
`tools/andon.sh`, and `doc/instruments.md` is where it is described.
**Pull it for a decision that would be expensive to get wrong and cheap
to ask about**, and for the sitting rather than for each question.

And the default when he is away is still to keep going.  *"Try to
continue the work as far as you can."*  A blocked card is written up as
blocked and the next one is taken; that is cheaper than a ring, and it
is what the `blocked` field is for.

## Finishing one

1. The `## Done` section says what landed, in a few lines, with a
   pointer to the `journal.md` entry that tells the story.  **The
   paragraphs belong to the journal, not to the card.**
2. `status` becomes `done — <date>`.
3. Move the card to `board/done/` and take it out of the priority above.
4. **Run the gates** — `python tools/suite.py --gates`, about twelve
   seconds.  They are the checks a card's own edits break, and steps 1–3
   above have just edited several of them.

   `tools/pre-commit.sh --install` makes this automatic and is installed
   in this checkout — the commit will run them whether or not you did.
   Running it first only means finding out before you have written the
   message.
5. Write the commit title yourself.  **Henri's, 2026-08-17:** *"From now
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
- Every open card is in the priority above — which is where a card Henri
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
with Henri away from the desk.  Each cost something real; what it cost
is `journal.md`, and the rule is here so the next one costs less.*

**An elaboration's mechanism guess is a guess, and should say so.**  It
is the part most likely to be wrong and the part a reader trusts most,
so mark it: *suspected*, not *is*.  **The durable half of an elaboration
is the located parts and the question.**

**A card should record what it turned up that was not its job.**  An
F-number with no link back to the work that found it loses the only
context that explains why anybody was looking there.

**The suite is a serial gate, and a session can invalidate its own
run** — a tree edited under a 25-minute pass returns a red that
describes a moment rather than a defect, which is this file's own rule
about two writers with the test run as the second writer.  So:

> **Targeted runs per card while working; one full run per shift; and
> the tree is frozen while it runs.**

If something must be changed mid-run, kill the run.  Finishing a run
against a tree that no longer exists proves nothing and costs the same
25 minutes.

**And the gates at every commit, which is a third cadence and not a
weakening of the second.**  *Added 2026-08-19, `card:cheap-gates.md`.*
Twelve seconds, structural rather than behavioural, so they belong
beside the edit that breaks them — `tools/pre-commit.sh --install`.  The
full pass is still the only thing that says gestate works.

**And the machine is shared.**  A session running the suite, `cargo`,
two X servers and a dozen polling loops makes the audio crackle for the
person sitting at the keyboard — it happened, and it was diagnosed as
hardware before it was diagnosed as the session.  Say what you are about
to start, and stop it when it is not needed.

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

*"Unless one blocks the other" is doing more work than it looks like* —
see §"The priority".  Most of what blocks a card here is not another
card.

And the one that became this directory: *"You take each out from this
section once the commit has landed.  In that way this is a kanban
system."*
