"""Render Type values as surface syntax strings."""

from __future__ import annotations
from .types import Type, TVar, TCon, TFun, TApp, TInt, Scheme, tuple_parts


def show_type(t: Type, names: dict[int, str] | None = None,
              *, paren: bool = False) -> str:
    """Render a ``Type`` as surface-syntax string.

    ``names`` optionally maps type-variable ids to display names (see
    ``name_vars``), so internal ids never leak into user-facing text.
    """
    return _show(t, _APP_ARG if paren else _TOP, names or {})


# Precedence levels for parenthesisation.
_TOP = 0       # nothing binds looser
_FUN_ARG = 1   # left of `->`: parenthesise a function type
_APP_ARG = 2   # argument of an application: also parenthesise an application


def name_vars(types: list[Type]) -> dict[int, str]:
    """Assign ``a``, ``b``, … to the type variables of ``types``, in order
    of first appearance."""
    names: dict[int, str] = {}

    def walk(t: Type) -> None:
        if isinstance(t, TVar):
            if t.id not in names:
                i = len(names)
                names[t.id] = chr(ord('a') + i % 26) + ("" if i < 26 else str(i // 26))
        elif isinstance(t, TFun):
            walk(t.arg)
            walk(t.ret)
        elif isinstance(t, TApp):
            walk(t.fn)
            walk(t.arg)

    for t in types:
        walk(t)
    return names


def show_predicate(pred, names: dict[int, str] | None = None) -> str:
    """Render a ``Predicate`` as surface syntax: ``Show (List a)``."""
    return f"{pred.class_name} {show_type(pred.type_, names, paren=True)}"


def show_scheme(s: Scheme) -> str:
    """Render a ``Scheme`` as a surface-syntax string."""
    if s.vars:
        vs = " ".join(f"a{v}" for v in sorted(s.vars))
        return f"forall {vs}. {show_type(s.type_)}"
    return show_type(s.type_)


def _show(t: Type, prec: int, names: dict[int, str]) -> str:
    if isinstance(t, TVar):
        # A signature variable knows the name it was written with, which
        # beats an internal id wherever no display map was built.
        return names.get(t.id) or t.name or f"a{t.id}"
    if isinstance(t, TInt):
        return str(t.n)
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TFun):
        arrow = "~>" if t.mono else "->"
        s = f"{_show(t.arg, _FUN_ARG, names)} {arrow} {_show(t.ret, _TOP, names)}"
        return f"({s})" if prec >= _FUN_ARG else s
    if isinstance(t, TApp):
        parts = tuple_parts(t)
        if parts is not None:
            # `Tuple2 A B` is written `(A, B)` — already bracketed, so it
            # needs no parentheses of its own at any precedence.
            return "(" + ", ".join(_show(p, _TOP, names) for p in parts) + ")"
        # The function part of a spine never needs parens (`Pair a b`),
        # the argument does (`Maybe (List a)`).
        fn = _show(t.fn, _FUN_ARG, names)
        arg = _show(t.arg, _APP_ARG, names)
        # Cyclic 12, Bounded 4 30, Set Int, etc.
        if isinstance(t.fn, TCon) and t.fn.name == "Set":
            return f"{{{arg}}}"
        if isinstance(t.fn, TApp) and isinstance(t.fn.fn, TCon) \
           and t.fn.fn.name == "Bounded":
            # Bounded 4 30 → 4 .. 30
            lo = _show(t.fn.arg, _TOP, names)
            hi = arg
            return f"{lo} .. {hi}"
        s = f"{fn} {arg}"
        return f"({s})" if prec >= _APP_ARG else s
    return str(t)
