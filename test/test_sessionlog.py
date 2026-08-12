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

from gestate.session import Detached, Session, act
from gestate.sessionlog import (ASK, Step, editing, read, replay,
                                world_dependent)


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


# ── Typing ───────────────────────────────────────────────────────────────


class Typed(Bench):
    """A bench whose view holds text, so a session can be typed into."""


def _typing(tmp_path, text):
    from gestate.sessionlog import Typing

    class View(Typing):
        showing = "source"

    return View(text, under=Detached())


def test_the_typing_is_recorded_and_not_only_the_commands(tmp_path):
    """**The half that had to be written by hand.**

    A transcript that recorded `audition` and not the line just changed
    was a reproduction you had to annotate before anybody could use it —
    Henri wrote *"# write to end of line 10: + lead"* into one, which is
    the report saying what the tool was missing.
    """
    view = _typing(tmp_path, "a = 1\nb = 2\n")
    s = Session(bench=Bench(tmp_path / "demo.ges"), view=view)
    s.run("seek", 4)
    view.retype(["a = 1", "b = 2 + lead"])
    s.run("octave", -1)

    kinds = [step.verb for step in s.log.steps]
    assert kinds == ["seek", "edit", "octave"], kinds
    # **Between commands, not per keystroke.**  A step per character
    # would bury the things somebody did under the ones they did not
    # think of as doing anything.
    edit = s.log.steps[1]
    assert edit.said == "1 line changed"
    # And it reads as a diff, which is what a person opens it for.
    shown = "\n".join(edit.shown)
    assert "-   2 b = 2" in shown and "+   2 b = 2 + lead" in shown


def test_the_file_as_opened_is_not_recorded_as_typing(tmp_path):
    """A transcript that opened by "adding" the whole file would bury the
    one line that mattered."""
    view = _typing(tmp_path, "a = 1\nb = 2\n")
    s = Session(bench=Bench(tmp_path / "demo.ges"), view=view)
    s.run("seek", 4)
    assert [step.verb for step in s.log.steps] == ["seek"]


def test_a_replay_types_what_was_typed(tmp_path):
    """Read and not *done* would make a transcript describe a
    reproduction it could not perform."""
    from gestate.sessionlog import Typing

    view = _typing(tmp_path, "a = 1\nb = 2\n")
    s = Session(bench=Bench(tmp_path / "demo.ges"), view=view)
    s.run("seek", 4)
    view.retype(["a = 1", "b = 2 + lead", "c = 3"])
    s.run("octave", -1)

    steps = read(s.log.text())
    again = _typing(tmp_path, "a = 1\nb = 2\n")
    drifted = replay(Session(bench=Bench(tmp_path / "demo.ges"), view=again),
                     steps, again)
    assert drifted == []
    assert again.text() == view.text(), "the typing did not come back"
    assert isinstance(again, Typing)


def test_the_edits_survive_the_file(tmp_path):
    """Exact, not descriptive: the ops reconstruct the text."""
    from gestate.sessionlog import _apply, _ops

    before = ("a", "b", "c", "d")
    for after in (("a", "B", "c", "d"), ("a", "d"), ("a", "b", "c", "d", "e"),
                  ("x",), (), ("a", "b", "c", "d")):
        assert _apply(before, _ops(before, after)) == after, after


def test_a_long_paste_is_shown_short(tmp_path):
    """A pasted template is thirty lines nobody needs to read back — the
    ops keep all of it and the reading stops."""
    view = _typing(tmp_path, "")
    s = Session(bench=Bench(tmp_path / "demo.ges"), view=view)
    s.run("seek", 0)
    view.retype([f"line {i}" for i in range(40)])
    s.run("seek", 1)
    edit = next(step for step in s.log.steps if step.verb == "edit")
    assert len(edit.shown) <= 13, edit.shown
    assert "more" in edit.shown[-1]
    # But nothing is lost: it still replays exactly.
    from gestate.sessionlog import _apply
    assert _apply((), edit.args) == tuple(f"line {i}" for i in range(40))


# ── The questions ───────────────────────────────────────────────────────────
#
# **`Session.run` was recorded and `Session.choices` was not**, and the
# questions are where the defects have been: a dialog that offered the
# wrong rows replayed as a session saying all the right sentences.  The
# first bug a user of this editor reported lived exactly there — an open
# dialog whose listing never refreshed — and no transcript could have
# shown it.


def _asked(tmp_path, queries, then=("open", "two.ges")):
    """A session that opened a dialog, typed, and ran the command."""
    room = tmp_path / "room"
    room.mkdir(exist_ok=True)
    for name in ("one.ges", "two.ges"):
        (room / name).write_text("sound : Sig Float\n")
    s = Session(bench=Bench(room / "one.ges"), view=Detached())
    for query in queries:
        act(s, f"wants\topen\t0\t{query}")
        s.choices()
    s.run(*then)
    return s, room


def test_a_dialog_is_one_step_however_much_was_typed(tmp_path):
    """**The budget, and the reason the collapse exists.**

    A `wants` gesture arrives on every character, so recorded as they
    come a dialog is five steps a second — and `KEEP` is four thousand,
    so a dialog-heavy sitting would push the run-up to the fault off the
    top of the transcript that exists to hold it.  `Log.typed` refuses
    the same bargain for text, in the same words.
    """
    s, _room = _asked(tmp_path, ("", "t", "tw", "two"))
    asks = [step for step in s.log.steps if step.verb == ASK]
    assert len(asks) == 1, "one dialog, one step"
    assert asks[0].args == ("open", 0, "Path", "two"), "the query as it ended"
    # How many times the list was worked out rides as a comment: it is
    # for the reader, and must stay out of `said`, which a replay diffs.
    assert asks[0].shown == ("4 looks",)
    assert "look" not in asks[0].said


def test_the_answer_is_a_digest_and_not_the_listing(tmp_path):
    """40× cheaper, measured: `examples/audio` is 1.9 KB of rows against
    48 bytes for the question and a digest.  The engine half settled
    this — `spec/verification.md` keeps a hash of every rendered block."""
    s, _room = _asked(tmp_path, ("",))
    said = next(x for x in s.log.steps if x.verb == ASK).said
    assert said.startswith("3 rows "), said       # `../`, one.ges, two.ges
    assert len(said) < 40, "a listing would be a great deal longer"
    assert "one.ges" not in said, "the names are hashed, not kept"


def test_a_listing_that_moved_is_the_report(tmp_path):
    """The point of recording the question at all: replay re-asks it,
    and a different set of rows is a different digest."""
    s, room = _asked(tmp_path, ("",))
    steps = read(s.log.text())

    (room / "arrived.ges").write_text("sound : Sig Float\n")
    drifted = replay(Session(bench=Bench(room / "one.ges"),
                             view=Detached()), steps)
    moved = [step for step, _now in drifted if step.verb == ASK]
    assert moved, "the directory changed and the replay did not notice"


def test_the_same_directory_replays_to_the_same_digest(tmp_path):
    """**And an empty report is the whole point.**  A question re-asked
    against an unchanged directory must come back identical, or the
    oracle cries wolf on every run and stops being read."""
    s, room = _asked(tmp_path, ("",))
    steps = read(s.log.text())
    drifted = replay(Session(bench=Bench(room / "one.ges"),
                             view=Detached()), steps)
    assert [x for x, _n in drifted if x.verb == ASK] == []


def test_a_question_about_the_world_is_marked_as_one(tmp_path):
    """**The difference between a report somebody reads and one they
    learn to ignore.**  A `Path` answer is about the filesystem and the
    filesystem is allowed to move; a template or a symbol is a function
    of the program and must not.  The kind is recorded so the rule can
    be applied without a list of verbs kept anywhere."""
    s, _room = _asked(tmp_path, ("",))
    ask = next(x for x in s.log.steps if x.verb == ASK)
    assert world_dependent(ask)

    other = Session(bench=Bench(_room / "one.ges"), view=Detached())
    act(other, "wants\ttemplate\t0\t")
    other.choices()
    other.run("template", "knob")
    picked = next(x for x in other.log.steps if x.verb == ASK)
    assert picked.args[2] == "Template"
    assert not world_dependent(picked), "the program owns this answer"


def test_an_abandoned_dialog_leaves_no_step(tmp_path):
    """A question opened and walked away from is not what anybody is
    reproducing, and a step for it would be a step spent."""
    room = tmp_path / "room"
    room.mkdir(exist_ok=True)
    (room / "one.ges").write_text("sound : Sig Float\n")
    s = Session(bench=Bench(room / "one.ges"), view=Detached())
    act(s, "wants\topen\t0\t")
    s.choices()
    s.run("seek", 8)                     # something else entirely
    assert [x.verb for x in s.log.steps] == ["seek"]
