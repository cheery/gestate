"""Every complaint says where — `fixme.md` F152.

**A message with no position has nowhere to be drawn.**  The editor
puts a complaint in a content box under the line it names; one that
names no line falls back to a single sentence in the status bar, which
is where Henri found this: `sound : Sig Floa`, and *"the error messages
no longer interleave into their places… the message doesn't land."*

It had never landed.  Type errors carry spans and kind errors did not,
except for the one message somebody had already hit (`foo : int`, F141,
`test_skolems.py`) — so the arithmetic was in the file and used once.

This file is where that gets held, and where
`board/error-messages.md`'s audit will land as it goes: one test per
message that must name a place.  The assertion is deliberately about
*a position being there at all* rather than about the exact line, since
the line moves with the prelude offset and `audiospans.in_source` is
what turns it into the author's own file.
"""

from __future__ import annotations

import re

import pytest

from gestate.kindcheck import KindError
from gestate.pipeline import evaluate

#: What a message must carry to be drawable: a raw `line:col`, which
#: `audiospans.in_source` rewrites into `file:line:col` on the way out.
PLACE = re.compile(r"\(at \d+:\d+")


def test_an_unknown_type_constructor_says_where_it_was_written():
    """Henri's own reproduction, 2026-08-17: one letter off a type."""
    with pytest.raises(KindError, match=PLACE):
        evaluate("sound : Sig Floa\nsound = 0.2\n\n"
                 "main : Float\nmain = sound\n")


def test_a_kind_mismatch_says_where():
    """`Maybe Maybe` — a constructor where a type belongs."""
    with pytest.raises(KindError, match=PLACE):
        evaluate("thing : Maybe Maybe\nthing = 0\n\n"
                 "main : Int\nmain = 0\n")


def test_the_message_still_says_what_is_wrong():
    """**A position is an addition, not a replacement.**  It would be a
    poor trade to learn where a mistake is and stop being told what it
    is, and appending to a message is exactly how that gets lost."""
    with pytest.raises(KindError, match="Unknown type constructor: Floa"):
        evaluate("sound : Sig Floa\nsound = 0.2\n\n"
                 "main : Float\nmain = sound\n")


def test_a_lowercase_type_variable_still_says_where(  # F141, kept in sight
):
    """The one that already worked, asserted here too so the audit's
    file shows the whole family rather than only its gaps."""
    with pytest.raises(KindError, match=PLACE):
        evaluate("depth : float\ndepth = 0.5\n\n"
                 "main : Float\nmain = depth\n")
