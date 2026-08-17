# interface-oracle — nothing checks what the window says

    status   open
    because  "So interface needs an oracle" — three interface changes
             shipped in one evening and nothing in the tree records what
             the window used to do, so every claim about it rests on
             screenshots one session took by hand and will never take
             again
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    see      manifesto.md §"The instruments, and what each cannot see"
             shell/editor/src/view.rs — the frame builders, and the gap
             board/button.md — where the need was found
             fixme.md F150, F151, F153 — the three that shipped unheld
             spec/verification.md §"The screen is an oracle"

## The ask

> So interface needs an oracle.

Out of the evening's kaizen: the golden `.samples` protect the sound,
the example rosters protect the corpus, the transcripts protect a
handful of replayed sessions — **and the interface has nothing.**

## Found by looking, before it was taken

**Three interface changes shipped on 2026-08-17 and none is held by a
test.**  The starter's text (F150), the `sound behind · audition
Ctrl-Return` readout (F151), and the `Ctrl-K` hint's inverted default
(F153).  What proves each of them today is a screenshot a session took
by hand, described in a commit body, and deleted.  Change any of the
three tomorrow and 2,595 passing tests will agree with you.

### The cheap half already exists, and one module is missing it

`view.rs` draws by **building a display list** — `burger_frame`,
`chrome_only`, `bar_rows`, `frame`, `peep_frame` are functions of a
`View`, a `Font` and the `Furniture`, returning `Frame { items }`.  No
window, no display, no pixels.  Asserting on that list is an ordinary
unit test:

> the bar contains a run reading `Ctrl-K` when the key has not been
> used, and does not once it has

**And the gap is exact**: `palette.rs`, `walk.rs`, `font.rs`,
`furniture.rs` and `shapes.rs` all carry `#[cfg(test)]` blocks.
`view.rs` — the module that decides what a person sees — carries none.
It is the largest drawing file in the crate and the only untested one.

### Two layers, and the second is the one that cannot be automated

| | catches | cannot catch |
|---|---|---|
| **the display list** | a run that stopped being emitted, a colour that changed, a readout that moved | whether the result is *legible* — the burger was correct in the list and 2.3:1 on screen |
| **the photograph** | what a person actually sees | anything nobody points it at, and anything that looks right for the wrong reason |

The second row is already in `manifesto.md`'s instrument table, added
the same day.  What this card adds is the first row, which is free and
runs in the suite, and the honest note that it does **not** replace the
photograph: F150's whole defect — 24 lit pixels of `FAINT` on `BG` —
would pass every display-list assertion anybody would think to write,
because the glyph *was* being emitted, in the colour it was asked for.

## Questions

1. **Where do the assertions live — Rust or Python?**  The display list
   is Rust's, so `#[cfg(test)]` in `view.rs` is the direct route and
   needs no window.  But every *other* interface claim in this tree is
   already Python-side (`furniture()` rows, `test_desktop.py`,
   `test_starter_and_first_command.py`), and a reader looking for
   "what does the window say" would find those first.  Two homes is how
   a check gets written twice and believed once.

2. **Does a golden frame belong in the tree?**  A committed display
   list for one window size would catch *everything* at once rather
   than one assertion at a time — and `doc/atlas/*.png` is the standing
   argument against committed renderings.  A display list is text, so
   the argument may not carry; that is the question.

3. **What is the first thing it should hold?**  Suggested: the three
   from tonight, because they are fresh, they are small, and one of
   them (the hint) is a *default* that a future session would flip back
   without noticing.

## What the work is

1. Answer 1 and 2 — they decide the shape.
2. `#[cfg(test)]` in `view.rs`, starting with tonight's three.
3. A line in `manifesto.md`'s instrument table for the display list,
   **with its blind spot**: it sees what was emitted, never what it
   looked like.
4. Say in `board/done/button.md` that the corner is now held, once it is —
   that card's remaining answers all change what `view.rs` draws.
