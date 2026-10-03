"""A document of any kinds, written back and edited by its declaration.

**The second writer, and the declaration is what it reads.**
`gestate/notes.py` writes a `.notes` and asserts and retracts its
records with the three shipped kinds in hand — `bpm` first, a section's
line, a blank line at every bar.  A document whose kinds a program
declares for itself (`card:gui-is-difficult.md` §"The mashup, asked",
2026-09-13: the board of a game, one mark a line) has no such writer,
and this is it: the kinds in the order declared, a kind's records in
its declared order (`facts.sort_key`), a record's fields in their
declared order, the prose above and beside each record kept — nothing
here knows what a kind means.

Held to the `.notes` writer on `arc.notes` by `test/test_documents.py`,
modulo the blank lines that writer puts between bars, which is the one
thing it knows that a declaration does not say.  `declare, hold to
parity, derive` — `doc/memory/declare-parity-derive.md`.

The two primitive edits, `asserted` and `retracted`, are `notes.py`'s
in shape: a line in the document's own syntax in, the whole document
out, refused in the parser's words when the result would not read —
`card:relational-model.md` scar 5, *nothing writes a document that does
not read it back.*
"""

from __future__ import annotations

from pathlib import Path

from .facts import Document, Kind, beside, dangling
from .notes import NotesError, _given_key, _lines, _uncomment, records, relations_of


# ── Writing one back ─────────────────────────────────────────────────────


def record_line(kind: Kind, values: dict, beside_it: str | None = None) -> str:
    """One record as the file writes it — the kind's word, then its
    fields in the declared order, a `Headed` kind's name bare after the
    word and a `Bare` kind's one value alone.  An absent `May` field is
    not written; a `Names` field is its names joined by commas."""
    shape = kind.shape
    if shape[0] == "Bare":
        out = f"{kind.name} {values[shape[1]]}"
    else:
        parts = [kind.name]
        if shape[0] == "Headed":
            parts[0] = f"{kind.name} {values[shape[1]]}"
        for f in kind.fields:
            value = values.get(f.name)
            if value is None:
                continue
            if f.value == "Names" and not isinstance(value, str):
                value = ",".join(value)
            parts.append(f"{f.name} {value}")
        out = "  ".join(parts)
    return out + (f"  {beside_it}" if beside_it else "")


def key_line(kind: Kind, values: dict) -> str:
    """A record's key as `retracted` takes it — `mark cell 4`, or
    `section A` for a `Headed` kind."""
    if kind.shape[0] == "Headed":
        return f"{kind.name} {values[kind.shape[1]]}"
    return " ".join([kind.name] + [f"{c} {values[c]}" for c in kind.key])


def _lookups(document: Document, kind: Kind, entries: list):
    """The two callbacks `facts.sort_key` takes for records of `kind`,
    over these entries: where a record stands among its own kind, and
    the names the record a reference points at carries — both read off
    the file's own order, and nothing else."""
    by_kind: dict = {}
    for _line, one, values, _above, _beside in entries:
        by_kind.setdefault(one.name, []).append(values)

    def head_of(other: Kind, values: dict):
        if other.shape[0] == "Headed":
            return values[other.shape[1]]
        return tuple(values[c] for c in other.key)

    def named(other: Kind, value):
        return value if other.shape[0] == "Headed" else (value,)

    def among(other_name: str, value) -> int:
        other = document[other_name]
        rank = [head_of(other, v) for v in by_kind.get(other_name, [])]
        wanted = named(other, value)
        return rank.index(wanted) if wanted in rank else len(rank)

    def along(other_name: str, ofield: str, record: dict):
        other = document[other_name]
        via = next((r[1] for r in kind.refers
                    if r[0] == "Refer" and r[2] == other_name), None)
        if via is None:
            return ()
        for v in by_kind.get(other_name, []):
            if head_of(other, v) == named(other, record[via]):
                names = v.get(ofield) or ()
                #: A `Names` field as `records` hands it: the token
                #: itself, split here.
                return (tuple(n for n in names.split(",") if n)
                        if isinstance(names, str) else tuple(names))
        return ()

    return among, along


def rendered(document: Document, entries: list, closing: tuple = ()) -> str:
    """The file these records make: kinds in the declared order, a blank
    line between kinds, each kind's records in its declared order —
    stably, so records the order does not separate keep the order they
    were read in — and every comment back where its author put it."""
    from .facts import sort_key

    lines: list[str] = []
    first = True
    for kind in document.kinds:
        mine = [e for e in entries if e[1].name == kind.name]
        if not mine:
            continue
        if kind.order:
            among, along = _lookups(document, kind, entries)
            mine = sorted(mine, key=lambda e: sort_key(kind, e[2], along, among))
        if not first:
            lines.append("")
        first = False
        for _line, _kind, values, above, beside_it in mine:
            lines += list(above)
            lines.append(record_line(kind, values, beside_it))
    lines += list(closing)
    return "\n".join(lines) + "\n"


def write(text: str, name: str = "<document>", where=None) -> str:
    """The same document, in its own order — the canonical form."""
    document = beside(where)
    entries = records(text, name, where)
    _e, closing = _lines(text, name, document)
    return rendered(document, entries, closing)


# ── The two primitive edits ──────────────────────────────────────────────


def _checked(text: str, name: str, where) -> str:
    """`text`, having read it back — the structural pass, the domains,
    and the references derived from the declaration — or the refusal."""
    rels = relations_of(text, name, where=where)
    loose = dangling(beside(where), rels)
    if loose:
        kind, key = sorted(loose, key=str)[0]
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(
            f"{name}: `{kind} " + " ".join(str(k) for k in key)
            + "` refers to a record this file does not have")
    return text


def asserted(text: str, written: str, name: str = "<document>",
             where=None) -> tuple:
    """`(text, said)` — the document with one record added.

    `written` is a line in the document's own syntax; what it may say
    is the declaration's, and a key already written is refused — a
    doubled line is one fact said twice, and asserting it again is a
    gesture with nothing to do."""
    document = beside(where)
    entries = records(text, name, where)
    _e, closing = _lines(text, name, document)
    place = f"{name}: the asserted record"
    line, beside_it = _uncomment(written)
    if not line.split():
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place} is empty")
    new = records(line, place, where)
    if len(new) != 1:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place} must be one record")
    _n, kind, values, _above, _b = new[0]
    key = tuple(values[c] for c in kind.key) if kind.key else None
    for _l, other, had, _a, _b2 in entries:
        if other.name == kind.name and (
                not kind.key or tuple(had[c] for c in kind.key) == key):
            what = key_line(kind, values) if kind.key else kind.name
            #: complaint  command — a program's act on its document, answered in the status line
            raise NotesError(
                f"{place}: `{what}` is already written, on line {_l}"
                + (" — a doubled line is one fact said twice" if kind.key
                   else " — this document has at most one"))
    entries.append((0, kind, values, (), beside_it))
    out = _checked(rendered(document, entries, closing), name, where)
    return out, f"asserted {record_line(kind, values)}"


def retracted(text: str, key: str, name: str = "<document>",
              where=None) -> tuple:
    """`(text, said)` — the document with one record's fact removed, by
    its key in the document's own syntax.  Refused when nothing says
    it, and when what is left would not read — restrict, not cascade,
    with the reader as the oracle."""
    document = beside(where)
    entries = records(text, name, where)
    _e, closing = _lines(text, name, document)
    line, _b = _uncomment(key)
    tokens = line.split()
    place = f"{name}: the retracted record"
    if not tokens:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place} is empty")
    word = tokens[0]
    place = f"{name}: the retracted `{word}`"
    kind = document.kind(word)
    if kind is None:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(
            f"{place}: `{word}` is not a record; a line is "
            + ", ".join(f"`{k} …`" for k in document.names))
    if not kind.key:
        wanted = None
    else:
        given = _given_key(kind, tokens[1:], place)
        wanted = tuple(given[c] for c in kind.key)

    def says(values: dict) -> bool:
        return wanted is None or tuple(str(values[c]) for c in kind.key) == wanted

    gone = [e for e in entries if e[1].name == word and says(e[2])]
    if not gone:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place}: no `{word}` here says that")
    kept = [e for e in entries if e not in gone]
    made = rendered(document, kept, closing)
    try:
        _checked(made, name, where)
    except NotesError as why:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(
            f"{place}: retracting it would leave the file unreadable — "
            f"{why}") from None
    lines = "" if len(gone) == 1 else f", written on {len(gone)} lines"
    return made, f"retracted {' '.join(tokens)}{lines}"


def moved(text: str, kind_name: str, old: dict, new: dict,
          name: str = "<document>", where=None) -> tuple:
    """`(text, said)` — one record moved: its line found by its key, and
    every field `new` names that differs rewritten in place, one field's
    bytes at a time (`notes.retune`, `spec/north_star.md`'s law).  The
    act a reactor's commit sends for a carried note
    (`card:gui-is-difficult.md` §"The next slice: the notes editor's
    note hand"), and for a dragged dot, whose `x` is not its key: the
    line keeps its place, its prose and its other fields, which a
    retract and an assert would not — the file's opening comment rides
    on its first record, and went with it (F248).

    Refused, whole, by the reader's own rules — a domain, a reference, a
    bar past its section's end, a tick past its bar — and when it would
    land on a record already written there; `do_carry`'s refusals, said
    by the document rather than by the command."""
    from .notes import doubled, refused, retune

    document = beside(where)
    kind = document.kind(kind_name)
    if kind is None or not kind.key:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{name}: `{kind_name}` is not a keyed record — a move "
                         "names a record by its key")
    want = tuple(str(old[c]) for c in kind.key)
    found = [e for e in records(text, name, where)
             if e[1].name == kind.name
             and tuple(str(e[2][c]) for c in kind.key) == want]
    if not found:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{name}: no `{key_line(kind, old)}` here to move")
    line, _kind, values, _above, _beside = found[0]
    out, said = text, []
    #: The key first, then the rest in the declared order — a `new` of
    #: the key alone (`fact_of`'s `keyed`) moves only the key.
    for col in list(kind.key) + [f.name for f in kind.fields if f.name not in kind.key]:
        if col in new and str(new[col]) != str(values.get(col)):
            if kind.name in ("note", "section", "bpm"):
                out, word = retune(out, line, col, values[col], new[col])
            else:
                out, word = _rewritten(out, line, kind, col, values.get(col), new[col])
            said.append(word)
    if out == text:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{name}: `{key_line(kind, old)}` is already there — nothing to move")
    _checked(out, name, where)
    if document.kind("note") is None or document.kind("section") is None:
        return out, f"moved line {line}: " + ", ".join(said)
    rels = relations_of(out, name, where=where)
    if refused(rels, where):
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{name}: line {line} would leave its section — "
                         "a note does not leave its section by dragging")
    if any(a["line"] == line or b["line"] == line for a, b in doubled(rels)):
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{name}: line {line} would land on a note already "
                         "written there — the file cannot say one place twice")
    return out, f"moved line {line}: " + ", ".join(said)


def _rewritten(text: str, line: int, kind: Kind, field: str, was, now) -> tuple:
    """`(text, said)` — one field of one record's line rewritten
    byte-exactly, for a kind the program declares: `notes.retune`'s law
    without its knowledge of notes.  A `Headed` kind's name and a `Bare`
    kind's value stand bare after the word; any other field is written
    `field value`.  Only the record half of the line is searched, so the
    prose beside it is never edited; refused when the line does not say
    `was` — the file has moved under the picture."""
    import re

    lines = text.splitlines(keepends=True)
    place = f"line {line}"
    if not 0 < line <= len(lines):
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place} is not in this file any more")
    row = lines[line - 1]
    record, _said = _uncomment(row)
    head = kind.shape[0] in ("Headed", "Bare") and kind.shape[1] == field
    pattern = (rf"^(\s*{re.escape(kind.name)}\s+)(\S+)" if head
               else rf"(\b{re.escape(field)}\s+)(\S+)")
    found = re.search(pattern, record)
    if found is None:
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(f"{place} has no `{field}` to change")
    if found.group(2) != str(was):
        #: complaint  command — a program's act on its document, answered in the status line
        raise NotesError(
            f"{place} says `{field} {found.group(2)}` where the picture "
            f"thought `{field} {was}` — the file has moved under the picture")
    lines[line - 1] = row[:found.start(2)] + str(now) + row[found.end(2):]
    return "".join(lines), f"{field} {was} → {now} on line {line}"


def revealed(text: str, kind_name: str, key: dict, name: str = "<document>",
             where=None) -> str:
    """Where a record is written, said — what a click on a note in an
    included file answers (`session._reveal`): the file and the line."""
    document = beside(where)
    kind = document.kind(kind_name)
    want = tuple(str(key[c]) for c in kind.key) if kind and kind.key else None
    for line, other, values, _a, _b in records(text, name, where):
        if other.name == kind_name and want == tuple(str(values[c]) for c in kind.key):
            return f"{name}:{line} — {record_line(other, values)}"
    #: complaint  command — a program's act on its document, answered in the status line
    raise NotesError(f"{name}: no `{key_line(kind, key)}` here")


def stamp(path: Path) -> tuple:
    """When a document last changed — what a host compares a frame
    later to know whether to read it again."""
    try:
        return (path.stat().st_mtime_ns, path.stat().st_size)
    except OSError:
        return ()
