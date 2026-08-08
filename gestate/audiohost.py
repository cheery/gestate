"""The audio callback with no interpreter in it — `gestate/host.c`.

`audiolive` keeps the *language* out of the audio path and always did: per
block it did about 16 µs of control work against a 5,333 µs budget, and no
arithmetic at all.  What it could not escape is that a Python frame can be
**stopped** — the GIL for a slice, the cyclic collector for a hundred
milliseconds — and a thread that is stopped misses its deadline however
little it had to do.  `audiolive.deadline_scheduling` shortens both, and
shortening is not removing.

So the four things Python was still doing per block moved into C: which
engine is sounding, the crossfade across an edit, the control block, and
the frame count.  What is left here is *preparing and publishing*, which is
not on anybody's deadline:

    host = Host(channels=1, rate=48000)
    host.install(engine)                 # what is sounding now
    host.publish(rebuilt)                # taken between blocks, faded in

**The migration still happens in Python**, before publishing, and that is
a deliberate ordering: `audioengine.migrate` is a hundred lines of
dictionary work that has no business on a real-time thread.  It reads a
snapshot taken a block or so before the swap lands, so the new engine
starts from a state that is a few milliseconds stale — under a 40 ms
crossfade, during which the *old* engine is still sounding, which is why
that is affordable.

Nothing in `host.c` allocates, takes a lock, or calls back into Python.
"""

from __future__ import annotations

import ctypes
import subprocess
from pathlib import Path

RENDER = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                          ctypes.c_int64, ctypes.c_void_p)
MIX = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_int64, ctypes.c_void_p,
                       ctypes.c_double, ctypes.c_double)


class HostError(Exception):
    pass


_LIB = None


def library(directory=None):
    """`host.c`, compiled and loaded once.

    Built with the same `clang` the graphs are, into the caller's scratch
    directory — there is no wheel to ship a binary in, and a source file
    next to the module is one thing to keep in step rather than two.
    """
    global _LIB
    if _LIB is not None:
        return _LIB

    import tempfile

    source = Path(__file__).with_name("host.c")
    if not source.exists():                     # pragma: no cover
        raise HostError(f"{source} is missing")
    directory = Path(directory or tempfile.mkdtemp(prefix="gestate-host-"))
    directory.mkdir(parents=True, exist_ok=True)
    so = directory / "gestatehost.so"
    # **The device is compiled in when the machine has one to open.**
    # `alsa/asoundlib.h` is what `host.c` needs, and a machine without it
    # gets a host that renders but cannot open anything — which is the
    # same bargain every other backend here makes, and is why the probe is
    # a file test rather than a try/except around a build.
    alsa = Path("/usr/include/alsa/asoundlib.h").exists()
    flags = ["-DGESTATE_ALSA", "-lasound"] if alsa else []
    try:
        subprocess.run(["clang", "-O2", "-shared", "-fPIC", str(source),
                        *flags, "-lm", "-o", str(so)],
                       check=True, capture_output=True)
    except FileNotFoundError as exc:
        raise HostError("no `clang` to build the audio host with") from exc
    except subprocess.CalledProcessError as exc:      # pragma: no cover
        raise HostError(exc.stderr.decode("utf-8", "replace")) from exc

    lib = ctypes.CDLL(str(so))
    lib.gestate_host_new.restype = ctypes.c_void_p
    lib.gestate_host_new.argtypes = [ctypes.c_int, ctypes.c_int64,
                                     ctypes.c_void_p]
    for name in ("gestate_host_install", "gestate_host_publish"):
        fn = getattr(lib, name)
        fn.restype = None
        fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                       ctypes.c_void_p]
    lib.gestate_host_fill.restype = None
    lib.gestate_host_fill.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.c_int64]
    lib.gestate_host_run.restype = ctypes.c_int64
    lib.gestate_host_run.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                     ctypes.c_void_p, ctypes.c_int64,
                                     ctypes.c_int64]
    for name in ("gestate_host_frames", "gestate_host_position"):
        fn = getattr(lib, name)
        fn.restype = ctypes.c_int64
        fn.argtypes = [ctypes.c_void_p]
    for name in ("gestate_host_fading", "gestate_host_is_playing"):
        fn = getattr(lib, name)
        fn.restype = ctypes.c_int
        fn.argtypes = [ctypes.c_void_p]
    for name in ("gestate_host_playing", "gestate_host_watch_peak"):
        fn = getattr(lib, name)
        fn.restype = None
        fn.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.gestate_host_set_gain.restype = None
    lib.gestate_host_set_gain.argtypes = [ctypes.c_void_p, ctypes.c_double]
    lib.gestate_host_seek.restype = None
    lib.gestate_host_seek.argtypes = [ctypes.c_void_p, ctypes.c_int64]
    lib.gestate_host_loop.restype = None
    lib.gestate_host_loop.argtypes = [ctypes.c_void_p, ctypes.c_int64,
                                      ctypes.c_int64]
    lib.gestate_host_peak.restype = ctypes.c_float
    lib.gestate_host_peak.argtypes = [ctypes.c_void_p]
    lib.gestate_host_rms.restype = ctypes.c_float
    lib.gestate_host_rms.argtypes = [ctypes.c_void_p]
    lib.gestate_host_bands.restype = ctypes.c_int
    lib.gestate_host_bands.argtypes = []
    lib.gestate_host_watch_bands.restype = None
    lib.gestate_host_watch_bands.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                             ctypes.c_uint]
    lib.gestate_host_band.restype = ctypes.c_float
    lib.gestate_host_band.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.gestate_host_open.restype = ctypes.c_int
    lib.gestate_host_open.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                      ctypes.c_uint, ctypes.c_uint]
    lib.gestate_host_run_device.restype = ctypes.c_int64
    lib.gestate_host_run_device.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_int64, ctypes.c_int64]
    lib.gestate_host_has_device.restype = ctypes.c_int
    lib.gestate_host_has_device.argtypes = []
    lib.gestate_host_close_device.restype = None
    lib.gestate_host_close_device.argtypes = [ctypes.c_void_p]
    for name in ("gestate_host_stop", "gestate_host_free"):
        fn = getattr(lib, name)
        fn.restype = None
        fn.argtypes = [ctypes.c_void_p]
    _LIB = lib
    return lib


def _address(lib, name: str) -> int:
    """The address of a generated entry point, as a plain integer.

    `ctypes` hands back a callable; what `host.c` wants is the pointer, and
    taking it this way keeps the *only* thing crossing the boundary a
    number rather than a Python object with a lifetime.
    """
    return ctypes.cast(getattr(lib, name), ctypes.c_void_p).value


class Host:
    """A sounding instrument that C owns and Python steers.

    Holds the C side's `host*` and, so that nothing it points at is
    collected while it points at it, a reference to every engine that has
    been handed over.
    """

    def __init__(self, channels: int = 1, rate: int = 48000,
                 fade_ms: int = 40, controls: int = 0, directory=None,
                 fade_in: bool = True):
        self.lib = library(directory)
        self.channels = max(1, channels)
        self.rate = rate
        #: The control block the generated code reads its knobs out of.
        #: **Allocated once**, where the Python driver allocated one per
        #: block — an allocation in the audio path is against this file's
        #: whole reason for existing, and it fed the very collector whose
        #: pauses it was written to escape.
        self.control = (ctypes.c_int64 * max(1, controls))()
        fade = max(1, int(rate * fade_ms / 1000))
        self._host = self.lib.gestate_host_new(
            self.channels, fade, ctypes.cast(self.control, ctypes.c_void_p))
        if not self._host:                              # pragma: no cover
            raise HostError("could not make an audio host")
        #: Every engine handed over, kept alive: C holds raw pointers into
        #: their state buffers and their loaded libraries.
        self._kept: list = []
        self._open = False
        # **A session starts with the fader down.**  The first block is the
        # same step in the waveform as any other and pops the same way.
        # `fade_in=False` is for a caller with no device to pop — an
        # offline render, and the comparison that proves this renders what
        # the engine does.
        if not fade_in:
            self.set_gain(1.0)

    # -- what is sounding ----------------------------------------------------

    def install(self, engine) -> None:
        """Set what is sounding, before anything is playing."""
        self._kept.append(engine)
        self.lib.gestate_host_install(self._host, *self._slots(engine))

    def publish(self, engine) -> None:
        """Hand over an engine to be taken at the next block boundary.

        The state must already have been migrated into it — see the module
        docstring for why that is Python's job and not the render thread's.
        """
        self._kept.append(engine)
        self.lib.gestate_host_publish(self._host, *self._slots(engine))

    def _slots(self, engine) -> tuple:
        lib = engine.lib
        return (ctypes.c_void_p(_address(lib, "render_block_f32")),
                ctypes.c_void_p(_address(lib, "render_block_mix_f32")),
                ctypes.cast(engine.state, ctypes.c_void_p))

    # -- running -------------------------------------------------------------

    def fill(self, buffer, frames: int) -> None:
        """One block, for a caller that owns the clock — tests, and the
        offline comparison that proves this renders what Python did."""
        self.lib.gestate_host_fill(
            self._host, ctypes.cast(buffer, ctypes.c_void_p), frames)

    def run(self, fd: int, block: int, total: int = 0) -> int:
        """Render into `fd` until stopped.  **Releases the GIL**, which is
        the point: `ctypes` drops it around a foreign call, so the whole
        loop — every block, every swap, every fade — runs with Python
        stopped and cannot be interrupted by it."""
        scratch = (ctypes.c_float * (block * self.channels))()
        return self.lib.gestate_host_run(
            self._host, fd, ctypes.cast(scratch, ctypes.c_void_p),
            block, total)

    # -- the device C opens for itself --------------------------------------

    @property
    def has_device(self) -> bool:
        """Was a device backend compiled in?"""
        return bool(self.lib.gestate_host_has_device())

    def open(self, device: str = "default", latency_ms: int = 30) -> None:
        """Open the sound card **from C**, so no file descriptor, pipe or
        player process passes through Python at all.

        This is what the pipe was standing in for.  Handing a
        `subprocess.PIPE` across meant Python owned the write end while C
        wrote through it, which is two owners for one thing and hung the
        first time it was asked to finish.  A device the render loop opens
        and closes itself has one owner.
        """
        if not self.has_device:
            raise HostError(
                "this host was built without a device backend; install "
                "`libasound2-dev` and let it rebuild, or render to a file")
        code = self.lib.gestate_host_open(
            self._host, device.encode(), self.rate, max(1, latency_ms) * 1000)
        if code:
            raise HostError(
                f"could not open `{device}` "
                + ("(no such device)" if code == -1 else
                   "(it would not take float32 at this rate and channel "
                   "count)"))
        self._open = True

    def run_device(self, block: int = 256, total: int = 0) -> int:
        """Render into the open device until stopped.

        **Releases the GIL for the whole loop**, so a block, a swap and a
        fade all happen with Python unable to interrupt them.
        """
        scratch = (ctypes.c_float * (block * self.channels))()
        return self.lib.gestate_host_run_device(
            self._host, ctypes.cast(scratch, ctypes.c_void_p), block, total)

    def set_gain(self, gain: float) -> None:
        """Put the master fader somewhere directly — see `fade_in`."""
        self.lib.gestate_host_set_gain(self._host, float(gain))

    def stop(self) -> None:
        self.lib.gestate_host_stop(self._host)

    @property
    def frames(self) -> int:
        return self.lib.gestate_host_frames(self._host)

    @property
    def fading(self) -> bool:
        return bool(self.lib.gestate_host_fading(self._host))

    # -- the transport, which C owns now ------------------------------------

    @property
    def playing(self) -> bool:
        return bool(self.lib.gestate_host_is_playing(self._host))

    @playing.setter
    def playing(self, on: bool) -> None:
        self.lib.gestate_host_playing(self._host, 1 if on else 0)

    @property
    def position(self) -> int:
        """Where the engine has reached, in frames."""
        return self.lib.gestate_host_position(self._host)

    def seek(self, to: int) -> None:
        """Ask for a new instant.  **Taken at the next block boundary**,
        not here: writing the instant into a state the render thread is
        halfway through reading is the one race this design exists to
        avoid, and a block is 5 ms to wait."""
        self.lib.gestate_host_seek(self._host, max(0, int(to)))

    def loop(self, start: int | None, end: int | None) -> None:
        """Loop between two samples, or `loop(None, None)` for none."""
        self.lib.gestate_host_loop(self._host, int(start or 0),
                                   0 if not end else int(end))

    def watch_peak(self, on: bool) -> None:
        self.lib.gestate_host_watch_peak(self._host, 1 if on else 0)

    def peak(self) -> float:
        """The loudest sample since the last look, and clears it."""
        return float(self.lib.gestate_host_peak(self._host))

    def rms(self) -> float:
        """The same span as `peak`, averaged rather than maxed — and taken
        rather than read, for the reason the peak is: a meter shows what
        has happened since it last looked.

        A peak says whether it clipped; an RMS says how loud it sounded.
        Both ride the one walk `watch_peak` switches on.
        """
        return float(self.lib.gestate_host_rms(self._host))

    # -- the spectrum --------------------------------------------------------

    @property
    def bands(self) -> int:
        """How many bands the analyser reports."""
        return int(self.lib.gestate_host_bands())

    def watch_bands(self, on: bool) -> None:
        """Switch the filter bank on, tuned to this host's rate.

        Off unless a program asks — the same bargain the meter makes, and
        for the same reason: this is the one place with no time to spare.
        """
        self.lib.gestate_host_watch_bands(self._host, 1 if on else 0,
                                          self.rate)

    def band(self, k: int) -> float:
        """One band's level.  **Read, not taken** — unlike the peak, which
        is cleared on reading: a bar falls on its own release, so a look
        that emptied it would show a gap rather than a decay."""
        return float(self.lib.gestate_host_band(self._host, k))

    # -- the knobs -----------------------------------------------------------

    def set_control(self, index: int, value, kind: str = "Float") -> None:
        """Write one parameter into the block the generated code reads.

        **Pushed when it changes, not pulled every block.**  The Python
        driver called back into the host once per block per parameter; here
        a knob turn is a store, and the render thread reads whatever is
        there when it looks.  A `Float` is *reinterpreted* into its slot
        rather than converted, because the generated code bitcasts it back
        — `audiollvm.pack_control` makes the same choice and for the same
        reason: getting it backwards is silent.
        """
        import struct

        if not 0 <= index < len(self.control):
            raise HostError(f"no control slot {index}")
        if kind == "Float":
            self.control[index] = struct.unpack(
                "<q", struct.pack("<d", float(value)))[0]
        else:
            self.control[index] = int(value)

    def close(self) -> None:
        if getattr(self, "_host", None):
            if getattr(self, "_open", False):
                self.lib.gestate_host_close_device(self._host)
                self._open = False
            self.lib.gestate_host_free(self._host)
            self._host = None
        self._kept.clear()
