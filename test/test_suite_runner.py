"""`tools/suite.py`'s own reporting, which nothing checked.

**The suite is the instrument that says whether the tree is good, and
it has twice reported a green page for a partial run** — its own
comments carry both cases: a two-pass run whose totals came from the
second pass alone, and a version that captured output instead of
streaming it so a healthy run looked like a hang.

The Rust workspace joined it on 2026-08-18 (`card:interface-oracle.md`,
Henri: *"we have to add the command to run rust tests from suite… I had
no idea rust tests weren't there in the suite"*).  344 tests across
eighteen binaries had been running nowhere.  The risk a new pass brings
is the old one: that it fails and the page still reads green.

So what is checked here is the **verdict**, not the crates — the crates
check themselves, and `cargo` is what runs them.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# F180: `suite.py` imports `rulecount`, `journalroll` and `arrivals` by
# bare name, so this file only passed when an earlier test had put
# `tools/` on the path.  A test that passes only in company has a
# verdict that depends on collection order.
import sys
sys.path.insert(0, str(ROOT / "tools"))

spec = importlib.util.spec_from_file_location("suite", ROOT / "tools" / "suite.py")
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


def fake_stream(rc: int, out: str):
    """Stands in for `main`'s streaming runner, which needs a terminal."""
    def stream(argv):
        return rc, out
    return stream


GREEN = "test result: ok. 81 passed; 0 failed\ntest result: ok. 9 passed; 0 failed\n"


def test_a_green_workspace_is_counted_across_every_binary():
    """Eighteen binaries, and the count has to be their sum.

    The failure this guards is the one the file already made once with
    pytest's totals: keeping the **last** match rather than adding them
    up, which reported twenty-six tests as the whole run.
    """
    rc, _out, note = suite._rust(fake_stream(0, GREEN), False, ROOT)
    assert rc == 0
    assert note == "90 passed"


def test_a_red_crate_reaches_the_report_and_the_exit_code():
    """A pass that fails silently is worse than one that does not run.

    Deliberately **not a stop**: the Python pass is twenty-five minutes
    of evidence and must still reach the page.  So the contract is that
    the return code survives and the row says so.
    """
    rc, _out, note = suite._rust(fake_stream(101, "test result: FAILED"), False, ROOT)
    assert rc == 101, "a red workspace must not exit zero"
    assert "fail" in note.lower(), "the report row must say the crates failed"


def test_no_cargo_is_a_note_and_not_a_failure(monkeypatch):
    """`doc/install.md`'s posture, kept: everything `apt` buys is a
    backend, and a missing one degrades politely.  A machine with no
    cargo still has a Python suite worth running — and must not be told
    its tree is broken.
    """
    monkeypatch.setattr(suite.shutil, "which", lambda _name: None)
    rc, _out, note = suite._rust(fake_stream(0, GREEN), False, ROOT)
    assert rc == 0
    assert "no cargo" in note


# ── `--gates`, and the page it must not be mistaken for ──────────────────
#
# `card:cheap-gates.md`: the eight structural checks cost seventeen
# seconds and ran once a shift, because the only way to reach them was to
# start a twenty-five-minute pass.  `--gates` is the mode that stops
# after them.  **Its whole risk is that a cheap check reads like an
# expensive one** — eight green document checks are a true page and an
# untrue impression — so what is tested here is the labelling, not the
# checks.

GATE_OUT = "........\n8 passed in 11.31s\n"


def test_the_gate_page_says_it_is_not_a_suite_run(tmp_path, monkeypatch):
    """Three times over, and a reader must not be able to skim past it.

    The failure being designed against is somebody opening the tree
    cold, finding a green page written by `tools/suite.py`, and taking
    it for evidence that gestate works.  It is evidence that the tree's
    documents agree with each other and nothing more.
    """
    monkeypatch.setattr(suite, "ROOT", tmp_path)
    monkeypatch.setattr(suite, "GATES_PAGE", tmp_path / "gates.md")
    from datetime import datetime
    rc = suite._draw_gates(0, GATE_OUT, datetime(2026, 8, 19, 15, 0), 12.0,
                           "unfenced", ["test/test_board.py"])
    page = (tmp_path / "gates.md").read_text()
    assert rc == 0
    assert "not a suite run" in page, "the header has to disown the suite"
    assert "the suite did not run" in page.lower(), \
        "the totals line is what a skimmer reads; it has to say so too"
    assert "8 passed" in page


def test_a_gate_run_does_not_overwrite_the_suite_report(tmp_path, monkeypatch):
    """Two writers, one file — this board's own rule, in miniature.

    A gate run happens per commit and a full run per shift, so sharing
    `test/report.md` would mean the shift's evidence is destroyed by the
    next commit and the reader cannot tell which run wrote the page.
    """
    monkeypatch.setattr(suite, "ROOT", tmp_path)
    monkeypatch.setattr(suite, "GATES_PAGE", tmp_path / "gates.md")
    monkeypatch.setattr(suite, "REPORT", tmp_path / "report.md")
    from datetime import datetime
    suite._draw_gates(0, GATE_OUT, datetime(2026, 8, 19, 15, 0), 12.0,
                      "unfenced", ["test/test_board.py"])
    assert not (tmp_path / "report.md").exists(), \
        "the gate page must not stand in for the suite's"


def test_a_red_gate_survives_into_the_page_and_the_exit_code():
    """The reason the hook exists: a failure has to *stop* something."""
    out = "FAILED test/test_atlas.py::test_every_module_has_a_lane - no lane\n" \
          "1 failed, 135 passed in 11.51s\n"
    assert suite._failures(out) == \
        [("test/test_atlas.py::test_every_module_has_a_lane", "no lane")]
    assert "1 failed" in suite._tally([out])


def test_the_gates_are_read_from_the_one_list():
    """No second copy of the eight paths anywhere.

    The card records a session hand-copying them out of this file into a
    `pytest` command on the days it could not spare the full pass —
    which works until the list grows, and then silently runs the old
    set.  `--gates` exists so that the list has exactly one home.
    """
    src = (ROOT / "tools" / "suite.py").read_text()  # the test file's ROOT
    assert src.count("GATES = {") == 1
    for path in suite.GATES:
        assert (ROOT / path.split("::")[0]).exists(), f"{path} named but absent"


# ── the hook that runs them ──────────────────────────────────────────────


def test_the_hook_installs_and_uninstalls_in_a_fresh_repository(tmp_path):
    """It lands in somebody else's working directory, so it has to leave.

    `card:cheap-gates.md` weighed a hook against a line in
    `board/README.md` and named this as the cost: it fires on Henri's
    commits too.  The answer given was that removing it is one command,
    which is only true if that command works.
    """
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "tools").mkdir()
    hook_src = ROOT / "tools" / "pre-commit.sh"
    (repo / "tools" / "pre-commit.sh").write_bytes(hook_src.read_bytes())
    (repo / "tools" / "pre-commit.sh").chmod(0o755)

    def run(*args):
        return subprocess.run([str(repo / "tools" / "pre-commit.sh"), *args],
                              cwd=repo, capture_output=True, text=True)

    assert run("--check").returncode == 1, "a fresh clone has no hook"
    assert run("--install").returncode == 0
    assert run("--check").returncode == 0
    assert run("--uninstall").returncode == 0
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()
    assert run("--check").returncode == 1


def test_the_hook_refuses_to_overwrite_a_hook_it_did_not_write(tmp_path):
    """Somebody else's pre-commit is somebody else's work."""
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "tools").mkdir()
    (repo / "tools" / "pre-commit.sh").write_bytes(
        (ROOT / "tools" / "pre-commit.sh").read_bytes())
    (repo / "tools" / "pre-commit.sh").chmod(0o755)
    theirs = repo / ".git" / "hooks" / "pre-commit"
    theirs.write_text("#!/bin/sh\necho mine\n")

    r = subprocess.run([str(repo / "tools" / "pre-commit.sh"), "--install"],
                       cwd=repo, capture_output=True, text=True)
    assert r.returncode == 3
    assert theirs.read_text() == "#!/bin/sh\necho mine\n", "it was overwritten"


WARNED = """\
..                                                                       [100%]
=============================== warnings summary ===============================
test/test_thing.py::test_it_warns
  /home/somebody/gestate/gestate/thing.py:12: DeprecationWarning: datetime.utcnow() is deprecated
    now = datetime.utcnow()

test/test_other.py: 3 warnings
  /usr/lib/python3/x.py:1: ResourceWarning: unclosed file
    f = open(p)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 4 warnings in 0.10s
"""


def test_a_warning_reaches_the_page_by_name():
    """The totals said *1 warning* and the page named none, so the only
    way to know which was to run twenty-three minutes again (Henri,
    2026-08-26).  The page keeps the test and the sentence."""
    found = suite._warnings(WARNED)
    assert [h for h, _ in found] == ["test/test_thing.py::test_it_warns",
                                     "test/test_other.py: 3 warnings"]
    assert found[0][1] == ["/home/somebody/gestate/gestate/thing.py:12: "
                           "DeprecationWarning: datetime.utcnow() is deprecated"]
    page = "\n".join(suite._warning_section(found))
    assert "test_it_warns" in page and "utcnow" in page
    assert "now = datetime.utcnow()" not in page, "the code line is noise"
    assert suite._warning_section([]) == ["## Warnings", "", "None.", ""]
    assert suite._warnings("2 passed in 0.1s\n") == []


def test_the_command_asks_pytest_for_warnings():
    """`-rfE` was the whole reason the page could count and not name."""
    src = (ROOT / "tools" / "suite.py").read_text()
    assert '"-rfEw"' in src
