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


def test_the_pointer_is_one_line_and_points_at_the_board():
    """`AGENTS.md`, capped at one line by the same hand that capped the five.

    **Why it exists.**  Until 2026-08-23 nothing loaded the five
    documents.  There was no `CLAUDE.md`, no `AGENTS.md`, and neither
    hook in `.claude/settings.json` injects anything — so a session met
    them only by choosing to go and read, and `rulecount.py`'s own
    justification for the cap (*"charged to every shift at full size"*)
    was describing a cost nobody was paying.  What did arrive at every
    boot was the memory index: 57 lines, outside the cap, and on
    2026-08-23 two agents that read nothing at all quoted house rules
    that live only in `doc/memory/`.

    Henri's call the same evening: **one line, and the line is the
    pointer.**  It makes the cap's premise true rather than aspirational.

    **One line is the whole discipline.**  A pointer that starts
    explaining is a sixth method document arriving through a side door,
    and it would be charged to every session at whatever size it drifted
    to, which is the tax the cap exists to hold.  So the size is checked
    rather than intended.

    **It is deliberately not in `RULES`.**  That set is closed at five
    and `rulecount.py` says changing it wants Henri in writing with a
    date.  A file whose entire content is a path is a signpost and not a
    document — but the call is his, and if it should be counted, this
    docstring is the place that was wrong.
    """
    pointer = ROOT / "AGENTS.md"
    assert pointer.exists(), (
        "AGENTS.md is gone, and with it the only thing that makes a "
        "session read the board before it knows what it is working on.")

    lines = pointer.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1, (
        f"AGENTS.md is {len(lines)} lines and may be one.  Henri, "
        "2026-08-23: it is a pointer, not a document — anything worth "
        "saying goes in board/README.md, which is what it points at.")
    assert "board/README.md" in lines[0], (
        f"AGENTS.md says {lines[0]!r} and must name board/README.md; "
        "a pointer that points somewhere else is a redirect nobody voted "
        "for.")


def _five():
    return {name: (ROOT / name).read_text(encoding="utf-8") for name in rulecount.RULES}


def test_no_rule_is_stated_twice_across_the_five():
    """One rule, one place, the others citing it.

    `card:working-standard.md` found on 2026-08-18 that the two-writers
    rule was stated three times in one file and the andon explained in
    five documents; the 2026-08-20 trim consolidated both, and until
    2026-08-24 nothing would have noticed them coming back.  A bold run
    of thirty characters or more is how a rule is stated in these
    documents, and the same one in two of them is a duplicate."""
    import re
    seen = {}
    for name, text in _five().items():
        for rule in set(re.findall(r"\*\*([^*\n]{30,})\*\*", text)):
            seen.setdefault(rule.strip().rstrip(".").lower(), set()).add(name)
    twice = {r: sorted(d) for r, d in seen.items() if len(d) > 1}
    assert not twice, "stated in more than one of the five:\n  " + "\n  ".join(
        f"{r!r}: {', '.join(d)}" for r, d in sorted(twice.items()))


def test_each_tool_is_explained_in_one_document():
    """A `### \`tools/…\`` heading is where a tool is explained.  Two
    documents explaining the same tool is the andon-in-five-places
    defect, which is what `doc/instruments.md` exists to end."""
    import re
    where = {}
    for name, text in _five().items():
        for tool in re.findall(r"^### `(tools/[\w./-]+)", text, re.M):
            where.setdefault(tool, set()).add(name)
    twice = {t: sorted(d) for t, d in where.items() if len(d) > 1}
    assert not twice, twice
