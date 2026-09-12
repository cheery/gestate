"""`card:gex-sheet.md` — a `.notes` file as a grid, the first sheet.

Off the shelf 2026-09-12: the textbox is the window's own line editor
(B), `.notes` the first grid.  What these hold: the grid library and
its host restate one arithmetic; the program draws every record as a
row and every cell carries its meaning; a press names the line and the
field; `field` sets one field of one record by key and the file stays
canonical; and the program's text does not change when a value does —
the drawn-scores lesson, held from the first day.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from gestate import gridbox, notes

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "examples" / "audio" / "arc.notes"
LIB = ROOT / "gestate" / "grid.ges"


def _rels(text: str | None = None):
    text = NOTES.read_text() if text is None else text
    return notes.relations_of(text, "arc.notes")


def _kind():
    return notes._kinds(NOTES).kind("note")


# ── The library and its host say one thing ──────────────────────────────


def test_gridbox_restates_the_library_numbers():
    """`gridbox.COLS` and `ROW_H` are `grid.ges`' `gridCols` and
    `gridRowH` — one arithmetic, two readers, as `scorebox` and
    `roll.ges` are held."""
    src = LIB.read_text()
    assert int(re.search(r"^gridCols = (\d+)$", src, re.M).group(1)) == gridbox.COLS
    assert int(re.search(r"^gridRowH = (\d+)$", src, re.M).group(1)) == gridbox.ROW_H


def test_the_grid_library_is_in_front_of_a_program_that_names_a_grid():
    """`audio.preludes` puts `grid.ges` after `roll.ges` for a program
    that declares a grid's rows channel, and not for a hand-written
    canvas or a page without one."""
    from gestate.audio import _GUI_GRID, _GUI_ROLL, has_grid, preludes

    text, _chans = gridbox.grid_program(_rels())
    assert has_grid(text)
    page = text + "\nsubstrate : Sig Sub\nsubstrate = __grid_0__\n"
    assert preludes(page) is _GUI_GRID
    assert "gridPage" in _GUI_GRID and _GUI_GRID.startswith(_GUI_ROLL)
    assert not has_grid("substrate : Sig Sub\nsubstrate = !(Gap 1 1)\n")


# ── The picture: a row per record, a meaning per cell ───────────────────


def test_the_program_draws_every_record_as_a_row_and_every_cell_carries_its_meaning():
    """291 notes of `arc.notes`: 292 rows of labels counting the head,
    2,619 attachments on one channel, each cell's meaning
    `row * COLS + col`, and a press at the cell's own rectangle —
    `gridbox.cell_rect`, the host's arithmetic — is answered by the
    picture with that meaning.  The two machines agree by construction:
    the hit table *is* the picture's.

    *Measured 2026-09-12 on the reference machine: compile 0.99 s, the
    first picture 5.9 s for 5,257 items — the Python interpreter's own
    cost per item, as the roll's 366 ms for 248 items is; the window
    walks in Rust and is not measured here.*
    """
    from gestate.gui import Substrate, _attachments

    rels = _rels()
    text, chans = gridbox.grid_program(rels)
    assert chans == ["__ng_cell_0__"]
    view = Substrate(text + "\nsubstrate : Sig Sub\nsubstrate = __grid_0__\n",
                     22050, entry="__grid_0__")
    reading = gridbox.grid_reading(rels)
    kind = _kind()
    cols = len(kind.fields)
    rows = len(reading) // cols
    assert rows == len(notes.notes_of(rels)) == 291
    assert view.write("__ng_rows_0__", reading)
    view.tick()
    pic = view.picture()
    texts = [i for i in pic if i[0] == "text"]
    assert len(texts) == (rows + 1) * cols
    assert [i[3] for i in texts[:cols]] == [f.name.upper() for f in kind.fields]
    hits = _attachments(view.signal.value, view.state)
    assert len(hits) == rows * cols
    assert sorted(int(h["means"]) for h in hits) == sorted(
        r * gridbox.COLS + c for r in range(rows) for c in range(cols))
    # A press aimed by the host's arithmetic lands on the cell the
    # picture says it is.
    W, H = gridbox.page_size(kind, rows)
    x0, y0 = -(W // 2), -(H // 2)
    for row, col in ((0, 0), (5, 7), (rows - 1, cols - 1)):
        x, y, w, h = gridbox.cell_rect(kind, row, col)
        said = view.touch("press", x0 + x + w // 2, y0 + y + h // 2)
        assert said == ("touched", "__ng_cell_0__", float(row * gridbox.COLS + col)), (row, col, said)
        view.touch("release", 0, 0)


def test_a_cell_shows_the_value_the_file_has_there():
    """The reading is numbers and the program shows them as the file
    writes them: a word by the file's own table, a level by the
    declaration's list, a set of manners as bits, an absent field as `-`."""
    rels = _rels()
    kind = _kind()
    records = notes.notes_of(rels)
    words = gridbox.words_of(rels, kind, records)
    assert "melody" in words and "A" in words
    fields = list(kind.fields)
    names = [f.name for f in fields]
    one = records[2]                                  # bar 1, at 192, accent
    row = gridbox.record_reading(one, fields, words)
    assert row[names.index("at")] == 192
    assert words[row[names.index("voice")]] == "melody"
    assert row[names.index("vel")] == ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"].index("f")
    assert row[names.index("manner")] == 1 << ["staccato", "accent", "portamento"].index("accent")
    assert row[names.index("spell")] == -1
    text, _c = gridbox.grid_program(rels)
    assert '1 -> "staccato"' in text and '2 -> "accent"' in text
    assert '5 -> "f"' in text


# ── A press names the line and the field ────────────────────────────────


class _Bench:
    kind = object()
    playing = False

    def __init__(self, rels):
        self.path = NOTES
        self.grid_regions = gridbox.grid_regions(rels)
        self.previewing = {}
        self.auditioned = []

    def audition(self, text):
        self.auditioned.append(text)


class _View:
    saved = True

    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text

    def replace(self, text):
        self._text = text
        return True

    def show(self, what):
        return True

    orders: list = []

    def ask(self, verb, *given):
        self.orders.append(("ask", verb, *given))
        return True

    def fill(self, text):
        self.orders.append(("fill", text))
        return True


def _seat(text: str | None = None):
    from gestate.session import Session

    text = NOTES.read_text() if text is None else text
    seat = Session(bench=_Bench(_rels(text)))
    seat.view = _View(text)
    seat.view.orders = []
    return seat


def test_a_press_on_a_cell_names_the_line_and_the_field():
    """The meaning crosses, the model answers with what the file says
    there, and the selection outlives the press — in `grid_cell` and on
    the box's `sel` channel for the picture."""
    seat = _seat()
    region = seat.bench.grid_regions["__ng_cell_0__"]
    names = list(region.fields)
    row = 5
    one = region.rows[row]
    said = seat.touched("__ng_cell_0__", row * gridbox.COLS + names.index("vel"))
    assert said == f"line {one['line']}: vel {one['vel']}"
    assert seat.grid_cell[0] == (row, names.index("vel"))
    assert seat.bench.previewing[region.sel] == float(row * gridbox.COLS + names.index("vel"))
    # An absent field reads `-`, a set of manners reads as the file writes it.
    assert seat.touched("__ng_cell_0__", row * gridbox.COLS + names.index("spell")).endswith(": spell -")
    accented = next(i for i, r in enumerate(region.rows) if r["manner"])
    said = seat.touched("__ng_cell_0__", accented * gridbox.COLS + names.index("manner"))
    assert said.endswith(": manner " + ",".join(region.rows[accented]["manner"]))
    # A meaning past the table is refused, not indexed.
    assert seat.touched("__ng_cell_0__", 10_000 * gridbox.COLS) == "grid: no cell there"


def test_a_press_asks_the_window_for_the_value_with_the_cell_filled_in():
    """Reading B, built on what `complete` already had: the press orders
    the palette to ask `field` with the region, the record's key and
    the field given, and the cell's own value in the box — so Return
    is the edit.  An absent field leaves the box empty; a refused
    press asks nothing."""
    seat = _seat()
    region = seat.bench.grid_regions["__ng_cell_0__"]
    names = list(region.fields)
    seat.touched("__ng_cell_0__", 0 * gridbox.COLS + names.index("vel"))
    key = "note section A bar 1 voice melody at 0 key 62"
    assert seat.view.orders == [("ask", "field", "__ng_cell_0__", key, "vel"),
                                ("fill", "ff")]
    seat.view.orders = []
    seat.touched("__ng_cell_0__", 0 * gridbox.COLS + names.index("spell"))
    assert seat.view.orders == [("ask", "field", "__ng_cell_0__", key, "spell")]
    seat.view.orders = []
    seat.touched("__ng_cell_0__", 10_000 * gridbox.COLS)
    assert seat.view.orders == []


def test_the_row_names_the_records_key_in_the_documents_own_syntax():
    """What `field` and `retract` take — the model's key, never the
    picture's index."""
    region = gridbox.grid_regions(_rels())["__ng_cell_0__"]
    assert gridbox.key_of(region, 0) == "note section A bar 1 voice melody at 0 key 62"


# ── `field`: one field of one record, by key ────────────────────────────


def test_field_sets_one_field_of_one_line_and_nothing_else():
    """One token of one line changes; every other byte of the file is
    the same; the file comes back canonical; the edit sounds."""
    seat = _seat()
    before = seat.view.text()
    key = "note section A bar 1 voice melody at 0 key 62"
    said = seat.do_field("__ng_cell_0__", key, "vel", "f")
    assert said == "field: arc.notes — set vel ff → f on line 9"
    # And through the door the window's palette uses — the gesture is
    # tab-split, so a key with spaces arrives as one argument.
    seat2 = _seat()
    assert seat2.run("field", "__ng_cell_0__", key, "vel", "f") == said
    after = seat.view.text()
    changed = [(a, b) for a, b in zip(before.splitlines(), after.splitlines()) if a != b]
    assert len(changed) == 1
    a, b = changed[0]
    assert a.replace("vel ff", "vel f") == b
    assert notes.canonical(after, "arc.notes") == after
    assert seat.bench.auditioned == [after]


def test_field_is_refused_in_the_parsers_words_and_the_file_stands():
    """A value the field may not say, a field the kind has not, a key
    naming no record, a required field dropped: each refused by name,
    and the file is the file it was."""
    seat = _seat()
    before = seat.view.text()
    key = "note section A bar 1 voice melody at 0 key 62"
    assert "not a dynamic" in seat.do_field("__ng_cell_0__", key, "vel", "loud")
    assert "no field `colour`" in seat.do_field("__ng_cell_0__", key, "colour", "red")
    assert "no `note` here says that" in seat.do_field(
        "__ng_cell_0__", "note section A bar 1 voice melody at 0 key 99", "vel", "f")
    assert "has 8 bars" in seat.do_field("__ng_cell_0__", key, "bar", "9")
    said = seat.do_field("__ng_cell_0__", key, "vel", "-")
    assert said.startswith("field: ") and "vel" in said
    assert "no grid region" in seat.do_field("__nb_rail_0__", key, "vel", "f")
    assert seat.view.text() == before


def test_field_on_a_key_field_refuses_a_double_and_drops_the_spelling():
    """Setting `key` moves the record's identity: onto another note it
    is refused as a doubled line; and the spelling goes with the key it
    spelt, as a drag drops it."""
    text = NOTES.read_text()
    key = "note section A bar 1 voice melody at 0 key 62"
    # The bass sounds 38 at tick 0 and again at tick 192 of bar 1;
    # setting the second one's `at` to 0 would say the first line twice.
    with pytest.raises(notes.NotesError, match="doubled line"):
        notes.assigned(text, "note section A bar 1 voice bass at 192 key 38",
                       "at", "0", "arc.notes", where=NOTES)
    # A spelling written on a note goes when its key is set.
    spelt = text.replace("key 62  vel ff", "key 62  spell d4  vel ff", 1)
    out, said = notes.assigned(spelt, key, "key", "63", "arc.notes", where=NOTES)
    assert "spell d4" in said and "spell d4" not in out
    assert "key 63  vel ff" in out


def test_the_program_text_does_not_change_when_a_value_does():
    """The drawn-scores lesson, held on the first day: a field set is a
    new reading and never a new program.  The text depends on the kind
    and the file's words; the reading differs in one number."""
    rels = _rels()
    text, _c = gridbox.grid_program(rels)
    out, _said = notes.assigned(NOTES.read_text(),
                                "note section A bar 1 voice melody at 0 key 62",
                                "vel", "f", "arc.notes", where=NOTES)
    after = _rels(out)
    text2, _c = gridbox.grid_program(after)
    assert text2 == text
    a, b = gridbox.grid_reading(rels), gridbox.grid_reading(after)
    assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


# ── The bench: `grid` draws the file's records in the canvas view ────────


def test_a_notes_file_opened_alone_draws_the_grid_when_asked():
    """`grid` sets the bench's `grid_view`; the next build grows the
    page's program by the grid's box, the canvas view takes its entry,
    the rows cross as a trace beside the roll's, and the cell channel
    is a region a press can name.  `roll` puts the page back."""
    from test_drawnscores import _opened_alone

    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    assert bench.substrate is not None and not bench.grid_regions
    page = bench.substrate
    bench.grid_view = True
    bench._load_substrate(bench.program())
    assert "__ng_cell_0__" in bench.grid_regions
    assert bench.substrate is not page
    assert bench.substrate.entry == "__grid_0__"
    said = dict(bench.note_rows)
    assert "__ng_rows_0__" in said and len(said["__ng_rows_0__"]) == 291 * 9
    assert sum(c.startswith("__nb_rc_") for c in said) == 3
    bench.grid_view = False
    bench._load_substrate(bench.program())
    assert not bench.grid_regions and bench.substrate.entry == "substrate"
