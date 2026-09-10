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

import re
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
    read, whether a record has to carry it, and the domain its value
    is drawn from — `None` when the declaration gives no bound."""
    name: str
    value: str                      # "Word" | "Number" | "Names"
    need: str                       # "Must" | "May"
    domain: tuple | None = None     # ("Range", lo, hi) | ("AtLeast", n) | ("OneOf", names) | ("Each", names)

    def outside(self, value) -> str | None:
        """Why `value` — already typed — is not in this field's domain,
        or `None`.  **The refusal, derived from the bound** rather than
        written per field; the sentence names the field and the bound
        and nothing a parser would have to remember."""
        if self.domain is None:
            return None
        head = self.domain[0]
        if head == "Range":
            _h, lo, hi = self.domain
            if not lo <= value <= hi:
                return f"`{self.name} {value}` is not within {lo}–{hi}"
        elif head == "AtLeast":
            if value < self.domain[1]:
                return f"`{self.name} {value}` is less than {self.domain[1]}"
        elif head == "OneOf":
            if value not in self.domain[1]:
                return (f"`{self.name} {value}` is not one of "
                        + " ".join(self.domain[1]))
        elif head == "Each":
            for one in value:
                if one not in self.domain[1]:
                    return (f"`{self.name} {one}` is not one of "
                            + " ".join(self.domain[1]))
        return None


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

    def __post_init__(self):
        """**The three lookups, made once.**  A kind is read for every
        field of every record — 2,913 times per read of `arc.notes` —
        and each was a scan over the field list, which is the same
        query-per-row cost `Relation.by` exists for (`tools/notecost.py`,
        2026-09-10).  Frozen, so the maps go in by the dataclass's own
        back door, and nothing outside can tell."""
        object.__setattr__(self, "_at", {f.name: f for f in self.fields})
        object.__setattr__(self, "_required",
                           tuple(f.name for f in self.fields if f.need == "Must"))
        object.__setattr__(self, "_named", tuple(f.name for f in self.fields))

    @property
    def required(self) -> tuple:
        """The fields a record must carry, in declaration order — what a
        refusal names, derived rather than written a second time."""
        return self._required

    @property
    def named(self) -> tuple:
        """The fields written as `key value` pairs.  A `Headed` kind's
        bare first token is **not** one of these: it is positional by
        declaration, which is the one place `spec/drawnscores.md` gate
        two allows a position to mean something."""
        return self._named

    def field(self, name: str) -> Field | None:
        return self._at.get(name)

    @property
    def refers(self) -> tuple:
        """The references a record of this kind must resolve — **derived
        from its order, not declared a second time.**

        `card:relational-model.md` §"The sketch", Q2: an `Among field
        kind` cannot order a record by where the one it names stands
        unless that one exists, and an `Along field kind list` cannot
        order a value along a list it is not in.  So the two sorts that
        read another record *are* the two foreign keys, and a
        declaration that said them twice would have two things to
        disagree.  `("Refer", field, kind)` — the field names a key of
        `kind`; `("Within", field, kind, list)` — the field is one of
        the names in the `list` field of the `kind` record this record
        refers to.
        """
        out = []
        for term in self.order:
            if term[0] == "Among":
                out.append(("Refer", term[1], term[2]))
            elif term[0] == "Along":
                out.append(("Within", term[1], term[2], term[3]))
        return tuple(out)


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


#: A domain's token shape: what the line carries, under the bound.
_SHAPE = {"Range": "Number", "AtLeast": "Number", "OneOf": "Word", "Each": "Names"}


def _field(term) -> Field:
    head, name, value, need = term
    if head != "Field":
        raise FactsError(f"`{head}` is not a field")
    form, *args = value
    if form in ("Word", "Number", "Names"):
        return Field(_text(name), form, need[0])
    if form not in _SHAPE:
        raise FactsError(f"`{form}` is not a value")
    if form in ("OneOf", "Each"):
        domain = (form, tuple(_text(a) for a in args[0]))
    else:
        domain = (form, *args)
    return Field(_text(name), _SHAPE[form], need[0], domain)


def _sort(term) -> tuple:
    head, *args = term
    if head == "By":
        return ("By", _text(args[0]))
    if head == "Along":
        return ("Along", _text(args[0]), _text(args[1]), _text(args[2]))
    if head == "Among":
        return ("Among", _text(args[0]), _text(args[1]))
    raise FactsError(f"`{head}` is not an order")


def _kind(term) -> Kind:
    head, name, shape, fields, key, order = term
    if head != "Kind":
        raise FactsError(f"`{head}` is not a kind")
    return Kind(name=_text(name), shape=_shape(shape),
                fields=tuple(_field(f) for f in fields),
                key=tuple(_text(k) for k in key),
                order=tuple(_sort(o) for o in order))


def sort_key(kind: Kind, record: dict, along=None, among=None) -> tuple:
    """Where a record stands in its kind's own order.

    **What the canonical writer sorts by, derived rather than written a
    second time.**  `record` is the record's fields, already read — a
    number as an `int`, a word as a `str`.

    Two of the three terms read *another* record, and each takes a
    callback rather than a document, so this stays a function of the
    declaration and nothing else:

    * `along(kind, field, record)` — the sequence an `Along` orders by.
      The voice order is the section's own, not alphabetical, because
      that is the order the roll stacks them in.
    * `among(kind, value)` — where the record a reference names stands
      among its own kind.  A note's section sorts by the section's place
      in the file, because a section is put where the author put it.

    A value absent from an `Along` sequence sorts last rather than
    raising: an unknown voice is a fact about the file, and refusing it
    belongs to the parser, which names the line.
    """
    out = []
    for term in kind.order:
        if term[0] == "By":
            out.append(record[term[1]])
        elif term[0] == "Along":
            _t, field, other, ofield = term
            if along is None:
                raise FactsError(
                    f"`{kind.name}` orders along `{other} {ofield}` and "
                    f"nothing was given to look it up in")
            sequence = list(along(other, ofield, record))
            value = record[field]
            out.append(sequence.index(value) if value in sequence
                       else len(sequence))
        else:
            _t, field, other = term
            if among is None:
                raise FactsError(
                    f"`{kind.name}` orders among `{other}` and nothing was "
                    f"given to find it in")
            out.append(among(other, record[field]))
    return tuple(out)


# ── What a reader gets ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Relation:
    """A heading and a set of rows — Codd's structure, and nothing else.

    Every value in a row is one `int` or one `str`: no list, no tuple,
    no bitmask, no line number.  That is the information principle,
    and `test/test_relations.py` measures it.
    """
    heading: tuple
    rows: frozenset

    def column(self, name: str) -> int:
        return self.heading.index(name)

    def project(self, *names: str) -> set:
        at = tuple(self.column(n) for n in names)
        return {tuple(row[i] for i in at) for row in self.rows}

    def by(self, *names: str) -> dict:
        """`{those columns: [row as a dict, …]}` — **the index a reader
        builds once** instead of scanning per row.

        A relation is a set and a scan is fine at a few hundred rows;
        the cost that bites is a scan *per row of another relation*,
        which is O(n·m) and is the shape that has killed relational
        UIs (guest fable, 2026-09-10).  So a reader that joins builds
        this first, the way an engine builds a hash for a join.
        """
        at = tuple(self.column(n) for n in names)
        out: dict = {}
        for row in self.rows:
            out.setdefault(tuple(row[i] for i in at), []).append(
                dict(zip(self.heading, row)))
        return out

    def where(self, **equal) -> list[dict]:
        """The rows whose named columns equal the values given, each as
        `{column: value}` — a select and nothing more, so a reader reads
        like a query and never by position."""
        at = [(self.column(n), v) for n, v in equal.items()]
        return [dict(zip(self.heading, row)) for row in self.rows
                if all(row[i] == v for i, v in at)]


def _typed(kind: Kind, record: dict) -> dict:
    """A record's values as the declaration reads them — a number an
    `int`, a word a `str`, names a tuple of `str`, an absent `May`
    field `None`.  Takes tokens or already-typed values, so both roads
    to a relation pass through one converter."""
    out = {}
    for f in kind.fields:
        value = record.get(f.name)
        if value is None:
            out[f.name] = None
        elif f.value == "Number":
            out[f.name] = int(value)
        elif f.value == "Names":
            out[f.name] = (tuple(v for v in value.split(",") if v)
                           if isinstance(value, str) else tuple(value))
        else:
            out[f.name] = str(value)
    if kind.shape[0] == "Headed":
        out[kind.shape[1]] = str(record[kind.shape[1]])
    return out


def relations(kind: Kind, records) -> dict:
    """The relations one kind's records are, **derived by one rule from
    the declaration** — `card:relational-model.md` Q6.

    The key plus every required scalar field is the base relation,
    under the kind's name.  Each `May` field is a relation of its own,
    `kind.field`, so that absence is no row and never a null.  Each
    `Names` field is a relation of its own with a rank, so that a list
    in a value has a row to hang a second fact on (scar 4) and the
    order the author wrote is a fact and not a position.  Both are
    headed by the key and then `value`, or `rank` and `value`.
    """
    key = kind.key
    base_cols = list(key) + [f.name for f in kind.fields
                             if f.need == "Must" and f.value != "Names"
                             and f.name not in key]
    base: set = set()
    split: dict[str, set] = {}
    for raw in records:
        record = _typed(kind, raw)
        k = tuple(record[c] for c in key)
        base.add(tuple(record[c] for c in base_cols))
        for f in kind.fields:
            if f.name in key or (f.need == "Must" and f.value != "Names"):
                continue
            value = record[f.name]
            if value is None:
                continue
            rows = split.setdefault(f.name, set())
            if f.value == "Names":
                for rank, name in enumerate(value, start=1):
                    rows.add(k + (rank, name))
            else:
                rows.add(k + (value,))
    out = {kind.name: Relation(tuple(base_cols), frozenset(base))}
    for f in kind.fields:
        if f.name in key or (f.need == "Must" and f.value != "Names"):
            continue
        #: `value`, always: a heading is a set of names, and a `section`
        #: keyed by `name` whose voices were also `name` would have two.
        cols = key + (("rank", "value") if f.value == "Names" else ("value",))
        out[f"{kind.name}.{f.name}"] = Relation(
            cols, frozenset(split.get(f.name, ())))
    return out


def dangling(document, rels: dict) -> set:
    """`(kind, key)` of every record whose reference does not resolve —
    the two foreign-key rules, run over the relations rather than
    remembered in a parser."""
    out: set = set()
    for kind in document.kinds:
        if kind.name not in rels:
            continue
        base = rels[kind.name]
        for ref in kind.refers:
            if ref[0] == "Refer":
                _r, field, other = ref
                known = rels[other].project(*document[other].key)
                for row in base.rows:
                    if (row[base.column(field)],) not in known:
                        out.add((kind.name, tuple(row[base.column(c)] for c in kind.key)))
            else:
                _w, field, other, listed = ref
                via = next(r[1] for r in kind.refers
                           if r[0] == "Refer" and r[2] == other)
                names = rels[f"{other}.{listed}"]
                held = names.project(*(document[other].key + ("value",)))
                for row in base.rows:
                    at = (row[base.column(via)], row[base.column(field)])
                    if at not in held:
                        out.add((kind.name, tuple(row[base.column(c)] for c in kind.key)))
    return out


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

#: **What makes a `.ges` beside a document its declaration**, cheaply
#: and without compiling it: the file says `kinds`.  Every other `.ges`
#: next to a document is a *piece* — `examples/audio/arc.ges` is one —
#: and compiling those with `facts.ges` in front would be expensive and
#: would fail, since a piece wants the audio preludes and not this one.
_DECLARES = re.compile(r"^kinds\s*[:=]", re.M)


def _document(path: Path) -> Document:
    """The kinds of one file, compiled once per edit of it or of the
    library — `charts.load`'s shape, and for its reason: the compile is
    a fifth of a second and the answer never changes while the files do
    not."""
    path = Path(path)
    key = str(path)
    stamp = (path.stat().st_mtime_ns, LIBRARY.stat().st_mtime_ns)
    found = _LOADED.get(key)
    if found is None or found[0] != stamp:
        found = _LOADED[key] = (stamp, Document(path))
    return found[1]


def load(name: str = "notes") -> Document:
    """The kinds gestate ships, from `gestate/<name>.ges`."""
    return _document(HERE / f"{name}.ges")


def beside(path) -> Document:
    """The kinds a document is read by — **the `.ges` of its own name,
    next to it**.

    Henri, 2026-09-09: *"entä jos laji eläisi `<file>.ges` -nimisessä
    dokumentissa, joka olisi `<file>.notes` ja jne. ohella?  Silloin
    olisi yksi lähde joka ilmoittaa lajin."*  One document, one
    declaration, paired by name, nothing to disagree — which is what
    kills the question of two programs declaring one kind differently.

    A sibling that does not say `kinds` is not a declaration at all: it
    is a piece, and the document falls back to the ones gestate ships.
    A sibling that *does* say it and will not compile is refused by
    name rather than skipped, because a document read by a schema
    nobody could load is a document read by the wrong schema.
    """
    if path is None:
        return load("notes")
    beside_it = Path(path).with_suffix(".ges")
    try:
        text = beside_it.read_text(encoding="utf-8")
    except OSError:
        return load("notes")
    if not _DECLARES.search(text):
        return load("notes")
    try:
        return _document(beside_it)
    except Exception as why:                                # noqa: BLE001
        raise FactsError(
            f"{beside_it.name} declares the kinds of {Path(path).name} and "
            f"will not load: {why}") from None
