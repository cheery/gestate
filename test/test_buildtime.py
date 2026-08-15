"""`GESTATE_BUILD_TIME` — the stopwatch that keeps a rebuild honest.

The thing this measures went from 400 ms to twelve seconds without one
test failing, because nothing was watching the clock.  So what is tested
here is what makes it worth leaving switched on in the code: that it
costs nothing when nobody asked, that the numbers it prints are *own*
time rather than a caller's time counted twice, and that `‖` means what
it says — two threads at once, and not merely two threads.
"""

from __future__ import annotations

import threading
import time

from gestate.buildtime import building, phase


def _report(capsys) -> str:
    return capsys.readouterr().err


def test_nobody_asked_so_nothing_is_measured(capsys, monkeypatch):
    """Off is the normal case, and it has to be free: `phase` hands back
    a shared do-nothing rather than a timer nobody will read."""
    from gestate import buildtime

    monkeypatch.delenv("GESTATE_BUILD_TIME", raising=False)
    with building("quiet.ges"):
        with phase("front end") as p:
            pass
        assert p is buildtime._OFF
    assert _report(capsys) == ""


def test_a_build_says_where_its_seconds_went(capsys, monkeypatch):
    monkeypatch.setenv("GESTATE_BUILD_TIME", "1")
    with building("noisy.ges"):
        with phase("front end"):
            time.sleep(0.02)
    said = _report(capsys)
    assert said.startswith("[build] noisy.ges "), said
    assert "front end" in said


def test_a_phase_inside_another_is_counted_once(capsys, monkeypatch):
    """The hole scan runs inside the knob placement.  Counting it in
    both would make the column read as if the build cost twice what it
    did — so a caller reports its own time and the child reports the
    rest."""
    monkeypatch.setenv("GESTATE_BUILD_TIME", "1")
    with building("nested.ges"):
        with phase("knobs"):
            time.sleep(0.01)
            with phase("holes"):
                time.sleep(0.05)
    rows = _rows(_report(capsys))
    assert rows["holes"] > rows["knobs"], rows
    assert rows["knobs"] < 0.04, rows


def test_the_parallel_mark_is_about_the_clock_and_not_the_thread(
        capsys, monkeypatch):
    """`pipeline._deep_stack` runs the front end on a worker and *waits*
    for it.  That is another thread and it is not concurrency; marking it
    `‖` would say the column overlaps when it does not."""
    monkeypatch.setenv("GESTATE_BUILD_TIME", "1")
    with building("handed-off.ges"):
        worker = threading.Thread(target=lambda: _sleep_in("front end", 0.02))
        worker.start()
        worker.join()                     # the caller is blocked meanwhile
        with phase("knobs"):
            time.sleep(0.01)
    said = _report(capsys)
    assert "‖" not in said, said


def test_work_that_really_overlaps_is_marked(capsys, monkeypatch):
    """And the case the mark exists for: `Workbench.start` walks the
    canvas and the score on a side thread while `clang` runs."""
    monkeypatch.setenv("GESTATE_BUILD_TIME", "1")
    with building("side-by-side.ges"):
        worker = threading.Thread(target=lambda: _sleep_in("substrate", 0.05))
        worker.start()
        with phase("clang"):
            time.sleep(0.05)
        worker.join()
    said = _report(capsys)
    assert "‖ substrate" in said, said
    assert "‖ clang" in said, said


def test_the_front_end_reports_itself(capsys, monkeypatch):
    """The wiring, not the mechanism: a real front end run inside a
    build is a phase, and one answered from the cache is not — because
    the number wanted is front ends actually run."""
    from gestate.pipeline import analyse, forget_analyses

    monkeypatch.setenv("GESTATE_BUILD_TIME", "1")
    src = "main : Int\nmain = 1 + 2\n"
    forget_analyses()
    with building("first.ges"):
        analyse(src)
    assert "front end" in _report(capsys)

    with building("again.ges"):
        analyse(src)                      # the same text, still in hand
    assert "front end" not in _report(capsys)


def _sleep_in(name: str, seconds: float) -> None:
    with phase(name):
        time.sleep(seconds)


def _rows(said: str) -> dict:
    """`name → seconds`, read back off the report's own lines."""
    out = {}
    for line in said.splitlines()[1:]:
        parts = line.split()
        if parts[-1].startswith("×"):
            parts.pop()
        took = float(parts.pop().rstrip("s"))
        out[" ".join(p for p in parts if p != "‖")] = took
    return out
