"""Lambda lifting -- `ELambda` -> closed supercombinators.

Implements the algorithm of "Simple Lambda Lifting: Formalisation In
Lean and a new efficient algorithm" (see `spec/supercomb.md`).

    EP   := Map Function (Set Variable)    -- extra params needed per fn
    work := Stack (Function, Variable)

The lifter takes the parser's output -- a list of
`(name: str, arity, ELambda(params, body))` triples -- and produces a
list of `(Name, Arity, ELambda)` triples with no NESTED `ELambda`
(an outer wrapping `ELambda` carries each SC's frame parameters).
Each nested lambda becomes a fresh `(int_id, frame_arity,
ELambda(frame_params, lifted_body))` supercombinator, and the original
lift-site is rewritten into an `EAp`/`EGlobal(int_id)` chain that
supplies the captured free variables as additional (innermost-applied)
arguments.

Entry-of-SC stack / frame ordering:

  * For a source SC ``K p_0 .. p_{m-1} = body`` the source parameter
    list is ``p_0 .. p_{m-1}`` in source order; ``p_i`` is the (i+1)-th
    applied arg (caller's source applies them left-to-right), so at SC
    entry ``p_i`` lives behind the i-th ``NAp`` -> ``PushArg i``.  The
    frame is ``own_params`` (= source order), and the G-machine
    compiler assigns ``params[i] -> Arg i`` directly.

  * For a lifted SC the frame is ``extras ++ own_params``: extras are
    the lambda's captured free vars, applied INNERMOST by the lift-site
    rewrite, so they occupy ``Arg 0..`` at SC entry; the caller then
    wraps own_args OUTER-applied (caller's ``f q`` becomes
    ``(partial_with_extras) q`` -> ``q`` lives at the deepest Arg
    index = ``Arg k``).  Hence own_params sit at the tail of the frame
    list, mapped to ``Arg k..k+m-1``.

Naming/indexing convention (matches `spec/supercomb.md`).

  * Every lifted SC gets a fresh ``int`` id, distinct from every
    source-named global (``str``).  These int ids appear only as the
    ``EGlobal`` payloads at lift-sites and as the canonical ``Name`` of
    the lifted SC itself; they never appear as a binder name inside
    any body.  Lifted SC own_params reuse the original lambda's source
    parameter names (which are ``str``s); extras are likewise ``str``
    names visible from the lift-site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .expr import (
    Alter,
    EAnnot,
    EAp,
    EBox,
    ECase,
    EAppEx,
    EAppFa,
    EChan,
    ECon,
    EDelay,
    EFix,
    EFor,
    EGFix,
    EGlobal,
    EHole,
    ELambda,
    ELet,
    ENever,
    EChr,
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
)

__all__ = ["lift", "LiftError"]


class LiftError(Exception):
    pass


# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

class _LiftSite:
    """Marker placed at a lift-site during `_walk`; replaces the original
    `ELambda` in the in-progress body.  `_reify` later rewrites it into
    an `EAp`/`EGlobal(child_id)` chain supplying `child`'s extras.
    """
    __slots__ = ("child",)

    def __init__(self, child):
        self.child = child


@dataclass
class Func:
    """A function under consideration: either a source SC (``kind='sc'``,
    identified by its ``str`` name) or a lifted lambda (``kind='anon'``,
    identified by its fresh ``int`` id).
    """
    id: Name                # str for source SCs, int for lifted SCs
    kind: str               # 'sc' or 'anon'
    own_params: list[Name]  # the lambda's own parameter names (source order)
    outer: tuple[Name, ...]  # ancestor binders visible from this fn body
    parent: Optional[Name]
    body: object            # walked body (with `_LiftSite` markers), or None
    fv: set = field(default_factory=set)    # captured vars (subset of `outer`)
    ep: set = field(default_factory=set)    # extras (= fv after propagation)


class Lifter:

    def __init__(self):
        self._fresh_anon = 0
        self._func: dict[Name, Func] = {}
        # `decl[func_id]` is the set of binders that Func's body
        # textually introduces -- own_params, `let` def binders, `case`
        # alt field binders, and the binders of `gfix`/`for`/`unbox`.
        # The EP work-list uses this to skip adding `name` to a Func's
        # extras when that same Func already declares `name` locally (it
        # has direct scope access).  It is keyed by Func rather than by
        # name because the same binder name legitimately occurs in
        # several Funcs -- the ϕ/δ transform, for one, emits two copies
        # of every SC body -- and a name-keyed map would let the last
        # copy walked decide for all of them.
        self._decl: dict[Name, set[Name]] = {}
        # call edges: for each func id, the set of func ids that textually
        # contain a lift-site for it (its `references` per the algorithm).
        self._refs: dict[Name, set] = {}

    # -- helpers -----------------------------------------------------------

    def _new_func(self, kind, own_params, outer, parent):
        fid = self._fresh_anon
        self._fresh_anon += 1
        f = Func(id=fid, kind=kind, own_params=list(own_params),
                 outer=tuple(outer), parent=parent,
                 body=None)
        self._func[fid] = f
        self._refs[fid] = set()
        self._decl[fid] = set(own_params)
        return f

    # -- stage 1: walk the source program ---------------------------------
    #
    # `local` is the list of binder names visible at the current Expr
    # node INSIDE this function body (own_params + let/case binders
    # introduced above).  `outer` is the set of further ancestor
    # binders visible from this function (a snapshot taken when this
    # Func was created).  EVar names in `outer` are "free" -- recorded
    # in `cur.fv`.  EVar names in `local` are local.  Every `ELambda`
    # becomes a child Func; the original lambda is replaced by a
    # `_LiftSite(child.id)` marker.

    def _make_sc(self, sname, arity, wrapped):
        if not isinstance(wrapped, ELambda) or len(wrapped.params) != arity:
            raise LiftError(
                f"SC {sname!r}: expected an ELambda with {arity} params")
        own_params = list(wrapped.params)
        f = Func(id=sname, kind="sc", own_params=own_params,
                 outer=(), parent=None,
                 body=None)
        self._func[sname] = f
        self._refs[sname] = set()
        self._decl[sname] = set(own_params)
        f.body = self._walk(wrapped.body, list(own_params), (), f)
        return f

    def _walk(self, e: Expr, local: list[Name], outer: tuple[Name, ...],
              cur: Func) -> Expr:
        if isinstance(e, EVar):
            if e.name in local:
                return EVar(e.name)
            if e.name in outer:
                cur.fv.add(e.name)
                return EVar(e.name)
            # Should not happen: the parser resolves unbound names to
            # EGlobal, so an EVar should always be bound by something
            # in `local` or `outer` exactly when we are within the
            # binding scope.
            raise LiftError(
                f"unbound EVar {e.name!r} inside {cur.id!r}")
        if isinstance(e, ENum):
            return ENum(e.n)
        if isinstance(e, EHole):
            # Carried through so the *compiler* is the one that refuses it,
            # with the position and the reason — see `gmachine.compile_c`.
            return e
        if isinstance(e, EChr):
            return EChr(e.n)
        if isinstance(e, EGlobal):
            return EGlobal(e.name)
        if isinstance(e, ECon):
            return ECon(e.tag,
                        [self._walk(a, local, outer, cur) for a in e.args])
        if isinstance(e, ETuple):
            return ETuple([self._walk(a, local, outer, cur) for a in e.args])
        if isinstance(e, EProj):
            # `EProj i` carries no binders and references no vars; it
            # is always inside `EAp (EProj i) tup`, and the `EAp` walk
            # is responsible for chasing `_LiftSite` markers in `tup`.
            return EProj(e.i, e.width)
        if isinstance(e, EAnnot):
            return EAnnot(self._walk(e.expr, local, outer, cur), e.type_)
        if isinstance(e, ENever):
            return ENever()
        if isinstance(e, EChan):
            return e   # carries its inferred element type; keep the node
        if isinstance(e, ESigCons):
            return ESigCons(self._walk(e.value, local, outer, cur),
                            self._walk(e.tail, local, outer, cur))
        if isinstance(e, ESigHead):
            return ESigHead(self._walk(e.sig, local, outer, cur))
        if isinstance(e, EDelay):
            return EDelay(self._walk(e.body, local, outer, cur))
        if isinstance(e, EAppFa):
            return EAppFa(self._walk(e.fn, local, outer, cur),
                          self._walk(e.arg, local, outer, cur))
        if isinstance(e, EAppEx):
            return EAppEx(self._walk(e.fn, local, outer, cur),
                          self._walk(e.arg, local, outer, cur))
        if isinstance(e, EWait):
            return EWait(self._walk(e.chan, local, outer, cur))
        if isinstance(e, EWatch):
            return EWatch(self._walk(e.sig, local, outer, cur))
        if isinstance(e, ESync):
            return ESync(self._walk(e.left, local, outer, cur),
                         self._walk(e.right, local, outer, cur))
        if isinstance(e, ETail):
            return ETail(self._walk(e.sig, local, outer, cur))
        if isinstance(e, EGFix):
            self._decl[cur.id].add(e.var)
            return EGFix(e.var, self._walk(e.body, [e.var] + local, outer, cur))
        if isinstance(e, EFix):
            return EFix(self._walk(e.body, local, outer, cur))
        if isinstance(e, EFor):
            self._decl[cur.id].add(e.var)
            return EFor(e.var,
                        self._walk(e.set_expr, local, outer, cur),
                        self._walk(e.body, [e.var] + local, outer, cur))
        if isinstance(e, EBox):
            return EBox(self._walk(e.body, local, outer, cur))
        if isinstance(e, EUnbox):
            self._decl[cur.id].add(e.var)
            return EUnbox(e.var,
                          self._walk(e.binding, local, outer, cur),
                          self._walk(e.body, [e.var] + local, outer, cur))
        if isinstance(e, ESet):
            return ESet([self._walk(a, local, outer, cur) for a in e.items])
        if isinstance(e, EAp):
            return EAp(self._walk(e.fn, local, outer, cur),
                       self._walk(e.arg, local, outer, cur))
        if isinstance(e, ELet):
            names = [n for (n, _) in e.defs]
            # Local let-binders are declared by `cur`.
            self._decl[cur.id].update(names)
            if e.is_rec:
                # All binders visible to each def AND the body.
                new_local = list(local) + list(names)
                defs_w = [(n, self._walk(d, new_local, outer, cur))
                          for (n, d) in e.defs]
                body_w = self._walk(e.body, new_local, outer, cur)
            else:
                # Each def sees only outer + previously-bound defs.
                defs_w = []
                scope_now = list(local)
                for (n, d) in e.defs:
                    defs_w.append((n, self._walk(d, scope_now, outer, cur)))
                    scope_now = scope_now + [n]
                body_w = self._walk(e.body, scope_now, outer, cur)
            return ELet(e.is_rec, defs_w, body_w)
        if isinstance(e, ECase):
            # Local alt field-binders are declared by `cur`.
            for alt in e.alts:
                self._decl[cur.id].update(alt.names)
            scrut_w = self._walk(e.scrut, local, outer, cur)
            alts_w = []
            for alt in e.alts:
                new_local = list(local) + list(alt.names)
                body_w = self._walk(alt.body, new_local, outer, cur)
                alts_w.append(Alter(alt.tag, list(alt.names), body_w))
            return ECase(scrut_w, alts_w)
        if isinstance(e, ELambda):
            # New anon function.  Its own outer = the union of the
            # current `local` and `outer` -- every binder visible at
            # the lift-site is visible from inside the lambda body
            # (minus the lambda's own params, which become its local).
            child_outer = tuple(local) + outer
            child = self._new_func("anon", list(e.params),
                                   outer=child_outer, parent=cur.id)
            child.body = self._walk(e.body, list(e.params),
                                    child_outer, child)
            self._refs[child.id].add(cur.id)
            return _LiftSite(child.id)
        raise LiftError(f"cannot walk {e!r}")

    # -- stage 2: EP propagation ------------------------------------------

    def _propagate(self):
        ep = {fid: set(f.fv) for fid, f in self._func.items()}
        work = []
        for fid, f in self._func.items():
            for v in f.fv:
                work.append((fid, v))
        # We need `decl[v]` = the Func id that declares (binds) `v`.
        # A name is "declared" by the ancestor Func whose own_params or
        # outer-list contains it.  We approximate by scanning all Funcs
        # for an ancestor of `f` (along parent links) whose frame
        # (own_params ++ outer-tuple) contains v; if none, the name is
        # declared by some outer scope we can't reach (treat as
        # "nobody", i.e. propagate unconditionally).
        while work:
            (f, v) = work.pop()
            for g in self._refs.get(f, ()):
                if v in self._decl.get(g, ()) or v in ep[g]:
                    continue
                ep[g].add(v)
                work.append((g, v))
        for fid, extras in ep.items():
            self._func[fid].ep = extras

    def _declares(self, fid, v) -> bool:
        """True if Func `fid`'s own_params bind the name `v`."""
        f = self._func[fid]
        return v in f.own_params

    # -- stage 3: reify -> ELambda-wrapped bodies --------------------------

    def _extras_sorted(self, f: Func) -> list[Name]:
        """Extras in a deterministic order (alphabetical for str).  A
        lifted SC's frame and its lift-site rewrite must agree on
        extras order; this function is the single source of truth.
        """
        return sorted(f.ep, key=lambda n: (str(type(n).__name__), n))

    def _frame(self, f: Func) -> list[Name]:
        """Frame binders (Arg-index order): extras ++ own_params.

        `frame[i] -> Arg i` (i.e. PushArg i) at SC entry.  extras are
        applied innermost by the lift-site rewrite (becoming ``a_0..``);
        the caller wraps own_args outermost (becoming ``a_k..``).
        """
        return self._extras_sorted(f) + list(f.own_params)

    def _reify(self, node, scope_names: list[Name],
               frame: list[Name], cur: Func) -> Expr:
        """Rewrite the walked node into the final `Expr`.

        - `_LiftSite` becomes an `EAp`-chain around `EGlobal(child.id)`
          applying the child's extras (in `_extras_sorted(child)`
          order), each referencing the corresponding name visible in
          `scope_names`.  The caller's own_args are not part of this
          rewrite (they live in the caller's source code).
        - `EVar`, `ENum`, `ECon`, `EAp`, `EGlobal` are returned
          verbatim (already named).
        - `ELet` and `ECase` recurse, extending `scope_names` with
          the new binders so that downstream lift-sites can capture
          local let/case names too.

        `frame` is the current Func's frame_params list (kept for
        consistency with `_frame`; reify doesn't otherwise need it
        because all references are by name).
        """
        if isinstance(node, _LiftSite):
            child = self._func[node.child]
            extras = self._extras_sorted(child)
            acc: Expr = EGlobal(child.id)
            for name in extras:
                acc = EAp(acc, EVar(name))
            return acc
        if isinstance(node, (EVar, ENum, EChr, EGlobal, EHole)):
            return node
        if isinstance(node, ECon):
            return ECon(node.tag,
                        [self._reify(a, scope_names, frame, cur)
                         for a in node.args])
        if isinstance(node, ETuple):
            return ETuple([self._reify(a, scope_names, frame, cur)
                           for a in node.args])
        if isinstance(node, EProj):
            return EProj(node.i, node.width)
        if isinstance(node, EAnnot):
            return EAnnot(self._reify(node.expr, scope_names, frame, cur), node.type_)
        if isinstance(node, ENever):
            return ENever()
        if isinstance(node, EChan):
            return node
        if isinstance(node, ESigCons):
            return ESigCons(self._reify(node.value, scope_names, frame, cur),
                            self._reify(node.tail, scope_names, frame, cur))
        if isinstance(node, ESigHead):
            return ESigHead(self._reify(node.sig, scope_names, frame, cur))
        if isinstance(node, EDelay):
            return EDelay(self._reify(node.body, scope_names, frame, cur))
        if isinstance(node, EAppFa):
            return EAppFa(self._reify(node.fn, scope_names, frame, cur),
                          self._reify(node.arg, scope_names, frame, cur))
        if isinstance(node, EAppEx):
            return EAppEx(self._reify(node.fn, scope_names, frame, cur),
                          self._reify(node.arg, scope_names, frame, cur))
        if isinstance(node, EWait):
            return EWait(self._reify(node.chan, scope_names, frame, cur))
        if isinstance(node, EWatch):
            return EWatch(self._reify(node.sig, scope_names, frame, cur))
        if isinstance(node, ESync):
            return ESync(self._reify(node.left, scope_names, frame, cur),
                         self._reify(node.right, scope_names, frame, cur))
        if isinstance(node, ETail):
            return ETail(self._reify(node.sig, scope_names, frame, cur))
        if isinstance(node, EGFix):
            return EGFix(node.var, self._reify(node.body, [node.var] + scope_names, frame, cur))
        if isinstance(node, EFix):
            return EFix(self._reify(node.body, scope_names, frame, cur))
        if isinstance(node, EFor):
            return EFor(node.var,
                        self._reify(node.set_expr, scope_names, frame, cur),
                        self._reify(node.body, [node.var] + scope_names, frame, cur))
        if isinstance(node, EBox):
            return EBox(self._reify(node.body, scope_names, frame, cur))
        if isinstance(node, EUnbox):
            return EUnbox(node.var,
                          self._reify(node.binding, scope_names, frame, cur),
                          self._reify(node.body, [node.var] + scope_names, frame, cur))
        if isinstance(node, ESet):
            return ESet([self._reify(a, scope_names, frame, cur) for a in node.items])
        if isinstance(node, EAp):
            return EAp(self._reify(node.fn, scope_names, frame, cur),
                       self._reify(node.arg, scope_names, frame, cur))
        if isinstance(node, ELet):
            if node.is_rec:
                new_scope = list(scope_names) + [n for (n, _) in node.defs]
                defs = [(n, self._reify(d, new_scope, frame, cur))
                        for (n, d) in node.defs]
                body = self._reify(node.body, new_scope, frame, cur)
            else:
                defs = []
                cur_scope = list(scope_names)
                for (n, d) in node.defs:
                    defs.append((n, self._reify(d, cur_scope, frame, cur)))
                    cur_scope = cur_scope + [n]
                body = self._reify(node.body, cur_scope, frame, cur)
            return ELet(node.is_rec, defs, body)
        if isinstance(node, ECase):
            scrut = self._reify(node.scrut, scope_names, frame, cur)
            alts = []
            for alt in node.alts:
                new_scope = list(scope_names) + list(alt.names)
                b = self._reify(alt.body, new_scope, frame, cur)
                alts.append(Alter(alt.tag, list(alt.names), b))
            return ECase(scrut, alts)
        raise LiftError(f"cannot reify {node!r}")

    # -- driver -----------------------------------------------------------

    def lift(self, sc_in):
        sc_funcs = [self._make_sc(sname, arity, wrapped)
                    for (sname, arity, wrapped) in sc_in]
        self._propagate()
        out = []
        for f in sc_funcs:
            frame = self._frame(f)
            body = self._reify(f.body, list(f.own_params), frame, f)
            out.append((f.id, len(frame), ELambda(list(frame), body)))
        for fid, f in self._func.items():
            if f.kind != "anon":
                continue
            frame = self._frame(f)
            body = self._reify(f.body, list(f.own_params), frame, f)
            out.append((fid, len(frame), ELambda(list(frame), body)))
        return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def lift(sc_in):
    """Lift a parsed program into a closed set of supercombinators.

    `sc_in` is the parser's output: a list of
    `(name: str, arity, ELambda(params, body))` triples.  Returns a
    list of `(Name, Arity, ELambda)` triples with no nested `ELambda`
    anywhere; nested lambdas appear as additional
    `(int_id, frame_arity, ELambda(frame_params, lifted_body))`
    supercombinators appended after the source SCs.  Each Elambda wraps
    its SC's `frame_params`.
    """
    return Lifter().lift(sc_in)