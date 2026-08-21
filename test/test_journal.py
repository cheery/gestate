"""The journal's archive against what is on disk — `spec/rules.md`
§"The journal rotates" is the contract.

**The index is the only reason the archive is worth having.**  A closed
month is a file nobody opens unless something tells them it is the one
they want, so the index in `journal.md`'s head is load-bearing: one line
per month, naming its themes, so a session looking for June's audio work
opens `journal/2026-06.md` and nothing else.  An index that has fallen
behind the directory sends that session to the wrong file or to all of
them, which is the cost the rotation was paid to remove.

So this is the ordinary gate defect class — **a generated page behind
its source**, the same as the atlas behind its modules and `doc/ref/`
behind the libraries.  `tools/journalroll.py --index` is the fix for
every failure here.

**What is deliberately not here is the budget.**  Being over it is an
andon and `tools/suite.py` lights it; nothing in this file fails a
commit because the journal is long, because the journal being long is
the project working.  What is refused is the archive and its index
disagreeing, which is not growth but the index having rotted.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import journalroll  # noqa: E402


def test_the_journal_is_where_the_index_says_it_is():
    """`journal.md` exists and carries the generated block.

    Losing the block is not a way under the budget: it is the archive
    becoming unfindable while every closed month is still on disk.
    """
    assert journalroll.JOURNAL.exists(), "journal.md is not there"
    text = journalroll.JOURNAL.read_text(encoding="utf-8")
    head = "\n".join(journalroll._split(text)[0])
    assert journalroll.INDEX_HEADING in head, (
        "journal.md's head has no archive index.  The block is generated — "
        "`python tools/journalroll.py --index` puts it back.")
    assert journalroll.STAMP.search(head), (
        "journal.md does not say which month it is holding, so nothing can "
        "tell whether the rotation is due — tools/journalroll.py --index.")


def test_every_closed_month_has_its_line_and_every_line_its_month():
    """The two directions, because they rot differently.

    A file with no row is a month that was archived and never indexed —
    invisible, and the reason it was moved was to be findable.  A row
    with no file is a citation trail to nothing.
    """
    on_disk = dict(journalroll.archived())
    rows = {m: (n, t) for m, n, t in journalroll.index_rows()}

    unindexed = sorted(set(on_disk) - set(rows))
    assert not unindexed, (
        "these months are in journal/ and not in the index, so nothing "
        f"points at them: {', '.join(unindexed)} — "
        "tools/journalroll.py --index")

    phantom = sorted(set(rows) - set(on_disk))
    assert not phantom, (
        "the index names months that are not in journal/: "
        f"{', '.join(phantom)} — tools/journalroll.py --index")

    behind = [f"{m}: the index says {rows[m][0]:,}, the file has {n:,}"
              for m, n in on_disk.items() if rows[m][0] != n]
    assert not behind, (
        "the index's sizes are behind the files they describe, and the "
        "size is what a session weighs before opening one:\n  "
        + "\n  ".join(behind) + "\n  tools/journalroll.py --index")


def test_a_closed_month_was_actually_skimmed():
    """The placeholder may not outlive the month.

    **This is the whole ritual, held by the one thing that can hold
    it.**  The rotation is a fire evening — skim the closing month once,
    promote what earns its place, write the index line — and the skim is
    the part with no mechanism behind it.  What a test *can* see is the
    line the skim was supposed to produce, so a month that closed
    wearing `OPEN_CELL` is the evening having been half done.
    """
    now = _dt.date.today().strftime("%Y-%m")
    unskimmed = [m for m, _n, themes in journalroll.index_rows()
                 if m < now and themes.strip() == journalroll.OPEN_CELL]
    assert not unskimmed, (
        f"{', '.join(unskimmed)} closed and still has no index line.  A cut "
        "made mid-month leaves the cell open on purpose; a month that has "
        "ended is owed the skim that names its themes — spec/rules.md "
        "§\"The journal rotates\".")


def test_an_archived_month_is_named_for_a_month():
    """`journal/` holds months and nothing else.

    A stray `notes.md` in there is a file outside every rule this
    directory has: not indexed, not append-only, not cited.
    """
    if not journalroll.ARCHIVE.is_dir():
        return
    stray = sorted(p.name for p in journalroll.ARCHIVE.iterdir()
                   if p.name != "README.md"
                   and not re.fullmatch(r"\d{4}-\d{2}\.md", p.name))
    assert not stray, (
        f"journal/ holds {', '.join(stray)}, which is not a closed month.  "
        "The directory is the archive and its names are its index keys.")


def test_the_lamp_works():
    """A signal that cannot fire is indistinguishable from a tree that
    is fine — `manifesto.md`, and the same test `test_rules.py` runs on
    the cap's lamp.

    Both triggers, because they are separate code and either one going
    quiet leaves the rotation resting on somebody remembering.
    """
    import suite

    assert bool(suite._journal_andon()) == bool(journalroll.due()), (
        "the journal lamp disagrees with tools/journalroll.py about "
        "whether the rotation is due — tools/suite.py §_journal_andon.")

    text = journalroll.JOURNAL.read_text(encoding="utf-8")
    head, body = journalroll._split(text)

    real = journalroll.BUDGET
    try:
        journalroll.BUDGET = 0
        assert any("over the budget" in r for r in journalroll.due(text)), (
            "the budget trigger does not fire even at a budget of nothing")
        assert suite._journal_andon(), "the lamp stays dark over the budget"
    finally:
        journalroll.BUDGET = real

    stale = journalroll.STAMP.sub("*The open month is 1970-01.*",
                                  "\n".join(head), count=1)
    assert any("the month turned" in r
               for r in journalroll.due("\n".join([stale, *body]))), (
        "the calendar trigger does not fire on a journal half a century "
        "stale.  The rotation would then rest on somebody remembering, "
        "which is the thing spec/rules.md says forgetting is not fixed by.")
