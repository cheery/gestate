"""`gestate/synth.ges` — the instrument builder's vocabulary.

Two obligations, and they are different in kind.

**The library has to say what it means.**  A filter is a claim about
frequencies and an envelope is a claim about time, and neither is checked by
the thing compiling.  So the tests below measure: a lowpass has to attenuate
a tone above its cutoff and pass one below it, resonance has to produce a
peak, and an ADSR has to reach its sustain and leave it.

**The library has to stay inside the fragment.**  Everything here is
prepended to every synth program, so a definition that cannot be extracted
is not a broken library function — it is a program that stops compiling for
somebody who never called it.  `spec/liveaudio.md` stage 1 is what says so,
and the examples are what exercise it.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from gestate.audio import DEFAULT_RATE, render
from gestate.audioengine import run
from gestate.audioextract import ExtractError, extract
from gestate.audiograph import check
from gestate.audioperform import graph_of, scored
from gestate.audiollvm import run_native

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

#: The examples built on the library.  All six are *scored*, so they are
#: read through `audioperform` rather than through `audio.render`.
LIB_EXAMPLES = ["polysine.ges", "fmpoly.ges", "polysaw.ges", "stereopad.ges",
                "quartet.ges", "gyre.ges"]

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")

#: Low and short.  A property of a filter is visible in a tenth of a second
#: and the interpreter is the slow way to get one.
RATE = 8000


def _render(body: str, seconds: float = 0.2, rate: int = RATE) -> list:
    """The samples, through the **graph engine** rather than the G-machine.

    Every test below measures a property of the *library* — that a lowpass
    attenuates, that an envelope reaches its sustain, that `dust` fires at
    its density.  Not one of them is a claim about the interpreter, and the
    interpreter is ten times the price: 2.8 ms a sample against 0.26 ms,
    measured on `pluck.ges`.  Sixty-odd renders at that rate were most of
    what this file spent, and the goldens — which is where the cost was
    looked for first — are a tenth of it.

    **The oracle is still checked, once instead of once per property.**
    `test_a_string_is_in_the_fragment_and_agrees_across_the_engines` and
    `test_the_new_effects_agree_across_all_three_engines` below call
    `render` by name and hold it to the graph bit-for-bit, and every
    example in `test_audiograph.py` does the same against the committed
    goldens.  Substituting here is only sound *because* those exist: if
    they are ever deleted, this helper becomes a measurement of the graph
    engine against itself.

    A program outside the static fragment has no graph and falls back to
    the interpreter rather than failing — `render` accepts strictly more
    than `extract` does, and a test that renders such a program is asking a
    fair question of the library.
    """
    try:
        graph = extract(body, rate=rate)
    except ExtractError:
        return render(body, seconds, rate)
    return run(graph, int(seconds * rate))


def _rms(xs) -> float:
    return (sum(x * x for x in xs) / len(xs)) ** 0.5 if xs else 0.0


# ── The library is in the fragment ──────────────────────────────────────────


def test_a_program_that_uses_nothing_still_compiles():
    """The whole library is prepended, so it is in *every* program's cost.

    A definition of it that did not typecheck would break a program that
    never mentioned it, which is the failure this asserts against.
    """
    assert len(_render("sound : Sig Float\nsound = map (n => 0.0) ticks\n",
                       4 / RATE)) == 4


@pytest.mark.parametrize("name", LIB_EXAMPLES)
def test_each_library_example_is_in_the_static_fragment(name):
    """A rejection here names the definition and why — see stage 1."""
    from gestate.audiograph import check_analysis
    from gestate.audioscore import assemble_performance
    from gestate.pipeline import analyse

    source = (AUDIO_DIR / name).read_text()
    # Through `assemble_performance`, not `check`: these carry a `score`, so
    # the program that actually runs has `music.ges` and the piece in it,
    # and checking a different assembly would be checking a different
    # program.
    report = check_analysis(analyse(assemble_performance(source, "", RATE)))
    assert report.errors == [], "\n".join(report.errors)


# ── Oscillators ─────────────────────────────────────────────────────────────


def test_a_sine_runs_at_the_frequency_it_is_asked_for():
    """Counted as zero crossings, which is what a frequency *is*."""
    hz, seconds = 500.0, 0.2
    xs = _render(f"sound : Sig Float\nsound = sine {hz}\n", seconds)
    crossings = sum(1 for i in range(len(xs) - 1)
                    if xs[i] <= 0.0 < xs[i + 1])
    assert abs(crossings - hz * seconds) <= 1


def test_a_pulse_narrower_than_a_half_spends_less_time_high():
    """`pulseOf 0.5` is a square; below that the duty cycle follows."""
    src = ("sound : Sig Float\n"
           "sound = map (p => pulseOf {w} p) (phase 200.0)\n")
    wide = _render(src.replace("{w}", "0.5"))
    narrow = _render(src.replace("{w}", "0.2"))
    high = lambda xs: sum(1 for x in xs if x > 0.0) / len(xs)
    assert high(wide) == pytest.approx(0.5, abs=0.02)
    assert high(narrow) == pytest.approx(0.2, abs=0.02)


def test_noise_is_noisy_and_reproducible():
    """A fold over a seed, so the same program renders the same noise."""
    once = _render("sound : Sig Float\nsound = white 12345\n", 0.05)
    twice = _render("sound : Sig Float\nsound = white 12345\n", 0.05)
    assert once == twice, "the same seed gave two different buffers"
    assert len(set(once)) > len(once) // 2, "not noise: too few distinct values"
    other = _render("sound : Sig Float\nsound = white 999\n", 0.05)
    assert other != once, "the seed does nothing"


# ── Envelopes ───────────────────────────────────────────────────────────────


def _env(expr: str, seconds: float = 0.5) -> list:
    """An envelope rendered as a signal, so it can be measured over time."""
    return _render(f"sound : Sig Float\nsound = map (n => {expr}) ticks\n",
                   seconds)


def test_an_adsr_rises_falls_to_its_sustain_and_holds_there():
    """The whole shape in one buffer: attack, decay, then flat."""
    # Held for the whole render — `off = 0` means "still down".
    xs = _env("adsrOf (Adsr 0.05 0.1 0.4 0.2) n 1 0", 0.5)
    peak_at = max(range(len(xs)), key=lambda i: xs[i])
    assert xs[0] == pytest.approx(0.0, abs=0.02), "did not start silent"
    assert max(xs) == pytest.approx(1.0, abs=0.02), "did not reach full"
    assert peak_at == pytest.approx(0.05 * RATE, abs=RATE * 0.01)
    tail = xs[int(0.35 * RATE):]
    assert _rms(tail) == pytest.approx(0.4, abs=0.02), "did not hold sustain"
    assert max(tail) - min(tail) < 1e-9, "the sustain is not flat"


def test_an_adsr_release_falls_from_wherever_the_note_had_reached():
    """Released during the *decay*, so the fall starts above the sustain.

    The level at release is recomputed rather than remembered, which is one
    less field in every voice — and this is what says the recomputation is
    right.
    """
    off = int(0.08 * RATE)
    xs = _env(f"adsrOf (Adsr 0.05 0.4 0.2 0.1) n 1 {off}", 0.4)
    at_release = xs[off]
    assert 0.2 < at_release < 1.0, "the test note did not release mid-decay"
    assert xs[off + int(0.05 * RATE)] < at_release, "it did not fall"
    assert xs[-1] == pytest.approx(0.0, abs=1e-6), "it did not reach silence"


def test_an_envelope_is_silent_before_its_note_and_for_a_note_that_never_came():
    """`on = 0` is a voice that has never played — what keeps a bank quiet."""
    assert max(_env("adsrOf (Adsr 0.01 0.1 0.5 0.1) n 0 0", 0.1)) == 0.0
    late = int(0.05 * RATE)
    xs = _env(f"adsrOf (Adsr 0.01 0.1 0.5 0.1) n {late} 0", 0.1)
    assert max(xs[:late - 1]) == 0.0, "sounded before its note"
    assert max(xs[late:]) > 0.5, "never sounded"


def test_a_zero_attack_is_a_step_rather_than_a_division_by_zero():
    """The case a percussive patch actually wants."""
    xs = _env("adsrOf (Adsr 0.0 0.2 0.5 0.1) n 1 0", 0.05)
    assert xs[0] == pytest.approx(1.0, abs=1e-9)


def test_a_percussive_envelope_decays_without_being_released():
    xs = _env("percOf 12.0 n 1", 0.4)
    assert xs[0] == pytest.approx(1.0, abs=0.01)
    assert xs[int(0.2 * RATE)] < 0.15
    assert all(xs[i + 1] <= xs[i] for i in range(len(xs) - 1)), "not monotone"


# ── Filters ─────────────────────────────────────────────────────────────────


def _through(filter_expr: str, hz: float, seconds: float = 0.25) -> float:
    """The RMS of a sine at `hz` after `filter_expr`, against its RMS before.

    A ratio rather than a level, so the measurement does not depend on the
    amplitude the oscillator happened to have.  The first fifth is dropped:
    a filter starts with empty integrators and its output is not yet what
    it will settle to.
    """
    src = (f"sound : Sig Float\nsound = {filter_expr} (sine {hz})\n")
    out = _render(src, seconds)
    plain = _render(f"sound : Sig Float\nsound = sine {hz}\n", seconds)
    skip = len(out) // 5
    return _rms(out[skip:]) / _rms(plain[skip:])


def test_the_svf_lowpass_passes_below_its_cutoff_and_stops_above_it():
    passed = _through("lowpassSvf 1000.0 0.0", 200.0)
    stopped = _through("lowpassSvf 1000.0 0.0", 3000.0)
    assert passed == pytest.approx(1.0, abs=0.15), f"passband {passed:.3f}"
    assert stopped < passed / 4, f"stopband {stopped:.3f} vs {passed:.3f}"


def test_the_svf_highpass_is_the_other_way_round():
    assert _through("highpassSvf 1000.0 0.0", 3000.0) > \
           4 * _through("highpassSvf 1000.0 0.0", 200.0)


def test_the_svf_bandpass_peaks_at_its_cutoff():
    at = _through("bandpassSvf 1000.0 0.5", 1000.0)
    assert at > _through("bandpassSvf 1000.0 0.5", 150.0)
    assert at > _through("bandpassSvf 1000.0 0.5", 3500.0)


def test_resonance_lifts_the_cutoff_and_is_what_the_knob_is_for():
    """Without this the resonance parameter could be ignored and pass.

    A tone *at* the cutoff comes out louder with the resonance up — that is
    the definition of a resonant filter, and it is the one property a
    plain one-pole cannot have.
    """
    flat = _through("lowpassSvf 1000.0 0.0", 1000.0)
    peaked = _through("lowpassSvf 1000.0 0.9", 1000.0)
    assert peaked > flat * 2.0, f"flat {flat:.3f}, resonant {peaked:.3f}"


def test_the_ladder_is_steeper_than_the_svf():
    """Four poles against two: an octave above the cutoff it takes more."""
    svf = _through("lowpassSvf 800.0 0.0", 3200.0)
    ladder = _through("lowpassLadder 800.0 0.0", 3200.0)
    assert ladder < svf, f"ladder {ladder:.3f} not below svf {svf:.3f}"


def test_a_filter_asked_for_an_impossible_cutoff_does_not_diverge():
    """A cutoff arrives from outside the synth, so it is clamped.

    `twoknobs.ges` is the long version of why: a host is free to send
    anything, and an unclamped `tan` at Nyquist is an infinity that reaches
    the speakers.
    """
    # A filter's cutoff is a `Sig Float`, and a *literal* is one already.
    # A `Float`-valued **expression** is not — `fromFloat` coerces literals
    # — so it is lifted with `!`, which is the same one-character lift
    # every voice already uses on its payload.  The graph is identical
    # either way: the constant folds out, so `!x` costs nothing.
    for cutoff in ("0.0", "1000000.0", "!(negate 500.0)"):
        xs = _render("sound : Sig Float\n"
                     f"sound = lowpassSvf ({cutoff}) 1.0 (saw 300.0)\n", 0.1)
        assert all(abs(x) < 100.0 for x in xs), f"diverged at cutoff {cutoff}"


def test_dc_block_removes_a_constant_offset():
    offset = _render("sound : Sig Float\n"
                     "sound = dcBlock (map (n => 0.5) ticks)\n", 0.5)
    assert abs(offset[-1]) < 0.02, f"offset survived: {offset[-1]:.4f}"


# ── Saturation ──────────────────────────────────────────────────────────────


def test_soft_clip_limits_without_folding_back():
    """Monotone all the way out, which is what separates it from `wrapFold`."""
    xs = _render("sound : Sig Float\n"
                 "sound = map (n => softClip (toFloat n / 400.0 - 5.0)) ticks\n",
                 0.4)
    assert all(xs[i + 1] >= xs[i] - 1e-12 for i in range(len(xs) - 1))
    assert max(abs(x) for x in xs) <= 0.6666666666666667 + 1e-12


def test_drive_keeps_a_quiet_signal_roughly_where_it_was():
    """A drive that halved the level would be a volume control."""
    quiet = _render("sound : Sig Float\nsound = gain 0.2 (sine 300.0)\n", 0.2)
    driven = _render("sound : Sig Float\n"
                     "sound = drive 0.0 (gain 0.2 (sine 300.0))\n", 0.2)
    assert _rms(driven) == pytest.approx(_rms(quiet) * 1.5, rel=0.15)


# ── Stereo ──────────────────────────────────────────────────────────────────


def test_an_equal_power_pan_holds_its_level_across_the_field():
    """The point of equal power: no dip in the middle."""
    from gestate.audio import render_frames

    levels = []
    for p in ("negate 1.0", "negate 0.5", "0.0", "0.5", "1.0"):
        frames = render_frames("sound : Sig Stereo\n"
                               f"sound = pan ({p}) (sine 300.0)\n",
                               0.2, RATE)
        left = _rms([f[0] for f in frames])
        right = _rms([f[1] for f in frames])
        levels.append((left * left + right * right) ** 0.5)
    assert max(levels) - min(levels) < 0.02 * max(levels)


def test_a_hard_pan_silences_the_other_side():
    from gestate.audio import render_frames

    frames = render_frames("sound : Sig Stereo\n"
                           "sound = pan (negate 1.0) (sine 300.0)\n",
                           0.1, RATE)
    assert _rms([f[0] for f in frames]) > 0.3
    assert _rms([f[1] for f in frames]) < 1e-9


# ── FM ──────────────────────────────────────────────────────────────────────


#: 250 Hz, and the number is load-bearing: it divides `RATE` exactly, so
#: one cycle is a whole 32 samples.  At 300 Hz a "period" is 26.67 samples,
#: the nearest integer is 2.5% out, and *every* patch measures as
#: aperiodic — which is a property of the measurement rather than of FM.
FM_HZ = 250.0


def _fm(patch: str, seconds: float = 0.2) -> list:
    """One FM voice with every operator wide open.

    Through `fm`, which is the whole of it now: the bank used to need a
    named step, a `scan` over `fmZero` and a `map` of `fmOut` back out,
    and all three are below `internal`.

    **The pitch and the levels are two signals.**  This built a `Sig Drive`
    until `Drive` went internal with the other step records — a `Drive` is
    what a `zip`'s step takes, the same as `SvfIn`, and `fm` pairs them
    itself now as `lowpassSvf` always has.
    """
    return _render(
        "openLevels : Sig Quad\n"
        "openLevels = map (n => Quad 1.0 1.0 1.0 1.0) ticks\n"
        f"\nsound : Sig Float\nsound = fm {patch} {FM_HZ} openLevels\n",
        seconds)


def _brightness(xs) -> float:
    """Mean absolute difference between neighbours — more is brighter.

    A crude spectral centroid, and enough for the claims here: FM adds
    sidebands *above* the carrier, so any measure that rises with high
    frequency content distinguishes the cases.
    """
    return sum(abs(xs[i + 1] - xs[i]) for i in range(len(xs) - 1)) / len(xs)


# ── FM as arithmetic ────────────────────────────────────────────────────────


def _brightness_of(body: str, seconds: float = 0.2) -> float:
    xs = _render(f"sound : Sig Float\nsound = {body}\n", seconds)
    return _brightness(xs)


def test_phase_modulation_is_a_map_and_an_addition():
    """`pm` is here for the name rather than for the work.

    `map sineOf (phase hz + mod)` was always legal — that is what removing
    the `Phase` newtype bought — and nothing said so.
    """
    named = _render("sound : Sig Float\nsound = pm 440.0 (1.0 * sine 880.0)\n",
                    0.1)
    spelled = _render("sound : Sig Float\n"
                      "sound = map sineOf (phase 440.0 + 1.0 * sine 880.0)\n",
                      0.1)
    assert named == spelled


def test_a_modulator_may_be_anything_the_library_produces():
    """The point of composing rather than packaging: an operator bank can
    only be modulated by its own operators."""
    for mod in ["1.2 * saw 110.0", "0.4 * pink (white 1)",
                "2.0 * pm 880.0 (1.5 * sine 1760.0)",
                "0.8 * lowpassSvf 300.0 0.6 (white 2)"]:
        xs = _render(f"sound : Sig Float\nsound = pm 440.0 ({mod})\n", 0.05)
        assert max(abs(x) for x in xs) > 0.0, mod


def test_depth_brightens_and_zero_depth_is_a_plain_sine():
    plain = _brightness_of("sine 250.0")
    assert _brightness_of("pm 250.0 (0.0 * sine 250.0)") == plain
    assert _brightness_of("pm 250.0 (1.0 * sine 250.0)") > 3 * plain


def test_self_feedback_is_a_sine_at_zero_and_a_saw_as_it_rises():
    """`pmSelf` is a *cycle* — the carrier reads its own output — so it is
    `feedback 1` with the sine inside the loop, which `pm` cannot express."""
    plain = _render("sound : Sig Float\nsound = sine 250.0\n", 0.2)
    assert _render("sound : Sig Float\nsound = pmSelf 250.0 0.0\n",
                   0.2) == plain, "zero feedback is not the identity"
    assert _brightness_of("pmSelf 250.0 0.5") > 4 * _brightness(plain)
    # …and it stays a sample rather than running away.
    xs = _render("sound : Sig Float\nsound = pmSelf 250.0 0.9\n", 0.2)
    assert max(abs(x) for x in xs) <= 1.0


def test_modulates_builds_the_matrix_the_literal_did():
    """`modulates` is a *writing* convenience and nothing else.

    The patch is a constant, so `audioextract._fold_constants` folds the
    whole construction away — which is what makes a readable spelling free
    rather than a trade.
    """
    built = _fm("(Patch (Quad 1.0 2.0 1.0 3.5) "
                "(modulates 4 3 0.4 (modulates 2 1 0.7 noWiring)) "
                "(Quad 0.6 0.0 0.4 0.0))")
    literal = _fm("(Patch (Quad 1.0 2.0 1.0 3.5) "
                  "(Matrix (Quad 0.0 0.7 0.0 0.0) (Quad 0.0 0.0 0.0 0.0) "
                  "(Quad 0.0 0.0 0.0 0.4) (Quad 0.0 0.0 0.0 0.0)) "
                  "(Quad 0.6 0.0 0.4 0.0))")
    assert built == literal
    # …and it is `fmBell`, which the library now writes the same way.
    assert built == _fm("fmBell")


def test_the_order_the_edges_are_written_in_does_not_matter():
    a = _fm("(Patch (Quad 1.0 1.0 1.0 1.0) "
            "(modulates 2 1 0.8 (modulates 3 2 0.5 noWiring)) "
            "(Quad 1.0 0.0 0.0 0.0))")
    b = _fm("(Patch (Quad 1.0 1.0 1.0 1.0) "
            "(modulates 3 2 0.5 (modulates 2 1 0.8 noWiring)) "
            "(Quad 1.0 0.0 0.0 0.0))")
    assert a == b


def test_the_bank_has_a_signal_level_face_like_everything_else():
    """`fm patch drive` — and the machinery it replaced is `internal`.

    The old shape passed the patch twice, to the step and to the output
    mix, so two *different* patches in the two places typechecked and made
    a sound belonging to neither.  One argument now.
    """
    from gestate.internals import InternalError
    hand = ("stepIt : Fm -> Int -> Fm\n"
            "stepIt st n = fmNext fmStack st (Drive 250.0 "
            "(Quad 1.0 1.0 1.0 1.0))\n"
            "\nsound : Sig Float\n"
            "sound = map (b => fmOut fmStack b) (scan stepIt fmZero ticks)\n")
    with pytest.raises(InternalError) as caught:
        _render(hand, 0.01)
    said = str(caught.value)
    for name in ("Fm", "fmNext", "fmOut", "fmZero"):
        assert name in said, name
    assert "reach for one of these instead: `fm`" in said


def test_an_unwired_bank_is_four_plain_sines():
    """No modulation is the identity: operator 1 alone is a sine."""
    xs = _fm("(Patch (Quad 1.0 1.0 1.0 1.0) noWiring "
             "(Quad 1.0 0.0 0.0 0.0))")
    plain = _render(f"sound : Sig Float\nsound = sine {FM_HZ}\n", 0.2)
    assert xs == pytest.approx(plain, abs=1e-12)


def test_modulation_adds_harmonics_above_the_carrier():
    quiet = _fm("(Patch (Quad 1.0 1.0 1.0 1.0) noWiring "
                "(Quad 1.0 0.0 0.0 0.0))")
    loud = _fm("fmStack")
    assert _brightness(loud) > 3 * _brightness(quiet)


def test_the_diagonal_is_feedback_and_nothing_else_is_needed_for_it():
    """One number on the diagonal turns a sine towards a sawtooth."""
    none = _fm("(Patch (Quad 1.0 1.0 1.0 1.0) noWiring "
               "(Quad 1.0 0.0 0.0 0.0))")
    fed = _fm("fmFeedback")
    assert _brightness(fed) > 1.5 * _brightness(none)
    assert max(abs(x) for x in fed) < 2.0, "feedback ran away"


def test_an_operators_level_is_what_an_envelope_moves():
    """A modulator at zero level modulates nothing, whatever the wiring."""
    open_ = _fm("fmStack")
    shut = _render(
        "shutLevels : Sig Quad\n"
        "shutLevels = map (n => Quad 1.0 0.0 0.0 0.0) ticks\n"
        f"\nsound : Sig Float\nsound = fm fmStack {FM_HZ} shutLevels\n",
        0.2)
    assert _brightness(shut) < _brightness(open_) / 3


def test_a_ratio_that_is_not_a_whole_number_is_inharmonic():
    """What makes `fmBell` a bell rather than a note.

    Measured as period: a harmonic sound repeats at the fundamental, an
    inharmonic one does not repeat at all within the buffer.
    """
    harmonic = _fm("fmStack", 0.2)
    bell = _fm("fmBell", 0.2)
    period = int(RATE / FM_HZ)

    def unlikeness(xs):
        """How much the wave differs from itself one fundamental later.

        Normalised by the signal's own level, because the two patches have
        different output amplitudes and a raw difference would be measuring
        loudness.  The first quarter is dropped: the feedback path is a
        sample behind, so a bank takes a few cycles to settle into whatever
        it is going to repeat.
        """
        xs = xs[len(xs) // 4:]
        later = _rms([xs[i + period] - xs[i] for i in range(len(xs) - period)])
        return later / _rms(xs)

    # Whole-number ratios repeat *exactly*: three stages of modulation at a
    # 1:1 ratio is still a waveform with the fundamental's period.
    assert unlikeness(harmonic) < 0.01
    assert unlikeness(bell) > 0.5


# ── The examples ────────────────────────────────────────────────────────────


@needs_clang
@pytest.mark.parametrize("name", LIB_EXAMPLES)
def test_each_library_example_plays_its_score(name):
    """Compiled, scheduled and run — and it has to make a sound.

    The one check a scored example can have without a golden: `duet.ges`'s
    problem is these examples' too, since what they play is decided by a
    schedule rather than by the program.  So this asserts the *properties* a
    golden would pin — in range, not silent, not a constant — with the notes
    actually supplied.
    """
    source = (AUDIO_DIR / name).read_text()
    rate, block = 8000, 256
    graph = graph_of(source, "", rate=rate)
    schedule, _samples, _allocs = scored(source, "", rate=rate, block=block)
    by_id = {n.id: n.chan for n in graph.control_sources()}

    def control(node, t):
        value = schedule.value_at(by_id.get(node), t)
        return 0 if value is None else value

    with tempfile.TemporaryDirectory() as d:
        frames = run_native(graph, d, int(1.5 * rate), block=block,
                            control=control)

    channels = graph.channels()
    flat = [x for f in frames
            for x in (f if channels > 1 else (f,))]
    assert max(abs(x) for x in flat) <= 1.05, "out of range"
    assert _rms(flat) > 0.01, "silent"
    assert len(set(round(x, 4) for x in flat)) > 100, "a constant"


def test_the_stereo_bank_really_carries_two_channels():
    """`voices pad 6 : Key -> Sig Stereo`, summed componentwise.

    The frame type comes from `synth.ges` rather than from the program,
    which is what the bank expander had to learn to look for.
    """
    source = (AUDIO_DIR / "stereopad.ges").read_text()
    graph = graph_of(source, "", rate=4000)
    assert graph.channels() == 2


# ── A voice as an expression ────────────────────────────────────────────────
#
# `spec/frp_lesson.md` set Fran beside this library: `stretch (abs wiggle)
# charlotte` is an expression over things that vary, and the same thought
# here had to be a state record, a `scan`, and three functions to take a
# note apart.  `sine`/`adsr`, a bank that hands its voice the
# timing and the payload *apart*, and `!` for the lift are what that
# thought needs to be written directly; `Num (Sig Float)` is what lets the
# parts be combined with `*` rather than with `zip`.
#
# The claim under test is not that the new spelling is nicer.  It is that
# it is **the same graph**: the tests below compare it, sample for sample,
# against the hand-written state machine it replaces.

PAYLOAD = """Key := Key Int Int

voices lead 2 voice : Sig Float

env : Adsr
env = Adsr 0.01 0.25 0.6 0.3

hzOfKey : Key -> Float
hzOfKey q = case q of
    Key k v -> keyHz k

velOfKey : Key -> Float
velOfKey q = case q of
    Key k v -> toFloat v / 127.0
"""

#: The voice as an expression — one line.
AS_EXPRESSION = PAYLOAD + """
voice : Sig Gate -> Sig Key -> Sig Float
voice g s = sine (!hzOfKey s) * adsr env g * !velOfKey s
"""

#: The same voice as every polyphonic example in this repository used to
#: write it: a state record for the phase and the instant, and the note
#: taken apart by hand at each use.
AS_A_STATE_MACHINE = PAYLOAD + """
Osc := Osc Float Int

stepVoice : Osc -> Both Gate Key -> Osc
stepVoice v nn = case v of
    Osc ph t -> case nn of
        Both w q -> case w of
            Gate on off -> Osc (wrap (ph + hzOfKey q / sampleRate)) (t + 1)

outVoice : Osc -> Both Gate Key -> Float
outVoice v nn = case v of
    Osc ph t -> case nn of
        Both w q -> case w of
            Gate on off -> sineOf ph * adsrOf env t on off
                         * velOfKey q

voice : Sig Gate -> Sig Key -> Sig Float
voice g s = voiceFolded (!Both g s)

voiceFolded : Sig (Both Gate Key) -> Sig Float
voiceFolded s = zip outVoice (scan stepVoice (Osc 0.0 0) s) s
"""

#: One note on the bank, so both are driven by the same schedule.
PIECE = """
bpm : Int
bpm = 96

score : [: Void :]
score = ('(Key 60 100) ++ '(Key 67 90)) >>= voices.lead

sound : Sig Float
sound = gain 0.5 lead
"""


# ── The resonator ───────────────────────────────────────────────────────────


IMPULSE = ("trig : Sig Float\ntrig = map impulse ticks\n"
           "impulse : Int -> Float\nimpulse n = case n == 5 of\n"
           "    True -> 1.0\n    False -> 0.0\n")


def _decay(xs, rate) -> float:
    """Seconds until the tail falls below a thousandth of the peak."""
    peak = max(abs(x) for x in xs)
    last = max((i for i, x in enumerate(xs) if abs(x) > peak / 1000.0),
               default=0)
    return last / rate


def test_the_svf_cannot_ring_long_and_that_is_why_resonate_exists():
    """**The measurement that produced `resonate`.**

    `svfK` floors its damping at 0.02 so the filter cannot oscillate on
    its own, and that floor caps the ring however hard resonance is
    pushed.  Half a second is a marimba bar; a tubular bell is 3 to 10,
    so a bell written on `bandpassSvf` sounds like a woodblock — which is
    how this was found.
    """
    rate = 4000
    xs = _render(IMPULSE + "sound : Sig Float\n"
                 "sound = bandpassSvf 220.0 1.0 trig\n", 1.5, rate)
    assert 0.3 < _decay(xs, rate) < 0.8


def test_resonate_rings_for_the_time_it_is_asked_to():
    """The decay is in **seconds to −60 dB**, which is how a struck object
    is described — so the number in the program is the number you hear."""
    rate = 4000
    for want in (0.1, 0.3, 1.0):
        xs = _render(IMPULSE + "sound : Sig Float\n"
                     f"sound = resonate 220.0 {want} trig\n",
                     want * 1.6 + 0.1, rate)
        got = _decay(xs, rate)
        assert got == pytest.approx(want, rel=0.25), f"{want} -> {got}"


def test_resonate_rings_at_the_frequency_it_is_asked_to():
    """Zero crossings, which is the cheapest honest pitch measurement."""
    rate = 8000
    for hz in (220.0, 440.0):
        xs = _render(IMPULSE + "sound : Sig Float\n"
                     f"sound = resonate {hz} 1.0 trig\n", 0.5, rate)
        crossings = sum(1 for i in range(1, len(xs))
                        if (xs[i - 1] < 0.0) != (xs[i] < 0.0))
        assert crossings / 2 / 0.5 == pytest.approx(hz, rel=0.05), hz


def test_resonate_peaks_near_one_so_a_modes_level_is_its_multiplier():
    """Normalised, so `0.7 * resonate …` is a mode at 0.7 and not at
    whatever the pole radius happened to make it."""
    for decay in (0.1, 1.0, 3.0):
        xs = _render(IMPULSE + "sound : Sig Float\n"
                     f"sound = resonate 220.0 {decay} trig\n", 0.3, 4000)
        assert 0.3 < max(abs(x) for x in xs) < 1.2, decay


# ── Noise: sparse, and coloured ─────────────────────────────────────────────


def test_dust_is_sparse_and_the_density_sets_how_sparse():
    """`dust d` fires about `d` times a second and is silent between."""
    for density in (200.0, 800.0):
        xs = _render(f"sound : Sig Float\nsound = dust 1 {density}\n", 0.5)
        fired = [x for x in xs if x != 0.0]
        # Poisson, so the tolerance is a few sigma at these counts.
        assert len(fired) == pytest.approx(density * 0.5, rel=0.25), density
        assert all(0.0 < x <= 1.0 for x in fired), "impulses are 0..1"
    # …and it is *not* white noise: almost every sample is exactly zero.
    xs = _render("sound : Sig Float\nsound = dust 1 200.0\n", 0.5)
    assert sum(1 for x in xs if x == 0.0) > 0.9 * len(xs)


def test_the_density_is_a_signal_and_may_move():
    """`dust : Sig Float -> Sig Float`, so the rate is a thing you sweep.

    Half a second at 5/s and half at 45/s comes out nearer the mean of the
    two than either — which a constant density could not do at all.
    """
    moving = _render("sound : Sig Float\n"
                     "sound = dust 1 (25.0 + 20.0 * sine 1.0)\n", 1.0)
    fired = sum(1 for x in moving if x != 0.0)
    assert fired == pytest.approx(25, rel=0.5), fired
    steady = sum(1 for x in _render("sound : Sig Float\nsound = dust 1 25.0\n",
                                    1.0) if x != 0.0)
    assert steady == pytest.approx(25, rel=0.5), steady


def test_the_four_colours_have_the_slopes_their_names_claim():
    """−3, −6, +3, +6 decibels per octave, measured off the spectrum.

    The names are a *claim about the spectrum*, and a filter that did not
    make it would be mis-sold rather than merely different — so this
    measures rather than checking that something changed.
    """
    import cmath
    import math

    rate, n = 16000, 1024

    def energy(xs, k0, k1):
        """Mean |DFT|² over bins `k0`..`k1`, averaged across the buffer.

        A hand-written DFT, because the suite has no numpy — so it is kept
        cheap deliberately: 1024-point windows, a band of bins rather than
        one (a single bin of a random process is far too noisy to assert
        on), and averaged over as many windows as the render gives.
        """
        total, windows = 0.0, 0
        for start in range(0, len(xs) - n + 1, n):
            chunk = xs[start:start + n]
            for k in range(k0, k1):
                acc = 0j
                w = -2j * math.pi * k / n
                for t, x in enumerate(chunk):
                    acc += x * cmath.exp(w * t)
                total += abs(acc) ** 2
            windows += 1
        return total / max(1, windows * (k1 - k0))

    def slope(expr):
        xs = _render(f"sound : Sig Float\nsound = {expr}\n", 0.25, rate)
        lo = energy(xs, int(500 * n / rate), int(1000 * n / rate))
        hi = energy(xs, int(1000 * n / rate), int(2000 * n / rate))
        return 10 * math.log10(hi / lo)

    for expr, want in [("white 1", 0.0), ("pink (white 1)", -3.0),
                       ("brown (white 1)", -6.0), ("blue (white 1)", 3.0),
                       ("violet (white 1)", 6.0)]:
        got = slope(expr)
        assert got == pytest.approx(want, abs=1.5), f"{expr}: {got:+.2f} dB/oct"


def test_the_colours_stay_at_a_usable_level():
    """Swapping `noise` for a colour must not be a volume jump."""
    for expr in ["white 1", "pink (white 1)", "brown (white 1)",
                 "blue (white 1)", "violet (white 1)"]:
        xs = _render(f"sound : Sig Float\nsound = {expr}\n", 0.3)
        assert 0.15 < _rms(xs) < 0.65, expr
        assert max(abs(x) for x in xs) <= 1.05, expr


def test_brown_is_the_same_colour_at_every_sample_rate():
    """The coefficient is a *frequency*, not a number picked at one rate.

    `brown` is `lowpassOnePole 20.0` scaled by √rate, so its slope and its
    level both survive a change of rate — which the hand-written leaky
    integrator it replaced did not.
    """
    levels = [_rms(_render("sound : Sig Float\nsound = brown (white 1)\n",
                           0.3, rate)) for rate in (8000, 16000, 32000)]
    assert max(levels) < 1.5 * min(levels), levels


# ── Dynamics ────────────────────────────────────────────────────────────────


def test_a_compressor_leaves_quiet_things_alone():
    for amp in (0.1, 0.25):
        xs = _render("sound : Sig Float\nsound = compress "
                     f"(Comp 0.3 4.0 0.005 0.15) ({amp} * sine 220.0)\n", 0.4)
        plain = _render(f"sound : Sig Float\nsound = {amp} * sine 220.0\n", 0.4)
        assert _rms(xs) == pytest.approx(_rms(plain), rel=0.02)


def test_a_compressor_turns_loud_things_down_by_the_ratio():
    """A 4:1 compressor over its threshold: the excess is quartered."""
    def peak(expr):
        xs = _render(f"sound : Sig Float\nsound = {expr}\n", 0.6)
        return max(abs(x) for x in xs[len(xs) // 3:])
    for amp in (0.6, 0.9):
        raw = peak(f"{amp} * sine 220.0")
        out = peak(f"compress (Comp 0.3 4.0 0.005 0.15) ({amp} * sine 220.0)")
        ideal = 0.3 + (raw - 0.3) / 4.0
        assert out < raw, "it did not compress"
        # Above the ideal by the ripple a peak detector always has, and
        # well below the input — see `limit`'s prose.
        assert ideal <= out < ideal * 1.25, (amp, raw, out, ideal)


def test_a_limiter_holds_a_ceiling_approximately_and_says_so():
    """The prose promises "approaches, does not guarantee"; this is that."""
    def peak(expr):
        xs = _render(f"sound : Sig Float\nsound = {expr}\n", 0.6)
        return max(abs(x) for x in xs[len(xs) // 3:])
    assert peak("limit 0.5 (0.4 * sine 220.0)") == pytest.approx(0.4, abs=1e-6)
    over = peak("limit 0.5 (5.0 * sine 220.0)")
    assert 0.5 < over < 0.65, over
    # …and `clip` after it is the hard bound the prose points at.
    assert peak("clip (limit 1.0 (5.0 * sine 220.0))") <= 1.0


def test_the_follower_tracks_between_zero_and_the_peak():
    xs = _render("sound : Sig Float\n"
                 "sound = follow 0.01 0.2 (0.8 * square 4.0)\n", 0.5)
    assert min(xs) >= 0.0
    assert max(xs) == pytest.approx(0.8, abs=0.02)


# ── `beat`, `clip` and `wrap` ───────────────────────────────────────────────


def test_clip_and_wrap_are_the_same_word_at_four_types():
    """`class Clip` and `class Wrap` — the convention says a plain verb is
    a transformation *at whatever type*, and these two had been at one."""
    for body in ["sound : Sig Float\nsound = clip (2.0 * sine 220.0)\n",
                 "sound : Sig Float\nsound = wrap (phase 110.0)\n",
                 "sound : Sig Stereo\n"
                 "sound = clip (widen (2.0 * sine 220.0))\n",
                 "sound : Sig Stereo\n"
                 "sound = wrap (pair (phase 110.0) (phase 55.0))\n"]:
        graph = graph_of(body, "", rate=8000)
        assert graph.nodes, body


def test_clip_at_a_frame_is_componentwise():
    """One channel over the limit does not move the other."""
    from gestate.pipeline import evaluate
    src = ((Path(__file__).resolve().parent.parent / "gestate"
            / "signal.ges").read_text() + "\n"
           + (Path(__file__).resolve().parent.parent / "gestate"
              / "audio.ges").read_text() + "\n"
           + (Path(__file__).resolve().parent.parent / "gestate"
              / "synth.ges").read_text()
           + "\nsampleRate : Float\nsampleRate = 8000.0\n"
           + "\nconstSig : a -> Sig a\nconstSig v = mapSig (n => v) ticks\n"
           + "\nmain : Float\nmain = monoOf (clip (Stereo 2.0 0.25))\n")
    # (1.0 + 0.25) / 2
    assert evaluate(src) == "0.625"


BEAT_PIECE = """
bpm : Int
bpm = 120

score : [: Void :]
score = '(Key 60 100) >>= voices.lead

sound : Sig Float
sound = beat
"""


@needs_clang
def test_beat_counts_the_piece_s_own_clock():
    """`beat : Sig Float` is generated where the tempo is — beside the
    entry point of a *scored* program, because `bpm` is the author's and a
    synth with no piece has none.

    At 120 bpm a beat is half a second, so at 8000 Hz sample 4000 is
    beat 1.0 and sample 6000 is beat 1.5.
    """
    samples = _perform(AS_EXPRESSION + BEAT_PIECE, samples=6001)
    assert abs(samples[0]) < 1e-9
    assert abs(samples[4000] - 1.0) < 1e-6
    assert abs(samples[6000] - 1.5) < 1e-6


def _perform(source: str, samples: int = 6000, rate: int = 8000,
             block: int = 256) -> list:
    """Compile, schedule and run — what `audioperform` does, as a list."""
    graph = graph_of(source, "", rate=rate)
    schedule, _samples, _allocs = scored(source, "", rate=rate, block=block)
    by_id = {n.id: n.chan for n in graph.control_sources()}

    def control(node, t):
        value = schedule.value_at(by_id.get(node), t)
        return 0 if value is None else value

    with tempfile.TemporaryDirectory() as directory:
        return run_native(graph, directory, samples, block=block,
                          control=control)


@needs_clang
def test_a_voice_written_as_an_expression_is_the_state_machine():
    """Bit-identical, through the engine, with the notes supplied.

    If `sine` folded its phase differently, if `adsr` read the
    instant from anywhere but `ticks`, or if `*` at `Sig Float` were
    anything but the `zip` its instance says it is, these would differ.
    """
    expression = _perform(AS_EXPRESSION + PIECE)
    assert expression == _perform(AS_A_STATE_MACHINE + PIECE)
    assert any(x != 0.0 for x in expression), "silent: nothing was compared"


def test_the_expression_voice_is_in_the_fragment():
    from gestate.audiograph import check_analysis
    from gestate.audioscore import assemble_performance
    from gestate.pipeline import analyse

    report = check_analysis(
        analyse(assemble_performance(AS_EXPRESSION + PIECE, "", RATE)))
    assert report.errors == [], "\n".join(report.errors)


def test_an_oscillator_that_follows_a_signal_is_the_one_that_does_not():
    """`sine (!hz)` is `sine hz`, sample for sample."""
    fixed = _render("sound : Sig Float\nsound = sine 440.0\n", 0.05)
    followed = _render("hz : Sig Float\nhz = !440.0\n"
                       "\nsound : Sig Float\nsound = sine hz\n", 0.05)
    assert fixed == followed
    assert max(fixed) == pytest.approx(1.0, abs=0.01)


# ── Gates — a note's timing without a note ──────────────────────────────────


def test_a_phase_comparison_is_a_metronome():
    """Lesson 3's `easy`: `perc` retriggered by `gateOn` of a `phase` ramp.

    The retrigger is the assertion that matters: the envelope must be
    *restored* at each period boundary, which is what no pure decay
    does.  The condition is true from the first sample, so the first
    press is the first sample — the gate plays from the program's
    start, exactly as the hand-drawn envelope beside it does.
    """
    xs = _render("env : Sig Float\n"
                 "env = perc 60.0 "
                 "(gateOn (!(x => x < 0.5) (phase 50.0)))\n"
                 "\nsound : Sig Float\nsound = sine 220.0 * env\n", 0.06)
    period = int(RATE / 50.0)
    tail = max(abs(x) for x in xs[period - 20:period])
    head = max(abs(x) for x in xs[period:period + 20])
    assert head > tail * 2, "no retrigger at the period boundary"


def test_a_gate_holds_and_releases():
    """The falling edge is a *release*: `adsr` must fall there.

    The condition is true for the first 60% of one long ramp, so with
    sustain 1.0 and a fast release the level right before the falling
    edge is the sustain and shortly after it is near zero — the two
    sides of `off` arriving.
    """
    xs = _render("env : Sig Float\n"
                 "env = adsr (Adsr 0.001 0.001 1.0 0.002) "
                 "(gateOn (!(x => x < 0.6) (phase 20.0)))\n"
                 "\nsound : Sig Float\nsound = env\n", 0.05)
    edge = int(0.6 * RATE / 20.0)
    assert xs[edge - 5] == pytest.approx(1.0, abs=0.05), "not sustaining"
    assert abs(xs[edge + int(0.004 * RATE)]) < 0.1, "no release at the edge"


def test_a_condition_is_a_note():
    """`gateOn` presses on the rising edge and releases on the falling.

    A 10 Hz LFO above 0.5 is high just under a third of each cycle, so
    with a fast attack and release the audible fraction must sit near
    it — silent-or-always-on is what edge detection gone wrong sounds
    like.
    """
    xs = _render("env : Sig Float\n"
                 "env = adsr (Adsr 0.001 0.001 1.0 0.001) "
                 "(gateOn (map (v => 0.5 < v) (sine 10.0)))\n"
                 "\nsound : Sig Float\nsound = env\n", 0.2)
    audible = sum(1 for x in xs if abs(x) > 0.5) / len(xs)
    assert 0.2 < audible < 0.45, audible


# ── `string` — the smallest physical model ──────────────────────────────────


#: A short burst of noise, which is what a pluck is.  Long enough to fill a
#: line at the pitches tested and short enough to be over before the second
#: round trip.
BURST = ("burst : Sig Float\n"
         "burst = zip (n w => early n w) ticks (white 3)\n"
         "\nearly : Int -> Float -> Float\n"
         "early n w = case n < 60 of\n"
         "    True -> 0.7 * w\n    False -> 0.0\n")


def _string(hz: float, seconds: float = 0.3, decay: float = 2.0) -> list:
    return _render(BURST + f"sound : Sig Float\n"
                           f"sound = string {hz} {decay} burst\n", seconds)


def test_a_string_rings_at_the_pitch_it_was_given():
    """The loop's length *is* the pitch, so this is a test of the arithmetic
    that turns one into the other — and of nothing else.

    The loop is the integer line, the averager's half sample and the
    tuning allpass's fraction, which together make the round trip
    `RATE / hz` — measured within a tenth of a cent over five octaves at
    48 kHz.  Autocorrelation quantises to whole lags, so the expectation
    here is the *nearest* one: it used to be `int(RATE / hz)`, the
    truncated line of the untuned string that rang 440 at 438.
    """
    for hz in (110.0, 220.0, 440.0):
        xs = _string(hz)[600:]
        best = max(range(4, 100),
                   key=lambda lag: sum(a * b for a, b in zip(xs, xs[lag:])))
        assert best == round(RATE / hz), f"{hz} Hz rang at a lag of {best}"


def test_a_string_decays_from_the_top_down():
    """Averaging two neighbouring samples is a lowpass, so the highest
    partials go first and the sound gets duller as it dies.  That is the
    difference between `string` and the `comb` it is built on."""
    xs = _string(440.0, 0.4)

    def brightness(w):
        return (sum(abs(b - a) for a, b in zip(w, w[1:]))
                / max(sum(abs(x) for x in w), 1e-12))

    early, late = xs[200:1000], xs[2000:2800]
    assert max(abs(x) for x in late) < max(abs(x) for x in early), "no decay"
    assert brightness(late) < brightness(early), "it died evenly, not dully"


def test_the_loop_gain_is_what_stops_the_offset_ringing_for_ever():
    """**The measurement that put a `decay` on `string`.**

    The averaging filter has gain 1 at zero frequency, so textbook
    Karplus-Strong circulates whatever DC the excitation carried and never
    loses it: measured at 880 Hz, the audible part was gone within a third
    of a second and a -0.137 offset stayed put.  Inaudible alone, it stacks
    across voices and eats headroom until it clips.
    """
    tail = _string(880.0, 1.0)[6000:6800]
    offset = sum(tail) / len(tail)
    assert abs(offset) < 0.02, f"a DC offset of {offset:+.4f} survived"


def test_the_decay_time_means_the_same_seconds_at_every_pitch():
    """The gain is applied once per round trip and there are `hz` of those
    a second, so the exponent divides by the length to undo it.  Without
    that the same number would mean eight different decays across three
    octaves, which is not what a parameter called `decay` can mean."""
    def tail_of(hz: float) -> float:
        xs = _string(hz, 1.0)[6000:6800]
        return _rms(xs)

    tails = [tail_of(hz) for hz in (110.0, 220.0, 440.0, 880.0)]
    assert min(tails) > 0.0, "one of them was silent"
    assert max(tails) / min(tails) < 5.0, tails


def test_a_longer_decay_rings_longer():
    assert _rms(_string(220.0, 1.0, decay=3.0)[6000:6800]) > \
        _rms(_string(220.0, 1.0, decay=0.4)[6000:6800])


def test_a_string_is_a_comb_that_got_a_filter():
    """Both are the same line at the same length; only the step differs, and
    the `comb` — with no loss in the loop beyond its feedback — keeps its
    high partials where the string loses them."""
    hz = 220.0
    strung = _string(hz, 0.4, decay=4.0)
    combed = _render(BURST + f"sound : Sig Float\n"
                             f"sound = comb {hz} 0.98 burst\n", 0.4)

    def brightness(w):
        return (sum(abs(b - a) for a, b in zip(w, w[1:]))
                / max(sum(abs(x) for x in w), 1e-12))

    tail = slice(2000, 2800)
    assert brightness(strung[tail]) < brightness(combed[tail])


def test_a_string_is_in_the_fragment_and_agrees_across_the_engines():
    source = BURST + "sound : Sig Float\nsound = string 220.0 2.0 burst\n"
    assert check(source, rate=RATE).errors == []
    graph = graph_of(source, "", rate=RATE)
    assert [n.kind for n in graph.nodes].count("loop") == 1
    # `render`, spelled out, and **not** `_render`: that helper runs the
    # graph now, so calling it here would compare the graph against itself
    # and this test — one of the two that keep the substitution honest —
    # would pass no matter how far the two engines had drifted apart.
    assert list(render(source, 0.1, RATE)) == list(run(graph,
                                                      int(0.1 * RATE)))


@pytest.mark.skipif(shutil.which("clang") is None, reason="no clang")
def test_the_generated_string_agrees_too():
    from gestate.audioengine import run

    source = BURST + "sound : Sig Float\nsound = string 220.0 2.0 burst\n"
    graph = graph_of(source, "", rate=RATE)
    n = int(0.1 * RATE)
    with tempfile.TemporaryDirectory() as directory:
        native = list(run_native(graph, directory, n, block=64))
    assert native == list(run(graph, n))


# ── What the delay lines are for ────────────────────────────────────────────
#
# `feedback`, `tap` and `loop` are three nodes; these are the effects built
# on them, and each test is of the *thing it claims to be* rather than of
# the arithmetic — an allpass that is not flat is not an allpass.


def _energy_at(xs, hz: float, rate: int = RATE) -> float:
    """The power at one frequency — a single-bin DFT, which is all these
    tests need and is cheaper than a whole spectrum."""
    import math

    n = len(xs)
    k = round(hz * n / rate)
    w = 2.0 * math.pi * k / n
    re = sum(x * math.cos(w * t) for t, x in enumerate(xs))
    im = sum(x * math.sin(w * t) for t, x in enumerate(xs))
    return (re * re + im * im) / (n * n)


def _brightness(xs) -> float:
    """How much of the signal is high frequency, near enough: the average
    step between neighbouring samples against the average level."""
    return (sum(abs(b - a) for a, b in zip(xs, xs[1:]))
            / max(sum(abs(x) for x in xs), 1e-12))


def test_an_allpass_passes_every_frequency_at_full_strength():
    """**The property it is named for.**  An allpass rearranges phase and
    changes no amplitude, which is what lets a reverb chain several of them
    without colouring anything — a filter that was not flat would tint the
    tail a little more with each one.
    """
    for hz in (110.0, 440.0, 1760.0):
        dry = _render(f"sound : Sig Float\nsound = sine {hz}\n", 0.2)
        wet = _render(f"sound : Sig Float\n"
                      f"sound = allpass 0.004 0.7 (sine {hz})\n", 0.2)
        # The first few milliseconds are the line filling; skip them.
        a, b = _rms(dry[400:]), _rms(wet[400:])
        assert b == pytest.approx(a, rel=0.08), f"{hz} Hz: {a:.4f} -> {b:.4f}"


def test_an_allpass_still_changes_the_sound():
    """Flat is not the same as doing nothing: an impulse comes out spread
    over the length of the line, which is the whole point."""
    xs = _render(IMPULSE + "sound : Sig Float\n"
                 "sound = allpass 0.004 0.7 trig\n", 0.1)
    spread = [x for x in xs[10:] if abs(x) > 0.01]
    assert len(spread) > 3, "it came out as an impulse, so it did nothing"


def test_a_damped_comb_loses_its_top_end_and_an_echo_does_not():
    """The difference `loop` bought: a filter *inside* the loop, so each
    repeat is duller than the last.  `echo` repeats unchanged for ever,
    which is why a reverb built on it sounds like a bucket."""
    bright = _render(IMPULSE + "sound : Sig Float\n"
                     "sound = echo 0.01 0.9 trig\n", 0.4)
    dull = _render(IMPULSE + "sound : Sig Float\n"
                   "sound = damped 0.01 0.9 0.6 trig\n", 0.4)
    tail = slice(1600, 2800)
    assert _rms(dull[tail]) > 0.0, "it died out entirely"
    assert _brightness(dull[tail]) < _brightness(bright[tail])


def test_damping_of_nothing_is_an_echo():
    """At `damp` 0 the loop filter is the identity, so this *is* `echo` —
    and being able to say so is the check that the filter is in the loop
    and not somewhere else."""
    plain = _render(IMPULSE + "sound : Sig Float\n"
                    "sound = echo 0.01 0.7 trig\n", 0.2)
    undamped = _render(IMPULSE + "sound : Sig Float\n"
                       "sound = damped 0.01 0.7 0.0 trig\n", 0.2)
    assert undamped == plain


def test_a_reverb_leaves_a_tail_and_a_longer_decay_leaves_a_longer_one():
    short = _render(IMPULSE + "sound : Sig Float\n"
                    "sound = reverb 0.3 0.4 trig\n", 0.8)
    long_ = _render(IMPULSE + "sound : Sig Float\n"
                    "sound = reverb 2.5 0.4 trig\n", 0.8)
    late = slice(4000, 5600)
    assert _rms(long_[late]) > 0.0, "even the long one was silent"
    assert _rms(long_[late]) > 3.0 * _rms(short[late])


def test_a_reverb_is_denser_than_the_comb_it_is_made_of():
    """Four lines with no common divisor, so the repeats interleave.  A
    single comb puts all its energy on one lag; the reverb should not."""
    rev = _render(IMPULSE + "sound : Sig Float\n"
                  "sound = reverb 1.5 0.3 trig\n", 0.5)[800:]
    one = _render(IMPULSE + "sound : Sig Float\n"
                  "sound = echo 0.0297 0.9 trig\n", 0.5)[800:]

    def peakiness(xs) -> float:
        """The strongest repeat against the average — how much one lag
        dominates."""
        lags = [abs(sum(a * b for a, b in zip(xs, xs[lag:])))
                for lag in range(40, 400)]
        return max(lags) / (sum(lags) / len(lags))

    assert peakiness(rev) < peakiness(one)


def test_a_flanger_moves_its_notches_and_a_fixed_delay_does_not():
    """What makes it a flanger rather than a feedforward comb: the same
    frequency is cancelled at one moment and not at another, which is the
    sweep being audible."""
    xs = _render("sound : Sig Float\nsound = flanger 2.0 1.0 (white 7)\n", 0.5)
    hz = 1500.0
    early = _energy_at(xs[400:1600], hz)
    later = _energy_at(xs[2000:3200], hz)
    assert max(early, later) > 4.0 * min(early, later), \
        f"the notch did not move: {early:.3e} vs {later:.3e}"


def test_a_chorus_delays_further_than_a_flanger():
    """The length is the whole difference between them — 25 ms against 5,
    which is heard as a second voice rather than as a filter."""
    from gestate.audioperform import graph_of

    def reach(name: str) -> int:
        source = f"sound : Sig Float\nsound = {name} 0.5 1.0 (white 7)\n"
        graph = graph_of(source, "", rate=RATE)
        return max(n.length for n in graph.nodes if n.kind == "tap")

    assert reach("chorus") > 3 * reach("flanger")


def test_brickwall_holds_a_ceiling_that_limit_only_approaches():
    """**The measurement `limit`'s own documentation asks for.**  A peak
    detector without lookahead is loosest exactly where the waveform is
    climbing again; delaying the signal by the attack time puts the gain
    down before the peak arrives."""
    loud = "sound : Sig Float\nsound = {} 0.5 (5.0 * sine 220.0)\n"
    chased = _render(loud.format("limit"), 0.4)[1600:]
    seen = _render(loud.format("brickwall"), 0.4)[1600:]
    assert max(abs(x) for x in seen) < max(abs(x) for x in chased)
    assert max(abs(x) for x in seen) < 0.52, "it did not hold the ceiling"


def test_the_new_effects_are_all_in_the_fragment():
    for body in ("allpass 0.01 0.6 (white 1)",
                 "damped 0.01 0.8 0.4 (white 1)",
                 "reverb 1.0 0.3 (white 1)",
                 "flanger 0.5 1.0 (white 1)",
                 "chorus 0.5 1.0 (white 1)",
                 "brickwall 0.5 (2.0 * white 1)"):
        source = f"sound : Sig Float\nsound = {body}\n"
        assert check(source, rate=RATE).errors == [], body


@pytest.mark.skipif(shutil.which("clang") is None, reason="no clang")
def test_the_new_effects_agree_across_all_three_engines():
    from gestate.audioengine import run
    from gestate.audioperform import graph_of

    for body in ("allpass 0.01 0.6 (white 1)",
                 "damped 0.01 0.8 0.4 (white 1)",
                 "reverb 1.0 0.3 (white 1)",
                 "flanger 0.5 1.0 (white 1)",
                 "brickwall 0.5 (2.0 * white 1)"):
        source = f"sound : Sig Float\nsound = {body}\n"
        graph = graph_of(source, "", rate=RATE)
        n = 800
        oracle = list(render(source, n / RATE, RATE))
        assert oracle == list(run(graph, n)), body
        with tempfile.TemporaryDirectory() as directory:
            assert oracle == list(run_native(graph, directory, n, block=64)), body


# ── `now` — the same name, the audio side (`fixme.md` F134) ────────────────


def test_now_is_the_sample_clock():
    """**`elapsed` under the name a reader expects.**  It is the same
    signal, exactly: a synth that reads one and a synth that reads the
    other are the same program, and this is what says so rather than a
    docstring claiming it."""
    a = list(render("sound : Sig Float\nsound = elapsed\n", 200 / RATE, RATE))
    b = list(render("sound : Sig Float\nsound = now\n", 200 / RATE, RATE))
    assert a == b
    assert b[0] == 0.0 and b[1] == 1.0 / RATE, "seconds, from zero"


def test_a_synth_with_its_own_now_keeps_it():
    """The renderer writes `now` after the author's text, where nothing
    shadows it — so it asks first.  See `audio.defines`."""
    source = ("now : Sig Float\nnow = !0.5\n\n"
              "sound : Sig Float\nsound = now\n")
    assert list(render(source, 3 / RATE, RATE)) == [0.5, 0.5, 0.5]
