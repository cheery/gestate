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


class DeclarationCycle(FactsError):
    """A declaration that needs its own document read first — said once,
    and passed through `beside` unwrapped."""


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


@dataclass(frozen=True)
class Rel:
    """One relation of a document's model, as its file declares it —
    `facts.ges`' `Rel` and `Of`.  `cols` is the heading in order, each
    `(name, domain)` with the domain a tuple `("Word",)`, `("Number",)`,
    `("Range", lo, hi)`, `("AtLeast", n)` or `("OneOf", names)`; `key`
    names columns of it.  An `Of` carries its parent's name and its
    field, and `need` — whether every parent must have a row here —
    and, once `model_of` has resolved it, its parent's key columns in
    front of its own (`facts.ges`' `relCols`, `relKey`); `own_key` is
    the part it declared, empty for a value a record may carry and
    `rank` for a list."""
    name: str
    cols: tuple
    key: tuple
    parent: str | None = None
    field: str | None = None
    need: str | None = None
    own_key: tuple = ()

    @property
    def heading(self) -> tuple:
        return tuple(c for c, _d in self.cols)

    def domain(self, col: str) -> tuple | None:
        return next((d for c, d in self.cols if c == col), None)


def _domain(term) -> tuple:
    """A column's domain — a `Value` that is one token; a list is an
    `Of` with a rank, and never a column's domain."""
    head, *args = term
    if head in ("Word", "Number"):
        return (head,)
    if head in ("Range", "AtLeast"):
        return (head, *args)
    if head == "OneOf":
        return (head, tuple(_text(a) for a in args[0]))
    if head in ("Names", "Each"):
        raise FactsError(
            f"`{head}` is no domain of a column: a list is an `Of` with a "
            "`rank` key, one row a name")
    raise FactsError(f"`{head}` is not a domain")


def _col(term) -> tuple:
    head, name, domain = term
    if head != "Col":
        raise FactsError(f"`{head}` is not a column")
    return (_text(name), _domain(domain))


def _rel(term) -> Rel:
    head, *args = term
    if head == "Rel":
        name, cols, key = args
        return Rel(name=_text(name), cols=tuple(_col(c) for c in cols),
                   key=tuple(_text(k) for k in key))
    if head == "Of":
        parent, field, cols, key, need = args
        key = tuple(_text(k) for k in key)
        return Rel(name=f"{_text(parent)}.{_text(field)}",
                   cols=tuple(_col(c) for c in cols), key=key,
                   parent=_text(parent), field=_text(field), need=need[0],
                   own_key=key)
    raise FactsError(f"`{head}` is not a relation")


def model_of(terms) -> tuple:
    """The model a program declares, read and checked: every `Of` names
    a parent the model has, and a relation's key is the front of its
    heading, in key order — so a row reads as its identity and then
    its facts, and `base_columns` and `relRow` agree on it."""
    raw = tuple(_rel(t) for t in terms)
    by_name = {r.name: r for r in raw if r.parent is None}
    rels = []
    for r in raw:
        if r.parent is not None:
            parent = by_name.get(r.parent)
            if parent is None:
                raise FactsError(
                    f"`{r.name}` hangs off `{r.parent}`, which the model does "
                    "not declare — " + ", ".join(f"`{n}`" for n in by_name))
            if not r.own_key and r.need == "Must":
                raise FactsError(
                    f"`{r.name}` is a required single value; that is a column "
                    f"of `{r.parent}`, not an `Of` with no key")
            #: **Resolved**: the parent's key columns in front, the way
            #: `relCols` and `relKey` read it in the language.
            front = tuple(c for c in parent.cols if c[0] in parent.key)
            r = Rel(name=r.name, cols=front + r.cols, key=parent.key + r.own_key,
                    parent=r.parent, field=r.field, need=r.need, own_key=r.own_key)
        own = tuple(c for c in r.heading if c in r.key)
        if r.heading[:len(r.key)] != r.key or own != r.key:
            raise FactsError(
                f"`{r.name}`'s key comes first in its heading, in key order — "
                + " ".join(r.key) + " and then the rest")
        rels.append(r)
    return tuple(rels)


#: A domain's token shape on the line, and the `Field` domain it keeps.
_LINE = {"Word": ("Word", None), "Number": ("Number", None),
         "Range": ("Number", "keep"), "AtLeast": ("Number", "keep"),
         "OneOf": ("Word", "keep")}


def _line_field(name: str, domain: tuple, need: str, listed: bool) -> Field:
    if listed:
        if domain[0] == "OneOf":
            return Field(name, "Names", need, ("Each", domain[1]))
        return Field(name, "Names", need)
    value, keep = _LINE[domain[0]]
    return Field(name, value, need, domain if keep else None)


def line_kind(rels: tuple, term) -> Kind:
    """**A `Kind` from a `Line` and the model** — the host's half of
    `facts.ges`' `lineKind`, held equal to it by `test/test_facts.py`.
    Each field the line folds in is a column of the line's relation
    (`Must`), or an `Of` of it: with no key of its own a value the
    record may carry (`May`), with a rank a list, required or not as
    the `Of` says.  A field nothing owns is refused by name."""
    head, word, shape, fields, order = term
    if head != "Line":
        raise FactsError(f"`{head}` is not a line")
    word = _text(word)
    by_name = {r.name: r for r in rels}
    base = by_name.get(word)
    if base is None or base.parent is not None:
        raise FactsError(
            f"the line `{word}` writes no relation of the model — "
            + ", ".join(f"`{r.name}`" for r in rels if r.parent is None))
    out = []
    for f in fields:
        f = _text(f)
        domain = base.domain(f)
        if domain is not None:
            out.append(_line_field(f, domain, "Must", False))
            continue
        of = by_name.get(f"{word}.{f}")
        if of is None:
            raise FactsError(
                f"the line `{word}` folds in `{f}`, which is no column of "
                f"`{word}` and no `Of` it — "
                + ", ".join(f"`{c}`" for c in base.heading)
                + "".join(f", `{r.field}`" for r in rels if r.parent == word))
        domain = of.domain("value") or ("Word",)
        out.append(_line_field(f, domain, of.need if of.own_key else "May",
                               bool(of.own_key)))
    return Kind(name=word, shape=_shape(shape), fields=tuple(out),
                key=base.key, order=tuple(_sort(o) for o in order))


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

    The key plus every required fieldScalar field is the base relation,
    under the kind's name.  Each `May` field is a relation of its own,
    `kind.field`, so that absence is no row and never a null.  Each
    `Names` field is a relation of its own with a rank, so that a list
    in a value has a row to hang a second fact on (scar 4) and the
    order the author wrote is a fact and not a position.  Both are
    headed by the key and then `value`, or `rank` and `value`.
    """
    key = kind.key
    base_cols = base_columns(kind)
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
        #: **A GUI program may declare its own document's kinds** —
        #: `card:gui-is-difficult.md` §"The mashup, asked", choice 1.
        #: Such a file wants the canvas's vocabulary, so it is compiled
        #: as the canvas compiles it, with `facts.ges` after that chain
        #: (`audio.preludes`), and the kinds are read off the result.
        #: A bare declaration is compiled with this library alone.
        text = self.path.read_text(encoding="utf-8")
        source = None
        from .audio import has_substrate
        from .notes import expand

        opened = expand(text, self.path.parent)
        if has_substrate(opened):
            from .gui import assembled
            source = assembled(opened)
        #: **From stage one when the program has been built** — a
        #: substrate that reads a `document` evaluated its `kinds` on the
        #: way (`gestate/stage.py`), and the analysis remembers them, so
        #: this is a dictionary read where it was a second compile
        #: (`card:strict-forms.md` §"The next cut").  A bare declaration,
        #: or a program nobody has built yet, compiles as before.
        from .pipeline import staged_value

        found = staged_value(source, "model") if source is not None else None
        self.from_stage = found is not None
        if found is not None:
            model, lines = found, staged_value(source, "lines")
        else:
            self.terms = Terms(self.path, LIBRARY, source)
            try:
                model = self.terms.read(self.terms.declared("model"))
                lines = self.terms.read(self.terms.declared("lines"))
            except ChartError as why:
                raise FactsError(str(why)) from None
        #: **The model first, the line view derived** — `facts.ges`
        #: §"The line view".  `rels` is what `document "name"` reads,
        #: any relation by name; `kinds` is what the parser and the
        #: writer read a line by, and nobody declares it.
        self.rels = model_of(model)
        self.kinds = tuple(line_kind(self.rels, l) for l in lines)

    def __getitem__(self, name: str) -> Kind:
        found = self.kind(name)
        if found is None:
            raise FactsError(
                f"{self.path.name} declares no kind `{name}`; it has "
                + ", ".join(f"`{k.name}`" for k in self.kinds))
        return found

    def kind(self, name: str) -> Kind | None:
        return next((k for k in self.kinds if k.name == name), None)

    def relation(self, name: str) -> Rel:
        """The relation of this name — a base one or an `Of`, as
        `section.voices` — or a refusal naming the ones there are."""
        found = next((r for r in self.rels if r.name == name), None)
        if found is None:
            raise FactsError(
                f"{self.path.name} declares no relation `{name}`; it has "
                + ", ".join(f"`{r.name}`" for r in self.rels))
        return found

    @property
    def names(self) -> tuple:
        return tuple(k.name for k in self.kinds)


_LOADED: dict = {}
_LOADING: set = set()

#: **What makes a `.ges` beside a document its declaration**, cheaply
#: and without compiling it: the file says `kinds`.  Every other `.ges`
#: next to a document is a *piece* — `examples/audio/arc.ges` is one —
#: and compiling those with `facts.ges` in front would be expensive and
#: would fail, since a piece wants the audio preludes and not this one.
_DECLARES = re.compile(r"^model\s*[:=]", re.M)


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
        #: **A declaration that includes its own document as a score is
        #: a cycle**, said once rather than found at the recursion
        #: limit: expanding the program parses the `.notes`, parsing it
        #: reads the declaration beside it, which is this program.  A
        #: document read through `document "<kind>"` is the program's
        #: own and is not a `.notes` score include (`notes.expanded`).
        if key in _LOADING:
            #: complaint  author, nowhere — the program's own include line and its own model need each other first; the fault is the pairing of a suffix and a declaration, which no one line holds
            raise DeclarationCycle(
                f"{path.name} declares the model of a `.notes` it includes as "
                "a score, and each needs the other first — a document the "
                "program reads through `document` is its own, not a score: "
                "name it by another suffix, or read the notes through the roll")
        _LOADING.add(key)
        try:
            found = _LOADED[key] = (stamp, Document(path))
        finally:
            _LOADING.discard(key)
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
    except DeclarationCycle:
        raise                       # already a sentence about this declaration
    except Exception as why:                                # noqa: BLE001
        raise FactsError(
            f"{beside_it.name} declares the model of {Path(path).name} and "
            f"will not load: {why}") from None


# **A program reads its document through one word**:
#
#     board = document "mark"
#
# **The type is computed from the kind** — `facts.ges`' `kindRow`, run by
# the compiler before the program is checked (`gestate/stage.py`): the
# key fields and then every required fieldScalar field, in the declared
# order, a `Number` an `Int` and a `Word` a `Text` — `relations`' base
# relation, exactly, and `base_columns` below is held to `kindColumns`
# there.  The compiler declares the channel the rows arrive on; the host
# checks the file against the kinds the program declares and feeds the
# rows at every change of the document (`Workbench._feed_documents`).
# The program stores nothing.
#
# Underneath it is the grid's road: a channel carrying the rows, the
# rows made a set.  A person never writes that channel, and a number
# channel carrying a cell was the seam Henri called hacky.  Until
# 2026-09-14 this file rewrote the line as text in front of the
# compiler, with the row's type written by hand in the program and
# checked against the kind by the host; `card:strict-forms.md` is where
# that seam was measured and closed.

#: A relation's name may carry a dot — `section.voices` — so the word
#: is wider than an identifier.
_DOCUMENT = re.compile(r'document[ \t]+"([\w.]+)"')


def channel_of(kind: str) -> str:
    """The channel a kind's rows arrive on — the host's name, never a
    person's; `stage.channel_of` says the same."""
    #: `section.voices` is a relation and no identifier: the dot is an
    #: underscore on the channel, and nothing but the host reads it.
    return f"__doc_{kind.replace('.', '_')}__"


def documents(source: str) -> list:
    """The kinds a program reads through `document "kind"`, in the order
    written, each once — what the host feeds."""
    out = []
    for m in _DOCUMENT.finditer(source):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


def base_columns(kind: Kind) -> list:
    """The columns of a kind's base relation — the key, then every
    required fieldScalar field not in it — which is also the row a program
    reads and the fields a `Fact` constructor carries."""
    return list(kind.key) + [f.name for f in kind.fields
                             if f.need == "Must" and f.value != "Names"
                             and f.name not in kind.key]


def rows_of(document: Document, rels: dict, name: str) -> list:
    """The rows a program's `document "name"` receives: that relation's
    — a base one or an `Of`, `section.voices` included — each a tuple
    in heading order, sorted so a feed is the same list for the same
    file."""
    document.relation(name)
    return sorted(rels[name].rows)


def fact_of(document: Document, kind_text, atoms) -> tuple:
    """`(kind, {column: value})` of the fact an `Act` carries.

    A fact is **the kind's word and its base columns' values as atoms,
    in column order** — `Assert "mark" [IntAtom 4, TextAtom "X"]` for
    `mark  cell 4  mark X`, which `facts.ges`' `asserting markKind (4,
    "X")` builds.  A `Text` arrives as the code points the machine
    holds it as; an atom of the wrong shape for its column is refused
    by name."""
    name = _text(kind_text)
    kind = document.kind(name)
    if kind is None:
        raise FactsError(
            f"`{name}` names no kind of {document.path.name}; a fact's "
            "word is a kind's — "
            + ", ".join(f"`{k.name}`" for k in document.kinds))
    cols = base_columns(kind)
    if len(atoms) != len(cols):
        raise FactsError(
            f"`{name}` carries {len(atoms)} values and `{kind.name}` has "
            f"{len(cols)} — " + ", ".join(f"`{c}`" for c in cols))
    values = {}
    for col, atom in zip(cols, atoms):
        head, value = atom
        field = kind.field(col)
        number = field is not None and field.value == "Number"
        if number and head != "IntAtom":
            raise FactsError(
                f"`{col}` of `{kind.name}` is a number and the fact carries a word")
        if not number and head != "TextAtom":
            raise FactsError(
                f"`{col}` of `{kind.name}` is a word and the fact carries a number")
        values[col] = int(value) if number else _text(value)
    return kind, values
