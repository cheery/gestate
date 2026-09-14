"""A document of any kinds: the generic writer, the two edits, and the
game whose state is a file.

`card:gui-is-difficult.md` §"The mashup, asked", 2026-09-13 — Henri:
*"tic-tac-toe could really go through relational model, and I'd want to
exhibit the facts being stored into and loaded from file, so that its
state is a document."*  The postcondition, written before the build:
a game of tic-tac-toe is played by pressing cells; its board is a plain
file of facts a person can read and edit by hand, so a mark typed into
the file appears on the board and a press on the board appears in the
file; and closing and reopening the window resumes the game from that
file.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from gestate import documents, notes

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "examples" / "audio" / "arc.notes"
GAME = ROOT / "examples" / "gui" / "tic-tac-toe-facts.ges"
BOARD = GAME.with_suffix(".board")

#: The centre of each cell, in the canvas's own pixels — `test_gui.py`'s
#: numbers for the same picture — and the foot below the board.
CELL_X = {0: -60, 1: 0, 2: 60}
CELL_Y = {0: -72, 1: -12, 2: 48}
FOOT = (0, 90)


def _strip(text: str) -> list:
    return [line for line in text.splitlines() if line.strip()]


# ── The generic writer, held to the `.notes` writer ─────────────────────────


def test_the_generic_writer_agrees_with_the_notes_writer_on_his_piece():
    """`declare, hold to parity, derive`: the writer that reads only the
    declaration writes `arc.notes` line for line as the writer that
    knows what a note is — apart from the blank lines that one puts
    between bars, which no declaration says."""
    text = NOTES.read_text()
    theirs = notes.write(notes.parse(text, "arc.notes", where=NOTES))
    mine = documents.write(text, "arc.notes", where=NOTES)
    assert _strip(mine) == _strip(theirs)
    assert len(_strip(mine)) == 298


# ── The game's own document ─────────────────────────────────────────────────


def _copy():
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(GAME, tmp / GAME.name)
    shutil.copy(BOARD, tmp / BOARD.name)
    return tmp / GAME.name, tmp / BOARD.name


def test_a_program_declares_its_own_documents_kinds_and_the_reader_uses_them():
    """The `.ges` beside the `.board` is a GUI program *and* the
    declaration — choice 1: compiled with the canvas's vocabulary and
    `facts.ges` after it, and the document read by the kinds it says."""
    from gestate.facts import beside

    _game, board = _copy()
    doc = beside(board)
    assert doc.names == ("mark",)
    assert doc["mark"].key == ("cell",)
    rels = notes.relations_of("mark  cell 4  mark X\n", board.name, where=board)
    assert rels["mark"].rows == frozenset({(4, "X")})


def test_the_two_edits_refuse_in_the_declarations_words():
    _game, board = _copy()
    text = board.read_text()
    out, said = documents.asserted(text, "mark  cell 4  mark X", board.name, where=board)
    assert said == "asserted mark  cell 4  mark X"
    assert "mark  cell 4  mark X" in out
    with pytest.raises(notes.NotesError, match="already written"):
        documents.asserted(out, "mark  cell 4  mark O", board.name, where=board)
    with pytest.raises(notes.NotesError, match="not within 0–8"):
        documents.asserted(out, "mark  cell 9  mark X", board.name, where=board)
    with pytest.raises(notes.NotesError, match="not one of X O"):
        documents.asserted(out, "mark  cell 2  mark Z", board.name, where=board)
    back, said = documents.retracted(out, "mark cell 4", board.name, where=board)
    assert said == "retracted mark cell 4"
    assert _strip(back) == _strip(text), "the prose came back where it was"
    with pytest.raises(notes.NotesError, match="no `mark` here says that"):
        documents.retracted(back, "mark cell 4", board.name, where=board)


def _code(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def test_the_row_type_is_computed_from_the_kind_and_written_nowhere_by_hand():
    """`card:strict-forms.md`, seam 1, closed 2026-09-14.  The postcondition:
    *a program that declares a document's kinds names its rows' type
    nowhere by hand.*  `type Placing = $(kindRow markKind)` is the one
    line about the row, and it is computed; `(Int, Text)` is not in the
    program's code, and the compiler declares the channel the rows come on."""
    from gestate.gui import Substrate

    text = GAME.read_text()
    assert "(Int, Text)" not in _code(text)
    assert "$(kindRow markKind)" in text and 'document "mark"' in text
    view = Substrate(notes.read(GAME), 22050)
    assert "__doc_mark__" in view.by_name, "the channel is the compiler's, not the text's"


def test_a_kind_edited_in_the_program_changes_what_the_checker_accepts():
    """The other half of the postcondition: *a kind edited in the program
    changes what the checker accepts on the next compile, with no Python
    between.*  A third required column makes a placing a triple, and the
    program's own `(c, m)` patterns no longer fit it — refused by the
    checker at the first of them, from the kind alone, with the triple
    the kind now implies in the message."""
    from gestate.gui import Substrate

    text = GAME.read_text()
    edited = text.replace(
        'Field "mark" (OneOf marks) Must :: Nil)',
        'Field "mark" (OneOf marks) Must :: Field "turn" Number Must :: Nil)')
    assert edited != text
    with pytest.raises(Exception) as why:
        Substrate(notes.expand(edited, GAME.parent), 22050)
    said = str(why.value)
    assert "expected (a, b)" in said and "got (Int, String, Int)" in said, said
    assert "while checking `markAt`" in said, said


def test_a_document_of_an_undeclared_kind_is_refused_on_its_line():
    """A stage-one refusal carries its position the way every compiler
    complaint does, and `audiospans.in_source` moves it back into the
    author's file — the line `document "marks"` stands on."""
    from gestate.audiospans import in_source
    from gestate.gui import Substrate
    from gestate.stage import StageError

    text = GAME.read_text().replace('document "mark"', 'document "marks"')
    line = next(i for i, l in enumerate(text.splitlines(), 1)
                if l.startswith('board = document "marks"'))
    opened = notes.expand(text, GAME.parent)
    with pytest.raises(StageError, match='`document "marks"` names no kind') as why:
        Substrate(opened, 22050)
    assert "`kinds` has `mark`" in str(why.value)
    said = in_source(str(why.value), opened)
    assert f"line {line}" in said or f" {line}:" in said, said


# ── The substrate: the door in, the door out ────────────────────────────────


def _texts(view) -> list:
    return [i[3] for i in view.picture() if i[0] == "text"]


def test_the_rows_reach_the_program_and_a_press_asks_for_a_fact():
    """`document "mark"` is a signal of a set fed on a channel of typed
    rows; a press on a cell moves `acts`, and nothing else does."""
    from gestate.gui import Substrate

    game, _board = _copy()
    view = Substrate(notes.read(game), 22050)
    assert view.crossing is None, "a program with a document stays home"
    assert _texts(view) == ["X TO PLAY"]
    assert view.write("__doc_mark__", [(4, "X"), (0, "O")])
    assert _texts(view) == ["O", "X", "X TO PLAY"]
    assert view.acts() is None or view.acts() is None, "the feed's step is not a hand's"
    view.touch_all("press", CELL_X[1], CELL_Y[0])
    assert view.acts() == [("Assert", ("Mark", 1, [ord("X")]))]
    assert view.acts() is None, "consumed"
    view.touch_all("drag", CELL_X[2], CELL_Y[0])
    assert view.acts() is None, "a motion that wrote nothing asks nothing"


# ── The bench: the state is the file ────────────────────────────────────────


def _bench(game):
    from gestate.audioeditor import Workbench

    bench = Workbench(game, rate=22050, block=256)
    bench._load_substrate(bench.program())
    bench.drain()
    return bench


def _press(bench, cell: int) -> None:
    bench.touch("press", CELL_X[cell % 3], CELL_Y[cell // 3])
    bench.touch("release", CELL_X[cell % 3], CELL_Y[cell // 3])


def test_a_press_on_the_board_appears_in_the_file_and_a_taken_cell_is_refused():
    game, board = _copy()
    bench = _bench(game)
    assert bench.documents == [board]
    _press(bench, 0)
    assert "mark  cell 0  mark X" in board.read_text()
    assert _texts(bench.substrate) == ["X", "O TO PLAY"]
    assert bench.drain() == ["tic-tac-toe-facts.board — asserted mark  cell 0  mark X"]
    _press(bench, 0)
    assert bench.drain() == ["that cell is taken"]
    assert _strip(board.read_text()).count("mark  cell 0  mark X") == 1


def test_a_mark_typed_into_the_file_appears_on_the_board():
    game, board = _copy()
    bench = _bench(game)
    board.write_text("mark  cell 4  mark X\n" + board.read_text())
    bench.tick()
    assert _texts(bench.substrate) == ["X", "O TO PLAY"]


def test_a_win_stops_the_game_and_the_foot_clears_the_board():
    game, board = _copy()
    bench = _bench(game)
    for cell in (0, 4, 1, 8, 2):          # X takes the top row
        _press(bench, cell)
    assert _texts(bench.substrate)[-1] == "X WINS"
    _press(bench, 3)
    assert bench.drain()[-1].startswith("the game is over")
    assert len(_strip(board.read_text())) == 5 + 3, "five marks and the prose"
    bench.touch("press", *FOOT)
    said = bench.drain()
    assert len(said) == 5 and all(s.startswith("tic-tac-toe-facts.board — retracted") for s in said)
    assert not [l for l in _strip(board.read_text()) if l.startswith("mark")]
    assert _texts(bench.substrate) == ["X TO PLAY"]


def test_reopening_resumes_the_game_from_the_file():
    game, board = _copy()
    bench = _bench(game)
    _press(bench, 4)
    _press(bench, 0)
    again = _bench(game)
    assert _texts(again.substrate) == ["O", "X", "X TO PLAY"]
    _press(again, 8)
    assert "mark  cell 8  mark X" in board.read_text()
