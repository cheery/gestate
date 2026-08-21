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
#: **`.claude` is here because an agent worktree lives inside it.**  A
#: worktree made for a subagent is a second checkout *under* `ROOT`, so
#: this walker found its copy of every document and checked citations
#: that belong to another branch — including this file's own docstring,
#: whose dead examples are exempt by identity and stop being identical
#: the moment there are two of them.  Found 2026-08-19 the first evening
#: a worktree existed: the gates went red, and with the pre-commit hook
#: installed that refuses every commit until the worktree is removed.
SKIP = {"target", ".venv", "__pycache__", ".git", "node_modules", ".claude"}

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


#: **`journal.md` names the journal, not one file of it.**  Closed
#: months move to `journal/YYYY-MM.md` and are never edited again
#: (`spec/rules.md` §"The journal rotates"), so a citation written in
#: June would break in July for no reason but the calendar — which is
#: exactly the rot this file was written to stop, and exactly the
#: separation the `card:` notation already makes between a card's id
#: and its shelf.  So the journal is searched as one corpus: the open
#: month plus every closed one.
#:
#: Rewriting the citations at each rotation was the alternative, and it
#: is the spelling that rots: a tree-wide edit every month, twenty-eight
#: of them at the first count, each one a chance to point at the wrong
#: month.
def _corpus(where: Path) -> list[Path]:
    if where == ROOT / "journal.md":
        return [where, *sorted((ROOT / "journal").glob("*.md"))]
    return [where]


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
                known[str(where)] = " ".join(_named(f) for f in _corpus(where))
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


#: `doc/method.md`'s table gives a size for each document so that a
#: visitor can decline to read one honestly.  A size is a claim, and
#: this file already holds the precedent for what happens to an
#: unchecked one — §"The register says how many it holds", where the
#: defect ledger advertised 130 entries while holding 155.
#:
#: **The page was out of date before it was a day old.**  Adding two
#: bullets to `README.md` in the same commit that wrote the table left
#: the table saying 247 for a 250-line file — which is the whole
#: argument for this check, arriving immediately and by accident.
METHOD = ROOT / "doc" / "method.md"

#: A row of that table: the linked document, then its size.
SIZE_ROW = re.compile(r"^\| \[`([^`]+)`\]\([^)]+\) \| ([\d,~]+) \|", re.M)

#: Numbers in this tree's prose are spelled, because prose is for
#: reading.  Only the words actually used are here, and a word that is
#: not is a readable failure rather than a `ValueError` — which this
#: table earned the hard way: the first version of `_said` fell through
#: to `int("forty")` and reported the checker's own stack trace to
#: somebody who had simply written a number out in words.  That is F162's
#: class exactly, in the file that holds the check for it.
WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
    "twenty-four": 24, "twenty-five": 25, "twenty-six": 26,
    "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29, "thirty": 30,
}


def _said(text: str, pattern: str) -> int:
    """The number the page claims, written either way."""
    m = re.search(pattern, text, re.I)
    assert m, f"doc/method.md no longer says anything matching /{pattern}/"
    word = m.group(1)
    if word.lower() in WORDS:
        return WORDS[word.lower()]
    digits = word.replace(",", "")
    assert digits.isdigit(), (
        f"doc/method.md writes {word!r} where /{pattern}/ wants a number, "
        f"and this checker cannot read it.  Either spell it in digits or "
        f"add {word.lower()!r} to WORDS above — do not leave it, because "
        f"an unreadable claim is an unchecked one.")
    return int(digits)


def _lines(rel: str) -> int:
    path = ROOT / rel
    if path.is_dir():
        return sum(len(f.read_text(encoding="utf-8").splitlines())
                   for f in sorted(path.glob("*.md")))
    return len(path.read_text(encoding="utf-8").splitlines())


def test_the_method_pages_sizes_are_the_sizes():
    """Every exact figure in the depth table, against the file.

    **Approximate figures are checked approximately**, and that is not
    a loophole: `~16,000` for `spec/` is an honest order of magnitude
    for sixteen files nobody reads in one sitting, and pinning it to
    the line would make the page churn on every spec edit for no
    reader's benefit.  Five per cent is where "about" stops being true.
    """
    text = METHOD.read_text(encoding="utf-8")
    rows = SIZE_ROW.findall(text)
    assert len(rows) >= 5, (
        "doc/method.md's depth table no longer parses — the check that "
        "keeps its sizes honest is now checking nothing.")

    wrong = []
    for name, claim in rows:
        real = _lines(name.rstrip("/"))
        if claim.startswith("~"):
            want = int(claim[1:].replace(",", ""))
            if abs(real - want) > 0.05 * real:
                wrong.append(f"{name}: page says ~{want:,}, it is {real:,}")
        elif int(claim.replace(",", "")) != real:
            wrong.append(f"{name}: page says {claim}, it is {real:,}")
    assert not wrong, (
        "doc/method.md's sizes are behind the files they describe, and "
        "that page is what a visitor is handed instead of the tree:\n  "
        + "\n  ".join(wrong))


def test_the_method_page_counts_what_the_tree_counts():
    """The four figures in its prose that something else already knows.

    Each of these is a number the tree measures somewhere — the gate
    list, the cap, the defect ledger, the archive — quoted into a page
    written for somebody with no way to check it.  That asymmetry is
    the reason this is a gate and not a habit.
    """
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import rulecount
    import suite

    text = METHOD.read_text(encoding="utf-8")
    fixme = (ROOT / "fixme.md").read_text(encoding="utf-8")
    heads = re.findall(r"^### F\d+\.\s+\*\*\[([^\]]+)\]\*\*", fixme, re.M)
    resolved = sum(1 for state in heads if state in ("resolved", "fixed"))

    checks = [
        ("the gates", _said(text, r"([A-Za-z-]+|\d+) structural checks"),
         len(suite.GATES)),
        ("the rules cap", _said(text, r"growing past ([\d,]+) lines"),
         rulecount.CAP),
        ("fixme's entries", _said(text, r"\| ([\d,]+) entries,"), len(heads)),
        ("fixme's resolved", _said(text, r"entries, ([\d,]+) resolved"),
         resolved),
        ("fixme's open", _said(text, r"so the ([\w-]+) open ones"),
         len(heads) - resolved),
        ("the archived month", _said(text, r"([\d,]+) lines for its first"),
         _lines("journal/2026-08.md")),
    ]
    wrong = [f"{what}: page says {said:,}, it is {real:,}"
             for what, said, real in checks if said != real]
    assert not wrong, (
        "doc/method.md quotes numbers the tree already measures, and they "
        "have drifted:\n  " + "\n  ".join(wrong))
