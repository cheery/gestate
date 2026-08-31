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


def test_trailing_comment_survives_the_formatter():
    """`x = 5  # gain` — trivia, reattached, never deleted.

    The comment is not part of the expression (`spec/comments.md`), but
    it is part of the file: it comes back out beside its declaration.
    """
    src = "x = 5  # gain\ny = 6  # level\n"
    out = format(src)
    assert "gain" in out and "level" in out
    assert out.index("gain") < out.index("y ="), "reattached out of order"


def test_a_declarations_interior_comment_survives():
    """A comment inside a multi-line expression is kept too — the
    position degrades to 'beside the declaration', the text never."""
    src = "x = (f\n    # pick the base\n    5)\n\nf y = y\n"
    out = format(src)
    assert "pick the base" in out


def test_trivia_is_one_list_on_the_module():
    """Every inside-a-declaration comment, in source order, spans intact
    — the accessible half of the design in `spec/comments.md`.

    **The text is what follows the `#`, spacing included.**  It used to
    be stripped both ends, and the formatter — which prints it straight
    back after a `#` — turned every `# like this` into `#like this`.  A
    formatter may move a comment; it may not edit one.
    """
    from gestate.syntax.parse import parse_module
    from gestate.syntax.tokenize import tokenize

    m = parse_module(tokenize("x = 5  # gain\ny = 6  # level\n"))
    assert [(c.text, c.span.start.line) for c in m.comments] == \
        [(" gain", 0), (" level", 1)]


def test_a_comment_keeps_the_space_after_its_hash():
    """What a person typed is what comes back — the whole point."""
    for text in ("# a header\n", "#no space\n", "#   wide\n"):
        assert format(text + "x = 5\n").startswith(text)


def test_a_blank_line_between_declarations_survives():
    """**Blank lines are the author's paragraphing.**

    Dropping them rewrote every file into one wall of declarations. The
    formatter owns spacing *within* a declaration; between them the
    grouping is a decision somebody made about their own program, and
    nothing in the tree could reconstruct it.

    One blank for any gap, not the exact count: two and three mean the
    same to a reader, and keeping whatever it was handed is what stops a
    formatter being idempotent.
    """
    out = format("a : Int\na = 1\n\nb : Int\nb = 2\n\n\nc : Int\nc = 3\n")
    assert out == "a : Int\na = 1\n\nb : Int\nb = 2\n\nc : Int\nc = 3\n"
    assert format(out) == out, "and it settles"


def test_a_header_stays_against_its_declaration():
    """The gap belongs *before* the comment, not between it and what it
    is about — a comment is a thing on a line too, so the gap after it
    is measured from it."""
    out = format("a = 1\n\n# what b is\nb = 2\n")
    assert out == "a = 1\n\n# what b is\nb = 2\n"


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


# ── Parentheses that carry meaning — `fixme.md` F46 ──────────────────────────
#
# `format` promises output that re-parses to the same AST.  Three shapes broke
# it and were repaired; none of them was named by a test until 2026-08-31, and
# each stayed green under a mutation that put the defect back.
#
# **Idempotency does not hold these.**  `x => x + 1 + 2` formats to itself, so
# `format(format(s)) == format(s)` passes on the wrong output.  What catches
# them is feeding in the text the formatter itself produces and asking for it
# back unchanged: a dropped parenthesis is then a diff on the first pass.


def _survives(source: str) -> None:
    """The formatter's own output, formatted again, comes back verbatim."""
    assert format(source) == source


def test_an_operand_that_runs_to_the_end_keeps_its_parentheses():
    """F46, first bullet: `(x => x + 1) + 2` must not lose the parens.

    `x => e`, `let … in e` and `case … of …` all run to the end of the
    expression, so an unparenthesised one swallows the operator that
    follows it.
    """
    _survives("main : Int\nmain = (let a = 1 in a) + 2\n")
    _survives("main : Int\nmain = (x => x + 1) + 2\n")
    _survives("g : Int -> Int\ng n = (case n of\n    _ -> 1) + 2\n")


def test_an_infix_operand_is_parenthesised_by_associativity():
    """F46, second bullet: `_fmt_infix` compared precedence and ignored
    associativity, so `(a -> b) -> c` came back as `a -> b -> c` — a
    different type — and `1 - (2 - 3)` as `1 - 2 - 3`.
    """
    _survives("f : (Int -> Int) -> Int\nf g = g 1\n")
    _survives("main : Int\nmain = 1 - (2 - 3)\n")


def test_a_compound_pattern_in_juxtaposed_position_keeps_its_parentheses():
    """F46, third bullet: a parameter and a constructor argument are
    juxtaposed, so a cons pattern printed bare there — `f x :: xs` — is a
    different program from `f (x :: xs)`.
    """
    _survives("f : List Int -> Int\nf (x :: xs) = x\n")
    _survives("g : Maybe Int -> Int\ng (Just x) = x\ng Nothing = 0\n")


# ── The positions F46 did not reach — F186, F187, F188 ───────────────────────
#
# Found 2026-08-31 while writing the three gates above, and repaired the same
# day.  Same check, same reason it works: the formatter's own output, handed
# back to it, must come out verbatim.


def test_an_application_head_keeps_its_parentheses():
    """`fixme.md` F186 — `_fmt_app` parenthesised every argument and wrote
    the head bare, so a head that runs to the end of the expression swallowed
    the argument beside it: `(x => x + 1) 2` came back as `x => x + 1 2`.
    """
    _survives("main : Int\nmain = (x => x + 1) 2\n")
    _survives("main : Int\nmain = (let f = y => y in f) 2\n")
    _survives("f : Int -> Int\nf n = (case n of\n    _ -> y => y) 2\n")


def test_a_lambdas_parameters_are_atoms():
    """`fixme.md` F187 — F46's third bullet in the two callers it did not
    reach: a lambda's parameters, and an instance member's.
    """
    _survives("f : List Int -> Int\nf = (x :: xs) => x\n")
    _survives("f : Maybe Int -> Int\nf = (Just x) => x\n")
    _survives("class C a where\n    f : a -> Int\n\n"
              "instance C (List Int) where\n    f (x :: xs) = x\n    f [] = 0\n")


def test_a_box_pattern_is_written_as_one():
    """`fixme.md` F188 — `_fmt_pat` had no `PBox` branch and fell through to
    the debugging placeholder, so `f (Box x) = x` formatted as `f <PBox> = x`,
    which does not parse at all.  Parenthesised where it is juxtaposed and
    bare where it stands alone, like a constructor pattern.
    """
    _survives("f : Box Int -> Int\nf (Box x) = x\n")
    _survives("f : Box Int -> Int\nf b = case b of\n    Box x -> x\n")


def test_no_output_wears_a_placeholder():
    """The catch-all `<PBox>` was silent, and the next pattern node added
    would be silent the same way — so this asks the question F188 wanted
    asked: nothing the formatter emits may be a `repr`.
    """
    for src in ("f : Box Int -> Int\nf (Box x) = x\n",
                "f : List Int -> Int\nf (x :: xs) = x\n",
                "f : (Int, Int) -> Int\nf (a, b) = a\n",
                "f : Sig Int -> Int\nf (x ::: xs) = x\n",
                "f : Maybe Int -> Int\nf (Just x) = x\nf Nothing = 0\n"):
        out = format(src)
        assert "<" not in out, f"placeholder in output for {src!r}: {out!r}"
