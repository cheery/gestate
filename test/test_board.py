"""The board's own shape, checked — `board/README.md` is the contract.

**The rules are executable and they live here, not in the editor.**
Henri, 2026-08-16: *"Since we're making a workbench, lets make it also a
tool that enforces our rules."*  Yes — and the enforcing belongs in the
suite, with the window as a reader of the verdict rather than its home.
The project has made that call twice already for the same reason: the
window never tokenizes, because *"a second lexer in the window would be
a second front end that could disagree with the compiler"*, and the
window never invents furniture.  A rule that lives in an editor holds
only for people using that editor — not for a collaborator with a
different one, and not for a session that writes files with tools and
never opens the workbench.

What the window would add is **timing**, not authority: saying it beside
the card while you type, the way a knob is drawn beside its own
declaration.  That wants card-editing in the workbench to be a thing
somebody does, and today `.md` opens inert.  It is a card for when that
has a caller.

The first of these is Henri's ask: *"One problem I see in the board is
that we need to check name collisions."*  A card's **filename is its
id** — cited from comments and tests the way `fixme.md`'s F-numbers are
— so two cards wearing one name is the id property quietly failing, and
the likeliest way in is a new card reusing a name that has already moved
to `done/`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "board"

#: The header block every card opens with — `board/README.md` §"What a
#: card is".  Read as `name  value`, the value running on over indented
#: continuation lines.
FIELD = re.compile(r"^ {4}(\w+)\s{2,}(.*)$")

#: What `status` may say.  `done` carries its date; the rest stand alone.
STATES = ("open", "doing", "blocked", "done")


def cards() -> list[Path]:
    return sorted(BOARD.glob("*.md")) + sorted((BOARD / "done").glob("*.md"))


def header(path: Path) -> dict:
    """The header block, as a dict.  Stops at the first blank line after
    it, because the body below is prose and not fields."""
    out: dict[str, str] = {}
    seen = False
    for line in path.read_text(encoding="utf-8").splitlines():
        found = FIELD.match(line)
        if found:
            seen = True
            out[found.group(1)] = found.group(2).strip()
        elif seen and not line.strip():
            break
    return out


def test_no_two_cards_wear_the_same_name():
    """Henri's ask, and the id property depends on it.

    Across the whole board including `done/`: a finished card keeps its
    name forever, so reusing it would make one citation mean two things
    — and the citation that breaks is the *old* one, in a comment
    nobody is looking at.
    """
    seen: dict[str, Path] = {}
    clashes = []
    for card in cards():
        first = seen.get(card.stem)
        if first is not None:
            clashes.append(f"{card.stem}: "
                           f"{first.relative_to(ROOT)} and "
                           f"{card.relative_to(ROOT)}")
        seen[card.stem] = card
    assert not clashes, (
        "two cards wear one name, so a citation to it is ambiguous:\n  "
        + "\n  ".join(clashes)
        + "\nA card's filename is its id (board/README.md).  Rename the "
          "new one; the finished card keeps the name it was cited by.")


@pytest.mark.parametrize("card", cards(), ids=lambda p: p.stem)
def test_every_card_says_why_it_exists(card: Path):
    """`because`, `status` and `asked`, on every card.

    **`because` is the one that matters** and the board's most expensive
    lesson: the card that read *"name datatypes eg. `type Duration =
    Float`"* named a **fix**, and the need behind it — *"I do not figure
    out quickly enough which argument in lowpass filters are which"* —
    turned out to have nothing to do with types.  A card that names the
    fix hides the problem, and the problem is the part a reader can
    solve differently.

    Checked for presence, not for wisdom: no test can tell a problem
    from a solution.  What it can do is refuse a card that answers
    neither.
    """
    fields = header(card)
    for want in ("status", "because", "asked"):
        assert fields.get(want), (
            f"{card.relative_to(ROOT)} has no `{want}` line.  "
            "board/README.md §\"What a card is\" has the block every "
            "card opens with.")
    assert fields["status"].split()[0].rstrip(":") in STATES, (
        f"{card.relative_to(ROOT)} says `status {fields['status']}`; "
        f"it must begin with one of {', '.join(STATES)}.")


@pytest.mark.parametrize("card", cards(), ids=lambda p: p.stem)
def test_a_finished_card_is_in_done_and_an_open_one_is_not(card: Path):
    """`ls board/*.md` **is** the live board, which is only true if the
    two halves agree about which is which."""
    finished = header(card)["status"].startswith("done")
    in_done = card.parent.name == "done"
    assert finished == in_done, (
        f"{card.relative_to(ROOT)} says `status "
        f"{header(card)['status']}` but sits in "
        f"{card.parent.relative_to(ROOT)}/.  A card leaves the board in "
        "the same commit as the work it describes.")


@pytest.mark.parametrize("card", cards(), ids=lambda p: p.stem)
def test_a_blocked_card_names_what_it_waits_on(card: Path):
    """A blocked card with no `blocked` line is how an item sits there
    for a week after the thing it waited for arrived.

    It happened, and that is why this is a test: the `open ../../hello`
    card was marked *"the one item I cannot start without an answer"*,
    the answer was given sixty lines further down the same file, and the
    session read the flag and skipped the card.
    """
    fields = header(card)
    if not fields["status"].startswith("blocked"):
        return
    waits = fields.get("blocked", "")
    assert waits, (
        f"{card.relative_to(ROOT)} is blocked and does not say on what.")
    for cited in re.findall(r"board/(?:done/)?[\w-]+\.md", waits):
        assert (ROOT / cited).exists(), (
            f"{card.relative_to(ROOT)} waits on {cited}, which is not "
            "there.")


def test_the_board_lists_every_open_card_in_order():
    """`board/README.md` carries the order, and it is the only place the
    order lives — so a card nobody listed is a card nobody will work.

    Which is the case a new card falls into by default: Henri creates
    cards and edits nothing, so a card arrives **unplaced** and the
    session is what puts it in the order.  This is the reminder.
    """
    listed = set(re.findall(r"\[[^\]]+\]\((\w[\w-]*\.md)\)",
                            (BOARD / "README.md").read_text()))
    on_disk = {p.name for p in BOARD.glob("*.md")} - {"README.md"}
    assert on_disk - listed == set(), (
        "these cards are on the board and not in the order — a new card "
        "arrives unplaced, and this is where it gets placed:\n  "
        + "\n  ".join(sorted(on_disk - listed)))
    assert listed - on_disk == set(), (
        "the order names cards that are not there (moved to done/?):\n  "
        + "\n  ".join(sorted(listed - on_disk)))
