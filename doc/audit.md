# Library audit — what the primitives measure as, against their tin

*2026-08-09.  Every number below is a native-engine render at 48 kHz,
measured with FFT/statistics; the "tin" is each definition's own
docstring in `audio.ges` and `synth.ges`.  The prompt for the audit was
that the examples sounded wrong in places while reading clean — so the
question was put to the layer below them.*

## Verified exact

These matched their documentation to measurement precision, and none
needed a change:

| primitive | claim | measured |
|---|---|---|
| `sine` | pure tone at hz | 440.0 Hz; harmonics −158 dB; amplitude exact |
| `saw` | ramp −1..1 | 1/n harmonics (H2 −5.6 dB); DC +0.0004 |
| `square` | 50 % duty | odd harmonics only (H2 −132 dB); H3 ≈ 1/3 |
| `triangle` | symmetric | odd only; H3 ≈ 1/9 |
| `pm` | phase-mod sine | bit-identical to `sine` at zero modulation |
| `white` | flat, ±1 | mean −0.0001; octave spread 0.40 dB |
| `dust` | ~density events/s, amps 0..1 | Poisson-consistent rate; amps uniform |
| `lowpassOnePole` | 6 dB/oct | −3.0 dB at cutoff; −6 dB/oct |
| `highpassOnePole` | the complement | complement, measured |
| `lowpassSvf` | 12 dB/oct; res 0..1 | −12.9 dB/oct; res 0.9 → +13 dB peak at fc |
| `bandpassSvf` | centred | peak at fc, unity, symmetric skirts |
| `lowpassLadder` | 24 dB/oct | −22 at 8 k (asymptote −24); −12 dB at fc, as four poles give |
| `resonate` | impulse peak ≈ 1; decay = seconds to −60 dB | peak 0.996; t60 1.01 s at 1.0; rings at 440.0 |
| `adsrOf` | linear segments, seconds | every segment and level exact |
| `percOf` | e-foldings per second | e^(−3.5) at 1 s, to four decimals |
| `echo` | repeats at `time`, gain per pass | 0.25 s spacing; 1.0/0.5/0.25 |
| `keyHz`, `centsHz` | 440 at 69; factor per cent | exact |

## Findings

### `string` played flat, each pitch by its own amount — fixed

The tin said a string's pitch is the length of a delay line, a whole
number of samples.  The model was missing half a sample: Karplus-Strong's
averager reads two neighbouring taps, so the loop is `N + 0.5` samples,
and `stringLen`'s `floor` — accidentally the best integer under that bias
— still left the pitch off by up to half a sample of period.  Measured:
`string 440` rang at **438.0 Hz (−8 cents)**, and the error varies with
pitch, so the eight strings of `strings.ges` were each off by a different
few cents — a chord that beats against itself, which is audible exactly
as "something is weird" and hard to attribute.

The fix is the standard one: a first-order tuning allpass inside the loop
(`y[n] = a·x[n] + x[n−1] − a·y[n−1]`, `a = (1−d)/(1+d)`) supplying the
fractional remainder.  Measured after: **110–1760 Hz all within ±0.1
cent**, decay times and peaks unchanged.  The allpass is unity-gain, so
the decay claim ("seconds to −60 dB per round trip") still holds as
measured.

### `reverb` amplified DC by the comb count times the comb gain — fixed

A comb's gain at zero frequency is `1/(1−g)` — about ×17 per comb at a
3.4 s decay — and four of them summed took a harp's harmless wandering
0.005 offset to **0.10 out of the room**, a tenth of the headroom spent
on silence, in every piece that used `reverb` on a plucked or driven
source.  The input is now DC-blocked once (`reverbCombs` carries the
combs; `reverb` is the door).  `drive` deserves its own note: it is the
one stage that *creates* DC — a waveshaper turns asymmetry into offset —
so a `dcBlock` after a drive chain is an amplifier's coupling capacitor,
in one word (`lead.ges` does this now; `quartet.ges` always did).

### `resonate` driven at its own resonance is not a mixing decision

The tin warns that continuous noise is "not the same animal" as an
impulse; measured, the animal at exact resonance is gain **in the
hundreds to thousands** — a peak-normalised discrete resonator
coherently integrates over its whole ring, far beyond the analog-Q
intuition.  `bar.ges` had wired its resonator tube to the bar's own
ringing at the same frequency and spent two thirds of every render
pinned at full scale; no coefficient rescues that wiring, because the
gain scales with the ring it is fed.  Rung by the strike — an impulse,
which the normalisation is *for* — the tube behaves and the mix numbers
mean what they say.

### `pink`'s claim quoted a different implementation — doc corrected

The code is Paul Kellet's *economy* three-pole approximation, with
coefficients quoted for 44.1 kHz; measured at 48 kHz it holds −3 dB/oct
within about ±0.5 dB per octave.  The docstring claimed "a tenth of a
decibel", which is the figure for his seven-state version.  The claim now
matches the code.  Audibly this is nothing; the tin should still tell
the truth.

### The audio fragment's `scan` never consumes input sample 0 — recorded

`out[0]` is the initial state and the fold reads `in[t]` from `t = 1`,
so a filter fed an impulse at exactly `t = 0` stays silent forever — the
sample is not delayed but dropped (`sum |h| = 0`, measured).  Stateless
chains (`map`, `+`, `gain`) pass it.  All three engines agree
bit-identically, so this is the fragment's semantics rather than a bug in
one of them; it is one boundary sample and musically irrelevant, but a
test that excites a filter at `t = 0` will read silence and conclude
wrongly — this audit did, for an afternoon minute.  Left unchanged:
altering it would shift every golden for a sample nobody can hear.

### `limit` overshoots on transients — already on its tin, worth repeating

Its own prose says it approaches the ceiling rather than guaranteeing it,
and measured on drum strikes the overshoot reached full scale — about a
millisecond of flat-top per hit through `safe_sample`'s clamp.  A drum is
nothing but the transients a peak-follower is loosest on, so an offline
render of percussion wants `brickwall` (lookahead, exact, 2 ms of latency
a file does not feel) — `membrane.ges` does now, and `bar.ges`'s
`clip`-after-`limit` note remains the live-path answer.

## How to repeat this

Render the primitive alone through the native path and measure the claim
directly — the whole audit is that sentence.  A single impulse is
`map imp ticks` with `imp n = case n of 1 -> 1.0` (1, not 0 — see the
`scan` note above); a response is Welch-averaged spectra of the filtered
white noise against the same seed unfiltered; a ring time is the envelope
of `resonate` fed that impulse; a pitch is parabolic interpolation over
the FFT peak.  None of it needs more than a page of numpy beside
`audioperform.graph_of` and `audiollvm.run_native`.
