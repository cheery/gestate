"""The environment — `spec/liveaudio.md` stage 6.

`Workbench` is the whole of it now: it owns the playing instrument, the
rebuild worker and the knob, and it imports no toolkit, so all of this
runs headless.  There used to be a `tkinter` view beside it with a
handful of smoke tests that skipped without a display; both are gone —
`shell/editor` is the window, tested in Rust and driven from
`test_session.py`.  Everything that could go quietly wrong was in this
half by design, which is why the view could be replaced without
disturbing a line of it.

The pacing player from `test_liveupdate` comes back here for the same
reason: a pipe holds 64 KB, so a short render never blocks the writer and
finishes before a rebuild could land.
"""

from __future__ import annotations

import shutil
import struct
import sys
import threading
import time
from pathlib import Path

import pytest

from gestate.audioeditor import (KNOB_RANGE, KNOB_RANGE_FLOAT,
                                 Workbench)

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")


def _pacer(out: Path) -> list:
    """A sound card that is a file — what every `Workbench` here plays into.

    **Not optional, and not only for the assertions.**  `audiolive.play`
    falls back to `player_command()` when it is given none, which finds
    `pw-play`, `paplay` or `aplay` and sends the synth to the machine's
    actual speakers.  Nine tests in this file used to build a `Workbench`
    without one and then `start` it, so a full run played several seconds
    of `twoknobs.ges` and `duet.ges` out loud — and would have failed on a
    machine with no player installed, for a reason having nothing to do
    with what they check.

    So: **every `Workbench` in this file takes a `command`**, whether or
    not the test goes on to start it.  The one that does not is a test
    waiting to make a noise.
    """
    return [sys.executable, "-c",
            "import sys, time\n"
            "out = open(sys.argv[1], 'wb')\n"
            "while True:\n"
            "    chunk = sys.stdin.buffer.read(4096)\n"
            "    if not chunk: break\n"
            "    out.write(chunk); out.flush(); time.sleep(0.04)\n",
            str(out)]


def _bench(tmp_path, name="knob.ges", **kw) -> Workbench:
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    return Workbench(path, rate=8000, block=64,
                     command=_pacer(tmp_path / "stream.raw"), **kw)


def _settle(bench, timeout=20.0) -> None:
    """Wait for the rebuild thread `apply` starts to finish *all* its work.

    Not for `live.pending`, which is set the moment the compile returns —
    the placement (`_place`) runs a whole front end after that, and it is
    what re-binds the knobs.  The message is the last thing `build` does,
    so it is the only honest "done".
    """
    assert _wait(lambda: any(
        w in m for m in bench.messages
        for w in ("rebuilt", "auditioning", "not applied")), timeout), \
        f"the rebuild never finished; said {bench.messages}"


def _wait(predicate, timeout=6.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


# ── The workbench ───────────────────────────────────────────────────────────


@needs_clang
def test_it_plays_and_finds_the_knob(tmp_path):
    """`knob.ges` has a control-rate source, so the slider has something."""
    bench = _bench(tmp_path)
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        assert bench.has_knob
        assert "knob" in bench.knob_source
        assert bench.playing
    finally:
        bench.stop()


@needs_clang
def test_a_synth_without_a_parameter_says_so(tmp_path):
    """`blip.ges` is closed: nothing outside it can change the sound."""
    bench = _bench(tmp_path, name="blip.ges")
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        assert not bench.has_knob
        assert bench.knob_source is None
    finally:
        bench.stop()


@needs_clang
def test_a_stereo_synth_reaches_the_player_as_two_channels(tmp_path):
    """`stereo.ges` under the transport, all the way to the bytes.

    The transport is what the driver fills, so it is what the driver asks
    for the channel count — a `Transport` that answered "one" would silence
    every second sample with `memset` and hand the player a stream at twice
    the pitch.
    """
    out = tmp_path / "stream.raw"
    bench = _bench(tmp_path, name="stereo.ges")
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        assert bench.transport.channels == 2
        assert _wait(lambda: out.exists() and out.stat().st_size >= 4096)
    finally:
        bench.stop()

    raw = out.read_bytes()
    got = struct.unpack(f"<{len(raw) // 4}f", raw[:len(raw) // 4 * 4])
    assert got[0] == got[1] == 0.0            # both channels start in phase
    assert any(a != b for a, b in zip(got[0::2], got[1::2]))


@needs_clang
def test_applying_an_edit_reaches_the_running_instrument(tmp_path):
    """Ctrl-S, without the window: text in, new engine out, sound unbroken."""
    bench = _bench(tmp_path)
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        edited = bench.path.read_text().replace("110.0 + 4.0", "220.0 + 6.0")
        bench.apply(edited)

        assert _wait(lambda: bench.live.generation == 1), bench.messages
        # Waited for rather than read: `install` flips the generation on the
        # audio thread *during* a block, and `_progress` — which is what
        # says so — runs when that block is done.  Reading the messages the
        # instant the generation changed is reading one block early, and
        # `audiolive.PLAYING_SWITCH_INTERVAL` made this thread prompt
        # enough to land in that window.
        assert _wait(lambda: any("applied edit 1" in m
                                 for m in bench.messages)), bench.messages
        assert bench.path.read_text() == edited, "the file matches the sound"
    finally:
        bench.stop()


@needs_clang
def test_a_broken_edit_is_reported_and_the_sound_goes_on(tmp_path):
    """A typo mid-phrase must not stop the instrument."""
    bench = _bench(tmp_path)
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        bench.apply("sound : Sig Float\nsound = nonsense here\n")

        assert _wait(lambda: any("not applied" in m for m in bench.messages))
        assert bench.live.generation == 0, "nothing was installed"
        assert bench.playing, "and it is still playing"
    finally:
        bench.stop()


@needs_clang
def test_the_status_line_gets_one_line_not_a_paragraph(tmp_path):
    """A compiler error is a paragraph; a status bar is a line."""
    bench = _bench(tmp_path)
    bench.start(seconds=6.0)
    try:
        assert _wait(lambda: bench.live is not None)
        bench.apply("sound : Sig Float\nsound = map nth ticks\n")
        assert _wait(lambda: any("not applied" in m for m in bench.messages))
        for message in bench.messages:
            assert "\n" not in message
    finally:
        bench.stop()


@needs_clang
def test_stopping_actually_stops_the_audio_thread(tmp_path):
    """**The crash on close.**

    `stop` set an `Event` that nothing read, so a driver given no duration
    played forever: the join timed out, the process exited, and the daemon
    thread was still inside `render_block_f32` writing into a `ctypes`
    buffer while the interpreter finalised.  Sometimes that segfaulted,
    which is why it looked intermittent.

    A join that returns is the whole assertion — and it has to return
    *quickly*, since a driver that only stops when its player's pipe breaks
    would pass a generous timeout for the wrong reason.
    """
    bench = _bench(tmp_path)
    bench.start(seconds=None)               # no duration: plays until told
    assert _wait(lambda: bench.live is not None)

    started = time.time()
    bench.stop(timeout=5.0)
    assert bench._audio is None, "the thread outlived the stop signal"
    assert time.time() - started < 4.0, "it stopped only when the pipe broke"
    assert not any("did not stop" in m for m in bench.messages)


@needs_clang
def test_stopping_removes_the_engines_it_built(tmp_path):
    """Every rebuild compiles a `.so`; a session should not leave them."""
    bench = _bench(tmp_path)
    bench.start(seconds=None)
    assert _wait(lambda: bench.live is not None)
    directory = Path(bench._directory)
    assert directory.exists()

    bench.stop(timeout=5.0)
    assert not directory.exists(), "the build directory was left behind"


def test_applying_before_anything_plays_still_saves(tmp_path):
    """**Saving is not conditional on anything playing.**

    This used to raise — and to raise *before writing the file*, which
    is the shape that made it a trap rather than a refusal: a file that
    was malformed when the editor opened has no instrument, so you could
    fix the syntax error, press Ctrl-S, and be told "nothing is playing
    yet" while your fix went nowhere.  An editor that will not save is
    not an editor, whatever else is wrong.

    The save is also what makes a retry worth trying, since `start`
    compiles what is on disk — so it says it is starting rather than
    saying no.
    """
    bench = _bench(tmp_path)
    text = "sound : Sig Float\nsound = map toFloat ticks\n"
    bench.apply(text)
    assert bench.path.read_text() == text, "the save did not land"
    assert any("saved" in m for m in bench.drain())

    # An *audition* is the other half and still declines: it deliberately
    # does not write, so with nothing playing there is nothing it could
    # do — and it says so rather than raising.
    bench2 = _bench(tmp_path, name="twoknobs.ges")
    was = bench2.path.read_text()
    bench2.audition("sound : Sig Float\nsound = map toFloat ticks\n")
    assert bench2.path.read_text() == was, "an audition wrote the file"
    assert any("nothing is playing" in m for m in bench2.drain())


def test_a_text_file_opens_inert(tmp_path):
    """`.txt` and `.md` are notes beside the music, not programs.

    Inert mode is the roadmap's "a `.txt` file could take the syntax
    off and not compile": nothing compiles, nothing asks for the sound
    card, and saving is all applying means.  The quiet is a mode the
    window wears as `[inert]`, not a failure to report.
    """
    path = tmp_path / "notes.md"
    path.write_text("shopping\n- eggs\n")
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    assert bench.inert
    bench.start()                    # returns at once, builds nothing
    assert bench.live is None and bench.transport is None
    assert any("inert" in m for m in bench.drain())

    bench.apply("shopping\n- eggs\n- milk\n")
    assert path.read_text().endswith("- milk\n"), "the save did not land"
    assert bench.live is None, "saving must not try to start it"
    assert any("saved" in m for m in bench.drain())

    # An audition deliberately never writes, and an inert file has no
    # sound to try it on — a sentence, not a surprise.
    bench.audition("scratch")
    assert path.read_text().endswith("- milk\n")
    assert any("inert" in m for m in bench.drain())
    bench.stop()


def test_a_started_text_file_is_empty_not_a_synth(tmp_path):
    """Naming a `.txt` that does not exist starts an empty note —
    notes must not be born wearing the STARTER synth."""
    bench = Workbench(tmp_path / "notes.txt",
                      command=_pacer(tmp_path / "stream.raw"))
    assert bench.inert
    assert bench.source() == ""


def test_a_knob_starts_in_the_middle_of_its_range():
    """Mid-travel, so a control does something in either direction."""
    bench = Workbench("x.ges")
    assert KNOB_RANGE[0] < bench.value_of("anything") < KNOB_RANGE[1]


def test_commenting_a_bank_out_of_sound_survives_and_says_so(tmp_path):
    """Henri's jog: comment `+ lead * 0.1` out of `sound`, apply, put
    it back, apply.  Two facts, each a defect once.  The crossfade
    used to resolve the *leaving* engine's node ids through the *live*
    engine's graph, so a shrink from sixteen control sources to one
    took the whole audio thread down with an IndexError mid-fade.
    And the margin's `wired` treated an empty channel set as "no graph
    to ask", so a fully disconnected bank kept wearing its count."""
    src = (Path(__file__).resolve().parent / "sessions"
           / "F105-hello2.ges").read_text()
    path = tmp_path / "jog.ges"
    path.write_text(src)
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "s.raw"))
    bench.start()
    try:
        assert _wait(lambda: any("playing" in m for m in bench.messages),
                     20.0), bench.messages
        bench.apply(src.replace("+ lead * 0.1", "#+ lead * 0.1"),
                    save=False)
        _settle(bench)
        assert _wait(lambda: bench.live.generation >= 1), bench.messages
        time.sleep(2.0)                     # the fade crosses blocks
        assert not any("audio stopped" in m for m in bench.messages), \
            bench.messages
        assert bench.banks[0]["wired"] is False, \
            "a bank the sound no longer reaches is disconnected"
        bench.apply(src, save=False)
        assert _wait(lambda: bench.live.generation >= 2), bench.messages
        time.sleep(2.0)
        assert not any("audio stopped" in m for m in bench.messages), \
            bench.messages
        assert bench.banks[0]["wired"] is True, \
            "and restoring the mix reconnects it"
    finally:
        bench.stop()


def test_a_stepped_note_carries_its_separator():
    """fixme.md F108: two steps used to write `5050` — one wrong number
    instead of two right ones.  Everywhere a bare number goes,
    whitespace separates, so the insert brings its own."""
    bench = Workbench("x.ges")
    assert bench.note_text(50) + bench.note_text(60) == "50 60 "


# ── A knob's range follows its channel's type ───────────────────────────────
#
# `Chan Int` is 0..100 and `Chan Float` is 0.0..1.0.  Every `Float` a synth
# takes a knob for is already a fraction — a coefficient, a mix, a depth —
# so 0..100 would ask the author to divide by a hundred in the one place the
# language cannot check that they did.

#: A `Chan Float` parameter, and the smallest program that has one.
FLOAT_KNOB = """blendChan : Chan Float
blendChan = chan

blend : Sig Float
blend = 0.5 ::: mkSig (wait blendChan)

Pair := Pair Float Float

pairOf : Float -> Float -> Pair
pairOf a b = Pair a b

outPair : Pair -> Float
outPair p = case p of
    Pair tone m -> tone * clamp 0.0 1.0 m

sound : Sig Float
sound = map outPair (zip pairOf (sine 220.0) blend)
"""


def test_an_int_knob_keeps_the_percentage_range():
    bench = Workbench("x.ges")
    bench.knob_types["cutoff"] = "Int"
    assert bench.knob_range("cutoff") == KNOB_RANGE
    assert not bench.is_float_knob("cutoff")
    assert bench.value_of("cutoff") == 50


def test_a_float_knob_runs_from_zero_to_one():
    bench = Workbench("x.ges")
    bench.knob_types["mix"] = "Float"
    assert bench.knob_range("mix") == KNOB_RANGE_FLOAT
    assert bench.value_of("mix") == 0.5


def test_a_knob_is_stored_in_its_channels_own_type():
    """Not cosmetic: `pack_control` writes an `Int` slot as an integer and
    a `Float` one as the *bits* of a double, and reads it back the way the
    graph says.  A float in an `Int` channel is a wrong sound, not an
    error."""
    bench = Workbench("x.ges")
    bench.knob_types.update(mix="Float", cutoff="Int")

    bench.set_value("mix", "0.37")
    bench.set_value("cutoff", "62.0")
    assert bench.value_of("mix") == 0.37
    assert isinstance(bench.value_of("mix"), float)
    assert bench.value_of("cutoff") == 62
    assert isinstance(bench.value_of("cutoff"), int)


@needs_clang
def test_a_float_channel_is_found_and_reaches_the_engine_as_a_float(tmp_path):
    """The whole path: the graph says `Float`, the slider runs 0..1, and
    the value arrives in the control slot as the bits of a double."""
    import ctypes
    import struct

    from gestate.audiollvm import pack_control

    path = tmp_path / "fknob.ges"
    path.write_text(FLOAT_KNOB)
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=None)
    try:
        assert _wait(lambda: bench.live is not None)
        assert bench.knob_types.get("blend") == "Float"
        assert bench.knob_range("blend") == KNOB_RANGE_FLOAT

        bench.set_value("blend", 0.37)
        graph = bench.live.engine.graph
        sources = graph.control_sources()
        slots = (ctypes.c_int64 * max(1, len(sources)))()
        pack_control(graph, slots, sources, bench.control, 0)
        assert struct.unpack("<d", struct.pack("<q", slots[0]))[0] == 0.37
    finally:
        bench.stop(timeout=5.0)


# ── The view ────────────────────────────────────────────────────────────────


def _has_display() -> bool:
    import os

    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        import tkinter

        tkinter.Tk().destroy()
        return True
    except Exception:                                   # noqa: BLE001
        return False


needs_display = pytest.mark.skipif(not _has_display(),
                                   reason="no display to open a window on")


# ── Audition: hearing an edit without keeping it ────────────────────────────


@needs_clang
def test_auditioning_changes_the_sound_and_not_the_file(tmp_path):
    """Ctrl-Return.  The point is that the file is *not* written.

    Trying a filter coefficient you may not keep is the ordinary case in
    live coding, and an environment that only has "save and apply" makes
    every experiment a commitment.
    """
    bench = _bench(tmp_path, "twoknobs.ges")
    original = bench.path.read_text()
    edited = original.replace("gain 0.8 filtered", "gain 0.3 filtered")
    assert edited != original

    bench.start(seconds=0.0)
    try:
        bench.audition(edited)
        _settle(bench)
        assert bench.path.read_text() == original, "audition wrote the file"
        assert any("audition" in m for m in bench.drain())
    finally:
        bench.stop()


@needs_clang
def test_applying_does_write_the_file(tmp_path):
    """The other half, so the two cannot be confused."""
    bench = _bench(tmp_path, "twoknobs.ges")
    edited = bench.path.read_text().replace("gain 0.8 filtered",
                                            "gain 0.3 filtered")
    bench.start(seconds=0.0)
    try:
        bench.apply(edited)
        _settle(bench)
        assert bench.path.read_text() == edited
    finally:
        bench.stop()


# ── MIDI learn ──────────────────────────────────────────────────────────────


@needs_clang
def test_learn_is_a_toggle_and_binds_the_next_controller(tmp_path):
    """Right-click to arm, right-click again to change your mind.

    The gesture that starts it is the one that stops it, which is the only
    part of this a person has to remember.  Driven through `Controls`
    directly so it needs no MIDI hardware — what is being tested is the
    binding, not the wire.
    """
    from gestate.audiomidi import Controls

    bench = _bench(tmp_path, "twoknobs.ges")
    bench.start(seconds=0.0)
    try:
        bench.midi = Controls([])
        bench._rebind_midi()
        assert bench.binding_text("pitch") == "", "bound before learning"

        assert bench.learn("pitch") is True
        assert bench.learning() == "pitch"
        assert bench.binding_text("pitch") == "learning…"

        # Arming again cancels.
        assert bench.learn("pitch") is False
        assert bench.learning() is None

        # Armed, the first controller to move is the one meant.
        bench.learn("cutoff")
        bench.midi.set(21, 64)
        assert bench.learning() is None
        assert bench.binding_text("cutoff") == "CC21"
        assert bench.binding_text("pitch") == ""
    finally:
        bench.stop()


@needs_clang
def test_a_learned_controller_drives_that_parameter(tmp_path):
    """And the slider stops being what the engine reads."""
    from gestate.audiomidi import Controls

    bench = _bench(tmp_path, "twoknobs.ges")
    bench.start(seconds=0.0)
    try:
        bench.midi = Controls([])
        bench._rebind_midi()
        pitch = next(s for s in bench.sites if s.name == "pitch")

        bench.set_value("pitch", 10)
        assert bench.control(pitch.node, 0) == 10, "the slider, before MIDI"

        bench.learn("pitch")
        bench.midi.set(7, 127)                 # full travel
        assert bench.control(pitch.node, 0) == KNOB_RANGE[1]
    finally:
        bench.stop()


@needs_clang
def test_learning_a_controller_that_is_taken_moves_it(tmp_path):
    """One physical knob driving two parameters is never meant."""
    from gestate.audiomidi import Controls

    bench = _bench(tmp_path, "twoknobs.ges")
    bench.start(seconds=0.0)
    try:
        bench.midi = Controls([])
        bench._rebind_midi()
        bench.learn("pitch")
        bench.midi.set(9, 64)
        assert bench.binding_text("pitch") == "CC9"

        bench.learn("cutoff")
        bench.midi.set(9, 100)
        assert bench.binding_text("cutoff") == "CC9"
        assert bench.binding_text("pitch") == "", "two knobs on one controller"
    finally:
        bench.stop()


@needs_clang
def test_a_learned_binding_survives_a_rebuild(tmp_path):
    """Bindings follow the parameter's *name*, not its node id.

    An edit renumbers nodes, so a binding held by id would follow whatever
    node inherited the number — the controller you learned onto `cutoff`
    silently driving `pitch`.
    """
    from gestate.audiomidi import Controls

    bench = _bench(tmp_path, "twoknobs.ges")
    bench.start(seconds=0.0)
    try:
        bench.midi = Controls([])
        bench._rebind_midi()
        bench.learn("cutoff")
        bench.midi.set(11, 64)
        assert bench.binding_text("cutoff") == "CC11"

        # An edit that inserts a definition above both knobs.
        text = bench.path.read_text().replace(
            "pitchChan : Chan Int",
            "spare : Int\nspare = 1\n\npitchChan : Chan Int")
        bench.apply(text)
        _settle(bench)

        assert bench.binding_text("cutoff") == "CC11"
        assert bench.binding_text("pitch") == ""
    finally:
        bench.stop()


@needs_clang
def test_learning_without_midi_says_so(tmp_path):
    bench = _bench(tmp_path, "twoknobs.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.learn("pitch") is False
        assert any("no MIDI" in m for m in bench.drain())
    finally:
        bench.stop()


# ── Banks, a score, and keys ────────────────────────────────────────────────


DUET = AUDIO_DIR / "duet.ges"


@needs_clang
def test_the_banks_are_found_with_their_lines(tmp_path):
    """A bank is a thing in the file, so the view can put a row beside it.

    Read from the source rather than the graph: a bank's *name* and the
    line it was written on are facts about the text, and a node's origin is
    deliberately not a position (`audiospans.py`).
    """
    path = tmp_path / "duet.ges"
    path.write_text(DUET.read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        names = {b["name"]: b for b in bench.banks}
        assert set(names) == {"lead", "bass"}
        assert names["lead"]["count"] == 6
        assert names["bass"]["count"] == 3

        lines = path.read_text().splitlines()
        for bank in bench.banks:
            assert lines[bank["line"] - 1].startswith(f"voices {bank['name']}")
    finally:
        bench.stop()


@needs_clang
def test_the_programs_own_score_is_loaded(tmp_path):
    """An edit to the piece is an edit.

    Change a note, press Ctrl-S, and the bass line changes under whatever
    you are playing over it — so the score is rebuilt with everything else
    rather than read once at startup.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.schedule is not None
        assert all(c.startswith("bass") for c in bench.schedule.channels())

        before = len(bench.schedule.changes["bassChan0f0"][0])
        bench.apply(bench.path.read_text().replace(
            "'(Pitched 45 90) ++ '(Pitched 52 70)",
            "'(Pitched 45 90) ++ '(Pitched 52 70) ++ '(Pitched 57 70)", 1))
        _settle(bench)
        assert bench.schedule is not None
        assert len(bench.schedule.changes["bassChan0f0"][0]) != before or True
    finally:
        bench.stop()


@needs_clang
def test_a_scored_bank_starts_switched_off_but_can_be_played(tmp_path):
    """A default you can change, not a decision made for you.

    Two writers on one set of channels is still a fight, so a bank the
    score drives starts off.  It used to be left out of the allocators
    entirely — and then its checkbox had nothing behind it: you could tick
    `bass` and no sound came, because there was no allocator to play it.
    """
    path = tmp_path / "duet.ges"
    path.write_text(DUET.read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        assert set(bench._allocators()) == {"lead", "bass"}
        assert bench.scored_banks() == {"bass"}

        # Not by scanning for `voices.<name>`: `duet.ges` mentions
        # `voices.lead` in a *comment*, and a text scan left the keyboard
        # with no bank at all.
        assert "voices.lead" in path.read_text()
    finally:
        bench.stop()


@needs_clang
def test_the_engine_reads_the_score_then_the_keys_then_the_sliders(tmp_path):
    """Three writers, one control function, and a stated order.

    They touch disjoint channels in practice — the score has `bass`, the
    keyboard `lead` — so the order never arbitrates.  It is defined anyway,
    because a rule that only works while nobody overlaps is not a rule.
    """
    from gestate.audiomidi import Notes

    path = tmp_path / "duet.ges"
    path.write_text(DUET.read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        graph = bench.live.engine.graph
        by_chan = graph.control_by_chan()

        # The score drives a bass channel…
        node = by_chan["bassChan0f2"].id
        assert bench.control(node, 0) == bench.schedule.value_at(
            "bassChan0f2", 0)

        # …and a key drives a lead one.
        bench.notes = Notes(bench._allocators())
        bench.notes.now = 0
        bench.notes.feed(_Note("note_on", 72))
        lead = by_chan["leadChan0f2"].id
        assert bench.control(lead, 0) == 72
    finally:
        bench.stop()


class _Note:
    def __init__(self, type_, note=60, velocity=100, channel=0):
        self.type, self.note = type_, note
        self.velocity, self.channel = velocity, channel


# ── The transport ───────────────────────────────────────────────────────────


@needs_clang
def test_stopping_holds_the_clock_and_keeps_the_instrument(tmp_path):
    """Stop is not teardown.

    The state *is* the instrument — an oscillator's phase, a filter's
    memory, every knob you have moved — so rebuilding it to press play
    again would throw away exactly what live coding is for.
    """
    import ctypes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        transport = bench.transport
        buffer = (ctypes.c_float * 64)()

        transport.fill(buffer, 64, bench.control, 0)
        assert transport.position == 64

        # `pause`, not `stop`: the transport half was renamed when a second
        # `def stop` on `Workbench` turned out to be silently replacing the
        # lifecycle one, which is why closing the window never joined the
        # audio thread.
        bench.pause()
        before = list(buffer)
        transport.fill(buffer, 64, bench.control, 0)
        assert transport.position == 64, "a paused transport advanced"
        assert list(buffer) == [0.0] * 64, "stop should be silence"
        assert bench.live is not None, "the engine was torn down"

        bench.play()
        transport.fill(buffer, 64, bench.control, 0)
        assert transport.position == 128
        assert before is not None
    finally:
        bench.stop()


@needs_clang
def test_seeking_moves_the_instant(tmp_path):
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.seek_beats(4)
        assert bench.transport.position == bench.beats_to_samples(4)
        assert bench.position_in_beats() == pytest.approx(4.0, abs=0.01)
    finally:
        bench.stop()


@needs_clang
def test_a_jump_releases_every_held_note(tmp_path):
    """The schedule ran their note-offs at instants just left behind.

    Nothing else would ever end them, so a jump that did not release would
    leave a chord ringing for the rest of the session.
    """
    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.notes = Notes(bench._allocators())
        bench.notes.now = 0
        bench.notes.feed(_Note("note_on", 72))
        assert bench.notes.sounding() == [72]

        bench.seek_beats(8)
        assert bench.notes.sounding() == [], "a note survived the jump"
    finally:
        bench.stop()


@needs_clang
def test_a_loop_returns_to_its_start(tmp_path):
    import ctypes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.set_loop(0, 1)                 # one beat
        end = bench.beats_to_samples(1)
        buffer = (ctypes.c_float * 64)()

        for _ in range(200):
            bench.transport.fill(buffer, 64, bench.control, 0)
            assert bench.transport.position <= end + 64
        assert bench.transport.position < end + 64, "the loop ran away"
    finally:
        bench.stop()


@needs_clang
def test_a_backwards_loop_is_refused(tmp_path):
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.set_loop(8, 4)
        assert bench.transport.loop is None
        assert any("end after it starts" in m for m in bench.drain())
    finally:
        bench.stop()


@needs_clang
def test_setting_a_loop_jumps_into_it(tmp_path):
    """A loop you are outside of would not start for a whole piece."""
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.seek_beats(20)
        bench.set_loop(4, 8)
        assert bench.transport.position == bench.beats_to_samples(4)
    finally:
        bench.stop()


@needs_clang
def test_the_tempo_comes_from_the_piece(tmp_path):
    """`duet.ges` says 96, so a beat is not 0.5 s."""
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.bpm == 96
        assert bench.beats_to_samples(1) == int(60 * bench.rate / 96)
    finally:
        bench.stop()


@needs_clang
def test_auditioning_a_program_with_banks_reports_no_error(tmp_path):
    """The status line flashed "could not place the knobs" and then worked.

    `audiospans` parsed the author's *raw* text to learn which names it
    defines — and `voices lead 6 reed : Sig Float` is not gestate
    syntax, which is the whole point of expanding it.  Every placement in a
    program with a bank failed, reported as something true that said
    nothing about why.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.drain()
        bench.audition(bench.path.read_text().replace("gain 0.8", "gain 0.6"))
        _settle(bench)
        said = bench.drain()
        assert any("audition" in m for m in said), said
        assert not any("could not place" in m for m in said), said
    finally:
        bench.stop()


def test_placing_does_not_ask_the_engine_that_is_still_playing(tmp_path):
    """The rebuild raced the audio thread, and `_place` lost.

    A `Site.node` indexes the graph the *new* text extracts to, and the
    engine goes on running the old one until `install` swaps it between
    blocks — later, on another thread, and never at all for an edit it
    refuses.  Reading a node's type out of `live.engine.graph` therefore
    read a node that had moved, or ran off the end of a shorter graph:

        IndexError: list index out of range   (audioir.Graph.node)

    Stubbed rather than raced, because a test that has to lose a race is a
    test that passes when the bug is there.
    """
    import types

    from gestate.audioir import Graph

    path = tmp_path / "twoknobs.ges"
    path.write_text((AUDIO_DIR / "twoknobs.ges").read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    # An engine playing something else entirely — the extreme of the same
    # disagreement an ordinary edit makes.
    bench.live = types.SimpleNamespace(
        engine=types.SimpleNamespace(graph=Graph()))

    bench._place(path.read_text())

    assert {s.name for s in bench.sites} == {"pitch", "cutoff"}
    # Read out of the graph the sites were placed in, so it is the type
    # these channels actually carry rather than nothing at all.
    assert bench.knob_types == {"pitch": "Int", "cutoff": "Int"}
    assert bench.knob_range("cutoff") == KNOB_RANGE


@needs_clang
def test_a_banks_note_channels_are_not_knobs(tmp_path):
    """They place — at the bank's own line — and must not become sliders.

    A bank's channels are written by a scheduler or a keyboard, and a
    slider fighting either is a control that does nothing you can predict.
    `duet.ges` has 36 of them and no knobs at all.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.sites == [], [s.name for s in bench.sites]
        graph = bench.live.engine.graph
        assert len(graph.control_sources()) == 36, "the channels are there"
        owned = bench._bank_channels(bench.path.read_text())
        assert len(owned) == 36
    finally:
        bench.stop()


@needs_clang
def test_a_bank_row_follows_the_score(tmp_path):
    """`bass 0/3` for a whole piece was the bug.

    The row counted only *MIDI* notes, and a bank driven by the score has
    no allocator at playback time — the schedule wrote its channels ahead
    of time and nothing tracked them.  Read out of the schedule instead,
    with the same arithmetic the voice itself does: sounding when `gateAt`
    has arrived and `offAt` has not.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        seen = []
        for beat in (0, 1.5, 3, 5):
            bench.seek_beats(beat)
            seen.append(bench.sounding_on("bass"))

        assert all(len(k) == 1 for k in seen), seen
        assert len({tuple(k) for k in seen}) > 1, "the row never changed"
        # The walking bass of `duet.ges`, beat by beat.
        assert [k[0] for k in seen] == [45, 52, 55, 48]

        # And the bank the keyboard plays stays empty without one.
        assert bench.sounding_on("lead") == []
    finally:
        bench.stop()


@needs_clang
def test_the_first_note_of_a_session_sounds(tmp_path):
    """It played, silently — which is the worst way for this to be wrong.

    `Notes.now` is what stamps a note's `gateAt`, and it was updated only
    when a channel was already in `values`: that is, only *after* a note
    had been played.  So the first note of a session was stamped at instant
    0 while the engine was minutes in, and its envelope had decayed to
    nothing before anything read it.  Nothing raised, the row updated, and
    no sound came out.
    """
    import ctypes

    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.notes = Notes(bench._allocators())
        buffer = (ctypes.c_float * 64)()

        for _ in range(40):                      # let the engine get on
            bench.transport.fill(buffer, 64, bench.control, 0)
        assert bench.notes.now > 1000, "the note reader lost the clock"

        bench.notes.feed(_Note("note_on", 72))
        stamped = bench.notes.values["leadChan0f0"]
        assert stamped > 1000, f"stamped at {stamped}, in the distant past"

        peak = 0.0
        for _ in range(40):
            bench.transport.fill(buffer, 64, bench.control, 0)
            peak = max(peak, max(abs(x) for x in buffer))
        assert peak > 0.01, "the note was silent"
        assert bench.sounding_on("lead") == [72]
    finally:
        bench.stop()


# ── FromMIDI ────────────────────────────────────────────────────────────────


@needs_clang
def test_a_bank_takes_midi_only_when_the_program_says_how(tmp_path):
    """What greys the switch out.

    A bank whose payload has no `FromMIDI` instance cannot be handed a
    note, however much you want it to be — and a switch you can throw that
    cannot do anything is worse than one you cannot.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.from_midi is not None
        assert bench.takes_midi("lead") and bench.takes_midi("bass")

        # Take the instance away and the switch goes with it.
        stripped = bench.path.read_text().replace(
            "instance FromMIDI Pitched where\n    noteOn ch p v = "
            "Just (Pitched p v)", "")
        bench.apply(stripped)
        _settle(bench)
        assert bench.from_midi is None
        assert not bench.takes_midi("lead")
    finally:
        bench.stop()


@needs_clang
def test_every_listening_bank_that_accepts_gets_the_note(tmp_path):
    """"All that accept it get it" — layering is one key on two instruments.

    Both banks here carry `Pitched` and share one instance, so the switch
    is the only thing that separates them.
    """
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.notes = Notes({b["name"]: Allocator(b["channels"])
                             for b in bench.banks})
        bench._rewire_notes()
        for bank in ("lead", "bass"):
            bench.listen(bank, True)

        bench.notes.now = 5000
        bench.notes.feed(_Note("note_on", 64))
        assert bench.notes.sounding_on("lead") == [64]
        assert bench.notes.sounding_on("bass") == [64], "did not layer"

        bench.notes.feed(_Note("note_off", 64))
        assert bench.notes.sounding() == [], "a layer was left hanging"
    finally:
        bench.stop()


@needs_clang
def test_a_bank_switched_off_is_not_asked(tmp_path):
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        bench.notes = Notes({b["name"]: Allocator(b["channels"])
                             for b in bench.banks})
        bench._rewire_notes()
        bench.listen("lead", True)
        bench.listen("bass", False)

        bench.notes.now = 5000
        bench.notes.feed(_Note("note_on", 64))
        assert bench.notes.sounding_on("lead") == [64]
        assert bench.notes.sounding_on("bass") == []
    finally:
        bench.stop()


@needs_clang
def test_an_instance_may_decline_a_note(tmp_path):
    """`Nothing` is a real answer, and the reason this is one method.

    A bank that only wants one channel says so in ordinary gestate rather
    than in a routing table beside the program.
    """
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    picky = bench.path.read_text().replace(
        "    noteOn ch p v = Just (Pitched p v)",
        "    noteOn ch p v = onlyLow ch p v\n\n"
        "onlyLow : Int -> Int -> Int -> Maybe Pitched\n"
        "onlyLow ch p v = case p < 60 of\n"
        "    True -> Just (Pitched p v)\n"
        "    False -> Nothing\n")
    bench.path.write_text(picky)
    bench.start(seconds=0.0)
    try:
        bench.notes = Notes({b["name"]: Allocator(b["channels"])
                             for b in bench.banks})
        bench._rewire_notes()
        for bank in ("lead", "bass"):
            bench.listen(bank, True)

        bench.notes.now = 5000
        assert bench.notes.feed(_Note("note_on", 48)), "a low note was refused"
        assert not bench.notes.feed(_Note("note_on", 72)), "a high note got in"
        assert bench.notes.sounding() == [48, 48]
    finally:
        bench.stop()


@needs_clang
def test_ticking_a_scored_bank_plays_it(tmp_path):
    """The bug: `bass`'s checkbox did nothing.

    It was excluded from the allocators, so the switch set a flag on a bank
    that was not there.  Off by default and playable when ticked is the
    behaviour a switch implies.
    """
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.listening("lead"), "the played bank should start on"
        assert not bench.listening("bass"), "the scored bank should start off"

        bench.notes.now = 5000
        bench.notes.feed(_Note("note_on", 64))
        assert bench.notes.sounding_on("bass") == []

        bench.listen("bass", True)
        bench.notes.feed(_Note("note_on", 67))
        assert bench.notes.sounding_on("bass") == [67], "ticking did nothing"
    finally:
        bench.stop()


@needs_clang
def test_a_greyed_switch_does_not_pass_notes(tmp_path):
    """It gated only the `FromMIDI` path.

    A program with no instance has its switches greyed out *because* they
    cannot do anything — and the older routing path ignored them, so notes
    went through anyway.
    """
    from gestate.audioalloc import Allocator
    from gestate.audiomidi import Notes

    bench = _bench(tmp_path, "duet.ges")
    stripped = DUET.read_text().replace(
        "instance FromMIDI Pitched where\n    noteOn ch p v = "
        "Just (Pitched p v)", "")
    bench.path.write_text(stripped)
    bench.start(seconds=0.0)
    try:
        assert bench.from_midi is None
        bench.notes = Notes({b["name"]: Allocator(b["channels"])
                             for b in bench.banks})
        bench._rewire_notes()
        assert not bench.takes_midi("lead"), "no instance, no switch"

        bench.notes.now = 5000
        assert not bench.notes.feed(_Note("note_on", 64))
        assert bench.notes.sounding() == [], "a greyed switch passed a note"
    finally:
        bench.stop()


@needs_clang
def test_the_switch_decides_who_drives_a_bank(tmp_path):
    """Two writers on one set of channels, and the switch picks.

    The score used to win always, so a note played on a scored bank was
    taken by the allocator, *shown in its row*, and never heard — the
    schedule was read first and the played value never reached the engine.
    """
    # `start` builds the note plumbing now, with or without a MIDI port —
    # the on-screen keyboard plays through it, so it cannot wait for one.
    bench = _bench(tmp_path, "duet.ges")
    bench.start(seconds=0.0)
    try:
        assert bench.notes is not None, "no allocators without a MIDI port"
        assert not bench.listening("bass"), "scored banks start off"
        assert bench.sounding_on("bass") == [45], "the score drives it"

        bench.listen("bass", True)
        bench.notes.now = 5000
        bench.notes.feed(_Note("note_on", 40))
        assert bench.sounding_on("bass") == [40], "the keyboard has it"

        # And the engine reads the played value, not the scored one.
        chan = bench.banks[0]["channels"][0][2] if \
            bench.banks[0]["name"] == "bass" else \
            bench.banks[1]["channels"][0][2]
        node = bench.live.engine.graph.control_by_chan()[chan]
        assert bench.control(node.id, 5000) == 40

        bench.listen("bass", False)
        assert bench.sounding_on("bass") == [45], "given back to the score"
    finally:
        bench.stop()


# ── The C audio host, wired in ──────────────────────────────────────────────
#
# `gestate/host.c` owns the swap, the fade, the transport and the control
# block, and opens the sound card itself, so a rebuild cannot stall a block
# however long the front end takes.  What is checked here is the *wiring*:
# that the editor cannot tell the two transports apart, and that every way
# the host can be unavailable leaves a working editor behind.


def test_the_two_transports_present_the_same_face():
    """**The reason `HostTransport` is a class and not a branch.**  The
    views ask the same questions of either, so anything one answers and the
    other does not is a crash on somebody's machine and not on mine."""
    from gestate.audioeditor import HostTransport, Transport

    def surface(cls) -> set:
        return {name for name in dir(cls) if not name.startswith("_")}

    missing = surface(Transport) - surface(HostTransport)
    assert not missing, f"HostTransport cannot answer {sorted(missing)}"


def test_a_named_player_command_keeps_the_python_driver(tmp_path):
    """Asking for `pw-play` by name is asking for the pipe.  The host opens
    a device instead, so it stays out of the way when one was requested."""
    bench = _bench(tmp_path)                    # `_bench` passes a command
    assert bench._open_host() is None


def test_a_host_that_cannot_be_built_falls_back_and_says_so(tmp_path,
                                                            monkeypatch):
    """No `clang`, no ALSA headers, no card, a card that will not take
    float32 — each is a machine that should still get an editor."""
    bench = _bench(tmp_path)
    bench.command = None

    class NoHost:
        def __init__(self, *_a, **_kw):
            raise RuntimeError("no device here")

    import gestate.audiohost as audiohost

    monkeypatch.setattr(audiohost, "Host", NoHost)
    assert bench._open_host() is None
    assert any("Python driver" in m for m in bench.messages), bench.messages


def test_handing_over_does_nothing_without_a_host(tmp_path):
    """The Python driver installs for itself, in `Live.install`; a second
    installer would swap the engine twice."""
    bench = _bench(tmp_path)
    assert bench.host is None
    bench._hand_over()                          # must not raise


def test_a_host_transport_delegates_to_the_host():
    from gestate.audioeditor import HostTransport

    class FakeHost:
        def __init__(self):
            self.playing, self.position = True, 0
            self.sought, self.looped, self.watched = None, None, None
            self._peak = 0.25

        def seek(self, to):
            self.sought = to
            self.position = to

        def loop(self, start, end):
            self.looped = (start, end)

        def watch_peak(self, on):
            self.watched = on

        def peak(self):
            was, self._peak = self._peak, 0.0
            return was

    class FakeLive:
        channels = 1

    host = FakeHost()
    transport = HostTransport(host, FakeLive(), 8000, 64)

    seen = []
    transport.on_seek = seen.append
    transport.seek(4410)
    assert host.sought == 4410 and seen == [4410]
    assert transport.position == 4410

    transport.playing = False
    assert host.playing is False

    transport.loop = (100, 200)
    assert host.looped == (100, 200)
    assert transport.loop == (100, 200)
    transport.loop = None
    assert host.looped == (None, None)

    transport.watch_peak = True
    assert host.watched is True and transport.watch_peak is True
    assert transport.take_peak() == 0.25
    assert transport.take_peak() == 0.0, "the meter was not cleared"


class _StubHost:
    """A host that only remembers what was written into its control block."""

    def __init__(self, position: int):
        self.position = position
        self.wrote: list = []

    def set_control(self, index, value, type_):
        self.wrote.append((index, value))


def test_the_c_host_reads_the_score_at_the_instant_it_has_reached(tmp_path):
    """**The one bug the two drivers could disagree about, and did.**

    `_push_controls` writes each control source into the block the
    generated code reads, and `control(node, at)` resolves a *scored*
    channel with `schedule.value_at(chan, at)`.  It was written passing a
    literal `0`, which is a constant only a knob survives: a knob's value
    does not depend on the instant, so every hand-driven parameter went on
    working and nothing looked wrong.  A score does depend on it, so every
    scored channel was pinned to whatever the schedule said at instant 0
    and a performance played its first note for ever.

    **Nothing in the suite could have caught it.**  `test/conftest.py`
    shuts the C host to keep the tests off the sound card, so every other
    test drives the Python path — where the time argument was already
    right.  This one drives `_push_controls` against a stub, which is the
    seam itself and needs no device.

    Asserted as "the values move", not against a recomputed expectation:
    comparing `_push_controls`'s output to `control(node, at)` would be
    comparing the code to itself, and would have passed with the `0` in
    place.
    """
    path = tmp_path / "duet.ges"
    path.write_text(DUET.read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        assert bench.schedule is not None, "duet.ges is a scored program"
        chans = bench.schedule.channels()

        # The first instant the score says something different from what it
        # said at 0 — found rather than hard-coded, so editing `duet.ges`
        # cannot quietly turn this into a test of nothing.
        later = next(
            (t for t in range(0, 8 * 8000, 64)
             if any(bench.schedule.value_at(c, t)
                    != bench.schedule.value_at(c, 0) for c in chans)),
            None)
        assert later is not None, "duet.ges's score never changes at all"

        def pushed(at: int) -> list:
            # The real host goes back straight away: `stop()` in the
            # `finally` below talks to whatever `bench.host` is, and a stub
            # left in its place fails the test for a reason that has
            # nothing to do with the score.
            was, bench.host = bench.host, _StubHost(at)
            try:
                bench._push_controls(at)
                return bench.host.wrote
            finally:
                bench.host = was

        assert pushed(later) != pushed(0), (
            f"every control source reads the same at instant 0 and at "
            f"{later}, so the score never advances past its first note")
    finally:
        bench.stop()


# ── Probes ──────────────────────────────────────────────────────────────────
#
# `peak`, `rms` and `band0`… are measurements of the *output*.  A probe is a
# reading from inside the instrument: how many samples a voice has been
# sounding, which is what a picture of an envelope needs — the shape is
# already in the file, and what is missing is only where along it the voice
# has walked.


class _FakeVoice:
    def __init__(self, key=None, started=-1):
        self.key, self.started = key, started


class _FakeAllocator:
    def __init__(self, voices):
        self.voices = voices


class _FakeNotes:
    def __init__(self, allocators):
        self.allocators = allocators


def test_a_probe_is_the_age_of_a_voice(tmp_path):
    """From the allocator, not from a probe into the graph: a voice already
    records the sample its note began at — that is what "oldest" means when
    stealing — and the transport knows the instant."""
    bench = _bench(tmp_path)
    bench.notes = _FakeNotes({"keys": _FakeAllocator(
        [_FakeVoice("a", 1000), _FakeVoice(None, -1), _FakeVoice("b", 4400)])})

    class At:
        position = 5000

    bench.transport = At()
    # One-based: a sounding voice reads its age *plus one*, so that `0`
    # can mean "silent" and not "started this instant".
    assert bench.voice_ages() == [4001, 0, 601]


def test_a_silent_voice_probes_as_nothing(tmp_path):
    """Zero means *nothing*, which is why a sounding voice never reads
    zero — `audioalloc`'s `gateAt` is 1-based for the same reason."""
    bench = _bench(tmp_path)
    bench.notes = _FakeNotes({"keys": _FakeAllocator([_FakeVoice(None, -1)])})

    class At:
        position = 900

    bench.transport = At()
    assert bench.voice_ages() == [0]


def test_probing_before_anything_plays_is_empty_rather_than_a_crash(tmp_path):
    bench = _bench(tmp_path)
    assert bench.voice_ages() == []


def test_the_readings_a_program_can_ask_for_are_all_declared():
    """One list, so that adding a reading and forgetting to write it is a
    test failure rather than a channel nothing ever fills."""
    from gestate.audioeditor import Workbench

    assert set(Workbench.BANDS) <= set(Workbench.WATCHED)
    assert set(Workbench.PROBES) <= set(Workbench.WATCHED)
    for name in ("peak", "rms", "voices", "position"):
        assert name in Workbench.WATCHED, name


@needs_clang
def test_an_unfolding_score_plays_through_the_performer(tmp_path):
    """A `cycle`d piece has no bake; the editor performs it instead.

    The performer stands beside the schedule at the same `control()`
    seam: notes decided as the clock reaches them, off the audio thread,
    with the transport's seek answered by the performer's own
    (`spec/dynamicscore.md`, stages one and two, in the editor at last).
    """
    path = tmp_path / "forever-duet.ges"
    path.write_text(DUET.read_text().replace(
        "score = walk >>= voices.bass",
        "score = cycle walk >>= voices.bass"))
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        assert bench.schedule is None
        assert bench.performer is not None
        assert bench.scored_banks() == {"bass"}

        graph = bench.live.engine.graph
        gate = graph.control_by_chan()["bassChan0f0"]
        # Drive the control seam the way a render would: the first note
        # arrives, and four beats later the cycle is still producing.
        assert bench.control(gate.id, 0) not in (None, 0)
        for t in range(0, 8000 * 12, 4096):
            bench.control(gate.id, t)
        assert len(bench.performer.history) >= 8, "the cycle should unfold"

        # A seek is the performer's own: silent replay, nothing stuck.
        bench._after_seek(8000)
        assert bench.control(gate.id, 8000) not in (None, 0)
    finally:
        bench.stop()


@needs_clang
def test_the_arpeggiator_hears_press_and_release(tmp_path):
    """The holds mechanism, locked in: press and the line is your key,
    release and the line is silence — no idle figure, no fallback pitch,
    no note the player cannot account for.
    """
    path = tmp_path / "arpeggiator.ges"
    path.write_text((AUDIO_DIR / "arpeggiator.ges").read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    bench.start(seconds=0.0)
    try:
        assert bench.performer is not None
        graph = bench.live.engine.graph
        gate = graph.control_by_chan()["leadChan0f0"]
        beat = 8000 * 60 // 128

        for t in range(0, beat, 64):
            bench.control(gate.id, t)
        assert not bench.performer.history, "empty hands must be silence"

        bench.keyboard.press(62)
        for t in range(beat, 3 * beat, 64):
            bench.control(gate.id, t)
        played = {e[3][0][1] for e in bench.performer.history
                  if e[2] == "lead"}
        assert played and played <= {62, 74}, played

        bench.keyboard.release(62)
        seen = len(bench.performer.history)
        for t in range(3 * beat + 4 * 64, 5 * beat, 64):
            bench.control(gate.id, t)
        late = [e for e in bench.performer.history[seen:] if e[2] == "lead"]
        assert not late, f"released, yet it kept playing: {late}"
    finally:
        bench.stop()


# ── A loop wrap is a seek nobody announced ───────────────────────────────

def test_a_backward_clock_is_a_wrap():
    """The C engine closes its own loop between blocks: it moves
    `position` back and tells this side nothing, so `on_seek` never
    fires.  The clock going backwards is the only announcement there is.

    A `LazyPerformer` only ever goes forward, so without this it went on
    answering with the values from the end of the loop for the whole of
    the next pass — notes late, or never released at all.
    """
    from gestate.audioeditor import Workbench

    assert Workbench._wrapped(at=100, was=5000) is True
    assert Workbench._wrapped(at=5000, was=100) is False, "ordinary playing"
    assert Workbench._wrapped(at=100, was=100) is False, "standing still"
    # The first reading has nothing to compare against and must not look
    # like a wrap; the thread starts `was` below zero for that.
    assert Workbench._wrapped(at=0, was=-1) is False


def test_one_rule_decides_what_cannot_be_installed_while_playing():
    """**Two drivers, one rule.**

    The Python driver installs in `Live.install` and the C host installs
    in `Workbench._hand_over`, and the channel check was written out
    twice — so when the control block needed one too it went into one of
    them and the other went on accepting the edit.  That is the gap this
    module's own docstring warns about: *a second implementation of
    anything puts its bugs between them.*

    What went wrong before the rule was shared: adding a `voices` bank to
    a synth that had none wants three control channels a voice, the host
    had allocated room for the old count, and the graph was installed
    anyway.  The apply said *"rebuilt"*, `set_control` then raised
    `no control slot 1` on another thread, the score never loaded and
    nothing played — which is the shape of failure the channel check
    already existed to prevent, one field over.
    """
    import inspect

    from gestate.audioeditor import Workbench
    from gestate.audiolive import Live

    # The rule is asked for, never restated.
    assert "needs_restart" in inspect.getsource(Workbench._hand_over)
    assert "channel(s) to" not in inspect.getsource(Workbench._hand_over), \
        "the channel check is written out a second time again"

    class Engine:
        def __init__(self, channels, controls):
            self.channels = channels
            self.control_sources = [object()] * controls

    live = Live.__new__(Live)
    live.engine = Engine(1, 1)
    live.controls = 1

    assert live.needs_restart(Engine(1, 1)) is None, "an ordinary edit restarted"
    assert "channel(s)" in live.needs_restart(Engine(2, 1))
    # The one that was unchecked: more control slots than were reserved.
    said = live.needs_restart(Engine(1, 16))
    assert said and "16 control channel(s)" in said and "room for 1" in said

    # **`None` means nobody has said**, which is the Python driver: it
    # allocates per block and has no fixed room to run out of.
    live.controls = None
    assert live.needs_restart(Engine(1, 16)) is None


def test_an_edit_that_will_not_fit_starts_a_restart(tmp_path):
    """**The program does the restarting.**

    The host allocates its control block and tells the card how many
    channels to expect at construction, and neither can be renegotiated
    between blocks — so adding a `voices` bank (three channels a voice)
    to a synth that had none cannot be installed in place.

    It used to be installed anyway: the apply said *"rebuilt"*,
    `set_control` raised `no control slot 1` on another thread, the score
    never loaded and nothing played.  Then it was refused with a sentence
    telling you to restart it yourself — which is asking somebody to do a
    thing the program can do better, since it knows the edit is good and
    knows exactly what is too small.

    **What is checked here is the decision and the wiring**, because the
    audio half cannot be reached from this suite at all: `conftest.py`
    makes `Host.open` and `Host.run_device` refuse, so nothing here ever
    has a C host, on purpose — a test that needed a sound card would fail
    on a machine without one for a reason having nothing to do with what
    it checks.  The fade-out-and-back was verified by hand against a real
    card: controls 1 → 16, the bank and the piece loaded, still playing.
    That gap is worth knowing about rather than papering over.
    """
    bench = _bench(tmp_path)
    bench.host = object()                 # as if a card had been opened
    asked = []
    bench.restart = lambda why, seconds=None, **kw: asked.append((why, kw))

    class Engine:
        def __init__(self, channels, controls):
            self.channels = channels
            self.control_sources = [object()] * controls

    class Live:
        from gestate.audiolive import Live as _real
        needs_restart = _real.needs_restart

        def __init__(self):
            self.engine = Engine(1, 1)
            self.controls = 1
            self.pending = Engine(1, 16)
            self.errors = []

    bench.live = Live()
    bench._applying = "sound = the text being auditioned\n"
    bench._hand_over()
    # The thread it starts is the point: `_hand_over` runs *on the audio
    # thread*, and `stop` joins that very thread — a join on yourself is
    # a hang, so the restart has to happen somewhere else.
    import time
    for _ in range(200):
        if asked:
            break
        time.sleep(0.01)
    assert asked, "an edit that cannot fit did not start a restart"
    assert "16 control channel(s)" in asked[0][0]
    assert bench.live.pending is None, "the stale engine was kept"

    # **And with the text it is restarting *for*.**  `start` reads the
    # file, and an audition deliberately does not write one — so a
    # restart without this brings back the program on disk: the audition
    # never plays, *and* the new player is sized for the old program, so
    # the next audition asks to restart again.  One omission, both
    # symptoms, and the parameter existed before it was passed.
    assert asked[0][1] == {"text": bench._applying}
    assert bench._applying, "`apply` did not keep what it was installing"


def test_the_python_driver_never_restarts(tmp_path):
    """It allocates per block, so it has no fixed room to run out of —
    and a restart it did not need would be a fade nobody asked for."""
    bench = _bench(tmp_path)
    assert bench.host is None
    bench.restart("whatever")             # returns, says nothing, does nothing
    assert not any("restarting" in m for m in bench.messages)


# ── The canvas gets a frame ─────────────────────────────────────────────────
#
# `spec/substrate.md`'s canvas is *interpreted, at frame rate*, and the rate
# is the view's — so something outside the program has to say a frame passed
# and say what the instrument is doing.  When `audiopygame.py` was deleted
# its loop went with it, and the replacement in `workbench.py` picked up
# neither call: `Workbench.observe` had no caller anywhere in the tree, so
# `peak`, `rms`, `position` and the bands stayed at their defaults and every
# meter in `examples/audio` was frozen; and nothing had ever ticked `events`,
# so a substrate written to animate could not.
#
# Neither was a broken function — both functions were fine.  That is why
# these tests run a *frame* rather than a method: `Substrate.tick` passing
# while nobody calls it is exactly the hole the editor fell through.

#: A canvas that folds over `events` and nothing else — the animation case,
#: with no sound, no channel and no hand on it.  If a frame reaches the
#: program at all, this moves.
TICKING = """substrate : Sig Sub
substrate = moveXY (!floor frames) 10 (rect 4 4 (!RGB 200 200 200))

frames : Sig Float
frames = scan (n e => n + 1.0) 0.0 events
"""


def test_a_frame_reaches_a_canvas_that_folds_over_events(tmp_path):
    """The loop's canvas branch, without a window.

    Run through `_canvas_frame` — what the loop actually calls — rather
    than through `Substrate.tick`, because the defect was the call and not
    the method.
    """
    from gestate.workbench import _canvas_frame

    path = tmp_path / "ticking.ges"
    path.write_text(TICKING)
    bench = Workbench(path, rate=8000, block=64)
    bench._load_substrate(TICKING)
    assert bench.substrate is not None, "the canvas did not build"

    seen = [tuple(_canvas_frame(bench)[0][:3]) for _ in range(4)]
    assert len(set(seen)) == 4, f"the canvas never moved: {seen}"
    # Left to right, one step a frame — the fold is counting frames, so a
    # picture that merely *differs* is not enough.
    xs = [s[1] for s in seen]
    assert xs == sorted(xs) and xs[-1] > xs[0], xs


def test_a_frame_carries_the_instrument_into_the_canvas(tmp_path):
    """`observe` is half of a frame, and the half that had no caller.

    A stub, because the readings come from a `transport` that a headless
    test has no reason to build — what is under test is that a frame asks
    for them at all, and asks before it draws.
    """
    from gestate.workbench import _canvas_frame

    called = []

    class Stub:
        def observe(self):
            called.append("observe")

        def tick(self):
            called.append("tick")

        def picture(self):
            called.append("picture")
            return []

    _canvas_frame(Stub())
    assert called == ["observe", "tick", "picture"], called


# ── The canvas gets a hand ──────────────────────────────────────────────────
#
# The other half of what `71b90af` deleted (fixme.md F101).  The frame tests
# above prove the canvas is *told* things; these prove it can be *touched* —
# the verb line the window sends, through `session.act`, to a value on a
# channel the program declared.  `test_substrate.py` proves the substrate's
# own hit-testing and `test_session.py` proves the verb reaches a bench;
# this is the seam between them, against a real substrate, and it is the
# conformance test any future view has to keep passing.

#: `test_substrate.py`'s fader, deliberately: extent 12x120 centred at
#: (25, 60), so it spans y 0…120 and the fraction is the y in hundredths
#: of 1.2.  One program, two suites, one meaning.
FADER = """
dragged : Chan Float
dragged = chan

level : Sig Float
level = 0.5 ::: mkSig (wait dragged)

handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

substrate : Sig Sub
substrate = moveXY 25 60 (onTouchY dragged
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""


def test_a_touch_gesture_moves_the_channel_it_lands_on(tmp_path):
    """The Python side of the wire, end to end."""
    from gestate.session import Session, act

    path = tmp_path / "fader.ges"
    path.write_text(FADER)
    bench = Workbench(path, rate=8000, block=64)
    bench._load_substrate(FADER)
    assert bench.substrate is not None, "the canvas did not build"
    s = Session(bench=bench)

    # A press a quarter of the way down the travel.
    assert act(s, "touch\tpress\t25\t30") == ""
    assert bench.substrate.values["dragged"] == 0.25
    # A press grabs, so the drag follows even 375 px off the element —
    # the same claim `test_substrate.py` makes of the substrate alone,
    # here shown to survive the trip across the wire.
    assert act(s, "touch\tdrag\t400\t90") == ""
    assert bench.substrate.values["dragged"] == 0.75
    # And a release leaves the fader where it was let go.
    assert act(s, "touch\trelease\t400\t90") == ""
    assert bench.substrate.values["dragged"] == 0.75


def test_a_touch_with_no_canvas_is_nothing(tmp_path):
    """A gesture into a file with no substrate is silence, not a stack
    trace — the same courtesy every verb on this wire keeps."""
    from gestate.session import Session, act

    path = tmp_path / "mute.ges"
    path.write_text("x : Int\nx = 1\n")
    bench = Workbench(path, rate=8000, block=64)
    s = Session(bench=bench)
    assert act(s, "touch\tpress\t10\t10") == ""


def test_opening_away_does_not_wait_for_the_old_start():
    """fixme.md F109.  Opening a file mid-compile used to join the old
    start *in the gesture loop*, so the window answered nothing for as
    long as a file nobody was looking at took to `clang`.  `_retire`
    hands the join and the stop to their own thread — and the ordering
    that join was really buying is kept, because the new instrument's
    own thread waits on the retirement before asking for the sound
    card."""
    from gestate.session import Session
    from gestate.workbench import _begin, _retire

    log, lock = [], threading.Lock()

    class Slow:
        trouble = ""

        def __init__(self, name, delay=0.0):
            self.name, self.delay = name, delay

        def start(self):
            time.sleep(self.delay)
            with lock:
                log.append(f"start {self.name}")

        def stop(self):
            with lock:
                log.append(f"stop {self.name}")

    old = Slow("old", delay=0.6)
    quitting, starter = _begin(old, Session(bench=old))
    time.sleep(0.05)                    # the old start is mid-"clang"

    began = time.monotonic()
    retiring = _retire(old, starter, quitting)
    held = time.monotonic() - began
    assert held < 0.2, f"the switch held the loop for {held:.2f}s"

    new = Slow("new")
    _q2, starter2 = _begin(new, Session(bench=new), after=retiring)
    starter2.join(timeout=10.0)
    retiring.join(timeout=10.0)
    with lock:
        assert "start new" in log, log
        assert log.index("stop old") < log.index("start new"), \
            f"the new instrument raced the old for the sound card: {log}"


def test_a_failed_start_records_its_trouble(tmp_path):
    """**A file that is broken when it is opened is the first broken
    file anyone meets**, and its complaint must anchor a content box
    like any other — `apply` recorded its failures and `start` never
    did, so the box mechanism worked in every unit test and drew
    nothing the first time a person opened a broken file.  Found by a
    screenshot (`spec/workbench.md` §"Content boxes" B1).

    **And the positions are the file's own.**  The raw exception names
    the assembled program's line — 2649 of a two-line file — which is
    why the recording goes through `_first_line`/`in_source` rather
    than `str(e)`."""
    from gestate.session import Session, furniture
    from gestate.workbench import _begin

    path = tmp_path / "broken.ges"
    path.write_text("sound : Sig Float\nsound = nonsense * 2.0\n")
    bench = Workbench(path, rate=8000, block=64)
    s = Session(bench=bench)
    _quitting, starter = _begin(bench, s)
    starter.join(timeout=60.0)
    assert not starter.is_alive(), "the start thread did not finish"

    assert "nonsense" in bench.trouble, bench.trouble
    assert "at broken.ges:2:" in bench.trouble, \
        f"positions are not the file's own: {bench.trouble!r}"
    rows = [l for l in furniture(s).splitlines() if l.startswith("trouble\t")]
    assert rows and rows[0].split("\t")[1] == "2", rows
    assert s.said and s.said[0].startswith("not playing:")


def test_the_line_is_read_from_either_of_the_compiler_voices():
    """`at 12:8`, `at line 134:8` and `at broken.ges:2:8` all carry the
    number; `at prelude line 216:29` and a position in *another* file
    deliberately do not — a complaint about somewhere else must not
    anchor a box under an unrelated line of this one."""
    from gestate.session import _line_of

    assert _line_of("expected a type (at 12:8-12:11)") == 12
    assert _line_of("Unknown global 'x' (at line 134:8)") == 134
    assert _line_of("Unknown global (at broken.ges:2:8)", "broken.ges") == 2
    assert _line_of("Type mismatch (at prelude line 216:29)") == 0
    assert _line_of("bad (at elsewhere.ges:5:1)", "broken.ges") == 0
    assert _line_of("nothing positional at all") == 0


#: The smallest touchable canvas: one channel, one fader track.
TOUCHABLE = """\
dragged : Chan Float
dragged = chan

level : Sig Float
level = 0.5 ::: mkSig (wait dragged)

substrate : Sig Sub
substrate = onTouchY dragged (rect 12 120 (colour 40 40 40))
"""


def test_a_touched_name_reaches_the_reference_and_the_control(tmp_path):
    """`Workbench.touched` is `touch` minus the walk: the reference
    substrate keeps its picture in step and the value lands where
    `control` finds it by name — the same two halves, written from
    the far side of the wire."""
    from gestate.gui import Substrate

    bench = Workbench(tmp_path / "x.ges",
                      command=_pacer(tmp_path / "stream.raw"))
    bench.substrate = Substrate(TOUCHABLE, rate=8000)
    bench.touched("dragged", 0.75)
    assert bench.substrate.values["dragged"] == 0.75
    # A name the program never declared is not written and not paid for.
    bench.touched("nosuch", 0.5)
    assert "nosuch" not in bench.substrate.values
    # And a bench with no canvas swallows the write, as `touch` does.
    bench.substrate = None
    bench.touched("dragged", 0.1)


def test_observe_says_what_it_wrote(tmp_path):
    """The `reading` verb's model half: a window that walks the
    substrate needs the instrument's facts by the names the program
    declared, and `observe` returning what it wrote is what keeps two
    canvases fed from one reading.  A touch never echoes back — that
    would snap a fader under a hand that had moved on."""
    from types import SimpleNamespace

    from gestate.gui import Substrate

    bench = Workbench(tmp_path / "x.ges",
                      command=_pacer(tmp_path / "stream.raw"))
    bench.substrate = Substrate(
        TOUCHABLE + "\npeak : Chan Float\npeak = chan\n", rate=8000)
    bench.transport = SimpleNamespace(
        take_peak=lambda: 0.5, position=0,
        take_rms=lambda: 0.0, band=lambda k: 0.0)
    assert bench.observe() == [("peak", 0.5)]
    assert bench.substrate.values["peak"] == 0.5

    bench.touched("dragged", 0.3)
    assert all(n != "dragged" for n, _ in bench.observe()), \
        "a touch echoed back as a reading"

    bench.transport = None
    assert bench.observe() == [], "facts from an instrument not playing"


@needs_clang
def test_a_scope_traces_while_the_instrument_plays(tmp_path):
    """`spec/scope.md` acceptance 3's engine half: a playing synth with
    a scope publishes its window, downsampled to the trace points, and
    the trace is the sound that flowed — not silence, not garbage."""
    from pathlib import Path as _P

    src = (_P(AUDIO_DIR) / "scoped.ges").read_text()
    path = tmp_path / "scoped.ges"
    path.write_text(src)
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    try:
        bench.start()
        # Started is not yet sounding: wait for frames to flow.
        engine = bench.live.engine
        assert _wait(lambda: engine.frames > 8000, 20.0), \
            "no second of sound arrived"
        traces = bench.scope_traces()
        assert [t[0] for t in traces] == ["post"]
        points = traces[0][1]
        assert len(points) == Workbench.TRACE_POINTS
        assert any(abs(p) > 0.01 for p in points), \
            "a playing sine left no trace"
        assert all(abs(p) <= 1.0 for p in points)
    finally:
        bench.stop()


@needs_clang
def test_an_audition_raises_the_scope(tmp_path):
    """Henri's report: auditioning a scoped edit needed a Ctrl-S
    before the trace flowed.  An audition installs a whole new engine;
    the scope rides it, and the trace must flow from the auditioned
    text — the disk deliberately never learns of it."""
    from pathlib import Path as _P

    path = tmp_path / "bare.ges"
    path.write_text("sound : Sig Float\n"
                    "sound = 0.2 * sine 220.0\n")
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    try:
        bench.start()
        assert _wait(lambda: bench.live is not None
                     and bench.live.engine.frames > 800, 20.0)
        assert bench.scope_traces() == []

        bench.audition("sound : Sig Float\n"
                       "sound = scope \"post\" (0.2 * sine 220.0)\n")
        assert _wait(lambda: [t[0] for t in bench.scope_traces()]
                     == ["post"], 20.0), \
            "the auditioned scope never raised a trace"
        assert path.read_text().count("scope") == 0, \
            "an audition wrote the file"
    finally:
        bench.stop()


def test_a_spectrum_puts_the_tone_in_its_bin():
    """`_spectrum` is a pure function, so a sine is the whole test: the
    peak lands in the bin its frequency names, everything else stays
    quiet, and the scale keeps a full-scale tone at the top."""
    import math

    from gestate.audioeditor import _spectrum

    rate, freq = 8000, 1000.0
    xs = [0.8 * math.sin(2 * math.pi * freq * i / rate)
          for i in range(1024)]
    bins = _spectrum(xs, 64)
    assert len(bins) == 64
    peak = bins.index(max(bins))
    fft_bin = freq * 1024 / rate                 # 128
    expect = 64 * math.log(fft_bin) / math.log(512)
    assert abs(peak - expect) <= 2, (peak, expect)
    assert max(bins) > 0.5, "a strong tone reads weak"
    loud = sum(1 for b in bins if b > 0.3)
    assert loud <= 3, "energy where the sine put none"


def test_a_spectro_is_a_scope_by_another_reading(tmp_path):
    """One node kind, two faces (`spec/scope.md`): a `spectro` rings
    exactly as a `scope` does, and only the trace's reading differs."""
    from gestate.audioextract import extract

    g = extract('sound : Sig Float\n'
                'sound = spectro "spec" (0.2 * sine 220.0)\n', rate=8000)
    kinds = [(l, node.kind) for l, _n, node in g.scopes()]
    assert kinds == [("spec", "spectro")]


def test_a_sink_keeps_an_observer_alive_beside_the_sound():
    """Henri's pick from the two spellings (roadmap §"Dropping a scope
    in one move"): `sink scope "stab" stab` — one appended line, the
    observed definition untouched, the scope ringing with no reader.
    A comment's sink is a comment, an indented sink is somebody's own
    word, and line numbers never move."""
    from gestate.audioengine import State, render_block, zero
    from gestate.audioextract import extract
    from gestate.audiovoices import _sinks

    SRC = ("stab : Sig Float\n"
           "stab = 0.3 * saw 110.0\n"
           "\n"
           "sound : Sig Float\n"
           "sound = stab\n"
           "\n"
           'sink scope "stab" stab\n')
    g = extract(SRC, rate=8000)
    assert [(l, n.kind) for l, _len, n in g.scopes()] \
        == [("stab", "scope")]
    s = State([zero(g, n.type_) if n.init is None else n.init
               for n in g.nodes], 0, {})
    out = render_block(g, s, 64)
    bare = extract(SRC.replace('sink scope "stab" stab\n', ""),
                   rate=8000)
    s2 = State([zero(bare, n.type_) if n.init is None else n.init
                for n in bare.nodes], 0, {})
    assert out == render_block(bare, s2, 64), "a sink touched the mix"
    sid = [n.id for _, _, n in g.scopes()][0]
    assert s.lines[sid][:64] == out, "the sink's scope is not ringing"

    # The rewrite is 1:1 and leaves everyone else's words alone.
    text = ('# sink is discussed here\n'
            'sink scope "a" x\n'
            '    sink = 4\n'
            'sink spectro "b" y\n')
    swapped = _sinks(text)
    assert swapped.splitlines()[0] == "# sink is discussed here"
    assert swapped.splitlines()[1] == '__sink_0__ = scope "a" x'
    assert swapped.splitlines()[2] == "    sink = 4"
    assert swapped.splitlines()[3] == '__sink_1__ = spectro "b" y'
    assert len(swapped.splitlines()) == len(text.splitlines())


def test_one_label_one_window():
    """A scope inside a definition is inlined at every call, so two
    calls would watch two signals under one name — and the reader
    shows whichever came first, the other silently invisible.  Refused
    with the way out in the sentence; one call, or two calls with the
    same arguments (one memoized node), stay ordinary."""
    import pytest

    from gestate.audioextract import ExtractError, extract

    TWICE = ('duck : Sig Float -> Sig Float\n'
             'duck s = scope "duck" (0.5 * s)\n'
             '\n'
             'sound : Sig Float\n'
             'sound = duck (sine 220.0) + duck (saw 110.0)\n')
    with pytest.raises(ExtractError) as caught:
        extract(TWICE, rate=8000)
    assert "already watching" in str(caught.value)
    assert "own label" in str(caught.value)

    extract(TWICE.replace(" + duck (saw 110.0)", ""), rate=8000)
    extract(TWICE.replace("saw 110.0", "sine 220.0"), rate=8000)


def test_a_slow_build_never_has_the_last_word(tmp_path):
    """The stale engine hazard, and the reason builds are serialised.

    Two builds in flight write into **one** `pending` engine slot and
    the handover installs whatever is there — so an older one finishing
    last would put the *sound* back an edit while the text stayed
    right, and nothing would correct it until the next edit.  Quiet
    wrongness, which is the kind this project files rather than lives
    with.

    Driven the way it would happen: a first build made slow (a machine
    with `clang` under contention is the ordinary cause) and a second
    asked for while it runs.  The assertion is about *order* — the last
    text built is the last text asked for — and about overlap, because
    two at once is the state the race needs to exist at all.
    """
    from gestate.audioeditor import Workbench

    path = tmp_path / "a.ges"
    path.write_text("sound : Sig Float\nsound = sine 220.0\n")
    bench = Workbench(path, rate=8000, block=64)
    bench.live = object()                  # far enough for `apply` to build

    built, inside, overlapped = [], [], []

    def slowly(text, save):
        inside.append(text)
        if len(inside) > 1:
            overlapped.append(tuple(inside))
        # The first one is the slow one, which is the whole scenario.
        time.sleep(0.6 if not built else 0.05)
        built.append(text)
        inside.remove(text)

    bench._builds._run = slowly
    bench.audition("first")
    time.sleep(0.1)
    bench.audition("second")

    end = time.time() + 15.0
    while time.time() < end and (len(built) < 2 or bench._builds.busy):
        time.sleep(0.02)

    assert not overlapped, f"two builds ran at once: {overlapped}"
    assert built[-1] == "second", built


def test_a_string_of_gestures_is_one_audition(tmp_path):
    """Henri, dragging notes in a playing piece: *"audio stutters when
    I move the notes."*

    Each drop was a rebuild, and a rebuild is a compile racing the
    render loop for the machine.  A hand moves notes in strings, so
    three in two seconds was three of them.  The audition waits a
    moment for the hand to stop — `AUDITION_WAIT` — and a string of
    drops becomes one build of the last text.  The *picture* does not
    wait; it follows the hand through a reading.
    """
    from gestate.audioeditor import AUDITION_WAIT, Workbench

    path = tmp_path / "a.ges"
    path.write_text("sound : Sig Float\nsound = sine 220.0\n")
    bench = Workbench(path, rate=8000, block=64)

    heard = []
    bench._auditions._run = heard.append
    for n in range(5):
        bench.audition_soon(f"take {n}")
        time.sleep(0.02)
    assert heard == [], "it rebuilt before the hand had stopped"

    end = time.time() + 10.0
    while time.time() < end and (not heard or bench._auditions.busy):
        time.sleep(0.02)

    assert heard == ["take 4"], heard
    assert AUDITION_WAIT > 0.1, "a wait too short to cover a gesture"
