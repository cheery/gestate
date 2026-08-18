"""Walking the factory floor — `board/done/gemba.md`.

Henri's ask: *"a program in the workspace that lets me walk the factory
floor — Claude presents and comments to the editor, I see it through the
workspace."*  The inversion is the point: today he reads sixteen commit
messages afterwards; this is being where the work is while it happens.

**The design's one hard part is the rate**, and it is his finding:

> In one hand "what is happening now" would be great, but you're much
> faster than me.  I think the design should account for that.  Give me
> room that I need.

Neither end can own the pace — a narration paced by the writer is
unreadable, and a log paced by the reader is a report.  So the tests
below are mostly about that: one item at a time, held for as long as it
takes to read, and the backlog itself being the interesting reading.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gestate import gemba
from gestate.gemba import Item, Walk, dwell, say


@pytest.fixture(autouse=True)
def a_floor_of_ones_own(tmp_path, monkeypatch):
    """Never the project's own `gemba.tsv` — a test that narrated into
    somebody's open workbench would be typing on their screen."""
    monkeypatch.setenv("GESTATE_GEMBA", str(tmp_path / "gemba.tsv"))
    return tmp_path


class Clock:
    """A hand that only moves when a test moves it."""

    def __init__(self):
        self.at = 0.0

    def __call__(self) -> float:
        return self.at


# ── The channel ─────────────────────────────────────────────────────────────


def test_what_a_session_says_is_a_line_of_the_house_format(tmp_path):
    """Verb first, tab separated — the fifth thing here wearing that
    shape, and the reason `cat` is enough to debug it."""
    say("building the thing")
    assert (tmp_path / "gemba.tsv").read_text() == "say\tbuilding the thing\n"


def test_it_is_appended_never_rewritten(tmp_path):
    """Two sessions may be walking at once and neither should have to
    lock anything."""
    say("one")
    say("two")
    assert (tmp_path / "gemba.tsv").read_text().splitlines() == [
        "say\tone", "say\ttwo"]


def test_a_verb_it_does_not_know_is_skipped_rather_than_refused(tmp_path):
    """The writer may be newer than the window — `shot <path>` is the
    kind this most wants next, and it must not break a reader that
    predates it."""
    (tmp_path / "gemba.tsv").write_text(
        "say\tfirst\nshot\t/tmp/x.png\nsay\tsecond\n")
    walk = Walk()
    assert walk.read() == 2
    assert [i.text for i in walk.queue] == ["first", "second"]


def test_a_half_written_line_waits_for_its_newline(tmp_path):
    """A file being appended to while it is read gives a partial last
    line, and showing half a sentence is worse than showing it a poll
    later."""
    where = tmp_path / "gemba.tsv"
    where.write_text("say\twhole\nsay\thalf a th")
    walk = Walk()
    assert walk.read() == 1
    where.write_text("say\twhole\nsay\thalf a thought\n")
    assert walk.read() == 1
    assert [i.text for i in walk.queue] == ["whole", "half a thought"]


def test_an_unchanged_file_costs_one_stat(tmp_path):
    say("something")
    walk = Walk()
    assert walk.read() == 1
    assert walk.read() == 0, "nothing has been said since"


def test_a_file_that_shrank_is_a_new_walk(tmp_path):
    """Deleting it is how you clear the board, so the sensible reading
    is *start again* rather than *the numbers are wrong now*."""
    say("one")
    say("two")
    walk = Walk()
    walk.read()
    (tmp_path / "gemba.tsv").write_text("say\tfresh\n")
    assert walk.read() == 1
    assert [i.text for i in walk.queue] == ["fresh"]


def test_nobody_narrating_costs_nothing(tmp_path):
    """The file does not exist until somebody says something, and a
    workbench nobody is walking past must not pay for the feature."""
    assert Walk().read() == 0


# ── The dwell: as long as it takes to read it ──────────────────────────────


def test_a_short_note_and_a_paragraph_do_not_get_the_same_room():
    """The whole of Henri's answer.  A constant would have forced
    somebody to pick a number that is wrong for one of them."""
    assert dwell("done") < dwell(" ".join(["word"] * 30))


def test_there_is_a_floor_so_a_glance_can_still_catch_it():
    assert dwell("done") == gemba.LEAST


def test_there_is_a_ceiling_so_nothing_holds_the_box_hostage():
    assert dwell(" ".join(["word"] * 500)) == gemba.MOST


# ── Paced to the reader ────────────────────────────────────────────────────


def test_one_thing_at_a_time_however_much_arrives(tmp_path):
    """**The reader's clock, not the writer's.**  This is the claim the
    whole card rests on: a session that says twenty things in a second
    does not put twenty things on the screen."""
    clock = Clock()
    walk = Walk(clock=clock)
    for i in range(20):
        say(f"thing {i}")
    walk.read()
    assert walk.showing().text == "thing 0"
    assert walk.showing().text == "thing 0", "and it stays"
    assert walk.behind == 19


def test_the_next_arrives_only_once_the_last_has_been_readable(tmp_path):
    clock = Clock()
    walk = Walk(clock=clock)
    say("first")
    say("second")
    walk.read()
    assert walk.showing().text == "first"
    clock.at = gemba.LEAST - 0.1
    assert walk.showing().text == "first", "not yet readable"
    clock.at = gemba.LEAST
    assert walk.showing().text == "second"


def test_the_depth_is_the_reading(tmp_path):
    """**The valuable line of the whole design.**  The rate mismatch
    stops being a defect to engineer away and becomes the instrument's
    most useful signal — *he is going faster than you are following* —
    which is `spec/author.md`'s standing problem made visible while it
    is happening instead of found in a commit log afterwards."""
    clock = Clock()
    walk = Walk(clock=clock)
    say("one")
    walk.read()
    walk.showing()
    assert walk.behind == 0
    for i in range(5):
        say(f"more {i}")
    walk.read()
    assert walk.behind == 5, "the box is running five behind"


def test_an_empty_queue_does_not_clear_the_box(tmp_path):
    """A box that empties itself is a box you have to watch rather than
    glance at."""
    clock = Clock()
    walk = Walk(clock=clock)
    say("the last thing")
    walk.read()
    assert walk.showing().text == "the last thing"
    clock.at = 1000.0
    assert walk.showing().text == "the last thing"


def test_a_window_redrawn_twice_as_often_does_not_advance_twice_as_fast(tmp_path):
    """Which is why the clock lives in the model: how long a thing has
    stood is a fact about the session, not about the window."""
    clock = Clock()
    walk = Walk(clock=clock)
    say("first")
    say("second")
    walk.read()
    for _ in range(50):
        walk.showing()
    assert walk.showing().text == "first"


# ── The box ────────────────────────────────────────────────────────────────


def _a_session(lines):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    class View:
        showing = "source"

        def __init__(self):
            self.typed = []

        def lines(self):
            return list(lines)

        def caret(self):
            return 0

        def insert(self, text):
            self.typed.append(text)
            return True

    it = session()
    it.view = View()
    return it


def _rows(it):
    from gestate.session import furniture

    return [l.split("\t") for l in furniture(it).splitlines()
            if l.startswith("gemba\t")]


def test_the_box_stands_on_the_gemba_line(tmp_path):
    """`canvas`'s manners, a fourth reading of machinery already built:
    one appended line asks, deleting it takes the box, no line no box."""
    it = _a_session(["sound : Sig Float", "gemba", ""])
    it.walk = Walk(clock=Clock())
    say("building the thing")
    it.walk.read()
    assert _rows(it) == [["gemba", "2", "building the thing", "0"]]


def test_no_line_no_box(tmp_path):
    it = _a_session(["sound : Sig Float", ""])
    it.walk = Walk(clock=Clock())
    say("building the thing")
    it.walk.read()
    assert _rows(it) == []


def test_one_box_however_many_lines_ask(tmp_path):
    """**The pace is the point**, so a second box would be a second
    thing to read at once — which is the failure this design is
    arranged against."""
    it = _a_session(["gemba", "x", "gemba", ""])
    it.walk = Walk(clock=Clock())
    say("one thing")
    it.walk.read()
    assert len(_rows(it)) == 1


def test_the_box_says_so_before_anything_has_been_said(tmp_path):
    it = _a_session(["gemba", ""])
    it.walk = Walk(clock=Clock())
    assert _rows(it) == [["gemba", "1", "nothing said yet", "0"]]


def test_the_depth_crosses_as_its_own_field(tmp_path):
    """So the window decides how to draw it and the model only says how
    far behind it is — a mark there, a number here."""
    it = _a_session(["gemba", ""])
    it.walk = Walk(clock=Clock())
    for i in range(4):
        say(f"thing {i}")
    it.walk.read()
    assert _rows(it)[0][3] == "3"


def test_a_workbench_with_no_walk_sends_no_row(tmp_path):
    it = _a_session(["gemba", ""])
    assert _rows(it) == []


# ── And the command line, which is what a session actually reaches for ─────


def test_a_session_narrates_with_one_command(tmp_path):
    assert gemba.main(["say", "reading", "the", "card"]) == 0
    assert (tmp_path / "gemba.tsv").read_text() == "say\treading the card\n"


def test_clearing_the_board_is_deleting_the_file(tmp_path):
    say("something")
    assert gemba.main(["clear"]) == 0
    assert not (tmp_path / "gemba.tsv").exists()
    assert gemba.main(["clear"]) == 0, "and clearing nothing is not an error"


# ── And the ask-line has to be invisible to the compiler ───────────────────


def test_a_gemba_line_does_not_break_the_program(tmp_path):
    """**Found by looking at the running window, not by reading.**

    The box drew perfectly on the first try and the file underneath it
    did not compile — *expected '=', got end of line* — so the first
    thing the feature did was break the program it was narrating about.
    Every other ask-line already knew to rewrite itself to a comment;
    this one was written without asking what the compiler would make of
    it, and the tests all passed because none of them compiled anything.
    """
    from gestate import audio

    src = "gemba\n\nsound : Sig Float\nsound = sine 220.0 * 0.2\n"
    assert len(list(audio.render(src, seconds=0.005, rate=8000))) > 0


def test_a_program_may_still_have_its_own_gemba(tmp_path):
    """The ask is a *bare* line, so a definition of that name is the
    author's — the same exemption `notes` has."""
    from gestate.audiovoices import expand

    src = "gemba : Float\ngemba = 3.0\n"
    assert "# gemba : Float" not in expand(src)


# ── What the first real walk found ────────────────────────────────────────
#
# Henri, 2026-08-18, the first time a session narrated at him:
#
#   > the first gemba walk didn't succeed.  I don't know how to subscribe
#   > to the gemba walk with my workbench.  But I can see the tool would
#   > work well.
#
# **Two defects, and neither was reachable from the source.**  Every test
# above passed while both were true, because every one of them set
# `GESTATE_GEMBA` and so never asked the question a person asks: *where
# is the file, and how do I get the box?*


def test_both_ends_find_the_same_file_from_anywhere_in_the_tree(monkeypatch,
                                                                tmp_path):
    """**The first defect, and it made the feature useless in silence.**

    The workbench rooted the walk at the *file's own directory* and a
    session's command line wrote to its *working directory*, so the two
    met only when the file being edited happened to sit at the top of
    the tree.  Nothing failed; nothing appeared either.
    """
    monkeypatch.delenv("GESTATE_GEMBA", raising=False)
    (tmp_path / ".git").mkdir()
    deep = tmp_path / "examples" / "audio"
    deep.mkdir(parents=True)
    piece = deep / "tuning.ges"
    piece.write_text("sound : Sig Float\n")

    assert gemba.path_for(tmp_path) == tmp_path / "gemba.tsv"
    assert gemba.path_for(deep) == tmp_path / "gemba.tsv"
    assert gemba.path_for(piece) == tmp_path / "gemba.tsv"


def test_a_tree_with_no_repository_still_answers(monkeypatch, tmp_path):
    """Walking up has to stop somewhere, and the honest stop is *here*."""
    monkeypatch.delenv("GESTATE_GEMBA", raising=False)
    loose = tmp_path / "loose"
    loose.mkdir()
    assert gemba.path_for(loose) == loose / "gemba.tsv"


def test_the_command_subscribes_without_touching_the_file(tmp_path):
    """**The second defect: the box was not findable** — and the first
    fix for it created a third.

    Writing a `gemba` line for you made the file *unsaved*, which
    tripped the walk's own refusal to take a file away from unsaved
    work — so subscribing was exactly what stopped it travelling.  Found
    by watching the real window sit still with a `[+]` in its corner.

    The better design was inside the collision: **the box's home is
    wherever the session is pointing**, not a line you had to remember
    to write.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import Editor, session
    from gestate.workbench import Window

    ed = Editor("sound : Sig Float\n")
    it = session()
    it.view = Window(ed)
    said = it.run("gemba")
    assert ed.orders == [], "it types nothing"
    assert it.walking is True
    assert "following the walk" in said, "and says where the channel is"


def test_the_command_says_whether_anybody_is_talking(tmp_path):
    """The other half of not being able to subscribe is not knowing
    whether there is anything to subscribe *to*."""
    it = _a_session(["sound : Sig Float", ""])
    it.walk = Walk(clock=Clock())
    say("a session is here")
    it.walk.read()
    assert "a session is talking" in it.run("gemba")


# ── Opening another file ──────────────────────────────────────────────────
#
# Henri, minutes after the walk started working:
#
#   AttributeError: 'NoneType' object has no attribute 'read'
#
# **A field was added to `Session` and nothing asked what happens when a
# `Session` is replaced.**  It is replaced on every `open`, by `_carry`,
# which builds a fresh one and hands it the things that belong to the
# *window* rather than to the instrument — the view, the log — and the
# walk was not among them.  So the first file anybody opened took the
# whole editor down, over a box nobody had asked for.


def test_opening_another_file_keeps_the_walk(tmp_path, monkeypatch):
    """It belongs to the window, like the view and the log."""
    monkeypatch.delenv("GESTATE_GEMBA", raising=False)
    from gestate.workbench import _walk_for

    (tmp_path / ".git").mkdir()
    one, two = tmp_path / "a.ges", tmp_path / "deep" / "b.ges"
    two.parent.mkdir()
    for f in (one, two):
        f.write_text("sound : Sig Float\n")

    walk = Walk(root=one)
    assert _walk_for(walk, two) is walk, "same project, same walk"


def test_a_file_in_another_project_is_another_walk(tmp_path, monkeypatch):
    """The channel is *under the project*, so following the file is what
    keeps that sentence true — a box quietly showing another tree's work
    is worse than a box showing none."""
    monkeypatch.delenv("GESTATE_GEMBA", raising=False)
    from gestate.workbench import _walk_for

    here, there = tmp_path / "here", tmp_path / "there"
    for d in (here, there):
        (d / ".git").mkdir(parents=True)
        (d / "p.ges").write_text("sound : Sig Float\n")

    walk = Walk(root=here / "p.ges")
    other = _walk_for(walk, there / "p.ges")
    assert other is not walk
    assert other.path == there / "gemba.tsv"


def test_a_session_with_no_walk_is_not_a_crash(tmp_path):
    """**A narration is a diagnostic, and a diagnostic that can take the
    editor down with it is worse than no diagnostic.**"""
    from gestate.workbench import _walk_for

    assert _walk_for(None, None) is None


# ── Travelling in the code ────────────────────────────────────────────────
#
# Henri, on the first version: *"'not travelling in code' means that the
# editor itself doesn't open a location, eg. `gestate/workbench.py`, and
# plant the box after a line you want to show.  That is, it's not
# travelling in the code."*  And afterwards: *"that's the point of the
# whole thing!  But this was a proof of concept that you built first.
# And it refined what I was requesting."*
#
# A `say` narrates from wherever the box stands.  An **`at`** takes you
# to the place — which is what *genba* means, and what the first version
# had only the report half of.


class _View:
    """A window that remembers what it was asked to open."""

    showing = "source"
    saved = True

    def __init__(self, lines):
        self._lines = list(lines)
        self.wanted = None
        self.typed = []
        self.went = []

    def lines(self):
        return list(self._lines)

    def text(self):
        return "\n".join(self._lines) + "\n"

    def caret(self):
        return 0

    def insert(self, text):
        self.typed.append(text)
        return True

    def open(self, path):
        self.wanted = path
        return True

    def goto(self, line):
        self.went.append(line)
        self.caret_line = line
        return True

    def caret(self):
        #: A character offset, the way the window answers — computed
        #: from this view's own lines so it converts back to the line
        #: the test meant.
        want = max(1, getattr(self, "caret_line", 1))
        return sum(len(l) + 1 for l in self._lines[:want - 1])


def _walking(tmp_path, lines, here="piece.ges"):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    it = session()
    it.view = _View(lines)
    it.bench.path = tmp_path / here
    it.walk = Walk(clock=Clock())
    return it


def test_a_place_in_this_file_puts_the_box_on_that_line(tmp_path):
    piece = tmp_path / "piece.ges"
    piece.write_text("one\ntwo\nthree\nfour\n")
    it = _walking(tmp_path, ["one", "two", "three", "four"])
    it.walking = True
    gemba.at(str(piece), 3, "look at this line")
    it.walk.read()
    assert _rows(it) == [["gemba", "3", "look at this line", "0"]]


def test_a_place_in_another_file_asks_the_window_to_open_it(tmp_path):
    """**The walk walking.**  The session says *look at workbench.py 854*
    and the window goes there — `open`'s own road, because opening a file
    is the loop's business and not a view port's."""
    other = tmp_path / "other.ges"
    other.write_text("\n".join(str(i) for i in range(20)))
    (tmp_path / "piece.ges").write_text("here\n")
    it = _walking(tmp_path, ["here"])
    it.walking = True
    gemba.at(str(other), 5, "over here")
    it.walk.read()
    _rows(it)
    assert it.view.wanted == str(other)


def test_unsaved_work_is_warned_about_and_not_gated(tmp_path):
    """**F113's own rule, and the first version broke it.**

    Refusing to move while anything was unsaved is stricter than what a
    person gets from `open`, and it stalled the walk *silently*.  Henri:
    *"when somebody wants to gemba, they discard the file's contents.
    That could be warned in the gemba command, just like how it's being
    warned in open command."*  So the warning is where the decision is —
    at subscribing — and the walk then does what it was asked to do.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import Editor, session
    from gestate.workbench import Window

    ed = Editor("sound : Sig Float\n")
    it = session()
    it.view = Window(ed)
    it.view.saved = False
    it.run("gemba")
    assert any("unsaved changes" in o for o in ed.orders), \
        "it says so, in red, where the eye already is"

    #: And having been told, the walk travels.
    other = tmp_path / "other.ges"
    other.write_text("x\n")
    (tmp_path / "piece.ges").write_text("here\n")
    go = _walking(tmp_path, ["here"])
    go.walking = True
    go.view.saved = False
    gemba.at(str(other), 1, "over here")
    go.walk.read()
    _rows(go)
    assert go.view.wanted == str(other)


def test_a_place_that_is_not_there_moves_nothing(tmp_path):
    (tmp_path / "piece.ges").write_text("here\ngemba\n")
    it = _walking(tmp_path, ["here", "gemba"])
    gemba.at(str(tmp_path / "gone.ges"), 3, "nowhere")
    it.walk.read()
    #: It waits on its own line, which is what a walk between stops
    #: looks like.
    assert _rows(it) == [["gemba", "2", "nowhere", "0"]]


def test_a_line_past_the_end_lands_in_the_file_it_names(tmp_path):
    piece = tmp_path / "piece.ges"
    piece.write_text("one\ntwo\n")
    it = _walking(tmp_path, ["one", "two"])
    it.walking = True
    gemba.at(str(piece), 900, "past the end")
    it.walk.read()
    assert _rows(it)[0][1] == "2"


def test_it_travels_only_for_somebody_who_asked(tmp_path):
    """**A session that can open files under your hands can take the
    file you were typing in away from you.**  So a window nobody
    subscribed shows nothing and opens nothing."""
    other = tmp_path / "other.ges"
    other.write_text("x\n")
    (tmp_path / "piece.ges").write_text("here\n")
    it = _walking(tmp_path, ["here"])          # no `gemba` line, no command
    gemba.at(str(other), 1, "over here")
    it.walk.read()
    assert _rows(it) == []
    assert it.view.wanted is None


def test_the_command_subscribes_this_window(tmp_path):
    (tmp_path / "piece.ges").write_text("here\n")
    it = _walking(tmp_path, ["here"])
    assert it.walking is False
    it.run("gemba")
    assert it.walking is True


def test_the_channel_carries_a_place(tmp_path):
    gemba.at("gestate/workbench.py", 854, "this is where it crashed")
    assert (tmp_path / "gemba.tsv").read_text() == (
        "at\tgestate/workbench.py\t854\tthis is where it crashed\n")


def test_a_session_walks_with_one_command(tmp_path):
    assert gemba.main(["at", "gestate/workbench.py", "854", "look", "here"]) == 0
    assert (tmp_path / "gemba.tsv").read_text().startswith(
        "at\tgestate/workbench.py\t854\t")


def test_a_switch_does_not_unsubscribe_the_window(tmp_path, monkeypatch):
    """**The same seam, twice in one day.**  `_carry` was taught to
    carry the walk in the morning and dropped `walking` in the
    afternoon — so a walk that opened a file un-subscribed the window it
    had just moved, opened at line 1 and stood still.

    Subscription belongs to the *window*: it is a person's decision
    about this window, and switching the instrument underneath is not
    them changing their mind.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import Bench, session
    from gestate.workbench import _carry

    it = _walking(tmp_path, ["here"])
    it.walking = True
    it._walked = ("somewhere", 3)
    after = _carry(it, Bench())
    assert after.walking is True
    assert after._walked == ("somewhere", 3)


def test_arriving_at_the_file_is_not_arriving_at_the_place(tmp_path):
    """**The window opens at the top.**  A walk that pointed at line 854
    showed line 1 and a box nobody could see, so arriving takes the
    caret to the line — once per stop, never every pass, or the walk
    would be one you could not read around.
    """
    piece = tmp_path / "piece.ges"
    piece.write_text("\n".join(str(i) for i in range(60)))
    it = _walking(tmp_path, [str(i) for i in range(60)])
    it.walking = True
    gemba.at(str(piece), 40, "down here")
    it.walk.read()
    _rows(it)
    assert it.view.went == [40], "it went to the line"
    _rows(it)
    _rows(it)
    assert it.view.went == [40], "and only once"


# ── What the first real use asked for — `board/done/gemba-follow.md` ───────────


def test_the_walk_stands_still_while_nobody_is_following(tmp_path):
    """**Stepping off has to be free**, and free means what you were
    looking at is still there when you come back.  A walk that ran on
    while you read something else would make interrupting a decision
    rather than a shrug."""
    #: No pinned box, so stepping off leaves nothing on screen —
    #: which is the case that has to keep your place.
    it = _walking(tmp_path, ["here"])
    it.run("gemba")
    say("the first thing")
    say("the second thing")
    it.walk.read()
    assert _rows(it)[0][2] == "the first thing"
    it.walking = False
    it.walk.clock.at = 1000.0            # long past the first item's dwell
    _rows(it)
    it.run("gemba")                      # coming back the way a person does
    assert _rows(it)[0][2] == "the first thing", "it moved on without me"
    #: And it keeps its dwell from *now*, so the thing you came back for
    #: is not replaced in the same breath.
    it.walk.clock.at = 1000.0 + gemba.LEAST - 0.1
    assert _rows(it)[0][2] == "the first thing"


def test_any_action_stops_it_following(tmp_path):
    from gestate.session import act

    it = _walking(tmp_path, ["here"])
    for gesture in ("edited", "struck\ta\t38\t1", "touch\t1\t2\t3",
                    "command\tplay"):
        it.walking = True
        act(it, gesture)
        assert it.walking is False, gesture


def test_the_window_volunteering_its_state_is_not_an_action(tmp_path):
    """**The whole of the list.**  A window says where it is many times
    a second whether or not anybody has touched it, so treating that as
    an action would end every walk in the frame it began."""
    from gestate.session import act

    it = _walking(tmp_path, ["here"])
    it.walking = True
    act(it, "state\t4\t9\t0\t0")
    assert it.walking is True


def test_gemba_again_resumes_rather_than_ending(tmp_path):
    from gestate.session import act

    it = _walking(tmp_path, ["here"])
    it.walking = True
    act(it, "command\tgemba")
    assert it.walking is True, "running it again is not an interruption"


def test_resuming_travels_to_the_place_again(tmp_path):
    """Because you may have walked off somewhere else in the meantime,
    and the walk should not assume you are still standing where it left
    you."""
    piece = tmp_path / "piece.ges"
    piece.write_text("\n".join(str(i) for i in range(30)))
    it = _walking(tmp_path, [str(i) for i in range(30)])
    it.walking = True
    gemba.at(str(piece), 12, "down here")
    it.walk.read()
    _rows(it)
    assert it.view.went == [12]
    it.walking = False
    it.run("gemba")
    _rows(it)
    assert it.view.went == [12, 12], "it did not take me back"


def test_the_mode_is_said_even_with_nothing_to_show(tmp_path):
    """`[gemba]` is true from the moment you subscribe; the box only
    exists once something has been said."""
    it = _walking(tmp_path, ["here"])
    it.walking = True
    assert _rows(it) == [["gemba", "0", "", "0"]]


def test_the_line_pins_a_box_and_the_command_leads_you(tmp_path):
    """**They were the same switch, and that made interrupting
    impossible**: the ask-line re-subscribed on every pass of the loop,
    so a walk you had stepped off resumed a frame later and no keystroke
    could stop it.

    Separated, each says what it is for — the line means *show me,
    here*, and following means *take me to it*.
    """
    it = _walking(tmp_path, ["here", "gemba"])
    say("something happened")
    it.walk.read()
    #: The box is there without following…
    assert it.walking is False
    assert _rows(it) == [["gemba", "2", "something happened", "0"]]
    #: …and a place does not move the window until you are.
    other = tmp_path / "other.ges"
    other.write_text("x\n")
    gemba.at(str(other), 1, "over there")
    it.walk.clock.at = 100.0
    it.walk.read()
    _rows(it)
    assert it.view.wanted is None


def test_using_the_list_is_not_an_interruption(tmp_path):
    """**The list is how you reach the walk**, so using it cannot be
    what ends it.

    Picking `gemba` sends `filter` while you type, `command gemba` when
    you take it, and `shut` when the list closes — and treating those as
    actions meant the walk ended in the same breath it began, with
    `[gemba]` never appearing at all.  Found by driving the real window
    and photographing the corner.
    """
    from gestate.session import act

    it = _walking(tmp_path, ["here"])
    it.walking = True
    for gesture in ("filter\tgem", "asked\t1\tgemba\t0\t", "shut"):
        act(it, gesture)
        assert it.walking is True, gesture


def test_moving_the_caret_steps_off_even_though_nothing_told_the_model(tmp_path):
    """**Most actions never reach the model at all.**

    `act` hears about text edits, commands and played notes, and hears
    *nothing* about an arrow key — a caret move is the window's own
    state and never crosses the wire.  So the first version went on
    leading somebody who was plainly reading something else, and the
    driven window showed it.  The model looks instead of waiting to be
    told.
    """
    from gestate.workbench import _stepped_off

    piece = tmp_path / "piece.ges"
    piece.write_text("\n".join(str(i) for i in range(30)))
    it = _walking(tmp_path, [str(i) for i in range(30)])
    it.walking = True
    it._walked = (str(piece), 12)

    it.view.caret_line = 12                 # where the walk put them
    _stepped_off(it)
    assert it.walking is True

    it.view.caret_line = 3                  # and where they went
    _stepped_off(it)
    assert it.walking is False
    assert any("stepped off" in s for s in it.said)


def test_following_the_file_does_not_end_the_walk(tmp_path):
    """**The reload moved the caret, and the model reads a moved caret
    as you moving** — so following the file ended the walk that was
    following it, and the window showed both in the same frame.

    Caught by driving it: the shot meant to show the reload showed the
    file unreloaded, because the step-off had already fired.
    """
    from gestate.workbench import _refollow, _stepped_off

    piece = tmp_path / "piece.ges"
    piece.write_text("\n".join(f"# line {i}" for i in range(1, 30)))
    it = _walking(tmp_path, [f"# line {i}" for i in range(1, 30)])
    it.walking = True
    it._walked = (str(piece), 20)
    it.view.caret_line = 20

    class Ed:
        def __init__(self):
            self.loaded = []

        def load(self, text):
            self.loaded.append(text)

    ed = Ed()
    watched = _refollow(it, ed, None)
    piece.write_text("\n".join(f"# EDITED {i}" for i in range(1, 30)))
    import os
    os.utime(piece, (watched[1] + 10, watched[1] + 10))
    _refollow(it, ed, watched)
    assert ed.loaded, "it did not reload"
    assert it.view.went[-1] == 20, "it did not put the caret back"
    _stepped_off(it)
    assert it.walking is True, "following the file ended the walk"


def test_stepping_to_another_file_does_not_end_the_walk(tmp_path):
    """**What made the walk cut off.**  Henri, watching one run for two
    minutes: *"the gemba walk cuts off."*

    A walk that moves to another file leaves the caret at line 1 of the
    new one while `_walked` still names the old place — so the very next
    pass read a mismatch and called it *you* having moved.  Every step
    to a different file ended the walk that took it.
    """
    from gestate.workbench import _stepped_off

    one = tmp_path / "one.ges"
    two = tmp_path / "two.ges"
    for f in (one, two):
        f.write_text("\n".join(str(i) for i in range(30)))

    it = _walking(tmp_path, [str(i) for i in range(30)], here="two.ges")
    it.walking = True
    it._walked = (str(one), 12)          # where the walk *was*
    it.view.caret_line = 1               # and the new file opens at the top

    _stepped_off(it)
    assert it.walking is True, "it ended itself on the way to the next file"


def test_the_walks_own_step_is_not_the_person_typing(tmp_path):
    """**The other half of *cut off*.**

    Loading a document makes the window report an `edited` — so the
    walk's own step looked exactly like somebody typing, and every move
    to another file interrupted the walk that made it.  The first stop
    arrived and nothing after it, which is what Henri watched for two
    minutes.
    """
    from gestate.session import act

    other = tmp_path / "other.ges"
    other.write_text("x\n")
    (tmp_path / "piece.ges").write_text("here\n")
    it = _walking(tmp_path, ["here"])
    it.walking = True

    gemba.at(str(other), 1, "over there")
    it.walk.read()
    _rows(it)                                  # asks for the open
    assert it._moving is True and it.view.wanted == str(other)

    act(it, "edited")                          # which the load provokes
    assert it.walking is True, "its own step ended it"

    #: And once the file has arrived, typing interrupts again.
    it._moving = False
    act(it, "edited")
    assert it.walking is False


def test_it_does_not_judge_a_caret_that_has_not_arrived_yet(tmp_path):
    """**The real cause of *cut off*.**

    An order is obeyed on the window's *next* frame, so the step-off
    read the caret before the walk's own `goto` had landed, saw the old
    position and called it the person moving.  The instrumented window
    said it in one line: `[walk] ended by the caret: 2 != 132`, one
    frame after the walk had asked to be at 132.

    So arrival is witnessed before departure can be.
    """
    from gestate.workbench import _stepped_off

    piece = tmp_path / "piece.ges"
    piece.write_text("\n".join(str(i) for i in range(30)))
    it = _walking(tmp_path, [str(i) for i in range(30)])
    it.walking = True
    it._walked = (str(piece), 20)
    it._arrived = False
    it.view.caret_line = 2                 # the goto has not landed yet

    _stepped_off(it)
    assert it.walking is True, "it judged a caret still in flight"

    it.view.caret_line = 20                # it lands
    _stepped_off(it)
    assert it.walking is True and it._arrived is True

    it.view.caret_line = 3                 # and now the person moves
    _stepped_off(it)
    assert it.walking is False
