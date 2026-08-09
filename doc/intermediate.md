# Playing it — the intermediate course

`doc/beginner.md` ended with patches that trigger themselves.  This course
is about **instruments and pieces**: sounds that are *played* — by a score
the same file carries, or by your hands on a keyboard — and music written
as values you can transform.  The lessons live in `examples/intermediate/`
and every one renders.

**How to work through this.**  Each lesson has three layers, and the code
is built for all three:

1. **The form** — run the file as it stands and read it until nothing in
   it is mysterious.  Every tunable number is named near the top.
2. **Turn it** — the `try:` comments are specific edits with predictable
   outcomes.  Make them, listen, undo.  This is where the vocabulary
   becomes yours.
3. **Leave it** — each lesson below ends with departures: changes with no
   given answer.  When one of those turns into twenty minutes of fiddling,
   the lesson worked.

The commands, once:

```
$ python -m gestate.audioperform examples/intermediate/01-instrument.ges -o l1.wav
$ python -m gestate.audioperform examples/intermediate/01-instrument.ges --midi
$ python -m gestate.audiopygame  examples/intermediate/01-instrument.ges
```

`audioperform` plays a scored synth (or renders it with `-o`); `--midi`
hands a bank to your keyboard.  `audiopygame` opens the editor: the file,
its knobs, and the sound, live — edits land without restarting the sound,
which is what makes the "turn it" layer cheap.  A plain synth (lessons 4)
still uses `audiolive`/`audio` as before.

---

## Lesson 1 — an instrument, not a patch  (`01-instrument.ges`)

**The form.**  The beginner lessons faked their notes with looping
envelopes.  A `voices` bank replaces the fake:

```
Key := Key Int Int                        -- key number, velocity

voices lead 4 leadVoice : Sig Float

leadVoice : Sig Gate -> Sig Key -> Sig Float
leadVoice g s = triangle (!hzOf s) * adsr env g * !velOf s
```

Read the declaration as: *`lead` is four copies of `leadVoice`, summed.*
Each copy is handed two signals it never computes:

- `Sig Gate` — **when**: the sample its note began and was released.
  `adsr env g` turns that into the real attack-decay-sustain-release
  envelope; the wrap-trick from beginner lesson 3 is retired.
- `Sig Key` — **what**: this program's own payload type.  A payload is
  whatever *you* decide a note carries — here a key number and a velocity;
  scalar functions like `hzOf` read it, lifted over the signal with `!`.

Notes reach the bank two ways, and the voice cannot tell which.  The score
at the bottom is one: `tune >>= voices.lead` commits every note of the
phrase to the bank, and the result type `[: Void :]` means *nothing left
unassigned* — a piece with an uninstrumented note does not compile, so
"did you forget an instrument" is a type error instead of a silence.  A
keyboard is the other: the `FromMIDI` instance says how a MIDI note
becomes a `Key` (returning `Nothing` declines it — a bank that only wants
the low octave says so here).

Two conventions worth adopting now: don't name a payload `Note` (the score
library owns that constructor), and set gains on the *thickest* chord —
the bank's name is the sum of its voices, so a level set on one note clips
on four.

**Turn it.**  The `try:` comments: a slow attack makes it bowed; `saw`
through a per-note filter sweep makes it the beginner guide's lesson 4,
now triggered properly.  Play it from a keyboard with `--midi` and hold a
chord: four voices, four independent envelopes.

**Leave it.**  Make a fifth signal the voice reads — a per-note vibrato
that only starts after the attack (`adsr` with a slow attack, multiplied
into the depth).  Or make `FromMIDI` selective: `Nothing` above key 60,
and the keyboard only plays the left hand.

## Lesson 2 — phrases are values  (`02-phrases.ges`)

**The form.**  A score is a value, so composition is function application.
The whole piece grows from one four-note cell:

```
cell = n 57 ++ n 60 ++ n 64 ++ n 62

up j q = case q of Key k v -> '(Key (k + j) v)

quick  = (cell ++ (cell >>= up 12)) |/ 2        -- transposed, halved
crab   = reverse cell                           -- retrograde
round2 = theme || at (4 * ticksPerBeat) (theme >>= up 12)
```

The operators: `++` sequences, `||` overlays (everything inside starts
together), `|*`/`|/` stretch and shrink durations, `reverse` is
retrograde, `r` is a rest, and `at` slides a phrase in time **without
changing its duration** — which is what makes a round: the same theme
against itself, entering a bar late.  Transposition is nothing special:
`>>=` substitutes a little score for every note, so *any* per-note rewrite
— transpose, thin the velocities, turn each note into a grace-note pair —
is an ordinary function.

**Turn it.**  Change the four notes of `cell` and the entire piece —
octave answer, retrograde, round — follows, which is the point: structure
survives material.  Then the marked edits: a third entry in the round; the
crab of `quick` rather than of `cell`.

**Leave it.**  Write `augment` (every duration doubled — `|* 2` inside a
`>>=` won't do it; why not? what will?).  Build an eight-bar piece from a
cell of *three* notes, and notice where the bar-line fights you.  Steal
the drum-fill trick from the manual: `groove ++ at (0 - ticksPerBeat) fill
++ crash` — the fill starts early, the grid doesn't move.

## Lesson 3 — a band is a sum  (`03-band.ges`)

**The form.**  Two banks in one file — a plucked bass, a sustained pad —
and each part of the piece commits to its own:

```
score = (bassLine >>= voices.bass) || (pads >>= voices.pad)

sound = 0.5 * bass + 0.35 * pad
```

Two things carry this lesson.  First, envelope *kind* is instrument
character: the bass uses `perc` (a pluck decays on its own; release means
nothing to it), the pad uses `adsr` (it holds while held — release is
where it lives).  Second, the banks **share one payload type**.  That is a
rule, not a style: the code generator lays a record out once per program,
so two banks declaring two records collide — one payload, read differently
by different voices, is the working arrangement (`quartet.ges` says this
too, with four).

**Turn it.**  The marked swap — bass part on the pad, pads on the bass —
is one word each, and the type checker allows it because the payloads
agree.  Hear how much of "bass-ness" was the *envelope* rather than the
notes.  Give the bass's filter its own `perc` rate and brightness detaches
from loudness.

**Leave it.**  Add a third bank — a kit.  The payload's key number can
*be* the drum selector: `case` on it in the voice, 0 for a kick (falling
sine), 1 for a snare (noise burst) — `examples/audio/quartet.ges` runs
this trick at full scale.  Then mix like a mixer: reverb send on the pad
only, `drive` on the bass only.

## Lesson 4 — knobs  (`04-knobs.ges`)

**The form.**  Everything so far was fixed at save time.  A knob is not:

```
cutoff : Sig Float
cutoff = mkKnob 0.4
```

`mkKnob v` is a **control-rate** parameter: held constant across a block,
costing a few instructions per block rather than per sample, drawn as a
slider beside its own declaration in the editors (`audioeditor`,
`audiopygame`), and mapped to MIDI CC in declaration order by
`audiolive --midi`.  A `Float` knob runs 0..1 — the program scales it,
so the range lives where you can read it:

```
hzOfKnob x = 150.0 + 4800.0 * unit x * unit x
```

Two idioms here: the square, because hearing is logarithmic and a linear
slider spends most of its travel on the top octave; and the `clamp`
(inside `unit`), because a knob is the one number the synth does not
compute — the offline renderer sweeps every knob with the sample index
precisely so that an unguarded parameter shows up as a broken render
rather than as a surprise on stage.

**Turn it.**  Open it in `audioeditor` and play the two sliders against
each other.  Then the marked edits: resonance as a third knob; a different
interval under the blend.

**Leave it.**  Put a knob where a *number* used to be in any beginner
lesson — echo feedback, FM depth, drum rate — and re-render.  Then try a
knob that chooses rather than sweeps: an `Int` knob (0..100) `case`d into
one of three waveforms.

## Lesson 5 — stereo  (`05-stereo.ges`)

**The form.**  `sound : Sig Stereo`, and every mixing habit carries over
because a `Stereo` is a number too.  Three widths, one per part:

- **placement** — the harp voice pans itself by its own key, low notes
  left: `!panOf (!panOf' s) mono`.  Equal-power, so a run crosses the
  field without dipping in the middle.
- **decorrelation** — the bed is two saws three cents apart, one per ear
  (`pair`).  Not one sound panned: two slightly different sounds, which
  the ear reads as *room*.
- **anchor** — whatever must hold the centre (a bass, a kick) goes to both
  ears unchanged (`widen`).

One lifting rule surfaces here: a literal becomes a constant signal by
itself, but a *computed* Float needs `!` — `saw (!hz)` where
`hz = centsHz spread 110.0`.

**Turn it.**  `spread` at 0.0 (mono), 12.0 (seasick).  Negate the pan
curve — audience side.  Set the pan to a constant and hear the harp
collapse into a point.

**Leave it.**  Put motion in the field: the *pan position* can be a signal
— a slow sine on the bed's placement.  Or width as drama: verse in mono,
chorus wide, driven by an `on` envelope over `elapsed`.

## Lesson 6 — tempo is a curve  (`06-tempo.ges`)

**The form.**  `tempo : List Tempo` in place of `bpm`, points at
(seconds, bpm):

```
tempo = [ Step 0.0 70.0, Ramp 10.0 130.0, Step 12.0 130.0, Ramp 16.0 90.0 ]
```

Stating a tempo (either form) puts **`beat : Sig Float`** in scope — what
time it is *in beats*, at audio rate.  The lesson's two halves both read
the curve: the scored arpeggio's notes are landed on the moving grid by
the scheduler, and the hat tick is the beginner guide's wrap-trick with
`beat` in place of `elapsed` —

```
map (b => exp (negate 50.0 * wrap b)) beat
```

— an instrument the score never touches, accelerating in lockstep with
notes it cannot see, because both readings are compiled from the same
derivation.  That is the idea worth keeping: **`beat` is the piece's own
clock, and anything arithmetic can be put on the grid.**

**Turn it.**  Flatten the envelope and hear what the curve was doing.
Make it fall — a piece running out of breath.  Put `elapsed` where `beat`
is and listen to the tick fall off the grid as the tempo moves.

**Leave it.**  A filter sweep that opens over exactly eight beats,
whatever the tempo (`on <points> beat` — the envelope's x-axis is beats
now).  A ritardando into a final chord.  Swing: the tick's phase offset as
a function of `wrap (b / 2.0)`.

## Lesson 7 — writing a MIDI file  (`07-midifile.ges`)

**The form.**  A program that is *only* a piece: `score` and `bpm`, no
`sound`, notes carrying bare GM key numbers.  `prog 0` (piano) and
`prog 32` (bass) commit the pitched parts; `percussion` takes the kit,
whose "pitches" are GM drum keys (36 kick, 38 snare, 42 hat).
`python -m gestate.midi` writes a `.mid` beside the source; `--events`
prints the layout as a table, which is also the fastest way to *see* what
`||` and `|*` did to time.

Everything from lesson 2 applies unchanged — same operators, same
algebra, different renderer.  That is the seam the design keeps: what a
piece *is* does not depend on who performs it.

**Turn it.**  The marked program swaps — the same melody through a flute,
a square lead, a nylon guitar.  Add an off-beat open hat (`r` then key 46,
shrunk).

**Leave it.**  Take the piece from lesson 3 and re-target it here: the
notes move, the banks are replaced by `prog`s.  What did the synth version
have that the GM version loses?  That difference is your instrument
design, isolated.  Then go the other way: import this groove into lesson
3's kit-bank idea and keep both renderers pointed at one set of phrases.

---

## Where the scaffold ends

You now hold the whole middle of the system: instruments (`voices`, gates,
payloads), performance (scores, `FromMIDI`, knobs), space (stereo), and
time (`beat`, tempo curves).  Three directions from here:

- **Scale it up.**  `examples/audio/quartet.ges` is four banks and three
  minutes of form; `gyre.ges` is a tempo envelope carrying a whole piece;
  `strings.ges` is an instrument the score *cannot* hold and plays in time
  anyway.  All three are the lessons above, composed.
- **Go under the floor.**  `doc/advanced.md` builds the toolkit you have
  been using — oscillators from `scan`, echoes from `feedback`, strings
  from `loop`, the FM bank, and a canvas UI for your own instrument.
- **Just write music.**  The fastest way to make these ideas permanent is
  a piece of your own, started from the lesson file whose sound is closest
  and edited until nobody would recognise it.
