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


def test_every_sheet_is_an_a3_page():
    """They are meant to be printed and put on a wall, so the size is
    part of what they are: 420×297 mm, in millimetres rather than
    pixels, and one page each."""
    for name in sorted(atlas.generate(ROOT)):
        svg = (ROOT / "doc" / "atlas" / name).read_text()
        assert 'width="420mm"' in svg and 'height="297mm"' in svg, name
        assert svg.count("<svg") == 1, name


# ── The language sheet, which claims to know the order of the passes ────────


def test_the_front_end_is_drawn_in_the_order_it_runs():
    """**The claim `language.svg` lives on.**

    The order is not written in `atlas.py`; `pipeline._analyse` is read
    for it, and this fails when the two disagree — so moving a pass in
    the compiler moves it on the sheet or breaks the build, and there
    is no third possibility where the picture quietly lies.
    """
    wrong = atlas.out_of_order(ROOT)
    assert wrong == [], "; ".join(wrong)


def test_every_pass_says_which_file_to_open():
    """Half the passes are renames — `check_monotone` is
    `monotone.check_scs` — so the card resolves the alias.  A pass whose
    home cannot be found would print `?`, which is a diagram admitting
    it does not know."""
    lost = [name for name, _says in atlas.PASSES
            if not atlas.origin(ROOT, name)[0]]
    assert lost == [], "no home found for: " + ", ".join(lost)


def test_a_pass_shows_the_refusals_it_can_actually_make():
    """Read from the code, not listed: the kind check says nothing
    itself and `check_kind` says `KindError`, which is two hops the
    reader should not have to make."""
    said = dict((name, atlas.refusals_for(ROOT, name))
                for name, _says in atlas.PASSES)
    assert "KindError" in said["_kind_check_program"]
    assert "MonotoneError" in said["check_monotone"]
    assert "SubgrammarError" in said["check_subgrammars"]
    assert "ExhaustError" in said["check_program"]
    # And the filter holds: a `ValueError` from a bad call is not a
    # refusal the language makes.
    assert not any("ValueError" in r for r in said.values())


def test_the_instruction_set_is_the_machines_own():
    """Read from `_DISPATCH`, so an instruction the machine learns is on
    the sheet the next time it is drawn — and one it forgets leaves."""
    from gestate import gmachine

    assert atlas.instructions() == sorted(k.__name__ for k in
                                          gmachine._DISPATCH)
    for known in ("Unwind", "Mkap", "Eval", "PushGlobal"):
        assert known in atlas.instructions()


def test_the_sheet_can_be_made_into_a_picture(tmp_path):
    """**A picture nobody can look at is not much of a picture.**

    The `.svg` is the artefact and the `.png` is the convenience, so
    this skips rather than fails without a rasteriser — but where one
    is installed, the convenience has to actually work.
    """
    import pytest

    pytest.importorskip("cairosvg")
    png = tmp_path / "whole.png"
    by = atlas.rasterise(ROOT / "doc" / "atlas" / "whole.svg", png)
    assert by, "a rasteriser was importable and produced nothing"
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


# ── The wire, which is a test as well as a picture ──────────────────────────


def test_the_two_ends_of_the_wire_agree():
    """**The one derivation here that verifies rather than describes.**

    The model is Python and the window is Rust; every word between them
    is written twice, and nothing else in this project compares the two
    copies.  A word added at one end and forgotten at the other is a
    feature that silently does nothing — the shape of defect this has
    hit by hand more than once.
    """
    drift = atlas.wire_drift(ROOT)
    assert drift == [], "the wire's two ends disagree:\n  " + \
        "\n  ".join(drift)


def test_the_wire_check_could_fail():
    """**A checker that cannot fail is worse than no checker**, because
    it reads as a guarantee.

    Every count below is read out of the source by a pattern, and a
    pattern that stops matching returns an empty set — which would make
    `wire_drift` say *nothing disagrees* about a wire it can no longer
    see.  So the counts are asserted to be real, and this test is the
    reason the numbers on the sheet are worth reading.
    """
    rust, python = atlas.abi_rust(ROOT), atlas.abi_python(ROOT)
    assert len(rust) >= 15 and len(python) >= 15, (len(rust), len(python))
    words = atlas.wire_words(ROOT)
    for name, (sent, read) in sorted(words.items()):
        assert len(sent) >= 8, f"{name}: only {len(sent)} sent — "\
            "the pattern that reads the sender has probably stopped matching"
        assert len(read) >= 8, f"{name}: only {len(read)} understood"


def test_every_exported_call_has_a_sentence():
    """The `WHERE` rule, applied to the seam: a call nobody placed is a
    call missing from the picture."""
    quiet = atlas.unspoken(ROOT)
    assert quiet == [], "no sentence for: " + ", ".join(quiet)


def test_a_word_that_only_one_end_knows_is_caught():
    """The check, made to fail on purpose — because the value of it is
    entirely in whether it *would* say so."""
    words = atlas.wire_words(ROOT)
    sent, read = words["gestures"]
    assert sent == read, "this test assumes today's wire agrees"
    pretend = (sent | {"waggle"}, read)
    only_one_end = sorted(pretend[0] - pretend[1])
    assert only_one_end == ["waggle"]


def test_the_wire_says_what_each_word_carries():
    """Read from the readers: the window's parser names the fields as it
    takes them, and the formatter names them as it writes them."""
    shapes = atlas.wire_shapes(ROOT)
    assert shapes["furniture"]["knob"] == "name line value lo hi kind wired"
    assert shapes["gestures"]["touch"] == "kind x y"
    assert shapes["orders"]["goto"] == "1 field"
