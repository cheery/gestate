"""Tests for type aliases (``type Name params = body``).

Per ``spec/types.md`` §6, aliases are expanded eagerly — they never reach
the unifier — and self-referential aliases (direct or transitive) are
rejected.
"""

from __future__ import annotations

import pytest

from gestate.declarations import DeclError, classify
from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.types import TCon, TFun


def _classify(source: str):
    return classify(parse(source))


def _sig(source: str, name: str):
    program = _classify(source)
    return next(sc.sig_type for sc in program.scs if sc.name == name)


# ── Expansion ────────────────────────────────────────────────────────────────


def test_alias_expands_in_signature():
    assert _sig("type Count = Int\n\nf : Count -> Count\nf x = x\n", "f") == \
        TFun(TCon("Int"), TCon("Int"))


def test_alias_never_reaches_the_type_table():
    program = _classify("type Count = Int\n\nf : Count\nf = 1\n")
    assert "Count" not in str(program.scs[0].sig_type)


def test_parameterized_alias():
    assert _sig("type Fn a = a -> a\n\nf : Fn Int\nf x = x\n", "f") == \
        TFun(TCon("Int"), TCon("Int"))


def test_nested_alias():
    src = "type Count = Int\ntype Fn a = a -> a\n\nf : Fn Count\nf x = x\n"
    assert _sig(src, "f") == TFun(TCon("Int"), TCon("Int"))


def test_alias_used_before_its_declaration():
    src = "f : Count -> Count\nf x = x\n\ntype Count = Int\n"
    assert _sig(src, "f") == TFun(TCon("Int"), TCon("Int"))


def test_alias_of_a_type_constructor_takes_extra_arguments():
    program = _classify("type S = Set\n\nf : S Int -> Int\nf x = 1\n")
    assert str(program.scs[0].sig_type) == "((Set Int) -> Int)"


def test_alias_parameter_shadows_an_alias_name():
    src = "type count = Int\ntype ident count = count\n\ng : ident Bool\ng = 1\n"
    assert _sig(src, "g") == TCon("Bool")


def test_alias_in_constructor_field():
    program = _classify("type Count = Int\n\nWrap := MkWrap Count\n")
    assert str(program.cons["MkWrap"].type_) == "(Int -> Wrap)"


def test_alias_in_class_and_instance():
    src = (
        "type Count = Int\n\n"
        "class Sized a where\n"
        "  size : a -> Count\n\n"
        "instance Sized Count where\n"
        "  size x = x\n"
    )
    program = _classify(src)
    assert str(program.classes["Sized"].methods["size"]).endswith("-> Int)")
    heads = [i.head_type for i in program.instances if i.class_name == "Sized"]
    assert heads == [TCon("Int")]


# ── Cycle detection ──────────────────────────────────────────────────────────


def test_direct_recursion_rejected():
    with pytest.raises(DeclError, match="Recursive type alias"):
        _classify("type T = List T\n")


def test_transitive_recursion_rejected():
    with pytest.raises(DeclError, match="Recursive type alias"):
        _classify("type A = List B\ntype B = Set A\n")


def test_self_reference_under_a_parameter_rejected():
    with pytest.raises(DeclError, match="Recursive type alias"):
        _classify("type T a = a -> T a\n")


# ── Other errors ─────────────────────────────────────────────────────────────


def test_partially_applied_alias_rejected():
    with pytest.raises(DeclError, match="fully applied"):
        _classify("type F a = List a\n\nf : F -> Int\nf x = 1\n")


def test_duplicate_alias_rejected():
    with pytest.raises(DeclError, match="Duplicate type alias"):
        _classify("type T = Int\ntype T = Bool\n")


def test_alias_clashing_with_a_data_type_rejected():
    with pytest.raises(DeclError, match="clashes with a data type"):
        _classify("Foo := Bar\ntype Foo = Int\n")


def test_alias_clashing_with_a_builtin_rejected():
    with pytest.raises(DeclError, match="clashes with a built-in type"):
        _classify("type Int = Bool\n")


def test_duplicate_alias_parameters_rejected():
    with pytest.raises(DeclError, match="duplicate type parameters"):
        _classify("type T a a = Int\n")


# ── End to end ───────────────────────────────────────────────────────────────


def test_program_with_aliases_runs():
    src = (
        "type Count = Int\n"
        "type Fn a = a -> a\n\n"
        "inc : Fn Count\n"
        "inc x = x + 1\n\n"
        "main : Count\n"
        "main = inc 5\n"
    )
    assert evaluate(src) == "6"


def test_alias_in_constructor_field_runs():
    src = (
        "type Count = Int\n\n"
        "Wrap := MkWrap Count\n\n"
        "unwrap : Wrap -> Count\n"
        "unwrap (MkWrap x) = x\n\n"
        "main : Count\n"
        "main = unwrap (MkWrap 7)\n"
    )
    assert evaluate(src) == "7"


def test_alias_in_an_expression_annotation():
    src = (
        "type Count = Int\n\n"
        "main : Count\n"
        "main = (7 : Count)\n"
    )
    assert evaluate(src) == "7"
