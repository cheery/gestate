"""`on <points> x` — envelopes at audio rate.

`audio.ges` defines `on` by walking a cons list, which is the readable
definition and the one an interpreted program runs.  The static audio
fragment refuses it, so `gestate/envexpand.py` rewrites a call whose points
are known at compile time into a balanced tree of comparisons.

**The rewrite is checked against something outside the language.**  All
three engines run the *rewritten* expression, so comparing them to each
other cannot catch a wrong tree — they would agree on the same wrong
answer, which is exactly what happened while this was being written: the
leaf indices were off by one and there was no "past the last point" leaf,
and interpreter, block engine and generated code agreed on all of it.
`tempo.value_on` is the independent reading, and it is what says the tree
is right.
"""

from __future__ import annotations

import math
import shutil
import tempfile

import pytest

from gestate.audio import render
from gestate.audioengine import run
from gestate.audioextract import extract
from gestate.audiograph import check
from gestate.audiollvm import run_native
from gestate.tempo import value_on

needs_clang = pytest.mark.skipif(shutil.which("clang") is None,
                                 reason="no clang to build the engine with")

#: A curve with every shape in it: a step, a ramp, a ramp down, and both
#: ends to run past.
CURVE = [(0.0, False, 0.2), (2.0, True, 0.9), (5.0, False, 0.4),
         (9.0, True, 0.75), (13.0, False, 0.1), (16.0, True, 1.0)]


def _literal(points) -> str:
    return "[" + ", ".join(
        f"{'Ramp' if r else 'Step'} {a} {v}" for a, r, v in points) + "]"


def _program(points, expr: str = "toFloat n") -> str:
    return (f"pts : List Envelope\npts = {_literal(points)}\n\n"
            f"sound : Sig Float\nsound = map (n => on pts ({expr})) ticks\n")


# ── The point of the exercise ───────────────────────────────────────────────


def test_an_envelope_read_per_sample_is_in_the_fragment():
    """**What the rewrite is for.**

    Without it this is `on: takes a parameter of type List Envelope, which
    is a list, which is recursive and so has no fixed size` — the fragment
    refusing a cons walk at audio rate, correctly.
    """
    report = check(_program(CURVE), rate=8000)
    assert report.errors == [], "\n".join(report.errors)


def test_the_unrewritten_definition_still_says_what_it_means():
    """A list whose contents are *not* known stays a list, and is refused.

    The rewrite declining to fire is not a failure: the program means what
    it wrote, and the fragment reports it in terms of the list it actually
    is rather than in terms of a rewrite that did not happen.
    """
    source = ("pts : List Envelope\n"
              "pts = case 1 < 2 of\n"
              "    True -> [Step 0.0 1.0]\n"
              "    False -> [Step 0.0 2.0]\n\n"
              "sound : Sig Float\n"
              "sound = map (n => on pts (toFloat n)) ticks\n")
    report = check(source, rate=8000)
    assert any("is a list" in e for e in report.errors), report.errors


# ── Against a reading from outside the language ─────────────────────────────


@pytest.mark.parametrize("points", [
    CURVE,
    [(0.0, False, 0.5)],                                   # one point
    [(0.0, False, 0.0), (1.0, True, 1.0)],                 # one ramp
    [(0.0, False, 0.0), (4.0, False, 1.0)],                # one step
    [(2.0, False, 0.3), (4.0, True, 0.8)],                 # starts late
    [(0.0, False, 0.0), (0.0, True, 1.0), (3.0, True, 0.2)],  # zero-width
])
def test_the_rewrite_computes_what_the_envelope_means(points):
    """Every instant, against `tempo.value_on`.

    Includes both ends deliberately: the clamped regions are where the
    first version of this was wrong, and they are also the ones a clock
    reaches in ordinary use.
    """
    n = 24
    got = render(_program(points), n, 1)
    want = [value_on(points, float(i)) for i in range(n)]
    assert got == pytest.approx(want, abs=1e-12)


def test_it_holds_the_last_value_rather_than_running_off_the_line():
    """**The leaf that was missing.**

    A tree over `n` breakpoints has `n+1` answers, not `n`: before the
    first, between each pair, and *past the last*.  Without that final leaf
    the closing ramp's straight line simply continues, so an envelope
    ending at 1.0 reads 2.2 a few beats later — and every engine agrees on
    it, because they all run the same wrong tree.
    """
    got = render(_program(CURVE, "toFloat n * 4.0"), 12, 1)
    assert all(v == pytest.approx(1.0) for v in got[4:]), got


def test_it_holds_the_first_value_before_the_envelope_starts():
    got = render(_program(CURVE, "toFloat n - 20.0"), 6, 1)
    assert all(v == pytest.approx(0.2) for v in got), got


# ── The engines agree, which is necessary and not sufficient ────────────────


def test_the_block_engine_renders_what_the_oracle_does():
    source = _program(CURVE)
    assert run(extract(source, rate=1), 22) == render(source, 22, 1)


@needs_clang
def test_the_generated_code_renders_what_the_oracle_does():
    source = _program(CURVE)
    graph = extract(source, rate=1)
    with tempfile.TemporaryDirectory() as directory:
        native = run_native(graph, directory, 22, block=4)
    assert native == render(source, 22, 1)


# ── The shape of the tree ───────────────────────────────────────────────────


def _depth(node) -> int:
    if type(node).__name__ == "Case":
        return 1 + max(_depth(b) for _t, _n, b in node.alts)
    kids = [getattr(node, a) for a in ("body", "value", "scrut")
            if hasattr(node, a)]
    kids += list(getattr(node, "args", ()))
    kids = [k for k in kids if hasattr(k, "__dataclass_fields__")]
    return max((_depth(k) for k in kids), default=0)


@pytest.mark.parametrize("n", [2, 4, 8, 16, 32, 64])
def test_the_search_is_binary_rather_than_a_chain(n):
    """`ceil(log2(n+1))` comparisons on the path, not `n`.

    This runs per sample, so the difference between a 64-point envelope
    costing 7 comparisons and costing 64 is the difference between an
    envelope being usable in a synth and being a thing you budget for.
    """
    points = [(float(i), i % 2 == 1, 0.1 + 0.01 * i) for i in range(n)]
    graph = extract(_program(points), rate=8)
    depth = _depth(graph.funcs["sound/map#0/step"].body)
    assert depth == math.ceil(math.log2(n + 1)), f"{n} points gave {depth}"


def test_a_ramp_leaf_is_one_multiply_and_one_add():
    """`y₀ + (y₁-y₀)(x-x₀)/(x₁-x₀)` has one variable in it, so the rest
    folds.  A leaf that recomputed the slope per sample would be four more
    operations inside the hot loop for a number that cannot change."""
    graph = extract(_program([(0.0, False, 0.0), (4.0, True, 1.0)]), rate=8)
    body = repr(graph.funcs["sound/map#0/step"].body)
    assert body.count("prim_div_float") == 0, "a division survived the fold"
    assert body.count("__Num_Float_*__") <= 1, body


# ── The interpreted half is untouched ───────────────────────────────────────


def test_an_envelope_still_works_where_there_is_no_fragment_at_all():
    """The canvas and a music program run the same `on`, and neither is
    subject to the audio fragment.  The rewrite must not have made the
    readable definition wrong on the way past."""
    n = 20
    got = render(_program(CURVE, "toFloat n * 0.7"), n, 1)
    want = [value_on(CURVE, i * 0.7) for i in range(n)]
    assert got == pytest.approx(want, abs=1e-12)
