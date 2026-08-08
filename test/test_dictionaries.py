"""Tests for dictionary-passing elaboration (implementation_order.md §18).

Every instance becomes a tuple of its method closures, built by a
supercombinator whose parameters are the dictionaries of its context, so
one generic ``Sum (List a)`` instance serves lists of every depth.
"""

from __future__ import annotations

import pytest

from gestate.constraint import match_head
from gestate.declarations import classify
from gestate.elaborate import elaborate
from gestate.expr import EAp, EGlobal, EProj, ETuple
from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.types import TApp, TCon, TVar


SUM = (
    "class Sum a where\n  total : a -> Int\n\n"
    "instance Sum Int where\n  total x = x\n\n"
)

RECURSIVE = SUM + (
    "instance (Sum a) => Sum (List a) where\n"
    "  total xs = case xs of\n"
    "    Nil -> 0\n"
    "    Cons h t -> total h + total t\n\n"
)


# ── Running ──────────────────────────────────────────────────────────────────


def test_instance_without_context():
    assert evaluate(SUM + "main : Int\nmain = total 7\n") == "7"


def test_context_dictionary_is_passed():
    src = RECURSIVE + "main : Int\nmain = total (Cons 1 (Cons 2 (Cons 3 Nil)))\n"
    assert evaluate(src) == "6"


def test_empty_structure():
    assert evaluate(RECURSIVE + "main : Int\nmain = total Nil\n") == "0"


def test_nested_structures_reuse_one_instance():
    # `Sum (List (List Int))` builds `dictList (dictList dictInt)` — the
    # List instance is compiled once, not specialised per element type.
    src = RECURSIVE + (
        "main : Int\n"
        "main = total (Cons (Cons 1 (Cons 2 Nil)) (Cons (Cons 3 Nil) Nil))\n"
    )
    assert evaluate(src) == "6"


def test_three_levels_deep():
    src = RECURSIVE + "main : Int\nmain = total (Cons (Cons (Cons 7 Nil) Nil) Nil)\n"
    assert evaluate(src) == "7"


def test_two_context_predicates():
    src = (
        "class Sum a where\n  total : a -> Int\n\n"
        "class Size a where\n  size : a -> Int\n\n"
        "instance Sum Int where\n  total x = x\n\n"
        "instance Size Int where\n  size x = 1\n\n"
        "Wrap a := MkWrap a\n\n"
        "instance (Sum a, Size a) => Sum (Wrap a) where\n"
        "  total w = case w of\n    MkWrap x -> total x + size x\n\n"
        "main : Int\nmain = total (MkWrap 5)\n"
    )
    assert evaluate(src) == "6"


def test_method_slots_are_indexed_by_class_order():
    src = (
        "class Two a where\n  first2 : a -> Int\n  second2 : a -> Int\n\n"
        "instance Two Int where\n  first2 x = x\n  second2 x = x + 100\n\n"
        "main : Int\nmain = second2 5\n"
    )
    assert evaluate(src) == "105"


def test_literals_in_instance_bodies_default_to_int():
    src = SUM.replace("total x = x", "total x = 42") + "main : Int\nmain = total 1\n"
    assert evaluate(src) == "42"


# ── Per-occurrence routing ───────────────────────────────────────────────────


def test_one_method_at_two_types_in_one_supercombinator():
    # Each occurrence carries its own predicate, so the two calls get
    # different dictionaries — a by-name map could only hold one.
    src = RECURSIVE + "main : Int\nmain = total 7 + total (Cons 1 (Cons 2 Nil))\n"
    assert evaluate(src) == "10"


def test_recursive_call_and_context_call_differ():
    # In the List instance `total h` is the element's dictionary and
    # `total t` is this instance's own, rebuilt from the same parameter.
    scs = _elaborated(RECURSIVE + "main : Int\nmain = total (Cons 1 Nil)\n")
    body = str(scs["__Sum_List_a-2_total__"])
    assert "EVar(name='_d0')" in body                 # the element call
    assert "__dict_Sum_List_a-2__'), arg=EVar(name='_d0')" in body  # recursion


# ── Generated shape ──────────────────────────────────────────────────────────


def _elaborated(source: str) -> dict[str, object]:
    from gestate.constraint import solve_constraints
    from gestate.desugar import desugar_program
    from gestate.infer import infer_program
    from gestate.pipeline import _build_builtins

    program = classify(parse(source))
    scs = desugar_program(program)
    contexts = {sc.name: sc.sig_constraints for sc in program.scs}
    results, per_sc, givens = infer_program(scs, _build_builtins(), program.cons,
                                            program.classes, contexts)
    resolved = solve_constraints([p for sl in per_sc for p in sl],
                                 program.instances)
    out = elaborate(scs, per_sc, resolved, program, results, givens)
    return {name: lam for name, _arity, lam, _sig in out}


def test_dictionary_is_a_tuple_of_methods():
    scs = _elaborated(SUM + "main : Int\nmain = total 7\n")
    dictionary = scs["__dict_Sum_Int__"]
    assert dictionary.params == []
    assert dictionary.body == ETuple([EGlobal("__Sum_Int_total__")])


def test_context_dictionary_takes_a_parameter():
    scs = _elaborated(RECURSIVE + "main : Int\nmain = total (Cons 1 Nil)\n")
    dictionary = scs["__dict_Sum_List_a-2__"]
    assert dictionary.params == ["_d0"]
    assert dictionary.body == ETuple(
        [EAp(EGlobal("__Sum_List_a-2_total__"), _var("_d0"))])


def test_call_site_projects_out_of_the_dictionary():
    scs = _elaborated(SUM + "main : Int\nmain = total 7\n")
    call = scs["main"].body
    assert call.fn == EAp(EProj(0), EGlobal("__dict_Sum_Int__"))


def _var(name: str):
    from gestate.expr import EVar
    return EVar(name)


# ── Instance-head matching ───────────────────────────────────────────────────


def test_match_head_binds_a_variable_to_a_variable():
    # `Sum [a]` matched against `Sum [b]` must record a ↦ b so the
    # instance's context can be instantiated.
    bindings = match_head(TApp(TCon("List"), TVar(-2)),
                          TApp(TCon("List"), TVar(3)))
    assert bindings == {-2: TVar(3)}


def test_match_head_still_accepts_unresolved_metavariables():
    assert match_head(TCon("Int"), TVar(7)) == {}


def test_match_head_rejects_a_different_constructor():
    assert match_head(TApp(TCon("List"), TVar(-2)), TCon("Int")) is None
