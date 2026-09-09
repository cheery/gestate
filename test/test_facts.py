"""The declaration a `.notes` is read by — `gestate/notes.ges`.

`card:gui-is-difficult.md` §"The document, decided" — a document is
**facts**, and since 2026-09-09 there is one statement of what a
`.notes` is: the kinds, their fields, which are required, the key and
the order live in `gestate/notes.ges` and `gestate/notes.py` reads
them.  These tests are therefore about **behaviour**, not about two
tables agreeing: comparing the parser with the declaration it is
derived from would prove nothing.

What is pinned here is that a person's mistake still earns the same
refusal, that the order is the file's own and not alphabetical, and
that the declaration and the parser are held to each other where they
still say separate things.
"""

from pathlib import Path

import pytest

from gestate import facts, notes

PIECE = Path(__file__).resolve().parent.parent / "examples" / "audio" / "arc.notes"

TWO_SECTIONS = """\
section Z  bars 1  beats 4  voices a,b
section A  bars 1  beats 4  voices a,b

note  section A  bar 1  at 0  len 96  voice a  key 60  vel mf
note  section Z  bar 1  at 0  len 96  voice a  key 60  vel mf
note  section Z  bar 1  at 0  len 96  voice b  key 60  vel mf
"""


@pytest.fixture(scope="module")
def declared():
    return facts.load()


@pytest.fixture(scope="module")
def parsed():
    return notes.parse(PIECE.read_text(), PIECE.name)


def test_the_kinds_are_the_three_a_line_may_be(declared):
    assert set(declared.names) == {"bpm", "section", "note"}


def test_an_unknown_record_is_refused_naming_the_declared_kinds():
    """The list in the refusal is the declaration's, so a kind added
    there is offered to a person without this message being touched."""
    with pytest.raises(notes.NotesError) as why:
        notes.parse("comment this is prose\n")
    said = str(why.value)
    assert "is not a record" in said
    for word in ("bpm", "section", "note"):
        assert f"`{word} …`" in said


def test_an_unknown_field_is_refused_naming_the_declared_ones(declared):
    with pytest.raises(notes.NotesError) as why:
        notes.parse("section A  bars 1  beats 4  voices a  colour red\n")
    said = str(why.value)
    assert "`colour` is not a field here" in said
    for field in declared["section"].named:
        assert f"`{field}`" in said


def test_a_missing_required_field_is_named(declared):
    """`vel` is `Must` in the declaration and nothing else says so."""
    assert "vel" in declared["note"].required
    with pytest.raises(notes.NotesError, match="missing `vel`"):
        notes.parse("section A  bars 1  beats 4  voices a\n"
                    "note  section A  bar 1  at 0  len 96  voice a  key 60\n")


def test_a_kind_with_no_key_is_written_at_most_once(declared):
    """An empty key is how `facts.ges` says *at most one of me in a
    document*; `bpm` is the one that has it, and the refusal is derived
    from that rather than written for `bpm` by name."""
    assert declared["bpm"].key == ()
    with pytest.raises(notes.NotesError, match="`bpm` is declared twice"):
        notes.parse("bpm 96\nbpm 120\n")


def test_a_bare_line_takes_one_value_of_its_declared_shape(declared):
    """`Bare` says the line is the word and one token, and the field's
    `Number` is what puts the word *number* in the refusal."""
    assert declared["bpm"].shape == ("Bare", "bpm")
    assert declared["bpm"].field("bpm").value == "Number"
    with pytest.raises(notes.NotesError, match="`bpm` takes one number"):
        notes.parse("bpm 96 120\n")


def test_the_order_is_the_file_s_sections_and_not_their_names():
    """**The defect deriving the writer found.**  A note's `section`
    sorts `Among` the sections *as the file places them*.  Written `By`
    the field, as the first declaration had it, it would sort by the
    name — which agrees on `arc.notes` only because its sections happen
    to be A, B, C.  Here Z is written first, so Z's notes come first.
    """
    parsed = notes.parse(TWO_SECTIONS, "t.notes")
    assert [(one.section, one.voice) for one in notes.ordered(parsed)] \
        == [("Z", "a"), ("Z", "b"), ("A", "a")]


def test_the_voice_order_is_the_section_s_own_and_not_alphabetical():
    """`Along` — the second term that reads another record.  `b` is
    written before `a` here, so `b`'s note is written first."""
    text = TWO_SECTIONS.replace("voices a,b", "voices b,a")
    parsed = notes.parse(text, "t.notes")
    assert [(one.section, one.voice) for one in notes.ordered(parsed)] \
        == [("Z", "b"), ("Z", "a"), ("A", "a")]


def test_the_declared_key_names_one_note(declared, parsed):
    """Q7's identity at the file's level — `section bar voice at key`.
    On `arc.notes` every note has its own, which is *0 doubled*
    arriving from the declaration's side."""
    kind = declared["note"]
    keys = [tuple(notes.record(one)[f] for f in kind.key)
            for one in parsed.notes]
    assert len(set(keys)) == len(keys) == 291


def test_a_record_carries_every_declared_field(declared, parsed):
    """`notes.record` is where a `Note` becomes what the declaration
    talks about, so it owes exactly the declared fields — no more, and
    none missing."""
    kind = declared["note"]
    assert set(notes.record(parsed.notes[0])) == set(kind.named)


def test_the_declared_field_order_is_the_written_order(declared, parsed):
    """The line writes its fields in the order they are declared.  The
    writer still spells that order out by hand, so this is what holds
    the two together until it does not."""
    line = notes._line(parsed.notes[0])
    at = [line.find(f" {f} ") for f in declared["note"].named
          if f" {f} " in line]
    assert at == sorted(at) and len(at) >= 6


def test_the_order_refuses_to_guess_without_what_it_reads(declared, parsed):
    """Both terms that read another record say so rather than quietly
    sorting by the name — which would be the F199 order again, and
    silently."""
    one = notes.record(parsed.notes[0])
    with pytest.raises(facts.FactsError, match="among"):
        facts.sort_key(declared["note"], one)
    with pytest.raises(facts.FactsError, match="along"):
        facts.sort_key(declared["note"], one, among=lambda k, v: 0)


def test_a_kind_declared_and_unbuilt_is_refused_out_loud(tmp_path, monkeypatch):
    """The gap between a declaration and the parser, said out loud the
    day somebody widens the first without the second.  Silence here
    would drop the record."""
    beside = tmp_path / "wider.ges"
    beside.write_text(
        (Path(notes.__file__).parent / "notes.ges").read_text()
        .replace("kinds = notesKinds",
                 'kinds = Kind "lyric" (Bare "text") '
                 "(Field \"text\" Word Must :: Nil) Nil Nil :: notesKinds"))
    wider = facts.Document(beside)
    monkeypatch.setattr(notes, "_kinds", lambda: wider)
    with pytest.raises(notes.NotesError, match="does not know how to read"):
        notes.parse("lyric hello\n")
