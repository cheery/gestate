"""tools/covercount.py — the numerator, the denominator, and the floor.

The tool answers *which lines of `gestate/` has the suite never run*, and
it is the kind of instrument that fails quietly: a denominator counted
one way and a numerator collected another disagree by a few per cent and
nobody notices, because both numbers still look like coverage.  So what
is tested here is the agreement between them, and the honesty of the
page — **not** the coverage of anything, which is a claim about one
machine and belongs in `test/coverage.md` where it is regenerated.

`spec/verification.md` §"Coverage, and the question it cannot answer" is
why the blind spot is asserted rather than merely documented: a floor
read as a verdict is the way this instrument gets misused.
"""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "covercount", ROOT / "tools" / "covercount.py")
covercount = importlib.util.module_from_spec(spec)
spec.loader.exec_module(covercount)


def test_the_denominator_is_what_the_interpreter_would_report(tmp_path):
    """`executable()` compiles and walks, rather than counting lines that
    look like code.

    The distinction is the whole correctness of the ratio: a blank line,
    a comment, a docstring's continuation and a bare `else:` never fire a
    LINE event, so counting them would inflate the denominator and report
    a permanent shortfall no test could ever close.  Nested functions,
    conversely, *do* fire and live in `co_consts` — missed, they deflate
    it."""
    f = tmp_path / "sample.py"
    f.write_text(
        "# a comment\n"                 # 1  — never fires
        "\n"                            # 2  — never fires
        "def outer():\n"                # 3  — fires (the def)
        "    '''doc'''\n"               # 4  — the docstring is not a line event
        "    def inner():\n"            # 5  — fires, and is nested
        "        return 1\n"            # 6  — fires, inside the nest
        "    return inner\n"            # 7  — fires
    )
    assert covercount.executable(f) == {3, 5, 6, 7}


def test_a_file_that_will_not_compile_is_counted_as_nothing(tmp_path):
    """A syntax error in the package must not take the run down.

    `gestate/` is where somebody is mid-edit; a measurement that raises
    on a half-written file is a measurement nobody runs while working."""
    f = tmp_path / "broken.py"
    f.write_text("def (:\n")
    assert covercount.executable(f) == set()


def test_only_the_package_is_recorded_and_every_line_retires():
    """The callback's two contracts.

    It records `gestate/` and nothing else — a run that counted pytest's
    own lines would have a denominator from one project and a numerator
    from two.  And it returns `DISABLE` **unconditionally**, including
    for the lines it just recorded: that is what makes the tool cost one
    event per line rather than one per execution, and it is the reason a
    full suite under it is minutes slower rather than hours."""
    covercount.SEEN.clear()
    covercount.OURS.clear()

    ours = compile("x = 1\n", str(covercount.PACKAGE / "made_up.py"), "exec")
    theirs = compile("x = 1\n", "/elsewhere/other.py", "exec")

    import sys
    assert covercount._line(ours, 1) is sys.monitoring.DISABLE
    assert covercount._line(theirs, 1) is sys.monitoring.DISABLE

    assert covercount.SEEN == {str(covercount.PACKAGE / "made_up.py"): {1}}

    covercount.SEEN.clear()
    covercount.OURS.clear()


def test_the_page_names_its_blind_spot(tmp_path, monkeypatch):
    """**The floor has to be on the page, not only in the docstring.**

    A test that shells out runs in a child this monitor never enters, so
    its lines come back uncovered though they ran.  A page that printed
    a percentage without saying which way its error points would be read
    as a verdict, and the percentage is the half people quote."""
    monkeypatch.setattr(covercount, "PAGE", tmp_path / "coverage.md")
    covercount.draw([("gestate/x.py", 3, 4)], 4, 3, ["-m", "not golden"],
                    12.0, 0, ["test/test_shells.py"])
    page = (tmp_path / "coverage.md").read_text()

    assert "floor, not a verdict" in page
    assert "test/test_shells.py" in page
    assert "75%" in page and "75.0%" in page


def test_the_files_that_shell_out_are_found_by_reading_them():
    """The blind spot is a real list, not a placeholder.

    If this ever returns nothing, the detection broke rather than the
    tree stopped shelling out — `tools/jukebox.py`'s whole design is one
    subprocess per track, and the suite drives `audioperform` the same
    way."""
    blind = covercount.shells_out()
    assert blind, "no test file reads as shelling out; the detection broke"
    assert all(b.startswith("test/") for b in blind)
