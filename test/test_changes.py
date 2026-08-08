"""Zero changes are built at their own type (`fixme.md` F3, F4, F5).

δ has to produce a zero change in five places — the change of a box, of a
literal, of a primitive, the `dx` a `for` binds for its element, and the
value a `case`'s never-taken branch returns.  Every one of them used to be
`bottom_Set_Int`.  That is invisible at run time (gestate's `⊥` is `Nil`,
and so is any other nullary constructor) and wrong the moment anything is
typed: `spec/data.md` §I.4 wants `()` where `ΔA = 1`, `⊥` at a set, and
`dummy x` — a *value*-directed zero — at a sum.

`spec/errata.md` D7 is why it is a real mismatch rather than a notational
one: `Φ(□(A+B))` is a boxed tagged pair and `Φ(□A+□B)` a tagged boxed
pair, and it is `split` that moves between them.
"""

from __future__ import annotations

from gestate.changes import UNIT, Changes
from gestate.declarations import classify
from gestate.expr import (
    Alter, EAp, EBox, ECase, ECon, EFor, EGlobal, ENum, EProj, ESet, ETuple,
    EVar,
)
from gestate.pipeline import evaluate
from gestate.seminaive import SeminaiveCtx, delta, phi
from gestate.syntax import parse
from gestate.types import TApp, TCon, TVar, mk_tuple


CONS = classify(parse("")).cons

INT = TCon("Int")
SET_INT = TApp(TCon("Set"), INT)
PAIR = mk_tuple([INT, INT])
MAYBE_INT = TApp(TCon("Maybe"), INT)


def _ctx() -> SeminaiveCtx:
    return SeminaiveCtx(builder=Changes(CONS))


def _changes() -> Changes:
    return Changes(CONS)


# ── The change structure ─────────────────────────────────────────────────────


def test_a_discrete_type_has_the_unit_change():
    """`ΔInt = 1` — nothing about an integer can change under a `fix`."""
    assert _changes().zero(INT, EVar("x")) == UNIT


def test_a_set_s_change_is_the_empty_set():
    """`ΔL = L` at a semilattice (lemma 20), and its zero is ⊥."""
    c = _changes()
    assert c.zero(SET_INT, EVar("x")) == EGlobal("bottom_Set_Int")
    # …and the helper is requested, because δ is what discovers the type.
    assert "Set_Int" in c.sets


def test_a_product_s_change_is_the_product_of_the_changes():
    """The case stage 2.2 needs: `⊥` is not a value at `L×M`."""
    got = _changes().zero(mk_tuple([SET_INT, INT]), EVar("p"))
    assert got == ETuple([EGlobal("bottom_Set_Int"), UNIT])


def test_a_relation_element_s_change_is_a_pair_of_units():
    assert _changes().zero(PAIR, EVar("p")) == ETuple([UNIT, UNIT])


def test_a_sum_s_change_needs_the_value():
    """`dummy (ini x) = ini (dummy x)`: the tag has to be reproduced."""
    c = _changes()
    assert c.zero(MAYBE_INT, EVar("m")) == EAp(EGlobal("dummy_Maybe_Int"),
                                               EVar("m"))
    assert "Maybe_Int" in c.dummies


def test_a_sum_with_no_value_at_hand_degrades_to_unit():
    assert _changes().zero(MAYBE_INT, None) == UNIT


def test_an_unknown_type_has_no_change():
    """Helpers are per monomorphic type (D9), so `a` has nothing to call."""
    assert _changes().zero(TApp(TCon("Maybe"), TVar(1)), EVar("m")) == UNIT
    assert _changes().zero(None, EVar("m")) == UNIT


# ── The generated `dummyA` ───────────────────────────────────────────────────


def test_dummy_is_generated_per_requested_type():
    c = _changes()
    c.zero(MAYBE_INT, EVar("m"))
    generated = c.generate()

    assert [name for name, _a, _l in generated] == ["dummy_Maybe_Int"]
    name, arity, lam = generated[0]
    assert arity == 1
    # `Nothing ▹ Nothing`, `Just x ▹ Just ()` — same tag, zeroed fields.
    body = lam.body
    assert isinstance(body, ECase)
    assert [(a.tag, len(a.names), a.body) for a in body.alts] == [
        (CONS["Nothing"].tag, 0, ECon(CONS["Nothing"].tag, [])),
        (CONS["Just"].tag, 1, ECon(CONS["Just"].tag, [UNIT])),
    ]


def test_a_recursive_type_generates_one_recursive_helper():
    c = _changes()
    c.zero(TApp(TCon("List"), INT), EVar("xs"))
    generated = c.generate()

    assert [name for name, _a, _l in generated] == ["dummy_List_Int"]
    cons_alt = generated[0][2].body.alts[1]
    # `Cons h t ▹ Cons () (dummy_List_Int t)`
    assert cons_alt.body.args[1] == EAp(EGlobal("dummy_List_Int"),
                                        EVar(cons_alt.names[1]))


# ── δ's zero changes ─────────────────────────────────────────────────────────


def test_delta_of_a_box_is_unit():
    """`ΔΦ□A = 1` — the crux of `fixme.md` F3."""
    assert delta(EBox(ESet([], SET_INT)), _ctx()) == UNIT


def test_delta_of_a_literal_is_unit():
    assert delta(ENum(3), _ctx()) == UNIT


def test_delta_of_a_primitive_is_unit():
    assert delta(EGlobal("prim_add_int"), _ctx()) == UNIT


def test_delta_of_a_captured_variable_is_the_zero_at_its_type():
    """A variable a box closes over is constant for the whole iteration."""
    inner = _ctx().enter_box()
    assert delta(EVar("s", SET_INT), inner) == EGlobal("bottom_Set_Int")
    assert delta(EVar("n", INT), inner) == UNIT


def test_delta_of_an_unannotated_variable_falls_back():
    """Nothing recorded a type, so the designated bottom stands."""
    inner = _ctx().enter_box()
    assert delta(EVar("s"), inner) == EGlobal("bottom_Set_Int")


def test_delta_distributes_over_a_projection():
    """`δ(πᵢ e) = πᵢ δe`, not `πᵢ ϕe δe` (`fixme.md` F57)."""
    got = delta(EAp(EProj(0, 2), EVar("p")), _ctx())
    assert got == EAp(EProj(0, 2), EVar("dp"))


# ── `for` binds `dummy x`, not ⊥ ─────────────────────────────────────────────

def _for(elem_type):
    return EFor("x", EVar("s"), EVar("x"), SET_INT, elem_type)


def test_for_binds_the_zero_change_at_the_element_type():
    got = phi(_for(PAIR), _ctx())
    assert got.body.defs == [("dx", ETuple([UNIT, UNIT]))]


def test_for_over_a_set_of_sets_still_binds_bottom():
    """`dummy{A} = {}`, so ⊥-propagation (D3) still sees a ⊥ to delete
    work with — the case where it matters is exactly the case it fires
    on."""
    got = phi(_for(SET_INT), _ctx())
    assert got.body.defs == [("dx", EGlobal("bottom_Set_Int"))]


# ── `case`'s dead branches ───────────────────────────────────────────────────

def _two_constructor_case():
    """`case m of Nothing ▹ {} | Just v ▹ {}` with `v : {Int}`."""
    return ECase(EVar("m"), [
        Alter(CONS["Nothing"].tag, [], ESet([], SET_INT)),
        Alter(CONS["Just"].tag, ["v"], ESet([], SET_INT),
              field_types=(SET_INT,)),
    ])


def _dead_alt(out, tag):
    """The inner `case δe` alternative for ``tag``, inside ``out``."""
    branch = next(a for a in out.body.alts if a.tag == tag)
    inner = branch.body.defs[0][1]
    return next(a for a in inner.alts if a.tag != tag)


def test_a_dead_branch_returns_dummy_of_the_matched_fields():
    out = delta(_two_constructor_case(), _ctx())
    dead = _dead_alt(out, CONS["Just"].tag)

    assert dead.body == EGlobal("bottom_Set_Int")


def test_a_dead_branch_binds_as_many_fields_as_its_own_constructor():
    """It bound exactly one whatever the arity, which mis-binds at any
    other — `Nothing` takes none."""
    out = delta(_two_constructor_case(), _ctx())
    dead = _dead_alt(out, CONS["Just"].tag)

    assert dead.tag == CONS["Nothing"].tag
    assert dead.names == []


# ── End to end ───────────────────────────────────────────────────────────────


def _cells(out: str) -> int:
    """How many elements the printed set has.

    A cons cell is the two-field constructor of the set's list
    representation; its *tag* moves when the program declares data types
    of its own, so it is counted by arity.
    """
    return out.count(",2}")


def test_a_case_with_mixed_arities_inside_a_datafun_program():
    """The whole point of the arity fix: two constructors, two arities,
    both reachable from δ."""
    assert _cells(evaluate("""T := A (Maybe Int) | B (Set (Cyclic 4)) Int

f : T -> Set (Cyclic 4)
f t = case t of
    A m -> {1}
    B s n -> s

main : Set (Cyclic 4)
main = for (x in {1, 2}) (f (A Nothing))
""")) == 1


def test_the_helpers_a_zero_change_asks_for_are_emitted():
    """A `⊥` at a set type no annotated node mentions still links."""
    assert _cells(evaluate("""T := A (Set (Cyclic 4)) | B Int

g : T -> Set (Cyclic 8)
g t = case t of
    A s -> {1}
    B n -> {2}

main : Set (Cyclic 8)
main = for (x in {1}) (g (B 0))
""")) == 1
