"""Two things one press reaches — `card:gui-is-difficult.md` Q8 and Q9,
his answers of 2026-10-02: *refuse* two writers of one fact kind on one
press, answered by *the inner one takes it*, tried in a small program.

`examples/gui/two-hands.ges`: a cell asserts a `note`, the note drawn
inside it retracts its own.  A press reaches the deepest thing it lands
on and every attachment around it (`gui._grabbed`), so a press on the
note reaches the cell too.  Before this, both ran in the walk's order —
retract, then assert — and the note stayed where it was with the file
written twice and nothing said.  The 2026-09-23 band that moved the
notes was the same shape in the editor's own boxes.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "examples" / "gui" / "two-hands.ges"
DOTS = GAME.with_suffix(".dots")
TAKES = "    True -> Takes ("


def _copy(word: str = "Takes"):
    tmp = Path(tempfile.mkdtemp())
    game, dots = tmp / GAME.name, tmp / DOTS.name
    text = GAME.read_text()
    assert TAKES in text, "the example no longer says `Takes` where the test edits it"
    game.write_text(text.replace(TAKES, f"    True -> {word} ("))
    shutil.copy(DOTS, dots)
    return game, dots


def _bench(game):
    from gestate.audioeditor import Workbench

    bench = Workbench(game, rate=22050, block=256)
    bench._load_substrate(bench.program())
    bench.drain()
    return bench


def _press(bench, step: int, key: int) -> list:
    """The centre of a cell: eight across from step 0, four up from key 0."""
    x, y = -119 + 34 * step, 51 - 34 * key
    bench.touch("press", x, y)
    bench.touch("release", x, y)
    return bench.drain()


def _notes(dots) -> list:
    return [l for l in dots.read_text().splitlines() if l.startswith("note")]


def test_an_empty_cell_asks_for_a_note():
    game, dots = _copy()
    bench = _bench(game)
    assert _press(bench, 1, 0) == ["two-hands.dots — asserted note  step 1  key 0"]
    assert "note  step 1  key 0" in _notes(dots)


def test_a_note_that_takes_the_press_goes_and_the_cell_around_it_hears_nothing():
    game, dots = _copy()
    bench = _bench(game)
    assert _press(bench, 0, 0) == ["two-hands.dots — retracted note step 0 key 0"]
    assert "note  step 0  key 0" not in _notes(dots)


def test_two_writers_of_one_kind_on_one_press_are_refused_and_nothing_is_written():
    game, dots = _copy("Does")
    bench = _bench(game)
    before = dots.read_text()
    said = _press(bench, 0, 0)
    assert len(said) == 1 and "two things that write `note`" in said[0], said
    assert "onTake" in said[0], "the refusal names the answer"
    assert dots.read_text() == before, "a refused press writes nothing"


def test_the_refusal_is_the_hosts_and_the_grab_is_the_walks():
    """The two halves apart: `_grabbed` stops at a `Takes`, and
    `two_writers` says a sentence only when two grabbed things share a
    kind — so a press that reaches two writers of *different* kinds is
    not refused."""
    from gestate.gui import _grabbed, two_writers

    inner = {"region": (10, 10, 20, 20), "does": None, "takes": False}
    takes = dict(inner, takes=True)
    outer = {"region": (0, 0, 30, 30), "does": None, "takes": False}
    assert _grabbed([inner, outer], 15, 15) == [inner, outer]
    assert _grabbed([takes, outer], 15, 15) == [takes]

    note = lambda: ("Assert", [ord(c) for c in "note"], [])
    mark = ("Retract", [ord(c) for c in "mark"], [])
    assert two_writers([[note()], [note()]]) is not None
    assert two_writers([[note()], [mark]]) is None
    assert two_writers([[note(), note()]]) is None, "one thing writing twice is its own order"
