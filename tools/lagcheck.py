"""Does the editor show the letter you just typed?

    python tools/lagcheck.py examples/audio/twoknobs.ges

**A test the test suite cannot run.** The bug this exists for lived
between three pieces of software — `baseview` waiting on a file
descriptor, `softbuffer` reading from the same X connection, and a
keystroke buffered where neither was looking. Every unit test passed
through all of it. What found it was typing a key and asking, out of
band, whether the pixels had changed.

So this drives a *real* window with real X events and reads the answer
off the screen. It needs a display, `libXtst`, and ImageMagick's
`import`; it is not part of `pytest` and is not meant to be.

**The driven vocabulary moved to `tools/driven.py`** on 2026-08-19
(`card:driven-runs.md`): this file was named for one latency scenario
and held the harness every driven tool imported, which is a small lie
in a filename.  It is re-exported below so nothing that imported it
from here broke.

The check itself: type a word, then type one more distinct letter, and
look at the screen a second later. If the last letter is missing, the
editor is a keystroke behind your hand — which is what the transport
being stopped used to cause, because a playing transport redrew the
window constantly and drained the connection as a side effect.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from driven import (  # noqa: E402,F401  — re-exported, see the header
    Refused, Run, a_copy_of, chord, click_into, differs, driven, find_window,
    shot, tap,
)


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python tools/lagcheck.py",
        description="type at the editor and see whether it kept up")
    ap.add_argument("file", help="a score to open")
    ap.add_argument("--stop", action="store_true",
                    help="run `stop` first — an idle window is where a "
                         "keystroke can go missing")
    args = ap.parse_args(argv)

    # **Through `Run`, which is what makes the answer quotable.**  This
    # scenario used to write two PNGs into a fresh `mkdtemp` and print a
    # sentence; the sentence was then repeated in a commit body with
    # nothing behind it, and the two runs that were quoted on 2026-08-18
    # turned out to have been against a stale library
    # (`card:driven-runs.md`).  Now the run refuses if it would not be
    # about this code, and leaves the shots beside a stamp saying which
    # binary drew them.
    try:
        run = Run("lagcheck",
                  why="does the editor show the letter you just typed?")
        run.__enter__()
    except Refused as why:
        print(f"lagcheck: the run did not start.\n{why}", file=sys.stderr)
        return 2

    proc = subprocess.Popen([sys.executable, "-m", "gestate.workbench",
                             a_copy_of(args.file)], env=run.env(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    rc = 1
    try:
        win = run.find_window()          # never a window that was already open
        if win is None:
            run.observe("did a window appear at all?", "no")
            print("no window appeared")
            rc = 2
        else:
            run.observe("did a window appear at all?", "yes")
            click_into(win)

            if args.stop:
                chord("Control_L", "k")
                time.sleep(0.4)
                for ch in "stop":
                    tap(ch)
                    time.sleep(0.1)
                time.sleep(0.3)
                tap("Return")
                time.sleep(1.5)
                run.note("ran `stop` first — an idle window is where a "
                         "keystroke goes missing")

            chord("Control_L", "k")
            time.sleep(0.5)
            for ch in "loo":
                tap(ch)
                time.sleep(0.1)
            time.sleep(1.2)
            before = run.shot(win, "three-letters")
            # One more letter, and a second — far longer than any frame.
            tap("p")
            time.sleep(1.2)
            after = run.shot(win, "fourth-letter")

            if differs(str(before), str(after)):
                run.observe("is the last keystroke on screen a second later?",
                            "yes — the window kept up")
                print("ok — the last keystroke is on screen")
                rc = 0
            else:
                run.observe("is the last keystroke on screen a second later?",
                            "**no — LAGGING**")
                print("LAGGING — a second after typing it, the last keystroke "
                      "has\n          not been drawn.  The window is idle and "
                      "something\n          is not draining the X connection; "
                      "see the note on\n          presenting clean frames in "
                      "shell/editor/src/window.rs.")
                rc = 1
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:                                # noqa: BLE001
            proc.kill()
        run.__exit__(None, None, None)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
