"""Bidirectional type inference with Hindley-Milner polymorphism
and typeclass constraint generation.

Class methods emit predicates during inference.  Constraint solving
happens separately; elaborated constraints become dictionary arguments
at the core-Expr boundary.
"""

from __future__ import annotations

import itertools as _itertools

from .expr import (
    EAnnot, EAp, EAppEx, EAppFa, EBox, ECase, EChan, ECon, EDelay, EField,
    EFix, EFor,
    EChr, EGFix, EGlobal, EHole, EJoin, Alter,
    ELambda, ELet, ENever, ENum, EProj, ESet, ETuple, ESigCons, ESigHead, ESync,
    ETail, EUnbox, EVar, EWait, EWatch, Expr, Name, subexprs,
)
from .types import (
    Scheme, TApp, TCon, TFun, TVar, Type, Subst, Unifier, Predicate, unifying,
    _apply_subst_map, free_vars, free_vars_of_env, has_nontrivial_order,
    mk_tuple, tuple_parts,
    scheme_free_vars, scheme_mono,
)
from .unify import unify, UnifyError
from .declarations import ConInfo, ClassInfo
from .match import MATCH_FAIL


class InferError(Exception):
    pass


def at(node) -> str:
    """` (at L:C)` for a node that carries a span, and `""` for one that does
    not.

    **The shape is not arbitrary**: `audiospans._AT` reads exactly this
    back, and is what moves the number out of assembled coordinates and
    into the author's file — which is what lets an editor put the message
    on the line it is about instead of at the top of the window.  Measured
    before this existed, six of ten kinds of error carried no position at
    all, and `Unknown global 'sinewave'` — a typo, the commonest mistake
    there is — was among them.

    Silent when there is no span, because there are nodes the desugaring
    builds that were never written down, and inventing a position for one
    would be worse than admitting there is none.
    """
    span = getattr(node, "span", None)
    if span is None:
        return ""
    start = getattr(span, "start", span)
    line, col = getattr(start, "line", None), getattr(start, "col", None)
    return "" if line is None or col is None else f" (at {line}:{col})"


class UnresolvedName(InferError):
    """A name with no definition — the one failure that stops the rest meaning
    anything.

    Its own class rather than a message to match on, because what depends
    on it is a *decision*: `typecheck._find_errors` falls back to inferring
    each supercombinator on its own to collect more errors than the first,
    and that fallback is only sound once the environment holds every
    definition's type.  A name that resolves to nothing throws before the
    environment is finished, so every later definition is then checked
    against a half-built one and reports as rigid.

    One `Unknown global` produced **forty-five** further errors about
    `reverse`, `showNat`, `sine` and the rest of the prelude — none of
    them real, none of them near the mistake, and the true one first in a
    list nobody would read to the end of.
    """


class Fresh:
    __slots__ = ("_n",)
    def __init__(self, start: int = 0): self._n = start
    def tv(self) -> TVar:
        v = TVar(self._n); self._n += 1; return v


_SITE_TOKENS = _itertools.count(1)


def _at_site(preds: list[Predicate], expr: Expr) -> list[Predicate]:
    """Tag constraints with the occurrence that emitted them.

    The tag is a stamp written *onto the node*, not `id(expr)`: an id is
    process-local, and a cached stack front carries its constraints
    through a pickle — the node comes back a new object with a new id,
    while a stamp rides along with it.
    """
    site = getattr(expr, "site_token", None)
    if site is None:
        site = next(_SITE_TOKENS)
        expr.site_token = site
    return [Predicate(p.class_name, p.type_, site) for p in preds]


def _apply_subst_constraints(constraints_out: list[Predicate] | None, s: Subst) -> None:
    # Under a destructive store there is nothing to push: a predicate's type
    # resolves through the store whenever it is next read, and every one of
    # them is read through `s.apply` before leaving `infer_program`.  This
    # ran after almost every inference step, so skipping it is most of what
    # the union-find buys (`fixme.md` F78).
    if isinstance(s, Unifier):
        return
    if not s or constraints_out is None:
        return
    for i in range(len(constraints_out)):
        p = constraints_out[i]
        nt = s.apply(p.type_)
        if nt is not p.type_:
            constraints_out[i] = Predicate(p.class_name, nt, p.site)


def _all_exprs(root: Expr):
    """Every node of an expression tree, root first.

    ``case`` alternatives are yielded alongside expressions: an ``Alter``
    is not an ``Expr`` but does carry annotations.
    """
    stack = [root]
    while stack:
        e = stack.pop()
        yield e
        if isinstance(e, ECase):
            for alt in e.alts:
                yield alt
        stack.extend(subexprs(e))


def _subst_scheme(sc: Scheme, s: Subst) -> Scheme:
    """Push a substitution through a scheme — *including* its constraints.

    Dropping it on the constraints is not a cosmetic loss.  A scheme's
    variables are metavariables — a signature's are quantified and
    instantiated fresh at each use, an inferred SC's are open until the
    program is — so a use site can bind one: `myElem : (Eq a) => …` called
    at `Bool` substitutes `a := Bool` in the type.  Leaving the constraint
    as `Eq a` then strands it — the variable no longer occurs in the type,
    so nothing will ever bind it, and the call site emits a constraint on
    a variable that resolution can only default.  That is how a recursive
    constrained supercombinator ended up handed the `Int` dictionary at
    every other element type.
    """
    return Scheme(
        sc.vars, s.apply(sc.type_),
        tuple(Predicate(p.class_name, s.apply(p.type_), p.site)
              for p in sc.constraints),
    )


def _subst_env(env: dict[Name, Scheme], s: Subst) -> dict[Name, Scheme]:
    """Push a substitution through every scheme in an environment."""
    if isinstance(s, Unifier):
        return env                      # see `_apply_subst_env`
    return {n: _subst_scheme(sc, s) for n, sc in env.items()}


def _infer_later_ap(env, expr, fn_mod: str, arg_mod: str, fresh, cons, classes,
                    constraints_out) -> tuple[Type, Subst]:
    """Type ``s ⊛ t`` / ``s 5 t`` — both are applicative action at a modality.

    ``fn_mod (A → B) → arg_mod A → arg_mod B``.  The result sits at the
    *argument's* modality, which is what makes ``5``'s result inherit its
    argument's clock (``cl (s 5 t) = cl t``).
    """
    f_t, s1 = infer(env, expr.fn, fresh, cons, classes, constraints_out)
    a_t, s2 = infer(_subst_env(env, s1), expr.arg, fresh, cons, classes,
                    constraints_out)
    s = s2.compose(s1)
    a, b = fresh.tv(), fresh.tv()
    s = s.compose(unify(s.apply(f_t), TApp(TCon(fn_mod), TFun(a, b))))
    s = s.compose(unify(s.apply(a_t), TApp(TCon(arg_mod), a)))
    _apply_subst_constraints(constraints_out, s)
    return s.apply(TApp(TCon(arg_mod), b)), s


# ---------------------------------------------------------------------------
# Polymorphism helpers
# ---------------------------------------------------------------------------

def generalize(env: dict[Name, Scheme], t: Type,
               constraints: tuple[Predicate, ...] = ()) -> Scheme:
    constraint_vars: set[int] = set()
    for p in constraints:
        constraint_vars |= free_vars(p.type_)
    quant = (free_vars(t) | constraint_vars) - free_vars_of_env(env)
    return Scheme(frozenset(quant), t, constraints)


def instantiate(scheme: Scheme, fresh: Fresh) -> tuple[Type, list[Predicate]]:
    """Instantiate a scheme: replace quantified vars with fresh TVars.
    Returns ``(type, constraints)`` — class-method schemes carry
    predicates that are emitted as constraints at the call site.
    """
    if not scheme.vars and not scheme.constraints:
        return scheme.type_, []
    m = {vid: fresh.tv() for vid in scheme.vars}
    t = _apply_subst_map(scheme.type_, m)
    cs = [_apply_pred(c, m) for c in scheme.constraints]
    return t, cs


def _apply_pred(p: Predicate, m: dict[int, TVar]) -> Predicate:
    return Predicate(p.class_name, _apply_subst_map(p.type_, m))


# ---------------------------------------------------------------------------
# ADT helpers
# ---------------------------------------------------------------------------

def _is_adt_param(tv: TVar) -> bool: return tv.id < 0

def _instantiate_adt(template: Type, fresh: Fresh) -> tuple[Type, Subst]:
    seen: dict[int, TVar] = {}
    return _inst_adt(template, seen, fresh)

def _inst_adt(t: Type, seen: dict[int, TVar], fresh: Fresh) -> tuple[Type, Subst]:
    if isinstance(t, TVar) and _is_adt_param(t):
        if t.id not in seen: seen[t.id] = fresh.tv()
        return seen[t.id], Subst.empty()
    if isinstance(t, TVar): return t, Subst.empty()
    if isinstance(t, TCon): return t, Subst.empty()
    if isinstance(t, TFun):
        a, sa = _inst_adt(t.arg, seen, fresh); r, sr = _inst_adt(t.ret, seen, fresh)
        return TFun(a, r), sr.compose(sa)
    if isinstance(t, TApp):
        f, sf = _inst_adt(t.fn, seen, fresh); a, sa = _inst_adt(t.arg, seen, fresh)
        return TApp(f, a), sa.compose(sf)
    return t, Subst.empty()

def _extract_field_types(ctor_type: Type) -> list[Type]:
    fields: list[Type] = []
    t = ctor_type
    while isinstance(t, TFun): fields.append(t.arg); t = t.ret
    return fields


# ---------------------------------------------------------------------------
# Method type lookup
# ---------------------------------------------------------------------------

def _lookup_method(name: str, classes: dict[str, ClassInfo],
                   fresh: Fresh) -> tuple[Scheme, Predicate] | None:
    """If ``name`` is a class method, return its qualified scheme.

    Associated type applications in the method's type are replaced with
    fresh type variables so they participate in normal unification.
    The actual normalization happens during elaboration.
    """
    for ci in classes.values():
        if name in ci.methods:
            mt = ci.methods[name]
            seen: dict[int, TVar] = {}
            inst_type, _ = _inst_adt(mt, seen, fresh)
            # Replace associated type applications with fresh TVars
            if ci.assoc_types:
                inst_type = _replace_assoc_types(inst_type, ci.assoc_types, fresh)
            # **The class parameter by identity, not by position.**  This
            # used to take the lowest-numbered ADT variable in the method's
            # type, which worked only while a method could mention no
            # variable but the class's own.  Once `map : (a -> b) -> f a ->
            # f b` has three, the lowest-numbered one is whichever
            # `adt_param_tv` happened to allocate last — `b` — and the
            # predicate would be `Functor b`.  `ci.param_tvs` is the class's
            # own record of which variable it is; ask that.
            if ci.param_tvs:
                pid = ci.param_tvs[0].id
                pred_tv = seen[pid] if pid in seen else fresh.tv()
            elif ci.params:
                param_ids = sorted(tv.id for tv in _collect_adt_tvs(mt))
                if param_ids and param_ids[0] in seen:
                    pred_tv = seen[param_ids[0]]
                else:
                    pred_tv = fresh.tv()
            else:
                pred_tv = TCon(ci.name)
            pred = Predicate(ci.name, pred_tv)
            scheme = Scheme(frozenset(), inst_type, (pred,))
            return scheme, pred
    return None


def _replace_assoc_types(t: Type, assoc_names: list[str], fresh: Fresh) -> Type:
    """Replace ``TApp(TCon(assoc), args...)`` with fresh type variables."""
    if isinstance(t, TFun):
        return TFun(_replace_assoc_types(t.arg, assoc_names, fresh),
                    _replace_assoc_types(t.ret, assoc_names, fresh))
    if isinstance(t, TApp):
        inner = t
        args: list[Type] = []
        while isinstance(inner, TApp):
            args.append(inner.arg)
            inner = inner.fn
        if isinstance(inner, TCon) and inner.name in assoc_names:
            return fresh.tv()
        return TApp(_replace_assoc_types(t.fn, assoc_names, fresh),
                    _replace_assoc_types(t.arg, assoc_names, fresh))
    return t


def _collect_adt_tvs(t: Type) -> list[TVar]:
    """Collect all ADT-param TVars (negative ids) in a type."""
    result: list[TVar] = []
    def go(ty):
        if isinstance(ty, TVar) and ty.id < 0:
            result.append(ty)
        elif isinstance(ty, TFun):
            go(ty.arg); go(ty.ret)
        elif isinstance(ty, TApp):
            go(ty.fn); go(ty.arg)
    go(t)
    return result


# ---------------------------------------------------------------------------
# Core judgments
# ---------------------------------------------------------------------------

def infer(env: dict[Name, Scheme], expr: Expr, fresh: Fresh,
          cons: dict[str, ConInfo],
          classes: dict[str, ClassInfo],
          constraints_out: list[Predicate] | None = None,
          ) -> tuple[Type, Subst]:
    if constraints_out is None:
        constraints_out = []

    if isinstance(expr, ENum):
        # The literal's *form* decides its type — a point makes it a
        # `Float` — so nothing here is ambiguous and nothing is defaulted.
        # Mixing still works, because `2` is `Num a => a` and unifies with
        # `Float` through `Num Float`: `x * 2 + 1.5` needs no coercion.
        return (TCon("Float") if isinstance(expr.n, float)
                else TCon("Int")), Subst.empty()

    if isinstance(expr, EHole):
        # **A hole takes the type its context demands.**  A fresh variable
        # unifies with whatever is expected of it, so the program around
        # the hole is checked exactly as if it were filled — and reading
        # the variable back under the final substitution is what says what
        # would fill it.
        t = fresh.tv()
        expr.type_ = t
        return t, Subst.empty()

    if isinstance(expr, EChr):
        return TCon("Char"), Subst.empty()

    if isinstance(expr, EVar):
        if expr.name not in env:
            raise UnresolvedName(
                f"Unbound variable: {expr.name!r}{at(expr)}")
        t, cs = instantiate(env[expr.name], fresh)
        constraints_out.extend(cs)
        # Recorded for ϕ/δ: the zero change of a variable a box closes
        # over is taken at this type.  It is finished off with the final
        # substitution in `infer_program`.
        expr.type_ = t
        return t, Subst.empty()

    if isinstance(expr, EGlobal):
        if expr.name == MATCH_FAIL:
            # A failed match diverges, so it inhabits every type.  Each
            # occurrence gets its own variable rather than one shared
            # monomorphic builtin, which is what `∀a. a` means here.
            return fresh.tv(), Subst.empty()
        if expr.name not in env:
            m = _lookup_method(expr.name, classes, fresh)
            if m is not None:
                scheme, _ = m
                t, cs = instantiate(scheme, fresh)
                constraints_out.extend(_at_site(cs, expr))
                return t, Subst.empty()
            raise UnresolvedName(
                f"Unknown global '{expr.name}' (not defined as a "
                f"supercombinator or class method){at(expr)}")
        t, cs = instantiate(env[expr.name], fresh)
        constraints_out.extend(_at_site(cs, expr))
        return t, Subst.empty()

    if isinstance(expr, ECon):
        con = _con_by_tag(expr.tag, cons)
        if con is None:
            raise InferError(
                f"Unknown constructor tag: {expr.tag}{at(expr)}")
        ctor_type, _ = _instantiate_adt(con.type_, fresh)
        field_types = _extract_field_types(ctor_type)
        if len(expr.args) != len(field_types):
            raise InferError(
                f"Constructor {con.name}: expected {len(field_types)} args, "
                f"got {len(expr.args)}{at(expr)}")
        s = Subst.empty()
        for arg_expr, ft in zip(expr.args, field_types):
            s = s.compose(check(env, arg_expr, ft, fresh, cons, classes, constraints_out))
        ret = ctor_type
        while isinstance(ret, TFun): ret = ret.ret
        _apply_subst_constraints(constraints_out, s)
        return s.apply(ret), s

    if isinstance(expr, EAnnot):
        inner_t, s = infer(env, expr.expr, fresh, cons, classes, constraints_out)
        ann_t = expr.type_
        assert isinstance(ann_t, Type)
        s = s.compose(unify(inner_t, ann_t))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(ann_t), s

    if isinstance(expr, EAp) and isinstance(expr.fn, EProj) \
            and expr.fn.width is not None:
        # `EProj i` is not a first-class value — it appears only as
        # `EAp (EProj i) tup` — so the pair is typed as one node.  The
        # width comes from the pattern the match compiler saw; without it
        # the operand's arity would be unknowable, since the tuple type
        # constructors are distinct per arity.
        n, i = expr.fn.width, expr.fn.i
        t, s = infer(env, expr.arg, fresh, cons, classes, constraints_out)
        known = s.apply(t)
        parts = tuple_parts(known)
        if parts is None or len(parts) != n:
            # The operand's shape is not settled yet, so unify it into
            # place.  When it *is* settled — the usual case, since the
            # tuple came from a signature — read the component off
            # directly instead: unifying a signature's variable against a
            # fresh one would bind it, and a bound signature variable is no
            # longer quantified (`fixme.md` F36).
            parts = [fresh.tv() for _ in range(n)]
            s = s.compose(unify(known, mk_tuple(parts)))
            parts = [s.apply(p) for p in parts]
        _apply_subst_constraints(constraints_out, s)
        return parts[i], s

    if isinstance(expr, EAp):
        fn_t, s1 = infer(env, expr.fn, fresh, cons, classes, constraints_out)
        arg_t, s2 = infer(_apply_subst_env(env, s1), expr.arg, fresh, cons, classes, constraints_out)
        s = s2.compose(s1)
        ret = fresh.tv()
        # The arrow's flavour comes from the function when it is already
        # known; an unannotated function defaults to `->`.  Unification
        # keeps the two apart, so guessing here would reject `f x` for a
        # monotone `f` outright.
        known = s.apply(fn_t)
        mono = known.mono if isinstance(known, TFun) else False
        expr.discrete_arg = not mono
        # `unify(actual, expected)` — the order decides which way the
        # error message reads.  The *actual* type here is the arrow the
        # call site implies; the *expected* one is the function's own.
        s = s.compose(unify(TFun(s.apply(arg_t), ret, None, mono), known))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(ret), s

    if isinstance(expr, ELet):
        return _infer_let(env, expr, fresh, cons, classes, constraints_out)

    if isinstance(expr, EField):
        t_base, s = infer(env, expr.base, fresh, cons, classes, constraints_out)
        t_base = s.apply(t_base)
        expr.base_type = t_base
        field_t, lowering = _resolve_field(t_base, expr.index, cons)
        expr.lowering = lowering
        _apply_subst_constraints(constraints_out, s)
        return s.apply(field_t), s

    if isinstance(expr, ETuple):
        s = Subst.empty(); ts: list[Type] = []
        for item in expr.args:
            t, si = infer(_subst_env(env, s), item, fresh, cons, classes,
                          constraints_out)
            s = si.compose(s); ts.append(t)
        _apply_subst_constraints(constraints_out, s)
        return s.apply(mk_tuple(ts)), s

    if isinstance(expr, ECase):
        return _infer_case(env, expr, fresh, cons, classes, constraints_out)

    if isinstance(expr, ELambda):
        if len(expr.params) == 0:
            return infer(env, expr.body, fresh, cons, classes, constraints_out)
        param_types = [fresh.tv() for _ in expr.params]
        new_env = dict(env)
        for p, t in zip(expr.params, param_types): new_env[p] = scheme_mono(t)
        body_t, s = infer(new_env, expr.body, fresh, cons, classes, constraints_out)
        ret = body_t
        for pt in reversed(param_types): ret = TFun(s.apply(pt), ret)
        _apply_subst_constraints(constraints_out, s)
        # Kept for the reader that has no other source for it — see
        # `ELambda.type_`.  It may still hold metavariables here; the walk
        # at the end of `infer_program` finishes it off, exactly as it does
        # for the annotations on `EVar` and `EFor`.
        expr.type_ = ret
        return ret, s

    # -- FRP nodes (Rizzo fig. 3) --
    #
    # The two later modalities are distinct type constructors.  ``FaL A``
    # is ⃝∀A, a computation available whenever *any* clock ticks; ``ExL A``
    # is ⃝∃A, one that fires on its own clock.  Keeping them apart is what
    # makes `<@>` the only bridge between them, and hence what forces a
    # computed signal to carry a clock from the signal it is computed from.

    if isinstance(expr, ENever):
        # never : ⃝∃A
        return TApp(TCon("ExL"), fresh.tv()), Subst.empty()

    if isinstance(expr, EChan):
        # chan_A : Chan A.  Record `A` on the node: the reactive driver
        # keeps a channel context and the heap is untyped, so this
        # occurrence is the only place the element type is known.
        a = fresh.tv()
        expr.elem_type = a
        return TApp(TCon("Chan"), a), Subst.empty()

    if isinstance(expr, ESigCons):
        # (::A) : A → ⃝∃(Sig A) → Sig A
        v_t, s1 = infer(env, expr.value, fresh, cons, classes, constraints_out)
        t_t, s2 = infer(_subst_env(env, s1), expr.tail, fresh, cons, classes,
                        constraints_out)
        s = s2.compose(s1)
        sig_a = TApp(TCon("Sig"), s.apply(v_t))
        s = s.compose(unify(s.apply(t_t), TApp(TCon("ExL"), sig_a)))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(sig_a), s

    if isinstance(expr, ESigHead):
        # head : Sig A → A
        sig_t, s = infer(env, expr.sig, fresh, cons, classes, constraints_out)
        a = fresh.tv()
        s = s.compose(unify(s.apply(sig_t), TApp(TCon("Sig"), a)))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(a), s

    if isinstance(expr, EDelay):
        # delay : A → ⃝∀A
        body_t, s = infer(env, expr.body, fresh, cons, classes, constraints_out)
        _apply_subst_constraints(constraints_out, s)
        return TApp(TCon("FaL"), body_t), s

    if isinstance(expr, EAppFa):
        # ⊛ : ⃝∀(A → B) → ⃝∀A → ⃝∀B
        return _infer_later_ap(env, expr, "FaL", "FaL", fresh, cons, classes,
                               constraints_out)

    if isinstance(expr, EAppEx):
        # 5 : ⃝∀(A → B) → ⃝∃A → ⃝∃B
        return _infer_later_ap(env, expr, "FaL", "ExL", fresh, cons, classes,
                               constraints_out)

    if isinstance(expr, EWait):
        # wait : Chan A → ⃝∃A
        chan_t, s = infer(env, expr.chan, fresh, cons, classes, constraints_out)
        a = fresh.tv()
        s = s.compose(unify(s.apply(chan_t), TApp(TCon("Chan"), a)))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(TApp(TCon("ExL"), a)), s

    if isinstance(expr, EWatch):
        # watch : Sig (Maybe A) → ⃝∃A
        sig_t, s = infer(env, expr.sig, fresh, cons, classes, constraints_out)
        a = fresh.tv()
        s = s.compose(unify(s.apply(sig_t),
                            TApp(TCon("Sig"), TApp(TCon("Maybe"), a))))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(TApp(TCon("ExL"), a)), s

    if isinstance(expr, ETail):
        # tail : Sig A → ⃝∃(Sig A)
        sig_t, s = infer(env, expr.sig, fresh, cons, classes, constraints_out)
        a = fresh.tv()
        s = s.compose(unify(s.apply(sig_t), TApp(TCon("Sig"), a)))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(TApp(TCon("ExL"), TApp(TCon("Sig"), a))), s

    if isinstance(expr, ESync):
        # sync : ⃝∃A₁ → ⃝∃A₂ → ⃝∃(Sync A₁ A₂).  The two arguments need not
        # agree: sync's whole purpose is combining clocks over unlike types.
        l_t, s1 = infer(env, expr.left, fresh, cons, classes, constraints_out)
        r_t, s2 = infer(_subst_env(env, s1), expr.right, fresh, cons, classes,
                        constraints_out)
        s = s2.compose(s1)
        a, b = fresh.tv(), fresh.tv()
        s = s.compose(unify(s.apply(l_t), TApp(TCon("ExL"), a)))
        s = s.compose(unify(s.apply(r_t), TApp(TCon("ExL"), b)))
        _apply_subst_constraints(constraints_out, s)
        sync_t = TApp(TApp(TCon("Sync"), a), b)
        return s.apply(TApp(TCon("ExL"), sync_t)), s

    if isinstance(expr, EGFix):
        # Γ, x : ⃝∀A ⊢ t : A  ⟹  Γ ⊢ gfix x. t : A
        #
        # The binder is universally delayed, so a recursive occurrence can
        # only be consumed through ⊛/5 — which is exactly the guard that
        # makes the definition productive.
        new_env = dict(env)
        a = fresh.tv()
        new_env[expr.var] = scheme_mono(TApp(TCon("FaL"), a))
        body_t, s = infer(new_env, expr.body, fresh, cons, classes, constraints_out)
        s = s.compose(unify(s.apply(body_t), s.apply(a)))
        _apply_subst_constraints(constraints_out, s)
        return s.apply(a), s

    # -- Datafun nodes (increment 10a) --

    if isinstance(expr, EFix):
        # Γ ⊢ e : □(L ~> L)  ⟹  Γ ⊢ fix e : L   (thesis fig. 2.3, `fix`)
        #
        # Boxed, because `fix` iterates the function from ⊥ and so needs a
        # change-free value — the ϕ/δ transform pairs it with its own
        # derivative.  *Monotone*, because that is why the least fixed
        # point exists at all: the chain ⊥ ⩽ f ⊥ ⩽ f (f ⊥) ⩽ … only
        # ascends if `f` respects the order.  ``L`` is restricted to
        # ``Set a``, the only semilattice the runtime helpers cover.
        # Any **fixtype**, not just `Set a`: a product of semilattices is
        # one, and it is how a Datalog query computes two relations at once
        # (`fixme.md` F37).  Inference only needs the two sides to agree and
        # the argument to be boxed and monotone; *which* semilattice it is
        # is `subgrammar.py`'s question, asked once the substitution has
        # settled.  Pinning it here answered that question too early and
        # answered it wrong.
        fix_t = fresh.tv()
        want = TApp(TCon("Box"), TFun(fix_t, fix_t, None, True))
        try:
            s = check(env, expr.body, want, fresh, cons, classes,
                      constraints_out)
        except (UnifyError, InferError) as exc:
            raise InferError(
                f"fix expects a boxed monotone set function {want}: {exc}; "
                f"write `fix Box (x => ...)`"
            )
        _apply_subst_constraints(constraints_out, s)
        expr.set_type = s.apply(fix_t)
        return expr.set_type, s

    if isinstance(expr, EFor):
        # for (x in e) f : the join of f's results over e's elements
        set_t, s1 = infer(env, expr.set_expr, fresh, cons, classes, constraints_out)
        elt_t = fresh.tv()
        s1 = s1.compose(unify(s1.apply(set_t), TApp(TCon("Set"), elt_t)))
        new_env = dict(env)
        new_env[expr.var] = scheme_mono(s1.apply(elt_t))
        body_t, s2 = infer(new_env, expr.body, fresh, cons, classes, constraints_out)
        s = s2.compose(s1)
        _apply_subst_constraints(constraints_out, s)
        expr.result_type = s.apply(body_t)
        expr.elem_type = s.apply(elt_t)
        return s.apply(body_t), s

    if isinstance(expr, EBox):
        body_t, s = infer(env, expr.body, fresh, cons, classes, constraints_out)
        _apply_subst_constraints(constraints_out, s)
        return TApp(TCon("Box"), body_t), s

    if isinstance(expr, EUnbox):
        bind_t, s = infer(env, expr.binding, fresh, cons, classes, constraints_out)
        inner_t = fresh.tv()
        s = s.compose(unify(s.apply(bind_t), TApp(TCon("Box"), inner_t)))
        new_env = dict(env)
        new_env[expr.var] = scheme_mono(s.apply(inner_t))
        body_t, s2 = infer(new_env, expr.body, fresh, cons, classes, constraints_out)
        total_s = s2.compose(s)
        _apply_subst_constraints(constraints_out, total_s)
        return s2.apply(body_t), total_s

    if isinstance(expr, EJoin):
        # `Γ ⊢ eᵢ : L ⟹ Γ ⊢ e₁ ∨ e₂ : L` (fig. 2.3, `join`).  Both sides
        # and the result are the same semilattice; which types *are*
        # semilattices is `subgrammar.py`'s business.
        l_t, s1 = infer(env, expr.left, fresh, cons, classes, constraints_out)
        r_t, s2 = infer(_apply_subst_env(env, s1), expr.right, fresh, cons,
                        classes, constraints_out)
        s = s2.compose(s1)
        s = s.compose(unify(s.apply(l_t), s.apply(r_t)))
        _apply_subst_constraints(constraints_out, s)
        expr.set_type = s.apply(l_t)
        return expr.set_type, s

    if isinstance(expr, ESet):
        if not expr.items:
            expr.set_type = TApp(TCon("Set"), fresh.tv())
            return expr.set_type, Subst.empty()
        s = Subst.empty()
        elt_t = fresh.tv()
        for item in expr.items:
            t, si = infer(env, item, fresh, cons, classes, constraints_out)
            s = si.compose(s)
            s = s.compose(unify(s.apply(t), elt_t))
        _apply_subst_constraints(constraints_out, s)
        expr.set_type = s.apply(TApp(TCon("Set"), elt_t))
        return expr.set_type, s

    raise InferError(f"Unknown expression: {type(expr).__name__}")


def check(env: dict[Name, Scheme], expr: Expr, expected: Type,
          fresh: Fresh, cons: dict[str, ConInfo],
          classes: dict[str, ClassInfo],
          constraints_out: list[Predicate] | None = None,
          ) -> Subst:
    if constraints_out is None: constraints_out = []

    if isinstance(expr, ELambda):
        if len(expr.params) == 0:
            return check(env, expr.body, expected, fresh, cons, classes, constraints_out)
        # Walk the whole parameter list against the arrow spine so the
        # flavour of each arrow can be recorded on *this* node — checking
        # one parameter at a time would annotate throwaway copies.
        new_env = dict(env)
        mono: list = []
        t = expected
        for p in expr.params:
            if not isinstance(t, TFun):
                raise InferError(
                    f"Lambda with {len(expr.params)} params: expected "
                    f"function type, got {t}{at(expr)}"
                )
            new_env[p] = scheme_mono(t.arg)
            if t.mono:
                mono.append((str(p), t.arg))
            t = t.ret
        expr.mono_candidates = tuple(mono)
        # The arrow it was *checked against* is its type, and the more
        # useful of the two: a step function checked against `zipSig`'s
        # `a -> b -> c` learns the element types from the call site.
        expr.type_ = expected
        return check(new_env, expr.body, t, fresh, cons, classes, constraints_out)

    if isinstance(expr, EAnnot):
        ann_t = expr.type_
        assert isinstance(ann_t, Type)
        s = check(env, expr.expr, ann_t, fresh, cons, classes, constraints_out)
        s = s.compose(unify(s.apply(ann_t), s.apply(expected)))
        _apply_subst_constraints(constraints_out, s)
        return s

    if isinstance(expr, ECase):
        return _check_case(env, expr, expected, fresh, cons, classes, constraints_out)

    if isinstance(expr, ELet):
        return _check_let(env, expr, expected, fresh, cons, classes, constraints_out)

    if isinstance(expr, EBox) and isinstance(expected, TApp) \
            and isinstance(expected.fn, TCon) and expected.fn.name == "Box":
        # Push through the box so a lambda inside it meets the arrow it is
        # expected at — `fix`'s argument is `□(L ~> L)`, and a lambda only
        # learns it binds monotonically from the arrow it is checked
        # against.
        return check(env, expr.body, expected.arg, fresh, cons, classes,
                     constraints_out)

    t, s = infer(env, expr, fresh, cons, classes, constraints_out)
    s = s.compose(unify(s.apply(t), s.apply(expected)))
    _apply_subst_constraints(constraints_out, s)
    return s


# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

def _apply_subst_env(env: dict[Name, Scheme], s: Subst) -> dict[Name, Scheme]:
    """The environment, seen through `s`.

    A no-op under a destructive store, and that is the point: the whole
    reason Algorithm W rebuilds the environment as it goes is that a scheme
    handed out earlier holds types the newest binding refines.  With one
    store the refinement is already visible — every type in there resolves
    through it when read — so the rebuild has nothing to do.  A scheme's
    *quantified* variables are never bound, because `instantiate` renames
    them fresh at each use.
    """
    if isinstance(s, Unifier):
        return env
    return {n: _subst_scheme(sc, s) for n, sc in env.items()}


# ---------------------------------------------------------------------------
# Let
# ---------------------------------------------------------------------------

def _generalize_let(env, t: Type) -> Scheme:
    """Generalize a `let` binding — except at a set type.

    Datafun is a monomorphic sublanguage: its operations are generated
    per concrete type, so a `let s = fix … in s` whose element type stays
    a variable has no helper to call.  Holding such a binding monomorphic
    lets the use site determine it, which is what the programmer meant.
    `spec/errata.md` D9 records the wider tension between §I.4.3's
    per-type generation and the rest of the language being polymorphic.
    """
    if has_nontrivial_order(t):
        return scheme_mono(t)
    return generalize(env, t)


def _infer_let(env, e, fresh, cons, classes, constraints_out):
    if e.is_rec:
        def_types = {n: fresh.tv() for n, _ in e.defs}
        rec_env = dict(env)
        for n, t in def_types.items(): rec_env[n] = scheme_mono(t)
        s = Subst.empty()
        for n, d in e.defs:
            t, si = infer(rec_env, d, fresh, cons, classes, constraints_out)
            s = si.compose(s); s = s.compose(unify(t, def_types[n]))
        body_env = dict(env)
        for n, t in def_types.items(): body_env[n] = scheme_mono(s.apply(t))
        body_t, si = infer(body_env, e.body, fresh, cons, classes, constraints_out)
        total_s = si.compose(s)
        _apply_subst_constraints(constraints_out, total_s)
        return total_s.apply(body_t), total_s
    else:
        let_env = dict(env); s = Subst.empty()
        for n, d in e.defs:
            t, si = infer(let_env, d, fresh, cons, classes, constraints_out)
            s = si.compose(s)
            let_env[n] = _generalize_let(let_env, s.apply(t))
        body_t, si = infer(let_env, e.body, fresh, cons, classes, constraints_out)
        total_s = si.compose(s)
        _apply_subst_constraints(constraints_out, total_s)
        return total_s.apply(body_t), total_s


def _check_let(env, e, expected, fresh, cons, classes, constraints_out):
    if e.is_rec:
        def_types = {n: fresh.tv() for n, _ in e.defs}
        rec_env = dict(env)
        for n, t in def_types.items(): rec_env[n] = scheme_mono(t)
        s = Subst.empty()
        for n, d in e.defs:
            t, si = infer(rec_env, d, fresh, cons, classes, constraints_out)
            s = si.compose(s); s = s.compose(unify(t, def_types[n]))
        body_env = dict(env)
        for n, t in def_types.items(): body_env[n] = scheme_mono(s.apply(t))
        total_s = s.compose(check(body_env, e.body, expected, fresh, cons, classes, constraints_out))
        _apply_subst_constraints(constraints_out, total_s)
        return total_s
    else:
        let_env = dict(env); s = Subst.empty()
        for n, d in e.defs:
            t, si = infer(let_env, d, fresh, cons, classes, constraints_out)
            s = si.compose(s)
            let_env[n] = _generalize_let(let_env, s.apply(t))
        total_s = s.compose(check(let_env, e.body, expected, fresh, cons, classes, constraints_out))
        _apply_subst_constraints(constraints_out, total_s)
        return total_s


# ---------------------------------------------------------------------------
# Case
# ---------------------------------------------------------------------------

def _infer_case(env, e, fresh, cons, classes, constraints_out):
    scrut_t, s = infer(env, e.scrut, fresh, cons, classes, constraints_out)
    ret_t = fresh.tv()
    for alt in e.alts:
        con = _con_by_tag(alt.tag, cons)
        if con is None: raise InferError(f"Unknown constructor tag: {alt.tag}")
        ctor_type, _ = _instantiate_adt(con.type_, fresh)
        field_types = _extract_field_types(ctor_type)
        ctor_ret = ctor_type
        while isinstance(ctor_ret, TFun): ctor_ret = ctor_ret.ret
        s = s.compose(unify(s.apply(scrut_t), s.apply(ctor_ret)))
        alt_env = dict(env)
        mono: list = []
        for nm, ft in zip(alt.names, field_types):
            ft = s.apply(ft)
            alt_env[nm] = scheme_mono(ft)
            mono.append((str(nm), ft))
        alt.mono_candidates = tuple(mono)
        s = s.compose(check(alt_env, alt.body, ret_t, fresh, cons, classes, constraints_out))
    _apply_subst_constraints(constraints_out, s)
    return s.apply(ret_t), s

def _check_case(env, e, expected, fresh, cons, classes, constraints_out):
    scrut_t, s = infer(env, e.scrut, fresh, cons, classes, constraints_out)
    for alt in e.alts:
        con = _con_by_tag(alt.tag, cons)
        if con is None: raise InferError(f"Unknown constructor tag: {alt.tag}")
        ctor_type, _ = _instantiate_adt(con.type_, fresh)
        field_types = _extract_field_types(ctor_type)
        ctor_ret = ctor_type
        while isinstance(ctor_ret, TFun): ctor_ret = ctor_ret.ret
        s = s.compose(unify(s.apply(scrut_t), s.apply(ctor_ret)))
        alt_env = dict(env)
        mono: list = []
        for nm, ft in zip(alt.names, field_types):
            ft = s.apply(ft)
            alt_env[nm] = scheme_mono(ft)
            mono.append((str(nm), ft))
        alt.mono_candidates = tuple(mono)
        s = s.compose(check(alt_env, alt.body, expected, fresh, cons, classes, constraints_out))
    _apply_subst_constraints(constraints_out, s)
    return s


def _con_by_tag(tag, cons):
    for ci in cons.values():
        if ci.tag == tag: return ci
    return None


# ---------------------------------------------------------------------------
# Program-level inference
# ---------------------------------------------------------------------------

def _attach_sc_constraints(env: dict[Name, Scheme], name: str,
                            raw_preds: list[Predicate], s: Subst) -> None:
    """Filter per-SC predicates and attach the relevant ones to the
    supercombinator's scheme in the environment so that cross-SC
    constraint propagation works.

    Only predicates whose free type variables overlap with the SC's
    result type are kept — the rest belong to sub-expressions whose
    types were resolved to concrete types.
    """
    sc = env[name]
    env_type = sc.type_
    if not raw_preds or env_type is None:
        return
    free_in_type = free_vars(env_type)
    filtered: list[Predicate] = []
    for p in raw_preds:
        pt = Predicate(p.class_name, s.apply(p.type_))
        if free_vars(pt.type_) & free_in_type:
            filtered.append(pt)
    if filtered:
        # Quantify: vars that appear in the type or constraints but
        # NOT in the rest of the environment.
        constraint_vars: set[int] = set()
        for p in filtered:
            constraint_vars |= free_vars(p.type_)
        other_env = {n: env[n] for n in env if n != name}
        env_free = free_vars_of_env(other_env)
        quant = (free_vars(env_type) | constraint_vars) - env_free
        env[name] = Scheme(frozenset(quant), env_type, tuple(filtered))


def _resolve_field(t: Type, index, cons: dict) -> tuple[Type, tuple]:
    """The type of `e.index`, and how to lower it, from `e`'s type.

    Both shapes are selected the same way in the surface and differently at
    run time: a tuple is an `NTuple`, a record a one-constructor `NCon`.
    """
    from .types import _apply_subst_map, _spine, tuple_parts

    if not isinstance(index, int):
        raise InferError(
            f"'.{index}' is not a projection: fields are selected by "
            f"position, and a record declares no field names"
        )

    parts = tuple_parts(t)
    if parts is not None:
        if index >= len(parts):
            raise InferError(
                f"'.{index}' on a {len(parts)}-tuple — the components are "
                f"0 to {len(parts) - 1}"
            )
        return parts[index], ("tuple", index, len(parts))

    head, args = _spine(t)
    if isinstance(head, TVar):
        raise InferError(
            f"'.{index}' needs the type of what it projects from, and it is "
            f"not known here.  Projection is resolved from the type rather "
            f"than through a class, so give the value a signature — or "
            f"destructure it with a pattern, which needs no annotation"
        )
    if isinstance(head, TCon) and cons:
        owned = [ci for ci in cons.values()
                 if _con_owner(ci) == head.name]
        if len(owned) == 1:
            ci = owned[0]
            fields, ret = [], ci.type_
            while isinstance(ret, TFun):
                fields.append(ret.arg)
                ret = ret.ret
            if index >= len(fields):
                raise InferError(
                    f"'.{index}' on '{head.name}', which has "
                    f"{len(fields)} field(s)"
                )
            _rh, params = _spine(ret)
            subst = {p.id: a for p, a in zip(params, args)
                     if isinstance(p, TVar)}
            return (_apply_subst_map(fields[index], subst),
                    ("con", ci.tag, len(fields), index))
        if len(owned) > 1:
            raise InferError(
                f"'.{index}' on '{head.name}', which has {len(owned)} "
                f"constructors — only a record (one constructor) can be "
                f"projected; use a `case`"
            )

    from .show import show_type
    raise InferError(f"'.{index}' on {show_type(t)}, which is not a "
                     f"tuple or a record")


def _con_owner(ci) -> str | None:
    """The name of the data type ``ci`` constructs."""
    from .types import TApp
    t = ci.type_
    while isinstance(t, TFun):
        t = t.ret
    while isinstance(t, TApp):
        t = t.fn
    return t.name if isinstance(t, TCon) else None


def settle_annotations(root: Expr, s: Subst, cons: dict | None = None) -> None:
    """Push a finished substitution back through a body's type annotations.

    Inference records a type on `ESet`/`EFix`/`EJoin`/`EFor`/`EVar`/`EChan`
    when it *visits* the node, and that type is routinely a metavariable the
    rest of the pass then solves.  Codegen reads these annotations to pick a
    per-type helper (`bottom_Set_Cyclic_4`), so a node left holding a
    metavariable names a helper nobody generated.

    Shared with `infer_instance_method` rather than inlined in
    `infer_program`, which is what `fixme.md` F58 was: a method body never
    had this run over it, so a `fix` in one compiled to `fix_Set_a0`, and a
    `{}` in one — `Guard Bool`'s false branch — to `bottom_Set_a1`, which
    crashed the moment a guard was false under a `fix`.
    """
    for node in _all_exprs(root):
        if isinstance(node, (EVar, ELambda, EHole)) and node.type_ is not None:
            node.type_ = s.apply(node.type_)
        if isinstance(node, EChan) and node.elem_type is not None:
            node.elem_type = s.apply(node.elem_type)
        if isinstance(node, (ESet, EFix, EJoin)) and node.set_type is not None:
            node.set_type = s.apply(node.set_type)
        if isinstance(node, EFor):
            if node.result_type is not None:
                node.result_type = s.apply(node.result_type)
            if node.elem_type is not None:
                node.elem_type = s.apply(node.elem_type)
        # A binder is monotone only where its type has a non-trivial
        # order, and that is not settled until the substitution is.
        if isinstance(node, (ELambda, Alter)) and node.mono_candidates:
            node.mono = frozenset(
                n for n, t in node.mono_candidates
                if has_nontrivial_order(s.apply(t), cons)
            )
        # An alternative's binders carry their types onward: δ builds
        # `dummy xᵢ` for its dead branches, and that is type-directed
        # (`spec/data.md` §I.4.2).  `mono_candidates` records one entry
        # per field, in order, which is exactly the list.
        if isinstance(node, Alter):
            node.field_types = tuple(
                s.apply(t) for _n, t in node.mono_candidates)


def infer_instance_method(
    body: Expr,
    params: list[str],
    method_type: Type,
    sc_types: dict[Name, Type],
    cons: dict[str, ConInfo] | None = None,
    classes: dict[str, ClassInfo] | None = None,
    context: list[Predicate] | None = None,
    sc_constraints: dict[Name, tuple] | None = None,
) -> tuple[list[Predicate], list[Predicate]]:
    """Infer one instance method, destructively (`fixme.md` F78)."""
    with unifying():
        return _infer_instance_method(body, params, method_type, sc_types, cons, classes, context, sc_constraints)


def _infer_instance_method(
    body: Expr,
    params: list[str],
    method_type: Type,
    sc_types: dict[Name, Type],
    cons: dict[str, ConInfo] | None = None,
    classes: dict[str, ClassInfo] | None = None,
    context: list[Predicate] | None = None,
    sc_constraints: dict[Name, tuple] | None = None,
) -> tuple[list[Predicate], list[Predicate]]:
    """Type-check one instance method body against its specialised type.

    ``method_type`` is the class's declaration for the method with the
    class parameter replaced by the instance head, so `show : a -> Int`
    for `instance Show (Wrap a)` is checked as `Wrap a -> Int`.

    Returns ``(body_predicates, context_predicates)``.  Each body
    predicate is tagged with the occurrence that produced it
    (``Predicate.site``) so elaboration can give every call its own
    dictionary, and the context predicates come back under the same
    substitution — a body constraint and the context predicate that
    discharges it are only recognisable as the same constraint once both
    have been substituted.
    """
    # A supercombinator with a class context has to enter the environment
    # *with* it, or its occurrence in the body emits no predicate and
    # elaboration has nothing to route — the call then goes out without
    # its dictionary argument.  `showItems : (Show a) => …` called from
    # `instance Show (List a)` is the case that showed it up.
    constrained = sc_constraints or {}
    env: dict[Name, Scheme] = {}
    for n, t in sc_types.items():
        preds = tuple(constrained.get(n, ()))
        # A supercombinator's type is closed — nothing encloses a top-level
        # definition — so every variable in it is quantified, whether or not
        # the definition also carries a context.  Entering an unconstrained
        # one monomorphically used to work by accident: the first use bound
        # its variables and a second use at another type simply lost.  Once
        # signature variables are rigid (`fixme.md` F36) the first use
        # *fails*, this whole body goes uninferred, and routing falls back
        # to by-name — which inside `instance (Show a) => Show (List a)`
        # cannot tell the context dictionary from a recursive call.  That
        # is `show` for lists, and it is why this quantifies.
        quant = free_vars(t)
        for p in preds:
            quant |= free_vars(p.type_)
        env[n] = Scheme(frozenset(quant), t, preds)
    fresh = Fresh()
    constraints: list[Predicate] = []
    s = check(env, ELambda(list(params), body), method_type, fresh,
              cons or {}, classes or {}, constraints)
    # The same final pass `infer_program` runs (`fixme.md` F58).  Without it
    # a `fix` or a `{}` in a method body reaches codegen still annotated
    # with a metavariable, and the helper name is derived from that.
    settle_annotations(body, s, cons)
    return (
        [Predicate(p.class_name, s.apply(p.type_), p.site) for p in constraints],
        [Predicate(p.class_name, s.apply(p.type_)) for p in (context or [])],
    )


#: Classes that make an ambiguous type variable default.  Haskell requires
#: at least one *numeric* class before it will default; `Eq`/`Ord` alone
#: are accepted here too, because `Int` is the only type gestate has
#: primitives for and refusing would only turn a working program into an
#: error nobody can act on.
_DEFAULTING_TRIGGERS = frozenset({"Num", "Eq", "Ord", "Floating"})


def _default_ambiguous_vars(s: Subst, per_sc: list[list[Predicate]],
                            env: dict) -> Subst:
    """Bind `Int` to the type variables no result type mentions.

    A literal's type variable is constrained (`Num a`) but does not escape
    into any supercombinator's type, so nothing will ever bind it —
    `show 42` leaves `(Num a, Show a)` with `a` open.  Defaulting has to
    happen *here*, as a substitution, rather than per-predicate at
    resolution time: it must reach every constraint on the variable at
    once, and the node annotations and reported types with them.  Deciding
    it one predicate at a time is what let `Show a` pick whichever `Show`
    instance came first — `show 42` rendered as a character.

    A variable that *does* occur in a result type is either genuinely
    polymorphic or pinned by its use, and is left alone.  So is a rigid
    one: a signature variable is chosen by the caller, never by defaulting.
    """
    by_var: dict[int, set[str]] = {}
    for preds in per_sc:
        for p in preds:
            t = s.apply(p.type_)
            if isinstance(t, TVar) and not t.rigid:
                by_var.setdefault(t.id, set()).add(p.class_name)
    if not by_var:
        return s

    escaping: set[int] = set()
    for scheme in env.values():
        escaping |= free_vars(s.apply(scheme.type_))
        for p in scheme.constraints:
            escaping |= free_vars(s.apply(p.type_))

    for vid, classes in by_var.items():
        if vid in escaping or not (classes & _DEFAULTING_TRIGGERS):
            continue
        # **`Floating` decides it, when it is there.**  A variable a float
        # literal reached cannot be `Int` — `Floating Int` is not an
        # instance and never should be — so the default follows the
        # constraint that admits fewer types, and `1.5` on its own is the
        # `Float` it always was.
        s = s.extend(vid, TCon("Float" if "Floating" in classes else "Int"))
    return s


def _blame(exc: Exception, name: str, lam) -> None:
    """Append `while checking \\`name\\` (at L:C)` to an error, in place.

    In place — mutating `message` and `args` — because the exception may
    be any `InferError` subclass and rebuilding one through its own
    constructor is a signature nobody should have to keep compatible.
    On its own line, so a status bar keeps showing the mismatch and the
    content box under the line shows both.  Idempotent, in case an
    inner layer learns to say it first.
    """
    said = getattr(exc, "message", None) or (exc.args[0] if exc.args else "")
    if "while checking" in str(said):
        return
    said = f"{said}\nwhile checking `{name}`{_site_of(lam)}"
    exc.message = said
    exc.args = (said,)


def _site_of(node, depth: int = 0) -> str:
    """The first written-down position inside a lifted declaration.

    The lifted lambda and the applications the desugaring builds carry
    no spans; the leaves the author actually typed do.  **Expressions
    only, never types**: a `set_type` hanging off a node carries the
    span of wherever that type was *declared* — the prelude, for
    anything instantiated from its signatures — and blaming the prelude
    is the exact mistake this walk exists to stop.
    """
    from .expr import Expr

    if depth > 24 or not isinstance(node, Expr):
        return ""
    said = at(node)
    if said:
        return said
    for child in vars(node).values():
        if isinstance(child, Expr):
            said = _site_of(child, depth + 1)
        elif isinstance(child, (list, tuple)):
            said = next((s for c in child
                         if (s := _site_of(c, depth + 1))), "")
        else:
            continue
        if said:
            return said
    return ""


def infer_program(
    scs: list[tuple[str, int, ELambda, Type | None]],
    builtins: dict[Name, Type] | None = None,
    cons: dict[str, ConInfo] | None = None,
    classes: dict[str, ClassInfo] | None = None,
    sc_constraints: dict[str, list[Predicate]] | None = None,
    *,
    imports: dict[Name, Scheme] | None = None,
    fresh: "Fresh | None" = None,
    export: dict | None = None,
) -> tuple[dict[str, Type], list[list[Predicate]], list[list[Predicate]]]:
    """Type-check a group of supercombinators.

    Runs inside `unifying()`, which makes every `Subst.empty()` below hand
    back the same destructive store, so the substitution threading costs
    nothing (`fixme.md` F78).  Everything returned has been through
    `s.apply`, so nothing escapes still pointing into a store that is about
    to go away.

    ``imports`` are *schemes*, not types, and that is the whole point of
    the parameter: a `builtins` entry is monomorphic, so a library's `map`
    seeded through it would be pinned to one caller's types for everybody.
    An import is instantiated fresh at every use, exactly as a signature
    is.  ``fresh`` lets a caller start the variable counter above another
    run's, so a stack analysed earlier and a program analysed now cannot
    mint the same variable; ``export``, when given, is filled with each
    SC's final scheme — type *and* constraints, the half `results` drops —
    which is what a later run needs to import.
    """
    with unifying():
        return _infer_program(scs, builtins, cons, classes, sc_constraints,
                              imports=imports, fresh=fresh, export=export)


def _infer_program(
    scs: list[tuple[str, int, ELambda, Type | None]],
    builtins: dict[Name, Type] | None = None,
    cons: dict[str, ConInfo] | None = None,
    classes: dict[str, ClassInfo] | None = None,
    sc_constraints: dict[str, list[Predicate]] | None = None,
    *,
    imports: dict[Name, Scheme] | None = None,
    fresh: Fresh | None = None,
    export: dict | None = None,
) -> tuple[dict[str, Type], list[list[Predicate]], list[list[Predicate]]]:
    """Type-check a group of supercombinators.

    ``sc_constraints`` are the contexts written in signatures.  They are
    *given*: the body may assume them, and each use site instantiates
    them as constraints to satisfy.

    Returns ``(name -> final_type, per_sc_constraints, per_sc_givens)``.
    ``per_sc_constraints`` is the list of predicates emitted while
    type-checking each SC; ``per_sc_givens`` is its declared context
    under the final substitution.
    """
    if builtins is None: builtins = {}
    if cons is None: cons = {}
    if classes is None: classes = {}
    if sc_constraints is None: sc_constraints = {}

    env: dict[Name, Scheme] = {n: scheme_mono(t) for n, t in builtins.items()}
    imported = frozenset(imports) if imports else frozenset()
    if imports:
        env.update(imports)
    if fresh is None:
        fresh = Fresh()
    all_constraints: list[Predicate] = []
    per_sc: list[list[Predicate]] = []

    for name, _arity, _lam, sig in scs:
        t = sig if sig is not None else fresh.tv()
        given = tuple(sc_constraints.get(name, ()))
        if sig is not None and (given or free_vars(sig)):
            # A signature with type variables is polymorphic: quantify
            # them so each use site gets its own instance, and carry the
            # declared context so each use site emits it.
            quant = free_vars(sig)
            for g in given:
                quant |= free_vars(g.type_)
            env[name] = Scheme(frozenset(quant), t, given)
        else:
            env[name] = scheme_mono(t)

    signed = {name for name, _a, _l, sig in scs if sig is not None}

    s = Subst.empty()
    for i, (name, _arity, lam, sig) in enumerate(scs):
        before = len(all_constraints)
        # **An error names the declaration it surfaced in.**  The
        # positions inside a message are the *types'* — a signature in
        # the prelude donates its own span, so a misuse of `flip` was
        # reported "at prelude line 216" with the author's file never
        # mentioned.  The one fact inference always has and the message
        # always lacked is which declaration was being checked, so it
        # is appended on its own line; `session._line_of` prefers a
        # position in the author's file anywhere in the message, which
        # is what anchors the complaint's box at *your* definition when
        # every other position is the prelude's.
        try:
            if sig is not None:
                s = s.compose(check(env, lam, sig, fresh, cons, classes,
                                    all_constraints))
                t = sig
            else:
                t, si = infer(env, lam, fresh, cons, classes,
                              all_constraints)
                s = si.compose(s)
            s = s.compose(unify(env[name].type_, t))
        except (UnifyError, InferError) as exc:
            _blame(exc, name, lam)
            raise
        # Collect constraints emitted during this SC
        per_sc.append(list(all_constraints[before:]))
        # Update env types with current substitution — except where the
        # user wrote a signature.  That signature is a contract: its type
        # variables stand for "any type the caller picks", and every use
        # site instantiates them fresh.  Letting the substitution reach
        # the scheme lets one use site bind them for everybody, so the
        # prelude showing a `String` with `append` would monomorphise
        # `append : List a -> List a -> List a` to `Char` for the whole
        # program (`fixme.md` F36).
        for n in env:
            if n in signed or n in imported:
                # An import's variables are the exporting run's and are all
                # quantified; substituting is a no-op paid per SC.
                continue
            env[n] = _subst_scheme(env[n], s)
        # Attach filtered constraints to this SC's scheme so
        # subsequent SCs see them during their own inference.  A declared
        # context is the user's contract — leave it alone.
        if not sc_constraints.get(name):
            _attach_sc_constraints(env, name, per_sc[i], s)

    s = _default_ambiguous_vars(s, per_sc, env)

    results: dict[str, Type] = {}
    for name, _arity, _lam, _sig in scs:
        results[name] = s.apply(env[name].type_)

    # Build final env for generalization — include per-SC constraints
    # from the already-attached schemes so that constraint TVars are
    # properly quantified.
    final_env: dict[Name, Scheme] = {}
    for name, _arity, _lam, _sig in scs:
        final_env[name] = scheme_mono(results[name])
    for n, t in builtins.items():
        final_env[n] = scheme_mono(t)
    if imports:
        for n, sch in imports.items():
            final_env.setdefault(n, sch)

    for name in results:
        other_env = {n: final_env[n] for n in final_env if n != name}
        inferred = env[name].constraints
        results[name] = generalize(other_env, results[name], inferred).type_

    if export is not None:
        # Each SC's final *scheme*: the generalized type together with its
        # constraints under the final substitution — declared for a signed
        # SC, attached for an inferred one, read off the same place either
        # way.  Quantify everything free, so an importer's substitution
        # can never reach in.
        for name, _arity, _lam, _sig in scs:
            given = tuple(Predicate(p.class_name, s.apply(p.type_), p.site)
                          for p in env[name].constraints)
            quant = free_vars(results[name])
            for g in given:
                quant |= free_vars(g.type_)
            export[name] = Scheme(frozenset(quant), results[name], given)

    # `chan`'s element type was recorded when the occurrence was visited,
    # so it may still be a metavariable that got solved later in the same
    # SC (`c = chan` with the type coming from `c`'s signature).
    for _name, _arity, lam, _sig in scs:
        settle_annotations(lam, s, cons)

    # Apply final substitution to all predicates
    def apply_to_pred(p: Predicate) -> Predicate:
        return Predicate(p.class_name, s.apply(p.type_), p.site)

    givens = [_givens_of(name, sig, sc_constraints, env, apply_to_pred)
              for name, _arity, _lam, sig in scs]

    return results, [[apply_to_pred(p) for p in sl] for sl in per_sc], givens


def _givens_of(name, sig, sc_constraints, env, apply_to_pred) -> list:
    """The constraints this supercombinator takes a **dictionary** for.

    A declared context is the author's contract and is taken as written.
    What was missing is the other half: an SC with **no signature** whose
    inferred type is polymorphic has been generalised over constraints by
    `_attach_sc_constraints` — its scheme carries them, and every use site
    duly emits them — and it was given no dictionary parameters all the
    same.

    **That is an ill-typed program accepted, and wrong at run time.**

        melody = pure 60 ++ pure 62          -- no signature
        score  = melody >>= prog 0

    `melody`'s own `Monad m` was resolved where it was defined, by picking
    the first instance that matched an unsolved variable — `List` — while
    `score`'s use site resolved its copy at `Score`.  Two instances for one
    value, silently, and then `CaseJump: no alt for tag 13` from a
    `List` meeting a `Score`'s alternatives.  Nothing reported anything.

    Only constraints still standing on a *type variable* count.  One that
    came out concrete — `Num Float` — is discharged by an instance and not
    by a parameter, and one that reached the same class at the same type
    twice is one dictionary, not two.

    **A written signature is taken at its word.**  `f : a -> String ; f x =
    show x` declares no context, and the `Show a` its body needs is
    therefore *unsatisfiable* — the error `test_skolems.py` exists to
    check, which says to write `(Show a) => …`.  Inferring the given here
    would grant the context the author did not write and turn three of
    those errors into silently accepted programs.  Inference fills in only
    where the author wrote nothing at all.
    """
    declared = sc_constraints.get(name)
    if declared:
        return [apply_to_pred(g) for g in declared]
    if sig is not None:
        return []
    scheme = env.get(name)
    if scheme is None or not scheme.constraints:
        return []
    kept: list = []
    for pred in scheme.constraints:
        settled = apply_to_pred(pred)
        if free_vars(settled.type_) and settled not in kept:
            kept.append(settled)
    return kept
