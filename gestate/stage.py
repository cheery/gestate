"""Stage one — a type computed from a value, before the program is checked.

`card:strict-forms.md` §"Decided — 2026-09-14".  Two forms reach here:

    type Row = $(kindRow markKind)        a splice: `e` is a `Type` value
    board = document "mark"             a document: its row, by `kindRow`

**The rule, in one line: a program may be computed but never patched.**
What this module does is run *part of the program itself* — the
definitions a splice needs, with the preludes in front of them — through
the ordinary compiler and the G-machine, read the `Type` value back, and
put it into the type grammar where the author wrote the splice.  Then
the whole program is checked as any program is.  Nothing dynamic
reaches the checker, the fixpoint or the two machines: they see the
second stage only.

**What is stage one.**  On demand, Zig's way and Henri's answer to Q7:
no marker in the file.  An item that holds a splice or a `document` is
stage two, and so is everything that mentions it, transitively — those
items are blanked, line for line so every position holds, and what is
left is compiled once with the splice expressions appended as globals.
A splice whose expression needs a stage-two item is refused with both
names: a type computed from a value cannot be computed from itself.

**What it costs.**  One more front end and back half over stage one's
items — the library stack answered from its cache
(`pipeline._stack_front`), the items never re-parsed — once per
distinct program text, inside that text's own analysis.  Stage one is
items and never text: it reads no source, cuts no seam and takes no
lock, which is the postcondition of `card:strict-forms.md` §"Read —
2026-09-18", item 1.  A program with neither form pays a substring
test.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass, replace

from .syntax.ast import (
    Span, Val, VApp, VConId, VInfix, VNum, VPrefix, VSCDecl, VSCEqn, VSig,
    VStr, VTuple, VTypeDecl, VWord,
)

#: The splice operator, and the word a document is read through.
SPLICE = "$"
DOCUMENT = "document"


#: complaint  author — a stage-one expression the author wrote, on the line of the splice or the `document` that needed it: not a type, a kind the program does not declare, a definition that depends on the type it computes
class StageError(Exception):
    """Stage one refused: the splice is not a type, the kind is not
    declared, or the value depends on what it types."""


# ── A generic walk over the surface syntax ──────────────────────────────────

def _map(node, f):
    """`node` with every `Val` for which `f` answers replaced by the
    answer, top-down; field-driven so it stays total as node kinds are
    added (`desugar._val_children` makes the same argument)."""
    if isinstance(node, Val):
        got = f(node)
        if got is not None:
            return got
    return _rebuild(node, f)


def _rebuild(node, f):
    if isinstance(node, list):
        out = [_map_any(x, f) for x in node]
        return out if any(a is not b for a, b in zip(out, node)) else node
    if isinstance(node, tuple):
        out = tuple(_map_any(x, f) for x in node)
        return out if any(a is not b for a, b in zip(out, node)) else node
    if not is_dataclass(node) or isinstance(node, type):
        return node
    changes = {}
    for fld in fields(node):
        if fld.name == "span":
            continue
        v = getattr(node, fld.name)
        nv = _map_any(v, f)
        if nv is not v:
            changes[fld.name] = nv
    return replace(node, **changes) if changes else node


def _map_any(v, f):
    if isinstance(v, (list, tuple)) or (is_dataclass(v) and not isinstance(v, type)):
        return _map(v, f)
    return v


def _walk(node):
    """Every dataclass node under `node`, itself first."""
    if isinstance(node, (list, tuple)):
        for x in node:
            yield from _walk(x)
        return
    if not is_dataclass(node) or isinstance(node, type):
        return
    yield node
    for fld in fields(node):
        if fld.name == "span":
            continue
        yield from _walk(getattr(node, fld.name))


def _names(node) -> set:
    """Every name the syntax under `node` mentions — an over-approximation
    (a local shadowing a global counts), which errs towards blanking."""
    return {n.value for n in _walk(node) if isinstance(n, (VWord, VConId))}


def _defined(item) -> set:
    """The names an item declares — its own, and its constructors'."""
    out = set()
    name = getattr(item, "name", None)
    if isinstance(name, str):
        out.add(name)
    if isinstance(item, VTypeDecl):
        for c in item.constructors:
            out.add(c.name)
    return out


def _respan(node, span: Span):
    """`node` with every span under it set to `span` — a generated
    expression reports at the line the author wrote."""
    def stamp(v):
        return None
    out = _map(node, stamp)

    def walk(n):
        if isinstance(n, (list, tuple)):
            return type(n)(walk(x) for x in n)
        if not is_dataclass(n) or isinstance(n, type):
            return n
        changes = {}
        for fld in fields(n):
            if fld.name == "span":
                changes["span"] = span
            else:
                v = getattr(n, fld.name)
                nv = walk(v)
                if nv is not v:
                    changes[fld.name] = nv
        return replace(n, **changes) if changes else n
    return walk(out)


# ── The sites ───────────────────────────────────────────────────────────────

def _is_splice(v) -> bool:
    """`$(e)` at the head of a phrase, or `T $(e)` — the second is `T`
    applied to the type, since `$` binds tightest of the infix operators
    (`descend.DEFAULT_INFIX`)."""
    return isinstance(v, (VPrefix, VInfix)) and v.op == SPLICE


def _is_document(v) -> bool:
    return (isinstance(v, VApp) and isinstance(v.fn, VWord)
            and v.fn.value == DOCUMENT and isinstance(v.arg, VStr))


def _sites(item) -> list:
    """`[(node, kind)]` — every splice and document under one item."""
    out = []
    for n in _walk(item):
        if _is_splice(n):
            out.append((n, "splice"))
        elif _is_document(n):
            out.append((n, "document"))
    return out


def _expr_of(site) -> Val:
    return site.right if isinstance(site, VInfix) else site.arg


def _at(node) -> str:
    """The site's position, the way every compiler complaint carries one
    — 0-based, in the assembled text, for `audiospans.in_source` to move
    back into the author's file.  A prefix's own span starts at the
    phrase, so a splice reports where its expression is."""
    at = _expr_of(node) if isinstance(node, (VPrefix, VInfix)) else node
    return f" (at {at.span.start.line}:{at.span.start.col})"


# ── The pass ────────────────────────────────────────────────────────────────

def might_stage(source: str) -> bool:
    """Cheap: a program with neither form pays this and nothing else."""
    return SPLICE in source or DOCUMENT in source


def staged(items: list, build) -> tuple:
    """`(items, values)` — the author's resolved items with every splice
    replaced by the type it computes, every `document "kind"` replaced by
    the read of its channel, and that channel declared after them; and
    the stage-one values a host may want without compiling again,
    `{"kinds": term}` when the program declares its kinds.

    `build` is the compiler's own door, handed in by whichever front end
    is running: a list of resolved items in, a `GmState` out, through
    the same front and back half the program itself goes through.
    Stage one is **items, never text** — the sited items and everything
    that mentions them are left out, the splice expressions are appended
    as `Type` globals with the author's own spans, and nothing here
    reads the source, cuts a seam or takes the front end's lock.  Allais
    and Kovács say staging is one evaluation and not a second parse
    (`doc/memory/the-language-goal.md` §"Read — 2026-09-18"); the
    blank-slice-recompile this replaced re-entered the compiler through
    the lockless door and waited on itself three times
    (`doc/memory/a-run-silent-for-a-minute.md`).
    """
    sited = [(item, _sites(item)) for item in items]
    if not any(s for _i, s in sited):
        return items, {}

    # ── Stage two: the sited items, and everything that mentions them ──
    names: set = {"main"}
    for item, sites in sited:
        if sites:
            names |= _defined(item)
    changed = True
    while changed:
        changed = False
        for item, _s in sited:
            if _defined(item) & names:
                continue
            if _names(item) & names:
                names |= _defined(item)
                changed = True
    second = {id(item) for item, _s in sited if _defined(item) & names}

    # ── The cycle: a splice needing a stage-two item ──
    mentions = {}
    for item, _s in sited:
        for n in _defined(item):
            mentions.setdefault(n, set()).update(_names(item))
    all_sites = [(site, kind, item) for item, sites in sited for site, kind in sites]
    has_kinds = any("model" in _defined(item) for item, _s in sited)
    for site, kind, item in all_sites:
        if kind == "document":
            if not has_kinds:
                raise StageError(
                    f'`document "{site.arg.value}"` needs `model : List Rel` '
                    "declared in this program — the row it reads is computed "
                    f"from the relation (`facts.ges`, `relRow`){_at(site)}")
            need = {"model"}
        else:
            need = _names(_expr_of(site))
        own = _defined(item) | {"main"}
        seen: set = set()
        queue = sorted(need)
        cyclic = []
        while queue:
            n = queue.pop(0)
            if n in seen:
                continue
            seen.add(n)
            if n in names and n not in own:
                cyclic.append(n)
                break
            queue += sorted(mentions.get(n, set()) - seen)
        if cyclic:
            what = (f'`document "{site.arg.value}"`' if kind == "document"
                    else "the splice")
            raise StageError(
                f"{what} needs `{cyclic[0]}`, and `{cyclic[0]}` is typed by "
                "what it computes — a type computed from a value cannot be "
                f"computed from itself{_at(site)}")

    # ── Stage one's program: the first stage's items, the splices as globals ──
    first = [item for item, _s in sited if id(item) not in second]
    tail = []
    for i, (site, kind, _item) in enumerate(all_sites):
        if kind == "document":
            tail += _global(f"__stage_{i}__", "List Type",
                            f'documentRow model "{site.arg.value}"', site.span)
        else:
            e = _expr_of(site)
            tail += _global(f"__stage_{i}__", "Type", e, e.span)
    if any(kind == "document" for _s, kind, _i in all_sites):
        tail += _global("__stage_names__", "List Text", "map relName model",
                        all_sites[0][0].span)
    if has_kinds:
        # **The model and its lines, read while the machine is warm** —
        # what `facts.Document` used to compile the whole program a
        # second time for, and now takes from the analysis
        # (`pipeline.staged_value`); and the line view the language
        # derives from them, for the host's derivation to be held to.
        span = all_sites[0][0].span
        tail += _global("__stage_model__", "List Rel", "model", span)
        tail += _global("__stage_lines__", "List Line", "lines", span)
        tail += _global("__stage_kinds__", "List Kind",
                        "map (lineKind model) lines", span)
    tail += _global("main", "Int", "0", all_sites[0][0].span)

    # ── Run it ──
    state = build(first + tail)
    values = {}
    if has_kinds:
        values["model"] = _read(state, "__stage_model__")
        values["lines"] = _read(state, "__stage_lines__")
        values["kinds"] = _read(state, "__stage_kinds__")
    kind_names = None
    if "__stage_names__" in state.globals:
        kind_names = [_text(t) for t in _read(state, "__stage_names__")]

    replacements: dict = {}
    channels: dict = {}
    for i, (site, kind, _item) in enumerate(all_sites):
        got = _read(state, f"__stage_{i}__")
        if kind == "document":
            name = site.arg.value
            if not got:
                raise StageError(
                    f'`document "{name}"` names no kind this program declares '
                    "— `model` has "
                    + ", ".join(f"`{k}`" for k in (kind_names or []))
                    + _at(site))
            row = _type_val(got[0], site.span)
            chan = channel_of(name)
            replacements[id(site)] = _respan(_document_read(chan), site.span)
            channels.setdefault(chan, (row, site.span))
        else:
            ty = _type_val(got, _expr_of(site).span)
            if isinstance(site, VInfix):
                ty = VApp(site.left, ty, site.span)       # `Set $(e)` is `Set` applied
            replacements[id(site)] = ty

    def swap(v):
        return replacements.get(id(v))

    out = [_map(item, swap) if _sites(item) else item for item in items]
    for chan, (row, span) in channels.items():
        out.append(VSig(chan, VApp(VConId("Chan", span),
                                   VApp(VConId("List", span), row, span), span), span))
        out.append(VSCDecl(chan, None,
                           [VSCEqn(chan, [], VWord("chan", span), [], span)], span))
    return out, values


def _global(name: str, type_text: str, body, span: Span) -> list:
    """A signature and a definition, `name : type_text` and `name = body`,
    as the two items the parser would make of them — the type and, when
    `body` is a text, the body parsed on their own, and every span set to
    `span`, the author's line, so a complaint lands where the splice is.
    A `body` that is already syntax (a splice's expression) is used as it
    stands, spans and all."""
    from .syntax import parse

    sig = parse(f"__x__ : {type_text}\n").items[0].type_
    if isinstance(body, str):
        body = parse(f"__x__ = {body}\n").items[0].equations[0].body
        body = _respan(body, span)
    return [VSig(name, _respan(sig, span), span),
            VSCDecl(name, None, [VSCEqn(name, [], body, [], span)], span)]


def channel_of(kind: str) -> str:
    """The channel a kind's rows arrive on — `facts.channel_of`, restated
    so the two modules need not import each other."""
    #: `section.voices` is a relation and no identifier: the dot is an
    #: underscore on the channel, and nothing but the host reads it.
    return f"__doc_{kind.replace('.', '_')}__"


def _document_read(chan: str) -> Val:
    """`map (rows => set rows) (Nil ::: mkSig (wait <chan>))` — the read
    of a document's channel as a signal of a set, built by the parser."""
    from .syntax import parse

    module = parse(f"__x__ = map (rows => set rows) (Nil ::: mkSig (wait {chan}))\n")
    return module.items[0].equations[0].body


# ── Reading the value back ──────────────────────────────────────────────────

def _read(state, name: str):
    """The global `name`, evaluated and read as a Python term — a
    number, a list, `(constructor, args…)`, a bare tuple; the reading
    `charts.Terms.read` and `gui._term` make of a heap node."""
    from . import gmachine as gm
    from .gmachine import run
    from .midi import _force

    names = {v.tag: k for k, v in state.cons.items()}
    node = state.globals[name]
    state.stack, state.dump, state.code = [node], [], [gm.Eval()]
    run(state)
    node = state.stack[0]

    def read(n):
        n = _force(n, state)
        while isinstance(n, gm.NInd) and n.target is not None:
            n = n.target
        if isinstance(n, gm.NNum):
            return n.n
        if not isinstance(n, gm.NCon):
            #: complaint  machine — a `Type` global evaluated to something the checker typed as a `Type` and the machine did not build as one
            raise StageError(f"a stage-one value is a {type(n).__name__}, not a value")
        head = names.get(n.tag)
        if head == "Nil":
            return []
        if head == "Cons":
            out, at = [], n
            while isinstance(at, gm.NCon) and names.get(at.tag) == "Cons":
                out.append(read(at.args[0]))
                at = _force(at.args[1], state)
                while isinstance(at, gm.NInd) and at.target is not None:
                    at = at.target
            return out
        args = tuple(read(a) for a in n.args)
        return (head, *args) if head is not None else args
    return read(node)


def _text(term) -> str:
    if isinstance(term, str):
        return term
    return "".join(chr(c) for c in term)


def reflect(t, place: str = "", variables: bool = False) -> tuple:
    """A compiler type as the term of a `Type` value — the inverse of
    `_type_val` on the ground fragment.  `card:types-in-the-host.md`:
    the other half of the stage, a type read back as a value.

    `("TyCon", name)`, `("TyApp", f, a)`, `("TyFun", a, r)`, `("TyInt",
    n)`, `("TyTuple", [parts])` — the shape `_read` yields for a `Type`
    the machine built, so what this returns can be fed wherever that is
    read.  `place` is the caller's — whose definition, and its line —
    and goes on the refusal.  Total on ground types; **a variable is
    refused**, because a
    scheme cannot be said in `Type` (it has no binder, and the theory
    says what one would cost — `doc/memory/the-language-goal.md`
    §"Read — 2026-09-16"); and a monotone arrow is refused, because
    `TyFun` does not carry the flag and a value that forgot it would
    reify to the other arrow.
    """
    from .types import TApp, TCon, TFun, TInt, TVar, tuple_parts

    if isinstance(t, TVar):
        if variables:
            # A reader whose answer *about* a variable is the point —
            # the flatness judge says *not flat: a variable* — asks for
            # it by name.  `_type_val` refuses it on the way back.
            from .show import show_type
            return ("TyVar", show_type(t))
        #: complaint  author — a definition whose inferred type has a variable in it was asked for as a value; `place` is the caller's, the definition and its line
        raise StageError(
            f"a type with a variable in it cannot be read as a value{place}: "
            f"`Type` says only closed types, and this one is a scheme")
    parts = tuple_parts(t)
    if parts is not None:
        # Before `TCon`: the unit type is the bare `Tuple0`, a tuple of
        # nothing, and a rule must see it as one.
        return ("TyTuple", [reflect(a, place, variables) for a in parts])
    if isinstance(t, TCon):
        return ("TyCon", t.name)
    if isinstance(t, TInt):
        return ("TyInt", t.n)
    if isinstance(t, TFun):
        if getattr(t, "mono", False):
            #: complaint  author — a monotone arrow `~>` reached the reflector, which `TyFun` cannot say; `place` is the caller's, the definition and its line
            raise StageError(
                f"a monotone arrow `~>` cannot be read as a value{place}: "
                f"`TyFun` is `->` only")
        return ("TyFun", reflect(t.arg, place, variables),
                reflect(t.ret, place, variables))
    if isinstance(t, TApp):
        return ("TyApp", reflect(t.fn, place, variables),
                reflect(t.arg, place, variables))
    #: complaint  machine — a type of a kind the compiler's grammar does not have reached the reflector
    raise StageError(f"no value for a {type(t).__name__}{place}")


def reflect_data(t, cons: dict, place: str = "",
                 variables: bool = False) -> list:
    """The constructors of a ground type, as `rules.ges`' `List Con` —
    `[("Con", name, [field types])]` in declaration order, the type's
    parameters filled in from `t`'s arguments so every field is ground;
    `[]` when `t`'s head is not a declared type.  The second reflector:
    what a type is *made of*, for a rule that decides over that."""
    from .types import TCon, TFun, TVar, _apply_subst_map, _spine

    head, args = _spine(t)
    if not isinstance(head, TCon):
        return []
    out = []
    for info in sorted(cons.values(), key=lambda c: c.tag):
        fields, result = [], info.type_
        while isinstance(result, TFun):
            fields.append(result.arg)
            result = result.ret
        rhead, params = _spine(result)
        if not (isinstance(rhead, TCon) and rhead.name == head.name):
            continue
        subst = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
        out.append(("Con", info.name,
                    [reflect(_apply_subst_map(f, subst), place, variables)
                     for f in fields]))
    return out


def reflect_closure(t, cons: dict, place: str = "") -> list:
    """Every declared type reachable from `t` through constructor fields,
    each with its constructors at the instantiation first met — the
    `List (Text, List Con)` a rule that walks a type's structure reads,
    keyed by the type's name the way recursion is detected.  Variables
    are said, not refused: a rule that walks structure answers for
    them."""
    from .types import TCon, TFun, TVar, _apply_subst_map, _spine

    table: dict = {}
    todo = [t]
    while todo:
        cur = todo.pop()
        head, args = _spine(cur)
        if isinstance(cur, TFun):
            todo += [cur.arg, cur.ret]
            continue
        todo += args
        if not isinstance(head, TCon) or head.name in table:
            continue
        found = reflect_data(cur, cons, place, variables=True)
        if not found:
            continue
        table[head.name] = found
        for info in cons.values():
            fields, result = [], info.type_
            while isinstance(result, TFun):
                fields.append(result.arg)
                result = result.ret
            rhead, params = _spine(result)
            if isinstance(rhead, TCon) and rhead.name == head.name:
                subst = {p.id: a for p, a in zip(params, args) if isinstance(p, TVar)}
                todo += [_apply_subst_map(f, subst) for f in fields]
    return [Bare((name, found)) for name, found in table.items()]


def term_text(term) -> str:
    """A `Type` term, printed the way `show_type` prints — reflected, or
    read back from the machine, where a `Text` is its codes."""
    head = term[0]
    if head in ("TyCon", "TyVar"):
        return _text(term[1])
    if head == "TyInt":
        return str(term[1])
    if head == "TyApp":
        arg = term_text(term[2])
        if term[2][0] in ("TyApp", "TyFun"):
            arg = f"({arg})"
        return f"{term_text(term[1])} {arg}"
    if head == "TyFun":
        return f"{term_text(term[1])} -> {term_text(term[2])}"
    return "(" + ", ".join(term_text(a) for a in term[1]) + ")"


#: The rules' machine — `rules.ges` after `facts.ges` — compiled once
#: per process, on first use, because importing this module must not
#: compile a library.
_RULES = None


def rules():
    """The machine that answers the compiler's rules.  Compiled through
    the **lockless door**, `pipeline._compile`, never `compile`: the
    first ask comes from inside a compile, which holds
    `pipeline._FRONT_END`, and that lock is not reentrant — the locked
    door waited on itself for two minutes on 2026-09-16
    (`doc/memory/a-run-silent-for-a-minute.md`), and the tests had not
    seen it only because one of them built the rule first, outside any
    compile."""
    global _RULES
    if _RULES is None:
        from .charts import Terms
        from .pipeline import _compile
        here = __import__("pathlib").Path(__file__).resolve().parent
        _RULES = Terms(here / "rules.ges", here / "facts.ges", compile=_compile)
    return _RULES


def ask(name: str, *terms):
    """`name` from `rules.ges` applied to Python terms, the answer read
    back as a term.  A string is `Text`, so it goes in as its codes."""
    rule = rules()
    return rule.read(rule._apply(rule.declared(name),
                                 *[rule.node(_codes(t)) for t in terms]))


class Bare(tuple):
    """A bare tuple in a term — `(name, cons)` — as opposed to a
    constructor's `("Con", …)`, which `Terms.node` tells apart by the
    head being a string; a pair whose first component is a `Text` would
    otherwise read as a constructor named by it."""


def _codes(term):
    if isinstance(term, str):
        return [ord(c) for c in term]
    if isinstance(term, list):
        return [_codes(a) for a in term]
    if isinstance(term, Bare):
        return tuple(_codes(a) for a in term)
    if isinstance(term, tuple):
        return (term[0], *[_codes(a) for a in term[1:]])
    return term


def unreflect(term):
    """A `Type` term as the compiler's type — `_type_val` and then the
    checker's own reader, so a value that reifies is read the way a
    signature is.  The inverse of `reflect` on the ground fragment;
    `test_stage.py` holds the pair."""
    from .declarations import desugar_type
    from .syntax.ast import Pos

    return desugar_type(_type_val(term, Span(Pos(0, 0), Pos(0, 0))))


def _type_val(term, span: Span) -> Val:
    """A `Type` value as the type syntax the checker reads — `facts.ges`'
    five constructors, and nothing else is a type."""
    if not isinstance(term, tuple) or not term:
        raise StageError(f"the splice is not a `Type` (at {span.start.line}:{span.start.col})")
    head, *args = term
    if head == "TyCon":
        name = _text(args[0])
        node = VConId if name[:1].isupper() else VWord
        return node(name, span)
    if head == "TyApp":
        return VApp(_type_val(args[0], span), _type_val(args[1], span), span)
    if head == "TyFun":
        return VInfix(_type_val(args[0], span), "->", _type_val(args[1], span), span)
    if head == "TyInt":
        return VNum(args[0], span)
    if head == "TyTuple":
        items = [_type_val(t, span) for t in args[0]]
        return items[0] if len(items) == 1 else VTuple(items, span)
    if head == "TyVar":
        #: complaint  author — a splice evaluated to a type variable, which nothing binds, so it cannot be the type the checker reads
        raise StageError(
            f"the splice is a type variable `{_text(args[0])}`, and a "
            f"variable cannot be a type — nothing binds it "
            f"(at {span.start.line}:{span.start.col})")
    raise StageError(
        f"the splice is a `{head}`, not a `Type` — `TyCon`, `TyApp`, `TyFun`, "
        f"`TyInt` or `TyTuple` (`facts.ges`) (at {span.start.line}:{span.start.col})")
