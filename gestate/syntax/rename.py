"""Capture-avoiding renaming of free variables in the surface AST.

Two callers need the same walk.  `gestate/prelude.py` renames a shadowed
prelude binding and the references to it; `gestate/match.py` renames an
equation's pattern variables to the subjects the match compiler dispatches
on.  Both must respect binders — a lambda parameter of the same name shadows
the rename — which is what makes this more than a search-and-replace.

Only the binder-carrying forms are enumerated.  Everything else is walked
generically off its dataclass fields, so a node added to the AST later is
traversed without editing this file.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace

from .ast import (
    Pat, PAnnot, PCon, PList, PSigCons, PTuple, PVar,
    Val, VAlt, VCase, VFor, VFunc, VGfix, VGiven, VLet, VOpPhrase,
    VSCDecl, VSCEqn, VSig, VUnbox, VWord,
)


def pat_names(pat: Pat) -> frozenset[str]:
    """Every variable a pattern binds."""
    if isinstance(pat, PVar):
        return frozenset() if pat.name == "_" else frozenset([pat.name])
    if isinstance(pat, PCon):
        return frozenset().union(*(pat_names(a) for a in pat.args)) \
            if pat.args else frozenset()
    if isinstance(pat, PTuple):
        return frozenset().union(*(pat_names(i) for i in pat.items)) \
            if pat.items else frozenset()
    if isinstance(pat, PList):
        names = frozenset().union(*(pat_names(i) for i in pat.items)) \
            if pat.items else frozenset()
        return names | (pat_names(pat.tail) if pat.tail is not None
                        else frozenset())
    if isinstance(pat, PSigCons):
        return pat_names(pat.head) | pat_names(pat.tail)
    if isinstance(pat, PAnnot):
        return pat_names(pat.pat)
    return frozenset()


def _names_of(pats) -> frozenset[str]:
    out = frozenset()
    for p in pats:
        out |= pat_names(p)
    return out


def rename_free(node, renames: dict[str, str], bound: frozenset = frozenset()):
    """Rewrite free occurrences of ``renames``' keys in ``node``.

    ``bound`` is the set of binders already in scope; occurrences of a name
    in it are left alone, because they refer to the binder rather than to
    the thing being renamed.
    """
    if not renames:
        return node

    if isinstance(node, VWord):
        if node.value in renames and node.value not in bound:
            return VWord(renames[node.value], node.span)
        return node

    if isinstance(node, VSig):
        return (replace(node, name=renames[node.name])
                if node.name in renames else node)

    if isinstance(node, VSCDecl):
        return replace(node, name=renames.get(node.name, node.name),
                       equations=[rename_free(e, renames, bound)
                                  for e in node.equations])

    if isinstance(node, VSCEqn):
        inner = bound | _names_of(node.params) | frozenset(node.using_params)
        return replace(node, name=renames.get(node.name, node.name),
                       body=rename_free(node.body, renames, inner))

    if isinstance(node, VFunc):
        return replace(node, body=rename_free(node.body, renames,
                                              bound | _names_of(node.params)))

    if isinstance(node, (VLet, VGiven)):
        binders = frozenset(n for n, _ in node.bindings)
        rhs = bound | binders if getattr(node, "is_rec", False) else bound
        return replace(
            node,
            bindings=[(n, rename_free(v, renames, rhs)) for n, v in node.bindings],
            body=rename_free(node.body, renames, bound | binders),
        )

    if isinstance(node, VCase):
        return replace(node, scrut=rename_free(node.scrut, renames, bound),
                       alts=[rename_free(a, renames, bound) for a in node.alts])

    if isinstance(node, VAlt):
        return replace(node, body=rename_free(node.body, renames,
                                              bound | pat_names(node.pat)))

    if isinstance(node, VFor):
        binders = _names_of([p for p, _ in node.bindings])
        return replace(
            node,
            bindings=[(p, rename_free(v, renames, bound))
                      for p, v in node.bindings],
            body=rename_free(node.body, renames, bound | binders),
        )

    if isinstance(node, VUnbox):
        return replace(node, binding=rename_free(node.binding, renames, bound),
                       body=rename_free(node.body, renames,
                                        bound | pat_names(node.pat)))

    if isinstance(node, VGfix):
        return replace(node, body=rename_free(node.body, renames,
                                              bound | {node.var}))

    if isinstance(node, VOpPhrase):
        # `atoms` interleaves operands with operator *strings*; only the
        # operands are expressions.
        return replace(node, atoms=[
            rename_free(a, renames, bound) if isinstance(a, Val) else a
            for a in node.atoms
        ])

    if not is_dataclass(node):
        return node
    changes = {}
    for fld in fields(node):
        v = getattr(node, fld.name)
        if isinstance(v, Val):
            changes[fld.name] = rename_free(v, renames, bound)
        elif isinstance(v, list) and v and all(isinstance(x, Val) for x in v):
            changes[fld.name] = [rename_free(x, renames, bound) for x in v]
    return replace(node, **changes) if changes else node
