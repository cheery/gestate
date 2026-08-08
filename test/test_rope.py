"""`balanced.py`'s rope — the editor's document, read in pieces.

A rope is only as good as its *partial* reads.  Everything here used to
join the whole thing (`"".join(rope)`) and everything worked; the first
caller to ask for one line — `audiopygame.Document.line` — found a bug that
had been sitting in `segments` the whole time, and it corrupted the top of
the screen on a backspace.

So this file reads *ranges*, against a plain string, over sequences of
edits.  A differential test rather than examples, because the shape of the
tree is what decides which branch of `segments` runs and no hand-written
case would have found the one that was wrong.
"""

from __future__ import annotations

import random

from gestate.balanced import blank


def _rope(text: str):
    return blank.insert(0, text)


def test_a_range_that_lies_inside_the_left_child():
    """The bug, pinned.

    A `RopeSegment` whose own text is *after* the range asked for: the
    middle slice was appended anyway, with a negative index, so
    `text[0:-1]` handed back a trimmed copy of the segment.  Reading the
    whole rope never touched that path.
    """
    rope = _rope("alpha\nbeta\ngamma\ndelta\n")
    rope = rope.insert(rope.length, "xx")       # forces `xx` to the root
    assert rope.segments(17, 22) == ["delta"]
    assert "".join(rope.segments(0, 5)) == "alpha"
    assert "".join(rope) == "alpha\nbeta\ngamma\ndelta\nxx"


def test_every_range_of_a_built_up_rope_reads_as_the_string_does():
    random.seed(3)
    text = "alpha\nbeta\ngamma\n"
    rope, model, pos = _rope(text), text, len(text)
    for _ in range(120):
        if random.random() < 0.5 and pos > 0:
            rope, model, pos = (rope.erase(pos - 1, pos),
                                model[:pos - 1] + model[pos:], pos - 1)
        else:
            ch = random.choice("xy\n")
            rope, model = rope.insert(pos, ch), model[:pos] + ch + model[pos:]
            pos += 1
        assert "".join(rope) == model
        for start in range(0, len(model) + 1, 3):
            for stop in range(start, len(model) + 1, 3):
                assert "".join(rope.segments(start, stop)) == model[start:stop]


def test_rows_and_positions_agree_with_the_string():
    random.seed(5)
    text = "one\ntwo\nthree\n"
    rope, model, pos = _rope(text), text, len(text)
    for _ in range(150):
        if random.random() < 0.5 and pos > 0:
            rope, model, pos = (rope.erase(pos - 1, pos),
                                model[:pos - 1] + model[pos:], pos - 1)
        else:
            ch = random.choice("ab\n")
            rope, model = rope.insert(pos, ch), model[:pos] + ch + model[pos:]
            pos += 1
        starts = [0] + [i + 1 for i, c in enumerate(model) if c == "\n"]
        assert rope.newlines == model.count("\n")
        assert [rope.rowpos(i) for i in range(len(starts))] == starts
        assert [rope.row(i) for i in range(len(model) + 1)] == \
            [model.count("\n", 0, i) for i in range(len(model) + 1)]
