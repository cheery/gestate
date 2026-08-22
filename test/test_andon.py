"""tools/andon.sh — the cord, and the one failure a cord may not have.

The andon is one of the two pieces `tools/seedaudit.py` found bare on
2026-08-22: present, promised by four documents, and with nothing behind
it.  It is also the piece that carries the most weight in the audit's
first half, because it is the affordance a session is told it has — *you
can raise a question and reach a person who answers.*

**Nothing here rings anything.**  `python` and `sleep` are stubbed on
`PATH`, so what is checked is the part that can be wrong silently: how
many times it would ring, and whether a failed ring is loud.
"""

import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANDON = ROOT / "tools/andon.sh"


def stubs(tmp_path, exit_code=0):
    """A `python` that records each call instead of making a sound, and a
    `sleep` that does not.  Eight seconds between rings is right for a
    person and wrong for a gate."""
    log = tmp_path / "rings"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "python").write_text(
        f"#!/bin/sh\necho \"$@\" >> {log}\nexit {exit_code}\n")
    (bindir / "sleep").write_text("#!/bin/sh\nexit 0\n")
    for f in bindir.iterdir():
        f.chmod(0o755)
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}")
    return log, env


def run(env, *args):
    return subprocess.run(["sh", str(ANDON), *args], env=env,
                          capture_output=True, text=True)


def rings(log):
    return log.read_text().splitlines() if log.exists() else []


def test_one_ring_by_default(tmp_path):
    log, env = stubs(tmp_path)
    assert run(env).returncode == 0
    assert len(rings(log)) == 1


def test_the_cap_is_three(tmp_path):
    """Stated in the script's own comment: three calls that did not reach
    him mean he is not in the room.  A comment is not a check."""
    log, env = stubs(tmp_path)
    assert run(env, "7").returncode == 0
    assert len(rings(log)) == 3


def test_zero_rings_once_rather_than_never(tmp_path):
    """The script clamps up, deliberately.  A cord asked for zero rings
    and giving zero has failed quietly, which is the thing it may not
    do."""
    log, env = stubs(tmp_path)
    assert run(env, "0").returncode == 0
    assert len(rings(log)) == 1


def test_a_typo_is_refused_out_loud(tmp_path):
    """`tools/andon.sh oops` must not ring zero times and exit clean —
    the script says so in a comment, and this is the check."""
    log, env = stubs(tmp_path)
    r = run(env, "oops")
    assert r.returncode == 2
    assert "not a number of rings" in r.stderr
    assert rings(log) == []


def test_a_ring_that_does_not_reach_the_card_is_loud(tmp_path):
    """The worst available failure: a session pulls the cord, nothing
    sounds, and the exit status says everything is fine."""
    log, env = stubs(tmp_path, exit_code=1)
    r = run(env, "1")
    assert r.returncode != 0
    assert "could not reach the sound card" in r.stderr


def test_the_sound_it_promises_exists():
    """The script names `tools/andon.ges` and a stranger's copy of this
    tree may not have it — which is `tools/seedaudit.py`'s second check,
    applied to the one file the cord actually needs."""
    assert (ROOT / "tools/andon.ges").is_file()
