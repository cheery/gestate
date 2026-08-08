"""Tests for class contexts on user supercombinators.

``f : (Show a) => a -> Int`` gives ``f`` one dictionary parameter per
constraint, ahead of its own parameters; every call site supplies them.
Inside the body those parameters discharge the constraints, so a
constrained SC can call class methods, other constrained SCs, and itself.
"""

from __future__ import annotations

import pytest

from gestate.declarations import classify
from gestate.elaborate import ElaborateError
from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.types import TCon, TFun


SUM = (
    "class Sum a where\n  total : a -> Int\n\n"
    "instance Sum Int where\n  total x = x\n\n"
)

LISTS = SUM + (
    "instance (Sum a) => Sum (List a) where\n"
    "  total xs = case xs of\n"
    "    Nil -> 0\n"
    "    Cons h t -> total h + total t\n\n"
)

SIZE = (
    "class Size a where\n  size : a -> Int\n\n"
    "instance Size Int where\n  size x = 1\n\n"
)


# ── Signatures ───────────────────────────────────────────────────────────────


def _sc(source: str, name: str):
    return next(sc for sc in classify(parse(source)).scs if sc.name == name)


def test_context_is_split_from_the_type():
    sc = _sc("f : (Sum a) => a -> Int\nf x = 1\n", "f")
    assert [p.class_name for p in sc.sig_constraints] == ["Sum"]
    # The constraint and the argument mention the same type variable.
    assert sc.sig_constraints[0].type_ == sc.sig_type.arg


def test_several_constraints_keep_their_order():
    sc = _sc("f : (Sum a, Size a) => a -> Int\nf x = 1\n", "f")
    assert [p.class_name for p in sc.sig_constraints] == ["Sum", "Size"]


def test_context_without_parentheses():
    sc = _sc("f : Sum a => a -> Int\nf x = 1\n", "f")
    assert [p.class_name for p in sc.sig_constraints] == ["Sum"]


def test_signature_type_variables_are_variables_now():
    # `id2 : a -> a` used to desugar `a` to a type *constructor*, which
    # then failed kind checking.
    sc = _sc("id2 : a -> a\nid2 x = x\n", "id2")
    assert sc.sig_type.arg == sc.sig_type.ret
    assert not isinstance(sc.sig_type.arg, TCon)


def test_a_polymorphic_signature_runs():
    assert evaluate("id2 : a -> a\nid2 x = x\n\nmain : Int\nmain = id2 5\n") == "5"


# ── Using the dictionary parameter ───────────────────────────────────────────


def test_body_may_call_the_class_method():
    src = SUM + (
        "twice2 : (Sum a) => a -> Int\n"
        "twice2 x = total x + total x\n\n"
        "main : Int\nmain = twice2 7\n"
    )
    assert evaluate(src) == "14"


def test_two_constraints_are_both_available():
    src = SUM + SIZE + (
        "both : (Sum a, Size a) => a -> Int\n"
        "both x = total x + size x\n\n"
        "main : Int\nmain = both 5\n"
    )
    assert evaluate(src) == "6"


def test_constraints_in_the_other_order():
    src = SUM + SIZE + (
        "both : (Size a, Sum a) => a -> Int\n"
        "both x = total x + size x\n\n"
        "main : Int\nmain = both 5\n"
    )
    assert evaluate(src) == "6"


def test_a_constrained_supercombinator_may_recurse():
    src = SUM + (
        "sumList : (Sum a) => List a -> Int\n"
        "sumList xs = case xs of\n"
        "  Nil -> 0\n"
        "  Cons h t -> total h + sumList t\n\n"
        "main : Int\nmain = sumList (Cons 1 (Cons 2 (Cons 3 Nil)))\n"
    )
    assert evaluate(src) == "6"


def test_a_constrained_supercombinator_may_call_another():
    src = LISTS + (
        "twice2 : (Sum a) => a -> Int\n"
        "twice2 x = total x + total x\n\n"
        "quad : (Sum a) => a -> Int\n"
        "quad x = twice2 x + twice2 x\n\n"
        "main : Int\nmain = quad (Cons 5 Nil)\n"
    )
    assert evaluate(src) == "20"


# ── Call sites ───────────────────────────────────────────────────────────────


def test_one_supercombinator_used_at_two_types():
    src = LISTS + (
        "twice2 : (Sum a) => a -> Int\n"
        "twice2 x = total x + total x\n\n"
        "main : Int\nmain = twice2 7 + twice2 (Cons 1 (Cons 2 Nil))\n"
    )
    assert evaluate(src) == "20"


def test_call_site_at_a_type_needing_a_context_instance():
    src = LISTS + (
        "twice2 : (Sum a) => a -> Int\n"
        "twice2 x = total x + total x\n\n"
        "main : Int\nmain = twice2 (Cons (Cons 1 Nil) (Cons (Cons 2 Nil) Nil))\n"
    )
    assert evaluate(src) == "6"


def test_missing_instance_is_reported():
    from gestate.constraint import ConstraintError
    src = SUM + (
        "twice2 : (Sum a) => a -> Int\n"
        "twice2 x = total x + total x\n\n"
        "main : Int\nmain = twice2 (Cons 1 Nil)\n"   # no Sum (List a) instance
    )
    with pytest.raises(ConstraintError, match="No instance"):
        evaluate(src)


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_may_not_have_a_context():
    with pytest.raises(ElaborateError, match="'main' cannot have a class context"):
        evaluate(SUM + "main : (Sum a) => a\nmain = 5\n")


def test_main_with_an_inferred_constraint_still_works():
    # `main = 5` infers `Num a`; that resolves to an instance rather than
    # becoming a parameter.
    assert evaluate("main : Int\nmain = 5\n") == "5"
