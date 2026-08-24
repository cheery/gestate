#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-18 — "Question into existence is critical if if prevents us to accumulate cards like crazy."
"""tools/arrivals.py — how many cards were minted, per day.

    python tools/arrivals.py            the last fourteen days
    python tools/arrivals.py --days N

**The rule travels with a measurement attached, not as doctrine.**
`card:working-standard.md` §"The questions, answered": Henri did not say
*question it into existence* is critical, he said it is critical *if*
it works, and the thing that shows whether it works is this number.
Nineteen cards in two days is what made `board/later/` necessary;
one a day is what the filter looks like holding.

A card is a file added under `board/` or `board/later/`, by the commit
that added it.  Moves between shelves are not arrivals.  The number is
drawn on `test/gates.md` at every commit and fails nothing — a lamp,
like the cap, because a refusal would teach the next session to fold
two problems into one card.
"""
import argparse
import collections
import datetime
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent


def counts(days=14, today=None):
    """[(date, cards minted)] for the last `days` days, oldest first,
    zero-filled."""
    today = today or datetime.date.today()
    since = today - datetime.timedelta(days=days - 1)
    out = subprocess.run(
        ["git", "-C", str(ROOT), "log", f"--since={since:%Y-%m-%d}",
         "--diff-filter=A", "--name-only", "--format=%ad", "--date=short",
         "--", "board/*.md", "board/later/*.md"],
        capture_output=True, text=True).stdout
    per = collections.Counter()
    day = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[:4].isdigit() and len(line) == 10:
            day = datetime.date.fromisoformat(line)
        elif line.endswith(".md") and not line.endswith("README.md") and day:
            per[day] += 1
    return [(since + datetime.timedelta(days=i), per[since + datetime.timedelta(days=i)])
            for i in range(days)]


def week(today=None):
    return sum(n for _, n in counts(7, today))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()
    rows = counts(args.days)
    for day, n in rows:
        print(f"  {day}  {'#' * n}{' ' if n else ''}{n}")
    print(f"\narrivals: {sum(n for _, n in rows)} cards in {args.days} days, "
          f"{week()} in the last seven")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
