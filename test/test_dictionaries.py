"""Tests for dictionary-passing elaboration (implementation_order.md §18).

Every instance becomes a tuple of its method closures, built by a
supercombinator whose parameters are the dictionaries of its context, so
one generic ``Sum (List a)`` instance serves lists of every depth.
"""

from __future__ import annotations

import pytest

from gestate.constraint import match_head
from gestate.declarations import classify
from gestate.elaborate import elaborate
from gestate.expr import EAp, EGlobal, EProj, ETuple
from gestate.gmachine import GmError
from gestate.pipeline import evaluate
from gestate.syntax import parse
from gestate.types import TApp, TCon, TVar


SUM = (
    "class Sum a where\n  total : a -> Int\n\n"
    "instance Sum Int where\n  total x = x\n\n"
)

RECURSIVE = SUM + (
    "instance (Sum a) => Sum (List a) where\n"
    "  total xs = case xs of\n"
    "    Nil -> 0\n"
    "    Cons h t -> total h + total t\n\n"
)


# ── Running ──────────────────────────────────────────────────────────────────


def test_instance_without_context():
    assert evaluate(SUM + "main : Int\nmain = total 7\n") == "7"


def test_context_dictionary_is_passed():
    src = RECURSIVE + "main : Int\nmain = total (Cons 1 (Cons 2 (Cons 3 Nil)))\n"
    assert evaluate(src) == "6"


def test_empty_structure():
    assert evaluate(RECURSIVE + "main : Int\nmain = total Nil\n") == "0"


def test_nested_structures_reuse_one_instance():
    # `Sum (List (List Int))` builds `dictList (dictList dictInt)` — the
    # List instance is compiled once, not specialised per element type.
    src = RECURSIVE + (
        "main : Int\n"
        "main = total (Cons (Cons 1 (Cons 2 Nil)) (Cons (Cons 3 Nil) Nil))\n"
    )
    assert evaluate(src) == "6"


def test_three_levels_deep():
    src = RECURSIVE + "main : Int\nmain = total (Cons (Cons (Cons 7 Nil) Nil) Nil)\n"
    assert evaluate(src) == "7"


def test_two_context_predicates():
    src = (
        "class Sum a where\n  total : a -> Int\n\n"
        "class Size a where\n  size : a -> Int\n\n"
        "instance Sum Int where\n  total x = x\n\n"
        "instance Size Int where\n  size x = 1\n\n"
        "Wrap a := MkWrap a\n\n"
        "instance (Sum a, Size a) => Sum (Wrap a) where\n"
        "  total w = case w of\n    MkWrap x -> total x + size x\n\n"
        "main : Int\nmain = total (MkWrap 5)\n"
    )
    assert evaluate(src) == "6"


def test_method_slots_are_indexed_by_class_order():
    src = (
        "class Two a where\n  first2 : a -> Int\n  second2 : a -> Int\n\n"
        "instance Two Int where\n  first2 x = x\n  second2 x = x + 100\n\n"
        "main : Int\nmain = second2 5\n"
    )
    assert evaluate(src) == "105"


def test_literals_in_instance_bodies_default_to_int():
    src = SUM.replace("total x = x", "total x = 42") + "main : Int\nmain = total 1\n"
    assert evaluate(src) == "42"


# ── Per-occurrence routing ───────────────────────────────────────────────────


def test_one_method_at_two_types_in_one_supercombinator():
    # Each occurrence carries its own predicate, so the two calls get
    # different dictionaries — a by-name map could only hold one.
    src = RECURSIVE + "main : Int\nmain = total 7 + total (Cons 1 (Cons 2 Nil))\n"
    assert evaluate(src) == "10"


def test_recursive_call_and_context_call_differ():
    # In the List instance `total h` is the element's dictionary and
    # `total t` is this instance's own, rebuilt from the same parameter.
    scs = _elaborated(RECURSIVE + "main : Int\nmain = total (Cons 1 Nil)\n")
    body = str(scs["__Sum_List_a-2_total__"])
    assert "EVar(name='_d0')" in body                 # the element call
    assert "__dict_Sum_List_a-2__'), arg=EVar(name='_d0')" in body  # recursion


# ── Generated shape ──────────────────────────────────────────────────────────


def _elaborated(source: str) -> dict[str, object]:
    from gestate.constraint import solve_constraints
    from gestate.desugar import desugar_program
    from gestate.infer import infer_program
    from gestate.pipeline import _build_builtins

    program = classify(parse(source))
    scs = desugar_program(program)
    contexts = {sc.name: sc.sig_constraints for sc in program.scs}
    results, per_sc, givens = infer_program(scs, _build_builtins(), program.cons,
                                            program.classes, contexts)
    resolved = solve_constraints([p for sl in per_sc for p in sl],
                                 program.instances)
    out = elaborate(scs, per_sc, resolved, program, results, givens)
    return {name: lam for name, _arity, lam, _sig in out}


def test_dictionary_is_a_tuple_of_methods():
    scs = _elaborated(SUM + "main : Int\nmain = total 7\n")
    dictionary = scs["__dict_Sum_Int__"]
    assert dictionary.params == []
    assert dictionary.body == ETuple([EGlobal("__Sum_Int_total__")])


def test_context_dictionary_takes_a_parameter():
    scs = _elaborated(RECURSIVE + "main : Int\nmain = total (Cons 1 Nil)\n")
    dictionary = scs["__dict_Sum_List_a-2__"]
    assert dictionary.params == ["_d0"]
    assert dictionary.body == ETuple(
        [EAp(EGlobal("__Sum_List_a-2_total__"), _var("_d0"))])


def test_call_site_projects_out_of_the_dictionary():
    scs = _elaborated(SUM + "main : Int\nmain = total 7\n")
    call = scs["main"].body
    assert call.fn == EAp(EProj(0), EGlobal("__dict_Sum_Int__"))


def _var(name: str):
    from gestate.expr import EVar
    return EVar(name)


# ── One occurrence, however many times inference walks it ────────────────────


def test_a_shared_fallback_arm_is_one_occurrence():
    """fixme.md F105.  The match compiler shares an equation's body
    across the leaves of its decision tree, so the fallback of a string
    pattern is inferred once per failure edge — ten `Num`/`Floating`
    predicates on `bimix`'s one stamp, and the router's arity check read
    that as inference having produced ten dictionaries.  Equal
    predicates on one site are one predicate; `bimix`'s two *distinct*
    ones must both survive the deduplication, which is what this
    program checks by needing exactly two.
    """
    assert evaluate(
        'f : String -> Float\n'
        'f "ab" = 0.0\n'
        'f _ = bimix 0.1 0.2 0.3\n\n'
        'main : Float\nmain = f "xy"\n'
    ) == "0.165"


def test_the_f105_specimen_compiles():
    """The program Henri actually wrote — a scored `voices` bank whose
    `sections` matches on string literals, with `'` in both arms."""
    from pathlib import Path

    from gestate import audioperform

    specimen = (Path(__file__).resolve().parent / "sessions"
                / "F105-hello2.ges")
    audioperform.graph_of(specimen.read_text(), rate=44100)


def test_an_elaboration_error_names_the_declaration():
    """F105's second half: whatever trips inside the rewrite, the reader
    is told whose declaration it was in — the invariant style must never
    reach `trouble` as a bare sentence about a mangled name.

    Built by hand, because the deduplication above makes the mismatch
    unreachable from source — which is the point of it — while the
    breadcrumb has to hold for whatever trips this seam next.  Two
    *different* predicates on one arity-1 stamp is the honest remaining
    shape: a genuinely changed type at one occurrence.
    """
    from gestate.declarations import classify
    from gestate.elaborate import ElaborateError
    from gestate.expr import EAp, ELambda, ENum
    from gestate.types import Predicate

    g_ref = EGlobal("g")
    g_ref.site_token = 99
    scs = [("f", 0, ELambda([], EAp(g_ref, ENum(1))), None),
           ("g", 1, ELambda(["x"], _var("x")), None)]
    preds = [[Predicate("Num", TCon("Int"), 99),
              Predicate("Floating", TCon("Float"), 99)],
             []]
    givens = [[], [Predicate("Num", TVar(1))]]
    with pytest.raises(ElaborateError) as caught:
        elaborate(scs, preds, {}, classify(parse("")),
                  per_sc_givens=givens)
    said = str(caught.value)
    assert "`g` expects 1 dictionary argument(s)" in said
    assert "while checking `f`" in said


# ── Instance-head matching ───────────────────────────────────────────────────


def test_match_head_binds_a_variable_to_a_variable():
    # `Sum [a]` matched against `Sum [b]` must record a ↦ b so the
    # instance's context can be instantiated.
    bindings = match_head(TApp(TCon("List"), TVar(-2)),
                          TApp(TCon("List"), TVar(3)))
    assert bindings == {-2: TVar(3)}


def test_match_head_still_accepts_unresolved_metavariables():
    assert match_head(TCon("Int"), TVar(7)) == {}


def test_match_head_rejects_a_different_constructor():
    assert match_head(TApp(TCon("List"), TVar(-2)), TCon("Int")) is None


def test_a_number_applied_to_arguments_says_so_first(tmp_path):
    """fixme.md F127.  `sound = 0.0 sine freq * …` — a missing operator
    — used to answer only `No instance for Floating ((Sig Float -> Sig
    Float) -> Sig Float -> Sig Float)`: the truth in inference's own
    language, with no position, no breadcrumb, and the human fact
    absent from the one line a status bar shows.  The author's
    sentence leads now, the owner rides with the file's own position,
    and the instance-speak keeps the second line for the box."""
    from pathlib import Path

    from gestate.audioeditor import Workbench
    from gestate.session import _line_of

    p = tmp_path / "typo.ges"
    p.write_text("freq : Sig Float\n"
                 "freq = !220.0\n"
                 "\n"
                 "sound : Sig Float\n"
                 "sound = 0.0 sine freq * 1.0\n")
    bench = Workbench(p, rate=8000, block=64)
    try:
        bench.start()
    except Exception:                                    # noqa: BLE001
        pass
    first = bench.trouble.splitlines()[0]
    assert "applied to 2 arguments" in first and "takes none" in first, \
        bench.trouble
    assert "while checking `sound`" in bench.trouble
    assert "typo.ges:5" in bench.trouble, "not the file's own position"
    assert _line_of(bench.trouble, "typo.ges") == 5, \
        "the content box has no line to anchor under"


# ── A block inside a member, or inside an alternative — `fixme.md` F52 ───────


def test_a_multi_line_member_does_not_end_the_instance_body():
    """`_parse_case` leaves its closing `DEDENT` for the caller, and inside
    a `class`/`instance` body that `DEDENT` read as the end of the *body*:
    every member after a multi-line one silently moved out to the top
    level.  The prelude holds the form hard — `Functor List` at
    `prelude.ges:39` is a multi-line member — and this names it, parse
    only, so a tidy-up there cannot take the gate away without a line
    changing colour."""
    module = parse("instance Two Int where\n"
                   "  first2 x = case x of\n"
                   "    0 -> 1\n"
                   "    n -> n\n"
                   "  second2 x = x + 100\n"
                   "\n"
                   "main : Int\nmain = 1\n")
    kinds = [type(i).__name__ for i in module.items]
    assert kinds == ["VInstance", "VSig", "VSCDecl"], kinds
    assert [m.name for m in module.items[0].members] == ["first2", "second2"]


def test_a_multi_line_alternative_does_not_end_the_match():
    """The same `DEDENT`, inside a `case` alternative, read as the end of
    the *match*: an alternative after a nested multi-line `case` was lost
    to the enclosing one."""
    module = parse("f : Int -> Int -> Int\n"
                   "f x y = case x of\n"
                   "  0 -> case y of\n"
                   "    0 -> 1\n"
                   "    m -> m\n"
                   "  n -> n\n")
    (decl,) = [i for i in module.items if type(i).__name__ == "VSCDecl"]
    body = decl.equations[0].body
    assert type(body).__name__ == "VCase" and len(body.alts) == 2


# ── A slot for an undefined method is loud, not zero — `fixme.md` F48 ────────


def test_an_undefined_method_slot_fails_when_projected():
    """`elaborate` filled a missing method's slot with `ENum(0)`, on the
    reasoning that a well-typed program never projects it.  It does, and
    `Unwind` on a number ignores the spine, so the call quietly evaluated
    to `0`.  The slot holds an unbound global now — inert unless projected,
    and an error naming the method when it is.  The synthetic `Num
    (Cyclic n)` instance that first tripped this defines all four methods
    today (`test_arith.py::test_cyclic_arithmetic_wraps`), so this is the
    only program left that projects the placeholder."""
    src = ("class Two a where\n  first2 : a -> Int\n  second2 : a -> Int\n\n"
           "instance Two Int where\n  first2 x = x\n\n"
           "main : Int\nmain = second2 5\n")
    with pytest.raises(GmError, match="second2"):
        evaluate(src)
