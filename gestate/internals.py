"""`internal`, enforced — the half of a library that is not yours to call.

    python -m gestate.internals examples/audio/quartet.ges

A library file may write `internal` on a line of its own, and everything
below that line is machinery: `svfSolve`, `ladderTail`, `fmPhasesWith` — the
insides of a filter, not a thing anybody builds a synth out of.  The marker
parses (`syntax/ast.py`'s `VInternal`) and `reference.py` sorts on it.  This
module is what makes it *mean* something.

**Why it is a separate pass rather than part of the compiler.**  The
question "did this reference cross a file boundary" cannot be asked of the
program the compiler sees, because there are no files in it: every audio
backend hands the front end one text with four libraries concatenated on
the front (`audio.assemble`), so `svfSolve` in a synth and `svfSolve` in
`synth.ges` are the same global at the same scope and nothing distinguishes
them.  The boundaries exist only in the strings that were concatenated, and
this reads them back out of those.

**What is checked is what the author wrote**, after `voices` expansion and
before the preludes go on — so a bank's voice is checked like any other
definition and a library's own use of its own machinery is not a violation.

**The suggestion is read out of the library, not declared in it.**  The
public face of a private name is whichever public definition *calls* it —
`svfLow` is used by `lowpassSvf` and `sweepSvf`, `adsrOf` by `adsr` —
and that is a fact the file already contains.  So an error can say what to
reach for instead without anyone maintaining a table of it, and a wrapper
that stops calling its machinery stops being offered for it.
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .reference import LIBRARIES as _PAGES
from .reference import entries_of

#: The library files, in the order they are concatenated.  `prelude.ges` is
#: merged as a module rather than prepended, and is in scope either way.
LIBRARIES = tuple(name for name, _title, _when in _PAGES)


class InternalError(Exception):
    """A program named something a library keeps to itself."""


@dataclass(frozen=True)
class Use:
    """One reference across the boundary, and everything the message needs."""

    name: str
    #: Which library keeps it private.
    library: str
    #: 1-based, in the text that was checked — the author's own file.
    line: int
    column: int
    #: The `# ── … ──` heading it lives under, or `""`.
    section: str
    #: The public definitions that use it — its faces.
    instead: tuple

    def __str__(self) -> str:
        where = f"line {self.line}"
        out = (f"{where}: `{self.name}` is internal to `{self.library}` "
               f"and cannot be named from here")
        if self.instead:
            names = ", ".join(f"`{n}`" for n in self.instead)
            out += f"\n    reach for one of these instead: {names}"
        elif self.section:
            out += (f"\n    it is machinery of the `{self.section}` section, "
                    "with no public face")
        return out


# ── Reading the libraries ───────────────────────────────────────────────────


@lru_cache(maxsize=None)
def _split(library: str) -> tuple:
    """`({private name: section}, {private name: the public names using it})`.

    A data declaration contributes its **constructors** as well as its type
    name: `SvfIn` is how a caller would reach a private filter, and a
    private type whose constructor stayed public would be a door left open
    beside a locked one.

    **The face of a private name is whatever public definition calls it**,
    read out of the file rather than declared anywhere.  `svfLow` is used
    by `lowpassSvf` and `sweepSvf`; `adsrOf` by `adsr`.  That is a
    truer answer than the section heading — which says only where a name
    lives — and it is one nobody has to maintain, because a wrapper that
    stops calling its machinery stops being offered for it.
    """
    from .audio import library_text

    source = library_text(library)
    lines = source.split("\n")
    entries = entries_of(source)

    private: dict = {}
    for entry in entries:
        if not entry.internal:
            continue
        for name in [entry.name] + [_head(a) for a in entry.alternatives]:
            if name:
                private.setdefault(name, entry.section)

    faces: dict = {name: [] for name in private}
    for entry, following in zip(entries, entries[1:] + [None]):
        if entry.internal:
            continue
        stop = len(lines) if following is None else following.line - 1
        body = lines[entry.line - 1:stop]
        # **An instance offers its methods, not its own name.**  `showNat`
        # is reached only from `instance Show Int`, and "reach for `Show
        # Int` instead" is not a thing anybody can write — `show` is.  A
        # type is likewise not something to reach for in place of a
        # function, so only these two kinds contribute.
        if entry.kind == "instance":
            offers = _methods_in(body)
        elif entry.kind in ("value", "operator"):
            offers = [entry.name]
        else:
            continue
        for word in _words(body):
            for offer in offers:
                if word in faces and offer not in faces[word]:
                    faces[word].append(offer)

    # A private *type* is usually named only in the signatures of other
    # private functions, so nothing public calls it and the honest answer
    # is empty — which is not a useful thing to tell somebody who has just
    # written `Ladder`.  So a name with no face of its own inherits the
    # faces of its section, which for `Ladder` is every filter there is.
    direct = {name: tuple(found) for name, found in faces.items()}
    for name, section in private.items():
        if direct[name]:
            continue
        faces[name] = [face for other, others_section in private.items()
                       if others_section == section
                       for face in direct[other]]
        faces[name] = list(dict.fromkeys(faces[name]))
    return (private, {k: tuple(v) for k, v in faces.items()})


#: An identifier, as the tokenizer spells one.
_WORD = re.compile(r"[A-Za-z_][\w']*")

#: `    show n = …` or `    (==) a b = …` — a method definition inside an
#: instance body, which is an indented name followed by its equation.
_METHOD = re.compile(r"^\s+(?:\((\S+?)\)|([A-Za-z_][\w']*))[^=]*=")


def _methods_in(lines) -> list:
    """The method names an instance body defines, in order."""
    out: list = []
    for line in lines:
        found = _METHOD.match(line.split("#")[0])
        if found:
            name = found.group(1) or found.group(2)
            if name not in out:
                out.append(name)
    return out


def _words(lines) -> set:
    """Every identifier in a run of source, comments left out.

    The doc block of the *next* declaration falls inside a definition's
    line range, and a comment that names a private function would otherwise
    make its neighbour look like the face of it.
    """
    out: set = set()
    for line in lines:
        text = line.split("#")[0]
        out.update(_WORD.findall(text))
    return out


def _head(alternative: str) -> str:
    """`Svf Float Float …` — the constructor a data alternative declares."""
    parts = alternative.split()
    return parts[0] if parts else ""


def private_names(library: str) -> frozenset:
    """Every name one library keeps to itself."""
    return frozenset(_split(library)[0])


def libraries_in_scope(source: str) -> tuple:
    """Which libraries this program is compiled against.

    Derived from the very text `audio.preludes` chose rather than by asking
    the same questions again: two answers to "is `synth.ges` in scope" is
    two answers to "is `svfSolve` a violation", and the compiler would side
    with whichever was wrong.  `prelude.ges` is always in scope and is
    never in that text, because it is merged as a module.
    """
    from .audio import library_text, preludes

    head = preludes(source)
    out = ["prelude.ges"]
    for name in LIBRARIES:
        if name == "prelude.ges":
            continue
        # `library_text`, not a fresh read: the comparison is against what
        # `preludes` returned, and reading the file again is a second
        # answer to the same question.  When the two disagree the library
        # is judged out of scope and enforcement silently switches off —
        # see `audio.library_text` for how that is reachable.
        text = library_text(name)
        if text and text in head:
            out.append(name)
    if _has_score(source) and "music.ges" not in out:
        out.append("music.ges")
    return tuple(out)


def _has_score(source: str) -> bool:
    from .audioperform import has_score

    return has_score(source)


# ── Reading the program ─────────────────────────────────────────────────────


def mentions(text: str) -> dict:
    """`{name: (line, column)}` — every global the text names, once each.

    Free of the text's own definitions: a name it binds anywhere — a
    parameter, a `let`, a pattern variable, a top-level equation — is its
    own and is subtracted wholesale rather than scope by scope.  That is
    deliberately the loose direction.  Being wrong here means *missing* a
    violation in a program that happens to reuse a library's private name
    as a local, which costs nothing; the precise version would sometimes
    reject a program that is fine, which is the failure a check like this
    cannot afford.

    Positions are 1-based lines, as an editor counts them; the tokenizer
    counts from 0.
    """
    from .prelude import _parsed

    module = _parsed(text)
    used: dict = {}
    bound: set = set()
    _walk(module, used, bound)
    return {name: where for name, where in used.items() if name not in bound}


#: The AST fields that *bind* rather than mention.  Everything else is
#: walked generically, so a new node type is checked the day it is added
#: rather than the day somebody remembers this file.
_BINDING = {
    "PVar": ("name",),
    "VSCEqn": ("name",),
    "VSCDecl": ("name",),
    "VSig": ("name",),
    "VImplicit": ("name",),
    "VTypeDecl": ("name", "params"),
    "VCtor": ("name",),
    "VTypeAlias": ("name", "params"),
    "VClass": ("name", "params"),
    "VKind": ("name",),
    "VFixity": ("op",),
}

#: Fields naming something the program *refers to*, on nodes where the name
#: is a plain string rather than a `VWord`.
_MENTION = {
    "VWord": ("value",),
    "VConId": ("value",),
    "PCon": ("name",),
    "VInfix": ("op",),
    "VPrefix": ("op",),
    "VPostfix": ("op",),
    "VInstance": ("name",),
    "VProj": (),
}


def _position(node) -> tuple:
    span = getattr(node, "span", None)
    start = getattr(span, "start", None)
    if start is None:
        return (0, 0)
    return (start.line + 1, start.col)


def _walk(node, used: dict, bound: set) -> None:
    """Every name in the tree, sorted into mentioned and bound.

    Generic over the dataclasses rather than a method per node: the AST has
    some forty node types and a visitor that had to name each one would be
    a check that silently stops covering the language whenever it grows.
    """
    if isinstance(node, str):
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            _walk(item, used, bound)
        return
    if not dataclasses.is_dataclass(node):
        return

    kind = type(node).__name__
    for name in _BINDING.get(kind, ()):
        value = getattr(node, name, None)
        for text in (value if isinstance(value, list) else [value]):
            if isinstance(text, str):
                bound.add(text)
    for name in _MENTION.get(kind, ()):
        value = getattr(node, name, None)
        if isinstance(value, str):
            used.setdefault(value, _position(node))

    # A `let` or `given` binds `(name, value)` pairs, and the name half is
    # not a node — walking the pair generically would miss it entirely.
    for pairs in (getattr(node, "bindings", None),):
        if isinstance(pairs, list):
            for pair in pairs:
                if isinstance(pair, tuple) and pair and isinstance(pair[0], str):
                    bound.add(pair[0])

    # An operator phrase carries its operators as bare strings between the
    # operands, so they are mentions with only the phrase's own position.
    if kind == "VOpPhrase":
        for atom in node.atoms:
            if isinstance(atom, str) and atom != "EOI":
                used.setdefault(atom, _position(node))

    for field in dataclasses.fields(node):
        if field.name == "span":
            continue
        _walk(getattr(node, field.name), used, bound)


# ── The check ───────────────────────────────────────────────────────────────


def expanded(source: str) -> str:
    """The author's text with its `voices` banks rewritten into declarations.

    `voices lead 6 reed : Sig Float` is not gestate syntax — it is the one
    thing in a program a parser cannot read — and a bank's voice is exactly
    where a synth reaches for machinery, so skipping it would leave the
    check blind to the programs it most needs to see.

    An expansion that *fails* is not this module's error to report: the
    assembly is about to fail on the same text with a message about banks,
    which is the true one.  So the raw source is checked instead, and what
    that costs is at worst a violation missed inside a program that is
    already broken.
    """
    from .audio import preludes
    from .audiovoices import expand

    try:
        return expand(source, preludes(source))
    except Exception:                                       # noqa: BLE001
        return source


def check(source: str, libraries=None, text: str | None = None) -> list:
    """Every internal name this program names, in the order it names them.

    `source` is the author's own text — not an assembly, and not a library.
    `text` is that same program with its banks already expanded, for the
    caller that has it: `audio.assemble` expands on the way past and a
    second expansion there would be a parse per bank per keystroke.
    """
    if libraries is None:
        libraries = libraries_in_scope(source)
    named = mentions(expanded(source) if text is None else text)
    # **Only the author's own lines.**  `voices` expansion blanks the bank
    # declarations in place and *appends* the generated program — a summing
    # fold, a `FromMIDI` bridge, a record per bank — and that generated
    # code reaches for library machinery quite properly: it is the library
    # writing, not the author.  `addSig` in a bank's sum is the same
    # `addSig` that `Num (Sig Float)` is built from.
    #
    # The author's text keeps its line numbers through the expansion, which
    # is what makes the range a sound test rather than a guess: a voice
    # function is an ordinary declaration and stays inside it, so nothing a
    # person wrote escapes the check.
    authored = len(source.splitlines())
    named = {n: (line, col) for n, (line, col) in named.items()
             if line <= authored}
    found = []
    for library in libraries:
        private, faces = _split(library)
        for name, (line, column) in named.items():
            if name not in private:
                continue
            found.append(Use(name=name, library=library, line=line,
                             column=column, section=private[name],
                             instead=faces.get(name, ())))
    return sorted(found, key=lambda u: (u.line, u.column, u.name))


def enforce(source: str, libraries=None, path: str | None = None,
            text: str | None = None) -> None:
    """`check`, as an exception — what an assembly calls.

    Every violation at once, because they come in families: a program that
    hand-folds an envelope names six private functions and being told about
    them one recompile at a time is six times the work of being told once.
    """
    found = check(source, libraries, text)
    if not found:
        return
    where = f"{path}: " if path else ""
    plural = "" if len(found) == 1 else "s"
    raise InternalError(
        f"{where}{len(found)} reference{plural} to library internals\n\n"
        + "\n".join("  " + str(use) for use in found)
        + "\n\nThese are a library's own machinery.  `doc/ref/` lists them "
          "under Internals, with the public face of each section beside "
          "them.")


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    """`python -m gestate.internals <file>…` — which programs still reach in.

    Worth having beside the enforcement: while a library is being divided
    the useful question is *how much* is left rather than whether anything
    is, and a list across several files answers it in one run.
    """
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        prog="python -m gestate.internals",
        description="Report references to library internals.")
    ap.add_argument("file", nargs="+")
    ap.add_argument("--count", action="store_true",
                    help="one line per file: how many, not which")
    args = ap.parse_args(argv)

    total = 0
    missing = 0
    for name in args.file:
        # Reading is inside the guard too.  This takes a *list* of files, so
        # one that is not there used to end the run with a traceback and
        # take the report on every later file with it.
        try:
            source = Path(name).read_text()
            found = check(source)
        except OSError as exc:
            print(f"gestate: {name}: {exc.strerror}", file=sys.stderr)
            missing += 1
            continue
        except Exception as exc:                   # noqa: BLE001 — a CLI
            print(f"{name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        total += len(found)
        if args.count:
            print(f"  {len(found):>3}  {name}")
            continue
        if not found:
            continue
        print(f"{name}:")
        for use in found:
            print("  " + str(use).replace("\n", "\n  "))
    return 1 if (total or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
