"""Signature type variables are skolems (`fixme.md` F36).

`spec/types.md` §3 reads a signature as a contract: its variables stand
for types the *caller* picks, so the body may not decide what they are.
Before this, they were ordinary metavariables and `f : a -> Int ;
f x = x + 1` type-checked by unifying `a` with `Int` — the one remaining
place the checker accepted an ill-typed program.

Two halves, because a variable is decided in two ways: unification binds
it, and constraint resolution picks an instance for it.  Both are refused
here; only the signature's own context can say anything about `a`.
"""

from __future__ import annotations

import pytest

from gestate.constraint import ConstraintError
from gestate.pipeline import evaluate
from gestate.types import Subst, TCon, TFun, TVar
from gestate.unify import UnifyError, unify


# ── The mechanism ────────────────────────────────────────────────────────────


def test_a_rigid_variable_is_not_bound_to_a_type():
    with pytest.raises(UnifyError, match="is rigid"):
        unify(TVar(1, rigid=True), TCon("Int"))


def test_rigidity_is_refused_from_either_side():
    """`check` unifies actual against expected, `infer_program` the reverse."""
    with pytest.raises(UnifyError, match="is rigid"):
        unify(TCon("Int"), TVar(1, rigid=True))


def test_two_rigid_variables_are_not_each_other():
    with pytest.raises(UnifyError, match="is rigid"):
        unify(TVar(1, rigid=True, name="a"), TVar(2, rigid=True, name="b"))


def test_a_rigid_variable_unifies_with_itself():
    assert unify(TVar(1, rigid=True), TVar(1, rigid=True)) == Subst.empty()


def test_a_metavariable_may_still_be_bound_to_a_skolem():
    """The direction that makes a signed body checkable at all.

    A parameter's type is a fresh metavariable; the signature says what it
    is.  Only the reverse — the body deciding the signature — is refused.
    """
    s = unify(TVar(7), TVar(1, rigid=True))

    assert s.apply(TVar(7)) == TVar(1)


def test_rigidity_does_not_change_a_variable_s_identity():
    """Two occurrences of `a` are the same variable however they are marked.

    Rigidity is a property of the occurrence — a use site instantiates the
    scheme into fresh metavariables — so it must stay out of equality.
    """
    assert TVar(1, rigid=True) == TVar(1)
    assert Subst.empty().extend(1, TCon("Int")).apply(TVar(1, rigid=True)) \
        == TCon("Int")


# ── Unification: the body may not decide the caller's type ───────────────────


def test_a_signature_variable_is_not_unified_with_a_concrete_type():
    """F36's example."""
    with pytest.raises(UnifyError, match="is rigid"):
        evaluate("f : a -> Int\nf x = x + 1\n\nmain : Int\nmain = f 3\n")


def test_two_signature_variables_are_not_unified_with_each_other():
    with pytest.raises(UnifyError, match="is rigid"):
        evaluate("f : a -> b\nf x = x\n\nmain : Int\nmain = f 3\n")


def test_a_signature_variable_is_not_unified_inside_a_former():
    with pytest.raises(UnifyError, match="is rigid"):
        evaluate("f : a -> {a}\nf x = x\n\nmain : {Int}\nmain = f 3\n")


def test_the_error_names_the_variable_as_written():
    with pytest.raises(UnifyError, match="'elem' is rigid"):
        evaluate("f : elem -> Int\nf x = x + 1\n\nmain : Int\nmain = f 3\n")


def test_a_genuinely_polymorphic_body_is_accepted():
    assert evaluate("f : a -> a\nf x = x\n\nmain : Int\nmain = f 3\n") == "3"


def test_a_signature_variable_may_be_used_at_the_caller_s_type():
    """Rigid inside the body, instantiated at every use site."""
    assert evaluate(
        'p : a -> a\np x = x\n\n'
        'main : String\nmain = append (p "ab") (p "cd")\n'
    ) == "abcd"


def test_a_body_ignoring_the_variable_is_accepted():
    assert evaluate("f : a -> Int\nf x = 1\n\nmain : Int\nmain = f 3\n") == "1"


# ── Resolution: an instance may not decide it either ─────────────────────────


def test_a_class_constraint_on_a_signature_variable_is_not_defaulted():
    """`Num a` at a skolem is unsatisfiable, not ambiguous.

    Defaulting it to `Int` would answer a question the caller answers, and
    `f` would claim to work at every type while adding integers.
    """
    with pytest.raises(ConstraintError, match="No instance for Num"):
        evaluate("f : a -> a\nf x = x + 1\n\nmain : Int\nmain = f 3\n")


def test_a_class_constraint_on_a_signature_variable_takes_no_instance():
    """`Show a` used to match whichever `Show` instance came first.

    `show x` at a skolem silently rendered as the head of the instance
    table — the program ran and printed nothing.
    """
    with pytest.raises(ConstraintError, match="No instance for Show"):
        evaluate("f : a -> String\nf x = show x\n\n"
                 "main : String\nmain = f 3\n")


def test_the_constraint_error_says_which_context_to_write():
    with pytest.raises(ConstraintError, match="signature variable"):
        evaluate("f : a -> a -> Bool\nf x y = x == y\n\n"
                 "main : Bool\nmain = f 1 2\n")


def test_the_declared_context_discharges_it():
    assert evaluate("f : (Num a) => a -> a\nf x = x + 1\n\n"
                    "main : Int\nmain = f 3\n") == "4"


def test_the_declared_context_discharges_a_method_call():
    assert evaluate("f : (Show a) => a -> String\nf x = show x\n\n"
                    "main : String\nmain = f 42\n") == "42"


def test_a_superclass_of_the_declared_context_discharges_it():
    """Contexts are closed under superclasses, so `Ord a` grants `Eq a`."""
    assert evaluate("f : (Ord a) => a -> a -> Bool\nf x y = x == y\n\n"
                    "main : Int\nmain = case f 1 1 of\n"
                    "  True -> 1\n  False -> 0\n") == "1"


# ── The rest of the program is unaffected ────────────────────────────────────


def test_an_unsigned_definition_is_still_inferred():
    """Only a *declared* variable is rigid; inference is unchanged."""
    assert evaluate("g x = x + 1\n\nmain : Int\nmain = g 3\n") == "4"


def test_a_concrete_signature_is_unaffected():
    assert evaluate("f : Int -> Int\nf x = x + 1\n\n"
                    "main : Int\nmain = f 3\n") == "4"


def test_a_polymorphic_signature_over_a_former_is_accepted():
    parts = evaluate("ident : {a} -> {a}\nident s = s\n\n"
                     "main : {Int}\nmain = ident {1, 2}\n")
    assert parts  # it compiles and runs; the set's rendering is not the point


def test_a_function_type_in_a_signature_stays_polymorphic():
    assert evaluate("apply : (a -> b) -> a -> b\napply f x = f x\n\n"
                    "inc : Int -> Int\ninc n = n + 1\n\n"
                    "main : Int\nmain = apply inc 4\n") == "5"


# ── The variable that was meant to be a type (`fixme.md` F141) ───────────────


def test_a_type_written_in_lowercase_is_named_as_the_typo_it_is():
    """`foo : int` — gestate's first outside user, and a fair mistake.

    A lowercase name *is* a type variable, so the signature was a legal
    polymorphic one over a variable spelled like a type, and the file
    analysed without a word about `int`.  What the person then got was
    a complaint about a class, somewhere else, in the vocabulary of a
    feature they were not using.
    """
    from gestate.kindcheck import KindError

    with pytest.raises(KindError, match="not the type `Int`"):
        evaluate("foo : int\nfoo = 3\n\nmain : Int\nmain = foo\n")


def test_it_says_where_the_name_was_written():
    """A signature variable is minted rather than desugared from a node,
    so it used to be the one thing in a type with no position at all."""
    from gestate.kindcheck import KindError

    with pytest.raises(KindError, match=r"\(at 0:8\)"):
        evaluate("depth : float\ndepth = 0.5\n\n"
                 "main : Float\nmain = depth\n")


def test_it_is_caught_before_the_advice_that_would_make_it_permanent():
    """The old first complaint was *"No instance for Num int — write
    '(Num int) => …' in the signature"*: true of the program written,
    and advice towards the wrong fix."""
    from gestate.kindcheck import KindError

    with pytest.raises(KindError):
        evaluate("double : float -> float\ndouble x = x * 2.0\n\n"
                 "main : Float\nmain = double 2.0\n")


def test_an_honest_variable_is_left_alone():
    """It fires on an exact case-insensitive match with a type this
    program has, which is what makes it a typo rather than a guess:
    `a` and `b` name nothing."""
    assert evaluate("apply : (a -> b) -> a -> b\napply f x = f x\n\n"
                    "inc : Int -> Int\ninc n = n + 1\n\n"
                    "main : Int\nmain = apply inc 4\n") == "5"


def test_a_declared_type_is_matched_too_and_not_only_a_builtin():
    """The vocabulary is the program's own kind environment, so a type
    the file declares protects its own name."""
    from gestate.kindcheck import KindError

    with pytest.raises(KindError, match="not the type `Colour`"):
        evaluate("Colour := Red | Blue\n\n"
                 "pick : colour -> Int\npick c = 1\n\n"
                 "main : Int\nmain = pick Red\n")


def test_a_one_letter_variable_is_never_the_typo():
    """`C := S` and a library signature that says `c`.

    Found by `test_session.py` rather than reasoned out: the check runs
    over the *assembled* program, so a one-letter type in the file
    would make every library signature spelling a variable `c` an error
    in that program's presence — a rule firing on somebody else's
    correct code, from a distance.  A single letter is how every
    signature everywhere spells a variable, and is never this mistake.
    """
    from gestate.pipeline import compile as _compile

    _compile("C := S\n\n"
             "pick : c -> C\npick x = S\n\n"
             "main : C\nmain = pick 1\n")
