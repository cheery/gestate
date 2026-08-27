"""`spec/syntax.md`'s examples compile — checked, not asserted.

`fixme.md` F63: the constrained-ADT example read `ShowThis := (Show a) =>
ShowThis a`, which the kind checker refuses — `a` is not bound by the head
— and nothing read the page, so the correction could drift back without a
line changing colour.  The example is pulled out of the page here and
compiled, the way `test_manual.py` holds `doc/manual.md` to its word.
"""

from __future__ import annotations

from pathlib import Path

from gestate.pipeline import compile

SYNTAX = Path(__file__).resolve().parent.parent / "spec" / "syntax.md"


def test_the_constrained_adt_example_compiles():
    text = SYNTAX.read_text()
    marker = "supports constraints to be supplied in type:"
    assert marker in text, "the example has moved; follow it"
    block = text.split(marker, 1)[1].lstrip("\n").split("\n\n", 1)[0]
    decl = "\n".join(line.strip() for line in block.splitlines())
    assert decl.startswith("ShowThis"), decl
    compile(decl + "\n\nmain : Int\nmain = 1\n")
