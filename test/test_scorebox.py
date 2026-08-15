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

    from gestate.scorebox import hands_of

    roll, _ = _roll("chopin.ges")
    program, hands = roll_program(roll)
    sub = Substrate(program, RATE)

    assert len(sub.picture()) == len(roll.events) + 2, \
        "one rect per note, on a ground, under a caption"
    assert sub.crossing is not None, "the window could not walk it"
    assert len(hands) == len(hands_of(roll)), "a hand per column"


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
        assert mine <= set(jumps), "a channel that is nobody's hand"
        seen |= mine
        assert v.payload(), "the box could not cross"


def test_every_hand_lands_on_a_line_that_exists():
    """A press anywhere in any column finds a note, and that note is
    written on a line of this file."""
    from gestate.scorebox import hands_of, note_under

    roll, source = _roll("chopin.ges")
    last = len(source.splitlines())
    hands = hands_of(roll)
    assert hands

    for hand, _h in enumerate(hands):
        for down in (0.0, 0.25, 0.5, 0.75, 1.0):
            note = note_under(roll, hand, down)
            line = roll.leaves[roll.events[note][2]].line
            assert 1 <= line <= last, (hand, down, line)


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

    # The gesture it owns: a press picks the note by where it lands and
    # says where *that one* is written, and the file is not touched.
    from gestate.scorebox import note_under

    roll, hand = bench.note_regions["__nb_c0_0__"]
    note = note_under(roll, hand, 0.5)
    where = roll.leaves[roll.events[note][2]].line
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

    from gestate.scorebox import note_under

    seat = session()
    seat.view = _View(source)
    seat.bench = bench
    said = seat.touched("__nb_c0_0__", 0.5)

    roll, hand = bench.note_regions["__nb_c0_0__"]
    note = note_under(roll, hand, 0.5)
    assert seat.view.went == roll.leaves[roll.events[note][2]].line
    assert said == f"line {seat.view.went}"
    assert seat.view.text() == source, "a press alone wrote to the file"


def test_a_press_where_a_note_is_drawn_finds_it():
    """**Aim at the picture, not at the channel.**

    Henri, 2026-08-15: *"note-regions press-to-jump is not working"* —
    and every test above passed, because they all press by *name*
    (`session.touched("__nb_c0_0__", …)`), which is the mapping and not
    the affordance.  The regions were `Sized w h (TouchX c (Gap 0 0))`:
    an attachment's extent is the extent of what it *wraps*, so each
    one was zero by zero and could be hit only by a press landing on a
    single point.  `onTouchY cutoff (rect 40 200 grey)` is the idiom
    `gui.ges` documents — the thing with an extent goes inside.

    So this presses at *places*, swept over the box the way a hand
    would arrive, and asks that every note the jump table names can be
    reached by aiming at it.  A harness built from the implementation
    cannot find a missing affordance; this one is built from the
    gesture.
    """
    from gestate.gui import Substrate
    from gestate.scorebox import ROLL_H, ROLL_W, build_rolls, page_program

    source = (AUDIO / "minute.ges").read_text()
    page = asks(source)
    rolls = build_rolls(source, page, RATE, 0)
    program, jumps, entries = page_program(rolls)
    views = Substrate.several(program, RATE, [e for e in entries if e])

    reached = set()
    for view in views:
        # The reference machine draws from its own origin, so the box
        # is the rectangle around (0, 0) — swept at four pixels, which
        # is finer than any note is tall and coarser than aiming.
        for x in range(-ROLL_W // 2, ROLL_W // 2, 4):
            for y in range(-ROLL_H // 2, ROLL_H // 2, 4):
                meant = view.touch("press", x, y)
                if meant and meant[0] == "touched":
                    reached.add(meant[1])
                view.touch("release", x, y)

    assert reached, "no press anywhere in any box landed on a note"
    missed = set(jumps) - reached
    assert not missed, f"{len(missed)} notes cannot be pressed: {sorted(missed)[:4]}"


# ── Writing back — `spec/north_star.md` ─────────────────────────────────────


def _rolled(name: str, ask: str | None = None):
    """A file and one roll of it, for the edits below."""
    source = (AUDIO / name).read_text()
    if not asks(source):
        source += "\nnotes score\n"
    pick = [a for a in asks(source) if ask is None or a[1] == ask][:1]
    from gestate.scorebox import build_rolls

    return source, build_rolls(source, pick, RATE, 0)[0]


def _only_change(before: str, after: str) -> tuple:
    """The one line that differs, or a failure saying how many did."""
    a, b = before.splitlines(), after.splitlines()
    assert len(a) == len(b), "a transposition changed the number of lines"
    moved = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    assert len(moved) == 1, f"{len(moved)} lines changed, not one"
    return a[moved[0]], b[moved[0]]


def test_a_transposition_is_one_number_and_nothing_else():
    """**The tier-one promise** (`spec/north_star.md`): one atom's byte
    range, no reflow, no reprint.  Asserted on the whole text rather
    than on the parsed tree, because "nothing else moved" is the claim —
    including the comment at the end of the line."""
    from gestate.scorebox import transposed

    source, roll = _rolled("chopin.ges")
    note = next(i for i, e in enumerate(roll.events)
                if not roll.leaves[e[2]].chancy)
    text, said = transposed(source, roll, note, roll.events[note][3] + 4)

    was, now = _only_change(source, text)
    assert was.replace(str(roll.events[note][3]), "", 1) == \
           now.replace(str(roll.events[note][3] + 4), "", 1), \
        f"more than the number moved:\n  {was}\n  {now}"
    assert "+4 semitones" in said


def test_the_pitch_may_be_the_authors_own_helpers_argument():
    """The rule this project measured its way to.  `low 38` is what a
    real piece writes, not `'(Key 38 …)`, and a box that only knew the
    library's spelling would refuse four files in five."""
    from gestate.scorebox import pitch_atom, transposed

    source, roll = _rolled("noted.ges", "ground")
    line, col, width, value = pitch_atom(roll, 0)

    assert source.splitlines()[line - 1][col:col + width] == str(value)
    assert "low" in source.splitlines()[line - 1], "the premise: a helper"
    text, _said = transposed(source, roll, 0, 42)
    assert "low 42 ++ low 45" in text


def _seated(source: str, roll):
    """A headless session over that text, with the box's regions on the
    bench — what the window's gestures arrive into."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    from gestate.scorebox import regions_of

    class _View:
        saved = True

        def __init__(self, text):
            self._text, self.went = text, None

        def text(self):
            return self._text

        def replace(self, text):
            self._text = text
            return True

        def goto(self, line):
            self.went = line
            return True

    seat = session()
    seat.view = _View(source)
    seat.bench.note_regions = regions_of([roll])
    return seat


def test_the_command_writes_the_note_the_region_and_the_key_name():
    """`transpose` — the first command in this project that a *gesture*
    will run and the first that writes text from a picture.

    Named as `spec/north_star.md` §"The vocabulary" settles it: the
    region, the key it says now, the key it is to say.  Both keys
    rather than a step, because a region can sound a chord and a
    recording that held `+3` would mean a different note the second
    time it was read.
    """
    source, roll = _rolled("noted.ges", "ground")
    seat = _seated(source, roll)
    chan = next(iter(seat.bench.note_regions))
    was = next(e[3] for e in roll.events if e[2] == 0)

    said = seat.run("transpose", chan, was, was + 2)

    assert "+2 semitone" in said, said
    before, after = _only_change(source, seat.view.text())
    assert before.replace(str(was), "", 1) == after.replace(str(was + 2), "",
                                                            1), \
        f"more than the number moved:\n  {before}\n  {after}"


def test_a_note_dragged_by_hand_is_written_where_it_was_dropped():
    """**The slice, whole** (`spec/north_star.md`): a vertical drag on
    span ink, one note, byte-exact — pressed at a *place*, carried, let
    go, and the file says so.

    Aimed at the picture rather than at a channel, for the reason the
    press sweep is: a harness built from the implementation cannot find
    a missing affordance.  What this drives is exactly what the window
    drives — `press`, `drag`, `release` in canvas coordinates on one
    side, `touched`/`released` into the session on the other.
    """
    from gestate.gui import Substrate
    from gestate.scorebox import (ROLL_H, ROLL_W, build_rolls, key_at,
                                  page_program)

    source, roll = _rolled("noted.ges", "ground")
    page = [a for a in asks(source) if a[1] == "ground"][:1]
    program, regions, entries = page_program(build_rolls(source, page,
                                                         RATE, 0))
    view = Substrate.several(program, RATE, [e for e in entries if e])[0]
    seat = _seated(source, roll)

    # **Aim at a note that is drawn**, which is what a hand does: the
    # thin bright rects in the picture are the notes, and the one in
    # the middle of the roll has room to be carried either way.
    notes = [it for it in view.picture()
             if it[0] == "rect" and it[4] == 3][1:]
    assert notes, "the roll drew no notes to aim at"
    notes.sort(key=lambda it: abs(it[2]))
    _kind, nx, ny, nw, _nh, _c = notes[0]
    x, y = nx + nw // 2, ny + 1

    meant = view.touch("press", x, y)
    assert meant and meant[0] == "touched" and meant[1] in regions, meant
    chan, down = meant[1], meant[2]
    said = seat.touched(chan, down)
    assert said.startswith("line "), said
    note = seat.holding[1]
    was = roll.events[note][3]
    assert seat.view.text() == source, "the press wrote to the file"

    # Carry it upward until the hand has travelled three semitones.
    grabbed = key_at(roll, down)
    up = next((yy for yy in range(y, -ROLL_H, -1)
               if key_at(roll, view.touch("drag", x, yy)[2]) == grabbed + 3),
              None)
    assert up is not None, "the box has no room for a third"
    moving = seat.touched(chan, view.touch("drag", x, up)[2])
    assert "+3" in moving, moving
    assert seat.view.text() == source, "the drag wrote before it was done"

    view.touch("release", x, up)
    said = seat.released(chan)

    assert "+3 semitone" in said, said
    before, after = _only_change(source, seat.view.text())
    assert before.replace(str(was), "", 1) == \
        after.replace(str(was + 3), "", 1), \
        f"more than the number moved:\n  {before}\n  {after}"
    # And it records as the command, which is what a replay reads.
    assert "transpose" in seat._journal().text()


def test_a_hand_reaches_two_octaves_past_the_music():
    """Henri, dragging one: *"the drag appears to stop to the canvas
    borders."*

    A `TouchY` writes a fraction of its own element and is clamped
    there — the law that makes every gesture bounded by construction.
    A hand exactly the size of the roll could therefore only ever say a
    pitch the piece already plays, which is the wrong bound for a
    gesture whose whole point is moving a note somewhere else.  So the
    element is taller than the picture: same pixels per semitone, two
    octaves further at each end, off the top and bottom of the band
    where the box's own clip hides it.
    """
    from gestate.scorebox import (DRAG_REACH, key_at, reach_of, scale_of,
                                  y_of)

    _source, roll = _rolled("noted.ges", "ground")
    lo, hi, _span = scale_of(roll)
    low, high = reach_of(roll)

    assert (low, high) == (lo - DRAG_REACH, hi + DRAG_REACH)
    assert key_at(roll, 0.0) == high, "the top of the hand is out of reach"
    assert key_at(roll, 1.0) == low

    # And the same line read backwards: a height where a note is
    # *drawn* still means that note, which is what picking depends on.
    for _on, _off, _k, key, _vel in roll.events:
        drawn = y_of(roll, key)
        top, bottom = y_of(roll, high), y_of(roll, low)
        assert key_at(roll, (drawn - top) / (bottom - top)) == key

    # The pixels are the roll's own, so the hand moves at the speed the
    # eye expects rather than a compressed one.
    tall = y_of(roll, low) - y_of(roll, high)
    assert abs(tall / (high - low) - (y_of(roll, lo) - y_of(roll, hi))
               / max(1, hi - lo)) < 0.5


def test_a_note_let_go_where_it_began_writes_nothing():
    """A press that wandered and came home is a press.  Nothing is
    written, so nothing is undone — and the transcript holds the
    gesture rather than an edit that did not happen."""
    source, roll = _rolled("noted.ges", "ground")
    seat = _seated(source, roll)
    chan = next(iter(seat.bench.note_regions))

    seat.touched(chan, 0.5)
    was = roll.events[seat.holding[1]][3]
    seat.touched(chan, 0.2)
    seat.touched(chan, 0.5)
    assert seat.holding[4] == was, seat.holding
    assert seat.released(chan) == ""
    assert seat.view.text() == source
    assert seat.holding is None, "the hand is still held after it let go"


def test_a_note_dropped_while_it_plays_is_auditioned():
    """`spec/north_star.md`: the drag rewrites the *buffer* and
    auditions, so the sound follows the hand and the file on disk is
    untouched until `Ctrl-S`.

    A gesture that saved would make an experiment permanent; one that
    only edited the buffer would be silent until you saved, which is
    the opposite of the room this editor is.  Stopped, it says nothing
    at all: an audition with no sound running has nothing to do but
    talk about the transport, over the top of the answer about the
    note.
    """
    source, roll = _rolled("noted.ges", "ground")
    heard = []

    for playing in (False, True):
        seat = _seated(source, roll)
        seat.bench.playing = playing
        seat.bench.audition = lambda text: heard.append(text)
        chan = next(iter(seat.bench.note_regions))
        was = next(e[3] for e in roll.events if e[2] == 0)
        seat.run("transpose", chan, was, was + 2)

    assert len(heard) == 1, "auditioned while stopped, or not while playing"
    assert f"low {was + 2}" in heard[0] or str(was + 2) in heard[0]
    assert heard[0] == seat.view.text(), "it auditioned something else"


def test_the_picture_follows_a_drop_with_nothing_playing(tmp_path):
    """Acceptance 2, and it only half held.

    A canvas is rebuilt by `_load_substrate`, which runs inside a
    *build* — so with nothing playing there was no build, and a dragged
    note moved in the file while the roll went on drawing it where it
    used to be.  For a mark in the margin that is this editor's
    ordinary rule; for a direct gesture it reads as the drag not having
    taken, which is the worst answer a gesture can give.
    """
    from gestate.audioeditor import Workbench

    from test_session import session

    source = (AUDIO / "noted.ges").read_text()
    path = tmp_path / "noted.ges"
    path.write_text(source)
    bench = Workbench(path, rate=RATE, block=256)
    bench._load_substrate(source)
    assert not bench.playing, "the premise: nothing is sounding"
    before = list(bench.canvases["__notes_0__"].picture())

    class _View:
        saved = True

        def __init__(self, text):
            self._text = text

        def text(self):
            return self._text

        def replace(self, text):
            self._text = text
            return True

        def goto(self, line):
            return True

    seat = session()
    seat.bench, seat.view = bench, _View(source)
    chan = sorted(bench.note_regions)[0]
    seat.touched(chan, 0.5)
    seat.touched(chan, 0.1)
    assert "semitone" in seat.released(chan)

    end = time.time() + 30.0
    while time.time() < end:
        if list(bench.canvases["__notes_0__"].picture()) != before:
            break
        time.sleep(0.05)
    assert list(bench.canvases["__notes_0__"].picture()) != before, \
        "the note moved in the file and the roll did not"


def test_a_burst_of_drops_is_one_redraw_and_the_newest_text(tmp_path):
    """A hand drags notes in bursts, and each one costs half a second
    of front end.  So at most one redraw runs and at most one waits —
    and the one that waits is the newest text, because a picture of an
    edit two edits ago is not worth the wait it cost."""
    from gestate.audioeditor import Workbench

    path = tmp_path / "noted.ges"
    path.write_text((AUDIO / "noted.ges").read_text())
    bench = Workbench(path, rate=RATE, block=256)

    drew = []

    def slowly(text):
        time.sleep(0.3)
        drew.append(text)

    bench._redraws._run = slowly
    for n in range(5):
        bench.redraw(f"take {n}")
    end = time.time() + 15.0
    while time.time() < end and (len(drew) < 2 or bench._redraws.busy):
        time.sleep(0.02)

    assert len(drew) < 5, f"five drops started {len(drew)} redraws"
    assert drew[-1] == "take 4", drew


def test_the_command_refuses_by_name_and_writes_nothing():
    """Every refusal is a sentence, and none of them touches the file —
    which is the property that lets a hand try things."""
    source, roll = _rolled("noted.ges", "ground")
    seat = _seated(source, roll)
    chan = next(iter(seat.bench.note_regions))
    was = next(e[3] for e in roll.events if e[2] == 0)

    # A region nobody drew.
    assert "no score box region" in seat.run("transpose", "__nb_c9_9__",
                                             was, was + 1)
    # A pitch that region does not sound: the picture and the file
    # disagree, which is a refusal rather than a guess.
    assert "sounds" in seat.run("transpose", chan, was + 7, was + 8)
    assert seat.view.text() == source, "a refusal wrote to the file"


def test_a_note_written_once_and_played_many_times_says_so():
    """Not refused — *said*.  The bytes are one atom, so moving it moves
    every voicing, and a box that offered to move "just this one" would
    be lying about the file."""
    from gestate.scorebox import transposed

    source, roll = _rolled("chopin.ges")
    note = next(i for i, e in enumerate(roll.events)
                if sum(1 for o in roll.events
                       if o[2] == e[2] and o[3] == e[3]) > 1)
    _text, said = transposed(source, roll, note, roll.events[note][3] + 1)
    assert "played" in said and "times" in said, said


def test_take_ink_is_refused_with_the_generators_line():
    """A note the dice drew.  The edit it would ask for is `below 4 s`,
    which is programming rather than a gesture."""
    from gestate.scorebox import RefusedError, transposed

    source, roll = _rolled("noted.ges", "tune")
    note = next(i for i, e in enumerate(roll.events)
                if roll.leaves[e[2]].chancy)
    with pytest.raises(RefusedError) as caught:
        transposed(source, roll, note, 60)
    said = str(caught.value)
    assert "drawn" in said and str(roll.leaves[roll.events[note][2]].line) \
        in said, said


def test_a_pitch_the_box_cannot_point_at_is_refused():
    """`minute.ges` reaches its pitches through a binder one definition
    away; the box says where it looked and declines."""
    from gestate.scorebox import RefusedError, transposed

    source, roll = _rolled("minute.ges", "score")
    note = next(i for i, e in enumerate(roll.events)
                if not roll.leaves[e[2]].chancy
                and not [a for a in roll.leaves[e[2]].atoms if a[3] == e[3]])
    with pytest.raises(RefusedError, match="not written"):
        transposed(source, roll, note, 60)


def test_a_doubled_note_in_a_chord_is_ambiguous():
    """Two atoms with one value on a line — an octave doubled at the
    unison, a pitch that happens to equal a velocity.  Guessing which
    one the hand meant would be a coin toss the file cannot see."""
    from gestate.scorebox import RefusedError, build_rolls, transposed

    source = (AUDIO / "chopin.ges").read_text().replace(
        "stroke 55 59 64", "stroke 55 59 55", 1)
    assert "stroke 55 59 55" in source, "the premise: a doubled note"
    source += "\nnotes score\n"
    roll = build_rolls(source, asks(source), RATE, 0)[0]
    note = next(i for i, e in enumerate(roll.events)
                if e[3] == 55 and "stroke 55 59 55"
                in source.splitlines()[roll.leaves[e[2]].line - 1])

    with pytest.raises(RefusedError, match="more than once"):
        transposed(source, roll, note, 57)


def test_a_file_that_moved_under_the_picture_is_refused():
    """The descent reads the *expanded* text, so a column can be a
    character out.  The literal is read back before anything is written
    — a mismatch refuses rather than corrupting a line."""
    from gestate.scorebox import RefusedError, transposed

    source, roll = _rolled("noted.ges", "ground")
    line = roll.leaves[roll.events[0][2]].line
    lines = source.splitlines(keepends=True)
    lines[line - 1] = "  " + lines[line - 1]          # two columns adrift
    with pytest.raises(RefusedError, match="moved under the picture"):
        transposed("".join(lines), roll, 0, 42)
