"""The gate `card:ungated-fixes.md` owed and did not build.

**The postcondition, from that card:** *a defect that was fixed once
cannot come back without something in the tree going red first.*  The
card swept 62 ungated entries across thirteen sessions, settled the two
rules — a gate is an **instrument** and not only a test, and closures
bind from 2026-08-18 on rather than retroactively — and closed on
2026-09-10 with its postcondition unmet, because nothing enforced the
rule on a *new* closure.  Six days after the last batch the count was
back, three of it entries written after the rule was agreed.  This file
is the enforcement, at Henri's ask the same day.

**What it refuses.**  An entry whose marker claims the defect is closed
and which nothing in the tree would catch coming back.  *Held* means a
file under `test/` names its F-number, or the entry's own `gate:` line
names an instrument.  An entry still open is not covered at all: an
unfixed defect is honest about itself, and a test for one is a
different argument.

**The baseline is a ratchet.**  `ACCEPTED` below is the fifteen that
were true on the day this landed, named rather than hidden, because a
gate that arrives red teaches the next reader to skip it — the shape
`test/fmt/test_roundtrip.py` used first.  **It may shrink and never
grow**, and gating an entry while leaving its name here fails just as
loudly as writing a new ungated closure, which is what keeps a baseline
from becoming a graveyard.

**What this cannot catch.**  The rule under it is a proxy and the card
says so: it measures whether a closure left an *address* pointing back
at the failure, not whether the instrument would catch it.  A gate can
exist and never name its number, and a `gate:` line can name a test
that would pass with the fix reverted.  What answers *that* is mutation,
which is the sweep's own method and costs an afternoon per entry.  This
costs milliseconds and holds the cheap half — that a closure says where
its gate is at all.

**And the converse, found while mutation-checking this file:** a test
that merely *mentions* an F-number holds it as far as this gate can
see.  `test_blind.py` uses `F999` as a fixture, so an entry numbered
F999 would pass unheld.  The proxy is a proxy in both directions and
neither is worth closing with a stricter regex — what would close it is
naming the instrument in the entry, which is the `gate:` line, and this
gate is what asks for one.

**Mutation-checked on the day it landed**, three ways: a new
`[resolved]` entry with nothing holding it goes red by name; a `gate:`
line added to an accepted entry goes red on the *other* jaw, naming the
line to delete; and a marker the gate has never read goes red asking
what it means.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import gatecount                                             # noqa: E402

FIXME = ROOT / "fixme.md"

#: **The fifteen true on 2026-09-10, and this set may shrink and never
#: grow.**  Twelve are from before `card:ungated-fixes.md` and were left
#: as they are by his answer to its question 2 — *"From now here on I
#: think"* — and three (F173, F185, F215) were written after the rule
#: was settled and are the reason this file exists.
ACCEPTED = frozenset({
    "F12", "F21", "F31", "F38", "F40", "F68", "F106", "F112", "F119",
    "F123", "F135", "F153", "F173", "F185", "F215",
})

#: How to make one of these go away, said once so that a red test does
#: not send somebody to guess.
HOW = ("write the instrument and name the entry's F-number in it, or "
       "add a `gate:` line to the entry naming the instrument that "
       "already holds it — then delete the number from ACCEPTED in "
       "test/test_fixme.py.  `gate: none` is an honest verdict and is "
       "not a gate: it says the defect can come back silently, and it "
       "keeps the entry in this set.")


def _text() -> str:
    return FIXME.read_text(encoding="utf-8")


def _unheld() -> set:
    return set(gatecount.unheld_closures(_text(), gatecount.named_in_tests()))


def test_no_new_closure_is_ungated():
    """A defect marked closed with nothing to catch it coming back.

    This is the card's postcondition, and the day it goes red the entry
    named is a hole somebody opened today."""
    new = sorted(_unheld() - ACCEPTED, key=lambda f: int(f[1:]))
    assert not new, (
        "fixme.md marks these closed and nothing in the tree would catch "
        f"them coming back: {', '.join(new)}.\n{HOW}")


def test_the_baseline_only_shrinks():
    """The ratchet's other jaw.

    A name left here after its entry was gated is a baseline rotting
    into a graveyard — the list stops being read and the gate stops
    tightening.  So repairing one and forgetting this file is a failure
    too, and the message says exactly which line to delete."""
    gone = sorted(ACCEPTED - _unheld(), key=lambda f: int(f[1:]))
    assert not gone, (
        f"these are gated now and are still named as accepted: {', '.join(gone)}."
        "\nDelete them from ACCEPTED in test/test_fixme.py — the baseline "
        "may shrink and never grow, and this is the shrinking.")


def test_every_marker_is_one_the_gate_has_read():
    """A **new** marker word must not carry an entry out of reach.

    The gate covers `resolved`, `fixed` and `partly resolved`.  If a
    future entry says `[done]` or `[closed]`, everything above would
    pass and the entry would be outside the rule without anybody
    choosing that.  So the vocabulary is pinned: a word added to
    `fixme.md` and not to `gatecount.MARKERS` is a red test asking
    whether it means the defect is closed."""
    seen = {gatecount.marker(body) for body in gatecount.entries(_text()).values()}
    unknown = sorted(m for m in seen if m and m not in gatecount.MARKERS)
    assert not unknown, (
        f"fixme.md uses markers the gate has never read: {', '.join(unknown)}. "
        "Add each to `gatecount.CLOSED` if it means the defect is closed, or "
        "to `gatecount.MARKERS` if it does not.")


def test_an_entry_with_no_marker_at_all_is_refused():
    """Every entry says what it is.  A heading with no `**[…]**` is
    outside every reading above, and the file has none today."""
    bare = sorted((f for f, body in gatecount.entries(_text()).items()
                   if gatecount.marker(body) is None), key=lambda f: int(f[1:]))
    assert not bare, (
        f"these entries carry no `**[…]**` marker: {', '.join(bare)}; "
        "the gate cannot tell whether they claim to be closed.")
