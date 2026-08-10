"""`spec/dynamicscore.md` stage two — lazy layout, the score unfolding.

Stage one held a dynamic performance to the bake; this holds the
*unfolding* one to both of stage two's claims.  The parity claim: for
every score that ends, the lazy stream through `LazyPerformer` sounds
exactly what the bake baked — the stream is a second spelling of
where-a-note-is, and this is what keeps it honest.  The productivity
claim: `cycle` and `unfold` are ordinary values, an endless overlay
interleaves, forcing is bounded by the beat horizon, a stall is absence
with its beat on record, and a note that arrives after its beat is
dropped and said so.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from test_dynamicscore import BLOCK, PIECE, RATE, SYNTH, _allocators

from gestate.audiodynamic import LazyPerformer, ScoreStream
from gestate.audioschedule import Schedule
from gestate.audioscore import (duration_of_voices, perform_voices,
                                schedule_voices, stream_root)

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

#: Two endless voices at once — a loop and a generator — which is exactly
#: what the eager `layVoices` can never produce: its accumulator walk
#: needs the end of the piece, and there is none.
FOREVER = """
bar : [: Custom :]
bar = '(Custom 1.0 60) ++ '(Custom 0.8 64)

walk : Int -> ([: Custom :], Int)
walk k = ('(Custom 0.5 k), k + 1)

score : [: Void :]
score = (cycle bar >>= voices.lead) || (unfold 40 walk >>= voices.bass)

bpm : Int
bpm = 120
"""

BEAT = 2000                                 # samples per beat at 120 / 4000


def _lazy(synth, piece, *, fuel=None, horizon=4.0):
    tempo, state, root, by_tag = stream_root(synth, piece, RATE)
    stream = (ScoreStream(state, root, by_tag) if fuel is None
              else ScoreStream(state, root, by_tag, fuel=fuel))
    return LazyPerformer(stream, tempo, RATE, _allocators(), block=BLOCK,
                         horizon=horizon)


def _changes(performer, upto, start=0):
    out = []
    for t in range(start, upto + BLOCK, BLOCK):
        out += performer.advance(t)
    return out


# ── The parity claim ────────────────────────────────────────────────────────


def test_a_finite_score_streams_its_own_bake():
    """The stream is the bake, change for change, for a score that ends.

    The stage-one fixture again — chord, steal, two banks — so the
    allocator faces the same decisions through both spellings of
    where-a-note-is.
    """
    bpm, events = perform_voices(SYNTH, PIECE, RATE)
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    samples = duration_of_voices(events, bpm, RATE)

    lazy = _lazy(SYNTH, PIECE)
    performed = Schedule()
    for boundary, chan, value in _changes(lazy, samples):
        performed.change(boundary, chan, value)
    assert performed.changes == baked.changes
    assert lazy.transcript == []
    assert lazy.stream.done


@needs_clang
def test_a_finite_score_renders_identically_through_the_stream():
    from gestate.audioextract import extract_analysis
    from gestate.audiollvm import run_native
    from gestate.audioperform import Performance, from_performer
    from gestate.audioscore import assemble_performance
    from gestate.pipeline import analyse

    bpm, events = perform_voices(SYNTH, PIECE, RATE)
    samples = duration_of_voices(events, bpm, RATE)
    graph = extract_analysis(
        analyse(assemble_performance(SYNTH, PIECE, RATE)), rate=RATE)
    baked = schedule_voices(events, bpm, RATE, _allocators(), block=BLOCK)
    control = Performance(graph, [from_performer(_lazy(SYNTH, PIECE))]).control()

    with tempfile.TemporaryDirectory() as d:
        want = run_native(graph, d, samples, block=BLOCK,
                          control=baked.control_for(graph))
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, samples, block=BLOCK, control=control)
    assert got == want


# ── Forever is a value ──────────────────────────────────────────────────────


def test_two_endless_voices_interleave():
    """`cycle` beside `unfold`, both without end, both sounding.

    The generator's pitches march upward, which is also the determinism
    check: what `walk` computes is what plays.
    """
    lazy = _lazy(SYNTH, FOREVER)
    _changes(lazy, 8 * BEAT)
    assert not lazy.stream.done
    assert lazy.transcript == []
    banks = {e[2] for e in lazy.history}
    assert banks == {"lead", "bass"}
    pitches = [e[3][0][1] for e in lazy.history if e[2] == "bass"]
    assert pitches == list(range(40, 40 + len(pitches)))
    assert len(pitches) >= 8, "the generator fell behind the clock"


def test_forcing_is_bounded_by_the_horizon():
    """The performer is the demand, and it stops demanding.

    Eight beats played with a four-beat horizon must not force events
    much past beat twelve — an endless piece stays affordable because
    nothing asks for more of it than the near future.
    """
    lazy = _lazy(SYNTH, FOREVER)
    _changes(lazy, 8 * BEAT)
    furthest = max(e[0] for e in lazy.history)
    assert furthest <= (8 + 4 + 1) * 96, furthest


def test_an_unfolding_score_replays_exactly():
    """Two performances of the same text are the same performance."""
    a, b = _lazy(SYNTH, FOREVER), _lazy(SYNTH, FOREVER)
    assert _changes(a, 6 * BEAT) == _changes(b, 6 * BEAT)


# ── The stall rule ──────────────────────────────────────────────────────────


def test_a_stall_is_absence_never_corruption():
    """A retrograde of forever cannot be laid, and must not crash.

    `reverse (cycle intro)` needs the cycle's duration, which diverges;
    the budget blows, the stall lands in the transcript at the beat it
    happened, the two intro notes already emitted play out, and every
    later `advance` keeps returning quietly.
    """
    piece = """
intro : [: Custom :]
intro = '(Custom 1.0 60) ++ '(Custom 0.8 64)

score : [: Void :]
score = (intro ++ reverse (cycle intro)) >>= voices.lead

bpm : Int
bpm = 120
"""
    lazy = _lazy(SYNTH, piece, fuel=20_000)
    changes = _changes(lazy, 4 * BEAT)
    assert len(lazy.history) == 2, "the intro should have arrived"
    gates = {c for _b, c, v in changes if c.endswith("f0") and v != 0}
    assert len(gates) == 2, "both intro notes should sound"
    stalls = [entry for entry in lazy.transcript if entry[0] == "stall"]
    assert len(stalls) == 1, lazy.transcript
    assert lazy.advance(4 * BEAT + BLOCK) == []       # quietly, ever after


def test_a_late_note_is_dropped_and_said_so():
    """A note backdated beyond the horizon rejoins nothing.

    Its beat is long past by the time the walk reaches it, so it is
    dropped, named in the transcript, and the notes around it play as if
    it had never been written — the rejoin rule, not a pile-up.
    """
    piece = """
bar : [: Custom :]
bar = '(Custom 1.0 60) ++ '(Custom 0.9 62) ++ '(Custom 0.8 64) ++ '(Custom 0.7 65)

score : [: Void :]
score = (bar ++ bar ++ bar ++ at (0 - 1152) '(Custom 0.5 40)) >>= voices.lead

bpm : Int
bpm = 120
"""
    lazy = _lazy(SYNTH, piece, horizon=2.0)
    changes = _changes(lazy, 13 * BEAT)
    dropped = [entry for entry in lazy.transcript if entry[0] == "dropped"]
    assert len(dropped) == 1 and dropped[0][1] == 0.0, lazy.transcript
    assert len(lazy.history) == 13                    # twelve played, one seen
    pitches = {v for _b, c, v in changes if not c.endswith(("f0", "f1"))}
    assert 40 not in pitches and 40.0 not in pitches


# ── The transport, on a score with no end ───────────────────────────────────


def test_a_loop_on_an_endless_score_replays_its_bars():
    """Loop four bars of forever: the second pass is the first.

    What stage one proved for a finite score holds when the score never
    ends — the loop seam releases, replays from memoised history, and the
    generator is not run twice (`history` does not regrow).
    """
    lazy = _lazy(SYNTH, FOREVER)
    first = _changes(lazy, 4 * BEAT - BLOCK)
    seen = len(lazy.history)
    lazy.seek(0)
    second = _changes(lazy, 4 * BEAT - BLOCK)
    assert first and first == second
    assert len(lazy.history) == seen, "the seek re-ran the generator"


def test_a_seek_forward_into_forever_forces_to_the_target():
    """Bar 33 of an endless piece exists the moment somebody stands there."""
    lazy = _lazy(SYNTH, FOREVER)
    lazy.seek(32 * BEAT)
    changes = _changes(lazy, 34 * BEAT, start=32 * BEAT)
    assert changes, "nothing sounded at bar 33"
    onsets = {e[0] for e in lazy.history}
    assert any(o >= 32 * 96 for o in onsets)


# ── Routing: the bake must not be hung ──────────────────────────────────────


def test_a_straight_score_is_not_flagged():
    from gestate.audioscore import unfolding_names

    assert unfolding_names(SYNTH + "\n" + PIECE) == []


def test_the_bake_refuses_an_unfolding_score():
    """`perform_voices` walks to the end, and this score has none.

    Refused with the names to blame rather than hung — the halting
    problem is not solved here, only not gambled on.
    """
    from gestate.audioscore import ScoreError, perform_voices, unfolding_names

    assert unfolding_names(SYNTH + "\n" + FOREVER) == ["cycle", "unfold"]
    with pytest.raises(ScoreError, match="unfolds"):
        perform_voices(SYNTH, FOREVER, RATE)


def test_an_authors_own_recursion_is_flagged_and_still_plays():
    """A recursive score that *does* end: flagged, routed, and correct.

    The scan cannot know `go 3` ends, so the bake refuses it — and the
    price of that ignorance is nothing but the route taken: the dynamic
    path plays its three notes and finds the end itself.
    """
    from gestate.audioscore import ScoreError, perform_voices, unfolding_names

    piece = """
go : Int -> [: Custom :]
go n = case n of
    0 -> r
    _ -> '(Custom 1.0 (60 + n)) ++ go (n - 1)

score : [: Void :]
score = go 3 >>= voices.lead

bpm : Int
bpm = 120
"""
    assert unfolding_names(SYNTH + "\n" + piece) == ["go"]
    with pytest.raises(ScoreError, match="unfolds"):
        perform_voices(SYNTH, piece, RATE)

    lazy = _lazy(SYNTH, piece)
    changes = _changes(lazy, 6 * BEAT)
    ons = [v for _b, c, v in changes if c.endswith("f0") and v != 0]
    assert len(ons) == 3, "three notes, then the rest"
    assert lazy.stream.done, "the end exists and was found"
