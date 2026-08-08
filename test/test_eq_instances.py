"""Structural `Eq`/`Ord` instances (`fixme.md` F50).

`Eq Int` and `Ord Int` are compiler-provided and bottom out in the integer
primitives; every other instance is ordinary prelude code compiled through
the same pipeline.  Getting them to work took three fixes, each of which
has its own test below:

* an instance whose context reproduced its goal ran resolution to the depth
  cap instead of letting the base case claim it;
* a scheme's substitution was applied to its type but not to its
  constraints, so a constrained supercombinator called at `Bool` still
  emitted a constraint on the signature's original variable — which nothing
  could bind, so it defaulted to `Int`;
* nested `case`s shared subject names (F53), which corrupted every
  multi-branch instance body.
"""

from __future__ import annotations

from gestate.pipeline import evaluate


def _bool(expr: str) -> str:
    return evaluate(f"main : Int\nmain = case {expr} of\n"
                    f"    True -> 1\n    False -> 0\n")


# ── Base instances ───────────────────────────────────────────────────────────


def test_eq_int():
    assert _bool("1 == 1") == "1"
    assert _bool("1 == 2") == "0"


def test_eq_bool():
    assert _bool("True == True") == "1"
    assert _bool("True == False") == "0"


def test_ord_bool():
    assert _bool("False < True") == "1"
    assert _bool("True < False") == "0"


# ── Eq (List a) ──────────────────────────────────────────────────────────────


def test_eq_list_of_int():
    assert _bool("[1, 2] == [1, 2]") == "1"
    assert _bool("[1, 2] == [1, 3]") == "0"


def test_eq_list_lengths_differ():
    assert _bool("[1] == [1, 2]") == "0"
    assert _bool("[1, 2] == [1]") == "0"


def test_eq_empty_lists():
    assert _bool("[] == []") == "1"


def test_eq_list_of_bool():
    """The element dictionary must be `Eq Bool`, not the defaulted `Eq Int`."""
    assert _bool("[True, False] == [True, False]") == "1"
    assert _bool("[True, False] == [True, True]") == "0"


def test_eq_nested_lists():
    """Two levels of the same generic instance, applied to itself."""
    assert _bool("[[1, 2], [3]] == [[1, 2], [3]]") == "1"
    assert _bool("[[1, 2], [3]] == [[1, 2], [4]]") == "0"


def test_not_equal_on_lists():
    assert _bool("[[1]] /= [[2]]") == "1"
    assert _bool("[[1]] /= [[1]]") == "0"


# ── Eq (Maybe a) and Eq (a, b) ───────────────────────────────────────────────


def test_eq_maybe():
    assert _bool("Just 3 == Just 3") == "1"
    assert _bool("Just 3 == Just 4") == "0"
    assert _bool("Just 3 == Nothing") == "0"
    assert _bool("Nothing == Nothing") == "1"


def test_eq_maybe_of_bool():
    assert _bool("Just True == Just True") == "1"
    assert _bool("Just True == Just False") == "0"


def test_eq_tuple():
    assert _bool("(1, True) == (1, True)") == "1"
    assert _bool("(1, True) == (1, False)") == "0"


def test_instances_compose():
    assert _bool("Just [1, 2] == Just [1, 2]") == "1"
    assert _bool("[Just 1, Nothing] == [Just 1, Nothing]") == "1"
    assert _bool("[(1, True)] == [(1, True)]") == "1"
    assert _bool("([1], [2]) == ([1], [2])") == "1"


# ── elem: a recursive supercombinator with a class context ───────────────────


def test_elem_at_int():
    assert _bool("elem 3 [1, 2, 3]") == "1"
    assert _bool("elem 9 [1, 2, 3]") == "0"


def test_elem_at_bool():
    """The recursive call must pass the SC's own dictionary parameter on."""
    assert _bool("elem False [True, False]") == "1"
    assert _bool("elem False [True, True]") == "0"


def test_elem_at_a_structural_type():
    assert _bool("elem [1, 2] [[3], [1, 2]]") == "1"
    assert _bool("elem (1, True) [(2, False), (1, True)]") == "1"


# ── Two element types in one supercombinator ─────────────────────────────────


def test_two_instance_types_in_one_body():
    assert evaluate("""both : Int
both = case [1] == [1] of
    True -> case True == True of
        True -> 1
        False -> 0
    False -> 0

main : Int
main = both
""") == "1"


# ── A user-declared class of the same shape ──────────────────────────────────


def test_user_generic_instance_over_its_own_base():
    assert evaluate("""class C a where
    f : a -> a -> Bool

instance C Int where
    f x y = x == y

instance (C a) => C (List a) where
    f xs ys = case xs of
        [] -> True
        x :: rest -> case ys of
            [] -> False
            z :: zs -> f x z

main : Int
main = case f [5] [1] of
    True -> 1
    False -> 0
""") == "0"


def test_constrained_recursive_supercombinator_at_a_non_default_type():
    assert evaluate("""myElem : (Eq a) => a -> List a -> Bool
myElem y xs = case xs of
    [] -> False
    x :: rest -> case x == y of
        True -> True
        False -> myElem y rest

main : Int
main = case myElem False [True, False] of
    True -> 1
    False -> 0
""") == "1"
