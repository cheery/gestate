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

import time
from pathlib import Path

from .session import Session, act, furniture


class Window:
    """`Session`'s view port, over the editor's ABI.

    What is *not* here is as much the point as what is: undo, find and
    zoom are the window's own keys and never cross the boundary, so a
    keystroke costs nothing and the palette's versions of them refuse
    honestly until there is a gesture for them.
    """

    def __init__(self, editor):
        self.editor = editor

    def text(self) -> str:
        return self.editor.text

    def close(self) -> None:
        self.editor.request_close()

    # The window handles these itself, on its own thread, and there is
    # no gesture yet that lets the model ask for one.  Saying so is
    # better than pretending: the palette prints the refusal.
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

    def insert(self, _text: str) -> bool:
        return False


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

    try:
        bench.start()
    except Exception as e:                               # noqa: BLE001
        session.said.append(f"not playing: {e}")

    said = ""
    wait = IDLE
    try:
        while editor.is_open:
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
            wait = pace(stirred, wait)
            time.sleep(wait)
    finally:
        editor.close()
        bench.stop()
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
