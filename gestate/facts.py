"""A document's kinds, read out of the file that declares them.

**A document is facts** — `gestate/facts.ges` is the vocabulary and a
document's own `.ges` declares `kinds : List Kind`.  This loads that
declaration the way `gestate/charts.py` loads a chart: the library in
front of the file, compiled once by the reference G-machine, and the
value read back as plain Python.

`card:gui-is-difficult.md` §"The document, decided" is the argument and
Henri's, 2026-09-09.  **Nothing here parses or writes a document yet.**
`gestate/notes.py` still does both, carrying the same facts by hand
since the format existed; `test/test_facts.py` holds the two to each
other on `examples/audio/arc.notes`, so the declaration is checked
before anything is asked to trust it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .charts import ChartError, Terms

HERE = Path(__file__).parent
LIBRARY = HERE / "facts.ges"


#: complaint  author, nowhere — a document's `.ges` that declares no kinds, or one whose kinds are not the shape the library gives: the fault is a name absent from a file, and an absent name has no line
class FactsError(Exception):
    """A kinds declaration that could not be read."""


@dataclass(frozen=True)
class Field:
    """One field of one kind: what it is called, how its one token is
    read, and whether a record has to carry it."""
    name: str
    value: str                      # "Word" | "Number" | "Names"
    need: str                       # "Must" | "May"


@dataclass(frozen=True)
class Kind:
    """One kind of fact, as its file declares it.

    `shape` is `("Named",)`, `("Bare", field)` or `("Headed", field)`;
    `order` is a list of `("By", field)` and
    `("Along", field, kind, field)`.  An empty `key` means at most one
    record of this kind in a document, and an empty `order` means the
    order they were written in — `facts.ges` says why for both.
    """
    name: str
    shape: tuple
    fields: tuple
    key: tuple
    order: tuple

    @property
    def required(self) -> tuple:
        """The fields a record must carry, in declaration order — what a
        refusal names, derived rather than written a second time."""
        return tuple(f.name for f in self.fields if f.need == "Must")

    @property
    def named(self) -> tuple:
        """The fields written as `key value` pairs.  A `Headed` kind's
        bare first token is **not** one of these: it is positional by
        declaration, which is the one place `spec/drawnscores.md` gate
        two allows a position to mean something."""
        return tuple(f.name for f in self.fields)

    def field(self, name: str) -> Field | None:
        return next((f for f in self.fields if f.name == name), None)


def _text(term) -> str:
    """A `Text` — `List Char`, and a `Char` is its code point, which is
    how `gui.py` reads one too."""
    if isinstance(term, str):
        return term
    if not isinstance(term, list):
        raise FactsError(f"not a text: {term!r}")
    return "".join(chr(c) if isinstance(c, int) else "?" for c in term)


def _shape(term) -> tuple:
    head, *args = term
    if head == "Named":
        return ("Named",)
    if head in ("Bare", "Headed"):
        return (head, _text(args[0]))
    raise FactsError(f"`{head}` is not a shape")


def _field(term) -> Field:
    head, name, value, need = term
    if head != "Field":
        raise FactsError(f"`{head}` is not a field")
    return Field(_text(name), value[0], need[0])


def _sort(term) -> tuple:
    head, *args = term
    if head == "By":
        return ("By", _text(args[0]))
    if head == "Along":
        return ("Along", _text(args[0]), _text(args[1]), _text(args[2]))
    raise FactsError(f"`{head}` is not an order")


def _kind(term) -> Kind:
    head, name, shape, fields, key, order = term
    if head != "Kind":
        raise FactsError(f"`{head}` is not a kind")
    return Kind(name=_text(name), shape=_shape(shape),
                fields=tuple(_field(f) for f in fields),
                key=tuple(_text(k) for k in key),
                order=tuple(_sort(o) for o in order))


def sort_key(kind: Kind, record: dict, along=None) -> tuple:
    """Where a record stands in its kind's own order.

    **The first thing derived from a declaration rather than written a
    second time.**  `record` is the record's fields, already read — a
    number as an `int`, a word as a `str`.  `along(kind, field, record)`
    answers the sequence an `Along` term orders by, which is the one
    case that reads another record: the voice order is the section's
    own, not alphabetical, because that is the order the roll stacks
    them in.

    A value absent from that sequence sorts last rather than raising:
    an unknown voice is a fact about the file, and refusing it belongs
    to the parser, which names the line.
    """
    out = []
    for term in kind.order:
        if term[0] == "By":
            out.append(record[term[1]])
            continue
        _along, field, other, ofield = term
        if along is None:
            raise FactsError(
                f"`{kind.name}` orders along `{other} {ofield}` and nothing "
                f"was given to look it up in")
        sequence = list(along(other, ofield, record))
        value = record[field]
        out.append(sequence.index(value) if value in sequence else len(sequence))
    return tuple(out)


class Document:
    """The kinds one document's file declares, read once per edit."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.terms = Terms(self.path, LIBRARY)
        try:
            declared = self.terms.declared("kinds")
        except ChartError as why:
            raise FactsError(str(why)) from None
        self.kinds = tuple(_kind(k) for k in self.terms.read(declared))

    def __getitem__(self, name: str) -> Kind:
        found = self.kind(name)
        if found is None:
            raise FactsError(
                f"{self.path.name} declares no kind `{name}`; it has "
                + ", ".join(f"`{k.name}`" for k in self.kinds))
        return found

    def kind(self, name: str) -> Kind | None:
        return next((k for k in self.kinds if k.name == name), None)

    @property
    def names(self) -> tuple:
        return tuple(k.name for k in self.kinds)


_LOADED: dict = {}


def load(name: str = "notes") -> Document:
    """The kinds of `gestate/<name>.ges`, compiled once per edit of
    either file — `charts.load`'s shape, and for its reason: the compile
    is a fifth of a second and the answer never changes while the files
    do not."""
    path = HERE / f"{name}.ges"
    stamp = (path.stat().st_mtime_ns, LIBRARY.stat().st_mtime_ns)
    found = _LOADED.get(name)
    if found is None or found[0] != stamp:
        found = _LOADED[name] = (stamp, Document(path))
    return found[1]
