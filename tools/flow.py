#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-04 — "virtauksen mittaaminen todella voitaisiin tehdä nyt näkyväksi" — and the lamp: "se voisi olla kortit joihin ei ole koskettu 7 päivään, niiden pitäisi mennä later/ hyllyyn meidän kauttamme."
"""tools/flow.py — the board's flow, and the seven-day lamp.

    python tools/flow.py               the report: lead times, open cards by age
                                       and by last touch, arrivals against drain
    python tools/flow.py --check       the lamp: exit 2 and the names when a live
                                       card has not been touched for STALE_DAYS
    python tools/flow.py --days N      another threshold
    python tools/flow.py --root PATH   another tree (tests)

**What this makes visible.**  The board is priority, not order, and
nothing measured whether the order moved.  On 2026-09-04 the first
measurement — a throwaway script, `~/gestate-lean.md` — found two
populations: a card finishes the day it is written (13 of 22, median
half a day) or it stands (six of eight open cards past seventeen
days).  The queue pulls nobody; the conversation pulls both.  Git knew
all of it and nobody read it.

**The lamp is Henri's rule, in his words the same evening:** *"se voisi
olla kortit joihin ei ole koskettu 7 päivään, niiden pitäisi mennä
later/ hyllyyn meidän kauttamme"* — a card nobody has touched for seven
days goes to `later/`, **through us**: a session moves it and the
reason goes in the card in his words (`board/README.md` §"And the
reason it was displaced goes in the card").  So `--check` names the cards and
exits 2, and `tools/pre-commit.sh` prints that as a lamp that never
refuses — the move is a decision with a person in it, not a rule a
script may apply.

**Touched means the card's own file changed in a commit.**  An edit to
the board README's order is not a touch — that is the order moving,
not the work — and an untracked card is touched now, since it is
being written.  Born is the first commit that added the card on any
shelf; done and shelved are the first commit that added it under
`done/` or `later/`.  One `git log --name-status` walk over `board/`
gives all of it, which is what keeps this cheap enough to print at
every commit.
"""
from __future__ import annotations

import argparse
import os
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STALE_DAYS = 7
DAY = 86400
SHELVES = ("board", "board/done", "board/later", "board/refused")


def _log(root: Path) -> list[tuple[int, list[tuple[str, str, str]]]]:
    """[(epoch, [(status, path, new_path_or_empty)…])…], oldest first."""
    out = subprocess.run(
        ["git", "-C", str(root), "log", "--reverse", "--format=%x00%ct",
         "--name-status", "--diff-filter=AMDR", "--", "board"],
        capture_output=True, text=True, check=True).stdout
    commits = []
    for chunk in out.split("\x00")[1:]:
        lines = chunk.strip("\n").split("\n")
        when = int(lines[0].strip())
        changes = []
        for ln in lines[1:]:
            if not ln.strip():
                continue
            parts = ln.split("\t")
            status = parts[0][0]
            if status == "R" and len(parts) == 3:
                changes.append(("R", parts[1], parts[2]))
            elif len(parts) >= 2:
                changes.append((status, parts[1], ""))
        commits.append((when, changes))
    return commits


def _shelf_of(path: str) -> str | None:
    parent, _, name = path.rpartition("/")
    if parent in SHELVES and name.endswith(".md") and name != "README.md":
        return parent
    return None


def cards(root: Path = ROOT, now: float | None = None) -> list[dict]:
    """One dict per card on any shelf: name, shelf, born, touched, done,
    shelved — epochs, or None."""
    now = time.time() if now is None else now
    born: dict[str, int] = {}
    touched: dict[str, int] = {}          # by current path
    first_on: dict[tuple[str, str], int] = {}  # (shelf, name) -> first arrival
    for when, changes in _log(root):
        for status, path, new in changes:
            arrivals = []
            if status in ("A", "M"):
                arrivals.append(path)
            elif status == "R":
                arrivals.append(new)
            for p in arrivals:
                shelf = _shelf_of(p)
                if not shelf:
                    continue
                name = p.rpartition("/")[2]
                born.setdefault(name, when)
                first_on.setdefault((shelf, name), when)
                touched[p] = when
    out = []
    for shelf in SHELVES:
        d = root / shelf
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if p.name == "README.md":
                continue
            path = f"{shelf}/{p.name}"
            out.append({
                "name": p.name, "shelf": shelf,
                "born": born.get(p.name, int(now)),
                "touched": touched.get(path, int(now)),
                "done": first_on.get(("board/done", p.name)) if shelf == "board/done" else None,
                "shelved": first_on.get(("board/later", p.name)) if shelf == "board/later" else None,
            })
    return out


def stale(rows: list[dict], days: int = STALE_DAYS, now: float | None = None) -> list[dict]:
    """Live cards nobody has touched for `days`, oldest touch first."""
    now = time.time() if now is None else now
    old = [r for r in rows if r["shelf"] == "board" and now - r["touched"] >= days * DAY]
    return sorted(old, key=lambda r: r["touched"])


def week(t: int) -> str:
    return time.strftime("%Y-W%W", time.gmtime(t))


def report(rows: list[dict], days: int = STALE_DAYS, now: float | None = None) -> str:
    now = time.time() if now is None else now
    live = [r for r in rows if r["shelf"] == "board"]
    done = [r for r in rows if r["done"]]
    later = [r for r in rows if r["shelf"] == "board/later"]
    refused = [r for r in rows if r["shelf"] == "board/refused"]
    lines = [f"{len(rows)} cards: {len(live)} open, {len(done)} done, "
             f"{len(later)} shelved, {len(refused)} refused"]
    if done:
        lead = [(r["done"] - r["born"]) / DAY for r in done]
        lines.append(f"lead time, done cards, days: median {statistics.median(lead):.1f}, "
                     f"mean {statistics.mean(lead):.1f}, max {max(lead):.1f}, "
                     f"same-day {sum(1 for l in lead if l < 1)} of {len(lead)}")
    if live:
        lines.append("open cards — age, and days since anybody touched the card:")
        for r in sorted(live, key=lambda r: r["touched"]):
            age, quiet = (now - r["born"]) / DAY, (now - r["touched"]) / DAY
            mark = "  ← stale" if quiet >= days else ""
            lines.append(f"  {age:5.1f}  {quiet:5.1f}  {r['name']}{mark}")
    arr = Counter(week(r["born"]) for r in rows)
    fin = Counter(week(r["done"]) for r in done)
    shv = Counter(week(r["shelved"]) for r in rows if r["shelved"])
    lines.append("week      arrived  done  shelved")
    for w in sorted(set(arr) | set(fin) | set(shv)):
        lines.append(f"{w}   {arr[w]:5d}  {fin[w]:4d}  {shv[w]:5d}")
    return "\n".join(lines)


def lamp(rows: list[dict], days: int = STALE_DAYS, now: float | None = None) -> tuple[bool, str]:
    """(tripped, the line).  Trips on any live card untouched for `days`."""
    now = time.time() if now is None else now
    old = stale(rows, days, now)
    if not old:
        return False, f"flow: every open card was touched within {days} days"
    names = ", ".join(f"{r['name']} ({(now - r['touched']) / DAY:.0f}d)" for r in old)
    return True, (f"flow: {len(old)} open card{'s' if len(old) != 1 else ''} untouched for "
                  f"{days} days — {names}; Henri's rule 2026-09-04: to later/, through a "
                  f"session and him, his words in the card")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the board's flow, and the seven-day lamp")
    ap.add_argument("--check", action="store_true", help="the lamp: exit 2 when a card is stale")
    ap.add_argument("--days", type=int, default=STALE_DAYS)
    ap.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    try:
        rows = cards(a.root)
    except subprocess.CalledProcessError as e:
        print(f"flow: git refused — {e.stderr.strip() if e.stderr else e}", file=sys.stderr)
        return 1
    if a.check:
        tripped, line = lamp(rows, a.days)
        print(line)
        return 2 if tripped else 0
    print(report(rows, a.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
