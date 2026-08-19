"""Does the picture stay under the hand while a note is dragged?

    python tools/dragcheck.py

**A test the test suite cannot run**, for the same reason
`tools/lagcheck.py` cannot: what is being checked is what a real window
did with a real press, and every unit test in the crate passed through
the defect this exists for.

That defect: a press on a note in a score box says where the note is
*written* (`spec/north_star.md`), and in `noted.ges` the box on line
142 draws notes written on line 94.  The jump scrolled the text — so
the box went out from under the finger that was pressing it, and the
drag went on against the pixels the grab remembered.  Nothing in the
window says so; you have to look.

The check itself: photograph a strip of text that is neither the box
nor the peep, press a note, and photograph it again.  If the view
scrolled, that strip is different text; if the hand kept its picture,
it is the same pixels.  The peep window (`spec/workbench.md` §"The
peep") is what should be showing line 94 meanwhile, and the third
screenshot is there to be looked at.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
#: **A driven window keeps no record of the day** — `lagcheck.driven`
#: says why, and it is shared so a fifth harness cannot forget.
from driven import a_copy_of, driven, move, press  # noqa: E402

#: Where the `notes score` box's notes sit in `noted.ges`, in the
#: window's own coordinates, once the file is scrolled to its foot.
#: Written down rather than searched for: a tool that hunts for a note
#: by colour would be a second implementation of the picture, and the
#: point here is the *view*, not the drawing.
NOTE = (622, 710)
#: A strip of ordinary text — above the box, below the peep, and
#: unchanged by anything the drag does.  If this moves, the view
#: scrolled.
STRIP = (0, 300, 900, 200)                     # x, y, w, h


from driven import a_copy_of, driven, move, press  # noqa: E402
def wheel(times: int) -> None:
    for _ in range(times):
        press(True, 5)
        press(False, 5)
        time.sleep(0.02)


def shot(win: int, path: str, crop: tuple | None = None) -> None:
    args = ["import", "-window", str(win)]
    if crop is not None:
        x, y, w, h = crop
        args += ["-crop", f"{w}x{h}+{x}+{y}"]
    subprocess.run(args + [path], capture_output=True)


def same(a: str, b: str) -> bool:
    out = subprocess.run(["compare", "-metric", "AE", a, b, "null:"],
                         capture_output=True, text=True)
    said = out.stderr.strip().split()[0] if out.stderr.strip() else "0"
    return said in ("0", "0.0")


def find_window(title: str = "gestate", patience: float = 60.0):
    until = time.time() + patience
    while time.time() < until:
        time.sleep(0.5)
        tree = subprocess.run(["xwininfo", "-root", "-tree"],
                              capture_output=True, text=True).stdout
        for line in tree.splitlines():
            if '"%s"' % title in line:
                return int(line.split()[0], 16)
    return None


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python tools/dragcheck.py",
        description="press a note and see whether the box stayed put")
    ap.add_argument("--keep", metavar="DIR",
                    help="where to leave the screenshots")
    ap.add_argument("--wheel", type=int, default=40,
                    help="wheel clicks down to the box (default 40)")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    score = os.path.join(root, "examples", "audio", "noted.ges")
    proc = subprocess.Popen([sys.executable, "-m", "gestate.workbench",
                             a_copy_of(score)], env=driven(),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    tmp = args.keep or tempfile.mkdtemp(prefix="dragcheck-")
    os.makedirs(tmp, exist_ok=True)
    before = os.path.join(tmp, "strip-before.png")
    during = os.path.join(tmp, "strip-during.png")
    whole = os.path.join(tmp, "dragged.png")
    try:
        win = find_window()
        if win is None:
            print("no window appeared")
            return 2
        # The build has to have run, or there are no boxes to press.
        time.sleep(12)
        move(600, 400)
        wheel(args.wheel)
        time.sleep(2.0)
        shot(win, before, STRIP)
        move(*NOTE)
        time.sleep(0.3)
        press(True)
        time.sleep(1.0)
        shot(win, during, STRIP)
        for step in range(1, 6):
            move(NOTE[0], NOTE[1] - 6 * step)
            time.sleep(0.15)
        time.sleep(0.8)
        shot(win, whole)
        press(False)
        time.sleep(2.0)
        if same(before, during):
            print(f"ok — the press left the view where it was ({whole})")
            return 0
        print("MOVED — the press scrolled the text, so the box went out\n"
              "        from under the hand and the drag is running against\n"
              "        pixels that are no longer there.  See `pinned` in\n"
              "        shell/editor/src/window.rs and spec/workbench.md\n"
              f"        §\"The peep\".  Screenshots in {tmp}.")
        return 1
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:                                # noqa: BLE001
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
