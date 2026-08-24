"""Who asked for each tool — the register, and the gate under it.

`tools/asked.py` is the instrument; this file is what makes it true.
The design argument lives in that docstring and in `card:who-asked.md`;
the short version is that a register of *questions from outside* cannot
be gated, because nothing can enumerate that set — and `tools/` can.

**What is refused here is silence, not a particular answer.**  `a
session` and `unrecorded` are legal stamps.  A gate accepting only
"somebody asked" would teach every future session to write "Henri
asked" and mean nothing by it, which is the failure `board/README.md`
names for a card stating a fix in place of a problem.

**The board already had half of this.**  Every card carries an `asked`
line and `test_board.py` refuses one without it.  What had no equivalent
was the other artifact a want produces — the tool — which is why
`driven.py` and `limit.sh` can each name the card that holds their
words, and why a tool built with no card was until today the one thing
here that could arrive from nowhere.
"""

import datetime
import importlib.util
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "asked", ROOT / "tools" / "asked.py")
asked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asked)

#: **The ratchet.**  `unrecorded` is honest and it is not free: left
#: ungated it becomes what every hurried session reaches for.  So the
#: count is written down, exactly as `fixme.md`'s header writes down how
#: many of its entries are resolved, and moving it costs an edit
#: somebody has to justify.  It may fall.  It may not rise.
UNRECORDED = 5  # 11 on 2026-08-23; six dug out of the record on 2026-08-24


@pytest.mark.parametrize("path", asked.tools(), ids=lambda p: p.name)
def test_every_tool_says_who_asked_for_it(path):
    """One `#: asked-by:` line, in the first forty, from a closed set.

    The roster half is the glob: a tool added tomorrow is in this
    parametrisation tomorrow and fails until somebody says where it came
    from.  Same shape as `test_every_audio_example_is_exercised_here`,
    and it is the only shape on this board that has held — a list typed
    by hand forgets the file just added.

    **Recoverable now, unrecoverable later.**  Who wanted a tool is
    plain on the day it is written and is a journal dig a fortnight
    after, which is why it is checked at the file rather than swept into
    a document periodically.
    """
    found = asked.stamp(path)
    assert found is not None, (
        f"{path.relative_to(ROOT)} does not say who asked for it.  Add one "
        f"line in the first {asked.WINDOW}:\n"
        "  #: asked-by: <who>, <YYYY-MM-DD> - <the words, or card:<name>.md>\n"
        f"where <who> is one of: {', '.join(asked.WHO)}.  "
        "`a session` and `unrecorded` are legal; silence is not.  "
        "See tools/asked.py and card:who-asked.md.")


@pytest.mark.parametrize("path", asked.tools(), ids=lambda p: p.name)
def test_a_persons_ask_carries_the_words_they_used(path):
    """`Henri` and `outside` must quote, or name the card that quotes.

    A person's ask paraphrased is a person's ask lost: this tree's rule
    is that his Finnish is quoted verbatim wherever the wording does the
    work, and a stamp reading *"Henri wanted a coverage tool"* would
    throw away the only part telling the next reader what he actually
    cared about.

    **A `card:` citation is the other legal form**, and is better where
    it applies: the card already carries the words under a gate of its
    own, and a quote copied into a second place is a quote that can rot
    in one of them.  `a session` and `the tree` are exempt — neither has
    words to quote.
    """
    found = asked.stamp(path)
    if found is None or found[0] not in asked.QUOTED:
        pytest.skip("no person's ask on this one")
    who, _, rest = found
    assert '"' in rest or "card:" in rest, (
        f"{path.relative_to(ROOT)} says `{who}` asked and does not say what "
        "they said.  Quote them, or cite the `card:` that does — the words "
        "are the part that keeps.")


@pytest.mark.parametrize("path", asked.tools(), ids=lambda p: p.name)
def test_a_cited_card_is_a_card_that_exists(path):
    """The citation has to land, or it is a quote that was never written.

    `test_citations.py` already refuses a `§"…"` pointing at a heading
    that no longer exists, *because three had rotted silently before
    anything checked*.  A `card:` on a stamp is the same hazard in a
    newer place: the escape hatch from quoting is only honest while the
    thing it points at is real.
    """
    found = asked.stamp(path)
    if found is None:
        pytest.skip("unstamped; the first test names it")
    for name in re.findall(r"card:([\w-]+\.md)", found[2]):
        assert (ROOT / "board" / name).exists() or \
               (ROOT / "board" / "done" / name).exists() or \
               (ROOT / "board" / "later" / name).exists(), (
            f"{path.relative_to(ROOT)} cites card:{name}, which is on no "
            "shelf of the board.")


def test_a_stamp_names_a_day_that_has_happened():
    """A date, and not a placeholder or a typo for next year.

    Cheap, and it catches the two ways this field goes wrong: a stamp
    copied from another file keeps that file's date, and a hand-typed
    year is wrong every January.
    """
    today = datetime.date.today()
    wrong = []
    for name, found in asked.register().items():
        if found is None:
            continue
        when = datetime.date.fromisoformat(found[1])
        if when > today or when < datetime.date(2026, 8, 8):
            wrong.append(f"{name}: {found[1]}")
    assert not wrong, (
        "a stamp dated outside this project's life (it began 2026-08-08):\n  "
        + "\n  ".join(wrong))


def test_the_unrecorded_ones_are_counted_and_may_only_fall():
    """The ratchet, and the reason the gate is not a formality.

    Every tool could be stamped `unrecorded` in ten minutes and the two
    tests above would still pass — so the honest half of this gate is
    the number.  It is written here, it is checked, and it falls only
    when somebody does the dig for one more tool.

    *`card:who-asked.md` holds which ones are still owed.*
    """
    n = sum(1 for f in asked.register().values()
            if f is not None and f[0] == "unrecorded")
    assert n <= UNRECORDED, (
        f"{n} tools say `unrecorded`, and this file allows {UNRECORDED}.  "
        "A new tool's provenance is known on the day it is written; "
        "`unrecorded` is for the ones written before this gate existed.")
    assert n == UNRECORDED, (
        f"{n} tools say `unrecorded` and this file still says "
        f"{UNRECORDED} — good news, and the number comes down with it or "
        "the ratchet stops holding.")


def test_the_register_is_a_command_somebody_can_run(capsys):
    """`python tools/asked.py` prints it, grouped, with the totals.

    A measurement living only inside a test is a measurement nobody
    looks at, and the distribution — how much of this bench came from
    outside pressure, how much from Henri, how much from a session on
    its own initiative — is the finding this gate exists to expose.
    """
    rc = asked.main([])
    said = capsys.readouterr().out
    assert rc == 0, "some tool is unstamped; the test above names it"
    assert re.search(r"\d+ tools, \d+ unrecorded, \d+ unstamped", said)


@pytest.mark.parametrize("path", asked.tools(), ids=lambda p: p.name)
def test_a_script_with_a_shebang_can_still_be_run(path):
    """A tool that loses its executable bit is a tool that stops working.

    **This lives here because stamping is what took it away.**  Adding
    the `asked-by` line to twenty-six files in one pass rewrote each
    through `head`/`tail`/`mv`, which does not carry the mode — and
    `tools/sandbox.sh` came back `rw-`, so the next `suite.py --gates`
    died with `PermissionError` before a single gate ran.  Nothing in
    the suite would have said why; what caught it was `git diff
    --summary` printing fourteen mode changes nobody asked for.

    A defect is a caller, and the call is cheap: a shebang is a promise
    that the file is run, not sourced.
    """
    if not path.read_text().startswith("#!"):
        pytest.skip("not run directly")
    import os
    assert os.access(path, os.X_OK), (
        f"{path.relative_to(ROOT)} starts with a shebang and is not "
        "executable — `chmod +x` it.  A rewrite through a temporary file "
        "drops the mode; `git diff --summary` is where that shows.")


def test_needed_by_is_computed_from_who_names_the_tool(tmp_path):
    """Henri, 2026-08-24: who-asked and needed-by, so that we get a
    graph.  The second axis is derived, never stamped."""
    (tmp_path / "tools").mkdir(); (tmp_path / "test").mkdir()
    (tmp_path / "doc").mkdir(); (tmp_path / "board").mkdir()
    (tmp_path / "tools" / "x.py").write_text("# tools/x.py names itself\n")
    (tmp_path / "tools" / "y.py").write_text("# calls x.py\n")
    (tmp_path / "test" / "test_x.py").write_text("run('tools/x.py')\n")
    (tmp_path / "test" / "test_provenance.py").write_text("x.py y.py\n")
    (tmp_path / "board" / "c.md").write_text("`x.py` was wanted here\n")
    needs = asked.needed_by("tools/x.py", tmp_path)
    assert needs["test"] == ["test/test_x.py"], "the provenance test does not count"
    assert needs["tools"] == ["tools/y.py"], "a tool never names itself"
    assert needs["cards"] == [str(pathlib.PurePosixPath("board") / "c.md")]
    assert needs["doc"] == []


def test_the_four_quadrants():
    none = {"test": [], "doc": [], "tools": [], "cards": [str(pathlib.PurePosixPath("board") / "c.md")]}
    some = {"test": ["test/test_x.py"], "doc": [], "tools": [], "cards": []}
    henri = ("Henri", "2026-08-24", "words")
    sess = ("a session", "2026-08-24", "")
    assert asked.quadrant(henri, some) == "asked, needed"
    assert asked.quadrant(henri, none) == "asked, not needed"
    assert asked.quadrant(sess, some) == "not asked, needed"
    assert asked.quadrant(("unrecorded", "2026-08-11", ""), none) == "neither"
    assert asked.quadrant(None, none) == "neither"
    assert asked.quadrant(henri, none) != "asked, needed", "a card alone is wanting, not need"


def test_the_graph_is_a_command_and_a_picture(capsys):
    assert asked.main(["--graph"]) == 0
    out = capsys.readouterr().out
    assert "asked, needed" in out and "asked:" in out
    assert asked.main(["--dot"]) == 0
    d = capsys.readouterr().out
    assert d.startswith("digraph") and d.rstrip().endswith("}")
    assert '"tools/asked.py"' in d


def test_the_svg_is_laid_out_by_dot(tmp_path):
    import shutil
    if shutil.which("dot") is None:
        pytest.skip("no graphviz on this machine — --svg refuses out loud instead")
    out = tmp_path / "asked.svg"
    assert asked.main(["--svg", str(out)]) == 0
    text = out.read_text()
    assert "<svg" in text and "tools/asked.py" in text
    assert text.count("<g id=\"node") >= 32, "every tool is a node"
