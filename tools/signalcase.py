#: asked-by: Henri, 2026-09-13 — "take the numbers for all five, but present them before acting on them." — doc/trial/signals.md
"""The signals trial's numbers — `doc/trial/signals.md`, five cases, two arms.

    python tools/signalcase.py             # all five: agreement, lines, a step's cost
    python tools/signalcase.py twoknobs    # one case

For each case, the signal arm is the tree's program and the message arm is
`doc/trial/signals/<name>`.  Three things are printed, in the sheet's
order:

1. **agree** — the control: both arms' output, compared.  An audio case
   against its committed golden buffer at the golden's own settings; a
   canvas case frame for frame (bounce) or picture for picture
   (tic-tac-toe) on the inputs `test/test_gui.py` uses.
2. **lines** — code lines by the rule that counted the tic-tac-toe:
   non-blank and not a comment.  A message arm's block under
   `# ── Not counted` is library by the sheet's rule and is left out.
3. **a step** — on the reference machine, by **difference**: a long run
   minus a short one over the extra steps, so the compile and the first
   instant drop out.  Fastest of three each.  And for an audio case, the
   same on the **native engine** — the path that plays — where the
   message arm is first asked whether it compiles for the sound card at
   all.

*Not taken:* `crust`.  It steps a canvas only from a Rust host fed an
exported program (`shell/panel/src/canvas.rs`), which is a bench of its
own, and says so in the output.
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ARMS = ROOT / "doc" / "trial" / "signals"

CASES = [
    ("blip", "examples/audio/blip.ges", "audio"),
    ("bounce", "examples/gui/bounce.ges", "bounce"),
    ("tic-tac-toe", "examples/gui/tic-tac-toe.ges", "ttt"),
    ("knob", "examples/audio/knob.ges", "audio"),
    ("twoknobs", "examples/audio/twoknobs.ges", "audio"),
]

SAMPLE_BUDGET_US = 1e6 / 44100
FRAME_BUDGET_MS = 1000 / 60


def code_lines(text: str) -> int:
    body = text.split("# ── Not counted", 1)[0]
    return sum(1 for line in body.splitlines()
               if line.strip() and not line.strip().startswith("#"))


def fastest(run, times: int = 3) -> float:
    best = None
    for _ in range(times):
        began = time.perf_counter()
        run()
        took = time.perf_counter() - began
        best = took if best is None else min(best, took)
    return best


# ── audio ──────────────────────────────────────────────────────────────────

def _golden(path: Path):
    from gestate.audio import parse_golden
    return parse_golden(path.with_suffix(".samples").read_text())


def audio_case(tree: Path, arm: Path) -> dict:
    from gestate import audio
    from gestate.audioextract import extract
    from gestate.audiollvm import native_blocks

    header, gold = _golden(tree)
    rate = int(header["rate"])
    every = int(header["control_every"]) if "control_every" in header else None
    kw = dict(rate=rate, control_every=every) if every else dict(rate=rate)
    out = {}
    for label, path in (("signal", tree), ("message", arm)):
        src = path.read_text()
        got = audio.render(src, seconds=float(header["seconds"]), **kw)
        short, long_ = 0.5, 2.0
        a = fastest(lambda: audio.render(src, seconds=short, **kw))
        b = fastest(lambda: audio.render(src, seconds=long_, **kw))
        ref_us = (b - a) / ((long_ - short) * rate) * 1e6
        try:
            graph = extract(src, rate=rate)
        except Exception as e:                           # noqa: BLE001
            native = f"does not compile for the sound card: {str(e).splitlines()[1][:90]}"
        else:
            with tempfile.TemporaryDirectory() as d:
                def run(n):
                    for _ in native_blocks(graph, d, n, block=every):
                        pass
                run(64)                                  # build once, outside the timing
                n1, n2 = rate, 20 * rate
                t1, t2 = fastest(lambda: run(n1)), fastest(lambda: run(n2))
            native = (t2 - t1) / (n2 - n1) * 1e6
        out[label] = {"agree": f"{sum(x == y for x, y in zip(got, gold))}/{len(gold)} of the golden",
                      "lines": code_lines(src), "reference": f"{ref_us:.1f} µs a sample",
                      "native": native}
    return out


# ── canvas ─────────────────────────────────────────────────────────────────

BOUNCE_LISTS = [[], [("Tick",)], [("Tick",)] * 4, [("Tick",), ("Press", 100, 200)],
                [("Move", 5, 5), ("Move", 300, 300)], [("Tick",)] * 260,
                [("Press", 10, 10)] + [("Tick",)] * 10]


def bounce_case(tree: Path, arm: Path) -> dict:
    from gestate.gui import scenes

    sig, msg = tree.read_text(), arm.read_text()
    same = sum(scenes(sig, s) == scenes(msg, s) for s in BOUNCE_LISTS)
    out = {}
    for label, src in (("signal", sig), ("message", msg)):
        a = fastest(lambda: scenes(src, [("Tick",)] * 20))
        b = fastest(lambda: scenes(src, [("Tick",)] * 220))
        out[label] = {"agree": f"{same}/{len(BOUNCE_LISTS)} event lists, every frame",
                      "lines": code_lines(src),
                      "reference": f"{(b - a) / 200 * 1000:.2f} ms a frame", "native": "—"}
    return out


CELL_X, CELL_Y = {0: -60, 1: 0, 2: 60}, {0: -72, 1: -12, 2: 48}
GAMES = [([0, 4], ()), ([0, 0, 0, 0, 0, 0], ()), ([0], (1, 2, 5, 8)),
         ([0, 4, 1, 8, 2, 3], ()), ([4, 0, 8, 2, 1, 7, 3, 5, 6], ())]


def _play(src: str, cells, drags=()):
    from gestate.gui import Substrate
    v = Substrate(src, 44100)
    pics = [v.picture()]
    for c in cells:
        v.touch_all("press", CELL_X[c % 3], CELL_Y[c // 3])
        pics.append(v.picture())
    for c in drags:
        v.touch_all("drag", CELL_X[c % 3], CELL_Y[c // 3])
        pics.append(v.picture())
    return pics


def ttt_case(tree: Path, arm: Path) -> dict:
    from gestate.gui import Substrate

    sig, msg = tree.read_text(), arm.read_text()
    same = sum(_play(sig, c, d) == _play(msg, c, d) for c, d in GAMES)
    out = {}
    for label, src in (("signal", sig), ("message", msg)):
        views = [Substrate(src, 44100) for _ in range(3)]
        order = [4, 0, 8, 2, 1, 7, 3, 5, 6]           # a whole game, no winner until the end

        def presses(view):
            began = time.perf_counter()
            for c in order:
                view.touch_all("press", CELL_X[c % 3], CELL_Y[c // 3])
                view.picture()
            return time.perf_counter() - began
        per = min(presses(v) for v in views) / len(order)
        out[label] = {"agree": f"{same}/{len(GAMES)} games, every picture",
                      "lines": code_lines(src),
                      "reference": f"{per * 1000:.2f} ms a press", "native": "—"}
    return out


def main(argv=None) -> int:
    from gestate.pipeline import _deep_stack  # noqa: F401  (the renders take it themselves)

    args = list(argv if argv is not None else sys.argv[1:])
    run = {"audio": audio_case, "bounce": bounce_case, "ttt": ttt_case}
    for name, tree, kind in CASES:
        if args and name not in args:
            continue
        tree_p = ROOT / tree
        arm_p = ARMS / Path(tree).name
        res = run[kind](tree_p, arm_p)
        print(f"{name}")
        for label in ("signal", "message"):
            r = res[label]
            native = r["native"] if isinstance(r["native"], str) else f"{r['native']:.3f} µs a sample"
            print(f"  {label:<8} agree {r['agree']:<34} lines {r['lines']:>3}   "
                  f"reference {r['reference']:<18} native {native}")
        s, m = res["signal"]["lines"], res["message"]["lines"]
        print(f"  lines: message arm {m - s:+d} ({(m - s) / s * 100:+.1f} %)")
    print(f"\nbudgets: a sample {SAMPLE_BUDGET_US:.1f} µs, a frame {FRAME_BUDGET_MS:.1f} ms; "
          f"crust not taken — see the docstring")
    return 0


if __name__ == "__main__":
    sys.exit(main())
