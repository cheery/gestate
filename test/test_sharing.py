"""§I.7's sharing requirement — `fixme.md` F42.

`spec/data.md` §I.7 says the ϕ/δ correctness proof is *inherited*, on one
assumption it singles out as needing scrutiny: I.4.1's rule for `for`,

    δ(for (x ∈ e) f) =  (for (x ∈ δe)      let dx = ⊥ in ϕf)
                      ∨ (for (x ∈ ϕe ∪ δe) let dx = ⊥ in δf)

mentions `ϕe` and `δe` twice each, and the thesis assumes they are the
*same code, referentially* — computed once, used twice.  Codegen has to
share them.  Inline them instead and every result is still correct, so
nothing fails and no example test notices: the program merely recomputes
its own input on every iteration and **silently degrades to naïve
evaluation while still being called seminaïve**.

That is why this needs a test of its own rather than an example.

**§I.7 proposes the wrong test.**  It suggests measuring `path` for Θ(n²)
rather than Θ(n³) work.  Measured here with the sharing deliberately
removed, the step counts are *indistinguishable* — 8055 against 8227 at
n=4, and the same 3.40/3.69 growth ratios — because a `for`'s source
expression is almost always a **variable**: `for (x ∈ r)` over a fixpoint
variable, `for (q ∈ e)` over a box-bound one.  Duplicating a variable
reference costs nothing, so the asymptotic difference §I.7 warns about only
appears for `for (x ∈ <computed expression>)`, which no query in the
literature writes.

So the structural tests below are the ones that guard the property, and
they were checked by breaking the sharing on purpose and confirming they
fail.  The asymptotic test is kept for what it *does* establish — that the
query is quadratic — and is labelled accordingly rather than as a guard on
sharing it cannot provide.
"""

from __future__ import annotations

from gestate.expr import EFor, EGlobal, ESet, EVar, subexprs
from gestate.gmachine import step
from gestate.pipeline import compile
from gestate.seminaive import SeminaiveCtx, delta
from gestate.types import TApp, TCon


def _walk(e):
    yield e
    for child in subexprs(e):
        yield from _walk(child)


def _steps(source: str) -> int:
    s = compile(source)
    n = 0
    while not s.isFinal:
        step(s)
        n += 1
    return n


# ── Structural: ϕe and δe are computed once ──────────────────────────────────


def _delta_of_a_for():
    """δ of `for (x ∈ src) {x}`, with `src` a marker global."""
    set_ty = TApp(TCon("Set"), TCon("Int"))
    node = EFor("x", EGlobal("src"), ESet([EVar("x")], set_ty),
                set_ty, TCon("Int"))
    return delta(node, SeminaiveCtx())


def test_phi_of_the_source_is_computed_once():
    out = _delta_of_a_for()
    names = [n.name for n in _walk(out) if isinstance(n, EGlobal)]
    assert names.count("src_phi") == 1, (
        "ϕe is inlined rather than shared — the loop recomputes its own "
        f"input, which is naïve evaluation wearing seminaïve's name: {names}")


def test_delta_of_the_source_is_computed_once():
    out = _delta_of_a_for()
    names = [n.name for n in _walk(out) if isinstance(n, EGlobal)]
    assert names.count("src_delta") == 1, names


def test_the_shared_bindings_are_the_ones_the_loops_use():
    """`δe` is used twice — once alone, once inside `ϕe ∪ δe`."""
    out = _delta_of_a_for()
    used = [n.name for n in _walk(out) if isinstance(n, EVar)]
    assert used.count("_pe") == 1
    assert used.count("_de") == 2


# ── Asymptotic: the end-to-end evidence §I.7 asks for ────────────────────────


_REACH = ("reach : Box (Set (Cyclic %d)) -> Set (Cyclic %d)\n"
          "reach (Box s) = fix r => s \\/ {x + 1 | x in r, x < %d}\n\n"
          "main : Set (Cyclic %d)\nmain = reach (Box {0})\n")


def test_work_grows_quadratically_not_cubically():
    """The query is quadratic — §I.7's asymptotic claim, directly.

    This does **not** guard the sharing above; see the module docstring for
    the measurement showing it cannot.  It guards the claim seminaïve
    evaluation is *for*: doubling the problem costs ~3.4–3.7× here, against
    4× for quadratic and 8× for cubic, so the bound is loose enough to be
    stable and tight enough to catch a real regression in the transform.
    """
    counts = [_steps(_REACH % (n, n, n - 1, n)) for n in (4, 8, 16)]
    ratios = [b / a for a, b in zip(counts, counts[1:])]
    assert all(r < 5.0 for r in ratios), (
        f"work is growing faster than quadratically: {counts}, "
        f"ratios {[round(r, 2) for r in ratios]} — §I.7's sharing has "
        f"probably been lost somewhere after ϕ/δ")


def test_the_query_is_actually_doing_the_work():
    """Guard the test above: a query optimised into nothing proves nothing."""
    counts = [_steps(_REACH % (n, n, n - 1, n)) for n in (4, 16)]
    assert counts[0] > 1000, counts
    assert counts[1] > counts[0] * 2, counts
