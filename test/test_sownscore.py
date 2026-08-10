"""`spec/dynamicscore.md` stage three, the seed half — `sown` and kin.

The claims under test are the spec's own: a draw is a pure function of
seed and position (so chance music *bakes*, and bake equals stream,
given the seed); the seed splits at every `++` and `||` (so draws under
one overlay are independent and every turn of a `cycle` is fresh);
`sow` re-roots (fixed art inside improvisation); an author-declared
seed beats the renderer's; and the arithmetic is SplitMix64 to the bit,
held against an independent reference — which is the contract the Rust
cursor will be held to in its turn.
"""

from __future__ import annotations

import pytest

from test_dynamicscore import BLOCK, PIECE, RATE, SYNTH, _allocators

from gestate.audiodynamic import LazyPerformer, ScoreStream
from gestate.audioschedule import Schedule
from gestate.audioscore import (duration_of_voices, perform_voices,
                                schedule_voices, stream_root,
                                unfolding_names)

BEAT = 2000                                 # samples per beat at 120 / 4000

CHANCY = """
melody : [: Custom :]
melody = roll (x => '(Custom x 60)) ++ chance 0.5 '(Custom 1.0 72) ++ roll (x => '(Custom x 48))

score : [: Void :]
score = (melody >>= voices.lead) || (chance 0.7 '(Custom 0.8 36) >>= voices.bass)

bpm : Int
bpm = 120
"""


def _velocities(events, bank="lead"):
    return [e[3][0][0] for e in events if e[2] == bank]


# ── The draw is arithmetic: bake equals stream, given the seed ──────────────


def test_a_chancy_score_bakes_and_performs_identically():
    bpm, events = perform_voices(SYNTH, CHANCY, RATE, seed=5)
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, bpm, RATE)

    tempo, state, root, by_tag = stream_root(SYNTH, CHANCY, RATE, seed=5)
    lazy = LazyPerformer(ScoreStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK)
    performed = Schedule()
    for t in range(0, samples + BLOCK, BLOCK):
        for boundary, chan, value in lazy.advance(t):
            performed.change(boundary, chan, value)
    assert performed.changes == baked.changes


def test_one_seed_is_one_performance_and_two_are_two():
    a = perform_voices(SYNTH, CHANCY, RATE, seed=5)[1]
    b = perform_voices(SYNTH, CHANCY, RATE, seed=5)[1]
    c = perform_voices(SYNTH, CHANCY, RATE, seed=6)[1]
    assert a == b
    assert a != c


def test_fixed_art_cannot_tell_seeds_apart():
    a = perform_voices(SYNTH, PIECE, RATE, seed=1)[1]
    b = perform_voices(SYNTH, PIECE, RATE, seed=99)[1]
    assert a == b
    assert unfolding_names(SYNTH + "\n" + CHANCY) == [], \
        "a chancy score is still bakeable — the scanner must not flag it"


# ── The seed rides the tree ─────────────────────────────────────────────────


def test_two_rolls_under_one_overlay_draw_independently():
    piece = """
score : [: Void :]
score = (roll (x => '(Custom x 60)) >>= voices.lead) || (roll (x => '(Custom x 36)) >>= voices.bass)

bpm : Int
bpm = 120
"""
    events = perform_voices(SYNTH, piece, RATE, seed=3)[1]
    lead, bass = _velocities(events, "lead"), _velocities(events, "bass")
    assert lead and bass and lead != bass


def test_every_turn_of_a_cycle_draws_fresh():
    piece = """
score : [: Void :]
score = cycle (roll (x => '(Custom x 60))) >>= voices.lead

bpm : Int
bpm = 120
"""
    tempo, state, root, by_tag = stream_root(SYNTH, piece, RATE, seed=11)
    lazy = LazyPerformer(ScoreStream(state, root, by_tag), tempo, RATE,
                         _allocators(), block=BLOCK)
    for t in range(0, 6 * BEAT, BLOCK):
        lazy.advance(t)
    draws = [e[3][0][0] for e in lazy.history]
    assert len(draws) >= 6
    assert len(set(draws)) == len(draws), "a loop must breathe, not repeat"


def test_sow_pins_a_subtree_whatever_the_take():
    piece = """
score : [: Void :]
score = (roll (x => '(Custom x 60)) ++ sow 7 (roll (x => '(Custom x 48)))) >>= voices.lead

bpm : Int
bpm = 120
"""
    a = perform_voices(SYNTH, piece, RATE, seed=1)[1]
    b = perform_voices(SYNTH, piece, RATE, seed=2)[1]
    assert a[0] != b[0], "the free half should differ between takes"
    assert a[1] == b[1], "the sown half is fixed art"


def test_an_authors_seed_beats_the_renderers():
    piece = CHANCY + "\nseed : Int\nseed = 7\n"
    a = perform_voices(SYNTH, piece, RATE, seed=1)[1]
    b = perform_voices(SYNTH, piece, RATE, seed=999)[1]
    assert a == b, "`seed = 7` in the text is fixed art"
    assert a != perform_voices(SYNTH, CHANCY, RATE, seed=1)[1]


# ── The box ─────────────────────────────────────────────────────────────────


def test_sown_content_is_clipped_to_its_beat():
    """Content bends, time doesn't: a decision is one beat wide.

    The continuation answers three beats of material; only what starts
    inside the box plays, and the phrase after the decision lands on the
    downbeat it always had.
    """
    piece = """
run : Float -> [: Custom :]
run x = '(Custom x 60) ++ '(Custom x 62) ++ '(Custom x 64)

score : [: Void :]
score = (roll run ++ '(Custom 1.0 72)) >>= voices.lead

bpm : Int
bpm = 120
"""
    events = perform_voices(SYNTH, piece, RATE, seed=4)[1]
    assert len(events) == 2, events            # one clipped note + the next
    assert events[0][:2] == (0, 96)
    assert events[1][:2] == (96, 192), "the downbeat after must not move"


def test_chance_rests_for_the_same_span_it_would_have_played():
    events = perform_voices(SYNTH, CHANCY, RATE, seed=6)[1]
    onsets = {e[0] for e in events if e[2] == "lead"}
    assert 384 in onsets or 192 in onsets      # the third leaf kept its place
    assert all(e[0] in (0, 96, 192, 384) or e[2] == "bass" for e in events)


# ── The bits are the contract ───────────────────────────────────────────────


def test_the_draws_are_splitmix64_to_the_bit():
    """Held against an independent reference — the future Rust cursor's
    parity contract, written while there is only one implementation."""
    M = (1 << 64) - 1

    def mix64(z):
        z &= M
        z ^= z >> 30
        z = (z * 0xBF58476D1CE4E5B9) & M
        z ^= z >> 27
        z = (z * 0x94D049BB133111EB) & M
        z ^= z >> 31
        return z

    def unit(s):
        return (mix64(s) >> 11) / float(1 << 53)

    def split(s):
        return (mix64((s + 0x9E3779B97F4A7C15) & M),
                mix64((s + 0x3C6EF372FE94F82A) & M))

    piece = """
score : [: Void :]
score = (roll (x => '(Custom x 60)) ++ roll (x => '(Custom x 62))) >>= voices.lead

bpm : Int
bpm = 120
"""
    for seed in (0, 1, 123456789, (1 << 63) + 17):
        got = _velocities(perform_voices(SYNTH, piece, RATE, seed=seed)[1])
        left, right = split(seed)
        assert got == [unit(left), unit(right)], seed
