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
able to rewrite one line and nothing else.
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


@dataclass(frozen=True)
class Note:
    """One note record, and the line it was written on."""
    section: str
    bar: int
    at: int
    length: int
    voice: str
    key: int
    level: int
    manners: int
    line: int


@dataclass
class Section:
    """One section record: the grid its notes are placed on."""
    name: str
    bars: int
    beats: int
    voices: tuple[str, ...]
    key: str | None
    mode: str | None
    line: int

    @property
    def bar_ticks(self) -> int:
        return self.beats * TICKS_PER_BEAT


@dataclass
class NotesFile:
    """A parsed `.notes` file — sections in the order written, and notes."""
    name: str
    sections: list[Section] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)

    def section(self, name: str) -> Section | None:
        for one in self.sections:
            if one.name == name:
                return one
        return None

    @property
    def voice_names(self) -> list[tuple[str, str]]:
        """`(section, voice)` for every voice every section declares."""
        return [(s.name, v) for s in self.sections for v in s.voices]


# ── Parsing ─────────────────────────────────────────────────────────────────

#: What each record kind may carry, and what it must.  Named here rather
#: than scattered through the parser so that the refusal for an unknown
#: field can *list* the ones that exist — the shape `audiovoices.py`'s
#: `voices.NAME` refusal already has.
_SECTION_FIELDS = {"key", "mode", "bars", "beats", "voices"}
_SECTION_REQUIRED = {"bars", "beats", "voices"}
_NOTE_FIELDS = {"section", "bar", "at", "len", "voice", "key", "vel", "manner"}
_NOTE_REQUIRED = {"section", "bar", "at", "len", "voice", "key", "vel"}


def _fields(tokens: list[str], allowed: set[str], place: str) -> dict[str, str]:
    """`key value key value …` into a dict, refusing what a person mistypes.

    Positional values are refused outright, which is gate two of
    `spec/drawnscores.md` §"The four gates" — *the failure that made
    `manner` unfindable was two fields of one shape telling apart only by
    position*.
    """
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
    missing = sorted(r for r in _required(allowed) if r not in out)
    if missing:
        raise NotesError(
            f"{place}: missing " + ", ".join(f"`{m}`" for m in missing))
    return out


def _required(allowed: set[str]) -> set[str]:
    return _SECTION_REQUIRED if allowed is _SECTION_FIELDS else _NOTE_REQUIRED


def _int(text: str, key: str, place: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise NotesError(f"{place}: `{key} {text}` is not a whole number") from None


def parse(text: str, name: str = "<notes>") -> NotesFile:
    """Read a `.notes` file.  Every refusal names the file and the line.

    Two passes, because a note may be written above the section it names
    — which is the reflow gate: a file whose lines are shuffled has to
    parse to the same score, and a parser that needed the header first
    would not have that property.
    """
    out = NotesFile(name=name)
    note_lines: list[tuple[int, list[str]]] = []

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        place = f"{name}:{number}"
        kind = tokens[0]
        if kind == "section":
            out.sections.append(_section(tokens[1:], number, place))
        elif kind == "note":
            note_lines.append((number, tokens[1:]))
        else:
            raise NotesError(
                f"{place}: `{kind}` is not a record; a line is `section …` "
                "or `note …`")

    seen: set[str] = set()
    for one in out.sections:
        if one.name in seen:
            place = f"{name}:{one.line}"
            raise NotesError(f"{place}: section `{one.name}` is declared twice")
        seen.add(one.name)

    for number, tokens in note_lines:
        out.notes.append(_note(tokens, number, f"{name}:{number}", out))

    _refuse_doubles(out, name)
    return out


def _section(tokens: list[str], number: int, place: str) -> Section:
    if not tokens or not _NAME.match(tokens[0]):
        raise NotesError(
            f"{place}: `section` needs a name — `section A key D bars 8 "
            "beats 4 voices melody,roots`")
    got = _fields(tokens[1:], _SECTION_FIELDS, place)
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
    return Section(name=tokens[0], bars=bars, beats=beats, voices=voices,
                   key=key, mode=mode, line=number)


def _note(tokens: list[str], number: int, place: str, out: NotesFile) -> Note:
    got = _fields(tokens, _NOTE_FIELDS, place)
    section = out.section(got["section"])
    if section is None:
        raise NotesError(
            f"{place}: no section `{got['section']}`; this file has "
            + (", ".join(f"`{s.name}`" for s in out.sections) or "none"))
    bar = _int(got["bar"], "bar", place)
    if not 1 <= bar <= section.bars:
        raise NotesError(
            f"{place}: `bar {bar}` — section `{section.name}` has "
            f"{section.bars} bars")
    tick = _int(got["at"], "at", place)
    if not 0 <= tick < section.bar_ticks:
        #: The friction this refusal is: W3 of
        #: `doc/notes/notes-on-writing-a-piece.md` — *"a fifth note in `a3`
        #: would compile, shift everything after it by a beat, and be found
        #: by ear an hour later."*  It does not compile here.
        raise NotesError(
            f"{place}: `at {tick}` is not inside bar {bar} of section "
            f"`{section.name}`, which is {section.beats} beats "
            f"({section.bar_ticks} ticks) long")
    length = _int(got["len"], "len", place)
    if length < 1:
        raise NotesError(f"{place}: `len {length}` — a note lasts at least one tick")
    if got["voice"] not in section.voices:
        raise NotesError(
            f"{place}: section `{section.name}` has no voice `{got['voice']}`; "
            "it has " + ", ".join(f"`{v}`" for v in section.voices))
    key = _int(got["key"], "key", place)
    if not 0 <= key <= 127:
        raise NotesError(f"{place}: `key {key}` is not a MIDI key number (0-127)")
    if got["vel"] not in LEVELS:
        raise NotesError(
            f"{place}: `vel {got['vel']}` is not a dynamic; "
            + " ".join(LEVELS))
    return Note(section=section.name, bar=bar, at=tick, length=length,
                voice=got["voice"], key=key, level=LEVELS.index(got["vel"]),
                manners=_manners(got.get("manner"), place), line=number)


def _manners(text: str | None, place: str) -> int:
    if text is None:
        return 0
    bits = 0
    for one in text.split(","):
        if not one:
            continue
        if one not in MANNERS:
            raise NotesError(
                f"{place}: `{one}` is not a manner; "
                + " ".join(sorted(MANNERS)))
        if bits & MANNERS[one]:
            raise NotesError(f"{place}: `{one}` is asked for twice")
        bits |= MANNERS[one]
    return bits


def _refuse_doubles(out: NotesFile, name: str) -> None:
    """One voice, one place, one note.

    Not a taste rule: two identical notes at one instant are one note
    played twice as loud by every renderer here, so the file would say
    something it cannot mean, and a round trip through the roll could not
    tell which line to rewrite.
    """
    seen: dict[tuple, int] = {}
    for one in out.notes:
        spot = (one.section, one.bar, one.at, one.voice, one.key)
        if spot in seen:
            place = f"{name}:{one.line}"
            raise NotesError(
                f"{place}: this note is already written at "
                f"{name}:{seen[spot]} — same section, bar, voice, tick and key")
        seen[spot] = one.line


# ── The stable order, and writing one back ──────────────────────────────────


def ordered(out: NotesFile) -> list[Note]:
    """The canonical order: section, bar, tick, the section's own voice
    order, then key.

    Gate four of `spec/drawnscores.md` — *two writings of one phrase are
    byte-identical, so a diff shows what changed and nothing else.*  The
    voice order is the section's rather than alphabetical because that is
    the order the roll stacks them in, so a written file reads top voice
    down like a score does.
    """
    rank = {(s.name, v): i for s in out.sections for i, v in enumerate(s.voices)}
    place = {s.name: i for i, s in enumerate(out.sections)}
    return sorted(out.notes, key=lambda n: (place[n.section], n.bar, n.at,
                                            rank[(n.section, n.voice)], n.key))


def write(out: NotesFile) -> str:
    """A `.notes` file, in the canonical order and the canonical spelling.

    Reading a file this wrote and writing it again is a no-op, which is
    what makes a gesture on the roll able to rewrite one line without
    disturbing the file around it.
    """
    lines = []
    for one in out.sections:
        head = [f"section {one.name}"]
        if one.key is not None:
            head.append(f"key {one.key}")
        if one.mode is not None:
            head.append(f"mode {one.mode}")
        head += [f"bars {one.bars}", f"beats {one.beats}",
                 "voices " + ",".join(one.voices)]
        lines.append("  ".join(head))
    lines.append("")
    at_bar = None
    for one in ordered(out):
        if (one.section, one.bar) != at_bar:
            if at_bar is not None:
                lines.append("")
            at_bar = (one.section, one.bar)
        lines.append(_line(one))
    return "\n".join(lines) + "\n"


def _line(one: Note) -> str:
    out = (f"note  section {one.section}  bar {one.bar}  at {one.at}  "
           f"len {one.length}  voice {one.voice}  key {one.key}  "
           f"vel {LEVELS[one.level]}")
    asked = [m for m, bit in sorted(MANNERS.items(), key=lambda kv: kv[1])
             if one.manners & bit]
    return out + ("  manner " + ",".join(asked) if asked else "")


# ── The lamp: what the mode says, and what it never does ────────────────────


def outside(out: NotesFile) -> list[tuple[Note, int]]:
    """Notes outside their section's declared mode — `(note, degree)`.

    **Reports, never refuses**, which is decision 3 of the spec.  A ♯11
    over a dominant is idiomatic and is the whole of `arc.ges`'s A
    section; a gate here would refuse the blues.  A section that declares
    no `key` or no `mode` says nothing and is silent rather than guessed
    at.
    """
    found = []
    for one in out.notes:
        section = out.section(one.section)
        if section is None or section.key is None or section.mode is None:
            continue
        degree = (one.key - _PITCH_CLASS[section.key]) % 12
        if degree not in _MODES[section.mode.lower()]:
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


def sounding(out: NotesFile) -> list:
    """`[(section, bar, [keys low to high])]` — what is heard in each bar.

    A note counts in every bar it is still sounding in, because a held
    root under four bars is part of all four — which is the thing a list
    of note *starts* cannot say and the reason
    `card:the-first-jam.md` item 2 exists.
    """
    heard: dict = {}
    for one in out.notes:
        section = out.section(one.section)
        if section is None:
            continue
        last = one.bar + (one.at + one.length - 1) // section.bar_ticks
        for bar in range(one.bar, min(last, section.bars) + 1):
            heard.setdefault((one.section, bar), set()).add(one.key)
    order = {s.name: i for i, s in enumerate(out.sections)}
    return [(s, b, sorted(keys)) for (s, b), keys
            in sorted(heard.items(), key=lambda kv: (order[kv[0][0]], kv[0][1]))]


# ── The expansion into `.ges` ───────────────────────────────────────────────

#: The name a voice of a section becomes.  Underscored and prefixed
#: because it is generated: nothing an author types can collide with it,
#: and a name in an error message that nobody wrote is the failure
#: `audiovoices._rewrite_dots` names.
def bound(section: str, voice: str) -> str:
    return f"notes_{section}_{voice}"


def _payload(one: Note) -> str:
    return f"'(fromNote {one.key} {one.level} {one.manners})"


def _held(one: Note) -> str:
    """A note of `one.length` ticks, out of the beat-long note `'x` is.

    `|*` scales a duration and `|/` divides it, both by whole numbers, so
    `L` ticks is `96 * p / q` with `p/q` reduced — and it is exact for
    every `L`, because `q` divides `96 * p` by construction.  This is
    where the 96-tick grid pays for itself: no fraction reaches the
    format and no special case reaches the editor.
    """
    body = _payload(one)
    common = gcd(one.length, TICKS_PER_BEAT)
    up, down = one.length // common, TICKS_PER_BEAT // common
    if up != 1:
        body = f"({body} |* {up})"
    if down != 1:
        body = f"({body} |/ {down})"
    return body


def _placed(one: Note) -> str:
    body = _held(one)
    return body if one.at == 0 else f"(at {one.at} {body})"


def declarations(out: NotesFile) -> tuple[str, dict[int, int]]:
    """The `.ges` text a file becomes, and `{generated line: source line}`.

    The map is what carries provenance: a note is one generated line, so
    a graph node placed on generated line 41 was written on whatever line
    of the `.notes` file the map says.  `audiospans.Site` already names a
    file and a line within it, so this is the last piece that reading was
    missing.
    """
    lines: list[str] = []
    origin: dict[int, int] = {}
    order = ordered(out)
    for section in out.sections:
        for voice in section.voices:
            mine = [n for n in order
                    if n.section == section.name and n.voice == voice]
            lines.append(f"{bound(section.name, voice)} : (FromNote a) => [: a :]")
            lines.append(f"{bound(section.name, voice)} =")
            for index in range(1, section.bars + 1):
                inside = [n for n in mine if n.bar == index]
                lead = "      " if index == 1 else "   ++ "
                if not inside:
                    lines.append(f"{lead}(long {section.beats} r)")
                    continue
                lines.append(f"{lead}(long {section.beats} (")
                for spot, one in enumerate(inside):
                    joint = "        " if spot == 0 else "     || "
                    lines.append(f"{joint}{_placed(one)}")
                    origin[len(lines)] = one.line
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
    found = [(_line_of(source, m.start()), m.group(2))
             for m in _INCLUDE.finditer(source)]
    if not found:
        return source
    root = Path(base) if base is not None else Path.cwd()
    out = _INCLUDE.sub(lambda m: m.group(1), source)
    tail: list[str] = []
    known: dict[str, set[str]] = {}
    for line, one in found:
        place = f"line {line}"
        path = (root / one)
        if not path.exists():
            raise NotesError(
                f'{place}: include "{one}" — no such file beside {root}')
        parsed = parse(path.read_text(), name=one)
        for section in parsed.sections:
            if section.name in known:
                raise NotesError(
                    f'{place}: include "{one}" — section `{section.name}` is '
                    "already included; two files cannot bring the same "
                    "section name")
            known[section.name] = set(section.voices)
        text, _ = declarations(parsed)
        tail.append(text)
    return _dots(out, known) + "\n" + "\n".join(tail)


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


def read(path: Path | str) -> str:
    """A `.ges` file, with its includes expanded — the door every reader
    of an author's file goes through."""
    path = Path(path)
    return expand(path.read_text(), path.parent)
