"""Declaration classification — VModule → Program.

Groups supercombinator equations by name, matches type signatures,
processes ADT/class/instance declarations, and provides type-expression
desugaring.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .syntax.ast import (
    Pat,
    PCon,
    PTuple,
    Val,
    VAnnot,
    VApp,
    VBox,
    VClass,
    VConId,
    VFixity,
    VFunc,
    VInfix,
    VList,
    VInstance,
    VInternal,
    VKind,
    VNum,
    VModule,
    PVar,
    VSCDecl,
    VSCEqn,
    VSet,
    VTuple,
    VSig,
    VImplicit,
    VTypeAlias,
    VTypeDecl,
    VWord,
)
from .types import TApp, TCon, TFun, TInt, TVar, Type, Predicate, mk_tuple
from .coherence import check_instances
from .deriving import DeriveError, derive, instance_head


class DeclError(Exception):
    pass


#: Data types the compiler synthesizes with fixed constructor tags because
#: the reactive driver matches on them (see ``classify``).  A user
#: declaration of the same name would be silently clobbered, so reject it.
_RESERVED_ADT_NAMES = frozenset({"Maybe", "Sync"})


# ---------------------------------------------------------------------------
# ADT / constructor information
# ---------------------------------------------------------------------------

@dataclass
class ConInfo:
    name: str
    tag: int
    arity: int
    type_: Type


# ---------------------------------------------------------------------------
# Class / instance information
# ---------------------------------------------------------------------------

@dataclass
class ClassInfo:
    name: str
    params: list[str]             # type parameter names
    methods: dict[str, Type]      # method name → type (using param TVars)
    assoc_types: list[str] = field(default_factory=list)  # associated type names
    param_tvs: list[TVar] = field(default_factory=list)   # the TVars in `methods`
    #: Superclass names — `class Eq a => Ord a` gives `Ord` the superclass
    #: `Eq`.  Single-parameter classes only, so a superclass is always a
    #: predicate on this class's own parameter and the name alone says it.
    superclasses: list[str] = field(default_factory=list)


@dataclass
class InstanceInfo:
    class_name: str
    head_type: Type               # the head type (e.g. TCon("Int"), List a)
    methods: dict[str, VSCEqn]    # method name → equation body
    assoc_types: dict[str, Type] = field(default_factory=dict)  # name → concrete type
    context: list[Predicate] = field(default_factory=list)  # `(Eq a) => Eq [a]`
    builtin: bool = False         # synthesized by the compiler, not declared
    span: object = None

    @property
    def predicate(self) -> Predicate:
        return Predicate(self.class_name, self.head_type)

    def __str__(self) -> str:
        from .show import name_vars, show_predicate
        names = name_vars([self.head_type] + [p.type_ for p in self.context])
        ctx = ""
        if self.context:
            preds = ", ".join(show_predicate(p, names) for p in self.context)
            ctx = f"({preds}) => "
        return ctx + show_predicate(self.predicate, names)


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

@dataclass
class AliasInfo:
    """A resolved type alias: ``type Name p1 … pn = body``.

    ``body`` is already desugared *and* alias-free — nested aliases are
    expanded while the table is built, so a single expansion at a use site
    is enough.  ``param_tvs`` are the (negative-id) TVars standing for the
    alias parameters inside ``body``.
    """
    name: str
    params: list[str]
    param_tvs: list[TVar]
    body: Type
    span: object = None


# ---------------------------------------------------------------------------
# SC info
# ---------------------------------------------------------------------------

@dataclass
class SCInfo:
    name: str
    equations: list[VSCEqn]
    sig_type: Type | None = None
    using_params: list[str] | None = None  # implicit param names from (using ...)
    sig_constraints: list[Predicate] = field(default_factory=list)  # `(Show a) =>`


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------

@dataclass
class Program:
    scs: list[SCInfo]
    fixities: list[VFixity]
    cons: dict[str, ConInfo] = field(default_factory=dict)
    kind_decls: list[VKind] = field(default_factory=list)
    classes: dict[str, ClassInfo] = field(default_factory=dict)
    instances: list[InstanceInfo] = field(default_factory=list)
    aliases: dict[str, AliasInfo] = field(default_factory=dict)
    #: `implicit n : τ` — every implicit parameter's declared type.  Keyed
    #: by name because that is how an implicit is resolved; see `VImplicit`.
    implicits: dict[str, Type] = field(default_factory=dict)

    @property
    def sc_names(self) -> set[str]:
        return {sc.name for sc in self.scs}


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(module: VModule) -> Program:

    # 4, not 0: tags 0–3 are `Nil`/`Cons`/`False`/`True`, pinned in
    # `gmachine` so that every numbering agrees on them — see the synthetic
    # ADT block below.
    _next_tag = 4
    _next_param = -1

    fixities: list[VFixity] = []
    kind_decls: list[VKind] = []
    sigs: dict[str, Type] = {}
    sig_contexts: dict[str, list[Predicate]] = {}
    implicits: dict[str, Type] = {}
    scs_by_name: dict[str, list[VSCEqn]] = {}
    sc_order: list[str] = []
    cons: dict[str, ConInfo] = {}
    classes: dict[str, ClassInfo] = {}
    instances: list[InstanceInfo] = []
    #: Instances synthesized by `deriving`, processed after the module's
    #: own items so that every constructor they mention is already known.
    derived: list[VInstance] = []

    def adt_param_tv(name: str) -> TVar:
        nonlocal _next_param
        vid = _next_param
        _next_param -= 1
        return TVar(vid)

    def fresh_tag() -> int:
        nonlocal _next_tag
        t = _next_tag
        _next_tag += 1
        return t

    def build_adt_return(name: str, param_tvs: list[TVar]) -> Type:
        if not param_tvs:
            return TCon(name)
        acc: Type = TCon(name)
        for tv in param_tvs:
            acc = TApp(acc, tv)
        return acc

    # Type aliases are collected up front (so they may be used before their
    # declaration), checked for cycles, and expanded eagerly from here on.
    aliases = _resolve_aliases(_collect_aliases(module), adt_param_tv)
    # `String = List Char`, as in Haskell.  An alias rather than a
    # primitive: every list function, `Eq (List a)` and `Show (List a)`
    # then apply to strings without a second implementation, and the
    # eqtype/fixtype grammars inherit the answer from `Char`.  It is
    # installed after user aliases so a clash is still reported (a user
    # cannot declare it — `String` is in `BUILTIN_TYPE_NAMES`).
    aliases["String"] = AliasInfo(
        name="String", params=[], param_tvs=[],
        body=TApp(TCon("List"), TCon("Char")),
    )

    for item in _with_derived(module.items, derived):
        if isinstance(item, VFixity):
            fixities.append(item)

        elif isinstance(item, VSig):
            if item.name in sigs:
                raise DeclError(
                    f"Duplicate type signature for '{item.name}'"
                )
            sig_contexts[item.name], sigs[item.name] = desugar_signature(
                item.type_, aliases, adt_param_tv)

        elif isinstance(item, VImplicit):
            if item.name in implicits:
                raise DeclError(
                    f"Duplicate `implicit` declaration for '{item.name}'"
                )
            context, ty = desugar_signature(item.type_, aliases, adt_param_tv)
            if context:
                # An implicit is supplied by a `given`, which passes a
                # value, not a dictionary; there is nowhere for a predicate
                # on it to be discharged.
                raise DeclError(
                    f"`implicit {item.name}` may not carry a class context"
                )
            implicits[item.name] = ty

        elif isinstance(item, VSCDecl):
            # The parser groups *adjacent* equations into one `VSCDecl`, so
            # a second declaration of a name means the definition is split
            # by something else — two separate definitions, as far as the
            # reader is concerned.  Shadowing between the prelude and user
            # code is resolved before this point (`gestate/prelude.py`), so
            # anything that reaches here is a genuine duplicate.
            if item.name in scs_by_name:
                raise DeclError(
                    f"Multiple declarations of '{item.name}' — its equations "
                    f"must be adjacent"
                )
            scs_by_name[item.name] = []
            sc_order.append(item.name)
            for eq in item.equations:
                scs_by_name[item.name].append(eq)

        elif isinstance(item, VKind):
            kind_decls.append(item)

        # `internal` declares nothing.  It marks a line, and what that line
        # means is a question about *files* — which this function cannot
        # see, because the backends hand it one text with the preludes
        # concatenated on the front.  `gestate/internals.py` reads the
        # markers back out of the sources that were concatenated, where the
        # boundaries still exist.
        elif isinstance(item, VInternal):
            pass

        elif isinstance(item, VTypeDecl):
            if item.name in _RESERVED_ADT_NAMES:
                raise DeclError(
                    f"'{item.name}' is a built-in data type of the FRP "
                    f"interface and cannot be redeclared"
                )
            param_tvs = [adt_param_tv(p) for p in item.params]
            param_map = dict(zip(item.params, param_tvs))
            return_ty = build_adt_return(item.name, param_tvs)

            for ctor in item.constructors:
                tag = fresh_tag()
                field_types = [desugar_type(f, param_map, aliases)
                               for f in ctor.fields]
                ctor_type: Type = return_ty
                for ft in reversed(field_types):
                    ctor_type = TFun(ft, ctor_type)
                cons[ctor.name] = ConInfo(
                    name=ctor.name, tag=tag,
                    arity=len(ctor.fields), type_=ctor_type,
                )

            # `deriving (Show, Eq)` becomes ordinary instance declarations,
            # appended to the module's own so they classify identically.
            for cls in item.deriving:
                try:
                    ctx, methods = derive(cls, item.name, item.params,
                                          item.constructors)
                except DeriveError as e:
                    raise DeclError(str(e)) from None
                derived.append(VInstance(
                    name=cls, params=instance_head(item.name, item.params),
                    members=list(methods.values()), context=ctx,
                    span=item.span,
                ))

        elif isinstance(item, VClass):
            param_tvs = [adt_param_tv(p) for p in item.params]
            param_map = dict(zip(item.params, param_tvs))
            methods: dict[str, Type] = {}
            assoc_types: list[str] = [m.name for m in item.members
                                      if isinstance(m, VKind)]
            for m in item.members:
                if isinstance(m, VSig):
                    # **A method's own type variables are quantified at the
                    # method, not at the class.**  `class Functor f where
                    # map : (a -> b) -> f a -> f b` has one class parameter
                    # and two variables belonging to `map` itself, and only
                    # `f` was being mapped here — so `a` and `b` fell
                    # through to `desugar_type`'s rigid signature variables,
                    # which are interned by *name* and therefore shared with
                    # every other `a` and `b` in the program.
                    #
                    # The symptom was spectacular and pointed nowhere near
                    # the cause: declaring any such class produced nine
                    # errors about `++`, `concat`, `reverse`, `sum` and the
                    # `Show` helpers being "rigid", because one leaked
                    # variable had unified with something in each of them.
                    # Giving them `adt_param_tv`s puts them in the set
                    # `infer._lookup_method` freshens per use site, which is
                    # what "quantified at the method" means operationally.
                    own = dict(param_map)
                    for v in _type_tyvars(m.type_):
                        if v not in own and v not in assoc_types:
                            own[v] = adt_param_tv(v)
                    methods[m.name] = desugar_type(m.type_, own, aliases)
            supers: list[str] = []
            for c in item.context:
                pred = _desugar_predicate(c, param_map, aliases)
                if not (isinstance(pred.type_, TVar)
                        and pred.type_ in param_tvs):
                    raise DeclError(
                        f"Superclass '{pred.class_name}' of class "
                        f"'{item.name}' must constrain the class's own type "
                        f"parameter"
                    )
                if pred.class_name not in supers:
                    supers.append(pred.class_name)
            classes[item.name] = ClassInfo(
                name=item.name, params=item.params,
                methods=methods, assoc_types=assoc_types,
                param_tvs=param_tvs, superclasses=supers,
            )

        elif isinstance(item, VInstance):
            # Type variables of the instance are shared by the head and the
            # context: in `(Eq a) => Eq [a]` both mention the same `a`.
            inst_map = {v: adt_param_tv(v) for v in _instance_tyvars(item)}
            head_params = [desugar_type(p, inst_map, aliases) for p in item.params]
            if len(head_params) != 1:
                raise DeclError(
                    f"Multi-parameter instance not supported yet: {item.name}"
                )
            methods: dict[str, VSCEqn] = {}
            assoc_types: dict[str, Type] = {}
            for m in item.members:
                if isinstance(m, VSCEqn):
                    methods[m.name] = m
                elif isinstance(m, VKind):
                    assoc_types[m.name] = desugar_type(m.kind, inst_map, aliases)
            instances.append(InstanceInfo(
                class_name=item.name,
                head_type=head_params[0],
                methods=methods,
                assoc_types=assoc_types,
                context=[_desugar_predicate(c, inst_map, aliases)
                         for c in item.context],
                span=item.span,
            ))

    # Synthetic ADT: List a = Nil | Cons a (List a)
    #
    # Pinned tags, like `Maybe`'s and `Sync`'s below and for the reason
    # `gmachine` gives beside them: a tag handed out after the module's
    # declarations lands at a different number depending on how many
    # types the program declares, and the staged front end compiles the
    # library stack and the program under two such numberings.
    from .gmachine import TAG_CONS, TAG_FALSE, TAG_NIL, TAG_TRUE

    p = adt_param_tv("a")
    list_ret = TApp(TCon("List"), p)
    cons["Nil"] = ConInfo(name="Nil", tag=TAG_NIL, arity=0, type_=list_ret)
    cons["Cons"] = ConInfo(name="Cons", tag=TAG_CONS, arity=2,
                           type_=TFun(p, TFun(list_ret, list_ret)))

    # Synthetic ADT: Bool = False | True
    bool_ty = TCon("Bool")
    cons["False"] = ConInfo(name="False", tag=TAG_FALSE, arity=0,
                            type_=bool_ty)
    cons["True"] = ConInfo(name="True", tag=TAG_TRUE, arity=0, type_=bool_ty)

    # Synthetic ADT: Maybe a = Nothing | Just a
    #
    # Rizzo writes `Maybe A = A + 1` with `just = in1`; gestate names the
    # injections instead of numbering them, so `watch` fires on `Just` and
    # the in1/in2 question `spec/errata.md` R4 raises does not arise.  The
    # tags are the reserved ones from `gmachine`, because `reactive.ticked`
    # has to recognise a `Just` with no constructor table to hand.
    from .gmachine import (
        TAG_NOTHING, TAG_JUST, TAG_SYNC_L, TAG_SYNC_R, TAG_SYNC_BOTH,
    )

    mp = adt_param_tv("a")
    maybe_ret = TApp(TCon("Maybe"), mp)
    cons["Nothing"] = ConInfo(name="Nothing", tag=TAG_NOTHING, arity=0,
                              type_=maybe_ret)
    cons["Just"] = ConInfo(name="Just", tag=TAG_JUST, arity=1,
                           type_=TFun(mp, maybe_ret))

    # Synthetic ADT: Sync a b = SyncLeft a | SyncRight b | SyncBoth a b
    #
    # The paper's `Sync A B = (A + B) + (A × B)` with `left`/`right`/`both`.
    # Naming the three cases directly saves user `cont` functions a nested
    # `case` and gives `advance` real constructor tags to build.
    sa, sb = adt_param_tv("a"), adt_param_tv("b")
    sync_ret = TApp(TApp(TCon("Sync"), sa), sb)
    cons["SyncLeft"] = ConInfo(name="SyncLeft", tag=TAG_SYNC_L, arity=1,
                               type_=TFun(sa, sync_ret))
    cons["SyncRight"] = ConInfo(name="SyncRight", tag=TAG_SYNC_R, arity=1,
                                type_=TFun(sb, sync_ret))
    cons["SyncBoth"] = ConInfo(name="SyncBoth", tag=TAG_SYNC_BOTH, arity=2,
                               type_=TFun(sa, TFun(sb, sync_ret)))

    # Synthetic class: Num a where fromInteger : Int -> a
    pa = adt_param_tv("a")
    classes["Num"] = ClassInfo(
        name="Num", params=["a"],
        methods={
            "fromInteger": TFun(TCon("Int"), pa),
            "+": TFun(pa, TFun(pa, pa)),
            "-": TFun(pa, TFun(pa, pa)),
            "*": TFun(pa, TFun(pa, pa)),
        },
        assoc_types=[], param_tvs=[pa],
    )

    # Synthetic class: Floating a where fromFloat : Float -> a
    #
    # **What makes `0.5` mean something other than a `Float`.**  `2` has
    # been `Num a => a` since there was a `Num`, so `x * 2` needs no
    # coercion at any type with an instance; a literal with a point in it
    # was `Float` and nothing else, so the same expression one decimal
    # place later stopped typechecking.  That asymmetry is invisible until
    # a type other than `Float` wants literals — `Sig Float` does, and
    # `tone * 0.5` reading as a type error while `tone * 2` worked is what
    # asked for this class (`spec/frp_lesson.md`).
    #
    # `Floating` rather than `Num`, and one method rather than four: what a
    # float literal needs is a way *in*, and arithmetic is already `Num`'s.
    # An instance at a type that has both is written for both.
    fa = adt_param_tv("a")
    classes["Floating"] = ClassInfo(
        name="Floating", params=["a"],
        methods={"fromFloat": TFun(TCon("Float"), fa)},
        assoc_types=[], param_tvs=[fa],
    )

    # Synthetic class: Div a where (/) : a -> a -> a; (%) : a -> a -> a
    #
    # **Division is not `Num`'s**, and the two types are why.  `Num` has
    # `+`, `-` and `*`, which every numeric type this language has can
    # answer for; division cannot be one of them because `Cyclic n` and
    # `Bounded n m` have no answer, and a `Num` method an instance leaves
    # out is a silent placeholder rather than an error.
    #
    # `/` was a plain `Float -> Float -> Float` in `prelude.ges` and `%`
    # was not there at all: an integer program said `prim_div_int` and
    # `prim_mod_int`, which are compiler-internal names, and said them
    # sixteen times across `examples/`.  One class answers both.
    da = adt_param_tv("a")
    classes["Div"] = ClassInfo(
        name="Div", params=["a"],
        methods={
            "/": TFun(da, TFun(da, da)),
            "%": TFun(da, TFun(da, da)),
        },
        assoc_types=[], param_tvs=[da],
    )

    # Synthetic class: Signed a where negate : a -> a; abs : a -> a
    #
    # **Separate from `Num` because `abs` is meaningless on a modular
    # type.**  `Cyclic 12` has a `Num` instance and no notion of a
    # magnitude or a sign — 11 is not "larger" than 1 in any sense the
    # type supports — so putting these on `Num` would oblige every finite
    # type to answer a question it cannot.  A type that has a sign says so
    # by having this instance, and `negate`/`abs` stop carrying
    # their type in their names.
    sa2 = adt_param_tv("a")
    classes["Signed"] = ClassInfo(
        name="Signed", params=["a"],
        methods={
            "negate": TFun(sa2, sa2),
            "abs": TFun(sa2, sa2),
        },
        assoc_types=[], param_tvs=[sa2],
    )

    # Synthetic class: Eq a where (==) : a -> a -> Bool
    ea = adt_param_tv("a")
    classes["Eq"] = ClassInfo(
        name="Eq", params=["a"],
        methods={
            "==": TFun(ea, TFun(ea, TCon("Bool"))),
            "/=": TFun(ea, TFun(ea, TCon("Bool"))),
        },
        assoc_types=[], param_tvs=[ea],
    )

    # Synthetic class: Ord a where (<) : a -> a -> Bool; (<=) : a -> a -> Bool;
    #                             (>) : a -> a -> Bool; (>=) : a -> a -> Bool
    oa = adt_param_tv("a")
    classes["Ord"] = ClassInfo(
        name="Ord", params=["a"],
        methods={
            "<": TFun(oa, TFun(oa, TCon("Bool"))),
            "<=": TFun(oa, TFun(oa, TCon("Bool"))),
            ">": TFun(oa, TFun(oa, TCon("Bool"))),
            ">=": TFun(oa, TFun(oa, TCon("Bool"))),
        },
        assoc_types=[], param_tvs=[oa],
        # `Ord` implies `Eq`, as in Haskell: `<=` and `==` have to agree,
        # and a generic ordering routine invariably wants both.
        superclasses=["Eq"],
    )

    # Synthetic instances: Num Int, Eq Int, Ord Int
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Num", head_type=TCon("Int"),
        methods={
            "fromInteger": _method_eqn("fromInteger", ["x"]),
            "+": _method_eqn("+", ["x", "y"]),
            "-": _method_eqn("-", ["x", "y"]),
            "*": _method_eqn("*", ["x", "y"]),
        },
    ))
    # `Floating Float` — the identity, and the one every float literal in a
    # program that declares no instance of its own resolves to.
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Floating", head_type=TCon("Float"),
        methods={"fromFloat": _method_eqn("fromFloat", ["x"])},
    ))
    # `Div` and `Signed` at both numeric types.  Four instances rather
    # than two classes' worth of special cases, because both are ordinary
    # generated bodies over primitives that already exist — `prim_mod_float`
    # being the one that did not, and was added for this.
    for _head in (TCon("Int"), TCon("Float")):
        instances.append(InstanceInfo(
            builtin=True,
            class_name="Div", head_type=_head,
            methods={
                "/": _method_eqn("/", ["x", "y"]),
                "%": _method_eqn("%", ["x", "y"]),
            },
        ))
        instances.append(InstanceInfo(
            builtin=True,
            class_name="Signed", head_type=_head,
            methods={
                "negate": _method_eqn("negate", ["x"]),
                "abs": _method_eqn("abs", ["x"]),
            },
        ))
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Eq", head_type=TCon("Int"),
        methods={
            "==": _method_eqn("==", ["x", "y"]),
            "/=": _method_eqn("/=", ["x", "y"]),
        },
    ))
    # `Char` is integer-represented, so it reaches the same primitives.
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Eq", head_type=TCon("Char"),
        methods={
            "==": _method_eqn("==", ["x", "y"]),
            "/=": _method_eqn("/=", ["x", "y"]),
        },
    ))
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Ord", head_type=TCon("Char"),
        methods={
            "<": _method_eqn("<", ["x", "y"]),
            "<=": _method_eqn("<=", ["x", "y"]),
            ">": _method_eqn(">", ["x", "y"]),
            ">=": _method_eqn(">=", ["x", "y"]),
        },
    ))
    # `Float` is an eqtype — equality on it is decidable, which is what the
    # set machinery asks — but not a *finite* one, so `fix` over `{Float}`
    # is refused exactly as over `{Int}`.
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Eq", head_type=TCon("Float"),
        methods={
            "==": _method_eqn("==", ["x", "y"]),
            "/=": _method_eqn("/=", ["x", "y"]),
        },
    ))
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Ord", head_type=TCon("Float"),
        methods={
            "<": _method_eqn("<", ["x", "y"]),
            "<=": _method_eqn("<=", ["x", "y"]),
            ">": _method_eqn(">", ["x", "y"]),
            ">=": _method_eqn(">=", ["x", "y"]),
        },
    ))
    instances.append(InstanceInfo(
        builtin=True,
        class_name="Ord", head_type=TCon("Int"),
        methods={
            "<": _method_eqn("<", ["x", "y"]),
            "<=": _method_eqn("<=", ["x", "y"]),
            ">": _method_eqn(">", ["x", "y"]),
            ">=": _method_eqn(">=", ["x", "y"]),
        },
    ))

    # Superclasses are discharged by *closing* every context under them,
    # rather than by storing a superclass dictionary inside the subclass's.
    # `f : (Ord a) => …` therefore takes an `Eq a` dictionary too, and its
    # body may call `Eq`'s methods; the caller resolves the extra predicate
    # exactly as it resolves the original one.  Closing here, once, is what
    # keeps the parameter order that elaboration and every call site agree
    # on from having to be recomputed downstream.
    instances = [replace(i, context=close_context(i.context, classes))
                 for i in instances]

    check_instances(instances, classes)

    return Program(
        scs=[SCInfo(name=n, equations=scs_by_name[n],
                    sig_type=sigs.get(n),
                    using_params=_extract_using(scs_by_name[n]),
                    sig_constraints=close_context(
                        sig_contexts.get(n, []), classes))
             for n in sc_order],
        fixities=fixities, cons=cons, kind_decls=kind_decls,
        classes=classes, instances=instances, aliases=aliases,
        implicits=implicits,
    )


def _with_derived(items: list[Val], derived: list) -> "object":
    """Yield the module's items, then whatever `deriving` produced.

    A generator rather than a concatenation: the derived instances are
    built *while* the data declarations are visited, so the list does not
    exist yet when iteration starts.
    """
    for item in items:
        yield item
    i = 0
    while i < len(derived):
        yield derived[i]
        i += 1


def close_context(context: list[Predicate],
                  classes: dict[str, ClassInfo]) -> list[Predicate]:
    """Add every superclass predicate implied by ``context``.

    ``(Ord a)`` becomes ``(Ord a, Eq a)``.  Order is stable — declared
    predicates first, then superclasses breadth-first — because
    elaboration turns the list into a dictionary parameter list and every
    call site applies the arguments positionally.
    """
    out = list(context)
    seen = {(p.class_name, str(p.type_)) for p in out}
    queue = list(context)
    while queue:
        pred = queue.pop(0)
        ci = classes.get(pred.class_name)
        if ci is None:
            continue
        for sup in ci.superclasses:
            key = (sup, str(pred.type_))
            if key in seen:
                continue
            seen.add(key)
            sup_pred = Predicate(sup, pred.type_)
            out.append(sup_pred)
            queue.append(sup_pred)
    return out


# ---------------------------------------------------------------------------
# Type-expression desugaring
# ---------------------------------------------------------------------------

def desugar_type(val: Val, param_map: dict[str, TVar] | None = None,
                 aliases: dict[str, AliasInfo] | None = None) -> Type:
    if param_map is None:
        param_map = {}
    if aliases is None:
        aliases = {}
    if isinstance(val, (VConId, VWord)):
        if val.value in param_map:
            return param_map[val.value]
        if val.value in aliases:
            return _expand_alias(aliases[val.value], [], val.span)
        return TCon(val.value, span=val.span)
    if isinstance(val, VNum):
        if isinstance(val.value, int):
            return TInt(val.value, span=val.span)
        return TCon(str(val.value), span=val.span)
    if isinstance(val, VApp):
        head, args = _type_spine(val)
        if (isinstance(head, (VConId, VWord))
                and head.value not in param_map
                and head.value in aliases):
            arg_types = [desugar_type(a, param_map, aliases) for a in args]
            return _expand_alias(aliases[head.value], arg_types, val.span)
        return TApp(desugar_type(val.fn, param_map, aliases),
                    desugar_type(val.arg, param_map, aliases), span=val.span)
    if isinstance(val, VInfix):
        if val.op in ("->", "~>"):
            # `~>` is Datafun's function space: the argument is a monotone
            # variable.  `->` is `□A → B`, whose argument is discrete.
            return TFun(desugar_type(val.left, param_map, aliases),
                        desugar_type(val.right, param_map, aliases),
                        span=val.span, mono=(val.op == "~>"))
        if val.op == "..":
            return TApp(TApp(TCon("Bounded"),
                             desugar_type(val.left, param_map, aliases)),
                        desugar_type(val.right, param_map, aliases), span=val.span)
        raise DeclError(f"Unexpected infix operator in type: {val.op}")
    if isinstance(val, VFunc):
        raise DeclError(
            "A class context (`(C a) => ...`) is only supported on a "
            "top-level signature, not here"
        )
    if isinstance(val, VAnnot):
        return desugar_type(val.expr, param_map, aliases)
    if isinstance(val, VSet):
        if len(val.items) == 1:
            return TApp(TCon("Set"),
                        desugar_type(val.items[0], param_map, aliases),
                        span=val.span)
        raise DeclError("Set type with multiple items: use {A} for the type of sets of A")
    if isinstance(val, VBox):
        return TApp(TCon("Box"), desugar_type(val.body, param_map, aliases),
                    span=val.span)
    if isinstance(val, VList):
        # `[a]` — the list type `syntax.md` documents.  Type annotations are
        # parsed with the expression grammar, so this arrives as a one-item
        # list *literal* and there was no case for it: `f : [Int] -> Int`
        # failed as "unsupported type expression" while `List Int` worked
        # (`fixme.md` F62).
        if val.tail is not None or len(val.items) != 1:
            raise DeclError(
                "A list type is written `[a]` — one element type, no tail"
            )
        return TApp(TCon("List"),
                    desugar_type(val.items[0], param_map, aliases),
                    span=val.span)
    if isinstance(val, VTuple):
        if len(val.items) == 1:
            raise DeclError("A one-component tuple type is just its component")
        # `()` is fig. 2.1's `1`.  It is a type in its own right, and it is
        # the element type of `Prop = {()}` (`errata.md` D5).
        return mk_tuple([desugar_type(i, param_map, aliases)
                         for i in val.items])
    raise DeclError(f"Unsupported type expression: {type(val).__name__}")


# ---------------------------------------------------------------------------
# Instance heads and contexts
# ---------------------------------------------------------------------------

def _type_tyvars(val: Val) -> list[str]:
    """The type-variable names in one surface type expression, in order.

    Lowercase (`VWord`) is a variable and uppercase a constructor, which is
    the same rule `_instance_tyvars` applies to a whole instance head — so
    they share the walk rather than keeping two opinions about what a type
    variable looks like.
    """
    seen: list[str] = []
    _walk_tyvars(val, seen)
    return seen


def _walk_tyvars(val: Val, seen: list[str]) -> None:
    if isinstance(val, VWord):
        if val.value not in seen:
            seen.append(val.value)
    elif isinstance(val, VApp):
        _walk_tyvars(val.fn, seen)
        _walk_tyvars(val.arg, seen)
    elif isinstance(val, VInfix):
        _walk_tyvars(val.left, seen)
        _walk_tyvars(val.right, seen)
    elif isinstance(val, VAnnot):
        _walk_tyvars(val.expr, seen)
    elif isinstance(val, VSet):
        for i in val.items:
            _walk_tyvars(i, seen)
    elif isinstance(val, VBox):
        _walk_tyvars(val.body, seen)


def _instance_tyvars(item: VInstance) -> list[str]:
    """The type-variable names of an instance declaration, in order.

    Lowercase names (``VWord``) in the head and the context are the
    instance's variables; uppercase names are type constructors.
    """
    seen: list[str] = []

    def walk(val: Val) -> None:
        if isinstance(val, VWord):
            if val.value not in seen:
                seen.append(val.value)
        elif isinstance(val, VApp):
            walk(val.fn)
            walk(val.arg)
        elif isinstance(val, VInfix):
            walk(val.left)
            walk(val.right)
        elif isinstance(val, VAnnot):
            walk(val.expr)
        elif isinstance(val, VSet):
            for i in val.items:
                walk(i)
        elif isinstance(val, VBox):
            walk(val.body)

    for p in item.params:
        walk(p)
    for c in item.context:
        walk(c)
    return seen


def desugar_signature(
    val: Val, aliases: dict[str, AliasInfo] | None = None,
    fresh_tv=None,
) -> tuple[list[Predicate], Type]:
    """Split a signature into its context and its type.

    ``(Show a, Eq a) => a -> Int`` parses as a lambda — ``=>`` is the
    lambda arrow — so the context arrives as the ``VFunc``'s parameter
    *patterns*.  Lowercase names anywhere in the signature are its type
    variables, shared between the context and the type.
    """
    context_pats: list[Pat] = []
    body = val
    while isinstance(body, VFunc):
        for p in body.params:
            if isinstance(p, PTuple):
                context_pats.extend(p.items)
            else:
                context_pats.append(p)
        body = body.body

    # A lowercase name that is a type alias is not a type variable.
    written = {n: span for n, span in
               _signature_tyvars(context_pats, body).items()
               if not (aliases and n in aliases)}
    names = list(written)
    # A signature's variables are *rigid* (`fixme.md` F36): the body is
    # checked against the type the user wrote, and each of its variables
    # stands for a type the caller chooses, so the body may not bind one.
    # A use site instantiates them into fresh metavariables — the scheme
    # quantifies exactly these — so rigidity is confined to the body.
    if fresh_tv is None:
        tyvars = {n: TVar(-1000 - i, written[n], rigid=True, name=n)
                  for i, n in enumerate(names)}
    else:
        tyvars = {n: _rigid(fresh_tv(n), n, written[n]) for n in names}

    context = [_pat_predicate(p, tyvars, aliases) for p in context_pats]
    return context, desugar_type(body, tyvars, aliases)


def _rigid(v: TVar, name: str, span=None) -> TVar:
    """The same variable, marked rigid and carrying its written name.

    And the place it was written, when the caller knows it: a fresh
    variable from a supply has no span of its own, and the signature
    that named it does.
    """
    return TVar(v.id, span if span is not None else v.span,
                rigid=True, name=name)


def _signature_tyvars(pats: list[Pat], type_val: Val) -> dict:
    """Lowercase names in a signature, in order of first appearance.

    **Each with the span it was first written at**, which is what lets a
    complaint about one point at it.  A signature variable is otherwise
    the one thing in a type with no position at all: it is minted here
    rather than desugared from a node, so without this its error lands
    on whatever failed to unify with it, half a file away.
    """
    names: dict = {}

    def add(n: str, span=None) -> None:
        if n not in names:
            names[n] = span

    def walk_pat(p: Pat) -> None:
        if isinstance(p, PVar):
            add(p.name, getattr(p, "span", None))
        elif isinstance(p, PCon):
            for a in p.args:
                walk_pat(a)
        elif isinstance(p, PTuple):
            for a in p.items:
                walk_pat(a)

    def walk_type(v: Val) -> None:
        if isinstance(v, VWord):
            add(v.value, v.span)
        elif isinstance(v, VApp):
            walk_type(v.fn)
            walk_type(v.arg)
        elif isinstance(v, VInfix):
            walk_type(v.left)
            walk_type(v.right)
        elif isinstance(v, VAnnot):
            walk_type(v.expr)
        elif isinstance(v, (VSet, VTuple, VList)):
            # `VList` is here because `[a]` is a type — a list literal is
            # how the expression grammar sees it.  Without it the `a` in
            # `f : [a] -> Int` was not collected as a signature variable
            # and came out a nullary constructor, which the kind checker
            # then reported as unknown (`fixme.md` F62).
            for i in v.items:
                walk_type(i)
        elif isinstance(v, VBox):
            walk_type(v.body)

    for p in pats:
        walk_pat(p)
    walk_type(type_val)
    return names


def _pat_predicate(pat: Pat, tyvars: dict[str, TVar],
                   aliases: dict[str, AliasInfo] | None) -> Predicate:
    """Convert one constraint pattern, ``Show a``, into a ``Predicate``."""
    if not isinstance(pat, PCon):
        raise DeclError(f"Malformed constraint in signature: {pat}")
    if len(pat.args) != 1:
        raise DeclError(
            f"Constraint '{pat.name}' must have exactly one type argument "
            f"(multi-parameter classes are not supported yet)"
        )
    return Predicate(pat.name, _pat_type(pat.args[0], tyvars, aliases))


def _pat_type(pat: Pat, tyvars: dict[str, TVar],
              aliases: dict[str, AliasInfo] | None) -> Type:
    """Read a type out of a pattern — constraints parse as patterns."""
    if isinstance(pat, PVar):
        return tyvars.get(pat.name, TCon(pat.name, span=pat.span))
    if isinstance(pat, PCon):
        head: Type = TCon(pat.name, span=pat.span)
        if aliases and pat.name in aliases:
            args = [_pat_type(a, tyvars, aliases) for a in pat.args]
            return _expand_alias(aliases[pat.name], args, pat.span)
        for a in pat.args:
            head = TApp(head, _pat_type(a, tyvars, aliases), span=pat.span)
        return head
    raise DeclError(f"Unsupported type in constraint: {pat}")


def _desugar_predicate(val: Val, param_map: dict[str, TVar],
                       aliases: dict[str, AliasInfo] | None = None) -> Predicate:
    """Convert a surface constraint ``C t`` into a ``Predicate``."""
    head, args = _type_spine(val)
    if not isinstance(head, (VConId, VWord)) or head.value in param_map:
        raise DeclError(f"Malformed constraint: {val}")
    if len(args) != 1:
        raise DeclError(
            f"Constraint '{head.value}' must have exactly one type argument "
            f"(multi-parameter classes are not supported yet)"
        )
    return Predicate(head.value, desugar_type(args[0], param_map, aliases))


# ---------------------------------------------------------------------------
# Type-alias collection, cycle detection, and expansion
# ---------------------------------------------------------------------------

def _collect_aliases(module: VModule) -> dict[str, VTypeAlias]:
    """Gather every ``type`` declaration, rejecting ill-formed ones.

    Aliases are collected before anything else is classified, so an alias
    may be used before the line that declares it.
    """
    from .kindcheck import BUILTIN_TYPE_NAMES

    decls: dict[str, VTypeAlias] = {}
    adt_names = {item.name for item in module.items
                 if isinstance(item, VTypeDecl)}

    for item in module.items:
        if not isinstance(item, VTypeAlias):
            continue
        if item.name in decls:
            raise DeclError(f"Duplicate type alias: {item.name}")
        if item.name in adt_names:
            raise DeclError(
                f"Type alias '{item.name}' clashes with a data type of the same name"
            )
        if item.name in BUILTIN_TYPE_NAMES:
            raise DeclError(
                f"Type alias '{item.name}' clashes with a built-in type"
            )
        if len(set(item.params)) != len(item.params):
            raise DeclError(
                f"Type alias '{item.name}' has duplicate type parameters"
            )
        decls[item.name] = item
    return decls


def _resolve_aliases(decls: dict[str, VTypeAlias],
                     fresh_tv) -> dict[str, AliasInfo]:
    """Desugar alias bodies, expanding nested aliases and rejecting cycles.

    Bodies are resolved dependency-first, so by the time an alias body is
    desugared every alias it mentions is already alias-free.  A name that
    is still on the resolution stack means the alias is self-referential
    (directly or transitively) — ``type T = List T`` — which per
    ``spec/types.md`` §6 is an error.
    """
    resolved: dict[str, AliasInfo] = {}
    stack: list[str] = []

    def resolve(name: str) -> None:
        if name in resolved:
            return
        if name in stack:
            cycle = " → ".join(stack[stack.index(name):] + [name])
            raise DeclError(f"Recursive type alias: {cycle}")
        decl = decls[name]
        stack.append(name)
        for dep in _alias_deps(decl.body, set(decl.params), decls.keys()):
            resolve(dep)
        param_tvs = [fresh_tv(p) for p in decl.params]
        param_map = dict(zip(decl.params, param_tvs))
        resolved[name] = AliasInfo(
            name=name, params=list(decl.params), param_tvs=param_tvs,
            body=desugar_type(decl.body, param_map, resolved),
            span=decl.span,
        )
        stack.pop()

    for name in decls:
        resolve(name)
    return resolved


def _alias_deps(val: Val, bound: set[str], names) -> list[str]:
    """Alias names referenced by the type expression ``val``.

    ``bound`` holds the alias' own parameters, which shadow alias names.
    """
    if isinstance(val, (VConId, VWord)):
        if val.value in names and val.value not in bound:
            return [val.value]
        return []
    if isinstance(val, VApp):
        return _alias_deps(val.fn, bound, names) + _alias_deps(val.arg, bound, names)
    if isinstance(val, VInfix):
        return (_alias_deps(val.left, bound, names)
                + _alias_deps(val.right, bound, names))
    if isinstance(val, VAnnot):
        return _alias_deps(val.expr, bound, names)
    if isinstance(val, VSet):
        return [d for item in val.items for d in _alias_deps(item, bound, names)]
    if isinstance(val, VBox):
        return _alias_deps(val.body, bound, names)
    return []


def _type_spine(val: Val) -> tuple[Val, list[Val]]:
    """Split a type application into its head and argument list."""
    args: list[Val] = []
    while isinstance(val, VApp):
        args.append(val.arg)
        val = val.fn
    args.reverse()
    return val, args


def _expand_alias(info: AliasInfo, args: list[Type], span) -> Type:
    """Substitute ``args`` for the alias parameters in its body.

    Aliases must be saturated: a partially applied alias has no meaning as
    a type constructor because its body may not be one.  Extra arguments
    are applied to the expansion, which keeps ``type F = Maybe; F Int``
    working.
    """
    arity = len(info.params)
    if len(args) < arity:
        raise DeclError(
            f"Type alias '{info.name}' expects {arity} argument(s) "
            f"but got {len(args)}; type aliases must be fully applied"
        )
    subst = {tv.id: a for tv, a in zip(info.param_tvs, args)}
    expanded = _respan(_subst_params(info.body, subst), span)
    for extra in args[arity:]:
        expanded = TApp(expanded, extra, span=span)
    return expanded


def _subst_params(t: Type, subst: dict[int, Type]) -> Type:
    if isinstance(t, TVar):
        return subst.get(t.id, t)
    if isinstance(t, TFun):
        return TFun(_subst_params(t.arg, subst), _subst_params(t.ret, subst),
                    span=t.span)
    if isinstance(t, TApp):
        return TApp(_subst_params(t.fn, subst), _subst_params(t.arg, subst),
                    span=t.span)
    return t


def _respan(t: Type, span) -> Type:
    """Point the expansion at the use site, so type errors blame the alias
    occurrence rather than its declaration."""
    if span is None:
        return t
    return replace(t, span=span)


def _extract_using(eqns: list[VSCEqn]) -> list[str] | None:
    """Extract the ``using_params`` list from the first equation, if any."""
    if eqns and eqns[0].using_params:
        return eqns[0].using_params
    return None


def _dummy_vsceq(name: str, param: str, body_word: str) -> VSCEqn:
    """Create a placeholder VSCEqn for synthetic instances.
    The actual Expr is generated during elaboration, bypassing desugaring.
    """
    from .syntax.ast import Span, Pos
    return VSCEqn(name=name, params=[PVar(param, Span(Pos(), Pos()))],
                  body=VWord(body_word, Span(Pos(), Pos())),
                  using_params=[], span=Span(Pos(), Pos()))


def _method_eqn(name: str, param_names: list[str]) -> VSCEqn:
    """Create a VSCEqn with the given parameter names.  The body is a
    dummy ``VWord("_")`` — the real body is generated during elaboration.
    """
    from .syntax.ast import Span, Pos
    return VSCEqn(
        name=name,
        params=[PVar(p, Span(Pos(), Pos())) for p in param_names],
        body=VWord("_", Span(Pos(), Pos())),
        using_params=[],
        span=Span(Pos(), Pos()),
    )
