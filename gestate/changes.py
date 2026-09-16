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

**The decision is the language's, since 2026-09-16** —
`card:types-in-the-host.md`, shape (c).  Which of the five shapes a type's
zero change has is `gestate/rules.ges`' `zeroShape`, over a `Type`
value the compiler reads back from the inferred type (`stage.reflect`);
this module builds the expression the shape says and nothing more.  A
type with a variable in it is refused there rather than answered `()`
(Q4), and a type the rule cannot name is a complaint, not a guess.
"""

from __future__ import annotations


from .expr import (
    Alter, EAp, ECase, ECon, EGlobal, ELambda, ENum, EProj, ETuple, EVar,
    Expr,
)
from .types import (
    TApp, TCon, TFun, TVar, Type, _apply_subst_map, tuple_parts,
)


#: complaint  machine — the rule in `rules.ges` and this builder disagree about a shape; nothing an author wrote can reach it
class ChangesError(Exception):
    """`zeroShape` answered something this module cannot build."""


#: `()`.  The unit type has one value and it carries no information, so it
#: compiles to the machine's cheapest nullary form.  `spec/data.md` §I.4
#: says `Pack 0 0`; in gestate tag 0 is an ordinary constructor's tag
#: (`Nil`, as it happens), and being distinguishable from the empty set is
#: the entire point of `fixme.md` F3 — so it is a number instead.  Nothing
#: ever inspects it: a value of type `1` is determined by its type.
UNIT: Expr = ENum(0)


def _key(term):
    return term if not isinstance(term, (list, tuple)) else \
        tuple(_key(a) for a in term)


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

    __slots__ = ("cons", "dummies", "sets", "_by_type", "_generated",
                 "_shapes", "_adts")

    def __init__(self, cons: dict):
        self.cons = cons
        #: suffix → (the type, whose definition first asked for it)
        self.dummies: dict[str, tuple[Type, str]] = {}
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
        #: The rule's answer per reflected type — six distinct types in a
        #: compile of the game, twenty-eight asks.
        self._shapes: dict = {}
        #: The names the rule is told have constructors, when first asked.
        self._adts = None

    # -- the rule -----------------------------------------------------------

    def shape(self, t: Type, place: str = ""):
        """What `rules.ges` says the zero change at `t` is — a term:
        `("ZUnit",)`, `("ZBottom",)`, `("ZPair", [shapes])`, `("ZDummy",)`,
        `("ZFun", shape)`.  Refuses a type with a variable in it, with
        the type and the place named (`stage.reflect`; `place` is the
        transform's, `` in `f` (at 12:0)``)."""
        from .show import show_type
        from .stage import ask, reflect

        term = reflect(t, place=f", the zero change at `{show_type(t)}`{place}")
        key = _key(term)
        got = self._shapes.get(key)
        if got is None:
            if self._adts is None:
                self._adts = sorted(self._by_type)
            got = ask("zeroShape", self._adts, term)
            self._shapes[key] = got
        return got

    # -- the zero change ----------------------------------------------------

    def zero(self, t: object, value: Expr | None = None,
             place: str = "") -> Expr:
        """The zero change at type ``t``, of the value ``value``.

        ``value`` is needed only where the change type follows the value's
        shape — a sum's tag, a function's result.  Where it is unavailable
        (an unannotated node) the answer degrades to `()`, which is what a
        change nothing can describe amounts to.  ``place`` is whose
        definition asked, for the refusal.
        """
        if not isinstance(t, Type):
            return UNIT
        return self._build(self.shape(t, place), t, value, place)

    def _build(self, shape, t: Type, value: Expr | None,
               place: str = "") -> Expr:
        """The expression a shape says, walked beside the type it is the
        shape of — the type names the helper (`bottom_X`, `dummy_X`)
        and the value is threaded to where the shape needs it."""
        from .helpers import _type_suffix

        head = shape[0]
        if head == "ZUnit":
            return UNIT
        if head == "ZBottom":
            suffix = _type_suffix(t)
            self.sets[suffix] = t
            return EGlobal(f"bottom_{suffix}")
        if head == "ZPair":
            # `Δ(A×B) = ΔA × ΔB`, componentwise.
            parts = tuple_parts(t)
            if parts is None or len(parts) != len(shape[1]):
                #: complaint  machine — the rule said a tuple's shape for a type that is not one, or not that wide: `rules.ges` and the reflector disagree
                raise ChangesError(
                    f"`zeroShape` answered a pair of {len(shape[1])} for "
                    f"`{t}`, which is not that tuple")
            n = len(parts)
            return ETuple([
                self._build(sh, p, None if value is None
                            else EAp(EProj(i, n), value), place)
                for i, (sh, p) in enumerate(zip(shape[1], parts))
            ])
        if head == "ZFun":
            # `Δ(A→B) = □A → ΔA → ΔB`.  fig. 3.5's `dummyA→B f = λx. dummy
            # (f x)` — the one place a zero change has to *call* the value
            # it is the change of, to get a result of the right shape.
            if not isinstance(t, TFun):
                #: complaint  machine — the rule said a function's shape for a type that is not an arrow
                raise ChangesError(
                    f"`zeroShape` answered a function's shape for `{t}`")
            if value is None:
                return UNIT
            return ELambda(["_zx", "_zdx"],
                           self._build(shape[1], t.ret,
                                       EAp(value, EVar("_zx")), place))
        if head == "ZDummy":
            # A sum: the tag must be reproduced, so this is the generated
            # `dummyA`.  Without the value there is nothing to reproduce.
            if value is None:
                return UNIT
            suffix = _type_suffix(t)
            self.dummies[suffix] = (t, place)
            return EAp(EGlobal(f"dummy_{suffix}"), value)
        #: complaint  machine — a shape `rules.ges` does not declare
        raise ChangesError(f"`zeroShape` answered `{head}`, which is no shape")

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
            pending = [(s, tp) for s, tp in self.dummies.items()
                       if s not in self._generated]
            if not pending:
                return out
            for suffix, (t, place) in pending:
                self._generated.add(suffix)
                out.append(self._gen_dummy(suffix, t, place))

    def _gen_dummy(self, suffix: str, t: Type,
                   place: str = "") -> tuple[str, int, ELambda]:
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
                self.zero(_apply_subst_map(f, sub), EVar(n),
                          f"{place}, a field of `{info.name}`")
                for f, n in zip(fields, names)
            ])))
        return (f"dummy_{suffix}", 1,
                ELambda(["_zv"], ECase(EVar("_zv"), alts)))
