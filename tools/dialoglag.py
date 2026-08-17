"""Drive the open dialog and read the editor's own stopwatch.

F112 wants a number: `GESTATE_EDITOR_TIME=1` makes the window count
every ask->answer round trip (query->list) and print avg/worst at
close.  This types into the real dialog with XTEST — lagcheck's
primitives — once on a settled editor and once mid-compile.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
REPO = "/home/cheery/gestate"
sys.path.insert(0, os.path.join(REPO, "tools"))
from lagcheck import (a_copy_of, chord, click_into, driven,  # noqa: E402
                      find_window, tap)


def drive(file: str, settle: float, cycles: int, label: str) -> None:
    env = driven(GESTATE_EDITOR_TIME="1")
    proc = subprocess.Popen(
        [sys.executable, "-m", "gestate.workbench", a_copy_of(file)],
        cwd=REPO, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        win = find_window()
        if win is None:
            print(f"{label}: no window appeared")
            return
        click_into(win)
        time.sleep(settle)
        chord("Control_L", "k")
        time.sleep(0.4)
        for ch in "open":
            tap(ch)
            time.sleep(0.12)
        time.sleep(0.3)
        tap("Return")            # into the Path question; the listing lists
        time.sleep(0.6)
        # Narrow and widen: every keystroke is one wants round trip.
        for _ in range(cycles):
            tap("t")
            time.sleep(0.25)
            tap("BackSpace")
            time.sleep(0.25)
        tap("Escape")
        time.sleep(0.3)
        chord("Control_L", "q")
        try:
            _, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            _, err = proc.communicate(timeout=5)
        for line in (err or "").splitlines():
            if "query->list" in line or "key->pixels" in line:
                print(f"{label}: {line.strip()}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    # Settled: a small synth, ten seconds to come up and go quiet.
    drive(f"{REPO}/examples/audio/twoknobs.ges", 10.0, 15, "settled")
    time.sleep(2.0)
    # Starved: a big score, the dialog driven while clang still runs.
    drive(f"{REPO}/examples/super/nightdrive.ges", 1.0, 15, "mid-compile")
