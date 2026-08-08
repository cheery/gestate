"""Tests for tuple types.

Core had ``ETuple``/``EProj`` and both Datafun subgrammars name ``A×B``, but
there was no way to *write* a tuple type: ``(Int, Int)`` was rejected by
``desugar_type`` and ``ETuple`` inferred a nullary ``Tuple2`` that threw its
components away.  A tuple type is now an ordinary applied constructor, so
unification, kind checking and the subgrammars need no special case.
"""

from __future__ import annotations

import pytest

from gestate.kindcheck import KindError
from gestate.pipeline import evaluate
from gestate.show import show_type
from gestate.types import TCon, mk_tuple, tuple_parts, is_eqtype, is_semilattice
from gestate.unify import UnifyError


def _eval(source: str) -> str:
    return evaluate(source)


# ── Writing tuple types ──────────────────────────────────────────────────────


def test_tuple_type_in_a_signature():
    assert _eval("""f : (Int, Int) -> Int
f (a, b) = a + b

main : Int
main = f (1, 2)
""") == "3"


def test_tuple_valued_definition():
    assert _eval("""p : (Int, Bool)
p = (3, True)

main : Int
main = case p of
    (n, b) -> n
""") == "3"


def test_nested_tuple_type():
    assert _eval("""f : (Int, (Int, Int)) -> Int
f (a, (b, c)) = a + b + c

main : Int
main = f (1, (2, 3))
""") == "6"


def test_triples():
    assert _eval("""f : (Int, Int, Int) -> Int
f (a, b, c) = a + b + c

main : Int
main = f (1, 2, 3)
""") == "6"


def test_tuple_inside_a_data_type():
    assert _eval("""f : List (Int, Int) -> Int
f [] = 0
f ((a, b) :: rest) = a + b

main : Int
main = f [(4, 5)]
""") == "9"


# ── Polymorphism ─────────────────────────────────────────────────────────────


def test_polymorphic_projection():
    assert _eval("""fst : (a, b) -> a
fst (x, y) = x

main : Int
main = fst (7, True)
""") == "7"


def test_polymorphic_second_projection():
    assert _eval("""snd : (a, b) -> b
snd (x, y) = y

main : Int
main = snd (True, 9)
""") == "9"


def test_tuple_used_at_two_types():
    assert _eval("""fst : (a, b) -> a
fst (x, y) = x

main : Int
main = fst (1, True) + fst (2, [3])
""") == "3"


# ── Type errors ──────────────────────────────────────────────────────────────


def test_component_type_is_checked():
    """`Tuple2` carries its components, so a wrong one is a mismatch."""
    with pytest.raises(UnifyError):
        _eval("""f : (Int, Int) -> Int
f (a, b) = a + b

main : Int
main = f (1, True)
""")


def test_width_is_checked():
    with pytest.raises(UnifyError):
        _eval("""f : (Int, Int) -> Int
f (a, b) = a + b

main : Int
main = f (1, 2, 3)
""")


def test_one_component_tuple_type_is_rejected():
    from gestate.declarations import DeclError

    # `(Int)` is just `Int`; a *tuple* needs at least two components, and a
    # too-wide one has no constructor.
    with pytest.raises((DeclError, KindError)):
        _eval("""f : (Int, Int, Int, Int, Int, Int, Int, Int, Int) -> Int
f x = 1

main : Int
main = 1
""")


# ── Rendering ────────────────────────────────────────────────────────────────


def test_tuple_types_render_as_source():
    t = mk_tuple([TCon("Int"), TCon("Bool")])
    assert show_type(t) == "(Int, Bool)"
    assert show_type(t, paren=True) == "(Int, Bool)"


def test_tuple_parts_round_trips():
    parts = [TCon("Int"), TCon("Bool"), TCon("Int")]
    assert tuple_parts(mk_tuple(parts)) == parts
    assert tuple_parts(TCon("Int")) is None


# ── Datafun subgrammars (fig. 2.1: `A×B`, `L×M`) ─────────────────────────────


def test_a_product_of_eqtypes_is_an_eqtype():
    assert is_eqtype(mk_tuple([TCon("Int"), TCon("Int")]))


def test_a_product_containing_a_signal_is_not_an_eqtype():
    from gestate.types import TApp

    assert not is_eqtype(mk_tuple([TCon("Int"), TApp(TCon("Sig"), TCon("Int"))]))


def test_a_product_of_semilattices_is_a_semilattice():
    from gestate.types import TApp

    sets = TApp(TCon("Set"), TCon("Int"))
    assert is_semilattice(mk_tuple([sets, sets]))
    assert not is_semilattice(mk_tuple([sets, TCon("Int")]))
