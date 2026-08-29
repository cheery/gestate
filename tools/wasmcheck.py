#!/usr/bin/env python3
#: asked-by: a session, 2026-08-29 - card:online.md, question 6: "how far `llc -march=wasm32` gets on one existing graph, in an afternoon, with no page at all"
"""tools/wasmcheck.py — the graph as wasm, held sample for sample to the native render.

    python tools/wasmcheck.py examples/audio/twinkle.ges
    python tools/wasmcheck.py examples/audio/twinkle.ges --seconds 4 --keep out/

**The measurement `card:online.md` asked for, kept as a command** so it
can be re-run when the emitter changes.  `gestate.audiowasm.build`
compiles the same `.ll` text `audiollvm.build` uses, for wasm32;
`audiowasm.run` drives it under `wasmtime` with the same control
values `run_native` gets; this prints what a person wanted to know —
the module's size, what it imports (the page supplies those from
`Math`), and whether the samples are bit-identical — and exits 1 when
they are not.  `test/test_wasm.py` holds the same claim across the
example set; this is the one-file, any-length, look-at-it form.

It needs `clang`, `wasm-ld` and `wasmtime` (`tools/toolbox.sh` names
the last two); it stops with a sentence at whichever is missing.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--rate", type=int, default=44100)
    ap.add_argument("--block", type=int, default=256)
    ap.add_argument("--keep", help="directory to leave the .ll/.o/.wasm in")
    args = ap.parse_args(argv)

    from gestate import audiollvm, audioperform, audiowasm

    why = audiowasm.missing()
    if why is not None:
        print(why)
        return 2
    src = Path(args.file).read_text()
    graph = audioperform.graph_of(src, rate=args.rate)
    total = int(args.seconds * args.rate)
    perf = audioperform.Performance(graph)
    if audioperform.has_score(src):
        schedule, samples, _ = audioperform.scored(src, rate=args.rate,
                                                   block=args.block)
        perf.sources.append(audioperform.from_schedule(schedule))
        total = min(total, samples)
    control = perf.control()

    keep = Path(args.keep) if args.keep else Path(
        tempfile.mkdtemp(prefix="wasmcheck"))
    keep.mkdir(parents=True, exist_ok=True)
    wasm = audiowasm.build(graph, keep)
    imports = audiowasm.imports_of(wasm)
    print(f"module: {wasm} ({wasm.stat().st_size} bytes); imports: "
          f"{', '.join(f'{m}.{n}' for m, n in imports) or 'none'}")

    try:
        got = audiowasm.run(wasm, graph, control, total, args.block)
    except audiowasm.WasmError as e:
        print(f"{e}; stopped after the link.")
        return 2
    with tempfile.TemporaryDirectory() as d:
        native = audiollvm.run_native(graph, d, total, block=args.block,
                                      control=control)
    same = sum(1 for a, b in zip(native, got) if a == b)
    flat = (lambda x: x if isinstance(x, tuple) else (x,))
    worst = max((abs(p - q) for a, b in zip(native, got)
                 for p, q in zip(flat(a), flat(b))), default=0.0)
    print(f"{args.seconds:g}s at {args.rate} Hz: {same}/{total} frames "
          f"bit-identical, worst |diff| {worst:.3g}")
    return 0 if same == total else 1


if __name__ == "__main__":
    sys.exit(main())
