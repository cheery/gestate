"""A mark the voice interprets — `spec/annotations.md`, the first slice.

**The claim, and it is one sentence:** a manner names an *intention*, and
what it means is the voice's.  That is not a thing prose can establish,
so it is executed here: the same score is played by a voice that reads
`Staccato` and by one that does not, and the second is held **bit-identical
to its own unmarked rendering**.  A mark that changed a voice which never
mentions it would be a command wearing an annotation's clothes.

Why it is `examples/audio/marked.ges` and not a fixture built here: the
example is the artefact a person opens and hears, and a test that built
its own would be checking a program nobody plays (`spec/verification.md`
makes the same argument about goldens).  The score is rewritten by
substitution so that the *only* difference between two renders is the
manner field — which is what makes a bit-identical result mean anything.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from gestate import audioperform
from gestate.audiollvm import run_native

ROOT = Path(__file__).resolve().parents[1]
MARKED = ROOT / "examples" / "audio" / "marked.ges"

#: The score line in the example, replaced so one bank plays one line and
#: the two renders differ in nothing else.
WHOLE = ("score = ((line Plain ++ line Staccato) >>= voices.bow)\n"
         "     ++ ((line Plain ++ line Staccato) >>= voices.pad)")


def _one(bank: str, mark: str) -> str:
    source = MARKED.read_text()
    assert WHOLE in source, "marked.ges's score line moved; this test rewrites it"
    return source.replace(WHOLE, f"score = line {mark} >>= voices.{bank}")


def _render(source: str) -> list:
    graph = audioperform.graph_of(source, rate=44100)
    perf = audioperform.Performance(graph)
    schedule, samples, _ = audioperform.scored(source, rate=44100, block=128)
    perf.sources.append(audioperform.from_schedule(schedule))
    with tempfile.TemporaryDirectory() as d:
        return run_native(graph, d, samples, 128, control=perf.control())


# ── the encoding ────────────────────────────────────────────────────────────

def _asks(ms: int, m: int) -> bool:
    """`audio.ges`'s `asks`, restated — the same arithmetic, so a change
    to one side without the other fails here rather than in a piece."""
    return (ms // m) % 2 == 1


def test_a_manner_is_a_set_and_every_combination_decodes():
    """**A set, not a choice**, which is the whole reason it is bits.

    A note may be accented *and* staccato — any violinist writes both
    marks on one head — and an ordinal would have made them exclusive by
    accident, which is a format deciding a musical question.  So all
    eight combinations are checked, not the three single ones.
    """
    staccato, accent, portamento = 1, 2, 4
    for ms in range(8):
        got = {m for m in (staccato, accent, portamento) if _asks(ms, m)}
        want = {m for m in (staccato, accent, portamento) if ms & m}
        assert got == want, f"manner {ms} decoded as {got}"
    assert _asks(3, staccato) and _asks(3, accent), "both marks on one head"
    assert not _asks(0, staccato), "Plain asks for nothing"


def test_an_unmarked_melody_asks_for_nothing():
    """`instance Notable Int` — the promise that costs a melody nothing.

    A `[: Int :]` melody is a key number and nothing else.  It must reach
    a voice that reads manners without the author writing anything, the
    same way that instance already gives it a velocity of 64.  **An
    unmarked note is not a special case**, and since the language has no
    default methods this is the *only* thing standing between a bare
    melody and a compile error.
    """
    source = """
manners : Int -> Int
manners k = manner k

sound : Sig Float
sound = !(toFloat (manners 60)) * 0.0 + sine 220.0 * 0.1
"""
    graph = audioperform.graph_of(source, rate=44100)
    assert graph.nodes, "a bare Int must answer `manner` with no instance written"


# ── the claim ───────────────────────────────────────────────────────────────

def test_the_voice_that_reads_the_mark_plays_it_differently():
    """One half of the claim: the mark crosses and is heard.

    Not merely *a* difference — the marked phrase must not be the
    unmarked one turned down, which is what a lazier voice would do and
    what a naive check would accept.  Both envelopes reach the same
    height and one lets go sooner, so the marked render is **quieter and
    more silent**, which is detachment rather than attenuation.
    """
    plain = _render(_one("bow", "Plain"))
    stacc = _render(_one("bow", "Staccato"))
    n = min(len(plain), len(stacc))
    differ = sum(1 for i in range(n) if plain[i] != stacc[i])
    assert differ > n * 0.5, f"only {differ} of {n} samples differ"

    quiet = lambda xs: sum(1 for x in xs[:n] if abs(x) < 1e-4) / n  # noqa: E731
    assert quiet(stacc) > quiet(plain) + 0.3, (
        "the staccato render is not more *silent* — it may be merely quieter, "
        "which is attenuation and not detachment")


def test_the_voice_that_ignores_the_mark_is_untouched_sample_for_sample():
    """The other half, and the one that says a manner is a hint.

    `padVoice` never mentions `manner`.  Every mark in the score reaches
    it and none of them may do anything — so this is **bit-identical**,
    not merely close.  If it ever drifts, a manner has become a command
    that the score imposes on a voice that did not ask for it, and the
    argument in `spec/annotations.md` §"Why this is notation and not
    syntax" is no longer true of the code.
    """
    plain = _render(_one("pad", "Plain"))
    stacc = _render(_one("pad", "Staccato"))
    assert len(plain) == len(stacc)
    assert plain == stacc, (
        "a voice that does not read manners rendered differently under one")


@pytest.mark.parametrize("mark", ["Plain", "Staccato", "Accent", "Portamento"])
def test_every_manner_crosses_whether_or_not_a_voice_reads_it(mark):
    """A mark no voice honours is still a legal score.

    `bowVoice` reads only `Staccato`.  `Accent` and `Portamento` are
    written, travel, and are ignored — which must be a rendering rather
    than a refusal, because the vocabulary is the tree's and a piece may
    use a word before any of its instruments answers to it.
    """
    assert _render(_one("bow", mark)), f"{mark} did not render"


# ── the mark on the roll — `spec/annotations.md` §"The picture" ─────────────

def test_the_roll_reads_the_manner_off_every_note():
    """The box draws the mark, so the box has to read it.

    **That is the reason `manner` is a method of `Notable`** and not of
    a class of its own — a design this file's spec had the other way
    round until the building found that the roll needs the same fact the
    voice does.  Here it is, riding out of the take with the key and the
    velocity.
    """
    from gestate.scorebox import asks as box_asks, build_rolls

    source = MARKED.read_text()
    roll = build_rolls(source, box_asks(source + "\nnotes score\n"), 44100, 0)
    assert roll, "marked.ges built no roll"
    events = roll[0].events
    assert events, "the roll is empty"
    marks = {e[5] for e in events}
    assert marks == {0, 1}, (
        f"the roll saw manners {marks}; marked.ges writes Plain and Staccato")


def test_a_staccato_note_is_drawn_with_a_dot_and_a_plain_one_is_not():
    """The picture, and the property that a mark is *added* to a note.

    **The bar keeps its full written length.**  A staccato note is still
    the note it was — the dot says how it is to be played, and a picture
    that shortened the bar instead would be drawing the voice's decision
    rather than the score's instruction, which is the confusion this
    whole spec exists to avoid.
    """
    from gestate.scorebox import asks as box_asks, build_rolls, roll_program

    source = MARKED.read_text() + "\nnotes score\n"
    roll = build_rolls(source, box_asks(source), 44100, 0)[0]
    text, _named = roll_program(roll)
    #: The generated program draws the dot only when the row's manner
    #: asks for it — the same `asks` arithmetic `audio.ges` uses, so the
    #: two cannot drift without this failing.
    assert "Rect 2 2" in text, "no dot is drawn at all"
    assert "% 2 == 1" in text, "the picture does not decode the manner set"
    rows = [l for l in text.splitlines() if l.strip().startswith("__nb_rows")]
    assert rows, "no row listing in the generated picture"


# ── the gesture — `spec/annotations.md` §"The gesture" ──────────────────────

#: `marked.ges` writes `line m` and calls it with `Plain` and
#: `Staccato`, so the manner is a *parameter* and no note carries an
#: atom for it — which is the right way to write that piece and the
#: wrong shape for a gesture to bite on (§"What a written manner
#: costs").  So the manners are written out here, note by note.
WRITTEN = """written : [: Tone :]
written = '(Tone 0.9 0 0) ++ '(Tone 0.9 1 0) ++ '(Tone 0.9 2 1) ++ '(Tone 0.9 3 1)
       ++ '(Tone 0.9 4 0) ++ '(Tone 0.9 3 2) ++ '(Tone 0.9 2 1) ++ '(Tone 0.9 1 0)

score = written >>= voices.bow"""


def _written_out() -> tuple:
    from gestate.scorebox import asks as box_asks, build_rolls

    source = MARKED.read_text().replace(WHOLE, WRITTEN) + "\nnotes score\n"
    return source, build_rolls(source, box_asks(source), 44100, 0)[0]


def test_marking_a_note_changes_one_atom_and_nothing_else():
    """Byte-exact, which is the tier-one invariant `transpose` set.

    One atom's characters are replaced; no reflow, no reprint, no
    reparse-and-print.  So the diff of a mark is one number and text
    undo puts it back.
    """
    from gestate.scorebox import marked

    source, roll = _written_out()
    note = next(i for i, e in enumerate(roll.events) if e[5] == 0
                and len([a for a in roll.leaves[e[2]].atoms if a[3] == 0]) == 1)
    text, said = marked(source, roll, note, 1)
    before, after = source.splitlines(), text.splitlines()
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert len(changed) == 1, f"{len(changed)} lines moved, not one"
    assert len(before) == len(after), "the file changed length"
    assert "staccato" in said, said


def test_the_margin_says_the_marks_by_name_and_not_by_number():
    """A number is what the file holds; it is not what a margin says.

    `3` is a staccato accent, and a person reading a transcript should
    not have to decode a bitmask to know what they did.
    """
    from gestate.scorebox import _manner_words

    assert _manner_words(0) == "plain"
    assert _manner_words(1) == "staccato"
    assert _manner_words(3) == "staccato + accent"
    assert _manner_words(7) == "staccato + accent + portamento"


def test_a_manner_the_box_cannot_tell_apart_is_refused_not_guessed():
    """The measured hazard, held as a refusal.

    A manner is a small number and so is a degree, so `'(Tone 0.9 0 0)`
    has two atoms equal to `0`.  **A guess here would write the wrong
    field of the right note** — the worst kind of wrong, because the
    file still parses and the piece still plays.  So it refuses with a
    sentence, and `spec/annotations.md` §"What a written manner costs"
    carries the open question about finding it by position instead.
    """
    from gestate.scorebox import RefusedError, marked

    source, roll = _written_out()
    note = next(i for i, e in enumerate(roll.events)
                if len([a for a in roll.leaves[e[2]].atoms if a[3] == e[5]]) > 1)
    with pytest.raises(RefusedError) as caught:
        marked(source, roll, note, 1)
    assert "cannot tell the manner" in str(caught.value)


def test_a_note_whose_payload_has_no_manner_is_refused_rather_than_rewritten():
    """The gesture replaces and never adds.

    Adding a field moves every character after it, which the tier-one
    invariant forbids — so a payload with nothing to change says so.
    `marked.ges`'s own `line m` form is exactly this case.
    """
    from gestate.scorebox import RefusedError, asks as box_asks, build_rolls, marked

    source = MARKED.read_text() + "\nnotes score\n"
    roll = build_rolls(source, box_asks(source), 44100, 0)[0]
    with pytest.raises(RefusedError) as caught:
        marked(source, roll, 0, 1)
    assert "no manner field" in str(caught.value) or "not written" in str(caught.value)


def test_mark_is_a_command_or_it_is_not_a_capability():
    """`spec/north_star.md`: *a gesture with no command behind it is a
    capability that does not exist.*  So it is in `command.ges`, it
    appears in the list, it carries its own sentence, and a gesture
    records in the transcript as a command a replay can read back.
    """
    from gestate.session import Session

    text = (ROOT / "gestate" / "command.ges").read_text()
    assert "mark : Text -> Int -> Int -> Command" in text
    assert "mark region was manners = Stated" in text
    assert hasattr(Session, "do_mark"), "the command has no verb behind it"


# ── the preview — `spec/annotations.md` §"The three paths, priced" ──────────

class _Bench:
    """A bench that records what was asked of it, and nothing else."""

    def __init__(self, playing=False):
        self.playing = playing
        self.rate, self.bpm = 44100, 104
        self.calls = []
        self.note_regions = {}

    def beats_to_samples(self, beat):
        return int(beat * 60 * self.rate / max(1, self.bpm))

    def start(self, seconds=None, text=None):
        self.calls.append("start")
        self.playing = True

    def seek(self, sample):
        self.calls.append(("seek", sample))

    def audition_soon(self, text, quiet=False):
        self.calls.append("audition")

    def redraw(self, text):
        self.calls.append("redraw")


def _clean_note(roll) -> tuple:
    """`(hand, note)` for a note the gesture can actually reach.

    Three things have to line up, and each is a real refusal rather than
    a quirk of this fixture: the note must sit under a **column**, since
    that is how a hand names it; the column must sound its key **once**;
    and its manner atom must be unambiguous.  A test that reached past
    any of them would be exercising a path a hand cannot take.
    """
    from gestate.scorebox import hands_of

    for hand, (_t0, _t1, under) in enumerate(hands_of(roll)):
        for j in under:
            e = roll.events[j]
            if len([k for k in under if roll.events[k][3] == e[3]]) != 1:
                continue
            if len([a for a in roll.leaves[e[2]].atoms if a[3] == e[5]]) == 1:
                return hand, j
    raise AssertionError("no note in this take is nameable and unambiguous")


def _seated(playing: bool):
    """A session with one score box region on a written-out `marked.ges`."""
    from types import SimpleNamespace

    from gestate.scorebox import asks as box_asks, build_rolls
    from gestate.session import Session

    source = MARKED.read_text().replace(WHOLE, WRITTEN) + "\nnotes score\n"
    roll = build_rolls(source, box_asks(source), 44100, 0)[0]
    seat = Session.__new__(Session)
    seat.bench = _Bench(playing)
    seat.bench.note_regions = {"r": SimpleNamespace(roll=roll, hand=0)}
    seat.view = SimpleNamespace(replace=lambda text: True)
    seat._source = lambda: source
    return seat, roll


def test_marking_while_stopped_plays_the_piece_from_that_note():
    """Path 3, and it carries the mark **because the score plays it**.

    The other two are priced in the spec: the keyboard sounds a note
    *plain* — `FromMIDI` has no manner and cannot — and rendering one
    note in isolation needs a seam into the engine that does not exist.
    This one needed nothing new: the roll knows the onset, the bench
    converts beats to samples, the transport seeks.
    """
    from gestate.midi import TICKS_PER_BEAT

    seat, roll = _seated(playing=False)
    hand, note = _clean_note(roll)
    seat.bench.note_regions["r"].hand = hand
    said = seat.do_mark("r", str(roll.events[note][3]), "1")
    assert "playing from there" in said, said
    assert "start" in seat.bench.calls, "it did not play"
    seeks = [c for c in seat.bench.calls if isinstance(c, tuple)]
    assert seeks, "it played from the top rather than from the note"
    want = int(roll.events[note][0] / TICKS_PER_BEAT * 60 * 44100 / 104)
    assert seeks[0][1] == want, f"sought {seeks[0][1]}, not the note's onset {want}"


def test_marking_while_it_plays_does_not_restart_it():
    """**The answer to the objection**, and the reason path 3 was
    takeable at all.

    Henri, on being shown it: *"this is really hard question again.
    maybe play from the marked note would work."*  The hesitation was
    that marking starts the piece — so mark five notes and it restarts
    five times.  It cannot: the seek-and-play branch is only reached
    from a **standing start**.  The first mark starts it; every mark
    after that finds it playing and auditions in place.
    """
    seat, roll = _seated(playing=True)
    hand, note = _clean_note(roll)
    seat.bench.note_regions["r"].hand = hand
    said = seat.do_mark("r", str(roll.events[note][3]), "1")
    assert "playing from there" not in said
    assert "start" not in seat.bench.calls, "it restarted a piece already playing"
    assert "audition" in seat.bench.calls, "it did not hear the edit at all"


def test_a_refused_mark_neither_writes_nor_plays():
    """A courtesy on top of an edit that succeeded — so no edit, no
    courtesy.  A preview after a refusal would say the mark took."""
    seat, roll = _seated(playing=False)
    from gestate.scorebox import hands_of

    hand, note = next((h, j) for h, (_a, _b, under) in enumerate(hands_of(roll))
                      for j in under
                      if len([a for a in roll.leaves[roll.events[j][2]].atoms
                              if a[3] == roll.events[j][5]]) > 1)
    seat.bench.note_regions["r"].hand = hand
    said = seat.do_mark("r", str(roll.events[note][3]), "1")
    assert said.startswith("mark: "), said
    assert seat.bench.calls == [], f"it acted on a refusal: {seat.bench.calls}"


# ── Accent, and the set — `spec/annotations.md`, the second slice ───────────

def test_the_accent_is_in_the_attack_and_not_in_the_level():
    """A mark is an intention, and this voice's reading of it is a
    faster bow — brightness for the first instant, settling back.

    **Not a louder note**, which is what a velocity number would have
    done and what the score deliberately did not say.  So the check is
    not that it differs but that it differs *without* being simply
    turned up: the accented render is brighter, and its overall level
    stays within a hair of the plain one.
    """
    plain = _render(_one("bow", "Plain"))
    acc = _render(_one("bow", "Accent"))
    n = min(len(plain), len(acc))
    assert sum(1 for i in range(n) if plain[i] != acc[i]) > n * 0.5

    rms = lambda xs: (sum(x * x for x in xs[:n]) / n) ** 0.5  # noqa: E731
    assert abs(rms(acc) - rms(plain)) < rms(plain) * 0.35, (
        "the accent moved the level rather than the attack — that is a "
        "velocity number wearing a mark's name")


def test_a_note_may_ask_for_two_marks_at_once():
    """**The reason a manner is a set and not a choice.**

    Any violinist writes a staccato accent on one head.  An ordinal
    would have made the two exclusive by accident, so the property to
    hold is that `Staccato + Accent` is *neither* of them: it differs
    from plain, from staccato alone and from accent alone.
    """
    takes = {m: _render(_one("bow", m)) for m in
             ("Plain", "Staccato", "Accent", "(Staccato + Accent)")}
    both = takes["(Staccato + Accent)"]
    for name in ("Plain", "Staccato", "Accent"):
        other = takes[name]
        n = min(len(both), len(other))
        assert sum(1 for i in range(n) if both[i] != other[i]) > 0, (
            f"a note asking for both sounded the same as {name} alone")


@pytest.mark.parametrize("mark", ["Accent", "(Staccato + Accent)"])
def test_a_voice_that_reads_no_manner_is_untouched_by_any_of_them(mark):
    """The claim, held for every mark rather than only the first.

    `padVoice` never mentions `manner`.  Bit-identical, not close — the
    day it drifts, a manner has become a command the score imposes.
    """
    assert _render(_one("pad", mark)) == _render(_one("pad", "Plain"))


def test_the_roll_draws_each_mark_and_both_together():
    """Under the head and over it, which is where a score puts them.

    Different side **and** different shape, so the two read apart at a
    glance — and a note asking for both draws both, which is the set
    made visible.  The generated picture asks with the tree's own
    `Staccato` and `Accent`, so it cannot drift from what a voice reads.
    """
    from collections import Counter

    from gestate.gui import Substrate, _flatten
    from gestate.scorebox import asks as box_asks, build_rolls, roll_program

    written = WRITTEN.replace("0 0)", "0 0)").replace(
        "'(Tone 0.9 1 0) ++ '(Tone 0.9 2 1) ++ '(Tone 0.9 3 1)",
        "'(Tone 0.9 1 1) ++ '(Tone 0.9 2 2) ++ '(Tone 0.9 3 3)")
    source = MARKED.read_text().replace(WHOLE, written) + "\nnotes score\n"
    roll = build_rolls(source, box_asks(source), 44100, 0)[0]
    program, _named = roll_program(roll)
    canvas = Substrate(source + "\n" + program, 44100)
    shapes = Counter((i[3], i[4]) for i in _flatten(canvas.signal.value, canvas.state)
                     if i[0] == "rect")

    wants = lambda bit: sum(1 for e in roll.events if (e[5] // bit) % 2)  # noqa: E731
    assert shapes[(2, 2)] == wants(1), "a staccato dot per staccato note"
    assert shapes[(6, 2)] == wants(2), "an accent bar per accented note"
    assert wants(1) and wants(2), "this fixture must exercise both marks"
    assert any(e[5] == 3 for e in roll.events), "and one note asking for both"


def test_every_combination_of_marks_is_drawn():
    """All eight, including the note that asks for all three.

    **A drawing that handled one mark and forgot the sum** would look
    right on every single-mark note and wrong only where they meet,
    which is the case a person writes and a fixture usually misses.  So
    the manners here run 0…7 and each glyph is counted against the
    notes that asked for it.
    """
    from collections import Counter

    from gestate.gui import Substrate, _flatten
    from gestate.scorebox import MANNERS, asks as box_asks, build_rolls, roll_program

    every = """written : [: Tone :]
written = '(Tone 0.9 0 0) ++ '(Tone 0.9 1 1) ++ '(Tone 0.9 2 2) ++ '(Tone 0.9 3 4)
       ++ '(Tone 0.9 4 3) ++ '(Tone 0.9 3 5) ++ '(Tone 0.9 2 6) ++ '(Tone 0.9 1 7)

score = written >>= voices.bow"""
    source = MARKED.read_text().replace(WHOLE, every) + "\nnotes score\n"
    roll = build_rolls(source, box_asks(source), 44100, 0)[0]
    assert sorted(e[5] for e in roll.events) == list(range(8)), (
        "the fixture must carry every combination, 0 through 7")

    program, _named = roll_program(roll)
    canvas = Substrate(source + "\n" + program, 44100)
    shapes = Counter((i[3], i[4]) for i in _flatten(canvas.signal.value, canvas.state)
                     if i[0] == "rect")
    glyph = {1: (2, 2), 2: (6, 2), 4: (2, 9)}
    for bit, word in MANNERS:
        asked = sum(1 for e in roll.events if (e[5] // bit) % 2)
        assert asked == 4, f"{word} should be asked for by four of the eight"
        assert shapes[glyph[bit]] == asked, (
            f"{word}: {asked} notes ask, {shapes[glyph[bit]]} drawn")


def test_the_drawn_bits_are_the_ones_audio_ges_declares():
    """One fact, two copies, held equal.

    A canvas program is assembled **without** `audio.ges`, so the
    picture cannot ask `asks m Staccato` the way a voice does — it has
    to write the bit.  `scorebox.MANNERS` is that copy, and a copy
    nothing checks is two things that can disagree: the day `Accent`
    moves, the roll would draw dots where a voice hears bars and neither
    would complain.
    """
    import re

    from gestate.scorebox import MANNERS

    text = (ROOT / "gestate" / "audio.ges").read_text()
    for bit, word in MANNERS:
        name = word.capitalize()
        m = re.search(rf"^{name}\s*=\s*(\d+)$", text, re.M)
        assert m, f"audio.ges no longer declares {name}"
        assert int(m.group(1)) == bit, (
            f"audio.ges says {name} = {m.group(1)}, scorebox draws {bit}")
