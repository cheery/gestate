"""`tools/mutate.py` — the sweep's instrument, and the promise it makes.

`card:ungated-fixes.md` runs on mutation: put a repair's defect back, run
the tests, read whether anything goes red.  The hazard is the tree being
left holding the defect, and the tool's whole reason for existing is that
the restore is made four ways and **verified by hash**.

Nine batches wrote that harness by hand; batch 11 made it a tool on
2026-09-02 and it arrived with **no test at all** — the instrument the
sweep depends on, ungated, which is the card's own subject arriving at the
card's own instrument.  Batch 12 found `fixme.md` F196 on its first use.

What is held here: the documented invocation, the mutation being visible
to the command and gone afterwards, the occurrence count refusing a
missed anchor, and the restore surviving a `SIGTERM`.  What is not: the
`atexit` path, and a restore that fails its hash check — both would need
the tool to be lied to about its own bytes.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "mutate", ROOT / "tools" / "mutate.py")
mutate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mutate)


BODY = "value = 1\nother = 2\n"


@pytest.fixture
def bench(tmp_path, monkeypatch):
    """A one-file tree, outside the repository, with a two-mutation spec."""
    monkeypatch.setattr(mutate, "ROOT", tmp_path)
    target = tmp_path / "thing.py"
    target.write_text(BODY)
    spec = [
        {"id": "a", "what": "one becomes nine",
         "edits": [["thing.py", "value = 1", "value = 9", 1]]},
        {"id": "b", "what": "two becomes nine",
         "edits": [["thing.py", "other = 2", "other = 9", 1]]},
    ]
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path, target


def _reads(target: pathlib.Path) -> list[str]:
    """A command that prints the file as the mutation run sees it."""
    return [sys.executable, "-c",
            f"print(open({str(target)!r}).read().strip().replace(chr(10), '|'))"]


# ── The invocation ───────────────────────────────────────────────────────────


def test_the_documented_invocation_is_accepted(bench, capsys):
    """`mutate.py spec.json --only a -- cmd` — the form the docstring gives.

    It was rejected as *"unrecognized arguments: -- python …"* the first
    time a batch used it, because argparse cannot hold an option after a
    positional whose `nargs` is open.  `fixme.md` F196.
    """
    path, target = bench
    assert mutate.main([str(path), "--only", "a", "--", *_reads(target)]) == 0
    out = capsys.readouterr().out
    assert "value = 9" in out
    assert "other = 9" not in out          # and only the one named ran


def test_the_option_may_also_come_first(bench, capsys):
    path, target = bench
    assert mutate.main(["--only", "b", str(path), "--", *_reads(target)]) == 0
    assert "other = 9" in capsys.readouterr().out


def test_a_spec_with_no_command_is_refused(bench):
    path, _target = bench
    with pytest.raises(SystemExit):
        mutate.main([str(path)])


# ── The mutation, and the restore ────────────────────────────────────────────


def test_the_command_sees_the_defect_and_the_tree_does_not(bench, capsys):
    path, target = bench
    mutate.main([str(path), "--", *_reads(target)])
    assert "value = 9|other = 9" not in capsys.readouterr().out  # one at a time
    assert target.read_text() == BODY


def test_each_mutation_starts_from_the_original(bench, capsys):
    """`b` must not run on top of `a`."""
    path, target = bench
    mutate.main([str(path), "--", *_reads(target)])
    lines = [l for l in capsys.readouterr().out.splitlines() if "|" in l]
    assert "value = 9|other = 2" in lines[0]
    assert "value = 1|other = 9" in lines[1]


def test_an_anchor_that_missed_is_refused_and_nothing_is_written(tmp_path,
                                                                monkeypatch,
                                                                capsys):
    """A count is a claim.  A mutation that was never applied would
    otherwise report a green that means nothing."""
    monkeypatch.setattr(mutate, "ROOT", tmp_path)
    target = tmp_path / "thing.py"
    target.write_text(BODY)
    path = tmp_path / "spec.json"
    path.write_text(json.dumps([
        {"id": "a", "what": "an anchor that is not there",
         "edits": [["thing.py", "value = 3", "value = 9", 1]]},
        {"id": "b", "what": "an anchor claimed twice and present once",
         "edits": [["thing.py", "value = 1", "value = 9", 2]]},
    ]))
    assert mutate.main([str(path), "--", sys.executable, "-c", "pass"]) == 1
    out = capsys.readouterr().out
    assert out.count("REFUSED") == 2
    assert target.read_text() == BODY


def test_a_file_someone_else_has_edited_is_refused(bench, monkeypatch):
    """The sweep's rule is a clean tree before and after, and a harness
    that mutates an edited file cannot put it back to anything."""
    path, target = bench
    monkeypatch.setattr(mutate, "dirty", lambda paths: list(paths))
    with pytest.raises(mutate.MutateError, match="already modified"):
        mutate.run(json.loads(path.read_text()), ["true"], None)
    assert target.read_text() == BODY


# ── The signal, which is why the tool exists ─────────────────────────────────


KILLED = '''
import importlib.util, os, pathlib, signal, sys
spec = importlib.util.spec_from_file_location("mutate", {tool!r})
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ROOT = pathlib.Path({root!r})
tree = m.Tree(["thing.py"])
tree.arm()
assert tree.apply([["thing.py", "value = 1", "value = 9", 1]]) is None
assert "value = 9" in (pathlib.Path({root!r}) / "thing.py").read_text()
print("mutated", flush=True)
os.kill(os.getpid(), signal.SIGTERM)
'''


def test_a_killed_run_puts_the_file_back(tmp_path):
    """A `finally` covers an exception and does not cover a signal.

    On 2026-09-02 a killed batch-11 harness left `gestate/reactive.py`
    holding a deliberate bug in the working tree, where the next
    `git commit -a` would have taken it.  That is the whole reason this
    tool exists, so it is checked the way it happened: mutate, then kill.
    """
    target = tmp_path / "thing.py"
    target.write_text(BODY)
    done = subprocess.run(
        [sys.executable, "-c", KILLED.format(
            tool=str(ROOT / "tools" / "mutate.py"), root=str(tmp_path))],
        capture_output=True, text=True)

    assert "mutated" in done.stdout          # it really was on disk
    assert done.returncode == -15            # and the signal was not swallowed
    assert target.read_text() == BODY        # and the file came back


# ── --check ──────────────────────────────────────────────────────────────────


def test_check_reads_the_real_tree(capsys):
    """`--check` is what a session runs after any abnormal end to a batch,
    before anything is read or committed."""
    rc = mutate.main(["--check"])
    out = capsys.readouterr().out
    assert rc in (0, 1)
    assert ("the tree is clean" in out) == (rc == 0)
