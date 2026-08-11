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
"""

from __future__ import annotations

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

    def text(self) -> str:
        return self.editor.text

    def close(self) -> None:
        self.editor.request_close()

    def note_state(self, zoom: int, rungs: int,
                   undos: int, redos: int) -> None:
        """The window saying where its own state stands."""
        self.zoom_at, self.zoom_rungs = zoom, rungs
        self.undos, self.redos = undos, redos

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

    def insert(self, text: str) -> bool:
        if not text:
            return False
        self.editor.order(f"insert\t{text}")
        return True


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


def _begin(bench, session):
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
    """
    quitting = threading.Event()

    def begin():
        try:
            bench.start()
        except Exception as e:                           # noqa: BLE001
            session.said.append(f"not playing: {e}")
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

    bench = Workbench(Path(path), rate=rate, block=block, midi=midi,
                      seed=seed)
    session = Session(bench=bench)
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

    said, drawn = "", None
    wait = IDLE
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
                said, drawn = "", None
                quitting.set()
                starter.join(timeout=15.0)
                try:
                    bench.stop()
                except Exception:                        # noqa: BLE001
                    pass
                bench = Workbench(Path(wanted), rate=rate, block=block,
                                  midi=midi, seed=seed)
                editor.text = bench.source()
                view = session.view
                session = Session(bench=bench)
                session.view = view
                session.said.append(f"opened {Path(wanted).name}")
                quitting, starter = _begin(bench, session)
            stirred = False
            # **Gestures first, then the description.**  A command run
            # this tick should be visible in the status line this tick,
            # and the other order shows it one frame late — which reads
            # as the editor lagging your hand.
            for line in editor.gestures():
                stirred = True
                answer = act(session, line)
                if answer:
                    session.said.append(answer)

            # Whatever the model has been saying to itself — a rebuild
            # finishing, a seed drawn, a score that would not load.
            for message in bench.drain():
                stirred = True
                session.said.append(message)

            now = furniture(session)
            if now != said:
                editor.describe(now)
                said = now

            # **The canvas, and only while it is what you are looking
            # at.**  A substrate is a program that draws every frame, so
            # asking for one nobody is watching is a whole graph forced
            # per tick for a picture behind a page of text.
            if getattr(session.view, "showing", "source") == "canvas":
                drawing = _shapes(bench.picture())
                if drawing != drawn:
                    editor.draw(drawing)
                    drawn = drawing
            wait = pace(stirred, wait)
            time.sleep(wait)
    finally:
        editor.close()
        # Say so first, *then* wait: a start already past its own check
        # finishes and is stopped below, and one that has not reached it
        # stops itself.  Either way something stops the device, and this
        # returns only once that has happened.
        quitting.set()
        starter.join(timeout=15.0)
        try:
            bench.stop()
        except Exception:                                # noqa: BLE001
            pass
    return 0


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m gestate.workbench",
        description="the editor: a synth you can hear while you write it")
    ap.add_argument("file")
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--midi", action="store_true",
                    help="listen to a MIDI controller as well")
    ap.add_argument("--seed", type=int, default=None,
                    help="which take of a chancy piece to play")
    args = ap.parse_args(argv)
    return run(args.file, rate=args.rate, block=args.block,
               midi=args.midi, seed=args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
