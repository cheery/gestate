"""`python -m gestate.export` — the parity `spec/export.md` demands.

The exported artifact must render what the engine that made it
renders.  So this file is a miniature CLAP host in ctypes: it dlopens
the `.clap`, walks `clap_entry` → factory → descriptor → plugin,
activates at the exported rate, calls `process`, and holds the frames
against `run_native` of the same graph — the strongest statement a
plugin can be asked for, and the same shape of check `test_audiohost`
runs on the C host.

The struct mirrors below must match `shell/clap/src/abi.rs` field for
field, which is not a maintenance burden but the *point*: a drifted
layout fails here before it fails in somebody's DAW.
"""

from __future__ import annotations

import ctypes
import shutil
import tempfile
from ctypes import (POINTER, c_bool, c_char_p, c_double, c_float, c_int32,
                    c_int64, c_uint32, c_uint64, c_void_p)
from pathlib import Path

import pytest

needs_toolchain = pytest.mark.skipif(
    shutil.which("clang") is None or shutil.which("cargo") is None,
    reason="exporting needs clang and cargo")

RATE = 8000
SOURCE = "sound : Sig Float\nsound = sine 440.0 * 0.5\n"


# ── The CLAP ABI, mirrored ──────────────────────────────────────────────────


class Version(ctypes.Structure):
    _fields_ = [("major", c_uint32), ("minor", c_uint32),
                ("revision", c_uint32)]


class Entry(ctypes.Structure):
    _fields_ = [("clap_version", Version),
                ("init", ctypes.CFUNCTYPE(c_bool, c_char_p)),
                ("deinit", ctypes.CFUNCTYPE(None)),
                ("get_factory", ctypes.CFUNCTYPE(c_void_p, c_char_p))]


class Factory(ctypes.Structure):
    _fields_ = [("get_plugin_count", ctypes.CFUNCTYPE(c_uint32, c_void_p)),
                ("get_plugin_descriptor",
                 ctypes.CFUNCTYPE(c_void_p, c_void_p, c_uint32)),
                ("create_plugin",
                 ctypes.CFUNCTYPE(c_void_p, c_void_p, c_void_p, c_char_p))]


class Plugin(ctypes.Structure):
    _fields_ = [("desc", c_void_p),
                ("plugin_data", c_void_p),
                ("init", ctypes.CFUNCTYPE(c_bool, c_void_p)),
                ("destroy", ctypes.CFUNCTYPE(None, c_void_p)),
                ("activate", ctypes.CFUNCTYPE(c_bool, c_void_p, c_double,
                                              c_uint32, c_uint32)),
                ("deactivate", ctypes.CFUNCTYPE(None, c_void_p)),
                ("start_processing", ctypes.CFUNCTYPE(c_bool, c_void_p)),
                ("stop_processing", ctypes.CFUNCTYPE(None, c_void_p)),
                ("reset", ctypes.CFUNCTYPE(None, c_void_p)),
                ("process", ctypes.CFUNCTYPE(c_int32, c_void_p, c_void_p)),
                ("get_extension",
                 ctypes.CFUNCTYPE(c_void_p, c_void_p, c_char_p)),
                ("on_main_thread", ctypes.CFUNCTYPE(None, c_void_p))]


class AudioBuffer(ctypes.Structure):
    _fields_ = [("data32", POINTER(POINTER(c_float))),
                ("data64", c_void_p),
                ("channel_count", c_uint32),
                ("latency", c_uint32),
                ("constant_mask", c_uint64)]


class Process(ctypes.Structure):
    _fields_ = [("steady_time", c_int64),
                ("frames_count", c_uint32),
                ("transport", c_void_p),
                ("audio_inputs", c_void_p),
                ("audio_outputs", POINTER(AudioBuffer)),
                ("audio_inputs_count", c_uint32),
                ("audio_outputs_count", c_uint32),
                ("in_events", c_void_p),
                ("out_events", c_void_p)]


def _plugin_of(path: Path):
    """dlopen the `.clap` and walk it to a created, activated plugin."""
    lib = ctypes.CDLL(str(path))
    entry = Entry.in_dll(lib, "clap_entry")
    assert entry.init(str(path).encode())
    raw = entry.get_factory(b"clap.plugin-factory")
    assert raw, "no factory for the factory id"
    factory = ctypes.cast(raw, POINTER(Factory))
    assert factory.contents.get_plugin_count(raw) == 1
    plug_raw = factory.contents.create_plugin(raw, None, b"any")
    assert plug_raw, "the factory made no plugin"
    plugin = ctypes.cast(plug_raw, POINTER(Plugin))
    # `lib` rides along or the mapping is collected under the pointers.
    return lib, plug_raw, plugin.contents


# ── The parity ──────────────────────────────────────────────────────────────


@needs_toolchain
def test_the_exported_plugin_renders_what_the_engine_does(tmp_path):
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.export import export_clap

    out = tmp_path / "tone.clap"
    export_clap(SOURCE, out, rate=RATE, name="tone")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    # The audio-ports extension is what a real DAW configures buffers
    # from — a plugin without it loads and sits silent, so its absence
    # must fail here and not in somebody's session.
    ports = plugin.get_extension(plug_raw, b"clap.audio-ports")
    assert ports, "no clap.audio-ports extension"
    assert not plugin.activate(plug_raw, 44100.0, 32, 512), \
        "activated at a rate the graph is not truthful at"
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames = 256
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    proc = Process(steady_time=0, frames_count=frames, transport=None,
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=None, out_events=None)
    # Two blocks: the second proves the state advanced rather than
    # rewound — a plugin that re-seeds per call plays block one forever.
    through_plugin = []
    for _ in range(2):
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        through_plugin += list(buf)

    graph = graph_of(SOURCE, "", rate=RATE)
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, 2 * frames, block=frames))

    assert through_plugin == pytest.approx(offline)
    assert max(abs(x) for x in offline) > 0.4, "silent: nothing compared"

    plugin.stop_processing(plug_raw)
    plugin.deactivate(plug_raw)
    plugin.destroy(plug_raw)
