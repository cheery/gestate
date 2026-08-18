"""Instance coherence — overlap and the Paterson conditions.

Implements ``spec/typeclasses.md`` §4 and §5.1.  Both checks run at
instance-declaration time (from ``classify``), so a conflict is reported
where the offending instance is written rather than at some later,
ambiguous call site.

*Overlap*: with one instance per ``(class, type)`` pair, two instance
heads of the same class may never unify — if they do, some concrete
predicate would match both and resolution would not be deterministic.

*Paterson conditions*: every predicate in an instance context must be
structurally smaller than the head, which makes the resolution body
strictly decreasing and instance resolution terminating.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .show import name_vars, show_predicate
from .types import Predicate, TApp, TCon, TFun, TInt, TVar, Type
from .syntax.ast import at as _at
from .unify import UnifyError, unify

if TYPE_CHECKING:  # `declarations` imports this module — annotations only
    from .declarations import ClassInfo, InstanceInfo


#: complaint  author — an instance as written, placed at its head
class CoherenceError(Exception):
    pass


def check_instances(instances: list[InstanceInfo],
                    classes: dict[str, ClassInfo] | None = None) -> None:
    """Check every instance for unknown classes, overlap, and Paterson."""
    if classes is not None:
        for inst in instances:
            _check_classes_exist(inst, classes)
    _check_overlap(instances)
    for inst in instances:
        check_paterson(inst)


# ---------------------------------------------------------------------------
# Known classes
# ---------------------------------------------------------------------------

def _check_classes_exist(inst: InstanceInfo,
                         classes: dict[str, ClassInfo]) -> None:
    if inst.class_name not in classes:
        raise CoherenceError(
            f"Instance for unknown class '{inst.class_name}'{_where(inst)}"
        )
    for pred in inst.context:
        if pred.class_name not in classes:
            raise CoherenceError(
                f"Unknown class '{pred.class_name}' in the context of "
                f"instance {inst}{_where(inst)}"
            )


# ---------------------------------------------------------------------------
# Overlap
# ---------------------------------------------------------------------------

def _check_overlap(instances: list[InstanceInfo]) -> None:
    """Reject two instances of one class whose heads can unify.

    Contexts are deliberately ignored: an instance context restricts when
    an instance *applies*, not which predicates it matches, so two heads
    that unify overlap however their contexts differ.
    """
    for i, later in enumerate(instances):
        for earlier in instances[:i]:
            if earlier.class_name != later.class_name:
                continue
            if not _heads_unify(earlier.head_type, later.head_type):
                continue
            # Blame the declared instance, not a built-in one.
            offender, other = (earlier, later) if later.builtin \
                else (later, earlier)
            raise CoherenceError(
                f"Overlapping instances for class {later.class_name}: "
                f"{_describe(offender)} overlaps {_describe(other)}"
                f"{_where(offender)}"
            )


def _heads_unify(a: Type, b: Type) -> bool:
    """Could some concrete type match both heads?

    Instance variables are rigid within an instance but stand for "any
    type" when asking whether two heads can be matched by one predicate,
    which is exactly what unification decides.  The heads of two
    instances never share variable ids (each declaration draws fresh
    ones), so no renaming is needed.
    """
    try:
        unify(a, b)
    except UnifyError:
        return False
    return True


# ---------------------------------------------------------------------------
# Paterson conditions (spec/typeclasses.md §5.1)
# ---------------------------------------------------------------------------

def check_paterson(inst: InstanceInfo) -> None:
    """Check the three Paterson conditions on ``inst``'s context."""
    if not inst.context:
        return

    head = inst.head_type
    head_cons = _count_constructors(head)
    head_vars = _var_occurrences(head)
    names = name_vars([head] + [p.type_ for p in inst.context])

    for predicate in inst.context:
        pred = show_predicate(predicate, names)
        si = predicate.type_

        # (1) no more type constructors than the head
        cons = _count_constructors(si)
        if cons > head_cons:
            raise CoherenceError(
                f"Paterson condition 1 violated in instance {inst}: the "
                f"context predicate '{pred}' has {cons} type constructor(s) "
                f"but the head has only {head_cons}{_where(inst)}"
            )

        # (2) every type variable occurs in the head
        occurrences = _var_occurrences(si)
        for vid, count in occurrences.items():
            if vid not in head_vars:
                raise CoherenceError(
                    f"Paterson condition 2 violated in instance {inst}: the "
                    f"context predicate '{pred}' mentions type variable "
                    f"'{names[vid]}', which does not occur in the "
                    f"head{_where(inst)}"
                )

            # (3) not more often than in the head
            if count > head_vars[vid]:
                raise CoherenceError(
                    f"Paterson condition 3 violated in instance {inst}: the "
                    f"context predicate '{pred}' repeats type variable "
                    f"'{names[vid]}' {count} time(s) but the head has it "
                    f"{head_vars[vid]} time(s){_where(inst)}"
                )


def _count_constructors(t: Type) -> int:
    """Type constructors (including ``->``) in ``t``."""
    if isinstance(t, (TCon, TInt)):
        return 1
    if isinstance(t, TFun):
        return 1 + _count_constructors(t.arg) + _count_constructors(t.ret)
    if isinstance(t, TApp):
        return _count_constructors(t.fn) + _count_constructors(t.arg)
    return 0


def _var_occurrences(t: Type, acc: dict[int, int] | None = None) -> dict[int, int]:
    """How often each type variable occurs in ``t``."""
    if acc is None:
        acc = {}
    if isinstance(t, TVar):
        acc[t.id] = acc.get(t.id, 0) + 1
    elif isinstance(t, TFun):
        _var_occurrences(t.arg, acc)
        _var_occurrences(t.ret, acc)
    elif isinstance(t, TApp):
        _var_occurrences(t.fn, acc)
        _var_occurrences(t.arg, acc)
    return acc


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def _describe(inst: InstanceInfo) -> str:
    return f"'{inst}'" + (" (built-in)" if inst.builtin else "")


#: ` (at line:col)` for an instance — the third copy of six lines that
#: are now `syntax.ast.at`, and kept under this name because six call
#: sites in this file read better with it.
_where = _at
