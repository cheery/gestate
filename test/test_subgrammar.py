"""Tests for Datafun's four type subgrammars (thesis fig. 2.1).

    eqtypes         A, B ::= {A}_eq | 1 | A×B | A+B
    semilattices    L, M ::= {A}_eq | 1 | L×M
    finite eqtypes  A, B ::= {A}_fin | 1 | A×B | A+B
    fixtypes        L, M ::= {A}_fin | 1 | L×M

`spec/data.md` §II.1 calls not extending these with the Rizzo formers
"the one edit that makes the union sound".  Also covers the helper
monomorphization those checks made necessary — once `{Int}` stops being a
fixtype, the types that *are* one have to actually run
(`implementation_order.md` §17).
"""

from __future__ import annotations

import pytest

from gestate.declarations import classify
from gestate.helpers import HelperError
from gestate.pipeline import SubgrammarError, compile, evaluate
from gestate.syntax import parse
from gestate.types import (
    TApp, TCon, TInt, TVar, is_eqtype, is_finite_eqtype, is_fixtype,
    is_semilattice,
)


@pytest.fixture(scope="module")
def cons():
    return classify(parse("main : Int\nmain = 1\n")).cons


SET = lambda a: TApp(TCon("Set"), a)
CYCLIC8 = TApp(TCon("Cyclic"), TInt(8))
SIG_INT = TApp(TCon("Sig"), TCon("Int"))


# ── The grammars themselves ─────────────────────────────────────────────────


def test_base_eqtypes(cons):
    assert is_eqtype(TCon("Int"), cons)
    assert is_eqtype(TCon("Bool"), cons)
    assert is_eqtype(CYCLIC8, cons)


def test_the_rizzo_formers_are_in_no_subgrammar(cons):
    """§II.1: this is the whole soundness argument for the union."""
    for t in (SIG_INT, TApp(TCon("Chan"), TCon("Int")),
              TApp(TCon("ExL"), TCon("Int")), TApp(TCon("FaL"), TCon("Int"))):
        assert not is_eqtype(t, cons)
        assert not is_semilattice(t, cons)
        assert not is_fixtype(t, cons)


def test_integers_are_an_eqtype_but_not_a_finite_one(cons):
    """Footnote 2, p. 16 — and the reason `fix` over `{Int}` may diverge."""
    assert is_eqtype(TCon("Int"), cons)
    assert not is_finite_eqtype(TCon("Int"), cons)
    assert is_semilattice(SET(TCon("Int")), cons)
    assert not is_fixtype(SET(TCon("Int")), cons)


def test_cyclic_integers_are_finite(cons):
    assert is_finite_eqtype(CYCLIC8, cons)
    assert is_fixtype(SET(CYCLIC8), cons)
    assert is_fixtype(SET(TCon("Bool")), cons)


def test_bounded_is_not_yet_finite(cons):
    """`0 .. 3` names a finite range but nothing confines its values.

    `main : 0 .. 3; main = 7` evaluates to 7, so counting it finite would
    have `fix` promise a termination the runtime does not deliver.
    """
    bounded = TApp(TApp(TCon("Bounded"), TInt(0)), TInt(3))
    assert is_eqtype(bounded, cons)
    assert not is_finite_eqtype(bounded, cons)


def test_a_recursive_data_type_is_never_finite(cons):
    """`List Bool` has infinitely many values even though `Bool` does not."""
    assert is_eqtype(TApp(TCon("List"), TCon("Bool")), cons)
    assert not is_finite_eqtype(TApp(TCon("List"), TCon("Bool")), cons)
    assert is_finite_eqtype(TApp(TCon("Maybe"), TCon("Bool")), cons)


def test_a_data_type_inherits_from_its_fields(cons):
    assert not is_eqtype(TApp(TCon("Maybe"), SIG_INT), cons)


def test_int_is_not_a_semilattice(cons):
    """`for` joins one result per element, so it needs ⊥ and ∨."""
    assert not is_semilattice(TCon("Int"), cons)


def test_unknowns_are_allowed(cons):
    """A type variable might be instantiated either way; rejecting it
    would make every polymorphic set function unwritable."""
    assert is_eqtype(TVar(0), cons)
    assert is_fixtype(TVar(0), cons)


# ── Enforcement ─────────────────────────────────────────────────────────────


def test_a_set_of_signals_is_rejected():
    """§II.1's headline consequence."""
    with pytest.raises(SubgrammarError, match="set element must be an eqtype"):
        compile("main : Set (Sig Int)\nmain = {1 ::: never}\n")


def test_for_into_a_non_semilattice_is_rejected():
    """Used to type-check and then die in the G-machine."""
    with pytest.raises(SubgrammarError, match="eliminates into a semilattice"):
        compile("main : Int\nmain = for (x in {1,2}) x\n")


def test_fix_over_an_infinite_eqtype_is_rejected():
    with pytest.raises(SubgrammarError, match="not a \\*finite\\* one"):
        compile("main : Set Int\nmain = fix Box (r => {1})\n")


def test_the_fix_error_says_what_to_use_instead():
    with pytest.raises(SubgrammarError, match="Cyclic n"):
        compile("main : Set Int\nmain = fix Box (r => {1})\n")


def test_fix_over_a_fixtype_is_accepted():
    assert evaluate("main : Set (Cyclic 8)\n"
                    "main = fix Box (r => {1})\n") == "Pack{1,2} 1 Pack{0,0}"


def test_a_set_is_still_fine_at_an_infinite_eqtype():
    """Only `fix` needs finiteness; `{Int}` is a perfectly good set."""
    assert evaluate("main : Set Int\n"
                    "main = for (x in {1,2}) {x}\n").startswith("Pack")


# ── Monomorphization (§17) ──────────────────────────────────────────────────


def test_helpers_are_generated_per_element_type():
    """A `fix` resolves to the helpers of the type actually in play, not
    to `Set Int` — wherever the definition sits (`fixme.md` F9)."""
    in_main = evaluate("main : Set (Cyclic 8)\nmain = fix Box (r => {1})\n")
    in_an_sc = evaluate("f : Set (Cyclic 8)\nf = fix Box (r => {1})\n"
                        "main : Set (Cyclic 8)\nmain = f\n")

    assert "1" in in_main and "1" in in_an_sc


def test_two_set_types_in_one_program():
    """Helpers are generated per type, so both coexist."""
    assert evaluate("small : Set (Cyclic 8)\n"
                    "small = fix Box (r => {1})\n"
                    "big : Set Int\n"
                    "big = for (x in {5,6}) {x}\n"
                    "main : Set Int\nmain = big\n").startswith("Pack")


def test_a_let_bound_fixed_point_takes_its_type_from_the_use_site():
    """Datafun is a monomorphic sublanguage: generalizing here would leave
    the element type a variable and no helper to call (`errata.md` D9)."""
    assert evaluate("main : Set (Cyclic 8)\n"
                    "main = let s = fix Box (x => {1}) in s\n") \
        == "Pack{1,2} 1 Pack{0,0}"


def test_a_set_of_bool_is_buildable():
    """`{Bool}` is a fixtype, and now has a comparator to match (F11)."""
    compile("main : Set Bool\nmain = fix Box (r => {True})\n")


def test_a_set_the_helpers_cannot_order_is_reported():
    """A user data type *does* have a generated order now — by constructor
    position, then fields — so what is refused is a type with a field the
    helpers cannot order.  A `Sig` is in none of the four subgrammars, so
    the eqtype check reports it before the comparator is reached.
    """
    from gestate.helpers import ComparatorError
    from gestate.pipeline import SubgrammarError

    with pytest.raises((ComparatorError, SubgrammarError)):
        compile("D := D (Sig Int)\n\nmain : Set D\nmain = {}\n")

    # …and the ordinary case is accepted rather than refused.
    compile("C := R | G deriving Eq\n\nmain : Set C\nmain = {R}\n")


# ── Join, and what it makes writable ────────────────────────────────────────


def test_join_needs_a_semilattice():
    with pytest.raises(SubgrammarError, match="semilattice join"):
        compile("main : Int\nmain = 1 \\/ 2\n")


def test_join_and_bottom():
    """⊥ at a set type is the empty literal, so `{} \\/ e` is `e`."""
    assert evaluate("main : Set Int\nmain = {} \\/ {3}\n").startswith("Pack")
    assert evaluate("main : Set Int\nmain = {1} \\/ {2}\n").startswith("Pack")


def test_a_datalog_query_computes_the_right_set():
    """`fix (r => base \\/ step r)` — the shape every Datalog query has.

    Closing a singleton under `+k` in `Cyclic m` gives the subgroup it
    generates.  Nothing of this shape was writable before: there was no
    `∨`, so a fixed point could only be the identity on its seed.
    """
    from gestate import gmachine as G

    def elements(src):
        state = G.run(compile(src))

        def force(node):
            sub = G.GmState([G.Eval()], [node], state.globals, [],
                            now=state.now, chanCounter=state.chanCounter,
                            chans=state.chans)
            G.run(sub)
            return G._deref(sub.stack[0])

        out, node = [], force(state.stack[0])
        while isinstance(node, G.NCon) and node.args:
            out.append(force(node.args[0]).n)
            node = force(node.args[1])
        return sorted(out)

    def query(modulus, step, seed):
        return elements(
            f"reach : Box (Set (Cyclic {modulus})) -> Set (Cyclic {modulus})\n"
            f"reach bs = unbox s = bs in fix Box "
            f"(r => s \\/ (for (x in r) {{x + {step}}}))\n"
            f"main : Set (Cyclic {modulus})\n"
            f"main = reach (Box {{{seed}}})\n")

    assert query(4, 1, 1) == [0, 1, 2, 3]
    assert query(8, 2, 1) == [1, 3, 5, 7]
    assert query(9, 3, 0) == [0, 3, 6]
    assert query(8, 4, 2) == [2, 6]
