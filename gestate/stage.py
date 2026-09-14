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

**What it costs.**  One more compile of a program's stage-one half, with
the library stack answered from its cache (`pipeline._stack_front`), per
distinct program text — the same cache every compile goes through.  A
program with neither form pays a substring test.
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
    return isinstance(v, VPrefix) and v.op == SPLICE


def _is_infix_splice(v) -> bool:
    """`Set $(e) -> Int` — the expression grammar reads `$` between two
    things as an operator binding looser than `->`, so the splice would
    swallow the arrow.  Refused, with the spelling that works."""
    return isinstance(v, VInfix) and v.op == SPLICE


def _is_document(v) -> bool:
    return (isinstance(v, VApp) and isinstance(v.fn, VWord)
            and v.fn.value == DOCUMENT and isinstance(v.arg, VStr))


def _sites(item) -> list:
    """`[(node, kind)]` — every splice and document under one item."""
    out = []
    for n in _walk(item):
        if _is_splice(n):
            out.append((n, "splice"))
        elif _is_infix_splice(n):
            raise StageError(
                "a splice is written as an argument of its own — `Set ($(e))`, "
                "not `Set $(e)` — because `$` between two things is read as an "
                f"operator (at {n.left.span.start.line}:{n.left.span.start.col})")
        elif _is_document(n):
            out.append((n, "document"))
    return out


def _expr_of(site) -> Val:
    return site.arg


def _at(node) -> str:
    """The site's position, the way every compiler complaint carries one
    — 0-based, in the assembled text, for `audiospans.in_source` to move
    back into the author's file.  A prefix's own span starts at the
    phrase, so a splice reports where its expression is."""
    at = node.arg if isinstance(node, VPrefix) else node
    return f" (at {at.span.start.line}:{at.span.start.col})"


# ── The pass ────────────────────────────────────────────────────────────────

def might_stage(source: str) -> bool:
    """Cheap: a program with neither form pays this and nothing else."""
    return SPLICE in source or DOCUMENT in source


def staged(items: list, source: str, cut: int | None) -> list:
    """`items` — the author's parsed, unresolved items — with every splice
    replaced by the type it computes, every `document "kind"` replaced by
    the read of its channel, and that channel declared after them.

    `source` is the whole assembled text the items were parsed from, at
    their own positions; `cut` is its seam, when an assembler registered
    one, so stage one's compile answers the library stack from cache.
    """
    sited = [(item, _sites(item)) for item in items]
    if not any(s for _i, s in sited):
        return items
    from .syntax import note_seam

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
    second = [item for item, _s in sited if _defined(item) & names]

    # ── The cycle: a splice needing a stage-two item ──
    mentions = {}
    for item, _s in sited:
        for n in _defined(item):
            mentions.setdefault(n, set()).update(_names(item))
    all_sites = [(site, kind, item) for item, sites in sited for site, kind in sites]
    has_kinds = any("kinds" in _defined(item) for item, _s in sited)
    for site, kind, item in all_sites:
        if kind == "document":
            if not has_kinds:
                raise StageError(
                    f'`document "{site.arg.value}"` needs `kinds : List Kind` '
                    "declared in this program — the row it reads is computed "
                    f"from the kind (`facts.ges`, `kindRow`){_at(site)}")
            need = {"kinds"}
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

    # ── Stage one's text: the second stage blanked, the splices appended ──
    lines = source.split("\n")
    for item in second:
        for k in range(item.span.start.line, item.span.end.line + 1):
            if 0 <= k < len(lines):
                lines[k] = ""
    tail = []
    for i, (site, kind, _item) in enumerate(all_sites):
        if kind == "document":
            tail.append(f"__stage_{i}__ : List Type\n__stage_{i}__ = "
                        f'documentRow kinds "{site.arg.value}"\n')
        else:
            e = _expr_of(site)
            tail.append(f"__stage_{i}__ : Type\n__stage_{i}__ = "
                        f"({_slice(source, e.span)})\n")
    if any(kind == "document" for _s, kind, _i in all_sites):
        tail.append("__stage_names__ : List Text\n__stage_names__ = map kindName kinds\n")
    text = "\n".join(lines).rstrip("\n") + "\n\n" + "".join(tail) + "\nmain : Int\nmain = 0\n"
    if cut is not None:
        note_seam(text, cut)

    # ── Run it ──
    # `_compile`, not `compile`: this runs *inside* a compile, on its
    # deep stack and under `pipeline._FRONT_END`, which is not reentrant
    # — `compile` would wait on the lock this very call holds
    # (`doc/memory/a-run-silent-for-a-minute.md`).  The lockless door
    # goes through the same cache as every other reader.
    from .pipeline import _compile

    state = _compile(text)
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
                    "— `kinds` has "
                    + ", ".join(f"`{k}`" for k in (kind_names or []))
                    + _at(site))
            row = _type_val(got[0], site.span)
            chan = channel_of(name)
            replacements[id(site)] = _respan(_document_read(chan), site.span)
            channels.setdefault(chan, (row, site.span))
        else:
            replacements[id(site)] = _type_val(got, site.arg.span)

    def swap(v):
        return replacements.get(id(v))

    out = [_map(item, swap) if _sites(item) else item for item in items]
    for chan, (row, span) in channels.items():
        out.append(VSig(chan, VApp(VConId("Chan", span),
                                   VApp(VConId("List", span), row, span), span), span))
        out.append(VSCDecl(chan, None,
                           [VSCEqn(chan, [], VWord("chan", span), [], span)], span))
    return out


def channel_of(kind: str) -> str:
    """The channel a kind's rows arrive on — `facts.channel_of`, restated
    so the two modules need not import each other."""
    return f"__doc_{kind}__"


def _document_read(chan: str) -> Val:
    """`map (rows => set rows) (Nil ::: mkSig (wait <chan>))` — the read
    of a document's channel as a signal of a set, built by the parser."""
    from .syntax import parse

    module = parse(f"__x__ = map (rows => set rows) (Nil ::: mkSig (wait {chan}))\n")
    return module.items[0].equations[0].body


def _slice(source: str, span: Span) -> str:
    lines = source.split("\n")
    a, b = span.start, span.end
    if a.line == b.line:
        return lines[a.line][a.col:b.col]
    parts = [lines[a.line][a.col:]]
    parts += lines[a.line + 1:b.line]
    parts.append(lines[b.line][:b.col])
    return "\n".join(parts)


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
    raise StageError(
        f"the splice is a `{head}`, not a `Type` — `TyCon`, `TyApp`, `TyFun`, "
        f"`TyInt` or `TyTuple` (`facts.ges`) (at {span.start.line}:{span.start.col})")
