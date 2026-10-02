"""`tools/grades.py` — the grader over `scanE` arms, held to what it found.

`doc/trial/signals.md` §"Case 5 graded by hand" made a claim by hand; the
grader made it re-runnable, and on its first run it corrected the hand
(bounce reads a stale velocity).  These hold the five verdicts, so a
change to the grader or to an arm that moves one goes red here — the
two drafts being the half that must keep failing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import grades  # noqa: E402

ARMS = ROOT / "doc" / "trial" / "signals"


def _stale(name: str) -> set:
    return grades.stale((ARMS / f"{name}.ges").read_text())


def test_the_committed_twoknobs_arm_reads_nothing_stale():
    assert _stale("twoknobs") == set()


def test_draft_one_hears_the_phase_before_the_step():
    found = grades.stale(grades.draft(1))
    assert found and {(c, o) for _m, c, o in found} == {("y", "p")}
    assert ("clock", "y", "p") in found


def test_draft_two_reads_the_knobs_before_their_turn():
    found = {(m, c, o) for m, c, o in grades.stale(grades.draft(2))}
    assert ("clock + pitchChan", "p", "pk") in found
    assert ("clock + cutoffChan", "y", "ck") in found
    # Alone, a message has nothing to be stale against: only the
    # simultaneous arrivals are wrong, which is what the golden said.
    assert not {m for m, _c, _o in found if "+" not in m}


def test_bounce_reads_the_old_velocity_and_says_so():
    """Explicit Euler: the position moves by the velocity before the
    reflection.  Correct, and a decision about *when a value is read* —
    so the rule asks for it written, `pre dx`."""
    assert {(c, o) for _m, c, o in _stale("bounce")} == {("x", "dx"), ("y", "dy")}


def test_blip_knob_and_tic_tac_toe_read_nothing_stale():
    for name in ("blip", "knob", "tic-tac-toe"):
        assert _stale(name) == set(), name
