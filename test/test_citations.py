"""Every `§"…"` citation points at a heading that exists.

**Written after three of them had already rotted.**  `roadmap.md` §"Small
improvements queued from use", §"Dropping a scope in one move" and §"The
canvas walks over crust" were cited from five files on 2026-08-16 and
none of the three sections was still in the roadmap: each had been
consumed when the work landed and moved to `journal.md` under a
different heading.  Nothing noticed, because a citation is prose and
prose is not run.

The roadmap says it itself, about keeping the stage numbers: *"A
citation that no longer resolves is worse than a long file."*  This is
that sentence with a test under it — and it matters more since the board
became `board/*.md`, because a card's **filename is its id** and cards
are cited the way `fixme.md`'s F-numbers are.

Deliberately forgiving about the text and strict about existence: a
citation may quote the first few words of a long heading, and headings
wrap across lines in source comments.  What is checked is that
*something* with that beginning is there to be read.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Comment markers, so a citation wrapped across lines in a `#:` block
#: or a `///` doc comment flattens to the same words as the heading.
#:
#: **`*` is deliberately not one of them.**  It would read a C block
#: comment's continuation line, and it would also eat the first star of
#: a markdown `**bold lead-in**` at the start of a line — which is
#: exactly what this has to find.  Nothing in this tree wraps a citation
#: in a block comment; several hundred passages are named in bold.
MARKER = re.compile(r"^\s*(?:#:|#|///|//|>)\s?")

#: Where to look for citations.  The tree's own text, not its inputs:
#: `target/`, `.venv/` and the caches hold copies of things.
SEARCHED = ("*.py", "*.rs", "*.md", "*.ges")
SKIP = {"target", ".venv", "__pycache__", ".git", "node_modules"}

#: ``· `roadmap.md` §"The rule"`` — the file, then the section.  The
#: backticks are optional because the older comments do not use them, and
#: the section text may run over a line break in a wrapped comment.
#:
#: **The path is part of the name.**  Matching a bare `[\w.]+\.md` read
#: `board/README.md` as `README.md`, resolved it against the repository's
#: own README, and reported a section that was perfectly present as
#: missing — a checker sending somebody to look at the wrong file is
#: worse than no checker.
CITE = re.compile(r"`?([\w./-]+\.md)`?\s*§\"([^\"]+)\"")

#: `card:peep-window.md` — a card cited **by its id**, which is its
#: filename and nothing else.
#:
#: **Adopted 2026-08-18, and it replaced a path.**  Henri: *"we would
#: come with some notation to refer to a card?  We already have F0,
#: F100 … card:button.md is good notation."*  A card's name never
#: changes and its *shelf* does — `board/`, `board/done/`,
#: `board/later/` — so a citation spelled as a path broke every time a
#: card was finished or shelved.  Sixteen cards had moved in ten days,
#: and each move was a tree-wide rewrite.
#:
#: **Backticks are optional here, unlike the path form**, and that is
#: the second half of the fix: the old regex only saw citations inside
#: backticks, so the `see` lines at the head of every card — which are
#: written bare — were never checked at all.  Two of them had already
#: rotted in that blind spot — `card:gemba.md` and `card:button.md`,
#: both finished and moved to `done/` long before anybody noticed, both
#: still cited at their old shelf.  F166.
CARD = re.compile(r"`?card:([\w-]+\.md)`?")

#: Where a card may sit.  The shelf is not part of the id, which is the
#: whole point: finishing a card must not break a citation to it.
SHELVES = ("board", "board/done", "board/later")


def _files():
    """Every text file in the tree, except this one.

    **The checker cannot be its own subject**: the docstring above names
    three citations *because they were dead*, which is the whole point
    of the file and would fail its own test forever.  Naming the
    exception here rather than quietly special-casing it keeps the
    exemption to exactly one file.
    """
    here = Path(__file__).resolve()
    for pattern in SEARCHED:
        for path in ROOT.rglob(pattern):
            if any(part in SKIP for part in path.parts):
                continue
            if path.resolve() == here:
                continue
            yield path


def _flat(text: str) -> str:
    """One line, one space between words, comment markers gone — what a
    wrapped citation and the heading it names have in common."""
    return " ".join(" ".join(MARKER.sub("", ln)
                             for ln in text.splitlines()).split())


def _named(path: Path) -> str:
    """The file flattened and lowercased, for asking whether a name is
    still in it.

    **A `§` in this project does not mean a `#` heading**, and pinning it
    to one would fail on most of the tree's own citations.  It names a
    passage, and the tree names passages five ways: an ATX heading
    (`## The rule`), a numbered one (`## 10. Asking the compiler`), a
    setext one with `---` under it, a bold lead-in on a paragraph
    (`**Two clocks**`), and a bold lead-in on a bullet.  Several
    citations quote only a distinctive phrase from the middle of one.

    So what is checked is the thing that actually rots: **are these
    words still anywhere in that file.**  A section that was renamed or
    consumed takes its words with it — which is exactly how the three in
    the docstring above were found — while a citation that quotes a
    heading loosely, as half this tree does, keeps passing.
    """
    return _flat(path.read_text(encoding="utf-8")).lower()


def test_every_section_citation_resolves():
    known: dict[str, str] = {}
    missing = []
    for path in _files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:                        # pragma: no cover
            continue
        for target, section in CITE.findall(text):
            # A file citing its own sections is checked too — that is
            # where a rename goes unnoticed most easily.
            for where in (path.parent / target, ROOT / target,
                          ROOT / "spec" / target, ROOT / "doc" / target):
                if where.exists():
                    break
            else:
                continue                    # the file itself is elsewhere
            if str(where) not in known:
                known[str(where)] = _named(where)
            want = _flat(section).rstrip(".,;:").lower()
            if want not in known[str(where)]:
                missing.append(
                    f"{path.relative_to(ROOT)}: {target} §\"{section}\"")
    assert not missing, (
        "these citations point at headings that are not there:\n  "
        + "\n  ".join(sorted(set(missing))))


def test_every_card_citation_resolves():
    """A card is cited by its id, so a renamed card is a broken link —
    and a *moved* one is not, which is the point of the notation.

    The board's own rule: the filename is the id and it never
    renumbers, which is only worth anything if something checks.
    """
    missing = []
    for path in _files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:                        # pragma: no cover
            continue
        for card in CARD.findall(text):
            if not any((ROOT / shelf / card).exists() for shelf in SHELVES):
                missing.append(f"{path.relative_to(ROOT)}: card:{card}")
    assert not missing, (
        "these cards are cited and are on no shelf:\n  "
        + "\n  ".join(sorted(set(missing))))


#: A card written as a path, which is the spelling this replaced.
#: `board/README.md` is exempt: it is a real file that never moves, so
#: it is a path and not a card.
AS_PATH = re.compile(r"board/(?:done/|later/)?(?!README)[a-z][\w-]*\.md")


def test_no_card_is_cited_as_a_path():
    """**Two spellings of one id is how the churn comes back.**

    The `card:` notation only pays if the old form cannot return — and
    it would, because a path *looks* right and a reader who finds one
    pointing at the wrong shelf will helpfully correct it rather than
    delete it.  So the old spelling is refused outright.

    The exception is the markdown link list in `board/README.md`, which
    holds the order: those are relative links to files in the same
    directory, they resolve for a person clicking one, and they are
    checked by `test_board.py` against what is actually on the board.
    """
    stray = []
    for path in _files():
        if path.name == "README.md" and path.parent.name == "board":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:                        # pragma: no cover
            continue
        for hit in AS_PATH.findall(text):
            stray.append(f"{path.relative_to(ROOT)}: {hit}")
    assert not stray, (
        "a card is cited by path, and a path is the thing that rots "
        "when the card is finished — write `card:<name>.md`:\n  "
        + "\n  ".join(sorted(set(stray))))


def test_the_register_says_how_many_it_holds() -> None:
    """`fixme.md`'s own header counts its entries, and it had rotted.

    **The file whose discipline is that a claim does not go stale said
    "Of 130 entries, 113 are resolved" when it held 155 and 133** —
    read by everyone who opens it, wrong by twenty-five, for as long as
    nobody counted.  A number in prose is a claim like any other, so it
    gets the same treatment: something runs it.

    Finding it also turned up F100, which carried no `**[state]**` at
    all and appeared in no table — invisible since it was written,
    because every reader's eye and every count went past it.
    """
    text = (ROOT / "fixme.md").read_text(encoding="utf-8")
    heads = re.findall(r"^### F(\d+)\.\s+\*\*\[([^\]]+)\]\*\*", text, re.M)
    all_heads = re.findall(r"^### F\d+\.", text, re.M)
    assert len(heads) == len(all_heads), (
        "an entry carries no **[state]** — the counts below cannot see it")

    said = re.search(r"Of (\d+) entries, \*\*(\d+) are resolved\*\*", text)
    assert said, "fixme.md no longer says how many entries it holds"
    resolved = sum(1 for _n, state in heads if state in ("resolved", "fixed"))
    assert (int(said.group(1)), int(said.group(2))) == (len(heads), resolved), (
        f"fixme.md says {said.group(1)} entries and {said.group(2)} resolved; "
        f"it holds {len(heads)} and {resolved}")


def test_the_way_in_has_nothing_left_to_fill_in() -> None:
    """A command a stranger is told to run must be runnable as written.

    **F162**, found by a person: `README.md` and `doc/install.md` both
    opened the install with `git clone <this-repo>`, and the first
    instruction in the project's front door could not be carried out by
    the one reader it was written for.  He asked what he was supposed to
    put there, which is the whole defect — a placeholder in prose is a
    note to the author, and a placeholder inside a shell block is a
    question asked of somebody who cannot answer it.

    Scoped to fenced `sh` blocks in the two files that are the way in,
    deliberately: `<date>` and `<expr>` are honest placeholders in prose
    all over this tree, and a check that fired on those would be an
    andon nobody could read.
    """
    bad = []
    for name in ("README.md", "doc/install.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for block in re.findall(r"```sh\n(.*?)```", text, re.S):
            for token in re.findall(r"<[^>\s]+>", block):
                bad.append(f"{name}: {token}")
    assert not bad, (
        "a shell block in the way in still has something to fill in, and "
        "the reader it is written for cannot fill it:\n  "
        + "\n  ".join(bad))
