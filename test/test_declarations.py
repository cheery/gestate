"""The constructor tags `declarations.classify` hands out.

`gmachine` pins a few tags — `Nothing`/`Just` at 80–81, `Sync` at
82–84, the FRP nodes at 90–96, tuples from 200 — and until 2026-09-14
`fresh_tag` counted straight through them: the seventy-seventh declared
constructor of a chain was `Nothing`'s number (`fixme.md` F232, found
the day `gui.ges` grew five).  What these hold is that no declared
constructor ever wears a reserved tag, however many a program declares.
"""
from __future__ import annotations

import pytest

from gestate import pipeline
from gestate.declarations import DeclError, reserved_tags
from gestate.gmachine import TAG_TUPLE_BASE


def _program(constructors: int) -> str:
    """One data type with this many constructors, and a `Maybe` read
    back through `case` — the collision F232 showed."""
    cons = " | ".join(f"K{i} Int" for i in range(constructors))
    return (
        f"Big := {cons}\n"
        "main : Int\n"
        "main = case (Just 7) of\n"
        "    Just n -> n\n"
        "    Nothing -> 0\n"
    )


def test_declared_constructors_never_take_a_reserved_tag():
    state = pipeline.compile(_program(120))
    reserved = reserved_tags()
    taken = {name: info.tag for name, info in state.cons.items()
             if name.startswith("K")}
    assert len(taken) == 120
    assert not [n for n, t in taken.items() if t in reserved], \
        "a declared constructor on a reserved tag"
    assert len(set(taken.values())) == 120, "and every tag distinct"
    assert state.cons["Just"].tag == 81 and state.cons["Nothing"].tag == 80


def test_a_just_is_still_a_just_past_the_seventy_seventh_constructor():
    from gestate.gmachine import NNum, run

    state = pipeline.compile(_program(120))
    node = state.globals["main"]
    from gestate.gmachine import Eval
    state.stack, state.dump, state.code = [node], [], [Eval()]
    run(state)
    got = state.stack[0]
    while getattr(got, "target", None) is not None:
        got = got.target
    assert isinstance(got, NNum) and got.n == 7


def test_too_many_constructors_is_a_refusal_and_not_a_tuple():
    with pytest.raises(DeclError, match="too many constructors"):
        pipeline.compile(_program(TAG_TUPLE_BASE))
