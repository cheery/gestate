"""tools/limit.sh — the sitting, and the direction it may not run in.

The other piece `tools/seedaudit.py` found bare on 2026-08-22.  It is
the one instrument in this tree whose subject is Henri rather than the
program, and the property that matters is an asymmetry: **a session may
end a sitting and may never extend one.**  That is not a promise anybody
can keep by intending to, so it is checked here.

Two of these are regressions.  The previous session found both by
running the thing end to end, and `bash -n` passed on both:

* a session-closed sitting printed *"The 0 minutes are up"* instead of
  its reason, because a patch missed on indentation;
* the hook's state write dropped the reason field, so the *why* survived
  one read and vanished on the next prompt.

Nothing here touches the live sitting: `XDG_RUNTIME_DIR` and
`GESTATE_LIMIT_LOG` are pointed at a temporary directory.
"""

import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIMIT = ROOT / "tools/limit.sh"


class Desk:
    """One temporary desk: its own state file, its own log."""

    def __init__(self, tmp_path, claudecode=True):
        self.tmp = tmp_path
        self.log = tmp_path / "sittings.log"
        self.env = dict(os.environ,
                        XDG_RUNTIME_DIR=str(tmp_path),
                        GESTATE_LIMIT_LOG=str(self.log))
        if claudecode:
            self.env["CLAUDECODE"] = "1"
        else:
            self.env.pop("CLAUDECODE", None)
        self.state = tmp_path / f"gestate-sitting-{os.getuid()}"

    def run(self, *args, prompt=None):
        stdin = json.dumps({"prompt": prompt}) if prompt is not None else ""
        return subprocess.run(["bash", str(LIMIT), *args], env=self.env,
                              input=stdin, capture_output=True, text=True)

    def prompt(self, text):
        return self.run("--hook", prompt=text)

    def rewind(self, minutes):
        """Move this sitting's start back, so the limit can be reached
        without waiting for it."""
        started, last, limit, *why = self.state.read_text().split()
        started = int(started) - minutes * 60
        self.state.write_text(" ".join([str(started), last, limit, *why]) + "\n")

    def lines(self):
        return [l.split("\t") for l in self.log.read_text().splitlines()] \
            if self.log.exists() else []


def test_a_session_may_not_grant_itself_a_sitting(tmp_path):
    """The asymmetry, in the direction that matters.  `CLAUDECODE` is set
    for Henri's own `!` commands too, so this refuses him as well — which
    is why the real grant is a typed prompt and not this."""
    desk = Desk(tmp_path)
    r = desk.run("reset")
    assert r.returncode == 3
    assert "not granted from inside a session" in r.stderr
    assert not desk.state.exists()


def test_a_real_terminal_may(tmp_path):
    desk = Desk(tmp_path, claudecode=False)
    assert desk.run("reset").returncode == 0
    assert desk.state.exists()


def test_the_typed_word_grants_and_never_reaches_the_session(tmp_path):
    """Exit 2 on UserPromptSubmit discards the prompt.  `sitting 45` is a
    control word, so the session must never see it as a question."""
    desk = Desk(tmp_path)
    r = desk.prompt("sitting 45")
    assert r.returncode == 2
    assert "45 minutes" in r.stderr
    assert desk.state.read_text().split()[2] == "45"


def test_the_bare_word_is_the_short_default(tmp_path):
    desk = Desk(tmp_path)
    assert desk.prompt("sitting").returncode == 2
    assert desk.state.read_text().split()[2] == "15"


def test_a_question_that_merely_mentions_it_is_not_a_grant(tmp_path):
    """The regex is anchored on purpose.  If asking *about* the
    instrument extended the sitting, the instrument would be a
    formality — and a session can put those words in his mouth by
    quoting them back."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    desk.rewind(60)
    r = desk.prompt("what does `sitting 90` do?")
    assert r.returncode == 2
    assert "minutes are up" in r.stderr


def test_a_prompt_inside_the_limit_passes(tmp_path):
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    assert desk.prompt("a real question").returncode == 0


def test_a_prompt_past_the_limit_is_blocked(tmp_path):
    desk = Desk(tmp_path)
    desk.prompt("sitting 20")
    desk.rewind(21)
    r = desk.prompt("one more thing")
    assert r.returncode == 2
    assert "The 20 minutes are up" in r.stderr
    assert "sitting 45" in r.stderr, "the way back in has to be in the message"


def test_a_session_may_end_one(tmp_path):
    """The other direction, which is open."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    assert desk.run("stop", "the thing you came for is done").returncode == 0
    assert desk.prompt("something else").returncode == 2


def test_a_closed_sitting_says_why_and_not_zero_minutes(tmp_path):
    """Regression, defect one.  The closed branch never fired, so a
    session-closed sitting reported *"The 0 minutes are up"* — true, and
    useless, and it hid the one thing the close was for."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    desk.run("stop", "the export bug is fixed")
    r = desk.prompt("next")
    assert "the export bug is fixed" in r.stderr
    assert "0 minutes are up" not in r.stderr


def test_the_reason_survives_more_than_one_read(tmp_path):
    """Regression, defect two.  The hook's state write dropped the reason
    field, so the *why* was there on the first blocked prompt and gone on
    the second — the worst shape for a message whose whole job is to be
    read by somebody who came back."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    desk.run("stop", "the export bug is fixed")
    desk.prompt("next")
    r = desk.prompt("and again")
    assert "the export bug is fixed" in r.stderr


def test_the_log_records_the_events_and_never_the_prompt(tmp_path):
    """The privacy claim, checked rather than promised.  The log exists
    to settle GESTATE_LIMIT_GAP; it is kept outside the repo, and what a
    person typed is not what it is for."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    desk.prompt("a private question about something")
    desk.rewind(60)
    desk.prompt("blocked now")
    desk.run("stop", "done")

    events = [row[1] for row in desk.lines()]
    assert events == ["grant", "prompt", "block", "close"]
    body = desk.log.read_text()
    assert "a private question" not in body
    assert "blocked now" not in body


def test_a_gap_of_silence_starts_a_fresh_sitting(tmp_path):
    """The shape of the actual problem: logging in for one small thing.
    The number this uses is the one `tools/gapcheck.py` is measuring."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 45")
    started, _, limit, *_ = desk.state.read_text().split()
    long_ago = int(time.time()) - 40 * 60
    desk.state.write_text(f"{started} {long_ago} {limit}\n")
    desk.prompt("back the next morning")
    assert desk.state.read_text().split()[2] == "15", \
        "a fresh sitting is the short default, not the length last granted"


def test_reading_the_clock_grants_nothing(tmp_path):
    """A session may read freely — the one thing it may do with the
    instrument besides ending a sitting."""
    desk = Desk(tmp_path)
    desk.prompt("sitting 20")
    before = desk.state.read_text()
    r = desk.run()
    assert r.returncode == 0
    assert "20" in r.stdout
    assert desk.state.read_text().split()[:3] == before.split()[:3]
