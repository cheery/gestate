"""⊥-propagation and change minimization — `spec/errata.md` D3 and D4.

ϕ/δ on its own buys "roughly 20%" (thesis §4.2.3): the derivative of a term
that cannot change is still built and still iterated over.  D3 deletes that
work; D4 stops a rediscovered element from re-deriving everything reachable
from it.  Both are transformations of *generated* code, so the tests come
in two kinds — the rewrite fires where it should, and the program still
computes the same answer.
"""

from __future__ import annotations

from gestate.bottoms import is_bottom, propagate
from gestate.expr import (
    EAp, ECon, EFor, EGlobal, EJoin, ELambda, ELet, ENum, ESet, EVar,
)
from gestate.gmachine import step
from gestate.pipeline import compile, evaluate
from gestate.seminaive import make_semifix_helpers
from gestate.types import TApp, TCon

SET_INT = TApp(TCon("Set"), TCon("Int"))
BOT = EGlobal("bottom_Set_Int")


# ── Recognising ⊥ ────────────────────────────────────────────────────────────


def test_a_generated_bottom_is_bottom():
    assert is_bottom(BOT)
    assert is_bottom(EGlobal("bottom_Set_Cyclic_4"))


def test_an_empty_set_literal_is_bottom():
    assert is_bottom(ESet([]))
    assert not is_bottom(ESet([ENum(1)]))


def test_an_ordinary_global_is_not_bottom():
    assert not is_bottom(EGlobal("union_Set_Int"))
    assert not is_bottom(EVar("x"))


# ── The rewrites (thesis fig. 4.1) ───────────────────────────────────────────


def test_join_with_bottom_collapses():
    e = EVar("e")
    assert propagate(EJoin(BOT, e)) == e
    assert propagate(EJoin(e, BOT)) == e


def test_join_of_two_bottoms_is_bottom():
    assert is_bottom(propagate(EJoin(BOT, BOT)))


def test_a_join_of_two_real_terms_is_left_alone():
    j = EJoin(EVar("a"), EVar("b"))
    assert propagate(j) == j


def test_a_loop_with_a_bottom_body_becomes_bottom():
    """The rule that matters: a loop whose length grows with the input
    becomes constant work."""
    loop = EFor("x", EVar("s"), BOT, SET_INT, TCon("Int"))
    assert propagate(loop) == BOT


def test_a_loop_over_bottom_becomes_bottom():
    loop = EFor("x", BOT, EVar("body"), SET_INT, TCon("Int"))
    assert propagate(loop) == BOT


def test_a_loop_over_an_empty_literal_becomes_bottom():
    loop = EFor("x", ESet([]), EVar("body"), SET_INT, TCon("Int"))
    assert propagate(loop) == BOT


def test_a_let_bound_bottom_is_substituted_inward():
    """This is the ⊥-*insertion* half: carrying a zero change to where the
    other rules can see it."""
    e = ELet(False, [("dx", BOT)],
             EFor("y", EVar("s"), EVar("dx"), SET_INT, TCon("Int")))
    assert propagate(e) == BOT


def test_a_let_whose_body_is_bottom_collapses():
    assert propagate(ELet(False, [("x", EVar("e"))], BOT)) == BOT


def test_a_recursive_let_is_left_alone():
    """`letrec` binders may be forced by each other; the rule is unsound there."""
    e = ELet(True, [("x", BOT)], EVar("x"))
    assert propagate(e) == e


def test_propagation_reaches_nested_positions():
    inner = EFor("x", EVar("s"), BOT, SET_INT, TCon("Int"))
    assert propagate(EJoin(EVar("a"), inner)) == EVar("a")


def test_a_loop_body_that_is_not_bottom_survives():
    loop = EFor("x", EVar("s"), EVar("x"), SET_INT, TCon("Int"))
    assert propagate(loop) == loop


# ── Change minimization ──────────────────────────────────────────────────────


def test_the_loop_minimizes_the_next_delta():
    """`dx_{i+1} = (f' xi dxi) \\ x_{i+1}` — thesis §4.3."""
    helpers = dict((name, lam)
                   for name, _arity, lam in make_semifix_helpers(0, 1, 3, 2))
    body = helpers["semifixL_Set_Int"].body
    recursive = body.alts[1].body
    assert isinstance(recursive, ELet)
    assert dict(recursive.defs)["x'"] == EAp(
        EAp(EGlobal("join_Set_Int"), EVar("x")), EVar("dx"))
    assert recursive.body.arg == EAp(
        EAp(EGlobal("diff_Set_Int"),
            EAp(EAp(EVar("f'"), EVar("x")), EVar("dx"))),
        EVar("x'"))


def test_diff_is_generated_per_semilattice():
    from gestate.declarations import classify
    from gestate.helpers import generate_all_helpers
    from gestate.syntax import parse

    program = classify(parse("main : Int\nmain = 1\n"))
    names = {n for n, _a, _l in generate_all_helpers([SET_INT], program.cons)}
    assert "diff_Set_Int" in names


# ── And the pipeline runs the pass ───────────────────────────────────────────

#: A query whose δ collapses: `for (x in r) {x + 1}` cannot change
#: independently of its own recomputation, so ϕ marks it ⊥ and pass 1
#: deletes the loop that would iterate over it.
PATH = ("path : Box (Set (Cyclic 8)) -> Set (Cyclic 8)\n"
        "path bs = unbox s = bs in fix Box (r => s \\/ (for (x in r) {x + 1}))\n"
        "\n"
        "main : Set (Cyclic 8)\nmain = path (Box {1})\n")


def _steps(source: str) -> int:
    s = compile(source)
    n = 0
    while not s.isFinal:
        step(s)
        n += 1
    return n


def test_the_compiled_query_pays_the_propagated_price():
    """`propagate` above is a function; this asks whether it is *called*.

    Every rewrite in the section above is tested on a hand-built term,
    and `pipeline.py` wiring the pass into the compilation was held by
    nothing: taking `propagate_bottoms(scs)` out left all 429 tests of
    the batch's set green, though the pass demonstrably fires — a probe
    raising when it changed anything took 52 of them down
    (`card:ungated-fixes.md`, batch 12, 2026-09-03).  `fixme.md` F10.

    Measured 2026-09-03: **8,966** G-machine steps with the pass,
    **12,130** without — the 26% the thesis §4.2.3 says ϕ/δ alone does
    not buy.  The bound is a number and will drift as the compiler
    changes; re-measure it rather than raise it blindly, because a bound
    raised past 12,130 is this gate switched off.
    """
    assert _steps(PATH) < 10_500


# ── The answers do not change ────────────────────────────────────────────────


def test_a_fixed_point_still_converges_to_the_same_set():
    assert evaluate("""reach : Box (Set (Cyclic 4)) -> Set (Cyclic 4)
reach bs = unbox s = bs in fix Box (r => s \\/ (for (x in r) {x + 1}))

main : Set (Cyclic 4)
main = reach (Box {1})
""").count("Pack{1,2}") == 4


def test_a_query_whose_step_contributes_nothing_still_terminates():
    assert evaluate("""q : Box (Set (Cyclic 4)) -> Set (Cyclic 4)
q bs = unbox s = bs in fix Box (r => s \\/ (for (x in r) {}))

main : Set (Cyclic 4)
main = q (Box {1, 2})
""").count("Pack{1,2}") == 2
