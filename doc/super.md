# The patch book

No lessons here.  `examples/super/` is six finished sounds, built from
everything the three courses taught, and the intended use is **theft**:
run one, find the block the header says to steal, paste it into your own
file, and bend it until it is yours.  Every patch renders offline and
plays live; most reward `audiolive --watch` left running while you gut
them.

```
$ python -m gestate.audiolive examples/super/hoverdrone.ges
$ python -m gestate.audio     examples/super/acidline.ges -o acid.wav --seconds 16
$ python -m gestate.audioperform examples/super/nightdrive.ges --midi
```

For each patch: what it is, the trick worth taking, and the first numbers
to grab.

---

## `hoverdrone.ges` — the pad that fills the room

A six-saw stack (three pitches × two ears, each ear detuned its own way)
into two filters that breathe on *different* slow clocks, high resonators
struck by `dust`, and a mix that is 65% reverb — which is what "ambient"
means, mechanically.

**Steal:** the `stack` function — a chord as a detune pattern — and the
out-of-phase breathing pair: two LFOs at 0.031 and 0.043 Hz never realign,
so the pad never sits still and never loops.

**Grab first:** `root` (the whole cloud transposes), the two breathe
rates, the wet/dry split in `wet`.

## `acidline.ges` — the squelch

A 303-flavoured sequence: pitch *and* accent as `Step` envelopes over a
two-second loop, a pluck envelope driving a resonant ladder, `drive` on
the way out, echo behind.

**Steal:** the sequencer pair — `on line (loopT t)` for pitch,
`on accent (loopT t)` for per-step gain.  Two lanes on one clock is a
groovebox; add a third lane for filter depth and you have programmed a
real one.  And the actual 303 trick: **the accent multiplies the filter
sweep**, not just the volume.

**Grab first:** the eight pitches (keep them in one key and you cannot
lose), the ladder resonance 0.82, the `drive` amount.

## `bellfield.ges` — struck metal, forever

An FM bell — inharmonic 2→1 pair plus a 3.51× sparkle pair, modulators
decaying faster than carriers — struck in both ears at *different* rates
(0.21 vs 0.17 Hz), pitch stepping through a triad, drowned six seconds
deep in reverb.

**Steal:** the `bell` patch and `ringOf` envelope quad, as a unit — a
bell in data.  And the stereo idea: two ears on incommensurate clocks
cannot line up, so the field never centres.

**Grab first:** the 3.51 (toward 4.0 it turns polite and harmonic), the
strike rates, the reverb depth.

## `dubgate.ges` — the echo that answers

A drum machine — kick, snare, hat, offbeat skank — where the tape echo's
*input* is gated by a step pattern: the delay only hears the last quarter
of the bar, so it answers the band instead of smearing it.  The tape
itself is a `slide` line that warbles and dulls each pass.

**Steal:** `sendGate` — dub is *when* the echo hears, and a gated send
works on any effect you own.  The `tape` function is a second theft: 
`slide` + wobbling position + lowpass in the fold = worn tape, three
lines.

**Grab first:** the send pattern (open it on the snare only; open it one
bar in four), the echo time 0.375 against the 2-second bar, the warble
depth.

## `nightdrive.ges` — the whole band

Eight bars of synthwave through three `voices` banks — ladder bass on
eighths, detuned pad on fifths, a sixteenth arpeggio swimming in echo —
with the arrangement written as one progression (`roots`) bound three
ways by `>>=`.

**Steal:** the arranger.  `roots >>= eighths`, `roots >>= fifth`,
`roots >>= arpBar`: one chord progression, three parts, and changing a
chord changes the band.  That is what scores-as-values buys and it is the
most reusable twelve lines in this book.

**Grab first:** the four roots (45 41 48 43 — go find your own four),
the arp contour in `arpBar`, the echo time against the bpm.

## `machinist.ges` — the ship that thinks

A sound *place*, no notes anywhere: a sample-and-hold computer bleeping
on a whole-tone grid, an engine drone that is brown noise through a comb
with two formants drifting across it — almost a voice, never a word —
and a servo whose pitch is `slew` chasing the S&H staircase: a motor
audibly making up its mind.

**Steal:** the quantiser (`bleepHz` — random through a grid is *tuned*
random, and any scale fits in the `prim_mod_int`), and the servo idiom:
slew-chasing-a-staircase reads as intention, and intention is what makes
a machine a character.

**Grab first:** the S&H clock (9 Hz — at 2 it ponders, at 30 it panics),
the formant centres, the servo's slew rate.

---

## The habits underneath, one last time

Every patch here obeys the same five: gains set on the thickest moment;
`brickwall` (or per-ear brickwalls — it is mono) last and nothing after
it; seeds kept apart wherever two noises must not be the same noise;
every outside number clamped where it enters; and slow modulation on
unrelated clocks wherever a sound must live longer than its loop.  When a
patch of yours sounds wrong in a way you cannot name, check those five
before touching the timbre.

Where to send what you make: `examples/contrib/` is the tree's open door.
