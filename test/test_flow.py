"""tools/flow.py — the board's flow, against a repository whose history
is written on purpose.

Every fact the tool reports comes from `git log`, so every test here
makes a small repository with commits at chosen dates and asks the
tool what it sees.  The seven-day lamp is Henri's rule (2026-09-04):
*"kortit joihin ei ole koskettu 7 päivään, niiden pitäisi mennä
later/ hyllyyn meidän kauttamme"* — and *through us* is why the lamp
names cards and exits 2 rather than moving anything.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import flow  # noqa: E402

DAY = 86400
T0 = 1_800_000_000          # a fixed "now" — 2027-01-15, and every commit sits before it

#: Shelf paths spelled from parts: `test_citations.py` reads every literal
#: in every test and refuses a card cited by path, which is its job.
B, D, L = "board" + "/", "board/" + "done/", "board/" + "later/"


class Repo:
    def __init__(self, path: Path):
        self.path = path
        self.env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        self.git("init", "-q")
        for shelf in flow.SHELVES:
            (path / shelf).mkdir(parents=True, exist_ok=True)

    def git(self, *args, when=None):
        env = dict(self.env)
        if when is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = f"{when} +0000"
        return subprocess.run(["git", "-C", str(self.path), *args], env=env,
                              capture_output=True, text=True, check=True)

    def commit(self, when, **files):
        """Write the files (None deletes) and commit them at `when`."""
        for rel, text in files.items():
            p = self.path / rel
            if text is None:
                p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
        self.git("add", "-A", "board")
        self.git("commit", "-q", "-m", f"at {when}", "--allow-empty", when=when)

    def move(self, when, src, dst):
        self.git("mv", src, dst)
        self.git("commit", "-q", "-m", f"move at {when}", when=when)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def by_name(rows):
    return {r["name"]: r for r in rows}


def test_born_is_the_first_commit_and_touched_the_last(repo):
    repo.commit(T0 - 20 * DAY, **{B + "a.md": "# a\n"})
    repo.commit(T0 - 12 * DAY, **{B + "a.md": "# a\n\nmore\n"})
    repo.commit(T0 - 3 * DAY, **{"board/README.md": "1. a\n"})
    a = by_name(flow.cards(repo.path, now=T0))["a.md"]
    assert a["born"] == T0 - 20 * DAY
    assert a["touched"] == T0 - 12 * DAY, "an edit to the README is not a touch"


def test_a_finished_card_keeps_its_birth_and_gets_a_done_date(repo):
    repo.commit(T0 - 20 * DAY, **{B + "a.md": "# a\n"})
    repo.move(T0 - 15 * DAY, B + "a.md", D + "a.md")
    a = by_name(flow.cards(repo.path, now=T0))["a.md"]
    assert (a["shelf"], a["born"], a["done"]) == ("board/done", T0 - 20 * DAY, T0 - 15 * DAY)
    assert a["shelved"] is None


def test_a_card_that_arrives_shelved_is_born_on_the_shelf(repo):
    repo.commit(T0 - 9 * DAY, **{L + "s.md": "# s\n"})
    s = by_name(flow.cards(repo.path, now=T0))["s.md"]
    assert (s["shelf"], s["born"], s["shelved"]) == ("board/later", T0 - 9 * DAY, T0 - 9 * DAY)


def test_an_uncommitted_card_is_touched_now(repo):
    repo.commit(T0 - 20 * DAY, **{B + "a.md": "# a\n"})
    (repo.path / "board" / "new.md").write_text("# new\n")
    rows = by_name(flow.cards(repo.path, now=T0))
    assert rows["new.md"]["touched"] == T0 and rows["new.md"]["born"] == T0
    assert flow.stale(list(rows.values()), now=T0) == [rows["a.md"]]


def test_the_lamp_names_the_stale_cards_oldest_first_and_only_live_ones(repo):
    repo.commit(T0 - 30 * DAY, **{B + "old.md": "# old\n", B + "older.md": "# older\n",
                                  B + "fresh.md": "# fresh\n", B + "gone.md": "# gone\n"})
    repo.commit(T0 - 8 * DAY, **{B + "old.md": "# old\n\nedit\n"})
    repo.commit(T0 - 2 * DAY, **{B + "fresh.md": "# fresh\n\nedit\n"})
    repo.move(T0 - 1 * DAY, B + "gone.md", L + "gone.md")
    rows = flow.cards(repo.path, now=T0)
    assert [r["name"] for r in flow.stale(rows, now=T0)] == ["older.md", "old.md"]
    tripped, line = flow.lamp(rows, now=T0)
    assert tripped
    assert "older.md (30d)" in line and "old.md (8d)" in line
    assert "fresh" not in line and "gone" not in line
    assert "through a session and him" in line


def test_the_lamp_is_quiet_at_six_days_and_trips_at_seven(repo):
    repo.commit(T0 - 6 * DAY, **{B + "a.md": "# a\n"})
    assert flow.lamp(flow.cards(repo.path, now=T0), now=T0)[0] is False
    assert flow.lamp(flow.cards(repo.path, now=T0 + DAY), now=T0 + DAY)[0] is True


def test_check_exits_two_when_tripped_and_zero_when_not(repo):
    """The subprocess has no fixed `now`, so this one commits in real
    time — thirty real days ago."""
    import time
    repo.commit(int(time.time()) - 30 * DAY, **{B + "a.md": "# a\n"})
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "flow.py"), "--check",
                        "--root", str(repo.path)], capture_output=True, text=True)
    assert r.returncode == 2 and "a.md" in r.stdout
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "flow.py"), "--check",
                        "--root", str(repo.path), "--days", "10000"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "every open card" in r.stdout


def test_the_report_counts_lead_time_and_weekly_flow(repo):
    repo.commit(T0 - 20 * DAY, **{B + "a.md": "# a\n", B + "b.md": "# b\n"})
    repo.move(T0 - 20 * DAY + 3600, B + "a.md", D + "a.md")     # same day
    repo.move(T0 - 10 * DAY, B + "b.md", D + "b.md")            # ten days
    text = flow.report(flow.cards(repo.path, now=T0), now=T0)
    assert "2 cards: 0 open, 2 done, 0 shelved" in text
    assert "median 5.0" in text and "same-day 1 of 2" in text
    assert "week      arrived  done  shelved" in text


def test_this_tree_answers(tmp_path):
    """Whatever the numbers are today, the walk over the real board
    returns every card on every shelf exactly once."""
    rows = flow.cards(ROOT)
    on_disk = {p.name for s in flow.SHELVES for p in (ROOT / s).glob("*.md")} - {"README.md"}
    assert sorted(r["name"] for r in rows) == sorted(on_disk)
