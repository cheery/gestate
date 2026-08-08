"""⊥-propagation — the pass that makes seminaïve evaluation pay off.

`spec/errata.md` D3, thesis §4.2.3 and fig. 4.1.  ϕ/δ on its own buys
"roughly 20%": the derivative of a term that cannot change is still *built*
and still *iterated over*, so the asymptotics do not move.  The speedup
comes from noticing that those derivatives are ⊥ and deleting the work.

The rewrites, all from fig. 4.1:

===========================  ==========================================
``e ∨ ⊥``, ``⊥ ∨ e``         ``e``
``for (x ∈ e) ⊥``            ``⊥``
``for (x ∈ ⊥) e``            ``⊥``
``let x = ⊥ in e``           ``e{x ↦ ⊥}``
``let x = e in ⊥``           ``⊥``
===========================  ==========================================

``for (x ∈ e) ⊥ ⇝ ⊥`` is the one that matters — it turns a loop whose
length grows with the input into constant work.  ``let x = ⊥ in e`` is what
carries a zero change inward to reach it, which is the *⊥-insertion* half
of D3: rather than a separate marking pass, the zeros δ already emits
(`fixme.md` F3's `ctx.zero()`) are substituted into place and the other
rules fire on them.

The pass runs between ϕ/δ and Datafun desugaring, while `EJoin`/`EFor` are
still nodes.  Afterwards they are calls to generated helpers and nothing
short of an inliner could see through them.
"""

from __future__ import annotations

from .expr import (
    EAp, EFor, EGlobal, EJoin, ELet, ESet, Expr, map_children,
)
from .match import count_var, subst_var
from .types import Type


#: Generated ⊥ is a nullary global named after its semilattice.
_BOTTOM_PREFIX = "bottom_"


def is_bottom(e: Expr) -> bool:
    """Is ``e`` syntactically ⊥?

    An empty set literal counts: `{}` *is* ⊥ at a set type, and writing it
    is how a Datalog query spells its base case when a branch contributes
    nothing.
    """
    if isinstance(e, EGlobal):
        return isinstance(e.name, str) and e.name.startswith(_BOTTOM_PREFIX)
    return isinstance(e, ESet) and not e.items


def bottom_of(t: object) -> Expr | None:
    """The ⊥ of semilattice ``t``, or ``None`` if the type is not known."""
    from .helpers import _type_suffix

    if not isinstance(t, Type):
        return None
    return EGlobal(f"{_BOTTOM_PREFIX}{_type_suffix(t)}")


def propagate(e: Expr, _fuel: int = 64) -> Expr:
    """Rewrite ``e`` to a fixed point of the ⊥ rules."""
    e = map_children(e, lambda c: propagate(c, _fuel))

    if _fuel <= 0:
        return e

    if isinstance(e, EJoin):
        # `e ∨ ⊥ = e`.  The annotation is dropped with the node; nothing
        # downstream needs it once the join is gone.
        if is_bottom(e.left):
            return propagate(e.right, _fuel - 1)
        if is_bottom(e.right):
            return propagate(e.left, _fuel - 1)
        return e

    if isinstance(e, EFor):
        # A big join of ⊥ is ⊥, and so is a big join over no elements.
        if is_bottom(e.body) or is_bottom(e.set_expr):
            bot = bottom_of(e.result_type)
            if bot is not None:
                return bot
        return e

    if isinstance(e, ELet) and not e.is_rec:
        # `let x = e in ⊥ = ⊥` — the binding cannot be forced.
        if is_bottom(e.body):
            return e.body
        body = e.body
        kept: list[tuple] = []
        changed = False
        for name, defn in e.defs:
            # `let x = ⊥ in f = f{x ↦ ⊥}`.  Substituting rather than
            # keeping the binding is the point: it puts a ⊥ where the
            # `for` and `∨` rules can see it.
            if is_bottom(defn) and count_var(body, name) <= _SUBST_LIMIT:
                body = subst_var(body, name, defn)
                changed = True
            else:
                kept.append((name, defn))
        if changed:
            rebuilt = ELet(False, kept, body) if kept else body
            return propagate(rebuilt, _fuel - 1)
        return e

    return e


#: A ⊥ is a nullary global, so duplicating it costs nothing at run time and
#: the cap only guards against pathological code size.
_SUBST_LIMIT = 32


def propagate_scs(scs: list) -> list:
    """Run the pass over every supercombinator body."""
    from .expr import ELambda

    out = []
    for name, arity, lam, sig in scs:
        out.append((name, arity,
                    ELambda(list(lam.params), propagate(lam.body)), sig))
    return out
