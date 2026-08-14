"""LLVM code generation — `spec/liveaudio.md` stage 4.

Two halves, and they need different things.

**The IR itself** is text, and the emitter imports nothing, so those tests
run everywhere.  They assert the properties the bit-identity argument rests
on: no fast-math flag anywhere, and generated symbols in their own
namespace.

**Running it** needs `clang`, and skips without one the way the MIDI tests
skip without `mido`.  That half is the stage's actual acceptance test: the
generated code, run offline, is bit-identical to stage 3 — and to stage 2,
and to `render()`, which are the same numbers all the way down.

Two bugs are pinned here because both were invisible at `-O2` and both
would have been heard rather than seen:

* `floor` collided with libm's, so `wrap` recursed until the stack ran out;
* a primitive's *name* is not its type — `prim_lt_int` legitimately arrives
  with two doubles.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from gestate.audio import parse_golden, render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiollvm import LLVMError, emit, run_native

AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"
EXAMPLES = ["blip.ges", "drums.ges", "knob.ges", "fm.ges", "pluck.ges",
            "twoknobs.ges", "stereo.ges"]

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")


def _source(name: str) -> str:
    return (AUDIO_DIR / name).read_text()


def _golden(name: str):
    return parse_golden((AUDIO_DIR / name).with_suffix(".samples").read_text())


def _block(header) -> int | None:
    """The block size a golden's schedule requires, or `None` for any.

    Only the control-rate example names one: its boundaries are where its
    knob updates, so a different block is a different buffer.  An audio-rate
    golden is identical at every block size, which is asserted separately.
    """
    return int(header["control_every"]) if "control_every" in header else None


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


# ── The IR, without building it ─────────────────────────────────────────────


@pytest.mark.parametrize("name", EXAMPLES)
def test_no_fast_math_flag_is_ever_emitted(name):
    """The whole reason the target is IR rather than C.

    A fast-math flag on a float instruction licenses reassociation, and
    `fast` implies flush-to-zero, which would silently delete the
    subnormals stage 0 found.  Emitting none is what makes `-O2` safe.
    """
    text = emit(extract(_source(name), rate=8000))
    for flag in ("fast", "nnan", "ninf", "nsz", "arcp", "contract", "afn",
                 "reassoc"):
        assert f" {flag} " not in text, f"`{flag}` reached the IR"
    assert "fmuladd" not in text, "an fma would change the arithmetic"


def test_generated_symbols_have_their_own_namespace():
    """`audio.ges` defines `floor`, and so does libm.

    At `-O0` LLVM lowers `llvm.floor.f64` to a *call* to `floor`, which
    bound to the generated function: `wrap` recursed half a million frames
    and segfaulted.  At `-O2` the intrinsic becomes an SSE instruction and
    nothing happens, which is why both levels are built below.
    """
    text = emit(extract(_source("blip.ges"), rate=8000))
    assert '@"gestate.floor"' in text
    assert "declare double @llvm.floor.f64(double)" in text

    # The two entry points keep their names — they are what the host calls.
    # Three now: `render_block_mix_f32` multiplies by a ramp and
    # accumulates, which is how two engines are crossfaded in the
    # engine rather than in the host.
    entry = {"render_block", "render_block_f32", "render_block_mix_f32"}
    defined = [line.split("@", 1)[1].split("(")[0]
               for line in text.splitlines() if line.startswith("define")]
    assert entry <= set(defined), "the entry points keep their names"
    for symbol in defined:
        assert symbol in entry or symbol.startswith('"gestate.'), \
            f"`{symbol}` could collide with a C library symbol"


def test_the_state_is_one_field_per_node():
    """A field index *is* a node id, which is what stage 5 migrates."""
    graph = extract(_source("blip.ges"), rate=8000)
    text = emit(graph)
    state = next(line for line in text.splitlines()
                 if line.startswith("%State"))
    # `t`, then Int, Voice, Float, LowpassIn (the zip `lowpass`'s
    # signal coefficient rides in), Float, Float.
    assert state == ('%State = type { i64, i64, %"Voice", double, '
                     '%"LowpassIn", double, double }')
    assert '%"Voice" = type { i64, double, i64 }' in text


def test_a_sum_type_with_unlike_constructors_is_refused():
    """The engine lays a data type out as one struct.

    `Maybe Float` would need a union, and a union layout is a decision
    nothing has needed — so it is an error naming the type rather than a
    struct that quietly reads the wrong field.
    """
    graph = extract(_source("blip.ges"), rate=8000)
    graph.layouts["Odd"] = [
        {"tag": 90, "name": "A", "fields": []},
        {"tag": 91, "name": "B", "fields": ["Float"]},
    ]
    graph.nodes[0].type_ = "Odd"
    with pytest.raises(LLVMError, match="different shapes"):
        emit(graph)


# ── Running it ──────────────────────────────────────────────────────────────


@needs_clang
@pytest.mark.parametrize("name", EXAMPLES)
def test_the_generated_code_is_bit_identical_to_the_oracle(name):
    """Stage 4's acceptance test, over the whole committed window.

    The golden buffer is `render()` pinned, so this is the generated engine
    against the interpreter — through the graph, the block renderer and a
    C compiler — with nothing rounded on the way.
    """
    header, want = _golden(name)
    graph = extract(_source(name), rate=int(header["rate"]))
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, len(want), block=_block(header))
    assert len(got) == len(want)
    if got != want:
        i = next(i for i, (a, b) in enumerate(zip(got, want)) if a != b)
        pytest.fail(f"{name} first differs at sample {i}: native {got[i]!r}, "
                    f"oracle {want[i]!r}")


@needs_clang
@pytest.mark.parametrize("name", EXAMPLES)
def test_optimised_and_unoptimised_builds_agree(name):
    """`-O2` may not reassociate, because no instruction says it may.

    This is the claim the target was chosen for, so it is checked rather
    than believed — and it is the comparison that found the `floor`
    collision, which only `-O0` could reach.
    """
    graph = extract(_source(name), rate=1000)
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, 120, opt="-O0") == \
               run_native(graph, d, 120, opt="-O2")


def test_a_mono_graph_emits_no_interleaving_arithmetic():
    """One channel must cost exactly what it cost before.

    The output store is the only thing stereo changed, and a mono graph has
    to come out of it unchanged — a multiply by one in the inner loop would
    be harmless and would also mean the two paths had been merged rather
    than the second added.
    """
    ir = emit(extract(_source("blip.ges"), rate=1000))
    assert "%kbase" not in ir
    assert "%base = getelementptr inbounds double, ptr %out, i64 %k" in ir


def test_a_stereo_graph_stores_both_channels_interleaved():
    graph = extract(_source("stereo.ges"), rate=1000)
    assert graph.channels() == 2
    ir = emit(graph)
    assert "%kbase = mul i64 %k, 2" in ir
    # Past the tag word: field 0 of the struct is the constructor tag.
    assert "extractvalue %\"Stereo\"" in ir


def test_an_output_type_that_is_not_floats_is_refused():
    """A frame is a record of `Float`s; anything else has no channel count."""
    from gestate.audioir import IRError

    graph = extract(_source("blip.ges"), rate=1000)
    graph.layouts["Odd"] = [{"tag": 1, "name": "Odd", "fields": ["Float", "Int"]}]
    graph.nodes[graph.out].type_ = "Odd"
    with pytest.raises(IRError, match="all `Float`"):
        emit(graph)


@needs_clang
def test_a_stereo_graph_runs_native_bit_identically_at_any_block():
    """The interleaving must not be a function of where the block ends."""
    header, want = _golden("stereo.ges")
    graph = extract(_source("stereo.ges"), rate=int(header["rate"]))
    with tempfile.TemporaryDirectory() as d:
        for block in (1, 7, 64):
            assert run_native(graph, d, len(want), block=block) == want


@needs_clang
@pytest.mark.parametrize("block", [1, 7, 64])
def test_the_block_size_is_not_audible_in_the_generated_code_either(block):
    header, want = _golden("drums.ges")
    graph = extract(_source("drums.ges"), rate=int(header["rate"]))
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, len(want), block=block) == want


@needs_clang
@pytest.mark.parametrize("block", [4, 8])
def test_control_rate_survives_code_generation(block):
    """The host hands the block's control value in; the engine holds it."""
    graph = extract(CONTROL, rate=1000)
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, 40, block=block)
    assert got == render(CONTROL, 40 / 1000, 1000, control_every=block)


@needs_clang
def test_division_floors_on_negative_operands():
    """Python's `//` and `%` floor; LLVM's `sdiv`/`srem` truncate.

    They agree on positives and differ on negatives, so an example that
    only ever divided positive numbers would pass with the correction
    missing.  `n - 7` is negative for the first seven samples.
    """
    src = ("sound : Sig Float\nsound = map (n => "
           "toFloat (prim_div_int (n - 7) 3) + "
           "toFloat (prim_mod_int (n - 7) 3) / 10.0) ticks\n")
    graph = extract(src, rate=100)
    with tempfile.TemporaryDirectory() as d:
        native = run_native(graph, d, 12)
    assert native == run(graph, 12) == render(src, 12 / 100, 100)
    assert native[0] == -2.8, "floor division, not truncation"


@needs_clang
def test_a_primitives_name_is_not_its_type():
    """`prim_lt_int` at `Float`, which the compiler generates on purpose.

    `helpers.py` and `elaborate.py` both emit the integer comparison for
    `Float`, because the G-machine's instruction is Python's `<` and that
    is correct on either.  A generator that trusted the name emits `icmp`
    on `double` and does not build; `drums.ges` reaches it through
    `decay`'s `t > len`.
    """
    src = ("sound : Sig Float\n"
           "sound = map (n => case toFloat n > 3.0 of\n"
           "    True -> 1.0\n"
           "    False -> 0.0) ticks\n")
    graph = extract(src, rate=100)
    assert "prim_lt_int" in str(graph.funcs), "the premise of this test"
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, 6) == run(graph, 6)


@needs_clang
def test_it_is_fast_enough_to_be_the_point_of_all_this():
    """The claim the whole plan rests on, measured.

    The interpreter renders ~1,400 samples a second against the 44,100 real
    time needs.  This is not a benchmark — it is the assertion that the gap
    is *closed*, with a wide margin so the test does not fail on a busy
    machine.
    """
    import ctypes
    import time

    from gestate.audiollvm import _slots, build, load

    graph = extract(_source("drums.ges"), rate=48000)
    with tempfile.TemporaryDirectory() as d:
        lib = load(build(graph, d))
        buf = (ctypes.c_double * 256)()
        state = ctypes.create_string_buffer(
            8 * (1 + sum(_slots(graph, n) for n in graph.nodes)))
        ptr = ctypes.cast(state, ctypes.c_void_p)
        start = time.perf_counter()
        for _ in range(400):                       # 102,400 samples
            lib.render_block(ptr, buf, 256, 0)
        elapsed = time.perf_counter() - start

    rate = 400 * 256 / elapsed
    assert rate > 48000 * 5, f"only {rate:,.0f} samples/sec"


# ── The CLI ─────────────────────────────────────────────────────────────────


def test_the_cli_writes_ir(capsys):
    """The retired door refuses by name and points at
    the replacement — the voices-retirement rule for a
    CLI (`spec/crust.md` era consolidation: one door,
    `gestate.audioperform`, beside the editors)."""
    from gestate.audiollvm import main as retired_main

    assert retired_main([]) == 2
    err = capsys.readouterr().err
    assert "retired" in err
    assert "library call" in err


@needs_clang
def test_several_knobs_reach_the_generated_code_in_the_right_slots():
    """One slot per control source, and the order is the graph's.

    A buffer indexed wrongly is silent in every way that matters — the
    synth plays, and the knobs are swapped.  So the two are driven to
    values that cannot be confused and checked against the Python engine,
    which is the oracle for a control schedule.
    """
    graph = extract(_source("twoknobs.ges"), rate=2000)
    a, b = (n.id for n in graph.control_sources())
    knobs = {a: 90, b: 15}
    control = lambda node, _t: knobs[node]          # noqa: E731

    want = run(graph, 300, block=64, control=control)
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, 300, block=64, control=control)
    assert got == want

    # Swapping them must change the sound, or the slots are interchangeable
    # and this test proves nothing.
    swapped = {a: 15, b: 90}
    with tempfile.TemporaryDirectory() as d:
        other = run_native(graph, d, 300, block=64,
                           control=lambda node, _t: swapped[node])
    assert other != got


# ── The output stage is the last thing before a speaker ─────────────────────
#
# Two failures can leave this program, and both of them arrive at hardware:
# a sample outside ±1, which the conversion to 16 bits *wraps* rather than
# clips, and a NaN, which a naive clamp does not reject at all.  Neither is
# hypothetical — the interpreter refuses to divide by zero, and the
# generated code has no such scruple, so the compiled engine is exactly the
# one that can produce them and exactly the one that drives the sound card.


#: `(1/n) * n` is 1 everywhere except `n = 0`, where it is `inf * 0` — a NaN
#: that no constant folder can settle, because `n` is the instant.
NAN_AT_ZERO = ("sound : Sig Float\n"
               "sound = map bad ticks\n"
               "\nbad : Int -> Float\n"
               "bad n = (1.0 / toFloat n) * toFloat n\n")


def test_a_naive_clamp_does_not_stop_a_nan_which_is_why_there_is_a_guard():
    """**The reason `safe_sample` exists**, stated as the thing that is
    surprising: `min`/`max` return the operand that is *not* NaN, so the
    obvious clamp passes a NaN straight through as its own bound.  IEEE
    `minNum`/`maxNum` in the generated code behave the same way.
    """
    nan = float("nan")
    assert max(-1.0, min(1.0, nan)) == 1.0, "the trap this guards against"


def test_the_guard_turns_a_broken_sample_into_silence():
    from gestate.audio import safe_sample

    assert safe_sample(float("nan")) == 0.0
    # Infinities need no special case; the clamp already bounds them.
    assert safe_sample(float("inf")) == 1.0
    assert safe_sample(float("-inf")) == -1.0
    assert safe_sample(1.2) == 1.0
    assert safe_sample(-3.0) == -1.0
    assert safe_sample(0.5) == 0.5


def test_the_generated_float_output_guards_before_it_clamps():
    """Order matters: the NaN test has to happen *before* `minnum`, because
    `minnum` is what would launder it into 1.0."""
    graph = extract(NAN_AT_ZERO, rate=4000)
    ir = emit(graph)
    assert "fcmp ord" in ir, "no NaN test in the generated output stage"
    guard = ir.index("fcmp ord")
    clamp = ir.index("llvm.minnum.f64(double %cl")
    assert guard < clamp, "the clamp would launder the NaN before the guard"


@needs_clang
def test_a_nan_reaches_the_device_as_silence_and_not_as_full_scale():
    """**The one that matters.**  Without the guard this sample leaves as
    +1.0 — sustained full-scale DC, which is maximum power into a voice
    coil that is not moving and so is not being cooled by moving.
    """
    import ctypes

    from gestate.audiollvm import build, load, state_size

    graph = extract(NAN_AT_ZERO, rate=4000)
    with tempfile.TemporaryDirectory() as directory:
        lib = load(build(graph, directory))
        lib.render_block_f32.restype = None
        lib.render_block_f32.argtypes = ([ctypes.c_void_p] * 2
                                         + [ctypes.c_int64, ctypes.c_void_p])
        state = ctypes.create_string_buffer(state_size(graph))
        buffer = (ctypes.c_float * 8)()
        lib.render_block_f32(ctypes.cast(state, ctypes.c_void_p),
                             ctypes.cast(buffer, ctypes.c_void_p), 8, None)
        out = list(buffer)

    assert not any(x != x for x in out), "a NaN reached the buffer"
    assert out[0] == 0.0, f"the NaN instant came out as {out[0]}"
    assert out[1:] == [1.0] * 7, "it damaged the samples that were fine"


def test_no_sample_written_to_a_wav_can_wrap_the_conversion():
    """A sample above 1.0 does not clip in the 16-bit conversion, it wraps —
    so the bound is what stops a 20% overshoot becoming a full-scale square
    wave, and it has to hold for every path that writes a file."""
    from gestate.audio import safe_sample

    for x in (-1e9, -1.0001, 0.0, 1.0001, 1e9, float("nan")):
        v = int(safe_sample(x) * 32767)
        assert -32767 <= v <= 32767, f"{x} packed as {v}"


@needs_clang
def test_a_scope_publishes_the_window_it_saw(tmp_path):
    """`spec/scope.md`: identity on the sound, and a ring the host may
    read — oldest first, holding exactly the samples that flowed
    through, matching the oracle's own ring to the bit."""
    import ctypes

    from gestate.audioengine import State, render_block, zero
    from gestate.audiollvm import build, load
    from gestate.audioir import SCOPE_LEN

    src = ('sound : Sig Float\n'
           'sound = scope "post" (0.2 * sine 220.0)\n')
    g = extract(src, rate=8000)
    assert [(l, n) for l, n, _ in g.scopes()] == [("post", SCOPE_LEN)]

    # The oracle: the sound, and the ring beside it.
    bare = extract('sound : Sig Float\nsound = 0.2 * sine 220.0\n',
                   rate=8000)
    want = run(bare, 256, block=64)
    assert run(g, 256, block=64) == want, "a scope changed the sound"

    # The generated code: render, then read the window back.
    lib = load(build(g, tmp_path))
    lib.render_block.restype = None
    lib.render_block.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_int64, ctypes.c_void_p]
    lib.read_scope_0.restype = None
    lib.read_scope_0.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_int64]
    from gestate.audiollvm import _slots
    width = 8 * (1 + sum(_slots(g, n) for n in g.nodes))
    state = ctypes.create_string_buffer(width)
    buf = (ctypes.c_double * 64)()
    for _ in range(4):
        lib.render_block(state, buf, 64, None)
    window = (ctypes.c_double * SCOPE_LEN)()
    lib.read_scope_0(state, window, SCOPE_LEN)
    got = list(window)
    # Oldest first: after 256 instants the window's tail is exactly
    # the 256 samples that played, in order, and everything before
    # them is the silence the ring was born with.
    assert got[-256:] == want, "the window is not the sound that flowed"
    assert all(v == 0.0 for v in got[:-256]), "silence before the sound"
