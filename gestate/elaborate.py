"""Elaboration: surface + constraints → dictionary-passing Expr.

Every instance becomes a **dictionary**: a tuple of its method closures,
built by a generated supercombinator whose parameters are the
dictionaries of the instance's context.  ``Show (List Int)`` is then the
expression ``__dict_Show_List__ __dict_Show_Int__``, and a call to a
class method is a projection out of that tuple, ``(#0 dict) x``.

Per-SC constraint tracking picks the dictionary for each call site, so
calls at different types route to the correct instance.  Type-level
integers (TInt) in instance heads are extracted as implicit parameter
values and baked into the dictionary's slot.
"""

from __future__ import annotations

from .expr import map_children, subexprs
from .expr import (
    EAp, ECase, ECon, EGlobal, ELambda, EProj, ETuple, EVar, ENum, Expr,
    Name, Alter,
)
from .syntax.ast import PVar
from .types import Predicate, Type, TApp, TCon, TInt
from .constraint import (
    RESOLUTION_DEPTH_CAP, _default_ambiguous, match_head, rigid_hint,
    solve_predicate, subst_vars,
)
from .declarations import InstanceInfo, Program
from .desugar import desugar_expr
from .infer import InferError, infer_instance_method
from .unify import UnifyError
from .show import show_predicate, show_type


class ElaborateError(Exception):
    pass


#: Classes whose method bodies the compiler generates itself.
_GENERATED_CLASSES = ("Num", "Eq", "Ord", "Floating", "Div", "Signed")


def check_main_has_no_context(constrained) -> None:
    """`main` takes no dictionary, so it may not declare a context.

    Checked before constraint resolution as well as here: the body of a
    `main : (Sum a) => a` will usually *also* fail to satisfy some
    constraint at the signature's rigid variable, and that error explains
    the program far less well than this one.
    """
    if "main" in constrained:
        raise ElaborateError(
            "'main' cannot have a class context: nothing calls it, so there "
            "is no caller to supply the dictionary — give it a concrete type"
        )


def elaborate(
    scs: list[tuple[str, int, ELambda, object]],
    per_sc_constraints: list[list[Predicate]],
    resolved: dict[Predicate, InstanceInfo],
    program: Program,
    sc_types: dict[Name, Type] | None = None,
    per_sc_givens: list[list[Predicate]] | None = None,
) -> list[tuple[str, int, ELambda, object]]:
    givens_of = per_sc_givens or [[] for _ in scs]
    # An SC with a declared context takes one dictionary per constraint,
    # ahead of its own parameters, and every call site supplies them.
    constrained = {name: len(givens_of[i])
                   for i, (name, _a, _l, _s) in enumerate(scs)
                   if i < len(givens_of) and givens_of[i]}
    check_main_has_no_context(constrained)
    dicts = _Dictionaries(program, resolved, sc_types, constrained)

    result: list[tuple[str, int, ELambda, object]] = []
    for i, (name, arity, lam, sig) in enumerate(scs):
        sc_preds = per_sc_constraints[i] if i < len(per_sc_constraints) else []
        givens = givens_of[i] if i < len(givens_of) else []
        dict_params = [f"_g{k}" for k in range(len(givens))]
        assumptions = tuple(zip(givens, [EVar(p) for p in dict_params]))

        # Per-occurrence routing where inference recorded a site, plus a
        # by-name fallback for occurrences it did not reach.
        by_site = _group_by_site(sc_preds)
        by_name: dict[str, Expr] = {}
        for pred in sc_preds:
            inst = resolved.get(pred)
            if inst is None:
                continue
            dict_e = dicts.dict_expr(pred, assumptions)
            for mname in inst.methods:
                by_name[mname] = EAp(
                    EProj(dicts.method_index(inst.class_name, mname)), dict_e)

        router = _Router(dicts, by_site, by_name, {}, assumptions)
        params = dict_params + list(lam.params)
        try:
            body = _rewrite(lam.body, router)
        except ElaborateError as exc:
            # The same breadcrumb `infer._blame` writes: whatever went
            # wrong, the reader is told whose declaration it was in and
            # where, so an invariant tripping deep in a rewrite never
            # again reaches `trouble` as a bare sentence about a
            # mangled name (`fixme.md` F105's second half).
            from .infer import _blame

            _blame(exc, str(name), lam)
            raise
        result.append((name, len(params), ELambda(params, body), sig))

    return result + dicts.extra_scs


def _group_by_site(preds: list[Predicate]) -> dict[int, list[Predicate]]:
    """Predicates per occurrence, in emission (i.e. declaration) order.

    **Deduplicated within a site.**  A site is one occurrence the author
    wrote, but inference may visit it many times: the match compiler
    shares an equation's body across the leaves of its decision tree, so
    a `'` in an arm behind the string pattern `"question"` is inferred
    once per leaf — seventeen identical `Monad Score` predicates on one
    stamp, and the arity check below read the repetition as inference
    having produced seventeen dictionaries (`fixme.md` F105).  One
    occurrence has one type, so equal predicates are one predicate; a
    *different* predicate on the same stamp still comes through, and the
    mismatch it causes is real.
    """
    grouped: dict[int, list[Predicate]] = {}
    for p in preds:
        if p.site is None:
            continue
        rows = grouped.setdefault(p.site, [])
        if not any(q.class_name == p.class_name and q.type_ == p.type_
                   for q in rows):
            rows.append(p)
    return grouped


class _Router:
    """Decides what a class-method reference becomes.

    Preference order: the predicate inferred for *this occurrence* (so two
    calls to `show` at different types get different dictionaries), then
    the by-name map (used where the body was not inferred), then nothing.
    """

    def __init__(self, dicts: "_Dictionaries",
                 by_site: dict[int, list[Predicate]] | None = None,
                 by_name: dict[str, Expr] | None = None,
                 ambiguous: dict[str, str] | None = None,
                 assumptions: tuple[tuple[Predicate, Expr], ...] = ()):
        self.dicts = dicts
        self.by_site = by_site or {}
        self.by_name = by_name or {}
        self.ambiguous = ambiguous or {}
        self.assumptions = assumptions

    def route(self, node: EGlobal) -> Expr | None:
        preds = self.by_site.get(getattr(node, "site_token", None))
        if preds:
            arity = self.dicts.constrained.get(node.name)
            if arity:
                # A call to a supercombinator with a context: pass one
                # dictionary per declared constraint, in order.
                if len(preds) != arity:
                    # An internal invariant, but it reaches `trouble`
                    # when it trips, so it is spelled for the reader:
                    # the name in backticks (`'` used to render as
                    # `'''`), what was expected against what arrived,
                    # and the caller below adds whose declaration it
                    # happened in.
                    got = ", ".join(sorted({f"{p.class_name} "
                                            f"{show_type(p.type_)}"
                                            for p in preds}))
                    raise ElaborateError(
                        f"`{node.name}` expects {arity} dictionary "
                        f"argument(s), inference produced {len(preds)} "
                        f"({got})"
                    )
                call: Expr = EGlobal(node.name)
                for pred in preds:
                    call = EAp(call, self.dicts.dict_expr(pred, self.assumptions))
                return call
            pred = preds[0]
            cls = self.dicts.program.classes.get(pred.class_name)
            if cls is not None and node.name in cls.methods:
                return EAp(
                    EProj(self.dicts.method_index(pred.class_name, node.name)),
                    self.dicts.dict_expr(pred, self.assumptions),
                )
        if node.name in self.ambiguous:
            raise ElaborateError(
                f"Cannot tell which dictionary '{node.name}' needs: "
                f"{self.ambiguous[node.name]}"
            )
        return self.by_name.get(node.name)


# ---------------------------------------------------------------------------
# Dictionary construction
# ---------------------------------------------------------------------------

class _Dictionaries:
    """Builds the dictionary and method supercombinators on demand."""

    def __init__(self, program: Program,
                 resolved: dict[Predicate, InstanceInfo],
                 sc_types: dict[Name, Type] | None = None,
                 constrained: dict[str, int] | None = None):
        self.program = program
        self.resolved = resolved
        self.sc_types = sc_types or {}
        self.constrained = constrained or {}   # SC name → dictionary count
        self.extra_scs: list[tuple[str, int, ELambda, object]] = []
        self._built: set[str] = set()

    # -- lookups ------------------------------------------------------------

    def method_index(self, class_name: str, mname: str) -> int:
        """Slot of ``mname`` in ``class_name``'s dictionary."""
        cls = self.program.classes.get(class_name)
        if cls is None or mname not in cls.methods:
            raise ElaborateError(
                f"Class '{class_name}' has no method '{mname}'"
            )
        return list(cls.methods).index(mname)

    def dict_expr(self, pred: Predicate,
                  assumptions: tuple[tuple[Predicate, Expr], ...] = (),
                  depth: int = 0) -> Expr:
        """The dictionary expression satisfying ``pred``.

        ``assumptions`` are the dictionaries already in scope — inside an
        instance method those are its context parameters, which is what
        makes a recursive instance work: the dictionary for
        ``Show (List a)`` inside that very instance is
        ``__dict_Show_List__ _d0``, not an infinite regress.

        An instance with a context becomes an application: the dictionary
        for ``Show (List Int)`` is ``__dict_Show_List__`` applied to the
        dictionary for ``Show Int``.
        """
        for assumed, expr in assumptions:
            if (assumed.class_name == pred.class_name
                    and assumed.type_ == pred.type_):
                return expr
        # Past the assumptions, a predicate still on a bare type variable
        # is genuinely ambiguous — an instance context would have matched
        # above — so it defaults like any other.  Without this, a variable
        # matches *every* head and resolution takes whichever instance is
        # declared first: the element dictionary for `[1,2] == [1,3]`
        # came back as `Eq Bool`.
        pred = _default_ambiguous(pred)
        if depth > RESOLUTION_DEPTH_CAP:
            raise ElaborateError(
                f"dictionary construction exceeded depth "
                f"{RESOLUTION_DEPTH_CAP} for {show_predicate(pred)}"
            )
        inst = self.resolved.get(pred)
        if inst is None:
            inst = solve_predicate(pred, self.program.instances)
        if inst is None:
            raise ElaborateError(
                f"No instance for {show_predicate(pred)}{rigid_hint(pred)}")

        expr = EGlobal(self._build(inst))
        bindings = match_head(inst.head_type, pred.type_) or {}
        for ctx_pred in inst.context:
            arg = Predicate(ctx_pred.class_name,
                            subst_vars(ctx_pred.type_, bindings))
            expr = EAp(expr, self.dict_expr(arg, assumptions, depth + 1))
        return expr

    # -- generation ---------------------------------------------------------

    def _build(self, inst: InstanceInfo) -> str:
        """Emit ``inst``'s dictionary SC (once); return its name."""
        name = _dict_sc_name(inst)
        if name in self._built:
            return name
        self._built.add(name)

        params = [f"_d{i}" for i in range(len(inst.context))]
        if inst.class_name in _GENERATED_CLASSES:
            ctx_map, ambiguous = {}, {}   # bodies are generated, not desugared
        else:
            ctx_map, ambiguous = self._context_map(inst, params)
        uv = _extract_using(inst.predicate, inst)

        slots: list[Expr] = []
        for mname in self.program.classes[inst.class_name].methods:
            eq = inst.methods.get(mname)
            if eq is None:
                # The instance leaves this method undefined.  The slot has
                # to hold *something* — the dictionary is a tuple built
                # eagerly — but it must not hold a value: `Unwind` on a
                # number ignores the spine, so a numeric placeholder makes
                # `x + y` quietly evaluate to it.  An unbound global fails
                # instead, and only if the slot is actually projected.
                slots.append(EGlobal(
                    f"__undefined_{inst.class_name}_{mname}__"))
                continue
            using = list(eq.using_params or [])
            method_params = params + using + _method_frame(eq)
            self.extra_scs.append((
                _method_sc_name(inst, mname), len(method_params),
                ELambda(method_params,
                        self._method_body(inst, mname, eq, using, uv,
                                          method_params, params,
                                          ctx_map, ambiguous)),
                self._method_type(inst, mname, params, using),
            ))
            # The slot closes over the context dictionaries and the
            # implicit (`using`) values, leaving the method's own
            # parameters to the call site.
            slot: Expr = EGlobal(_method_sc_name(inst, mname))
            for p in params:
                slot = EAp(slot, EVar(p))
            for u in using:
                slot = EAp(slot, ENum(uv[u]) if u in uv else EVar(u))
            slots.append(slot)

        self.extra_scs.append(
            (name, len(params), ELambda(params, ETuple(slots)), None))
        return name

    def _method_type(self, inst: InstanceInfo, mname: str,
                     params: list[str], using: list[str]):
        """This instance's method type, when there *is* one to state.

        A generated method supercombinator used to carry no signature at
        all, and nothing downstream could work one out: it is not in the
        source, so inference never saw it, and its name is invented here.
        Every pass that asks a definition its type therefore had to give
        up on instance methods — which is why the audio fragment refused
        `instance Num (Sig Float)` with "calls `__Num_Sig_Float_*__`,
        whose type is not known" (`spec/frp_lesson.md`).  A synth may now
        say `tone * env` and mean it, and that is Fran's whole trick: a
        signal is a value, and arithmetic on values is arithmetic.

        Stated only when it is *honest*, which is three conditions:

        * **No context dictionaries.**  `instance (Eq a) => Eq (List a)`
          takes its context as extra leading parameters, so the method SC
          is wider than the method's type; declaring the narrow one would
          claim a monomorphic definition where there is a dictionary.
        * **No `using` parameters**, which are implicit values passed the
          same way.
        * **A ground head.**  `Eq (List a)` leaves `a` free, so no
          substitution produces a type without variables in it.

        Everything else keeps the `None` it had, so this can only add
        knowledge — a pass that used to see nothing now sees a type or
        still sees nothing.
        """
        from .types import free_vars

        if params or using:
            return None
        cls = self.program.classes.get(inst.class_name)
        if cls is None:
            return None
        scheme = cls.methods.get(mname)
        if scheme is None or free_vars(inst.head_type):
            return None
        # The class parameter *is* the instance head, which is what an
        # instance says.  `Num (Sig Float)` therefore has
        # `+ : Sig Float -> Sig Float -> Sig Float`.
        bindings = {tv.id: inst.head_type for tv in cls.param_tvs}
        return subst_vars(scheme, bindings)

    def _method_body(self, inst: InstanceInfo, mname: str, eq, using: list[str],
                     uv: dict[str, int], method_params: list[str],
                     dict_params: list[str],
                     ctx_map: dict[str, Expr],
                     ambiguous: dict[str, str]) -> Expr:
        # `Eq`/`Ord`/`Num` are declared by the compiler, but only their
        # *built-in* instances have generated bodies — those are the ones
        # that reach the integer primitives.  A declared `instance Eq Bool`
        # supplies its own methods like any other instance; short-cutting
        # on the class name is what confined equality to integers
        # (`fixme.md` F11).
        if inst.builtin:
            if inst.class_name == "Num":
                return _num_body(inst.head_type, mname, using, uv)
            if inst.class_name == "Floating":
                # `Floating Float` is the identity: the literal is already
                # a `Float`, and the class exists so that other types can
                # say what one means *to them*.
                return EVar("x")
            if inst.class_name == "Div":
                return _div_body(inst.head_type, mname)
            if inst.class_name == "Signed":
                return _signed_body(inst.head_type, mname, self.program.cons)
            if inst.class_name == "Eq":
                return _eq_body(mname, self.program.cons)
            if inst.class_name == "Ord":
                return _ord_body(mname, self.program.cons)

        own_params = _method_frame(eq)
        body = _method_equation_body(eq, own_params, method_params,
                                     self.program.cons, self.program.aliases)
        by_site, context = self._infer_sites(inst, mname, body, own_params)
        # The context dictionaries are in scope as this method's leading
        # parameters, so a call at a context type uses the parameter and a
        # recursive call rebuilds this same dictionary from it.
        assumptions = tuple(
            (pred, EVar(dict_params[i])) for i, pred in enumerate(context))
        return _rewrite(body, _Router(self, by_site, ctx_map, ambiguous,
                                      assumptions))

    def _infer_sites(self, inst: InstanceInfo, mname: str, body: Expr,
                     params: list[str]
                     ) -> tuple[dict[int, Predicate], list[Predicate]]:
        """Type-check an instance method body to learn each call's type.

        Returns the per-occurrence predicates and the instance context
        under the same substitution.  Failure is not fatal: the by-name
        routing from ``_context_map`` still applies, so a body this
        cannot check elaborates exactly as it did before.
        """
        cls = self.program.classes.get(inst.class_name)
        if cls is None or mname not in cls.methods or not cls.param_tvs:
            return {}, list(inst.context)
        method_type = subst_vars(cls.methods[mname],
                                 {cls.param_tvs[0].id: inst.head_type})
        try:
            preds, context = infer_instance_method(
                body, params, method_type, self.sc_types,
                self.program.cons, self.program.classes, inst.context,
                {sc.name: tuple(sc.sig_constraints)
                 for sc in self.program.scs if sc.sig_constraints})
        except (InferError, UnifyError):
            return {}, list(inst.context)
        return (_group_by_site(preds), context)

    def _context_map(self, inst: InstanceInfo,
                     params: list[str]) -> tuple[dict[str, Expr], dict[str, str]]:
        """Route method calls in ``inst``'s body to its context dictionaries.

        Instance bodies are not type-inferred, so the routing is by class:
        a call to a method of class ``C`` goes to the context dictionary
        for ``C``.  When that is not enough to identify the dictionary the
        name is recorded as ambiguous, and using it is an error rather
        than a silent miscompilation.
        """
        ctx_map: dict[str, Expr] = {}
        ambiguous: dict[str, str] = {}
        by_class: dict[str, list[str]] = {}

        for i, pred in enumerate(inst.context):
            by_class.setdefault(pred.class_name, []).append(params[i])

        for class_name, dict_params in by_class.items():
            cls = self.program.classes.get(class_name)
            if cls is None:
                continue
            for mname in cls.methods:
                if len(dict_params) > 1:
                    ambiguous[mname] = (
                        f"the context of instance {inst} constrains class "
                        f"'{class_name}' at more than one type"
                    )
                elif class_name == inst.class_name:
                    # Could be the context dictionary or a recursive call
                    # to this very instance; without inference on instance
                    # bodies there is no way to tell them apart.
                    ambiguous[mname] = (
                        f"instance {inst} is an instance of '{class_name}' "
                        f"and also constrains it, so a call to '{mname}' in "
                        f"its body could mean either the context dictionary "
                        f"or a recursive call"
                    )
                else:
                    ctx_map[mname] = EAp(EProj(self.method_index(class_name, mname)),
                                         EVar(dict_params[0]))

        # Arithmetic and comparison in an instance body have no inferred
        # type either — a literal is just `fromInteger n`.  Default those
        # to `Int`, the way Haskell defaults an ambiguous `Num` — except
        # `Floating`, whose whole point is that its literal is not an `Int`
        # and whose only built-in instance is at `Float`.
        for class_name in _GENERATED_CLASSES:
            cls = self.program.classes.get(class_name)
            if cls is None or class_name in by_class:
                continue
            head = TCon("Float" if class_name == "Floating" else "Int")
            default = None
            for mname in cls.methods:
                if mname in ctx_map or mname in ambiguous:
                    continue
                if default is None:
                    default = self.dict_expr(Predicate(class_name, head))
                ctx_map[mname] = EAp(EProj(self.method_index(class_name, mname)),
                                     default)
        return ctx_map, ambiguous


# ---------------------------------------------------------------------------
# Using-param extraction
# ---------------------------------------------------------------------------

def _extract_using(pred: Predicate, inst: InstanceInfo) -> dict[str, int]:
    """Extract type-level integer values from predicate's concrete type args."""
    up: list[str] = []
    for m in inst.methods.values():
        if hasattr(m, 'using_params') and m.using_params:
            up = m.using_params
            break
    if not up:
        return {}
    args = _type_args(pred.type_)
    result = {}
    for i, name in enumerate(up):
        if i < len(args) and isinstance(args[i], TInt):
            result[name] = args[i].n
    return result


def _type_args(t: Type) -> list[Type]:
    """Collect the type arguments of a TApp chain, left to right."""
    args: list[Type] = []
    while isinstance(t, TApp):
        args.insert(0, t.arg)
        t = t.fn
    return args


# ---------------------------------------------------------------------------
# Rewrite method calls
# ---------------------------------------------------------------------------

def _rewrite(expr: Expr, router: _Router) -> Expr:
    """Replace each class-method reference with its dictionary projection.

    Only ``EGlobal`` is interesting; everything else is a structural walk,
    so it goes through ``map_children`` rather than a per-node table.  A
    hand-written table silently missed whichever node kind was added last
    — and dropped the annotations inference leaves on the tree.
    """
    if isinstance(expr, EGlobal):
        replacement = router.route(expr)
        return replacement if replacement is not None else expr
    return map_children(expr, lambda child: _rewrite(child, router))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _method_frame(eq) -> list[str]:
    """The frame parameter names of a method equation.

    A `PVar` keeps its own name; anything else gets a fresh one, because
    the value has to be *matched* rather than bound.  This used to read
    `p.name for p in eq.params if hasattr(p, "name")`, and a `PCon` has a
    `.name` too — the *constructor's* — so `get (P x y) = x` contributed a
    parameter called `"P"` and never bound `x` at all (`fixme.md` F69).  A
    `PTuple` has no `.name` and was dropped instead, losing the parameter.
    """
    return [p.name if isinstance(p, PVar) else f"_mp{i}"
            for i, p in enumerate(eq.params)]


def _method_equation_body(eq, own_params: list[str], scope: list[str],
                          cons, aliases) -> Expr:
    """Desugar a method's body, compiling its parameter patterns.

    Supercombinator equations go through the match compiler
    (`desugar._desugar_pattern_sc`); method equations did not, which is
    why a constructor pattern in one silently lost its bindings.
    """
    from .desugar import DesugarError
    from .match import MatchError, Matcher, Row, fail_expr, normalize

    if all(isinstance(p, PVar) for p in eq.params):
        return desugar_expr(eq.body, frozenset(scope), cons, {}, aliases)

    matcher = Matcher(
        cons,
        lambda val, loc: desugar_expr(val, loc, cons, {}, aliases),
        where="instance method",
    )
    rows = [Row([normalize(p) for p in eq.params], eq.body)]
    try:
        return matcher.compile(own_params, rows, fail_expr(), frozenset(scope))
    except MatchError as e:
        raise DesugarError(str(e)) from None


def _type_name(t: object) -> str:
    if isinstance(t, TCon):
        return t.name
    return str(t).replace(" ", "_").replace("(", "").replace(")", "")


def _method_sc_name(inst: InstanceInfo, mname: str) -> str:
    """Per-method SC name: ``__Eq_Int_==__`` etc."""
    return f"__{inst.class_name}_{_type_name(inst.head_type)}_{mname}__"


def _dict_sc_name(inst: InstanceInfo) -> str:
    """Dictionary SC name: ``__dict_Eq_Int__`` etc."""
    return f"__dict_{inst.class_name}_{_type_name(inst.head_type)}__"


def _num_body(head: Type, mname: str, using_params: list[str],
              using_values: dict[str, int]) -> Expr:
    x = EVar("x")
    y = EVar("y")

    def modulus() -> Expr | None:
        """`n` of a `Cyclic n`, as the value if it is known statically."""
        if not (isinstance(head, TApp) and isinstance(head.fn, TCon)
                and head.fn.name == "Cyclic"):
            return None
        n_name = using_params[0] if using_params else "n"
        return (ENum(using_values[n_name]) if n_name in using_values
                else EVar(n_name))

    def wrap(e: Expr) -> Expr:
        """Bring a result back into `Cyclic n`.

        Every operation has to, not just `fromInteger` — `3 + 3` at
        `Cyclic 4` is 2, and a `Cyclic n` whose values escaped its range
        would not be the finite type the fixtype rule takes it for.
        """
        n = modulus()
        return EAp(EAp(EGlobal("prim_mod_int"), e), n) if n is not None else e

    # `Num Float`.  `fromInteger` really converts here rather than passing
    # the value through: an `Int`-valued cell would compute correctly but
    # print as `1` where the type says `1.0`.
    if isinstance(head, TCon) and head.name == "Float":
        if mname == "fromInteger":
            return EAp(EGlobal("prim_to_float"), x)
        prim = {"+": "prim_add_float", "-": "prim_sub_float",
                "*": "prim_mul_float"}.get(mname)
        if prim is not None:
            return EAp(EAp(EGlobal(prim), x), y)
        return x

    if mname == "fromInteger":
        return wrap(x)
    if mname == "+":
        return wrap(EAp(EAp(EGlobal("prim_add_int"), x), y))
    if mname == "-":
        return wrap(EAp(EAp(EGlobal("prim_sub_int"), x), y))
    if mname == "*":
        return wrap(EAp(EAp(EGlobal("prim_mul_int"), x), y))

    return x


def _bool_tags(program=None, cons=None) -> tuple[int, int]:
    """Return ``(true_tag, false_tag)`` for *this* program's `Bool`.

    Read from `cons` every time and never remembered.  A tag is a position
    in one program's constructor table — `declarations.fresh_tag` counts
    from zero as it walks the declarations — so `True` is a different
    number in a program that declares one datatype before `prelude.ges`
    than in a program that declares none.  A module-global memo of it was
    the first program compiled in the process deciding what `abs` compared
    against in every program after it: the `case` picked the wrong arm, and
    `softClip` — whose only nonlinearity is an `abs` — stopped saturating,
    so `polysaw.ges`'s ladder ran its own feedback away to an infinity.
    That is `elaborate` reading state no analysis put there, and it is what
    `pipeline`'s cache is allowed to assume nothing does.
    """
    if cons is not None and "True" in cons and "False" in cons:
        return (cons["True"].tag, cons["False"].tag)
    return (0, 1)


def _div_body(head: Type, mname: str) -> Expr:
    """`/` and `%` at `Int` and at `Float` — four primitives, no cleverness.

    Both are floored at both types, which is Python's convention and is
    the one the oracle uses; `audiollvm.floor_div` and `floor_rem_float`
    are what make the generated code agree with it on negative operands.
    """
    x, y = EVar("x"), EVar("y")
    floating = isinstance(head, TCon) and head.name == "Float"
    prim = {("/", False): "prim_div_int", ("%", False): "prim_mod_int",
            ("/", True): "prim_div_float", ("%", True): "prim_mod_float"}
    name = prim.get((mname, floating))
    if name is None:
        return x
    return EAp(EAp(EGlobal(name), x), y)


def _signed_body(head: Type, mname: str, cons: dict) -> Expr:
    """`negate` and `abs`, written as arithmetic rather than as primitives.

    There is no `prim_neg_*` or `prim_abs_*` and there does not need to be:
    `negate x` is `0 - x` and `abs x` is a comparison, which is exactly
    what `prelude.ges`'s `negate` and `abs` already were.
    Building them out of `sub` and `lt` keeps the primitive set the size
    it was before this class existed — two new *names* at two types, and
    no new machine instruction.

    `ENum` carries the literal's type in the literal, so `0` and `0.0`
    are what pick the integer and the floating primitives apart here.
    """
    x = EVar("x")
    floating = isinstance(head, TCon) and head.name == "Float"
    zero = ENum(0.0 if floating else 0)
    sub = "prim_sub_float" if floating else "prim_sub_int"
    lt = "prim_lt_float" if floating else "prim_lt_int"
    negated = EAp(EAp(EGlobal(sub), zero), x)
    if mname == "negate":
        return negated
    if mname == "abs":
        true_tag, false_tag = _bool_tags(cons=cons)
        return ECase(EAp(EAp(EGlobal(lt), x), zero), [
            _alt(true_tag, [], negated),
            _alt(false_tag, [], x),
        ])
    return x


def _eq_body(mname: str, cons: dict) -> Expr:
    """Generate body for ``Eq Int`` methods."""
    x, y = EVar("x"), EVar("y")
    eq_call = EAp(EAp(EGlobal("prim_eq_int"), x), y)
    if mname == "==":
        return eq_call
    if mname == "/=":
        return _mk_not(cons, eq_call)
    raise ValueError(f"Unknown Eq method: {mname}")


def _ord_body(mname: str, cons: dict) -> Expr:
    """Generate body for ``Ord Int`` methods."""
    x, y = EVar("x"), EVar("y")
    lt_xy = EAp(EAp(EGlobal("prim_lt_int"), x), y)
    lt_yx = EAp(EAp(EGlobal("prim_lt_int"), y), x)

    if mname == "<":
        return lt_xy
    if mname == ">":
        return lt_yx
    if mname == "<=":
        return _mk_not(cons, lt_yx)  # x <= y  <=>  not (y < x)
    if mname == ">=":
        return _mk_not(cons, lt_xy)  # x >= y  <=>  not (x < y)
    raise ValueError(f"Unknown Ord method: {mname}")


def _mk_not(cons: dict, arg: Expr) -> Expr:
    """``not arg`` = case arg of True -> False; False -> True."""
    true_tag = cons["True"].tag
    false_tag = cons["False"].tag
    return ECase(arg, [
        _alt(true_tag, [], ECon(false_tag, [])),
        _alt(false_tag, [], ECon(true_tag, [])),
    ])


def _alt(tag: int, names: list[str], body: Expr):
    from .expr import Alter
    return Alter(tag, names, body)


# ---------------------------------------------------------------------------
# Static method resolution
# ---------------------------------------------------------------------------

def resolve_static_methods(
    scs: list[tuple[str, int, ELambda, object]],
) -> tuple[list[tuple[str, int, ELambda, object]], set[str]]:
    """Replace `πᵢ __dict_C_T__` with the method global it must select.

    A dictionary with no context is a compile-time constant: its body is a
    tuple of method globals, so projecting a fixed slot out of it has one
    answer and the run time need not compute it.

    This is not (only) an optimization.  ϕ/δ has no rule for a projection
    out of a *discrete* value: a dictionary's change is `()` (`errata.md`
    D8), `π₀ ()` is not a projection of anything, and δ fell through to
    returning the `EProj` node unchanged — which then got applied to two
    arguments, the shape `fixme.md` F57 is about.  The result compiled to
    a number and died as `CaseJump on non-constructor`.  Resolving the
    projection here means δ sees an ordinary global and can ask for its
    derivative by name.

    Returns the rewritten SCs and the set of method globals now referred
    to directly, which is what the ϕ/δ gate must stop skipping.

    Dictionaries *with* a context take parameters, so their slots close
    over those parameters and are not constants; those are left alone and
    remain unable to cross a `fix`.
    """
    table: dict[str, list[Expr]] = {}
    for name, arity, lam, _sig in scs:
        if arity == 0 and not lam.params and isinstance(lam.body, ETuple):
            table[str(name)] = list(lam.body.args)

    resolved: set[str] = set()

    def rewrite(e: Expr) -> Expr:
        if (isinstance(e, EAp) and isinstance(e.fn, EProj)
                and isinstance(e.arg, EGlobal)):
            slots = table.get(str(e.arg.name))
            if slots is not None and e.fn.i < len(slots):
                slot = slots[e.fn.i]
                if isinstance(slot, EGlobal):
                    resolved.add(str(slot.name))
                    return slot
        return map_children(e, rewrite)

    def selects_a_method(e: Expr) -> bool:
        """Is there anything here to rewrite?

        A read-only scan, because `rewrite` rebuilds every node it visits
        and most supercombinators have no dictionary projection at all.
        Rebuilding the whole prelude on every compile cost more than the
        rest of this pass put together.
        """
        stack = [e]
        while stack:
            n = stack.pop()
            if (isinstance(n, EAp) and isinstance(n.fn, EProj)
                    and isinstance(n.arg, EGlobal)
                    and str(n.arg.name) in table):
                return True
            stack.extend(subexprs(n))
        return False

    from dataclasses import replace as _replace

    out = []
    for name, arity, lam, sig in scs:
        if selects_a_method(lam.body):
            # `replace` rather than a fresh `ELambda`: the binder flavours
            # inference left on it are fields this pass does not name.
            lam = _replace(lam, body=rewrite(lam.body))
        out.append((name, arity, lam, sig))
    return out, resolved
