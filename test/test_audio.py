"""The audio backend — `fixme.md` F87.

`render(source, seconds, rate)` is the whole thing as far as correctness
goes: it steps the signal once per sample and hands back the numbers.  No
file, no audio device, and — like `midi.perform` and `gui.scenes` — nothing
outside gestate, so this file runs anywhere.

Sizes here are small on purpose.  A second of sound is several seconds of
work, and that is the point of the design rather than a defect: this renders
*offline*, and the tests only have to establish that a synth means what it
says.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest

from gestate.audio import (AudioError, golden_text, parse_golden, render,
                           render_frames, write)

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
EXAMPLE = AUDIO_DIR / "blip.ges"
DRUMS = AUDIO_DIR / "drums.ges"

#: Every synth in `examples/audio/`.
EXAMPLES = ["sine.ges", "blip.ges", "drums.ges", "knob.ges", "fm.ges",
            "pluck.ges", "twoknobs.ges", "duet.ges", "stereo.ges",
            "polysine.ges", "fmpoly.ges", "polysaw.ges", "stereopad.ges",
            "quartet.ges", "substrate.ges", "pachelbel.ges", "bell.ges",
            "bar.ges", "membrane.ges",
            # **Three pieces rather than three synths**, and the only
            # entries here with a `sound` and no golden.  They are minutes
            # long, and a golden is re-rendered through the *interpreter*
            # twice per run — the modal examples cost the suite forty-five
            # minutes at two seconds each before they were cut to half a
            # second, and these are three minutes each.
            #
            # Nothing is lost by it.  What they exercise — `string`,
            # `loop`, `damped`, `reverb`, `chorus`, `brickwall` — is
            # covered sample-for-sample against the oracle in
            # `test_delayline.py` and `test_synthlib.py`, where a failure
            # names the combinator rather than the tune; and
            # `test_examples.py` compiles all three every run.  A golden of
            # a composition would be a slow, brittle oracle for things
            # already tested precisely.
            "strings.ges", "strings2.ges", "lead.ges",
            # Three more pieces, for the same reason — and the two `slide`
            # showcases would be the *worst* goldens in the file: the
            # slide oracle walks its whole ring per sample, so a minute of
            # it through the interpreter is the forty-five-minute mistake
            # again.  `test_delayline.py` checks the node itself
            # sample-for-sample against all three engines.
            "gyre.ges", "bottleneck.ges", "flutter.ges",
            # A canvas rather than a synth, so no golden for the reason
            # `substrate.ges` has none: what it *shows* is the point, and a
            # buffer of the sound it makes would not check that.
            "spectrum.ges", "envelope.ges",
            # A soundscape: no score, no notes, no keyboard — every input
            # moved by an `Envelope` read against `elapsed`.  No golden for
            # the reason the pieces have none: ninety seconds re-rendered
            # through the interpreter twice a run, for a thing whose
            # combinators are already checked sample-for-sample elsewhere.
            "scenery.ges",
            # A joke with a `slide` in it — the dubgate with a portamento
            # violin over the top.  A piece, so no golden, same as the
            # others; what it exercises (`gateOn`, `slew`, `slide`, the
            # signal-resonance filters) is each tested by name elsewhere,
            # and `test_examples.py` compiles it every run.
            "violin.ges",
            # The Float-knob showcase for the CLAP export — a drone whose
            # two dials are the interface.  A drone, so no golden; the
            # knobs themselves are exercised by `test_export.py`.
            "warmdrone.ges",
            # The tempo showcase: a drum machine whose every envelope is
            # arithmetic on `beat`, so the DAW's transport conducts it.
            # A groove, so no golden; the host clock is exercised by
            # `test_export.py`'s beat parity.
            "fourfloor.ges",
            # The stereo showcase: a pluck alternating ears on the beat,
            # a detuned bed, a crossing swoosh.  A piece, so no golden;
            # the two-channel port is exercised by `test_export.py`'s
            # stereo parity.
            "pingpong.ges",
            # Two endless, seeded pieces (`cycle` + `sown`), so they are
            # the dynamic path's to play and a golden is impossible by
            # construction — a bake would refuse them by name
            # (`unfolding_names`).  What they exercise is pinned in
            # `test_sownscore.py` and `test_lazyscore.py`, and the
            # rejoin-cost measurement carries a fixture of `moods.ges`'s
            # own shape.
            "moods.ges", "nightdrive.ges",
            # The two listeners: hold keys on one bank, the line comes
            # out another — chancy and deterministic respectively.  A
            # probe piece with no hands is honest silence, so a golden
            # would be a buffer of nothing; the listening semantics are
            # pinned in `test_probescore.py`, keyboard to line, end to
            # end.
            "arpeggiator.ges", "ladder.ges",
            # The trio that waits: a listening piece is honest silence
            # without hands, so a golden would be a buffer of nothing.
            # `test_probescore.py` holds its `FromMIDI` instance, and
            # the listening semantics are pinned there end to end.
            "jazz.ges",
            # **All three halves at once** — an unfolding seeded score, a
            # compiled synth, and a canvas.  No golden for both of the
            # reasons above at the same time: the score is `cycle` +
            # `draw`, so a bake refuses it by name, and what the canvas
            # *shows* is the point, which a buffer of the sound would not
            # check.  The picture is pinned instead where a picture can
            # be — `shell/panel/tests/substrate_parity.rs` walks this
            # file's own `substrate` and compares it with what `gui.py`
            # draws, captions included.
            "lantern.ges"]

#: The ones with committed golden buffers — all of them, now.  `knob.ges`
#: had none for as long as the interpreter and the engine disagreed about
#: what a control tick *is* (`spec/liveaudio.md` open question 3): a golden
#: would have frozen one of the two answers.  An instant is a set of
#: arrivals since, a block boundary is one instant on both clocks, and the
#: two agree — so the control-rate example has an oracle like the others,
#: and its header carries the block schedule it was rendered at.
#: The **scored** examples have none, and for a reason rather than an
#: omission: what they play is decided by a *schedule* and a keyboard, so a
#: golden of one with neither would be a golden of silent voices.
#: `test_audionotes.py` renders `duet.ges` bit-identically against the
#: oracle *with* a schedule, which is the same check with the notes
#: supplied; `test_synthlib.py` checks the other four the same way.
GOLDEN = ["sine.ges", "blip.ges", "drums.ges", "knob.ges", "fm.ges",
          "pluck.ges", "twoknobs.ges", "stereo.ges",
          # The three modal examples.  Rendered at 6 kHz rather than the
          # 1-2 kHz the older ones use, because a bell's top partial is at
          # 1965 Hz and a golden below its Nyquist would be an oracle for
          # aliasing rather than for the bell.
          #
          # **Half a second, not two.**  Made at two seconds first — 12,000
          # samples against the 600-1,200 every other golden holds — and
          # each is re-rendered twice by the tests below, through the
          # *interpreter*.  That one decision took the suite from fourteen
          # minutes to over an hour.  A golden is an oracle, not a
          # recording: it has to be long enough to contain the sound and no
          # longer.
          "bell.ges", "bar.ges", "membrane.ges"]

#: Low and short: enough samples to see shape, few enough to be quick.
RATE = 4000
SECONDS = 0.12


def _source() -> str:
    return EXAMPLE.read_text()


# ── The example ─────────────────────────────────────────────────────────────


def test_it_renders_the_right_number_of_samples():
    assert len(render(_source(), SECONDS, RATE)) == int(SECONDS * RATE)


def test_the_samples_are_in_range():
    samples = render(_source(), SECONDS, RATE)
    assert all(-1.0 <= s <= 1.0 for s in samples)
    assert max(abs(s) for s in samples) > 0.05, "silent"


def test_it_is_not_a_constant():
    """An oscillator that never moved would still be "in range"."""
    samples = render(_source(), SECONDS, RATE)
    assert len(set(round(s, 4) for s in samples)) > 20


def test_the_envelope_decays_across_a_note():
    """Loud at the attack, quiet by the end — the cubic decay.

    Measured as peak amplitude in the first and last quarter of one note,
    which is what an envelope *is* independent of the waveform under it.
    """
    rate, speed = 4000, 4
    per_note = rate // speed
    samples = render(_source(), per_note / rate, rate)
    quarter = per_note // 4
    early = max(abs(s) for s in samples[:quarter])
    late = max(abs(s) for s in samples[-quarter:])
    assert late < early / 2, f"attack {early:.3f}, tail {late:.3f}"


def test_the_phase_is_continuous_across_a_note_change():
    """Accumulated, not computed from `n`.

    `wrap (p + f/rate)` carries the phase over a frequency change; `n*f/rate`
    would jump and click.  A click is a large single-sample step, so the
    largest difference between neighbouring samples stays modest.
    """
    rate = 4000
    samples = render(_source(), 0.3, rate)         # spans a note boundary
    jumps = [abs(samples[i + 1] - samples[i]) for i in range(len(samples) - 1)]
    assert max(jumps) < 0.5, f"largest step {max(jumps):.3f}"


def test_the_filter_smooths_it():
    """`lowpass` is a signal transformation, so it must change the signal.

    Compared against the same program with the filter opened right up.
    """
    filtered = render(_source(), SECONDS, RATE)
    opened = render(_source().replace("lowpass 0.25 raw", "lowpass 1.0 raw"),
                    SECONDS, RATE)
    rough = lambda xs: sum(abs(xs[i + 1] - xs[i]) for i in range(len(xs) - 1))
    assert rough(filtered) < rough(opened)


# ── The backend ─────────────────────────────────────────────────────────────


def test_zero_seconds_renders_nothing():
    assert render(_source(), 0.0, RATE) == []


def test_the_sample_rate_is_the_renderers_business():
    """The same program at two rates: more samples, same length of sound."""
    a = render(_source(), SECONDS, 4000)
    b = render(_source(), SECONDS, 8000)
    assert len(b) == 2 * len(a)


def test_a_synth_that_never_reads_ticks_is_rejected():
    """It has no clock, so it cannot advance — say so rather than hang."""
    with pytest.raises(AudioError, match="no clock|never reads"):
        render("sound : Sig Float\nsound = 0.0 ::: never\n", SECONDS, RATE)


def test_a_sound_that_is_not_a_signal_is_rejected():
    from gestate.unify import UnifyError

    with pytest.raises((AudioError, UnifyError)):
        render("sound : Float\nsound = 0.5\n", SECONDS, RATE)


def test_write_produces_a_playable_wav(tmp_path):
    path = tmp_path / "out.wav"
    n, peak = write(_source(), str(path), SECONDS, RATE)
    with wave.open(str(path)) as f:
        assert f.getnchannels() == 1
        assert f.getsampwidth() == 2
        assert f.getframerate() == RATE
        assert f.getnframes() == n
        frames = f.readframes(n)
    values = struct.unpack(f"<{n}h", frames)
    assert max(abs(v) for v in values) == pytest.approx(peak * 32767, rel=0.01)


#: A frame type and two constants — the smallest program that is not mono.
STEREO = ("Stereo := Stereo Float Float\n"
          "\nframeOf : Float -> Float -> Stereo\nframeOf l r = Stereo l r\n"
          "\nsound : Sig Stereo\n"
          "sound = zip frameOf (map (n => 0.25) ticks)"
          " (map (n => negate 0.5) ticks)\n")


def test_a_record_of_floats_renders_one_frame_per_instant():
    """The channel count is the program's, read off the value."""
    frames = render_frames(STEREO, SECONDS, RATE)
    assert len(frames) == int(SECONDS * RATE)
    assert set(frames) == {(0.25, -0.5)}


def test_render_refuses_a_multichannel_sound_by_name():
    """`render` is the mono view, and says so rather than losing a channel."""
    with pytest.raises(AudioError, match="2 channels.*render_frames"):
        render(STEREO, SECONDS, RATE)


def test_a_mono_program_still_renders_one_float_per_instant():
    """`render_frames` did not change what `render` means."""
    assert render_frames(_source(), SECONDS, RATE) == [
        (s,) for s in render(_source(), SECONDS, RATE)]


def test_write_produces_a_stereo_wav(tmp_path):
    """Two channels, interleaved left then right — field order, as written."""
    path = tmp_path / "out.wav"
    n, peak = write(STEREO, str(path), SECONDS, RATE)
    with wave.open(str(path)) as f:
        assert f.getnchannels() == 2
        assert f.getnframes() == n == int(SECONDS * RATE)
        values = struct.unpack(f"<{2 * n}h", f.readframes(n))
    assert values[0::2] == tuple([int(0.25 * 32767)] * n)
    assert values[1::2] == tuple([int(-0.5 * 32767)] * n)
    assert peak == 0.5


def test_a_frame_whose_fields_are_not_numbers_is_rejected():
    """A record of `Float`s and nothing else — say which field, and why."""
    bad = ("Mixed := Mixed Float Int\n"
           "\nframeOf : Float -> Int -> Mixed\nframeOf a b = Mixed a b\n"
           "\nsound : Sig Mixed\n"
           "sound = zip frameOf (map (n => 0.25) ticks) ticks\n")
    with pytest.raises(AudioError, match="field 1"):
        render_frames(bad, SECONDS, RATE)


def test_samples_are_clamped_not_normalised(tmp_path):
    """A synth that goes over 1.0 should sound like it did."""
    loud = "sound : Sig Float\nsound = gain 4.0 (map (n => 1.0) ticks)\n"
    path = tmp_path / "loud.wav"
    write(loud, str(path), SECONDS, RATE)
    with wave.open(str(path)) as f:
        values = struct.unpack(f"<{f.getnframes()}h", f.readframes(f.getnframes()))
    assert max(values) == 32767


# ── The building blocks in `audio.ges` ──────────────────────────────────────


def _first(src: str) -> float:
    return render(src, 4 / RATE, RATE)[3]


def test_the_oscillator_shapes():
    from gestate.pipeline import evaluate

    def at(fn, p):
        return evaluate(f"main : Float\nmain = {fn} {p}\n")

    # Read them out of the prelude files directly, with a stub `sampleRate`.
    # `signal.ges` too: `audio.ges`'s `lowpass` is built on its `scan`.
    root = Path(__file__).resolve().parent.parent / "gestate"
    src = ((root / "signal.ges").read_text() + "\n"
           + (root / "audio.ges").read_text())
    prog = src + "\nsampleRate : Float\nsampleRate = 100.0\n"
    for expr, want in [("sawOf 0.0", "-1.0"), ("sawOf 1.0", "1.0"),
                       ("squareOf 0.25", "1.0"), ("squareOf 0.75", "-1.0"),
                       ("triangleOf 0.5", "1.0"), ("triangleOf 0.0", "-1.0"),
                       ("wrap 2.75", "0.75"), ("clip 3.0", "1.0"),
                       ("seconds 1.0", "100")]:
        got = evaluate(prog + f"\nmain : Float\nmain = {expr}\n"
                       if want.endswith(".0") or "." in want
                       else prog + f"\nmain : Int\nmain = {expr}\n")
        assert got == want, f"{expr} gave {got}"


# ── `drums.ges` — three voices and a noise source ───────────────────────────


def test_every_audio_example_is_exercised_here():
    assert {p.name for p in AUDIO_DIR.glob("*.ges")} == set(EXAMPLES)


def _steps(rate=3000, bars=1.0):
    """The peak of each sixteenth of a bar."""
    tempo = 96
    per = int(rate * 15 / tempo)
    samples = render(DRUMS.read_text(), 16 * per * bars / rate, rate)
    return [max((abs(x) for x in samples[i * per:(i + 1) * per]), default=0.0)
            for i in range(int(16 * bars))]


def test_the_pattern_is_where_it_says():
    peaks = _steps(bars=0.5)
    loud = [i for i, p in enumerate(peaks) if p > 0.05]
    quiet = [i for i, p in enumerate(peaks) if p < 0.001]
    # Kicks on 0 and 6, snare on 4, hats on the evens — so every even
    # sixteenth sounds and every odd one is silent.
    assert loud == [0, 2, 4, 6], loud
    assert quiet == [1, 3, 5, 7], quiet


def test_the_kick_is_louder_than_the_hat():
    peaks = _steps(bars=0.25)
    assert peaks[0] > peaks[2] * 2, peaks[:3]


def test_the_noise_is_reproducible():
    """It is a fold over a seed, not a random source: same file every time."""
    a = render(DRUMS.read_text(), 0.05, 3000)
    b = render(DRUMS.read_text(), 0.05, 3000)
    assert a == b


def test_the_noise_is_actually_noisy():
    """A snare that repeated every few samples would be a tone."""
    rate, tempo = 3000, 96
    per = int(rate * 15 / tempo)
    samples = render(DRUMS.read_text(), 5 * per / rate, rate)
    snare = samples[4 * per:4 * per + per // 4]
    assert len(set(round(s, 4) for s in snare)) > len(snare) // 2


def test_it_stays_in_range():
    samples = render(DRUMS.read_text(), 0.15, 3000)
    assert all(-1.0 <= s <= 1.0 for s in samples)


# ── The golden buffers — `spec/liveaudio.md` stage 7.0 ──────────────────────
#
# Everything above asserts a *property* of the sound: in range, decaying,
# noisy, on the beat.  Those are what tell you a synth means what it says,
# and none of them pins the numbers.
#
# Stage 7 needs the numbers.  `render()` stops being the product and becomes
# the oracle: graph extraction, block rendering and generated code are each
# verified by rendering the same program both ways and comparing samples, so
# a committed buffer is what those comparisons are against.  Without it
# stages 7.2–7.4 have nothing to be wrong against.


def _golden(name: str) -> tuple[dict[str, str], list[float]]:
    path = (AUDIO_DIR / name).with_suffix(".samples")
    assert path.exists(), (
        f"{path.name} has not been rendered — "
        f"`python -m gestate.audio examples/audio/{name} --golden`")
    return parse_golden(path.read_text())


@pytest.mark.golden
@pytest.mark.parametrize("name", GOLDEN)
def test_the_committed_samples_are_what_renders_today(name):
    """Exact equality, sample for sample.

    Exact rather than approximate on purpose, and it is legitimate here for
    a stated reason: a gestate synth is `+ - * /` on doubles and integer
    arithmetic, all of which are correctly rounded, so the render is
    reproducible bit for bit rather than merely closely.

    **This docstring used to predict that `sin`/`exp` arriving would force
    it into a tolerance argument, and that prediction was half wrong.**
    They have arrived — `fm.ges` and `pluck.ges` are built on them — and
    the comparison is still exact *on one machine*, because the question
    was never accuracy but **identity**: the interpreter's `math.sin` and
    the generated code's `llvm.sin.f64` reach the same libm.
    `test_transcendental.py` measures that rather than assuming it.

    **On another machine it is not a claim anybody can check**, and that
    was found by moving the suite: `pluck.ges`, the only golden built on
    `exp`, differed in 3 samples of 1200 by 2.22e-16 — one place in the
    last — between two machines *reporting the same glibc*.  Same version,
    different dispatch.  So the header carries a `libm_fingerprint`, which
    asks the functions themselves rather than trusting a version string,
    and a golden that differs **and** was made under a different one is
    **skipped** rather than failed.

    The skip is narrow on purpose.  It needs all three of: the samples
    differ, the fingerprint differs, and every difference is within a few
    places in the last — so a real regression on a new machine still fails,
    and a golden from *this* machine is compared exactly as before.

    The settings come out of the file's own header, so re-rendering cannot
    quietly use a different rate than the numbers were made at.
    """
    header, want = _golden(name)
    rate, seconds = int(header["rate"]), float(header["seconds"])
    control = int(header["control_every"]) if "control_every" in header else None
    # `channels` in the header picks the reader: a mono golden is a list of
    # floats and `render` hands back exactly that, a multi-channel one is a
    # list of frames and `render_frames` does.  Comparing either against the
    # wrong one would compare a float with a tuple and fail loudly, which is
    # the failure mode to want here.
    read = render if int(header.get("channels", 1)) == 1 else render_frames
    got = read((AUDIO_DIR / name).read_text(), seconds, rate,
               control_every=control)

    assert len(want) == int(header["samples"]) == int(seconds * rate)
    assert len(got) == len(want)
    if got != want:
        i, (a, b) = next((i, p) for i, p in enumerate(zip(got, want))
                         if p[0] != p[1])
        _skip_if_another_machines_libm(name, header, got, want)
        pytest.fail(
            f"{name} first differs at sample {i} of {len(want)}: "
            f"rendered {a!r}, committed {b!r}.  If that is meant, "
            f"`python -m gestate.audio examples/audio/{name} --golden`")


#: How far apart two renders may be and still be called *the same numbers
#: through a different libm*: four places in the last, relative.  `sin`,
#: `cos`, `exp` and `log` are within an ulp or so in every implementation
#: anyone ships, and a feedback path can carry one a little further; a
#: changed evaluator moves a sample by vastly more than this.
_LIBM_SLACK = 4 * 2.220446049250313e-16


def _skip_if_another_machines_libm(name, header, got, want) -> None:
    """Skip — *yellow*, not green — when the difference is only the machine.

    Three conditions, and all of them are needed.  Without the fingerprint
    check a genuine regression here would be excused anywhere; without the
    magnitude check the fingerprint would excuse any regression made on a
    new machine; and without doing this only *after* the samples differ, a
    golden that still matches would be skipped instead of passing, which
    would quietly stop testing on every machine but one.
    """
    from gestate.audio import libm_fingerprint

    made_under = header.get("libm")
    here = libm_fingerprint()
    if made_under is None or made_under == here:
        return

    def flat(xs):
        return [v for x in xs for v in (x if isinstance(x, tuple) else (x,))]

    worst = max(abs(a - b) / max(abs(b), 1e-9)
                for a, b in zip(flat(got), flat(want)) if a != b)
    if worst > _LIBM_SLACK:
        return
    pytest.skip(
        f"{name}'s golden was made where libm is {made_under} and this is "
        f"{here}; {sum(1 for a, b in zip(flat(got), flat(want)) if a != b)} "
        f"of {len(flat(want))} samples differ by at most {worst:.3g} "
        f"relative, which is the last place or two.  Exactness is a claim "
        f"about one machine.  `python -m gestate.audio "
        f"examples/audio/{name} --golden` makes this the machine of record."
    )


@pytest.mark.golden
@pytest.mark.parametrize("name", GOLDEN)
def test_the_golden_window_is_not_just_silence(name):
    """A golden of the first ten samples would pass every test above.

    Each window was chosen to *contain* the thing its example is about, and
    a shorter one regenerated by accident would lose that quietly.  So the
    window is checked for what it is supposed to hold.
    """
    header, samples = _golden(name)
    rate = int(header["rate"])
    flat = [x for s in samples for x in (s if isinstance(s, tuple) else (s,))]
    assert max(abs(x) for x in flat) > 0.05, "silent"

    if name == "sine.ges":
        # The whole envelope, which is the only thing this example is: it
        # starts before the note, it is loud at `onAt`, and it has fallen
        # to silence a release after `offAt`.  A window that stopped at the
        # sustain would show a tone and pin nothing.
        on, off, release = rate // 10, rate // 2, int(0.4 * rate)
        assert len(samples) > off + release, "the window stops before the end"
        assert max(abs(s) for s in samples[:on - 1]) == 0.0, "sounding early"
        assert max(abs(s) for s in samples[on:off]) > 0.05, "no note"
        assert max(abs(s) for s in samples[off + release:]) == 0.0, \
            "the release does not reach silence"
    elif name == "blip.ges":
        # `speed` is 4 notes a second, so more than a quarter-second of
        # samples means the window crosses a note change — the phase
        # continuity the example exists to demonstrate.
        assert len(samples) > rate // 4, "one note only: no note change"
    elif name == "fm.ges":
        # Three notes a second, so half a second crosses a boundary — and
        # what this example is *about* is the index envelope, which makes
        # the start of a note spectrally unlike its end.
        assert len(samples) > rate // 3, "one note only: no note change"
    elif name == "pluck.ges":
        # Two notes a second.  The decay is the point, so the window has to
        # contain enough of one note to show it falling away.
        assert len(samples) > rate // 2, "the window stops inside one note"
        head = max(abs(s) for s in samples[:rate // 8])
        tail = max(abs(s) for s in samples[rate // 2 - rate // 8:rate // 2])
        assert tail < head / 2, "the note does not decay across the window"
    elif name == "twoknobs.ges":
        # The oracle drives every control channel with the sample index, so
        # both knobs sweep and then clamp at 100.  The window has to hold
        # enough boundaries for that sweep to be audible — a golden taken
        # after both had pinned would be a steady tone, and would pass
        # while testing nothing about having two of them.
        every = int(header["control_every"])
        assert len(samples) > 3 * every, "too short to hold a knob change"
        before = samples[:every]
        after = samples[2 * every:3 * every]
        assert before != after, "the knobs change nothing across a boundary"
    elif name == "knob.ges":
        # What this example is *for* is the control clock, so a window that
        # did not cross a boundary would pin nothing the other two do not.
        every = int(header["control_every"])
        assert len(samples) > 4 * every, "too short to hold a control tick"
        # And the knob has to be doing something: the oracle feeds the
        # sample index as the control value, so the pitch climbs and the
        # second half of the window cannot repeat the first.
        half = len(samples) // 2
        assert samples[:half] != samples[half:2 * half], "the knob does nothing"
    elif name == "stereo.ges":
        # The one example whose golden is frames rather than floats, so the
        # shape is asserted first: a mono render of it would be the failure
        # this file exists to catch, and it would be *in range* and *not a
        # constant* like everything else.
        assert all(isinstance(s, tuple) and len(s) == 2 for s in samples)
        assert samples[0][0] == samples[0][1], "the two do not start in phase"
        # 440 against 442 is two hertz, so the channels are in opposition a
        # quarter of a second in.  A window that stopped before that would
        # show them agreeing to three decimals and pin nothing.
        assert len(samples) > rate // 4, "too short for the channels to part"
        assert max(abs(l - r) for l, r in samples) > 1.0, "the channels agree"
    elif name in ("bell.ges", "bar.ges", "membrane.ges"):
        # **Struck, and then ringing** — which is what modal synthesis is,
        # and what `resonate` gives that `bandpassSvf` could not.  The
        # window has to hold both halves: one that caught only the attack
        # would pin a click, and one that caught only the tail would pin a
        # tone that nothing hit.
        quiet = next(i for i, s in enumerate(samples) if abs(s) > 0.02)
        assert quiet > 0, "it is already sounding at the first sample"
        peak = max(range(len(samples)), key=lambda i: abs(samples[i]))
        assert peak < len(samples) - rate // 20, "the strike is at the end"
        after = samples[peak + rate // 20:]
        assert max(abs(s) for s in after) > 0.02, "it does not ring"
    elif name == "drums.ges":
        # Five sixteenths at 96bpm: kick, silence, hat, silence, snare.  The
        # snare is the noise fold, which is the thing `drums.ges` is for.
        per = rate * 15 // 96
        assert len(samples) > 4 * per, "the window stops before the snare"
        step = lambda i: samples[i * per:(i + 1) * per]
        assert max(abs(s) for s in step(4)) > 0.05, "no snare in the window"
        # Silent to the ear, and not exactly zero: `lowpass` multiplies its
        # state by `1 - k` every sample, so a gate that shuts leaves a
        # geometric tail that approaches zero without arriving.  It matters
        # more than it looks — see `spec/liveaudio.md` stage 4.
        assert max(abs(s) for s in step(1)) < 1e-9, "step 1 should be silent"
    else:
        # **Named rather than fallen into.**  This chain used to end in the
        # `drums.ges` branch as its `else`, so three examples added to
        # `GOLDEN` were silently asked to contain a kick, a hat and a snare
        # at sixteenths of 96 bpm.  A golden without a claim about what its
        # window holds is a golden that pins only its own length.
        raise AssertionError(
            f"{name} is in GOLDEN with nothing said about what its window "
            f"is supposed to contain — add a branch above")


def test_a_golden_buffer_round_trips_exactly():
    """The format has to be lossless, or the comparison above means nothing.

    `repr` of a double is the shortest text that reads back as the same
    double; these are the values that catch a format which is merely
    close — a long decimal, a denormal, the smallest step near 1.0.
    """
    values = [0.0, -0.0, 1.0, 0.1, 1 / 3, 5e-324, 1.0 + 2 ** -52,
              -0.9999999999999999, 2.220446049250313e-16]
    header, back = parse_golden(
        golden_text(values, name="x.ges", rate=8, seconds=0.5))
    assert back == values
    assert [repr(v) for v in back] == [repr(v) for v in values]  # -0.0 too
    assert header["rate"] == "8" and header["samples"] == str(len(values))


def test_the_golden_cli_reuses_the_settings_it_finds(tmp_path):
    """Regenerating must not silently re-render at a different rate.

    An existing `.samples` supplies the rate and duration it was made at,
    so `--golden` with no flags reproduces the same buffer and only the
    numbers can change.
    """
    from gestate.audioperform import main as audio_main

    src = tmp_path / "tone.ges"
    src.write_text("sound : Sig Float\nsound = map (n => 0.25) ticks\n")
    assert audio_main([str(src), "--golden", "--rate", "200",
                       "--seconds", "0.05"]) == 0

    out = tmp_path / "tone.samples"
    header, samples = parse_golden(out.read_text())
    assert (header["rate"], len(samples)) == ("200", 10)

    assert audio_main([str(src), "--golden"]) == 0       # no flags at all
    again, samples_again = parse_golden(out.read_text())
    assert (again, samples_again) == (header, samples)
