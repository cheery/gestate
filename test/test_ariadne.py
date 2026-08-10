"""Ariadne's leaves — `spec/ariadne.md`, stages one to three.

The law everything here answers to: **route a constant through any
reactive construct and the algebra must not notice.**  `draw` and
`hear` are zero-width leaves of the score monad — no box, the
continuation's content carrying its own time — so a constant draw is
invisible to the bake, a constant answer equals its own splice to the
tick, and what follows a `hear` is placed after whatever the answer
chose, which is the one place time is decided by the thread rather
than the text.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_dynamicscore import BLOCK, RATE, SYNTH, _allocators

from gestate.audiodynamic import LazyPerformer, LiveStream
from gestate.audioscore import perform_voices, stream_root

BPM = "\nbpm : Int\nbpm = 120\n"


def _events(piece, seed=0):
    return perform_voices(SYNTH, piece + BPM, RATE, seed=seed)[1]


def _drive(piece, reading, beats=14, seed=3):
    tempo, state, root, by_tag = stream_root(SYNTH, piece + BPM, RATE,
                                             seed, 0, True)
    perf = LazyPerformer(LiveStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK,
                         reader=lambda port: list(reading))
    for t in range(0, beats * 2000, BLOCK):
        perf.advance(t)
    return [(on, off, p) for on, off, _b, p in perf.history]


# ── draw ────────────────────────────────────────────────────────────────────


def test_a_constant_draw_is_invisible_to_the_algebra():
    """The constant law, chance half: a draw whose continuation ignores
    the seed changes nothing — events, ticks, durations — at any seed."""
    law = ("\nscore : [: Void :]\n"
           "score = ((do s <- draw; '(Custom 1.0 60) |* 2)"
           " ++ '(Custom 0.8 64)) >>= voices.lead\n")
    plain = law.replace("(do s <- draw; '(Custom 1.0 60) |* 2)",
                        "('(Custom 1.0 60) |* 2)")
    for seed in (0, 7, 123):
        assert _events(law, seed) == _events(plain, seed)


def test_a_used_draw_is_deterministic_by_position():
    """Same seed, same take; different seed, different take; two draws
    in one chain are two splits, not one value twice."""
    used = ("\nscore : [: Void :]\n"
            "score = (do a <- draw; b <- draw;"
            " '(Custom 1.0 (60 + below 12 a))"
            " ++ '(Custom 0.9 (60 + below 12 b))) >>= voices.lead\n")
    take5 = _events(used, seed=5)
    assert take5 == _events(used, seed=5)
    assert take5 != _events(used, seed=9)
    first, second = take5[0][3], take5[1][3]
    assert first != second, "two draws drew the same value — one split"


def test_a_draw_can_seed_a_walk():
    """The take-entropy gap (`dynscore-constraints.md` §D4), closed:
    `do s <- draw; unfold …` threads the take's own entropy into an
    endless walk — the spelling the old surface could not say."""
    from gestate.audiodynamic import ScoreStream

    piece = ("""
step : Int -> ([: Custom :], Int)
step s = case split s of
    (use, keep) -> ('(Custom 1.0 (60 + below 12 use)), keep)

score : [: Void :]
score = (do s <- draw; unfold s step) >>= voices.lead
""" + BPM)
    def take(seed):
        _t, state, root, by_tag = stream_root(SYNTH, piece, RATE, seed)
        return ScoreStream(state, root, by_tag).pull(8 * 96)

    assert take(4) == take(4), "a take must be replayable from its seed"
    assert take(4) != take(11), "the walk ignored the take's entropy"
    assert len(take(4)) == 8, "the walk did not stream"


# ── hear ────────────────────────────────────────────────────────────────────


HEARD = """
phraseOf : List Int -> [: Custom :]
phraseOf ks = case ks of
    Nil -> r
    k :: kt -> '(Custom 0.9 k) ++ phraseOf kt

score : [: Void :]
score = ((do ks <- hear 0; phraseOf ks) ++ '(Custom 0.5 36)) >>= voices.lead
"""


def _spliced(keys):
    body = " ++ ".join([f"'(Custom 0.9 {k})" for k in keys] + ["r"])
    return (f"\nscore : [: Void :]\n"
            f"score = (({body}) ++ '(Custom 0.5 36)) >>= voices.lead\n")


def test_a_constant_answer_equals_its_own_splice():
    """The constant law, world half — and the deliberate break with the
    old surface: the answer's content carries its own time, so the coda
    lands after one beat, three beats, or the bare rest, moving with
    what the world said.  No box."""
    for world in ([60], [60, 64, 67], []):
        assert _drive(HEARD, world) == _drive(_spliced(world), world), world


def test_what_follows_moves_with_the_answer():
    """B7 restated, measured: the same written coda starts at three
    different ticks under three different worlds."""
    codas = {tuple(w): _drive(HEARD, list(w))[-1][0]
             for w in ((60,), (60, 64, 67), ())}
    assert codas[(60,)] == 2 * 96          # note + trailing rest
    assert codas[(60, 64, 67)] == 4 * 96
    assert codas[()] == 96                 # the rest alone


def test_the_crust_twin_speaks_hear_unchanged(tmp_path):
    """`Hear` reaches the performer as `CueAsk` — the same cue, the
    same wire — so the native stream listens without a line of new
    machinery.  Change for change against the reference."""
    import shutil

    import pytest

    if shutil.which("cargo") is None:
        pytest.skip("no cargo to build crust with")
    from gestate.crust import native_stream

    def drive_stream(make_perf):
        held = [60, 64]
        perf = make_perf(lambda port: list(held))
        out = []
        for t in range(0, 20_000, BLOCK):
            out += perf.advance(t)
        return out

    tempo, state, root, by_tag = stream_root(SYNTH, HEARD + BPM, RATE,
                                             6, 0, True)
    want = drive_stream(lambda r: LazyPerformer(
        LiveStream(state, root, by_tag), tempo, RATE, _allocators(),
        block=BLOCK, reader=r))
    tempo2, _native, stream, _tags = native_stream(SYNTH, HEARD + BPM,
                                                   RATE, seed=6,
                                                   live=True)
    got = drive_stream(lambda r: LazyPerformer(
        stream, tempo2, RATE, _allocators(), block=BLOCK, reader=r))
    assert got == want and want
