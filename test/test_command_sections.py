"""The command list knows which run of the file each verb is in.

`board/command-categories.md`.  The categories were never missing —
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
        "Leaving the workshop", "The window", "The algebra",
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
