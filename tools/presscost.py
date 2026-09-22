#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-22 — "measure the window's press first" — card:relational-model.md §"Drive and probe, asked"
"""What a press on a note costs in the window — the walk over the hit list, in Rust.

    Xvfb :99 -screen 0 1600x1000x24 &
    DISPLAY=:99 python tools/presscost.py                 # arc.notes, thirty presses
    DISPLAY=:99 python tools/presscost.py --presses 60

`card:relational-model.md` §"Drive and probe, asked" left one number
unknown: the reference machine's walk on a press is 2.8 ms and the
probe 0.4 ms (`tools/notecost.py`), but the window a person presses
in is Rust, and whether the per-note `Meaning` should go waits on
*its* walk and not the reference's.  This drives that press.

**What it reads, and from where.**  The window prints one line per
press under `GESTATE_EDITOR_TIME` — `[editor] press: walk N us, M
writes` — timed around the walk over the picture's hit table to what
the press took hold of, and nothing else (`shell/editor/src/window.rs`).
The model stamps the gesture's arrival on the wire (`GESTATE_WIRE`),
and this process stamps the press on the same monotonic clock, so
*press → the model has it* is one subtraction, as `tools/commitlag.py`
does for a release.  The notes are found by their ink in a photograph,
as there: a tool that asked the model where the notes are would be a
second reading of the picture, and the thing measured is the window.

A `driven.Run`: stamped, under `test/driven/`, with the library's md5.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commitlag import geometry, notes_in, wire                # noqa: E402
from driven import (Refused, Run, a_copy_of, chord, click_into,  # noqa: E402
                    move, press)

ROOT = Path(__file__).resolve().parent.parent
PRESS = re.compile(r"^\[editor\] press: walk (\d+) us, (\d+) writes$")


def presses_in(log: Path) -> list[tuple[int, int]]:
    """`(us, writes)` per press the window reported, in order."""
    out = []
    for line in log.read_text(errors="replace").splitlines():
        m = PRESS.match(line)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", default=str(ROOT / "examples" / "audio" / "arc.notes"))
    ap.add_argument("--presses", type=int, default=30)
    args = ap.parse_args(argv)

    try:
        run = Run("presscost", why="what does a press on a note cost the window's "
                  "walk, and how long until the model has it?",
                  GESTATE_WIRE="1", GESTATE_EDITOR_TIME="1")
        run.__enter__()
    except Refused as why:
        print(f"presscost: the run did not start.\n{why}", file=sys.stderr)
        return 2
    run.note("commit " + subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h %s"],
                                        capture_output=True, text=True).stdout.strip()[:100])
    log = run.dir / "wire.log"
    copy = a_copy_of(args.file)
    with open(log, "w") as err:
        proc = subprocess.Popen([sys.executable, "-m", "gestate.workbench", copy],
                                cwd=ROOT, env=run.env(PYTHONPATH=str(ROOT)),
                                stdout=subprocess.DEVNULL, stderr=err)
    rc = 1
    try:
        win = run.find_window(patience=90)
        if win is None:
            run.observe("did a window appear?", "no")
            return 2
        run.observe("did a window appear?", "yes")
        click_into(win)
        chord("Control_L", "Tab")
        until = time.time() + 60
        while time.time() < until and not any(k == "rows" for _t, k, _s in wire(log)):
            time.sleep(0.5)
        time.sleep(3.0)
        wx, wy, _ww, _wh = geometry(win)
        page = run.shot(win, "the-page")
        bars = notes_in(page)
        run.note(f"note bars found by ink: {len(bars)}")
        if not bars:
            run.observe("were notes drawn?", "no")
            return 2
        run.observe("were notes drawn?", f"yes — {len(bars)} bars")

        # Notes spread over the page, each pressed once at its centre
        # and let go where it was, so nothing is carried and no rewrite
        # follows.
        step = max(1, len(bars) // args.presses)
        picks = bars[::step][: args.presses]
        reached, missed = [], 0
        before = len(presses_in(log))
        for bar in picks:
            x, y = wx + bar[0] + bar[2] // 2, wy + bar[1] + bar[3] // 2
            move(x, y)
            time.sleep(0.12)
            press(True)
            pressed = time.monotonic()
            time.sleep(0.15)
            press(False)
            time.sleep(0.45)
            arrived = next((t for t, k, s in wire(log)
                            if k == "gesture" and s.startswith("touched") and t >= pressed), None)
            if arrived is None:
                missed += 1
            else:
                reached.append((arrived - pressed) * 1000)
        time.sleep(1.0)
        walked = presses_in(log)[before:]
        run.shot(win, "after-the-presses")

        frames = [line for line in log.read_text(errors="replace").splitlines()
                  if line.startswith("[editor]") and "paint" in line]
        if frames:
            run.note("window, last frame report: " + frames[-1])
        run.note(f"presses sent {len(picks)}, the window reported {len(walked)}, "
                 f"the model heard {len(reached)}")
        if walked:
            us = sorted(u for u, _w in walked)
            writes = sorted(w for _u, w in walked)
            run.observe("the window's walk on a press",
                        f"{len(us)} presses — best {us[0] / 1000:.2f} ms, median "
                        f"{us[len(us) // 2] / 1000:.2f} ms, worst {us[-1] / 1000:.2f} ms")
            run.observe("attachments a press took hold of",
                        f"median {writes[len(writes) // 2]}, most {writes[-1]}")
        if reached:
            reached.sort()
            run.observe("press → the model has it",
                        f"{len(reached)} presses — best {reached[0]:.0f} ms, median "
                        f"{reached[len(reached) // 2]:.0f} ms, worst {reached[-1]:.0f} ms")
        run.observe("presses the model never heard", str(missed))
        print("\n".join(f"{q} — {a}" for q, a in run.observations))
        rc = 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        run.__exit__(None, None, None)
        print(f"report: {run.dir / 'report.md'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
