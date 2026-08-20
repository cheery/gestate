"""The rules set against its cap — `spec/rules.md` is the contract.

**Held out of the suite until the count came in under.**  A gate that is
red the day it arrives blocks every commit for work that has nothing to
do with it, so `tools/rulecount.py` was run by hand from 2026-08-20
until the trim landed the same morning.  This file is that condition
being met: from here it is the ordinary defect class the gates live on,
a structural check that a session doing ordinary work breaks.

**What it is really guarding is the context window.**  The five
documents are read *before a session knows what it is working on*, so
they are charged to every shift at full size, out of the same window the
work has to fit in.  `spec/` is 16,000 lines and costs nothing until you
touch the part it describes; that is the property the rules lack, and
the reason they are the only documents in this tree with a ceiling.

The failure it catches is not carelessness — it is pride.  A session
that has just arrived at a rule writes down how it got there, and the
arriving goes into the rule document because that is where the rule is.
`journal.md` is where the arriving belongs.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import rulecount  # noqa: E402


def test_the_five_are_all_there():
    """Losing one is not a way under the cap.

    The set is closed at five — `spec/rules.md` §"The three cheats" —
    so a missing file is a contract change, and a contract change wants
    Henri, in writing, with the date.
    """
    gone = [name for name, n in rulecount.counts() if n < 0]
    assert not gone, (
        f"{', '.join(gone)} is not where the rules set says it is.  "
        f"The set is closed at five and deleting one does not meet the "
        f"cap, it abandons it — spec/rules.md.")


def test_the_lamp_works():
    """**The cap is an andon, not a refusal** — Henri, 2026-08-20:
    *"make it light the andon."*

    Growth in the method is a visible event, not a forbidden one: a
    genuine amendment arrives with a good reason and no room, and a gate
    that refuses it teaches the next session to make the method worse in
    smaller words.  The lamp is `tools/suite.py`'s, lit on `test/gates.md`
    and at every commit through the hook.

    So what is left to test here is the lamp itself, and it is worth
    testing for the reason `manifesto.md` gives about every instrument:
    a signal that cannot fire is indistinguishable from a system that is
    fine.  A cap nobody can see reached is a mood again.
    """
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import suite

    total, cap = suite._rules_total()
    assert total > 0 and cap > 0, "the counter reported nothing to count"

    assert bool(suite._rules_andon()) == (total > cap), (
        f"the rules are {total} against a cap of {cap}, and the andon "
        f"{'did not light' if total > cap else 'lit anyway'}.  "
        f"tools/suite.py §_rules_andon.")

    real = rulecount.CAP
    try:
        rulecount.CAP = 1
        lit = suite._rules_andon()
    finally:
        rulecount.CAP = real
    assert lit and any("over their cap" in line for line in lit), (
        "the andon does not light even when the rules are over by "
        "everything.  A lamp that cannot come on is worse than no lamp: "
        "it reads as a tree that is fine.")
