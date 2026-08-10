"""The seed half — `draw` and kin (`spec/ariadne.md`).

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


def test_a_draws_content_takes_its_own_time_and_long_is_the_box():
    """Ariadne's reading of the old box law (`spec/ariadne.md`): a
    decision's content carries its own time — three beats take three
    beats, and what follows waits — and a *written* box is spelled
    where boxes are spelled, with `long`.  The constant law both ways.
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
    assert len(events) == 4, events            # all three, then the next
    assert [e[:2] for e in events] == [(0, 96), (96, 192), (192, 288),
                                       (288, 384)], "time from content"

    boxed = piece.replace("roll run", "long 1 (roll run)")
    events = perform_voices(SYNTH, boxed, RATE, seed=4)[1]
    assert len(events) == 2, events            # the box, written, clips
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


# ── The transcript ──────────────────────────────────────────────────────────


def test_a_performance_equals_its_own_replay(tmp_path):
    """The format's oracle, `spec/dynamicscore.md`: the transcript records
    the world and the seed; everything else is arithmetic.

    Today the world half carries only the performance's own confessions
    (stalls, drops), so a replay is the same text under the transcript's
    seed — and it must match change for change, through a round trip on
    disk, refusing another program's log by name.
    """
    from gestate.audioperform import dynamic
    from gestate.transcript import Transcript

    def changes_of(performer):
        out = []
        for t in range(0, 6 * BEAT, BLOCK):
            out += performer.advance(t)
        return out

    live, _allocs = dynamic(SYNTH, CHANCY, rate=RATE, block=BLOCK,
                            seed=424242)
    first = changes_of(live)
    path = tmp_path / "take.transcript"
    live.record.save(path)

    kept = Transcript.load(path)
    assert kept.seed == 424242
    assert kept.belongs_to(SYNTH + "\n" + CHANCY)
    assert not kept.belongs_to(SYNTH + "\n" + PIECE), \
        "another program's log is a collage, not a replay"
    assert kept.events == live.record.events

    again, _allocs = dynamic(SYNTH, CHANCY, rate=RATE, block=BLOCK,
                             seed=kept.seed)
    assert changes_of(again) == first
    assert again.record.events == kept.events


# ── Declared spans ──────────────────────────────────────────────────────────


def test_long_pins_a_branch_to_its_declared_beats():
    """`long n s` — the stage-three invariant, handed to the author.

    Four beats of content in a two-beat box: the overflow is clipped
    and the phrase after lands where the declaration said, not where
    the content wandered.  Short content rests out the difference the
    same way.
    """
    piece = """
runOn : [: Custom :]
runOn = '(Custom 1.0 60) ++ '(Custom 0.9 62) ++ '(Custom 0.8 64) ++ '(Custom 0.7 65)

score : [: Void :]
score = (long 2 runOn ++ long 4 '(Custom 0.6 72) ++ '(Custom 0.5 74)) >>= voices.lead

bpm : Int
bpm = 120
"""
    events = perform_voices(SYNTH, piece, RATE, seed=0)[1]
    onsets = [e[:2] for e in events]
    assert onsets == [(0, 96), (96, 192),      # two of four survive the box
                      (192, 288),              # the boxed single note
                      (576, 672)], events      # after 2 + 4 declared beats


def test_marks_enumerate_without_touching_a_note():
    """`mark n` — zero beats wide, invisible to the banks, listed lazily.

    The marks stream is the transport's map of re-entry points; the
    event stream must not know they exist.  Marks survive `>>=` (an
    instrument reaches through them), recur per pass of a `cycle`, and
    cost nothing they stand between.
    """
    from gestate.gmachine import NAp, NNum, is_tuple
    from gestate.midi import _force, _int, _list

    piece = """
intro : [: Custom :]
intro = '(Custom 1.0 60) ++ '(Custom 0.9 62)

score : [: Void :]
score = (bar ++ intro ++ mark 2 ++ long 2 (cycle intro)) >>= voices.lead

bpm : Int
bpm = 120
"""
    tempo, state, root, by_tag = stream_root(SYNTH, piece, RATE, seed=3)
    marks_root = NAp(state.globals["marksMain"], NNum(3))
    marks = []
    for cell in _list(marks_root, state):
        node = _force(cell, state)
        assert is_tuple(node, 2)
        marks.append((_int(node.args[0], state), _int(node.args[1], state)))
    assert marks == [(0, 0), (192, 2)]   # anonymous, then named

    # And the notes neither moved nor multiplied for it — checked on a
    # finite variant, because the eager bake lays a clip's content whole
    # before filtering, so `cycle` under `long` is (rightly) the dynamic
    # path's to play.
    finite = piece.replace("long 2 (cycle intro)", "long 2 intro")
    events = perform_voices(SYNTH, finite, RATE, seed=3)[1]
    assert [e[:2] for e in events] == [(0, 96), (96, 192),
                                       (192, 288), (288, 384)]


# ── Resume: the remainder from a tick ───────────────────────────────────────


def _stream_events(piece, seed, tick, horizon=100_000, synth=SYNTH):
    tempo, state, root, by_tag = stream_root(synth, piece, RATE, seed, tick)
    stream = ScoreStream(state, root, by_tag)
    out = []
    while not stream.done:
        got = stream.pull(horizon)
        out += got
        if not got and not stream.stalled:
            break
        assert not stream.stalled, "these fixtures must not stall"
    return out


def test_a_resume_is_the_suffix_of_the_same_take():
    """`resumeAt` rebased against the full take, draw for draw.

    Sown first, cut second: the third roll's velocity after the resume
    is the velocity it had in the uninterrupted performance, because
    the cut never moved its position in the tree — which is the whole
    point of seeds that ride structure instead of a walked generator.
    """
    full = _stream_events(CHANCY, seed=5, tick=0)
    resumed = _stream_events(CHANCY, seed=5, tick=192)
    want = [(on - 192, off - 192, bank, payload)
            for on, off, bank, payload in full if on >= 192]
    assert resumed == want and want, (resumed, want)


def test_a_resume_skips_instead_of_unfolding():
    """Bar 50 of an endless cycle, reached by arithmetic.

    The resumed stream's first events equal the full stream's at that
    region, rebased — same positions, same draws — while the resume
    side forced only its own neighbourhood, never the forty-nine bars
    it skipped.
    """
    piece = """
score : [: Void :]
score = cycle ((do s <- draw; '(Custom (random s) 60)) |* 2) >>= voices.lead

bpm : Int
bpm = 120
"""
    T = 100 * 96                                # beat 100: bar 50 of 2-beat bars
    full = [e for e in _stream_events(piece, seed=9, tick=0,
                                      horizon=T + 4 * 96) if e[0] >= T]
    tempo, state, root, by_tag = stream_root(SYNTH, piece, RATE, 9, T)
    stream = ScoreStream(state, root, by_tag)
    resumed = []
    for _ in range(200):            # a deep descent spans fuel rounds
        resumed += stream.pull(4 * 96)
        if resumed and not stream.stalled:
            break
    want = [(on - T, off - T, b, p) for on, off, b, p in full]
    assert resumed == want[:len(resumed)] and resumed, (resumed, want)


def test_a_rebuild_rejoins_in_seconds_not_minutes():
    """The measurement that motivated all of this: resuming an endless
    sown piece fifteen minutes in cost 157 seconds of left-to-right
    forcing (measured on `moods.ges`, a scratch piece that lived at the
    repo root); by declared widths it must be near-instant.  The
    fixture below reproduces that piece's shape — an endless `cycle` of
    sown two-beat bars, the right-nested `Seq` whose bar-`k` seed is
    `k` mix64s deep — so the claim no longer depends on a file the
    repository never owned.  Ten seconds is the loose ceiling for a
    slow machine; the observed figure is well under one.
    """
    import time

    from gestate.audioalloc import Allocator
    from gestate.audiovoices import banks_of, channels_of

    piece = """
score : [: Void :]
score = cycle ((do s <- draw; '(Custom (random s) 60)) |* 2
               ++ (do s <- draw; '(Custom (random s) 64)) |* 2) >>= voices.lead

bpm : Int
bpm = 96
"""
    source = SYNTH + piece
    RATE48 = 48000
    minutes = 15
    target = minutes * 60 * RATE48
    tick = (minutes * 60 * 96 * 96) // 60      # beats at 96 bpm, in ticks

    tempo, state, root, by_tag = stream_root(SYNTH, piece, RATE48, 7, tick)
    allocators = {b.name: Allocator(channels_of(source, b))
                  for b in banks_of(source)}
    lazy = LazyPerformer(ScoreStream(state, root, by_tag), tempo, RATE48,
                         allocators, block=64, origin=tick)
    # The clock starts *after* the compile: the claim under test is the
    # descent's cost, and a loaded machine's cold compiler was tripping
    # a ceiling the descent itself clears with room to spare.
    t0 = time.monotonic()
    for k in range(0, 400):         # housekeeping ticks; fuel rounds included
        lazy.advance(target + k * 64)
        if lazy.history:
            break
    took = time.monotonic() - t0
    assert lazy.history, "the resumed remainder should be sounding"
    assert took < 10.0, f"rejoin took {took:.1f}s"
