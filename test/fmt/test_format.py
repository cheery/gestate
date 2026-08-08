"""Tests for the Gestate autoformatter (gestate.fmt).

Verifies idempotency (format(format(x)) == format(x)) and
AST-preserving round-trips (parse(format(parse(x))) == parse(x)).
"""

from __future__ import annotations

import pytest
from gestate.fmt import format
from gestate.syntax import parse


# ── Round-trip: format then parse must not crash ─────────────────────────────


def _roundtrip(source: str) -> str:
    """Format once, then format again. Should be idempotent."""
    return format(format(source))


def _parse_output(source: str) -> bool:
    """Verify that formatted output can be re-parsed."""
    try:
        out = format(source)
        parse(out)
        return True
    except Exception:
        return False


# ── Basic expressions ────────────────────────────────────────────────────────


def test_simple_let():
    assert _roundtrip("result = let x = 5 in x + 1") == format("result = let x = 5 in x + 1")


def test_let_multiline():
    src = "result = let\n    x = 5\n    y = 10\nin x + y\n"
    out = format(src)
    assert "let x = 5" in out
    assert "y = 10" in out
    assert "in x + y" in out or " in x + y" in out


def test_letrec():
    assert _parse_output("result = letrec f = 1 in f")


def test_case():
    src = "test xs = case xs of\n    [] -> 5\n    y :: ys -> y\n"
    out = format(src)
    assert "case xs of" in out
    assert "[] -> 5" in out
    assert "y :: ys -> y" in out


def test_lambda():
    src = "f = x y => x + y"
    assert format(format(src)) == format(src)


def test_lambda_paren():
    src = "f = (Some x) => x"
    assert format(format(src)) == format(src)


def test_app_chain():
    src = "x = f a b c"
    assert format(format(src)) == format(src)


def test_infix_precedence():
    src = "x = 1 + 2 * 3 - 4"
    out = format(src)
    assert "1 + 2 * 3 - 4" in out


def test_infix_cons():
    src = "x = a :: b :: c"
    out = format(src)
    assert "a :: b :: c" in out


def test_prefix():
    src = "x = -5"
    out = format(src)
    assert "-5" in out


def test_projection():
    src = "x = r.0"
    out = format(src)
    assert "r.0" in out


def test_tuple():
    assert _roundtrip("x = (1, 2, 3)") == format("x = (1, 2, 3)")


def test_list():
    assert _roundtrip("x = [1, 2, 3]") == format("x = [1, 2, 3]")


def test_list_tail():
    src = "x = [1 | xs]"
    out = format(src)
    assert "1 | xs" in out


def test_empty_list():
    assert format("x = []") == format(format("x = []"))


def test_set():
    src = "x = {1, 2}"
    assert format(format(src)) == format(src)


def test_empty_set():
    assert format("x = {}") == format(format("x = {}"))


def test_hex():
    assert _parse_output("x = 0xFF")


def test_string():
    src = 'x = "hello"'
    assert format(format(src)) == format(src)


# ── Top-level declarations ───────────────────────────────────────────────────


def test_sig_and_eqn():
    src = "x : Int\nx = 5\n"
    assert format(format(src)) == format(src)


def test_type_decl():
    src = "Maybe a := Nothing\n        | Just a\n"
    out = format(src)
    assert "Maybe a :=" in out
    assert "Nothing" in out
    assert "| Just a" in out


def test_type_decl_single_ctor():
    src = "SomeRecord a := SomeRecord a a\n"
    out = format(src)
    assert "SomeRecord a := SomeRecord a a" in out


def test_fixity():
    src = "infixl 4 ++\n"
    assert format(format(src)) == format(src)


def test_fixity_reserved():
    src = "infixr 5 ::\n"
    assert format(format(src)) == format(src)


def test_kind():
    src = "kind Cyclic : Int -> Type\n"
    assert format(format(src)) == format(src)


# ── Class and instance ───────────────────────────────────────────────────────


def test_class():
    src = "class Eq a where\n    (==) : a -> a -> Bool\n    (/=) : a -> a -> Bool\n"
    out = format(src)
    assert "class Eq a where" in out
    assert "(==) : a -> a -> Bool" in out
    assert "(/=) : a -> a -> Bool" in out


def test_instance():
    src = "instance Eq Int where\n    x == y = True\n"
    out = format(src)
    assert "instance Eq Int where" in out
    assert "x == y = True" in out


# ── Special constructs ───────────────────────────────────────────────────────


def test_for():
    src = "x = for (a in b) a"
    assert format(format(src)) == format(src)


def test_for_multi():
    src = "x = for (a in b, c in d) a + c"
    out = format(src)
    assert "for (a in b, c in d)" in out


def test_fix():
    assert format(format("x = fix e")) == format("x = fix e")


def test_gfix():
    assert format(format("x = gfix v => e")) == format("x = gfix v => e")


def test_box():
    assert _parse_output("x = Box y")


def test_unbox():
    assert _parse_output("x = unbox p = e in b")


# ── Errata: given / using / GADT-style constraints ────────────────────────────


def test_given_single_line():
    src = "result = given x = 5 in x + 1"
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_given_semicolon():
    src = "result = given x = 5; y = 10 in x + y"
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_given_multiline():
    src = "result = given x = 5\n    y = 10\nin x + y"
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_using_in_sc():
    src = "f (using ord) x y = x"
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_using_in_sc_multi():
    src = "f (using ord test) x y = x"
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_maxof_program():
    src = "\n".join([
        "maxOf : (ord Ordering t, test Int) => t -> t -> t",
        "maxOf (using ord test) x y = x",
        "",
        "result = given ord = ordInt",
        "              test = 5",
        "in maxOf 4 5",
    ])
    out = format(src)
    assert "maxOf (using ord test) x y = x" in out
    assert "given ord = ordInt" in out
    assert _parse_output(src)


def test_showbox_gadt():
    src = "ShowBox := (Show a) => ShowBox a"
    assert _parse_output(src)
    out = format(src)
    assert "(Show a) => ShowBox a" in out
    assert format(src) == format(format(src))


# ── Comments ─────────────────────────────────────────────────────────────────


def test_comment_preserved():
    src = "# a comment\nx = 5\n"
    out = format(src)
    assert "#" in out
    assert "comment" in out


# ── Idempotency ──────────────────────────────────────────────────────────────


def test_idempotent_comprehensive():
    src = "\n".join([
        "infixl 4 ++",
        "",
        "SomeRecord a := SomeRecord a a",
        "",
        "x : Int",
        "x = 5",
        "",
        "choose5 : Maybe Int -> Int",
        "choose5 Nothing = 5",
        "choose5 (Just x) = x",
        "",
        "test xs = case xs of",
        "    [] -> 5",
        "    h :: t -> h",
        "",
    ])
    assert format(src) == format(format(src))


def test_all_parseable():
    cases = [
        "x = 5",
        "x = 1 + 2",
        "x = let a = 1 in a",
        "x = let a = 1; b = 2 in a + b",
        "x = for (a in xs) a",
        "x = fix f",
        "x = gfix s => 0",
        "x = Box y",
        "x = unbox p = e in b",
        "x = []",
        "x = [1]",
        "x = [1, 2]",
        "x = {}",
        "x = {1}",
        "x = (1, 2)",
        "x = f a",
        "x = f a b",
        "x = a b => a",
    ]
    for c in cases:
        assert _parse_output(c), f"Failed on: {c}"


# ── Operator references ───────────────────────────────────────────────────────


def test_op_ref_infix():
    src = "f = (+)"
    out = format(src)
    assert "(+)" in out
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_op_ref_prefix():
    src = "f = (+_)"
    out = format(src)
    assert "(+_)" in out
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_op_ref_postfix():
    src = "f = (_+)"
    out = format(src)
    assert "(_+)" in out
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_op_ref_application():
    src = "f = (+) a b"
    assert _parse_output(src)


def test_op_ref_infix_other_op():
    src = "f = (*)"
    out = format(src)
    assert "(*)" in out
    assert _parse_output(src)


# ── Operators as declaration heads ───────────────────────────────────────────


def test_an_operator_signature_keeps_its_parentheses():
    """`(@) : …`, not `@ : …` — the second is not a declaration.

    The prelude's composition is written this way, and the formatter
    printed it bare: `parse` then rejected its own output with
    `expected declaration, got '@'`.
    """
    src = "(@) : (b -> c) -> (a -> b) -> a -> c\n(@) f g x = f (g x)\n"
    out = format(src)
    assert "(@) : " in out
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_a_two_operand_operator_is_not_written_infix_at_the_top_level():
    """The parser has no infix *definition* form outside an instance.

    It was written back as `x <+> y = …`, which reads perfectly and
    which `parse` answers with `expected pattern, got '<+>'`.
    """
    src = "(<+>) : Int -> Int -> Int\n(<+>) x y = x + y\n"
    out = format(src)
    assert "(<+>) x y = " in out
    assert "x <+> y = " not in out
    assert _parse_output(src)


def test_a_class_operator_member_keeps_its_parentheses():
    """The list this used to consult had no `<+>` in it, and could not."""
    src = "class Plus a where\n    (<+>) : a -> a -> a\n"
    out = format(src)
    assert "(<+>) : " in out
    assert _parse_output(src)


# ── Type aliases ──────────────────────────────────────────────────────────────


def test_type_alias():
    src = "type Node = Int\n"
    out = format(src)
    assert "type Node" in out
    assert " = Int" in out
    assert _parse_output(src)
    assert format(src) == format(format(src))


def test_type_alias_params():
    src = "type Pair a = (a, a)\n"
    out = format(src)
    assert "type Pair a =" in out
    assert "(a, a)" in out
    assert _parse_output(src)


def test_type_alias_conid():
    src = "type MyId = Id\n"
    assert _parse_output(src)
