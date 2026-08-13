"""Graph extraction and the reference engine — `spec/liveaudio.md` stage 2.

**The bit-identical comparison is the point of this file.**  Everything else
here is structure: the graph has the nodes it should, it serialises, node
identity survives an edit.  What makes the stage worth doing is that the
extracted graph, interpreted one sample at a time, produces *the same
numbers* as `render()` — because that fixes the meaning of the graph before
stage 3 and stage 4 depend on it.

It has already earned its keep: the first version of the engine read a
`scan`'s input from the previous instant instead of this one, and this
comparison caught it on the first run.  `test_scan_reads_this_instants_input`
is that bug, pinned.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gestate.audio import parse_golden, render
from gestate.audioengine import State, render_block, run
from gestate.audioextract import ExtractError, extract

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
EXAMPLES = ["sine.ges", "blip.ges", "drums.ges", "knob.ges", "fm.ges",
            "pluck.ges", "twoknobs.ges"]

#: The ones with no control clock.  Block size is inaudible in these and
#: *defining* in `knob.ges`, so the invariance test below takes only these
#: — `test_control_rate_is_what_makes_the_block_size_audible` is the other
#: half of the same fact.
AUDIO_ONLY = ["sine.ges", "blip.ges", "drums.ges", "fm.ges", "pluck.ges"]


def _source(name: str) -> str:
    return (AUDIO_DIR / name).read_text()


def _golden(name: str):
    text = (AUDIO_DIR / name).with_suffix(".samples").read_text()
    return parse_golden(text)


def _block(header) -> int | None:
    """The block size a golden's schedule requires, or `None` for any.

    An audio-rate example is identical at every block size, so its golden
    names none.  A control-rate one is *defined* by where its boundaries
    fall, so `knob.ges`'s header carries `control_every` and the engine has
    to be run in blocks of exactly that — the same schedule the oracle was
    fed, which is what makes the two comparable at all.
    """
    return int(header["control_every"]) if "control_every" in header else None


# ── The comparison that fixes the meaning of the graph ──────────────────────


@pytest.mark.parametrize("name", EXAMPLES)
def test_the_graph_renders_what_the_oracle_renders(name):
    """Bit-identical over the whole committed window.

    Against the golden rather than a fresh `render()` because the graph
    runs in milliseconds where the interpreter takes seconds — and the
    golden *is* `render()`, pinned, which is what stage 0 was for.
    """
    header, want = _golden(name)
    graph = extract(_source(name), rate=int(header["rate"]))
    got = run(graph, len(want), block=_block(header))

    assert len(got) == len(want)
    if got != want:
        i = next(i for i, (a, b) in enumerate(zip(got, want)) if a != b)
        pytest.fail(f"{name} first differs at sample {i} of {len(want)}: "
                    f"graph {got[i]!r}, oracle {want[i]!r}")


@pytest.mark.parametrize("name", EXAMPLES)
def test_the_graph_agrees_with_a_fresh_render_too(name):
    """Short, and against the interpreter directly.

    The test above would pass if the goldens and the extractor were wrong
    in the same way — they cannot be, since one predates the other, but a
    comparison whose only oracle is a committed file is worth backing with
    one that runs the real evaluator.

    One block schedule for all three: an audio-rate example cannot tell,
    having no control clock for `control_every` to tick, and a control-rate
    one is only comparable when both sides are given the same boundaries.
    """
    rate, samples, block = 800, 24, 8
    graph = extract(_source(name), rate=rate)
    assert (run(graph, samples, block=block)
            == render(_source(name), samples / rate, rate,
                      control_every=block))


def test_scan_reads_this_instants_input():
    """The off-by-one this stage exists to get right.

    `scan (y x => x) 0 ticks` discards its state and keeps its input, so
    the samples are the sample numbers.  Had the engine read the *previous*
    instant's input — the obvious reading, and the one written first — they
    would lag by one and this would be `[0, 0, 1, 2, …]`.

    Why the obvious reading is wrong: `f z (head s)` sits inside `scan`'s
    `delay`, so it runs one instant later, and by then `s` has been
    overwritten in place with its next value.
    """
    src = ("sound : Sig Float\n"
           "sound = map toFloat (scan (y x => x) 0 ticks)\n")
    graph = extract(src, rate=100)
    got = run(graph, 6)
    assert got == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert got == render(src, 6 / 100, 100)


def test_zipsig_is_a_node_and_shares_what_it_can():
    """Two oscillators, one clock — the case no example covers.

    Both read the same source, so the graph is a DAG rather than a tree:
    the extractor gives them one `source` node between them and two
    `scan`s, because their arguments differ.
    """
    src = """
osc : Float -> Sig Float
osc hz = map sawOf (scan (p n => wrap (p + hz / sampleRate)) 0.0 ticks)

sound : Sig Float
sound = gain 0.4 (osc 220.0 + osc 330.0)
"""
    graph = extract(src, rate=1000)
    kinds = [n.kind for n in graph.nodes]
    assert kinds.count("source") == 1, "the clock is one node"
    assert kinds.count("scan") == 2, "two oscillators, two phases"
    assert kinds.count("zip") == 1
    zip_node = next(n for n in graph.nodes if n.kind == "zip")
    assert len(zip_node.inputs) == 2

    assert run(graph, 40) == render(src, 40 / 1000, 1000)


# ── The structure ───────────────────────────────────────────────────────────


def test_the_graph_is_the_signal_chain_and_nothing_else():
    """`blip`'s six nodes, in order, with the definitions inlined away.

    `gain` is not a node; it *becomes* the last one, its argument folded
    into the step.  `lowpass` is two — a zip carrying the sample and the
    coefficient, then the scan — because its coefficient is a **signal**,
    which is the shape every SVF filter always had; the constant `0.25`
    folds into the zip's step, so the pair is still straight-line
    arithmetic per sample.
    """
    graph = extract(_source("blip.ges"), rate=22050)
    assert [n.kind for n in graph.nodes] == [
        "source", "scan", "map", "map", "scan", "map"]
    assert [n.inputs for n in graph.nodes] == [(), (0,), (1,), (2,), (3,),
                                               (4,)]
    assert graph.out == 5
    assert graph.node(1).type_ == "Voice", "the scan's state is the voice"
    # The tag is read out of the layout rather than written as a number:
    # a constructor's tag is its *position among all of them*, so adding
    # one to `audio.ges` renumbers every later type.  Hardcoding it made
    # this test fail for `Played` arriving, which is not what it is about.
    voice_tag = graph.layouts["Voice"][0]["tag"]
    assert graph.node(1).init == (voice_tag, (0.0, 0)), "Voice 0.0 0"
    assert graph.node(3).type_ == "LowpassIn", "the zip carries the pair"
    assert graph.node(4).init == 0.0, "the filter starts silent"
    assert graph.rate == 22050


def test_constants_are_folded_so_the_graph_needs_no_prelude():
    """`sampleRate` is a definition and must not survive as a call.

    A graph handed to a code generator has to be self-contained; a node
    that still had to look up `sampleRate` would drag the whole prelude
    into the engine.
    """
    graph = extract(_source("blip.ges"), rate=22050)
    text = json.dumps(graph.to_dict())
    assert "sampleRate" not in text
    assert "22050" in text, "the rate is folded in as a literal"


def test_the_graph_serialises():
    graph = extract(_source("drums.ges"), rate=8000)
    blob = json.loads(json.dumps(graph.to_dict()))
    assert len(blob["nodes"]) == len(graph.nodes)
    assert blob["out"] == graph.out
    assert set(blob["funcs"]) == set(graph.funcs)
    # A constructor-valued initial state survives the round trip.
    kit = next(n for n in blob["nodes"] if n["type"] == "Kit")
    assert kit["init"]["fields"] == [0.0, 20250804, 0]


CONTROL = """
c2 : Chan Int
c2 = chan

knob : Sig Int
knob = 0 ::: mkSig (wait c2)

blend : Int -> Int -> Float
blend n k = sawOf (wrap (toFloat n / 40.0)) * toFloat k / 100.0

sound : Sig Float
sound = gain 0.5 (zip blend ticks knob)
"""


def test_the_two_clocks_are_partitioned_by_name():
    """`clock` is audio rate; any other channel a program declares is not.

    By name and not by channel id: ids are handed out in *evaluation*
    order, so the audio clock is perfectly capable of not being the lowest
    (`fixme.md` F90, F91).
    """
    graph = extract(CONTROL, rate=1000)
    sources = [n for n in graph.nodes if n.kind == "source"]
    assert [n.clock for n in sources] == ["audio", "control"]
    assert [n.origin for n in sources] == ["sound/ticks/source#0",
                                           "sound/knob/source#0"]


def test_a_third_clock_is_a_second_knob_and_is_allowed():
    """Two *rates* is the ceiling; two *channels* never was.

    This used to be `test_a_third_clock_is_refused`, and the rule it
    asserted conflated the two.  N control channels all tick at the same
    rate, at the same block boundary — a synth with three knobs needs no
    third rate.  The old rule cost a synth its parameters: one, or a record
    on one channel, which stage 5 then reset in full whenever a field was
    added to it.
    """
    src = CONTROL + """
c3 : Chan Int
c3 = chan

other : Sig Int
other = 0 ::: mkSig (wait c3)
"""
    src = src.replace("sound = gain 0.5 (zip blend ticks knob)",
                      "sound = gain 0.5 (zip blend ticks (zip plus knob other))")
    src = "plus : Int -> Int -> Int\nplus a b = a + b\n" + src
    graph = extract(src, rate=100)
    assert len(graph.control_sources()) == 2
    assert [n.clock for n in graph.nodes if n.kind == "source"] \
        == ["audio", "control", "control"]


def test_a_control_channel_must_carry_a_scalar():
    """What replaced the third-clock rule, and it is a real limit.

    A control value is **one slot** of the buffer the host fills, so a
    channel carrying a constructor with fields has nowhere to go.  It used
    to extract and then die inside the engine as `case on a
    non-constructor`, because the host supplied a scalar into a slot the
    graph read as a record — the failure was in the sound, not at the
    boundary.
    """
    src = """
Knobs := Knobs Int Int

kc : Chan Knobs
kc = chan

knobs : Sig Knobs
knobs = Knobs 40 20 ::: mkSig (wait kc)

blend : Int -> Knobs -> Float
blend n k = case k of
    Knobs a b -> toFloat (a + b) * 0.0001

sound : Sig Float
sound = zip blend ticks knobs
"""
    with pytest.raises(ExtractError, match="not a scalar"):
        extract(src, rate=100)


def test_one_clock_read_twice_is_one_node():
    """Two `mkSig (wait clock)` for the same channel is one source."""
    src = """
other : Sig Int
other = 0 ::: mkSig (wait clock)

sound : Sig Float
sound = map toFloat (zip (a b => a + b) ticks other)
"""
    graph = extract(src, rate=100)
    assert [n.kind for n in graph.nodes].count("source") == 1
    assert run(graph, 8) == render(src, 8 / 100, 100)


def test_extraction_refuses_a_program_outside_the_fragment():
    """No stage begins before the previous one verifies."""
    src = """
countdown : Int -> Float
countdown n = case n == 0 of
    True -> 0.0
    False -> countdown (n - 1) + 1.0

sound : Sig Float
sound = map countdown ticks
"""
    with pytest.raises(ExtractError, match="the static signal fragment"):
        extract(src, rate=100)


# ── Node identity, for stage 5's state migration ────────────────────────────


def _origins(src: str) -> list[str]:
    return [n.origin for n in extract(src, rate=4000).nodes]


def test_editing_a_step_function_does_not_move_a_node():
    """The case live coding is *for*: change the sound, keep the phase.

    Identity is a path of the definitions a node was inlined through, so a
    definition's body can change completely without moving anything.
    """
    before = _source("blip.ges")
    after = before.replace("decay v = v * v * v", "decay v = v * v")
    assert after != before
    assert _origins(after) == _origins(before)


def test_editing_a_constant_does_not_move_a_node():
    """Turning a knob is an edit to a step function's folded-in constant."""
    before = _source("blip.ges")
    after = before.replace("gain 0.6 (lowpass 0.25 raw)",
                           "gain 0.5 (lowpass 0.30 raw)")
    assert after != before
    assert _origins(after) == _origins(before)


def test_adding_a_node_leaves_the_ones_before_it_alone():
    """An insert downstream must not reset the oscillator."""
    before = _source("blip.ges")
    after = before.replace("gain 0.6 (lowpass 0.25 raw)",
                           "gain 0.6 (lowpass 0.25 (gain 0.9 raw))")
    origins = _origins(after)
    assert len(origins) == len(_origins(before)) + 1
    # The `ticks` source is shared and its origin is the *first* path
    # that reaches it — which, with `lowpass`'s coefficient a signal, is
    # the coefficient literal's own coercion (`fromFloat` → `constSig` →
    # `ticks`).  Asserted as the oscillator's own nodes plus the filter's,
    # which are the ones an insert downstream must not move.
    for kept in ("sound/raw/scan#0", "sound/raw/map#0",
                 "sound/lowpass/scan#0"):
        assert kept in origins


def test_a_second_call_of_the_same_definition_does_move_one():
    """The known limit of this scheme, pinned rather than hidden.

    Occurrences of one definition along one path are told apart by an
    index, so inserting a *second* `lowpass` renumbers the first.  The
    alternative — putting the arguments in the identity — is worse, because
    then tuning a filter would reset it, and tuning is the commoner edit.
    Recorded in `spec/liveaudio.md`, stage 5.
    """
    before = _source("blip.ges")
    after = before.replace("lowpass 0.25 raw", "lowpass 0.25 (lowpass 0.5 raw)")
    assert "sound/lowpass/scan#1" in _origins(after)
    assert "sound/lowpass/scan#1" not in _origins(before)


# ── The CLI ─────────────────────────────────────────────────────────────────


# ── Block rendering — `spec/liveaudio.md` stage 3 ───────────────────────────


BLOCK_SIZES = [1, 2, 3, 64, 1024]


@pytest.mark.parametrize("name", AUDIO_ONLY)
def test_the_block_size_is_not_audible(name):
    """Every block size, and the naive per-sample reference, agree exactly.

    This is the whole of stage 3's check.  A graph with no control-rate
    node has nothing in it that can notice where a block begins, so if the
    output moves when the block size does, the state is being carried
    wrongly across the boundary — which is the one thing blocks introduce.
    """
    header, want = _golden(name)
    graph = extract(_source(name), rate=int(header["rate"]))
    samples = len(want)

    reference = run(graph, samples)
    assert reference == want, "the naive run must still match the oracle"
    for block in BLOCK_SIZES:
        assert run(graph, samples, block=block) == want, f"block {block}"


def test_a_block_is_a_buffer_and_the_state_persists():
    """`render_block` is called repeatedly with the same state.

    That is what an audio callback does, so it is what the test does: the
    concatenation of the blocks must be the whole render, and the state
    object is the only thing carried between them.
    """
    graph = extract(_source("blip.ges"), rate=1000)
    state = State.initial(graph)
    out = []
    for size in (5, 1, 17, 3, 64):
        out += render_block(graph, state, size)
    assert out == run(graph, len(out))
    assert state.t == len(out)


def test_a_partial_last_block_is_not_special():
    graph = extract(_source("drums.ges"), rate=1000)
    assert run(graph, 50, block=8) == run(graph, 50)


# ── Control rate — the second clock, which now has a meaning ────────────────


@pytest.mark.parametrize("block", [4, 8, 16])
def test_control_rate_matches_the_oracle_at_every_block_size(block):
    """Open question 3, settled.

    A control-rate source updates at the start of a block and is held
    across it; `render(control_every=block)` is the same schedule in the
    interpreter, feeding both channels at once on a boundary so that `sync`
    reports `SyncBoth`.  The two agree sample for sample.
    """
    graph = extract(CONTROL, rate=1000)
    got = run(graph, 40, block=block)
    want = render(CONTROL, 40 / 1000, 1000, control_every=block)
    assert got == want


def test_a_scan_under_the_control_clock_accumulates_once():
    """Open question 3, **answered** — the case that reopened it.

    This is the program `examples/audio/knob.ges` reduced to what made the
    interpreter and the engine disagree: a `scan` *downstream of the control
    clock*.  While an instant was one arrival, feeding two channels was two
    instants, `sync` never saw `SyncBoth` from the driver, and the control
    tick advanced this `scan` an extra time — it added the old knob and the
    new one at every boundary, 40 + 8, where the engine held the value and
    added 8 once.

    For a graph of maps and zips the extra instant left no state behind,
    which is why stage 3's simpler test passed and why the claim there had
    to be narrowed to what it tested.  A `scan` is what shows it.

    An instant is now a *set* of arrivals (`react_instant`), so a block
    boundary is one instant on both clocks and the two agree.  The number
    below is the engine's, and it is pinned in both: 8 per boundary, not 48.
    """
    src = """
kc : Chan Int
kc = chan

knob : Sig Int
knob = 40 ::: mkSig (wait kc)

R := R Int Int

pack : Int -> Int -> R
pack n k = R n k

stepR : Float -> R -> Float
stepR p r = case r of
    R n k -> p + toFloat k / 1000.0

sound : Sig Float
sound = scan stepR 0.0 (zip pack ticks knob)
"""
    graph = extract(src, rate=1000)
    engine = run(graph, 16, block=8)
    oracle = render(src, 16 / 1000, 1000, control_every=8)

    assert engine == oracle, "including across the control tick, which is new"

    # One knob per boundary, in both.  48 here would be the old defect back:
    # the arriving 8 added on top of the held 40 in a single instant.
    assert round((oracle[8] - oracle[7]) * 1000) == 8
    assert round((engine[8] - engine[7]) * 1000) == 8

    # And the knob is *held* between boundaries rather than re-arriving:
    # every sample inside the block adds the same 8.
    assert round((oracle[12] - oracle[11]) * 1000) == 8


def test_control_rate_is_what_makes_the_block_size_audible():
    """The invariant above holds *because* nothing is on the control clock.

    `spec/liveaudio.md` said "block size must not be audible; if it is, the
    control/audio partition is wrong".  That is right for an audio-rate
    graph and exactly backwards for a control-rate one: a control node is
    *defined* as updating once per block, so changing the block changes
    when it updates.  Both facts are asserted here so neither can be
    mistaken for the other later.
    """
    graph = extract(CONTROL, rate=1000)
    assert run(graph, 40, block=8) != run(graph, 40, block=16)

    audio_only = extract(_source("blip.ges"), rate=1000)
    assert run(audio_only, 40, block=8) == run(audio_only, 40, block=16)


def test_the_control_value_is_held_not_interpolated():
    """Held constant across the block — the simple rule, stated in the spec.

    Interpolating is named there as a later refinement; this pins which of
    the two the engine currently does, so the refinement has to be a
    deliberate change rather than a drift.
    """
    graph = extract(CONTROL, rate=1000)
    control = graph.nodes[1]
    assert control.clock == "control"

    state = State.initial(graph)
    render_block(graph, state, 8)
    first = state.values[control.id]
    render_block(graph, state, 8)
    assert state.values[control.id] == 8, "updated at the block boundary"
    assert first == 0, "and held at its initial value before that"


def test_the_audio_clock_is_found_by_name_not_by_id():
    """`fixme.md` F91 — `min(reactive.chans)` was the wrong channel.

    Ids are handed out in evaluation order, so a program that declares its
    own channel can take id 0 and leave the audio clock at 1.  The renderer
    used to advance the lowest id every sample, which in that program is
    the user's channel: the clock never ticks and the synth never advances.
    """
    from gestate.audio import _channels, assemble
    from gestate.pipeline import compile as gcompile
    from gestate.reactive import init_program

    state = gcompile(assemble(CONTROL, 1000))
    reactive = init_program(state)
    audio, controls = _channels(state, reactive)
    assert audio != min(reactive.chans), (
        "this program is only a regression test while the clock is not "
        "the lowest id")
    assert controls == [min(reactive.chans)]

    # And the sound is right, which is what the wrong channel would break:
    # with the clock never ticking, every sample stays at the initial value.
    # (The knob is 0 until it first arrives, so this needs `control_every`
    # and a window past the first block to be a sound at all.)
    samples = render(CONTROL, 24 / 1000, 1000, control_every=8)
    assert any(s != 0.0 for s in samples)


def test_the_cli_prints_a_graph(capsys):
    """The retired door refuses by name and points at
    the replacement — the voices-retirement rule for a
    CLI (`spec/crust.md` era consolidation: one door,
    `gestate.audioperform`, beside the editors)."""
    from gestate.audiograph import main as retired_main

    assert retired_main([]) == 2
    err = capsys.readouterr().err
    assert "retired" in err
    assert "refused by name" in err


def test_two_knobs_are_driven_independently():
    """The point of a channel each: one moves without the other.

    The oracle drives every control channel with the same number, so a
    synth whose knobs were secretly one value would still match it — this
    is the test that a second channel is a second *parameter*.
    """
    graph = extract(_source("twoknobs.ges"), rate=2000)
    a, b = (n.id for n in graph.control_sources())

    def at(pitch, cutoff):
        return run(graph, 300, block=64,
                   control=lambda node, _t: pitch if node == a else cutoff)

    base = at(40, 70)
    assert at(90, 70) != base, "the pitch knob does nothing"
    assert at(40, 10) != base, "the cutoff knob does nothing"
    # And they are not the same knob under two names.
    assert at(90, 10) != at(10, 90)
