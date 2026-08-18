"""Every complaint this program can make, and what it is for — `card:error-messages.md`.

**A message that names no place has nowhere to be drawn.**  The
workbench puts a complaint in a content box under the line it names,
and it finds that line by reading the message text: `session._line_of`
looks for `at 12:8`, `at line 134:8` or `at broken.ges:2:8` and gets
`0` — nowhere — from anything else.  So "does this message land where
the person is looking" is a property of the *string*, and therefore one
a tool can ask about.

That is what this module is.  It walks the source, finds every `raise`
of an error this program defines, and pairs it with a **verdict** the
author of that error wrote down beside it.  The list it emits
(`doc/complaints.md`) is the deliverable the card asked for: not "the
messages are fine" but *every complaint with its verdict*, so the next
sweep starts from what the last one decided rather than from the code.

**Why a verdict has to be declared and cannot be derived.**  Whether a
message should carry a position depends on who meets it, and nothing in
the source says who that is.  `ScoreError` is raised both for *"this
piece assigns notes to a bank it does not declare"* — which a person
wrote, in their own file, on a line — and for *"internal: the marks
stream is not a list"*, which is this program failing its own invariant
and has no line in anybody's file.  One class, one raise keyword, two
different obligations.  So the obligation is written down:

    #: complaint  author — a mistake in the piece, on the line that made it
    class ScoreError(Exception):
        ...

and where one site departs from its class, it says so on the spot:

    #: complaint  machine — the stream shape is this program's own doing
    raise ScoreError("internal: the marks stream is not a list")

## The vocabulary

Four words, and the whole point of them is *who is standing in front of
the message*:

`author`
    A person provoked it with their own file, and there is a line in
    that file to answer under.  **These must say where**, and this
    module fails the suite when one does not.
`command`
    A person provoked it by asking for something — a file that is not
    there, a bank that is not declared, a switch that wants an
    argument.  Met by a person, but about the *request* rather than
    about a line, so it lands in the status bar and that is correct.
`world`
    The machine or the world outside refused: no sound card, no
    `clang`, a file that will not open.  Nothing in anybody's file is
    wrong and a position would be a fiction.
`machine`
    This program failed its own invariant.  A person cannot provoke it
    by writing anything, and if one ever sees it, the bug is here.

And one modifier, for the case the card was written around:

`nowhere`
    An `author` complaint that deliberately names no place, because it
    is honestly about a *whole program* — exhaustiveness, coherence,
    monotonicity.  *Henri, 2026-08-18: a position is "a default, with
    the exceptions recorded", so that a later reader cannot read the
    absence as an oversight.*  The prose after the dash is the reason,
    and it is not optional.
`unplaced`
    **And the honest third state, which the card did not foresee.**  A
    place is possible, the data is at hand, and nobody has carried it
    through — which is not a decision and must not be filed as one.
    `nowhere` would launder a debt into a design, so these say
    `unplaced` and **must cite an `fixme.md` F-number**, which is what
    turns "somebody should" into something with a name.  The page
    prints them in their own section, and it is a list that is supposed
    to get shorter.

## What is checked

Three things, and each is a defect that has already happened:

1. **Every complaint has a verdict.**  A new error class, or a raise of
   one in a file that had none, arrives with no verdict and fails the
   gate — which is the thing that did not exist when the last sweep was
   scoped to type errors and nothing recorded the gap (F152, a year
   later, in a checker written after the sweep).
2. **Every `author` complaint says where**, unless it says `nowhere`
   and why, or `unplaced` and which defect owns it.  This is F152
   itself, stated as a rule.
3. **A place is a place the editor can read.**  `line 4: …` is not: the
   reader wants `at`, and a message that spells it any other way is a
   position that exists and is never used.

## What it cannot check

Whether the sentence is any good.  Four of the six properties on the
card — says what, survives formatting, speaks in the vocabulary of what
you were doing, does not fire when nobody asked — are judgements about
prose and timing, and a tool that claimed to check them would be the
second source of truth this project keeps refusing to build.  They are
what the *sweep* is for; this module is what stops the sweep's result
from rotting.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

#: The verdict words, and what each one promises.  The page prints these.
WHO = {
    "author": "a person wrote it, in their own file, on a line",
    "command": "a person asked for it — about the request, not a line",
    "world": "the machine or the world outside refused",
    "machine": "this program failed its own invariant",
}

#: `#: complaint  author, nowhere — because …`
MARKER = re.compile(
    r"^\s*#:\s*complaint\s+(?P<who>\w+)(?P<flags>(?:\s*,\s*\w+)*)\s*"
    r"(?:[—-]\s*(?P<why>.*))?$")

#: What `session._line_of` will read out of a message, and nothing else.
#: The two spellings that function knows: `(at …)`, which
#: `audiospans.in_source` re-bases on the way out, and `at line N:C`,
#: which it leaves alone because the number is already the author's.
#: The numbers themselves are usually interpolated and so are not in
#: the source text at all, which is why this looks for the word and not
#: for a digit.
PLACE = re.compile(r"\(at |\bat line ")

#: Placer helpers — the functions whose whole job is to return ` (at l:c)`.
#: A message that calls one carries a place even though the literal text
#: of the position is not in this file's source.  Each is asserted in
#: `test/test_complaints.py`, so this list cannot quietly go wrong.
PLACERS = ("_where", "at", "_at", "_of", "_span_str", "span_str",
           "_place", "_pos", "where_of", "_site")

#: And the one name a place is bound to when it is handed to a function
#: rather than fetched in one.  A convention, held by the gate: an
#: `author` complaint that interpolates `{place}` is placed, and one
#: that spells the same variable `where` is not — because `where` is
#: already taken in this tree for *which file*, and a checker that
#: guessed between them would be reading English.
CARRIER = "place"


@dataclass(frozen=True)
class Complaint:
    """One `raise`, with the verdict that governs it."""

    file: str
    line: int
    error: str
    #: The message expression as written, near enough to read.
    message: str
    who: str | None
    nowhere: bool
    why: str
    #: Where the verdict came from — `"site"`, `"function"`, `"module"`,
    #: `"class"`, or `""` when nothing governs it.
    ruled: str
    #: A place is possible and is not built; `why` names the defect.
    unplaced: bool
    #: What made this look like it carries a place, or `""`.
    place: str

    @property
    def placed(self) -> bool:
        return bool(self.place)

    @property
    def owes_a_place(self) -> bool:
        """An `author` complaint that neither says where nor accounts for it.

        The two ways of accounting are not the same thing and the
        difference is the point: `nowhere` is a decision about the
        message, `unplaced` is a debt with an F-number on it.
        """
        return (self.who == "author" and not self.placed
                and not self.nowhere and not self.unplaced)


@dataclass(frozen=True)
class Verdict:
    who: str
    nowhere: bool
    unplaced: bool
    why: str


def _verdict(text: str) -> Verdict | None:
    m = MARKER.match(text)
    if not m:
        return None
    flags = {f.strip() for f in m.group("flags").split(",") if f.strip()}
    return Verdict(m.group("who"), "nowhere" in flags, "unplaced" in flags,
                   (m.group("why") or "").strip())


def _markers(source: str) -> dict:
    """Every `#: complaint` line in a file, by the line it sits on."""
    out = {}
    for n, line in enumerate(source.split("\n"), start=1):
        got = _verdict(line)
        if got is not None:
            out[n] = got
    return out


#: The names a caught complaint is bound to in this tree, by convention.
CAUGHT = ("exc", "e", "err", "error", "caught", "failure", "said")


def _place_in(message: str) -> str:
    """What in this message expression carries a position, or `""`.

    Read off the *expression*, not the rendered string, because the
    rendered string does not exist until somebody makes the mistake.
    Three ways it can be there.

    Written out (`(at {line}:{col})`), fetched by a helper whose only
    job is to write it out — and **carried**, which is the one that
    needed thinking about.  A `raise FitsError(str(exc))` is a rename,
    not a message: whatever place the complaint it wraps had, this one
    has, and whatever place it lacked, this one lacks.  Reporting those
    as placeless would be false and reporting them as placed would be
    a claim this file cannot support, so they are reported as what they
    are, and the page prints the word.  **It is also the one honest
    loophole in the gate** — a message that interpolates a caught
    exception passes without saying where — and it is left open because
    closing it means auditing the wrapped complaint, which is a row of
    its own further up the same list.
    """
    if PLACE.search(message):
        return "written out"
    for name in PLACERS:
        if re.search(rf"\b{re.escape(name)}\(", message):
            return f"`{name}()`"
    if re.search(rf"\{{{CARRIER}\}}", message):
        return "handed in"
    for name in CAUGHT:
        # `{e!r}` is a *node* being shown, not a complaint being carried —
        # `compileC: unknown expr {e!r}` says nothing about where.
        if re.fullmatch(rf"str\({name}\)", message) or \
                re.search(rf"\{{{name}(?::[^}}!]*)?\}}", message):
            return f"carried from `{name}`"
    if re.search(r"\.join\(", message) and re.search(r"\bstr\(\w+\)|"
                                                    r"\w*(?:errors|complaints|said)\)",
                                                    message):
        return "carried from the complaints it collects"
    return ""


def _error_classes(tree: ast.Module) -> dict:
    """The error classes a module defines, with any verdict on each."""
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [ast.unparse(b) for b in node.bases]
        if not any(b.endswith(("Exception", "Error", "Warning", "Limit"))
                   for b in bases):
            continue
        out[node.name] = (node, bases)
    return out


def _raised_name(node: ast.Raise) -> str | None:
    exc = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    if isinstance(exc, ast.Name):
        return exc.id
    if isinstance(exc, ast.Attribute):
        return exc.attr
    return None


def _message_of(node: ast.Raise) -> str:
    exc = node.exc
    if not isinstance(exc, ast.Call) or not exc.args:
        return ""
    text = ast.unparse(exc.args[0])
    return re.sub(r"\s+", " ", text).strip()


def _functions(tree: ast.Module) -> list:
    """Every function body, innermost last, with its line range."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.lineno, getattr(node, "end_lineno", node.lineno),
                        node))
    return sorted(out, key=lambda t: t[1] - t[0])


def _site_marks(tree: ast.Module, marks: dict) -> set:
    """Marker lines that sit directly above a `raise` — site markers.

    **They are taken out of the function rule.**  A marker written above
    one raise governs that raise; without this it also governed every
    other raise in the same function, silently, and a `machine` beside
    one line was answering for its neighbour three lines down.
    """
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise):
            for back in (1, 2, 3):
                if node.lineno - back in marks:
                    out.add(node.lineno - back)
                    break
    return out


def _governing(line: int, marks: dict, tree: ast.Module,
               classes: dict, error: str, module_rule,
               sites: set = frozenset()) -> tuple:
    """Which verdict rules a raise at `line`, and where it came from.

    Nearest wins: a marker on the spot beats one on the function, which
    beats the file's own default, which beats the error class.  That is
    the order a reader would guess, and it is the order that makes a
    file like `audioscore.py` — a whole class of piece-level complaints
    with a handful of internal invariants among them — cost a default
    and three exceptions rather than forty-one markers.
    """
    for back in (1, 2, 3):
        got = marks.get(line - back)
        if got is not None:
            return got, "site"
    for start, end, node in _functions(tree):
        if start <= line <= end:
            inside = [n for n in marks if start <= n <= end and n not in sites]
            if inside:
                return marks[min(inside)], "function"
    if module_rule is not None:
        return module_rule, "module"
    if error in classes:
        got = _on_class(classes[error][0], marks)
        if got is not None:
            return got, "class"
    return None, ""


def _on_class(node, marks: dict):
    """The verdict written on an error class — above it or inside it.

    Above reads better and is where these ended up: the class bodies in
    this tree are `pass`, and a sentence about who meets the error wants
    to sit where a decorator would rather than under a docstring.
    """
    end = getattr(node, "end_lineno", node.lineno)
    inside = [n for n in marks if node.lineno - 3 <= n <= end]
    return marks[min(inside)] if inside else None


def _module_rule(source: str, marks: dict, tree: ast.Module):
    """A file-wide default — a `#: complaint` line at module level.

    Only one, and it must sit outside every class and function, which
    is what makes it readable as *"this whole file speaks to …"*.
    """
    spans = [(n.lineno - 3, getattr(n, "end_lineno", n.lineno))
             for n in tree.body
             if isinstance(n, (ast.ClassDef, ast.FunctionDef,
                               ast.AsyncFunctionDef))]
    for line in sorted(marks):
        if not any(a <= line <= b for a, b in spans):
            return marks[line]
    return None


def read(root=None) -> list:
    """Every complaint in the tree, with its verdict.  The whole list."""
    root = Path(root) if root is not None else Path(__file__).parent.parent
    out = []
    known = {}
    trees = {}
    for path in sorted((root / "gestate").glob("*.py")):
        source = path.read_text()
        tree = ast.parse(source)
        trees[path] = (source, tree)
        known.update(_error_classes(tree))

    #: Where each error class is defined, so a raise in another file
    #: still finds the verdict written beside the class.
    #:
    #: **Keyed by file as well as by name, because names repeat.**
    #: `MidiError` is declared twice — in `midi.py`, about the shape of a
    #: score stream, and in `audiomidi.py`, about which keyboard to
    #: listen to — and a table keyed by name alone let one file's verdict
    #: answer for the other's raises.  Which it did, silently, and the
    #: two verdicts were `machine` and `command`: as wrong as this can
    #: get without being noticed.
    home = {}
    for path, (source, tree) in trees.items():
        marks = _markers(source)
        for name, (node, _) in _error_classes(tree).items():
            home[(path.name, name)] = (node, marks)

    for path, (source, tree) in trees.items():
        marks = _markers(source)
        rule = _module_rule(source, marks, tree)
        sites = _site_marks(tree, marks)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise) or node.exc is None:
                continue
            error = _raised_name(node)
            if error is None or error not in known:
                continue        # a re-raise, or Python's own
            verdict, ruled = _governing(node.lineno, marks, tree, {}, error,
                                        rule, sites)
            if verdict is None:
                # This file's own class first; then a homonym elsewhere,
                # but only if there is exactly one — two would be a guess.
                elsewhere = [k for k in home if k[1] == error]
                key = ((path.name, error) if (path.name, error) in home
                       else elsewhere[0] if len(elsewhere) == 1 else None)
                if key is not None:
                    got = _on_class(*home[key])
                    if got is not None:
                        verdict, ruled = got, "class"
            message = _message_of(node)
            out.append(Complaint(
                file=path.name, line=node.lineno, error=error,
                message=message,
                who=verdict.who if verdict else None,
                nowhere=bool(verdict and verdict.nowhere),
                unplaced=bool(verdict and verdict.unplaced),
                why=verdict.why if verdict else "",
                ruled=ruled, place=_place_in(message)))
    return sorted(out, key=lambda c: (c.file, c.line))


# ── The verdicts, read back ─────────────────────────────────────────────────


def unverdicted(complaints=None) -> list:
    """Complaints nobody has ruled on — what the gate refuses."""
    return [c for c in (complaints if complaints is not None else read())
            if c.who is None or c.who not in WHO]


def owing_a_place(complaints=None) -> list:
    """`author` complaints that neither say where nor say why not."""
    return [c for c in (complaints if complaints is not None else read())
            if c.owes_a_place]


def unexplained(complaints=None) -> list:
    """A `nowhere` with no reason after it is the oversight it claims not to be."""
    return [c for c in (complaints if complaints is not None else read())
            if c.nowhere and not c.why]


#: An `unplaced` says a defect owns the debt, and this is what proves it.
OWNER = re.compile(r"\bF\d+\b")


def unowned(complaints=None) -> list:
    """An `unplaced` that names no defect — a debt with nobody's name on it.

    Without this the third state becomes the softest of the three and
    everything drifts into it, which is the failure mode of every
    "known issue" list ever kept.
    """
    return [c for c in (complaints if complaints is not None else read())
            if c.unplaced and not OWNER.search(c.why)]


# ── The page ────────────────────────────────────────────────────────────────


def _short(message: str, width: int = 96) -> str:
    text = message
    if text.startswith(("f'", 'f"')):
        text = text[1:]
    if len(text) > width:
        text = text[:width - 1] + "…"
    return text.replace("|", "\\|")


def render(complaints=None) -> str:
    """`doc/complaints.md` — the list, and the counts above it."""
    cs = complaints if complaints is not None else read()
    lines = ["# Every complaint, and what it is for", "",
             # **The marker closes on its own line**, because
             # `test_doc_commands.py` reads every `python -m …` in
             # `doc/*.md` and takes the words after it as flags — so a
             # `-->` on the same line is a flag nobody has.  It caught
             # this the first time this page was scanned, which is the
             # check working.
             "<!--", "Generated by `python -m gestate.complaints`.",
             "Do not edit by hand.", "-->", ""]
    lines += [
        "The sweep `card:error-messages.md` asked for, kept as a list "
        "rather than as a memory.  Each row is one `raise` in "
        "`gestate/`, and the verdict beside it was written next to that "
        "raise — on the site, the function, the file or the error class, "
        "whichever is nearest.",
        "",
        "**What the words mean.**",
        "",
        "| verdict | who is standing in front of it | owes a place |",
        "|---|---|---|",
    ]
    for who, prose in WHO.items():
        owes = "**yes**" if who == "author" else "no"
        lines.append(f"| `{who}` | {prose} | {owes} |")
    lines += [
        "",
        "An `author` complaint may say `nowhere` instead, and then the "
        "reason is printed with it: the message is about a whole "
        "program — exhaustiveness, coherence, monotonicity — and a line "
        "number would be a fiction.  *That is a decision, not a gap, "
        "which is the whole reason this file exists.*",
        "",
    ]

    counts = {}
    for c in cs:
        counts[c.who or "—"] = counts.get(c.who or "—", 0) + 1
    total = len(cs)
    placed = sum(1 for c in cs if c.placed)
    nowhere = sum(1 for c in cs if c.nowhere)
    lines += [
        "## The count", "",
        f"**{total} complaints**, in {len({c.file for c in cs})} files.",
        "",
        "| | |", "|---|---|",
    ]
    for who in list(WHO) + ["—"]:
        if counts.get(who):
            lines.append(f"| `{who}` | {counts[who]} |")
    lines += [
        f"| say where | {placed} |",
        f"| say `nowhere`, on purpose | {nowhere} |",
        f"| `unplaced`, with a defect that owns it | "
        f"{sum(1 for c in cs if c.unplaced)} |",
        "",
    ]

    owed = [c for c in cs if c.owes_a_place]
    if owed:
        lines += ["## Owing a place", "",
                  "An `author` complaint that neither says where nor says "
                  "why not.  **The gate fails while this section exists.**",
                  "", "| where | error | message |", "|---|---|---|"]
        for c in owed:
            lines.append(f"| `{c.file}:{c.line}` | `{c.error}` | "
                         f"{_short(c.message)} |")
        lines.append("")

    debt = [c for c in cs if c.unplaced and not c.placed]
    if debt:
        lines += ["## A place that could exist, and does not", "",
                  "The data is at hand and nobody has carried it through.  "
                  "**These are debts, not decisions** — each names the defect "
                  "that owns it, and this section is supposed to get shorter.",
                  "", "| where | error | owed to |", "|---|---|---|"]
        for c in debt:
            lines.append(f"| `{c.file}:{c.line}` | `{c.error}` | {c.why} |")
        lines.append("")

    said = [c for c in cs if c.nowhere and not c.placed]
    if said:
        lines += ["## No place, on purpose", "",
                  "The exceptions, with their reasons — so that a later "
                  "reader cannot mistake one for an oversight.",
                  "", "| where | error | why |", "|---|---|---|"]
        for c in said:
            lines.append(f"| `{c.file}:{c.line}` | `{c.error}` | {c.why} |")
        lines.append("")

    lines += ["## Every complaint", ""]
    for name in sorted({c.file for c in cs}):
        here = [c for c in cs if c.file == name]
        lines += [f"### `{name}`", ""]
        rules = {c.why for c in here if c.ruled in ("module", "class") and c.why}
        for why in sorted(rules):
            lines.append(f"*{why}*")
            lines.append("")
        lines += ["| line | error | verdict | says where | message |",
                  "|---|---|---|---|---|"]
        for c in here:
            place = c.place or ("*nowhere, on purpose*" if c.nowhere
                                else f"*unplaced — {c.why}*" if c.unplaced
                                else "—")
            lines.append(f"| {c.line} | `{c.error}` | `{c.who}` | {place} | "
                         f"{_short(c.message)} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def page(root=None) -> Path:
    root = Path(root) if root is not None else Path(__file__).parent.parent
    return root / "doc" / "complaints.md"


def stale(root=None) -> bool:
    """Is the page behind the source it is derived from?"""
    target = page(root)
    return not target.exists() or target.read_text() != render(read(root))


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.complaints",
        description="List every complaint in the tree, with its verdict.")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit non-zero if the page is behind")
    args = ap.parse_args(argv)

    cs = read()
    if args.check:
        if stale():
            print("doc/complaints.md is behind gestate/ — "
                  "run `python -m gestate.complaints`")
            return 1
        print(f"doc/complaints.md is current — {len(cs)} complaints")
        return 0

    target = page()
    target.write_text(render(cs))
    missing, owed = unverdicted(cs), owing_a_place(cs)
    print(f"{target}: {len(cs)} complaints")
    if missing:
        print(f"  {len(missing)} with no verdict")
    if owed:
        print(f"  {len(owed)} owing a place")
    for c in unexplained(cs):
        print(f"  {c.file}:{c.line} says `nowhere` and no reason")
    for c in unowned(cs):
        print(f"  {c.file}:{c.line} says `unplaced` and names no defect")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
