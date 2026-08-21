# Working a board of task files

This is how a task is worked.  The board is a directory of files, one
file per task, and this page is the contract for what is in them and who
touches them.

The practice below is the mainstream one — Kanban as it is usually
taught, with the parts of the Toyota Production System that survived
into software, and the ticket-writing conventions common to most teams.
Nothing here is unusual.  It is written down because a convention
everybody assumes and nobody states is a convention new people get
wrong.

---

## Pull, and the limit that makes it pull

**Work is pulled, not pushed.**  Nobody is assigned a card.  A worker
who has finished takes the next thing they can work on, which means the
board has to be readable enough for that choice to be quick.

**Limit work in progress.**  This is the one rule that makes a board a
kanban board rather than a list, and it is the one most often dropped.
The limit is on the *doing* column, it is a number, and it is small —
one or two per worker.  Everything the method claims follows from it:

* **Cycle time falls.**  Little's law is not a metaphor here — average
  cycle time is work in progress divided by throughput, so halving the
  number of things in flight halves how long each takes, with no change
  to how fast anybody works.
* **Blockages become visible.**  When a worker cannot start something
  new, the blocked item is in front of them instead of behind a pile of
  started ones.
* **Context switching stops being free.**  It never was; the limit is
  what makes the cost land somewhere a person notices.

A common starting point is *number of workers plus one*, then lower it
until the board is uncomfortable, which is where it belongs.

## Columns, and the definition of done

The minimum board is three columns: **to do**, **doing**, **done**.
Most teams need one or two more, and each extra column is a real cost —
it is another place work waits.  Add a column only when something
genuinely queues there.

**Every column needs an explicit exit criterion**, written down.  "Done"
without a definition of done is the single most common source of
rework:

* the change works and has been seen to work
* it has tests, and they run in the normal pipeline
* it is documented where a user would look
* it has been reviewed by somebody who did not write it
* it is merged and deployed, or explicitly staged

If a step in that list is routinely skipped, either fix the practice or
delete the line.  A definition of done that lies is worse than none,
because it is quoted in arguments.

**A definition of ready** is the same idea at the other end: what a card
must contain before anybody may pull it.  Usually: a clear problem, an
acceptance criterion, no unanswered blocking question, and small enough
to finish inside a normal work period.

## Prioritising

Priority is the product owner's call, and it is a call, not a
calculation.  Three frames that help make it and each of which fails
alone:

* **Value against effort.**  Cheap and valuable first.  Fails when it
  systematically starves the expensive-and-essential.
* **Cost of delay.**  What does it cost per week that this is not done?
  Divide by duration and you have weighted shortest job first, which is
  the scheduling rule with the best theoretical backing available.
* **Risk.**  Do the thing that could invalidate the plan early, while
  changing the plan is still cheap.

**Write the priority down and keep it in one place.**  Two lists is
zero lists.  Re-order it on a fixed cadence rather than continuously,
because a queue that re-sorts every hour cannot be planned against.

**MoSCoW** — must, should, could, won't — is worth the ceremony mainly
for its fourth bucket.  Writing down what will *not* be done is the part
teams skip and the part that prevents the argument recurring.

## What a card contains

One file per task, named for the task, with a stable identifier that
does not change when the card moves.  Numbering by position breaks the
moment something is inserted or removed; a name or an issued number does
not.

A card should carry:

```
    id        stable, never reused
    title     what a person would call this
    status    to do | doing | blocked | done
    owner     who is working it, while somebody is
    problem   what is wrong, for whom, and how you know
    outcome   how anybody will tell it worked
    estimate  size, not hours
    links     designs, tickets, related cards
```

**Write the problem, not the solution.**  A ticket that says *add a
dropdown* has thrown away the information that would let a reader solve
it better.  A ticket that says *users cannot tell which of the two
export formats they picked* keeps it.  This is the same discipline as a
good bug report and it is just as often skipped.

**Five whys** is the standard tool for getting from a symptom to a
cause, and its standard failure is stopping at the first answer that
assigns blame.  A cause you can act on is a process, not a person.

### INVEST, for the shape of a card

The mnemonic is worth knowing because each letter names a real failure:

* **Independent** — can be done without another card landing first.
* **Negotiable** — describes a need, leaving room for how.
* **Valuable** — a user or the business can say why it matters.
* **Estimable** — enough is known to size it; if not, the card is a
  research spike and should say so.
* **Small** — finishable in a few days at most.
* **Testable** — has an acceptance criterion somebody could check.

A card failing three or more of these is usually an epic wearing a
card's clothes, and should be split before it is pulled.

### Acceptance criteria

Written before the work, in the user's terms, and checkable.  The
*given / when / then* form is popular because it forces all three parts
to exist:

```
given  a project with no saved exports
when   the user picks CSV and confirms
then   a file appears in the chosen folder and the format is named in
       the confirmation
```

Criteria written after the implementation describe the implementation.
That is the most common way acceptance testing becomes theatre.

## Estimation

**Estimate size, not duration.**  Story points, t-shirt sizes, or any
scale a team agrees on — the scale does not matter and the relative
judgements do.  Convert to time using measured throughput, never by
declaring a points-per-day rate.

**Estimates are for planning, not for accountability.**  The moment an
estimate is used to judge a person, it becomes a negotiation and stops
being information.  This is the single fastest way to destroy the
practice.

**Reference cards** beat abstract scales.  Pick two or three finished
cards everyone remembers and size against those.

And it is legitimate to run with **no estimates at all**, counting cards
instead: for cards of roughly similar size, throughput measured in cards
per week predicts as well as points do and costs nothing to maintain.

## Blockages, and stopping the line

**A blocked card is marked blocked, with what it waits on and since
when.**  A blocked card that looks like a working one is the most
expensive object on a board, because the time it spends waiting is
invisible.

**Andon** is the Toyota practice this comes from: any worker may stop
the line when they see a defect, and stopping is treated as correct
behaviour rather than as an escalation.  The software version is that
anybody may halt a release, and that a broken build is fixed before
anything else is pulled.  The practice fails in exactly one way — when
stopping the line is punished, quietly, and people stop doing it.

**Escalate on age, not on noise.**  A card blocked for two days is
raised because it is two days old, not because somebody complained.
That is a rule a board can apply mechanically and a person cannot apply
fairly.

## The daily pass

Fifteen minutes, standing up, **walking the board from right to left** —
right being closest to done.

The reason for right to left is that finishing beats starting, and a
board read left to right talks about new work first every single day.
Three questions per card, and they are about the card and not about the
person:

* what does this need in order to move?
* is anything blocking it?
* is anything about to be blocked?

It is not a status report.  If the meeting has become one, the board
stopped being readable and the meeting is compensating for it.

## Flow, and the measurements worth keeping

Four measurements pay for themselves and each one answers a specific
question:

| measurement | question it answers |
|---|---|
| **cycle time** | how long from pulled to done |
| **lead time** | how long from asked to done — the customer's number |
| **throughput** | how many cards per week |
| **work in progress** | how many things are open right now |

A **cumulative flow diagram** shows all four at once; a band that widens
over time is work in progress growing, which is the disease this whole
method treats.

**Measure the distribution, not the average.**  Cycle time is heavily
skewed, so the useful statement is *85% of cards finish within nine
days*, not *the average is four*.  Averages of skewed data promise dates
that are missed more than half the time.

**And a measurement nobody looks at should be deleted.**  A dashboard
that has stopped being read is not neutral; it is evidence that the team
is measured rather than measuring, and it makes the next real number
harder to introduce.

## Classes of service

Not all cards are the same kind of thing, and pretending otherwise is
what produces heroics:

* **Expedite** — drop everything.  Strictly limited: one at a time, and
  it should be rare enough to be memorable.
* **Fixed date** — has a real external deadline.
* **Standard** — the normal case, pulled by priority.
* **Intangible** — maintenance, refactoring, tooling.  Valuable, always
  loses a priority argument, and therefore needs a reserved share of
  capacity rather than a place in the queue.

Give each a swimlane or a tag, and give the intangible one a percentage
of the board.  A team with no reserved capacity for maintenance does
none, regardless of what anybody believes.

## Bugs

Triage by **severity** — how bad when it happens — crossed with
**frequency** — how often.  The crossing is what stops the loudest bug
from beating the worst one.

Keep bugs on the same board as features and pulled from the same
capacity.  A separate bug backlog becomes a place bugs go to be
forgotten, and the split hides the true cost of a feature that shipped
badly.

**A fixed bug earns a regression test**, or it is not fixed, it is
currently absent.  This is the cheapest rule in software and the most
frequently waived under deadline.

## Going to see

**Gemba** — go to the actual place — is the practice of forming
judgements where the work happens rather than from a report about it.
For software that means: watch a user use it, read the logs, run the
build yourself, open the file.

The standard failure is the **inspection**: arriving to evaluate people
rather than to see the work.  Done that way it is worse than not going,
because it teaches everybody to prepare a version of the work for
visitors.

## Improving the method itself

**Kaizen** is small, continuous, and done by the people doing the work
— not a quarterly initiative.  The board practice for it is a
**retrospective** on a fixed cadence, with three properties that decide
whether it is worth the hour:

* it produces **one change**, not a list of aspirations
* the change has an **owner and a date**
* the next retrospective **starts by checking the last one's change**

A retrospective that skips the third property is a complaints meeting
with a facilitator, and everybody in the room knows it by the third
session.

**Blameless post-mortems** on incidents, written down, with a timeline
and contributing causes rather than a root cause.  The written record is
the whole product; the meeting is how it gets written.

## Refinement — how a card becomes ready

Cards do not arrive ready and they do not become ready by sitting.
Refinement is the scheduled work of taking the next few cards from the
inbox and making them pullable, and it has one measurable purpose: **at
any moment there should be about two iterations of ready work and no
more.**

Less than that and the board stalls waiting on decisions.  More than
that and the effort is wasted, because priorities will change before the
cards are pulled and the elaboration will be rewritten or thrown away.
Refining the whole backlog is the most common way a team spends real
time producing nothing.

What refinement does to a card, in order:

1. **State the problem** in the affected person's terms, not the
   system's.
2. **Find the unknown.**  Every card has one thing nobody has checked;
   name it, and check it now if the check is cheap.
3. **Write the acceptance criterion**, and see whether it can be written
   at all.  A criterion that cannot be stated means the card is not
   understood yet.
4. **Size it**, and split it if the size is a guess wearing a number.
5. **Name the dependencies** — the other cards, the people, the
   decisions.

The output of a refinement session is not a filled-in template.  It is
**the list of questions somebody now has to answer**, and a session that
produced none probably did not look hard.

## Splitting a card that is too big

Splitting by *layer* — one card for the database, one for the API, one
for the interface — is the intuitive move and it is the wrong one:
nothing is finishable, nothing is demonstrable, and every card is
blocked on its neighbour.  The patterns that work all produce something
end-to-end and thin:

* **By workflow step** — the first step only, working all the way
  through.
* **By variation** — one input format now, the rest later.
* **By rule** — the simple case, with the exceptions as their own cards.
* **By interface** — the plainest usable version first; the polish is a
  second card that can be prioritised honestly against everything else.
* **By operation** — create now; edit, delete and list later.

The test for a good split: **each half is worth doing on its own.**  If
one half only makes sense once the other lands, that is not a split,
that is a dependency you have written down twice.

## Spikes

When a card cannot be estimated because something is unknown, the
honest move is a **spike**: a separate, timeboxed card whose deliverable
is knowledge rather than working software.

Three rules keep it from becoming an open-ended research project:

* **Fixed timebox**, agreed in advance — a day, two days.  When it
  expires the spike is over whether or not the answer arrived, and the
  absence of an answer is itself a finding worth reporting.
* **A written question**, decided before the work starts, and the spike
  is done when the question is answered.
* **The deliverable is a note, not a branch.**  Code written during a
  spike is evidence, not product, and expecting to keep it is what turns
  a two-day spike into a fortnight of cleanup.

## Dependencies between cards

Record a dependency in **one** place — on the card that is waiting, not
on both — because two records disagree eventually and the disagreement
is discovered by the person least able to resolve it.

Then treat dependencies as a queue problem rather than a scheduling one:

* **A card blocked on another card should usually be split**, so the
  unblocked part can move.
* **A card blocked on a person** needs that person told, with a date.
  Nobody has ever been unblocked by a field in a tracker.
* **A card blocked on a decision** is the expensive kind, because it
  looks like work and is actually a question.  Collect these and take
  them to whoever decides, in a batch — decisions are far cheaper in
  groups than one at a time.

## Ownership and hand-offs

One owner at a time, named on the card, and the owner is whoever is
actually working it rather than whoever requested it.

**Every hand-off costs a re-read**, which is the cost the person handing
off never pays and never sees.  A board with many small columns has many
hand-offs by construction; that is the hidden price of the extra column,
and it is why the minimum board is three.

When work must change hands, the outgoing owner writes what they know
into the card before releasing it — what was tried, what was ruled out,
what they would do next.  A hand-off with no written state is a restart
with a friendly face.

## Linking the board to the code

The connection between a card and the change that implemented it is
worth maintaining in exactly one direction: **the commit or the pull
request names the card.**  Cheap to write, impossible to forget once it
is a convention, and it makes the archive searchable from the code side,
which is the direction people actually search in — somebody reading a
strange line of code wants to know why it is there.

Do not attempt the reverse as a discipline.  A card kept updated with
the commits that touched it is a second copy of information version
control already holds perfectly, and it goes stale the first busy week.

## What does not belong on the board

* **Ideas nobody has committed to.**  Keep an inbox, and let things die
  there.  A backlog of four hundred cards is not an asset; it is a
  reading cost paid by every person who scans it, forever.
* **Work in progress that nobody can see.**  If it is being worked, it
  is on the board.  Side work kept off the board is how a team discovers
  its capacity was never what it thought.
* **Documentation of the system.**  A card is a task, not a reference.
  When a card starts explaining how the thing works, that text belongs
  in the documentation and the card should link to it.

## Archiving

Keep finished cards, do not delete them.  They are the only honest
record of what was actually done and how long it took, and the first
time somebody asks *when did we change that, and why* they are the
answer.

Archive on a cadence — monthly is common — so the live board stays
scannable in one screen. The archive is read rarely and searched often,
which means the searchable parts are the title and the problem
statement.  Write those two as though a stranger will find them in two
years, because that is who reads them.
