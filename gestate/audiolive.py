"""Play a synth — `spec/liveaudio.md` stage 4's other half.

The end of the chain the whole plan builds: source text, to a graph, to
LLVM IR, to machine code, to a sound card, in real time.

**Python is not in the audio path.**  Per block, the driver makes exactly
one call — `render_block_f32`, which fills the device's buffer in the
device's format, clamping as `audio.write()` does.  No arithmetic, no
allocation and no per-sample work happens in the interpreter, which is the
architecture's one rule: *the language never enters the audio callback.*
At 593× real time the engine has room to spare; what it must not acquire
is a garbage collector between it and the deadline.

Two backends, tried in that order:

* **`sounddevice`** — a genuine PortAudio callback, and the right answer
  for latency.  Used when it is installed.
* **a pipe to a system player** — `pw-play`, `paplay` or `aplay`, fed raw
  `float32`.  No third-party package at all, and the pipe's back-pressure
  is the clock: the player consumes at the sample rate and the writer
  blocks, so the engine runs exactly as fast as the sound does.

    python -m gestate.audiolive examples/audio/drums.ges --seconds 5
    python -m gestate.audiolive examples/audio/blip.ges --rate 48000
"""

from __future__ import annotations

import ctypes
import gc
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass

from .audioextract import extract
from .audiollvm import _slots, build, load

#: 256 frames at 48 kHz is 5.3 ms — small enough to feel immediate when
#: stage 5 starts changing the graph underneath, large enough that the
#: per-block Python call is nothing.
DEFAULT_BLOCK = 256
DEFAULT_RATE = 48000


class LiveError(Exception):
    pass


#: How much sound the *player* is allowed to hold.
#:
#: **This is the latency you feel**, and it is nothing to do with the
#: engine: a block is 5.3 ms at 48 kHz and the engine fills one in
#: microseconds, but the writer runs ahead until the player's buffer is
#: full, so a key pressed now is heard once that buffer drains.  `pw-play`
#: defaults to **100 ms** and a server may add its own on top — which is
#: how playing a keyboard came to feel a third of a second late.
#:
#: 30 ms is tight enough to play against and slack enough not to glitch.
#: Lower it if your machine can take it; the engine cannot be the reason
#: it cannot.
DEFAULT_LATENCY_MS = 30

#: The GIL slice, while sound is playing.  **This is what stops a rebuild
#: from garbling the sound**, and it is nothing the engine does wrong.
#:
#: The block itself is machine code, but the thread that asks for it is a
#: Python thread, and a rebuild is *seconds* of pure-Python front end on
#: another one — the compile, the placement, the score and the MIDI
#: instances are each a whole analysis of the program.  CPython hands the
#: GIL over only every `sys.getswitchinterval()` — 5 ms by default, which
#: is a block and a half at 48 kHz — and the convoy effect makes a waiting
#: thread wait several of those.
#:
#: Measured by auditioning `duet.ges` at 48 kHz, alternating the two
#: settings in one process: **519 blocks of 2,909 missed their 5.3 ms
#: deadline at 5 ms, and 13 of 4,641 at 1 ms**, with the 99th percentile
#: falling from 15.3 ms to 3.6 ms.  That is the tearing you hear on Ctrl-S.
#:
#: 1 ms rather than less because the interval is also what the *rebuild*
#: pays — about 15% here, and 0.1 ms cost 80% for no further gain.  It is a
#: process-wide setting, which is why it is scoped to `play`: a program
#: that is only rendering has no deadline to protect.
PLAYING_SWITCH_INTERVAL = 0.001

#: What the cyclic collector's generations are raised to while playing.
#:
#: **The GIL was only half of it.**  Shortening the slice fixed the
#: *contention* and left the *pauses*, because a collection is not
#: preemptible: it stops every thread, including the one with 5.3 ms to
#: fill a buffer.  A rebuild is where the garbage comes from — a front end
#: builds and drops a large graph of small objects, and reference counting
#: frees the acyclic majority at once while the cycles pile up for the
#: collector to find later, at a moment nobody chose.
#:
#: Measured on two cores, a different edit each rebuild, 750 blocks of
#: 5.33 ms, against the worst pause and the 99th percentile:
#:
#: | | worst | p99 | late |
#: |---|---|---|---|
#: | as it was | 99.5 ms | 75.5 ms | 45 |
#: | `freeze()` alone | 54.5 ms | 17.5 ms | 15 |
#: | **frozen, raised** | **15.4 ms** | **3.2 ms** | **14** |
#: | collector off | 0.0 ms | 0.0 ms | 0 |
#:
#: Off is perfect and is not an option: twelve edits leaked 44 MB and left
#: 368,245 cyclic objects for the eventual collection, so a long session
#: would page.  Frozen and raised is bounded — 14 MB over the same twelve —
#: and puts the 99th percentile comfortably inside one block, with the
#: player's 30 ms of latency to absorb what is left.
PLAYING_GC_THRESHOLD = (20000, 50, 50)


@contextmanager
def deadline_scheduling():
    """Shorten the GIL slice and calm the collector while a driver runs.

    `min`, so a caller that has already asked for something tighter keeps
    it, and nested players restore each other's setting rather than the
    default.

    **`freeze` before raising the thresholds.**  It moves everything alive
    right now into a generation that is never scanned again, and what is
    alive right now is the part that never dies: the preludes' syntax
    trees, `pipeline`'s analysis cache, the module table.  Without it every
    full collection walks all of that to prove none of it is garbage, which
    is most of the pause and all of it wasted.
    """
    previous = sys.getswitchinterval()
    sys.setswitchinterval(min(previous, PLAYING_SWITCH_INTERVAL))
    thresholds = gc.get_threshold()
    gc.collect()
    gc.freeze()
    gc.set_threshold(*PLAYING_GC_THRESHOLD)
    try:
        yield
    finally:
        sys.setswitchinterval(previous)
        gc.set_threshold(*thresholds)
        gc.unfreeze()

#: Raw `float32`, read from stdin, interleaved.  In preference order; the
#: first one on the machine wins.  Each spells its buffer differently —
#: milliseconds, bytes, microseconds — so the substitution is per player
#: rather than one number passed through.
PLAYERS = {
    "pw-play": ["pw-play", "--format=f32", "--rate={rate}",
                "--channels={channels}", "--latency={latency_ms}ms", "-"],
    "paplay": ["paplay", "--raw", "--format=float32le", "--rate={rate}",
               "--channels={channels}", "--latency={latency_bytes}"],
    "aplay": ["aplay", "-q", "-f", "FLOAT_LE", "-r", "{rate}",
              "-c", "{channels}", "-t", "raw",
              "--buffer-time={latency_us}", "-"],
}


def player_command(rate: int, prefer: str | None = None,
                   latency_ms: int = DEFAULT_LATENCY_MS,
                   channels: int = 1) -> list:
    """The command to pipe raw `float32` into, or raise saying there is none.

    `channels` is the *graph's*, not a preference: a `sound : Sig Stereo`
    produces two interleaved floats per frame and a player told to expect
    one would play them at twice the pitch, alternating ears.
    """
    # A frame of `float32` is four bytes a channel, which is the only
    # conversion any of these needs.
    fields = {"rate": rate, "latency_ms": latency_ms, "channels": channels,
              "latency_bytes": max(1, latency_ms * rate * 4 * channels // 1000),
              "latency_us": max(1000, latency_ms * 1000)}
    names = [prefer] if prefer else list(PLAYERS)
    for name in names:
        if name in PLAYERS and shutil.which(name.split()[0]):
            return [part.format(**fields) for part in PLAYERS[name]]
    if prefer:
        raise LiveError(f"no player `{prefer}` on this machine")
    raise LiveError(
        "no way to reach the sound card: none of "
        + ", ".join(PLAYERS) + " is installed, and `sounddevice` is not "
        "either.  Render to a file instead with `python -m gestate.audio`")


# ── The engine, as a thing that fills buffers ───────────────────────────────


@dataclass
class Engine:
    """A compiled graph and its state — one running instrument."""
    lib: object
    state: object
    graph: object
    frames: int = 0

    @classmethod
    def compile(cls, source: str, rate: int, directory) -> "Engine":
        # `graph_of` rather than `extract`: a program carrying its own
        # `score` is assembled with the music prelude and its piece, and a
        # graph built from the *other* assembly would have different
        # channels than the schedule writes to.  A synth with no score
        # still takes the plain path and pays nothing.
        from .audioperform import graph_of

        graph = graph_of(source, rate=rate)
        lib = load(build(graph, directory))
        # The crossfade's entry point: the same body, multiplying by a gain
        # that ramps `g0`→`g1` across the block and *adding* into the
        # buffer.  Two calls mix two programs in the engine — see
        # `Live._blend`, and `audiollvm._render_block`'s `mix`.
        lib.render_block_mix_f32.restype = None
        lib.render_block_mix_f32.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64,
            ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
        lib.render_block_f32.restype = None
        lib.render_block_f32.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_int64, ctypes.c_void_p]
        width = 8 * (1 + sum(_slots(graph, n) for n in graph.nodes))
        return cls(lib, ctypes.create_string_buffer(width), graph)

    @property
    def control_sources(self) -> list:
        """The parameters this instrument accepts, in buffer order."""
        return self.graph.control_sources()

    @property
    def channels(self) -> int:
        """How many interleaved floats one frame of this instrument is.

        The engine's, and asked of the engine rather than decided by the
        driver, because only the graph knows.  A driver reads it once when
        it starts and it must not change under one — see `Live.install`,
        which refuses the edit that would change it.
        """
        from .audiollvm import out_channels

        return out_channels(self.graph)

    def fill(self, buffer, frames: int, control=None, t: int = 0) -> None:
        """One call per block.  This is the entire audio path.

        `control(node_id, t)` is read once here, per parameter — a synth may
        declare several, and each is its own knob.  Packing them is a
        handful of integer stores, which is the most that may happen on
        this side of the callback.
        """
        from .audiollvm import pack_control

        sources = self.control_sources
        slots = (ctypes.c_int64 * max(1, len(sources)))()
        if sources:
            pack_control(self.graph, slots, sources,
                         control or (lambda _node, _t: 0), t)
        self.lib.render_block_f32(
            ctypes.cast(self.state, ctypes.c_void_p),
            address_of(buffer), frames,
            ctypes.cast(slots, ctypes.c_void_p))
        self.frames += frames

    def fill_mix(self, buffer, frames: int, control, t: int,
                 g0: float, g1: float) -> None:
        """One block, scaled by a ramp and **added** to what is there.

        The other half of a crossfade: the engine coming in is called with
        `0 → 1` and the one going out with `1 → 0`, into the same buffer,
        and the two complementary ramps sum to unity — measured, a constant
        through both comes back flat.
        """
        from .audiollvm import pack_control

        sources = self.control_sources
        slots = (ctypes.c_int64 * max(1, len(sources)))()
        if sources:
            pack_control(self.graph, slots, sources,
                         control or (lambda _node, _t: 0), t)
        self.lib.render_block_mix_f32(
            ctypes.cast(self.state, ctypes.c_void_p),
            address_of(buffer), frames,
            ctypes.cast(slots, ctypes.c_void_p), g0, g1)
        self.frames += frames

    def snapshot(self) -> tuple:
        from .audiollvm import unpack_state

        return unpack_state(self.graph, self.state.raw)

    def restore(self, values: list, t: int, lines=None) -> None:
        from .audiollvm import pack_state

        self.state.raw = pack_state(self.graph, values, t, lines)


# ── Live update — `spec/liveaudio.md` stage 5 ───────────────────────────────


#: How long an edit takes to fade in over the one it replaces, in
#: milliseconds.
#:
#: **Migration is not enough on its own**, and the two do different jobs.
#: `audioengine.migrate` carries a phase, a filter's memory and a delay
#: line across so that editing an instrument does not restart its
#: envelopes — deliberately *not* a crossfade, because a crossfade
#: restarts everything and that is the difference between editing an
#: instrument and replacing it.  What it cannot do is make the two agree
#: sample for sample at the seam: a changed coefficient, a node that is
#: new and starts at its `init`, a filter whose state means something
#: slightly different now.  The waveform steps, and a step is a click.
#:
#: So the state migrates *and* the output is faded across the join.  40 ms
#: is long enough that the steepest step becomes a slew the ear reads as
#: a change of tone rather than a tick, and short enough to feel immediate.
FADE_MS = 40


class Live:
    """A playing instrument that can be replaced without stopping.

    **Two clocks of a different kind run here**, and keeping them apart is
    the whole design.  Compiling a changed source takes ~400 ms — a
    gestate front end, an extraction and a `clang` — and that happens on a
    worker thread while the old engine keeps sounding.  Installing the
    result takes microseconds: read the running state out, migrate it by
    origin, write it into the new engine, swap the reference.  That part
    happens *between blocks*, on the thread that fills them.

    So an edit never stops the sound, and never blocks the deadline.
    """

    def __init__(self, engine: Engine, rate: int, directory,
                 fade_ms: int = FADE_MS):
        self.engine = engine
        self.rate = rate
        self.directory = directory
        #: Compiled-and-waiting, or an error to report.  One slot: a second
        #: edit while one is in flight replaces it, which is what a person
        #: typing means by it.
        self.pending: object = None
        self.generation = 0
        self.errors: list = []
        #: How many control slots the *player* was started with, or
        #: `None` when nobody has said — see `install`.  Told rather
        #: than read, because it is the host's allocation and this does
        #: not own one.
        self.controls: int | None = None
        #: The engine being faded out, and how many samples of it are
        #: left.  `None` and `0` the rest of the time, which is almost all
        #: of it — nothing here costs anything until an edit lands.
        self.leaving: object = None
        self.fading = 0
        #: `0` turns the crossfade off, and that is not only a setting.
        #:
        #: **The fade costs a property worth naming.**  `spec/liveaudio.md`
        #: says a swap to a graph extracted from the *same text* must be
        #: bit-identical to never having swapped — "the whole of
        #: migration's correctness in one comparison: any state dropped or
        #: misplaced shows up immediately instead of as a click somebody
        #: notices later".  Two engines mixed with complementary ramps are
        #: *inaudibly* the same and not *bitwise* the same: `a·g +
        #: a·(1−g)` rounds, measured at 1e-9.
        #:
        #: So the comparison is made with the fade off, where it is still
        #: exact, and the fade is checked separately for being smooth.
        #: Turning it off to test migration is not weakening the test — it
        #: is testing one thing at a time.
        self.fade_ms = max(0, fade_ms)
        self.fade_samples = max(1, int(rate * self.fade_ms / 1000))
        self._scratch: object = None

    @classmethod
    def start(cls, source: str, rate: int, directory,
              fade_ms: int = FADE_MS) -> "Live":
        return cls(Engine.compile(source, rate, directory), rate, directory,
                   fade_ms)

    def compile(self, source: str) -> None:
        """Build a new engine.  Slow, and never on the audio thread."""
        try:
            self.pending = Engine.compile(source, self.rate, self.directory)
        except Exception as exc:                        # noqa: BLE001
            # A synth that does not compile must not stop the one that is
            # playing — a typo mid-phrase is the ordinary case, not an
            # exceptional one.
            self.pending = LiveError(str(exc))

    def needs_restart(self, waiting) -> str | None:
        """Why this edit cannot be installed *in place*, or `None`.

        **One rule, because there are two drivers.**  The Python driver
        installs in `install` below and the C host installs in
        `audioeditor._publish`, and the channel check was written out
        twice — so when a second thing needed refusing, it went into one
        of them and the other went on accepting it.  That is the gap this
        file's own docstring warns about: *a second implementation of
        anything puts its bugs between them.*

        Two things are sized when playback starts and cannot be
        renegotiated between blocks:

        * **The output channels.**  A stereo graph filling a buffer cut
          for mono writes past the end of it, which is memory corruption
          rather than a wrong sound.
        * **The control block.**  `audiohost.Host` allocates it at
          construction and hands C the pointer there, so a graph wanting
          more slots than were reserved cannot be fed.  This was the
          unchecked one: adding a `voices` bank to a synth that had none
          installed a graph the host could not drive, the apply said
          *"rebuilt"*, the score never loaded, and nothing played.

        **Neither is grown, and neither is refused any more.**  Growing
        means a second pointer handed across while the audio thread is
        reading the first, which is a renegotiation not to attempt in the
        middle of a block.  Refusing meant telling somebody to quit and
        start the program again — which is asking them to do a thing the
        program can do better, since it knows the edit is good, knows
        exactly what is too small, and has a master fader.  So the
        answer is a sentence saying what is too small, and the caller
        fades out and builds the player again at the size that fits.
        """
        if waiting.channels != self.engine.channels:
            return (f"this edit takes the output from "
                    f"{self.engine.channels} channel(s) to "
                    f"{waiting.channels}")
        want, have = len(waiting.control_sources), self.controls
        if have is not None and want > have:
            return (f"this edit wants {want} control channel(s) and the "
                    f"player has room for {have}")
        return None

    def install(self) -> bool:
        """Hand the running state to a waiting engine.  Between blocks."""
        from .audioengine import State, migrate

        waiting, self.pending = self.pending, None
        if waiting is None:
            return False
        if isinstance(waiting, Exception):
            self.errors.append(str(waiting))
            return False

        # The Python driver allocates per block, so it has no
        # fixed room to run out of and `controls` stays `None`.
        bigger = self.needs_restart(waiting)
        if bigger is not None:
            self.errors.append(bigger)
            return False

        values, t, lines = self.engine.snapshot()
        carried = migrate(self.engine.graph, State(values, t, lines),
                          waiting.graph)
        # The ring buffers go across too, and `migrate` decides which: a
        # delay line keeps its buffer when its origin, its type **and its
        # length** all match, because the buffer's meaning is positional.
        waiting.restore(carried.values, carried.t, carried.lines)
        waiting.frames = self.engine.frames
        # **The old engine is kept, not dropped**, so its last few
        # milliseconds can be faded under the new one's first few.  It goes
        # on running from where it was; the two diverge, and that
        # divergence is exactly what is being smoothed over.
        self.leaving, self.fading = ((self.engine, self.fade_samples)
                                     if self.fade_ms else (None, 0))
        self.engine = waiting
        self.generation += 1
        return True

    @property
    def channels(self) -> int:
        return self.engine.channels

    def fill(self, buffer, frames: int, control=None, t: int = 0) -> None:
        self.install()
        if self.leaving is None:
            self.engine.fill(buffer, frames, control, t)
            return
        self._blend(buffer, frames, control, t)

    def _blend(self, buffer, frames: int, control, t: int) -> None:
        """Fade the engine that is leaving out from under the new one.

        **In the engine, not here.**  Both programs are rendered by
        generated code that multiplies by a ramp and accumulates, so the
        mix happens sample for sample in C: the buffer is cleared once,
        the arriving engine is called with a gain going `0 → 1` across the
        block, the leaving one with `1 → 0`, and their two ramps sum to
        unity.  Nothing in this method runs per sample, which is the rule
        the rest of this file is written to.

        **Linear, not equal-power.**  The two are almost the same signal —
        one program and an edit of it — and for correlated sources an
        equal-power law adds about 3 dB in the middle, which is a bump
        where the point was to have nothing happen at all.  Equal power is
        for uncorrelated material and this is the opposite case.

        The ramp is per *frame* rather than per sample, so the channels of
        a stereo pair are never faded by different amounts — that is an
        image that wanders, and it would be audible exactly where the fade
        is meant not to be.  `audiollvm` computes it once and applies it to
        every channel of the frame.
        """
        import ctypes

        step = self.fade_samples
        done = step - self.fading
        # Where the ramp is at the first and last frame of *this* block.
        # A fade is 40 ms and a block is often less, so it has to pick up
        # where it left off rather than restart — otherwise it never ends.
        # `a1` unclamped on purpose — see `audiollvm`'s ramp, which clamps
        # per sample so a fade shorter than a block finishes inside it.
        a0 = min(1.0, done / step)
        a1 = (done + frames) / step

        ctypes.memset(address_of(buffer), 0,
                      frames * self.channels * ctypes.sizeof(ctypes.c_float))
        self.engine.fill_mix(buffer, frames, control, t, a0, a1)
        self.leaving.fill_mix(buffer, frames, control, t, 1.0 - a0, 1.0 - a1)

        self.fading = max(0, self.fading - frames)
        if self.fading == 0:
            self.leaving = None


# ── Backends ────────────────────────────────────────────────────────────────


def play_through_pipe(engine: Engine, seconds: float | None, rate: int,
                      block: int, command: list, progress=None,
                      control=None, should_stop=None) -> int:
    """Feed a player process, blocking on the pipe.

    The pipe *is* the clock: the player drains at the sample rate, so the
    write blocks and the engine advances in step with the sound.  Nothing
    here has to sleep or measure time.

    `should_stop`, if given, is asked once per block — see `play` for why a
    driver that cannot be asked to stop is a crash rather than a hang.
    """
    channels = channels_of(engine)
    buffer = (ctypes.c_float * (block * channels))()
    total = None if seconds is None else int(seconds * rate)
    written = 0
    stopping = should_stop or (lambda: False)
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        while (total is None or written < total) and not stopping():
            frames = block if total is None else min(block, total - written)
            # The control-rate parameters, read once per block — which is
            # what "control rate" means.  A slider in the environment is
            # exactly this callable, and `control(node_id, t)` is asked once
            # per parameter (`spec/liveaudio.md` stage 6).
            engine.fill(buffer, frames, control, written)
            # Sliced by *items*, not bytes: a `memoryview` of a ctypes
            # array is typed, so its indices are items.  Getting that wrong
            # re-sent whatever the buffer still held from the block before,
            # which is a stutter at the end of every finite render.  An item
            # is one channel of one frame, hence the multiply.
            proc.stdin.write(bytes(memoryview(buffer)[:frames * channels]))
            written += frames
            if progress is not None:
                progress(written)
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
        proc.wait()
    return written


def play_through_sounddevice(engine, seconds: float | None, rate: int,
                             block: int, device=None, control=None,
                             latency_ms: int = DEFAULT_LATENCY_MS,
                             should_stop=None) -> int:
    """A real PortAudio callback — the low-latency path.

    Worth having over the pipe by an order of magnitude: the pipe's delay
    is whatever the *player* buffers, which `pw-play` sets to 100 ms and a
    server may add to, while this is the device's own.

    **A callback may not raise.**  PortAudio calls it from its own thread
    through cffi, so an exception is printed and swallowed and the stream
    goes on producing silence — which is how a missing attribute here read
    as "the synth stopped working" rather than as a traceback anyone could
    act on.  So the position is asked for by a name every driver has, and
    a failure stops the stream rather than haunting it.
    """
    import sounddevice                                  # noqa: PLC0415

    failure = []

    def callback(out, frames, _time, _status):
        try:
            engine.fill(out, frames, control, position_of(engine))
        except Exception as exc:                        # noqa: BLE001
            failure.append(exc)
            raise sounddevice.CallbackAbort from exc

    stream = sounddevice.RawOutputStream(
        samplerate=rate, blocksize=block, device=device,
        channels=channels_of(engine), dtype="float32",
        latency=latency_ms / 1000.0, callback=callback)
    stopping = should_stop or (lambda: False)
    with stream:
        if seconds is None:
            while not failure and not stopping():
                sounddevice.sleep(100)
        else:
            # Woken in slices rather than slept through, so a window
            # closing does not have to wait out the whole render.
            left = int(seconds * 1000)
            while left > 0 and not failure and not stopping():
                sounddevice.sleep(min(100, left))
                left -= 100
    if failure:
        raise LiveError(f"the audio callback failed: {failure[0]}")
    return position_of(engine)


def address_of(buffer):
    """The address of a block buffer, whichever kind it is.

    The pipe driver allocates a `ctypes` array; **PortAudio hands the
    callback a cffi buffer**, and `ctypes.cast` refuses that with
    `TypeError: wrong type`.  Raised inside a callback that may not raise,
    it became silence rather than a traceback — see
    `play_through_sounddevice`.

    `c_char.from_buffer` accepts anything writable that supports the buffer
    protocol, which both of them do.
    """
    import ctypes

    try:
        return ctypes.cast(buffer, ctypes.c_void_p)
    except (ctypes.ArgumentError, TypeError):
        return ctypes.c_void_p(
            ctypes.addressof(ctypes.c_char.from_buffer(buffer)))


def channels_of(engine) -> int:
    """How many interleaved floats a driver should expect per frame.

    Asked of the engine for the reason `position_of` is: a `Transport` and
    a `Live` and a bare `Engine` are all things a driver fills, and only
    the innermost one knows the graph.  Defaults to 1 for anything that
    does not answer — a test double filling a mono buffer, which is what
    every driver test but one is.
    """
    return getattr(engine, "channels", 1) or 1


def position_of(engine) -> int:
    """How far a driver has got, whatever kind of driver it is.

    `Engine` counts `frames`; a `Transport` has a `position` it may rewind.
    Both are "the instant being filled", which is what a callback needs and
    what a note is stamped with — so it is asked for once, here, rather
    than by name at three call sites that then disagree.
    """
    return getattr(engine, "position", None) or getattr(engine, "frames", 0)


class MasterFader:
    """Fade the whole render in at the start and out at the end.

    The first sample of a synth is a step from silence to wherever the
    waveform happens to begin, and the last is a step back — and a step is
    a click, the same fact `Live`'s crossfade exists for.  The same
    machinery serves: inside a fade the block is zeroed and the engine
    *adds* into it through `render_block_mix_f32`'s per-frame ramp, so
    nothing here runs per sample.  Outside a fade the plain entry point is
    called and this costs two comparisons per block.

    The endpoints are handed over unclamped, as `Live._blend` hands its
    own — the generated ramp clamps per sample, so a corner that falls
    inside a block lands on the sample it belongs to rather than being
    smeared across the block.

    The fade-out needs to know where the end is, so an open-ended play
    (`--seconds` omitted) fades in and then stands clear; there is nothing
    to anchor a fade-out to when the end is a Ctrl-C.
    """

    def __init__(self, engine, rate: int, seconds: float | None,
                 fade_ms: int = FADE_MS):
        self.engine = engine
        self.span = max(1, int(rate * fade_ms / 1000))
        self.total = None if seconds is None else int(seconds * rate)

    @property
    def channels(self) -> int:
        return channels_of(self.engine)

    @property
    def position(self) -> int:
        return position_of(self.engine)

    def _level(self, t: int) -> float:
        """The fader at frame `t`, unclamped.  `min` of two lines is
        concave, so a block whose endpoints are both at or above 1 is at
        full level throughout — the test `fill` steers by."""
        rise = t / self.span
        if self.total is None:
            return rise
        return min(rise, (self.total - t) / self.span)

    def fill(self, buffer, frames: int, control=None, t: int = 0) -> None:
        g0 = self._level(t)
        g1 = self._level(t + frames)
        if g0 >= 1.0 and g1 >= 1.0:
            self.engine.fill(buffer, frames, control, t)
            return
        ctypes.memset(address_of(buffer), 0,
                      frames * self.channels * ctypes.sizeof(ctypes.c_float))
        self.engine.fill_mix(buffer, frames, control, t, g0, g1)


def play(source: str, seconds: float | None = None, rate: int = DEFAULT_RATE,
         block: int = DEFAULT_BLOCK, prefer: str | None = None,
         command: list | None = None, progress=None, engine=None,
         control=None, latency_ms: int = DEFAULT_LATENCY_MS,
         should_stop=None, fade_ms: int = 0) -> tuple:
    """Compile and play.  Returns `(frames, backend)`.

    **`should_stop` is what makes closing the window safe**, and its
    absence was a crash rather than a hang.  A driver given no duration
    plays forever, so a host that wanted it to stop could only set a flag
    nobody read, fail to join the thread, and let the interpreter finalise
    with that thread still inside `render_block_f32` — writing into a
    `ctypes` buffer, or calling back into a Python that is being torn down.
    Sometimes it got away with it.  Asked once per block, both drivers
    return, the thread joins, and the stream and the player close on the
    way out.

    Held under `deadline_scheduling` for the whole session, because from
    here on there is a thread in this process with a deadline of a few
    milliseconds and the rest of the program does not know it.

    **No `command` means the sound card, by whichever of two doors is
    open** — `sounddevice` if it imports, a system player if it does not.
    Worth stating because it is what a caller gets by *saying nothing*, and
    a caller that did not mean to make a noise has to know that silence is
    not the default.  `test/conftest.py` shuts both for the test suite, and
    says what it cost to find out that shutting one is not enough.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as directory, deadline_scheduling():
        engine = engine or Engine.compile(source, rate, directory)
        # `0` keeps the stream bit-identical to the oracle, which is what
        # the tests compare and the default an API caller gets; the CLI
        # asks for the fade.  A `Live` has no `fill_mix` — its own fade is
        # the crossfade — so `--watch` passes through unfaded.
        if fade_ms and hasattr(engine, "fill_mix"):
            engine = MasterFader(engine, rate, seconds, fade_ms)

        if command is None and prefer is None:
            try:
                return (play_through_sounddevice(
                            engine, seconds, rate, block, control=control,
                            latency_ms=latency_ms, should_stop=should_stop),
                        "sounddevice")
            except ImportError:
                pass
        cmd = command or player_command(rate, prefer, latency_ms,
                                        channels_of(engine))
        frames = play_through_pipe(engine, seconds, rate, block, cmd,
                                   progress, control, should_stop)
        return frames, cmd[0]


class SourceWatcher:
    """Has the file changed since last time?  If so, rebuild.

    Separated from the thread that runs it so that the interesting half —
    noticing an edit and starting a compile — is a function that can be
    called once and asserted on.  What is left in the thread is `sleep`.
    """

    def __init__(self, path, live: Live | None = None):
        from pathlib import Path

        self.path = Path(path)
        self.live = live
        self.stamp = self._stamp()

    def _stamp(self):
        try:
            info = self.path.stat()
            return (info.st_mtime_ns, info.st_size)
        except OSError:
            return None                 # mid-save; look again shortly

    def check(self) -> bool:
        """`True` if an edit was seen and a rebuild started."""
        now = self._stamp()
        if now is None or now == self.stamp:
            return False
        self.stamp = now
        try:
            source = self.path.read_text()
        except OSError:
            return False
        self.live.compile(source)
        return True


def watch(path, seconds: float | None = None, rate: int = DEFAULT_RATE,
          block: int = DEFAULT_BLOCK, prefer: str | None = None,
          command: list | None = None, report=None,
          interval: float = 0.15, control=None, should_stop=None,
          fade_ms: int = 0) -> tuple:
    """Play a file and recompile it whenever it changes.

    The loop that live coding is for: edit the synth in an editor, save,
    and the sound changes without stopping.  A node whose origin and shape
    survive the edit keeps its state, so an oscillator keeps its phase and
    an envelope is not restarted — see `audioengine.migrate`.

    `should_stop` is asked once a block, as `play`'s is — which `watch` did
    not pass on, so the only way to end one was to give it a duration and
    hope.  A caller that knows when it has seen enough can say so, and a
    *test* that is waiting for a rebuild can wait for the rebuild rather
    than for a stopwatch: a build is ~400 ms on an idle machine and much
    longer on a busy one, so a fixed duration is a race that a loaded
    machine loses.
    """
    import tempfile
    import threading
    from pathlib import Path

    path = Path(path)
    report = report or (lambda _message: None)

    with tempfile.TemporaryDirectory() as directory:
        # The baseline is taken **before** the first build, not after.  A
        # build takes ~400 ms, and a save inside that window would
        # otherwise be folded into the starting stamp and lost — save
        # twice quickly and the second one vanishes.  Taking it early can
        # instead cost one redundant rebuild, which is the right way round.
        watcher = SourceWatcher(path)
        live = Live.start(path.read_text(), rate, directory)
        watcher.live = live
        stop = threading.Event()

        def poll():
            while not stop.wait(interval):
                watcher.check()

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()
        try:
            generation = 0

            def progress(_written):
                nonlocal generation
                while live.errors:
                    report("gestate: " + live.errors.pop(0))
                if live.generation != generation:
                    generation = live.generation
                    report(f"reloaded {path} (edit {generation})")

            frames, backend = play(None, seconds, rate, block, prefer,
                                   command, progress, engine=live,
                                   control=control, should_stop=should_stop,
                                   fade_ms=fade_ms)
        finally:
            stop.set()
    return frames, backend


# ── CLI ─────────────────────────────────────────────────────────────────────


def _open_midi(source: str, rate: int, port: str | None, span: str | None):
    """Bind the synth's control channels to CC numbers and start listening.

    Separate from `main` because the interesting half is the binding, and a
    function that returns `(controls, listener)` can be asserted on where a
    block inside an argument parser cannot.
    """
    from .audioextract import extract
    from .audiomidi import Controls, Listener, MidiError
    from .audiospans import controls as sites

    graph = extract(source, rate=rate)
    if not graph.control_sources():
        raise LiveError("this synth declares no control channel, so there "
                        "is nothing for MIDI to turn")

    spans = None
    if span:
        try:
            lo, hi = (int(v) for v in span.split(":"))
        except ValueError:
            raise LiveError(f"`--midi-span {span}` is not `LO:HI`") from None
        # One range for every knob: a per-knob range would want syntax in
        # the language to say it, and nothing has asked for that yet.
        spans = {s.name: (lo, hi) for s in sites(source, rate=rate)}

    controls = Controls.bind(graph, source, spans=spans)
    try:
        return controls, Listener(controls, port).start()
    except MidiError as exc:
        raise LiveError(str(exc)) from None


def main(argv=None) -> int:
    """Retired — `audioperform` plays, and the live room is an editor."""
    import sys

    print("gestate: the `gestate.audiolive` CLI is retired —\n"
          "  python -m gestate.audioperform <file> [--midi]   plays it;\n"
          "  python -m gestate.workbench    <file>            edits it "
          "while it plays.\n"
          "The engine and the drivers live on here; every player still "
          "uses them.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
