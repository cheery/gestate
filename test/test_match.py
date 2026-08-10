"""Tests for the pattern-match compiler (``gestate/match.py``).

Every case here was either miscompiled or rejected before the matrix
algorithm replaced the one-level ``_desugar_pattern``.
"""

from __future__ import annotations

import pytest

from gestate.desugar import DesugarError
from gestate.exhaust import ExhaustError
from gestate.pipeline import evaluate


def _eval(source: str) -> str:
    return evaluate(source, prelude=True)


# ── Fixed-length list patterns ───────────────────────────────────────────────
#
# `[x]` used to compile to `Cons x _fresh` with the tail never tested, so it
# matched *any* non-empty list — and collided with `y :: ys`.


def test_singleton_pattern_rejects_longer_list():
    assert _eval("""main : Int
main = case [1, 2, 3] of
    [x] -> x
    [] -> 99
    y :: ys -> 5
""") == "5"


def test_singleton_pattern_matches_singleton():
    assert _eval("""main : Int
main = case [7] of
    [x] -> x
    [] -> 99
    y :: ys -> 5
""") == "7"


def test_two_element_list_pattern():
    assert _eval("""main : Int
main = case [1, 2] of
    [x, y] -> x + y
    [] -> 0
    z :: zs -> 100
""") == "3"


def test_singleton_and_cons_are_distinguishable():
    """Both used to desugar to a bare `Cons` alt, so one was 'redundant'."""
    assert _eval("""f : List Int -> Int
f ys = case ys of
    [] -> 0
    [x] -> 1
    y :: rest -> 2

main : Int
main = f [1, 2, 3]
""") == "2"


# ── List tail syntax ─────────────────────────────────────────────────────────
#
# `[a, b | tail]` parsed on the pattern side but not on the expression side:
# `_is_infix_op` claimed `|`, so `_parse_val` swallowed it and the list came
# back one element long holding `1 | xs`.


def test_list_tail_in_expression():
    assert _eval("main : Int\nmain = length [1, 2 | [3, 4]]\n") == "4"


def test_single_item_list_tail_in_expression():
    assert _eval("main : Int\nmain = length [1 | [2, 3]]\n") == "3"


def test_list_tail_over_a_variable():
    assert _eval("""f : List Int -> Int
f xs = length [0 | xs]

main : Int
main = f [1, 2]
""") == "3"


def test_list_tail_in_pattern():
    assert _eval("""f : List Int -> Int
f [x | rest] = x
f [] = 0

main : Int
main = f [4, 5]
""") == "4"


# ── Nested patterns ──────────────────────────────────────────────────────────
#
# Sub-pattern *tags* used to be discarded, keeping only the names: `Just x ::
# rest` bound `x` to the whole head, and the binder list stopped matching the
# constructor's arity (an `IndexError` out of the G-machine).


def test_nested_constructor_pattern():
    assert _eval("""f : Maybe (Maybe Int) -> Int
f m = case m of
    Just (Just x) -> x
    Just Nothing -> 1
    Nothing -> 2

main : Int
main = f (Just (Just 42))
""") == "42"


def test_constructor_inside_cons_pattern():
    assert _eval("""f : List (Maybe Int) -> Int
f ys = case ys of
    Just x :: rest -> x
    Nothing :: rest -> 0
    [] -> 99

main : Int
main = f [Just 7, Just 8]
""") == "7"


def test_nested_pattern_falls_through_to_later_alternative():
    assert _eval("""f : List (Maybe Int) -> Int
f ys = case ys of
    Just x :: rest -> x
    Nothing :: rest -> 0
    [] -> 99

main : Int
main = f [Nothing, Just 8]
""") == "0"


def test_list_inside_list_pattern():
    assert _eval("""f : List (List Int) -> Int
f ys = case ys of
    (a :: as) :: rest -> a
    [] :: rest -> 0
    [] -> 99

main : Int
main = f [[5, 6], [7]]
""") == "5"


def test_deeply_nested_pattern():
    assert _eval("""f : Maybe (List (Maybe Int)) -> Int
f m = case m of
    Just (Just x :: rest) -> x
    Just (Nothing :: rest) -> 1
    Just [] -> 2
    Nothing -> 3

main : Int
main = f (Just [Just 9])
""") == "9"


# ── Multi-argument equations ─────────────────────────────────────────────────


def test_multi_argument_pattern_equations():
    assert _eval("""f : Int -> List Int -> Int
f n [] = n
f n (x :: xs) = x + n

main : Int
main = f 10 [5]
""") == "15"


def test_multi_argument_dispatches_on_both_columns():
    assert _eval("""f : Maybe Int -> Maybe Int -> Int
f Nothing Nothing = 0
f (Just x) Nothing = x
f Nothing (Just y) = y
f (Just x) (Just y) = x + y

main : Int
main = f (Just 3) (Just 4)
""") == "7"


def test_parameter_list_takes_atoms():
    """`f Nothing (x :: xs)` is two parameters, not one applied constructor."""
    assert _eval("""f : Maybe Int -> List Int -> Int
f Nothing (x :: xs) = x
f Nothing [] = 0
f (Just n) ys = n

main : Int
main = f Nothing [4, 5]
""") == "4"


# ── Literal patterns ─────────────────────────────────────────────────────────


def test_literal_patterns():
    src = """f : Int -> Int
f 0 = 100
f 1 = 200
f n = n

main : Int
main = f %s
"""
    assert _eval(src % "0") == "100"
    assert _eval(src % "1") == "200"
    assert _eval(src % "7") == "7"


def test_literal_pattern_in_case():
    assert _eval("""main : Int
main = case 3 of
    0 -> 10
    3 -> 30
    n -> 99
""") == "30"


def test_a_string_pattern_is_a_list_pattern():
    """`String` is `List Char`, so a string literal *pattern* is the
    list of its characters — sugar, desugared in the parser.  It used
    to be refused ("only integer literal patterns"), which meant
    matching a label had to be written `case s == "verse" of True ->`,
    a comparison where the author meant a case.

    A `Char` is integer-*represented* but its own type, so the
    elements compare through `ord`; integer patterns are untouched.
    """
    assert _eval('''f : String -> Int
f s = case s of
    "" -> 1
    "ab" -> 2
    "abc" -> 3
    _ -> 4

main : String
main = show (f "abc" * 1000 + f "ab" * 100 + f "" * 10 + f "z")
''') == "3214"


def test_a_float_literal_pattern_is_still_rejected():
    """The refusal that remains, and it is honest: an exact test on a
    float is a question about bits wearing the clothes of a value."""
    with pytest.raises(DesugarError, match="integer literal"):
        evaluate("f : Float -> Int\nf 1.5 = 1\nf n = 2\n"
                 "\nmain : Int\nmain = f 1.5\n")


# ── Variables and wildcards in alternatives ──────────────────────────────────


def test_wildcard_alternative():
    assert _eval("""f : Maybe Int -> Int
f m = case m of
    Just x -> x
    _ -> 0

main : Int
main = f Nothing
""") == "0"


def test_variable_catchall_alternative():
    assert _eval("""f : Maybe Int -> Int
f m = case m of
    Just x -> x
    other -> 0

main : Int
main = f Nothing
""") == "0"


def test_catchall_binds_the_scrutinee():
    assert _eval("""f : List Int -> Int
f xs = case xs of
    [] -> 0
    ys -> length ys

main : Int
main = f [1, 2, 3]
""") == "3"


# ── Failure ──────────────────────────────────────────────────────────────────


def test_unmatched_pattern_is_rejected_at_compile_time():
    """`Int` has infinitely many values, so a literal match needs a catch-all."""
    with pytest.raises(ExhaustError, match="non-exhaustive"):
        _eval("""f : Int -> Int
f 0 = 1

main : Int
main = f 5
""")


# ── Errors ───────────────────────────────────────────────────────────────────


def test_constructor_arity_mismatch_is_reported():
    with pytest.raises(DesugarError, match="argument"):
        _eval("""f : Maybe Int -> Int
f (Just x y) = x

main : Int
main = f (Just 1)
""")


def test_unknown_constructor_is_reported():
    with pytest.raises(DesugarError, match="unknown constructor"):
        _eval("""f : Maybe Int -> Int
f (Nope x) = x

main : Int
main = f (Just 1)
""")


def test_equations_must_agree_on_arity():
    with pytest.raises(DesugarError, match="same number of parameters"):
        _eval("""f : Int -> Int -> Int
f x = x
f x y = y

main : Int
main = f 1 2
""")


# ── Sharing ──────────────────────────────────────────────────────────────────


def test_failure_continuation_is_shared_not_copied():
    """Each uncovered constructor jumps to one `let`-bound thunk.

    Without sharing the tree is exponential in the number of columns; this
    program has 2^4 fall-through positions and would blow up.
    """
    assert _eval("""f : Maybe Int -> Maybe Int -> Maybe Int -> Maybe Int -> Int
f (Just a) (Just b) (Just c) (Just d) = a + b + c + d
f x y z w = 0

main : Int
main = f (Just 1) (Just 2) (Just 3) (Just 4)
""") == "10"
