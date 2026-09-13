#: asked-by: Henri, 2026-09-13 — "yes, start with DBSP" — card:gui-is-difficult.md
"""The picture by its changes — DBSP's algebra tried on the roll, a number.

    python tools/zset.py            # the stacked roll of line 127, the page, and 600 synthetic rows
    python tools/zset.py --box      # the stacked roll alone

`card:gui-is-difficult.md` §"Implementations that already match the
card" names DBSP (Budiu, McSherry, Ryzhyk, Tannen, arXiv 2203.16684) as
the piece Q1 measured missing: *there is no retraction*.  Its algebra,
checked against the paper §§2–4 on 2026-09-13:

* a **Z-set** is a finite map from rows to integer weights; a set is one
  whose weights are all 1, and a change is one whose weights may be −1;
* a query's **incremental version** is `Q^Δ = D ∘ Q ∘ I` — integrate the
  changes, run the query, differentiate the answer (Def. 3.1);
* a **linear** query is its own incremental version, `Q^Δ = Q`
  (Thm. 3.3) — filter, projection and map are linear, so the picture's
  `for` over the rows can be run on the changes alone;
* a **bilinear** one — a join — is `Δ(a⋈b) = Δa⋈Δb + a⋈Δb + Δa⋈b`
  (Thm. 3.4), which needs the relations it joins kept;
* and `distinct` is the one that is neither: making a Z-set a set again
  needs the integrated state (Prop. 4.7, the function `H`).

**What this measures.**  One note of his piece is moved one step later
— a retraction of its row and an assertion of the moved one, which is
what `assert`/`retract` already are as commands.  Then, for the same
compiled program:

1. **whole** — the picture of every row after the move, which is what a
   rebuild costs today;
2. **changes** — the picture of the two changed rows, the linear query
   run on the change (Thm. 3.3);
3. **host** — that change applied to the picture the host already held:
   take out what the retraction drew, put in what the assertion drew.
   The language has no set difference (Datafun is monotone), so
   integration, `I`, is the host's — which is seam 1 of §"The whole notes
   GUI in one `.ges` file", the host holding the facts;
4. **agree?** — the picture integrated from the changes against the
   picture computed whole, row for row.

And the same done twice, because the paper's caveat about `distinct` is
a question about *this* roll: once with the picture's item **keyed** by
the note (`i` carried, the identity law of Q7), and once **unkeyed**, as
`tools/queryframe.py` draws it.  An unkeyed item is a set element two
notes can share; taking one note out then takes out a rectangle the
other still draws, unless the weights are counted.

**Two traps from `tools/queryframe.py`, kept:** compile off the deep
stack and force on it, never nested; and no unary minus in a literal.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import queryframe as Q                                    # noqa: E402
import retraction as R                                    # noqa: E402
from gestate import gmachine as gm                        # noqa: E402

T7 = Q.T7


def literal(rows) -> str:
    return "{" + ", ".join("(" + ", ".join(Q.num(v) for v in r) + ")" for r in rows) + "}"


def program(before, after, gone, came) -> str:
    return f"""before : Set {T7}
before = {literal(before)}

after : Set {T7}
after = {literal(after)}

gone : Set {T7}
gone = {literal(gone)}

came : Set {T7}
came = {literal(came)}

hue : Int -> Int -> Int
hue t d = t * 2 + d

keyed : Set {T7} -> Set (Int, Int, Int, Int, Int)
keyed rs = for (r in rs) (case r of
    (i, x, y, w, t, d, m) -> {{(i, x, y, w, hue t d)}})

unkeyed : Set {T7} -> Set (Int, Int, Int, Int)
unkeyed rs = for (r in rs) (case r of
    (i, x, y, w, t, d, m) -> {{(x, y, w, hue t d)}})

main : Int
main = 0
"""


def moved(rows, which: int):
    """One note one step later: its row retracted, the moved row asserted."""
    r = rows[which]
    step = max(1, r[3] // 2)
    new = (r[0], r[1] + step) + tuple(r[2:])
    after = [new if k == which else row for k, row in enumerate(rows)]
    return after, [r], [new]


def synthetic(n: int):
    """`n` rows shaped like the roll's: four voices, a chord every so often."""
    return [(k, 40 + 12 * (k // 4), 200 - 9 * ((k * 7) % 30), 10, k % 4, 0, 0)
            for k in range(n)]


def elements(node, state) -> set:
    """A set's runtime value — a sorted cons list of tuples of `Int` —
    as a Python set, forced."""
    from gestate.midi import _force

    def whole(n):
        n = _force(n, state)
        while isinstance(n, gm.NInd) and n.target is not None:
            n = n.target
        return n

    out = set()
    cell = whole(node)
    while isinstance(cell, gm.NCon) and len(cell.args) == 2:
        item = whole(cell.args[0])
        out.add(tuple(whole(a).n for a in item.args))
        cell = whole(cell.args[1])
    return out


def best(times: int, run) -> tuple:
    """`(seconds, value)`, the fastest of `times` — **the first run of
    anything pays the machine's warm-up**, and timed once the change
    read as growing with the roll: 0.78, 1.25, 3.89 ms for the same two
    rows, where warm it is 0.14 ms at 88 rows and at 600 alike
    (2026-09-13)."""
    runs = [run() for _ in range(times)]
    return min(runs, key=lambda tv: tv[0])


def _integrate(held: set, took: set, put: set) -> tuple:
    import time
    began = time.perf_counter()
    out = (held - took) | put
    return time.perf_counter() - began, out


def measure(rows, which: int) -> dict:
    from gestate.pipeline import _deep_stack

    after, gone, came = moved(rows, which)
    src = program(rows, after, gone, came)
    out = {}
    for query in ("keyed", "unkeyed"):
        state = R.compile_program(src)                 # off the deep stack
        g = state.globals

        def one(state=state, g=g, query=query):
            fn = g[query]
            _t, held = R._timed(state, fn, g["before"])
            held = elements(held, state)
            whole, now = best(3, lambda: R._timed(state, fn, g["after"]))
            now = elements(now, state)
            t_gone, took = best(7, lambda: R._timed(state, fn, g["gone"]))
            t_came, put = best(7, lambda: R._timed(state, fn, g["came"]))
            took, put = elements(took, state), elements(put, state)
            host, integrated = best(7, lambda: _integrate(held, took, put))
            out[query] = {
                "whole": whole * 1000,
                "changes": (t_gone + t_came) * 1000,
                "host": host * 1000,
                "agree": integrated == now,
                "lost": sorted(now - integrated),
                "items": len(now),
            }
        _deep_stack(one)
    return out


def sharing(rows) -> list:
    """The positions of notes whose unkeyed item another note also draws."""
    seen: dict = {}
    for k, (i, x, y, w, t, d, m) in enumerate(rows):
        seen.setdefault((x, y, w, t * 2 + d), []).append(k)
    return sorted(k for ks in seen.values() if len(ks) > 1 for k in ks)


def report(label: str, rows) -> bool:
    """Every note moved in turn would be the honest sweep, and costs a
    compile each.  So: one note from the middle, and — where the roll
    has any — one note that shares its unkeyed item with another, which
    is the move the paper's `distinct` caveat is about."""
    moves = [len(rows) // 2] + sharing(rows)[:1]
    ok = True
    print(f"{label}: {len(rows)} rows; {len(sharing(rows))} notes share an unkeyed item")
    for which in moves:
        m = measure(rows, which)
        kind = "a shared note" if which in sharing(rows) else "a note"
        print(f"  {kind}, {rows[which][0]}, moved one step later")
        for query in ("keyed", "unkeyed"):
            r = m[query]
            print(f"    {query:<8} whole {r['whole']:7.1f} ms   changes {r['changes']:5.2f} ms   "
                  f"host {r['host']:5.3f} ms   agree {'yes' if r['agree'] else 'NO'}"
                  + (f" — drawn whole but lost by the changes: {r['lost']}" if r["lost"] else ""))
            ok = ok and (r["agree"] or query == "unkeyed")
    return ok


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    rolls = Q.rolls_of_piece()
    ok = report("the stacked roll of line 127", Q.rows_for(rolls, 2))
    if "--box" not in args:
        ok = report("every roll of the page", Q.rows_for(rolls, None)) and ok
        ok = report("synthetic", synthetic(600)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
