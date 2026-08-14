"""Drive the real editor window and collect GESTATE_EDITOR_TIME reports.

One scenario per process, so each run's [editor] lines mean one thing:

  idle     open the file, click in, hands off for ~12 s
  typing   type ~30 distinct characters at typing speed  (key->pixels)
  palette  Ctrl-K and type a query letter by letter      (query->list)
  canvas   Ctrl-K `canvas` Return, watch it animate ~12 s
  canvas-drag
           settle on the canvas, then saw a fader up and down for
           ~10 s — what a hand on a knob feels like while it draws.
           Aimed at lantern.ges's WARMTH fader (track centre ~(-80,-11)
           from the window's middle, from the row arithmetic in the
           file); the shots at the saw's two extremes are the proof the
           handle tracked the hand.

Usage: python measure_editor.py <scenario> <file.ges>
Prints every [editor] stderr line, prefixed, plus the scenario name.
Needs the display; do not touch the keyboard while it runs.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, "/home/cheery/gestate/tools")
from lagcheck import (tap, chord, find_window, click_into,  # noqa: E402
                      shot, DPY, X, XTEST)

WORKBENCH = [sys.executable, "-m", "gestate.workbench"]

def type_word(word: str, gap: float = 0.1):
    names = {" ": "space", ".": "period", "\n": "Return"}
    for ch in word:
        tap(names.get(ch, ch))
        time.sleep(gap)

def geometry(win: int):
    """The window's absolute corner and size, off xwininfo."""
    geo = subprocess.run(["xwininfo", "-id", str(win)],
                         capture_output=True, text=True).stdout
    at = {}
    for line in geo.splitlines():
        words = line.split()
        if "Absolute upper-left X" in line:
            at["x"] = int(words[-1])
        elif "Absolute upper-left Y" in line:
            at["y"] = int(words[-1])
        elif line.strip().startswith("Width:"):
            at["w"] = int(words[-1])
        elif line.strip().startswith("Height:"):
            at["h"] = int(words[-1])
    return at

def _move(x: int, y: int):
    XTEST.XTestFakeMotionEvent(DPY, -1, x, y, 0)
    X.XFlush(DPY)

def _button(down: bool):
    XTEST.XTestFakeButtonEvent(DPY, 1, 1 if down else 0, 0)
    X.XFlush(DPY)

def to_the_canvas():
    chord("Control_L", "k")
    time.sleep(0.5)
    type_word("canvas", gap=0.12)
    time.sleep(0.5)
    tap("Return")

def main() -> int:
    scenario, path = sys.argv[1], sys.argv[2]
    env = dict(os.environ, GESTATE_EDITOR_TIME="1", GESTATE_LOOP_TIME="1")
    # Into the caller's working directory, never beside this file — a
    # measurement run must not leave droppings in `tools/`.
    err = open(os.path.abspath(f"editor-{scenario}.stderr"), "w")
    proc = subprocess.Popen(WORKBENCH + [path], env=env,
                            cwd="/home/cheery/gestate",
                            stdout=subprocess.DEVNULL, stderr=err)
    try:
        win = find_window()
        if win is None:
            print("no window appeared")
            return 2
        click_into(win)
        time.sleep(2.0)          # let start-up traffic settle

        if scenario == "idle":
            time.sleep(12.0)
        elif scenario == "typing":
            type_word("the quick brown fox jumped over")
            time.sleep(3.0)
        elif scenario == "palette":
            chord("Control_L", "k")
            time.sleep(0.5)
            type_word("loop", gap=0.25)
            for _ in range(4):
                tap("BackSpace"); time.sleep(0.25)
            type_word("seek", gap=0.25)
            time.sleep(0.5)
            tap("Escape")
            time.sleep(3.0)
        elif scenario == "canvas-settled":
            # Let the instrument's own clang/LLVM startup finish so the
            # numbers are steady state, not startup contention.
            time.sleep(20.0)
            to_the_canvas()
            time.sleep(12.0)
        elif scenario == "canvas":
            to_the_canvas()
            time.sleep(12.0)
        elif scenario == "canvas-palette":
            # The starving number: the palette answered from the same
            # loop the G-machine animates on, so the query is typed
            # *while* the canvas draws — spec/performance.md §2.
            time.sleep(20.0)
            to_the_canvas()
            time.sleep(4.0)
            chord("Control_L", "k")
            time.sleep(0.5)
            type_word("seek", gap=0.4)
            time.sleep(0.5)
            tap("Escape")
            time.sleep(3.0)
        elif scenario == "canvas-drag":
            time.sleep(20.0)
            to_the_canvas()
            time.sleep(4.0)
            geo = geometry(win)
            # The WARMTH fader: the row is warm(52) gap(22) glow(52)
            # gap(34) meter(52), centred, so the warm track's centre
            # stands 80 left of the window's middle; its travel is the
            # 200-tall track, and the saw stays inside it.
            cx = geo["x"] + geo["w"] // 2 - 80
            cy = geo["y"] + geo["h"] // 2
            top, bottom = cy - 90, cy + 70
            _move(cx, bottom)
            time.sleep(0.3)
            _button(True)
            time.sleep(0.3)
            ends = {top: "drag-top.png", bottom: "drag-bottom.png"}
            began, going = time.time(), -1
            y = bottom
            while time.time() - began < 10.0:
                y += going * 8
                if y <= top or y >= bottom:
                    y = max(top, min(bottom, y))
                    going = -going
                    _move(cx, y)
                    time.sleep(0.25)          # let the frame land
                    name = ends.pop(y, None)
                    if name is not None:
                        shot(win, os.path.abspath(name))
                    continue
                _move(cx, y)
                time.sleep(0.03)
            _button(False)
            time.sleep(3.0)
        else:
            print(f"unknown scenario {scenario}")
            return 2
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:                                 # noqa: BLE001
            proc.kill()
        err.close()
    print(f"--- {scenario} {os.path.basename(path)} ---")
    with open(err.name) as f:
        for line in f:
            if line.startswith(("[editor]", "[loop]")):
                print(line.rstrip())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
