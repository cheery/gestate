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
    """Where both readings cost exactly one accidental, the flat wins —
    and this is the case that would put names in the file."""
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
    assert [a for _, a in asks] == [notes.bound("A", "melody"),
                                    notes.bound("A", "bass")], asks

    for (_, ask), roll in zip(asks, build_rolls(source, asks, 22050, 0)):
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
