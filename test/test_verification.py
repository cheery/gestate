"""The other half's oracle — `spec/verification.md`, first increments.

The engine half is checked sample-for-sample; the Python around it is
where `fixme.md` F97's nine defects lived, four of them silent.  These
are the differential oracles that need no transcript format to exist:
two routes to the same answer that the codebase already contains, held
together for the first time.

Every assertion here is *total* — whole value vectors, whole sample
runs — because silence was the failure mode being closed.
"""

from __future__ import annotations

import copy
import ctypes
import shutil
import tempfile
from pathlib import Path

import pytest

from gestate.audioengine import State, migrate, render_block
from gestate.audioextract import extract

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
SUPER_DIR = Path(__file__).resolve().parent.parent / "examples" / "super"

#: One plain synth and one with delay lines: `migrate` carries `values`
#: and `lines` by different mechanisms, and an identity that holds for
#: one and not the other is exactly the silent kind of wrong.
PROGRAMS = {
    "blip.ges": AUDIO_DIR / "blip.ges",
    "dubgate.ges": SUPER_DIR / "dubgate.ges",
}


def _graph(name: str, rate: int = 8000):
    return extract(PROGRAMS[name].read_text(), rate=rate)


# ── The identity edit is the identity ───────────────────────────────────────


def test_the_identity_edit_is_the_identity():
    """Republishing unchanged source must move nothing at all.

    `migrate(g, s, g')` for `g'` extracted from the same text has to
    return the state it was given — same slot values, same delay-line
    rings, same instant — and the sound after must be the sound that
    would have played.  An edit that subtly moved state moved it just
    as much when the edit changed nothing, which is the property the
    four silent defects would have tripped.
    """
    for name in PROGRAMS:
        graph = _graph(name)
        state = State.initial(graph)
        render_block(graph, state, 256)

        again = _graph(name)
        carried = migrate(graph, state, again)
        assert carried.t == state.t, name
        assert carried.values == state.values, name
        assert carried.lines == state.lines, name

        straight = copy.deepcopy(state)
        a = render_block(graph, straight, 256)
        b = render_block(again, carried, 256)
        assert a == b, f"{name}: the identity edit changed the sound"


# ── The block size is not observable ────────────────────────────────────────


def test_the_block_size_is_not_observable():
    """One render, any dicing — 512 samples as 1×512, 8×64, and a
    ragged mix must be the same samples and the same final state.

    `render_block`'s own docstring stakes this claim ("with no
    control-rate node in the graph … the block size is not observable
    at all"); this holds it, wholesale, on a program with scans and
    sliding delay lines in it.
    """
    for name in PROGRAMS:
        graph = _graph(name)

        whole_state = State.initial(graph)
        whole = render_block(graph, whole_state, 512)

        diced_state = State.initial(graph)
        diced: list = []
        for n in (64,) * 8:
            diced += render_block(graph, diced_state, n)
        assert whole == diced, f"{name}: 8x64 differs from 1x512"

        ragged_state = State.initial(graph)
        ragged: list = []
        for n in (1, 7, 120, 3, 253, 128):
            ragged += render_block(graph, ragged_state, n)
        assert whole == ragged, f"{name}: ragged blocks differ"

        assert diced_state.t == whole_state.t
        assert diced_state.values == whole_state.values
        assert diced_state.lines == whole_state.lines
        assert ragged_state.values == whole_state.values


# ── Rendering is a function of the graph and the state ──────────────────────


def test_the_same_state_renders_the_same_sound():
    """Determinism, held totally: two copies of one state, rendered
    apart, agree to the last sample and the last slot.

    Replay (`spec/verification.md`) is only possible if this holds;
    a wall-clock read or an iteration-order dependence anywhere in the
    render path breaks it here, loudly, before the transcript format
    exists to depend on it.
    """
    for name in PROGRAMS:
        graph = _graph(name)
        state = State.initial(graph)
        render_block(graph, state, 100)

        one = copy.deepcopy(state)
        two = copy.deepcopy(state)
        a = render_block(graph, one, 300)
        b = render_block(graph, two, 300)
        assert a == b, name
        assert one.values == two.values, name
        assert one.lines == two.lines, name


# ── A quiescent live session is the offline render ──────────────────────────

#: `test_audioassigned.py`'s fixture, trimmed: one bank, three notes.  The
#: point is not the music — it is that a *score* drives control channels,
#: which is the plumbing `audioeditor._push_controls`'s docstring records
#: two silent, shipped defects in, neither seen by the suite because every
#: test drove the Python control path.  This drives the C one.
SCORED = """
Custom := Custom Float Int

voices lead 3 : Custom -> Sig Float
lead = myVoice

outV : Both Gate Custom -> Float
outV p = case p of
    Both w c -> case w of
        Gate on off -> inner on off c

inner : Int -> Int -> Custom -> Float
inner on off c = case c of
    Custom f k -> sawOf (wrap (toFloat k * 0.002)) * f * 0.2

myVoice : Sig Gate -> Sig Custom -> Sig Float
myVoice g s = myVoiceFolded (!Both g s)

myVoiceFolded : Sig (Both Gate Custom) -> Sig Float
myVoiceFolded s = map outV s

sound : Sig Float
sound = gain 0.5 lead

tune : [: Custom :]
tune = '(Custom 1.0 60) ++ '(Custom 0.8 64) ++ '(Custom 0.6 67)

score : [: Void :]
score = tune >>= voices.lead

bpm : Int
bpm = 120
"""


@needs_clang
def test_a_quiescent_live_session_is_the_offline_render():
    """Publish a scored program, touch nothing: the C host must render
    what `audioperform` renders offline, to f32 precision, block for
    block.

    The two halves share one `schedule.control_for(graph)` on purpose —
    the oracle is not about what the schedule says, it is about whether
    the C host's control slots, block loop and position accounting
    deliver what it says the way the offline driver does.  This is the
    seam `audioeditor._push_controls` documents shipping two silent
    defects across (a score pinned to instant 0; `gateAt` stamped 0),
    with the suite blind because `conftest.py` keeps tests off the C
    device path — `Host.fill` is that path with the clock held by hand.
    """
    from gestate.audiohost import Host
    from gestate.audiolive import Engine
    from gestate.audiollvm import run_native
    from gestate.audioperform import graph_of, scored

    rate, block = 8000, 128
    schedule, samples, _ = scored(SCORED, "", rate=rate, block=block)
    graph = graph_of(SCORED, "", rate=rate)
    control = schedule.control_for(graph)

    with tempfile.TemporaryDirectory() as d:
        offline = list(run_native(graph, d, samples, block=block,
                                  control=control))

    with tempfile.TemporaryDirectory() as d:
        engine = Engine.compile(SCORED, rate, d)
        sources = engine.control_sources
        host = Host(channels=1, rate=rate, controls=len(sources),
                    directory=d, fade_in=False)
        host.install(engine)
        buffer = (ctypes.c_float * block)()
        live: list = []
        at = 0
        while at < samples:
            # What the housekeeping thread does at its own pace, done at
            # every block boundary exactly — quiescence is the timing the
            # thread approximates.
            for i, node in enumerate(sources):
                host.set_control(i, control(node.id, at), node.type_)
            host.fill(buffer, block)
            live += list(buffer)
            at += block
        host.close()

    assert live[:samples] == pytest.approx(offline[:samples]), \
        "the C host under a schedule is not the offline render"
    loud = sum(1 for x in offline if abs(x) > 0.01)
    assert loud > samples // 10, "silent: nothing was compared"
