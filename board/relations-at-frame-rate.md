# relations-at-frame-rate — a query over a few hundred rows takes seconds, and a picture has a frame

    status   open
    because  the picture as a query over the model's relations — the
             derivative of the query as the damage rectangle, a lens
             from a row to the line that wrote it — is the shape
             `card:gui-is-difficult.md` Q1 reaches for, and measured
             on 2026-09-07 it costs 665 ms for a hundred rows and 27 s
             for six hundred, against 80 ms a frame for the roll walked
             as a list in the same machine.  Henri, 2026-09-07, on the
             number: "I think that's worth a card."
    asked    Henri, 2026-09-07
    see      card:gui-is-difficult.md Q1 — the model as types and
             relations; the measurement and its table
             tools/retraction.py — the command that made the number
             gestate/helpers.py — the set as a canonical sorted
             cons-list, union as one merge pass
             spec/data.md — Datafun with seminaive evaluation
             crust/ — the G-machine in Rust, the reference is gmachine.py

## What this is, what it is not, and when it runs

**The cost of evaluating a relational query in gestate, brought down
to where a picture can be one.**  It is not a change to the language,
to what a set means, or to the seminaive transform; it is not the
retraction question, which the same measurement answered — there is
none, every evaluation is whole — and which stays answered.  It runs
wherever a `for` over a set is evaluated: the reference G-machine
today, `crust` when it runs the same program.

## The postcondition

A picture-shaped query over the rows of a real piece evaluates inside
a frame, so that a view may be a query and not a walk.

## Measured against the tree, 2026-09-07 — the session's reading

| | |
|---|---|
| a set is a canonical sorted cons-list; `union` is one merge, linear | `gestate/helpers.py` `_gen_union` |
| `for (p in r) {f p}` joins one singleton per row — n merges of growing length | quadratic, and the whole of the number |
| `rows n = {(n, n+1)} \/ rows (n - 1)` does the same on the way in | the benchmark's own construction, not exempt |
| the interpreted machine's constant | ~130 µs a merge step in Python, *suspected* — `crust` unmeasured |
| the roll, hundreds of notes as a list, walked | 80 ms a frame — the machine is not the ceiling |

So the quadratic is not the machine and not the representation; it
is **the fold** — a `for` that could collect its results and sort once
merges instead, n times.  *Suspected, not measured:* that a collect-
and-sort `for` alone brings a hundred rows under a frame in Python;
that `crust` brings the constant down by the usual factor.

## Readings, each with what would kill it

1. **`for` collects, then sorts once** — O(n log n) where it is O(n²);
   the generated helper changes, the language does not.  *Killed if*
   the seminaive transform depends on `for`'s result being built by
   joins — it rewrites `for` nodes, so this must be read before it is
   assumed.
2. **`crust` runs the query.**  The same program on the Rust machine.
   *Killed if* `crust` does not yet run the Datafun helpers, or if the
   constant falls and the quadratic stays — a hundred rows is the
   easy case and six hundred is a piece.
3. **Both**, in that order — the fold first because it is the growth,
   the machine second because it is the constant.
4. **Neither: the picture stays a walk over a list**, as `roll.ges` is
   today, and relations stay the model on disk and the lookup.  This
   is where the tree stands and it works; the card exists because Q1
   wants more than that and the wanting has a number now.

## Questions

1. **Does ϕ/δ care how `for` builds its result?**  Read
   `gestate/seminaive.py`'s rewrite of `EFor` before reading 1 is
   taken.  *A session can answer this by reading.*
2. **Does `crust` run a `for`?**  *A session can answer this by
   running `tools/retraction.py`'s program on it.*
3. **What is the number that says done?**  *Session's proposal:* the
   `picture` row of `tools/retraction.py` at 600 under 80 ms, on the
   machine the window runs.  His to set.

## What a session does on day one

Answer Q1 and Q2 by reading and running, put both numbers on this
card, then take reading 1 if Q1 allows it.  Nothing is drawn.
