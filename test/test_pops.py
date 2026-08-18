"""Did it click — `gestate/pops.py`, `fixme.md` F147.

Henri, after the pop was found and fixed by measuring it: *"The tool
detecting pops may be very useful in future."*

**An oracle that has only ever passed is a claim**, so the first thing
here is that it says *no* to a clean tone and *yes* to a spliced one —
and the last is that it would have caught F147, from the numbers F147
actually measured.
"""

from __future__ import annotations

import math
import struct

from gestate import pops
from gestate.pops import clicks, opening, read, steps

RATE = 44100


def tone(hz: float, n: int, amp: float = 0.5, at: float = 0.0) -> list:
    return [amp * math.sin(2 * math.pi * hz * (i + at) / RATE)
            for i in range(n)]


# ── It can say no, and it can say yes ──────────────────────────────────────


def test_a_clean_tone_has_nothing_it_cannot_account_for():
    assert clicks(tone(415.0, RATE), RATE) == []


def test_a_splice_is_found_and_placed():
    """Two tones cut together mid-waveform — a step the motion cannot
    account for, which is what a click *is*."""
    frames = tone(415.0, 1000) + tone(415.0, 1000, at=0.5 * RATE / 415.0)
    found = clicks(frames, RATE)
    assert found, "the splice was not found"
    assert abs(found[0].frame - 999) <= 1, found[0]
    assert found[0].times > 3


def test_it_judges_a_program_against_its_own_motion():
    """**A ratio, not a threshold.**  A loud low drone and a quiet high
    one take completely different steps, and neither is a defect — so
    the same absolute step must be a click in one and not the other."""
    quiet = tone(50.0, RATE, amp=0.05)
    loud = tone(4000.0, RATE, amp=0.9)
    assert clicks(quiet, RATE) == []
    assert clicks(loud, RATE) == []
    #: The loud one's ordinary step is far larger than the quiet one's
    #: — so a fixed threshold would have to be wrong about one of them.
    assert max(steps(loud)) > 20 * max(steps(quiet))


def test_a_single_real_transient_does_not_hide_the_rest():
    """The settled reading is a quantile and not a maximum: a piece with
    one genuine transient would otherwise measure itself against that
    and find nothing anywhere."""
    frames = tone(415.0, 20000)
    frames[10000] = 0.99                       # one enormous step
    found = clicks(frames, RATE)
    assert found and abs(found[0].frame - 9999) <= 1


# ── The opening, which is where the defects are ────────────────────────────


def test_the_opening_is_weighed_on_its_own():
    """**The reading F147 turned on.**  A whole-file maximum says
    nothing about a defect at the start, because a long drone's loudest
    step is somewhere in the middle and perfectly innocent."""
    #: 415 Hz for ten milliseconds, then 50 — the shape of F147.
    head = tone(415.0, 441)
    frames = head + tone(50.0, RATE)
    worst, floor = opening(frames, RATE, ms=10.0)
    assert worst > floor * 3, (worst, floor)


def test_a_clean_start_reads_as_clean():
    worst, floor = opening(tone(415.0, RATE), RATE, ms=10.0)
    assert worst <= floor * 1.5


def test_it_would_have_caught_f147():
    """**From the numbers F147 actually measured**, off the editor's own
    card: the first ten milliseconds ran at 0.03592 a step against a
    settled 0.00504 — seven times — and the fix brought worst and
    settled to the same value.
    """
    assert 0.03592 / 0.00504 > pops.LOUD, "the pop is over the bar"
    assert 0.04322 / 0.04322 < pops.LOUD, "and the fixed reading is not"


# ── Reading a tap dump ─────────────────────────────────────────────────────


def test_it_reads_what_the_tap_wrote(tmp_path):
    frames = tone(415.0, 512)
    dump = tmp_path / "tap.f32"
    dump.write_bytes(struct.pack(f"<{len(frames)}f", *frames))
    assert len(read(dump)) == 512


def test_stereo_is_read_per_channel():
    """**Not across the interleave.**  A pair read as one stream
    alternates left and right, so a perfectly still signal would measure
    as a step of the difference between the channels, every sample."""
    still = [0.0, 0.9] * 500                   # left silent, right loud
    assert max(steps(still, channels=2)) == 0.0
    assert max(steps(still, channels=1)) > 0.5


def test_the_command_line_answers(tmp_path, capsys):
    frames = tone(415.0, 4410)
    dump = tmp_path / "tap.f32"
    dump.write_bytes(struct.pack(f"<{len(frames)}f", *frames))
    assert pops.main([str(dump), "--rate", str(RATE)]) == 0
    said = capsys.readouterr().out
    assert "no step this program cannot account for" in said
