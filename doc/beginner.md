# Making sound — a beginner's course

This teaches synthesizer programming from nothing, using gestate.  Each
lesson is a complete synth in `examples/beginner/`, a few lines long, and
each one adds a single idea from synthesis — not from the language.  By the
end you will know what an oscillator, an envelope, a filter, an LFO and an
effect are, and how to combine them into a piece, which is the same
knowledge every hardware synth and every DAW plugin assumes.

The language you need is small: a synth is a file of named definitions, and
the one the engine plays is

```
sound : Sig Float
```

— a *signal* of floats, one per sample, in −1.0 .. 1.0.  Everything else in
the file exists to feed it.  `doc/manual.md` is the language course; this
file uses only what it must.

## Hearing anything at all

```
$ python -m gestate.audioperform examples/beginner/01-tone.ges --seconds 3
```

`audioperform` compiles the synth to machine code and plays it through
your speakers — this is the fast path, and the one to use.  Two more
forms of it are worth knowing from day one:

```
$ python -m gestate.workbench   examples/beginner/01-tone.ges
$ python -m gestate.audioperform examples/beginner/01-tone.ges -o tone.wav
```

`workbench` is the editor: it plays the file and it *is* where you change
it, and an edit you apply with `Ctrl-S` swaps the sound without
restarting it — the best way to work through these lessons is to leave it
open and turn numbers.  There is one mode in it, and it is typing;
`Ctrl-K` opens the list of everything else it can do.  `-o` renders a
`.wav` instead of playing, which is what you want when you want a file,
not when you want to listen.

---

## Lesson 1 — a tone  (`01-tone.ges`)

```
sound : Sig Float
sound = 0.3 * sine 220.0
```

`sine 220.0` swings between −1 and 1, 220 times a second, and that number
is the **pitch**: 220 Hz is the A below middle C, doubling it is an octave
up, halving it an octave down.  The `0.3 *` is the **loudness** — signals
do ordinary arithmetic in this language, so a gain is a multiplication and
a mix is an addition, and that is most of the plumbing you will ever need.

Why 0.3 and not 1.0?  The engine plays −1..1 and *clips* whatever goes
beyond it, audibly and badly.  A synth that peaks at 1.0 alone has no room
left to be mixed with anything, so leave **headroom** from the first line.
This habit is cheap now and every later lesson depends on it.

Things to try with the workbench open: change the pitch; change the gain;
write `sine 220.0 + 0.5 * sine 330.0` and hear that a mix is a `+`.

## Lesson 2 — waveforms are timbre  (`02-waves.ges`)

Two sounds at the same pitch and loudness still differ — a flute is not a
violin.  That difference is **timbre**, and for an oscillator it comes from
the wave's shape.  A shape's character is its **harmonics**: every periodic
wave is a stack of sines at 1×, 2×, 3×… the pitch, and how strong the high
ones are is how bright it sounds.

```
sound = 0.25 * (0.4 * sine 110.0 + 0.3 * triangle 110.0
              + 0.2 * square 110.0 + 0.4 * saw 110.0 + 0.3 * pulse 0.15 110.0)
```

The lesson file plays all five at once, which is a chord of one note.  To
actually learn them, solo each — comment the others out with `#` — and
listen in this order:

- `sine` — one harmonic, no character at all.  The raw material.
- `triangle` — a few weak harmonics.  Soft, flute-like.
- `square` — odd harmonics only.  Hollow, clarinet-like.
- `saw` — *every* harmonic, strong.  Bright and brassy, and the most
  useful starting point in synthesis, because lesson 4 subtracts from it.
- `pulse 0.15` — a square whose up-portion is 15% of the cycle.  Thin and
  nasal, and the width is a knob timbre moves with.

## Lesson 3 — envelopes  (`03-envelope.ges`)

A held tone is not a note.  What makes a note is loudness *changing over
time* — a struck string is loud immediately and dies away; a bowed one
swells.  The curve loudness follows is the **envelope**, and shaping it is
the single biggest step from "a tone" to "an instrument".

```
env : Sig Float
env = map (t => exp (negate 6.0 * wrap (2.0 * t))) elapsed

sound : Sig Float
sound = 0.4 * sine 220.0 * env
```

Read `env` inside out.  `elapsed` is a signal of how long the program has
been running, in seconds.  `map (t => …) elapsed` applies a function to it
at every instant, so the lambda is a curve *drawn as arithmetic on time*:
`wrap (2.0 * t)` is time sped up 2× with the whole part discarded — a ramp
0..1 repeating twice a second — and `exp (negate 6.0 * …)` turns each ramp
into an exponential fall from 1 toward 0.  Real decays are exponential
(that is how vibrating things lose energy), which is why this sounds like
plucking and a straight line down would not.

Multiplying the oscillator by it is the whole trick: **a note is a tone ×
an envelope**.  The `6.0` is how fast it dies — try 2.0 (a soft pad-like
tail) and 30.0 (a tick).  The `2.0` is how often it repeats.

The library has the same curve as a tool: `perc` is exactly this
exponential fall, and it reads *when to fall* off a **gate** — a note's
timing, the sample it began and the sample it was released.  A keyboard
or a score makes gates, but so does any true/false signal, through
`gateOn` — a rising edge presses, a falling edge releases — and one is
a comparison away:

```
easy : Sig Float
easy = perc 6.0 (gateOn (!(x => x < 0.5) (phase 2.0)))
```

Two new tools, each one idea.  `phase 2.0` is the ramp you just built
by hand — 0..1, twice a second — as a library word.  `!` **lifts** an
ordinary function over signals: `!(x => x < 0.5) (phase 2.0)` asks *is
the ramp in its first half* at every instant, the same job `map` did
for `env`, one character shorter.  The comparison is true for the
first half of each turn, so the gate presses twice a second, and
`perc 6.0` is the `6.0` you just tuned — the same pluck, with the
note's *timing* and its *shape* finally separate things.  Swap `env`
for `easy` in `sound` and it barely changes.  The other envelope tool
is `adsr`, which sustains while the gate is held and *releases* when
it lets go — `adsr (Adsr 0.01 0.1 0.7 0.2) (gateOn (!(x => x < 0.6)
(phase 0.5)))` is a slow organ-like note, and the four numbers are
attack, decay, sustain level, release.  And a gate need not come from
the clock at all: a note that plays whenever an LFO is high is
`gateOn (!(v => 0.5 < v) lfo)`, which lesson 5 will give you the LFO
for.

The `wrap` trick stays worth knowing — an envelope is just arithmetic
on time, and later lessons bend that arithmetic in ways no preset
shape offers.  These lessons keep using both.

## Lesson 4 — subtractive synthesis  (`04-filter.ges`)

Here is the sound most people mean by "a synthesizer", and the recipe is
called **subtractive** synthesis: start from a wave with too many harmonics
and carve away the top with a **filter**.

```
env : Sig Float
env = map (t => exp (negate 6.0 * wrap (2.0 * t))) elapsed

sound : Sig Float
sound = 0.4 * lowpassSvf (150.0 + 2500.0 * env) 0.7 (saw 55.0) * env
```

`lowpassSvf cutoff resonance input` passes what is below the cutoff
frequency and rejects what is above.  Two knobs:

- **cutoff** — where the ceiling sits.  Low is muffled, high is bright.
- **resonance** (0..1) — a peak *at* the ceiling.  At 0.7 the filter rings
  audibly at its own cutoff, which is the electric, vowel-ish character
  resonant filters are loved for.

The important move: the cutoff here is not a number, it is `150.0 + 2500.0
* env` — the *same envelope that shapes the loudness sweeps the filter*,
so every note starts bright and darkens as it fades.  Timbre moving with
loudness is what your ear reads as "played" rather than "switched on".
This one line — envelope into cutoff — is the classic analogue synth
sound, and half the presets on any synthesizer ever sold.

Try: resonance 0.0 vs 0.9; sweep depth 500 vs 4000; `lowpassLadder` in
place of `lowpassSvf` for a steeper, warmer cousin.

## Lesson 5 — LFOs: modulation  (`05-lfo.ges`)

Lesson 4's move — one signal steering a parameter of another — has a name,
**modulation**, and it generalises.  An oscillator too slow to hear (a few
Hz) used only to steer things is an **LFO**, low-frequency oscillator.
Where you point it decides what you get:

```
vibrato : Sig Float
vibrato = sine (220.0 + 4.0 * sine 5.0)      -- LFO into pitch

tremolo : Sig Float
tremolo = 0.6 + 0.4 * unipolar (sine 3.0)    -- LFO into loudness

wah : Sig Float
wah = lowpassSvf (400.0 + 1800.0 * unipolar (sine 0.4)) 0.8 (saw 55.0)

sound : Sig Float
sound = 0.25 * vibrato * tremolo + 0.2 * wah
```

- LFO → pitch is **vibrato**: the frequency argument is itself a signal,
  wobbling ±4 Hz five times a second, the width a singer's vibrato has.
- LFO → loudness is **tremolo**.  `unipolar` shifts −1..1 to 0..1, the
  usual first step when a modulator feeds a depth: `0.6 + 0.4 * …` then
  reads as "between 0.6 and 1.0", the range it sweeps written out.
- LFO → cutoff is an **auto-wah** — lesson 4's sweep, but cyclic.

The general lesson: *anything* that takes a signal can be modulated, and a
patch's life comes almost entirely from slow movement layered onto fast
sound.  When a sound feels static, the fix is usually an LFO somewhere.

## Lesson 6 — drums are shaped noise  (`06-drums.ges`)

Percussion has no pitch to speak of, so oscillators step aside for
**noise** — every frequency at once — and the envelope does almost all of
the work.  Three classic recipes:

```
kick = sine (45.0 + 180.0 * kickEnv) * kickEnv
```

A kick drum is a sine whose *pitch* falls fast — 225 Hz down to 45 in a
few tens of milliseconds (the same envelope again, into the frequency),
which your ear hears as the "boom" tightening into the low thud.

```
hat = highpassSvf 6000.0 0.3 (white 1) * hatEnv
```

A hi-hat is white noise, high-passed so only the sizzle above 6 kHz
remains, with a very fast decay.  `white 1` is white noise; the `1` is a
**seed** choosing which stream of randomness, and two noises that should
not be the same sound (hat and snare) must be seeded apart.

```
snare = (0.7 * white 2 + 0.5 * triangle 180.0) * snareEnv
```

A snare is both at once: a noise burst (the wires) plus a short tone (the
drum head), sharing a medium-fast envelope.

The envelopes run at different rates and offsets — kicks twice a second,
hats four times offset by half a cycle so they land *between* the kicks,
the snare on the backbeat — which is why three multiplications sound like
a groove.  Rhythm, at this level, is just envelope phase.

## Lesson 7 — physical modelling  (`07-pluck-bell.ges`)

Instead of assembling a sound from waves and filters, model the *object*
that makes it and hit it.  Two models, both one call:

```
plucked = string 220.0 2.0 (white 1 * pluckEnv)
```

`string hz decay excitation` is Karplus-Strong — a delay line the length
of one wave at `hz`, fed back through a softening filter, which is
physically what a string is.  You *excite* it with a short burst (a few
milliseconds of noise is the classic pluck) and the string turns that
energy into a note that dies from the top down, exactly as a real string
does.  What you feed it is what it sounds like: try `dust 3 4.0` as the
excitation and it becomes a string being scratched.

```
bell = resonate 660.0 5.0 strike + 0.6 * resonate 1512.0 4.0 strike
     + 0.4 * resonate 2403.0 3.0 strike
```

`resonate hz decay input` is one ringing **mode** — a frequency and how
many seconds it takes to fade.  A struck object is a sum of modes, and the
numbers *are* the instrument: these three are deliberately not multiples
of each other (660, 1512, 2403), and that inharmonicity is precisely what
makes it a bell rather than a note.  Make them 660/1320/1980 and hear it
turn into a plucked tone.  `strike` here is `dust 7 0.5` — random impulses
about every two seconds, each one a strike.

`limit 0.9` guards the sum: resonators ring on top of each other, and a
limiter on the way out is how you let them.

## Lesson 8 — FM  (`08-fm.ges`)

Frequency modulation is vibrato pushed absurd: wobble a sine's phase not
five times a second but at *audio rate*, and the wobble stops being heard
as movement and becomes new frequencies — sidebands — that were in
neither oscillator.  It is the cheapest way to get complex, glassy,
bell-like spectra, and it was the sound of the 1980s (the DX7 is this).

```
env : Sig Float
env = map (t => exp (negate 3.0 * wrap t)) elapsed

voice : Sig Float
voice = pm 220.0 (0.8 * env * sine 308.0)

sound : Sig Float
sound = 0.4 * env * voice
```

`pm carrier mod` is a sine at the carrier frequency with the modulator
added to its phase.  Three numbers matter:

- the **ratio** of modulator to carrier — 308/220 = 1.4, not a whole
  number, so the sidebands are inharmonic and bell-ish.  Whole-number
  ratios (220/440/660…) give harmonic, brassy tones instead.
- the **depth** (0.8 here, in whole turns of phase) — how *bright*.  At 0
  it is a plain sine; useful depths run to about 1.3.
- the depth's **envelope** — the point of the patch.  The same `env`
  scales the depth and the loudness, so the note is brightest at the
  strike and decays toward a pure sine, which is what struck metal does.
  Give brightness a *faster* envelope than loudness and it gets more so.

For four operators with a wiring matrix, `fm` and `Patch` in
`doc/ref/synth.md` scale this idea up; `pm` is the whole concept in one
call.

## Lesson 9 — effects  (`09-effects.ges`)

Everything so far happens in zero space, right at your ear.  Effects are
transformations *after* the instrument, and the first two anyone reaches
for are time-based:

```
dry : Sig Float
dry = string 330.0 1.5 (white 1 * pluckEnv)

sound : Sig Float
sound = brickwall 0.8 (dry + 0.4 * echo 0.375 0.45 dry
                           + 0.3 * reverb 2.0 0.4 dry)
```

- `echo time feedback` — discrete repeats, each quieter.  At 0.375 s the
  repeats are a musical rhythm of their own.
- `reverb decay damp` — thousands of echoes too dense to separate: a
  room.  `decay` is how long the tail lasts, `damp` how fast its top end
  dulls, which is what makes it sound like walls rather than a bucket.

Note the shape of the line: the effects give back only the **wet** signal,
and you *mix* it with the dry — `dry + 0.4 * echo … dry` — so how much
space a sound sits in stays your decision, made with the same `+` and `*`
as everything else.

`brickwall 0.8` is the safety on the way out: a look-ahead limiter that
holds the result under 0.8 no matter what the mix does.  End every patch
that sums several voices with one.  (Its cousin `drive` is the opposite
move — push *into* saturation for warmth and dirt rather than away from
it; try `drive 2.0 dry` and hear the string thicken.)

## Lesson 10 — a piece  (`10-piece.ges`)

Everything at once, plus the one missing ingredient: **a sequence of
pitches**.

```
melody : List Envelope
melody = [ Step 0.0 220.0, Step 0.5 261.63, Step 1.0 329.63, Step 1.5 440.0
         , Step 2.0 392.0, Step 2.5 329.63, Step 3.0 261.63, Step 3.5 293.66 ]

pitch : Sig Float
pitch = map (t => on melody (4.0 * wrap (t / 4.0))) elapsed
```

`on points t` reads a breakpoint list at time `t`: `Step b y` jumps to `y`
at `b` (and `Ramp b y` would slide there instead — a portamento).  Feeding
it *looped* time — `4.0 * wrap (t / 4.0)` cycles 0..4 forever — turns a
breakpoint list into a **step sequencer**: eight pitches, half a second
each, repeating.  One caution the compiler will also give you: the points
must be named as a literal list like this, where `on` can see them — it
compiles the list away, and cannot if the list hides behind a function
argument.

The rest of the file is this course reassembled:

- `lead` — lesson 4's filtered saw, playing `pitch`, its envelope
  retriggering in step with the sequence;
- `bass` — the same sequence at `0.25 * pitch`, two octaves down (octaves
  are ×2, so arithmetic on the pitch signal *is* transposition);
- `kick` and `hat` — lesson 6, landing on and off the beat;
- `echo` on the lead, `reverb` on the mix, `brickwall` at the end —
  lesson 9;
- and a mix that is nothing but `+` and `*`, with the gains chosen so the
  peak stays under 1.  That last discipline has a name — **gain staging**
  — and it is the difference between a mix and a mess.

Run it, then break it: change `melody`'s pitches, halve the loop length,
point the lead's envelope depth somewhere new.  It is eight definitions;
you now know what every one of them does.

---

## Where to go from here

**The next course.**  `doc/intermediate.md` continues from exactly here:
instruments played by scores and keyboards (`voices`, `adsr`, `FromMIDI`),
knobs, stereo, tempo curves, and writing MIDI files — with its lessons in
`examples/intermediate/`.  After it, `doc/advanced.md` builds the toolkit
itself, and `doc/super.md` is a patch book to steal from.

**Play it with your hands.**  These lessons trigger themselves so they need
no hardware, but the real instrument interface is a `voices` bank:

```
voices lead 8 leadVoice : Sig Float

leadVoice : Sig Gate -> Sig Int -> Sig Float
leadVoice gate note = triangle (!keyHz note) * adsr (Adsr 0.01 0.2 0.6 0.3) gate
```

eight copies of a voice, driven by MIDI (`--midi`), each handed *when* it
was struck and released (`Sig Gate`) and *what* (the note).  The `adsr`
is lesson 3's, unchanged — a played gate and a generated one are the
same thing to an envelope; only where the timing comes from is new.
`examples/audio/duet.ges` and `doc/ref/audio.md` are the path in.

**The rest of the toolbox.**  `doc/ref/synth.md` documents every
oscillator, filter and effect, each entry saying what the numbers mean and
what the thing is for.  Read it like a synth's front panel.  The prose
around the code in `examples/audio/` is a second course in itself —
`blip.ges` for what a synth is under these combinators, `scenery.ges` for
a piece with no notes at all, `fmpoly.ges` for full four-operator FM.

**Three gotchas** before they cost you time: there is no `if` (use `case`)
and no unary minus (use `negate x` or `0.0 - x`); a signal definition the
audio engine runs is restricted to what compiles to a fixed graph — the
error messages name the construct they refuse; and when something clips,
turn *down* the inputs to the mix rather than the master — distortion
created early cannot be removed later.
