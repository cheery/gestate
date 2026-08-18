"""Desugar VModule AST → Expr grammar.

The bridge between the surface syntax AST and the G-machine's core
``Expr`` grammar (``gestate/expr.py``).  Strips types, resolves
operator phrases, desugars ADT constructors to ``ECon``, converts
``case`` and pattern-matching SC equations to ``ECase``, and wraps
supercombinator equations into ``ELambda`` forms ready for lambda
lifting.
"""

from __future__ import annotations

from .expr import (
    Alter,
    EField,
    EAnnot,
    EAp,
    EAppEx,
    EAppFa,
    EBox,
    ECase,
    EChan,
    EChr,
    ECon,
    EDelay,
    EField,
    EFix,
    EFor,
    EGFix,
    EGlobal,
    EHole,
    EJoin,
    ELambda,
    ELet,
    ENever,
    ENum,
    EProj,
    ESet,
    ESigCons,
    ESigHead,
    ESync,
    ETail,
    ETuple,
    EUnbox,
    EVar,
    EWait,
    EWatch,
    Expr,
    Name,
    subexprs,
    map_children as _map_children,
)
from .declarations import AliasInfo, ConInfo, Program, desugar_type
from .match import (
    MatchError, Matcher, Row, count_var, fail_expr, fresh_name, normalize,
    reset_names, subst_var,
)
from .syntax.ast import (
    at,
    Pat,
    PAnnot,
    PBox,
    PCon,
    PSigCons,
    PLit,
    PList,
    PTuple,
    PVar,
    Val,
    VAlt,
    VAnnot,
    VApp,
    VBox,
    VCase,
    VConId,
    VFix,
    VFor,
    VFunc,
    VGfix,
    VGiven,
    VInfix,
    VLet,
    VList,
    VNum,
    VPostfix,
    VProj,
    VPrefix,
    VSet,
    VStr,
    VTuple,
    VUnbox,
    VWord,
)
from .syntax.rename import pat_names
from .types import TFun


def _of(sc) -> str:
    """` (at L:C)` for a whole definition — its first equation.

    An `SCInfo` is a name and a list of equations and carries no span of
    its own; the equations do.  A complaint about a *definition* wants
    the line the definition starts on, which is the first one.
    """
    return at(sc.equations[0]) if getattr(sc, "equations", None) else ""


#: complaint  author — the program as written, before it is typed
class DesugarError(Exception):
    pass


def _lift_spine(val):
    """`(head, args)` if `val` is a `!`-marked application, else `None`.

    `!` binds to the head — the parser takes one atom for it, so `!f x y`
    arrives as `(!f) x y` — and the marker is found by walking the
    application spine down to its head, exactly where a reader sees it.
    The marker's own operand is **one value and stays one value**:
    `!(f x)` is the constant signal of the *computed value* `f x`, and
    `!(f x) y` lifts that computed function over `y`.  One rule serves
    every spelling — the marker takes the next atom, and the application
    around it supplies the lifted arguments.

    (It was not always so: the marker used to be resolved after
    application folding, which made `!(f x)` and `!f x` the same tree
    and the parenthesised constant unwritable — the history is in
    `spec/exclamation.md`.)
    """
    args = []
    node = val
    while isinstance(node, VApp):
        args.append(node.arg)
        node = node.fn
    if not (isinstance(node, VPrefix) and node.op == "!"):
        return None
    return node.arg, list(reversed(args))


def _desugar_lift(lifted, locals_, cons, using_map, aliases) -> Expr:
    """`!f x y …` — one function over as many signals as it is given.

    **The lift is written, not inferred.**  A lift a compiler inserted
    where types disagreed would put a node in the graph the author never
    wrote, and stage 5 migrates running state by comparing node *origins*:
    an edit that changed an inferred lift would silently reset an
    oscillator's phase.  One character says which application is lifted,
    and the graph is exactly what it says.

    Four cases, and only the last is interesting:

    * `!x`         — `constSig x`, the constant signal.  Applicative
                     `pure`; the backend supplies the name, since what a
                     signal is constant *over* is the backend's clock.
    * `!f x`       — `mapSig f x`.
    * `!f x y`     — `zipSig f x y`.
    * `!f x y z …` — the arguments are paired up into a `Both` tree with
                     `zipSig`, and one `mapSig` at the end takes the tree
                     apart and applies `f` to the pieces.  There is no
                     three-signal former to fuse to and there cannot be a
                     `Sig (b -> c)` to chain through — a signal of
                     functions has no layout — so a shape is what carries
                     the extra arguments, which is what the `voices`
                     expander does with its `Part` records for the same
                     reason.
    """
    head, args = lifted
    of = lambda v: desugar_expr(v, locals_, cons, using_map, aliases)
    fn = of(head)

    if not args:
        return EAp(EGlobal("constSig"), fn)
    if len(args) == 1:
        return EAp(EAp(EGlobal("mapSig"), fn), of(args[0]))
    if len(args) == 2:
        return EAp(EAp(EAp(EGlobal("zipSig"), fn), of(args[0])), of(args[1]))

    if "Both" not in cons:
        #: complaint  author, nowhere — which libraries the program was assembled with, which is a fact about the assembly and not about a line of it
        raise DesugarError(
            "`!` over three or more signals needs `Both` from "
            "`signal.ges`, which this program was not assembled with")
    tag = cons["Both"].tag

    # Left fold: ((x, y), z), … — one `zipSig` per extra argument, pairing
    # with a **lambda** rather than a named `bothOf`.  A step function
    # survives into the IR as a function emitted once, at one type, so a
    # named polymorphic pairer would be one entry serving two element
    # types; a lambda is inlined at each site and has the type of that
    # site.
    def pair(left: Expr, right: Expr) -> Expr:
        a, b = fresh_name("pairL"), fresh_name("pairR")
        step = ELambda([a, b], ECon(tag, [EVar(a), EVar(b)]))
        return EAp(EAp(EAp(EGlobal("zipSig"), step), left), right)

    tree = pair(of(args[0]), of(args[1]))
    for extra in args[2:]:
        tree = pair(tree, of(extra))

    # …and one `mapSig` that unfolds it in the same order and applies `f`.
    #
    # `peels[k]` is the tree of the first `k + 2` arguments, so the case
    # nest runs outside in: the last argument comes off first, and the
    # innermost alternative binds the first two.
    names = [fresh_name(f"lift{i}") for i in range(len(args))]
    peels = [fresh_name(f"both{i}") for i in range(len(args) - 1)]

    body: Expr = fn
    for n in names:
        body = EAp(body, EVar(n))
    body = ECase(EVar(peels[0]),
                 [Alter(tag=tag, names=[names[0], names[1]], body=body)])
    for i in range(2, len(args)):
        body = ECase(EVar(peels[i - 1]),
                     [Alter(tag=tag, names=[peels[i - 2], names[i]],
                            body=body)])
    return EAp(EAp(EGlobal("mapSig"), ELambda([peels[-1]], body)), tree)


def _val_children(v) -> list:
    """Every immediate `Val` sub-node, read off the dataclass fields.

    Field-driven so it stays total as node kinds are added, the same
    argument `expr.subexprs` makes for the core grammar.
    """
    from dataclasses import fields, is_dataclass

    if not is_dataclass(v):
        return []
    out = []
    for f in fields(v):
        got = getattr(v, f.name, None)
        if isinstance(got, Val):
            out.append(got)
        elif isinstance(got, (list, tuple)):
            for item in got:
                if isinstance(item, Val):
                    out.append(item)
                elif isinstance(item, tuple):
                    out.extend(x for x in item if isinstance(x, Val))
    return out


def _needs_of(val, bound: frozenset, needs: dict[str, set[str]]) -> set[str]:
    """Implicits `val` refers to that nothing in scope supplies.

    A mention of a supercombinator that needs implicits requires them
    *here* unless something binds them — its own `using` parameters, or a
    `given` between it and this point.  That is what makes the scope
    dynamic: the requirement travels outward until a `given` stops it.

    `bound` does double duty, because in this language one set answers both
    questions it is asked: a bound name is not a reference to the global of
    that name, *and* a bound name supplies the implicit of that name (which
    is how `desugar_expr` fills the argument in).  So every binder form has
    to be enumerated — a lambda parameter called `f` must not be read as a
    call to a supercombinator `f`.  The list mirrors `syntax/rename.py`,
    which walks the same binders for the same reason.
    """
    if isinstance(val, VWord):
        if val.value in bound:
            return set()                       # a local, not a global
        return {n for n in needs.get(val.value, ()) if n not in bound}

    if isinstance(val, (VLet, VGiven)):
        # A `given` reads as a `let` whose names are *also* implicits, so
        # its right-hand sides are outside the scope it introduces.
        binders = frozenset(n for n, _rhs in val.bindings)
        rhs_scope = bound | binders if getattr(val, "is_rec", False) else bound
        out: set[str] = set()
        for _n, rhs in val.bindings:
            out |= _needs_of(rhs, rhs_scope, needs)
        return out | _needs_of(val.body, bound | binders, needs)

    if isinstance(val, VFunc):
        return _needs_of(val.body, bound | _pat_names(val.params), needs)

    if isinstance(val, VCase):
        # Explicit because `VAlt` is not a `Val`, so `_val_children` does
        # not yield the alternatives — walking a `case` generically reaches
        # the scrutinee and nothing else.
        out = _needs_of(val.scrut, bound, needs)
        for alt in val.alts:
            out |= _needs_of(alt.body, bound | pat_names(alt.pat), needs)
        return out

    if isinstance(val, VAlt):
        return _needs_of(val.body, bound | pat_names(val.pat), needs)

    if isinstance(val, VFor):
        out = set()
        for _p, src in val.bindings:
            out |= _needs_of(src, bound, needs)
        inner = bound | _pat_names([p for p, _src in val.bindings])
        return out | _needs_of(val.body, inner, needs)

    if isinstance(val, VUnbox):
        return (_needs_of(val.binding, bound, needs)
                | _needs_of(val.body, bound | pat_names(val.pat), needs))

    if isinstance(val, VGfix):
        return _needs_of(val.body, bound | {val.var}, needs)

    out = set()
    for child in _val_children(val):
        out |= _needs_of(child, bound, needs)
    return out


def _pat_names(pats) -> frozenset[str]:
    out = frozenset()
    for p in pats:
        out |= pat_names(p)
    return out


def _implicit_needs(program: Program) -> dict[str, list[str]]:
    """Every implicit each supercombinator needs, its callees' included.

    `(using n)` says which implicits a *body* names.  A caller that never
    writes `n` still has to supply it, so the requirement propagates along
    the call graph to a fixed point — which is what makes `given`'s scope
    dynamic rather than a `let` with extra steps.

    The order is sorted rather than declaration order, because a caller's
    set is a union and has no declaration order of its own; the frame and
    every call site read it from here, so they agree.
    """
    own = {sc.name: set(sc.using_params or ()) for sc in program.scs}

    # An implicit is resolved by name, so the name has to exist.  Without
    # this a mistyped `(using ppq)` becomes a fresh implicit that nothing
    # supplies, and the only complaint is about a name the program never
    # meant to mention.
    for sc in program.scs:
        for n in sorted(own[sc.name]):
            if n not in program.implicits:
                raise DesugarError(
                    f"`{sc.name}` uses an undeclared implicit `{n}`.  "
                    f"Declare its type at the top level: `implicit {n} : …`"
                    f"{_of(sc)}"
                )

    if not any(own.values()):
        # Nothing declares an implicit, so nothing can require one, and the
        # fixed point below has no work to do.  Worth short-circuiting: it
        # walks every body once per round, and almost no program uses this.
        return {}
    needs = {name: set(v) for name, v in own.items()}

    while True:
        changed = False
        for sc in program.scs:
            acc = set(needs[sc.name])
            for eq in sc.equations:
                params = _pat_names(eq.params)
                acc |= _needs_of(eq.body, frozenset(own[sc.name]) | params,
                                 needs)
            if acc != needs[sc.name]:
                needs[sc.name] = acc
                changed = True
        if not changed:
            break

    out = {name: sorted(v) for name, v in needs.items() if v}

    # An implicit that reaches the entry point has nothing left to fill it,
    # and a program must not be constructible in that state.  Everything
    # else may carry a requirement, because carrying it *is* how it reaches
    # a `given`: propagation guarantees that if `main` needs none, every
    # path from `main` passed one.
    if "main" in out:
        wanted = out["main"]
        source = {n: sc for sc, ns in own.items() for n in ns if n in wanted}
        detail = ", ".join(
            f"`{n}`" + (f" (required by `{source[n]}`)" if n in source else "")
            for n in wanted)
        #: complaint  author, nowhere — an implicit nothing supplies is an absence, and an absence is not written anywhere
        raise DesugarError(
            f"unfilled implicit: {detail} reaches `main`, and nothing "
            f"supplies it.  Bind it with `given {wanted[0]} = … in …` "
            f"somewhere the use is inside"
        )
    return out


def desugar_program(program: Program) -> list[tuple[str, int, ELambda, object]]:
    """Convert a classified Program into SC triples ready for lifting."""
    result: list[tuple[str, int, ELambda, object]] = []
    reset_names()
    aliases = program.aliases
    using_map = _implicit_needs(program)

    for sc in program.scs:
        if not sc.equations:
            #: complaint  machine — a definition with no equations cannot be parsed; this guards the desugarer's own input
            raise DesugarError(f"SC '{sc.name}' has no equations")

        eqs = sc.equations
        using_params = using_map.get(sc.name, [])
        # The implicits become *leading* parameters, so the signature the
        # user wrote describes only what is left.  Extending it here, from
        # the `implicit n : τ` declarations, is what keeps implicits out of
        # every signature along the call chain: `bar = quarter * 4` does
        # not change type when `quarter` starts needing one.
        sig = sc.sig_type
        if sig is not None and using_params:
            for n in reversed(using_params):
                sig = TFun(program.implicits[n], sig)

        # Only a single equation of plain variables skips the match
        # compiler — there is nothing for it to do there, and binding the
        # parameters directly keeps the generated code readable.
        has_patterns = any(
            any(not isinstance(p, PVar) for p in eq.params) for eq in eqs
        )

        if has_patterns or len(eqs) > 1:
            lam = _desugar_pattern_sc(sc.name, eqs, program.cons, using_map,
                                      aliases, using_params)
            all_params = using_params + [str(lam[1].params[i]) for i in range(len(lam[1].params))]
            lam_with_using = ELambda(all_params, lam[1].body)
            result.append((sc.name, len(all_params), lam_with_using, sig))
        else:
            eq = eqs[0]
            all_params = using_params + [p.name for p in eq.params]
            scope = frozenset(all_params)
            body = desugar_expr(eq.body, scope, program.cons, using_map, aliases)
            result.append((sc.name, len(all_params),
                          ELambda(list(all_params), body), sig))

    # Guarded recursion, last: it needs the SC's whole body, and the
    # `delay`s it looks for may come from `|>` sugar in `desugar_expr`.
    return [(name, *_guard_recursion(name, arity, lam), sig)
            for name, arity, lam, sig in result]


# ---------------------------------------------------------------------------
# Guarded recursion  (Rizzo §2.4)
# ---------------------------------------------------------------------------
#
#     f x₁ … xₙ = C[delay t₁, …, delay tₙ]          (f not free in C)
#   ⇝ f = fix r. λx₁ … λxₙ. C[delay(λr'. t₁[r'/f]) ⊛ r, …,
#                             delay(λr'. tₙ[r'/f]) ⊛ r]
#
# Every recursive call sits under a `delay`, which is what makes the
# definition productive; the transform turns each such guard into a use of
# the guarded fixed point's own binder, so the user never writes `gfix`,
# `⊛` or the `λr'` plumbing by hand.


def _guard_recursion(name: str, arity: int, lam: ELambda) -> tuple[int, ELambda]:
    """Rewrite ``lam`` into a guarded fixed point, if it is one.

    Returns the SC's ``(arity, lambda)`` unchanged when the definition is
    not guarded-recursive — ordinary recursion (``fact``, ``fib``) has no
    ``delay`` around its recursive call and is compiled as it always was.
    """
    body = lam.body
    if not any(isinstance(e, EDelay) and _mentions(e.body, name)
               for e in _walk(body)):
        return arity, lam

    r = f"_gfix_{name}"
    r_self = f"_gfix_{name}_self"

    def rewrite(e: Expr) -> Expr:
        if isinstance(e, EDelay) and _mentions(e.body, name):
            inner = _subst_global(e.body, name, EVar(r_self))
            return EAppFa(EDelay(ELambda([r_self], inner)), EVar(r))
        return _map_children(e, rewrite)

    new_body = rewrite(body)
    if _mentions(new_body, name):
        raise DesugarError(
            f"SC '{name}': some recursive calls are guarded by `delay` and "
            f"some are not.  A guarded definition must have every recursive "
            f"call under a `delay`, or it is not productive{at(lam)}"
        )

    # `fix r` goes *outside* the parameters, so the SC itself takes none.
    inner_lam: Expr = ELambda(list(lam.params), new_body) if lam.params else new_body
    return 0, ELambda([], EGFix(r, inner_lam))


def _walk(e: Expr):
    """Every node of ``e``, root first."""
    stack = [e]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(subexprs(node))


def _mentions(e: Expr, name: str) -> bool:
    return any(isinstance(n, EGlobal) and n.name == name for n in _walk(e))


def _subst_global(e: Expr, name: str, replacement: Expr) -> Expr:
    if isinstance(e, EGlobal) and e.name == name:
        return replacement
    return _map_children(e, lambda c: _subst_global(c, name, replacement))


def _desugar_pattern_sc(
    name: str, eqs: list, cons: dict[str, ConInfo],
    using_map: dict[str, list[str]] | None = None,
    aliases: dict[str, AliasInfo] | None = None,
    using_params: list[str] | None = None,
) -> tuple[int, ELambda]:
    """Desugar a pattern-matching SC through the match compiler.

    Every equation becomes one row of a pattern matrix whose columns are
    the SC's arguments; `gestate/match.py` lowers the matrix to one-level
    ``ECase``.  All arities, nesting depths and pattern kinds go through
    the same path, so ``f n [] = …; f n (x :: xs) = …`` is no harder than
    a single-argument dispatch.
    """
    if not eqs:
        #: complaint  machine — a definition with no equations cannot be parsed; this guards the desugarer's own input
        raise DesugarError(f"SC '{name}' has no equations")

    arity = len(eqs[0].params)
    if any(len(eq.params) != arity for eq in eqs):
        raise DesugarError(
            f"SC '{name}': all equations must have the same number of "
            f"parameters{at(eqs[0])}"
        )

    arg_names = [f"_{name}_arg{i}" for i in range(arity)]
    scope = frozenset(arg_names) | frozenset(using_params or ())

    matcher = Matcher(
        cons,
        lambda val, loc: desugar_expr(val, loc, cons, using_map, aliases),
        where=f"SC '{name}'",
    )
    rows = [Row([normalize(p) for p in eq.params], eq.body) for eq in eqs]
    try:
        body = matcher.compile(arg_names, rows, fail_expr(), scope)
    except MatchError as e:
        raise DesugarError(str(e)) from None
    return (arity, ELambda(arg_names, body))


def strip_annotations(e: Expr) -> Expr:
    """Remove all ``EAnnot`` nodes from an expression tree."""
    if isinstance(e, EAnnot):
        return strip_annotations(e.expr)
    if isinstance(e, ELambda):
        return ELambda(list(e.params), strip_annotations(e.body))
    if isinstance(e, EAp):
        return EAp(strip_annotations(e.fn), strip_annotations(e.arg))
    if isinstance(e, ELet):
        defs = [(n, strip_annotations(d)) for n, d in e.defs]
        return ELet(e.is_rec, defs, strip_annotations(e.body))
    if isinstance(e, ECase):
        alts = [Alter(a.tag, list(a.names), strip_annotations(a.body)) for a in e.alts]
        return ECase(strip_annotations(e.scrut), alts)
    if isinstance(e, ETuple):
        return ETuple([strip_annotations(a) for a in e.args])
    if isinstance(e, ECon):
        return ECon(e.tag, [strip_annotations(a) for a in e.args])
    # FRP nodes: pass through
    if isinstance(e, ESigCons):
        return ESigCons(strip_annotations(e.value), strip_annotations(e.tail))
    if isinstance(e, ESigHead):
        return ESigHead(strip_annotations(e.sig))
    if isinstance(e, EDelay):
        return EDelay(strip_annotations(e.body))
    if isinstance(e, EAppFa):
        return EAppFa(strip_annotations(e.fn), strip_annotations(e.arg))
    if isinstance(e, EAppEx):
        return EAppEx(strip_annotations(e.fn), strip_annotations(e.arg))
    if isinstance(e, EWait):
        return EWait(strip_annotations(e.chan))
    if isinstance(e, EWatch):
        return EWatch(strip_annotations(e.sig))
    if isinstance(e, ESync):
        return ESync(strip_annotations(e.left), strip_annotations(e.right))
    if isinstance(e, ETail):
        return ETail(strip_annotations(e.sig))
    if isinstance(e, EGFix):
        return EGFix(e.var, strip_annotations(e.body))
    if isinstance(e, (ENever, EChan)):
        return e
    # Datafun nodes
    if isinstance(e, EFix):
        return EFix(strip_annotations(e.body))
    if isinstance(e, EFor):
        return EFor(e.var, strip_annotations(e.set_expr), strip_annotations(e.body))
    if isinstance(e, EBox):
        return EBox(strip_annotations(e.body))
    if isinstance(e, EUnbox):
        return EUnbox(e.var, strip_annotations(e.binding), strip_annotations(e.body))
    if isinstance(e, ESet):
        return ESet([strip_annotations(a) for a in e.items])
    return e


def _irrefutable(pat: Pat) -> bool:
    """Can this pattern fail to match?

    Only shapes that match every value of their type: a variable, and a
    tuple of them.  A constructor pattern is excluded even at a
    single-constructor type — the check would have to consult `cons`, and
    the restriction is meant to be readable from the pattern alone.
    """
    if isinstance(pat, PVar):
        return True
    if isinstance(pat, PAnnot):
        return _irrefutable(pat.pat)
    if isinstance(pat, PTuple):
        return all(_irrefutable(i) for i in pat.items)
    if isinstance(pat, PBox):
        return _irrefutable(pat.pat)
    return False


def desugar_expr(val: Val, locals_: frozenset[str],
                 cons: dict[str, ConInfo],
                 using_map: dict[str, list[str]] | None = None,
                 aliases: dict[str, AliasInfo] | None = None) -> Expr:
    """Convert a surface ``Val`` to an ``Expr``."""
    if using_map is None:
        using_map = {}
    if aliases is None:
        aliases = {}

    if isinstance(val, VWord):
        # `_` in expression position is a **hole** — a value not written
        # yet.  In a *pattern* it is the wildcard it has always been, and
        # nothing here sees patterns, so the two do not collide.  A hole
        # bound as a name is still a name: `f _ = _` binds nothing and
        # returns a hole, which is what both spellings already meant.
        if val.value == "_" and val.value not in locals_:
            return EHole(span=val.span)
        # FRP primitives used as standalone values
        if val.value == "never":
            return ENever()
        if val.value == "chan":
            return EChan()
        # **The author's own position, carried across the desugaring.**
        # This is the one place a name the author typed becomes a core
        # node, so it is the one place the position can be picked up — and
        # without it `Unknown global 'sinewave'` has nothing to say about
        # where the typo is.  The implicit arguments below get it too: they
        # stand at the same place in the text.
        where = getattr(val, "span", None)
        if val.value in locals_:
            return EVar(val.value, span=where)
        if val.value in using_map:
            fn_expr: Expr = EGlobal(val.value, span=where)
            for up in using_map[val.value]:
                if up in locals_:
                    fn_expr = EAp(fn_expr, EVar(up, span=where))
                else:
                    fn_expr = EAp(fn_expr, EGlobal(up, span=where))
            return fn_expr
        return EGlobal(val.value, span=where)

    if isinstance(val, VConId):
        if val.value in cons:
            info = cons[val.value]
            if info.arity == 0:
                return ECon(info.tag, [])
            # **A constructor used as a value, eta-expanded here.**
            #
            # `ECon` is saturated by construction — it carries its fields —
            # so a constructor that is not applied to all of them has no
            # `ECon` to become.  It used to become `EGlobal(name)`, and
            # nothing defines that global: `zipSig Stereo l r` was rejected
            # with *Unknown global 'Stereo'*, naming an internal form for a
            # program that is perfectly ordinary.  Writing
            # `frameOf l r = Stereo l r` by hand was the whole workaround,
            # which is the language asking the author to do eta-expansion
            # it can do itself.
            #
            # A lambda rather than a generated supercombinator per
            # constructor: lambda lifting already turns this into exactly
            # that, and only for the constructors a program actually uses
            # as values.  Every existing program compiles to what it did.
            names = [fresh_name(f"c{j}") for j in range(info.arity)]
            return ELambda(names, ECon(info.tag, [EVar(n) for n in names]))
        return EGlobal(val.value)

    if isinstance(val, VNum):
        # Both literals go through their class's way *in*, which is what
        # makes either one polymorphic: `2` is `Num a => a` and `0.5` is
        # `Floating a => a`.  A float literal used to be a bare `Float`,
        # so `tone * 0.5` was a type error at a type where `tone * 2` was
        # not — see `Floating` in `declarations.py`.
        if isinstance(val.value, int):
            return EAp(EGlobal("fromInteger"), ENum(val.value))
        return EAp(EGlobal("fromFloat"), ENum(val.value))

    # `!f x y` — an application lifted over signals.
    lifted = _lift_spine(val)
    if lifted is not None:
        return _desugar_lift(lifted, locals_, cons, using_map, aliases)

    # FRP single-arg forms: `head e`, `delay e`, `wait e`, `watch e`, `tail e`
    if isinstance(val, VApp) and isinstance(val.fn, VWord):
        fn_name = val.fn.value
        if fn_name == "head":
            return ESigHead(desugar_expr(val.arg, locals_, cons, using_map, aliases))
        if fn_name == "delay":
            return EDelay(desugar_expr(val.arg, locals_, cons, using_map, aliases))
        if fn_name == "wait":
            return EWait(desugar_expr(val.arg, locals_, cons, using_map, aliases))
        if fn_name == "watch":
            return EWatch(desugar_expr(val.arg, locals_, cons, using_map, aliases))
        if fn_name == "tail":
            return ETail(desugar_expr(val.arg, locals_, cons, using_map, aliases))

    # FRP two-arg form: `sync a b`
    if isinstance(val, VApp) and isinstance(val.fn, VApp) and isinstance(val.fn.fn, VWord):
        if val.fn.fn.value == "sync":
            return ESync(
                desugar_expr(val.fn.arg, locals_, cons, using_map, aliases),
                desugar_expr(val.arg, locals_, cons, using_map, aliases),
            )

    if isinstance(val, VApp):
        con = _resolve_con_app(val, cons)
        if con is not None:
            con_name, con_info, con_args = con
            if len(con_args) == con_info.arity:
                return ECon(con_info.tag,
                            [desugar_expr(a, locals_, cons, using_map, aliases) for a in con_args])
            elif len(con_args) < con_info.arity:
                pass
            else:
                raise DesugarError(
                    f"Constructor {con_name} applied to {len(con_args)} args, "
                    f"but arity is {con_info.arity}{at(val)}"
                )
        return EAp(
            desugar_expr(val.fn, locals_, cons, using_map, aliases),
            desugar_expr(val.arg, locals_, cons, using_map, aliases),
        )

    if isinstance(val, VInfix):
        if val.op == "\\/":
            return EJoin(
                desugar_expr(val.left, locals_, cons, using_map, aliases),
                desugar_expr(val.right, locals_, cons, using_map, aliases),
            )
        if val.op in (":::", "<*>", "<@>", "|>"):
            left = desugar_expr(val.left, locals_, cons, using_map, aliases)
            right = desugar_expr(val.right, locals_, cons, using_map, aliases)
            if val.op == ":::":
                return ESigCons(left, right)
            if val.op == "<*>":
                return EAppFa(left, right)
            if val.op == "<@>":
                return EAppEx(left, right)
            # `f |> x = delay f <@> x` (Rizzo §2.1's ▷) — the functorial
            # action on ⃝∃, sugar rather than a primitive.
            return EAppEx(EDelay(left), right)
        if val.op == "::":
            left = desugar_expr(val.left, locals_, cons, using_map, aliases)
            right = desugar_expr(val.right, locals_, cons, using_map, aliases)
            return ECon(cons["Cons"].tag, [left, right])
        if val.op[:1].isalpha() or val.op[:1] == "_":
            # **A name in backticks is the name applied to two arguments**,
            # and is desugared as exactly that rather than as an operator
            # that happens to be spelled with letters: `x `over` y` and
            # `over x y` must not be two things, or a local, a `using`
            # parameter, a constructor and an FRP form would each have to
            # be taught to this branch a second time.
            head = (VConId(val.op, val.span) if val.op[:1].isupper()
                    else VWord(val.op, val.span))
            applied = VApp(VApp(head, val.left, val.span), val.right, val.span)
            return desugar_expr(applied, locals_, cons, using_map, aliases)
        return EAp(
            EAp(EGlobal(val.op), desugar_expr(val.left, locals_, cons, using_map, aliases)),
            desugar_expr(val.right, locals_, cons, using_map, aliases),
        )

    if isinstance(val, VPrefix):
        return EAp(EGlobal(val.op), desugar_expr(val.arg, locals_, cons, using_map, aliases))

    if isinstance(val, VPostfix):
        return EAp(EGlobal(val.op), desugar_expr(val.arg, locals_, cons, using_map, aliases))

    if isinstance(val, VFunc):
        # A pattern parameter binds a fresh name and matches it, so
        # `map ((a, b) => a) xs` works — the parser accepted this and only
        # the desugarer refused, which is the gap that surprises
        # (`fixme.md` F71).
        params: list[str] = []
        body = val.body
        wraps: list[tuple[str, Pat]] = []
        for p in val.params:
            if isinstance(p, PVar):
                params.append(p.name)
                continue
            if not _irrefutable(p):
                raise DesugarError(
                    f"a lambda's parameter must be irrefutable — a variable "
                    f"or a tuple of them — because there is nowhere for a "
                    f"failed match to go.  Use `case` to match a "
                    f"constructor{at(p)}"
                )
            name = fresh_name("lam")
            params.append(name)
            wraps.append((name, p))
        for name, pat in reversed(wraps):
            body = VCase(VWord(name, pat.span), [VAlt(pat, body, pat.span)],
                         pat.span)
        new_locals = locals_ | frozenset(params)
        return ELambda(params, desugar_expr(body, new_locals, cons, using_map, aliases))

    if isinstance(val, VLet):
        binder_names = frozenset(val.bindings[i][0] for i in range(len(val.bindings)))
        # A recursive group sees every binder everywhere; a plain `let`
        # is *sequential* — each binding sees the ones above it, which is
        # `ELet`'s stated contract and what `compile_let` lays out.  It
        # used to see none of them, so `let a = …` followed by
        # `b = f a` resolved `a` as a global and failed a definition away
        # from where it was written.
        rhs_env = locals_ | binder_names if val.is_rec else locals_
        defs: list[tuple[Name, Expr]] = []
        for nm, rhs in val.bindings:
            defs.append((nm, desugar_expr(rhs, rhs_env, cons, using_map, aliases)))
            if not val.is_rec:
                rhs_env = rhs_env | frozenset((nm,))
        body = desugar_expr(val.body, locals_ | binder_names, cons, using_map, aliases)
        return ELet(val.is_rec, defs, body)

    if isinstance(val, VCase):
        scrut = desugar_expr(val.scrut, locals_, cons, using_map, aliases)
        matcher = Matcher(
            cons,
            lambda v, loc: desugar_expr(v, loc, cons, using_map, aliases),
            where="case",
        )
        subject = matcher.fresh("scrut")
        rows = [Row([normalize(a.pat)], a.body) for a in val.alts]
        try:
            body = matcher.compile([subject], rows, fail_expr(),
                                   locals_ | {subject})
        except MatchError as e:
            raise DesugarError(str(e)) from None

        # Put the scrutinee back where its subject stood, rather than
        # binding it.  A constructor dispatch names the subject exactly
        # once, so this recovers `case e of …` verbatim — which matters
        # beyond tidiness: a `let` the source did not write is a change
        # variable the ϕ/δ transform has no rule for.  A literal dispatch
        # tests the subject repeatedly and does need the binding, so that
        # the scrutinee is evaluated once.
        uses = count_var(body, subject)
        if uses <= 1 or isinstance(scrut, (EVar, EGlobal, ENum)):
            return subst_var(body, subject, scrut)
        return ELet(False, [(subject, scrut)], body)

    if isinstance(val, VProj):
        # `e.N` cannot be lowered here — which shape it selects from
        # depends on `e`'s type, and there are none yet (`fixme.md` F28).
        return EField(desugar_expr(val.base, locals_, cons, using_map, aliases),
                      val.index)

    if isinstance(val, VTuple):
        return ETuple([desugar_expr(item, locals_, cons, using_map, aliases) for item in val.items])

    if isinstance(val, VAnnot):
        return EAnnot(desugar_expr(val.expr, locals_, cons, using_map, aliases),
                      desugar_type(val.type_, None, aliases))

    # -- Datafun forms (increment 10a) --

    if isinstance(val, VFix):
        return EFix(desugar_expr(val.body, locals_, cons, using_map, aliases))

    if isinstance(val, VFor):
        # `for (C, D) e` is `for (C) for (D) e`, peeled one clause at a
        # time.  It used to read `val.bindings[0]` and *drop the rest*, so
        # `for (x in a, y in b) e` — the form `spec/syntax.md` documents —
        # compiled to `for (x in a) e` with `y` unbound.
        (pat, src), rest = val.bindings[0], val.bindings[1:]
        body = val.body if not rest else VFor(rest, val.body, val.span)

        if not isinstance(pat, PVar):
            # A pattern binds the element and then matches it, which is what
            # makes `{(fst p, snd q) | p in r, q in e}` writable at all.
            # Only irrefutable patterns: fig. 2.2 gives a failing match the
            # value ⊥, and ⊥ is type-directed (`{}` at a set, `()` at unit,
            # componentwise at a product) so desugaring cannot build it.
            # Filtering is what a guard clause is for, and it is right here.
            if not _irrefutable(pat):
                raise DesugarError(
                    "a `for`/comprehension clause needs an irrefutable "
                    "pattern — a variable or a tuple of them — because a "
                    "pattern that can fail has no value to take when it "
                    "does.  Bind the element and filter with a guard "
                    "clause instead: `{e | x in s, <test>}`"
                    f"{at(pat)}"
                )
            name = fresh_name("elem")
            body = VCase(VWord(name, pat.span), [VAlt(pat, body, pat.span)],
                         val.span)
            pat = PVar(name, pat.span)

        new_locals = locals_ | frozenset([pat.name])
        return EFor(pat.name,
                    desugar_expr(src, locals_, cons, using_map, aliases),
                    desugar_expr(body, new_locals, cons, using_map, aliases))

    if isinstance(val, VSet):
        return ESet([desugar_expr(item, locals_, cons, using_map, aliases) for item in val.items])

    if isinstance(val, VBox):
        return EBox(desugar_expr(val.body, locals_, cons, using_map, aliases))

    if isinstance(val, VUnbox):
        if not isinstance(val.pat, PVar):
            raise DesugarError(
                f"unbox pattern must be a variable{at(val.pat)}")
        new_locals = locals_ | frozenset([val.pat.name])
        return EUnbox(val.pat.name,
                      desugar_expr(val.binding, locals_, cons, using_map, aliases),
                      desugar_expr(val.body, new_locals, cons, using_map, aliases))

    if isinstance(val, VGfix):
        new_locals = locals_ | frozenset([val.var])
        return EGFix(val.var, desugar_expr(val.body, new_locals, cons, using_map, aliases))

    if isinstance(val, VGiven):
        binder_names = frozenset(val.bindings[i][0] for i in range(len(val.bindings)))
        defs: list[tuple[Name, Expr]] = []
        for nm, rhs in val.bindings:
            defs.append((nm, desugar_expr(rhs, locals_, cons, using_map, aliases)))
        new_locals = locals_ | binder_names
        body = desugar_expr(val.body, new_locals, cons, using_map, aliases)
        return ELet(False, defs, body)

    if isinstance(val, VStr):
        # "hi" is `'h' :: 'i' :: []` at `List Char`, spelled out rather
        # than given a heap node of its own: every list function, and
        # `Eq`/`Show (List a)`, then work on it unchanged.
        nil_tag = cons["Nil"].tag
        cons_tag = cons["Cons"].tag
        acc: Expr = ECon(nil_tag, [])
        for ch in reversed(val.value):
            acc = ECon(cons_tag, [EChr(ord(ch)), acc])
        return acc

    if isinstance(val, VList):
        nil_tag = cons["Nil"].tag
        cons_tag = cons["Cons"].tag
        items = [desugar_expr(item, locals_, cons, using_map, aliases) for item in val.items]
        rest = (desugar_expr(val.tail, locals_, cons, using_map, aliases)
                if val.tail is not None else ECon(nil_tag, []))
        for item in reversed(items):
            rest = ECon(cons_tag, [item, rest])
        return rest

    raise DesugarError(
        f"Unsupported expression form: {type(val).__name__}{at(val)}")


# ---------------------------------------------------------------------------
# Constructor application helpers
# ---------------------------------------------------------------------------

def _resolve_con_app(app: VApp, cons: dict[str, ConInfo]) -> tuple[str, ConInfo, list[Val]] | None:
    """If ``app`` is a constructor application spine, return (name, info, args)."""
    if isinstance(app.fn, VConId) and app.fn.value in cons:
        con_info = cons[app.fn.value]
        args = [app.arg]
        return (app.fn.value, con_info, args)
    if isinstance(app.fn, VApp):
        inner = _resolve_con_app(app.fn, cons)
        if inner is not None:
            name, info, args = inner
            args.append(app.arg)
            return (name, info, args)
    return None


# Pattern compilation lives in `gestate/match.py`.


# ---------------------------------------------------------------------------
# Field projection — lowering, after inference has resolved the shape
# ---------------------------------------------------------------------------

def lower_fields(scs: list) -> list:
    """Rewrite every `EField` into the selector its base type calls for.

    Runs after inference and before anything else looks at the tree, so no
    later pass has to know `EField` exists.  A tuple becomes the ordinary
    `EProj` the match compiler already emits; a record becomes a `case`
    with one alternative, which is what a one-constructor `NCon` *is*.
    """
    def rewrite(e: Expr) -> Expr:
        e = _map_children(e, rewrite)
        if not isinstance(e, EField):
            return e
        if e.lowering is None:                  # pragma: no cover - defensive
            #: complaint  machine — inference resolves every projection or refuses it, so reaching codegen unresolved is this program's own doing
            raise DesugarError(
                f"internal: a projection reached codegen unresolved; "
                f"inference should have rejected it"
            )
        kind = e.lowering[0]
        if kind == "tuple":
            _k, i, width = e.lowering
            return EAp(EProj(i, width), e.base)
        _k, tag, arity, i = e.lowering
        names = [fresh_name(f"f{j}") for j in range(arity)]
        return ECase(e.base, [Alter(tag, names, EVar(names[i]))])

    # `replace`, not `ELambda(params, body)`: a lambda also carries the
    # binder flavours inference left on it, and naming only the fields this
    # pass knows about drops them — which is the failure mode
    # `expr.map_children`'s docstring warns about, and it silently disabled
    # the monotone check for every supercombinator.
    from dataclasses import replace as _replace

    return [(name, arity, _replace(lam, body=rewrite(lam.body)), sig)
            for name, arity, lam, sig in scs]
