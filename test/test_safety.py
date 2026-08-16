"""The safety machinery, checked by something that is not a person's attention.

**Four things can now stop working silently**, and until this file existed
exactly one of them was checked by anything — `tools/sandbox.sh --check`,
run by hand, when somebody remembered:

* the **fence** (`tools/sandbox.sh`) — no `~/.ssh`, no network, nothing
  writable but the project;
* the **leash** (`.claude/settings.json`, read by `tools/leash.sh`) — the
  deny-list that a malformed file silently disables in full;
* the **hook** (`tools/fence-hook.sh`) — which decides what gets fenced,
  and which broke a working command the first time it ran;
* the **AppArmor profile** — without which the fence cannot start at all
  on Ubuntu 24.04.

`spec/sandbox.md` is the argument for all four.  This is the oracle for
it, and the reason it is a test rather than a script is `manifesto.md`
rule 2: *what is built must be able to say when it is wrong, and visible
to something that is not a person's attention, because attention is what
runs out.*

**These run OUTSIDE the fence, and must.**  A `bwrap` cannot nest — the
inner one cannot create the namespaces it wants — so every probe here
would fail for the wrong reason inside a fenced run.  `tools/sandbox.sh`
sets `GESTATE_FENCED=1`, this file skips on it, and `tools/suite.py` runs
this file in the same unfenced second pass it uses for the window tests.
That is a real gap and it is stated rather than hidden: **run under
`python tools/suite.py`, not a bare fenced `pytest`, or these do not
run.**

The failures worth having: a fence that stops fencing, a deny-list that
stopped applying, a hook that wraps `grep pytest notes.txt`.  All three
happened on 2026-08-16.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

pytestmark = pytest.mark.skipif(
    os.environ.get("GESTATE_FENCED") == "1",
    reason="the fence cannot nest; tools/suite.py runs these unfenced",
)

needs_bwrap = pytest.mark.skipif(
    subprocess.run(["sh", "-c", "command -v bwrap"], capture_output=True).returncode != 0,
    reason="bubblewrap not installed — see doc/hardening.md",
)


def _hook(command: str) -> str | None:
    """What the hook would turn `command` into, or None for untouched."""
    out = subprocess.run(
        [str(TOOLS / "fence-hook.sh")],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True, text=True,
    ).stdout.strip()
    if not out:
        return None
    return json.loads(out)["hookSpecificOutput"]["updatedInput"]["command"]


def _fenced(script: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(TOOLS / "sandbox.sh"), "sh", "-c", script],
                          capture_output=True, text=True, cwd=ROOT)


# ── The fence ────────────────────────────────────────────────────────────

@needs_bwrap
def test_the_fence_says_it_is_up():
    """`--check` is the gate everything else trusts, so it is checked first.

    Thirteen probes; a non-zero exit means one of them disagreed, and the
    output names which.  If this fails on a new machine the cause is
    almost always the AppArmor profile (`doc/hardening.md` §2.3).
    """
    r = subprocess.run([str(TOOLS / "sandbox.sh"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"the fence is not up:\n{r.stdout}{r.stderr}"
    assert "the fence is up" in r.stdout


@needs_bwrap
def test_the_ssh_key_is_not_merely_denied_but_absent():
    """Absent, not unreadable — the distinction the fence is built on.

    `$HOME` inside is an empty tmpfs, so there is nothing to deny.
    """
    assert _fenced('test -e "$HOME/.ssh"').returncode != 0
    assert _fenced('cat "$HOME/.ssh/id_ed25519"').returncode != 0


@needs_bwrap
def test_there_is_no_network():
    """A build script that phones home gets nowhere.

    Resolution rather than a connection: a DNS lookup is the cheapest
    thing that proves the namespace is unshared, and it cannot hang past
    the timeout.
    """
    assert _fenced("timeout 5 getent ahostsv4 github.com").returncode != 0


@needs_bwrap
def test_a_write_to_home_does_not_escape():
    """Graded from outside, because a sandbox cannot grade its own escape.

    `$HOME` inside is writable on purpose — cargo, pytest and git all
    want a home — so what must hold is that the writes do not survive.
    """
    sentinel = Path.home() / ".gestate-test-escape-probe"
    sentinel.unlink(missing_ok=True)
    _fenced(f'touch "$HOME/{sentinel.name}"')
    escaped = sentinel.exists()
    sentinel.unlink(missing_ok=True)
    assert not escaped, f"a write inside the fence reached {sentinel}"


@needs_bwrap
def test_the_project_is_writable_and_usr_is_not():
    """The fence has to be usable, which is a separate claim from tight."""
    assert _fenced("touch .safety-probe && rm .safety-probe").returncode == 0
    assert _fenced("touch /usr/.safety-probe").returncode != 0


# ── The leash ────────────────────────────────────────────────────────────

def test_the_leash_is_on():
    """A malformed settings.json disables every rule in it, silently.

    That is the failure this guards: not a wrong rule, but no rules and
    no symptom.
    """
    r = subprocess.run([str(TOOLS / "leash.sh")], capture_output=True, text=True)
    assert r.returncode == 0, f"the leash is off:\n{r.stdout}{r.stderr}"


def test_the_leash_cannot_be_edited_by_the_thing_it_restrains():
    """An agent that can edit its own leash does not have one.

    Checked separately from `leash.sh`'s own list because this is the
    rule the others depend on: remove it and the rest can be removed.
    """
    deny = json.loads((ROOT / ".claude" / "settings.json").read_text())
    deny = deny["permissions"]["deny"]
    assert "Edit(./.claude/**)" in deny


# ── The hook ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("command", [
    "pytest -q",
    "python3 -m pytest test/test_arith.py",
    "cargo build --offline",
    "cargo test",
    "cd test && pytest -q",
])
def test_things_that_execute_dependency_code_are_fenced(command):
    got = _hook(command)
    assert got is not None, f"{command!r} would have run unfenced"
    assert "tools/sandbox.sh" in got


@pytest.mark.parametrize("command", [
    # The regression that broke a real command: the `|` inside the awk
    # pattern read as a pipe, so `|pytest` looked like a command position.
    r"""ps -eo args= | awk '/suite\.py|pytest/ {print}'""",
    "grep pytest notes.txt",
    'echo "cargo build"',
    # Wants the network the fence removes.
    "cargo fetch",
    # Opens a window; the fence binds no X11 socket.
    "python3 -m gestate.workbench",
    # The visible opt-out.
    "NOFENCE=1 pytest -q",
    # Already inside; wrapping twice is not tighter.
    "tools/sandbox.sh pytest -q",
])
def test_things_that_must_not_be_wrapped(command):
    assert _hook(command) is None, f"{command!r} was wrapped and should not be"


def test_a_wrapped_command_still_runs():
    """The question a decision test cannot answer.

    The first version of the hook decided correctly and produced a
    command bash could not parse: `jq -Rs '@sh'` returns the shell
    quoting still JSON-encoded, so the escapes arrived doubled.  Nested
    quotes are the case that exposed it.
    """
    wrapped = _hook('python3 -m pytest test/test_arith.py -q -k "not nothing" -p no:randomly')
    assert wrapped is not None
    r = subprocess.run(["bash", "-c", wrapped], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, f"a wrapped command failed to run:\n{r.stdout}{r.stderr}"
    assert "passed" in r.stdout
