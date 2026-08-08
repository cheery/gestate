"""Enforce Datafun's four type subgrammars (thesis fig. 2.1).

    eqtypes         A, B ::= {A}_eq | 1 | A×B | A+B
    semilattices    L, M ::= {A}_eq | 1 | L×M
    finite eqtypes  A, B ::= {A}_fin | 1 | A×B | A+B
    fixtypes        L, M ::= {A}_fin | 1 | L×M

`spec/data.md` §II.1 calls not extending these with the Rizzo formers
"the one edit that makes the union sound": a `Sig A` is then automatically
never comparable with `=`, never a `fix`/`∨`/`⊥` target, and never a set
element — no side conditions to state, and none to prove.

Three checks, one per rule of fig. 2.3 that gestate can reach:

  * `set`  — `{eᵢ} : {A}_eq` needs `A` an eqtype.  The runtime keeps a
    sorted list, so the elements must be comparable at all.
  * `join` — `e \\/ f : L` needs `L` a semilattice.
  * `for`  — `for (x ∈ e) f : L` eliminates into a *semilattice*, not
    only into sets.  `Int` is not one, and used to reach the G-machine
    and die there.
  * `fix`  — `fix e : fixL` needs a **fixtype**: sets of *finite* eqtypes.
    Footnote 2 on p. 16 is explicit that integers are an eqtype but not a
    finite one, so `{Int}` has infinite ascending chains and the
    iteration `⊥ ⩽ f ⊥ ⩽ f (f ⊥) ⩽ …` need not stabilise.

The `fix` rule is the one users notice, because every Datafun example in
the literature is written over `{Int}`.  It is not a formality: `fix Box
(r => for (x in r) {x + 1})` at `{Int}` diverges, and gestate has finite
integer types (`Cyclic n`, `Bounded lo hi`) that make the same program
terminate.  `spec/errata.md` D1 asked for this restriction to be either
stated or explicitly dropped; it is stated.
"""

from __future__ import annotations

from .expr import EFix, EFor, EJoin, ESet, Expr, subexprs
from .show import show_type
from .types import (
    Type, is_eqtype, is_fixtype, is_finite_eqtype, is_semilattice,
    why_not_eqtype,
)


def check_scs(scs, cons: dict) -> list[str]:
    """Check every supercombinator; return one message per violation."""
    errors: list[str] = []
    for name, _arity, lam, _sig in scs:
        _walk(lam.body, cons, str(name), errors)
    return errors


def _walk(e: Expr, cons: dict, sc: str, errors: list[str]) -> None:
    if isinstance(e, ESet) and isinstance(e.set_type, Type):
        elem = _set_elem(e.set_type)
        if elem is not None and not is_eqtype(elem, cons):
            errors.append(
                f"{sc}: a set element must be an eqtype, but "
                f"{show_type(elem)} is {why_not_eqtype(elem)}.  Sets are "
                f"compared and deduplicated by equality, and the Rizzo "
                f"types deliberately have none"
            )

    elif isinstance(e, EJoin) and isinstance(e.set_type, Type):
        if not is_semilattice(e.set_type, cons):
            errors.append(
                f"{sc}: `\\/` is the semilattice join, but "
                f"{show_type(e.set_type)} has none"
            )

    elif isinstance(e, EFor) and isinstance(e.result_type, Type):
        if not is_semilattice(e.result_type, cons):
            errors.append(
                f"{sc}: `for` eliminates into a semilattice — it joins one "
                f"result per element and needs ⊥ for the empty set — but "
                f"its body has type {show_type(e.result_type)}, which has "
                f"no join"
            )

    elif isinstance(e, EFix) and isinstance(e.set_type, Type):
        t = e.set_type
        if not is_fixtype(t, cons):
            errors.append(
                f"{sc}: `fix` needs a fixtype and {show_type(t)} is not "
                f"one.  {_fix_hint(t, cons)}"
            )

    for child in subexprs(e):
        _walk(child, cons, sc, errors)


def _set_elem(t: Type):
    from .types import TApp, TCon
    if isinstance(t, TApp) and isinstance(t.fn, TCon) and t.fn.name == "Set":
        return t.arg
    return None


def _fix_hint(t: Type, cons: dict) -> str:
    """Say which of the two conditions failed, and what to do about it."""
    elem = _set_elem(t)
    if elem is None:
        return ("A fixtype is a set of finite eqtypes, or a tuple of "
                "those — `fix` iterates to a least fixed point, so it "
                "needs ⊥ and a join to iterate over.")
    if not is_eqtype(elem, cons):
        return (f"{show_type(elem)} is {why_not_eqtype(elem)}, so it is "
                f"not even an eqtype.")
    if not is_finite_eqtype(elem, cons):
        return (f"{show_type(elem)} is an eqtype but not a *finite* one, "
                f"so {show_type(t)} has infinite ascending chains and the "
                f"iteration need not stabilise.  Use a bounded element "
                f"type — `Cyclic n`, `4 .. 30`, `Bool`, or a non-recursive "
                f"data type built from those.")
    return "A fixtype is a set of finite eqtypes, or a tuple of those."
