"""The rules set against its cap — `spec/rules.md` is the contract.

The five documents a session reads *before it knows what it is working
on*.  They are charged to every shift at full size, out of the same
window the work has to fit in, which is why they have a ceiling and
`spec/` does not.

In `tools/suite.py`'s `GATES` as `test/test_rules.py` since 2026-08-20,
the morning the count first came in under the cap — which was the
condition `spec/rules.md` §"The proof" set for it.  This script stays
because it prints the *room left*, which a green gate does not.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: **Closed at five.**  A sixth document is a cheat: it moves the
#: per-file numbers without moving what a session must read.  Adding a
#: line here is changing the contract, and wants Henri, in writing,
#: with the date — same as changing CAP.
RULES = (
    "board/README.md",
    "manifesto.md",
    "spec/author.md",
    "doc/instruments.md",
    "vision.md",
)

#: Henri, 2026-08-20: *"2000 lines, for now."*
CAP = 2000


def counts() -> list[tuple[str, int]]:
    out = []
    for name in RULES:
        path = ROOT / name
        n = len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else -1
        out.append((name, n))
    return out


def main() -> int:
    rows = counts()
    missing = [name for name, n in rows if n < 0]
    total = sum(n for _, n in rows if n >= 0)

    width = max(len(name) for name, _ in rows)
    for name, n in rows:
        print(f"  {name:<{width}}  {'gone' if n < 0 else n:>5}")
    print(f"  {'':<{width}}  {'':>5}")
    print(f"  {'total':<{width}}  {total:>5}   cap {CAP}")

    if missing:
        print(f"\nrulecount: {', '.join(missing)} is not there — "
              "the set is closed at five, and losing one is not a way "
              "under the cap.  spec/rules.md.")
        return 1

    if total > CAP:
        print(f"\nrulecount: **over by {total - CAP}**.  The fat is session "
              "narration; it belongs in journal.md, a card, or nowhere.  "
              "Not the dates, and not a sixth file.  spec/rules.md.")
        return 1

    print(f"\nrulecount: under, with {CAP - total} lines of room.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
