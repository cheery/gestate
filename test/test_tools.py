"""The three questions an editor asks — `python -m gestate.typecheck`.

Each is about the program *as compiled*: the type comes from inference and
the position from the parser, so neither can drift from what the compiler
thinks.  A tool that read the text instead would be a second opinion, and
the second opinion is the one that goes stale.

    --query NAME   what it is, where it says so, and the prose above it
    --holes        every `_`, its type, and its line:column
    --fits TYPE    what in scope could stand where that type is wanted

They are three tools rather than one on purpose.  "What goes here" is a
question about a *type*, and a version of it that only worked inside a `_`
would be one you had to prepare for.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate.typecheck import main

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

PROGRAM = """#: How many of each, and what they cost.
#:
#: The price is in whole cents, because money in floats is how a total
#: comes out at 9.999999.
Order := Order Int Int

#: What one order comes to.
total : Order -> Int
total o = case o of
    Order n each -> n * each

main : Int
main = total (Order 3 250)
"""


def _run(tmp_path, source: str, *argv) -> tuple[int, str, str]:
    import io
    import sys

    path = tmp_path / "q.ges"
    path.write_text(source)
    out, err = io.StringIO(), io.StringIO()
    stdout, stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main([str(path), *argv])
    finally:
        sys.stdout, sys.stderr = stdout, stderr
    return code, out.getvalue(), err.getvalue()


# ── --query ─────────────────────────────────────────────────────────────────


def test_query_answers_with_the_type_the_place_and_the_prose(tmp_path):
    code, out, _ = _run(tmp_path, PROGRAM, "--query", "total")
    assert code == 0
    # **With the name the definition gave its argument.**  The types are
    # what a compiler knows and the names are what a reader needs; four
    # filters in `synth.ges` carry the same three `Sig Float`s and the
    # first means hertz in one and a coefficient in its neighbour
    # (`board/done/argument-names.md`).
    assert out.splitlines()[0] == "total o : Order -> Int"
    assert "at: line 8 (declaration)" in out
    assert "What one order comes to." in out


def test_query_answers_for_a_name_whose_author_wrote_its_type(tmp_path):
    """The interleaved view leaves those alone; a *question* must not.

    `--sigs` prints inferred signatures beside source that already shows
    the written ones, so a written one is deliberately absent there — and
    that absence used to make `--sig main` say there was no such name.
    """
    code, out, _ = _run(tmp_path, PROGRAM, "--sig", "main")
    assert code == 0 and out.strip() == "main : Int"


def test_query_reaches_a_constructor(tmp_path):
    """Hovering `Order` is hovering a name in the same text."""
    code, out, _ = _run(tmp_path, PROGRAM, "--query", "Order")
    assert code == 0
    assert out.splitlines()[0] == "Order : Int -> Int -> Order"
    assert "type declaration" in out
    assert "money in floats" in out, "the prose above the declaration"


def test_query_stops_at_a_blank_line(tmp_path):
    """A comment separated from a declaration is about something else."""
    source = ("# About the file, not about `x`.\n"
              "\n"
              "#: About `x`.\n"
              "x : Int\nx = 1\n"
              "\nmain : Int\nmain = x\n")
    _code, out, _ = _run(tmp_path, source, "--query", "x")
    assert "About `x`." in out
    assert "About the file" not in out


def test_query_says_when_there_is_no_such_name(tmp_path):
    code, _out, err = _run(tmp_path, PROGRAM, "--query", "nope")
    assert code == 1 and "no declaration named" in err


# ── --holes ─────────────────────────────────────────────────────────────────


def test_a_hole_is_typed_by_what_is_wanted_of_it(tmp_path):
    source = PROGRAM.replace("main = total (Order 3 250)",
                             "main = total (Order 3 _)")
    code, out, _ = _run(tmp_path, source, "--holes")
    assert code == 0
    assert out.splitlines()[0].endswith("_ : Int   (in main)")


def test_a_hole_is_reported_where_it_is(tmp_path):
    """Line and column, because the caller is an editor.

    1-based lines and 0-based columns — a text widget's convention, and
    the one `audiospans` already reports in.
    """
    source = "main : Int\nmain = 1 + _\n"
    _code, out, _ = _run(tmp_path, source, "--holes")
    line, col, rest = out.split(":", 2)
    assert (int(line), int(col)) == (2, 11)
    assert rest.strip().startswith("_ : Int")
    assert "main = 1 + _" in out, "the line itself, to show in place"


def test_several_holes_come_back_in_reading_order(tmp_path):
    source = ("f : Int -> Int -> Int\nf a b = a\n"
              "\nmain : Int\nmain = f _ (f _ 2)\n")
    _code, out, _ = _run(tmp_path, source, "--holes")
    places = [l.split(":")[0] for l in out.splitlines() if l[:1].isdigit()]
    assert places == ["5", "5"]
    assert out.count("_ : Int") == 2


def test_a_program_with_no_holes_says_so(tmp_path):
    code, out, _ = _run(tmp_path, PROGRAM, "--holes")
    assert code == 0 and out.strip() == "no holes"


def test_a_hole_type_checks_and_does_not_run(tmp_path):
    """Which is the whole point of having one.

    The evaluator refuses it by name and by position, because the
    alternative is an unknown-node crash from a program whose author knows
    exactly what is missing.  The position is in the compiler's own 0-based
    coordinates and in the `(at line:col)` form, so that
    `audiospans.in_source` puts it back in the file the author is looking
    at rather than in an assembly they never wrote.
    """
    from gestate.gmachine import GmError
    from gestate.pipeline import evaluate

    with pytest.raises(GmError, match=r"hole \(`_`\) \(at 1:7\)"):
        evaluate("main : Float\nmain = _\n")


def test_a_hole_stops_what_reaches_it_and_nothing_else(tmp_path):
    """A hole is an *absent declaration*, not a broken program.

    It used to be refused when the code around it was compiled, which took
    the whole program with it: one unfinished definition and a file's synth
    would not start, its score would not load and its canvas would not
    build — none of which had anything to do with the hole.  Compiled to an
    instruction that aborts when it is reached, everything that does not
    reach it runs.
    """
    from gestate.gmachine import GmError
    from gestate.pipeline import evaluate

    source = ("unfinished : Int\nunfinished = _\n"
              "\nmain : Int\nmain = 1 + 2\n")
    assert evaluate(source) == "3"
    with pytest.raises(GmError, match=r"hole"):
        evaluate(source.replace("main = 1 + 2", "main = unfinished"))


def test_a_wildcard_pattern_is_still_a_wildcard(tmp_path):
    """`_` on the left of `=` binds nothing; only an expression is a hole."""
    code, out, _ = _run(tmp_path,
                        "f : Int -> Int\nf _ = 1\n"
                        "\nmain : Int\nmain = f 2\n", "--holes")
    assert code == 0 and out.strip() == "no holes"


# ── --fits ──────────────────────────────────────────────────────────────────


def test_fits_finds_what_produces_the_type(tmp_path):
    code, out, _ = _run(tmp_path, PROGRAM, "--fits", "Order -> Int")
    assert code == 0
    assert "total : Order -> Int" in out


def test_fits_says_how_many_arguments_are_needed(tmp_path):
    code, out, _ = _run(tmp_path, PROGRAM, "--fits", "Int")
    assert code == 0
    assert "total : Order -> Int   (after 1 argument)" in out


def test_fits_leaves_out_what_fits_everything(tmp_path):
    """`id`, `const` and `(@)` unify with any question asked.

    Listing them is listing the prelude in a different order, so the test
    is where the two types run out of arrows together: a candidate that
    ends in a variable there fits by being unconstrained, not by being
    right.
    """
    _code, out, _ = _run(tmp_path, PROGRAM, "--fits", "Order -> Int")
    for junk in ("id :", "const :", "@ :", "flip :"):
        assert junk not in out, out


def test_fits_reports_an_unreadable_type_rather_than_failing(tmp_path):
    code, _out, err = _run(tmp_path, PROGRAM, "--fits", "Order ->")
    assert code == 1 and "could not read the type" in err


# ── …on a synth, which is what the editor opens ─────────────────────────────


def _synth(tmp_path, name: str = "polysine.ges") -> str:
    return (AUDIO_DIR / name).read_text()


def test_query_reaches_the_prose_in_the_audio_prelude(tmp_path):
    """`--audio` puts `signal.ges`, `audio.ges` and `synth.ges` in front.

    Hovering `adsr` should reach the paragraph above it rather than
    come back with a type and a shrug — that paragraph is where the
    library says what it means.
    """
    code, out, _ = _run(tmp_path, _synth(tmp_path), "--audio",
                        "--query", "adsr")
    assert code == 0
    # The names come out of the prelude the query reached into, which is
    # the half a reader cannot see at all from their own file.
    assert out.splitlines()[0] == "adsr e g : Adsr -> Sig Gate -> Sig Float"
    assert "synth.ges line" in out
    assert "envelope" in out


def test_a_hole_in_a_synth_is_placed_in_the_authors_file(tmp_path):
    """The assembly puts three preludes in front; the line does not move.

    Without taking the offset back off, every position an editor was given
    would be a few hundred lines past the end of the file it is showing.
    """
    source = _synth(tmp_path).replace("* adsr env g *", "* _ *")
    code, out, _ = _run(tmp_path, source, "--audio", "--holes")
    assert code == 0
    line = int(out.split(":")[0])
    assert source.splitlines()[line - 1].lstrip().startswith("sineVoice g s =")
    assert "_ : Sig Float" in out


def test_fits_a_signal_type(tmp_path):
    code, out, _ = _run(tmp_path, _synth(tmp_path), "--audio",
                        "--fits", "Sig Gate -> Sig Float")
    assert code == 0
    assert "adsr : Adsr -> Sig Gate -> Sig Float" in out
    assert "perc : Float -> Sig Gate -> Sig Float" in out
