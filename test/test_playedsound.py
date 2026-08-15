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

**And the C host too**, in the last section, which is the seam nobody
covered: a fake player means `_open_host` finds no card and the
*Python* driver renders, so the sections above are all about
`Transport.fill` and the C loop is what a machine with a sound card
actually runs.  `test_audiohost.py` proves the C host renders what the
engine renders for a synth with no parameters; a key is the case it
cannot make, because a key arrives through the **control block**.
Driven from a press, both drivers now render the same samples to 1e-6 —
with the C fader up, since a session's fade-in is the one difference
between them and is deliberate.

Its own mutation: with `_push_controls` made a no-op, the C host plays
*nothing* and the join fails.  The same mutation against the Python
sections passes, because there the driver pulls its own controls — one
line of evidence that this section covers something the others do not.

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
            name: str = "polysaw.ges", hush: str | None = "poly",
            source: str | None = None) -> list:
    """Run the instrument, do `gesture` to it, hand back what was heard.

    `gesture(bench)` is called once the sound is running.  The capture
    is everything the player received, as floats.

    `source` replaces the example's text, for a piece an edit made.

    `hush` is the bank switched over to the keyboard before the gesture,
    because a file that plays itself cannot say whose note was heard —
    `listen(bank, True)` is the workbench's own words for *the score no
    longer drives it*.  `None` leaves the piece playing, which is what
    the schedule half of the last test wants.
    """
    out = tmp_path / f"stream{next(_TAKE)}.raw"
    path = tmp_path / name
    # `source` is the file to play when it is not the example itself —
    # a piece some *edit* produced, which is the only way to hear
    # whether the edit did what it said.
    path.write_text(source if source is not None
                    else (AUDIO_DIR / name).read_text())
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


# ── Through the C host ──────────────────────────────────────────────────────
#
# The seam the section above names and cannot reach.  A fake player means
# `_open_host` finds no card and the *Python* driver renders, so every
# assertion so far is about `Transport.fill` and none is about the C one —
# and the C host is what a machine with a sound card actually runs.
#
# `test_audiohost.py` proves the C host renders what the engine renders,
# for a synth with no parameters.  A played key is the other half: it
# reaches the sound through the **control block**, which the C loop reads
# and never asks anybody for, so `_push_controls` is the whole of the
# bridge and nothing has ever driven it from a key.
#
# What is re-made here rather than driven is the five-line loop inside
# `_run_host` — a host, and a call per block.  Everything it calls is the
# workbench's own: `_push_controls`, `Workbench.control`, the same engine.
# It is also *deterministic*, which the sections above are not: the press
# lands at a block boundary of this test's choosing rather than whenever a
# thread got there.


def _idle_bench(tmp_path, name: str = "polysaw.ges"):
    """A workbench with everything built and nothing playing.

    `seconds=0.0` starts the driver and gives it no time to render, so
    the engine, the allocators and the keyboard are all real and the
    audio thread is finished with.  What the test drives afterwards is
    the C host, block by block.
    """
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    bench = Workbench(path, rate=RATE, block=64,
                      command=_pacer(tmp_path / f"idle{next(_TAKE)}.raw"))
    bench.start(seconds=0.0)
    assert _wait(lambda: bench.live is not None), bench.messages
    assert _wait(lambda: not bench.playing), "the driver kept going"
    return bench


def _through_c(bench, blocks: int = 60) -> list:
    """Fill `blocks` from a C host, pushing controls as `_run_host` does."""
    import ctypes

    from gestate.audiohost import Host

    engine = bench.live.engine
    # **`fade_in=False`, and it is the one difference between the two
    # drivers.**  A session starts with the C fader down so the card does
    # not pop on the first block; the Python driver has no such ramp.
    # `test_audiohost.py` turns it off for the same reason — a comparison
    # against another renderer is not a comparison of session openings.
    host = Host(channels=engine.channels, rate=RATE,
                controls=len(engine.control_sources),
                directory=bench._directory, fade_in=False)
    host.install(engine)
    bench.host = host
    bench.live.controls = len(host.control)
    got: list = []
    frames = 64
    buffer = (ctypes.c_float * (frames * engine.channels))()
    try:
        for k in range(blocks):
            bench._push_controls(k * frames)
            host.fill(buffer, frames)
            got.extend(buffer)
    finally:
        bench.host = None
        host.close()
    return got


def test_a_key_played_through_the_c_host_is_heard(tmp_path):
    """The join: a press, the control block, the C render loop, samples.

    Every piece of this is covered on its own and the seam is not —
    which is the shape of `fixme.md` F101, two artifacts agreeing in an
    omission while the wire between them is dead.
    """
    bench = _idle_bench(tmp_path)
    try:
        bench.listen("poly", True)
        quiet = _through_c(bench, blocks=20)
        assert not any(quiet), "the C host made a sound nobody asked for"

        assert bench.keyboard.press(60), "the bank took no note"
        got = _through_c(bench, blocks=60)
    finally:
        bench.stop()

    assert any(got), "a key was pressed and the C host played nothing"
    assert heard_note(_tail(got), RATE) == 60


def test_both_drivers_play_the_same_key(tmp_path):
    """The C host and the Python one, same press, same samples.

    `test_audiohost.py` makes this comparison for a synth with no
    parameters, where the control block never moves.  A key is the case
    it cannot make: the value arrives *through* the block, pushed on one
    side and pulled on the other, and two drivers that disagreed about
    when a control lands would differ by exactly one block of envelope —
    audible as a click on every note, and invisible to both halves
    tested apart.
    """
    import ctypes

    left = _idle_bench(tmp_path)
    right = _idle_bench(tmp_path)
    try:
        for bench in (left, right):
            bench.listen("poly", True)
            assert bench.keyboard.press(60)

        through_c = _through_c(left, blocks=40)

        # The Python driver's own loop, the same call per block.
        frames, engine = 64, right.live.engine
        buffer = (ctypes.c_float * (frames * engine.channels))()
        through_python: list = []
        for k in range(40):
            right.transport.fill(buffer, frames, right.control, k * frames)
            through_python.extend(buffer)
    finally:
        left.stop()
        right.stop()

    assert any(through_c) and any(through_python)
    apart = max(abs(a - b) for a, b in zip(through_c, through_python))
    assert apart < 1e-6, f"the two drivers disagree by {apart}"


# ── The band that waits for you ─────────────────────────────────────────────


def test_the_band_plays_along_and_lays_out(tmp_path):
    """`jazz.ges`'s own claim, checked as sound.

    Its header: *"you comp on `keys` — your hands ARE the comping —
    while the horn solos over whatever harmony you hold… **Lift your
    hands and the band lays out** — no idle track, no fallback: a
    rendered take with no player is an honest silence."*

    It was not true, and nothing could tell.  A `hear holds.keys` is
    answered by port *id*; an id is `NewChan`'s in forcing order; and
    the native stream that asks is a different machine from the state
    the model read the ids off.  So the model believed 0 was `horn`
    while the stream asked 0 meaning `keys`, every reading came back
    empty, and the band laid out for ever — a silence indistinguishable
    from the one the file promises when you lift your hands.

    **Listened for in the band's own register**, which is the only
    place the two can be told apart: the file says pitch classes travel
    and registers do not, so the bass answers a chord at 60/64/67 an
    octave and more below it.  A test that merely asked whether
    *something* sounded would hear the keyboardist and pass while the
    band sat out — the first version of this test did exactly that.
    """
    def comp(bench):
        bench.listen("keys", True)
        for note in (60, 64, 67):
            assert bench.keyboard.press(note), "the keys bank took no note"

    def power(got, notes):
        return max(tone_power(got, RATE, 440.0 * 2.0 ** ((n - 69) / 12.0))
                   for n in notes)

    playing = _played(tmp_path, comp, seconds=1.5, name="jazz.ges", hush=None)
    assert any(playing), "nobody played at all"
    hands = power(playing, (60, 64, 67))
    band = power(playing, range(33, 49))
    assert band > hands / 10, (
        f"the hands are heard at {hands:.3f} and the band's own register "
        f"at {band:.5f} — it laid out while somebody was playing")

    laid_out = _played(tmp_path, lambda bench: bench.listen("keys", True),
                       seconds=1.5, name="jazz.ges", hush=None)
    assert not any(laid_out), "the band played with no hands on the keys"


# ── The gesture, the text and the sound, as one thing ───────────────────────


def _with_notes(source: str) -> str:
    """A piece with a score box on it — the two lines a person adds to
    see its notes: what a payload's key and velocity are, and the ask."""
    return (source
            + "\ninstance Notable Pitched where\n"
            + "    noteKey p = case p of\n"
            + "        Pitched k v -> k\n"
            + "    noteVel p = case p of\n"
            + "        Pitched k v -> v\n"
            + "\nnotes score\n")


def test_a_note_dropped_while_it_plays_changes_the_sound_not_the_file(tmp_path):
    """The other half of the same line: the drag **auditions**.

    `spec/north_star.md` — the sound follows the hand and the file on
    disk is untouched until `Ctrl-S`.  A gesture that saved would make
    an experiment permanent; one that only edited the buffer would be
    silent until you saved, which is the opposite of the room this
    editor is.  So this drags a note in a piece that is *sounding* and
    asks for both halves: the engine was rebuilt and handed over while
    it played, and the file on disk still says what it said.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    from gestate.scorebox import key_at

    source = _with_notes((AUDIO_DIR / "duet.ges").read_text())
    held: dict = {}

    class _View:
        saved = True

        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

        def replace(self, text):
            self._text = text
            return True

        def goto(self, line):
            return True

    def drag(bench):
        held["bench"] = bench
        regions = getattr(bench, "note_regions", {})
        assert regions, "the piece was built with no score box to drag"
        chan = sorted(regions)[0]
        roll, _hand = regions[chan]
        seat = session()
        seat.bench, seat.view = bench, _View(source)
        assert seat.touched(chan, 0.5).startswith("line ")
        grabbed = key_at(roll, 0.5)
        down = next(d / 200 for d in range(200, -1, -1)
                    if key_at(roll, d / 200) == grabbed + 4)
        seat.touched(chan, down)
        said = seat.released(chan)
        assert "+4 semitone" in said, said
        # The engine is replaced *while it sounds* — the handover is
        # `apply`'s, mid-render, with the phases migrated.
        assert _wait(lambda: bench.live is not None
                     and bench.live.generation > 0,
                     timeout=25.0), bench.messages[-4:]

    # Long enough that there is still music left to render when the
    # rebuild lands, which is the whole of what is being watched.
    _played(tmp_path, drag, seconds=20.0, name="duet.ges", hush=None,
            source=source)

    bench = held["bench"]
    assert any("applied edit" in m for m in bench.messages), bench.messages
    # **And the file did not move.**  An audition never writes.
    assert (tmp_path / "duet.ges").read_text() == source, \
        "the drag wrote to the disk"


def test_a_dragged_note_is_heard_where_it_was_dropped(tmp_path):
    """**The claim the score box makes** (`spec/north_star.md`,
    acceptance 5), and the reason this file was written before it.

    A hand takes hold of a note in a picture, carries it up a third and
    lets go; the file differs by one number; the piece plays a third
    higher.  Every step of that is checked somewhere else — the atom in
    `test_scorebox.py`, the pitch here — and none of those says the
    whole thing happened.  This does: press, drag, release, render,
    listen.

    `duet.ges` because its bass line is a written literal and its first
    note is 45, which is the note every measurement in this file
    already knows how to hear.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_scorebox import _seated

    from gestate.scorebox import asks, build_rolls, key_at

    source = _with_notes((AUDIO_DIR / "duet.ges").read_text())
    page = asks(source)
    roll = build_rolls(source, page, 22050, 0)[0]
    seat = _seated(source, roll)

    # The first note of the walk, taken hold of by name — the *place* a
    # hand aims at is `test_scorebox.py`'s business, and the two meet
    # at the channel.
    chan = next(iter(seat.bench.note_regions))
    assert seat.touched(chan, 0.5).startswith("line ")
    was = roll.events[seat.holding[1]][3]
    assert was == BASS_NOTE, "the first note of the walk moved"

    # Carry it up a third: four semitones from wherever it was grabbed.
    grabbed = key_at(roll, 0.5)
    down = next(d / 200 for d in range(200, -1, -1)
                if key_at(roll, d / 200) == grabbed + 4)
    seat.touched(chan, down)
    said = seat.released(chan)
    assert "+4 semitone" in said, said

    moved = seat.view.text()
    assert f"Pitched {BASS_NOTE + 4} 90" in moved, "the file did not move"

    got = _played(tmp_path, lambda bench: None, seconds=1.0,
                  name="duet.ges", hush=None, source=moved)
    assert any(got), "the moved piece played nothing"
    heard = heard_note(_voice(got, _onset(got)), RATE)

    assert heard == BASS_NOTE + 4, \
        f"dragged up a third and heard {heard}, not {BASS_NOTE + 4}"
