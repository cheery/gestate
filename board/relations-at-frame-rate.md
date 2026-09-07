# relations-at-frame-rate — a query over a few hundred rows takes seconds, and a picture has a frame

    status   doing
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

1. **Does ϕ/δ care how `for` builds its result?**  **Answered by
   reading, 2026-09-07, with Henri** — *no.*  `seminaive.py`'s ϕ keeps
   a `for` as a `for` node and δ wraps two `for` nodes in `join_` and
   `union_` calls; neither looks inside.  The fold is later and
   elsewhere: `pipeline._desugar_datafun` lowers `for (x in s) body`
   to `for_L s (λx. body)`, and `for_L` is the generated helper in
   `gestate/helpers.py` that joins one body result at a time.  So
   reading 1 changes one generated helper — a balanced merge of the
   body results, `O(n log n)` merges where there are `n` — and nothing
   the transform sees.
2. **Does `crust` run a `for`?**  **Answered by running, the same
   evening** — *yes*, the helpers are ordinary supercombinators.
   `python tools/retraction.py --crust`:

   | rows | Python | crust | ratio |
   |---|---|---|---|
   | 100 | 665 ms | 49 ms | 13.6 |
   | 300 | 6.2 s | 430 ms | 14.3 |
   | 600 | 27.0 s | 2.1 s | 12.7 |

   The constant falls by thirteen and the growth stays (×8.8, ×4.9):
   crust is the machine and the fold is the fold, as the front said.
   A hundred rows is under a frame on crust today, process start
   included; six hundred is not on either.
3. **What is the number that says done?**  *Session's proposal:* the
   `picture` row of `tools/retraction.py` at 600 under 80 ms, on the
   machine the window runs.  His to set.

## Reading 1, landed — 2026-09-07, evening

*"okay, do reading 1."*  `helpers._gen_for` generates the
comprehension as a balanced merge — the body results gathered into a
list, merged pairwise in rounds — and the set literal
(`pipeline._desugar_datafun`) uses the same `mergeAll_X` over its
singletons instead of folding them into an accumulator.  Three new
helper prefixes (`forList_`, `mergeAll_`, `mergePairs_`) registered
with the transform; nothing about what a set is changed, and the 104
tests of the Datafun suites are green unchanged.

**Two things the measuring itself taught.**  The first table timed
`picture (rows n)` as one evaluation, and after reading 1 it barely
moved — because `rows`, the benchmark's own recursive union, is the
other quadratic and was inside the number.  And the machine is lazy:
a `rows n` timed to weak head normal form had built one cons cell and
left the rest for the query to pay, so the second table lied the
other way (*build 18 ms*).  `tools/retraction.py` now forces the
whole value, on the pipeline's deep stack (compiled off it: nested,
the two deadlock), and times the query over a relation already built.

**The query, alone, before and after** — `python tools/retraction.py`
and `--crust`:

| rows | Python, before | Python, after | crust, after |
|---|---|---|---|
| 100 | 665 ms | 33 ms | 8 ms |
| 300 | 6.2 s | 123 ms | 20 ms |
| 600 | 27.0 s | 627 ms *(281 ms with a row gone — noisy, not chased)* | 14 ms |

Linear now, where it was quadratic.  **What remains quadratic is the
relation's construction by repeated union** — `rows n = {(n, n+1)} \/
rows (n - 1)`, 464 ms / 4.7 s / 19 s — which is a program's own
recursion and not the language's: a relation written as a literal or
built by a `for` is `n log n` now, and one handed in from Python
(`charts.py`'s way, the `.notes` records as a canonical list) is
linear.  The closure through `fix` is unchanged and should be: its
output is the chain's `n²` pairs.

**The done-number, Q3, both ways:** on crust the six-hundred-row
picture is 14 ms, under the 80 ms proposed; on the reference machine
it is 627 ms, and a hundred rows is 33 ms.  Which machine "the window
runs" is his to say — the canvas is walked in Rust, the roll's
reference walk in Python — and so is whether this card is done.

## What a session does on day one

~~Answer Q1 and Q2 by reading and running, put both numbers on this
card~~ — done 2026-09-07, evening, with Henri at the desk.  Next:
reading 1, since Q1 allows it — the `for_L` helper as a balanced
merge, held by `tools/retraction.py`'s table before and after and by
the Datafun suites unchanged.  Then reading 2 is a switch, not a
build.  Nothing is drawn.
