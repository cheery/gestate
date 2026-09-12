# gex-sheet — gestate's own spreadsheet, and the sequencer that is one

    status   doing — 2026-09-12.  Off the shelf the same day, the
             textbox decided and `.notes` the first grid
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
             card:gui-is-difficult.md §"The whole notes GUI in one
             `.ges` file" — what waits on *this*, since 2026-09-12:
             the sheet is the client that tests the seams first
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

## Added 2026-09-10 — the schema travels in the file, and a sheet is kinds, not cells

*From `card:relational-model.md`, the evening it was continued.  Henri:
"I'd want this to be extended to card:gex-sheet.md and in that case the
.gex could carry the schema along it, so that .gex files can stand on
their own."  Then: "yes. write it to both cards."*

**The rule, and why it flips here.**  `card:relational-model.md`
argued that a `.notes` keeps its declaration in `gestate/notes.ges`,
the catalog, because every piece's notes have the same kinds and a
copy in thirty pieces is one fact stored thirty times.  A sheet has no
shipped schema at all: its columns are the user's, so each sheet is
its own schema by nature and the declaration has nowhere else to live.
Practice split on exactly this line — a database keeps the schema
once because it is one system with one schema; Avro puts the schema
in every file because the files cross systems that share nothing;
SQLite's argument for itself as an application file format is the
one he is making.  So: **the schema travels in the file when it is
the document's own, and in the catalog when it is shared.**  `.notes`
stays on the catalog and `.gex` carries its own, by the same rule.

**The form.**  Codd's fourth rule: the catalog is itself relations,
in the same form as the data, queryable by the same language.
Datomic did it literally — an attribute is an entity with ident, value
type and cardinality, transacted as datoms like any other fact, and
only the schema of the schema is fixed.  Here a `.gex` carries its
declaration as record lines in its own grammar,

    kind   row      key name
    field  row  name    Word    Must
    field  row  price   Number  Must
    field  row  total   Formula May

with `kind` and `field` the two bootstrap kinds `facts.ges` fixes.
Nothing new in the language for a document to describe itself, which
is the reason `facts.ges` already gives for a kind being a value.
`Formula` as a value form is a placeholder: a formula column is a
derived field, and its type is the G-machine's to infer or check.

**What it does to Q1.**  Q1 says the model is *a relation from
address to expression*.  Read relationally that is the
entity-attribute-value shape — row, column, value — which
`card:relational-model.md` scar 7 refuses: it defeats the types, the
checks and the eye.  The relational form of a sheet is what Kale
arrived at and what Excel's table objects are: **a sheet is one or
more kinds, a row is a record, a column is a field, and a formula
column is a derived field, which is a view.**  The schema in the file
is precisely those column declarations, and it is what makes the
sheet a relation rather than a cell grid.  The thing, place and set
references of the 2026-09-08 section sit on top of this unchanged: a
thing is a record by key, a place is an offset among records in
declared order, a set is a `for` over the kind.  So Q1's first
sentence is corrected here, and its invariants stand — *every value
derivable from the file alone* now includes the schema.

**Three things to keep straight.**

- *The schema travels; the vocabulary may not.*  The 2026-09-09 lean
  is that a cell holds its expression and the `.ges` beside supplies
  what it calls.  A sheet using only the prelude stands on its own; a
  sheet calling a piece's instruments does not, and carrying the
  schema does not change that.  Two dependencies, and the file
  carries one.
- *Scar 6 inverts.*  Per-file schema means every sheet is its own
  schema version and evolution is per document — fine for a sheet,
  whose reader handles any columns anyway, and exactly why it would be
  wrong for `.notes`.
- *One decision it creates.*  His 2026-09-09 call was that kinds live
  in the `.ges` beside the document, so one document has one
  declaration and nothing can disagree.  Schema-as-records is a
  second road for the same document type.  *Default:* a document's
  declaration is either carried or beside, never both, and the parser
  refuses a file that has both — one line.  *Trigger:* the first
  `.gex` parsed.  This is the only place the two cards conflict.


## Off the shelf — 2026-09-12, the textbox decided

**Henri:** *"Let's start looking at how gex sheets would be
implemented.  I think they have one challenge prep for us: they need
a textbox or text input."*  Then, of the three readings below: *"B.
yes.  .notes as the first grid."*  And: *"begin.  This looks like a
good situation."*

**What the tree already had for the text input**, measured before
the readings were shaped.  The Rust editor has the half of a text
editor nobody writes twice — a rope, a caret that keeps its column,
undo, clipboard, a monospaced bitmap font with every character this
repository uses (`shell/editor/src/keys.rs`, `document.rs`,
`font.rs`).  The palette already asks for a command's argument as
typed text and returns it as a command with its arguments
(`shell/editor/src/palette.rs`, `Asks::Wants`).  And the substrate's
refusal of a text editor — *the language cannot measure text* — is
narrower than it sounds: both hosts agree on a monospaced cell, and a
caret in a monospaced font is the same arithmetic that admits a label.
What the substrate lacks is a `Text` constructor in the editor's font
(the label font is 3×5, uppercase) and any `Key` reaching a canvas.

**The three readings, and his choice.**

| | the textbox is | cost |
|---|---|---|
| A | the file's own text view; a press on a cell puts the caret on that token | nothing; the person then looks at text, not a grid |
| **B — chosen** | the window's one line editor, drawn where the canvas asks, its result one command line (`field …`) | one furniture verb; the substrate unchanged |
| C | a monospaced `Text` in the substrate, the edit buffer a signal over `Key` events, the editing state a chart | a constructor in both machines, the editor font in the walk, key delivery to the canvas |

*Trigger to revisit B:* the first cell that must be drawn differently
while it is typed in, or the browser tab needing the sheet.

**A cell is a span of source.**  Every field value in the record
format is one whitespace-free token, and `spec/editor.md`'s literal
rule says a widget is a view over a span of source and dragging it is
a text edit.  A cell edit is that rule on a record line instead of a
`.ges` declaration; the verbs are `assert` and `retract`, and setting
one field is `notes.retune`, which transpose and move already use.
The textbox is the last piece, not the first.

**Readiness, checked in the code the same day.**  Ready: the kinds
(`gestate/notes.ges`), the canonical parser and writer, `assert` and
`retract` as commands, a label whose text is computed in the program
(`rollNum`), a meaning per element and the window's hit walk, the
headless press harness in `test/test_drawnscores.py`, the palette's
argument mode, one canvas per `canvas <line> <key>` furniture line,
and the bench.  Missing, in build order:

1. **The grid program** — `gestate/grid.ges`, a library from the
   start: rows from the rows channel, a column per declared field, a
   label per cell, a meaning per cell.  The number to watch: a full
   piece is ~800 labels, each glyph blits where a note was one
   rectangle.
2. **A `field` command** — one line in `command.ges` over `retune`;
   a cell edit is then one transcript line, `field <region> <voice>
   <tick> <key> <name> <value>`, transpose's address with a field.
3. **One furniture verb, model to window: `ask <verb> <args…>`** —
   the palette asks for an argument today only when the window opens
   it; a press on a cell must make the model open it, pre-filled.
   The one thing that touches the window; break its build on purpose
   once before trusting it.

*In the first slice the typed field opens where the palette lives,
not at the cell's rectangle* — the cheapest honest B, exercising the
whole road from press to command to file to redraw.  Moving the field
onto the cell is a later slice, taken only if the grid earns it.

### Slice 1, built — 2026-09-12: the grid, the press, and `field`

*Henri: "begin.  This looks like a good situation."*  Headless, on
`arc.notes`, the road from a press to a command to the file to the
picture; the window's half — the `ask` verb — is slice 2.

| built | where |
|---|---|
| the drawing, a library from the first day: rows cut from a flat reading, a cell a `Meaning` over a tile and a label, the head, alternate rows a shade apart, the selected cell lit | `gestate/grid.ges` |
| the host half: the per-file program (channels, the file's word table, a case table per bounded field, widths and heads, one picture lifted over rows and selection), the reading, the regions, the record's key from a row | `gestate/gridbox.py` |
| the prelude door: a program declaring a rows channel gets `grid.ges` after `roll.ges` | `audio.has_grid`, `preludes` |
| `assigned` — one field of one record by key, read back through the parser, the spelling dropped with a set key, a doubled key refused | `notes.assigned` |
| **`field <region> <key> <name> <value>`**, and `grid` / `roll` to choose the canvas view's picture | `command.ges`, `session.do_field`, `do_grid`, `do_roll` |
| a press on a cell names the line and the field, the selection outliving it on the box's `sel` channel | `session._grid_touched`, `grid_cell` |
| the bench: `grid_view` grows the page's one program by the grid's box, the canvas view takes its entry, the rows cross as a trace beside the roll's | `audioeditor._load_substrate`, `grid_regions` |
| the tests — eleven, under *the first sheet* | `test/test_gridsheet.py` |

**Measured on the reference machine, `arc.notes`, 291 notes × 9
fields:**

| | |
|---|---|
| the program's text | 1,869 chars — the kind's columns and the file's words; the rows are a reading |
| compiled once | 0.99 s |
| the first picture | **5.9 s**, 5,257 items, 2,619 cells with a meaning |
| the program after a value edit | byte-identical; the reading differs in one number |
| a press aimed by the host's arithmetic | answered by the picture with the cell's own meaning, three corners tried |

**The 5.9 s is the Python interpreter's cost per item** — 1.1 ms an
item, where the roll's first picture is 366 ms for 248 items, 1.5 ms —
and it is the number a headless test pays, not the one a person sees:
the window walks the program in Rust.  **That number is not measured
here** and it is the next one that matters, because a grid of a whole
piece is ten times the roll's items.  It takes a driven run
(`tools/driven.py`), which takes his screen.  If the Rust walk is slow
too, the answer is the one every grid has — draw the rows in the
window and no more, the scroll offset arriving as a channel — and it
is a slice, not a rewrite: the library's `gridRows` takes a first row
and a count today in all but name.

**What the first slice does not do, said now:** nothing opens the
textbox — a press selects and says the value, and `field` is typed in
the palette by hand; the `ask` furniture verb that opens the palette
pre-filled from a press is slice 2, the one thing that touches the
window.  Only the `note` kind is a grid; `section` and `bpm` lines
are edited as text.  A new word in the file — a spelling it has not
used — is a new program, once, and the card says so where the word
table is written.  Labels are the chrome font, 3×5 and uppercase, so
`melody` reads `MELODY`; a grid in the editor's own font is reading C
of the textbox question and is not taken.
