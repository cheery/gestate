---
name: mide-staves-ui
description: "What mide's staves.ui does in 55 lines, the nine holes Henri left open in it, and the eight experiments elsewhere that each answer one of them — read 2026-09-06 before deciding drawn-scores rung 5"
metadata:
  type: project
---

**This was read on 2026-09-06, at Henri's ask** — *"let's look at mide's staves.ui
before deciding rung 5"* — and written down at his word, *"yes.  write
it down."*  His own verdict on it, the same sitting: **"I didn't
complete staves.ui and there left open holes into the design.  But I do
find it was unique space to explore."**  So the holes below are named
because he asked what a reader sees, not as a review; [[henri-lever-language]]
is the standing rule and it holds.  The file is
`~/Asiakirjat/mide/staves.ui`, 55 lines, and `counter.ui` beside it is
what makes the notation unambiguous.  **mide is unpublished and his** —
[[henri-prior-tools]] is the parent memory and says so.

## What the 55 lines are

A whole draggable staff editor: layout, hit regions, hover, a drag
preview with snapping, and the commit.  Four rules carry it.

    order (N+1) Onset K :- event Onset K, set Onset K : order by [Onset,K] : rank as N.
    offset (N+1) (X + 50*(T-U)^0.19 + W) T (12*(1-K2)) :- offset N X U W, order (N+1) T K2.
    present   (note K) [X-5,290-5,10,10] :- offset K X Onset W, order K Onset 1.
    draggable (note K)                    :- order K Onset 1.

**`A :/: B` is assert-A-retract-B**, which `counter.ui` settles: `count
(N+1) :/: count N :- on click upcount.`  So a gesture's *commit* is the
head of a rule:

    note TO :/: ?note Onset :- offset K X Onset W0, on (drop DX DY) (note K), …

No handler, no dispatch, no verb-table entry.  That is
[[henri-prior-tools]]' *everything has a command under it* in its
sharpest form: a binding and a command are one object rather than two
kept in step.

**And spacing is a recurrence with a power law** — `(T-U)^0.19`, with
bars taking width `12` and notes none.

## The three properties worth taking

1. **The hit region is derived from the layout.**  The drawn circle and
   `present`'s box read the same `offset` term, so the position cannot
   drift between what is seen and what is pickable.  That is exactly the
   failure [[gestate-canvas-unwired]] records — `observe`/`touch`
   orphaned when the pygame editor went, the drawing surviving and the
   interaction not, silently — and it is `spec/drawnscores.md`'s named
   cost for rung 5, *"the three seams that lost `touch`, none of which
   failed loudly"*.
2. **Preview and commit share one criterion.**  The snap is
   `:min ((TX-X-DX)*(TX-X-DX))`, written once to draw the ghost circle
   at the target and once to decide where the drop lands.
3. **55 lines is the size of what a staff editor essentially contains.**
   Not a portability claim — it says the cost of rung 5 is the seams and
   not the content.

## The nine holes

*In the model*

1. **No pitch.**  Y is nailed to 290 and `note Onset` has one argument.
   The staff lines are drawn and nothing lands on them.
2. **A note is keyed by its onset**, so a drop onto an occupied onset
   asserts a fact that already exists and one note silently vanishes.
   Chords are unrepresentable for the same reason.  Same shape as
   `notes.doubled` in gestate, which is refused at the gesture; here
   there is nothing to refuse with.
3. **The snap target is always an existing event** — `offset Target TX
   TO W1` ranges over what is already there — so a drag can move a note
   *onto* another event but never to a position nothing occupies.  No
   grid, no subdivision.  With 2, every drag tends toward collapsing the
   piece.

*In the derivation*

4. **The shared-derivation property covers position and not extent.**
   Hit box 10×10, note circle r=5, hover circle r=10 — three sizes for
   one object, written separately.  *A session claimed the stronger
   thing first and corrected it on reading again; the weaker claim is
   the true one.*
5. **`offset` is a linear recurrence over the global rank**, so every
   note's x depends on every earlier one and one edit invalidates the
   line.  Fine for a bar, not for a piece.
6. **No line breaking.**  One 1200-wide staff and a monotone `offset`,
   so a piece runs off the right forever — and xylem's Knuth–Plass is
   next door in the same lineage.

*In the semantics*

7. **Aggregation under recursion.**  `offset` is recursive over `order`,
   and `order` is defined by `rank as`.  Interleaving aggregation with
   recursion is where a rule language stops having an obvious fixpoint
   and needs stratification.  **The hard part, not an oversight** —
   `logic2/evaluator.py`'s aggregation branch is commented out, which
   reads as where it stalled.
8. **No selection.**  Hover and drag of one note.  For a design where
   everything has a command under it, *what the command applies to* is
   the missing noun, and most commands need it.
9. **No undo**, though `:/:` makes it nearly free: the retracted fact is
   right there in the rule that discards it.

## The eight elsewhere, each against one hole

| for | the work |
|---|---|
| `:/:`, hole 9 | **Dedalus** and **Bloom** (Alvaro, Hellerstein) — time as an explicit column, so assert-next-tick / retract-this-tick has a fixpoint that provably exists |
| `:min`, hole 7 | **Dyna** (Jason Eisner) — weighted logic programming, aggregation and recursion designed together |
| hole 5 | **differential dataflow** (McSherry), **DDlog** — incremental maintenance of exactly this recurrence |
| the whole idea | **Garnet** and **Amulet** (Brad Myers, CMU, late 80s–90s) — *interactors* as declared objects over a one-way constraint system; `present` + `draggable` reached independently, and the deepest prior art on what breaks |
| the whole idea | **Eve** (Chris Granger, ~2015–18) — a UI whose program and display were both records searched and produced.  Closest in ambition, and discontinued |
| holes 1 and 3 | **Apparatus** (Toby Schachman) — direct manipulation of a constrained drawing |
| hole 6 | **Lilypond** — spring-and-rod spacing with Knuth–Plass breaking, the sibling of `(T-U)^0.19` |
| the layout | **ThingLab** → **Cassowary** (Borning, Badros) → **xylem**, which is already his |

## Why it matters here

`card:drawn-scores.md` rung 5 is a `.notes` view that takes the window,
and its named cost is a new furniture kind crossing `furniture.rs`,
`window.rs` and the verb table — the three seams that can disagree.
`staves.ui` is a working demonstration that they need not be three.

**And the two projects hold complementary halves.**  `staves.ui` drags
in **time** and never in pitch; gestate's rung 4 (`notes.retune`) drags
in **pitch** and not in time, and `fixme.md` F199 already named
drag-in-time as the awkward one here.  Neither has the two-dimensional
case, which needs **two kinds of snap** — discrete-to-staff-line in
pitch, grid-in-subdivision in time — and the second is missing in one
dimension already (hole 3).

**How to apply:** before designing rung 5, take property 1 as a
*requirement* — one place says where a note is, and drawing, hit-testing
and draggability all read it — and take holes 2, 3 and 8 as the
questions any such view has to answer before it is built.  Do not take
the rule language itself as the thing to copy; hole 7 is why.  And ask
him before opening the files: they are his, and unpublished.

Related: [[henri-prior-tools]] is the parent and covers all three tools;
[[gestate-canvas-unwired]] is the seam this is about;
[[the-language-goal]] is the measure a rule language would be judged by.
