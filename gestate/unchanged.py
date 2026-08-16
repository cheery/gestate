"""unchanged.py — did this edit touch what that phase reads?

A rebuild redoes the file.  For a one-line change that is mostly waste:
editing a constant inside one voice re-walks a score that did not move,
recompiles a canvas that did not move, and rebuilds the MIDI half that
did not move.  Measured on `examples/audio/quartet.ges` — one constant
changed inside `bassOsc`:

    clang      1.53s    the C did change, so this is earned
    score      1.45s    the score was not touched
    front end  1.32s
    substrate  0.31s    no canvas in the edit either
    midi       0.19s

This says whether a phase's inputs moved, so the ones that did not can
be kept.

**Textual, and deliberately so.**  The obvious implementation parses
both texts and compares declarations.  It costs 0.6 s to expand and
0.16 s to parse this file, which is most of what it would save — and
it needs the program to *parse*, which during editing it often does
not.  A top-level declaration in this language begins in column zero,
which is enough to split the text into blocks with a regular
expression, in under a millisecond, on text that does not compile.

**Every uncertainty answers "changed".**  A block it cannot classify,
a declaration that appeared or vanished, a `class`, `instance`, `data`,
`type` or `voices` line that differs by a byte — all of them say *the
whole thing moved*, and everything is rebuilt.  The reachability walk
is over identifiers rather than resolved names, so it sees more than
the real dependency graph: a bigger reachable set means fewer skips,
which is the safe direction.  The cost of being wrong here is a stale
score under a new synth — silently the wrong music — and there is no
number of saved seconds worth that.

What it *does* catch, which is the common case while working:

* a comment above a definition — its own block, and blocks that are
  only comments are ignored;
* a constant or an expression inside one definition, when nothing the
  score reaches names that definition;
* whitespace nowhere, because layout is meaning in this language and
  nothing here normalises it away.
"""

from __future__ import annotations

import re

#: Words that begin a block this file will not reason about.  Every one
#: of them can change what any other declaration *means* — an instance
#: chooses a method body, a `voices` line rewrites into a bank, a
#: fixity declaration reassociates an operator somebody else wrote — so
#: a difference in any of them is taken as "everything moved".
#:
#: The editor's own ask lines (`canvas`, `notes`, `sink`, `scope`) are
#: here for the same reason from the other side: they are not
#: declarations at all, they are furniture, and a change to one is a
#: change to what the window is being asked to build.
STRUCTURAL = frozenset({
    "class", "instance", "data", "type", "deriving", "import",
    "infix", "infixl", "infixr", "voices",
    "canvas", "notes", "sink", "scope", "spectro",
})

#: An identifier, for the reachability walk.  Punctuation operators are
#: matched separately: `(||)` is a name a declaration can define.
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")
_OPNAME = re.compile(r"^\(([^)]+)\)")


def _split(source: str) -> list:
    """The text as blocks: a top-level line and everything indented under it."""
    out: list = []
    held: list = []
    for line in source.splitlines(keepends=True):
        if line[:1] not in (" ", "\t", "\n", "\r", ""):
            if held:
                out.append("".join(held))
            held = [line]
        else:
            held.append(line)
    if held:
        out.append("".join(held))
    return out


def blocks(source: str):
    """`(value declarations by name, everything else)`.

    The second half is one string on purpose: nothing here reasons about
    *which* structural thing changed, only whether any did.
    """
    named: dict = {}
    structural: list = []
    for block in _split(source):
        head = block.lstrip()
        if not head or head.startswith("#"):
            # A comment block between declarations, which is why editing
            # one costs nothing.
            continue
        first = head.split(None, 1)[0]
        op = _OPNAME.match(head)
        if op:
            name = f"({op.group(1)})"
        elif first in STRUCTURAL or ":=" in block.split("\n")[0]:
            structural.append(block)
            continue
        else:
            name = first
        named[name] = named.get(name, "") + block
    return named, "".join(structural)


def changed(before: str, after: str):
    """Which declarations differ — or `None` when it cannot tell.

    `None` is *not* "nothing changed": it is "ask me no more questions",
    and every caller reads it as rebuild.
    """
    if before is None or after is None:
        return None
    if before == after:
        return set()
    mine, my_rest = blocks(before)
    theirs, their_rest = blocks(after)
    if my_rest != their_rest:
        return None                    # a class, an instance, a bank line
    if set(mine) != set(theirs):
        return None                    # something appeared or vanished
    return {name for name in mine if mine[name] != theirs[name]}


def reaches(source: str, roots) -> set:
    """Every declaration a root can reach, by name.

    Over *identifiers*, not resolved references: `bassOsc` inside a
    comment in `score`'s body counts as reached.  That is the wrong
    answer in the safe direction — it can only make the reachable set
    bigger, and a bigger set means fewer things are skipped.
    """
    named, _rest = blocks(source)
    seen: set = set()
    stack = [r for r in roots if r in named]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        for word in _WORD.findall(named[name]):
            if word in named and word not in seen:
                stack.append(word)
    return seen


def kept(before: str, after: str, roots=()) -> bool:
    """Can a phase reading `roots` keep what it built from `before`?

    With no roots the question is the strictest one — *did anything at
    all change* — which is what a phase asks when its dependencies
    cannot be bounded honestly.
    """
    moved = changed(before, after)
    if moved is None:
        return False
    if not moved:
        return True
    if not roots:
        return False
    return not (moved & reaches(after, roots))
