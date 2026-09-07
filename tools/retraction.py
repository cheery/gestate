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

closureOfSet : Set (Cyclic 4096, Cyclic 4096) -> Set (Cyclic 4096, Cyclic 4096)
closureOfSet r = closure (Box r)

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


def _timed(state, fn, *args) -> tuple:
    """`(seconds, result node)` — **the whole value forced**, not the
    outer constructor: the machine is lazy, and a `rows n` timed to
    weak head normal form had built one cons cell and left the rest
    for the query to pay (the first table said *build 18 ms*).
    `canonical` walks and forces everything."""
    from gestate.crust import canonical

    began = time.perf_counter()
    node = _apply(state, fn, *args)
    canonical(node, state)
    return time.perf_counter() - began, node


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
    def timed(source: str, tmp: str, label: str) -> float:
        path = Path(tmp) / f"{label}.crust"
        path.write_text(serialize(compile_program(source), "main"))
        began = time.perf_counter()
        subprocess.run([str(binary), str(path)], capture_output=True,
                       text=True, check=True)
        return time.perf_counter() - began

    head = "main : Set (Cyclic 4096, Cyclic 4096)\n"
    print(f"{'rows':>6} {'build':>10} {'build+picture':>14} {'picture':>10}")
    with tempfile.TemporaryDirectory() as tmp:
        for n in sizes:
            build = timed(PROGRAM.replace("main : Int\nmain = 0\n",
                                          head + f"main = rows {n}\n"),
                          tmp, f"rows{n}")
            both = timed(PROGRAM.replace("main : Int\nmain = 0\n",
                                         head + f"main = picture (rows {n})\n"),
                         tmp, f"picture{n}")
            print(f"{n:>6} {build * 1000:>8.1f}ms {both * 1000:>12.1f}ms "
                  f"{(both - build) * 1000:>8.1f}ms")
    print()
    print("process start included in each; picture is the difference")
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
    # **Forced on the pipeline's deep stack, compiled off it**: a value
    # of a few hundred rows recurses past Python's default limit when
    # forced, and `compile` takes the deep stack itself — nested, the
    # two deadlock before a line is printed (2026-09-07).
    from gestate.pipeline import _deep_stack

    return _deep_stack(lambda: _tables(state, sizes))


def _tables(state, sizes) -> int:
    g = state.globals
    num = gm.NNum
    # **The relation is built first and the query timed alone.**  The
    # first version of this table timed `picture (rows n)` as one
    # evaluation, and `rows` — n unions of a singleton into a growing
    # set — is quadratic on its own; the card's reading 1 changed the
    # query's fold and the table barely moved, which is how the two
    # were told apart (2026-09-07, evening).
    print(f"{'rows':>6} {'build':>10} {'picture':>10} {'one gone':>10} {'ratio':>6}")
    for n in sizes:
        built, relation = _timed(state, g["rows"], num(n))
        _b, relation_but = _timed(state, g["rowsBut"], num(n), num(n // 2))
        whole, _r = _timed(state, g["picture"], relation)
        gone, _r = _timed(state, g["picture"], relation_but)
        print(f"{n:>6} {built * 1000:>8.1f}ms {whole * 1000:>8.1f}ms "
              f"{gone * 1000:>8.1f}ms {gone / whole:>6.2f}")
    print()
    print(f"{'chain':>6} {'closure':>10} {'one gone':>10} {'ratio':>6}")
    for n in [8, 16, 24]:
        _b, relation = _timed(state, g["rows"], num(n))
        _b, relation_but = _timed(state, g["rowsBut"], num(n), num(n // 2))
        whole, _r = _timed(state, g["closureOfSet"], relation)
        gone, _r = _timed(state, g["closureOfSet"], relation_but)
        print(f"{n:>6} {whole * 1000:>8.1f}ms {gone * 1000:>8.1f}ms "
              f"{gone / whole:>6.2f}")
    print()
    print("retraction: none — every evaluation is whole; ϕ/δ runs inside `fix`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
