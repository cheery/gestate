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
from pathlib import Path

from gestate.audioengine import State, migrate, render_block
from gestate.audioextract import extract

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
