"""The editor — `spec/workbench.md`, running.

    python -m gestate.workbench examples/audio/twoknobs.ges

Three pieces, one direction of dependency: `Workbench` is the model and
imports no toolkit, `Session` turns a gesture into a transition and a
sentence, and `shell/editor` owns the window, the rope and the loop.
This module is the wire between them and nothing else — a poll, a
description out, gestures in.

**Ctrl-K opens the command list**, which is the whole of the interface:
there is one mode, you are typing, and everything else has a name you
can read.

When something feels slow, `GESTATE_EDITOR_TIME=1` makes the window
report where a frame goes and — the number that matters — **key to
pixels**, from the event that changed something to the `present` that
showed it. Guessing about lag across two runtimes is how an afternoon
disappears; the report says which side to look at.

A slow *save* is the other clock, and a different one:
`GESTATE_BUILD_TIME=1` says where a rebuild's seconds went — the front
end, `clang`, the canvas, the score (`gestate/buildtime.py`).
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

from .session import Session, act, furniture


class Window:
    """`Session`'s view port, over the editor's ABI.

    **Two directions and neither is a call.**  Things the window did
    arrive as gestures; things it should do leave as orders, obeyed on
    its next frame. Undo, the zoom and the caret are the window's own
    state and live on the window's thread, so nothing here reaches in.

    What it *does* keep is a mirror of four numbers — which zoom rung,
    how many there are, and how deep undo and redo go — because a
    command has to answer *"undone"* or *"nothing to undo"* the instant
    it runs and cannot wait a frame to find out which. The window
    volunteers them whenever they move.
    """

    def __init__(self, editor):
        self.editor = editor
        #: Which of the two the window is pointed at.
        self.showing = "source"
        #: A file the model has asked to open, until the loop takes it.
        self.wanted = None
        self.zoom_at = 0
        self.zoom_rungs = 1
        self.undos = 0
        self.redos = 0
        #: Whether the text is what was last written.
        self.saved = True
        #: Whether a selection exists, and whether the clipboard holds
        #: anything — what `copy` and `paste` answer from.
        self.sel = False
        self.clip = False
        #: The rows on screen — mirrored from the window, like the undo
        #: counts and for the same reason: colouring needs to know what
        #: is visible and must not reach across a thread to ask.
        self.top = 0
        self.rows = 40
        #: `None` until the document has been read once — see
        #: `lines`, where the difference is load-bearing.
        self._lines: list | None = None
        #: The text those lines came from, kept so the model can be
        #: asked about it without a second copy crossing the ABI.
        #: **`.text` is a copy of the document** and the poll runs five
        #: hundred times a second; comparing two strings already in hand
        #: is a `memcmp`, and fetching one is not.
        self._held: str = ""
        #: Whether the document moved since anybody asked — read and
        #: cleared by the loop, which is what turns typing into an
        #: audition (`audioeditor.Workbench.typed`).
        self.moved = False

    def text(self) -> str:
        return self.editor.text

    def lines(self) -> list:
        """The document's lines, copied only when it has moved.

        **`changed()` is the whole polling protocol** — an atomic read
        and a comparison — and `.text` is a copy of the document, so
        this is the difference between one copy per keystroke and one
        per poll, which at five hundred polls a second is the difference
        between an editor and a fan.
        """
        # **`None` and empty are different, and that was the bug.**
        # `changed()` answers *has it moved since I last asked*, which on
        # a freshly opened file is `False` — the text arrived before
        # anyone asked.  Filling only on a change therefore left the
        # cache empty until the first keystroke, so nothing was painted
        # and the file was drawn in plain ink: colouring that appeared
        # only once you typed, which reads as colouring that does not
        # work.
        if self._lines is None or self.editor.changed():
            # **One copy, three readers.**  The lines are for painting,
            # `_held` is what the model is asked about (`behind`) and
            # what an automatic audition is built from — all from the
            # same fetch, because `changed()` is consumed here and a
            # second caller asking it would get `False` and be wrong.
            got = self.editor.text
            self._held = got
            self._lines = got.splitlines()
            self.moved = True
        return self._lines

    def held(self) -> str:
        """The text the last read saw, without reading again."""
        return self._held

    def visible(self) -> list:
        """`(line number, text)` for the rows on screen, 1-based.

        Only these are painted: colouring a million-line file to draw
        fifty rows would make the rope decorative, which is the same
        argument `view.rs` opens with.
        """
        lines = self.lines()
        top = max(0, self.top)
        return [(n + 1, lines[n])
                for n in range(top, min(len(lines), top + max(1, self.rows)))]

    def close(self) -> None:
        self.editor.request_close()

    def note_state(self, zoom: int, rungs: int,
                   undos: int, redos: int, saved: bool = True,
                   top: int = 0, rows: int = 40,
                   sel: bool = False, clip: bool = False) -> None:
        """The window saying where its own state stands.

        `sel` and `clip` are what let `copy` and `paste` answer
        honestly the instant they run — "nothing selected" and
        "nothing to paste" are the mirror's to say, exactly as
        "nothing to undo" is.
        """
        self.zoom_at, self.zoom_rungs = zoom, rungs
        self.undos, self.redos = undos, redos
        self.saved = saved
        self.top, self.rows = top, rows
        self.sel, self.clip = sel, clip

    def mark_saved(self) -> bool:
        """This text is what is on disk now.

        The window keeps the saved *root* and compares against it, so
        undoing back to what you saved clears the mark — which a flag
        set by `edited` could never do, and a version counter could not
        either: both say the document has *moved*, and moving twice and
        arriving back is not modified.
        """
        self.editor.order("saved")
        self.saved = True
        return True

    def undo(self) -> bool:
        if self.undos <= 0:
            return False
        # **Counted here rather than waited for.**  The order is obeyed
        # a frame from now and the window will say so; answering from
        # the mirror keeps the sentence honest and immediate, and the
        # count is corrected by the window either way.
        self.undos -= 1
        self.redos += 1
        self.editor.order("undo")
        return True

    def redo(self) -> bool:
        if self.redos <= 0:
            return False
        self.redos -= 1
        self.undos += 1
        self.editor.order("redo")
        return True

    def find(self, pattern: str, back: bool = False) -> int:
        """The next line a pattern is on, counting from one, or -1.

        **Searched here, where the text already is.**  The window would
        have to answer across a thread to be asked, and the model holds
        a copy of the document anyway — so the search is a fact the
        model can establish, and only moving the caret is an order.

        **From the caret, wrapping** — which is what makes running it
        again mean *next* rather than *the same one for ever*.  A search
        that always started at line one would find the first match, and
        then find it again, and there would be no way to reach the
        second.
        """
        if not pattern:
            return -1
        text = self.text()
        lines = text.splitlines()
        here = text[:self.editor.pos].count("\n")      # 0-based
        if back:
            order = (list(range(here - 1, -1, -1))
                     + list(range(len(lines) - 1, here - 1, -1)))
        else:
            order = list(range(here + 1, len(lines))) + list(range(here + 1))
        for i in order:
            if pattern in lines[i]:
                self.goto(i + 1)
                return i + 1
        return -1

    def goto(self, line: int) -> bool:
        if line < 1 or line > len(self.text().splitlines()) + 1:
            return False
        self.editor.order(f"goto\t{int(line)}")
        return True

    def col(self, col: int) -> bool:
        """Put the caret at a column of the line it is already on.

        **Its own order, not a field on `goto`.**  A jump names a line
        and says nothing about columns; `complete` has just written
        into the middle of one and wants the hole it made.  Two
        motions, two verbs — a trailing optional field would be one
        verb meaning two things depending on how many words it was
        given, which is how a wire stops being readable.
        """
        self.editor.order(f"col\t{max(0, int(col))}")
        return True

    def zoom(self, by: int) -> bool:
        """Step the ladder, or say it is already at the end of it."""
        at = self.zoom_at + by
        if at < 0 or at >= self.zoom_rungs:
            return False
        self.zoom_at = at
        self.editor.order(f"zoom\t{int(by)}")
        return True

    def show(self, what: str) -> bool:
        """Point the window at the canvas, or back at the source."""
        if what not in ("canvas", "source"):
            return False
        self.showing = what
        self.editor.order(f"show\t{what}")
        return True

    def open(self, path: str) -> bool:
        """Ask for another file.

        **Left here rather than done here.**  Opening one means stopping
        an instrument and starting another, which is the loop's business
        and not a view port's — this is the same shape as an order, in
        the direction the model already talks.
        """
        self.wanted = path
        return True

    def copy(self) -> None:
        """Copy the selection — the same act `Ctrl-C` is."""
        self.editor.order("copy")

    def cut(self) -> None:
        self.editor.order("cut")

    def paste(self) -> None:
        self.editor.order("paste")

    def warn(self, message: str) -> None:
        """Say `message` in red beside the caret, briefly.

        What a refused `open` does with its reason: a sentence at the
        foot is easy to miss at the moment your hands are elsewhere, so
        the window flashes the `[+]` and puts the words where the eye
        already is — transient, like the piano key's number.
        """
        self.editor.order(f"warn\t{message}")

    def insert(self, text: str) -> bool:
        if not text:
            return False
        self.editor.order(f"insert\t{text}")
        return True

    def caret(self) -> int:
        """Where the cursor is, as a character offset.

        **Read across, not mirrored.**  `undo` needs a mirror because it
        has to answer in the same breath it is asked; this is only ever
        wanted when a command is already running, and `ged_pos` is an
        atomic read of a number — the same one `find` has always used to
        know where to search from.
        """
        return self.editor.pos

    def close_list(self) -> bool:
        """Put the command list away — the model saying it is finished.

        Return on a finished call means *again*, which is right for
        `find` and wrong for `template`, where again is a second copy of
        the same code.  So the command that is done says so, rather than
        the view keeping a table of which ones repeat.
        """
        self.editor.order("close")
        return True

    def fill(self, text: str) -> bool:
        """Put text in the question the list is asking."""
        if not text:
            return False
        self.editor.order(f"fill\t{text}")
        return True

    def ask(self, verb: str, *given: str) -> bool:
        """Ask this command, with these arguments already given.

        **`fill` answers the question; this one asks it.**  A hole's
        type is known before the person is asked for it, so `complete`
        arrives with the type *taken* and the caret in the field after
        it — and a completion that walks to the next hole asks itself
        again with the new type, which empties the field, re-ranks the
        list, and stops the box saying `Int` over a `Float` hole.
        `spec/workbench.md` §"The list" has the law.
        """
        if not verb:
            return False
        self.editor.order("\t".join(["ask", verb, *given]))
        return True

    def replace(self, text: str) -> bool:
        """Put a whole new document in, as one edit.

        **Not an order, and not a second kind of edit either.**  This is
        the same door a file open goes through — `ged_set_text`, picked
        up on the window's next frame — and on the far side it is
        `Document::set_text`, which *commits*: the undo stack gets one
        entry and the caret is clamped rather than reset.  So laying out
        a file is one `undo` away from the file you had, which is the
        only thing that makes a format safe to press.

        An order would have been the other obvious shape and is wrong
        here: `insert` carries its text through one tab-separated line,
        and a document with a tab in it would be truncated at it.
        """
        if not text:
            return False
        self.editor.text = text
        return True


def walking(canvas) -> bool:
    """Whether the window is walking this canvas for itself.

    **A file's own `substrate` is not the only thing that walks.**  The
    readings a frame owes were gated on *this* being true of the file's
    main canvas — so a program with no `substrate` at all, which is
    every piece that only stands `notes` or `canvas <expr>` boxes on
    its lines, was never sent a single `reading`.  Its boxes drew and
    then stood still: a meter that never moved, and a note that would
    not follow a hand however hard the hand was tracked, because what
    moves it is a reading and none was crossing.

    Found on 2026-08-15 with `minute.ges`, which has four score boxes
    and no `substrate`.  The same mistake as the one the comment below
    records — *"the substrates stand still" was readings gated on the
    canvas view* — from the other side: gated on the *file* having a
    main canvas rather than on the view showing one.  A box is a canvas
    and asks for what a canvas needs.
    """
    return canvas is not None and getattr(canvas, "crossing", None) is not None


def worth_telling(bench) -> bool:
    """Whether this program has anything the window walks.

    The loop's own question, with a name so that it can be asked in a
    test and answered wrongly only on purpose — see `walking` for the
    day it was answered wrongly by accident.
    """
    return walking(getattr(bench, "substrate", None)) or any(
        walking(box) for box in getattr(bench, "canvases", {}).values())


#: How long the loop sleeps while a hand is moving, and while it is not.
#:
#: **The fast one is the answer to a lagging command list.**  What the
#: window draws from its own state — the text, the caret, what is typed
#: into the list — appears on the next frame and cannot lag.  What is
#: *filtered*, though, is decided here, so a keystroke costs a round
#: trip: gesture out, poll, description back.  A flat 30 ms poll made
#: that round trip as long as the gap between two keys, so the list you
#: were reading answered the letter before the one you had just typed.
#: At 2 ms the whole round trip measures under 10 ms, which is less than
#: a frame and therefore not a thing a hand can feel.
BUSY, IDLE = 0.002, 0.010


def _payloads(sub, boxes: dict) -> str:
    """Every walkable canvas, as one `box`-sectioned payload.

    Each section reuses `Substrate.payload()` whole, with its
    open-ended `program` line rewritten to carry the text's line
    count, so sections can follow each other without a sentinel the
    serialized text would have to promise never to contain.  Empty
    when nothing crosses — the model taking the canvas back.
    """
    parts = []
    if sub is not None:
        parts.append(("substrate", sub.payload()))
    for key, s in sorted(boxes.items()):
        parts.append((key, s.payload()))
    out = []
    for key, p in parts:
        if not p:
            continue
        head, _, prog = p.partition("\nprogram\n")
        out.append(f"box\t{key}\n{head}\n"
                   f"program\t{len(prog.splitlines())}\n{prog}")
    return "\n".join(out)


def pace(stirred: bool, wait: float) -> float:
    """How long to sleep, given whether this tick found anything.

    **A gesture or a message counts; a changed description does not.**
    The description carries the beat, so while the transport runs it
    differs on every single tick — pacing on *that* would hold the fast
    pace forever and spin a core to keep a number looking smooth.  What
    deserves haste is a hand that moved.

    Going quiet backs off by doubling rather than dropping straight to
    `IDLE`, so the tick after a keystroke is still quick: people type in
    bursts, and the second letter should not pay for the first having
    finished.
    """
    return BUSY if stirred else min(IDLE, wait * 2)


class _LoopClock:
    """`GESTATE_LOOP_TIME=1` — the loop's own stopwatch, `[loop]` lines
    on stderr every few seconds.

    The window's `GESTATE_EDITOR_TIME` measures the view's half of a
    frame; this is the model's: what a pass spends answering gestures,
    deriving the furniture and walking the canvas, and how far apart
    canvas frames actually *land* — which is the period a hand on a
    fader feels, and a number no headless measurement can give because
    it is made of the loop's pacing, the throttle and the GIL together.
    """

    EVERY = 5.0

    def __init__(self):
        self.last_frame = None
        self.reset()

    def reset(self):
        self.passes = 0
        self.act_s = self.furn_s = self.canvas_s = 0.0
        self.canvas_worst = 0.0
        self.frames = 0
        self.gap_s = 0.0
        self.since = time.monotonic()

    def lap(self, acted: float, furnished: float, canvased: float,
            drew: bool) -> None:
        self.passes += 1
        self.act_s += acted
        self.furn_s += furnished
        self.canvas_s += canvased
        if drew:
            self.frames += 1
            self.canvas_worst = max(self.canvas_worst, canvased)
            now = time.monotonic()
            if self.last_frame is not None:
                self.gap_s += now - self.last_frame
            self.last_frame = now
        now = time.monotonic()
        if now - self.since < self.EVERY:
            return
        n = max(self.passes, 1)
        line = (f"[loop] {self.passes} passes"
                f" | act {self.act_s / n * 1000:.2f}ms"
                f"  furniture {self.furn_s / n * 1000:.2f}ms per pass")
        if self.frames:
            line += (f" | canvas {self.canvas_s / self.frames * 1000:.2f}ms"
                     f" avg {self.canvas_worst * 1000:.2f}ms worst,"
                     f" {self.frames} frames"
                     f" {self.gap_s / max(self.frames - 1, 1) * 1000:.2f}ms"
                     f" apart")
        print(line, file=sys.stderr)
        self.reset()


def _begin(bench, session, after=None):
    """Start an instrument beside the loop, and say how to stop it.

    **Starting must not be able to hold the editor shut.**
    `Workbench.start` compiles the file with `clang` — seconds on a
    large score — and then asks for the sound card, which another
    program may already have. Done on the way in, either of those leaves
    a window that is open and answers nothing.

    **And the shutdown has to wait for it.**  `stop` signals the C audio
    loop, joins its thread and closes the host; called while `start` is
    still building those, it stops a device that does not exist yet and
    the one that arrives a moment later is never stopped at all — the
    segfault `Workbench.stop` carries a comment about, earned once.

    `after` is the previous instrument's retirement (`_retire`), and
    the wait for it belongs *here*, on the new instrument's own thread:
    the sound card is not free until the old instrument is truly gone,
    but a join in the gesture loop held the window shut for as long as
    the old file's `clang` took (`fixme.md` F109).  A start overtaken
    by yet another file while it waits its turn simply never begins —
    there is nothing to stop, because nothing started.
    """
    quitting = threading.Event()

    def begin():
        if after is not None:
            after.join(timeout=15.0)
        if quitting.is_set():
            return
        try:
            bench.start()
        except Exception as e:                           # noqa: BLE001
            # **`start` has already recorded the mapped complaint**
            # (`Workbench.trouble`, positions in the file's own lines)
            # — the content box under the line draws from that, and the
            # status line takes the first line of the same fact rather
            # than a second, raw formatting of it.  Found by a
            # screenshot: every unit test drove `apply`, which always
            # recorded, and this path never had.
            whole = getattr(bench, "trouble", "") or str(e)
            session.said.append(f"not playing: {whole.splitlines()[0]}")
            return
        if quitting.is_set():
            # The window shut while the instrument was still coming up.
            # Whoever started it stops it; nobody else knows it is there.
            try:
                bench.stop()
            except Exception:                            # noqa: BLE001
                pass

    starter = threading.Thread(target=begin, daemon=True)
    starter.start()
    return quitting, starter


def _carry(session, bench):
    """The next session: a new instrument under the same window — and
    the same recording.

    **The window outlives the instrument; the recording does too.**  A
    switch used to build a bare `Session`, so the log restarted with
    the instrument and the story that *led to* the switch — exactly
    the part a reproduction loses — was the part it forgot: Henri's
    `its-good-now` transcript answered "nothing has happened yet" one
    step after a switch.  The carried log keeps its `path` and its
    base text, so the replay starts where the recording did and plays
    the switch as it was played.

    `Log.was` is deliberately left holding the old file's lines: the
    next command's `typed()` then records the swap as one ordinary
    edit step, which is what makes the text right when a replayed
    command runs on the far side of the switch.  The `#!` note marks
    the seam for the reader, since an edit step alone reads as typing.

    A switch before anything was recorded carries nothing — the log
    begins on first use, and then it begins on the new file.
    """
    fresh = Session(bench=bench)
    fresh.view = session.view
    fresh.log = session.log
    if fresh.log is not None:
        fresh.log.note(f"opened {Path(bench.path).name}")
    return fresh


def _retire(bench, starter, quitting):
    """The old instrument's teardown, off the gesture loop — F109.

    `quitting` is set here, so a start still inside its `clang` stops
    itself the moment it returns; the join and the stop then happen on
    this thread, because doing them in the gesture loop held the window
    shut for seconds while a file nobody was looking at finished
    compiling.  The returned thread is the retirement itself: the next
    `_begin` waits on it before asking for the sound card, and the quit
    path joins it so the process never exits over a teardown still
    running — which is the daemon-thread segfault `Workbench.stop`
    carries a comment about.
    """
    quitting.set()

    def reap():
        starter.join(timeout=15.0)
        try:
            bench.stop()
        except Exception:                                # noqa: BLE001
            pass

    reaper = threading.Thread(target=reap, daemon=True)
    reaper.start()
    return reaper


def _canvas_frame(bench) -> list:
    """One frame of the canvas: readings in, a tick, and the picture out.

    **A seam, because this is where a canvas goes still.**  Both calls
    belong to the *view* — a reading is once a frame because that is as
    often as anyone can see it, and `events` is the frame clock itself —
    and both were lost when `audiopygame.py` went and its loop with them.
    `observe` was left with no caller at all, so `peak`, `rms`, `position`
    and the bands sat at their defaults and every meter in
    `examples/audio` was frozen; and nothing here had *ever* ticked
    `events`, so a substrate that animates could not, in the editor, no
    matter what it was written over.

    Called rather than inlined so a test can run a frame without a window,
    which is the only way this stays wired: the bug was never in a
    function, it was in the fact that nobody called two.
    """
    bench.observe()
    bench.tick()
    return bench.picture()


#: **How long the next canvas frame is held off, as a multiple of the
#: last one's cost.**  A frame is `tick` plus `picture`, both the
#: G-machine walking the whole substrate, and the multiple is adaptive
#: because the cost is the *program's* — no constant here could know it.
#:
#: **One, not two, and the reason is the clock** (`spec/performance.md`
#: §4).  This began at 2.0 — hold the loop back so gestures keep two
#: thirds of it — but the stopwatch showed the rest was where the
#: machine cooled: on a `powersave` governor the loop napping between
#: walks dropped the core to 0.7 GHz and *tripled* the walk it was
#: resting from, a self-inflicted 5.8 Hz lantern.  Walking back-to-back
#: keeps the core hot, and the numbers all moved the right way: the
#: walk 60 → 26 ms, the cadence 8 → 34 Hz settled, and the palette
#: *faster* while animating (worst 51 ms against 64), because a gesture
#: always waited for the walk in progress and a hot walk is a shorter
#: wait.  What 1.0 spends is a core, roughly pegged while — and only
#: while — a canvas is being watched; the loop still runs one pass
#: between walks, so gestures are answered every walk-length, the same
#: bound the hold-off never changed.  `GESTATE_CANVAS_SHARE` overrides
#: it for measuring.
CANVAS_SHARE = float(os.environ.get("GESTATE_CANVAS_SHARE", "1.0"))

#: And never further apart than this, however dear the frame — a canvas that
#: costs a second still moves, visibly, rather than looking hung.
CANVAS_SLOWEST = 0.25

#: How often the instrument is read for a walked canvas, in seconds.
#:
#: `observe`'s contract is *once a frame* — `take_peak` accumulates
#: since it was last taken, so the read rate is the meter's window.
#: The first wiring read it every loop pass: five hundred 2 ms slivers
#: a second, and the PEAK meter flickered ("it's so fast" — Henri,
#: 2026-08-14).  Thirty a second is a meter the eye can read, and about
#: what the old per-frame path gave a cheap canvas.
READ_EVERY = 1 / 30


def _shapes(picture) -> str:
    """`gui.py`'s display list, as lines the window can read.

    **The string last in each line**, because it is the only field that
    can contain anything — everything before it is a number, so the
    split is unambiguous however somebody's label is written.
    """
    out = []
    for shape in picture or ():
        kind = shape[0]
        if kind == "rect":
            _k, x, y, w, h, c = shape
            out.append(f"rect\t{x}\t{y}\t{w}\t{h}"
                       f"\t{c[0]}\t{c[1]}\t{c[2]}")
        elif kind == "dot":
            _k, cx, cy, r, c = shape
            out.append(f"dot\t{cx}\t{cy}\t{r}\t{c[0]}\t{c[1]}\t{c[2]}")
        elif kind == "text":
            _k, x, y, text, c, scale = shape
            out.append(f"text\t{x}\t{y}\t{scale}"
                       f"\t{c[0]}\t{c[1]}\t{c[2]}\t{text}")
    return "\n".join(out)


def run(path, rate: int = 44100, block: int = 512,
        midi: bool = False, seed: int | None = None) -> int:
    """Open the file, play it, and hand the window the keyboard."""
    from .audioeditor import Workbench
    from .editor import Editor
    from .presence import Presence

    bench = Workbench(Path(path), rate=rate, block=block, midi=midi,
                      seed=seed)
    session = Session(bench=bench)
    #: **How long the day has been** — `spec/timer.md`.  Rooted at the
    #: file's own repository rather than at the process's directory, so
    #: the project half reads the tree being worked on and not whatever
    #: shell the window was launched from.
    presence = Presence(root=Path(path).resolve().parent)
    editor = Editor(bench.source(), 1100, 760)
    session.view = Window(editor)

    # **Starting the instrument must not be able to hold the editor
    # shut.**  `Workbench.start` compiles the file with `clang` — seconds
    # on a large score — and then asks for the sound card, which another
    # program may already have.  Done here on the way in, either of those
    # leaves a window that is open and answers nothing, because the loop
    # below has not begun; a DAW running in the background turns "the
    # editor" into "the editor hangs".
    #
    # So it starts beside the loop.  You can type immediately, the status
    # line says when the instrument arrives or why it did not, and a
    # score you cannot hear is still a score you can edit — which is the
    # right order of those two things.
    # **And the shutdown has to wait for it.**  `stop` signals the C
    # audio loop, joins its thread and closes the host; called while
    # `start` is still building those, it stops a device that does not
    # exist yet and the one that arrives a moment later is never stopped
    # at all.  The process then exits with a daemon thread inside the
    # generated code — which is the segfault `Workbench.stop` already
    # carries a comment about, earned once before.
    quitting, starter = _begin(bench, session)
    #: The previous instrument's teardown, still running — what the
    #: quit path must join before the process may end.
    retiring = None

    said, drawn = "", None
    #: The substrate whose payload the window last got — an identity,
    #: because a rebuild makes a new `Substrate` and nothing else does.
    #: Starts as a sentinel no substrate can be, so the first pass
    #: sends whatever is there, `None` included.
    walked: object = run
    wait, next_frame = IDLE, 0.0
    clock = _LoopClock() if os.environ.get("GESTATE_LOOP_TIME") else None
    try:
        while editor.is_open:
            # **A file asked for is a whole new instrument.**  The window
            # outlives it — the same rope, the same view, the same
            # command list — and everything below it is replaced, which
            # is what makes `open` a command rather than a second
            # program.
            wanted = getattr(session.view, "wanted", None)
            if wanted:
                session.view.wanted = None
                # **Built before the old one is retired**, and inside a
                # try — a file that will not read (a `.wav`, a
                # permission) used to raise here, in the gesture loop,
                # and the whole editor quit over a click.  On failure
                # the old instrument plays on and the status says why;
                # `do_open` refuses the obvious cases with a better
                # sentence before it gets this far.
                try:
                    fresh = Workbench(Path(wanted), rate=rate,
                                      block=block, midi=midi, seed=seed)
                    text = fresh.source()
                except Exception as e:              # noqa: BLE001
                    said_why = str(e).splitlines()[0] if str(e) else "unreadable"
                    session.said.append(
                        f"could not open {Path(wanted).name}: {said_why}")
                    continue
                said, drawn = "", None
                # **The switch is immediate; the teardown is not the
                # loop's.**  This used to join the old start right here
                # — so opening away from a big file mid-compile froze
                # the window for as long as its `clang` took, and the
                # compile it was waiting for was for a file nobody was
                # looking at (`fixme.md` F109).  `_retire` takes the
                # join and the stop; the new instrument's own thread
                # waits on it before asking for the sound card, so the
                # card ordering that join was really buying is kept.
                retiring = _retire(bench, starter, quitting)
                bench = fresh
                # `load`, not the setter: a different file is a
                # different past, and the setter commits — undo after a
                # switch stood the old file's text under the new file's
                # name, one save from overwriting it (F113).  And a
                # file being *started* loads unsaved — the `[+]` from
                # birth is the one durable tell that the file under
                # you is a starter wearing the name you asked for,
                # not the thing you went looking for.
                if Path(wanted).exists():
                    editor.load(text)
                else:
                    editor.load_new(text)
                session = _carry(session, bench)
                session.said.append(f"opened {Path(wanted).name}")
                quitting, starter = _begin(bench, session, after=retiring)
            stirred = False
            t0 = time.monotonic()
            # **Gestures first, then the description.**  A command run
            # this tick should be visible in the status line this tick,
            # and the other order shows it one frame late — which reads
            # as the editor lagging your hand.
            for line in editor.gestures():
                stirred = True
                # **The hand, and only the hand.**  `bench.drain()` below
                # stirs the loop too and is the *model* talking to
                # itself; counting it would have the timer accrue hours
                # while a rebuild ran in an empty room, which is the
                # exact lie `presence` exists not to tell.
                presence.touched()
                answer = act(session, line)
                if answer:
                    session.said.append(answer)

            # Whatever the model has been saying to itself — a rebuild
            # finishing, a seed drawn, a score that would not load.
            # Into the transcript as well as the status line: an error
            # the user *saw* belongs in the recording they reach for
            # when something has gone wrong.
            for message in bench.drain():
                stirred = True
                session.said.append(message)
                session.note(message)

            t1 = time.monotonic()
            # Two statements, not one: `warm` describes the reading
            # that was just taken, so the order they are asked in is the
            # whole of their agreement.
            tally = presence.reading()
            now = furniture(session, tally=tally, warm=presence.warm)
            if now != said:
                editor.describe(now)
                said = now

            # **Typing is an audition, when an audition is cheap** —
            # `Workbench.typed`, `fixme.md` F151.  Asked here rather
            # than anywhere closer to the keys because `furniture` has
            # just read the document (the flag is set by `Window.lines`)
            # and this is the one place that knows both the text and the
            # instrument.  `typed` decides whether to do anything at
            # all; every condition is its, so the loop stays a wire.
            if session.view.moved:
                session.view.moved = False
                heard = getattr(bench, "typed", None)
                if heard is not None:
                    heard(session.view.held())

            # **The payload, on rebuild and never on keystrokes.**  A
            # new instrument or an applied edit builds a new
            # `Substrate`; the identity moving is the one honest tell,
            # and it moves a handful of times a session.  An empty
            # payload takes the canvas back — a switch to a file with
            # nothing to walk must not leave the old file's canvas
            # walking.  Every canvas crosses in one payload as `box`
            # sections (B2, multiple canvas): the file's own keyed
            # `substrate`, each `canvas <expr>` ask keyed by its
            # hidden name, `program <lines>` bounding each text.
            sub = getattr(bench, "substrate", None)
            boxes = getattr(bench, "canvases", {})
            marks = (id(sub) if sub is not None else None,
                     tuple(sorted((k, id(s)) for k, s in boxes.items())))
            if marks != walked:
                walked = marks
                editor.walk(_payloads(sub, boxes))

            t2 = time.monotonic()
            # **The canvas, and only while it is what you are looking
            # at.**  A substrate is a program that draws every frame, so
            # asking for one nobody is watching is a whole graph forced
            # per tick for a picture behind a page of text.
            drew = False
            showing = getattr(session.view, "showing", "source") == "canvas"
            sub = getattr(bench, "substrate", None)
            crossed = walking(sub)
            told = worth_telling(bench)
            if (showing and crossed) or (
                    not (showing and not crossed)
                    and time.monotonic() >= next_frame):
                # `told`, not `crossed`, below: see `walking`.
                # **The window walks the canvas and draws the boxes**
                # (`spec/workbench.md` §"The canvas walks over crust",
                # `spec/scope.md`) — so what the model's frame owes is
                # facts, not pictures: `reading` lines for a crossed
                # canvas and `trace` lines for the scopes, both
                # *whatever shows*, for the same reason: the boxes
                # stand in the source view beside the code — the
                # scopes' from the start, and the canvas's since B2
                # ("the substrates stand still" was readings gated on
                # the canvas *view*, freezing every fader and lamp in
                # the box).  At `READ_EVERY`, because the read rate is
                # the meter's window; only when they moved, because a
                # meter at rest is not news; never a touch's echo,
                # which would snap a fader under a hand that had moved
                # on.
                if time.monotonic() >= next_frame:
                    next_frame = time.monotonic() + READ_EVERY
                    lines_out = []
                    if told:
                        lines_out += [f"reading\t{n}\t{v}"
                                      for n, v in bench.observe()]
                    for label, points in bench.scope_traces():
                        lines_out.append(
                            "trace\t" + label + "\t"
                            + "\t".join(f"{p:.5g}" for p in points))
                    heard = "\n".join(lines_out)
                    if lines_out and heard != drawn:
                        editor.readings(heard)
                        drawn = heard
            elif showing and time.monotonic() >= next_frame:
                drew = True
                began = time.monotonic()
                drawing = _shapes(_canvas_frame(bench))
                next_frame = began + min(
                    CANVAS_SLOWEST, (time.monotonic() - began) * CANVAS_SHARE)
                if drawing != drawn:
                    editor.draw(drawing)
                    drawn = drawing
            if clock is not None:
                t3 = time.monotonic()
                clock.lap(t1 - t0, t2 - t1, t3 - t2, drew)
            # **A canvas this loop animates keeps the fast pace.**
            # `pace`'s rule — a changed description does not count —
            # stands for the transport readout, where haste would spin a
            # core to keep a number smooth.  A canvas the loop *draws*
            # (the uncrossed `_canvas_frame` path) earns haste the same
            # way a hand does: `IDLE`'s 10 ms granularity would jitter
            # its frame schedule, and the person is looking at exactly
            # the pixels the haste buys.  A *walked* canvas earns
            # nothing: the window animates it natively, the loop's whole
            # duty to it is `reading`/`trace` lines gated at
            # `READ_EVERY`, and holding `BUSY` for that was hundreds of
            # furniture passes a second serving a 30 Hz cadence.  (The
            # rule once covered walked canvases too, against a governor
            # that let a napping loop's core collapse to 0.7 GHz —
            # `spec/performance.md` §4 — but the EPP holds the clock
            # now, and the walk left the loop besides.)
            wait = pace(stirred or (showing and not crossed), wait)
            time.sleep(wait)
    finally:
        # **Before anything that can fail.**  The seconds since the last
        # flush are the ones a crash costs, and the teardown below is the
        # part of this program most likely to raise.
        presence.close()
        editor.close()
        # Say so first, *then* wait: a start already past its own check
        # finishes and is stopped below, and one that has not reached it
        # stops itself.  Either way something stops the device, and this
        # returns only once that has happened.
        #
        # **Synchronously, and the retirement first.**  These waits are
        # the one place they may not move off-thread: a daemon thread
        # still inside a teardown when the process ends is the segfault.
        # The current starter may itself be waiting on the retirement,
        # so the retirement is joined first and the chain unwinds in
        # order.
        quitting.set()
        if retiring is not None:
            retiring.join(timeout=15.0)
        starter.join(timeout=15.0)
        try:
            bench.stop()
        except Exception:                                # noqa: BLE001
            pass
    return 0


def install_desktop() -> int:
    """Write the `.desktop` entry and icons a desktop needs.

    **What makes the taskbar show the egg instead of a gear.**  The
    window sets `_NET_WM_ICON` and `WM_CLASS=gestate` itself, but
    GNOME's dock only names a window it can match to a `.desktop`
    file — so this writes one under `~/.local/share`, with
    `StartupWMClass` equal to the class the window declares, and the
    icon at the sizes `hicolor` looks for.  Run once; run again after
    moving the repository or the venv, because `Exec` pins both.

    The scalable copy goes in beside the rasters, because a desktop
    that can use it will render the sizes nobody thought to install —
    and it is the artwork itself, not a rendering of it.

    **`Exec` is `tools/gestate-editor`, and that is the fix for a
    launcher that did nothing when clicked.**  It used to be `env
    PYTHONPATH=… python -m gestate.workbench %f`, which is correct in
    every way but the one that matters: a dock click passes *no file*,
    `%f` expands to nothing, `main` answers `a file to edit (or
    --desktop)` and exits 2 — into a journal nobody reads, because
    `Terminal=false`.  The wrapper was written for exactly this and
    says so in its own comment: it opens the file it was handed or the
    scratch file when it was handed nothing, it finds the venv, and it
    `cd`s to the tree.  Henri hit this on a fresh 26.04 install and
    fixed it there before it was fixed here; `board/installation-test.md`
    is the card about the fact that nothing caught it.
    """
    from gestate import icon

    home = Path.home() / ".local" / "share"
    for side in icon.HICOLOR:
        where = home / "icons" / "hicolor" / f"{side}x{side}" / "apps"
        where.mkdir(parents=True, exist_ok=True)
        (where / "gestate.png").write_bytes(icon.png(side))
    scalable = home / "icons" / "hicolor" / "scalable" / "apps"
    scalable.mkdir(parents=True, exist_ok=True)
    (scalable / "gestate.svg").write_text(icon.svg())
    root = Path(__file__).resolve().parent.parent
    apps = home / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    entry = apps / "gestate.desktop"
    entry.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=gestate\n"
        "Comment=a synth you can hear while you write it\n"
        f"Exec={root}/tools/gestate-editor %f\n"
        "Icon=gestate\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Audio;Development;\n"
        "StartupWMClass=gestate\n")
    print(f"wrote {entry}")
    sizes = ", ".join(str(s) for s in icon.HICOLOR)
    print(f"wrote gestate.png at {sizes} px, and gestate.svg, under "
          f"{home / 'icons' / 'hicolor'}")
    print("the dock reads these on its next look; log out and in if "
          "it does not")
    return 0


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.workbench",
        description="the editor: a synth you can hear while you write it")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--desktop", action="store_true",
                    help="install the desktop entry and icon, then exit")
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--midi", action="store_true",
                    help="listen to a MIDI controller as well")
    ap.add_argument("--seed", type=int, default=None,
                    help="which take of a chancy piece to play")
    args = ap.parse_args(argv)
    if args.desktop:
        return install_desktop()
    if args.file is None:
        ap.error("a file to edit (or --desktop)")
    return run(args.file, rate=args.rate, block=args.block,
               midi=args.midi, seed=args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
