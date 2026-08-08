"""The evaluator's inner loop — `fixme.md` F79.

Four changes, none of them to what the machine computes:

* `step` advanced with `instr, s.code = s.code[0], s.code[1:]`, allocating a
  fresh list per instruction.  A program counter replaces it.
* `run` called `step` and consulted the `isFinal` *property* once per
  instruction.  Both are written out in the loop now.
* `_unwind` tested five node kinds with one `isinstance` before reaching the
  common case.
* `_unwind` followed the spine one link per instruction, which was a third
  of everything the machine executed.  It now follows all of it at once.

The last is the one that could be wrong, because unwinding leaves state
behind: the code the one-at-a-time version ends on is the `[Unwind]` it just
consumed.  The reference below is that version, and the tests run the two
against each other.

These build heap nodes directly and never compile anything, so the file
costs nothing to run.  What the machine *computes* is already covered by
every other test in the suite.
"""

from __future__ import annotations

import pytest

from gestate.gmachine import (
    GmError, GmState, NAp, NCon, NGlobal, NInd, NNum, Unwind, _unwind, run,
)


def _unwind_naive(s):
    """`_unwind` as the rule states it: one link, then round again."""
    node = s.stack[0]
    if isinstance(node, (NNum, NCon)):
        return
    if isinstance(node, NAp):
        s.stack.insert(0, node.fn)
        s.code = [Unwind()]
    elif isinstance(node, NGlobal):
        if len(s.stack) < node.arity + 1:
            raise GmError("Unwinding global with too few args")
        s.code = list(node.code)
    elif isinstance(node, NInd):
        s.stack[0] = node.target
        s.code = [Unwind()]
    else:
        raise GmError("bad node")


def _drive_naive(stack):
    s = GmState([Unwind()], list(stack), {}, [])
    while s.code:
        instr = s.code[0]
        s.code = s.code[1:]
        assert isinstance(instr, Unwind)
        _unwind_naive(s)
    return s


def _drive_fused(stack):
    s = GmState([Unwind()], list(stack), {}, [])
    s.code = s.code[1:]          # as `run` would, having taken the Unwind
    _unwind(Unwind(), s)
    return s


#: A supercombinator body that is not itself `[Unwind]`.  It matters: a
#: global whose code unwinds again is an infinite loop, and the reference
#: driver below has no step limit to save it.  These tests are about where
#: the walk *lands*, never about running the callee, so empty will do.
_BODY: list = []


def _spine(depth):
    """`((g x) x) ...` — an application spine `depth` links deep."""
    node = NGlobal(0, _BODY)
    for i in range(depth):
        node = NAp(node, NNum(i))
    return node


@pytest.mark.parametrize("depth", [0, 1, 2, 5, 20])
def test_the_fused_unwind_lands_where_the_naive_one_does(depth):
    stack = [_spine(depth)]
    a, b = _drive_naive(stack), _drive_fused(stack)
    assert a.stack == b.stack, "the spine was not pushed identically"
    assert list(a.code) == list(b.code), "the code left behind differs"


def test_it_stops_on_a_value_with_the_code_exhausted():
    # The subtlety: reaching WHNF after moving must leave nothing to run,
    # because the code the naive version ends on is the `[Unwind]` it just
    # consumed.  Leaving the caller's code in place would run it twice.
    s = _drive_fused([NAp(NNum(1), NNum(2))])
    assert list(s.code) == []
    assert s.stack[0] == NNum(1)


def test_a_value_already_on_top_leaves_the_code_alone():
    # Nothing moved, so nothing is discarded.
    s = GmState([Unwind(), Unwind()], [NNum(3)], {}, [])
    s.code = s.code[1:]
    _unwind(Unwind(), s)
    assert len(list(s.code)) == 1


def test_it_follows_indirections_inside_the_walk():
    body = _BODY
    stack = [NInd(NAp(NInd(NGlobal(1, body)), NNum(7)))]
    a, b = _drive_naive(stack), _drive_fused(stack)
    assert a.stack == b.stack
    assert list(a.code) == list(b.code) == body


def test_a_null_indirection_still_reports_itself():
    with pytest.raises(GmError, match="null indirection"):
        _drive_fused([NInd(None)])


def test_too_few_arguments_is_still_caught():
    with pytest.raises(GmError, match="too few args"):
        _drive_fused([NAp(NGlobal(5, _BODY), NNum(1))])


# ── The program counter ─────────────────────────────────────────────────────


def test_assigning_code_rewinds_the_counter():
    s = GmState([Unwind(), Unwind(), Unwind()], [], {}, [])
    s._pc = 2
    assert len(s.code) == 1, "`code` reads as what is left"
    s.code = [Unwind()]
    assert s._pc == 0


def test_is_final_reads_the_counter_not_the_list():
    s = GmState([Unwind()], [], {}, [])
    assert not s.isFinal
    s._pc = 1
    assert s.isFinal


def test_the_step_limit_still_fires():
    # `f = f`, as instructions: push it and unwind to its own body again.
    # Caught after fifty steps, so the test costs nothing.
    from gestate.gmachine import PushGlobal

    loop = NGlobal(0, [PushGlobal("f"), Unwind()])
    s = GmState([PushGlobal("f"), Unwind()], [], {"f": loop}, [])
    with pytest.raises(GmError, match="step limit"):
        run(s, max_steps=50)
