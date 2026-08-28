"""`deriving (Show, Eq)` on a data declaration.

The instances are built as *surface* AST and classified alongside the
declared ones, so they go through inference, constraint solving, dictionary
passing and code generation on exactly the path a hand-written instance
takes.  That is what makes a parameterised type work without a special
case: `Wrap a := W a deriving Show` derives `(Show a) => Show (Wrap a)`,
and the field's dictionary is threaded like any other.

This file is `fixme.md` F54's gate, with `test_strings.py`.
"""

from __future__ import annotations

import pytest

from gestate.declarations import DeclError
from gestate.pipeline import evaluate

COLOR = "Color := Red | Green | Blue deriving (Show, Eq)\n\n"
TREE = "Tree := Leaf | Node Tree Int Tree deriving (Show, Eq)\n\n"


def _str(decls: str, expr: str) -> str:
    return evaluate(f"{decls}main : String\nmain = {expr}\n")


def _bool(decls: str, expr: str) -> str:
    return evaluate(f"{decls}main : Int\nmain = case {expr} of\n"
                    f"    True -> 1\n    False -> 0\n")


# ── Derived Show ─────────────────────────────────────────────────────────────


def test_show_a_nullary_constructor():
    assert _str(COLOR, "show Green") == "Green"


def test_show_every_constructor():
    assert _str(COLOR, "show Red") == "Red"
    assert _str(COLOR, "show Blue") == "Blue"


def test_show_a_constructor_with_fields():
    assert _str("Point := P Int Int deriving Show\n\n", "show (P 1 2)") == "P 1 2"


def test_show_a_parameterised_type():
    assert _str("Wrap a := W a deriving Show\n\n", "show (W 5)") == "W 5"


def test_show_a_parameterised_type_at_a_structural_argument():
    assert _str("Wrap a := W a deriving Show\n\n",
                "show (W [1, 2])") == "W [1, 2]"


def test_show_a_recursive_type():
    assert _str(TREE, "show (Node Leaf 3 Leaf)") == "Node Leaf 3 Leaf"


def test_derived_show_composes_with_prelude_instances():
    assert _str(COLOR, "show [Red, Green]") == "[Red, Green]"
    assert _str(COLOR, "show (Just Blue)") == "Just Blue"
    assert _str(COLOR, "show (Red, 1)") == "(Red, 1)"


# ── Derived Eq ───────────────────────────────────────────────────────────────


def test_eq_on_nullary_constructors():
    assert _bool(COLOR, "Red == Red") == "1"
    assert _bool(COLOR, "Red == Green") == "0"


def test_eq_compares_fields():
    decls = "Point := P Int Int deriving Eq\n\n"
    assert _bool(decls, "P 1 2 == P 1 2") == "1"
    assert _bool(decls, "P 1 2 == P 1 3") == "0"
    assert _bool(decls, "P 1 2 == P 9 2") == "0"


def test_eq_on_a_single_constructor_type():
    """With one constructor every value matches, so no catch-all is emitted."""
    decls = "Box2 := B Int deriving Eq\n\n"
    assert _bool(decls, "B 1 == B 1") == "1"
    assert _bool(decls, "B 1 == B 2") == "0"


def test_eq_on_a_recursive_type():
    assert _bool(TREE, "Node Leaf 3 Leaf == Node Leaf 3 Leaf") == "1"
    assert _bool(TREE, "Node Leaf 3 Leaf == Node Leaf 4 Leaf") == "0"
    assert _bool(TREE, "Node Leaf 3 Leaf == Leaf") == "0"


def test_eq_on_a_parameterised_type():
    decls = "Wrap a := W a deriving Eq\n\n"
    assert _bool(decls, "W [1, 2] == W [1, 2]") == "1"
    assert _bool(decls, "W [1, 2] == W [1, 3]") == "0"


def test_not_equal_is_derived_too():
    assert _bool(COLOR, "Red /= Green") == "1"
    assert _bool(COLOR, "Red /= Red") == "0"


def test_a_derived_eq_satisfies_a_class_context():
    assert _bool(COLOR, "elem Green [Red, Green]") == "1"
    assert _bool(COLOR, "elem Blue [Red, Green]") == "0"


def test_derived_eq_composes_with_prelude_instances():
    assert _bool(COLOR, "[Red] == [Red]") == "1"
    assert _bool(COLOR, "Just Red == Just Green") == "0"


# ── Syntax ───────────────────────────────────────────────────────────────────


def test_deriving_without_parentheses():
    assert _str("Color := Red | Green deriving Show\n\n", "show Red") == "Red"


def test_deriving_is_optional():
    assert evaluate("Color := Red | Green\n\nmain : Int\nmain = 1\n") == "1"


def test_deriving_a_class_that_cannot_be_derived():
    # `Ord` used to be the example here and is derivable now; `Num` is not,
    # and could not sensibly be — there is no positional reading of `+`.
    with pytest.raises(DeclError, match="cannot derive 'Num'"):
        evaluate("Color := Red deriving Num\n\nmain : Int\nmain = 1\n")


def test_a_derived_instance_is_a_real_instance():
    """It must clash with a hand-written one, like any other duplicate."""
    from gestate.coherence import CoherenceError

    with pytest.raises(CoherenceError):
        evaluate("""Color := Red | Green deriving Eq

instance Eq Color where
    (==) a b = True
    (/=) a b = False

main : Int
main = 1
""")
