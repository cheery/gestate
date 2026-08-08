"""A schedule of control changes — `gestate/audioschedule.py`.

This exists so that notes can be *checked*.  Every stage of
`spec/liveaudio.md` is verified by rendering the same program through the
interpreter and through the engine and comparing samples bit for bit, and
`render(control_every=n)` could only drive a control channel with the
instant number — enough to show that the control clock ticks, and useless
for anything with a shape.

So the load-bearing test here is the last one: **the same schedule played
through the oracle, the block renderer and generated code gives the same
samples.**  Everything above it is the arithmetic that has to be right for
that to mean anything.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from gestate.audio import AudioError, render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiollvm import run_native
from gestate.audioschedule import Schedule, ScheduleError

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")

#: One knob, read straight out as the sample value — so a sample *is* the
#: control value, and a schedule can be read back off the output.
KNOB = """
kc : Chan Int
kc = chan

knob : Sig Int
knob = 40 ::: mkSig (wait kc)

blend : Int -> Int -> Float
blend n k = toFloat k * 0.001

sound : Sig Float
sound = zip blend ticks knob
"""

RATE, BLOCK = 1000, 64


# ── The step function ───────────────────────────────────────────────────────


def test_a_value_is_held_from_its_change_onwards():
    """A schedule is a step function per channel, not a stream of events.

    Which is what a control source *is* — so a schedule that recorded
    anything richer would be recording something the engine cannot hold.
    """
    s = Schedule().change(10, "a", 1).change(20, "a", 2)
    assert s.value_at("a", 0) is None, "before the first change"
    assert s.value_at("a", 9) is None
    assert s.value_at("a", 10) == 1
    assert s.value_at("a", 19) == 1
    assert s.value_at("a", 20) == 2
    assert s.value_at("a", 1000) == 2


def test_changes_may_be_added_out_of_order():
    """A scheduler walking a `Score` by voice, not by time, is the caller."""
    s = Schedule().change(20, "a", 2).change(10, "a", 1).change(15, "a", 9)
    assert [s.value_at("a", t) for t in (10, 15, 20)] == [1, 9, 2]


def test_two_changes_at_one_instant_keep_the_last():
    """One instant, one value: a channel holds a value, not a queue."""
    s = Schedule().change(10, "a", 1).change(10, "a", 7)
    assert s.value_at("a", 10) == 7


def test_channels_are_independent():
    s = Schedule().change(10, "a", 1).change(50, "b", 2)
    assert s.value_at("b", 10) is None
    assert s.value_at("a", 50) == 1
    assert s.channels() == ["a", "b"]


def test_a_change_before_the_start_is_refused():
    with pytest.raises(ScheduleError, match="before the start"):
        Schedule().change(-1, "a", 0)


# ── Delivery, which is not event time ───────────────────────────────────────


def test_a_value_is_delivered_at_the_boundary_before_its_event():
    """The arithmetic that keeps an onset sample-accurate.

    A note starting at 1200 has to be *held* by the voice before instant
    1200 arrives, so the voice can compare its own `ticks` against it and
    begin partway through a block.  Delivering it at 1200 would be a block
    late; quantising the note to 1216 would be the thing this avoids.
    """
    s = Schedule().deliver(1200, "g0", 1200, block=64)
    assert s.value_at("g0", 1152) == 1200, "held from the boundary before"
    assert s.value_at("g0", 1151) is None
    assert 1152 % 64 == 0


def test_an_event_in_the_first_block_is_delivered_at_zero():
    s = Schedule().deliver(10, "g0", 10, block=64)
    assert s.value_at("g0", 0) == 10


def test_a_block_size_of_zero_is_refused():
    with pytest.raises(ScheduleError, match="block size"):
        Schedule().deliver(10, "a", 1, block=0)


# ── Driving a graph ─────────────────────────────────────────────────────────


def test_an_unscheduled_channel_keeps_the_synths_own_default():
    """Not zero — the same rule `audiomidi` follows, for the same reason.

    `knob = 40 ::: …` is the program saying what it sounds like before
    anything drives it, and a schedule that says nothing about a channel is
    not an instruction to silence it.
    """
    graph = extract(KNOB, rate=RATE)
    control = Schedule().control_for(graph)
    node = graph.control_sources()[0]
    assert control(node.id, 0) == 40


def test_a_schedule_naming_a_channel_the_graph_lacks_is_refused():
    """A typo in a channel name would otherwise be silence, not an error."""
    graph = extract(KNOB, rate=RATE)
    with pytest.raises(ScheduleError, match="does not have"):
        Schedule().change(0, "nope", 1).control_for(graph)


def test_the_oracle_refuses_one_too():
    with pytest.raises(AudioError, match="does not declare"):
        render(KNOB, 0.05, RATE, control_every=BLOCK,
               schedule=Schedule().change(0, "nope", 1))


def test_the_channel_name_is_on_the_node():
    """`Node.chan` is the key both sides resolve — the point of adding it."""
    graph = extract(KNOB, rate=RATE)
    assert [n.chan for n in graph.control_sources()] == ["kc"]
    assert set(graph.control_by_chan()) == {"kc"}
    # An audio-rate source keeps its channel name too; it is simply not
    # something a schedule may drive.
    assert graph.nodes[graph.control_sources()[0].id].chan == "kc"


# ── The comparison this file exists for ─────────────────────────────────────


@needs_clang
def test_a_schedule_plays_the_same_through_all_three_engines():
    """Bit-identical: oracle, block renderer, generated code.

    Without this there is no way to build a voice bank or a `Score`
    scheduler to the standard the rest of stage 7 was built to — the
    schedule is what makes a note *checkable*.
    """
    schedule = (Schedule()
                .change(0, "kc", 10)
                .change(128, "kc", 90)
                .change(256, "kc", 30))
    samples = 400
    graph = extract(KNOB, rate=RATE)
    control = schedule.control_for(graph)

    oracle = render(KNOB, samples / RATE, RATE,
                    control_every=BLOCK, schedule=schedule)
    assert run(graph, samples, block=BLOCK, control=control) == oracle
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, samples, block=BLOCK,
                          control=control) == oracle


def test_the_samples_follow_the_schedule():
    """And the numbers are the ones asked for, not merely consistent.

    Three engines agreeing on the wrong thing is the failure a comparison
    alone cannot see, so the shape is read back off the output: this synth
    hands the knob straight through, scaled.
    """
    schedule = (Schedule()
                .change(0, "kc", 10)
                .change(128, "kc", 90)
                .change(256, "kc", 30))
    out = render(KNOB, 400 / RATE, RATE, control_every=BLOCK,
                 schedule=schedule)
    assert round(out[64] * 1000) == 10
    assert round(out[130] * 1000) == 90, "the change at 128 is heard"
    assert round(out[127] * 1000) == 10, "and not before it"
    assert round(out[300] * 1000) == 30


def test_a_change_between_boundaries_lands_on_the_next_one():
    """Control rate is once per block, and a schedule cannot cheat it.

    A *value* may still name an instant inside the block — that is what
    `deliver` is for, and what makes onsets sample-accurate — but the value
    itself arrives when the control clock ticks.
    """
    schedule = Schedule().change(100, "kc", 90)      # between 64 and 128
    out = render(KNOB, 200 / RATE, RATE, control_every=BLOCK,
                 schedule=schedule)
    assert round(out[110] * 1000) == 40, "still the declared default"
    assert round(out[128] * 1000) == 90, "and heard at the next boundary"
