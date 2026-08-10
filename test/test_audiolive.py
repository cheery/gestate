"""Playing a synth — `spec/liveaudio.md` stage 4's other half.

The device cannot be asserted on, so the thing that *can* be is asserted
instead: **the bytes that would reach the sound card**.  A player process
is a program reading raw `float32` from a pipe, so a test substitutes `cat`
for it and compares what arrives against the oracle's samples.  That covers
every step between the source text and the card except the card.

The property worth protecting here is not a number, it is a shape: the
driver makes **one call per block** and does no arithmetic.  Python in an
audio callback is what the whole architecture exists to avoid, so the
conversion to the device's format lives in the generated code.
"""

from __future__ import annotations

import shutil
import struct
import tempfile
from pathlib import Path

import pytest

from gestate.audio import render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiolive import (DEFAULT_BLOCK, Engine, LiveError, PLAYERS,
                               play, player_command)
from gestate.audiollvm import emit, run_native

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")


def _source(name: str) -> str:
    return (AUDIO_DIR / name).read_text()


def _as_float32(samples) -> list:
    """What a `double` becomes on the way to the card: clamped, narrowed."""
    return [struct.unpack("<f", struct.pack("<f", max(-1.0, min(1.0, s))))[0]
            for s in samples]


# ── The generated float32 path ──────────────────────────────────────────────


def test_the_engine_exports_a_device_format_entry_point():
    """The conversion belongs in the generated code, not in the driver."""
    text = emit(extract(_source("blip.ges"), rate=8000))
    assert "define void @render_block_f32(ptr %s, ptr %out, i64 %n" in text
    assert "fptrunc double" in text
    assert "@llvm.minnum.f64" in text and "@llvm.maxnum.f64" in text


@needs_clang
def test_the_float32_samples_are_the_double_ones_clamped():
    """Same numbers, narrowed — and clamped as `audio.write()` clamps.

    A synth that goes over 1.0 should sound like it did rather than be
    quietly rescaled, which is the rule the `.wav` writer already follows.
    """
    import ctypes

    from gestate.audiollvm import _slots, build, load

    graph = extract(_source("drums.ges"), rate=1000)
    with tempfile.TemporaryDirectory() as d:
        lib = load(build(graph, d))
        lib.render_block_f32.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_int64, ctypes.c_int64]
        buf = (ctypes.c_float * 40)()
        state = ctypes.create_string_buffer(
            8 * (1 + sum(_slots(graph, n) for n in graph.nodes)))
        lib.render_block_f32(ctypes.cast(state, ctypes.c_void_p),
                             ctypes.cast(buf, ctypes.c_void_p), 40, 0)
        got = list(buf)
    assert got == _as_float32(run(graph, 40))


@needs_clang
def test_a_loud_synth_is_clamped_not_wrapped():
    src = "sound : Sig Float\nsound = gain 4.0 (map (n => 1.0) ticks)\n"
    out = Path(tempfile.mkdtemp()) / "loud.raw"
    play(src, seconds=8 / 1000, rate=1000, block=4,
         command=["sh", "-c", f"cat > {out}"])
    data = out.read_bytes()
    assert set(struct.unpack(f"<{len(data) // 4}f", data)) == {1.0}


# ── A literal standing where a signal is wanted ─────────────────────────────


#: Three literals used as `Sig Float`, and one of them a filter's cutoff.
#:
#: `Floating (Sig Float)` lifts each with `fromFloat x = constSig x`, and
#: `constSig v = mapSig (n => v) ticks` — so each becomes a *node*, and the
#: cutoff becomes a node feeding a `zip` feeding the filter's `scan`.  That
#: is the shape a constant-folding pass would collapse.
LITERAL_AS_SIGNAL = """
tone : Sig Float
tone = sine 220.0

sound : Sig Float
sound = 0.25 * tone + 0.1 * lowpassSvf 900.0 0.4 (saw 110.0)
"""


@needs_clang
def test_a_literal_used_as_a_signal_agrees_across_all_three_engines():
    """The invariant a constant-folding pass must not break.

    **Written before the pass, deliberately.**  `spec/liveaudio.md` stage 2
    emits one node per signal combinator, so `0.25 * tone` costs a constant
    source, a `map` and a `zip` where `gain 0.25 tone` costs one `map`.
    Folding those away is worth doing — a fixed filter cutoff currently
    recomputes `tan` every sample because it arrives as a signal rather
    than as a folded constant — and it is safe only because `map` and `zip`
    carry no state: `render_block` computes both from `cur` alone, so
    nothing crosses an instant and `migrate` has nothing to lose.  A `scan`
    or a `source` may never be removed or re-kinded, and that is the whole
    of the rule.

    **The existing oracle tests would not have caught a bad fold.**  This
    file's other comparisons use `blip.ges`, `drums.ges` and `stereo.ges`,
    and not one of them has a `constSig` node — the only program in the
    tree that covers this bit-exactly is `duet.ges`, through
    `test_audionotes.py`, and it covers it by accident rather than intent.
    This says it on purpose.

    Three engines, because a fold can go wrong in each differently: the
    interpreter evaluates the graph reduction, the block renderer walks the
    node list, and the generated code inlines the step into LLVM IR.
    """
    rate, samples = 4000, 300
    oracle = render(LITERAL_AS_SIGNAL, samples / rate, rate)
    graph = extract(LITERAL_AS_SIGNAL, rate=rate)

    assert max(abs(x) for x in oracle) > 0.05, "silent — nothing is proven"
    assert len(set(round(x, 6) for x in oracle)) > 50, "a constant"

    assert run(graph, samples, block=64) == oracle, "the block renderer"
    with tempfile.TemporaryDirectory() as directory:
        assert run_native(graph, directory, samples,
                          block=64) == oracle, "the generated code"


def test_the_literal_fixture_really_contains_a_lifted_constant():
    """Otherwise the test above could pass by testing nothing.

    A fixture that stopped exercising a lifted literal — because someone
    rewrote it with `gain`, or because folding became so eager that the
    program no longer has one — would still render identically and would
    still pass.  This is the part that has to be *read* when it fails:
    if a fold removes these nodes, that is the pass working, and the right
    response is to weaken this assertion deliberately rather than to
    delete the test above with it.
    """
    graph = extract(LITERAL_AS_SIGNAL, rate=4000)
    lifted = [n for n in graph.nodes if "constSig" in n.origin]
    assert lifted, "the fixture no longer lifts a literal into a signal"
    assert [n for n in graph.nodes if n.kind == "scan"], "no state to protect"


# ── What actually reaches the card ──────────────────────────────────────────


@needs_clang
@pytest.mark.parametrize("name", ["blip.ges", "drums.ges"])
def test_the_stream_is_the_oracles_samples(name):
    """End to end, with `cat` where the sound card would be.

    Source text → fragment check → graph → LLVM IR → machine code → the
    bytes on the pipe, compared against what the interpreter says the synth
    sounds like.  Every stage of `spec/liveaudio.md` is in this one line.
    """
    out = Path(tempfile.mkdtemp()) / "stream.raw"
    frames, backend = play(_source(name), seconds=40 / 1000, rate=1000,
                           block=8, command=["sh", "-c", f"cat > {out}"])
    assert frames == 40 and backend == "sh"

    data = out.read_bytes()
    assert len(data) == 40 * 4, "one float32 per frame, one channel"
    got = list(struct.unpack("<40f", data))
    assert got == _as_float32(run(extract(_source(name), rate=1000), 40))


@needs_clang
@needs_clang
def test_a_stereo_engine_feeds_the_pipe_interleaved():
    """The whole live path, ending in bytes: two floats per frame.

    Written to a file rather than to a sound card, which is the only part
    of `play_through_pipe` that has to be faked — the buffer, the engine
    call and the slicing are the real ones, and the slicing is where a
    channel count gets dropped.
    """
    from gestate.audiolive import Engine, play_through_pipe

    with tempfile.TemporaryDirectory() as d:
        engine = Engine.compile(_source("stereo.ges"), 8000, d)
        assert engine.channels == 2
        out = Path(d) / "raw.f32"
        frames = play_through_pipe(engine, 0.02, 8000, 64,
                                   ["dd", "status=none", f"of={out}"])
        raw = out.read_bytes()
    got = struct.unpack(f"<{len(raw) // 4}f", raw)
    assert len(got) == frames * 2
    # Left is 440 and right 442, so they begin together and separate.  A
    # mono buffer read as stereo would pass a length check and fail this.
    assert got[0] == got[1] == 0.0
    assert any(a != b for a, b in zip(got[0::2], got[1::2]))


@needs_clang
def test_an_edit_that_changes_the_channel_count_is_refused(tmp_path):
    """Memory safety, not taste.

    The driver sized its buffer for the channel count it started with, so
    installing a stereo graph under a mono buffer writes past the end of
    it.  Refused like a syntax error: the sound goes on and the message
    says why.
    """
    from gestate.audiolive import Live

    with tempfile.TemporaryDirectory() as d:
        live = Live.start(_source("blip.ges"), 8000, d)
        assert live.channels == 1
        live.compile(_source("stereo.ges"))
        assert live.install() is False
        assert live.generation == 0
        assert any("channel" in e for e in live.errors), live.errors
        assert live.channels == 1, "the mono instrument is still the one playing"


def test_the_block_size_does_not_change_the_stream():
    """The same invariant as stage 3, now through the device path."""
    streams = []
    for block in (1, 5, 64):
        out = Path(tempfile.mkdtemp()) / "s.raw"
        play(_source("blip.ges"), seconds=40 / 1000, rate=1000, block=block,
             command=["sh", "-c", f"cat > {out}"])
        streams.append(out.read_bytes())
    assert streams[0] == streams[1] == streams[2]


@needs_clang
def test_a_partial_final_block_is_not_padded():
    """`--seconds` that is not a whole number of blocks stops on the sample.

    Writing the whole buffer would append however many frames the block
    happened to be short, which is silence at the end of every render and
    a click in a loop.
    """
    out = Path(tempfile.mkdtemp()) / "s.raw"
    frames, _backend = play(_source("blip.ges"), seconds=13 / 1000, rate=1000,
                            block=8, command=["sh", "-c", f"cat > {out}"])
    assert frames == 13
    assert len(out.read_bytes()) == 13 * 4


@needs_clang
def test_the_driver_does_one_call_per_block_and_no_arithmetic():
    """The shape that keeps Python out of the audio path.

    Asserted by counting: 40 frames in blocks of 8 is five calls into the
    engine, and everything else the driver does is a `write`.
    """
    graph_calls = []

    class Counting(Engine):
        def fill(self, buffer, frames, control=None, t=0):
            graph_calls.append(frames)
            super().fill(buffer, frames, control, t)

    import gestate.audiolive as live

    original = live.Engine
    live.Engine = Counting
    try:
        out = Path(tempfile.mkdtemp()) / "s.raw"
        play(_source("blip.ges"), seconds=40 / 1000, rate=1000, block=8,
             command=["sh", "-c", f"cat > {out}"])
    finally:
        live.Engine = original
    assert graph_calls == [8, 8, 8, 8, 8]


# ── Choosing a player ───────────────────────────────────────────────────────


def test_the_player_command_asks_for_raw_float32_at_the_right_rate():
    for name in PLAYERS:
        if shutil.which(name) is None:
            continue
        cmd = player_command(48000, prefer=name)
        assert cmd[0] == name
        assert any("48000" in part for part in cmd), cmd
        assert any("f32" in part.lower() or "float" in part.lower()
                   for part in cmd), cmd


def test_the_player_is_told_how_many_channels_it_is_getting():
    """A stereo stream sent to a mono player is not a quiet failure.

    It plays at twice the pitch with the ears alternating, which sounds
    like a broken synth rather than like a misconfigured player — so the
    count comes from the graph and reaches every player's spelling of it.
    """
    for name in PLAYERS:
        assert any("{channels}" in part for part in PLAYERS[name]), name
        if shutil.which(name) is None:
            continue
        assert any("2" == part.rsplit("=", 1)[-1] or part == "2"
                   for part in player_command(48000, prefer=name, channels=2))


def test_a_driver_is_asked_how_many_channels_it_fills():
    """As `position_of` is asked: only the innermost thing knows the graph."""
    from gestate.audiolive import channels_of

    class _Stereo:
        channels = 2

    assert channels_of(_Stereo()) == 2
    assert channels_of(object()) == 1        # a mono test double


def test_an_absent_player_is_reported_rather_than_guessed():
    with pytest.raises(LiveError, match="no player"):
        player_command(48000, prefer="definitely-not-installed")


def test_the_default_block_is_a_few_milliseconds():
    """Small enough to feel immediate, large enough that the call is free."""
    assert 1.0 < DEFAULT_BLOCK / 48000 * 1000 < 20.0


def test_playing_shortens_the_gil_slice_and_puts_it_back():
    """What stops a rebuild from tearing the sound it is rebuilding.

    The block is machine code, but the thread that asks for it is a Python
    thread, and an editor rebuilds on another one — seconds of pure-Python
    front end, holding the GIL for a whole switch interval at a time.
    Auditioning `duet.ges` at 48 kHz, the 5 ms default missed 519 of 2,909
    block deadlines; 1 ms missed 13 of 4,641.

    Asserted from *inside* the driver, because the setting is only worth
    anything while a block is due.  And put back afterwards: it is
    process-wide, and a render that is not playing has no deadline.
    """
    import sys

    from gestate.audiolive import PLAYING_SWITCH_INTERVAL

    class _Silence:
        """A driver's engine, filling nothing.  See `channels_of`."""
        frames = 0

        def fill(self, buffer, frames, control=None, t=0):
            self.frames += frames

    before = sys.getswitchinterval()
    seen = []
    play(None, seconds=32 / 1000, rate=1000, block=8, engine=_Silence(),
         command=[sys.executable, "-c",
                  "import sys\nwhile sys.stdin.buffer.read(4096): pass"],
         progress=lambda _n: seen.append(sys.getswitchinterval()))

    assert seen, "the driver never ran"
    assert max(seen) <= PLAYING_SWITCH_INTERVAL, seen
    assert sys.getswitchinterval() == before, "left the interpreter tuned"


# ── The CLI ─────────────────────────────────────────────────────────────────


def test_the_cli_reports_a_program_it_cannot_play(capsys):
    """The retired door refuses by name and points at
    the replacement — the voices-retirement rule for a
    CLI (`spec/crust.md` era consolidation: one door,
    `gestate.audioperform`, beside the editors)."""
    from gestate.audiolive import main as retired_main

    assert retired_main([]) == 2
    err = capsys.readouterr().err
    assert "retired" in err
    assert "audioeditor" in err


# ── The sounddevice path ────────────────────────────────────────────────────


def test_a_driver_reports_its_position_whatever_it_is():
    """`fixme.md`-worthy on its own: the callback asked for `frames`.

    `Engine` counts `frames`; a `Transport` has a `position` it may rewind.
    The PortAudio callback asked the first of a driver that only had the
    second — and **a callback may not raise**: PortAudio calls it from its
    own thread through cffi, so the `AttributeError` was printed and
    swallowed and the stream went on producing silence.  It read as "the
    synth stopped working" rather than as anything anyone could act on.
    """
    from gestate.audiolive import position_of

    class _Engine:
        frames = 7

    class _Transport:
        position = 42

    assert position_of(_Engine()) == 7
    assert position_of(_Transport()) == 42
    assert position_of(object()) == 0


#: It installs a fake `sounddevice` below and calls the backend against it,
#: so no device is reached — `test/conftest.py`'s guard stands aside.
@pytest.mark.own_audio_backend
def test_a_failing_callback_stops_the_stream(monkeypatch):
    """Rather than haunting it.

    A swallowed exception in an audio callback is the worst shape of bug
    there is: everything reports success and no sound comes out.
    """
    import sys
    import types

    from gestate import audiolive

    aborted = []

    class _Abort(Exception):
        pass

    class _Stream:
        def __init__(self, **kw):
            self.callback = kw["callback"]

        def __enter__(self):
            try:
                self.callback(None, 64, None, None)
            except _Abort:
                aborted.append(True)
            return self

        def __exit__(self, *a):
            return False

    fake = types.ModuleType("sounddevice")
    fake.RawOutputStream = lambda **kw: _Stream(**kw)
    fake.CallbackAbort = _Abort
    fake.sleep = lambda _ms: None
    monkeypatch.setitem(sys.modules, "sounddevice", fake)

    class _Broken:
        position = 0

        def fill(self, *_a):
            raise RuntimeError("no such attribute")

    with pytest.raises(audiolive.LiveError, match="callback failed"):
        audiolive.play_through_sounddevice(_Broken(), 0.01, 8000, 64)
    assert aborted, "the stream should have been aborted, not left running"


@needs_clang
def test_a_block_fills_either_kind_of_buffer():
    """The pipe allocates a `ctypes` array; PortAudio hands over cffi's.

    `ctypes.cast` refuses the second with `TypeError: wrong type` — and
    raised inside a callback that may not raise, it became **silence**
    rather than a traceback.  Both must give the same samples, so this
    fills one of each and compares.
    """
    import ctypes

    sd = pytest.importorskip("sounddevice")
    ffi = sd._ffi

    src = _source("blip.ges")
    with tempfile.TemporaryDirectory() as d:
        through_cffi = Engine.compile(src, 8000, d)
        raw = ffi.new("char[]", 64 * 4)
        through_cffi.fill(ffi.buffer(raw), 64, None, 0)
        cffi_samples = list(ffi.unpack(ffi.cast("float *", raw), 64))

        through_ctypes = Engine.compile(src, 8000, d)
        array = (ctypes.c_float * 64)()
        through_ctypes.fill(array, 64, None, 0)

    assert cffi_samples == list(array)
    assert any(s != 0.0 for s in cffi_samples), "silent either way"


def test_the_address_helper_takes_both():
    """Without a sound card, and without `sounddevice` — it is arithmetic."""
    import ctypes

    from gestate.audiolive import address_of

    array = (ctypes.c_float * 8)()
    assert address_of(array).value == ctypes.addressof(array)

    view = bytearray(32)
    assert address_of(view).value is not None


# ── The fade across an edit ─────────────────────────────────────────────────
#
# `audioengine.migrate` carries a phase, a filter's memory and a delay line
# across an edit so that editing an instrument does not restart its
# envelopes — deliberately *not* a crossfade.  What it cannot do is make the
# two engines agree sample for sample at the seam: a changed coefficient, a
# node that is new and starts at its `init`.  The waveform steps, and a step
# is a click.  So the state migrates *and* the output is faded across it.


class _Steady:
    """An engine that fills every sample with one value."""

    def __init__(self, value: float, channels: int = 1):
        self.value = value
        self._channels = channels
        self.frames = 0
        self.graph = None

    @property
    def channels(self) -> int:
        return self._channels

    def fill(self, buffer, frames, control=None, t=0) -> None:
        for i in range(frames * self._channels):
            buffer[i] = self.value

    def fill_mix(self, buffer, frames, control, t, g0, g1) -> None:
        """The contract the generated `render_block_mix_f32` implements:
        multiply by a ramp `g0`→`g1` across the block, **add** rather than
        store, and use one gain per *frame* so a stereo pair cannot drift
        apart.  `test_the_generated_engine_honours_the_mix_contract` checks
        the real one against the same description."""
        for i in range(frames):
            gain = g0 + (g1 - g0) * i / frames
            for c in range(self._channels):
                k = i * self._channels + c
                buffer[k] += self.value * gain


def _live(rate: int = 1000, channels: int = 1):
    from gestate.audiolive import Live

    live = Live(_Steady(1.0, channels), rate, None)
    return live


def _fill(live, frames: int):
    import ctypes

    buffer = (ctypes.c_float * (frames * live.channels))()
    live.fill(buffer, frames)
    return list(buffer)


def test_with_no_edit_nothing_is_blended(tmp_path):
    """The common case, and it has to cost nothing."""
    live = _live()
    assert _fill(live, 8) == [1.0] * 8
    assert live.leaving is None and live.fading == 0


def test_an_edit_fades_from_the_old_engine_to_the_new(tmp_path):
    live = _live(rate=1000)                    # 40 ms -> 40 samples
    live.leaving, live.fading = _Steady(0.0), live.fade_samples
    live.engine = _Steady(1.0)

    got = _fill(live, live.fade_samples)
    assert got[0] == pytest.approx(0.0, abs=0.05), "it did not start at the old"
    assert got[-1] == pytest.approx(1.0, abs=0.05), "it did not reach the new"
    assert got == sorted(got), "the fade was not monotone"


def test_the_fade_ends_and_the_old_engine_is_let_go(tmp_path):
    live = _live(rate=1000)
    live.leaving, live.fading = _Steady(0.0), live.fade_samples
    live.engine = _Steady(1.0)

    _fill(live, live.fade_samples + 4)
    assert live.leaving is None, "the old engine was kept for ever"
    assert live.fading == 0
    assert _fill(live, 4) == [1.0] * 4, "it went on blending after the fade"


def test_a_fade_spanning_several_blocks_picks_up_where_it_left_off(tmp_path):
    """A fade is 40 ms and a block is often less, so it has to survive
    being interrupted — otherwise it restarts every block and never ends."""
    live = _live(rate=1000)
    live.leaving, live.fading = _Steady(0.0), live.fade_samples
    live.engine = _Steady(1.0)

    first = _fill(live, 10)
    assert live.fading == live.fade_samples - 10
    second = _fill(live, 10)
    assert second[0] > first[-1], "it started over instead of continuing"


def test_both_channels_of_a_frame_fade_by_the_same_amount(tmp_path):
    """Otherwise the stereo image wanders during the fade, which is
    audible exactly where the point was for nothing to be."""
    live = _live(rate=1000, channels=2)
    live.leaving, live.fading = _Steady(0.0, 2), live.fade_samples
    live.engine = _Steady(1.0, 2)

    got = _fill(live, 12)
    assert got[0::2] == got[1::2], got[:8]


def test_the_fade_is_long_enough_to_be_a_slew_and_not_a_tick(tmp_path):
    """Forty milliseconds at the rate actually being played, not forty
    samples — the constant is a time, and a rate that changes must not
    change what it means."""
    from gestate.audiolive import FADE_MS

    for rate in (8000, 44100, 48000):
        live = _live(rate=rate)
        assert live.fade_samples == int(rate * FADE_MS / 1000)


@pytest.mark.skipif(shutil.which("clang") is None, reason="no clang")
def test_the_generated_engine_honours_the_mix_contract():
    """**The fade is in the engine, not in the host.**  Two calls with
    complementary ramps must sum to unity, or a crossfade is a dip.

    Checked on the generated code rather than on the stub above, because
    the stub is a description of this and not evidence for it.
    """
    import ctypes
    import tempfile

    from gestate.audiollvm import build, load, state_size
    from gestate.audioperform import graph_of

    graph = graph_of("sound : Sig Float\nsound = !0.5\n", "", rate=8000)
    with tempfile.TemporaryDirectory() as directory:
        lib = load(build(graph, directory))
        lib.render_block_mix_f32.restype = None
        lib.render_block_mix_f32.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64,
            ctypes.c_void_p, ctypes.c_double, ctypes.c_double]

        n = 16
        buffer = (ctypes.c_float * n)()

        def run(g0: float, g1: float) -> None:
            state = ctypes.create_string_buffer(state_size(graph))
            lib.render_block_mix_f32(ctypes.cast(state, ctypes.c_void_p),
                                     ctypes.cast(buffer, ctypes.c_void_p),
                                     n, None, g0, g1)

        run(0.0, 1.0)
        rising = list(buffer)
        assert rising[0] == pytest.approx(0.0)
        assert rising == sorted(rising), "the ramp is not monotone"

        run(1.0, 0.0)                       # accumulates into the same buffer
        assert list(buffer) == pytest.approx([0.5] * n), \
            "complementary ramps did not sum to unity — a fade would dip"


# ── The master fade at the edges of a render ────────────────────────────────
#
# The first sample of a synth is a step from silence to wherever the
# waveform happens to begin, and stopping at `--seconds` is a step back —
# and a step is a click, the same fact the crossfade above exists for.  The
# same generated ramp serves both: `MasterFader` zeroes the block and lets
# the engine add into it through `render_block_mix_f32`.  Off by default,
# which is what keeps every bit-identical comparison in this file honest;
# the CLI is what asks for it.


@needs_clang
def test_the_master_fade_takes_both_edges_off_a_finite_render():
    """End to end: the bytes on the pipe rise from silence and return to
    it, and between the fades they are exactly the engine's own."""
    src = "sound : Sig Float\nsound = map (n => 1.0) ticks\n"
    out = Path(tempfile.mkdtemp()) / "faded.raw"
    frames, _backend = play(src, seconds=0.2, rate=1000, block=8,
                            command=["sh", "-c", f"cat > {out}"], fade_ms=40)
    assert frames == 200
    got = list(struct.unpack("<200f", out.read_bytes()))
    span = 40                                    # 40 ms at 1000 Hz
    assert got[0] < 0.05 and got[-1] < 0.05, "an edge is still loud"
    assert got[:span] == sorted(got[:span]), "the fade-in is not monotone"
    assert got[-span:] == sorted(got[-span:], reverse=True), \
        "the fade-out is not monotone"
    assert got[span:-span] == [1.0] * (200 - 2 * span), \
        "between the fades the stream is not the engine's own samples"


def test_outside_its_fades_the_master_fader_stands_clear():
    """Blocks at full level go through the plain entry point — the fade
    must not put a cost on every block of a long render, and an open-ended
    play (`--seconds` omitted) has no end to fade toward, so after the
    fade-in every block is plain."""
    import ctypes

    from gestate.audiolive import MasterFader

    class _Counting(_Steady):
        def __init__(self):
            super().__init__(1.0)
            self.plain, self.mixed = 0, 0

        def fill(self, buffer, frames, control=None, t=0):
            self.plain += 1
            super().fill(buffer, frames, control, t)

        def fill_mix(self, buffer, frames, control, t, g0, g1):
            self.mixed += 1
            super().fill_mix(buffer, frames, control, t, g0, g1)

    engine = _Counting()
    fader = MasterFader(engine, 1000, None)      # 40 ms -> 40 samples, no end
    buffer = (ctypes.c_float * 8)()
    for t in range(0, 400, 8):
        fader.fill(buffer, 8, None, t)
    assert engine.mixed == 5, "the fade-in is 40 samples in blocks of 8"
    assert engine.plain == 45, "a block at full level was still mixed"


# ── What a rebuild is allowed to do to the thread with a deadline ───────────


def test_playing_calms_the_collector_and_puts_it_back():
    """**The GIL was only half of the crackle.**  Shortening the slice
    fixed contention and left the pauses: a collection is not preemptible,
    so it stops the thread that has 5.3 ms to fill a buffer.  Measured on
    two cores with a different edit each rebuild, the 99th percentile fell
    from 75.5 ms to 3.2 ms.

    Restored on the way out, because both are process-wide and a program
    that has stopped playing has no deadline to protect.
    """
    import gc
    import sys

    from gestate.audiolive import (PLAYING_GC_THRESHOLD,
                                   PLAYING_SWITCH_INTERVAL,
                                   deadline_scheduling)

    before = (gc.get_threshold(), sys.getswitchinterval())
    with deadline_scheduling():
        assert gc.get_threshold() == PLAYING_GC_THRESHOLD
        assert sys.getswitchinterval() <= PLAYING_SWITCH_INTERVAL
    assert (gc.get_threshold(), sys.getswitchinterval()) == before


def test_the_collector_is_calmed_and_not_switched_off():
    """Off is perfect for latency and leaks: twelve edits left 368,245
    cyclic objects and 44 MB.  A long session has to stay bounded, so the
    collector still runs — just not in the middle of a block."""
    import gc

    from gestate.audiolive import deadline_scheduling

    with deadline_scheduling():
        assert gc.isenabled(), "a session would grow without bound"
