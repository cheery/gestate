---
name: gestate-canvas-unwired
description: Canvas/substrate calls orphaned when audiopygame.py was deleted — observe and touch lost their only callers
metadata: 
  node_type: memory
  type: project
  originSessionId: aad11af2-b3a9-4a98-8596-6fc7e08c0490
  modified: 2026-08-12T15:49:18.813Z
---

When `audiopygame.py` was deleted (commit 71b90af, "vastly improved editor
coming", 2026-08-11), its frame loop went with it and `workbench.py` did not
pick up what that loop was calling.  Three separate holes, found 2026-08-12:

- **`Workbench.observe()` had no caller anywhere in the tree.**  So `peak`,
  `rms`, `position`, `band0..7`, `probe0..7` were never written into the
  canvas and every meter in `examples/audio` was frozen (`lantern.ges`).
  Old caller was `audiopygame.py:2533`.  **Fixed**: `workbench._canvas_frame`.
- **Nothing had *ever* ticked `events` in the editor** — `Substrate` had no
  tick method at all; only the standalone `gui.run` pygame window sent
  `("Tick",)`.  **Fixed**: `Substrate.tick` / `Workbench.tick`.
- **`touch` still has no caller** (now `AudioEditor.touch`,
  gestate/audioeditor.py:993 → `Substrate.touch`, gui.py:698) — canvas
  dragging is *not wired* in the Rust shell.  Confirmed 2026-08-12: it
  worked from the initial commit via audiopygame.py's event loop (click →
  `touch("press", x-inner)`, MOUSEMOTION → `"drag"`, BUTTONUP →
  `"release"`) and broke exactly at 71b90af when that file was deleted;
  the Rust shell (66d8fb0…d89cb3a) never carried it.
  `shell/editor/src/window.rs` mouse handling has no `on_canvas` branch
  (a press falls through to `keys::click`, moving the caret behind the
  canvas), `furniture.rs`'s `Gesture` has no Touch variant, and
  session.py's gesture verb table (~line 2760, `turn`/`note`/…) has no
  `touch` verb.  **FIXED 2026-08-12** at those three seams: `Gesture::Touch(&'static
  str, i32, i32)` in furniture.rs, `touching: Cell<bool>` +
  press/drag/release branches in window.rs (canvas branch AFTER
  palette/piano/tick/grab, matching pygame's chrome-first order;
  coordinates pass 1:1), `touch` verb in session.act.  Registered as
  fixme.md F101; post-mortem in journal.md "The canvas lost its hands";
  spec/workbench.md gesture list now carries touch.  Seam tests:
  test_session (verb→bench), test_audioeditor "canvas gets a hand"
  (verb→real substrate→channel).  Unverified inch: a real mouse in the
  real window (Rust branches are build+unit tested only).

Two facts that shape any canvas work:

- **`elapsed` does not advance on the canvas.**  It is `map … ticks` and
  `ticks` waits on `clock : Chan Int`, the *audio* clock, which nothing
  fires on the drawing side.  A canvas animates by folding over `events`.
- **A canvas frame is expensive**: ~38 ms `tick` + ~11 ms `picture` for
  `lantern.ges`, against the 2 ms `pace` sleeps while a hand is moving.
  Hence `CANVAS_SHARE` in `workbench.py` — hold the next frame off by twice
  the last one's cost, so an expensive canvas cannot starve gestures.
  Everything waits on `input` regardless of whether the program names
  `events`, because the entry defines `constSig v = mapSig (n => v) events`
  (`gui.py:_entry`) — so "does it listen?" is never a useful filter.

Separately: building `lantern.ges`'s canvas takes **~17 s** in `_compile`
(`assembled`), and that is pre-existing — identical on a clean HEAD
worktree.  Not investigated.

Root cause (five-whys with Henri, 2026-08-12): the rewrite was built to
spec/workbench.md, written in the same commit, whose gesture list
("flat and few") has eight verbs and no `touch` — the inventory was
drawn from the model's *published furniture* (knobs→turn, piano→note),
but a canvas touch target is declared inside the .ges program
(`onTouchY`), invisible to that method; the only records that the
canvas was an input device were the pygame view's event loop and
test_audiopygame.py, both deleted in 71b90af.  Component tests
(test_substrate.py) stayed green — the seam had no test, and nobody
dragged a canvas fader for a day.  Lesson: when deleting a frontend,
its tests are a conformance checklist; seam-level tests (gesture line →
channel moved) survive view rewrites, view-coupled tests don't.

The plugin's half (2026-08-12, same day): Panel/Canvas touch was already
well tested (`substrate_parity.rs` — press/grab/bridge on real exports),
but its fixtures were frozen bytes nobody compared with the living
exporter.  `test/test_panel_fixtures.py` now regenerates program/tags/
display/chans/bridge from current code and diffs — and caught F102 on
its first run (`_channel_names` leaking `voices`-expansion channels
into the canvas export; fixed by subtracting `banks_of`×`channels_of` +
`holds<Bank>`).  Subtlety: channel ids have two correct readings
(declarations-first vs program-order); the parity fixtures pin
program-order (`open()` forces `main` alone) — a display regenerator
must NOT pre-force declarations.  Canvas facts: pure `sin` works on
the canvas; `sine`/`tau` don't exist in the gui assembly at all.

Still open (Henri, 2026-08-12 evening): substrate _compile ~17 s, and
visible control lag while dragging (canvas tick ~38 ms/frame throttles
gesture pacing via CANVAS_SHARE) — next investigation.

Related: [[gestate-testing-standard]], [[gestate-editor-latency]],
[[test-what-a-person-would-do]]
