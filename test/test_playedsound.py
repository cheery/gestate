"""A played key, against the sound that comes out.

**The oracle this project has been missing**, named in `roadmap.md`
since stage 10: *"there is no obvious oracle for 'a key was pressed and
a sound came out'; finding one is worth more than more care."*  Every
defect in the live half was found by Henri playing a keyboard while two
thousand tests passed, and the reason is visible in the test files
themselves — `test_audiokeyboard.py` follows a keystroke as far as the
*allocator* and stops one step before sound, `test_audioeditor.py`
follows the bytes as far as the player and never asks what they say.

So this file joins the two ends.  It drives the real `Workbench` with a
fake player, reads the float32 the driver actually wrote, and asks the
one question nothing could ask: **which note is that?**

The answer comes from `audioperform.heard_note`, whose candidate
frequencies are equal temperament from A440 — a fact about music, not
about this compiler.  Asking `keyHz` what it thinks 60 is would make
the oracle agree with the thing it is checking.

What it can and cannot pin: *when* a key lands is wall-clock and not
reproducible, so nothing here asserts a sample index.  What is asserted
is what a person would say about a recording — there is a note in it,
it is the note that was pressed, two keys are two notes, and after
nothing is pressed there is nothing.

**It was checked against a broken instrument before it was believed**,
because an oracle that has never failed is a claim and not a test.  Two
mutations, run by hand: a `Keyboard.press` a semitone out is heard as
61 and fails the note assertion, and a `Workbench.control` that answers
0.0 for everything makes the capture silent and fails the first line of
it.  Both are the defects this file exists for — the wrong note, and no
note.

**One seam it does not reach**, and saying so is the point: a fake
player means `_open_host` finds no card and the *Python* driver renders,
so the C host's own control push is not on this path.  That half is
`test_audiohost.py`, which fills blocks straight from a `Host` and
compares them with the engine's.  Nobody yet plays a key *through the C
host* — the two halves are each covered and their join is not.

**The last section is the one worth having.**  `duet.ges` has claimed
in prose since it was written that *a note is the same thing whether a
schedule or a hand decided it*, and that claim was checked as far as
the allocator, where it is nearly a tautology.  Checked as sound, with
the same bank and the same note and the same velocity, the two takes
agree to three decimal places — and getting there caught a wrong
assumption in this file's own setup first, which is the sort of thing
an ear is for.
"""

from __future__ import annotations

import shutil
import struct
import sys
import time
from pathlib import Path

import pytest

from gestate.audioeditor import Workbench
from gestate.audioperform import heard_note, tone_power

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")

pytestmark = needs_clang

#: Low enough that a capture is a few thousand samples rather than a
#: hundred thousand, high enough that middle C has forty periods in it.
RATE = 8000


def _pacer(out: Path) -> list:
    """A player that swallows the stream into a file as fast as it comes.

    No sleep in it, unlike `test_audioeditor`'s: nothing here is
    checking a rate, and a capture that renders at speed keeps the test
    to a second of wall clock.
    """
    return [sys.executable, "-c",
            "import sys\n"
            "out = open(sys.argv[1], 'wb')\n"
            "while True:\n"
            "    chunk = sys.stdin.buffer.read(4096)\n"
            "    if not chunk: break\n"
            "    out.write(chunk); out.flush()\n",
            str(out)]


#: A capture per run, and not by tidiness: two runs in one test wrote
#: to one path, and the second `_wait` was satisfied by the *first*
#: run's bytes before the second had rendered a sample.  A file that
#: already exists is not evidence that anything has been heard.
_TAKE = __import__("itertools").count()


def _played(tmp_path, gesture, seconds: float = 0.6,
            name: str = "polysaw.ges", hush: str | None = "poly") -> list:
    """Run the instrument, do `gesture` to it, hand back what was heard.

    `gesture(bench)` is called once the sound is running.  The capture
    is everything the player received, as floats.

    `hush` is the bank switched over to the keyboard before the gesture,
    because a file that plays itself cannot say whose note was heard —
    `listen(bank, True)` is the workbench's own words for *the score no
    longer drives it*.  `None` leaves the piece playing, which is what
    the schedule half of the last test wants.
    """
    out = tmp_path / f"stream{next(_TAKE)}.raw"
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    bench = Workbench(path, rate=RATE, block=64, command=_pacer(out))
    bench.start(seconds=seconds)
    try:
        assert _wait(lambda: bench.live is not None), bench.messages
        if hush is not None:
            bench.listen(hush, True)
        gesture(bench)
        assert _wait(lambda: out.exists()
                     and out.stat().st_size >= 4 * int(RATE * seconds / 2),
                     timeout=15.0), "the player received almost nothing"
    finally:
        bench.stop()
    raw = out.read_bytes()
    return list(struct.unpack(f"<{len(raw) // 4}f", raw[:len(raw) // 4 * 4]))


def _wait(predicate, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def _tail(got: list, part: float = 0.5) -> list:
    """The last part of a capture — after whatever was pressed landed."""
    return got[int(len(got) * (1.0 - part)):]


# ── Nothing pressed ─────────────────────────────────────────────────────────


def test_an_instrument_nobody_touches_is_silent(tmp_path):
    """The floor the rest stands on.  A synth whose score is switched off
    and whose keyboard nobody touched must produce silence, or every
    assertion below is about something else."""
    got = _played(tmp_path, lambda bench: None)

    assert got, "the player received nothing at all"
    assert not any(got), "a synth nobody played made a sound"


# ── A key ───────────────────────────────────────────────────────────────────


def test_a_pressed_key_is_heard_as_the_note_that_was_pressed(tmp_path):
    """The claim in one line, and the one nothing could make before."""
    got = _played(tmp_path, lambda bench: bench.keyboard.press(60))

    assert any(got), "a key was pressed and nothing came out"
    assert heard_note(_tail(got), RATE) == 60


def test_the_keyboard_plays_in_tune_with_itself(tmp_path):
    """An octave up is an octave up.  This is the assertion that survives
    every mapping decision `keyHz` could make: whatever 60 is, 72 is
    twice it, and a synth that transposed or detuned its keyboard would
    fail here without the test having to know the frequency."""
    low = _played(tmp_path, lambda bench: bench.keyboard.press(60))
    high = _played(tmp_path, lambda bench: bench.keyboard.press(72))

    heard_low = heard_note(_tail(low), RATE)
    heard_high = heard_note(_tail(high), RATE)
    assert heard_low is not None and heard_high is not None
    assert heard_high - heard_low == 12, (heard_low, heard_high)


def test_two_keys_are_two_notes(tmp_path):
    """A bank has voices, and the point of them is that a chord is a
    chord — one voice stealing the other would sound like the second
    note alone, which is what the allocator tests cannot see."""
    def chord(bench):
        bench.keyboard.press(60)
        bench.keyboard.press(67)

    got = _tail(_played(tmp_path, chord))
    hz = [440.0 * 2.0 ** ((n - 69) / 12.0) for n in (60, 67)]
    powers = [tone_power(got, RATE, f) for f in hz]
    quiet = tone_power(got, RATE, 440.0 * 2.0 ** ((63 - 69) / 12.0))

    assert min(powers) > 8 * quiet, (powers, quiet)


def test_a_released_key_stops_sounding(tmp_path):
    """Press, release, and the tail is quiet — a note that never ends is
    the defect a `gateAt`/`offAt` pair exists to prevent, and it is
    inaudible to every test that stops at the allocator."""
    def press_and_let_go(bench):
        bench.keyboard.press(60)
        time.sleep(0.15)
        bench.keyboard.release(60)

    got = _played(tmp_path, press_and_let_go, seconds=1.2)
    assert any(got), "nothing was heard at all"
    end = got[int(len(got) * 0.8):]
    loud = max(abs(x) for x in got)
    assert max(abs(x) for x in end) < loud / 8, "the note never let go"


# ── The schedule and the hand ───────────────────────────────────────────────
#
# `duet.ges`'s own header makes the claim this section checks, and it has
# been prose for as long as the file has existed:
#
#     **A note is the same thing either way**, and that is the point of
#     the example: only *when it is decided* differs.  One `Allocator`
#     serves both, and the engine cannot tell which of its channels was
#     written by a scheduler and which by a hand.
#
# The engine cannot tell.  Until now, neither could anything else — the
# claim was checked as far as the allocator, where it is nearly a
# tautology, and never as sound, where it is the whole point.


#: `duet.ges`'s bass walks `Pitched 45 90` first — the note the schedule
#: plays at the top of the piece, and the note the hand will play back.
BASS_NOTE, BASS_VEL = 45, 90


def _onset(got: list, floor: float = 0.005) -> int:
    """Where a note starts, so two captures can be compared from it.

    A schedule decides at tick zero and a hand decides whenever the
    thread got there, so the *offset* is not comparable and everything
    after the offset is.  Alignment by onset is what lets the two be
    held to the same window of the same envelope — comparing 50 ms into
    a pluck with 300 ms into one would call a decay a difference.
    """
    for i, x in enumerate(got):
        if abs(x) > floor:
            return i
    return len(got)


def _voice(got: list, at: int, hold: float = 0.25) -> list:
    """A window of a note, from `at`, once the attack has passed."""
    start = at + int(0.03 * RATE)
    return got[start:start + int(hold * RATE)]


def _harmonics(seg: list, note: int, upto: int = 6) -> list:
    """The note's harmonic profile, as fractions of its own total.

    Normalised deliberately: the two takes are at different points of
    the same envelope and a level comparison would be about the
    envelope.  What survives normalisation is *timbre* — which voice
    played it, with which filter open how far — and that is the half a
    wrong routing would change.
    """
    f0 = 440.0 * 2.0 ** ((note - 69) / 12.0)
    powers = [tone_power(seg, RATE, f0 * h) for h in range(1, upto + 1)]
    total = sum(powers) or 1.0
    return [p / total for p in powers]


def _decay_rate(got: list, at: int) -> float:
    """How fast the note is dying, per second, from `at`.

    `duet.ges`'s envelope is `exp(-rate · t)` while a note is held, so
    this reads back the rate the instrument was written with — and it is
    what caught the setup mistake below, because a *sum* of two
    envelopes is not an envelope with either of their rates.
    """
    import math

    def rms(xs):
        return math.sqrt(sum(x * x for x in xs) / max(1, len(xs)))

    first = rms(got[at:at + 400])
    later = rms(got[at + 2800:at + 3200])
    return math.log(first / later) / 0.35 if later > 0 else float("inf")


def test_a_note_is_the_same_whether_a_schedule_or_a_hand_decided_it(tmp_path):
    """`duet.ges`'s header, checked as sound.

    The same bank, the same note, the same velocity, twice: once as the
    piece's own first bass note, once played by hand with the score
    handed off that bank.  Same pitch, same harmonic profile from the
    same point of the envelope, same decay rate.

    **It bit on its first run, and what it caught was this test.**  A
    keyboard plays every bank that *listens*, and `listening.get(bank,
    True)` means a bank nobody has spoken about listens by default — so
    the hand was playing the reed as well as the pluck.  The ear said so
    before the code did: two envelopes summed, 3.5 and 0.6, read back as
    a single decay of 1.63 per second where the schedule's was 3.45.
    With `lead` switched off the two takes agree to **three decimal
    places**, which is why the tolerances below are tight enough to mean
    something.

    What this would catch that nothing else does: a hand note routed to
    the wrong bank, a velocity dropped on the keyboard path, a
    `FromMIDI` instance reading the payload's fields in the other order.
    Every one of those leaves the allocator reporting exactly what it
    should.
    """
    scheduled = _played(tmp_path, lambda bench: None, seconds=1.0,
                        name="duet.ges", hush=None)

    def by_hand(bench):
        # The reed listens unless told otherwise, and this is about the
        # pluck alone — see the docstring; this line is the finding.
        bench.listen("lead", False)
        bench.keyboard.velocity = BASS_VEL
        assert bench.keyboard.press(BASS_NOTE), "the bank took no note"

    played = _played(tmp_path, by_hand, seconds=1.0,
                     name="duet.ges", hush="bass")

    assert any(scheduled), "the piece played nothing"
    assert any(played), "the hand played nothing"

    a_at, b_at = _onset(scheduled), _onset(played)
    one, two = _voice(scheduled, a_at), _voice(played, b_at)
    assert heard_note(one, RATE) == BASS_NOTE, "the schedule was out of tune"
    assert heard_note(two, RATE) == BASS_NOTE, "the hand was out of tune"

    a, b = _harmonics(one, BASS_NOTE), _harmonics(two, BASS_NOTE)
    apart = max(abs(x - y) for x, y in zip(a, b))
    assert apart < 0.02, (f"the same note sounds different by hand: "
                          f"{['%.3f' % v for v in a]} scheduled, "
                          f"{['%.3f' % v for v in b]} played")

    # And it dies the same way.  A note that decayed differently would
    # be the same note through a different voice, or through the same
    # voice with a stale `gateAt` — inaudible to the profile above,
    # which is normalised, and the reason this line is here.
    scored_rate = _decay_rate(scheduled, a_at)
    hand_rate = _decay_rate(played, b_at)
    assert abs(scored_rate - hand_rate) < 0.2, (scored_rate, hand_rate)
