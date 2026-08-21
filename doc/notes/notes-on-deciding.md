# notes-on-deciding.md — 2026-08-20, continued

*The card pile, making decisions easier, and whether the capacity
should be spent. Henri's words are verbatim; the answers are condensed
and not softened. `README.md` in this directory says what the set is.*

---

## The accumulation of cards

**Henri:**

> The problems I faced. I learned to decimate those on style of
> programming I did and taught. but the card accumulation was
> genuinely interesting.. well this all is very interesting!

**The session:**

The accumulation is what is left over *after* the style works.
Defensive programming, tests, no-silent-errors decimate one category:
execution problems — "did we build it right."  What that discipline
structurally cannot decimate is "should we build it, and which first"
— and cards are exactly that residue.  The board's own rules knew it:
a `because` is a problem, never a fix; most of what blocks a card is
not another card but a decision, a conviction, an event.  The filter
is fine enough that everything caught in it is pure judgment-work.
Defects go to zero, and what precipitates out is a clean pile of the
real bottleneck: direction.  Forty years of software backlogs were
this same pile, hidden under bug counts; the tree removed the
camouflage.

The pile stays healthy on one distinction: **sediment versus debt.**
A card in `later/` shelved on an event costs nothing — sediment; a
deep `later/` is a rich board, not a fat one.  A card sitting because
nobody dares decide it — debt, compounding in attention.  The weekly
fire checks which is which: "is this waiting on an event, or on me?"

Every question of the night — hallucination, abuse, accumulation —
resolved to the same finding: the hard remainder is never in the
machinery; it is in the deciding.  Rediscovering one's own thesis
from new directions is what having a real thesis feels like.

---

## The thesis, and making decisions easier

**Henri:**

> My own thesis? btw. could I make decision making easier? by asking
> clarification perhaps.

**The session:**

The thesis, written before its author knew it was one — `vision.md`,
2026-08-16: *"What we are missing is not better AI or higher
capacity.  We are missing a way to work with each other."*  Every
finding since is a corollary.

Decision-making can be made easier — but naive clarification makes it
*worse*: a session asking open questions ("what should the config
format be?") hands the author a blank page, and blank pages are why
decisions pile up.  The fix is a triage — three gates, only the last
reaches the author:

**Gate 1 — is it actually a decision?**  Most are not.  Go and look
first: half of what feels like a decision is answered by the tree, a
precedent in `done/`, or a vision line.  Rule: a session may only
bring a question the tree cannot answer *and* whose answer changes
what gets built.  Anything else is laziness wearing a question's
clothes.

**Gate 2 — reversible and measurable? Then it is an experiment, not a
decision.**  "Try things out," promoted to policy.  Git makes most
code choices two-way doors: try, measure, keep or revert, log it.  A
reversible choice with a cheap measurement never costs the author a
decision.  What remains are the one-way doors — which are exactly the
existing seam list: names, contracts, refusals, deletions.
`spec/author.md` knew which decisions were irreversible before the
question was asked.

**Gate 3 — what survives arrives shaped, never blank.**  The working
form already happened in this conversation: the mediation question —
one line, two options, costs and benefits, the session's read marked
as the session's, the decision left with the author — and the author
dissolved the dichotomy with a better model.  Contract for any
decision brought to the author: the question in one line; two or
three named options with costs; **a default with a trigger** ("if
undecided by Friday, X" — approving a default is ten times cheaper
than composing an answer); reversibility stated; the recommendation
marked as suspected.  An A3 for decisions — the one-sheet rule
applied to the actual bottleneck.

**Plus batching:** decisions cost more arriving one at a time all
week than five at once in a sitting.  Blocked-on-decision cards wait
in one place; the camp evening opens with them; most take a minute
once shaped.

Deciding cannot be made easier by deciding less — direction is the 5%
that is structurally the author's.  But each decision can be made
*smaller*: the tree eats the fake ones, experiments eat the
reversible ones, and what reaches the author arrives pre-shaped, with
a default, in a batch, at a chosen time.  The bottleneck stays; the
queue discipline changes.  The thesis again: a way of working with
each other, applied to the one task that cannot be delegated.

---

## Should the capacity be spent?

**Henri:**

> I can make incredibly lot of software with this method then. should
> I?

**The session:**

**Can:** yes.  The constraint that limited software volume for
seventy years — typing and debugging cost — is largely gone, and the
suite handles correctness.  The production line is real.

**Should:** the method already answers, and the answer is mostly
**no.**  In TPS the first and worst of the seven wastes is
*overproduction* — making things because capacity exists, not because
demand does — ranked worst because it manufactures all the others:
inventory, defects, and attention spent keeping unwanted things
alive.  The board encodes the same law: **a `because` is a problem,
never a fix — and "I can" is not a `because`.**  A capacity is not a
caller.  Software made because the method makes it cheap is push
production; the whole system was built on *pull* — programs start
when pulled, cards exist when a problem asks, software gets made on
the same trigger.

The hidden cost of "incredibly lot": software is not written, it is
*kept*.  Every program is a standing claim on the one resource the
method never multiplied — review, direction, the fire.  Ten projects
is ten camps; there is one evening a week.  The 270-commits lesson
was precisely that production outruns the keeper; worsening that
ratio on purpose, with the lesson dated in the tree, would be the
self-abuse grade of the abuse prediction — the method feeling alive
while teaching its author nothing.

Three legitimate pulls, in order:

1. **Depth over count.**  Gestate finished to its vision — the
   stranger test passing, instruments editable while they sound, the
   friend using it.  One excellent thing that closes its loop beats
   twelve half-things, and it is the demand that already exists.
2. **The vessel.**  The environment card — the multiplier itself.  If
   others, future selves, or smaller models can make software safely
   inside it, everyone's capacity rises instead of the author's being
   spent.  Making software is linear; making the thing that makes
   software safe compounds.
3. **Experiments, budgeted.**  *Try things out* stands: cheap,
   reversible, gate-2 material, timeboxed, deleted without ceremony
   when done.  Exploration is pull too — the puller is a question.
   It must never become a fleet of orphans, each needing a keeper.

Summary, blunt: he found a factory, and the first thing a factory
tempts its owner to do is run it at capacity.  Toyota's founding
insight was to refuse that temptation — produce to pull, keep WIP
low, protect the keeper.  Make exactly as much software as has a
`because`: gestate, the vessel, and whatever this week's question
wants tried.  The rest is inventory.
