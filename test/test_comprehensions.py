"""Comprehension guards and multi-clause `for` — `errata.md` D6, roadmap 2.1.

Fig. 2.2's clause grammar is `C ::= p ∈ e | e | C,D`, and `{e | C}` is
defined as `for (C) {e}`.  Gestate had only the binding clause, and only
syntactically: see `test_a_second_generator_binds` for the miscompile that
turned up while wiring this, which is the reason the multi-generator tests
below are worth having at all.

The guard clause `| e` is the half that needed `errata.md` D5 settled
first, because "which boolean is a guard" *is* the boolean question.  The
answer is neither and both: a guard is whatever `Guard` has an instance
for, so `Prop` goes in unchanged and `Bool` goes in by `case`.  That is
what lets the desugaring live in the parser, which it must, since types do
not exist until long after.
"""

from __future__ import annotations

import re

import pytest

from gestate.desugar import DesugarError
from gestate.pipeline import evaluate

#: An element sits immediately after a cons cell: an integer, or a tuple.
#: The *spine* between cells is often still an unforced union thunk, which
#: is why these tests read the elements out rather than compare the printed
#: result — a set built by comprehension and the same set written literally
#: are equal but do not print alike.
_ELEM = re.compile(r"Pack\{1,2\} (\([^()]*\)|-?\d+)")


def _elems(source: str) -> list[str]:
    """The resulting set's elements, in order."""
    return _ELEM.findall(evaluate(source))


def _cells(source: str) -> int:
    """How many elements the resulting set has."""
    return evaluate(source).count("Pack{1,2}")


# ── `{e | C}` is `for (C) {e}` ───────────────────────────────────────────────


def test_a_comprehension_with_one_generator():
    assert _cells("main : {Int}\nmain = {x | x in {1,2,3}}") == 3


def test_a_comprehension_is_a_for():
    # Same set, both spellings — the comprehension is sugar and nothing more.
    comp = evaluate("main : {Int}\nmain = {x | x in {1,2,3}}")
    loop = evaluate("main : {Int}\nmain = for (x in {1,2,3}) {x}")
    assert comp == loop


def test_the_head_may_be_any_expression():
    assert _elems("main : {Int}\nmain = {x + 10 | x in {1,2}}") == ["11", "12"]


def test_a_set_literal_still_parses():
    # `{a, b}` must not be read as a comprehension: `|` is what marks one.
    assert _cells("main : {Int}\nmain = {1, 2}") == 2


# ── Multiple generators ──────────────────────────────────────────────────────


def test_a_second_generator_binds():
    """The regression this stage uncovered.

    `desugar_expr` read `bindings[0]` and dropped every later clause, so
    `for (x in a, y in b) e` compiled to `for (x in a) e` — with `y` free.
    The form is documented in `spec/syntax.md`, and nothing exercised it.
    """
    assert _cells("main : {(Int,Int)}\n"
                  "main = for (x in {1,2}, y in {3,4}) {(x,y)}") == 4


def test_a_comprehension_with_two_generators_is_the_product():
    assert _cells("main : {(Int,Int)}\n"
                  "main = {(x,y) | x in {1,2}, y in {3,4}}") == 4


def test_generators_scope_left_to_right():
    # The second clause may mention the first's binder: `for (C,D)` nests as
    # `for (C) for (D)`, so `x` is in scope in `D`.
    assert _elems("main : {(Int,Int)}\n"
                  "main = {(x,y) | x in {1,2}, y in {x}}") == ["(1, 1)", "(2, 2)"]


# ── Patterns in a clause ─────────────────────────────────────────────────────


def test_a_tuple_pattern_destructures_the_element():
    assert _elems("main : {Int}\nmain = {x | (x,y) in {(1,2),(3,4)}}") == ["1", "3"]


def test_a_refutable_pattern_is_rejected():
    # Fig. 2.2 gives a failed match the value ⊥, and ⊥ is type-directed, so
    # the desugarer has nothing to build.  Rejected rather than compiled
    # into a runtime failure.
    with pytest.raises(DesugarError):
        evaluate("main : {Int}\nmain = {x | Just x in {1,2}}")


# ── The guard clause ─────────────────────────────────────────────────────────


def test_a_bool_guard_filters():
    assert _elems("main : {Int}\nmain = {x | x in {1,2,3}, x == 2}") == ["2"]


def test_a_prop_guard_filters():
    # No coercion written: `Guard Prop` is the identity instance.
    assert _cells("main : {Int}\nmain = for (x in {1,2,3}, {()}) {x}") == 3
    assert _cells("main : {Int}\nmain = for (x in {1,2,3}, ({} : Prop)) {x}") == 0


def test_a_guard_may_stand_alone():
    # `for (e) f` with no generator at all — fig. 2.2's one-sided
    # conditional, which is the whole reason a guard is a `for` clause.
    assert _cells("main : {Int}\nmain = for (1 == 1) {5}") == 1
    assert _cells("main : {Int}\nmain = for (1 == 2) {5}") == 0


def test_several_guards_conjoin():
    assert _elems("main : {Int}\n"
                  "main = {x | x in {1,2,3,4}, x > 1, x < 4}") == ["2", "3"]


def test_a_guard_may_mention_earlier_binders():
    assert _elems("main : {(Int,Int)}\n"
                  "main = {(x,y) | x in {1,2}, y in {1,2}, x == y}") == [
        "(1, 1)", "(2, 2)"]


def test_the_generated_binders_do_not_capture():
    # Two fresh names are generated: `_guardN` for a guard clause (in the
    # parser) and `_mN_elem` for a pattern clause (in the desugarer).  Were
    # either to collide with a name the body uses, the body would read the
    # generated binding instead of its own.
    assert _elems("main : {Int}\n"
                  "main = {_guard1 | _guard1 in {1,2,3}, _guard1 == 2}") == ["2"]
    assert _elems("main : {Int}\n"
                  "main = {_m1_elem | (_m1_elem, y) in {(1,2),(3,4)}}") == ["1", "3"]


# ── The point of the exercise ────────────────────────────────────────────────


CLOSURE = """closure : Box (Set (Cyclic 8, Cyclic 8)) -> Set (Cyclic 8, Cyclic 8)
closure be = unbox e = be in fix Box (r => e \\/ {(x, w) | (x, y) in r, (z, w) in e, y == z})

main : Set (Cyclic 8, Cyclic 8)
main = closure (Box {%s})
"""


def test_transitive_closure_reads_as_datalog():
    """`test_relations.py`'s query, without the helper supercombinator.

    That version needs a two-argument `compose` returning `{…}` or `{}`,
    because there was no way to write a join and a filter inline.  This is
    the same query and the same answers, in one line of comprehension —
    which is what roadmap 2.1 was for.
    """
    assert evaluate(CLOSURE % "(0, 1), (1, 2)") == (
        "Pack{1,2} (0, 1) Pack{1,2} (0, 2) Pack{1,2} (1, 2) Pack{0,0}")


def test_transitive_closure_of_a_longer_path():
    assert evaluate(CLOSURE % "(0, 1), (1, 2), (2, 3)").count("Pack{1,2}") == 6


def test_transitive_closure_of_a_cycle_is_complete():
    assert evaluate(CLOSURE % "(0, 1), (1, 2), (2, 0)").count("Pack{1,2}") == 9


def test_transitive_closure_of_a_disconnected_graph():
    assert evaluate(CLOSURE % "(0, 1), (2, 3)").count("Pack{1,2}") == 2


# ── Guards inside a `fix` (`errata.md` D8) ───────────────────────────────────
#
# A guard calls the `Guard` class method, so a guard under a `fix` makes ϕ/δ
# differentiate a *dictionary method* — which it could not do.  δ emitted the
# discrete `()` and applied it; `UNIT` is `ENum(0)` and `Unwind` on a number
# ignores the spine, so the program died later as `CaseJump on non-constructor`
# with nothing pointing at the cause.  Three things fixed it: resolving
# `πᵢ dict` to the method's own name, letting instance methods be
# transformed like the ordinary code they are, and giving a saturated
# primitive the zero change at its result type rather than a unit to apply.

_FIX = ("f : Box (Set (Cyclic 4)) -> Set (Cyclic 4)\n"
        "f (Box e) = fix r => e \\/ (%s)\n\n"
        "main : Set (Cyclic 4)\nmain = f (Box {0})\n")


def test_a_guard_may_appear_under_a_fix():
    assert _elems(_FIX % "{x | x in r, x < 3}") == ["0"]


def test_a_guard_under_a_fix_may_compare_against_a_constant():
    # The shape that crashed: one operand is a literal, so its change is a
    # zero and δ met the derivative of `prim_eq_int`.
    assert _elems(_FIX % "{x | x in r, x == 0}") == ["0"]


def test_a_constant_guard_under_a_fix():
    assert _elems(_FIX % "for (x in r) (for (u in guard True) {x + 1})") == [
        "0", "1", "2", "3"]


def test_the_closure_query_still_converges():
    # The guard here compares two generator variables, which is the case
    # that always worked — kept so a regression in either path is visible.
    assert evaluate(CLOSURE % "(0, 1), (1, 2)") == (
        "Pack{1,2} (0, 1) Pack{1,2} (0, 2) Pack{1,2} (1, 2) Pack{0,0}")
