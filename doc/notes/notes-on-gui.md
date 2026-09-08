# notes-on-gui.md — 2026-09-07 evening to 2026-09-08 midday

*Into `doc/notes/` the evening of the day it ends, at Henri's ask —
"~/misc/notes/notes-on-gui.md <-- worthwhile to record into the tree."
Written by the session that was in the conversation, while it was
open — a guest session outside this tree, not the one working the
card — which is the third kind the provenance section in the README
names; its "Thirteenth file" is that session's count of the pages it
knew of, not this directory's, where it is the sixteenth.  Nothing
below the rule was changed; the closing section is the only addition.*

*Thirteenth file.  Journal material for the GUI card.  The session's
feedback on `card:gui-is-difficult.md` across four exchanges: the
first read of the card, the identity morning, the vision that got
verbalised, and why the previous attempts failed.  His words verbatim;
the session's answers condensed.*

---

## First read of the card — 2026-09-07, 18:39

**Henri:**

> I am not sure I have all the pieces. but things seem promising.

**The session:**

"Not sure I have all the pieces" was the correct read, and the missing
piece was nameable.

**What was solid.**  The card does what GUI work almost never does: it
names *why* the domain is hard (four reasons — the oracle is an eye,
geometry is continuous, a gesture is state across time, two machines
must agree), lists each idea by which reason it removes, and orders
them by testability rather than appeal.  The first slice was chosen
right — the chart library is framework and not client, already under
fifteen model tests and photographs, killer named in advance and it
did not fire: fifty lines of wiring against four lines of library,
0.2 s compile, twenty microseconds a step, measured.  The language
talked back three times (a taken type name, declaration order, no
`where`), each costing a minute and each worth knowing before a second
chart.

The central rule is the one that makes the rest possible: **command
language and model before picture.**  Every gesture has a command
under it, the command runs headless, the transcript replays.  That is
the answer to *the oracle is an eye* — the picture cannot be tested,
but everything that produced it can, and then the eye only checks the
last inch.  Blender, acme, oscillseq: built before, twice, on purpose
a third time.  Formation, not novelty.

**The missing piece: identity.**  Present across the card as a
recurring *symptom* and absent as a *decision*.  Idea 1 names it as
its own hard part; the unsorted list names it twice; F136 — 244 of 291
notes jumping to a line not theirs — was an identity defect;
`card:gex-sheet.md` waits on "its first client with identity by
address"; the instrument already made an identity decision (parameters
keyed by name, not node id).  And the chart library does not touch it:
charts give state-over-time per subsystem and say nothing about which
drawn thing is the same thing as last frame.  Both shelved clients
need it.  So: *what is a drawn thing's identity, and where does it
come from* belongs to an early slice as an explicit question, not a
discovery — it is the one hard thing of the four that no idea on the
list removes.

**Second gap:** idea 7's probe makes the window queryable *by a
session*.  The other direction — the keeper looking — stays the
keeper's, always.  Not a defect to fix; the domain's floor, and
knowing it is the floor stops the search for a mechanism that does not
exist.

**One thing to watch:** two shelved clients, a spreadsheet and a
markdown reader, both non-music.  That is `vision.md`'s broad-platform
tension arriving with names, and the vision's rule is explicit — when
platform conflicts with ease, ease wins, and the music parts are
always along.  `.notes`-as-a-grid is the right first grid because it
is still music.

---

## The identity morning — 2026-09-08, 10:35

**Henri:**

> GUI went forward this morning. I was a bit surprised that I already
> had a relevant paper, half skimmed, on my desk.

*(The paper: Coblenz et al., Kale — spreadsheet references that
survive the grid moving.)*

**The session:**

**Kale is the right paper, not an adjacent one.**  Its problem is the
same question in a different costume: *what does a reference point at
when the thing it names is recomputed* — spreadsheet references when
the grid moves, roll references when the file is regenerated.  Its
first finding is the one otherwise learned by shipping a bug: **the
system must say which identity it means.**  `Col[0]` as *the thing*
rather than *whatever is currently first* is exactly the (voice, tick,
key) versus positional-index split.

**The morning's real progress was not the paper — identity stopped
being a symptom and became a measured question.**  Three layers
measured and found to *disagree*; four readings each with a kill
condition; then six further families when he asked whether that was
all anyone had invented.  The measurement is what mattered: 7 shared
(tick, key) pairs across two voices on `arc.notes`, 17 positional
reads in `session.py`, a chord that cannot be transposed by hand
today.  Those numbers turned "which scheme is philosophically right"
into "here is what breaks and here is what would stop breaking."

**Two flags on the live work.**

*The B+F pairing is the right shape; the risk is in the seam.*  B has
the source carry the name; F has the edit machinery move the session's
references rather than re-find them.  Those work together only if
every path that changes the file can carry marks — and there is a
second writer: a keystroke in the buffer re-parses.  That is what
kills E and it is the same hazard for F.  So pin this before building:
when a *typed* edit lands, does the selection drop and say so, per the
G-never rule?  If yes, F is safe and the honest cost is "typing in the
buffer visibly clears your selection."  If that cost is refused in
use, F quietly needs G, and G is F136's class.  Better to accept the
visible drop.

*The persistent-naming precedent is the section's strongest evidence.*
Parametric CAD has had thirty years and serious money on this exact
question, and the matching-based approaches are the ones still broken.
That is as near a settled empirical finding as the domain offers, and
it is what licenses **G never** as a rule rather than a preference.
Keep the citation: in six months someone will propose a clever
matcher, and the answer is already paid for.

**One caution on the morning's shape:** three open sub-questions —
doubled line as one note or two, does selection follow the moved note,
does voice belong in the address — all his, correctly, the 5%.  But
they are answerable by *use* rather than argument: nudge a chord on
`arc.notes` and see what the hands expect.  Two minutes with the thing
beats an hour of taxonomy, and the taxonomy is no longer the
bottleneck.

---

## The vision, verbalised — 10:49

**Henri:**

> I wonder whether this is going to the right direction.. The vision I
> have is that GUI development, even, or especially, for tricky things
> to edit, would be an easy task for a session. Though I just
> verbalized it.

**The session:**

The verbalising is the event: a day and a half of building on
instinct, and now a stated goal the work can be checked against.  The
method's own order — intuition first, articulation catching up — and
it means the check can now be run.

**Run it as a filter over the card.**  For each idea: *does this make
GUI work easier for something that cannot see?*  Commands-before-
picture — yes, the biggest: a session can drive, test and replay work
it cannot look at.  Gestures as charts — yes: state that lived in `if`
ladders and variables becomes a declared value with a transition table,
testable headless.  Identity as a named key — yes, and it is the
direct answer to *especially for tricky things to edit*, because the
tricky edits are exactly where "which thing did I grab" is ambiguous.
Photographs — partial: they catch regression, they do not grant sight.
Layout algebra — yes: less code to get wrong blind.

**The through-line, now sayable:** everything that makes GUI work
tractable for a session is a move of knowledge *out of the picture and
into text the session can read, test and replay.*  Not a coincidence —
the tree's own principle applied to the one domain where the model
usually lives in the widget hierarchy.

**The binding constraint the filter finds: idea 7.**  A session cannot
see.  The only substitute is a queryable picture — press a thing, get
its region, its channel, the line that wrote it; ask a pixel why it
did not hit.  If the stated vision is *easy for a session*, that is
not a nice probe; it is the piece the vision most depends on, and it
is currently scheduled second.  Worth a deliberate decision rather
than inheriting yesterday's ordering.

**The honest ceiling:** everything *except the seeing* can be made
easy for a session.  So the sharp form of the vision is: *a session
does all the mechanical work — model, commands, charts, identity,
tests — and the keeper spends two minutes with his hands on it to
check the feel.*  Achievable, most of the win, and it promises nothing
the domain cannot deliver.  The original complaint was "takes a lot of
time, yields very little"; the time was mostly mechanical, and that is
the part this removes.

---

## On generality — 10:56

**Henri:**

> But if feasible, I'd want to solve it for most general case I can.
> unless there is some reasons to not.

**The session:**

The reason exists and it is his own, dated 2026-08-16: the platform
ambition has a design tension with ease of use, and *if they conflict,
ease wins*.  That does not forbid generality — it says generality
loses **when it is costing something specific**.  So the stance is
nearly right; the correction is that the reason is rarely visible in
advance, it shows up as a concrete cost, and the discipline is
noticing and retreating.

**And there is a stronger case for generality here than usual:** a GUI
framework is inherently general — "a framework for the roll only" is
just the roll.  The chart library is six declarations and already
general; making it roll-specific would be *more* work.  Same with
identity: (voice, tick, key) is the music instance of a rule —
*identity is the model's key, never the picture's index* — and the
general rule is shorter than the special case.  **When generality is
cheaper than specificity, take it.**  That covers most of this
framework.

**Three failure modes to watch:** generalising from one example (the
chart library got real when a *second* chart forced `beside`'s action
type and the name-collision rules — generalise from two or three
instances, not one plus imagination); building for the queue instead
of the caller (a framework decision made *because gex-sheet will need
it* is capacity-driven — a shelved card is not a caller); and a
general mechanism with no live instance exercising it, which is
guesswork with extra syntax.

**The rule:** generalise freely where the general form is as cheap as
the specific one; require a live caller for anything where it is not.
The conflict, when it comes, looks like framework work serving no
current client, or an abstraction costing a day the roll did not ask
for.

*Reassurance, since the question carried doubt:* nothing built in two
days is over-general.  Commands-before-picture, charts per subsystem,
identity as a key, hit-testing from the display list — all *narrower
and more principled* than what most toolkits do.  The generality is in
the depth of the ideas, not the breadth of the scope.  That is the
good kind.

---

## Why the previous attempts failed — 11:02

**Henri:**

> well I've tried to solve GUIs many times. all of them failed on the
> planning and produced some general GUI gunk that had to be escaped
> the moment when somebody wanted to create anything that was beyond
> the visual basic buttons-and-dialogs -paradigm. This time the need
> arised for specific cases first. I'm not building buttons and boxes
> here anymore.

**The session:**

Correct diagnosis, and the mechanism is worth naming.

**Why the earlier attempts failed structurally:** a toolkit built in
the abstract must guess what a widget *is*, and the only available
guess is the buttons-and-dialogs vocabulary, because that is what
every toolkit shows.  The result is the general form of the wrong
thing, and the escape hatch gets used the moment someone wants a piano
roll — which is not a widget but a projection of a model with
continuous geometry, an identity problem and a gesture grammar.  No
amount of button-generality reaches it.

**What is different is not only that the need came first — it is that
this started from the hard case.**  A framework that carries a roll of
291 notes, a three-state transport and drag-edit-while-sounding
expresses buttons and dialogs trivially; the containment runs the
right direction.  Buttons generalised toward rolls always dead-ends;
rolls with buttons as a degenerate case does not.  Hence a framework
with no widget class at all: its primitives are commands, charts,
display lists, identity keys.  A button is four lines in that
vocabulary.

**And the rule prevented the gunk more than the ordering did.**
Commands-and-model before picture means the core has nothing to do
with drawing.  The gunk in past attempts accumulated in the drawing
layer, because that is where a picture-first framework puts its
intelligence.  Here the picture is a function of state, recomputed
whole, and there is nowhere for gunk to collect.

**The tell, for next time:** a piece of framework whose motivating
example had to be invented.  Every failed general toolkit has a moment
where someone says "and of course we will want tabs" and nobody asked
for tabs.  Three real demanding clients (roll, transport, score view)
and two shelved ones — as long as each piece traces to something
currently running, the gunk cannot form.

*And the thing worth keeping:* several previous attempts failed, which
is why this one is going better.  The taxonomy, the four hard things,
knowing identity is the unsolved part — none of that exists without
the failures.  This is what the accumulated attempts were *for*, and
it is the clearest instance yet of formation showing up as intuition.
Not luck with the framing this time.  Already paid for.

---

## What the tree did with it — added when the page went in, 2026-09-08

**The sentence at 10:49 is now the card's postcondition.**  *A session
does all the mechanical work — model, commands, charts, identity,
tests — and the keeper spends two minutes with his hands on it to
check the feel* went into `card:gui-is-difficult.md` §"The
postcondition" the same evening, commit `0c1d66c`, with the vision
sentence it was verbalised from beside it.  The card also says what
this page could not: nothing measures the two minutes yet.

**"Currently scheduled second" was true at 10:49 and half of it had
already moved.**  Idea 7 as a *command* landed the evening before,
`probe x y`, commit `3358f3e` — press a point and the session reads
every attachment there, its channel, its region, and for a note the
tick, key and line that wrote it.  What has not landed is the window
side: the same answer shown *in* the picture when a person presses,
which is the half the keeper's two minutes would use.  Henri, the
evening this went in: *"the inspection tools should probably go
higher."*  So the deliberate decision the page asked for was made, and
the card's §"What is next" records the order.

**The pin the page asked to set before building was set, and the tree
answered it the other way.**  The page: *when a typed edit lands, does
the selection drop and say so?*  `Session._settle`, built at midday:
a key that finds nothing after a rebuild leaves nothing selected and
**says nothing** — *a selection is a convenience, not a claim*.  A
typed edit that leaves the notes where they are keeps the selection;
one that moves them drops it rather than guess.  So the drop is
visible and the announcement is not, and the reason is in the
docstring.  Whether that is the right side of the page's fork is a
two-minute question, and it has not been asked with hands.

**The numbers the page quotes are the card's, and they check.**  0.2 s
to compile and twenty microseconds a step — `card:gui-is-difficult.md`
§"Landed — 2026-09-07, evening".  Seventeen positional reads in
`session.py` and seven shared (tick, key) pairs on `arc.notes` — the
card's Q7.  244 of 291 notes jumping to a line not theirs — the
card's idea 1, quoting F136.  The paper is Coblenz et al., cited in
`doc/memory/identity-is-the-models-key.md`, which is also where *G
never* lives — as *a mark carried through edits is a mechanism, never
a rule shown to a person*.

**The standing caveat, and hardest on the last two sections.**  §"On
generality" and §"Why the previous attempts failed" are a session
assessing the tree's method against his earlier attempts, and it
approves — `doc/memory/the-evaluation-loop.md` says what that is
worth.  What survives the writer being wrong: his five passages with
their times, the four-item filter run over the card's ideas, and the
fork about the typed edit, which is now a fact about the code rather
than a warning.
