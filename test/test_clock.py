"""`tools/clock.sh` — the wrist clock, which lied downwards for two hours.

**Why this file exists at all.**  The clock's own argument is that *an
elapsed time is computed, never remembered*, because a session has no
felt duration and a dense day reads as a long one.  Two and a half hours
after it was built it rendered 1h58m as `1h`, and Henri — who had said
"about two hours" and was right to within two minutes — read it and
retracted a true statement (F169).

That is not an ordinary off-by-one.  A truncating unit conversion in a
*reporting* path is a biased estimator wearing the clothes of a
measurement, and it spends its error in the one place the tool is for:
the moment somebody checks the number against what they remember.  So
what is pinned here is the **boundary**, at every unit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CLOCK = ROOT / "tools" / "clock.sh"


def clock_in_a_repo(tmp_path, seconds_ago: int) -> str:
    """A throwaway repository whose one commit is `seconds_ago` old.

    The buggy path was the `last commit … (X ago)` line, which reads the
    commit's own `%ct` — so the only honest way to exercise it is to make
    a commit at a chosen time and let the script do its arithmetic.
    """
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "clock.sh").write_bytes(CLOCK.read_bytes())
    (repo / "tools" / "clock.sh").chmod(0o755)

    def git(*args, **env):
        subprocess.run(["git", *args], cwd=repo, check=True,
                       capture_output=True, env={**BASE_ENV, **env})

    import os
    import time
    BASE_ENV = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "home"),
        # Keep the workbench line out: `presence.tsv` is the real
        # machine's and would make this test read somebody's afternoon.
        "XDG_STATE_HOME": str(tmp_path / "state"),
        "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    (tmp_path / "home").mkdir()
    git("init", "-q")
    (repo / "a").write_text("a\n")
    git("add", "a")
    when = time.strftime("%Y-%m-%dT%H:%M:%S",
                         time.localtime(time.time() - seconds_ago))
    git("commit", "-qm", "one", GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)

    r = subprocess.run([str(repo / "tools" / "clock.sh")], cwd=repo,
                       capture_output=True, text=True, env=BASE_ENV)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_an_hour_and_fifty_eight_minutes_is_not_an_hour(tmp_path):
    """F169, exactly as it happened.

    `1h` for 1h58m discards fifty-eight minutes and discards them one
    way — the reading is never too large.  Henri had said "2 hours or
    so"; the clock said `1h`; he believed the clock.
    """
    out = clock_in_a_repo(tmp_path, 3600 + 58 * 60)
    assert "1h58m" in out, f"the clock truncated again:\n{out}"
    assert "(1h ago)" not in out


@pytest.mark.parametrize("seconds, shown", [
    (3599, "59m"),        # the last minute before the unit changes
    (3600, "1h00m"),      # and the first one after it
    (86399, "23h59m"),    # a whole day, still counted in hours
    (172799, "47h59m"),   # the last hour before days take over
    (172800, "2d0h"),     # and the first one after
])
def test_every_boundary_keeps_the_smaller_unit(tmp_path, seconds, shown):
    """Two units, always.  A bare `2d` hides up to twenty-three hours."""
    assert shown in clock_in_a_repo(tmp_path, seconds)
