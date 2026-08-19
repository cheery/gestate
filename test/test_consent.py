"""Nobody's name or words enter this tree before they have been asked.

**The repository is public**, so a commit is a publication, and a
person quoted in it has been published whether or not anyone meant to
publish them.  Henri, 2026-08-19: *"make sure that consentless reference
doesn't happen."*

`doc/consent.md` is the register.  This file is what makes it bite,
and it follows `test_board.py`'s call: **a rule that is executable
belongs in the suite**, not in a reviewer's memory.  The failure mode it
guards is not malice — it is a session writing *"a friend said"* into a
public file at the exact moment that felt like good attribution.

**What it can and cannot see.**  It reads *attribution positions* — the
two idioms this tree quotes people with — because that is how a person
actually gets into these files: as a voice.  It does not attempt to
recognise names generally; a scan of every capitalised word in the tree
returns 1067 tokens and would be a baseline nobody could read, which is
`manifesto.md`'s third failure mode wearing a green tick.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "doc" / "consent.md"

#: `Henri, 2026-08-19` and `Henri → Janne, 2026-08-18` — the dated
#: attribution idiom.
DATED = re.compile(
    r"\b([A-ZÅÄÖ][a-zåäö]{2,20})(?:\s*(?:→|->)\s*([A-ZÅÄÖ][a-zåäö]{2,20}))?,?\s*\d{4}-\d{2}-\d{2}"
)

#: `**Janne:** *"…"*` — a bold or italic lead-in followed by speech.
QUOTED = re.compile(
    r"(?:\*\*|\*)([A-ZÅÄÖ][a-zåäö]{2,20})(?:\s*(?:→|->)\s*([A-ZÅÄÖ][a-zåäö]{2,20}))?[,:]"
    r"[^\n]{0,40}?[*_]*\s*[*_]*[\"“>]"
)

#: Bold lead-ins and dated verbs that land in an attribution position
#: and are not anybody.  Kept explicit: a name added here instead of to
#: the register is the exact bypass this test exists to prevent, so the
#: list is short enough to read in one look.
NOT_A_PERSON = frozenset("""
    Added Adopted Agreed Amended Answered Argued Asked Built Checked
    Corrected Costs Established Open Picked Reproduced Started
    Buys Decided Diagnosis Done Filed Fixed Found Generated Imposed
    Kaizen Known Measured Mon Tue Wed Thu Fri Sat Sun Noted Offered
    Opened Predicted Recommendation Reported Resolution Resolved
    Shelved Shown Spent Status Steal Tried Unprompted Vacuous Verified
    Written From The This That And But For When Where With Then Only
    Both Each Every All Not None Three Two One Four Five Six Seen
""".split())

#: Cited the way a paper cites — not a consent question.
CITED = frozenset("Ohno Karplus Rizzo Strong Toyota Deming Shingo".split())

TEXT_SUFFIXES = (".md", ".py", ".rs", ".ges", ".toml")


#: Directories that are not this checkout's own text.  **`.claude` is
#: here because an agent worktree lives inside it** — a second checkout
#: under `ROOT`, whose documents would be read as this tree's and could
#: fail a gate on the main branch for something written on another one
#: (F175).  Found in `test_citations.py` first; the same walk is here.
NOT_OURS = (".git", "target", "__pycache__", ".claude", ".venv")


def documents() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.md")
        if not any(part in NOT_OURS for part in p.parts)
    )


def sources() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*")
        if p.suffix in TEXT_SUFFIXES
        and p.is_file()
        and not any(part in NOT_OURS for part in p.parts)
    )


def register() -> dict[str, dict[str, str]]:
    """The table in `doc/consent.md`, as `name -> {column: value}`."""
    rows: dict[str, dict[str, str]] = {}
    columns: list[str] = []
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
        if not columns:
            columns = cells
            continue
        if set("".join(cells)) <= set("- :"):
            continue
        rows[cells[0]] = dict(zip(columns[1:], cells[1:]))
    return rows


def attributions() -> dict[str, list[str]]:
    """Every name in an attribution position, and where it was found."""
    found: dict[str, list[str]] = {}
    for path in documents():
        text = re.sub(r"```.*?```", " ", path.read_text(encoding="utf-8"), flags=re.S)
        for pattern in (DATED, QUOTED):
            for match in pattern.finditer(text):
                for name in match.groups():
                    if name and name not in NOT_A_PERSON and name not in CITED:
                        found.setdefault(name, []).append(path.name)
    return found


def test_register_parses():
    """Nothing below means anything if the table does not read."""
    rows = register()
    assert rows, "doc/consent.md has no register table"
    for name, row in rows.items():
        assert "named" in row, f"{name} has no `named` column"


def test_everyone_quoted_is_in_the_register():
    """A person quoted anywhere is a person who had to be asked.

    Failing here is not a demand to edit this file.  It is the question
    arriving on time: **has that person agreed to be in a public
    repository?**  If the answer is yes, add the row.  If the token is
    not a person, add it to `NOT_A_PERSON` — and read it twice, because
    that is the door out of this check.
    """
    unknown = {n: w for n, w in attributions().items() if n not in register()}
    assert not unknown, (
        "quoted in the tree and not in doc/consent.md: "
        + "; ".join(f"{n} ({', '.join(sorted(set(w))[:3])})" for n, w in sorted(unknown.items()))
    )


def test_nobody_who_said_no_is_here():
    """`named: no` is a hard floor — the name comes out of the tree."""
    refused = [n for n, row in register().items() if row.get("named") == "no"]
    for name in refused:
        hits = [p.relative_to(ROOT) for p in sources()
                if p != REGISTER and re.search(rf"\b{re.escape(name)}\b", p.read_text(encoding="utf-8", errors="replace"))]
        assert not hits, f"{name} declined to be named and appears in {hits[:5]}"


#: Published before being asked.  **May shrink, never grow.**  It stood
#: at 1 for a few hours on 2026-08-19 — Janne, named on 2026-08-18 and
#: asked the next day — and he said yes the same day it was put to him.  **Zero is now a
#: hard floor**: nobody else gets into this public tree unasked, and
#: raising this number is not the way to make the suite green.
PENDING_BASELINE = 0


def test_the_unasked_debt_does_not_grow():
    pending = [n for n, row in register().items() if row.get("named") == "pending"]
    assert len(pending) <= PENDING_BASELINE, (
        f"{len(pending)} people are in this public tree unasked "
        f"({', '.join(sorted(pending))}); the baseline is {PENDING_BASELINE}. "
        "Ask, or take the words out — do not raise the number."
    )


def test_training_consent_is_not_assumed():
    """Naming is reversible; training is not.  No row may say yes to
    training without a date beside the ask."""
    for name, row in register().items():
        if row.get("training", "").lower().startswith("yes"):
            assert row.get("asked", "") not in ("", "—", "-"), (
                f"{name} is marked yes to training with no record of being asked"
            )
