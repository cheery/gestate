"""`tools/pre-commit.sh` — the gates, at the commit that breaks them.

Until 2026-08-24 no test named this file: `tools/seedaudit.py` scored
"the gates" as backed because `tools/suite.py` was mentioned somewhere,
and the mutation sweep (`tools/seedmutate.sh`) showed the hook could
vanish unnoticed.  `journal.md` §"The hook that was not committed" is
the incident that makes that worth a test.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "tools" / "pre-commit.sh"


def sh(*args, cwd=ROOT):
    return subprocess.run(["sh", str(HOOK), *args], cwd=cwd, capture_output=True, text=True)


def test_the_hook_parses():
    assert subprocess.run(["sh", "-n", str(HOOK)]).returncode == 0


def test_the_hook_runs_the_gates_and_nothing_else():
    """What the hook does at a commit is `tools/suite.py --gates`.  A hook
    that ran the whole suite would be the seventeen seconds the card was
    built to end; one that ran nothing would be the shim with no body.

    **It asks for the invocation, not for one spelling of the
    interpreter.**  Written on 2026-08-24 as `"python3 tools/suite.py
    --gates" in text`, it went red the same day the hook learned to find
    a virtualenv's python and call it `"$PY"` — and stayed red until
    2026-08-25, because this check lives in the long pass and the long
    pass was not run to completion in between.  That is the lesson of
    `tools/leash.sh`'s own header applied to the file next door: *a gate
    that fails closed on a spelling change is a gate people learn to wave
    past.*  So the assertion is on the arguments, and the interpreter is
    whatever the hook decided to be.
    """
    text = HOOK.read_text(encoding="utf-8")
    runs = [l.strip() for l in text.splitlines()
            if "tools/suite.py" in l and not l.lstrip().startswith("#")]
    assert runs, "the hook does not run tools/suite.py at all"
    assert all("--gates" in l for l in runs), (
        "the hook runs the suite without --gates somewhere, which is the "
        "whole suite at every commit:\n  " + "\n  ".join(runs))


def test_the_hook_is_installed_in_this_clone():
    """Per clone, and deliberately: a copy of this tree that has not run
    `--install` has the gates only when somebody remembers, which is the
    state the hook was built to end.  So a fresh clone is red here until
    it installs, and that is the finding, not a broken test."""
    r = sh("--check")
    assert r.returncode == 0, r.stdout + r.stderr


def test_an_unknown_argument_is_refused_out_loud():
    r = sh("--bogus")
    assert r.returncode == 2
    assert "unknown argument" in r.stderr


def test_install_check_uninstall_in_a_scratch_repository(tmp_path):
    """The three verbs, against a repository that is not this one."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "tools").mkdir()
    copy = tmp_path / "tools" / "pre-commit.sh"
    copy.write_text(HOOK.read_text(encoding="utf-8"))
    run = lambda *a: subprocess.run(["sh", str(copy), *a], cwd=tmp_path, capture_output=True, text=True)
    assert run("--check").returncode == 1
    assert run("--install").returncode == 0
    assert run("--check").returncode == 0
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert "gestate:tools/pre-commit.sh" in hook.read_text()
    assert run("--uninstall").returncode == 0
    assert not hook.exists()


def test_somebody_elses_hook_is_not_overwritten(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "tools").mkdir()
    copy = tmp_path / "tools" / "pre-commit.sh"
    copy.write_text(HOOK.read_text(encoding="utf-8"))
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho theirs\n")
    r = subprocess.run(["sh", str(copy), "--install"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 3
    assert hook.read_text() == "#!/bin/sh\necho theirs\n"
