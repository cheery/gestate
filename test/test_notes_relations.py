"""The relations a reader gets — `card:relational-model.md` Q6 and Q2.

Henri, 2026-09-10: *"The data can be displayed like it's shown in the
file, today.  But it should reach the reader of that data normalized."*

Two roads lead to one set of relations and are held to each other
here on `examples/audio/arc.notes`: `notes.parse` reads the file in
the author's terms and refuses what it may not say, `notes.relations_of`
reads the same file by the declaration alone.  What is pinned beyond
their agreement is the
information principle — nothing carried by nesting, encoding, position
or adjacency — and that the integrity rules, run over the relations,
refuse what the parser refuses and nothing the parser accepts.
"""

import re
from pathlib import Path

import pytest

from gestate import facts, notes

PIECE = Path(__file__).resolve().parent.parent / "examples" / "audio" / "arc.notes"

#: The relations that are the model, and the three that are not.
MODEL = {"bpm", "section", "section.key", "section.mode", "section.voices",
         "note", "note.spell", "note.manner"}
INDEX = {"line", "above", "beside", "closing"}


@pytest.fixture(scope="module")
def text():
    return PIECE.read_text()


@pytest.fixture(scope="module")
def by_declaration(text):
    return notes.relations_of(text, PIECE.name)


@pytest.fixture(scope="module")
def by_parser(text):
    return notes.parse(text, PIECE.name)


# ── Two roads, one set ──────────────────────────────────────────────────────


def test_the_two_roads_agree_on_the_piece(by_declaration, by_parser):
    assert by_declaration.keys() == by_parser.keys() == MODEL | INDEX
    for name in by_declaration:
        assert by_declaration[name] == by_parser[name], name


def test_every_note_is_one_row_and_nothing_is_lost(by_parser):
    """291 facts and 291 lines — the file has no doubled note, so the
    set and the bag are the same size here.  `test_a_doubled_line`
    below is where they part."""
    assert len(by_parser["note"].rows) == 291
    assert len(by_parser["line"].where(kind="note")) == 291


# ── The information principle ──────────────────────────────────────────────


def test_nothing_in_the_model_is_nested_or_encoded(by_declaration):
    """Every value is one `int` or one `str`.  A section's voices are
    rows with a rank, a note's manners are rows with a word, and no
    bitmask or tuple reaches a reader."""
    for name in MODEL:
        for row in by_declaration[name].rows:
            for value in row:
                assert isinstance(value, (int, str)) and not isinstance(value, bool), (name, row)


def test_no_line_number_is_in_the_model(by_declaration):
    for name in MODEL:
        assert "line" not in by_declaration[name].heading


def test_the_voice_order_is_a_fact_with_a_rank(by_declaration):
    voices = by_declaration["section.voices"]
    assert voices.heading == ("name", "rank", "value")
    assert {row for row in voices.rows if row[0] == "A"} == {
        ("A", 1, "melody"), ("A", 2, "upper"), ("A", 3, "middle"),
        ("A", 4, "lower"), ("A", 5, "bass")}


def test_a_manner_is_a_row_and_not_a_bit(by_declaration):
    manner = by_declaration["note.manner"]
    assert manner.heading[-2:] == ("rank", "value")
    assert {row[-1] for row in manner.rows} <= set(notes.MANNERS)


def test_absent_is_no_row():
    text = ("section A  bars 1  beats 4  voices lead\n"
            "section B  key D  mode lydian  bars 1  beats 4  voices lead\n")
    rels = notes.relations_of(text, "two.notes")
    assert rels["section.key"].rows == {("B", "D")}
    assert rels["section.mode"].rows == {("B", "lydian")}
    assert rels["note.spell"].rows == frozenset()


def test_prose_is_keyed_and_not_adjacent():
    text = ("section A  bars 1  beats 4  voices lead\n"
            "# a word about this note\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf  # and beside\n")
    rels = notes.relations_of(text, "prose.notes")
    key = ("A", 1, "lead", 0, 60)
    assert rels["above"].rows == {(3, 1, "# a word about this note")}
    assert rels["beside"].rows == {(3, "# and beside")}
    assert rels["line"].rows == {("section", ("A",), 1), ("note", key, 3)}


def test_a_doubled_line_is_one_fact_and_two_writings():
    """The set and the bag part here, and the prose goes with the
    *writing* — which is what the derivation found: keyed by the record
    instead, the two sentences merged onto one note and one of the two
    lines was lost."""
    text = ("section A  bars 1  beats 4  voices a\n"
            "\n"
            "# the first saying\n"
            "note  section A  bar 1  at 0  len 96  voice a  key 60  vel mf\n"
            "# the second\n"
            "note  section A  bar 1  at 0  len 96  voice a  key 60  vel mf\n")
    rels = notes.parse(text, "twice.notes")
    assert len(rels["note"].rows) == 1, "one fact"
    assert len(rels["line"].where(kind="note")) == 2, "said twice"
    written = notes.notes_of(rels)
    assert [one["line"] for one in written] == [4, 6]
    assert [one["above"] for one in written] == [("# the first saying",),
                                                 ("# the second",)]
    assert notes.write(rels) == text, "and it round-trips"
    assert len(notes.doubled(rels)) == 1


# ── The references, derived from the sort declaration ───────────────────────


def test_the_two_foreign_keys_are_the_two_sorts_that_read_another_record():
    assert facts.load()["note"].refers == (
        ("Refer", "section", "section"),
        ("Within", "voice", "section", "voices"))
    assert facts.load()["section"].refers == ()


# ── The integrity rules, over the relations ────────────────────────────────


def test_the_piece_is_refused_nowhere(by_declaration):
    assert notes.refused(by_declaration) == set()


HEAD = "section A  bars 2  beats 4  voices lead\n"


@pytest.mark.parametrize("line,parser_says", [
    ("note  section B  bar 1  at 0  len 96  voice lead  key 60  vel mf",
     "no section `B`"),
    ("note  section A  bar 1  at 0  len 96  voice horn  key 60  vel mf",
     "has no voice `horn`"),
    ("note  section A  bar 3  at 0  len 96  voice lead  key 60  vel mf",
     "has 2 bars"),
    ("note  section A  bar 1  at 384  len 96  voice lead  key 60  vel mf",
     "is not inside bar 1"),
    ("note  section A  bar 1  at 0  len 96  voice lead  key 60  spell d4  vel mf",
     "names key 62"),
])
def test_what_the_parser_refuses_lands_its_key_in_refused(line, parser_says):
    """The parity while both exist: the five rules `notes.py` carries in
    `_note` and the same five run over the relations name the same
    record — and the day the parser stops running, this is what
    remembers them."""
    text = HEAD + line + "\n"
    with pytest.raises(notes.NotesError, match=parser_says):
        notes.parse(text, "one.notes")
    fields = line.split()
    key = ("A" if "section A" in line else "B",
           int(fields[fields.index("bar") + 1]),
           fields[fields.index("voice") + 1],
           int(fields[fields.index("at") + 1]),
           int(fields[fields.index("key") + 1]))
    assert notes.refused(notes.relations_of(text, "one.notes")) == {("note", key)}


def test_records_reads_structure_and_nothing_else():
    """A note naming no section is a record; a note with no `vel` is not."""
    got = notes.records(HEAD + "note  section B  bar 1  at 0  len 96  voice lead  key 60  vel mf\n")
    assert [kind.name for _n, kind, *_ in got] == ["section", "note"]
    with pytest.raises(notes.NotesError, match="missing `vel`"):
        notes.records(HEAD + "note  section A  bar 1  at 0  len 96  voice lead  key 60\n")


# ── The domains, declared once and held to the parser ───────────────────────


def test_the_parser_s_lists_are_the_declaration_s():
    """`LEVELS` and `MANNERS` were the parser's own; `notes.ges` now says
    them, and while both exist they are one list."""
    note = facts.load()["note"]
    assert note.field("vel").domain == ("OneOf", notes.LEVELS)
    assert note.field("manner").domain == ("Each", tuple(notes.MANNERS))


def _boundary(field):
    """A value just outside the declared domain, derived from it."""
    head = field.domain[0]
    if head == "Range":
        return field.domain[2] + 1
    if head == "AtLeast":
        return field.domain[1] - 1
    return "nosuchthing"


@pytest.mark.parametrize("kind,field", [
    (k.name, f.name) for k in facts.load().kinds for f in k.fields if f.domain])
def test_the_parser_refuses_what_the_domain_refuses(kind, field):
    """For every field with a domain, the value one step outside it is
    refused by the parser in its own sentence *and* by the declaration
    road in the derived one — the parity while both run."""
    declared = facts.load()[kind].field(field)
    bad = _boundary(declared)
    good = ("section A  bars 2  beats 4  voices lead\n"
            "note  section A  bar 1  at 0  len 96  voice lead  key 60  vel mf  manner accent\n"
            "bpm 96\n")
    text = re.sub(rf"\b{field} \S+", f"{field} {bad}", good, count=1)
    assert f"{field} {bad}" in text
    with pytest.raises(notes.NotesError):
        notes.parse(text, "edge.notes")
    with pytest.raises(notes.NotesError, match=f"`{field} {bad}`"):
        notes.records(text, "edge.notes")


# ── The two views the roll and the performer read ───────────────────────────


def test_the_two_views_are_the_same_on_both_roads(by_declaration, by_parser):
    """The roll reads one of these and the writer the other; they are
    one document, so the views agree field for field."""
    assert notes.notes_of(by_declaration) == notes.notes_of(by_parser)
    assert notes.sections_of(by_declaration) == notes.sections_of(by_parser)


def test_a_note_view_carries_the_file_s_own_words(by_parser):
    """No renamed attribute and no encoding: `len` not `length`, `vel`
    the dynamic's name, `manner` the names in the order written."""
    one = next(n for n in notes.notes_of(by_parser) if n["manner"])
    assert set(one) == {"section", "bar", "at", "len", "voice", "key",
                        "spell", "vel", "manner", "line", "above", "beside"}
    assert one["vel"] in notes.LEVELS
    assert all(m in notes.MANNERS for m in one["manner"])


def test_the_readers_hold_no_parsed_file():
    """The roll, the performer, the wrapper and the compiled road's
    declarations read relations — `NotesFile` reaches none of them."""
    import inspect

    from gestate import audioeditor, scorebox

    for reader in (scorebox.notes_rolls, audioeditor.NotesKind.events,
                   audioeditor.NotesKind.rolls, audioeditor.NotesKind.engine_program,
                   notes.declarations, notes._wrapper_of, notes.tempo_of,
                   notes.write, notes.outside, notes.sounding, notes.spellings,
                   notes.asserted, notes.retracted):
        source = inspect.getsource(reader)
        assert "notes_parsed" not in source and ".sections" not in source, reader.__name__


def test_the_record_classes_are_gone():
    """`Note`, `Section` and `NotesFile` were a third statement of what
    a `.notes` is — 2026-09-10, and nothing in the tree may bring one
    back without saying so here."""
    for name in ("Note", "Section", "NotesFile"):
        assert not hasattr(notes, name), name


def test_the_closing_prose_is_a_relation_too():
    rels = notes.relations_of("section A  bars 1  beats 4  voices a\n# the end\n# of it\n")
    assert rels["closing"].rows == {(1, "# the end"), (2, "# of it")}
