# data.md — Datafun (with seminaïve evaluation) ∪ Rizzo, compiled to the G-machine

This spec extends the compilation target established previously (`supercomb.md`'s
lambda-lifted supercombinator G-machine). It has three parts: (I) Datafun compiled
with seminaïve evaluation, which needs **no machine changes**, only a source-to-source
transform before lambda-lifting; (II) Rizzo folded into the same surface language,
which **does** need machine changes (mutable heap cells, a reactive driver loop) because
in-place update is the entire point of Rizzo's design; (III) a shared Haskell-style ADT
sugar layer both halves desugar through.

Where I'm making a real design choice rather than reporting the papers, I say so.
Where something is unresolved, I say that too, instead of papering over it.

## 0. Pipeline

```
surface source
  -> parse, then resolve fixities
  -> classify: ADTs, classes, instances, aliases, coherence   (Part III)
  -> exhaustiveness, on *surface* patterns
  -> desugar: ADT / pattern / match compilation               (Part III)
  -> kind-check
  -> infer                              (extended grammar, Part II.1)
  -> monotone/discrete check            (Part I.3's discipline)
  -> subgrammar check                   (eqtype / semilattice / fixtype, II.1)
  -> solve constraints, elaborate to dictionary passing
  ┌ Datafun programs only ────────────────────────────────────────────┐
  │ -> generate set helpers (eqA/unionA/bottomL/joinL, monomorphized)  │
  │ -> ϕ/δ seminaïve transform                              (Part I)   │
  │ -> change structures: the dummy_X/bottom_X δ asked for  (§I.8)     │
  │ -> ⊥-propagation                                        (§4.2.3)   │
  │ -> Datafun desugaring: EFix/EFor/ESet -> helper calls              │
  └────────────────────────────────────────────────────────────────────┘
  -> lambda lifting                     (unchanged from supercomb.md)
  -> G-machine codegen                  (unchanged for Part I; extended for Part II)
  -> reactive driver                    (Part II.5, FRP programs)
```

□ erasure and ⃝∀ erasure are not stages: both modalities are gone by
construction once ϕ/δ has run (§I.6), so nothing erases them separately.

**Order is load-bearing in four places**, and each was a bug before it was a
rule.  *Exhaustiveness before desugaring*: the match compiler writes an
alternative for every constructor, so a core `case` is complete by
construction and there would be nothing left to check.  *The monotone check
before elaboration*: elaboration rebuilds the lambdas to insert dictionary
parameters, and the binder flavours do not survive it.  *ϕ/δ before Datafun
desugaring*: ϕ/δ matches on `EFix`/`EFor`, which desugaring destroys.
*⊥-propagation between the two*: its rewrites are stated over `∨` and `for`
as *nodes*, and after desugaring there are none.

The ϕ/δ pass and the Rizzo lowering pass are independent and commute: ϕ/δ only ever
touches subterms typed at a Datafun (Sig/Chan/⃝-free) type, so a `fix` buried inside a
signal's per-tick body gets seminaïved in place, and the surrounding Rizzo code is
untouched by ϕ/δ. This is the intended integration point: Datafun-with-seminaïve-fix is
the "what to compute this instant" language; Rizzo is the "when" language.

Two scope notes §0 used to leave ambiguous (`errata.md` S2).  ϕ/δ is applied
**per supercombinator and per half**, not to every function: ϕ where the body
contains a `fix`, a box or a `for`, and δ only where something differentiates
a call to it — a reachability question that starts at the globals under a box
and closes over the call graph (`fixme.md` F7).  And the whole bracketed
block above is skipped entirely for a program that uses no Datafun at all.

---

## Part I — Datafun with seminaïve evaluation

### I.1 Recap: what ϕ and δ are for

`fix e` in Datafun (§2.4, fig 2.5) is naïve: iterate `e` from `⊥` until two successive
iterates compare equal, recomputing the whole result each time. Seminaïve evaluation
(thesis ch. 3) replaces this with `semifix (f, f′)`, where `f′` is a *derivative* of `f`:
a function that computes only the **change** in `f`'s output given a change to its
input, so each iteration does `O(new work)` instead of `O(total work)`.

Two static, purely syntactic transforms compute this:

- **ϕe** ("speed-up"): rewrites `e` into sped-up code, replacing every `fix` with
  `semifix`, and — critically — decorating every `[e]` (box introduction) with a zero
  change, `[(ϕe, δe)]`, so that derivatives are available wherever `fix` needs them.
- **δe** ("derivative"): computes the change in `ϕe` as a function of changes to `e`'s
  free variables. `δe` is mutually recursive with `ϕe`.

Neither transform is a runtime operation — both run once, at compile time, before
lambda-lifting. **The G-machine itself needs no new instructions for this**: ϕ and δ
just decide what ordinary `Expr` code (in `supercomb.md`'s grammar) gets emitted for
each Datafun construct.

What "change" and "derivative" *mean* — and what a new base type, primitive or
semilattice has to supply for them to keep meaning it — is §I.8, from the
thesis's Definitions 14–16 and their antecedent, Cai et al.'s *A Theory of
Changes for Higher-Order Languages*.  Read that before adding either.

### I.2 Type transform: Φ and Δ (fig 3.1)

| Source type | ΦA (sped-up type) | ΔA (change type) |
|---|---|---|
| `1` | `1` | `1` |
| `{A}_eq` | `{ΦA}_eq` (= `{A}_eq`, lemma 19: Φ is the identity on eqtypes) | `{A}_eq` |
| `□A` | `□(ΦA × ΔΦA)` | `1` |
| `A × B` | `ΦA × ΦB` | `ΔA × ΔB` |
| `A + B` | `ΦA + ΦB` | `ΔA + ΔB` |
| `A → B` | `ΦA → ΦB` | `□A → ΔA → ΔB` |

Two lemmas make the codegen tractable:

- **Lemma 19**: `Φ` is the identity on eqtypes. So set elements, sum/product/unit
  eqtype data never change shape under ϕ — nothing extra to generate at eqtypes.
- **`for` is a big *join*, not a big union** (§2.3.2): it denotes `collect(f)`
  over any semilattice, and set union is only its instance at `{A}`.  This is
  why `for`'s result type is a semilattice rather than a set, and why
  `for (x ∈ e) 5` is ill-typed — `Int` has no join.
- **Lemma 20**: at semilattice types `L`, `ΔL = L`. Changes to sets are more sets
  (unioned in); changes to products of semilattices are products of the same shape.
  So the *change representation* for any `fix`-eligible type reuses the ordinary
  set/product runtime representation from the earlier G-machine spec (canonical
  sorted-deduped cons-lists for sets) — no new heap node type.

The one type that actually grows is `□A`: `Φ(□A) = □(ΦA × ΔΦA)`. A boxed value now
carries its own zero-change alongside it. This is where the compiler earns its keep:
every `[e]` in source becomes a pair at codegen time.

**Why `fix` takes a *boxed* function** (`errata.md` D10) — the rule is stated
in §I.5 and reads as arbitrary without this.  A zero change to a function
*is* a derivative for it: Cai et al.'s Theorem 2.9, the thesis's §3.3.3.  So
boxing `fix`'s argument is exactly what makes `f′` available at the one place
that needs it, instead of decorating every function in the program with a
derivative it will never be asked for.  §I.8 states the definitions this
turns on.

Two further notes the thesis makes and the specs did not.  An expression with
*n* free variables has a derivative with *2n* — a base point and a change for
each — which is why δ of a λ interleaves its parameters (§I.4).  And the
thesis's footnote 9 (p. 58) assumes **source programs contain no variable
starting with `d`**, because ϕ/δ mints `dx` from `x`.  Gestate does mint
names that way and **nothing enforces the assumption**.  A program written
to collide — a box-bound `dx` referenced inside `for (x ∈ …)`, whose ϕ body
is wrapped in a generated binding of the same name — nevertheless produces
the right answer, so the hazard is *unproven* rather than known-live.
Recorded as `fixme.md` F67 with that caveat rather than asserted.

### I.3 Context transform

| Context entry | □Γ | ΦΓ | ΔΓ |
|---|---|---|---|
| `X : A` (monotone) | `x :: A` | `X : ΦA` | `DX : ΔA` |
| `x :: A` (discrete) | `x :: A` | `x :: ΦA, dx :: ΔΦA` | `ε` (nothing) |

`ϕe` type-checks in context `ΦΓ`; `δe` type-checks in context `□ΦΓ, ΔΦΓ` — i.e. δ needs
the *base points* of all free variables (boxed/discrete) plus their *changes*.
Concretely: whenever the compiler emits code for `δe`, every monotone variable `X` in
scope must be accessed through its already-erased discrete companion `x` (weakening
theorem 22 — a discrete binding always subsumes a monotone one at the term level, and
in our target `Expr` language this is free, since `EVar`/`PushArg`/`Push` don't
distinguish monotone from discrete at runtime anyway; the monotone/discrete split is
purely a compile-time typing discipline, invisible past ϕ/δ).

### I.4 ϕ/δ term transform — codegen table

For each source construct, this table gives (a) the paper's ϕ/δ rule, (b) what target
code the compiler actually emits, referencing the `Expr`/instruction machinery already
defined for plain Datafun compilation (see the companion G-machine answer: canonical
sorted sets, generated `eqA`/`unionA`/`bottomL`/`joinL` per monomorphic type instance).

| Construct | ϕe | δe | Codegen note |
|---|---|---|---|
| Monotone var `X` | `X` | `DX` | Both are plain `EVar` lookups (post-lambda-lifting: `PushArg`/`Push`); `DX` is just the extra change-parameter the enclosing λ now takes (see below). |
| Discrete var `x` | `x` | `dx` | Same. |
| `λX. e` | `λX. ϕe` | `λ[x]. λDX. δe` | ϕ compiles to an ordinary `ELambda`. δ compiles to a **two-argument** supercombinator: it takes the base point `x` (unboxed via pattern match — no-op after □ erasure, I.6) and the change `DX`, and its body is `δe`. Concretely: every function the source defines gets *two* generated supercombinators, `f_phi` (arity n) and `f_delta` (arity 2n: n base points + n changes), sharing free-variable capture via the normal lambda-lifting pass. |
| `e f` | `ϕe ϕf` | `δe [ϕf] δf` | ϕ is ordinary `EAp`. δ is `EAp(EAp(δe, box(ϕf)), δf)` — i.e. call the *derivative* of `e` (a value of function-change type `□ΦA → ΔA → ΔB`) with the base point and the change of the argument. `box(x) = x` after erasure (I.6), so this is just `δe ϕf δf`, two ordinary applications. |
| `(e, f)`, `πᵢe` | distribute | distribute (`πᵢδe`) | `(e, f)` compiles to `ETuple [e, f]`; `πᵢe` compiles to `EAp (EProj i) e` (i.e. `Eval` + `Proj i` on the tuple's `NTuple` node).  `□`-box pairs reuse the same `ETuple`/`EProj` machinery (see line for `[e]` below); no separate primitive is needed.
| `iniₑ`, `case` | distribute (see below) | see I.4.2 | Sums are the one place δ needs real logic — the tag can't change (§3.3.2), so δ-of-case has to route through `split`.  Note `δ(inᵢ e) = inᵢ δe` and `δ(πᵢ e) = πᵢ δe` really are distribution; **`δ(case …)` is not**, which is what "see below" means here. |
| `⊥`, `{eᵢ}ᵢ`, `e = f`, `fix e` | distribute — `ϕ(e = f) = (ϕe = ϕf)` | `⊥` | These subexpressions are discrete data / control, incapable of "changing" independently of their own recomputation, so δ is the zero change at their (semilattice or `1+1`) result type — compiles to the generated `bottomL`/empty-set constant for that type, computed once at compile time, not per call. |
| `empty? e` | `empty? ϕe` | zero change at `Bool` | Both halves are the ordinary application rule: `empty?` is a primitive global, so ϕ leaves it alone. δ is the zero change *because `empty?`'s argument is discrete* — its arrow is `□Prop → Bool` (`syntax.md`), and §I.3's context transform gives a discrete binding no entry in `ΔΓ` at all. So this is §I.8's Rule 2 and the discrete arrow agreeing, not two separate facts. |
| `split e` | see below | `let [y] = ϕe in case π₁ y of (inᵢ _ ▹ inᵢ ())ᵢ` | **Not reached in gestate**, and the reason is worth recording rather than leaving as an omission: □ is erased (§I.6), so the outer `case ϕe` *is* the split, and the type mismatch the rule exists to repair has no runtime witness. δ's type here is `1+1`, so the tag has to be recovered from `ϕe` — `empty? ϕe` alone would not give it. |
| `e ∨ f` | `ϕe ∨ ϕf` | `δe ∨ δf` | Both compile to calls to the generated `joinL`. Note (§3.4.6): this is a deliberate **overapproximation** — the precise change would be `(δe∖ϕf) ∪ (δf∖ϕe)`, but computing that needs `ϕe`/`ϕf`, which is exactly the recomputation seminaïve evaluation exists to avoid. The generated code accepts extra (redundant, harmless — `∨` is idempotent/monotone) elements into the delta rather than pay for exactness. **This is a genuine engineering tradeoff baked into the algorithm, not a bug**: worst case, deltas grow larger than strictly necessary, which costs iteration time but never correctness. |
| `[e]` | `[(ϕe, δe)]` | `()` | This is the crux of the whole scheme. Codegen: allocate a pair node `NCon 0 [ϕe_code, δe_code]` — i.e. compile `e` twice, once through ϕ and once through δ, and pack the results. δ of the box itself is trivially the unit value (boxed things can't change — `ΔΦ□A = 1`), compiled as `Pack 0 0`. |
| `let [x] = e in f` | `let [(x,dx)] = ϕe in ϕf` | `let [(x,dx)] = ϕe in δf` | Compiles to an `ECase`-style unpack of the pair built by `[e]`'s codegen (a single non-recursive `ELet` binding both `x` and `dx` from the two projections), then continues into `ϕf` (resp. `δf`). Note δ **discards** `ϕe`'s second half and doesn't even look at `δe : 1` — the unpack only exists to expose `dx` to `δf`. |
| `fix e` | `semifix ϕe` | `⊥` | See I.5 — this is the actual optimization. δ is the constant `⊥` at the fixtype (`ΔfixL = fixL` by lemma 20), because `e : □(fixL → fixL)` is boxed and thus can't change. |
| `for (x ∈ e) f` | `for (x ∈ ϕe) let [dx] = [0ₓ] in ϕf` | two-clause union, see below | See I.4.1 — the computational core of the whole transform. |
| `case e of (iniX ▹ fᵢ)ᵢ` | `case ϕe of (iniX ▹ ϕfᵢ)ᵢ` | see fig. 3.2/3.3, expanded | See I.4.2. |

#### I.4.1 `for` — codegen

Recall from the earlier G-machine spec that `for (x ∈ e) f` already compiles to a
generated fold-with-join supercombinator over the canonical sorted set representation
of `e`. The δ-transform just generates **two** such folds and unions their results:

```
δ(for (x ∈ e) f)
  =   (for (x ∈ δe)        let [dx] = [0x] in ϕf)     -- new elements: run the sped-up body
    ∨ (for (x ∈ ϕe ∨ δe)   let [dx] = [0x] in δf)      -- all elements: run the changed body
```

Codegen: two calls to the generated `forLoop` supercombinator (I.2 of the earlier
spec), one over the delta set `δe` running `ϕf`'s code, one over the *union* of the old
set and its delta running `δf`'s code, joined with the generated `joinL` for the result
type. `[0x] = [dummy x]` — see I.4.3 below, `dummy` is a genuinely generated
per-eqtype function, not erased, because unlike □ itself, the *value* `dummy x`
participates in later computation (it's fed to `δf` as `dx`).

This is literally `step′` from §3.1 made mechanical: for the transitive-closure example,
this transform derives exactly the hand-written `step′ s ds = {(x,z) | (x,y)∈edge, (y,z)∈ds}`
from the `step` definition, with no programmer intervention.

#### I.4.2 `case`/`split` — codegen

Because sums are ordered disjointly (§3.3.2 — the value inside can grow, but the tag
can never flip), δe's tag is *guaranteed* to match ϕe's tag at runtime; the "tag
mismatch" branches the transform must nonetheless generate (to satisfy the
target-language type checker) are genuinely dead code. Per fig. 3.3, expanded:

```
δ(case e of (iniX ▹ fᵢ)ᵢ)
  = case split [ϕe] of
      (iniY ▹ let [x] = Y in
              (λDX. δfᵢ) (case δe of iniDX ▹ DX
                                    ini₊₁ mod 2 _ ▹ dummy x))ᵢ
```

Codegen: compile `split [ϕe]` as an ordinary `ECase` on the (already-computed) `ϕe`
value's tag (no extra runtime work — `split` here is a compile-time-scheduled
projection, not a new primitive), bind `x` via `Push`, then a *second*, nested `ECase`
on `δe`'s tag. The generated dead branch (`dummy x`) calls the compile-time-generated
`dummyA` function (fig. 3.5), not `bottomL`: `dummy` is defined per source type by
structural recursion (empty set at set type, unit at unit type, recurse into products/
sums, `dummy□A[x] = [dummy x]`, and — the one non-inductive case —
`dummyA→B f = λx. dummy(f x)`, meaning generated dummy-function code for a function
type actually *calls* the underlying function once to get a same-shaped output, then
zeroes that). This is the only place codegen has to synthesize a function-typed dead
value by re-invoking a real function; it happens exactly once per `case` compiled by δ,
and only on the (never-taken) mismatched-tag path, so it costs nothing at runtime
despite being real generated code.

`dummyA` on eqtypes coincides with the zero-change function (lemma 23), which is why
`for`'s `[0x]` and `case`'s dead-branch `dummy x` are literally the same generated
helper — implement `dummyA` once per monomorphic type instance and reuse it in both
places.

#### I.4.3 What actually gets generated per program

For a program using seminaïve evaluation, the compiler emits, per **monomorphic type
instance** `A` occurring in the source (same monomorphization argument as the
non-seminaïve G-machine target: Datafun as given has no polymorphism, so every use site
is a known ground type):

- `eqA`, `unionA`, `bottomL`, `joinL` (unchanged from the base compilation)
- `dummyA` (fig. 3.5) — new
- `f_phi`, `f_delta` for every user-defined function `f` — new, doubling the number of
  generated supercombinators for the program, but each is still just an ordinary
  first-order recursive `Expr` translated the normal way
- `semifixL` (I.5) in place of `fixLoop` — new

None of this requires touching `Instruction`, `Node`, or `step` from `supercomb.md`.
Seminaïve evaluation is, in the end, "compile the program twice" (once straight, once
differentiated) plus a smarter fixed-point driver.

#### I.4.4 `ϕ(split e)`, and the type mismatch it repairs

Fig. 3.2's rule, reproduced because §I.4's table pointed at it without
giving it (`errata.md` D7):

```
ϕ(split e) = let [z] = ϕe in
             case split [π₁ z] of
               (inᵢ Y ▹ let [x] = Y in
                        case split [π₂ z] of
                          inᵢ DY  ▹ let [dx] = DY in inᵢ [(x, dx)]
                          in(i+1 mod 2) _ ▹ inᵢ [(x, dummy x)])ᵢ
```

The reason it is this shape, which the thesis assumes and no spec stated:
Φ does not commute with □ over a sum.

```
Φ(□(A+B)) = □((ΦA+ΦB) × (ΔΦA+ΔΦB))     -- a boxed pair of tagged values
Φ(□A+□B)  = □(ΦA×ΔΦA) + □(ΦB×ΔΦB)       -- a tagged pair of boxed values
```

`split` converts between them, and the inner `case` is where it can fail to:
the value's tag and the change's tag are carried *separately*, so nothing
forces them to agree.  Where they disagree the change is discarded and
`dummy x` put in its place — the second of the two places `dummy` is needed
(§I.4.2's dead branches are the first), and the reason `dummy` has to exist
at every type rather than only at semilattices.

**Gestate does not reach this.**  □ is erased (§I.6), so a box is not a
runtime pair and the outer `case ϕe` *is* the split; the two Φ-images above
are the same erased thing and there is no mismatch left to repair.  Recorded
so that the rule is here if □ ever stops being erased.

#### I.4.5 Type formation is not uniform (`errata.md` R10)

Rizzo's fig. 2 requires **both** premises *closed* for an arrow: `⊢A:type`
and `⊢B:type` give `Φ ⊢ A→B : type`.  §II.1 recorded only `⊢B:type`, which
understates it.  The same closed premise applies to `Chan A`, `⃝∃A` and
`⃝∀A`.  Only `Sig A`, `×`, `+`, `1` and `μα.A` propagate the open context
`Φ`.

This is not bookkeeping: it is what makes

```
μα. A + Sig (A × α × A)        legal
μα. 1 + (α → α)                not
```

and §III.2's "recursive ADTs inherit Rizzo's μ restriction" depends on
exactly this asymmetry — a recursive occurrence may sit under a `Sig` or a
product but not under an arrow.

### I.5 `semifix` — the actual speed-up (Definition 17 / §3.4.2)

```
semifixL (f, f′) :
  x0  = ⊥          x{i+1} = xi ∨ dxi
  dx0 = f ⊥         dx{i+1} = (f′ xi dxi) \ x{i+1}
  -- stop when dxi ⊑ xi — the change is subsumed by the accumulator
```

**Amended 2026-09-04** (`errata.md` D2, `fixme.md` F6).  This section
prescribed `eq dx' ⊥` — *stop when the delta is empty* — which is not the
thesis's test (fig. 4.2, p. 71: "seminaïve iteration stabilizes once
`dxi ⩽ xi`") and **loops forever** on the shape every Datalog query has:
`δ(e ∨ f) = δe ∨ δf` overapproximates, so a delta routinely contains
elements `x` already holds, and such a delta is non-empty while `x` has
stopped growing.  `gestate/seminaive.py` has tested `subset_L dx x` since
the fix; the paragraph below, which argues for the empty-delta test, is
the original text and is **wrong** — kept because the reasoning in it is
what a reader will otherwise reconstruct.  The `\ x{i+1}` is change
minimization (§4.3, `errata.md` D4), separate and also implemented.

Compare to I.5 of the earlier (naïve) spec's `fixLoop`, which recomputed `f u2` every
iteration and tested full equality of successive iterates. `semifixL` instead:

```
semifixLoop f f' x dx =
  let dx' = f' x dx
  in eqL dx' bottomL  ->  x ∨ dx           -- converged: dx' contributes nothing new
                      ;   semifixLoop f f' (x ∨ dx) dx'
semifix (f, f') = semifixLoop f f' bottomL (f bottomL)
```

*Original text, superseded by the amendment above.*  Convergence test changed
from "compare two full iterates" to "is the new delta empty" —
cheaper on both counts (smaller value to compare, and it's the natural stopping
condition already implied by `∨`'s idempotence). `f` here is `ϕe`'s first projection,
`f′` its second — recall `ϕ(fix e) = semifix ϕe` where `ϕe : □((fixL → fixL) ×
(□fixL → fixL → fixL))`, i.e. `ϕe` evaluates (once, since it's boxed) to the pair
`(f, f′)` this loop consumes.

Typing/semantics rule to add to the target `Expr` language's supercombinator
generation (this is *not* a new G-machine instruction, just a recognized shape of
generated code, same status as `fixLoop` was before):

```
Γ ⊢ e : □((fixL → fixL) × (□fixL → fixL → fixL))
------------------------------------------------
Γ ⊢ semifix e : fixL
```

### I.6 □ erasure, still trivial — with one caveat

As established previously, `□A`/`[e]`/`let [x]=e in f` erase to identity at runtime.
That's still true **for the source language's own □**. But note ϕ *introduces new uses*
of □ internally (`Φ(A→B) = ΦA→ΦB` doesn't box, but `δ(λX.e) = λ[x].λDX.δe` does pattern-
match a box) — these compiler-introduced boxes erase exactly the same way: `λ[x].λDX.e`
compiles to an ordinary two-argument supercombinator, no runtime tag, `x` is just bound
directly. So erasure is uniform regardless of whether the box was written by the
programmer or synthesized by δ.

### I.7 Correctness note (honesty check)

The thesis proves ϕ/δ correct via a logical-relations argument (§3.5) tying `e`, `ϕe`,
`δe` together through the change-structure relation `dx ▷ x ,→ y`. This spec doesn't
re-derive that proof — it inherits it, on the assumption that codegen is a faithful,
meaning-preserving rendering of the ϕ/δ term-rewriting rules into `Expr`. The one place
this assumption needs real scrutiny is I.4.1's `for`: the thesis's `δ` rule assumes
`ϕe`/`δe`/`ϕf`/`δf` are the *same* pieces of code, referentially, in both for-loops (no
recomputation) — codegen must actually share the compiled subexpressions (bind them
once via `ELet`, don't inline the `compileC e env` call twice), or you silently regress
to naïve evaluation while still calling it `semifix`. Worth a dedicated test — but **not the asymptotic one**.  Measuring `path`
for Θ(n²) rather than Θ(n³) does not detect a lost share: with the sharing
removed on purpose the step counts are indistinguishable, because a `for`'s
source is almost always a *variable* (`for (x ∈ r)` over the fixpoint
variable, `for (q ∈ e)` over a box-bound one) and duplicating a variable
reference costs nothing.  The penalty appears only for
`for (x ∈ <computed expression>)`, which neither paper writes.  Test the
*shape* instead: δ of a `for` must bind `ϕe` and `δe` once each and the two
loops must use those bindings.  `test/test_sharing.py`; `fixme.md` F42.

### I.8 The change-structure interface — what an extension must satisfy

§§I.1–I.7 say what the compiler *does*.  This section says what anyone adding a
base type, a primitive, or a semilattice has to *supply*, and it is the interface
§I.7's inherited proof quantifies over — without it, "inherits the proof" has
nothing to inherit against.

Sources: thesis §3.3, Definitions 14–16.  Their antecedent is
Cai, Giarrusso, Rendel and Ostermann,
*A Theory of Changes for Higher-Order Languages: Incrementalizing λ-Calculi by
Static Differentiation* (arXiv:1312.0658, 2013), which the thesis cites as
Cai et al. 2014.  That paper is the origin of the **plugin discipline** this
section is an instance of: a plugin supplies base types and primitive
operations, and for each one a change representation and an incremental
version; the differentiation transform itself is parametric in the plugin, so
a new plugin is supported — and proved correct — without touching it.  Gestate
is a plugin over Datafun's core, and what follows is its obligation list.

**Definition 14 (change structure).**  A change structure `A` consists of a
poset `VA` of *values*, a poset `ΔA` of *changes*, and a relation
`RA ⊆ ΔA × VA × VA`, written `dx ▷ x ,→ y : A` and read "`dx` changes `x` into
`y`".  It must satisfy three properties:

| | |
|---|---|
| **Functionality** | if `dx ▷ x ,→ y : A` and `dx ▷ x ,→ z : A` then `y = z` |
| **Soundness** | if `dx ▷ x ,→ y : A` then `x ⩽A y` |
| **Zero changes** | for every `x : VA` there is some `dx : ΔA` with `dx ▷ x ,→ x : A` |

Functionality makes `(dx, x) ↦ y` a partial function.  Soundness says a change
only ever moves *up* — Datafun needs only increasing changes, because iteration
towards a fixed point grows monotonically, and this is what lets `semifix`
accumulate rather than recompute.  A `dx` with `dx ▷ x ,→ x` is a **zero
change** to `x`, written `0x`; this is the property δ leans on at every term
that cannot change, and it is why `dummy`/`⊥` has to exist at *every* type
(`errata.md` D7, and `gestate/changes.py`).

**Definition 15 (derivative).**  A derivative of a monotone map `f : A → B`
between change structures is a monotone map `f′ : □VA → ΔA → ΔB` satisfying

```
dx ▷ x ,→ y : A  ⟹  f′ x dx ▷ f x ,→ f y : B
```

Note the `□` on the base point: a derivative consumes its input *discretely*.
That is exactly why ϕ decorates every box with a pair `[(ϕe, δe)]` (§I.1) —
`fix` needs a derivative, and a derivative needs a base point that cannot
itself change.  Cai et al.'s Theorem 2.9 ("nil changes are derivatives") is the
same fact from the other side: the zero change *of a function* is its
derivative.

Say *a* derivative, not *the*: derivatives are not unique, because changes are
not — for fixed `x, y` there may be many `dx` with `dx ▷ x ,→ y`.

**Definition 16.**  Change structures and differentiable monotone maps form a
category (`ΔPoset`).  Differentiable maps compose.  This is the load-bearing
fact behind §I.4's table: δ can be defined structurally, one rule per former,
because the derivative of a composite is built from the derivatives of its
parts.

**The two instances that matter.**  At finite sets,

```
V{A}eq = Δ{A}eq = {A}eq        dx ▷ x ,→ y : {A}eq  ⟺  x ∪ dx = y
```

— functionality holds because union is a (total) function, soundness because
`x ⊆ x ∪ dx`, zero changes because `x ∪ ∅ = x`.  Generalised to any semilattice
`L`: `VL = ΔL = L` and `dx ▷ x ,→ y ⟺ x ∨ dx = y`, with `⊥` the zero.  That is
§I.2's Lemma 20, and it is the only change structure `fix` itself needs — which
is why `fix` is restricted to fixtypes.

#### What gestate supplies

Gestate has base types and primitives Datafun does not (`Int`, `Char`,
`Cyclic n`, `lo .. hi`, `+`, `*`, `-`, comparison), plus the Rizzo formers.
The change structure in force, per fig. 3.1 plus gestate's own rows:

| type | `ΔA` | zero change |
|---|---|---|
| `{A}` | `{A}` | `⊥` |
| `1` | `1` | `()` |
| `A × B` | `ΔA × ΔB` | componentwise |
| `A + B` (every gestate ADT, `Bool` included) | `ΔA + ΔB` | `dummy (ini x) = ini (dummy x)`, generated per type |
| `A → B` | `□A → ΔA → ΔB` | `λx. λdx. dummy (f x)` |
| `□A` | `1` | `()` |
| `Int`, `Char`, `Cyclic n`, `lo .. hi`, every Rizzo former | `1` | `()` |

**Rule 1 — every non-set base type carries the trivial change structure
`ΔA = 1`.**  Its values are discretely ordered, so `x ⩽ y ⟺ x = y`;
functionality and soundness hold vacuously and `()` is the zero.  A new base
type must either satisfy this or state its own change structure and discharge
Definition 14.

**Rule 2 — a saturated primitive application is discrete.**  If every argument
type of a primitive `p` has `ΔAᵢ = 1`, then no argument can change, so neither
can the result:

```
δ(p e₁ … eₙ)  =  0 at p's result type
```

Definition 15 is satisfied by the zero-change derivative: with no `dxᵢ` moving
any argument, `f x = f y`, and the zero change relates them.  `δ(prim_eq_int x y)`
is therefore `dummy` at `Bool`.

Two things this rule is *not*.  It is not `δp` applied to arguments — `Δ(base)`
is `1` and `()` takes none; emitting that anyway was a real defect, and because
the unit is represented as a number and `Unwind` on a number ignores the spine,
it failed far from its cause (`errata.md` D8).  And it does not extend to a
**partial** application, which is still a function and whose change type is
`□A → ΔA → ΔB`.

#### The obligation a new semilattice takes on

Rules 1 and 2 cover every primitive gestate currently has, because every one of
them is over discretely-ordered arguments.  They say nothing about a primitive
whose argument may *genuinely* change — that is, one over a semilattice.  For
such a primitive Definition 15 has real content: the implementer must supply
`p′ : □VA → ΔA → ΔB` and show the implication holds, and Definition 14 must be
discharged for the new type.

**`Score` is not that case**, and it is worth saying so here because it is the
obvious candidate and the answer is no.  A score lays out to a *list* of timed
events (`spec/music.md`), so overlay is not idempotent: `a || a` sounds two
notes together and lays out to two events, where `a` lays out to one.  Overlay
is an associative, commutative monoid, not a semilattice — there is no `⩽` for
soundness to hold against and no join for `for` to eliminate into.  `Score`
therefore stays in Rule 1's row, `ΔScore = 1`, like every other discretely
ordered type.

So this subsection currently has **no claimant**: nothing in gestate, and
nothing music.md implies, needs a primitive over a semilattice.  It is stated
so that if one is ever proposed the obligation is already written down, rather
than discovered afterwards the way the primitive-function rule above was.

---

## Part II — Union with Rizzo

### II.1 Extended type grammar

Add Rizzo's type formers directly to Datafun's single `types` grammar (fig 2.1), rather
than inventing a parallel grammar:

```
types A, B ::= {A}_eq | 1 | A×B | A+B | A→B | □A          -- Datafun (unchanged)
             | SigA | ChanA | ⃝∃A | ⃝∀A | μα.A              -- Rizzo (new)
```

Crucially, **do not** add these to the `eqtypes`, `semilattices`, `finite eqtypes`, or
`fixtypes` subgrammars. This one edit is what makes the union sound without touching
anything else in Datafun's type discipline: a `Sig A` can never be compared with `=`,
never used as a `fix`/`∨`/`⊥` target, never be a set element type. That's the correct
restriction on independent grounds — signals are not posets with the right structure
for any of that — and it falls out for free from "just don't extend those three
subgrammars," no new side-conditions to state or prove.

Rizzo's own restriction — type formation `Φ ⊢ A : type` requires `⊢B:type` (i.e. `B`
closed, no free type variable) as a side-condition on `A→B`, `⃝∃A`, `⃝∀A`, `ChanA` — is
inherited unchanged; it interacts with Datafun's types only insofar as any Datafun type
mentioned inside a `Sig`/`Chan`/later type must itself be closed, which it always is
(Datafun has no type variables at all in this core calculus).

### II.2 Monotone/discrete placement — the real design decision

Datafun's type grammar doesn't separate "monotone types" from "discrete types"; the
distinction lives on *variables*, and is enforced by which expressions count as
"non-monotone" (get the light-blue background, strip monotone variables from scope).
The clean way to fold Rizzo in: **every Rizzo-native construct is non-monotone**, added
to the same list `e=f`, `empty?e`, `split e`, `fix e` already occupy. Concretely:
`head t`, `tail t`, `wait t`, `watch t`, `sync s t`, `delay t`, `chanA`, `s ::A t`,
`gfix x.t` (see II.3), `rec(x.s,t)`, and any subterm scrutinizing a `Sig`/`Chan`/`⃝`
value all strip monotone variables from scope, same mechanism, same enforcement,
zero new type-checker machinery.

This is a real constraint, not a formality: it means you cannot close over a monotone
Datafun variable `X` (e.g. a variable bound by an outer `for`) inside a signal body —
you have to `let [x] = ... in` it into a discrete binding first, exactly as you already
would to compare it with `=`. That's the correct behavior: a signal that could observe
a *changing* monotone quantity without going through `head`'s explicit current-value
read would break causality in the same way an unrestricted `=` would break
monotonicity.

**Open question I'm not resolving here**: can a semilattice type `L` (e.g. `{Int}`) be
the payload of a `Sig`, i.e. is `Sig {Int}` well-formed, and can you then run a
Datafun `fix`/`for` over the *current value* of such a signal once per tick? Nothing in
the grammar above forbids it (`{Int}` is a perfectly good `A` to instantiate `SigA`
with), and I think it should be allowed — "recompute this Datalog query fresh each
reactive step, sourced from live signal values" is exactly the "Datafun inside Rizzo"
integration this union is for. But I haven't checked it against Rizzo's own metatheory
(causality/no-space-leaks proofs, §4.6) to confirm nothing there implicitly assumed the
signal payload type has no internal recursive/fixed-point structure of its own. Flag
this for whoever formalizes the union — it's the first thing to check.

### II.3 Naming collision: `fix`

Datafun's `fix e : fixL` (iterate to convergence over a semilattice, no recursion in
the ordinary sense — see the earlier spec, Datafun's grammar has no general recursion
construct at all) and Rizzo's `fix x.t : A` (guarded structural recursion via `⃝∀`) are
different operators that happen to share a keyword in their respective papers. In the
union surface syntax, rename Rizzo's to **`gfix`** ("guarded fix"):

```
terms e,f ::= ... | fix e                      -- Datafun: semilattice fixed point
                   | gfix x.t                   -- Rizzo:   guarded recursion
```

Both still compile to recursive supercombinators in the target `Expr` language (per
I.5 above for `fix`/`semifix`, and directly per Rizzo's own reduction rule
`gfix x.t ⟶ t[delay(gfix x.t)/x]` for `gfix` — this is a plain self-referential
definition, compiles via `ELet rec` / a `letrec`-bound `EGlobal`, no new machine
support needed for `gfix` itself, only for what its body touches: `Sig`/`Chan`).

### II.4 Machine extensions — new `Node` and `Instruction` cases

Unlike Part I, this part **does** require touching `supercomb.md`'s core. The reason is
structural, not incidental: Rizzo's entire contribution is replacing signals-as-streams
(which a pure graph-reduction machine already handles fine, as an ordinary lazy
infinite `Cons`-list, no changes needed) with signals-as-in-place-mutated-heap-cells,
specifically to avoid retaining old values. `Update n` in the base G-machine already
does one-shot heap mutation (indirection-on-first-force), but that's memoization, not
what Rizzo needs: a `Sig` cell must be overwritten *repeatedly*, once per reactive step,
for the lifetime of the program, and old overwritten values must become unreachable
immediately (§4.4's reference-counting recommendation) rather than sitting behind an
`NInd` chain.

**`spec/frp.md` is the specification for these extensions; this section is
the motivation for them.**  It used to restate the node and instruction set
in different terms, and the two drifted into genuinely incompatible
machines (`errata.md` S1) — a `Bool`-tagged `NSignal` against `NSig`, a
queue-shaped `NChan [Addr]` against an identity `NChan Int`, a distinct
`NDelayN` node against reused `NCon` tags, and four instruction names
against another four.  Only one of them can be the spec, and `frp.md`'s is
the one the implementation follows and the more economical of the two: it
reuses `Pack`, which is right given the paper's "they behave similarly to
strict constructors", so `Unwind` needs no new guard — an `NCon` is already
WHNF.

The correspondence, for anyone reading the older text:

| this section said | `frp.md`, and the implementation |
|---|---|
| `NSignal Addr Addr Bool` | `NSig` — value, tail, ticked |
| `NChan [Addr]`, a queue of pending values | `NChan Int`, an *identity* |
| `NDelayN Addr`, a distinct node kind | `NCon Tag [Addr]`, tags 90–96 |
| `MkSignal`, `UpdateSignal n`, `Advance`, `ChanRecv` | `SigCons`, `SigHead`, `NewChan`, `MkDelayAp` |
| `Unwind` needs a guard for `NDelayN` | nothing to add |

One difference is substantive rather than cosmetic and is worth keeping in
mind: the queue-shaped `NChan` was the only place *either* spec accounted
for input delivery.  `frp.md` handles it by passing the input value down
through `advance`, which is why a channel needs no queue — the driver
already has the value in hand when it reaches the signal waiting on it.

What stands, and is not in `frp.md`, is the paragraph above: *why* the
machine has to change at all, and that `Update n`'s one-shot
indirection-on-force is memoization rather than the repeated in-place
overwrite a `Sig` cell needs.

### II.5 The reactive driver — outside `evaluate`

The base G-machine's `evaluate`/`step` loop computes one term to WHNF and stops
(`gmFinal`). Rizzo needs an outer loop around that, implementing the paper's three-part
reactive semantics (fig. 8/10) directly:

```
initProgram t =
  let s0 = evaluate (compile t)     -- ordinary G-machine run: pure eval semantics, fig. 8
  in  (result s0, heap s0, chanCtx s0)

reactiveStep (v, heap, Δ) (κ, w) =
  -- 1. mark every NSignal in `heap` as "earlier" (conceptually; in-heap this is a
  --    scan, not a copy — see below)
  -- 2. process signals left-to-right (the "update semantics", fig. 10 update rule):
  --      for each l : NSignal(v1, tailComp, _):
  --        if ticked κ heap tailComp
  --          then advance tailComp (via Advance instr, using `evaluate` internally
  --               for the ordinary-CBV subcomputations it triggers -- e.g. the
  --               function application inside `delay t 5 v`)
  --               -> produces a new NSignal(v1', tailComp')
  --               -> UpdateSignal l NOT allocate: overwrite in place, ticked := true
  --          else UpdateSignal l: unchanged, ticked := false
  -- 3. deliver `w` to channel κ's NChan queue (consumed by ChanRecv during step 2)
  --      via wait κ / watch l lookups
  in (v, heap', Δ')
```

The "now heap ✓ earlier heap" split in the paper (§4.1) is a proof device more than an
implementation requirement — practically, per §4.4's own recommendation, use one heap
with in-place update and process signals in a fixed left-to-right heap-allocation order
per step; the ✓ divider becomes an implicit "already visited this step" mark rather than
a second physical heap. This matches what the paper itself suggests for a practical
implementation.

**This driver is genuinely new relative to the base G-machine** — it's not expressible
as a supercombinator, because it needs to (a) hold onto the heap *across* calls to
`evaluate` (the base machine's `evaluate` is meant to run to completion and be
discarded) and (b) mutate specific, previously-allocated cells by address rather than
by constructing new graph and relying on `Update`'s indirection trick. Treat it as a
second top-level entry point alongside `evaluate`, not as compiled `Expr` code.

### II.6 `ticked`/`cl` predicates — compiled, not interpreted

Fig. 10's `tickedκ_η(v)` and `clη(v)` are defined by structural recursion on the shape
of a `⃝∃A` value (`never`/`watch l`/`v5w`/`wait κ`/`sync v w`/`tail l`). Since these
shapes are exactly the `NDelayN` tags from II.4, compile `ticked`/`cl` as ordinary
recursive functions pattern-matching on `NDelayN`'s sub-tag, run by the driver (not
inline in `evaluate`) each reactive step. No new instruction needed beyond what II.4
already added; this is just more generated code, same status as `eqA` was in Part I.

### II.7 Reference counting (§4.4) — a memory-management note, not a semantics one

The paper recommends ARC specifically because Rizzo's type system provably forbids
reference cycles (Theorem 4.1 rules out the stuck states that would arise from one).
If the G-machine's existing heap uses a tracing GC (typical for this style of machine),
that's not wrong, just leaves performance on the table for the Rizzo fragment
specifically — worth special-casing `NSignal`/`NChan`/`NDelayN` cells for prompt ARC-
style collection even if the rest of the heap stays traced, since those are exactly the
cells the paper's whole design is oriented around freeing promptly (§4.4, "no unused
signals are ever updated"). Not required for correctness; is required to actually get
the "no space leaks" property to manifest as *low* memory use rather than merely
*bounded* memory use under a lazy tracing collector that doesn't run often enough.

---

## Part III — Shared ADT sugar

### III.1 `data` declarations

```
data T a1 .. an = C1 A11 .. A1k1 | C2 A21 .. A2k2 | ... | Cm Am1 .. Amkm
```

desugars to a sum-of-products with runtime tags 0..m-1, exactly Datafun's own §2.2
sugar item 5, generalized to carry type parameters:

```
type T a1 .. an = A11×..×A1k1 + A21×..×A2k2 + ... + Am1×..×Amkm
Ci x1 .. xki  ~>  in_i (x1, .., xki)                   -- constructor = injection + tuple
```

`Maybe a = Nothing | Just a` ~> `type Maybe a = 1 + a`, `Nothing ~> in1 ()`,
`Just x ~> in2 x` — the plain `1+a` sum, not a set.  An ordinary `Maybe` has
no use for a semilattice structure, and neither does `Bool`: **`Bool` is an
ordinary two-constructor ADT under this rule like any other**, ordered by
equality, and it is not Datafun's `{1}`.

Gestate has that type too, spelled `Prop = {()}`, as a *separate* type
whose eliminator is `for` rather than `case` — `errata.md` D5 records why
both exist and which is for what.  Nothing in this section applies to it:
`Prop` is an alias for a set type, so it is not declared, not tagged, and
not desugared here.

Nullary constructors with no fields (`C` with `k=0`) get unit payload, same as `Ci ()`.
`1` — the surface `()` — is an ordinary type: it is in all four of fig. 2.1's
subgrammars, which is what makes `{()}` a semilattice and a fixtype.
Constructors used as patterns desugar to nested `case`/`ini` patterns the same way.

### III.2 Recursive ADTs — inherit Rizzo's μ restriction, don't relax it

```
data List a = Nil | Cons a (List a)
```

desugars through Rizzo's `μα.A` (§2.4), **not** through unrestricted named recursion,
because that restriction (fig. 2, `α` may appear only nested under product/sum/`Sig`,
and the core grammar allows at most one free type variable) is what makes `rec`
terminating and lets §4 prove type preservation for terms mentioning heap-stored data.
Relaxing it would mean re-deriving those proofs. So:

```
List a  ~>  μβ. 1 + (a × β)             -- one recursive tyvar β; `a` closed over as a parameter
Nil     ~>  cons_{μβ.1+(a×β)} (in1 ())
Cons x xs ~>  cons_{μβ.1+(a×β)} (in2 (x, xs))
```

Consuming a `List a` uses `rec(r.s, t)` with `fmap` doing the structural recursion per
fig. 8's bottom definition (already given for `α | 1 | A→B | ⃝∀D | ⃝∃D | μα.D | F×G |
F+G | SigF`) — no changes needed, that `fmap` table already covers everything this
union's type grammar can produce, since II.1 only added type formers `fmap` already has
cases for (`Sig`) or that don't recurse at all (`Chan`, treated like `⃝∀D`/`⃝∀D`'s
"return x unchanged" case since a `Chan A`'s `A` is a message payload type, not a
recursive occurrence site).

**Multi-parameter mutual recursion** (e.g. a `Tree`/`Forest` pair, or — the paper's own
example — `Widget` containing `Sig Widget` via `dyn`) works today only because Rizzo's
`dyn (Sig Widget)` example nests the recursive occurrence under `Sig`, which the fmap
table explicitly supports (`fmapSig F f x = map (fmapF f) x`). A `data` declaration that
tries to define two ADTs recursive-in-each-other *without* going through a `Sig` or
`×`/`+` boundary (i.e. genuine mutual recursion via direct named reference, not nested
under an allowed constructor) is **not supported** — desugar-time error, same
restriction the source paper accepts. If mutual recursion without `Sig` indirection is
needed later, standard fix is the "sum of injected constructors into one shared μ"
encoding, but that's out of scope here — flagging it rather than quietly generating
something unsound.

### III.3 Pattern matching desugaring

One `case`/`match` frontend, three backends depending on scrutinee type — resolved
by the typechecker before desugaring runs, not guessed structurally:

| Pattern surface form | Backend | Desugars via |
|---|---|---|
| `C x1 .. xk` (ADT constructor) | III.1's `data` encoding | nested `case`/`ini`/tuple projection |
| `[p]` (box pattern) | Datafun `□` | `let [x] = e in ...` (Datafun, §2.2 item 2) |
| `!e` (equality-check pattern) | Datafun eqtype `=` | guard compiled to `case (scrutinee = e) of ...`, useful combined with `for`/comprehension sugar exactly as the thesis intends |
| `x :: xs` (signal cons) | Rizzo `Sig` | `head`/`tail` projection, per §2.1 ("we will usually use pattern matching syntax instead [of head/tail]") |
| `cons v` / recursive-type constructor patterns | Rizzo `μ`/`rec` | `rec(x.s, t)` per §2.4's general desugaring scheme for recursive function definitions with guarded recursive calls |

All five compile down to the same target-level primitive: nested `ECase` plus, for the
`Sig`/`rec` rows, the II.4/III.2 machinery already described. No new pattern-matching
runtime machinery beyond what's already specified — this section is purely a frontend
routing table.

---

## Summary of what's genuinely new vs. inherited

| Piece | Needs new `Node`/`Instruction`? | Why / why not |
|---|---|---|
| Datafun core (products, sums, `case`, `for`, naïve `fix`) | No | Ordinary recursive supercombinators over canonical set/list representations (prior spec). |
| Seminaïve ϕ/δ (Part I) | No | Compiles the program twice (`ϕ`, `δ`) plus `semifix`; still ordinary `Expr`/`ECase`/recursive supercombinators. |
| Rizzo `Sig`/`Chan`/⃝ (Part II) | **Yes** | In-place, repeated heap mutation and a driver loop straddling multiple `evaluate` runs are not expressible as pure supercombinators — that mutation *is* Rizzo's contribution over stream-based FRP. |
| Haskell-style ADTs (Part III) | No | Pure frontend sugar over existing sum/product/μ machinery from both halves. |
