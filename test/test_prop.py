"""`Prop`, the monotone boolean — `errata.md` D5, roadmap 1.1.

Gestate has two booleans, on purpose.  `Bool` is the discrete one: a
two-constructor ADT, what `==` returns, what `case` analyses.  `Prop` is
Datafun's `bool = {1}` — `{}` is false, `{()}` is true, `\\/` is or, and
`for (u in p) e` is the one-sided conditional.  The second exists for one
reason the first cannot serve: a predicate returning `Prop` is *monotone*,
so its truth may grow as a fixpoint converges, which is what
`test_a_predicate_may_be_monotone_in_a_set` pins down.

`Prop` is a type *alias* for `{()}` and deliberately not a new constructor:
every property above is the set structure, so an opaque type would have to
re-derive ⊥, ∨, the change structure and the fixpoint, and would gain only
prettier output.

Three things had to be repaired before it could be written at all.  `()`
was a value but not a type, and not an instance head.  `Tuple0` had no
kind.  And `is_eqtype` answered `False` for it — bare `TCon`s never reached
the product case — so `{()}` was neither a semilattice nor a fixtype, which
is exactly backwards.  Fig. 2.1 puts `1` in all four subgrammars.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import compile, evaluate
from gestate.types import (
    TApp, TCon, is_eqtype, is_finite_eqtype, is_fixtype, is_semilattice,
    has_nontrivial_order, tuple_con,
)

UNIT = tuple_con(0)
PROP = TApp(TCon("Set"), UNIT)

#: `{}` — the empty set, and `Prop`'s false.  `Bool`'s `False` is a
#: constructor of its own and a different value entirely (`Pack{2,0}`),
#: which is the whole point: the two booleans do not unify.
FALSE = "Pack{0,0}"


def _true(source: str) -> bool:
    """Did `main : Prop` evaluate to `{()}` rather than `{}`?"""
    return evaluate(source) != FALSE


def _bool(expr: str) -> str:
    """A `Bool`-valued expression, through `show` — tags are not stable."""
    return evaluate(f"main : String\nmain = show ({expr})")


# ── The unit type is in all four subgrammars ─────────────────────────────────


def test_unit_is_an_eqtype():
    # `1` in fig. 2.1's eqtypes: one value, and it equals itself.
    assert is_eqtype(UNIT)
    assert is_finite_eqtype(UNIT)


def test_unit_is_a_semilattice_and_a_fixtype():
    assert is_semilattice(UNIT)
    assert is_fixtype(UNIT)


def test_unit_is_discretely_ordered():
    # One value, so the order *is* equality — which is why every function
    # out of `()` (and out of `Bool`) is trivially monotone.
    assert not has_nontrivial_order(UNIT)


def test_a_set_of_units_is_a_semilattice_and_a_fixtype():
    # The regression that mattered: `{()}` could be neither joined nor
    # fixed, because `is_eqtype(Tuple0)` was `False`.
    assert is_semilattice(PROP)
    assert is_fixtype(PROP)


# ── `()` in the surface ──────────────────────────────────────────────────────


def test_unit_is_a_type():
    assert evaluate("k : () -> Int\nk u = 3\nmain : Int\nmain = k ()") == "3"


def test_unit_has_equality():
    assert _bool("() == ()") == "True"
    assert _bool("() /= ()") == "False"


def test_unit_shows():
    assert evaluate('main : String\nmain = show ()') == "()"


# ── `Prop` as a boolean ──────────────────────────────────────────────────────


def test_the_alias_names_the_set_of_units():
    # An alias expands structurally, so `Prop` and `{()}` are one type and
    # a signature written either way accepts the other's value.
    assert _true("p : Prop\np = {()}\nmain : {()}\nmain = p")


def test_false_is_the_empty_set():
    assert not _true("main : Prop\nmain = {}")


def test_join_is_disjunction():
    assert _true("main : Prop\nmain = {} \\/ {()}")
    assert not _true("main : Prop\nmain = ({} : Prop) \\/ {}")


def test_true_is_idempotent():
    # A set, so `true \\/ true` is one `()` and not two.
    assert evaluate("main : Prop\nmain = {()} \\/ {()}").count("Pack{1,2}") == 1


def test_for_is_the_one_sided_conditional():
    # `for (u in p) e` is `e if p else ⊥` — Datafun's guard, thesis §2.2.
    guard = "main : Set Int\nmain = for (u in ({0} : Prop)) {1}"
    assert evaluate(guard.replace("{0}", "{()}")).count("Pack{1,2}") == 1
    assert evaluate(guard.replace("{0}", "{}")) == FALSE


def test_fix_at_prop_converges():
    # `{()}` is a fixtype: the chain `{} ⩽ {()}` cannot ascend further.
    assert _true("main : Prop\nmain = fix Box (r => r \\/ {()})")


# ── The reason for having two booleans ───────────────────────────────────────


_MEMBER = (
    "member : Box Int -> {Int} ~> Prop\n"
    "member n s = for (x in s) (unbox m = n in case x == m of\n"
    "    True -> {()}\n"
    "    False -> {})\n"
)


def test_a_predicate_may_be_monotone_in_a_set():
    """The one thing `Bool` cannot do.

    `member` takes its set argument at the *monotone* arrow `~>`, so it may
    be applied to a fixpoint variable and its truth grows with the set.  The
    same function returning `Bool` would need the set discretely, and would
    be unusable under `fix`.
    """
    assert _true(_MEMBER + "main : Prop\nmain = member (Box 2) {1,2,3}")
    assert not _true(_MEMBER + "main : Prop\nmain = member (Box 9) {1,2,3}")


def test_bool_is_still_the_discrete_boolean():
    # Unchanged by any of the above: `==` returns `Bool` and `case`
    # analyses it.
    assert _bool("case 1 == 1 of\n"
                 "    True -> False\n"
                 "    False -> True") == "False"


def test_the_two_booleans_do_not_unify():
    # The tax option (b) accepts, stated as a test: `True` is not a `Prop`.
    # `errata.md` D5 records where the coercion is to go instead.
    with pytest.raises(Exception):
        compile("main : Prop\nmain = True")
