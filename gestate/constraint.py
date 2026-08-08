"""Constraint generation and solving.

Constraints (predicates) are generated during type inference when class
methods are used.  They are solved by matching against the instance table.
Associated type families are resolved as part of constraint solving.
"""

from __future__ import annotations

from .types import Type, Predicate, TVar, TApp, TCon, TFun, TInt, Subst
from .declarations import InstanceInfo, ClassInfo
from .show import show_predicate


class ConstraintError(Exception):
    pass


#: Backstop for runaway resolution (spec/typeclasses.md §5.2).  The
#: Paterson conditions should make this unreachable in ordinary programs.
RESOLUTION_DEPTH_CAP = 200


def solve_predicate(
    pred: Predicate,
    instances: list[InstanceInfo],
    _depth: int = 0,
    _in_progress: frozenset = frozenset(),
) -> InstanceInfo | None:
    """Find the instance satisfying ``pred``, solving its context too.

    Resolution is Horn-clause resolution over the instance table: a
    matching head commits to that instance (coherence guarantees at most
    one matches), and every predicate in its context must be solvable in
    turn.

    A predicate on a bare type variable is *ambiguous*: nothing has pinned
    the variable down, and an unresolved metavariable matches every head.
    Where the class allows a default (`Num`/`Eq`/`Ord` → `Int`) that
    settles it.  Where it does not, the permissive match stands — several
    programs rely on it — but it can then lead an instance back to its own
    context unchanged, so ``_in_progress`` cuts the cycle.
    """
    if _depth > RESOLUTION_DEPTH_CAP:
        raise ConstraintError(
            f"instance resolution exceeded depth {RESOLUTION_DEPTH_CAP} "
            f"solving {show_predicate(pred)}, likely a missing base case "
            f"in class '{pred.class_name}'"
        )

    pred = _default_ambiguous(pred)
    key = (pred.class_name, str(pred.type_))
    inner = _in_progress | {key}

    for inst in instances:
        if inst.class_name != pred.class_name:
            continue
        bindings = match_head(inst.head_type, pred.type_)
        if bindings is None:
            continue
        context = [Predicate(c.class_name, subst_vars(c.type_, bindings))
                   for c in inst.context]
        # An instance whose context reproduces the goal cannot discharge
        # it.  That happens when the goal is a bare variable: the head
        # matches only because an unresolved metavariable matches
        # anything, so the context comes back just as unresolved and
        # resolution re-enters this very instance.  Skipping lets a later
        # instance — the base case — claim the goal instead of running to
        # the depth cap.
        if any((c.class_name, str(c.type_)) in inner for c in context):
            continue
        for sub in context:
            if solve_predicate(sub, instances, _depth + 1, inner) is None:
                raise ConstraintError(
                    f"No instance for {show_predicate(sub)}, required by the "
                    f"context of instance {inst}{rigid_hint(sub)}"
                )
        return inst

    # Synthetic instances for numeric types
    if pred.class_name == "Num":
        inst = _numeric_instance(pred.type_)
        if inst is not None:
            return inst
    if pred.class_name in ("Eq", "Ord"):
        inst = _comparison_instance(pred.class_name, pred.type_)
        if inst is not None:
            return inst

    return None


#: Methods of the two comparison classes, in declaration order.
_COMPARISON_METHODS = {"Eq": ("==", "/="), "Ord": ("<", "<=", ">", ">=")}


def _comparison_instance(class_name: str, t: Type) -> InstanceInfo | None:
    """`Eq`/`Ord` at an integer-represented type with a parameter.

    `Cyclic n` and `lo .. hi` are families, so their instances cannot be
    written out the way `Eq Int` is — one is needed per `n`.  They are
    synthesized on demand, exactly as `Num (Cyclic n)` already is, and
    reach the same integer primitives because their values are normalised
    to a plain integer.
    """
    from .declarations import _method_eqn

    head = t
    while isinstance(head, TApp):
        head = head.fn
    if not (isinstance(head, TCon) and head.name in ("Cyclic", "Bounded")):
        return None
    return InstanceInfo(
        class_name=class_name, head_type=t, builtin=True,
        methods={m: _method_eqn(m, ["x", "y"])
                 for m in _COMPARISON_METHODS[class_name]},
    )


#: Classes whose ambiguous constraints default (`fixme.md` F32).  To `Int`,
#: except that a `Floating` constraint can only be satisfied by a type a
#: float literal makes sense at — so a variable carrying one defaults to
#: `Float`, and `1.5` in a program that pins it nowhere is a `Float` as it
#: always was.
_DEFAULTABLE = ("Num", "Eq", "Ord", "Floating", "Div", "Signed")


def rigid_hint(pred: Predicate) -> str:
    """Why a constraint on a signature variable cannot be resolved.

    The body of `f : a -> a ; f x = x + 1` needs `Num a` at a type the
    *caller* names, and no instance covers every such choice.  The one
    thing that can grant it is the signature's own context, so the message
    says which context to write.
    """
    t = pred.type_
    if not (isinstance(t, TVar) and t.rigid):
        return ""
    name = t.name or f"a{t.id}"
    return (f" — '{name}' is a signature variable, standing for whatever type "
            f"the caller chooses; write '({pred.class_name} {name}) => …' in "
            f"the signature to require it of the caller")


def _default_ambiguous(pred: Predicate) -> Predicate:
    """Resolve an ambiguous numeric or comparison constraint to `Int`.

    A predicate still on a bare type variable by the time it reaches
    resolution is one nothing can pin down: an instance context would have
    been substituted by its head's bindings, and a dictionary parameter
    would have been matched as an assumption before this point.  An
    unresolved metavariable matches *every* instance head, so without
    defaulting the choice falls to whichever instance is declared first —
    adding `instance Ord Bool` to the prelude would silently retype
    `3 < 5`.

    A *rigid* variable is not ambiguous — it is decided, by the caller —
    so defaulting it would be answering a question that is not open.  It is
    left alone, and the missing dictionary is reported instead.
    """
    if (isinstance(pred.type_, TVar) and not pred.type_.rigid
            and pred.class_name in _DEFAULTABLE):
        default = "Float" if pred.class_name == "Floating" else "Int"
        return Predicate(pred.class_name, TCon(default), pred.site)
    return pred


def match_head(pattern: Type, target: Type,
                bindings: dict[int, Type] | None = None) -> dict[int, Type] | None:
    """One-way match of an instance head against a predicate's type.

    Returns the variable bindings that make ``pattern`` equal to
    ``target``, or ``None`` if the head does not match.  A type variable
    in ``target`` is an *unresolved metavariable* from inference, not a
    rigid variable: it is treated as matching anything, which is what
    lets `Num a` resolve while `a` is still open.
    """
    if bindings is None:
        bindings = {}
    if isinstance(pattern, TVar):
        # Bind first, even against a metavariable: `Show [a]` matched to
        # `Show [b]` must record a ↦ b, or the instance's context comes
        # back mentioning the *head's* variable and matches nothing.
        seen = bindings.get(pattern.id)
        if seen is not None and seen != target:
            return None
        bindings[pattern.id] = target
        return bindings
    if isinstance(target, TVar):
        # A *rigid* target is not an open metavariable: it is a type the
        # caller picks, and no instance is known to cover every such
        # choice.  Only the enclosing signature's context can discharge it,
        # and that is matched as an assumption before resolution is
        # reached (`fixme.md` F36).
        return None if target.rigid else bindings
    if type(pattern) is not type(target):
        return None
    if isinstance(pattern, TCon):
        return bindings if pattern.name == target.name else None
    if isinstance(pattern, TInt):
        return bindings if pattern.n == target.n else None
    if isinstance(pattern, TFun):
        if match_head(pattern.arg, target.arg, bindings) is None:
            return None
        return match_head(pattern.ret, target.ret, bindings)
    if isinstance(pattern, TApp):
        if match_head(pattern.fn, target.fn, bindings) is None:
            return None
        return match_head(pattern.arg, target.arg, bindings)
    return None


def subst_vars(t: Type, bindings: dict[int, Type]) -> Type:
    """Instantiate an instance context with the head's bindings."""
    if isinstance(t, TVar):
        return bindings.get(t.id, t)
    if isinstance(t, TFun):
        return TFun(subst_vars(t.arg, bindings), subst_vars(t.ret, bindings))
    if isinstance(t, TApp):
        return TApp(subst_vars(t.fn, bindings), subst_vars(t.arg, bindings))
    return t


def _numeric_instance(t: Type) -> InstanceInfo | None:
    """Generate a synthetic InstanceInfo for numeric types.

    For ``Num Int``: direct instance with ``fromInteger x = x``.
    For ``Num (Cyclic 12)``: generic instance ``fromInteger (using n) x = prim_mod_int x n``
    where ``n`` is unified with the concrete type-level integer at the call site.
    """
    if isinstance(t, TCon) and t.name == "Int":
        return _make_num_instance("Int", t, None)
    if isinstance(t, TCon) and t.name == "Float":
        return _make_num_instance("Float", t, None)
    if isinstance(t, TApp) and isinstance(t.fn, TCon) and t.fn.name == "Cyclic":
        # Generic: Num (Cyclic n) with (using n)
        return _make_num_instance("Cyclic", t, ["n"])
    if isinstance(t, TApp) and isinstance(t.fn, TApp) and \
       isinstance(t.fn.fn, TCon) and t.fn.fn.name == "Bounded":
        return _make_num_instance("Bounded", t, ["n", "m"])
    return None


def _make_num_instance(base: str, head: Type,
                       using_params: list[str] | None = None) -> InstanceInfo:
    """All four methods, not just `fromInteger`.

    A dictionary slot for a method the instance leaves out has no body to
    call; leaving `+`/`-`/`*` out here meant every arithmetic operation at
    `Cyclic n` silently produced the placeholder instead of a result.
    """
    from .declarations import _dummy_vsceq, _method_eqn

    methods = {"fromInteger": _dummy_vsceq("fromInteger", "x", "x")}
    for op in ("+", "-", "*"):
        methods[op] = _method_eqn(op, ["x", "y"])
    if using_params:
        for eq in methods.values():
            eq.using_params = list(using_params)
    return InstanceInfo(
        class_name="Num", head_type=head, methods=methods, builtin=True,
    )


def literal_hint(pred: Predicate) -> str:
    """Say what an unsatisfiable literal constraint means, in the source.

    `Floating` and `Num` are classes a program never writes: they arrive
    from a *literal*, and "No instance for Floating Int" is the compiler's
    way of saying that `1.5` is where an `Int` was wanted.  Saying the
    second is the point of having the first.
    """
    if not (isinstance(pred.type_, TCon) and pred.class_name in
            ("Floating", "Num")):
        return ""
    if pred.class_name == "Floating":
        return (f".  A literal with a point in it is not "
                f"`{pred.type_.name}` — `1.5` needs a type with a "
                f"`Floating` instance, and `Float` is the one every "
                f"program has")
    return (f".  A whole-number literal is not `{pred.type_.name}` — it "
            f"needs a type with a `Num` instance")


def solve_constraints(
    predicates: list[Predicate],
    instances: list[InstanceInfo],
) -> dict[Predicate, InstanceInfo]:
    resolved: dict[Predicate, InstanceInfo] = {}
    for pred in predicates:
        pred = _default_ambiguous(pred)
        inst = solve_predicate(pred, instances)
        if inst is None:
            sp = ""
            t = pred.type_
            if hasattr(t, 'span') and t.span is not None:
                try:
                    s = t.span
                    if hasattr(s, 'start') and hasattr(s, 'end'):
                        sp = f" (at {s.start.line}:{s.start.col}–{s.end.line}:{s.end.col})"
                    elif hasattr(s, 'line') and hasattr(s, 'col'):
                        sp = f" (at {s.line}:{s.col})"
                except Exception:
                    pass
            raise ConstraintError(
                f"No instance for {show_predicate(pred)}{sp}"
                f"{literal_hint(pred)}{rigid_hint(pred)}"
            )
        resolved[pred] = inst
    return resolved


def normalize_associated(
    method_type: Type,
    class_param: Type,
    head_type: Type,
    assoc_types: dict[str, Type],
) -> Type:
    """Replace associated type applications in a method type with their
    concrete values from an instance.

    Example: method_type = ``Elem c -> c -> c``, head_type = ``Int``,
    assoc_types = ``{"Elem": String}``.
    Returns ``String -> Int -> Int``.
    """
    return _norm(method_type, class_param, head_type, assoc_types)


def _norm(t: Type, param: Type, head: Type, ats: dict[str, Type]) -> Type:
    if isinstance(t, TFun):
        return TFun(_norm(t.arg, param, head, ats),
                    _norm(t.ret, param, head, ats))
    if isinstance(t, TApp):
        # Check if this is an associated type application
        inner = t
        name_parts: list[str] = []
        args: list[Type] = []
        while isinstance(inner, TApp):
            args.append(inner.arg)
            inner = inner.fn
        if isinstance(inner, TCon) and inner.name in ats:
            # Resolve: Elem Int → String (after substituting head_type for param)
            return _subst_type(ats[inner.name], param, head)
        # Not an assoc type: recurse
        return TApp(_norm(t.fn, param, head, ats),
                    _norm(t.arg, param, head, ats))
    return t


def _subst_type(t: Type, param: Type, replacement: Type) -> Type:
    """Substitute ``param`` with ``replacement`` in ``t``."""
    if isinstance(t, TVar):
        return replacement if t == param else t
    if isinstance(t, TCon):
        return t
    if isinstance(t, TFun):
        return TFun(_subst_type(t.arg, param, replacement),
                    _subst_type(t.ret, param, replacement))
    if isinstance(t, TApp):
        return TApp(_subst_type(t.fn, param, replacement),
                    _subst_type(t.arg, param, replacement))
    return t


