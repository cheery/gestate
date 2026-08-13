"""Type representation for the type system.

    Type := TVar(id)           -- type metavariable (fresh during inference)
          | TCon(name)         -- named type constructor (Int, Bool, etc.)
          | TFun(arg, ret)     -- function type  A -> B
          | TApp(fn, arg)      -- type application
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, eq=True)
class TVar:
    """A type variable.  ``id`` is a unique integer from a fresh-name supply.

    ``rigid`` distinguishes the two kinds.  A *metavariable* (the default)
    is a hole inference may fill: unification binds it.  A **rigid**
    variable is a signature's skolem — `spec/types.md` §3 — and stands for
    "whatever type the caller picks", so unification must refuse to bind
    it.  Without that, `f : a -> Int ; f x = x + 1` type-checks by
    unifying `a` with `Int`, which is the one place the checker accepted an
    ill-typed program (`fixme.md` F36).

    Rigidity is a property of the *occurrence*, not of the variable's
    identity: a use site instantiates the signature's quantified variables
    with fresh metavariables of new ids, and it is the id that says which
    variable this is.  Hence ``compare=False`` — the same as ``span``.

    ``name`` is the name the signature gave it, kept for error messages
    only, so a rejection can say `a` rather than `a-1003`.
    """
    id: int
    span: object = field(default=None, compare=False)
    rigid: bool = field(default=False, compare=False)
    name: str | None = field(default=None, compare=False)

    def __repr__(self):
        return f"a{self.id}"


@dataclass(frozen=True, eq=True)
class TCon:
    """A named type constructor: ``Int``, ``Bool``, ``String``, etc."""
    name: str
    span: object = field(default=None, compare=False)

    def __repr__(self):
        return self.name


@dataclass(frozen=True, eq=True)
class TFun:
    """Function type.

    ``mono`` picks the arrow.  ``A ~> B`` (``mono=True``) is Datafun's
    function space: the argument is a *monotone* variable, and the
    function must respect the ordering on ``A``.  ``A -> B``
    (``mono=False``, the default) is Datafun's ``□A → B``: the argument is
    *discrete* and may be used any way at all.

    The two coincide whenever ``A`` carries the discrete order — see
    `has_nontrivial_order` — which is why ordinary code never has to think
    about the distinction.  Both compile to the same thing; §I.3 notes the
    monotone/discrete split is "purely a compile-time typing discipline,
    invisible past ϕ/δ".
    """
    arg: Type
    ret: Type
    span: object = field(default=None, compare=False)
    mono: bool = False

    def __repr__(self):
        return f"({self.arg} {'~>' if self.mono else '->'} {self.ret})"


@dataclass(frozen=True, eq=True)
class TApp:
    """Type application: ``TCon Maybe`` applied to ``TCon Int``."""
    fn: Type
    arg: Type
    span: object = field(default=None, compare=False)

    def __repr__(self):
        return f"({self.fn} {self.arg})"


@dataclass(frozen=True, eq=True)
class TInt:
    """A type-level integer: ``12`` in ``Cyclic 12``."""
    n: int
    span: object = field(default=None, compare=False)

    def __repr__(self):
        return str(self.n)


Type = TVar | TCon | TFun | TApp | TInt


# ---------------------------------------------------------------------------
# Substitutions
# ---------------------------------------------------------------------------

class _SubstBase:
    """What every substitution can do: resolve a type through its bindings.

    Two subclasses differ only in how a binding is *added*.  `Subst` is
    persistent, which is what `constraint.py` and the ADT instantiation in
    `infer.py` want.  `Unifier` is destructive, which is what inference
    wants; see its docstring.
    """

    __slots__ = ("_map",)

    def lookup(self, var_id: int) -> Optional[Type]:
        return self._map.get(var_id)

    def apply(self, t: Type) -> Type:
        if not self._map:
            return t
        if isinstance(t, TVar):
            return self._apply_var(t)
        if isinstance(t, (TCon, TInt)):
            return t
        # Rebuilt only when a part actually changed.  Most types a
        # substitution meets are ground or mention none of its variables,
        # and `compose` applies one substitution across the whole of
        # another, so the no-op case is the common one — returning `t`
        # itself keeps it free instead of allocating an equal copy.
        if isinstance(t, TFun):
            arg, ret = self.apply(t.arg), self.apply(t.ret)
            if arg is t.arg and ret is t.ret:
                return t
            return TFun(arg, ret, t.span, t.mono)
        if isinstance(t, TApp):
            # Carrying the span matters: `unify` reads it off the types it
            # is handed to say *where* a mismatch came from, and dropping it
            # here severed that at the first substitution (`fixme.md` F31).
            fn, arg = self.apply(t.fn), self.apply(t.arg)
            if fn is t.fn and arg is t.arg:
                return t
            return TApp(fn, arg, t.span)
        return t

    def _apply_var(self, t: TVar) -> Type:
        """Follow a variable's binding chain to its representative.

        Iterative and cycle-guarded: composition can leave `α ↦ β, β ↦ α`
        behind, and then either variable is an equally good representative
        of the class — but chasing the chain recursively would not stop.
        """
        seen: set[int] | None = None
        cur = t
        m = self._map
        while True:
            found = m.get(cur.id)
            if found is None:
                return cur
            if not isinstance(found, TVar):
                return self.apply(found)
            if found.id == cur.id:
                return cur
            if seen is None:
                seen = {cur.id}
            elif found.id in seen:
                return cur
            seen.add(found.id)
            cur = found

    def __bool__(self):
        return len(self._map) > 0


class Subst(_SubstBase):
    """An immutable substitution mapping metavariable ids to types.

    Backed by a `dict`, not an association list (`fixme.md` F75).  The
    difference is not a micro-optimisation: `lookup` runs in the innermost
    loop of inference, and against a list it costs the *size of the
    substitution*, which itself grows with the program.  Two growing
    factors multiplied is what made compiling a 512-note melody take fifty
    seconds.

    The values are never mutated after construction — `extend` and
    `compose` each build a new dict — so this stays a persistent structure.
    """

    __slots__ = ()

    _empty: Optional[Subst] = None

    def __init__(self, pairs=()):
        if type(pairs) is dict:
            self._map: dict[int, Type] = pairs      # trusted, built here
        else:
            # An iterable of pairs, as `test/test_types.py` writes them.
            # Reversed because the list form resolved a repeated key to its
            # *first* entry, and a dict keeps the last one written.
            self._map = dict(reversed(list(pairs)))

    def __repr__(self):
        return f"Subst({sorted(self._map.items())!r})"

    def __eq__(self, other):
        return isinstance(other, Subst) and self._map == other._map

    @staticmethod
    def empty() -> _SubstBase:
        """The identity substitution — or the run's `Unifier`, if one is up.

        Inference asks for `Subst.empty()` at every leaf and at the start of
        every `unify`, then composes the results back together.  Inside an
        `unifying()` scope those are all the *same* destructive store, so
        the composing is already done and the threading costs nothing.
        """
        current = getattr(_CURRENT, "unifier", None)
        return current if current is not None else Subst._empty

    def extend(self, var_id: int, t: Type) -> Subst:
        # `α ↦ α` carries no information and makes `apply` diverge.
        # `compose` produces one whenever the two substitutions unify the
        # same pair of variables from opposite sides: `{17 ↦ β}` composed
        # with `{β ↦ 17}` maps 17 to itself.
        if isinstance(t, TVar) and t.id == var_id:
            return self
        m = dict(self._map)
        m[var_id] = t
        return Subst(m)

    def compose(self, other: Subst) -> Subst:
        """``self ∘ other`` — `self`'s bindings, seen through `other`.

        One dict built in a single pass.  The association-list version
        re-extended `other` once per binding of `self`, so composing cost
        the *product* of the two sizes; it is now the sum.
        """
        if not self._map:
            return other
        if not other._map:
            # `self`'s bindings were α↦α-filtered as they were added, and
            # applying an empty substitution changes none of them.
            return self
        m = dict(other._map)
        for k, v in self._map.items():
            nv = other.apply(v)
            # Same filter `extend` applies.  Skipping rather than deleting
            # is deliberate: it leaves `other`'s binding for `k` in place,
            # which is what re-extending `other` used to do.
            if isinstance(nv, TVar) and nv.id == k:
                continue
            m[k] = nv
        return Subst(m)


Subst._empty = Subst()


class Unifier(_SubstBase):
    """A destructive substitution: one store, mutated in place.

    The persistent `Subst` is still asymptotically wrong for inference, and
    fixing `lookup` did not change that (`fixme.md` F78).  Two costs remain
    and neither is about lookup:

    * `extend` copies the whole dict, so binding the k-th variable costs k.
    * Threading forces the environment and the constraint list to be
      *rebuilt* whenever the substitution grows — `_apply_subst_env` and
      `_apply_subst_constraints` — because a scheme already handed out
      holds types the new binding refines.

    Both vanish if there is only ever one substitution.  Binding a variable
    is then a dict store, composition is a no-op, and nothing needs
    rebuilding because every type resolves through the same store whenever
    it is next read.  This is the standard union-find formulation of
    Hindley–Milner; the functional threading in `infer.py` is left in place
    and simply becomes free, since every `Subst.empty()` inside the scope
    returns *this* object.

    Sound here because inference never backtracks: there is no `except
    UnifyError` in `infer.py`, no speculative branch, and no substitution
    that is built and then discarded.  Every one of them is composed
    forward, so aliasing them to one store reaches the same fixed point.
    """

    __slots__ = ()

    def __init__(self):
        self._map: dict[int, Type] = {}

    def __repr__(self):
        return f"Unifier({len(self._map)} bindings)"

    def extend(self, var_id: int, t: Type) -> "Unifier":
        # `α ↦ α` carries no information and makes `apply` diverge.
        if isinstance(t, TVar) and t.id == var_id:
            return self
        self._map[var_id] = t
        return self

    def _apply_var(self, t: TVar) -> Type:
        """As the base class, but the chain is flattened on the way out.

        Path compression, which a persistent substitution cannot do: after
        following `α ↦ β ↦ γ ↦ Int` once, all three point straight at `Int`
        and the next lookup is a single step.  Without it the chains grow
        with the program — 70,000 of these calls on a 1,024-note score were
        walking about twenty links each.

        Storing a *resolved* type is safe even though the store may still
        grow: `apply` recurses into what it finds, so a binding that is
        only partly resolved when written is finished off when read.
        """
        m = self._map
        first = m.get(t.id)
        if first is None:
            return t
        if not isinstance(first, TVar):
            rep = self.apply(first)
            if rep is not first:
                m[t.id] = rep
            return rep

        path: list[int] = [t.id]
        seen: set[int] | None = None
        cur = first
        while True:
            found = m.get(cur.id)
            if found is None:
                rep: Type = cur
                break
            if not isinstance(found, TVar):
                rep = self.apply(found)
                break
            if found.id == cur.id:
                rep = cur
                break
            if seen is None:
                seen = {t.id, cur.id}
            elif found.id in seen:
                # `α ↦ β, β ↦ α`: either is an equally good representative,
                # and rewriting the path would make one point at itself.
                return cur
            seen.add(found.id)
            path.append(cur.id)
            cur = found

        for vid in path:
            if not (isinstance(rep, TVar) and rep.id == vid):
                m[vid] = rep
        return rep

    def compose(self, other: _SubstBase) -> "Unifier":
        """Already done.

        `other` is this same store whenever it came from `Subst.empty()`,
        which is where every substitution inference builds starts.  A
        genuinely separate `Subst` — the ADT instantiation in `infer.py`
        builds one — is absorbed instead, which is what composing meant.
        """
        if other is self:
            return self
        for k, v in other._map.items():
            self.extend(k, v)
        return self


#: The store in force, if inference is running.  A module global because
#: `Subst.empty()` is called from three modules and forty places, none of
#: which have anywhere to thread a store from; inference is single-threaded
#: and the scope below saves and restores, so nesting is safe.
# **Per thread, and that is a fix, not a nicety.**  As a module global
# this poisoned itself: the workbench runs inference on build threads
# (`audioeditor.apply`, `audiolive`'s watcher) while the loop thread
# answers `fits`, and when two threads' `unifying()` scopes overlapped,
# the later exit restored the *other thread's* store — permanently, so
# every `Subst.empty()` in the process answered with a dead `Unifier`.
# Reproduced 2026-08-13, and the likely cause of the run-to-run rigid-
# variable failures a same-text rebuild could never explain (F103).
_CURRENT = threading.local()


@contextmanager
def unifying():
    """Make inference destructive for the duration.

    Scoped rather than global because metavariable ids restart with each
    `Fresh()`, and there are two inference entry points — `infer_program`
    and `infer_instance_method` — whose variables must not be confused.
    Scoped *per thread* because inference runs on build threads while the
    session thread typechecks palette queries, and neither may see — or
    worse, restore — the other's store.
    """
    previous = getattr(_CURRENT, "unifier", None)
    _CURRENT.unifier = Unifier()
    try:
        yield _CURRENT.unifier
    finally:
        _CURRENT.unifier = previous


# ---------------------------------------------------------------------------
# Free variables
# ---------------------------------------------------------------------------

def free_vars(t: Type) -> set[int]:
    if isinstance(t, TVar):
        return {t.id}
    if isinstance(t, (TCon, TInt)):
        return set()
    if isinstance(t, TFun):
        return free_vars(t.arg) | free_vars(t.ret)
    if isinstance(t, TApp):
        return free_vars(t.fn) | free_vars(t.arg)
    return set()


# ---------------------------------------------------------------------------
# Type schemes (polymorphism)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Scheme:
    """A polymorphic type scheme: ``forall vars. constraints => type_``.

    ``constraints`` is an ordered tuple, not a set: the order is the one
    written in the signature, and elaboration passes one dictionary
    argument per constraint in exactly that order.
    """
    vars: frozenset[int]
    constraints: tuple[Predicate, ...] = ()
    type_: Type | None = None  # set below by __init__ hack, see post_init

    def __init__(self, vars, type_, constraints=()):
        object.__setattr__(self, 'vars', vars)
        object.__setattr__(self, 'constraints', _dedup(constraints))
        object.__setattr__(self, 'type_', type_)

    def __repr__(self):
        cs = ', '.join(str(c) for c in sorted(self.constraints, key=str)) if self.constraints else ''
        vlist = ', '.join(f'a{v}' for v in sorted(self.vars)) if self.vars else ''
        parts = []
        if vlist: parts.append(f"forall {vlist}")
        if cs: parts.append(f"({cs})")
        parts.append(str(self.type_))
        return ' '.join(parts) if len(parts) > 1 else parts[0]


def scheme_free_vars(s: Scheme) -> set[int]:
    """Free type variables of a scheme (those NOT quantified).

    **Memoised on the scheme**, which is what makes a large prelude
    affordable.  `generalize` asks this of *every* binding in the
    environment, so the work is quadratic in the number of definitions in
    scope: compiling one synth against `prelude.ges` + `audio.ges` +
    `synth.ges` made 36,000 of these calls and 225,000 recursive
    `free_vars` calls underneath them, a fifth of the whole compile.

    Safe because a `Scheme` is frozen and a `Type` is built from frozen
    dataclasses: the answer cannot go stale, because the value it is about
    cannot change.  Substitution builds *new* schemes rather than editing
    one, which is exactly the property this relies on.

    A copy is returned rather than the memo, because callers do `fvs |=`
    and one of them doing `fvs = scheme_free_vars(s)` first would poison
    the cache.
    """
    fvs = s.__dict__.get("_fvs")
    if fvs is None:
        fvs = free_vars(s.type_) - s.vars
        object.__setattr__(s, "_fvs", fvs)
    return set(fvs)


def _dedup(preds) -> tuple:
    """Order-preserving de-duplication of a constraint list."""
    out: list = []
    for p in preds:
        if p not in out:
            out.append(p)
    return tuple(out)


def scheme_mono(t: Type) -> Scheme:
    """Wrap a monomorphic type as a scheme with no quantifiers."""
    return Scheme(frozenset(), t, ())


def free_vars_of_env(env: dict) -> set[int]:
    """Union of all free type variables across all schemes in the environment.

    The memo `scheme_free_vars` keeps is read directly here rather than
    through the copy that function returns: this is the hot caller, it only
    unions, and almost every prelude scheme answers with the empty set —
    a generalised binding usually quantifies everything it mentions.
    """
    fvs: set[int] = set()
    for s in env.values():
        if isinstance(s, Scheme):
            cached = s.__dict__.get("_fvs")
            if cached is None:
                cached = free_vars(s.type_) - s.vars
                object.__setattr__(s, "_fvs", cached)
            if cached:
                fvs |= cached
    return fvs


def _apply_subst_map(t: Type, m: dict[int, TVar]) -> Type:
    """Replace TVars whose ids are in ``m`` with the mapped values."""
    if isinstance(t, TVar):
        if t.id in m:
            return m[t.id]
        return t
    if isinstance(t, (TCon, TInt)):
        return t
    if isinstance(t, TFun):
        return TFun(_apply_subst_map(t.arg, m), _apply_subst_map(t.ret, m),
                    t.span, t.mono)
    if isinstance(t, TApp):
        return TApp(_apply_subst_map(t.fn, m), _apply_subst_map(t.arg, m))
    return t


# ---------------------------------------------------------------------------
# Predicates (typeclass constraints)
# ---------------------------------------------------------------------------

@dataclass(frozen=True, order=True)
class Predicate:
    """A typeclass constraint: ``Show a``, ``Eq Int``, etc.

    ``site`` identifies the expression occurrence that emitted the
    constraint (``id()`` of the ``EGlobal`` node), so elaboration can give
    each occurrence of a method its own dictionary.  It never takes part
    in comparison — two predicates are the same constraint whatever
    occurrence produced them.
    """
    class_name: str
    type_: Type
    site: object = field(default=None, compare=False)

    def __repr__(self):
        return f"{self.class_name} {self.type_}"



# ---------------------------------------------------------------------------
# Orders on types
# ---------------------------------------------------------------------------

#: Type constructors whose values carry the discrete order `x ⩽ y ⟺ x = y`,
#: whatever they are applied to.  A channel of sets is still just a
#: channel; a boxed anything is discrete by construction.
_DISCRETE_CONS = frozenset({
    "Int", "Char", "Bool",
    "Sig", "Chan", "FaL", "ExL", "Box",
    "Cyclic", "Bounded", "Score",
})


def has_nontrivial_order(t: Type, cons: dict | None = None) -> bool:
    """Is ``t`` *known* to carry an order coarser than equality?

    `{A}` is ordered by inclusion; products, sums and user data types
    inherit an order from their components; functions from their result.
    Everything else is discretely ordered, and at a discrete order every
    function is monotone — so Datafun's monotone/discrete distinction says
    nothing there.

    Unknowns answer ``False``.  A type variable *could* be instantiated to
    a set, so this is an over-approximation in the permissive direction:
    it means a polymorphic binder is treated as discrete.  The alternative
    is worse in practice — it marks every `case` binder in generic code
    monotone and rejects ordinary programs — and it costs little here,
    because a body polymorphic in `a` cannot do anything order-sensitive
    with an `a` in the first place.
    """
    if isinstance(t, (TVar, TCon, TInt)):
        return False
    if isinstance(t, TFun):
        # Functions are ordered pointwise.
        return has_nontrivial_order(t.ret, cons)
    if isinstance(t, TApp):
        head, args = t, []
        while isinstance(head, TApp):
            args.append(head.arg)
            head = head.fn
        if isinstance(head, TCon):
            if head.name == "Set":
                return True
            if head.name in _DISCRETE_CONS:
                return False
        return any(has_nontrivial_order(a, cons) for a in args)
    return False


# ---------------------------------------------------------------------------
# The type subgrammars (thesis fig. 2.1)
# ---------------------------------------------------------------------------
#
#   eqtypes         A, B ::= {A}_eq | 1 | A×B | A+B
#   semilattices    L, M ::= {A}_eq | 1 | L×M
#   finite eqtypes  A, B ::= {A}_fin | 1 | A×B | A+B
#   fixtypes        L, M ::= {A}_fin | 1 | L×M
#
# These are what keep the Datafun/Rizzo union sound (`spec/data.md` §II.1):
# the Rizzo formers are simply *not added* to them, so a `Sig A` can never
# be compared with `=`, joined, or made a set element — no side conditions
# to state, and none to prove.
#
# Unknowns answer "allowed": a type variable might be instantiated either
# way, and rejecting it would make every polymorphic set function
# unwritable.  The same permissive over-approximation as
# `has_nontrivial_order`, for the same reason.

#: Base types with decidable equality.  The thesis has none of its own —
#: §2.2 assumes "eqtypes string, char, int" for its examples — so this is
#: gestate's reading of that assumption.
_BASE_EQTYPES = frozenset({"Int", "Float", "Char", "Bool", "Cyclic",
                          "Bounded"})

#: Base eqtypes with *finitely many* inhabitants.  Footnote 2 on p. 16 is
#: explicit that integers would be an eqtype but not a finite one, which
#: is why `{Int}` has infinite ascending chains and `fix` over it need not
#: terminate.  `Cyclic n` and `Bounded lo hi` are the finite ones gestate
#: actually has.
#: `Bounded lo hi` is *not* here: nothing normalises its values into the
#: range (`main : 0 .. 3; main = 7` evaluates to 7), so treating it as
#: finite would let `fix` promise a termination the runtime does not
#: deliver.  Add it once its `fromInteger` clamps or wraps.
_FINITE_BASE_EQTYPES = frozenset({"Bool", "Cyclic"})

#: Formers that are in none of the four subgrammars.  Naming them makes
#: the error messages say *why* rather than merely that.
_NOT_EQTYPE_REASON = {
    "Sig": "a signal", "Chan": "a channel",
    "FaL": "a delayed computation", "ExL": "a delayed computation",
    "Box": "a boxed value", "Score": "a score",
}


#: A tuple type is an ordinary applied constructor, one per arity:
#: ``(A, B)`` is ``TApp(TApp(TCon("Tuple2"), A), B)``.  Making it ordinary is
#: the point — unification, substitution, free variables and kind checking
#: all work on it without a special case.
def tuple_con(n: int) -> "TCon":
    return TCon(f"Tuple{n}")


def mk_tuple(args: list) -> Type:
    acc: Type = tuple_con(len(args))
    for a in args:
        acc = TApp(acc, a)
    return acc


def tuple_parts(t: Type) -> list | None:
    """The components of a tuple type, or ``None`` if ``t`` is not one."""
    head, args = _spine(t)
    if (isinstance(head, TCon) and head.name.startswith("Tuple")
            and head.name[5:].isdigit() and len(args) == int(head.name[5:])):
        return args
    return None


def _spine(t: Type) -> tuple[Type, list[Type]]:
    args: list[Type] = []
    while isinstance(t, TApp):
        args.append(t.arg)
        t = t.fn
    args.reverse()
    return t, args


def is_eqtype(t: Type, cons: dict | None = None, _seen=frozenset()) -> bool:
    """`{A}_eq | 1 | A×B | A+B`, plus gestate's base eqtypes."""
    return _in_grammar(t, cons, finite=False, _seen=_seen)


def is_finite_eqtype(t: Type, cons: dict | None = None, _seen=frozenset()) -> bool:
    """`{A}_fin | 1 | A×B | A+B` — an eqtype with no infinite chains.

    A *recursive* data type is infinite even when its fields are finite
    (`List Bool` is), so recursion disqualifies it.
    """
    return _in_grammar(t, cons, finite=True, _seen=_seen)


def _in_grammar(t: Type, cons, finite: bool, _seen=frozenset()) -> bool:
    if isinstance(t, (TVar, TInt)):
        return True                     # unknown: allowed, see above
    base = _FINITE_BASE_EQTYPES if finite else _BASE_EQTYPES
    if isinstance(t, TCon):
        # `1` is `Tuple0`, and a *bare* constructor rather than an
        # application, so it never reaches the product case below.  Fig. 2.1
        # puts `1` in all four grammars; without this line `{()}` was neither
        # a semilattice nor a fixtype, which is exactly backwards for the
        # type `errata.md` D5 settles on for monotone truth.
        if t.name in base or tuple_parts(t) is not None:
            return True
        if t.name in _NOT_EQTYPE_REASON or cons is None:
            return False
        # A user data type with *no parameters* is a bare `TCon` too, so it
        # never reached the ADT case either — `C := R | G | B` was reported
        # "not an eqtype" however simple it was, and `Set C` was rejected
        # for a type that is finite, ordered and perfectly comparable.
        # `Maybe Bool` escaped only by being an application.
        return _adt_in_grammar(t.name, [], cons, finite, _seen)
    if isinstance(t, TFun):
        return False                    # no arrow in any of the grammars
    head, args = _spine(t)
    if not isinstance(head, TCon):
        return False
    if head.name == "Set":
        return _in_grammar(args[0], cons, finite, _seen) if args else True
    if tuple_parts(t) is not None:
        # `A×B` (fig. 2.1) — a product is an eqtype exactly when both its
        # components are, and finite exactly when both are finite.
        return all(_in_grammar(a, cons, finite, _seen) for a in args)
    if head.name in _NOT_EQTYPE_REASON:
        return False
    if head.name in base:
        return True                     # Cyclic n, Bounded lo hi
    if head.name in _NOT_EQTYPE_REASON or cons is None:
        return False
    return _adt_in_grammar(head.name, args, cons, finite, _seen)


def _adt_in_grammar(name: str, args: list, cons: dict, finite: bool, seen) -> bool:
    """A data type is a sum of products, so it inherits from its fields.

    ``args`` are the type arguments at *this* use, substituted for the
    declaration's parameters — otherwise `Maybe (Sig Int)` would be judged
    by `Maybe a`'s field `a`, which says nothing.
    """
    if name in seen:
        # Recursive: still an eqtype (equality remains decidable) but
        # never a finite one — `List Bool` has infinitely many values.
        return not finite
    seen = seen | {name}
    found = False
    for info in cons.values():
        ret = info.type_
        fields = []
        while isinstance(ret, TFun):
            fields.append(ret.arg)
            ret = ret.ret
        head, params = _spine(ret)
        if not (isinstance(head, TCon) and head.name == name):
            continue
        found = True
        subst = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
        for f in fields:
            if not _in_grammar(_apply_subst_map(f, subst), cons, finite, seen):
                return False
    # A constructor gestate does not know is not in any grammar.  Without
    # this an unknown name looks like a data type with no constructors and
    # so passes vacuously — which is how `Bounded lo hi` slipped in as a
    # *finite* eqtype after being taken out of the base set.
    return found


def is_semilattice(t: Type, cons: dict | None = None) -> bool:
    """`{A}_eq | 1 | L×M` — has ⊥ and ∨.

    Note what is *absent*: `Int` is not a semilattice, so `for (x ∈ e) x`
    is ill-typed.  Datafun's `bool` is `{1}` and so would be one; gestate
    makes `Bool` an ordinary two-constructor data type (`errata.md` D5),
    and an ordinary sum is not.
    """
    if isinstance(t, (TVar, TInt)):
        return True
    parts = tuple_parts(t)
    if parts is not None:
        # `L×M` — a product of semilattices is one, ordered componentwise.
        return all(is_semilattice(a, cons) for a in parts)
    head, args = _spine(t)
    if isinstance(head, TCon) and head.name == "Set":
        return is_eqtype(args[0], cons) if args else True
    return False


def is_fixtype(t: Type, cons: dict | None = None) -> bool:
    """`{A}_fin | 1 | L×M` — a semilattice with no infinite ascending chains.

    This is what makes `fix` terminate: the chain `⊥ ⩽ f ⊥ ⩽ f (f ⊥) ⩽ …`
    stabilises only if it cannot ascend forever.
    """
    if isinstance(t, (TVar, TInt)):
        return True
    parts = tuple_parts(t)
    if parts is not None:
        return all(is_fixtype(a, cons) for a in parts)
    head, args = _spine(t)
    if isinstance(head, TCon) and head.name == "Set":
        return is_finite_eqtype(args[0], cons) if args else True
    return False


# ---------------------------------------------------------------------------
# The flat types — the audio fragment's subgrammar (`spec/liveaudio.md`)
# ---------------------------------------------------------------------------
#
#   flat  A, B ::= Int | Float | Bool | Char | 1 | Cyclic n | Bounded lo hi
#                | A × B | a non-recursive data type over flat fields
#
# A fifth subgrammar, and **none of Datafun's four is the one wanted** — a
# fact worth stating, because reaching for `is_finite_eqtype` is the obvious
# move and it is wrong twice over.  The finite eqtypes exclude `Float` and
# `Int`, which is most of what a synth is made of, and every eqtype admits
# `Set A`, which is a heap structure of unbounded size.  What this grammar
# is *for* is different from what those are for: they ask whether values can
# be compared or iterated to a fixed point, and this asks whether a value
# has a **known, fixed size in a state struct**.
#
# One consequence of that purpose, and it is the opposite of the other four:
# an unknown type is **rejected**.  `_in_grammar` answers "allowed" for a
# type variable, because refusing would make every polymorphic set function
# unwritable.  Here a variable is exactly the thing that cannot be laid out,
# so `a` is a rejection and the fragment is monomorphic by construction.

#: Base types that occupy a fixed number of bytes.
_FLAT_BASE = frozenset({"Int", "Float", "Bool", "Char", "Cyclic", "Bounded"})

#: Why a former is not flat — the message says which one and why.
_NOT_FLAT_REASON = dict(_NOT_EQTYPE_REASON, **{
    "Set": "a set, which is a heap structure of unbounded size",
    "List": "a list, which is recursive and so has no fixed size",
})


def is_flat(t: Type, cons: dict | None = None, _seen=frozenset()) -> bool:
    """Does a value of this type have a known, fixed size?

    This is the condition on a step function's state and on every value
    flowing through an audio-rate node: the engine lays the state out once,
    as a struct, and never allocates again.
    """
    if isinstance(t, TInt):
        return True                     # a type-level number, not a value
    if isinstance(t, TVar):
        return False                    # see above: unknown is a rejection
    if isinstance(t, TFun):
        return False
    parts = tuple_parts(t)
    if parts is not None:
        return all(is_flat(a, cons, _seen) for a in parts)
    head, args = _spine(t)
    if not isinstance(head, TCon):
        return False
    if head.name in _NOT_FLAT_REASON:
        return False
    if head.name in _FLAT_BASE:
        return True
    if cons is None:
        return False
    return _adt_flat(head.name, args, cons, _seen)


def _adt_flat(name: str, args: list, cons: dict, seen) -> bool:
    """A data type is flat when it is non-recursive over flat fields.

    Recursion is the disqualifier rather than a depth bound: a value of a
    recursive type is a chain of heap cells whose length is a run-time
    fact, and a state layout is a compile-time one.
    """
    if name in seen:
        return False
    seen = seen | {name}
    found = False
    for info in cons.values():
        ret = info.type_
        fields = []
        while isinstance(ret, TFun):
            fields.append(ret.arg)
            ret = ret.ret
        head, params = _spine(ret)
        if not (isinstance(head, TCon) and head.name == name):
            continue
        found = True
        subst = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
        for f in fields:
            if not is_flat(_apply_subst_map(f, subst), cons, seen):
                return False
    return found


def why_not_flat(t: Type, cons: dict | None = None) -> str:
    """A phrase saying which part of ``t`` is not flat, and why."""
    if isinstance(t, TVar):
        return ("a type variable, so its size is not known at compile "
                "time — the fragment is monomorphic")
    if isinstance(t, TFun):
        return "a function, and a function has no layout in a state struct"
    parts = tuple_parts(t)
    if parts is not None:
        for a in parts:
            if not is_flat(a, cons):
                return f"a tuple whose component {show(a)} is {why_not_flat(a, cons)}"
    head, args = _spine(t)
    if isinstance(head, TCon):
        if head.name in _NOT_FLAT_REASON:
            return _NOT_FLAT_REASON[head.name]
        if head.name not in _FLAT_BASE and cons is not None:
            # A field that is not flat is the more useful answer, so look
            # for one first: `Maybe (List Int)` is not recursive, its field
            # is, and saying "recursive" of `Maybe` would be a lie.
            for info in cons.values():
                ret, fields = info.type_, []
                while isinstance(ret, TFun):
                    fields.append(ret.arg)
                    ret = ret.ret
                rhead, params = _spine(ret)
                if not (isinstance(rhead, TCon) and rhead.name == head.name):
                    continue
                subst = {p.id: a for p, a in zip(params, args)
                         if isinstance(p, TVar)}
                for f in fields:
                    f = _apply_subst_map(f, subst)
                    if not is_flat(f, cons):
                        return (f"a data type whose field {show(f)} is "
                                f"{why_not_flat(f, cons)}")
            if not _adt_flat(head.name, args, cons, frozenset()):
                return ("recursive, so a value of it is a chain of heap "
                        "cells whose length is a run-time fact")
            return "not a data type gestate knows"
    return "not flat"


def show(t) -> str:
    """`show_type`, imported late — `show.py` imports this module."""
    from .show import show_type
    return show_type(t)


def why_not_eqtype(t: Type) -> str:
    """A phrase naming the offending former, for an error message."""
    head, _ = _spine(t)
    if isinstance(head, TCon):
        if head.name in _NOT_EQTYPE_REASON:
            return _NOT_EQTYPE_REASON[head.name]
        if isinstance(t, TFun):
            return "a function"
    if isinstance(t, TFun):
        return "a function"
    return "not an eqtype"
