#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-22 — "We aren't smart or super.  We just have good processes."
"""tools/seedaudit.py — does this directory have the pieces, and is anything behind them?

    tools/seedaudit.py              audit this tree
    tools/seedaudit.py PATH         audit a directory that copied the standard
    tools/seedaudit.py --quiet      exit status only
    tools/seedaudit.py --table      the pieces as a markdown table, for doc/method.md

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

**Tested by taking pieces away, 2026-08-24.**  `tools/seedmutate.sh`
removes one piece or one gate at a time from a copy and audits it; the
first sweep found three pieces whose gate could vanish unseen, because
`backed_by` searched every test for a mention.  Now each piece declares
its `gate` and only that file is read.  The in-process half is
`test_seedaudit.py::test_taking_any_piece_away_is_seen`, a suite gate.

**First run against a real copy on 2026-08-24** — `~/tend`, the first
directory this audit was pointed at that is not its own.  It found the
tree it was aimed at (2 of 10 pieces at its first commit, 6 by the end
of that day), and it found one thing about itself: `CAPPED` is this
tree's own list of documents, so a tree that never promised
`doc/instruments.md` is reported as unable to keep a promise it never
made.  Encoding this project's accidents as another project's
requirements is the failure `card:working-standard.md` warned about,
and the `PATH` argument now has the evidence for it rather than the
warning alone.
"""

import argparse
import pathlib
import re
import sys

# Every entry here is an artifact that has no reason to exist except that
# somebody on the other end is a person.  `why` is that reason, in one
# line, and it is the column that decides whether an entry belongs.
PIECES = [
    dict(name="the fence", gate="test/test_safety.py",
         why="a session cannot edit its own restraints",
         paths=[".claude/settings.json", "tools/sandbox.sh"]),
    dict(name="the gates", gate="test/test_precommit.py",
         why="the rules are enforced outside the model that must follow them",
         paths=["tools/suite.py", "tools/pre-commit.sh"]),
    dict(name="the consent register", gate="test/test_consent.py",
         why="a named third party agreed to being named",
         paths=["doc/consent.md"]),
    dict(name="the andon", gate="test/test_andon.py",
         why="a session can raise a question and reach a person who answers",
         paths=["tools/andon.sh"]),
    dict(name="a blocked status", gate="test/test_board.py",
         why="a session may stop and say why, instead of guessing on",
         paths=["board/README.md"]),
    dict(name="the rules cap", gate="test/test_rules.py",
         why="the rules stay short enough that a person actually reads them",
         paths=["spec/rules.md", "tools/rulecount.py"]),
    dict(name="the memory split", gate="test/test_memory.py",
         why="what is known about a person is not automatically the tree's",
         paths=["doc/memory/README.md"]),
    dict(name="the sitting limit", gate="test/test_limit.py",
         why="the person's own hours are the person's",
         paths=["tools/limit.sh"]),
    dict(name="the boot surface", gate="test/test_rules.py",
         # Henri, 2026-08-24, the whole why in his words.  What arrives
         # at a session before it asks for anything: the one-line pointer
         # (and, outside any directory, the memory index — which this
         # audit cannot see and says so in card:working-standard.md).
         why="nothing else reaches a session unasked",
         paths=["AGENTS.md"]),
    dict(name="the author's own document", gate="test/test_gemba.py",
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


def backed_by(root, path, gate):
    """Does the piece's declared gate exist, and name this path?

    One file per piece, declared in `PIECES`, and only that file is
    read.  Until 2026-08-24 this searched every `test_*.py` for a
    mention, and `tools/seedmutate.sh` showed what that bought: the
    test behind a piece could be deleted and a citation of the path in
    some other test kept the piece green — three of nine, then two of
    ten.  A gate somebody named is a claim somebody can be wrong about;
    a mention found by search is not a claim at all.

    Still weak on purpose beyond that — mention inside the gate is
    checkable from outside, correctness is not; see the module
    docstring.  `test_seedaudit.py` is refused as a gate because it
    names every path in order to test this audit."""
    if gate.endswith("test_seedaudit.py") or not gate.startswith("test/test_"):
        return None
    f = root / gate
    if not f.is_file():
        return None
    try:
        return gate if path.rstrip("/") in f.read_text(encoding="utf-8", errors="ignore") else None
    except OSError:
        return None


def audit_pieces(root):
    rows = []
    for piece in PIECES:
        missing = [p for p in piece["paths"] if not (root / p).exists()]
        backing = None
        if not missing:
            # Every path of the piece, in the one declared gate.
            hits = [backed_by(root, p, piece["gate"]) for p in piece["paths"]]
            backing = piece["gate"] if all(hits) else None
        rows.append(dict(piece, missing=missing, backing=backing))
    return rows


def ignore_rules(root):
    """Every `.gitignore` under root, as (directory, pattern) pairs.

    The tree's own rule for that file — *ignore what a command can make
    again, keep what it cannot* — is exactly the distinction a promise
    check needs and could not make until 2026-08-24: a fresh clone was
    red on `test/gates.md` and `target/release/`, five promises that
    were not broken but unbuilt.  Read here rather than asked of `git`,
    because a copy of the standard need not be a repository."""
    rules = []
    for f in sorted(root.rglob(".gitignore")):
        if any(part in (".git", ".venv", "node_modules") for part in f.parts):
            continue
        base = f.parent.relative_to(root)
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            rules.append((base, line))
    return rules


def is_ignored(root, rel, rules=None):
    """Would git ignore `rel`?  The common cases of the syntax, no more:
    an anchored pattern (`/target/`, `test/gates.md`) matches under its
    own directory; a bare one (`*.wav`, `target/`) matches any level."""
    import fnmatch
    rules = ignore_rules(root) if rules is None else rules
    rel = rel.rstrip("/")
    parts = pathlib.PurePosixPath(rel).parts
    for base, pat in rules:
        try:
            sub = pathlib.PurePosixPath(rel).relative_to(base) if str(base) != "." else pathlib.PurePosixPath(rel)
        except ValueError:
            continue
        pat = pat.rstrip("/")  # a cited `x/` is a directory promise either way
        anchored = pat.startswith("/") or "/" in pat
        pat = pat.lstrip("/")
        sp = sub.parts
        for i in range(len(sp)):
            head = "/".join(sp[: i + 1])
            if anchored:
                if fnmatch.fnmatchcase(head, pat):
                    return True
            elif fnmatch.fnmatchcase(sp[i], pat):
                return True
    return False


def audit_promises(root):
    """Paths the method documents name, that this directory does not have.

    Returns (broken, unbuilt): the second is every missing promise the
    tree's own `.gitignore` says a command makes again.  Reported, never
    failed on — the audit cannot run the command, and a clone that has
    not built yet is not a clone that copied the prose and left the
    machinery."""
    broken, unbuilt = {}, {}
    rules = ignore_rules(root)
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
            if is_ignored(root, cited, rules):
                unbuilt.setdefault(cited, []).append(doc)
            else:
                broken.setdefault(cited, []).append(doc)
    return broken, unbuilt


def method_table():
    """The standard, stated for a person: one row per piece.

    `doc/method.md` carries this block verbatim and `test_citations.py`
    refuses the page when it differs — the same rule as the atlas: a
    generated page behind its source is the defect class the gates
    exist for.  Until 2026-08-24 the pieces were stated only here, in a
    Python list, and a stranger asking what the standard was had to
    read a tool."""
    lines = ["| the piece | it exists because | the test that gates it |",
             "|---|---|---|"]
    for piece in PIECES:
        paths = ", ".join(f"`{p}`" for p in piece["paths"])
        lines.append(f"| {piece['name']} — {paths} | {piece['why']} | `{piece['gate']}` |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".", type=pathlib.Path)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    root = args.path.resolve()
    if args.table:
        print(method_table())
        return 0

    rows = audit_pieces(root)
    broken, unbuilt = audit_promises(root)

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
        elif not unbuilt:
            print("    none — every path the documents name exists here")
        for cited, docs in sorted(unbuilt.items()):
            print(f"    unbuilt   {cited:<26}  a command makes it; named in {', '.join(sorted(set(docs)))}")
        print()
        print(f"  {len(rows) - len(absent)} of {len(rows)} pieces present,"
              f"  {len(unbacked)} unbacked,"
              f"  {len(broken)} unkept promise(s),"
              f"  {len(unbuilt)} unbuilt")
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
