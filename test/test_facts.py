"""The declared kinds, held to the parser that has carried them by hand.

`card:gui-is-difficult.md` §"The document, decided" — a document is
**facts**, and `gestate/notes.ges` says what a `.notes` is in the
language.  `gestate/notes.py` has said the same thing in Python since
the format existed, and while both exist the Python is the one that
runs.  So every one of these compares the two, on
`examples/audio/arc.notes`, which is the only real piece in the tree.

The postcondition this serves, Henri's slice of 2026-09-09: *when the
kinds are declared beside the document, gestate reads, refuses and
writes `arc.notes` exactly as it does now.*  This is the reading half;
nothing here writes.
"""

from pathlib import Path

import pytest

from gestate import facts, notes

PIECE = Path(__file__).resolve().parent.parent / "examples" / "audio" / "arc.notes"


@pytest.fixture(scope="module")
def declared():
    return facts.load()


@pytest.fixture(scope="module")
def parsed():
    return notes.parse(PIECE.read_text(), PIECE.name)


def test_the_kinds_are_the_three_the_parser_takes(declared):
    """A line is `section …`, `note …` or `bpm …` — the parser's own
    refusal names those three, and the declaration has to be that list
    and no longer."""
    assert set(declared.names) == {"bpm", "section", "note"}


def test_a_note_takes_the_fields_the_parser_allows(declared):
    assert set(declared["note"].named) == notes._NOTE_FIELDS


def test_a_note_must_carry_what_the_parser_requires(declared):
    assert set(declared["note"].required) == notes._NOTE_REQUIRED


def test_a_section_takes_the_fields_the_parser_allows(declared):
    """The section's **name** is not among them: it is written bare
    after the kind word, which the declaration says with `Headed` and
    the parser says by slicing `tokens[1:]` past it."""
    assert declared["section"].shape == ("Headed", "name")
    assert set(declared["section"].named) == notes._SECTION_FIELDS


def test_a_section_must_carry_what_the_parser_requires(declared):
    assert set(declared["section"].required) == notes._SECTION_REQUIRED


def test_bpm_is_one_bare_number_and_has_no_key(declared):
    """An empty key is how a kind says *at most one of me in a
    document*, and the parser refuses a second `bpm` outright."""
    bpm = declared["bpm"]
    assert bpm.shape == ("Bare", "bpm")
    assert bpm.key == ()
    assert [(f.name, f.value, f.need) for f in bpm.fields] == [
        ("bpm", "Number", "Must")]
    with pytest.raises(notes.NotesError, match="declared twice"):
        notes.parse("bpm 96\nbpm 120\n")


def _record(one, file):
    """A parsed `Note` as its fields — what a record is, before anything
    has been decided about how records are held."""
    return {"section": one.section, "bar": one.bar, "at": one.at,
            "len": one.length, "voice": one.voice, "key": one.key}


def _along(kind, field, record, file=None):
    """The sequence an `Along` term orders by: the section's own voice
    list, found by the record's `section`."""
    assert (kind, field) == ("section", "voices")
    for one in file.sections:
        if one.name == record["section"]:
            return one.voices
    return ()


def test_the_declared_order_is_the_canonical_order(declared, parsed):
    """**The whole point of the slice, on his own piece.**  Sorting
    `arc.notes`' 291 notes by the *declaration* — section, bar, the
    voice in the section's own order, tick, key — puts them in exactly
    the order `notes.ordered` puts them in.  Compared as the lines they
    are, so a difference reads as a file and not as an index."""
    kind = declared["note"]
    mine = sorted(parsed.notes,
                  key=lambda one: facts.sort_key(
                      kind, _record(one, parsed),
                      lambda k, f, r: _along(k, f, r, parsed)))
    assert [notes._line(one) for one in mine] \
        == [notes._line(one) for one in notes.ordered(parsed)]


def test_the_declared_key_names_one_note(declared, parsed):
    """Q7's identity, at the file's level: `section bar voice at key`.
    On `arc.notes` every note has its own, which is the measurement the
    card records as *0 doubled* arriving from the declaration's side."""
    kind = declared["note"]
    keys = [tuple(_record(one, parsed)[f] for f in kind.key)
            for one in parsed.notes]
    assert len(set(keys)) == len(keys) == 291


def test_the_order_refuses_to_guess_without_its_sequence(declared, parsed):
    """`Along` reads another record, and a caller that gave nothing to
    read is told so rather than quietly sorting alphabetically — which
    would be the F199 order again, and silently."""
    one = parsed.notes[0]
    with pytest.raises(facts.FactsError, match="along"):
        facts.sort_key(declared["note"], _record(one, parsed))
