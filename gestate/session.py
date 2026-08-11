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


def vocabulary(path: Path = COMMANDS) -> list:
    """Every command `command.ges` declares, in the order written.

    **Derived, never maintained.**  The order is the file's, so the
    palette reads in the order somebody thought about them rather than
    alphabetically, which is a worse order for learning.
    """
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
    return out


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

    def commands(self) -> list:
        """The palette.  Derived from `command.ges` every time it is
        asked for, which is cheap and cannot go stale."""
        return vocabulary()

    def names(self) -> list:
        """Every name a `Named` argument could be, and what it is.

        Knobs and banks, which are the names a person means when a
        command asks for one — and they are already facts the workbench
        keeps, so this is a reading rather than a second list.
        """
        out, seen = [], set()
        kinds = getattr(self.bench, "knob_types", {}) or {}
        for site in getattr(self.bench, "sites", []) or []:
            name = getattr(site, "name", None)
            if name is None or name in seen:
                continue
            seen.add(name)
            out.append((name, f"Chan {kinds.get(name, 'Int')}"))
        for bank in getattr(self.bench, "banks", []) or []:
            name = _of(bank, "name", "")
            if not name or name in seen:
                continue
            seen.add(name)
            out.append((name, f"{_of(bank, 'count', 0)} voices"))
        return out

    def naming(self, query: str) -> list:
        """The names a typed query means, best first.

        **The same rule as `matching`, over names instead of commands**,
        and here for the same reason: which of several things a person
        meant is a decision, and a decision belongs in one place.
        """
        query = query.strip().lower()
        found = []
        for i, (name, note) in enumerate(self.names()):
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
            found.append((rank, i, (name, note)))
        return [pair for _r, _i, pair in sorted(found, key=lambda f: f[:2])]

    def choices(self) -> list:
        """What the argument being asked for could be, or nothing."""
        if self.asking is None:
            return []
        verb, at, query = self.asking
        found = self.find(verb)
        if found is None or at >= found.arity:
            return []
        if found.args[at] != "Named":
            # **Only names can be offered.**  A number or a piece of
            # text is typed, not chosen; offering a list of numbers
            # would be a menu of guesses.
            return []
        return self.naming(query)

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
        try:
            args = _typed(verb, args)
        except ValueError as e:
            return self._say(str(e))
        try:
            return self._say(handler(*args))
        except Exception as e:                            # noqa: BLE001
            # The workbench refusing is a thing to read, not a traceback
            # in somebody's terminal: this layer is between a person and
            # a machine that is playing music.
            return self._say(f"{name}: {e}")

    def _say(self, sentence: str) -> str:
        self.said.append(sentence)
        return sentence

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
        return "applying"

    def do_audition(self) -> str:
        self.bench.audition(self.view.text())
        return "auditioning"

    def do_play(self) -> str:
        return "playing" if self.bench.toggle() else "stopped"

    def do_stop(self) -> str:
        self.bench.pause()
        return "stopped"

    def do_seek(self, bar: int) -> str:
        # Bars count from one where a person is concerned and from zero
        # where a transport is; the conversion belongs here, once.
        self.bench.seek_beats(_beats_of(bar))
        return f"at bar {bar}"

    # -- the loop ------------------------------------------------------

    def do_loop(self, first: int, last: int) -> str:
        if last <= first:
            return f"bar {last} is not after bar {first}"
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
        return f"{name} {'hears' if on else 'ignores'} the keyboard"

    def do_octave(self, by: int) -> str:
        where = self.bench.keyboard.transpose(by)
        return f"octave {where}"

    # -- the text ------------------------------------------------------

    def do_undo(self) -> str:
        return "undone" if self.view.undo() else "nothing to undo"

    def do_redo(self) -> str:
        return "redone" if self.view.redo() else "nothing to redo"

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
        found = _reference(name)
        if found is not None:
            self.page = _page(name)
            return found
        return f"no declaration `{name}`"

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
            return "this file draws nothing"
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

    def do_skip(self) -> str:
        """The identity of `++`.

        In the palette because it is a real command and hiding it would
        be a special case: composing is the point, and the thing that
        composes with everything and changes nothing belongs beside the
        things that do.
        """
        return "nothing"


#: Bars count from one for a person and from zero for a transport.
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
    """A bar number as the beat it starts on."""
    return float(max(0, bar - 1) * BEATS_PER_BAR)


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
        first = trouble.strip().splitlines()[0]
        out.append(f"trouble\t{_line_of(trouble)}\t{first}")

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
                   f"\t{value}\t{lo}\t{hi}\t{kind}")

    for bank in getattr(b, "banks", []) or []:
        name = _of(bank, "name", "")
        if not name:
            continue
        out.append(f"bank\t{name}\t{_of(bank, 'line', 0)}"
                   f"\t{_held(b, name)}\t{_of(bank, 'count', 0)}"
                   f"\t{1 if _listening(b, name) else 0}")

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
    for text, note in session.choices():
        out.append(f"choice\t{text}\t{note}")

    # And a page to read, when a command answered with one.
    for line in session.page or []:
        out.append(f"page\t{line}")
    return "\n".join(out)


def _line_of(trouble: str) -> int:
    """Which line a complaint is about, or `0` for one about nowhere.

    The compiler says `at 12:8-12:11`; a status bar shows one line of
    that and the margin wants the number.  Read rather than re-derived,
    because the message is the only place it exists by the time it gets
    here.
    """
    import re

    found = re.search(r"\bat (\d+):", trouble)
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
        found = session.choices()
        return f"{len(found)} name(s)" if found else ""
    if verb == "asked":
        session.asking = None
        return ""
    if verb == "shut":
        # The list is closed, so the page it was showing is over.
        session.page = None
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
                noting(int(parts[1]), int(parts[2]),
                       int(parts[3]), int(parts[4]))
            except ValueError:
                return f"state: {line!r} is not four numbers"
        return ""
    if verb == "struck" and len(parts) >= 4:
        return session.play_key(parts[1], parts[2], parts[3] == "1")
    if verb == "note" and len(parts) >= 3:
        return session.play_note(int(parts[1]), parts[2] == "1")
    return f"no gesture `{verb}`"
