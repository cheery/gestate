"""One window: the editor, and the canvas behind it — `spec/substrate.md`.

Two tabs and `Esc` between them.  The editor is on one, the program's own
`substrate` on the other, and both are views of the same `Workbench` —
which owns the instrument, the rebuild thread, the knobs, the transport and
the keyboard, and imports no toolkit.  That seam is why this is a second
view rather than a rewrite: the `tkinter` editor goes on working while this
one grows up.

**The useful half is headless**, the same split `gui.py` makes.  `Document`
is text and a cursor over `balanced.py`'s rope; `Pane` is what a key
*means* — the mode, the edit, the gesture — and neither imports pygame.
`run` is the loop, and is the only thing that does.

    python -m gestate.audiopygame examples/audio/polysine.ges
    python -m gestate.audiopygame file.ges --midi 1    # and a controller
    python -m gestate.audiopygame --midi-ls            # what is plugged in

Keys: `Esc` outward, `Return` back in, `i` to type, `Ctrl-S` to apply,
`Ctrl-Return` to audition, `Ctrl-Q` to quit; `Page Up`/`Page Down` and the
arrows move; `Ctrl +`/`Ctrl -` size the text.  `Tab` at a `_` lists what
would fit the hole and is an indent anywhere else.  From command mode:
space plays and stops, `s` applies, `p` opens the piano and `P` opens it in
**step** mode, which writes what it plays at the cursor, `?` says what the
name under the cursor is, `o` loops and `O` loops the whole piece, and
`[`/`]` put the loop's ends where the transport has reached.  `/` searches
and `n`/`N` step through what it found, as they do in vim — the cursor
follows the pattern as you type it, `Return` keeps the place and `Esc` puts
it back.

**The mouse turns things.**  A knob is a trough beside the line that
declares it: drag it to turn it, right-click it to bind the next controller
that moves.  The drawn keyboard plays under the pointer, and `<`/`>` move
its octave.  Everything placed by *content* rather than by the chrome is
found through `Layout.knob_rect` and `Layout.piano_keys` — the same
arithmetic the draw uses, so where a thing is painted and where a click
lands cannot drift apart, and both can be checked without a window.

The window is resizable, and nothing here remembers a size: `Layout` is
built from the window there is, each frame, which is also what makes the
chrome testable — where a click *lands* is arithmetic, and arithmetic can
be checked without opening anything.

**The editor is already modal and has always been**, which is the argument
for saying so.  `tkinter`'s space bar plays or types a space depending on
where the focus happens to be, and the on-screen piano takes letter keys
away from whatever had them.  A mode you cannot see is worse than one you
choose, so here it is chosen, and the whole gutter changes colour with it.

Three rules keep it from being the thing people mean when they say "modal":

* **`Esc` goes outward and `Return` comes back** — text, command, canvas,
  and back again.  Two keys, two directions, and neither is ever a
  question.  (`Return` in text mode is a newline, which is why the test is
  on the mode rather than on the key.)
* **Insert mode is an ordinary editor.**  Arrows, Home/End, Ctrl-S,
  Backspace: everything works where it always did.  A modal editor that
  also breaks insert mode is where the reputation comes from.
* **The piano is its own mode** rather than stealing letters from another.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .balanced import blank as _empty_rope

#: The modes, outermost last.  `Esc` moves right along this list and stops.
MODES = ("text", "command", "canvas")

#: What `plain` means: start in text and never leave.  One setting rather
#: than a fork — the same code, a different starting mode and no `Esc`.
PLAIN = "plain"


class Document:
    """Text and a cursor, over `balanced.py`'s rope.

    The rope is what makes this cheap: `insert`, `erase`, `row` and
    `rowpos` are already written and already tested, which is the half of a
    text editor nobody wants to write twice.  What is here is the cursor,
    and the cursor is the only thing that has to be got right.
    """

    def __init__(self, text: str = ""):
        self.rope = _empty_rope.insert(0, text)
        #: Character offset into the whole document.  One number, because a
        #: (row, column) pair has to be kept true across every edit and this
        #: does not — the rope answers both questions from it.
        self.pos = 0
        #: Where a selection was started, or `None`.  A selection is the
        #: span between this and the cursor, in whichever order they are —
        #: one number, so dragging backwards needs no special case.
        self.mark: int | None = None
        #: The column a vertical move aims for.  Moving down through a
        #: short line and on to a long one should come back out where it
        #: went in, which one wandering column cannot do.
        self.goal: int | None = None

    # -- reading ------------------------------------------------------------

    @property
    def text(self) -> str:
        return "".join(self.rope)

    @property
    def rows(self) -> int:
        return self.rope.newlines + 1

    def line(self, row: int) -> str:
        """One line, without its newline."""
        if row < 0 or row >= self.rows:
            return ""
        start = self.rope.rowpos(row)
        stop = (self.rope.rowpos(row + 1) - 1 if row + 1 < self.rows
                else self.rope.length)
        return "".join(self.rope.segments(start, max(start, stop)))

    @property
    def row(self) -> int:
        return self.rope.row(self.pos)

    @property
    def column(self) -> int:
        return self.pos - self.rope.rowpos(self.row)

    # -- selecting ----------------------------------------------------------

    def selection(self) -> tuple | None:
        """`(start, stop)`, or `None` when nothing is selected.

        **Clamped to the text there is.**  A mark is a number, and an edit
        that shortens the document can leave it past the end — which is a
        wrong highlight if it is only read, and an `IndexError` out of the
        rope if it is used to cut.  The editing methods below drop the mark
        for that reason and this is the second answer to the same question:
        a selection is never allowed to name text that is not there.
        """
        if self.mark is None or self.mark == self.pos:
            return None
        mark = max(0, min(self.mark, self.rope.length))
        pos = max(0, min(self.pos, self.rope.length))
        if mark == pos:
            return None
        return (min(mark, pos), max(mark, pos))

    def selected(self) -> str:
        span = self.selection()
        return "" if span is None else "".join(self.rope.segments(*span))

    def drop_mark(self) -> None:
        self.mark = None

    def cut_selection(self) -> str:
        """Remove what is selected and hand it back."""
        span = self.selection()
        if span is None:
            return ""
        text = self.selected()
        start, stop = span
        self.rope = self.rope.erase(start, stop)
        self.pos, self.mark, self.goal = start, None, None
        return text

    # -- editing ------------------------------------------------------------

    # **An edit drops the mark**, which is the same rule as "a selection you
    # moved away from is one you did not mean to keep" and is not only
    # tidiness.  A click leaves the mark *at* the cursor, so a `Backspace`
    # after one used to walk the cursor away from a mark that stayed put:
    # what you had just deleted came back highlighted, and when the mark
    # ended up past the shortened text the next keystroke cut a range the
    # rope does not have — an `IndexError` from `segments`, mid-typing.

    def insert(self, text: str) -> None:
        """Typing over a selection replaces it, as everywhere else."""
        self.cut_selection()
        self.rope = self.rope.insert(self.pos, text)
        self.pos += len(text)
        self.mark, self.goal = None, None

    def backspace(self) -> None:
        if self.cut_selection():
            return
        self.mark = None
        if self.pos == 0:
            return
        self.rope = self.rope.erase(self.pos - 1, self.pos)
        self.pos -= 1
        self.goal = None

    def delete(self) -> None:
        if self.cut_selection():
            return
        self.mark = None
        if self.pos >= self.rope.length:
            return
        self.rope = self.rope.erase(self.pos, self.pos + 1)
        self.goal = None

    # -- moving -------------------------------------------------------------

    def move(self, by: int) -> None:
        self.pos = max(0, min(self.rope.length, self.pos + by))
        self.goal = None

    def home(self) -> None:
        self.pos = self.rope.rowpos(self.row)
        self.goal = None

    def end(self) -> None:
        self.pos = self.rope.rowpos(self.row) + len(self.line(self.row))
        self.goal = None

    def vertical(self, by: int) -> None:
        """Up or down, keeping the column you set out from.

        `goal` is remembered rather than recomputed: passing through a
        short line would otherwise drag the column in with it, and coming
        back out on a long line is where an editor feels wrong.
        """
        goal = self.column if self.goal is None else self.goal
        row = max(0, min(self.rows - 1, self.row + by))
        self.pos = self.rope.rowpos(row) + min(goal, len(self.line(row)))
        self.goal = goal

    def go_to(self, row: int, column: int) -> None:
        row = max(0, min(self.rows - 1, row))
        self.pos = self.rope.rowpos(row) + max(0, min(column,
                                                      len(self.line(row))))
        self.goal = None


@dataclass
class Dialog:
    """Lines over the text, and how much of them is on screen.

    `?`'s answer is three lines and any key takes it away, which is the
    whole design: it is about the word you are looking at.  `Tab`'s answer
    is every name in scope that fits a hole, which is regularly forty — so
    a dialog has to be able to **scroll**, and one that scrolls has to keep
    the keys that scroll it rather than being dismissed by them.

    Which it is, is `scrolls`.  Both kinds are this class because the
    difference between them is one flag and not a second popup.
    """

    #: `[(kind, text)]`, coloured by `_FACT` like every other fact here.
    rows: list
    #: The first row on screen.  Here rather than on the pane because it
    #: belongs to *this* dialog and goes away with it.
    top: int = 0
    #: Does it scroll, and therefore own the arrows while it is up?
    scrolls: bool = False
    #: How many rows the last draw had room for — what a page is worth.
    #: Written by the view, because only the view knows the height.
    shown: int = 1

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def scroll(self, by: int) -> str:
        """Move the window, and say where it got to."""
        self.top = max(0, min(max(0, len(self.rows) - 1), self.top + by))
        return ""

    def window(self, most: int) -> list:
        """The rows that fit in `most` lines, the position clamped to them.

        The clamp is here rather than in `scroll` because how many fit is
        the view's answer and changes with the window: a dialog scrolled to
        the end of a short screen has to come back into view when the
        window is made taller, and only a draw knows that it has.
        """
        self.shown = max(1, most)
        self.top = max(0, min(self.top, len(self.rows) - self.shown))
        return self.rows[self.top:self.top + self.shown]


class Reference:
    """The standard library, searchable — what the `[ref]` button opens.

    **Built from `gestate.reference.entries_of`, not from `doc/ref/`.**  The
    generated markdown and this view are two renderings of one extraction,
    so a name cannot be in the page and missing from the editor; and a
    reader who has not run the generator still gets an answer, because the
    `.ges` files are the source either way.

    Headless, like everything else worth testing here: it holds a query, a
    selection and a filter, and answers with entries.  The view draws what
    `results` and `current` return and owns none of it.
    """

    def __init__(self, entries=None):
        #: Every entry, in library order, each tagged with its library.
        self.entries = entries if entries is not None else _library_entries()
        #: What has been typed.  Matched against the name first and the
        #: signature second — see `results`.
        self.query = ""
        #: Which result is selected, as an index into `results()`.
        self.at = 0
        #: The first result on screen, and the first line of the shown
        #: entry's prose: two panes, two scrolls.
        self.top = 0
        self.scroll = 0
        #: **Off by default**, which is the whole point of the marker: the
        #: vocabulary is what you want and the machinery is what you want
        #: only when you have met a name and cannot place it.
        self.internals = False

    # -- searching ----------------------------------------------------------

    def results(self) -> list:
        """The entries matching the query, best first.

        Ranked rather than filtered, because a person typing `sine` wants
        `sine` and `sine` above `bandpassSvf`'s prose that happens to
        mention a sine: an exact name, then a name that starts with the
        query, then a name that contains it, then the signature, then the
        prose.  Ties keep library order, which is the author's grouping.
        """
        query = self.query.strip().lower()
        found = []
        for entry in self.entries:
            if entry.internal and not self.internals:
                continue
            if not query:
                found.append((3, entry))
                continue
            name = entry.name.lower()
            if name == query:
                rank = 0
            elif name.startswith(query):
                rank = 1
            elif query in name:
                rank = 2
            elif query in entry.signature.lower():
                rank = 4
            elif any(query in line.lower() for line in entry.doc):
                rank = 5
            else:
                continue
            found.append((rank, entry))
        return [entry for _rank, entry in
                sorted(found, key=lambda pair: pair[0])]

    def current(self):
        """The selected entry, or `None` when nothing matched."""
        found = self.results()
        if not found:
            return None
        self.at = max(0, min(self.at, len(found) - 1))
        return found[self.at]

    # -- what the keys do ----------------------------------------------------

    def type_in(self, char: str) -> str:
        self.query += char
        self.at, self.scroll, self.top = 0, 0, 0
        return self.said()

    def backspace(self) -> str:
        self.query = self.query[:-1]
        self.at, self.scroll, self.top = 0, 0, 0
        return self.said()

    def clear(self) -> str:
        self.query = ""
        self.at, self.scroll, self.top = 0, 0, 0
        return self.said()

    def move(self, by: int) -> str:
        found = self.results()
        if not found:
            return ""
        self.at = max(0, min(len(found) - 1, self.at + by))
        self.scroll = 0
        return ""

    def toggle_internals(self) -> str:
        """The `[ ] show internals` switch.

        The selection is reset rather than kept: the list it indexed into
        has just changed length, and an index that survived would land on
        a different entry — which reads as the view jumping for no reason.
        """
        self.internals = not self.internals
        self.at, self.scroll, self.top = 0, 0, 0
        return f"internals {'shown' if self.internals else 'hidden'}"

    def said(self) -> str:
        found = self.results()
        if not found:
            return f"no name matches {self.query!r}"
        return f"{len(found)} match" + ("" if len(found) == 1 else "es")

    def lines(self) -> list:
        """`[(kind, text)]` for the selected entry — what the right pane
        draws, and what a test can read without a window."""
        entry = self.current()
        if entry is None:
            return [("prose", "nothing matches")]
        out = [("query", entry.signature)]
        if entry.alternatives[1:]:
            out += [("query", f"    {alt}") for alt in entry.alternatives[1:]]
        out.append(("prose", ""))
        out.append(("bank", f"{entry.library}  ·  {entry.section or 'top'}"
                            + ("  ·  internal" if entry.internal else "")))
        if entry.doc:
            out.append(("prose", ""))
            out += [("prose", line) for line in entry.doc]
        return out


def _library_entries() -> list:
    """Every library's entries, each tagged with the library it came from.

    Imported here rather than at module scope: `reference` reads six files
    off the disk, and the editor should not pay for that unless the button
    is pressed.
    """
    from .reference import LIBRARIES, entries_of, language_entries
    from pathlib import Path as _Path

    here = _Path(__file__).parent
    # **The language first**, because it is what a reader looking for
    # `wait` or `chan` is looking for, and because it is in none of the
    # files below — they are desugaring forms, not definitions, so
    # `entries_of` has nothing to find.  Searching the reference for the
    # most-used word in the language used to return nothing at all.
    out = list(language_entries())
    for name, title, _when in LIBRARIES:
        for entry in entries_of((here / name).read_text()):
            entry.library = title
            out.append(entry)
    return out


#: A parameter, as the text has it: `level = mkKnob 0.6`, at the left
#: margin, which is where a declaration a graph could reach is written.
#: `Pane.declared` is why this is a regular expression and not a front end.
_DECLARED = re.compile(r"^([A-Za-z_][\w']*)[ \t]*=[ \t]*mkKnob\b[ \t]*(.*?)"
                       r"[ \t]*$", re.M)

#: What `Pane.asked` holds while a `Tab` is out.  Not a name any program
#: could have, so a `?` and a `Tab` racing each other cannot answer into the
#: other's dialog.
_HOLE = "\0hole"


def _lone_hole(line: str, i: int) -> bool:
    """Is `line[i]` a `_` standing on its own — a hole rather than a name?

    `_x` and `x_` are identifiers and `_` is not, and the difference is
    what the neighbours are.
    """
    if not (0 <= i < len(line)) or line[i] != "_":
        return False
    before = line[i - 1] if i else " "
    after = line[i + 1] if i + 1 < len(line) else " "
    return not (before.isalnum() or before == "_") \
        and not (after.isalnum() or after == "_")


@dataclass
class Pane:
    """What a key means — the half worth testing, with no pygame in it.

    Holds the `Workbench`, the `Document` and the mode, and turns input
    into what it does.  Every method returns a short string naming what
    happened, which is what the status line shows and what a test asserts
    on: an action that reports nothing is one nobody can check.
    """

    bench: object
    document: Document
    mode: str = "text"
    #: `plain` never leaves text — the setting for someone who wants an
    #: ordinary editor and no modes at all.
    style: str = ""
    said: list = field(default_factory=list)

    @classmethod
    def open(cls, bench, style: str = "") -> "Pane":
        text = bench.source()
        return cls(bench=bench, document=Document(text), style=style,
                   saved=text)

    # -- what is playing ------------------------------------------------------

    def is_playing(self) -> bool:
        """The *transport*, not the audio thread.

        `Workbench.playing` is "the thread is alive", which is true from
        the moment it starts until it is stopped — so a button reading it
        never changed, whatever the transport was doing.
        """
        transport = getattr(self.bench, "transport", None)
        return bool(transport is not None and transport.playing)

    def position(self) -> str:
        """Where the transport has reached, as a person reads a clock."""
        transport = getattr(self.bench, "transport", None)
        if transport is None:
            return "--:--"
        seconds = transport.position / max(1, self.bench.rate)
        return f"{int(seconds) // 60}:{seconds % 60:05.2f}"

    # -- saving ---------------------------------------------------------------

    @property
    def dirty(self) -> bool:
        """Does the text differ from what is on disk?"""
        return self.document.text != self.saved

    def caption(self) -> str:
        return f"gestate — {self.bench.path.name}" + (" [+]" if self.dirty
                                                      else "")

    def save(self) -> str:
        """Write the file, whatever the instrument is doing.

        Separated from `apply` because they are two promises: this one is
        about the file and cannot fail for want of a running synth.

        **This is where a new file is created**, and the parent directory
        with it, so `gestate.audiopygame sketches/a.ges` works before
        `sketches` does.  Until then the program lives in `Workbench.
        pending` and nothing is on disk — a name typed by mistake leaves
        nothing behind.
        """
        self.bench.path.parent.mkdir(parents=True, exist_ok=True)
        self.bench.path.write_text(self.document.text)
        self.bench.pending = ""
        self.saved = self.document.text
        return f"saved {self.bench.path.name}"

    # -- undo -----------------------------------------------------------------

    def remember(self) -> None:
        self.history.append((self.document.rope, self.document.pos))
        del self.history[:-200]

    def undo(self) -> str:
        if not self.history:
            return "nothing to undo"
        rope, pos = self.history.pop()
        self.document.rope, self.document.pos = rope, pos
        self.document.mark, self.document.goal = None, None
        return "undone"

    # -- modes --------------------------------------------------------------

    #: How many lines a page is.  The view sets it, because only the view
    #: knows how tall the window is.
    page: int = 20
    #: Point size of the text.  Here rather than in the view because it is
    #: a *preference*, and the view is what draws it.
    size: int = 15
    #: `""` off, `"play"` playable, `"step"` playable and writing what it
    #: plays at the cursor.
    piano: str = ""
    #: The first row on screen, kept here so a click and the last draw
    #: agree about which line the pointer is on.
    top: int = 0
    #: Physical keys currently down, so a repeat can be told from a press.
    held_keys: set = field(default_factory=set)
    #: Is the instrument still being built?  The window opens before it —
    #: see `run` — so there is a stretch at the beginning of every session
    #: where there is a text and no sound, and one key has to know:
    #: `Ctrl-S` starts an instrument that never started, and must not start
    #: a second one on top of the first.
    starting: bool = False
    #: What `?` last asked about, and what it found — the dialog over the
    #: text, or `None` when there is none.
    asked: str = ""
    dialog: object = None
    #: Which sidebar row is where, so a click can reach the one control
    #: that lives there.
    rows: dict = field(default_factory=dict)
    #: The text as it last reached the file, for `[+]` in the caption.
    saved: str = ""
    #: `(rope, pos)` before each edit — free, because the rope is
    #: persistent and an old one costs nothing to keep.
    history: list = field(default_factory=list)
    _seen: object = None
    _facts: list = field(default_factory=list)
    _thinking: bool = False
    #: What was last copied.  The view hands the *system* clipboard in and
    #: out when it can; this is what works when it cannot, and is what a
    #: test can see.
    clipboard: str = ""
    #: The knob a drag is turning, or `""`.  A drag has to remember which
    #: control it started on: the pointer leaves the trough almost at once
    #: and the knob must go on following it, the way every slider does.
    turning: str = ""
    #: The note the *pointer* is holding on the drawn keyboard, or `None`.
    #: One, because a mouse has one finger — the typing keys are the way to
    #: play a chord and `Keyboard` already tracks those.
    pressed: object = None
    #: The library, searchable, or `None` until `[ref]` is first pressed.
    #: Built lazily: it reads six files off the disk, and a session that
    #: never asks should not pay for them.
    library: object = None
    #: `"canvas"` when the piano was opened over the canvas, and `""`
    #: otherwise — what `close_piano` reads to know where to go back to.
    #: The reference keeps `was` for the same reason; this is a second
    #: field rather than a shared one because the two can be open at once
    #: and a single slot would lose one of them.
    piano_over: str = ""
    #: The mode to go back to when the reference is closed.  A reference is
    #: something you open *over* what you were doing, so `Esc` has to
    #: return there rather than to a fixed mode.
    was: str = "command"
    #: **The search prompt** — what has been typed into it, or `None` when
    #: it is not open.  A *prompt* and not a mode: it is up for as long as
    #: you are typing a pattern and gone the moment you are not, which is
    #: too short a life to be worth a colour on the gutter.  It owns the
    #: keyboard while it is up, the way a dialog does.
    finding: str | None = None
    #: Where the cursor was when the prompt opened.  Searching moves the
    #: cursor *as you type*, so cancelling has to have somewhere to put it
    #: back — an editor that leaves you somewhere else after you changed
    #: your mind has lost your place for you.
    found_from: int = 0
    #: `(kind, row, text)` for each screen row of the last draw — see
    #: `laid_out`.  Written by the view, read by every click, because a
    #: diagnostic interleaved into the text moves every line below it and
    #: the two must not disagree about by how much.
    shown: list = field(default_factory=list)
    #: The last pattern committed with `Return`, which is what `n` and `N`
    #: repeat.  Kept after the prompt closes, and that is the whole point
    #: of it being separate from `finding`.
    pattern: str = ""
    #: The loop, in beats.  `loop_to` is `None` for "wherever the piece
    #: ends", which is the answer nine times in ten and the one nobody
    #: should have to measure — see `loop_span`.
    looping: bool = False
    loop_from: float = 0.0
    loop_to: object = None

    def escape(self) -> str:
        """Outward: text → command → canvas, and stop.

        One key and one direction, so there is never a question of which
        way `Esc` goes.
        """
        if self.style == PLAIN:
            return "plain: no modes"
        i = MODES.index(self.mode)
        self.mode = MODES[min(i + 1, len(MODES) - 1)]
        return f"mode: {self.mode}"

    def inward(self) -> str:
        """`Return`: canvas → command → text, and stop.

        The mirror of `Esc`, and the way *back*.  Without it the canvas is
        a room with a door in one wall: `Esc` stops at the outermost mode
        by design, so something has to be the other direction and `Return`
        is the key already in your hand.  In text mode it is a newline and
        never this.
        """
        if self.style == PLAIN:
            return "plain: no modes"
        i = MODES.index(self.mode)
        self.mode = MODES[max(i - 1, 0)]
        return f"mode: {self.mode}"

    # -- copying ------------------------------------------------------------

    def copy(self) -> str:
        text = self.document.selected()
        if text:
            self.clipboard = text
        return f"copied {len(text)}" if text else ""

    def cut(self) -> str:
        self.remember()
        text = self.document.cut_selection()
        if text:
            self.clipboard = text
        return f"cut {len(text)}" if text else ""

    def paste(self, text: str = "") -> str:
        text = text or self.clipboard
        if not text:
            return ""
        self.remember()
        self.document.insert(text)
        return f"pasted {len(text)}"

    # -- the transport --------------------------------------------------------

    def end_sample(self) -> int | None:
        """Where the piece ends, or `None` when the file has no piece.

        Read off the *schedule* — a program with no `score` has nothing
        that could be called an end, and a button that jumped somewhere
        arbitrary would be worse than one that is plainly unavailable.
        """
        schedule = getattr(self.bench, "schedule", None)
        if schedule is None:
            return None
        end = schedule.horizon()
        return end if end > 1 else None

    def to_start(self) -> str:
        if getattr(self.bench, "transport", None) is None:
            return ""
        self.bench.transport.seek(0)
        return "at the start"

    def to_end(self) -> str:
        end = self.end_sample()
        if end is None or getattr(self.bench, "transport", None) is None:
            return "this program has no piece to reach the end of"
        self.bench.transport.seek(end)
        return "at the end"

    # -- the loop -------------------------------------------------------------

    def loop_span(self) -> tuple:
        """`(from, to)` in beats — **the piece's own end when none is set**.

        A score knows how long it is, and `end_sample` already reads it off
        the schedule for `>`.  Asking someone to type the number a file
        could have told them is the kind of small tax that makes a loop a
        thing you set up rather than a thing you use, so the default is the
        whole piece and `[`/`]` move the points afterwards.

        A program with no score has no end to borrow, so it gets sixteen
        beats from the start — a bar of four, which is a guess, but a guess
        you can hear and then adjust rather than a refusal.
        """
        if self.loop_to is not None:
            return (self.loop_from, float(self.loop_to))
        end = self.end_sample()
        if end is None:
            return (self.loop_from, self.loop_from + 16.0)
        return (self.loop_from, self.bench.samples_to_beats(end))

    def set_loop(self) -> str:
        """Hand the current span to the transport, or say why not."""
        if getattr(self.bench, "transport", None) is None:
            self.looping = False
            return "nothing is playing to loop"
        start, end = self.loop_span()
        if end <= start:
            self.looping = False
            return "a loop must end after it starts"
        self.looping = True
        self.bench.set_loop(start, end)
        return f"looping {start:g}–{end:g}"

    def toggle_loop(self) -> str:
        """`o` — round and round, or not."""
        if self.looping:
            self.looping = False
            self.bench.clear_loop()
            return "loop off"
        return self.set_loop()

    def whole_piece(self) -> str:
        """`O` — forget the points and loop the piece, however long it is.

        The way *back* to the default, which a pair of adjustable points
        needs as much as it needs the points: having set `[` at beat 30 to
        hear one bar, the next thing you want is the whole thing again, and
        without this that means remembering what the whole thing was.
        """
        self.loop_from, self.loop_to = 0.0, None
        return self.set_loop()

    def loop_from_here(self) -> str:
        """`[` — the loop begins where the transport has reached."""
        self.loop_from = round(self.bench.position_in_beats(), 3)
        return self.set_loop() if self.looping \
            else f"loop from {self.loop_from:g}"

    def loop_to_here(self) -> str:
        """`]` — and ends there.  Sets it explicitly, so the piece's own
        end is no longer what is meant; `O` puts that back."""
        self.loop_to = round(self.bench.position_in_beats(), 3)
        return self.set_loop() if self.looping \
            else f"loop to {float(self.loop_to):g}"

    def loop_text(self) -> str:
        """What the toolbar says beside the clock, or nothing."""
        if not self.looping:
            return ""
        start, end = self.loop_span()
        return f"⟲ {start:g}–{end:g}"

    # -- the reference --------------------------------------------------------

    def open_reference(self) -> str:
        """`[ref]` — the standard library, over whatever you were doing.

        **A mode rather than a dialog**, because looking a name up is not
        one keystroke's worth of interruption: you type, you read, you
        change the query, and a popup that any key dismissed would be
        unusable for it.  `Esc` puts you back where you were.
        """
        if self.mode == "reference":
            return self.close_reference()
        if self.library is None:
            self.library = Reference()
        self.was = self.mode
        self.mode = "reference"
        return "reference — type to search, Esc to close"

    def close_reference(self) -> str:
        self.mode = self.was if self.was != "reference" else "command"
        return f"mode: {self.mode}"

    def reference_key(self, char: str, key: str = "") -> str:
        """A key while the reference is open.

        Printable characters are the *query*, which is why this is a mode:
        there is no other way for typing to mean searching without taking
        the letters away from somewhere they already meant something.
        """
        ref = self.library
        if key == "backspace":
            return ref.backspace()
        if key == "up":
            return ref.move(-1)
        if key == "down":
            return ref.move(1)
        if key == "pageup":
            return ref.move(-self.page)
        if key == "pagedown":
            return ref.move(self.page)
        # `Tab` toggles the internals, and is free here: there is no indent
        # in a search box and no hole to ask about.
        if key == "tab":
            return ref.toggle_internals()
        if char and char.isprintable():
            return ref.type_in(char)
        return ""

    def click_reference(self, x: int, y: int, layout: "Layout") -> str:
        """A click in the reference: the switch, or a name in the list."""
        if _inside(layout.internals_box, x, y):
            return self.library.toggle_internals()
        rx, ry, _rw, _rh = layout.ref_list
        row = (y - ry - 2) // max(1, layout.line_h)
        found = self.library.results()
        if 0 <= row < len(found):
            self.library.at = row
            self.library.scroll = 0
            return f"{found[row].name}"
        return ""

    def trouble_at(self) -> tuple:
        """`(banner, {line: message})` — the last error, *placed*.

        A message whose position is in the author's own file belongs
        against that line and is interleaved beneath it.  One that names a
        prelude, or names nowhere at all, cannot be: there is no line in
        this file to put it on.  Those become a **banner** at the top with
        the location left in, which is the honest version of "not here" —
        `audiospans.in_source` has already said `prelude line 873` rather
        than translating it into a negative number, and throwing that away
        would be disguising the one thing worth knowing.
        """
        import re

        text = getattr(self.bench, "trouble", "")
        if not text.strip():
            return "", {}
        name = re.escape(Path(getattr(self.bench, "path", "x")).name)
        # `prelude line 873:5` and `entry line 1:7` both contain `line N:C`,
        # so the author's own positions have to be matched to the exclusion
        # of them.  Getting this wrong is not a missed mark but a *wrong*
        # one: `entry line 8` put the note on line 8 of a two-line program.
        found = (re.search(rf"{name}:(\d+):\d+", text)
                 or re.search(r"(?<!prelude )(?<!entry )\bline (\d+):\d+",
                              text))
        if found is not None:
            return "", {int(found.group(1)): text.strip()}
        # **No position, so look for the name instead.**  `UnresolvedName`
        # and `InferError` carry none — measured, six of ten kinds of error
        # do not — and "Unknown global 'sinewave'" with no line is the most
        # common mistake there is reported the least usefully.  The name is
        # in the message, though, and an editor may do what a compiler
        # cannot: find where it is written.
        #
        # A guess, and it says so by being a *mention* rather than a claim
        # about a position: the first line that uses the name as a word.
        # When the name is not in the text at all — `Unknown global 'sound'`
        # in a program that never wrote one — nothing matches and it stays a
        # banner, which is the right answer to "where is the thing you did
        # not write".
        # **Only where the quoted thing is a *name*.**  Matching any quoted
        # word put a type error on line 1 of every program: `Type mismatch:
        # expected 'Float'` found the `Float` in `sound : Sig Float`, which
        # is a confident answer and the wrong one.  A wrong line is worse
        # than no line, so this is the four messages that quote something
        # the author wrote and nothing else.
        names = (r"(?:Unknown global|Unknown constructor|Unbound variable"
                 r"|Unknown type constructor):?\s*")
        quoted = (re.search(names + r"'([^']+)'", text)
                  or re.search(names + r"([A-Za-z_]\w*)", text))
        if quoted is not None:
            word = re.compile(rf"(?<![\w']){re.escape(quoted.group(1))}(?![\w'])")
            for row in range(self.document.rows):
                if word.search(self.document.line(row)):
                    return "", {row + 1: text.strip()}
        return text.strip(), {}

    def laid_out(self, most: int, cols: int) -> list:
        """What the view puts on screen, in order — `(kind, row, text)`.

        **The one place the interleaving is decided**, because two readers
        need the same answer: the draw, and the click that has to say which
        line the pointer was over.  A view that inserted rows only while
        drawing would put the cursor a line above where it was clicked for
        every diagnostic on screen.

        `kind` is `"line"` for a line of the program, `"note"` for a line
        of a diagnostic beneath the one it is about, and `"banner"` for an
        error that belongs to no line here.  A `note` and a `banner` carry
        the row they are *attached* to, so a click on one lands on the code
        it is talking about rather than nowhere.
        """
        banner, marks = self.trouble_at()
        out: list = []
        if banner:
            for line in _wrapped(banner, cols):
                out.append(("banner", self.top, line))
            out.append(("banner", self.top, ""))
        for row in range(self.top, self.document.rows):
            if len(out) >= most:
                break
            out.append(("line", row, self.document.line(row)))
            note = marks.get(row + 1)
            if note is not None:
                for line in _wrapped(note, cols - 6):
                    out.append(("note", row, "  " + line))
        return out[:most]

    def row_at(self, screen_row: int) -> int:
        """Which line of the program is `screen_row` of the last draw.

        Read back from what was drawn rather than recomputed, which is the
        arrangement `_aside` and `click_aside` already use: the alternative
        is two answers to "how many rows did the diagnostics take", and a
        click would land wherever the two disagreed.
        """
        shown = self.shown
        if not shown:
            return self.top + screen_row          # nothing drawn yet
        if screen_row < 0:
            return shown[0][1]
        if screen_row >= len(shown):
            return shown[-1][1] + (screen_row - len(shown) + 1)
        return shown[screen_row][1]

    def screen_row(self, row: int) -> int:
        """Where line `row` was drawn, as a screen row.  The inverse."""
        for i, (kind, at, _text) in enumerate(self.shown):
            if kind == "line" and at == row:
                return i
        return row - self.top

    # -- searching ------------------------------------------------------------
    #
    # `/` to open, type, `Return` to keep it, `Esc` to put the cursor back;
    # `n` and `N` for the next and the previous.  Vim's, because that is
    # what `hjkl` beside the arrows already promised, and a half-kept
    # promise about keys is worse than none.
    #
    # **No backward `?`.**  It is the one key of vim's search vocabulary
    # that is already spoken for here — `?` says what the name under the
    # cursor is, which is the more useful key in an editor for a language
    # you are still learning — and `N` reaches every match `?` would.

    def open_search(self) -> str:
        """`/` — start typing a pattern."""
        self.finding = ""
        self.found_from = self.document.pos
        return "/"

    def search_key(self, char: str, key: str = "") -> str:
        """A key while the prompt is up; it owns all of them.

        **Backspace on an empty pattern cancels**, which is where the
        prompt came from and so where deleting all of it should leave you.
        """
        if key == "escape":
            return self.close_search(keep=False)
        if key == "return":
            return self.close_search(keep=True)
        if key == "backspace":
            if not self.finding:
                return self.close_search(keep=False)
            self.finding = self.finding[:-1]
            return self.preview()
        if char and char.isprintable():
            self.finding = (self.finding or "") + char
            return self.preview()
        return f"/{self.finding}"

    def close_search(self, keep: bool) -> str:
        """Put the prompt away, keeping the pattern or the place."""
        pattern, self.finding = self.finding or "", None
        if not keep or not pattern:
            self.document.pos = min(self.found_from, len(self.document.text))
            self.document.drop_mark()
            return "search cancelled"
        self.pattern = pattern
        if self.seek(pattern, self.found_from) is None:
            return f"/{pattern}: no match"
        return f"/{pattern}  line {self.document.row + 1}"

    def preview(self) -> str:
        """Move to the first match as the pattern is typed.

        Searching from `found_from` and not from wherever the last
        keystroke landed: otherwise deleting a character searches forward
        from the match it just found, and backspacing walks away down the
        file instead of back to where it was.
        """
        if not self.finding:
            self.document.pos = min(self.found_from, len(self.document.text))
            return "/"
        at = self.seek(self.finding, self.found_from)
        if at is None:
            self.document.pos = min(self.found_from, len(self.document.text))
            return f"/{self.finding}   no match"
        self.document.pos = at
        self.document.drop_mark()
        return f"/{self.finding}"

    def find_next(self, by: int) -> str:
        """`n` and `N` — the next match, and the previous."""
        if not self.pattern:
            return "no search yet — `/` starts one"
        doc = self.document
        # Forward starts one past the cursor so `n` leaves the match it is
        # sitting on; backward starts *at* it, so `N` finds the one before.
        at = self.seek(self.pattern, doc.pos + (1 if by > 0 else 0),
                       backward=by < 0)
        if at is None:
            return f"/{self.pattern}: no match"
        doc.pos = at
        doc.drop_mark()
        return f"/{self.pattern}  line {doc.row + 1}"

    def seek(self, pattern: str, start: int, backward: bool = False):
        """Where the next match is, wrapping — or `None` if there is none.

        **Wrapping, and silently.**  A file is a loop when you are looking
        for something in it; stopping at the end to announce that it is the
        end is a message about the search rather than about the text.

        **Smart case**: a pattern with no capital in it ignores case, and
        one with a capital in it does not.  `svf` finds `lowpassSvf`, which
        is the search you actually type in a language whose names are
        camel case; `Svf` finds only the capitalised one.  Plain text, not
        a regular expression — `spec/` is full of `[:` and `⃝`, and a
        search box that treated those as syntax would be a trap.
        """
        if not pattern:
            return None
        text = self.document.text
        if pattern.islower():
            text, pattern = text.lower(), pattern.lower()
        if backward:
            at = text.rfind(pattern, 0, max(0, start))
            if at < 0:
                at = text.rfind(pattern)
        else:
            at = text.find(pattern, max(0, start))
            if at < 0:
                at = text.find(pattern)
        return at if at >= 0 else None

    def enter_command(self) -> str:
        self.mode = "command"
        self.piano = ""
        return "mode: command"

    def enter_text(self) -> str:
        self.mode = "text"
        self.piano = ""
        return "mode: text"

    # -- the piano ----------------------------------------------------------

    def open_piano(self, step: bool = False) -> str:
        """`p` plays; `P` plays *and writes what it played* at the cursor.

        Step mode shows the text with its cursor, because what it is for is
        entering notes into a piece — `Keyboard.press_key` already returns
        the note whether or not a bank took it, for exactly this.

        **Opened over the canvas, it stays over the canvas.**  A synth that
        draws is one you want to play *while watching it*, and sending the
        keyboard to the text would take away the thing you opened it for.
        There is deliberately no *key* for this in canvas mode — the
        letters are the canvas's own, and a mode that quietly took one back
        is the thing modes are complained about for — so the toolbar button
        is the way in, which is what a toolbar is.
        """
        # Step mode is for writing notes into the text, so it goes to the
        # text whatever it was opened from; there is nothing to type into
        # on a canvas.
        self.piano_over = "canvas" if (self.mode == "canvas"
                                       and not step) else ""
        self.mode = "piano"
        self.piano = "step" if step else "play"
        return f"mode: piano ({self.piano})"

    def close_piano(self) -> str:
        """Leave the piano, back to whatever it was opened over."""
        over, self.piano_over = self.piano_over, ""
        if over == "canvas":
            self.mode, self.piano = "canvas", ""
            return "mode: canvas"
        return self.enter_command()

    def piano_key(self, char: str, keysym: str = "") -> str:
        """A physical key, while the piano is open."""
        note = self.bench.keyboard.press_key(char, keysym or char)
        if note is None:
            return ""
        if self.piano == "step":
            self.remember()
            self.document.insert(f"{note} ")
        return f"note {note}"

    def piano_release(self, char: str, keysym: str = "") -> str:
        note = self.bench.keyboard.release_key(keysym or char, char)
        return "" if note is None else f"off {note}"

    # -- size ---------------------------------------------------------------

    def bigger(self) -> str:
        self.size = min(40, self.size + 1)
        return f"size {self.size}"

    def smaller(self) -> str:
        self.size = max(8, self.size - 1)
        return f"size {self.size}"

    # -- the document -------------------------------------------------------

    def typed(self, char: str) -> str:
        """A printable character, in text mode; a command otherwise."""
        if self.mode == "text":
            self.remember()
            self.document.insert(char)
            return ""
        if self.mode == "command":
            return self.command(char)
        return ""

    #: Cursor keys for command mode, where the letters are free.  Only
    #: there: in text mode `h` is an `h`, and an editor that took it away
    #: would be the thing people mean when they complain about modes.
    VIM = {"h": (0, -1), "l": (0, 1), "k": (-1, 0), "j": (1, 0)}

    def command(self, char: str) -> str:
        """Single keys, which is what a mode is *for*.

        Deliberately few, and none of them a letter you would reach for by
        accident: what modality buys is the transport and the canvas, not a
        second alphabet.
        """
        if char == "i":
            return self.enter_text()
        if char == " ":
            return self.toggle()
        if char == "s":
            return self.apply()
        if char == "p":
            return self.open_piano()
        if char == "P":
            return self.open_piano(step=True)
        if char == "?":
            return self.query()
        if char == "/":
            return self.open_search()
        if char == "n":
            return self.find_next(1)
        if char == "N":
            return self.find_next(-1)
        if char == "<":
            return self.to_start()
        if char == ">":
            return self.to_end()
        # `o` rather than `l`, which `hjkl` has already spent: what a
        # circle looks like is the next best thing to a mnemonic.
        if char == "o":
            return self.toggle_loop()
        if char == "O":
            return self.whole_piece()
        if char == "[":
            return self.loop_from_here()
        if char == "]":
            return self.loop_to_here()
        if char.lower() in self.VIM:
            rows, cols = self.VIM[char.lower()]
            # **Shift selects**, here as everywhere: `HJKL` is `hjkl` with
            # the mark left where it was.
            self.travel(rows, cols, select=char.isupper())
            return ""
        return f"command: {char!r} does nothing"

    # -- the instrument -----------------------------------------------------

    def apply(self, save: bool = True) -> str:
        """`Ctrl-S` saves *and* applies; `Ctrl-Return` applies only.

        The file is written here rather than left to `Workbench.apply`,
        which refuses when nothing is playing — a synth that failed to
        start is exactly when you most want your text on disk.

        **And when nothing is playing, `Ctrl-S` starts it.**  The editor
        opens on a file that will not compile (see `run`), which leaves it
        with no instrument at all; without this the only way back to sound
        would be to close the window you have just fixed the program in.
        An audition cannot do it — starting reads the *file*, and the whole
        point of `Ctrl-Return` is that the file has not changed.
        """
        if save:
            self.save()
        if self.starting:
            # The file is written either way — that is the promise `save`
            # makes — but a second start on top of the one in flight would
            # be two instruments racing for one sound card.
            return f"{'saved; ' if save else ''}still starting"
        if getattr(self.bench, "live", None) is None:
            if not save:
                return "nothing is playing — Ctrl-S starts it"
            try:
                # On this thread, and deliberately: a start is a few
                # hundred milliseconds of front end and it is what the key
                # was pressed for.  One held frame is the honest cost; a
                # worker would only hide it behind a window that lies
                # about being ready.
                self.bench.start()
            except Exception as exc:                    # noqa: BLE001
                return f"saved; could not start: {_first_line(exc, self.bench.path)}"
            return "saved and started"
        try:
            self.bench.apply(self.document.text, save=False)
        except Exception as exc:                        # noqa: BLE001
            return f"{'saved; ' if save else ''}not applied: {exc}"
        return "saved and applied" if save else "auditioning"

    def audition(self) -> str:
        return self.apply(save=False)

    def toggle(self) -> str:
        try:
            self.bench.toggle()
        except Exception as exc:                        # noqa: BLE001
            return f"transport: {exc}"
        return "playing" if getattr(self.bench, "playing", False) else "stopped"

    # -- the sidebar --------------------------------------------------------

    def inspect(self) -> list:
        """What the compiler knows about this text, per line.

        Three things a person wants while looking at a program and cannot
        get from the text: what each **knob** is worth right now, what type
        each **hole** would have to be filled with, and what the last
        attempt to build it **complained** about.  All three are per line,
        because a line is what you are looking at.

        Cached on the text, so looking twice is free.  **Synchronous**,
        and therefore not what the view calls: see `facts`.
        """
        text = self.document.text
        if self._seen != text:
            self._facts, self._seen = self._facts_for(text), text
        return sorted(self._live() + self._facts)

    def banks(self) -> list:
        """`(line, name, "2/4", takes_midi, listening)` per `voices` bank.

        What the `tkinter` view put in a row beside each declaration: how
        many of the bank's voices are sounding, and whether the keyboard is
        driving it.  The switch is *greyed* rather than absent when the
        program declares no `FromMIDI` for that payload — a switch you can
        throw that cannot do anything is worse than one you cannot.
        """
        out = []
        for bank in getattr(self.bench, "banks", []):
            name = bank["name"]
            held = len(self.bench.sounding_on(name))
            out.append((bank["line"], name, f"{held}/{bank['count']}",
                        self.bench.takes_midi(name),
                        self.bench.listening(name)))
        return sorted(out)

    def word(self) -> str:
        """The name under the cursor."""
        line = self.document.line(self.document.row)
        col = min(self.document.column, max(0, len(line) - 1))
        if not line or not (line[col].isalnum() or line[col] in "_'"):
            return ""
        start = col
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1
        stop = col
        while stop < len(line) and (line[stop].isalnum() or line[stop] == "_"):
            stop += 1
        return line[start:stop]

    def query(self) -> str:
        """`?` — what is this, and what did whoever wrote it say about it.

        The same answer `python -m gestate.typecheck --query --audio`
        gives, because it is the same two questions: the type from
        inference, and the comment block above the declaration that carries
        it.  It opens **over** the text and any key takes it away, because
        it is about the word you are looking at rather than about the
        program — nothing here is worth giving a corner of the window to
        permanently.

        Answered on a worker, like the sidebar: it is a whole front end,
        and a draw that waits for one is how a held key walks through the
        modes while the frame is stuck.
        """
        import threading

        name = self.word()
        if not name:
            return "nothing under the cursor"
        self.asked = name
        self.dialog = Dialog([("query", f"{name}"), ("prose", "  reading…")])
        threading.Thread(target=self._answer_into, args=(name,),
                         daemon=True).start()
        return f"? {name}"

    def _answer_into(self, name: str) -> None:
        try:
            answer = self.answer()
        except Exception as exc:                        # noqa: BLE001
            answer = [("query", name), ("prose", f"  {exc}")]
        if self.asked == name and self.dialog is not None:
            self.dialog = Dialog(answer)

    # -- what fits ----------------------------------------------------------

    def at_hole(self) -> bool:
        """Is the cursor on a `_`?  What decides whether `Tab` asks.

        Either side of it, because a hole is one character wide and the
        cursor is between two: having just typed `_` you are after it, and
        having arrived from the right you are on it.  A `_` with a letter
        beside it is part of a name and not a hole at all.
        """
        line = self.document.line(self.document.row)
        col = self.document.column
        return any(_lone_hole(line, i) for i in (col, col - 1))

    def fits(self) -> str:
        """`Tab` — what could stand in the hole the cursor is at.

        The same answer `python -m gestate.typecheck --fits TYPE --audio`
        gives, asked of the hole's **own** type rather than of one retyped
        into a command line: `--holes` already says what the type is, so
        the pair of them was one question with a copy in the middle.

        On a worker, like `?` and the sidebar, and for the same reason: it
        is a whole front end and a draw is sixteen milliseconds.  The list
        it opens **scrolls and stays** — forty names are not a thing you
        read before your finger comes off the key.
        """
        import threading

        row = self.document.row
        line = self.document.line(row)
        # Answered from the text before a thread is started: a line with no
        # `_` on it cannot have a hole, and spending a front end to say so
        # would make the one case where there is nothing to say the slowest.
        if not any(_lone_hole(line, i) for i in range(len(line))):
            return "no hole on this line"
        self.asked = _HOLE
        self.dialog = Dialog([("query", "what fits _"),
                              ("prose", "  reading…")])
        threading.Thread(target=self._fits_into,
                         args=(self.document.text, row, self.document.column),
                         daemon=True).start()
        return "? what fits here"

    def _fits_into(self, text: str, row: int, col: int) -> None:
        try:
            rows = self.what_fits(text, row, col)
        except Exception as exc:                        # noqa: BLE001
            rows = [("query", "what fits _"), ("prose", f"  {exc}")]
        if self.asked == _HOLE and self.dialog is not None:
            self.dialog = Dialog(rows, scrolls=True)

    def what_fits(self, text: str, row: int, col: int) -> list:
        """`[(kind, text)]` — the names that fit the hole on `row`.

        The hole is found the way `holes` finds all of them, and the one
        answered for is the nearest to `col`: a line may hold two, and the
        one you pressed `Tab` at is the one you meant.
        """
        from .audio import assemble
        from .audioperform import has_score
        from .audioscore import assemble_performance
        from .audiospans import prelude_lines
        from .expr import EHole
        from .infer import _all_exprs
        from .pipeline import _build_builtins, analyse
        from .show import show_type
        from .typecheck import fits_in_scope, needed

        source = (assemble_performance(text, "", self.bench.rate)
                  if has_score(text) else assemble(text, self.bench.rate))
        analysis = analyse(source)
        offset = prelude_lines(text)
        here = []
        for _name, _arity, lam, _sig in analysis.scs:
            for node in _all_exprs(lam):
                if isinstance(node, EHole) and node.span is not None \
                        and node.span.start.line + 1 - offset == row + 1:
                    here.append((abs(node.span.start.col - col), node))
        if not here:
            return [("query", "no hole on this line")]
        hole = min(here, key=lambda p: p[0])[1]
        if hole.type_ is None:
            return [("query", "that hole has no type yet")]
        wanted = show_type(hole.type_)
        found = fits_in_scope(hole.type_, analysis.program, analysis.types,
                              _build_builtins())
        if not found:
            return [("query", f"nothing in scope fits {wanted}")]
        return [("query", f"what fits {wanted}:")] + \
            [("prose", f"  {name} : {type_}{needed(depth)}")
             for depth, name, type_ in found]

    def dismiss(self) -> bool:
        """Any key takes the dialog away.  `True` if there was one."""
        if self.dialog is None:
            return False
        self.dialog, self.asked = None, ""
        return True

    def answer(self) -> list:
        """`[(kind, text)]` for the pinned query, or nothing."""
        if not self.asked:
            return []
        from .typecheck import _declared_at, _doc_above

        out = [("query", f"{self.asked} : {self._type_of(self.asked)}")]
        text = self.document.text
        line, kind = _declared_at(text, self.asked)
        if line:
            out.append(("query", f"  at line {line} ({kind})"))
            for prose in _doc_above(text, line)[:6]:
                out.append(("prose", f"  {prose}"))
        else:
            for label, prelude in self._preludes():
                line, kind = _declared_at(prelude, self.asked)
                if not line:
                    continue
                out.append(("query", f"  {label} line {line}"))
                for prose in _doc_above(prelude, line)[:6]:
                    out.append(("prose", f"  {prose}"))
                break
        return out

    def _preludes(self) -> tuple:
        from pathlib import Path as _Path

        here = _Path(__file__).parent
        return tuple((name, (here / name).read_text())
                     for name in ("signal.ges", "audio.ges", "synth.ges",
                                  "gui.ges"))

    def _type_of(self, name: str) -> str:
        """Its type, from the program as compiled — or `?`."""
        from .audio import assemble
        from .audioperform import has_score
        from .audioscore import assemble_performance
        from .pipeline import analyse
        from .show import show_type

        text = self.document.text
        try:
            source = (assemble_performance(text, "", self.bench.rate)
                      if has_score(text) else assemble(text, self.bench.rate))
            analysis = analyse(source)
        except Exception:                               # noqa: BLE001
            return "?"
        found = analysis.types.get(name)
        if found is not None:
            return show_type(found)
        info = analysis.program.cons.get(name)
        return show_type(info.type_) if info is not None else "?"

    def toggle_midi(self, name: str) -> str:
        """The checkbox: hand the bank to the keyboard, or take it back."""
        if not self.bench.takes_midi(name):
            return f"{name} has no `FromMIDI` to take a note through"
        self.bench.listen(name, not self.bench.listening(name))
        return f"{name}: {'midi' if self.bench.listening(name) else 'score'}"

    def _live(self) -> list:
        """The rows that are about **now** rather than about the text.

        A knob's value and how many of a bank's voices are sounding change
        while nothing is typed, so they cannot be cached on the text the way
        the compiler's answers are — and were: the sidebar read `lead 0/4`
        for as long as you did not touch the keyboard, which is precisely
        when you are watching it.  Cheap enough to read every frame: a
        dictionary lookup and the allocator's own count.
        """
        # A declared knob nothing has reached yet says so: it is a real
        # parameter and it is not turning anything, and a row that read the
        # same as a live one would be a promise the sound does not keep.
        rows = [(line, "knob", f"{name} = {value}"
                 + ("" if wired else "  (not wired)"))
                for line, name, value, wired in self.knobs()]
        rows += [(line, "bank",
                  f"{name} {held}" + ("  [x] midi" if listening else
                                      "  [ ] midi" if takes else "  ( ) midi"))
                 for line, name, held, takes, listening in self.banks()]
        # **A complaint is about *now*, not about the text.**  It used to be
        # computed with the holes, which are cached on the text — so a
        # message arriving without a keystroke behind it could not refresh
        # them, and `note_fault` had to reach in and null the cache to make
        # it happen.  It also had to *accumulate*, in a list nothing ever
        # emptied, so a fixed error sat in the sidebar until the editor was
        # closed.  Read from the build every frame instead: there is one
        # copy of it, `Workbench.trouble`, and it is cleared when an edit
        # lands.
        rows += [(line, "error", message) for line, message in self.errors()]
        return rows

    def _facts_for(self, text: str) -> list:
        """What the *compiler* says about a text.  Runs on either thread.

        Only the answers that a text decides, because this is the half that
        costs a front end and is therefore the half that is cached.  See
        `_live` for the other one.
        """
        return sorted((line, "hole", f"_ : {type_}")
                      for line, type_ in self.holes(text))

    def facts(self) -> tuple:
        """`(what is known, still reading?)` — for the view, off the frame.

        `inspect` is a whole front end, and running one inside a draw
        stalls the window for as long as it takes.  That is not merely
        slow: the keyboard goes on repeating into the queue meanwhile, and
        the events all arrive at once when the frame finally ends — which
        is how holding `Esc` through a slow draw walked past command mode
        and landed on the canvas.

        So it runs on a worker, and the sidebar shows what it knew until
        the answer arrives.  The worker is handed a *copy* of the text and
        touches nothing the main thread writes.

        **The live rows are read here, every time.**  They are about the
        instrument rather than the text, so caching them on the text would
        freeze them — see `_live`.
        """
        import threading

        text = self.document.text
        if self._seen == text:
            return sorted(self._live() + self._facts), False
        if not self._thinking:
            self._thinking = True
            threading.Thread(target=self._think, args=(text,),
                             daemon=True).start()
        return sorted(self._live() + self._facts), True

    def _think(self, text: str) -> None:
        try:
            facts = self._facts_for(text)
        except Exception:                               # noqa: BLE001
            facts = self._facts
        self._facts, self._seen = facts, text
        self._thinking = False

    def holes(self, text: str = "") -> list:
        """`(line, type)` for every `_` — what would have to go there.

        The same answer `python -m gestate.typecheck --holes --audio`
        gives, because it is the same walk: a hole takes the type its
        context demands, so reading it back is what says what belongs.
        """
        from .audio import assemble, has_scene
        from .audioperform import has_score
        from .audioscore import assemble_performance
        from .audiospans import _regions
        from .expr import EHole
        from .infer import _all_exprs
        from .pipeline import analyse
        from .show import show_type

        text = text or self.document.text
        if "_" not in text:
            return []
        try:
            source = (assemble_performance(text, "", self.bench.rate)
                      if has_score(text) else assemble(text, self.bench.rate))
            analysis = analyse(source)
        except Exception:                               # noqa: BLE001
            return []                    # a program that will not compile
        offset = _regions(text)[2] if True else 0
        out = []
        for _name, _arity, lam, _sig in analysis.scs:
            for node in _all_exprs(lam):
                if isinstance(node, EHole) and node.span is not None:
                    out.append((node.span.start.line + 1 - offset,
                                show_type(node.type_) if node.type_ is not None
                                else "?"))
        return sorted(out)

    def errors(self) -> list:
        """`(line, message)` from the last build that had something to say.

        **One line of it**, because this is the sidebar's row and the
        sidebar's row is one line wide; the whole of it is interleaved into
        the text by `laid_out`.  Line `0` means the message names nowhere in
        this file — a prelude, or no position at all — which the sidebar
        draws without a number.

        Derived from `Workbench.trouble` rather than remembered here.  Two
        copies of "what went wrong" is two answers to "has it been fixed",
        and the one that was remembered here never said yes.
        """
        banner, marks = self.trouble_at()
        if banner:
            return [(0, banner.splitlines()[0])]
        return [(line, text.splitlines()[0]) for line, text in marks.items()]

    # -- the canvas ---------------------------------------------------------

    def touch(self, kind: str, x: int, y: int) -> str:
        """A gesture, which only means anything on the canvas tab."""
        if self.mode != "canvas":
            return ""
        self.bench.touch(kind, x, y)
        return f"{kind} {x},{y}"

    def drag_to(self, x: int, y: int, layout: "Layout") -> str:
        """Extend the selection to the pointer, without moving the mark.

        The row is **clamped to a little past what is on screen**, so
        dragging beyond an edge takes the cursor just off it and the view
        follows — rather than jumping to whichever line the pointer would
        have been over had the document been drawn that far.  How far past
        is `_REACH`, and is the scroll speed: see there.
        """
        if self.mode not in ("text", "command", "piano"):
            return ""
        mark = self.document.mark
        rows = max(1, layout.inner[3] // layout.line_h)
        local_y = min(max(y - layout.inner[1], -_REACH * layout.line_h),
                      (rows - 1 + _REACH) * layout.line_h)
        self.place(x - layout.inner[0], local_y, layout, select=True)
        self.document.mark = mark if mark is not None else self.document.mark
        return ""

    def wheel(self, notches: int) -> str:
        """The mouse wheel: move the page, and take the cursor with it.

        **There is one scroll position here and the cursor decides it.**
        `_text` derives `top` from where the cursor is, on every frame and
        by design — which is what makes a click, a drag and the last draw
        agree about which line the pointer is on.  A view scrolled away
        from the cursor would be a second opinion about that, and the next
        frame would overrule it: the page would twitch back under the hand
        that moved it.

        So the wheel moves *both*, by the same lines.  The cursor keeps the
        row of the window it was on, the page moves under it, and every
        rule about where the view follows to is left alone.

        Every mode but the canvas, which is the program's own picture and
        has no lines to scroll — what a wheel means there is the program's
        question to answer, and `spec/substrate.md` leaves the event
        vocabulary to the programs that ask for it.
        """
        if self.mode == "canvas":
            return ""
        if self.mode == "reference":
            # The list, not the page: it is what a hand over this view is
            # reaching for, and the prose beside it scrolls with the
            # selection rather than on its own.
            return self.library.move(notches)
        by = notches * _WHEEL
        self.top = max(0, min(max(0, self.document.rows - 1), self.top + by))
        self.document.vertical(by)
        self.document.drop_mark()
        return ""

    def click_aside(self, y: int, layout: "Layout") -> str:
        """A click in the sidebar — the only thing there to press is a
        bank's MIDI switch, which is the one fact that is also a control.

        The row is counted from the top of the panel, which is how `_aside`
        records it: any other pair of answers is a switch that cannot be
        hit and says nothing about why.
        """
        row = (y - layout.aside[1] - 2) // max(1, layout.line_h)
        got = self.rows.get(row)
        if got is None:
            return ""
        line, kind, text = got
        if kind == "bank":
            return self.toggle_midi(text.split()[0])
        # **Every other row goes to the line it is about.**  It used to
        # return `""` for a knob and the message for an error, which is to
        # say that two thirds of a panel of facts about lines did nothing
        # when pressed — and did it silently, exactly as a miss does.  A
        # fact about line 30 is a thing you press to get to line 30.
        if line:
            self.document.go_to(line - 1, 0)
            self.document.drop_mark()
            return f"line {line}" + (f": {text}" if kind == "error" else "")
        return text if kind == "error" else ""

    def click(self, x: int, y: int, layout: "Layout", button: int = 1) -> str:
        """A press on the window, as what it does.

        The chrome is checked first and the mode's own area after, so a
        button is a button in every mode — which is the point of having a
        toolbar rather than a key nobody remembers.

        **Within the view it is content before text**, and in the order the
        draw stacks it: the keyboard is painted over the code, the knobs
        over the code, and the code is what is left.  Putting the cursor
        somewhere is the *fallback* rather than the rule, which is the
        whole of what was wrong before — everything placed by content fell
        through to it, so a knob was a label and a piano key was a picture.
        """
        if button == 3:
            # The second button means one thing, and only over a knob.
            return self.learn(self.knob_at(x, y, layout))
        for name, rect in layout.buttons.items():
            if _inside(rect, x, y):
                return self.button(name)
        if layout.sidebar and _inside(layout.aside, x, y):
            return self.click_aside(y, layout)
        if _inside(layout.inner, x, y):
            if self.mode == "reference":
                return self.click_reference(x, y, layout)
            if self.mode == "canvas":
                return self.touch("press", x - layout.inner[0],
                                  y - layout.inner[1])
            if self.mode == "piano":
                said = self.press_note(x, y, layout)
                if said:
                    return said
            name = self.knob_at(x, y, layout)
            if name:
                self.turning = name
                return self.turn(name, x, layout)
            if self.mode in ("text", "command", "piano"):
                return self.place(x - layout.inner[0], y - layout.inner[1],
                                  layout)
        return ""

    def button(self, name: str) -> str:
        return {
            # One button, which is the *state* rather than two commands:
            # what it shows is what pressing it does next.
            "transport": self.toggle,
            "to_start": self.to_start,
            "to_end": self.to_end,
            "loop": self.toggle_loop,
            "reference": self.open_reference,
            "piano": lambda: self.open_piano(),
            "step": lambda: self.open_piano(step=True),
            "bigger": self.bigger,
            "smaller": self.smaller,
        }.get(name, lambda: "")()

    def travel(self, rows: int, cols: int, select: bool = False) -> None:
        """Move the cursor, keeping or dropping the selection.

        One place, because a selection that behaved differently under the
        arrows and under `hjkl` would be two rules for one idea.  Without
        `select` the mark is dropped: a selection you moved away from is
        one you did not mean to keep.
        """
        doc = self.document
        if select and doc.mark is None:
            doc.mark = doc.pos
        if rows:
            doc.vertical(rows)
        else:
            doc.move(cols)
        if not select:
            doc.drop_mark()

    def place(self, x: int, y: int, layout: "Layout", select: bool = False
              ) -> str:
        """Put the cursor where the pointer is.

        A press drops the mark there, so the drag that may follow has
        something to select *from*; a drag moves the cursor and leaves it.
        """
        row = self.row_at(y // layout.line_h)
        self.document.go_to(row, max(0, (x - layout.margin) // layout.advance))
        if not select:
            self.document.mark = self.document.pos
        return ""

    def play(self) -> str:
        if not getattr(self.bench, "playing", False):
            self.bench.toggle()
        return "playing"

    def stop(self) -> str:
        if getattr(self.bench, "playing", False):
            self.bench.toggle()
        return "stopped"

    def picture(self) -> list:
        return self.bench.picture()

    def knobs(self) -> list:
        """`(line, name, value, wired)` per parameter — drawn, not placed.

        The `tkinter` view hangs a widget beside each declaration and asks
        the text widget where that line ended up.  Here the view owns the
        layout, so a knob is three numbers and a name, and where it goes is
        the same walk that drew the line.

        **A knob appears when it is declared, not when it is wired.**  The
        `Workbench`'s sites come out of the extracted *graph*, and a graph
        only contains what `sound` reaches — so `k = mkKnob 5` was invisible
        until something used it, which is exactly backwards from how a
        parameter gets written: you declare it, then you reach for it, and
        the thing that was meant to tell you it exists said nothing until
        you no longer needed telling.  `declared` reads the text instead,
        and `wired` says which kind each row is.
        """
        out, seen = [], set()
        for site in getattr(self.bench, "sites", []):
            if site.file != self.bench.path.name:
                continue
            seen.add(site.name)
            out.append((site.line, site.name, self.bench.value_of(site.name),
                        True))
        out += [(line, name, value, False)
                for line, name, value in self.declared()
                if name not in seen]
        return sorted(out)

    # -- turning one ----------------------------------------------------------

    def knob_at(self, x: int, y: int, layout: "Layout") -> str:
        """The knob under the pointer, or `""`.

        **Only a wired one**, which is the same rule the grey label states:
        an unwired knob has no channel behind it, so a trough you could
        drag would move a number the sound has never heard of.  The greyed
        row says the parameter exists; turning it has to wait for something
        to use it.
        """
        rows = layout.rows_on_screen()
        for line, name, _value, wired in self.knobs():
            row = line - 1 - layout.top
            if wired and 0 <= row < rows \
                    and _inside(layout.knob_rect(row), x, y):
                return name
        return ""

    def turn(self, name: str, x: int, layout: "Layout") -> str:
        """Set a knob from where the pointer is across its trough.

        **Absolute rather than relative**, which is what a trough means: a
        slider you click halfway along goes halfway, and the alternative —
        picking the value up where it happens to be — makes a control whose
        position tells you nothing until you have already moved it.

        The x is not clamped to the slot on the way in, only the fraction
        is: a drag runs off the end of a twenty-character trough almost
        immediately, and a knob that stopped following the pointer there
        would never reach 0 or 1.
        """
        low, high = self.bench.knob_range(name)
        rx, _ry, rw, _rh = layout.knob_rect(0)
        across = (x - rx - KNOB_PAD) / max(1, rw - 2 * KNOB_PAD)
        self.bench.set_value(name, low + min(1.0, max(0.0, across))
                             * (high - low))
        return f"{name} = {self.bench.value_of(name)}"

    def release_knob(self) -> str:
        self.turning = ""
        return ""

    def learn(self, name: str) -> str:
        """Right-click a knob: bind the next controller that moves to it.

        The same gesture the `tkinter` view has and the same toggle —
        right-click to arm, right-click again to change your mind — because
        `Workbench.learn` is where that decision already lives and a second
        answer to it would be a second answer.
        """
        if not name:
            return ""
        if getattr(self.bench, "midi", None) is None:
            return f"{name}: no MIDI to learn from (start with --midi)"
        return f"{name}: " + ("move a controller to bind it"
                              if self.bench.learn(name) else "learn cancelled")

    def binding(self, name: str) -> str:
        """`CC7`, `learning…`, or nothing — what to show in the trough."""
        try:
            return self.bench.binding_text(name)
        except Exception:                               # noqa: BLE001
            return ""

    # -- the drawn keyboard ---------------------------------------------------

    def note_at(self, x: int, y: int, layout: "Layout"):
        """The piano key under the pointer, or `None`.

        The *last* rectangle the pointer is inside, because `piano_keys`
        puts the black keys after the white ones they overlap — see there.
        """
        if self.mode != "piano":
            return None
        keyboard = self.bench.keyboard
        base = keyboard.MIDDLE_C + (keyboard.octave - 4) * 12
        found = None
        for note, rect in layout.piano_keys(base):
            if _inside(rect, x, y):
                found = note
        return found

    def press_note(self, x: int, y: int, layout: "Layout") -> str:
        """Play the key under the pointer, and glissando while it is held.

        A drag across the keyboard releases what it is leaving and presses
        what it arrives at, which is what a keyboard does under a finger —
        and is why the note being held is remembered rather than looked up
        again on the way out.
        """
        note = self.note_at(x, y, layout)
        if note is None or note == self.pressed:
            return ""
        self.release_note()
        self.pressed = note
        self.bench.keyboard.press(note)
        if self.piano == "step":
            self.remember()
            self.document.insert(f"{note} ")
        return f"note {note}"

    def release_note(self) -> str:
        if self.pressed is None:
            return ""
        note, self.pressed = self.pressed, None
        self.bench.keyboard.release(note)
        return f"off {note}"

    def transpose(self, octaves: int) -> str:
        """`<` and `>` in piano mode — the tracker keys for the octave.

        Only there: in command mode they are the transport's ends, and the
        piano is the only place a keyboard's octave means anything.  The
        drawn keyboard already reads `keyboard.octave` to decide what it is
        showing; until this there was nothing that could change it.
        """
        return f"octave {self.bench.keyboard.transpose(octaves)}"

    def declared(self) -> list:
        """`(line, name, value)` for every `name = mkKnob v` in the text.

        Read off the text rather than the graph, and deliberately: it costs
        a regular expression instead of a front end, so it can run in a
        draw, and it is still true of a program that will not compile —
        which is the state a half-written declaration is usually in.

        The value is the literal as written, because an unwired knob has no
        channel for the host to drive and `value_of` would answer with a
        default that belongs to nothing.  A knob written the long way —
        `x = 0.6 ::: mkSig (wait chan)`, as `twoknobs.ges` does — is not
        matched here: it appears once it is wired, like any other node.
        """
        out = []
        for match in _DECLARED.finditer(self.document.text):
            line = self.document.text.count("\n", 0, match.start()) + 1
            out.append((line, match.group(1), match.group(2)))
        return out


# ── The window ──────────────────────────────────────────────────────────────

#: How wide a knob's slot is, in characters of the current font.  Wide
#: enough for `cutoff 0.62   CC7` and no wider: it is drawn over the right
#: end of the code, and a control that covered the line it belongs to would
#: have solved one problem by making another.
KNOB_CELLS = 22

#: The gap between a knob's slot and the trough inside it, in pixels.  The
#: click reads a fraction across the *trough*, so this is subtracted at both
#: ends — a knob whose ends you cannot reach does not go to 0 or to 1.
KNOB_PAD = 3

#: The mode, as a colour you cannot fail to notice: a border all the way
#: round, thickening at the bottom to carry the status line.  A word in a
#: corner is what a long line writes over, and a mode you cannot see is the
#: thing this design is against.
BORDER = 5

_INK = (222, 222, 214)
_PAPER = {"text": (24, 24, 28), "command": (28, 26, 20),
          "canvas": (16, 20, 24), "piano": (20, 18, 26),
          "reference": (18, 22, 26)}
_EDGE = {"text": (70, 90, 140), "command": (170, 140, 60),
         "canvas": (60, 140, 110), "piano": (150, 90, 150),
         "reference": (90, 130, 170)}


def _legible_on(colour) -> tuple:
    """Ink that can be read on `colour` — the status line sits *in* the
    border, so which one it is depends on the mode."""
    r, g, b = colour
    return (16, 16, 20) if (r * 299 + g * 587 + b * 114) / 1000 > 140 \
        else (245, 245, 240)


def _inside(rect, x: int, y: int) -> bool:
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh


@dataclass
class Layout:
    """Where everything is, as numbers.

    A dataclass of rectangles rather than drawing code, so what a click
    *hits* can be tested without opening a window — the same split the rest
    of this file makes.  The view builds one per frame from the window it
    actually has, which is what makes the window resizable: nothing here
    remembers a size.
    """

    width: int
    height: int
    line_h: int
    advance: int
    #: The first row on screen.  Passed *in* from the pane, because a
    #: layout is rebuilt every frame and a scroll position kept on one
    #: would be zero again before the next click could read it — which is
    #: exactly why a drag put the cursor somewhere else.
    top: int = 0
    #: Where the text begins, past the line numbers.
    margin: int = 56

    @property
    def toolbar(self) -> tuple:
        return (0, 0, self.width, self.line_h + 2 * BORDER)

    @property
    def status(self) -> tuple:
        bar = self.line_h + 2 * BORDER
        return (0, self.height - bar, self.width, bar)

    #: Command mode puts a sidebar on the right; every other mode has the
    #: whole width.  It is a *mode's* furniture rather than a panel you
    #: toggle, so there is nothing to remember about whether it is there.
    sidebar: int = 0

    @property
    def inner(self) -> tuple:
        bar = self.line_h + 2 * BORDER
        return (BORDER, bar, self.width - 2 * BORDER - self.sidebar,
                self.height - bar - bar - BORDER)

    @property
    def aside(self) -> tuple:
        bar = self.line_h + 2 * BORDER
        return (self.width - BORDER - self.sidebar, bar, self.sidebar,
                self.height - bar - bar - BORDER)

    @property
    def piano(self) -> tuple:
        """The keyboard, along the bottom of the view."""
        x, y, w, h = self.inner
        keys = min(h // 2, 8 * self.line_h)
        return (x, y + h - keys, w, keys)

    @property
    def buttons(self) -> dict:
        """The chrome, by name.

        The transport is on the left where a transport goes, the piano on
        the right where the user asked for it, and the two size keys sit in
        the status bar beside them — visible in the modes that have text to
        size and absent from the ones that do not.
        """
        bar = self.line_h + 2 * BORDER
        b = bar - 2 * BORDER + 4
        out = {
            "to_start": (BORDER, BORDER, b, b),
            "transport": (BORDER + b + 4, BORDER, b, b),
            "to_end": (BORDER + 2 * (b + 4), BORDER, b, b),
            "loop": (BORDER + 3 * (b + 4), BORDER, b, b),
            "piano": (self.width - BORDER - 2 * b - 4, BORDER, b, b),
            "step": (self.width - BORDER - b, BORDER, b, b),
            # Top right, and wider than a chip because it carries a word:
            # a reference is not a thing you find by guessing an icon.
            "reference": (self.width - BORDER - 2 * b - 12 - 5 * self.advance
                          - 8, BORDER, 5 * self.advance + 8, b),
        }
        sy = self.height - bar + BORDER - 2
        out["smaller"] = (self.width - BORDER - 2 * b - 4, sy, b, b)
        out["bigger"] = (self.width - BORDER - b, sy, b, b)
        return out

    # -- what the *content* puts somewhere -----------------------------------
    #
    # **The chrome is not the only thing you can press.**  A knob belongs
    # beside the line that declares it and a piano key belongs where it is
    # drawn, so neither can be a fixed rectangle in `buttons` — and for a
    # while that meant neither could be pressed at all: `click` knew three
    # regions, and anything placed by content fell through to "put the text
    # cursor here".  The knobs were labels and the drawn keyboard was a
    # picture of a keyboard.
    #
    # These two are the missing vocabulary, and they are **arithmetic** for
    # the same reason everything else here is: the draw calls them to find
    # out where to paint and the click calls them to find out what was hit,
    # so the two cannot drift apart, and a test can check either without
    # opening a window.

    def knob_rect(self, screen_row: int) -> tuple:
        """The slot for a knob on the `screen_row`-th visible line.

        A **fixed** width rather than one fitted to the label: a trough
        that grew and shrank with the number written in it would be a
        target that moved while you were aiming at it, and a knob you are
        turning is exactly when the number is changing.
        """
        x, y, w, h = self.inner
        wide = max(8 * self.advance, min(KNOB_CELLS * self.advance, w // 2))
        return (x + w - wide - 8, y + screen_row * self.line_h, wide,
                self.line_h)

    def rows_on_screen(self) -> int:
        return max(0, self.inner[3] // self.line_h)

    #: How much of the width the list of names gets.  A third: a name is
    #: short and its prose is not, and the pane that is read needs the room.
    REF_LIST = 0.32

    @property
    def ref_search(self) -> tuple:
        x, y, w, _h = self.inner
        return (x + 8, y + 6, w - 16, self.line_h)

    @property
    def internals_box(self) -> tuple:
        """The `[ ] show internals` switch, under the search box."""
        x, y, w, _h = self.inner
        return (x + 8, y + 10 + self.line_h, 17 * self.advance,
                self.line_h)

    @property
    def ref_list(self) -> tuple:
        x, y, w, h = self.inner
        top = y + 14 + 2 * self.line_h
        return (x + 8, top, int(w * self.REF_LIST) - 8,
                max(self.line_h, y + h - top - 6))

    @property
    def ref_body(self) -> tuple:
        x, y, w, h = self.inner
        top = y + 14 + 2 * self.line_h
        left = x + int(w * self.REF_LIST) + 8
        return (left, top, x + w - left - 8,
                max(self.line_h, y + h - top - 6))

    def piano_keys(self, base: int) -> list:
        """`[(note, rect)]` for the drawn keyboard, whites then blacks.

        **Blacks last, and that ordering is the hit test.**  A black key
        overlaps the two whites it sits between, so whoever reads this list
        takes the *last* rectangle the pointer is inside and gets the key
        that is drawn on top — which is the one under your finger.
        """
        x0, y0, w, h = self.piano
        whites = _OCTAVES * len(_WHITE)
        kw = max(6, w // whites)
        out = [(base + (i // 7) * 12 + _WHITE[i % 7],
                (x0 + i * kw + 1, y0 + 1, kw - 2, h - 2))
               for i in range(whites)]
        out += [(base + octave * 12 + semitone,
                 (x0 + (octave * 7 + after) * kw + kw - kw // 3, y0 + 1,
                  2 * (kw // 3), int(h * 0.62)))
                for octave in range(_OCTAVES)
                for semitone, after in _BLACK]
        return out


#: The white keys of an octave, and which semitone each is.
_WHITE = (0, 2, 4, 5, 7, 9, 11)
#: The black ones, and the white key each sits after.
_BLACK = ((1, 0), (3, 1), (6, 3), (8, 4), (10, 5))
#: How many octaves the drawn keyboard shows.
_OCTAVES = 3


def run(path, style: str = "", size=(960, 640), fps: int = 60,
        rate: int = 0, block: int = 0, midi: bool = False,
        midi_port=None) -> int:
    """Open the window and play the file until it is closed."""
    try:
        import pygame
    except ImportError:                                 # noqa: BLE001
        raise SystemExit(
            "the pygame view needs pygame (`pip install pygame`); "
            "`python -m gestate.audioeditor` is the tkinter one")

    from .audioeditor import Workbench
    from .audiolive import DEFAULT_BLOCK, DEFAULT_RATE

    bench = Workbench(Path(path), rate=rate or DEFAULT_RATE,
                      block=block or DEFAULT_BLOCK,
                      midi=midi, midi_port=midi_port)
    pane = Pane.open(bench, style=style)

    pygame.init()
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    # **SDL2 resizes the window itself, and asking it to again is a fight.**
    # `VIDEORESIZE` used to be answered with a second `set_mode`, which is
    # what pygame 1 required and what pygame 2 turns into a *request* to the
    # window manager — issued while the pointer is still dragging the edge.
    # The manager is then told a size by the drag and another by us, some
    # tens of times a second, and the window flickers between them and
    # snaps out from under the hand.  Here the event is a notification: the
    # surface has already changed, and `get_surface` is where the new one
    # is.  Kept for pygame 1, where it is not a request but the only way.
    resizes = pygame.version.vernum[0] < 2

    # **The window first, and the instrument behind it.**  Starting one is a
    # front end, an extraction and a `clang` — four seconds for a synth and
    # nearly *thirty* for `quartet.ges`, whose score is four voices long —
    # and it used to happen before there was anything on the screen.  From
    # the outside that is not a slow editor, it is one that does not open:
    # no window, no message, nothing to look at but the shell.
    #
    # So the text is on the screen in the time it takes to make a window,
    # and the sound arrives when it arrives.  Everything the chrome asks of
    # a `Workbench` already answers for one that has not started — there
    # was no instrument at all when a file would not compile — which is why
    # this is a thread rather than a state machine.
    status = f"starting {Path(path).name}…"
    _starting(pane, bench, path)

    # Holding a key repeats it, which every editor does and none says.
    pygame.key.set_repeat(300, 30)
    try:
        pygame.scrap.init()
    except Exception:                                   # noqa: BLE001
        pass                        # the pane's own buffer still works
    clock = pygame.time.Clock()
    font, drawn_at, shown = None, None, ""

    try:
        while True:
            if drawn_at != pane.size:
                font = pygame.font.SysFont("monospace", pane.size)
                drawn_at = pane.size
            # Re-read rather than remembered: under SDL2 the surface behind
            # a resized window is a new one, and drawing into the old one
            # paints somewhere nobody is looking.
            screen = pygame.display.get_surface() or screen
            width, height = screen.get_size()
            layout = Layout(width, height, font.get_linesize(),
                            max(1, font.size("m")[0]), top=pane.top,
                            sidebar=(width // 3 if pane.mode == "command"
                                     else 0))
            pane.page = max(1, layout.inner[3] // layout.line_h - 1)
            caption = pane.caption()
            if caption != shown:
                pygame.display.set_caption(caption)
                shown = caption

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 0
                if event.type == pygame.VIDEORESIZE:
                    if resizes:                 # pygame 1 — see above
                        screen = pygame.display.set_mode(event.size,
                                                         pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    said = _key(pane, event, pygame)
                    if said == "quit":
                        return 0
                    status = said or status
                elif event.type == pygame.KEYUP:
                    pane.held_keys.discard(event.key)
                    if pane.mode == "piano":
                        pane.piano_release(event.unicode,
                                           pygame.key.name(event.key))
                elif event.type == pygame.MOUSEWHEEL:
                    # The wheel belongs to the dialog while there is one:
                    # a list that scrolls is a list a hand expects to
                    # scroll this way, whatever the keyboard also does.
                    # Otherwise it is the page — every mode but the canvas.
                    if pane.dialog is not None and pane.dialog.scrolls:
                        pane.dialog.scroll(-3 * event.y)
                    else:
                        pane.wheel(-event.y)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if pane.dialog is not None:
                        # In the way, exactly as a key is — and swallowed
                        # for the same reason, so a click that dismissed it
                        # does not also move the cursor under it.
                        pane.dismiss()
                    elif event.button in (1, 3):
                        status = pane.click(*event.pos, layout,
                                            button=event.button) or status
                elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                    # **What the press started is what the drag continues**,
                    # whatever it is now over: a knob followed only while
                    # the pointer stayed inside a twenty-character trough
                    # would never reach either end, and a finger sliding off
                    # a piano key would leave the note sounding.
                    if pane.turning:
                        status = pane.turn(pane.turning, event.pos[0],
                                           layout) or status
                    elif pane.pressed is not None:
                        pane.press_note(*event.pos, layout)
                    elif pane.mode == "canvas":
                        status = pane.touch(
                            "drag", event.pos[0] - layout.inner[0],
                            event.pos[1] - layout.inner[1]) or status
                    elif _inside(layout.inner, *event.pos):
                        pane.drag_to(*event.pos, layout)
                elif event.type == pygame.MOUSEBUTTONUP:
                    pane.release_knob()
                    status = pane.release_note() or status
                    if pane.mode == "canvas":
                        status = pane.touch(
                            "release", event.pos[0] - layout.inner[0],
                            event.pos[1] - layout.inner[1]) or status

            # What the instrument is doing, into the canvas — once a frame,
            # which is as often as anyone can see it.
            bench.observe()

            while bench.messages:
                status = bench.messages.pop(0)

            _draw(screen, pygame, font, layout, pane, status)
            pygame.display.flip()
            clock.tick(fps)
    finally:
        bench.stop()
        pygame.quit()


def _starting(pane: Pane, bench, path) -> None:
    """Start the instrument on a worker, and say so when it cannot.

    The failure goes into `Workbench.messages` rather than being returned,
    because that is the queue the loop already drains into the status line
    — a start that failed is the same kind of news as a rebuild that
    failed, and reads the same way.

    **A file that will not compile is the ordinary reason to open an
    editor**, and this used to be a traceback instead of a window: the one
    program that could have shown you where the error was refused to start
    because of it.  `Ctrl-S` starts it once the text compiles — see
    `Pane.apply`.
    """
    import threading

    def begin():
        try:
            bench.start()
        except Exception as exc:                        # noqa: BLE001
            bench.say(f"could not start: {_first_line(exc, path)}")
        finally:
            pane.starting = False

    pane.starting = True
    threading.Thread(target=begin, daemon=True).start()


def _first_line(error, path=None) -> str:
    """A compiler error is a paragraph and a status bar is a line.

    Through `audiospans.cli_error`, so the line numbers are the ones the
    author's file has: everything is compiled with the preludes in front,
    and an error reported at line 872 of a nine-line synth is not wrong so
    much as answering a question nobody asked.
    """
    from .audiospans import cli_error

    return cli_error(error, path).strip().splitlines()[0]


def _fresh(pane: Pane, key) -> bool:
    """Is this a *new* press of `key`, or the keyboard repeating itself?

    **By what is held rather than by the clock.**  Key repeat is what an
    editor wants for typing and exactly what it does not want for `Esc`,
    and pygame does not mark which events are repeats.  A time-based guess
    fails the moment a frame is slow: the repeats queue up, arrive together
    long after the press, and the first of them looks new — which is
    precisely how holding `Esc` through a slow draw landed on the canvas.

    A key is not new until it has been *released*, and `KEYUP` says so.
    """
    if key in pane.held_keys:
        return False
    pane.held_keys.add(key)
    return True


def _key(pane: Pane, event, pygame) -> str:
    """One key press, as what it means."""
    if pane.dialog is not None:
        # The dialog was in the way, so this key was for it.  Swallowed
        # rather than acted on: a popup that also typed the letter that
        # closed it is one you learn to close by pressing something
        # harmless, which is a rule nobody should have to learn.
        return _in_dialog(pane, event, pygame)

    # **The search prompt owns every key while it is up**, and this is
    # above `Esc` and above `Ctrl` on purpose: `Esc` is how you cancel a
    # search, so it has to arrive here rather than being spent closing a
    # mode you are still in.
    if pane.finding is not None:
        return pane.search_key(event.unicode, pygame.key.name(event.key))

    ctrl = event.mod & pygame.KMOD_CTRL
    if ctrl and event.key == pygame.K_q:
        return "quit"
    if ctrl and event.key == pygame.K_s:
        return pane.apply()
    if ctrl and event.key == pygame.K_RETURN:
        return pane.audition()
    if ctrl and event.key in (pygame.K_PLUS, pygame.K_EQUALS):
        return pane.bigger()
    if ctrl and event.key == pygame.K_MINUS:
        return pane.smaller()
    if ctrl and event.key == pygame.K_c:
        said = pane.copy()
        _to_clipboard(pygame, pane.clipboard)
        return said
    if ctrl and event.key == pygame.K_x:
        said = pane.cut()
        _to_clipboard(pygame, pane.clipboard)
        return said
    if ctrl and event.key == pygame.K_v:
        return pane.paste(_from_clipboard(pygame))
    if ctrl and event.key == pygame.K_z:
        return pane.undo()

    if event.key == pygame.K_ESCAPE:
        if not _fresh(pane, event.key):
            return ""
        if pane.mode == "reference":
            return pane.close_reference()
        if pane.mode == "piano":
            return pane.close_piano()
        return pane.escape()

    # **The reference owns every remaining key**, because typing into it is
    # searching.  Above the mode branches below and below `Ctrl` and `Esc`,
    # which keep meaning what they mean everywhere.
    if pane.mode == "reference":
        return pane.reference_key(event.unicode, pygame.key.name(event.key))

    if pane.mode == "piano":
        # **`Return` lands in text**, because what a piano is next to is
        # the thing you were writing — and in step mode you are already
        # looking at the cursor.  Over the canvas it is next to the
        # *canvas*, so there it goes back to that instead.
        if event.key == pygame.K_RETURN:
            return (pane.close_piano() if pane.piano_over == "canvas"
                    else pane.enter_text())
        # The octave, before the note: `<` and `>` are the tracker keys for
        # it, and they are shifted because the unshifted `,` and `.` are
        # notes in the lower row — the same forced choice the `tkinter`
        # keyboard makes, so one habit works in both views.
        if event.unicode in ("<", ">"):
            return pane.transpose(-1 if event.unicode == "<" else 1)
        if event.unicode:
            return pane.piano_key(event.unicode, pygame.key.name(event.key))
        return ""

    if event.key == pygame.K_RETURN and pane.mode != "text":
        # Inward.  `Esc` stops at the canvas by design, so this is the way
        # back — and in text mode it is a newline, which is why the test is
        # on the mode rather than on the key.
        if not _fresh(pane, event.key):
            return ""
        return pane.inward()

    # **`Tab` asks where there is something to ask about.**  At a `_` it is
    # what fits the hole; anywhere else in text mode it is the indent it has
    # always been, because an editor that took `Tab` away from typing would
    # be trading a key you press a hundred times a day for one you press
    # when you are stuck.  Command mode has no indent to lose, so there it
    # always asks — and says so when the line holds no hole.
    if event.key == pygame.K_TAB and pane.mode in ("text", "command") \
            and (pane.mode == "command" or pane.at_hole()):
        # By what is *held*, like `Esc`: a repeat here would start a front
        # end per repeat, and a held key would spend the rest of the second
        # opening the answer and closing it again.
        if not _fresh(pane, event.key):
            return ""
        return pane.fits()

    # **Moving around works in text and command alike.**  A mode that took
    # the arrow keys away would be teaching a lesson nobody asked for; what
    # command mode adds is `hjkl` beside them, not instead of them.
    if pane.mode in ("text", "command") and _navigate(pane, event, pygame):
        return ""

    if pane.mode == "text":
        doc = pane.document
        if event.key == pygame.K_BACKSPACE:
            pane.remember()
            doc.backspace()
        elif event.key == pygame.K_DELETE:
            pane.remember()
            doc.delete()
        elif event.key == pygame.K_RETURN:
            pane.remember()
            doc.insert("\n")
        elif event.key == pygame.K_TAB:
            pane.remember()
            doc.insert("    ")
        elif event.unicode and event.unicode.isprintable():
            return pane.typed(event.unicode)
        return ""
    if event.unicode:
        return pane.typed(event.unicode)
    return ""


def _in_dialog(pane: Pane, event, pygame) -> str:
    """A key while a dialog is up — it belongs to the dialog.

    A dialog that **scrolls** keeps the four keys that scroll it and goes
    away on anything else, which is the same bargain as `?`'s "any key" with
    four exceptions carved out of it: a list you cannot reach the bottom of
    without closing it is a list that was never shown to you.
    """
    dialog = pane.dialog
    if dialog.scrolls:
        by = {pygame.K_UP: -1, pygame.K_DOWN: 1,
              pygame.K_PAGEUP: -dialog.shown, pygame.K_PAGEDOWN: dialog.shown,
              }.get(event.key)
        if by is not None:
            return dialog.scroll(by)
        if event.key == pygame.K_HOME:
            return dialog.scroll(-len(dialog))
        if event.key == pygame.K_END:
            return dialog.scroll(len(dialog))
    pane.dismiss()
    _fresh(pane, event.key)
    return ""


def _navigate(pane: Pane, event, pygame) -> bool:
    """The cursor keys, in whichever mode has a cursor.  `True` if handled.

    A plain move drops the mark, because a selection you moved away from is
    one you did not mean to keep.
    """
    doc = pane.document
    moves = {
        pygame.K_LEFT: lambda: doc.move(-1),
        pygame.K_RIGHT: lambda: doc.move(1),
        pygame.K_UP: lambda: doc.vertical(-1),
        pygame.K_DOWN: lambda: doc.vertical(1),
        pygame.K_HOME: doc.home,
        pygame.K_END: doc.end,
        pygame.K_PAGEUP: lambda: doc.vertical(-pane.page),
        pygame.K_PAGEDOWN: lambda: doc.vertical(pane.page),
    }
    move = moves.get(event.key)
    if move is None:
        return False
    # **Shift selects**, which is the rule everywhere else and is why it is
    # here rather than in each of the eight.
    select = bool(event.mod & pygame.KMOD_SHIFT)
    if select and doc.mark is None:
        doc.mark = doc.pos
    move()
    if not select:
        doc.drop_mark()
    return True


def _to_clipboard(pygame, text: str) -> None:
    """The system clipboard when it works, and never a failure if not.

    `scrap` needs a display and is not there on every platform; the pane's
    own buffer is what makes copy and paste work regardless, and the system
    one is a bonus rather than a dependency.
    """
    if not text:
        return
    try:
        pygame.scrap.put_text(text)
    except Exception:                                   # noqa: BLE001
        pass


def _from_clipboard(pygame) -> str:
    try:
        return pygame.scrap.get_text() or ""
    except Exception:                                   # noqa: BLE001
        return ""


def _draw(screen, pygame, font, layout: Layout, pane: Pane,
          status: str) -> None:
    """The window: a toolbar, a bordered view, and a status line.

    Everything in the view is drawn **clipped to the inner rectangle**, so
    a long line stops at the border instead of running over the one thing
    that says which mode you are in.
    """
    mode = pane.mode
    edge, paper = _EDGE[mode], _PAPER[mode]
    ink = _legible_on(edge)

    screen.fill(edge)
    screen.fill(paper, layout.inner)
    if layout.sidebar:
        screen.fill((paper[0] + 8, paper[1] + 8, paper[2] + 10), layout.aside)
    _toolbar(screen, pygame, font, layout, pane, ink)

    screen.set_clip(layout.inner)
    if mode == "reference":
        _reference(screen, pygame, font, layout, pane, edge, paper)
    elif mode == "canvas" or pane.piano_over == "canvas":
        # The piano opened over the canvas keeps the canvas behind it: a
        # synth that draws is one you want to play *while watching it*.
        _canvas(screen, pygame, layout, pane)
        if mode == "piano":
            _piano(screen, pygame, layout, pane, edge)
    else:
        _text(screen, pygame, font, layout, pane, edge, paper)
        if mode == "piano":
            _piano(screen, pygame, layout, pane, edge)
    if layout.sidebar:
        _aside(screen, pygame, font, layout, pane, edge)
    screen.set_clip(None)

    if pane.dialog is not None:
        _dialog(screen, pygame, font, layout, pane, edge, paper)

    # **The bar is one line wide and says so.**  This used to hand the
    # message to `font.render` whole and at whatever length it happened to
    # be: a long type error ran off the right edge of the window, and a
    # multi-line one drew a box where the break belonged.  The text was on
    # the screen and could not be read, which is the same as not being
    # there.  The bar is a *summary* now; the error itself is interleaved
    # into the text beside the line it is about — see `Pane.laid_out`.
    cols = max(12, (layout.width - 2 * BORDER - 8) // max(1, layout.advance))
    screen.blit(font.render(_elided(f"[{mode}]  {status}", cols), True, ink),
                (BORDER + 4, layout.status[1] + BORDER))
    if mode in ("text", "command"):
        for name, glyph in (("smaller", "-"), ("bigger", "+")):
            _chip(screen, pygame, font, layout.buttons[name], glyph, ink, edge)


#: The transport is drawn in **black**: the toolbar is the mode's colour,
#: and a control that changed shade with the mode would read as a different
#: control.  Grey is the same statement for one that cannot be pressed.
_KEYCAP = (16, 16, 20)
_DISABLED = (120, 120, 128)


def _toolbar(screen, pygame, font, layout: Layout, pane: Pane, ink) -> None:
    """Transport on the left, position beside it, piano on the right.

    The same places in every mode: a toolbar that came and went would be
    one more thing to learn.
    """
    playing = pane.is_playing()
    ends = pane.end_sample() is not None

    x, y, w, h = layout.buttons["to_start"]
    pygame.draw.rect(screen, _KEYCAP, (x + 3, y + 3, 2, h - 6))
    pygame.draw.polygon(screen, _KEYCAP,
                        [(x + w - 3, y + 3), (x + w - 3, y + h - 3),
                         (x + 6, y + h // 2)])

    # **One button, showing the state rather than the command.**  What it
    # shows is what pressing it does next: a stop square while it plays, a
    # play triangle while it does not.
    x, y, w, h = layout.buttons["transport"]
    if playing:
        pygame.draw.rect(screen, _KEYCAP, (x + 4, y + 4, w - 8, h - 8))
    else:
        pygame.draw.polygon(screen, _KEYCAP,
                            [(x + 4, y + 3), (x + 4, y + h - 3),
                             (x + w - 3, y + h // 2)])

    # Grey when the file has no piece: there is nothing that could be
    # called an end, and a button that jumped somewhere arbitrary would be
    # worse than one plainly unavailable.
    x, y, w, h = layout.buttons["to_end"]
    colour = _KEYCAP if ends else _DISABLED
    pygame.draw.polygon(screen, colour, [(x + 3, y + 3), (x + 3, y + h - 3),
                                         (x + w - 6, y + h // 2)])
    pygame.draw.rect(screen, colour, (x + w - 5, y + 3, 2, h - 6))

    # **Round and round**: a bracket with a play triangle inside it, filled
    # while it is on.  Grey when there is neither a piece to take an end
    # from nor a point anyone has set — the same statement `to_end` makes,
    # for the same reason.
    x, y, w, h = layout.buttons["loop"]
    colour = _KEYCAP if (ends or pane.loop_to is not None) else _DISABLED
    pygame.draw.rect(screen, colour, (x + 2, y + 4, w - 4, h - 8),
                     0 if pane.looping else 2)
    pygame.draw.polygon(screen, _EDGE[pane.mode] if pane.looping else colour,
                        [(x + w // 2 - 3, y + h // 2 - 4),
                         (x + w // 2 - 3, y + h // 2 + 4),
                         (x + w // 2 + 4, y + h // 2)])

    # Where it has reached, always — a transport with no clock beside it is
    # a transport you have to guess at, and the loop's span beside it when
    # there is one: a transport that silently refuses to leave a section is
    # worse than no loop.
    clock = font.render(f"{pane.position()}  {pane.loop_text()}".rstrip(),
                        True, _KEYCAP)
    screen.blit(clock, (layout.buttons["loop"][0]
                        + layout.buttons["loop"][2] + 10, y))

    # **A word, not an icon.**  A reference is the one control a person
    # goes looking for without knowing it exists, and no glyph says
    # "everything in the standard library".
    _chip(screen, pygame, font, layout.buttons["reference"], "ref",
          _KEYCAP, _EDGE[pane.mode], filled=pane.mode == "reference")

    for name, glyph in (("piano", "p"), ("step", "P")):
        on = pane.mode == "piano" and (
            pane.piano == ("step" if name == "step" else "play"))
        _chip(screen, pygame, font, layout.buttons[name], glyph,
              _KEYCAP, _EDGE[pane.mode], filled=on)


def _chip(screen, pygame, font, rect, glyph: str, ink, edge,
          filled: bool = False) -> None:
    x, y, w, h = rect
    pygame.draw.rect(screen, ink, rect, 0 if filled else 1)
    label = font.render(glyph, True, edge if filled else ink)
    screen.blit(label, (x + (w - label.get_width()) // 2,
                        y + (h - label.get_height()) // 2))


#: How close to an edge the cursor may come before the view follows it.
_MARGIN = 2

#: Lines to the notch, for the mouse wheel.  Three is what every other
#: editor moves and therefore what a hand expects.
_WHEEL = 3

#: How far past the drawn text a **drag** may reach, in lines.  Beyond the
#: edge the view follows the cursor, so this is the scroll *speed*: with the
#: pointer held outside, each mouse move carries the cursor `_MARGIN` lines
#: plus this one, and the view comes after it.  One line rather than a
#: handful — a drag that outran the eye would be no easier to aim than the
#: jump this replaced.
_REACH = 1

#: What each kind of fact is worth looking at in.
_FACT = {"knob": (200, 180, 90), "hole": (120, 190, 220),
         "error": (220, 110, 110), "bank": (150, 200, 150),
         "query": (220, 220, 210), "prose": (150, 150, 158)}


def _aside(screen, pygame, font, layout: Layout, pane: Pane, edge) -> None:
    """Knobs, holes and complaints — what the compiler knows, per line.

    In command mode only, which is the mode for looking at a program
    rather than typing into it.
    """
    x, y, w, h = layout.aside
    screen.set_clip(layout.aside)
    pygame.draw.rect(screen, edge, (x, y, 1, h))
    known, thinking = pane.facts()
    pane.rows = {}
    row = y + 2
    for i, (line, kind, text) in enumerate(known):
        if row > y + h - layout.line_h:
            break
        label = f"{line:4d} {text}" if line else f"     {text}"
        # **By the index drawn, which is what `click_aside` computes back.**
        # This recorded `row // line_h` — an *absolute* y — while the click
        # asked for the row within the panel, so the two agreed only when
        # the toolbar happened to be zero lines tall.  The bank switch was
        # therefore unclickable, silently: the lookup found nothing and a
        # row that is not a bank does nothing, which is also what a miss
        # looks like.  Cleared each frame so a row that has gone away
        # cannot be hit by what is drawn where it used to be.
        pane.rows[i] = (line, kind, text)
        screen.blit(font.render(label, True, _FACT[kind]), (x + 6, row))
        row += layout.line_h
    if thinking:
        screen.blit(font.render("  reading…", True, (110, 110, 118)),
                    (x + 6, row))
    elif row == y + 2:
        screen.blit(font.render("  nothing to say", True, (110, 110, 118)),
                    (x + 6, row))
    screen.set_clip(layout.inner)


def _wrapped(text: str, cols: int) -> list:
    """A paragraph as lines no wider than `cols`.

    Its own newlines are kept — a compiler error puts the offending source
    on a line of its own and breaking that apart would lose the shape of
    it — and only lines longer than the width are folded, indented so a
    continuation reads as one.
    """
    out: list = []
    for line in text.replace("\t", "    ").split("\n"):
        line = line.rstrip()
        if not line:
            out.append("")
            continue
        while len(line) > cols:
            cut = line.rfind(" ", 0, cols)
            if cut <= 0:
                cut = cols
            out.append(line[:cut].rstrip())
            line = "    " + line[cut:].lstrip()
        out.append(line)
    return out or [""]


def _elided(text: str, cols: int) -> str:
    """One line, at most `cols` wide, ending in an ellipsis if it was cut.

    **`font.render` does not know what a newline is.**  A message with one
    in it came out as a single line with a box where the break belonged,
    running past the edge of the window — so any further lines are marked
    with `⏎` rather than drawn.
    """
    first, _, rest = text.partition("\n")
    first = first.rstrip()
    if rest.strip():
        first += " ⏎"
    if cols > 1 and len(first) > cols:
        first = first[:cols - 1].rstrip() + "…"
    return first


def _dialog(screen, pygame, font, layout: Layout, pane: Pane, edge,
            paper) -> None:
    """A dialog's answer, over the text, until a key takes it away.

    Placed **near the cursor** rather than in the middle: it is about the
    word you are looking at, and a box in the centre of the screen makes
    you look away from it to read about it.

    **Never taller than the view**, which is what `Tab` needed: forty names
    would otherwise run off both ends of the window, and a box drawn past
    the border would write over the one thing that says which mode you are
    in.  What does not fit is scrolled to, and the box says which way.
    """
    dialog = pane.dialog
    x0, y0, w, h = layout.inner
    # The width of *every* row, not of the ones on screen, so the box does
    # not breathe in and out as the list is scrolled.
    width = max(font.size(text)[0] for _kind, text in dialog) + 24
    width = min(width, w - 16)
    most = max(1, (h - 24) // layout.line_h)
    rows = dialog.window(most)
    height = len(rows) * layout.line_h + 16

    at_row = pane.screen_row(pane.document.row)
    y = y0 + (at_row + 1) * layout.line_h + 4
    if y + height > y0 + h:                 # no room below: go above
        y = max(y0 + 4, y0 + at_row * layout.line_h - height - 4)
    y = min(y, y0 + h - height - 4)
    x = min(x0 + layout.margin, x0 + w - width - 8)

    pygame.draw.rect(screen, paper, (x, y, width, height))
    pygame.draw.rect(screen, edge, (x, y, width, height), 2)
    screen.set_clip((x, y, width, height))
    for i, (kind, text) in enumerate(rows):
        screen.blit(font.render(text, True, _FACT[kind]),
                    (x + 10, y + 8 + i * layout.line_h))
    # Which way there is more, on the row it is more of: an arrow at the
    # edge is what says a list did not end where the box did.
    for glyph, there, row in (("↑", dialog.top > 0, 0),
                              ("↓", dialog.top + len(rows) < len(dialog),
                               len(rows) - 1)):
        if there:
            mark = font.render(glyph, True, _FACT["query"])
            screen.blit(mark, (x + width - mark.get_width() - 6,
                               y + 8 + row * layout.line_h))
    screen.set_clip(None)


def _reference(screen, pygame, font, layout: Layout, pane: Pane, edge,
               paper) -> None:
    """The library: a search box, a switch, the names, and the one selected.

    Two panes, because the two questions are different.  "What is there"
    is a list you scan, and "what is this one" is prose you read; one pane
    doing both means either a list you cannot see the end of or prose in a
    column four words wide.
    """
    ref = pane.library
    found = ref.results()

    # The query, and what it caught.
    x, y, w, _h = layout.ref_search
    pygame.draw.rect(screen, _TROUGH, (x, y, w, layout.line_h))
    pygame.draw.rect(screen, edge, (x, y, w, layout.line_h), 1)
    typed = font.render(f"/{ref.query}", True, _INK)
    screen.blit(typed, (x + 6, y))
    # A caret, so an empty search box reads as one you can type into.
    pygame.draw.rect(screen, edge,
                     (x + 6 + typed.get_width() + 1, y + 2, 2,
                      layout.line_h - 4))
    count = font.render(f"{len(found)}", True, _FACT["prose"])
    screen.blit(count, (x + w - count.get_width() - 6, y))

    # `[x] show internals` — a switch, drawn as one, and hit as one.
    bx, by, bw, _bh = layout.internals_box
    pygame.draw.rect(screen, _TROUGH, (bx, by, bw, layout.line_h))
    pygame.draw.rect(screen, _DISABLED, (bx, by, bw, layout.line_h), 1)
    mark = "[x]" if ref.internals else "[ ]"
    screen.blit(font.render(f"{mark} show internals", True,
                            _ARMED if ref.internals else _FACT["prose"]),
                (bx + 4, by))

    # The names.  Scrolled to keep the selection on screen, by the same
    # rule the text view follows the cursor: only as far as it must.
    lx, ly, lw, lh = layout.ref_list
    rows = max(1, lh // layout.line_h)
    ref.top = max(0, min(ref.top, max(0, len(found) - rows)))
    if ref.at < ref.top:
        ref.top = ref.at
    elif ref.at >= ref.top + rows:
        ref.top = ref.at - rows + 1
    screen.set_clip(layout.ref_list)
    for i in range(ref.top, min(len(found), ref.top + rows)):
        entry = found[i]
        row = ly + (i - ref.top) * layout.line_h
        if i == ref.at:
            screen.fill(edge, (lx, row, lw, layout.line_h))
        # **Internals are a different colour**, which is the whole of what
        # the marker buys a reader: the list stays one list, and a name
        # that is not yours to call says so where you meet it.
        ink = (_ARMED if entry.internal else
               (_legible_on(edge) if i == ref.at else _INK))
        screen.blit(font.render(entry.name, True, ink), (lx + 4, row))
    screen.set_clip(layout.inner)
    pygame.draw.rect(screen, edge, layout.ref_list, 1)

    # The selected entry.
    bx, by, bw, bh = layout.ref_body
    screen.set_clip(layout.ref_body)
    wide = max(20, bw // max(1, layout.advance) - 2)
    row = by
    shown = 0
    for kind, text in ref.lines():
        for piece in (_wrap(text, wide) or [""]):
            if shown >= ref.scroll and row < by + bh - layout.line_h:
                screen.blit(font.render(piece, True, _FACT[kind]), (bx + 4,
                                                                    row))
                row += layout.line_h
            shown += 1
    screen.set_clip(layout.inner)


def _wrap(text: str, wide: int) -> list:
    """`text` broken to `wide` characters, on spaces where it can be."""
    if not text:
        return [""]
    out, line = [], ""
    for word in text.split(" "):
        if line and len(line) + 1 + len(word) > wide:
            out.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


def _canvas(screen, pygame, layout: Layout, pane: Pane) -> None:
    ox, oy = layout.inner[0], layout.inner[1]
    for shape in pane.picture():
        if shape[0] == "rect":
            _k, x, y, w, h, colour = shape
            pygame.draw.rect(screen, colour, (ox + x, oy + y, w, h))
        else:
            _k, x, y, r, colour = shape
            pygame.draw.circle(screen, colour, (ox + x, oy + y), r)


def _text(screen, pygame, font, layout: Layout, pane: Pane, edge,
          paper) -> None:
    doc = pane.document
    x0, y0, _w, h = layout.inner
    rows = h // layout.line_h
    # **Only far enough.**  Centring on the cursor scrolls on every move,
    # which under a drag reads as the page tearing past — what a reader
    # wants is for the view to stay still until the cursor reaches an edge
    # and then to follow it by a line.
    top = min(pane.top, max(0, doc.rows - rows))
    if doc.row < top + _MARGIN:
        top = max(0, doc.row - _MARGIN)
    elif doc.row >= top + rows - _MARGIN:
        top = min(max(0, doc.rows - rows), doc.row - rows + 1 + _MARGIN)
    pane.top = max(0, top)              # what the next click reads back
    top = pane.top
    knobs = {line: (name, value, wired)
             for line, name, value, wired in pane.knobs()}
    # Holes and complaints go **beside the line they are about**, the way
    # a knob does: a panel that only listed them would make you count.
    aside = {}
    for line, kind, text in pane.facts()[0]:
        if kind in ("hole", "error", "bank") and line:
            aside.setdefault(line, (kind, text))

    span = doc.selection()
    # **The error goes *between* the lines, not beside them.**  It used to
    # be drawn right-aligned on the line it was about, which is fine for
    # `hole` and `bank` — three words each — and hopeless for a compiler
    # error: a sentence right-aligned in a narrow window starts at a
    # negative x and is drawn straight through the code and the gutter.
    # Interleaved, it has the whole width and as many lines as it needs.
    cols = max(24, (layout.inner[2] - layout.margin - 16) // layout.advance)
    pane.shown = pane.laid_out(rows, cols)
    # **The diagnostics take room from the lines below them**, so the line
    # being typed on can be pushed off the bottom by an error above it —
    # which is the cursor disappearing while you are using it.  Scrolling
    # by what they cost brings it back, and the next frame is stable.
    if doc.row >= top and pane.screen_row(doc.row) >= rows:
        pane.top = min(doc.row, top + pane.screen_row(doc.row) - rows + 1)
        pane.shown = pane.laid_out(rows, cols)
    for i, (kind, at, text) in enumerate(pane.shown):
        y = y0 + i * layout.line_h
        if kind != "line":
            screen.blit(font.render(text, True, _FACT["error"]),
                        (x0 + layout.margin, y))
            continue
        if span is not None:
            # The selected part of *this* line, in its own coordinates.
            begin = doc.rope.rowpos(at)
            lo = max(span[0] - begin, 0)
            hi = min(span[1] - begin, len(text))
            if lo < hi:
                left = font.size(text[:lo])[0]
                wide = font.size(text[lo:hi])[0]
                screen.fill(edge, (x0 + layout.margin + left, y, wide,
                                   layout.line_h))
        screen.blit(font.render(f"{at + 1:4d} ", True, (90, 90, 100)),
                    (x0 + 4, y))
        screen.blit(font.render(text, True, _INK), (x0 + layout.margin, y))
        mark = aside.get(at + 1)
        if mark is not None and mark[0] != "error":
            label = font.render(mark[1], True, _FACT[mark[0]])
            spot = (x0 + layout.inner[2] - label.get_width() - 8, y)
            screen.fill(paper, (spot[0] - 4, y, label.get_width() + 8,
                                layout.line_h))
            screen.blit(label, spot)
        knob = knobs.get(at + 1)
        if knob is not None and mark is None:
            _knob(screen, pygame, font, layout.knob_rect(i), pane,
                  knob, edge, paper)
    cy = y0 + pane.screen_row(doc.row) * layout.line_h
    cx = x0 + layout.margin + font.size(doc.line(doc.row)[:doc.column])[0]
    pygame.draw.rect(screen, edge, (cx, cy, 2, layout.line_h))


#: The trough a knob is drawn in and the fill inside it, and the ink of one
#: armed for MIDI learn.
#:
#: **Fixed rather than the mode's colour**, which is the same argument
#: `_KEYCAP` makes about the transport: a control that changed shade with
#: the mode would read as a different control.  It is also the only way the
#: fill stays legible under `_INK` in every mode — command mode's edge is a
#: light gold, and pale text on it is a value you have to lean in to read.
#:
#: Armed is a *colour* rather than a word alone, because the word is four
#: characters at the far end of a line and the state it names lasts until
#: you move something.
_TROUGH = (52, 52, 60)
_FILL = (72, 96, 128)
_ARMED = (210, 175, 80)


def _knob(screen, pygame, font, rect, pane: Pane, knob, edge, paper) -> None:
    """A knob: a trough, a fill, its name and what it is bound to.

    **The trough is the point.**  This was a right-aligned label — a name
    and a number beside the line that declares the parameter — and a label
    is what it looked like: nothing about it said that the number could be
    changed, and nothing in the view could change it.  A slot with a fill
    in it says *control* before it is read, which is the whole difference
    between a readout and an instrument.

    Drawn from `Layout.knob_rect`, which is also what `Pane.knob_at` hit
    tests, so where this paints and where a click lands are one arithmetic.
    """
    name, value, wired = knob
    x, y, w, h = rect
    bound = pane.binding(name) if wired else ""
    armed = bound == "learning…"
    ink = _ARMED if armed else (_FILL if wired else _DISABLED)

    # The code behind it first: a trough over a half-drawn identifier reads
    # as neither.
    screen.fill(paper, (x - 4, y, w + 8, h))
    pygame.draw.rect(screen, _TROUGH, rect)
    if wired:
        low, high = pane.bench.knob_range(name)
        across = min(1.0, max(0.0, (float(value) - low)
                              / max(1e-9, float(high) - low)))
        pygame.draw.rect(screen, ink, (x + KNOB_PAD, y + 2,
                                       int((w - 2 * KNOB_PAD) * across),
                                       h - 4))
    pygame.draw.rect(screen, ink, rect, 1)

    shown = f"{value:.2f}" if isinstance(value, float) else f"{value}"
    label = font.render(f"{name} {shown}", True, _INK if wired else _DISABLED)
    screen.blit(label, (x + KNOB_PAD + 2, y))
    # What a controller has been bound to, at the far end — the one fact
    # about a knob that is not in the file and not in the sound.
    if bound:
        mark = font.render(bound, True, _ARMED if armed else _INK)
        screen.blit(mark, (x + w - mark.get_width() - KNOB_PAD - 2, y))


def _piano(screen, pygame, layout: Layout, pane: Pane, edge) -> None:
    """The keyboard, along the bottom, with what is sounding lit.

    The same layout the `tkinter` view drew and the same one
    `Keyboard.LOWER`/`UPPER` type: two rows of the typing keyboard are two
    octaves, so the shape under your fingers is the shape on the screen.

    **Drawn from `Layout.piano_keys`, which is also the hit test.**  It was
    drawn from its own copy of the arithmetic and hit tested by nothing at
    all — clicking a key put the text cursor somewhere and made no sound,
    because the keyboard was inside the text area and the text area is what
    a click fell through to.
    """
    x0, y0, w, h = layout.piano
    keyboard = pane.bench.keyboard
    held = keyboard.sounding()
    base = keyboard.MIDDLE_C + (keyboard.octave - 4) * 12

    pygame.draw.rect(screen, (12, 12, 14), (x0, y0, w, h))
    keys = layout.piano_keys(base)
    whites = _OCTAVES * len(_WHITE)
    for note, rect in keys[:whites]:
        pygame.draw.rect(screen, (90, 200, 130) if note in held else
                         (230, 230, 222), rect)
    for note, rect in keys[whites:]:
        pygame.draw.rect(screen, (90, 200, 130) if note in held else
                         (20, 20, 24), rect)
    pygame.draw.rect(screen, edge, (x0, y0, w, h), 1)


def main(argv=None) -> int:
    import argparse
    import sys

    from .audiomidi import MidiError, describe_ports, resolve_port

    ap = argparse.ArgumentParser(
        prog="python -m gestate.audiopygame",
        description="Edit a synth and its canvas in one window.")
    # `file` is optional only so `--midi-ls` can be asked on its own: being
    # made to name a program before being told what devices exist is the
    # wrong way round, and the answer does not depend on the program.
    ap.add_argument("file", nargs="?")
    ap.add_argument("--plain", action="store_true",
                    help="start in text and never leave it — no modes")
    ap.add_argument("--midi", nargs="?", const="", default=None,
                    metavar="PORT",
                    help="open a MIDI input — an index from --midi-ls, part "
                         "of a name, or nothing for the first; right-click a "
                         "knob to bind a controller to it")
    ap.add_argument("--midi-ls", action="store_true",
                    help="list the MIDI inputs on this machine and stop")
    ap.add_argument("--rate", type=int, default=0)
    ap.add_argument("--block", type=int, default=0)
    args = ap.parse_args(argv)

    if args.midi_ls:
        print(describe_ports())
        return 0
    if args.file is None:
        ap.error("a file to edit is required (or --midi-ls on its own)")
    # A name that is not there yet is how an editor is asked to start a new
    # file, not an error — see `audioeditor.is_new`.  Nothing is written
    # until the first save.
    from .audioeditor import is_new

    if is_new(args.file):
        print(f"gestate: {args.file} is new — nothing is written until you "
              f"save", file=sys.stderr)
    try:
        port = resolve_port(args.midi)
    except MidiError as exc:
        # Not a traceback: "there is no MIDI input 3" with the list under it
        # is the whole answer, and a stack of frames above it is noise
        # between the question and it.
        raise SystemExit(str(exc))
    return run(args.file, style=PLAIN if args.plain else "",
               rate=args.rate, block=args.block,
               midi=args.midi is not None, midi_port=port)


if __name__ == "__main__":
    import sys

    sys.exit(main())
