"""The Datafun monomorphization boundary — `errata.md` D9, `fixme.md` F64/F58.

Datafun helpers are generated per *concrete* set type, so an operation at a
type that is still a variable has nothing to call.  The boundary was real
and entirely unenforced: such a program compiled and then died at run time
as `unknown global 'for_Set_a-43'`, a G-machine error naming an internal
symbol and pointing nowhere near the cause.

The check is on *references*, not on types.  A non-ground set type that
nothing reaches is harmless — the polymorphic prelude's dead branches
mention them legitimately — so only a helper some body actually calls is
required to exist.  That distinction is what makes the check precise enough
to turn on, and it is what found F58's latent crash below.
"""

from __future__ import annotations

import re

import pytest

from gestate.pipeline import (MonomorphizationError,
                              compile as pcompile, evaluate)

_ELEM = re.compile(r"Pack\{1,2\} (\([^()]*\)|-?\d+)")


def _elems(source: str) -> list[str]:
    return _ELEM.findall(evaluate(source))


def _cells(source: str) -> int:
    """How many elements the result has.

    Used where the point is that the program *compiles and runs*: a set
    built one way and the same set built another do not print alike, since
    the union spine is often still an unforced thunk.
    """
    return evaluate(source).count("Pack{1,2}")


# ── The boundary is reported, not crashed into ───────────────────────────────


def test_a_polymorphic_datafun_signature_is_a_compile_error():
    with pytest.raises(MonomorphizationError, match="not concrete"):
        evaluate("f : {a} ~> {a}\nf s = for (x in s) {x}\n\n"
                 "main : {Int}\nmain = f {1} \\/ f {2}\n")


def test_a_polymorphic_fix_is_a_compile_error():
    with pytest.raises(MonomorphizationError, match="not concrete"):
        evaluate("f : Box {a} -> {a}\nf (Box s) = fix r => s \\/ r\n\n"
                 "main : {Cyclic 4}\nmain = f (Box {1})\n")


def test_the_error_names_the_supercombinator_the_user_wrote():
    # Not `f_phi`, which is what ϕ/δ renamed it to.
    with pytest.raises(MonomorphizationError, match=r"'f' needs"):
        evaluate("f : {a} ~> {a}\nf s = for (x in s) {x}\n\n"
                 "main : {Int}\nmain = f {1} \\/ f {2}\n")


def test_the_error_does_not_leak_a_type_variable_id():
    with pytest.raises(MonomorphizationError) as exc:
        evaluate("f : {a} ~> {a}\nf s = for (x in s) {x}\n\n"
                 "main : {Int}\nmain = f {1} \\/ f {2}\n")
    assert "`Set a`" in str(exc.value)
    assert not re.search(r"a-?\d", str(exc.value))


# ── What stays legal ─────────────────────────────────────────────────────────


def test_an_unsigned_body_is_monomorphized_at_its_use():
    assert _cells("f s = for (x in s) {x}\n\nmain : {Int}\nmain = f {1}\n") == 1


def test_a_concrete_signature_is_fine():
    assert _cells("f : {Int} ~> {Int}\nf s = for (x in s) {x}\n\n"
                  "main : {Int}\nmain = f {1}\n") == 1


def test_the_polymorphic_prelude_still_compiles():
    # The check must not fire on a non-ground set type nothing calls; the
    # prelude has them in dead branches.  Every other test in the suite
    # depends on this, but say it once explicitly.
    assert evaluate("main : Int\nmain = 1\n") == "1"


# ── F58: annotations inside an instance method body ──────────────────────────


def test_a_fix_inside_an_instance_method():
    """`fixme.md` F58 — compiled to `unknown global 'fix_Set_a0'`.

    An instance method body is checked by `infer_instance_method`, which
    never ran the pass that pushes the finished substitution back through
    `ESet`/`EFix`/`EFor` annotations, so the helper name was derived from a
    metavariable.  Both now share `settle_annotations`.
    """
    assert _elems("class Loop a where\n    go : a -> Set (Cyclic 8)\n\n"
                  "instance Loop Int where\n    go n = fix r => {1} \\/ r\n\n"
                  "main : Set (Cyclic 8)\nmain = go 0\n") == ["1"]


def test_an_empty_set_inside_an_instance_method():
    """The same defect reached through the prelude's own `Guard Bool`.

    Its `False -> {}` branch is ⊥ at a set type, left unsettled, so a guard
    that was *false* under a `fix` crashed on `bottom_Set_a1`.  Every guard
    test passed because none of them ever took the false branch under a
    fixpoint — which is what the reference check found.
    """
    assert _elems("f : Box (Set (Cyclic 4)) -> Set (Cyclic 4)\n"
                  "f (Box e) = fix r => e \\/ {x | x in r, x > 100}\n\n"
                  "main : Set (Cyclic 4)\nmain = f (Box {0})\n") == ["0"]


def test_a_guard_that_is_sometimes_false_under_a_fix():
    assert _elems("f : Box (Set (Cyclic 4)) -> Set (Cyclic 4)\n"
                  "f (Box e) = fix r => e \\/ {x + 1 | x in r, x < 2}\n\n"
                  "main : Set (Cyclic 4)\nmain = f (Box {0})\n") == ["0", "1", "2"]


# ── The transform is skipped where nothing needs it — `fixme.md` F41 ─────────


def test_a_program_with_no_datafun_form_gets_no_set_helpers():
    """F41: a default `Set Int` was injected into every program.

    The helper family is generated per concrete set type, and the set types
    are collected from signatures — where a set used only inside a body is
    invisible, so an injected `Set Int` covers it.  That fallback is right
    *inside* a Datafun program and wrong outside one, where it hands a
    program with no set anywhere the whole family plus a ϕ/δ pass that gives
    every FRP combinator a nonsensical `f_delta`.  `_uses_datafun` is the
    guard, and nothing named it until 2026-08-31.
    """
    state = pcompile("double : Int -> Int\ndouble n = n + n\n\n"
                     "main : Int\nmain = double 21\n", prelude=True)
    injected = sorted(n for n in state.globals
                      if isinstance(n, str) and "_Set_Int" in n)
    assert injected == []
