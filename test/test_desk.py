"""Where the workbench was — `board/done/persistent-workbench-state.md`.

The `because` this is held against is Henri's: *"when the window is
closed the data is lost; it causes possible data loss, and leads to
forgetting where one was yesterday"*, and the postcondition written
before any of it was built:

> **Opening a piece puts you back where you were in it; opening the
> workbench with nothing puts you back in the piece you were last
> working on; and no window's closing takes another window's place
> away.**

Three clauses because there are three ways to lose a day, and each has
its own section below.  The last one is the hazard he named himself and
the one that needed a mechanism rather than a rule.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from gestate import desk as desks
from gestate.desk import Desk


@pytest.fixture(autouse=True)
def a_desk_of_ones_own(tmp_path, monkeypatch):
    """**Never the real one.**  These tests write a desk record, and the
    person running them has one of their own with their own work in it.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    return tmp_path


def a_piece(tmp_path, name: str = "sauna.ges") -> Path:
    path = tmp_path / name
    path.write_text("sound : Sig Float\nsound = sine 220.0 * 0.2\n")
    return path


# ── The document ────────────────────────────────────────────────────────────


def test_it_is_a_document_a_person_can_read(tmp_path):
    """*"As if that state was a document in itself."*  Which means it is
    legible, and that is a property worth asserting rather than hoping
    for: a format nobody can read is a dot-directory with extra steps."""
    text = Desk(line=41, column=8, zoom=4, seed=99, loop=(0, 8),
                knobs={"cutoff": 0.42}).text()
    assert "line 41" in text
    assert "seed 99" in text
    assert "knob cutoff 0.42" in text
    assert text.startswith("#"), "it says what it is"


def test_it_reads_back_what_it_wrote(tmp_path):
    was = Desk(line=41, column=8, zoom=4, showing="canvas", seed=99,
               loop=(0, 8), octave=6, knobs={"cutoff": 0.42, "q": 3.0})
    assert desks.parse(was.text()) == was


def test_a_document_it_does_not_understand_is_not_a_refusal(tmp_path):
    """**Forgiving on purpose.**  The worst a broken desk file may do is
    put you somewhere unhelpful; refusing to open a piece because the
    note about where you were is malformed would be the cure being worse
    than the disease."""
    got = desks.parse("line 12\nzoom banana\nfuture-thing 3\n\n# hello\n")
    assert (got.line, got.zoom) == (12, None)


def test_it_lives_beside_the_piece(tmp_path):
    """Because it is the *piece's* — it travels with it, commits with
    it, and can be handed to somebody else."""
    assert desks.beside(tmp_path / "sauna.ges").name == "sauna.desk"


def test_nothing_about_the_transport_or_the_build_is_written_down(tmp_path):
    """**A stronger guarantee than remembering not to apply them.**  A
    window that reopened playing would be a program making noise nobody
    asked for; there is nowhere in the document to say it was."""
    fields = set(Desk().__dataclass_fields__)
    assert not fields & {"playing", "position", "build", "graph", "engine"}


# ── Clause one: opening a piece puts you back where you were ────────────────


def test_where_you_were_survives_the_close(tmp_path):
    piece = a_piece(tmp_path)
    assert desks.write(piece, Desk(line=41, column=8, seed=99), was="")
    back = desks.read(piece)
    assert (back.line, back.column, back.seed) == (41, 8, 99)


def test_a_piece_nobody_has_opened_has_no_document(tmp_path):
    assert desks.read(a_piece(tmp_path)) is None


# ── Clause two: a bare launch reopens the piece you were last in ────────────


def test_the_last_piece_is_what_a_bare_launch_gets(tmp_path):
    piece = a_piece(tmp_path)
    desks.opened(piece)
    assert desks.last_file() == str(piece.resolve())


def test_somebody_who_has_never_opened_a_file_still_meets_the_starter(tmp_path):
    """**The first screen survives on exactly the person it is for.**
    `board/done/button.md` and `fixme.md` F150 are the account of how
    hard that screen was to get right, and a convenience feature must
    not take it from a stranger."""
    assert desks.last_file() is None


def test_a_piece_that_is_gone_is_not_offered(tmp_path):
    """An editor opening on a file that is not there is a worse answer
    than the starter."""
    piece = a_piece(tmp_path)
    desks.opened(piece)
    piece.unlink()
    assert desks.last_file() is None


# ── Clause three: no window's closing takes another's place away ────────────


def test_the_second_window_does_not_overwrite_the_first(tmp_path):
    """Henri's own hazard.  Last-writer-wins was available and rejected:
    you would find out it was the wrong rule *by losing yesterday's
    place*, which is the thing this card exists to prevent."""
    piece = a_piece(tmp_path)
    both_saw = desks.stamp(piece)                 # both opened here: ""
    assert desks.write(piece, Desk(line=10), was=both_saw), "the first writes"
    assert not desks.write(piece, Desk(line=400), was=both_saw), \
        "the second is refused"
    assert desks.read(piece).line == 10


def test_the_refused_window_keeps_its_place_somewhere(tmp_path):
    """**Which is what makes the refusal safe rather than lossy.**  Two
    views of a long piece is a real thing to have open, and each comes
    back where it was: the shared document holds one position and the
    desk record holds the rest."""
    piece = a_piece(tmp_path)
    desks.keep(piece, Desk(line=400, column=2), nth=1)
    assert desks.kept(piece, 1) == (400, 2)
    assert desks.kept(piece, 2) is None


def test_the_first_window_keeps_nothing_because_it_wrote(tmp_path):
    piece = a_piece(tmp_path)
    desks.keep(piece, Desk(line=400), nth=0)
    assert desks.kept(piece, 0) is None


def test_windows_are_counted_as_they_arrive(tmp_path):
    """`opened` answers *which* window this is, and that is what decides
    whose position it takes."""
    piece = a_piece(tmp_path)
    assert desks.opened(piece) == 0, "the first window on it"
    #: A second *process* would answer 1; this one is the same process,
    #: so its own row is replaced rather than counted twice.
    assert desks.opened(piece) == 0


def test_a_window_that_died_does_not_hold_a_place_forever(tmp_path):
    """**The record is best-effort by construction.**  Nothing
    supervises the set — three windows are three processes with no
    parent between them — so a crash leaves a row behind, and a row is
    believed only while the process that wrote it is there to mean it.
    """
    piece = a_piece(tmp_path)
    desks.opened(piece)
    where = desks.record_path()
    #: A pid that cannot be running: `opened` should read past it.
    where.write_text(where.read_text()
                     + f"open 999999999 {piece.resolve()}\n")
    assert desks.opened(piece) == 0
    assert "999999999" not in where.read_text(), "the dead row is gone"


def test_closing_takes_the_row_out(tmp_path):
    piece = a_piece(tmp_path)
    desks.opened(piece)
    desks.closed(piece)
    rows = desks.record_path().read_text()
    assert f"open {os.getpid()}" not in rows
    assert "last" in rows, "which piece you were in outlives the window"


# ── And the whole way round: a window, closed and opened again ─────────────
#
# **The postcondition, not the functions.**  Everything above is about
# the two documents; this is about a workbench being put back, which is
# the thing the card was written for and the only claim a person would
# recognise.


class _Bench:
    """As much workbench as a place needs — what `of` reads and what
    `restore` writes back to."""

    def __init__(self, text: str = "one\ntwo\nthree\nfour\n"):
        self._text = text
        self.seed = 7
        self.rate = 44100
        self.transport = None
        self.values = {"cutoff": 0.42}
        self.written: list = []

    def source(self) -> str:
        return self._text

    def set_value(self, name, value) -> None:
        self.values[name] = value
        self.written.append((name, value))


def _a_view(text: str = "one\ntwo\nthree\nfour\n"):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import a_window

    win, ed = a_window(text)
    win.note_state(zoom=2, rungs=9, undos=0, redos=0)
    return win, ed


def test_it_reads_the_place_off_a_living_workbench():
    """The itemising the card asked for, exercised rather than listed:
    every fact that survives a close is a line of `of`."""
    bench = _Bench()
    view, ed = _a_view()
    ed.pos = 8                                   # line 3, column 0
    view.showing = "canvas"
    where = desks.of(bench, view)
    assert (where.line, where.column) == (3, 0)
    assert (where.zoom, where.showing, where.seed) == (2, "canvas", 7)
    assert where.knobs == {"cutoff": 0.42}


def test_it_puts_the_window_back_by_asking_rather_than_reaching_in():
    """**The caret and the zoom are the window's own state**, and live
    on the window's thread — so this goes out as orders, in the
    direction the model already talks."""
    bench, (view, ed) = _Bench(), _a_view()
    put = desks.restore(Desk(line=3, column=2, zoom=4, showing="canvas",
                             knobs={"cutoff": 0.9}), bench, view)
    assert "goto\t3" in ed.orders
    assert "col\t2" in ed.orders
    assert "zoom\t2" in ed.orders, "stepped from where the mirror stands"
    assert "show\tcanvas" in ed.orders
    assert bench.values["cutoff"] == 0.9
    assert put, "it says what it did"


def test_a_close_and_an_open_put_you_back_where_you_were(tmp_path):
    """The first clause of the postcondition, end to end."""
    piece = a_piece(tmp_path)
    bench, (view, ed) = _Bench(), _a_view()
    ed.pos = 8
    bench.values["cutoff"] = 0.31

    # Closing.
    assert desks.write(piece, desks.of(bench, view), was=desks.stamp(piece))

    # And opening again, into a window that knows nothing.
    again, (view2, ed2) = _Bench(), _a_view()
    again.values = {}
    desks.restore(desks.read(piece), again, view2)
    assert "goto\t3" in ed2.orders
    assert again.values["cutoff"] == 0.31


def test_the_zoom_is_left_alone_when_the_document_says_nothing():
    bench, (view, ed) = _Bench(), _a_view()
    desks.restore(Desk(line=1), bench, view)
    assert not [o for o in ed.orders if o.startswith("zoom")]


# ── The launch itself ──────────────────────────────────────────────────────


def test_naming_a_file_always_means_that_file(tmp_path, monkeypatch):
    """*"the workbench `filename.ges` should land to that file"* — a
    document about yesterday does not get to argue with an argument."""
    from gestate import workbench

    piece, other = a_piece(tmp_path), a_piece(tmp_path, "other.ges")
    desks.opened(other)                            # `other` is the last one
    opened: list = []
    monkeypatch.setattr(workbench, "run",
                        lambda path, **kw: opened.append(path) or 0)
    workbench.main([str(piece)])
    assert opened == [str(piece)]


def test_a_bare_launch_reopens_the_piece_you_were_last_in(tmp_path, monkeypatch):
    from gestate import workbench

    piece = a_piece(tmp_path)
    desks.opened(piece)
    opened: list = []
    monkeypatch.setattr(workbench, "run",
                        lambda path, **kw: opened.append(path) or 0)
    workbench.main([])
    assert opened == [str(piece.resolve())]


def test_a_bare_launch_with_no_desk_asks_for_a_file(tmp_path):
    """Which is what leaves `tools/gestate-editor`'s `${1:-untitled.ges}`
    holding the starter for somebody who has never opened anything."""
    from gestate import workbench

    with pytest.raises(SystemExit):
        workbench.main([])


def test_the_seed_is_remembered_and_an_argument_still_wins(tmp_path, monkeypatch):
    """A seed is a *choice* — which take of a chancy piece you were
    listening to — so losing it loses the piece you had.  But `--seed`
    is somebody saying which take they want now."""
    from gestate import workbench

    piece = a_piece(tmp_path)
    desks.write(piece, Desk(seed=99), was="")
    seen: list = []
    monkeypatch.setattr(workbench, "Session", None)   # never reached

    def fake_run(path, **kw):
        seen.append(kw.get("seed"))
        return 0

    monkeypatch.setattr(workbench, "run", fake_run)
    workbench.main([str(piece)])
    workbench.main([str(piece), "--seed", "5"])
    assert seen == [None, 5], "main passes it through; `run` reads the desk"


def test_a_window_that_could_not_write_does_not_take_the_editor_down(tmp_path):
    """**A window that failed to write down where it was lost your
    place; a window that crashed on the way out because it could not
    lost your work.**  Those are not the same size of problem."""
    from gestate.workbench import _place, _remember

    class Broken:
        def __getattr__(self, name):
            raise RuntimeError("everything is on fire")

    assert _place(Broken()) is None
    _remember(tmp_path / "gone.ges", None, was="", nth=0)


def test_the_place_is_read_while_the_window_is_still_open(tmp_path):
    """**The caret is the editor's**, read across the ABI, so asking a
    closed one answers zero — which would file *you were at the top of
    the file* over wherever you actually were, every time.  So the
    reading and the writing are two functions, in that order."""
    from gestate.workbench import _place

    class Session:
        pass

    it = Session()
    it.bench, (it.view, ed) = _Bench(), _a_view()
    ed.pos = 8
    assert _place(it).line == 3


# ── The zoom belongs to the reader ───────────────────────────────────────
#
# **F165.**  Henri, on the fresh laptop install: *"The text was too small
# to read was my first reaction.  Zoom ladder worked."*  It worked, and
# then it stopped working — because the rung it fixed was written into
# `<piece>.desk`, so the next piece opened small again.
#
# Every other field of a `Desk` is a place in the piece.  This one
# describes the person's screen and the person's eyes, and it now lives
# where the module already says a person's own things live.


def test_a_piece_with_no_desk_opens_at_the_rung_you_read_at(tmp_path):
    """The whole of the defect, in one assertion: a piece nobody has
    ever opened should not be the size the developer's monitor liked.
    """
    desks.remember(3)
    got = desks.opening(a_piece(tmp_path))
    assert got is not None, "a stored rung is enough to open a desk"
    assert got.zoom == 3


def test_the_piece_wins_wherever_it_speaks(tmp_path):
    """**Not second-guessing the document.**  A `.desk` naming a rung
    was written by somebody looking at *that* piece — a dense score read
    close in, a sketch read far out — and the person's default is for
    the silence, not for overruling them.
    """
    path = a_piece(tmp_path)
    desks.write(path, Desk(line=4, zoom=7))
    desks.remember(3)
    got = desks.opening(path)
    assert got.zoom == 7
    assert got.line == 4, "and the rest of the document is untouched"


def test_saying_nothing_still_means_nothing(tmp_path):
    """A person who has never zoomed has no preference, and inventing
    one for them would be this fix overshooting into the thing it was
    meant to stop.
    """
    got = desks.opening(a_piece(tmp_path))
    assert got is None, "no desk and no rung is still nothing to restore"


def test_closing_writes_the_rung_down(tmp_path):
    """It is written on the way out, beside the piece's own document —
    and `gestate/workbench.py` writes it **before** the piece's, because
    a refusal to clobber is about where that piece was and says nothing
    about the size somebody reads at.
    """
    desks.remember(5)
    assert desks.mine() == 5
    assert desks.zoom_path().parent == desks.record_path().parent, (
        "it lives beside the desk record, outside any tree")


def test_a_rung_nobody_can_read_does_not_stop_a_window_opening(tmp_path):
    """Same manners the desk document keeps: *unknown names ignored*.
    A file a person edited by hand, or half-written by a crash, must
    cost them nothing worse than the default.
    """
    desks.zoom_path().parent.mkdir(parents=True, exist_ok=True)
    desks.zoom_path().write_text("banana\n")
    assert desks.mine() is None
    assert desks.opening(a_piece(tmp_path)) is None


def test_the_way_out_writes_the_rung_and_the_piece_separately(tmp_path):
    """The real `_remember`, not `desks.remember` — because the wiring
    is the half that can be wrong while every unit passes.

    **The rung is written even when the piece's document is refused.**
    A refusal to clobber means another window already said where *that
    piece* was; it says nothing about the size this person reads at, and
    losing the rung to somebody else's caret would be the same defect
    F165 is about, arriving from the other side.
    """
    from gestate.workbench import _remember

    piece = a_piece(tmp_path)
    # Another window got there first and wrote a different document, so
    # `was` no longer matches and the write is refused.
    desks.write(piece, Desk(line=99, zoom=8))
    _remember(piece, Desk(line=2, zoom=6), was="something else entirely",
              nth=1)

    assert desks.mine() == 6, "the reader's rung survived the refusal"
    assert desks.read(piece).line == 99, "and the other window kept its place"
