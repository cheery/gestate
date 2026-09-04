"""tools/backlinks.py — who cites this, validated against known answers.

`card:backlinks.md` — the tree's citations run one way, and the reader
of a target cannot see who leans on it.  This holds the inverse index
to the cases each citer kind is built from, the hook contract to the
shape Claude Code reads, and the warm cost to the budget the card set.

**Validated against known answers, not read.**  `tools/dangling.py`'s
three bugs were all found by checking it against a case whose answer
was already known and none by reading it, so every kind here has a
tiny tree with one citation whose citer is known in advance — and one
test asks this tree about a card whose citers were counted by hand
the day the tool was written.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import backlinks  # noqa: E402

TOOL = ROOT / "tools" / "backlinks.py"

#: The small tree's card, and the shelves it sits on, spelled from parts:
#: `test_citations.py` reads every literal in every test, and would go
#: looking for `thing.md` on a shelf of this tree — or refuse the path
#: spelling outright, which is its job.
THING = "card:" + "thing.md"
SHELF = "board" + "/"
DONE = SHELF + "done/"


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A small tree of its own, with its own cache, so nothing here
    reads or writes the desk's."""
    monkeypatch.setenv("GESTATE_BACKLINKS_CACHE", str(tmp_path / "cache.json"))
    for rel in ("board", "board/done", "doc/memory", "spec", "tools", "gestate"):
        (tmp_path / rel).mkdir(parents=True)
    (tmp_path / "board" / "thing.md").write_text("# thing\n")
    (tmp_path / "doc" / "memory" / "a-rule.md").write_text("# a rule\n")
    (tmp_path / "spec" / "types.md").write_text("# types\n\n## The spine\n")
    (tmp_path / "tools" / "clock.sh").write_text("# clock\n")
    (tmp_path / "gestate" / "host.c").write_text("/* host */\n")
    (tmp_path / "fixme.md").write_text("### F7. **[fixed]** a thing\n\ntext\n")
    return tmp_path


def ask(root, target):
    name, rows = backlinks.citers(backlinks.Tree(root), target)
    return name, [(rel, line) for rel, line, _text in rows]


# --- each kind of citer, one known case ------------------------------------

def test_a_card_cited_by_id_on_any_shelf(tree):
    (tree / "board" / "done" / "other.md").write_text(f"see {THING}\n")
    assert ask(tree, THING) == (THING, [(DONE + "other.md", 1)])


def test_a_card_read_as_a_path_answers_to_its_id(tree):
    (tree / "spec" / "rules.md").write_text(f"\n\nwhy: {THING}\n")
    assert ask(tree, str(tree / "board" / "thing.md")) == (SHELF + "thing.md", [("spec/rules.md", 3)])


def test_a_memory_cited_by_wiki_link_and_by_bare_name(tree):
    (tree / "doc" / "memory" / "b.md").write_text("See [[a-rule]].\n")
    assert ask(tree, "[[a-rule]]") == ("doc/memory/a-rule.md", [("doc/memory/b.md", 1)])
    assert ask(tree, "a-rule") == ("doc/memory/a-rule.md", [("doc/memory/b.md", 1)])
    assert ask(tree, str(tree / "doc/memory/a-rule.md"))[1] == [("doc/memory/b.md", 1)]


def test_a_passage_citation_resolves_the_way_test_citations_does(tree):
    (tree / "doc" / "notes.md").write_text('`types.md` §"The spine" says so\n')
    assert ask(tree, "spec/types.md") == ("spec/types.md", [("doc/notes.md", 1)])


def test_a_defect_number(tree):
    (tree / "tools" / "x.py").write_text("# put back F7 and watch\n# 0xF7 is not one\n")
    assert ask(tree, "F7") == ("F7", [("tools/x.py", 1)])


def test_the_ledgers_own_heading_is_the_entry_not_a_citer(tree):
    (tree / "fixme.md").write_text("### F7. **[fixed]** a thing\n\nfound with F7's sibling F8\n")
    assert ask(tree, "F7") == ("F7", [("fixme.md", 3)])


def test_a_file_named_by_path_or_by_unique_basename(tree):
    (tree / "doc" / "x.md").write_text("read gestate/host.c\nthen host.c again\nand clock.sh\n")
    assert ask(tree, "gestate/host.c")[1] == [("doc/x.md", 1), ("doc/x.md", 2)]
    assert ask(tree, "tools/clock.sh")[1] == [("doc/x.md", 3)]


def test_an_ambiguous_basename_cites_nothing(tree):
    (tree / "spec" / "README.md").write_text("a\n")
    (tree / "doc" / "README.md").write_text("see README.md\n")
    assert ask(tree, "spec/README.md")[1] == []


def test_a_file_does_not_cite_itself(tree):
    (tree / "board" / "thing.md").write_text(f"# thing\n\nthis is {THING}\n")
    assert ask(tree, THING)[1] == []


def test_a_target_outside_the_tree_has_no_citers(tree):
    assert ask(tree, "/etc/hostname") == ("/etc/hostname", [])


# --- the cache ----------------------------------------------------------------

def test_a_changed_file_is_rescanned_and_an_unchanged_one_is_not(tree, monkeypatch):
    (tree / "doc" / "x.md").write_text(THING + "\n")
    assert ask(tree, THING)[1] == [("doc/x.md", 1)]
    calls = []
    real = backlinks.scan

    def counting(t, rel, text):
        calls.append(rel)
        return real(t, rel, text)

    monkeypatch.setattr(backlinks, "scan", counting)
    assert ask(tree, THING)[1] == [("doc/x.md", 1)]
    assert calls == [], "nothing changed, and something was rescanned"
    p = tree / "doc" / "y.md"
    p.write_text("\n" + THING + "\n")
    assert ask(tree, THING)[1] == [("doc/x.md", 1), ("doc/y.md", 2)]
    assert calls == ["doc/y.md"]


def test_a_broken_cache_is_ignored_not_fatal(tree):
    Path(os.environ["GESTATE_BACKLINKS_CACHE"]).write_text("{not json")
    (tree / "doc" / "x.md").write_text(THING + "\n")
    assert ask(tree, THING)[1] == [("doc/x.md", 1)]


# --- the hook contract ----------------------------------------------------------

def run_hook(payload, env=None):
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(TOOL), "--hook"], input=stdin,
                          capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


def test_the_hook_hands_context_back_in_the_shape_claude_code_reads(tmp_path):
    """The check the card's day one opened with: a PostToolUse hook may
    return `hookSpecificOutput.additionalContext`, and that is what
    reaches the model.  A card every session reads is the subject."""
    env = {"GESTATE_BACKLINKS_CACHE": str(tmp_path / "c.json")}
    r = run_hook({"tool_name": "Read", "hook_event_name": "PostToolUse",
                  "tool_input": {"file_path": str(ROOT / "board" / "ungated-fixes.md")}}, env)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    spec = out["hookSpecificOutput"]
    assert spec["hookEventName"] == "PostToolUse"
    text = spec["additionalContext"]
    assert text.startswith(SHELF + "ungated-fixes.md is cited by ")
    assert "board/README.md:" in text
    assert len(text.splitlines()) <= backlinks.HOOK_CUT + 2


def test_the_hook_is_silent_on_a_file_outside_the_tree_and_on_garbage(tmp_path):
    env = {"GESTATE_BACKLINKS_CACHE": str(tmp_path / "c.json")}
    r = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/hostname"}}, env)
    assert (r.returncode, r.stdout) == (0, "")
    r = run_hook("not json at all", env)
    assert (r.returncode, r.stdout) == (0, "")
    assert "backlinks --hook" in r.stderr
    r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}}, env)
    assert (r.returncode, r.stdout) == (0, "")


def test_the_hook_is_silent_on_a_file_nobody_cites(tree):
    r = run_hook({"tool_name": "Read", "tool_input": {"file_path": str(tree / "gestate" / "host.c")}})
    # `tree` is outside ROOT, so the tool's own root refuses it before
    # any citer is looked for — the silent path either way.
    assert (r.returncode, r.stdout) == (0, "")


# --- this tree ------------------------------------------------------------------

def test_a_known_answer_in_this_tree(tmp_path, monkeypatch):
    """Counted by hand on 2026-09-04: `tools/dangling.py` is named from
    its instrument section and from the card that says it is *not*
    this tool.  A superset is allowed — citations are added — and a
    miss of either is the detector being wrong."""
    monkeypatch.setenv("GESTATE_BACKLINKS_CACHE", str(tmp_path / "c.json"))
    name, rows = backlinks.citers(backlinks.Tree(ROOT), "tools/dangling.py")
    assert name == "tools/dangling.py"
    files = {rel for rel, _line, _text in rows}
    assert {"doc/instruments.md", str(Path("board") / "backlinks.md")} <= files
    assert "tools/dangling.py" not in files


def test_the_warm_walk_is_inside_the_budget(tmp_path, monkeypatch):
    """`card:backlinks.md`: a tenth of a second per read, because it runs
    on every one.  Measured at 20 ms on 2026-09-04; the bound here is
    loose enough that a loaded machine does not make it lie, and tight
    enough that walking the tree twice — the first version — fails it."""
    monkeypatch.setenv("GESTATE_BACKLINKS_CACHE", str(tmp_path / "c.json"))
    backlinks.citers(backlinks.Tree(ROOT), "tools/dangling.py")     # cold
    t0 = time.perf_counter()
    backlinks.citers(backlinks.Tree(ROOT), "tools/dangling.py")
    warm = time.perf_counter() - t0
    assert warm < 0.25, f"warm walk took {warm * 1000:.0f} ms"


def test_check_reads_the_settings_file_it_is_asked_about(tmp_path):
    off = tmp_path / "off.json"
    off.write_text(json.dumps({"hooks": {}}))
    assert backlinks.installed(off) is False
    on = tmp_path / "on.json"
    on.write_text(json.dumps({"hooks": {"PostToolUse": [{"matcher": "Read", "hooks": [
        {"type": "command", "command": "~/gestate/tools/backlinks.py --hook"}]}]}}))
    assert backlinks.installed(on) is True
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "~/gestate/tools/backlinks.py --hook"}]}]}}))
    assert backlinks.installed(wrong) is False
    assert backlinks.installed(tmp_path / "missing.json") is False


def test_install_prints_lines_that_check_accepts(tmp_path):
    """What `--install` says to add is what `--check` looks for."""
    conf = {"hooks": json.loads("{" + backlinks.INSTALL + "}")}
    p = tmp_path / "s.json"
    p.write_text(json.dumps(conf))
    assert backlinks.installed(p) is True
