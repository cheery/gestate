"""`reactor` blocks — `gestate/reactors.py`, the slice of
`card:gui-is-difficult.md` §"The next slice: two checkboxes, as reactors".

The example is driven the way the window drives it, on the tests' own
document (`doc/memory/a-shipped-document-gets-played.md`); every check
the block promises is seen refusing a program that breaks it.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from gestate.reactors import GENERATED, ReactorError, desugar

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "gui" / "checkboxes.ges"
TODAY = ROOT / "doc" / "trial" / "reactors" / "checkboxes-today.ges"
DRAG = ROOT / "examples" / "gui" / "drag.ges"
DRAG_TODAY = ROOT / "doc" / "trial" / "reactors" / "drag-today.ges"
DOTS = "dot  name a  x -80\ndot  name b  x 0\ndot  name c  x 80\n"
OFF, ON = (38, 42, 52), (240, 184, 72)


def _bench(game: Path, flags: str = "flag  name mute\n", suffix: str = ".flags"):
    from gestate.audioeditor import Workbench

    tmp = Path(tempfile.mkdtemp())
    shutil.copy(game, tmp)
    doc = tmp / game.with_suffix(suffix).name
    doc.write_text(flags)
    bench = Workbench(tmp / game.name, rate=22050, block=256)
    bench._load_substrate(bench.program())
    bench.drain()
    return bench, doc


def _inks(bench) -> list:
    return [i[5] for i in bench.substrate.picture() if i[0] == "rect"]


def _press(bench, row: int) -> list:
    """Row 0 is mute, row 1 solo — the centre of each, never an edge."""
    y = -10 + 20 * row
    bench.touch("press", -30, y)
    bench.touch("release", -30, y)
    return bench.drain()


@pytest.mark.parametrize("game", [EXAMPLE, TODAY], ids=["reactors", "today"])
def test_a_press_flips_its_own_fact_and_only_its_own(game):
    bench, doc = _bench(game)
    assert _inks(bench) == [ON, OFF], "the file says mute, and nothing else"
    said = _press(bench, 0)
    assert said and "retracted flag name mute" in said[0]
    assert _inks(bench) == [OFF, OFF]
    said = _press(bench, 1)
    assert said and "asserted flag  name solo" in said[0]
    assert _inks(bench) == [OFF, ON]
    assert [l for l in doc.read_text().splitlines() if l.startswith("flag")] == ["flag  name solo"]


def test_the_boxes_follow_a_hand_edit_of_the_file():
    """No copy: the box is the lens's view, so the file is the truth."""
    bench, doc = _bench(EXAMPLE, flags="")
    assert _inks(bench) == [OFF, OFF]
    doc.write_text("flag  name mute\nflag  name solo\n")
    bench.tick()
    assert _inks(bench) == [ON, ON]


def test_it_opens_the_way_the_window_opens_it():
    from gestate import audio, notes

    audio.render(notes.read(EXAMPLE), seconds=0.01)


def test_the_block_is_blanked_in_place_and_desugaring_twice_changes_nothing():
    src = EXAMPLE.read_text()
    once = desugar(src)
    author = once.split(GENERATED)[0].rstrip("\n").split("\n")
    assert len(author) == len(src.rstrip("\n").split("\n")), "no author line moved"
    assert not any(l.startswith("reactor ") for l in author)
    assert desugar(once) == once
    assert desugar("x : Int\nx = 1\n") == "x : Int\nx = 1\n", "a file with none pays nothing"


# ── the checks, each seen refusing ─────────────────────────────────────────

HEAD = "reactor Box (at : Lens Flags Bool) (other : Lens Flags Bool)\n"


def _refused(block: str) -> str:
    with pytest.raises(ReactorError) as caught:
        desugar(block)
    return str(caught.value)


def test_a_reaction_writes_only_what_its_signature_declares():
    why = _refused(HEAD + "  on press -> at = put other True\n"
                          "  picture = feeds press (Gap 0 0)\n")
    assert "`put other`" in why and "line 2" in why


def test_an_effect_must_be_a_lens_the_reactor_was_given():
    why = _refused(HEAD + "  on press -> nowhere = Nil\n  picture = feeds press (Gap 0 0)\n")
    assert "`nowhere`" in why


def test_get_reads_only_a_parameter():
    why = _refused(HEAD + "  mode A when get ghost\n    picture = Gap 0 0\n")
    assert "`get ghost`" in why


def test_a_region_feeds_only_a_port_someone_hears():
    why = _refused(HEAD + "  on press -> at = put at True\n  picture = feeds tap (Gap 0 0)\n")
    assert "feeds `tap`" in why


def test_two_writers_of_one_lens_in_one_mode_are_refused():
    """The Q8 refusal, now at compile time and over declarations."""
    why = _refused(HEAD + "  mode A when get at\n"
                          "    on press -> at = put at True\n"
                          "    on press -> at = put at False\n"
                          "    picture = feeds press (Gap 0 0)\n")
    assert "two reactions on `press` write `at`" in why and "mode `A`" in why


def test_a_writer_outside_every_mode_is_live_in_each():
    why = _refused(HEAD + "  on press -> at = put at True\n"
                          "  mode A when get at\n"
                          "    on press -> at = put at False\n"
                          "    picture = feeds press (Gap 0 0)\n")
    assert "two reactions on `press` write `at`" in why


def test_two_writers_in_separate_modes_are_allowed():
    """Modal Reactors §VI-C — the checkbox itself."""
    out = desugar(HEAD + "  mode A when get at\n"
                         "    on press -> at = put at False\n"
                         "    picture = feeds press (Gap 0 0)\n"
                         "  mode B when not (get at)\n"
                         "    on press -> at = put at True\n"
                         "    picture = feeds press (Gap 0 0)\n")
    assert "box__A__feeds_press" in out and "box__B__feeds_press" in out


def test_new_names_a_reactor_and_picture_names_an_instance():
    assert "`new Ghost`" in _refused("reactor P\n  x = new Ghost\n  picture = x.picture\n")
    assert "`y.picture`" in _refused(HEAD + "reactor P\n  x = new Box\n  picture = y.picture\n")


# ── a drag: a stored mode, its own hold, the commit on the release ────────
#
# `card:gui-is-difficult.md` §"The next slice: a drag, as a reactor with a
# stored mode", 2026-10-03.  Both programs — the reactor blocks and the
# control written without them — are driven the same way.


def _dots(bench) -> list:
    return [i[1] for i in bench.substrate.picture() if i[0] == "dot"]


def _rows(doc) -> list:
    return [l for l in doc.read_text().splitlines() if l.startswith("dot")]


@pytest.mark.parametrize("game", [DRAG, DRAG_TODAY], ids=["reactors", "today"])
def test_a_drag_moves_its_own_dot_and_writes_the_file_once_on_the_release(game):
    bench, doc = _bench(game, DOTS, ".dots")
    assert _dots(bench) == [-80, 0, 80]
    bench.touch("press", -80, 0)
    bench.touch("drag", -60, 4)
    bench.touch("drag", -40, 9)
    assert _dots(bench) == [-40, 0, 80], "the held dot follows, alone"
    assert _rows(doc) == DOTS.splitlines(), "and nothing is written while it moves"
    assert bench.drain() == []
    bench.touch("release", -40, 9)
    said = bench.drain()
    assert said == [f"{doc.name} — retracted dot name a",
                    f"{doc.name} — asserted dot  name a  x -40"]
    assert _rows(doc) == ["dot  name a  x -40", "dot  name b  x 0", "dot  name c  x 80"]
    assert _dots(bench) == [-40, 0, 80]
    # a second dot, after the first: its own hold, its own mode
    bench.touch("press", 0, 0)
    bench.touch("drag", 300, 0)
    assert _dots(bench) == [-40, 200, 80], "held past the track's end, clamped"
    bench.touch("release", 300, 0)
    bench.drain()
    assert "dot  name b  x 200" in _rows(doc)


def test_the_dots_follow_a_hand_edit_of_the_file():
    """No copy: a dot at rest is its lens's view, so the file is the truth."""
    bench, doc = _bench(DRAG, DOTS, ".dots")
    doc.write_text(DOTS.replace("x 0", "x 50"))
    bench.tick()
    assert _dots(bench) == [-80, 50, 80]


def test_the_drag_opens_the_way_the_window_opens_it():
    from gestate import audio, notes

    audio.render(notes.read(DRAG), seconds=0.01)


def test_each_stored_instance_gets_its_own_hold_and_mode():
    out = desugar(DRAG.read_text())
    for k in "abc":
        assert f"panel__{k}__hold : Chan Event" in out
        assert f"panel__{k}__mode = scanE dot__step DotResting (wait panel__{k}__hold)" in out
    assert "DotMode := DotResting | DotCarrying Int Int" in out


STORED = ("reactor Dot (at : Lens Dots Int)\n"
          "  mode Resting\n"
          "    on grab x y -> Carrying x x\n"
          "    picture = hold (Gap 0 0)\n"
          "  mode Carrying (x0 : Int) (x : Int)\n"
          "    on drag a b -> Carrying x0 a\n"
          "    on release -> Resting\n"
          "    on release -> at = put at x\n"
          "    picture = hold (Gap 0 0)\n")


def test_the_stored_block_itself_is_accepted():
    assert "dot__Carrying__release" in desugar(STORED)


def test_a_transition_reads_only_its_fields_and_the_hand():
    why = _refused(STORED.replace("Carrying x0 a\n", "Carrying x0 (get at)\n"))
    assert "not the model" in why
    why = _refused(STORED.replace("Carrying x0 a\n", "Carrying x0 at\n"))
    assert "`at` is a parameter" in why


def test_a_transition_names_a_mode_the_reactor_has():
    assert "no mode of that name" in _refused(
        STORED.replace("-> Carrying x x", "-> Flying x x"))


def test_two_transitions_on_one_phase_in_one_mode_are_refused():
    why = _refused(STORED.replace("    on release -> Resting\n",
                                  "    on release -> Resting\n"
                                  "    on release -> Carrying 0 0\n"))
    assert "two transitions on `release`" in why


def test_a_hold_writes_nothing_while_the_hand_moves():
    why = _refused(STORED.replace("    on drag a b -> Carrying x0 a\n",
                                  "    on drag a b -> Carrying x0 a\n"
                                  "    on drag -> at = put at x\n"))
    assert "writes nothing while the hand moves" in why


def test_a_stored_mode_and_a_derived_one_do_not_mix():
    why = _refused(STORED.replace("  mode Resting\n", "  mode Resting when True\n"))
    assert "mixes a stored mode with a derived one" in why


def test_hold_needs_a_stored_mode_to_set():
    why = _refused(HEAD + "  on press -> at = put at True\n"
                          "  picture = hold (feeds press (Gap 0 0))\n")
    assert "no stored mode" in why


def test_a_transition_belongs_to_a_mode():
    why = _refused("reactor Dot (at : Lens Dots Int)\n"
                   "  on grab x y -> Resting\n"
                   "  mode Resting\n"
                   "    picture = hold (Gap 0 0)\n")
    assert "belongs to the mode it leaves" in why

