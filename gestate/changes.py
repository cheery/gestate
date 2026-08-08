"""Zero changes — `()`, `⊥`, and `dummy` (`spec/data.md` §I.4.2, §I.4.3).

δ has to produce a *zero change* in several places: the change of a box
(`δ[e] = ()`), the change of a literal, the `dx` a `for` binds for its
element, and the value a `case`'s never-taken branch returns.  Each of
those lives at a definite type, and the zero change at a type is fixed by
the change structure:

======================  ===================================================
`ΔΦ□A = 1`, `ΔInt = 1`  `()` — nothing about the value can change
`Δ{A} = {A}`            `⊥`, the empty set (lemma 20)
`Δ(A×B) = ΔA × ΔB`      the pair of zero changes
`Δ(A+B) = ΔA + ΔB`      `dummy (ini x) = ini (dummy x)` — needs the *value*,
                        because the tag has to be reproduced (fig. 3.5)
`Δ(A→B) = □A → ΔA → ΔB` `λx. λdx. dummy (f x)` — the one non-inductive case
======================  ===================================================

Until this module existed every one of those was `bottom_Set_Int`
(`fixme.md` F3, F4).  That is invisible at run time — a nullary
constructor is a nullary constructor, and gestate's `⊥` is `Nil` — and
type-incorrect the moment anything looks: a `case` under a `fix` at `L×M`
wants `(⊥,⊥)` and would get the empty set.

The sum case is why `dummyA` is a *generated* function (§I.4.3 lists it
alongside `eqA`/`unionA`): the tag comes from the value, so it cannot be
folded to a constant, and a recursive type needs a recursive helper.
Everything else is built inline, which matters for `spec/errata.md` D3:
`⊥`-propagation recognises the `⊥` it can delete work with, and would not
recognise a call.
"""

from __future__ import annotations

from .expr import (
    Alter, EAp, ECase, ECon, EGlobal, ELambda, ENum, EProj, ETuple, EVar,
    Expr,
)
from .types import (
    TApp, TCon, TFun, TVar, Type, _apply_subst_map, free_vars, tuple_parts,
)


#: `()`.  The unit type has one value and it carries no information, so it
#: compiles to the machine's cheapest nullary form.  `spec/data.md` §I.4
#: says `Pack 0 0`; in gestate tag 0 is an ordinary constructor's tag
#: (`Nil`, as it happens), and being distinguishable from the empty set is
#: the entire point of `fixme.md` F3 — so it is a number instead.  Nothing
#: ever inspects it: a value of type `1` is determined by its type.
UNIT: Expr = ENum(0)


def _spine(t: Type) -> tuple[Type, list[Type]]:
    args: list[Type] = []
    while isinstance(t, TApp):
        args.insert(0, t.arg)
        t = t.fn
    return t, args


class Changes:
    """Builds zero changes, and remembers the helpers they need.

    ``dummies`` and ``sets`` are the requests: the ADT types that need a
    generated `dummy_X`, and the set types whose `bottom_X` was
    referenced.  The pipeline emits both after the transform, because
    which ones are needed is not known until δ has run.
    """

    __slots__ = ("cons", "dummies", "sets", "_by_type", "_generated")

    def __init__(self, cons: dict):
        self.cons = cons
        self.dummies: dict[str, Type] = {}
        self.sets: dict[str, Type] = {}
        #: Already emitted, so `generate` can be called again for whatever
        #: the last round asked for.
        self._generated: set[str] = set()
        #: type name → its constructors, for the sum case.
        self._by_type: dict[str, list] = {}
        for info in cons.values():
            ret = info.type_
            while isinstance(ret, TFun):
                ret = ret.ret
            head, _ = _spine(ret)
            if isinstance(head, TCon):
                self._by_type.setdefault(head.name, []).append(info)

    # -- the zero change ----------------------------------------------------

    def zero(self, t: object, value: Expr | None = None) -> Expr:
        """The zero change at type ``t``, of the value ``value``.

        ``value`` is needed only where the change type follows the value's
        shape — a sum's tag, a function's result.  Where it is unavailable
        (an unannotated node) the answer degrades to `()`, which is what a
        change nothing can describe amounts to.
        """
        from .helpers import _type_suffix

        if not isinstance(t, Type):
            return UNIT
        if free_vars(t):
            # A change at an unknown type.  Helpers are generated per
            # monomorphic type (`spec/errata.md` D9), so there is nothing
            # to call; the places this arises are the polymorphic
            # prelude's dead branches.
            return UNIT

        parts = tuple_parts(t)
        if parts is not None:
            # `Δ(A×B) = ΔA × ΔB`, componentwise.
            n = len(parts)
            return ETuple([
                self.zero(p, None if value is None
                          else EAp(EProj(i, n), value))
                for i, p in enumerate(parts)
            ])

        if isinstance(t, TFun):
            # `Δ(A→B) = □A → ΔA → ΔB`.  fig. 3.5's `dummyA→B f = λx. dummy
            # (f x)` — the one place a zero change has to *call* the value
            # it is the change of, to get a result of the right shape.
            if value is None:
                return UNIT
            return ELambda(["_zx", "_zdx"],
                           self.zero(t.ret, EAp(value, EVar("_zx"))))

        head, args = _spine(t)
        if isinstance(head, TCon) and head.name == "Set":
            suffix = _type_suffix(t)
            self.sets[suffix] = t
            return EGlobal(f"bottom_{suffix}")

        if isinstance(head, TCon) and head.name in self._by_type:
            # A sum: the tag must be reproduced, so this is the generated
            # `dummyA`.  Without the value there is nothing to reproduce.
            if value is None:
                return UNIT
            suffix = _type_suffix(t)
            self.dummies[suffix] = t
            return EAp(EGlobal(f"dummy_{suffix}"), value)

        # `Int`, `Char`, `Cyclic n`, `lo .. hi`, `□A`, and every Rizzo
        # former: discrete, so `ΔA = 1` (`spec/errata.md` D8).
        return UNIT

    # -- the generated helpers ----------------------------------------------

    def generate(self) -> list[tuple[str, int, ELambda]]:
        """`dummy_X` for every ADT a zero change was asked for.

            dummy_T v = case v of (Cᵢ x₁ … xₖ ▹ Cᵢ (dummy x₁) … (dummy xₖ))ᵢ

        Generating one may ask for another — a recursive type asks for
        itself, which is why this is a worklist and why the name is
        recorded before the body is built.
        """
        from .helpers import _type_suffix

        out: list[tuple[str, int, ELambda]] = []
        while True:
            pending = [(s, t) for s, t in self.dummies.items()
                       if s not in self._generated]
            if not pending:
                return out
            for suffix, t in pending:
                self._generated.add(suffix)
                out.append(self._gen_dummy(suffix, t))

    def _gen_dummy(self, suffix: str, t: Type) -> tuple[str, int, ELambda]:
        head, args = _spine(t)
        assert isinstance(head, TCon)
        alts: list[Alter] = []
        for info in self._by_type[head.name]:
            fields, ret = [], info.type_
            while isinstance(ret, TFun):
                fields.append(ret.arg)
                ret = ret.ret
            _, params = _spine(ret)
            # The constructor's fields are written in the declaration's
            # parameters; this use fixes them.  `Maybe Int`'s field is
            # `Int`, not `a`.
            sub = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
            names = [f"_z{i}" for i in range(len(fields))]
            alts.append(Alter(info.tag, names, ECon(info.tag, [
                self.zero(_apply_subst_map(f, sub), EVar(n))
                for f, n in zip(fields, names)
            ])))
        return (f"dummy_{suffix}", 1,
                ELambda(["_zv"], ECase(EVar("_zv"), alts)))
