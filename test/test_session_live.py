"""`Session` over a real `Workbench` — the layer, against the model.

`test_session.py` drives the command layer against a stand-in and is
where the *sentences* are pinned.  This is the other half: that the
things `Session` reaches for are things a `Workbench` actually has, and
that a transcript of names moves a real instrument.

The pacing player from `test_audioeditor` comes back for the reason it
exists there: `audiolive.play` given no command finds `pw-play` or
`aplay` and sends the synth to the machine's speakers.  A test suite
that plays music at you is a test suite people stop running.
"""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import pytest

from gestate.audioeditor import Workbench
from gestate.session import Session

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")


def _pacer(out: Path) -> list:
    """A sound card that is a file."""
    return [sys.executable, "-c",
            "import sys,time\n"
            "out = open(sys.argv[1], 'wb')\n"
            "while True:\n"
            "    chunk = sys.stdin.buffer.read(4096)\n"
            "    if not chunk: break\n"
            "    out.write(chunk); out.flush(); time.sleep(0.04)\n",
            str(out)]


def _session(tmp_path, name="twoknobs.ges") -> Session:
    path = tmp_path / name
    path.write_text((AUDIO_DIR / name).read_text())
    bench = Workbench(path, rate=8000, block=64,
                      command=_pacer(tmp_path / "stream.raw"))
    return Session(bench=bench)


def _settle(bench, timeout=20.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if not getattr(bench, "building", False):
            time.sleep(0.2)
            return
        time.sleep(0.05)


# ── The layer reaches only for things that exist ─────────────────────────


def test_every_command_finds_the_method_it_needs(tmp_path):
    """**The check that the stand-in cannot make.**

    `test_session.py`'s `Bench` has whatever `Session` asks of it,
    because it was written to.  This runs the same list against the real
    model, where a method that does not exist is an `AttributeError` —
    and `Session` turns those into sentences, so the assertion is on the
    *sentence* rather than on an exception never being raised.
    """
    s = _session(tmp_path)
    # **`pitch`, not `pitchChan`.**  A control source is declared
    # `pitchChan` and the editors show it as `pitch` — the suffix is
    # dropped where a person reads it, which is a fact about the model
    # that only the model can teach.
    # **A name that is certainly not on the disk**, so `open` and `steal`
    # answer about a missing file rather than opening one under a test.
    sample = {"Int": 1, "Float": 0.5, "Text": "sine",
              "Named": "pitch", "a": 40, "Path": "no-such-file.ges",
              # A port and a template that certainly are not there, and a
              # `no` for the overwrite question nobody asked — each is
              # reached for the refusal rather than the act.
              "Device": "no-such-controller", "Template": "knob",
              "Symbol": "a", "Answer": "no"}
    for verb in s.commands():
        said = s.run(verb.name, *(sample[a] for a in verb.args))
        assert "object has no attribute" not in said, \
            f"{verb.name}: {said}"
        assert said, f"{verb.name} said nothing"
    s.bench.stop()


def test_the_workbench_answers_the_three_it_was_never_asked(tmp_path):
    """`end_beat`, `set_seed` and `roll_seed` — questions the model
    could always have answered and was never asked, because the old
    editors reached into its attributes instead."""
    s = _session(tmp_path, "duet.ges")
    s.bench._load_score((AUDIO_DIR / "duet.ges").read_text())
    assert s.bench.end_beat() == 16.0, "duet is four bars"

    # A reroll never lands on the take already playing.
    s.bench.seed = 7
    for _ in range(20):
        assert s.bench.roll_seed() != 7
    s.bench.stop()


def test_an_unfolding_score_has_no_end_to_loop(tmp_path):
    """A `cycle` has no end, so `loopAll` has nothing to loop — and says
    so rather than looping to zero."""
    s = _session(tmp_path, "moods.ges")
    s.bench._load_score((AUDIO_DIR / "moods.ges").read_text())
    assert s.bench.end_beat() is None
    assert s.run("loopAll") == "nothing to loop"
    s.bench.stop()


def test_a_finite_score_loops_the_whole_piece(tmp_path):
    s = _session(tmp_path, "duet.ges")
    s.bench._load_score((AUDIO_DIR / "duet.ges").read_text())
    assert s.run("loopAll") == "looping the whole piece"
    s.bench.stop()


# ── A transcript, against the instrument ─────────────────────────────────


@needs_clang
def test_a_transcript_of_names_moves_a_real_instrument(tmp_path):
    """Names in, sentences out — and the knob really turned.

    This is `spec/workbench.md` acceptance 2 with the model behind it
    rather than a double: the same transcript a test writes is the one a
    person types into the palette.
    """
    s = _session(tmp_path)
    s.bench.start()
    try:
        _settle(s.bench)
        assert s.bench.has_knob, "twoknobs declares two"

        said = [s.run(*c) for c in [
            ("what", "pitch"),
            ("set", "pitch", 52),
        ]]
        assert said[0] == "pitch : Chan Int"
        assert said[1] == "pitch = 52"
        assert s.bench.values["pitch"] == 52, "the model did not move"

        # **`start()` leaves the transport running**, which is a real
        # decision of the model — opening a file and hearing it is the
        # point — so the toggle is checked as a toggle rather than
        # against an assumed starting state.
        first = "stopped" if s.bench.playing else "playing"
        second = "playing" if first == "stopped" else "stopped"
        assert [s.run("play"), s.run("play")] == [first, second]
    finally:
        s.bench.stop()


@needs_clang
def test_goto_and_what_read_the_declarations(tmp_path):
    """Both are readings of a fact the workbench already keeps for the
    margin — `audiospans` says which line each control source was
    written on, which is what puts a knob beside its own declaration."""
    s = _session(tmp_path)
    s.bench.start()
    try:
        _settle(s.bench)
        names = [getattr(site, "name", None) for site in s.bench.sites]
        assert "pitch" in names, f"no sites: {names}"
        # `goto` has no window here, so it reports the line instead of
        # jumping to it — a refusal that still answers the question.
        said = s.run("goto", "pitch")
        assert said.startswith("`pitch` is on line "), said
        assert s.run("goto", "nowhere") == "no declaration `nowhere`"
    finally:
        s.bench.stop()
