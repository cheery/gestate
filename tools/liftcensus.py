#!/usr/bin/env python3
#: asked-by: Henri, 2026-09-18 — "go to 4" — the reach of the lift coercion, `card:strict-forms.md` item 4
"""tools/liftcensus.py — how the audio examples lift, and how far the lift coercion reaches.

    python tools/liftcensus.py            over examples/audio/*.ges

Two numbers per run.  First, on the desugared core of every example that
assembles alone: how many lifts are of a *value* (`!x`, `constSig`) and
how many of a *function* (`!f x`, `mapSig`).  Second, with every
parenthesised bare-name lift `(!x)` stripped from the text: how many
examples still analyse — those are the lifts the coercion of
2026-09-18 inserts by itself (`gestate/infer.py`, `_lift_into_signal`).
An example that does not analyse after stripping names the boundary.
"""
import glob
import re
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BARE = re.compile(r"\(!([a-z][A-Za-z0-9_]*)\)")


def _walk(n):
    if isinstance(n, (list, tuple)):
        for x in n:
            yield from _walk(x)
    elif is_dataclass(n) and not isinstance(n, type):
        yield n
        for f in fields(n):
            yield from _walk(getattr(n, f.name))


def main() -> int:
    from gestate import audio, pipeline
    from gestate.expr import EAp, EGlobal

    kinds = {"constSig": 0, "mapSig": 0}
    analysed = stripped = still = 0
    fails = []
    for f in sorted(glob.glob(str(ROOT / "examples" / "audio" / "*.ges"))):
        src = Path(f).read_text()
        try:
            a = pipeline.analyse(audio.assemble(src))
        except Exception:                                   # noqa: BLE001
            continue
        analysed += 1
        for sc in a.scs:
            for n in _walk(sc[2]):
                if isinstance(n, EAp) and isinstance(n.fn, EGlobal) and n.fn.name in kinds:
                    kinds[n.fn.name] += 1
        bare, n = BARE.subn(r"\1", src)
        if not n:
            continue
        stripped += n
        try:
            pipeline.analyse(audio.assemble(bare))
            still += 1
        except Exception as e:                              # noqa: BLE001
            fails.append((Path(f).name, n, str(e).split("\n")[0][:70]))
    print(f"{analysed} examples analyse alone; lifts of a value {kinds['constSig']}, "
          f"of a function {kinds['mapSig']}")
    print(f"{stripped} parenthesised bare lifts stripped across {still + len(fails)} "
          f"examples; {still} still analyse, {len(fails)} do not")
    for x in fails:
        print("  ", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
