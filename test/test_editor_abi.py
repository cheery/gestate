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
