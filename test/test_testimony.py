"""doc/testimony.md against the memories it classifies.

`card:testimony-inventory.md`.  The table is a session's judgment and
no test can check a judgment; what a test can hold is that the table
points at things that exist, that the count on the page is the count
the table gives, and that the tool refuses a row that resolves to
nothing — so the page cannot drift from the directory it describes
without saying so.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import testimony  # noqa: E402

TOOL = ROOT / "tools" / "testimony.py"


def test_every_row_names_a_memory_that_exists_and_a_kind_that_is_one():
    assert testimony.faults(testimony.rows(), testimony.memories()) == []


def test_the_count_on_the_page_is_the_count_the_table_gives():
    """The page quotes the table's line; a row added or re-kinded
    without the line leaves a stale number, and this is the thing that
    says so.  **A gate since 2026-09-13**, and it can be one only
    because the line reads nothing but the table — see the next test."""
    page = testimony.PAGE.read_text(encoding="utf-8")
    quoted = re.search(r"^\s+(testimony: .*)$", page, re.M)
    assert quoted, "the page carries the tool's summary line under §\"The count\""
    assert quoted.group(1) == testimony.table_line(testimony.rows())


def test_a_new_memory_is_named_and_does_not_move_the_quoted_line():
    """`card:testimony-inventory.md` Q1, *report, not gate*: a memory
    with no row is printed by the commit's lamp, and the line the gate
    holds the page to does not change — so the gate cannot refuse it."""
    table = [("one", "henri", "his words")]
    before = testimony.summary(table, {"one"}).splitlines()
    after = testimony.summary(table, {"one", "a-new-one"}).splitlines()
    assert before[0] == after[0] == testimony.table_line(table)
    assert "1 of 2 memories classified" in after[1]
    assert after[2] == "  unclassified (1): a-new-one"


def test_a_row_that_points_at_nothing_is_refused(tmp_path):
    table = [("a-memory-that-is-not-there", "session", "nothing")]
    assert testimony.faults(table, set()) == [
        "row names a memory that is not there: a-memory-that-is-not-there"]
    assert testimony.faults([("x", "vibes", "")], {"x"}) == [
        "x: kind `vibes` is not one of harness, henri, session, argument"]


def test_the_command_runs_and_checks():
    out = subprocess.run([sys.executable, str(TOOL), "--check"],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stdout + out.stderr
    assert out.stdout.startswith("testimony: ")
