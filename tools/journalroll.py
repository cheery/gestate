"""The journal against its budget, and the rotation that meets it —
`spec/rules.md` §"The journal rotates" is the contract.

**Why the journal has a budget at all, when `spec/` does not.**  It is
not read whole; it is *grepped*, and that is exactly the cost.  At
530 KB every session that searches it pays attention-tax on ten
thousand lines of closed months to find the one paragraph it wanted,
and a smaller model reading the same file pays it in the only window it
has.  Henri, 2026-08-21, on the timing: *"not because the journal is
sick but because at 530K every session that greps it is paying
attention-tax for no return."*

**The shape is an archive, not an edit.**  A closed month moves to
`journal/YYYY-MM.md` whole and is never rewritten — cuts are appended
at the bottom and nothing above them is touched.  Henri, 2026-08-21:
*"nothing is rewritten, because git already remembers and a journal
that gets retroactively edited becomes a second source of truth about
the past.  Archive, don't airbrush."*  That is also how the grudge
class is handled: the fact stays in the archive and the heat does not
get an index line.

**The index is what makes the archive worth having.**  One line per
closed month, naming its themes, so a session looking for June's audio
work opens exactly that file instead of inhaling everything.  This
script owns the block; a hand-kept index rots and `test/test_journal.py`
is what says so.

    python tools/journalroll.py                  where the lines are, and whether it is due
    python tools/journalroll.py --roll           cut the open month into the archive
    python tools/journalroll.py --roll --themes "…"   …and close it with its index line

**Over the budget is an andon, not a refusal**, the same as the rules
cap it sits beside, and the lamp's meaning is *rotation is due* rather
than *stop writing*.  Nothing here ever fails a commit for the journal
being long: the journal being long is the project working.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "journal.md"
ARCHIVE = ROOT / "journal"

#: **8,000 for now** — Claude, 2026-08-21, derived and Henri's to move,
#: in writing, with the date, the same as `rulecount.CAP`.
#:
#: The anchor is the *skim*, because that is the act the budget has to
#: pay for: the rotation is a fire evening — one pass over the closing
#: month, two or three lines promoted into the method files, one index
#: line written.  A month you cannot skim in a sitting does not get
#: rotated, it gets postponed.
#:
#: **At the measured pace this lights before the month ends, and that
#: is not a miscalibration.**  `journal.md` reached 10,450 lines in the
#: thirteen days from 2026-08-08, about 800 a day; a calendar month at
#: that pace is 25,000, which is three or four sittings, not one.  The
#: lamp saying *due* on the tenth is the mechanism reporting that this
#: month wants more than one cut — which the archive allows, because it
#: is append-only and a month may be closed in several.
BUDGET = 8000

#: The generated block in `journal.md`'s head.  Everything from this
#: heading to the end of the head belongs to this script; the prose
#: above it belongs to whoever is writing the journal.
INDEX_HEADING = "## The archive — the closed months, one line each"

#: What an open month's cell says before the skim has been done.  It is
#: allowed only while the month is still the current one — a past month
#: wearing this is the index having rotted, and the gate refuses it.
OPEN_CELL = "*open — not closed yet, so not yet skimmed*"

MONTH = re.compile(r"^(\d{4})-(\d{2})$")
STAMP = re.compile(r"^\*The open month is (\d{4}-\d{2})\.\*", re.M)
ROW = re.compile(r"^\|\s*\[(\d{4}-\d{2})\]\([^)]*\)\s*\|\s*([\d,]+)\s*\|\s*(.*?)\s*\|$")


def _today() -> str:
    return _dt.date.today().strftime("%Y-%m")


def _split(text: str) -> tuple[list[str], list[str]]:
    """The head, and the month's entries.

    The head is everything down to the first `---` on a line of its
    own, which is the separator `journal.md` has had since it was one
    file.  Using the file's own furniture rather than a planted marker
    means the head stays something a person edits by hand.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return lines[:i], lines[i:]
    return lines, []


def _prose(head: list[str]) -> list[str]:
    """The head with the generated block taken off the end."""
    for i, line in enumerate(head):
        if line.strip() == INDEX_HEADING:
            while i and not head[i - 1].strip():
                i -= 1
            return head[:i]
    return head


def archived() -> list[tuple[str, int]]:
    """Every closed month on disk, oldest first, with its size."""
    if not ARCHIVE.is_dir():
        return []
    out = []
    for path in sorted(ARCHIVE.glob("*.md")):
        if MONTH.match(path.stem):
            n = len(path.read_text(encoding="utf-8").splitlines())
            out.append((path.stem, n))
    return out


def index_rows(text: str | None = None) -> list[tuple[str, int, str]]:
    """The index as it is written, which is the claim being checked."""
    if text is None:
        text = JOURNAL.read_text(encoding="utf-8")
    rows = []
    for line in _split(text)[0]:
        m = ROW.match(line.strip())
        if m:
            rows.append((m.group(1), int(m.group(2).replace(",", "")), m.group(3)))
    return rows


def open_month(text: str | None = None) -> str:
    """Which month `journal.md` is holding.

    The stamp is authoritative because the script writes it.  The
    fallback reads the entries, and exists for exactly one rotation —
    the first, on a file that predates the stamp.
    """
    if text is None:
        text = JOURNAL.read_text(encoding="utf-8")
    m = STAMP.search("\n".join(_split(text)[0]))
    if m:
        return m.group(1)
    dates = re.findall(r"^##+ .*?(\d{4}-\d{2})-\d{2}", "\n".join(_split(text)[1]), re.M)
    return max(dates) if dates else _today()


def lines_now(text: str | None = None) -> int:
    if text is None:
        text = JOURNAL.read_text(encoding="utf-8")
    return len(text.splitlines())


def due(text: str | None = None) -> list[str]:
    """Why the rotation is due, in the words the lamp will use.

    Two triggers and one act.  The calendar is the rule; the budget is
    the tripwire for a month that is running hot enough that leaving it
    to the calendar makes the skim unaffordable.
    """
    if text is None:
        text = JOURNAL.read_text(encoding="utf-8")
    reasons = []
    open_, now = open_month(text), _today()
    if open_ < now:
        reasons.append(f"the month turned — `journal.md` still holds {open_}, "
                       f"and it is {now}")
    n = lines_now(text)
    if n > BUDGET:
        reasons.append(f"over the budget — {n:,} lines against {BUDGET:,}, "
                       f"by {n - BUDGET:,}")
    return reasons


def _render_index(rows: list[tuple[str, int, str]], open_: str) -> list[str]:
    body = [
        INDEX_HEADING,
        "",
        "`journal/` holds the closed months.  A closed month is **append-only**:",
        "a cut is added at the bottom and nothing above it is ever edited, because",
        "git already remembers and a journal that is retroactively edited becomes a",
        "second source of truth about the past.  Archive, don't airbrush.",
        "",
        "**A citation says `journal.md` whatever month it landed in.**  The file is",
        "the journal's name and the archive is where its closed months live — the",
        "same separation as a card's id and its shelf, and for the same reason: a",
        "citation must not rot because time passed.  `test/test_citations.py`",
        "resolves a `journal.md §\"…\"` against the archive too.",
        "",
    ]
    if rows:
        body += ["| month | lines | what it was about |", "|---|---|---|"]
        for month, n, themes in rows:
            body.append(f"| [{month}](journal/{month}.md) | {n:,} | {themes} |")
    else:
        body.append("*No month has closed yet.*")
    body += [
        "",
        f"*The open month is {open_}.*  `python tools/journalroll.py` says where the",
        "lines are and whether the rotation is due; `spec/rules.md` §\"The journal",
        "rotates\" is the contract, and the rotation is an act of the fire, not of a",
        "gate.",
    ]
    return body


def write_index(themes: dict[str, str] | None = None) -> str:
    """Redraw the block from what is actually on disk, keeping the
    themes already written.  This is the repair, and the gate's fix."""
    text = JOURNAL.read_text(encoding="utf-8")
    head, body = _split(text)
    kept = {m: t for m, _n, t in index_rows(text)}
    kept.update(themes or {})
    rows = [(m, n, kept.get(m, OPEN_CELL)) for m, n in archived()]
    # **The `---` is not decoration, it is the seam.**  `_split` finds
    # the month's entries by it, so a journal that has just been rolled
    # empty still has to carry one: without it the next entry written
    # lands inside the head, and the following rotation reports a month
    # with nothing to cut while holding a month's work.
    if not body:
        body = ["---", ""]
    out = "\n".join(_prose(head) + [""] + _render_index(rows, open_month(text))
                    + [""] + body)
    if not out.endswith("\n"):
        out += "\n"
    JOURNAL.write_text(out, encoding="utf-8")
    return out


def roll(themes: str | None = None) -> tuple[Path, int]:
    """Cut the open month out of `journal.md` and into the archive.

    One code path for both triggers: the whole of the month's entries
    go to `journal/<open>.md`, appended if a cut is already there, and
    `journal.md` restarts carrying its head.
    """
    text = JOURNAL.read_text(encoding="utf-8")
    head, body = _split(text)
    open_ = open_month(text)
    closing = open_ < _today()

    entries = "\n".join(body).strip("\n")
    if not entries or entries == "---":
        raise SystemExit("journalroll: the open month has no entries to cut.")
    if closing and not themes:
        raise SystemExit(
            f"journalroll: {open_} is a closed month and has no index line.\n"
            f"  The rotation is the fire's, not the script's: skim the month\n"
            f"  once, promote what earns its place into the method files, then\n"
            f"  name the themes here —\n"
            f"      python tools/journalroll.py --roll --themes \"…\"\n"
            f"  spec/rules.md §\"The journal rotates\".")

    ARCHIVE.mkdir(exist_ok=True)
    target = ARCHIVE / f"{open_}.md"
    today = _dt.date.today().isoformat()
    if target.exists():
        prior = target.read_text(encoding="utf-8").rstrip("\n")
        out = f"{prior}\n\n---\n\n*Cut from `journal.md` on {today}.*\n\n{entries}\n"
    else:
        out = "\n".join([
            f"# journal/{open_}.md — the month of {open_}",
            "",
            "*A month of `journal.md`, moved here whole.  **Append-only**: later",
            "cuts are added at the bottom and nothing above them is edited.  What",
            "is wrong in it stays wrong and is corrected in the open journal, not",
            "here — git already remembers, and a past that is rewritten is a second",
            "source of truth about the past.*",
            "",
            f"*Cut from `journal.md` on {today}.*",
            "",
            entries,
            "",
        ])
    target.write_text(out, encoding="utf-8")

    JOURNAL.write_text("\n".join(_prose(head)) + "\n", encoding="utf-8")
    write_index({open_: themes} if themes else None)
    # The stamp follows the calendar: an early cut leaves the month open.
    if closing:
        text = JOURNAL.read_text(encoding="utf-8")
        JOURNAL.write_text(
            STAMP.sub(f"*The open month is {_today()}.*", text, count=1),
            encoding="utf-8")
    return target, len(entries.splitlines())


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--roll", action="store_true")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--themes")
    ap.add_argument("-h", "--help", action="store_true")
    args = ap.parse_args()
    if args.help:
        print(__doc__)
        return 0

    if args.roll:
        target, n = roll(args.themes)
        print(f"journalroll: {n:,} lines cut to "
              f"{target.relative_to(ROOT)}, and journal.md restarts.")
        print("             the index is redrawn; check it reads true.")
        return 0

    if args.index:
        write_index()
        print("journalroll: the index is redrawn from journal/.")
        return 0

    n, open_ = lines_now(), open_month()
    print(f"  journal.md          {n:>6}   budget {BUDGET}   open month {open_}")
    for month, size in archived():
        print(f"  journal/{month}.md  {size:>6}   closed")
    reasons = due()
    if not reasons:
        print(f"\njournalroll: under, with {BUDGET - n} lines of room, and the "
              f"month is current.")
        return 0
    print("\njournalroll: **the rotation is due** —")
    for r in reasons:
        print(f"  * {r}")
    print("\n  It means rotate, not stop writing.  The act is the fire's: skim\n"
          "  the closing month once, promote what earns its place into the\n"
          "  method files, write the index line, close the file.\n"
          "      python tools/journalroll.py --roll --themes \"…\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
