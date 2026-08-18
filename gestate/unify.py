"""Syntactic unification with mandatory occurs check.

Total: never crashes, always returns ``Either[TypeError, Subst]``.
Error messages include source spans when available.
"""

from __future__ import annotations

from .types import (
    Subst,
    TApp,
    TCon,
    TFun,
    TInt,
    TVar,
    Type,
    free_vars,
)


#: complaint  author — two types that do not fit, said at both of their spans
class UnifyError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _span_str(t: Type) -> str:
    """Extract a source-location suffix from a type's span, if any."""
    for node in (t,):
        sp = getattr(node, 'span', None)
        if sp is not None:
            s = _format_span(sp)
            if s:
                return f" (at {s})"
    return ""


def _format_span(sp) -> str:
    """Format a Span/Pos from the syntax module as 'line:col'."""
    if hasattr(sp, 'start') and hasattr(sp, 'end'):
        s = sp.start
        e = sp.end
        return f"{s.line}:{s.col}–{e.line}:{e.col}"
    if hasattr(sp, 'line') and hasattr(sp, 'col'):
        return f"{sp.line}:{sp.col}"
    return ""


def unify(actual: Type, expected: Type) -> Subst:
    """Unify two types, returning a substitution on success.

    Raises ``UnifyError`` on failure (type mismatch or occurs-check
    violation).  The resulting substitution, when applied to both
    arguments, makes them syntactically equal.

    **The argument order is part of the interface.**  Unification itself is
    symmetric, but the error message is not: it reads "expected `expected`,
    got `actual`".  Calling it the other way round produces a message with
    the two roles swapped, which is what `f : List Int -> Int` applied to
    `True` used to report — "expected Bool, got List Int" (`fixme.md` F30).
    """
    return _go(actual, expected, Subst.empty())


def _pair(a: Type, b: Type) -> tuple[str, str]:
    """Both types rendered with **one** naming of their variables.

    Lettered together, because `expected` and `got` sit one above the
    other in the message and a `b` in one line must mean the same
    variable as a `b` in the other — two independent renderings could
    hand the same letter to different metavariables and the comparison
    would lie.
    """
    from .show import name_vars, show_type

    names = name_vars([b, a])
    return show_type(a, names), show_type(b, names)


def _head(t: Type) -> Type:
    """The constructor at the bottom of an application spine."""
    while isinstance(t, TApp):
        t = t.fn
    return t


def _go(a: Type, b: Type, s: Subst) -> Subst:
    a = s.apply(a)
    b = s.apply(b)

    if isinstance(a, TVar) and isinstance(b, TVar) and a.id == b.id:
        return s
    # A rigid variable is a signature's skolem: it names a type the caller
    # chooses, so nothing the body does may bind it.  A metavariable on the
    # other side is still bound — *to* the skolem — which is what lets a
    # signed body use its own parameters at all.
    if isinstance(a, TVar) and not a.rigid:
        return _bind(a.id, b, s)
    if isinstance(b, TVar) and not b.rigid:
        return _bind(b.id, a, s)
    if isinstance(a, TVar) or isinstance(b, TVar):
        raise _rigid_error(a, b)

    if isinstance(a, TCon) and isinstance(b, TCon):
        if a.name == b.name:
            return s
        # **`got` on its own line, indented to `expected`'s column**,
        # here and at every mismatch below: a status bar shows the
        # first line, and the content box under the line shows
        # expected, got and the `while checking` breadcrumb as three
        # rows — with the two types starting one above the other, so
        # the eye can walk them for the difference.
        raise UnifyError(
            f"Type mismatch: expected '{b.name}'{_span_str(b)}\n"
            f"               got '{a.name}'{_span_str(a)}"
        )

    if isinstance(a, TInt) and isinstance(b, TInt):
        if a.n == b.n:
            return s
        raise UnifyError(
            f"Type mismatch: {a.n}{_span_str(a)} vs {b.n}{_span_str(b)}")

    if isinstance(a, TFun) and isinstance(b, TFun):
        if a.mono != b.mono:
            ga, gb = _pair(a, b)
            raise UnifyError(
                f"Arrow mismatch: expected {'a monotone' if b.mono else 'an ordinary'} "
                f"function {gb}{_span_str(b)}\n"
                f"                got {'a monotone' if a.mono else 'an ordinary'} "
                f"one {ga}{_span_str(a)}"
            )
        s = _go(a.arg, b.arg, s)
        return _go(a.ret, b.ret, s)

    if isinstance(a, TApp) and isinstance(b, TApp):
        # **Different constructors are reported as the whole types.**
        # Descending first meant the collision arrived at the `TCon`
        # arm with only the heads in hand — "expected 'List', got
        # 'Sig'" for a string where a signal goes — when the fact the
        # author can act on is `String` against `Sig Float`.
        ha, hb = _head(a), _head(b)
        if (isinstance(ha, TCon) and isinstance(hb, TCon)
                and ha.name != hb.name):
            ga, gb = _pair(a, b)
            raise UnifyError(
                f"Type mismatch: expected {gb}{_span_str(b)}\n"
                f"               got {ga}{_span_str(a)}"
            )
        s = _go(a.fn, b.fn, s)
        return _go(a.arg, b.arg, s)

    # Structural mismatch (e.g. TFun vs TCon)
    ga, gb = _pair(a, b)
    raise UnifyError(
        f"Type mismatch: expected {gb}{_span_str(b)}\n"
        f"               got {ga}{_span_str(a)}"
    )


def tvar_name(t: TVar) -> str:
    """How to call a type variable in a message: its source name if it has one."""
    return t.name or f"a{t.id}"


def _render(t: Type, avoid: str) -> str:
    """Surface syntax for a type, with letters for its metavariables.

    An internal id in a message (`a-42 -> a-42`) tells the reader nothing;
    `b -> b` tells them the shape.  ``avoid`` is the name the message
    already uses for the rigid variable, so the two cannot collide.
    """
    from .show import show_type

    names: dict[int, str] = {}
    used = {avoid} | {v.name for v in _tvars(t) if v.name is not None}
    for v in _tvars(t):
        if v.name is not None or v.id in names:
            continue                    # already has a name of its own
        letter = next((c for c in "bcdefghijklmnopqrstuvwxyza"
                       if c not in used), None)
        if letter is None:
            break
        names[v.id] = letter
        used.add(letter)
    return show_type(t, names)


def _tvars(t: Type):
    """The type variables of ``t``, in order of first appearance."""
    if isinstance(t, TVar):
        yield t
    elif isinstance(t, TFun):
        yield from _tvars(t.arg)
        yield from _tvars(t.ret)
    elif isinstance(t, TApp):
        yield from _tvars(t.fn)
        yield from _tvars(t.arg)


def _rigid_error(a: Type, b: Type) -> UnifyError:
    """Report the one thing a signature's variable may not do.

    Both directions reach here — `check` unifies actual against expected,
    `infer_program` expected against actual — so the rigid side is
    whichever one it is.  When *both* are rigid the message names both:
    `f : a -> b ; f x = x` fails because two variables the caller chooses
    separately are not the same type.
    """
    rigid, other = (a, b) if isinstance(a, TVar) and a.rigid else (b, a)
    assert isinstance(rigid, TVar)
    if isinstance(other, TVar) and other.rigid:
        what = f"the signature variable '{tvar_name(other)}'"
    else:
        what = f"'{_render(other, avoid=tvar_name(rigid))}'"
    return UnifyError(
        f"Signature variable '{tvar_name(rigid)}' is rigid: it stands for "
        f"whatever type the caller chooses, so the body may not use it as "
        f"{what}{_span_str(other)}"
    )


def _bind(var_id: int, t: Type, s: Subst) -> Subst:
    if occurs(var_id, t, s):
        # Lettered like every other message — `a3303 occurs in (a3303 ->
        # a3305)` names nothing the author can search for.
        from .show import name_vars, show_type
        names = name_vars([TVar(var_id), t])
        raise UnifyError(
            f"Occurs check: `{names.get(var_id, f'a{var_id}')}` would "
            f"contain itself in {show_type(t, names)} — an infinite "
            f"type{_span_str(t)}")
    return s.extend(var_id, t)


def occurs(var_id: int, t: Type, s: Subst) -> bool:
    t = s.apply(t)
    return var_id in free_vars(t)
