"""Drive the real editor window and collect GESTATE_EDITOR_TIME reports.

One scenario per process, so each run's [editor] lines mean one thing:

  idle     open the file, click in, hands off for ~12 s
  typing   type ~30 distinct characters at typing speed  (key->pixels)
  palette  Ctrl-K and type a query letter by letter      (query->list)
  canvas   Ctrl-K `canvas` Return, watch it animate ~12 s

Usage: python measure_editor.py <scenario> <file.ges>
Prints every [editor] stderr line, prefixed, plus the scenario name.
Needs the display; do not touch the keyboard while it runs.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, "/home/cheery/gestate/tools")
from lagcheck import tap, chord, find_window, click_into  # noqa: E402

WORKBENCH = [sys.executable, "-m", "gestate.workbench"]

def type_word(word: str, gap: float = 0.1):
    names = {" ": "space", ".": "period", "\n": "Return"}
    for ch in word:
        tap(names.get(ch, ch))
        time.sleep(gap)

def main() -> int:
    scenario, path = sys.argv[1], sys.argv[2]
    env = dict(os.environ, GESTATE_EDITOR_TIME="1")
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
            chord("Control_L", "k")
            time.sleep(0.5)
            type_word("canvas", gap=0.12)
            time.sleep(0.5)
            tap("Return")
            time.sleep(12.0)
        elif scenario == "canvas":
            chord("Control_L", "k")
            time.sleep(0.5)
            type_word("canvas", gap=0.12)
            time.sleep(0.5)
            tap("Return")
            time.sleep(12.0)
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
            if line.startswith("[editor]"):
                print(line.rstrip())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
