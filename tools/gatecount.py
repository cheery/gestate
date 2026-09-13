#!/usr/bin/env python3
"""How many of `fixme.md`'s entries are named by no instrument.

    python tools/gatecount.py [--list]

#: asked-by: Henri, 2026-08-18 — "we need computer systems that are learning
#: from their failures and get stronger and stronger by same mechanism that
#: they are pummeled" — card:ungated-fixes.md, whose closing measurement this
#: is; built 2026-09-10 when the card closed, so the next reading is one line

**What it counts, and what that is worth.**  An entry is *named* when
some file under `test/` mentions its F-number, or when the entry itself
carries a `gate:` line saying which instrument holds it.  That is a
proxy and the card says so: it measures whether a fix left an *address*
pointing back at the failure, not whether the instrument would catch it.
A gate can exist and never name its number.  Read a rise as a question,
not as a verdict.

**Why the number is worth watching.**  `card:ungated-fixes.md` swept 62
ungated repairs across thirteen sessions and closed on 2026-09-04 with
92 `gate:` lines written.  Six days later the count was 62 again — a
different 62, 19 of them entries that had arrived since.  The sweep
cleared its tail and the file refilled at about the rate it was being
cleared, because the rule the card settled (bind every new closure) is
enforced by nothing.  So this is the instrument the card's own
postcondition needs and did not get.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "fixme"
TESTS = ROOT / "test"

#: The last entry that existed when `card:ungated-fixes.md` was written,
#: 2026-08-18.  Anything above it arrived after the rule was settled and
#: is the half the card could not reach.
BEFORE_THE_CARD = 161


#: An entry's file and the heading that opens it.
ENTRY_FILE = re.compile(r"F(\d+)\.md")
HEAD = re.compile(r"# (F\d+)(?=\.)")


def entries(ledger: Path = LEDGER) -> dict:
    """`{F-number: its body}` — every entry the ledger holds, by number.

    One file an entry since 2026-09-13, `fixme/F123.md`, opening with
    `# F123. **[marker]** title`.  The body starts after the number, at
    the `.`, exactly where it started when this split one file on its
    `### F123` headings — so `marker` and `verdict` read it unchanged.
    A file whose heading is not its own number is left out, and
    `test/test_fixme.py` names it."""
    out = {}
    for path in sorted(ledger.glob("F*.md"), key=lambda p: int(p.stem[1:]) if p.stem[1:].isdigit() else -1):
        name, text = ENTRY_FILE.fullmatch(path.name), path.read_text(encoding="utf-8")
        head = HEAD.match(text)
        if name and head and head.group(1) == f"F{name.group(1)}":
            out[head.group(1)] = text[head.end():]
    return out


def misnamed(ledger: Path = LEDGER) -> list:
    """The files under the ledger `entries` cannot read as the entry their
    name says — a copied file whose heading kept the old number, say."""
    out = []
    for path in ledger.glob("F*.md"):
        head = HEAD.match(path.read_text(encoding="utf-8"))
        if not (ENTRY_FILE.fullmatch(path.name) and head and head.group(1) == path.stem):
            out.append(path.name)
    return sorted(out)


#: **The gate's own baseline does not count as naming anything.**
#: `test/test_fixme.py` lists the entries nothing catches, so a plain
#: scan of `test/` reads that list as fifteen tests naming fifteen
#: F-numbers and the whole set disappears — a gate that made its own
#: subject vanish, found the minute it first ran, 2026-09-10.
NOT_A_GATE = ("test_fixme.py",)

#: **And a compiled copy is not a test either.**  Excluding the
#: baseline by name left `__pycache__/test_fixme.cpython-*.pyc`, which
#: holds the same fifteen strings, so the set half-vanished instead of
#: vanishing — 27 where the truth was 41, which is worse than the first
#: failure because it looks like an answer.  Found the same minute,
#: 2026-09-10.
def _readable(path: Path) -> bool:
    return (path.is_file() and path.suffix != ".pyc"
            and "__pycache__" not in path.parts
            and path.name not in NOT_A_GATE)


def named_in_tests() -> set:
    """Every F-number some file under `test/` mentions — except the
    gate's own baseline, which names them in order to refuse them."""
    out: set = set()
    for path in TESTS.rglob("*"):
        if _readable(path):
            try:
                out |= set(re.findall(r"\bF\d{1,3}\b", path.read_text(errors="ignore")))
            except OSError:
                continue
    return out


#: What a marker means *the defect is closed*.  The gate covers these
#: and nothing else: an unfixed defect is honest about itself, and a
#: test for it is a different argument (`card:ungated-fixes.md`
#: §"What this is not").  **`partly resolved` is here on purpose** —
#: batch 13's finding was that *a resolution which names its own
#: outstanding half is an open defect wearing a closed marker*, and
#: the marker is what a reader trusts.
CLOSED = ("resolved", "fixed", "partly resolved")

#: Every marker the file actually uses.  Pinned so that a **new** word
#: cannot quietly carry an entry out of the gate's reach: a marker
#: added here is a decision, and one added only to `fixme.md` is a
#: red test asking whether it means closed.
MARKERS = CLOSED + ("bug", "missing", "open", "deviates")


#: A verdict that names no instrument.  `none` is the sweep's own word
#: for *nothing in the tree would say so*, written after looking — which
#: is worth much more than silence and is still not a gate.
EMPTY = ("none", "none yet")


def verdict(body: str) -> str | None:
    """What an entry's `gate:` line says, or `None` if it has none."""
    said = re.search(r"^gate:\s*`?([a-z ]+)", body, re.M)
    return said.group(1).strip() if said else None


def bare(held: dict, named: set) -> list:
    """The entries **nothing would catch** — no test names them, and
    their verdict either is missing or is `none`.  Oldest first."""
    out = []
    for f, body in held.items():
        if f in named:
            continue
        said = verdict(body)
        if said is None or said in EMPTY:
            out.append(f)
    return sorted(out, key=lambda f: int(f[1:]))


def marker(body: str) -> str | None:
    """What an entry's `**[…]**` marker says, or `None`."""
    said = re.match(r"\.\s+\*\*\[([^\]]+)\]\*\*", body)
    return said.group(1) if said else None


def unheld_closures(held: dict, named: set) -> list:
    """**What the gate refuses**: entries whose marker claims the defect
    is closed and which nothing in the tree would catch coming back.

    This is the postcondition of `card:ungated-fixes.md` written as a
    set — *a defect that was fixed once cannot come back without
    something in the tree going red first* — and `test/test_fixme.py`
    holds it against a baseline that may shrink and never grow.
    """
    bare_now = set(bare(held, named))
    return sorted((f for f, body in held.items()
                   if marker(body) in CLOSED and f in bare_now),
                  key=lambda f: int(f[1:]))


def looked_at(held: dict) -> list:
    """The entries the sweep read and marked `none` — ungated, and known
    to be.  These are not a backlog; they are an answer."""
    return sorted((f for f, body in held.items()
                   if (verdict(body) or "") in EMPTY),
                  key=lambda f: int(f[1:]))


def main(argv: list[str]) -> int:
    held = entries()
    unnamed = bare(held, named_in_tests())
    since = [f for f in unnamed if int(f[1:]) > BEFORE_THE_CARD]
    marked = looked_at(held)
    print(f"{len(held)} entries — {len(unnamed)} that nothing would catch")
    print(f"  {len(unnamed) - len(since)} from before card:ungated-fixes.md, "
          f"{len(since)} since")
    print(f"  of them {len([f for f in unnamed if f in marked])} were read and "
          f"marked `none` by the sweep; the rest were never looked at")
    closed = unheld_closures(held, named_in_tests())
    print(f"{len(closed)} of them **claim to be closed** — the gate's set, "
          f"held by test/test_fixme.py")
    if "--list" in argv:
        print("  " + " ".join(closed))
    if "--list" in argv:
        print("\n  " + "\n  ".join(unnamed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
