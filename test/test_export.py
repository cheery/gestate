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


class EventHeader(ctypes.Structure):
    _fields_ = [("size", c_uint32), ("time", c_uint32),
                ("space_id", ctypes.c_uint16), ("type_", ctypes.c_uint16),
                ("flags", c_uint32)]


class Transport(ctypes.Structure):
    _fields_ = [("header", EventHeader),
                ("flags", c_uint32),
                ("song_pos_beats", c_int64),
                ("song_pos_seconds", c_int64),
                ("tempo", c_double),
                ("tempo_inc", c_double),
                ("loop_start_beats", c_int64),
                ("loop_end_beats", c_int64),
                ("loop_start_seconds", c_int64),
                ("loop_end_seconds", c_int64),
                ("bar_start", c_int64),
                ("bar_number", c_int32),
                ("tsig_num", ctypes.c_uint16),
                ("tsig_denom", ctypes.c_uint16)]


IS_PLAYING = 1 << 4


class OStream(ctypes.Structure):
    _fields_ = [("ctx", c_void_p),
                ("write", ctypes.CFUNCTYPE(c_int64, c_void_p, c_void_p,
                                           c_uint64))]


class IStream(ctypes.Structure):
    _fields_ = [("ctx", c_void_p),
                ("read", ctypes.CFUNCTYPE(c_int64, c_void_p, c_void_p,
                                          c_uint64))]


class StateExt(ctypes.Structure):
    _fields_ = [("save", ctypes.CFUNCTYPE(c_bool, c_void_p, c_void_p)),
                ("load", ctypes.CFUNCTYPE(c_bool, c_void_p, c_void_p))]


def _state_roundtrip(plugin, plug_raw, plugin2, plug2_raw):
    """Save one instance's state, load it into another."""
    raw = plugin.get_extension(plug_raw, b"clap.state")
    assert raw, "no clap.state extension"
    state = ctypes.cast(raw, POINTER(StateExt)).contents

    saved = bytearray()

    def write(_ctx, buf, size):
        saved.extend(ctypes.string_at(buf, size))
        return size

    out = OStream(ctx=None,
                  write=ctypes.CFUNCTYPE(c_int64, c_void_p, c_void_p,
                                         c_uint64)(write))
    assert state.save(plug_raw, ctypes.cast(ctypes.pointer(out),
                                            c_void_p))
    assert saved, "an empty save"

    cursor = [0]

    def read(_ctx, buf, size):
        take = min(int(size), len(saved) - cursor[0])
        ctypes.memmove(buf, bytes(saved[cursor[0]:cursor[0] + take]),
                       take)
        cursor[0] += take
        return take

    raw2 = plugin2.get_extension(plug2_raw, b"clap.state")
    state2 = ctypes.cast(raw2, POINTER(StateExt)).contents
    ins = IStream(ctx=None,
                  read=ctypes.CFUNCTYPE(c_int64, c_void_p, c_void_p,
                                        c_uint64)(read))
    assert state2.load(plug2_raw, ctypes.cast(ctypes.pointer(ins),
                                              c_void_p)), \
        "the state did not load"


class ParamInfo(ctypes.Structure):
    _fields_ = [("id", c_uint32), ("flags", c_uint32),
                ("cookie", c_void_p),
                ("name", ctypes.c_char * 256),
                ("module", ctypes.c_char * 1024),
                ("min_value", c_double), ("max_value", c_double),
                ("default_value", c_double)]


class Params(ctypes.Structure):
    _fields_ = [("count", ctypes.CFUNCTYPE(c_uint32, c_void_p)),
                ("get_info", ctypes.CFUNCTYPE(c_bool, c_void_p, c_uint32,
                                              POINTER(ParamInfo))),
                ("get_value", ctypes.CFUNCTYPE(c_bool, c_void_p, c_uint32,
                                               POINTER(c_double))),
                ("value_to_text",
                 ctypes.CFUNCTYPE(c_bool, c_void_p, c_uint32, c_double,
                                  c_char_p, c_uint32)),
                ("text_to_value",
                 ctypes.CFUNCTYPE(c_bool, c_void_p, c_uint32, c_char_p,
                                  POINTER(c_double))),
                ("flush", ctypes.CFUNCTYPE(None, c_void_p, c_void_p,
                                           c_void_p))]


class ParamValueEvent(ctypes.Structure):
    _fields_ = [("header", EventHeader),
                ("param_id", c_uint32),
                ("cookie", c_void_p),
                ("note_id", c_int32),
                ("port_index", ctypes.c_int16),
                ("channel", ctypes.c_int16),
                ("key", ctypes.c_int16),
                ("value", c_double)]


class InputEvents(ctypes.Structure):
    _fields_ = [("ctx", c_void_p),
                ("size", ctypes.CFUNCTYPE(c_uint32, c_void_p)),
                ("get", ctypes.CFUNCTYPE(c_void_p, c_void_p, c_uint32))]


class NoteEvent(ctypes.Structure):
    _fields_ = [("header", EventHeader),
                ("note_id", c_int32),
                ("port_index", ctypes.c_int16),
                ("channel", ctypes.c_int16),
                ("key", ctypes.c_int16),
                ("velocity", c_double)]


def _note_event(type_: int, key: int, velocity: float):
    """An event list holding one NOTE_ON (0) or NOTE_OFF (1)."""
    ev = NoteEvent()
    ev.header.size = ctypes.sizeof(NoteEvent)
    ev.header.time = 0
    ev.header.space_id = 0
    ev.header.type_ = type_
    ev.header.flags = 0
    ev.note_id = -1
    ev.port_index = 0
    ev.channel = 0
    ev.key = key
    ev.velocity = velocity

    size_cb = ctypes.CFUNCTYPE(c_uint32, c_void_p)(lambda _ctx: 1)
    get_cb = ctypes.CFUNCTYPE(c_void_p, c_void_p, c_uint32)(
        lambda _ctx, _i: ctypes.cast(ctypes.pointer(ev), c_void_p).value)
    events = InputEvents(ctx=None, size=size_cb, get=get_cb)
    return events, (ev, size_cb, get_cb)


def _event_list(*events):
    """A host event list over any mix of already-built event structs."""
    kept = list(events)
    size_cb = ctypes.CFUNCTYPE(c_uint32, c_void_p)(
        lambda _ctx: len(kept))
    get_cb = ctypes.CFUNCTYPE(c_void_p, c_void_p, c_uint32)(
        lambda _ctx, i: ctypes.cast(ctypes.pointer(kept[i]),
                                    c_void_p).value)
    return InputEvents(ctx=None, size=size_cb, get=get_cb), \
        (kept, size_cb, get_cb)


def _note_struct(type_: int, key: int, velocity: float) -> NoteEvent:
    ev = NoteEvent()
    ev.header.size = ctypes.sizeof(NoteEvent)
    ev.header.time = 0
    ev.header.space_id = 0
    ev.header.type_ = type_
    ev.header.flags = 0
    ev.note_id = -1
    ev.port_index = 0
    ev.channel = 0
    ev.key = key
    ev.velocity = velocity
    return ev


def _param_struct(param_id: int, value: float) -> "ParamValueEvent":
    ev = ParamValueEvent()
    ev.header.size = ctypes.sizeof(ParamValueEvent)
    ev.header.time = 0
    ev.header.space_id = 0
    ev.header.type_ = 5
    ev.header.flags = 0
    ev.param_id = param_id
    ev.note_id = -1
    ev.port_index = -1
    ev.channel = -1
    ev.key = -1
    ev.value = value
    return ev


def _one_event(param_id: int, value: float):
    """A host's event list holding a single PARAM_VALUE."""
    ev = ParamValueEvent()
    ev.header.size = ctypes.sizeof(ParamValueEvent)
    ev.header.time = 0
    ev.header.space_id = 0                    # CLAP_CORE_EVENT_SPACE_ID
    ev.header.type_ = 5                       # CLAP_EVENT_PARAM_VALUE
    ev.header.flags = 0
    ev.param_id = param_id
    ev.note_id = -1
    ev.port_index = -1
    ev.channel = -1
    ev.key = -1
    ev.value = value

    size_cb = ctypes.CFUNCTYPE(c_uint32, c_void_p)(lambda _ctx: 1)
    get_cb = ctypes.CFUNCTYPE(c_void_p, c_void_p, c_uint32)(
        lambda _ctx, _i: ctypes.cast(ctypes.pointer(ev), c_void_p).value)
    events = InputEvents(ctx=None, size=size_cb, get=get_cb)
    # Everything the callbacks close over rides along, or it is
    # collected while the plugin walks the list.
    return events, (ev, size_cb, get_cb)


class Process(ctypes.Structure):
    _fields_ = [("steady_time", c_int64),
                ("frames_count", c_uint32),
                ("transport", POINTER(Transport)),
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
    # No transport at all: a free-running host, in which an instrument
    # simply plays — which is also what keeps this comparison honest
    # against `run_native`, which has no transport either.
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


@needs_toolchain
def test_a_stereo_program_fills_both_channel_pointers(tmp_path):
    """The engine speaks interleaved frames; a CLAP port is one pointer
    per channel — the deinterleave is shipped, and this is its test.

    Left and right must differ (a pan is the point) and each must be
    its half of `run_native`'s interleaved stream.
    """
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.export import export_clap

    source = "sound : Sig Stereo\nsound = pan 0.3 (sine 440.0)\n"
    out = tmp_path / "wide.clap"
    export_clap(source, out, rate=RATE, name="wide")
    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames = 128
    left = (c_float * frames)()
    right = (c_float * frames)()
    chans = (POINTER(c_float) * 2)(
        ctypes.cast(left, POINTER(c_float)),
        ctypes.cast(right, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=2,
                       latency=0, constant_mask=0)
    proc = Process(steady_time=0, frames_count=frames, transport=None,
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=None, out_events=None)
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1

    graph = graph_of(source, "", rate=RATE)
    with tempfile.TemporaryDirectory() as d:
        pairs = list(run_native(graph, d, frames, block=frames))
    assert list(left) == pytest.approx([p[0] for p in pairs]), \
        "left is not left"
    assert list(right) == pytest.approx([p[1] for p in pairs]), \
        "right is not right"
    assert list(left) != pytest.approx(list(right)), "the pan did nothing"
    plugin.destroy(plug_raw)


@needs_toolchain
def test_one_plugin_is_honest_at_several_rates(tmp_path):
    """Exported at two rates, the plugin carries two whole graphs and
    `activate` picks the one the host names — each rendering exactly
    what the engine renders *at that rate*, and every other rate still
    refused.
    """
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.export import export_clap

    out = tmp_path / "tone.clap"
    export_clap(SOURCE, out, rate=(8000, 12000), name="tone")
    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)

    frames = 256
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    proc = Process(steady_time=0, frames_count=frames, transport=None,
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=None, out_events=None)

    assert not plugin.activate(plug_raw, 44100.0, 32, 512), \
        "activated at a rate the plugin does not carry"
    for rate in (8000, 12000):
        assert plugin.activate(plug_raw, float(rate), 32, 512), rate
        assert plugin.start_processing(plug_raw)
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        got = list(buf)
        graph = graph_of(SOURCE, "", rate=rate)
        with tempfile.TemporaryDirectory() as d:
            want = list(run_native(graph, d, frames, block=frames))
        assert got == pytest.approx(want), f"wrong sound at {rate} Hz"
        plugin.stop_processing(plug_raw)
        plugin.deactivate(plug_raw)
    plugin.destroy(plug_raw)


@needs_toolchain
def test_beat_is_the_renderers_own_and_the_daw_is_the_renderer(tmp_path):
    """`beat` and `beatRate`, supplied by the transport — the context
    contract's clause 1, and `tempoChan`'s retirement in force.

    The program names `beat` and `beatRate` and declares its own
    `bpm`; nothing in it mentions a host.  Free-running, it conducts
    itself at its declared 120.  Under a transport with a beats
    timeline it plays the *session's* clock: `beatRate` is the DAW's
    tempo in beats a second, and `beat` is the transport's position
    continued sample-accurately through the block — one block late,
    which is the engine's own control-rate semantics.  The supply
    channels are descriptor-declared slots, never parameters.
    """
    from gestate.export import export_clap

    source = ("bpm : Int\nbpm = 120\n"
              "\nsound : Sig Float\n"
              "sound = 0.01 * beatRate + 0.001 * beat\n")
    out = tmp_path / "beaten.clap"
    export_clap(source, out, rate=RATE, name="beaten")
    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)

    raw = plugin.get_extension(plug_raw, b"clap.params")
    params = ctypes.cast(raw, POINTER(Params)).contents
    for i in range(params.count(plug_raw)):
        info = ParamInfo()
        assert params.get_info(plug_raw, i, ctypes.byref(info))
        assert not info.name.startswith(b"beat"), \
            "the host clock leaked into the parameter list"

    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)
    frames = 64
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)

    # Free-running: its own conductor at the declared 120 — beatRate
    # 2.0 beats a second, beat ramping from zero.
    proc = Process(steady_time=0, frames_count=frames, transport=None,
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=None, out_events=None)
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
    own = [0.01 * 2.0 + 0.001 * (2.0 * n / RATE) for n in range(frames)]
    assert list(buf) == pytest.approx(own), \
        "free-running, the program is not its own conductor"

    # Under a transport: bar 3 of a 90 bpm session (beat 8, 1.5 bps).
    transport = Transport()
    transport.flags = IS_PLAYING | (1 << 0) | (1 << 1)
    transport.tempo = 90.0
    transport.song_pos_beats = 8 << 31
    proc.transport = ctypes.pointer(transport)
    # One block for the `:::` initials to hand over to the channels —
    # only the *first* write is masked by them; every later one lands
    # on its own block.
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
    # The line is anchored at this block's own start (t = 128):
    # beat = 8 + 1.5·(n − 128)/rate across n = 128… .
    want = [0.01 * 1.5 + 0.001 * (8.0 + 1.5 * (n - 2 * frames) / RATE)
            for n in range(2 * frames, 3 * frames)]
    assert list(buf) == pytest.approx(want, rel=1e-4), \
        "beat is not the transport's"
    plugin.destroy(plug_raw)


@needs_toolchain
def test_the_transport_is_followed_and_stop_means_rewind(tmp_path):
    """Play a block; stop — silence; play again — the *same* block.

    The replay being byte-identical to the first play is the whole
    rewind claim in one equality: the rising edge zeroed the state, and
    a zeroed state is the piece's top.  A synth whose second play
    continued mid-phrase, or drifted by one block of retained filter
    memory, fails here.
    """
    from gestate.export import export_clap

    out = tmp_path / "tone.clap"
    export_clap(SOURCE, out, rate=RATE, name="tone")
    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames = 200
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    transport = Transport()
    proc = Process(steady_time=0, frames_count=frames,
                   transport=ctypes.pointer(transport),
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=None, out_events=None)

    def block(playing: bool) -> list:
        transport.flags = IS_PLAYING if playing else 0
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        return list(buf)

    first = block(playing=True)
    assert max(abs(x) for x in first) > 0.4, "silent on play"
    second = block(playing=True)
    assert second != first, "the piece did not advance while playing"
    assert block(playing=False) == [0.0] * frames, "not silent on stop"
    assert block(playing=True) == first, \
        "play after stop is not the piece from the top"
    plugin.destroy(plug_raw)


@needs_toolchain
def test_the_knobs_are_the_daws_parameters(tmp_path):
    """`twoknobs.ges` exported: two automatable parameters, named as
    the author named them, defaulted as the program declares — and a
    turned knob renders exactly what the engine renders at that value.

    The last equality is the one that matters: a `PARAM_VALUE` event
    into the plugin and a `control` answer into `run_native` are the
    same fact through two doors, and the samples must not know which
    door it came through.
    """
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.export import export_clap

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "twoknobs.ges").read_text()
    out = tmp_path / "twoknobs.clap"
    export_clap(source, out, rate=RATE, name="twoknobs")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    raw = plugin.get_extension(plug_raw, b"clap.params")
    assert raw, "no clap.params extension"
    params = ctypes.cast(raw, POINTER(Params)).contents

    assert params.count(plug_raw) == 2
    knobs = {}
    for i in range(2):
        info = ParamInfo()
        assert params.get_info(plug_raw, i, ctypes.byref(info))
        knobs[info.name.decode()] = info
    # The author wrote `pitchChan` and `cutoffChan`; the knobs drop the
    # `Chan`, and the defaults are the program's own `40` and `70`.
    assert set(knobs) == {"pitch", "cutoff"}
    assert knobs["pitch"].default_value == 40.0
    assert knobs["cutoff"].default_value == 70.0
    for info in knobs.values():
        assert info.flags & (1 << 5), "not automatable"
        assert info.flags & (1 << 0), "an Int knob is stepped"

    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames = 256
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    events, kept = _one_event(knobs["pitch"].id, 52.0)
    proc = Process(steady_time=0, frames_count=frames, transport=None,
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=ctypes.cast(ctypes.pointer(events), c_void_p),
                   out_events=None)
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
    turned = list(buf)

    got = c_double()
    assert params.get_value(plug_raw, knobs["pitch"].id,
                            ctypes.byref(got))
    assert got.value == 52.0, "the event did not land in the slot"

    graph = graph_of(source, "", rate=RATE)
    by_id = {n.id: (52 if n.chan == "pitchChan" else n.init)
             for n in graph.control_sources()}
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, frames, block=frames,
                                  control=lambda node, _t: by_id[node]))
    assert turned == pytest.approx(offline), \
        "a turned knob is not the engine at that value"
    assert max(abs(x) for x in offline) > 0.05, "silent: nothing compared"

    # **The knobs survive the rewind.**  Stop, then play: the piece
    # restarts from its top, but the knob's value is the host's belief
    # and must not quietly return to its default — the samples after
    # the rewind are the first block at 52 again, and the parameter
    # still reads 52.
    transport = Transport()
    for flags in (0, IS_PLAYING):
        transport.flags = flags
        proc2 = Process(steady_time=0, frames_count=frames,
                        transport=ctypes.pointer(transport),
                        audio_inputs=None,
                        audio_outputs=ctypes.pointer(port),
                        audio_inputs_count=0, audio_outputs_count=1,
                        in_events=None, out_events=None)
        assert plugin.process(plug_raw, ctypes.byref(proc2)) == 1
    assert list(buf) == pytest.approx(offline), \
        "the rewind forgot the knob"
    got2 = c_double()
    assert params.get_value(plug_raw, knobs["pitch"].id,
                            ctypes.byref(got2))
    assert got2.value == 52.0, "the parameter display and the sound differ"

    # **The session remembers the knob** — `clap.state`: save this
    # instance, load into a fresh one, and the fresh one reads 52 too.
    lib2, plug2_raw, plugin2 = _plugin_of(out)
    assert plugin2.init(plug2_raw)
    _state_roundtrip(plugin, plug_raw, plugin2, plug2_raw)
    raw2 = plugin2.get_extension(plug2_raw, b"clap.params")
    params2 = ctypes.cast(raw2, POINTER(Params)).contents
    got3 = c_double()
    assert params2.get_value(plug2_raw, knobs["pitch"].id,
                             ctypes.byref(got3))
    assert got3.value == 52.0, "the project forgot the knob"
    plugin2.destroy(plug2_raw)
    plugin.destroy(plug_raw)


@needs_toolchain
def test_a_played_note_is_the_scheduled_note(tmp_path):
    """`fmpoly.ges` exported: a NOTE_ON through the plugin's port is a
    note through Python's own allocator, sample for sample.

    The shell carries its own voice allocation (Rust, mirroring
    `audioalloc`) and its own payloads (`noteOn` run through the
    G-machine at export time and tabled).  Both are second
    implementations, which is where bugs live — so both halves of this
    test are driven from one fact, *a note on key 60 at sample 0,
    released at sample 128*, and the samples must agree about it.

    The velocity sits exactly on a table level (127·x quantising to
    103, the level's own evaluation point), so the comparison is exact
    rather than within a bucket.
    """
    from gestate.audio import assemble
    from gestate.audioalloc import Allocator, into_schedule
    from gestate.audiollvm import run_native
    from gestate.audiomidi import FromMidi
    from gestate.audioperform import graph_of, has_score
    from gestate.audioschedule import Schedule
    from gestate.audioscore import assemble_performance
    from gestate.audiovoices import banks_of, channels_of
    from gestate.export import export_clap
    from gestate.pipeline import compile as _compile

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "fmpoly.ges").read_text()
    out = tmp_path / "fmpoly.clap"
    export_clap(source, out, rate=RATE, name="fmpoly")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    assert plugin.get_extension(plug_raw, b"clap.note-ports"), \
        "no clap.note-ports extension"
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames, key, vel127 = 128, 60, 103
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)

    # A *stopped* transport, not a null one: `fmpoly` carries a demo
    # score, and with no transport at all a free-running host now
    # performs it (the cursor, `spec/dynamicscore.md` stage one) —
    # this test is the keyboard's, and a DAW auditions a keyboard
    # with the timeline stopped.
    still = Transport()
    still.flags = 0

    def block(events=None) -> list:
        proc = Process(steady_time=0, frames_count=frames,
                       transport=ctypes.pointer(still),
                       audio_inputs=None,
                       audio_outputs=ctypes.pointer(port),
                       audio_inputs_count=0, audio_outputs_count=1,
                       in_events=ctypes.cast(ctypes.pointer(events),
                                             c_void_p) if events else None,
                       out_events=None)
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        return list(buf)

    on, kept_on = _note_event(0, key, vel127 / 127.0)
    off, kept_off = _note_event(1, key, 0.0)
    played = block(on) + block(off) + block()

    graph = graph_of(source, "", rate=RATE)
    bank = banks_of(source)[0]
    allocator = Allocator(channels_of(source, bank), policy="oldest")
    # The assembly the program needs — `fmpoly` carries a demo score,
    # so the music prelude rides along, exactly as `export.note_bank`
    # chooses it.
    assembled = (assemble_performance(source, "", RATE)
                 if has_score(source) else assemble(source, RATE))
    fm = FromMidi(_compile(assembled), [bank.name])
    payload = fm.payload_for(bank.name, 0, key, vel127)
    assert payload is not None, "the instance declined the test note"
    schedule = Schedule()
    into_schedule(schedule, allocator.note_on((0, key), payload, 0),
                  0, frames)
    into_schedule(schedule, allocator.note_off((0, key), frames),
                  frames, frames)
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, 3 * frames, block=frames,
                                  control=schedule.control_for(graph)))

    assert played == pytest.approx(offline), \
        "a played note is not the scheduled note"
    assert max(abs(x) for x in offline) > 0.05, "silent: nothing compared"

    # **It plays while the transport runs, or while a note does.**  A
    # DAW sends keyboard notes with the timeline stopped, and a synth
    # that refused them could not be auditioned — a held or ringing
    # voice keeps the render alive; the stop-means-silence half of the
    # rule gates only self-playing material.
    transport = Transport()
    transport.flags = 0                                   # stopped
    on2, kept2 = _note_event(0, key, vel127 / 127.0)
    proc = Process(steady_time=0, frames_count=frames,
                   transport=ctypes.pointer(transport),
                   audio_inputs=None, audio_outputs=ctypes.pointer(port),
                   audio_inputs_count=0, audio_outputs_count=1,
                   in_events=ctypes.cast(ctypes.pointer(on2), c_void_p),
                   out_events=None)
    assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
    assert max(abs(x) for x in buf) > 0.05, \
        "an instrument refused a note because the timeline was stopped"
    plugin.destroy(plug_raw)


@needs_toolchain
def test_the_routing_matrix_layers_banks(tmp_path):
    """`duet.ges` exported: channel 1 plays `lead` by default, and
    ticking the `bass ch1` checkbox layers both banks on one key.

    The matrix is parameters — one stepped 0/1 per (bank × channel),
    module `routing`, defaulted to the diagonal that is
    `audiomidi.by_midi_channel`'s own rule — so every DAW's generic
    parameter view *is* the checkbox matrix.  Parity as ever: the
    routed notes must equal the same notes through Python's own
    allocators, one per bank, sample for sample.
    """
    from gestate.audio import assemble
    from gestate.audioalloc import Allocator, into_schedule
    from gestate.audiollvm import run_native
    from gestate.audiomidi import FromMidi
    from gestate.audioperform import graph_of, has_score
    from gestate.audioschedule import Schedule
    from gestate.audioscore import assemble_performance
    from gestate.audiovoices import banks_of, channels_of
    from gestate.export import export_clap
    from gestate.pipeline import compile as _compile

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "duet.ges").read_text()
    out = tmp_path / "duet.clap"
    export_clap(source, out, rate=RATE, name="duet")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    raw = plugin.get_extension(plug_raw, b"clap.params")
    params = ctypes.cast(raw, POINTER(Params)).contents

    cells = {}
    for i in range(params.count(plug_raw)):
        info = ParamInfo()
        assert params.get_info(plug_raw, i, ctypes.byref(info))
        if info.module == b"routing":
            cells[info.name.decode()] = info
    assert {"lead ch1", "bass ch2"} <= set(cells), sorted(cells)[:4]
    assert len(cells) == 32, "two banks, sixteen channels each"
    assert cells["lead ch1"].default_value == 1.0, "the diagonal"
    assert cells["bass ch1"].default_value == 0.0

    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    frames, key, vel127 = 128, 60, 103
    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)

    # Stopped rather than null: `duet`'s bass is scored, and a null
    # transport free-runs the piece now — the matrix is the keyboard's
    # test, so the timeline stands still.
    still = Transport()
    still.flags = 0

    def block(*evs) -> list:
        events, kept = _event_list(*evs) if evs else (None, None)
        proc = Process(steady_time=0, frames_count=frames,
                       transport=ctypes.pointer(still),
                       audio_inputs=None,
                       audio_outputs=ctypes.pointer(port),
                       audio_inputs_count=0, audio_outputs_count=1,
                       in_events=ctypes.cast(ctypes.pointer(events),
                                             c_void_p) if evs else None,
                       out_events=None)
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        return list(buf)

    velocity = vel127 / 127.0
    played = (
        block(_note_struct(0, key, velocity))            # lead only
        + block(_note_struct(1, key, 0.0))
        + block(_param_struct(cells["bass ch1"].id, 1.0),  # tick the box,
                _note_struct(0, key, velocity))            # layer both
        + block(_note_struct(1, key, 0.0))
        + block())

    graph = graph_of(source, "", rate=RATE)
    banks = banks_of(source)
    allocators = {b.name: Allocator(channels_of(source, b),
                                    policy="oldest") for b in banks}
    assembled = (assemble_performance(source, "", RATE)
                 if has_score(source) else assemble(source, RATE))
    fm = FromMidi(_compile(assembled), [b.name for b in banks])
    schedule = Schedule()

    def strike(names, on_at):
        for name in names:
            payload = fm.payload_for(name, 0, key, vel127)
            assert payload is not None
            into_schedule(schedule,
                          allocators[name].note_on((0, key), payload,
                                                   on_at),
                          on_at, frames)
            into_schedule(schedule,
                          allocators[name].note_off((0, key),
                                                    on_at + frames),
                          on_at + frames, frames)

    strike(["lead"], 0)
    strike(["lead", "bass"], 2 * frames)
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, 5 * frames, block=frames,
                                  control=schedule.control_for(graph)))

    assert played == pytest.approx(offline), \
        "the routed notes are not the allocated notes"
    assert max(abs(x) for x in offline) > 0.05, "silent: nothing compared"

    # **The session remembers the matrix** — the ticked `bass ch1`
    # survives a save into a fresh instance.
    lib2, plug2_raw, plugin2 = _plugin_of(out)
    assert plugin2.init(plug2_raw)
    _state_roundtrip(plugin, plug_raw, plugin2, plug2_raw)
    raw2 = plugin2.get_extension(plug2_raw, b"clap.params")
    params2 = ctypes.cast(raw2, POINTER(Params)).contents
    got = c_double()
    assert params2.get_value(plug2_raw, cells["bass ch1"].id,
                             ctypes.byref(got))
    assert got.value == 1.0, "the project forgot the matrix"
    plugin2.destroy(plug2_raw)
    plugin.destroy(plug_raw)


# ── The score cursor — `spec/dynamicscore.md` stage one's Rust half ─────────


def _transport_at(t: int, rate: int, bpm: float) -> "Transport":
    """A playing timeline standing at engine sample `t` — beats fixed
    point the way a host computes it, rounded, so the cursor's slack
    is exercised rather than sidestepped."""
    transport = Transport()
    transport.flags = IS_PLAYING | (1 << 0) | (1 << 1)
    transport.tempo = bpm
    transport.song_pos_beats = round(t / rate * (bpm / 60.0) * (1 << 31))
    return transport


@needs_toolchain
def test_the_daw_plays_the_piece(tmp_path):
    """Press play and the piece performs itself — the stage-one
    promise, through the exported artifact.

    The descriptor carries `duet`'s events in beats; a playing
    transport at the piece's own tempo walks the cursor over them; and
    the result must be the *bake* — the same `schedule_voices` control
    the offline render uses — sample for sample, because cursor and
    bake share one arithmetic (`tick * 60 * rate // (bpm * TPB)`) and
    one allocation order.
    """
    from gestate.audioalloc import Allocator
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.audioscore import (duration_of_voices, perform_voices,
                                    schedule_voices)
    from gestate.audiovoices import banks_of, channels_of
    from gestate.export import export_clap

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "duet.ges").read_text()
    out = tmp_path / "duet.clap"
    export_clap(source, out, rate=RATE, name="duet")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    bpm, events = perform_voices(source, "", RATE)
    frames = 128
    samples = duration_of_voices(events, bpm, RATE)
    blocks = samples // frames

    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    played: list = []
    for k in range(blocks):
        transport = _transport_at(k * frames, RATE, float(bpm))
        proc = Process(steady_time=0, frames_count=frames,
                       transport=ctypes.pointer(transport),
                       audio_inputs=None,
                       audio_outputs=ctypes.pointer(port),
                       audio_inputs_count=0, audio_outputs_count=1,
                       in_events=None, out_events=None)
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        played += list(buf)

    graph = graph_of(source, "", rate=RATE)
    allocators = {b.name: Allocator(channels_of(source, b),
                                    policy="oldest")
                  for b in banks_of(source)}
    schedule = schedule_voices(events, bpm, RATE, allocators,
                               block=frames)
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, blocks * frames,
                                  block=frames,
                                  control=schedule.control_for(graph)))

    assert max(abs(x) for x in offline) > 0.05, "silent: nothing compared"
    assert played == pytest.approx(offline), \
        "the performed piece is not the baked piece"
    plugin.destroy(plug_raw)


@needs_toolchain
def test_play_from_bar_five_plays_bar_five(tmp_path):
    """Seek to the middle and press play: the piece continues from
    there, standing exactly where playing from the top would stand.

    The oracle is `audiodynamic.Performer` itself — seek then advance,
    its changes poured into a `Schedule` with the time-valued channels
    rebased to the plugin's engine clock (`gateAt` names an instant
    before the engine began, which is how a held note resumes
    mid-envelope).  One semantics, two implementations, one render
    each.
    """
    from gestate.audioalloc import GATE_AT, OFF_AT, Allocator
    from gestate.audiodynamic import Performer
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of
    from gestate.audioschedule import Schedule
    from gestate.audioscore import duration_of_voices, perform_voices
    from gestate.audiovoices import banks_of, channels_of
    from gestate.export import export_clap

    source = (Path(__file__).resolve().parent.parent
              / "examples" / "audio" / "duet.ges").read_text()
    out = tmp_path / "duet.clap"
    export_clap(source, out, rate=RATE, name="duet")

    lib, plug_raw, plugin = _plugin_of(out)
    assert plugin.init(plug_raw)
    assert plugin.activate(plug_raw, float(RATE), 32, 512)
    assert plugin.start_processing(plug_raw)

    bpm, events = perform_voices(source, "", RATE)
    frames = 128
    samples = duration_of_voices(events, bpm, RATE)
    target = samples // 2                      # beat 8 of 16, on a beat
    blocks = (samples - target) // frames

    buf = (c_float * frames)()
    chans = (POINTER(c_float) * 1)(ctypes.cast(buf, POINTER(c_float)))
    port = AudioBuffer(data32=chans, data64=None, channel_count=1,
                       latency=0, constant_mask=0)
    played: list = []
    for k in range(blocks):
        transport = _transport_at(target + k * frames, RATE, float(bpm))
        proc = Process(steady_time=0, frames_count=frames,
                       transport=ctypes.pointer(transport),
                       audio_inputs=None,
                       audio_outputs=ctypes.pointer(port),
                       audio_inputs_count=0, audio_outputs_count=1,
                       in_events=None, out_events=None)
        assert plugin.process(plug_raw, ctypes.byref(proc)) == 1
        played += list(buf)

    # The Python performer's own seek, rebased to the plugin's clock:
    # the plugin rewound at the play edge, so its engine sample 0 is
    # score sample `target`, and every gate/off stamp shifts by it.
    allocators = {b.name: Allocator(channels_of(source, b),
                                    policy="oldest")
                  for b in banks_of(source)}
    timechans = set()
    for b in banks_of(source):
        for voice in channels_of(source, b):
            timechans.update((voice[GATE_AT], voice[OFF_AT]))

    def rebased(chan, value):
        return value - target if value and chan in timechans else value

    performer = Performer(events, bpm, RATE, allocators, block=frames)
    performer.seek(target)
    schedule = Schedule()
    for chan, value in performer.values.items():
        schedule.change(0, chan, rebased(chan, value))
    for t in range(target, samples + frames, frames):
        for boundary, chan, value in performer.advance(t):
            schedule.change(boundary - target, chan,
                            rebased(chan, value))

    graph = graph_of(source, "", rate=RATE)
    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, blocks * frames,
                                  block=frames,
                                  control=schedule.control_for(graph)))

    assert max(abs(x) for x in offline) > 0.05, "silent: nothing compared"
    assert played == pytest.approx(offline), \
        "playing from the middle is not standing in the middle"
    plugin.destroy(plug_raw)
