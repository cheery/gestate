#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-23 — "build a meter for sittings that I can track"
"""tools/sittings.py — the sittings, as they actually went.

    tools/sittings.py                 every day in the log
    tools/sittings.py --days 7        the last seven
    tools/sittings.py --log PATH      a different log
    tools/sittings.py --bare          one row per day, tab separated

**What it is for.**  `tools/limit.sh` asks for a length at the door and
says so when it is up.  Nothing said whether the limits were *kept* —
the nag is spoken once and evaporates, and the answer to *how is this
going* was a guess.  This is the pull side of that tool: one screen,
per day, from the ledger the hook already writes.

**It is a meter and not a nagger**, and the difference is the whole
design.  Nothing here runs on a hook, nothing warns, nothing arrives on
its own — it is read when somebody wants to know, which is the only
register in which a number about a person is read honestly rather than
resented.  `keeper.md` act 3 is where it belongs in a week.

**The one number to look at is the last column**, and it is the one a
nag cannot give you: how many times the limit was reached and a new
sitting was granted straight after it.  A limit that is never the end of
a sitting is either mis-sized or is not a limit, and which of those it is
is a question for the fire and not for a session.

**What it cannot see, stated.**  It reads arrivals and declarations —
when a prompt was typed, what length was asked for, when the hook
blocked.  It does not read strain, and it must not be read that way: a
long sitting is deep work or is not being able to stop, and this log
cannot tell them apart.  **And time at the desk is measured to the last
prompt**, because walking away leaves no event — every span here is a
floor, and the quiet hour after the last message is invisible.  It never
reads prompt text; the ledger does not contain any.

**Run it outside the fence.**  `tools/sandbox.sh` gives the run a tmpfs
`$HOME`, and the ledger lives in the real one — fenced, this prints *no
log* and means *no home*.  Nothing here executes dependency code, so
there is nothing for the fence to protect against, and a session that
reads the fenced answer as an empty week has concluded from the check
rather than from the world.

`tools/gapcheck.py` reads the same file for the other question — whether
the 30-minute silence that starts a fresh sitting is the right 30.
"""

import argparse
import datetime
import os
import pathlib
import sys

DEFAULT_LOG = pathlib.Path(
    os.environ.get("GESTATE_LIMIT_LOG",
                   pathlib.Path.home() / ".local/state/gestate/sittings.log"))

#: `grant` is the word Henri types; `open` is the hook noticing a fresh
#: sitting he did not declare.  Both start one, and the difference is
#: worth keeping: a declared sitting is a contract, an undeclared one is
#: the arrival the limit tool was built for.
STARTS = ("grant", "open")

#: **Not a person.**  A finished background agent or command is
#: delivered to the session as a prompt, so `limit.sh` saw it as an
#: arrival until 2026-08-23.  It is logged under its own name now and
#: skipped here entirely — not merely excluded from the count, because a
#: wake that extended a sitting's end would put the machine's working
#: hours into a person's day.
IGNORED = ("wake",)

#: **The day the ledger stopped counting machines.**  Rows before this
#: cannot be repaired: a notification then wrote `prompt`, `open` or
#: `block` and the log kept no source, so there is no way to tell them
#: from Henri afterwards.  Every day at or before this date is reported
#: with that said out loud rather than quietly averaged in.
WAKES_NAMED = "2026-08-23"


def read(path):
    """Every row, oldest first, as `(epoch, event, detail)`.

    `gapcheck.py` has a reader for the same file and it drops the third
    column; this one needs it, because the declared length lives in the
    `detail` of a `grant` and is the only record of what was promised.
    """
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            rows.append((int(parts[0]), parts[1], parts[2] if len(parts) > 2 else ""))
        except ValueError:
            continue
    rows.sort()
    return rows


def field(detail, key):
    """`min=45 gap=3` → the value of one key, or None."""
    for part in detail.split():
        if part.startswith(key + "="):
            try:
                return int(part[len(key) + 1:])
            except ValueError:
                return None
    return None


def sittings(rows):
    """Cut the log into sittings at every `grant` or `open`.

    Each is `{start, end, declared, blocks, override}`.  `override` is
    exact rather than inferred: the sitting is one whose **immediately
    preceding event was a block** — the limit was reached and the desk
    was taken again with nothing in between.
    """
    out = []
    previous = None
    for when, event, detail in rows:
        if event in IGNORED:
            continue
        if event in STARTS:
            out.append({"start": when, "end": when, "declared": field(detail, "min"),
                        "blocks": 0, "override": previous == "block",
                        "declared_by": event})
        elif out:
            out[-1]["end"] = when
            if event == "block":
                out[-1]["blocks"] += 1
        if event != "prompt" or previous != "prompt":
            previous = event
    return out


def by_day(items):
    """Sittings grouped by the local day they started on."""
    days = {}
    for s in items:
        key = datetime.date.fromtimestamp(s["start"]).isoformat()
        days.setdefault(key, []).append(s)
    return dict(sorted(days.items()))


def blocks_by_day(rows):
    """`block` events counted straight from the log, per day.

    **Not from the sittings**, and the first version of this file made
    exactly that mistake: a block attached to whichever sitting was open
    loses any block that lands before the log's first `grant`, and the
    totals then printed *"reached 8 times and taken again after 9 of
    them"* — a number that cannot be true, on its first run against real
    data.  The two things are counted from the same stream now, so the
    second can never exceed the first.
    """
    days = {}
    for when, event, _ in rows:
        if event == "block":
            key = datetime.date.fromtimestamp(when).isoformat()
            days[key] = days.get(key, 0) + 1
    return days


def hhmm(seconds):
    m = int(round(seconds / 60))
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log", type=pathlib.Path, default=DEFAULT_LOG)
    ap.add_argument("--days", type=int, default=0,
                    help="only the last N days that have rows")
    ap.add_argument("--bare", action="store_true",
                    help="tab separated, no headings, for grepping")
    args = ap.parse_args(argv)

    rows = read(args.log)
    if not rows:
        print(f"sittings: no log at {args.log}.  `tools/limit.sh --hook` "
              "writes it; nothing has arrived yet.")
        return 0

    days = by_day(sittings(rows))
    hits = blocks_by_day(rows)
    if args.days:
        days = dict(list(days.items())[-args.days:])

    if not args.bare:
        print(f"  {'day':<12}{'sat':>5}{'at the desk':>13}{'longest':>9}"
              f"{'declared':>10}{'limit hit':>11}{'sat again':>11}")
    totals = [0, 0, 0, 0]
    for day, items in days.items():
        desk = sum(s["end"] - s["start"] for s in items)
        longest = max(s["end"] - s["start"] for s in items)
        declared = [s["declared"] for s in items if s["declared"]]
        blocks = hits.get(day, 0)
        again = sum(1 for s in items if s["override"])
        totals = [totals[0] + len(items), totals[1] + desk,
                  totals[2] + blocks, totals[3] + again]
        shown = f"{min(declared)}–{max(declared)}m" if declared else "—"
        if len(set(declared)) == 1:
            shown = f"{declared[0]}m"
        if args.bare:
            print(f"{day}\t{len(items)}\t{desk}\t{longest}\t{blocks}\t{again}")
        else:
            print(f"  {day:<12}{len(items):>5}{hhmm(desk):>13}"
                  f"{hhmm(longest):>9}{shown:>10}{blocks:>11}{again:>11}")

    if args.bare:
        return 0
    sat, desk, blocks, again = totals
    print(f"\n  {len(days)} day(s), {sat} sitting(s), {hhmm(desk)} at the desk.")
    if blocks:
        print(f"  The limit was reached {blocks} time(s) and the desk was "
              f"taken again straight after {again} of them.")
        if again == blocks:
            print("  Every one of them.  That is a question for the fire — "
                  "either the limit is mis-sized, or it is not a limit.")
    else:
        print("  The limit was never reached.")
    print("  Time at the desk is a floor: walking away leaves no event.")
    stale = [d for d in days if d <= WAKES_NAMED]
    if stale:
        print(f"  {len(stale)} day(s) at or before {WAKES_NAMED} counted "
              "finished background tasks as arrivals; those rows cannot be "
              "told from a person now.  Read them as an upper bound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
