"""Exhaustiveness and redundancy checking (`spec/types.md` §4).

This runs on *surface* patterns, before desugaring.  It has to: the match
compiler writes out an alternative for every constructor of the scrutinee's
ADT — the uncovered ones jump to the failure continuation — so by the time a
match reaches the core ``ECase`` its tag coverage is complete by
construction, and there is nothing left to count.

The algorithm is Maranget's (*Warnings for pattern matching*, JFP 2007).
One predicate does both jobs:

    useful(P, q)  —  is there a value that ``q`` matches and no row of the
                     matrix ``P`` matches?

A match is **non-exhaustive** exactly when ``useful(P, (_, …, _))`` holds,
and the witness the algorithm returns *is* the counterexample to print.  A
row is **redundant** exactly when it is not useful with respect to the rows
above it.  Nesting, literals, tuples and wildcards all fall out of the same
recursion, which is why the old tag-set check could not be repaired in
place.

"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass

from .declarations import ConInfo, Program
from .match import MatchError, normalize, siblings
from .syntax.ast import (
    at,
    Pat, PBox, PCon, PLit, PSigCons, PTuple, PVar, Val, VCase,
)


#: complaint  author — a definition that does not cover every value, placed at its first equation
class ExhaustError(Exception):
    pass


# ---------------------------------------------------------------------------
# Internal pattern form
# ---------------------------------------------------------------------------
#
# Surface patterns carry spans and sugar; the algorithm wants a uniform
# "wildcard / constructor / literal" shape.  A key identifies a constructor:
# a data constructor's name, or the synthetic ``("tuple", n)`` / ``("sig",)``
# for the two structural forms, which each have a one-element signature.

WILD = None


@dataclass(frozen=True)
class Ctor:
    key: object
    args: tuple


@dataclass(frozen=True)
class Lit:
    value: object


def _to_pattern(pat: Pat):
    """Surface ``Pat`` → the internal form.  ``pat`` must be normalised."""
    if isinstance(pat, PVar):
        return WILD
    if isinstance(pat, PCon):
        return Ctor(pat.name, tuple(_to_pattern(a) for a in pat.args))
    if isinstance(pat, PLit):
        return Lit(pat.value)
    if isinstance(pat, PTuple):
        return Ctor(("tuple", len(pat.items)),
                    tuple(_to_pattern(i) for i in pat.items))
    if isinstance(pat, PSigCons):
        return Ctor(("sig",), (_to_pattern(pat.head), _to_pattern(pat.tail)))
    if isinstance(pat, PBox):
        # Irrefutable, one field: `Box A` has exactly one shape, so the
        # box contributes nothing to coverage and only its sub-pattern does.
        return Ctor(("box",), (_to_pattern(pat.pat),))
    raise MatchError(f"unsupported pattern: {type(pat).__name__}")


def _arity(key, cons: dict[str, ConInfo]) -> int:
    if isinstance(key, tuple):
        if key[0] == "tuple":
            return key[1]
        return 1 if key[0] == "box" else 2
    ci = cons.get(key)
    if ci is None:
        raise MatchError(f"unknown constructor in pattern: {key}")
    return ci.arity


# ---------------------------------------------------------------------------
# Matrix operations
# ---------------------------------------------------------------------------

def _specialize(key, arity: int, rows: list[list]) -> list[list]:
    """S(c, P) — keep the rows that can match ``key``, expanding its fields."""
    out = []
    for row in rows:
        head = row[0]
        if head is WILD:
            out.append([WILD] * arity + row[1:])
        elif isinstance(head, Ctor) and head.key == key:
            out.append(list(head.args) + row[1:])
    return out


def _specialize_lit(value, rows: list[list]) -> list[list]:
    out = []
    for row in rows:
        head = row[0]
        if head is WILD:
            out.append(row[1:])
        elif isinstance(head, Lit) and head.value == value:
            out.append(row[1:])
    return out


def _default(rows: list[list]) -> list[list]:
    """D(P) — the rows that match anything the column's constructors do not."""
    return [row[1:] for row in rows if row[0] is WILD]


def _column_keys(rows: list[list]) -> tuple[list, list]:
    """The constructor keys and literal values heading the first column."""
    keys, lits = [], []
    for row in rows:
        head = row[0]
        if isinstance(head, Ctor) and head.key not in keys:
            keys.append(head.key)
        elif isinstance(head, Lit) and head.value not in lits:
            lits.append(head.value)
    return keys, lits


def _missing(keys: list, lits: list, cons: dict[str, ConInfo]):
    """A constructor the column does not cover — the head of a witness."""
    if lits:
        v = 0
        while v in lits:
            v += 1
        return Lit(v)
    if not keys:
        return WILD
    first = keys[0]
    if isinstance(first, tuple):
        return WILD          # tuples and signals have complete signatures
    for ci in siblings(first, cons):
        if ci.name not in keys:
            return Ctor(ci.name, tuple([WILD] * ci.arity))
    return WILD


def _is_complete(keys: list, lits: list, cons: dict[str, ConInfo]) -> bool:
    if lits:
        return False         # infinitely many integers
    if not keys:
        return False
    first = keys[0]
    if isinstance(first, tuple):
        # A tuple or a signal-cons has exactly one constructor, so the
        # column covers its whole signature as soon as it mentions it.
        return all(k == first for k in keys)
    if any(isinstance(k, tuple) for k in keys):
        return False         # mixed shapes — a type error, not our business
    covered = set(keys)
    return all(ci.name in covered for ci in siblings(first, cons))


# ---------------------------------------------------------------------------
# Usefulness
# ---------------------------------------------------------------------------

def _useful(rows: list[list], q: list, cons: dict[str, ConInfo]) -> list | None:
    """Maranget's ``U``, returning a witness vector rather than a boolean.

    ``None`` means ``q`` is not useful: every value it matches is already
    matched by a row of ``rows``.
    """
    if not q:
        return [] if not rows else None

    head, rest = q[0], q[1:]

    if isinstance(head, Ctor):
        arity = _arity(head.key, cons)
        sub = _useful(_specialize(head.key, arity, rows),
                      list(head.args) + rest, cons)
        if sub is None:
            return None
        return [Ctor(head.key, tuple(sub[:arity]))] + sub[arity:]

    if isinstance(head, Lit):
        sub = _useful(_specialize_lit(head.value, rows), rest, cons)
        return None if sub is None else [Lit(head.value)] + sub

    keys, lits = _column_keys(rows)
    if _is_complete(keys, lits, cons):
        # Every value has one of these heads, so a wildcard is useful only
        # where one of the specialised matrices leaves a gap.
        for key in keys:
            arity = _arity(key, cons)
            sub = _useful(_specialize(key, arity, rows),
                          [WILD] * arity + rest, cons)
            if sub is not None:
                return [Ctor(key, tuple(sub[:arity]))] + sub[arity:]
        return None

    sub = _useful(_default(rows), rest, cons)
    if sub is None:
        return None
    return [_missing(keys, lits, cons)] + sub


# ---------------------------------------------------------------------------
# Rendering a witness
# ---------------------------------------------------------------------------

def show_pattern(p, top: bool = True) -> str:
    if p is WILD:
        return "_"
    if isinstance(p, Lit):
        return repr(p.value) if isinstance(p.value, str) else str(p.value)
    if isinstance(p.key, tuple) and p.key[0] == "tuple":
        return "(" + ", ".join(show_pattern(a) for a in p.args) + ")"
    # `::` and `:::` are right-associative, so the tail needs no parentheses
    # however deep it goes; the head does as soon as it is compound.
    if isinstance(p.key, tuple):
        sig = f"{show_pattern(p.args[0], False)} ::: {show_pattern(p.args[1])}"
        return sig if top else f"({sig})"
    if p.key == "Nil":
        return "[]"
    if p.key == "Cons":
        cons = f"{show_pattern(p.args[0], False)} :: {show_pattern(p.args[1])}"
        return cons if top else f"({cons})"
    if not p.args:
        return str(p.key)
    inner = f"{p.key} " + " ".join(show_pattern(a, False) for a in p.args)
    return inner if top else f"({inner})"


def _show_row(row: list) -> str:
    # A multi-column row reads as an argument list, so its columns need the
    # parentheses an argument would need: `f Nothing (Just _)`.
    top = len(row) == 1
    return " ".join(show_pattern(p, top) for p in row)


# ---------------------------------------------------------------------------
# Checking one matrix
# ---------------------------------------------------------------------------

def check_matrix(rows: list[list[Pat]], cons: dict[str, ConInfo],
                 what: str, where: str, place: str = "") -> list[str]:
    """Check one pattern matrix.

    ``what`` names the construct ("case", "definition") and ``where`` the
    enclosing supercombinator, for the message.  ``place`` is ` (at L:C)`
    for the equation or ``case`` this matrix came from — **a definition
    that does not cover every value is a mistake with a line**, and
    naming the definition alone left the workbench nothing to draw a box
    under (`card:error-messages.md`).
    """
    prefix = f"{where}: " if where else ""
    errors: list[str] = []
    try:
        matrix = [[_to_pattern(normalize(p)) for p in pats] for pats in rows]
        if not matrix:
            return [f"{prefix}{what}: no alternatives{place}"]
        width = len(matrix[0])
        if any(len(r) != width for r in matrix):
            return []        # arity mismatch — the desugarer reports it
        for row in matrix:
            _validate(row, cons)

        # Redundancy: a row unreachable from the rows above it.
        seen: list[list] = []
        for row in matrix:
            if _useful(seen, row, cons) is None:
                errors.append(
                    f"{prefix}{what}: unreachable alternative — "
                    f"`{_show_row(row)}` is already covered{place}"
                )
            seen.append(row)

        witness = _useful(seen, [WILD] * width, cons)
        if witness is not None:
            errors.append(
                f"{prefix}{what}: non-exhaustive — no alternative matches "
                f"`{_show_row(witness)}`{place}"
            )
    except MatchError:
        # A malformed pattern — unknown constructor, wrong arity.  The
        # desugarer reports those, and with the source span; saying it
        # twice, worse, helps nobody.
        return []
    return errors


def _validate(row: list, cons: dict[str, ConInfo]) -> None:
    """Reject a row whose constructors do not exist or take other arities."""
    stack = list(row)
    while stack:
        p = stack.pop()
        if isinstance(p, Ctor):
            if len(p.args) != _arity(p.key, cons):
                raise MatchError(f"arity mismatch for {p.key}")
            stack.extend(p.args)


# ---------------------------------------------------------------------------
# Walking a program
# ---------------------------------------------------------------------------

def _subvals(v):
    """Every immediate sub-``Val`` of ``v``, read off its dataclass fields."""
    if not is_dataclass(v):
        return []
    out = []
    for f in fields(v):
        val = getattr(v, f.name)
        if isinstance(val, Val):
            out.append(val)
        elif isinstance(val, (list, tuple)):
            for item in val:
                if isinstance(item, Val):
                    out.append(item)
                elif isinstance(item, tuple):
                    out.extend(x for x in item if isinstance(x, Val))
                elif hasattr(item, "body") and isinstance(item.body, Val):
                    out.append(item.body)      # VAlt / VSCEqn
    return out


def _all_vals(root):
    stack = [root]
    while stack:
        v = stack.pop()
        yield v
        stack.extend(_subvals(v))


def _check_equations(eqs: list, cons: dict[str, ConInfo], name: str) -> list[str]:
    """Check one definition's equations, and every ``case`` in their bodies."""
    errors: list[str] = []
    if eqs and eqs[0].params:
        errors.extend(check_matrix([list(eq.params) for eq in eqs],
                                   cons, "definition", name, at(eqs[0])))
    for eq in eqs:
        for v in _all_vals(eq.body):
            if isinstance(v, VCase):
                errors.extend(check_matrix([[a.pat] for a in v.alts],
                                           cons, "case", name, at(v)))
    return errors


def check_program(program: Program) -> list[str]:
    """Check every definition and every ``case`` in ``program``."""
    cons = program.cons
    errors: list[str] = []
    for sc in program.scs:
        errors.extend(_check_equations(sc.equations, cons, sc.name))
    for inst in program.instances:
        for mname, eqn in inst.methods.items():
            errors.extend(_check_equations(
                [eqn], cons, f"instance {inst.class_name}.{mname}"))
    return errors
