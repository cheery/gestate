"""Did it click, and where — `fixme.md` F147, `board/done/unheard-output.md`.

*Henri, 2026-08-18, after the pop was found and fixed by measuring it:
"The tool detecting pops may be very useful in future."*  It had been a
scratchpad script all afternoon, which is exactly what
`doc/instruments.md`'s first rule says not to leave it as.

## What a click is, as a number

A click is a **discontinuity**: one sample to the next moves further
than the waveform's own motion can account for.  So the reading is a
ratio, not a threshold — *this step against the steps this program
normally takes* — and that is what makes it work on a drone and on a
snare without being told which it is.

    worst step / settled step

`settled` is a high quantile of the later steps rather than their
maximum, because a program with a genuine transient every bar would
otherwise judge itself against its own loudest moment and find nothing.

**Where it looks matters as much as what it measures.**  Every defect
this was built for is at the *start*: a control arriving late, a fade
spent inside one block, an engine handing over.  So `opening` weighs the
first stretch separately, and that is the number F147 turned on — the
first ten milliseconds ran seven times faster than the settled tone, and
nothing about the whole-file maximum said so.

## What it cannot see

**Whether a click is wrong.**  A square wave is a discontinuity forty
times a second and is not broken; a plucked string is meant to start
abruptly.  This says *there is a step here much larger than this
program's own motion*, and whether that is a defect is a question about
the piece.  Pointing it at a synth that has no business clicking is what
makes the answer mean something — which is the same bargain every row in
`manifesto.md`'s table makes.

And it reads samples, so it knows nothing about the speaker, the room or
the ear.  `Host.tap()` and `GESTATE_HOST_TAP_TO` are where the samples
come from when the question is about a *live* program, and they carry
that blind spot with them.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

#: How much larger than the settled motion a step has to be before it is
#: worth a person's attention.  Three was enough for F147 by a wide
#: margin — the pop measured seven — and it is loose enough that a
#: vibrato or a fast envelope does not trip it.
LOUD = 3.0

#: Which quantile of the later steps counts as "what this program
#: normally does".  Not the maximum: a piece with one real transient
#: would then measure itself against that and find nothing anywhere.
SETTLED = 0.99


@dataclass(frozen=True)
class Click:
    """One step larger than the program's own motion accounts for."""

    #: The frame the step lands on, and the same in seconds.
    frame: int
    at: float
    #: The step itself, and what the program's settled motion is.
    step: float
    settled: float

    @property
    def times(self) -> float:
        """How many times the settled motion this step is."""
        return self.step / self.settled if self.settled else float("inf")

    def __str__(self) -> str:
        return (f"{self.at * 1000:8.2f} ms  frame {self.frame:<8d} "
                f"step {self.step:.5f}  {self.times:.1f}× the settled "
                f"{self.settled:.5f}")


def steps(frames, channels: int = 1) -> list:
    """Sample-to-sample motion, per channel, interleaved back together.

    **Per channel and not across the interleave**, which is the whole
    reason this takes a channel count: a stereo pair read as one stream
    alternates left and right, so a perfectly still signal measures as a
    step of the difference between the channels, every sample.
    """
    if channels <= 1:
        return [abs(frames[i + 1] - frames[i]) for i in range(len(frames) - 1)]
    out = []
    for i in range(len(frames) - channels):
        out.append(abs(frames[i + channels] - frames[i]))
    return out


def settled_step(motion, after: int = 0) -> float:
    """What this program's own motion is, as a high quantile."""
    tail = sorted(motion[after:]) or sorted(motion)
    if not tail:
        return 0.0
    return tail[min(len(tail) - 1, int(len(tail) * SETTLED))]


def clicks(frames, rate: int = 44100, channels: int = 1,
           loud: float = LOUD, ignore: int = 0) -> list:
    """Every step this program cannot account for, loudest first.

    `ignore` is how many frames at the front to leave out of the
    *settled* reading — never out of the search.  The opening is exactly
    where the defects are, so it must be searched; it is a poor witness
    to what the program normally does, so it does not vote.
    """
    motion = steps(list(frames), channels)
    if not motion:
        return []
    floor = settled_step(motion, ignore)
    if floor <= 0:
        return []
    found = [Click(frame=i, at=i / float(rate), step=v, settled=floor)
             for i, v in enumerate(motion) if v > floor * loud]
    return sorted(found, key=lambda c: -c.step)


def opening(frames, rate: int = 44100, channels: int = 1,
            ms: float = 100.0) -> tuple:
    """`(worst step in the first `ms`, the settled step)`.

    **The reading F147 turned on.**  Every defect this was built for is
    at the start — a control arriving late, a fade spent inside one
    block, an engine handing over — and a whole-file maximum says
    nothing about any of them, because a long drone's loudest step is
    somewhere in the middle and perfectly innocent.
    """
    motion = steps(list(frames), channels)
    if not motion:
        return (0.0, 0.0)
    head = max(1, int(rate * ms / 1000.0))
    early = motion[:head] or motion
    return (max(early), settled_step(motion, head))


def read(path, channels: int = 1) -> list:
    """A `GESTATE_HOST_TAP_TO` dump — raw little-endian floats."""
    raw = Path(path).read_bytes()
    return list(struct.unpack(f"<{len(raw) // 4}f", raw))


def main(argv=None) -> int:
    """`python -m gestate.pops <dump> [--rate …]` — did it click?"""
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.pops",
        description="find the steps a program's own motion cannot account "
                    "for — a tap dump, or any raw float32 file")
    ap.add_argument("dump", help="a GESTATE_HOST_TAP_TO file")
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--channels", type=int, default=1)
    ap.add_argument("--loud", type=float, default=LOUD,
                    help=f"times the settled motion (default {LOUD})")
    ap.add_argument("--opening", type=float, default=100.0,
                    help="milliseconds at the front to weigh separately")
    args = ap.parse_args(argv)

    frames = read(args.dump, args.channels)
    if not frames:
        print("nothing in that file")
        return 1
    worst, floor = opening(frames, args.rate, args.channels, args.opening)
    print(f"{len(frames) // max(1, args.channels)} frames, "
          f"{len(frames) / float(args.rate * max(1, args.channels)):.2f} s")
    print(f"the first {args.opening:g} ms: worst step {worst:.5f} "
          f"against a settled {floor:.5f}"
          + (f"  — {worst / floor:.1f}×" if floor else ""))
    found = clicks(frames, args.rate, args.channels, args.loud)
    if not found:
        print("no step this program cannot account for")
        return 0
    print(f"{len(found)} step(s) over {args.loud:g}×, loudest first:")
    for click in found[:10]:
        print(" ", click)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
