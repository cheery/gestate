"""Seminaïve evaluation — ϕ/δ transform (data.md Part I).

The ϕ (speed-up) and δ (derivative) transforms run once at compile time,
before lambda lifting.  Both are ``Expr → Expr`` — the output is ordinary
``Expr`` that compiles through the existing codegen unchanged.

``fix`` is replaced by ``semifix``, and boxes become pairs ``(ϕe, δe)``.

The transform generates ``f_phi`` where ϕ has something to do, and
``f_delta`` where something differentiates a call to ``f`` — see `Plan`.
It used to generate both for every supercombinator in the program, which
doubled it (`fixme.md` F7).

No new G-machine instructions are needed.
"""

from __future__ import annotations

from .expr import (
    Alter,
    EAnnot,
    EAp,
    EBox,
    ECase,
    ECon,
    EFix,
    EFor,
    EGlobal,
    EJoin,
    ELambda,
    ELet,
    ESet,
    EUnbox,
    EVar,
    ENum,
    ETuple,
    EChr,
    EProj,
    Expr,
    Name,
    map_children,
    subexprs,
)
from .changes import UNIT, Changes
from .declarations import ConInfo


# ---------------------------------------------------------------------------
# Context — tracks which names are in scope and their change-parameter names
# ---------------------------------------------------------------------------

class SeminaiveError(Exception):
    pass


class SeminaiveCtx:
    """Maps variable names to their δ change-parameter names, and carries
    the change-structure builder every zero change goes through.

    Each binding records the □-nesting depth it was made at.  A variable
    bound *outside* the enclosing box has a **zero change** inside it:
    `ϕ[e] = [(ϕe, δe)]` is the only place ϕ calls δ, and the δ it builds
    is consumed by `semifix`, which varies only its own accumulator.
    Everything the box closes over is constant for the whole iteration, so
    its change is ⊥ — which is also what `spec/errata.md` D3 means by "ϕ
    marks the terms δ is known to produce as zero changes".

    Without this the box body asks for a `dx` that no enclosing lambda
    bound (`ϕ(λX. e) = λX. ϕe` gives a lambda no change parameters), and
    the reference escapes to the lambda lifter.
    """

    __slots__ = ("_changes", "_depth", "zero_suffix", "changes", "plan")

    def __init__(self, changes: dict | None = None, depth: int = 0,
                 zero_suffix: str = "Set_Int", builder=None,
                 plan=None):
        self._changes: dict[str, tuple[str, int]] = changes or {}
        self._depth = depth
        #: Where a zero change goes when the tree does not record its
        #: type.  One case is left: a variable referenced inside a box and
        #: bound outside it has a zero change at *its* type, and an `EVar`
        #: does not carry one.  Every other zero is built at its own type
        #: by `changes` (`fixme.md` F3).  Parking this one on a generated
        #: bottom keeps it well-formed wherever a set is expected, which
        #: is where it lands in practice — `f s = fix [r ⇒ s ∨ …]`.
        self.zero_suffix = zero_suffix
        #: The change-structure builder (`gestate/changes.py`).
        self.changes = builder if builder is not None else Changes({})
        #: Which supercombinators this run is generating each half for —
        #: the only names a reference may be renamed to.  ``None`` means
        #: "ask `_is_user_sc`", which is a guess and is only for direct
        #: calls to `phi`/`delta`.
        self.plan = plan

    def bind(self, name: str, chg_name: str) -> SeminaiveCtx:
        changes = dict(self._changes)
        changes[name] = (chg_name, self._depth)
        return SeminaiveCtx(changes, self._depth, self.zero_suffix,
                            self.changes, self.plan)

    def enter_box(self) -> SeminaiveCtx:
        """The context inside a `□`: everything bound so far is constant."""
        return SeminaiveCtx(self._changes, self._depth + 1, self.zero_suffix,
                            self.changes, self.plan)

    def has_phi(self, name: Name) -> bool:
        """Is there a `name_phi` to rename this reference to?"""
        if self.plan is None:
            return _is_user_sc(name)
        return name in self.plan.phi

    def has_delta(self, name: Name) -> bool:
        """Is there a `name_delta` to rename this reference to?"""
        if self.plan is None:
            return _is_user_sc(name)
        if name in self.plan.delta:
            return True
        if name in self.plan.scs:
            # The gate promised nothing would differentiate this one.  A
            # zero change here would be a lie that shows up as `unknown
            # global` or worse, so say which supercombinator went missing.
            raise SeminaiveError(
                f"internal: δ needs a derivative of '{name}', which the "
                f"ϕ/δ gate did not plan one for (`fixme.md` F7)"
            )
        return False

    def zero(self) -> Expr:
        return EGlobal(f"bottom_{self.zero_suffix}")

    def zero_at(self, t: object, value: Expr | None = None) -> Expr:
        """The zero change at type ``t`` — see `gestate/changes.py`."""
        return self.changes.zero(t, value)

    def change_of(self, name: str) -> str | None:
        """The change variable for ``name``, or ``None`` for a zero change."""
        entry = self._changes.get(name)
        if entry is None:
            # Untracked inside a box means bound outside it.
            return None if self._depth else "d" + name
        chg, depth = entry
        return chg if depth == self._depth else None


# ---------------------------------------------------------------------------
# is-user-sc — determines whether a global name refers to a user function
# ---------------------------------------------------------------------------

def _is_user_sc(name: Name) -> bool:
    """Guess whether ``name`` is a user supercombinator.

    A guess, and it was wrong twice: `chr`/`ord` are machine primitives
    that were in none of these lists, and a user definition whose name
    starts with a single `_` is skipped by `transform` while every
    reference to it was still renamed.  Both produced an unknown global
    at run time (`fixme.md` F9).  `transform` therefore passes the set it
    is actually generating pairs for, and this is only the fallback for a
    direct call to `phi`/`delta`.
    """
    return isinstance(name, str) and not name.startswith("_") \
        and not name.startswith("prim_") \
        and not name.startswith(_HELPER_PREFIXES) \
        and name not in _BUILTINS


_BUILTINS = {
    "prim_eq_int", "prim_lt_int", "chr", "ord",
    "Nil", "Cons", "True", "False",
    "Nothing", "Just", "SyncLeft", "SyncRight", "SyncBoth",
    "head", "tail", "delay", "wait", "watch", "sync", "never", "chan",
}

#: Generated Datafun helpers.  Matched by prefix rather than listed, so
#: that one instance per monomorphic type (`bottom_Set_Cyclic_8`, …) does
#: not have to be enumerated here.
_HELPER_PREFIXES = (
    "eq_", "union_", "bottom_", "join_", "diff_", "dummy_",
    "fix_", "fixLoop_", "for_", "semifix_", "semifixL_", "subset_",
)


#: The result type of each primitive, per arity of application.  Filled by
#: `transform` from `pipeline._build_builtins()` so there is one source of
#: truth for what a primitive is and what it returns.
_PRIM_TYPES: dict[str, object] = {}


def _primitive_result(expr, ctx):
    """The result type of ``expr`` if it is a *saturated* primitive call.

    ``None`` when the head is not a primitive, or when it is applied to
    too few arguments — a partially applied primitive is still a function,
    and a function's zero change is not its result's.
    """
    from .types import TFun

    spine, args = expr, 0
    while isinstance(spine, EAp):
        args += 1
        spine = spine.fn
    if not isinstance(spine, EGlobal):
        return None
    t = _PRIM_TYPES.get(str(spine.name))
    if t is None:
        return None
    for _ in range(args):
        if not isinstance(t, TFun):
            return None
        t = t.ret
    return None if isinstance(t, TFun) else t


def _suffix(t, what: str) -> str:
    """The generated-helper suffix for a node's annotated type."""
    from .helpers import _type_suffix
    from .types import Type

    if not isinstance(t, Type):
        raise SeminaiveError(
            f"the type of this {what} did not reach the ϕ/δ transform; "
            f"it should have been annotated during inference"
        )
    return _type_suffix(t)


def _set_of(elem, what: str) -> str:
    from .types import TApp, TCon
    return _suffix(TApp(TCon("Set"), elem), what)


def _interleave_params(params: list) -> list:
    """``[x, y]`` → ``[x, dx, y, dy]`` — a base point and its change, in pairs."""
    out: list = []
    for p in params:
        out.append(p)
        out.append("d" + str(p))
    return out


def _unpack_box(var: str, boxed: Expr, body: Expr) -> Expr:
    """`let [(x, dx)] = boxed in body`.

    `ϕ[e]` is the pair `(ϕe, δe)`; □ is erased at runtime, so unpacking is
    two projections.  The intermediate binder is named after `var` so
    nested unboxes do not shadow one another.
    """
    tmp = f"_box_{var}"
    return ELet(False, [(tmp, boxed)],
                ELet(False, [
                    (var, EAp(EProj(0), EVar(tmp))),
                    ("d" + var, EAp(EProj(1), EVar(tmp))),
                ], body))


# ---------------------------------------------------------------------------
# ϕ — speed-up transform
# ---------------------------------------------------------------------------

def phi(expr: Expr, ctx: SeminaiveCtx) -> Expr:
    if isinstance(expr, EVar):
        return expr
    if isinstance(expr, (ENum, EChr)):
        return expr
    if isinstance(expr, EGlobal):
        if ctx.has_phi(expr.name):
            return EGlobal(str(expr.name) + "_phi")
        return expr
    if isinstance(expr, ECon):
        args = [phi(a, ctx) for a in expr.args]
        return ECon(expr.tag, args)
    if isinstance(expr, ETuple):
        return ETuple([phi(a, ctx) for a in expr.args])
    if isinstance(expr, EAp):
        return EAp(phi(expr.fn, ctx), phi(expr.arg, ctx))
    if isinstance(expr, ELambda):
        new_ctx = ctx
        for p in expr.params:
            new_ctx = new_ctx.bind(p, "d" + p)
        return ELambda(list(expr.params), phi(expr.body, new_ctx))
    if isinstance(expr, ELet):
        if expr.is_rec:
            defs = [(n, phi(d, ctx)) for n, d in expr.defs]
            return ELet(True, defs, phi(expr.body, ctx))
        else:
            new_ctx = ctx
            defs = []
            for n, d in expr.defs:
                defs.append((n, phi(d, new_ctx)))
                new_ctx = new_ctx.bind(n, "d" + n)
            return ELet(False, defs, phi(expr.body, new_ctx))
    if isinstance(expr, ECase):
        scrut = phi(expr.scrut, ctx)
        alts = [Alter(a.tag, list(a.names), phi(a.body, ctx)) for a in expr.alts]
        return ECase(scrut, alts)

    # Box: [e] → [(ϕe, δe)] — a pair
    if isinstance(expr, EBox):
        base = phi(expr.body, ctx)
        change = delta(expr.body, ctx.enter_box())
        return ETuple([base, change])

    # Unbox: let [x] = e in f → let [(x,dx)] = ϕe in ϕf
    #
    # `ϕ[e]` builds the pair `(ϕe, δe)`, so the unpack binds both halves:
    # `x` is the base point and `dx` its change.  This is where a discrete
    # variable's change enters scope — §I.3's `ΦΓ` gives a discrete
    # `x :: A` the pair `x :: ΦA, dx :: ΔΦA`.
    if isinstance(expr, EUnbox):
        binding = phi(expr.binding, ctx)
        new_ctx = ctx.bind(expr.var, "d" + expr.var)
        body = phi(expr.body, new_ctx)
        return _unpack_box(expr.var, binding, body)

    # fix: fix e → semifix ϕe
    if isinstance(expr, EFix):
        suffix = _suffix(expr.set_type, "`fix`")
        return EAp(EGlobal(f"semifix_{suffix}"), phi(expr.body, ctx))

    # for (x ∈ e) f → for (x ∈ ϕe) let [dx] = [0x] in ϕf   (I.4.1)
    #
    # `0x` is `dummy x`, the zero change *at the element type* — not ⊥.
    # They coincide at a set element type (`dummy{A} = {}`) and nowhere
    # else: at `(Int, Int)`, a Datalog relation's element, the zero change
    # is `((), ())`.
    if isinstance(expr, EFor):
        dx_var = "d" + expr.var
        new_ctx = ctx.bind(expr.var, dx_var)
        return EFor(expr.var, phi(expr.set_expr, ctx),
                    ELet(False, [(dx_var, ctx.zero_at(expr.elem_type,
                                                      EVar(expr.var)))],
                         phi(expr.body, new_ctx)),
                    expr.result_type, expr.elem_type)
    if isinstance(expr, ESet):
        return ESet([phi(a, ctx) for a in expr.items], expr.set_type)

    # `ϕ(e ∨ f) = ϕe ∨ ϕf`
    if isinstance(expr, EJoin):
        return EJoin(phi(expr.left, ctx), phi(expr.right, ctx), expr.set_type)

    # Annotations — strip
    if isinstance(expr, EAnnot):
        return phi(expr.expr, ctx)

    # Everything else — the Rizzo formers, chiefly — is rebuilt from its
    # transformed children.  ϕ used to *stop* here and return the node
    # unrecursed, so a `fix` under a `:::` stayed an `EFix` and came out
    # as the naïve loop, against `spec/data.md` §0's "a `fix` buried
    # inside a signal's per-tick body gets seminaïved in place".  δ keeps
    # its own fall-through: a signal's change is not its subterms'.
    return map_children(expr, lambda c: phi(c, ctx))


# ---------------------------------------------------------------------------
# δ — derivative transform
# ---------------------------------------------------------------------------

def delta(expr: Expr, ctx: SeminaiveCtx) -> Expr:
    if isinstance(expr, EVar):
        chg = ctx.change_of(expr.name)
        if chg is not None:
            return EVar(chg)
        # Bound outside the enclosing box, so constant for the whole
        # iteration: the zero change at its own type.  Inference records
        # that type on the occurrence; without it there is nothing to go
        # on and the old designated bottom stands.
        if expr.type_ is None:
            return ctx.zero()
        return ctx.zero_at(expr.type_, expr)
    if isinstance(expr, (ENum, EChr)):
        # `ΔInt = ΔChar = 1`: a literal is the same literal next time.
        return UNIT
    if isinstance(expr, EGlobal):
        if ctx.has_delta(expr.name):
            return EGlobal(str(expr.name) + "_delta")
        if expr.name == "Nil" or str(expr.name).startswith("bottom_"):
            return expr
        # A primitive is discrete (`spec/errata.md` D8), so its change is
        # the unit.  What D8 leaves open is a primitive *function*: `δ(e f)
        # = δe [ϕf] δf` applies this, and `()` takes no arguments.  Such a
        # term is unreachable today — δ of an arithmetic expression only
        # arises under a set literal or a `fix`, whose δ is ⊥ — and the
        # contract that would settle it is stage 1.2's.
        return UNIT
    if isinstance(expr, ECon):
        return ECon(expr.tag, [delta(a, ctx) for a in expr.args])
    if isinstance(expr, ETuple):
        return ETuple([delta(a, ctx) for a in expr.args])
    if isinstance(expr, EAp) and isinstance(expr.fn, EProj):
        # δ(πᵢ e) = πᵢ δe — the table's "distribute".  It has to come
        # before the application rule: a projection is *not* a function,
        # and `δe [ϕf] δf` built `πᵢ ϕe δe`, a projection applied to two
        # arguments, which nothing downstream can compile (`fixme.md`
        # F57).  δ of a tuple is a tuple of the same width, so the index
        # and the width carry over unchanged.
        #
        # `EProj` does double duty in this IR: it also selects a method
        # out of a dictionary, and a dictionary is a compile-time constant
        # whose change is `()`.  `πᵢ ()` is not a projection of anything,
        # so a discrete operand keeps the application path — δ of a
        # *method* is the derivative of a primitive, which is the contract
        # `spec/errata.md` D8 has yet to state.
        d = delta(expr.arg, ctx)
        if d is not UNIT:
            return EAp(EProj(expr.fn.i, expr.fn.width), d)
    if isinstance(expr, EAp):
        # A *saturated primitive* is discrete: every argument type has the
        # trivial change structure (`ΔInt = ΔChar = 1`), so the result
        # cannot change either and its derivative is the zero change at the
        # result type.  This is the rule `spec/errata.md` D8 was missing —
        # `δ(prim_eq_int x y)` is `dummy` at `Bool`, not `() ϕx δx ϕy δy`.
        prim = _primitive_result(expr, ctx)
        if prim is not None:
            return ctx.zero_at(prim, expr)

        # δ(e f) = δe (ϕf) δf
        dfn = delta(expr.fn, ctx)
        if dfn is UNIT:
            # The head is discrete, so its change is `()` — and `()` takes
            # no arguments.  This is the one gap `spec/errata.md` D8 names
            # and does not close: the derivative of a *primitive function*.
            #
            # It used to be emitted anyway.  `UNIT` is `ENum(0)` and
            # `Unwind` on a number ignores the spine, so the application
            # quietly evaluated to `0` and died further on as
            # `CaseJump on non-constructor` — a G-machine error, pointing
            # nowhere near the cause.  Refusing here is stage 0.4's rule:
            # a derivative the plan cannot supply is a compiler error, not
            # a lie.
            raise SeminaiveError(
                "internal: δ needs the derivative of a discrete function, "
                "which has none — its change is `()` and `()` cannot be "
                "applied.  `spec/errata.md` D8 is the contract that would "
                "say what the derivative of a primitive is"
            )
        return EAp(EAp(dfn, phi(expr.arg, ctx)), delta(expr.arg, ctx))
    if isinstance(expr, ELambda):
        # δ(λx. e) = λ[x]. λDX. δe, so nested lambdas *interleave*:
        # `λ[x].λDX.λ[y].λDY.δe`.  That is what `δ(e f) = δe [ϕf] δf`
        # supplies for a curried spine — `f a b` becomes
        # `f_delta ϕa δa ϕb δb`.  Grouping them (`x y dx dy`) agrees only
        # at arity 1, which is why nothing caught it: at arity ≥ 2 every
        # `f_delta` bound `dx₁` to `b` (`fixme.md` F2).
        new_ctx = ctx
        for p in expr.params:
            new_ctx = new_ctx.bind(p, "d" + p)
        return ELambda(_interleave_params(list(expr.params)),
                       delta(expr.body, new_ctx))
    if isinstance(expr, ELet):
        # δ(let x = e in f) = let x = ϕe ; dx = δe in δf
        #
        # Both halves are needed: `δf` may refer to the binding's *value*
        # as well as to its change, and the context promises `dx` exists
        # the moment `x` is bound.  Binding only the change — which is what
        # this did — left every `dx` in the body dangling as far as the
        # lambda lifter was concerned.
        new_ctx = ctx
        defs: list[tuple[Name, Expr]] = []
        for n, d in expr.defs:
            body_ctx = ctx if not expr.is_rec else new_ctx
            defs.append((n, phi(d, body_ctx)))
            defs.append(("d" + str(n), delta(d, body_ctx)))
            new_ctx = new_ctx.bind(str(n), "d" + str(n))
        return ELet(expr.is_rec, defs, delta(expr.body, new_ctx))
    if isinstance(expr, ECase):
        # δ(case e of Cᵢ xᵢ → fᵢ) =                          (I.4.2)
        #   let _de = δe in
        #   case split [ϕe] of
        #     Cᵢ xᵢ → let dxᵢ = case _de of Cᵢ dxᵢ → dxᵢ
        #                                 | Cⱼ _ → dummy xᵢ
        #              in δfᵢ
        #
        # `split [ϕe]` pushes the box inside the sum — `Φ(□(A+B))` is a
        # boxed tagged pair and `Φ(□A+□B)` a tagged boxed pair, a real
        # type mismatch (`spec/errata.md` D7) and not a notational one.
        # □ is erased here (§I.6), so the two coincide at run time and the
        # outer `case ϕe` *is* the split.  What the discrete binding buys
        # is `xᵢ` in scope in the dead branch, which is what `dummy xᵢ`
        # needs.
        #
        # The dead branches are unreachable — a sum is ordered disjointly,
        # so δe's tag always matches ϕe's (§3.3.2) — and are emitted only
        # so every branch returns a value of the change type.  That is
        # exactly why it must be `dummy xᵢ` rather than ⊥: ⊥ is a value at
        # the *set* type, and these branches sit at whatever ΔΦAᵢ is.
        tags_in_order: list[int] = []
        arity_of: dict[int, int] = {}
        for a in expr.alts:
            if a.tag not in arity_of:
                tags_in_order.append(a.tag)
            arity_of[a.tag] = len(a.names)
        _phe = phi(expr.scrut, ctx)
        _de = delta(expr.scrut, ctx)

        def _delta_alt(alt):
            dx_names = [ctx.change_of(nm) for nm in alt.names]
            # `dummy xᵢ`, one per field of *this* branch, in the shape the
            # matching branch produces.  A field whose type inference did
            # not record degrades to `()`.
            types = alt.field_types or ((),) * len(alt.names)
            dummies = [ctx.zero_at(t, EVar(nm))
                       for nm, t in zip(alt.names, types)]
            dead_value: Expr = (dummies[0] if len(dummies) == 1
                                else ETuple(dummies))
            # Dead branches — every tag that is NOT alt.tag, each binding
            # as many fields as its own constructor has.  They all used to
            # bind exactly one, which mis-binds at any other arity.
            dead_alts = [
                Alter(other, ["_"] * arity_of[other], dead_value)
                for other in tags_in_order if other != alt.tag
            ]
            # Matching branch — bind change names from δe
            if dx_names:
                match_body: Expr = EVar(dx_names[0]) if len(dx_names) == 1 \
                    else ETuple([EVar(d) for d in dx_names])
                match_alt = Alter(alt.tag, dx_names, match_body)
                inner = ECase(EVar("_de"), [match_alt] + dead_alts)
                if len(dx_names) == 1:
                    body = ELet(False, [(dx_names[0], inner)],
                                delta(alt.body, ctx))
                else:
                    width = len(dx_names)
                    body = ELet(False, [("_dxt", inner)],
                           ELet(False, [(d, EAp(EProj(i, width), EVar("_dxt")))
                                         for i, d in enumerate(dx_names)],
                                delta(alt.body, ctx)))
            else:
                body = delta(alt.body, ctx)
            return Alter(alt.tag, list(alt.names), body)

        return ELet(False, [("_de", _de)],
                    ECase(_phe, [_delta_alt(a) for a in expr.alts]))

    # Box: δ[e] = () — `ΔΦ□A = 1`, so there is nothing to say.  This used
    # to be the empty set, which is a value at a type `[e]` need not have
    # anything to do with (`fixme.md` F3).
    if isinstance(expr, EBox):
        return UNIT

    # Unbox: let [(x,dx)] = ϕe in δf
    #
    # δ discards ϕe's second half and never looks at δe : 1 — the unpack
    # exists only to bring `dx` into scope for δf (§I.4).
    if isinstance(expr, EUnbox):
        binding = phi(expr.binding, ctx)
        new_ctx = ctx.bind(expr.var, "d" + expr.var)
        return _unpack_box(expr.var, binding, delta(expr.body, new_ctx))

    # fix: δ(fix e) = ⊥ at the fixed point's own type (lemma 20: ΔfixL = fixL)
    if isinstance(expr, EFix):
        return EGlobal(f"bottom_{_suffix(expr.set_type, '`fix`')}")

    if isinstance(expr, EFor):
        # δ(for (x ∈ e) f) =                                      (I.4.1)
        #   (for (x ∈ δe)  let dx = ⊥ in ϕf)                     -- new elements
        # ∨ (for (x ∈ ϕe ∪ δe) let dx = ⊥ in δf)                 -- all elements
        dx_var = "d" + expr.var
        new_ctx = ctx.bind(expr.var, dx_var)
        # Share ϕe, δe via ELet (the union is inlined — compile_let does
        # not allow defs to reference sibling defs).
        result = _suffix(expr.result_type, "`for`")
        set_of_elem = _set_of(expr.elem_type, "`for`")
        zero_x = lambda: ctx.zero_at(expr.elem_type, EVar(expr.var))
        phi_f_body = ELet(False, [(dx_var, zero_x())],
                          phi(expr.body, new_ctx))
        delta_f_body = ELet(False, [(dx_var, zero_x())],
                            delta(expr.body, new_ctx))
        return ELet(False, [
            ("_pe", phi(expr.set_expr, ctx)),
            ("_de", delta(expr.set_expr, ctx)),
        ], EAp(EAp(EGlobal(f"join_{result}"),
                  EFor(expr.var, EVar("_de"), phi_f_body,
                       expr.result_type, expr.elem_type)),
              EFor(expr.var,
                   EAp(EAp(EGlobal(f"union_{set_of_elem}"), EVar("_pe")), EVar("_de")),
                   delta_f_body, expr.result_type, expr.elem_type)))
    # `δ(e ∨ f) = δe ∨ δf` — a deliberate overapproximation (§3.4.6): the
    # precise change is `(δe∖ϕf) ∪ (δf∖ϕe)`, but computing it needs ϕe/ϕf,
    # which is the recomputation seminaive evaluation exists to avoid.
    if isinstance(expr, EJoin):
        return EJoin(delta(expr.left, ctx), delta(expr.right, ctx),
                     expr.set_type)

    if isinstance(expr, ESet):
        # `δ{eᵢ} = ⊥` — a set literal cannot change independently of its
        # own recomputation (§I.4's table).
        return EGlobal(f"bottom_{_suffix(expr.set_type, 'set literal')}")
    if isinstance(expr, EAnnot):
        return delta(expr.expr, ctx)

    return expr


# ---------------------------------------------------------------------------
# Which supercombinators need which half
# ---------------------------------------------------------------------------

#: The constructs ϕ does not leave alone.  Everything else it rebuilds
#: identically, so an SC containing none of these *is* its own ϕ.
_DATAFUN_NODES = (ESet, EFix, EFor, EJoin, EBox, EUnbox)


class Plan:
    """Which supercombinators get a ϕ, and which get a δ (`fixme.md` F7).

    Every SC used to get both, doubling the program — including list
    functions with no set anywhere near them.  The two halves are needed
    for different reasons, and neither implies the other:

    - **ϕ** rewrites `fix` to `semifix`, packs a box as a pair, and binds
      a `for`'s `dx`.  A body with none of those is unchanged by ϕ, so it
      needs no `_phi` and callers can keep calling it by name.
    - **δ** is needed only where something *differentiates* a call to it.
      That is a reachability question, not a syntactic one: `id` has no
      set in it and `fix [r ⇒ id r]` still needs `id_delta`.  ϕ calls δ
      at exactly one place — `ϕ[e] = (ϕe, δe)` — so the demand starts at
      the globals under a box and closes over the call graph.

    `main` typically gets a ϕ and no δ: nothing calls it.
    """

    __slots__ = ("phi", "delta", "scs")

    def __init__(self, phi: frozenset, delta: frozenset, scs: frozenset):
        self.phi = phi
        self.delta = delta
        self.scs = scs

    @staticmethod
    def of(bodies: dict[str, ELambda]) -> "Plan":
        phi = {n for n, lam in bodies.items() if _mentions_datafun(lam.body)}

        delta: set[str] = set()
        work = [g for n in phi
                for g in _globals_under_box(bodies[n].body) if g in bodies]
        while work:
            g = work.pop()
            if g in delta:
                continue
            delta.add(g)
            # Every global in a differentiated body may end up under δ —
            # `δ(e f) = δe [ϕf] δf` reaches all of it — so this closes
            # over the whole body rather than tracking positions.
            work.extend(h for h in _globals_in(bodies[g].body)
                        if h in bodies and h not in delta)

        return Plan(frozenset(phi), frozenset(delta), frozenset(bodies))


def _mentions_datafun(e: Expr) -> bool:
    stack = [e]
    while stack:
        node = stack.pop()
        if isinstance(node, _DATAFUN_NODES):
            return True
        stack.extend(subexprs(node))
    return False


def _globals_in(e: Expr) -> set[str]:
    out: set[str] = set()
    stack = [e]
    while stack:
        node = stack.pop()
        if isinstance(node, EGlobal) and isinstance(node.name, str):
            out.add(node.name)
        stack.extend(subexprs(node))
    return out


def _globals_under_box(e: Expr) -> set[str]:
    """The globals ϕ will differentiate: those inside a `[e]`."""
    out: set[str] = set()
    stack = [e]
    while stack:
        node = stack.pop()
        if isinstance(node, EBox):
            out |= _globals_in(node.body)
            continue                    # `_globals_in` covered the subtree
        stack.extend(subexprs(node))
    return out


# ---------------------------------------------------------------------------
# Program-level transform — generate f_phi/f_delta pairs
# ---------------------------------------------------------------------------

def transform(
    scs: list[tuple[str, int, ELambda, object]],
    helper_names: set[str] | None = None,
    cons: dict[str, ConInfo] | None = None,
    method_scs: set[str] | None = None,
) -> tuple[list[tuple[str, int, ELambda, object]], Changes]:
    """Apply the ϕ/δ transform to a list of SCs.

    ``helper_names`` is a set of SC names that should NOT be transformed
    (generated helpers, primitives, etc.).  ``cons`` is the program's
    constructor table, which the change structure needs for `dummy` at a
    sum type.  ``method_scs`` names the instance methods
    `elaborate.resolve_static_methods` has made directly callable; they
    are ordinary code and must be transformed despite their `__` prefix.

    Returns the transformed SCs and the `Changes` builder they were built
    with: it records which `dummy_X`/`bottom_X` the emitted code refers
    to, and those have to be generated afterwards — δ is what discovers
    them.
    """
    if helper_names is None:
        helper_names = set()
    if method_scs is None:
        method_scs = set()
    if not _PRIM_TYPES:
        from .pipeline import _build_builtins
        _PRIM_TYPES.update(_build_builtins())
    builder = Changes(cons or {})

    def _skip(name: str) -> bool:
        """Everything the user wrote is transformed; generated code is not.

        `main` is *not* skipped.  It is an ordinary supercombinator,
        `spec/data.md` §0 exempts nothing, and exempting it meant a `fix`
        in `main` ran the naïve loop while the same `fix` one definition
        over ran the seminaïve one (`fixme.md` F9).  The entry point keeps
        its name because every transformed SC is kept as an alias for its
        own `_phi`.

        The skipped set is the compiler's own output: generated helpers,
        and the `__`-named dictionaries elaboration emits.  A *user* name
        starting with a single `_` used to land here too, which gave
        `_foo` a different evaluation strategy from `foo` — the same
        defect this item is about.

        **Instance methods are not in it.**  They used to be, by sharing
        the `__` prefix with dictionaries, and that was the same mistake
        one level down: a method body is ordinary user code, and a `fix`
        that calls one needs its derivative like any other.  Skipping it
        meant δ asked for a derivative that was never planned, got the
        discrete `()` instead, and applied it.  A *dictionary* is still
        skipped, and rightly — it is discrete data, `Δdict = 1`.  What
        makes the distinction reachable is that `resolve_static_methods`
        has already turned `πᵢ dict` into the method's own name.
        """
        if name in helper_names:
            return True
        if name in method_scs:
            return False
        return name.startswith("__")

    plan = Plan.of({name: lam for name, _a, lam, _s in scs
                    if not _skip(name)})

    result: list[tuple[str, int, ELambda, object]] = []

    for name, arity, lam, sig in scs:
        if _skip(name) or not (name in plan.phi or name in plan.delta):
            # Nothing to do: ϕ would rebuild this body unchanged and
            # nothing differentiates it.  Left as it is, under its own
            # name, which is also the name every call site already uses.
            result.append((name, arity, lam, sig))
            continue

        ctx = SeminaiveCtx(builder=builder, plan=plan)
        for p in lam.params:
            ctx = ctx.bind(p, "d" + p)

        if name in plan.phi:
            result.append((name + "_phi", arity,
                           ELambda(list(lam.params), phi(lam.body, ctx)), sig))

        if name in plan.delta:
            # Base points and changes *interleaved*, which is the order
            # `δ(e f) = δe [ϕf] δf` supplies them in (F2).
            delta_params = _interleave_params(list(lam.params))
            result.append((name + "_delta", len(delta_params),
                           ELambda(delta_params, delta(lam.body, ctx)), sig))

        if name in plan.phi:
            # Keep the original name as an alias for `f_phi`, so a call
            # from code the transform left alone still finds the sped-up
            # definition — `main` among them.
            alias_body: Expr = EGlobal(name + "_phi")
            for p in lam.params:
                alias_body = EAp(alias_body, EVar(p))
            result.append((name, arity,
                           ELambda(list(lam.params), alias_body), sig))
        else:
            result.append((name, arity, lam, sig))

    return result, builder


# ---------------------------------------------------------------------------
# Generate semifix helpers
# ---------------------------------------------------------------------------

def make_semifix_helpers(
    nil_tag: int, cons_tag: int, true_tag: int, false_tag: int,
    suffix: str = "Set_Int",
) -> list[tuple[str, int, ELambda]]:
    """Generate ``semifixL`` and ``semifix`` for one monomorphic type.

        semifixL f f' x dx =
            case subset_L dx x of
                True  -> x
                False -> let x' = join_L x dx
                         in semifixL f f' x' (diff_L (f' x dx) x')
        semifix (f, f') = semifixL f f' bottom_L (f bottom_L)

    The ``diff_L`` is *change minimization* (thesis §4.3, `spec/errata.md`
    D4): the next delta is `(f' xᵢ dxᵢ) \\L xᵢ₊₁`, not `f' xᵢ dxᵢ`.

    Without it seminaïve evaluation is asymptotically wrong on any relation
    with a cycle.  `δ(e ∨ f) = δe ∨ δf` overapproximates, so an element
    rediscovered at iteration *i* stays in `dxᵢ`; it is then treated as new
    and re-derives everything reachable from it, in that iteration and
    every later one.  The thesis measures 745s against 1.5s at 400 nodes on
    a loopy line graph.  Subtracting what `x` already contains is sound
    because `x ∨ dx = x ∨ (dx \\ x)` — the fixed point is unchanged; only
    the work is.

    The test is `dx ⊑ x`, not `dx = ⊥` — the thesis's fig. 4.2, and p. 71:
    "seminaïve iteration stabilizes once `dxᵢ ⩽ xᵢ`".  This is not an
    optimization.  `δ(e ∨ f) = δe ∨ δf` is a deliberate overapproximation
    (§3.4.6), so a delta routinely contains elements already in `x`; such
    a delta is non-empty but adds nothing, and `x` stops growing while
    `dx` never reaches ⊥.  The `dx = ⊥` test then **loops forever** on
    exactly the shape every Datalog query has, `fix (r => base ∨ step r)`.
    """
    f = EVar("f")
    fp = EVar("f'")
    x = EVar("x")
    dx = EVar("dx")
    dxp = EVar("dx'")
    p = EVar("p")

    bottom = EGlobal(f"bottom_{suffix}")
    eq = EGlobal(f"eq_{suffix}")
    join = EGlobal(f"join_{suffix}")

    subset = EGlobal(f"subset_{suffix}")
    diff = EGlobal(f"diff_{suffix}")
    xp = EVar("x'")
    semifixL_body = ECase(EAp(EAp(subset, dx), x), [
        Alter(true_tag, [], x),
        Alter(false_tag, [], ELet(
            False, [("x'", EAp(EAp(join, x), dx))],
            EAp(EAp(EAp(EAp(EGlobal(f"semifixL_{suffix}"), f), fp), xp),
                EAp(EAp(diff, EAp(EAp(fp, x), dx)), xp)))),
    ])

    semifixL = (f"semifixL_{suffix}", 4,
                ELambda(["f", "f'", "x", "dx"], semifixL_body))

    # semifix takes the *pair* ϕ produced for the boxed function:
    # ϕ(fix e) = semifix ϕe, and ϕ[e] = (ϕe, δe).  Unpack it, then
    # semifixL f f' ⊥ (f ⊥).
    semifix_body = ELet(
        False,
        [("f", EAp(EProj(0), p)), ("f'", EAp(EProj(1), p))],
        EAp(EAp(EAp(EAp(EGlobal(f"semifixL_{suffix}"), f), fp), bottom),
            EAp(f, bottom)),
    )
    semifix = (f"semifix_{suffix}", 1, ELambda(["p"], semifix_body))

    return [semifixL, semifix]
