"""The command list knows which run of the file each verb is in.

`card:command-categories.md`.  The categories were never missing —
`command.ges` has been written in labelled sections since it existed,
and nothing read them, so the palette showed fifty-three names flat.
This holds the *derivation*; what the window does with it is still open
on the card, deliberately.

Same rule as the order (`session.vocabulary`): the file is the command
list, so anything the list wants comes out of the file rather than
being kept beside it.  A category maintained anywhere else is a second
place to forget.
"""

from __future__ import annotations

from gestate.session import vocabulary


def test_every_command_is_in_a_section():
    """A verb under no header would be a category nobody chose, which
    is how a list quietly grows an *Other*."""
    homeless = [v.name for v in vocabulary() if not v.section]
    assert homeless == [], (
        "these commands are declared before any `# ── … ──` header in "
        "command.ges: " + ", ".join(homeless))


def test_the_sections_are_the_file_s_own_headings():
    """Nobody writes a category — they write the heading they were
    already writing.  So the names here should be readable English out
    of `command.ges`, and this is the list as it stands."""
    seen = []
    for v in vocabulary():
        if v.section not in seen:
            seen.append(v.section)
    assert seen == [
        "The instrument", "The loop", "Parameters", "Notes",
        "Performing", "Chance", "The text", "Laying it out",
        "Leaving the workshop", "The history", "The window", "The algebra",
    ], seen


def test_a_section_is_a_heading_and_not_a_sentence():
    """**A header is a label the moment something reads it.**  One of
    these was written as prose the same day — *"The algebra's identity,
    last on purpose"* — which is a fine comment and a poor category, and
    it was only visible once the derivation existed.  The reason belongs
    in the doc comment underneath, where it already was."""
    for v in vocabulary():
        assert "," not in v.section, (
            f"`{v.section}` reads as a sentence; a heading in "
            "command.ges is now a category name")
        assert len(v.section) <= 24, f"`{v.section}` is long for a label"


def test_the_sections_follow_the_file_and_so_does_the_order():
    """The two derivations agree because they are the same walk: a
    command's section is the last header above it, so the sections come
    out in file order and each is a contiguous run."""
    runs = []
    for v in vocabulary():
        if not runs or runs[-1] != v.section:
            runs.append(v.section)
    assert len(runs) == len(set(runs)), (
        "a section appears twice, so the commands in it are not "
        "together in the file: " + ", ".join(runs))


def test_the_first_command_is_still_the_first_thing_in_its_section():
    """Guarding the F150 fix from the other side: whatever grouping the
    palette grows, `apply` is what a stranger meets first."""
    first = vocabulary()[0]
    assert (first.name, first.section) == ("apply", "The instrument")


# ── And what crosses to the window ──────────────────────────────────────────
#
# `card:command-categories.md` option A landed on 2026-08-18.  The
# section rides on each command row rather than as heading rows of its
# own, so nothing has to agree about where a heading *goes* — the window
# draws one wherever the section changes, and one that does not know the
# field shows the flat list it always showed.


def _rows(session):
    from gestate.session import furniture

    return [line.split("\t") for line in furniture(session).splitlines()
            if line.startswith("command\t")]


def _a_session():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_session import session

    return session()


def test_every_command_row_carries_its_section():
    rows = _rows(_a_session())
    assert rows, "no commands crossed at all"
    for row in rows:
        assert len(row) >= 8, f"the section is missing from {row[1]!r}"
    named = {row[1]: row[7] for row in rows}
    assert named["apply"] == "The instrument"
    assert named["loop"] == "The loop"


def test_the_sections_cross_as_contiguous_runs():
    """What makes one heading per group possible at the far end: the
    window draws a heading when the field changes, so a section that
    came back twice would be drawn twice."""
    seen = [row[7] for row in _rows(_a_session())]
    runs = []
    for s in seen:
        if not runs or runs[-1] != s:
            runs.append(s)
    assert len(runs) == len(set(runs)), runs


def test_a_query_sends_no_sections_at_all():
    """**The decision about when grouping helps.**  Filtering re-ranks,
    so the runs break into ones and twos and eleven headings become
    noise over a list somebody has already narrowed.  A person who has
    typed something is looking for a match, not for a taxonomy."""
    it = _a_session()
    it.filtered = it.matching("loop")
    rows = _rows(it)
    assert rows, "the query matched nothing, so this tests nothing"
    assert all(row[7] == "" for row in rows), rows
