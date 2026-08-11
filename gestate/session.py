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
                out.setdefault(name, _first_sentence(text))
        if not stripped.startswith("#:"):
            held = []
    return out


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


#: The shortcuts.  **Every one names a command**, and a test holds that
#: — a key that did something the list did not offer would be a second
#: vocabulary, which is the thing the list exists to prevent.
KEYS = {
    "apply": "Ctrl-S",
    "audition": "Ctrl-Return",
    "play": "Space",
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

    def find(self, _pattern: str) -> int:
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
    performing: str = "on"
    #: The palette's current answer — what `filter` last produced.
    filtered: list = field(default_factory=list)

    def commands(self) -> list:
        """The palette.  Derived from `command.ges` every time it is
        asked for, which is cheap and cannot go stale."""
        return vocabulary()

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
        self.bench.listen(name, on)
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

    def do_goto(self, name: str) -> str:
        where = self._declared(name)
        if where is None:
            return f"no declaration `{name}`"
        return f"line {where}" if self.view.goto(where) \
            else f"`{name}` is on line {where}"

    def do_what(self, name: str) -> str:
        kind = self.bench.knob_types.get(name) if hasattr(
            self.bench, "knob_types") else None
        if kind:
            return f"{name} : Chan {kind}"
        if self._declared(name) is None:
            return f"no declaration `{name}`"
        return f"{name} is declared here"

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
        return None

    # -- the window ----------------------------------------------------

    def do_canvas(self) -> str:
        return "canvas" if self.view.show("canvas") else "this file draws nothing"

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

    def do_performOff(self) -> str:
        return self._perform("off")

    def do_performOn(self) -> str:
        return self._perform("on")

    def do_performStep(self) -> str:
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
        seen.add(name)
        lo, hi = b.knob_range(name)
        kind = getattr(b, "knob_types", {}).get(name, "Int")
        out.append(f"knob\t{name}\t{getattr(site, 'line', 0)}"
                   f"\t{b.values[name]}\t{lo}\t{hi}\t{kind}")

    for bank in getattr(b, "banks", []) or []:
        name = getattr(bank, "name", str(bank))
        out.append(f"bank\t{name}\t{getattr(bank, 'line', 0)}"
                   f"\t{getattr(bank, 'voices', 0)}"
                   f"\t{1 if _listening(b, name) else 0}")

    out.append(f"play\t{1 if getattr(b, 'playing', False) else 0}"
               f"\t{_beats(b)}")
    span = getattr(b, "loop_span", None)
    if span:
        out.append(f"loop\t{span[0]}\t{span[1]}")

    for verb in session.commands():
        out.append(f"command\t{verb.name}\t{verb}\t{verb.key}"
                   f"\t{verb.summary}")
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


def _listening(bench, name: str) -> bool:
    try:
        return bool(bench.listening(name))
    except Exception:                                    # noqa: BLE001
        return False


def _beats(bench) -> float:
    try:
        return round(bench.position_in_beats(), 3)
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
        session.filtered = session.matching(query)
        return f"{len(session.filtered)} of {len(session.commands())}"
    if verb == "turn" and len(parts) >= 3:
        try:
            return session.run("set", parts[1], float(parts[2]))
        except ValueError:
            return f"turn: `{parts[2]}` is not a number"
    if verb == "edited":
        return ""
    if verb == "note" and len(parts) >= 3:
        return session.play_note(int(parts[1]), parts[2] == "1")
    return f"no gesture `{verb}`"
