"""One window, two tabs — `spec/substrate.md` S4.

The same split `gui.py` makes and `audioeditor.py` makes: the half worth
testing has no toolkit in it.  `Document` is text and a cursor over
`balanced.py`'s rope, `Pane` is what a key *means*, and neither imports
pygame — so this file runs anywhere and the window is the only thing it
does not check.

The editor is modal, and it is worth saying why that is not a new tax.  The
`tkinter` one already is: its space bar plays or types a space depending on
where the focus happens to be, and its piano takes letter keys from
whatever had them.  A mode you cannot see is worse than one you choose.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.audioeditor import Workbench
from gestate.audiopygame import PLAIN, Document, Pane

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

SOURCE = """wiggle : Sig Float
wiggle = sine 3.0

sound : Sig Float
sound = sine 440.0 * (0.5 + wiggle * 0.25)
"""


def _pane(tmp_path, source: str = SOURCE, style: str = "") -> Pane:
    path = tmp_path / "s.ges"
    path.write_text(source)
    return Pane.open(Workbench(path, rate=8000, block=64), style=style)


# ── The document ────────────────────────────────────────────────────────────


def test_a_document_is_text_and_a_cursor():
    doc = Document("hello\nworld\n")
    assert doc.text == "hello\nworld\n"
    assert doc.rows == 3 and doc.line(1) == "world"
    doc.go_to(1, 3)
    assert (doc.row, doc.column) == (1, 3)


def test_editing_where_the_cursor_is():
    doc = Document("hello\nworld\n")
    doc.go_to(1, 3)
    doc.insert("XY")
    assert doc.line(1) == "worXYld"
    doc.backspace()
    doc.backspace()
    assert doc.line(1) == "world"


def test_a_vertical_move_keeps_the_column_it_set_out_from():
    """Through a short line and out the other side.

    A column that wandered would come back out of a long line in the wrong
    place, which is exactly where an editor feels wrong.
    """
    doc = Document("aaaaaaaaaa\nbb\ncccccccccc\n")
    doc.go_to(0, 8)
    doc.vertical(1)
    assert (doc.row, doc.column) == (1, 2), "clamped to the short line"
    doc.vertical(1)
    assert (doc.row, doc.column) == (2, 8), "and back out where it went in"


def test_an_edit_drops_the_mark_it_would_otherwise_outlive():
    """A click leaves the mark *at* the cursor.

    `Backspace` after one used to walk the cursor away from a mark that
    stayed put — so what you had just deleted came back highlighted, and
    once the mark was past the shortened text the next keystroke cut a
    range the rope does not have: `IndexError` out of `segments`, in the
    middle of typing.
    """
    doc = Document("hello world\n")
    doc.pos = doc.mark = doc.rope.length        # what a click leaves behind
    for _ in range(5):
        doc.backspace()
    assert doc.selection() is None, "nothing was ever selected to show"
    doc.insert("x")                             # this used to raise
    assert doc.text == "hello wx"


def test_a_selection_never_names_text_that_is_not_there():
    doc = Document("abc")
    doc.mark, doc.pos = 99, 0
    assert doc.selection() == (0, 3) and doc.selected() == "abc"


def test_home_and_end():
    doc = Document("hello\nworld\n")
    doc.go_to(1, 3)
    doc.home()
    assert doc.column == 0
    doc.end()
    assert doc.column == 5


# ── Modes ───────────────────────────────────────────────────────────────────


def test_escape_goes_outward_and_stops(tmp_path):
    """One key, one direction — which is what stops it being vi's `Esc`."""
    pane = _pane(tmp_path)
    assert pane.mode == "text"
    pane.escape()
    assert pane.mode == "command"
    pane.escape()
    assert pane.mode == "canvas"
    pane.escape()
    assert pane.mode == "canvas", "outermost, and it stays there"


def test_i_comes_back_to_text(tmp_path):
    pane = _pane(tmp_path)
    pane.escape()
    assert pane.command("i") == "mode: text"
    assert pane.mode == "text"


def test_plain_never_leaves_text(tmp_path):
    """One setting rather than a fork, for someone who wants no modes."""
    pane = _pane(tmp_path, style=PLAIN)
    assert "no modes" in pane.escape()
    assert pane.mode == "text"


def test_typing_inserts_in_text_and_commands_elsewhere(tmp_path):
    pane = _pane(tmp_path)
    pane.document.go_to(0, 0)
    pane.typed("x")
    assert pane.document.line(0).startswith("x")

    pane.escape()
    said = pane.typed("z")
    assert "does nothing" in said, "an unbound command says so"
    assert pane.document.line(0).startswith("x"), "and types nothing"


# ── The canvas tab ──────────────────────────────────────────────────────────


CANVAS = SOURCE + """
dragged : Chan Float
dragged = chan

level : Sig Float
level = 0.5 ::: mkSig (wait dragged)

handle : Float -> Sub
handle v = Shift 0 (floor (mix (0.0 - 60.0) 60.0 v)) (Rect 12 8 (RGB 200 200 200))

substrate : Sig Sub
substrate = moveXY 25 60 (onTouchY dragged
    (rect 12 120 (colour 40 40 40) `over` !handle level))
"""


def test_a_gesture_only_lands_on_the_canvas_tab(tmp_path):
    """The mode is what says whether a click is a click.

    On the text tab a press is the mouse doing something else entirely,
    and a fader that moved when you selected a word would be the same
    invisible-mode problem in a new place.
    """
    pane = _pane(tmp_path, CANVAS)
    pane.bench._load_substrate(CANVAS)

    assert pane.touch("press", 25, 30) == "", "text mode: nothing"
    assert pane.bench.substrate.values == {}

    pane.escape()
    pane.escape()
    assert pane.mode == "canvas"
    pane.touch("press", 25, 30)
    # The fader spans y 0…120, so a press at 30 is a quarter down it.
    assert pane.bench.substrate.values == {"dragged": 0.25}


def test_the_canvas_shows_what_the_program_draws(tmp_path):
    pane = _pane(tmp_path, CANVAS)
    pane.bench._load_substrate(CANVAS)
    assert ("rect", 19, 56, 12, 8, (200, 200, 200)) in pane.picture()


def test_a_file_with_no_canvas_shows_nothing(tmp_path):
    pane = _pane(tmp_path)
    pane.bench._load_substrate(SOURCE)
    assert pane.picture() == []


# ── Knobs, drawn rather than placed ─────────────────────────────────────────


def test_knobs_come_back_as_a_line_a_name_and_a_value(tmp_path):
    """The `tkinter` view hangs a widget beside a line and asks the text
    widget where that line ended up.  Here the view owns the layout, so a
    knob is three things and where it goes is the walk that drew the line.
    """
    source = ("cutoff : Sig Float\ncutoff = mkKnob 0.6\n"
              "\nsound : Sig Float\n"
              "sound = zip (x c => x * c) (sine 440.0) cutoff\n")
    pane = _pane(tmp_path, source)
    pane.bench._place(source)

    knobs = pane.knobs()
    assert [(name, value, wired) for _line, name, value, wired in knobs] \
        == [("cutoff", 0.5, True)]
    # Beside the *definition* — the line that is the knob, which is where
    # `audiospans` places one and what the person turning it is looking at.
    line = knobs[0][0]
    assert source.splitlines()[line - 1] == "cutoff = mkKnob 0.6"


def test_a_knob_appears_when_it_is_declared_rather_than_when_it_is_wired(
        tmp_path):
    """The sites come out of the extracted graph, and a graph only holds
    what `sound` reaches — so a knob nothing uses yet was invisible until it
    was no longer news.  Read off the text instead, and said to be idle.
    """
    source = ("cutoff : Sig Float\ncutoff = mkKnob 0.6\n"
              "\nspare : Sig Float\nspare = mkKnob 5\n"
              "\nsound : Sig Float\n"
              "sound = zip (x c => x * c) (sine 440.0) cutoff\n")
    pane = _pane(tmp_path, source)
    pane.bench._place(source)

    assert pane.knobs() == [(2, "cutoff", 0.5, True), (5, "spare", "5", False)]
    assert (5, "knob", "spare = 5  (not wired)") in pane.inspect()


def test_a_declared_knob_is_read_from_a_program_that_will_not_compile(
        tmp_path):
    """Which is the state a half-written declaration is usually in, and the
    reason this is a regular expression rather than a front end."""
    pane = _pane(tmp_path, "k = mkKnob 5\nsound = ((((\n")
    assert pane.declared() == [(1, "k", "5")]


# ── Getting back, and getting around ────────────────────────────────────────


def test_return_goes_inward(tmp_path):
    """The way *back*, and the mirror of `Esc`.

    `Esc` stops at the outermost mode by design, so without this the canvas
    is a room with a door in one wall.
    """
    pane = _pane(tmp_path)
    pane.escape()
    pane.escape()
    assert pane.mode == "canvas"
    assert pane.inward() == "mode: command"
    assert pane.inward() == "mode: text"
    assert pane.inward() == "mode: text", "innermost, and it stays there"


def test_a_page_is_as_tall_as_the_window_says(tmp_path):
    """`Page Up`/`Page Down` move by what is on screen.

    The pane cannot know that and the view can, so the view sets it — the
    same division as everywhere else here.
    """
    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    pane.page = 30
    pane.document.go_to(0, 0)
    pane.document.vertical(pane.page)
    assert pane.document.row == 30
    pane.document.vertical(-pane.page)
    assert pane.document.row == 0


def test_the_status_ink_is_readable_on_every_mode(tmp_path):
    """The status line sits *in* the border, so the ink follows the mode.

    A long line used to run over the one thing that says where you are;
    now it is clipped and the border carries it.
    """
    from gestate.audiopygame import _EDGE, _legible_on

    for mode, edge in _EDGE.items():
        ink = _legible_on(edge)
        contrast = abs(sum(ink) - sum(edge))
        assert contrast > 200, f"{mode}: {ink} on {edge}"


# ── The chrome ──────────────────────────────────────────────────────────────
#
# A toolbar in every mode, a status line in the border, and both of them
# built from the window the view actually has — which is what makes it
# resizable: nothing here remembers a size.


def _layout(width=900, height=560, line_h=20, advance=9, sidebar=0):
    from gestate.audiopygame import Layout

    return Layout(width, height, line_h, advance, sidebar=sidebar)


def test_the_window_is_divided_by_the_size_it_has_now():
    small, large = _layout(400, 300), _layout(1200, 900)
    for layout in (small, large):
        toolbar, inner, status = layout.toolbar, layout.inner, layout.status
        assert toolbar[1] == 0
        assert inner[1] == toolbar[3], "the view starts under the toolbar"
        assert inner[1] + inner[3] <= status[1], "and stops above the status"
        assert status[1] + status[3] == layout.height
    assert large.inner[2] > small.inner[2], "resizing is just a new layout"


def test_every_button_is_inside_the_chrome():
    layout = _layout()
    for name, rect in layout.buttons.items():
        band = layout.status if name in ("bigger", "smaller") else layout.toolbar
        assert band[1] <= rect[1] and rect[1] + rect[3] <= band[1] + band[3], name


def test_a_click_finds_the_button_under_it(tmp_path):
    pane = _pane(tmp_path)
    layout = _layout()
    x, y, _w, _h = layout.buttons["piano"]
    assert pane.click(x + 1, y + 1, layout) == "mode: piano (play)"


def test_the_toolbar_works_in_every_mode(tmp_path):
    """A toolbar that came and went with the mode would be one more thing
    to learn."""
    pane = _pane(tmp_path)
    layout = _layout()
    x, y, _w, _h = layout.buttons["to_start"]

    class _T:
        playing = False
        at = None

        def seek(self, sample):
            self.at = sample

    pane.bench.transport = _T()
    for mode in ("text", "command", "canvas"):
        pane.mode = mode
        assert pane.click(x + 1, y + 1, layout) == "at the start"


def test_clicking_the_text_places_the_cursor(tmp_path):
    pane = _pane(tmp_path)
    layout = _layout()
    layout.top = 0
    ix, iy, _w, _h = layout.inner
    # Row 1, which has text on it: `go_to` clamps to the line, and row 2
    # of this source is blank.
    pane.click(ix + layout.margin + 3 * layout.advance,
               iy + 1 * layout.line_h, layout)
    assert (pane.document.row, pane.document.column) == (1, 3)


# ── Size ────────────────────────────────────────────────────────────────────


def test_the_text_can_be_resized_and_stops(tmp_path):
    pane = _pane(tmp_path)
    assert pane.bigger() == f"size {pane.size}"
    for _ in range(60):
        pane.bigger()
    assert pane.size == 40
    for _ in range(60):
        pane.smaller()
    assert pane.size == 8


# ── The piano ───────────────────────────────────────────────────────────────


def test_p_plays_and_shift_p_writes(tmp_path):
    """`Keyboard.press_key` returns the note whether or not a bank took it,
    which its own docstring says is for exactly this."""
    pane = _pane(tmp_path)
    pane.escape()                                   # command
    assert pane.command("p") == "mode: piano (play)"
    before = pane.document.text
    assert pane.piano_key("z", "z") == "note 60", "the tracker layout's C"
    assert pane.document.text == before, "play mode writes nothing"
    pane.piano_release("z", "z")

    assert pane.command("P") == "mode: piano (step)"
    pane.document.go_to(0, 0)
    pane.piano_key("z", "z")
    assert pane.document.line(0).startswith("60 "), "step writes what it played"


def test_the_piano_is_left_by_either_direction(tmp_path):
    pane = _pane(tmp_path)
    pane.open_piano()
    assert pane.enter_command() == "mode: command"
    assert pane.piano == "", "and stops being a piano"


def test_a_key_that_plays_nothing_writes_nothing(tmp_path):
    pane = _pane(tmp_path)
    pane.open_piano(step=True)
    before = pane.document.text
    assert pane.piano_key("£", "£") == ""
    assert pane.document.text == before


# ── Selecting, and the clipboard ────────────────────────────────────────────


def test_a_selection_is_the_span_between_the_mark_and_the_cursor():
    """One number, so dragging backwards needs no special case."""
    doc = Document("alpha\nbeta\ngamma\n")
    doc.go_to(1, 4)
    doc.mark = doc.pos
    doc.go_to(1, 0)
    assert doc.selected() == "beta", "backwards reads the same"


def test_typing_over_a_selection_replaces_it():
    doc = Document("alpha\nbeta\n")
    doc.go_to(0, 0)
    doc.mark = doc.pos
    doc.go_to(0, 5)
    doc.insert("X")
    assert doc.text == "X\nbeta\n"


def test_backspace_over_a_selection_takes_the_selection():
    doc = Document("alpha\nbeta\n")
    doc.go_to(0, 0)
    doc.mark = doc.pos
    doc.go_to(0, 5)
    doc.backspace()
    assert doc.text == "\nbeta\n", "and not one character more"


def test_copy_and_paste(tmp_path):
    """`Ctrl-C` and `Ctrl-V`, through the pane's own buffer.

    The system clipboard is a bonus rather than a dependency: `scrap` needs
    a display and is not on every platform, and copy and paste have to work
    regardless.
    """
    pane = _pane(tmp_path)
    doc = pane.document
    doc.go_to(0, 0)
    doc.mark = doc.pos
    doc.go_to(0, 6)
    assert pane.copy() == "copied 6"
    assert pane.clipboard == "wiggle"

    doc.drop_mark()
    doc.end()
    pane.paste()
    assert doc.line(0) == "wiggle : Sig Floatwiggle"


def test_cut_removes_and_remembers(tmp_path):
    pane = _pane(tmp_path)
    doc = pane.document
    doc.go_to(0, 0)
    doc.mark = doc.pos
    doc.go_to(0, 6)
    assert pane.cut() == "cut 6"
    assert pane.clipboard == "wiggle"
    assert doc.line(0) == " : Sig Float"


def test_dragging_selects(tmp_path):
    pane = _pane(tmp_path)
    layout = _layout()
    layout.top = 0
    ix, iy, _w, _h = layout.inner
    pane.click(ix + layout.margin, iy, layout)
    pane.drag_to(ix + layout.margin + 6 * layout.advance, iy, layout)
    assert pane.document.selected() == "wiggle"


# ── Command mode moves too ──────────────────────────────────────────────────


def test_command_mode_has_the_cursor_keys_and_hjkl(tmp_path):
    """`hjkl` *beside* the arrows, not instead of them.

    In text mode `h` is an `h`, and an editor that took it away would be
    the thing people mean when they complain about modes.
    """
    pane = _pane(tmp_path)
    pane.escape()
    pane.document.go_to(0, 0)
    pane.command("l")
    pane.command("l")
    assert pane.document.column == 2
    pane.command("j")
    assert pane.document.row == 1
    pane.command("k")
    assert pane.document.row == 0
    pane.command("h")
    assert pane.document.column == 1

    pane.mode = "text"
    pane.typed("h")
    assert pane.document.line(0).startswith("wh"), "a letter is a letter"


# ── The transport ───────────────────────────────────────────────────────────


def test_the_transport_button_is_the_state_not_the_command(tmp_path):
    """What it shows is what pressing it does next."""
    pane = _pane(tmp_path)

    class _T:
        playing = False

        def seek(self, sample):
            self.at = sample

    pane.bench.transport = _T()
    seen = []
    pane.bench.toggle = lambda: seen.append("toggled")
    pane.button("transport")
    assert seen == ["toggled"]


def test_the_end_is_the_pieces_and_there_may_be_none(tmp_path):
    """A file with no `score` has nothing that could be called an end.

    A button that jumped somewhere arbitrary would be worse than one
    plainly unavailable, so the view greys it and this says why.
    """
    from gestate.audioschedule import Schedule

    pane = _pane(tmp_path)
    assert pane.end_sample() is None
    assert "no piece" in pane.to_end()

    pane.bench.schedule = Schedule().change(4096, "g0", 1)
    assert pane.end_sample() == 4097


def test_the_angle_brackets_seek(tmp_path):
    pane = _pane(tmp_path)

    class _T:
        playing = False
        at = None

        def seek(self, sample):
            self.at = sample

    pane.bench.transport = _T()
    pane.escape()
    assert pane.command("<") == "at the start"
    assert pane.bench.transport.at == 0


def test_return_from_the_piano_lands_in_text(tmp_path):
    """What a piano is next to is the thing you were writing."""
    pane = _pane(tmp_path)
    pane.open_piano(step=True)
    assert pane.enter_text() == "mode: text"
    assert pane.piano == ""


# ── Scrolling, saving, undoing ──────────────────────────────────────────────


def test_a_click_reads_the_scroll_the_last_draw_used(tmp_path):
    """The bug a drag showed: the cursor did not follow the mouse.

    A `Layout` is rebuilt every frame, so a scroll position kept on one was
    zero again before the next click could read it.  It lives on the pane,
    which is the thing that persists.
    """
    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    pane.top = 40
    layout = _layout()
    layout.top = pane.top
    ix, iy, _w, _h = layout.inner
    pane.click(ix + layout.margin + 2 * layout.advance,
               iy + 3 * layout.line_h, layout)
    assert pane.document.row == 43, "the row under the pointer, not near the top"


def test_the_transport_button_reads_the_transport(tmp_path):
    """`Workbench.playing` is "the thread is alive", which never changes
    while the window is open — so a button reading it never moved."""
    pane = _pane(tmp_path)

    class _T:
        playing = False
        position = 0

    pane.bench.transport = _T()
    assert pane.is_playing() is False
    _T.playing = True
    assert pane.is_playing() is True


def test_the_position_reads_as_a_clock(tmp_path):
    pane = _pane(tmp_path)

    class _T:
        playing = True
        position = 8000 * 75

    pane.bench.transport = _T()
    assert pane.position() == "1:15.00"


def test_ctrl_s_writes_the_file_even_with_nothing_playing(tmp_path):
    """Two promises, and only one of them needs a synth.

    `Workbench.apply` refuses when nothing is playing, and a synth that
    failed to start is exactly when you most want your text on disk.
    """
    pane = _pane(tmp_path)
    pane.document.go_to(0, 0)
    pane.typed("x")
    said = pane.apply()
    assert "saved" in said
    assert pane.bench.path.read_text().startswith("x")
    assert not pane.dirty


def test_the_caption_says_when_the_text_differs(tmp_path):
    pane = _pane(tmp_path)
    assert "[+]" not in pane.caption()
    pane.typed("x")
    assert pane.caption().endswith("[+]")
    pane.save()
    assert "[+]" not in pane.caption()


def test_undo_goes_back_one_edit_at_a_time(tmp_path):
    """Free, because the rope is persistent: an old one costs nothing."""
    pane = _pane(tmp_path)
    pane.document.go_to(0, 0)
    pane.typed("a")
    pane.typed("b")
    assert pane.document.line(0).startswith("ab")
    assert pane.undo() == "undone"
    assert pane.document.line(0).startswith("a")
    pane.undo()
    assert pane.document.line(0).startswith("wiggle")
    assert pane.undo() == "nothing to undo"


# ── The sidebar ─────────────────────────────────────────────────────────────


def test_the_sidebar_has_a_place_of_its_own(tmp_path):
    """A mode's furniture rather than a panel you toggle."""
    from gestate.audiopygame import Layout

    wide = Layout(900, 560, 20, 9, sidebar=300)
    assert wide.aside[2] == 300
    assert wide.inner[0] + wide.inner[2] <= wide.aside[0]
    assert Layout(900, 560, 20, 9).aside[2] == 0


def test_the_sidebar_shows_a_knob_beside_its_line(tmp_path):
    source = ("cutoff : Sig Float\ncutoff = mkKnob 0.6\n"
              "\nsound : Sig Float\n"
              "sound = zip (x c => x * c) (sine 440.0) cutoff\n")
    pane = _pane(tmp_path, source)
    pane.bench._place(source)
    assert pane.inspect() == [(2, "knob", "cutoff = 0.5")]

def test_the_sidebar_says_what_a_hole_would_have_to_be(tmp_path):
    """The same walk `typecheck --holes` does, in the window."""
    source = ("wobble : Float\nwobble = _\n"
              "\nsound : Sig Float\nsound = map (n => wobble) ticks\n")
    pane = _pane(tmp_path, source)
    assert (2, "hole", "_ : Float") in pane.inspect()


def test_the_sidebar_keeps_the_last_complaint_beside_its_line(tmp_path):
    """The row is one line of it, beside the line it names.  The rest is
    interleaved into the text — see `laid_out`."""
    pane = _pane(tmp_path)
    pane.bench._first_line(Exception("something wrong (at s.ges:4:1)"))
    assert (4, "error", "something wrong (at s.ges:4:1)") in pane.inspect()


def test_a_message_that_is_not_a_complaint_is_not_kept(tmp_path):
    """**Enforced at the source now, not by matching words.**  A complaint
    is whatever passed through `Workbench._first_line`, which is the one
    place an *exception* is turned into a sentence; `"playing knob.ges"` is
    said directly and never goes near it.  The old rule looked for the
    words "error", "not applied" and "could not" in the finished string,
    which would have kept a synth whose author had named something
    `error`."""
    pane = _pane(tmp_path)
    pane.bench.say("playing knob.ges at 48000 Hz")
    assert pane.bench.trouble == ""
    assert pane.inspect() == []


def test_the_sidebar_never_stalls_a_frame(tmp_path):
    """It is a whole front end, and a draw is sixteen milliseconds.

    The first look hands back what it knows — nothing — and says it is
    still reading; the answer arrives on a worker.  Without that the
    keyboard goes on repeating into the queue while the frame is stuck,
    and the events all land at once when it ends.
    """
    import time

    source = ("wobble : Float\nwobble = _\n"
              "\nsound : Sig Float\nsound = map (n => wobble) ticks\n")
    pane = _pane(tmp_path, source)

    started = time.monotonic()
    known, thinking = pane.facts()
    assert time.monotonic() - started < 0.05, "the frame waited for it"
    assert known == [] and thinking is True

    deadline = time.monotonic() + 30
    while pane.facts()[1] and time.monotonic() < deadline:
        time.sleep(0.02)
    assert pane.facts() == ([(2, "hole", "_ : Float")], False)


def test_the_view_follows_the_cursor_only_as_far_as_it_must(tmp_path):
    """Centring scrolls on every move; under a drag that reads as tearing.

    The view stays still until the cursor comes within a couple of lines of
    an edge, and then follows by a line.
    """
    pygame = pytest.importorskip("pygame")

    from gestate.audiopygame import _text

    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    pygame.init()
    screen = pygame.display.set_mode((640, 400))
    font = pygame.font.SysFont("monospace", pane.size)
    layout = _layout(640, 400, font.get_linesize(), 9)
    rows = layout.inner[3] // layout.line_h

    pane.document.go_to(rows // 2, 0)
    _text(screen, pygame, font, layout, pane, (0, 0, 0), (0, 0, 0))
    assert pane.top == 0, "a cursor in view does not move the view"

    pane.document.go_to(rows + 5, 0)
    _text(screen, pygame, font, layout, pane, (0, 0, 0), (0, 0, 0))
    assert 0 < pane.top <= 8, f"followed a little, not to the middle: {pane.top}"
    pygame.quit()


def test_a_drag_past_the_bottom_stops_just_past_the_last_visible_line(
        tmp_path):
    """So it scrolls by a couple of lines rather than jumping to wherever
    the pointer would have been had the document been drawn that far.

    `_REACH` is how far past the last drawn line the cursor may be carried,
    and with the view following it that is the scroll *speed* — a nudge
    beyond the edge rather than the leap this replaced.
    """
    from gestate.audiopygame import _REACH

    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    layout = _layout(640, 400, 20, 9)
    layout.top = pane.top = 0
    rows = layout.inner[3] // layout.line_h

    ix, iy, _w, _h = layout.inner
    pane.click(ix + layout.margin, iy, layout)
    pane.drag_to(ix + layout.margin, iy + 10_000, layout)
    assert pane.document.row == rows - 1 + _REACH

    pane.top = layout.top = 50
    pane.drag_to(ix + layout.margin, iy - 10_000, layout)
    assert pane.document.row == 50 - _REACH, "and the same off the top"


def test_a_held_escape_does_not_walk_through_the_modes(tmp_path):
    """By what is *held*, not by the clock.

    A time-based guess fails the moment a frame is slow: the repeats queue
    up, arrive together long after the press, and the first of them looks
    new — which is how holding `Esc` through the sidebar's front end walked
    past command mode and landed on the canvas.  A key is not new until it
    has been released.
    """
    from gestate.audiopygame import _fresh

    pane = _pane(tmp_path)
    assert _fresh(pane, "escape") is True
    assert _fresh(pane, "escape") is False, "still held: a repeat"
    assert _fresh(pane, "escape") is False, "however long it is held"
    pane.held_keys.discard("escape")            # what `KEYUP` does
    assert _fresh(pane, "escape") is True, "released, so a new press"


def test_shift_and_a_movement_selects(tmp_path):
    """The rule everywhere else, so it is one rule here.

    `HJKL` is `hjkl` with the mark left where it was, and the arrows do the
    same through `travel` — one place, because a selection that behaved
    differently under each would be two rules for one idea.
    """
    pane = _pane(tmp_path)
    pane.escape()
    pane.document.go_to(0, 0)
    for _ in range(6):
        pane.command("L")
    assert pane.document.selected() == "wiggle"

    pane.command("h")
    assert pane.document.selection() is None, "moving away drops it"


def test_the_wheel_moves_the_page_and_takes_the_cursor_with_it(tmp_path):
    """There is one scroll position here and the cursor decides it.

    `_text` derives `top` from the cursor every frame, which is what makes
    a click and the last draw agree about which line the pointer is on — so
    a view scrolled away from the cursor would be overruled by the next
    frame, and the page would twitch back under the hand that moved it.
    """
    from gestate.audiopygame import _WHEEL

    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    pane.document.go_to(20, 0)
    pane.top = 18

    pane.wheel(1)
    assert (pane.top, pane.document.row) == (18 + _WHEEL, 20 + _WHEEL), \
        "both, by the same lines: the cursor keeps its row of the window"
    pane.wheel(-1)
    assert (pane.top, pane.document.row) == (18, 20)

    pane.wheel(-50)
    assert (pane.top, pane.document.row) == (0, 0), "and it stops at the top"


def test_the_wheel_is_the_program_s_own_on_the_canvas(tmp_path):
    """Which has no lines to scroll: what a wheel means there is the
    program's question, and `spec/substrate.md` leaves that vocabulary to
    the programs that ask for it."""
    pane = _pane(tmp_path, "\n".join(f"line {i}" for i in range(200)))
    pane.mode, pane.top = "canvas", 10
    pane.wheel(1)
    assert (pane.top, pane.document.row) == (10, 0)


# ── Opening on a file that will not compile ─────────────────────────────────


def test_nothing_playing_leaves_every_answer_a_shrug_rather_than_a_crash(
        tmp_path):
    """The editor opens on a file that will not compile, which leaves it
    with no instrument — and everything the chrome asks has to answer."""
    pane = _pane(tmp_path, "sound = sine 440.0 +\n")   # never started
    assert pane.knobs() == [] and pane.banks() == []
    assert pane.is_playing() is False and pane.position() == "--:--"
    assert pane.picture() == [] and pane.end_sample() is None
    assert pane.toggle() == "stopped"
    assert pane.to_start() == "" and "no piece" in pane.to_end()


# ── A file that does not exist yet ──────────────────────────────────────────


def test_a_name_that_is_not_there_opens_a_new_synth(tmp_path):
    """`gestate.audiopygame a.ges` on a missing name used to be a
    `FileNotFoundError` traceback out of `Pane.open`.  Naming a file that
    does not exist is how every editor is asked to start a new one."""
    from gestate.audioeditor import STARTER, is_new

    path = tmp_path / "a.ges"
    assert is_new(path)
    pane = Pane.open(Workbench(path, rate=8000, block=64))
    assert pane.document.text == STARTER


def test_nothing_is_written_until_the_first_save(tmp_path):
    """Every other editor waits for `Ctrl-S`, so a name typed by mistake
    leaves nothing behind."""
    path = tmp_path / "typo.ges"
    pane = Pane.open(Workbench(path, rate=8000, block=64))
    assert not path.exists(), "opening it wrote it"
    assert pane.bench.source(), "the engine still has a program to compile"

    pane.save()
    assert path.exists()
    assert path.read_text() == pane.document.text
    assert pane.bench.pending == "", "it is the file's now, not the buffer's"


def test_the_first_save_makes_the_directory_too(tmp_path):
    """`audiopygame sketches/a.ges` should work before `sketches` does."""
    path = tmp_path / "sketches" / "a.ges"
    pane = Pane.open(Workbench(path, rate=8000, block=64))
    assert not path.parent.exists()
    pane.save()
    assert path.exists()


def test_the_starter_is_a_synth_that_plays(tmp_path):
    """Not an empty file: an empty one has no `sound`, so the editor would
    open on a compile error, which is a poor first second in a tool whose
    point is that the program is running while you type."""
    from gestate.audio import render
    from gestate.audioeditor import STARTER

    xs = render(STARTER, 0.05, 8000)
    assert max(abs(x) for x in xs) > 0.1


def test_ctrl_s_starts_the_instrument_that_never_started(tmp_path):
    """Without it the only way back to sound would be to close the window
    you have just fixed the program in."""
    pane = _pane(tmp_path)
    started = []
    pane.bench.start = lambda: started.append(True)

    assert pane.apply(save=False) == "nothing is playing — Ctrl-S starts it"
    assert started == [], "an audition cannot: starting reads the *file*"
    assert pane.apply() == "saved and started"
    assert started == [True]


def test_the_instrument_starts_behind_the_window(tmp_path):
    """Because starting one is a front end, an extraction and a `clang`.

    Four seconds for a synth and nearly thirty for `quartet.ges`, and it
    used to happen before there was anything on the screen — which from the
    outside is not a slow editor but one that does not open.
    """
    import threading
    import time

    from gestate.audiopygame import _starting

    pane = _pane(tmp_path)
    gate = threading.Event()
    pane.bench.start = lambda: gate.wait(10)

    began = time.monotonic()
    _starting(pane, pane.bench, pane.bench.path)
    assert time.monotonic() - began < 0.05, "the window waited for it"
    assert pane.starting is True

    gate.set()
    deadline = time.monotonic() + 10
    while pane.starting and time.monotonic() < deadline:
        time.sleep(0.01)
    assert pane.starting is False


def test_a_start_that_fails_behind_the_window_reaches_the_status_line(tmp_path):
    """Through `Workbench.messages`, which is the queue the loop already
    drains into the status line and the sidebar."""
    import time

    from gestate.audiopygame import _starting

    pane = _pane(tmp_path)

    def broken():
        raise RuntimeError("type error: at line 4")

    pane.bench.start = broken
    _starting(pane, pane.bench, pane.bench.path)
    deadline = time.monotonic() + 10
    while pane.starting and time.monotonic() < deadline:
        time.sleep(0.01)
    assert any(m.startswith("could not start:") for m in pane.bench.messages)


def test_ctrl_s_does_not_start_a_second_instrument_over_the_first(tmp_path):
    pane = _pane(tmp_path)
    started = []
    pane.bench.start = lambda: started.append(True)
    pane.starting = True

    assert pane.apply() == "saved; still starting"
    assert started == [], "two instruments racing for one sound card"
    assert pane.dirty is False, "and the file was written either way"


def test_a_start_that_fails_again_is_said_rather_than_raised(tmp_path):
    pane = _pane(tmp_path)

    def broken():
        raise RuntimeError("type error: at line 4\nand three more lines")

    pane.bench.start = broken
    said = pane.apply()
    assert said.startswith("saved; could not start: type error: at line 4")
    assert "\n" not in said, "a status bar is a line"


# ── Banks, and the switch that is also a fact ───────────────────────────────


def _banked(tmp_path):
    from gestate.audioeditor import Workbench

    source = (AUDIO_DIR / "polysine.ges").read_text()
    path = tmp_path / "polysine.ges"
    path.write_text(source)
    bench = Workbench(path, rate=8000, block=64)
    bench._find_banks(source)
    bench._load_from_midi(source)
    bench._start_notes()
    return Pane.open(bench), source


def test_a_bank_shows_what_it_is_playing(tmp_path):
    """What the `tkinter` view put in a row beside each declaration."""
    pane, source = _banked(tmp_path)
    (line, name, held, takes, listening), = pane.banks()
    assert source.splitlines()[line - 1].startswith("voices lead")
    assert (name, held, takes) == ("lead", "0/4", True)


def test_the_midi_switch_hands_the_bank_over_and_back(tmp_path):
    pane, _source = _banked(tmp_path)
    assert pane.banks()[0][4] is True or pane.toggle_midi("lead")
    was = pane.banks()[0][4]
    pane.toggle_midi("lead")
    assert pane.banks()[0][4] is not was


def test_a_bank_with_no_from_midi_says_so_rather_than_switching(tmp_path):
    """A switch you can throw that cannot do anything is worse than one
    you cannot."""
    pane = _pane(tmp_path)
    pane.bench.banks = [{"name": "lead", "count": 2, "line": 1}]
    assert "no `FromMIDI`" in pane.toggle_midi("lead")


def test_a_click_in_the_sidebar_throws_the_switch(tmp_path):
    pane, _source = _banked(tmp_path)
    layout = _layout(sidebar=300)
    pane.mode = "command"
    pane.rows = {1: (46, "bank", "lead 0/4  [ ] midi")}
    said = pane.click(layout.aside[0] + 5,
                      layout.aside[1] + 2 + layout.line_h, layout)
    assert said.startswith("lead:")


def test_the_row_a_click_finds_is_the_row_that_was_drawn(tmp_path):
    """Which is a test the pair of them can only pass together.

    `_aside` recorded an *absolute* y over the line height and
    `click_aside` asked for the row within the panel, so the two agreed
    only when the toolbar happened to be zero lines tall — and the switch
    was unclickable, silently: a lookup that misses and a row that is not a
    bank both do nothing at all.
    """
    pygame = pytest.importorskip("pygame")

    from gestate.audiopygame import Layout, _aside

    pane, _source = _banked(tmp_path)
    pane.mode = "command"
    pygame.init()
    screen = pygame.display.set_mode((900, 560))
    font = pygame.font.SysFont("monospace", pane.size)
    layout = Layout(900, 560, font.get_linesize(),
                    max(1, font.size("m")[0]), sidebar=300)

    _aside(screen, pygame, font, layout, pane, (0, 0, 0))
    row = next(i for i, r in pane.rows.items() if r[1] == "bank")
    was = pane.banks()[0][4]
    said = pane.click(layout.aside[0] + 5,
                      layout.aside[1] + 2 + row * layout.line_h + 1, layout)
    pygame.quit()
    assert said.startswith("lead:")
    assert pane.banks()[0][4] is not was, "the switch actually moved"


def test_a_bank_row_is_read_fresh_rather_than_cached_on_the_text(tmp_path):
    """It is about the instrument, not about the program.

    The sidebar's answers are cached on the text, which is right for the
    ones a front end computes and wrong for these: nothing is typed while a
    piece plays, so `lead 0/4` sat there through the whole of it.
    """
    pane, _source = _banked(tmp_path)
    assert any("lead 0/4" in text for _l, kind, text in pane.facts()[0]
               if kind == "bank")

    pane.bench.banks[0]["count"] = 9          # what a sounding voice moves
    assert any("lead 0/9" in text for _l, kind, text in pane.facts()[0]
               if kind == "bank"), "the row is still the one from before"


# ── `?` ─────────────────────────────────────────────────────────────────────


def test_the_word_under_the_cursor(tmp_path):
    pane = _pane(tmp_path)
    pane.document.go_to(0, 2)
    assert pane.word() == "wiggle"
    pane.document.go_to(2, 0)
    assert pane.word() == "", "a blank line has no word"


def test_question_mark_asks_what_it_is(tmp_path):
    """The same two answers `typecheck --query` gives: the type from
    inference, and the prose above the declaration that carries it."""
    source = ("#: How loud, and for how long.\n"
              "level : Float\nlevel = 0.5\n"
              "\nsound : Sig Float\nsound = map (n => level) ticks\n")
    pane = _pane(tmp_path, source)
    pane.escape()
    pane.document.go_to(1, 1)
    assert pane.command("?") == "? level"

    answer = pane.answer()
    assert answer[0] == ("query", "level : Float")
    assert any("declaration" in text for _kind, text in answer)
    assert any("How loud" in text for _kind, text in answer)


def test_the_answer_opens_over_the_text_and_any_key_takes_it_away(tmp_path):
    """It is about the word you are looking at rather than the program, so
    nothing here is worth a corner of the window permanently."""
    import time

    source = ("#: How loud.\nlevel : Float\nlevel = 0.5\n"
              "\nsound : Sig Float\nsound = map (n => level) ticks\n")
    pane = _pane(tmp_path, source)
    pane.escape()
    pane.document.go_to(1, 1)

    started = time.monotonic()
    pane.command("?")
    assert time.monotonic() - started < 0.05, "the frame waited for it"
    assert pane.dialog[-1][1].strip() == "reading…"

    deadline = time.monotonic() + 30
    while pane.dialog[-1][1].strip() == "reading…" and \
            time.monotonic() < deadline:
        time.sleep(0.02)
    assert pane.dialog[0] == ("query", "level : Float")

    assert pane.dismiss() is True
    assert pane.dialog is None
    assert pane.dismiss() is False, "and there is nothing left to dismiss"


def test_question_mark_reaches_the_prelude(tmp_path):
    """Hovering a name from `synth.ges` should reach the paragraph above
    it rather than come back with a type and a shrug."""
    pane, _source = _banked(tmp_path)
    pane.asked = "adsr"
    answer = pane.answer()
    assert answer[0][1].startswith("adsr : Adsr -> Sig Gate")
    assert any("synth.ges" in text for _kind, text in answer)
    assert any("envelope" in text for _kind, text in answer)


def test_question_mark_on_nothing_says_so(tmp_path):
    pane = _pane(tmp_path)
    pane.escape()
    pane.document.go_to(2, 0)
    assert pane.command("?") == "nothing under the cursor"


# ── `Tab`, and what fits a hole ─────────────────────────────────────────────


HOLED = ("wobble : Sig Float\nwobble = _\n"
         "\nsound : Sig Float\nsound = map (n => 0.5) ticks * wobble\n")


def test_tab_asks_only_where_there_is_a_hole(tmp_path):
    """Which is what leaves `Tab` an indent everywhere else.

    An editor that traded a key you press a hundred times a day for one you
    press when you are stuck would be a bad bargain, so the question is
    asked of the cursor rather than of the mode.
    """
    pane = _pane(tmp_path, HOLED)
    pane.document.go_to(1, 9)
    assert pane.at_hole() is True, "on it"
    pane.document.go_to(1, 10)
    assert pane.at_hole() is True, "and just after it, having typed it"
    pane.document.go_to(1, 3)
    assert pane.at_hole() is False

    pane = _pane(tmp_path, "wobble_ = 1\n")
    pane.document.go_to(0, 7)
    assert pane.at_hole() is False, "a `_` in a name is not a hole"


def test_tab_answers_with_what_fits_the_hole_underneath_it(tmp_path):
    """The same answer `typecheck --fits` gives, asked of the hole's *own*
    type rather than of one retyped into a command line."""
    pane = _pane(tmp_path, HOLED)
    rows = pane.what_fits(HOLED, 1, 9)
    assert rows[0] == ("query", "what fits Sig Float:")
    assert any(text.strip().startswith("sine : Sig Float -> Sig Float")
               and "after 1 argument" in text for _kind, text in rows)
    assert not any("  id :" in text for _kind, text in rows), \
        "a name that fits everything is not an answer"


def test_tab_on_a_line_with_no_hole_says_so(tmp_path):
    pane = _pane(tmp_path, HOLED)
    pane.document.go_to(4, 0)
    assert pane.fits() == "no hole on this line"
    assert pane.dialog is None


def test_the_list_of_what_fits_never_stalls_a_frame(tmp_path):
    """A whole front end, like `?` and the sidebar, and a draw is sixteen
    milliseconds."""
    import time

    pane = _pane(tmp_path, HOLED)
    pane.document.go_to(1, 9)

    started = time.monotonic()
    assert pane.fits() == "? what fits here"
    assert time.monotonic() - started < 0.05, "the frame waited for it"
    assert pane.dialog[-1][1].strip() == "reading…"

    deadline = time.monotonic() + 30
    while pane.dialog[-1][1].strip() == "reading…" and \
            time.monotonic() < deadline:
        time.sleep(0.02)
    assert pane.dialog[0] == ("query", "what fits Sig Float:")
    assert pane.dialog.scrolls is True, "forty names have to be reachable"


def test_a_scrolling_dialog_keeps_the_keys_that_scroll_it(tmp_path):
    """A list you cannot reach the bottom of without closing it is a list
    that was never shown to you."""
    pygame = pytest.importorskip("pygame")

    from gestate.audiopygame import Dialog, _in_dialog

    pane = _pane(tmp_path)
    pane.dialog = Dialog([("prose", f"row {i}") for i in range(40)],
                         scrolls=True)
    pane.dialog.shown = 10

    _in_dialog(pane, _press(pygame.K_DOWN), pygame)
    assert pane.dialog.top == 1
    _in_dialog(pane, _press(pygame.K_PAGEDOWN), pygame)
    assert pane.dialog.top == 11
    _in_dialog(pane, _press(pygame.K_HOME), pygame)
    assert pane.dialog.top == 0
    _in_dialog(pane, _press(pygame.K_UP), pygame)
    assert pane.dialog.top == 0, "and it stops at the top"

    _in_dialog(pane, _press(pygame.K_ESCAPE), pygame)
    assert pane.dialog is None, "anything else still takes it away"


def test_a_window_shows_what_fits_in_it_and_clamps_to_it(tmp_path):
    """How many rows fit is the view's answer and changes with the window,
    so a dialog scrolled to the end has to come back into view when the
    window is made taller."""
    from gestate.audiopygame import Dialog

    dialog = Dialog([("prose", f"row {i}") for i in range(20)], scrolls=True)
    dialog.scroll(100)
    assert dialog.window(5) == [("prose", f"row {i}") for i in range(15, 20)]
    assert dialog.window(20) == [("prose", f"row {i}") for i in range(20)]
    assert Dialog([("prose", "one")]).window(10) == [("prose", "one")]


def _press(key, unicode: str = "", mod: int = 0):
    """One `KEYDOWN`, without a window to have pressed it in.

    `importorskip` rather than a bare import, like the three tests that use
    pygame directly: without it those four *errored* where every other
    optional backend skips, so a machine with no pygame could not run the
    suite at all.  The rest of this file drives the editor's model, which
    needs no window and no pygame.
    """
    pygame = pytest.importorskip("pygame")

    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode,
                              mod=mod)


def test_two_front_ends_at_once_do_not_confuse_each_other():
    """Inference is destructive through a *module global*.

    `types.unifying` swaps in a `Unifier` for the duration, which is sound
    in one thread and unsound in two — and stopped being hypothetical when
    the editor grew a rebuild worker and a sidebar that reads types while
    you type.  `pipeline._deep_stack` holds a lock so that whoever asks,
    one front end runs at a time.
    """
    import threading

    from gestate.pipeline import analyse

    source = ("level : Float\nlevel = 0.5\n"
              "\nmain : Float\nmain = level\n")
    seen = []

    def ask():
        seen.append(str(analyse(source).types.get("level")))

    threads = [threading.Thread(target=ask) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert seen == ["Float"] * 6, seen


# ── What the content places, and what a click therefore hits ────────────────
#
# The chrome is five fixed rectangles; a knob belongs beside the line that
# declares it and a piano key belongs where it is drawn, so neither can be
# one.  For a while that meant neither could be *pressed*: `click` knew the
# toolbar, the sidebar and the text, and everything else fell through to
# "put the cursor here".  The knobs were labels and the keyboard was a
# picture of a keyboard.  These check the arithmetic that fixed it — the
# same arithmetic the draw uses, which is the point of it being arithmetic.

KNOBBED = ("cutoff : Sig Float\ncutoff = mkKnob 0.6\n"
           "\nsound : Sig Float\n"
           "sound = zip (x c => x * c) (sine 440.0) cutoff\n")


def _knobbed(tmp_path):
    pane = _pane(tmp_path, KNOBBED)
    pane.bench._place(KNOBBED)
    return pane


def test_a_knob_slot_is_inside_the_view_and_does_not_move_with_its_value():
    """A trough fitted to the label would be a target that moved while you
    were aiming at it, and a knob you are turning is exactly when the
    number written in it is changing."""
    layout = _layout()
    x, y, w, h = layout.knob_rect(0)
    ix, iy, iw, ih = layout.inner
    assert ix <= x and x + w <= ix + iw, "inside the view"
    assert y == iy and h == layout.line_h, "one line, at the top of it"
    assert layout.knob_rect(3)[:1] + layout.knob_rect(3)[2:] \
        == (x, w, h), "every row's slot is the same slot, lower down"
    assert layout.knob_rect(3)[1] == iy + 3 * layout.line_h


def test_dragging_a_knob_turns_it(tmp_path):
    """The thing that was missing.  `Workbench.set_value` is what drives the
    channel, and until now the pygame view had no caller for it at all."""
    pane = _knobbed(tmp_path)
    layout = _layout()
    layout.top = 0
    x, y, w, h = layout.knob_rect(1)            # `cutoff` is on line 2

    assert pane.knob_at(x + w // 2, y + 2, layout) == "cutoff"
    said = pane.click(x + w // 2, y + 2, layout)
    assert pane.turning == "cutoff"
    assert said.startswith("cutoff = ")
    assert pane.bench.value_of("cutoff") == pytest.approx(0.5, abs=0.05)

    # A drag is absolute across the trough, which is what a trough means:
    # a slider you click halfway along goes halfway.
    pane.turn("cutoff", x + w, layout)
    assert pane.bench.value_of("cutoff") == pytest.approx(1.0)
    pane.turn("cutoff", x, layout)
    assert pane.bench.value_of("cutoff") == pytest.approx(0.0)

    # And keeps following the pointer off the end of a 20-character
    # trough, which is where a drag arrives almost at once.
    pane.turn("cutoff", x + 10 * w, layout)
    assert pane.bench.value_of("cutoff") == pytest.approx(1.0)
    pane.release_knob()
    assert pane.turning == ""


def test_a_knob_takes_the_channels_own_type(tmp_path):
    """`set_value` coerces, and it is not cosmetic: `pack_control` writes an
    `Int` channel as an integer and a `Float` one as the bits of a double."""
    pane = _knobbed(tmp_path)
    layout = _layout()
    x, _y, w, _h = layout.knob_rect(0)
    pane.turn("cutoff", x + w // 3, layout)
    assert isinstance(pane.bench.value_of("cutoff"), float)


def test_an_unwired_knob_has_nothing_to_turn(tmp_path):
    """The grey label already says the parameter has no channel behind it.
    A trough you could drag would move a number the sound never hears."""
    source = ("spare : Sig Float\nspare = mkKnob 0.5\n"
              "\nsound : Sig Float\nsound = sine 440.0\n")
    pane = _pane(tmp_path, source)
    layout = _layout()
    layout.top = 0
    assert [(n, w) for _l, n, _v, w in pane.knobs()] == [("spare", False)]
    x, y, w, _h = layout.knob_rect(1)
    assert pane.knob_at(x + w // 2, y + 2, layout) == ""


def test_a_knob_scrolled_off_the_screen_cannot_be_hit(tmp_path):
    """A slot is at the y of a *visible* line.  Without the bound, the
    arithmetic for row 40 of a 20-row window answers a rectangle nobody
    drew, somewhere past the bottom of the view."""
    pane = _knobbed(tmp_path)
    layout = _layout()
    layout.top = 3                        # `cutoff`'s line is above the top
    x, _y, w, _h = layout.knob_rect(0)
    for row in range(layout.rows_on_screen()):
        ry = layout.knob_rect(row)[1]
        assert pane.knob_at(x + w // 2, ry + 2, layout) == ""


def test_a_click_that_is_not_on_a_knob_still_places_the_cursor(tmp_path):
    """Content before text, but text is still what is left."""
    pane = _knobbed(tmp_path)
    layout = _layout()
    layout.top = 0
    ix, iy, _w, _h = layout.inner
    pane.click(ix + layout.margin + 2 * layout.advance,
               iy + 1 * layout.line_h, layout)
    assert (pane.document.row, pane.document.column) == (1, 2)


def test_right_clicking_a_knob_asks_to_learn_a_controller(tmp_path):
    """The same gesture the `tkinter` view has, and the same toggle — the
    decision itself is `Workbench.learn`, which is where it already was."""
    pane = _knobbed(tmp_path)
    layout = _layout()
    layout.top = 0
    x, y, w, _h = layout.knob_rect(1)

    # With no port open there is nothing to learn *from*, and saying so is
    # the whole answer: arming a binding against no device would be a state
    # you could not get out of by moving anything.
    assert "no MIDI" in pane.click(x + w // 2, y + 2, layout, button=3)

    class _Midi:
        learning = None
        bindings = ()

        def learn(self, node):
            self.learning = node

        def cancel(self):
            self.learning = None

        def binding_of(self, _node):
            return None

    pane.bench.midi = _Midi()
    assert pane.click(x + w // 2, y + 2, layout, button=3) \
        == "cutoff: move a controller to bind it"
    assert pane.bench.learning() == "cutoff"
    assert pane.binding("cutoff") == "learning…"
    # Again to change your mind.
    assert pane.click(x + w // 2, y + 2, layout, button=3) \
        == "cutoff: learn cancelled"
    assert pane.bench.learning() is None
    # And it is a knob's gesture, not the window's.
    assert pane.click(x + w // 2, y + 2 + 3 * layout.line_h, layout,
                      button=3) == ""


# ── The drawn keyboard ──────────────────────────────────────────────────────


def test_a_black_key_wins_the_white_one_it_overlaps():
    """`piano_keys` puts the blacks last precisely so that whoever takes the
    last match gets the key drawn on top — which is the one under a finger.
    """
    from gestate.audiopygame import _WHITE, _OCTAVES, _inside

    layout = _layout()
    keys = layout.piano_keys(60)
    whites = _OCTAVES * len(_WHITE)
    assert [note for note, _r in keys[:whites]][:3] == [60, 62, 64]
    assert keys[whites][0] == 61, "C sharp, after all the white keys"

    # A point on the left edge of C sharp, which is over C: two rectangles
    # contain it, and the later one is the black key.
    _note, (bx, by, _bw, _bh) = keys[whites]
    hits = [n for n, r in keys if _inside(r, bx + 1, by + 2)]
    assert hits[0] == 60 and hits[-1] == 61


class _Fingers:
    """A keyboard that only records, so the *order* can be asserted on.

    The real one hands notes to an allocator and reports nothing when there
    is no instrument behind it — which is right, and is why `sounding()`
    cannot answer this question in a test with no synth running.
    """

    MIDDLE_C = 60
    octave = 4

    def __init__(self):
        self.log = []

    def press(self, note):
        self.log.append(("on", note))

    def release(self, note):
        self.log.append(("off", note))

    def sounding(self):
        return set()


def test_clicking_the_drawn_keyboard_plays_it(tmp_path):
    """It used to put the text cursor somewhere and make no sound: the
    keyboard is inside the text area, and the text area is what a click fell
    through to."""
    pane = _pane(tmp_path)
    pane.bench.keyboard = _Fingers()
    layout = _layout()
    pane.open_piano()
    note, (x, y, w, h) = layout.piano_keys(_Fingers.MIDDLE_C)[0]

    assert pane.click(x + w // 2, y + h - 3, layout) == f"note {note}"
    assert pane.pressed == note
    assert pane.release_note() == f"off {note}"
    assert pane.pressed is None
    assert pane.bench.keyboard.log == [("on", note), ("off", note)]


def test_dragging_across_the_keyboard_is_a_glissando(tmp_path):
    """What a keyboard does under a finger: release what it is leaving and
    press what it arrives at, in that order — the other way round would
    steal the voice back from the note it had just given it to."""
    pane = _pane(tmp_path)
    pane.bench.keyboard = _Fingers()
    layout = _layout()
    pane.open_piano()
    keys = layout.piano_keys(_Fingers.MIDDLE_C)
    first, second = keys[0], keys[1]

    pane.press_note(first[1][0] + 2, first[1][1] + first[1][3] - 3, layout)
    pane.press_note(second[1][0] + 2, second[1][1] + second[1][3] - 3, layout)
    assert pane.pressed == second[0]
    assert pane.bench.keyboard.log == [("on", first[0]), ("off", first[0]),
                                       ("on", second[0])]
    # And the same key twice is not a new press: a mouse held still sends
    # a stream of motions, and each would have retriggered the note.
    pane.press_note(second[1][0] + 3, second[1][1] + second[1][3] - 3, layout)
    assert len(pane.bench.keyboard.log) == 3


def test_the_keyboard_only_plays_in_piano_mode(tmp_path):
    pane = _pane(tmp_path)
    layout = _layout()
    _note, (x, y, _w, h) = layout.piano_keys(60)[0]
    for mode in ("text", "command"):
        pane.mode = mode
        assert pane.note_at(x + 2, y + h - 3, layout) is None


def test_the_octave_keys_move_the_drawn_keyboard(tmp_path):
    """`<` and `>`, the tracker keys — shifted because `,` and `.` are notes
    in the lower row.  The draw already read `keyboard.octave`; nothing
    could change it."""
    pane = _pane(tmp_path)
    pane.open_piano()
    was = pane.bench.keyboard.octave
    assert pane.transpose(1) == f"octave {was + 1}"
    assert pane.transpose(-1) == f"octave {was}"


def test_a_piano_key_is_hit_before_a_knob_and_a_knob_before_the_text(
        tmp_path):
    """The order the draw stacks them in, which is the only order that can
    be right: the keyboard is painted over the code and the knobs over it.
    """
    pane = _knobbed(tmp_path)
    layout = _layout()
    layout.top = 0
    pane.open_piano()
    _note, (px, py, pw, ph) = layout.piano_keys(
        pane.bench.keyboard.MIDDLE_C)[0]
    before = (pane.document.row, pane.document.column)
    assert pane.click(px + pw // 2, py + ph - 3, layout).startswith("note ")
    assert (pane.document.row, pane.document.column) == before, \
        "the cursor did not also move"


# ── The loop ────────────────────────────────────────────────────────────────


class _Transport:
    """Enough transport to set a loop on."""

    playing = False
    position = 0
    loop = None

    def seek(self, sample):
        self.position = sample


def test_the_loop_takes_its_end_from_the_piece(tmp_path):
    """A score knows how long it is, and `end_sample` already reads it off
    the schedule for `>`.  Asking someone to type the number a file could
    have told them is what makes a loop a thing you set up rather than use.
    """
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()

    class _Schedule:
        def horizon(self):
            return pane.bench.beats_to_samples(32.0)

    pane.bench.schedule = _Schedule()
    assert pane.loop_span() == (0.0, 32.0)
    assert pane.toggle_loop() == "looping 0–32"
    assert pane.looping
    assert pane.bench.transport.loop == (0, pane.bench.beats_to_samples(32.0))
    assert pane.loop_text() == "⟲ 0–32"

    assert pane.toggle_loop() == "loop off"
    assert not pane.looping
    assert pane.bench.transport.loop is None
    assert pane.loop_text() == ""


def test_a_program_with_no_piece_gets_a_loop_it_can_hear(tmp_path):
    """A guess you can hear and then adjust, rather than a refusal."""
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()
    assert pane.end_sample() is None
    assert pane.loop_span() == (0.0, 16.0)
    assert pane.toggle_loop() == "looping 0–16"


def test_the_loop_points_are_adjustable_and_the_piece_is_the_way_back(
        tmp_path):
    """`[` and `]` put an end where the transport has reached; `O` forgets
    them.  A pair of adjustable points needs the way back as much as it
    needs the points."""
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()

    class _Schedule:
        def horizon(self):
            return pane.bench.beats_to_samples(32.0)

    pane.bench.schedule = _Schedule()
    pane.bench.transport.position = pane.bench.beats_to_samples(8.0)
    assert pane.loop_from_here() == "loop from 8"
    assert pane.loop_span() == (8.0, 32.0), "the end is still the piece's"

    pane.bench.transport.position = pane.bench.beats_to_samples(12.0)
    assert pane.loop_to_here() == "loop to 12"
    assert pane.loop_span() == (8.0, 12.0)

    assert pane.whole_piece() == "looping 0–32"
    assert (pane.loop_from, pane.loop_to) == (0.0, None)


def test_moving_a_point_while_looping_moves_the_loop(tmp_path):
    """A point set on a running loop that the transport did not hear would
    be a control that lies about what it did."""
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()
    pane.loop_to = 8.0
    pane.toggle_loop()
    pane.bench.transport.position = pane.bench.beats_to_samples(2.0)
    assert pane.loop_from_here() == "looping 2–8"
    assert pane.bench.transport.loop \
        == (pane.bench.beats_to_samples(2.0), pane.bench.beats_to_samples(8.0))


def test_a_loop_must_end_after_it_starts(tmp_path):
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()
    pane.loop_from, pane.loop_to = 8.0, 4.0
    assert pane.toggle_loop() == "a loop must end after it starts"
    assert not pane.looping
    assert pane.bench.transport.loop is None


def test_there_is_nothing_to_loop_before_anything_plays(tmp_path):
    """`Workbench.set_loop` returns silently with no transport, which would
    make the button a control that does nothing and says nothing."""
    pane = _pane(tmp_path)
    assert pane.bench.transport is None
    assert pane.toggle_loop() == "nothing is playing to loop"
    assert not pane.looping


def test_the_loop_is_a_button_and_a_key(tmp_path):
    pane = _pane(tmp_path)
    pane.bench.transport = _Transport()
    layout = _layout()
    x, y, _w, _h = layout.buttons["loop"]
    assert pane.click(x + 1, y + 1, layout) == "looping 0–16"
    assert pane.click(x + 1, y + 1, layout) == "loop off"

    pane.mode = "command"
    assert pane.command("o") == "looping 0–16"
    assert pane.command("o") == "loop off"
    # And `l` is still a movement: `hjkl` spent it, which is why the loop
    # is on `o`.
    pane.command("l")
    assert pane.document.pos == 1


# ── The sidebar's dead end ──────────────────────────────────────────────────


def test_every_sidebar_row_goes_to_the_line_it_is_about(tmp_path):
    """It returned `""` for a knob row — silently, and indistinguishably
    from a miss.  Two thirds of a panel of facts about lines did nothing."""
    pane = _pane(tmp_path, KNOBBED)
    layout = _layout(sidebar=300)
    pane.rows = {0: (2, "knob", "cutoff = 0.5"),
                 1: (5, "error", "line 5: nope")}
    y = layout.aside[1] + 2

    assert pane.click_aside(y + 1, layout) == "line 2"
    assert pane.document.row == 1
    assert pane.click_aside(y + layout.line_h + 1, layout) \
        == "line 5: line 5: nope"
    assert pane.document.row == 4
    assert pane.click_aside(y + 9 * layout.line_h, layout) == "", "a miss"


# ── Picking a MIDI port ─────────────────────────────────────────────────────


def test_a_port_is_named_by_index_or_by_part_of_its_name(monkeypatch):
    """The names real drivers hand out look like `Launchkey Mini MK3:
    Launchkey Mini MK3 MIDI 1 28:0`, which is not a thing anyone types
    twice — so `--midi 1` is an index and `--midi launchkey` is a search.
    """
    from gestate import audiomidi

    names = ["Midi Through:Midi Through Port-0 14:0",
             "Launchkey Mini MK3:Launchkey Mini MK3 MIDI 1 28:0"]
    monkeypatch.setattr(audiomidi, "input_names", lambda: names)

    assert audiomidi.resolve_port(None) is None, "the first, as Listener means"
    assert audiomidi.resolve_port("") is None
    assert audiomidi.resolve_port("1") == names[1]
    assert audiomidi.resolve_port("launchkey") == names[1]
    assert audiomidi.describe_ports().splitlines()[1].startswith("  1  ")

    with pytest.raises(audiomidi.MidiError, match="no MIDI input 7"):
        audiomidi.resolve_port("7")
    with pytest.raises(audiomidi.MidiError, match="no MIDI input matches"):
        audiomidi.resolve_port("nord")


def test_a_spec_that_matches_two_ports_is_refused(monkeypatch):
    """Quietly taking the first would bind your knobs to whichever device
    enumerated first today."""
    from gestate import audiomidi

    monkeypatch.setattr(audiomidi, "input_names",
                        lambda: ["Keystep 1", "Keystep 2"])
    with pytest.raises(audiomidi.MidiError, match="matches 2 inputs"):
        audiomidi.resolve_port("keystep")


def test_midi_ls_is_asked_on_its_own(monkeypatch, capsys):
    """Being made to name a program before being told what is plugged in is
    the wrong way round, and the answer does not depend on the program."""
    from gestate import audiomidi, audiopygame

    monkeypatch.setattr(audiomidi, "input_names", lambda: ["Keystep 1"])
    assert audiopygame.main(["--midi-ls"]) == 0
    assert capsys.readouterr().out.strip() == "0  Keystep 1"


# ── Searching ───────────────────────────────────────────────────────────────
#
# `/` to open, type, `Return` to keep it, `Esc` to put the cursor back; `n`
# and `N` for the next and the previous.  Vim's keys, because `hjkl` beside
# the arrows already promised them.

FINDABLE = ("alpha beta\n"
            "lowpassSvf here\n"
            "gamma svf delta\n"
            "beta again\n")


def _finding(tmp_path, at: int = 0) -> Pane:
    pane = _pane(tmp_path, FINDABLE)
    pane.mode = "command"
    pane.document.pos = at
    return pane


def _type(pane: Pane, text: str) -> str:
    said = ""
    for char in text:
        said = pane.search_key(char)
    return said


def test_slash_opens_a_prompt_and_typing_goes_into_it(tmp_path):
    pane = _finding(tmp_path)
    assert pane.command("/") == "/"
    assert pane.finding == "", "the prompt is open and empty"
    assert _type(pane, "gamma") == "/gamma"
    assert pane.finding == "gamma"


def test_the_cursor_follows_the_pattern_as_it_is_typed(tmp_path):
    """Incremental, which is the half that makes it worth having: you stop
    typing when you can see you have arrived."""
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "gamma")
    assert pane.document.row == 2


def test_return_keeps_the_place_and_the_pattern(tmp_path):
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "gamma")
    said = pane.search_key("", "return")
    assert pane.finding is None, "the prompt closed"
    assert pane.pattern == "gamma", "and `n` has something to repeat"
    assert pane.document.row == 2
    assert "line 3" in said


def test_escape_puts_the_cursor_back(tmp_path):
    """**The reason `found_from` exists.**  Searching moves the cursor while
    you type, so changing your mind has to be able to undo that — an editor
    that leaves you somewhere else has lost your place for you."""
    pane = _finding(tmp_path, at=30)
    pane.command("/")
    _type(pane, "alpha")
    assert pane.document.pos == 0, "it moved while typing"
    assert pane.search_key("", "escape") == "search cancelled"
    assert pane.document.pos == 30, "and came back"
    assert pane.finding is None


def test_a_pattern_that_matches_nothing_says_so_and_moves_nothing(tmp_path):
    pane = _finding(tmp_path, at=30)
    pane.command("/")
    assert "no match" in _type(pane, "zzz")
    assert pane.document.pos == 30


def test_backspace_walks_back_and_then_cancels(tmp_path):
    """Deleting the last character of a pattern leaves you where the prompt
    came from, which is the only place it can sensibly leave you."""
    pane = _finding(tmp_path, at=30)
    pane.command("/")
    _type(pane, "al")
    assert pane.search_key("", "backspace") == "/a"
    assert pane.search_key("", "backspace") == "/"
    assert pane.finding == "", "still open, and empty"
    assert pane.search_key("", "backspace") == "search cancelled"
    assert pane.finding is None and pane.document.pos == 30


def test_backspacing_searches_from_where_the_prompt_opened(tmp_path):
    """Not from the match the last keystroke found — otherwise deleting a
    character searches forward from there and backspacing walks *away* down
    the file instead of back to where it started."""
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "beta")
    first = pane.document.pos
    _type(pane, "x")                       # no match; cursor goes home
    assert pane.search_key("", "backspace") == "/beta"
    assert pane.document.pos == first, "it walked off instead of back"


def test_n_and_shift_n_step_through_the_matches(tmp_path):
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "beta")
    pane.search_key("", "return")
    assert pane.document.row == 0
    assert "line 4" in pane.command("n")
    assert "line 1" in pane.command("N")


def test_the_search_wraps_at_both_ends(tmp_path):
    """A file is a loop when you are looking for something in it; stopping
    at the end to say it is the end is a message about the search rather
    than about the text."""
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "beta")
    pane.search_key("", "return")
    rows = [pane.document.row]
    for _ in range(3):
        pane.command("n")
        rows.append(pane.document.row)
    assert rows == [0, 3, 0, 3], rows
    pane.command("N")
    assert pane.document.row == 0, "backward wraps too"


def test_a_lowercase_pattern_ignores_case_and_a_capital_does_not(tmp_path):
    """Smart case.  `svf` finds `lowpassSvf`, which is the search you
    actually type in a language whose names are camel case."""
    pane = _finding(tmp_path)
    pane.command("/")
    _type(pane, "svf")
    assert pane.document.row == 1, "lowercase found the capitalised one"
    pane.search_key("", "escape")

    pane.command("/")
    _type(pane, "Svf")
    assert pane.document.row == 1, "a capital finds only the capital"
    pane.search_key("", "return")
    assert "no match" not in pane.command("n") or pane.document.row == 1


def test_the_pattern_is_plain_text_and_not_a_regular_expression(tmp_path):
    """`spec/` is full of `[:` and `⃝`; a search box that read those as
    syntax would be a trap rather than a feature."""
    pane = _pane(tmp_path, "a [: b :] c\nd (x) e\n")
    pane.mode = "command"
    pane.command("/")
    assert _type(pane, "[:") == "/[:"
    assert pane.document.pos == 2
    pane.search_key("", "escape")
    pane.command("/")
    assert "no match" in _type(pane, "a.c"), "`.` matched any character"


def test_n_before_any_search_says_what_to_press(tmp_path):
    pane = _finding(tmp_path)
    assert "`/`" in pane.command("n")
    assert pane.document.pos == 0


def test_the_prompt_owns_the_keyboard_while_it_is_up(tmp_path):
    """`i` while searching is the letter `i`, not "enter text mode" — the
    same bargain the reference makes, and the reason this is a prompt and
    not a set of bindings."""
    pane = _finding(tmp_path)
    pane.command("/")
    pane.search_key("i")
    assert pane.mode == "command" and pane.finding == "i"


# ── Errors you can actually read ────────────────────────────────────────────
#
# A compiler error is a paragraph and a status bar is a line.  The bar used
# to be handed the paragraph: `font.render` does not know what a newline is,
# so a multi-line error drew a box where the break belonged, and a long one
# ran off the right edge of the window.  The text was on the screen and
# could not be read, which is the same as not being there.


def test_a_long_line_is_elided_to_what_fits():
    from gestate.audiopygame import _elided

    got = _elided("Type mismatch: expected Sig Float but got Sig Int", 24)
    assert len(got) <= 24
    assert got.endswith("…")


def test_a_further_line_is_marked_rather_than_drawn():
    """`font.render` renders a newline as a box.  Saying there is more is
    the honest thing a single line can do."""
    from gestate.audiopygame import _elided

    got = _elided("first line\nsecond line", 40)
    assert "\n" not in got
    assert got == "first line ⏎"


def test_a_short_message_is_left_exactly_alone():
    from gestate.audiopygame import _elided

    assert _elided("saved s.ges", 40) == "saved s.ges"


def test_wrapping_folds_long_lines_and_keeps_the_shape():
    """Its own newlines are kept — a compiler error puts the offending
    source on a line of its own, and breaking that apart would lose the
    shape of it."""
    from gestate.audiopygame import _wrapped

    rows = _wrapped("a long sentence that will not fit in the box\n"
                    "\n    sound = zip f a b", 26)
    assert all(len(r) <= 26 for r in rows), rows
    assert "" in rows, "the blank line was dropped"
    # Short enough to fit, so it is left exactly as written — indentation
    # and all, because that indentation is what says it is source.
    assert "    sound = zip f a b" in rows, rows
    assert len(rows) > 3, "the long sentence was not folded"


def test_the_whole_error_is_kept_not_just_its_first_line(tmp_path):
    """**The half that was thrown away.**  `_first_line` returned line one
    and dropped the rest, so the part of a type error that says *what was
    expected where* existed only until it was formatted."""
    bench = _pane(tmp_path).bench
    summary = bench._first_line(Exception("expected Sig Float, got Sig Int\n"
                                          "  in the second argument of zip\n"
                                          "  at line 2"))
    assert summary == "expected Sig Float, got Sig Int"
    assert len(bench.trouble.splitlines()) == 3, bench.trouble


def test_a_complaint_reaches_the_sidebar_without_a_keystroke(tmp_path):
    """**Why an error is a live row and not a cached one.**  The holes are
    computed from the text and cached on it; a message arriving with no
    keystroke behind it could not refresh that cache, so `note_fault` used
    to reach in and null it.  Read from the build instead."""
    pane = _pane(tmp_path, FAULTY)
    assert pane.errors() == []
    pane.bench._first_line(Exception("expected Sig Float (at s.ges:2:9)"))
    assert pane.errors() == [(2, "expected Sig Float (at s.ges:2:9)")]


def test_a_fixed_error_stops_being_shown(tmp_path):
    """**The bug this replaced.**  `faults` was a list nothing ever
    emptied, so an error stayed in the sidebar after it was fixed — until
    the editor was closed."""
    pane = _pane(tmp_path, FAULTY)
    pane.bench._first_line(Exception("expected Sig Float (at s.ges:2:9)"))
    assert pane.errors()

    pane.bench.trouble = ""          # what `_progress` does on a good build
    assert pane.errors() == []
    assert not [k for k, _r, _t in pane.laid_out(14, 44) if k != "line"]


def test_an_error_that_names_nowhere_here_has_no_line_number(tmp_path):
    """Line `0` is the sidebar's "no number to draw" — it is what a
    prelude error gets, and it is the same one the banner is built from."""
    pane = _pane(tmp_path, FAULTY)
    pane.bench._first_line(Exception("No instance (at prelude line 873:12)"))
    assert pane.errors() == [(0, "No instance (at prelude line 873:12)")]


def test_the_sidebar_shows_one_line_of_an_error_and_the_text_shows_it_all(
        tmp_path):
    """A sidebar row is one line wide; the interleave is not."""
    pane = _pane(tmp_path, FAULTY)
    pane.bench._first_line(Exception(
        "expected Sig Float (at s.ges:2:9)\n  in the second argument"))
    assert pane.errors() == [(2, "expected Sig Float (at s.ges:2:9)")]
    notes = " ".join(t for k, _r, t in pane.laid_out(14, 60) if k == "note")
    assert "in the second argument" in notes


# ── The error goes between the lines ────────────────────────────────────────
#
# It used to be drawn right-aligned on the line it was about, which suits
# `hole` and `bank` — three words each — and is hopeless for a compiler
# error: a sentence right-aligned in a narrow window starts at a negative x
# and is drawn straight through the code and the gutter.

FAULTY = "sound : Sig Float\nsound = zip f a b\nf : Int\nf = 3\n"


def _with_trouble(tmp_path, message: str) -> Pane:
    pane = _pane(tmp_path, FAULTY)
    pane.bench.trouble = message
    return pane


def test_an_error_in_this_file_is_interleaved_under_its_line(tmp_path):
    pane = _with_trouble(tmp_path, "expected Sig Float, got Sig Int "
                                   "(at s.ges:2:9)")
    shown = pane.laid_out(14, 44)
    kinds = [k for k, _r, _t in shown]
    assert kinds[:3] == ["line", "line", "note"], kinds
    notes = [(r, t) for k, r, t in shown if k == "note"]
    assert notes, "nothing was interleaved"
    assert all(r == 1 for r, _t in notes), "attached to the wrong line"
    assert "expected Sig Float" in " ".join(t for _r, t in notes)


def test_an_error_elsewhere_becomes_a_banner_that_says_where(tmp_path):
    """You cannot put a mark on a line that is not in this file, so the
    location is spelled out instead — `in_source` already says `prelude
    line 873` rather than translating it into a negative number, and
    throwing that away would discard the one thing worth knowing."""
    pane = _with_trouble(tmp_path, "No instance for Floating "
                                   "(at prelude line 873:12)")
    shown = pane.laid_out(14, 60)
    banner = [t for k, _r, t in shown if k == "banner"]
    assert banner, "it was not hoisted to the top"
    assert shown[0][0] == "banner", "the banner is not first"
    assert "prelude line 873" in " ".join(banner), "the location was lost"
    assert not [k for k, _r, _t in shown if k == "note"]


def test_a_long_message_is_wrapped_rather_than_run_off_the_edge(tmp_path):
    pane = _with_trouble(
        tmp_path, "Type mismatch in the second argument of zip: expected a "
                  "signal of floats but got a signal of integers "
                  "(at s.ges:2:9)")
    shown = pane.laid_out(20, 40)
    notes = [t for k, _r, t in shown if k == "note"]
    assert len(notes) > 1, "it was not wrapped"
    assert all(len(t) <= 40 for t in notes), notes


def test_clicking_a_note_lands_on_the_code_it_is_about(tmp_path):
    """A note carries the row it is attached to, so the pointer never
    lands on nothing."""
    pane = _with_trouble(tmp_path, "expected Sig Float (at s.ges:2:9)")
    pane.shown = pane.laid_out(14, 44)
    note_rows = [i for i, (k, _r, _t) in enumerate(pane.shown) if k == "note"]
    assert note_rows
    for i in note_rows:
        assert pane.row_at(i) == 1


def test_the_lines_below_an_error_are_still_clickable_where_they_are_drawn(
        tmp_path):
    """**The bug an interleave invites.**  Inserting rows while drawing and
    not while clicking puts the cursor a line above the pointer for every
    diagnostic on screen."""
    pane = _with_trouble(tmp_path, "expected Sig Float (at s.ges:2:9)")
    pane.shown = pane.laid_out(14, 44)
    for i, (kind, row, _t) in enumerate(pane.shown):
        if kind == "line":
            assert pane.row_at(i) == row
            assert pane.screen_row(row) == i


def test_with_no_error_the_view_is_exactly_the_document(tmp_path):
    """Nothing is interleaved unless something is wrong, which is the
    common case and has to cost nothing."""
    pane = _pane(tmp_path, FAULTY)
    shown = pane.laid_out(14, 44)
    assert [k for k, _r, _t in shown] == ["line"] * len(shown)
    assert [t for _k, _r, t in shown] == [
        pane.document.line(i) for i in range(len(shown))]


def test_row_at_falls_back_before_anything_has_been_drawn(tmp_path):
    """`place` can be called before the first frame — a click that arrives
    in the same tick as the window opening."""
    pane = _pane(tmp_path, FAULTY)
    pane.shown = []
    assert pane.row_at(3) == 3
    pane.top = 2
    assert pane.row_at(1) == 3


# ── The piano over the canvas ───────────────────────────────────────────────
#
# A synth that draws is one you want to play *while watching it*, and the
# piano used to take you to the text to do it.  There is deliberately no
# *key* for this in canvas mode — the letters are the canvas's own, and a
# mode that quietly took one back is the thing modes are complained about
# for — so the toolbar button is the way in, which is what a toolbar is.


def test_the_button_opens_the_piano_from_the_canvas(tmp_path):
    pane = _pane(tmp_path)
    pane.mode = "canvas"
    assert pane.button("piano") == "mode: piano (play)"
    assert pane.mode == "piano"
    assert pane.piano_over == "canvas", "it forgot where it came from"


def test_no_letter_opens_the_piano_in_canvas_mode(tmp_path):
    """The canvas owns its letters.  `p` is a command-mode key and stays
    one."""
    pane = _pane(tmp_path)
    pane.mode = "canvas"
    assert pane.typed("p") == ""
    assert pane.mode == "canvas"


def test_escape_goes_back_to_the_canvas_it_was_opened_over(tmp_path):
    pane = _pane(tmp_path)
    pane.mode = "canvas"
    pane.button("piano")
    assert pane.close_piano() == "mode: canvas"
    assert pane.mode == "canvas" and pane.piano == ""
    assert pane.piano_over == ""


def test_opened_from_command_it_still_goes_back_to_command(tmp_path):
    """The old way round, unchanged: nothing about this may move the
    keyboard for someone who was editing text."""
    pane = _pane(tmp_path)
    pane.mode = "command"
    pane.command("p")
    assert pane.mode == "piano" and pane.piano_over == ""
    assert pane.close_piano() == "mode: command"
    assert pane.mode == "command"


def test_step_mode_goes_to_the_text_even_from_the_canvas(tmp_path):
    """Step mode is for writing notes *into* the file, and there is
    nothing to type into on a canvas."""
    pane = _pane(tmp_path)
    pane.mode = "canvas"
    pane.button("step")
    assert pane.piano == "step"
    assert pane.piano_over == "", "it would have drawn over the canvas"


def test_the_canvas_is_what_is_drawn_behind_it(tmp_path):
    """The one thing a test can check about the drawing without a window:
    which branch `_draw` would take."""
    pane = _pane(tmp_path)
    pane.mode = "canvas"
    pane.button("piano")
    # `_draw` chooses the canvas branch on either of these being true.
    assert pane.mode == "piano" and pane.piano_over == "canvas"


# ── The patch next door ─────────────────────────────────────────────────────
#
# `prev`/`next` walk the directory, `[patch]` is a chooser over the same
# list, and `steal` is save-as-copy-and-continue.  All of it is `Pane`
# methods with no pygame in them, which is what these assert on.


def _three(tmp_path) -> Pane:
    for name in ("a.ges", "b.ges", "c.ges"):
        (tmp_path / name).write_text(f"# {name}\n" + SOURCE)
    return Pane.open(Workbench(tmp_path / "a.ges", rate=8000, block=64))


def test_next_and_prev_walk_the_directory(tmp_path):
    pane = _three(tmp_path)
    assert pane.switch_by(1) == "opened b.ges"
    assert pane.bench.path.name == "b.ges"
    assert pane.document.text.startswith("# b.ges")
    assert pane.switch_by(-1) == "opened a.ges"
    # The ends wrap, so the buttons never die at a wall.
    assert pane.switch_by(-1) == "opened c.ges"


def test_a_dirty_file_holds_the_door(tmp_path):
    pane = _three(tmp_path)
    pane.document.insert("edited ")
    said = pane.switch_by(1)
    assert "unsaved" in said and pane.bench.path.name == "a.ges", \
        "a switch must not silently discard edits"
    assert (tmp_path / "a.ges").read_text().startswith("# a.ges"), \
        "and must not silently save them either"
    # The same request again is the confirmation.
    assert pane.switch_by(1) == "opened b.ges"
    assert not pane.dirty


def test_a_different_target_restarts_the_question(tmp_path):
    pane = _three(tmp_path)
    pane.document.insert("edited ")
    assert "unsaved" in pane.switch_by(1)          # asks about b
    assert "unsaved" in pane.switch_by(-1), \
        "changing the target must ask again, not inherit the confirmation"


def test_steal_copies_the_unsaved_text_and_moves_there(tmp_path):
    pane = _three(tmp_path)
    pane.document.insert("# bent\n")
    said = pane.steal()
    assert said == "stole into a-take2.ges"
    assert pane.bench.path.name == "a-take2.ges"
    assert (tmp_path / "a-take2.ges").read_text().startswith("# bent")
    assert (tmp_path / "a.ges").read_text().startswith("# a.ges"), \
        "the original is left exactly as it was"
    assert not pane.dirty, "the copy opens clean - the edits are saved in it"
    # Stealing a steal counts upward rather than growing a suffix.
    assert pane.steal() == "stole into a-take3.ges"


def test_the_chooser_picks_with_arrows_and_return(tmp_path):
    pane = _three(tmp_path)
    said = pane.choose()
    assert pane.choosing and pane.dialog is not None and "3 patches" in said
    assert pane.choice_move(1) == "b.ges"
    assert pane.choice_commit() == "opened b.ges"
    assert not pane.choosing and pane.dialog is None
    assert pane.bench.path.name == "b.ges"


def test_dismissing_the_chooser_changes_nothing(tmp_path):
    pane = _three(tmp_path)
    pane.choose()
    pane.choice_move(1)
    pane.dismiss()
    assert not pane.choosing and pane.bench.path.name == "a.ges"


def test_the_patch_buttons_exist():
    """Containment is `test_every_button_is_inside_the_chrome`'s sweep;
    this pins that the four are in the chrome at all."""
    for name in ("prev", "patch", "next", "steal"):
        assert name in _layout().buttons, name
