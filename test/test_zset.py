"""`tools/zset.py` — the picture by its changes, `card:gui-is-difficult.md`.

The tool's number is a timing and is not held here; what is held is the
verdict it rests on, on four rows small enough to read: a picture whose
items carry the note's key is assembled exactly from the changes, and
one whose items do not loses a rectangle the moment one of two notes
drawing it moves — DBSP's `distinct` caveat, which the page of
`arcnotes.ges` meets at note 19.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import zset  # noqa: E402

#: Two notes drawing the same rectangle — a unison across voices — and
#: two that draw their own.
ROWS = [(1, 40, 100, 10, 0, 0, 0), (2, 40, 100, 10, 0, 0, 0),
        (3, 52, 91, 10, 0, 0, 0), (4, 64, 82, 10, 0, 0, 0)]


def test_a_keyed_picture_is_assembled_exactly_from_its_changes():
    for which in range(len(ROWS)):
        assert zset.measure(ROWS, which)["keyed"]["agree"], which


def test_an_unkeyed_picture_loses_what_a_second_note_still_draws():
    assert zset.sharing(ROWS) == [0, 1]
    m = zset.measure(ROWS, 0)["unkeyed"]
    assert not m["agree"]
    assert m["lost"] == [(40, 100, 10, 0)]
    assert zset.measure(ROWS, 2)["unkeyed"]["agree"], "a note sharing nothing moves cleanly"
