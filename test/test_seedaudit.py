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
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh", "tools/andon.sh") is None


def test_a_test_does_back_it(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "andon.sh").write_text("x")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "test_andon.py").write_text("run('tools/andon.sh')\n")
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh", "test/test_andon.py") == "test/test_andon.py"


def test_a_mention_in_some_other_test_is_not_a_gate(tmp_path):
    """The fourth harvester bug, found by `tools/seedmutate.sh` on
    2026-08-24: `backed_by` searched every test file, so deleting the
    test behind a piece left it green whenever another test cited the
    path.  Only the declared gate counts now."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "limit.sh").write_text("x")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "test_provenance.py").write_text("# see tools/limit.sh\n")
    assert seedaudit.backed_by(tmp_path, "tools/limit.sh", "test/test_limit.py") is None


def test_only_files_named_test_are_searched(tmp_path):
    """A helper under test/ is not a gate."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "andon.sh").write_text("x")
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "conftest.py").write_text("tools/andon.sh\n")
    assert seedaudit.backed_by(tmp_path, "tools/andon.sh", "test/conftest.py") is None


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
    assert seedaudit.audit_promises(tmp_path) == ({}, {})


def test_a_promise_that_is_really_missing_is_reported(tmp_path):
    """The check has to keep working after being taught to resolve."""
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("x\n")
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text("run `tools/andon.sh` to reach me\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    broken, unbuilt = seedaudit.audit_promises(tmp_path)
    assert "tools/andon.sh" in broken and unbuilt == {}


def test_a_missing_promise_the_tree_ignores_is_unbuilt_not_broken(tmp_path):
    """Finding one of the 2026-08-24 mutation run: a `git archive` of
    HEAD was red on five promises that were generated pages and build
    output.  `.gitignore`'s own rule — ignore what a command can make
    again — is the distinction, and the audit reads it now."""
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("x\n")
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text(
        "see `test/gates.md`, `target/release/` and `tools/andon.sh`\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    (tmp_path / ".gitignore").write_text("# made by suite.py\ntest/gates.md\n/target/\n")
    broken, unbuilt = seedaudit.audit_promises(tmp_path)
    assert sorted(unbuilt) == ["target/release/", "test/gates.md"]
    assert list(broken) == ["tools/andon.sh"]


def test_a_nested_gitignore_counts_for_its_own_directory(tmp_path):
    (tmp_path / "shell" / "editor").mkdir(parents=True)
    (tmp_path / "shell" / "editor" / ".gitignore").write_text("target/\n")
    assert seedaudit.is_ignored(tmp_path, "shell/editor/target/release/")
    assert not seedaudit.is_ignored(tmp_path, "tools/target/")  # anchored to shell/editor


def test_a_placeholder_is_not_a_promise(tmp_path):
    for name in ("manifesto.md", "vision.md"):
        (tmp_path / name).write_text("x\n")
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "README.md").write_text("archived as `journal/YYYY-MM.md`\n")
    (tmp_path / "spec").mkdir(); (tmp_path / "spec" / "author.md").write_text("x\n")
    (tmp_path / "doc").mkdir(); (tmp_path / "doc" / "instruments.md").write_text("x\n")
    assert seedaudit.audit_promises(tmp_path) == ({}, {})


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


def _copy_pieces(tmp_path):
    """A directory holding exactly the pieces and their gates."""
    for piece in seedaudit.PIECES:
        for rel in list(piece["paths"]) + [piece["gate"]]:
            src, dst = ROOT / rel, tmp_path / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                dst.mkdir(exist_ok=True)
            elif not dst.exists():
                dst.write_bytes(src.read_bytes())


def test_taking_any_piece_away_is_seen(tmp_path):
    """The mutation run as a gate — the in-process half of
    `tools/seedmutate.sh`.  Each piece in turn: remove one of its paths
    and it must be ABSENT; remove its gate and it must be UNBACKED.
    The sweep of 2026-08-24 found two pieces that could lose their
    gate and stay green; from here that fails the suite."""
    _copy_pieces(tmp_path)
    survived = []
    for piece in seedaudit.PIECES:
        for rel in piece["paths"]:
            saved = (tmp_path / rel).read_bytes(); (tmp_path / rel).unlink()
            row = next(r for r in seedaudit.audit_pieces(tmp_path) if r["name"] == piece["name"])
            if not row["missing"]:
                survived.append(f"rm {rel}")
            (tmp_path / rel).write_bytes(saved)
        g = tmp_path / piece["gate"]
        saved = g.read_bytes(); g.unlink()
        row = next(r for r in seedaudit.audit_pieces(tmp_path) if r["name"] == piece["name"])
        if row["backing"]:
            survived.append(f"rm {piece['gate']}")
        g.write_bytes(saved)
    assert survived == [], survived
