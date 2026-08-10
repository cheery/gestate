<p align="center">
  <img src="doc/gestate.svg" width="200" alt="gestate — a signal carried to term">
</p>

<h1 align="center">gestate</h1>

<p align="center"><em>A language for programs that develop while they are already alive.</em></p>

Gestate is a small functional language for sound, music and moving
pictures.  A program is a handful of signal declarations; the compiler
checks them into a **static graph** — fixed memory, bounded work per
sample, no allocation after the first instant — and runs it native
through LLVM.  Because the graph is exactly what the source says, an
edit while the program plays **migrates the running state**: the
oscillator keeps its phase and the filter its memory while the sound
changes under your hands.  That is the logo, and the name.

```
env : Sig Float
env = perc 6.0 (gateOn (!(x => x < 0.5) (phase 2.0)))

sound : Sig Float
sound = 0.4 * sine 220.0 * env
```

`!` lifts an ordinary function over signals; everything else is
functions and values.  Scores, polyphonic voice banks, MIDI in, a tape
echo you can gate, and a canvas the same program draws on are all
library and language, documented down to the measured decibel.

## Hear it

```sh
python -m gestate.audioperform examples/super/dubgate.ges      # live, editable
python -m gestate.audioperform examples/super/dubgate.ges -o dub.wav --seconds 16
python -m pytest                                            # the suite
```

Try `examples/audio/violin.ges` for a concert soloist lost in a sound
system, or anything under `examples/beginner/` beside its lesson.

## Read it

* **[The beginner course](doc/beginner.md)** — ten lessons from a sine
  to a piece; `doc/intermediate.md`, `doc/advanced.md` and
  `doc/super.md` continue it.
* **[The manual](doc/manual.md)** — the language, plainly.
* **[The reference](doc/ref/index.md)** — every name in every library,
  generated from the sources so it cannot drift.
* **[The specs](spec/)** — how each part is designed and why, costs
  stated; `journal.md` is the honest running account, `fixme.md` the
  defect ledger.

The logo: an egg, and inside it a signal growing to full amplitude —
carried to term while already sounding.
