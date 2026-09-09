# gex-sheet — gestate's own spreadsheet, and the sequencer that is one

    status   shelved — 2026-09-07
    because  "I'd like to implement excel and markdown reader to gestate
             some day.  I wonder if that's crazy talk or whether it
             makes sense." — Henri, 2026-09-07; then, of the three
             readings a session offered: "I meant the third one,
             gestate's own spreadsheet.  .gex (just as an idea of a name
             format for them) and maybe make a sequencer that uses it
             … And yes. .notes could use excel view as well."
    asked    Henri, 2026-09-07 — "Write the cards into later/ shelf."
    see      card:gui-is-difficult.md — what this waits on: the
             framework, and its first client with identity by address
             card:drawn-scores.md — `.notes`, a flat table of records
             already; the grid is its second view
             card:notes-editor.md — the data road a cell edit must take:
             data to the running instrument, never a recompiled program
             spec/data.md — Datafun with seminaive evaluation ∪ Rizzo:
             a cell is a signal, a formula a pure function, recalculation
             already incremental
             doc/memory/gui-command-language-first.md — the model and
             the verbs before any grid is drawn
             vision.md §"Gestate as a generic working platform" — "a
             visual system along the text", "Gestate gestates"; and
             §"What gestate won't be" — plain files you can read
             without it, no borrowed vocabulary

## What this is, what it is not, and when it runs

**A sheet of cells whose formulas are gestate expressions**, a `.gex`
file that is plain text a person can read without the tool, evaluated
by the G-machine at edit time, drawn as a grid in the window.  **And
the sequencer is the sheet**: a tracker is a grid whose rows are time
and whose columns are voices, the one sequencer family that was always
a spreadsheet — so a column may be computed from another, a row
generated, a cell an expression in the language the instruments are
written in.  It is **not** Excel read or recalculated: `vision.md`
refuses borrowing a vocabulary to get power cheaply, and an `.xlsx`
import, if ever, is one importer among others.  It is not a new
engine: the sound arrives as events to the running instrument, the
road `card:notes-editor.md` built for records.  **`.notes` gets the
grid view too**, his ask — a notes file is already a table.

## Measured against the tree, 2026-09-07 — the session's reading

| exists | where |
|---|---|
| cells as signals, formulas as pure functions, incremental recalculation | `gestate/seminaive.py`, `gestate/reactive.py`, `spec/data.md` |
| a flat table of records as a score, swapped live under the instrument | `.notes`, `card:notes-editor.md` slices 1–2 |
| feedback through a delay, which a cell reading its own past would be | the `Sig` grammar, `spec/liveaudio.md` |
| a grid view | **nothing** — the GUI framework's first client |
| the model written down | **nothing** |

## What would kill it

1. **A cell edit that recompiles a program.**  Five seconds a
   keystroke, the drawn-scores lesson.  The cells are data the
   G-machine evaluates; the LLVM road is for instruments.
2. **Cycles undecided.**  Excel forbids or iterates; here a cell may
   read its own past through a delay, and that is what makes the sheet
   a sequencer.  Decided in the model, not found in the grid.
3. **Drawn before modelled** — the score box's hundred and thirty
   hands.  The framework first, this as its first client.

## Fitted to gestate's one document type — Henri, 2026-09-09

**Q1 below is answered before this card wakes.**  In
`card:gui-is-difficult.md`'s clean-board sitting he took `.notes` and
`.desk` as one form — a text of **record lines**, a record being a kind
word and its fields, with the kind declaring its key and a reference
declaring whether it means a thing, a place or a set — and then:
*"me voitaisiin ottaa se gex-spreadsheet ja sovittaa se tähän
dokumenttityyppiin mukaan."*

So a `.gex` is not a format of its own: a cell is a record, its
address is its key, and the sheet's kinds sit beside `note`, `section`
and `knob` in one grammar.  Kale's three reference kinds — `Col[0]` a
thing, `Col[+1]` a place, a query a set — are the second half of that
decision and were already this card's open question.  **And where a formula lives, his lean the same day:** a cell holds its
own expression and the `.ges` beside supplies the vocabulary it calls —
reading (i), *"Minä arvelen että (i) on hyvä.."* — the way `arc.notes`
holds the notes and `arcnotes.ges` the instruments.  With it comes one
rule: a cell's **address is its key and must be literal**, its content
is its expression; a key that is an expression has no identity until it
is evaluated.  What stays this card's own: where time lives in a
sequencer sheet, and how long the G-machine takes over a few hundred
cells.

## Questions — day one, when it wakes

1. **What is the model?**  Sheet := a relation from address to
   expression; value := its evaluation; the dependency relation
   derived.  Sentences, a type, invariants — *every value derivable
   from the file alone*, *no cycle without a delay* — and the gestures
   as a statechart, the way `spec/transport.md` did it.
2. **How long does the G-machine take to recalculate a few hundred
   cells?**  A number, measured before anything is drawn.
3. **Which grid first** — `.notes` as a grid (data already owned, no
   formulas) or `.gex` (formulas, no data yet)?  *Session's suggestion:
   `.notes`, because it decides whether a grid in this substrate is any
   good before a second format exists.*
4. **Where does time live** in a `.gex` that is a sequencer: a row per
   tick, or a `bpm`/`bars` record as `.notes` has?

## Shelved, 2026-09-07

**Henri:** *"And yup.  It needs the GUI framework.  I'd say.  Write the
cards into later/ shelf."*  Waits on an event: `card:gui-is-difficult.md`
reaching a framework this can be the first client of.  Sediment, not
debt.

## Added 2026-09-08 — which reference kinds a `.gex` formula has

*From `card:gui-is-difficult.md` Q7, after Coblenz et al., **Kale: A
Transformation-Safe Spreadsheet System** (arXiv 2608.26345, 2026-08-26)
and its source.  Henri: "gex-sheet voisi todella saada tuon kysymyksen
ja vastauksen siihen."*

**The question.**  A formula refers to cells; when rows are inserted,
sorted or moved, what does the reference mean — the *thing* that was
there, the *place*, or the *set* that matches?  Excel rewrites
references on structural change and Kale measured that people cannot
predict the rewrite (7 of 15 right); 50–83 % of Sheets users left a
broken formula behind on four of five risks.

**The answer, taken from Kale and one form further.**  A reference
declares its kind, and there are three:

| kind | Kale's spelling | means | under sort / insert / move |
|---|---|---|---|
| a thing | `Col[0]` | the row that is 0th *now*, held by identity | follows the row |
| a place | `Col[+1]` | the row one below the formula's own | stays an offset |
| a set | whole `Col`, or `Col[Experience > 10]` | every row that matches | re-runs |

No rectangle `B2:C3` — a place pretending to be a set.  Kale left the
query form unevaluated; here it is a Datafun `for` over the sheet's
rows (`spec/data.md`), which the tree already compiles, so the set kind
is the one gestate can do best and Kale could not.

**How Kale holds the thing kind, read from its source:** the id is the
grid's row-node id, session-scoped, never written to the file; the
formula's text is regenerated from the id after every change, so what
the person sees is `Col[5]` when the row is fifth.  For a `.gex` whose
truth is a text file the same trick is available only if the file
carries something stable — which is `card:gui-is-difficult.md` Q7's
question, and a `.gex` row may want a name column for exactly this.

