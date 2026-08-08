"""Tests for the strict integer primitives and nested applications.

The primitives (``prim_add_int`` and friends) evaluate their arguments
through the ordinary ``Eval``/``Unwind`` machinery, so an argument may be
an arbitrary thunk — including another call to the same primitive.
"""

from __future__ import annotations

import pytest

from gestate.gmachine import GmError
from gestate.pipeline import evaluate


def _int(source: str) -> int:
    return int(evaluate(source))


# ── Nested applications ──────────────────────────────────────────────────────


def test_nested_primitive_application():
    assert _int("main : Int\nmain = prim_add_int (prim_add_int 5 1) 1\n") == 7


def test_nested_operator_application():
    assert _int("main : Int\nmain = (5 + 1) + 1\n") == 7


def test_nested_user_function_application():
    src = (
        "inc : Int -> Int\n"
        "inc x = x + 1\n\n"
        "main : Int\n"
        "main = inc (inc 5)\n"
    )
    assert _int(src) == 7


def test_function_argument_applied_twice():
    src = (
        "inc : Int -> Int\n"
        "inc x = x + 1\n\n"
        "twice : (Int -> Int) -> Int -> Int\n"
        "twice f x = f (f x)\n\n"
        "main : Int\n"
        "main = twice inc 5\n"
    )
    assert _int(src) == 7


def test_deeply_nested_arithmetic():
    assert _int("main : Int\nmain = ((1 + 2) * (3 + 4)) - 1\n") == 20


def test_arithmetic_in_a_let_binding():
    assert _int("main : Int\nmain = let x = 2 + 3 in x * x\n") == 25


# ── Operand order (non-commutative ops) ──────────────────────────────────────


def test_subtraction_operand_order():
    assert _int("main : Int\nmain = 10 - 3\n") == 7


def test_modulo_operand_order():
    assert _int("main : Int\nmain = prim_mod_int 10 3\n") == 1


# ── Recursion through the primitives ─────────────────────────────────────────


def test_factorial():
    src = (
        "fact : Int -> Int\n"
        "fact n = case n == 0 of\n"
        "  True -> 1\n"
        "  False -> n * fact (n - 1)\n\n"
        "main : Int\n"
        "main = fact 5\n"
    )
    assert _int(src) == 120


def test_fibonacci():
    src = (
        "fib : Int -> Int\n"
        "fib n = case n < 2 of\n"
        "  True -> n\n"
        "  False -> fib (n - 1) + fib (n - 2)\n\n"
        "main : Int\n"
        "main = fib 10\n"
    )
    assert _int(src) == 55


# ── Comparisons ──────────────────────────────────────────────────────────────


def _bool(expr: str) -> int:
    """Evaluate a Bool-valued expression as 1 (True) or 0 (False)."""
    src = (
        "main : Int\n"
        f"main = case {expr} of\n"
        "  True -> 1\n"
        "  False -> 0\n"
    )
    return _int(src)


def test_less_than():
    assert _bool("3 < 5") == 1
    assert _bool("5 < 3") == 0


def test_equality_of_nested_expressions():
    assert _bool("(1 + 1) == 2") == 1
    assert _bool("(1 + 1) == 3") == 0


# ── Laziness is preserved ────────────────────────────────────────────────────


def test_unused_argument_is_not_forced():
    src = (
        "const : Int -> Int -> Int\n"
        "const x y = x\n\n"
        "main : Int\n"
        "main = const 1 (prim_mod_int 1 0)\n"
    )
    assert _int(src) == 1


def test_division_by_zero_is_reported():
    with pytest.raises(GmError, match="division by zero"):
        evaluate("main : Int\nmain = prim_mod_int 1 0\n")


def test_cyclic_arithmetic_wraps():
    """Every operation returns to the range, not only `fromInteger`.

    The synthetic `Num` instance used to define `fromInteger` alone, so
    `+`/`-`/`*` projected an undefined dictionary slot — which held a
    number, and `Unwind` on a number ignores the spine, so `x + y` quietly
    evaluated to the placeholder.
    """
    assert evaluate("main : Cyclic 4\nmain = 1 + 1\n") == "2"
    assert evaluate("main : Cyclic 4\nmain = 3 + 3\n") == "2"
    assert evaluate("main : Cyclic 4\nmain = 2 * 3\n") == "2"
    assert evaluate("main : Cyclic 4\nmain = 7\n") == "3"


def test_integer_arithmetic_does_not_wrap():
    assert evaluate("main : Int\nmain = 3 + 3\n") == "6"
