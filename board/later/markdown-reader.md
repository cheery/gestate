# markdown-reader — the tree's own dialect, read and travelled inside the window

    status   shelved — 2026-09-07
    because  "for markdown that's actually used here, the dialect we
             talk in all the time here." — Henri, 2026-09-07, choosing
             it over a markdown implementation; the workbench opens
             `.md` inert today and the tree is seventy documents in one
             house style, its board, specs, journal and memory
    asked    Henri, 2026-09-07 — "Write the cards into later/ shelf."
    see      card:gui-is-difficult.md — what this waits on
             card:gemba.md — `at <path> <line>` already travels from
             outside the window; this is travel from inside
             test/test_citations.py, tools/backlinks.py — the dialect's
             citations already parsed: `card:` names, §"…" quotes,
             F-numbers, `[[name]]` links
             doc/memory/the-tree-withers.md — a living document has a
             source and a check; a reader is a second reader of the same
             source, held to the first
             vision.md §"Gestate as a generic working platform" — "a
             visual system along the text", and the tension it names:
             the ease of use is preferred

## What this is, what it is not, and when it runs

**A reader for the markdown this tree writes** — headings, bold
lead-ins, lists with italic attributions, tables, code fences, and the
four citation forms — in the workbench, on the substrate, with the
citations followed: caret on `card:transport-modes.md`, and the window
opens it on whichever shelf it is on.  It is **not** CommonMark:
hundreds of edge cases for a corpus that uses none of them, and a
second renderer that disagrees with the first on documents that are
suite gates is a second source of truth.

## Measured against the tree, 2026-09-07 — the session's reading

| exists | where |
|---|---|
| the citations parsed and resolved | `test/test_citations.py`, `tools/backlinks.py`, `test/test_memory.py` |
| travel to a file and line, from outside | `gestate/gemba.py` `at` |
| `.md` opened in the window, inert | `Workbench.inert`, `INERT` |
| a rendered page | **nothing** |
| follow-the-citation from the caret | **nothing** |

## What would kill it

**Building the renderer first.**  The value is travel, not typography:
a reader that draws the page and cannot follow a `card:` to its shelf
has done the cheap half.  So: follow-the-citation over raw text first,
the picture second.

## Questions — day one, when it wakes

1. **Which citation forms, exactly**, and is the list the checker's
   own?  One parser for the reader and the gate, or the reader drifts.
2. **Travel first, then draw?**  *Session's default: yes* — a `follow`
   command from the caret, replayable in a transcript, before a line of
   rendering.
3. **What is the model** — a document is a list of blocks; which
   blocks does the house style actually use?  Counted over the seventy
   files, not guessed.

## Shelved, 2026-09-07

**Henri:** *"And yup.  It needs the GUI framework.  I'd say.  Write the
cards into later/ shelf."*  Waits on `card:gui-is-difficult.md`.  The
travel half needs no framework and could be pulled earlier if he says
so; the rendering half waits.
