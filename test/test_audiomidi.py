"""MIDI CC as control-rate parameters — `gestate/audiomidi.py`.

Two halves, and the split is why anything here runs at all.

**The mapping and the coalescing** are a dict and some arithmetic, and
`Controls.set` is the whole interface the engine needs — so they are tested
with no device, on any machine.  That matters more than it looks: a suite
whose MIDI tests all skip is a suite with no MIDI tests, and the parts that
can be quietly wrong (which knob a CC drives, what an untouched controller
reads) are exactly the parts that need no hardware.

**The device** is tested through whatever loopback port the machine offers,
and skips when there is none.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiomidi import Binding, Controls, Listener, MidiError, input_names

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
RATE = 2000

needs_midi = pytest.mark.skipif(not input_names(),
                                reason="no MIDI input on this machine")


def _graph(name="twoknobs.ges"):
    return extract((AUDIO_DIR / name).read_text(), rate=RATE)


def _source(name="twoknobs.ges") -> str:
    return (AUDIO_DIR / name).read_text()


# ── Binding ─────────────────────────────────────────────────────────────────


def test_knobs_bind_to_consecutive_ccs_in_declaration_order():
    """Reading order, not node-id order.

    A person plugging in a controller counts knobs down the page; node ids
    are an artefact of the order the extractor happened to reach them.  The
    two agree in `twoknobs.ges` and would not have to.
    """
    controls = Controls.bind(_graph(), _source())
    assert [(b.name, b.cc) for b in controls.bindings] == [
        ("pitch", 1), ("cutoff", 2)]


def test_a_graph_alone_binds_by_origin():
    """Without the source text there is still a name — the origin path.

    Worth having because a host may hold a compiled graph and no longer the
    text it came from, and `CC1 = pitch` is a better thing to show a player
    than `CC1 = node 1`.
    """
    controls = Controls.bind(_graph())
    assert {b.name for b in controls.bindings} == {"pitch", "cutoff"}


def test_an_untouched_controller_reads_the_synths_own_default():
    """Not zero, and this is the bug the first version had.

    `cutoff = 70 ::: mkSig (wait c)` says what the synth sounds like before
    anything is plugged in.  A host answering 0 at the first block boundary
    would override that — and the synth would play, sounding wrong, with
    nothing raised anywhere.
    """
    controls = Controls.bind(_graph(), _source())
    assert [b.initial for b in controls.bindings] == [40, 70]

    read = controls.control()
    assert [read(b.node, 0) for b in controls.bindings] == [40, 70]

    graph = _graph()
    declared = {n.id: n.init for n in graph.control_sources()}
    assert run(graph, 200, block=64, control=read) == \
        run(graph, 200, block=64, control=lambda node, _t: declared[node])


def test_a_span_maps_the_controllers_range_onto_the_parameters():
    """0..127 is the wire; 0..100 is what this synth's knobs mean."""
    controls = Controls.bind(_graph(), _source(),
                             spans={"pitch": (0, 100), "cutoff": (0, 100)})
    pitch = controls.bindings[0]
    assert pitch.value_of(0) == 0
    assert pitch.value_of(127) == 100
    assert pitch.value_of(64) == 50

    # No span is the raw value, deliberately: a synth that wants 0..127
    # should not have a range imposed on it.
    raw = Controls.bind(_graph(), _source()).bindings[0]
    assert raw.value_of(127) == 127


def test_a_cc_with_no_binding_is_ignored():
    """A controller nobody asked about must not become a parameter."""
    controls = Controls.bind(_graph(), _source())
    controls.set(64, 100)                       # sustain pedal, unbound
    read = controls.control()
    assert [read(b.node, 0) for b in controls.bindings] == [40, 70]


# ── Coalescing — the reason CC fits and notes do not ────────────────────────


def test_the_latest_value_in_a_block_is_the_one_that_is_heard():
    """A knob that moved fifty times is a knob where it ended up.

    This is the whole argument for admitting MIDI at control rate: nothing
    a *value* source can lose by being sampled once per block is audible.
    A note-on would be lost outright, which is why notes are not here.
    """
    controls = Controls.bind(_graph(), _source(),
                             spans={"pitch": (0, 100), "cutoff": (0, 100)})
    read = controls.control()
    graph = _graph()

    for value in range(0, 128, 3):              # a sweep, inside one block
        controls.set(1, value)
    controls.set(1, 127)
    swept = run(graph, 200, block=64, control=read)

    fresh = Controls.bind(_graph(), _source(),
                          spans={"pitch": (0, 100), "cutoff": (0, 100)})
    fresh.set(1, 127)
    assert swept == run(_graph(), 200, block=64, control=fresh.control())


def test_each_knob_moves_only_its_own_parameter():
    """The failure this cannot be allowed to have: swapped knobs.

    Silent in every way that matters — the synth plays and the controls are
    wrong — so it is checked by driving them to values that cannot be
    confused and requiring the two orders to differ.
    """
    spans = {"pitch": (0, 100), "cutoff": (0, 100)}
    a = Controls.bind(_graph(), _source(), spans=spans)
    a.set(1, 120)
    a.set(2, 10)

    b = Controls.bind(_graph(), _source(), spans=spans)
    b.set(1, 10)
    b.set(2, 120)

    assert run(_graph(), 300, block=64, control=a.control()) != \
        run(_graph(), 300, block=64, control=b.control())


# ── The listener ────────────────────────────────────────────────────────────


class _Message:
    """A mido message, as far as `feed` is concerned."""

    def __init__(self, type_, control=0, value=0, channel=0):
        self.type = type_
        self.control = control
        self.value = value
        self.channel = channel


def test_only_control_change_messages_are_taken():
    """A note-on must not silently become a knob turn.

    `feed` returning `False` is the honest answer for a message this module
    has no meaning for — notes need a per-block event list, which the static
    fragment has no room for.
    """
    controls = Controls.bind(_graph(), _source())
    listener = Listener(controls)

    assert not listener.feed(_Message("note_on", value=64))
    assert not listener.feed(_Message("pitchwheel"))
    assert listener.feed(_Message("control_change", control=1, value=64))
    assert controls.latest == {1: 64}
    assert listener.messages == 1


def test_a_listener_can_be_pinned_to_one_midi_channel():
    controls = Controls.bind(_graph(), _source())
    listener = Listener(controls, channel=3)

    assert not listener.feed(_Message("control_change", 1, 64, channel=0))
    assert listener.feed(_Message("control_change", 1, 99, channel=3))
    assert controls.latest == {1: 99}


def test_asking_for_a_port_that_is_not_there_says_which_are():
    controls = Controls.bind(_graph(), _source())
    with pytest.raises(MidiError, match="no MIDI input"):
        Listener(controls, port_name="Nonexistent Device 99").start()


@needs_midi
def test_a_real_cc_message_reaches_the_control_value():
    """End to end through an actual MIDI port.

    Uses whatever loopback the machine has — on Linux that is usually
    `Midi Through`.  Skipped rather than mocked where there is none: the
    thing being tested here is precisely the part a fake would replace.
    """
    import mido

    name = next((n for n in input_names() if "Through" in n), None)
    if name is None:
        pytest.skip("no loopback MIDI port to send to")

    controls = Controls.bind(_graph(), _source(),
                             spans={"pitch": (0, 100), "cutoff": (0, 100)})
    listener = Listener(controls, port_name=name).start()
    try:
        with mido.open_output(name) as out:
            out.send(mido.Message("control_change", control=1, value=127))
            deadline = time.time() + 2.0
            while time.time() < deadline and 1 not in controls.latest:
                time.sleep(0.01)
    finally:
        listener.close()

    assert controls.latest.get(1) == 127, "the CC never arrived"
    read = controls.control()
    assert read(controls.bindings[0].node, 0) == 100


# ── The CLI's binding step ──────────────────────────────────────────────────


def test_a_synth_with_no_knobs_says_so_rather_than_listening():
    """`--midi` on `blip.ges` is a mistake worth naming."""
    from gestate.audiolive import LiveError, _open_midi

    with pytest.raises(LiveError, match="no control channel"):
        _open_midi(_source("blip.ges"), RATE, None, None)


def test_a_malformed_span_is_reported():
    from gestate.audiolive import LiveError, _open_midi

    with pytest.raises(LiveError, match="not `LO:HI`"):
        _open_midi(_source(), RATE, None, "loud")


@needs_midi
def test_the_cli_binds_every_knob():
    from gestate.audiolive import _open_midi

    controls, listener = _open_midi(_source(), RATE, None, "0:100")
    try:
        assert controls.describe() == "pitch=CC1, cutoff=CC2"
        assert all(b.span == (0, 100) for b in controls.bindings)
    finally:
        listener.close()
