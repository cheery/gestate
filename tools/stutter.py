#!/usr/bin/env python3
#: asked-by: unrecorded, 2026-08-15
"""Play a piece, rebuild it a few times, and say what that cost.

    python tools/stutter.py examples/audio/minute.ges --rate 44100

**A harness for a bisect, so it lives outside what it measures.**  The
obvious command — replaying a transcript with `--play` — cannot bisect
anything: `git bisect run` runs the tool *from the commit under test*,
and a commit from before the flag existed answers "unrecognized
arguments" with exit 2, which git reads as **bad**.  Five steps later
it names a commit that never ran.  (That happened.  It is why this file
exists.)

So this is run by absolute path and imports `gestate` from whatever
tree is checked out:

    git bisect start && git bisect bad && git bisect good <commit>
    git bisect run python /home/you/gestate/tools/stutter.py \
        examples/audio/minute.ges --rate 44100 --worst-ms 25

The same rule applies to what it *measures*.  The card's own account —
`[audio] card ran dry …` — was added on 2026-08-15 and does not exist
in the commits worth bisecting, so the numbers here are ones any
version can produce:

* **starved** — the worst overshoot of a 5 ms sleep on a thread of this
  process, in milliseconds.  A proxy for the GIL being held, which is
  what starves the *Python* driver; a machine running the C host keeps
  its audio out of Python's reach, so a big number here matters less
  and a small one proves less.
* **rebuild** — wall seconds per audition, and the process CPU spent.
  A commit that doubled what a rebuild costs is a commit that made
  every crackle likelier, whoever is driving.
* **dry** — the card's own count, *when the tree under test has it*.
  That is the honest one; the others are its stand-ins.

The verdict is `--worst-ms` (starvation) or `--rebuild-s` (cost), and
they are separate on purpose: which one you bisect on is a claim about
the mechanism, and this file does not know which mechanism it is.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time

# **The tree under test, not the tree this file lives in.**  Running a
# script puts *its own* directory first, which would import tonight's
# `gestate` into every step of a bisect and measure nothing.
sys.path.insert(0, os.getcwd())


def watchdog(stop: threading.Event, worst: list) -> None:
    """Sleep 5 ms in a loop and remember the longest one that wasn't.

    The thread has nothing to do, so every millisecond over is a
    millisecond somebody else held the interpreter — the same hold that
    makes the Python driver miss a block.
    """
    while not stop.is_set():
        began = time.perf_counter()
        time.sleep(0.005)
        over = (time.perf_counter() - began - 0.005) * 1000.0
        if over > worst[0]:
            worst[0] = over


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="tools/stutter.py",
        description="what a rebuild costs the machine, and the sound")
    ap.add_argument("file", help="a .ges to play and rebuild")
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--block", type=int, default=256)
    ap.add_argument("--auditions", type=int, default=3,
                    help="how many rebuilds to make it do (default 3)")
    ap.add_argument("--worst-ms", type=float, default=None,
                    help="fail if a thread was starved longer than this")
    ap.add_argument("--rebuild-s", type=float, default=None,
                    help="fail if a rebuild took longer than this")
    ap.add_argument("--cached", action="store_true",
                    help="leave the object store on; the default turns it "
                         "off so that `clang` actually runs, which is the "
                         "load being measured")
    args = ap.parse_args(argv)

    if not args.cached:
        os.environ["GESTATE_SO_CACHE"] = "0"

    from pathlib import Path

    from gestate.audioeditor import Workbench

    path = Path(args.file)
    if not path.exists():
        print(f"{path}: not here", file=sys.stderr)
        return 125                      # a step this tree cannot answer
    source = path.read_text()

    bench = Workbench(path, rate=args.rate, block=args.block)
    stop, worst = threading.Event(), [0.0]
    watching = threading.Thread(target=watchdog, args=(stop, worst),
                                daemon=True)
    began_cpu = time.process_time()
    took, dry = [], None
    try:
        bench.start()
        end = time.time() + 180.0
        while bench.live is None and time.time() < end:
            time.sleep(0.05)
        if bench.live is None:
            print("it never started", file=sys.stderr)
            return 125
        time.sleep(1.0)                 # let it settle before measuring
        watching.start()

        for n in range(args.auditions):
            was = bench.live.generation
            at = time.time()
            bench.audition(source + f"\n# take {n}\n")
            while bench.live.generation == was and time.time() < end:
                time.sleep(0.02)
            took.append(time.time() - at)
        # **Read before the teardown**, which closes the host and takes
        # the account with it — the first version of this printed no
        # card line at all and looked like a machine without one.
        host = getattr(bench, "host", None)
        dry = getattr(host, "dry", None) if host is not None else None
    finally:
        stop.set()
        bench.stop()

    cpu = time.process_time() - began_cpu
    slowest = max(took) if took else 0.0
    beat = args.block / max(1, args.rate) * 1000.0
    line = (f"[stutter] starved {worst[0]:.1f} ms of a {beat:.1f} ms block "
            f"· rebuild {slowest:.2f}s worst of {len(took)} "
            f"· cpu {cpu:.1f}s")
    if dry is not None:
        line += f" · card dry {dry}×"
    print(line)

    if args.worst_ms is not None and worst[0] > args.worst_ms:
        print(f"starved longer than {args.worst_ms} ms — bad")
        return 1
    if args.rebuild_s is not None and slowest > args.rebuild_s:
        print(f"a rebuild took longer than {args.rebuild_s}s — bad")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
