"""Derived instances: ``Color := Red | Green deriving (Show, Eq)``.

The instances are built as *surface* AST — the same `VSCEqn` bodies a user
would write — and handed to `classify` alongside the declared ones.  That
is the point: a derived method then goes through inference, constraint
solving, dictionary passing and code generation on exactly the path a
hand-written instance takes, so a field with its own context (`Wrap a`
needing `Show a`) works without any special case, and a mistake shows up as
an ordinary type error rather than as bad output.

The generated context is one predicate per type parameter: `Pair a b`
derives `(Show a, Show b) => Show (Pair a b)`.  That is Haskell's rule, and
it is what makes the recursive case of `Show (List a)`-shaped data types
resolve.
"""

from __future__ import annotations

from .syntax.ast import (
    Pat, PCon, PVar, Pos, Span,
    Val, VAlt, VApp, VCase, VConId, VCtor, VSCEqn, VStr, VWord,
)


#: complaint  author, nowhere — caught and re-raised by the `declarations.py` that reads the `deriving` clause, which is what places it
class DeriveError(Exception):
    pass


#: What `deriving` understands.
#:
#: `Ord` compares constructor *positions* first, then fields
#: lexicographically — Haskell's rule.  A constructor's tag cannot be named
#: in the surface language, which is why this looked to need a primitive;
#: it does not.  Enumerating both scrutinees gives the comparison
#: positionally, because the *order the alternatives are written in* is the
#: constructor order, and that is exactly the information a tag would carry.
#: The cost is n² alternatives for n constructors, which is fine at the
#: sizes anyone writes and is what the match compiler is for.
DERIVABLE = ("Show", "Eq", "Ord")

_S = Span(Pos(), Pos())


# ---------------------------------------------------------------------------
# Surface-AST helpers
# ---------------------------------------------------------------------------

def _w(name: str) -> Val:
    return VWord(name, _S)


def _ap(fn: Val, *args: Val) -> Val:
    for a in args:
        fn = VApp(fn, a, _S)
    return fn


def _str(text: str) -> Val:
    return VStr(text, _S)


def _con_pat(ctor: VCtor, prefix: str) -> tuple[Pat, list[str]]:
    """``C x0 … xn`` and the names it binds."""
    names = [f"_{prefix}{i}" for i in range(len(ctor.fields))]
    return PCon(ctor.name, [PVar(n, _S) for n in names], _S), names


def _wild_alt(body: Val) -> VAlt:
    return VAlt(PVar("_", _S), body, _S)


def _true() -> Val:
    return VConId("True", _S)


def _false() -> Val:
    return VConId("False", _S)


def _if_true(scrut: Val, then: Val, otherwise: Val) -> Val:
    """``case scrut of True -> then ; False -> otherwise``."""
    return VCase(scrut, [
        VAlt(PCon("True", [], _S), then, _S),
        VAlt(PCon("False", [], _S), otherwise, _S),
    ], _S)


# ---------------------------------------------------------------------------
# Show
# ---------------------------------------------------------------------------

def _show_body(ctors: list[VCtor]) -> VSCEqn:
    """``show v = case v of C x0 … -> "C" ++ " " ++ show x0 ++ …``"""
    alts: list[VAlt] = []
    for ctor in ctors:
        pat, names = _con_pat(ctor, "s")
        body: Val = _str(ctor.name)
        for n in names:
            # `append "C" (append " " (show x))`, left to right.
            body = _ap(_w("append"), body,
                       _ap(_w("append"), _str(" "), _ap(_w("show"), _w(n))))
        alts.append(VAlt(pat, body, _S))
    return VSCEqn("show", [PVar("_dv", _S)], VCase(_w("_dv"), alts, _S), [], _S)


# ---------------------------------------------------------------------------
# Eq
# ---------------------------------------------------------------------------

def _eq_body(ctors: list[VCtor]) -> VSCEqn:
    """``(==) a b = case a of C x… -> case b of C y… -> x == y ∧ … ; _ -> False``

    The inner wildcard is emitted only when there is something for it to
    catch — with a single constructor every value matches, and an
    unreachable alternative is an error, not a warning.
    """
    outer: list[VAlt] = []
    for ctor in ctors:
        lpat, lnames = _con_pat(ctor, "l")
        rpat, rnames = _con_pat(ctor, "r")

        conj: Val = _true()
        for ln, rn in reversed(list(zip(lnames, rnames))):
            conj = _if_true(_ap(_w("=="), _w(ln), _w(rn)), conj, _false())

        inner: list[VAlt] = [VAlt(rpat, conj, _S)]
        if len(ctors) > 1:
            inner.append(_wild_alt(_false()))
        outer.append(VAlt(lpat, VCase(_w("_db"), inner, _S), _S))

    return VSCEqn("==", [PVar("_da", _S), PVar("_db", _S)],
                  VCase(_w("_da"), outer, _S), [], _S)


def _ne_body() -> VSCEqn:
    """``(/=) a b = not (a == b)``"""
    return VSCEqn("/=", [PVar("_da", _S), PVar("_db", _S)],
                  _ap(_w("not"), _ap(_w("=="), _w("_da"), _w("_db"))), [], _S)


# ---------------------------------------------------------------------------
# Ord
# ---------------------------------------------------------------------------

def _lex(lnames: list[str], rnames: list[str]) -> Val:
    """`x₁ < y₁ ∨ (x₁ = y₁ ∧ (x₂ < y₂ ∨ …))` — fields, left to right.

    Bottoms out in `False`: two values whose fields are all equal are not
    *less* than one another.
    """
    acc: Val = _false()
    for ln, rn in reversed(list(zip(lnames, rnames))):
        acc = _if_true(
            _ap(_w("<"), _w(ln), _w(rn)), _true(),
            _if_true(_ap(_w("=="), _w(ln), _w(rn)), acc, _false()))
    return acc


def _lt_body(ctors: list[VCtor]) -> VSCEqn:
    """``(<) a b`` — constructor position first, then fields.

    Both scrutinees are enumerated, so the answer for a pair of
    constructors is decided by their *declaration order*: everything
    earlier is less than everything later, and a matching pair falls
    through to `_lex`.
    """
    outer: list[VAlt] = []
    for i, lctor in enumerate(ctors):
        lpat, lnames = _con_pat(lctor, "l")
        inner: list[VAlt] = []
        for j, rctor in enumerate(ctors):
            rpat, rnames = _con_pat(rctor, "r")
            if j < i:
                answer: Val = _false()      # a's constructor comes later
            elif j > i:
                answer = _true()            # a's constructor comes earlier
            else:
                answer = _lex(lnames, rnames)
            inner.append(VAlt(rpat, answer, _S))
        outer.append(VAlt(lpat, VCase(_w("_db"), inner, _S), _S))

    return VSCEqn("<", [PVar("_da", _S), PVar("_db", _S)],
                  VCase(_w("_da"), outer, _S), [], _S)


def _ord_rest() -> dict[str, VSCEqn]:
    """The other three, defined from `<` exactly as the prelude's do."""
    a, b = _w("_da"), _w("_db")
    params = [PVar("_da", _S), PVar("_db", _S)]
    return {
        "<=": VSCEqn("<=", params, _ap(_w("not"), _ap(_w("<"), b, a)), [], _S),
        ">":  VSCEqn(">",  params, _ap(_w("<"), b, a), [], _S),
        ">=": VSCEqn(">=", params, _ap(_w("not"), _ap(_w("<"), a, b)), [], _S),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def derive(class_name: str, type_name: str, params: list[str],
           ctors: list[VCtor]) -> tuple[list[Val], dict[str, VSCEqn]]:
    """The context and methods of a derived instance.

    Returns ``(context, methods)`` — the context as surface constraint
    expressions (``Show a``) so that `classify` desugars them with the
    instance's own type variables, and the methods as equations.
    """
    if class_name not in DERIVABLE:
        raise DeriveError(
            f"cannot derive '{class_name}' for '{type_name}' — deriving "
            f"understands {', '.join(DERIVABLE)}"
        )
    if not ctors:
        raise DeriveError(
            f"cannot derive '{class_name}' for '{type_name}': it has no "
            f"constructors"
        )

    context = [_ap(VConId(class_name, _S), _w(p)) for p in params]

    if class_name == "Show":
        return context, {"show": _show_body(ctors)}
    if class_name == "Ord":
        # `Ord` has `Eq` as a superclass, so a derived `Ord` needs an `Eq`
        # instance to exist as well — Haskell's rule, and instance
        # resolution reports it if the program does not derive both.
        return context, {"<": _lt_body(ctors), **_ord_rest()}
    return context, {"==": _eq_body(ctors), "/=": _ne_body()}


def instance_head(type_name: str, params: list[str]) -> list[Val]:
    """``T a b`` as the instance head's argument list."""
    head: Val = VConId(type_name, _S)
    for p in params:
        head = VApp(head, _w(p), _S)
    return [head]
