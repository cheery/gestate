"""Tests for the substitution representation (``gestate/types.py``).

``spec/types.md`` §2 requires ``unify`` to be total on well-formed input.
It has an occurs check, so no variable is ever bound to a type containing
itself — but a *composition* can still produce a binding the occurs check
never saw.
"""

from __future__ import annotations

from gestate.pipeline import evaluate
from gestate.types import Subst, TApp, TCon, TFun, TVar


def test_a_self_binding_is_dropped():
    """`α ↦ α` says nothing, and following it would not terminate."""
    s = Subst.empty().extend(1, TVar(1))

    assert not s
    assert s.apply(TVar(1)) == TVar(1)


def test_composing_opposite_bindings_terminates():
    """`{17 ↦ β}` after `{β ↦ 17}` maps 17 to itself.

    Both substitutions are what `unify` legitimately produces — one from
    each side of `α ~ β` — so the identity binding has to be absorbed
    rather than stored.
    """
    left = Subst.empty().extend(17, TVar(99))
    right = Subst.empty().extend(99, TVar(17))
    s = left.compose(right)

    assert s.apply(TVar(17)) in (TVar(17), TVar(99))
    assert s.apply(TApp(TCon("Sig"), TVar(17))) is not None


def test_a_variable_cycle_resolves_to_a_representative():
    """`α ↦ β, β ↦ α` — either variable stands for the class."""
    s = Subst(((1, TVar(2)), (2, TVar(1))))

    assert s.apply(TVar(1)) in (TVar(1), TVar(2))
    assert s.apply(TFun(TVar(1), TVar(2))) is not None


def test_chains_still_resolve():
    """The cycle guard must not stop an ordinary chain early."""
    s = Subst(((1, TVar(2)), (2, TVar(3)), (3, TCon("Int"))))

    assert s.apply(TVar(1)) == TCon("Int")


def test_mutually_recursive_signal_combinator_typechecks():
    """The program that first hit the cycle: `switch` with a local `cont`."""
    assert evaluate("""
mkSig : ExL a -> ExL (Sig a)
mkSig d = (x => x ::: mkSig d) |> d

switch : Sig a -> ExL (Sig a) -> Sig a
switch (x ::: xs) d = x ::: ((s => case s of
    SyncLeft xs2 -> switch xs2 d
    SyncRight d2 -> d2
    SyncBoth d2 d3 -> d3) |> sync xs d)

main : Int
main = head (switch (1 ::: never) never)
""") == "1"
