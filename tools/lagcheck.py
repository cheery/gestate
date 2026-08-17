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

The check itself: type a word, then type one more distinct letter, and
look at the screen a second later. If the last letter is missing, the
editor is a keystroke behind your hand — which is what the transport
being stopped used to cause, because a playing transport redrew the
window constantly and drained the connection as a side effect.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time

X = ctypes.CDLL("libX11.so.6")
XTEST = ctypes.CDLL("libXtst.so.6")
X.XOpenDisplay.restype = ctypes.c_void_p
X.XOpenDisplay.argtypes = [ctypes.c_char_p]
X.XStringToKeysym.restype = ctypes.c_ulong
X.XStringToKeysym.argtypes = [ctypes.c_char_p]
X.XKeysymToKeycode.restype = ctypes.c_ubyte
X.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
X.XFlush.argtypes = [ctypes.c_void_p]
XTEST.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                    ctypes.c_int, ctypes.c_ulong]
XTEST.XTestFakeMotionEvent.argtypes = ([ctypes.c_void_p] + [ctypes.c_int] * 3
                                       + [ctypes.c_ulong])
XTEST.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                       ctypes.c_int, ctypes.c_ulong]

DPY = X.XOpenDisplay(None)


def _code(name: str) -> int:
    return X.XKeysymToKeycode(DPY, X.XStringToKeysym(name.encode()))


def tap(name: str) -> None:
    c = _code(name)
    XTEST.XTestFakeKeyEvent(DPY, c, 1, 0)
    XTEST.XTestFakeKeyEvent(DPY, c, 0, 0)
    X.XFlush(DPY)


def chord(modifier: str, name: str) -> None:
    m, c = _code(modifier), _code(name)
    XTEST.XTestFakeKeyEvent(DPY, m, 1, 0)
    XTEST.XTestFakeKeyEvent(DPY, c, 1, 0)
    XTEST.XTestFakeKeyEvent(DPY, c, 0, 0)
    XTEST.XTestFakeKeyEvent(DPY, m, 0, 0)
    X.XFlush(DPY)


def find_window(title: str = "gestate", patience: float = 30.0):
    """The window id, once it exists."""
    until = time.time() + patience
    while time.time() < until:
        time.sleep(0.5)
        tree = subprocess.run(["xwininfo", "-root", "-tree"],
                              capture_output=True, text=True).stdout
        for line in tree.splitlines():
            if '"%s"' % title in line:
                return int(line.split()[0], 16)
    return None


def click_into(win: int, dx: int = 300, dy: int = 60) -> None:
    """**Click, do not just focus.**  `XSetInputFocus` alone does not
    stick under a window manager, and injected keys then land in
    whatever the person at the keyboard was using."""
    geo = subprocess.run(["xwininfo", "-id", str(win)],
                         capture_output=True, text=True).stdout
    at = {}
    for line in geo.splitlines():
        for axis in ("X", "Y"):
            if "Absolute upper-left %s" % axis in line:
                at[axis] = int(line.split()[-1])
    XTEST.XTestFakeMotionEvent(DPY, -1, at["X"] + dx, at["Y"] + dy, 0)
    X.XFlush(DPY)
    time.sleep(0.3)
    XTEST.XTestFakeButtonEvent(DPY, 1, 1, 0)
    XTEST.XTestFakeButtonEvent(DPY, 1, 0, 0)
    X.XFlush(DPY)
    time.sleep(1.0)


def driven(**extra) -> dict:
    """The environment a *driven* workbench runs in.

    **XTEST types with the same X events a hand does**, and
    `gestate.presence` cannot tell them apart — nothing can, which is
    the point of XTEST.  So a harness left running for an hour would put
    an hour into somebody's week and the one instrument that measures
    the person would be measuring the test suite.  `GESTATE_PRESENCE=`
    (empty) turns the record off for the child.

    Every tool here that opens a window goes through this, so a fifth
    one cannot forget.
    """
    return dict(os.environ, GESTATE_PRESENCE="", **extra)


def shot(win: int, path: str) -> None:
    subprocess.run(["import", "-window", str(win), path], capture_output=True)


def differs(a: str, b: str) -> bool:
    """Whether two screenshots show anything different at all."""
    out = subprocess.run(["compare", "-metric", "AE", a, b, "null:"],
                         capture_output=True, text=True)
    return (out.stderr.strip().split()[0] if out.stderr.strip() else "0") != "0"


def main(argv=None) -> int:
    import argparse
    import os
    import tempfile

    ap = argparse.ArgumentParser(
        prog="python tools/lagcheck.py",
        description="type at the editor and see whether it kept up")
    ap.add_argument("file", help="a score to open")
    ap.add_argument("--stop", action="store_true",
                    help="run `stop` first — an idle window is where a "
                         "keystroke can go missing")
    args = ap.parse_args(argv)

    proc = subprocess.Popen([sys.executable, "-m", "gestate.workbench",
                             args.file], env=driven(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    tmp = tempfile.mkdtemp(prefix="lagcheck-")
    before, after = os.path.join(tmp, "a.png"), os.path.join(tmp, "b.png")
    try:
        win = find_window()
        if win is None:
            print("no window appeared")
            return 2
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

        chord("Control_L", "k")
        time.sleep(0.5)
        for ch in "loo":
            tap(ch)
            time.sleep(0.1)
        time.sleep(1.2)
        shot(win, before)
        # One more letter, and a second — far longer than any frame.
        tap("p")
        time.sleep(1.2)
        shot(win, after)

        if differs(before, after):
            print("ok — the last keystroke is on screen")
            return 0
        print("LAGGING — a second after typing it, the last keystroke has\n"
              "          not been drawn.  The window is idle and something\n"
              "          is not draining the X connection; see the note on\n"
              "          presenting clean frames in shell/editor/src/"
              "window.rs.")
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:                                # noqa: BLE001
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
