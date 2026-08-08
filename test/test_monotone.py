"""Tests for the monotone/discrete discipline, and for boxes crossing
between the naive and seminaive paths.

Datafun checks a box in the stripped context `⌈Γ⌉` (thesis fig. 2.3), so
`[e]` may not close over a monotone variable.  The ϕ/δ transform depends
on it — `ϕ(λX. e) = λX. ϕe` gives a lambda no change parameters, while
`ϕ[e]` compiles the body again through δ, which wants them.

A box is the runtime pair `(base, change)` on *both* paths; before that
was settled a box built by ordinary code could not be consumed by
ϕ/δ-generated code (`implementation_order.md` §17).
"""

from __future__ import annotations

import pytest

from gestate.infer import InferError
from gestate.pipeline import MonotoneError, compile, evaluate


# ── Where monotone variables come from ──────────────────────────────────────


def test_fix_requires_a_monotone_function():
    """`Γ ⊢ e : □(fixL ~> fixL) ⟹ Γ ⊢ fix e : fixL` (fig. 2.3).

    Monotonicity is *why* the least fixed point exists: the chain
    `⊥ ⩽ f ⊥ ⩽ f (f ⊥) ⩽ …` only ascends if `f` respects the order.
    """
    compile("step : Set (Cyclic 8) ~> Set (Cyclic 8)\nstep r = r\n"
            "main : Set (Cyclic 8)\nmain = fix Box step\n")

    with pytest.raises(InferError, match="boxed monotone set function"):
        compile("step : Set (Cyclic 8) -> Set (Cyclic 8)\nstep r = r\n"
                "main : Set (Cyclic 8)\nmain = fix Box step\n")


def test_a_monotone_variable_may_not_be_boxed():
    """`[e]` is checked in `⌈Γ⌉`, which drops the monotone variables."""
    with pytest.raises(MonotoneError, match="'r' is a monotone variable"):
        compile("main : Set (Cyclic 8)\n"
                "main = fix Box (r => fix Box (r2 => r))\n")


def test_a_monotone_variable_may_not_be_passed_to_an_ordinary_function():
    """`A -> B` is `□A → B`, so its argument goes under a box."""
    with pytest.raises(MonotoneError, match="'s' is a monotone variable"):
        compile("g : Set (Cyclic 8) -> Set (Cyclic 8)\ng s = s\n"
                "h : Set (Cyclic 8) ~> Set (Cyclic 8)\nh s = g s\n"
                "main : Set (Cyclic 8)\nmain = h {1}\n")


def test_a_monotone_variable_may_be_passed_to_a_monotone_function():
    compile("g : Set (Cyclic 8) ~> Set (Cyclic 8)\ng s = s\n"
            "h : Set (Cyclic 8) ~> Set (Cyclic 8)\nh s = g s\n"
            "main : Set (Cyclic 8)\nmain = h {1}\n")


def test_a_monotone_variable_may_be_looped_over():
    """`for`'s scrutinee is not a stripped position (fig. 2.3, `for`)."""
    compile("h : Set (Cyclic 8) ~> Set (Cyclic 8)\nh s = for (x in s) {x}\n"
            "main : Set (Cyclic 8)\nmain = h {1}\n")


def test_the_error_names_the_way_out():
    with pytest.raises(MonotoneError, match="unbox"):
        compile("main : Set (Cyclic 8)\n"
                "main = fix Box (r => fix Box (r2 => r))\n")


# ── Discrete binders, which is nearly everything ────────────────────────────


def test_an_ordinary_parameter_may_be_boxed():
    """`->` binds discretely, so a box may close over it.

    This is the whole point of the two arrows: under Datafun's single
    (monotone) arrow this program is ill-typed, and gestate used to crash
    on it in the lambda lifter.
    """
    assert evaluate("close : Set (Cyclic 8) -> Set (Cyclic 8)\n"
                    "close s = fix Box (r => s)\n"
                    "main : Set (Cyclic 8)\n"
                    "main = close {1,2}\n").startswith("Pack")


def test_a_for_bound_variable_may_be_boxed():
    """`for (x ∈ e) f` binds `x :: A` — discrete (fig. 2.3, `for`)."""
    assert evaluate("f : Set (Cyclic 8) -> Set (Cyclic 8)\n"
                    "f s = for (x in s) (fix Box (r => {x}))\n"
                    "main : Set (Cyclic 8)\n"
                    "main = f {1,2}\n").startswith("Pack")


def test_an_unbox_bound_variable_may_be_captured():
    assert evaluate("close : Box (Set (Cyclic 8)) -> Set (Cyclic 8)\n"
                    "close bs = unbox s = bs in fix Box (r => s)\n"
                    "main : Set (Cyclic 8)\n"
                    "main = close (Box {1,2})\n").startswith("Pack")


def test_a_closed_box_is_fine():
    assert evaluate("main : Set (Cyclic 8)\nmain = fix Box (r => {1})\n") \
        .startswith("Pack")


def test_polymorphic_code_is_untouched():
    """A binder whose type is a variable is treated as discrete.

    An over-approximation in the permissive direction — see
    `types.has_nontrivial_order`.  The alternative marks every `case`
    binder in generic code monotone and rejects ordinary programs.
    """
    assert evaluate("len : List a -> Int\n"
                    "len xs = case xs of\n"
                    "  Nil -> 0\n"
                    "  Cons h t -> 1 + len t\n"
                    "main : Int\nmain = len (Cons 1 (Cons 2 Nil))\n") == "2"


def test_frp_code_is_untouched():
    """Every FRP type is discretely ordered, so nothing here is monotone."""
    compile("mkSig : ExL a -> ExL (Sig a)\n"
            "mkSig d = (x => x ::: mkSig d) |> d\n"
            "map : (a -> b) -> Sig a -> Sig b\n"
            "map f (x ::: xs) = f x ::: (map f |> xs)\n"
            "c : Chan Int\nc = chan\n"
            "main : Sig Int\nmain = map (n => n) (0 ::: mkSig (wait c))\n")


# ── One box representation ───────────────────────────────────────────────────


def test_unbox_of_a_box_built_outside_the_transform():
    """`main` is not ϕ/δ-transformed, so the `Box 5` it builds and the
    `unbox` in a transformed SC must agree on the representation."""
    assert evaluate("f : Box Int -> Int\n"
                    "f b = unbox x = b in x\n"
                    "main : Int\nmain = f (Box 5)\n") == "5"


def test_fix_takes_the_pair_wherever_it_is_written():
    """`fix` is handed a boxed function, i.e. a pair, and unpacks it.

    Both spellings run the same `semifix` now (`fixme.md` F9); before,
    `main` was exempt from ϕ/δ and the first of these ran the naïve loop.
    """
    in_main = evaluate("main : Set (Cyclic 8)\nmain = fix Box (x => {7})\n")
    in_an_sc = evaluate("f : Set (Cyclic 8)\nf = fix Box (x => {7})\n"
                        "main : Set (Cyclic 8)\nmain = f\n")

    assert "7" in in_main and "7" in in_an_sc


# ── Datafun and FRP in one program ───────────────────────────────────────────


def test_a_signal_carrying_a_datafun_fixed_point():
    """`spec/data.md` §II.2's open question, answered in the affirmative:
    `Sig {(Cyclic 8)}` is well-formed and a `fix`/`for` may compute a signal's
    value.  (D1's caveat stands — `{(Cyclic 8)}` is not a fixtype, so `fix` over
    it is not guaranteed to terminate.)"""
    from gestate.reactive import init_program

    state = compile("mkSig : ExL a -> ExL (Sig a)\n"
                    "mkSig d = (x => x ::: mkSig d) |> d\n"
                    "close : Box (Set (Cyclic 8)) -> Set (Cyclic 8)\n"
                    "close bs = unbox s = bs in fix Box (r => for (x in s) {x})\n"
                    "c : Chan (Set (Cyclic 8))\nc = chan\n"
                    "main : Sig (Set (Cyclic 8))\n"
                    "main = close (Box {1,2}) ::: mkSig (wait c)\n")
    reactive = init_program(state)

    assert reactive.chans == {0: "{(Cyclic 8)}"}
    assert len(state.now) == 1


def test_a_signal_value_can_feed_a_datafun_query():
    """`spec/errata.md` R14, resolved by the discrete arrow.

    `map`'s function is an ordinary `->`, so `n` is discrete and may be
    boxed.  Under Datafun's single monotone arrow this is ill-typed —
    which is what used to make the union a demo rather than a language.
    """
    from gestate.reactive import init_program, react

    state = compile("mkSig : ExL a -> ExL (Sig a)\n"
                    "mkSig d = (x => x ::: mkSig d) |> d\n"
                    "map : (a -> b) -> Sig a -> Sig b\n"
                    "map f (x ::: xs) = f x ::: (map f |> xs)\n"
                    "close : Box (Set (Cyclic 8)) -> Set (Cyclic 8)\n"
                    "close bs = unbox s = bs in fix Box (r => for (y in s) {y})\n"
                    "c : Chan (Cyclic 8)\nc = chan\n"
                    "main : Sig (Set (Cyclic 8))\n"
                    "main = map (n => close (Box {n})) (0 ::: mkSig (wait c))\n")
    reactive = init_program(state)
    react(reactive, [(0, 7)])

    # The sampled signal now holds the singleton set {7}.
    computed = state.now[-1].value
    assert computed.args[0].n == 7
