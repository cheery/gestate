"""`gestate/tempo.py` — tempo that varies, and stays invertible.

The one property everything else rests on is that `beat_at` and `time_at`
are the *same* answer read in two directions.  A schedule is built with
`time_at` and a playhead is drawn with `beat_at`, so a piece whose two
directions disagreed would put a note somewhere the ruler does not say it
is — and the disagreement would be invisible until somebody looked at both
at once.
"""

from __future__ import annotations

import pytest

from gestate.midi import TICKS_PER_BEAT
from gestate.tempo import TempoError, constant, envelope, value_on


# ── The two directions agree ────────────────────────────────────────────────


@pytest.mark.parametrize("points", [
    [(0.0, False, 120.0)],
    [(0.0, False, 60.0), (8.0, True, 120.0)],
    [(0.0, False, 90.0), (4.0, False, 140.0), (12.0, True, 70.0)],
    [(0.0, False, 100.0), (2.0, True, 200.0), (6.0, True, 50.0),
     (10.0, False, 120.0)],
])
@pytest.mark.parametrize("beat", [0.0, 0.5, 1.0, 3.25, 7.9, 8.0, 11.5, 20.0])
def test_time_and_beat_invert_each_other(points, beat):
    """`beat_at(time_at(b)) == b`, which is what "invertible" means here.

    Exact to floating point rather than approximately: `time_at` is the
    quadratic formula applied to the quadratic `beat_at` evaluates, not a
    search or a table, so there is no error term to allow for.
    """
    env = envelope(points)
    assert env.beat_at(env.time_at(beat)) == pytest.approx(beat, abs=1e-9)


def test_a_constant_tempo_is_beats_per_minute_and_nothing_else():
    env = constant(120)
    assert env.beat_at(0.0) == 0.0
    assert env.beat_at(1.0) == 2.0
    assert env.beat_at(30.0) == 60.0
    assert env.time_at(60.0) == 30.0


# ── The ramp is a trapezoid, not an approximation of one ────────────────────


def test_a_ramp_takes_the_time_the_average_tempo_would():
    """60 to 120 bpm over eight beats.

    A linear ramp covers its beats in the time its *mean* tempo would —
    `dt = 120·db/(y₀+y₁)` — which is what integrating the ramp gives
    exactly.  Getting this wrong is the classic tempo bug: using the start
    tempo makes every accelerando late and every ritardando early, and it
    stays plausible enough to ship.
    """
    env = envelope([(0.0, False, 60.0), (8.0, True, 120.0)])
    assert env.time_at(8.0) == pytest.approx(120 * 8 / (60 + 120))


def test_the_ramp_arrives_at_exactly_the_tempo_it_was_given():
    """Continuity: the segment's slope has to land on the next point.

    A ramp that overshot or undershot would make every following segment
    start from the wrong tempo, and the error would accumulate down the
    piece rather than staying local.
    """
    env = envelope([(0.0, False, 60.0), (8.0, True, 120.0)])
    at_end = env.bpms[0] + env.ks[0] * (env.ts[1] - env.ts[0])
    assert at_end == pytest.approx(120.0)


def test_a_step_holds_the_old_tempo_right_up_to_the_point():
    """`ramp=False` means "hold, then step", and holding is the whole of it.

    Eight beats at 60 bpm is eight seconds whatever comes next, so the
    tempo written at beat 8 must not bend the approach to it.
    """
    stepped = envelope([(0.0, False, 60.0), (8.0, False, 240.0)])
    assert stepped.time_at(8.0) == pytest.approx(8.0)
    # …and the new tempo applies immediately after.
    assert stepped.time_at(12.0) == pytest.approx(8.0 + 60 * 4 / 240)


def test_the_last_tempo_continues_for_ever():
    """Past the final point there is no next tempo to ramp to."""
    env = envelope([(0.0, False, 60.0), (8.0, True, 120.0)])
    beyond = env.time_at(16.0) - env.time_at(8.0)
    assert beyond == pytest.approx(60 * 8 / 120)


def test_a_piece_that_does_not_start_at_beat_zero_still_starts_at_time_zero():
    """The tempo before the first point is the first tempo, held.

    Without the inserted segment `time_at` of anything before the first
    point would read off the end of the lists — and a piece whose first
    tempo mark is at bar 2 is an ordinary thing to write.
    """
    env = envelope([(4.0, False, 60.0), (8.0, True, 120.0)])
    assert env.time_at(0.0) == pytest.approx(0.0)
    assert env.time_at(4.0) == pytest.approx(4.0)


# ── The constant path is the *old* path, exactly ────────────────────────────


@pytest.mark.parametrize("bpm", [1, 60, 96, 120, 128, 140, 240])
@pytest.mark.parametrize("rate", [8000, 22050, 44100])
def test_a_constant_tempo_lands_notes_where_the_integer_formula_did(bpm, rate):
    """**Bit-identical, and it has to be.**

    Every committed schedule in the tree was built with `tick * 60 * rate
    // (bpm * 96)`.  The bit-identity tests between the interpreter, the
    block engine and the generated code compare a rendered *performance*,
    so a note moved by one sample is a failed test — and a real fault, not
    a tolerance: an offline render and a live one would disagree about a
    rhythm.

    So a constant tempo must not go anywhere near `sqrt`.  This is the
    assertion that says so.
    """
    env = constant(bpm)
    for tick in (0, 1, 47, 96, 97, 1000, 12345, 96 * 400):
        assert env.samples_of(tick, rate) == (
            tick * 60 * rate // (bpm * TICKS_PER_BEAT))


def test_an_envelope_of_one_repeated_tempo_is_the_constant_path():
    """A piece writing its unchanging tempo as an envelope pays nothing.

    Otherwise "I wrote it the other way" would silently move every note in
    the piece by a sample, which is exactly the class of difference nobody
    would go looking for.
    """
    assert not envelope([(0.0, False, 120.0)]).varies
    assert not envelope([(0.0, False, 120.0), (8.0, False, 120.0)]).varies
    assert envelope([(0.0, False, 120.0)]).samples_of(96, 44100) == \
        constant(120).samples_of(96, 44100)


def test_a_varying_tempo_says_that_it_varies():
    assert envelope([(0.0, False, 60.0), (8.0, True, 120.0)]).varies


def test_notes_come_out_in_order_under_a_ramp():
    """Monotonicity — the property a schedule builder assumes silently.

    `time_at` is a square root, and a sign error in the quadratic formula
    gives a curve that runs backwards over part of its range.  The result
    is not an obviously wrong number, it is a piece whose notes are
    subtly out of order in one bar.
    """
    env = envelope([(0.0, False, 40.0), (16.0, True, 200.0)])
    ticks = list(range(0, 16 * TICKS_PER_BEAT + 1, 7))
    samples = [env.samples_of(t, 44100) for t in ticks]
    assert samples == sorted(samples)


# ── What it refuses ─────────────────────────────────────────────────────────


def test_a_tempo_of_zero_or_less_is_refused():
    """Not merely invalid: a tempo of zero divides by zero in `time_at`,
    and a negative one runs the piece backwards."""
    with pytest.raises(TempoError):
        constant(0)
    with pytest.raises(TempoError):
        envelope([(0.0, False, 120.0), (4.0, True, 0.0)])
    with pytest.raises(TempoError):
        envelope([(0.0, False, -60.0)])


def test_points_out_of_beat_order_are_refused():
    """`bisect` assumes sorted, and would otherwise pick a wrong segment
    rather than fail — a wrong answer instead of an error."""
    with pytest.raises(TempoError):
        envelope([(8.0, False, 120.0), (4.0, False, 60.0)])


def test_an_empty_envelope_is_refused():
    with pytest.raises(TempoError):
        envelope([])


def test_a_sample_rate_of_zero_is_refused():
    with pytest.raises(TempoError):
        constant(120).samples_of(96, 0)


# ── `on` — envelopes read as plain curves ───────────────────────────────────


ENV = [(0.0, False, 0.0), (4.0, True, 1.0), (8.0, False, 0.25),
       (12.0, True, 0.75)]


def test_on_clamps_at_both_ends_rather_than_refusing():
    """**Total, and that is the point.**

    Its argument is nearly always a clock — a beat, an age, a position —
    and a clock will run past the end of any envelope written for it.
    Raising there would put a `clamp` that says nothing at every use site;
    extrapolating would send a cutoff to infinity ten seconds after the
    note ended.
    """
    assert value_on(ENV, -100.0) == 0.0
    assert value_on(ENV, 0.0) == 0.0
    assert value_on(ENV, 12.0) == 0.75
    assert value_on(ENV, 1e9) == 0.75


def test_a_ramp_interpolates_from_the_point_before_it():
    assert value_on(ENV, 2.0) == pytest.approx(0.5)
    assert value_on(ENV, 4.0) == pytest.approx(1.0)
    assert value_on(ENV, 10.0) == pytest.approx(0.5)


def test_an_at_holds_the_previous_value_and_steps():
    """`At` is a hold: the value written at 8 does not bend the approach.

    Between 4 and 8 the envelope reads 1.0 throughout — the `At 8 0.25`
    says what happens *at* 8, not how to get there.
    """
    assert value_on(ENV, 5.0) == 1.0
    assert value_on(ENV, 7.9) == 1.0
    assert value_on(ENV, 8.0) == 0.25


def test_one_point_is_a_constant():
    for x in (-5.0, 0.0, 5.0):
        assert value_on([(3.0, False, 0.4)], x) == 0.4


def test_two_points_at_the_same_place_land_on_the_later_one():
    """A vertical step is legal, must not divide by zero, and **the later
    point wins** — a jump lands on its top, which is what writing two
    points at one instant is for.

    Stated here because it is the one case where the rule is a choice
    rather than a consequence, and because `envexpand`'s compiled tree has
    to make the same one: it did not, at first, and the disagreement showed
    up only against this reading.
    """
    assert value_on([(0.0, False, 0.0), (0.0, True, 1.0)], 0.0) == 1.0
    assert value_on([(0.0, False, 0.0), (0.0, True, 1.0)], 1.0) == 1.0
    assert value_on([(0.0, False, 0.0), (0.0, True, 1.0)], -1.0) == 0.0


def test_an_empty_envelope_is_refused_where_it_is_read():
    with pytest.raises(TempoError):
        value_on([], 0.0)


# ── A piece writing its tempo as an envelope ────────────────────────────────


PIECE = """
Key := Key Int Int

voices lead 2 sineVoice : Sig Float

env : Adsr
env = Adsr 0.01 0.2 0.6 0.2

hzOfKey : Key -> Float
hzOfKey (Key k v) = keyHz k

sineVoice : Sig Gate -> Sig Key -> Sig Float
sineVoice g s = sine (!hzOfKey s) * adsr env g

tune : [: Key :]
tune = '(Key 60 100) ++ '(Key 62 100) ++ '(Key 64 100) ++ '(Key 65 100)

score : [: Void :]
score = tune >>= voices.lead

sound : Sig Float
sound = gain 0.4 lead
"""

FLAT = "bpm : Int\nbpm = 120\n" + PIECE
AS_ENVELOPE = "tempo : List Tempo\ntempo = [Step 0.0 120.0]\n" + PIECE
SLOWING = ("tempo : List Tempo\n"
           "tempo = [Step 0.0 120.0, Ramp 4.0 60.0]\n" + PIECE)

SCORE_RATE = 8000


def _onsets(source):
    from gestate.audioscore import perform_voices, samples_of

    tempo, events = perform_voices(source, "", rate=SCORE_RATE)
    return sorted({samples_of(on, tempo, SCORE_RATE) for on, *_ in events})


def test_a_flat_envelope_places_notes_exactly_where_a_plain_bpm_does():
    """**The compatibility claim, at the level a listener would notice.**

    Not the unit assertion in `samples_of` but the whole path — entry
    point, heap read, envelope build, schedule — so that "I wrote the tempo
    the other way" cannot move a single note.
    """
    assert _onsets(AS_ENVELOPE) == _onsets(FLAT)


def test_a_ritardando_spaces_the_notes_further_apart_as_it_goes():
    """A tempo that halves over four beats, heard as gaps that grow.

    Asserted as *monotonically increasing gaps* rather than against
    particular sample numbers: what a ritardando is is that each beat takes
    longer than the last, and pinning the arithmetic would be pinning the
    trapezoid twice.
    """
    gaps = [b - a for a, b in zip(_onsets(SLOWING), _onsets(SLOWING)[1:])]
    assert gaps == sorted(gaps) and gaps[0] < gaps[-1], gaps
    # …and it is slower than the flat piece it started at the same tempo as.
    assert _onsets(SLOWING)[-1] > _onsets(FLAT)[-1]


def test_declaring_both_a_bpm_and_a_tempo_is_refused_by_name():
    """Two answers to how fast a piece goes is not a question this can
    settle, and letting one win silently is how a piece plays at a tempo
    nothing in the file states."""
    from gestate.audioscore import ScoreError

    with pytest.raises(ScoreError, match="both a `bpm` and a `tempo`"):
        _onsets("bpm : Int\nbpm = 96\n" + AS_ENVELOPE)


def test_asking_for_beat_under_an_envelope_says_why_it_is_not_there():
    """A piecewise tempo makes the beat clock piecewise *quadratic*, and
    reading it needs a segment search the static fragment refuses.

    Answered by name rather than as `Unknown global 'beat'` from a prelude
    the author never wrote — the difference between a restriction and a
    mystery.
    """
    from gestate.audioscore import ScoreError

    using = SLOWING.replace("sound = gain 0.4 lead",
                            "sound = gain 0.4 lead * (0.5 + beat * 0.0)")
    with pytest.raises(ScoreError, match="piecewise quadratic"):
        _onsets(using)


def test_a_step_and_a_ramp_are_different_pieces():
    """The flag is the whole difference, so it had better be audible."""
    stepped = ("tempo : List Tempo\n"
               "tempo = [Step 0.0 120.0, Step 4.0 60.0]\n" + PIECE)
    assert _onsets(stepped) != _onsets(SLOWING)
    # A step holds 120 right up to beat 4, so its first notes are the
    # flat piece's; the ramp is already slowing by then.
    assert _onsets(stepped)[1] == _onsets(FLAT)[1]
    assert _onsets(SLOWING)[1] > _onsets(FLAT)[1]
