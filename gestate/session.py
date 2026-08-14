"""What a gesture means — `spec/workbench.md`, and no toolkit in here.

`Workbench` is the model: a playing instrument, a rebuild worker, a
transport, parameters and a keyboard.  This is the layer above it, and
its whole job is:

    command : (Workbench, args) -> (Workbench', sentence)

A **transition**, in other words, and four things fall out of that shape
rather than having to be built:

* **Undo is the model's.**  A transition on a small state is undone by
  keeping the state before it.
* **A session is a list of commands**, so recording, replaying and
  testing are one mechanism — `spec/verification.md`'s transcript, one
  floor up.
* **A test reads as documentation**: names in, sentences out.
* **The boundary carries names and arguments and nothing else** — no
  handles, no callbacks, no pointers into anybody's heap.

**The command list is not written here.**  `gestate/command.ges`
declares every verb with a type and a sentence, and this reads that
file.  A capability therefore cannot exist without appearing in the
palette, because appearing in the palette is what declaring one *is* —
the same reason `doc/ref/` cannot drift from the libraries it describes.
What this module owns is the *doing*: one handler per verb, and a test
beside it that neither list has an entry the other lacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

#: Where the vocabulary is declared.
COMMANDS = Path(__file__).with_name("command.ges")

#: The symbols worth a table, in the order they are worth one.
#:
#: **Ordered, and the letters follow the order.**  `a` is the first cell
#: because it is the first thing you reach for, not because `>` starts
#: with an `a` — a mnemonic would need a second thing to remember and
#: would run out at the tenth symbol.  Position is the mnemonic, and the
#: grid is what makes position readable.
#:
#: What is in it: the characters gestate's own grammar leans on, sorted
#: by how hard a European layout makes them.  `=>` and `->` are here as
#: whole tokens because typing one is two awkward keys, not one.
SYMBOLS = [
    # The characters a layout hides — what the table was asked for.
    (">", "greater"), ("<", "less"), ("|", "bar"), ("\\", "backslash"),
    ("[", "open bracket"), ("]", "close bracket"),
    ("{", "open brace"), ("}", "close brace"),
    ("`", "backtick"), ("~", "tilde"), ("^", "caret"), ("@", "at"),
    ("$", "dollar"), ("&", "ampersand"), ("#", "hash"), ("_", "hole"),
    ("'", "note quote"), ("\"", "string quote"),
    # Then every operator the language has.
    #
    # **Read off the libraries, never remembered.**  A picker offering an
    # operator gestate does not have would teach a wrong vocabulary from
    # inside the editor, which is worse than a short table — `/\\` was in
    # a draft of this list and appears in no `.ges` file anywhere.
    ("->", "arrow"), ("=>", "lambda"), ("<-", "bind"),
    ("==", "equal"), ("/=", "not equal"),
    ("<=", "at most"), (">=", "at least"),
    ("++", "append sequence"), ("||", "overlay or"),
    (">>=", "bind then"), (":::", "cons signal"), ("\\/", "join union"),
    ("[:", "open score"), (":]", "close score"),
    (">|", "clip"), ("|<", "pan"), ("|*", "scale"), ("|/", "divide by"),
    ("+", "plus"), ("-", "minus"), ("*", "times"), ("/", "over"),
]


def _letter(i: int) -> str:
    """The keys that reach the `i`th cell — `a` … `z`, then `aa`, `ab` …

    **A prefix, not a code.**  `a` is also the start of `aa`, so typing
    it narrows to both and picks the shorter — which is what makes the
    first twenty-six one keystroke while the rest are still reachable by
    name.  A scheme where every label was two characters would cost the
    common ones their whole point.
    """
    if i < 26:
        return chr(ord("a") + i)
    j = i - 26
    return chr(ord("a") + j // 26) + chr(ord("a") + j % 26)


#: Where the snippets live.  One file, one idea; the directory is the
#: list, so adding one is adding a file and nothing else.
TEMPLATES = Path(__file__).with_name("templates")


@dataclass(frozen=True)
class Verb:
    """One command, as `command.ges` declares it."""

    name: str
    #: The argument types, in order — `["Int", "Int"]` for `loop`.
    args: tuple
    #: The `#:` comment, first sentence: what the palette shows.
    summary: str
    #: The keystroke that is a shortcut onto it, or `""`.
    key: str = ""

    @property
    def arity(self) -> int:
        return len(self.args)

    def __str__(self) -> str:
        # A lone type variable is whatever the named thing carries —
        # `set cutoff 0.42` or `set mode 3` — so the usage line says
        # `<value>` rather than `<a>`, which would only be readable to
        # somebody who had the signature open.
        spec = " ".join(f"<{'value' if len(a) == 1 else a.lower()}>"
                        for a in self.args)
        return f"{self.name} {spec}".strip()


def _type_name(node) -> str:
    """What to call one argument's type, for the palette.

    `Named a` is the interesting case: the *head* is what the view needs
    — it says "this argument is a name that exists" — and the phantom
    parameter is what the checker uses.  So the palette reads `Named`
    and the type system reads `Named Float`, from one signature.
    """
    from .syntax.ast import VApp, VConId, VWord

    if isinstance(node, VConId):
        return node.value
    if isinstance(node, VApp):
        return _type_name(node.fn)
    if isinstance(node, VWord):
        # A type *variable* — `set : Named a -> a -> Command`.  The
        # checker resolves it from the name in the first argument; the
        # palette cannot, and does not need to.
        return node.value
    return "?"


def _arrow_parts(node) -> list:
    """A signature's arguments and result, as type names.

    Reads the parsed form rather than the text, so `Int -> Int ->
    Command` and a reformatting of it are the same answer — and a
    constraint (`(FromCC a) => …`) is stepped through rather than
    parsed a second way.
    """
    from .syntax.ast import VFunc, VOpPhrase

    # `(FromCC a) => Named a -> Command` parses as a function *type*
    # whose parameters are the constraints.  The palette does not care
    # which class; the checker does, at the use site.
    while isinstance(node, VFunc):
        node = node.body
    if isinstance(node, VOpPhrase):
        return [_type_name(a) for a in node.atoms if a != "->"]
    return [_type_name(node)]


#: `(path, mtime) -> the commands it declares`.
_VOCABULARY: dict = {}


def vocabulary(path: Path = COMMANDS) -> list:
    """Every command `command.ges` declares, in the order written.

    **Derived, never maintained.**  The order is the file's, so the
    palette reads in the order somebody thought about them rather than
    alphabetically, which is a worse order for learning.

    **Kept between calls, by the file's own timestamp.**  This used to
    say it was derived every time and that this was cheap; it is 650µs,
    which is a third of the two-millisecond poll spent re-reading a file
    that had not changed — measured, once `furniture` grew enough rows
    to make anybody look.  Keying on the mtime is what lets it stay
    honest: edit `command.ges` and the next poll re-reads it, so
    *derived, never maintained* is still true and is now also fast.
    """
    try:
        stamp = (str(path), path.stat().st_mtime)
    except OSError:
        stamp = (str(path), 0.0)
    if stamp in _VOCABULARY:
        return _VOCABULARY[stamp]
    from .audio import _authored

    source = path.read_text()
    sigs, _names = _authored(source)
    docs = _summaries(source)
    out = []
    for name, sig in sigs.items():
        parts = _arrow_parts(sig)
        if not parts or parts[-1] != "Command":
            # A helper or a type alias — only the verbs are the list.
            continue
        if "Command" in parts[:-1]:
            # **A combinator, not a verb.**  `andThen` takes commands
            # and so cannot be picked from a palette — there is no box
            # to type a command into.  Derived from the type rather
            # than kept on a list of exceptions, so a second combinator
            # needs no edit here.
            continue
        out.append(Verb(name=name, args=tuple(parts[:-1]),
                        summary=docs.get(name, ""), key=KEYS.get(name, "")))
    # One entry per timestamp, so an edit supersedes rather than adds.
    _VOCABULARY.clear()
    _VOCABULARY[stamp] = out
    return out


@dataclass(frozen=True)
class Snippet:
    """One template: what it is called, what it says, and what you get."""

    name: str
    #: The header's first sentence — what the palette shows.
    summary: str
    #: The whole header, as lines — the page you can read before choosing.
    doc: tuple
    #: The body, comments already off.  What `template` inserts.
    body: str


def _uncommented(lines) -> str:
    """A template's body: full-line comments off, blank runs collapsed.

    **Full lines only, and deliberately.**  Deciding whether a `#` part
    way along a line is a comment or a character in a string needs the
    tokenizer, and a snippet is not worth a second front end — so a
    template that wants a note kept puts it at the end of a line, and
    `templates/README.md` says so.

    The blank-run collapse is what makes the paste read as written: a
    header stripped from between two declarations leaves the blank lines
    that were around it, and three of them in a row is not what anybody
    wrote.
    """
    out, blank = [], False
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        if not line.strip():
            # One blank line between things, never a drift of them — and
            # none at all until something has been kept, so a stripped
            # header does not become a gap at the top of the paste.
            blank = bool(out)
            continue
        if blank:
            out.append("")
            blank = False
        out.append(line)
    return "\n".join(out) + "\n" if out else ""


def templates(where: Path = TEMPLATES) -> list:
    """Every snippet the directory holds, by name.

    **Derived from the files**, the way the palette is derived from
    `command.ges` and `doc/ref/` from the libraries: a template cannot
    exist without a name and a sentence, because that is what writing one
    *is*.  Sorted, because a directory has no order a reader can predict
    and the list is read by eye.
    """
    out = []
    if not where.is_dir():
        return out
    for path in sorted(where.glob("*.ges")):
        lines = path.read_text().splitlines()
        doc = [line.strip()[2:].strip() for line in lines
               if line.strip().startswith("#:")]
        out.append(Snippet(
            name=path.stem,
            summary=_plain(_first_sentence(" ".join(d for d in doc if d))),
            doc=tuple(_plain(d) for d in doc),
            body=_uncommented(lines)))
    return out


def _first_line(exc: Exception) -> str:
    """A compiler's complaint, as much of it as a status line can hold."""
    text = str(exc).strip()
    return text.splitlines()[0] if text else type(exc).__name__


def _export_clap(text: str, want, bench):
    """`gestate.export`'s own door, so the plugin is the documented one.

    **`gui` stays off, as the CLI has it.**  `export.py` argues that
    default rather than picking it — without the window the shell has no
    dependencies at all, which is the property `shell/README.md` is built
    around — and a command that quietly disagreed with the flag's own
    documentation would be the drift this whole list exists to prevent.
    """
    from .export import export_clap

    return export_clap(text, want, name=want.stem, gui=False)


def _trim_wav(path, start: float) -> None:
    """Take the first `start` seconds off a `.wav`, in place.

    **Which is why the render began at the top.**  A synth's sound at bar
    five is what its filters and envelopes have been doing since bar one;
    rendering from bar five would give a different piece that happens to
    share a score.  So the piece is played and the front is cut, which is
    what a bounce does everywhere else.
    """
    import wave

    with wave.open(str(path), "rb") as w:
        params = w.getparams()
        frames = w.readframes(w.getnframes())
    drop = int(start * params.framerate) * params.sampwidth * params.nchannels
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(frames[drop:])


def _export_wav(text: str, want, span=None):
    """`gestate.audioperform`'s, for the same reason.

    **The CLI, not a private path.**  What the command writes is what
    `python -m gestate.audioperform file -o out.wav` writes, because a
    second renderer here would be a second answer to *what does this
    file sound like* — and the two would disagree the first time either
    grew a flag.
    """
    import contextlib
    import io
    import tempfile

    from .audioperform import main as perform_main

    with tempfile.NamedTemporaryFile("w", suffix=".ges", delete=False) as f:
        f.write(text)
        source = f.name
    # **No `--seconds` unless a span asked for one.**  `audioperform`
    # works the length out of the score itself, and passing a number over
    # the top of that made every render the same arbitrary length —
    # a thirty-second piece cut to eight, and a synth with no piece given
    # eight seconds of tone that meant nothing.  A bar range is the one
    # case where the caller genuinely knows better, because it *said*.
    at, to = span if span else (0.0, None)
    argv = [source, "-o", str(want)]
    if to is not None:
        argv += ["--seconds", str(to)]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = perform_main(argv)
    finally:
        Path(source).unlink(missing_ok=True)
    if code:
        raise RuntimeError(f"the render refused (exit {code})")
    if at > 0:
        _trim_wav(want, at)
    return want


#: The reference index, read once.  493 entries parsed out of five
#: libraries is not a thing to redo per keystroke, and it cannot change
#: while the process runs — the libraries ship with it.
_REFERENCE_ALL: list = []


def _builtin_types() -> list:
    """Type constructors the compiler knows and no library declares.

    **Read from `kindcheck`'s own table**, so a type the compiler learns
    is a type this offers — a list written out here would be a second
    place the language's vocabulary lived, which is the thing every other
    list in this file is derived to avoid.

    The internal spellings are left out: `Tuple2` is what a pair is
    called inside the checker and `(a, b)` is what anybody writes, so
    offering the first would be teaching the wrong name for a thing the
    reader already has one for.
    """
    try:
        from .kindcheck import _BUILTIN_KINDS
    except Exception:                                    # noqa: BLE001
        return []
    return sorted(n for n in _BUILTIN_KINDS if not n.startswith("Tuple"))


#: A token kind as a colour class.  **Six, not twelve**: what a reader
#: needs from colour is *which sort of thing is this*, and a palette with
#: a shade per token kind is a palette nobody can hold in their head.
#: `SEP` and `SYMBOL` share one because a bracket and an operator are
#: both punctuation to the eye.
_PAINT = {
    "COMMENT": "note", "STRING": "text", "NUMBER": "num",
    "CONID": "con", "RESERVED": "word", "WORD": "",
    "SYMBOL": "op", "SEP": "op",
}

#: Per-line colouring, keyed by the line's own text.
#:
#: **Which is exactly right because colouring here is line-local.**
#: Tokenising `lantern.ges` whole and line by line gives the same 996
#: tokens: the only cross-line state is `INDENT`/`DEDENT`, and layout
#: carries no colour.  So a line that has not changed cannot have
#: changed colour, and an edit costs one line's tokens — 37µs — rather
#: than a screen's.
_PAINTED: dict = {}


def painted(line: str) -> str:
    """`col:len:class` for each coloured run in one line, space separated.

    **The real tokenizer, and only ever the real one.**  A second lexer
    in the window would be fast and would be a second front end that
    could disagree with the compiler — the root cause `spec/comments.md`
    is written about.  This is the same `tokenize` the parser reads, so
    a colour is the compiler's own opinion or it is not shown.

    The lexer is total, which is what makes this safe on a file that
    does not compile: `sound = ((` and an unterminated string both
    tokenize.  Anything it cannot make sense of simply gets no run and
    is drawn in the ordinary ink.
    """
    if line in _PAINTED:
        return _PAINTED[line]
    from .syntax.tokenize import tokenize

    runs = []
    try:
        for token in tokenize(line):
            paint = _PAINT.get(token.kind.name)
            if not paint:
                continue
            at = token.span.start.col
            width = max(0, token.span.end.col - at)
            if width:
                runs.append(f"{at}:{width}:{paint}")
    except Exception:                                    # noqa: BLE001
        # A lexer that has surprised us is not worth a broken window:
        # no runs is a line in ordinary ink, which is what it was doing
        # before any of this.
        runs = []
    out = " ".join(runs)
    if len(_PAINTED) > 4000:
        # Long editing sessions leave a line behind per keystroke; the
        # cache is a speed-up, not a record.
        _PAINTED.clear()
    _PAINTED[line] = out
    return out


def _builtin_kind(name: str) -> str | None:
    """`Type`, or `(Type -> Type)`, for a type the compiler knows."""
    try:
        from .kindcheck import _BUILTIN_KINDS
    except Exception:                                    # noqa: BLE001
        return None
    found = _BUILTIN_KINDS.get(name)
    return None if found is None else repr(found)


def _all_reference() -> list:
    global _REFERENCE_ALL
    if not _REFERENCE_ALL:
        try:
            from .reference import all_entries

            _REFERENCE_ALL = list(all_entries())
        except Exception:                                # noqa: BLE001
            _REFERENCE_ALL = []
    return _REFERENCE_ALL


def _declared_names(source: str) -> set:
    """Every name the text defines — the same reading `goto` uses."""
    from .typecheck import _defined_lines

    return set(_defined_lines(source))


def _formatted(source: str) -> str:
    """`source`, laid out — the same answer `python -m gestate.fmt` gives.

    One door, so the editor and the command line cannot disagree about
    what laid out means.
    """
    from .fmt.format import format_source

    return format_source(source)


#: What a declaration is made of, for the purpose of laying one out: a
#: signature and its equation are two items and one declaration, and
#: formatting one without the other would split a pair the reader thinks
#: of as one thing.
def _declaration_spans(module) -> list:
    """`(name, first_line, last_line)` per declaration, 1-based inclusive.

    Items that share a name and stand together — `f : Int` above
    `f x = …` — are one entry, because that is what a person means by
    "this declaration" and what `fmt` therefore has to take whole.
    """
    from .syntax.ast import VComment

    out = []
    for item in getattr(module, "items", []):
        if isinstance(item, VComment):
            continue
        span = getattr(item, "span", None)
        if span is None:
            continue
        first, last = span.start.line + 1, span.end.line + 1
        name = getattr(item, "name", None)
        if out and name is not None and out[-1][0] == name \
                and first <= out[-1][2] + 1:
            out[-1] = (name, out[-1][1], max(out[-1][2], last))
        else:
            out.append((name, first, last))
    return out


def _formatted_range(source: str, first: int, last: int) -> tuple:
    """`(whole source with those lines laid out, from, to)`, 1-based.

    **The whole file is parsed and only part of it is reprinted.**
    Parsing just the chosen lines would lose the context a fragment
    needs — and the trivia, which `spec/comments.md` keeps on the module
    rather than on the item.  So the parse is entire, the *reprint* is
    the part asked for, and everything outside the widened span is the
    author's own bytes, untouched.

    `(…, 0, 0)` when no declaration is in range, which the caller reports
    rather than treating as a formatting that did nothing.
    """
    from .syntax import parse
    from .syntax.ast import VModule

    module = parse(source)
    touched = [d for d in _declaration_spans(module)
               if d[1] <= last and d[2] >= first]
    if not touched:
        return source, 0, 0
    at, to = min(d[1] for d in touched), max(d[2] for d in touched)

    from .syntax.ast import VComment

    keep, comments = [], []
    for item in getattr(module, "items", []):
        span = getattr(item, "span", None)
        if span is None or not (at <= span.start.line + 1 <= to):
            continue
        (comments if isinstance(item, VComment) else keep).append(item)
    if not keep:
        return source, 0, 0
    # The trivia inside the widened span travels with it, so a trailing
    # comment on a formatted equation is reattached rather than dropped.
    inner = [c for c in getattr(module, "comments", [])
             if getattr(c, "span", None) is not None
             and at <= c.span.start.line + 1 <= to]
    piece = _formatted_module(VModule(items=comments + keep,
                                      comments=inner))
    lines = source.splitlines()
    out = lines[:at - 1] + piece.rstrip("\n").splitlines() + lines[to:]
    return "\n".join(out) + ("\n" if source.endswith("\n") else ""), at, to


def _formatted_module(module) -> str:
    from .fmt.format import format_module

    return format_module(module)


def _summaries(source: str) -> dict:
    """`name -> first sentence of its `#:` comment`.

    The palette has one line; a doc comment has as many as it needs.
    Taking the first sentence is what makes the two agree without asking
    an author to write the summary twice.
    """
    out, held = {}, []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#:"):
            held.append(stripped[2:].strip())
            continue
        if stripped and not stripped.startswith("#") and ":" in stripped:
            name = stripped.split(":", 1)[0].strip()
            if name.isidentifier() and held:
                text = " ".join(t for t in held if t)
                out.setdefault(name, _plain(_first_sentence(text)))
        if not stripped.startswith("#:"):
            held = []
    return out


def _plain(text: str) -> str:
    """A doc comment's emphasis, taken off.

    `spec/comments.md` makes doc comments markdown-ish, and a palette
    row is not markdown — `**while it plays**` in a list of commands is
    noise wearing the costume of emphasis.  Done here, where the
    comment is read and where what a palette shows is decided, rather
    than in the view: it is a fact about the *summary*, and the view
    should not have to know the model writes markdown.
    """
    return text.replace("**", "").replace("`", "")


def _first_sentence(text: str) -> str:
    """Up to the first full stop that ends a sentence.

    Naive on purpose: an abbreviation would fool it, and the fix for
    that is to write the summary as a sentence, which every doc comment
    in this project already does.
    """
    for i, ch in enumerate(text):
        if ch == "." and (i + 1 >= len(text) or text[i + 1] == " "):
            return text[: i + 1]
    return text


#: Which command undoes the direction of which.
#:
#: **Beside the handlers, because it is a fact about what they do**, and
#: sent out with the description so the window never has to know it.  A
#: view that decided `find` runs backwards as `findBack` would be a
#: second vocabulary, and the list exists to prevent exactly that: it is
#: handed the pairing the same way it is handed the key and the argument
#: types.  A test holds that both sides of every pair are real commands.
REVERSE = {
    "find": "findBack",
    "findBack": "find",
}


#: The shortcuts.  **Every one names a command**, and a test holds that
#: — a key that did something the list did not offer would be a second
#: vocabulary, which is the thing the list exists to prevent.
#:
#: **And every one takes Control**, which a test also holds.  There is
#: one mode and you are typing in it, so a bare key is text: `play` was
#: advertised as `Space` for a while, inherited from a window where the
#: piano had the focus, and in an editor that is either a shortcut that
#: never fires or an editor you cannot type a space into.
KEYS = {
    "apply": "Ctrl-S",
    "audition": "Ctrl-Return",
    "play": "Ctrl-Space",
    "undo": "Ctrl-Z",
    "redo": "Ctrl-Y",
    "find": "Ctrl-F",
    # **A letter, deliberately.**  The symbol table exists because a
    # layout hides punctuation, so reaching it through punctuation would
    # be the joke telling itself — `Ctrl-;` is shift-comma on the very
    # keyboard this is for.
    "symbol": "Ctrl-E",
    # **The one bare key**, and the rule it bends is stated in
    # `window.rs`: every other shortcut takes Control, because a bare key
    # is text and an editor that stole one would be an editor you cannot
    # type in.  `Tab` is the exception the language earns — the layout
    # rule counts columns, a tab's width is the *renderer's* choice, so a
    # tab-indented file means something other than it looks, and no
    # `.ges` in the tree contains one.  It is what `audiopygame` pressed
    # at a hole, and asking what fits is what it is for everywhere else.
    "fits": "Tab",
    "copy": "Ctrl-C",
    "cut": "Ctrl-X",
    "paste": "Ctrl-V",
    "canvas": "Ctrl-Tab",
    "source": "Ctrl-Tab",
    "zoomIn": "Ctrl-+",
    "zoomOut": "Ctrl--",
    "quit": "Ctrl-Q",
}


class Detached:
    """The view, when there is not one.

    **A refusal that reads**, rather than an attribute error: half the
    commands are about the window — undo, find, zoom — and a headless
    session must be able to run the whole list and be told which ones
    it cannot do.  That is what makes acceptance 2's test a list of
    names in and a list of sentences out, including the ones that say
    no.
    """

    def text(self) -> str:
        return ""

    def undo(self) -> bool:
        return False

    def redo(self) -> bool:
        return False

    def find(self, _pattern: str, back: bool = False) -> int:
        return -1

    def goto(self, _line: int) -> bool:
        return False

    def zoom(self, _by: int) -> bool:
        return False

    def show(self, _what: str) -> bool:
        return False

    def close(self) -> None:
        pass

    def insert(self, _text: str) -> bool:
        return False

    def replace(self, _text: str) -> bool:
        return False

    def close_list(self) -> bool:
        return False

    def open(self, _path: str) -> bool:
        return False

    def copy(self) -> None:
        pass

    def cut(self) -> None:
        pass

    def paste(self) -> None:
        pass

    def caret(self) -> int:
        return 0

    def fill(self, _text: str) -> bool:
        return False


@dataclass
class Session:
    """A workbench, a view, and the commands that move them."""

    bench: object
    #: Where the text and the window live.  **Not this layer's**, and
    #: that is the point: `spec/editor.md` requires undo to be *text*
    #: undo, so the thing holding the text is the thing that owns it.
    view: object = field(default_factory=Detached)
    #: What was said, newest last — the status line's history and what a
    #: test asserts on.
    said: list = field(default_factory=list)
    #: What a played note does: `"off"`, `"on"` or `"step"`.
    #:
    #: **Off to begin with.**  A file is opened to be read at least as
    #: often as to be played, and three rows of keys taken from the
    #: document before anybody asked for them is a window that has
    #: decided what you are here for.
    performing: str = "off"
    #: What `what` last found, as lines to show — or `None`.
    #:
    #: **A box rather than the status line.**  One sentence is the right
    #: size for *what just happened*; a signature, where it comes from
    #: and what it is for is a paragraph, and squeezing it into the foot
    #: of the window is the same as hiding it.
    page: object = None
    #: Which argument the window is asking about — `(verb, index,
    #: query)` — or `None` when it is not asking.
    asking: object = None
    #: What `filter` last produced, or `None` when nothing is being
    #: filtered.  **`None` and `[]` are different**: no filter shows
    #: everything, a filter that matched nothing shows nothing.
    filtered: object = None
    #: An export waiting on a yes — `(kind, target)`, or `None`.
    confirming: object = None
    #: The `(verb, argument)` a name or a type has already been filled
    #: into.  **Once per question, never per empty box** — see
    #: `proposed_name`.
    proposed: object = None
    #: `(question, answer)` — what `choices` last worked out, so a poll
    #: that changed nothing costs a comparison instead of a ranking.
    _answered: object = None
    #: `(when, token)` — the last look at the world outside the program,
    #: and when it was taken.  See `_outside`.
    _looked: object = None
    #: The dialog in progress — `(verb, at, kind, query, looks)` — or
    #: `None`.  Flushed into the log as one `ask` step when the command
    #: it was collecting for runs.  See `_asked_about`.
    _episode: object = None
    #: Every transition this session has made — see `_record`.
    log: object = None
    #: A template pasted and not yet kept — the name, or `None`.
    #: Return keeps it, `Esc` undoes it, and running anything else
    #: settles it, because by then you have moved on.
    inserted: object = None

    def commands(self) -> list:
        """The palette.  Derived from `command.ges` every time it is
        asked for, which is cheap and cannot go stale."""
        return vocabulary()

    #: Which commands want which names.  **Not every `Named` is the
    #: same question**: `set cutoff` only means anything for a knob and
    #: `listen` only for a bank, while `what` is the compiler answering
    #: about *anything* — offering a bank to `set` is offering a choice
    #: that cannot work, which is a list telling you a lie.
    WANTS = {"set": "knobs", "learn": "knobs",
             "listen": "banks", "deafen": "banks",
             "goto": "written", "infer": "written",
             "what": "everything"}

    def names(self, wants: str = "controls") -> list:
        """Every name a `Named` argument could be, and what it is.

        **Grouped, and the group is the note.**  What is in the window
        comes first — knobs, banks, then whatever else the file declares
        — and the libraries follow, tagged by which one they are in.
        That order is the answer to *what did I call it*, which is the
        question somebody has when they open this list; the alphabet
        would answer a question nobody asked.
        """
        if wants == "everything":
            return self._everything()
        if wants == "written":
            return self._declarations()
        out, seen = [], set()
        kinds = getattr(self.bench, "knob_types", {}) or {}
        if wants in ("controls", "knobs"):
            for site in getattr(self.bench, "sites", []) or []:
                name = getattr(site, "name", None)
                if name is None or name in seen:
                    continue
                seen.add(name)
                out.append((name, f"Chan {kinds.get(name, 'Int')}", ""))
        if wants in ("controls", "banks"):
            for bank in getattr(self.bench, "banks", []) or []:
                name = _of(bank, "name", "")
                if not name or name in seen:
                    continue
                seen.add(name)
                out.append((name, f"{_of(bank, 'count', 0)} voices", ""))
        return out

    def _declarations(self) -> list:
        """What the file itself declares — knobs, banks, and the rest.

        The knobs and banks come first because they are what the window
        is already drawing; everything else the text defines follows, so
        `goto` can reach a helper that has no widget.
        """
        out = list(self.names("controls"))
        seen = {row[0] for row in out}
        for name in _declared_names(self._source()):
            if name not in seen:
                seen.add(name)
                out.append((name, "declared here", ""))
        return out

    def _everything(self) -> list:
        """Every name there is — this file's, then every library's.

        **What `what` is for.**  It already answers out of the reference
        when a name is not in the file — `what wait` reaches the
        language's own documentation — so a completion that offered only
        the file's names was offering less than the command could do.
        Asking a machine that is playing music what a word means, being
        told nothing, and finding it in the manual it ships with is the
        sort of answer that teaches somebody the tool does not know
        things.
        """
        out = self._declarations()
        seen = {row[0] for row in out}
        # **The builtin types, which are in no `.ges` file.**  `Int` and
        # `Bool` are the compiler's own, so the reference — which is
        # generated from the libraries' prose — has never heard of them,
        # and a completion over "everything" that could not offer `Int`
        # was offering everything except the words a beginner reaches
        # for first.  Read from the kind table rather than listed here,
        # so a type the compiler learns is a type this offers.
        for name in _builtin_types():
            if name not in seen:
                seen.add(name)
                out.append((name, "built in", "type"))
        for entry in _all_reference():
            if entry.name in seen:
                continue
            # **Not offered, still answered.**  A name a program cannot
            # say — `constSig`, or anything below a library's `internal`
            # marker — must not be proposed by a completion, which would
            # be the list teaching a word the compiler then refuses.
            # `what constSig` typed in full still answers, because "what
            # is this thing my editor just showed me" is a fair question
            # about machinery too (`_reference` keeps every entry).
            if getattr(entry, "internal", False):
                continue
            seen.add(entry.name)
            # **The kind travels with the name.**  A type is a different
            # sort of answer from a function — you reach for one to say
            # what something *is* and the other to say what it *does* —
            # and a list that spelled them the same made the reader open
            # each to find out which they had.
            out.append((entry.name, getattr(entry, "library", "") or "library",
                        entry.kind))
        return out

    def naming(self, query: str, wants: str = "controls") -> list:
        """The names a typed query means, best first.

        **The same rule as `matching`, over names instead of commands**,
        and here for the same reason: which of several things a person
        meant is a decision, and a decision belongs in one place.
        """
        query = query.strip().lower()
        found = []
        for i, (name, note, kind) in enumerate(self.names(wants)):
            low = name.lower()
            if not query:
                rank = 3
            elif low == query:
                rank = 0
            elif low.startswith(query):
                rank = 1
            elif query in low:
                rank = 2
            else:
                continue
            found.append((rank, i, (name, note, kind)))
        return [row for _r, _i, row in sorted(found, key=lambda f: f[:2])]

    def symbols(self, query: str) -> list:
        """The symbol table — `(letter, symbol)` per cell.

        **The letter is what is sent**, so typing one picks that cell and
        the ordinary filter machinery does the whole job.  The symbol
        rides along as the note, which is what the grid draws large.

        The symbol itself also matches, because somebody who knows they
        want a backtick will type one sooner than count to `i` — and a
        picker you have to read every time is one you stop opening.
        """
        want = query.strip().lower()
        cells = [(_letter(i), g, n) for i, (g, n) in enumerate(SYMBOLS)]
        if not want:
            return [(l, g) for l, g, _n in cells]
        # **A letter names one cell and nothing else.**  Matching names
        # as well as letters made `a` — the first cell — also match
        # `backslash`, `bar` and half the table, so the one keystroke
        # the grid exists to make sufficient was not.
        # **A label is a prefix, so a query narrows rather than picks.**
        # `a` is also the start of `aa`, and returning only the exact
        # match put every cell past `z` out of reach by name — so the
        # rest of the row is kept and the exact one is put first, where
        # the cursor already is.  One keystroke and Return still lands on
        # `a`; one more letter reaches `aa`.
        by_label = [(l, g) for l, g, _n in cells if l.startswith(want)]
        if by_label:
            by_label.sort(key=lambda c: (len(c[0]) > len(want), c[0]))
            return by_label
        return [(l, g) for l, g, n in cells
                if g.startswith(query.strip()) or want in n]

    def devices(self, query: str) -> list:
        """The MIDI inputs a typed query means, and which is listening.

        **The note is the answer to "is it on".**  Choosing a device and
        seeing which one is live are the same act here, because they are
        the same question asked half a second apart — and a window that
        could only tell you *afterwards* is how an evening goes into
        deciding whether the keyboard is broken.

        A machine with no MIDI gets an empty list rather than a row
        saying so: the palette shows what could be chosen, and there is
        nothing.  `midiOn` is the one that says why.
        """
        live = getattr(self.bench, "midi_port", None)
        query = query.strip().lower()
        out = []
        for name in getattr(self.bench, "midi_ports", lambda: [])():
            if query and query not in name.lower():
                continue
            out.append((name, "listening" if name == live else "idle"))
        return out

    def snippets(self, query: str) -> list:
        """The templates a typed query means, best first.

        The same rule as `matching` and `naming`, and here for the same
        reason — which of several things somebody meant is a decision,
        and a decision belongs in one place.  The *summary* is searched
        too, because a person reaching for a template is more likely to
        remember what it does than what it is called.
        """
        query = query.strip().lower()
        found = []
        for i, snip in enumerate(templates()):
            low = snip.name.lower()
            if not query:
                rank = 3
            elif low == query:
                rank = 0
            elif low.startswith(query):
                rank = 1
            elif query in low:
                rank = 2
            elif query in snip.summary.lower():
                rank = 4
            else:
                continue
            found.append((rank, i, (snip.name, snip.summary)))
        return [pair for _r, _i, pair in sorted(found, key=lambda f: f[:2])]

    def _where(self, path: str, verb: str | None = None):
        """The file a chosen path names, from wherever the list had got to.

        **Relative to the query, not to the file you started in.**  The
        list walks: after `../audio/` a row says `two.ges` and means the
        one *there*.  Resolving against the open file's directory would
        find a different `two.ges`, or none — a walk that lied about
        where it had arrived.

        `verb` is whose question may lend its walk: a question stands
        until the list closes (F123), so a command must not inherit a
        walk that some *other* command's finished question left behind.
        """
        from pathlib import Path as _Path

        here = _Path(getattr(self.bench, "path", ".")).resolve().parent
        walked = ""
        if (self.asking and len(self.asking) > 2
                and (verb is None or str(self.asking[0]) == verb)):
            # **A picked row is bare; a typed query is whole.**  The
            # rows of a listing carry names relative to the walk, so
            # the walk is prepended — but an answer that *is* the query
            # (typed, accepted with no row) already carries its own
            # path, and prepending walked it twice:
            # `transcript ../../x.ges` from `examples/audio/` resolved
            # to `/home/x.ges` and died on permissions (F122).
            q = str(self.asking[2])
            if path != q:
                walked = q.rpartition("/")[0]
        return (here / walked / path).resolve()

    def _listing(self, query: str, free: bool = False,
                 mark: bool = False) -> list:
        """What is in the directory the query points at, best first.

        **Directories first, then files, and `..` above both.**  Going
        up is the move you make when you opened the wrong place, so it
        is where the eye already is; and a directory is a step rather
        than a destination, which is why its row says so.

        The query is a *path*, not a filter: everything up to the last
        separator says where to look, and only the last piece narrows
        what is shown. That is what makes typing `exa/au` walk two
        directories the way a shell does.
        """
        here = self._here()
        # **Split the text, not the path.**  `Path("../").parent` is
        # `.` — a path object normalises away the trailing separator and
        # then answers about the wrong directory, so `../` listed where
        # you already were and the walk could not leave. Everything up
        # to the last separator says *where*, and only what follows it
        # narrows what is shown.  `_directory` is that rule, and the
        # freshness token keys on it so the two cannot watch different
        # folders.
        head, _sep, stem = query.rpartition("/")
        where = self._directory(query)
        try:
            entries = sorted(where.iterdir(), key=lambda e: e.name.lower())
        except Exception:                                # noqa: BLE001
            return []
        out = []
        low = stem.lower()
        # **`..` is filtered like anything else.**  Always putting it
        # first meant that typing a name left it still at the top and
        # still selected, so Enter stepped *out* of the directory you
        # were narrowing — the query said one thing and the cursor did
        # another.
        # **`..` is a path, not a word.**  Choosing it has to leave a
        # query you could have typed — `../`, then `../../` — because
        # the query is what the next listing is read from, and a row
        # that put an absolute path there would end the walk you were
        # in the middle of.
        if where.parent != where and (not low or "..".startswith(low)):
            import os

            up = os.path.relpath(where.parent, here)
            # Five wide like every other row: a listing whose shape
            # depended on which row it was would make every reader of it
            # carry the exception.
            #
            # **The note says where you are, not where up goes.**  It
            # used to show the parent's absolute path, and Henri read
            # it as where his file would land — a destination, when the
            # row means a step.  The one absolute path worth printing
            # in a walk is the place you are standing (his design:
            # "you are here").
            out.append(("../", f"you are here: {where}", True,
                        up + "/", False))
        matched = []
        for entry in entries:
            if entry.name.startswith(".") and not stem.startswith("."):
                continue
            if low and low not in entry.name.lower():
                continue
            matched.append(entry)
        # **An exact name outranks a fuzzy one** (F129: `test` offered
        # `pytest.ini` above the `test/` that *is* the query).  The
        # palette's own law — a name match beats a prose match — one
        # floor down: exactness first, a prefix next, a substring
        # last; directories before files at each rank, because a
        # directory named what was typed is almost certainly where the
        # person is going; the alphabet inside.
        if low:
            matched.sort(key=lambda e: (
                0 if e.name.lower() == low else
                1 if e.name.lower().startswith(low) else 2,
                e.is_file(), e.name.lower()))
        for entry in matched:
            # **A name already taken is shown and not offered.**  You
            # cannot choose what you cannot have, and hiding it would
            # be worse: the reason the name is refused is that it is
            # there, so it has to be visible for the refusal to read.
            # **Two questions, not one.**  `free` refuses a name that
            # is taken; `mark` only *shows* that it is.  They rode on one
            # flag while `steal` was the only caller, because a name it
            # refused was also the one it greyed — and then an export
            # arrived, which overwrites and still wants you to see that
            # you are about to.  Seeing and being refused are different
            # facts and now say so separately.
            taken = free and entry.is_file()
            dim = (free or mark) and entry.is_file()
            # **A directory is a step, not an answer.**  Choosing one
            # moves the query into it and asks again — which is what a
            # file dialog does and what makes walking down and back up
            # feel like walking. Choosing a *file* is the answer.
            step = (head + "/" if head else "") + entry.name + "/" \
                if entry.is_dir() else ""
            out.append((entry.name + ("/" if entry.is_dir() else ""),
                        "taken" if taken else
                        "there" if dim else
                        "directory" if entry.is_dir() else _size(entry),
                        not taken, step, dim))
        # **A file you can name is a file the dialog can find** (F130).
        # A query that matches nothing here is offered matches from
        # below, nearest first — `open lantern.ges` from the root used
        # to answer 0 rows three times while starting phantoms, because
        # the listing was one directory deep and lantern lives two.
        # Deep rows wear their path from the walk, so what is picked is
        # exactly what is shown, and `_where` resolves it like any
        # bare row.
        if low and not out:
            out.extend(self._below(where, head, low, free, mark))
        return out

    #: What a deep search may touch: directories this far down, this
    #: many directory reads, this many rows.  Bounds rather than
    #: tuning — a dialog is read at a keystroke's pace whatever the
    #: tree looks like.
    BELOW_DEEP, BELOW_READS, BELOW_ROWS = 4, 64, 40

    def _below(self, where, head: str, low: str,
               free: bool, mark: bool) -> list:
        """Matches under the walk, nearest first — F130's finding half.

        Breadth-first, so a shallow answer beats a deep one; what a
        build writes (`target`, `__pycache__`) is not descended,
        because a file a person can *name* is one they put somewhere;
        and bounded in depth, reads and rows, because an unbounded
        walk is a dialog that sometimes hangs.
        """
        junk = {"target", "__pycache__", "node_modules"}
        found = []
        frontier = [(where, "")]
        reads = 0
        while (frontier and reads < self.BELOW_READS
               and len(found) < self.BELOW_ROWS):
            below, rel = frontier.pop(0)
            reads += 1
            try:
                entries = sorted(below.iterdir(),
                                 key=lambda e: e.name.lower())
            except Exception:                            # noqa: BLE001
                continue
            for entry in entries:
                if entry.name.startswith(".") or entry.name in junk:
                    continue
                wearing = rel + entry.name
                if entry.is_dir():
                    if (not entry.is_symlink()
                            and wearing.count("/") < self.BELOW_DEEP):
                        frontier.append((entry, wearing + "/"))
                    if low in entry.name.lower():
                        found.append((wearing + "/", "directory", True,
                                      (head + "/" if head else "")
                                      + wearing + "/", False))
                elif low in entry.name.lower():
                    taken = free
                    dim = free or mark
                    found.append((wearing,
                                  "taken" if taken else
                                  "there" if dim else _size(entry),
                                  not taken, "", dim))

        # Nearest first, then the exactness rank the flat listing
        # keeps, directories before files, the alphabet inside.
        def rank(row):
            text = row[0].rstrip("/")
            name = text.rpartition("/")[2].lower()
            return (text.count("/"),
                    0 if name == low else
                    1 if name.startswith(low) else 2,
                    0 if row[3] else 1, text.lower())

        found.sort(key=rank)
        return found[:self.BELOW_ROWS]

    def choices(self) -> list:
        """What the argument being asked for could be, or nothing.

        **Answered once per question, not once per poll.**  `furniture`
        is derived every time the loop comes round — every two
        milliseconds — and it reads this; ranking `what`'s five hundred
        names there would spend most of a poll on an answer that had not
        changed since the last one.  The question is the key, so a
        keystroke recomputes and a redraw does not.
        """
        if self.asking is None:
            return []
        question = (self.asking, self._outside())
        if self._answered is not None and self._answered[0] == question:
            return self._answered[1]
        found = self._choices()
        self._answered = (question, found)
        self._note_look()
        return found

    def _note_look(self) -> None:
        """Count one working-out of the list, for the transcript.

        **Here and not in the `wants` gesture**, because this is the one
        place that sees every question actually answered — the window
        asks, the model re-asks itself when a directory is stepped into,
        and the world changing re-lists under an untouched query.  All
        three are looks, and a count taken at the wire would miss two of
        them.

        A new verb starts a new dialog: the arguments of one command are
        one episode, however many boxes it takes to fill them.
        """
        verb, at, query = self.asking
        kind = self._asking_kind()
        looks = self._episode[4] + 1 \
            if self._episode is not None and self._episode[0] == verb else 1
        self._episode = (verb, at, kind, query, looks)

    #: How often a question may look outside the program again.
    #:
    #: The poll is 2ms after a keystroke and backs off to 10ms
    #: (`workbench.pace`), and neither a directory nor a MIDI socket is
    #: worth asking about a hundred times a second.  A fifth of a second
    #: is under the threshold at which a list appearing reads as a
    #: consequence of what you did rather than as the program noticing
    #: later, and it bounds the cost on a network mount, where the stat
    #: below is a round trip rather than a dentry lookup.
    OUTSIDE_EVERY = 0.2

    #: How old a directory's stamp must be before it is believed.
    #:
    #: The kernel stamps files on its **coarse clock** — a tick of one
    #: to twenty milliseconds, measured (F124's specimen: 801 writes,
    #: 37 distinct directory mtimes) — so a write landing in the same
    #: granule as the directory's last change leaves the mtime exactly
    #: where it stood, and a cache keyed on it serves the old listing
    #: for ever.  That was F124 whole: not load, not a margin — the
    #: test's setup and its arriving file fit inside one granule when
    #: the suite ran warm, and load *stretched* the granules, which is
    #: why the flakes arrived with parallel compiles.  While a stamp is
    #: younger than this, the mtime is treated as unsettled and the
    #: listing is re-read once per `OUTSIDE_EVERY`; make, git and ninja
    #: all keep a version of this rule — theirs is called "racily
    #: clean".
    MTIME_SETTLES = 0.05

    def _outside(self) -> object:
        """What the answer depends on that is **not** the question.

        `choices` used to key on the question alone, and the docstring
        above says why that is nearly right: a keystroke recomputes and
        a redraw does not.  What it missed is that two of the answers
        are not about the program at all.  A `Path` question lists a
        directory and a `Device` question enumerates MIDI inputs, and
        either can change while the query sits untouched — so the
        dialog stayed open showing a file that was no longer the whole
        story, which is the bug a first user found.

        **A directory says when it last changed and a socket does
        not.**  So a path is keyed on the directory's own mtime — the
        same trick `vocabulary` plays on `command.ges`, one `stat`
        instead of a walk, and no re-listing at all until something
        really moved.  Devices have nothing to ask, so they are keyed
        on the clock and re-enumerated a few times a second.

        Everything else — `what`'s five hundred names, the templates,
        the symbols — is a fact about the program in the window, which
        cannot change without a keystroke.  Those keep the old
        behaviour exactly: `None`, and the question alone is the key.

        Note what mtime does *not* answer: a file that is rewritten in
        place keeps its directory's timestamp, so the size in a row can
        lag.  Adding, removing and renaming — which is what a dialog is
        watching for — all bump it.  And a filesystem with a coarse
        clock (FAT's two seconds) or a client that caches attributes
        (NFS, SMB) can still hold a listing back; there is no fixing
        that from here, and it is worth knowing rather than hiding.
        """
        import time

        kind = self._asking_kind()
        if kind not in ("Path", "Device"):
            return None
        now = time.monotonic()
        # **Throttled, and the throttle is the point.**  Between looks
        # the last token is handed back unchanged, so the cached answer
        # stands and the poll costs a comparison, exactly as before.
        if self._looked is not None and now - self._looked[0] < self.OUTSIDE_EVERY:
            return self._looked[1]
        if kind == "Device":
            # Nothing to ask, so the clock is the token: a new one every
            # `OUTSIDE_EVERY`, which re-enumerates and no oftener.
            token = now
        else:
            try:
                token = self._directory(self.asking[2]).stat().st_mtime_ns
                if time.time_ns() - token < self.MTIME_SETTLES * 1e9:
                    # **A stamp this young is not a fact yet** — see
                    # `MTIME_SETTLES`.  The look itself rides the
                    # token, so the listing keeps being worked out
                    # until the stamp has safely aged.
                    token = (token, now)
            except Exception:                            # noqa: BLE001
                # A directory that cannot be statted is one `_listing`
                # is about to fail on too, and it answers `[]`.  Hold
                # the token steady so a vanished directory does not spin
                # the listing on every poll.
                token = "gone"
        self._looked = (now, token)
        return token

    def _asking_kind(self) -> str:
        """The type of the argument being asked for, or `""`."""
        if self.asking is None:
            return ""
        verb, at, _query = self.asking
        found = self.find(verb)
        if found is None or at >= found.arity:
            return ""
        return found.args[at]

    def _here(self):
        """The directory the file being edited is in.

        Every query in the dialog is relative to this, and three places
        worked it out for themselves before one of them needed to agree
        with another.
        """
        from pathlib import Path as _Path

        return _Path(getattr(self.bench, "path", ".")).resolve().parent

    def _directory(self, query: str):
        """The directory a `Path` query points at — where `_listing` reads.

        **Shared with `_listing`, because there must be one answer.**
        The head of the query says where to look and the last piece
        narrows what is shown; a second copy of that rule would be a
        cache watching a different directory from the one on screen,
        which is a staleness bug wearing the fix's clothes.

        Not to be confused with `_where`, which answers about the *file*
        a chosen row names.  This one is about the folder it sits in.
        """
        here = self._here()
        head, _sep, _stem = query.rpartition("/")
        return (here / head if head else here).resolve()

    def _choices(self) -> list:
        verb, at, query = self.asking
        found = self.find(verb)
        if found is None or at >= found.arity:
            return []
        kind = found.args[at]
        if kind == "Path":
            # `steal` refuses a taken name; an export only shows you that
            # it is taken, and asks before it writes.
            rows = self._listing(query, free=verb == "steal",
                                 mark=verb in self.PROPOSES)
            return self._pinned(verb, at, query, rows)
        if kind == "Template":
            return self.snippets(query)
        if kind == "Symbol":
            return self.symbols(query)
        if kind == "Device":
            return self.devices(query)
        if kind == "Answer":
            # **A question with two rows, and `y`/`n` filter to one of
            # them.**  So it reads as `[y/n]` at the keyboard while
            # staying an ordinary palette question — an inline prompt
            # that captured the keys would be a mode, and this editor
            # has one mode.
            rows = [("yes", "overwrite it"), ("no", "leave it alone")]
            q = query.strip().lower()
            return [r for r in rows if r[0].startswith(q)] if q else rows
        if kind != "Named":
            # **Only names and paths can be offered.**  A number or a
            # piece of text is typed, not chosen; offering a list of
            # numbers would be a menu of guesses. A path has a small,
            # knowable set of next steps — what is in this directory —
            # which is exactly what makes it offerable.
            return []
        return self.naming(query, self.WANTS.get(verb, "controls"))

    def palette_list(self) -> list:
        """What the command list should be showing right now."""
        return self.commands() if self.filtered is None else self.filtered

    def matching(self, query: str) -> list:
        """The commands a typed query means, **best first**.

        Ranked rather than filtered, because somebody typing `loop`
        wants `loop` above a command whose *sentence* happens to mention
        looping: an exact name, then a name that starts with the query,
        then one that contains it, then the summary.  Ties keep the
        order `command.ges` declares them in, which is the order
        somebody thought about them.

        Lifted from `audiopygame`'s reference browser, which is going —
        the browser was one screen of chrome over a generated index, but
        this rule was the part with a decision in it, and a palette
        needs the same one.
        """
        query = query.strip().lower()
        found = []
        for i, verb in enumerate(self.commands()):
            if not query:
                found.append((3, i, verb))
                continue
            name = verb.name.lower()
            if name == query:
                rank = 0
            elif name.startswith(query):
                rank = 1
            elif query in name:
                rank = 2
            elif query in verb.summary.lower():
                rank = 4
            else:
                continue
            found.append((rank, i, verb))
        return [v for _r, _i, v in sorted(found, key=lambda t: (t[0], t[1]))]

    def find(self, name: str):
        """The verb by that name, or `None`."""
        for verb in self.commands():
            if verb.name == name:
                return verb
        return None

    def run(self, name: str, *args) -> str:
        """Do one command and say what happened.

        **A refusal is a sentence, not an exception.**  Everything here
        is reached from a palette a person is typing into, so the wrong
        name and the wrong number of arguments are ordinary events and
        the answer to both is a line they can read.
        """
        verb = self.find(name)
        if verb is None:
            return self._say(f"no command `{name}`")
        if len(args) != verb.arity:
            want = "no arguments" if verb.arity == 0 else str(verb)
            return self._say(f"`{name}` takes {want}")
        handler = getattr(self, f"do_{name}", None)
        if handler is None:
            return self._say(f"`{name}` is declared and not implemented")
        # **Anything else settles a pasted template.**  It is only
        # undoable while it is the thing you are looking at; once you
        # have gone and done something else, an `Esc` three commands
        # later taking back a paste you had forgotten about would be the
        # editor undoing your work behind you.
        if name != "template":
            self.inserted = None
        try:
            args = _typed(verb, args)
        except ValueError as e:
            return self._say(str(e))
        try:
            said = self._say(handler(*args))
        except Exception as e:                            # noqa: BLE001
            # The workbench refusing is a thing to read, not a traceback
            # in somebody's terminal: this layer is between a person and
            # a machine that is playing music.
            said = self._say(f"{name}: {e}")
        # **Recorded after the fact, refusals included.**  What a command
        # answered *is* the transcript — a replay that says something
        # else is the report — and a refusal is as much an answer as a
        # success, often the more interesting one.
        self._record(name, args, said)
        return said

    def _say(self, sentence: str) -> str:
        self.said.append(sentence)
        return sentence

    def _record(self, verb: str, args, said: str) -> None:
        """Keep what was done, in case it turns out to matter.

        **Always on, and in memory.**  A transcript is wanted *after*
        something has gone wrong — by which time offering to start
        recording is offering to reproduce it a second time — and a file
        growing under every keystroke of every session is a thing
        somebody has to clean up rather than one they reach for.
        """
        self._journal()
        # Typing since the last step, before the step it led to — the
        # order a person did them in.
        self.log.typed(self._lines())
        self._asked_about(verb)
        self.log.add(verb, args, said)

    def _journal(self):
        """The log, started on first use."""
        if self.log is None:
            from .sessionlog import Log

            self.log = Log(path=str(getattr(self.bench, "path", "") or ""))
            # **Seeded with the file as opened**, so the first thing
            # recorded is typing and not the program somebody started
            # from.  A transcript that opened by "adding" the whole file
            # would bury the one line that mattered.
            self.log.was = tuple(self._lines())
            # And kept as the text the recording *began* on: the header
            # carries its fingerprint always, and the text itself when
            # the file was not on disk — a session on an unsaved
            # `untitled.ges` used to replay against nothing.
            self.log.base = self.log.was
            self.log.unwritten = not (self.log.path
                                      and Path(self.log.path).exists())
        return self.log

    def note(self, message: str) -> None:
        """Record a sentence the user was shown that no command asked for.

        The other half of what the transcript keeps: `run` records what
        was asked and answered, and this records what the model
        volunteered — a rebuild finishing, a canvas refusing.  Without
        it a session full of error messages replayed as a session where
        nothing happened, which is the difference between a flight
        recorder and one with the cockpit audio erased.
        """
        self._journal().note(message)

    def _asked_about(self, verb: str) -> None:
        """Put the dialog that collected this command into the log.

        **One step for the whole dialog, not one per keystroke.**  A
        `wants` gesture arrives on every character typed into the
        palette, and recorded as they come they would be five steps a
        second — the `KEEP` window is four thousand, so a dialog-heavy
        sitting would push the run-up to the bug off the top of the very
        transcript that exists to hold it.  `Log.typed` already refused
        this bargain for text and the argument is the same one: *a step
        per character would bury the six things somebody actually did
        under four hundred they did not think of as doing anything.*

        So what is kept is the question as it stood when the command
        ran, the digest of what was on offer then, and how many times
        the list was worked out on the way — which is the shape a
        reproduction needs and about fifty bytes.

        **The last question, when a command takes several.**  Every
        `Path` in `command.ges` is its command's last argument, so the
        question worth keeping is the one still standing; an `Int` box
        filled before it offers nothing a digest would say anything
        about.
        """
        episode, self._episode = self._episode, None
        if episode is None or episode[0] != verb or self._answered is None:
            return
        from .sessionlog import ASK, Bare, answer

        _verb, at, kind, query, looks = episode
        # `Bare` for the two that are not text: the command asked about
        # and the type of the box.  `command.ges` writes `open` and
        # `Path` unquoted and so does this.
        self.log.add(ASK, (Bare(verb), at, Bare(kind), query),
                     answer(self._answered[1]))
        # The looks ride as a comment: they are for the person reading
        # the transcript and must stay out of `said`, which is what a
        # replay is diffed on — a replay does no typing, so a count in
        # there would drift on every honest run.
        self.log.steps[-1].shown = (f"{looks} look{'s' if looks != 1 else ''}",)

    def _lines(self) -> list:
        """The document, as lines, however cheaply the view can say.

        `Window.lines` keeps a copy refreshed on `changed()`; a view
        without one is asked for its text, which is what the headless
        sessions and the tests have.
        """
        cheap = getattr(self.view, "lines", None)
        if cheap is not None:
            try:
                return list(cheap())
            except Exception:                            # noqa: BLE001
                pass
        return self._source().splitlines()

    # ── The handlers ─────────────────────────────────────────────────
    #
    # One per verb in `command.ges`, named `do_<verb>`, and a test holds
    # that neither list has an entry the other lacks.  A signature and
    # its implementation are two different things, so a *check* is the
    # right tool here — unlike two copies of the same data, where the
    # right tool is deriving one from the other.

    # -- the instrument ------------------------------------------------

    def do_apply(self) -> str:
        self.bench.apply(self.view.text())
        # **Saved as far as the marker is concerned.**  `apply` writes
        # the file before it starts the rebuild, so the text on disk is
        # this text whether or not the build that follows succeeds — and
        # a `[+]` that stayed up because the program did not compile
        # would be reporting the wrong fact entirely.
        marked = getattr(self.view, "mark_saved", None)
        if marked is not None:
            marked()
        # An inert file has no rebuild coming, so "applying" would
        # promise one; the honest sentence is the act that happened.
        return ("saving" if getattr(self.bench, "inert", False)
                else "applying")

    def do_audition(self) -> str:
        self.bench.audition(self.view.text())
        return "auditioning"

    def do_play(self) -> str:
        # "stopped" for a file that cannot play would be the quiet
        # reading as breakage — the exact thing inert mode is worded
        # against.
        if getattr(self.bench, "inert", False):
            return "nothing plays — the file is inert"
        return "playing" if self.bench.toggle() else "stopped"

    def do_stop(self) -> str:
        self.bench.pause()
        return "stopped"

    def do_seek(self, bar: int) -> str:
        # Bars, beats and samples all count from zero; the conversion
        # between them belongs here, once.
        self.bench.seek_beats(_beats_of(bar))
        return f"at bar {bar}"

    # -- the loop ------------------------------------------------------

    def do_loop(self, first: int, last: int) -> str:
        if last <= first:
            return f"bar {last} is not after bar {first}"
        if first < 0:
            return "bars count from zero"
        self.bench.set_loop(_beats_of(first), _beats_of(last))
        return f"looping bars {first}-{last}"

    def do_loopAll(self) -> str:
        end = self.bench.end_beat()
        if end is None:
            # An unfolding score has no end, so looping "all" of it
            # means nothing.  The workbench says `None` rather than
            # zero, which is the difference between "no answer" and
            # "the answer is nothing".
            return "nothing to loop"
        self.bench.set_loop(0.0, float(end))
        return "looping the whole piece"

    def do_loopOff(self) -> str:
        self.bench.clear_loop()
        return "not looping"

    # -- parameters ----------------------------------------------------

    def do_set(self, name: str, value) -> str:
        # **The clamp survives the type.**  `Named a` stops a `Float`
        # reaching an `Int` knob, which is what it is for; it says
        # nothing about a number being inside the knob's *range*, and
        # 140 is a perfectly good `Int`.
        if not self.bench.has_knob or name not in self.bench.values:
            return f"no parameter `{name}`"
        # **The wire is strings, so the type comes back here.**
        # `Named a` gives an `Int` knob an `Int` where a command is
        # *written*, and the checker holds that — but a gesture crossing
        # the ABI is text, and `70` read as a float shows `cutoff = 70.0`
        # on a knob whose channel carries an integer.  The kind the
        # workbench already knows is what restores it.
        if getattr(self.bench, "knob_types", {}).get(name) == "Int":
            value = int(round(float(value)))
        low, high = self.bench.knob_range(name)
        held = min(high, max(low, value))
        self.bench.set_value(name, held)
        if held != value:
            return f"{name} = {held} (clamped from {value})"
        return f"{name} = {held}"

    def do_learn(self, name: str) -> str:
        if not self.bench.learn(name):
            return f"no parameter `{name}`"
        return f"turn a controller to bind it to {name}"

    # -- notes ---------------------------------------------------------

    def do_listen(self, name: str) -> str:
        return self._listen(name, True)

    def do_deafen(self, name: str) -> str:
        return self._listen(name, False)

    def _listen(self, name: str, on: bool) -> str:
        """Throw the switch, and say what it actually did.

        **`listen` refuses quietly.**  A bank whose payload has no
        `FromMIDI` instance cannot be handed a note however much you
        want it to be — `Workbench.listen` checks that and returns
        without doing anything. This used to report success either way,
        so `listen pad` on a bank that cannot take notes said *"pad
        hears the keyboard"* and then nothing played, which is the worst
        of both: no note, and no reason.
        """
        if not getattr(self.bench, "banks", None):
            return f"no bank `{name}`"
        if name not in {_of(b, "name", "") for b in self.bench.banks}:
            return f"no bank `{name}`"
        self.bench.listen(name, on)
        if _listening(self.bench, name) != on:
            if on and not _takes_notes(self.bench, name):
                return (f"`{name}` cannot be played from a keyboard: "
                        f"its voices take no note")
            return f"`{name}` would not switch"
        if on:
            # **The switch may be thrown on a disconnected bank** — a
            # person wiring MIDI before wiring the mix is composing in
            # an honest order — but the sentence must not promise
            # sound: `lol-session.ges` threw it mid-jog and played keys
            # into silence with the switch proudly on.
            row = next((x for x in getattr(self.bench, "banks", []) or []
                        if _of(x, "name", "") == name), None)
            if row is not None and not _of(row, "wired", True):
                return (f"{name} hears the keyboard — though it is "
                        f"disconnected")
        return f"{name} {'hears' if on else 'ignores'} the keyboard"

    def do_midiOn(self, port: str = "") -> str:
        """Listen to a controller — this one, or the first there is.

        **Three answers, because there are three different facts.**  A
        machine with no MIDI at all, a name that is not one of them, and
        a port that refused to open are not the same thing, and telling
        them apart is what `canvas` had to learn: a fact about the
        machine reported as a fact about your choice sends somebody
        looking in the wrong place.
        """
        ports = getattr(self.bench, "midi_ports", lambda: [])()
        if not ports:
            return "no MIDI input on this machine"
        want = (port or "").strip()
        if want and want not in ports:
            return f"no MIDI input `{want}`"
        opener = getattr(self.bench, "midi_open", None)
        if opener is None:
            return "nothing to listen with"
        if not opener(want or None):
            return f"could not open {want or ports[0]}"
        return f"listening to {self.bench.midi_port or want or ports[0]}"

    def do_midiOff(self) -> str:
        """Stop listening.  The typed keyboard is unaffected."""
        closer = getattr(self.bench, "midi_close", None)
        was = getattr(self.bench, "midi_port", None)
        if closer is None or not closer():
            return "not listening to any controller"
        return f"stopped listening to {was}" if was else "stopped listening"

    def do_octave(self, by: int) -> str:
        where = self.bench.keyboard.transpose(by)
        return f"octave {where}"

    # -- the text ------------------------------------------------------

    def do_undo(self) -> str:
        return "undone" if self.view.undo() else "nothing to undo"

    def do_redo(self) -> str:
        return "redone" if self.view.redo() else "nothing to redo"

    def do_copy(self) -> str:
        """Copy the selection — `Ctrl-C`, as a command the list can
        teach.  The refusals answer from the mirror the way `undo`'s
        do, because "copied" over nothing selected is a sentence that
        lies."""
        if not getattr(self.view, "sel", False):
            return "nothing selected"
        self.view.copy()
        return "copied"

    def do_cut(self) -> str:
        if not getattr(self.view, "sel", False):
            return "nothing selected"
        self.view.cut()
        return "cut"

    def do_paste(self) -> str:
        if not getattr(self.view, "clip", False):
            return "nothing to paste"
        self.view.paste()
        return "pasted"

    def do_open(self, path: str) -> str:
        """Open a file, or step into a directory.

        **A directory is not a refusal.**  Naming one means *look in
        there*, so it answers by re-asking with the query moved along —
        which is what makes typing a path feel like walking one.
        """
        want = self._where(path, "open")
        if want.is_dir():
            # Stay in the question, one step along — and keep the path
            # as it was *given*, so the query reads the way it was typed
            # rather than jumping to an absolute one.
            self.asking = ("open", 0, path.rstrip("/") + "/")
            return f"{want.name or want}/"
        # **Unsaved changes warn, they do not gate** (F113): the moment
        # `open` was picked, the window said so in red beside the query
        # caret and holds the words there for as long as the question is
        # open.  A person who chooses a file past that has decided — the
        # switch proceeds and the edits go, history and all, which is
        # exactly what they were warned about.
        if want.exists():
            # **A file that is not text is refused with a sentence** —
            # it used to be an editor-shaped hole: the switch read the
            # bytes in the gesture loop, the decode raised, and the
            # whole window quit over a `.wav` somebody clicked.
            #
            # **Where the decode fails is the whole test.**  The first
            # cut dropped four bytes off the chunk's end so a split
            # UTF-8 character could not fail an honest file — which
            # only *moves* the boundary, and `duet.ges`'s box-drawing
            # headers put a `─` straddling exactly the moved edge: the
            # editor refused its own flagship example as "not a text
            # file".  A real binary fails in its first bytes; text
            # fails only at the cut, so a failure inside the final
            # three bytes is the chunk's fault and not the file's.
            try:
                chunk = want.open("rb").read(4096)
                chunk.decode()
            except UnicodeDecodeError as e:
                if e.start < len(chunk) - 3:
                    return f"cannot open {want.name}: not a text file"
            except OSError:
                return f"cannot open {want.name}: not a text file"
        if not want.exists():
            # **A started file is text**, so a name wearing one of the
            # binary suffixes this toolchain itself produces is a miss,
            # not a request.  Without this, `open blip.wav` resolved
            # against the wrong directory, missed the real file, and
            # quietly started a fresh STARTER synth *named* `blip.wav`
            # — playing its sine as if the wav had opened (F120's
            # second face).  Only the known-binary suffixes refuse: an
            # advanced editor that would not start `notes.txt` would be
            # refusing somebody's notes over another file's format.
            if want.suffix.lower() in {".wav", ".mid", ".midi",
                                       ".clap", ".png", ".so"}:
                return (f"no file {want.name} — and a new "
                        f"{want.suffix} would not be text")
            # **A name nobody has used is a file being started, not a
            # mistake.**  The workbench has known this shape since the
            # starter text: a `Workbench` on a missing path opens with
            # `STARTER` and the first save creates the file, parent
            # directories included — so refusing here was the one place
            # the editor still treated a new name as an error.  The
            # sentence says which of the two happened, so a typo of an
            # existing name is at least *visible* as a fresh file.
            if not self.view.open(str(want)):
                return "this window cannot open another file yet"
            # **And the list goes away, because opening is finished.**
            # Return on a finished call means *again* — right for
            # `find`, meaningless for `open` — so the table sat over
            # the freshly opened file and caught the first keystrokes
            # somebody aimed at their code.  The same
            # say-when-you-are-done `template` and `symbol` use: the
            # next key you press types into the file you just opened.
            self.view.close_list()
            return f"new file {want.name} — saving creates it"
        if not self.view.open(str(want)):
            return "this window cannot open another file yet"
        self.view.close_list()
        return f"opened {want.name}"

    def do_steal(self, path: str) -> str:
        """Take a free name for what you are writing.

        **Only a free one.**  Overwriting a file is not something a name
        box should be able to do by accident — a `steal` that could
        would be a delete wearing a friendlier word — so an existing
        name is refused here as well as greyed in the list. The two are
        the same rule said twice on purpose: the list is a courtesy and
        the check is the guarantee.
        """
        want = self._where(path, "steal")
        if want.is_dir():
            self.asking = ("steal", 0, path.rstrip("/") + "/")
            return f"{want.name or want}/"
        if want.exists():
            return f"`{want.name}` is taken; a name has to be free"
        self.bench.path = want
        self.bench.apply(self.view.text())
        return f"writing {want.name} from now on"

    def do_find(self, pattern: str) -> str:
        at = self.view.find(pattern)
        return f"found `{pattern}`" if at >= 0 else f"no `{pattern}`"

    def do_findBack(self, pattern: str) -> str:
        at = self.view.find(pattern, back=True)
        return f"found `{pattern}`" if at >= 0 else f"no `{pattern}`"

    def do_goto(self, name: str) -> str:
        where = self._declared(name)
        if where is None:
            return f"no declaration `{name}`"
        return f"line {where}" if self.view.goto(where) \
            else f"`{name}` is on line {where}"

    def do_what(self, name: str) -> str:
        """What a name is — this file first, then the reference.

        **The reference is the same index the pages are made of**
        (`gestate/reference.py`), so `what wait` answers out of the
        language's own documentation rather than shrugging. Asking a
        machine that is playing music what a word means and being told
        *"no declaration"* — when the word is in the manual it ships
        with — is the sort of answer that teaches somebody the tool does
        not know things.
        """
        kind = self.bench.knob_types.get(name) if hasattr(
            self.bench, "knob_types") else None
        if kind:
            return f"{name} : Chan {kind}"
        if self._declared(name) is not None:
            return f"{name} is declared here"
        # **A builtin type is an answer, not a shrug.**  `Int` and `Bool`
        # are the compiler's own and appear in no library, so this used
        # to offer them in the list and then refuse them when picked —
        # which is the shape every refusal here is meant not to have.
        # The kind is what there is to say: `Int` is a type, `Sig` is a
        # type constructor, and knowing which is what the reader wanted.
        kind = _builtin_kind(name)
        if kind is not None:
            return f"{name} : {kind} — built in"
        found = _reference(name)
        if found is not None:
            self.page = _page(name)
            return found
        return f"no declaration `{name}`"

    #: Which argument of which command gets a name proposed into it.
    #: The `Path` one, and only for the commands that write a file whose
    #: name follows from the source's — an `open` proposing a name would
    #: be proposing you open something you did not ask for.
    PROPOSES = {"exportClap": (0, ".clap"), "exportWav": (0, ".wav"),
                "exportWavAt": (2, ".wav"),
                # **Not `.ges`**, which would propose the name of the
                # file being edited and offer to write the session over
                # the program it recorded.
                "transcript": (0, "-session.ges")}

    def _pinned(self, verb: str, at: int, query: str, rows: list) -> list:
        """The name an export proposes, put at the top of its listing.

        **Marked, not typed.**  `open` shows you the file you are in by
        putting the cursor on its row and leaving the query blank, so the
        first letter you type is a new name rather than an edit of the
        old one.  A proposed export name is the same courtesy: a row to
        press Return on, with the box empty and backspace still meaning
        what it means everywhere else.

        The row is added when the file does not exist yet — which is the
        usual case the first time — and merely lifted to the front when
        it does, so a name that is already there keeps the `taken` note
        that says so.
        """
        want = self.proposed_name(verb, at, query)
        if not want:
            return rows
        found = [r for r in rows if r[0] == want]
        rest = [r for r in rows if r[0] != want]
        if found:
            return found + rest
        return [(want, "new", True, "", False)] + rest

    def proposed_name(self, verb: str, at: int, query: str) -> str:
        """What to put in an export's empty name box.

        **`demo.ges` wants `demo.wav`**, which is what you would have
        typed — the same courtesy as marking the file you are in when
        `open` lists a directory, one argument along.  Only into an empty
        box, so it never eats what somebody has started typing.

        **A row, not a fill.**  Typing it into the box made the box
        impossible to clear — backspace emptied it and the model filled
        it straight back in, so backspace-on-empty, which is how you step
        *out* of a question, could never be reached.  Pinning it in the
        list has no such failure mode: the box stays empty, the row is
        one Return away, and the first letter typed is a new name.
        """
        if query or verb not in self.PROPOSES:
            return ""
        which, suffix = self.PROPOSES[verb]
        if at != which:
            return ""
        here = Path(getattr(self.bench, "path", "") or "")
        return f"{here.stem}{suffix}" if here.stem else ""

    def hole_at_caret(self) -> str | None:
        """The type of the `_` the cursor is standing on, if it is.

        **At either end of it**, because both are where a hand leaves the
        caret: you arrow onto a `_` and stop before it, or you delete
        what was there and stop after it.  Insisting on one would make
        the affordance work half the times it is reached for, which is
        worse than not having it — a control that works sometimes is one
        nobody trusts.

        Read from `holes`, which the workbench computed when the program
        last compiled, so this costs a lookup rather than a typecheck.
        """
        try:
            at = self.view.caret()
        except Exception:                                # noqa: BLE001
            return None
        text = self._source()
        if not text:
            return None
        lines = text.split("\n")
        # The caret is a character offset; a hole is a line and a column.
        row, seen = 0, 0
        for n, line in enumerate(lines):
            if seen + len(line) >= at:
                row = n
                break
            seen += len(line) + 1
        else:
            return None
        col = at - seen
        for line, at_col, type_ in getattr(self.bench, "holes", []) or []:
            if line == row + 1 and at_col <= col <= at_col + 1:
                return type_
        return None

    def do_fits(self, wanted: str) -> str:
        """What could stand where this type is wanted — the compiler answering.

        **The text in the window, not the file on disk.**  A person asks
        what fits while writing the thing that needs it, and the answer
        has to be about the program in front of them; reading the saved
        file would answer about the program they had before they started.

        A file that does not compile is the ordinary case here, not an
        error — you are mid-line — so the complaint is the answer, and it
        goes on the page where it can be read rather than into a status
        line that truncates it.
        """
        from .typecheck import FitsError, fits_in_source

        try:
            text = self.view.text() or self.bench.source()
        except Exception:                                # noqa: BLE001
            text = ""
        if not (wanted or "").strip():
            wanted = self.hole_at_caret() or ""
            if not wanted:
                return "fits: which type?"
        try:
            matches, shown = fits_in_source(wanted, text,
                                            rate=getattr(self.bench, "rate",
                                                         22050))
        except FitsError as exc:
            self.page = [f"what fits {wanted}:", "",
                         *str(exc).splitlines()]
            return f"fits {wanted}: the file does not compile"
        if not matches:
            self.page = None
            return f"nothing in scope fits {shown}"
        self.page = [f"what fits {shown}:", "", *(f"  {m}" for m in matches)]
        return (f"{len(matches)} fit {shown}" if len(matches) != 1
                else f"one thing fits {shown}")

    def _source(self) -> str:
        """The program as it stands — the window's copy, not the file's."""
        try:
            return self.view.text() or self.bench.source()
        except Exception:                                # noqa: BLE001
            return ""

    def do_fmtAll(self) -> str:
        """Lay the whole file out the way `gestate fmt` would.

        **One edit, and therefore one undo.**  The document is replaced
        rather than rewritten line by line, which the rope does as a
        single commit — so a format you did not want is one `undo` away,
        and the caret is clamped rather than reset because losing your
        place on every format is what makes an editor feel like a form.
        """
        text = self._source()
        try:
            laid = _formatted(text)
        except Exception as exc:                         # noqa: BLE001
            return f"fmtAll: {_first_line(exc)}"
        if laid == text:
            return "already laid out"
        if not self.view.replace(laid):
            return "fmtAll: nowhere to put it"
        return "laid out the file"

    def do_fmt(self, first: int, last: int) -> str:
        """Lay out the declarations these lines touch, and nothing else.

        **Whole declarations, always.**  A range landing in the middle of
        a body widens to the declaration around it, because half a
        declaration is not a thing the parser can lay out and a formatter
        that quietly did something else to the other half would be worse
        than one that says what it took.  The sentence names what it
        actually formatted, so the widening is visible rather than
        surprising.
        """
        text = self._source()
        first, last = min(first, last), max(first, last)
        try:
            laid, at, to = _formatted_range(text, first, last)
        except Exception as exc:                         # noqa: BLE001
            return f"fmt: {_first_line(exc)}"
        if at == 0:
            return f"fmt: no declaration on lines {first}-{last}"
        if laid == text:
            return f"lines {at}-{to} are already laid out"
        if not self.view.replace(laid):
            return "fmt: nowhere to put it"
        return (f"laid out line {at}" if at == to
                else f"laid out lines {at}-{to}")

    def _annotated(self, only: str | None) -> tuple:
        """`(new source, the names annotated)` — the shared half of `infer`.

        **Written above the definition, never over it.**  A signature the
        author typed is the authority and is left alone; what is offered
        is only what nobody wrote, which is also what makes this safe to
        press twice — the second time there is nothing left to add.
        """
        from .typecheck import signatures_in_source

        text = self._source()
        found = signatures_in_source(text)
        if only is not None:
            found = {k: v for k, v in found.items() if k == only}
        if not found:
            return text, ()
        lines = source_lines = text.splitlines()
        where = {}
        for n, line in enumerate(source_lines, start=1):
            if not line[:1].isalpha():
                continue
            head = line.split("=", 1)[0].split(":", 1)[0].split()
            if head and head[0] in found:
                where.setdefault(head[0], n)
        # Bottom up, so an insertion never moves a line still to be used.
        done = []
        for name in sorted(where, key=lambda k: -where[k]):
            at = where[name]
            lines = lines[:at - 1] + [found[name]] + lines[at - 1:]
            done.append(name)
        return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), \
            tuple(sorted(done))

    def do_inferAll(self) -> str:
        """Write a signature above every declaration that has none.

        The compiler already knows these types — it inferred them to
        compile the file — so this is the answer being *written down*
        rather than computed, which is why it cannot disagree with what
        the program means.
        """
        try:
            laid, done = self._annotated(None)
        except Exception as exc:                         # noqa: BLE001
            return f"inferAll: {_first_line(exc)}"
        if not done:
            return "every declaration already has a signature"
        if not self.view.replace(laid):
            return "inferAll: nowhere to put it"
        return (f"wrote {len(done)} signatures" if len(done) != 1
                else f"wrote `{done[0]}`'s signature")

    def do_infer(self, name: str) -> str:
        """Write the signature of one declaration.

        `inferAll` for the whole file is the sweep; this is for the line
        you are looking at, which is the ordinary case — a type you want
        to *read* before you decide whether it is the type you meant.
        """
        if not (name or "").strip():
            return "infer: which declaration?"
        name = name.strip()
        try:
            laid, done = self._annotated(name)
        except Exception as exc:                         # noqa: BLE001
            return f"infer: {_first_line(exc)}"
        if not done:
            # Two very different facts, and telling them apart is the
            # whole of `canvas`'s lesson: a name that already says what
            # it is, against a name that is not there at all.
            if name in _declared_names(self._source()):
                return f"`{name}` already has a signature"
            return f"no declaration `{name}`"
        if not self.view.replace(laid):
            return "infer: nowhere to put it"
        return f"wrote `{name}`'s signature"

    def do_symbol(self, which: str = "") -> str:
        """Put a symbol at the cursor.

        Takes the letter the table shows, or the symbol itself — the
        second because a command is a thing you can also *type*, and
        `symbol >` refusing while `symbol a` worked would be a picker
        that only answers to its own table.
        """
        want = (which or "").strip()
        if not want:
            return "symbol: which one?"
        table = {_letter(i): g for i, (g, _n) in enumerate(SYMBOLS)}
        glyph = table.get(want.lower())
        if glyph is None:
            glyph = next((g for g, _n in SYMBOLS if g == want), None)
        if glyph is None:
            return f"no symbol `{want}`"
        if not self.view.insert(glyph):
            return "symbol: nowhere to put it"
        # **And it goes away, because typing a character is finished.**
        # Return on a finished call means *again* — right for `find`,
        # and here it left the table sitting over the line you had just
        # put the symbol into, hiding the one thing you opened it to
        # change.  `template` needed the same say-when-you-are-done, and
        # this is the same order.
        self.view.close_list()
        return f"typed {glyph}"

    def do_transcript(self, path: str = "") -> str:
        """Write down what this session has done so far.

        The recording is always running; this is where it lands.  It
        replays with `python -m gestate.sessionlog <file>`, which reports
        every command whose answer has moved — a bug found by playing,
        kept by having been played.
        """
        if self.log is None or not self.log.steps:
            return "nothing has happened yet"
        want = self._where(path, "transcript") if (path or "").strip() \
            else self._default_out("session")
        if want.is_dir():
            self.asking = ("transcript", 0, path.rstrip("/") + "/")
            return f"{want.name or want}/"
        try:
            want.parent.mkdir(parents=True, exist_ok=True)
            want.write_text(self.log.text())
        except OSError as exc:
            return f"transcript: {_first_line(exc)}"
        # **And the list goes away, because writing it is finished** —
        # the same say-when-you-are-done `open`, `template` and
        # `symbol` use.  Return on a finished transcript meant *write
        # it again*, and the keystrokes after saving a recording are
        # aimed at the work, not the dialog.
        self.view.close_list()
        return f"wrote {want.name} — {len(self.log.steps)} steps"

    def do_template(self, name: str) -> str:
        """Put one of the language's ideas at the cursor.

        **The prose stays behind.**  A template's header is written to be
        read in the list — it says what the idea is and why it is spelled
        that way — and pasting it would put somebody else's explanation
        in the middle of your file, where it goes stale the moment you
        change the line under it.

        The insertion is an ordinary text edit, which is what keeps undo
        text undo: there is no record of "a template was pasted" for a
        second model to disagree with the first about.
        """
        if not (name or "").strip():
            return "template: which one?"
        # **Return again means done, not again.**  A finished call
        # repeats on Return — the next match, the next take — which is
        # right for `find` and wrong here, where again is a second copy
        # of the same code pasted under the first.  So the second press
        # closes the dialog and keeps what you have.
        if self.inserted == name.strip():
            self.inserted = None
            self.view.close_list()
            return f"kept `{name}`"
        found = next((s for s in templates() if s.name == name.strip()), None)
        if found is None:
            return f"no template `{name}`"
        if not found.body:
            return f"`{name}` is all prose and no program"
        if not self.view.insert(found.body):
            return f"`{name}`: nowhere to put it"
        # The header is worth reading *after* choosing too — it is where
        # the reasoning is, and the file no longer carries it.
        self.inserted = found.name
        self.page = [f"{found.name} — Return keeps it, Esc undoes it", "",
                     *found.doc]
        return f"inserted `{name}`"

    #: An export that has been asked for and is waiting on a yes.
    #: `(kind, target)`, or `None`.
    def _default_out(self, kind: str):
        """Where an export goes when nobody says.

        `~/.clap/` for a plugin because that is where a CLAP host looks,
        so exporting and hearing it in a DAW is one step rather than two.
        A `.wav` goes beside the source it came from, because a render is
        a thing you made *of this file* and the file's own directory is
        where you will look for it.
        """
        here = Path(getattr(self.bench, "path", "") or "untitled.ges")
        if kind == "clap":
            return Path.home() / ".clap" / f"{here.stem}.clap"
        if kind == "session":
            return here.parent / f"{here.stem}-session.ges"
        return here.parent / f"{here.stem}.wav"

    def _seconds_of(self, bar: int) -> float:
        """When a bar starts, in seconds, at the tempo now playing."""
        bpm = getattr(self.bench, "bpm", 120)
        if not isinstance(bpm, (int, float)) or bpm <= 0:
            bpm = 120
        return _beats_of(bar) * 60.0 / float(bpm)

    def _export(self, kind: str, path: str, bars=None) -> str:
        # **Nothing to export is a refusal, not a build.**  An export
        # runs `clang` or eight seconds of audio, and starting either on
        # an empty buffer would be a long wait for an answer about a
        # program that is not there.
        if not self._source().strip():
            return "nothing to export yet"
        want = self._where(path, f"export{kind.capitalize()}") if (path or "").strip() \
            else self._default_out(kind)
        if want.is_dir():
            self.asking = (f"export{kind.capitalize()}", 0,
                           path.rstrip("/") + "/")
            return f"{want.name or want}/"
        span = None
        if bars is not None:
            span = (self._seconds_of(bars[0]), self._seconds_of(bars[1] + 1))
            if span[1] <= span[0]:
                return "exportWavAt: that is no time at all"
        if want.exists() and self.confirming != (kind, want, span):
            # **Asked, not refused.**  `steal` refuses a taken name
            # because taking one is naming what you are writing and
            # doing that over somebody's file is a delete wearing a
            # friendlier word.  An export is the opposite case: writing
            # over the plugin you exported an hour ago is the *ordinary*
            # thing, and refusing it would make the command useless
            # exactly when it is working.  So the question is asked.
            self.confirming = (kind, want, span)
            self.asking = ("overwrite", 0, "")
            return f"{want.name} exists — you want to overwrite? [y/n]"
        self.confirming = None
        return self._start_export(kind, want, span)

    def _start_export(self, kind: str, want, span=None) -> str:
        """Off the loop's thread, and it says so when it lands.

        A CLAP export runs `clang` and `cargo`; a render is seconds of
        audio.  `spec/workbench.md`'s rule — *applying an edit never
        blocks* — is about exactly this: a GUI callback that waits for a
        build is a frozen window.  So the work goes to a thread and the
        answer arrives the way a rebuild's does, as a message the status
        line picks up.
        """
        import threading

        text = self._source()
        want.parent.mkdir(parents=True, exist_ok=True)

        def work():
            try:
                made = (_export_clap(text, want, self.bench)
                        if kind == "clap" else _export_wav(text, want, span))
            except Exception as exc:                     # noqa: BLE001
                self.bench.say(f"{want.name}: {_first_line(exc)}")
            else:
                self.bench.say(f"wrote {made}")

        threading.Thread(target=work, daemon=True).start()
        return f"exporting {want.name}…"

    def do_exportClap(self, path: str = "") -> str:
        """Build this file as a CLAP plugin."""
        return self._export("clap", path)

    def do_exportWav(self, path: str = "") -> str:
        """Render this file to a `.wav`."""
        return self._export("wav", path)

    def do_exportWavAt(self, first: int, last: int, path: str = "") -> str:
        """Render the bars between two numbers, counting from zero.

        **Played from the top and cut, never started at the bar.**  A
        synth's sound at bar five is what its filters and envelopes have
        been doing since bar one — starting the render there would give
        you a different piece that happens to share a score.  So the
        whole thing is rendered to the end of the last bar and the front
        is taken off, which is what a bounce does everywhere else.
        """
        first, last = min(first, last), max(first, last)
        if first < 0:
            return "exportWavAt: bars count from zero"
        return self._export("wav", path, bars=(first, last))

    def do_overwrite(self, answer: str) -> str:
        """Answer the question an export asked.

        **It only ever answers a question that was asked.**  Run with
        nothing pending it says so, rather than doing something to a file
        nobody named — a command whose meaning depends on what happened
        before it has to be able to say when nothing did.
        """
        if self.confirming is None:
            return "nothing is waiting to be overwritten"
        kind, want, span = self.confirming
        # **Cleared either way, before anything happens.**  Left set, a
        # yes would answer the *next* export to the same name too — the
        # question asked once and silently taken as standing, which is
        # the one thing a confirmation must never do.
        self.confirming = None
        if not (answer or "").strip().lower().startswith("y"):
            return f"left {want.name} alone"
        return self._start_export(kind, want, span)

    def _declared(self, name: str):
        """The line a name was declared on, or `None`.

        `audiospans` already answers this — it is what puts a knob beside
        its own declaration — so `goto` and `what` are two readings of a
        fact the workbench keeps for the margin.

        **Lines are 1-based**, which is `audiospans.Site`'s own
        convention: "the convention a text widget wants, and not the
        tokenizer's, which counts lines from 0".  So this hands back
        what a person would say, and nothing adds one to it.
        """
        for site in getattr(self.bench, "sites", []):
            if getattr(site, "name", None) == name:
                return getattr(site, "line", None)
        # **Banks are declarations too.**  `goto` used to know only the
        # knobs, because `sites` is what puts a knob beside its own
        # line — so `goto pad` on a `voices` bank answered "no
        # declaration" about a name the window was drawing a box for
        # three lines further down.
        for bank in getattr(self.bench, "banks", []) or []:
            if _of(bank, "name", "") == name:
                return _of(bank, "line", None)
        # And anything else the file declares, read from the text.  The
        # workbench keeps lines for the things it draws; a name it draws
        # nothing for still has one, and `goto` is the command for
        # reaching a name rather than a widget.
        return self._written(name)

    def _written(self, name: str):
        """The line a name is defined on in the source, or `None`.

        **The signature or the definition, whichever comes first**, and
        read rather than parsed: a declaration is a name at the left
        margin followed by `:` or `=`, which is what the language's own
        layout rule already guarantees.  Anything cleverer would be a
        second front end that could disagree with the real one.
        """
        try:
            text = self.view.text() or self.bench.source()
        except Exception:                                # noqa: BLE001
            return None
        for n, line in enumerate(text.splitlines(), start=1):
            if not line[:1].isalpha():
                continue
            head = line.split("=", 1)[0].split(":", 1)[0].strip()
            if head == name and (":" in line or "=" in line):
                return n
        return None

    # -- the window ----------------------------------------------------

    def do_canvas(self) -> str:
        """Show the picture the file draws.

        **Three answers, and they are about three different things.**  A
        file with no `substrate` draws nothing, and that is a fact about
        the file. A file that has one which is not built *yet* is a fact
        about the clock — `start` compiles the canvas on its own thread,
        so asking early is the ordinary case rather than an error, and
        the honest reply is to say so and open it anyway: it fills in
        when it arrives. Only a window that cannot show one at all is a
        fact about the window.

        Answering the first when the second is true sends somebody back
        to look for a bug in a program that is merely still compiling.
        """
        if not _draws(self.bench):
            # And how one would: the declaration is the whole of it
            # (`spec/substrate.md` — a canvas is a value).
            return ("this file draws nothing — a canvas is a "
                    "`substrate : Sig Sub` declaration")
        if not self.view.show("canvas"):
            return "this window shows the source only"
        return ("canvas" if getattr(self.bench, "substrate", None) is not None
                else "opening the canvas — it will appear when it builds")

    def do_source(self) -> str:
        self.view.show("source")
        return "source"

    def do_zoomIn(self) -> str:
        return "bigger" if self.view.zoom(1) else "as big as it goes"

    def do_zoomOut(self) -> str:
        return "smaller" if self.view.zoom(-1) else "as small as it goes"

    # -- performing ----------------------------------------------------
    #
    # What a played *note* does — not what a *key* means.  The letters go
    # on typing, so this is a setting on the input road and not a mode of
    # the editor; where the keyboard goes is focus.

    def do_pianoOff(self) -> str:
        return self._perform("off")

    def do_pianoOn(self) -> str:
        return self._perform("on")

    def do_pianoStep(self) -> str:
        return self._perform("step")

    def _perform(self, how: str) -> str:
        self.performing = how
        return {"off": "notes go nowhere",
                "on": "notes sound",
                "step": "notes sound and are written"}[how]

    # -- chance --------------------------------------------------------

    def do_seed(self, value: int) -> str:
        self.bench.set_seed(value)
        return f"seed {value}"

    def do_reroll(self) -> str:
        return self.do_seed(self.bench.roll_seed())

    def do_quit(self) -> str:
        self.view.close()
        return "closing"

    def play_key(self, char: str, code: str, on: bool) -> str:
        """A note from a *typed* key, while the piano has the keyboard.

        **The mapping is the model's**, because which letter is which
        note is a fact about `Keyboard`, and a window that knew it would
        be a second one to keep in step. The window sends what was
        pressed; this says what it means.
        """
        if self.performing == "off":
            return ""
        board = getattr(self.bench, "keyboard", None)
        if board is None:
            return ""
        if not on:
            board.release_key(code, char)
            return ""
        note = board.press_key(char, code)
        if note is not None and self.performing == "step":
            self.view.insert(self.bench.note_text(note))
        return ""

    def play_note(self, midi: int, on: bool) -> str:
        """A note from the drawn piano or a controller.

        **Where `performing` is read**, and the only place it is: the
        setting says what a played note *does*, so this is the one
        function that has to know, and every caller is spared asking.
        """
        if self.performing == "off":
            return ""
        self.bench.keyboard.press(midi) if on \
            else self.bench.keyboard.release(midi)
        if on and self.performing == "step":
            self.view.insert(self.bench.note_text(midi))
        return ""

    def touched(self, name: str, value: float) -> str:
        """A canvas element wrote its channel — the meaning, not the
        place.

        The window that walks the substrate did the hit-testing, the
        grab and the clamp where the picture is
        (`spec/workbench.md` §"The canvas walks over crust"); what
        crosses is the channel's declared name and the fraction its
        own rule produced.  Recorded with the slide coalesced —
        consecutive `touched` on one channel keep where the hand
        ended — which is what makes this the first canvas gesture a
        transcript can hold and replay.
        """
        value = float(value)
        doing = getattr(self.bench, "touched", None)
        if doing is not None:
            doing(name, value)
        self._journal().slid("touched", (name, value))
        return ""

    def do_skip(self) -> str:
        """The identity of `++`.

        In the palette because it is a real command and hiding it would
        be a special case: composing is the point, and the thing that
        composes with everything and changes nothing belongs beside the
        things that do.
        """
        return "nothing"


#: Bars, beats and samples all count from zero.
BEATS_PER_BAR = 4


def _typed(verb: "Verb", args: tuple) -> tuple:
    """The arguments a verb declared, from what actually arrived.

    **Everything from a palette is text**, because a person typed it and
    the wire carries names and literals; the signature in `command.ges`
    is the only thing that knows `seek` wants a number.  Reading the
    declared types here is what keeps every handler from parsing its own
    arguments — and what makes a mistyped number a sentence rather than
    a traceback.

    A type this does not recognise is left alone. `set : Named a -> a ->
    Command` has a *variable* second argument, whose real type is
    whatever the named channel carries — `do_set` resolves that from
    `knob_types`, which is the only place it is known.
    """
    out = []
    for kind, given in zip(verb.args, args):
        if not isinstance(given, str) or kind not in ("Int", "Float"):
            out.append(given)
            continue
        try:
            out.append(int(given) if kind == "Int" else float(given))
        except ValueError:
            raise ValueError(
                f"{verb.name}: `{given}` is not "
                f"{'a whole number' if kind == 'Int' else 'a number'}")
    return tuple(out)


def _beats_of(bar: int) -> float:
    """A bar number as the beat it starts on.

    **Bars count from zero, like everything else here.**  They used to
    count from one — the convention a score on paper uses — and that is
    defensible in a tool for players and wrong in this one: gestate
    counts ticks, samples, voices and list indices from zero, and an
    interface that alone said *bar 1* for the first bar made the reader
    do arithmetic to cross between the program and the window.  A
    programmatic editor should not have a house style it breaks in its
    own status line.

    Lines are the deliberate exception and stay 1-based: those are a
    *text* coordinate, every editor and every compiler message counts
    them from one, and matching the outside world matters more there
    than matching the inside.
    """
    return float(max(0, bar) * BEATS_PER_BAR)


# ── The window, and what passes between them ─────────────────────────────


def furniture(session: "Session", bench=None) -> str:
    """What the model has to say about the chrome — `furniture.rs`.

    **Derived every time it is asked for**, which is cheap and cannot go
    stale.  Everything in it is already a fact the workbench keeps for
    its own reasons: `sites` is what puts a knob beside its declaration,
    `values` is what a knob holds, `trouble` is the last complaint.  The
    description is a *reading* of those, not a second copy.
    """
    b = bench if bench is not None else session.bench
    out = [f"status\t{session.said[-1] if session.said else ''}"]

    trouble = getattr(b, "trouble", "")
    if trouble:
        # **Every line of it, one `trouble` row each, one line number.**
        # The complaint is drawn as a content box under its line now
        # (`spec/workbench.md` §"Content boxes" B1), and a box one line
        # deep proves nothing — a clang failure is many lines.  The wire
        # is line-oriented and its fields are tab-separated, so newlines
        # become rows and tabs become spaces; an old window that only
        # reads the first row draws what it always drew.
        line = _line_of(trouble, Path(getattr(b, "path", "") or "").name)
        for said in trouble.strip().splitlines():
            out.append(f"trouble\t{line}\t{said.replace(chr(9), '    ')}")

    seen = set()
    for site in getattr(b, "sites", []):
        name = getattr(site, "name", None)
        if name is None or name in seen or name not in getattr(b, "values", {}):
            continue
        # **A knob whose range is not known yet is left out, not raised
        # over.**  The description is read while the workbench may still
        # be starting — it compiles and opens a sound card on its own
        # thread now, so the editor is usable while it does — and a
        # reading of a model halfway through becoming itself must not be
        # the thing that stops the loop.  It reappears next tick.
        try:
            lo, hi = b.knob_range(name)
            value = b.values[name]
        except Exception:                                # noqa: BLE001
            continue
        seen.add(name)
        kind = getattr(b, "knob_types", {}).get(name, "Int")
        out.append(f"knob\t{name}\t{getattr(site, 'line', 0)}"
                   f"\t{value}\t{lo}\t{hi}\t{kind}\t1")

    # **And the ones the sound never reaches, drawn and marked.**  A
    # `mkKnob` nothing downstream of `sound` reads has no site, so the
    # margin drew nothing — which reads as the editor having missed the
    # line rather than as the program having ignored it.  Declaring a
    # parameter and forgetting to use it is an ordinary mistake, and the
    # window is the thing best placed to point at it.
    for name, line, literal, is_float in getattr(b, "loose", []) or []:
        if name in seen:
            continue
        seen.add(name)
        lo, hi = (0.0, 1.0) if is_float else (0, 100)
        out.append(f"knob\t{name}\t{line}\t{literal}\t{lo}\t{hi}"
                   f"\t{'Float' if is_float else 'Int'}\t0")

    # **One row per line, not per hole.**  Two holes on a line are two
    # facts about the same row of the margin, and the margin has one row
    # to say them in — so they are joined here, where the decision
    # belongs, rather than left for a painter to work out.  Ordered by
    # column, because that is the order they are read in.
    holes: dict = {}
    for line, col, type_ in sorted(getattr(b, "holes", []) or []):
        holes.setdefault(line, []).append((col, type_))
    for line, found in sorted(holes.items()):
        said = ", ".join(f"_ : {t}" for _c, t in sorted(found))
        out.append(f"hole\t{line}\t{said}")

    for bank in getattr(b, "banks", []) or []:
        name = _of(bank, "name", "")
        if not name:
            continue
        # `wired` rides at the end so a window built before it still
        # reads the five it knows — the knob row's own precedent.
        out.append(f"bank\t{name}\t{_of(bank, 'line', 0)}"
                   f"\t{_held(b, name)}\t{_of(bank, 'count', 0)}"
                   f"\t{1 if _listening(b, name) else 0}"
                   f"\t{1 if _of(bank, 'wired', True) else 0}")

    # **The score's word: layered away.**  A bank whose switch is on is
    # MIDI's — `listen` says "the score no longer drives it" — so every
    # score line that writes `voices.<bank>` is silently displaced, and
    # the margin says so at the line itself: a person reading the score
    # otherwise watches notes they can see not sound, and decides the
    # synth is broken.
    scored = set()
    try:
        scored = set(getattr(b, "scored_banks", lambda: set())())
    except Exception:                                    # noqa: BLE001
        pass
    for bank in getattr(b, "banks", []) or []:
        name = _of(bank, "name", "")
        if not name:
            continue
        # One word each — Henri shortened them from sentences: the line
        # each stands beside is the context, and a margin is not a
        # place for prose.  "disconnected" wins over "away", because a
        # bank the sound does not reach is silent whatever MIDI holds.
        if not _of(bank, "wired", True):
            word = "disconnected"
        elif name in scored and _listening(b, name):
            word = "away"
        else:
            continue
        for line in _of(bank, "mentions", []) or []:
            out.append(f"away\t{line}\t{word}")

    # **What file this is, and whether it is written down.**  The window
    # had no way to say either: a name you cannot see is one you have to
    # remember, and an edit you have not saved looked exactly like one
    # you had.
    # **Asked of the window, which keeps the saved root.**  A flag set
    # by `edited` cannot answer this: undoing back to what you saved has
    # moved twice and changed nothing, and a flag — or a version
    # counter — would go on saying modified for the rest of the session.
    out.append(f"file\t{Path(getattr(b, 'path', '') or '').name}"
               f"\t{0 if getattr(session.view, 'saved', True) else 1}")
    # **What colour each visible line is, and only the visible ones.**
    # Colouring is line-local here — tokenising a file whole and line by
    # line gives the same tokens, because the only cross-line state is
    # layout and layout carries no colour — so a line that has not
    # changed cannot have changed colour, and `painted` answers from a
    # cache for every row a keystroke did not touch.
    # **An inert file takes the syntax off and loses the transport.**
    # `.txt` and `.md` open as text beside the music (`Workbench.inert`):
    # colouring prose with a program's lexer would be wrong twice over,
    # and a stopped transport for a file that cannot play would read as
    # something waiting to be fixed.  The word crosses the wire so the
    # window can wear `[inert]` where the transport would stand — an
    # old window skips the unknown verb and loses the word, not the file.
    inert = bool(getattr(b, "inert", False))
    if inert:
        out.append("inert\t1")
    seeing = getattr(session.view, "visible", None)
    if seeing is not None and not inert:
        for line, text in seeing():
            runs = painted(text)
            if runs:
                out.append(f"paint\t{line}\t{runs}")

    if not inert:
        out.append(f"play\t{1 if _rolling(b) else 0}\t{_beats(b)}")
    # **What a played note would do, and whether anything would hear
    # it.**  The keyboard is drawn from these two: a piano nobody is
    # listening to is drawn grey, because a control that does nothing
    # and looks exactly like one that works is how you lose an evening
    # deciding whether your synth is broken.
    heard = [_of(bank, "name", "") for bank in getattr(b, "banks", []) or []
             if _listening(b, _of(bank, "name", ""))]
    out.append(f"perform\t{session.performing}\t{','.join(heard)}"
               f"\t{','.join(str(n) for n in sorted(_held_notes(b)))}"
               f"\t{getattr(getattr(b, 'keyboard', None), 'octave', 4)}")
    span = _looping(b)
    if span:
        out.append(f"loop\t{span[0]}\t{span[1]}")

    # **What the palette should be showing**, which is the filtered
    # list when one is open and everything otherwise.  The ranking is
    # the model's, so the window is handed an answer rather than a
    # question.
    for verb in session.palette_list():
        # **The argument types travel with the command**, because they
        # are what let the view *ask*: a list that only said `loop <int>
        # <int>` would leave the window parsing a usage string to learn
        # how many boxes to open, and a usage string is prose.
        out.append(f"command\t{verb.name}\t{verb}\t{verb.key}"
                   f"\t{verb.summary}\t{','.join(verb.args)}"
                   f"\t{REVERSE.get(verb.name, '')}")

    # What the argument being asked for could be, when one is.
    here = Path(getattr(b, "path", "") or "").name
    # **And when an export is asking, the one it proposes.**  `open`
    # marks the file you are in; an export marks the file it would
    # write, which is the same fact one argument along — the row the
    # cursor should open on.
    if session.asking is not None:
        verb, at, query = session.asking
        proposed = session.proposed_name(verb, at, query)
        if proposed:
            here = proposed
        # And when a device is being chosen, the one already listening —
        # the cursor opens on what is live, which is the answer to the
        # question you opened the list to ask.
        elif verb == "midiOn":
            here = getattr(b, "midi_port", None) or here
    # **The one you are on is marked, not selected.**  The view puts its
    # cursor there and leaves the query blank, so the list opens showing
    # where you are and the first letter you type is a new name rather
    # than an edit of the old one.
    for choice in session.choices():
        text, note = choice[0], choice[1]
        # **A naming row is `(name, note, kind)` and a listing row is
        # `(text, note, can, step, dim)`.**  Told apart by what the third
        # element *is*: a kind is a word, and `can` is a boolean.
        if len(choice) == 3 and not isinstance(choice[2], bool):
            choice = (choice[0], choice[1], True, "", False, choice[2])
        can = choice[2] if len(choice) > 2 else True
        step = choice[3] if len(choice) > 3 else ""
        # **Drawn faint is not the same question as may be chosen.**  A
        # name an export would overwrite is worth seeing and is still
        # yours to pick; a name `steal` refuses is neither.  Absent, it
        # follows the refusal, which is what every row did before an
        # export needed the two apart.
        dim = choice[4] if len(choice) > 4 else not can
        # **And what kind of thing it is**, so a type can be drawn as
        # one.  Empty for a row that is not a name — a path, a symbol, a
        # yes — because those are not kinds of anything.
        kind = choice[5] if len(choice) > 5 else ""
        out.append(f"choice\t{text}\t{note}"
                   f"\t{1 if text == here else 0}\t{1 if can else 0}"
                   f"\t{step}\t{1 if dim else 0}\t{kind}")

    # And a page to read, when a command answered with one.
    for line in session.page or []:
        out.append(f"page\t{line}")
    return "\n".join(out)


def _line_of(trouble: str, name: str = "") -> int:
    """Which line a complaint is about, or `0` for one about nowhere.

    The compiler has three voices — `at 12:8-12:11`, `at line 134:8`,
    and, once `in_source` was handed the path, `at broken.ges:2:8` —
    and the margin wants the number from any of them.  Read rather
    than re-derived, because the message is the only place it exists by
    the time it gets here.

    **A position in another file stays 0 on purpose**: `at prelude
    line 216:29` and `at somewhere-else.ges:5:1` must not anchor a box
    under an unrelated line of this one, so the file spelling is
    matched only against `name` — this file's own.
    """
    import re

    if name:
        found = re.search(rf"\bat {re.escape(name)}:(\d+):", trouble)
        if found:
            return int(found.group(1))
    found = re.search(r"\bat (?:line )?(\d+):", trouble)
    return int(found.group(1)) if found else 0


def _of(bank, key: str, default):
    """One field of a bank, however the workbench keeps them.

    **`Workbench.banks` is a list of dicts**, and reading it with
    `getattr` — which is what this did — quietly gave the default for
    every field: each bank went out named after its own `repr`, on line
    zero, with no voices.  Nothing drew banks at the time, so the wire
    carried nonsense for as long as it took somebody to look at it.
    """
    if isinstance(bank, dict):
        return bank.get(key, default)
    return getattr(bank, key, default)


def _held(bench, name: str) -> int:
    """How many of a bank's voices are sounding right now.

    **From `sounding_on`, which asks both sources.**  A bank driven by a
    keyboard has an allocator that knows what it holds; one driven by
    the score has none, because the schedule wrote its channels ahead of
    time and nothing tracks them — so a count that asked only the
    allocator would sit at zero through an entire piece.
    """
    try:
        return len(bench.sounding_on(name))
    except Exception:                                    # noqa: BLE001
        return 0


#: The reference, read once — it parses six files.
_REFERENCE: dict | None = None


def _reference(name: str) -> str | None:
    """What the manual says about a name, in one line, or nothing."""
    global _REFERENCE
    if _REFERENCE is None:
        try:
            from .reference import all_entries

            _REFERENCE = {}
            for entry in all_entries():
                _REFERENCE.setdefault(entry.name, entry)
        except Exception:                                # noqa: BLE001
            # A reference that will not parse must not stop a command
            # from answering about the file in front of you.
            _REFERENCE = {}
    entry = _REFERENCE.get(name)
    if entry is None:
        return None
    said = _plain(_first_sentence(" ".join(entry.doc))) if entry.doc else ""
    where = f" ({entry.library})" if entry.library else ""
    line = entry.signature.strip() or f"{entry.name} : ?"
    return f"{line}{where}" + (f" — {said}" if said else "")


def _size(entry) -> str:
    """A file's size, in the units a person reads."""
    try:
        n = entry.stat().st_size
    except Exception:                                    # noqa: BLE001
        return ""
    for unit in ("B", "K", "M", "G"):
        if n < 1024 or unit == "G":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024.0
    return ""


def _draws(bench) -> bool:
    """Whether this file draws a canvas at all.

    **Asked of the text when the built one is not there yet.**  The
    substrate compiles on its own thread, so `bench.substrate` being
    `None` means either *no canvas* or *not yet* — and the source can
    tell them apart, with the same check `_load_substrate` uses to
    decide whether to compile one.
    """
    if getattr(bench, "substrate", None) is not None:
        return True
    try:
        from .audio import has_substrate

        return bool(has_substrate(bench.source()))
    except Exception:                                    # noqa: BLE001
        return False


def _held_notes(bench) -> set:
    """Which notes the keyboard is holding down."""
    try:
        return {int(n) for n in bench.keyboard.held}
    except Exception:                                    # noqa: BLE001
        return set()


def _page(name: str) -> list:
    """What the manual says about a name, as lines to read."""
    entry = (_REFERENCE or {}).get(name)
    if entry is None:
        return []
    out = [entry.signature.strip() or name]
    if entry.library:
        out.append(entry.library
                   + (f" — {entry.section}" if entry.section else ""))
    if entry.doc:
        out.append("")
        out.extend(_plain(line) for line in entry.doc)
    if entry.alternatives:
        out.append("")
        out.extend(f"  {alt}" for alt in entry.alternatives)
    return out


def _takes_notes(bench, name: str) -> bool:
    """Whether a bank can be handed a note at all.

    A fact about its payload's type, not about a cable: a bank whose
    voices have no `FromMIDI` instance cannot be played from a keyboard,
    on-screen or otherwise.
    """
    try:
        return bool(bench.takes_midi(name))
    except Exception:                                    # noqa: BLE001
        return False


def _listening(bench, name: str) -> bool:
    try:
        return bool(bench.listening(name))
    except Exception:                                    # noqa: BLE001
        return False


def _rolling(bench) -> bool:
    """Whether time is moving.

    **Not `Workbench.playing`**, which asks whether the audio *thread*
    is alive — a different question wearing the same word, and true even
    with the transport stopped.  What a readout means by playing is that
    the beat is advancing, and that is the transport's to say.
    """
    transport = getattr(bench, "transport", None)
    if transport is not None:
        return bool(getattr(transport, "playing", False))
    return bool(getattr(bench, "playing", False))


def _looping(bench) -> tuple | None:
    """The loop, in beats, or nothing.

    **Read from the transport, in beats.**  The transport keeps it in
    *samples*, because that is what the audio thread compares against;
    the description says beats, because beats are what `loop` was given
    and what the readout shows. One conversion, here, where the rate is
    already known.
    """
    transport = getattr(bench, "transport", None)
    span = getattr(transport, "loop", None) if transport is not None else None
    if not span:
        return None
    try:
        return (round(bench.samples_to_beats(span[0]), 1),
                round(bench.samples_to_beats(span[1]), 1))
    except Exception:                                    # noqa: BLE001
        return None


def _beats(bench) -> float:
    """Where the transport is, at the precision a readout shows.

    **How often this number changes is how often the window repaints.**
    The description is compared whole and sent only when it differs, so
    a beat carried to three decimals differs on every single tick of the
    loop — and the window then reparses and redraws everything for a
    digit no one can read. One decimal is what `audioeditor`'s own
    position readout has always shown (`:.1f`), which makes this the
    precision that was already decided rather than a new guess.
    """
    try:
        return round(bench.position_in_beats(), 1)
    except Exception:                                    # noqa: BLE001
        return 0.0


def act(session: "Session", line: str) -> str:
    """One gesture from the window, done.

    The other half of the wire, and the same shape: a verb, then
    literals.  An unknown verb is a sentence rather than an exception,
    for the reason every refusal here is — this is between a person and
    a machine that is playing music.
    """
    parts = line.split("\t")
    verb = parts[0] if parts else ""
    if verb == "command":
        return session.run(*(p for p in parts[1:] if p))
    if verb == "filter":
        query = parts[1] if len(parts) > 1 else ""
        session.filtered = session.matching(query) if query else None
        if not query:
            # **Nothing to say about a list nobody is filtering.**  The
            # window clears the filter after running a command, so a
            # count answered here would land in the status line *after*
            # the command's own sentence and hide it: you would pick
            # `seek`, it would work, and the line would read "29 of 29".
            # A command's answer is the news; the size of an unfiltered
            # list is not.
            return ""
        shown = session.palette_list()
        return f"{len(shown)} of {len(session.commands())}"
    if verb == "turn" and len(parts) >= 3:
        try:
            return session.run("set", parts[1], float(parts[2]))
        except ValueError:
            return f"turn: `{parts[2]}` is not a number"
    if verb == "wants" and len(parts) >= 4:
        # The window asking what an argument could be.  It knows which
        # command and which argument; what each one *could* be is the
        # model's to say, like every other ranking here.
        try:
            at = int(parts[2])
        except ValueError:
            return f"wants: `{parts[2]}` is not an argument number"
        session.asking = (parts[1], at, parts[3])
        # **`open` says so the moment it is picked** — the one warning
        # there is: choosing a file past it proceeds, because a person
        # who was told and went on has decided (`do_open` says why it
        # keeps no guard).  Once, on the opening of the question — every
        # keystroke in the box re-asks, and a warning per letter is a
        # warning nobody reads; the window holds the words up for as
        # long as the question is open.
        if (parts[1] == "open" and at == 0 and not parts[3]
                and not getattr(session.view, "saved", True)):
            early = getattr(session.view, "warn", None)
            if early is not None:
                early("warning: unsaved changes")
        # **Backspacing out of a finished `template` is a cancel too.**
        # The palette steps back an argument and asks again, which is
        # the same *never mind* `Esc` means — and the rule the whole
        # dialog is built on is that a template you did not keep does not
        # come out.  Only for the command that pasted it: backing out of
        # anything else is about that command.
        if parts[1] == "template" and session.inserted is not None:
            name, session.inserted = session.inserted, None
            if session.view.undo():
                session.said.append(f"undid `{name}`")
        # **`fits` at a hole answers itself.**  Inference already knows
        # what belongs there, so leaving the box empty for somebody to
        # retype the compiler's own answer is the affordance failing at
        # the one moment it is most wanted.  The box is filled, and the
        # fill comes back as another `wants` — the same round trip a
        # typed letter makes — so the answer below is about what the box
        # now holds and there is one path, not two.
        if (parts[1] == "fits" and at == 0 and not parts[3]
                and session.proposed != ("fits", at)):
            found = session.hole_at_caret()
            if found:
                filler = getattr(session.view, "fill", None)
                if filler is not None and filler(found):
                    session.proposed = ("fits", at)
                    session.said.append(session.run("fits", found))
                    return ""
        # **And an export proposes a name rather than an empty box.**
        # `demo.ges` wants `demo.wav`, which is what you would have typed;
        # the row you are in is already marked in the listing, and this is
        # the same courtesy one argument along.  Typed over, because a
        # proposal you cannot refuse is a decision.
        # **An export's name is pinned in the list, not typed into the
        # box.**  Filling the box made it impossible to backspace out of
        # the question, and it was the wrong shape besides: `open`
        # already *marks* the file you are in rather than selecting it,
        # so the first letter you type is a new name rather than an edit
        # of the old.  A proposal is the same courtesy — a row to press
        # Return on, with the box left empty.
        found = session.choices()
        return f"{len(found)} name(s)" if found else ""
    if verb == "asked":
        session.asking = None
        # **And the proposal is spent with the question.**  Kept, the
        # next `exportWav` would open on an empty box because this one
        # had already been offered a name — a courtesy that works once
        # per session is worse than none.
        session.proposed = None
        return ""
    if verb == "shut":
        # The list is closed, so the page it was showing is over.
        session.page = None
        session.proposed = None
        # **A template still unkept when the list closes was refused.**
        # Return keeps it and clears this first, so anything still
        # standing here got here by `Esc` — and `Esc` out of a dialog
        # means *never mind*, which for a paste means take it back.  One
        # insert is one edit, so one undo is exact.
        if session.inserted is not None:
            name, session.inserted = session.inserted, None
            if session.view.undo():
                return f"undid `{name}`"
        return ""
    if verb == "edited":
        return ""
    if verb == "state" and len(parts) >= 5:
        # **The window volunteering its own state**, so commands about
        # the window can answer at once instead of across a frame.  A
        # view that does not keep a mirror simply does not hear it.
        noting = getattr(session.view, "note_state", None)
        if noting is not None:
            try:
                # **The fifth is optional**, so a window built before it
                # existed still reports the four it has rather than
                # having its whole state dropped for the one it does not.
                noting(int(parts[1]), int(parts[2]),
                       int(parts[3]), int(parts[4]),
                       parts[5] != "0" if len(parts) > 5 else True,
                       int(parts[6]) if len(parts) > 6 else 0,
                       int(parts[7]) if len(parts) > 7 else 40,
                       parts[8] == "1" if len(parts) > 8 else False,
                       parts[9] == "1" if len(parts) > 9 else False)
            except ValueError:
                return f"state: {line!r} is not four numbers"
        return ""
    if verb == "struck" and len(parts) >= 4:
        return session.play_key(parts[1], parts[2], parts[3] == "1")
    if verb == "note" and len(parts) >= 3:
        return session.play_note(int(parts[1]), parts[2] == "1")
    if verb == "touch" and len(parts) >= 4:
        # A hand on the canvas.  The window says where, in the canvas's
        # own pixels; which element that lands on — and what fraction of
        # its extent the point means — is the substrate's decision
        # (`spec/substrate.md`), so nothing here interprets the place.
        try:
            session.bench.touch(parts[1], int(parts[2]), int(parts[3]))
        except ValueError:
            return f"touch: `{parts[2]} {parts[3]}` is not a place"
        return ""
    if verb == "touched" and len(parts) >= 3:
        # The crust-walking canvas's word: what the gesture *meant*,
        # already hit-tested and clamped where the picture is —
        # `spec/workbench.md` §"The canvas walks over crust".
        try:
            return session.touched(parts[1], float(parts[2]))
        except ValueError:
            return f"touched: `{parts[2]}` is not a value"
    return f"no gesture `{verb}`"
