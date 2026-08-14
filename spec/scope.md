# scope.md — a scope on a signal

*Companion to `spec/delaylines.md` (the ring it reads),
`spec/sampling.md` (`input`, the same buffer run the other way) and
`spec/workbench.md` §"The canvas walks over crust" (the road to the
eye).  The ask is Henri's, and the rule's: the last several synths
were debugged by ear against a graph the eye could not enter — you
can hear that a filter is wrong and you cannot see where it went
wrong.*

## The word

`scope`.  Not `probe` — spoken for twice, as ariadne's retired score
construct and as `Workbench.PROBES`, the voice ages that are live
right now.  Not `tap` — the audio term of art is a delay line's here:
`tap n pos s` is built and reads a `line` at a position
(`spec/delaylines.md`).  A third meaning for either word would be the
collision this project has avoided everywhere else.  `scope` names
the act and the display at once, which for once is honest: dropping
one *is* asking to see.

## The declaration — in the text, because the file remembers

    scope : Text -> Sig Float -> Sig Float

    filtered = scope "post" (lowpass cutoff raw)

Identity on the sound: what flows through is exactly what flowed in,
and the label is an assembly-time fact the way `voices`' name and
`sample`'s path are.  **In the text and not in the margin**, for the
margin's own reason: a mark beside the code needs a second identity
that survives edits by origin, and a declaration is carried by the
one identity the program already has.  The file remembers its scopes;
a diagnosis interrupted on Tuesday is still on the screen on
Wednesday.

**Dropping a scope is an edit and a `Ctrl-S`** — a rebuild, exactly
like every other change, and that is fine rather than the whole
problem because it is already the editor's entire rhythm: apply is
how a change reaches the ear, and now the same press is how a
question reaches the eye.  The sound keeps playing through the
rebuild, as it does for any edit; a scope is never worth an
interruption the edit itself would not cost.

## The buffer — a delay line's ring, published

A scope keeps the last window of its signal in a ring inside
`%State`, written per sample in `render_block` — **which is machinery
`spec/delaylines.md` already built**: `line`'s rings, their cursor
arithmetic, `zero` for their silence and `migrate` for their
survival across an applied edit.  A scope adds no new state shape; it
adds *publication*:

* The generated module exports `read_scope_<i>(%State*, double* out,
  i64 n)` per scope, copying the ring oldest-first using the same
  cursor the writes use.  **No offsets cross the boundary** — the
  generated code owns its layout, and the host calls a function, the
  discipline every other seam keeps.
* Python knows the labels and their order because it compiled the
  graph; `Graph.scopes()` answers `[(label, length)]` in declaration
  order.
* The read races the audio thread and may seam at a block edge.  A
  delay line could never tolerate that; **a diagnostic can**, and
  saying so here is what keeps anyone from ever feeding a scope's
  read back into the sound.

The window is 4096 samples — ~93 ms at 44.1 kHz, a few cycles of
anything audible — fixed rather than declared, because a window is
the reader's concern and the first argument a scope grows should be
earned by somebody needing it.

`input` (`spec/sampling.md`) is this ring with the writer on the
other side of the wall, and the looper wants it a third time; the
publication mechanism built here is what both inherit.

## The road to the eye

The scope rides the machinery the crust canvas built, and adds one
word to the wire:

* `Workbench.observe` drains each scope at the reading cadence
  (`READ_EVERY`) and **downsamples to 128 points by max-absolute per
  bucket** — a scope that averages away a click is a scope that
  lies.
* The points cross on the canvas's own channel as one line:

      trace <label> <v0> <v1> … <v127>

  `reading`'s plural sibling, and like every furniture verb an old
  window skips the word and loses the trace, not the file.
* The walked canvas writes the points to the channel named `<label>`
  as a `List Float` arrival; the reference substrate's `write` does
  the same, so headless and windowed draw one picture.

## The display is a substrate somebody writes

    post : Chan (List Float)
    post = chan

    substrate = column (scopeOf 200 60 (0.0 ::: mkSig (wait post)))
                       (caption "POST")

No new drawing vocabulary: a trace is a fold over the points into
`Rect`s, composed with `row` and `column` like everything else, and
`examples/audio/scoped.ges` is the worked example the way `lantern`
is for faders.  A `scopeOf` helper belongs in `gui.ges` the day two
files have written it.

**No spectrogram yet.**  The eight host bands already give a coarse
spectrum for free; a real spectrogram needs an FFT, which is a
library-or-host decision this spec deliberately does not smuggle in.
`spectro` is the natural second reader of the same window, and it
should arrive as one.

## Costs, stated

* A node kind through the vertical: syntax, extract, both engines,
  spans (a scope belongs to a line like a knob does), `zero`/
  `migrate` — though each stop reuses the delay line's answer.
* 32 KB of state per scope, and a ring write per sample per scope.
  A scope left in a shipped patch costs what a `delay 4096` costs;
  the export may carry it, because a plugin somebody is debugging in
  a DAW is still being debugged.
* The wire grows `trace`, and the walker grows a `List Float`
  arrival — the first non-scalar to cross either seam.

## Acceptance

1. Scope a filter's input and output in a playing synth and *see*
   the difference move as the knob turns — using only what the
   window shows.
2. Headless parity: `touches`-style, the reference engine fills the
   same window the compiled one publishes, held by a golden.
3. Adding and removing a scope is an ordinary apply: the sound does
   not stop, and the trace appears and disappears with the
   declaration.
4. The walked canvas draws the trace at the window's own frame rate,
   and the gesture loop pays one drain per reading cadence, nothing
   per frame.
