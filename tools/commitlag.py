#: asked-by: Henri, 2026-09-13 — "yes, step 1 first, then the driven run" — card:gui-is-difficult.md
"""How long a note let go of on the page takes to reach the window.

    Xvfb :99 -screen 0 1600x1000x24 &
    DISPLAY=:99 python tools/commitlag.py                 # arc.notes, six drags
    DISPLAY=:99 python tools/commitlag.py --tree ../other # the same drags against another checkout

`card:gui-is-difficult.md` slice (a)'s postcondition is *a note let go
of on the roll is drawn in its new place within 60 ms, and the rest of
the picture does not redraw to get there*.  The half a headless bench
can time is `Workbench._load_substrate`; what a person waits for starts
at the button's release and ends at the window's next frame, and passes
through the X server, the window, the session's commit, the audition's
build and the wire on the way.  This drives that road.

**What it reads, and from where.**  The model stamps every send to the
window with `time.monotonic()` (`GESTATE_WIRE`), and so does this
process at the release — one clock on Linux, `CLOCK_MONOTONIC`, so the
difference is the model's side of the commit, end to end.  Whether a
`walk` crossed after the release says whether the picture was rebuilt
or changed.  The window's own side is one frame after the rows arrive,
and `GESTATE_EDITOR_TIME` reports what a frame costs to paint and copy;
it is *added*, not measured per commit, and the report says so.

**How it finds a note**: by its ink in a photograph of the page, the
three note colours `scorebox`'s hues draw — a tool that asked the model
where the notes are would be a second reading of the picture, and the
thing being measured is the window.  A drag that lands on another note
is refused by the document and sends no rows; that is reported as
refused and not timed.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from driven import (Refused, Run, a_copy_of, chord, click_into,  # noqa: E402
                    move, press)

ROOT = Path(__file__).resolve().parent.parent
#: The note inks on the page (`test/driven/…notes-tones…/report.md`):
#: a note, a tonic, a note outside the mode.
INKS = {(122, 200, 235), (96, 150, 220), (236, 200, 120)}
WIRE = re.compile(r"^\[wire (\d+\.\d+)\] (\w+): (.*)$")


def geometry(win: int) -> tuple[int, int, int, int]:
    out = subprocess.run(["xdotool", "getwindowgeometry", "--shell", str(win)],
                         capture_output=True, text=True).stdout
    g = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    return int(g["X"]), int(g["Y"]), int(g["WIDTH"]), int(g["HEIGHT"])


def notes_in(path: Path) -> list[tuple[int, int, int, int]]:
    """`(x, y, w, h)` of every horizontal run of note ink at least 12
    pixels long, one per bar — the shape a note is drawn as."""
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    found, seen = [], set()
    for y in range(h):
        x = 0
        while x < w:
            if px[x, y] in INKS and (x, y) not in seen:
                x0 = x
                while x < w and px[x, y] in INKS:
                    x += 1
                if x - x0 >= 12:
                    y1 = y
                    while y1 + 1 < h and px[x0 + 1, y1 + 1] in INKS:
                        y1 += 1
                    for yy in range(y, y1 + 1):
                        for xx in range(x0, x):
                            seen.add((xx, yy))
                    found.append((x0, y, x - x0, y1 - y + 1))
            else:
                x += 1
    return found


def wire(log: Path) -> list[tuple[float, str, str]]:
    out = []
    for line in log.read_text(errors="replace").splitlines():
        m = WIRE.match(line)
        if m:
            out.append((float(m.group(1)), m.group(2), m.group(3)))
    return out


def drag(x: int, y: int, dx: int) -> float:
    """Press at root `(x, y)`, carry the hand `dx` pixels right in small
    steps the way a hand moves, let go; the release's clock."""
    move(x, y)
    time.sleep(0.15)
    press(True)
    time.sleep(0.12)
    steps = max(1, abs(dx) // 4)
    for k in range(1, steps + 1):
        move(x + dx * k // steps, y)
        time.sleep(0.016)
    time.sleep(0.12)
    press(False)
    return time.monotonic()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", default=str(ROOT / "examples" / "audio" / "arc.notes"))
    ap.add_argument("--drags", type=int, default=6)
    ap.add_argument("--dx", type=int, default=40,
                    help="how far right each note is carried, in window pixels")
    ap.add_argument("--tree", default=str(ROOT),
                    help="the checkout whose gestate the window runs")
    args = ap.parse_args(argv)
    tree = Path(args.tree).resolve()

    try:
        run = Run("commitlag", why="how long does a note let go of on the page "
                  "take to reach the window, and is the page re-walked?",
                  GESTATE_WIRE="1", GESTATE_EDITOR_TIME="1", GESTATE_BUILD_TIME="1")
        run.__enter__()
    except Refused as why:
        print(f"commitlag: the run did not start.\n{why}", file=sys.stderr)
        return 2
    run.note(f"tree: {tree}  commit "
             + subprocess.run(["git", "-C", str(tree), "log", "-1", "--format=%h %s"],
                              capture_output=True, text=True).stdout.strip())
    log = run.dir / "wire.log"
    copy = a_copy_of(args.file)
    with open(log, "w") as err:
        proc = subprocess.Popen([sys.executable, "-m", "gestate.workbench", copy],
                                cwd=tree, env=run.env(PYTHONPATH=str(tree)),
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

        timed, refused, walked, halves = [], 0, 0, []
        # Notes spread over the page, each carried once, left of the
        # page's right edge so the hand stays on the roll.
        picks = [b for b in bars if b[2] >= 16][:: max(1, len(bars) // (args.drags * 2))]
        for bar in picks[: args.drags]:
            x, y = wx + bar[0] + 6, wy + bar[1] + bar[3] // 2
            before = len(wire(log))
            released = drag(x, y, args.dx)
            time.sleep(2.5)
            after = [e for e in wire(log)[before:] if e[0] >= released]
            rows = [e for e in after if e[1] == "rows"]
            walks = [e for e in after if e[1] == "walk"]
            let_go = next((e for e in after if e[1] == "gesture"
                           and e[2].startswith("released")), None)
            answered = next((e for e in after if let_go and e[1] == "answered"
                             and e[0] >= let_go[0]), None)
            walked += bool(walks)
            if not rows:
                refused += 1
                run.note(f"drag at {bar[:2]}: no rows after the release — refused or missed")
                continue
            ms = (rows[0][0] - released) * 1000
            timed.append(ms)
            split = ""
            if let_go and answered:
                split = (f" — the release reached the model at "
                         f"{(let_go[0] - released) * 1000:.0f} ms, its command "
                         f"answered at {(answered[0] - released) * 1000:.0f} ms "
                         f"({answered[2][:40]!r})")
                halves.append(((let_go[0] - released) * 1000,
                               (answered[0] - let_go[0]) * 1000,
                               (rows[0][0] - answered[0]) * 1000))
            run.note(f"drag at {bar[:2]}: rows {ms:.0f} ms after the release "
                     f"({rows[0][2]}); walks after it: {len(walks)}{split}")
        run.shot(win, "after-the-drags")

        frames = [line for line in log.read_text(errors="replace").splitlines()
                  if line.startswith("[editor]") and "paint" in line]
        if frames:
            run.note("window, last frame report: " + frames[-1])
        builds = [line for line in log.read_text(errors="replace").splitlines()
                  if line.startswith("[build]")]
        run.note(f"rebuilds reported: {len(builds)}; last: {builds[-1] if builds else '-'}")
        if timed:
            timed.sort()
            run.observe("release to rows, the model's side",
                        f"{len(timed)} commits — best {timed[0]:.0f} ms, median "
                        f"{timed[len(timed) // 2]:.0f} ms, worst {timed[-1]:.0f} ms")
        if halves:
            mid = lambda xs: sorted(xs)[len(xs) // 2]
            run.observe("where the wait goes, medians",
                        f"release → the model has it {mid([h[0] for h in halves]):.0f} ms; "
                        f"its command {mid([h[1] for h in halves]):.0f} ms; "
                        f"answered → rows sent {mid([h[2] for h in halves]):.0f} ms")
        run.observe("was the page re-walked after a commit?",
                    f"{walked} of {len(timed) + refused} drags")
        run.observe("drags that sent no rows", str(refused))
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
