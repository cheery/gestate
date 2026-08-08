# errata.md — what the specs leave out relative to the papers

Scope: `spec/*.md` read against the three works they implement.

**Sources.**  None of these are in this repository — they are cited by name
and identifier so that they can be found, which is the only form of
citation that survives a directory being tidied away.

* **"the thesis"** — Michael Arntzenius, *Deconstructing Datalog*, PhD
  thesis, University of Birmingham, July 2021.  Datafun, seminaïve
  evaluation, and the ϕ/δ transform.  The specs say "the thesis" some
  forty times without ever saying which; **this is the line that says
  which**, and the title is not the word "Datafun".
* **"Rizzo"** — Patrick Bahr, *Simple Modal Types for Functional Reactive
  Programming* (arXiv:2512.09412).  Rizzo is the calculus's own name in
  that paper, which is why the specs use it as one rather than saying
  "Bahr's system".  Cited the same way in `spec/frp.md`.
* **"Cai et al."** — Yufei Cai, Paolo G. Giarrusso, Tillmann Rendel and
  Klaus Ostermann, *A Theory of Changes for Higher-Order Languages:
  Incrementalizing λ-Calculi by Static Differentiation* (arXiv:1312.0658).
  The antecedent of the thesis's Definitions 14–16.

This file records **gaps and disagreements between the specs and the papers
they claim to implement**.  It does not record implementation bugs — those go
in `fixme.md`.  Each item says what the paper requires, what the spec says (or
fails to say), and why it matters.

Section 4 records contradictions *between* spec files; those are not paper
errata but they surfaced during the same read and have nowhere better to live.

Of the 28 entries, 19 are resolved, answered or implemented.  Every one that
asked a *question* has been answered — D5 (`Bool` and `Prop`), D8 (the
change-structure interface, now `data.md` §I.8), D9 (a monomorphic Datafun
sublanguage) — which is what `roadmap.md`'s milestone turns on.  What remains
is omissions and hygiene.  D9's decision is now *enforced* as well as
settled: a Datafun operation at a non-ground set type is a compile error
rather than a run-time missing global (`fixme.md` F64).

---

## 1. Datafun thesis → `spec/data.md`, `spec/types.md`, `spec/syntax.md`

### D1. The eqtype / semilattice / fixtype subgrammars — **resolved**

All four are implemented (`gestate/types.py`) and enforced
(`gestate/subgrammar.py`) at the three rules of fig. 2.3 gestate can
reach: `set` (elements must be eqtypes), `for` (the result must be a
semilattice), and `fix` (a fixtype).  §II.1's soundness argument now has
a mechanism: the Rizzo formers are simply not in any of the grammars, so
`{someSignal}` and `Maybe (Sig Int)` as a set element are rejected, with
no side condition to state.

The choice D1 asked for is made rather than dodged: **the restriction is
stated, not dropped.**  `Int` is an eqtype but not a finite one, so
`{Int}` is not a fixtype and `fix` over it is rejected — with a message
saying why and naming the finite element types gestate has (`Cyclic n`,
`lo .. hi`, `Bool`).  A fixed point that closes a set under `+1`
terminates at `Cyclic 4` and would not at `Int`, so this is a real
distinction, not bookkeeping.

Two consequences worth recording:

- Every Datafun example in the literature is written over `{Int}` and now
  has to name a bounded element type.  That is the honest cost of the
  rule; the alternative is a `fix` that may not return.
- It forced §17's monomorphization: once `{Int}` stops being the only
  fix-able type, the helpers have to be selected from the inferred type
  rather than hardcoded.  `fixme.md` F8 and half of F11 went with it.

The original item:

### D1 (original). The subgrammars never reach the surface language

Fig. 2.1 defines four subgrammars over types:

```
eqtypes        A,B ::= {A}_eq | 1 | A×B | A+B
semilattices   L,M ::= {A}_eq | 1 | L×M
finite eqtypes A,B ::= {A}_fin | 1 | A×B | A+B
fixtypes       L,M ::= {A}_fin | 1 | L×M
```

`data.md` §II.1 refers to all four ("do not add these to the `eqtypes`,
`semilattices`, `finite eqtypes`, or `fixtypes` subgrammars"), and §I.5's
typing rule for `semifix` is stated at `fixL`.  But **no spec file ever defines
them**, and `spec/syntax.md` — which claims "Anything that is not appearing
here is not part of the syntax" — offers `{a}` set types and bare `fix expr`
with no element-type restriction at all, and `spec/types.md` has no notion of a
type-level side condition beyond kinds.

Consequences the spec does not state:

- `{e}` requires the element type to be an eqtype (thesis fig. 2.3, rule
  `set`); `e = f` requires an eqtype (rule `eq`).  With `Sig`/`Chan`/`→` in the
  grammar, `{someSignal}` must be rejected — §II.1's soundness argument depends
  on exactly this and it is never enforceable as written.
- `fix e` requires a **fixtype**, i.e. sets of *finite* eqtypes.  Footnote 2 on
  p. 16 is explicit: with integers in the language `{Int}` is an eqtype but
  **not** a finite one, so `{Int}` has infinite ascending chains and `fix` over
  it need not terminate.  Gestate has `Int`, and every worked example in
  `data.md` and `journal.md` Part I uses `Set Int`.  The spec should
  either state the restriction (bounded/cyclic integers are finite; `Int` is
  not) or state that it is deliberately dropped and that `fix` is therefore
  partial.
- `⊥`, `∨` and the result type of `for` require a semilattice type (rules
  `bot`, `join`, `for`).  `for` is *not* a monadic bind restricted to sets — it
  eliminates into any semilattice.

### D2. `semifix`'s convergence test — **resolved**

`semifixL` now tests `dx ⊑ x` (a generated `subset_L`, computed as
`eq (union a b) b`) and returns the accumulator, matching fig. 4.2.

This was not theoretical.  The first Datalog query gestate could express
— `fix (r => seed ∨ for (x in r) {x + 1})`, which only became writable
once `∨` was added — **hung** under the old `dx = ⊥` test, exactly as the
analysis below predicts.  `spec/data.md` §I.5 should be amended to the
thesis's test.

The naive `fix` still compares `next == cur`.  That one is equivalent:
`f` is monotone, so `next ⊇ cur` always, and then `next ⊆ cur` iff
`next = cur`.  The original diagnosis:

### D2 (original). `semifix`'s convergence test in §I.5 is not the thesis's

`data.md` §I.5 stops when "`dxi` is empty-equivalent", coded as
`eqL dx' bottomL`.  The thesis's runtime (fig. 4.2) stops on `dx <: x` — the
change is **subsumed by the accumulator**, not empty:

```haskell
semifix (f, df) = loop empty (f empty)
  where loop x dx = if dx <: x then x else loop (union x dx) (df x dx)
```

and it says so explicitly on p. 71: "seminaïve iteration stabilizes once
`dxi ⩽ xi`. (This is an optimization over checking equality `xi = xi+1`.)"

This is not a micro-optimization.  `δ(e ∨ f) = δe ∨ δf` is a deliberate
*overapproximation* (§3.4.6), so deltas routinely contain elements already in
`x`.  A delta that is non-empty but wholly contained in `x` makes `x` stop
growing while `dx` never reaches `⊥` — the `dx = ⊥` test then loops forever
where `dx ⊑ x` terminates.  §I.5 needs `⊑L` (per-type, generated alongside
`eqA`/`unionA`), not `eqL … bottomL`.

The same applies to naïve `fix`: the thesis uses `x' <: x`, not `x' == x`.

### D3. ⊥-insertion and ⊥-propagation are missing — **resolved**

`data.md` §I.7 proposes a test: "compiling `path` from §3.1 with a
duplicate-counting instrumented `for` gives Θ(n²) total work, not Θ(n³)."  Per
the thesis §4.2.3 that test **fails** for a compiler that implements only ϕ/δ:

> These asymptotic improvements depend on ⊥ propagation: *seminaïve raw* yields
> only a small constant-factor speedup over naïve, roughly 20%.

The thesis's compiler (fig. 4.1) has two extra passes after ϕ/δ that no spec
file mentions:

1. **propagate ⊥** — IL rewrites `e ∨ ⊥ ⇝ e`, `⊥ ∨ e ⇝ e`,
   `for (x ∈ e) ⊥ ⇝ ⊥`, `for (x ∈ ⊥) e ⇝ ⊥`,
   `let x = ⊥ in e ⇝ e{x↦⊥}`, `let x = e in ⊥ ⇝ ⊥`, `(⊥,⊥) ⇝ ⊥`, `πi ⊥ ⇝ ⊥`.
   `for (x ∈ e) ⊥ ⇝ ⊥` is the one that matters — it turns a loop whose length
   grows with the input into constant work.
2. **insert ⊥** — ϕ marks the terms δ is *known* to produce as zero changes
   (`δx` for discrete `x`, `δ[e] = ()`, `δ{ei} = δ(e=f) = δ(fix e) = δ⊥ = ⊥`)
   plus the derived cases (`let x = e in f` when `f` is a zero change; a
   variable let-bound to a zero change; `e1 e2 e3` when `e1` and `e3` are both
   zero changes — i.e. `δ(e f)` with neither side changing), and replaces them
   with `⊥` at semilattice type so pass 1 can fire.

The thesis measured pass 2 as effectively free but also effectively
unnecessary once pass 1 runs; pass 1 is mandatory.  `data.md` §0's pipeline
should have a "⊥-propagation" stage between ϕ/δ and lambda-lifting, and §I.4.3
should list the marks ϕ has to emit for it.

### D4. Change minimization (§4.3) is missing entirely — **implemented, benefit unmeasured**

Without it, seminaïve evaluation is *asymptotically* wrong on any relation with
a cycle — the thesis's own measurements (fig. 4.8) show 745s vs 1.5s at 400
nodes on a loopy line graph.  The cause: an element rediscovered at iteration
*i* stays in `dxi`, is treated as "new", and seeds redundant re-derivations in
every later iteration.  The fix is one line in the loop:

```
dx_{i+1} = (f' xi dxi) \L x_{i+1}
```

generalized by a per-semilattice operator `(\)L : L → L → L` obeying
"if `dx ▷ x ,→ y : L` then `dx \L x ▷ x ,→ y : L`", with
`dx \{A} x = dx \ x`, `(dx,dy) \L×M (x,y) = (dx \L x, dy \M y)`, and the
degenerate-but-lawful default `dx \L x = dx`.  §I.4.3's "what gets generated
per program" list should include `diffL` alongside `eqA`/`unionA`/`bottomL`/
`joinL`/`dummyA`, and §I.5 should show the minimizing loop.

Note the thesis's caveat: for a totally ordered semilattice (e.g. `N∞min` for
shortest paths) the degenerate default is the *only* valid minimizer.  If
Gestate adds such semilattices, it inherits that open problem.

### D5. Booleans are `{1}`, not a sum — **answered: gestate has both**

Neither of the two answers the original item offered.  Gestate keeps `Bool`
*and* adds Datafun's `{1}` under the name **`Prop`**, because the two are
not competing encodings of one concept — they are two different concepts
that happen to have two inhabitants each:

- **`Bool`** is the *discrete* boolean.  A two-constructor ADT, ordered by
  equality, what `==` returns, what `case` analyses, what `deriving` and
  `Show` produce.  Two `Bool`s can never be joined, and that is correct for
  what it is for: questions about data you already have.
- **`Prop = {()}`** is the *semilattice* boolean.  `{}` is false, `{()}` is
  true, `false < true` is set inclusion, `\/` is or, and `for (u in p) e` is
  the one-sided conditional.  It is for questions about data still being
  derived.

The deciding argument is the third bullet of the original item, made
concrete.  A predicate returning `Prop` may take its arguments at the
*monotone* arrow:

```
member : Box Int -> {Int} ~> Prop
```

so its truth grows as the set grows, and it may therefore be applied to a
fixpoint variable.  The same predicate returning `Bool` would need its set
argument discretely and would be unusable under `fix`.  That is a class of
Datalog query, not a stylistic preference, and answer (a) — ADT only —
loses it outright.  Answer (c) — `{1}` only — keeps it and pays by
rewriting `Eq`, the prelude, `deriving`, the FRP `Maybe`/`Sync` types and
every `case` in the test suite, to obtain a boolean that `case` cannot
analyse.

**`Prop` is a type alias, not a new type constructor.**  This is the load-
bearing half of the decision.  Every property that makes `Prop` worth
having *is* the set structure: ⊥ is `{}`, ∨ is set union, `for` is already
its eliminator, `Δ{()} = {()}` needs no new δ rule and no new entry in D8's
contract, and `{()}` is a fixtype so `fix` at it terminates in at most two
steps.  An opaque constructor would have to re-derive all of that by hand
and would gain only prettier `show` output.  The alias expands
structurally, exactly as `String = List Char` does, so `Prop` and `{()}`
are one type and unify freely; the cost, also `String`'s, is that a type
error prints the expansion rather than the name.

Three repairs were needed before `{()}` could be written at all, and all
three were defects independent of this decision:

- `()` was a value but not a *type* (`declarations.py` rejected the empty
  tuple) and not an instance head (`parse.py`'s `_parse_atomic_type`).
- `Tuple0` had no kind; the builtin table started at width 2.
- `is_eqtype(Tuple0)` answered `False` — a bare `TCon` never reached the
  product case in `_in_grammar` — so **`{()}` was neither a semilattice nor
  a fixtype**, which is exactly backwards.  Fig. 2.1 puts `1` in all four
  subgrammars; gestate had it in two.

What is settled, and what is not.  Settled: both types exist, `Prop` is the
alias, `Eq`/`Ord`/`Show` instances at `()` are in the prelude, and **`==`
keeps returning `Bool`** — the prelude, `deriving` and `Show` depend on it,
and since `=` is non-monotone in Datafun too, returning `{1}` would buy
nothing at the equality itself, only at its use site.  Deferred to D6 and
roadmap 2.1, which is where it belongs: the guard clause `| e`, `empty?`,
and the coercion between the two booleans.  The recommended shape for the
guard is a one-method class

```
class Guard a where guard : a ~> Prop
```

with instances at `Bool` and `Prop`, so `{e | C, g}` desugars to
`for (() in guard g) {e}` whichever boolean the author wrote.  This matters
because `desugar_program` runs *before* `infer_program` (`pipeline.py`), so
a type-directed guard desugaring is not available; a dictionary-resolved
method is, on machinery that already exists.  The one thing to verify when
it is built is that the `Bool` instance body passes the monotonicity
checker at the `~>` arrow — it should, since `Bool` is discretely ordered
and every function out of a discrete type is monotone.

`data.md` §III.1's parenthesis about "the semilattice structure booleans
get for `for`-loop desugaring" is now accurate about `Prop` and was never
accurate about `Bool`; it is corrected there.  `test/test_prop.py`.

The original item:

### D5 (original). Booleans are `{1}`, not a sum — and `data.md` III.1 says the opposite

Thesis §2.2 item 1: `bool` desugars to `{1}`, `true` to `{()}`, `false` to
`{}`, ordered `false < true`.  This is load-bearing:

- `for (e) f` (the elided-variable form) is the *one-sided conditional*
  `f if e else ⊥`, which is how set comprehensions get their guards
  (fig. 2.2: `{e | C}` → `for (C) {e}`, and `for (p ∈ e) f` →
  `for (x ∈ e) if p ⩿ x then f else ⊥`).
- `empty? e : 1 + 1` is the *only* way to case-analyse a boolean, and it is
  non-monotone precisely because `1+1` is ordered disjointly while
  `false < true`.
- It lets `P : A → bool` be a monotone predicate — the property §2.2 calls out
  as the reason not to use `1 + 1`.

`data.md` §III.1 in contrast says ADTs desugar to sums and adds "an ordinary
`Maybe` doesn't need the semilattice structure booleans get for `for`-loop
desugaring" — acknowledging the encoding without ever specifying it — while
`spec/syntax.md` and `spec/types.md` treat `Bool` as an ordinary two-constructor
ADT with `==`/`/=` returning it.  The specs need one answer: either Datafun's
`bool = {1}` (and then `Eq`'s `==` returns `{1}`, and `empty?` exists), or an
ADT `Bool` (and then the `for`-guard desugaring in fig. 2.2 has to be
re-derived, `empty?` has no meaning, and monotone predicates are lost).

### D6. Surface syntax for the Datafun sugars — **partly resolved**

Done, and specified in `syntax.md`: the **comprehension** `{e | C}`, the
full clause grammar `C ::= p ∈ e | e | C,D` for both `{…}` and `for`, and
the **guard clause**, which accepts either boolean through `Guard`'s
`guard : a ~> Prop` (D5).  The wildcard `_` already worked.  Transitive
closure is now writable as one comprehension with no helper
supercombinator — `test/test_comprehensions.py`.

Two things worth carrying forward.

**A guard needed no construct of its own.**  `for (e) f` *is* fig. 2.2's
one-sided conditional, so a guard desugars to a generator over `guard e`
binding a fresh unused variable, and everything downstream — ϕ/δ,
⊥-propagation, the match compiler — sees an ordinary `for`.  Dispatching
the coercion through a class rather than by inspecting the type is what
lets this run in the *parser*, which it must: desugaring finishes long
before inference starts.

**The multi-clause form was already documented and never worked.**
`desugar_expr` read `bindings[0]` and discarded every later clause, so
`for (x in a, y in b) e` — `syntax.md`'s own second example — compiled to
`for (x in a) e` with `y` free, reported as an unknown global rather than
as a scope error.  Nothing exercised it.  That is a stage-0-class defect
that stage 0 did not find, and the reason `fixme.md` F29's "no property
tests" is the highest-value item in stage 5.

Generated binders are now *unwritable* rather than merely unlikely: the
matcher's `_mN#hint` and the guard's `_guardN#` contain a `#`, which opens
a comment and so cannot occur in an identifier.  Before this, a program
using the name `_m1_elem` could read a generated binding in place of its
own — the same namespace hazard D10 records for variables starting with
`d`, and the only one of the two now closed.

**The remaining sugars are done too, at three spellings that had to be
decided rather than inherited** — Datafun's notation collides with syntax
gestate already had:

- **`empty?`** keeps its name.  A trailing `?` now belongs to an
  identifier (only one, only at the end, and greedily — so an infix `?`
  needs spaces).  It is a *primitive*, and had to be: `for` eliminates only
  into a semilattice, `Bool` is not one, so the non-monotone observation of
  a `Prop` has no definition in the language.  `holds = not . empty?` is
  the prelude reading.  Both take the plain `->`, which *is* `□A -> B`, so
  a fixpoint variable cannot be observed as it converges — checked.
- **`fix r => e`** in place of fig. 2.2's `fix X is e`, which would have
  reserved `is` to save one `Box`.  The parenthesised `fix (r => e)` means
  the same; an unboxed lambda could never be well-typed there, so nothing
  is stolen.  The box is still *inserted*, so its discipline is unchanged:
  a monotone variable captured under it is rejected exactly as before.
- **`Box p`** in place of `[p]`, which is unavailable — `[p]` is a
  one-element list pattern.  Irrefutable, and it lowers to `EUnbox`, so it
  binds discretely just as `unbox` does.  It matters because `unbox` is an
  expression form and cannot appear in a binder: `closure (Box e) = …`.

Transitive closure is now one line of Datalog:

```
closure : Box (Set (Cyclic 8, Cyclic 8)) -> Set (Cyclic 8, Cyclic 8)
closure (Box e) = fix r => e \/ {(x, w) | (x, y) in r, (z, w) in e, y == z}
```

Still open: `split` (which 0.2 records as having no runtime witness to fix,
□ being erased) and the equality-check pattern `!e`.  `!e` is now cheap and
was not before — it needs the ⊥ that fig. 2.2's refutable-pattern rule
requires, *unless* each `!e` sub-pattern is compiled to a fresh binder plus
an appended equality **guard**, which the clause grammar above now
provides.  `(!y, w) in e` becomes `(z, w) in e, y == z` — exactly the join
the closure query writes by hand.

The original item:

### D6 (original). `spec/syntax.md` has no surface syntax for `empty?`, `split`, or the Datafun sugars

`empty?` and `split` are core Datafun terms (fig. 2.1) and both appear in
`data.md`'s ϕ/δ table; neither appears in `syntax.md`.  Nor do fig. 2.2's
sugars that `data.md` §III.3 assumes exist: the equality-check pattern `!e`
(listed in III.3's routing table but not in `syntax.md`), the wildcard pattern
`_`, box patterns `[p]` (`syntax.md` has only `unbox pat = expr in expr`),
`fix X is e` as a binding form, and the multi-clause comprehension
`{e | C}` / `for (C) e` with `C ::= p ∈ e | e | C,D`.  `syntax.md` gives only
`for (pat in expr, pat2 in expr2) expr`, which covers `C,D` but not the
boolean-guard clause `| e` that makes comprehension filters work.

### D7. `data.md`'s ϕ/δ table omitted several rules from fig. 3.2 — **resolved**

**All of these are now in `data.md`**: `ϕ(e = f)` and `ϕ(empty? e)` as table
rows, `split` as a row plus §I.4.4 giving fig. 3.2's rule and — the part the
thesis assumes and no spec stated — *why* it has that shape, namely that Φ
does not commute with □ over a sum, so the value's tag and the change's tag
are carried separately and nothing forces them to agree.  Both `split` rows
say plainly that **gestate does not reach them**: □ is erased, so the outer
`case ϕe` is the split and the mismatch has no runtime witness.  `δ(case …)`
is now marked as *not* distribution at the point of use.

One row is new rather than restored: `empty? e` exists in gestate now, and
its δ is a zero change *because its argument is discrete* — §I.8's Rule 2
and the `□Prop → Bool` arrow agreeing, rather than two separate facts.

The original item:

Missing outright:

- `ϕ(e = f) = (ϕe = ϕf)` — the table lists `e = f` only under the δ column.
- `ϕ(empty? e) = empty? ϕe`.
- `ϕ(split e)` — the table says "see figures 3.2/3.3" but never reproduces it,
  and it is the *second* place `dummy` is needed:
  ```
  ϕ(split e) = let [z] = ϕe in
               case split [π1 z] of
                 (ini Y ▹ let [x] = Y in
                          case split [π2 z] of
                            ini DY  ▹ let [dx] = DY in ini [(x, dx)]
                            in(i+1 mod 2) _ ▹ ini [(x, dummy x)])i
  ```
  The reason is a genuine type mismatch the spec never explains:
  `Φ(□(A+B)) = □((ΦA+ΦB) × (ΔΦA+ΔΦB))` (a boxed pair of tagged values) but
  `Φ(□A+□B) = □(ΦA×ΔΦA) + □(ΦB×ΔΦB)` (a tagged boxed pair).
- `δ(split e) = let [y] = ϕe in case π1 y of (ini _ ▹ ini ())i` — the type is
  `1+1`, so the tag must be recovered from `ϕe`; §I.4's table shows only
  `empty? ϕe`.
- `δ(ini e) = ini δe` and `δ(πi e) = πi δe` are given as "distribute", which is
  right, but `δ(case …)` is *not* distribution and the table's "see below"
  should say so at the point of use.

### D8. The change-structure interface is never stated, so new semilattices/primitives have no contract

`data.md` §I.7 says the spec "inherits" the correctness proof.  What it does
not inherit is the *interface* that proof quantifies over.  Anyone adding a
semilattice (music durations, `Cyclic n`, bounded integers) or a primitive
(`+`, `prim_eq_int`, `prim_lt_int`) needs Definitions 14/15:

- **Change structure** (Def. 14): posets `VA`, `ΔA` and a relation
  `dx ▷ x ,→ y : A` satisfying *functionality* (`y` determined by `dx,x`),
  *soundness* (`x ⩽ y`), and *zero changes* (some `dx` with `dx ▷ x ,→ x`).
- **Derivative** (Def. 15): `f' : □VA → ΔA → ΔB` with
  `dx ▷ x ,→ y ⟹ f' x dx ▷ f x ,→ f y`.
- The semilattice change structure: `VL = ΔL = L`, `dx ▷ x ,→ y ⟺ x ∨ dx = y`.

Cai et al.'s *A Theory of Changes for Higher-Order Languages* is the source
for the higher-order half of this and is **not cited by any spec file**.  Its plugin discipline is exactly what
Gestate needs and lacks: a plugin supplies, per base type, a change
representation, and per primitive, an incremental version.  Gestate has base
types and primitives Datafun does not (`Int`, `+`, `*`, `-`, comparison), and
the specs say nothing about their derivatives.  The honest minimum is a rule
along the lines of "every non-set base type carries the trivial change
structure `ΔA = 1` and every primitive over it is treated as discrete", which
is sound but must be *written down*, because `δ` currently has no case for
them.

**What the implementation now assumes** (`gestate/changes.py`, added for
`fixme.md` F3/F4).  δ can no longer avoid the question — every zero change is
built at its own type — so it works to exactly the rule above, plus fig. 3.1's
structure:

| type | `ΔA` | zero change |
|---|---|---|
| `{A}` | `{A}` | `⊥` |
| `A × B` | `ΔA × ΔB` | componentwise |
| `A + B` (every gestate ADT, `Bool` included) | `ΔA + ΔB` | `dummy (ini x) = ini (dummy x)`, generated per type |
| `A → B` | `□A → ΔA → ΔB` | `λx. λdx. dummy (f x)` |
| `Int`, `Char`, `Cyclic n`, `lo .. hi`, `□A`, and every Rizzo former | `1` | `()` |

This is a *working rule*, not a decision: it is what the code needs to emit
well-typed zeros, and it is written here so that whatever this item concludes
has something concrete to confirm or overrule.

**The derivative of a primitive function is no longer optional, and half of
it is now implemented.**  This entry used to end "nothing reaches it today".
That stopped being true the moment comprehension guards landed (D6): a guard
calls the `Guard` class method, so a guard under a `fix` asks δ to
differentiate a *dictionary method*.  δ had no rule, emitted the discrete
`()`, and **applied it**.  `UNIT` is `ENum(0)` and `Unwind` on a number
ignores the spine, so the program did not fail there — it failed later, as
`CaseJump on non-constructor`, with nothing pointing at the cause.
`{x | x in r, x < 3}` under a `fix` is about the most ordinary Datalog query
there is, and it crashed.

The rule now in force, and the first real content of this interface:

> A **saturated primitive application** is discrete.  Every argument type
> has the trivial change structure, so the result cannot change either, and
> `δ(p e₁ … eₙ)` is the **zero change at `p`'s result type** — not `δp`
> applied to anything.  `δ(prim_eq_int x y)` is `dummy` at `Bool`.
> A *partially* applied primitive is still a function and gets no such rule.

Two supporting changes were needed to make the rule reachable:

- **`πᵢ __dict_C_T__` is resolved at compile time** to the method global it
  selects (`elaborate.resolve_static_methods`).  A context-free dictionary
  is a constant, so the projection has one answer; more importantly ϕ/δ has
  no rule for a projection out of a discrete value, and δ was returning the
  `EProj` node unchanged, to be applied to two arguments — `fixme.md` F57's
  shape.
- **Instance methods are no longer skipped by the ϕ/δ gate.**  They shared
  the `__` prefix with dictionaries and were skipped with them.  A method
  body is ordinary user code and a `fix` that calls one needs its
  derivative.  Dictionaries *are* still skipped, correctly: they are
  discrete data, `Δdict = 1`.

And δ now **refuses** rather than lying: applying a unit raises a compiler
error naming this item, instead of emitting code that dies as a G-machine
fault. That is stage 0.4's rule — a derivative the plan cannot supply is an
error, not a zero.

**Definitions 14–16 are now written down**, in `data.md` **§I.8**, with the
Cai et al. citation this entry asked for: the three change-structure
properties, the derivative law and its `□`, the set and semilattice instances,
the table above, and Rules 1 and 2 as the obligations a gestate plugin
discharges.

What remains open is not the statement but a *case* it deliberately does not
cover: a primitive over a **semilattice**, whose argument may genuinely change.
Rules 1 and 2 cover every primitive gestate has, because all of them are over
discretely-ordered arguments.  §I.8's last subsection states the obligation such
a primitive takes on, and names the first thing that would incur it — `Score`,
if `music.md`'s overlay turns out to be idempotent.

### D9. `data.md` §I.4.3's monomorphization premise does not hold in Gestate

§I.4.3 justifies per-type helper generation with "Datafun as given has no
polymorphism, so every use site is a known ground type."  True of the thesis's
compiler (§4.2.2 even notes it had to replace `A_eq` with a concrete type by
hand).  Not true of Gestate: `types.md` §3 specifies let-generalization and
`typeclasses.md` §7.1 specifies dictionary passing *precisely so that*
whole-program monomorphization is not required, and §7.1 calls out polymorphic
recursion as a case monomorphization cannot handle at all.

So either (a) Datafun-typed code is a monomorphic sublanguage and the spec must
say where the boundary is and how it is enforced, or (b) the set operations
become a class (`class Semilat a where (⊑) ; unions ; diff ; dummy`) resolved
by the ordinary dictionary machinery — which is exactly what the thesis did in
Haskell (fig. 4.2, `class Semilat`).  Option (b) also removes the need to
enumerate set types at compile time.  As written the two specs contradict.

### D10. Minor omissions worth recording — **resolved**

All four are now in `data.md`: the reason for boxing `fix`'s argument and
the `2n`-variable intuition in §I.2, `for` as a big *join* in §I.2's lemma
list, and the `d`-prefix constraint in §I.2 with the caveat that a
constructed collision did not misbehave, so it is recorded as an unenforced
assumption rather than a live bug (`fixme.md` F67).  Weakening and the
`disc` rule remain cited rather than reproduced.

The original item:

- `fix` is typed as taking a **boxed** function `□(fixL → fixL)` and the thesis
  says why (§2.3.1, §3.3.5): a zero change to a function *is* a derivative for
  it (Thm 2.9 in the changes paper; §3.3.3 in the thesis), so boxing the
  argument is what makes `f'` available at `fix` without decorating every
  function in the program with a derivative.  `data.md` states the rule but not
  the reason, which is why it reads as arbitrary.
- Weakening (Thm 22) and the `disc` rule (`Γ, X : A ⊑ ∆, x :: A`) are cited in
  §I.3 but the relation itself (fig. 3.4) is not given.
- `for` denotes `collect(f)` — a **big join**, not a big union (§2.3.2).
- The 2ⁿ-variable intuition ("an expression with n variables has a derivative
  with 2n variables") and the naming convention that source programs contain no
  variable starting with `d` (footnote 9, p. 58) — the latter is a real
  constraint on Gestate's identifier namespace, since ϕ/δ mint `dx` from `x`.

---

## 2. Rizzo (Bahr) → `spec/frp.md`, `spec/data.md` Part II, `spec/syntax.md`

### R1. No spec states Rizzo's typing rules — **resolved**

`spec/syntax.md` §"Rizzo-originated surface syntax" now gives the whole
interface at these types, and `gestate/infer.py` implements it.  `⃝∀` is the
type constructor `FaL` and `⃝∃` is `ExL`; before this they were both spelled
`Sig`, which is why R2/R3 and `fixme.md` F14/F15 all existed.

Two decisions the paper leaves to the implementation:

- `Maybe a = Nothing | Just a` and `Sync a b = SyncLeft a | SyncRight b |
  SyncBoth a b` are **built-in data types with fixed constructor tags**, not
  library code.  `watch` and `sync` name them in their own signatures, and the
  reactive driver has to recognise a `Just` and build a `Sync` with no
  constructor table to hand.  A user declaration of either name is rejected.
  Naming the three `Sync` cases rather than nesting `(A+B)+(A×B)` also saves
  every `cont` function a nested `case`.  This is what settles R4 and R6.
- `⊛`, `5` and `▷` are written `<*>`, `<@>` and `|>`, all `infixl 4`.

The rules a front end has to implement:

```
delay : A → ⃝∀A                    ⊛ : ⃝∀(A→B) → ⃝∀A → ⃝∀B
never : ⃝∃A                        ⊛5 : ⃝∀(A→B) → ⃝∃A → ⃝∃B
wait  : Chan A → ⃝∃A               watch : Sig (A+1) → ⃝∃A
sync  : ⃝∃A₁ → ⃝∃A₂ → ⃝∃((A₁+A₂) + (A₁×A₂))
head  : Sig A → A                  tail  : Sig A → ⃝∃(Sig A)
(::A) : A → ⃝∃(Sig A) → Sig A      chanA : Chan A
Γ, x : ⃝∀A ⊢ t : A  ⟹  Γ ⊢ fix x.t : A
Γ, x : A[(μα.A)×B/α] ⊢ s : B ,  Γ ⊢ t : μα.A  ⟹  Γ ⊢ rec(x.s, t) : B
```

Also missing: the `Sync A B = (A+B)+(A×B)` shorthand with `left`/`right`/`both`
and `Maybe A = A + 1` with `just`/`nothing`, both of which the paper's
combinators (`switch`, `zip`, `interleave`, `filter`) are written against.

### R2. `⊛` and `5` have no surface syntax — **resolved**

They are now `<*>` and `<@>`, both `infixl 4`, with `|>` as sugar for `▷`;
`syntax.md`'s fixity table and FRP section carry all three.  `map`, `mkSig`,
`const`, `sample`, `filter` and `sync`-based combinators are expressible and
exercised in `test/test_frp.py`.  The original gap:

`syntax.md` §"Rizzo-originated surface syntax" lists `gfix`, `Sig`, `Chan`,
`FaL`, `ExL`, and says "delay, head, tail, chan are ordinary functions".  There
is no notation for `⊛ : ⃝∀(A→B) → ⃝∀A → ⃝∀B` or `5 : ⃝∀(A→B) → ⃝∃A → ⃝∃B`, and
no fixity entry for either.  `frp.md` compiles `EApp∀`/`EApp∃` but nothing
produces them.

Without those two operators none of §2–3 of the paper is expressible: `▷` is
*defined* as `f ▷ x = delay f 5 x` and is the only way to move a function
across `⃝∃`.  `map`, `mkSig`, `const`, `sample`, `zip`, `scan`, `switch`,
`switchS`, `switchR`, `interleave`, `filter` and the whole GUI example all go
through `▷` or `⊛`.  `syntax.md` needs entries for `⊛`, `5`, and preferably
`▷` as sugar, with fixities.

### R3. `syntax.md`'s guarded-recursion example is ill-typed — **resolved**

`syntax.md` now gives `const x = x ::: never` and the `mkSig` fixed point
instead, and states that the old example does not type.  With `FaL`/`ExL`
distinct the type checker rejects it (`test_frp.py`), which is also what
let the `ticked` hack behind `fixme.md` F15 go.  The original diagnosis:

```
counter : Sig Int
counter = gfix self => 0 ::: delay self
```

`::` has type `A → ⃝∃(Sig A) → Sig A`, but `fix x.t` binds `x : ⃝∀A` so
`self : ⃝∀(Sig Int)` and `delay self : ⃝∀(⃝∀(Sig Int))`.  Neither is `⃝∃`.
There is no `⃝∀ → ⃝∃` coercion in the language — `5` is the only bridge and it
needs an `⃝∃` argument to supply the clock.  A constant signal in Rizzo is
`const x = x :: never`; a driven one is `mkSig d = (λa. a :: mkSig da) ▷ da`,
i.e. `fix r. λd. delay (λr'. λx. x :: r' d) ⊛ r 5 d` (§4.5).  The example
should be replaced by one of those, and the general desugaring scheme (R5)
should be spelled out.

### R4. The `Maybe`/`in1` convention for `watch` is unspecified — **resolved**

Gestate names the injections rather than numbering them: `Maybe a = Nothing
| Just a` is a built-in data type at reserved tags, and `watch l` fires when
`l` updates to a `Just`.  The in1/in2 question does not arise, and
`data.md` §III.1's desugaring is irrelevant to it because `Maybe` is not
desugared to a sum.  The original disagreement:

`watch : Sig (A+1) → ⃝∃A` fires when the signal updates to `in1 v`
(paper: `Maybe A = A + 1`, `just t = in1 t`, `nothing = in2 ()`;
`ticked^κ_η(watch l) ⟺ ∃v,w. η(l) = in1 v⟨⊤⟩w`).

- `data.md` §III.1 desugars `Maybe a = Nothing | Just a` to `1 + a`, so
  `Nothing = in1 ()` and `Just x = in2 x` — the **opposite** injection.
- `frp.md`'s `ticked` writes `NCon 1{-inr-}` and comments it as
  `"in1 v ⟨⊤⟩" i.e. current value is Just-shaped` — calling tag 1 both `inr`
  and `in1` in one line.

Nothing anywhere fixes the tag numbering (is `in1` tag 0 or tag 1?).  Since
`watch` is the mechanism by which partial signals join clocks, and `filter` is
built on it, this has to be pinned down: one sentence stating the injection
numbering, and one stating whether `Maybe` is `A+1` (paper) or `1+A`
(`data.md`).

### R5. The surface-to-core desugaring for recursive definitions — **mostly resolved**

The general scheme is implemented in `gestate/desugar.py`
(`_guard_recursion`) and documented in `syntax.md`: a definition whose
recursive calls all sit under a `delay` becomes a `gfix` with each guard
rewritten to `delay (\r'. t[r'/f]) <*> r`.  `mkSig`, `map`, `const`,
`filter` and `switch` are all writable as the paper writes them
(`test/test_frp.py`).  Two decisions the paper does not force:

- The rule fires only when at least one recursive call is under a `delay`,
  which is what keeps ordinary recursion (`fact`) out of it.  A definition
  with some calls guarded and some not is *rejected* rather than left
  alone — Rizzo requires every recursive call to be guarded, so such a
  definition is not productive under either reading.
- Pattern matching on `x :: xs` is `x ::: xs`, an irrefutable pattern
  binding `head`/`tail` (so `xs : ExL (Sig A)`).  Its parts must be
  variables; a nested pattern would need a refutable match on `head s`,
  which the binding form cannot express.

Still missing: recursion over `μα.A` via `rec(x.s, t)`, which needs
recursive types — gestate has no `μ` type former at all, so `frp.md`'s
`rec`/`fmap_F` remains unimplemented rather than merely undocumented.
Mutual guarded recursion is also out of scope: the scheme is stated for a
single `f`, so `switch`/`cont` compile as ordinary mutually recursive
supercombinators (correct, but with no productivity guard).  The original
item:

§2.4 gives a general scheme, and every combinator in the paper is written in
the surface form:

```
f x₁ … xₙ = C[delay t₁, …, delay tₙ]        (f not free in C)
  ⇝  f = fix r. λx₁ … λxₙ. C[delay(λr'. t₁[r'/f]) ⊛ r, …, delay(λr'. tₙ[r'/f]) ⊛ r]
```

plus pattern matching on `x :: xs` becoming `head`/`tail`, and recursion over
`μα.A` becoming `rec(x.s, t)` (worked in the paper for `length`).  `data.md`
§III.3's routing table names both backends but gives no rule; `frp.md` says
`rec`'s `fmap_F` "desugars to a fold" without saying how; `syntax.md` exposes
only the raw `gfix`.  As written, a user must hand-write `fix`/`delay`/`⊛`,
which is precisely the bureaucracy Rizzo's surface syntax exists to avoid.

### R6. `frp.md`'s `advance` for `sync` builds the wrong shape — **resolved**

`packLeft1`/`packLeft2`/`packBoth` are now `SyncLeft`/`SyncRight`/`SyncBoth`,
the three constructors of the built-in `Sync a b` (see R1), at reserved tags
the driver can build without a constructor table.  `frp.md` should be updated
to name them.  The original diagnosis:

The paper's rules:

```
ticked(v_i) ∧ ¬ticked(v_{3-i})  ⟹  ⟨sync v₁ v₂⟩ ⇒ in1 (in_i v)
ticked(v₁) ∧ ticked(v₂)         ⟹  ⟨sync v₁ v₂⟩ ⇒ in2 (u₁, u₂)
```

i.e. the result is a value of `Sync A B = (A+B)+(A×B)` — an ordinary
sum/product that user code (`cont`) pattern-matches.  `frp.md` writes
`packLeft1 v'`, `packLeft2 w'`, `packBoth v' w'` and never defines them.  They
must be `Pack in1∘in1 / in1∘in2 / in2` over the *ordinary* constructor tags,
not over the `tagSync` reserved tag.

### R7. The clock function `cl_η(v)` and the ticked/cl invariant — **resolved**

`reactive.cl` implements the six rules below and `reactive.clock_fires`
the invariant.  A clock is a set of *sources* — `("chan", id)` for
channels and `("sig", cell)` for watched partial signals — because both
kinds appear on the right of the invariant.

The pre-step reading is the point, so it is what the driver enforces:
`reactive_step` snapshots every earlier-heap signal's clock *before*
touching a cell, and `_update_one` then checks each `ticked` answer
against that snapshot.  A driver that recomputed clocks mid-sweep would
disagree and say so.  The check is on by default (`GmReactive.check_clocks`).
The original item:

`data.md` §II.6 says to compile "`ticked`/`cl`" but neither spec defines `cl`:

```
cl(never) = ∅            cl(wait κ) = {κ}          cl(watch l) = {l}
cl(v 5 w) = cl(w)        cl(sync v w) = cl(v) ∪ cl(w)
cl(tail l) = cl(w)   where η = η₁, l ↦ v⟨U⟩w, η₂
```

and the invariant that ties it to `ticked` (§4.3, p. 17):

> `ticked^κ_{η_N}(u)` iff `κ ∈ cl_η(u)` or there is some `l ∈ cl_η(u)` with
> `η_N(l) = in1 v₁⟨⊤⟩v₂`.

with the crucial note that `cl_η` is taken **with respect to the heap from
before the step**, because the timing information in `η_N` is for the *next*
step.  A driver that recomputes clocks mid-sweep is wrong; the spec gives no
way to notice this.

### R8. `head` is only defined on the *now* heap — **resolved**

`NSig` carries a `current` flag: the ✓ frontier as a per-cell mark, which
is what §II.5 proposed.  `reactive_step` clears it on every signal moving
to the earlier heap and `_update_sig` sets it again as the sweep reaches
each cell.  `SigHead` raises on a cell that is still behind the frontier,
and so do `ticked`/`advance` for `watch l` and `tail l` — fig. 10 states
both of those against η_N, so they need `l` already swept for the same
reason.  `data.md` §II.5 should be amended: the split is a proof device
for *performance*, but the mark is load-bearing for diagnostics.  The
original item:

The paper's rule is
`⟨t;ε⟩ ⇓ ⟨l; η_N ✓ η_E/Δ⟩, η_N(l) = v⟨U⟩w ⟹ ⟨head t;ε⟩ ⇓ ⟨v; …⟩`.
There is deliberately **no rule** for `head` on a location in the earlier heap
— such a program is *stuck*, and §4.6.3 says that is the whole basis of the
no-space-leak guarantee ("any attempt of the program to dereference a signal
from that heap would result in a stuck execution, which Theorem 4.1 rules
out").

`data.md` §II.5 dismisses the split as "a proof device more than an
implementation requirement".  That is right about *performance* and wrong about
*diagnostics*: with one heap and in-place update, a `head` on a stale signal
silently returns last step's value instead of getting stuck, so a
scheduler-ordering bug becomes a wrong answer rather than an error.  The spec
should keep the ✓ frontier as an assertion (a per-cell "visited this step"
mark, which §II.5 already proposes) and require `SigHead` to check it.

Relatedly, §4.4's in-place-update optimization is justified *because* `l` is in
the earlier heap when its tail is advanced ("we can rule out that the process
of advancing the tail of `l` will itself read from `l`").  `data.md` §II.4
quotes the optimization but not its side condition.

### R9. β and η are not equivalence-preserving — **resolved**

**The rule is now written into `frp.md`**, where the reason lives, as a
constraint on every optimizer rather than on any one of them: *no β or η
rewriting across `head`, `delay`, `⊛`, `5`, or a `Sig`-typed subterm*.
`typeclasses.md` §7.2 now says its specializer is bounded by it — inlining
*is* β — and `roadmap.md` closes specialization partly on those grounds.
Nothing in gestate does β/η today, which is why adopting the rule costs
nothing now and would be expensive to retrofit.

The original item:

§4.3, last paragraph: `(λx. delay x) (head xs)` differs from
`delay (head xs)`; `f (head xs)` differs from `λx. f (head xs) x`.

This is a constraint on every optimizer in the pipeline, and two specs propose
optimizers that would violate it: `typeclasses.md` §7.2 (specialization
"during or after inlining", "let ordinary inlining then fully eliminate the
dictionary indirection") and `supercomb.md`'s lambda lifting, which floats
lambda bodies to the top level.  `frp.md` flags one instance of this ("if you
ever add a G-machine optimization that eagerly normalizes `NCon` fields, this
breaks") but not the general rule.  The specs need: *no β/η rewriting across
`head`, `delay`, `⊛`, `5`, or a `Sig`-typed subterm.*

### R10. Type-formation side conditions were understated — **resolved**

**Stated in `data.md` §I.4.5**, with what it buys: it is exactly what makes
`μα. A + Sig (A × α × A)` legal and `μα. 1 + (α → α)` not, which §III.2's
"recursive ADTs inherit Rizzo's μ restriction" depends on.

The original item:

Fig. 2 requires **both** premises closed for arrows: `⊢A:type` and `⊢B:type`
give `Φ ⊢ A→B : type`.  `data.md` §II.1 records only "requires `⊢B:type`".
Same for `Chan A`, `⃝∃A`, `⃝∀A` (all take `⊢A:type`, closed).  Only `Sig A`,
`×`, `+`, `1` and `μα.A` propagate the open context `Φ`.  This is what makes
`μα. A + Sig(A × α × A)` legal while `μα. 1 + (α → α)` is not, and `data.md`
§III.2 relies on it.

### R11. Dynamic channel allocation is not in the driver spec — **resolved**

`GmState` carries `chans : Map Int Type` (exposed as `GmReactive.chans`),
`NewChan` extends it, and because `advance` runs its sub-evaluation on a
state sharing that dict, a channel minted while a sweep is in progress is
registered too.  `react` rejects an input naming a channel the program has
not allocated, which is the premise `κ : Chan B ∈ Δ_n` the productivity
theorem assumes.

The element type comes from inference, which records it on the `EChan`
node; the heap is untyped, so at run time it is a label for diagnostics
rather than something the machine checks a value against.  Note Δ is a
*runtime* context: a declared but never-forced `c = chan` was never
allocated and is not in it.  The original item:

`chan_A` extends the channel context (`⟨chanA; σ/Δ⟩ ⇓ ⟨κ; σ/Δ, κ:Chan A⟩`), and
the advance semantics may allocate channels too ("the advance semantics may
allocate new signals on the now heap and create fresh channels").  `frp.md`'s
`GmReactive` carries `chans :: Map Int Type` but `reactiveStep`/`react` never
touch it, and there is no notion of the environment's channel context growing
across steps — which matters for well-formedness of inputs (`κ : Chan B ∈ Δ_n`
is a premise of the productivity theorem) and for the GUI example, where every
`simpleButton` mints a channel at runtime.

### R12. The worked `filter` trace is missing — **resolved**

`test/test_frp.py::test_watch_fires_only_on_just` is the value regression;
the trace is now written into `frp.md` beside §4.5's `sample` one, with the
allocation-order invariant stated for `watch l` as well as `tail l`.

The reason the two traces differ turned out to be worth stating plainly, and
is now the heart of that section: `sample` inherits a **channel** clock
through `tagTail`, while `watch l`'s clock is `{(sig, l)}`, a **signal**
clock.  Whether the watcher fires depends on the value `l` holds *this*
instant, so `ticked` must read `l` after `l` has been updated in the same
sweep — which is precisely why allocation order is load-bearing here, and
not a separate rule needing its own justification.  Asserted against heap
shapes rather than values (`fixme.md` F22).  The original item:

`frp.md` reproduces §4.5's `sample` trace.  It omits the `filter` trace, which
is the one that exercises `watch`: `l1 : Sig (Maybe Int)` must be updated
*before* `l2 = mkSig (watch l1)` is consulted, and `l2` must **not** update on
the step where `l1` becomes `nothing`.  `frp.md` states the allocation-order
invariant only for `tail l`; it holds for `watch l` too and for the same
reason.  This trace is also the natural regression test for the `Maybe` tag
convention in R4.

### R13. `data.md` §II.2's open question — **partly answered**

`Sig {Int}` is well-formed and a Datafun `fix`/`for` does run over a
signal's value, demonstrated in
`test_monotone.py::test_a_signal_carrying_a_datafun_fixed_point`.  What
the experiment does *not* settle is the composition of the two
restrictions below, and R14 records the reason it cannot yet be settled
usefully: the query has to be closed, because there is no way to feed it
a value the signal produced.  The original analysis:


§II.2 flags it honestly: is `Sig {Int}` well-formed, and may a Datafun
`fix`/`for` run over a signal's current value each tick?  Checking it against
the paper: fig. 2 permits `Sig A` for any `Φ ⊢ A : type`, so the *type* is
fine, and the metatheory (§4.6) constrains only the shape of delayed
computations, not the payload — so nothing in Rizzo forbids it.  What does
constrain it is Datafun's side (D1): `{Int}` is not a fixtype, so a per-tick
`fix` over it is not guaranteed to terminate, and Rizzo's productivity theorem
assumes evaluation terminates.  The two restrictions have to be composed:
*a `fix` inside a signal body must be at a fixtype*, which is a stronger
statement than either paper makes alone.

### R14. §II.2's "every Rizzo construct is non-monotone" — **resolved, differently**

§II.2 proposes folding Rizzo into Datafun by adding every Rizzo-native
construct to the non-monotone list — "same mechanism, same enforcement,
zero new type-checker machinery".  Taken literally it rejects the paper's
own combinators.  Datafun's `λ` binds *monotone* (`ϕ(λX. e) = λX. ϕe`
commits to it: the lambda gets one parameter per binder and no change
parameters), so in

```
map f (x ::: xs) = f x ::: (map f |> xs)
```

the `:::` would strip `f` and `x` from scope and `map` would not type.
Every combinator in §2–3 of the paper has this shape.

The `□` half of the rule *is* implementable and is now implemented
(`gestate/monotone.py`): a box may not close over a monotone variable,
which is Datafun's own fig. 2.3 rule and is what the ϕ/δ transform
already assumes.  But it exposes the same problem from the other side:

```
map (n => close (Box {n})) xs      -- rejected: `n` is monotone
```

Values arriving from the FRP side are λ-bound, hence monotone, and a
monotone variable can never be boxed.  So the two halves compose only
when the Datafun computation is closed or reads its inputs from globals —
which is a demo, not an integration.

What is missing is the thing Datafun has and gestate does not: a way to
*ask* for a discrete argument.  In Datafun a function that needs one takes
`□A → B` and the caller supplies `[e]` with `e`'s own variables discrete.
Gestate has `Box` as a type but every arrow is the same arrow, so there is
no monotone/discrete distinction for a function to make.  Two ways out:

- **(a) Give gestate monotone and discrete arrows.**  An ordinary `a -> b`
  binds discretely and Datafun's monotone arrow becomes a separate former.
  This is the thesis's own answer, and D9's dictionary discussion already
  points at needing the distinction in the type system rather than in a
  side condition.
- **(b) Declare the Rizzo fragment discrete throughout.**  Its constructs
  stay non-monotone but their binders bind discretely, which keeps the
  paper's combinators legal.  The cost lands on ϕ/δ: `ΦΓ` gives a discrete
  `x` both `x` and `dx`, so `f_phi` would need change parameters for those
  binders, and `ϕ(e f) = ϕe ϕf` no longer matches its arity.

**Resolution: (a).**  Gestate now has both arrows.  `A ~> B` is Datafun's
function space and `A -> B` is `□A → B`; ordinary code keeps `->` and so
binds discretely, which is what lets a signal's value reach a Datafun
query:

```
map (n => close (Box {n})) xs      -- accepted: `n` is discrete
```

`fix` demands `□(L ~> L)`, so the monotonicity that makes the least fixed
point exist is now checked rather than assumed.

One judgement the papers do not force, because Datafun has no second
arrow to raise it: a binder is marked monotone only where its type is
*known* to carry an order coarser than equality (`types.has_nontrivial_order`).
At a discrete order every function is monotone, so the flavours coincide
there and the discipline is silent — which is why `Int`, `Sig A`, `Chan A`
and every FRP combinator are unaffected.  Type *variables* answer "not
known", i.e. they are treated as discrete.  That is an over-approximation
in the permissive direction, and deliberately so: the strict reading marks
every `case` binder in polymorphic code monotone and rejects ordinary
programs, while a body polymorphic in `a` cannot do anything
order-sensitive with an `a` in the first place.  It should be revisited if
gestate ever gains the eqtype subgrammar (D1), which is where the strict
reading would start paying for itself.

§II.2's own proposal — adding the Rizzo constructs to the non-monotone
list — remains rejected for the reason above: it does not survive contact
with `map`.

---

## 3. Papers cited by no spec

**Resolved.**  Cai et al. is now cited from `data.md` §I.1
and used in **§I.8**, the change-structure interface, which states thesis
Definitions 14–16 and gestate's own plugin obligations.  Cai et al.'s
contributions are attributed where they are used: the **plugin discipline**
§I.8 is an instance of (a plugin supplies base types and primitives, each with
a change representation and an incremental version, and the transform is
parametric in it), and **Theorem 2.9**, "nil changes are derivatives", which is
the other side of Definition 15's `□` on the base point and so of why `fix`'s
argument is boxed (D10).

This was the last paper cited *only* by this file's scope header.  The other
two are referred to throughout the specs by section (`thesis §3.3`,
`Rizzo §2.4`) rather than by filename, which is the same thing said less
explicitly.

---

## 4. Contradictions between spec files

Not paper errata, but they must be resolved before either half is
implementable as written.

### S1. `data.md` §II.4 and `frp.md` specified two incompatible machines — **resolved**

| | `data.md` §II.4 | `frp.md` |
|---|---|---|
| signal node | `NSignal Addr Addr Bool` | `NSig Addr Addr Bool` |
| channel node | `NChan [Addr]` — a *queue of pending values* | `NChan Int` — an *identity* |
| later values | `NDelayN Addr`, a distinct node kind | `NCon Tag [Addr]`, tags 90–96 |
| instructions | `MkSignal`, `UpdateSignal n`, `Advance`, `ChanRecv` | `SigCons`, `SigHead`, `NewChan`, `MkDelayAp` |
| `Unwind` | needs a new guard for `NDelayN` | needs nothing (`NCon` is already WHNF) |

**`data.md` §II.4 now points at `frp.md`** instead of restating it, keeping
only what is unique to it — *why* the machine must change at all, and that
`Update n`'s one-shot indirection is memoization rather than the repeated
in-place overwrite a `Sig` cell needs — plus a table mapping the old names
to the real ones for anyone reading the older text.  The substantive
difference is recorded there too: the queue-shaped `NChan` was the only
place either spec accounted for input delivery, which `frp.md` handles by
passing the value down through `advance`.

The original item:

Neither file mentions the other's design.  `frp.md`'s is the more economical
(it reuses `Pack`, which is correct given the paper's "they behave similarly to
strict constructors") and is the one the implementation follows; `data.md`
§II.4–II.6 should be rewritten to reference `frp.md` rather than restate it
differently.  Note also that `data.md`'s queue-shaped `NChan` is the only place
either spec accounts for input delivery, which `frp.md` handles by passing the
input value down through `advance` — worth keeping the distinction in mind, but
only one of them can be the spec.

### S2. `data.md` §0's pipeline did not match the real one — **resolved**

**Rewritten against the real pipeline.**  §0 now lists the stages that
exist — exhaustiveness before desugaring, the match compiler, kind and
monotone and subgrammar checks, helper generation, change structures,
⊥-propagation — with the Datafun-only block bracketed, and states the four
places where **order is load-bearing** and why each one is.  It also settles
the scope question below: ϕ/δ is applied per supercombinator *and per half*,
not to every function.  `journal.md` Part I's diagram was the same
drift and is corrected too (`fixme.md` F40).

The original item:

§0 orders "ϕ/δ transform → □/⃝∀ erasure → set canonicalization codegen →
Rizzo lowering → lambda lifting"; `journal.md` Part I orders "Datafun
desugar → ϕ/δ transform → lambda lift".  Also, §0 says ϕ/δ applies to
"Datafun-typed subterms only" and §I.4.3 says it doubles the SC count for
"every user-defined function `f`" — the two are only consistent if a program is
entirely Datafun-typed.

### S3. `syntax.md` gaps — **mostly resolved**

Fixed: `Box` and `deriving` are in the reserved-word list, `..` is in the
fixity table at `infixl 7`, `->`'s un-overridability is now enforced as well
as stated (`fixme.md` F23–F25), and `music.md` item 5 names `(a >|)`.
Still open: `examples.md` does not exist, and the `AttrN` example writes
`type Attr4 a` for both the class and its associated type.

The original items:

- `Box` is used as both a type and a term constructor (`Box type`, `Box expr`)
  but is absent from the reserved-word list.
- `..` (bounded-integer ranges, `4 .. 30`) is listed under reserved characters
  but has no entry in the default fixity table, so `4 .. 30 + 1` has no
  defined parse.
- The default fixity table has `prefix 6 |<` "music unit negative left" and
  `postfix 6 >|` "music unit negative right"; `music.md` item 5 names the
  right-shift operator `(|< a)` as well — a typo for `(a >|)`.
- `syntax.md` §"Testing strategy" references `examples.md`, which does not
  exist in the repository.
- The `AttrN` projection classes are specified for digits 0–15 ("each digit, up
  to 15") but the example class body writes `type Attr4 a` for both the
  associated type and the class name; the class and its associated type cannot
  share a name under `typeclasses.md` §6.

### S4. `music.md` has no semantics — **partly resolved**

`music.md` now says what a `[: A :]` **is**: a box-layout tree whose
elimination form is `layout : [: A :] -> [(Onset, Offset, A, Instrument)]`,
with the payload `A` opaque to layout and interpreted by the instrument it is
handed to.  That answers the question roadmap 3.1 could not start without, and
it settles one thing downstream of it: overlay is not idempotent (`a || a`
lays out to two events), so **`Score` is a commutative monoid, not a
semilattice** — `ΔScore = 1`, and `for` cannot eliminate into it.

The **constructor question is answered too**: `(') : A -> [: A :]` is the
unit note and `r` the unit rest, so `Score` is inhabited and this item's
"unsatisfiable as stated" no longer applies.  A note is one beat by
construction; `|*` reaches every other duration.

**The operators are typed.**  `music.md` gives all of them; they are
ordinary once `[: a :]` is a layout tree over a payload.  Two notes.  `@`
(instrument selection) is **withdrawn** — `>>=` does its job, since an
instrument is a function from a note's payload to a score and applying one
to every note is monadic bind; it has been removed from the fixity table.
And `|*`/`|/` take a plain `Int`, with `class ToInt a` applied explicitly at
the call site (`x |* toInt i`): the constrained form would make `x |* 2`
ambiguous between `Num` and `ToInt` and leave it to defaulting.  **No existential is needed**
either way, so `fixme.md` F35 is not a prerequisite for music.

`layout : [: Void :] -> [(Onset, Offset, R)]`, and `[: Void :]` is reachable
without an erasing operator: an **instrument** is `a -> [: b :]`, applied by
`>>=`, and one whose result holds only committed leaves is parametric in
`b`, so `b` unifies with `Void`.  Performability is a typing property rather
than a runtime check, and a score still holding unassigned notes simply does
not type against `layout`.  `R` — the playable thing — is built in and is
*not* the payload parameter.

**Stretch is withdrawn** along with `@`.  `|~|`/`sp` was to expand and fill
a loose sequence, which is *engraving* — justifying noteheads across a
printed system — and neither of the outputs this design targets has that
problem: a piano-roll grid has linear time, and so does MIDI.  It also
carried the whole cost of the layout pass, which is a single bottom-up fold
without it and a two-pass constrained solve with it.

**The two shifts are one operation**, `at : Int -> [: a :] -> [: a :]`, with
`|<`/`>|` as sugar for a beat either way.  What makes it work is separating
a score's **duration** (how far `++` advances) from its **extent** (where
its content actually sits) — a font's advance width against its bounding
box.  `at` translates the extent and leaves the duration alone, so
`a ++ at (-1) b` overlaps `a` without moving anything after it, while
`at (-4) x` alone simply sounds from -4.  Time is integer ticks, 96 to the
beat, so `|/ n` is exact for every division anyone writes and `|/ 5` is an
error rather than a silent retiming.

The three implementation gaps this exposed are all fixed (`fixme.md` F59,
F60, F61, and F62 alongside).  What is left is bodies — no operator has an
implementation, `ToInt` is not in the prelude, and the committed-leaf
constructor (`R -> [: a :]`, the counterpart of `'`) has no surface syntax.

The original item:

### S4 (original). `music.md` has no semantics

Eleven musical constructs are named with no types, no laws, and no evaluation
rules; `Score` is declared to have no constructors ("Score values are produced
exclusively by user-defined functions whose return type is `[: a :]`, the
built-in core supplies no Score constructors"), which is unsatisfiable as
stated — a value of an empty type cannot be produced.  Either `Score` gets
constructors (`rest`, `note`, `overlay`, `seq`, …) or the layout/render stage
is defined over an ADT the user writes and `[: a :]` is sugar for it.
