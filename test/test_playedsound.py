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
            name: str = "polysaw.ges") -> list:
    """Run the instrument, do `gesture` to it, hand back what was heard.

    `gesture(bench)` is called once the sound is running.  The capture
    is everything the player received, as floats.
    """
    out = tmp_path / f"stream{next(_TAKE)}.raw"
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    bench = Workbench(path, rate=RATE, block=64, command=_pacer(out))
    bench.start(seconds=seconds)
    try:
        assert _wait(lambda: bench.live is not None), bench.messages
        # **The score is switched off first.**  `polysaw.ges` plays
        # itself otherwise, and a capture with the piece in it cannot
        # say whose note it heard.
        bench.listen("poly", True)
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
