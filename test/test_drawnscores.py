"""A flat note file the score is written in — `spec/drawnscores.md`.

**The claim this file executes:** a `.notes` file says the same piece as
the `.ges` it replaces, note for note, and says the things
`doc/notes/notes-on-writing-a-piece.md` found a `.ges` cannot say.

The pair is `examples/audio/arc.ges` and `examples/audio/arcnotes.ges`,
which stand side by side on purpose.  `arc.ges` is the exhibit that log
was written from — five hundred lines of notes spelled out by hand, and
overwriting it would have destroyed the measurement.  So parity here is
a real A/B between two files a person can render and hear, which is
better evidence than a rewrite would have been.

**Where parity stops, and it stops by design.**  `arc.ges` writes sixteen
different velocities as raw floats; the format writes eight named
dynamics, because W4 of that log is that the floats were invented by
their writer and checkable by nobody.  So the claim held below is
*every note at the same tick, for the same length, on the same bank, at
the same pitch* — and the velocity difference is measured rather than
waved at.
"""

from __future__ import annotations

import contextlib
import random
import tempfile
import time
from pathlib import Path

import pytest

from gestate import notes
from gestate.audioscore import perform_voices

ROOT = Path(__file__).resolve().parents[1]
ARC = ROOT / "examples" / "audio" / "arc.ges"
ARCNOTES = ROOT / "examples" / "audio" / "arcnotes.ges"
NOTES = ROOT / "examples" / "audio" / "arc.notes"


def _events(source: str, arc: bool = False):
    """`(bpm, [(onset, offset, bank, key, loudness)])` — a piece, in ticks.

    Two field orders, because the two files carry different payloads and
    that is the point of the comparison.  `arc.ges` declares its own
    `Tone Float Int Int` — velocity, key, manner — as twenty-three other
    pieces declare their own; `arcnotes.ges` declares none and gets
    `audio.ges`'s `Tone Int Int Int` — key, level, manners.  The loudness
    is put on one scale here so the assertion is about the music rather
    than about the record.
    """
    bpm, raw = perform_voices(source, "", 48000, 0)
    return bpm, sorted(
        (on, off, bank,
         payload[0][1] if arc else payload[0][0],
         payload[0][0] if arc else _LOUDNESS[payload[0][1]])
        for on, off, bank, payload in raw)


#: `audio.ges`'s `loudness` — a dynamic as a weight, in even eighths.
#: Spelled again here rather than imported because a test that computed
#: it the way the library does would agree with the library about a
#: mistake (`manifesto.md` §"The three ways an instrument fails").
_LOUDNESS = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]


def _arcnotes(text: str | None = None) -> str:
    """`arcnotes.ges` expanded, optionally against a rewritten note file."""
    if text is None:
        return notes.read(ARCNOTES)
    parsed = notes.parse(text, "arc.notes")
    body, _ = notes.declarations(parsed)
    source = ARCNOTES.read_text().replace('include "arc.notes"', "")
    known = {s.name: set(s.voices) for s in parsed.sections}
    return notes._dots(source + "\n" + body, known)


# ── 1.  Parity ──────────────────────────────────────────────────────────────


def test_the_same_notes_at_the_same_ticks():
    """Acceptance 1.  Every note of `arc.ges`, in `arcnotes.ges`.

    Onset, offset, bank and key, all 219 of them.  Not "similar": the
    format claims to be a different *spelling* of the same score, and
    anything less would be a different piece.
    """
    was_bpm, was = _events(ARC.read_text(), arc=True)
    now_bpm, now = _events(_arcnotes())

    assert was_bpm == now_bpm == 92
    assert len(was) == len(now) == 291, "the two files do not hold the same count"
    for old, new in zip(was, now):
        assert old[:4] == new[:4], (
            f"arc.ges plays {old[3]} at {old[0]}-{old[1]} on `{old[2]}`; "
            f"arcnotes.ges plays {new[3]} at {new[0]}-{new[1]} on `{new[2]}`")


def test_the_velocity_difference_is_the_one_the_format_chose():
    """Acceptance 1's stated exception, held to a number.

    Named rather than tolerated.  A raw float is what W4 is about, so the
    format refusing to carry sixteen of them is the design working — but
    a design that quietly moved a piece would be indistinguishable from a
    bug, so the size of the move is asserted.
    """
    _, was = _events(ARC.read_text(), arc=True)
    _, now = _events(_arcnotes())
    moved = [abs(o[4] - n[4]) for o, n in zip(was, now) if abs(o[4] - n[4]) > 1e-9]

    assert len(moved) == 273, f"{len(moved)} of 291 velocities moved, not 273"
    assert max(moved) <= 0.05 + 1e-9, f"worst velocity move is {max(moved)}"
    # **Sixteen, and it was fifteen until 2026-09-05.**  The missing
    # one belonged to `bass`, which `arc.ges` defined in twenty-four
    # bars and never played (`fixme.md` F198).  This assertion is how
    # that defect was first seen — it failed at 15 against an expected
    # 16 — and it is left in as the count of what *sounds*, so the day
    # the score drops a voice again the number says so.
    assert len({round(v[4], 6) for v in was}) == 16
    assert set(round(v[4], 6) for v in now) <= set(_LOUDNESS), (
        "every loudness that sounds should be one of the eight levels")


# ── 2.  The bar is a thing ──────────────────────────────────────────────────


def test_a_fifth_beat_in_a_four_beat_bar_is_refused():
    """Acceptance 2, and it is W3 of the log.

    *"A fifth note in `a3` would compile, shift everything after it by a
    beat, and be found by ear an hour later."*  It does not compile here,
    and the refusal names the file, the line and the bar.
    """
    text = ("section A  bars 2  beats 4  voices lead\n"
            "note  section A  bar 1  at 0    len 96  voice lead  key 60  vel mf\n"
            "note  section A  bar 1  at 384  len 96  voice lead  key 62  vel mf\n")
    with pytest.raises(notes.NotesError) as caught:
        notes.parse(text, "five.notes")
    said = str(caught.value)
    assert "five.notes:3" in said and "at 384" in said and "bar 1" in said
    assert "384 ticks" in said


def test_a_bar_past_the_end_of_a_section_is_refused():
    text = ("section A  bars 2  beats 4  voices lead\n"
            "note  section A  bar 3  at 0  len 96  voice lead  key 60  vel mf\n")
    with pytest.raises(notes.NotesError, match=r"`bar 3`.*has 2 bars"):
        notes.parse(text, "over.notes")


def test_a_tie_across_the_bar_line_is_a_length_and_is_allowed():
    """The other half of the same rule, and it has to be the other way.

    A note may *last* past its bar — that is a tie, and every notation
    has one.  What may not happen is a note *starting* outside its bar,
    which is the thing that shifts a piece.
    """
    text = ("section A  bars 2  beats 4  voices lead\n"
            "note  section A  bar 1  at 288  len 192  voice lead  key 60  vel mf\n")
    parsed = notes.parse(text, "tie.notes")
    assert parsed.notes[0].length == 192


# ── 3.  The voices cannot drift ─────────────────────────────────────────────


def test_deleting_a_bar_of_one_voice_leaves_the_piece_the_same_length():
    """Acceptance 3, and it is W5 and W8 together.

    *"If one of them had twenty-three bars the piece would still compile
    and everything after the short one would be a bar out."*  Here the
    bar count is declared and every note names its bar, so a voice that
    has lost a bar loses that bar and nothing else moves.
    """
    kept = [line for line in NOTES.read_text().splitlines()
            if not (line.startswith("note ") and "  section C " in line
                    and "  bar 1 " in line and "  voice middle " in line)]
    _, was = _events(_arcnotes())
    _, now = _events(_arcnotes("\n".join(kept) + "\n"))

    assert len(now) == len(was) - 1, "exactly the deleted note should be gone"
    assert max(e[1] for e in now) == max(e[1] for e in was), (
        "the piece changed length when one voice lost a bar")
    gone = set(was) - set(now)
    assert {e[2] for e in gone} == {"chord"} and len(gone) == 1


# ── 4.  Reflow ──────────────────────────────────────────────────────────────


def test_a_shuffled_file_is_the_same_piece():
    """Acceptance 4 — gate three, *no significant whitespace and no nesting*.

    Every record names its own section, bar and voice, so the file has no
    order.  A format whose meaning survives being reflowed by anything is
    a format an editor, a diff tool or a session can rewrite without
    reading it carefully.
    """
    lines = [l for l in NOTES.read_text().splitlines() if l.strip()]
    shuffled = list(lines)
    random.Random(4).shuffle(shuffled)
    assert shuffled != lines

    _, was = _events(_arcnotes())
    _, now = _events(_arcnotes("\n".join(shuffled) + "\n"))
    assert was == now


def test_indentation_means_nothing():
    plain = NOTES.read_text()
    indented = "\n".join(("      " + l if l.strip() else l)
                         for l in plain.splitlines()) + "\n"
    assert notes.write(notes.parse(indented, "x")) == notes.write(
        notes.parse(plain, "x"))


# ── 5.  The round trip ──────────────────────────────────────────────────────


def test_writing_the_shipped_file_back_is_a_no_op():
    """Acceptance 5 — gate four, *a stable order*.

    Two writings of one phrase are byte-identical, so a diff shows what
    changed and nothing else.  Held against the file that ships, not
    against a fixture, because the property is only worth anything if the
    real file has it.
    """
    text = NOTES.read_text()
    assert notes.write(notes.parse(text, "arc.notes")) == text


def test_moving_one_note_in_time_moves_it_among_its_own_voice():
    """**F199, and the gate it never had.**

    The old claim was *moving one note changes exactly one line*, and the
    old test proved it by changing a **key** — which is not part of the
    canonical order.  A drag in *time* is what a roll is for, and under
    the tick-major order it moved **five** lines for one note.

    Henri chose voice-major on 2026-09-05, so a note now reorders only
    among its own voice's notes in its own bar.  The rule is exact:
    **one line per position it moves past, plus one** — which is
    inherent to any sorted file and is worth writing down rather than
    approximating, because the next person will otherwise re-derive it
    from a surprise.
    """
    text = NOTES.read_text()
    before = text.splitlines()

    def moved(**change):
        parsed = notes.parse(text, "arc.notes")
        one = notes.ordered(parsed)[40]
        parsed.notes[parsed.notes.index(one)] = notes.Note(
            **{**one.__dict__, **change})
        after = notes.write(parsed).splitlines()
        assert len(before) == len(after), "a drag must not change the length"
        return sum(1 for a, b in zip(before, after) if a != b)

    assert moved(at=96 + 48) == 2, "half a beat: past one neighbour"
    assert moved(at=288) == 3, "a whole beat: past two"
    # And the property the whole format rests on is unaffected by any of
    # it: the note's own line still carries the whole of its own edit.
    assert moved(key=64) == 1


def test_moving_one_note_changes_exactly_one_line():
    """The property the roll rests on — `spec/north_star.md`'s law, here
    for free rather than by careful implementation."""
    text = NOTES.read_text()
    parsed = notes.parse(text, "arc.notes")
    one = notes.ordered(parsed)[40]
    moved = notes.Note(**{**one.__dict__, "key": one.key + 2})
    parsed.notes[parsed.notes.index(one)] = moved

    before = text.splitlines()
    after = notes.write(parsed).splitlines()
    assert len(before) == len(after)
    differ = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(differ) == 1, f"{len(differ)} lines changed for one note"
    assert f"key {one.key + 2}" in after[differ[0]]


# ── 6.  Every note is written down ──────────────────────────────────────────


def test_every_note_of_the_file_is_one_line_and_carries_its_own_pitch():
    """Acceptance 6, as far as this slice reaches — and said exactly.

    `card:drawn-scores.md` §"The editing surface, measured" counted the
    score box at 0-5% on real pieces, because provenance is *guessed by
    value*: the atom is the one literal in a leaf whose value is the
    note's key, and a computed pitch has no such literal.

    What is executed here is the property that makes the guess
    unnecessary — **every sounding note has exactly one line of the file
    that wrote it, and that line spells the pitch as a literal**.  There
    is nothing to search for.  Wiring the roll to follow provenance into
    the `.notes` file is the slice after this one; this is the half the
    format is responsible for, and it is 100%.
    """
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    _, played = _events(_arcnotes())

    assert len(parsed.notes) == len(played) == 291
    lines = NOTES.read_text().splitlines()
    for one in parsed.notes:
        written = lines[one.line - 1]
        assert written.startswith("note "), one
        assert f"key {one.key}" in written

    assert len({n.line for n in parsed.notes}) == len(parsed.notes), (
        "two notes claim the same line")

    _, where = notes.declarations(parsed)
    assert len(where) == len(parsed.notes), (
        "the expansion lost a note's line on the way into `.ges`")
    assert sorted(where.values()) == sorted(n.line for n in parsed.notes)


# ── 7.  The mode lamp ───────────────────────────────────────────────────────


def test_the_mode_reports_and_does_not_refuse():
    """Acceptance 7, and it is decision 3.

    A ♯11 over a dominant is the whole of `arc.ges`'s A section and is
    idiomatic, not a typo.  A check that refused out-of-mode notes would
    refuse the blues, so the mode is a lamp: it names what is outside and
    the author decides.
    """
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    outside = notes.outside(parsed)

    # **Thirteen of 291, and it was six before the bass was played.**
    # The first is W2's own sentence answered: *"nothing can check that
    # 68 is the sharp fourth and not a typo for 67"*.  Section A is D
    # lydian, whose fourth is 68; bar 3 of the melody is a **67**, and
    # the lamp says so.
    #
    # It is not a typo, and the bass is now the proof: bar 3 is the IV,
    # and `bass` plays a G under that melody G.  A lamp that refused
    # would have refused the chord the section is built on — which is
    # exactly why this reports and never refuses.
    assert len(outside) == 13, [(n.line, d) for n, d in outside]
    first = outside[0][0]
    assert (first.section, first.bar, first.voice, first.key) == ("A", 3, "melody", 67)
    assert outside[0][1] == 5, "the natural fourth, in a mode whose fourth is sharp"
    assert any(n.voice == "bass" and n.key % 12 == 7 for n, _ in outside), (
        "the IV's own root is out of lydian, and that is the point of it")
    # And it loaded.  That is the other half of the assertion.
    assert len(parsed.notes) == 291


def test_a_section_with_no_mode_says_nothing():
    text = ("section A  bars 1  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 61  vel mf\n")
    assert notes.outside(notes.parse(text, "quiet.notes")) == []


# ── The refusals, one each ──────────────────────────────────────────────────


@pytest.mark.parametrize("line,says", [
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  vel loud",
     "is not a dynamic"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf  manner sharp",
     "is not a manner"),
    ("note  section A  bar 1  at 0  len 96  voice horn  key 60  vel mf",
     "has no voice `horn`"),
    ("note  section B  bar 1  at 0  len 96  voice lead  key 60  vel mf",
     "no section `B`"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf  loud 3",
     "is not a field here"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60",
     "missing `vel`"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf  vel f",
     "`vel` is written twice"),
    ("note  section A  bar 1  at 0  len 0  voice lead  key 60  vel mf",
     "at least one tick"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 200  vel mf",
     "not a MIDI key number"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  spell d4  vel mf",
     "names key 62, and this note is `key 60`"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  spell middle-c  vel mf",
     "is not a pitch name"),
])
def test_each_mistake_is_named_in_the_author_s_terms(line, says):
    text = "section A  bars 1  beats 4  voices lead\n" + line + "\n"
    with pytest.raises(notes.NotesError, match=says.replace("`", "`")):
        notes.parse(text, "one.notes")


def test_a_positional_value_is_refused():
    """Gate two — *every field named, never positional*.

    The failure it is for: two fields of one shape telling apart only by
    position is what made `manner` unfindable, and a format that allowed
    one bare number would allow the same mistake back in.
    """
    text = ("section A  bars 1  beats 4  voices lead\n"
            "note  A  1  0  96  lead  60  mf\n")
    with pytest.raises(notes.NotesError, match="is not a field here"):
        notes.parse(text, "bare.notes")


def test_the_same_note_written_twice_is_allowed_and_named():
    """**The constraint belongs on the gesture, not on the bytes.**

    This refused at `parse` until 2026-09-05, when a half-written sketch
    of Henri's was rejected wholesale — and took the collection of a
    whole test file with it.  His call: *"lets do the middle one.  I
    think that's fairly fair."*

    Writing two identical notes is merely redundant; the renderer plays
    both and that is what the file says.  What is genuinely impossible is
    a **drag**: nothing in a click on one of two identical lines says
    which to rewrite, so `spec/north_star.md`'s byte-exact law has no
    answer.  `doubled` is the predicate rung 4 owes.
    """
    text = ("section A  bars 1  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf\n"
            "note  section A  bar 1  at 0  len 48  voice lead  key 60  vel f\n")
    parsed = notes.parse(text, "twice.notes")
    assert len(parsed.notes) == 2, "a hand-written file may say it twice"
    assert [(a.line, b.line) for a, b in notes.doubled(parsed)] == [(2, 3)]

    # And it still round-trips, which is what makes allowing it safe:
    # identical notes sort adjacently and `sorted` is stable.
    once = notes.write(parsed)
    assert notes.write(notes.parse(once, "twice.notes")) == once

    # The shipped file has none, so the gesture is unblocked on it.
    assert notes.doubled(notes.parse(NOTES.read_text(), "arc.notes")) == []


# ── The vocabulary is one vocabulary ────────────────────────────────────────


def test_the_manners_are_audio_ges_s_manners():
    """Two spellings of one vocabulary is what `spec/annotations.md` was
    written to stop, so the names here are held to the tree's."""
    source = (ROOT / "gestate" / "audio.ges").read_text()
    for name, bit in notes.MANNERS.items():
        declared = f"{name.capitalize()} : Int\n{name.capitalize()} = {bit}"
        assert declared in source, f"`{name}` is not {bit} in audio.ges"


def test_the_dynamics_are_audio_ges_s_dynamics():
    source = (ROOT / "gestate" / "audio.ges").read_text()
    for index, name in enumerate(notes.LEVELS):
        spelt = name.capitalize()
        assert f"{spelt} : Int\n{spelt} = {index}" in source, (
            f"`{name}` is not {index} in audio.ges")


def test_a_beat_is_the_tree_s_beat():
    from gestate.midi import TICKS_PER_BEAT

    assert notes.TICKS_PER_BEAT == TICKS_PER_BEAT == 96


# ── The include door ────────────────────────────────────────────────────────


def test_a_program_with_no_include_is_untouched():
    """The contract `voices` has: a feature costs nothing to a program
    that does not use it."""
    source = ARC.read_text()
    assert notes.expand(source, ARC.parent) is source


def test_the_include_line_is_blanked_and_the_lines_below_do_not_move():
    """`audiovoices.py`'s rule, and for its reason: every line below an
    `include` would otherwise shift, and `audiospans` would place the
    author's own knobs against the wrong ones."""
    was = ARCNOTES.read_text().splitlines()
    now = notes.read(ARCNOTES).splitlines()
    assert len(now) > len(was), "the declarations should be appended, not spliced"

    at = [i for i, line in enumerate(was) if line.startswith("include ")]
    assert len(at) == 1
    assert now[at[0]] == "", "the `include` line should be blanked, not removed"
    # Every other line of the author's file stays on the line it was on.
    # `A.melody` becomes a generated name in place, which is the one
    # rewrite — the *line* does not move, which is the property
    # `audiospans` needs.
    for index, line in enumerate(was):
        if index == at[0]:
            continue
        voices = {"melody", "upper", "middle", "lower", "bass"}
        assert now[index] == notes._dots(
            line, {"A": voices, "B": voices, "C": voices})


def test_an_include_of_a_file_that_is_not_there_says_so():
    with pytest.raises(notes.NotesError, match="no such file"):
        notes.expand('include "nowhere.notes"\n', ARCNOTES.parent)


def test_a_voice_the_section_does_not_have_is_refused_where_it_is_written():
    source = ARCNOTES.read_text().replace("A.melody", "A.trumpet")
    with pytest.raises(notes.NotesError, match=r"`A\.trumpet` names no voice"):
        notes.expand(source, ARCNOTES.parent)


def test_a_projection_out_of_something_that_is_not_a_section_is_left_alone():
    """The one difference from `voices.NAME`, and it is forced: `voices`
    is a reserved word and a section name is the author's, so `x.field`
    has to keep meaning what it always meant."""
    out = notes.expand('include "arc.notes"\nq = thing.field\n', ARCNOTES.parent)
    assert "thing.field" in out
    assert notes.bound("A", "melody") in notes.expand(
        'include "arc.notes"\nq = A.melody\n', ARCNOTES.parent)


def test_a_program_read_without_the_door_is_told_so():
    """The leak, named — `spec/drawnscores.md` §"What the building taught".

    A tool that calls `Path.read_text()` instead of `notes.read` hands the
    parser a bare `include` line, and what it says is *"expected '=', got
    end of line"* about a line the author wrote correctly.  So both
    assemblers refuse it first and say whose fault it is.

    **Both**, and that is the point of the second half: the score path and
    the sound path are different functions with different parameter names,
    and the guard was written once and pasted.  It was wrong in
    `assemble_performance` — `source` where the parameter is `synth` — and
    every test passed, because nothing here rendered a scored program
    through the CLI until somebody did it by hand.
    """
    from gestate.audio import assemble
    from gestate.audioscore import assemble_performance

    bare = ARCNOTES.read_text()
    with pytest.raises(notes.NotesError, match="read without"):
        assemble(bare, 44100)
    with pytest.raises(notes.NotesError, match="read without"):
        assemble_performance(bare, "", 44100)


def test_the_piece_renders_through_the_command_line():
    """Gemba: the thing a person actually types.

    Every other test here calls a function.  This one runs the renderer's
    own argument parsing, its file reading and its error boundary, which
    is where the two mistakes above were living.
    """
    import tempfile

    from gestate import audioperform

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "take.wav"
        code = audioperform.main([str(ARCNOTES), "-o", str(out),
                                  "--seconds", "1.5", "--rate", "8000"])
    assert code == 0


# ── What the window shows, and what it compiles ─────────────────────────────

from gestate.audioeditor import Workbench            # noqa: E402


#: A player that writes into a file instead of into the room —
#: `test_audioeditor._pacer`'s rule, and its reason: *every `Workbench`
#: in this file takes a `command`, whether or not the test goes on to
#: start it.  The one that does not is a test waiting to make a noise.*
def _pacer(out: Path) -> list:
    import sys

    return [sys.executable, "-c",
            "import sys, time\n"
            "out = open(sys.argv[1], 'wb')\n"
            "while True:\n"
            "    chunk = sys.stdin.buffer.read(4096)\n"
            "    if not chunk: break\n"
            "    out.write(chunk); out.flush(); time.sleep(0.04)\n",
            str(out)]


@contextlib.contextmanager
def _copied():
    """The pair, in a scratch directory — because these tests write."""
    with tempfile.TemporaryDirectory() as tmp:
        here = Path(tmp) / "arcnotes.ges"
        here.write_text(ARCNOTES.read_text())
        (Path(tmp) / "arc.notes").write_text(NOTES.read_text())
        yield here


def _settled(bench, words: tuple, timeout: float = 60.0) -> list:
    """Wait until the build thread says one of `words`, then hand back
    everything it said.

    `test_audioeditor._settle`'s rule: the message is the last thing a
    build does, so it is the only honest *done*.  The words are the
    caller's because the two paths end differently — a start says
    *playing*, a rebuild says *auditioning* — and a wait that accepted
    either would let a test pass on the wrong one.
    """
    end = time.time() + timeout
    while time.time() < end:
        said = list(bench.messages)
        if any(w in m for m in said for w in words):
            return said
        time.sleep(0.05)
    raise AssertionError(f"the rebuild never finished; said {bench.messages}")


def test_the_window_shows_the_file_and_not_the_expansion():
    """**The defect Henri found by opening the file** — 2026-09-05.

    `Workbench.source()` fills the editor's text buffer
    (`workbench.py:829`) *and* was the door every compiler went through,
    so routing the include expansion into it made the window display a
    program the author had not written: the `include` line blanked and
    nine hundred generated lines after it.  A `Ctrl-S` would have made
    that true on disk.

    His words: *"arcnotes.ges … I don't find the `include` there in other
    than comments."*

    Two needs, two methods.  `source` is the author's bytes — what the
    window shows and what a save writes.  `program` is what compiles.
    One method serving both is how a view becomes a second source of
    truth, which is the thing this whole format was designed not to be.
    """
    bench = Workbench(ARCNOTES, rate=22050, block=256)
    assert bench.source() == ARCNOTES.read_text(), (
        "the editor's buffer is not the file")
    assert 'include "arc.notes"' in bench.source()

    program = bench.program()
    assert 'include "arc.notes"' not in program
    assert notes.bound("A", "melody") in program


def test_the_window_compiles_what_it_is_looking_at():
    """The other half: an edit in the buffer is what plays.

    `program(text)` takes the window's own copy, because a person who has
    typed something and not saved it should hear that and not the file.
    """
    bench = Workbench(ARCNOTES, rate=22050, block=256)
    edited = ARCNOTES.read_text().replace("bpm = 92", "bpm = 120")
    program = bench.program(edited)
    assert "bpm = 120" in program
    assert notes.bound("C", "bass") in program


def test_the_editor_can_build_the_piece():
    """Gemba again, one layer up: the banks and the score, as the editor
    finds them — which is the path `source()` used to break."""
    bench = Workbench(ARCNOTES, rate=22050, block=256)
    allocators = bench._allocators()
    assert set(allocators) == {"song", "chord", "ground"}


def test_the_window_can_audition_the_piece():
    """**The second half of Henri's find** — 2026-09-05, from his own
    session log (`arcnotes-session.ges`):

        audition                               #= auditioning
        #! not applied: `include "arc.notes"` reached the assembler …

    `apply` and `audition` are handed the *window's buffer*, which has an
    `include` in it and no path attached, so the guard fired on the one
    gesture the editor exists for.  `_built` now expands before it
    compiles and saves the author's bytes unchanged, which is the same
    split `source`/`program` made one layer up.

    Driven through `apply` rather than through a compiler directly,
    because the thing that broke was the *editor's* path and a test that
    called the compiler would have stayed green through both bugs.
    """
    with _copied() as here:
        bench = Workbench(here, rate=22050, block=256,
                          command=_pacer(here.parent / "stream.raw"))
        try:
            # The open: `apply` with nothing playing yet starts the
            # instrument, which is `_start` and `program()`.
            bench.apply(bench.source(), save=True)
            said = _settled(bench, ("playing ", "not applied",
                                    "still not playing"))
            assert not any("not applied" in one or "still not playing" in one
                           for one in said), said

            # And then the gesture his log caught — `audition`, which goes
            # the other way, through `_builds` into `_built`.  Both paths,
            # because only the second one was broken and only the first
            # would have been covered by a careless test.
            bench.messages.clear()
            bench.audition(bench.source())
            said = _settled(bench, ("auditioning", "not applied", "rebuilt"))
            assert any("auditioning" in one for one in said), said
        finally:
            bench.stop()

        # And the file on disk is still the author's, `include` and all.
        assert here.read_text() == ARCNOTES.read_text()


def test_a_bad_include_is_reported_at_the_window_and_the_file_is_kept():
    """The failure the same path owes: a name that is not a file is a
    mistake a person made at the window, so it is said there — and the
    save still happened, because an editor that will not save is not an
    editor."""
    with _copied() as here:
        bench = Workbench(here, rate=22050, block=256,
                          command=_pacer(here.parent / "stream.raw"))
        broken = ARCNOTES.read_text().replace('include "arc.notes"',
                                              'include "nowhere.notes"')
        try:
            bench.apply(broken, save=True)
            said = _settled(bench, ("no such file", "playing ", "rebuilt"))
        finally:
            bench.stop()

        assert here.read_text() == broken, "the save must still have happened"
        assert any("no such file" in one for one in said), said


def test_the_bar_does_not_say_behind_on_a_file_nobody_has_touched():
    """**The other half of Henri's find** — *"It shows that it's not
    auditioned at the start."*

    `behind(text)` compares the window's own buffer to what was built.
    Storing the *expanded* text there made the answer `True` the moment a
    file had an `include` in it, on every keystroke, forever — the bar
    reporting an edit nobody had made.

    So a build now records both: `_built_from` is the author's bytes,
    which is what *behind* is a question about, and `_built_program` is
    what the compiler saw, which is what *may this rebuild skip* is a
    question about.  One field could not answer both.
    """
    with _copied() as here:
        bench = Workbench(here, rate=22050, block=256,
                          command=_pacer(here.parent / "stream.raw"))
        try:
            bench.apply(bench.source(), save=True)
            _settled(bench, ("playing ", "not applied", "still not playing"))

            assert bench._built_from == here.read_text(), (
                "what a build is compared against must be the author's text")
            assert bench._built_program is not None
            assert 'include "arc.notes"' not in bench._built_program
            assert not bench.behind(bench.source()), (
                "a file nobody has touched is not behind its own sound")
            assert bench.behind(bench.source() + "\n# a real edit\n")
        finally:
            bench.stop()


# ── The payload nobody has to declare ───────────────────────────────────────


def test_a_piece_that_declares_no_payload_gets_the_library_s():
    """`arcnotes.ges` declares no type, no `Notable`, no `FromNote`.

    Henri, 2026-09-05, on the version that did: *"The `Tone := Tone Float
    Int Int` feels like ceremony in the file.  I wonder why it is
    necessary there now?"*  It was not.  Twenty-four payload
    declarations across `examples/audio/` under seven names, every one of
    them a key, a loudness and (since `spec/annotations.md`) a manner —
    a freedom offered two dozen times and exercised nowhere.
    """
    source = ARCNOTES.read_text()
    assert "Tone :=" not in source, "the piece should not declare a payload"
    assert "instance Notable" not in source
    assert "instance FromNote" not in source
    assert "!noteHz s" in source and "!noteLoud s" in source

    library = (ROOT / "gestate" / "audio.ges").read_text()
    assert "Tone := Tone Int Int Int" in library
    assert "instance Notable Tone" in library
    assert "instance FromNote Tone" in library


def test_the_manner_accessors_stay_the_piece_s():
    """What a mark *does* is the voice's answer and not the library's.

    `spec/annotations.md` is the whole argument: a staccato is a filter
    and an envelope in this piece and would be a bow stroke in another,
    so `bowOf`/`pushOf`/`glideOf` are exactly the part that must not move
    into `audio.ges` however repetitive it looks.
    """
    source = ARCNOTES.read_text()
    for one in ("bowOf", "pushOf", "glideOf"):
        assert f"{one} : Tone -> Float" in source, one
    library = (ROOT / "gestate" / "audio.ges").read_text()
    for one in ("bowOf", "pushOf", "glideOf"):
        assert one not in library, f"`{one}` belongs to the piece, not here"


def test_a_piece_with_its_own_payload_still_wins():
    """The freedom is kept, and this is what keeps it.

    Eleven pieces declare their own `Tone`, and `prelude.shadow_libraries`
    renames constructors as well as values — so `arc.ges`'s
    `Tone Float Int Int` goes on meaning `arc.ges`'s.  Executed rather
    than argued, because the failure it prevents is silent: two
    constructors wearing one name, and the cons table keeping whichever.
    """
    from gestate.audioscore import perform_voices

    assert "Tone := Tone Float Int Int" in ARC.read_text()
    _, raw = perform_voices(ARC.read_text(), "", 48000, 0)
    # Its own record's order — velocity first — which is only true if the
    # program's declaration beat the library's.
    velocity, key, manner = raw[0][3][0]
    assert isinstance(velocity, float) and 0.0 < velocity <= 1.0
    assert isinstance(key, int) and 21 <= key <= 108


def test_a_bank_may_play_a_payload_the_vocabulary_declares():
    """The expander's own rule, extended.

    `_frame` already looked for a bank's *result* type in the program and
    then in the prelude — *"`synth.ges` declares `Stereo` so that two
    programs mean the same thing by a stereo frame."*  That sentence was
    always about the payload too; until 2026-09-05 the payload lookup
    read the program alone and a library type raised *"neither Float or
    Int nor a data type declared here"*.
    """
    from gestate.audiovoices import banks_of, channels_of

    source = notes.read(ARCNOTES)
    banks = {b.name: b for b in banks_of(source)}
    assert set(banks) == {"song", "chord", "ground"}
    # Three payload fields — key, level, manners — plus the timing ones,
    # and `channels_of` is asked with no prelude in hand.
    rows = channels_of(source, banks["song"])
    assert len(rows) == 4, "four voices in the `song` bank"
    assert len(rows[0]) == len(channels_of(ARC.read_text(),
                                           banks_of(ARC.read_text())[0])[0]), (
        "the library payload and arc.ges's own are both three fields")


# ── What a bar sounds, said in words — card:the-first-jam.md item 2 ─────────


def test_a_degree_is_named_by_its_place_in_the_mode():
    """Six semitones over the tonic is lydian's ♯4 and locrian's ♭5.

    The same pitch, a different scale position.  Calling locrian's ♭5 a
    sharp fourth would misname the interval
    `doc/notes/notes-on-writing-a-piece.md` spends a day on.
    """
    assert notes.degree_of(68, "D", "lydian") == "♯4"
    assert notes.degree_of(61, "G", "locrian") == "♭5"
    # And a tone the mode does not own has no position in it, so the
    # chromatic reading answers.
    assert notes.degree_of(67, "D", "lydian") == "4"
    assert notes.degree_of(68, "D") == "♯4"


@pytest.mark.parametrize("key,tonic,mode,want,why", [
    (66, "D", "lydian", "fis4", "the mode's own third, not a flattened ♯4"),
    (68, "D", "lydian", "gis4", "the ♯4 itself"),
    (67, "D", "lydian", "g4", "the ♯4 lowered — sharpening the third is `fisis4`"),
    (64, "D", "phrygian", "e4", "the ♭2 raised — flattening the ♭3 is `fes4`"),
    (61, "D", "lydian", "cis4", "the seventh, in the octave its letter sits in"),
    (68, "Bb", "lydian", "aes4", "the seventh lowered, in a flat key"),
])
def test_a_pitch_is_spelled_the_way_its_mode_asks(key, tonic, mode, want, why):
    """Nearest degree first, then the smallest accidental.

    Both halves were found by getting them wrong: sorting on the
    accidental alone spelled D lydian's third `ges4`, and preferring the
    flat unconditionally spelled D phrygian's second `fes4`.
    """
    assert notes.spell(key, tonic, mode) == want, why


def test_the_one_arbitrary_choice_is_the_documented_one():
    """Where both readings cost exactly one accidental, the flat wins.

    **And this is the case that put names in the file** — the rule is
    unchanged and still arbitrary here, which is why the file may
    overrule it per note; see §"The spelling a rule cannot guess" at the
    foot of this file.
    """
    assert notes.spell(63, "D", "lydian") == "ees4"    # not `dis4`


def test_a_held_note_sounds_in_every_bar_it_spans():
    """The half a list of onsets cannot say, and item 2's whole point:
    a whole-bar chord under a melody is the harmony of that bar."""
    text = ("section A  bars 3  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 1152  voice lead  key 60  vel mf\n")
    heard = notes.sounding(notes.parse(text, "held.notes"))
    assert [(s, b, k) for s, b, k in heard] == [
        ("A", 1, [60]), ("A", 2, [60]), ("A", 3, [60])]


def test_the_report_reads_arc_the_same_way_from_either_file():
    """`arc.notes` and `arc.ges` are the same music, so the report must
    say the same words about them — which is a cross-check on `spell`
    and on `pitch_of` at once, since the two paths reach the pitches by
    completely different routes."""
    import subprocess
    import sys

    def lines(argv):
        out = subprocess.run([sys.executable, "tools/bars.py"] + argv,
                             cwd=ROOT, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        return [l.split(maxsplit=1)[1] for l in out.stdout.splitlines()
                if l.strip()[:1].isdigit()]

    from_notes = lines(["examples/audio/arc.notes"])[:8]
    from_ges = lines(["examples/audio/arc.ges", "D", "lydian"])[:8]
    assert from_notes == from_ges, "the two readings of one piece disagree"
    assert "gis4" in from_notes[0] and "♯4" in from_notes[0]
    assert from_notes[2].endswith("g4"), (
        "bar 3's natural fourth is the note the mode lamp found, named")


# ── Which field of a payload is the pitch — fixme.md F201 ───────────────────


def test_the_pitch_is_found_in_a_payload_of_either_shape():
    """`Tone Float Int Int` puts the key second, `audio.ges`'s own
    `Tone Int Int Int` puts it first, and a reader that assumed a
    position crashed on every piece written since manners landed."""
    from gestate.audioscore import pitch_of

    assert pitch_of(((0.85, 62, 0),)) == 62      # a piece's own payload
    assert pitch_of(((62, 4, 0),)) == 62         # audio.ges's `Tone`
    assert pitch_of(((0.7, 38),)) == 38          # the two-field shape


def test_an_ambiguous_payload_is_refused_rather_than_guessed():
    """A wrong pitch would be a report that reads plausibly and is
    false, which is worse than no report."""
    from gestate.audioscore import ScoreError, pitch_of

    with pytest.raises(ScoreError, match="cannot tell which field"):
        pitch_of(((60, 64),))                    # two playable numbers
    with pytest.raises(ScoreError, match="cannot tell which field"):
        pitch_of(((0.5, 7),))                    # none in the playable range


def test_modecheck_runs_on_a_piece_that_carries_manners():
    """The regression F201 is: `tools/modecheck.py` unpacked every
    payload as a pair, so it crashed on `arc.ges` — the file it was
    written to measure — from the day annotations landed."""
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "tools/modecheck.py", "examples/audio/arc.ges",
         "song", "2"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "123 notes" in out.stdout


# ── The view arrives without being asked ────────────────────────────────────


def test_a_render_says_what_its_bars_sound():
    """*"It needs a 'view', just like how I look toward to that score
    being rendered in the editor."* — Henri, 2026-09-05.

    `card:the-first-jam.md` item 1 named the shape first, for the
    ceiling share: a line after a render puts the criterion into every
    run's own mouth.  This is the same move for item 2, and it is the
    half that makes the report a view rather than a command somebody has
    to think of.
    """
    import io
    import contextlib
    import tempfile

    from gestate import audioperform

    with _copied() as here, tempfile.TemporaryDirectory() as out:
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            code = audioperform.main([str(here), "-o", f"{out}/take.wav",
                                      "--seconds", "1.0", "--rate", "8000"])
        assert code == 0
        page = said.getvalue()
        assert "── section A — D lydian" in page
        assert "gis4" in page and "♯4" in page
        assert "more bars" in page, "it should point at the rest"


def test_a_render_of_a_piece_with_no_include_says_nothing_about_bars():
    """Only where the piece says what key it is in.  Nothing else in this
    tree declares a mode, and a report that guessed a tonic would print
    confident nonsense."""
    import io
    import contextlib
    import tempfile

    from gestate import audioperform

    with tempfile.TemporaryDirectory() as out:
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            audioperform.main([str(ARC), "-o", f"{out}/take.wav",
                               "--seconds", "1.0", "--rate", "8000"])
        assert "sounding" not in said.getvalue()


def test_the_read_hook_answers_for_a_notes_file_and_nothing_else():
    """A `PostToolUse` hook on `Read`, so opening a `.notes` file shows
    its bars — `tools/backlinks.py`'s shape, and its rule: silent on
    everything it is not about, and silent on failure."""
    import json
    import subprocess
    import sys

    def fired(payload):
        out = subprocess.run([sys.executable, "tools/bars.py", "--hook"],
                             cwd=ROOT, input=json.dumps(payload),
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        return out.stdout.strip()

    spoke = fired({"tool_name": "Read",
                   "tool_input": {"file_path": str(NOTES)}})
    said = json.loads(spoke)["hookSpecificOutput"]
    assert said["hookEventName"] == "PostToolUse"
    assert "── section A — D lydian" in said["additionalContext"]

    # Not for another file, not for another tool, and not for a `.notes`
    # that is not there — each of which a reader is about to hear about
    # from whatever they were actually running.
    assert fired({"tool_name": "Read",
                  "tool_input": {"file_path": str(ARC)}}) == ""
    assert fired({"tool_name": "Edit",
                  "tool_input": {"file_path": str(NOTES)}}) == ""
    assert fired({"tool_name": "Read",
                  "tool_input": {"file_path": "no/such.notes"}}) == ""
    assert fired({}) == ""


def test_the_hook_is_not_installed_by_a_session():
    """`.claude/settings.json` is behind the leash — `--install` prints
    the lines and the install is Henri's, exactly as `backlinks.py` has
    it."""
    import subprocess
    import sys

    out = subprocess.run([sys.executable, "tools/bars.py", "--install"],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0
    assert '"matcher": "Read"' in out.stdout
    assert "bars.py --hook" in out.stdout


# ── Where the energy sits — the instrument that was missing ─────────────────


def test_a_render_says_how_much_a_small_speaker_cannot_play():
    """**Henri could not hear his own bass**, 2026-09-05, through four
    passes of rewriting — and no instrument here said why.

    The peak was fine and the RMS was fine, and both are deaf to *where*
    the energy sits: `arc.ges`'s ground bank puts every note between 73
    and 185 Hz through a 320 Hz lowpass, which is under a laptop
    speaker's floor and under most of a phone's.  `doc/instruments.md`'s
    first rule is his — *a missing capability is built the moment the
    need arises* — and this one had cost an hour.
    """
    import tempfile

    from gestate.audioperform import _Meter, SMALL_SPEAKER_HZ

    rate = 8000
    # A 60 Hz tone is under the floor; a 1 kHz tone is well over it.
    import math

    for hz, want_low in ((60.0, True), (1000.0, False)):
        meter = _Meter(1, rate, "second", rate)
        block = [math.sin(2 * math.pi * hz * i / rate) for i in range(rate)]
        meter.feed(block)
        said = meter.low_line()
        share = meter._low_sq / meter._all_sq
        if want_low:
            # 0.77, not 1.0 — the split is two one-poles and a pure tone
            # entirely under the floor still leaks a quarter of itself
            # across.  The docstring carries this number so a reader
            # knows what "77%" means before they meet one.
            assert share > 0.75, f"{hz} Hz read as {share:.0%} low: {said}"
            assert "reproduce little of that" in said
        else:
            assert share < 0.05, f"{hz} Hz read as {share:.0%} low: {said}"
            assert "reproduce little of that" not in said
    assert SMALL_SPEAKER_HZ == 160.0


def test_the_low_share_line_survives_a_silent_render():
    """A render of nothing must not divide by nothing."""
    from gestate.audioperform import _Meter

    meter = _Meter(1, 100, "second", 8000)
    meter.feed([0.0] * 200)
    assert "no signal" in meter.low_line()


def test_the_report_still_says_peak_and_rms():
    """The line is added beside what `--report` already said, not
    instead of it — `spec/firstpiece.md`'s ears are what a CI has."""
    import io
    import contextlib

    from gestate.audioperform import _Meter

    meter = _Meter(1, 4, "bar", 8000)
    meter.feed([0.5, -0.9, 0.2, 0.1] * 2)
    page = io.StringIO()
    with contextlib.redirect_stdout(page):
        meter.say()
    said = page.getvalue()
    assert "report: peak 0.900" in said
    assert "below 160 Hz" in said
    assert "bar   1: rms" in said


# ── Slice 0: the roll a `.notes` file already has ───────────────────────────


def test_a_voice_of_an_included_section_draws_and_is_wholly_editable():
    """**The claim this format exists for, executed** —
    `spec/drawnscores.md` §"The slices after", rung 0.

    `card:drawn-scores.md` §"The editing surface, measured" counted the
    score box at **0–5%** on real `.ges` pieces: provenance is guessed by
    value, and a computed pitch has no literal to point at.  A `.notes`
    line *is* the note, so there is nothing to guess — and this asserts
    the number rather than the argument.

    Nothing was built for it.  `A.melody` is an ordinary `[: Tone :]`
    once the include has run, and the ask names it because the dotted
    rewrite reaches the ask line too.
    """
    import re

    from gestate.scorebox import build_rolls, pitch_atom

    source = notes.read(ARCNOTES)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    # The single-voice asks are what this test is about; the stacked one
    # beside them is `test_a_whole_section_stacks_on_one_roll…`.
    single = [a for a in asks if "||" not in a[1]]
    assert [a for _, a in single] == [notes.bound("A", "melody"),
                                      notes.bound("A", "bass")], asks

    for (_, ask), roll in zip(single, build_rolls(source, single, 22050, 0)):
        assert hasattr(roll, "events"), f"{ask} did not draw: {roll}"
        assert roll.events, f"{ask} drew nothing"
        written = 0
        for index in range(len(roll.events)):
            try:
                _line, _col, _width, value = pitch_atom(roll, index)
            except Exception:                             # noqa: BLE001
                continue
            assert value == roll.events[index][3], (
                "the atom must be the note's own pitch")
            written += 1
        assert written == len(roll.events), (
            f"{ask}: {written} of {len(roll.events)} notes carry a pitch "
            "atom; the whole point is that all of them do")
        assert written == 32


# ── Rung 1: the expansion counts its own offset ─────────────────────────────


def test_every_note_resolves_to_the_file_and_line_that_wrote_it():
    """**Rung 1** — `spec/drawnscores.md` §"The slices after".

    `declarations` always knew which generated line a note was written
    on.  What it cannot know is where its block lands once the author's
    source is in front of it — and that was reconstructed from outside
    on 2026-09-05, by counting the author's lines and adding one for a
    separator.  It was **wrong by one, on the fourth note**, and three
    of four still resolved, which is how it went unnoticed.

    So the concatenation and the counting are one loop now, and this
    asserts the end-to-end join the roll will make: a note drawn on the
    box, back to the line of `arc.notes` that says it.
    """
    import re

    from gestate.scorebox import build_rolls, pitch_atom

    source, where = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    assert asks, "arcnotes.ges should carry the rung-0 asks"

    written = NOTES.read_text().splitlines()
    for roll in build_rolls(source, asks, 22050, 0):
        assert hasattr(roll, "events"), roll
        for index in range(len(roll.events)):
            line, _col, _width, value = pitch_atom(roll, index)
            got = where.get(line)
            assert got is not None, (
                f"a note on expanded line {line} resolves to no file")
            name, at = got
            assert name == "arc.notes"
            # Not "a line exists" — *that* line says *that* pitch.
            assert f"key {value}" in written[at - 1], (
                f"{name}:{at} does not say key {value}: {written[at - 1]!r}")


def test_the_origin_map_answers_for_notes_and_not_for_scaffolding():
    """`long 4 (` and `))` were written by nobody.

    Answering for them would be inventing a provenance, and a roll that
    jumped to a line the author never typed is worse than one that
    admits it cannot.
    """
    source, where = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    lines = source.splitlines()
    assert len(where) == 291, "one origin per note, and no more"
    for at in where:
        assert "fromNote" in lines[at - 1], lines[at - 1]
    scaffolding = [i + 1 for i, line in enumerate(lines)
                   if line.strip().startswith("(long ")]
    assert scaffolding, "the bars are opened by something"
    assert not (set(scaffolding) & set(where)), "scaffolding claims no origin"


def test_a_program_with_no_include_has_no_origins_and_is_unchanged():
    """The contract `voices` has: a feature costs nothing to a program
    that does not use it — including the cost of being copied."""
    source = ARC.read_text()
    text, where = notes.expanded(source, ARC.parent)
    assert text is source
    assert where == {}


# ── Rung 3: a gesture knows which file wrote the note ───────────────────────


def _first_roll():
    """The rung-0 roll of `arcnotes.ges`, with the map beside it."""
    import re

    from gestate.scorebox import build_rolls

    source, origins = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    return build_rolls(source, asks, 22050, 0)[0], origins


def test_a_transpose_of_an_included_note_names_the_file_it_lives_in():
    """**Henri met this the hour rung 0 shipped**, in his own sketch:

        transpose: line 57 is not in this file any more

    The picture is drawn from the *expanded* program and the rewrite
    lands in the author's text.  Identical for a program with no
    `include` — which is every program written before 2026-09-05 — and
    divergent past one, so line 57 of the expansion is past the end of a
    thirty-line file.
    """
    from gestate.scorebox import RefusedError, transposed

    roll, origins = _first_roll()
    author = ARCNOTES.read_text()

    with pytest.raises(RefusedError, match=r"arc\.notes:\d+, not in this file"):
        transposed(author, roll, 0, 64, origins)

    # And without the map it still refuses — just uselessly, which is the
    # sentence that was wrong rather than the safety.
    with pytest.raises(RefusedError, match="not in this file any more"):
        transposed(author, roll, 0, 64)


def test_the_generated_block_is_always_past_the_author_s_last_line():
    """**Why this was never a silent corruption**, checked rather than
    assumed — I nearly wrote the opposite into the tree.

    The expansion appends after the author's text, so a note's line is
    always beyond it and the range check always fires.  Padding the
    author's file pushes the block down with it, which is the property
    that makes it structural rather than lucky.
    """
    from gestate.scorebox import pitch_atom

    for extra in (0, 120):
        text = ARCNOTES.read_text() + "\n".join(
            f"# filler {i}" for i in range(extra))
        source, origins = notes.expanded(text, ARCNOTES.parent)
        authored = len(text.splitlines())
        assert min(origins) > authored, (
            "a generated line landed inside the author's text")
        roll, _ = _first_roll()
        line, _c, _w, _v = pitch_atom(roll, 0)
        assert line > len(ARCNOTES.read_text().splitlines())


def test_a_whole_section_stacks_on_one_roll_with_every_note_placeable():
    """**The thing only a `.notes` roll can draw** — and rung 2.

    A `.ges` box draws an expression and cannot know that `melody` and
    `bass` are the same eight bars; a section declares them.  So W5 and
    W8 stop being merely refusable and become visible.

    It could not be drawn until `scorebox.MAX_LEAVES` was raised on
    2026-09-05: the cap was 48 for a reason that had stopped being true,
    and a stacked section drew with 244 of its notes pointing at a line
    that was not theirs.  This asserts the count rather than the fix.
    """
    import re

    from gestate.scorebox import build_rolls, pitch_atom

    source, origins = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    stacked = [a for a in asks if "||" in a[1]]
    assert len(stacked) == 1, "arcnotes.ges should carry one stacked ask"

    roll = build_rolls(source, stacked, 22050, 0)[0]
    assert hasattr(roll, "events"), roll
    voices = set()
    for index in range(len(roll.events)):
        line, _col, _width, _value = pitch_atom(roll, index)   # never refuses
        where = origins.get(line)
        assert where is not None, f"note {index} resolves to no file"
        voices.add(NOTES.read_text().splitlines()[where[1] - 1].split(
            "voice ")[1].split()[0])
    assert len(roll.events) > 48, (
        "the point is that it is past the old cap; this piece got smaller")
    assert voices == {"melody", "upper", "middle", "lower", "bass"}, voices


# ── Rung 4: the drag writes into the file that owns the note ───────────────


def _first_note(text: str) -> int:
    """The 1-based line of the first `note` record, found and not counted."""
    for i, line in enumerate(text.splitlines(), start=1):
        if line.startswith("note "):
            return i
    raise AssertionError("the fixture has no note records")


def test_a_field_of_a_note_line_is_rewritten_byte_exactly():
    """`spec/north_star.md`'s law, for a `.notes` file.

    One field's bytes change and nothing else — including every other
    field of that same line — which is what makes a drag undoable by
    dragging back.  And the rewrite needs no column arithmetic, because
    the field is named: gate two met from the other side.
    """
    text = NOTES.read_text()
    #: Found rather than counted — a line number written into a test is
    #: a claim about a fixture, and four of them rotted the day
    #: `arc.notes` grew a header.
    at = _first_note(text)
    out, said = notes.retune(text, at, "key", 62, 64)

    assert "key 62 → 64" in said
    was, now = text.splitlines(), out.splitlines()
    differ = [i for i, (a, b) in enumerate(zip(was, now)) if a != b]
    assert differ == [at - 1], "exactly the one line"
    assert now[at - 1] == was[at - 1].replace("key 62", "key 64")
    assert len(out) == len(text), "and the file did not change length"


@pytest.mark.parametrize("where,was,says", [
    # A section line is a record too, since its `bars` is dragged
    # (slice 4): a pitch drag aimed at it is refused on its `key`, the
    # tonic, which never says a number.
    ("section", 62, "says `key D` where the roll thought `key 62`"),
    ("comment", 62, "is not a record"),
    ("note", 999, "the file has moved under the picture"),
    ("past the end", 62, "not in this file any more"),
])
def test_a_rewrite_is_refused_rather_than_forced(where, was, says):
    text = NOTES.read_text()
    line = {"section": text.splitlines().index(
                [l for l in text.splitlines() if l.startswith("section ")][0]) + 1,
            "comment": 1,
            "note": _first_note(text),
            "past the end": 99999}[where]
    with pytest.raises(notes.NotesError, match=says):
        notes.retune(text, line, "key", was, 64)


def test_a_drag_on_an_included_note_writes_that_file_and_says_so():
    """**Rung 4** — the first time this window writes a file it is not
    editing, which is stated rather than hidden.

    There is no buffer for an included file, so the edit reaches the
    disk at once where a `.ges` drag waits for `Ctrl-S`.  The person is
    told which file moved, because a gesture that silently writes
    something you are not looking at is the one thing an editor must
    not do.
    """
    import re

    from gestate.scorebox import build_rolls, pitch_atom

    with _copied() as here:
        source, origins = notes.expanded(here.read_text(), here.parent)
        asks = [(i + 1, m.group(1))
                for i, line in enumerate(source.splitlines())
                for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
        roll = build_rolls(source, asks[:1], 22050, 0)[0]
        line, _c, _w, was = pitch_atom(roll, 0)
        name, at = origins[line]

        target = here.parent / name
        before = target.read_text()
        out, said = notes.retune(before, at, "key", was, was + 2)
        target.write_text(out)

        # The file moved, by one line, and the roll would now draw it there.
        after = target.read_text()
        assert sum(1 for a, b in zip(before.splitlines(), after.splitlines())
                   if a != b) == 1
        assert f"key {was + 2}" in after.splitlines()[at - 1]

        # And the piece still plays, with the note where it was dropped.
        again, _ = notes.expanded(here.read_text(), here.parent)
        assert f"fromNote {was + 2} " in again


# ── The spelling a rule cannot guess — 2026-09-06 ───────────────────────────


def test_the_cadence_the_rule_could_not_spell_is_written_out():
    """The trigger `spec/drawnscores.md` named, fired in the only
    `.notes` file there is.

    The rule takes the flat where both readings cost one accidental, and
    the last bar of `arc.notes` is `73 → 69 → 62` in D phrygian — a
    leading tone resolving up to the tonic, which is a `cis` and cannot
    be a `des`.  The degree column said `7` all along; the letter column
    disagreed with it, on one file, at its cadence.
    """
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    one, = [n for n in parsed.notes
            if n.section == "C" and n.bar == 8 and n.voice == "melody"
            and n.at == 0]
    assert one.key == 73
    assert notes.spell(73, "D", "phrygian") == "des5", "the rule is unchanged"
    assert one.spell == "cis5", "and the file overrules it, on this note"
    assert notes.degree_of(73, "D", "phrygian") == "7", (
        "the two columns of one report now agree about this note")


def test_one_pitch_is_spelled_by_the_section_it_is_in():
    """Why the field is on the note and not on the file.

    Key 61 is `des4` in section B and `cis4` in section C of the shipped
    file — G locrian's flattened fifth and D phrygian's leading tone,
    the same twelve-tone pitch, two different notes.  A spelling table
    per file could not say this and neither can a rule.
    """
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    at_b = [n for n in parsed.notes if n.section == "B" and n.key == 61]
    at_c = [n for n in parsed.notes if n.section == "C" and n.key == 61]
    assert at_b and at_c
    assert all(n.spell is None for n in at_b), "B's is what the rule says"
    assert notes.spell(61, "G", "locrian") == "des4"
    assert [n.spell for n in at_c] == ["cis4"], "C's is written down"


def test_the_report_prints_the_written_letter_where_there_is_one():
    """The field is read back where a person reads the file, or it is a
    thing stored and never looked at."""
    said: list = []
    notes.report(notes.rows_of_notes(NOTES), tell=said.append)
    bars = [l for l in said if l.strip()[:1].isdigit()]
    assert "cis5" in bars[-1] and "des5" not in bars[-1], bars[-1]
    assert "cis4" in bars[-2], bars[-2]
    #: and one bar carries both readings at once — section B's last bar
    #: writes `fis3` and lets the rule spell `des4` beside it, which is
    #: the field doing exactly as much as it claims and no more
    assert "fis3" in bars[15] and "des4" in bars[15], bars[15]
    #: while section A, which wrote none, reads as it did before
    assert "gis4" in bars[0] and "spell" not in bars[0]


def test_a_spelling_travels_with_a_held_note_through_its_bars():
    """A held note is part of every bar it sounds in, and so is the
    letter it was written with — the same walk `sounding` makes."""
    text = ("section A  key D  mode phrygian  bars 3  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 1152  voice lead  key 61"
            "  spell cis4  vel mf\n")
    said = notes.spellings(notes.parse(text, "held.notes"))
    assert said == {("A", 1, 61): "cis4", ("A", 2, 61): "cis4",
                    ("A", 3, 61): "cis4"}


def test_a_note_cannot_be_made_to_contradict_its_own_spelling():
    """The refusal is on the record, so there is one rule and every
    caller meets it — the parser, a drag, and anything that moves a note
    by rebuilding it."""
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    one, = [n for n in parsed.notes if n.spell == "cis5"]
    with pytest.raises(notes.NotesError, match="names key 73"):
        notes.Note(**{**one.__dict__, "key": one.key + 2})
    # and the same note, spelled by nobody, moves freely
    plain = notes.Note(**{**one.__dict__, "spell": None})
    assert notes.Note(**{**plain.__dict__, "key": 75}).key == 75


def test_a_drag_in_pitch_drops_the_written_spelling_and_says_so():
    """A stored letter is an intention about the pitch that *was*.

    `cis5` because it resolves up to `d`; drag it and no rule can carry
    that anywhere.  So the field goes with the note that had it, the
    gesture names the loss, and every other byte of the line — `at`,
    `len`, `voice`, `vel` — is untouched.
    """
    text = NOTES.read_text()
    at = text.splitlines().index(
        [l for l in text.splitlines() if "spell cis5" in l][0]) + 1

    out, said = notes.retune(text, at, "key", 73, 75)
    assert "key 73 → 75" in said and "`spell cis5` with it" in said
    was, now = text.splitlines(), out.splitlines()
    assert [i for i, (a, b) in enumerate(zip(was, now)) if a != b] == [at - 1]
    assert now[at - 1] == was[at - 1].replace("key 73  spell cis5", "key 75")
    #: and the file that comes back is one a person can still load
    assert notes.parse(out, "dragged.notes")


def test_a_drag_in_time_keeps_the_spelling():
    """Only the pitch invalidates a spelling.  Everything else about a
    note may move and the letter still names the same note."""
    text = NOTES.read_text()
    at = text.splitlines().index(
        [l for l in text.splitlines() if "spell cis5" in l][0]) + 1
    out, said = notes.retune(text, at, "at", 0, 96)
    assert "with it" not in said
    assert "spell cis5" in out.splitlines()[at - 1]


def test_a_written_spelling_survives_the_four_gates():
    """One line, a named field, no nesting, a stable order — the field
    is new and the gates are not, so it is held to them."""
    text = NOTES.read_text()
    parsed = notes.parse(text, "arc.notes")

    # one note per line, and the spelling is on the note's own line
    lines = [l for l in text.splitlines() if l.startswith("note ")]
    assert len(lines) == len(parsed.notes)
    assert sum(1 for l in lines if " spell " in l) == 3

    # named, never positional
    with pytest.raises(notes.NotesError, match="is not a field here"):
        notes.parse("section A  bars 1  beats 4  voices lead\n"
                    "note  section A  bar 1  at 0  len 96  voice lead"
                    "  key 60  c4  vel mf\n", "bare.notes")

    # a stable order: writing the file back is byte-identical
    assert notes.write(parsed) == text


# ── The prose survives a rewrite — fixme.md F200 ───────────────────────────


HAND = '''\
# arc.notes — three sections, bright to dark
#
#   python -m gestate.audioperform examples/audio/arcnotes.ges
section A  key D  mode lydian  bars 1  beats 4  voices melody,bass  # G# is the mode
section B  key G  mode locrian  bars 1  beats 4  voices melody,bass

#: the melody opens on the tonic and reaches the sharp fourth
note  section A  bar 1  at 0  len 96  voice melody  key 62  vel ff
note  section A  bar 1  at 96  len 96  voice melody  key 68  vel f  # the sharp fourth
note  section A  bar 1  at 0  len 384  voice bass  key 38  vel mf

note  section B  bar 1  at 0  len 96  voice melody  key 67  vel f
note  section B  bar 1  at 0  len 384  voice bass  key 43  vel mf
# and that is all of it
'''


def test_the_shipped_file_carries_prose_and_keeps_it():
    """The fixture now has the thing the property is about.

    F200 went unnoticed because `arc.notes` was generated and carried no
    comment, so the only file in the tree had nothing to lose —
    `doc/memory/a-targeted-set-is-a-claim.md` from the other side.  It
    carries seven now: a header run and a remark beside each of the
    three notes the spelling rule could not guess.
    """
    text = NOTES.read_text()
    parsed = notes.parse(text, "arc.notes")
    said = [n for n in parsed.notes if n.beside]
    assert len(said) == 3 and {n.spell for n in said} == {"fis3", "cis4", "cis5"}
    assert parsed.sections[0].above[0].startswith("# arc.notes")
    assert notes.write(parsed) == text, "and a rewrite gives all seven back"


def test_a_hand_annotated_file_comes_back_word_for_word():
    """F200: the round trip used to delete every comment.

    The premise of this format is that a person and a session edit one
    file, and `arc.ges` next door is 27% prose about *why* those notes.
    A writer that dropped it would take the explanation in the same
    gesture that was supposed to be byte-exact.
    """
    back = notes.write(notes.parse(HAND, "hand.notes"))
    for said in [l for l in HAND.splitlines() if "#" in l]:
        assert said.strip() in back, f"lost: {said}"
    assert back == HAND, "and in the same places"


def test_prose_belongs_to_the_record_below_it_and_travels_with_it():
    """The rule, and the one thing it costs.

    A comment names its owner by sitting above it or beside it, so a
    reorder carries it along — which is right for a note's own remark
    and is the stated limit for a remark about a bar.
    """
    parsed = notes.parse(HAND, "hand.notes")
    one, = [n for n in parsed.notes if n.key == 68]
    assert one.beside == "# the sharp fourth"
    two, = [n for n in parsed.notes if n.key == 62]
    assert two.above == ("#: the melody opens on the tonic "
                         "and reaches the sharp fourth",)
    assert parsed.sections[0].beside == "# G# is the mode"
    assert parsed.sections[0].above[0].startswith("# arc.notes")
    assert parsed.closing == ("# and that is all of it",)

    #: and the prose moves with the note, not with the line number
    moved = notes.Note(**{**one.__dict__, "at": 0, "key": 68, "spell": None})
    parsed.notes[parsed.notes.index(one)] = moved
    back = notes.write(parsed)
    said = [l for l in back.splitlines() if l.endswith("# the sharp fourth")]
    assert len(said) == 1 and "key 68" in said[0] and " at 0 " in said[0], (
        "the remark rode with the note it was written beside")


def test_a_drag_rewrites_the_record_and_never_the_prose():
    """A line's prose may say anything, including the words a rewrite
    looks for.  `# the key 70 next door` is a sentence, not a field."""
    text = ("section A  bars 1  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 60"
            "  spell c4  vel mf  # not the key 70 next door, nor spell des5\n")
    out, said = notes.retune(text, 2, "key", 60, 62)
    assert "`spell c4` with it" in said
    row = out.splitlines()[1]
    assert " key 62 " in row and "spell c4" not in row
    assert row.endswith("# not the key 70 next door, nor spell des5")


def test_a_comment_only_file_still_parses_to_nothing():
    """Prose with no record under it is the file's, and is not lost."""
    parsed = notes.parse("# nothing here yet\n# but a plan\n", "empty.notes")
    assert parsed.notes == [] and parsed.sections == []
    assert parsed.closing == ("# nothing here yet", "# but a plan")


@pytest.mark.parametrize("tonic", ["C#", "D#", "F#", "G#", "A#"])
def test_a_sharp_tonic_is_a_tonic_and_not_a_comment(tonic):
    """**fixme.md F203.**  `_PITCH_CLASS` offers seventeen names and five
    of them end in a sharp; `#` opening a comment anywhere made those
    five unwritable, and the refusal blamed the author for the `bars` it
    had just eaten.  A `#` opens a comment where a token could start."""
    text = (f"section A  key {tonic}  mode lydian  bars 1  beats 4"
            "  voices lead  # and a real comment after it\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 61  vel mf\n")
    parsed = notes.parse(text, "sharp.notes")
    assert parsed.sections[0].key == tonic
    assert parsed.sections[0].mode == "lydian"
    assert parsed.sections[0].beside == "# and a real comment after it"


# ── Rung 5, the first slice — the rail, the selection, `move` — 2026-09-06 ──


def _rolled_page(here):
    """The first roll of a `.ges` on disk, its regions, and a headless
    session seated over it with the bench a gesture needs: the regions,
    the origins, the path, and somewhere for the previews to go."""
    import re

    from gestate.scorebox import build_rolls, regions_of
    from gestate.session import Session

    source, origins = notes.expanded(here.read_text(), here.parent)
    asks = [(i + 1, m.group(1))
            for i, line in enumerate(source.splitlines())
            for m in [re.match(r"^notes\s+(\S.*)$", line)] if m]
    roll = build_rolls(source, asks[:1], 22050, 0)[0]

    class _Bench:
        note_regions = regions_of([roll])
        playing = False
        rate, bpm = 44100, 104

        def __init__(self):
            self.origins, self.path, self.previewing = origins, here, {}
            self.auditioned, self.calls = [], []

        def audition(self, text):
            self.auditioned.append(text)

        # The three things `_hear_at` asks of a bench, recorded — the
        # form `test_annotations.py`'s bench takes for the mark gesture.
        def beats_to_samples(self, beat):
            return int(beat * 60 * self.rate / max(1, self.bpm))

        def start(self, seconds=None, text=None):
            self.calls.append("start")
            self.playing = True

        def seek(self, sample):
            self.calls.append(("seek", sample))

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

    seat = Session(bench=_Bench())
    seat.view = _View(here.read_text())
    return roll, seat


def _press_a_note(seat, roll, note: int, box: int = 0):
    """Press note `note` at its own tick and key — what a hand aiming at
    it does: the pad's rail half first, then its pitch half — and
    answer the pitch channel."""
    from gestate.scorebox import across_of, reach_of

    low, high = reach_of(roll)
    on, _off, _k, key, _v, _m = roll.events[note]
    assert seat.touched(f"__nb_rail_{box}__", across_of(roll, on)) == ""
    said = seat.touched(f"__nb_pitch_{box}__", (high - key) / (high - low))
    assert said.startswith("line "), said
    return f"__nb_pitch_{box}__"


def test_the_roll_has_a_rail_a_selection_and_a_slide():
    """**The three things the seam round asked the roll for** — Henri,
    2026-09-06: *"Give roll a selected -channel"*, a hand for time, and
    the picture following it.  Declared in the program, so the window
    that walks it needs to learn nothing (`spec/drawnscores.md` §"The
    view — rung 5, the seam as decided")."""
    from gestate.scorebox import RAIL, build_rolls, regions_of, roll_program

    source, _o = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, l[6:]) for i, l in enumerate(source.splitlines())
            if l.startswith("notes ")]
    roll = build_rolls(source, asks[:1], 22050, 0)[0]
    text, named = roll_program(roll, 0)
    for chan in ("__nb_rail_0__", "__nb_pitch_0__", "__nb_sel_0__", "__nb_slide_0__"):
        assert f"{chan} : Chan Float" in text, chan
    assert "__nb_rail_0__" in named and "__nb_pitch_0__" in named, "the pad's two hands"
    assert "TouchY __nb_pitch_0__ (TouchX __nb_rail_0__" in text, "one pad, the rail inner"
    rail = [k for k, r in regions_of([roll]).items() if r.hand == RAIL]
    assert rail == ["__nb_rail_0__"]
    assert regions_of([roll])["__nb_rail_0__"].on_rail


def test_a_tick_is_x_inverted_and_the_grid_is_the_rolls_own():
    """One arithmetic, two readers, the law `y_of`/`key_at` keep — now
    for time.  And the grid is read off the roll's events, never finer
    than a thirty-second."""
    from gestate.scorebox import (GRID_MIN, across_of, body_of, build_rolls,
                                  grid_of, scale_of, tick_at)

    source, _o = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, l[6:]) for i, l in enumerate(source.splitlines())
            if l.startswith("notes ")]
    roll = build_rolls(source, asks[:1], 22050, 0)[0]
    _lo, _hi, span = scale_of(roll)
    for tick in (0, 96, 288, span):
        across = across_of(roll, tick)
        assert abs(tick_at(roll, across) - tick) <= span / body_of(roll)[2] + 1
    grid = grid_of(roll)
    assert grid >= GRID_MIN
    assert all((on % grid == 0) and ((off - on) % grid == 0)
               for on, off, *_ in roll.events), "the grid divides every note"


def test_a_press_selects_and_a_click_keeps_the_selection():
    """A press picks the note; letting go where it began is a click, and
    the selection outlives it — the outline and the rail marker keep
    saying which note the next command is about."""
    with _copied() as here:
        roll, seat = _rolled_page(here)
        chan = _press_a_note(seat, roll, 0)
        assert seat.selected[0] == 0
        assert seat.bench.previewing["__nb_sel_0__"] == 0.0
        seat.released(chan)
        assert seat.selected[0] == 0, "a click does not unselect"
        assert seat.bench.previewing["__nb_sel_0__"] == 0.0
        assert seat.bench.previewing["__nb_held_0__"] == -1.0


def test_the_rail_alone_holds_a_tick_and_commits_nothing():
    """The pad's rail half arrives first and names no note until the
    pitch half has spoken; released alone it writes nothing."""
    with _copied() as here:
        _roll, seat = _rolled_page(here)
        target = here.parent / "arc.notes"
        before = target.read_text()
        assert seat.touched("__nb_rail_0__", 0.5) == ""
        assert seat.holding is None and seat.holding_x[1] is None
        assert seat.touched("__nb_rail_0__", 0.6) == ""
        assert seat.released("__nb_rail_0__") == ""
        assert target.read_text() == before and seat.holding_x is None


def test_a_rail_drag_moves_the_selected_note_by_the_grid_and_writes_one_line():
    """**The slice's own number**: press a note, drag the rail one beat,
    let go — one line of the `.notes` file changes, by one field, and
    the transcript holds it as `move`."""
    from gestate.scorebox import across_of, grid_of, scale_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        note = 0
        _press_a_note(seat, roll, note)
        on = roll.events[note][0]
        grid = grid_of(roll)
        _lo, _hi, span = scale_of(roll)
        across0 = across_of(roll, on)
        across1 = across0 + grid / span
        moving = seat.touched("__nb_rail_0__", across1)
        assert f"→ {on + grid}" in moving, moving
        assert seat.bench.previewing["__nb_slide_0__"] > 0, "the picture slid"

        target = here.parent / "arc.notes"
        before = target.read_text()
        said = seat.released("__nb_rail_0__")
        assert said.startswith("move: arc.notes —"), said
        after = target.read_text()
        changed = [(a, b) for a, b in zip(before.splitlines(), after.splitlines())
                   if a != b]
        assert len(changed) == 1, f"{len(changed)} lines changed"
        a, b = changed[0]
        assert a.replace(f"at {on}", "", 1) == b.replace(f"at {on + grid}", "", 1) \
            or "bar" in said, f"more than the time moved:\n  {a}\n  {b}"
        assert "move" in seat._journal().text()
        # **The selection follows the note** (2026-09-08, Q7 of
        # `card:gui-is-difficult.md`): held by key across the rebuild the
        # commit causes, so the next drag moves the same note.
        assert seat.pending[0][1] == [(on + grid, roll.events[note][3], "melody")], seat.pending
        assert seat.bench.auditioned, "and the piece is rebuilt"


def test_a_move_onto_a_written_note_is_refused_and_writes_nothing():
    """`notes.doubled` on the gesture, as rung 4 put it: the file may
    not say one place twice, so the drag says so and moves nothing."""
    from gestate.scorebox import across_of, scale_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        # The roll is one voice (`notes A.melody`).  Two notes at one
        # tick with different keys are a chord and legal; a double is
        # the *same* key written twice, so find two notes of one pitch
        # and drag the earlier onto the later's onset.
        events = roll.events
        pair = next(((i, j) for i in range(len(events))
                     for j in range(i + 1, len(events))
                     if events[i][3] == events[j][3]
                     and events[i][0] != events[j][0]), None)
        assert pair is not None, "the roll repeats no pitch"
        first, second = pair
        on, nxt = events[first][0], events[second][0]
        _press_a_note(seat, roll, first)
        _lo, _hi, span = scale_of(roll)
        seat.touched("__nb_rail_0__", across_of(roll, nxt))
        target = here.parent / "arc.notes"
        before = target.read_text()
        said = seat.released("__nb_rail_0__")
        assert said.startswith("move:") and "already written" in said, said
        assert target.read_text() == before


def test_a_ges_written_note_cannot_be_moved_on_the_rail():
    """A note whose time is arithmetic in a `.ges` is refused by name —
    the provenance idea the card declined, not attempted here."""
    import shutil
    import tempfile
    from pathlib import Path

    from gestate.scorebox import across_of, scale_of

    with tempfile.TemporaryDirectory() as tmp:
        here = Path(tmp) / "noted.ges"
        shutil.copy(ROOT / "examples" / "audio" / "noted.ges", here)
        here.write_text(here.read_text() + "\nnotes score\n")
        roll, seat = _rolled_page(here)
        _press_a_note(seat, roll, 0)
        on = roll.events[0][0]
        _lo, _hi, span = scale_of(roll)
        seat.touched("__nb_rail_0__", across_of(roll, on) + 0.2)
        said = seat.released("__nb_rail_0__")
        assert said.startswith("move:") and ".notes" in said, said
        assert here.read_text().endswith("notes score\n"), "nothing was written"


# ── Rung 5, the second slice — the sound with the transport stopped ─────────


def test_a_move_while_stopped_plays_the_piece_from_where_the_note_went():
    """Decision 2 of rung 5 — Henri: *"lets do (a)"*: annotating is not
    performing, so a note dragged with the transport stopped is heard,
    and heard from itself — where it *went*, not where it was."""
    from gestate.midi import TICKS_PER_BEAT
    from gestate.scorebox import across_of, grid_of, scale_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        _press_a_note(seat, roll, 0)
        on, grid = roll.events[0][0], grid_of(roll)
        _lo, _hi, span = scale_of(roll)
        across0 = across_of(roll, on)
        seat.touched("__nb_rail_0__", across0 + grid / span)
        said = seat.released("__nb_rail_0__")
        assert said.startswith("move: arc.notes —") and "playing from there" in said, said
        assert "start" in seat.bench.calls, "it did not play"
        seeks = [c for c in seat.bench.calls if isinstance(c, tuple)]
        want = int((on + grid) / TICKS_PER_BEAT * 60 * 44100 / 104)
        assert seeks and seeks[0][1] == want, (seeks, want)


def test_a_transpose_of_an_included_note_while_stopped_plays_from_it():
    from gestate.midi import TICKS_PER_BEAT
    from gestate.scorebox import key_at, reach_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        chan = _press_a_note(seat, roll, 0)
        low, high = reach_of(roll)
        grabbed = key_at(roll, (high - roll.events[0][3]) / (high - low))
        # two semitones up: the fraction that reads as grabbed + 2
        up = next(d / 1000 for d in range(1000)
                  if key_at(roll, d / 1000) == grabbed + 2)
        seat.touched(chan, up)
        said = seat.released(chan)
        assert said.startswith("transpose: arc.notes —") and "playing from there" in said, said
        want = int(roll.events[0][0] / TICKS_PER_BEAT * 60 * 44100 / 104)
        seeks = [c for c in seat.bench.calls if isinstance(c, tuple)]
        assert seeks and seeks[0][1] == want, (seeks, want)


def test_a_lone_notes_file_is_lent_chopins_hammer_and_plays_every_note():
    """Henri, 2026-09-06: *"the .notes could get a default voice,
    something that sounds piano-like"*, and (a): the wrapper carries
    `chopin.ges`'s hammer verbatim rather than the library gaining a
    word.  Verbatim is checked, not claimed."""
    from pathlib import Path

    chopin = (ROOT / "examples" / "audio" / "chopin.ges").read_text()
    for line in ("env = Adsr 0.004 1.4 0.25 0.4",
                 "timbre hz = sine hz + 0.4 * sine (hz * 2.0) + 0.15 * sine (hz * 3.0)"):
        assert line in chopin and line in notes.HAMMER, line

    text = notes.wrapper(NOTES)
    source, _origins = notes.expanded(text, NOTES.parent)
    bpm, raw = perform_voices(source, "", 48000, 0)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    assert bpm == notes.WRAPPER_BPM
    assert len(raw) == len(parsed.notes), "every written note plays"
    voices = {v for s in parsed.sections for v in s.voices}
    assert {b for _on, _off, b, _p in raw} == voices, "each voice its own bank"
    assert text.count("\nnotes (") == len(parsed.sections), "a roll per section"


def test_the_wrapper_rests_a_voice_a_section_lacks():
    """Two sections, one voice missing from the second: the wrapper
    rests it for the section's length, so the voices stay the same
    bars — W5 and W8, the alignment this format exists for."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        here = Path(tmp) / "two.notes"
        here.write_text(
            "section A  key C  mode ionian  bars 1  beats 4  voices lead,low\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 72  vel mf\n"
            "note  section A  bar 1  at 0  len 384  voice low  key 48  vel mf\n"
            "section B  key C  mode ionian  bars 2  beats 4  voices lead\n"
            "note  section B  bar 2  at 0  len 96  voice lead  key 74  vel mf\n")
        text = notes.wrapper(here)
        assert "(long 8 r)" in text, "the low voice rests through section B's eight beats"
        source, _o = notes.expanded(text, here.parent)
        _bpm, raw = perform_voices(source, "", 48000, 0)
        assert len(raw) == 3
        lead = sorted(on for on, _off, b, _p in raw if b == "lead")
        assert lead == [0, 4 * 96 + 4 * 96], "B's note lands after A's one bar and B's first"


# ── Rung 5, the third slice — a file kind is a registration ─────────────────


def _opened_alone():
    """`arc.notes` opened as the document, in a scratch directory, on a
    headless bench: the kind, the program, the page."""
    import shutil
    import tempfile
    from pathlib import Path

    from gestate.audioeditor import Workbench

    tmp = Path(tempfile.mkdtemp())
    here = tmp / "arc.notes"
    shutil.copy(NOTES, here)
    bench = Workbench(here, rate=22050, block=256)
    return here, bench


def test_a_notes_file_opens_as_a_program_through_the_wrapper():
    """Henri's reading of *plugin-like*, 1: a file kind is a registration.
    `.notes` is the first row, and what it registers is how the file
    builds — the wrapper, expanded over the window's own text."""
    from gestate.audioeditor import KINDS, NotesKind

    assert KINDS[".notes"] is NotesKind
    here, bench = _opened_alone()
    assert bench.kind is NotesKind and not bench.inert
    program = bench.program()
    assert "hammerVoice" in program and 'include' not in program.split("\n")[0]
    assert bench.origins and {n for n, _l in bench.origins.values()} == {"arc.notes"}
    # The buffer, not the disk: a note retuned in the text plays retuned.
    edited = here.read_text().replace("key 62", "key 63", 1)
    was = bench.program().count("fromNote 63 ")
    assert bench.program(edited).count("fromNote 63 ") == was + 1


def test_the_page_is_the_files_own_picture_stacked():
    """`Ctrl-Tab` on a `.notes` shows every section's roll in one
    column — the file's `substrate`, which it never declared."""
    from gestate.scorebox import RAIL

    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    parsed = notes.parse(here.read_text(), "arc.notes")
    assert sorted(bench.canvases) == [f"__notes_{k}__" for k in range(len(parsed.sections))]
    assert bench.substrate is not None, "the page is the file's own picture"
    picture = bench.substrate.picture()
    titles = [f"{s.name} {s.key} {s.mode}".upper() for s in parsed.sections]
    captions = [i for i in picture if i[0] == "text" and i[3] in titles]
    assert len(captions) == len(parsed.sections), "one roll per section, stacked, each captioned with its section"
    tops = sorted(i[2] for i in captions)
    assert len(set(tops)) == len(tops), "stacked, not overlaid"
    rails = [k for k, r in bench.note_regions.items() if r.hand == RAIL]
    assert len(rails) == len(parsed.sections)


def _clear_note(roll) -> int:
    """A note a hand can name without ambiguity — the stacked page puts
    five voices in one column, and a key sounding twice under a column
    is refused by name, as `note_of` says."""
    from gestate.scorebox import RefusedError, note_of

    for i, (on, _off, _k, key, _v, _m) in enumerate(roll.events):
        try:
            if note_of(roll, on, key) == i:
                return i
        except RefusedError:
            pass
    raise AssertionError("every note of the roll is ambiguous at its own place")


def _seated_on(bench, text: str):
    from gestate.session import Session

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

    bench.previewing = {}
    bench.auditioned = []
    bench.audition = lambda text: bench.auditioned.append(text)
    seat = Session(bench=bench)
    seat.view = _View(text)
    return seat


def test_a_drag_on_the_notes_document_writes_the_buffer_not_the_disk():
    """Rung 4 wrote an included file to disk at once, because there was
    no buffer for it.  When the `.notes` *is* the document there is, so
    the drag is a text edit like a `.ges`'s — undoable, waiting for
    `Ctrl-S` — and the disk is untouched until then."""
    from gestate.scorebox import key_at, reach_of

    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    before = here.read_text()
    seat = _seated_on(bench, before)
    roll = bench.note_regions["__nb_rail_0__"].roll
    note = _clear_note(roll)
    chan = _press_a_note(seat, roll, note)
    low, high = reach_of(roll)
    grabbed = key_at(roll, (high - roll.events[note][3]) / (high - low))
    up = next(d / 1000 for d in range(1000) if key_at(roll, d / 1000) == grabbed + 2)
    seat.touched(chan, up)
    said = seat.released(chan)
    assert said.startswith("transpose: arc.notes —"), said
    assert here.read_text() == before, "the disk moved under a buffer edit"
    changed = [(a, b) for a, b in zip(before.splitlines(), seat.view.text().splitlines())
               if a != b]
    assert len(changed) == 1 and f"key {roll.events[note][3] + 2}" in changed[0][1], changed
    assert bench.auditioned and bench.auditioned[-1] == seat.view.text(), \
        "the audition is of the buffer"


def test_a_click_on_the_notes_document_goes_to_its_own_line():
    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    seat = _seated_on(bench, here.read_text())
    roll = bench.note_regions["__nb_rail_0__"].roll
    note = _clear_note(roll)
    chan = _press_a_note(seat, roll, note)
    line = roll.leaves[roll.events[note][2]].line
    row = bench.origins[line][1]
    assert seat.view.went == row, "the press goes to the note's own line"
    seat.view.went = None
    said = seat.released(chan)
    assert seat.view.went == row, (seat.view.went, row)
    assert said.endswith(f"line {row}"), said


def test_the_notes_program_is_idempotent_like_a_ges_expansion():
    """**Found by a driven window, not by these tests** (2026-09-06):
    the bench hands `program` a program it already produced, which for a
    `.ges` is harmless and for a `.notes` parsed the wrapper as the note
    file — *`env` is not a record*, at line 7 of `arc.notes`, in the
    status bar of the real window.  A second expansion is the first."""
    here, bench = _opened_alone()
    once = bench.program()
    origins = dict(bench.origins)
    twice = bench.program(once)
    assert twice == once
    assert bench.origins == origins, "and the origins survive the second call"


def test_the_canvas_opens_on_a_notes_file_before_its_page_has_built():
    """**Found by a driven window** (2026-09-06): `Ctrl-Tab` pressed
    while the page was still building answered *this file draws
    nothing*, because the guard asked the program's text for a
    `substrate` and the wrapper declares none — the page does.  A
    registered kind whose page is the file's picture draws by
    registration, and the view opens and fills in when it arrives."""
    here, bench = _opened_alone()
    assert bench.substrate is None, "the page has not been built yet"
    seat = _seated_on(bench, here.read_text())
    seat.view.show = lambda what: True
    said = seat.do_canvas()
    assert "draws nothing" not in said, said
    assert said.startswith("opening the canvas"), said



# ── card:notes-editor.md, slice 1 — the roll drawn from the file ────────────


def _both_roads():
    from gestate.scorebox import asks, build_rolls, notes_rolls

    text = notes.wrapper(NOTES)
    source, origins = notes.expanded(text, NOTES.parent)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    page = asks(source)
    fast = notes_rolls(source, page, origins, parsed)
    slow = build_rolls(source, page, 44100, 0)
    return page, parsed, fast, slow


def test_the_data_road_draws_what_the_compiled_road_draws():
    """**Held to the compiled road, event for event** — onset, offset,
    which leaf, which key — and leaf for leaf: the line in the expanded
    program and the literals it writes, so every gesture reads either
    road the same.  Velocity and manner are compared against the *file*
    in the test below, because the compiled road gets them wrong for a
    note-file note (`fixme.md` F206)."""
    page, _parsed, fast, slow = _both_roads()
    assert len(fast) == len(slow) == len(page)
    for a, b in zip(fast, slow):
        assert [e[:4] for e in a.events] == [e[:4] for e in b.events]
        assert [(l.line, l.bank, l.chancy, l.atoms) for l in a.leaves] == \
            [(l.line, l.bank, l.chancy, l.atoms) for l in b.leaves]
        assert (a.cut, a.chancy) == (b.cut, b.chancy) == (False, False)


def test_the_data_road_says_what_the_file_says_about_loudness_and_manner():
    from gestate.notes import LEVELS

    _page, parsed, fast, _slow = _both_roads()
    by_line = {n.line: n for n in parsed.notes}
    text = notes.wrapper(NOTES)
    _source, origins = notes.expanded(text, NOTES.parent)
    accents = 0
    for roll in fast:
        for on, off, k, key, vel, manner in roll.events:
            note = by_line[origins[roll.leaves[k].line][1]]
            assert manner == note.manners
            assert vel == int((0.125 + note.level * 0.125) * 127.0)
            accents += manner != 0
    assert accents > 0, "arc.notes writes accents, and they must reach the roll"


def test_the_data_road_is_milliseconds_and_the_bench_takes_it():
    """The number this slice exists for: 5.0 s for one section through
    the compiler on 2026-09-06, against a lookup."""
    import time

    from gestate.scorebox import asks, notes_rolls

    text = notes.wrapper(NOTES)
    source, origins = notes.expanded(text, NOTES.parent)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    t0 = time.perf_counter()
    rolls = notes_rolls(source, asks(source), origins, parsed)
    took = time.perf_counter() - t0
    assert len(rolls) == 3 and took < 0.5, f"{took:.2f} s for the page"

    here, bench = _opened_alone()
    program = bench.program()
    assert bench.notes_parsed is not None
    fast = bench.kind.rolls(bench, program, asks(program))
    assert [e[:4] for e in fast[0].events] == [e[:4] for e in rolls[0].events]


def test_an_ask_the_data_road_cannot_read_is_a_roll_error_in_its_slot():
    from gestate.scorebox import RollError, notes_rolls

    text = notes.wrapper(NOTES)
    source, origins = notes.expanded(text, NOTES.parent)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    out = notes_rolls(source, [(1, "notes_A_melody ++ notes_B_melody"),
                               (2, "notes_Q_nothing"),
                               (3, "(notes_A_bass)")], origins, parsed)
    assert isinstance(out[0], RollError) and "names something else" in str(out[0])
    assert isinstance(out[1], RollError) and "no voice of this file" in str(out[1])
    assert not isinstance(out[2], RollError) and len(out[2].events) > 0


# ── card:notes-editor.md, slice 2 — the score as records, the engine once ──


def test_the_engine_half_has_the_full_programs_banks_and_no_notes():
    """`notes.wrapper(notes=False)`: the same voices and channels as the
    full wrapper, no `include`, a score that rests on every bank — so
    `Voice` is declared as the full program declares it (F207) — and it
    compiles to a graph."""
    from gestate.audioperform import graph_of
    from gestate.audiovoices import banks_of, channels_of

    full = notes.wrapper(NOTES)
    engine = notes.wrapper(NOTES, notes=False)
    assert "include" not in engine and "notes (" not in engine
    assert len(engine.splitlines()) < 60
    source, _o = notes.expanded(full, NOTES.parent)
    assert [b.name for b in banks_of(engine)] == [b.name for b in banks_of(source)]
    for a, b in zip(banks_of(engine), banks_of(source)):
        assert channels_of(engine, a) == channels_of(source, b)
    graph_of(engine, rate=44100)


def test_the_records_are_the_events_the_compiled_road_performs():
    """Held to `perform_voices` on `arc.notes`: the same `(onset, offset,
    bank, payload)` set — and then the same `Schedule`, channel for
    channel, sample for sample.  Q1's default: the events."""
    from gestate.audioalloc import Allocator
    from gestate.audioeditor import NotesKind
    from gestate.audioscore import perform_voices, schedule_voices
    from gestate.audiovoices import banks_of, channels_of

    here, bench = _opened_alone()
    program = bench.program()
    engine = NotesKind.engine_program(bench, bench.source())
    data = NotesKind.events(bench)
    bpm, played = perform_voices(program, "", 44100, 0)
    assert sorted(data) == sorted(played)
    assert bpm == notes.WRAPPER_BPM

    def allocs(src):
        return {b.name: Allocator(channels_of(src, b)) for b in banks_of(src)}

    fast = schedule_voices(data, bpm, 44100, allocs(engine), block=256)
    slow = schedule_voices(played, bpm, 44100, allocs(program), block=256)
    assert fast.changes == slow.changes


def test_the_score_loads_off_the_records_without_a_front_end():
    """The number: 4.5 s cold through `perform_voices` on 2026-09-06,
    against the records."""
    import time

    here, bench = _opened_alone()
    program = bench.program()
    bench._engine = bench.kind.engine_program(bench, bench.source())
    t0 = time.perf_counter()
    bench._load_score(program)
    took = time.perf_counter() - t0
    assert bench.schedule is not None and bench.performer is None
    assert took < 1.0, f"{took:.2f} s"
    assert bench.bpm == notes.WRAPPER_BPM


def test_a_note_edit_leaves_the_engine_text_byte_identical():
    """What lets the bench keep the engine: the kind's engine half does
    not read the notes, so a moved note changes nothing in it."""
    from gestate.audioeditor import NotesKind

    here, bench = _opened_alone()
    before = NotesKind.engine_program(bench, bench.source())
    bench.notes_parsed = None
    moved = bench.source().replace("key 62", "key 63", 1)
    after = NotesKind.engine_program(bench, moved)
    assert after == before
    assert bench.program(moved) != bench.program(bench.source()), "the program did move"


# ── card:notes-editor.md, slice 3 — the roll compiled once, the notes as a reading ──


def _live_and_baked():
    from gestate.scorebox import asks, notes_rolls, page_program

    text = notes.wrapper(NOTES)
    source, origins = notes.expanded(text, NOTES.parent)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    rolls = notes_rolls(source, asks(source), origins, parsed)
    return rolls, page_program(rolls, stacked=True), page_program(rolls, stacked=True, live=True)


def test_a_live_rolls_text_holds_still_while_a_note_moves():
    """The number this slice exists for: a picture whose text names no
    note is compiled once, and a moved note recompiles nothing."""
    from gestate.scorebox import asks, notes_rolls, page_program

    rolls, (baked, _r, _e), (live, _r2, _e2) = _live_and_baked()
    assert "__nb_rc_0__ : Chan (List Float)" in live
    text = notes.wrapper(NOTES)
    moved_file = NOTES.read_text().replace("key 62", "key 64", 1)
    source, origins = notes.expanded(text, NOTES.parent, texts={"arc.notes": moved_file})
    parsed = notes.parse(moved_file, "arc.notes")
    rolls2 = notes_rolls(source, asks(source), origins, parsed)
    assert page_program(rolls2, stacked=True, live=True)[0] == live
    assert page_program(rolls2, stacked=True)[0] != baked, "the baked text moves; that was the cost"


def test_a_live_roll_draws_the_picture_the_baked_one_draws():
    from gestate.gui import Substrate
    from gestate.scorebox import geometry_of, rows_channel, rows_reading

    rolls, (baked, _r, entries), (live, _r2, _e2) = _live_and_baked()
    vb = Substrate.several(baked, 44100, entries)
    vl = Substrate.several(live, 44100, entries)
    for k, (roll, view) in enumerate(zip(rolls, vl)):
        view.write(rows_channel(k), rows_reading(roll))
    for view in vl:
        view.tick()
    for k in range(len(entries)):
        rects = lambda v: [i for i in v.picture() if i[0] == "rect"]
        assert rects(vl[k]) == rects(vb[k]), f"box {k} differs"
        assert any(i[4] == geometry_of(rolls[k]).note_h for i in rects(vl[k])), "and there are notes in it"


def test_the_data_roads_scale_is_the_sections_length_and_the_files_range():
    """**Found by a photograph, not by the parity test**: the span had
    counted the section once per voice, so every note sat in the left
    fifth of the roll — and the baked and live roads, sharing the
    scale, agreed with each other about the wrong picture."""
    from gestate.midi import TICKS_PER_BEAT
    from gestate.scorebox import body_of, scale_of, x_of

    rolls, _b, _l = _live_and_baked()
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    keys = [n.key for n in parsed.notes]
    for roll, section in zip(rolls, parsed.sections):
        lo, hi, span = scale_of(roll)
        assert span == section.bars * section.beats * TICKS_PER_BEAT
        assert (lo, hi) == (min(keys), max(keys)), "one axis for the page"
        last = max(off for _on, off, *_r in roll.events)
        left, _top, width, _h = body_of(roll)
        assert x_of(roll, last) > left + width // 4, "the notes reach across the roll"


def test_the_body_is_one_pad_and_every_note_is_found_at_its_own_place():
    """Henri, 2026-09-06, evening: *"yksi käsi koko rungon yli"* — a
    `TouchY` around a `TouchX` over the whole body, three hands a box
    with the ruler where there were a hundred and thirty, and every
    note found by its tick and key."""
    from gestate.scorebox import PITCH, RAIL, RULER, note_under, regions_of

    rolls, _b, _l = _live_and_baked()
    roll = rolls[0]
    regions = regions_of(rolls)
    assert sorted(r.hand for k, r in regions.items() if r.box == 0) == sorted([PITCH, RAIL, RULER])
    for i, (on, off, _k, key, _v, _m) in enumerate(roll.events):
        assert note_under(roll, on, key) == i or roll.events[note_under(roll, on, key)][3] == key


def test_the_page_after_a_moved_note_is_a_lookup_not_a_compile():
    """1.96 s cold, and then under a second — the compiled text did not
    move, so only the rows are written."""
    import time

    from gestate.scorebox import geometry_of

    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    assert len(bench.note_rows) == 3
    moved = bench.program(here.read_text().replace("key 62", "key 63", 1))
    t0 = time.perf_counter()
    bench._load_substrate(moved)
    took = time.perf_counter() - t0
    assert took < 1.5, f"{took:.2f} s"
    roll = bench.note_regions["__nb_rail_0__"].roll
    bars = [i for i in bench.canvases["__notes_0__"].picture()
            if i[0] == "rect" and i[4] == geometry_of(roll).note_h]
    assert len(bars) == len(roll.events)


# ── The editing scale — `card:notes-editor.md`, 2026-09-06 ──────────────────
#
# Rung 5 opened a `.notes` as a roll; what it opened was the score box's
# glance — 384 by 116, a note three pixels tall, no keys, no bars.  The
# league the card names needs a page a hand can work: a semitone a row,
# a beat a stride, the keys named down the side and the bars numbered
# along the top.  One arithmetic still, at two scales.


def test_a_notes_page_is_drawn_at_editing_scale_and_the_box_is_not():
    """A `.notes` roll is `editing`: a semitone is `SEMI_H` pixels and a
    beat `BEAT_W`, read off the same `y_of`/`x_of` every gesture reads.
    A `.ges` box beside a line is `COMPACT`, to the pixel it was."""
    from gestate.midi import TICKS_PER_BEAT
    from gestate.scorebox import (BEAT_W, BODY_H, COMPACT, ROLL_H, SEMI_H,
                                  build_rolls, geometry_of, scale_of, x_of,
                                  y_of)

    rolls, _b, _l = _live_and_baked()
    for roll in rolls:
        geo = geometry_of(roll)
        assert geo is not COMPACT and geo.note_h == SEMI_H - 2
        lo, hi, _span = scale_of(roll)
        for key in range(lo, hi):
            assert y_of(roll, key) - y_of(roll, key + 1) == SEMI_H, key
        assert x_of(roll, TICKS_PER_BEAT) - x_of(roll, 0) == BEAT_W

    source, _o = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, l[6:]) for i, l in enumerate(source.splitlines())
            if l.startswith("notes ")]
    box = build_rolls(source, asks[:1], 22050, 0)[0]
    assert geometry_of(box) is COMPACT
    lo, hi, _span = scale_of(box)
    for key in range(lo, hi + 1):
        assert y_of(box, key) == ROLL_H // 2 - 14 - int((key - lo) * BODY_H / max(1, hi - lo)), \
            "the compact box's line, as it was written before the editing scale"


def test_the_page_names_its_keys_its_bars_and_its_sections():
    """What the eye needs to read a note without leaving it: a key per
    semitone down the side with the octaves named, a number per bar
    along the ruler, a line per beat, and the section's own name and
    mode as the caption — the four things Reaper's editor has and the
    glance did not (`card:notes-editor.md`)."""
    from gestate.gui import Substrate
    from gestate.scorebox import body_of, geometry_of, scale_of

    rolls, (baked, _r, entries), _l = _live_and_baked()
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    views = Substrate.several(baked, 44100, entries)
    for roll, section, view in zip(rolls, parsed.sections, views):
        geo = geometry_of(roll)
        lo, hi, _span = scale_of(roll)
        items = view.picture()
        keys = [i for i in items if i[0] == "rect" and i[3] == geo.keys - 4]
        assert len(keys) == hi - lo + 1, "a key per semitone of the range"
        names = sorted(i[3] for i in items if i[0] == "text" and i[3].startswith("C") and i[3][1:].lstrip("-").isdigit())
        assert names == sorted(f"C{k // 12 - 1}" for k in range(lo, hi + 1) if k % 12 == 0)
        numbers = sorted(int(i[3]) for i in items if i[0] == "text" and i[3].isdigit())
        assert numbers == list(range(1, section.bars + 1)), "a number per bar"
        _left, _top, _w, body_h = body_of(roll)
        lines = [i for i in items if i[0] == "rect" and i[3] == 1 and i[4] == body_h]
        assert len(lines) == section.bars * section.beats + section.bars, "a line per beat, and a brighter one per bar"
        caption = [i for i in items if i[0] == "text" and i[3] == f"{section.name} {section.key} {section.mode}".upper()]
        assert len(caption) == 1, "captioned with what it is"


def test_a_hand_takes_a_note_by_its_row_and_the_body_around_it():
    """The reference walk over the editing-scale page: a press on a
    note's own rectangle lands on a column and names that note — and
    on the body around the column, which is the hand for time (F204's
    repair).  The hands folded balanced (`_overs`) record in the same
    order the chain did."""
    from gestate.gui import Substrate
    from gestate.scorebox import (geometry_of, key_at, note_under,
                                  regions_of, tick_at)

    rolls, (baked, _r, entries), _l = _live_and_baked()
    regions = regions_of(rolls)
    view = Substrate.several(baked, 44100, entries)[0]
    roll = rolls[0]
    geo = geometry_of(roll)
    heads = [i for i in view.picture() if i[0] == "rect" and i[4] == geo.note_h]
    assert len(heads) == len(roll.events)
    hit, named = 0, 0
    for _kind, x, y, w, h, _c in heads:
        meant = view.touch_all("press", x + w // 2, y + h // 2)
        view.touch_all("release", x + w // 2, y + h // 2)
        if not meant:
            continue
        hit += 1
        rail, pitch = meant
        assert regions[rail[1]].on_rail, "the rail first"
        assert regions[pitch[1]].on_pitch, "then the pitch hand around it"
        try:
            note_under(roll, tick_at(roll, rail[2]), key_at(roll, pitch[2]))
            named += 1
        except Exception:                                # noqa: BLE001
            pass
    assert hit == len(heads), f"{hit} of {len(heads)} notes could be pressed"
    assert named == hit


def test_two_sections_on_one_roll_follow_one_another():
    """An ask naming voices of two sections draws the second after the
    first — the bar lines and the notes agree on where a section
    starts, which they did not before the editing scale: every section
    began at tick 0 and only the span was summed."""
    from gestate.midi import TICKS_PER_BEAT
    from gestate.scorebox import notes_rolls, scale_of

    text = notes.wrapper(NOTES)
    source, origins = notes.expanded(text, NOTES.parent)
    parsed = notes.parse(NOTES.read_text(), "arc.notes")
    a, b = parsed.sections[0], parsed.sections[1]
    ask = f"(notes_{a.name}_{a.voices[0]} || notes_{b.name}_{b.voices[0]})"
    line = next(i + 1 for i, l in enumerate(source.splitlines()) if l.startswith("notes "))
    roll = notes_rolls(source, [(line, ask)], origins, parsed)[0]
    first = a.bars * a.beats * TICKS_PER_BEAT
    _lo, _hi, span = scale_of(roll)
    assert span == first + b.bars * b.beats * TICKS_PER_BEAT
    assert roll.bars[a.bars] == first, "the second section's first bar line"
    assert any(on >= first for on, *_r in roll.events), "the second section's notes follow the first's"
    assert roll.title == f"{a.name} {a.key} {a.mode}  {b.name} {b.key} {b.mode}"


# ── F204 repaired — a pad is two on one element, and a note is carried in both axes ──


def test_a_pad_is_two_attachments_on_one_element_and_a_press_writes_both():
    """`spec/substrate.md` §"S3": *a pad is two on one element*.  Measured
    false on 2026-09-06 (F204): a press wrote the inner one only, in
    both machines.  Now a press grabs the deepest attachment and every
    one around it, so `onTouchX cx (onTouchY cy rect)` writes `cy` and
    `cx` from one press — and two faders side by side still write one."""
    from gestate.gui import Substrate

    pad = ("cx : Chan Float\ncx = chan\ncy : Chan Float\ncy = chan\n"
           "substrate : Sig Sub\n"
           "substrate = !(TouchX cx (TouchY cy (Rect 40 40 (RGB 9 9 9))))\n")
    v = Substrate(pad, 22050)
    said = v.touch_all("press", 5, 5)
    assert [s[1] for s in said] == ["cy", "cx"], said
    assert abs(said[0][2] - 0.625) < 1e-9 and abs(said[1][2] - 0.625) < 1e-9
    said = v.touch_all("drag", 10, 12)
    assert dict((s[1], round(s[2], 3)) for s in said) == {"cy": 0.8, "cx": 0.75}
    assert v.touch_all("release", 10, 12) == [("released", "cy"), ("released", "cx")]
    assert v.touch("press", 5, 5) == ("touched", "cy", 0.625), "touch answers the innermost, as before"

    two = ("a : Chan Float\na = chan\nb : Chan Float\nb = chan\n"
           "substrate : Sig Sub\n"
           "substrate = !(Row (TouchY a (Rect 40 40 (RGB 9 9 9))) "
           "(TouchY b (Rect 40 40 (RGB 9 9 9))))\n")
    v = Substrate(two, 22050)
    assert [s[1] for s in v.touch_all("press", -10, 0)] == ["a"]


def _diagonal(seat, roll, note: int):
    """Press `note`, carry it up two semitones and along one grid step,
    and let go — the way one hand does it since F204's repair, the
    column's channel and the body's written by the same press and
    released one after the other."""
    from gestate.scorebox import across_of, grid_of

    chan = _press_a_note(seat, roll, note)
    on = roll.events[note][0]
    seat.touched("__nb_rail_0__", across_of(roll, on))
    _n, _note, was, grabbed, _k = seat.holding
    from gestate.scorebox import reach_of
    low, high = reach_of(roll)
    up = (high - (grabbed + 2)) / (high - low)
    seat.touched(chan, up)
    seat.touched("__nb_rail_0__", across_of(roll, on + grid_of(roll)))
    first = seat.released(chan)
    second = seat.released("__nb_rail_0__")
    return first, second


def test_one_drag_carries_a_note_in_pitch_and_in_time():
    """The postcondition F204 stood in front of: a note moves in both
    axes under one hand.  The first `released` commits both — **as one
    `carry`** since 2026-09-08 (F211: after a `move` the file is in its
    own order, so a second command's address named a line that had
    moved) — and the second finds nothing held."""
    from gestate.scorebox import grid_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        note = 0
        on, key = roll.events[note][0], roll.events[note][3]
        assert seat.bench.previewing == {}
        first, second = _diagonal(seat, roll, note)
        assert first.startswith("carry: arc.notes — 1 note, +2 semitones, +") and "ticks" in first, first
        assert second == "", second
        target = here.parent / "arc.notes"
        moved = [l for l in target.read_text().splitlines()
                 if f"key {key + 2}" in l and f"at {on + grid_of(roll)}" in l]
        assert moved, "the line carries both the new key and the new tick"
        assert seat.holding is None and seat.holding_x is None


def test_a_drag_previews_both_axes_at_once():
    """The picture follows the hand in pitch *and* time before anything
    is written: neither preview wipes the other's reading."""
    from gestate.scorebox import across_of, grid_of, reach_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        chan = _press_a_note(seat, roll, 0)
        on = roll.events[0][0]
        seat.touched("__nb_rail_0__", across_of(roll, on))
        _n, _note, _was, grabbed, _k = seat.holding
        low, high = reach_of(roll)
        seat.touched(chan, (high - (grabbed + 3)) / (high - low))
        seat.touched("__nb_rail_0__", across_of(roll, on + grid_of(roll)))
        shown = seat.bench.previewing
        assert shown["__nb_lift_0__"] < 0, "carried up"
        assert shown["__nb_slide_0__"] > 0, "and along"
        seat.released(chan)
        seat.released("__nb_rail_0__")


def test_a_press_on_nothing_selects_nothing_and_the_body_carries_nothing():
    """A press on an empty column, with a note selected earlier, must
    not let the body drag that old selection off in time."""
    from gestate.scorebox import across_of, reach_of

    with _copied() as here:
        roll, seat = _rolled_page(here)
        chan = _press_a_note(seat, roll, 0)
        seat.released(chan)
        assert 0 in seat.selected.values()
        low, high = reach_of(roll)
        assert seat.touched("__nb_rail_0__", across_of(roll, 0)) == ""
        said = seat.touched("__nb_pitch_0__", (high - min(high, 110)) / (high - low))
        assert said.startswith("sweep a band"), said
        assert 0 not in seat.selected, "a press on nothing selects nothing"
        seat.released("__nb_rail_0__")
        seat.released("__nb_pitch_0__")
        assert here.parent.joinpath("arc.notes").read_text() == (ROOT / "examples/audio/arc.notes").read_text()


def test_the_window_view_answers_its_own_replacement_until_the_window_takes_it():
    """Found on the real window and on no headless bench: `ged_set_text`
    is picked up on the window's next frame and `ged_text` reads what
    the window last published, so two commands writing back to back —
    `transpose` then `move`, one hand's drag — had the second read the
    text from before the first, and the last write won.  The view
    answers the replacement until the document has taken it."""
    from gestate.workbench import Window

    class _Deferred:
        """An editor whose `text` setter lands on the next frame."""

        def __init__(self, text):
            self._text, self._pending, self.orders = text, None, []

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, value):
            self._pending = value

        def frame(self):
            if self._pending is not None:
                self._text, self._pending = self._pending, None

        def changed(self):
            return False

    ed = _Deferred("a 1\nb 2\n")
    view = Window(ed)
    assert view.replace("a 9\nb 2\n")
    assert view.text() == "a 9\nb 2\n", "the replacement, before the window's frame"
    assert view.replace(view.text().replace("b 2", "b 8"))
    ed.frame()
    assert ed.text == "a 9\nb 8\n", "both writes landed, the second on top of the first"
    assert view.text() == "a 9\nb 8\n"
    ed._text = "typed\n"
    assert view.text() == "typed\n", "the document is the answer once it says something else"


# ── Slice 4 of card:notes-editor.md — select multiple, and move them around ──
#
# A hand sweeping over empty roll selects the notes its band covers
# (`select`), and a hand on any note of the group carries them all by
# one interval and one number of ticks (`carry`): one rewrite, one
# undo entry, one rebuild.  Every gesture a command, as before.


def _rebuilt(seat):
    """The rebuild a commit causes in the window, done by hand here: the
    bench's pictures from the buffer, which fires `Session._settle`."""
    seat.bench._load_substrate(seat.bench.program(seat.view.text()))
    return seat.bench.note_regions["__nb_rail_0__"].roll



def _page_seat():
    """The `.notes` page opened alone, its first roll's reference view,
    and a seat over the bench — the way the window does it, one press
    writing the column and the body around it."""
    here, bench = _opened_alone()
    bench._load_substrate(bench.program())
    seat = _seated_on(bench, here.read_text())
    view = bench.canvases["__notes_0__"]
    roll = bench.note_regions["__nb_rail_0__"].roll
    return here, seat, view, roll


def _feed(seat, view, kind, x, y):
    out = []
    for meant in view.touch_all(kind, x, y):
        out.append(seat.touched(meant[1], meant[2]) if meant[0] == "touched"
                   else seat.released(meant[1]))
    return out


def _sweep(seat, view, roll, t0, k0, t1, k1):
    """Press on empty roll at `(t0, k0)`, sweep to `(t1, k1)`, let go."""
    from gestate.scorebox import x_of, y_of

    x0, y0 = x_of(roll, t0) + 2, y_of(roll, k0)
    x1, y1 = x_of(roll, t1) - 2, y_of(roll, k1)
    said = _feed(seat, view, "press", x0, y0)
    assert said[-1].startswith("sweep a band"), said
    _feed(seat, view, "drag", (x0 + x1) // 2, (y0 + y1) // 2)
    _feed(seat, view, "drag", x1, y1)
    band = seat.bench.previewing.get("__nb_band_0__")
    assert band and len(band) == 4 and band[2] > 0 and band[3] > 0, "the band is drawn while it is swept"
    return _feed(seat, view, "release", x1, y1)


def test_a_press_beyond_reach_of_any_note_is_empty_roll():
    """`BAND_REACH`: a column is the roll's whole height, so a press four
    semitones off the only note under it means empty roll, not that
    note — and a press within three still means it."""
    from gestate.scorebox import BAND_REACH, RefusedError, note_under

    _here, _seat, _view, roll = _page_seat()
    on = roll.events[0][0]
    top = max((j for j, e in enumerate(roll.events) if e[0] <= on < e[1]),
              key=lambda j: roll.events[j][3])
    key = roll.events[top][3]
    assert note_under(roll, on, key + BAND_REACH) == top
    with pytest.raises(RefusedError, match="within reach"):
        note_under(roll, on, key + BAND_REACH + 1)
    with pytest.raises(RefusedError, match="nothing sounds at that tick"):
        note_under(roll, 10**9, key)


def test_a_band_selects_every_note_it_touches_as_one_command():
    """Sweep bar 1 of section A from key 78 down to 62: the melody's
    four notes and whatever else sounds there, `select` in the
    transcript with the corners in the roll's own ticks and keys, the
    group outlined in the picture."""
    _here, seat, view, roll = _page_seat()
    said = _sweep(seat, view, roll, 0, 78, 384, 62)
    assert said[0].startswith("select: ") and " notes — ticks " in said[0], said
    assert said[1] == "", "the second release finds no band"
    group = seat.group[0]
    assert len(group) >= 4
    for n in group:
        on, off, _k, key, _v, _m = roll.events[n]
        assert on < 384 and off > 0 and 62 <= key <= 78
    assert seat.selected[0] == group[0]
    assert seat.bench.previewing["__nb_sels_0__"] == [float(n) for n in group]
    assert seat.bench.previewing["__nb_band_0__"] == [], "the band is gone once it has selected"
    assert any(step.verb == "select" for step in seat.log.steps), "select is in the transcript"


def test_a_typed_select_picks_the_same_notes_a_sweep_did():
    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    swept = seat.group[0]
    seat.group.clear()
    said = seat.run("select", "__nb_rail_0__", 384, 62, 0, 78)
    assert said.startswith("select: ")
    assert seat.group[0] == swept, "either way round, the same notes"
    assert seat.run("select", "__nb_pitch_0__", 0, 60, 96, 70).startswith("select: name the box's rail")
    assert seat.run("select", "__nb_rail_0__", 0, 120, 10, 127).startswith("select: nothing sounds")
    assert 0 not in seat.group, "a band over nothing clears the selection"


def test_a_hand_on_any_note_of_the_group_carries_them_all_in_one_rewrite():
    """The slice's own number: N selected lines change by the same
    interval and the same ticks, through one `replace` of the buffer,
    and the transcript says `carry`."""
    from gestate.scorebox import x_of, y_of

    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    n = group[-1]
    on, off, _k, key, _v, _m = roll.events[n]
    nx, ny = (x_of(roll, on) + x_of(roll, off)) // 2, y_of(roll, key)
    said = _feed(seat, view, "press", nx, ny)
    assert said[-1].startswith("line "), said
    assert seat.group[0] == group, "a press on a note of the group keeps the group"
    _feed(seat, view, "drag", nx, ny - 8)
    _feed(seat, view, "drag", nx, ny - 16)
    assert seat.bench.previewing["__nb_sels_0__"] == [float(m) for m in group]
    assert seat.bench.previewing["__nb_lift_0__"] < 0
    before = seat.view.text()
    writes = []
    real = seat.view.replace
    seat.view.replace = lambda text: writes.append(text) or real(text)
    said = _feed(seat, view, "release", nx, ny - 16)
    assert said[0].startswith("carry: arc.notes — ") and f"{len(group)} notes" in said[0], said
    assert len(writes) == 1, "one rewrite for the whole group"
    changed = [(a, b) for a, b in zip(before.splitlines(), seat.view.text().splitlines()) if a != b]
    assert len(changed) == len(group)
    for a, b in changed:
        ka = int(a.split("key ")[1].split()[0]); kb = int(b.split("key ")[1].split()[0])
        assert kb - ka == 2, (a, b)
        assert a.split("key")[0] == b.split("key")[0], "only the key moved"
    # The group is held by key across the rebuild (2026-09-08, Q7):
    # every note, two semitones up, in its own voice.
    roll2 = _rebuilt(seat)
    assert sorted((roll2.events[n][0], roll2.events[n][3]) for n in seat.group[0]) == \
        sorted((roll.events[n][0], roll.events[n][3] + 2) for n in group)


def test_a_carry_that_would_double_a_note_refuses_whole_and_keeps_the_group():
    """Bar 1's melody carried one beat along puts its last note where
    bar 2's first already is: nothing moves, and the group stands."""
    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    before = seat.view.text()
    said = seat.run("carry", "__nb_rail_0__", 2, 96)
    assert said.startswith("carry: arc.notes: a note would land on one already written"), said
    assert seat.view.text() == before
    assert seat.group[0] == group
    assert seat.run("carry", "__nb_rail_0__", 0, 0).startswith("carry: nothing to do")
    assert seat.run("carry", "__nb_pitch_0__", 1, 0).startswith("carry: name the box's rail")
    seat.group.clear()
    assert seat.run("carry", "__nb_rail_0__", 1, 0).startswith("carry: nothing selected")


def test_a_press_on_a_note_outside_the_group_selects_that_one_alone():
    from gestate.scorebox import x_of, y_of

    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    outside = next(i for i, (on, *_r) in enumerate(roll.events) if on >= 384 * 4 and i not in group)
    on, off, _k, key, _v, _m = roll.events[outside]
    nx, ny = (x_of(roll, on) + x_of(roll, off)) // 2, y_of(roll, key)
    _feed(seat, view, "press", nx, ny)
    assert seat.group[0] == (seat.selected[0],) and seat.selected[0] not in group
    _feed(seat, view, "release", nx, ny)


def test_the_picture_outlines_the_group_and_moves_it_with_the_hand():
    from gestate.gui import Substrate
    from gestate.scorebox import geometry_of, rows_channel, rows_reading

    rolls, _b, (live, _r, entries) = _live_and_baked()
    view = Substrate.several(live, 44100, entries)[0]
    roll = rolls[0]
    view.write(rows_channel(0), rows_reading(roll))
    view.write("__nb_sels_0__", [0.0, 1.0, 2.0])
    view.write("__nb_band_0__", [-300.0, 0.0, 200.0, 100.0])
    view.tick()
    geo = geometry_of(roll)
    pic = view.picture()
    outlines = [i for i in pic if i[0] == "rect" and i[4] == geo.note_h + 2 and i[5] == (236, 240, 248)]
    assert len(outlines) == 3, "every selected note wears an outline"
    band = [i for i in pic if i[0] == "rect" and i[5] == (58, 70, 96)]
    assert band and band[0][3:5] == (200, 100), "the band is drawn where it was said"
    heads = lambda v: [(i[1], i[2]) for i in v.picture() if i[0] == "rect" and i[4] == geo.note_h][:4]
    before = heads(view)
    view.write("__nb_held_0__", 1.0)
    view.write("__nb_lift_0__", -16.0)
    view.tick()
    after = heads(view)
    assert [a[1] - b[1] for a, b in zip(after, before)] == [-16, -16, -16, 0], \
        "the three selected move with a hand on the second; the fourth stays"


# ── Slice 4, continued — resize a note by its end, and the selection with it ──


def _end_of(roll, note):
    """Where a hand takes a note's end: three pixels inside its last
    column, on its own row."""
    from gestate.scorebox import x_of, y_of

    on, off, _k, key, _v, _m = roll.events[note]
    return x_of(roll, off) - 3, y_of(roll, key)


def test_a_press_in_a_notes_last_column_takes_its_end():
    """The note's offset falls in the pressed column and the note is
    wider than a column: the press reveals the line and says *its end*,
    and pitch is not carried while the end is held."""
    _here, seat, view, roll = _page_seat()
    n = next(i for i, e in enumerate(roll.events) if e[1] - e[0] == 384)
    ex, ey = _end_of(roll, n)
    said = _feed(seat, view, "press", ex, ey)
    assert said[-1].endswith("— its end"), said
    assert seat.resizing is not None and seat.resizing[1] == n
    _feed(seat, view, "drag", ex, ey - 24)
    assert seat.bench.previewing["__nb_lift_0__"] == 0.0, "a hand on an end carries no pitch"
    before = seat.view.text()
    said = _feed(seat, view, "release", ex, ey - 24)
    assert any("line " in x for x in said), "let go where it took hold is a click"
    assert seat.view.text() == before
    assert seat.resizing is None


def test_a_press_in_the_middle_of_a_note_is_not_its_end():
    from gestate.scorebox import x_of, y_of

    _here, seat, view, roll = _page_seat()
    n = next(i for i, e in enumerate(roll.events) if e[1] - e[0] == 384)
    on, off, _k, key, _v, _m = roll.events[n]
    _feed(seat, view, "press", (x_of(roll, on) + x_of(roll, off)) // 2, y_of(roll, key))
    assert seat.resizing is None
    _feed(seat, view, "release", (x_of(roll, on) + x_of(roll, off)) // 2, y_of(roll, key))


def test_a_drag_on_the_end_rewrites_one_notes_length_by_the_grid():
    """The slice's own number: a whole-bar note's end carried back one
    beat changes its `len` field — 384 to 288 — on one line, and the
    transcript says `resize`."""
    _here, seat, view, roll = _page_seat()
    n = next(i for i, e in enumerate(roll.events) if e[1] - e[0] == 384)
    ex, ey = _end_of(roll, n)
    _feed(seat, view, "press", ex, ey)
    _feed(seat, view, "drag", ex - 16, ey)
    said = _feed(seat, view, "drag", ex - 32, ey)
    assert "len 384 → 288" in said[0], said
    assert seat.bench.previewing["__nb_grow_0__"] == -32.0, "the picture shows it shorter first"
    before = seat.view.text()
    said = _feed(seat, view, "release", ex - 32, ey)
    assert said[0].startswith("resize: arc.notes — len 384 → 288 on line "), said
    changed = [(a, b) for a, b in zip(before.splitlines(), seat.view.text().splitlines()) if a != b]
    assert len(changed) == 1
    assert changed[0][0].replace("len 384", "len 288") == changed[0][1], "only the length moved"
    assert any(step.verb == "resize" for step in seat.log.steps)


def test_a_typed_resize_names_the_note_as_transpose_does():
    _here, seat, view, roll = _page_seat()
    n = next(i for i, e in enumerate(roll.events) if e[1] - e[0] == 384)
    on, key = roll.events[n][0], roll.events[n][3]
    before = seat.view.text()
    assert seat.run("resize", "__nb_pitch_0__", "-", on, key, 0).startswith("resize: a note is at least one tick")
    assert seat.run("resize", "__nb_pitch_0__", "-", on, key + 1, 96).startswith("resize: nothing sounds")
    assert seat.run("resize", "__nb_pitch_0__", "-", on, key, 384).startswith("resize: nothing to do")
    assert seat.view.text() == before
    said = seat.run("resize", "__nb_pitch_0__", "-", on, key, 480)
    assert said.startswith("resize: arc.notes — len 384 → 480"), said
    assert "len 480" in seat.view.text(), "past the bar line is written as it is"


def test_a_hand_on_the_end_of_any_note_of_the_group_stretches_them_all():
    """Sweep bar 1, take the end of one of the melody's notes, carry it
    along one beat: six lines change their `len` by the same ticks,
    through one rewrite, and the transcript says `stretch`."""
    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    m = next(i for i in group if roll.events[i][1] - roll.events[i][0] == 96)
    ex, ey = _end_of(roll, m)
    _feed(seat, view, "press", ex, ey)
    assert seat.group[0] == group, "a press on the end of a group's note keeps the group"
    _feed(seat, view, "drag", ex + 16, ey)
    _feed(seat, view, "drag", ex + 32, ey)
    assert seat.bench.previewing["__nb_sels_0__"] == [float(x) for x in group]
    assert seat.bench.previewing["__nb_grow_0__"] == 32.0
    before = seat.view.text()
    writes = []
    real = seat.view.replace
    seat.view.replace = lambda text: writes.append(text) or real(text)
    said = _feed(seat, view, "release", ex + 32, ey)
    assert said[0].startswith("stretch: arc.notes — ") and f"{len(group)} notes, +96 ticks" in said[0], said
    assert len(writes) == 1
    changed = [(a, b) for a, b in zip(before.splitlines(), seat.view.text().splitlines()) if a != b]
    assert len(changed) == len(group)
    for a, b in changed:
        la = int(a.split("len ")[1].split()[0]); lb = int(b.split("len ")[1].split()[0])
        assert lb - la == 96, (a, b)
    roll2 = _rebuilt(seat)
    assert sorted((roll2.events[n][0], roll2.events[n][3]) for n in seat.group[0]) == \
        sorted((roll.events[n][0], roll.events[n][3]) for n in group), "held by key across the rebuild"


def test_a_stretch_that_would_leave_a_note_shorter_than_a_tick_refuses_whole():
    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    before = seat.view.text()
    assert seat.run("stretch", "__nb_rail_0__", -96).startswith("stretch: arc.notes:"), "the melody's beat-long notes would vanish"
    assert seat.view.text() == before and seat.group[0] == group
    assert seat.run("stretch", "__nb_rail_0__", 0).startswith("stretch: nothing to do")
    assert seat.run("stretch", "__nb_pitch_0__", 12).startswith("stretch: name the box's rail")
    said = seat.run("stretch", "__nb_rail_0__", -48)
    assert said.startswith("stretch: arc.notes — ") and "-48 ticks" in said, said


def test_the_picture_draws_the_held_selection_longer_from_its_start():
    from gestate.gui import Substrate
    from gestate.scorebox import geometry_of, rows_channel, rows_reading

    rolls, _b, (live, _r, entries) = _live_and_baked()
    view = Substrate.several(live, 44100, entries)[0]
    roll = rolls[0]
    geo = geometry_of(roll)
    view.write(rows_channel(0), rows_reading(roll))
    view.tick()
    heads = lambda: [i for i in view.picture() if i[0] == "rect" and i[4] == geo.note_h][:3]
    before = heads()
    view.write("__nb_sels_0__", [0.0, 1.0])
    view.write("__nb_held_0__", 0.0)
    view.write("__nb_grow_0__", 24.0)
    view.tick()
    after = heads()
    for k in (0, 1):
        assert after[k][1] == before[k][1] and after[k][3] == before[k][3] + 24, "the start stays, the end moves"
    assert after[2] == before[2], "an unselected note is untouched"


# ── Slice 4, continued — the section resized on its ruler ──────────────────


def test_the_ruler_is_the_sections_handle_and_a_drag_along_rewrites_its_bars():
    """A press on the ruler takes the section's end; a drag along by one
    bar says `bars 8 → 9`, the picture marks the end, and the release
    runs `bars`: the section record's one field on one line."""
    from gestate.scorebox import rail_of, scale_of, x_of

    _here, seat, view, roll = _page_seat()
    cx, cy, w, h = rail_of(roll)
    _lo, _hi, span = scale_of(roll)
    one = roll.bars[1] - roll.bars[0]
    said = _feed(seat, view, "press", x_of(roll, 4 * one), cy)
    assert said[0].startswith("the section's end"), said
    assert said[1] == "", "the body carries nothing while the ruler has the hand"
    assert seat.sizing is not None and seat.sizing[2] == 8
    assert seat.bench.previewing["__nb_endx_0__"] > -9000, "the end is drawn"
    _feed(seat, view, "drag", x_of(roll, 4 * one) + 64, cy)
    said = _feed(seat, view, "drag", x_of(roll, 5 * one), cy)
    assert said[0] == "bars 8 → 9 (+1)", said
    before = seat.view.text()
    said = _feed(seat, view, "release", x_of(roll, 5 * one), cy)
    assert said[0].startswith("bars: arc.notes — section A bars 8 → 9 on line "), said
    changed = [(a, b) for a, b in zip(before.splitlines(), seat.view.text().splitlines()) if a != b]
    assert changed == [("section A  key D  mode lydian  bars 8  beats 4  voices melody,upper,middle,lower,bass",
                        "section A  key D  mode lydian  bars 9  beats 4  voices melody,upper,middle,lower,bass")]
    assert seat.sizing is None
    assert any(step.verb == "bars" for step in seat.log.steps)


def test_a_section_does_not_shrink_past_its_notes_and_grows_freely():
    _here, seat, view, roll = _page_seat()
    before = seat.view.text()
    said = seat.run("bars", "__nb_ruler_0__", 8, 7)
    assert said.startswith("bars: arc.notes:") and "bar 8 of section A has notes" in said, said
    assert seat.view.text() == before
    assert seat.run("bars", "__nb_ruler_0__", 8, 0).startswith("bars: a section is at least one bar")
    assert seat.run("bars", "__nb_ruler_0__", 7, 9).startswith("bars: section A has 8 bars, not 7")
    assert seat.run("bars", "__nb_ruler_0__", 8, 8).startswith("bars: nothing to do")
    assert seat.run("bars", "__nb_rail_0__", 8, 9).startswith("bars: name the box's ruler")
    assert seat.run("bars", "__nb_ruler_0__", 8, 10).startswith("bars: arc.notes — section A bars 8 → 10")
    assert "bars 10  beats 4" in seat.view.text()
    assert seat.run("bars", "__nb_ruler_0__", 10, 8).startswith("bars: arc.notes — section A bars 10 → 8"), "back past empty bars"


def test_a_click_on_the_ruler_changes_nothing_and_the_compact_box_has_no_ruler():
    from gestate.scorebox import RULER, build_rolls, rail_of, regions_of

    _here, seat, view, roll = _page_seat()
    cx, cy, _w, _h = rail_of(roll)
    before = seat.view.text()
    _feed(seat, view, "press", cx, cy)
    said = _feed(seat, view, "release", cx, cy)
    assert said == ["", "", ""] and seat.view.text() == before
    assert seat.bench.previewing["__nb_endx_0__"] == -10000.0, "the end mark is gone"

    source, _o = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks = [(i + 1, l[6:]) for i, l in enumerate(source.splitlines()) if l.startswith("notes ")]
    box = build_rolls(source, asks[:1], 22050, 0)[0]
    assert not any(r.hand == RULER for r in regions_of([box]).values()), "no section, no handle"


# ── Slice 4, the last tool — the tapped tempo ─────────────────────────────
#
# Henri, Q2: *"tempo could still live in .ges, but allow tapping it.  bit
# like how mkKnob creates sliders that can be edited.  .notes could also
# have bpm marking, but it's not used if .ges has one."*


def test_a_notes_file_may_say_its_tempo_once_and_the_writer_puts_it_first():
    text = "section A  bars 1  beats 4  voices lead\nbpm 132\nnote  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf\n"
    parsed = notes.parse(text, "t.notes")
    assert parsed.bpm == 132 and parsed.bpm_line == 2
    assert notes.write(parsed).splitlines()[0] == "bpm 132", "first, the one fact about the whole file"
    assert notes.parse(notes.write(parsed), "t.notes").bpm == 132, "and it survives the round trip"
    assert notes.parse("section A  bars 1  beats 4  voices lead\n", "t.notes").bpm is None
    with pytest.raises(notes.NotesError, match="declared twice"):
        notes.parse("bpm 100\nbpm 120\nsection A  bars 1  beats 4  voices lead\n", "t.notes")
    with pytest.raises(notes.NotesError, match="takes one number"):
        notes.parse("bpm 100 120\nsection A  bars 1  beats 4  voices lead\n", "t.notes")
    with pytest.raises(notes.NotesError, match="at least one"):
        notes.parse("bpm 0\nsection A  bars 1  beats 4  voices lead\n", "t.notes")
    with pytest.raises(notes.NotesError, match="not a whole number"):
        notes.parse("bpm fast\nsection A  bars 1  beats 4  voices lead\n", "t.notes")
    # the prose above it belongs to it, and comes back with it
    prosed = ("# the tempo of the day\nbpm 132  # tapped\nsection A  bars 1  beats 4  voices lead\n\n"
              "note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf\n")
    assert notes.write(notes.parse(prosed, "t.notes")) == prosed


def test_the_wrapper_plays_a_notes_file_at_its_own_tempo_and_an_including_ges_keeps_its_own():
    with _copied() as here:
        target = here.parent / "arc.notes"
        target.write_text("bpm 132\n" + target.read_text())
        wrapped = notes.wrapper(target)
        assert "bpm = 132" in wrapped and "The file says `bpm 132`" in wrapped
        assert "bpm = 100" not in wrapped
        assert "bpm = 100" in notes.wrapper(NOTES), "a silent file goes at the wrapper's tempo"
        source, _o = notes.expanded(here.read_text(), here.parent)
        assert "bpm = 92" in source and "132" not in source, "the include brings notes only"


def test_tempo_writes_the_notes_record_and_rewrites_it_and_the_bench_plays_at_it():
    _here, seat, _view, _roll = _page_seat()
    before = seat.view.text()
    said = seat.run("tempo", 132)
    assert said == "tempo: arc.notes — bpm 132 written on line 1", said
    assert seat.view.text() == "bpm 132\n" + before
    said = seat.run("tempo", 96)
    assert said == "tempo: arc.notes — bpm 132 → 96 on line 1", said
    assert seat.run("tempo", 96).startswith("tempo: nothing to do")
    assert seat.run("tempo", 0).startswith("tempo: a tempo is between")
    assert seat.run("tempo", 1000).startswith("tempo: a tempo is between")
    # the records road goes at the file's tempo
    program = seat.bench.program(seat.view.text())
    seat.bench._engine = seat.bench.kind.engine_program(seat.bench, seat.view.text())
    seat.bench._load_score(program)
    assert seat.bench.bpm == 96 and "bpm = 96" in seat.bench._engine


def test_tempo_rewrites_the_ges_files_bpm_literal_and_refuses_a_file_without_one():
    with _copied() as here:
        _roll, seat = _rolled_page(here)
        said = seat.run("tempo", 120)
        assert said == "tempo: arcnotes.ges — bpm 92 → 120 on line 158", said
        assert [l for l in seat.view.text().splitlines() if l.startswith("bpm")] == ["bpm : Int", "bpm = 120"]
        assert seat.run("tempo", 120).startswith("tempo: nothing to do")
        seat.view._text = seat.view._text.replace("bpm = 120", "tempo = 120")
        assert seat.run("tempo", 100).startswith("tempo: this file says no `bpm = …`")


def test_taps_in_time_are_a_tempo_and_a_pause_starts_a_new_run(monkeypatch):
    from gestate import session as S

    ticks = iter([10.0, 10.5, 11.0, 11.5, 20.0, 20.25, 20.5])
    monkeypatch.setattr(S, "_tap_clock", lambda: next(ticks))
    _here, seat, _view, _roll = _page_seat()
    assert seat.run("tap") == "tap 1 — again, in time"
    assert seat.run("tap") == "tap 2 — 120 bpm; tempo: arc.notes — bpm 120 written on line 1"
    assert seat.run("tap").startswith("tap 3 — 120 bpm")
    assert seat.run("tap").startswith("tap 4 — 120 bpm")
    assert seat.run("tap") == "tap 1 — again, in time", "eight and a half seconds later is a new run"
    assert seat.run("tap") == "tap 2 — 240 bpm; tempo: arc.notes — bpm 120 → 240 on line 1"
    assert seat.run("tap") == "tap 3 — 240 bpm"
    assert seat.view.text().splitlines()[0] == "bpm 240"
    assert [step.verb for step in seat.log.steps if step.verb in ("tap", "tempo")].count("tempo") == 2, \
        "the written half is in the transcript exactly as often as the number changed"


def test_tap_has_a_chord_and_the_command_list_advertises_it():
    from gestate.session import KEYS

    assert KEYS["tap"] == "Ctrl-T"
    _here, seat, _view, _roll = _page_seat()
    assert any(getattr(c, "name", None) == "tap" and getattr(c, "key", "") == "Ctrl-T"
               for c in seat.commands()), "the window binds the chord off the list"


# ── The roll's vocabulary is a library — 2026-09-06, evening ───────────────


def test_the_page_is_written_over_roll_ges_and_the_compact_box_is_not():
    """Henri: *"Tehdään sitten se idea 2, moduuli."*  A `.notes` page's
    program declares its boxes' `Body` and is compiled with `roll.ges`
    in front; a `.ges` box beside a line still carries its own drawing
    and gets `gui.ges` alone.  The page's text is a third of what the
    unrolled program was."""
    from gestate.audio import has_roll, library_text, preludes
    from gestate.scorebox import asks, build_rolls, page_program

    _rolls, (baked, _r, _e), (live, _r2, _e2) = _live_and_baked()
    assert has_roll(live) and has_roll(baked)
    assert library_text("roll.ges") in preludes(live)
    assert len(live) < 40_000, len(live)
    assert "rollFurniture" in live and "rollNotes" in live and "TouchY __nb_pitch_0__ (TouchX __nb_rail_0__" in live

    source, _o = notes.expanded(ARCNOTES.read_text(), ARCNOTES.parent)
    asks_ = [(i + 1, l[6:]) for i, l in enumerate(source.splitlines()) if l.startswith("notes ")]
    compact, _regions, _entries = page_program(build_rolls(source, asks_[:1], 22050, 0))
    assert not has_roll(compact)
    assert library_text("roll.ges") not in preludes(compact)


def test_roll_ges_states_the_editing_scales_numbers_as_scorebox_does():
    """The library says `rollSemi`, `rollNoteH`, `rollRulerH` for itself,
    and they are `scorebox`'s — one arithmetic, held in two places."""
    import re

    from gestate.audio import library_text
    from gestate.scorebox import RULER_H, SEMI_H, editing

    text = library_text("roll.ges")
    said = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(roll\w+) : Int\n\1 = (\d+)$", text, re.M)}
    assert said["rollSemi"] == SEMI_H
    assert said["rollNoteH"] == editing(60, 72, 384).note_h
    assert said["rollRulerH"] == RULER_H


def test_probe_says_what_is_under_a_point_and_where_it_was_written():
    """`card:gui-is-difficult.md` idea 7 as a command: a point on a
    note of the page names the rail and the pitch hand around it, the
    tick and key the point means, and the line of `arc.notes` the note
    was written on — read off the hit table, nothing written."""
    from gestate.gui import Substrate
    from gestate.scorebox import geometry_of, regions_of
    from gestate.session import probe_at

    rolls, (baked, _r, entries), _l = _live_and_baked()
    view = Substrate.several(baked, 44100, entries)[0]
    roll = rolls[0]
    geo = geometry_of(roll)
    heads = [i for i in view.picture() if i[0] == "rect" and i[4] == geo.note_h]
    _kind, x, y, w, h, _c = heads[0]

    class Bench:
        substrate = view
        note_regions = regions_of(rolls)
        origins = {}

    said = probe_at(Bench(), x + w // 2, y + h // 2)
    assert "rail" in said and "pitch" in said, said
    assert "written at line" in said, said
    assert "tick" in said and "key" in said, said
    # Somewhere with nothing under it says so, and how many there are.
    assert probe_at(Bench(), -5000, -5000).startswith("probe: nothing at")


def test_a_ctrl_press_asks_and_holds_nothing():
    """`spec/workbench.md` §"The window inspects itself": a `pointed` on
    the rail then on the pitch half names the tick, then the note and
    the line that wrote it; the answer goes back to the view by name to
    be drawn where the attachment is; and nothing is held — the hand
    chart stays free, nothing is selected, no preview is written.  The
    transcript keeps the step with its answer."""
    from gestate.scorebox import across_of, reach_of
    from gestate.session import act

    with _copied() as here:
        roll, seat = _rolled_page(here)
        told = []
        seat.view.tell = lambda name, text: told.append((name, text))
        low, high = reach_of(roll)
        on, _off, _k, key, _v, _m = roll.events[0]
        rail = act(seat, f"pointed\t__nb_rail_0__\t{across_of(roll, on)}")
        assert rail.startswith("the rail — tick"), rail
        pitch = act(seat, f"pointed\t__nb_pitch_0__\t{(high - key) / (high - low)}")
        assert "note" in pitch and "written at line" in pitch, pitch
        assert seat.hand == {} and seat.selected == {}
        assert seat.bench.previewing == {}
        assert [n for n, _ in told] == ["__nb_rail_0__", "__nb_pitch_0__"]
        assert told[1][1] == pitch
        step = seat.log.steps[-1]
        assert step.verb == "pointed" and step.said == pitch
        # The pitch half alone has no tick to name a note by, and says so.
        seat.pointed_tick.clear()
        assert "no rail spoke" in act(seat, "pointed\t__nb_pitch_0__\t0.5")


def test_ask_is_the_press_without_the_grab():
    """`Substrate.ask` names the attachments a press would take with the
    values a press would write, and keeps no hold; and `touch point x y`
    through `act` says, for each, the words `probe x y` says for the
    same point — one reader, by construction."""
    from gestate.scorebox import geometry_of
    from gestate.session import Session, act, probe_at

    _here, seat, view, roll = _page_seat()
    geo = geometry_of(roll)
    heads = [i for i in view.picture() if i[0] == "rect" and i[4] == geo.note_h]
    _kind, x, y, w, h, _c = heads[0]
    cx, cy = x + w // 2, y + h // 2
    asked = view.ask(cx, cy)
    assert view._held is None
    pressed = [(n, v) for _k, n, v in view.touch_all("press", cx, cy)]
    view.touch_all("release", cx, cy)
    assert asked == pressed, (asked, pressed)
    assert {n for n, _ in asked} == {"__nb_rail_0__", "__nb_pitch_0__"}

    class Bench:
        substrate = view
        note_regions = seat.bench.note_regions
        origins = getattr(seat.bench, "origins", None) or {}

        def ask(self, x, y):
            return view.ask(x, y)

    class View:
        def text(self):
            return ""

    other = Session(bench=Bench())
    other.view = View()
    by_ask = set(act(other, f"touch\tpoint\t{cx}\t{cy}").split("; "))
    by_probe = {part.split(" — ", 1)[1]
                for part in probe_at(Bench(), cx, cy).split("; ")}
    assert by_ask == by_probe, (by_ask, by_probe)
    assert act(other, "touch\tpoint\t-5000\t-5000") == "pointed: nothing at -5000,-5000"


FADER = """
dragged : Chan Float
dragged = chan

level : Sig Float
level = 0.5 ::: mkSig (wait dragged)

substrate : Sig Sub
substrate = onTouchY dragged (rect 12 120 (colour 40 40 40))
"""


def test_a_plain_channel_is_told_its_value_and_its_line():
    """A fader is a channel and not a note, and the picture still answers
    *which line made this*: what a press would write, and the line that
    declared the channel."""
    from gestate.gui import Substrate
    from gestate.session import describe_touch

    class Bench:
        substrate = Substrate(FADER, rate=8000)
        source = FADER

    said = describe_touch(Bench(), "dragged", 0.25)
    assert "a press here would write 0.25" in said, said
    assert "declared at line 2" in said, said
    Bench.substrate.write("dragged", 0.75)
    assert describe_touch(Bench(), "dragged", 0.25).startswith("holds 0.75")



# ── Identity: the file is a table, and the selection follows the note ──────
#
# `card:gui-is-difficult.md` Q7, Henri, 2026-09-08: *"nuotti saisi
# lajittua siihen järjestykseen mikä on tiedostolle sovittu."*  A note's
# identity is its content, never its number in the roll; the file is
# written in its own order after every gesture; a selection is held by
# key across the rebuild the commit causes.


def test_a_note_moved_in_time_sorts_to_the_files_order():
    """The buffer is canonical after a rail drag, and the change is one
    field of one line — the line now standing where the note sounds."""
    from gestate.scorebox import across_of, grid_of, scale_of

    _here, seat, view, roll = _page_seat()
    note = 5
    on, key = roll.events[note][0], roll.events[note][3]
    chan = _press_a_note(seat, roll, note)
    grid = grid_of(roll)
    _lo, _hi, span = scale_of(roll)
    seat.touched("__nb_rail_0__", across_of(roll, on) + 2 * grid / span)
    before = seat.view.text()
    said = seat.released("__nb_rail_0__")
    assert said.startswith("move: arc.notes —"), said
    after = seat.view.text()
    assert notes.write(notes.parse(after, "arc.notes")) == after, "the file is in its own order"
    gone = sorted(set(before.splitlines()) - set(after.splitlines()))
    came = sorted(set(after.splitlines()) - set(before.splitlines()))
    assert len(gone) == 1 and len(came) == 1, (gone, came)
    assert gone[0].replace(f"at {on % 384}", "", 1) == came[0].replace(f"at {on % 384 + 2 * grid}", "", 1), \
        "one field changed and the line moved"
    assert before.splitlines().index(gone[0]) != after.splitlines().index(came[0]), \
        "and the line stands somewhere else now — past the neighbour it overtook"


def test_the_selection_follows_the_note_it_moved_through_the_rebuild():
    """Two nudges of one note without pressing it again: after the first
    commit's rebuild the selection names the note at its new tick, so
    the second `move` moves the same note — what a person expects and
    what an index cannot give."""
    _here, seat, view, roll = _page_seat()
    note = 5
    on, key = roll.events[note][0], roll.events[note][3]
    chan = _press_a_note(seat, roll, note)
    seat.released(chan); seat.released("__nb_rail_0__")
    assert seat.run("move", "__nb_rail_0__", on, on + 96).startswith("move: arc.notes —")
    roll2 = _rebuilt(seat)
    assert 0 not in seat.pending and 0 in seat.selected, "settled"
    assert roll2.events[seat.selected[0]][0] == on + 96 and roll2.events[seat.selected[0]][3] == key
    assert seat.bench.previewing["__nb_sel_0__"] == float(seat.selected[0]), "and the picture outlines it"
    said = seat.run("move", "__nb_rail_0__", on + 96, on + 192)
    assert said.startswith("move: arc.notes —"), said
    roll3 = _rebuilt(seat)
    assert roll3.events[seat.selected[0]][:1] == (on + 192,)


def test_a_group_follows_through_the_rebuild_and_can_be_carried_twice():
    _here, seat, view, roll = _page_seat()
    _sweep(seat, view, roll, 0, 78, 384, 62)
    group = seat.group[0]
    assert seat.run("carry", "__nb_rail_0__", 2, 0).startswith("carry: arc.notes —")
    roll2 = _rebuilt(seat)
    assert len(seat.group[0]) == len(group)
    assert sorted(roll2.events[n][3] for n in seat.group[0]) == sorted(roll.events[n][3] + 2 for n in group)
    assert seat.run("carry", "__nb_rail_0__", 2, 0).startswith("carry: arc.notes —"), "a second carry, no second sweep"


def test_a_unison_doubling_is_transposed_through_the_selection():
    """Seven places on `arc.notes` where two voices sound one key at one
    tick.  **The voice is the address** (Henri, 2026-09-08: "laita
    transkription transpose-osoitteeseen ääni"): said, the command needs
    no press; `-` is no voice, and then the press that selected one of
    the two decides, and with nothing selected it refuses.  And a drag
    spells the voice into the transcript itself."""
    from gestate.scorebox import key_at, reach_of

    _here, seat, view, roll = _page_seat()
    twice = [i for i, e in enumerate(roll.events) if e[0] == 0 and e[3] == 62]
    assert len(twice) == 2, twice
    said = seat.run("transpose", "__nb_pitch_0__", "-", 0, 62, 64)
    assert said.startswith("transpose: 62 sounds 2 times at tick 0") and "press the one you mean" in said, said
    said = seat.run("transpose", "__nb_pitch_0__", "bass", 0, 62, 64)
    assert said.startswith("transpose: no bass sounds 62 at tick 0 — melody and middle do"), said
    said = seat.run("transpose", "__nb_pitch_0__", "middle", 0, 62, 63)
    assert said.startswith("transpose: arc.notes — key 62 → 63 on line "), said
    roll2 = _rebuilt(seat)
    assert sorted(e[3] for e in roll2.events if e[0] == 0 and e[3] in (62, 63)) == [62, 63], \
        "the middle's moved, the melody's did not"
    # `-` with a press: bar 5's doubling, the melody's pressed
    at = 4 * 384
    pair = [i for i, e in enumerate(roll2.events) if e[0] == at and e[3] == 62]
    assert len(pair) == 2, pair
    chan = _press_a_note(seat, roll2, pair[0])
    seat.released(chan); seat.released("__nb_rail_0__")
    said = seat.run("transpose", chan, "-", at, 62, 64)
    assert said.startswith("transpose: arc.notes — key 62 → 64 on line "), said
    roll3 = _rebuilt(seat)
    assert roll3.events[seat.selected[0]][:1] == (at,) and roll3.events[seat.selected[0]][3] == 64
    assert seat._voice_of(seat.bench.note_regions["__nb_rail_0__"], seat.selected[0]) == "melody"
    # and a drag spells the voice: the middle's 62 at bar 5, two semitones up
    other, = [i for i, e in enumerate(roll3.events) if e[0] == at and e[3] == 62]
    chan = _press_a_note(seat, roll3, other)
    low, high = reach_of(roll3)
    grabbed = key_at(roll3, (high - 62) / (high - low))
    up = next(d / 1000 for d in range(1000) if key_at(roll3, d / 1000) == grabbed + 2)
    seat.touched(chan, up)
    said = seat.released(chan)
    assert said.startswith("transpose: arc.notes — key 62 → 64 on line "), said
    spelled = [step for step in seat.log.steps if step.verb == "transpose"][-1]
    assert spelled.args[1] == "middle", spelled.args


def test_a_diagonal_drag_on_a_note_whose_move_reorders_the_file_keeps_both_axes():
    """F211: the note at tick 480 of `arc.notes` sorts past its neighbour
    when moved a beat, so a `move` then a `transpose` by address lost
    the pitch.  One `carry` writes both fields of one line."""
    from gestate.scorebox import across_of, grid_of, key_at, reach_of, scale_of

    _here, seat, view, roll = _page_seat()
    note = 5
    on, key = roll.events[note][0], roll.events[note][3]
    chan = _press_a_note(seat, roll, note)
    grid = grid_of(roll)
    _lo, _hi, span = scale_of(roll)
    low, high = reach_of(roll)
    grabbed = key_at(roll, (high - key) / (high - low))
    up = next(d / 1000 for d in range(1000) if key_at(roll, d / 1000) == grabbed + 2)
    seat.touched("__nb_rail_0__", across_of(roll, on) + 2 * grid / span)
    seat.touched(chan, up)
    before = seat.view.text()
    said = seat.released("__nb_rail_0__")
    assert said.startswith("carry: arc.notes — 1 note, +2 semitones, +192 ticks"), said
    assert seat.released(chan) == ""
    after = seat.view.text()
    gone = sorted(set(before.splitlines()) - set(after.splitlines()))
    came = sorted(set(after.splitlines()) - set(before.splitlines()))
    assert len(gone) == 1 and len(came) == 1, (gone, came)
    assert f"key {key + 2}" in came[0] and f"at {on % 384 + 2 * grid}" in came[0], came
    assert notes.write(notes.parse(after, "arc.notes")) == after, "and the file is in its own order"

