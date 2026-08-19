"""Typing is an audition, when an audition is cheap — `fixme.md` F151.

Henri, 2026-08-17: *"If audition takes less than half a second after a
change, then I think it should be automatic.  That's the case with the
intro's example function, but not the case with every program."*  And:
*"we need some mechanism that shows the command to audition and tells
the audio is off sync, but still doesn't complain when user types
away."*

Three rules, and this file is one section per rule:

* **cheap, measured** — the gate is the last audition of *this file*,
  because the cost does not follow the size of the program;
* **quiet** — an unasked-for audition may change the sound and may not
  complain, since half of what anybody types is briefly not a program;
* **and it says so** — the bar carries `behind` whenever what is
  sounding is not what is written, which is the sentence a stranger
  needed and nothing was saying.

**Waiting is not `_settle`'s job here.**  That helper waits for a
message, and the whole point of a quiet audition is that there is no
message — so these wait on the observable that matters instead: the
workbench no longer being `behind` the text.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

from gestate.audioeditor import AUTO_AUDITION, Workbench
from gestate.session import KEYS

AUDIO = Path(__file__).resolve().parent.parent / "examples" / "audio"


def _pacer(out: Path) -> list:
    """A player that consumes the stream and makes no noise — the rule
    `test_audioeditor` states: every `Workbench` here takes one."""
    return [sys.executable, "-c",
            "import sys, time\n"
            "out = open(sys.argv[1], 'wb')\n"
            "while True:\n"
            "    chunk = sys.stdin.buffer.read(4096)\n"
            "    if not chunk: break\n"
            "    out.write(chunk); out.flush(); time.sleep(0.04)\n",
            str(out)]


def _wait(f, timeout=30.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if f():
            return True
        time.sleep(0.02)
    return False


@pytest.fixture()
def bench(tmp_path):
    path = tmp_path / "twoknobs.ges"
    path.write_text((AUDIO / "twoknobs.ges").read_text())
    w = Workbench(path, rate=8000, block=64,
                  command=_pacer(tmp_path / "stream.raw"))
    w.start()
    yield w
    try:
        w.stop()
    except Exception:                                    # noqa: BLE001
        pass


@pytest.fixture()
def idle(tmp_path):
    """The same file, never started — nothing is playing."""
    path = tmp_path / "twoknobs.ges"
    path.write_text((AUDIO / "twoknobs.ges").read_text())
    return Workbench(path, rate=8000, block=64,
                     command=_pacer(tmp_path / "quiet.raw"))


def _edit(bench, mark: str = "  ") -> str:
    """One character of whitespace — a real change that still compiles."""
    return bench.source().replace("sound =", "sound" + mark + "=", 1)


# ── cheap, and measured ─────────────────────────────────────────────────────


def test_the_first_one_is_taken_on_trust_when_the_file_opened_quickly(bench):
    """**The gate has to open by itself, or it never opens for the
    person it is for.**

    The first cut of this gated on the last audition and nothing else —
    which meant a file nobody had applied was never auditioned
    automatically, and *a stranger never applies anything*.  The feature
    would have been switched off for exactly the case it was built for,
    and every test still passed.

    So a file that opened quickly gets one on trust, and what that one
    costs decides all the rest.
    """
    bench.last_audition = None
    assert bench.last_start is not None, "the start left no measurement"
    assert bench.last_start <= 2.0, "twoknobs opened too slowly to judge"
    text = _edit(bench)
    bench.typed(text)
    assert _wait(lambda: bench._built_from == text), \
        "the first automatic audition was never attempted"


def test_a_file_that_opened_slowly_is_never_tried_at_all(bench):
    """The other side of that trust: opening is the only measurement
    that exists before an audition has been timed, so it is used — as a
    veto and never as an estimate.  It cannot be scaled into one; the
    ratio runs from 0.37 to 1.24 across the corpus."""
    from gestate.audioeditor import COLD_ENOUGH

    bench.last_audition = None
    bench.last_start = COLD_ENOUGH + 1.0
    text = _edit(bench, "\t\t")
    bench.typed(text)
    assert not _wait(lambda: bench._built_from == text, 2.0), \
        "a file that took an age to open auditioned itself anyway"


def test_a_cheap_file_auditions_itself(bench):
    """The whole feature, on a file measured at about half a second."""
    bench.audition(_edit(bench, "   "))
    assert _wait(lambda: bench.last_audition is not None), "nothing timed"
    if bench.last_audition >= AUTO_AUDITION:
        pytest.skip(f"this machine builds twoknobs in "
                    f"{bench.last_audition:.2f}s, over the gate")
    text = _edit(bench, "    ")
    bench.typed(text)
    assert _wait(lambda: bench._built_from == text), \
        "typing did not reach the sound on a file cheap enough for it"


def test_an_expensive_file_is_left_alone(bench):
    """The other half of his sentence — *"not the case with every
    program"*.  A file whose last audition ran long is not auditioned
    unasked, however cheap the one before it was."""
    bench.last_audition = AUTO_AUDITION * 10
    text = _edit(bench, "     ")
    bench.typed(text)
    assert not _wait(lambda: bench._built_from == text, 2.0), \
        "an expensive file auditioned itself anyway"


def test_the_gate_is_measured_even_when_the_build_fails(bench):
    """A file that fails *slowly* is exactly one whose next audition
    must not be automatic, so the clock runs in a `finally`."""
    bench.last_audition = None
    bench.audition("sound : Sig Float\nsound = not a program\n")
    assert _wait(lambda: bench.last_audition is not None), \
        "a failed audition left no measurement behind"


def test_nothing_is_auditioned_while_nothing_plays(idle):
    """Stopped, an audition has nothing to do but say so — the rule the
    dragged note already keeps.

    `Workbench.playing` is read-only and means *the audio thread is
    alive*, so the honest way to write this is a workbench nobody
    started rather than a flag set behind its back."""
    idle.last_audition = 0.01
    assert not idle.playing, "the fixture started something after all"
    text = idle.source().replace("sound =", "sound  =", 1)
    idle.typed(text)
    assert not _wait(lambda: idle._built_from == text, 2.0)


# ── quiet: it may change the sound and may not complain ─────────────────────


def test_typing_something_that_is_not_a_program_says_nothing(bench):
    """**The may-not-complain rule.**  Half of what a person types is,
    for a moment, not a program; an editor that answered every pause
    with a compiler error would be unusable to think in."""
    bench.last_audition = 0.01
    was_trouble, seen = bench.trouble, len(bench.messages)
    bench.typed("sound : Sig Float\nsound = 0.2 * sine\n")   # half-typed
    time.sleep(2.5)
    assert bench.trouble == was_trouble, \
        "an automatic audition raised a complaint"
    said = " ".join(bench.messages[seen:])
    assert "not applied" not in said, f"it complained anyway: {said}"


def test_an_asked_for_audition_still_complains(bench):
    """The rule is about the *unasked-for* ones.  A person who pressed
    the key is owed the answer, and losing that would be a worse defect
    than the one this fixes."""
    seen = len(bench.messages)
    bench.audition("sound : Sig Float\nsound = 0.2 * sine\n")
    assert _wait(lambda: any("not applied" in m
                             for m in bench.messages[seen:])), \
        "an asked-for audition went quiet"


def test_a_quiet_success_does_not_chatter(bench):
    """It succeeded, the sound is the text, and the bar stops saying
    `behind` — which is the answer.  A sentence per pause in typing
    would bury the one the last real command left there.

    **Both sentences, and the second was the one that shipped.**  The
    first version silenced `_built` and left `_progress` announcing
    *applied edit 4 (no knob in this synth)* on every generation change
    — one per pause, photographed five deep before Henri saw what was
    meant: *"typing doesn't need that."*
    """
    bench.audition(_edit(bench, "\t"))
    assert _wait(lambda: bench.last_audition is not None)
    if bench.last_audition >= AUTO_AUDITION:
        pytest.skip("too slow on this machine for the automatic path")
    text = _edit(bench, "  \t")
    # **Wait for the setup's own announcement, not merely its timing**
    # (F172).  `last_audition` is set when the audition is *measured*;
    # `applied edit 1` is said later, by `_progress`, on the
    # housekeeping thread between blocks.  Taking the barrier between
    # those two moments lets the asked-for audition's sentence land
    # inside the window this test attributes to typing — which is what
    # failed, twice, both times under a loaded machine, announcing
    # edit *1* when the typed edit is 2.
    assert _wait(lambda: any("applied edit" in m for m in bench.messages)), \
        "the asked-for audition never announced itself"
    seen = len(bench.messages)
    bench.typed(text)
    assert _wait(lambda: bench._built_from == text)
    time.sleep(1.0)                       # let `_progress` see it land
    said = " ".join(bench.messages[seen:])
    assert "auditioning" not in said, f"the quiet path spoke: {said}"
    assert "applied edit" not in said, \
        f"the driver announced an edit nobody asked for: {said}"


def test_an_asked_for_apply_still_announces_itself(bench):
    """The other side of it: pressing `Ctrl-S` is a question, and
    *applied edit N* is its answer.  Losing that to silence the typing
    would be a worse trade than the noise it removed."""
    seen = len(bench.messages)
    bench.apply(_edit(bench, "\t\t\t"), save=True)
    assert _wait(lambda: any("applied edit" in m or "rebuilt" in m
                             for m in bench.messages[seen:])), \
        "an asked-for apply went silent"


# ── and it says so ─────────────────────────────────────────────────────────


def test_behind_is_true_between_the_edit_and_the_sound(bench):
    """The state itself: what is sounding is not what is written."""
    assert not bench.behind(bench.source()), \
        "behind on the text that was just built"
    assert bench.behind(_edit(bench, "       ")), \
        "an edit that has not been applied is not reported as behind"


def test_behind_is_false_once_the_audition_lands(bench):
    text = _edit(bench, "        ")
    bench.audition(text)
    assert _wait(lambda: not bench.behind(text)), \
        "the sound caught up and the mark stayed"


def test_behind_says_nothing_while_nothing_plays(idle):
    """No sound, nothing for it to be behind."""
    assert not idle.behind(
        idle.source().replace("sound =", "sound  =", 1))


def test_the_bar_names_the_command_and_the_key_that_is_bound(bench):
    """*"shows the command to audition and tells the audio is off
    sync"*.  The words are the model's, so the key cannot drift from
    `KEYS` — a window that composed this sentence itself would be free
    to teach a shortcut nobody bound."""
    from gestate.session import Session, furniture

    class View:
        def __init__(self, text): self._t = text
        def held(self): return self._t
        def visible(self): return []

    session = Session(bench)
    session.view = View(_edit(bench, "          "))
    rows = [r for r in furniture(session, bench).splitlines()
            if r.startswith("behind\t")]
    assert rows, "the bar was told nothing about the sound being behind"
    said = rows[0].split("\t", 1)[1]
    assert "audition" in said, "it does not name the command"
    assert KEYS["audition"] in said, "it does not name the bound key"

    session.view = View(bench.source())
    assert not [r for r in furniture(session, bench).splitlines()
                if r.startswith("behind\t")], \
        "the mark stayed after the text and the sound agreed"


def test_the_window_reads_the_verb(bench):
    """The other end of the wire — an unknown verb is skipped, so the
    row is only worth sending if `furniture.rs` knows it."""
    rust = (Path(__file__).resolve().parent.parent / "shell" / "editor"
            / "src" / "furniture.rs").read_text()
    assert '"behind" =>' in rust, "the window does not read the row"
    assert "pub behind: String" in rust
