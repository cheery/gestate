"""The read-only score box — `spec/scorebox.md`.

The box is a *view*: it reads the author's own text, rebuilds the
expression the ask names with every written leaf tagged, and walks the
result with the library's own algebra.  So what these check is that
the picture tells the truth about the file — the notes it draws are
the notes the piece plays, and the region a note belongs to is where a
person would say it is written.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from gestate.scorebox import (RollError, asks, build_roll, roll_program)

AUDIO = Path(__file__).resolve().parent.parent / "examples" / "audio"
RATE = 22050


def _roll(name: str, ask: str = "score", seed: int = 0, **kw):
    source = (AUDIO / name).read_text() + f"\nnotes {ask}\n"
    line, expr = asks(source)[0]
    return build_roll(source, expr, line, RATE, seed, **kw), source


# ── The ask ─────────────────────────────────────────────────────────────────


def test_the_ask_is_read_the_way_the_sinks_are():
    """`sink`'s manners exactly: top level, one line, and a trailing
    comment on the word is not an expression."""
    text = ("notes score\n"
            "  notes indented\n"
            "notes # just a comment\n"
            "notes chords ++ tune\n")
    assert asks(text) == [(1, "score"), (4, "chords ++ tune")]


def test_a_program_keeps_its_own_notes():
    """A word the box claims is a word an author already had.  One
    did — `test_audioeditor.py`'s fixture declares `notes = …` — and
    the first rewrite ate the declaration, taking a global the
    program went on to use with it."""
    text = ("notes = flow 1\n"
            "notes : List Int\n"
            "notes k = k + 1\n"
            "notes score\n")
    assert asks(text) == [(4, "score")]


def test_the_ask_says_nothing_to_the_compiler():
    """The line is rewritten at the door every assembly passes, so a
    file with a score box in it compiles exactly as it did without
    one — and keeps its line numbering, which every jump depends on."""
    from gestate.audiovoices import _sinks

    before = "a = 1\nb = 2\n"
    after = _sinks("a = 1\nnotes score\nb = 2\n")
    assert "notes score" not in after.replace("# notes score", "")
    assert len(after.splitlines()) == 3
    assert after.splitlines()[0] == "a = 1"
    assert after.splitlines()[2] == "b = 2"
    assert _sinks(before) == before          # nothing paid for by others


# ── What it draws ───────────────────────────────────────────────────────────


def test_chopin_draws_the_ladder_it_describes():
    """The piece's own comment claims a descent written note by note;
    the box has to show that piece and not some other.  The opening
    stroke is `stroke 55 59 64` at the `quiet` velocity, and the
    eleven bars end where the score ends."""
    roll, _ = _roll("chopin.ges")

    assert not roll.cut and not roll.chancy
    # The chord tones are the quiet ones; the tune sings over them from
    # the same downbeat, which is what `chords || tune` means.
    opening = sorted(e[3] for e in roll.events if e[0] == 0 and e[4] == 46)
    assert opening == [55, 59, 64], "the E minor stroke the file opens on"
    sung = [e[3] for e in roll.events if e[0] == 0 and e[4] == 84]
    assert sung == [71], "the sigh the piece opens on, over the chord"
    # Eleven bars of four beats at 96 ticks: the ladder plus its close.
    assert max(e[1] for e in roll.events) == 11 * 4 * 96
    assert {leaf.bank for leaf in roll.leaves} == {"piano"}


def test_a_note_belongs_to_the_line_that_wrote_it():
    """The jump's whole promise.  Chopin's chords are written one bar
    to a line and the box has to say so — *those* lines, not the body
    of the `quiet` helper the descent never enters."""
    roll, source = _roll("chopin.ges")
    lines = source.splitlines()

    for leaf in roll.leaves:
        text = lines[leaf.line - 1]
        assert any(word in text for word in ("barOf", "sing", "stroke")), \
            f"line {leaf.line} is not where a note is written: {text!r}"

    # And the first chord's region is the first `barOf` line.
    first = roll.leaves[roll.events[0][2]]
    assert "stroke 55 59 64" in lines[first.line - 1]


def test_a_chancy_piece_is_one_take_and_the_seed_names_it():
    """`spec/scorebox.md` §"The take": the box shows the take the
    session's seed names — the same seed twice is the same picture,
    and another seed is another night over the same floor."""
    a, _ = _roll("undertow.ges", seed=0)
    again, _ = _roll("undertow.ges", seed=0)
    other, _ = _roll("undertow.ges", seed=7)

    assert a.events == again.events, "a take is its seed's, and repeats"
    assert a.events != other.events, "another seed tells another night"
    assert a.chancy and a.seed == 0, "the label owes a seed here"
    # The floor is the same under both: the bass is written down.
    def bass(roll):
        return [e for e in roll.events
                if roll.leaves[e[2]].bank == "bass"]
    assert bass(a) == bass(other), "the ground bass is not chancy"


def test_take_ink_is_marked_and_span_ink_is_not():
    """The two kinds of ink: a note the dice chose wears the
    generator's line and is drawn dimmer, one that is written down is
    not.  Undertow is one of each."""
    roll, _ = _roll("undertow.ges")

    kinds = {leaf.bank: leaf.chancy for leaf in roll.leaves}
    assert kinds == {"bass": False, "chimes": True}


def test_the_modern_idiom_is_readable_at_all():
    """Undertow assigns *inside* its parts — `voices.bass (Key k 96)`
    in a do-block, two calls down for the chimes — and the payload is
    gone by the time an ordinary walk sees it.  The unassigned twin is
    what makes the newest idiom readable; without it this raises
    `Notable Void`."""
    roll, _ = _roll("undertow.ges")

    assert roll.events, "the piece drew nothing"
    assert {leaf.bank for leaf in roll.leaves} == {"bass", "chimes"}
    keys = {e[3] for e in roll.events}
    assert min(keys) < 40 < max(keys), "both banks, high and low"


def test_the_demo_shows_the_three_things_it_claims():
    """`noted.ges` is the box's own example, and its header makes
    three promises: a written hand, a drawn one, and a box on each
    plus one on both.  A demo that stopped demonstrating would be
    worse than none."""
    source = (AUDIO / "noted.ges").read_text()
    found = {expr: (line, expr) for line, expr in asks(source)}
    assert set(found) == {"ground", "tune", "score"}

    rolls = {expr: build_roll(source, expr, line, RATE, 0)
             for line, expr in asks(source)}

    # The written hand: four notes, D A F A, none of them the dice's.
    ground = rolls["ground"]
    assert [e[3] for e in ground.events] == [38, 45, 41, 45]
    assert not ground.chancy, "the left hand is written down"

    # The drawn one: every note take ink, and another seed moves them.
    tune = rolls["tune"]
    assert tune.chancy and tune.events
    assert all(leaf.chancy for leaf in tune.leaves)
    other = build_roll(source, "tune", found["tune"][0], RATE, 7)
    assert [e[3] for e in other.events] != [e[3] for e in tune.events]

    # Both at once: two banks, and the left hand is the same sixteen
    # notes whatever the dice say.
    both = rolls["score"]
    banks = {leaf.bank for leaf in both.leaves}
    assert banks == {"left", "right"}
    left = [e[3] for e in both.events if both.leaves[e[2]].bank == "left"]
    assert left == [38, 45, 41, 45] * 4, "four bars of the written hand"


def test_a_minute_of_music_keeps_the_form_its_header_claims():
    """`minute.ges` is the box on a whole arrangement, and its header
    tells you the shape you are looking at: four blocks, the tune in
    the middle sixteen bars and the dice in the middle eight.  A
    header that drifted from its piece would be teaching the wrong
    thing to the one reader who cannot hear it."""
    source = (AUDIO / "minute.ges").read_text()
    line, expr = [ask for ask in asks(source) if ask[1] == "score"][0]
    roll = build_roll(source, expr, line, RATE, 0)

    bar = 4 * 96                                # four beats of ticks
    assert max(e[1] for e in roll.events) == 24 * bar, "a minute exactly"

    def bars(bank):
        mine = [e for e in roll.events if roll.leaves[e[2]].bank == bank]
        return (min(e[0] for e in mine) // bar + 1,
                max(e[1] for e in mine) // bar)

    assert bars("bass") == (1, 24), "the floor runs the whole way"
    assert bars("chord") == (1, 24), "and its chords with it"
    assert bars("top") == (5, 20), "the tune arrives and leaves"
    assert bars("spark") == (13, 20), "the dice are the middle eight"

    # And only the sparkle is the dice's — everything else is written.
    drawn = {leaf.bank for leaf in roll.leaves if leaf.chancy}
    assert drawn == {"spark"}


# ── When it cannot ──────────────────────────────────────────────────────────


def test_a_payload_with_no_instance_is_refused_by_name():
    """The refusal names the type and the class rather than drawing a
    wrong picture — `specimens/sauna_specimen.ges` has no `Notable`,
    and that is the sentence its author needs."""
    specimen = (Path(__file__).resolve().parent.parent / "specimens"
                / "sauna_specimen.ges")
    source = specimen.read_text() + "\nnotes score\n"
    line, expr = asks(source)[0]

    with pytest.raises(RollError) as caught:
        build_roll(source, expr, line, RATE, 0)
    said = str(caught.value)
    assert "Notable" in said and "Key" in said, said


def test_a_walk_that_cannot_end_runs_out_of_fuel_not_time():
    """The sauna lesson as a bound: a `cycle` of something zero beats
    wide has no end and no width to reach one, and the box says it was
    cut rather than hanging the window that asked."""
    source = ("K := K Int\n\n"
              "voices lead 2 lv : Sig Float\n\n"
              "instance FromMIDI K where\n"
              "    noteOn ch p v = Just (K p)\n\n"
              "instance Notable K where\n"
              "    noteKey q = case q of\n"
              "        K k -> k\n"
              "    noteVel q = 96\n\n"
              "lv : Sig Gate -> Sig K -> Sig Float\n"
              "lv g s = map (n => 0.0) ticks\n\n"
              "sound : Sig Float\nsound = lead\n\n"
              "bpm : Int\nbpm = 120\n\n"
              "score : [: Void :]\n"
              "score = '(K 60) >>= voices.lead\n\n"
              "tune : [: K :]\n"
              "tune = cycle (mark \"a\")\n\n"
              "notes tune\n")
    line, expr = asks(source)[0]

    began = time.time()
    roll = build_roll(source, expr, line, RATE, 0, fuel=20_000)
    assert roll.cut, "an endless zero-width walk has to say it was cut"
    assert time.time() - began < 60, "and has to say it quickly"


# ── The picture ─────────────────────────────────────────────────────────────


def test_the_roll_is_an_ordinary_substrate_that_draws():
    """The box is handed to the window as a canvas like any other, so
    it has to build and draw as one — and *cross*, or the walking
    window would have nothing to walk."""
    from gestate.gui import Substrate

    roll, _ = _roll("chopin.ges")
    program, jumps = roll_program(roll)
    sub = Substrate(program, RATE)

    assert len(sub.picture()) == len(roll.events) + 2, \
        "one rect per note, on a ground, under a caption"
    assert sub.crossing is not None, "the window could not walk it"
    assert len(jumps) == len(roll.leaves), "a hand per written region"


def test_two_boxes_do_not_share_a_hand():
    """Two rolls in one file are two walks in one program's channel
    namespace: a shared channel name would make a press in either jump
    to whichever was built last."""
    roll, _ = _roll("chopin.ges")
    _first, one = roll_program(roll, 0)
    _second, two = roll_program(roll, 1)

    assert set(one) & set(two) == set()


def test_a_page_of_boxes_is_the_same_page_built_one_at_a_time():
    """**The acceptance for building them together.**  Three boxes used
    to be three whole programs; they are one now, and the only thing
    that makes that safe is that every box still gets the roll it got
    alone.  `noted.ges` is the file to ask, because its three asks
    overlap: `score` reaches both hands, and `ground` is reached from
    `score` under a bank and from its own ask under none — the
    hidden-definition collision that numbering `_Descent.box` exists to
    prevent, which would show up here as a hand wearing the other's
    colour.
    """
    from gestate.scorebox import build_rolls

    source = (AUDIO / "noted.ges").read_text()
    page = asks(source)
    together = build_rolls(source, page, RATE, 0)
    alone = [build_roll(source, expr, line, RATE, 0) for line, expr in page]

    assert len(together) == len(alone) == 3
    for (line, expr), got, want in zip(page, together, alone):
        assert not isinstance(got, Exception), f"{expr}: {got}"
        assert got.events == want.events, expr
        assert [(l.line, l.bank, l.chancy) for l in got.leaves] == \
               [(l.line, l.bank, l.chancy) for l in want.leaves], expr
        assert (got.cut, got.chancy, got.seed) == \
               (want.cut, want.chancy, want.seed), expr


def test_one_bad_ask_does_not_blank_the_page():
    """A page is built as one program, so a refusal in one ask refuses
    the whole compile — and the answer is to ask each again alone
    rather than to draw nothing.  The box that is wrong says so in its
    own slot; the others are unaffected."""
    from gestate.scorebox import build_rolls

    source = ((AUDIO / "noted.ges").read_text()
              + "\nnotes noSuchTuneAnywhere\n")
    page = asks(source)
    got = build_rolls(source, page, RATE, 0)

    assert isinstance(got[-1], RollError), got[-1]
    assert all(not isinstance(r, Exception) for r in got[:-1]), got
    assert got[0].events, "the written hand still drew"


def test_a_page_is_one_program_and_still_three_pictures():
    """Compiled once, drawn as many — and each box keeps its own.

    The saving is only worth having if a view is still a box: its own
    picture, its own hands, and a payload naming only the channels its
    own program has.  A channel from another box in the header is a
    global the walking window is asked to force and does not have.
    """
    from gestate.gui import Substrate
    from gestate.scorebox import build_rolls, page_program

    source = (AUDIO / "noted.ges").read_text()
    page = asks(source)
    rolls = build_rolls(source, page, RATE, 0)
    program, jumps, entries = page_program(rolls)
    drawn = [e for e in entries if e is not None]
    assert drawn == ["__notes_0__", "__notes_1__", "__notes_2__"]

    views = Substrate.several(program, RATE, drawn)
    assert all(v.state is views[0].state for v in views), "one machine"

    pictures = [v.picture() for v in views]
    assert all(pictures), "every box drew"
    assert pictures[0] != pictures[1] != pictures[2]

    seen: set = set()
    for v in views:
        mine = set(v.crossing["chans"])
        assert mine, "a box with no hands cannot be pressed"
        assert not mine & seen, "two boxes claimed one channel"
        assert mine <= set(jumps), "a channel with nowhere to jump"
        seen |= mine
        assert v.payload(), "the box could not cross"


def test_every_hand_lands_on_a_line_that_exists():
    roll, source = _roll("chopin.ges")
    _program, jumps = roll_program(roll)
    last = len(source.splitlines())

    assert jumps and all(1 <= line <= last for line in jumps.values())


# ── In the workbench ────────────────────────────────────────────────────────


def test_the_workbench_stands_a_box_on_the_ask_and_a_press_jumps(tmp_path):
    """End to end, the way a person meets it: open a file with a
    `notes` line, and the box is built, standing on that line, with a
    press on a note revealing where it is written."""
    from gestate.audioeditor import Workbench
    from gestate.session import furniture

    source = (AUDIO / "chopin.ges").read_text() + "\nnotes score\n"
    path = tmp_path / "chopin.ges"
    path.write_text(source)
    bench = Workbench(path, rate=RATE, block=256)
    bench._load_substrate(source)

    assert not [m for m in bench.messages if "notes" in m], bench.messages
    assert "__notes_0__" in bench.canvases
    assert bench.canvases["__notes_0__"].picture(), "the roll drew nothing"

    rows = _furniture_rows(source, bench)
    ask_line = asks(source)[0][0]
    assert f"canvas\t{ask_line}\t__notes_0__" in rows

    # The one gesture it owns: a press is a jump, and the file is not
    # touched by it.
    where = bench.note_jumps["__nb_c0_0__"]
    assert source.splitlines()[where - 1].strip().startswith("chords =") \
        or "stroke" in source.splitlines()[where - 1]


def _furniture_rows(source: str, bench) -> list:
    """`furniture` against a view that is only the text — what the
    headless sessions and these tests have."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    from gestate.session import furniture

    class _View:
        saved = True

        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

        def goto(self, n):
            self.went = n
            return True

        def undo(self):
            return False

        def redo(self):
            return False

    seat = session()
    seat.view = _View(source)
    return furniture(seat, bench).splitlines()


def test_a_press_moves_the_caret_and_writes_nothing(tmp_path):
    """The read-only promise, checked: the gesture reaches the *view*
    and the document is untouched."""
    from gestate.audioeditor import Workbench

    source = (AUDIO / "chopin.ges").read_text() + "\nnotes score\n"
    path = tmp_path / "chopin.ges"
    path.write_text(source)
    bench = Workbench(path, rate=RATE, block=256)
    bench._load_substrate(source)

    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    class _View:
        saved = True

        def __init__(self, text):
            self._text, self.went = text, None

        def text(self):
            return self._text

        def goto(self, n):
            self.went = n
            return True

        def undo(self):
            return False

        def redo(self):
            return False

    seat = session()
    seat.view = _View(source)
    seat.bench = bench
    said = seat.touched("__nb_c0_0__", 0.5)

    assert seat.view.went == bench.note_jumps["__nb_c0_0__"]
    assert said == f"line {seat.view.went}"
    assert seat.view.text() == source, "a read-only box wrote to the file"
