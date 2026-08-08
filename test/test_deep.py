"""Deeply nested programs compile, and quickly — `fixme.md` F66, F75, F78.

Two limits used to sit close together and both were hit by the same
program: a piece of music written as one `++` chain.

*F66* was a ceiling.  Every stage that walks an expression recurses, at
about six Python frames per level of source nesting, so CPython's default
limit of 1000 stopped compilation at roughly 165 nested applications —
about 170 notes.  `pipeline.compile` now runs on a thread with a stack
sized for real programs.

*F75* was a slope.  `Subst` was an association list, so `lookup` cost the
size of the substitution, and that size grew with the program; two growing
factors multiplied.  Compiling 512 notes took fifty seconds.

*F78* was the rest of that slope.  A persistent substitution has to copy on
every binding and forces the environment to be rebuilt whenever it grows.
Inference now runs against one destructive store — the union-find
formulation — which is sound here only because inference never backtracks.
Those tests state the properties that soundness rests on.

Sizes here are kept modest on purpose — the point is to be past the old
ceiling, not to benchmark.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import compile, evaluate
from gestate.types import Subst, TCon, TFun, TVar


# ── F66: the depth ceiling ───────────────────────────────────────────────────


def test_a_chain_far_past_the_old_recursion_ceiling_compiles():
    # ~165 was the old limit.  400 is comfortably past it and still quick.
    n = 400
    assert evaluate("main : Int\nmain = " + " + ".join("1" for _ in range(n))
                    + "\n") == str(n)


def test_a_deeply_nested_application_compiles():
    src = ("f : Int -> Int\nf x = x + 1\n\n"
           "main : Int\nmain = " + "f (" * 300 + "0" + ")" * 300 + "\n")
    assert evaluate(src) == "300"


def test_a_long_score_compiles():
    """The program that motivated the fix: a melody is one `++` chain."""
    from gestate.midi import perform

    n = 200                       # past the old ~170-note ceiling
    notes = " ++ ".join(f"'{60 + (i % 12)}" for i in range(n))
    bpm, events = perform(
        f"melody : [: Int :]\nmelody = {notes}\n\n"
        "score : [: Void :]\nscore = melody >>= prog 0\n\n"
        "bpm : Int\nbpm = 120\n")
    assert len(events) == n


def test_nesting_beyond_even_the_raised_limit_is_a_compiler_error():
    """Still finite, and still says something a reader can act on.

    A raised ceiling that turns runaway recursion into a segfault would be
    a worse failure mode than the one being fixed, so the limit stays a
    limit — it just reports itself (`fixme.md` F30's rule).
    """
    from gestate.pipeline import PipelineError, _deep_stack

    def runaway():
        def f(n):
            return f(n + 1)
        return f(0)

    with pytest.raises(PipelineError, match="nests too deeply"):
        _deep_stack(runaway)


# ── F75: `Subst` semantics survived the change of representation ─────────────


def test_a_later_binding_shadows_an_earlier_one():
    s = Subst.empty().extend(1, TCon("Int")).extend(1, TCon("Bool"))
    assert s.lookup(1) == TCon("Bool")


def test_the_list_form_still_resolves_to_its_first_entry():
    # `test_types.py` and this constructor predate the dict; a repeated key
    # there meant the *first* pair, and a dict keeps the last written.
    s = Subst(((1, TCon("Int")), (1, TCon("Bool"))))
    assert s.lookup(1) == TCon("Int")


def test_a_self_binding_is_dropped():
    # `α ↦ α` carries nothing and makes `apply` diverge.
    assert not Subst.empty().extend(7, TVar(7))


def test_compose_sees_the_left_bindings_through_the_right():
    left = Subst.empty().extend(1, TVar(2))
    right = Subst.empty().extend(2, TCon("Int"))
    both = left.compose(right)
    assert both.apply(TVar(1)) == TCon("Int")
    assert both.apply(TVar(2)) == TCon("Int")


def test_compose_keeps_the_right_binding_when_the_left_becomes_trivial():
    # `{1 ↦ β} ∘ {β ↦ 1}` maps 1 to itself, so the binding is skipped —
    # and skipping must leave the right-hand side's own binding alone.
    left = Subst.empty().extend(1, TVar(2))
    right = Subst.empty().extend(2, TVar(1))
    both = left.compose(right)
    assert both.lookup(2) == TVar(1)


def test_compose_with_empty_is_identity_on_both_sides():
    s = Subst.empty().extend(1, TCon("Int"))
    assert s.compose(Subst.empty()) == s
    assert Subst.empty().compose(s) == s


def test_apply_returns_the_same_object_when_nothing_changes():
    """The optimisation, stated as the property it must preserve.

    Returning `t` itself rather than an equal copy is only sound because
    types are immutable; if that stops being true this test is the warning.
    """
    s = Subst.empty().extend(99, TCon("Int"))
    t = TFun(TCon("Bool"), TCon("Char"))
    assert s.apply(t) is t
    assert s.apply(TVar(3)) is not None


def test_apply_still_rebuilds_when_something_does_change():
    s = Subst.empty().extend(3, TCon("Int"))
    t = TFun(TVar(3), TCon("Char"))
    got = s.apply(t)
    assert got is not t
    assert got == TFun(TCon("Int"), TCon("Char"))


def test_apply_follows_a_chain_and_survives_a_cycle():
    assert Subst(((1, TVar(2)), (2, TCon("Int")))).apply(TVar(1)) == TCon("Int")
    # `1 ↦ 2, 2 ↦ 1` — either is an equally good representative, and the
    # walk must stop rather than chase the loop.
    assert Subst(((1, TVar(2)), (2, TVar(1)))).apply(TVar(1)) in (
        TVar(1), TVar(2))


# ── F78: destructive unification, aliasing every substitution to one store ──


def test_outside_an_inference_scope_substitutions_are_still_persistent():
    """`Subst` is unchanged for everyone who is not inference.

    `constraint.py` and the ADT instantiation in `infer.py` build ordinary
    substitutions and rely on extending one not disturbing the original.
    """
    a = Subst.empty().extend(1, TCon("Int"))
    b = a.extend(2, TCon("Bool"))
    assert a.lookup(2) is None and b.lookup(2) == TCon("Bool")
    assert Subst.empty().lookup(1) is None


def test_inside_a_scope_every_empty_is_the_same_store():
    from gestate.types import Unifier, unifying

    with unifying() as store:
        assert Subst.empty() is store
        assert isinstance(store, Unifier)
        # Extending mutates in place and composing is already done, which
        # is exactly what makes the threading in `infer.py` free.
        assert store.extend(1, TCon("Int")) is store
        assert Subst.empty().lookup(1) == TCon("Int")
        assert store.compose(Subst.empty()) is store
    assert Subst.empty() is Subst._empty


def test_the_scope_nests_and_restores():
    from gestate.types import unifying

    with unifying() as outer:
        outer.extend(1, TCon("Int"))
        with unifying() as inner:
            assert inner is not outer
            assert inner.lookup(1) is None       # ids restart with `Fresh`
        assert Subst.empty() is outer
        assert outer.lookup(1) == TCon("Int")


def test_a_separate_subst_is_absorbed_rather_than_ignored():
    from gestate.types import unifying

    with unifying() as store:
        store.compose(Subst(((5, TCon("Char")),)))
        assert store.lookup(5) == TCon("Char")


def test_path_compression_flattens_a_chain():
    from gestate.types import unifying

    with unifying() as store:
        for i in range(1, 60):
            store.extend(i, TVar(i + 1))
        store.extend(60, TCon("Int"))
        assert store.apply(TVar(1)) == TCon("Int")
        # Every link now points straight at the answer, so the next walk is
        # one step.  Without this the chains grow with the program.
        assert all(store.lookup(i) == TCon("Int") for i in range(1, 61))


def test_path_compression_leaves_a_cycle_alone():
    from gestate.types import unifying

    # `α ↦ β, β ↦ α` — rewriting the path would make one point at itself,
    # and `apply` would then not terminate.
    with unifying() as store:
        store.extend(1, TVar(2))
        store.extend(2, TVar(1))
        assert store.apply(TVar(1)) in (TVar(1), TVar(2))
        assert store.apply(TVar(2)) in (TVar(1), TVar(2))


def test_the_same_program_infers_the_same_types_either_way():
    """The property the whole change rests on.

    Aliasing every substitution to one store is only sound because
    inference never backtracks.  This checks the visible consequence:
    inferred signatures are what they were.
    """
    assert evaluate("f : a -> a\nf x = x\n\nmain : Int\nmain = f 3\n") == "3"
    assert evaluate("main : Int\nmain = sum (map (x => x * 2) [1,2,3])\n") == "12"
    # A signature variable is still rigid — the store must not let a body
    # bind one just because it is visible sooner.
    with pytest.raises(Exception, match="rigid"):
        evaluate("f : a -> Int\nf x = x + 1\n\nmain : Int\nmain = f 1\n")
