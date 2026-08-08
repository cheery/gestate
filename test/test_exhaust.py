"""Tests for exhaustiveness and redundancy checking (``gestate/exhaust.py``).

The check runs on surface patterns via Maranget's usefulness algorithm, so
it sees nesting, literals and wildcards — none of which the previous
tag-counting version could represent.
"""

from __future__ import annotations

import pytest

from gestate.exhaust import ExhaustError
from gestate.pipeline import compile


def _compile(source: str):
    return compile(source, prelude=True)


def _error(source: str) -> str:
    with pytest.raises(ExhaustError) as exc:
        _compile(source)
    return str(exc.value)


# ── Exhaustiveness ───────────────────────────────────────────────────────────


def test_missing_nil_alternative():
    assert "`[]`" in _error("""main : Int
main = case [1, 2] of
    x :: xs -> x
""")


def test_missing_nested_alternative():
    """A gap one level down — invisible to a check that counts top-level tags."""
    assert "`Just Nothing`" in _error("""f : Maybe (Maybe Int) -> Int
f m = case m of
    Just (Just x) -> x
    Nothing -> 0

main : Int
main = f Nothing
""")


def test_missing_column_combination():
    """Two arguments, one uncovered combination."""
    msg = _error("""f : Maybe Int -> Maybe Int -> Int
f Nothing Nothing = 0
f (Just x) Nothing = x
f (Just x) (Just y) = x + y

main : Int
main = f Nothing Nothing
""")
    assert "Nothing (Just _)" in msg


def test_missing_longer_list():
    assert "`_ :: _ :: _`" in _error("""f : List Int -> Int
f [] = 0
f [x] = x

main : Int
main = f []
""")


def test_integers_need_a_catchall():
    """`Int` has no finite constructor set, so literals never exhaust it."""
    assert "non-exhaustive" in _error("""f : Int -> Int
f 0 = 1
f 1 = 2

main : Int
main = f 0
""")


# ── Accepted programs ────────────────────────────────────────────────────────


def test_all_combinations_is_exhaustive():
    _compile("""f : Maybe Int -> Maybe Int -> Int
f Nothing Nothing = 0
f (Just x) Nothing = x
f Nothing (Just y) = y
f (Just x) (Just y) = x + y

main : Int
main = f (Just 1) (Just 2)
""")


def test_list_length_cases_are_exhaustive():
    _compile("""f : List Int -> Int
f [] = 0
f [x] = x
f (x :: y :: rest) = x + y

main : Int
main = f [1, 2, 3]
""")


def test_catchall_makes_literals_exhaustive():
    _compile("""f : Int -> Int
f 0 = 1
f n = n

main : Int
main = f 3
""")


def test_wildcard_is_exhaustive():
    _compile("""f : Maybe Int -> Int
f m = case m of
    Just x -> x
    _ -> 0

main : Int
main = f Nothing
""")


# ── Redundancy ───────────────────────────────────────────────────────────────


def test_duplicate_alternative_is_unreachable():
    assert "unreachable" in _error("""f : Maybe Int -> Int
f m = case m of
    Just x -> x
    Nothing -> 0
    Just y -> 1

main : Int
main = f Nothing
""")


def test_alternative_after_wildcard_is_unreachable():
    assert "unreachable" in _error("""f : Maybe Int -> Int
f m = case m of
    _ -> 0
    Just x -> x

main : Int
main = f Nothing
""")


def test_nested_pattern_subsumption():
    """`Just _` covers `Just (Just _)`, one level down."""
    assert "unreachable" in _error("""f : Maybe (Maybe Int) -> Int
f m = case m of
    Just y -> 0
    Just (Just x) -> x
    Nothing -> 1

main : Int
main = f Nothing
""")


def test_specific_before_general_is_fine():
    _compile("""f : Maybe (Maybe Int) -> Int
f m = case m of
    Just (Just x) -> x
    Just y -> 0
    Nothing -> 1

main : Int
main = f Nothing
""")


# ── Instance methods ─────────────────────────────────────────────────────────


def test_instance_method_bodies_are_checked():
    msg = _error("""class Size a where
    size : a -> Int

instance Size (List Int) where
    size xs = case xs of
        y :: ys -> 1

main : Int
main = size [1]
""")
    assert "non-exhaustive" in msg
