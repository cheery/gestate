"""tools/seedaudit.py — the audit, and the two harvesters inside it.

Both of this file's subjects failed on their first run, in the way
`card:dangling-names.md` warns about: the detector was fine and the
*harvester* was wrong, so the report looked plausible and said the
opposite of the truth.  These tests pin the two bugs.
"""

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("seedaudit", ROOT / "tools" / "seedaudit.py")
seedaudit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seedaudit)


def test_a_tool_does_not_back_itself(tmp_path):
    """The first bug.  `backed_by` searched `tools/` as well, so every
    tool contained its own name and all nine pieces scored ok — the
    audit's whole finding, inverted, by a one-word search path."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "andon.sh").write_text("# tools/andon.sh\n")
    (tmp_path / "test").mkdir()
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh") is None


def test_a_test_does_back_it(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "andon.sh").write_text("x")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "test_andon.py").write_text("run('tools/andon.sh')\n")
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh") == "test/test_andon.py"


def test_only_files_named_test_are_searched(tmp_path):
    """A helper under test/ is not a gate."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "andon.sh").write_text("x")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "conftest.py").write_text("tools/andon.sh\n")
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh") is None


def test_a_bare_basename_is_resolved_before_it_is_called_missing(tmp_path):
    """The second bug.  The documents write `test_board.py` and
    `dialoglag.py` without their directories, and the first run reported
    thirteen unkept promises that were all present on disk."""
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text("see `test_board.py` and `later/`\n")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "test_board.py").write_text("x")
    (tmp_path / "board" / "later").mkdir()
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("nothing cited\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    assert seedaudit.audit_promises(tmp_path) == {}


def test_a_promise_that_is_really_missing_is_reported(tmp_path):
    """The check has to keep working after being taught to resolve."""
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("x\n")
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text("run `tools/andon.sh` to reach me\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    assert "tools/andon.sh" in seedaudit.audit_promises(tmp_path)


def test_a_placeholder_is_not_a_promise(tmp_path):
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("x\n")
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text("archived as `journal/YYYY-MM.md`\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    assert seedaudit.audit_promises(tmp_path) == {}


def test_this_tree_has_every_piece_present():
    """The people-pieces are the audit's subject; if one goes missing
    here, that is the finding, not a broken test."""
    rows = seedaudit.audit_pieces(ROOT)
    assert [r["name"] for r in rows if r["missing"]] == []


def test_nothing_is_unbacked():
    """This was a canary and is now a gate.

    It was written on 2026-08-22 asserting the two pieces that had no
    test — the andon and the sitting limit — precisely so it would fail
    when they gained one.  It did, the same morning, and this is the
    other side of that: from here a piece added to `PIECES` without a
    test fails the suite, which is the ratchet the audit's second half
    is about.

    It also caught the audit's third harvester bug on the way through.
    A test that fails on good news is easy to argue away; this is the
    case for keeping one."""
    rows = seedaudit.audit_pieces(ROOT)
    unbacked = sorted(r["name"] for r in rows if not r["missing"] and not r["backing"])
    assert unbacked == [], unbacked
