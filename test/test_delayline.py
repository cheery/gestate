"""The `line` node — `feedback`, and what is built on it.

`spec/delaylines.md` is the design.  `feedback` is the first of the three
answers in it: **a `scan` with a longer arm**, where a `scan`'s step sees
the previous instant's output and this one's sees the output from `n`
instants ago.

    scan       f z s :  out[t] = f (out[t-1], s[t])
    feedback n f   s :  out[t] = f (out[t-n], s[t])

That shape is why it is first.  The loop is *inside* the node exactly as a
`scan`'s is, so the graph stays acyclic and `audiograph._check_recursion`
needs no relaxation at all — the hard half of the design is untouched, and
echo, comb, allpass and therefore reverb fall out of the easy half.

**Three engines, and they have to agree.**  The oracle is `signal.ges`'s
own definition run by the G-machine; the Python block engine is what the
graph *means*; the generated code is what plays.  A delay line is the
first node whose state is not one value, so every one of those three had
to learn something, and this file is where they are made to say the same
thing.
"""

from __future__ import annotations

import shutil
import tempfile

import pytest

from gestate.audio import assemble, render
from gestate.audioengine import run, zero
from gestate.audioextract import ExtractError, extract_analysis
from gestate.audiollvm import pack_state, state_size, unpack_state
from gestate.pipeline import analyse

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")

RATE = 4000

#: An impulse at sample 5 — **not at 0**, which a `line` skips for the
#: reason `scan` does: its input is read from inside a `delay`, so `s[0]`
#: never reaches the fold.
IMPULSE = ("trig : Sig Float\ntrig = map impulse ticks\n"
           "impulse : Int -> Float\nimpulse n = case n == 5 of\n"
           "    True -> 1.0\n    False -> 0.0\n")

COMB = IMPULSE + ("sound : Sig Float\n"
                  "sound = feedback 20 (y x => x + 0.6 * y) trig\n")


def _graph(source: str, rate: int = RATE):
    return extract_analysis(analyse(assemble(source, rate)), rate=rate)


# ── What the node is ────────────────────────────────────────────────────────


def test_it_extracts_to_one_line_node_of_the_length_asked_for():
    graph = _graph(COMB)
    lines = [n for n in graph.nodes if n.kind == "line"]
    assert len(lines) == 1
    assert lines[0].length == 20


def test_the_graph_stays_acyclic():
    """The point of `feedback` being first: a node that reads its own past
    is not an edge that closes a cycle, so nothing about the graph's shape
    changes."""
    graph = _graph(COMB)
    for node in graph.nodes:
        assert node.id not in node.inputs
        for i in node.inputs:
            assert i < node.id, "inputs come earlier, as in any DAG"


def test_a_length_of_nothing_is_refused_with_a_reason():
    """`feedback 0` reaches back to nothing.

    Written expecting to test a length that *varies*, which turned out to
    be unreachable: `feedback : Int -> …`, and an `Int` at signal level is
    always built from literals, so the constant folder settles every one of
    them before the graph exists.  A knob is a `Sig Int` and does not
    typecheck there at all.  The "not known before the program runs" branch
    is therefore a guard rather than a live path — kept, because the type
    that makes it unreachable is not the one that would keep it so.
    """
    source = IMPULSE + ("sound : Sig Float\n"
                        "sound = feedback (floor 0.5) (y x => x + y) trig\n")
    with pytest.raises(ExtractError) as caught:
        _graph(source)
    assert "reaches back to nothing" in str(caught.value)


def test_a_length_folded_from_seconds_is_accepted():
    """`feedback (seconds 0.01) …` — the constant folder settles it before
    the graph exists, which is what `echo` and `comb` are written on."""
    graph = _graph(IMPULSE + "sound : Sig Float\n"
                   "sound = feedback (seconds 0.01) (y x => x + 0.5 * y) trig\n")
    line = next(n for n in graph.nodes if n.kind == "line")
    assert line.length == int(0.01 * RATE)


# ── What it computes ────────────────────────────────────────────────────────


def test_a_feedback_comb_is_a_decaying_train_of_impulses():
    xs = list(render(COMB, 130 / RATE, RATE))
    fired = [(i, round(x, 6)) for i, x in enumerate(xs) if abs(x) > 1e-9]
    # Twenty samples apart, and 0.6 of the last each time — exactly.
    assert [i for i, _x in fired] == [5, 25, 45, 65, 85, 105, 125]
    assert [x for _i, x in fired] == [round(0.6 ** k, 6) for k in range(7)]


def test_the_first_instant_is_silent_as_a_scan_s_is():
    """Not a wart to work around — it is what `signal.ges`'s definition
    says, and the definition is what the graph means.  A former that fired
    at `t = 0` would need `s[0]` under the fold, and `scan` reads its input
    from inside a `delay`, so `s[0]` never reaches one."""
    source = ("trig : Sig Float\ntrig = map impulse ticks\n"
              "impulse : Int -> Float\nimpulse n = case n == 0 of\n"
              "    True -> 1.0\n    False -> 0.0\n"
              "sound : Sig Float\n"
              "sound = feedback 20 (y x => x + 0.6 * y) trig\n")
    assert not any(abs(x) > 1e-12 for x in render(source, 60 / RATE, RATE))


# ── The three engines say the same thing ────────────────────────────────────


def test_the_oracle_and_the_block_engine_agree():
    """`signal.ges`'s definition carries the line as an ordinary *list* —
    a thing the interpreter can do and the engine cannot, which is the
    whole reason the engine has a node kind instead."""
    n = 130
    assert list(render(COMB, n / RATE, RATE)) == list(run(_graph(COMB), n))


@needs_clang
def test_the_generated_code_agrees_too():
    n = 130
    graph = _graph(COMB)
    with tempfile.TemporaryDirectory() as directory:
        from gestate.audiollvm import run_native

        native = list(run_native(graph, directory, n, block=64))
    assert native == list(run(graph, n))


# ── The state a line carries ────────────────────────────────────────────────


def test_the_state_struct_makes_room_for_the_whole_ring():
    """**The bug this test exists for was a segfault.**  A node's value and
    its state are the same thing everywhere except here, and a line counted
    as one word gave the generated code a buffer shorter than the struct it
    writes through — the ring read uninitialised memory until the overflow
    took the process down.
    """
    graph = _graph(COMB)
    line = next(n for n in graph.nodes if n.kind == "line")
    plain = sum(1 for n in graph.nodes if n.kind != "line")
    assert state_size(graph) == 8 * (1 + plain + line.length)


def test_the_ring_survives_the_trip_through_the_native_layout():
    graph = _graph(COMB)
    line = next(n for n in graph.nodes if n.kind == "line")
    values = [zero(graph, n.type_) for n in graph.nodes]
    rings = {line.id: [float(i) for i in range(line.length)]}

    back, t, lines = unpack_state(graph, pack_state(graph, values, 7, rings))
    assert t == 7
    assert lines[line.id] == rings[line.id]
    # A line's *value* is the sample it last produced, which is the slot
    # the cursor has just moved off.
    assert back[line.id] == rings[line.id][(7 - 1) % line.length]


def test_a_line_whose_length_changed_does_not_keep_its_buffer():
    """A ring's meaning is positional — slot `k` is "k instants ago" — so
    carrying it into a line of another length reads the wrong instants.
    Editing the number restarts that line and nothing else."""
    from gestate.audioengine import State, migrate

    old = _graph(COMB)
    new = _graph(IMPULSE + "sound : Sig Float\n"
                 "sound = feedback 30 (y x => x + 0.6 * y) trig\n")
    was = next(n for n in old.nodes if n.kind == "line")
    state = State([zero(old, n.type_) for n in old.nodes], 100,
                  {was.id: [1.0] * was.length})

    carried = migrate(old, state, new)
    now = next(n for n in new.nodes if n.kind == "line")
    assert now.id not in carried.lines, "it kept a ring of the wrong length"


def test_a_line_that_did_not_change_keeps_its_buffer():
    from gestate.audioengine import State, migrate

    old, new = _graph(COMB), _graph(COMB)
    was = next(n for n in old.nodes if n.kind == "line")
    ring = [float(i) for i in range(was.length)]
    state = State([zero(old, n.type_) for n in old.nodes], 100, {was.id: ring})

    carried = migrate(old, state, new)
    now = next(n for n in new.nodes if n.kind == "line")
    assert carried.lines[now.id] == ring


# ── `tap` — a moving read ───────────────────────────────────────────────────


TAP = IMPULSE + "sound : Sig Float\nsound = tap 64 20.0 trig\n"


def test_a_tap_delays_by_the_position_it_is_given():
    xs = list(render(TAP, 60 / RATE, RATE))
    assert [(i, x) for i, x in enumerate(xs) if x] == [(25, 1.0)]


def test_a_fractional_position_is_interpolated():
    """The reason `tap` exists rather than a whole-sample `delay`: a
    position that moves has to glide, and a nearest-sample read clicks."""
    src = IMPULSE + "sound : Sig Float\nsound = tap 64 20.5 trig\n"
    xs = list(render(src, 60 / RATE, RATE))
    assert [(i, x) for i, x in enumerate(xs) if x] == [(25, 0.5), (26, 0.5)]


def test_the_position_is_clamped_to_at_least_one_sample():
    """**Not fussiness.**  A tap that could hand back the sample it was
    given this instant would let a cycle close with nothing in it — and
    reading at least one back is what makes this node's value a function of
    its *state*, which is the whole reason it is the cycle-breaker."""
    src = IMPULSE + "sound : Sig Float\nsound = tap 64 0.0 trig\n"
    xs = list(render(src, 20 / RATE, RATE))
    assert [(i, x) for i, x in enumerate(xs) if x] == [(6, 1.0)]


def test_a_moving_position_bends_the_pitch():
    """Vibrato, which is what a moving tap is."""
    rate = 4000
    src = ("sound : Sig Float\n"
           "sound = tap 512 (200.0 + 150.0 * sine 6.0) (sine 220.0)\n")
    xs = list(render(src, 900 / rate, rate))[400:]

    def crossings(ys):
        return sum(1 for i in range(1, len(ys)) if (ys[i - 1] < 0) != (ys[i] < 0))

    half = len(xs) // 2
    assert crossings(xs[:half]) != crossings(xs[half:]), "the pitch is steady"


def test_the_tap_agrees_across_all_three_engines():
    """The oracle carries the line as a list and reads it by index; the
    block engine and the generated code index a ring.  Same samples."""
    n = 60
    graph = _graph(TAP)
    assert list(render(TAP, n / RATE, RATE)) == list(run(graph, n))


@needs_clang
def test_the_generated_tap_agrees_too():
    n = 60
    graph = _graph(TAP)
    with tempfile.TemporaryDirectory() as directory:
        from gestate.audiollvm import run_native

        native = list(run_native(graph, directory, n, block=16))
    assert native == list(run(graph, n))


def test_a_taps_state_is_its_whole_ring():
    """The same trap `feedback` fell into: a node's value and its state are
    one thing everywhere except a delay line, and getting it wrong gave the
    generated code a buffer shorter than the struct it writes through."""
    graph = _graph(TAP)
    tap = next(n for n in graph.nodes if n.kind == "tap")
    assert tap.length == 64
    plain = sum(1 for n in graph.nodes if n.kind != "tap")
    assert state_size(graph) == 8 * (1 + plain + tap.length)


# ── What is built on it ─────────────────────────────────────────────────────


def test_echo_repeats_at_the_time_asked_for_and_decays_by_the_amount():
    xs = list(render("trig : Sig Float\ntrig = map impulse ticks\n"
                     "impulse : Int -> Float\nimpulse n = case n == 5 of\n"
                     "    True -> 1.0\n    False -> 0.0\n"
                     "sound : Sig Float\nsound = echo 0.01 0.5 trig\n",
                     0.06, 8000))
    fired = [(i, round(x, 4)) for i, x in enumerate(xs) if abs(x) > 1e-9]
    # 0.01 s at 8 kHz is 80 samples, and each repeat is half the last.
    assert fired[:4] == [(5, 1.0), (85, 0.5), (165, 0.25), (245, 0.125)]


def test_echo_cannot_be_asked_to_grow_without_bound():
    """Feedback at or above 1.0 never dies away, so it is clamped."""
    xs = render("sound : Sig Float\nsound = echo 0.005 4.0 (dust 9 200.0)\n",
                0.4, 8000)
    assert max(abs(x) for x in xs) < 60.0, "it ran away"


def test_a_comb_resonates_on_the_harmonics_of_its_frequency():
    """A delay of `1/hz` fed back on itself resonates at `hz` and at every
    multiple of it — which is the comb its response is named for."""
    import math

    rate, hz = 8000, 250.0
    xs = list(render(f"sound : Sig Float\n"
                     f"sound = comb {hz} 0.9 (0.2 * white 4)\n", 0.25, rate))
    n = len(xs)

    def energy_at(f: float) -> float:
        k = round(f * n / rate)
        w = 2 * math.pi * k / n
        re = sum(x * math.cos(w * t) for t, x in enumerate(xs))
        im = sum(x * math.sin(w * t) for t, x in enumerate(xs))
        return re * re + im * im

    # A harmonic against the frequency midway to the next one.
    for k in (1, 2, 3):
        on, between = energy_at(hz * k), energy_at(hz * (k + 0.5))
        assert on > 4 * between, f"harmonic {k}: {on:.3g} vs {between:.3g}"


# ── `loop` — a line with a filter in it ─────────────────────────────────────
#
# `feedback`'s ring holds samples, so its step reaches one instant: the one
# `n` back.  A `loop`'s holds whole *states*, and that brings a second
# instant within reach — the slot written last time round.  Karplus-Strong
# needs exactly that second one, which is why the node exists.

#: The sample that left the line, and the one that left it before that.
WG_TYPE = """
Wg := Wg Float Float

wgStep : Wg -> Wg -> Float -> Wg
wgStep prev old x = case prev of
    Wg y p -> case old of
        Wg yn q -> Wg (x + 0.5 * (yn + p)) yn

wgOut : Wg -> Float
wgOut st = case st of
    Wg y p -> y
"""

WG = IMPULSE + WG_TYPE + ("sound : Sig Float\n"
                          "sound = map wgOut (loop 32 wgStep (Wg 0.0 0.0) trig)\n")


def _loop(step: str, init: str = "0.0", n: int = 8) -> str:
    """A `loop` over a bare `Float` state, which is `feedback` plus an arm."""
    return IMPULSE + (f"sound : Sig Float\n"
                      f"sound = loop {n} (p o x => {step}) {init} trig\n")


def test_a_loop_extracts_to_one_node_of_the_length_asked_for():
    graph = _graph(WG)
    loops = [n for n in graph.nodes if n.kind == "loop"]
    assert len(loops) == 1
    assert loops[0].length == 32
    assert loops[0].type_ == "Wg", "its element type is its state, as a scan's is"


def test_a_loop_leaves_the_graph_acyclic():
    """The loop is inside the node, as `scan`'s and `feedback`'s are — a
    feedback path that has to leave the node is what `tap` is for."""
    for node in _graph(WG).nodes:
        assert node.id not in node.inputs
        for i in node.inputs:
            assert i < node.id


def test_the_two_arms_reach_different_instants():
    """The far arm is `n` instants back and the near one is a single
    instant back.  Fed the same impulse, one recirculates every `n` samples
    and the other every sample."""
    far = list(render(_loop("x + 0.5 * o"), 40 / RATE, RATE))
    near = list(render(_loop("x + 0.5 * p"), 40 / RATE, RATE))
    assert far[5] == 1.0 and near[5] == 1.0, "the impulse itself"
    assert far[6] == 0.0, "the far arm has nothing to say for 8 samples"
    assert far[5 + 8] == 0.5, "and then it does, once round the ring"
    assert near[6] == 0.5, "the near arm repeats at once"
    assert near[7] == 0.25, "and keeps halving, being a one-sample loop"


def test_at_a_length_of_one_a_loop_is_a_feedback():
    """Both arms land on the same slot, so the step's two states are the
    same state and what is left is `scan` with a chosen initial value."""
    step = "x + 0.6 * o"
    as_loop = list(render(_loop(step, n=1), 40 / RATE, RATE))
    as_line = list(render(IMPULSE + "sound : Sig Float\n"
                          "sound = feedback 1 (y x => x + 0.6 * y) trig\n",
                          40 / RATE, RATE))
    assert as_loop == as_line
    assert list(render(_loop("x + 0.6 * p", n=1), 40 / RATE, RATE)) == as_line


def test_the_first_instant_is_the_initial_state_and_not_silence():
    """`feedback` starts at silence because its ring holds samples; a
    `loop`'s holds the program's own state, and `z` is where it said to
    start.  That is `scan`'s rule."""
    xs = list(render(_loop("p", init="0.25"), 4 / RATE, RATE))
    assert xs[0] == 0.25
    graph = _graph(_loop("p", init="0.25"))
    assert list(run(graph, 4)) == xs


def test_a_plucked_string_decays_without_being_told_to():
    """Karplus-Strong: the averaging is a lowpass, so each round trip loses
    the highest partial first and the sound dies from the top down."""
    xs = list(render(WG, 0.25, RATE))
    windows = [max(abs(x) for x in xs[k:k + 64]) for k in (0, 200, 500, 900)]
    assert windows[0] > 0.4, "it never got going"
    assert all(a > b for a, b in zip(windows, windows[1:])), windows
    assert windows[-1] < 0.5 * windows[0]


def test_a_plucked_string_rings_at_the_length_of_its_line():
    """A round trip of `n` samples is `rate / n` hertz — the pitch a string
    of that length plays."""
    xs = list(render(WG, 0.2, RATE))[100:]

    def agreement(lag: int) -> float:
        return sum(a * b for a, b in zip(xs, xs[lag:]))

    best = max(range(8, 65), key=agreement)
    assert best in (32, 33), f"it rang at a lag of {best}, not its 32"


def test_the_oracle_and_the_block_engine_agree_on_a_loop():
    n = 200
    assert list(render(WG, n / RATE, RATE)) == list(run(_graph(WG), n))


@needs_clang
def test_the_generated_code_agrees_on_a_loop_too():
    n = 200
    graph = _graph(WG)
    with tempfile.TemporaryDirectory() as directory:
        from gestate.audiollvm import run_native

        native = list(run_native(graph, directory, n, block=64))
    assert native == list(run(graph, n))


def test_a_loops_state_is_its_whole_ring_of_states():
    """**Wider than a line's**, and that is the price of the second arm: a
    ring of `n` copies of the whole state rather than `n` samples.  `Wg` is
    a tag and two fields, so a 32-sample string is 96 words where a
    `feedback` of the same length would be 32.

    Getting this wrong is a segfault rather than a wrong number — the host
    allocates `%State` from it.
    """
    graph = _graph(WG)
    node = next(n for n in graph.nodes if n.kind == "loop")
    width = graph.words(node.type_)
    assert width == 3, "a tag and two floats"
    plain = sum(graph.words(n.type_) for n in graph.nodes if n.kind != "loop")
    assert state_size(graph) == 8 * (1 + plain + width * node.length)


def test_a_loops_ring_survives_the_native_layout():
    graph = _graph(WG)
    node = next(n for n in graph.nodes if n.kind == "loop")
    values = [zero(graph, n.type_) for n in graph.nodes]
    # A `Wg` is `(tag, fields)`; the tag is whatever the constructor got.
    tag = node.init[0]
    ring = [(tag, (float(i), float(-i))) for i in range(node.length)]

    back, t, lines = unpack_state(graph,
                                  pack_state(graph, values, 9, {node.id: ring}))
    assert t == 9
    assert lines[node.id] == ring
    assert back[node.id] == ring[(9 - 1) % node.length]


def test_a_fresh_loops_ring_starts_at_its_initial_state():
    """Silence would be wrong here for the reason the first instant is: both
    arms read `z` before anything has been written, and a ring of zeroes
    would only agree with that when `z` happens to be zero."""
    source = IMPULSE + WG_TYPE + (
        "sound : Sig Float\n"
        "sound = map wgOut (loop 4 wgStep (Wg 0.5 0.25) trig)\n")
    graph = _graph(source)
    node = next(n for n in graph.nodes if n.kind == "loop")
    _back, _t, lines = unpack_state(
        graph, pack_state(graph, [zero(graph, n.type_) for n in graph.nodes], 0))
    assert node.init[1] == (0.5, 0.25), "the `z` the program wrote"
    assert lines[node.id] == [node.init] * 4


def test_a_loop_whose_length_changed_does_not_keep_its_buffer():
    from gestate.audioengine import State, migrate

    old = _graph(WG)
    new = _graph(IMPULSE + WG_TYPE + (
        "sound : Sig Float\n"
        "sound = map wgOut (loop 33 wgStep (Wg 0.0 0.0) trig)\n"))
    was = next(n for n in old.nodes if n.kind == "loop")
    state = State([zero(old, n.type_) for n in old.nodes], 100,
                  {was.id: [was.init] * was.length})

    carried = migrate(old, state, new)
    now = next(n for n in new.nodes if n.kind == "loop")
    assert now.id not in carried.lines


def test_a_loop_that_did_not_change_keeps_its_buffer():
    """Retuning the *step* of a ringing string keeps the string ringing —
    which is what live coding a physical model is."""
    from gestate.audioengine import State, migrate

    old, new = _graph(WG), _graph(WG)
    was = next(n for n in old.nodes if n.kind == "loop")
    ring = [(was.init[0], (float(i), 0.0)) for i in range(was.length)]
    state = State([zero(old, n.type_) for n in old.nodes], 100, {was.id: ring})

    carried = migrate(old, state, new)
    now = next(n for n in new.nodes if n.kind == "loop")
    assert carried.lines[now.id] == ring


# ── `slide` — the position becomes a signal ─────────────────────────────────
#
# `tap`'s interpolated moving read closed into `feedback`'s loop: the ring
# holds the node's own output and the length of the feedback path is a
# *signal*.  A constant position must therefore sound exactly like the
# `feedback` it degenerates to, a fractional one must split a repeat
# across the two samples either side, and a moving one is a glissando.

SLIDE_COMB = IMPULSE + (
    "sound : Sig Float\n"
    "sound = slide 40 (y x => x + 0.6 * y) (!20.0) trig\n")


def test_a_slide_at_a_constant_position_is_a_feedback_comb():
    n = 120
    graph = _graph(SLIDE_COMB)
    got = run(graph, n)
    plain = run(_graph(IMPULSE + (
        "sound : Sig Float\n"
        "sound = feedback 20 (y x => x + 0.6 * y) trig\n")), n)
    assert [round(v, 12) for v in got] == [round(v, 12) for v in plain]


def test_the_three_engines_agree_about_a_slide():
    """The whole method, applied to the new node: the oracle is the
    definition, the block engine is the meaning, the generated code is
    what plays — and a block boundary must not be audible."""
    n = 160
    src = IMPULSE + (
        "pos : Int -> Float\n"
        "pos t = 12.0 + toFloat t * 0.05\n\n"
        "sound : Sig Float\n"
        "sound = slide 64 (y x => x + 0.7 * y) (map pos ticks) trig\n")
    oracle = render(src, n / RATE, RATE)
    graph = _graph(src)
    blockless = run(graph, n)
    blocked = run(_graph(src), n, block=13)
    assert oracle == blockless == blocked


@needs_clang
def test_the_generated_slide_is_bit_identical():
    from gestate.audiollvm import run_native

    n = 160
    src = IMPULSE + (
        "pos : Int -> Float\n"
        "pos t = 12.0 + toFloat t * 0.05\n\n"
        "sound : Sig Float\n"
        "sound = slide 64 (y x => x + 0.7 * y) (map pos ticks) trig\n")
    graph = _graph(src)
    with tempfile.TemporaryDirectory() as d:
        native = run_native(graph, d, n, block=13)
    assert native == run(graph, n)


def test_a_fractional_position_splits_the_repeat():
    """Position 20.5 puts the first repeat *between* two samples: the lerp
    lands 0.3 on each neighbour, which is the interpolation doing exactly
    what `tap`'s does — this is the sample-accurate half of a slide's
    tuning, measured rather than trusted."""
    got = run(_graph(IMPULSE + (
        "sound : Sig Float\n"
        "sound = slide 40 (y x => x + 0.6 * y) (!20.5) trig\n")), 60)
    repeat = {i: round(v, 6) for i, v in enumerate(got) if 20 < i < 30 and v}
    assert repeat == {25: 0.3, 26: 0.3}


def test_a_moving_position_widens_the_echo():
    src = IMPULSE + (
        "pos : Int -> Float\n"
        "pos t = 12.0 + toFloat t * 0.05\n\n"
        "sound : Sig Float\n"
        "sound = slide 64 (y x => x + 0.7 * y) (map pos ticks) trig\n")
    got = run(_graph(src), 200)
    onsets = [i for i, v in enumerate(got) if abs(v) > 1e-3]
    heads = [i for i in onsets if i - 1 not in onsets]
    gaps = [b - a for a, b in zip(heads, heads[1:])]
    assert gaps == sorted(gaps) and gaps[0] < gaps[-1], \
        f"a rising position should stretch the repeats: {gaps}"


def test_a_slide_with_no_room_is_refused_with_a_reason():
    with pytest.raises(ExtractError) as err:
        _graph(IMPULSE + (
            "sound : Sig Float\n"
            "sound = slide 1 (y x => x + y) (!1.0) trig\n"))
    assert "room to move" in str(err.value)
