"""Tests for superclass constraints (`spec/typeclasses.md`, `fixme.md` F33).

`class Eq a => Ord a` is discharged by *closing* every context under its
superclasses rather than by storing a superclass dictionary inside the
subclass's: `f : (Ord a) => …` takes an `Eq a` dictionary too, and a caller
resolves the extra predicate exactly as it resolves the original.  The
dictionary layout is therefore unchanged.
"""

from __future__ import annotations

import pytest

from gestate.declarations import DeclError, close_context, ClassInfo
from gestate.pipeline import compile, evaluate
from gestate.types import Predicate, TCon, TVar


def _eval(source: str) -> str:
    return evaluate(source)


# ── Context closure ──────────────────────────────────────────────────────────


def test_close_context_adds_superclasses():
    classes = {
        "Ord": ClassInfo("Ord", ["a"], {}, superclasses=["Eq"]),
        "Eq": ClassInfo("Eq", ["a"], {}),
    }
    closed = close_context([Predicate("Ord", TVar(1))], classes)
    assert [(p.class_name, p.type_) for p in closed] == [
        ("Ord", TVar(1)), ("Eq", TVar(1))]


def test_close_context_is_transitive():
    classes = {
        "C": ClassInfo("C", ["a"], {}, superclasses=["B"]),
        "B": ClassInfo("B", ["a"], {}, superclasses=["A"]),
        "A": ClassInfo("A", ["a"], {}),
    }
    closed = close_context([Predicate("C", TVar(1))], classes)
    assert [p.class_name for p in closed] == ["C", "B", "A"]


def test_close_context_terminates_on_a_cycle():
    classes = {
        "P": ClassInfo("P", ["a"], {}, superclasses=["Q"]),
        "Q": ClassInfo("Q", ["a"], {}, superclasses=["P"]),
    }
    closed = close_context([Predicate("P", TVar(1))], classes)
    assert sorted(p.class_name for p in closed) == ["P", "Q"]


def test_close_context_does_not_duplicate():
    classes = {
        "Ord": ClassInfo("Ord", ["a"], {}, superclasses=["Eq"]),
        "Eq": ClassInfo("Eq", ["a"], {}),
    }
    closed = close_context(
        [Predicate("Ord", TCon("Int")), Predicate("Eq", TCon("Int"))], classes)
    assert len(closed) == 2


# ── Ord implies Eq ───────────────────────────────────────────────────────────


def test_ord_context_grants_eq():
    """An `(Ord a)` context may use `==`, because `Ord`'s superclass is `Eq`."""
    assert _eval("""cmp : (Ord a) => a -> a -> Int
cmp x y = case x == y of
    True -> 0
    False -> case x < y of
        True -> 1
        False -> 2

main : Int
main = cmp 3 5
""") == "1"


def test_ord_context_at_equal_arguments():
    assert _eval("""cmp : (Ord a) => a -> a -> Int
cmp x y = case x == y of
    True -> 0
    False -> 1

main : Int
main = cmp 4 4
""") == "0"


# ── User-declared superclasses ───────────────────────────────────────────────


def test_user_declared_superclass():
    assert _eval("""class Eq a => Sized a where
    size : a -> Int

instance Sized Int where
    size n = n

sameSize : (Sized a) => a -> a -> Int
sameSize x y = case x == y of
    True -> size x
    False -> 0

main : Int
main = sameSize 7 7
""") == "7"


def test_parenthesized_superclass_context():
    assert _eval("""class (Eq a) => Tagged a where
    tag : a -> Int

instance Tagged Int where
    tag n = n + 1

main : Int
main = tag 4
""") == "5"


def test_superclass_method_reachable_through_two_levels():
    assert _eval("""class Eq a => Mid a where
    mid : a -> Int

class Mid a => Top a where
    top : a -> Int

instance Mid Int where
    mid n = n

instance Top Int where
    top n = mid n + 1

use : (Top a) => a -> Int
use x = case x == x of
    True -> top x
    False -> 0

main : Int
main = use 5
""") == "6"


# ── Rejections ───────────────────────────────────────────────────────────────


def test_superclass_must_constrain_the_class_parameter():
    with pytest.raises(DeclError, match="own type parameter"):
        compile("""class (Eq Int) => Bad a where
    bad : a -> Int

main : Int
main = 1
""")
