# snap-grid — a control for the grid a note snaps to

    status   open — 2026-09-23
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

## The postcondition

Not written yet — it is the first thing the card's day owes, before
anything is built (`board/README.md` §"The postcondition").
