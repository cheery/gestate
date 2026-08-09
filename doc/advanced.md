# Building the toolkit — the advanced course

`doc/beginner.md` used the library; `doc/intermediate.md` played it.  This
course opens it: everything in `synth.ges` is a fold, a delay line, or a
lift, and after these ten lessons you can build the combinator the library
does not have.  The lessons live in `examples/advanced/`, every one
renders, and the end of this file is a **coverage map** — every public
name in `doc/ref/`, and where it is taught.

Work the same way as before: run the form, make the `try:` edits with
`audiolive --watch` running, then take the departure at the end of each
section.  At this level the departures are the course.

---

## Lesson 1 — the floor  (`01-fold.ges`)

**The form.**  A synth with no library combinators above the waist: a
`case`-table tune, a `Blip` record folded over `ticks` by `scan`, a
`map` out to samples.  Everything you have used — `sine`, `adsr`,
`lowpassSvf` — is this shape with the numbers chosen.

Three rules of the compiled fragment show up bare, and they are the rules
you will live under for the rest of the course:

- **tables, not lists** — a cons walk per sample has no fixed cost, so
  the tune is `case i of 0 -> 110.0 …`;
- **records and named functions** — the fragment has no `let`; state is a
  declared record, taken apart by `case`;
- **phase accumulates** — `wrap (p + hz/rate)`, never `n * hz / rate`: an
  accumulated phase bends through a frequency change, a computed one
  snaps, and a snap is a click.

**Turn it.**  The shapes (`sawOf` → `triangleOf`, `squareOf`, `sineOf`)
all read the same 0..1 phase — one convention, any waveform.  The
envelope rate turns notes into ticks.

**Leave it.**  Put a *second* phase in `Blip` at a slightly detuned
frequency and sum the two shapes in `blipOut` — you have built
`polysaw.ges`'s fatness by hand and know exactly what it costs: one field
and one add.

## Lesson 2 — your own combinator  (`02-samplehold.ges`)

**The form.**  The library has no sample-and-hold, so this file writes
it: a record (`SH`), a step (grab the input when the phase wraps, hold
otherwise), and a face —

```
sampleHold : Sig Float -> Sig Float
sampleHold s = map shOut (scan stepSH (SH 0.0 0.0) s)
```

That last line is the lesson: nothing distinguishes your combinator from
the library's.  One more fragment rule appears: state is **its own
record**, not a tuple and not a shared `Both` — a record type is laid out
once per program, and one used at two element types collides in the code
generator.

**Turn it.**  `shRate` at 12.0 and 1.0.  Feed it a slow sine instead of
noise (a staircase arpeggio); quantise the output (the marked edit) and
random cutoffs become random *pitches*.

**Leave it.**  Write the next classic the library lacks: a *slew-rate
limited* random walk (S&H into `slew` — two combinators you now both
understand), or a clocked S&H whose rate is `beat`-locked from the
intermediate course.

## Lessons 3–5 — the delay-line trilogy

Four primitives, one family, each adding a single power:

```
scan       f z s   out[t] = f (out[t-1],  s[t])     one sample back
feedback n f   s   out[t] = f (out[t-n],  s[t])     n samples back
loop     n f z s   st[t]  = f (st[t-1], st[t-n], s[t])   both arms
tap   n pos s      read s at pos samples back - pos a signal, fractional
slide n f pos s    feedback whose arm is pos - the line that bends
```

`n` folds to a number before the program runs — the engine has no
allocator — and none of them puts a cycle in the graph: the loop lives
*inside* the node.  `spec/delaylines.md` is the design.

**`03-feedback.ges`** builds an echo (`x + 0.6 * y` around a 400 ms line)
and then shortens the same code to 1/220 s, where repeats stop being
rhythm and become **pitch** — a comb, the resonator a plucked string is
made of, here ringing `dust` impulses.  Turn the feedback toward 1.0 and
learn why the library clamps it; make the line `1/110` s and hear the
octave.  Depart: two combs at a fifth apart, fed the same dust — a
power-chord resonator.

**`04-loop.ges`** is Karplus-Strong with the lid off: the `Wire` record
carries the neighbouring sample `feedback` cannot reach, and averaging
the pair is the lowpass that makes the string die treble-first.  The
marked edits are the physics: drop the averaging and it rings cold like a
comb; lower the loop gain and you have palm muting.  Depart: put a
*different* filter in the step — that is the whole definition of a
waveguide, and `string`/`damped` in the library are exactly such steps
with their numbers measured.

**`05-tap.ges`** makes the arm move.  A 1–5 ms tap swept at 0.15 Hz,
mixed with the dry signal, is a **flanger**; the same code at 25 ms is a
**chorus** — the length is the entire difference.  `slide` closes the
moving read into a feedback loop: a quarter-second echo whose time
flutters like worn tape.  Freeze the position and hear what the motion
was doing (a fixed comb); overdo the wobble and meet tape-sickness.
Depart: a vibrato is a 5–10 ms `tap` on *any* signal with nothing mixed
in — apply it to lesson 4's string.  (`allpass`, the reverb's glue, is
this family too: a delay that rearranges *when* without touching *how
much* — `doc/ref/synth.md` has it.)

## Lesson 6 — the noise cabinet  (`06-noise.ges`)

**The form.**  Five colours named by slope — `violet` +6, `blue` +3,
`white` 0, `pink` −3, `brown` −6 dB/octave — and `dust`, which is noise
pulled apart into events.  The file is a shoreline: brown surf under a
breathing gain, pink air, dust-struck resonator rain, and a gull that is
a narrow band of violet gated by `follow` over very sparse dust.

The two reusable moves: **colour is weather** (swap the colour under one
gain and the scene changes season), and **dust triggers things** — any
resonator, any envelope, anything that wants striking at natural-feeling
random.

**Turn it.**  Each `try:` swaps a colour or a density.  Seeds matter:
give two parts the same seed and they stop being independent weather.

**Leave it.**  Build a different place from the same six sounds — a
campfire (brown crackle is dust into a lowpass), a machine room (combs
from lesson 3 on pink), a crowd.  Nothing new is needed; that is the
lesson.

## Lesson 7 — dirt and dynamics  (`07-shape.ges`)

**The form.**  Tools that act on *level*: `follow` measures it,
`compress` (a `Comp` of threshold/ratio/attack/release) evens it,
`drive` saturates it (level-matched `softClip`), `wrapFold` destroys it
artistically.  Two habits ride along: `dcBlock` after asymmetric shaping,
`dbGain` for thinking in decibels.

The centrepiece is **sidechain ducking** — the pump in every dance mix,
and here it is three lines: `follow` the kick, subtract from one, multiply
into the bass.  No routing, no "sidechain input": one signal steering
another, which by now is your oldest reflex.

**Turn it.**  `duckDepth` 0 → 1.4; the compressor's attack at 0.05 lets
each kick's front through and the mix starts to thump; sweep `foldDepth`
and a clean tone turns metallic.

**Leave it.**  An auto-wah: `follow` into a `lowpassSvf` cutoff — the
filter opens when you play harder, which is most of what a wah pedal is.
Then de-ess a hi-hat: `follow` a `highpassSvf`'d copy, duck the original
with it.

## Lesson 8 — the filter cabinet  (`08-filters.ges`)

**The form.**  The SVF computes lowpass, highpass, bandpass and notch in
one pass, and which door you take is the sound.  The centrepiece: **a
voice is a filter bank** — two narrow `bandpassSvf`s at formant
frequencies over a PWM buzz, with `bimix` sweeping the formant pair from
*ah* to *ee*.  Around it, the rest of the cabinet: the one-pole pair
(gentle), the ladder (steep, saturating, thins its own bass — character,
not defect), a notch taking a bite, and an oscillator built from `phase`
+ `pulseOf` — pulse-width modulation, which the shipped `pulse` cannot
do because its width is fixed.

**Turn it.**  Pin the vowel at each end; make the sweep a `sampleHold`
staircase (lesson 2 — a robot choir); A/B the ladder against the one-pole
under the same bass.

**Leave it.**  A third formant makes the vowel a *person* — look up
formant tables and pick a different speaker.  Or run lesson 6's noise
through the vowel bank: whispering.

## Lesson 9 — the operator bank  (`09-fm.ges`)

**The form.**  `pm` was one sine bending another; `fm` is four, and the
instrument is **data**:

```
Patch (Quad 1.0 2.0 3.51 2.005)   -- ratios: each op, × the note
      wiring                      -- modulates src dst turns, stacked on noWiring
      (Quad 1.0 0.0 0.0 0.12)     -- amps: who is heard (the carriers)
```

The levels arrive as a `Sig Quad`, one envelope per operator, and that is
the sound's life: a modulator's level is *brightness*, a carrier's is
loudness, and modulators decaying faster than carriers is why every note
starts metal and dies to a sine.  The diagonal of the matrix is feedback;
`pmSelf` is that diagonal alone, the cheapest bright wave there is.

**Turn it.**  Ratio 2.0 → 2.01 (beating); 3.51 → 4.0 (suddenly
harmonic); the presets `fmBell`, `fmStack`, `fmFeedback` under the same
levels — same envelopes, different animals.

**Leave it.**  Swap the level envelopes so notes *open* instead of dying
(reverse instruments).  Then take the patch into a `voices` bank with
`adsrOf` building the `Quad` per note — `examples/audio/fmpoly.ges` is
that file, and after this lesson it reads as yours.

## Lesson 10 — a face for the instrument  (`10-canvas.ges`)

**The form.**  One file, two halves: `sound` compiles and runs per
sample, `substrate` is interpreted per frame, and they meet on
**channels** — a picture with a channel attached is a control, and the
signal it feeds is the same signal the filter reads.  Run it with
`python -m gestate.audiopygame`.

The instrument is a **ribbon**: `onTouchX` reports a 0..1 fraction of the
element's own extent, `pow` makes equal distances equal intervals, and
`slew` glides the pitch to your finger — the glide rate is the entire
feel.  A fader (`onTouchY`) and a meter (fed by the `peak` channel the
host writes) complete it, laid out with `over`/`row`/`column`, spaced
with `gap`/`pad`/`sized`, placed by centres throughout.

Two boundary rules, both of which will bite you exactly once: **clamp
every control** — the offline renderer sweeps controls with the sample
index on purpose, so an unguarded `pow` renders as `inf` instead of
failing on stage — and **`onTouchY` counts from the top**, so a fader
inverts it in one named place or meets the flip again as a bug.

**Turn it.**  The glide at 0.02 (keys) and 0.0005 (theremin); a second
ribbon an octave down in a `column` — a two-string instrument.

**Leave it.**  A `circle` is a knob face; `events` and `scan` (see
`examples/gui/bounce.ges`) make the canvas a *game*, and the canvas
lesson of `examples/audio/envelope.ges` draws the very envelope the
sound walks, with probe channels reporting each voice's age.  Build the
face your instrument from any earlier lesson deserves.

---

## The coverage map

Every public name in `doc/ref/`, and where it is taught.  *(B n)* =
beginner lesson, *(I n)* = intermediate, *(A n)* = advanced; a file name
means the example that carries it; **ref** means the reference entry is
the teaching — read it when you reach for the name.

**Signals** (`signal.md`): `scan` `map` (A 1) · `zip` (A 1, A 8) ·
`Both` (I 1's doc; `duet.ges`) · `feedback` (A 3) · `loop` (A 4) ·
`tap` `slide` (A 5) · `mkSig` (A 10) · `gain` (B 1).

**Audio** (`audio.md`): `ticks` (A 1) · `elapsed` (B 3) · `seconds`
(A 3) · `Num`/`Floating (Sig Float)` (B 1) · `mkKnob` (I 4) · `wrap`
(B 3, A 1) · `sawOf` `squareOf` `triangleOf` `sineOf` (A 1) · `pulseOf`
(A 8) · `tau` — the 0..1-turns convention every phase here shares, ref ·
`unipolar` (B 5) · `bipolar` — its inverse, ref · `Gate` (I 1) ·
`FromMIDI` (I 1) · `lowpass` (A 1) · `clip`/`Clip` (B 9's doc) ·
`Envelope`/`on` (B 10, `scenery.ges`) · `beatOf` ref.

**Synthesis** (`synth.md`): `sine` `saw` `square` `triangle` `pulse`
(B 2) · `phase` (A 8) · `keyHz` (I 1) · `centsHz` (I 5) · `dbGain`
(A 8) · `nyquist` (`polysaw.ges`) · `secondsSince` ref · `Seed` `white`
(B 6) · `dust` (B 7, A 6) · `pink` `brown` `violet` `blue` (A 6) ·
`Adsr` `adsr` (I 1) · `adsrOf` (`fmpoly.ges`, `sine.ges`) · `perc`
(I 3) · `percOf` (`envelope.ges`) · `onset` ref · `slew` (A 10,
`lead.ges`) · `lowpassOnePole` `highpassOnePole` (A 8) · `dcBlock`
(A 7) · `lowpassSvf` (B 4) · `highpassSvf` (B 6) · `bandpassSvf`
`notchSvf` (A 8) · `lowpassLadder` (A 8, `polysaw.ges`) · `resonate`
(B 7, A 6) · `softClip` `driveOf` `drive` (A 7) · `wrapFold` (A 7) ·
`follow` (A 6, A 7) · `Comp` `compress` (A 7) · `limit` (B 7's doc,
A 6) · `brickwall` (B 9, A 2) · `echo` (B 9) · `comb` (A 3) · `string`
(B 7) · `allpass` ref (A 5's doc) · `damped` (`strings.ges`) · `reverb`
(B 9) · `flanger` `chorus` (A 5) · `Stereo` and its instances, `pan`
`panOf` `widen` `pair` (I 5) · `widenOf` `monoOf` ref · `pm` (B 8) ·
`pmSelf` (A 9) · `Quad` `Matrix` `Patch` `fm` `noWiring` `modulates`
`fmStack` `fmBell` `fmFeedback` (A 9).

**Music** (`music.md`): `'` `++` `||` `at` `|*` `|/` `r` `reverse`
`>>=` `ticksPerBeat` (I 2) · `|<` `>|` — sugar for `at` by one beat,
ref · `prog` `percussion` (I 7) · `Tempo` (I 6) · `Score` `Rendered`
`lay` `layout` `layVoices` — the machinery the backends call, ref.

**Canvas** (`gui.md`): `Sub` `rect` `over` `row` `column` `sized` `pad`
`gap` `moveXY` `onTouchX` `onTouchY` `colour` (A 10) · `circle` `blank`
`events` `Event` `input` (`examples/gui/bounce.ges`, and A 10's
departure) · `Num (Sig Int)` (A 10, implicitly — every size in it).

**Prelude** (`prelude.md`): `clamp` (A 10) · `mix` (`substrate.ges`) ·
`bimix` (A 8) · `pow` (A 10) · `exp` (B 3) · the rest is general-purpose
language, taught by `doc/manual.md`.

**The language page** (`language.md`): `chan` `wait` `:::` (A 10) · `!`
(I 1, I 5) · `head` `tail` `delay` `gfix` `sync` `watch` `never` — the
FRP core under everything here; `doc/manual.md` §6 and `spec/frp.md`
are its course.

If a name has no lesson, its reference entry was written to stand alone —
that is what `doc/ref/` is for, and `--query NAME` asks the same question
of the program you actually have open.

## After this

`doc/super.md` is the patch book: finished sounds, built from everything
above, meant to be stolen from.  And the library itself is now readable —
`gestate/synth.ges` is folds you can write, measured and named.  The next
combinator it grows could be yours.
