#!/usr/bin/env python3
"""tools/seedaudit.py — does this directory have the pieces, and is anything behind them?

    tools/seedaudit.py              audit this tree
    tools/seedaudit.py PATH         audit a directory that copied the standard
    tools/seedaudit.py --quiet      exit status only

**What this is for.**  Henri, 2026-08-22, on finding the same practice
being re-derived elsewhere:

    "We aren't smart or super.  We just have good processes.  The unsafe
    part about what I saw, was that nothing in the ruleset it had, did
    not encode respect toward people and others.  Also, it relied on
    unchecked processes."

Two failures, and this looks for both.  It does **not** read the prose
and judge it — no test finds respect in a document, and a check that
tried would be the unchecked process it is complaining about.  It checks
the two things an outsider can check without reading anything:

1. **The pieces that exist only because a person is on the other end.**
   Take the people out of this project and every artifact in `PIECES`
   below is dead weight.  That is the auditable form of "encodes respect
   toward people": not a sentiment in a document, an affordance on disk.

2. **The promises.**  The capped documents name tools, files and
   commands.  Every one of those is a promise to whoever reads them.  A
   directory that copied the documents and not the machinery is the 9B
   case — `card:working-standard.md` §"The documents assume an
   environment, and never say which" — and it is invisible from inside,
   because the file on disk reads correctly either way.

**What "backed" means, and its honest limit.**  A piece is *backed* when
a **test** names its path — so removing it breaks a run rather than
passing silently.  That is a weaker claim than "a test fails if this is
wrong", and it is deliberately weak: mention is checkable from outside,
correctness is not.  A piece marked UNBACKED is a rule with no gate; a
piece marked backed may still be one.

**This file's harvester was wrong three times, all the same way.**  It
searched `tools/` as well, so every tool named itself and all nine
pieces passed.  It called thirteen present files unkept promises,
because the documents write `test_board.py` without its directory.  And
then `test/test_seedaudit.py` — which names the paths in order to test
the audit — backed them, so the andon went green by being *discussed*.
That is `card:dangling-names.md` arriving three times in one morning:
*the experiment did not test the detector, it tested the harvester, and
the harvester failed.*  The third one was caught only by the canary at
the bottom of that test file, which is the argument for keeping it.

**It has only ever been run against this tree.**  There is no seeded
project yet, so the `PATH` argument is untested against a real copy —
which is itself a finding this file should keep printing until it is
false.
"""

import argparse
import pathlib
import re
import sys

# Every entry here is an artifact that has no reason to exist except that
# somebody on the other end is a person.  `why` is that reason, in one
# line, and it is the column that decides whether an entry belongs.
PIECES = [
    dict(name="the fence",
         why="a session cannot edit its own restraints",
         paths=[".claude/settings.json", "tools/sandbox.sh"]),
    dict(name="the gates",
         why="the rules are enforced outside the model that must follow them",
         paths=["tools/suite.py", "tools/pre-commit.sh"]),
    dict(name="the consent register",
         why="a named third party agreed to being named",
         paths=["doc/consent.md"]),
    dict(name="the andon",
         why="a session can raise a question and reach a person who answers",
         paths=["tools/andon.sh"]),
    dict(name="a blocked status",
         why="a session may stop and say why, instead of guessing on",
         paths=["board/README.md"]),
    dict(name="the rules cap",
         why="the rules stay short enough that a person actually reads them",
         paths=["spec/rules.md", "tools/rulecount.py"]),
    dict(name="the memory split",
         why="what is known about a person is not automatically the tree's",
         paths=["doc/memory/README.md"]),
    dict(name="the sitting limit",
         why="the person's own hours are the person's",
         paths=["tools/limit.sh"]),
    dict(name="the author's own document",
         why="the person keeps a document no session rewrites",
         paths=["spec/author.md"]),
]

# The documents that carry the method, and therefore do the promising.
CAPPED = ["board/README.md", "manifesto.md", "spec/author.md",
          "doc/instruments.md", "vision.md"]

# A path named in prose: `tools/andon.sh`, `doc/memory/`, `spec/rules.md`.
CITED = re.compile(r"`([a-z_][\w./-]*\.(?:sh|py|md|json)|[a-z_][\w./-]*/)`")

# Where a bare basename in prose is allowed to live.  `test_board.py` and
# `dialoglag.py` are written without their directory all over the
# documents, and calling those unkept promises was the first version's
# second harvester bug.
LOOKIN = ["", "tools/", "test/", "board/", "doc/", "spec/", "journal/",
          "board/done/", "board/later/", "doc/memory/", "doc/notes/"]

# A citation with a placeholder in it promises a shape, not a file.
PLACEHOLDER = re.compile(r"YYYY|MM|<|>|\{|\.\.\.|\*|N\.md")


def backed_by(root, path):
    """Which test names this path?

    Tests only, and never the artifact itself.  Searching `tools/` too
    was the first version's bug: a tool always contains its own name, so
    every piece passed.  Weak on purpose beyond that — see the module
    docstring."""
    needle = path.rstrip("/")
    base = root / "test"
    if not base.is_dir():
        return None
    for f in sorted(base.rglob("test_*.py")):
        # A test *about* this audit is not a gate on the pieces it names.
        if f.name == "test_seedaudit.py":
            continue
        if f.samefile(root / path) if (root / path).is_file() else False:
            continue
        try:
            if needle in f.read_text(encoding="utf-8", errors="ignore"):
                return f"test/{f.relative_to(base)}"
        except OSError:
            continue
    return None


def audit_pieces(root):
    rows = []
    for piece in PIECES:
        missing = [p for p in piece["paths"] if not (root / p).exists()]
        backing = None
        if not missing:
            for p in piece["paths"]:
                backing = backing or backed_by(root, p)
        rows.append(dict(piece, missing=missing, backing=backing))
    return rows


def audit_promises(root):
    """Paths the method documents name, that this directory does not have."""
    broken = {}
    for doc in CAPPED:
        f = root / doc
        if not f.is_file():
            broken.setdefault("(the document itself)", []).append(doc)
            continue
        text = re.sub(r"```.*?```", " ", f.read_text(encoding="utf-8"), flags=re.S)
        for cited in sorted(set(CITED.findall(text))):
            if PLACEHOLDER.search(cited):
                continue
            if any((root / where / cited).exists() for where in LOOKIN):
                continue
            broken.setdefault(cited, []).append(doc)
    return broken


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".", type=pathlib.Path)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    root = args.path.resolve()

    rows = audit_pieces(root)
    broken = audit_promises(root)

    absent = [r for r in rows if r["missing"]]
    unbacked = [r for r in rows if not r["missing"] and not r["backing"]]

    if not args.quiet:
        print(f"seedaudit: {root}")
        print()
        print("  the pieces that exist only because a person is on the other end")
        print()
        for r in rows:
            if r["missing"]:
                mark, note = "ABSENT  ", "missing " + ", ".join(r["missing"])
            elif r["backing"]:
                mark, note = "ok      ", r["backing"]
            else:
                mark, note = "UNBACKED", "no test names it"
            print(f"    {mark}  {r['name']:<26}  {note}")
            if not r["backing"] or r["missing"]:
                print(f"              {r['why']}")
        print()
        print("  promises the method documents make that this directory cannot keep")
        print()
        if broken:
            for cited, docs in sorted(broken.items()):
                print(f"    MISSING   {cited:<26}  named in {', '.join(sorted(set(docs)))}")
        else:
            print("    none — every path the documents name exists here")
        print()
        print(f"  {len(rows) - len(absent)} of {len(rows)} pieces present,"
              f"  {len(unbacked)} unbacked,"
              f"  {len(broken)} unkept promise(s)")
        if unbacked:
            print()
            print("  An unbacked piece is a rule with no gate — the second of the")
            print("  two failures this audit exists for.  It fails the run.")

    # Unbacked joined this list on 2026-08-22, once the andon and the
    # sitting limit had tests.  It could not before: a check nobody can
    # leave green gets switched off, so the ratchet is pulled after the
    # tree is clean, never as a way of announcing that it should be.
    return 1 if (absent or broken or unbacked) else 0


if __name__ == "__main__":
    sys.exit(main())
