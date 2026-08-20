---
name: gestate-editor-latency
description: "The editor's one-behind typing bug and how it was found — idle windows must still present, plus the XTEST/GESTATE_EDITOR_TIME instruments"
metadata: 
  node_type: memory
  type: project
  originSessionId: 753ff05e-7489-4e11-b1c1-e5c873af5781
  modified: 2026-08-11T16:13:04.926Z
---

**When Henri reports the editor lagging, measure — do not reason about
it.** Six guesses were wrong before the measurement was right.

## The bug that was actually there (fixed 2026-08-11)

`baseview` waits on the X connection's fd to learn a key arrived.
`softbuffer` was handed the **same** connection, and its round trips
read that socket — moving queued events into XCB's own queue, where
they no longer wake the loop. A keystroke landing there waited for the
*next* keystroke's bytes: the letter on screen was the letter before the
one typed.

Invisible while the transport played (the beat changed the description
~60×/s, every frame presented, every present drained the queue) and
obvious after `stop`. **So `shell/editor` now presents every frame even
when clean** — skipping only the expensive half (layout + rasterise,
2–4 ms), keeping copy + present (~0.5 ms). Do not "optimise" that back
into an early return; the comment in `window.rs` `on_frame` explains why.

Decisive experiment: `GESTATE_EDITOR_STRESS=1` (never lets the picture
go clean) made the lag vanish. That is how the mechanism was pinned.

## Instruments

- `GESTATE_EDITOR_TIME=1` reports paint/copy/present, the loop period,
  **`key->pixels`** (event → the present that showed it; healthy ~10 ms)
  and **`query->list`** (a letter in the palette, out to the model and
  back; healthy ~20 ms).
- `tools/lagcheck.py <score> --stop` — types via XTEST and compares
  screenshots; exits non-zero if the last keystroke is not on screen.
  Needs a display, `libXtst`, ImageMagick `import` + `compare`.
- Keys inject through **ctypes** (`libX11.so.6` + `libXtst.so.6`); no
  xdotool on this machine. `xwininfo -root -tree` finds the `"gestate"`
  window; **click into it** — `XSetInputFocus` alone does not stick.

## Keyboard layout complaints: check the session type first

Henri runs **GNOME on Wayland**. GNOME owns the real layout; **Xwayland
keeps its own X keymap** for X11 clients and the two can silently
disagree — `gsettings get org.gnome.desktop.input-sources sources` said
`fi` while `xkbcomp -xkb :0 -` said `English (US)`. The editor is an X11
client under Xwayland, so it sees Xwayland's. No amount of work inside
`shell/editor` can fix a keymap that is already wrong upstream; the fix
is at the compositor (Henri removed the American layout).

**So run `echo $XDG_SESSION_TYPE` before diagnosing any input problem.**
Doing this the other way round cost ~300 lines of `keymap.rs` that was
written, verified, and then reverted, because it addressed a real but
different bug (baseview reads the keymap once at window open and never
again) that was not the one reported.

**Never run `setxkbmap` on Henri's machine.** A test did, to prove a
keymap change was followed; the `xkbcomp` restore silently failed and
left Xwayland on US — which is very likely what he was fighting. If it
must be repaired: `setxkbmap -display :0 fi,se -variant ,us_dvorak`
matches his GNOME sources. `GESTATE_EDITOR_KEYS=1` logs key/code/mods
per keystroke and answers layout questions without touching anything.

**Type *distinct* characters.** A burst of the same key cannot reveal a
one-behind bug — that is how the first test came back falsely clean.
And Henri's own typing steals focus from a test window, so injected keys
can land in his terminal instead; results during a live session can be
contaminated.

## Also fixed the same day

- `run`'s loop slept a flat 30 ms, about the gap between two keys, so
  the palette answered the previous letter. Now `pace()`: 2 ms busy,
  10 ms idle.
- The beat went out at 3 decimals, so the description differed every
  tick and forced a repaint for a digit nothing draws. Now 1 decimal.
- Closing the palette sent no gesture, so `session.filtered` stayed
  stuck at the last query.
- The palette's summary line was drawn *below* the panel, over the file
  — a panel over a document owns every pixel it writes on.

Cleared by measurement, so don't re-suspect them: key delivery (0.7 ms
at every speed), dropped keys (none), rollover typing, and rope
fragmentation (5 µs/insert, flat over 10 000 keystrokes — guarded by
`shell/editor/tests/pace.rs`).
