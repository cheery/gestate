"""Reading the log in the workbench — `board/git-viewer.md`.

Henri's ask: *"I think we could design a git-viewer into gestate
workbench… It'd have `git log --oneline` view.  It'd be able to go into
commit message and its `--stat` view.  It'd be able to unfold a file for
diff viewing… This would suit gemba walks by being more ergonomic and
the bonus would be that my friend could use it as well."*

**A proof of concept, at his ask** — *"we commit to the try-something
approach.  Implement the smallest viable proof-of-concept program"* — so
what is held here is that the four readings come back and that the walk
through them is `open`'s own shape, not that the design is settled.

The repository these run against is **this one**, which is the honest
fixture: a temporary repo with one commit would agree with anything.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate import history

ROOT = Path(__file__).resolve().parent.parent

needs_git = pytest.mark.skipif(not (ROOT / ".git").exists(),
                               reason="not a checkout")

pytestmark = needs_git


# ── Reading it ──────────────────────────────────────────────────────────────


def test_it_finds_the_repository_from_anywhere_in_it():
    assert history.root(ROOT / "gestate" / "session.py") == ROOT
    assert history.root(ROOT / "test") == ROOT


def test_the_log_comes_back_split():
    """**Split rather than one string**, because the window draws a row
    as *a thing on the left and a note on the right*: the sha is what
    you pick and the subject is what tells you which one to."""
    rows = history.commits(ROOT)
    assert rows, "no commits"
    sha, said = rows[0]
    assert 6 <= len(sha) <= 12 and " " not in sha
    assert said


def test_a_commit_says_what_it_touched():
    rows = history.touched(ROOT, "HEAD")
    assert rows, "HEAD touched nothing"
    for name, note in rows:
        assert "|" not in name and name.strip() == name
        assert note, f"{name} has no count"


def test_the_bar_is_narrow_enough_to_leave_the_name_readable():
    """**The bar is a note on a row and the row has a name on it.**  At
    `--stat=200` a hundred-line change drew eighty-odd plus signs and
    elided the filename it belonged to — which is the one thing you were
    reading the row for.  Seen in the window on the first walk through a
    real log."""
    for _name, note in history.touched(ROOT, "HEAD"):
        assert len(note) <= 60, note


def test_a_commit_shows_its_message():
    said = history.show(ROOT, "HEAD")
    assert len(said[0]) == 40, "the full sha comes first"
    assert any(said[2:]), "the message is there"


def test_a_file_shows_its_diff():
    name = history.touched(ROOT, "HEAD")[0][0]
    lines = history.diff(ROOT, "HEAD", name)
    assert any(l.startswith("diff --git") for l in lines)
    assert any(l.startswith(("+", "-")) for l in lines)


def test_a_repository_that_is_not_there_is_a_sentence(tmp_path):
    """`git`'s own words, kept — paraphrasing *"not a git repository"*
    would be a second vocabulary for a message somebody may have seen
    before."""
    with pytest.raises(OSError):
        history.commits(tmp_path)


# ── Walking it, which is `open`'s shape ────────────────────────────────────


def _a_session():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    it = session()
    it.bench.path = ROOT / "gestate" / "session.py"
    return it


def test_the_bare_command_opens_the_question():
    it = _a_session()
    it.run("log", "")
    assert it.asking == ("log", 0, "")


def test_a_commit_is_a_step_and_not_an_answer():
    """**Stepping is the palette's own mechanism.**  Hand-rolling it in
    the model was what made Return do nothing in the real window while
    working perfectly headlessly — the model was re-asking itself and
    the window had already finished the call."""
    it = _a_session()
    it.run("log", "")
    rows = it.choices()
    assert rows, "no commits offered"
    text, note, can, step, _dim = rows[0]
    assert can and step == f"{text}/", (text, step)


def test_stepping_into_a_commit_shows_its_message():
    """And it happens on `wants`, because the palette moves the question
    along itself and the command never runs."""
    from gestate.session import act

    it = _a_session()
    sha = history.commits(ROOT)[0][0]
    act(it, f"wants\tlog\t0\t{sha}/")
    assert it.page and len(it.page[0]) == 40


def test_the_files_of_a_commit_are_offered_next():
    it = _a_session()
    sha = history.commits(ROOT)[0][0]
    it.asking = ("log", 0, f"{sha}/")
    rows = it.choices()
    assert rows, "no files offered"
    assert all(r[0].startswith(f"{sha}/") for r in rows)


def test_typing_narrows_the_files():
    it = _a_session()
    sha = history.commits(ROOT)[0][0]
    it.asking = ("log", 0, f"{sha}/")
    all_of_them = it.choices()
    it.asking = ("log", 0, f"{sha}/zzzz-nothing")
    assert it.choices() == [] and all_of_them


def test_taking_a_file_shows_its_diff():
    it = _a_session()
    sha = history.commits(ROOT)[0][0]
    name = history.touched(ROOT, sha)[0][0]
    said = it.run("log", f"{sha}/{name}")
    assert name in said
    assert any(l.startswith("diff --git") for l in it.page)


def test_a_commit_that_is_not_there_is_a_sentence():
    it = _a_session()
    assert "no such commit" in it.run("log", "notacommit")
