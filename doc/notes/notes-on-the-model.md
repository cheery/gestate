# notes-on-the-model.md — 2026-09-09, morning

*Into `doc/notes/` the same day, at Henri's ask — "~/misc/notes/notes-on-the-model.md
could be added into the notes and to card:gui-is-difficult.md."  Written
by a guest session outside this tree, in the conversation, while a
different session worked the card here — the third kind the provenance
section in the README names; its "Fifteenth file" is that session's
count of the pages it knew of, not this directory's, where it is the
eighteenth.  Nothing below the rule was changed; the closing section is
the only addition.*

*Fifteenth file.  Written to be handed to a session working
`card:gui-is-difficult.md`.  Two exchanges: what the GUI framework
actually is, and the relational model as a candidate.  Henri's words
verbatim; the session's answers condensed.  The session is outside the
tree and its reads are **suspected** — the two model sketches at the
end are what would settle them.*

---

## The model and its command language *are* the framework

**Henri, 09:33:**

> btw. I understood a thing: It is that a model and command language
> are the GUI framework. standardized formats do form the foundation
> for GUI to exist. text editors are an example of such successful GUI
> formation. there likely is no general GUI framework that would work
> for everything. All the successes are relative to model they form.

**The session:**

Correct, and it explains every failure named the day before —
including tic-tac-toe.

**The text editor case is the strongest support, stated precisely.**
What makes editors a solved GUI is not that someone built a great
widget toolkit — it is that the *model* is settled: a buffer is a
sequence of characters with a point and marks.  Once that is fixed,
everything follows.  The command language is expressible (insert,
delete, move point, mark region); the picture is a function of the
model; undo is a stack of model operations; and — the giveaway —
**every editor converges on roughly the same commands**, because the
commands are implied by the model rather than invented by the
designer.  Vi, emacs, acme, sam: wildly different pictures, nearly
identical operational vocabularies.  That is what it looks like when
the model does the work.

The same holds for every GUI domain that actually works.
Spreadsheets: cells addressed by coordinate, values or formulas, a
dependency graph.  Terminals: a character grid with a cursor.  Vector
drawing: a scene graph of shapes with transforms.  Each is a *solved
model with a settled vocabulary*, and the interface is downstream.
The domains that stay hard — GUI builders, node editors, music
notation — are exactly the ones where the model is contested or
unstated.

**So the corollary holds: there is no general GUI framework, because
"general" would mean model-independent, and the model is where all the
leverage is.**  What can be general is only the *substrate* — pixels,
hit-testing, event delivery, layout — the thin layer that already
stands and that the card correctly refuses to call the framework.
Everything above it is per-model.  That is why buttons-and-dialogs
toolkits fail outside their domain: they *do* have a model (a tree of
controls with properties and callbacks), it is merely impoverished,
and everything that does not fit gets an escape hatch.  Yesterday's
diagnosis and this morning's realisation are the same fact seen twice.

**And it explains tic-tac-toe.**  There was no model.  Nine cells, two
players, a win predicate — trivial, and *unstated*, so the session had
nothing to derive commands from and filled the vacuum with structure.
Give it the model first (board := position → mark; move := place mark;
state := in-play | won | drawn) and the commands are three, the
picture is a function, and there is nothing left to over-engineer.
The complexity was not the session's taste; it was the absence of the
thing that constrains taste.  So the rule the framework needs is not
"be simpler" — it is **no picture before the model is written down**,
which the card already stresses, now with a demonstrated cost for
skipping it.

**One sharpening, because it changes what the deliverable is.**  If the
model is the framework, then what is being built is not a toolkit — it
is **a method plus a substrate**.  The method: write the model, derive
the command language, make gestures charts over it, key identity from
the model, test headless, then draw.  The substrate: the thin general
part.  A new client does not get a toolkit to assemble; it gets the
method applied to its own model.  That is a smaller and more honest
claim than "GUI framework", it is what would actually transfer, and it
retires the gunk risk permanently — general widget machinery cannot
accumulate if the deliverable is a procedure.

> **The line for the card:** *the model and its command language are
> the framework; the general part is only the substrate, and successes
> are always relative to a model.*

---

## The relational model as the candidate

**Henri, 09:45:**

> I am believing that a relational model, eg. facts asserted or
> retracted, would make a good model. and right now I am experimenting
> with that. It does resemble spreadsheets, so that card may go with
> it.

**The session:**

Well-motivated, and it fits the tree unusually well: `spec/data.md`
already has Datafun with seminaive evaluation, so the incremental
recalculation a relational model needs is not hypothetical, it runs.
The spreadsheet connection is real rather than a resemblance — a
spreadsheet *is* a relational model wearing a grid, which is why
`card:gex-sheet.md`'s day-one question already framed it as *a
relation from address to expression, dependency derived*.  Not two
ideas converging by luck; one idea already written down twice.

**Why the bet is sound.**  Assert/retract gives what every hard GUI
problem needs and most toolkits fake — a single authoritative model
with derived views:

- **The picture becomes a query.**
- **Undo becomes retracting what an operation asserted.**
- **Identity becomes what a fact is *about*** — the (voice, tick, key)
  decision restated in general form: a fact's subject is its key, and
  positions are derived, never authoritative.
- **Commands fall out**, because assert/retract *is* a command
  vocabulary.

There is precedent — datom-based UIs, Datalog-backed editors, the
whole *the UI is a query over a database* lineage — so the failure
modes are known rather than undiscovered.

**The known failure modes, as things to watch:**

1. **Query cost under interaction.**  The card already measured this
   as the killer for query-per-frame hit-testing — 103 ms on the
   stacked roll.  A relational model makes it tempting to derive
   *everything* per frame, and derivation cost is what turns an
   elegant model into a laggy editor.  Seminaive incremental
   evaluation is the answer and it exists; the discipline is making
   sure the hot paths go through the incremental path rather than
   recomputing.
2. **Where non-relational state lives.**  Drag-in-progress, caret,
   selection, scroll — transient, and it is not obvious they belong in
   the fact store.  Two answers: assert them too, as facts about the
   session; or keep them in the statechart.  Both work; mixing them
   arbitrarily is where confusion starts.  Decide once, early, write
   it down — cheap now, expensive in three weeks.
3. **Retraction semantics.**  What happens to facts derived from a
   retracted fact — cascade, or dangle?  Datalog has answers; pick one
   and state it.  Same class of question as *does selection follow the
   moved note*, and it bites in the same place.
4. **Is it faster to think in?**  Relational models are elegant and
   can be slower to reason about for concrete manipulation than a
   plain structure.  The test is not whether it is principled — it is
   whether **tic-tac-toe's model fits in five lines and the roll's
   model fits on a page.**  If the roll needs a paragraph of encoding
   tricks, that is the signal.

**The experiment worth running while it is cheap:** write the model —
only the model, in facts — for two clients already understood: **the
roll and tic-tac-toe.**  Nothing drawn.  If both come out small and the
commands fall out as assert/retract pairs without contortion, the bet
is validated in an afternoon and `card:gex-sheet.md` becomes the third
instance rather than a hope.  Two instances is also the tree's own
rule for when generalising is safe — the chart library became real
when a *second* chart forced the questions the first could not.

---

## What the tree did with it — added when the page went in, 2026-09-09

**The line went to the card's front.**  *The model and its command
language are the framework; the general part is only the substrate, and
successes are always relative to a model* is now in
`card:gui-is-difficult.md` §"What this is, what it is not, and when it
runs", where a reader who stops after the first sheet meets it.

**It is not independent confirmation of the sitting, and saying so
matters.**  The same day, in this tree, a clean-board sitting arrived at
the same place — a document is **facts**, the algebra is **assert and
retract**, the framework is a form and not an object.  That reads like
two witnesses and is one: this conversation is at 09:33 and 09:45, and
his questions in the sitting — *what is the model, what is the command,
what is the view* — came after it.  So the sitting's evidence stands on
its own (the tree already wrote this grammar twice in `.notes` and
`.desk`; the roll's seven verbs are three shapes; the record algebra's
add and remove turned out to be *typing*) and its **agreement** with
this page proves nothing.  `doc/memory/conditioning-shows-under-work.md`
has the tree's name for this shape.

**The experiment it proposes was overtaken by half of itself, the same
day.**  The page asks for *the model — only the model, in facts — for
the roll and tic-tac-toe*, nothing drawn.  What exists is more than a
sketch on one of the two: `gestate/notes.ges` is what a `.notes` **is**,
in facts, and `gestate/notes.py` reads it — the field sets, the
refusals, the at-most-one rule and the canonical order are derived from
it and no longer written twice.  Tic-tac-toe's model is not written.

**And its own test has a number now.**  *Tic-tac-toe's model fits in
five lines and the roll's model fits on a page* — the `.notes`
declaration is **41 lines of code**, 95 with its prose, which is a page.
No encoding tricks were needed; what it *did* need was a third sort
term, `Among`, for a reference ordered by where the record it names
stands.

**Of its four failure modes, one is decided, one is open, and two have
numbers.**  *Where non-relational state lives* is decided: the
statechart, not the fact store — the card's three forms are records,
charts and queries, and the drag, the caret and the transport are
charts.  *Retraction semantics* — what happens to facts derived from a
retracted one — is **open**, is in nothing the card says, and is the
first thing an assert/retract command will meet.  *Query cost under
interaction* is the card's `tools/queryframe.py` and now also
`tools/pressable.py`, which measures what a press costs when every note
is its own pressable element.  *Is it faster to think in* is the one
only hands can answer.

**The standing caveat, which the page sets itself.**  The writer is a
session outside this tree and marks its own reads *suspected*.  What
survives the writer being wrong is his two passages verbatim with their
times, and the four failure modes, which are a list to check against
rather than a claim about here.
