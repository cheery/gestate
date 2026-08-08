"""Specialise a constrained supercombinator at a constant dictionary.

`elaborate` gives an SC with a context one parameter per constraint and
makes every call site pass a dictionary:

    clamp : (Ord a) => a -> a -> a -> a

    clamp _g0 _g1 lo hi x = …            -- `_g0 : Ord a`, `_g1 : Eq a`
    cut x = clamp __dict_Ord_Float__ __dict_Eq_Float__ 0.0 1.0 x

That is the right compilation in general and it is **fatal to the audio
backend**, which is monomorphic: a dictionary is a record of functions and
the engine has nowhere to put one, so `audiograph` refuses any definition
that mentions one.  `clamp` written at `Float` was fine; `clamp` written
against `Ord` was not, and the difference is invisible at the call site —
the program says `clamp 0.0 1.0 x` either way.

**So specialise where the dictionary is known.**  A call whose dictionary
arguments are all constant dictionary *globals* has exactly one possible
callee, so it can have a copy of its own with them substituted in:

    clamp#Ord_Float#Eq_Float lo hi x = …   -- no dictionary parameters
    cut x = clamp#Ord_Float#Eq_Float 0.0 1.0 x

`resolve_static_methods` then finishes the job: the copy's body projects
methods out of a *global* dictionary rather than out of a parameter, which
is the shape it already knows how to turn into `__Ord_Float_<__`.  Run this
between the two and a constrained definition compiles to the same code the
hand-monomorphised one did.

**What is deliberately not specialised.**  A dictionary built at run time
— `__dict_Eq_List__ __dict_Eq_Int__`, the instance with a context — is an
application rather than a global, and a dictionary passed *through* from
the caller's own context is a variable.  Neither has one answer here, so
both are left as they are and the fragment still refuses them.  Ordinary
compiled code is unaffected either way: it can pass dictionaries, and the
originals stay in the program for it.

The pass is semantics-preserving and runs for every backend, not only the
audio one — a specialised copy is a call the G-machine no longer has to
route through a record.
"""

from __future__ import annotations

from dataclasses import replace

from .elaborate import _dict_sc_name
from .expr import (
    Expr, EAp, EGlobal, EVar, ELambda, ELet, ECase, map_children,
)
from .types import Predicate, Subst, TApp, TFun, TVar, Type

__all__ = ["specialise"]

#: How a specialised copy is named: the original, then one `#Class_Head`
#: per dictionary it was given.  Not the `__…__` shape the other generated
#: names use, because that shape is *parsed* — `audiograph._instance_head`
#: reads `__Num_Float_+__` as a method at `Float` — and a copy of a user's
#: definition is not an instance method.  `#` is safe in every backend:
#: `audiollvm._ident` already quotes names because origins contain one.
def _spec_name(name: str, dicts: list[str]) -> str:
    return name + "".join("#" + _dict_tag(d) for d in dicts)


def _dict_tag(dict_name: str) -> str:
    """`__dict_Ord_Float__` → `Ord_Float`."""
    return dict_name[len("__dict_"):-2]


def specialise(scs, givens_by_name, instances):
    """Add a dictionary-free copy of each constrained SC that is called
    with constant dictionaries, and point those calls at it.

    `givens_by_name` maps an SC's name to its declared context, in the
    order `elaborate` turned into parameters.  `instances` is the
    program's instance list, which is where a dictionary global's head
    type is read from.
    """
    heads = {_dict_sc_name(inst): inst.head_type for inst in instances}
    if not heads or not givens_by_name:
        return scs

    original = {str(name): (arity, lam, sig) for name, arity, lam, sig in scs}
    constrained = {
        name: givens
        for name, givens in givens_by_name.items()
        if givens and name in original
        and len(original[name][1].params) >= len(givens)
    }
    if not constrained:
        return scs

    #: `spec name → (arity, lam, sig)`, and the worklist of copies whose
    #: bodies have not been rewritten yet.  A copy is registered *before*
    #: its body is walked, so a recursive constrained function specialises
    #: to itself rather than forever.
    made: dict[str, tuple] = {}
    pending: list[str] = []
    #: Copies that cannot be made — an instantiation whose type does not
    #: come out concrete.  Remembered rather than re-attempted, because the
    #: attempt copies a whole body and the same call is met again on the
    #: way down through `map_children`.
    refused: set[str] = set()

    def copy_of(name: str, dicts: list[str]) -> str | None:
        """The specialised copy's name, making it if this is the first ask."""
        spec = _spec_name(name, dicts)
        if spec in made or spec in original:
            return spec
        if spec in refused:
            return None
        arity, lam, sig = original[name]
        k = len(dicts)
        spec_sig = _instantiate(sig, constrained[name][:k], dicts, heads)
        if spec_sig is None:
            refused.add(spec)
            return None
        bound = {str(p): EGlobal(d) for p, d in zip(lam.params[:k], dicts)}
        made[spec] = (arity - k,
                      replace(lam, params=list(lam.params[k:]),
                              body=_substitute(lam.body, bound)),
                      spec_sig)
        pending.append(spec)
        return spec

    def rewrite(e: Expr) -> Expr:
        head, nodes = _spine(e)
        if isinstance(head, EGlobal) and str(head.name) in constrained:
            name = str(head.name)
            k = len(constrained[name])
            if len(nodes) >= k and all(
                    isinstance(n.arg, EGlobal) and str(n.arg.name) in heads
                    for n in nodes[:k]):
                spec = copy_of(name, [str(n.arg.name) for n in nodes[:k]])
                if spec is not None:
                    return _apply(EGlobal(spec), nodes[k:], rewrite)
        return map_children(e, rewrite)

    out = [(name, arity, replace(lam, body=rewrite(lam.body)), sig)
           for name, arity, lam, sig in scs]

    # A copy's own body may call another constrained SC with what is now a
    # constant dictionary — that is the whole reason this is a worklist and
    # not a single sweep.
    while pending:
        spec = pending.pop()
        arity, lam, sig = made[spec]
        made[spec] = (arity, replace(lam, body=rewrite(lam.body)), sig)

    return out + [(spec, arity, lam, sig)
                  for spec, (arity, lam, sig) in made.items()]


# ── The pieces ───────────────────────────────────────────────────────────────


def _spine(e: Expr) -> tuple[Expr, list[EAp]]:
    """The head and the `EAp` nodes above it, outermost last.

    The nodes rather than the arguments, so `_apply` can put back the
    `discrete_arg` each one was built with rather than guessing it.
    """
    nodes: list[EAp] = []
    while isinstance(e, EAp):
        nodes.append(e)
        e = e.fn
    nodes.reverse()
    return e, nodes


def _apply(head: Expr, nodes: list[EAp], rewrite) -> Expr:
    for node in nodes:
        head = replace(node, fn=head, arg=rewrite(node.arg))
    return head


def _instantiate(sig, givens: list[Predicate], dicts: list[str],
                 heads: dict[str, Type]):
    """The copy's type: the original's, with the class variables settled.

    Each dictionary says what its constraint's type variable stands for —
    `Ord a` given `__dict_Ord_Float__` says `a` is `Float` — so matching
    the two pairwise is the whole substitution.  A copy with no type is no
    use to `audiograph`, which reads argument types off the signature, so a
    match that fails means no copy rather than an untyped one.
    """
    if sig is None:
        return None
    binding: dict[int, Type] = {}
    for pred, dict_name in zip(givens, dicts):
        head = heads.get(dict_name)
        if head is None or not _match(pred.type_, head, binding):
            return None
    if not binding:
        return sig
    return Subst(tuple(binding.items())).apply(sig)


def _match(pattern: Type, concrete: Type, binding: dict[int, Type]) -> bool:
    """One-way structural match, binding `pattern`'s variables.

    **Not `unify`**, and the difference is the point: a signature's
    variables are *rigid*, and `unify` refuses to bind one because a body
    may not decide what the caller's `a` is.  Here the caller has already
    decided — the dictionary at the call site *is* that decision — so this
    reads the answer off rather than inferring it.
    """
    if isinstance(pattern, TVar):
        seen = binding.get(pattern.id)
        if seen is not None:
            return seen == concrete
        binding[pattern.id] = concrete
        return True
    if isinstance(pattern, TApp) and isinstance(concrete, TApp):
        return (_match(pattern.fn, concrete.fn, binding)
                and _match(pattern.arg, concrete.arg, binding))
    if isinstance(pattern, TFun) and isinstance(concrete, TFun):
        return (pattern.mono == concrete.mono
                and _match(pattern.arg, concrete.arg, binding)
                and _match(pattern.ret, concrete.ret, binding))
    return pattern == concrete


def _substitute(e: Expr, bound: dict[str, Expr]) -> Expr:
    """Replace free `EVar`s named in `bound`, respecting inner binders.

    The names are `elaborate`'s own `_g0`, `_g1`, … so a collision needs a
    program that binds one of those itself — which is exactly the kind of
    thing that is true until it is not, and honouring the binders costs
    three cases.
    """
    if not bound:
        return e
    if isinstance(e, EVar):
        return bound.get(str(e.name), e)
    if isinstance(e, ELambda):
        inner = _without(bound, [str(p) for p in e.params])
        return replace(e, body=_substitute(e.body, inner))
    if isinstance(e, ELet):
        inner = _without(bound, [str(n) for n, _v in e.defs])
        # A `letrec`'s definitions see its own binders; a `let`'s do not.
        defs_scope = inner if e.is_rec else bound
        return replace(e,
                       defs=[(n, _substitute(v, defs_scope)) for n, v in e.defs],
                       body=_substitute(e.body, inner))
    if isinstance(e, ECase):
        return replace(
            e,
            scrut=_substitute(e.scrut, bound),
            alts=[replace(a, body=_substitute(
                a.body, _without(bound, [str(n) for n in a.names])))
                for a in e.alts])
    return map_children(e, lambda x: _substitute(x, bound))


def _without(bound: dict[str, Expr], names: list[str]) -> dict[str, Expr]:
    if not any(n in bound for n in names):
        return bound
    return {k: v for k, v in bound.items() if k not in names}
