"""A session, recorded and replayed — `spec/verification.md`, built.

    A session is a list of commands, so recording, replaying and testing
    stop being three mechanisms and become one.

The editor's half of this project has no oracle, and it is where every
defect has come from: nine in the Python around the engine, twelve in
the editor rewrite, six more the session after — all found by a person,
none by a test, with two thousand tests passing throughout.

**A transcript does not find any of those.**  It keeps them.  So what is
checked here is the keeping: that a session records, that it reads back
as what it was, and that replaying it gives the same answers — because a
recording that replayed differently would be a reproduction of nothing.
"""

from __future__ import annotations

from pathlib import Path

from gestate.session import Detached, Session
from gestate.sessionlog import Step, editing, read, replay


class Bench:
    """A workbench that answers, and remembers nothing it need not."""

    has_knob = True

    def __init__(self, path):
        self.path = path
        self.sites, self.banks, self.holes, self.loose = [], [], [], []
        self.values = {"cutoff": 40}
        self.knob_types = {"cutoff": "Int"}
        self.ranges = {"cutoff": (0, 100)}
        self.on, self.octaves, self.ends = False, 0, 32.0
        self.keyboard = self

    def knob_range(self, name):
        return self.ranges[name]

    def set_value(self, name, value):
        self.values[name] = value

    def seek_beats(self, beat):
        pass

    def set_loop(self, a, b):
        pass

    def clear_loop(self):
        pass

    def toggle(self):
        self.on = not self.on
        return self.on

    def pause(self):
        self.on = False

    def transpose(self, by):
        self.octaves += by
        return self.octaves

    def end_beat(self):
        return self.ends

    def source(self):
        return ""


A_SESSION = [("play",), ("seek", 4), ("set", "cutoff", 70),
             ("octave", -1), ("loopAll",), ("play",)]


def _ran(tmp_path):
    """A session that has done a few things."""
    s = Session(bench=Bench(tmp_path / "demo.ges"), view=Detached())
    for call in A_SESSION:
        s.run(*call)
    return s


def test_a_session_records_itself_without_being_asked(tmp_path):
    """**Always on.**  A transcript is wanted *after* something has gone
    wrong, and a command that had to be pressed first would be one you
    press after reproducing the fault a second time."""
    s = _ran(tmp_path)
    assert s.log is not None
    assert [step.verb for step in s.log.steps] == [c[0] for c in A_SESSION]
    assert s.log.steps[1].args == (4,)
    # The answers are recorded too — they are what a diff is taken on.
    assert s.log.steps[1].said == "at bar 4"


def test_a_refusal_is_recorded_as_much_as_a_success():
    """Often the more interesting one: what a command answered *is* the
    transcript, and a refusal is an answer."""
    s = Session(bench=Bench(Path("nowhere.ges")), view=Detached())
    s.run("listen", "nosuchbank")
    assert s.log.steps[-1].verb == "listen"
    assert s.log.steps[-1].said, "the refusal was not written down"


def test_it_reads_back_as_what_it_was(tmp_path):
    """The file is the record, so the file has to survive the trip."""
    s = _ran(tmp_path)
    steps = read(s.log.text())
    assert [(x.verb, x.args) for x in steps] == \
           [(y.verb, y.args) for y in s.log.steps]
    # Text stays text and numbers stay numbers, which is the only
    # distinction the reader has to make.
    assert Step("set", ("cutoff", 70)).line().strip().startswith(
        'set "cutoff" 70')


def test_a_replay_says_what_it_said_before(tmp_path):
    """**An empty answer is the whole point.**  A session that replays
    to the same sentences is one this build still behaves the way it did
    when somebody was sitting in front of it."""
    first = _ran(tmp_path)
    steps = read(first.log.text())
    again = Session(bench=Bench(tmp_path / "demo.ges"), view=Detached())
    assert replay(again, steps) == []
    assert again.said == first.said[:len(steps)]


def test_a_moved_answer_is_the_report(tmp_path):
    """What the tool is for: the step that no longer agrees, named."""
    s = _ran(tmp_path)
    steps = read(s.log.text())
    steps[1].said = "at bar 9"            # as if the build had moved
    again = Session(bench=Bench(tmp_path / "demo.ges"), view=Detached())
    drifted = replay(again, steps)
    assert [(d[0].verb, d[1]) for d in drifted] == [("seek", "at bar 4")]


def test_a_transcript_says_what_it_was_recorded_against(tmp_path):
    """**Only honest replayed against the same program.**  A fresh
    workbench on the same file is the same starting state; any other
    file is a different session wearing these commands."""
    s = _ran(tmp_path)
    assert editing(s.log.text()) == str(tmp_path / "demo.ges")
    assert editing("do\n    play\n") == ""


def test_writing_it_out_is_a_command(tmp_path):
    s = _ran(tmp_path)
    said = s.run("transcript", "")
    out = tmp_path / "demo-session.ges"
    assert out.exists(), said
    assert said.endswith("steps")
    # **Not `demo.ges`.**  Proposing the name of the file being edited
    # would offer to write the session over the program it recorded.
    assert out.name != "demo.ges"
    assert "seek 4" in out.read_text()


def test_nothing_to_write_says_so():
    s = Session(bench=Bench(Path("x.ges")), view=Detached())
    assert s.run("transcript", "") == "nothing has happened yet"


def test_a_line_it_cannot_read_costs_that_line_and_not_the_file():
    """A transcript is read long after it was written, by a build that
    may have moved on.  Losing the reproduction is what must not
    happen."""
    steps = read("# a header\ndo\n    play   #= playing\n    \n"
                 "    seek 2  #= at bar 2\n")
    assert [s.verb for s in steps] == ["play", "seek"]
