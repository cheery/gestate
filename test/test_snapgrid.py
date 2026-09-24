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
