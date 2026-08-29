"""The front end still compiles where no thread can be started.

`pipeline._deep_stack_alone` runs the typecheck on a thread with a big
stack.  Two platforms refuse that differently: one refuses the size
(`threading.stack_size` raises), and Pyodide accepts the size and then
refuses `Thread.start` — `RuntimeError: can't start new thread`, found
on 2026-08-29 measuring `card:online.md`'s C1.  Both take the inline
path; this holds the second, which the first's fallback did not cover.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from gestate import pipeline

TWINKLE = Path(__file__).resolve().parents[1] / "examples" / "audio" / "twinkle.ges"


def test_a_thread_that_cannot_start_falls_back_to_inline(monkeypatch):
    def refuse(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(threading.Thread, "start", refuse)
    from gestate.audioperform import graph_of

    graph = graph_of(TWINKLE.read_text(), rate=44100)
    assert graph.channels() == 1


def test_the_inline_path_reraises_the_program_error_not_the_platform(monkeypatch):
    def refuse(self):
        raise RuntimeError("can't start new thread")

    monkeypatch.setattr(threading.Thread, "start", refuse)
    with pytest.raises(Exception, match="nosuchname"):
        pipeline.analyse("sound : Sig Float\nsound = nosuchname 1.0\n")
