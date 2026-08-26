"""The diff over the file — `card:git-viewer.md`'s last piece.

Henri, 2026-08-20: *"I'd like to see which lines go away which come in,
within the editor."*  And 2026-08-26, when the shape was put to him:
*"open file versus HEAD, first that … removed lines should appear where
they were removed from."*

What is held here is the model's half: which rows cross the wire for a
given edit of a committed file.  `shell/editor/tests/view.rs` holds the
drawing.  The repository these run against is **this one**, the honest
fixture `test_history.py` already uses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate import history
from gestate.session import furniture

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "examples" / "closure.ges"
NAME = "examples/closure.ges"

pytestmark = pytest.mark.skipif(not (ROOT / ".git").exists(),
                                reason="not a checkout")


def _session(lines, path=FILE):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    class View:
        showing = "source"

        def lines(self):
            return list(lines)

        def text(self):
            return "\n".join(lines) + "\n"

        def caret(self):
            return 0

    it = session()
    it.bench.path = path
    it.view = View()
    return it


def _rows(it, verb):
    return [l.split("\t") for l in furniture(it).splitlines()
            if l.startswith(verb + "\t")]


def _at_head():
    base = history.at(ROOT, "HEAD", NAME)
    assert len(base) > 6, "the fixture needs a few lines to move"
    return base


# ── Nothing until asked ─────────────────────────────────────────────────────


def test_nothing_stands_until_asked():
    it = _session(_at_head())
    assert _rows(it, "diff") == [] and _rows(it, "gone") == [] \
        and _rows(it, "added") == []


def test_an_unchanged_file_says_so_and_sends_only_the_word():
    it = _session(_at_head())
    said = it.run("diff", "")
    assert said.startswith("against HEAD: 0 added, 0 gone")
    assert _rows(it, "diff") == [["diff", "HEAD"]]
    assert _rows(it, "gone") == [] and _rows(it, "added") == []


# ── Where a removed line stands ────────────────────────────────────────────


def test_a_removed_line_is_boxed_under_the_line_before_the_gap():
    """**Where they were removed from.**  Line 3 gone: it stood between
    lines 2 and 3 of what is left, so it is boxed under line 2."""
    base = _at_head()
    lines = base[:2] + base[3:]
    it = _session(lines)
    assert "1 gone" in it.run("diff", "HEAD")
    assert _rows(it, "gone") == [["gone", "2", base[2]]]
    assert _rows(it, "added") == []


def test_a_run_removed_together_is_one_box_a_row_each():
    base = _at_head()
    lines = base[:2] + base[5:]
    it = _session(lines)
    it.run("diff", "HEAD")
    assert _rows(it, "gone") == [["gone", "2", base[2]],
                                 ["gone", "2", base[3]],
                                 ["gone", "2", base[4]]]


def test_a_line_removed_from_the_very_top_stands_under_line_one():
    """A box has no line to hang from above the first; under line one
    is the nearest honest place, and the text says which it was."""
    base = _at_head()
    it = _session(base[1:])
    it.run("diff", "HEAD")
    assert _rows(it, "gone") == [["gone", "1", base[0]]]


# ── What came, and what changed ────────────────────────────────────────────


def test_an_added_line_is_marked_and_not_boxed():
    base = _at_head()
    lines = base[:4] + ["# a line the commit never had"] + base[4:]
    it = _session(lines)
    assert "1 added" in it.run("diff", "HEAD")
    assert _rows(it, "added") == [["added", "5"]]
    assert _rows(it, "gone") == []


def test_a_changed_line_is_both_and_the_old_text_stands_under_the_new():
    """A replaced run is boxed under the *last* of the lines that took
    its place, so the old text is read right after what stands there."""
    base = _at_head()
    lines = list(base)
    lines[3] = "# changed"
    it = _session(lines)
    it.run("diff", "HEAD")
    assert _rows(it, "added") == [["added", "4"]]
    assert _rows(it, "gone") == [["gone", "4", base[3]]]


def test_a_tab_in_a_removed_line_crosses_as_spaces():
    """The wire is tab-separated, so a tab in the text would be read as
    a field — the same rule `trouble` rows keep."""
    base = _at_head()
    it = _session(base)
    it._diff_base = {("HEAD", str(FILE)): base[:1] + ["\tindented"] + base[1:]}
    it._diffing = "HEAD"
    assert _rows(it, "gone") == [["gone", "1", "    indented"]]


# ── The mode, and leaving it ───────────────────────────────────────────────


def test_the_same_command_again_clears_it():
    it = _session(_at_head()[2:])
    it.run("diff", "")
    assert _rows(it, "gone")
    assert it.run("diff", "HEAD") == "diff against HEAD cleared"
    assert _rows(it, "diff") == [] and _rows(it, "gone") == []


def test_a_different_commit_replaces_rather_than_clears():
    it = _session(_at_head())
    it.run("diff", "HEAD")
    said = it.run("diff", "HEAD~1")
    assert said.startswith("against HEAD~1:")
    assert _rows(it, "diff") == [["diff", "HEAD~1"]]


def test_it_follows_the_text_as_it_is_edited():
    """**The buffer, not the file on disk** — an edit you have not saved
    is already in the reading, and the reading moves with the next
    poll rather than the next save."""
    base = _at_head()
    lines = list(base)
    it = _session(lines)
    it.run("diff", "HEAD")
    assert _rows(it, "gone") == []
    del lines[2]
    assert _rows(it, "gone") == [["gone", "2", base[2]]]


def test_a_commit_git_cannot_read_is_a_sentence():
    it = _session(_at_head())
    said = it.run("diff", "nosuchcommit")
    assert said.startswith("cannot read it at nosuchcommit:")
    assert _rows(it, "diff") == []


def test_a_file_outside_a_repository_is_a_sentence(tmp_path):
    outside = tmp_path / "loose.ges"
    outside.write_text("main = 1\n")
    it = _session(["main = 1"], path=outside)
    said = it.run("diff", "")
    assert "not inside a repository" in said or "cannot read it" in said
    assert _rows(it, "diff") == []


def test_the_commit_question_offers_commits_as_answers_not_steps():
    """`log`'s rows step into a commit's files; `diff` wants the commit
    itself, and stepping away from the question would never answer it."""
    it = _session(_at_head())
    it.asking = ("diff", 0, "")
    rows = it.choices()
    assert rows and all(r[3] == "" for r in rows if r[0] not in ("older", "newer"))
    it.asking = ("log", 0, "")
    assert it.choices()[0][3].endswith("/")
