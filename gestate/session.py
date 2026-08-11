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
        spec = " ".join(f"<{a.lower()}>" for a in self.args)
        return f"{self.name} {spec}".strip()


def _arrow_parts(node) -> list:
    """A signature's arguments and result, as type names.

    Reads the parsed form rather than the text, so `Int -> Int ->
    Command` and a reformatting of it are the same answer.
    """
    from .syntax.ast import VConId, VOpPhrase

    if isinstance(node, VOpPhrase):
        return [a.value if isinstance(a, VConId) else "?"
                for a in node.atoms if a != "->"]
    if isinstance(node, VConId):
        return [node.value]
    return ["?"]


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

    def zoom(self, _by: int) -> bool:
        return False

    def show(self, _what: str) -> bool:
        return False

    def close(self) -> None:
        pass


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
        end = getattr(self.bench, "end_beat", None)
        if end is None:
            return "nothing to loop"
        self.bench.set_loop(0.0, float(end))
        return "looping the whole piece"

    def do_loopOff(self) -> str:
        self.bench.clear_loop()
        return "not looping"

    # -- parameters ----------------------------------------------------

    def do_set(self, name: str, value: float) -> str:
        if not self.bench.has_knob() or name not in self.bench.values:
            return f"no parameter `{name}`"
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

    def do_what(self) -> str:
        return "nothing under the cursor"

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

    def do_quit(self) -> str:
        self.view.close()
        return "closing"


#: Bars count from one for a person and from zero for a transport.
BEATS_PER_BAR = 4


def _beats_of(bar: int) -> float:
    """A bar number as the beat it starts on."""
    return float(max(0, bar - 1) * BEATS_PER_BAR)
