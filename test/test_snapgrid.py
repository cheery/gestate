"""`card:snap-grid.md` — a bar may be told the grid its notes snap to.

Henri, 2026-09-24: *"Maybe the grid should be a property of the bars
themselves, eg. "section A bar 1 grid 1/8""* — and, of three readings,
*"sparse bar record."*  A bar with no record is `auto`, the roll's grid
as before.  The grid is spelled as a fraction of a whole note, so a
triplet needs no sign: an eighth triplet is `1/12`.
"""

import pytest

from gestate import notes

HEAD = "section A  bars 2  beats 4  voices a\n"
ONE = "note  section A  bar 2  at 0  len 96  voice a  key 60  vel mf\n"


# ── Slice 1: the record ─────────────────────────────────────────────────────


def test_a_bar_record_is_read_as_its_section_bar_and_grid():
    rels = notes.parse(HEAD + "bar  section A  bar 2  grid 1/8\n" + ONE, "t.notes")
    assert [{k: one[k] for k in ("section", "bar", "grid")}
            for one in notes.bars_of(rels)] == [{"section": "A", "bar": 2, "grid": "1/8"}]


def test_a_file_without_one_has_none():
    assert notes.bars_of(notes.parse(HEAD + ONE, "t.notes")) == []


@pytest.mark.parametrize("line, says", [
    ("bar  section B  bar 1  grid 1/8", "section `B`"),
    ("bar  section A  bar 3  grid 1/8", "bar 3"),
    ("bar  section A  bar 1  grid 1/7", "1/7"),
])
def test_a_bar_record_is_refused_where_a_note_would_be(line, says):
    with pytest.raises(notes.NotesError, match=says.replace("/", "/")):
        notes.parse(HEAD + line + "\n", "t.notes")


def test_one_bar_is_told_its_grid_once():
    """Two grids for one bar is not one fact said twice, as a doubled note
    is — it is two facts that disagree, and the file cannot say which."""
    with pytest.raises(notes.NotesError, match="bar 1 of section `A`"):
        notes.parse(HEAD + "bar  section A  bar 1  grid 1/8\n"
                    "bar  section A  bar 1  grid 1/16\n", "t.notes")


def test_the_record_is_written_at_the_head_of_its_bar():
    """Where a reader of the file looks for what a bar is — above its
    notes, and still there when the bar has none."""
    text = (HEAD + "\n" + ONE + "bar  section A  bar 2  grid 1/12\n"
            "bar  section A  bar 1  grid 1/16\n")
    written = notes.write(notes.parse(text, "t.notes"))
    assert written == (
        HEAD + "\n"
        "bar  section A  bar 1  grid 1/16\n"
        "\n"
        "bar  section A  bar 2  grid 1/12\n"
        "note  section A  bar 2  at 0  len 96  voice a  key 60  vel mf\n")
    assert notes.write(notes.parse(written, "t.notes")) == written


def test_every_grid_the_toolbar_offers_is_one_the_file_takes():
    for grid in notes.GRIDS:
        rels = notes.parse(HEAD + f"bar  section A  bar 1  grid {grid}\n", "t.notes")
        assert notes.bars_of(rels)[0]["grid"] == grid


def test_the_grids_are_the_declaration_s_in_its_order():
    """`notes.GRIDS` is the Python's copy of `notes.ges`' `grids`, and a
    copy is held to its source or it drifts."""
    from gestate.facts import load
    grid = next(f for f in load("notes")["bar"].fields if f.name == "grid")
    assert grid.domain == ("OneOf", tuple(notes.GRIDS))


def test_every_grid_divides_a_beat():
    from gestate.midi import TICKS_PER_BEAT
    for name, ticks in notes.GRIDS.items():
        whole = 4 * TICKS_PER_BEAT
        assert whole // int(name.split("/")[1]) == ticks
        assert TICKS_PER_BEAT % ticks == 0


@pytest.mark.parametrize("line, key", [
    ("bar  section B  bar 1  grid 1/8", ("B", 1)),
    ("bar  section A  bar 3  grid 1/8", ("A", 3)),
])
def test_the_declaration_s_road_refuses_what_the_parser_refuses(line, key):
    """Both roads, one boundary — `test_relations.py`'s parity, for the
    record that came after it."""
    rels = notes.relations_of(HEAD + line + "\n", "t.notes")
    assert ("bar", key) in notes.refused(rels)


def test_both_roads_agree_on_a_file_with_a_bar_record():
    text = HEAD + "bar  section A  bar 2  grid 1/24  # a fill\n" + ONE
    a, b = notes.relations_of(text, "t.notes"), notes.parse(text, "t.notes")
    assert a.keys() == b.keys()
    for name in a:
        assert a[name] == b[name], name
    assert notes.refused(a) == set()


# ── Slice 2: the snap reads it ──────────────────────────────────────────────
#
# His piece, `arc.notes`, is written in quarters: its roll's own grid is
# 96 ticks, so an eighth could not be reached — the `because`.  Bar 2 of
# section A is told `1/8` here, and bar 1 is told nothing.


def _told_page(grid: str = "1/8"):
    """A copied `arc.notes` with bar 2 of section A told `grid`, rolled
    the way the window draws it."""
    import contextlib

    from test_drawnscores import _copied, _rolled_page

    @contextlib.contextmanager
    def opened():
        with _copied() as here:
            path = here.parent / "arc.notes"
            text = path.read_text()
            path.write_text(text.replace(
                "\nnote  section A  bar 2 ",
                f"\nbar  section A  bar 2  grid {grid}\nnote  section A  bar 2 ", 1))
            yield (here, *_rolled_page(here, page=True))
    return opened()


def test_the_roll_knows_each_bar_s_grid_and_a_bar_told_nothing_is_auto():
    from gestate.scorebox import grid_at, grid_of

    with _told_page() as (_here, roll, _seat):
        assert grid_of(roll) == 96, "his piece is in quarters"
        assert grid_at(roll, roll.bars[1]) == 48
        assert grid_at(roll, roll.bars[1] + 300) == 48
        assert grid_at(roll, roll.bars[0]) == 96, "bar 1 is told nothing"
        assert grid_at(roll, roll.bars[2]) == 96


def test_two_clicks_in_a_bar_told_an_eighth_make_an_eighth_on_an_eighth():
    """The postcondition's first verb, the way a person does it."""
    from gestate.scorebox import across_of, reach_of
    from test_drawnscores import _empty_key

    with _told_page() as (here, roll, seat):
        low, high = reach_of(roll)
        tick = roll.bars[1] + 48 + 5          # a hand is never exact
        key = _empty_key(roll, tick)
        where = (high - key) / (high - low)
        before = (here.parent / "arc.notes").read_text().splitlines()

        def click():
            seat.touched("__nb_rail_0__", across_of(roll, tick))
            seat.touched("__nb_pitch_0__", where)
            seat.released("__nb_pitch_0__")
            return seat.released("__nb_rail_0__")

        click()
        said = click()
        now = (here.parent / "arc.notes").read_text().splitlines()
        made = [l for l in now if l not in before]
        assert len(made) == 1, said
        assert "bar 2  at 48  len 48" in made[0], made[0]


def test_a_move_in_a_bar_told_an_eighth_steps_by_an_eighth():
    from gestate.session import Session

    with _told_page() as (_here, roll, _seat):
        on = roll.bars[1]
        assert Session._snapped(roll, on, 50) == on + 48
        assert Session._snapped(roll, on, 0) == on, "let go unmoved: a click"
        assert Session._snapped(roll, roll.bars[0], 50) == roll.bars[0] + 96, \
            "bar 1 is told nothing, and snaps as before"


def test_a_note_in_a_bar_told_an_eighth_lengthens_by_an_eighth():
    from gestate.session import Session

    with _told_page() as (_here, roll, _seat):
        on = roll.bars[1]
        assert Session._length_of(roll, on, 96, 50) == 144
        assert Session._length_of(roll, on, 96, -60) == 48, "an eighth is the least"
        assert Session._length_of(roll, roll.bars[0], 96, 50) == 192


def test_a_bar_told_a_triplet_makes_a_triplet():
    from gestate.scorebox import grid_at

    with _told_page("1/12") as (_here, roll, _seat):
        assert grid_at(roll, roll.bars[1]) == 32


# ── Slice 3: the verb, and the bar it lands on ──────────────────────────────
#
# `snap A 2 1/8` names its bar, so a transcript replays the same edit;
# which bar the toolbar fills in is the session's to remember — *"the
# last clicked/edited bar would be what is modified."*


def test_telling_a_bar_writes_one_record_and_auto_takes_it_back():
    text = HEAD + "# the head\n" + ONE
    told, said = notes.told(text, "A", 2, "1/8", "t.notes")
    assert "bar  section A  bar 2  grid 1/8\n" in told
    assert said == "section A bar 2 grid 1/8"
    again, said = notes.told(told, "A", 2, "1/16", "t.notes")
    assert "grid 1/16" in again and "grid 1/8" not in again
    assert said == "section A bar 2 grid 1/8 → 1/16"
    back, said = notes.told(again, "A", 2, "auto", "t.notes")
    assert back == notes.write(notes.parse(text, "t.notes"))
    assert said == "section A bar 2 grid 1/16 → auto"


@pytest.mark.parametrize("section, bar, grid, says", [
    ("A", 2, "1/7", "`grid 1/7` is not a grid"),
    ("A", 3, "1/8", "section `A` has 2 bars"),
    ("B", 1, "1/8", "no section `B`"),
])
def test_telling_a_bar_refuses_in_the_file_s_own_words(section, bar, grid, says):
    with pytest.raises(notes.NotesError, match=says):
        notes.told(HEAD + ONE, section, bar, grid, "t.notes")


def test_telling_a_bar_what_it_is_already_told_has_nothing_to_do():
    assert notes.told(HEAD + ONE, "A", 2, "auto", "t.notes") == (
        None, "nothing to do — section A bar 2 is auto")


def test_a_record_s_prose_stays_when_its_grid_changes():
    text = HEAD + "# a fill, faster\nbar  section A  bar 2  grid 1/8\n" + ONE
    told, _ = notes.told(text, "A", 2, "1/16", "t.notes")
    assert "# a fill, faster\nbar  section A  bar 2  grid 1/16\n" in told


def _page():
    from test_drawnscores import _page_seat
    return _page_seat()


def test_the_verb_tells_the_bar_on_his_page_and_the_roll_follows():
    from gestate.scorebox import grid_at

    _here, seat, _view, roll = _page()
    said = seat.run("snap", "A", 2, "1/8")
    assert said.startswith("snap: arc.notes — section A bar 2 grid 1/8"), said
    assert "bar  section A  bar 2  grid 1/8" in seat.view.text()
    assert any(step.verb == "snap" for step in seat.log.steps)
    assert seat.run("snap", "A", 2, "1/8").startswith("snap: nothing to do")
    assert seat.run("snap", "A", 9, "1/8") == "snap: arc.notes:5: `bar 9` — section `A` has 8 bars"
    assert seat.run("snap", "A", 2, "auto").startswith("snap: arc.notes — section A bar 2 grid 1/8 → auto")
    assert "grid" not in seat.view.text()


def test_a_press_on_the_roll_is_the_bar_the_toolbar_tells():
    """*"the last clicked/edited bar would be what is modified."*"""
    from gestate.scorebox import x_of, y_of
    from test_drawnscores import _empty_key, _feed

    _here, seat, view, roll = _page()
    assert seat.bar_at is None, "nothing pressed, nothing to tell"
    tick = roll.bars[2] + 10
    x, y = x_of(roll, tick), y_of(roll, _empty_key(roll, tick))
    _feed(seat, view, "press", x, y)
    _feed(seat, view, "release", x, y)
    assert seat.bar_at == ("A", 3)
