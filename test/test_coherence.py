"""Tests for instance coherence — overlap, Paterson conditions, resolution.

Implements the checks from ``spec/typeclasses.md`` §4 (one instance per
``(class, type)`` pair), §5.1 (Paterson conditions) and §5.2 (depth cap).
"""

from __future__ import annotations

import pytest

from gestate.coherence import CoherenceError, check_paterson
from gestate.constraint import (
    RESOLUTION_DEPTH_CAP, ConstraintError, solve_predicate,
)
from gestate.declarations import InstanceInfo, classify
from gestate.elaborate import ElaborateError
from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.types import Predicate, TApp, TCon, TVar


SHOW = "class Show2 a where\n  show2 : a -> Int\n\n"


def _classify(source: str):
    return classify(parse(source))


def _instance(source: str, index: int = 0) -> InstanceInfo:
    declared = [i for i in _classify(source).instances if not i.builtin]
    return declared[index]


# ── Instance heads and contexts ──────────────────────────────────────────────


def test_parametric_instance_head():
    inst = _instance(SHOW + "instance Show2 (List a) where\n  show2 x = 1\n")
    assert str(inst) == "Show2 (List a)"


def test_instance_context_is_recorded():
    inst = _instance(
        SHOW + "instance (Show2 a) => Show2 (List a) where\n  show2 x = 1\n")
    assert str(inst) == "(Show2 a) => Show2 (List a)"
    # Head and context share the same type variable.
    assert inst.context[0].type_ == inst.head_type.arg


def test_unparenthesized_single_context():
    inst = _instance(
        SHOW + "instance Show2 a => Show2 (List a) where\n  show2 x = 1\n")
    assert str(inst) == "(Show2 a) => Show2 (List a)"


def test_multiple_context_predicates():
    src = (SHOW + "class Eq2 a where\n  eq2 : a -> Int\n\n"
           "instance (Show2 a, Eq2 a) => Show2 (List a) where\n  show2 x = 1\n")
    inst = _instance(src)
    assert [p.class_name for p in inst.context] == ["Show2", "Eq2"]


# ── Overlap ──────────────────────────────────────────────────────────────────


def test_duplicate_instances_overlap():
    src = (SHOW + "instance Show2 Int where\n  show2 x = x\n\n"
           "instance Show2 Int where\n  show2 x = 1\n")
    with pytest.raises(CoherenceError, match="Overlapping instances"):
        _classify(src)


def test_variable_head_overlaps_concrete_head():
    src = (SHOW + "instance Show2 (List a) where\n  show2 x = 1\n\n"
           "instance Show2 (List Int) where\n  show2 x = 2\n")
    with pytest.raises(CoherenceError, match="Overlapping instances"):
        _classify(src)


def test_contexts_do_not_excuse_overlap():
    src = (SHOW + "class Eq2 a where\n  eq2 : a -> Int\n\n"
           "instance (Show2 a) => Show2 (List a) where\n  show2 x = 1\n\n"
           "instance (Eq2 a) => Show2 (List a) where\n  show2 x = 2\n")
    with pytest.raises(CoherenceError, match="Overlapping instances"):
        _classify(src)


def test_distinct_heads_do_not_overlap():
    src = (SHOW + "instance Show2 (List a) where\n  show2 x = 1\n\n"
           "instance Show2 Int where\n  show2 x = 2\n")
    assert len([i for i in _classify(src).instances if not i.builtin]) == 2


def test_same_type_different_classes_do_not_overlap():
    src = (SHOW + "class Eq2 a where\n  eq2 : a -> Int\n\n"
           "instance Show2 Int where\n  show2 x = 1\n\n"
           "instance Eq2 Int where\n  eq2 x = 1\n")
    assert len([i for i in _classify(src).instances if not i.builtin]) == 2


def test_redefining_a_builtin_instance_overlaps():
    with pytest.raises(CoherenceError, match="built-in"):
        _classify("instance Eq Int where\n  x == y = x\n")


# ── Unknown classes ──────────────────────────────────────────────────────────


def test_instance_of_unknown_class():
    with pytest.raises(CoherenceError, match="unknown class"):
        _classify("instance Bogus Int where\n  show2 x = x\n")


def test_unknown_class_in_context():
    with pytest.raises(CoherenceError, match="Unknown class 'Bogus'"):
        _classify(SHOW +
                  "instance (Bogus a) => Show2 (List a) where\n  show2 x = 1\n")


# ── Paterson conditions ──────────────────────────────────────────────────────


def test_lawful_context_passes():
    inst = _instance(
        SHOW + "instance (Show2 a) => Show2 (List a) where\n  show2 x = 1\n")
    check_paterson(inst)  # does not raise


def test_paterson_1_context_larger_than_head():
    src = (SHOW + "instance (Show2 (List (List a))) => Show2 (List a) where\n"
           "  show2 x = 1\n")
    with pytest.raises(CoherenceError, match="Paterson condition 1"):
        _classify(src)


def test_paterson_2_context_variable_not_in_head():
    src = (SHOW + "class Eq2 a where\n  eq2 : a -> Int\n\n"
           "instance (Eq2 b) => Show2 (List a) where\n  show2 x = 1\n")
    with pytest.raises(CoherenceError, match="Paterson condition 2"):
        _classify(src)


def test_paterson_3_context_repeats_a_variable():
    src = (SHOW + "Pair a b := MkPair a b\n\n"
           "instance (Show2 (Pair a a)) => Show2 (Pair a Int) where\n"
           "  show2 x = 1\n")
    with pytest.raises(CoherenceError, match="Paterson condition 3"):
        _classify(src)


# ── Resolution with contexts ─────────────────────────────────────────────────


_WITH_CONTEXT = (
    SHOW +
    "instance Show2 Int where\n  show2 x = x\n\n"
    "instance (Show2 a) => Show2 (List a) where\n  show2 x = 1\n"
)


def test_context_is_solved_recursively():
    instances = _classify(_WITH_CONTEXT).instances
    pred = Predicate("Show2", TApp(TCon("List"), TCon("Int")))
    assert solve_predicate(pred, instances).context  # the List instance


def test_unsatisfiable_context_is_reported():
    instances = _classify(_WITH_CONTEXT).instances
    pred = Predicate("Show2", TApp(TCon("List"), TCon("Bool")))
    with pytest.raises(ConstraintError, match="required by the context"):
        solve_predicate(pred, instances)


def test_self_referential_instance_does_not_apply():
    # `C [a]` needs `C [a]`.  The Paterson conditions permit it (nothing
    # grows), so resolution has to stop it: an instance whose context
    # reproduces the goal cannot discharge that goal, and with no other
    # instance to try the predicate is simply unsolved.
    looping = InstanceInfo(
        class_name="C", head_type=TApp(TCon("List"), TVar(-1)), methods={},
        context=[Predicate("C", TApp(TCon("List"), TVar(-1)))],
    )
    check_paterson(looping)  # legal by Paterson
    pred = Predicate("C", TApp(TCon("List"), TCon("Int")))
    assert solve_predicate(pred, [looping]) is None


def test_a_base_case_wins_over_a_self_referential_instance():
    """Cutting the cycle lets a later instance claim the goal."""
    looping = InstanceInfo(
        class_name="C", head_type=TVar(-1), methods={},
        context=[Predicate("C", TVar(-1))],
    )
    base = InstanceInfo(class_name="C", head_type=TCon("Int"), methods={})
    assert solve_predicate(Predicate("C", TCon("Int")), [looping, base]) is base


def test_resolution_depth_cap_catches_a_growing_context():
    # `C [a]` needing `C [[a]]` never repeats a predicate, so cycle
    # detection cannot see it — the depth cap is the backstop.
    growing = InstanceInfo(
        class_name="C", head_type=TApp(TCon("List"), TVar(-1)), methods={},
        context=[Predicate("C", TApp(TCon("List"),
                                     TApp(TCon("List"), TVar(-1))))],
    )
    pred = Predicate("C", TApp(TCon("List"), TCon("Int")))
    with pytest.raises(ConstraintError,
                       match=f"exceeded depth {RESOLUTION_DEPTH_CAP}"):
        solve_predicate(pred, [growing])


# ── Elaboration ──────────────────────────────────────────────────────────────


def test_a_context_instance_runs():
    # See test_dictionaries.py for the dictionary-passing details.
    src = _WITH_CONTEXT + "\nmain : Int\nmain = show2 (Cons 1 Nil)\n"
    assert evaluate(src) == "1"


def test_context_free_instances_still_run():
    src = (SHOW + "instance Show2 Int where\n  show2 x = x\n\n"
           "main : Int\nmain = show2 7\n")
    assert evaluate(src) == "7"
