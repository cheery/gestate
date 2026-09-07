"""Does the tree's Datafun retract a fact, or recompute? — a number.

#: asked-by: Henri, 2026-09-07 - "do the chart library slice, and the measurement" — card:gui-is-difficult.md Q1

    python tools/retraction.py            # the table below, ~10 s
    python tools/retraction.py 400 800    # other relation sizes
    python tools/retraction.py --crust    # the picture rows on crust, the Rust machine

`card:gui-is-difficult.md` Q1 (Henri: *"a mix of algebraic types and
relations"*) waits on this: if the picture is a query over the model's
relations, a deleted note is a **retraction**, and seminaive evaluation
(`spec/data.md` Part I) is built for growth.  So: one program compiled
once, a relation of `n` rows built at run time, a picture-shaped query
over it evaluated whole, then the same query over the relation with one
row gone — and, through `fix`, a transitive closure, where the ϕ/δ
transform actually runs.  Only the evaluation is timed; the compile is
paid once, as a chart's is (`gestate/charts.py`).

**What the runtime has:** no delta across evaluations.  `evaluate` is
whole; ϕ/δ lives inside `fix`.  So "with one row gone" is a second full
evaluation, and the number this prints is what a retraction *costs
today*, not what an incremental one would.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestate import gmachine as gm                       # noqa: E402
from gestate.gmachine import run                         # noqa: E402
from gestate.pipeline import compile as compile_program  # noqa: E402

PROGRAM = """
rows : Cyclic 4096 -> Set (Cyclic 4096, Cyclic 4096)
rows n = case n == 0 of
    True -> {}
    False -> {(n, n + 1)} \\/ rows (n - 1)

rowsBut : Cyclic 4096 -> Cyclic 4096 -> Set (Cyclic 4096, Cyclic 4096)
rowsBut n k = case n == 0 of
    True -> {}
    False -> case n == k of
        True -> rowsBut (n - 1) k
        False -> {(n, n + 1)} \\/ rowsBut (n - 1) k

picture : Set (Cyclic 4096, Cyclic 4096) -> Set (Cyclic 4096, Cyclic 4096)
picture r = for (p in r) {(fst p * 8, snd p * 6)}

compose : (Cyclic 4096, Cyclic 4096) -> (Cyclic 4096, Cyclic 4096) -> Set (Cyclic 4096, Cyclic 4096)
compose p q = case snd p == fst q of
    True -> {(fst p, snd q)}
    False -> {}

closure : Box (Set (Cyclic 4096, Cyclic 4096)) -> Set (Cyclic 4096, Cyclic 4096)
closure be = unbox e = be in fix Box (r => e \\/ (for (p in r) (for (q in e) (compose p q))))

closureOf : Cyclic 4096 -> Set (Cyclic 4096, Cyclic 4096)
closureOf n = closure (Box (rows n))

closureBut : Cyclic 4096 -> Cyclic 4096 -> Set (Cyclic 4096, Cyclic 4096)
closureBut n k = closure (Box (rowsBut n k))

main : Int
main = 0
"""


def _apply(state, fn, *args):
    node = fn
    for a in args:
        node = gm.NAp(node, a)
    state.stack, state.dump = [node], []
    state.code = [gm.Eval()]
    run(state, max_steps=200_000_000)
    return state.stack[0]


def _timed(state, fn, *args) -> float:
    began = time.perf_counter()
    _apply(state, fn, *args)
    return time.perf_counter() - began


def crust(sizes) -> int:
    """The picture rows on `crust`: the same program, `main` set to each
    query, serialized and run by the Rust machine — the constant, not
    the growth (`card:relations-at-frame-rate.md` Q2)."""
    import subprocess
    import tempfile

    from gestate.crust import serialize

    root = Path(__file__).resolve().parent.parent
    crate = root / "crust"
    subprocess.run(["cargo", "build", "--quiet", "--release",
                    "--target-dir", str(crate / "target")],
                   cwd=crate, check=True)
    binary = crate / "target" / "release" / "crust"
    print(f"{'rows':>6} {'picture on crust':>18}")
    with tempfile.TemporaryDirectory() as tmp:
        for n in sizes:
            source = PROGRAM.replace(
                "main : Int\nmain = 0\n",
                "main : Set (Cyclic 4096, Cyclic 4096)\n"
                f"main = picture (rows {n})\n")
            path = Path(tmp) / f"picture{n}.crust"
            path.write_text(serialize(compile_program(source), "main"))
            began = time.perf_counter()
            subprocess.run([str(binary), str(path)], capture_output=True,
                           text=True, check=True)
            print(f"{n:>6} {(time.perf_counter() - began) * 1000:>16.1f}ms")
    print()
    print("process start included; the growth is the fold's, the constant the machine's")
    return 0


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    on_crust = "--crust" in args
    sizes = [int(a) for a in args if a != "--crust"] or [100, 300, 600]
    if on_crust:
        return crust(sizes)
    began = time.perf_counter()
    state = compile_program(PROGRAM)
    print(f"compiled once in {time.perf_counter() - began:.2f} s")
    g = state.globals
    num = gm.NNum
    print(f"{'rows':>6} {'picture':>10} {'one gone':>10} {'ratio':>6}")
    for n in sizes:
        whole = _timed(state, g["picture"], gm.NAp(g["rows"], num(n)))
        gone = _timed(state, g["picture"],
                      gm.NAp(gm.NAp(g["rowsBut"], num(n)), num(n // 2)))
        print(f"{n:>6} {whole * 1000:>8.1f}ms {gone * 1000:>8.1f}ms "
              f"{gone / whole:>6.2f}")
    print()
    print(f"{'chain':>6} {'closure':>10} {'one gone':>10} {'ratio':>6}")
    for n in [8, 16, 24]:
        whole = _timed(state, g["closureOf"], num(n))
        gone = _timed(state, g["closureBut"], num(n), num(n // 2))
        print(f"{n:>6} {whole * 1000:>8.1f}ms {gone * 1000:>8.1f}ms "
              f"{gone / whole:>6.2f}")
    print()
    print("retraction: none — every evaluation is whole; ϕ/δ runs inside `fix`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
