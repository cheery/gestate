"""`.notes` — a flat note file the score is written in.

    section A  key D  mode lydian  bars 8  beats 4  voices melody,roots
    note  section A  bar 1  at 0    len 96  voice melody  key 62  vel mf
    note  section A  bar 1  at 96   len 96  voice melody  key 66  vel mp
    note  section A  bar 1  at 0    len 384 voice roots   key 38  vel mf

`spec/drawnscores.md` is the contract and the argument; this is the
parser, the refusals, and the source-to-source expansion that turns a
file into ordinary `.ges` declarations.

**Why a source-to-source expansion**, which is `audiovoices.py`'s answer
to the same question and is copied from it deliberately: a `.notes` file
is finite, deterministic data, and the score algebra already expresses
all of it.  So the expander writes out the `[: a :]` the author would
have written by hand, and the extractor, the type checker, the renderer
and the score box all go on seeing a program they already understood.

**The line is the note, and that is the whole point.**  Every record is
self-contained — it names its section, its bar and its voice — so no
line's meaning depends on a line above it.  That is what makes the
format survive being reflowed, and it is what makes a drag on the roll
able to rewrite one line and nothing else — and, since 2026-09-08, to
put that line where the note sounds (`canonical`): the file is a table,
a note's identity is its content, and the line it was typed on is not
kept.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import gcd
from pathlib import Path


#: complaint  author — a mistake in a `.notes` file, placed by the line
#: that made it.  Every one of them can be: a note **is** a line, which
#: is the whole property this format is for, so there is never a case
#: here where the position had to be guessed at or given up on.
class NotesError(Exception):
    """A `.notes` file that will not load, said in the author's terms."""


#: **The eight dynamics, as names.**  `spec/drawnscores.md` §"`vel` is a
#: named level": a dynamic is the same kind of thing a manner is — an
#: intention the voice realises — and `doc/notes/notes-on-writing-a-piece.md`
#: W4 is what a raw float cost.  The index is what travels to the voice.
LEVELS = ("ppp", "pp", "p", "mp", "mf", "f", "ff", "fff")

#: The manner names, and the bit each one is.  Kept in step with
#: `audio.ges`'s `Plain`/`Staccato`/`Accent`/`Portamento` by
#: `test_drawnscores.py`, because two spellings of one vocabulary is
#: exactly what `spec/annotations.md` was written to stop.
MANNERS = {"staccato": 1, "accent": 2, "portamento": 4}

#: A beat, in ticks — `music.ges`' `ticksPerBeat`, and `spec/music.md`
#: chose 96 because it divides by 2, 3, 4, 6, 8, 12, 16, 24, 32 and 48.
#: So a triplet eighth is 32 and a sixteenth is 24, both whole numbers,
#: which is the whole of Henri's *"flat, but only if it allows writing
#: triplets/tuplets"*.
TICKS_PER_BEAT = 96

#: The twelve, spelled the way a person writes a key.  Only the section
#: header uses these; a note writes a MIDI key number, which is decision
#: 2 of the spec and the rule the format hangs on.
_PITCH_CLASS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
                "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
                "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

#: The modes the lamp knows, as semitones from the tonic.  Reporting
#: only: `spec/drawnscores.md` decision 3 — a ♯11 over a dominant is the
#: whole of `arc.ges`'s A section, and a check that refused it would
#: refuse the blues.
_MODES = {
    "ionian":     (0, 2, 4, 5, 7, 9, 11), "major":      (0, 2, 4, 5, 7, 9, 11),
    "dorian":     (0, 2, 3, 5, 7, 9, 10),
    "phrygian":   (0, 1, 3, 5, 7, 8, 10),
    "lydian":     (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "aeolian":    (0, 2, 3, 5, 7, 8, 10), "minor":      (0, 2, 3, 5, 7, 8, 10),
    "locrian":    (0, 1, 3, 5, 6, 8, 10),
}

_NAME = re.compile(r"^[A-Za-z_]\w*$")


#: **The record classes are gone** — 2026-09-10,
#: `card:relational-model.md` Q6.  A parsed document *is* its relations
#: (`facts.Relation`), and a record is a `dict` of its fields as the
#: declaration names them: `{"section": "A", "bar": 1, …}`.  `Note`,
#: `Section` and `NotesFile` were a third statement of what a `.notes`
#: is, beside the declaration and the file itself, and each of their
#: attributes renamed a field it already had — `length` for `len`,
#: `level` for `vel`, `manners` for `manner` — so a reader had to know
#: two vocabularies for one document.  The views are `sections_of` and
#: `notes_of`; the facts themselves are the relations.


# ── Parsing ─────────────────────────────────────────────────────────────────

#: **What a `.notes` is, is declared in `gestate/notes.ges`** — the
#: kinds, their fields, which are required, the key, and the order.  It
#: used to be four sets here; since 2026-09-09 there is one statement of
#: it and this reads it (`card:gui-is-difficult.md` §"Landed —
#: 2026-09-09").  What stays in this file is what a note *means*: a
#: dynamic is a name, a manner is a bit, a bar has at least one beat.
#:
#: **And which declaration is *this* file's is its own name** — Henri,
#: 2026-09-09: the kinds live in `<file>.ges` beside `<file>.notes`, so
#: one document has one declaration and there is nothing to disagree.  A
#: sibling that does not say `kinds` is a piece and not a declaration
#: (`examples/audio/arc.ges` is one), and the document falls back to the
#: ones gestate ships.  `where` is the document's path when the caller
#: has one; a text with no file behind it gets the shipped kinds.
#:
#: Loaded lazily and cached by `facts`, so importing this module still
#: costs nothing and the compile — 0.27 s, once per process — is paid by
#: whoever first reads a file.
def _kinds(where=None):
    from .facts import beside

    return beside(where)


#: How a value's shape is said in a refusal — `Bare` lines are the only
#: place a person is told what one token has to be.
_AS = {"Number": "number", "Word": "word", "Names": "names"}


def _oneof(items: list[str]) -> str:
    """`a`, `b` or `c` — a list a person reads, from a list a
    declaration gives."""
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " or " + items[-1]


def _fields(tokens: list[str], kind, place: str) -> dict[str, str]:
    """`key value key value …` into a dict, refusing what a person mistypes.

    Positional values are refused outright, which is gate two of
    `spec/drawnscores.md` §"The four gates" — *the failure that made
    `manner` unfindable was two fields of one shape telling apart only by
    position*.

    **The list a refusal names is the declaration's**, so a field added
    there is offered here without this function being touched.
    """
    allowed = set(kind.named)
    out: dict[str, str] = {}
    rest = list(tokens)
    while rest:
        key = rest.pop(0)
        if key not in allowed:
            raise NotesError(
                f"{place}: `{key}` is not a field here; this record takes "
                + ", ".join(f"`{f}`" for f in sorted(allowed)))
        if key in out:
            raise NotesError(f"{place}: `{key}` is written twice")
        if not rest:
            raise NotesError(f"{place}: `{key}` has no value")
        out[key] = rest.pop(0)
    missing = sorted(r for r in kind.required if r not in out)
    if missing:
        raise NotesError(
            f"{place}: missing " + ", ".join(f"`{m}`" for m in missing))
    return out


#: A `#` opens a comment only where a **token** could start — at the
#: beginning of the line or after whitespace.  `key C#` is a tonic and
#: not a comment, and five of the seventeen names `_PITCH_CLASS` offers
#: end in a sharp: `fixme.md` F203, where the old rule made `C#`, `D#`,
#: `F#`, `G#` and `A#` unwritable and blamed the author for the fields
#: it had just eaten.  Every value in this format is one `\S+` token, so
#: there is no other reading to lose.
_COMMENT = re.compile(r"(?:^|(?<=\s))#")


def _uncomment(raw: str) -> tuple[str, str | None]:
    """`(the record, the comment)` — either may be empty, neither is lost."""
    found = _COMMENT.search(raw)
    if found is None:
        return raw, None
    return raw[:found.start()], raw[found.start():].rstrip()


def _int(text: str, key: str, place: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise NotesError(f"{place}: `{key} {text}` is not a whole number") from None


def parse(text: str, name: str = "<notes>", where=None) -> dict:
    """Read a `.notes` file into **its relations**.  Every refusal names
    the file and the line.

    Two passes, because a note may be written above the section it names
    — which is the reflow gate: a file whose lines are shuffled has to
    parse to the same score, and a parser that needed the header first
    would not have that property.

    **And the prose is kept.**  A comment line belongs to the record
    below it and a trailing comment to the record it sits on, so that a
    canonical rewrite puts every word back where its author put it —
    `fixme.md` F200, and `spec/drawnscores.md` §"The prose belongs to
    the record below it" is the rule and its one limit.

    **What this refuses and `relations_of` does not** is integrity: a
    note naming no section, a bar past the section's end, a spelling
    that names another key.  Both roads read one file into one set of
    relations; this one is the gate, and it says what is wrong in the
    author's terms and at a line — which `refused` cannot, because a
    set of keys is not a sentence.
    """
    document = _kinds(where)
    entries, closing = _lines(text, name, document)
    sections: list[dict] = []
    by_name: dict = {}
    note_lines: list = []
    kept: list = []

    for number, declared, tokens, above, beside in entries:
        word = declared.name
        place = f"{name}:{number}"
        if word == "section":
            one = _section(tokens, declared, place)
            if one["name"] in by_name:
                raise NotesError(
                    f"{place}: section `{one['name']}` is declared twice")
            sections.append(one)
            by_name[one["name"]] = one
            kept.append((number, declared, one, above, beside))
        elif word == "note":
            note_lines.append((number, declared, tokens, above, beside))
        elif word == "bpm":
            got = _int(tokens[0], "bpm", place)
            if got < 1:
                raise NotesError(f"{place}: `bpm {tokens[0]}` — a tempo is at least one")
            kept.append((number, declared, {"bpm": got}, above, beside))
        else:
            #: The gap between a declaration and this file, said out
            #: loud the day somebody widens the first without the
            #: second — silence here would drop the record.
            raise NotesError(
                f"{place}: `{word}` is declared in the kinds, and this "
                "version does not know how to read one")

    for number, declared, tokens, above, beside in note_lines:
        one = _note(tokens, declared, f"{name}:{number}", by_name, sections)
        kept.append((number, declared, one, above, beside))

    return _with_index(document, kept, closing)


def _lines(text: str, name: str, document) -> tuple[list, tuple]:
    """The **structural** pass — Codd's first third, and nothing of the
    other two.

    `(entries, closing)`: each entry is `(line, kind, tokens after the
    kind word, prose above, prose beside)`, refused only for what the
    declaration alone can refuse — a word that is no kind, a keyless
    kind written twice, a `Bare` line that is not two tokens.  What a
    record *means* is `parse`'s, and what its fields must be is
    `records`'; splitting them is what lets the integrity rules be run
    over relations instead of remembered here
    (`card:relational-model.md` §"Decided", slice 1).
    """
    entries: list = []
    above: list[str] = []
    alone: set[str] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        record, beside = _uncomment(raw)
        line = record.strip()
        if not line:
            #: **Stripped, not kept as written.**  A comment's indentation
            #: means nothing in a format with no nesting, and keeping it
            #: would make `test_indentation_means_nothing` false for the
            #: prose while it stays true for the records — one file with
            #: two rules about whitespace.
            if beside is not None:
                above.append(raw.strip())
            continue
        tokens = line.split()
        place = f"{name}:{number}"
        word = tokens[0]
        declared = document.kind(word)
        if declared is None:
            raise NotesError(
                f"{place}: `{word}` is not a record; a line is "
                + _oneof([f"`{k} …`" for k in document.names]))
        #: **A kind with no key is one a document has at most one of** —
        #: `facts.ges` says that is what an empty key means, and `bpm`
        #: is the one that has it.  The refusal used to be written here
        #: for `bpm` alone.
        if not declared.key:
            if word in alone:
                raise NotesError(f"{place}: `{word}` is declared twice")
            alone.add(word)
        #: `Bare` is one value and no name, so the line is two tokens.
        if declared.shape[0] == "Bare" and len(tokens) != 2:
            written = declared.field(declared.shape[1])
            raise NotesError(
                f"{place}: `{word}` takes one {_AS[written.value]}")
        entries.append((number, declared, tokens[1:], tuple(above), beside))
        above = []
    return entries, tuple(above)


# ── The relations a reader gets ────────────────────────────────────────────
#
# `card:relational-model.md` Q6 — Henri, 2026-09-10: *"the data can be
# displayed like it's shown in the file, today.  But it should reach the
# reader of that data normalized."*  Two roads lead to one set of
# relations and `test/test_relations.py` holds them to each other on
# `arc.notes`: `parse` reads a file in the author's terms and refuses
# what it may not say, `relations_of` reads the same file by the
# declaration alone.  The file is the source on both; nothing here is
# stored.


def records(text: str, name: str = "<notes>", where=None) -> list:
    """Every record as its **fields**, typed by the declaration and
    checked by nothing else — `(line, kind, fields, above, beside)`.

    A record here may name a section that does not exist or a bar past
    the section's end; those are integrity, and `refused` finds them
    over the relations.  What this refuses is structure: an unknown
    field, a missing required one, a number that is not one, a headed
    record with no head.
    """
    document = _kinds(where)
    out = []
    entries, _closing = _lines(text, name, document)
    for number, kind, tokens, above, beside in entries:
        place = f"{name}:{number}"
        if kind.shape[0] == "Bare":
            got = {kind.shape[1]: tokens[0]}
        elif kind.shape[0] == "Headed":
            if not tokens or not _NAME.match(tokens[0]):
                raise NotesError(f"{place}: `{kind.name}` needs a name")
            got = _fields(tokens[1:], kind, place)
            got[kind.shape[1]] = tokens[0]
        else:
            got = _fields(tokens, kind, place)
        for f in kind.fields:
            value = got.get(f.name)
            if value is None:
                continue
            if f.value == "Number":
                value = got[f.name] = _int(value, f.name, place)
            elif f.value == "Names":
                value = tuple(v for v in value.split(",") if v)
            #: The domain's refusal, derived from the declaration's
            #: bound — `facts.Field.outside`.  `parse` still says the
            #: same thing in the author's terms, and the test holds the
            #: two to one boundary.
            why = f.outside(value)
            if why is not None:
                raise NotesError(f"{place}: {why}")
        out.append((number, kind, got, above, beside))
    return out


def _with_index(document, entries, closing: tuple = ()) -> dict:
    """The relations, plus what is **not** the model — the index.

    `line` maps a written line to the fact it says: `(kind, key, line)`,
    one row per line, **and a key may have several**, because a doubled
    line is one note said twice (`doubled`) and the file honestly holds
    both.  A line number is a physical locator — a rowid — dropped at
    every write and rebuilt at the next read.

    **Prose is keyed by the line, not by the fact**, and that is F200
    read exactly: a comment belongs to the *writing* below it, so two
    identical notes with a sentence each keep a sentence each.  Keying
    it by the record merged them, and the derivation is what found
    that (`doc/memory/declare-parity-derive.md`).
    """
    from .facts import Relation, relations as derive

    by_kind: dict = {}
    line: set = set()
    above: set = set()
    beside: set = set()
    for number, kind, got, over, side in entries:
        by_kind.setdefault(kind.name, []).append(got)
        typed = {c: (int(got[c]) if kind.field(c) and kind.field(c).value == "Number"
                     else str(got[c])) for c in kind.key}
        key = tuple(typed[c] for c in kind.key)
        line.add((kind.name, key, number))
        for rank, text in enumerate(over, start=1):
            above.add((number, rank, text))
        if side is not None:
            beside.add((number, side))
    out: dict = {}
    for kind in document.kinds:
        out.update(derive(kind, by_kind.get(kind.name, [])))
    out["line"] = Relation(("kind", "key", "line"), frozenset(line))
    out["above"] = Relation(("line", "rank", "text"), frozenset(above))
    out["beside"] = Relation(("line", "text"), frozenset(beside))
    out["closing"] = Relation(("rank", "text"), frozenset(
        (rank, text) for rank, text in enumerate(closing, start=1)))
    return out


def _prose_of(rels: dict):
    """`line -> (above, beside)`, indexed once — see `Relation.by`."""
    over = rels["above"].by("line")
    side = rels["beside"].by("line")

    def one(line: int) -> tuple:
        at = (line,)
        return (tuple(o["text"] for o in
                      sorted(over.get(at, ()), key=lambda o: o["rank"])),
                side[at][0]["text"] if at in side else None)

    return one


def relations_of(text: str, name: str = "<notes>", where=None) -> dict:
    """The first road: the relations, from the file by the declaration."""
    document = _kinds(where)
    _entries, closing = _lines(text, name, document)
    return _with_index(document, records(text, name, where), closing)


# ── The two views a reader joins for itself ────────────────────────────────
#
# A reader usually wants the joined form — the performer wants a note
# with its dynamic and its manners and the bar it sits in — and that
# is a view, derived here at every read and stored nowhere
# (`card:relational-model.md` Q6, the first caution).  The roll, the
# performer and the compiled road's declarations read these, and no
# reader anywhere holds a record class, since 2026-09-10.


def sections_of(rels: dict) -> list[dict]:
    """Every section with its voices in rank order and its key and
    mode when said, **in the order the file places them** — which is
    the one fact this format carries by position on purpose
    (`notes.ges`: a section list is the author's sequence), so it is
    read off the `line` index and not off a sort."""
    at = {row["key"][0]: row["line"]
          for row in rels["line"].by("kind").get(("section",), ())}
    voices = rels["section.voices"].by("name")
    said = {field: rels[f"section.{field}"].by("name") for field in ("key", "mode")}
    prose = _prose_of(rels)
    out = []
    for row in sorted(rels["section"].rows, key=lambda r: at[r[0]]):
        one = dict(zip(rels["section"].heading, row))
        one["voices"] = tuple(v["value"] for v in
                              sorted(voices.get((one["name"],), ()), key=lambda v: v["rank"]))
        for field in ("key", "mode"):
            found = said[field].get((one["name"],))
            one[field] = found[0]["value"] if found else None
        one["line"] = at[one["name"]]
        one["above"], one["beside"] = prose(one["line"])
        out.append(one)
    return out


def notes_of(rels: dict) -> list[dict]:
    """Every note **as the file writes it**, in the declared order —
    one entry per written line, each joined with its spelling, its
    manners and its prose.

    **One per line and not one per fact**, because the file is a bag
    and the model is a set: a doubled line is one row of `note` and two
    of `line`, the renderer plays both, and a reader that drew one
    would be drawing a file nobody wrote.  The set is `rels["note"]`,
    for whoever wants the facts.

    The order is `facts.sort_key` over the declaration `ordered` obeys,
    then the line, so two identical notes keep the order they were read
    in — which is what makes a rewrite a no-op.
    """
    kind = _kinds()["note"]
    sections = sections_of(rels)
    #: **Indexed once, then joined** — `facts.Relation.by`.  A `.where`
    #: per note is a scan per row, and 291 notes on his piece made one
    #: read of the file eight times what it had been (measured
    #: 2026-09-10, `tools/notecost.py`).
    fields = rels["note"].by(*kind.key)
    spelt = rels["note.spell"].by(*kind.key)
    manners = rels["note.manner"].by(*kind.key)
    prose = _prose_of(rels)
    out = []
    for row in rels["line"].by("kind").get(("note",), ()):
        key = row["key"]
        one = dict(fields[key][0])
        said = spelt.get(key)
        one["spell"] = said[0]["value"] if said else None
        one["manner"] = tuple(m["value"] for m in
                              sorted(manners.get(key, ()), key=lambda m: m["rank"]))
        one["line"] = row["line"]
        one["above"], one["beside"] = prose(row["line"])
        out.append(one)
    return _in_order(sections, out)


def _in_order(sections: list, notes_: list) -> list:
    """Those notes in the file's declared order — `facts.sort_key` over
    `notes.ges`, then the line, so two identical notes keep the order
    they were read in and a rewrite is a no-op."""
    from .facts import sort_key

    kind = _kinds()["note"]
    place = {s["name"]: i for i, s in enumerate(sections)}
    voices = {s["name"]: s["voices"] for s in sections}
    return sorted(notes_, key=lambda one: sort_key(
        kind, one,
        along=lambda _k, _f, one: voices.get(one["section"], ()),
        #: A section that is not there sorts last rather than raising —
        #: `facts.sort_key`'s own rule for the other term, and what
        #: lets a retraction *write* the file it would leave and then
        #: be refused by the parser reading it back.
        among=lambda _k, named: place.get(named, len(place))) + (one["line"],))


def level_of(vel: str) -> int:
    """A dynamic's rank, softest first — what `Tone` carries."""
    return LEVELS.index(vel)


def bits_of(manner: tuple) -> int:
    """The manners as the bitmask `Tone` carries — an encoding, made at
    the reader and never stored."""
    bits = 0
    for one in manner:
        bits |= MANNERS[one]
    return bits


def refused(rels: dict, where=None) -> set:
    """`(kind, key)` of every record the integrity rules refuse — **the
    rules that no schema holds, run over the relations.**

    `card:relational-model.md` §"The sketch": the two references come
    from the declaration (`facts.dangling`), and the three below are
    what SQL called assertions and never implemented — a bar past its
    section's end, a tick past its bar, a spelling that names another
    key.  Empty on a file the parser accepts; every fixture the parser
    refuses for one of these reasons lands its key here, which is the
    parity `test_relations.py` holds while both exist.
    """
    from .facts import dangling

    document = _kinds(where)
    out = dangling(document, rels)
    note, section = rels["note"], rels["section"]
    bars = {row[section.column("name")]: (row[section.column("bars")],
                                          row[section.column("beats")])
            for row in section.rows}
    key_at = [note.column(c) for c in document["note"].key]
    for row in note.rows:
        s, bar, at = (row[note.column("section")], row[note.column("bar")],
                      row[note.column("at")])
        if s not in bars:
            continue
        if bar > bars[s][0] or at >= bars[s][1] * TICKS_PER_BEAT:
            out.add(("note", tuple(row[i] for i in key_at)))
    spell = rels["note.spell"]
    for row in spell.rows:
        k = row[:spell.column("value")]
        if key_of(row[spell.column("value")]) != k[spell.column("key")]:
            out.add(("note", k))
    return out


def _section(tokens: list[str], kind, place: str) -> dict:
    """One `section` record, checked in the author's terms."""
    if not tokens or not _NAME.match(tokens[0]):
        raise NotesError(
            f"{place}: `section` needs a name — `section A key D bars 8 "
            "beats 4 voices melody,roots`")
    got = _fields(tokens[1:], kind, place)
    bars = _int(got["bars"], "bars", place)
    beats = _int(got["beats"], "beats", place)
    if bars < 1:
        raise NotesError(f"{place}: `bars {bars}` — a section has at least one bar")
    if beats < 1:
        raise NotesError(f"{place}: `beats {beats}` — a bar has at least one beat")
    voices = tuple(v for v in got["voices"].split(",") if v)
    if not voices:
        raise NotesError(f"{place}: `voices` names none")
    for one in voices:
        if not _NAME.match(one):
            raise NotesError(f"{place}: `{one}` is not a voice name")
    if len(set(voices)) != len(voices):
        raise NotesError(f"{place}: a voice is named twice in `voices`")
    key, mode = got.get("key"), got.get("mode")
    if key is not None and key not in _PITCH_CLASS:
        raise NotesError(
            f"{place}: `key {key}` is not a note name; "
            + ", ".join(sorted(_PITCH_CLASS)))
    if mode is not None and mode.lower() not in _MODES:
        raise NotesError(
            f"{place}: `mode {mode}` is not one this knows; "
            + ", ".join(sorted(_MODES)))
    return {"name": tokens[0], "key": key, "mode": mode,
            "bars": bars, "beats": beats, "voices": voices}


def bar_ticks(section: dict) -> int:
    """How many ticks one bar of this section is."""
    return section["beats"] * TICKS_PER_BEAT


def at_line(rels: dict, line: int) -> dict | None:
    """The note written on that line of the file, or `None`.

    **The one lookup a gesture makes**: the roll points at a line and
    the editor asks what note is there.  It goes through the `line`
    index rather than through a scan, because a line *is* the index —
    `card:relational-model.md` scar 3, where the picture's row and the
    model's key are held apart on purpose.
    """
    return next((one for one in notes_of(rels) if one["line"] == line), None)


def named(rels: dict, name: str) -> dict | None:
    """The section of that name, or `None`."""
    return next((one for one in sections_of(rels) if one["name"] == name), None)


def _note(tokens: list[str], kind, place: str, by_name: dict,
          sections: list) -> dict:
    """One `note` record, checked in the author's terms.

    **The order of the refusals is the author's, not the
    declaration's**: a line with two faults earns the one a person
    would fix first.  `records` checks the same file by the declaration
    alone, and `test_notes_relations.py` holds the two to one boundary
    per field; what lives here is the *sentence*, which
    `card:error-messages.md` paid for.
    """
    got = _fields(tokens, kind, place)
    section = by_name.get(got["section"])
    if section is None:
        raise NotesError(
            f"{place}: no section `{got['section']}`; this file has "
            + (", ".join(f"`{s['name']}`" for s in sections) or "none"))
    bar = _int(got["bar"], "bar", place)
    if not 1 <= bar <= section["bars"]:
        raise NotesError(
            f"{place}: `bar {bar}` — section `{section['name']}` has "
            f"{section['bars']} bars")
    tick = _int(got["at"], "at", place)
    if not 0 <= tick < bar_ticks(section):
        #: The friction this refusal is: W3 of
        #: `doc/notes/notes-on-writing-a-piece.md` — *"a fifth note in `a3`
        #: would compile, shift everything after it by a beat, and be found
        #: by ear an hour later."*  It does not compile here.
        raise NotesError(
            f"{place}: `at {tick}` is not inside bar {bar} of section "
            f"`{section['name']}`, which is {section['beats']} beats "
            f"({bar_ticks(section)} ticks) long")
    length = _int(got["len"], "len", place)
    if length < 1:
        raise NotesError(f"{place}: `len {length}` — a note lasts at least one tick")
    if got["voice"] not in section["voices"]:
        raise NotesError(
            f"{place}: section `{section['name']}` has no voice `{got['voice']}`; "
            "it has " + ", ".join(f"`{v}`" for v in section["voices"]))
    key = _int(got["key"], "key", place)
    if not 0 <= key <= 127:
        raise NotesError(f"{place}: `key {key}` is not a MIDI key number (0-127)")
    if got["vel"] not in LEVELS:
        raise NotesError(
            f"{place}: `vel {got['vel']}` is not a dynamic; "
            + " ".join(LEVELS))
    return {"section": section["name"], "bar": bar, "at": tick, "len": length,
            "voice": got["voice"], "key": key,
            "spell": _spelled(got.get("spell"), key, place),
            "vel": got["vel"], "manner": _manners(got.get("manner"), place)}


def _spelled(spell: str | None, key: int, place: str) -> str | None:
    """The written spelling, or the refusal that it names another note.

    **A file may choose the letter and may not choose the note.**  That
    is the whole safety of storing a spelling at all: `cis5` and `des5`
    are both key 73 and either may be written, but `spell des5` on `key
    60` would make the report say a pitch the render does not play, and
    nothing downstream could catch it.
    """
    if spell is None:
        return None
    named = key_of(spell)
    if named is None:
        raise NotesError(
            f"{place}: `spell {spell}` is not a pitch name — a letter, an "
            "optional `is`/`es`/`isis`/`eses`, and an octave, as `cis5`")
    if named != key:
        raise NotesError(
            f"{place}: `spell {spell}` names key {named}, and this note is "
            f"`key {key}`")
    return spell


def _manners(text: str | None, place: str) -> tuple:
    """The manners a line asks for, in the file's own order and each
    once — **the names, not a bitmask.**  `bits_of` makes the mask
    where a reader needs one, at that reader."""
    if text is None:
        return ()
    out: list[str] = []
    for one in text.split(","):
        if not one:
            continue
        if one not in MANNERS:
            raise NotesError(
                f"{place}: `{one}` is not a manner; "
                + " ".join(sorted(MANNERS)))
        if one in out:
            raise NotesError(f"{place}: `{one}` is asked for twice")
        out.append(one)
    return tuple(out)


def doubled(rels: dict) -> list:
    """`[(first, second)]` — notes at one place a drag cannot tell apart.

    One voice, one bar, one tick, one key, twice.  **Allowed in the file
    and refused at the gesture**, which is the shape Henri chose on
    2026-09-05 after a half-written sketch was rejected wholesale:
    *"lets do the middle one.  I think that's fairly fair."*

    **The constraint belongs on the gesture, not on the bytes.**  What is
    genuinely impossible is a *drag*: two identical lines, and nothing in
    a click says which to rewrite, so `spec/north_star.md`'s byte-exact
    law has no answer.  Writing them by hand is merely redundant — the
    renderer plays both, which is louder, and that is what the file
    honestly says.

    The first draft of this refused at `parse`, on the argument that a
    file should not be able to say something it cannot mean.  It can mean
    it; it is the *editor* that cannot act on it.  And the cost of
    getting that wrong was paid by the person the format is for, in the
    middle of a sketch, which is the worst moment to be stopped.

    Round-tripping is unaffected: two identical notes sort adjacently and
    `sorted` is stable, so `write` emits them in the order they were read
    and reading that back is a no-op.
    """
    seen: dict = {}
    pairs = []
    for one in notes_of(rels):
        spot = tuple(one[c] for c in _kinds()["note"].key)
        if spot in seen:
            pairs.append((seen[spot], one))
        else:
            seen[spot] = one
    return pairs


# ── The stable order, and writing one back ──# ── The stable order, and writing one back ──────────────────────────────────


def write(rels: dict) -> str:
    """A `.notes` file, in the canonical order and the canonical spelling.

    Reading a file this wrote and writing it again is a no-op, which is
    what makes a gesture on the roll able to rewrite one line without
    disturbing the file around it.

    **And every comment comes back**, above the record it was written
    above or beside the record it was written beside — `fixme.md` F200.
    What this does *not* keep is a blank line inside a run of prose: the
    house spelling for that is a bare `#`, which `arc.ges` already uses,
    and a canonical writer that guessed at blank lines would have a
    second thing to be canonical about.
    """
    return _rendered(sections_of(rels), notes_of(rels), _bpm_line(rels),
                     tuple(one["text"] for one in
                           sorted(rels["closing"].where(), key=lambda o: o["rank"])))


def _bpm_line(rels: dict) -> dict | None:
    """The `bpm` record with its prose, or `None` — the one fact a
    document has at most one of."""
    said = bpm_of(rels)
    if said is None:
        return None
    at = rels["line"].where(kind="bpm")
    line = at[0]["line"] if at else 0
    above, beside = _prose_of(rels)(line)
    return {"bpm": said, "line": line, "above": above, "beside": beside}


def _rendered(sections: list, notes_: list, bpm: dict | None,
              closing: tuple) -> str:
    """The file those records make — the one writer, so that `write`
    and the two primitive edits put a line together once."""
    lines: list[str] = []
    if bpm is not None:
        # First, as the one fact about the whole file — and so a
        # `tempo` that writes one into a file without it writes line 1.
        lines += list(bpm["above"])
        lines.append(f"bpm {bpm['bpm']}"
                     + (f"  {bpm['beside']}" if bpm["beside"] else ""))
    for one in sections:
        lines += list(one["above"])
        head = [f"section {one['name']}"]
        if one["key"] is not None:
            head.append(f"key {one['key']}")
        if one["mode"] is not None:
            head.append(f"mode {one['mode']}")
        head += [f"bars {one['bars']}", f"beats {one['beats']}",
                 "voices " + ",".join(one["voices"])]
        lines.append("  ".join(head) + (f"  {one['beside']}" if one["beside"] else ""))
    lines.append("")
    at_bar = None
    for one in notes_:
        if (one["section"], one["bar"]) != at_bar:
            if at_bar is not None:
                lines.append("")
            at_bar = (one["section"], one["bar"])
        lines += list(one["above"])
        lines.append(_line(one))
    lines += list(closing)
    return "\n".join(lines) + "\n"


#: **The two primitive edits#: **The two primitive edits — `card:gui-is-difficult.md`, 2026-09-09.**
#: A document's algebra is *assert*, *retract* and *set*, and setting a
#: field is the pair; `retune` above is the derived one and had been
#: built for a year of afternoons before either of these existed,
#: because a gesture on the roll can only move a note that is already
#: there.  Adding and deleting were **typing**, in the buffer, outside
#: the command language and outside the gesture language — which is why
#: they are the two edits that drop a selection.
#:
#: Both go through `parse` and `write` rather than through the text, so
#: a record's own prose travels with it: `fixme.md` F200 decided that
#: the lines above a record *belong* to it, and a retraction that left
#: them behind would silently re-attach somebody's sentence to the next
#: note down.


def asserted(text: str, written: str, name: str = "<notes>",
             where=None) -> tuple:
    """`(text, said)` — the document with one record added.

    `written` is a line in the document's own syntax, which is the whole
    of the argument: the command language does not restate the fields,
    because the declaration beside the document already has them.

    Refused when the line does not parse *in this document* — a note
    naming no section, a bar past the section's end — with the parser's
    own words, and when the key is already written: **a doubled line is
    one note said twice** (`notes.doubled`, his *"the middle one"*), so
    asserting one that is already there is a gesture with nothing to do.
    """
    rels = parse(text, name, where=where)
    document = _kinds(where)
    sections, notes_ = sections_of(rels), notes_of(rels)
    line, _beside = _uncomment(written)
    tokens = line.split()
    place = f"{name}: the asserted record"
    if not tokens:
        raise NotesError(f"{place} is empty")
    word = tokens[0]
    place = f"{name}: the asserted `{word}`"
    kind = document.kind(word)
    if kind is None:
        raise NotesError(
            f"{place}: `{word}` is not a record; a line is "
            + _oneof([f"`{k} …`" for k in document.names]))
    if word not in ("note", "section"):
        raise NotesError(
            f"{place}: `{word}` cannot be added by hand; this version "
            "asserts a note or a section")
    #: A record added by hand carries no prose and no line — it was not
    #: written anywhere yet, and the line it lands on is the writer's to
    #: decide.  `0` sorts it before an identical one, which cannot
    #: happen, because a doubled key is refused just below.
    fresh = {"line": 0, "above": (), "beside": None}
    if word == "section":
        one = {**_section(tokens[1:], kind, place), **fresh}
        if any(s["name"] == one["name"] for s in sections):
            raise NotesError(f"{place}: section `{one['name']}` is already written")
        sections.append(one)
        said = f"section {one['name']}"
    else:
        by_name = {s["name"]: s for s in sections}
        one = {**_note(tokens[1:], kind, place, by_name, sections), **fresh}
        for other in notes_:
            if _key(kind, other) == _key(kind, one):
                raise NotesError(
                    f"{place}: that note is already written, on line "
                    f"{other['line']} — a doubled line is one note said twice")
        notes_.append(one)
        notes_ = _in_order(sections, notes_)
        said = (f"note {one['key']} at {one['at']} in bar {one['bar']}, "
                f"voice {one['voice']}")
    return (_rendered(sections, notes_, _bpm_line(rels), _closing(rels)),
            f"asserted {said}")


def retracted(text: str, key: str, name: str = "<notes>",
              where=None) -> tuple:
    """`(text, said)` — the document with one record's fact removed.

    `key` is the record's **key**, written in the document's own
    syntax: `note section A bar 1 voice melody at 0 key 62`, or
    `section A`.  Which fields those are is the declaration's, so this
    refuses a key with a field too many or too few and names the ones
    it wanted.

    **And a retraction that would leave the document unreadable is
    refused, with the parser as the oracle.**  Nothing in a `.notes`
    stores a derived fact — the roll, the sound and the picture are all
    recomputed from it — so the only dependency inside the document is
    one record naming another, and the parser already refuses a note
    whose section is not there.  So there is no cascade to write and no
    dependency graph to keep: *the document is retracted from, re-read,
    and the refusal it earns is the answer.*  Henri, 2026-09-09:
    *"retraktoidun faktan johdetut faktat pitää jotenkin kadottaa.
    retraktio saattaa tarkoittaa uudelleenlaskentaa."*  Outside the
    document it does mean exactly that, and nothing here has to know.
    """
    rels = parse(text, name, where=where)
    document = _kinds(where)
    sections, notes_ = sections_of(rels), notes_of(rels)
    line, _beside = _uncomment(key)
    tokens = line.split()
    place = f"{name}: the retracted record"
    if not tokens:
        raise NotesError(f"{place} is empty")
    word = tokens[0]
    place = f"{name}: the retracted `{word}`"
    kind = document.kind(word)
    if kind is None:
        raise NotesError(
            f"{place}: `{word}` is not a record; a line is "
            + _oneof([f"`{k} …`" for k in document.names]))
    wanted = _given_key(kind, tokens[1:], place)
    if word == "section":
        gone = [one for one in sections if one["name"] == wanted["name"]]
        sections = [one for one in sections if one not in gone]
    elif word == "note":
        gone = [one for one in notes_ if _key(kind, one) == tuple(
            wanted[f] for f in kind.key)]
        notes_ = [one for one in notes_ if one not in gone]
    else:
        raise NotesError(
            f"{place}: `{word}` cannot be retracted by hand; this version "
            "retracts a note or a section")
    if not gone:
        raise NotesError(f"{place}: no `{word}` here says that")
    made = _rendered(sections, notes_, _bpm_line(rels), _closing(rels))
    try:
        parse(made, name, where=where)
    except NotesError as why:
        raise NotesError(
            f"{place}: retracting it would leave the file unreadable — "
            f"{why}") from None
    #: **Every line that said it goes**, not the first: two identical
    #: lines are one note said twice, so retracting the note retracts
    #: the saying of it.
    lines = "" if len(gone) == 1 else f", written on {len(gone)} lines"
    return made, f"retracted {word} {' '.join(tokens[1:])}{lines}"


def _key(kind, one: dict) -> tuple:
    """A record's key, as the declaration names it, written as a person
    writes it — so that a key given on the command line compares."""
    return tuple(str(one[f]) for f in kind.key)


def _closing(rels: dict) -> tuple:
    """The prose after the last record, which no record follows."""
    return tuple(one["text"] for one in
                 sorted(rels["closing"].where(), key=lambda o: o["rank"]))


def _given_key(kind, tokens: list[str], place: str) -> dict:
    """The key a person wrote, read against the declaration's.

    A `Headed` kind's key is the bare name after the word; a `Named`
    kind's is field-and-value pairs.  Exactly the key fields, so a
    retraction cannot half-name a record and take the wrong one.
    """
    if kind.shape[0] == "Headed":
        if len(tokens) != 1:
            raise NotesError(
                f"{place}: name one `{kind.name}` — its key is its "
                f"`{kind.shape[1]}`")
        return {kind.shape[1]: tokens[0]}
    got: dict[str, str] = {}
    rest = list(tokens)
    while rest:
        field = rest.pop(0)
        if not rest:
            raise NotesError(f"{place}: `{field}` has no value")
        got[field] = rest.pop(0)
    if set(got) != set(kind.key):
        raise NotesError(
            f"{place}: a `{kind.name}` is named by "
            + ", ".join(f"`{f}`" for f in kind.key)
            + " and this says "
            + (", ".join(f"`{f}`" for f in sorted(got)) or "nothing"))
    return got


def canonical(text: str, name: str = "<notes>") -> str:
    """The same file, in the file's own order — what a gesture writes.

    **The file is a table.**  Henri, 2026-09-08, closing
    `card:gui-is-difficult.md` Q7: *"nuotti saisi lajittua siihen
    järjestykseen mikä on tiedostolle sovittu."*  So a note moved in
    time does not keep the line it was typed on; it sorts to where it
    sounds, and every gesture's write goes through here — `retune`
    rewrites the field, this puts the line in its place, and both are
    byte-exact on everything else (measured on every note of
    `arc.notes`: `key` and `len` identical to the in-place rewrite,
    `at` the same lines in canonical order).  A file the parser refuses
    is returned as it came, so a gesture still lands on a file with a
    mistake elsewhere in it.
    """
    try:
        return write(parse(text, name))
    except NotesError:
        return text


def _line(one: dict) -> str:
    #: `spell` goes beside `key`, because it is about that field and
    #: nothing else — and it is absent on almost every line, which is
    #: the point: a spelling is written only where the rule would get it
    #: wrong.  Gate four holds either way, the order being fixed here.
    out = (f"note  section {one['section']}  bar {one['bar']}  at {one['at']}  "
           f"len {one['len']}  voice {one['voice']}  key {one['key']}  "
           + (f"spell {one['spell']}  " if one["spell"] else "")
           + f"vel {one['vel']}")
    #: **The manners in the file's own order**, which is the order they
    #: were read in: `manner` is a `Names` field and its rank is a fact
    #: (`facts.relations`), so nothing here sorts them.
    out += "  manner " + ",".join(one["manner"]) if one["manner"] else ""
    return out + (f"  {one['beside']}" if one["beside"] else "")


# ── Rewriting one field of one line ─────────────────────────────────────────

#: A named field and its value, on a note line.  **Named, so the rewrite
#: needs no column arithmetic** — which is the whole reason
#: `spec/drawnscores.md` gate two exists, met from the other side: the
#: same property that stops two fields telling apart by position is what
#: lets an editor find one without counting.
_FIELD = r"(\b{0} )(\S+)"


def retune(text: str, line: int, field: str, was, now) -> tuple:
    """`(text, said)` — one field of one line, rewritten byte-exactly.

    `spec/north_star.md`'s law for a `.notes` file: **one field's bytes
    change and nothing else.**  Every other character of the file,
    including every other field of this very line, is the same
    afterwards — which is what makes a drag safe to undo by dragging
    back.  Since 2026-09-08 the line then goes to the file's own order
    (`canonical`), which moves it and changes no byte of it.

    Refused rather than forced when the line is not a note, when it has
    no such field, or when the field does not currently say `was` — the
    last being *the file has moved under the picture*, the same guard
    `scorebox.transposed` keeps and for the same reason.
    """
    import re

    lines = text.splitlines(keepends=True)
    place = f"line {line}"
    if not 0 < line <= len(lines):
        raise NotesError(f"{place} is not in this file any more")
    row = lines[line - 1]
    # **A note's line, or a section's** — the section record's `bars` is
    # rewritten the same way when its end is dragged (`card:notes-editor.md`
    # slice 4, *resize the clip*), one field's bytes and nothing else.
    if not row.lstrip().startswith(("note ", "section ", "bpm ")):
        raise NotesError(f"{place} is not a record — a line is `section …`, `note …` or `bpm …`")
    #: **Only the record half is rewritten.**  A line may carry prose
    #: (`fixme.md` F200) and that prose may say anything at all — `# the
    #: key 70 next door` — so a search over the whole line could edit a
    #: sentence and call it a drag.
    record, _said = _uncomment(row)
    found = re.search(_FIELD.format(re.escape(field)), record)
    if found is None:
        raise NotesError(f"{place} has no `{field}` to change")
    if found.group(2) != str(was):
        raise NotesError(
            f"{place} says `{field} {found.group(2)}` where the roll "
            f"thought `{field} {was}` — the file has moved under the picture")
    row = row[:found.start(2)] + str(now) + row[found.end(2):]
    said = f"{field} {was} → {now} on line {line}"

    #: **A drag in pitch drops the spelling the note was written with**,
    #: and says so.  The stored letter is an intention about the *old*
    #: pitch — `cis5` because it resolves up to `d` — and no rule can
    #: carry that to the note it became; keeping it would leave the line
    #: contradicting itself, which `Note.__post_init__` refuses anyway.
    #: So the field goes, the gesture names it, and the person writes
    #: the new one if they meant one.  `spec/drawnscores.md` §"The
    #: spelling a rule cannot guess".
    if field == "key" and row.lstrip().startswith("note "):
        for one in re.finditer(r"\s+spell (\S+)", _uncomment(row)[0]):
            if key_of(one.group(1)) == int(was):
                row = row[:one.start()] + row[one.end():]
                said += f", and `spell {one.group(1)}` with it"
                break

    lines[line - 1] = row
    return "".join(lines), said


# ── The lamp: what the mode says, and what it never does ────────────────────


def outside(rels: dict) -> list[tuple[dict, int]]:
    """Notes outside their section's declared mode — `(note, degree)`.

    **Reports, never refuses**, which is decision 3 of the spec.  A ♯11
    over a dominant is idiomatic and is the whole of `arc.ges`'s A
    section; a gate here would refuse the blues.  A section that declares
    no `key` or no `mode` says nothing and is silent rather than guessed
    at.
    """
    found = []
    by_name = {s["name"]: s for s in sections_of(rels)}
    for one in notes_of(rels):
        section = by_name.get(one["section"])
        if section is None or section["key"] is None or section["mode"] is None:
            continue
        degree = (one["key"] - _PITCH_CLASS[section["key"]]) % 12
        if degree not in _MODES[section["mode"].lower()]:
            found.append((one, degree))
    return found


# ── What a bar sounds, said in words ────────────────────────────────────────

#: The twelve, named against the tonic the way a musician names them —
#: `♯4`, `♭7` — rather than against the mode.  Mode-independent on
#: purpose: *the sharp fourth* means the same thing whether or not the
#: mode contains it, which is exactly the case worth reporting.
DEGREES = ("1", "♭2", "2", "♭3", "3", "4", "♯4", "5", "♭6", "6", "♭7", "7")

#: The letter each natural sits on, and the seven in order.
_NATURAL = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
_LETTERS = "cdefgab"
_MARKS = {-2: "eses", -1: "es", 0: "", 1: "is", 2: "isis"}

#: A pitch name as `spell` writes one: a letter, an optional accidental,
#: an octave — `cis5`, `des4`, `fisis3`, `a4`, `c-1`.
_SPELLED = re.compile(r"^([a-g])(isis|is|eses|es)?(-?\d+)$")


def key_of(name: str) -> int | None:
    """The MIDI key a spelling names, or `None` if it is not a spelling.

    **`spell`'s inverse, and it is total where `spell` is not.**  Many
    names reach one key — `cis5` and `des5` are both 73 — so this
    direction is a function and the other one has to choose, which is
    the whole reason a written spelling exists.  It is what makes the
    field checkable rather than decorative: a file may say a letter the
    rule would not have picked, and may not say a letter that is a
    different note.
    """
    found = _SPELLED.match(name)
    if found is None:
        return None
    letter, mark, octave = found.groups()
    delta = {v: k for k, v in _MARKS.items()}[mark or ""]
    return _NATURAL[letter] + (int(octave) + 1) * 12 + delta


#: The major scale, which every degree name is measured against — that
#: is what makes `♭3` and `♯4` mean the same thing in every mode.
_MAJOR = (0, 2, 4, 5, 7, 9, 11)


def degree_of(key: int, tonic: str, mode: str | None = None) -> str:
    """`♯4` — where this pitch stands against the tonic.

    **The mode decides which name a tone wears when it owns it.**  Six
    semitones above the tonic is lydian's `♯4` and locrian's `♭5` — the
    same pitch, a different scale position, and calling locrian's `♭5` a
    sharp fourth would misname the interval this tree's own log keeps
    talking about.  So where the mode contains the tone, its *position*
    in the mode names it; where it does not, the chromatic reading does,
    because a tone outside the scale has no position in it.
    """
    away = (key - _PITCH_CLASS[tonic]) % 12
    steps = _MODES[mode.lower()] if mode else ()
    if away in steps:
        place = steps.index(away)
        mark = {-1: "♭", 0: "", 1: "♯"}.get(away - _MAJOR[place])
        if mark is not None:
            return f"{mark}{place + 1}"
    return DEGREES[away]


def spell(key: int, tonic: str, mode: str) -> str:
    """`gis4` — the pitch, spelled the way its mode asks for.

    **The letter comes from the degree, not from the pitch**, which is
    what an accidental *is*: a raised fourth keeps the fourth's letter
    and takes a sharp, so `gis` and `g` sit on one line of a stave and a
    reader sees the alteration rather than a different note.

    *Derived and never stored* — `spec/drawnscores.md` §"The three
    spellings, and two of them are derived".  The file keeps the MIDI
    number, because that is what a drag rewrites and what the roll
    points at; this is a view over it, and a view costs nothing because
    nothing round-trips through a report.

    **The one place it must choose, and the limit is named:** a pitch the
    mode does not contain could be a raised degree or a lowered one.
    **Nearest degree first, then the smallest accidental**, and neither
    half is taste.  *Nearest* because a pitch the mode contains is that
    degree and nothing else: D lydian's third is `fis4`, and reaching it
    as a flattened ♯4 gives `ges4`, which is one accidental too and is a
    different note on the page.  A first pass sorted on the accidental
    alone and produced exactly that, on a file the `.notes` path had
    already spelled correctly.

    Then *the smallest accidental*, which is not taste either: the
    natural fourth of D lydian is `g4` — the ♯4 lowered, needing none —
    where sharpening the third would spell it `fisis4`, and the natural
    second of D phrygian is `e4` rather than `fes4` for the same reason.
    A first draft preferred the flat unconditionally and produced that
    `fes4`, which is how this rule was found.

    Where **both** readings cost exactly one accidental — D♯ against E♭
    in D — this takes the flat.  That is the one arbitrary choice here,
    and a piece that wants the other is **the case that would put names
    in the file**; until one turns up the spelling is a report's
    business, correctable by re-running it.
    """
    steps, base = _MODES[mode.lower()], _PITCH_CLASS[tonic]
    root = _LETTERS.index(tonic[0].lower())
    away = (key - base) % 12
    found = []
    for shift in (0, -1, 1, -2, 2):
        if (away - shift) % 12 not in steps:
            continue
        index = steps.index((away - shift) % 12)
        letter = _LETTERS[(root + index) % 7]
        for octave in range(-1, 10):
            delta = key - (_NATURAL[letter] + (octave + 1) * 12)
            if -2 <= delta <= 2:
                found.append((abs(shift), abs(delta), delta, letter, octave))
                break
    if not found:
        return str(key)                   # no letter reaches it; say the number
    _far, _size, delta, letter, octave = min(found)
    return f"{letter}{_MARKS[delta]}{octave}"


#: The picture's spelling of a raised and a lowered degree.
#:
#: **Not `♯` and `♭`, because the canvas font has neither** — nor any
#: lowercase, the walk upper-casing every label — so `b7` would draw as
#: `B7` and read as the note B.  `+` and `-` are in the font, cannot be
#: mistaken for a letter, and say the one thing the band is for: this
#: degree is raised or lowered out of the mode the section declared.
#: `tools/bars.py` keeps `♯` and `♭`; a terminal has the glyphs.
RAISED, LOWERED = "+", "-"


def harmony(rels: dict) -> list:
    """`[(section, bar, [(degree, inside, name)])]` — what each bar
    sounds, as degrees against its section's **declared** mode.

    **The thing no engraver can answer**, and the reason this is a view
    of its own (`card:notes-editor.md`, the score view, 2026-09-11):
    notation software infers a key from the notes and can then only
    draw an accidental.  A `.notes` section *states* its key and mode,
    so a note leaving them is a **fact** rather than a guess — which is
    what `outside` reports and what the band lights.

    Degrees are distinct and low to high, the order a chord is read in.
    A section that declares no key or no mode says nothing, the same
    silence `outside` keeps and for the same reason.
    """
    by_name = {s["name"]: s for s in sections_of(rels)}
    out = []
    for section, bar, keys in sounding(rels):
        one = by_name.get(section)
        if one is None or one["key"] is None or one["mode"] is None:
            continue
        scale = _MODES[one["mode"].lower()]
        tonic = _PITCH_CLASS[one["key"]]
        seen, row = set(), []
        for key in keys:
            step = (key - tonic) % 12
            if step in seen:
                continue
            seen.add(step)
            inside = step in scale
            row.append((step, inside, _degree_name(step, scale)))
        out.append((section, bar, row))
    return out


def _degree_name(step: int, scale) -> str:
    """A degree as the band draws it: its number in the seven, with
    `+`/`-` where it is raised or lowered out of the mode.

    Against the **mode**, not against the major scale, because the band
    is about this section's own seven: in D lydian the ♯4 *is* the
    fourth degree and reads as `4`, and it is the G natural — a fourth
    the mode does not have — that reads as `-4`.  That is the reading
    `arc.notes`' A section makes obvious and the one a report against
    the tonic cannot make.
    """
    for n, at in enumerate(sorted(scale), start=1):
        if step == at:
            return str(n)
    below = [n for n, at in enumerate(sorted(scale), start=1) if at < step]
    above = [n for n, at in enumerate(sorted(scale), start=1) if at > step]
    if above:
        return LOWERED + str(above[0])
    return RAISED + str(below[-1] if below else 7)


def sounding(rels: dict) -> list:
    """`[(section, bar, [keys low to high])]` — what is heard in each bar.

    A note counts in every bar it is still sounding in, because a held
    root under four bars is part of all four — which is the thing a list
    of note *starts* cannot say and the reason
    `card:the-first-jam.md` item 2 exists.
    """
    heard: dict = {}
    sections = sections_of(rels)
    by_name = {s["name"]: s for s in sections}
    for one in notes_of(rels):
        section = by_name.get(one["section"])
        if section is None:
            continue
        last = one["bar"] + (one["at"] + one["len"] - 1) // bar_ticks(section)
        for bar in range(one["bar"], min(last, section["bars"]) + 1):
            heard.setdefault((one["section"], bar), set()).add(one["key"])
    order = {s["name"]: i for i, s in enumerate(sections)}
    return [(s, b, sorted(keys)) for (s, b), keys
            in sorted(heard.items(), key=lambda kv: (order[kv[0][0]], kv[0][1]))]


def spellings(rels: dict) -> dict:
    """`{(section, bar, key): name}` — the spellings the file wrote out.

    A note's spelling holds for every bar it sounds in, the same walk
    `sounding` makes and for the same reason: a held note is part of
    every bar it is heard in, and the letter it was written with is part
    of it.

    **Where one bar spells one key twice, the canonical order decides**
    — the first note of `ordered` wins.  That is a limit of a bar-wise
    view and not of the file: two voices may legitimately write a `cis`
    and a `des` at once, and both lines stay exactly as written.  Only
    this column has to pick one.
    """
    said: dict = {}
    by_name = {s["name"]: s for s in sections_of(rels)}
    for one in notes_of(rels):
        if one["spell"] is None:
            continue
        section = by_name.get(one["section"])
        if section is None:
            continue
        last = one["bar"] + (one["at"] + one["len"] - 1) // bar_ticks(section)
        for bar in range(one["bar"], min(last, section["bars"]) + 1):
            said.setdefault((one["section"], bar, one["key"]), one["spell"])
    return said


def rows_of_notes(path) -> list:
    """`(section, bar, keys, tonic, mode, spelled)` from a file's own headers.

    `spelled` is `{key: name}` for that bar — empty wherever the file
    wrote no spelling, which is almost everywhere.
    """
    path = Path(path)
    rels = parse(path.read_text(), path.name, where=path)
    modes = {s["name"]: (s["key"], s["mode"]) for s in sections_of(rels)}
    said = spellings(rels)
    return [(s, b, keys) + modes[s]
            + ({k: said[(s, b, k)] for k in keys if (s, b, k) in said},)
            for s, b, keys in sounding(rels)]


def report(rows: list, tell=print) -> None:
    at = None
    for section, bar, keys, tonic, mode, spelled in rows:
        if (section, tonic, mode) != at:
            at = (section, tonic, mode)
            head = f"── {'section ' + section if section else 'the piece'}"
            tell(f"{head} — {tonic} {mode}" if tonic and mode else head)
            tell(f"   {'bar':>3}  {'sounding':<34} {'degrees':<26} outside")
        if tonic and mode:
            #: **A written spelling wins over the derived one**, which is
            #: the whole of the field: the rule takes the flat where two
            #: readings cost one accidental each, and `arc.notes`' final
            #: cadence is a `cis` resolving up to `d`.  Everywhere else
            #: this map is empty and the rule answers, as it did before.
            def named(k, _t=tonic, _m=mode, _s=spelled):
                return _s.get(k) or spell(k, _t, _m)

            names = " ".join(named(k) for k in keys)
            steps = _MODES[mode.lower()]
            marks = " ".join(degree_of(k, tonic, mode) for k in keys)
            #: **Named, not counted.**  A count says a bar is wrong; a
            #: name says which note, and the note is what an author
            #: decides about.  `arc.notes`' one out-of-mode note in
            #: section A is a `g4` where the mode's fourth is `gis` —
            #: which is `doc/notes/notes-on-writing-a-piece.md` W2's own
            #: sentence, and it is not a typo.
            odd = [named(k) for k in keys
                   if (k - _PITCH_CLASS[tonic]) % 12 not in steps]
        else:
            names = " ".join(str(k) for k in keys)
            marks, odd = "", []
        tell(f"   {bar:>3}  {names:<34} {marks:<26} "
             + (" ".join(odd) if odd else "—"))


# ── The expansion into `.ges` ───────────────────────────────────────────────

#: The name a voice of a section becomes.  Underscored and prefixed
#: because it is generated: nothing an author types can collide with it,
#: and a name in an error message that nobody wrote is the failure
#: `audiovoices._rewrite_dots` names.
def bound(section: str, voice: str) -> str:
    return f"notes_{section}_{voice}"


def _payload(one: dict) -> str:
    return f"'(fromNote {one['key']} {level_of(one['vel'])} {bits_of(one['manner'])})"


def _held(one: dict) -> str:
    """A note of `one.length` ticks, out of the beat-long note `'x` is.

    `|*` scales a duration and `|/` divides it, both by whole numbers, so
    `L` ticks is `96 * p / q` with `p/q` reduced — and it is exact for
    every `L`, because `q` divides `96 * p` by construction.  This is
    where the 96-tick grid pays for itself: no fraction reaches the
    format and no special case reaches the editor.
    """
    body = _payload(one)
    common = gcd(one["len"], TICKS_PER_BEAT)
    up, down = one["len"] // common, TICKS_PER_BEAT // common
    if up != 1:
        body = f"({body} |* {up})"
    if down != 1:
        body = f"({body} |/ {down})"
    return body


def _placed(one: dict) -> str:
    body = _held(one)
    return body if one["at"] == 0 else f"(at {one['at']} {body})"


def declarations(rels: dict) -> tuple[str, dict[int, int]]:
    """The `.ges` text a file becomes, and `{generated line: source line}`
    — **read off the relations**, `notes_of` and `sections_of`.

    The map is what carries provenance: a note is one generated line, so
    a graph node placed on generated line 41 was written on whatever line
    of the `.notes` file the map says.  `audiospans.Site` already names a
    file and a line within it, so this is the last piece that reading was
    missing.
    """
    lines: list[str] = []
    origin: dict[int, int] = {}
    order = notes_of(rels)
    for section in sections_of(rels):
        for voice in section["voices"]:
            mine = [n for n in order
                    if n["section"] == section["name"] and n["voice"] == voice]
            lines.append(f"{bound(section['name'], voice)} : (FromNote a) => [: a :]")
            lines.append(f"{bound(section['name'], voice)} =")
            for index in range(1, section["bars"] + 1):
                inside = [n for n in mine if n["bar"] == index]
                lead = "      " if index == 1 else "   ++ "
                if not inside:
                    lines.append(f"{lead}(long {section['beats']} r)")
                    continue
                lines.append(f"{lead}(long {section['beats']} (")
                for spot, one in enumerate(inside):
                    joint = "        " if spot == 0 else "     || "
                    lines.append(f"{joint}{_placed(one)}")
                    origin[len(lines)] = one["line"]
                lines.append("      ))")
            lines.append("")
    return "\n".join(lines), origin


#: `include "arc.notes"` — the door, and the only new line of `.ges` this
#: whole design adds.  A path, in quotes, resolved relative to the file
#: that wrote it, which is what `session.py`'s `open` already does for a
#: person.
_INCLUDE = re.compile(r'^([ \t]*)include[ \t]+"([^"]*)"[ \t]*$', re.M)


def includes(source: str) -> list[str]:
    """The paths a program includes, in the order it writes them."""
    return [m.group(2) for m in _INCLUDE.finditer(source)]


def expand(source: str, base: Path | None = None) -> str:
    """`source` with its `include` lines blanked and their notes appended.

    **Blanked in place rather than removed**, which is `audiovoices.py`'s
    rule and for its reason: every line below an `include` would otherwise
    shift, and `audiospans` would place the author's own knobs against the
    wrong ones.

    A program with no `include` is returned unchanged and pays nothing —
    the same contract `voices` has.
    """
    return expanded(source, base)[0]


def expanded(source: str, base: Path | None = None,
             texts: dict | None = None) -> tuple:
    """`(text, {line of the text: (included file, line of it)})`.

    `texts` is `{file name: its text}` for an included file whose text
    is *not* what is on disk — the window's own buffer, when the
    document being edited is the `.notes` itself (`audioeditor.KINDS`).
    What a person is looking at is what should play, which is the rule
    `program` keeps for a `.ges`; this is the same rule one file over.

    **The offset has to come from here**, which is the whole of rung 1
    (`spec/drawnscores.md` §"The slices after").  `declarations` already
    knows which generated line each note was written on; what it cannot
    know is where its block lands once the author's source is in front of
    it.  That was reconstructed from outside on 2026-09-05 — count the
    author's lines, add one for the separator — and it was **wrong by one
    on the fourth note**, silently, because three of four still resolved.

    So the concatenation and the counting are one loop.  Nothing that
    needs a line number does arithmetic it cannot check, and a reader
    asking *which line of which file wrote this note* gets an answer
    rather than a recipe.

    Only note lines are in the map.  The `long 4 (` that opens a bar and
    the `))` that closes it were written by nobody, and answering for
    them would be inventing a provenance.
    """
    found = [(_line_of(source, m.start()), m.group(2))
             for m in _INCLUDE.finditer(source)]
    if not found:
        return source, {}
    root = Path(base) if base is not None else Path.cwd()
    blanked = _INCLUDE.sub(lambda m: m.group(1), source)
    read: list = []
    known: dict[str, set[str]] = {}
    for line, one in found:
        place = f"line {line}"
        path = (root / one)
        if texts and one in texts:
            text, at = texts[one], None
        elif not path.exists():
            raise NotesError(
                f'{place}: include "{one}" — no such file beside {root}')
        else:
            text, at = path.read_text(), path
        rels = parse(text, name=one, where=at)
        for section in sections_of(rels):
            if section["name"] in known:
                raise NotesError(
                    f'{place}: include "{one}" — section `{section["name"]}` is '
                    "already included; two files cannot bring the same "
                    "section name")
            known[section["name"]] = set(section["voices"])
        read.append((one, rels))

    lines = _dots(blanked, known).splitlines()
    where: dict = {}
    for one, rels in read:
        text, origin = declarations(rels)
        #: **The line the block's first line becomes**, counted rather
        #: than derived — `lines` is the answer to *how much is in front
        #: of it* and it is already in hand.
        at = len(lines) + 1
        lines += text.splitlines()
        for generated, wrote in origin.items():
            where[at + generated - 1] = (one, wrote)
    return "\n".join(lines) + "\n", where


def _line_of(source: str, offset: int) -> int:
    """The 1-based line an offset falls on — `audiospans.Site`'s convention."""
    return source.count("\n", 0, offset) + 1


#: `A.melody` → `notes_A_melody`, and only where `A` is a section this
#: program included.  Textual, exactly as `audiovoices._rewrite_dots` is,
#: and for its reason: `.` is projection in gestate, so `A.melody` would
#: parse as a field of a variable called `A`.
#:
#: **A section name that is not included is left alone**, which is the
#: one difference from `voices.NAME` and is forced: `voices` is a
#: reserved word and a section name is the author's, so a projection out
#: of a record called `A` has to keep working.  A *voice* that section
#: does not have is refused, because there the intent is unambiguous.
_DOTTED = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)")


def _dots(source: str, known: dict[str, set[str]]) -> str:
    def one(match):
        section, voice = match.group(1), match.group(2)
        if section not in known:
            return match.group(0)
        if voice not in known[section]:
            #: Placed, where `audiovoices.py`'s `voices.NAME` is not
            #: (fixme.md F158): the rewrite runs over the author's own
            #: text, so the offset is right here and the line is one
            #: count away.  The debt next door was never necessary.
            place = f"line {_line_of(source, match.start())}"
            raise NotesError(
                f"{place}: `{section}.{voice}` names no voice; "
                f"section `{section}` has "
                + ", ".join(f"`{v}`" for v in sorted(known[section])))
        return bound(section, voice)

    return _DOTTED.sub(one, source)


#: **The voice a `.notes` file gets when it is opened alone.**  A note
#: file names no instrument — `spec/drawnscores.md` §"Open questions",
#: kept that way so the format stays poor — and *play from the dragged
#: note* needs something to play through.  Henri, 2026-09-06: *"the
#: .notes could get a default voice, something that sounds piano-like"*,
#: and on how: the wrapper carries `chopin.ges`'s hammer verbatim, no
#: library word — a new word in the vocabulary is a one-way door and
#: wants a second caller first.  The envelope and the timbre are
#: chopin's to the digit; what differs is the payload it reads, `Tone`
#: from `audio.ges` rather than that piece's own `Hammer`, because that
#: is what `fromNote` builds.
HAMMER = """\
#: Struck, not bowed: the attack is immediate, the body is decay, and
#: what sustain there is stands low — a held key on a piano is a note
#: getting quieter slowly.  `examples/audio/chopin.ges`'s hammer, verbatim.
env : Adsr
env = Adsr 0.004 1.4 0.25 0.4

#: A fundamental and two overtones, each quieter — enough of a spectrum
#: to read as felt on string without pretending to be a piano.
timbre : Sig Float -> Sig Float
timbre hz = sine hz + 0.4 * sine (hz * 2.0) + 0.15 * sine (hz * 3.0)

hammerVoice : Sig Gate -> Sig Tone -> Sig Float
hammerVoice g s = timbre (!noteHz s) * adsr env g * !noteLoud s
"""

#: A tempo the file does not carry.  A `.notes` says bars and beats and
#: nothing about how fast; the wrapper has to say something, and says
#: this, in a comment a person can see.
WRAPPER_BPM = 100


def bpm_of(rels: dict) -> int | None:
    """The file's own tempo — the one row of `bpm`, or `None`."""
    rows = rels["bpm"].rows
    return next(iter(rows))[0] if rows else None


def tempo_of(rels: dict) -> int:
    """The tempo a `.notes` file played alone goes at: its own `bpm`
    record, or `WRAPPER_BPM` when it says nothing."""
    said = bpm_of(rels)
    return said if said is not None else WRAPPER_BPM


def _tempo_lines(rels: dict) -> list[str]:
    """The wrapper's `bpm`, saying where the number came from."""
    said = bpm_of(rels)
    said = (f"#: The file says `bpm {said}`." if said is not None
            else "#: The file says nothing about tempo; this is `notes.WRAPPER_BPM`.")
    return [said, "bpm : Int", f"bpm = {tempo_of(rels)}"]

#: How many notes one voice may sound at once through the wrapper.  A
#: `.notes` voice is written as a line, and a chord across lines is
#: several voices — but a tail overlaps the next stroke, so more than one.
WRAPPER_POLYPHONY = 4


def wrapper(path: Path | str, *, notes: bool = True) -> str:
    """The `.ges` a `.notes` file is played through when opened alone.

    **Generated, never written to disk**: the file stays the one source
    and this is the projection over it, the same way a roll is.  It
    includes the file by name, binds every voice the file's sections
    declare to `HAMMER`, concatenates the sections in the order written
    — a section that lacks a voice rests for its length, so the voices
    stay the same bars — and asks a roll of every section, which is
    what rung 5's view draws.  Expand it with `expanded(text,
    path.parent)`, as any program with an `include`.
    """
    path = Path(path)
    rels = parse(path.read_text(encoding="utf-8"), path.name, where=path)
    return _wrapper_of(rels, path.name, notes=notes)


def generated(name: str) -> str:
    """The first line of the wrapper for `name` — how a reader tells the
    generated program from the file it wraps.  `audioeditor.NotesKind`
    needs it: every reader that hands text to a compiler goes through
    `program`, and some hand it a program already expanded, which for a
    `.ges` is harmless (`expanded` of an expanded text is the text) and
    for a `.notes` would parse the wrapper as the note file — which is
    what a driven window did on 2026-09-06, complaining that `env` is not
    a record at line 7 of `arc.notes`."""
    return f"# {name}, opened alone — played through a piano the tree"


def _wrapper_of(rels: dict, name: str, notes: bool = True) -> str:
    """`notes=False` is the **engine's** half of the wrapper — the same
    voices, sound and tempo with the score a rest and no `include`.
    `card:notes-editor.md` slice 2: 291 notes expanded to nine hundred
    lines of source, and the language front end paid for every one of
    them twice per audition (3.95 s ×2 on 2026-09-06) though the
    instrument had not changed.  The engine compiles this text, which a
    note edit leaves byte-identical, and the notes reach the performer
    as records (`audioeditor.NotesKind.events`).  The banks and their
    channels are the same either way, because they come from the
    `voices` lines and those are here."""
    sections = sections_of(rels)
    voices: list[str] = []
    for section in sections:
        for voice in section["voices"]:
            if voice not in voices:
                voices.append(voice)
    lines = [generated(name),
             "# lends it (`notes.wrapper`).  Generated; the file is the source.",
             "", HAMMER]
    for voice in voices:
        lines.append(f"voices {voice} {WRAPPER_POLYPHONY} hammerVoice : Sig Float")
    lines.append("")
    lines.append("sound : Sig Float")
    lines.append(("sound = " + " + ".join(voices)) if voices else "sound = 0.0 * sine 440.0")
    lines.append("")
    if not notes:
        # **A rest on every bank**, not one bare rest: the voices
        # expander declares `Voice` from the banks a score *assigns*
        # to, so a score that assigns none leaves `Voice` undeclared
        # and the music prelude fails its kind check at a line the
        # author never wrote (`fixme.md` F207).  Resting on each bank
        # also keeps this assembly the shape the full one has — the
        # same `Voice` constructors, the same channels.
        rests = " || ".join(f"(r >>= voices.{v})" for v in voices) if voices else "r"
        lines += ["score : [: Void :]", f"score = {rests}", "",
                  *_tempo_lines(rels), ""]
        return "\n".join(lines) + "\n"
    lines.append(f'include "{name}"')
    lines.append("")
    parts = []
    for voice in voices:
        run = []
        for section in sections:
            if voice in section["voices"]:
                run.append(bound(section["name"], voice))
            else:
                run.append(f"(long {section['bars'] * section['beats']} r)")
        parts.append(f"(({' ++ '.join(run)}) >>= voices.{voice})")
    lines.append("score : [: Void :]")
    lines.append("score = " + ("\n     || ".join(parts) if parts else "r"))
    lines.append("")
    lines += _tempo_lines(rels)
    lines.append("")
    for section in sections:
        stacked = " || ".join(bound(section["name"], v) for v in section["voices"])
        lines.append(f"notes ({stacked})")
    return "\n".join(lines) + "\n"


def read(path: Path | str) -> str:
    """A `.ges` file, with its includes expanded — the door every reader
    of an author's file goes through."""
    path = Path(path)
    return expand(path.read_text(), path.parent)
