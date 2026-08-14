# Editor and canvas performance — the baseline before content boxes

Measured **2026-08-13**, at commit `13c6f6e`, before any content-box
work.  The point of this file: the numbers below are what the editor
does *today*, so any change that makes them worse is a regression we
can name.  Re-measure with the same harnesses before and after
anything that touches the frame path.

## Machine and conditions

- Intel Core m3-8100Y (fanless), 4 cores, `powersave` governor, 7.6 GiB
- Linux 6.8.0-137, GNOME on Wayland; the editor is an X11 client under
  Xwayland (`DISPLAY=:0`)
- Python 3.12.3, rustc 1.97.1; `libgestate_editor.so` prebuilt (no
  cargo build inside any measured run)
- Machine otherwise idle — measured *after* the full test suite
  finished and cooled down.  On this fanless chip a busy core throttles
  everything, so numbers taken under load are not comparable to these.

## How to reproduce

    python tools/measure_canvas.py            # headless, model side
    python tools/measure_editor.py idle   examples/audio/twoknobs.ges
    python tools/measure_editor.py typing examples/audio/twoknobs.ges
    python tools/measure_editor.py palette examples/audio/twoknobs.ges
    python tools/measure_editor.py canvas-settled examples/audio/lantern.ges

`measure_editor.py` drives the real window over XTEST (the
`lagcheck.py` machinery) with `GESTATE_EDITOR_TIME=1` and prints the
`[editor]` reports.  **Hands off the keyboard while it runs** — your
own typing steals focus and contaminates key→pixels.

## 1. The canvas, headless (model side)

What `workbench._canvas_frame` pays per frame: `tick()` +
`picture()` + `_shapes()` serialization, over 120 frames after warmup.
No transport, so `observe()` is absent — this is the floor.

| example | lines | compile cold | compile warm | tick | picture | `_shapes` | frame avg | unthrottled | items / wire bytes |
|---|---|---|---|---|---|---|---|---|---|
| substrate.ges | 96 | 1.54 s | 112 ms | 2.62 ms | 0.20 ms | 0.01 ms | **2.83 ms** | 353 fps | 3 / 84 B |
| envelope.ges | 189 | 1.10 s | 136 ms | 2.88 ms | 12.73 ms | 0.09 ms | **15.70 ms** | 64 fps | 43 / 1182 B |
| spectrum.ges | 151 | 0.83 s | 134 ms | 4.18 ms | 7.87 ms | 0.04 ms | **12.09 ms** | 83 fps | 16 / 451 B |
| lantern.ges | 273 | 5.54 s | 1.25 s | 7.16 ms | 2.21 ms | 0.04 ms | **9.40 ms** | 106 fps | 17 / 492 B |

Notes:

- **Compile cold vs warm**: the first `Substrate()` in a process pays
  imports and the prelude; later builds (what a `Ctrl-S` rebuild pays)
  are the warm number.  Both are "canvas compile time" — cold is what
  opening a file costs, warm is what an edit costs.
- The cost is the G-machine walking the substrate, and it is the
  *program's*: envelope's cost is in `picture` (43 items), lantern's in
  `tick`.  `_shapes` serialization is noise (≤0.1 ms) at these picture
  sizes — the wire is not the cost, the walk is.
- With `CANVAS_SHARE = 2`, the editor holds the next frame off by twice
  the last one's cost, so the in-editor ceiling is roughly half the
  unthrottled rate (e.g. lantern ~53 fps ceiling; measured in-editor
  update rate is lower still, see below, because the loop also polls,
  observes and paces).
- One outlier seen: spectrum's worst `picture` was 141 ms in one frame
  (GC or a late allocation); its median is 6 ms.  Medians are the
  comparable number.

## 2. The editor window (view side)

From `GESTATE_EDITOR_TIME=1` reports, one scenario per process.
Reports come every 240 frames; the loop runs ~50–60 Hz (asks every
16.5–21.4 ms).

**Read the reports knowing this accounting trap**: `paint` is divided
by *drawn* frames, but the bucket also collects
`surface.buffer_mut()` (~0.5–1 ms, paid every frame, drawn or idle).
A window with few drawn frames therefore shows an inflated "paint" —
`0 drawn … paint 226ms` means ~0.94 ms/frame of buffer acquisition
across 240 idle frames, not a 226 ms paint.  Only compare windows with
many drawn frames.

Steady state, source view, transport running (`twoknobs.ges`,
~100 drawn per 240-frame window):

| number | value |
|---|---|
| paint per drawn frame | **9–11 ms** |
| copy | 1.2–1.4 ms |
| present | 0.03 ms |
| **key→pixels** (25 strikes, typing at ~10 cps) | **avg 16.2 ms, worst 25.3 ms** |
| **query→list** (palette, 11 answers) | **avg 11.1 ms, worst 15.5 ms** |

Canvas view, steady state (instrument startup finished):

| example | picture updates | paint per drawn frame | query→list while animating |
|---|---|---|---|
| substrate.ges | ~100–149 / 240 frames (≈25–37 Hz) | 4.5–10.4 ms | avg 17.6 ms, worst 28.9 ms |
| lantern.ges | 62–69 / 240 frames (≈15–17 Hz) | 6.0–7.8 ms | avg 136 ms, worst 386 ms |

- The view-side paint of the canvas is *cheap* (a handful of shapes
  through the shared painter); the update rate is bounded by the model
  side (§1) plus the loop's pacing, which is the design
  (`CANVAS_SHARE`).
- **An expensive canvas starves the palette**: lantern's ~10 ms of
  G-machine per frame sits on the same Python loop that answers
  `filter`, so query→list degrades an order of magnitude while it
  animates.  That is today's behaviour, recorded so it at least does
  not get *worse* — and it is the number to watch when B2 boxes put
  more substrate programs on the same loop.

During instrument startup (in-process clang/LLVM compiling the synth,
all cores busy): query→list was seen at avg 266–599 ms, worst
**1037 ms**, and paints stutter for the several seconds the compile
runs.  Also today's behaviour, also a bar not to sink under.

## 3. What must not regress (the short list)

Content boxes touch layout, scroll, hit-testing and the description.
After the slots-table refactor and each B-stage, re-run and hold:

1. **key→pixels avg ≤ ~16 ms, worst ≤ ~25 ms** (typing, source view).
2. **paint per drawn frame ≤ ~11 ms** in the source view with a
   transport running — the slots walk replaces `i × ch` arithmetic and
   must stay invisible at this scale.
3. **query→list ≤ ~18 ms** steady state (source or cheap canvas).
4. Headless canvas frame times within §1's medians (boxes reuse the
   same machinery; B2 adds *more* pictures on the same loop, so the
   per-picture cost must not grow).
5. Rope editing already guarded by `shell/editor/tests/pace.rs`
   (~5 µs/insert, flat over 10k keystrokes) — keep that test green.

The known soft spots, so they are not rediscovered as regressions:
palette latency under an expensive canvas or a startup compile (§2),
and the report's paint/drawn denominator (§2, first note).

## 4. Re-measured 2026-08-14 — the lantern canvas, and a hand on its fader

The roadmap's "lagcheck the lantern canvas": whether §1–2 still hold
after the week's work (slots table, bar growth, burger, inert mode),
and the number §2 never had — what a hand on a knob feels like while
the canvas draws.  Same machine, same harnesses; two scenarios grew in
`measure_editor.py` for it (`canvas-palette`, `canvas-drag`).

| number | 2026-08-13 | today |
|---|---|---|
| lantern headless frame avg | 9.40 ms | **9.41 ms** |
| lantern in-editor updates, settled | 62–69 / 240 (≈15–17 Hz) | **70–73 / 240 (≈16 Hz)** |
| paint per drawn frame, settled | 6.0–7.8 ms | **7.5–7.7 ms** |
| query→list while animating | avg 136 ms, worst 386 ms | **avg ~60 ms, worst 64 ms** |

- **The prediction holds.**  Model-bound at ~9.4 ms/frame headless to
  the second decimal, ~16 Hz in-editor; nothing this week touched the
  canvas path's cost.  (Envelope's headless frame read 18.2 ms against
  13.7–15.7 recorded — its cost is `picture`, the most
  allocation-heavy walk, and this fanless chip's governor moves such
  numbers; lantern, the one under test, did not move.)
- **The palette is starved less than recorded.**  Only 2–6 answers per
  run land while animating, so the sample is small — but the worst
  today (64 ms) is under half the recorded *average*.  Not traced to a
  cause; recorded so the next measurement has both points.
- **A hand on the fader** (`canvas-drag`: saw the WARMTH fader over
  XTEST for 10 s while the piece plays): the drag *raises* the update
  rate to **89–91 / 240 (≈22 Hz)**, paint 3.5–3.8 ms — motion keeps
  the loop on its fast pace, so the handle trails the finger by one to
  two picture periods, **~45–90 ms**.  Felt, that is a slightly soft
  fader, not a laggy one.  The harness screenshots both saw extremes;
  the handle stands at the finger's stop in each, fill running the
  right way — the affordance, verified from outside.
