"""`gestate/host.c` — the audio callback with no interpreter in it.

`audiolive` kept the *language* out of the audio path and always did: per
block it did about 16 µs of control work against a 5,333 µs budget.  What
it could not escape is that a Python frame can be **stopped** — the GIL for
a slice, the collector for a hundred milliseconds — and a thread that is
stopped misses its deadline however little it had to do.

So the swap, the fade, the control block and the frame count moved into C,
and Python's job became preparing and publishing.  These check that the C
side does what the Python side did, and that Python cannot interrupt it.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import tempfile
import threading
import time

import pytest

from gestate.audiohost import Host, HostError

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the host with")

pytestmark = needs_clang

RATE = 8000


def _engine(body: str, rate: int, directory):
    from gestate.audiolive import Engine

    return Engine.compile(f"sound : Sig Float\nsound = {body}\n", rate,
                          directory)


@pytest.fixture
def scratch():
    with tempfile.TemporaryDirectory() as directory:
        yield directory


# ── It renders what the engine renders ──────────────────────────────────────


def test_the_c_host_renders_exactly_what_the_engine_does(scratch):
    """**The comparison the whole thing rests on.**  Moving the callback
    into C is only safe if it is the same sound — the DSP did not move, so
    a difference here would be the host getting the call wrong."""
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of

    source = "sound : Sig Float\nsound = sine 440.0\n"
    # `fade_in=False`: there is no device here to pop, and the comparison
    # is against the engine's own output rather than a session's first
    # block.
    host = Host(channels=1, rate=RATE, directory=scratch, fade_in=False)
    host.install(_engine("sine 440.0", RATE, scratch))
    buffer = (ctypes.c_float * 128)()
    host.fill(buffer, 128)
    through_c = list(buffer)
    host.close()

    graph = graph_of(source, "", rate=RATE)
    with tempfile.TemporaryDirectory() as other:
        assert through_c == pytest.approx(list(run_native(graph, other, 128)))


def test_with_nothing_installed_it_is_silent_rather_than_a_crash(scratch):
    """A host is made before an engine is compiled — the window opens
    first, which is the whole reason `Workbench` starts on a thread."""
    host = Host(channels=1, rate=RATE, directory=scratch)
    buffer = (ctypes.c_float * 32)()
    for i in range(32):
        buffer[i] = 0.5
    host.fill(buffer, 32)
    assert list(buffer) == [0.0] * 32
    host.close()


# ── The swap and the fade, in C ─────────────────────────────────────────────


def test_a_published_engine_is_taken_and_faded_in(scratch):
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!0.0", 1000, scratch))
    buffer = (ctypes.c_float * 40)()

    host.fill(buffer, 40)
    assert list(buffer) == [0.0] * 40, "it changed before being asked to"

    host.publish(_engine("!1.0", 1000, scratch))
    host.fill(buffer, 40)                       # exactly the fade's length
    got = list(buffer)
    assert got[0] == pytest.approx(0.0, abs=0.05)
    assert got[-1] == pytest.approx(1.0, abs=0.05)
    assert got == sorted(got), "the fade is not monotone"
    host.close()


def test_the_fade_ends_and_stays_ended(scratch):
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!0.0", 1000, scratch))
    host.publish(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 64)()

    assert host.fading is False, "nothing has been rendered yet"
    host.fill(buffer, 64)
    assert host.fading is False, "the fade outlasted its length"
    host.fill(buffer, 64)
    assert list(buffer) == [1.0] * 64
    host.close()


def test_a_fade_spanning_several_blocks_picks_up_where_it_left_off(scratch):
    """A fade is 40 ms and a block is often less, so it has to survive
    being interrupted — otherwise it restarts every block and never ends."""
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!0.0", 1000, scratch))
    host.publish(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 10)()

    seen = []
    for _ in range(4):
        host.fill(buffer, 10)
        seen.append(list(buffer))
    assert seen[0][0] < seen[1][0] < seen[2][0], "it started over each block"
    assert seen[3][-1] == pytest.approx(1.0, abs=0.05)
    host.close()


def test_a_second_publish_before_the_first_is_taken_replaces_it(scratch):
    """One slot, and the newest wins — which is what a person typing
    means by two edits in a row."""
    host = Host(channels=1, rate=1000, fade_ms=4, directory=scratch)
    host.install(_engine("!0.0", 1000, scratch))
    host.publish(_engine("!0.5", 1000, scratch))
    host.publish(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 32)()
    host.fill(buffer, 32)
    assert buffer[31] == pytest.approx(1.0, abs=0.01), \
        "the older edit won, or both were applied"
    host.close()


def test_the_swap_lands_on_a_block_boundary(scratch):
    """Never inside a buffer: the staged engine is taken at the top of
    `fill` and nowhere else, which is why publishing needs no lock."""
    host = Host(channels=1, rate=1000, fade_ms=1, directory=scratch)
    host.install(_engine("!0.0", 1000, scratch))
    buffer = (ctypes.c_float * 16)()
    host.publish(_engine("!1.0", 1000, scratch))
    host.fill(buffer, 16)
    # A one-frame fade, so everything after the first frame is the new one.
    assert list(buffer)[2:] == [1.0] * 14
    host.close()


# ── What it must not do ─────────────────────────────────────────────────────


def test_the_control_block_is_allocated_once(scratch):
    """**An allocation per block is what this file exists to remove.**  The
    Python driver built a fresh `ctypes` array every callback — garbage
    172 times a second, feeding the very collector whose pauses were the
    problem."""
    host = Host(channels=1, rate=RATE, controls=4, directory=scratch)
    host.install(_engine("sine 440.0", RATE, scratch))
    was = ctypes.addressof(host.control)
    buffer = (ctypes.c_float * 64)()
    for _ in range(20):
        host.fill(buffer, 64)
    assert ctypes.addressof(host.control) == was
    host.close()


def test_an_engine_handed_over_is_kept_alive(scratch):
    """C holds raw pointers into the engine's state and its loaded
    library.  Letting Python collect one would be a use-after-free in the
    render thread, which is the worst kind of bug this could have."""
    host = Host(channels=1, rate=RATE, directory=scratch)
    engine = _engine("sine 440.0", RATE, scratch)
    host.install(engine)
    host.publish(_engine("saw 220.0", RATE, scratch))
    assert len(host._kept) == 2
    assert engine in host._kept
    host.close()


def test_running_releases_the_gil(scratch):
    """**The point of the exercise.**  `ctypes` drops the GIL around a
    foreign call, and `run` *is* the whole loop — so Python cannot
    interrupt a block, a swap or a fade.  It can only compete for CPU,
    which is the scheduler's business and not the interpreter's.
    """
    host = Host(channels=1, rate=RATE, directory=scratch)
    host.install(_engine("sine 440.0", RATE, scratch))
    devnull = os.open(os.devnull, os.O_WRONLY)

    ticks, stop = [0], threading.Event()

    def counting():
        while not stop.is_set():
            ticks[0] += 1

    worker = threading.Thread(target=counting, daemon=True)
    worker.start()
    time.sleep(0.05)
    host.run(devnull, 256, RATE)              # a second of audio
    stop.set()
    worker.join(timeout=5)
    os.close(devnull)
    host.close()

    assert ticks[0] > 1000, "Python made no progress; the GIL was held"


def test_frames_are_counted_in_c(scratch):
    host = Host(channels=1, rate=RATE, directory=scratch)
    host.install(_engine("sine 440.0", RATE, scratch))
    buffer = (ctypes.c_float * 64)()
    host.fill(buffer, 64)
    host.fill(buffer, 64)
    assert host.frames == 128
    host.close()


def test_stereo_frames_are_interleaved_and_sized_right(scratch):
    host = Host(channels=2, rate=RATE, directory=scratch)
    host.install(_engine("sine 440.0", RATE, scratch))
    buffer = (ctypes.c_float * 64)()
    host.fill(buffer, 32)                     # 32 frames, 2 channels
    assert host.frames == 32
    host.close()


def test_a_missing_toolchain_says_so(monkeypatch, scratch):
    """The message a machine without `clang` should get, rather than a
    `FileNotFoundError` from a subprocess."""
    import gestate.audiohost as audiohost

    monkeypatch.setattr(audiohost, "_LIB", None)

    def no_clang(*_args, **_kw):
        raise FileNotFoundError("clang")

    monkeypatch.setattr(audiohost.subprocess, "run", no_clang)
    with pytest.raises(HostError, match="clang"):
        audiohost.library(scratch)


# ── The last thing before a speaker ─────────────────────────────────────────
#
# The guard is in the *generated* code — `audiollvm._render_block` emits the
# NaN test and the clamp for every `float` entry point, and the mix entry
# point is emitted by the same function — so moving the callback into C did
# not move the guard.  Checked here anyway, because "it should still be
# there" is a claim about a path nobody had run before.

NAN_AT_ZERO = ("sound : Sig Float\n"
               "sound = map bad ticks\n"
               "\nbad : Int -> Float\n"
               "bad n = (1.0 / toFloat n) * toFloat n\n")


def test_a_nan_still_reaches_the_device_as_silence(scratch):
    """Without the guard this leaves as +1.0 — sustained full-scale DC,
    maximum power into a voice coil that is not moving and so is not being
    cooled by moving.  The interpreter refuses to divide by zero; the
    generated code has no such scruple, and it is what drives the card."""
    from gestate.audiolive import Engine

    host = Host(channels=1, rate=RATE, directory=scratch, fade_in=False)
    host.install(Engine.compile(NAN_AT_ZERO, RATE, scratch))
    buffer = (ctypes.c_float * 8)()
    host.fill(buffer, 8)
    got = list(buffer)
    host.close()

    assert not any(x != x for x in got), "a NaN reached the buffer"
    assert got[0] == 0.0, f"the NaN instant came out as {got[0]}"
    assert got[1:] == [1.0] * 7, "it damaged the samples that were fine"


def test_an_over_range_program_is_clamped(scratch):
    """A sample above 1.0 does not clip in the conversion to the device's
    format, it *wraps* — a 20% overshoot becomes a full-scale square."""
    host = Host(channels=1, rate=RATE, directory=scratch)
    host.install(_engine("40.0 * sine 440.0", RATE, scratch))
    buffer = (ctypes.c_float * 64)()
    host.fill(buffer, 64)
    assert max(abs(x) for x in buffer) <= 1.0
    host.close()


def test_the_crossfade_cannot_add_its_way_out_of_range(scratch):
    """**The case worth checking rather than reasoning about.**  The mix
    entry point clamps each engine and then *accumulates*, so the value
    written is `was + sample * gain` and is not itself re-clamped.  It
    stays bounded only because `gestate_host_fill` zeroes the buffer first
    and the two gains are complementary.  If either stopped being true this
    is what would notice."""
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!40.0", 1000, scratch))
    host.publish(_engine("!(negate 40.0)", 1000, scratch))
    buffer = (ctypes.c_float * 64)()
    host.fill(buffer, 64)
    assert max(abs(x) for x in buffer) <= 1.0
    host.close()


def test_a_nan_program_faded_in_is_still_silence(scratch):
    from gestate.audiolive import Engine

    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!0.5", 1000, scratch))
    host.publish(Engine.compile(NAN_AT_ZERO, 1000, scratch))
    buffer = (ctypes.c_float * 64)()
    host.fill(buffer, 64)
    assert not any(x != x for x in buffer)
    assert max(abs(x) for x in buffer) <= 1.0
    host.close()


# ── The device, opened from C ───────────────────────────────────────────────
#
# The pipe was a stand-in and it was the wrong shape: handing a
# `subprocess.PIPE` across meant Python owned the write end while C wrote
# through it — two owners for one thing, and it hung the first time it was
# asked to finish.  A device the render loop opens and closes itself has one
# owner, and no descriptor, pipe or player process passes through Python.
#
# Two below are marked `own_audio_backend`: they are *about* the guard's
# subject rather than users of it — one opens a device that does not exist
# and one is refused before ALSA is reached — so `conftest`'s blanket
# refusal, which exists to stop a test making a noise, would otherwise stop
# the two tests that prove it cannot.


def test_a_device_backend_is_compiled_in_where_the_header_exists(scratch):
    """Gated the way every backend here is: a machine with
    `alsa/asoundlib.h` gets one, a machine without gets a host that renders
    and cannot open anything, and the difference is a file test rather than
    a build that may fail."""
    from pathlib import Path

    host = Host(channels=1, rate=RATE, directory=scratch)
    assert host.has_device == Path("/usr/include/alsa/asoundlib.h").exists()
    host.close()


@pytest.mark.own_audio_backend
def test_opening_a_device_that_is_not_there_says_so(scratch):
    """A `HostError` naming the device, rather than a return code — this is
    reached by someone who typed a device name, and `-1` is not an answer."""
    host = Host(channels=1, rate=RATE, directory=scratch)
    if not host.has_device:
        host.close()
        pytest.skip("no device backend compiled in")
    with pytest.raises(HostError, match="nowhere-at-all"):
        host.open("nowhere-at-all")
    host.close()


@pytest.mark.own_audio_backend
def test_a_host_without_a_device_backend_says_what_to_install(scratch,
                                                              monkeypatch):
    host = Host(channels=1, rate=RATE, directory=scratch)
    monkeypatch.setattr(type(host), "has_device", property(lambda _self: False))
    with pytest.raises(HostError, match="libasound2-dev"):
        host.open()
    host.close()


def test_closing_twice_is_safe(scratch):
    """`close` runs from a `finally` and from a `__del__`-ish path in the
    editor, so it has to be idempotent — closing a PCM twice is a crash,
    not an error."""
    host = Host(channels=1, rate=RATE, directory=scratch)
    host.close()
    host.close()


# ── No pops ─────────────────────────────────────────────────────────────────
#
# Going to silence in one sample is a step in the waveform, and a step is a
# click however quiet what came before it was.  Three of them: pressing
# stop, pressing play, and quitting — the last because the loop used to
# leave the moment `stop` was set, closing the device mid-waveform.


def _ramps(values: list) -> bool:
    """Does this move a step at a time rather than in one jump?"""
    steps = [abs(b - a) for a, b in zip(values, values[1:])]
    return bool(steps) and max(steps) < 0.5


def test_the_first_block_of_a_session_fades_up(scratch):
    """The first block is the same step as any other and pops the same
    way — so a session starts with the fader down."""
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 16)()
    host.fill(buffer, 16)
    got = list(buffer)
    assert got[0] == pytest.approx(0.0, abs=0.01), "it started at full scale"
    assert got == sorted(got) and _ramps(got)
    host.close()


def test_stopping_fades_out_rather_than_cutting(scratch):
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 16)()
    host.fill(buffer, 16)
    host.fill(buffer, 16)                       # up to full
    assert list(buffer) == [1.0] * 16

    host.playing = False
    host.fill(buffer, 16)
    got = list(buffer)
    assert got[0] == pytest.approx(1.0, abs=0.01), "it jumped"
    assert got[-1] < 0.1 and _ramps(got)
    host.close()


def test_the_clock_still_freezes_once_it_is_silent(scratch):
    """A stopped transport is stopped, not playing nothing — it just takes
    a few milliseconds to get there, and the tail is heard rather than
    cut."""
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 16)()
    host.fill(buffer, 16)
    host.playing = False
    host.fill(buffer, 16)                       # the fade out
    host.fill(buffer, 16)                       # now fully down
    was = host.position
    host.fill(buffer, 16)
    assert host.position == was, "the clock moved while silent"
    assert list(buffer) == [0.0] * 16
    host.close()


def test_starting_again_fades_back_up(scratch):
    host = Host(channels=1, rate=1000, fade_ms=40, directory=scratch)
    host.install(_engine("!1.0", 1000, scratch))
    buffer = (ctypes.c_float * 16)()
    host.playing = False
    host.fill(buffer, 16)
    host.playing = True
    host.fill(buffer, 16)
    got = list(buffer)
    assert got[0] == pytest.approx(0.0, abs=0.01)
    assert _ramps(got)
    host.close()


def test_quitting_drains_the_fade_before_the_loop_leaves(scratch):
    """**The pop on quit.**  The loop used to break the moment `stop` was
    set, which closes the device in the middle of a waveform.  `fill` is
    already fading toward silence by then, so the loop waits for it to
    arrive."""
    import struct
    import threading
    import time

    host = Host(channels=1, rate=8000, fade_ms=40, directory=scratch)
    host.install(_engine("!1.0", 8000, scratch))
    read_fd, write_fd = os.pipe()
    got = bytearray()

    def drain():
        while True:
            chunk = os.read(read_fd, 65536)
            if not chunk:
                break
            got.extend(chunk)

    reader = threading.Thread(target=drain, daemon=True)
    runner = threading.Thread(target=lambda: host.run(write_fd, 256, 0),
                              daemon=True)
    reader.start()
    runner.start()
    time.sleep(0.2)
    host.stop()
    runner.join(timeout=5)
    os.close(write_fd)
    reader.join(timeout=2)
    os.close(read_fd)
    host.close()

    samples = struct.unpack(f"<{len(got) // 4}f", bytes(got))
    assert samples, "nothing was rendered"
    assert abs(samples[-1]) < 0.05, \
        f"it ended at {samples[-1]:.3f} — the device closed mid-waveform"
    assert _ramps(list(samples[-12:]))


# ── The spectrum ────────────────────────────────────────────────────────────
#
# Eight one-pole lowpasses; band `k` is what `lp[k]` passes and `lp[k-1]`
# did not, and the top band is what none of them did.  A crude filter bank
# and the right one here — the output is eight numbers a person looks at
# sixty times a second, not an analysis.


def _bars(host, body: str, rate: int, scratch, blocks: int = 12) -> list:
    from gestate.audiolive import Engine

    host.install(Engine.compile(f"sound : Sig Float\nsound = {body}\n",
                                rate, scratch))
    host.watch_bands(True)
    buffer = (ctypes.c_float * 2048)()
    for _ in range(blocks):
        host.fill(buffer, 2048)
    return [host.band(k) for k in range(host.bands)]


def test_a_low_tone_lights_the_low_band(scratch):
    host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
    bars = _bars(host, "0.8 * sine 60.0", 22050, scratch)
    host.close()
    assert bars.index(max(bars)) == 0, bars


def test_a_high_tone_lights_a_high_band(scratch):
    host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
    bars = _bars(host, "0.8 * sine 8000.0", 22050, scratch)
    host.close()
    assert bars.index(max(bars)) >= 4, bars


def test_the_bands_are_ordered_by_pitch(scratch):
    """The loudest band climbs with the tone, which is the only property
    a picture of a spectrum has to have."""
    loudest = []
    for hz in (60.0, 400.0, 1500.0, 8000.0):
        host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
        bars = _bars(host, f"0.8 * sine {hz}", 22050, scratch)
        host.close()
        loudest.append(bars.index(max(bars)))
    assert loudest == sorted(loudest), loudest
    assert loudest[0] < loudest[-1], "it never moved"


def test_noise_reaches_every_band(scratch):
    host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
    bars = _bars(host, "0.8 * white 1", 22050, scratch)
    host.close()
    assert all(b > 0.01 for b in bars), bars


def test_a_band_is_read_and_not_taken(scratch):
    """Unlike the peak, which is cleared on reading: a bar falls on its own
    release, so a look that emptied it would show a gap rather than a
    decay."""
    host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
    bars = _bars(host, "0.8 * sine 60.0", 22050, scratch)
    again = [host.band(k) for k in range(host.bands)]
    host.close()
    assert again == bars


def test_nothing_is_analysed_unless_a_program_asks(scratch):
    """The same bargain the meter makes: this is the one place with no
    time to spare, and a reading nobody looks at is a cost nobody agreed
    to."""
    from gestate.audiolive import Engine

    host = Host(channels=1, rate=22050, directory=scratch, fade_in=False)
    host.install(Engine.compile("sound : Sig Float\nsound = 0.8 * white 1\n",
                                22050, scratch))
    buffer = (ctypes.c_float * 2048)()
    for _ in range(8):
        host.fill(buffer, 2048)
    assert all(host.band(k) == 0.0 for k in range(host.bands))
    host.close()


def test_the_editor_watches_the_bands_a_program_declares():
    """`band0` … `band7` are well-known names: declaring one is what
    switches the filter bank on."""
    from gestate.audioeditor import Workbench

    assert Workbench.BANDS == tuple(f"band{k}" for k in range(8))
    assert set(Workbench.BANDS) <= set(Workbench.WATCHED)
