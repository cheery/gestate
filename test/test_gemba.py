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


def test_the_command_writes_the_line_for_you(tmp_path):
    """**The second defect: the box was not findable.**

    It had been an ask-line since it was built, and the only way to
    raise one was to know to type the word — so the first person a
    session narrated at could not see any of it.  A capability nobody
    can reach is `fixme.md` F150 one floor up, and the answer is the
    same: put it in the list.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import Editor, session
    from gestate.workbench import Window

    ed = Editor("sound : Sig Float\n")
    it = session()
    it.view = Window(ed)
    said = it.run("gemba")
    assert "insert\t\ngemba\n" in ed.orders, "it writes the line"
    assert "watching" in said, "and says where the channel is"


def test_the_command_does_not_raise_a_second_box(tmp_path):
    """One box, because the pace is the point — and a person who runs it
    twice should be told, not given a second thing to read."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    it = _a_session(["sound : Sig Float", "gemba", ""])
    assert "already" in it.run("gemba")


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
