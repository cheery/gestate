#!/usr/bin/env python3
#: asked-by: unrecorded, 2026-08-22
"""tools/gapcheck.py — is 30 minutes the right silence gap?

    tools/gapcheck.py                    the arrivals so far, and what
                                         each candidate gap would do
    tools/gapcheck.py --log PATH         read a different log
    tools/gapcheck.py --days 7           only the last 7 days

`tools/limit.sh` calls a sitting **fresh** when the desk has been empty
for `GESTATE_LIMIT_GAP` minutes, default 30.  Nobody chose that 30 — a
session picked it while writing the script, which is exactly the defect
`fixme.md` F169 names: *a number nobody asked for is a number nobody
checks*.  `card:sitting-limit.md` lists it as unsettled.

**What this measures and what it does not.**  It measures arrivals: when
prompts were typed, and the silences between them.  It does not measure
strain, and the temptation to read it that way should be resisted for as
long as there is nothing to check the reading against — a short gap is a
person mid-thought, or a person who cannot leave.  The log cannot tell
those apart, and neither can a session.  What it can do is answer the
one question the number is for: **would a different threshold have cut
the days into different sittings?**  If every candidate agrees, the
number does not matter and 30 can stay on the grounds that nothing turns
on it.  If they disagree, the disagreement is the evidence.

The log holds timestamps and event names.  It has never held prompt
text.
"""

import argparse
import os
import pathlib
import time

CANDIDATES = (10, 15, 20, 30, 45, 60, 90)

DEFAULT_LOG = pathlib.Path(
    os.environ.get("GESTATE_LIMIT_LOG",
                   pathlib.Path.home() / ".local/state/gestate/sittings.log"))


def read(path):
    """Every arrival in the log, oldest first.  One (epoch, event) each."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            rows.append((int(parts[0]), parts[1]))
        except ValueError:
            continue
    rows.sort()
    return rows


def arrivals(rows):
    """The events that mean *Henri typed something*, which is all of them
    except `close` — that one is a session's call, not an arrival."""
    return [t for t, event in rows if event != "close"]


def sittings(times, gap_min):
    """Cut the arrivals into sittings at every silence of `gap_min`."""
    out = []
    for t in times:
        if out and (t - out[-1][-1]) / 60 < gap_min:
            out[-1].append(t)
        else:
            out.append([t])
    return out


def hhmm(seconds):
    m = int(round(seconds / 60))
    return f"{m//60}h{m%60:02d}m" if m >= 60 else f"{m}m"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=pathlib.Path, default=DEFAULT_LOG)
    ap.add_argument("--days", type=float, default=None)
    args = ap.parse_args()

    rows = read(args.log)
    if args.days is not None:
        floor = time.time() - args.days * 86400
        rows = [r for r in rows if r[0] >= floor]

    times = arrivals(rows)
    if len(times) < 2:
        print(f"gapcheck: {len(times)} arrivals in {args.log}")
        print("          not enough to say anything.  Come back in a few days.")
        return

    span = (times[-1] - times[0]) / 86400
    print(f"gapcheck: {len(times)} arrivals over {span:.1f} days"
          f"  ({time.strftime('%Y-%m-%d %H:%M', time.localtime(times[0]))}"
          f" .. {time.strftime('%Y-%m-%d %H:%M', time.localtime(times[-1]))})")
    print()

    gaps = sorted((b - a) / 60 for a, b in zip(times, times[1:]))
    bands = [(0, 2), (2, 5), (5, 10), (10, 15), (15, 20),
             (20, 30), (30, 45), (45, 60), (60, 120), (120, 1e9)]
    for lo, hi in bands:
        n = sum(1 for g in gaps if lo <= g < hi)
        if n:
            label = f"{lo:g}–{hi:g}m" if hi < 1e9 else f"{lo:g}m+"
            print(f"  {label:>9}  {'#' * n} {n}")
    print()
    print(f"  median gap {gaps[len(gaps)//2]:.0f}m,"
          f"  {sum(1 for g in gaps if g >= 30)} of {len(gaps)} at or over 30m")
    print()

    print("  what each candidate threshold would have done:")
    print(f"    {'gap':>5}  {'sittings':>8}  {'median length':>14}  {'longest':>8}")
    for cand in CANDIDATES:
        cut = sittings(times, cand)
        lengths = sorted(s[-1] - s[0] for s in cut)
        print(f"    {cand:>4}m  {len(cut):>8}  "
              f"{hhmm(lengths[len(lengths)//2]):>14}  {hhmm(lengths[-1]):>8}")
    print()
    print("  If those rows agree, the number does not matter.  If they")
    print("  disagree, the row that matches how the days actually felt")
    print("  is the answer — and only Henri can supply that half.")


if __name__ == "__main__":
    main()
