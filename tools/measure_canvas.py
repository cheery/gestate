"""Measure the substrate/canvas half, headless.

Per canvas example:
  - compile: Substrate(text, rate) construction, best of 3
  - per frame: tick(), picture(), and workbench._shapes() serialization,
    over N frames after a short warmup
  - the picture's size: items and serialized bytes

No window, no sound card, no transport: tick/picture are exactly what
`workbench._canvas_frame` runs per frame (observe is host reads and is
gated on a transport we don't have; it is measured as absent, which is
the floor the editor loop pays).
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/cheery/gestate")

from gestate.gui import Substrate            # noqa: E402
from gestate.workbench import _shapes        # noqa: E402

RATE = 44100
FRAMES = 120
WARMUP = 10

def stats(xs):
    xs = sorted(xs)
    n = len(xs)
    return (sum(xs) / n, xs[n // 2], xs[0], xs[-1])

def measure(path: Path):
    text = path.read_text()

    builds = []
    for _ in range(3):
        t0 = time.perf_counter()
        sub = Substrate(text, RATE)
        builds.append(time.perf_counter() - t0)

    # Warmup frames (first forces settle allocations)
    for _ in range(WARMUP):
        sub.tick()
        sub.picture()

    ticks, pics, sers = [], [], []
    pic = []
    for _ in range(FRAMES):
        t0 = time.perf_counter()
        sub.tick()
        t1 = time.perf_counter()
        pic = sub.picture()
        t2 = time.perf_counter()
        wire = _shapes(pic)
        t3 = time.perf_counter()
        ticks.append(t1 - t0)
        pics.append(t2 - t1)
        sers.append(t3 - t2)

    frame = [a + b + c for a, b, c in zip(ticks, pics, sers)]
    print(f"\n== {path.name} ({len(text.splitlines())} lines) ==")
    print(f"compile Substrate(): best of 3 = {min(builds)*1000:.1f} ms "
          f"(all: {', '.join(f'{b*1000:.1f}' for b in builds)})")
    for name, xs in (("tick", ticks), ("picture", pics),
                     ("_shapes", sers), ("frame total", frame)):
        avg, med, lo, hi = stats(xs)
        print(f"{name:12s} avg {avg*1000:7.2f} ms  med {med*1000:7.2f}"
              f"  min {lo*1000:7.2f}  max {hi*1000:7.2f}")
    avg = sum(frame) / len(frame)
    print(f"-> {1/avg:.0f} fps unthrottled; editor budget: CANVAS_SHARE=2 "
          f"holds next frame off ~{2*avg*1000:.0f} ms -> ~{1/(2*avg):.0f} fps")
    print(f"picture: {len(pic)} items, {len(_shapes(pic))} bytes on the wire")

if __name__ == "__main__":
    for name in sys.argv[1:] or ["substrate.ges", "envelope.ges",
                                 "spectrum.ges", "lantern.ges"]:
        p = Path("/home/cheery/gestate/examples/audio") / name
        try:
            measure(p)
        except Exception as e:                           # noqa: BLE001
            print(f"\n== {p.name} == FAILED: {e}")
