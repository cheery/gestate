# examples/

Programs that run.  `fixme.md` F29 asked for these: every other test in the
suite was written by someone who already knew the language's workarounds,
and that is a characteristic blind spot — writing these found three parse
defects (F70, F71, F72) and two bugs in the `typecheck` CLI (F73), none of
which 653 tests had touched.

`test/test_examples.py` runs all of them, so an example that stops working
is a failing test rather than a stale file.

## The courses — `beginner/`, `intermediate/`, `advanced/`, `super/`

Four directories of lesson synths, one per guide in `doc/`, meant to be
read *with* their guide and edited while they sound
(`python -m gestate.workbench <file>`):

| directory | guide | what it teaches |
|---|---|---|
| `beginner/` | `doc/beginner.md` | synthesis itself: oscillators, envelopes, filters, LFOs, noise, FM, effects — patches that trigger themselves |
| `intermediate/` | `doc/intermediate.md` | instruments and pieces: `voices` banks, gates, payloads, knobs, stereo, scores, tempo curves, MIDI files |
| `advanced/` | `doc/advanced.md` | the toolkit's own construction: raw `scan` folds, the delay-line primitives, noise colours, dynamics, the filter cabinet, the FM operator bank, a canvas UI |
| `super/` | `doc/super.md` | no lessons — six finished patches, built to be stolen from |

`test/test_courses.py` builds every one of them, so these cannot quietly
go stale either; the guides' `try:` lines are the listening half.

## The language

| file | what it shows |
|---|---|
| `closure.ges` | Datalog: a fixed point, a comprehension with two generators and a guard |
| `relations.ges` | `fix` at a product of semilattices; a set of a user data type |
| `signals.ges` | Rizzo's FRP: a channel, a guarded fixed point, `map` over a signal |
| `records.ges` | records, `x.0` projection, classes, `deriving` |

```
python -m gestate.typecheck examples/closure.ges
```

## Music — `music/`

| file | what it shows |
|---|---|
| `scale.ges` | notes, sequence, instrument selection |
| `chords.ges` | overlay, duration scaling, `at` shifting the grid |
| `canon.ges` | a round: one melody against itself, offset; two instruments |
| `arpeggio.ges` | `|/` for sixteenths under a held bass |
| `drums.ges` | percussion, and a fill that arrives a beat early |
| `nocturne.ges` | 85 seconds, five voices, five sections — how a whole piece is put together |
| `passacaglia.ges` | five minutes, six voices, eight sections; `transpose` written in the language |
| `duetline.ges` | the same walking bass, committed to a MIDI program instead — `Play Rendered` beside `duet.ges`'s `Assigned Voice` |

The first five are each one idea, small enough to read in a sitting.
`nocturne.ges` is the one to read once those make sense: it is the same
operators used at the scale where they start to earn their keep — a section
is an overlay of voices, a piece is a sequence of sections, and repetition
is a function rather than a copy.

`passacaglia.ges` is five minutes long and exists to find out whether any of
that survives at length.  It repeats one bass line under eight sections, and
its `transpose` is four words of ordinary code — `s >>= (k => '(k + n))` —
because the score monad already substitutes a score for every note.

```
python -m gestate.midi examples/music/drums.ges --events   # print the layout
python -m gestate.midi examples/music/drums.ges            # write drums.mid
```

The `.mid` files beside them are **golden**: rendering is byte-deterministic,
so `test_examples.py` re-renders each one and compares.  A change to layout,
tick arithmetic, event ordering or channel allocation shows up as a diff in
a file you can also listen to.

A music program is different in shape: it supplies `score : [: Void :]` and
`bpm : Int` rather than `main`, and the renderer supplies `main`.  It also
needs `gestate/music.ges`, which the MIDI backend prepends and the core
prelude deliberately does not carry — eight constructors would renumber
`Nil`/`Cons` for every program in the language.  So a music program is read
with `python -m gestate.midi`, not `typecheck`.

## GUI — `gui/`

| file | what it shows |
|---|---|
| `bounce.ges` | a ball you can throw with the mouse: state as a fold over events |
| `chain.ges` | a chain that follows the pointer: a *list* in the state, and why the past has to be carried |

```
python -m gestate.gui examples/gui/bounce.ges              # open a window
python -m gestate.gui examples/gui/bounce.ges --frames 5   # print shapes, no window
```

A GUI program supplies `substrate : Sig Sub` — a picture that varies over
time and says what it listens to — and `gestate/gui.py` drives it, the way
the MIDI backend drives a `Score`.  `gui.ges` is prepended, and gives it
`Event`, `Sub`, and the signal combinators.

The shape of one is three definitions and a fold:

```
substrate : Sig Sub
substrate = map draw (scan stepBall start events)
```

That folds the events into a state and draws it.  There is
no callback and no mutable variable — and `scan`, which does the folding, is
guarded recursion, so the type system knows the signal always has a next
value.  A signal is a heap cell overwritten in place, so the past positions
of the ball are not retained anywhere.

Running it needs `pygame`.  `gestate.gui.scenes()` does not, which is why
`test/test_gui.py` never opens a window.

## Audio — `audio/`

| file | what it shows |
|---|---|
| `sine.ges` | the smallest note there is: one sine, one `Adsr`, and an envelope that carries no state |
| `blip.ges` | a synth: oscillator, envelope and filter, each a fold over time |
| `drums.ges` | kick, snare and hat: noise from a folded seed, three voices summed in one state |
| `knob.ges` | a control-rate parameter: a second clock, and a slider that turns it |
| `fm.ges` | FM — the instrument that needs a real `sin`, and two envelopes, one of them on timbre |
| `pluck.ges` | additive: three harmonics, each with its own exponential decay |
| `twoknobs.ges` | two parameters, two channels — one knob each, placed at their declarations |
| `polysine.ges` | `sine.ges` made an instrument: a `voices` bank, a `FromMIDI` instance and a piece — and a voice that is one expression |
| `duet.ges` | **one program**: two `voices` banks, its own piece, and a mix — a score plays one bank, your keyboard the other |
| `stereo.ges` | two *output* channels: `sound : Sig Stereo`, 440 Hz left against 442 Hz right |
| `fmpoly.ges` | six-voice FM — the operator wiring is a **matrix in the file**, feedback included |
| `polysaw.ges` | eight-voice subtractive: detuned saws, an envelope-swept resonant ladder |
| `stereopad.ges` | a bank whose voices are *stereo* — `voices pad 6 padVoice : Sig Stereo` |
| `substrate.ges` | a synth you can **see and touch**: a fader and a meter on the canvas behind the editor, feeding and fed by the same signals |
| `lantern.ges` | **all three halves at once** — an unfolding seeded score, a compiled synth, and a canvas with two faders, a meter, and `label` captions naming them.  The one to export as a plugin (`--gui`) if you want to see the whole window doing its job |

```
python -m gestate.audioperform examples/audio/blip.ges -o blip.wav
python -m gestate.audioperform examples/audio/blip.ges --seconds 1 --peak  # no file
```

A synth program supplies `sound : Sig Float` — samples in -1.0 .. 1.0, one
per instant.  `audio.ges` is prepended and gives it `ticks`, the signal
combinators, and the oscillator shapes.  The sample rate is the *renderer's*
business, not the program's, so the same synth renders at any rate.

**A signal is a number.**  `audio.ges` declares `Num (Sig Float)` and
`Floating (Sig Float)`, so `tone * (0.5 + wiggle * 0.25)` is arithmetic and
means the `zip` chain it looks like — the same graph, node for node.
That is Fran's move (`spec/frp_lesson.md`), and what it took was a compiler
gap rather than a language: a generated instance method carried no type, so
the audio fragment refused every one of them by the name of its instance
head.

**`!` lifts anything else.**  `!x` is a constant signal, `!f x` is
`map f x`, `!f x y` is `zip f x y`, and more arguments pair up
through `signal.ges`'s `Both`.  One marker over the whole application, and
*written* rather than inferred: a lift a compiler inserted where types
disagreed would put a node in the graph the author never wrote, and stage 5
migrates running state by comparing node origins.

**`synth.ges` is prepended too**, after `audio.ges`, and is where the parts
you reach for after the oscillator shapes live: `Adsr` and `adsrOf`, a
state-variable filter and a four-pole ladder that both take a cutoff in
hertz and a resonance, a four-operator FM bank you wire with a matrix,
noise, soft clipping, and the stereo frame.

**A voice is an expression.**  `…At` takes a `Float` and is fixed when you
write it; `…From` follows a *signal* — `sine`, `saw`, `phase`.
A bank hands its voice **two** signals, `Sig Gate` (when the note began,
when it was released) and `Sig <payload>`, so a pitch reads one and
`adsr` reads the other without either opening a record.  With `!f x`
for the lift, a whole polyphonic voice is one line:

    sineVoice g s = sine (!hzOfKey s) * adsr env g * !velOfKey s

with no state record, no `scan`, and no note taken apart per sample —
`polysine.ges` is that file, and it renders sample for sample what the
hand-written state machine did.  Two rules still shape everything:

* **a component is a state record and a step function, never a closure** —
  there is no `makeOscillator hz`, there is a `Phase` and a `phaseNext` you
  fold with `scan`.  The static fragment forbids building a function while
  the program runs.  (`sine` is that fold, written once.)
* **a parameter travels in the state or in the signal, never in a partial
  application.**  `lowpassSvf 800.0 0.7 s` works because the extractor
  *inlines* it; `scan (osc hz) …` does not work at all.

A **parameter** is one line — `level : Sig Float` / `level = mkKnob 0.6` —
and the editor draws a slider beside that declaration.  `mkKnob : a -> Sig
a` is polymorphic — the *type* picks the slider, a `Float` running 0.0..1.0
and an `Int` 0..100 — which works because a signal definition is inlined at
every use and no type variable survives into the graph.  The long
form (`Chan Float`, then `0.6 ::: mkSig (wait levelChan)`) still works and
`twoknobs.ges` writes it out, because a file about what a channel *is*
should.  Note `gain` takes a `Float` *constant*, so a knob cannot go there:
multiplying by a signal is `mulSig`.

There is deliberately **no delay line** — and so no chorus, echo or comb, and
no Karplus-Strong.  A delay is a buffer, and the fragment admits no
allocation.  `pluck.ges` shows the additive answer.

**More than one channel is a record.**  `sound : Sig Stereo`, for a
program's own `Stereo := Stereo Float Float`, is one channel per field in
field order — and it goes the whole way: the `.wav` is two-channel, the
graph extracts unchanged, and the generated engine stores both fields
interleaved and is bit-identical to the oracle.  `stereo.ges` is the one
that does it.  A *tuple* is not admitted, and `fixme.md` F95 says why: the
G-machine gives `NTuple` no tag word, and every flat value the audio IR
lays out is a tagged `NCon`.

Everything in `blip.ges` is one idea: **a synth is a fold over time.**  An
oscillator's phase, an envelope's level and a filter's memory are all state
that depends on the previous instant, and `scan` is what carries state
across instants.

```
ticks ─scan stepVoice─► Voice ─map voiceOut─► raw ─lowpass─► sound
```

`lowpass` is a *signal transformation* — a signal in, a signal out, its
memory held by another `scan`.  Chaining those is what a synth is.

**This is offline.**  A gestate signal stepped per sample runs a few
thousand instants a second against the 44,100 real time needs, and a faster
interpreter would not close that gap: audio DSP wants flat buffers and no
allocation, which graph reduction is not.  SuperCollider splits the language
that *describes* an instrument from the engine that runs it; this is the
describing half, and rendering to a file is the part that needs no engine.
Only the stdlib `wave` module is involved.
