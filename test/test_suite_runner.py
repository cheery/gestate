"""`tools/suite.py`'s own reporting, which nothing checked.

**The suite is the instrument that says whether the tree is good, and
it has twice reported a green page for a partial run** — its own
comments carry both cases: a two-pass run whose totals came from the
second pass alone, and a version that captured output instead of
streaming it so a healthy run looked like a hang.

The Rust workspace joined it on 2026-08-18 (`board/done/interface-oracle.md`,
Henri: *"we have to add the command to run rust tests from suite… I had
no idea rust tests weren't there in the suite"*).  344 tests across
eighteen binaries had been running nowhere.  The risk a new pass brings
is the old one: that it fails and the page still reads green.

So what is checked here is the **verdict**, not the crates — the crates
check themselves, and `cargo` is what runs them.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("suite", ROOT / "tools" / "suite.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


def fake_stream(rc: int, out: str):
    """Stands in for `main`'s streaming runner, which needs a terminal."""
    def stream(argv):
        return rc, out
    return stream


GREEN = "test result: ok. 81 passed; 0 failed\ntest result: ok. 9 passed; 0 failed\n"


def test_a_green_workspace_is_counted_across_every_binary():
    """Eighteen binaries, and the count has to be their sum.

    The failure this guards is the one the file already made once with
    pytest's totals: keeping the **last** match rather than adding them
    up, which reported twenty-six tests as the whole run.
    """
    rc, _out, note = suite._rust(fake_stream(0, GREEN), False, ROOT)
    assert rc == 0
    assert note == "90 passed"


def test_a_red_crate_reaches_the_report_and_the_exit_code():
    """A pass that fails silently is worse than one that does not run.

    Deliberately **not a stop**: the Python pass is twenty-five minutes
    of evidence and must still reach the page.  So the contract is that
    the return code survives and the row says so.
    """
    rc, _out, note = suite._rust(fake_stream(101, "test result: FAILED"), False, ROOT)
    assert rc == 101, "a red workspace must not exit zero"
    assert "fail" in note.lower(), "the report row must say the crates failed"


def test_no_cargo_is_a_note_and_not_a_failure(monkeypatch):
    """`doc/install.md`'s posture, kept: everything `apt` buys is a
    backend, and a missing one degrades politely.  A machine with no
    cargo still has a Python suite worth running — and must not be told
    its tree is broken.
    """
    monkeypatch.setattr(suite.shutil, "which", lambda _name: None)
    rc, _out, note = suite._rust(fake_stream(0, GREEN), False, ROOT)
    assert rc == 0
    assert "no cargo" in note
