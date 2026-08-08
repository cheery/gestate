"""The monotone/discrete variable discipline (thesis fig. 2.3).

Datafun has two variable flavours: `X : A` is *monotone* and may only be
used in ways that respect the ordering on `A`; `x :: A` is *discrete* and
may be used any way at all.  It is enforced by variable hygiene rather
than by a judgement: a *non-monotone* expression is checked in the
stripped context

        ⌈ε⌉ = ε        ⌈Γ, X : A⌉ = ⌈Γ⌉        ⌈Γ, x :: A⌉ = ⌈Γ⌉, x :: A

so a monotone variable simply is not in scope inside one.  The rules that
strip, of those gestate has: `box` (`⌈Γ⌉ ⊢ e : A ⟹ Γ ⊢ [e] : □A`), `set`
(`⌈Γ⌉ ⊢ eᵢ : A_eq`), and the argument of a discrete arrow — `A -> B` is
Datafun's `□A → B`, whose argument goes under a box.

Where the flavours come from:

  * `λ` checked at `A ~> B` binds monotone; at `A -> B`, discrete.
  * `case e of (inᵢ Xᵢ ▹ fᵢ)ᵢ` binds monotone.
  * `for (x ∈ e) f` binds **discrete** — `Γ, x :: A_eq ⊢ f : L`.  This is
    what lets fig. 2.2 desugar a pattern clause to `if p ⩿ x then …`,
    which is an equality test and so non-monotone.
  * `let [x] = e in f` binds discrete.

Both flavours coincide at a type whose order is discrete: `x ⩽ y ⟺ x = y`
makes every function out of it monotone.  Inference applies that (see
`types.has_nontrivial_order`) before marking anything monotone, so
ordinary code — where every type is `Int`, `Bool`, `Sig A`, … — never
meets this pass at all.  Sets are the one former with a real order, so
`{A}` is where the discipline has teeth, and that is exactly where
Datafun needs it.
"""

from __future__ import annotations

from .expr import (
    EAp, EBox, ECase, EFor, EGFix, ELambda, ELet, ESet, EUnbox, EVar, Expr,
    subexprs,
)


def check_scs(scs) -> list[str]:
    """Check every supercombinator; return one message per violation."""
    errors: list[str] = []
    for name, _arity, lam, _sig in scs:
        mono = frozenset(str(p) for p in getattr(lam, "mono", frozenset()))
        disc = frozenset(str(p) for p in lam.params) - mono
        _walk(lam.body, mono, disc, {}, str(name), errors)
    return errors


def _walk(e: Expr, mono: frozenset, disc: frozenset,
          stripped: dict, sc: str, errors: list[str]) -> None:
    """Walk ``e``.

    ``stripped`` maps a name removed from scope to the construct that
    removed it, so the message can say why rather than merely that.
    """
    if isinstance(e, EVar):
        name = str(e.name)
        if name in stripped and name not in mono and name not in disc:
            errors.append(
                f"{sc}: '{name}' is a monotone variable and cannot be used "
                f"in {stripped[name]}, which is checked in the stripped "
                f"context.  Monotone variables may only be used in ways "
                f"that respect the ordering on their type; bind it "
                f"discretely first (`unbox`, or a `->` rather than `~>` "
                f"parameter)"
            )
        return

    if isinstance(e, EBox):
        _walk(e.body, frozenset(), disc, _strip(mono, stripped, "a box"),
              sc, errors)
        return

    if isinstance(e, ESet):
        # `⌈Γ⌉ ⊢ eᵢ : A_eq` — a set literal's elements are compared for
        # equality, which is not monotone.
        gone = _strip(mono, stripped, "a set literal")
        for item in e.items:
            _walk(item, frozenset(), disc, gone, sc, errors)
        return

    if isinstance(e, EAp):
        _walk(e.fn, mono, disc, stripped, sc, errors)
        if e.discrete_arg:
            # `A -> B` is `□A → B`: the argument is boxed, so it strips.
            _walk(e.arg, frozenset(), disc,
                  _strip(mono, stripped, "the argument of an ordinary "
                                         "(`->`) function"), sc, errors)
        else:
            _walk(e.arg, mono, disc, stripped, sc, errors)
        return

    if isinstance(e, EUnbox):
        _walk(e.binding, mono, disc, stripped, sc, errors)
        _walk(e.body, mono, disc | {str(e.var)}, stripped, sc, errors)
        return

    if isinstance(e, EFor):
        # `for` binds *discrete* — see the module docstring.
        _walk(e.set_expr, mono, disc, stripped, sc, errors)
        _walk(e.body, mono, disc | {str(e.var)}, stripped, sc, errors)
        return

    if isinstance(e, ELambda):
        lam_mono = frozenset(str(p) for p in e.mono)
        lam_disc = frozenset(str(p) for p in e.params) - lam_mono
        _walk(e.body, mono | lam_mono, disc | lam_disc, stripped, sc, errors)
        return

    if isinstance(e, ECase):
        _walk(e.scrut, mono, disc, stripped, sc, errors)
        for alt in e.alts:
            alt_mono = frozenset(str(n) for n in alt.mono)
            alt_disc = frozenset(str(n) for n in alt.names) - alt_mono
            _walk(alt.body, mono | alt_mono, disc | alt_disc, stripped,
                  sc, errors)
        return

    if isinstance(e, ELet):
        # A `let` binder is discrete.  Datafun has no `let` of its own —
        # fig. 2.2 desugars it to `(λx. f) e` — but the binders that reach
        # here are compiler-introduced (`unbox`'s pair, `for`'s zero
        # change, the sharing `_pe`/`_de` in δ), and those name a value
        # rather than abstract over it.
        inner = disc
        for name, defn in e.defs:
            _walk(defn, mono, inner if e.is_rec else disc, stripped, sc, errors)
            inner = inner | {str(name)}
        _walk(e.body, mono, inner, stripped, sc, errors)
        return

    if isinstance(e, EGFix):
        _walk(e.body, mono, disc | {str(e.var)}, stripped, sc, errors)
        return

    for child in subexprs(e):
        _walk(child, mono, disc, stripped, sc, errors)


def _strip(mono: frozenset, stripped: dict, what: str) -> dict:
    """`⌈Γ⌉`: record why each monotone variable left scope."""
    if not mono:
        return stripped
    gone = dict(stripped)
    for name in mono:
        gone[name] = what
    return gone
