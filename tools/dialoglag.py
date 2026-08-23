#: asked-by: unrecorded, 2026-08-13
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
from driven import (Refused, a_copy_of, chord, click_into,  # noqa: E402
                      driven, find_window,
                      refuse_if_the_run_cannot_happen, tap)


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
    # **Not beside somebody's open editor** — F171.  XTEST sends keys to
    # whatever holds X focus and `click_into` is what hands focus over,
    # so this scenario, which opens a command box and types, would type
    # into a window whose file is not a copy.  `lagcheck.py` has had the
    # refusal since the day it was found because it goes through `Run`;
    # this file drives just as hard and had nothing.
    #
    # **Once, here, and not inside `drive()`**, which runs twice: the
    # second call would be weighing our own first window on its way out
    # and refuse the run for the wrong reason.  The question is whether
    # the display was somebody else's before we touched it.
    try:
        refuse_if_the_run_cannot_happen("python tools/dialoglag.py")
    except Refused as why:
        print(f"dialoglag: the run did not start.\n{why}", file=sys.stderr)
        raise SystemExit(2)
    # Settled: a small synth, ten seconds to come up and go quiet.
    drive(f"{REPO}/examples/audio/twoknobs.ges", 10.0, 15, "settled")
    time.sleep(2.0)
    # Starved: a big score, the dialog driven while clang still runs.
    drive(f"{REPO}/examples/super/nightdrive.ges", 1.0, 15, "mid-compile")
