"""Kind checking.

Kind is a separate, smaller type-level discipline that validates
type expressions before value-level inference.  It uses the same
structural rules as the type checker but over kind terms instead of
type terms.

    Kind := KType      -- the kind of inhabited types (Int, Bool, Maybe Int)
          | KInt       -- the kind of integer-like types (bounded/cyclic)
          | KFun(Kind, Kind)  -- type constructor kinds (Maybe: Type -> Type)

A well-kinded type expression like ``Maybe Int`` has kind ``Type``
because ``Maybe : Type -> Type`` and ``Int : Type``.  The checker
rejects nonsense like ``Maybe Maybe`` (``Type -> Type`` applied to
``Type -> Type`` — the arg kind must be ``Type``).
"""

from __future__ import annotations

from dataclasses import dataclass

from .syntax.ast import Val, VConId, VInfix, VKind
from .types import TApp, TCon, TFun, TInt, TVar, Type
from .declarations import ConInfo, DeclError


# ---------------------------------------------------------------------------
# Kind terms
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KType:
    """The kind of ordinary (inhabited) types."""
    def __repr__(self):
        return "Type"


@dataclass(frozen=True)
class KInt:
    """The kind of integer-like types (bounded/cyclic integers)."""
    def __repr__(self):
        return "Int"


@dataclass(frozen=True)
class KFun:
    """The kind of a type constructor: ``arg -> ret``."""
    arg: Kind
    ret: Kind

    def __repr__(self):
        return f"({self.arg} -> {self.ret})"


Kind = KType | KInt | KFun


# ---------------------------------------------------------------------------
# Kind-environment construction
# ---------------------------------------------------------------------------

def desugar_kind(val: Val) -> Kind:
    """Convert a surface kind-expression ``Val`` to a ``Kind``."""
    if isinstance(val, VConId):
        if val.value == "Type":
            return KType()
        if val.value == "Int":
            return KInt()
        raise DeclError(f"Unknown kind atom: {val.value}")
    if isinstance(val, VInfix):
        if val.op == "->":
            return KFun(desugar_kind(val.left), desugar_kind(val.right))
        raise DeclError(f"Unexpected infix operator in kind: {val.op}")
    raise DeclError(f"Unsupported kind expression: {type(val).__name__}")


_BUILTIN_KINDS: dict[str, Kind] = {
    "Int": KType(),
    # Double-precision, and *not* a `Num` default: a literal with a point
    # in it is a `Float` and one without is an `Int`.  Nothing is defaulted
    # (`fixme.md` F84).
    "Float": KType(),
    # `Char` is a code point, represented as an integer.  `String` is not
    # here: it is a built-in *alias* for `List Char` (`declarations.py`),
    # expanded before anything asks for its kind.
    "Char": KType(),
    "Sig": KFun(KType(), KType()),
    "Chan": KFun(KType(), KType()),
    # The two later modalities.  ``FaL A`` is Rizzo's ⃝∀A — a delayed
    # computation that produces an ``A`` whenever *any* clock ticks;
    # ``ExL A`` is ⃝∃A — one that produces an ``A`` when *its own* clock
    # ticks.  Signal tails, ``wait``, ``watch``, ``sync`` and ``never``
    # all live at ⃝∃; ``delay`` and ``gfix``'s binder live at ⃝∀.
    "FaL": KFun(KType(), KType()),
    "ExL": KFun(KType(), KType()),
    # ``watch`` observes a partial signal and ``sync`` returns a three-way
    # join, so both types are part of the FRP interface rather than library
    # code the user could supply.
    "Maybe": KFun(KType(), KType()),
    "Sync": KFun(KType(), KFun(KType(), KType())),
    "Set": KFun(KType(), KType()),
    "Box": KFun(KType(), KType()),
    "List": KFun(KType(), KType()),
    "Bool": KType(),
    # `Void` is the uninhabited type, and builtin because the `:=` syntax
    # cannot declare one — a declaration needs at least one constructor.
    # Its use is `[: Void :]`, a score with no *unassigned* notes: since
    # `[: a :]` means "unassigned notes carry `a`" and nothing inhabits
    # `Void`, there can be none.  That is `spec/music.md`'s performability
    # condition said at rank 1, `forall b. [: b :]` needing rank 2.
    "Void": KType(),
    "Score": KFun(KType(), KType()),
    "Cyclic": KFun(KInt(), KType()),
    "Bounded": KFun(KInt(), KFun(KInt(), KType())),
}

#: `TupleN : * -> … -> *`, one constructor per width.  Eight is arbitrary and
#: generous; the parser has no limit, so a wider tuple is a kind error rather
#: than a crash.  Width 0 is the unit type `1` (`Tuple0 : *`); width 1 does
#: not exist, since `(A)` is just `A`.
for _n in [0, *range(2, 9)]:
    _k: Kind = KType()
    for _ in range(_n):
        _k = KFun(KType(), _k)
    _BUILTIN_KINDS[f"Tuple{_n}"] = _k
del _n, _k

#: Names a user program may not redefine as a type alias.
#: `String` is not a kind — it is a built-in alias for `List Char` — but a
#: user may not redeclare it either.
BUILTIN_TYPE_NAMES: frozenset[str] = frozenset(_BUILTIN_KINDS) | {"String"}


def build_kind_env(
    adt_cons: dict[str, ConInfo],
    kind_decls: list[VKind],
) -> dict[str, Kind]:
    """Build the initial kind environment.

    Sources (in priority order):
    1. Built-in types (Int, String, etc.)
    2. Explicit kind declarations (``kind Cyclic : Int -> Type``)
    3. ADT declarations (inferred from the number of type parameters)

    Every type constructor mentioned in the program must have a known kind.
    """
    env: dict[str, Kind] = dict(_BUILTIN_KINDS)

    # Kind declarations
    for kd in kind_decls:
        env[kd.name] = desugar_kind(kd.kind)

    # ADT declarations: derive from collected constructor info.
    # We need the ADT name and arity; infer from the constructor types.
    seen_adts: set[str] = set()
    for ci in adt_cons.values():
        # Walk the constructor's return type to find the ADT name.
        adt_name = _adt_name_from_con_type(ci.type_)
        if adt_name is None or adt_name in seen_adts:
            continue
        seen_adts.add(adt_name)
        # Arity = number of type parameters = number of ADT param TVars.
        arity = _count_adt_params(ci.type_)
        if adt_name not in env:
            env[adt_name] = _make_adt_kind(arity)

    return env


def _adt_name_from_con_type(t: Type) -> str | None:
    """Extract the ADT name from a constructor's type template.

    For ``Just : a -> Maybe a``, the return type is ``TApp(TCon("Maybe"), TVar(-1))``,
    and the ADT name is ``"Maybe"``.
    """
    # Unwrap TFun chain to get the return type.
    while isinstance(t, TFun):
        t = t.ret
    # Unwrap TApp chain to get the base type constructor.
    while isinstance(t, TApp):
        t = t.fn
    if isinstance(t, TCon):
        return t.name
    return None


def _count_adt_params(t: Type) -> int:
    """Count the number of distinct ADT type parameters in a constructor type."""
    while isinstance(t, TFun):
        t = t.ret
    params: set[int] = set()
    _collect_adt_params(t, params)
    return len(params)


def _collect_adt_params(t: Type, acc: set[int]) -> None:
    if isinstance(t, TVar) and t.id < 0:
        acc.add(t.id)
    elif isinstance(t, TApp):
        _collect_adt_params(t.fn, acc)
        _collect_adt_params(t.arg, acc)
    elif isinstance(t, TFun):
        _collect_adt_params(t.arg, acc)
        _collect_adt_params(t.ret, acc)


def _is_int_literal(name: str) -> bool:
    """Check if a TCon name represents a type-level integer literal."""
    return name.lstrip('-').isdigit()


def _make_adt_kind(arity: int) -> Kind:
    """``arity=0`` → ``Type``, ``arity=1`` → ``Type -> Type``, etc."""
    k: Kind = KType()
    for _ in range(arity):
        k = KFun(KType(), k)
    return k


# ---------------------------------------------------------------------------
# Kind checking
# ---------------------------------------------------------------------------

class KindError(Exception):
    pass


def _refuse_a_type_in_lowercase(var: TVar, env: dict[str, Kind]) -> None:
    """`foo : int` — the type wearing the wrong case.

    **Reported by gestate's first outside user** (`fixme.md` F141), who
    wrote `foo : int` and could not see why it did not work.  Nothing
    was broken: a name that begins with a lowercase letter *is* a type
    variable, so the signature was a legal polymorphic one over a
    variable that happens to be spelled like a type — and the file
    analysed without a word about `int`.

    What made it worse than silence is what the compiler said next.
    The complaint surfaced wherever the variable failed to satisfy a
    class — *"No instance for Num int — 'int' is a signature variable;
    write '(Num int) => …' in the signature"* — which is a correct
    sentence about the program that was written and **advice towards
    the wrong fix**: taking it makes the mistake permanent.

    So the case is caught at the signature, where the person can still
    read it as a typo.  It fires only on an exact case-insensitive
    match with a type this program actually has, which is what makes it
    a typo rather than a guess: `a`, `m` and `k` name nothing, and
    `int` names `Int`.  A variable genuinely wanted under such a name
    has to be spelled differently, and that is the price — paid on the
    rare side of a trade whose common side is this report.
    """
    if not var.name or not var.name.islower():
        return
    meant = next((known for known in env
                  if known != var.name and known.lower() == var.name.lower()),
                 None)
    if meant is None:
        return
    # The same reading `infer._at` does, and the same spelling: a span is
    # either a pair or a position, and `(at line:col)` is the form the
    # assembler re-bases and the editor's margin reads back out.
    span = getattr(var, "span", None)
    start = getattr(span, "start", span)
    line, col = getattr(start, "line", None), getattr(start, "col", None)
    where = "" if line is None or col is None else f" (at {line}:{col})"
    raise KindError(
        f"`{var.name}` is a type variable, not the type `{meant}`{where} — "
        f"a name in lowercase stands for whatever type the caller picks. "
        f"Write `{meant}` if that is the type you meant, or rename the "
        f"variable if it is not."
    )


def check_kind(texpr: Type, env: dict[str, Kind]) -> Kind:
    """Check that ``texpr`` is well-kinded and return its kind.

    Raises ``KindError`` if the type expression is ill-kinded.
    """
    if isinstance(texpr, (TVar, TInt)):
        # Type variables and type-level integers have default kind
        if isinstance(texpr, TVar):
            _refuse_a_type_in_lowercase(texpr, env)
            return KType()
        return KInt()
    if isinstance(texpr, TCon):
        if texpr.name not in env:
            if _is_int_literal(texpr.name):
                return KInt()
            raise KindError(f"Unknown type constructor: {texpr.name}")
        return env[texpr.name]
    if isinstance(texpr, TApp):
        # **A type *variable* in function position is a constructor
        # variable**, and its kind is whatever the application needs.
        #
        # Every `TVar` is given kind `Type` above, because there is no kind
        # *inference* here — only checking.  That is right for the argument
        # of a function type and wrong the moment a signature quantifies
        # over a container: `join : (Monad m) => m (m a) -> m a` asks for
        # `m : Type -> Type`, and nothing in the signature says so in a
        # form this pass could read.  Rejecting it made every higher-kinded
        # class impossible to *use*, even though declaring one already
        # worked — `class Monad m` checked, and the first ordinary function
        # written against it did not.
        #
        # So the spine's head decides: a variable there is accepted at the
        # kind it is used at.  This is a deliberate loosening — it admits a
        # signature a real kind inferencer would reject, such as one using
        # `m` at two different arities — and the alternative is having no
        # higher-kinded signatures at all.  The type checker still catches
        # the consequences, because such a signature has no instance that
        # can satisfy it.
        head = texpr.fn
        while isinstance(head, TApp):
            head = head.fn
        if isinstance(head, TVar):
            check_kind(texpr.arg, env)
            return KType()
        fn_k = check_kind(texpr.fn, env)
        arg_k = check_kind(texpr.arg, env)
        if not isinstance(fn_k, KFun):
            raise KindError(
                f"Type {texpr.fn} has kind {fn_k} "
                f"(expected a type-constructor kind like Type -> Type)"
            )
        if fn_k.arg != arg_k:
            raise KindError(
                f"Kind mismatch in {texpr}: "
                f"expected argument of kind {fn_k.arg}, got {arg_k}"
            )
        return fn_k.ret
    if isinstance(texpr, TFun):
        ak = check_kind(texpr.arg, env)
        rk = check_kind(texpr.ret, env)
        if ak != KType():
            raise KindError(
                f"Function argument type must have kind Type, got {ak} in {texpr}"
            )
        if rk != KType():
            raise KindError(
                f"Function return type must have kind Type, got {rk} in {texpr}"
            )
        return KType()
    raise KindError(f"Unknown type expression: {type(texpr).__name__}")
