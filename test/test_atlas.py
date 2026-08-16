"""The atlas says what the tree is — `gestate/atlas.py`.

A picture is believed longer than prose is, and nothing about a drawing
says how old it is.  So the sheet in `doc/atlas/` is generated, and this
file is the reason that is worth anything: it fails when a module has no
place on the page, when the page names something that is gone, when an
arrow has outlived the call behind it, and when the committed sheet is
not what today's source renders.

Same shape as `test_reference.py`'s guarantee over `doc/ref/`, and the
same sentence when it breaks: **run `python -m gestate.atlas`.**
"""

from __future__ import annotations

from pathlib import Path

from gestate import atlas

ROOT = Path(__file__).resolve().parent.parent


def test_every_module_has_a_lane():
    """**A module nobody placed is a module missing from the picture.**

    Which is the drift this whole arrangement exists to prevent, so it
    is a failure rather than a silent omission — and it names the file,
    because the answer is one line in `atlas.WHERE`.
    """
    missing = atlas.unplaced(ROOT)
    assert missing == [], (
        "these modules have no lane — give each one a line in "
        "`gestate/atlas.py`'s WHERE: " + ", ".join(missing))


def test_no_lane_names_a_module_that_is_gone():
    """The other direction, which is how a deleted module leaves the
    page rather than lingering on it as a box with nothing behind it."""
    gone = atlas.phantom(ROOT)
    assert gone == [], (
        "WHERE names modules that no longer exist: " + ", ".join(gone))


def test_every_drawn_arrow_has_something_behind_it():
    """**An arrow is a claim.**  Each one names the import that makes it
    true — or, for the one crossing that is not a Python call, the file
    that does — and a claim nothing supports is worse on a picture than
    in prose, because nobody re-reads a picture sceptically."""
    loose = atlas.unproven(ROOT)
    assert loose == [], (
        "these arrows have nothing behind them any more: "
        + "; ".join(loose))


def test_the_libraries_and_crates_it_names_are_there():
    """The `.ges` libraries and the Rust crates are drawn from a written
    list — the one place the sheet says something the import graph
    cannot — so the list is checked against the tree."""
    gone = atlas.missing_files(ROOT)
    assert gone == [], "the atlas names files that are not there: " + \
        ", ".join(gone)


def test_the_sheet_is_not_behind_the_source():
    """**The whole guarantee.**  A generated picture nothing checks
    drifts exactly as fast as a hand-drawn one; this is what stops it.

    If this fails, run `python -m gestate.atlas`.
    """
    behind = atlas.stale(ROOT)
    assert behind == [], (
        "doc/atlas/ is out of date — run `python -m gestate.atlas`: "
        + ", ".join(behind))


def test_rendering_twice_says_the_same_thing():
    """**Deterministic, or the regeneration is noise.**  A sheet that
    changes when nothing changed makes every commit carry a diff nobody
    can read, and people stop regenerating it — which is exactly the
    drift again, arrived at from the other side."""
    assert atlas.render(ROOT) == atlas.render(ROOT)


def test_the_sheet_is_an_a3_page():
    """It is meant to be printed and put on a wall, so the size is part
    of what it is: 420×297 mm, in millimetres rather than pixels."""
    svg = (ROOT / "doc" / "atlas" / "whole.svg").read_text()
    assert 'width="420mm"' in svg and 'height="297mm"' in svg
    assert svg.count("<svg") == 1
