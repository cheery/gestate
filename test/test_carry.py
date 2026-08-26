"""`workbench._carry` — the seam, held to the *set* of fields.

**A rule in prose did not hold this seam.**  `spec/verification.md`
§"The defect is in the seam, and the test is in the module" was written
at midday on 2026-08-18 and the same function dropped a field twice more
before the day was out, crashing the editor in Henri's hands both times
(`card:carried-state.md`).  Every one of those was closed with a test
naming *that* field — `test_gemba.py` has two and `test_sessionlog.py`
has two — and none of them could fail for the twenty-fifth field,
because none of them knows how many there are.

**So this is a roster**, the shape this tree already uses three times:
`test_every_audio_example_is_exercised_here`,
`test_every_gui_example_is_exercised_here` and
`test_every_module_has_a_lane`.  A roster does not test behaviour.  It
takes the real set — here, `dataclasses.fields(Session)` — and refuses
to let a list fall behind it.

**Henri, 2026-08-19, choosing it over the larger change:** *"do the
roster first.  I'm not convinced that the carried state itself is bad.
Lets try it and see what happens to the problem."*  The card's other
question — whether the window should keep one `Session` and swap the
instrument inside it, leaving no seam to forget — stays open on purpose,
and this roster is what would make that rewrite safe to attempt: it
would say at once if the new design dropped a field.

**What this cannot check.**  That a field is on the *right* list.  No
test can read a mind; what it can do is make a new field a decision
somebody takes, instead of a line somebody forgets.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_session import Bench                                   # noqa: E402

from gestate.session import Session                              # noqa: E402
from gestate.workbench import _carry                             # noqa: E402


#: **Every field that must NOT survive a switch, and why.**
#:
#: This is the half of the roster a person writes.  A field lands here
#: because starting the next instrument *without* it is the right
#: behaviour — not because carrying it was never considered.  The
#: reasons are taken from each field's own comment in `session.py`; a
#: field whose reason cannot be written is a field somebody has to look
#: at, which is the whole point of being made to write one.
DELIBERATELY_FRESH = {
    "said": "the status line's history, and the switch says `opened <name>` "
            "as its first line — carrying the old file's sentences would "
            "make the new window claim things about a piece it never had",
    "transient": "a sentence standing *while long work runs*, and the work "
                 "belonged to the instrument being retired",
    "performing": "what a played note does; a new file is opened to be read "
                  "at least as often as to be played (`session.py`'s own "
                  "argument for it starting `off`)",
    "page": "what `what` last found — an answer about the old program",
    "asking": "which argument the *old* window was asking about; a "
              "half-finished question does not survive its subject",
    "filtered": "what `filter` last produced, over the old file's list",
    "confirming": "an export waiting on a yes, for a piece no longer open — "
                  "carrying this would export the wrong thing on a keypress",
    "_reading": "`(sha, path)` of the file the log last showed",
    "_diff_base": "the old file's lines at the commit the diff is against — "
                  "keyed by path, and the new file's are read on its first "
                  "poll; `_diffing` itself is carried",
    "_diff_last": "the last diff made, of the old text",
    "proposed": "the `(verb, argument)` a name was already filled into",
    "given": "the arguments the old box was holding",
    "holding": "a note a hand has hold of in a score box, between press and "
               "release — there is no hand on the new file",
    "marked": "`(text, holes)` — the program the hole marks were true for, "
              "and it is not this one",
    "_answered": "`(question, answer)` from the old program's choices, kept "
                 "only so an unchanged poll costs a comparison",
    "_fillers": "the tail of the old window's `wants`",
    "_looked": "when the world outside was last looked at — cheap to redo, "
               "and a stale token is worse than none",
    "_episode": "the dialog in progress, flushed into the log when its "
                "command runs; the command is not going to run now",
    "inserted": "a template pasted and not yet kept — it belongs to the "
                "text that was on screen",
}

#: `bench` is the switch itself: the new instrument is the reason
#: `_carry` was called, so it is neither carried nor deliberately fresh.
THE_SWITCH = {"bench"}


def _assigned_in_carry() -> set[str]:
    """Which fields `_carry` actually sets, read off the source.

    Read rather than declared, so this cannot agree with a list that
    has itself gone stale — the failure `card:ungated-fixes.md` is about
    one layer up.
    """
    return set(re.findall(r"\bfresh\.([A-Za-z_]+)\s*=",
                          inspect.getsource(_carry)))


def test_every_field_is_carried_or_deliberately_fresh():
    """**The roster.**  A twenty-sixth field fails this until somebody
    says which side it is on.

    That is the whole of it.  The two crashes this card is named for
    were both a field added in one file and not mentioned in the other,
    and both were found by Henri opening a file rather than by anything
    here.
    """
    fields = {f.name for f in dataclasses.fields(Session)}
    carried = _assigned_in_carry()
    accounted = carried | set(DELIBERATELY_FRESH) | THE_SWITCH

    unplaced = fields - accounted
    assert not unplaced, (
        "these `Session` fields are new and nobody has said what a file "
        "switch should do with them:\n  "
        + "\n  ".join(sorted(unplaced))
        + "\n\ncarry it in `workbench._carry`, or name it in this file's "
          "DELIBERATELY_FRESH with the reason. A field that resets "
          "silently is how this seam crashed the editor twice in one day.")

    gone = accounted - fields
    assert not gone, (
        "these are named here and are not `Session` fields any more "
        "(renamed? removed?):\n  " + "\n  ".join(sorted(gone)))

    both = carried & set(DELIBERATELY_FRESH)
    assert not both, (
        "carried by `_carry` *and* listed as deliberately fresh — one of "
        "the two is wrong:\n  " + "\n  ".join(sorted(both)))


def test_the_roster_is_not_vacuously_satisfied():
    """A roster that names nothing passes forever.

    `test_atlas.py` learned this the same way: the check that lists
    zero things is green and worthless.
    """
    assert len(dataclasses.fields(Session)) >= 20
    assert len(_assigned_in_carry()) >= 5


# ── and the behaviour, because a roster cannot see a wrong carry ─────────


def test_what_is_carried_actually_survives_the_switch(tmp_path):
    """The roster says a field was *considered*; this says it arrives.

    A line reading `fresh.walk = session.walk` satisfies any roster and
    could still be `fresh.walk = session.walking`.  So every carried
    field is given a value nothing else would produce, and looked for on
    the far side.
    """
    old = Session(bench=Bench())
    marks = {}
    for name in sorted(_assigned_in_carry()):
        if name in ("walk", "log"):
            continue                      # objects with their own rules, below
        marks[name] = f"carried-{name}"
        setattr(old, name, marks[name])

    fresh = _carry(old, Bench())
    for name, value in marks.items():
        assert getattr(fresh, name) == value, (
            f"`{name}` is assigned in `_carry` and did not arrive — "
            "the seam names it and carries something else")


def test_what_is_deliberately_fresh_is_actually_fresh(tmp_path):
    """The other direction, which is the one that would catch a carry
    added by accident — a field quietly starting to survive is as much
    a defect as one quietly resetting, and nothing would report it."""
    defaults = Session(bench=Bench())
    old = Session(bench=Bench())
    for name in DELIBERATELY_FRESH:
        setattr(old, name, f"stale-{name}")

    fresh = _carry(old, Bench())
    for name in DELIBERATELY_FRESH:
        assert getattr(fresh, name) == getattr(defaults, name), (
            f"`{name}` is listed as deliberately fresh and survived the "
            "switch — either `_carry` grew a line, or this file is wrong "
            "about what a switch should do")
