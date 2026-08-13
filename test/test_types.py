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


def test_unifying_scopes_do_not_cross_threads():
    """Overlapping `unifying()` scopes on two threads stay two stores.

    As a module global the store poisoned itself: when a build thread's
    scope and this thread's scope overlapped, whichever exited *last*
    restored the other thread's dead `Unifier` — permanently, so every
    later `Subst.empty()` in the process answered with it.  That is the
    2026-08-13 suite failure (this file's self-binding test saw
    `Unifier(9 bindings)`), and the shape of F103's run-to-run rigid-
    variable errors: inference runs on daemon threads in the workbench
    (`audioeditor.apply`, `audiolive`'s watcher) while the session
    thread typechecks palette queries.
    """
    import threading

    from gestate.types import Unifier, unifying

    entered = threading.Event()
    leave = threading.Event()

    def background():
        with unifying() as theirs:
            for k in range(9):
                theirs.extend(k, TVar(99 + k))
            entered.set()
            leave.wait(5.0)

    worker = threading.Thread(target=background, daemon=True)
    worker.start()
    assert entered.wait(5.0)
    try:
        with unifying() as ours:
            # Their nine bindings are not in this thread's store.
            assert isinstance(Subst.empty(), Unifier)
            assert Subst.empty() is ours
            assert not Subst.empty().extend(1, TVar(1))
            # The poisoning order: they exit while this scope is open.
            leave.set()
            worker.join(5.0)
    finally:
        leave.set()

    # After both scopes close, empty() is the identity again — not
    # whichever thread's store happened to be restored last.
    assert Subst.empty() is Subst._empty
    assert not Subst.empty().extend(1, TVar(1))


def test_a_mismatch_names_whole_types_with_shared_letters():
    """`expected 'List', got 'Sig'` told the author about two
    constructor heads when the fact they can act on is `String` against
    `Sig Float` — so a head collision under an application reports the
    whole types, resugared (`List Char` is written `String`, as the
    prelude writes it), with `got` indented to `expected`'s column."""
    import pytest

    from gestate.unify import UnifyError, unify

    with pytest.raises(UnifyError) as caught:
        unify(TApp(TCon("Sig"), TCon("Float")),
              TApp(TCon("List"), TCon("Char")))
    said = str(caught.value)
    assert "expected String" in said, said
    assert "got Sig Float" in said, said
    lines = said.splitlines()
    assert lines[1].lstrip().startswith("got")
    assert lines[1].index("got") == lines[0].index("expected"), \
        "the two types do not start one above the other"


def test_metavariables_are_lettered_in_messages():
    """`got (a3303 -> a3305)` names nothing the author can search for;
    both sides of a mismatch are rendered with **one** lettering, so a
    `b` in `expected` is the same variable as a `b` in `got`."""
    import pytest

    from gestate.unify import UnifyError, unify

    with pytest.raises(UnifyError) as caught:
        unify(TFun(TVar(3303), TVar(3305)),
              TApp(TCon("ExL"), TCon("Int")))
    said = str(caught.value)
    assert "a3303" not in said and "a3305" not in said, said
    assert "a -> b" in said, said
