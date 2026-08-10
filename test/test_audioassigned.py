"""`Assigned Voice` — a `Score` performed by this program's own banks.

`music.ges` has always had `Play Rendered`: a note committed to a MIDI
program, carrying (program, key, velocity) and nothing else.  `Assigned
Voice` is its twin — a note committed to a `voices` bank, carrying **the
author's own payload**.

The two are the same construct at different ages: a sum over the targets a
backend offers, each constructor carrying its target's payload.  They are
kept side by side rather than merged, because merging would make `Rendered`
— and therefore `music.ges`, which the spec describes — partly generated.

What makes this work rather than needing a second type parameter on `Score`
is that `Assigned` is **parametric in `a`**, exactly as `Play` is: it
carries no payload of type `a`, so a bound score unifies with `Void` and
`[: Void :]` still proves every note was assigned.  That is the property the
first test here pins, because everything else rests on it.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from gestate.audioalloc import Allocator
from gestate.audioengine import run
from gestate.audioextract import extract_analysis
from gestate.audiollvm import run_native
from gestate.audioscore import (ScoreError, assemble_performance,
                                duration_of_voices, perform_voices,
                                schedule_voices)
from gestate.audiovoices import banks_of, channels_of, expand
from gestate.pipeline import analyse

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

SYNTH = """
Custom := Custom Float Int

voices lead 3 myVoice : Sig Float

levelAt : Int -> Int -> Int -> Float
levelAt n on off = case on of
    0 -> 0.0
    _ -> exp (negate 3.0 * toFloat (n - on + 1) / sampleRate)

outV : Both Gate Custom -> Float
outV p = case p of
    Both w c -> case w of
        Gate on off -> inner on off c

inner : Int -> Int -> Custom -> Float
inner on off c = case c of
    Custom f k -> sawOf (wrap (toFloat k * 0.002)) * f * 0.2

myVoice : Sig Gate -> Sig Custom -> Sig Float
myVoice g s = myVoiceFolded (!Both g s)

myVoiceFolded : Sig (Both Gate Custom) -> Sig Float
myVoiceFolded s = map outV s

sound : Sig Float
sound = gain 0.5 lead
"""

PIECE = """
tune : [: Custom :]
tune = '(Custom 1.0 60) ++ '(Custom 0.8 64) ++ '(Custom 0.6 67)

score : [: Void :]
score = tune >>= voices.lead

bpm : Int
bpm = 120
"""

RATE, BLOCK = 4000, 64
BOTH = SYNTH + "\n" + PIECE


def _allocators():
    return {"lead": Allocator(channels_of(BOTH, banks_of(BOTH)[0]))}


# ── The property everything rests on ────────────────────────────────────────


def test_an_assigned_score_is_still_void():
    """`Assigned : Voice -> Score a` is parametric in `a`, like `Play`.

    Which is why `Score` needs no second type parameter: a bound score
    carries no payload of type `a`, so it unifies with `Void` and
    `[: Void :]` goes on proving that every note was assigned — while the
    payload the *bank* receives is the author's own type.
    """
    analysis = analyse(assemble_performance(SYNTH, PIECE, RATE))
    assert str(analysis.types["score"]) == "(Score Void)"
    assert str(analysis.types["tune"]) == "(Score Custom)"


def test_a_payload_may_not_reach_a_bank_that_does_not_take_it():
    """The guarantee that replaces "did you remember an instrument".

    Two banks with different payloads: assigning one's notes to the other
    is a *type error*, not a note that plays wrong or vanishes.
    """
    from gestate.unify import UnifyError

    synth = SYNTH.replace(
        "sound = gain 0.5 lead",
        "sound = 0.5 * (lead + bass)\n\n"
        "Other := Other Int\n\n"
        "voices bass 2 bassVoice : Sig Float\n\n"
        "bassVoice : Sig Gate -> Sig Other -> Sig Float\n"
        "bassVoice s = map (p => 0.0) s\n")
    bad = PIECE.replace("tune >>= voices.lead", "tune >>= voices.bass")
    with pytest.raises(UnifyError):
        analyse(assemble_performance(synth, bad, RATE))


# ── What the expander generates ─────────────────────────────────────────────


def test_voice_is_a_constructor_per_bank_carrying_its_payload():
    out = expand(BOTH)
    assert "Voice := LeadNote Custom" in out
    assert "voicesLead : Custom -> [: a :]" in out
    assert "voicesLead x = Assigned (LeadNote x)" in out


def test_the_dot_spelling_is_rewritten():
    """`voices.lead` is not projection.

    `.` is projection in gestate — `x.0`, `x.field`, resolved from the
    base's type — so `voices.lead` would parse as a projection out of a
    variable called `voices`, needing a record with a *polymorphic* field.
    Rewriting the source keeps the spelling without growing the parser.
    """
    out = expand(BOTH)
    assert "voices.lead" not in out
    assert "tune >>= voicesLead" in out


def test_a_synth_with_no_assignment_gets_no_voice_type():
    """The injections name `Assigned`, which belongs to `music.ges`.

    A plain synth is not given `music.ges` — nine constructors and their
    compile time are not something a program that plays no score should pay
    — so a program that never writes `voices.<name>` gets neither.
    """
    out = expand(SYNTH)
    assert "Voice :=" not in out
    assert "Assigned" not in out


def test_assigning_to_a_bank_that_is_not_there_is_refused():
    """And refused where the spelling the author wrote is still visible.

    Left to the type checker it would surface as `Unknown global
    'voicesNothing'` — a name nobody typed, from a rewrite they did not
    know had happened.
    """
    from gestate.audiovoices import VoicesError

    with pytest.raises(VoicesError, match="names no bank"):
        expand("score : [: Void :]\nscore = r >>= voices.nothing\n")

    with pytest.raises(VoicesError, match="names no bank"):
        expand(BOTH.replace("voices.lead", "voices.brass"))


# ── Reading it back — the host opens `Voice` ────────────────────────────────


def test_a_layout_gives_the_bank_and_the_payload():
    """"The host opens it" is a tag lookup and nothing more.

    The constructor's position is the bank and its arguments are the
    payload, exactly as `midi.py` reads `Midi`/`Perc`.  Nothing in gestate
    ever takes a `Voice` apart, which is what lets it be opaque.
    """
    bpm, events = perform_voices(SYNTH, PIECE, RATE)
    assert bpm == 120
    assert events == [(0, 96, "lead", ((1.0, 60),)),
                      (96, 192, "lead", ((0.8, 64),)),
                      (192, 288, "lead", ((0.6, 67),))]


def test_a_bank_with_no_allocator_is_named():
    bpm, events = perform_voices(SYNTH, PIECE, RATE)
    with pytest.raises(ScoreError, match="no allocator was given"):
        schedule_voices(events, bpm, RATE, {}, block=BLOCK)


def test_the_same_payload_twice_is_two_notes():
    """Keyed by the event, not by the payload.

    A `Score` may hold one payload twice and each is its own note — where
    MIDI's key doubles as an identity only because a keyboard cannot press
    one key twice.
    """
    piece = PIECE.replace(
        "tune = '(Custom 1.0 60) ++ '(Custom 0.8 64) ++ '(Custom 0.6 67)",
        "tune = '(Custom 1.0 60) ++ '(Custom 1.0 60)")
    both = SYNTH + "\n" + piece
    allocators = {"lead": Allocator(channels_of(both, banks_of(both)[0]))}
    bpm, events = perform_voices(SYNTH, piece, RATE)
    schedule = schedule_voices(events, bpm, RATE, allocators, block=BLOCK)

    # Two voices used, not one taken and released twice.
    started = {c.split("f")[0] for c in schedule.channels()}
    assert len(started) == 2
    assert allocators["lead"].sounding() == []


# ── And it plays ────────────────────────────────────────────────────────────


@needs_clang
def test_a_piece_assigned_to_its_own_banks_plays_identically():
    """The end of the whole thread: a piece written in gestate, in the
    program's own payload type, performed by an instrument written in
    gestate — and the three engines agree about the result."""
    bpm, events = perform_voices(SYNTH, PIECE, RATE)
    schedule = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    graph = extract_analysis(
        analyse(assemble_performance(SYNTH, PIECE, RATE)), rate=RATE)
    control = schedule.control_for(graph)
    samples = min(duration_of_voices(events, bpm, RATE), 400)

    engine = run(graph, samples, block=BLOCK, control=control)
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, samples, block=BLOCK,
                          control=control) == engine
    assert max(abs(s) for s in engine) > 0.01, "silent"
    assert all(-1.0 <= s <= 1.0 for s in engine), "out of range"


def test_an_unassigned_bank_is_silent():
    """Nothing plays until a note says so — `gateAt` 0 means no note."""
    from gestate.audioschedule import Schedule

    graph = extract_analysis(
        analyse(assemble_performance(SYNTH, PIECE, RATE)), rate=RATE)
    control = Schedule().control_for(graph)
    assert run(graph, 200, block=BLOCK, control=control) == [0.0] * 200


# ── The example ─────────────────────────────────────────────────────────────


def test_the_duet_is_one_program_and_assigns_its_own_bass():
    """`examples/audio/duet.ges` — instruments, piece and mix together.

    The piece is written in the program's own payload and assigned with
    `voices.bass`, so which bank plays it is decided *lexically* and checked
    by the type checker.  `lead` is left alone for a keyboard.
    """
    from pathlib import Path

    from gestate.audioperform import has_score, scored

    duet = (Path(__file__).resolve().parent.parent
            / "examples" / "audio" / "duet.ges").read_text()
    assert has_score(duet), "the piece should be in the program"
    assert "voices.bass" in duet

    bpm, events = perform_voices(duet, "", RATE)
    assert bpm == 96
    assert {bank for _on, _off, bank, _p in events} == {"bass"}, \
        "the score should not touch the bank the keyboard plays"

    schedule, samples, allocators = scored(duet, rate=RATE, block=BLOCK)
    assert set(allocators) == {"bass", "lead"}
    assert samples > 0
    # Only the bass bank's channels are written: the lead's are the
    # keyboard's, and a schedule that touched them would fight it.
    assert all(c.startswith("bass") for c in schedule.channels())
