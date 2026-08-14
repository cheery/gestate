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

### Why the fader is soft — examined (same day)

`GESTATE_LOOP_TIME=1` now gives the loop the stopwatch the window
already had: `[loop]` lines with per-pass `act`/`furniture` cost, the
in-situ canvas walk, and — the number a hand feels — how far apart
canvas frames actually land.  What it showed corrects one §2/§4
number and explains the rest:

- **The window's `drawn` count is not the picture rate.**  The
  description carries the beat, so most "drawn" frames are status
  repaints.  True picture cadence, from `[loop]`: **settled ≈5.8 Hz**
  (frames 170–180 ms apart), **dragging ≈17.5 Hz** (57 ms apart).
  §2's "15–17 Hz" and §4's "16 Hz / 22 Hz" carried the same
  inflation; the `[loop]` gap is the honest number from here on.
- **The canvas walk in situ is not 9.4 ms.**  Settled it averages
  **72–83 ms**; during the drag **24–25 ms**.  Same code — and
  `furniture`, entirely unrelated code on the same loop, moved
  3.4 → 1.2 ms in the same runs.  One cause moves both:
- **The CPU governor.**  This fanless m3 under `powersave` idles at
  **0.7 GHz** and ramps to **~1.9 GHz** under load (read off
  `scaling_cur_freq`; ratio ≈2.7, matching both workloads).  A
  settled canvas *naps itself slow*: the loop sleeps `IDLE` between
  cheap passes, the core drops to 0.7 GHz, and every Python
  millisecond triples.  A dragging hand streams motion events, the
  loop holds `BUSY`, the core wakes, and the same walk runs 3× faster
  — **the drag is soft for two reasons that partly cancel**: the
  throttle (`CANVAS_SHARE=2` doubles whatever the walk costs →
  ~50 ms between pictures hot) plus one window frame (~17 ms), on a
  walk that even hot costs 25 ms in situ against 9.4 headless (the
  residual is `observe` plus GIL neighbours — housekeeping, notes —
  not separated by this measurement).
- The **first touch** of a settled canvas pays the cold clock: worst
  walks 112–137 ms in the reports, which is the moment a fader feels
  genuinely laggy rather than soft.
- This also explains §4's "palette starved less than recorded": a
  query typed into an animating canvas *stirs the loop itself*, so
  the walks between answers run at the hot clock.  The 2026-08-13
  number was likely measured colder, same mechanism, not a code
  improvement.

Nothing tuned yet.  If the softness is worth chasing: the honest
knobs are the throttle's floor (it currently doubles the *cold* cost
too), pacing `BUSY` while the canvas is showing (refused before as
core-burning — but a showing canvas is bounded time), or moving the
walk off the gesture loop.  Each is a design change; measured here,
decided elsewhere.

**Tried the same day: `BUSY` while the canvas shows.**  The loop now
holds the fast pace whenever the canvas is what is on screen (the
`pace` call's comment carries the argument).  Measured effect,
settled: walk 72–83 → **60 ms**, cadence 170–180 → **122–127 ms
apart** (≈5.8 → ≈8 Hz).  Real, and not the drag's 25 ms: 2 ms naps
between ~3 ms passes are a ~60 % duty cycle, and this governor wants
more sustained load than that — the drag's extra heat comes from the
*window thread* churning motion events in the same process, which the
loop cannot imitate by pacing alone.  Dragging is unchanged (~28 ms
walks, 67 ms apart, within run variance).  Cost of the change: ~500
wakeups/s while — and only while — a canvas is being watched.

### The third mask (2026-08-14, after the crust walk landed)

Henri: F103-untitled feels oddly laggy; lantern runs excellent.
Measured: the walked canvas costs **0.55 ms/frame flat** headless
(3000 frames, no drift — `examples/walktime.rs` is the tool) and
0.73–0.79 ms with clear+paint, F103 and lantern near identical.  In
the window both read 6.3–6.8 ms paint and the frame gap stretches to
22–23 ms (~43 Hz).  The clock, again: with the model's per-frame walk
retired the whole process is so light that the governor parks at
**500–600 MHz** — below even the 700 idle baseline — and every
millisecond triples.  F103 shows it because its animation is
continuous label motion, where ~43 Hz reads as judder; lantern hides
it because its visible motion is a 30 Hz meter and a fader that is
watched while dragging, and a drag heats the clock.

So the whole week's performance story is one sentence: **on this
governor, the cost of the work is set by how much other work there
is.**  The surgical fix, if wanted: `uclamp_min` on the window thread
(`sched_setattr`, unprivileged for own threads) — it names exactly
the mechanism, costs nothing when the machine is busy, and is the
one knob that is per-thread rather than system-wide.  Not done;
noted for the decision.

Separately measured on F103: the startup story is unchanged from §2
— canvas dark until the payload lands (the sound's clang holds the
side thread's fruits back ~10 s) and query→list 302 ms avg/952 worst
while compiling.  Known behaviour, now with a walked canvas in it.

**And the lever that landed: `CANVAS_SHARE` 2 → 1.**  Still
noticeably laggy at 8 Hz, and the stopwatch said why: the hold-off
*rest* after each walk was where the core cooled, so the throttle was
buying its own cost — resting a walk makes the next walk dearer.
Walking back-to-back (hold-off = the walk's own length, i.e. the next
walk starts as the hold-off expires):

| number | SHARE=2 | SHARE=1 |
|---|---|---|
| settled walk | 60 ms | **26–27 ms** |
| settled cadence | 122–127 ms (≈8 Hz) | **29.5 ms (≈34 Hz)** |
| dragging cadence | 57–67 ms (≈15–17 Hz) | **26–27 ms (≈38 Hz)** |
| query→list while animating | avg ~60, worst 64 ms | **avg 16–26, worst 51 ms** |

Nothing paid: a gesture always waited for the walk in progress — the
hold-off never shortened that bound — and a hot walk is a *shorter*
wait, which is why even the palette got faster.  What SHARE=1 spends
is one core, roughly pegged while — and only while — a canvas is
watched; on this fanless chip a long session may eventually thermal-
throttle, which would show up as the walk creeping back up.  The
constant keeps a `GESTATE_CANVAS_SHARE` override for measuring, and
the old worst case is unchanged: a 200 ms walk gave 200 ms gesture
gaps under either setting.
