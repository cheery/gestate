"""The standard library, as pages you can look things up in — `doc/ref/`.

    python -m gestate.reference            # rewrite doc/ref/
    python -m gestate.reference --check    # fail if it is out of date

**Generated, and that is the point.**  There are 218 definitions across six
library files and a hand-written reference for them would be behind within
a month — the failure mode of every reference document ever written by
hand.  Everything here is read back out of the `.ges` files themselves, so
the page and the code cannot disagree: rename a function and the reference
renames it, delete one and it leaves.

What was already there did not answer the question.  `doc/manual.md` is a
narrative and you cannot look anything up in it; `spec/*.md` says why the
language is the way it is and never what is in it; `typecheck --query NAME`
is exact and requires you to **already know the name**, which is the one
thing a person looking something up does not.  So the only way to find out
that `sine` existed was to read all 745 lines of `synth.ges`.

**Textual, not compiled.**  A signature is read off the line the author
wrote it on rather than out of inference, and deliberately: what belongs in
a reference is what the library *promises*, which is the written signature,
not the more general type inference may have found for it.  It also means
this runs on a file that does not compile, which is when a reference is
most wanted.

**`internal` is honoured here and nowhere else yet.**  The marker parses
(`syntax/ast.py`'s `VInternal`) and this reader acts on it, but nothing
*enforces* it: a program that names a private function still compiles.
That is deliberate sequencing rather than an oversight — see `plan.md`.
Enforcement has to wait for the libraries to have a private half to
enforce, and today they do not, because the older examples reach into the
machinery of every filter and envelope in `synth.ges`.

A name below the marker still gets an entry, because "what is this thing
my editor just showed me" is a fair question about a private function too;
it is marked, sorted after the vocabulary, and the reader is told it is
not theirs to call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

#: The libraries, in the order a reader meets them, with the one sentence
#: that says when each is in scope.
LIBRARIES = (
    ("prelude.ges", "Prelude",
     "Always in scope, in every program and every backend."),
    ("signal.ges", "Signals",
     "Any reactive backend — a synth or a canvas."),
    ("audio.ges", "Audio",
     "Synths: `audioperform`, `audioeditor`, `audio`."),
    ("synth.ges", "Synthesis",
     "Synths, beside `audio.ges`. Oscillators, envelopes, filters, FM."),
    ("music.ges", "Music",
     "Programs with a `score` — the MIDI backend and performances."),
    ("gui.ges", "Canvas",
     "Programs with a `substrate` — `gui`, and the editor's canvas tab."),
)

#: **The language itself**, which no library declares and so no page could
#: be generated from.
#:
#: `head`, `delay`, `wait`, `watch`, `tail` and `sync` are *desugaring
#: forms* — `desugar.py` turns `wait c` into an `EWait` node — and `chan`
#: and `never` are nullary ones.  They are in `seminaive._BUILTINS` and in
#: no `.ges` file at all, so the generator, which reads the libraries, had
#: nothing to read and left them out.  Every reactive program uses `wait`
#: on its first line and the reference did not mention it.
#:
#: Hand-written for that reason, and the types are taken from `infer.py`'s
#: rules rather than from prose — the comment beside each case there is the
#: same line as here, so the two can be checked against each other by
#: reading.  Spelled `FaL` and `ExL` rather than with the circled
#: quantifiers: `⃝` is a *combining* mark, so it lands on whatever glyph
#: precedes it and comes out garbled in the editor that shows this.
PRIMITIVES = (
    ("Channels", (
        ("chan", "Chan a",
         "A fresh channel.  Its identity *is* the declaration: two `chan`s "
         "are two channels, and a name bound to one is how anything else "
         "reaches it."),
        ("wait", "Chan a -> ExL a",
         "The next thing to arrive on a channel.  `0.0 ::: mkSig (wait c)` "
         "is a signal fed by one — a value now, and whatever comes next "
         "later.  This is the first line of nearly every canvas program."),
        ("never", "ExL a",
         "An arrival that never comes.  The unit of `sync`, and what a "
         "signal that only ever holds one value waits on."),
    )),
    ("Signals", (
        ("head", "Sig a -> a",
         "What a signal holds *now*."),
        ("tail", "Sig a -> ExL (Sig a)",
         "The rest of it, once one more instant has passed.  `scan` is "
         "written with this and `:::`."),
        ("(:::)", "a -> ExL (Sig a) -> Sig a",
         "A value now and a signal later, which is what a signal *is*.  "
         "The one constructor; everything else builds it."),
    )),
    ("Later", (
        ("delay", "a -> FaL a",
         "Something available from the next instant on.  Guarded "
         "recursion's guard: a recursive occurrence under one is "
         "productive by construction."),
        ("(<*>)", "FaL (a -> b) -> FaL a -> FaL b",
         "Apply, later.  Rizzo's ⊛."),
        ("(<@>)", "FaL (a -> b) -> ExL a -> ExL b",
         "Apply a delayed function to an arrival.  Rizzo's ⑤ — and the "
         "asymmetry is the point: what a `Sig` consumes is ExL and what "
         "`gfix` binds is FaL, so this is where the two meet."),
        ("gfix", "(FaL a -> a) -> a",
         "Guarded recursion.  `gfix q => …` binds `q` to the whole "
         "expression *one instant later*, so it can only be consumed "
         "through `<*>` or `<@>` — which is the guard, in the type."),
    )),
    ("Clocks", (
        ("sync", "ExL a -> ExL b -> ExL (Sync a b)",
         "Whichever arrives first, or both — `SyncLeft`, `SyncRight`, "
         "`SyncBoth`.  The two need not agree in type: combining unlike "
         "clocks is what it is for."),
        ("watch", "Sig (Maybe a) -> ExL a",
         "The next instant at which a signal holds a `Just`.  A signal "
         "turned back into an arrival."),
    )),
    ("Lifting", (
        ("(!)", "(a -> … -> z) -> Sig a -> … -> Sig z",
         "Where an ordinary function meets signals.  `!f x y z` pairs its "
         "arguments up through `Both` and takes them apart again, so it "
         "lifts over **any number** of them — there is no three-signal "
         "former and none is needed.  The marker binds the **next atom** "
         "and the application around it supplies the lifted arguments, so "
         "parentheses read the way an eye expects: `!f x` lifts `f` over "
         "the signal `x`; `!(f x)` is the constant signal of the computed "
         "value `f x`; `!(f x) y` lifts the computed function `f x` over "
         "`y`; `!x` alone is the constant signal of `x`."),
    )),
    # **Supplied by the renderer, defined in no library file.**  Which is
    # exactly why they belong here: `reference.py` builds its pages from
    # the `.ges` sources, so a name the *host* puts into the assembly is
    # invisible to it and is reported as not existing.  `beat` was — it
    # works in any scored program and appeared nowhere in `doc/ref/` but
    # in prose, so the honest conclusion from reading the reference was
    # that there is no such thing.
    ("The renderer's own", (
        ("ticks", "Sig Int",
         "The instant number, one per sample.  The clock everything at "
         "audio rate is a function of, and the argument `map` is usually "
         "given."),
        ("sampleRate", "Float",
         "How many instants there are in a second.  The *renderer's* "
         "answer, not the program's: the same synth renders at any rate, "
         "and which one is a property of the file being written."),
        ("constSig", "a -> Sig a",
         "The same value at every instant.  What it is constant *over* is "
         "whichever clock is running — `ticks` for a synth, the event "
         "stream for a canvas — which is why the renderer supplies it and "
         "no library can.  **Internal**: it is the node `!` builds, and "
         "the marker is the spelling — `!x`, or `!(f x)` for a computed "
         "value.  A program that names it is refused, the way a library's "
         "own machinery is."),
        ("beat", "Sig Float",
         "**What beat it is** — at audio rate, for a synth moving in time "
         "with the music rather than with the second.  In scope wherever "
         "the program states a `bpm`, score or no score: a drone on a grid "
         "needs a tempo and no notes.  A program that states none gets "
         "`Unknown global 'beat'`, which is the truth — there is nothing "
         "to answer with.  Under a `tempo` envelope it is piecewise "
         "*quadratic* rather than linear, because tempo is linear in time "
         "and beat is its integral; it is compiled from the same "
         "derivation the schedule is, so what a synth reads and where the "
         "notes landed cannot drift apart."),
        ("elapsed", "Sig Float",
         "How long the program has been running, in **seconds**.  The "
         "clock a piece with no tempo has, and what an `Envelope` is "
         "usually read against — `on <points> elapsed`.  Defined in "
         "`audio.ges` rather than supplied, but it belongs beside `beat`: "
         "they are the two answers to \"how far in are we\"."),
    )),
)

#: `# ── Oscillators ────` — the section headers the library files already
#: carry.  They are the author's own grouping and a better one than
#: anything a generator could infer, so the pages simply keep them.
_SECTION = re.compile(r"^#\s*──\s*(.*?)\s*─*\s*$")

#: `name : Type`, and not `name := …` or `name :: …`.
_SIG = re.compile(r"^([A-Za-z_][\w']*)\s*:(?![:=])\s*(.*)$")
#: `(++) : [: a :] -> …` — an operator names itself in brackets.
_OPSIG = re.compile(r"^\((\S+?)\)\s*:(?![:=])\s*(.*)$")
#: `Score a := Note a` — a data declaration and its parameters.
_TYPE = re.compile(r"^([A-Z][\w']*)((?:\s+[a-z][\w']*)*)\s*:=\s*(.*)$")
#: `         | Rest` — an alternative on its own line.
_ALT = re.compile(r"^\s*\|\s*(.*)$")
_CLASS = re.compile(r"^class\s+(.*?)(?:\s+where)?\s*$")
_INSTANCE = re.compile(r"^instance\s+(.*?)(?:\s+where)?\s*$")
_ALIAS = re.compile(r"^type\s+([A-Z][\w']*)((?:\s+[a-z][\w']*)*)\s*=\s*(.*)$")
#: `internal`, alone on its line.
_INTERNAL = re.compile(r"^internal\s*$")


@dataclass
class Entry:
    """One name, and everything a reader wants next to it."""

    name: str
    #: `value`, `operator`, `type`, `class`, `instance` or `alias`.
    kind: str
    #: The line the author wrote, verbatim — a signature, or a `:=` head.
    signature: str
    #: The `#:` block above it, already stripped of its markers.
    doc: list = field(default_factory=list)
    #: The `# ── … ──` heading it appears under, or `""`.
    section: str = ""
    #: Below this file's `internal` marker?
    internal: bool = False
    #: 1-based, in its own file — what `--query` and an editor count in.
    line: int = 0
    #: For a `type`: its constructors, as written.
    alternatives: list = field(default_factory=list)
    #: Which library it came from.  Filled in by whoever gathers several
    #: files together — the pages know already, the editor's search does
    #: not, since it puts all six in one list.
    library: str = ""


def doc_above(lines: list, index: int) -> list:
    """The comment block immediately above `lines[index]`, in source order.

    The same rule `typecheck._doc_above` uses, and the same reason: a blank
    line ends the block, because a comment separated from a declaration is
    about something else.  Not shared with it because that one takes a
    source and a line number and this one is already walking a list, and
    threading a second caller through it would be the more coupled of the
    two.
    """
    out = []
    i = index - 1
    while i >= 0:
        text = lines[i].strip()
        if not text.startswith("#"):
            break
        # A section header is not a doc comment, and swallowing one would
        # put a heading in the prose of whatever happened to follow it.
        if _SECTION.match(text):
            break
        # **Indentation inside the block is kept.**  Only the marker and
        # the one space after it come off, because a doc comment may hold
        # an indented example or a bulleted list and `.strip()` turned
        # both into prose — `signal.ges`'s three `sync` cases ran together
        # into one paragraph, and `fm`'s example line read as a sentence.
        body = text[2:] if text.startswith("#:") else text[1:]
        out.append(body[1:] if body.startswith(" ") else body)
        i -= 1
    return [line.rstrip() for line in reversed(out)]


def entries_of(source: str) -> list:
    """Every declaration in one library file, in the order it is written."""
    lines = source.split("\n")
    out: list = []
    section = ""
    internal = False
    for i, raw in enumerate(lines):
        line = raw.rstrip()
        head = _SECTION.match(line)
        if head:
            section = head.group(1)
            continue
        if _INTERNAL.match(line):
            internal = True
            continue
        # A continuation of the data declaration above — `| Rest`.
        alt = _ALT.match(raw)
        if alt and out and out[-1].kind == "type":
            out[-1].alternatives.append(alt.group(1).strip())
            continue
        if not line or line.startswith((" ", "\t", "#")):
            continue

        def add(name, kind, signature, alternatives=()):
            out.append(Entry(name=name, kind=kind, signature=signature,
                             doc=doc_above(lines, i), section=section,
                             internal=internal, line=i + 1,
                             alternatives=list(alternatives)))

        found = _ALIAS.match(line)
        if found:
            add(found.group(1), "alias", line)
            continue
        found = _TYPE.match(line)
        if found:
            add(found.group(1), "type", line, [found.group(3).strip()])
            continue
        found = _CLASS.match(line)
        if found:
            add(found.group(1).split()[0], "class", line)
            continue
        found = _INSTANCE.match(line)
        if found:
            add(found.group(1), "instance", line)
            continue
        found = _OPSIG.match(line)
        if found:
            add(found.group(1), "operator", line)
            continue
        found = _SIG.match(line)
        if found:
            add(found.group(1), "value", line)
            continue
        # Anything else is an equation — `f x = …` — and an equation for a
        # name that already has a signature is not a second entry.  One with
        # no signature is a definition the library declined to promise a
        # type for, and is left out for that reason rather than missed.
    return out


def _anchor(name: str) -> str:
    """A GitHub-flavoured heading anchor for a name.

    Operators are mostly punctuation, and punctuation is what the anchor
    rule throws away — `'`, `>|` and `@` all become the empty string, so
    the index linked three names to the top of the page and to each
    other.  A name whose slug comes out empty is spelled by the code
    points instead: `op-64` for `@`, `op-62-124` for `>|`.  Unlovely,
    unique, and stable — an operator keeps its anchor when the page is
    reordered, which anchoring on position would not.

    `_body` emits the matching `<a id=…>` beside the heading, because
    the slug GitHub would compute from `` `@` `` is the empty one.
    """
    slug = _github_slug(name)
    if slug:
        return slug
    return "op-" + "-".join(str(ord(ch)) for ch in name)


def _github_slug(name: str) -> str:
    """What GitHub itself makes of a heading — empty for an operator."""
    return re.sub(r"[^\w -]", "", name).strip().lower().replace(" ", "-")


def render(title: str, when: str, path: str, entries: list) -> str:
    """One library's page."""
    public = [e for e in entries if not e.internal]
    private = [e for e in entries if e.internal]
    out = [f"# {title}", "",
           f"*{when}*", "",
           f"Source: `gestate/{path}` — "
           f"{len(public)} public, {len(private)} internal.", "",
           "<!-- Generated by `python -m gestate.reference`. "
           "Do not edit by hand. -->", ""]

    if private:
        out += [f"Everything below `{path}`'s **`internal`** marker is "
                "listed at the end, under [Internals](#internals).  Those "
                "names are the library's own machinery: they are documented "
                "because an editor may show you one, not because they are "
                "yours to call.", ""]

    out += _index(public)
    out += _section_bodies(public)
    if private:
        out += ["", "---", "", "## Internals", "",
                "**Not callable from another file.**  Listed so that a name "
                "you meet in a stack trace or a definition can be looked "
                "up.", ""]
        out += _section_bodies(private, depth=3)
    return "\n".join(out).rstrip() + "\n"


def _index(entries: list) -> list:
    """The names, up front, so the page can be scanned before it is read."""
    if not entries:
        return []
    out = ["## Index", ""]
    line = "  ".join(f"[`{e.name}`](#{_anchor(e.name)})" for e in
                     sorted(entries, key=lambda e: e.name.lower()))
    return out + [line, ""]


def _section_bodies(entries: list, depth: int = 2) -> list:
    out: list = []
    section = None
    for entry in entries:
        if entry.section != section:
            section = entry.section
            if section:
                out += ["", "#" * depth + f" {section}", ""]
        out += _body(entry, depth + 1)
    return out


_KINDS = {"value": "", "operator": "operator", "type": "data",
          "class": "class", "instance": "instance", "alias": "type alias"}


def _body(entry: Entry, depth: int) -> list:
    label = _KINDS.get(entry.kind, entry.kind)
    head = "#" * depth + f" `{entry.name}`"
    if label:
        head += f"  <sub>{label}</sub>"
    # An all-punctuation name gets an explicit anchor: the slug GitHub
    # computes from the heading text would be empty, and `_anchor` has
    # spelled it `op-…` for the index to point at.
    if not _github_slug(entry.name):
        head += f' <a id="{_anchor(entry.name)}"></a>'
    out = ["", head, "", "```", entry.signature]
    out += [f"    {alt}" for alt in entry.alternatives[1:]]
    out += ["```", ""]
    if entry.doc:
        out += ["\n".join(entry.doc), ""]
    return out


def index_page() -> str:
    """`doc/ref/index.md` — what is in scope when, which is the question
    that comes before any of the others."""
    return "\n".join([
        "# Reference", "",
        "<!-- Generated by `python -m gestate.reference`. "
        "Do not edit by hand. -->", "",
        "Every name the standard library defines, with the signature and "
        "the prose the library itself carries.  For *why* the language is "
        "shaped this way see `spec/`; to learn it in order see "
        "`doc/manual.md`; this is for looking things up.", "",
        "## What is in scope when", "",
        "**Which library you get depends on the backend**, because the "
        "backends assemble different preludes in front of your file.  This "
        "is the table to check first when a name you are sure exists is "
        "not defined.", "",
        "| you are writing | you run | in scope |",
        "|---|---|---|",
        "| plain code | `typecheck` | Prelude |",
        "| a synth | `audioeditor`, `audioperform` | "
        "Prelude, Signals, Audio, Synthesis |",
        "| a synth with a piece | `audioperform` | "
        "…and Music |",
        "| a piece for MIDI | `midi` | Prelude, Music |",
        "| a canvas | `gui`, the editor\'s canvas tab | "
        "Prelude, Signals, Canvas |",
        "",
        "## What each one expects you to declare", "",
        "**A backend finds your program by name.**  It looks for one "
        "particular declaration and builds its entry point out of it, so a "
        "program that spells the name differently is not a broken program "
        "— it is a program that backend cannot see at all, and the error "
        "says the name is missing rather than that you meant another one.  "
        "This is the other half of the table above.", "",
        "| you are writing | it must declare | the backend builds |",
        "|---|---|---|",
        "| plain code | `main : a` | — |",
        "| a synth | `sound : Sig Float` — or `Sig Stereo` for two "
        "channels | `main = sound` |",
        "| a piece for MIDI | `score : [: Void :]` **and** `bpm : Int` "
        "(*no* `main`) | `main = (bpm, layout score)` |",
        "| a synth with a piece | `sound`, `score`, `bpm`, and a "
        "`voices` bank per instrument | `main = (bpm, layVoices score)`, "
        "read beside `main = sound` |",
        "| a canvas | `substrate : Sig Sub` | `main = substrate` |",
        "", "Optional, and recognised wherever they make sense:", "",
        "- **`voices NAME N VOICE : Sig Float`** — a bank of `N` copies of "
        "one voice, summed.  Its name is bound to that sum, so mixing "
        "banks is ordinary signal arithmetic.  `voices.NAME` in a score "
        "assigns notes to it, and names it *lexically*, which is how the "
        "type checker can say a piece fits an instrument.",
        "- **`NAME = mkKnob V`** — a control-rate parameter.  The editors "
        "draw a knob beside the line that declares it.",
        "- **`instance FromMIDI P where noteOn ch p v = …`** — how a MIDI "
        "note becomes your payload `P`.  It says a bank *can* be played "
        "from a keyboard, not that it is: which bank listens is a switch "
        "in the editor.",
        "- **`bpm : Int`** — the tempo.  A synth with no score keeps the "
        "default of 120.",
        "",
        "## Names no page lists", "",
        "**Three names are written by the renderer, not by a library**, so "
        "they appear in no `.ges` file and therefore on no page below.  "
        "They are in scope all the same.", "",
        "| name | type | in scope when |",
        "|---|---|---|",
        "| `sampleRate` | `Float` | any audio or canvas program |",
        "| `constSig` | `a -> Sig a` | **internal** — write `!x`, or "
        "`!(f x)` for a computed value |",
        "| `beat` | `Sig Float` | a **scored** synth only |",
        "",
        "`beat` is what time it is in beats, at audio rate — `sine (5.0 + "
        "beat)` rises a hertz a beat.  It is the renderer's because it "
        "reads the piece's own `bpm`, and a synth with no piece has no "
        "tempo to answer with: naming it there is `Unknown global 'beat'`, "
        "which is the truth.  `music.ges`'s `ticksPerBeat` is the layout "
        "resolution and a different thing.",
        "",
        "## Pages", "",
    ] + ["- **[The language](language.md)** — the forms the compiler "
         "provides: `chan`, `wait`, `:::`, `delay`, `gfix`, `!`.  Declared "
         "by no library, and so missing from every page below."] + [
        f"- **[{title}]({name.replace('.ges', '')}.md)** — {when}"
        for name, title, when in LIBRARIES] + [
        "", "## Asking the compiler instead", "",
        "The reference is a document; these are the same questions asked "
        "of the program you are actually writing, which knows things a "
        "document cannot.", "",
        "```",
        "python -m gestate.typecheck f.ges --audio --query NAME   "
        "# a name's type and its prose",
        "python -m gestate.typecheck f.ges --audio --fits TYPE    "
        "# what could stand where TYPE is wanted",
        "python -m gestate.typecheck f.ges --audio --holes        "
        "# every `_`, and what belongs in it",
        "```", "",
        "In the editor the same three are a command: `what` over a name, and "
        "`Tab` at a `_`.  The **[reference] button** opens these pages in "
        "the editor.",
    ]) + "\n"


def all_entries() -> list:
    """Every library's entries, plus the language's, each tagged.

    **The language first**, because it is what a reader looking for
    `wait` or `chan` is looking for, and because it is in none of the
    library files — they are desugaring forms, not definitions, so
    `entries_of` has nothing to find.  Searching the reference for the
    most-used word in the language used to return nothing at all.

    Lifted out of `audiopygame` when its reference browser went
    (`spec/workbench.md`): the browser was chrome over an index, and the
    index is what both a page and a palette are made of.
    """
    from pathlib import Path as _Path

    here = _Path(__file__).parent
    out = list(language_entries())
    for name, title, _when in LIBRARIES:
        for entry in entries_of((here / name).read_text()):
            entry.library = title
            out.append(entry)
    return out


def language_entries() -> list:
    """The primitives as `Entry` values, for a reader that searches.

    The pages are one reader and the editor's `[ref]` is another, and the
    second could not see these at all: it gathers `entries_of` over the six
    libraries, and a form that is in no library is in no list.  Searching
    `wait` in the editor found nothing, which is a poor answer about the
    most-used word in the language.
    """
    out = []
    for section, entries in PRIMITIVES:
        for name, type_, prose in entries:
            out.append(Entry(
                name=name.strip("()"),
                kind="operator" if name.startswith("(") else "value",
                signature=f"{name} : {type_}",
                doc=[prose],
                section=section,
                library="Language",
            ))
    return out


def language_page() -> str:
    """`language.md` — the primitives, which no library declares.

    Written by hand because there is no source to extract: they are
    desugaring forms in `desugar.py` and cases in `infer.py`, not
    definitions.  A generator that reads `.ges` files cannot see them, and
    for a long time neither could anybody reading the reference.
    """
    out = [
        "# The language", "",
        "The forms the *compiler* provides.  Nothing declares these — they "
        "are not functions in a library but shapes the desugaring knows, "
        "so unlike every other page here this one is written rather than "
        "generated.  Their types are `infer.py`'s rules.", "",
        "`FaL` and `ExL` are the two later modalities — written that way "
        "here and everywhere a *type* is spelled, because the circled "
        "quantifiers the papers use are a combining mark and garble in a "
        "monospace font.  `doc/manual.md` §6 is what they mean and why a "
        "signal needs both.", "",
    ]
    for section, entries in PRIMITIVES:
        out += [f"## {section}", ""]
        for name, type_, prose in entries:
            out += [f"### `{name}`", "", "```", f"{name} : {type_}", "```",
                    "", prose, ""]
    out += [
        "## Why these are not in a library", "",
        "`wait c` is not a call — the desugaring turns it into an `EWait` "
        "node, and inference gives that node a type directly.  There is no "
        "`wait` to declare and nothing for the generator to read, which is "
        "why every page here listed the libraries and none listed the "
        "language.", "",
        "The practical consequence: **`python -m gestate.typecheck "
        "--query wait` has nothing to say about it either.**  This page is "
        "the answer to that question.", "",
    ]
    return "\n".join(out) + "\n"


def generate(root=None) -> dict:
    """`{relative path: text}` for the whole of `doc/ref/`."""
    here = Path(__file__).parent
    root = Path(root) if root is not None else here.parent
    pages = {"index.md": index_page(), "language.md": language_page()}
    for name, title, when in LIBRARIES:
        source = (here / name).read_text()
        pages[name.replace(".ges", "") + ".md"] = render(
            title, when, name, entries_of(source))
    return pages


def write(root=None) -> list:
    """Write `doc/ref/`, and say what changed."""
    here = Path(__file__).parent
    root = Path(root) if root is not None else here.parent
    out = root / "doc" / "ref"
    out.mkdir(parents=True, exist_ok=True)
    changed = []
    for name, text in generate(root).items():
        target = out / name
        if not target.exists() or target.read_text() != text:
            target.write_text(text)
            changed.append(name)
    return changed


def stale(root=None) -> list:
    """Which pages are behind the libraries — what `--check` reports."""
    here = Path(__file__).parent
    root = Path(root) if root is not None else here.parent
    out = root / "doc" / "ref"
    behind = []
    for name, text in generate(root).items():
        target = out / name
        if not target.exists() or target.read_text() != text:
            behind.append(name)
    return behind


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.reference",
        description="Generate doc/ref/ from the library sources.")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit non-zero if doc/ref/ is behind")
    args = ap.parse_args(argv)

    if args.check:
        behind = stale()
        if behind:
            print("doc/ref/ is out of date: " + ", ".join(behind))
            print("run `python -m gestate.reference`")
            return 1
        print("doc/ref/ is up to date")
        return 0
    changed = write()
    print(f"wrote {len(changed)} page(s)" +
          (": " + ", ".join(changed) if changed else " — nothing to do"))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
