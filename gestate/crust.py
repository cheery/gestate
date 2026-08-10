"""Serialize a compiled program for `crust/` — and read both answers.

`crust` is the G-machine's pure core in Rust (`spec/crust.md`), and
`gmachine.py` is the reference it is held against.  This module is the
seam: `serialize` lowers the globals reachable from an entry point into
the flat text format the crate parses, refusing — by name, before
anything runs — any instruction outside the core.  A program that
crosses is one the mirror wholly understands, which is what makes a
disagreement a bug rather than a shrug.

`canonical` renders a forced value the way `crust` prints one —
`42`, `#tag(a b)` — so the parity test compares strings and the strings
mean the same thing.
"""

from __future__ import annotations

from . import gmachine as gm


class CrustError(Exception):
    pass


#: The pure core: what a score's forcing needs, and nothing reactive.
_SIMPLE = {gm.Unwind: "Unwind", gm.Mkap: "Mkap", gm.Eval: "Eval",
           gm.MatchFail: "MatchFail", gm.AddInt: "AddInt",
           gm.SubInt: "SubInt", gm.MulInt: "MulInt", gm.DivInt: "DivInt",
           gm.ModInt: "ModInt", gm.XorInt: "XorInt"}
_UNARY = {gm.PushInt: "PushInt", gm.Push: "Push", gm.PushArg: "PushArg",
          gm.Update: "Update", gm.Pop: "Pop", gm.Alloc: "Alloc",
          gm.Slide: "Slide", gm.Proj: "Proj"}


def serialize(state, entry: str = "main") -> str:
    """The program under `entry`, in crust's flat text format.

    Only what `entry` reaches crosses: a compiled program's globals
    include every library definition, reactive machinery and all, and a
    score-forcing core has no business refusing a program over a
    `NewChan` nothing will ever call.
    """
    blocks: list = []
    lines: list = ["crust 1"]

    def block_of(code) -> int:
        rows: list = []
        for instr in code:
            t = type(instr)
            if t in _SIMPLE:
                rows.append(f"I {_SIMPLE[t]}")
            elif t in _UNARY:
                field = next(iter(instr.__dataclass_fields__))
                rows.append(f"I {_UNARY[t]} {getattr(instr, field)}")
            elif t is gm.PushGlobal:
                rows.append(f"I PushGlobal {instr.name}")
            elif t is gm.Pack:
                rows.append(f"I Pack {instr.tag} {instr.arity}")
            elif t is gm.PackTuple:
                rows.append(f"I PackTuple {gm.tuple_tag(instr.arity)} "
                            f"{instr.arity}")
            elif t is gm.EqInt:
                rows.append(f"I EqInt {instr.tag_true} {instr.tag_false}")
            elif t is gm.LtInt:
                rows.append(f"I LtInt {instr.tag_true} {instr.tag_false}")
            elif t is gm.CaseJump:
                pairs = [(tag, block_of(body)) for tag, body in instr.table]
                rows.append("I CaseJump " + str(len(pairs)) + " "
                            + " ".join(f"{t} {b}" for t, b in pairs))
            else:
                raise CrustError(
                    f"`{t.__name__}` is outside crust's pure core — this "
                    f"program needs the reference machine")
        blocks.append(rows)
        return len(blocks) - 1

    done: dict = {}
    queue = [entry]
    globals_out = []
    while queue:
        name = queue.pop()
        if name in done:
            continue
        node = state.globals.get(name)
        if node is None:
            raise CrustError(f"unknown global `{name}`")
        done[name] = True
        for instr in _walk(node.code):
            if isinstance(instr, gm.PushGlobal):
                queue.append(instr.name)
        globals_out.append((name, node.arity, block_of(node.code)))

    for rows in blocks:
        lines.append("block")
        lines.extend(rows)
    for name, arity, block in globals_out:
        lines.append(f"global {name} {arity} {block}")
    lines.append(f"entry {entry}")
    return "\n".join(lines) + "\n"


def _walk(code):
    for instr in code:
        yield instr
        if isinstance(instr, gm.CaseJump):
            for _tag, body in instr.table:
                yield from _walk(body)


def canonical(node, state) -> str:
    """The value, spelled the way `crust` spells it."""
    from .midi import _force

    node = _force(node, state)
    while isinstance(node, gm.NInd) and node.target is not None:
        node = node.target
    if isinstance(node, gm.NNum):
        return str(node.n)
    if isinstance(node, gm.NCon):
        inner = " ".join(canonical(a, state) for a in node.args)
        return f"#{node.tag}({inner})"
    raise CrustError(f"canonical: unexpected node {type(node).__name__}")
