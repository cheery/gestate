# snap-grid — a control for the grid a note snaps to

    status   doing — 2026-09-24
    because  "itseasiassa mitä haluaisin olisi jokin nappi jolla ohjata
             ruudukon snap-väliä.  Esim. nyt kaikki on
             neljäsosanuotteja, jos haluaisin luoda
             kahdeksasosanuotteja, se ei onnistuisi." — Henri,
             2026-09-23, the evening `card:notes-editor.md` closed.
    asked    Henri, 2026-09-23 — "jatketaan huomenna"
    see      gestate/scorebox.py — `grid_of`, `GRID_MIN`: the grid is read
             off the roll's own events, never declared
             card:notes-editor.md — where the grid snap came from

## What is there today

The grid is **derived, not chosen**: `scorebox.grid_of` takes the
largest tick that divides every onset and length in the roll, floored at
`GRID_MIN` (a thirty-second).  Henri, 2026-09-06: *"allow grid snap"* —
and the reason it was read off the events is written beside it: a `.ges`
score has no section record to declare a subdivision in.  So a piece
written in quarters snaps in quarters, and a note made by two clicks is
one grid step long: there is no way to reach an eighth on it.

## Where it goes — Henri, 2026-09-23, evening

*"Se saisi olla vasemmassa yläkulmassa oleva työkalupalkki, mutta en ole
varma minkälainen sen pitäisi olla."*  So: a toolbar at the top left of
the page; its form is open and his.  What the session owes before
anything is built is a few shapes of it to choose between — drawn, not
described — since the choice is a feel and a feel is judged by eye.

## Decided — Henri, 2026-09-24

Four shapes drawn over the real page (arc.notes, the handlag run of
2026-09-23): a row of values, one word that steps, the rhythm drawn,
one word that opens a list.

* **The shape: C, the rhythm drawn** — each button a beat cut as the
  grid cuts it, no numbers.  *"C is appearing neatest there."*
* **`auto` stays**, and is where a bar starts.  *"'auto' is good."*
* **Triplets are in.**  *"yup, triplets are good."*
* **Where it lives: the bar, in the file.**  *"Maybe the grid should be
  a property of the bars themselves, eg. "section A bar 1 grid 1/8""* —
  and of three readings (on the section; a sparse bar record; both),
  *"sparse bar record."*  A bar with no record is `auto`: the roll's
  grid, read off its notes as before.  *(The session first said "that
  bar's own notes", and took it back the same hour: a bar where only
  the long voices begin would snap to whole notes.)*  The session's reading of why this is not what
  `spec/drawnscores.md` §"What is deliberately not here" refused: that
  was bar lines as musical *objects* — repeats, endings — and this is a
  property a bar carries.
* **Which bar a press sets:** *"the last clicked/edited bar would be
  what is modified."*
* **Spelled** as a fraction of a whole note, so a triplet needs no
  sign: `1/4 1/8 1/16 1/32`, `1/12 1/24` — the session's default, never
  read by him in the file since C draws it.

## The postcondition

**A bar can be told its grid, and making, moving and lengthening notes
in that bar snaps to it; a bar told nothing snaps as it did before.**
Written 2026-09-24 before anything was built, from the `because`: a
piece in quarters can be given an eighth.

## Built — 2026-09-24

Four slices, each with its tests seen failing first; `test/test_snapgrid.py`,
30 tests.

1. **The record** (`e9acb50`) — `bar  section A  bar 2  grid 1/8`,
   declared in `notes.ges`, refused where a note would be, written at
   the head of its bar; `spec/drawnscores.md` §"A bar's grid".
2. **The snap reads it** (`aae9cb8`) — making, moving and lengthening a
   note in that bar go by its grid; a bar told nothing snaps as before.
   On his piece, two clicks aimed at an eighth had made `at 96 len 96`.
3. **The verb** (`e74a86b`) — `snap A 2 1/8`, `auto` to take it back;
   named `snap` because `grid` is the sheet view's.  The session keeps
   the bar last pressed or moved into.
4. **Toolbar C** (`4cb9136`) — above the page's sections, a press runs
   `snap` on that bar, the lit button is read off the file.  The page's
   own walk found a defect the session tests could not: the first box's
   reach lies under the toolbar, so a button's press also landed on a
   bar and moved the one it tells.  A bar is now remembered only once a
   press is the box's own.

**Not seen yet: the picture.**  No driven window was started (F241);
the toolbar's look and feel is his hands' — the check notes-editor
closed on.
