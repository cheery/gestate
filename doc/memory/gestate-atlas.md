---
name: gestate-atlas
description: "The five generated A3 architecture sheets (doc/atlas/) — what each derives, the two wire poka-yokes, the stamp rule, and that the set is CLOSED at five"
metadata: 
  node_type: memory
  type: project
  originSessionId: 14ee1763-056a-4a3b-a7f9-bfd346e03708
  modified: 2026-08-16T05:45:59.979Z
---

**`python -m gestate.atlas` → `doc/atlas/*.svg` (+ `.png`, gitignored).**
Built 2026-08-16. Five A3 sheets, generated from the tree; `test_atlas.py`
(24 tests) fails when a committed sheet is not what the source renders —
same guarantee and same sentence as `doc/ref/`.

**The five**: `whole` (modules/lanes/imports), `language` (front end in
`pipeline._analyse`'s own call order, homes through aliases, refusals
followed two hops, `_DISPATCH` instruction set), `wire` (editor seam),
`sound` (formers/primitives/IR kinds + C host seam), `score`
(`music.ges` signatures grouped by what you're doing).

**Two poka-yokes — the real payoff.** `wire_drift()` compares `abi.rs`↔
`editor.py` (names, arity, types), `session.furniture`↔`Furniture::read`,
`Editor.order`↔`Order::read`, `Gesture::line`↔`session.act`.
`host_drift()` compares `host.c`↔`audiohost`, ASYMMETRICALLY: Python
naming a C function that is missing = fail; C having more = fact (host.c
calls itself, e.g. `gestate_host_halt`→`gestate_host_unblock`).
**Three tests exist only to prove the checkers can fail** — a pattern
that stops matching returns an empty set and reads as a guarantee.

**The stamp rule** (Henri asked, since sheets get shared): each sheet
carries `gestate <commit> · <date>` (+ `+` if the tree was dirty), and
`stale()` IGNORES the stamp via `_unstamped()`. Otherwise every commit
anywhere would demand a redraw. Sheets always name the commit *before*
the one carrying them — the fixed point, and correct.

**CLOSED AT FIVE** (Henri, 2026-08-16: "This is enough… the remaining
could turn out noise"). A sixth needs a caller; "the set would be
complete" is not one.

Hand-written halves that a new thing must be added to or the test fails:
`WHERE` (module→lane), `SPINE` (arrows + the import proving each),
`PASSES` (order checked against the code), `ABI_SAYS`, `MUSIC_WORDS`.

Rasteriser chain: cairosvg (pip, ~1 s, in `tools/toolbox.sh`) →
rsvg-convert → resvg → inkscape (2.5 s, a whole app).
