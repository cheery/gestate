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
`board/done/error-messages.md`'s audit will land as it goes: one test per
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


# ── And the whole way out: does the box land on the line? ───────────────────
#
# **The tests above assert that a message contains a position.  These
# assert that a person sees it under the line they typed**, which is the
# postcondition `board/done/error-messages.md` was written against and is not
# the same claim: between the raise and the box are two coordinate
# systems (`audiospans.in_source` re-bases assembled positions and leaves
# the author's alone) and one regular expression (`session._line_of`, the
# only thing that ever reads the number back).  A message can carry a
# perfectly good `at 4:2` and still land nowhere, which is exactly what
# `line 4:` did in `internals.py` and `audioscore.py` until this card.
#
# Each case is a mistake somebody actually makes, written into a file,
# compiled the way the workbench compiles it, and read back the way the
# workbench reads it.

import pytest as _pytest

from gestate import audio
from gestate.audiospans import in_source
from gestate.session import _line_of

#: source, the line the mistake is on (1-based), and what to call it.
LANDS = [
    ("sound : Sig Floa\nsound = 0.2\n", 1,
     "a type constructor one letter off"),
    ("depth : float\ndepth = 0.5\n\nsound : Sig Float\nsound = mkSig depth\n", 1,
     "a type written in lowercase"),
    ("gain : Float\ngain : Float\ngain = 0.2\n\n"
     "sound : Sig Float\nsound = mkSig gain\n", 2,
     "a signature written twice"),
    ("f : [Int, Int] -> Int\nf x = 1\n\n"
     "sound : Sig Float\nsound = mkSig 0.1\n", 1,
     "a list type with a tail"),
    ("f : Maybe Float -> Float\nf (Just x) = x\n\n"
     "sound : Sig Float\nsound = mkSig (f Nothing)\n", 2,
     "a definition that does not cover every value"),
    ("voices lead 0 voice : Sig Float\n\n"
     "voice : Sig Gate -> Sig Float -> Sig Float\nvoice g p = mkSig 0.1\n\n"
     "sound : Sig Float\nsound = lead\n", 1,
     "a bank declared with no voices"),
    ("sound : Sig Float\nsound = mapSig (\\x => x) (mkSig 0.1)\n", 2,
     "a name a library keeps to itself"),
]


@_pytest.mark.parametrize("source,line,what",
                          LANDS, ids=[c[2] for c in LANDS])
def test_the_complaint_lands_on_the_line_the_mistake_is_on(source, line, what):
    with _pytest.raises(Exception) as caught:
        audio.render(source, seconds=0.01, rate=8000)
    whole = in_source(str(caught.value), source, "broken.ges")
    assert _line_of(whole, "broken.ges") == line, (
        f"{what}: the workbench would draw this at line "
        f"{_line_of(whole, 'broken.ges')}\n  {whole.splitlines()[0]}")
