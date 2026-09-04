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
    monkeypatch.setenv("GESTATE_BACKLINKS_LOG", str(tmp_path / "fires.log"))
    for rel in ("board", "board/done", "doc/memory", "spec", "tools", "gestate", "journal"):
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
                          env={**os.environ, "GESTATE_BACKLINKS_LOG": os.devnull,
                               **(env or {})})


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
    assert len(text.splitlines()) <= backlinks.HOOK_CUT + 2 + len(backlinks.TIERS)


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
    assert "doc/instruments.md" in files
    #: The card moved to `done/` the day it was written; a citer is
    #: found on whatever shelf it stands.
    assert any(f.startswith("board") and f.endswith("/backlinks.md") for f in files)
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


# --- not all citations are equal --------------------------------------------------

def test_the_rows_come_ranked_and_the_cut_falls_on_history(tree):
    """Henri, 2026-09-04: *"Not all citations are equal."*  A reader of
    the target wants what currently leans on it first and the past last,
    and within a tier a deliberate pointer before a passing mention."""
    (tree / "journal" / "2026-08.md").write_text("we read gestate/host.c today\n")
    (tree / "fixme.md").write_text("### F7. **[fixed]**\n\nhost.c did it\n")
    (tree / "test" ).mkdir()
    (tree / "test" / "test_host.py").write_text("# gestate/host.c\n")
    (tree / "spec" / "audio.md").write_text("`gestate/host.c` is the callback\n")
    (tree / "board" / "done" / "old.md").write_text("see gestate/host.c\n")
    (tree / "board" / "flare.md").write_text("# flare\n" + "\n" * 30 + "later, host.c\n")
    (tree / "board" / "crack.md").write_text("# crack\n    see gestate/host.c\n")
    (tree / "doc" / "memory" / "m.md").write_text("host.c\n")
    _name, rows = ask(tree, "gestate/host.c")
    assert [r for r, _l in rows] == [
        SHELF + "crack.md",        # a live card's header block
        SHELF + "flare.md",        # a live card, further down
        "doc/memory/m.md",         # memory, same tier, after the cards by name
        "spec/audio.md",           # a standing document
        "test/test_host.py",       # code and tests
        DONE + "old.md",           # shelved
        "fixme.md",                # the ledger
        "journal/2026-08.md",      # history last
    ]


def test_an_explicit_citation_outranks_a_mention_in_the_same_tier(tree):
    (tree / "doc" / "a.md").write_text("mentions thing.md in passing\n")
    (tree / "doc" / "b.md").write_text("cites " + THING + " on purpose\n")
    _name, rows = ask(tree, str(tree / "board" / "thing.md"))
    assert rows == [("doc/b.md", 1), ("doc/a.md", 1)]


def test_the_output_is_grouped_under_tier_labels(tree):
    (tree / "journal" / "j.md").write_text("gestate/host.c\n")
    (tree / "board" / "c.md").write_text("gestate/host.c\n")
    name, rows = backlinks.citers(backlinks.Tree(tree), "gestate/host.c")
    lines = backlinks.report(name, rows).splitlines()
    assert lines[1] == "cards and memory:"
    assert lines[3] == "history:"


# --- the hook watches itself ----------------------------------------------------------

def test_every_fire_is_logged_with_its_denominator(tmp_path):
    log = tmp_path / "fires.log"
    env = {"GESTATE_BACKLINKS_CACHE": str(tmp_path / "c.json"), "GESTATE_BACKLINKS_LOG": str(log)}
    run_hook({"tool_name": "Read", "tool_input": {"file_path": str(ROOT / "gestate" / "host.c")}}, env)
    run_hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/hostname"}}, env)
    lines = [l.split("\t") for l in log.read_text().splitlines()]
    assert len(lines) == 1, "a silent fire is not a fire"
    _when, rel, total, shown, session, offered = lines[0]
    assert rel == "gestate/host.c"
    assert int(total) > int(shown) == backlinks.HOOK_CUT
    #: The two fields `earned` needs.  The offers are the paths actually
    #: put in front of the reader — not the whole citer list, because a
    #: name cut at twenty was never shown and cannot have been followed.
    assert session == "", "no session_id in this payload"
    #: **Distinct files, not rows.**  Twenty citations may come from
    #: thirteen files, because one file cites a target on several lines;
    #: what a reader can go and open is the file.  So the offers are a
    #: set, and counting rows here would have made every repeat citation
    #: look like another chance the tool gave the reader.
    names = offered.split(",")
    assert 0 < len(names) <= backlinks.HOOK_CUT
    assert len(set(names)) == len(names)
    assert all((ROOT / n).exists() for n in names)


def _log(path, rows, now):
    path.write_text("".join(f"{now - i * 3600}\tf{i}.md\t{total}\t{shown}\n"
                            for i, (total, shown) in enumerate(rows)))


def test_the_lamp_trips_when_the_cut_has_become_the_rule(tmp_path, monkeypatch):
    """The mechanism behind *write something that ensures you will
    correct the issue if it becomes an issue* (Henri, 2026-09-04): the
    hook keeps its own denominator, and the pre-commit lamp names the
    designed fix the day a third of a fortnight's fires were cut."""
    log = tmp_path / "fires.log"
    monkeypatch.setenv("GESTATE_BACKLINKS_LOG", str(log))
    now = 1_800_000_000
    cut, ok = (58, backlinks.HOOK_CUT), (7, 7)
    _log(log, [cut] * 10 + [ok] * 20, now)                # 30 fires, a third cut
    tripped, line = backlinks.lamp(now=now)
    assert tripped and "card:backlinks-ranges.md" in line
    _log(log, [cut] * 9 + [ok] * 21, now)                 # under a third
    assert backlinks.lamp(now=now)[0] is False
    _log(log, [cut] * 10 + [ok] * 19, now)                # under the floor
    assert backlinks.lamp(now=now)[0] is False
    _log(log, [cut] * 30, now - 15 * 86400)               # all of it outside the window
    tripped, line = backlinks.lamp(now=now)
    assert tripped is False and "no fires" in line


def test_check_exits_two_when_the_lamp_trips_and_zero_when_not(tmp_path):
    log = tmp_path / "fires.log"
    env = {**os.environ, "GESTATE_BACKLINKS_LOG": str(log)}
    if not backlinks.installed():
        pytest.skip("the Read hook is not installed on this desk")
    _log(log, [(58, 20)] * 30, int(time.time()))
    r = subprocess.run([sys.executable, str(TOOL), "--check"], env=env, capture_output=True, text=True)
    assert r.returncode == 2 and "backlinks-ranges" in r.stdout
    _log(log, [(7, 7)] * 30, int(time.time()))
    r = subprocess.run([sys.executable, str(TOOL), "--check"], env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "installed" in r.stdout


# --- did it earn its place? -----------------------------------------------------------

def _sitting(path, rows, now):
    """`rows` as `(seconds ago, session, file read, [names offered])`."""
    path.write_text("".join(
        f"{now - ago}\t{rel}\t9\t9\t{sess}\t{','.join(offered)}\n"
        for ago, sess, rel, offered in rows))


def test_a_follow_is_a_later_fire_on_a_name_the_tool_offered(tmp_path, monkeypatch):
    """The number `card:backlinks.md` left open and Henri asked for:
    *does the answer change what the reader does next?*

    A follow is a fire on a file an **earlier fire in the same sitting**
    put in front of the reader.  Everything it must not count is here,
    because each of them would inflate the one number the tool is being
    judged on.
    """
    log = tmp_path / "fires.log"
    monkeypatch.setenv("GESTATE_BACKLINKS_LOG", str(log))
    now = 1_800_000_000

    # Offered, then opened: the whole point.
    _sitting(log, [(300, "s1", "a.md", ["b.md"]), (200, "s1", "b.md", [])], now)
    assert backlinks.earned(now=now)["follows"] == 1

    # **Not across sittings.**  A name offered yesterday cannot explain
    # a file opened today; the reader is a different session with no
    # memory of the offer.
    _sitting(log, [(300, "s1", "a.md", ["b.md"]), (200, "s2", "b.md", [])], now)
    assert backlinks.earned(now=now)["follows"] == 0

    # **Not backwards.**  Reading `b` and then being told `a` cites it is
    # the tool describing a journey already made.
    _sitting(log, [(300, "s1", "b.md", []), (200, "s1", "a.md", ["b.md"])], now)
    assert backlinks.earned(now=now)["follows"] == 0

    # **Not a re-read.**  A file opened before it was offered was on the
    # reader's own path; opening it again is not the tool's doing.
    _sitting(log, [(400, "s1", "b.md", []), (300, "s1", "a.md", ["b.md"]),
                   (200, "s1", "b.md", [])], now)
    assert backlinks.earned(now=now)["follows"] == 0

    # **Not a name that was never shown.**  The offers logged are the
    # rows that survived the cut at twenty.
    _sitting(log, [(300, "s1", "a.md", []), (200, "s1", "b.md", [])], now)
    assert backlinks.earned(now=now)["follows"] == 0


def test_the_fires_that_predate_the_sitting_id_are_named_not_dropped(tmp_path, monkeypatch):
    """A four-field line is still a fire.

    It cannot take part in a follow, and the honest thing is to say how
    many were left out rather than divide by the smaller number and
    report a healthier rate than the log supports.
    """
    log = tmp_path / "fires.log"
    monkeypatch.setenv("GESTATE_BACKLINKS_LOG", str(log))
    now = 1_800_000_000
    log.write_text(f"{now - 500}\told.md\t9\t9\n"
                   f"{now - 300}\ta.md\t9\t9\ts1\tb.md\n"
                   f"{now - 200}\tb.md\t9\t9\ts1\t\n")
    got = backlinks.earned(now=now)
    assert (got["fires"], got["follows"], got["blind"]) == (2, 1, 1)
    assert "1 fires predate" in backlinks.report_earned()
    # And the old line still counts as a fire everywhere else.
    assert len(backlinks.fires(now=now)) == 3


def test_the_lamp_says_when_nothing_offered_was_ever_opened(tmp_path, monkeypatch):
    """The second cause, and it is the decision the card asked for.

    Zero follows over a real number of fires means the tool is
    decoration with a context bill.  It is named apart from the cut
    share, because one lamp lighting for two reasons under one sentence
    is how an andon gets muted.
    """
    log = tmp_path / "fires.log"
    monkeypatch.setenv("GESTATE_BACKLINKS_LOG", str(log))
    now = 1_800_000_000
    # Thirty fires, none of them following anything, and none cut.
    _sitting(log, [(i * 60, "s1", f"f{i}.md", []) for i in range(30)], now)
    tripped, line = backlinks.lamp(now=now)
    assert tripped and "none of 30 fires was followed" in line
    assert "card:backlinks-ranges.md" not in line, "that is the other cause"

    # One follow is enough to say it did something no other route did.
    rows = [(i * 60, "s1", f"f{i}.md", []) for i in range(29)]
    rows.insert(0, (30 * 60, "s1", "f1.md", ["f0.md"]))
    _sitting(log, rows, now)
    tripped, line = backlinks.lamp(now=now)
    assert tripped is False and "1 of 30 followed" in line
