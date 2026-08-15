"""The editor's C ABI, driven the way `audioeditor` will drive it.

Opens a real window — briefly — because that is what there is to test:
the boundary between a Rust-owned rope and a Python orchestrator, and
whether the two agree about text, versions and shutting down.

Skipped where there is no display and where there is no cargo, for the
same reasons `test_export.py` skips without a toolchain.
"""

from __future__ import annotations

import os
import shutil
import time

import pytest

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"),
    reason="the editor opens a window")
needs_cargo = pytest.mark.skipif(shutil.which("cargo") is None,
                                 reason="the editor is Rust")


def _wait(f, seconds=5.0):
    """Until `f()`, or give up — the window's loop is on its own thread."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if f():
            return True
        time.sleep(0.02)
    return False


@needs_display
@needs_cargo
def test_the_editor_opens_holds_text_and_closes():
    from gestate.editor import Editor

    text = "sound : Sig Float\nsound = sine 220.0\n"
    with Editor(text, 600, 400) as ed:
        assert _wait(lambda: ed.is_open), "the window never opened"
        # **The text crosses unchanged**, which is the whole contract:
        # what Python handed over is what the rope holds.
        assert ed.text == text
        assert ed.version == 0, "opening is not an edit"
        assert not ed.changed(), "nothing has happened yet"

        # Loading from this side is a pull the window makes on its next
        # frame, so it takes a moment rather than being instant.
        ed.text = "changed : Sig Float\n"
        assert _wait(lambda: ed.text.startswith("changed")), \
            "the window never picked up the text"
        assert ed.changed(), "a load is an edit"
        assert not ed.changed(), "and it is only reported once"

        ed.request_close()
        assert _wait(lambda: not ed.is_open), "the window would not shut"


@needs_display
@needs_cargo
def test_characters_not_bytes_cross_the_boundary():
    """Positions are characters — the rope's unit, and Python's.

    A text with multi-byte characters in it is where a boundary that
    thought in bytes would come apart, and it would come apart
    *quietly*: the text would look right and every offset after the
    first non-ASCII character would be wrong.
    """
    from gestate.editor import Editor

    text = "åäö 日本 🎹\nsecond line\n"
    with Editor(text, 400, 300) as ed:
        assert _wait(lambda: ed.is_open)
        assert ed.text == text
        assert ed.pos == 0
        # The caret starts at zero and the document is what it is; the
        # count that matters is characters, not the 30-odd bytes.
        assert len(ed.text) == len(text)


@needs_display
@needs_cargo
def test_closing_twice_and_using_a_closed_editor_are_quiet():
    """A host that tidies up twice must not crash the process."""
    from gestate.editor import Editor

    ed = Editor("x", 300, 200)
    assert _wait(lambda: ed.is_open)
    ed.close()
    ed.close()
    assert not ed.is_open
    assert ed.text == ""
    assert ed.version == 0
    ed.request_close()


@needs_display
@needs_cargo
def test_the_furniture_reaches_the_window_and_gestures_come_back():
    """The wire, both directions, through a real window.

    `spec/workbench.md`: the model publishes a description of the
    furniture and the window draws it; what comes back is names and
    literals.  Nothing in either direction is a pointer into the other
    side's heap, which is what makes this a boundary rather than a
    shared object.
    """
    from gestate.editor import Editor

    with Editor("sound : Sig Float\n", 500, 360) as ed:
        assert _wait(lambda: ed.is_open)
        assert ed.gestures() == [], "nothing has happened yet"

        ed.describe("status\tapplied\n"
                    "knob\tcutoff\t1\t0.4\t0\t1\tFloat\n"
                    "command\tapply\tapply\tCtrl-S\tRebuild it.\n"
                    "command\tplay\tplay\tSpace\tStart or stop.")
        # The window takes it on its next frame; nothing here waits on
        # a reply, because a description is not a question.
        time.sleep(0.2)
        assert ed.is_open, "a description must not shut the window"
        ed.request_close()
        assert _wait(lambda: not ed.is_open)


@needs_display
@needs_cargo
def test_gestures_are_drained_rather_than_read():
    """Nothing is seen twice: a command run because the queue was polled
    again is the sort of bug that plays a note nobody asked for."""
    from gestate.editor import Editor

    with Editor("x\n", 400, 300) as ed:
        assert _wait(lambda: ed.is_open)
        # An edit from this side is an edit, so the window says so.
        ed.text = "y\n"
        assert _wait(lambda: ed.gestures() != [] or ed.text == "y\n")
        first = ed.gestures()
        second = ed.gestures()
        assert second == [], f"seen twice: {first} then {second}"
        ed.request_close()
        assert _wait(lambda: not ed.is_open)


@needs_display
@needs_cargo
def test_a_file_is_coloured_before_it_is_edited():
    """**`None` and empty are different**, and that was the whole bug.

    `changed()` answers *has it moved since I last asked*, which on a
    freshly opened file is `False` — the text arrived before anyone
    asked.  Filling the line cache only on a change therefore left it
    empty until the first keystroke, so nothing was painted and the file
    was drawn in plain ink: colouring that appeared only once you typed,
    which reads as colouring that does not work.

    Checked through a real window because that is where it went wrong; a
    double would have been primed by whatever the test handed it.
    """
    from gestate.editor import Editor
    from gestate.session import Session, furniture
    from gestate.workbench import Window

    class Bench:
        sites, banks, values, knob_types = [], [], {}, {}

    with Editor("cutoff = mkKnob 0.4  # hi\n", 400, 300) as ed:
        assert _wait(lambda: ed.is_open)
        view = Window(ed)
        assert view.visible(), "nothing was visible before an edit"
        said = furniture(Session(bench=Bench(), view=view))
        painted = [l for l in said.splitlines() if l.startswith("paint\t")]
        assert painted, f"no colour without typing first: {said!r}"
        assert "note" in painted[0], "the comment was not coloured"
        ed.request_close()
        assert _wait(lambda: not ed.is_open)


@needs_display
@needs_cargo
def test_a_caret_order_lands_in_the_text_that_came_with_it():
    """One frame, and the text arrives before the orders about it.

    `complete` fills a hole and then stands on the next one: it
    replaces the document through `ged_set_text` and moves the caret
    through `goto` and `col`, all in the same breath, and the window
    collects both on its next frame.  Collected the other way round the
    column is measured against the *old* line — `foo = _` is seven
    characters, so column 14 clamps back to 7 — and the new text then
    keeps that wrong place, which put the caret inside `(length` rather
    than on the hole it had just made.  The order is the model's.
    """
    from gestate.editor import Editor

    was = "foo : Int\nfoo = _\n"
    now = "foo : Int\nfoo = (length _)\n"
    hole = now.index("_)")            # the hole the completion made
    line = now[:hole].count("\n") + 1
    col = hole - (now.rindex("\n", 0, hole) + 1)

    with Editor(was, 500, 300) as ed:
        assert _wait(lambda: ed.is_open)
        ed.text = now
        ed.order(f"goto\t{line}")
        ed.order(f"col\t{col}")
        assert _wait(lambda: ed.text == now), "the text never landed"
        assert _wait(lambda: ed.pos == hole), \
            f"the caret is at {ed.pos}, not on the hole at {hole}"


@needs_display
@needs_cargo
def test_the_model_may_ask_a_question_of_its_own():
    """`ask` — the wire word behind `complete`'s walk, through a real
    window.

    `Tab` at a hole knows the type before the person does, so the
    question arrives with that argument taken and the caret in the
    field after it; and a completion that lands on another hole asks
    itself again with the *new* type, which is what empties the field.
    Both are this order, and what comes back is the `wants` that says
    which argument the box is on now — the same round trip a typed
    letter makes.
    """
    from gestate.editor import Editor

    with Editor("foo : Int\nfoo = _\n", 500, 360) as ed:
        assert _wait(lambda: ed.is_open)
        ed.describe("status\tready\n"
                    "command\tcomplete\tcomplete\tTab\tFill a hole."
                    "\tText,Filler\n"
                    "command\tplay\tplay\tSpace\tStart or stop.")
        time.sleep(0.2)
        ed.gestures()                       # the description's own traffic

        ed.order("ask\tcomplete\tInt")
        # Argument **one**, empty field, and the type riding after it:
        # taken, not stood in the box for somebody to press Return on
        # — and said back, so a list ranked for `Int` can be ranked
        # for whatever is typed over it instead.
        assert _wait(lambda: "wants\tcomplete\t1\t\tInt" in ed.gestures()), \
            "the window never said which argument it is on"

    # A verb the list never advertised cannot be asked for: the
    # vocabulary rule, from the model's side of the wire.
    with Editor("foo : Int\n", 400, 300) as ed:
        assert _wait(lambda: ed.is_open)
        ed.describe("status\tready\n"
                    "command\tplay\tplay\tSpace\tStart or stop.")
        time.sleep(0.2)
        ed.gestures()
        ed.order("ask\ttranspose\t3")
        time.sleep(0.3)
        said = ed.gestures()
        assert not any("transpose" in g for g in said), said
        assert ed.is_open, "and it did not take the window down with it"
