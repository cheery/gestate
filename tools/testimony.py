#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-06 — "yes.  Do cards for these" and, mid-turn,
#: "and do the measurement as well." — card:testimony-inventory.md
"""tools/testimony.py — what each memory's load-bearing claim rests on

    python tools/testimony.py            the counts, and every memory with no row
    python tools/testimony.py --check    exit 1 when a row names a memory that is not there, or a kind that is not one
    python tools/testimony.py --kind session   the rows of one kind, with what each rests on

**The table is `doc/testimony.md` and the judgment in it is a
session's.**  This tool does not classify anything — a classifier that
reads a memory and decides whether it rests on a harness or on a
session's word would be a session's judgment wearing a program, which is
`doc/memory/the-evaluation-loop.md` with a green tick.  What it does is
hold the table to the tree: every row names a memory that exists, every
kind is one of the four, and the count on the page is the count the
table gives — so the page cannot quietly say 14 when the table says 15.

**Four kinds, and a memory gets one** — the one its load-bearing claim
rests on, not the one most of its sentences are:

    harness    a number, a test, a transcript, a command a reader can re-run
    henri      his decision or his words, quoted and dated — a rule by fiat
    session    a session's report of what it saw, judged or felt, with no command under it
    argument   reasoning from outside the tree — a book, a tradition, a mechanism named — unmeasured here

A memory with no row is **unclassified**, printed and not refused:
`card:testimony-inventory.md` Q1 — a gate here would make every new
memory cost a classification line from a session about its own claim.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "doc" / "testimony.md"
MEMORY = ROOT / "doc" / "memory"

KINDS = ("harness", "henri", "session", "argument")

#: `| name | kind | what it rests on |` — the first column a memory's id,
#: bare or as a `[[name]]` link.
ROW = re.compile(r"^\|\s*(?:\[\[)?([a-z0-9][a-z0-9-]*)(?:\]\])?\s*\|\s*(\w+)\s*\|\s*(.*?)\s*\|\s*$")


def memories(root: Path = ROOT) -> set[str]:
    return {p.stem for p in (root / "doc" / "memory").glob("*.md") if p.name != "README.md"}


def rows(page: Path = PAGE) -> list[tuple[str, str, str]]:
    out = []
    for line in page.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m and m.group(2) != "kind" and not set(m.group(2)) <= {"-"}:
            out.append((m.group(1), m.group(2), m.group(3)))
    return out


def counts(table) -> dict[str, int]:
    out = {k: 0 for k in KINDS}
    for _n, kind, _r in table:
        out[kind] = out.get(kind, 0) + 1
    return out


def faults(table, have: set[str]) -> list[str]:
    out = []
    seen: set[str] = set()
    for name, kind, _r in table:
        if name not in have:
            out.append(f"row names a memory that is not there: {name}")
        if kind not in KINDS:
            out.append(f"{name}: kind `{kind}` is not one of {', '.join(KINDS)}")
        if name in seen:
            out.append(f"{name} has two rows")
        seen.add(name)
    return out


def summary(table, have: set[str]) -> str:
    c = counts(table)
    n = len(table)
    line = ", ".join(f"{c[k]} {k}" for k in KINDS)
    missing = sorted(have - {name for name, _k, _r in table})
    out = [f"testimony: {n} of {len(have)} memories classified — {line}"]
    if missing:
        out.append(f"  unclassified ({len(missing)}): " + ", ".join(missing))
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--check", action="store_true", help="exit 1 on a row that does not resolve")
    ap.add_argument("--kind", choices=KINDS, help="list the rows of one kind")
    a = ap.parse_args(argv)
    if not PAGE.exists():
        print(f"testimony: no page at {PAGE}")
        return 1
    table = rows()
    have = memories()
    bad = faults(table, have)
    if a.check:
        for b in bad:
            print("testimony: " + b)
        print(summary(table, have).splitlines()[0])
        return 1 if bad else 0
    if a.kind:
        for name, kind, rests in table:
            if kind == a.kind:
                print(f"{name}\n    {rests}")
        return 0
    print(summary(table, have))
    for b in bad:
        print("testimony: " + b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
