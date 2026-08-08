"""Tempo that varies, and stays invertible.

A piece needs two questions answered, and needs them to be *the same*
answer read in two directions:

    beat_at(t)     what beat is it, at this instant
    time_at(beat)  when does this beat happen

`time_at` is the one that does the work — every note in a score is a tick
position, and scheduling it means asking when it sounds.  `beat_at` is what
a synth modulating against the piece reads, and what a playhead shows.

**Tempo is linear in *time*, not in beat, and that is the whole design.**
The two readings look interchangeable and are not.  With tempo linear in
time, beat is its integral — a quadratic — and a quadratic inverts in
closed form, so `time_at` is the quadratic formula and costs nothing.
With tempo linear in *beat* the integral is a logarithm and the inverse an
exponential, which is still closed-form but no longer agrees with what a
tempo ramp sounds like: a ritardando is something a conductor does over
*seconds*.

What that closed-form inverse buys is not elegance, it is four features:

  * a schedule that is **precomputed** into sample instants, so nothing
    downstream of `audioscore` has to know tempo varies at all;
  * **seeking to a bar**, which needs beat → time;
  * a **bar ruler**, which needs it once per gridline;
  * **looping between bars**, same.

An arbitrary `bpm : Sig Float` has none of them.  It can only be integrated
forward from zero, so a seek is a replay and a schedule cannot be built in
advance.  That is the reason this is an envelope and not a signal.

The construction is ported from a previous project of the author's
(`beet/music.py`), including the trapezoid: a segment's duration comes from
the *average* of its endpoint tempi, `dt = 120·db/(y₀+y₁)`, which is what
integrating a linear ramp gives and not an approximation of it.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass

from .midi import TICKS_PER_BEAT


class TempoError(Exception):
    pass


# ── Envelopes in general ────────────────────────────────────────────────────
#
# A tempo envelope is a *particular* envelope — bpm against beat — read by
# integrating it.  The plain reading is below, and it is the one everything
# other than tempo wants: what value does this curve have here.


def value_on(points, x: float) -> float:
    """`on` — what an envelope reads at `x`.  **Total: it never raises.**

    Clamped at both ends rather than extrapolated or refused.  Before the
    first point it reads the first value and after the last it reads the
    last, so an envelope is a function on the whole line and a caller never
    has to bound its argument.  That is not laziness about errors: the
    argument is nearly always a clock — a beat, an age, a position — and a
    clock *will* run past the end of any envelope written for it.  An
    envelope that raised there would make every use site carry a `clamp`
    that says nothing, and an envelope that extrapolated would send a
    filter cutoff to infinity ten seconds after the note finished.

    `Ramp` interpolates from the previous point; `At` holds the previous
    value and steps.  The flag rides on the *arriving* point, the same way
    a tempo's does, so "be at 0.8 by beat 16" says nothing about beat 17.

    An empty envelope has no value to give and is the one refusal — but it
    is a *construction* error, raised where the envelope is built, not here
    where it is read.
    """
    if not points:
        raise TempoError("an envelope with no points in it has no value")
    if x <= points[0][0]:
        return float(points[0][2])
    for (x0, _r0, y0), (x1, r1, y1) in zip(points, points[1:]):
        # `>=`, so a point's own value is what is read *at* it: `At 8 0.25`
        # means the envelope is 0.25 at 8, not just after it.  With `>` the
        # step landed one segment late and every point read as the value
        # before it — which for a tempo mark is a whole bar at the old
        # tempo.
        if x >= x1:
            continue
        if not r1 or x1 == x0:
            return float(y0)                    # hold, then step at x1
        return float(y0) + (float(y1) - float(y0)) * (x - x0) / (x1 - x0)
    return float(points[-1][2])


@dataclass(frozen=True)
class TempoEnvelope:
    """A piecewise-linear tempo, in four parallel lists.

    Segment `i` runs from `ts[i]` seconds at `beats[i]` beats, starting at
    `bpms[i]` and changing by `ks[i]` bpm per second.

    `bpm` is the whole envelope's tempo when it never changes, and `None`
    when it does — see `samples_of`, which needs to know.
    """

    ts: tuple[float, ...]
    bpms: tuple[float, ...]
    ks: tuple[float, ...]
    beats: tuple[float, ...]
    bpm: int | None

    # ── The two directions ──────────────────────────────────────────────

    def beat_at(self, t: float) -> float:
        """What beat it is, `t` seconds in.

        The integral of `bpm(t)/60` over the segment: linear tempo makes
        beat quadratic in time, which is the fact `time_at` inverts.
        """
        i = max(0, bisect.bisect_right(self.ts, t) - 1)
        dt = t - self.ts[i]
        return self.beats[i] + self.bpms[i] / 60 * dt + self.ks[i] / 120 * dt * dt

    def time_at(self, beat: float) -> float:
        """When `beat` happens, in seconds.

        `beat_at` solved for `dt`.  The `k == 0` case is split out rather
        than left to the quadratic formula because the formula divides by
        `2d`: a constant-tempo segment is the common one, and it is exactly
        the one that would divide by zero.
        """
        i = max(0, bisect.bisect_right(self.beats, beat) - 1)
        s = self.bpms[i] / 60
        d = self.ks[i] / 120
        db = beat - self.beats[i]
        if d == 0.0:
            return self.ts[i] + db / s
        return self.ts[i] + (-s + math.sqrt(s * s + 4 * d * db)) / (2 * d)

    # ── What a schedule actually asks ───────────────────────────────────

    def samples_of(self, tick: int, rate: int) -> int:
        """A tick position as a sample index.

        **A constant tempo takes the integer path, exactly as before.**
        Not an optimisation: `tick * 60 * rate // (bpm * 96)` is what every
        committed schedule in the tree was built with, and routing it
        through `sqrt` and a rounding step would move notes by a sample
        here and there.  Every bit-identity test between the interpreter,
        the block engine and the generated code compares a *rendered
        performance*, so a one-sample shift is a failure — and a real one,
        since the offline render and the live one would then disagree about
        a rhythm, which is what this arithmetic exists to prevent.

        So the envelope changes the answer only for pieces that asked for a
        changing tempo, and every existing piece is untouched.
        """
        if rate <= 0:
            raise TempoError(f"a sample rate of {rate}")
        if self.bpm is not None:
            if self.bpm <= 0:
                raise TempoError(f"a tempo of {self.bpm} bpm")
            return tick * 60 * rate // (self.bpm * TICKS_PER_BEAT)
        # `floor`, not `round`, to match the integer path above: `//` is
        # what a constant tempo does and the two must agree at the tempo
        # where they meet.
        return int(self.time_at(tick / TICKS_PER_BEAT) * rate)

    @property
    def varies(self) -> bool:
        return self.bpm is None


def constant(bpm: int) -> TempoEnvelope:
    """The envelope a piece with a plain `bpm` has.

    Carries the integer through so `samples_of` can use the exact path.
    """
    if bpm <= 0:
        raise TempoError(f"a tempo of {bpm} bpm")
    return TempoEnvelope(ts=(0.0,), bpms=(float(bpm),), ks=(0.0,),
                         beats=(0.0,), bpm=bpm)


def envelope(points) -> TempoEnvelope:
    """Build an envelope from `(beat, ramp, bpm)` points, in beat order.

    `ramp` is a property of the segment *arriving at* this point: `True`
    slides from the previous tempo to this one, `False` holds the previous
    tempo and steps here.  Putting the flag on the arriving point rather
    than the leaving one is what lets a piece say "get to 90 by bar 9"
    without also saying anything about what happens after bar 9.

    A single point is a constant tempo and is returned as one, so a piece
    that writes its tempo as an envelope of one gets the integer path.
    """
    points = [(float(b), bool(r), float(y)) for b, r, y in points]
    if not points:
        raise TempoError("a tempo envelope with no points in it")
    if any(y <= 0 for _b, _r, y in points):
        raise TempoError("a tempo envelope must be positive throughout")
    if any(a[0] > b[0] for a, b in zip(points, points[1:])):
        raise TempoError("a tempo envelope's points must be in beat order")

    if len(points) == 1 or all(y == points[0][2] for _b, _r, y in points):
        whole = points[0][2]
        if whole.is_integer():
            return constant(int(whole))

    beats = [b for b, _r, _y in points]
    bpms = [y for _b, _r, y in points]
    ks: list[float] = []

    # Where the first point falls, if the piece does not start at beat 0:
    # the tempo before it is the first tempo, held.
    ts = [60 * beats[0] / bpms[0]]
    for i in range(len(points) - 1):
        db = beats[i + 1] - beats[i]
        if points[i + 1][1]:
            # The trapezoid: a linear ramp covers `db` beats in the time
            # the *average* of its two tempi would.
            dt = 120 * db / (bpms[i] + bpms[i + 1])
            ks.append((bpms[i + 1] - bpms[i]) / dt if dt > 0 else 0.0)
        else:
            dt = 60 * db / bpms[i]
            ks.append(0.0)
        ts.append(ts[-1] + dt)
    ks.append(0.0)

    if ts[0] > 0.0:
        ts.insert(0, 0.0)
        bpms.insert(0, bpms[0])
        ks.insert(0, 0.0)
        beats.insert(0, 0.0)

    return TempoEnvelope(tuple(ts), tuple(bpms), tuple(ks), tuple(beats),
                         bpm=None)
