"""Where a graph node came from — which file, and which line of it.

`audioir.Node.origin` is a path of the definitions a node was inlined
through — `sound/raw/phase/driven/knob/source#0`.  It is deliberately *not*
a source position: stage 5 migrates state by comparing origins across a
recompile, and a position moves whenever anyone adds a line above it, which
would throw away an oscillator's phase for an edit that did not touch it
(`spec/liveaudio.md` stage 5).

So the two facts live apart on purpose, and joining them is this module's
whole job.  The caller that wants it is an environment that shows a control
*where it is declared* — a knob beside the line introducing it, rather than
in a panel off to one side.

**Four files, not one.**  A running synth is assembled from `prelude.ges`,
`signal.ges`, `audio.ges` and the author's own source, and an editor may
want to open any of them: `lowpass` is as editable as `sound` is, and a
site that said only "line 41" would be useless for it.  Every `Site`
therefore names its file and carries a line **within that file**.

Getting that right is the work here, because the four are combined two
different ways and only one of them preserves coordinates:

* `signal.ges` and `audio.ges` are prepended as **text** by
  `audio.assemble`, so their spans are already in assembled coordinates and
  a line range identifies them exactly.  So is the author's source.
* `prelude.ges` is merged as a **module** (`prelude.merge` parses it
  separately), so its spans are in *its own* coordinates and start again at
  1.  A line-range test would happily place `showFloat` in the middle of
  the author's file.  Names are what distinguish it, which is why this
  module reads the defining names of each file rather than trusting
  arithmetic alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

#: The file an author is editing, when no better name was given.
UNNAMED = "<source>"


@dataclass(frozen=True)
class Site:
    """One graph node, placed in a file.

    Lines are **1-based** and columns **0-based** — the convention a text
    widget wants, and not the tokenizer's, which counts lines from 0.
    """
    node: int
    kind: str
    clock: str
    origin: str
    #: The innermost definition in `origin` that could be placed at all.
    name: str
    #: Which file `line` is a line of.  `path` is where it can be opened,
    #: and is `None` for the author's own source, whose location is the
    #: caller's business rather than this module's.
    file: str
    path: Path | None
    line: int
    column: int
    end_line: int
    end_column: int

    @property
    def is_control(self) -> bool:
        """Is this a source the host supplies a value for once per block?

        Both halves are load-bearing.  `clock` is only meaningful on a
        *source* — every other node keeps the default `"audio"` and nothing
        reads it (`fixme.md` F93) — so asking `clock == "control"` alone
        would be asking a question of a field that has no answer.  And an
        audio-rate source is the sample clock, which there is nothing for a
        knob to do to.
        """
        return self.kind == "source" and self.clock == "control"

    @property
    def is_prelude(self) -> bool:
        """Is this in a file the author did not write but may still edit?"""
        return self.path is not None


def _blanked(source: str) -> str:
    from .audiovoices import blanked

    return blanked(source)


def _prelude_path(name: str) -> Path:
    return Path(__file__).with_name(name)


@lru_cache(maxsize=None)
def _names_of(text: str) -> frozenset:
    """The supercombinator names a source text defines.

    Cached on the text because the four prelude files never change within a
    run, and this is called once per placement — which an editor does on
    every rebuild.
    """
    # `prelude._defined_names` rather than a copy: it is the same question
    # `merge` asks to decide shadowing, and two answers to it would be two
    # opinions about which definition the author owns.
    from .prelude import _defined_names
    from .syntax import parse

    return frozenset(_defined_names(parse(text, descend_fixity=False).items))


def _regions(source: str = "") -> tuple:
    """`(signal_start, audio_start, source_start)`, 0-based assembled lines.

    `source` decides which assembly is meant, and in two ways: a program
    carrying its own `score` is compiled with `music.ges` in front of the
    author's first line, and one that **draws** is compiled with `gui.ges`
    in front of `audio.ges` (`audio.preludes`).  Passing the source in
    rather than assuming is what keeps a performance's — and a substrate's
    — knobs on the right lines.

    Getting the second one wrong did not shift the numbers so much as
    throw them away: `gui.ges` is some three hundred lines, so every
    definition in a file with a `substrate` fell *past* the region
    `declaration_sites` believes the author's file to be, was placed
    nowhere, and the program came up saying "no parameters" with its knobs
    in plain sight.

    Derived from the same strings `audio.assemble` concatenates, and by
    counting newlines in the exact prefix rather than by adding up file
    lengths — a file that does or does not end in a newline shifts the
    total, and this cannot be off by one for that reason.
    """
    from .audio import _SIGNAL, has_scene, preludes

    # Where `audio.ges` begins: after `signal.ges`, and after `gui.ges` too
    # when there is one.  The same order `audio._AUDIO_GUI` builds, counted
    # off the same texts.
    before_audio = _SIGNAL + "\n"
    if source and has_scene(source):
        before_audio += _prelude_path("gui.ges").read_text() + "\n"
    head = preludes(source) + "\n"
    if source and _has_score(source):
        head += (Path(__file__).with_name("music.ges")).read_text() + "\n"
    return (0, before_audio.count("\n"), head.count("\n"))


def _has_score(source: str) -> bool:
    import re

    return re.search(r"^score\s*[:=]", source, re.M) is not None


def prelude_lines(source: str = "") -> int:
    """How many lines the assembly puts before the author's first one."""
    return _regions(source)[2]


#: `Pos(869,20)` — how the tokenizer's positions reach a `ParseError`.
_POS = re.compile(r"Pos\((\d+),\s*(\d+)\)")
#: `(at 869:11–869:16)` and `(at 869:11)` — how a span reaches a type error.
_AT = re.compile(r"\(at (\d+):(\d+)(?:–(\d+):(\d+))?\)")


def in_source(message: str, source: str = "", path=None) -> str:
    """An error message with its line numbers moved back into the author's file.

    **Every position a compiler error carries is in *assembled*
    coordinates**, because `audio.assemble` hands the compiler one text
    with the preludes on the front — so a mistake on line 3 of a synth is
    reported at line 872, and the number is not wrong so much as answering
    a question nobody asked.  It got worse rather than started when
    `synth.ges` was prepended: the offset went from 182 lines to 869.

    Positions are 0-based inside the compiler (`Pos(0,0)` is the first
    character) and 1-based here, because that is what an editor's gutter
    counts in and this text is read beside one.

    A position that lands *before* the author's first line is in a prelude,
    and is said to be rather than translated into a negative number: it
    means the error is in `signal.ges`, `audio.ges`, `synth.ges` or
    `music.ges`, which is a different kind of problem and worth not
    disguising.

    **And one that lands after the author's last line is in the entry**,
    which is generated: `audio._entry` writes `main = sound`, so a program
    with no `sound` in it fails at a position that is real, is in the
    assembled text, and is in nobody's file.  Translated naively it named
    line 11 of a two-line program — a number an editor will believe and
    put a mark on.  Said instead, for the same reason the prelude is.
    """
    offset = prelude_lines(source)
    name = Path(path).name if path else None
    written = len(source.split("\n")) if source else 0

    def where(line: str, col: str) -> str:
        n = int(line) - offset
        if n < 0:
            return f"prelude line {int(line) + 1}:{col}"
        if written and n >= written:
            return f"entry line {n - written + 1}:{col}"
        return f"{name}:{n + 1}:{col}" if name else f"line {n + 1}:{col}"

    def pos(match) -> str:
        return where(match.group(1), match.group(2))

    def at(match) -> str:
        start = where(match.group(1), match.group(2))
        if match.group(3) is None:
            return f"(at {start})"
        end = where(match.group(3), match.group(4))
        return f"(at {start}–{end})"

    return _AT.sub(at, _POS.sub(pos, message))


def cli_error(exc, path=None) -> str:
    """`str(exc)` with its positions moved into the author's file.

    The one-liner every audio CLI wants at its boundary — see `in_source`
    for why an untranslated message names a line nobody has.  It never
    raises: losing the error to the thing that was meant to make it
    readable would be the worse failure.
    """
    try:
        text = Path(path).read_text() if path else ""
        return in_source(str(exc), text, path)
    except Exception:                                       # noqa: BLE001
        return str(exc)


def declaration_sites(analysis, source: str,
                      path: str | None = None) -> dict[str, tuple]:
    """`name → (file, path, line, column, end_line, end_column)`.

    Every definition that can be placed in a file — the author's and the
    two prepended preludes' in assembled coordinates, `prelude.ges`'s in its
    own.  A name with several equations spans all of them, so a multi-clause
    definition is one region rather than several.

    Resolution order matters and is not arbitrary.  `prelude.ges` is
    checked **first**, because it is the one file whose spans mean nothing
    in assembled coordinates — left to the line test, a definition 200
    lines into it would land in the author's file whenever the author's
    file is long enough to reach there.  A name the author has *shadowed*
    is excluded from that first test: `prelude.merge` renames the prelude's
    copy and leaves the plain name to the author, so the plain name is
    theirs.
    """
    from .prelude import load

    _sig_start, audio_start, source_start = _regions(source)
    source_end = source_start + len(source.splitlines())

    signal_text = _prelude_path("signal.ges").read_text()
    audio_text = _prelude_path("audio.ges").read_text()
    signal_names = _names_of(signal_text)
    audio_names = _names_of(audio_text)
    core_names = _names_of(load())
    # The *blanked* source: a `voices` declaration is not gestate syntax,
    # and `_names_of` parses.  Reading the raw text failed every placement
    # in a program with a bank — reported as "could not place the knobs",
    # which is true and says nothing about why.
    user_names = _names_of(_blanked(source))

    def place(name: str, start_line: int) -> tuple | None:
        """`(file, path, base)` — the file, and the line its line 1 is."""
        if name in core_names and name not in user_names:
            # Own coordinates: `prelude.ges` is merged as a module, so its
            # spans never went through `assemble` at all.
            return ("prelude.ges", _prelude_path("prelude.ges"), 0)
        if source_start <= start_line < source_end:
            return (path or UNNAMED, None, source_start)
        if name in signal_names:
            return ("signal.ges", _prelude_path("signal.ges"), 0)
        if name in audio_names:
            return ("audio.ges", _prelude_path("audio.ges"), audio_start)
        return None

    out: dict[str, tuple] = {}
    for sc in analysis.program.scs:
        spans = [eq.span for eq in sc.equations if eq.span is not None]
        if not spans:
            continue
        first = min(spans, key=lambda s: s.start.line)
        final = max(spans, key=lambda s: s.end.line)
        where = place(sc.name, first.start.line)
        if where is None:
            # A generated helper, `main` from `_entry`, or anything else
            # with no file a person could open.  Absent rather than guessed.
            continue
        file, file_path, base = where
        out[sc.name] = (file, file_path,
                        first.start.line - base + 1, first.start.col,
                        final.end.line - base + 1, final.end.col)
    return out


def _innermost(origin: str, known: dict) -> str | None:
    """The last component of `origin` that can be placed, if any.

    Right to left because a path runs outermost-first: `sound/lowpass/…`
    means `sound` *calls* `lowpass`, and the innermost definition is the one
    that actually introduced the node.  The final component is the former
    and its counter (`scan#0`), never a definition.
    """
    for part in reversed(origin.split("/")[:-1]):
        if part in known:
            return part
    return None


def _authored(origin: str, known: dict) -> str | None:
    """The innermost component of `origin` the *author* wrote, if any.

    `known[name][1]` is the file a definition can be opened in, and it is
    `None` exactly for the author's own source.
    """
    for part in reversed(origin.split("/")[:-1]):
        if part in known and known[part][1] is None:
            return part
    return None


def sites(graph, analysis, source: str, path: str | None = None) -> list[Site]:
    """Every node that resolves to a definition in some openable file.

    **A control source is placed at the author's declaration**, not at the
    innermost definition that produced it — which for every other kind of
    node is the right answer and for this one is not.

    The difference appeared with `knob`: `level = knob 0.6` puts a source
    node at origin `sound/level/knob/source#0`, whose innermost placeable
    component is `knob` — a definition in `audio.ges`.  Both of a program's
    knobs would then be called `knob`, be placed on the same prelude line,
    and — because an editor keys a parameter's *value* by name — share one
    slider between them.

    A knob is the one node whose name is a promise to a person: it is what
    they think they are turning.  So it is resolved to the definition they
    wrote, and only falls back to the innermost when a prelude declares a
    parameter of its own.
    """
    known = declaration_sites(analysis, source, path)
    out = []
    for node in graph.nodes:
        name = _innermost(node.origin, known)
        if node.kind == "source" and node.clock == "control":
            name = _authored(node.origin, known) or name
        if name is None:
            continue
        file, file_path, line, column, end_line, end_column = known[name]
        out.append(Site(node=node.id, kind=node.kind, clock=node.clock,
                        origin=node.origin, name=name, file=file,
                        path=file_path, line=line, column=column,
                        end_line=end_line, end_column=end_column))
    return out


def located(source: str, *, rate: int = 22050, entry: str = "sound",
            path: str | None = None) -> tuple:
    """`(sites, graph)` from source text, analysing once rather than twice.

    `extract(source)` analyses internally, so calling it and then analysing
    again to read spans would compile the program twice — which at ~200 ms
    of front end is the difference between an editor that can place its
    knobs on a rebuild and one that cannot.

    **The graph comes back with the sites** because a `Site.node` is an
    index into *this* graph and means nothing against another one.  A caller
    that wants a node's channel or type — the editor does, to decide a
    knob's range — has to read it out of the graph the sites were placed
    in; reading it out of the one that happens to be *playing* is a bug
    that waits for an edit which adds or removes a node.
    """
    from .audio import assemble
    from .audioextract import extract_analysis
    from .audioscore import assemble_performance
    from .pipeline import analyse

    # A program with its own `score` needs the music prelude and its piece,
    # or `'` and `>>=` are unknown globals — the same choice
    # `audioperform.graph_of` makes, and it has to be the same one.
    program = (assemble_performance(source, "", rate) if _has_score(source)
               else assemble(source, rate))
    analysis = analyse(program)
    graph = extract_analysis(analysis, entry=entry, rate=rate)
    return sites(graph, analysis, source, path), graph


def locate(source: str, *, rate: int = 22050, entry: str = "sound",
           path: str | None = None) -> list[Site]:
    """The sites alone, for a caller with no use for the graph."""
    return located(source, rate=rate, entry=entry, path=path)[0]


def controls(source: str, *, rate: int = 22050, entry: str = "sound",
             path: str | None = None) -> list[Site]:
    """The control-rate sources, in the order they appear.

    This is the one an environment calls: each is a parameter the running
    graph will accept a value for between blocks, at the line that declares
    it.  Sorted by position rather than by node id, because what the caller
    is about to do is lay them out down a page.

    **One per channel**, and a synth may declare as many as it likes: two
    *rates* is the engine's ceiling and several control channels all tick
    at the same one.  Each is its own source node with its own origin, so
    each keeps its value across an edit independently — which is why they
    are separate channels rather than fields of one record, where adding a
    parameter would reset the others (stage 5 migrates by shape).

    The order here is the order they are *written*.  It is deliberately not
    `Graph.control_sources()`'s order, which is by node id and is what the
    control buffer is indexed by: a caller laying knobs down a page wants
    the file's order, and a caller filling the buffer wants the graph's.
    Confusing the two puts the wrong value in the wrong knob, so they are
    two functions rather than one.
    """
    return controls_and_graph(source, rate=rate, entry=entry, path=path)[0]


def controls_and_graph(source: str, *, rate: int = 22050,
                       entry: str = "sound",
                       path: str | None = None) -> tuple:
    """`controls`, with the graph its `Site.node`s index into.

    See `located`: the pair has to be read together, and an environment
    rebuilding while a synth plays has an older graph within reach that
    would answer every question plausibly and some of them wrongly.
    """
    found, graph = located(source, rate=rate, entry=entry, path=path)
    return sorted((s for s in found if s.is_control),
                  key=lambda s: (s.file, s.line, s.column)), graph


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv=None) -> int:
    """`python -m gestate.audiospans <file>` — the placement, as a table.

    Worth having beyond debugging: the join is the sort of thing that can be
    wrong by one line for a year without anything failing, and reading it
    against the files is how a person checks it.
    """
    import argparse
    import sys

    ap = argparse.ArgumentParser(
        prog="python -m gestate.audiospans",
        description="Show where each node of a synth's graph was written.")
    ap.add_argument("file")
    ap.add_argument("--rate", type=int, default=22050)
    ap.add_argument("--controls", action="store_true",
                    help="only the control-rate sites — the ones an "
                         "environment would offer a knob for")
    ap.add_argument("--source", action="store_true",
                    help="print the line each site names, read back from "
                         "the file it names")
    args = ap.parse_args(argv)

    path = Path(args.file)
    source = path.read_text()
    try:
        found = (controls if args.controls else locate)(
            source, rate=args.rate, path=path.name)
    except Exception as exc:                       # noqa: BLE001 — a CLI
        print(f"gestate: {type(exc).__name__}: "
              f"{cli_error(exc, args.file)}", file=sys.stderr)
        return 1

    if not found:
        print("no control-rate sites" if args.controls else "no sites")
        return 0

    width = max(len(s.name) for s in found)
    for s in found:
        where = f"{s.file}:{s.line}"
        print(f"  {s.name:<{width}}  {s.kind:<6} {s.clock:<7} {where}")
        if args.source:
            text = (s.path.read_text() if s.path else source).splitlines()
            print(f"  {'':<{width}}  | {text[s.line - 1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
