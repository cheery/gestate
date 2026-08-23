#!/usr/bin/env python3
#: asked-by: Henri, 2026-08-21 — card:dangling-names.md — he asked whether option D was safe enough to try
"""tools/dangling.py — names the tree leans on and never says.

    python tools/dangling.py                 the report, against the working tree
    python tools/dangling.py --at 5f42f68    against a revision, for validation
    python tools/dangling.py --all           every candidate, not only the suspects

**This is a report and not a gate.**  It is in `tools/` and not in
`test/` on purpose: `card:dangling-names.md` measured option D at one
clean hit in five, and a check that accuses honest text four times out
of five is a check that gets muted — and a muted gate costs the standing
of the gates that work.  So this prints and returns 0.  Whether it ever
becomes a gate is a decision Henri has not made, and two of the things
it waits on are written under §"What this cannot do" below.

**What it looks for.**  A named concept — *the A3 rule*, *the drop rule*
— cited as though it were defined somewhere, in prose, with no id.  The
signature is a name that is only ever *referred to* and never
*asserted*: no heading carries it, no bold lead, no sentence of the form
*the X rule is / says / means*.  Grep cannot tell a citation from a
definition and fails outright when the two use different words, which is
not a limitation of grep — it is the whole of the defect.

**Three measurement bugs are already recorded on the card, and two of
them are fixed here.**  The third is not a bug in code.

1. *The census excluded `A3` from its own motivating case* — the name
   pattern required a lowercase first letter.  Fixed: `NAME` admits
   digits and capitals.
2. *`\\*\\*[^*]*` crossed newlines*, so any `**` earlier in a file made
   every later name read as asserted.  Fixed: `BOLD` is line-bounded,
   and the assertion scan runs per line.
3. *The site list undercounted documents* — a harvester matching
   roughly *"the ⟨word⟩ rule"* cannot see `the knob's placement rule`,
   `the ordinary application rule` or `one transport rule for every
   plugin`.  Fixed by **dropping the article from the pattern
   altogether**: what is harvested is the noun phrase, whatever stands
   in front of it.  That third bug is the one that mattered, because a
   definition often introduces itself with exactly the shape the old
   pattern was blind to — `transport rule` was flagged only because the
   site holding its definition was invisible.

**And the confound the work order found is fixed here too.**  Three of
the five names checked on 2026-08-21 crossed a document boundary only
because one sentence had been quoted — a journal entry quoting
`fixme.md`, or one spec file copying a sentence into another.  Two sites
whose surrounding prose is the same prose are **one** use, so they are
folded together before the documents are counted.  See `_dedup`.

**The journal is one document.**  Closed months move to
`journal/YYYY-MM.md` and are never edited again, so counting them
separately would make a name cross a boundary by the calendar.  Same
reading as `test/test_citations.py` §"`journal.md` names the journal".
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SEARCHED = ("*.py", "*.rs", "*.md", "*.ges")
SKIP = {"target", ".venv", "__pycache__", ".git", "node_modules", ".claude"}

#: **The checker cannot be its own subject.**  `card:dangling-names.md`
#: is this file's argument, and it cites all five suspect names dozens of
#: times while asserting none of them — so left in, it would flag every
#: name it exists to discuss and would keep flagging them after they were
#: fixed.  Same exemption, and the same reason, as `test_citations.py`
#: excluding itself.  One file, named here rather than special-cased
#: quietly.
EXEMPT = {ROOT / "board" / "dangling-names.md", Path(__file__).resolve()}

#: The noun phrase.  Three things in it are each a repair.
#:
#: **Capitals and digits are admitted** — bug 1, the run that existed for
#: `A3` could not see `A3`.
#:
#: **The determiner may stand one word away from the name** — bug 3.  A
#: pattern anchored on *"the ⟨word⟩ rule"* is blind to `the knob's
#: placement rule`, `the ordinary application rule` and `one transport
#: rule for every plugin`, and that last one is a *definition*.  A
#: determiner is still required, because without one the harvester
#: collects every verb phrase in the tree; what is lifted is the
#: requirement that it sit flush against the name.
#:
#: **Singular only, and `rule` only.**  Both are narrowings against
#: measured noise, and both are stated in the report.  Plurals in this
#: corpus are ordinary English — *"eqtype/semilattice/fixtype rules"* is
#: one row of a pipeline diagram, and the 2026-08-21 hand-check read that
#: plural as evidence the name was not a term.  And `test` in a
#: repository of tests collects `MIDI test`, `fenced test`, `five test`
#: and `equality test` before it collects one name: 36 suspects, of which
#: the `rule` shape held every case anybody has confirmed.  The cost is
#: written down — *the earning test* is exactly the class this is for and
#: this pattern cannot see it.
NAME = re.compile(
    r"\b(?:the|a|an|one|this|that|its|his|her|their|our|each|every|"
    r"another)[ ]+(?:[\w'’-]+[ ]+)?([A-Za-z][\w-]*)[ ]+(rule)\b")

#: Ordinary English in the modifier slot.  `the same rule`, `no rule`,
#: `each test` — the harvester's own noise, not names.
GENERIC = {
    "the", "a", "an", "one", "two", "three", "this", "that", "these",
    "those", "each", "every", "no", "any", "some", "same", "other",
    "others", "another", "first", "second", "third", "last", "next",
    "only", "own", "new", "old", "whole", "general", "ordinary",
    "simple", "single", "real", "right", "wrong", "good", "bad", "main",
    "above", "below", "following", "such", "per", "its", "his", "her",
    "their", "our", "my", "your", "more", "most", "less", "few", "many",
    "several", "both", "all", "which", "what", "whose", "and", "or",
    "separate", "different", "special", "further", "own",
    "but", "of", "in", "on", "by", "for", "to", "as", "is", "are", "was",
    "were", "be", "been", "it", "they", "we", "you", "he", "she", "not",
    "than", "then", "when", "where", "how", "why", "if", "so", "with",
    "without", "under", "over", "into", "onto", "from", "at",
    "unit", "regression", "smoke", "acceptance", "property", "failing",
    "passing", "green", "red", "broken", "new-", "the-",
}

#: A bold lead, **bounded by the line**.  Bug 2 was this pattern reaching
#: across newlines: one `**` early in a file made every later name in it
#: read as asserted, and the first detector run reported one suspect
#: where there were six.  The result looked clean and was an artefact.
BOLD = re.compile(r"\*\*([^*\n]+)\*\*")

#: A heading of any of the shapes this tree uses.
HEADING = re.compile(r"^\s*(?:#{1,6}|(?:#:|#|///|//|>)?\s*\d+\.)\s+(.*)$")

#: *the X rule is / says / means / restricts …* — the name carrying its
#: own definition.  The verb list is the card's, widened by the verbs
#: this corpus actually uses to state a rule.
ASSERTS = re.compile(
    r"\b(is|was|says?|said|means?|meant|restricts?|takes?|requires?|"
    r"reads?|holds?|applies|governs?|states?|forbids?|allows?|demands?)\b")

#: A definition given in place: the name, then a colon or an em-dash,
#: then the content.  `spec/export.md:22` — *"under one transport rule
#: for every plugin: **it plays while the transport runs**"* — is
#: asserted in exactly this shape and was missed twice by the first
#: detector, once because the determiner was `one` and once because the
#: assertion follows the name instead of carrying it.
INPLACE = re.compile(r"[^.!?\n]{0,90}[:—]\s*\S")

MARKER = re.compile(r"^\s*(?:#:|#|///|//|>|\*)\s?")


def _norm(s: str) -> str:
    """Prose stripped to what two copies of one sentence have in common."""
    s = MARKER.sub("", s)
    s = re.sub(r"[`*_\[\]()]", "", s)
    return " ".join(re.sub(r"[^\w\s]", " ", s).lower().split())


# --------------------------------------------------------------- sources

def _tree_files():
    for pattern in SEARCHED:
        for path in ROOT.rglob(pattern):
            if any(part in SKIP for part in path.parts):
                continue
            if path.resolve() in EXEMPT:
                continue
            yield str(path.relative_to(ROOT)), path.read_text(
                encoding="utf-8", errors="replace")


def _rev_files(rev: str):
    """The same corpus at a revision.

    **Validation needs this.**  The one thing option D has actually
    proven is that it flagged `A3 rule` at `5f42f68`, before the rule was
    named, and went silent once the name was attached — detects the real
    case, responds to the real fix.  A rewritten detector that cannot be
    run against that revision cannot make the same claim, and both bugs
    already on the card were found by checking against a case whose
    answer was known.
    """
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", rev],
                             cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.split()
    suffixes = {p.lstrip("*") for p in SEARCHED}
    for name in listing:
        if not any(name.endswith(s) for s in suffixes):
            continue
        if any(part in SKIP for part in Path(name).parts):
            continue
        if (ROOT / name).resolve() in EXEMPT:
            continue
        blob = subprocess.run(["git", "show", f"{rev}:{name}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
        yield name, blob.decode("utf-8", errors="replace")


def _document(path: str) -> str:
    """Which document a file belongs to.  The journal is one."""
    if path == "journal.md" or path.startswith("journal/"):
        return "journal"
    return path


# ---------------------------------------------------------------- harvest

class Site:
    __slots__ = ("path", "line", "text", "name", "form", "asserted")

    def __init__(self, path, line, text, name, form):
        self.path, self.line, self.text = path, line, text
        self.name, self.form = name, form
        self.asserted = None


def _assertion(line: str, name: str, form: str) -> str | None:
    """Does this line *say what the rule is*, rather than lean on it?

    Four shapes, and the range of all four is stated in the report.
    """
    phrase = f"{name} {form}"
    low = line.lower()
    where = low.find(phrase.lower())
    if where < 0:
        return None
    head = HEADING.match(line)
    if head and phrase.lower() in head.group(1).lower():
        return "heading"
    for bold in BOLD.finditer(line):
        if phrase.lower() in bold.group(1).lower():
            return "bold lead"
    after = line[where + len(phrase):]
    verb = ASSERTS.match(after.strip())
    if verb:
        return f"“… {form} {verb.group(1)} …”"
    if INPLACE.match(after):
        return "defined in place"
    return None


def _harvest(files):
    sites: dict[str, list[Site]] = defaultdict(list)
    for path, text in files:
        for n, line in enumerate(text.splitlines(), 1):
            for m in NAME.finditer(line):
                word, form = m.group(1), m.group(2)
                if word.lower() in GENERIC:
                    continue
                singular = form.rstrip("s")
                name = f"{word} {singular}"
                site = Site(path, n, line.strip(), word, form)
                site.asserted = _assertion(line, word, form)
                sites[name].append(site)
    return sites


def _dedup(sites: list[Site], window: int = 150, ratio: float = 0.70):
    """Fold sites whose surrounding prose is the same prose.

    **The confound, in the form the work order predicted and in the form
    it did not.**  `fixtype rule` and `application rule` each crossed a
    document boundary because a journal entry quoted a `fixme.md`
    sentence back with one connective changed; `drop rule` crossed
    because one *spec* file copied a sentence into another, three words
    inserted.  Neither name ever left the sentence it was written in.

    Compared on a window either side of the name rather than on a
    sentence, because sentence boundaries in this prose are unreliable —
    backticks, colons, em-dashes and `Cyclic n.` all break a naive
    split, and the two `fixtype` copies differ exactly at a connective
    near the boundary.
    """
    groups: list[list[Site]] = []
    for site in sites:
        low = site.text.lower()
        at = low.find(site.name.lower())
        start = max(0, at - window)
        ctx = _norm(site.text[start:at + window])
        for group in groups:
            head = group[0]
            hlow = head.text.lower()
            hat = hlow.find(head.name.lower())
            hctx = _norm(head.text[max(0, hat - window):hat + window])
            if difflib.SequenceMatcher(None, ctx, hctx).ratio() >= ratio:
                group.append(site)
                break
        else:
            groups.append([site])
    return groups


# ----------------------------------------------------------------- report

def _report(sites, show_all: bool, where: str) -> int:
    rows, folded = [], []
    for name, found in sorted(sites.items()):
        groups = _dedup(found)
        docs = {_document(g[0].path) for g in groups}
        raw = {_document(s.path) for s in found}
        asserted = [s for g in groups for s in g if s.asserted]
        if len(docs) < 2:
            # **Folded, not dropped.**  A name that crossed a document
            # boundary only by being quoted is not a suspect — that is
            # the confound the work order predicted.  But it is also not
            # nothing: `drop rule` folds here, and the 2026-08-21
            # hand-check called it *genuine* on the content while the
            # work order's own confound rule says the boundary was an
            # artefact.  The two readings disagree, so neither is
            # applied silently; the fold is shown.
            if len(raw) > 1 and not asserted:
                folded.append((name, groups, raw))
            continue
        rows.append((name, groups, docs, asserted))

    suspects = [r for r in rows if not r[3]]
    cleared = [r for r in rows if r[3]]

    print(f"tools/dangling.py — {where}")
    print(f"{len(sites)} candidate names harvested, "
          f"{len(rows)} cited from more than one document, "
          f"{len(suspects)} asserted nowhere, "
          f"{len(folded)} folded to one sentence.\n")

    for name, groups, docs, asserted in suspects:
        print(f"EPÄILTY  {name}  —  {len(docs)} documents, "
              f"{len(groups)} independent uses")
        for group in groups:
            head = group[0]
            print(f"    {head.path}:{head.line}  {head.text[:96]}")
            for dup in group[1:]:
                print(f"      = {dup.path}:{dup.line}  (same sentence)")
        print()

    for name, groups, raw in folded:
        print(f"folded   {name}  —  {len(raw)} documents, one sentence")
        for group in groups:
            head = group[0]
            print(f"    {head.path}:{head.line}  {head.text[:96]}")
            for dup in group[1:]:
                print(f"      = {dup.path}:{dup.line}  (same sentence)")
        print()

    if show_all:
        for name, groups, docs, asserted in cleared:
            first = asserted[0]
            print(f"asserted {name}  —  {first.asserted} "
                  f"at {first.path}:{first.line}")
        print()

    print("""What this cannot do, and it belongs beside the result
  * It sees one shape — ⟨name⟩ rule / test / convention.  *The corner*,
    *the way in*, *the earning test* are the same class and only the
    last of those is visible to this pattern.
  * False negatives are silent.  A rule asserted in a sentence none of
    the four shapes covers reads as healthy.
  * It is a heuristic over English, so it will accuse honest text.
  * **And it does not know what a verdict turns on.**  Whether a name is
    dangling because no sentence says what the rule *is*, or because no
    sentence attaches *the name* to the rule, is undecided —
    card:dangling-names.md §"Two questions back".  `drop rule` and
    `placement rule` land differently under the two readings, and this
    report answers the second one, because that is what the A3 case
    turned on.  It is not the report's decision to make.""")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--at", metavar="REV",
                    help="run against a git revision, for validation")
    ap.add_argument("--all", action="store_true",
                    help="also list the names an assertion cleared")
    args = ap.parse_args()
    if args.at:
        files, where = _rev_files(args.at), f"at {args.at}"
    else:
        files, where = _tree_files(), "the working tree"
    return _report(_harvest(files), args.all, where)


if __name__ == "__main__":
    sys.exit(main())
