"""Strings, `Char`, and the `Show` class.

`String` is a built-in alias for `List Char`, and `Char` is a code point
represented as an integer.  Making it an alias rather than a primitive is
what lets every list function, `Eq (List a)` and `Show (List a)` apply to
strings without a second implementation.

This file is `fixme.md` F54's gate, with `test_deriving.py`.
"""

from __future__ import annotations

import pytest

from gestate.pipeline import evaluate


def _str(expr: str) -> str:
    return evaluate(f"main : String\nmain = {expr}\n")


def _int(expr: str) -> str:
    return evaluate(f"main : Int\nmain = {expr}\n")


def _bool(expr: str) -> str:
    return evaluate(f"main : Int\nmain = case {expr} of\n"
                    f"    True -> 1\n    False -> 0\n")


# ── String literals ──────────────────────────────────────────────────────────


def test_string_literal_renders_as_text():
    assert _str('"hi there"') == "hi there"


def test_empty_string():
    assert _str('""') == ""


def test_escapes():
    assert _str('"a\\tb\\nc"') == "a\tb\nc"
    assert _str('"say \\"hi\\""') == 'say "hi"'


def test_a_string_is_a_list():
    assert _int('length "hello"') == "5"


def test_list_functions_apply_to_strings():
    assert _str('append "ab" "cd"') == "abcd"
    assert _str('reverse "abc"') == "cba"
    assert _str('join ["a", "bc"]') == "abc"


def test_a_computed_string_is_forced_for_rendering():
    """`run` stops at the head; the spine has to be forced to print it."""
    assert _str('append (reverse "cb") (join ["d", "e"])') == "bcde"


def test_string_equality_comes_from_eq_list():
    assert _bool('"ab" == "ab"') == "1"
    assert _bool('"ab" == "ac"') == "0"
    assert _bool('"ab" == "abc"') == "0"


def test_a_list_of_int_is_not_rendered_as_text():
    """Only a `String`-typed result decodes; `List Int` keeps its structure."""
    out = evaluate("main : List Int\nmain = [104, 105]\n")
    assert "Pack" in out


# ── Char ─────────────────────────────────────────────────────────────────────


def test_chr_and_ord_are_inverse():
    assert _int("ord (chr 65)") == "65"


def test_chr_builds_a_string():
    assert _str("[chr 104, chr 105]") == "hi"


def test_char_is_not_int():
    """The two share a representation but not a type."""
    from gestate.constraint import ConstraintError
    from gestate.unify import UnifyError

    with pytest.raises((ConstraintError, UnifyError)):
        _int('length (filter (c => c == 97) "abc")')


# ── Primes in identifiers ────────────────────────────────────────────────────


def test_prime_is_an_identifier_character():
    assert _int("f 4\n\nf : Int -> Int\nf x' = x' + 1") == "5"


def test_prime_on_a_global_name():
    assert evaluate("inc' : Int -> Int\ninc' n = n + 1\n\n"
                    "main : Int\nmain = inc' 6\n") == "7"


def test_double_prime():
    assert evaluate("g : Int -> Int\ng x'' = x''\n\n"
                    "main : Int\nmain = g 3\n") == "3"


# ── Show ─────────────────────────────────────────────────────────────────────


def test_show_int():
    assert _str("show 42") == "42"
    assert _str("show 0") == "0"
    assert _str("show 1234567") == "1234567"


def test_show_negative_int():
    assert _str("show (0 - 15)") == "-15"


def test_show_bool():
    assert _str("show True") == "True"
    assert _str("show False") == "False"


def test_show_list():
    assert _str("show [1, 2, 3]") == "[1, 2, 3]"
    assert _str("show ([] : List Int)") == "[]"


def test_show_nested_list():
    assert _str("show [[1], [2, 3]]") == "[[1], [2, 3]]"


def test_show_maybe():
    assert _str("show (Just 5)") == "Just 5"
    assert _str("show (Nothing : Maybe Int)") == "Nothing"


def test_show_tuple():
    assert _str("show (1, True)") == "(1, True)"


def test_show_instances_compose():
    assert _str("show [Just 1, Nothing]") == "[Just 1, Nothing]"
    assert _str("show (Just [1, 2])") == "Just [1, 2]"
    assert _str("show [(1, True)]") == "[(1, True)]"


def test_show_results_concatenate():
    assert _str("append (show 1) (show 2)") == "12"


def test_show_char():
    assert _str("show (chr 65)") == "A"


# ── Defaulting ───────────────────────────────────────────────────────────────


def test_an_ambiguous_variable_defaults_across_all_its_constraints():
    """`show 42` leaves `(Num a, Show a)`; both must settle on `Int`.

    Defaulting one predicate at a time let `Show a` pick whichever `Show`
    instance was declared first, and `show 42` rendered as a character.
    """
    assert _str("show 42") == "42"
    assert _bool("3 < 5") == "1"


def test_a_signature_stays_polymorphic_across_uses():
    """A use at one type must not monomorphise the definition.

    The prelude itself uses `append` at `List Char` to build `show`'s
    output; before signatures were held fixed that pinned `append`'s
    element type to `Char` for the whole program.
    """
    assert _int("length (append [1, 2] [3, 4])") == "4"
    assert _str('append "ab" "cd"') == "abcd"
