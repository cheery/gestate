"""`sin`, `cos`, `exp`, `log`, `sqrt` — and whether the two sides agree.

`spec/liveaudio.md` open question 2 is the reason this file exists.  Every
stage of the live-audio plan is verified by **exact** comparison against the
offline renderer, and that was legitimate for as long as a synth was `+ - *
/` on doubles: those are correctly rounded, so any two implementations
agree.  The transcendentals are not correctly rounded.  `sin` is whatever
the library computed, to within an ulp or so, and two libraries may
disagree in the last bits while both being right.

So the question is not "is our `sin` accurate" — it is **"is it the same
`sin` on both sides"**, and the answer is yes for a reason worth stating:
the interpreter calls CPython's `math.sin`, which calls libm's `sin`, and
generated code calls `llvm.sin.f64`, which lowers to a call to libm's `sin`
— the same one, on the same machine.  LLVM's *constant folder* evaluates it
with the host libm too, which is the case that would otherwise slip past a
runtime comparison.

**This is an assumption about the platform, not a proof.**  A different
libm on the machine that builds versus the one that runs would break it,
and the committed golden buffers are what would catch that: they are the
detector, which is why the two new synths have them.  `sqrt` is the
exception and is exact anywhere, IEEE 754 requiring it to be correctly
rounded.
"""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

import pytest

from gestate.audio import render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiollvm import emit, run_native
from gestate.gmachine import GmError, MATH_FLOAT
from gestate.pipeline import evaluate

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the IR with")


def _bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


# ── The language ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("fn", MATH_FLOAT)
def test_the_interpreter_computes_pythons_answer(fn):
    """Which is libm's, and is the definition the oracle carries."""
    x = 0.7
    got = float(evaluate(f"main : Float\nmain = {fn} {x}\n"))
    assert _bits(got) == _bits(getattr(math, fn)(x))


def test_tan_and_pow_are_written_in_the_language():
    """Not primitives, and deliberately.

    An identity in gestate is the *same expression* on both sides, so it is
    bit-identical by construction — where a sixth and seventh primitive
    would be two more functions whose libm agreement had to hold.  They are
    therefore not `math.tan`/`math.pow` and are not expected to be.
    """
    got = float(evaluate("main : Float\nmain = tan 0.5\n"))
    assert _bits(got) == _bits(math.sin(0.5) / math.cos(0.5))

    got = float(evaluate("main : Float\nmain = pow 2.0 10.0\n"))
    assert _bits(got) == _bits(math.exp(10.0 * math.log(2.0)))


@pytest.mark.parametrize("fn,arg", [
    ("log", "(negate 1.0)"),
    ("sqrt", "(negate 1.0)"),
    ("log", "0.0"),
    ("exp", "100000.0"),
])
def test_outside_the_domain_is_an_error_not_a_nan(fn, arg):
    """Python raises where C returns NaN or an infinity, so the two would
    *disagree* here.

    Reporting it is the only answer that does not quietly pick one of them:
    returning a NaN would make the interpreter agree with the engine by
    giving up the thing that makes the interpreter the oracle.  A synth
    that reaches one of these has a bug either way, and the message names
    the function and the argument.
    """
    with pytest.raises(GmError, match=f"{fn} (is undefined|overflowed)"):
        evaluate(f"main : Float\nmain = {fn} {arg}\n")


# ── The generated code ──────────────────────────────────────────────────────


@needs_clang
@pytest.mark.parametrize("fn", MATH_FLOAT)
def test_generated_code_agrees_with_python_over_the_whole_range(fn):
    """The measurement open question 2 asked for, one function at a time.

    A `map` over `ticks` puts each argument through the real pipeline —
    extractor, block renderer and `clang` — rather than through a hand-built
    kernel, so what is compared is what a synth would actually run.
    """
    # `ticks` counts instants, so the arguments are generated *inside* the
    # program as a ramp rather than fed in as a table — `1/128` of a step,
    # which sweeps a phase cycle, an envelope's 0..1 and on past both.
    # `log` and `sqrt` start at the first step to stay in their domain.
    scale, n = 128.0, 400
    first = 1 if fn in ("log", "sqrt") else 0
    src = (f"sound : Sig Float\n"
           f"sound = map (n => {fn} (toFloat (n + {first}) / {scale!r})) "
           f"ticks\n")
    want = [float(getattr(math, fn)((i + first) / scale)) for i in range(n)]

    graph = extract(src, rate=1000)
    assert run(graph, n) == want, "the block renderer"
    with tempfile.TemporaryDirectory() as d:
        assert run_native(graph, d, n, opt="-O0") == want, "generated, -O0"
        assert run_native(graph, d, n, opt="-O2") == want, "generated, -O2"


@needs_clang
def test_a_constant_argument_is_folded_and_still_agrees():
    """The case a runtime comparison cannot see.

    A synth folds constants into its nodes, so `sin <literal>` is a shape
    the extractor really produces — and at `-O2` LLVM evaluates it during
    compilation with its own folder rather than calling libm at run time.
    If that disagreed with CPython, the oracle and the engine would differ
    on exactly the expressions a synth is made of.
    """
    src = ("sound : Sig Float\n"
           "sound = map (n => sin 0.5 + cos 1.25 * toFloat n * 0.0) ticks\n")
    want = math.sin(0.5) + math.cos(1.25) * 0.0

    graph = extract(src, rate=1000)
    with tempfile.TemporaryDirectory() as d:
        got = run_native(graph, d, 8, opt="-O2")
        ir = emit(graph)
    assert all(_bits(s) == _bits(want) for s in got)

    # And the fold really happened, so the assertion above proves something.
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "m.ll"
        path.write_text(ir)
        out = subprocess.run(["clang", "-O2", "-S", "-emit-llvm",
                              str(path), "-o", "-"],
                             capture_output=True, text=True, check=True).stdout
    assert "@llvm.sin.f64" not in out, (
        "the sine survived -O2, so this test did not exercise the folder")


# `afn` — "approximate functions" — is the fast-math flag that specifically
# licenses LLVM to swap `llvm.sin.f64` for something cheaper and less
# accurate, which would break everything above.  It is not checked here:
# `test_audiollvm.py`'s `test_no_fast_math_flag_is_ever_emitted` already
# asserts it over every example, and both examples using a transcendental
# are in that list.


# ── The synths that use them ────────────────────────────────────────────────


AUDIO_DIR = Path(__file__).resolve().parent.parent / "examples" / "audio"


@pytest.mark.parametrize("name", ["fm.ges", "pluck.ges"])
def test_the_new_synths_are_where_the_transcendentals_earn_their_place(name):
    """A caller, in the sense `implementation_order.md` means it.

    `fm.ges` is a sine carrier and a sine modulator — the one instrument
    that cannot be written without `sin` at all — and `pluck.ges` uses `exp`
    for a decay envelope that a linear ramp only approximates.
    """
    source = (AUDIO_DIR / name).read_text()
    used = {fn for fn in MATH_FLOAT if fn in source}
    assert used, f"{name} uses no transcendental, so it argues for nothing"

    samples = render(source, 0.05, 2000)
    assert max(abs(s) for s in samples) > 0.05, "silent"
    assert all(-1.0 <= s <= 1.0 for s in samples), "out of range"
