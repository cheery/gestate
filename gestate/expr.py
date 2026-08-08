"""Supercombinator expressions: the shared `Expr` grammar.

Both phases of the implementation -- lambda lifting and G-machine codegen
-- operate on this grammar.  See `spec/supercomb.md`.

    Expr := EGlobal Name
          | EVar Name
          | ENum Int
          | ECon Tag [Expr]
          | EAp Expr Expr
          | ELet IsRec [(Name, Expr)] Expr
          | ECase Expr [Alter]
          | ELambda [Name] Expr
          | ETuple [Expr]
          | EProj Int

    Name          := str | int       -- str is a "Known" source id;
                                     -- int is an "Anon" lifted-SC id
    Arity         := Int
    Tag           := Int
    IsRec         := Bool
    Alter         := (Tag, [Name], Expr)

The earlier draft of this grammar used DeBruijn indices for `EVar`;
the current grammar uses named binders throughout.  The Python
representation drops the `Known`/`Anon` dataclasses of the earlier
draft: a `Name` is just `Union[str, int]`.  `str` plays the role of
"Known" (a source-named identifier, whether a global SC or a local
binder); `int` plays the role of "Anon" (the id of a lambda-lifted
SC emitted by the lifter).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

#: A `Name` is either a source identifier (``str``) or the id of a
#: lambda-lifted supercombinator (``int``).  Source identifiers cover
#: both global SC names and local binders; lifted SC ids live in a
#: disjoint namespace and are assigned by the lifter.
Name = Union[str, int]


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

class Expr:
    """Base class for all expression forms."""


@dataclass
class EGlobal(Expr):
    """Reference to a global (supercombinator or built-in) by name.

    ``name`` is a ``str`` for source-named SCs (e.g. ``"main"``) or an
    ``int`` for a lambda-lifted SC (the lifter's fresh id).
    """
    name: Name
    #: Where the author wrote it, or `None`.  **Out of comparison and out
    #: of `repr`**, exactly as `EHole.span` is, so that two references to
    #: the same global remain the same expression to every pass but the one
    #: reporting them — nothing downstream may start distinguishing
    #: occurrences by where they were written.
    #:
    #: A core `Expr` normally has no position at all, and for a long time
    #: `EHole` was the only exception.  This is the second, and it buys one
    #: thing: `Unknown global 'sinewave'` can say *where*.  Measured before
    #: it existed, six of ten kinds of error carried no position, and the
    #: editor had nowhere to put them but a banner at the top of the file.
    span: object = field(default=None, compare=False, repr=False)


@dataclass
class EHole(Expr):
    """``_`` in expression position — a value not written yet.

    Inference gives it a fresh variable, so it takes whatever type its
    context demands and the program around it still type-checks.  Reading
    that variable back under the final substitution is what says what
    belongs here, and `span` is where "here" is: the editor wants a
    position, and a core `Expr` is the one thing in this pipeline that
    normally has none.

    It has no value.  A program with a hole in it type-checks and does not
    run, which is the point — `gmachine` refuses it by name rather than
    falling over an unknown node.
    """
    #: The `Span` the surface `_` had, or `None`.  Out of comparison: two
    #: holes at the same type are the same hole to every pass but the one
    #: reporting them.
    span: object = field(default=None, compare=False, repr=False)
    #: Its type under the final substitution — see `EVar.type_`.
    type_: object = field(default=None, compare=False, repr=False)


@dataclass
class EVar(Expr):
    """The bound variable named ``name``.

    Binders come from SC parameters (the outer ``ELambda`` of an SC),
    ``let``/``letrec`` defs, or ``case`` alt field names.  ``EVar``
    never carries a global id; only ``EGlobal`` does.

    ``type_`` is the occurrence's type under the final substitution, or
    ``None`` where nothing inferred it.  δ needs it for one case: a
    variable used inside a `□` but bound outside it cannot change, so its
    change is the zero change *at its type* (`spec/data.md` §I.3), and
    there is nowhere else to read that type from.
    """
    name: Name
    #: Out of comparison and out of `repr`: it is an annotation about an
    #: occurrence, not part of which variable this is.
    type_: object = field(default=None, compare=False, repr=False)
    #: Where the author wrote it — see `EGlobal.span`, which this
    #: matches.  **Last, and that is not cosmetic**: `EVar(name,
    #: type_)` is constructed positionally in `changes.py`'s tests,
    #: so a field inserted ahead of `type_` would silently become
    #: the type and leave the real one `None`.
    span: object = field(default=None, compare=False, repr=False)


@dataclass
class ENum(Expr):
    """A numeric literal.

    `int` or `float`, and which one it is *is* its type: `1` is an `Int`
    and `1.0` a `Float`.  There is no defaulting either way.
    """
    n: int | float


@dataclass
class EChr(Expr):
    """A character literal — a Unicode code point.

    Represented at run time exactly as ``ENum`` is, because ``Char`` is an
    integer type; the separate node is what keeps it *typed* as ``Char``
    rather than picking up a ``Num`` constraint and defaulting to ``Int``.
    """
    n: int


@dataclass
class ECon(Expr):
    """A data constructor of tag ``t`` applied to ``args``.

    ``args`` is in left-to-right (source) order; the G-machine compiler
    reverses them so that the last argument ends up on top of the stack.
    """
    tag: int
    args: list[Expr] = field(default_factory=list)


@dataclass
class EAp(Expr):
    """Application of one expression to another."""
    fn: Expr
    arg: Expr
    #: True when the function's arrow is `->` rather than `~>`, i.e. the
    #: argument position is discrete.  `A -> B` is Datafun's `□A → B`, so
    #: the argument is checked in the stripped context — a monotone
    #: variable may not appear there.  Filled in by inference.
    discrete_arg: bool = True


@dataclass
class ELet(Expr):
    """A (possibly recursive) ``let`` / ``letrec``.

    ``defs`` is a list of ``(Name, Expr)`` pairs in left-to-right source
    order.  After compilation those binders occupy contiguous stack
    slots ``[0..n-1]``; the i-th pair's value lives at offset ``n-1-i``
    (the last-pushed def is topmost).  When ``is_rec`` is true the
    binders may reference each other; otherwise each def may reference
    only outer (older) binders.
    """
    is_rec: bool
    defs: list[tuple[Name, Expr]]
    body: Expr


@dataclass
class ECase(Expr):
    """A ``case`` expression: evaluate ``scrut`` to WHNF and dispatch
    on its tag using ``alts``.
    """
    scrut: Expr
    alts: list[Alter]


@dataclass
class ELambda(Expr):
    """A lambda abstraction binding the list of parameter names ``params``.

    At the SC top level a single ``ELambda`` wraps the SC's parameter
    list.  Lambda lifting turns every *nested* ``ELambda`` into a
top-level ``(int_id, ELambda(frame_params, lifted_body))`` SC and
    replaces the lift-site with an ``EAp``/``EGlobal(int_id)`` chain.
    Any ``ELambda`` the G-machine compiler sees inside ``compileC`` is
    an error (lambda lifting did not run).
    """
    params: list[Name]
    body: Expr
    #: Parameters this lambda binds *monotonically*, filled in by
    #: inference from the arrows it was checked against.  A parameter is
    #: monotone only when its arrow is `~>` **and** its type has a
    #: non-trivial order; at a discretely ordered type the two flavours
    #: coincide, so ordinary code never lands here.  See
    #: `gestate/monotone.py`.
    mono: frozenset = frozenset()
    #: Candidate monotone binders with their types, recorded as inference
    #: visits the node.  The type may still be a metavariable at that
    #: point, so the discrete-order test runs once at the end over the
    #: final substitution — see `infer_program`.
    mono_candidates: tuple = ()
    #: This lambda's own type under the final substitution, or `None`.
    #:
    #: **What a step function's element types are read from.**  A signal
    #: former is typed by its step — `zipSig f l r` with
    #: `f : a -> b -> c` means `l : Sig a` — and a step written as a lambda
    #: had no type to read, so a former nested inside another with a lambda
    #: step could not be typed at all and had to be given a name of its own
    #: (`audioextract._former`).  Inference knew it and dropped it; this is
    #: where it is kept.  Out of comparison and `repr` for the reason
    #: `EVar.type_` is: it annotates an occurrence rather than saying which
    #: lambda this is.
    type_: object = field(default=None, compare=False, repr=False)


@dataclass
class ETuple(Expr):
    """An n-ary tuple of ``args`` (``len(args) >= 2``; the parser and
    compiler reject shorter tuples).  Tuples are NOT data
    constructors -- they have no ``Tag`` and are not matched by
    ``ECase``.  The G-machine compiles them to ``PackTuple n`` and
    represents them at runtime as ``NTuple`` (no tag), distinct from
    ``ECon``'s tagged ``NCon`` form.  Field access is via ``EProj``
    applied to the tuple.
    """
    args: list[Expr] = field(default_factory=list)


@dataclass
class EField(Expr):
    """``e.N`` — a projection whose meaning depends on ``e``'s *type*.

    A tuple and a record are different runtime shapes: a tuple is an
    `NTuple` selected with `Proj`, a record is a one-constructor `NCon`
    destructured with a `case`.  Which one `e.N` means is therefore not
    decidable at desugaring, which runs before inference — so it survives
    as this node, inference records what it resolved to, and a small pass
    lowers it.

    That is deliberately *not* principal: `f p = p.0` has no type unless
    `p`'s is already known, and the error says so.  `syntax.md` prescribes
    sixteen `AttrN` classes instead, which would make it principal at the
    cost of ~120 generated instances for polymorphism nothing in this
    language has asked for.

    ``lowering`` is ``("tuple", i, width)`` or ``("con", tag, arity, i)``,
    filled by inference.
    """
    base: Expr
    index: object
    base_type: object = None
    lowering: object = None


@dataclass
class EProj(Expr):
    """The i-th (0-based) field selector for a tuple.

    ``EProj i`` is a *partial* expression: it must appear exactly as
    ``EAp (EProj i) tup`` for some tuple-valued ``Expr tup``.  A bare
    ``EProj i`` (not directly applied via ``EAp``) is a compile error
    -- it is not a first-class value, mirroring ``ECon``'s ``Pack``
    convention.  The G-machine compiles ``EAp (EProj i) tup`` to
    ``compileC tup ++ [Eval, Proj i]``: the tuple is forced to WHNF
    and the i-th field is selected.

    ``width`` is the arity of the tuple being projected, recorded by the
    match compiler when it destructures a tuple pattern.  Inference needs
    it: a projection alone does not say how wide its operand is, and the
    tuple type constructors are distinct per arity.  Code generated after
    type checking (dictionary and box projections) leaves it ``None``.
    """
    i: int
    width: int | None = None


@dataclass
class EAnnot(Expr):
    """A type-annotated expression: ``(expr : type)``.

    Carries through the type checker; the G-machine compiler
    strips it and compiles the inner ``expr``.
    """
    expr: Expr
    type_: object  # Type, imported lazily to avoid circular import

    def __repr__(self):
        return f"({self.expr} : {self.type_})"


# ---------------------------------------------------------------------------
# FRP / Rizzo nodes (increment 9a)
# ---------------------------------------------------------------------------

@dataclass
class ESigCons(Expr):
    """Signal cons: ``value ::: tail`` — allocate a fresh ``NSig`` node."""
    value: Expr
    tail: Expr


@dataclass
class ESigHead(Expr):
    """Signal head: ``head sig`` — project the current value from an ``NSig``."""
    sig: Expr


@dataclass
class EDelay(Expr):
    """Delay: ``delay t`` — wrap ``t`` as a lazy ⃝∀ value (``NCon tagDelay``)."""
    body: Expr


@dataclass
class EAppFa(Expr):
    """⃝∀ applicative action: ``s <*> t`` (Rizzo's ``⊛``).

    ``⃝∀(A→B) → ⃝∀A → ⃝∀B``.  Both operands are already delayed, so the
    application is built structurally — ``delay f <*> delay x`` reduces to
    ``delay (f x)`` — and no clock is involved.
    """
    fn: Expr
    arg: Expr


@dataclass
class EAppEx(Expr):
    """⃝∀/⃝∃ applicative action: ``s <@> t`` (Rizzo's ``5``).

    ``⃝∀(A→B) → ⃝∃A → ⃝∃B``.  A universally delayed function is available
    whenever any clock ticks, in particular when the argument's clock does,
    so ``cl (s <@> t) = cl t``.  This is the only bridge between the two
    modalities and hence the only way to *compute* a signal from another.
    """
    fn: Expr
    arg: Expr


@dataclass
class EWait(Expr):
    """Wait: ``wait κ`` — produce a value when channel ``κ`` fires."""
    chan: Expr


@dataclass
class EWatch(Expr):
    """Watch: ``watch l`` — produce the current value of signal ``l`` when it updates."""
    sig: Expr


@dataclass
class ESync(Expr):
    """Sync: ``sync s t`` — combine two ⃝∃ values."""
    left: Expr
    right: Expr


@dataclass
class ENever(Expr):
    """Never: ``never`` — a ⃝∃ value that never fires."""
    pass


@dataclass
class ETail(Expr):
    """Tail: ``tail sig`` — wrap a signal reference as a ⃝∃ (Sig A) value."""
    sig: Expr


@dataclass
class EChan(Expr):
    """Channel: ``chan`` — allocate a fresh ``NChan``.

    ``elem_type`` is filled in by inference with the ``A`` of this
    occurrence's ``Chan A``.  The driver keeps a channel context Δ so it
    can reject input on a channel that was never allocated, and there is
    nowhere else to learn a channel's type: the heap is untyped and a
    channel minted at run time (one per widget, in the paper's GUI
    example) has no declaration to consult.
    """
    elem_type: object = None


@dataclass
class EGFix(Expr):
    """Guarded fixed point: ``gfix x.t`` — compile via cyclic ``delay``-wrapped self-reference."""
    var: str
    body: Expr


# ---------------------------------------------------------------------------
# Datafun nodes (increment 10a)
# ---------------------------------------------------------------------------

@dataclass
class EFix(Expr):
    """Datafun semilattice fixed point: ``fix e`` — iterate to convergence."""
    body: Expr
    #: The fixed point's type, filled in by inference.  Selects the
    #: generated helpers and is what the fixtype check is made against.
    set_type: object = None


@dataclass
class EFor(Expr):
    """Set comprehension: ``for (x in e) f`` — fold + join over a set."""
    var: str
    set_expr: Expr
    body: Expr
    #: The loop's *result* type — a semilattice — filled in by inference.
    #: `for` eliminates into any semilattice, not only into sets, so the
    #: join it compiles to has to be chosen from this rather than assumed.
    result_type: object = None
    #: The element type of the set being looped over.
    elem_type: object = None


@dataclass
class EBox(Expr):
    """Box introduction: ``Box e`` — wraps e in the □ modality."""
    body: Expr


@dataclass
class EUnbox(Expr):
    """Box elimination: ``unbox x = e in f`` — pattern-match box, bind x."""
    var: str
    binding: Expr
    body: Expr


@dataclass
class EJoin(Expr):
    """Semilattice join: ``e \\/ f`` — Datafun's ``e ∨ f`` (fig. 2.3, `join`).

    ``L`` must be a semilattice; ⊥ is the empty set literal ``{}``.
    Without this there is no way to *use* a semilattice, and so no way to
    write a fixed point that does anything: every Datalog query has the
    shape ``fix (r => base \\/ step r)``.
    """
    left: Expr
    right: Expr
    #: The semilattice being joined, filled in by inference.
    set_type: object = None


@dataclass
class ESet(Expr):
    """Set literal: ``{e1, e2, ...}`` — canonical sorted Cons-list."""
    items: list[Expr]
    #: The set's own type (`Set A`), filled in by inference.  `A` must be
    #: an eqtype: the runtime representation is a sorted list, so the
    #: elements have to be comparable.
    set_type: object = None


# ---------------------------------------------------------------------------
# Alts
# ---------------------------------------------------------------------------

@dataclass
class Alter:
    """A single ``case`` alternative: ``(Tag, [Name], Expr)``.

    ``names`` is the source-order list of field binders the alt
    introduces; the alt's arity is simply ``len(names)``.  The
    G-machine compiler uses this list directly (no separate arity
    table is needed).
    """
    tag: int
    names: list[Name]
    body: Expr
    #: Field binders this alternative binds monotonically (Datafun's
    #: `case` rule binds `Xi : Ai`), restricted the same way as
    #: `ELambda.mono`.
    mono: frozenset = frozenset()
    mono_candidates: tuple = ()
    #: The type of each binder in ``names``, under the final substitution.
    #: δ needs them: a `case`'s dead branch returns `dummy xᵢ`, and which
    #: zero change that is depends on `xᵢ`'s type (`spec/data.md` §I.4.2).
    field_types: tuple = ()


def mk_alt(tag: int, names: list[Name], body: Expr) -> Alter:
    return Alter(tag, names, body)


__all__ = [
    "Name",
    "Expr",
    "EGlobal",
    "EVar",
    "ENum",
    "EChr",
    "ECon",
    "EAp",
    "ELet",
    "ECase",
    "ELambda",
    "ETuple",
    "EField",
    "EProj",
    "EAnnot",
    "ESigCons",
    "ESigHead",
    "EDelay",
    "EWait",
    "EWatch",
    "ESync",
    "ENever",
    "ETail",
    "EChan",
    "EGFix",
    "EFix",
    "EFor",
    "EBox",
    "EUnbox",
    "EJoin",
    "ESet",
    "Alter",
    "mk_alt",
    "subexprs",
    "map_children",
]


def subexprs(e: Expr) -> list[Expr]:
    """Every immediate sub-expression of ``e``, whatever its node kind.

    Reading the dataclass fields keeps this total, so a pass that only
    needs to *find* something (rather than rebuild the tree) does not have
    to enumerate all twenty-odd node kinds and go stale when one is added.
    """
    from dataclasses import fields, is_dataclass

    if not is_dataclass(e):
        return []
    out: list[Expr] = []
    for f in fields(e):
        v = getattr(e, f.name)
        if isinstance(v, Expr):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, Expr):
                    out.append(item)
                elif isinstance(item, tuple):
                    out.extend(x for x in item if isinstance(x, Expr))
                elif isinstance(item, Alter):
                    out.append(item.body)
    return out

def map_children(e: Expr, f) -> Expr:
    """Rebuild ``e`` with ``f`` applied to each immediate sub-expression.

    Driven by the dataclass fields, so it stays total as node kinds are
    added *and* carries every other field through — the type annotations
    inference leaves on `ESet`/`EFix`/`EFor`/`EChan`, and the binder
    flavours it leaves on `ELambda`/`Alter`, would not survive a
    hand-written rebuilder that names only the fields it knows about.
    """
    from dataclasses import fields, is_dataclass, replace

    if not is_dataclass(e):
        return e
    changes: dict = {}
    for fld in fields(e):
        v = getattr(e, fld.name)
        if isinstance(v, Expr):
            changes[fld.name] = f(v)
        elif isinstance(v, list) and v:
            if all(isinstance(x, Expr) for x in v):
                changes[fld.name] = [f(x) for x in v]
            elif all(isinstance(x, Alter) for x in v):
                changes[fld.name] = [replace(a, body=f(a.body)) for a in v]
            elif all(isinstance(x, tuple) and len(x) == 2 for x in v):
                changes[fld.name] = [(n, f(d)) for n, d in v]
    return replace(e, **changes) if changes else e
