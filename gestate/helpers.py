"""Datafun helper generation — per-type operations on canonical sorted cons-lists.

For each concrete set type appearing in the program, generates recursive
supercombinators for equality, union, bottom, and join.  The helpers use
the synthetic ``List a`` ADT (Nil/Cons) for the set representation.
"""

from __future__ import annotations

from .expr import (
    ETuple,
    Alter,
    EAp,
    ECase,
    ECon,
    EGlobal,
    ELambda,
    ELet,
    EProj,
    EVar,
    Expr,
)
from .gmachine import EqInt, LtInt
from .declarations import ConInfo
from .types import TApp, TCon, TFun, TVar, Type, tuple_parts


def make_tag_of(cons: dict[str, ConInfo], name: str) -> int:
    """Look up the tag for a synthetic constructor name."""
    return cons[name].tag


def _spine(t: Type) -> tuple[Type, list[Type]]:
    args: list[Type] = []
    while isinstance(t, TApp):
        args.insert(0, t.arg)
        t = t.fn
    return t, args


def _type_suffix(t: Type) -> str:
    """Render a concrete type as a string suffix for SC names."""
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TApp):
        return f"{_type_suffix(t.fn)}_{_type_suffix(t.arg)}"
    return str(t).replace(" ", "_").replace("(", "").replace(")", "")


# ---------------------------------------------------------------------------
# Per-type helper generators
# ---------------------------------------------------------------------------

def _nil(nil_tag: int) -> Expr:
    return ECon(nil_tag, [])


def _cons(cons_tag: int, hd: Expr, tl: Expr) -> Expr:
    return ECon(cons_tag, [hd, tl])


def _bool_true(true_tag: int) -> Expr:
    return ECon(true_tag, [])


def _bool_false(false_tag: int) -> Expr:
    return ECon(false_tag, [])


def _var(name: str) -> Expr:
    return EVar(name)


# ---------------------------------------------------------------------------
# Element comparison
# ---------------------------------------------------------------------------
#
# A set is a *sorted* cons-list, so every set operation needs `=` and `<` on
# its elements.  These used to be `prim_eq_int`/`prim_lt_int` regardless of
# the element type (`fixme.md` F11), which confined Datafun to sets of
# integers — and so ruled out a set of pairs, which is what a Datalog
# relation is.
#
# The comparator is generated *structurally* from the element type rather
# than resolved through an `Eq`/`Ord` dictionary.  The helpers are emitted
# after elaboration, so no dictionary is in scope; and they are already
# monomorphic per type, so a monomorphic comparator is the consistent
# choice (`spec/errata.md` D9's option (a)).

def _elem_eq(elem: Type) -> Expr:
    return EGlobal(f"eqE_{_type_suffix(elem)}")


def _elem_lt(elem: Type) -> Expr:
    return EGlobal(f"ltE_{_type_suffix(elem)}")


def _eq_int(l: Expr, r: Expr, true_tag: int, false_tag: int) -> Expr:
    return EAp(EAp(EGlobal("prim_eq_int"), l), r)


def _lt_int(l: Expr, r: Expr, true_tag: int, false_tag: int) -> Expr:
    return EAp(EAp(EGlobal("prim_lt_int"), l), r)


def _case_of(scrut: Expr, alts: list[tuple[int, list[str], Expr]]) -> Expr:
    """Build an ``ECase`` from (tag, names, body) tuples."""
    return ECase(scrut, [Alter(t, n, b) for t, n, b in alts])


# ---------------------------------------------------------------------------
# eqA — structural equality on sorted cons-lists
# ---------------------------------------------------------------------------

def _gen_eq(suffix: str, elem: Type, nil_tag: int, cons_tag: int,
            true_tag: int, false_tag: int) -> tuple[str, int, ELambda]:
    name = f"eq_{suffix}"
    x = _var("x")
    y = _var("y")
    h1, t1 = _var("h1"), _var("t1")
    h2, t2 = _var("h2"), _var("t2")

    body = _case_of(x, [
        (nil_tag, [], _case_of(y, [
            (nil_tag, [], _bool_true(true_tag)),
            (cons_tag, ["_", "_"], _bool_false(false_tag)),
        ])),
        (cons_tag, ["h1", "t1"], _case_of(y, [
            (nil_tag, [], _bool_false(false_tag)),
            (cons_tag, ["h2", "t2"], _case_of(
                EAp(EAp(_elem_eq(elem), h1), h2),
                [(true_tag, [], EAp(EAp(EGlobal(name), t1), t2)),
                 (false_tag, [], _bool_false(false_tag))],
            )),
        ])),
    ])
    return (name, 2, ELambda(["x", "y"], body))


def _gen_union(suffix: str, elem: Type, nil_tag: int, cons_tag: int,
               true_tag: int, false_tag: int) -> tuple[str, int, ELambda]:
    name = f"union_{suffix}"
    x = _var("x")
    y = _var("y")
    h1, t1 = _var("h1"), _var("t1")
    h2, t2 = _var("h2"), _var("t2")

    body = _case_of(x, [
        (nil_tag, [], y),
        (cons_tag, ["h1", "t1"], _case_of(y, [
            (nil_tag, [], x),
            (cons_tag, ["h2", "t2"], _case_of(
                EAp(EAp(_elem_lt(elem), h1), h2),
                [(true_tag, [], _cons(cons_tag, h1, EAp(EAp(EGlobal(name), t1), y))),
                 (false_tag, [], _case_of(
                     EAp(EAp(_elem_eq(elem), h1), h2),
                     [(true_tag, [], _cons(cons_tag, h1, EAp(EAp(EGlobal(name), t1), t2))),
                      (false_tag, [], _cons(cons_tag, h2, EAp(EAp(EGlobal(name), x), t2)))],
                 ))],
            )),
        ])),
    ])
    return (name, 2, ELambda(["x", "y"], body))


def _gen_bottom(suffix: str, nil_tag: int) -> tuple[str, int, ELambda]:
    return (f"bottom_{suffix}", 0, ELambda([], _nil(nil_tag)))


def _gen_subset(suffix: str) -> tuple[str, int, ELambda]:
    """Generate: subset_X a b = eq_X (union_X a b) b

    `a ⊑ b` iff `a ∪ b = b`.  Reusing the two helpers that already exist
    keeps this O(|a| + |b|), the same order as the equality test it
    replaces in `semifixL`.
    """
    name = f"subset_{suffix}"
    a, b = _var("a"), _var("b")
    body = EAp(EAp(EGlobal(f"eq_{suffix}"),
                   EAp(EAp(EGlobal(f"union_{suffix}"), a), b)), b)
    return (name, 2, ELambda(["a", "b"], body))


def _gen_join(suffix: str) -> tuple[str, int, ELambda]:
    name = f"join_{suffix}"
    return (name, 2, ELambda(["x", "y"],
            EAp(EAp(EGlobal(f"union_{suffix}"), _var("x")), _var("y"))))


# ---------------------------------------------------------------------------
# fix — semilattice fixed point (naïve iteration)
# ---------------------------------------------------------------------------

def _gen_diff(suffix: str, elem: Type, nil_tag: int, cons_tag: int,
              true_tag: int, false_tag: int) -> tuple[str, int, ELambda]:
    """``diff_X dx x`` — the elements of ``dx`` that are not already in ``x``.

    This is `\\L` from the thesis §4.3, the *change minimizer*.  Both
    operands are sorted, so it is one merge pass.

    Its law is "if `dx ▷ x ,→ y : L` then `dx \\L x ▷ x ,→ y : L`": removing
    what `x` already contains does not change where the step lands, because
    `x ∨ dx = x ∨ (dx \\ x)`.  What it does change is what the *next*
    iteration iterates over — see `seminaive.make_semifix_helpers`.
    """
    name = f"diff_{suffix}"
    dx, x = _var("dx"), _var("x")
    h1, t1 = _var("h1"), _var("t1")
    h2, t2 = _var("h2"), _var("t2")

    body = _case_of(dx, [
        (nil_tag, [], _nil(nil_tag)),
        (cons_tag, ["h1", "t1"], _case_of(x, [
            # Nothing left to subtract: the rest of `dx` is all new.
            (nil_tag, [], dx),
            (cons_tag, ["h2", "t2"], _case_of(
                EAp(EAp(_elem_lt(elem), h1), h2),
                # h1 < h2: h1 cannot appear later in the sorted `x`.
                [(true_tag, [], _cons(cons_tag, h1,
                                      EAp(EAp(EGlobal(name), t1), x))),
                 (false_tag, [], _case_of(
                     EAp(EAp(_elem_eq(elem), h1), h2),
                     # h1 == h2: already known, drop it.
                     [(true_tag, [], EAp(EAp(EGlobal(name), t1), t2)),
                      # h1 > h2: advance `x`.
                      (false_tag, [], EAp(EAp(EGlobal(name), dx), t2))]))])),
        ])),
    ])
    return (name, 2, ELambda(["dx", "x"], body))


def _gen_fix(suffix: str, nil_tag: int, cons_tag: int,
             true_tag: int, false_tag: int) -> tuple[str, int, ELambda]:
    """Generate: fix_X p = fixLoop_X bottom_X (#0 p)
         fixLoop_X cur f =
           let next = f cur
           in case eq_X next cur of
                True  -> cur
                False -> fixLoop_X next f

    `fix` takes a *boxed* function (`spec/data.md` §I.5), and a box is the
    pair `(base, change)` at runtime — the representation ϕ/δ needs, which
    the naive path shares so a box can cross between them (§17).  The
    naive loop only ever wants the base point.
    """
    fix_name = f"fix_{suffix}"
    loop_name = f"fixLoop_{suffix}"
    f = _var("f")
    cur = _var("cur")
    nxt = _var("next")

    fixloop_body = ELet(False, [("next", EAp(f, cur))],
        _case_of(EAp(EAp(EGlobal(f"eq_{suffix}"), nxt), cur), [
            (true_tag, [], cur),
            (false_tag, [],
             EAp(EAp(EGlobal(loop_name), nxt), f)),
        ]))

    fix_body = EAp(EAp(EGlobal(loop_name), EGlobal(f"bottom_{suffix}")),
                   EAp(EProj(0), _var("p")))

    return (loop_name, 2, ELambda(["cur", "f"], fixloop_body)), \
           (fix_name, 1, ELambda(["p"], fix_body))


# ---------------------------------------------------------------------------
# for — set comprehension (fold + join)
# ---------------------------------------------------------------------------

def _gen_for(suffix: str, nil_tag: int, cons_tag: int) -> tuple[str, int, ELambda]:
    """Generate: for_X set f = case set of
         Nil      -> bottom_X
         Cons h t -> join_X (f h) (for_X t f)
    """
    name = f"for_{suffix}"
    s = _var("set")
    f = _var("f")
    h, t = _var("h"), _var("t")

    body = _case_of(s, [
        (nil_tag, [], EGlobal(f"bottom_{suffix}")),
        (cons_tag, ["h", "t"],
         EAp(EAp(EGlobal(f"join_{suffix}"),
                 EAp(f, h)),
             EAp(EAp(EGlobal(name), t), f))),
    ])
    return (name, 2, ELambda(["set", "f"], body))


# ---------------------------------------------------------------------------
# generate_helpers — updated entry point
# ---------------------------------------------------------------------------

class HelperError(Exception):
    pass


#: Element types the generated `eq`/`union` can compare.  They keep and
#: sort the set as a cons-list using `prim_eq_int`/`prim_lt_int`, so the
#: elements have to *be* integers at run time.  A wider set needs element
#: comparison to dispatch through `Eq`/`Ord` — `fixme.md` F11.

# ---------------------------------------------------------------------------
# Generated comparators, one pair per element type
# ---------------------------------------------------------------------------

#: Types whose runtime representation *is* an integer, so the primitives
#: compare them directly.  `Char` is a code point; `Cyclic n` and
#: `lo .. hi` are integers with a normalisation rule.
#: Types whose values are a single number in the heap, so `prim_eq_int` and
#: `prim_lt_int` order them directly.  `Float` is one: the instructions are
#: Python's `==` and `<`, which are correct on either kind of number, and a
#: total order is all a sorted-list set needs.
_INT_LIKE = frozenset({"Int", "Float", "Char", "Cyclic", "Bounded"})


class ComparatorError(Exception):
    pass


def _gen_comparators(elem: Type, cons: dict[str, ConInfo],
                     emitted: set[str]) -> list[tuple[str, int, ELambda]]:
    """``eqE_X`` and ``ltE_X`` for element type ``X``, and for its parts.

    ``ltE`` is a *total order* on the representation, not the semantic
    order: it exists so a set can be kept as a sorted list, and any total
    order will do as long as `eqE` agrees with it.  Products compare
    lexicographically; sets compare as their sorted lists.
    """
    suffix = _type_suffix(elem)
    if suffix in emitted:
        return []
    emitted.add(suffix)

    nil_tag = make_tag_of(cons, "Nil")
    cons_tag = make_tag_of(cons, "Cons")
    true_tag = make_tag_of(cons, "True")
    false_tag = make_tag_of(cons, "False")

    out: list[tuple[str, int, ELambda]] = []
    x, y = _var("x"), _var("y")
    head, args = _spine(elem)

    if isinstance(head, TCon) and head.name in _INT_LIKE:
        out.append((f"eqE_{suffix}", 2,
                    ELambda(["x", "y"], _eq_int(x, y, true_tag, false_tag))))
        out.append((f"ltE_{suffix}", 2,
                    ELambda(["x", "y"], _lt_int(x, y, true_tag, false_tag))))
        return out

    if isinstance(head, TCon) and head.name == "Bool":
        # `False < True`, matching the constructor order.
        out.append((f"eqE_{suffix}", 2, ELambda(["x", "y"], _case_of(x, [
            (false_tag, [], _case_of(y, [(false_tag, [], _bool_true(true_tag)),
                                         (true_tag, [], _bool_false(false_tag))])),
            (true_tag, [], _case_of(y, [(false_tag, [], _bool_false(false_tag)),
                                        (true_tag, [], _bool_true(true_tag))])),
        ]))))
        out.append((f"ltE_{suffix}", 2, ELambda(["x", "y"], _case_of(x, [
            (false_tag, [], _case_of(y, [(false_tag, [], _bool_false(false_tag)),
                                         (true_tag, [], _bool_true(true_tag))])),
            (true_tag, [], _bool_false(false_tag)),
        ]))))
        return out

    parts = tuple_parts(elem)
    if parts is not None:
        for part in parts:
            out.extend(_gen_comparators(part, cons, emitted))
        n = len(parts)
        # eq: every component equal.
        conj: Expr = _bool_true(true_tag)
        for i in reversed(range(n)):
            conj = _case_of(
                EAp(EAp(_elem_eq(parts[i]), EAp(EProj(i, n), x)),
                    EAp(EProj(i, n), y)),
                [(true_tag, [], conj), (false_tag, [], _bool_false(false_tag))])
        out.append((f"eqE_{suffix}", 2, ELambda(["x", "y"], conj)))

        # lt: lexicographic — earlier component decides, ties fall through.
        lex: Expr = _bool_false(false_tag)
        for i in reversed(range(n)):
            xi, yi = EAp(EProj(i, n), x), EAp(EProj(i, n), y)
            lex = _case_of(
                EAp(EAp(_elem_lt(parts[i]), xi), yi),
                [(true_tag, [], _bool_true(true_tag)),
                 (false_tag, [], _case_of(
                     EAp(EAp(_elem_eq(parts[i]), xi), yi),
                     [(true_tag, [], lex),
                      (false_tag, [], _bool_false(false_tag))]))])
        out.append((f"ltE_{suffix}", 2, ELambda(["x", "y"], lex)))
        return out

    if isinstance(head, TCon) and head.name == "Set" and args:
        inner = args[0]
        out.extend(_gen_comparators(inner, cons, emitted))
        # A set is its sorted list, so element equality is list equality
        # and the order is lexicographic on that list.
        out.append((f"eqE_{suffix}", 2,
                    ELambda(["x", "y"],
                            EAp(EAp(EGlobal(f"eq_{suffix}"), x), y))))
        h1, t1 = _var("h1"), _var("t1")
        h2, t2 = _var("h2"), _var("t2")
        lt_name = f"ltE_{suffix}"
        body = _case_of(x, [
            (nil_tag, [], _case_of(y, [
                (nil_tag, [], _bool_false(false_tag)),
                (cons_tag, ["_", "_"], _bool_true(true_tag)),
            ])),
            (cons_tag, ["h1", "t1"], _case_of(y, [
                (nil_tag, [], _bool_false(false_tag)),
                (cons_tag, ["h2", "t2"], _case_of(
                    EAp(EAp(_elem_lt(inner), h1), h2),
                    [(true_tag, [], _bool_true(true_tag)),
                     (false_tag, [], _case_of(
                         EAp(EAp(_elem_eq(inner), h1), h2),
                         [(true_tag, [], EAp(EAp(EGlobal(lt_name), t1), t2)),
                          (false_tag, [], _bool_false(false_tag))]))])),
            ])),
        ])
        out.append((lt_name, 2, ELambda(["x", "y"], body)))
        return out

    if isinstance(head, TCon) and cons:
        ctors = _adt_ctors(head.name, args, cons)
        if ctors is not None:
            return out + _gen_adt_comparators(
                suffix, ctors, cons, emitted, nil_tag, cons_tag,
                true_tag, false_tag)

    from .show import show_type
    raise ComparatorError(
        f"a set of {show_type(elem)} cannot be built: the generated set "
        f"operations need a total order on the element type, and one is "
        f"generated only for number-represented types (`Int`, `Float`, "
        f"`Char`, `Cyclic n`, `lo .. hi`), `Bool`, tuples of those, sets of those, "
        f"and data types whose fields are all of those"
    )


def _adt_ctors(name: str, args: list[Type],
               cons: dict[str, ConInfo]) -> list[tuple[int, list[Type]]] | None:
    """``(tag, field types)`` per constructor of ``name``, in tag order.

    ``args`` are the type arguments at *this* use, substituted for the
    declaration's parameters — otherwise `Maybe Int`'s field would be
    judged by `Maybe a`'s `a`, which names no comparator.
    """
    from .types import _apply_subst_map, _spine as _ty_spine, TVar

    found: list[tuple[int, list[Type]]] = []
    for info in cons.values():
        ret = info.type_
        fields: list[Type] = []
        while isinstance(ret, TFun):
            fields.append(ret.arg)
            ret = ret.ret
        rhead, params = _ty_spine(ret)
        if not (isinstance(rhead, TCon) and rhead.name == name):
            continue
        subst = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
        found.append((info.tag, [_apply_subst_map(f, subst) for f in fields]))
    if not found:
        return None
    found.sort(key=lambda c: c[0])
    return found


def _gen_adt_comparators(suffix: str, ctors: list[tuple[int, list[Type]]],
                         cons: dict[str, ConInfo], emitted: set[str],
                         nil_tag: int, cons_tag: int,
                         true_tag: int, false_tag: int):
    """``eqE_T``/``ltE_T`` for a data type: constructor position, then fields.

    The same order `deriving Ord` gives at the surface, and for the same
    reason — the *declaration order* of the constructors is the order, and
    listing the alternatives in that order is what encodes it.  This is a
    total order on the representation, which is all a sorted-list set needs;
    it does not have to agree with any `Ord` instance the user wrote, only
    with `eqE_T`.
    """
    out: list[tuple[str, int, ELambda]] = []
    for _tag, fields in ctors:
        for f in fields:
            out.extend(_gen_comparators(f, cons, emitted))

    def names(prefix: str, fields: list[Type]) -> list[str]:
        return [f"{prefix}{i}" for i in range(len(fields))]

    # eq: same constructor, and every field equal.
    eq_outer: list[tuple[int, list[str], Expr]] = []
    for tag, fields in ctors:
        ls = names("l", fields)
        inner: list[tuple[int, list[str], Expr]] = []
        for tag2, fields2 in ctors:
            rs = names("r", fields2)
            if tag2 != tag:
                inner.append((tag2, rs, _bool_false(false_tag)))
                continue
            conj: Expr = _bool_true(true_tag)
            for f, ln, rn in reversed(list(zip(fields, ls, rs))):
                conj = _case_of(
                    EAp(EAp(_elem_eq(f), _var(ln)), _var(rn)),
                    [(true_tag, [], conj),
                     (false_tag, [], _bool_false(false_tag))])
            inner.append((tag2, rs, conj))
        eq_outer.append((tag, ls, _case_of(_var("y"), inner)))
    out.append((f"eqE_{suffix}", 2,
                ELambda(["x", "y"], _case_of(_var("x"), eq_outer))))

    # lt: earlier constructor is less; a matching pair falls through to the
    # fields, compared lexicographically.
    lt_outer: list[tuple[int, list[str], Expr]] = []
    for i, (tag, fields) in enumerate(ctors):
        ls = names("l", fields)
        inner = []
        for j, (tag2, fields2) in enumerate(ctors):
            rs = names("r", fields2)
            if j < i:
                inner.append((tag2, rs, _bool_false(false_tag)))
            elif j > i:
                inner.append((tag2, rs, _bool_true(true_tag)))
            else:
                lex: Expr = _bool_false(false_tag)
                for f, ln, rn in reversed(list(zip(fields, ls, rs))):
                    lex = _case_of(
                        EAp(EAp(_elem_lt(f), _var(ln)), _var(rn)),
                        [(true_tag, [], _bool_true(true_tag)),
                         (false_tag, [], _case_of(
                             EAp(EAp(_elem_eq(f), _var(ln)), _var(rn)),
                             [(true_tag, [], lex),
                              (false_tag, [], _bool_false(false_tag))]))])
                inner.append((tag2, rs, lex))
        lt_outer.append((tag, ls, _case_of(_var("y"), inner)))
    out.append((f"ltE_{suffix}", 2,
                ELambda(["x", "y"], _case_of(_var("x"), lt_outer))))
    return out



def _gen_product_helpers(prod: Type, parts: list[Type],
                         cons: dict[str, ConInfo], emitted: set[str],
                         nil_tag: int, cons_tag: int,
                         true_tag: int, false_tag: int):
    """`bottom`/`join`/`eq`/`subset`/`diff`/`for` at a product semilattice.

    Each is the componentwise lift of the same operation at the components,
    which is what makes `L × M` a semilattice at all.  The components are
    generated first — they may themselves be products.
    """
    suffix = _type_suffix(prod)
    if suffix in emitted:
        return []
    emitted.add(suffix)

    out: list[tuple[str, int, ELambda]] = []
    for part in parts:
        p_parts = tuple_parts(part)
        if p_parts:
            out.extend(_gen_product_helpers(
                part, p_parts, cons, emitted, nil_tag, cons_tag,
                true_tag, false_tag))
            continue
        elem = _elem_of(part)
        if elem is None:
            from .show import show_type
            raise ComparatorError(
                f"`fix` at {show_type(prod)} needs every component to be a "
                f"semilattice, and {show_type(part)} is not one"
            )
        out.extend(_gen_comparators(elem, cons, emitted))
        ps = _type_suffix(part)
        if ps not in emitted:
            emitted.add(ps)
        out.append(_gen_eq(ps, elem, nil_tag, cons_tag, true_tag, false_tag))
        out.append(_gen_union(ps, elem, nil_tag, cons_tag, true_tag, false_tag))
        out.append(_gen_bottom(ps, nil_tag))
        out.append(_gen_join(ps))
        out.append(_gen_subset(ps))
        out.append(_gen_diff(ps, elem, nil_tag, cons_tag, true_tag, false_tag))

    n = len(parts)
    subs = [_type_suffix(p) for p in parts]
    x, y = _var("x"), _var("y")

    out.append((f"bottom_{suffix}", 0, ELambda(
        [], ETuple([EGlobal(f"bottom_{sp}") for sp in subs]))))

    out.append((f"join_{suffix}", 2, ELambda(["x", "y"], ETuple([
        EAp(EAp(EGlobal(f"join_{sp}"), EAp(EProj(i, n), x)),
            EAp(EProj(i, n), y))
        for i, sp in enumerate(subs)]))))

    out.append((f"diff_{suffix}", 2, ELambda(["x", "y"], ETuple([
        EAp(EAp(EGlobal(f"diff_{sp}"), EAp(EProj(i, n), x)),
            EAp(EProj(i, n), y))
        for i, sp in enumerate(subs)]))))

    def _conj(op: str) -> Expr:
        acc: Expr = _bool_true(true_tag)
        for i in reversed(range(n)):
            acc = _case_of(
                EAp(EAp(EGlobal(f"{op}_{subs[i]}"), EAp(EProj(i, n), x)),
                    EAp(EProj(i, n), y)),
                [(true_tag, [], acc), (false_tag, [], _bool_false(false_tag))])
        return acc

    out.append((f"eq_{suffix}", 2, ELambda(["x", "y"], _conj("eq"))))
    out.append((f"subset_{suffix}", 2, ELambda(["x", "y"], _conj("subset"))))
    out.append(_gen_for(suffix, nil_tag, cons_tag))
    loop, fix = _gen_fix(suffix, nil_tag, cons_tag, true_tag, false_tag)
    out.append(loop)
    out.append(fix)
    return out


def generate_all_helpers(
    set_types: list[Type],
    cons: dict[str, ConInfo],
) -> list[tuple[str, int, ELambda]]:
    """Generate all Datafun helpers for each concrete set type."""
    nil_tag = make_tag_of(cons, "Nil")
    cons_tag = make_tag_of(cons, "Cons")
    true_tag = make_tag_of(cons, "True")
    false_tag = make_tag_of(cons, "False")

    results: list[tuple[str, int, ELambda]] = []
    emitted: set[str] = set()
    for st in set_types:
        parts = tuple_parts(st)
        if parts:
            # A *product* of semilattices is a semilattice, ordered
            # componentwise (`data.md` §I.2, lemma 20), and `fix` accepts
            # one — which is how a Datalog query computes two relations at
            # once (`fixme.md` F37).  Everything `semifix` needs of a
            # semilattice distributes over the components.
            results.extend(_gen_product_helpers(
                st, parts, cons, emitted, nil_tag, cons_tag,
                true_tag, false_tag))
            continue
        elem = _elem_of(st)
        if elem is None:
            continue
        results.extend(_gen_comparators(elem, cons, emitted))
        suffix = _type_suffix(st)
        results.append(_gen_eq(suffix, elem, nil_tag, cons_tag, true_tag, false_tag))
        results.append(_gen_union(suffix, elem, nil_tag, cons_tag, true_tag, false_tag))
        results.append(_gen_bottom(suffix, nil_tag))
        results.append(_gen_join(suffix))
        results.append(_gen_subset(suffix))
        results.append(_gen_diff(suffix, elem, nil_tag, cons_tag,
                                 true_tag, false_tag))
        loop, fix = _gen_fix(suffix, nil_tag, cons_tag, true_tag, false_tag)
        results.append(loop)
        results.append(fix)
        results.append(_gen_for(suffix, nil_tag, cons_tag))
    return results


def _elem_of(set_type: Type) -> Type | None:
    """The element type of ``Set A``, or ``None`` if this is not a set type."""
    if (isinstance(set_type, TApp) and isinstance(set_type.fn, TCon)
            and set_type.fn.name == "Set"):
        return set_type.arg
    return None
