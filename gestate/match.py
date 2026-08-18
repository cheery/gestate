"""Pattern-match compilation: surface patterns → one-level ``ECase``.

The core ``ECase`` (`gestate/expr.py`) dispatches on a constructor tag and
binds that constructor's fields — nothing more.  Surface Gestate lets you
write nested patterns, literals, tuples, wildcards, list sugar and several
equations per definition.  This module is the bridge: it takes a *pattern
matrix* (one row per equation or ``case`` alternative, one column per
scrutinee) and lowers it to a tree of one-level ``ECase``/``ELet``.

The algorithm is the standard one — Augustsson's, as presented by Wadler in
chapter 5 of *The Implementation of Functional Programming Languages*.  Each
call to ``Matcher.compile`` consumes the leftmost column:

* **variable rule** — the column is irrefutable, so rename the user's
  variable to the subject and drop the column;
* **constructor rule** — group the rows by tag, emit one alternative per
  tag with the sub-patterns spliced onto the front of the row, and one
  alternative per *uncovered* constructor of the same ADT whose body is the
  failure continuation (core ``ECase`` has no default alternative, so the
  uncovered tags have to be written out);
* **literal rule** — an equality test per distinct value, falling through to
  the continuation;
* **tuple / signal-cons rules** — irrefutable like variables, but they
  project their sub-subjects out first.

Rows whose leading patterns are of different kinds are split into maximal
runs of one kind and folded right, each run's failure continuation being the
compilation of the runs after it (Wadler's *mixture rule*).  Because that
continuation can be reached from many places, it is bound to a `let` once
and referred to by name — otherwise the tree is exponential in the number of
equations.

Failure at the outermost level is ``__match_fail__``, a nullary global that
aborts (`gmachine.add_primitives`).  A program that passed
`gestate/exhaust.py` never reaches it, but the compiler emits it anyway
rather than assume the check ran.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .expr import (
    Alter, EAp, ECase, EGlobal, ELet, ENum, EProj, ESigHead, ETail, EUnbox,
    EVar, Expr,
)
from .declarations import ConInfo
from .syntax.ast import (
    Pat, PAnnot, PBox, PCon, PList, PLit, PSigCons, PTuple, PVar, Val,
)
from .syntax.rename import rename_free


#: complaint  machine — a pattern shape the desugarer has already refused, in the words it refused it with
class MatchError(Exception):
    """A pattern that cannot be compiled (bad arity, unknown constructor)."""


#: The nullary global a failed match falls through to.  Registered by
#: `gmachine.add_primitives`; typed as a fresh variable by `infer` so it
#: fits wherever it lands.
MATCH_FAIL = "__match_fail__"

#: Wildcard: binds nothing.
WILDCARD = "_"

#: Subject names are drawn from one supply shared by every `Matcher`.
#:
#: They have to be: a nested `case` is compiled by its *own* `Matcher`,
#: created while the enclosing one desugars an alternative's body.  With a
#: per-matcher counter both start at zero, the inner subjects shadow the
#: outer ones, and an outer pattern variable silently reads the inner
#: binding — `case xs of x :: _ -> case ys of z :: _ -> x < z` compiled to
#: `z < z`.  `reset_names` is called once per program so a given source
#: always produces the same names.
_NAME_COUNTER = 0


def reset_names() -> None:
    global _NAME_COUNTER
    _NAME_COUNTER = 0


def fresh_name(hint: str = "") -> str:
    """A name no source program can collide with, off the shared counter.

    Module-level so that desugarings which need a binder but not a whole
    `Matcher` — `for (p in e)`'s element, say — draw from the *same* supply.
    Two counters would reintroduce exactly the shadowing bug described above.

    The `#` is what makes the first sentence true rather than merely likely:
    it opens a comment, so no identifier can contain one, and a program that
    writes `_m1_elem` no longer captures a generated binder that happened to
    land on the same counter value.
    """
    global _NAME_COUNTER
    _NAME_COUNTER += 1
    return f"_m{_NAME_COUNTER}#{hint}" if hint else f"_m{_NAME_COUNTER}#"


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def normalize(pat: Pat) -> Pat:
    """Rewrite surface sugar into the four kinds the compiler dispatches on.

    List patterns become ``Cons``/``Nil`` chains — which is what makes
    ``[x]`` mean *a one-element list* rather than "a cons cell whose tail I
    forgot to check".  Annotations are dropped: there is nowhere to use a
    pattern type annotation yet, and keeping it would only make every
    consumer handle a transparent wrapper.
    """
    if isinstance(pat, PAnnot):
        return normalize(pat.pat)

    if isinstance(pat, PList):
        acc: Pat = (normalize(pat.tail) if pat.tail is not None
                    else PCon("Nil", [], pat.span))
        for item in reversed(pat.items):
            acc = PCon("Cons", [normalize(item), acc], pat.span)
        return acc

    if isinstance(pat, PCon):
        return PCon(pat.name, [normalize(a) for a in pat.args], pat.span)

    if isinstance(pat, PTuple):
        return PTuple([normalize(i) for i in pat.items], pat.span)

    if isinstance(pat, PSigCons):
        return PSigCons(normalize(pat.head), normalize(pat.tail), pat.span)

    if isinstance(pat, PBox):
        return PBox(normalize(pat.pat), pat.span)

    return pat


def _is_var(pat: Pat) -> bool:
    return isinstance(pat, PVar)


def _kind(pat: Pat) -> str:
    if isinstance(pat, PVar):
        return "var"
    if isinstance(pat, PCon):
        return "con"
    if isinstance(pat, PLit):
        return "lit"
    if isinstance(pat, PTuple):
        return "tuple"
    if isinstance(pat, PSigCons):
        return "sig"
    if isinstance(pat, PBox):
        return "box"
    raise MatchError(f"unsupported pattern: {type(pat).__name__}")


# ---------------------------------------------------------------------------
# ADT indexing
# ---------------------------------------------------------------------------

def _con_return_head(ci: ConInfo) -> str | None:
    """The name of the ADT ``ci`` constructs."""
    from .types import TApp, TCon, TFun

    t = ci.type_
    while isinstance(t, TFun):
        t = t.ret
    while isinstance(t, TApp):
        t = t.fn
    return t.name if isinstance(t, TCon) else None


def siblings(name: str, cons: dict[str, ConInfo]) -> list[ConInfo]:
    """Every constructor of the ADT that ``name`` belongs to, ``name`` first.

    Declaration order would do just as well; what matters is that the list
    is complete, because the uncovered constructors are what the compiler
    turns into fall-through alternatives.
    """
    ci = cons.get(name)
    if ci is None:
        raise MatchError(f"unknown constructor in pattern: {name}")
    adt = _con_return_head(ci)
    if adt is None:
        return [ci]
    out = [c for c in cons.values() if _con_return_head(c) == adt]
    out.sort(key=lambda c: (c.name != name, c.tag))
    return out


# ---------------------------------------------------------------------------
# Rows
# ---------------------------------------------------------------------------

@dataclass
class Row:
    """One equation or ``case`` alternative, mid-compilation.

    ``pats`` shrinks as columns are consumed; ``renames`` grows with the
    pattern variables those columns bound, each mapped to the subject that
    now holds its value.  The body stays *surface* until the row reaches a
    leaf, where the renaming is applied to it — a rename rather than a
    ``let`` because a binding the source did not write is a change variable
    the ϕ/δ transform has no rule for, and because it keeps the generated
    ``case`` the same shape a hand-written one would have.
    """
    pats: list[Pat]
    body: Val
    renames: dict[str, str] = field(default_factory=dict)


def _shift(row: Row, new_head: list[Pat], renames: dict[str, str]) -> Row:
    """Replace the row's leading pattern with ``new_head``, adding renames."""
    return Row(list(new_head) + row.pats[1:], row.body,
               {**row.renames, **renames})


# ---------------------------------------------------------------------------
# The compiler
# ---------------------------------------------------------------------------

#: ``desugar(val, locals) -> Expr`` — supplied by `gestate/desugar.py`, which
#: owns expression desugaring.  Passing it in keeps this module free of the
#: expression grammar and avoids an import cycle.
DesugarFn = Callable[[Val, frozenset], Expr]


class Matcher:
    def __init__(self, cons: dict[str, ConInfo], desugar: DesugarFn,
                 where: str = "") -> None:
        self.cons = cons
        self.desugar = desugar
        self.where = where          # for error messages
        true_ci, false_ci = cons.get("True"), cons.get("False")
        self.true_tag = true_ci.tag if true_ci else None
        self.false_tag = false_ci.tag if false_ci else None

    # -- names ------------------------------------------------------------

    def fresh(self, hint: str = "") -> str:
        return fresh_name(hint)

    def _err(self, msg: str) -> MatchError:
        return MatchError(f"{self.where}: {msg}" if self.where else msg)

    # -- entry point ------------------------------------------------------

    def compile(self, subjects: list[str], rows: list[Row], default: Expr,
                locals_: frozenset) -> Expr:
        """Compile the matrix ``rows`` against ``subjects``.

        ``default`` is the failure continuation; ``locals_`` is the scope
        the row bodies will be desugared in, before their own bindings.
        """
        if not rows:
            return default

        # The continuation is reached from every uncovered constructor, so
        # it is bound once rather than copied.
        if _atomic(default):
            return self._compile(subjects, rows, default, locals_)
        k = self.fresh("fail")
        body = self._compile(subjects, rows, EVar(k), locals_)
        if not _mentions_var(body, k):
            return body
        return ELet(False, [(k, default)], body)

    def _compile(self, subjects: list[str], rows: list[Row], default: Expr,
                 locals_: frozenset) -> Expr:
        if not rows:
            return default
        if not subjects:
            return self._leaf(rows, default, locals_)

        # Mixture rule: maximal runs of one pattern kind, folded right.
        result = default
        for group in reversed(_runs(rows)):
            result = self._group(subjects, group, result, locals_)
        return result

    # -- leaves -----------------------------------------------------------

    def _leaf(self, rows: list[Row], default: Expr, locals_: frozenset) -> Expr:
        """Every column is consumed, so the first row wins."""
        row = rows[0]
        return self.desugar(rename_free(row.body, row.renames), locals_)

    # -- groups -----------------------------------------------------------

    def _group(self, subjects: list[str], group: list[Row], default: Expr,
               locals_: frozenset) -> Expr:
        kind = _kind(group[0].pats[0])
        u, us = subjects[0], subjects[1:]
        if kind == "var":
            return self._var_rule(u, us, group, default, locals_)
        if kind == "con":
            return self._con_rule(u, us, group, default, locals_)
        if kind == "lit":
            return self._lit_rule(u, us, group, default, locals_)
        if kind == "tuple":
            return self._tuple_rule(u, us, group, default, locals_)
        if kind == "box":
            return self._box_rule(u, us, group, default, locals_)
        return self._sig_rule(u, us, group, default, locals_)

    def _var_rule(self, u, us, group, default, locals_) -> Expr:
        rows = []
        for row in group:
            pat = row.pats[0]
            rename = {} if pat.name == WILDCARD else {pat.name: u}
            rows.append(_shift(row, [], rename))
        return self._compile(us, rows, default, locals_)

    def _con_rule(self, u, us, group, default, locals_) -> Expr:
        # Group by constructor, keeping first-appearance order so the
        # generated alternatives read like the source.
        by_name: dict[str, list[Row]] = {}
        for row in group:
            by_name.setdefault(row.pats[0].name, []).append(row)

        alts: list[Alter] = []
        for name, rows in by_name.items():
            ci = self.cons.get(name)
            if ci is None:
                raise self._err(f"unknown constructor in pattern: {name}")
            for row in rows:
                if len(row.pats[0].args) != ci.arity:
                    raise self._err(
                        f"constructor {name} takes {ci.arity} argument(s), "
                        f"but the pattern gives {len(row.pats[0].args)}"
                    )
            fields = [self.fresh(f"{name}{i}") for i in range(ci.arity)]
            sub = [_shift(r, list(r.pats[0].args), {}) for r in rows]
            body = self._compile(fields + us, sub, default,
                                 locals_ | frozenset(fields))
            alts.append(Alter(ci.tag, fields, body))

        # Core `ECase` has no default alternative, so the constructors the
        # matrix does not mention are written out explicitly.
        covered = {self.cons[n].tag for n in by_name}
        for ci in siblings(next(iter(by_name)), self.cons):
            if ci.tag in covered:
                continue
            alts.append(Alter(ci.tag,
                              [self.fresh(f"{ci.name}{i}") for i in range(ci.arity)],
                              default))
        return ECase(EVar(u), alts)

    def _lit_rule(self, u, us, group, default, locals_) -> Expr:
        if self.true_tag is None or self.false_tag is None:
            raise self._err("literal patterns need the built-in `Bool` type")
        values: list[int] = []
        for row in group:
            v = row.pats[0].value
            if not isinstance(v, int) or isinstance(v, bool):
                raise self._err(
                    f"only integer literal patterns are supported, got {v!r}"
                )
            if v not in values:
                values.append(v)

        # **A char compares through `ord`.**  `Char` is its own type
        # sharing `Int`'s representation, so the scrutinee of a string
        # pattern's element needs the coercion the language already
        # names; an integer pattern is untouched.
        from .syntax.ast import CharLit

        scrut = (EAp(EGlobal("ord"), EVar(u))
                 if any(isinstance(r.pats[0].value, CharLit) for r in group)
                 else EVar(u))
        result = default
        for value in reversed(values):
            rows = [_shift(r, [], {}) for r in group if r.pats[0].value == value]
            matched = self._compile(us, rows, default, locals_)
            test = EAp(EAp(EGlobal("prim_eq_int"), scrut), ENum(value))
            result = ECase(test, [
                Alter(self.true_tag, [], matched),
                Alter(self.false_tag, [], result),
            ])
        return result

    def _tuple_rule(self, u, us, group, default, locals_) -> Expr:
        n = len(group[0].pats[0].items)
        for row in group:
            if len(row.pats[0].items) != n:
                raise self._err(
                    "tuple patterns in one column must all have the same "
                    f"width; got {n} and {len(row.pats[0].items)}"
                )
        fields = [self.fresh(f"t{i}") for i in range(n)]
        binds = [(fields[i], EAp(EProj(i, n), EVar(u))) for i in range(n)]
        rows = [_shift(r, list(r.pats[0].items), {}) for r in group]
        body = self._compile(fields + us, rows, default,
                             locals_ | frozenset(fields))
        return ELet(False, binds, body)

    def _box_rule(self, u, us, group, default, locals_) -> Expr:
        # `Box p` is irrefutable — every `Box A` matches — so like the tuple
        # rule it binds a sub-subject rather than dispatching.  The binding
        # is an `unbox`, which is what moves `p`'s variables into the
        # discrete context.
        inner = self.fresh("box")
        rows = [_shift(r, [r.pats[0].pat], {}) for r in group]
        body = self._compile([inner] + us, rows, default,
                             locals_ | frozenset([inner]))
        return EUnbox(inner, EVar(u), body)

    def _sig_rule(self, u, us, group, default, locals_) -> Expr:
        # `x ::: xs` is irrefutable — every `Sig A` matches — so it binds
        # rather than dispatches (Rizzo §2.4).  `xs` is the *delayed* rest,
        # at `ExL (Sig A)`, which is what `|>` consumes.
        for row in group:
            if not _is_var(row.pats[0].tail):
                raise self._err(
                    "the tail of a signal-cons pattern is a delayed "
                    "computation, not a signal, so it can only be bound to a "
                    "variable — write `x ::: xs`"
                )
        h, t = self.fresh("head"), self.fresh("tail")
        binds = [(h, ESigHead(EVar(u))), (t, ETail(EVar(u)))]
        rows = [_shift(r, [r.pats[0].head, r.pats[0].tail], {}) for r in group]
        body = self._compile([h, t] + us, rows, default,
                             locals_ | frozenset([h, t]))
        return ELet(False, binds, body)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _runs(rows: list[Row]) -> list[list[Row]]:
    """Split ``rows`` into maximal runs whose leading patterns agree in kind."""
    out: list[list[Row]] = []
    for row in rows:
        k = _kind(row.pats[0])
        if out and _kind(out[-1][0].pats[0]) == k:
            out[-1].append(row)
        else:
            out.append([row])
    return out


def _atomic(e: Expr) -> bool:
    return isinstance(e, (EVar, EGlobal, ENum))


def count_var(e: Expr, name: str) -> int:
    """How many times ``name`` occurs free in ``e``.

    The match compiler's subjects are fresh, so no inner binder can shadow
    one; a plain count is exact.
    """
    from .expr import subexprs

    n = 0
    stack = [e]
    while stack:
        node = stack.pop()
        if isinstance(node, EVar) and node.name == name:
            n += 1
        stack.extend(subexprs(node))
    return n


def _mentions_var(e: Expr, name: str) -> bool:
    return count_var(e, name) > 0


def subst_var(e: Expr, name: str, replacement: Expr) -> Expr:
    """Replace every occurrence of ``EVar(name)`` with ``replacement``.

    Used to put a ``case``'s scrutinee back where its subject stood, when
    the compiled match refers to it exactly once.  Capture is impossible
    for the same reason the count is exact.
    """
    from .expr import map_children

    if isinstance(e, EVar) and e.name == name:
        return replacement
    return map_children(e, lambda c: subst_var(c, name, replacement))


def fail_expr() -> Expr:
    """The outermost failure continuation."""
    return EGlobal(MATCH_FAIL)
