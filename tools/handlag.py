#: asked-by: Henri, 2026-09-23 — "Kelpaavat, parempaakin kuin odotin. Ok. voimme aloittaa mittauksella." — card:notes-editor.md
"""How long a moved note takes to be heard — `card:notes-editor.md`'s postcondition, driven.

    Xvfb :99 -screen 0 1600x1000x24 &
    DISPLAY=:99 python tools/handlag.py                 # arc.notes, four carries in each state
    DISPLAY=:99 python tools/handlag.py --carries 8

The postcondition is *move a note and hear it before the hand has left
the mouse, with the picture following the hand — on the piece he
writes, not a toy.*  So a carry here is what a hand does: press a note,
take it up a few semitones one row at a time, let go.  Three moments
are stamped on one monotonic clock (`GESTATE_WIRE`, as
`tools/commitlag.py` does):

* **the note under the hand** — `sounded`, stamped where the preview
  reaches the allocator (`session.py`): after the press, and again at
  each new semitone;
* **the model has the hand** — the `gesture` lines, which is what the
  picture following the hand waits on before the window's next frame;
* **the moved note in the piece** — `scored`, stamped when the rebuild
  has loaded the new score (`audioeditor.py`), audible on the next block.

**Both transport states**, because the preview is opened differently in
each: first as the window opens, then after `play`.  The report says
which lines were seen, and a stretch with no stamp is reported as *not
heard*, never as fast.
"""

from __future__ import annotations

import argparse
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from commitlag import geometry, notes_in, wire  # noqa: E402
from driven import (Refused, Run, a_copy_of, chord, click_into, move,  # noqa: E402
                    press, tap)

ROOT = Path(__file__).resolve().parent.parent


def carry(x: int, y: int, rows: int, row_h: int) -> tuple[float, list[float], float]:
    """Press at `(x, y)`, take the note up `rows` rows one at a time, let
    go.  The press's clock, each step's clock, the release's clock."""
    move(x, y)
    time.sleep(0.15)
    pressed = time.monotonic()
    press(True)
    time.sleep(0.25)
    steps = []
    for k in range(1, rows + 1):
        steps.append(time.monotonic())
        move(x, y - k * row_h)
        time.sleep(0.25)
    released = time.monotonic()
    press(False)
    return pressed, steps, released


def command(word: str) -> None:
    chord("Control_L", "k")
    time.sleep(0.4)
    for ch in word:
        tap(ch)
        time.sleep(0.1)
    time.sleep(0.3)
    tap("Return")
    time.sleep(1.5)


def ms(xs: list[float]) -> str:
    if not xs:
        return "none"
    return (f"{len(xs)} — best {min(xs):.0f} ms, median {statistics.median(xs):.0f} ms, "
            f"worst {max(xs):.0f} ms")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--file", default=str(ROOT / "examples" / "audio" / "arc.notes"))
    ap.add_argument("--carries", type=int, default=4, help="carries in each state")
    ap.add_argument("--rows", type=int, default=3, help="semitones each carry climbs")
    args = ap.parse_args(argv)

    try:
        run = Run("handlag", why="move a note on his piece: when is it heard under "
                  "the hand, and when in the piece?",
                  GESTATE_WIRE="1", GESTATE_EDITOR_TIME="1", GESTATE_BUILD_TIME="1")
        run.__enter__()
    except Refused as why:
        print(f"handlag: the run did not start.\n{why}", file=sys.stderr)
        return 2
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
        bars = notes_in(run.shot(win, "the-page"))
        if not bars:
            run.observe("were notes drawn?", "no")
            return 2
        run.observe("were notes drawn?", f"yes — {len(bars)} bars")
        row_h = max(2, statistics.median(b[3] for b in bars))
        # Notes with room above them for the climb, spread over the page.
        room = [b for b in bars if b[2] >= 16 and b[1] > (args.rows + 2) * row_h]
        picks = room[:: max(1, len(room) // (args.carries * 3))]

        # Named by what was done, and the clock's readings say what state
        # that left: the window may open playing or not.
        for state, first in (("as the window opens", None), ("after `play`", "play")):
            if first:
                command(first)
            here = picks[: args.carries]
            picks = picks[args.carries:]
            under, resound, steps_heard, steps_all, scored, grasp = [], [], 0, 0, [], []
            ticks = 0
            for bar in here:
                x, y = wx + bar[0] + 6, wy + bar[1] + bar[3] // 2
                before = len(wire(log))
                pressed, steps, released = carry(x, y, args.rows, int(row_h))
                # Wait for the piece to have it, or ten seconds: a fixed wait
                # shorter than the rebuild credits one carry's score to the next.
                until = time.monotonic() + 10.0
                while time.monotonic() < until and not any(
                        e[1] == "scored" and e[0] >= released for e in wire(log)[before:]):
                    time.sleep(0.2)
                time.sleep(0.5)
                seen = [e for e in wire(log)[before:] if e[0] >= pressed]
                ticks += sum(1 for e in seen if e[1] == "observed" and "playhead" in e[2])
                sounds = [e[0] for e in seen if e[1] == "sounded"]
                gests = [e[0] for e in seen if e[1] == "gesture" and "touched" in e[2]]
                if gests:
                    grasp.append((gests[0] - pressed) * 1000)
                first_sound = next((t for t in sounds if t < released), None)
                if first_sound is not None and first_sound < (steps[0] if steps else released):
                    under.append((first_sound - pressed) * 1000)
                for k, t in enumerate(steps):
                    end = steps[k + 1] if k + 1 < len(steps) else released
                    steps_all += 1
                    hit = next((s for s in sounds if t <= s < end), None)
                    if hit is not None:
                        steps_heard += 1
                        resound.append((hit - t) * 1000)
                done = next((e[0] for e in seen if e[1] == "scored" and e[0] >= released), None)
                if done is not None:
                    scored.append((done - released) * 1000)
                run.note(f"{state}: carry at {bar[:2]} — sounds {len(sounds)}, "
                         f"scored {'%.0f ms' % ((done - released) * 1000) if done else 'never'} "
                         f"after the release")
            run.observe(f"{state}: was the clock running?",
                        f"{ticks} playhead readings over {len(here)} carries")
            run.observe(f"{state}: press → the model has the hand", ms(grasp))
            run.observe(f"{state}: press → the note sounds under the hand",
                        ms(under) if under else f"not heard in {len(here)} carries")
            run.observe(f"{state}: a new semitone → it sounds again",
                        f"{steps_heard} of {steps_all} steps; {ms(resound)}")
            run.observe(f"{state}: release → the moved note is in the piece",
                        ms(scored) if scored else "never stamped")
        run.shot(win, "after-the-carries")
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
