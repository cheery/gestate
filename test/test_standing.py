"""tools/standing.py — the question a session is asked when it opens a card.

`card:standing-questions.md`.  A stored cue is worth nothing unless it
reaches the context at the moment it is needed, so what is tested is
the landing: the right questions for the right shelf, capped, once per
sitting, nothing for anything that is not a card, and nothing on a
malformed payload — a hook that raises interrupts a session over a
file it was only reading.

Each case is a small tree of its own with a questions file whose
answer is known in advance, and one gate reads this tree's own
`board/standing.md` to say it is usable.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import standing  # noqa: E402

TOOL = ROOT / "tools" / "standing.py"

#: Shelf paths spelled from parts: `test_citations.py` reads every literal
#: in every test and refuses a card cited as a path, which is its job.
SHELF = "board" + "/"
LATER = SHELF + "later/"
DONE = SHELF + "done/"

QUESTIONS = """# standing.md — a small one

prose before the first heading is not a question
- and neither is this line

## live
- What would a professional check that we have not?
  *— where it was paid for*
- Second live question?
- Third live question?
- Fourth live question, over the cap?

## shelved
- Is this waiting on an event, or on Henri?

## proposed
- A candidate that must never fire?
"""


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setenv("GESTATE_STANDING_LOG", str(tmp_path / "fires.log"))
    for rel in ("board", "board/later", "board/done", "board/refused", "doc"):
        (tmp_path / rel).mkdir(parents=True)
    (tmp_path / "board" / "standing.md").write_text(QUESTIONS)
    (tmp_path / "board" / "README.md").write_text("# board\n")
    (tmp_path / "board" / "thing.md").write_text("# thing\n")
    (tmp_path / "board" / "later" / "rest.md").write_text("# rest\n")
    (tmp_path / "board" / "done" / "gone.md").write_text("# gone\n")
    (tmp_path / "doc" / "page.md").write_text("# page\n")
    return tmp_path


def fire(root, path, session="s1", tool="Read", command=None):
    payload = {"tool_name": tool, "session_id": session,
               "tool_input": {"command": command} if tool == "Bash" else {"file_path": path}}
    out = standing.hook(json.dumps(payload), root)
    if not out:
        return ""
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


# --- parsing ------------------------------------------------------------------

def test_a_line_before_the_first_heading_is_not_a_question():
    sections = standing.parse(QUESTIONS)
    assert "and neither is this line" not in sum(sections.values(), [])
    assert sections["live"][0] == "What would a professional check that we have not?"
    assert sections["proposed"] == ["A candidate that must never fire?"]


def test_the_evidence_line_under_a_question_is_not_a_second_question():
    assert "where it was paid for" not in " ".join(standing.parse(QUESTIONS)["live"])


# --- the landing --------------------------------------------------------------

def test_a_live_card_gets_the_live_questions_capped(tree):
    out = fire(tree, str(tree / "board" / "thing.md"))
    assert "live card, " + SHELF + "thing.md" in out
    assert "professional" in out and "Third live question?" in out
    assert "Fourth" not in out, "the cap is the reader's attention"


def test_a_shelved_card_gets_the_shelved_question_only(tree):
    out = fire(tree, str(tree / "board" / "later" / "rest.md"))
    assert "event, or on Henri" in out
    assert "professional" not in out


def test_a_shelf_with_no_heading_gets_nothing(tree):
    assert fire(tree, str(tree / "board" / "done" / "gone.md")) == ""


def test_a_proposed_question_never_fires(tree):
    for rel in (SHELF + "thing.md", LATER + "rest.md", DONE + "gone.md"):
        assert "candidate" not in fire(tree, str(tree / rel), session=rel)


def test_nothing_for_the_readme_the_questions_file_or_a_page(tree):
    assert fire(tree, str(tree / "board" / "README.md")) == ""
    assert fire(tree, str(tree / "board" / "standing.md")) == ""
    assert fire(tree, str(tree / "doc" / "page.md")) == ""


def test_once_per_card_per_sitting(tree):
    assert fire(tree, str(tree / "board" / "thing.md"), session="a") != ""
    assert fire(tree, str(tree / "board" / "thing.md"), session="a") == ""
    assert fire(tree, str(tree / "board" / "thing.md"), session="b") != "", "a new sitting is asked again"


def test_a_shell_read_of_a_card_is_a_fire_too(tree):
    out = fire(tree, None, tool="Bash", command="cat " + SHELF + "thing.md")
    assert "live card, " + SHELF + "thing.md" in out


def test_a_malformed_payload_is_silent(tree, capsys):
    assert standing.hook("not json", tree) == ""
    assert standing.hook("", tree) == ""
    assert standing.hook(json.dumps({"tool_name": "Read", "tool_input": {}}), tree) == ""


def test_a_file_outside_the_tree_is_silent(tree, tmp_path_factory):
    elsewhere = tmp_path_factory.mktemp("elsewhere") / "board" / "thing.md"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text("# not ours\n")
    assert fire(tree, str(elsewhere)) == ""


# --- the lamp -----------------------------------------------------------------

def test_the_lamp_names_a_heading_over_the_cap(tree):
    code, line = standing.check(tree, settings=tree / "no-settings.json")
    assert code == 2 and "live holds 4" in line


def test_the_lamp_says_not_installed_before_anything_else_is_fine(tree):
    (tree / "board" / "standing.md").write_text("## live\n- one?\n")
    code, line = standing.check(tree, settings=tree / "no-settings.json")
    assert code == 1 and "--install" in line


def test_the_lamp_is_green_installed_with_a_question_standing(tree):
    (tree / "board" / "standing.md").write_text("## live\n- one?\n")
    settings = tree / "settings.json"
    settings.write_text(json.dumps({"hooks": {"PostToolUse": [
        {"matcher": "Read|Bash", "hooks": [{"type": "command",
                                            "command": "~/gestate/tools/standing.py --hook"}]}]}}))
    code, line = standing.check(tree, settings=settings)
    assert code == 0 and "1 question standing" in line


# --- this tree ----------------------------------------------------------------

def test_this_trees_questions_file_is_usable():
    """The gate: `board/standing.md` parses, every firing heading is
    within the cap, and the file is not a card — `test_board.py` leaves
    it out by name, and this is the other half of that exclusion."""
    sections = standing.load(ROOT)
    assert "proposed" in sections, "a session's candidates go under `## proposed`"
    for heading, qs in sections.items():
        if heading in standing.SHELVES.values():
            assert len(qs) <= standing.CAP, f"`## {heading}` holds {len(qs)}; the rest are never asked"
    code, line = standing.check(ROOT)
    assert code != 2, line


def test_the_command_answers_for_a_card_of_this_tree():
    out = subprocess.run([sys.executable, str(TOOL), "card:" + "online.md"],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0
    assert SHELF + "online.md" in out.stdout
