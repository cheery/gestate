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
FIXME = ROOT / "fixme.md"
TESTS = ROOT / "test"

#: The last entry that existed when `card:ungated-fixes.md` was written,
#: 2026-08-18.  Anything above it arrived after the rule was settled and
#: is the half the card could not reach.
BEFORE_THE_CARD = 161


def entries(text: str) -> dict:
    """`{F-number: its body}` — every entry the file holds."""
    parts = re.split(r"^### (F\d+)", text, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


def named_in_tests() -> set:
    """Every F-number some file under `test/` mentions."""
    out: set = set()
    for path in TESTS.rglob("*"):
        if path.is_file():
            try:
                out |= set(re.findall(r"\bF\d{1,3}\b", path.read_text(errors="ignore")))
            except OSError:
                continue
    return out


#: A verdict that names no instrument.  `none` is the sweep's own word
#: for *nothing in the tree would say so*, written after looking — which
#: is worth much more than silence and is still not a gate.
EMPTY = ("none", "none yet")


def verdict(body: str) -> str | None:
    """What an entry's `gate:` line says, or `None` if it has none."""
    said = re.search(r"^gate:\s*`?([a-z ]+)", body, re.M)
    return said.group(1).strip() if said else None


def bare(text: str, named: set) -> list:
    """The entries **nothing would catch** — no test names them, and
    their verdict either is missing or is `none`.  Oldest first."""
    out = []
    for f, body in entries(text).items():
        if f in named:
            continue
        said = verdict(body)
        if said is None or said in EMPTY:
            out.append(f)
    return sorted(out, key=lambda f: int(f[1:]))


def looked_at(text: str) -> list:
    """The entries the sweep read and marked `none` — ungated, and known
    to be.  These are not a backlog; they are an answer."""
    return sorted((f for f, body in entries(text).items()
                   if (verdict(body) or "") in EMPTY),
                  key=lambda f: int(f[1:]))


def main(argv: list[str]) -> int:
    text = FIXME.read_text(encoding="utf-8")
    held = entries(text)
    unnamed = bare(text, named_in_tests())
    since = [f for f in unnamed if int(f[1:]) > BEFORE_THE_CARD]
    marked = looked_at(text)
    print(f"{len(held)} entries — {len(unnamed)} that nothing would catch")
    print(f"  {len(unnamed) - len(since)} from before card:ungated-fixes.md, "
          f"{len(since)} since")
    print(f"  of them {len([f for f in unnamed if f in marked])} were read and "
          f"marked `none` by the sweep; the rest were never looked at")
    if "--list" in argv:
        print("\n  " + "\n  ".join(unnamed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
