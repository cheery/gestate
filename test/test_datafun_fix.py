"""Tests for Datafun's ``fix`` — the semilattice fixed point.

Per ``spec/data.md`` §I.5 (Datafun fig. 2.5) the rule is

    Γ ⊢ e : □(L → L)
    ────────────────
    Γ ⊢ fix e : L

so the iterated function must be *boxed*; ``L`` is a ``Set`` here, the
only semilattice the generated helpers cover.
"""

from __future__ import annotations

import pytest

from gestate.expr import ELet, EAp, EGlobal, EProj, EVar
from gestate.infer import InferError
from gestate.pipeline import evaluate
from gestate.seminaive import make_semifix_helpers
from gestate.unify import UnifyError


# ── Typing ───────────────────────────────────────────────────────────────────


def test_fix_requires_a_boxed_function():
    with pytest.raises(InferError, match="boxed monotone set function"):
        evaluate("main : Set (Cyclic 8)\nmain = fix {1}\n")


def test_fix_boxes_a_bare_lambda():
    """`fix r => e` and `fix (r => e)` mean `fix Box (r => e)`.

    Writing the box by hand was pure ceremony: an *unboxed* lambda here
    could never be well-typed, so the sugar steals no other reading.
    """
    for spelling in ("fix x => {1}", "fix (x => {1})", "fix Box (x => {1})"):
        assert evaluate(f"main : Set (Cyclic 8)\nmain = {spelling}\n") == \
            "Pack{1,2} 1 Pack{0,0}"


def test_the_implicit_box_still_disciplines():
    # The sugar drops the *writing* of `Box`, not what a box means: a
    # monotone variable captured under it is rejected exactly as before.
    from gestate.pipeline import MonotoneError

    with pytest.raises(MonotoneError, match="monotone variable"):
        evaluate("f : Set Int ~> Set Int\nf s = fix r => s \\/ r\n"
                 "main : Set Int\nmain = f {1}\n")


def test_fix_result_is_the_fixpoint_type_not_the_function_type():
    # `fix Box (x => {1}) : Set (Cyclic 8)` — before, `fix` returned the type of
    # its own argument, so this failed to check against the signature.
    assert evaluate("main : Set (Cyclic 8)\nmain = fix Box (x => {1})\n") == \
        "Pack{1,2} 1 Pack{0,0}"


def test_fix_over_a_non_semilattice_is_rejected():
    """Still rejected — but by the subgrammar check, not by inference.

    `fix` used to be pinned to `Set a` in the inferencer, so a non-set was
    a type error.  It now accepts any type the two sides agree on and lets
    `subgrammar.py` ask *which* semilattice, once the substitution has
    settled — which is what lets `fix` work at a product (`fixme.md` F37)
    while still refusing `Int`.
    """
    from gestate.pipeline import SubgrammarError

    with pytest.raises(SubgrammarError, match="fixtype"):
        evaluate("main : Int\nmain = fix Box (x => 1)\n")
    with pytest.raises(SubgrammarError, match="fixtype"):
        evaluate("main : Int -> Int\nmain = fix Box (f => f)\n")


# ── Naïve path (``fix_Set_Int``, used inside ``main``) ────────────────────────


def test_empty_fixpoint():
    src = "main : Set (Cyclic 8)\nmain = fix Box (x => for (y in x) {y})\n"
    assert evaluate(src) == "Pack{0,0}"


def test_fix_in_a_let_binding():
    src = "main : Set (Cyclic 8)\nmain = let s = fix Box (x => {1}) in s\n"
    assert evaluate(src) == "Pack{1,2} 1 Pack{0,0}"


def test_fix_as_a_function_argument():
    src = (
        "id : Set (Cyclic 8) -> Set (Cyclic 8)\n"
        "id s = s\n\n"
        "main : Set (Cyclic 8)\n"
        "main = id (fix Box (x => {1}))\n"
    )
    assert evaluate(src) == "Pack{1,2} 1 Pack{0,0}"


# ── Seminaïve path (``semifix_Set_Int``, used inside user SCs) ────────────────


def test_fix_inside_a_user_supercombinator():
    # A non-`main` SC goes through the ϕ/δ transform, so its `fix` becomes
    # `semifix ϕe` — the boxed function arrives as a (ϕe, δe) pair.
    src = (
        "f : Set (Cyclic 8) -> Set (Cyclic 8)\n"
        "f s = fix Box (x => {1})\n\n"
        "main : Set (Cyclic 8)\n"
        "main = f {2}\n"
    )
    result = evaluate(src)
    assert result.startswith("Pack{1,2}") and result.endswith("Pack{0,0}")


def test_semifix_takes_the_boxed_pair():
    helpers = dict((name, (arity, lam))
                   for name, arity, lam in make_semifix_helpers(0, 1, 3, 2))
    arity, lam = helpers["semifix_Set_Int"]
    assert arity == 1
    # It destructures the pair rather than expecting two separate arguments.
    defs = dict(lam.body.defs)
    assert defs["f"] == EAp(EProj(0), EVar("p"))
    assert defs["f'"] == EAp(EProj(1), EVar("p"))


def test_semifix_loop_passes_the_base_function_along():
    helpers = dict((name, (arity, lam))
                   for name, arity, lam in make_semifix_helpers(0, 1, 3, 2))
    _arity, lam = helpers["semifixL_Set_Int"]
    # The recursive alternative binds `x'` first (change minimization
    # needs the *new* accumulator), then recurses.
    recursive_alt = lam.body.alts[1].body
    assert isinstance(recursive_alt, ELet)
    assert dict(recursive_alt.defs)["x'"] == EAp(
        EAp(EGlobal("join_Set_Int"), EVar("x")), EVar("dx"))
    # semifixL f f' x' (diff (f' x dx) x') — the first argument is `f`.
    call = recursive_alt.body
    while isinstance(call, EAp) and not isinstance(call.fn, EGlobal):
        call = call.fn
    assert call.fn == EGlobal("semifixL_Set_Int")
    assert call.arg == EVar("f")


def test_the_next_delta_is_minimized_against_the_new_accumulator():
    """`dx_{i+1} = (f' xi dxi) \\ x_{i+1}` — thesis §4.3, `errata.md` D4."""
    helpers = dict((name, (arity, lam))
                   for name, arity, lam in make_semifix_helpers(0, 1, 3, 2))
    _arity, lam = helpers["semifixL_Set_Int"]
    recursive_alt = lam.body.alts[1].body
    delta_arg = recursive_alt.body.arg
    assert delta_arg == EAp(
        EAp(EGlobal("diff_Set_Int"),
            EAp(EAp(EVar("f'"), EVar("x")), EVar("dx"))),
        EVar("x'"))


def test_semifix_stabilises_on_containment_not_emptiness():
    """`dx ⊑ x`, not `dx = ⊥` — the thesis fig. 4.2, and `errata.md` D2.

    `δ(e ∨ f) = δe ∨ δf` overapproximates, so a delta routinely contains
    elements already known.  Testing for an *empty* delta then never
    fires and the loop runs forever.
    """
    helpers = dict((name, (arity, lam))
                   for name, arity, lam in make_semifix_helpers(0, 1, 3, 2))
    _arity, lam = helpers["semifixL_Set_Int"]

    test = lam.body.scrut
    assert test == EAp(EAp(EGlobal("subset_Set_Int"), EVar("dx")), EVar("x"))
    # On stabilising it returns the accumulator itself.
    assert lam.body.alts[0].body == EVar("x")


def test_a_datalog_fixed_point_terminates():
    """`fix (r => base \\/ step r)` — the shape every Datalog query has.

    Closing `{1}` under `+1` in `Cyclic 4` reaches `{0,1,2,3}` and stops.
    With the old emptiness test this looped forever.
    """
    result = evaluate(
        "reach : Box (Set (Cyclic 4)) -> Set (Cyclic 4)\n"
        "reach bs = unbox seed = bs in fix Box "
        "(r => seed \\/ (for (x in r) {x + 1}))\n"
        "main : Set (Cyclic 4)\n"
        "main = reach (Box {1})\n"
    )
    assert result.startswith("Pack")


def test_the_spec_prescribes_the_test_the_generator_builds():
    """`spec/data.md` §I.5 and `semifixL` say the same thing.

    F6's entry said the convergence test was "fixed in both spec and
    implementation" and, for a fortnight, only one of those was true:
    §I.5 still prescribed `eq dx' ⊥` while `make_semifix_helpers` had
    built `subset_L dx x` since the repair, and `errata.md` D2 carried
    the outstanding sentence under a *resolved* heading.  Nothing held
    the two texts together, so nothing said so.

    This is a citation check and not a proof — it catches the spec being
    reverted, not the implementation drifting from a spec that still
    reads correctly.  The behavioural half is the test above and the
    transitive-closure family in `test_relations.py`.
    """
    from pathlib import Path

    spec = Path(__file__).resolve().parent.parent / "spec" / "data.md"
    body = spec.read_text()
    i = body.index("### I.5 `semifix`")
    section = body[i:body.index("### I.6", i)]

    # The amendment states the thesis's test and marks the old one wrong.
    assert "dxi ⊑ xi" in section
    assert "**wrong**" in section

    # And the generator builds exactly that test.
    helpers = dict((name, (arity, lam))
                   for name, arity, lam in make_semifix_helpers(0, 1, 3, 2))
    _arity, lam = helpers["semifixL_Set_Int"]
    assert lam.body.scrut == EAp(EAp(EGlobal("subset_Set_Int"),
                                     EVar("dx")), EVar("x"))
