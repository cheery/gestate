# fixme.md — where `gestate/` and `spec/` disagree

Read of `gestate/**.py` against `spec/*.md`.  Only **divergences from the
spec** are listed; things the spec never decided are in `spec/errata.md`, and
things `journal.md` Part I already tracks as unbuilt increments are
noted as such rather than re-litigated.

**The numbers in this file are addresses.**  `gestate/*.py` cites them —
fifty-six distinct `F` numbers, in comments explaining why a piece of
code is the shape it is (`declarations.py` F36, `gmachine.py` F95,
`audioextract.py` F94).  So an entry is never renumbered and never
deleted once written: **[resolved]** is what closing one looks like,
and that is why nine tenths of this file is resolved.  The same is
true of `spec/errata.md`'s `D` numbers.

Legend: **[bug]** wrong behaviour · **[missing]** spec'd, not built ·
**[deviates]** built differently than spec'd · **[dead]** built, unreachable ·
**[resolved]** closed since this file was written, kept for the record.

Of 130 entries, **113 are resolved**.  What is left:

| # | State | What |
|---|---|---|
| F5 | partly resolved | `δ(case …)` does not go through `split [ϕe]` |
| F26 | missing | `{: … :}` parses to a type constructor nothing knows about |
| F29 | partly resolved | Property tests and examples exist; golden ASTs do not |
| F32 | partly resolved | Ambiguous `Num`/`Eq`/`Ord` constraints default silently to `Int` |
| F33 | partly resolved | No superclasses, no multi-parameter classes |
| F34 | missing | No orphan-instance rule |
| F35 | missing | No specialization, no existential dictionaries |
| F38 | partly resolved | No monotone/discrete discipline and no eqtype/semilattice/fixtype checks |
| F67 | missing | Nothing enforces the "no variable starting with `d`" rule |
| F93 | deviates | A graph node's `clock` is set only on sources, not inherited |
| F95 | fixed | The fragment admits tuples; the extractor now lays them out |
| F103 | resolved | The same file's canvas builds or fails typechecking, run to run |
| F106 | resolved | The drawn piano retriggers a held key (OS autorepeat) |
| F107 | resolved | Up/Down inside a palette argument runs the command |
| F108 | resolved | `pianoStep` inserts `50` with no trailing separator |
| F109 | resolved | Opening a file joins the previous start in the gesture loop — no cancel, late switch |
| F110 | mostly resolved | Zoom wedge: the mirror only synced after input — tell() every poll now |
| F111 | resolved | Space in `transcript`'s path box erases the proposed path |
| F116 | resolved | Every click was eaten while the command list was open |
| F117 | resolved | Tab did not complete paths in the file dialog |
| F118 | resolved | The list sat over a freshly opened file and caught the first keystrokes |
| F119 | resolved | The caret anchored the scroll — the view snapped back on every model description |
| F120 | resolved | Opening a `.wav` quit the whole editor |
| F121 | resolved | A template inserted while scrolled away appeared behind the list |
| F122 | resolved | A typed path was walked twice — `transcript ../../x` landed in `/home/` |
| F123 | resolved | A finished `open` re-runs from a different directory than its first run |
| F124 | resolved | The directory-watch tests flake under machine load — the kernel's coarse clock, not load |
| F126 | resolved | The crossfade resolved the leaving engine's nodes against the live graph |
| F127 | resolved | A literal applied to arguments answers with an instance at a function type |
| F128 | resolved | The text sniff refused `duet.ges` — the tail-drop moved the boundary instead of removing it |
| F129 | resolved | An exactly-named directory loses to a fuzzy file |
| F130 | resolved | A file you can name is a file the dialog cannot find — and Tab wiped the walk |
| F131 | resolved | An apply drops the notes it crosses — long holds die audibly, the pad most of all |
| F132 | resolved | A content box near the foot renders over the status bar |
| F133 | resolved | `what scope` draws its page outside the window when the panel is low |
| F125 | resolved | A phantom new file read as saved — no tell it was a starter wearing a borrowed name |
| F112 | resolved | The file dialog's listing sometimes lags — measured: a beat only while the model builds |
| F113 | resolved | Undo and redo cross a file switch — one history for the session |
| F114 | resolved | Copy and paste are not commands |
| F115 | resolved | A bank added by an audition could not be listened to — allocators followed the disk |
| F134 | missing | `now : Sig Float` — the current time in seconds, to the substrate |
| F135 | partly resolved | Long features work in silence; the CLI has progress text, the statusline does not |

Several of these are **closed rather than pending** under
`journal.md` Part I's rule — *do not build what nothing needs*.
F33, F34 and F35 have no caller and are not scheduled; F34 is vacuous
outright, there being one compilation unit.  Recording them is the
deliverable, not implementing them.


---

## 1. Seminaïve ϕ/δ — `gestate/seminaive.py` vs `spec/data.md` Part I

### F1. **[resolved]** `ϕ(unbox x = e in f)` emits a reference to an unbound variable

Fixed: both branches go through `_unpack_box`, which binds the pair to a
per-variable temporary (so nested unboxes do not shadow) and projects `x`
and `dx` out of it.  Fixing it exposed the box-representation split
recorded under `journal.md` Part I §17 — a box is now the pair
`(base, change)` on the naive path too, so one built by ordinary code can
be consumed by ϕ/δ-generated code.  The original diagnosis:

`seminaive.py`'s `EUnbox` branch of `phi` had two `return`
statements; the first one won and the second — the correct one — was dead code
with a `# Hmm, this is wrong. Let me rethink.` comment between them.  The live
return built

```python
ELet(False, [(var, EAp(EProj(0), EVar("_box"))),
             ("d"+var, EAp(EProj(1), EVar("_box")))], body)
```

`_box` is never bound and `binding` (the compiled `ϕe`) is discarded entirely.
`spec/data.md` §I.4 requires `ϕ(let [x] = e in f) = let [(x,dx)] = ϕe in ϕf`.

Reproduced:

```
f : Box Int -> Int
f b = unbox x = b in x
main : Int
main = f (Box 5)
```
→ `gestate.lift.LiftError: unbound EVar '_box' inside 'f_phi'`

The δ branch at `seminaive.py:251-258` has the correct shape; copy it.

### F2. **[resolved]** `f_delta`'s parameters are grouped, but `δ(e f)` supplies them interleaved

`seminaive.py:190-196` and `seminaive.py:326`.  For an SC of arity *n* the
implementation builds

```
f_delta = λ x₁ … xₙ dx₁ … dxₙ . δbody
```

but `delta(EAp)` (`seminaive.py:187-189`) implements the spec's
`δ(e f) = δe [ϕf] δf`, which for a curried application `f a b` produces

```
((f_delta ϕa δa) ϕb δb)     -- i.e. arguments in order  a, da, b, db
```

`spec/data.md` §I.4 says δ of a λ is `λ[x]. λDX. δe`, so nested λs give
`λ[x].λDX.λ[y].λDY.δe` — **interleaved**.  §I.4's own note ("arity 2n: n base
points + n changes") is the ambiguous phrasing that led here, but the
application rule in the same table settles it.  At arity 1 the two agree, which
is why nothing fails today; at arity ≥ 2 every `f_delta` binds `dx₁` to `b` and
`x₂` to `da`.

**Resolved** the way the spec reads: `_interleave_params` emits
`x₁ dx₁ … xₙ dxₙ` in both `delta(ELambda)` and `transform`.  The
consequence was worse than the note suggested — it did not merely bind the
wrong names, it made *every* multi-argument Datafun helper miscompile, and
so kept transitive closure (a two-argument `compose`) out of reach.  Tests:
`test/test_relations.py`.

### F3. **[resolved]** `δ[e]` returns an empty set instead of unit

Every zero change is now built at its own type by `gestate/changes.py`:
`()` where `ΔA = 1` (a box, a literal, a primitive, and every discrete
base type — `spec/errata.md` D8's reading, adopted there as the working
rule), `⊥` at a set, and componentwise at a product.  `()` is `ENum(0)`
rather than the spec's `Pack 0 0`, because in gestate tag 0 belongs to an
ordinary constructor (`Nil`) and being distinguishable from the empty set
is the whole point of this item.

One further zero turned out to be untyped and is now typed too: a
variable used inside a `□` but bound outside it cannot change, and δ
emitted the designated bottom for it whatever its type — the shape every
Datalog query has (`f s = fix [r ⇒ s ∨ step r]`).  Inference records the
type on the `EVar` occurrence (`EVar.type_`), so `closure`'s captured
relation now gets `bottom_Set_Tuple2_Cyclic_8_Cyclic_8` instead of
`bottom_Set_Int`.  The fallback survives for an `EVar` inference never
visited, and nothing in the pipeline produces one.

What is *not* settled: the derivative of a primitive **function**.  `δ(e
f) = δe [ϕf] δf` applies it, and `()` takes no arguments.  Such a term is
unreachable today (δ of an arithmetic expression only arises under a set
literal or a `fix`, whose δ is ⊥), and the contract that would settle it
is D8's.  The original text:

`seminaive.py:247-248` returns `EGlobal("bottom_Set_Int")`.  `spec/data.md`
§I.4 is explicit: "`δ[e] = ()` … compiled as `Pack 0 0`", because
`ΔΦ□A = 1`.  Same at `seminaive.py:176` (`δ(ENum)`) and `seminaive.py:182`
(δ of a primitive global): a zero change at a non-semilattice type is `()`, not
`⊥{Set Int}`.  Harmless today only because nothing consumes these values;
type-incorrect the moment anything does.

### F4. **[resolved]** `dummyA` is never generated; `⊥` is used in its place

`dummy` is now what `for` binds and what a dead branch returns, and it is
type-directed (`gestate/changes.py`).  Most of fig. 3.5 folds to a
constant and is emitted inline — `dummy{A} = {}` is the generated `⊥`,
`dummy1 = ()`, a product is the tuple of its components' zeros — which
matters for `spec/errata.md` D3: ⊥-propagation recognises a `⊥` and would
not recognise a call.  Note the two coincide exactly where the
optimization needs them to: at a *set* element type `dummy` **is** ⊥, so
`for (x ∈ e) ⊥ ⇝ ⊥` still fires.  At `(Int, Int)` — a Datalog relation's
element — the zero change is `((), ())`, which it never was before.

The sum case cannot fold: `dummy (ini x) = ini (dummy x)` reproduces the
value's tag, so it is a generated per-type helper, as §I.4.3 says.
`dummy_Maybe_Int` is `Nothing ▹ Nothing | Just x ▹ Just ()`; a recursive
type generates one recursive helper.  Which types need one is not known
until δ has run, so the transform returns its `Changes` builder and the
pipeline emits them afterwards — along with any set type whose `⊥` no
annotated node mentioned.

`dummyA→B f = λx. dummy (f x)` is implemented as
`λx. λdx. dummy (f x)`, since `Δ(A→B) = □A → ΔA → ΔB` in the transformed
world.  Unreachable today: a function-typed `case` field is the only way
to it.  Tests: `test/test_changes.py`.  The original text:

`spec/data.md` §I.4.1 requires `[0x] = [dummy x]` in both `for` loops and
§I.4.2 requires `dummy x` in `case`'s dead branch, with §I.4.3 listing
`dummyA` among the per-type generated helpers (fig. 3.5 of the thesis:
`dummy{A} = {}`, `dummy1 () = ()`, `dummyA×B (x,y) = (dummy x, dummy y)`,
`dummyA+B (ini x) = ini (dummy x)`, `dummy□A [x] = [dummy x]`,
`dummyA→B f = λx. dummy (f x)`).

Implementation substitutes `bottom_Set_Int` everywhere:
- `phi`/`delta` of `EFor` (`seminaive.py:156`, `272`, `274`) bind
  `dx = bottom_Set_Int`;
- `delta` of `ECase` dead branches (`seminaive.py:221-224`) return
  `bottom_Set_Int`.

`helpers.py` generates no `dummy_*` at all.  §I.4.2 stresses that the dead
branch must be `dummy x`, **not** `bottomL`, and that `dummy` at function type
has to re-invoke the function to get a same-shaped result.

### F5. **[partly resolved]** `δ(case …)` does not go through `split [ϕe]`

The two consequences are fixed; the notation is not, because it cannot
be.  `split [ϕe]` *is* the outer `case ϕe` here: □ is erased (§I.6), so
`Φ(□(A+B))` and `Φ(□A+□B)` — which D7 shows are genuinely different types
— have the same runtime shape, and gestate has no `split` to emit.  What
the discrete binding buys is what the code now uses it for:

- the dead branch returns `dummy xᵢ`, which needs `xᵢ` in scope (F4);
- it binds as many fields as *its own* constructor has.  It bound exactly
  one whatever the arity, so `case m of Nothing ▹ … | Just v ▹ …` emitted
  a dead `Nothing` branch binding a field `Nothing` does not have.  Dead
  code, but code the machine would have mis-split had a tag ever flipped.

Left open: nothing in the implementation *names* the split, so a later
typed IR would have to reintroduce it, and `empty?`/`split` as surface
constructs are D6's, not this item's.  The original text:

`seminaive.py:208-244` cases on `ϕe` directly and reads changes out of a
separately let-bound `δe`.  `spec/data.md` §I.4.2 (and fig. 3.3) require
`case split [ϕe] of (ini Y ▹ let [x] = Y in (λDX. δfᵢ) (case δe of …))ᵢ`, i.e.
the base point must be bound **discretely** via `split`.  Since □ is erased at
runtime the shapes coincide for the cases that work, but the "bind `x`
discretely" step is what licenses using `x` in `dummy x` (F4) and in `δfᵢ`'s
context per §I.3.  Related: the dead branch synthesises `["_"]` as the binder
list for *every* other tag (`seminaive.py:222`) regardless of that
constructor's arity, which will mis-bind as soon as a tag with arity ≠ 1 shows
up.

### F6. **[resolved]** `semifix`'s convergence test

Fixed in both spec and implementation: the test is `dx ⊑ x` via a
generated `subset_L`.  See `errata.md` D2 — the first expressible Datalog
query hung under the old one.  The original text:

`seminaive.py:368-376` tests `eq_Set_Int dx' bottom_Set_Int`, faithfully
implementing `spec/data.md` §I.5 — but §I.5 itself disagrees with the thesis,
which tests `dx ⊑ x`.  See `spec/errata.md` D2; the fix belongs in the spec
first, then here (and `helpers.py` needs a generated `subset_*`/`leq_*`
alongside `eq_*`).

### F7. **[resolved]** ϕ/δ is applied to every user SC of a Datafun program

Gated per supercombinator, and per *half*: the two are needed for
different reasons and neither implies the other (`seminaive.Plan`).

- **ϕ** rewrites `fix` to `semifix`, packs a box as a pair, and binds a
  `for`'s `dx`.  A body with none of those is rebuilt identically, so it
  gets no `_phi` and every call site keeps calling it by name.
- **δ** is needed where something *differentiates* a call to it, which is
  a reachability question rather than a syntactic one.  Gating it on "the
  body mentions a semilattice" — the obvious criterion, and the one the
  roadmap proposed — is unsound: `id` mentions none and
  `fix [r ⇒ id r]` still needs `id_delta`.  ϕ calls δ at exactly one
  place, `ϕ[e] = (ϕe, δe)`, so the demand starts at the globals under a
  box and closes over the call graph.

Measured on the transitive-closure query: 138 generated supercombinators
down to 90, of which the ϕ/δ halves are 6 rather than 54, and compilation
~25% faster.  The six are exactly right — `closure_phi` (holds the `fix`,
nothing differentiates it), `compose_phi`/`compose_delta` (set literals,
and called under the box), `fst_delta`/`snd_delta` (no Datafun in them at
all, but applied inside the box), `main_phi`.

Since a wrong gate would show up as a missing global at run time,
`SeminaiveCtx.has_delta` raises instead: if δ ever asks for a derivative
the plan did not schedule, that is a compiler bug and it says so.

**ϕ became structural while doing this.** It had no rule for the Rizzo
formers and returned them *unrecursed*, so a `fix` under a `:::` stayed
an `EFix` and compiled to the naïve `fix_Set_Cyclic_8` — against
`spec/data.md` §0's "a `fix` buried inside a signal's per-tick body gets
seminaïved in place", and the same defect as F9 one level down.  It now
rebuilds an unknown construct from its transformed children.  δ keeps its
own fall-through: a signal's change is not its subterms'.

Still not "Datafun-typed subterms only" in the strict sense — the unit is
a definition, not a subterm — but a definition with no Datafun construct
in it is now left alone entirely.  Tests:
`test/test_transform_scope.py`.  The original text:

`pipeline.py` ran `seminaive_transform` on all SCs whenever any set
type existed — and forced a default `Set Int` when the
program mentioned none, so this was unconditional.  `spec/data.md` §0 scopes the
pass to "[Datafun-typed subterms only]" and §I.4.3 to programs "using seminaïve
evaluation".  Consequences: every FRP SC gets a nonsensical `f_delta`
(`δ(head s)`, `δ(x ::: t)` fall through `delta`'s final `return expr`,
producing the *original* expression as its own change), and SC count doubles
for programs with no `fix` at all.

### F8. **[resolved]** `_BUILTINS` and every generated name are hard-wired to `Set Int`

Fixed: `ESet`/`EFix`/`EFor` carry their inferred type out of inference,
and every helper reference — `fix`, `for`, `semifix`, `bottom`, `join`,
`union` — is selected from it.  `_is_user_sc` matches helper names by
prefix rather than by a hardcoded list.  Zero changes whose type the tree
does not record (δ of a literal, of a primitive, of a `case`'s dead
branch) still land on one designated bottom, which `fixme.md` F3 will
settle.  The original diagnosis:

`seminaive.py:73-80` lists `eq_Set_Int`, `union_Set_Int`, … as literals, and
`phi`/`delta` emit `bottom_Set_Int`, `join_Set_Int`, `union_Set_Int`,
`semifix_Set_Int` unconditionally (`seminaive.py:149,156,176,182,248,262,272-285`).
`make_semifix_helpers` (`seminaive.py:345`) only ever emits
`semifixL_Set_Int`/`semifix_Set_Int`.  §I.4.3 requires one instance of each
helper per monomorphic type.  Tracked as `journal.md` Part I §17, but the
ϕ/δ side of it is not mentioned there.

### F9. **[resolved]** `transform` skips `main`

`main` is transformed like any other supercombinator.  It keeps its own
name — every transformed SC is kept as an alias for its `_phi`, which is
what the machine's `PushGlobal("main")` finds — so the entry point is
unaffected, and a `fix` in `main` costs what it costs anywhere else:
13,519 G-machine steps before, 12,652 after, against 12,657 for the same
query one definition over (the difference is the indirection).

**Why it was skipped** is not recorded anywhere, and nothing in
`spec/data.md` supports it.  What actually stood in the way was a
different bug: ϕ renamed a global to `name_phi` whenever `_is_user_sc`
*guessed* it was a user definition, and that guess was wrong twice —
`chr`/`ord` are machine primitives that appeared in none of the exclusion
lists, and a user definition starting with a single `_` was skipped by
`transform` while every reference to it was still renamed.  Both produce
`unknown global 'chr_phi'` / `'_base_phi'` at run time, in any
supercombinator; `main` escaped only by not being transformed.  So the
skip was masking, not preventing.

The renaming now follows the set of names the transform is actually
generating pairs for, which is the ground truth it had all along.  That
is also what `fixme.md` F7 / roadmap 0.4 needs: once ϕ/δ is gated per SC,
"which names have a `_phi`" stops being guessable from the name at all.

Two things this leaves behind:

- The **naïve `fix_X`/`fixLoop_X` loop is now unreachable from user
  code**.  Only `__`-generated supercombinators are still skipped, and a
  `fix` in one of those does not work for an unrelated reason (F58).  The
  helpers stay generated: `_desugar_datafun` needs the fallback for any
  `EFix` that survives the transform, and the naïve loop is the one
  `spec/data.md` §I.5 defines `semifix` against.
- Instance-method bodies are still not transformed.  A `for` written in
  one is evaluated naïvely — the same defect one level down, and F7's to
  weigh, since transforming generated code cuts against gating it.

The original text:

`seminaive.py:312` skips `main`, `_`-prefixed names and helpers.  Nothing in
`spec/data.md` exempts `main`; the effect is that a `fix` in `main` runs naïve
while the same `fix` in a helper SC runs seminaïve — two code paths for one
construct.

### F10. **[resolved]** No ⊥-insertion / ⊥-propagation pass — see §7's D3/D4 entry

See `spec/errata.md` D3 — this is the pass the asymptotic speedup depends on.
It is absent from the spec *and* the implementation, so `spec/data.md` §I.7's
proposed Θ(n²) test would fail today.  Listing it here as well because
`_desugar_datafun` (`pipeline.py:183`) is the natural place for it.

---

## 2. Datafun helpers — `gestate/helpers.py`

### F11. **[resolved]** Set element comparison is hard-coded to integers — see §7

The *dispatch* half is fixed (F8): helpers are generated and selected per
element type.  The *body* half stands — `_gen_eq`/`_gen_union` still emit
`prim_eq_int`/`prim_lt_int`.  It is no longer silent, though: a set whose
element type is not integer-represented is now rejected with a message
naming this item, so `{Bool}` (a perfectly good fixtype) reports that the
implementation cannot build it rather than miscomparing at run time.  The
original diagnosis:

`helpers.py:84-95`: `_eq_int`/`_lt_int` always emit `prim_eq_int`/`prim_lt_int`
regardless of the set's element type, while `_type_suffix` names the generated
SC after that element type.  So `eq_Set_Bool` compares `Bool` values with
integer primitives.  `spec/data.md` §I.4.3 requires per-monomorphic-type
`eqA`/`unionA`.  (`journal.md` Part I §17 covers the *dispatch* half of
this; the *body* half is this item.)

### F12. **[resolved]** `generate_helpers` is an unused, stale copy

Deleted.  It had already diverged: a guard added to the live generator
landed in the dead copy first.

### F13. **[resolved]** `diffL` (change minimization) — see §7's D3/D4 entry

Not spec'd either — see `spec/errata.md` D4.  Named here because `helpers.py`
is where it would be generated, next to `eq_`/`union_`/`bottom_`/`join_`.

---

## 3. Rizzo / FRP — `gestate/reactive.py`, `gestate/gmachine.py`, `gestate/desugar.py`

### F14. **[resolved]** `⊛` and `5` are unreachable

Fixed.  `expr.py` has `EAppFa`/`EAppEx`; `desugar.py` recognises `<*>`,
`<@>` and `|>` (sugar for `▷`, `infixl 4` each); `infer.py` types them at
Rizzo fig. 3; `compile_c` emits `MkDelayAp` and `Pack(TAG_EXISTS5, 2)`.
`FaL`/`ExL` exist as type constructors, which is F39.  Signals computed
from other signals work — `map`, `mkSig`, `filter` and `sync` combinators
are in `test/test_frp.py`.  The original diagnosis:

`spec/frp.md` specifies `compileC (EApp∀ s t) = … MkDelayAp` and
`compileC (EApp∃ s t) = … Pack tagExists5 2`.  In the implementation:

- `expr.py` has no `EApp∀`/`EApp∃` node;
- `desugar.py` recognises `head`, `delay`, `wait`, `watch`, `tail`, `sync`,
  `never`, `chan`, `:::` — and nothing else (`desugar.py:251-294`);
- `compile_c` (`gmachine.py:534-570`) has no clause emitting `MkDelayAp` or
  `Pack(TAG_EXISTS5, …)`;
- the `MkDelayAp` instruction (`gmachine.py:205`, `815`, dispatched at `909`)
  and `TAG_EXISTS5` (`gmachine.py:328`) are therefore **dead**, and
  `advance`'s `TAG_EXISTS5` branch (`reactive.py:128-152`) can never run.

Since `▷ = delay f 5 x` is the only way to move a function across `⃝∃`, no
program can currently build a signal whose update is *computed* from another
signal — only `wait`-driven leaves work.  `map`, `mkSig`, `sample`, `switch`,
`filter`, `zip`, `scan` are all out of reach.  (Related spec gap: `errata.md`
R2 — `syntax.md` gives these operators no notation either.)

### F15. **[resolved]** `ticked` fires on `TAG_DELAY`

Fixed: the case is gone, and so is `_update_one`'s paired `gfix cycle`
special case.  Neither is reachable now that `delay t : FaL A` cannot type
as a signal tail.  `gfix` compiles to the letrec `letrec x = delay v ; v =
t in v` rather than a self-referential delay node, so `x` is bound to a
⃝∀ wrapper around the fixed point's *value* — advancing it unrolls the
recursion instead of yielding another delay.  The original diagnosis:

`reactive.py:53-56`:

```python
if node.tag == TAG_DELAY:
    # delay t unrolls every step — always fires
    return True
```

`spec/frp.md`'s `ticked` has exactly six cases (never, `5`, wait, watch, tail,
sync) — mirroring fig. 10 — and no `delay` case, because `delay t : ⃝∀A` is
never a signal tail (tails are `⃝∃(Sig A)`).  The extra case exists to make
`syntax.md`'s `gfix self => 0 ::: delay self` run; that example is ill-typed
against the paper (see `errata.md` R3).  Effect: any signal whose tail is a
`delay` node updates on *every* input on *every* channel, i.e. an empty clock
behaves like a universal one.

Paired with `_update_one`'s `gfix cycle` special case
(`reactive.py:205-207`), which re-marks the signal ticked while keeping the
same tail — not in the spec either.

### F16. **[resolved]** `advance` on `sync` returned a `sync` node

Fixed: `_pack_left1`/`_pack_left2`/`_pack_both` build `SyncLeft`/
`SyncRight`/`SyncBoth`, the constructors of the built-in `Sync a b`, so
user `cont` functions can `case` on the result.  See `errata.md` R6.  The
original diagnosis:

`reactive.py:174-183`:

```python
def _pack_left1(v):   return NCon(TAG_SYNC, (v, NCon(TAG_NEVER, ())))
def _pack_left2(w):   return NCon(TAG_SYNC, (NCon(TAG_NEVER, ()), w))
def _pack_both(v, w): return NCon(TAG_SYNC, (v, w))
```

The advance semantics must produce `in1 (in₁ v)`, `in1 (in₂ w)`, `in2 (v, w)`
at type `Sync A B = (A+B)+(A×B)` — an ordinary sum/product that user code
pattern-matches (every `cont` in the paper's combinators does).  Producing a
`TAG_SYNC` node instead means the value handed back is a delayed-computation
shape, so a `case` over it hits `CaseJump: no alt for tag 92`.  `spec/frp.md`
names these `packLeft1`/`packLeft2`/`packBoth` without defining them, which is
`errata.md` R6 — but the current definitions are wrong under any reading.

### F17. **[resolved]** No `cl` (clock) function

Fixed: `reactive.cl` recurses over the ⃝∃ sub-tags per fig. 10, and
`reactive.clock_fires` states the invariant tying it to `ticked`.  The
driver snapshots every signal's clock before a sweep begins — §4.3's
"with respect to the heap from before the step" — and checks each
`ticked` answer against it, so a driver that recomputed clocks mid-sweep
now fails loudly instead of silently.  See `errata.md` R7.

### F18. **[resolved]** No now/earlier check on `head`

Fixed: `NSig.current` is the ✓ frontier as a per-cell mark.  `SigHead`
raises on a signal the sweep has not reached, and `ticked`/`advance` do
the same for `watch l`/`tail l`, whose fig. 10 rules are also stated
against the new heap.  A scheduler-ordering bug is now an error rather
than a stale read.  See `errata.md` R8.

### F19. **[resolved]** Channel context is never tracked

Fixed: `GmState.chans` is Δ, exposed as `GmReactive.chans`; `NewChan`
extends it with the element type inference recorded on the `EChan` node,
and `advance`'s sub-evaluation shares the dict so a channel minted
mid-sweep registers.  `react` rejects an input on a channel that was never
allocated.  See `errata.md` R11.

### F20. **[resolved]** `advance` for `TAG_EXISTS5` mutated the shared `GmState`

Fixed: `_apply` runs `f v` on a scratch `GmState` sharing the heap,
globals, now-heap and channel counter, so a `GmError` inside it cannot
wedge the live machine.  (The old code also built `NAp(v, f)` — operands
reversed — which would have been a plain bug once it was reachable.)  The
original diagnosis:

`reactive.py:139-152` pushes onto `gm.stack`, overwrites `gm.code`, appends to
`gm.dump`, calls `run`, then pops and restores.  `spec/frp.md` models this as
`putStack [f, v'] s' then [Mkap, Eval]` on a state value and returns
`(result, s'' with stack popped)`.  The in-place version leaves `gm.code`
empty and relies on the dump being balanced; a `GmError` inside `run` leaves
the machine wedged.  Dead code today (F14) but it is the one place the
scheduler re-enters the evaluator, so it should match the spec before it is
reachable.

### F21. **[resolved]** `ticked`/`advance` required already-forced operands

Fixed: both dereference their node and every operand they inspect, and
`MkDelayAp` does the same — a `gfix` binder reaches it as an indirection
into the letrec cell it shares.  The original diagnosis:

`reactive.py:60-64` returns `False` when a `wait`'s argument is not literally
an `NChan`, and `reactive.py:66-75`/`118-126` likewise for `NSig`.  A `Pack`ed
argument can be an `NInd` or an unforced graph (`compile_c` inserts `Eval`
before `Pack`, so this holds today for source-built nodes, but not for nodes
rebuilt by `advance`).  `advance`'s `TAG_DELAY` branch already chases one level
of `NInd` (`reactive.py:109-112`); the others do not.

### F22. **[resolved]** FRP tests

`test/test_frp.py` covers the typing rules, the rejections that
distinguish the two modalities, and four runtime traces (a `wait`-driven
signal and its clock, `map`, `watch`/`filter`, `sync`), plus signal
identity across steps.

**The heap-shape traces are now there too**, which is what `spec/syntax.md`
§"Testing strategy" asked for.  Per-step *values* are the weaker claim: a
driver that reallocated a fresh cell on every update, or let the live set
grow, produces identical values and passes every value test in the file.

For §4.5's `sample`: three cells at init; every cell keeps its identity
across every step and the live set stays at three (§4.4's "`hUpdate l …`,
not a fresh `l4` pointing back" — and `_update_one` really does allocate a
new signal and fold it in, so the test guards a delicate invariant rather
than a tautology); and the sampler's clock **is** the sampled signal's,
`cl (tail l3) = cl (tail l1) ≠ cl (tail l2)`, which says at the node what a
value trace only says for one run.

For `filter` (`errata.md` R12), the structurally different one: `watch l`'s
clock is `{(sig, l)}`, a **signal** clock rather than the channel clock
`sample` inherits through `tagTail`.  That is *why* the allocation-order
invariant matters for `watch` — whether the watcher fires depends on the
value `l` holds this instant, so `ticked` must read `l` after `l` was
updated in the same sweep.  The trace is now written into `frp.md`, which
was R12's remaining half.

---

## 4. Surface syntax — `gestate/syntax/` vs `spec/syntax.md`

### F23. **[resolved]** `Box` was reserved in the tokenizer but not in the spec's list

**Fixed.**  `syntax.md`'s reserved-word list now includes `Box` and
`deriving`; its fixity table now lists `..` at `infixl 7`; and a program
that declares a fixity for `->` (or `~>`) is **rejected** rather than
silently overriding the built-in — the spec said it could not be
overridden and it could.  `_UNOVERRIDABLE` in `descend.py`.


`tokenize.py:52-56` reserves `Box`; `spec/syntax.md`'s reserved-word list is
`class instance case let letrec where in for of type kind gfix fix unbox given
using`.  Either the spec gains `Box` or the tokenizer loses it (it is a
capitalised word, so it would otherwise lex as a type/constructor name — which
is arguably what `Box type` wants).

### F24. **[resolved]** `->` could be redefined by a user fixity declaration

**Fixed.**  `syntax.md`'s reserved-word list now includes `Box` and
`deriving`; its fixity table now lists `..` at `infixl 7`; and a program
that declares a fixity for `->` (or `~>`) is **rejected** rather than
silently overriding the built-in — the spec said it could not be
overridden and it could.  `_UNOVERRIDABLE` in `descend.py`.


`descend.py:70-80` installs user `VFixity` declarations first and only fills in
`DEFAULT_INFIX` for operators the user did not mention, so
`infixl 9 ->` silently wins.  `spec/syntax.md`: "`->` is the only operator that
cannot be overrided."

### F25. **[resolved]** `..` had a default fixity the spec did not give it

**Fixed.**  `syntax.md`'s reserved-word list now includes `Box` and
`deriving`; its fixity table now lists `..` at `infixl 7`; and a program
that declares a fixity for `->` (or `~>`) is **rejected** rather than
silently overriding the built-in — the spec said it could not be
overridden and it could.  `_UNOVERRIDABLE` in `descend.py`.


`descend.py:51` adds `"..": ("L", 7)`.  `spec/syntax.md` lists `..` among the
reserved character sequences and shows `4 .. 30`, but its default-fixity table
has no row for it — so the implementation is inventing a binding power equal to
`+`/`-`.  (Spec-side gap: `errata.md` S3.)

### F26. **[missing]** `{: … :}` parses to a type constructor nothing knows about

`parse.py:845-869` builds `VConId("EqSet")` / `VApp(VConId("EqSet"), …)` for
the eq-set syntax.  `EqSet` appears nowhere else in `gestate/` — no kind
(`kindcheck.py:76-88`), no desugaring, no runtime.  Any program using
`spec/syntax.md`'s eq-set literals or types dies downstream with an unknown
type constructor.

### F27. **[resolved]** `[: a :]` / `Score` — bodies, layout, and MIDI out

The *spec* half is done.  `music.md` now says what a `[: A :]` is — a
box-layout tree eliminated by `layout : [: Void :] -> [(Onset, Offset, R)]`
— and types every operator (`errata.md` S4).  The surface is writable:
`[: a :]` parses in a signature (F61), `Void` exists (F60), and a sequence
of notes resolves correctly (F59).  `@` and `|~|` were withdrawn rather than
implemented — `>>=` is instrument selection, and stretch is a value `sp`.

What is missing is **bodies**: no `Score` constructor, no operator
definition, no layout stage, and `ToInt` is not in the prelude.  Also
unspelled: the committed-leaf constructor `R -> [: a :]`, the counterpart of
`'` that an instrument returns.  Tracked as `journal.md` Part I §11.


**Done, end to end.**  `gestate/music.ges` declares `Score a` as an ordinary
data type and defines every operator; `gestate/midi.py` reads the layout out
of the heap and writes a Standard MIDI File.  A program supplies
`score : [: Void :]` and `bpm : Int`; the renderer supplies `main`.
`test/test_music.py` asserts on `(onset, offset, program, key, velocity)`
tuples rather than on printed heaps.

**Music is not in the core prelude**, and could not be: it declares eight
constructors, a constructor's tag is its position, so merging it would
renumber `Nil`/`Cons` for every program in the language — 61 tests failed
exactly that way when it was — and every non-musical program would pay its
compile time, which is superlinear in program size (98s to 230s across the
suite).  The MIDI backend prepends it to a music program's source instead,
which needs no module system.

Three parse defects turned up while writing it — a trailing comment
breaking an indented continuation (F70), a lambda unable to take a pattern
(F71), and a single-line `case` inside parentheses (F72) — and all three
are now fixed, so `music.ges` says what it wanted to.  A fourth is by
design: a projection needs its base type known and a lambda parameter's is
not, so the event helpers destructure in the lambda instead (F28).

Still open, and deliberately: `sp` is withdrawn (engraving, not
performance), and `layout` divides with `prim_div_int` rather than
rejecting an inexact `|/ n` — `beat` is 96 so every division anyone writes
is exact, and the check has no caller yet.
### F28. **[resolved]** Record/tuple projection — resolved from the type, not `AttrN`

`spec/syntax.md` specifies that `rec.N` desugars to the `.N` member of an
`AttrN` class with an associated type, for digits 0–15.  `VProj` is parsed
(`parse.py:594-597`) and rewritten by `descend.py:129-130`, but `desugar.py`
has no `VProj` case — so `x.0` never reaches the type checker, and no `AttrN`
classes are declared anywhere.


**Implemented, deliberately not the way `syntax.md` prescribes.**  Sixteen
`AttrN` classes with associated types would make `f p = p.0` principal —
`(Attr0 a) => a -> Field0 a` — at the cost of ~120 generated tuple
instances and sixteen classes in every program's namespace, buying
record-polymorphism nothing in this language has asked for while D9 has
already settled that the Datafun half is monomorphic on purpose.

So the base's *type* decides.  `x.N` desugars to an `EField` node that
survives to inference — it cannot be lowered earlier, because a tuple and a
record are different runtime shapes (`NTuple` with `Proj` against a
one-constructor `NCon` with a `case`) and desugaring runs before there are
any types.  Inference resolves the shape and a small pass lowers it, so no
later stage knows the node exists.

The cost is exactly one case: an unannotated `f p = p.0` is rejected, and
the message says to give a signature or destructure with a pattern.
Everything else — out of range, a multi-constructor type, a named field, a
type that is neither — is reported in its own terms.

Two things fixed alongside.  **Projection bound to the application rather
than the atom**, against the parser's own docstring, so `show p.1` read as
`(show p).1`; nothing could depend on that, since projection did nothing at
all.  And `x.0.1` does *not* lex as two projections — `0.1` is a float
literal, so the phrase reads `x . 0.1` and a nested projection needs
parentheses.  Recorded rather than fixed: stopping the number rule after a
`.`-projection is a lexical change nothing yet needs.

`test/test_projection.py`.

### F44. **[resolved]** Constructor sub-patterns swallowed a trailing cons

`parse.py`'s constructor-pattern branch parsed each argument with
`_parse_pat`, which consumes a trailing `::`.  `f (Just x :: xs)` therefore
parsed as `Just (x :: xs)` — silently the wrong program, since both parse.
Arguments are atoms now, as in expression space.  Found while adding the
`:::` pattern, which made the same mistake visible as a type error.

### F46. **[resolved]** The formatter dropped meaning-changing parentheses

`format` promises output that re-parses to the same AST.  Three cases
broke it, all pre-existing and all found by round-tripping the new FRP
syntax:

- an operand that runs to the end of the expression (`x => e`, `let … in
  e`, `case … of …`) was not parenthesised, so `(x => x + 1) + 2` came
  back as `x => x + 1 + 2`;
- `_fmt_infix` compared operand precedences but ignored associativity, so
  `(a -> b) -> c` came back as `a -> b -> c`;
- a cons pattern was printed bare in parameter position, so `f (x :: xs)`
  came back as `f x :: xs`.

`_fmt_pat` now takes an `atom` flag for the juxtaposed positions
(parameters, constructor arguments) and leaves a `case` alternative bare.

### F45. **[resolved]** A multi-line `case` inside parentheses does not parse

Fixed: the tokenizer records the bracket depth at which each layout level
was opened and emits the block's `DEDENT` just before a closing bracket
that ends it; the parser steps over those `DEDENT`s when it wants the
bracket.  This is Haskell's parse-error rule narrowed to the one case
that provokes it.  `spec/syntax.md` §Layout now says what closes a block,
not only what opens one.  The paper's `switch` can be written with `cont`
as a local lambda.  Tests: `test/test_layout.py`.

### F47. **[resolved]** `Subst.apply` diverged on a self-binding

`compose` produced `α ↦ α` whenever the two substitutions unified the
same pair of variables from opposite sides (`{17 ↦ β}` after `{β ↦ 17}`),
and `apply` chased the binding forever.  `unify`'s occurs check never saw
it — it is created by composition, not by binding.  `extend` now drops an
identity binding and `apply` follows variable chains iteratively with a
cycle guard.  Pre-existing; it surfaced as soon as F45's fix let a
program be written whose inference composes substitutions that way.
Tests: `test/test_types.py`.

### F48. **[resolved]** A dictionary slot for an undefined method held `0`

`elaborate` filled a missing method's slot with `ENum(0)`, reasoning that
"a well-typed program never projects the slot".  It does: the synthetic
`Num (Cyclic n)` instance defined only `fromInteger`, so `+`/`-`/`*`
projected the placeholder — and `Unwind` on a number ignores the spine,
so `x + y` evaluated to `0` at every `Cyclic` type.  The slot now holds an
undefined global, which fails if projected and is inert otherwise, and
the synthetic instance defines all four methods.

### F49. **[resolved]** `Cyclic n` arithmetic did not wrap

Only `fromInteger` reduced mod `n`; `+`/`-`/`*` (once they existed at all,
F48) would have let a value escape its own type.  That matters beyond
arithmetic: the fixtype rule takes `Cyclic n` for a finite type, and a
`Cyclic 4` holding 6 would make `fix` promise a termination it could not
deliver.  `Bounded lo hi` still does not confine its values
(`main : 0 .. 3; main = 7` gives 7), so it is deliberately *not* counted
as a finite eqtype until its `fromInteger` clamps or wraps.

### F29. **[partly resolved]** Property tests and examples exist; golden ASTs do not

`spec/syntax.md` §"Testing strategy" specifies golden ASTs for every example in
`examples.md` (file does not exist), property tests for unification totality,
Charney-style G-machine heap-shape tests, and a music regression.

**The property tests are done** — `test/test_properties.py`, the two the
roadmap called highest-value:

- **Set operations against Python's.**  Random literals, joins, comprehensions,
  guards, two-generator products, and `fix` closure, each checked against the
  same computation in Python.  This is the half that covers what kept moving.
- **The match compiler against a direct interpreter.**  A random two-column
  matrix over `Maybe Bool`, checked at all nine values, exercising column
  grouping, nested sub-patterns and the mixture rule.  Matrices with an
  unreachable row take the other branch: the compiler must *reject* them, and
  the test confirms with Python that a row really is dead.

Two things they had to work around, both worth knowing.  **A printed result is
not a value**: `evaluate` renders unevaluated thunks, so a `Cyclic 8` element
can come out as `((<global arity=2> 8) 2)`, an unforced `mod 8 2`.  The tests
read a set back by *membership probing* — `holds (for (x in S) guard (x == k))`
— which forces to a `Bool` and uses only surface syntax.  And **compile cost is
superlinear in program size**, so batching every case of a property into one
program is slower than several small ones; measured, 12 probes per program
beats 60 by a third.

Generation is seeded `random`, not Hypothesis.  The project has no third-party
dependencies, and the input spaces are small enough that a failure is already
near-minimal — shrinking is what would earn the dependency, and nothing needs
it yet.

**`examples/` exists** — six programs covering both halves of the language
and the music backend, each run by `test/test_examples.py` against the
result its own comments claim, so a stale example is a failing test.  The
music regression this item asked for is among them.

Writing them was worth more than the files: it found **five defects that
653 tests had not**.  Three parse bugs (F70, F71, F72) and two in the
`typecheck` CLI — a `NameError` that made `--check` crash, and, once that
was fixed, a false `No instance for Eq a` on *every* program, because the
CLI solved constraints an SC's own context grants while `pipeline.compile`
filters them.  The crash had been masking the false positive.

That is the blind spot this item is really about: every other test was
written by someone who already knew the workarounds.  Nobody had written a
program the way a reader of the specs would.

**The rendered `.mid` files are golden**, which is a better artifact than
the ASTs this item asked for: rendering is byte-deterministic, so
`test_examples.py` re-renders each music example and compares, and a change
to layout, tick arithmetic, event ordering or channel allocation shows up
as a diff in a file you can also listen to.

Still missing: golden *ASTs*, and Charney-style heap-shape tests.

---

## 5. Types and classes — `gestate/unify.py`, `infer.py`, `elaborate.py`

### F30. **[resolved]** `unify` raises rather than returning `Either` — deliberate

`spec/types.md` §2 demands `unify :: Type -> Type -> Either TypeError Subst`
and, under "Totality", "Every failure path returns a `TypeError` value, never
an exception".  `unify.py` raises `UnifyError`.  The occurs check itself is
present and mandatory as spec'd.

**Assessed and declined**, and `types.md` §2 is amended to say so.  The
requirement is a Haskell-ism: there, `error` is unchecked and invisible in
the type, so `Either` is how a failure is made impossible to ignore.  A
Python exception is already impossible to ignore, and converting would touch
28 call sites.

What was checked rather than assumed — whether anything needs to *recover*:

- `coherence.py` asks unification a genuine yes/no question (do two instance
  heads overlap?).  It is a two-line `try`, tight enough that nothing else
  can fall into it, and reads as well as a `Result` would.
- `infer.py`'s `fix` rule and `typecheck.py` catch to *enrich* the message,
  not to recover.
- `elaborate.py` catches broadly around a whole `infer_instance_method`,
  which could swallow an unrelated failure — but it also catches
  `InferError`, so the hazard is the breadth of that `except`, not the
  encoding of `unify`.  Recorded here rather than fixed; it changes no
  behaviour today.

**What *was* wrong here is fixed**: the error message read its arguments in
the wrong order.  `unify` is symmetric, but its message is not — it says
"expected `b`, got `a`" — and the application rule in `infer.py` called it
`(expected, actual)`.  So `f : List Int -> Int` applied to `True` reported

    Type mismatch: expected Bool, got (List Int)

with the two roles swapped, which is precisely the "points at the wrong
place" this stage is about.  The argument order is now documented as part of
`unify`'s interface and the call site corrected:

    Type mismatch: expected (List Int) (at 0:4–0:12), got Bool

### F31. **[resolved]** Substitution dropped source spans

`types.py:94-106`: `Subst.apply` rebuilds `TFun`/`TApp` without carrying the
`span` field, so a type that survives one substitution loses the location it
came from.  `spec/types.md` §9 requires spans threaded "through `Type` and
`Kind` representation from the beginning" so that "when `unify` fails, report
original source locations".  `unify.py` reads `span` off the types it is
handed, so the plumbing existed but was severed at the first `apply`.

Fixed: `TApp` now carries `t.span` through `apply` as `TFun` already did.

### F32. **[partly resolved]** Ambiguous `Num`/`Eq`/`Ord` constraints default silently to `Int`

`elaborate.py:356-368`.  `spec/typeclasses.md` §3 Phase 2 says an ambiguous
predicate left at the top level is an **error** — "Do not leave ambiguous
constraints to the runtime" — and §9 item 2 asks for "explicit, closed, opt-in
defaulting rules — never silent, never open-ended".  The current behaviour is
the silent, built-in kind.  (`journal.md` Part I §18 documents the
choice; the spec forbids it.)

### F33. **[partly resolved]** No superclasses, no multi-parameter classes

`spec/typeclasses.md` §3 Phase 2 ("Simplification: Remove redundant predicates
using superclass relationships") and §6 (which motivates associated types
precisely by "classes with more than one type parameter") both assume these
exist.  Tracked as `journal.md` Part I §8 (skipped).

### F34. **[missing]** No orphan-instance rule

`spec/typeclasses.md` §4 makes the orphan rule the enforcement mechanism for
global coherence, "decided before anything else is built".  `coherence.py`
implements overlap and the three Paterson conditions (§5.1) and
`constraint.py:21` has the depth cap of 200 (§5.2) — the orphan rule is the
missing third.  It is vacuous with no module system, but the spec's §4 asks for
it "as a separate compilation-unit check", so it should be recorded as blocked
on modules rather than silently absent.

### F35. **[missing]** No specialization, no existential dictionaries

§7.2 (specialization at statically-known call sites, "the default
optimization") and §7.3 (`ShowBox`-style boxed/existential dictionaries) are
unimplemented.  §7.1 dictionary passing — the always-correct default — is in
place.  Tracked as `journal.md` Part I §10.  Note the interaction with
`errata.md` R9: specialization + inlining is unsound near `head`/`delay` and
the spec has no rule fencing it off.

### F36. **[resolved]** Signature type variables are metavariables, not skolems

A signature's variables are now **rigid** in the body they declare.
`desugar_signature` marks them — `TVar.rigid`, plus the name they were written
with, so a message says `a` and not `a-1003` — and the two things that could
decide a variable both refuse to:

- **Unification** will not bind one.  The reverse direction still binds: a
  metavariable *may* be bound to a skolem, which is what lets a signed body
  use its own parameters at all.  `f : a -> Int ; f x = x + 1` now reports
  that `a` stands for whatever type the caller chooses.
- **Resolution** will not pick an instance for one.  `match_head` used to let
  any bare variable match any head, and `_default_ambiguous` used to send it
  to `Int`; a skolem is not ambiguous but *decided elsewhere*, so both leave
  it alone and the missing dictionary is reported instead, naming the context
  to write.  Without this half `f : a -> a ; f x = x + 1` was still accepted
  (defaulted to `Int`) and `f : a -> String ; f x = show x` silently took
  whichever `Show` instance came first and printed nothing.

Rigidity never leaves the body: a use site instantiates the scheme into fresh
metavariables, and rigidity is excluded from `TVar`'s equality because the
*id* is what says which variable this is.

One thing had to move with it.  `infer_instance_method` entered an
unconstrained supercombinator into its environment monomorphically, which
worked only because the first use bound its variables and a second use at
another type silently lost.  With signature variables rigid the first use
*fails*, the whole instance-method body goes uninferred, and routing falls
back to by-name — which inside `instance (Show a) => Show (List a)` cannot
tell the context dictionary from a recursive call.  Every top-level type is
closed, so it now quantifies whether or not the definition has a context.
Tests: `test/test_skolems.py`.  The original text:

`f : a -> Int ; f x = x + 1` type-checks by unifying `a` with `Int`.  Already
recorded under `journal.md` Part I §19 "Remaining"; noted here because
`spec/types.md` §3's whole point ("lambda-bound variables are monomorphic …
This is correct rejection, not a bug") is about rejecting exactly this class of
program.

### F37. **[resolved]** `fix` was restricted to `Set a` by the inferencer

The *converse* gap is closed: `fix` now requires a fixtype and a monotone
function, so a non-semilattice and an infinite eqtype are both rejected.
`L` is still unified with `Set a` rather than admitting tuples of
semilattices, which is what remains of this item.  The original text:

`infer.py:356-358` unifies `fix`'s semilattice with `Set a` because that is
"the only semilattice the generated helpers cover".  `spec/data.md` §I.5 types
`fix` at `fixL`, and `spec/types.md`/`syntax.md` do not restrict it.  Also the
converse gap: nothing rejects `fix` at a *non*-semilattice or a non-finite
eqtype, because those subgrammars are not implemented at all — see F38.


**Fixed.**  The `EFix` rule now takes a fresh metavariable and lets
`subgrammar.py` ask *which* semilattice once the substitution has settled —
pinning it in the inferencer answered that question too early.  `Int` and
`Int -> Int` are still refused, now with the fixtype message rather than a
type error.

Codegen needed the other half: `generate_all_helpers` emits a product
family — `bottom`/`join`/`eq`/`subset`/`diff`/`for`/`fix` at `L × M`, each
the componentwise lift, recursing into components that are themselves
products.

One ergonomic consequence, and it is Datafun's discipline rather than an
oversight: `fst`/`snd` take their argument at the ordinary arrow (`□A → B`),
so they cannot be applied to the *monotone* variable `fix` binds.  A
projection **is** monotone — a product is ordered componentwise — so the
prelude now supplies `fstM`/`sndM` at the arrow that says so, and

```
f (Box e) = fix r => (e \/ {x + 1 | x in fstM r, x < 3}, {x + 1 | x in fstM r})
```

converges with two genuinely different relations in one fixed point, which
is the Datalog idiom this item existed for.  `test/test_stage2.py`.

### F38. **[partly resolved]** No monotone/discrete discipline and no eqtype/semilattice/fixtype checks

`gestate/monotone.py` implements the one stripping rule the ϕ/δ transform
already depended on: `□`-introduction is checked in `⌈Γ⌉`, so a box may
not close over a monotone variable.  That turns what used to be an
unbound-change-variable crash in the lambda lifter into an error naming
the variable and pointing at `unbox`.

The discipline is now in: `A ~> B` is Datafun's monotone arrow and
`A -> B` is `□A → B`, so a binder's flavour comes from the arrow it was
checked against.  `fix` demands `□(L ~> L)`; the stripped positions are
`[e]`, a set literal, and the argument of a `->`.  See `errata.md` R14
for the one judgement the papers do not force (a binder is monotone only
where its type is known to carry a non-trivial order).

The four **type subgrammars** are in too — see `errata.md` D1.  Between
them, §II.1's soundness argument for the union is now mechanised: the
Rizzo formers are in none of the grammars, so `{someSignal}` is rejected
without a side condition.

Still missing from this item: `⌈Γ⌉` at `e = f` and `empty?`/`split`
(gestate has neither the Datafun equality nor those eliminators — see
D5/D6), and `fix` at a *tuple* of semilattices rather than only at a set
(F37).

The original text:

Datafun's typing rests on two variable flavours (`X : A` monotone, `x :: A`
discrete), context stripping `⌈Γ⌉` at every non-monotone expression, and four
type subgrammars.  Nothing in `gestate/` implemented any of it.  Consequences:

- `spec/data.md` §II.2's central claim — "every Rizzo-native construct is
  non-monotone … strip monotone variables from scope, same mechanism, same
  enforcement, zero new type-checker machinery" — has no mechanism to reuse.
  Nothing prevents closing over a monotone variable inside a signal body.
- `spec/data.md` §II.1's soundness argument — "a `Sig A` can never be compared
  with `=`, never used as a `fix`/`∨`/`⊥` target, never be a set element type"
  — is unenforced: `{someSignal}` and `someSig == someSig` are not rejected.
- `spec/data.md` §I.3's context transform (`ΦΓ`, `□ΦΓ, ∆ΦΓ`) has no typed input
  to work from, which is why `seminaive.py` guesses change-variable names by
  string-prefixing `"d"` (`seminaive.py:60`) rather than deriving them from the
  context.

This is the largest single gap between spec and implementation and it underlies
F1–F9.

### F39. **[resolved]** `FaL` / `ExL` type constructors do not exist

Fixed: `kindcheck.py` has `FaL`, `ExL`, `Maybe` and `Sync`, and every FRP
primitive is typed against them (`errata.md` R1).  `tail : Sig a -> ExL
(Sig a)` is writable and checked.

---

## 6. Pipeline and documentation drift

### F40. **[resolved]** `journal.md` Part I's flow diagram was stale

It had ϕ/δ *after* Datafun desugaring, which `spec/data.md` §0 forbids — ϕ/δ
works on `EFix`/`EFor` nodes and desugaring destroys them.  The diagram is
now rewritten against the real `pipeline.py`: it had also been missing the
exhaustiveness, monotone, subgrammar, helper-generation, change-structure
and ⊥-propagation stages entirely.  The three places where order is
load-bearing are stated under it, so the next drift is visible rather than
silent.

### F41. **[resolved]** A default `Set Int` is injected when the program mentions no set type

Fixed: the default is now reached only when the program *does* use a
Datafun form but no set type is visible in a signature — the residue of
`journal.md` Part I §17, which is where it belongs.  A program with
no Datafun form skips the whole block.

### F42. **[resolved]** `spec/data.md` §I.7's sharing requirement is not tested

§I.7: "codegen must actually share the compiled subexpressions (bind them once
via `ELet`, don't inline the `compileC e env` call twice), or you silently
regress to naïve evaluation while still calling it `semifix`."
`delta(EFor)` (`seminaive.py:276-283`) does bind `_pe`/`_de` via `ELet` as
required — but the spec's own suggested regression test ("duplicate-counting
instrumented `for`, Θ(n²) not Θ(n³)") does not exist, and per `errata.md` D3
it would fail anyway for want of ⊥-propagation.


**Tested — and §I.7's proposed test does not work.**  `test/test_sharing.py`
asserts the shape directly: δ of a `for` binds `ϕe` and `δe` once each and
the two loops use the bindings, checked by breaking the sharing on purpose
and confirming the tests fail.

§I.7 suggests measuring the query for Θ(n²) rather than Θ(n³) instead.  That
does not detect the defect.  With the sharing removed the step counts are
indistinguishable — 8055 against 8227 at n=4, identical 3.40/3.69 growth
ratios — because **a `for`'s source is almost always a variable**: `for (x ∈ r)`
over the fixpoint variable, `for (q ∈ e)` over a box-bound one.  Duplicating
a variable reference costs nothing, so the asymptotic penalty §I.7 warns
about arises only for `for (x ∈ <computed expression>)`, which no query in
either paper writes.

The asymptotic test is kept for what it does establish — the query is
quadratic — and labelled as that rather than as a guard on sharing.
`spec/data.md` §I.7's suggested test should be corrected to the structural
one.

### F43. **[resolved]** Bare variable patterns in `case` are rejected

`case x of y -> y` is unsupported because `CaseJump` has no default arm.
`spec/syntax.md` shows only constructor and literal alternatives, so this is
arguably spec-conformant — but `spec/types.md` §4's `checkPattern` is written
against arbitrary patterns, and `spec/data.md` §III.3's routing table has a
`_`-wildcard implied by fig. 2.2's desugarings.  Tracked as
`journal.md` Part I §3 (skipped).

---

## 7. Found while building the front end (2026-08-03)

### F50. **[resolved]** A class method inside a generic instance's *base* case misroutes

Reported as one bug; it was three, and the first two masked the third.

```
class C a where
    f : a -> a -> Bool

instance C Int where
    f x y = x == y          -- `<` here worked; `==` did not

instance (C a) => C (List a) where
    f xs ys = case xs of
        [] -> True
        x :: rest -> case ys of
            [] -> False
            z :: zs -> f x z

main : Int
main = case f [5] [1] of        -- 5 == 1 is False, so this is 0
    True -> 1
    False -> 0
```

- **F53 (nested `case`s shared subject names)** accounted for the whole
  reported symptom.  The original diagnosis — that the element call was
  routed to `__dict_C_Int__` instead of the dictionary parameter — was
  wrong; it was read off a compilation that F53 had already corrupted.

- **An instance whose context reproduces its goal ran to the depth cap.**
  Once F53 was fixed, `instance (Eq a) => Eq (List a)` diverged instead:
  `match_head` lets an unresolved metavariable match *any* head, so
  `Eq a` matched `Eq (List b)`, whose context `Eq b` was just as
  unresolved, and resolution re-entered the same instance forever.
  `solve_predicate` now carries the goals in progress and skips an
  instance whose context reproduces one, which lets the base case claim
  the goal.  The depth cap stays as the backstop for a context that
  *grows* (`C [a]` needing `C [[a]]`), where no predicate ever repeats.

- **A scheme's substitution reached its type but not its constraints.**
  Signature type variables were metavariables rather than skolems (F36, now
  closed), so a use site could bind one: calling `elem : (Eq a) => …` at `Bool`
  substitutes `a := Bool` in the scheme's *type* while leaving the
  constraint as `Eq a`.  Nothing could then bind that variable — it no
  longer occurs in the type — so the call site emitted a constraint that
  resolution could only default, and every constrained supercombinator was
  handed the `Int` dictionary at every other element type.  `_subst_scheme`
  now substitutes both halves.

**What this unblocks**: the prelude ships `Eq Bool`, `Ord Bool`,
`(Eq a) => Eq (List a)`, `(Eq a) => Eq (Maybe a)`, `(Eq a, Eq b) => Eq (a, b)`
and `elem`, all as ordinary compiled code, and they compose to any depth
(`[Just 1, Nothing] == …`, `([1], [2]) == …`).  F11 — set operations
comparing elements with the integer primitives — is now a matter of
routing the generated helpers through `Eq`, with nothing structural in the
way.  Tests: `test/test_eq_instances.py`.

### F51. **[resolved]** δ of a `let` never bound its change variable

`δ(let x = e in f)` emitted `let x = δe in δf` while the context promised
`dx` existed, so every `dx` in the body escaped to the lambda lifter.  It
is now `let x = ϕe ; dx = δe in δf`.  Nothing exercised it before because
no desugaring produced a `let` inside a Datafun-transformed body; tuple
patterns do.

### F52. **[resolved]** A block inside a `class`/`instance` body, or inside a `case` alternative, ended the enclosing block

`_parse_case` leaves its closing `DEDENT` for the caller — at the top level
the application-parsing loop needs to see it or `case … of …` swallows the
next declaration as an argument.  Inside a `class`/`instance` body that
same `DEDENT` read as the end of the *body*, and inside a `case`
alternative as the end of the *match*: every member or alternative after a
multi-line one silently moved out.  `Parser._close_inner_blocks` counts
what the member opened and consumes exactly those.

### F53. **[resolved]** Nested `case`s shared subject names

Each `case` builds its own `Matcher`, and the fresh-name counter was
per-matcher, so an inner `case`'s subjects shadowed the outer one's:
`case xs of x :: _ -> case ys of z :: _ -> x < z` compiled to `z < z`.
The supply is now shared and reset per program.

### F54. **[resolved]** Strings, `Char`, `Show`, and `deriving`

`VStr` reached the desugarer and died there; `String` was a primitive type
constructor with no values and no runtime.  Now:

- **`Char`** is a built-in type whose runtime representation is its code
  point, with built-in `Eq`/`Ord` instances (the integer primitives serve
  it unchanged) and `chr`/`ord` to move between it and `Int`.
- **`String` is an alias for `List Char`**, not a primitive.  That is the
  edit that pays: every list function, `Eq (List a)` and `Show (List a)`
  apply to strings with no second implementation, and the eqtype grammar
  inherits its answer from `Char`.
- **A string literal** is a spelled-out cons list of `EChr` nodes.
- **`show_result`** decodes a `String`-typed result, forcing the spine on a
  scratch machine the way the reactive driver re-enters the evaluator.
- **`Show`** is a prelude class with instances for `Int` (decimal, signed),
  `Char`, `Bool`, `List`, `Maybe` and pairs.
- **`deriving (Show, Eq)`** synthesizes instances as *surface* AST, so a
  derived method is compiled on the same path as a hand-written one and a
  parameterised type gets its field dictionaries for free.

`'` also became an identifier character — `x'`, `r'`, `f'`, which is how
`spec/syntax.md` and `spec/data.md` already write them.  Character
literals were dropped in favour of it; `chr` covers the gap.

**Not done**: `showsPrec`, so `show (Just (Just 3))` renders as
`Just Just 3`; and `show` on a `String` renders element-wise, because
`String` *is* `List Char` and coherence forbids an instance overlapping
`Show (List a)`.  `deriving Ord` needs a way to compare constructor
positions, which the surface language cannot name.

### F55. **[resolved]** Ambiguity was resolved one predicate at a time

An unresolved type variable matches every instance head, so a constraint
left on one picked whichever instance came first.  `Eq`/`Ord`/`Num` had a
per-predicate default to `Int` that hid this; `Show` did not, and
`show 42` — whose constraints are `(Num a, Show a)` — resolved `Show a`
against `Show Char` and rendered `42` as `'*'`.

Defaulting now happens once, in `infer_program`, as a *substitution* on
the variable rather than a rewrite of each predicate: a variable that no
supercombinator's type mentions and that carries a `Num`/`Eq`/`Ord`
constraint is bound to `Int`, and every constraint on it — plus the node
annotations and reported types — follows.  That is Haskell's rule.

**Still open**: a variable with no defaultable class in its constraint set
(`Show a` alone, say) still commits to the first matching instance instead
of being reported as ambiguous.

### F56. **[resolved]** A signature drifted when a use site bound its variables

`fixme.md` F36 says signature variables are metavariables rather than
skolems.  The consequence was worse than "a body that uses `a` concretely
is wrongly accepted": the environment update pushed the global
substitution through every scheme, so *one* use at a concrete type
monomorphised the definition for the whole program.  The prelude's own
`show` builds its output with `append`, which pinned
`append : List a -> List a -> List a` to `Char` and made
`append [1, 2] [3, 4]` fail with `No instance for Num Char`.

A declared signature is now held fixed: the environment update skips any
supercombinator the user gave a type, so each use site instantiates it
fresh.  This subsumes the constraint half of F50's third cause.  F36's
original complaint — that a signed *body* may still bind its own
signature's variables — was the other half, and is closed there: those
variables are now rigid.

### F57. **[resolved]** `δ(πᵢ e)` applied a projection to two arguments

Found while fixing F3/F4.  `δ(πᵢ e) = πᵢ δe` — the ϕ/δ table's
"distribute", and `spec/errata.md` D7 names it explicitly — but `delta`
had no case for a projection, so it fell through to the *application*
rule and built `πᵢ ϕe δe`.  `EProj` is not a function: the docstring says
it "must appear exactly as `EAp (EProj i) tup`", and the extra argument
is a term nothing downstream can compile.  Visible in the prelude's own
`fst_delta`, which read `π₀ p dp`.

Nothing caught it because it is unreachable in every query written so
far: δ of a projection only survives where it is not swallowed by a set
literal's or a `fix`'s ⊥.

One neighbour stays as it was.  `EProj` does double duty in this IR — it
also selects a method out of a dictionary — and a dictionary is a
compile-time constant whose change is `()`.  `π₀ ()` projects nothing, so
a discrete operand keeps the application path: δ of a *method* is the
derivative of a primitive, which is F3's open half and D8's contract.

### F58. **[resolved]** A `fix` inside an instance method compiled to `fix_Set_a0`

Found while resolving F9, which is why it matters: `__`-generated
supercombinators are the only ones the ϕ/δ transform still skips, so an
instance method is where the naïve `fix` loop would now be reached — and
it does not get there.

```
class Loop a where
  go : a -> Set (Cyclic 8)

instance Loop Int where
  go n = fix Box (r => {1} \/ r)
```

fails with `unknown global 'fix_Set_a0'`.  An instance method's body is
type-checked by `infer_instance_method`, which never runs `infer_program`'s
final pass — the one that pushes the finished substitution back through
`ESet`/`EFix`/`EFor`'s type annotations.  So the `EFix` reaches
`_desugar_datafun` still annotated with a metavariable, and the helper
name is derived from it.

Same family as F8 (an annotation that does not survive to codegen), and it
sits on `spec/errata.md` D9's boundary: helpers are generated per
monomorphic type, and a method body is exactly where a type may still be
open.

Fixed by giving both callers the same pass.  `infer_program`'s final loop
is now `infer.settle_annotations`, and `infer_instance_method` runs it too.

It was not only `fix`: the prelude's own `Guard Bool` has `False -> {}`,
a ⊥ at a set type, and it reached codegen as `bottom_Set_a1` — so **a
comprehension guard that was false under a `fix` crashed**, which no test
had exercised.  F64's link-time check is what surfaced it.

### F11. **[resolved]** Set element comparison is hard-coded to integers

`_gen_eq`/`_gen_union` compared elements with `prim_eq_int`/`prim_lt_int`
whatever the element type, so `{Bool}` and `{(A, B)}` were rejected by
`_check_comparable` — and a set of pairs is what a Datalog *relation* is,
so no relational query was expressible at all.

`helpers._gen_comparators` now emits `eqE_X`/`ltE_X` per element type,
generated **structurally** from the type rather than resolved through an
`Eq`/`Ord` dictionary: the helpers are emitted after elaboration, where no
dictionary is in scope, and they are already monomorphic per type
(`errata.md` D9's option (a)).  Covered: integer-represented types (`Int`,
`Char`, `Cyclic n`, `lo .. hi`), `Bool`, tuples of those (lexicographic),
and sets of those.  A user data type still has no generated order — that
wants `deriving Ord`.

Two things surfaced with it:

- **A set literal was not canonicalised.**  `{e₁, …, eₙ}` built a bare cons
  chain in source order, so `{(1,2), (0,1)}` produced an unsorted "set" and
  every operation on it — all merges — silently misbehaved.  A literal is
  now built with `union` over singletons, which establishes the invariant
  instead of trusting the author.
- **`Eq`/`Ord` at `Cyclic n`/`lo .. hi`** did not exist.  They are families,
  so their instances cannot be written out the way `Eq Int` is; they are
  synthesized on demand exactly as `Num (Cyclic n)` already was.

### D3/D4. **[implemented]** ⊥-propagation and change minimization

`gestate/bottoms.py` implements fig. 4.1's rewrites between ϕ/δ and Datafun
desugaring, while `EJoin`/`EFor` are still nodes; `seminaive` generates
`diff_L` and the loop is now
`dx_{i+1} = (f' xᵢ dxᵢ) \L x_{i+1}`.

Measured on this evaluator, counting G-machine steps:

- **⊥-propagation** takes ~28% off `reach` over `Cyclic n` (68,983 → 49,725
  at n=16), consistently across sizes.  On transitive closure it is worth
  ~2%: that query's derivative is not mostly zeros.
- **Change minimization** *costs* 10-12% on every program measured, and the
  cost shrinks monotonically with size (12.1% at 6 nodes → 9.8% at 12 on a
  loopy line graph) without crossing over.  The thesis's crossover (745s
  against 1.5s) is at 400 nodes; the largest graph this evaluator gets
  through in a reasonable step budget is 12, and `Cyclic n` caps the node
  count anyway.

So D4 is implemented to spec and its overhead behaves as the thesis
predicts, but **its benefit is not demonstrated here** — the scale that
shows it is out of reach until the evaluator is faster.  Recorded rather
than claimed.
\n
### F59. **[resolved]** A prefix operator only resolved only at the start of a phrase

`descend.py`'s `_resolve_phrase` strips prefix operators from the *front* of
an operator phrase and postfix operators from the *back*, then assumes what
remains alternates `Val op Val op Val`.  A prefix operator anywhere else
breaks that assumption, because the core then holds two adjacent operator
strings and precedence climbing reads the first as postfix and the second as
infix:

```
'a          ⇝  ('a)                     -- correct
'a ++ b     ⇝  (('a) ++ b)              -- correct
'a ++ 'b    ⇝  ((('a)++) ' b)           -- wrong
('a) ++ ('b) ⇝ (('a) ++ ('b))           -- correct, with parentheses
```

This is not hypothetical syntax: `'` is `music.md`'s unit-note constructor
and is already registered as a prefix operator at precedence 9
(`DEFAULT_PREFIX`).  **`music.md`'s own worked example does not parse as
`music.md` says it does** — it states

```
'1 ++ '2 ++ '3 |* 2 || '5 |* 6   ought be   (('1 ++ '2 ++ '3) |* 2) || ('5 |* 6)
```

and every `'` after the first is currently resolved as an infix operator.
Any music program is a sequence of notes, so this blocks essentially all of
stage 3 until it is fixed, and it is invisible today only because nothing
constructs a `Score`.

Two causes, both fixed.  The **parser** decided postfix-ness by lookahead —
any symbol followed by another symbol was postfix — so `++` before `'` was
taken as a postfix use; it now also requires the symbol to *be* a postfix
operator (`DEFAULT_POSTFIX`).  The **resolver** peeled prefix operators off
the front of a phrase and postfix off the back, so they worked only there; it
now recognises a prefix use wherever an operand is expected, inside the
precedence climb, and takes its operand at the prefix operator's own
precedence.  `a >| ++ b` — postfix before infix, the mirror case — works too.
`test/test_music_syntax.py`.

A user `postfix` declaration is still not visible to the parser, because
fixities are collected in a later pass; only the built-in postfix set is
consulted.  Nothing declares one today.

### F60. **[resolved]** A type with no constructors cannot be declared — `Void` is builtin

`Void :=` is a parse error ("expected constructor name").  Nothing needs an
uninhabited type today, which is why it has never come up, but `music.md`'s
`layout : [: Void :] -> …` does: `Void` is how a *performable* score — one
with no unassigned notes left — is said at rank 1, `forall b. [: b :]` being
rank 2 and out of reach.  `Void` is now a **builtin** type of kind `*` rather than something `:=`
can declare — the declaration syntax still requires at least one
constructor, and that stays true.  Nothing inhabits `Void`, which is the
point.

Note `errata.md` S4's original complaint was that `Score` was *declared* with
no constructors and so uninhabited.  That was a bug because `Score` needed
inhabitants; here uninhabitedness is exactly the point.

### F61. **[resolved]** `[: a :]` did not parse in a signature or a type alias

```
f : [: Int :] -> Int        -- ParseError: expected SEP ']', got SEP ':'
type Sc = [: Int :]         -- same
```

`_parse_type` is `_parse_op_phrase` — the **expression** grammar, converted
afterwards by `desugar_type`.  So the score-type branch in
`_parse_atomic_type` (`[` followed by `:` → `_parse_score_type`) is never
reached from a signature; expression space sees `[`, takes the list-literal
path, and fails on the `:`.  `_parse_atomic_type` is called only from
`_parse_instance_head`, so `instance C [: Int :]` parses and
`f : [: Int :]` does not.

The cause was not a missing branch but a *wrong* one: `_parse_list`'s `[:`
case read `[: a ]` and built a **List**, so the closing `:]` was a parse
error.  Nothing used that spelling — `syntax.md` gives `[a]` for lists — and
it now builds `Score a`, matching the copy in `_parse_atomic_type`.  Both
specs' `[: a :]` is writable, and `[: a :]` and `Score a` are the same type.

This was the sharp end of F27: `Score` did not merely lack a semantics, its
documented type syntax was unwritable.

### F62. **[resolved]** `[a]` was not a type

`syntax.md` documents `[a]` as the list type ("Lists are provided with
special syntax, type constructors: `[a]`"), and it is a `DeclError`:
`desugar_type` has no `VList` case, so `f : [Int] -> Int` fails with
"Unsupported type expression: VList".  `List a` works and is what the
prelude writes throughout, which is why this has never come up.

Found while fixing F61 — the two are the same defect in opposite
directions: `[: a :]` was documented and parsed as something else, `[a]` is
documented and parsed to something no later stage accepted.

Fixed with a `VList` case in `desugar_type`, plus one more that the first
did not cover: `_signature_tyvars` did not descend into a `VList` either,
because a list had never been a type, so the `a` in `f : [a] -> Int` was
not collected as a signature variable and became a nullary constructor the
kind checker then rejected.  `[a]` and `List a` are now the same type.

### F63. **[resolved]** `syntax.md`'s constrained-ADT example did not compile

It read

    ShowThis := (Show a) => ShowThis a

declaring `ShowThis` with no parameter while using `ShowThis a` as the
constructor's result — `KindError: Unknown type constructor: a`.  The
working form names the parameter on the left:

    ShowThis a := (Show a) => ShowThis a

Corrected in place.  Worth recording because the *broken* reading is the
interesting one: a type variable in a constructor's field that the ADT head
does not bind is an **existential**, which is exactly `typeclasses.md`
§7.3's `ShowBox` and exactly what F35 is missing.  The kind checker rejects
it uniformly today, with or without a constraint, so the error above is the
concrete blocker for that half of F35 rather than a separate gap.

### F64. **[resolved]** The monomorphization boundary was not enforced

A supercombinator whose *signature* is polymorphic in a set element type
compiles, and then fails at run time with an internal name:

```
f : {a} ~> {a}
f s = for (x in s) {x}          -- accepted
main = f {1} \/ f {2}           -- GmError: unknown global 'for_Set_a-43'
```

Helpers are generated per concrete set type (`errata.md` D9), so there is
nothing for `for` at `Set a` to call.  `_collect_set_types`' inner `add()`
drops any type with free variables — silently, which is where the boundary
is crossed without a word.  Without a signature the same body works, because
inference monomorphizes it at the use site.

This is the defect half of D9.  The *decision* — a monomorphic Datafun
sublanguage — is settled and needs no work; what is missing is the check
that says so at compile time.

The obvious fix is wrong: erroring in `add()` would reject the polymorphic
prelude, whose dead branches legitimately mention non-ground set types
(`changes.py` says so).  Fixed instead with a **link-time check**
(`pipeline._check_helpers_exist`): after helpers are generated, every
helper name the transformed supercombinators *refer to* must exist.
Checking references rather than types is what makes it precise — a
non-ground type nothing reaches stays harmless — and nothing is guessed
from a name.  The message names the supercombinator the user wrote (not
its `_phi` rename) and the type without its internal variable id.

**Turning it on found a live crash**, which is the argument for having it:
`__Guard_Bool_guard__`'s `False -> {}` branch is ⊥ at a set type left
unsettled, so a comprehension guard that was *false under a `fix`* died on
`bottom_Set_a1`.  Every guard test passed because none had ever taken that
branch under a fixpoint.  That is F58, below, and fixing it was the
prerequisite for this check being green.  `test/test_monomorphization.py`.

### F65. **[resolved]** An operator could not be given a top-level definition

`++` has a default fixity (`infixl 4`, "list append / music sequence" in
`syntax.md`) and no definition anywhere, so using it is an error:

```
main = "ab" ++ "cd"        -- InferError: Unknown global '++'
```

and it cannot be supplied, because an operator name does not parse as a
declaration head:

```
(++) : List a -> List a -> List a
(++) xs ys = append xs ys  -- ParseError: expected declaration, got '('
```

Operator names *do* work as class and instance members — the prelude
writes `(==) a b = …` inside `instance Eq Bool` — and `syntax.md` says any
operator "may be parenthesized into a value".  Only the top-level
definition form is missing, so every operator in the language today is
either a class method or built into the compiler.

The list functions this would name exist already (`append`), so the gap was
the binding, not the behaviour.  Same class as F61/F62: documented syntax
that did not work.

Fixed in `_parse_top_item`: a parenthesized operator name is now a
declaration head, for a signature and for one or more equations, so
`(+++) [] ys = …` / `(+++) (x :: xs) ys = …` groups like any multi-clause
definition.  `++` is bound to `append` in the prelude.
`test/test_music_syntax.py`.

This was a **blocker for stage 3**: `++`, `||`, `|*` and `|/` have
fixities and need bodies, and there was no form in which to write one.
Note for when those bodies land — `syntax.md` gives `++` as "list append /
music sequence", so a `Score` sequence wants the same operator at another
type, which will make it a class method.  Nothing needs it to be one yet.

### F66. **[resolved]** A deeply nested application crashes with `RecursionError`

A program with a long left-nested application spine — around 180 `append`s —
died as a Python `RecursionError` during compilation rather than as anything
a user could act on.  Found while writing F29's property tests, which build
probe programs by folding `append` over a list.

This entry used to say "there is no evidence a real program reaches it".
There is: **a melody is one `++` chain**, so a piece of music hit the ceiling
at about 170 notes.  The whole music half of the language was capped below
anything worth listening to, and the cap announced itself as an interpreter
crash.

Measured at six Python frames per level of source nesting, which is what put
CPython's default limit of 1000 at ~165 applications.  Every stage that walks
an expression is recursive (`infer`, `phi`/`delta`, `lift`, `compileC`), so
rewriting them iteratively would touch the six stages most likely to be
wrong for a bound that is not really about any of them.

`pipeline.compile` instead runs on a thread with a 256 MB stack and a raised
recursion limit — ~8,000 levels of nesting.  The limit stays *finite* so that
genuine runaway recursion is still reported rather than segfaulting, and a
`RecursionError` from inside is translated into a `PipelineError` that says
what to do.  `test/test_deep.py`.

### F67. **[missing]** Nothing enforces the "no variable starting with `d`" rule

The thesis's footnote 9 (p. 58) assumes source programs contain no variable
whose name starts with `d`, because ϕ/δ mints the change variable `dx` from
`x`.  Gestate mints names exactly that way and enforces nothing.

**The hazard is unproven.**  A program written to collide — a box-bound
`dx` referenced inside `for (x ∈ …)`, whose ϕ body is wrapped in a
generated binding of the same name — produces the right answer anyway.  So
this is recorded as an unenforced *assumption*, not as a known-live bug; a
check would either have to be shown necessary first, or the generated names
moved out of the user's namespace the way `fixme.md` F59's `_guardN#` and
the match compiler's `_mN#` already are.  That last is probably the right
fix if it ever matters: it is the same problem those solved, one pass over.

### F68. **[resolved]** `empty?` hardcoded the cons-list tags

Introduced with `empty?` itself and found by 2.3's tests.  The primitive's
G-machine code case-jumped on tags **0 and 1** for `Nil`/`Cons`, but user
constructors are numbered first, so a program declaring three of them
pushes `Nil`/`Cons` to 3/4.

Every comprehension guard goes through `holds`, and `holds` through
`empty?`, so **any program containing both a data declaration and a guard**
died as `CaseJump: no alt for tag 4`.  Nothing caught it because every
guard test until now declared no data type, leaving the tags at 0 and 1.

`add_primitives` takes the two tags now, as it already took `True`/`False`.
The lesson is the one `fixme.md` F9 recorded for a different guess: a tag
is not a constant, and anything that assumes one is wrong in exactly the
programs that also declare data.

### F69. **[resolved]** An instance method could not take a constructor pattern

```
P := P Int Bool

instance G P where
    get (P x y) = x      -- GmError: unknown global 'x'
```

The same equation as a plain supercombinator works, and the same instance
with a `case` body works; only the *method with a pattern parameter* fails.

`elaborate.py` builds a method's frame with
`[p.name for p in eq.params if hasattr(p, 'name')]`.  A `PCon` has a
`.name` too — the *constructor's* — so `P x y` contributes the parameter
name `"P"`, and `x`/`y` are never bound at all.  A `PTuple` has no `.name`
and is silently dropped instead, losing the parameter.

Instance method bodies did not go through the match compiler the way SC
equations do (`_desugar_pattern_sc`); they do now.  A `PVar` keeps its own
name and anything else gets a fresh one, with the patterns compiled against
those.  Found while checking whether `syntax.md`'s `AttrN` design for record
projection is implementable — it is, but its generated instances would have
hit this immediately.

### F70. **[resolved]** A trailing comment broke an indented continuation

```
T := A   # hi
   | B Int          -- ParseError: expected declaration, got INDENT
```

The same declaration parses with the comment removed, and parses with the
comment but no continuation.  A comment ends the line, the indented
continuation then emits an `INDENT`, and the data-declaration parser has no
case for one — so **a comment decides whether a program parses**, which is
the property a comment must never have.

Found while writing the music prelude.  Fixed: the constructor-list loop
skips `_skip_trivia` — newlines *and* comments — rather than newlines
alone.  A comment is an item at the top level, where the formatter keeps
it; inside a declaration it is only trivia, and treating it as a terminator
is what let it change the program.

### F71. **[resolved]** A lambda could not take a pattern

`(a, b) => a` parses and then fails: `Pattern matching in lambda not
supported yet: PTuple`.  A supercombinator equation with the same pattern
works, and so does `case`, so the machinery exists — `desugar` routes SC
equations through the match compiler and lambdas not at all.

Hit while writing `music.ges`'s event helpers, which want
`map ((a, b, x) => …)` — and which now do.  A pattern parameter binds a
fresh name and matches it, the same shape as a `for` clause's pattern, and
the same restriction applies for the same reason: **irrefutable only**,
because there is nowhere for a failed match in a lambda to go.  The message
names `case` as what to use instead.

### F72. **[resolved]** A single-line `case` inside parentheses did not parse

```
f = (case x of (a, b) -> a)          -- ParseError: expected pattern, got ')'
f = map (e => case e of (a, b) -> a) xs
```

The alternative list kept consuming past the closing bracket, so the `)`
was read as the start of another pattern.  F45 fixed the *multi-line* case
of this — a `case` block inside brackets, where the tokenizer now emits the
block's `DEDENT` before the closer — and the single-line form has no block
to close, so it never reached that machinery.  Same defect, other half.

Fixed: the alternative loop ends at a closing bracket or a comma as well as
at a `DEDENT`.  `test/test_layout.py`, beside F45's tests.

### F73. **[resolved]** `python -m gestate.typecheck --check` never worked

Two defects, one hiding the other, both found by running the CLI over the
new `examples/`.

`_find_errors` called `check_scs`, which does not exist, so **every** path
reaching it died with a `NameError` rather than reporting anything.  With
that fixed it reported `No instance for Eq a` on every program, including
`main = 1`: it solved *all* the constraints inference produced, where
`pipeline.compile` first drops those an SC's own declared context grants —
so the prelude's `elem : (Eq a) => …` looked like a missing instance.

The CLI and the pipeline now agree, which is the property that matters: a
second checker that disagrees with the compiler is worse than none.

### F74. **[resolved]** The implicits mechanism was unusable, in three ways

`spec/syntax.md` described `given`/`using` and the parser accepted both,
but nothing joined them up.  Found by writing the manual entry for the
feature, which is a recurring shape in this project: **writing real programs
finds what tests do not**.

*Propagation was absent.*  `(using n)` gave the definition an extra
parameter, and a caller of that definition got nothing, so anything but a
direct call under a `given` was broken.  A least fixed point over the call
graph now computes, per supercombinator, the implicits its body names plus
those of everything it calls (`desugar._implicit_needs`).

*The requirement analysis ignored binders.*  `_needs_of` read every `VWord`
as a global reference, so the prelude's `flip f x y = f y x` acquired an
implicit merely because a user program defined a supercombinator called
`f` — a silent miscompile of the prelude, triggered by an unrelated file.
Every binder form is now enumerated, mirroring `syntax/rename.py`, which
walks the same binders for the same reason.  Separately, `VAlt` is not a
`Val`, so the generic dataclass walk reached a `case`'s scrutinee and none
of its alternatives; an implicit used inside a branch was never seen.

*The signature had to carry it.*  With implicits as leading parameters,
`f (using n) = n` typed as `Int -> Int`, and so did every caller up the
chain — restating at each level exactly what propagation had just derived,
and making a `(using …)` added deep in a library break every signature
above it.  `implicit n : τ` now declares the name's type once at the top
level; signatures stay silent, and `desugar_program` extends the checked
type from the declaration.  The alternative — a context,
`f : (n Int) => Int` — was considered and rejected for that restatement.

Two errors are now possible and both are compile-time: a `(using n)` with
no `implicit n : τ`, and an implicit reaching `main` unfilled.  A program
that leaves one unfilled cannot be constructed, which was the requirement.

`test/test_implicits.py` (19 tests) and `doc/manual.md` §4.

### F75. **[resolved]** Inference was superlinear: `Subst` was an association list

Found by measuring, after asking whether the Python *evaluator* was the
bottleneck.  It was not, by a wide margin — for a 256-note score, compiling
took 7.9s against 0.67s to evaluate, and compilation grew about ×5 per
doubling of the score.

`Subst` stored its bindings as a tuple of pairs:

```python
_map: tuple[tuple[int, Type], ...] = ()

def lookup(self, var_id):
    for k, v in self._map: ...              # linear scan
def extend(self, var_id, t):
    return Subst(((var_id, t),) + self._map)
def compose(self, other):
    s = other
    for k, v in self._map:                  # O(|self| × |other|)
        s = s.extend(k, other.apply(v))
```

`lookup` ran in the innermost loop of inference and cost the *size of the
substitution* — and that size grew with the program too.  A 128-note program
made 271,446 lookups against a substitution averaging 84 entries and peaking
at 1,275; both factors growing is what produced the exponent.

Three changes, all inside `gestate/types.py`:

* `_map` is a `dict`, still never mutated after construction, so the
  persistent interface and the functional threading in `infer.py` are
  unchanged.  `lookup` is O(1).
* `compose` builds one dict in a single pass — the sum of the two sizes
  rather than the product.
* `apply` returns its argument unchanged when no part of it changed, instead
  of allocating an equal copy.  Most types a substitution meets mention none
  of its variables, and `compose` applies one substitution across the whole
  of another, so the no-op is the common case.

| notes | before | after | |
|---|---|---|---|
| 64 | 0.54s | 0.29s | 1.9× |
| 128 | 1.62s | 0.53s | 3.1× |
| 256 | 7.93s | 1.26s | 6.3× |
| 512 | 49.8s | 4.04s | 12.3× |

Growth per doubling fell from ~6× to ~3.2× (about O(n²·⁶) to O(n¹·⁷)), and
the suite went from 75s to 59s.  What remains is `extend` copying the dict
and inference re-applying the substitution across the environment — the
textbook fix for both is a mutable union-find, which would restructure
`infer.py` rather than one class.  Not done: nothing needs it yet.

`test/test_deep.py` pins the semantics that had to survive the change of
representation, including the shadowing rule and the identity property
`apply` now relies on.

### F76. **[resolved]** Laying out a score was quadratic in its length

The last of the three slopes found by measuring where time actually went.
With F66 and F75 out of the way, evaluation was what remained, and it grew
about ×3.9 per doubling of the note count — quadratic.

`lay` was written the direct way:

```
    Seq a b -> case lay a of
        (da, ea) -> case lay b of
            (db, eb) -> (da + db, append ea (shiftEvents da eb))
```

A melody is one long `Seq` chain, so `append ea …` copied every event
gathered so far at every level.  Nesting the chain the other way does not
help — it only moves the cost from `append` to `shiftEvents`.

`layOnto` replaces it.  It carries the offset *down* rather than shifting
events up, and prepends onto an accumulator rather than appending, so each
event is touched once.  Prepending reverses, which `lay` undoes once at the
end instead of n times on the way.

`Scale` and `Shrink` are the exception and stay as they were: an event at
local `x` inside `Scale t k` belongs at `off + x*k`, which is not
`(off + x)*k`, so an offset cannot be folded through them.  They lay their
subtree at the origin and transform its events — the one remaining pass, and
no worse than before.

`shiftEvents` has no callers left and is gone.

| notes | before | after | |
|---|---|---|---|
| 64 | 0.049s | 0.016s | 3.1× |
| 128 | 0.171s | 0.036s | 4.7× |
| 256 | 0.670s | 0.069s | 9.8× |

Growth per doubling fell from ~3.9× to ~2.2×.  1,024 notes now lay out in
0.41s; before, 512 was as far as anything got.

**`reverse` was quadratic too** — `append (reverse rest) (single x)`, in the
core prelude, for the one list function nobody expects to be expensive.
`lay` calls it once per layout, so leaving it would have undone the fix.  It
accumulates now, via `reverseOnto`.

`test/test_music_layout.py` checks the rewrite against a reference
implementation of the *original* semantics over randomly shaped scores —
verified to fail on the specific mistake the design avoids (folding the
offset through `Scale`).  The committed `.mid` files are unchanged, byte for
byte.

### F77. **[resolved]** A comment inside a `case` block ended the block

```
    Seq a b -> ...
    # a comment about the next alternative
    Over a b -> ...          -- ParseError: expected pattern, got COMMENT
```

The alternative loop skipped newlines but not comments, so a comment between
two alternatives was handed to the pattern parser.  F70 added `_skip_trivia`
for exactly this reading — inside a declaration a comment is trivia, and
treating it as a terminator lets it change what a program means — but the
`case` loop was not switched over to it.

Found while writing F76's rewrite, which wanted a comment on the `Seq` case
explaining why the two sides are laid in order.  A comment at the *outer*
indentation still ends the block, because the tokenizer emits the `DEDENT`
before it.

### F78. **[resolved]** Inference threaded a persistent substitution

F75 made `Subst` a dict and took compiling a 512-note melody from 50s to
4.0s, but the growth was still ~1.6× per doubling above linear.  Two costs
remained, and neither was `lookup`:

* `extend` copied the whole dict, so binding the k-th variable cost k.
* Threading forced the environment and the constraint list to be *rebuilt*
  every time the substitution grew (`_apply_subst_env`,
  `_apply_subst_constraints`), because a scheme handed out earlier holds
  types the newest binding refines.  These ran after almost every step.

Both are consequences of there being more than one substitution.  The
standard answer is the union-find formulation: one mutable store, bindings
written in place, composition a no-op, and nothing to rebuild because every
type resolves through the store whenever it is next read.

**The change is smaller than that description suggests.**  The functional
threading in `infer.py` is left exactly as it was; it simply becomes free.
`_SubstBase` holds what both kinds of substitution can do, `Subst` stays
persistent for `constraint.py` and the ADT instantiation, and a new
`Unifier` is destructive.  Inside `unifying()` — installed at the two
inference entry points — `Subst.empty()` hands back that one store, so
every substitution `infer.py` builds and composes *is* the same object.

Sound because **inference never backtracks**: there is no `except
UnifyError` in `infer.py`, no speculative branch, and no substitution built
and then discarded.  Every one is composed forward, so aliasing them
reaches the same fixed point.  `unify` gains a genuine occurs check as a
side effect — it used to run against only its own local substitution.

`Unifier` also compresses paths, which a persistent structure cannot: after
following `α ↦ β ↦ γ ↦ Int` once, all three point straight at `Int`.  On a
1,024-note score `_apply_var` had been walking about twenty links per call.
A two-variable cycle is left uncompressed — rewriting it would make a
variable point at itself and `apply` would not terminate.

Compiling one melody as a single `++` chain:

| notes | at session start | after F75 | after F78 | |
|---|---|---|---|---|
| 64 | 0.54s | 0.29s | 0.148s | 3.7× |
| 128 | 1.62s | 0.53s | 0.197s | 8.2× |
| 256 | 7.93s | 1.26s | 0.230s | 34× |
| 512 | 49.8s | 4.04s | 0.371s | **134×** |
| 1024 | *crashed* | — | 0.679s | |
| 2048 | *crashed* | — | 1.313s | |

Growth per doubling is now ~1.5–1.9×, i.e. linear; it began the session at
~6×.  End to end, a 4,096-note score renders to MIDI in 6.6s, and the suite
went from 75s to 53s.

`test/test_deep.py` pins the properties soundness rests on: that `Subst` is
still persistent for everyone outside inference, that the scope nests and
restores, that a separate `Subst` is absorbed rather than ignored, that
compression flattens a chain and leaves a cycle alone, and that a signature
variable is still rigid.

### F79. **[resolved]** The evaluator's inner loop did work that was not evaluation

The last of the four bottlenecks found by measuring.  Unlike the other
three this one is a constant factor, not a slope — but it was the largest
remaining term for anything compute-heavy.

*Per-instruction allocation.*  `step` advanced with
`instr, s.code = s.code[0], s.code[1:]`, building a fresh list for every
instruction executed — 1.5M of them for `fib 20`.  A program counter
replaces it.  `code` stays a property, so the fifteen sites that *assign* a
code sequence are unchanged; only `step` and `run` touch the counter.

*Per-instruction call overhead.*  `run` called `step`, and consulted
`isFinal` — a property — once per instruction to ask a question the loop
already had the answer to.  Between them a third of the machine's time.
`step`'s body is written out in `run`; `step` remains for the reactive
driver and for single-stepping.

*The spine walk.*  `Unwind` on an `NAp` pushed one link, set the code to
`[Unwind]`, and returned to the dispatch loop to do it again.  **A third of
all instructions executed were this** — 507,000 of `fib 19`'s 1,461,000 —
and every one did the same two things.  `_unwind` now follows the whole
spine, indirections included, in one instruction.  The subtlety is what it
leaves behind: the code the one-at-a-time version ends on is the `[Unwind]`
it just consumed, so an unwind that *moved* must end with the code
exhausted.  `test/test_gmachine_loop.py` runs the fused version against the
rule as originally stated.

*Node dispatch.*  `_unwind` tested five node kinds with one `isinstance`
against a tuple before reaching `NAp`, which is the common case.  Every node
class is a leaf, so `type(x) is C` decides it; `NAp` is tested first and the
WHNF kinds became a frozenset.  `[Unwind()]` and `list(node.code)` are no
longer rebuilt on each use — a code list is only ever rebound, never mutated.

`fib 22`: **7.12s → 4.84s (1.5×)**, and instructions executed fell from
6,189,763 to 4,814,262.

**What was not done, and why.**  The stack is stored top-at-index-0, so
every push is `insert(0, …)`.  Reversing it would touch some forty sites.
The profile says it is 3.7% of the time — stacks are shallow, averaging
under three entries — so the refactor would have bought almost nothing.
Worth recording as a measurement rather than a hunch: it was my first guess.

What remains is the dispatch loop itself, about 40% of the machine's time
and close to the floor for a bytecode interpreter written in Python.  Going
further means either fewer instructions (a compiler change) or a different
host — and on the workload this language is for, evaluation is no longer
what dominates.

### F80. **[resolved]** `|*` swallowed the rest of the piece into its factor

`a ++ b |* 2 ++ c` parsed as `(a ++ b) |* (2 ++ c)`.  Writing
`examples/music/nocturne.ges` ran into it on the first phrase that scaled a
group and then continued — which is most of them.  It surfaces as a type
mismatch about `Int` several definitions away from the cause.

The operator's two operands are not the same kind of thing: a score on the
left, a number on the right.  On the left it wants to be **loose**, taking a
whole phrase, which is what `music.md`'s worked example asks for.  On the
right it wants to be **tight**, taking a factor and stopping.  One
precedence cannot be both.

The resolver is precedence climbing, where one number does two jobs: it
decides whether an operator may take what is to its left, and it seeds the
minimum for what it takes to the right.  Splitting them is a few lines, and
`RIGHT_PREC` gives `|*` and `|/` a right precedence of 6 — the highest that
still leaves arithmetic alone, so `a |* 2 + 1` scales by three while `::`
(5) and `++` (4) stay outside.

The declaration syntax exposes it, `infixl 3 6 |*`, rather than keeping it
a private table: an operator whose operands differ in kind is a thing users
of a music language will write, and a built-in using a mechanism the surface
cannot reach is its own trap.  `prefix` and `postfix` reject a second
precedence — they have one operand.

**Still open, and a design question rather than a bug.**  The *left* side is
unchanged, so `a |/ 2 ++ b |/ 2` is `((a |/ 2) ++ b) |/ 2` — the second `|/`
takes everything before it.  Left-looseness is what `music.md` asks for and
what makes `'1 ++ '2 ++ '3 |* 2` scale the whole sequence; the cost is that
two scaled groups in a row need parentheses.  Every use in `nocturne.ges`
parenthesises its left operand anyway, which is evidence the looseness earns
less than it costs — but changing it contradicts the spec's own example, so
it is the author's call.

### F81. **[resolved]** A prefix operator could not stand as an argument

`four '38` read as `four ' 38` — `'` infix — so every note passed to a
function needed parentheses.  Recorded in `doc/manual.md` §9 as something to
work around; found again writing `nocturne.ges`.

`'` and `|<` are declared prefix and are never infix, so a symbol from that
set standing where an argument may stand cannot be an infix operator.  The
application parser now takes it together with the atom after it as one
argument.  The operand is an *atom*, so `f 'x ++ 'y` still sequences: the
`++` belongs to the phrase around the application, not to the argument.

`at 4 '60` needs no parentheses now, which retires the §9 entry — the
manual's own test failed when the limitation was fixed, which is what that
file is for.

### F82. **[resolved]** A definition body could not be broken across lines

Not across lines, not inside brackets, not after the `=` — a body had to
fit on one line or not parse.  For a language whose expressions are long
chains of notes that is a standing cost; `nocturne.ges` worked around it by
naming every bar, which is defensible style but should not have been forced.

An indented line was *always* a layout block, so the tokenizer emitted
`INDENT` and the parser, in the middle of an expression, had nowhere to put
it.  The general fix is Haskell's full layout rule, where a block opens at
the column of its first item wherever that falls; that needs the
parse-error rule to close a block on `in`, and would rework the one part of
the tokenizer every other construct depends on.

Two shapes are unambiguous and only those are taken:

* **the line begins with an operator** — nothing that starts a declaration,
  a binding or a case alternative does;
* **the previous line ends with `=`** — only a body can follow.

Both suppress the newline and open no block, so the tokens flow on as one
logical line.  Everything else opens a block exactly as before, which is
what keeps `let x = 5` with its later bindings indented beneath it working:
`y = 6` could begin an item, so it still does.  A baseline of nine existing
layout forms was taken before the change and all nine still behave.

Not covered: a bare operand on its own line (`f 1` then an indented `2`).
It reads as a new item and there is no way to tell it from one.

`test/test_layout.py`, beside F45's tests.  `nocturne.ges` is written a bar
to a line now, and its rendered `.mid` is unchanged byte for byte.

### F83. **[resolved]** Duration scaling bound looser than sequencing

F80 gave `|*` and `|/` two precedences — loose on the left, tight on the
right — to stop the scaling factor swallowing the rest of a phrase.  That
fixed the reported bug and left the left-hand half of it: `a |/ 2 ++ b |/ 2`
still read as `((a |/ 2) ++ b) |/ 2`, because a loose left side takes
everything before it.

Two scaled groups in a row is *a bar of eighth notes*.  It is the common
shape, not an edge case, and it failed silently — as a type error about
`Int`, some definitions from the cause.

`|*` and `|/` are `infixl 6` now, tighter than `++` (4).  Scaling applies to
the group beside it; a phrase to be scaled is parenthesised, which is what
every use in `examples/music/` already did.  `music.md`'s worked example is
updated with the reasoning, since it had asserted the other grouping.

The asymmetry turns out not to be needed at 6: left-associativity there
gives the right operand a floor of 7, which still takes `+` (7) and `*` (8)
— so `a |* 2 + 1` scales by three — and stops before `::` (5) and `++` (4).
`RIGHT_PREC` is therefore empty and no built-in operator uses two
precedences.  The mechanism and the `infixl 3 6 <@` declaration form are
kept: an operator whose operands differ in kind is a thing a user of a music
language will write, and it costs fifteen lines.  It should be removed if
that stops being true.

### F84. **[resolved]** There was no `Float`

`desugar.py` had a line reading `raise DesugarError("Float literals not
supported yet")`, and the manual said the language had "no floating point in
the parts that matter".  Audio synthesis needs it outright, and GUI physics
wants it; the music backend's tick arithmetic (96 to the beat, chosen so
every subdivision is exact) is a small monument to not having it.

Less work than it looks, because `Num` was already a real class with builtin
`InstanceInfo`s per type — that is how `Cyclic n` works — and `NNum` holds a
plain Python number, so `AddInt`/`SubInt`/`MulInt`/`EqInt`/`LtInt` were
already float-correct. Only division differs (floor versus true), and the
two coercions are new.

**A literal's form is its type.**  `1.5` is a `Float`, `1` is an `Int`.  No
`Fractional` class, no defaulting — which was the point, and matches the
standing objection to F32.  They still mix without coercion, because an
integer literal carries `Num a` and `Num Float` discharges it: `x * 2 + 1.5`
type-checks at `Float` by *deriving* the answer rather than guessing it.
`fromInteger` at `Float` genuinely converts, so `main : Float ; main = 3`
prints `3.0` and not `3`.

* `Float` is a builtin type of kind `*`.
* `DivFloat`, `ToFloat` and `FloorFloat` instructions; a `_prim_unop_code`
  beside the existing binary one.  The other `prim_*_float` globals share
  the integer instructions — Python's operators are correct on either kind
  of number — and exist so generated code says which type it meant.
* `Num Float`, `Eq Float`, `Ord Float`, `Show Float`.
* `/` at `Float` only.  Integer division stays the explicit
  `prim_div_int`; an overloaded `/` that silently floored at `Int` is the
  classic footgun.  `toFloat`, `floor`, `negateFloat`, `absFloat`.
* **Subgrammars: exactly `Int`'s standing.**  An eqtype, so `{Float}` builds
  and `_INT_LIKE` generates its comparators; *not* a finite one, so
  `fix` over `{Float}` is refused with the same message `{Int}` gets.

`show` truncates to three places rather than rounding — rounding needs a
carry into the integer part and nothing needs it yet.  It peels the sign
first, because `floor (0.0 - 2.75)` is -3 and taking the fraction from there
would print `-3.250`.

Not done, deliberately: transcendental functions.  They come with audio,
when it is known which are wanted.  *(They came: `sin`, `cos`, `exp`,
`log` and `sqrt` are primitives, with `tan` and `pow` written in the
language on top of them — `spec/liveaudio.md` open question 2 for why
that split, and `test/test_transcendental.py` for the measurement that
lets the bit-identical comparison survive them.)*

`test/test_float.py`.  Writing the prelude's `showFloat` also ran straight
into F82's limit — a continuation line may not begin with `(` — which is
worth recording as a second sighting.

### F85. **[resolved]** The FRP half had no driver anything could watch

`reactive.py` could step a signal and the tests could read numbers out of
one, but nothing put it on a screen, so the whole reactive half was
exercised only by unit tests.  Every time this session a *real program* was
written against a part of the language, it found something — so a backend
was overdue.

Built to the same plan as the MIDI one, which is the pattern that already
works here:

| | music | GUI |
|---|---|---|
| prelude, prepended | `music.ges` | `gui.ges` |
| program supplies | `score`, `bpm` | `scene : Sig Scene` |
| pure core | `perform` | `scenes(src, events)` |
| needs a library | `write` (mido) | `run` (pygame) |

`scenes` opens no window and imports no pygame, so `test/test_gui.py` costs
nothing and runs anywhere.

**One event channel, not one per input kind.**  Channel identifiers are
handed out in allocation order, so several channels would be positional and
fragile; one `Chan Event` is also the honest reading of what a GUI receives.

**`scan` is what makes a GUI writable**, and it is ordinary guarded
recursion — the recursive call under a `delay`, so the signal is productive
by construction.  `world step init draw` folds it with `mapSig` and a whole
application becomes three definitions.

Measured: 0.77 ms per frame for `examples/gui/bounce.ges`, against a 16.7 ms
budget at 60 Hz.  About 1,300 frames a second of headroom, which settles the
earlier question — **the GUI half needs no change of host language.**

Three things writing it shook loose, none of them in the backend:

* `Box` is a reserved word, so a `Shape` constructor could not be called
  that.  Renamed `Rect`.  The error — "expected constructor name" — points
  at the right line but does not say that the name is reserved.
* `mkSig` is `ExL a -> ExL (Sig a)`, not `ExL (Sig a) -> Sig a`.  The
  manual's §6 example is right; the signature is easy to get backwards.
* F82's continuation rule again: a line beginning with `(` is not a
  continuation, which the prelude's `showFloat` had already run into.

### F86. **[resolved]** A continuation line could not begin with `(`

F82 let a definition body span lines when the next one starts with an
operator or the previous one ends with `=`.  Breaking a long *application*
was still impossible, and that is the commonest reason to want it —

```
showFloat x = append (showNat (floor x))
                     (append "." (digits x))
```

which the prelude's own `showFloat` wanted, and then `gui.ges` wanted, both
within an hour of F82 landing.  Two sightings in a day is the argument.

`(` is now a continuation opener, **except directly after a block opener**
(`of`, `where`, `let`, `letrec`, `given`).  That exception is the whole
difficulty: a case alternative may be `(a, b) -> …` and a class member may
be `(==) : …`, and a deeper line starting with `(` is indistinguishable from
a continuation *unless* you know a block was just opened.  The guard applies
to the older triggers too, where it was harmlessly implicit.

A baseline of thirteen existing layout forms was taken first — including the
two the naive rule would have broken, which is how the guard was found
rather than guessed.  All thirteen still behave, and `showFloat` is written
the way it wanted to be.

`test/test_layout.py`.

### F87. **[resolved]** "expected constructor name" did not say why

`Shape := Box Int …` was rejected with "expected constructor name", which is
true and unhelpful: `Box` is a *reserved word* — it is the box type, term
and pattern constructor — and the message never said so.  Found writing
`gui.ges`, where `Box` is the obvious name for a rectangle.

Now: ``\`Box\` is a reserved word, so it cannot name a constructor — pick
another name``, and a non-word gets ``expected a constructor name, got '3'``
rather than the same sentence for both.  Same family as F30: an error the
reader cannot act on.

### F88. **[resolved]** There was no way to hear a signal

The FRP half could be watched (F85) but not heard, and synthesis is the
application that most needs `Sig Float` to be a good idea.  A third backend
on the same plan as the other two:

| | music | GUI | audio |
|---|---|---|---|
| prelude | `music.ges` | `gui.ges` | `audio.ges` |
| supplies | `score`, `bpm` | `scene : Sig Scene` | `sound : Sig Float` |
| pure core | `perform` | `scenes` | `render` |
| writes | `.mid` (mido) | a window (pygame) | `.wav` (stdlib `wave`) |

**Offline, by design.**  Stepping a gestate signal once per sample runs at a
few thousand instants a second against the 44,100 real time needs — and a
faster interpreter would not close it, because audio DSP wants flat buffers
and no allocation, which graph reduction is not.  SuperCollider's split is
the right one: the language *describes* the instrument, an engine runs it.
Rendering to a file is the half that needs no engine, and it answers the
question that decides whether the rest is worth building.

**The sample rate is the renderer's, not the program's.**  `audio.py`
appends `sampleRate` as a definition, the way it appends `main`, so the same
synth renders at any rate and the rate stays a property of the file.

`examples/audio/blip.ges` is an oscillator, an envelope and a one-pole
filter, each a `scan`.  The phase is *accumulated* rather than computed from
the sample number: `wrap (p + f/rate)` stays continuous across a note change
where `n*f/rate` would jump and click — and there is a test for exactly that,
measured as the largest step between neighbouring samples.

One thing the design cannot do yet: **`mapSig` cannot pair two signals**, so
two oscillators cannot be mixed as separate signals — a polyphonic synth has
to hold both voices in one `scan`'s state.  A `zipSig` is the obvious
missing combinator and nothing has needed it yet.  Transcendentals (`sin`,
`sqrt`) are likewise still absent; the oscillators here are saw, square and
triangle, which need only arithmetic.

### F89. **[resolved]** One example each is not enough to know a backend works

`bounce.ges` and `blip.ges` each exercised one shape of program.  A second
of each, deliberately unlike the first, is what tells you whether the
vocabulary generalises — and both found something.

**`examples/gui/chain.ges`** holds a *list* in its state rather than one
value.  Written first as a chain of eased segments, each following the one
ahead; that looks right on paper and is nearly motionless in practice, since
a segment moves 0.38 of what the one ahead moved and 0.38¹⁵ is nothing.  It
is a **trail** now — the head eases toward the pointer and the rest is where
the head has just been — which is both simpler and the better illustration:
a signal is a cell overwritten in place and does not remember, so a program
that wants the past carries it explicitly, and sixteen positions costs
sixteen positions.

**`examples/audio/drums.ges`** is three voices and a noise source.  Noise is
a fold: the state carries an LCG seed and steps it every sample, so the same
program renders the same file every time — worth having in a sound you mean
to keep.  The kick is a triangle whose pitch falls 195 Hz to 45 Hz across
its envelope; no `sin` is involved anywhere.

It also runs straight into the gap F88 recorded: **`mapSig` cannot pair two
signals**, so three voices are not three signals added together but three
readings of one `Kit` state, summed as it becomes a sample.  Two examples
have now wanted `zipSig`.  That is the argument for building it; it was not
built today.

### F90. **[resolved]** `zipSig` — two signals could not be combined

`mapSig` maps one signal; nothing paired two.  A synth therefore could not
mix two oscillators as two signals, and had to hold both voices in one
`scan`'s state — which `drums.ges` does and which two examples had by then
wanted (F88, F89).

The reason it is not a two-line function is that **two signals need not tick
together**: each has its own clock.  So the tails cannot simply be paired.
`sync` reports which arrived —

```
SyncLeft s2     -> q2 f s2 t      -- only the left advanced; keep the right
SyncRight t2    -> q2 f s t2
SyncBoth s2 t2  -> q2 f s2 t2
```

— and carrying the other one over is sound precisely because a signal is a
*cell overwritten in place*: the one that did not tick still holds what it
held, so there is nothing stale to read.

`mkSig`, `mapSig` and `scan` had been copied into both `gui.ges` and
`audio.ges`.  A third combinator was the point to stop: they live in
`gestate/signal.ges` now, with `zipSig`, `addSig` and `gain`, and both
backends prepend it.  It declares no constructors, so it renumbers nothing.

**A trap found on the way, and worth more than the function.**  Channel
identifiers are handed out in *evaluation* order, not declaration order, and
`:::` evaluates its tail before its value — so in a program declaring
`lchan` then `rchan`, the **right** signal's channel is 0.  Testing `zipSig`
against the wrong numbering made it look as though `SyncLeft` and
`SyncRight` were swapped in the runtime, and the packing in `reactive.py`
was very nearly "fixed".  Settling the identities by *element type* showed
`zipSig` correct in every case.  `test/test_signal.py` pins the ordering
itself, so the next reader is told rather than having to find out.

### F91. **[resolved]** The audio renderer drove the wrong channel

`render()` picked `min(reactive.chans)` as the audio clock.  Channel ids are
handed out in **evaluation** order (F90), not declaration order, so a
program that declares its own channel can perfectly well take id 0 and leave
`audio.ges`'s `clock` at id 1 — at which point the renderer advances the
user's channel once per sample and never ticks the clock at all.  The synth
does not advance; every sample is the value the signal started at.

No example declares a second channel, so nothing had ever exercised it.  It
became reachable the moment stage 3 of `spec/liveaudio.md` wanted a
**control-rate** clock, and the first two-clock program written hit it
immediately: `clock` was 1 and the new channel was 0.

Fixed by resolving the clock **by name**: dereference the `clock` global to
its `NChan` and read the id.  That is exact, and it is available for the
same reason F90's trap exists — the id is a runtime fact, so the only
reliable way to name a channel is to ask the global that holds it.  The
old behaviour survives as a fallback for a program with channels but no
`clock`.

`render()` also grew `control_every`, which advances every *other* channel
once every so many samples.  That is the oracle for control rate: without
it a second clock never ticks offline, and there was nothing to check a
two-clock graph against (`spec/liveaudio.md`, open question 3).
`test/test_audiograph.py` covers both halves.

### F92. **[resolved]** An instant was one arrival, so two clocks were two instants

`react(reactive, inputs)` ran a full `reactive_step` **per input**, which is
the paper's κ ↦ w and is right for two independent events.  It is wrong for
two *clocks*.  A block boundary is an audio clock and a control clock
ticking at the same instant, and running them one after the other advances
every signal downstream of the control clock by a step that no sample is
taken at.

Three consequences, in the order they were noticed:

- **`sync` never reported `SyncBoth` from the driver.**  `_pack_both` was
  reachable only when both sides of a `sync` watched the same channel — so
  the `.kr → .ar` boundary `spec/liveaudio.md` §"Two clocks" is built on
  had no way to occur, in the one place it was supposed to.
- **A `scan` under the control clock accumulated twice per boundary.**  With
  a knob holding 40 and an 8 arriving, the interpreter added 48 in one
  sample where the engine added 8.  For maps and zips the extra instant
  leaves no state behind, which is why stage 7.3's test passed and why the
  claim there had to be narrowed to what it had tested.
- **The oracle stopped being the oracle.**  `examples/audio/knob.ges` had no
  golden buffer on purpose: committing one would have frozen one of two
  answers.  Every stage of `spec/liveaudio.md` is verified against
  `render()`, so a program the oracle disagreed with the engine about was
  outside the plan's method entirely.

**Fixed by making an instant a set of arrivals.**  `Arrivals` is
`{channel id: input node}`, threaded through `ticked`, `advance`,
`_update_one` and `reactive_step`; `react_instant` runs one instant on
several channels, and `react` is unchanged — one arrival, one instant.

It is conservative because of the shape of the rules rather than by
argument: each asked exactly two questions of κ, *is this the channel that
ticked* and *what did it carry*, and both have per-channel answers.  Set
membership for the first, a lookup for the second.

The lookup half is the one with teeth.  `advance` used to take a single
`input_node` and hand it down the recursion, so `wait κ` returned it
whatever κ was — safe only because `ticked` had already gated the call on
one channel.  With two arrivals that would give a `sync`'s control side the
audio side's sample, so `advance` now reads the channel out of the node and
indexes the map, and raises if the channel did not arrive.  Two values on
one channel in one instant is refused for the same reason: that is two
instants, and letting the second silently win would drop an input.

`spec/frp.md` §"Several arrivals in one instant" states the extension
against the paper's rules and what it must degenerate to.

**What it is checked by**: `knob.ges` has a golden buffer now — 600 samples
at 2 kHz, `control_every: 64` in its header, since a control-rate buffer is
only defined against the block schedule it was rendered at.  Oracle,
extracted graph, block renderer and generated LLVM are bit-identical on it.
`test_audiograph.py` keeps the number that found the defect, now agreeing at
8 per boundary in both rather than 48 in one and 8 in the other.

### F93. **[deviates]** A graph node's `clock` claimed to be inherited, and is not

`audioir.Node.clock` documented itself as *"Only a `source` has one; every
other node inherits its inputs'."*  The second half does not happen.  The
extractor sets `clock` when it builds a source and never again, so every
`map`, `scan` and `zip` keeps the default `"audio"` whatever it reads —
and no reader minds, because the engine (`audioengine.py`) and the code
generator (`audiollvm.py`) both consult `clock` **only inside their
`kind == "source"` branch**.

Harmless in the sound and misleading in the file, which is the combination
worth recording.  It cost something immediately: `audiospans.controls` was
written to select nodes by `clock == "control"`, which is the reading the
docstring invites, and would have offered a knob for a `mapSig` over a
knob — a node the host cannot supply a value for.  It selects
`kind == "source" and clock == "control"` now, and says why.

**Not fixed, under the rule.**  Propagating the clock is what a per-block
evaluation of control-rate subgraphs would need — a real optimisation, and
one nothing has asked for: a control-rate `map` is evaluated every sample
today and produces the right samples, just more often than it has to.  The
docstring is corrected to say what is true instead, and names what would
have to change if a caller appears.

`test/test_audiospans.py::test_only_a_source_is_offered_as_a_control` pins
the consequence, so a future propagation cannot silently change which
nodes an environment treats as parameters.

### F94. **[resolved]** A former nested inside a former lost its element type

`zipSig f a (zipSig g b c)` extracted with the inner node's `type_` empty,
because `_former` threaded `""` down to its inputs and only `_inline` — the
path a *named* signal definition takes — ever computed one.  Every example
named its intermediate signals, so nothing had produced the shape.

The failure was in code generation, far from the cause: `no layout for ``.

Fixed where the answer already was: **a step function's type says what its
signal's elements are.**  `zipSig f l r` with `f : a -> b -> c` means
`l : Sig a`, `r : Sig b` and the node `Sig c`; `scan f z s` with
`f : b -> a -> b` means `s : Sig a`.  So `_former` reads the step's arrow
and types its inputs from it, which needs no threading at all.  A *lambda*
step has no written type by then, and that case now raises naming the fix
— a signature, or a name for the inner signal — rather than reaching a
back end with an empty string.

Found while writing `examples/audio/twoknobs.ges`, where `zipSig pairUp
pitch cutoff` inside another `zipSig` is the obvious way to combine two
knobs.  Unrelated to control channels, and reproducible on one clock.

### F95. **[fixed]** The fragment admits tuples; the extractor now lays them out

`spec/liveaudio.md`'s flat-type grammar lists `A × B`, and `is_flat` agrees:
`tuple_parts` is checked before anything else and a tuple of flat types is
flat.  So `audiograph.check` **passes** a program with a tuple-valued
signal, and `audioextract` then refuses it:

    fragment check passes: True
    extract: ExtractError: `(Float, Float)` is not a data type gestate knows

The checker promising what the extractor cannot deliver is the one shape of
disagreement this stage was built to avoid — `spec/liveaudio.md` stage 1
exists so that a rejection names *which definition* and *why*, and here the
rejection arrives a stage late with a message about data types for a program
that mentions none.

**The cause is representation, not an oversight in `_layout`.**  A tuple is
an `NTuple`, which the G-machine deliberately gives *no tag* and never
matches with `CaseJump` — field access goes through `Proj`.  Every other
flat value in the audio IR is an `NCon` with a tag word, which is what
`Graph.layouts`, `audiollvm`'s struct emission and `unpack_state` are all
written against.  So admitting tuples means giving the IR a tagless product,
not adding a table entry.

**Fixed — the extractor grew tuples, and this entry outlived the problem.**
Re-run today, the disagreement is gone:

    fragment check passes: True
    extract: OK
    sound : Sig (Float, Float) renders identically through the oracle, the
    block renderer and the generated code

The representation objection above was answered rather than worked around:
a tuple reaches the engine with a tag like any other product — the block
renderer hands back `(202, (l, r))` — so `Graph.layouts`, `audiollvm`'s
struct emission and `unpack_state` need no tagless case.

**Two live decisions still cite this entry as their reason, and should be
revisited rather than left standing on it:**

* `signal.ges`'s `Both` is "a **record** rather than a tuple, because the
  extractor lays out `Int`, `Float` and declared data types and nothing
  else (`fixme.md` F95)".
* a `voices` bank generates its own `Part` records for the same stated
  reason.

Neither is *wrong* — a named record documents what its fields mean, which
a tuple does not — but the constraint they were chosen under is gone, so
the choice is now taste rather than necessity.  The same applies to
`Stereo`, which `sound : Sig (Float, Float)` could now replace.

Found while costing n-channel output, which does **not** depend on it: a
record of `Float`s already extracts, carries its layout and reaches
`%State`.

### F96. **[resolved]** The fragment refused a parametric payload it admits

`audiograph.py`'s `ECon` case asked `is_flat` about the constructor's
**declared result type**.  For `Played a := Played Int Int a` that is
`Played a`, whose `a` is the declaration's own parameter — so every use was
refused with *"field a-57 is a type variable, so its size is not known at
compile time"*, while `is_flat(Played Custom)` is `True` and the extractor's
`_layout` substitutes and lays it out perfectly well.

A fragment check rejecting programs the fragment admits is the one failure
it must not have.  `spec/liveaudio.md` stage 1 exists so that a rejection
names the definition and the reason; here the reason was an internal
variable id from a type the author never wrote.

**Fixed by judging the constructor's *shape*.**  An `ECon` carries a tag and
its arguments, not an inferred type, so the use site's type is not available
at this point; `_monomorphise` substitutes a known-flat stand-in for every
type variable and the result is checked as before.  That is sound for what
this check is for: a recursive or function-valued field is disqualified by
its own structure whatever its arguments are, so `Cons` is still refused —
`List` is recursive whether its element is `Int` or anything else — and the
message is now about a list rather than about `a-57`.

What it deliberately does not decide is whether the *argument* at a use site
is flat: `Played (List Int)` looks flat here.  Nothing is lost, because
building that list is refused by this same check one constructor down.

Found while separating a note's **payload** from its **timing**: a voice
should be handed its own record with `gateAt`/`offAt` alongside, and
`Played a` is that wrapper.  The check made the wrapper unwritable.

### F97. **[resolved]** Nine defects in the host layer, and one shape between them

Recorded as one entry rather than nine because they are one finding.  Each
was in the Python **around** the engine — the driver, the editor, the note
reader — not in the language, the fragment, the extractor or code
generation.  That half has the bit-identity comparison behind it and turned
up almost nothing; this half has no oracle, several paths that only run
with a person present, and produced a defect roughly per hour of work on it.

What they were:

* **`Node.chan` did not exist.**  The interpreter drives *channels* and the
  engine drives *nodes*, and a schedule needs one name both resolve — there
  was none, so a note could not be delivered to both and compared.
* **A voice built from control channels alone runs at control rate**, so
  its oscillator advanced once per block.  The synth plays, at a fraction of
  the right pitch, reporting nothing.  Found only because a channel came out
  missing and `_channels` promoted a *note* channel to the audio clock.
* **`Notes.now` was updated only after a note had been played**, so the
  first note of a session was stamped at instant 0 while the engine was
  minutes in.  Its envelope had decayed before anything read it: the note
  played, silently, and every indicator said it had worked.
* **The PortAudio callback asked a `Transport` for `Engine.frames`.**  A
  callback may not raise — cffi swallows it — so the stream went on
  producing silence rather than reporting an `AttributeError`.
* **`ctypes.cast` refuses a cffi buffer**, which is what PortAudio hands
  that callback.  Same silence, one layer down; visible only once the
  callback learned to abort.
* **`audiospans` parsed the author's raw source** for the names it defines,
  and a `voices` declaration is not gestate syntax — so every placement in a
  program with a bank failed, reported as something true that said nothing.
* **`_load_score` performed the piece twice**, once for the tempo and once
  inside `scored`, on top of the two front ends a rebuild already paid.
* **A bank the score drives was left out of the allocators**, so ticking its
  switch set a flag on a bank that was not there.
* **The score won over the keyboard always**, so a note played on a scored
  bank was allocated, shown in its row, and never heard — the schedule was
  read first and the played value never reached the engine.  And the switch
  gated only the `FromMIDI` path, so a *greyed* switch went on passing notes
  through the older one.

**Four of the nine were silent** — the synth played and nothing reported
anything, which is the failure mode this layer specialises in.  Three were
found by the author playing a keyboard rather than by a test.  What that
argues for is not more care but the thing the audio core already has: a way
to be *wrong on purpose* and see it.  There is no obvious oracle for "a key
was pressed and a sound came out", which is why the tests written for these
assert on **samples** rather than on the bookkeeping that reported success
the whole time it was broken.

### F98. **[resolved]** A file that both draws and plays was several programs

One entry rather than seven, because they are one finding with one shape:
**`gestate/audio.py`'s `preludes` is the single answer to "what vocabulary
is this program written in", and almost nobody asked it.**  Every reader of
a file assembled its own text — the renderer, the canvas, the score, the
placement of knobs, the offset a line number is reported in — and each one
that assembled a *different* text was reading a different program.

Nothing showed it while a file did one thing at a time.  It took a file
with a `score` **and** a `substrate` — the obvious thing to write once both
exist — for the halves to disagree out loud:

* **`audioscore.assemble_performance` prepended `_AUDIO`**, never
  `preludes`, so a performance that also drew was checked against a program
  in which `Sub` was undeclared: `KindError: Unknown type constructor: Sub`,
  from `--holes`, `--fits` and the editor's sidebar alike.
* **`gui.ges` and `music.ges` both declared `Over`.**  One program, two
  declarations of one name, the later silently winning — so `over a b =
  Over a b` stopped type-checking, and `gui.py`, which looks `cons["Over"]`
  up *by name* to walk the picture, would have drawn by the score's tag.
  Renamed to `Par` in `music.ges`: the surface there is `||`, so no program
  wrote it.
* **`audiospans._regions` counted `_AUDIO` only.**  `gui.ges` is some three
  hundred lines, so in a file with a substrate every definition fell past
  the region believed to be the author's, was placed nowhere, and the
  program came up saying "no parameters" with its knobs in plain sight.
* **The canvas never expanded `voices`.**  `expand` is in `assemble` and
  the canvas assembles its own text, so a file with a bank *and* a
  substrate drew nothing: `expected pattern, got ':'`, at a line in a
  prelude.
* **The canvas had no `music.ges`** for a file with a score — `Unknown
  global '||'`, about a line in the piece.
* **The score's custom entry replaced `constSig` along with `main`.**  It
  was invisible until a prelude was written in terms of one; then reading
  the piece failed and the synth played no notes at all.

And one that is not an assembly at all but was found the same way:

* **The peak meter read the callback's buffer by index.**  The pipe driver
  hands it a `ctypes` array of floats and PortAudio hands it raw bytes, so
  `abs(buffer[i])` raised `TypeError` inside a callback that may not raise
  — and a file declaring `peak`, which is exactly a file with a canvas,
  played nothing on the low-latency path.  `audiolive.address_of` had been
  written for this same difference one layer down (F97).

**What it argues for.**  F97's lesson was that the host layer has no
oracle; this one is narrower and easier to act on.  There is one function
that decides what a program is compiled against and there were six
assemblies: every one of these is *"asked the question in a second place
and got a second answer"*.  The reason it survived is that each pair agreed
for every file anyone had written, and combinations are what a substrate
was built to make ordinary.  `test/test_substrate.py` now holds a program
that plays a piece and draws a fader, which is the cheapest thing that
would have failed on all six.

### F99. **[resolved]** One text, six front ends, twenty-eight seconds

`python -m gestate.audiopygame examples/audio/quartet.ges` did not appear
to open.  It opened after twenty-eight seconds, which from the outside is
the same thing: no window, no message, nothing but the shell.

Two separate faults, and the second is the interesting one.

**The window was built after the instrument.**  `run` called
`Workbench.start` and only then `pygame.init`, so the whole compile
happened with nothing on the screen.  The window now comes first and the
instrument starts on a worker behind it — 0.13 s to a usable editor.  It
costs one flag (`Pane.starting`, so `Ctrl-S` cannot start a second engine
onto the sound card) because every other question the chrome asks already
had an answer for a workbench with no instrument: that is the state a file
that will not compile leaves behind, and `run` has had to survive it since
the editor learned to open on one.

**And the twenty-eight seconds were mostly the same work, done again.**
Starting a file ran the front end four times over one program — the
engine's graph (`audioperform.graph_of`), the knob placement
(`audiospans.located`), the `FromMIDI` instances (`_load_from_midi`) and
the piece (`audioscore.perform_voices`) — and *assembled* it five times,
each assembly re-parsing the program once per `voices` bank.  Nine and a
half of those seconds were spent discovering that `quartet.ges` has no
knobs.

None of the readers is wrong to ask.  They are separate on purpose: a
placement that fails must not stop the sound, the piece is read through a
different entry point, and the canvas is a different assembly again.  What
was wrong is that asking twice cost twice, for a question whose answer
cannot have changed — the source is the same string.

So three things are kept, all keyed on the exact text that produced them:

* `pipeline.analyse` — four recent analyses.  Sound only because an
  `Analysis` *stays usable*: a later front end does not disturb one and
  `compile` reads rather than rewrites it, both of which are now tests in
  `test/test_pipeline.py` because inference is destructive through a module
  global and that is exactly the sort of thing that makes it false.  The
  lookup happens **before** `_FRONT_END` is taken, so the sidebar's
  questions no longer queue behind a rebuild.
* `audiovoices.expand` — text in, text out, and every assembly wants it.
* `audiovoices._prepared` — the bank reading, which is a parse per bank.
  A `Bank` is mutable (`_prepare` fills its payload in), so what is kept is
  the reading and what is handed out is a copy.

| | before | after |
|---|---|---|
| `Live.start` (front end, extraction, `clang`) | 4.7 s | 4.5 s |
| knob placement | 9.5 s | 1.5 s |
| the piece | 7.2 s | 4.2 s |
| `FromMIDI` | 2.4 s | 0.3 s |
| **to a playing instrument** | **23.7 s** | **10.4 s** |
| **to a window** | **28 s** | **0.13 s** |

The editor's own questions gained more than the numbers show: `?` and
`Tab` each ran a whole front end on the text you are looking at, which for
this file was three seconds a keypress and is now instant after the
sidebar's first look.

What is left is real work — a front end, an extraction, a `clang`, and an
interpreter laying out the piece — and the two halves that remain
duplicated are duplicated for a reason: the score is compiled with a
different entry point (`main = (bpm, layVoices score)`), so it is a
different program and not a second look at the same one.

**What it argues for.** The same thing F98 did, from the other side.  There
it was six readers assembling *different* texts and disagreeing; here it is
six readers assembling the *same* text and each paying for it.  Both follow
from the same shape: a reader that wants a program says so by building one,
and nothing between them knows that the last reader just did.

### F100. A constraint naming a class that does not exist is accepted

Found while typing `spec/commands.md`'s vocabulary, where two classes
say which road a command may be reached by — `FromMIDI` for a bank that
hears a keyboard, `FromCC` for a knob a controller can drive.

    f : (Nonsuch a) => a -> C          -- accepted
    f x = S

A signature may name any class at all.  Nothing resolves the name at
the point it is written, so a typo — `FromMidi`, `FormCC` — is a
constraint that constrains nothing, silently.

**Use sites are checked, and that is why this is small rather than
serious.**

    use : (Fc a) => N a -> C
    bad : N Int -> C
    bad n = use n
    -- ConstraintError: No instance for Fc Int

So a *real* class does the work it promises: `listen` on a bank whose
payload has no `FromMIDI` instance is refused, which is the whole point
of putting it in the type.  What is missing is the check that the class
in the signature is a class at all.  A misspelled one degrades to no
constraint — the signature reads as a promise and keeps none.

The fix is where the other kind checks are: resolve the name against
the declared classes when a signature is elaborated, and say *why* —
`no class \`Nonsuch\`; did you mean \`FromCC\`?` — which is the
`subgrammar.py` shape `spec/liveaudio.md` asks of the fragment check.

### F101. **[resolved]** The editor delivered no touches, and both of its specs agreed it was fine

`spec/substrate.md` builds its whole argument on a picture you can
touch — `onTouchX`/`onTouchY` over a `Chan Float`, press grabs, motion
clamped to the element's extent — and `gui.py` implements all of it.
For a day and a half no host delivered a touch: `71b90af` deleted
`audiopygame.py`, whose event loop was the only mouse-to-touch bridge,
and `spec/workbench.md`, written in that same commit, listed eight
gesture verbs and `touch` was not among them.  The Rust shell
implemented its spec faithfully, so a press on the canvas fell through
to `keys::click` and moved the caret behind the picture.

**This entry is filed against the register itself as much as the
code.**  This file catches code disagreeing with spec; `errata.md`
catches spec disagreeing with paper.  Here two specs disagreed with
*each other* — `substrate.md` promising what `workbench.md`'s boundary
could not carry — and code agreed with the nearer spec, so nothing
fired.  A divergence between two specs is a fixme-class defect and
gets an F number; this is the first.

Resolved the day it was found: `touch(kind, x, y)` added to
`workbench.md`'s gesture list, `Gesture::Touch` in the shell with an
`on_canvas` branch per mouse event, the `touch` verb in `session.act`,
and seam tests in `test_session.py`/`test_audioeditor.py` that the
verb moves a real channel.  Post-mortem: `journal.md`, "The canvas
lost its hands".

### F102. **[resolved]** The canvas export carried the expansion's channels as the author's

Caught by `test/test_panel_fixtures.py` on its first run — the seam
test written because of F101, finding a second defect of exactly
F101's shape: two artifacts agreeing while the contract between them
drifted.

`substrate_of` promises **"every `name : Chan …` the file declares, in
the order written"**, and `test_export.py` asserts it — against
`substrate.ges`, which has no `voices` bank.  A file *with* a bank does
not parse plainly, so `_authored` falls back to the expanded text, and
`gui._channel_names` inherited the expansion's declarations:
`lantern.ges`'s canvas crossed with 31 channels, 28 of them
`lampsChan0f0`-shaped internals the host writes through slots and no
substrate can name.  Benign at run time — the authored names precede
the generated ones, so every id lands where it did — which is why
nothing visible ever went wrong, and why nothing green ever went red:
`substrate_parity.rs` tests literals frozen before the drift.

Resolved in `_channel_names`: the generated names (`banks_of` ×
`channels_of`, plus `holds<Bank>`) are subtracted, which is sound
because `audiovoices._refuse_collisions` already refuses an author
those spellings.  The freshness suite now pins program text, tags,
display walk, chans and bridge to the same bytes the Rust suite reads,
each failure message naming the regeneration step — so the next drift
on this seam is a red test with instructions rather than a stale
fixture holding a green light.

### F103. **[resolved]** The same file's canvas builds or fails typechecking, run to run

Two launches of the editor on the same `untitled.ges` (kept as
`test/sessions/F103-untitled.ges`), minutes apart,
from the same desktop icon.  One: the canvas builds and draws.  The
other: `the canvas did not build: Signature variable 'c' is rigid: it
stands for whatever type the caller chooses, so the body may not use it
as 'b -> c' (at prelude line 7:13–7:19)` — which is `flip`'s own
signature, in text that does not change between runs.  Evidence:
`test/sessions/F103-untitled-session.ges` /
`test/sessions/F103-untitled-session-2.ges` as recorded
2026-08-12 evening — the first thing the transcript's new `#!` notes
ever caught, on their first day.

A type error in fixed text that comes and goes is a race.  **Where it
is not**: the front half is already serialized — `_FRONT_END` in
`pipeline.py` is taken by every `compile` and `analyse` — so two
inferences cannot interleave, and a harness racing the performance
graph against the canvas compile against a loop-thread tokenizer
(6×6×N fresh texts, lock additionally neutralized) reproduced nothing.
An earlier claim of reproduction was a harness bug: `assemble()` on a
*scored* file misses `music.ges` and fails deterministically with
`Unknown global '|*'` — that is misuse, not the race.

**Where it therefore likely is**: the assembly layer, which runs
*outside* `_FRONT_END` and is shared between the editor's loop thread
(colouring, `_authored`, `vocabulary`) and both build threads —
`prelude._parsed`'s shared ASTs, `shadow_libraries`/`merge`,
`syntax._SEAMS`, the `assemble` caches.  A raced assembly that emits a
corrupted *text* (or hands a mutated shared AST to a consumer) then
fails honestly under the lock, wearing a typecheck error.

**To catch it next time**: the failure is now recorded with its exact
sentence in every transcript.  When it recurs, before anything else,
re-run the canvas build on the same text in the same process — if the
second build succeeds, hash and keep the assembled text of both, and
the diff is the corrupting structure's confession.  Until then this
stays open rather than wearing a plausible lock: `_FRONT_END` already
covers the part a lock was proposed for, and a fix without a
reproduction is a mask.

**Resolved 2026-08-14, with the reproduction this entry demanded —
and the entry's own serialization argument was the blind spot.**
"Two inferences cannot interleave" was true of `compile` and
`analyse`; it was not true of `typecheck._unifies`, the would-these-
unify probe behind `fits_in_source` and `holes_in_source`, which
enters `unifying()` directly on the session thread (`do_fits`, and
`Workbench._find_holes` after every apply) with no `_FRONT_END`
anywhere in its path.  Under the old module-global `_CURRENT`, a
probe's scope exit restored *its* saved `previous` over a build
thread's active store mid-inference — the build finished its walk
against a stranger's bindings and failed honestly, wearing a
typecheck error such as `flip`'s rigid `c`.  Whether a launch built
or failed depended on whether a hole refresh happened to overlap the
canvas build: a race between two things one keypress starts.

The 2026-08-12 harness raced builds against a *tokenizer* and found
nothing because the tokenizer never touches the store; today's
harness raced two cache-busted canvas `Substrate` builds against two
threads spinning `_unifies` for 50 s.  With `types._CURRENT` reverted
to a shared object: **7 failures**, among them `Type mismatch:
expected Float -> Sig Sub -> Sig Sub` and `dictionary changed size
during iteration` — the run-to-run flip, on demand.  With the shipped
`threading.local` (the 2026-08-13 fix, made for that day's suite
poisoning before anyone knew it was also F103): **0 failures**.  The
deterministic shape is held by
`test_types.test_unifying_scopes_do_not_cross_threads`; the assembly
layer this entry suspected was innocent.

### F104. **[resolved]** The fragment classifies a specialised method per name, and refuses a program that uses it both ways

`test/sessions/F104-hello.ges` (2026-08-13, Henri's, two lines):

    sound : Sig Float
    sound = let freq = 440.0 in sine freq * saw (freq*1.005) * 0.01

Refused: `` `fromFloat` (of `Floating Float`) is used both as a signal
(via `sound`) and as an ordinary value (via `phase`) ``.  The refusal
is now *legible* (the provenance and the demangling are 2026-08-13's
message work) and it is still wrong: `__Floating_Float_fromFloat__` is
one shared specialised definition, and `audiograph`'s walk gives every
name one kind globally — but an instance method at a flat type is
legitimately a scalar wherever it is called, and its "signal" use is a
literal being lifted.  A per-name classification is too coarse exactly
for the definitions `specialise.py` shares.  The shape of the fix is
to admit flat-instance methods the way `PRIMITIVES` are admitted, or
to classify per use; either way `F104-hello.ges` is a reasonable program
and must compile.

**Resolved 2026-08-13, and not where this entry pointed.**  The
classification was the messenger: `__Floating_Float_fromFloat__`
really was standing in a signal position, because inference had put
it there.  `let freq = 440.0` generalized the binding over its
`Floating` variable while the pending predicate kept naming the
*original* variable — the uses instantiated fresh copies and pinned
those to `Sig Float`, nothing ever reached the original, defaulting
made it `Float`, and the one shared binding was elaborated with the
wrong dictionary.  The reference engine died on the same program
(`SigHead on non-NSig`), which is what said the defect sat upstream
of the fragment; `audiograph.py` needed no change at all.  The fix is
the monomorphism restriction, in `infer._generalize_let`: a variable
a pending constraint mentions is not quantified, so the use site
settles it.  Not Haskell nostalgia but a soundness condition of this
elaborator — a binding is one expression, resolved once by its site,
so it can only ever be handed one dictionary, and quantifying a
constrained variable promises a per-use choice nothing downstream can
deliver.  `test_audiofragment.py` holds the two-line specimen and a
render parity against the written-out form.

### F105. **[resolved]** An internal dictionary-count invariant surfaces as the user's error message

`test/sessions/F105-hello2.ges` (same day, a `voices` bank +
`FromMIDI` instance + an `Adsr`): the whole complaint is

    ''' expects 1 dictionary argument(s), inference produced 17

Two defects in one line.  The count mismatch itself — something in
elaboration hands a specialised definition seventeen constraints where
its arity says one — and the report: an internal invariant wearing a
mangled name (rendered as `'''`) in the place a user message goes,
with no position, no author name, and no sentence.  Whatever the count
bug turns out to be, the *invariant style* must never reach `trouble`
raw; it should say which declaration it was elaborating, like
`infer._blame` now does for unification.

**Resolved 2026-08-13, and the seventeen had a face.**  The match
compiler shares an equation's body across the leaves of its decision
tree, so the *fallback* of a string pattern is reachable from every
failure edge of the match — and `"question"` has seventeen of them
(eight cons-tests, eight character-tests, one nil-test).  Inference
walks the shared `'` node once per edge and stamps all seventeen
identical `Monad Score` predicates onto its one site token; the
router's arity check read the repetition as inference having produced
seventeen dictionaries.  One occurrence has one type, so
`_group_by_site` now deduplicates equal predicates within a site —
`bimix`'s two *distinct* ones still come through as two, which the
regression test needs exactly.  And the report half: the message
spells the name in backticks (`` `'` `` rather than `'''`), says what
arrived, and `elaborate` wraps the rewrite in the same
`infer._blame` breadcrumb unification gets, so anything that trips
this seam next names the declaration and its position.  Tests in
`test_dictionaries.py`; the specimen compiles and renders 15 s of
score.

### F106. **[resolved]** The drawn piano retriggers a held key

`pianoOn`, hold a key: the OS keyboard autorepeat arrives as repeated
presses and each one plays a note — a held key should sound once until
released.  The window knows the physical key (`Gesture::Struck`
carries the keycode precisely so releases match presses); repeats of a
key already down should be swallowed at that seam.

**Diagnosis, 2026-08-13, while writing the piano's contract into
`spec/workbench.md`**: that seam already swallows repeats — the
shell's `fingers` set predates this report by two days — and the
model's `Keyboard.press` refuses a note already held besides.  Both
guards standing while the retrigger was heard means the repeats do
not arrive as repeated presses: X11's default autorepeat is a
*release+press pair*, which empties the `fingers` set and re-arms
both guards per repeat.  The fix's shape is detectable autorepeat —
`keyboard_types`' `repeat` flag if baseview sets it on X11, or
`XkbSetDetectableAutoRepeat` — and it needs a hand on a real keyboard
to verify, which is why it is diagnosed here rather than fixed: a
guard nothing can exercise is a mask (the F103 rule).

**Resolved 2026-08-13, verified by hand, and the verification earned
its round trip.**  `XkbSetDetectableAutoRepeat` on baseview's own
display at window creation — per-client, so it must be that
connection and not one of ours — after which the server sends press,
press, …, release and the standing guards do exactly what they were
written for.  The first attempt was loaded and silently did nothing:
baseview answers the display question twice on X11, the platform
handle's answer is the XCB connection and the context's is the Xlib
`Display*`, and matching `Xlib` against the first is an arm that
never fires.  Henri's machine-gun report is what caught it, and
`GESTATE_EDITOR_KEYS=1` now prints what detectable autorepeat
answered so the next such fix cannot pretend to be in the room.
Held arrows and letters in the text still repeat — repeats still
arrive, only the fake releases stop.

### F107. **[resolved]** Up/Down inside a typed argument runs the command

Palette, `seek 0`, then Up or Down (perhaps reaching for history or
the choice list): the command fires.  Arrow keys inside an argument
box must never be an accidental Return.

**Resolved 2026-08-13.**  The arrows "walk a finished call" — for the
`find`/`findBack` pair that is the next match and the one before,
which is right — and a call with *no* declared reverse "simply
repeated", which is exactly the accidental Return.  `Palette::step`
now answers nothing for a call without a reverse; repeating a
finished call is Enter's, deliberately.  The find pair keeps its walk
in both directions (`the_arrows_walk_forwards_and_back` still
passes); `an_arrow_is_not_an_accidental_return` pins the fix.

### F108. **[resolved]** `pianoStep` writes notes with no separator

Step mode inserts `50` where it should insert `50 ` — two steps write
`5050`, which is one wrong number rather than two right ones.  The
insert should carry the trailing space (or whatever separator the
surrounding text calls for).

**Resolved 2026-08-13**: `Workbench.note_text` brings its own
trailing space — everywhere a bare number goes, whitespace separates.
Pinned by `test_a_stepped_note_carries_its_separator`.

### F109. **[resolved]** Opening a file waits for the previous file's start instead of cancelling it

Reported from use, 2026-08-13 (and made likelier the same day: `open`
on a fresh name now starts a new file, so opening *away* from a big
file mid-compile is an ordinary move).  `workbench.run`'s loop, on a
`wanted` file, does `quitting.set(); starter.join(timeout=15.0)` —
**a synchronous join in the gesture loop**, so the window answers
nothing until the previous instrument's `start` finishes its `clang`
and its sound-card open; the switch that should be immediate arrives
seconds late.  And `quitting` is only *consulted* after `start`
returns, so nothing in flight is truly cancelled — the old compile
runs to completion for a file nobody is looking at.

The fix's shape: switch the window at once, and hand the old
`(bench, starter, quitting)` to a reaper that stops the instrument
whenever its start does return — which is exactly the contract
`_begin`'s `quitting` flag already implements, minus the join in the
loop.  True cancellation of a compile in flight is a bigger question
(the subprocess could be killed; the Python half cannot), but the
*felt* bug is the join, not the wasted compile.

**Resolved 2026-08-13, in exactly that shape, verified by hand.**
`_retire` takes the join and the stop onto their own thread the
moment a file is wanted; the window switches at once.  The ordering
the old join was really buying — the sound card is not free until
the old instrument is truly gone — is kept where it belongs: the new
instrument's `begin` waits on the retirement *on its own thread*
before starting, and a start overtaken by yet another file while
waiting its turn never begins at all.  The quit path stays
synchronous and joins the retirement first, so the process cannot
exit over a teardown still running (the daemon-thread segfault
rule).  `test_opening_away_does_not_wait_for_the_old_start` pins
both facts — the loop is held under 0.2 s, and "stop old" precedes
"start new" — and fails in 0.65 s on the old loop.  The wasted
compile still runs to completion, as predicted above; it is now
merely wasted rather than felt.

### F110. **[mostly resolved]** The zoom could wedge — the mirror only synced after input

Reported 2026-08-13, found with the zoom buttons; the transcript
(`test/sessions/F110-zoomOut-stuck.ges`) showed the model's mirror twelve
rungs up a **nine**-rung ladder, answering `smaller` twelve times
while the window sat at the largest.

**Root cause found and fixed the same day, one line**: `tell()` — the
only thing that syncs the model's mirror — fired only from the input
paths (`after`, the order handler).  A window nobody had touched never
volunteered its state, so the mirror sat at its `0/1` initials and
refused every zoom in both directions (reproduced exactly); and a
mirror corrupted by *anything* stayed corrupted until a keystroke
happened to heal it.  `on_frame`'s poll now calls `tell()` every pass
— the `told` guard makes it free when nothing moved — so no mirror
drift can outlive one frame.  Verified against the real window:
mirror settles with zero input, full ladder walks both ways, refusals
only at the true ends.

**Still unexplained**: how the recorded mirror ever reached 12/13+.
No path in today's source can set it past the rungs; suspect an
earlier build or a `state` field drift since healed.  With the
per-poll sync it cannot persist, so this stays a note rather than an
open defect — reopen if a transcript ever shows it again.

### F111. **[resolved]** Space in `transcript`'s path box erases the path

Reported the same session: `transcript` proposes a path in its
argument box (`Order::Fill`), and pressing space wipes what was
filled instead of typing a space.  Whatever the palette does with
space in an argument query — separator, choice step, or a
first-keystroke replace of proposed text — it must not eat a path
somebody was about to accept.

**Resolved 2026-08-13, and it was the choice step.**  A `Path`
listing opens with the cursor on a row nobody chose — `../` at the
top — and space's accept-the-pick semantics "stepped" into it: the
proposed path, one Return from being taken, was replaced by the walk.
Space in a `Path` box is now content, the same exemption `Text` has;
taking the path is Return's, and Tab completes (F117).  Pinned by
`space_does_not_eat_a_proposed_path`.

### F112. **[resolved]** The file dialog's listing sometimes lags

Reported from use (2026-08-13), unmeasured: the dialog's listing
appears a beat late sometimes.  The instrument for this class of
report exists — `tools/lagcheck.py` drives the real window through
XTEST and reads the screen — and pointing it at the dialog is how
"appears to" becomes a number before anything is changed.

**Measured 2026-08-13 (`tools/dialoglag.py`, the window's own
`GESTATE_EDITOR_TIME` stopwatch): settled, query->list averages
13 ms with a worst of 29 ms — imperceptible.  Driven mid-compile it
averages ~71 ms with a worst of 167 ms — a visible beat, and the
"sometimes".**  The dialog's code is innocent: the beat is the
gesture loop sharing its thread with a build, which is the starvation
`spec/performance.md` already documents in the extreme (an expensive
canvas or a startup compile pushing query->list toward a second).
The status line says a build is running exactly when the beat
happens, so the report is answered rather than the code changed —
the rule wants a caller before loop-pacing work, and a bounded beat
during a visible build is not yet one.  Reopen with a transcript if
a listing ever lags past ~200 ms with *no* build in flight.

### F113. **[resolved]** Undo and redo cross a file switch

One undo history for the session, not one per file: open a second
file, press undo, and the edit that unwinds is the *previous* file's.
Whether a per-file history is wanted, or crossing is refused, is
Henri's to answer — what is certain is that an undo landing in text
the window no longer shows cannot be what the key meant.  `spec/
editor.md` requires text undo and says nothing about file boundaries,
so the spec needs the sentence too, whichever way it goes.

**Henri answered (2026-08-13): the barrier.**  And the code made the
stakes plain before the design did — the switch went through
`set_text`, which *commits*, so the old file's whole content sat on
the new file's undo stack as one step: open B, press Ctrl-Z, and A's
text stood under B's name, one Ctrl-S from overwriting B with A.  Not
odd behaviour but a loaded save.

Resolved as two doors and a warning.  `Document::load`
(`ged_load_text`) replaces the text and clears both histories — a
different file is a different past — while `set_text` keeps
committing, because `fmt` depends on being one undo away.  And since
the barrier makes discarded edits truly unrecoverable, picking `open`
while unsaved makes the window flash the `[+]` and say *warning:
unsaved changes* in red — Henri's own design, refined twice while it
was built.  **Beside the caret that is active**: the query box's
while the list is up, the document's otherwise — words beside a caret
nobody is at are said to an empty chair.  **Held as long as the user
is there**: the warning stands until the list closes (the flash
settles after its first moments; a blink that never ends is a blink
nobody can read past).  And **a warning, not a gate**: a person who
chooses a file past it has decided, the switch proceeds, and the
edits go — history and all — which is what they were warned about.
And `load` marks the text saved — it came off the disk — because
left at the old file's root, a freshly opened file wore the `[+]`
from its first frame and warned about edits nobody had made (Henri
caught it on the first hand-test).
The `warn` order is in the spec's vocabulary; tests pin the barrier
(`loading_a_file_clears_the_histories`), both drawings
(`a_warning_stands_beside_the_caret`,
`a_warning_stands_beside_the_query_caret`, the `[+]` flash keeping
the bar's width), the warning firing once at the pick
(`test_picking_open_says_unsaved_at_once`) and the choice standing
(`test_open_warns_and_then_lets_the_choice_stand`).  Per-file
histories (buffers) remain the upgrade path if they ever earn a
caller; the barrier's contract is a subset of theirs.

### F114. **[resolved]** Copy and paste are not commands

The command list (`gestate/command.ges`) has no copy and no paste —
forgotten, not declined.  The vocabulary rule makes the fix's shape
plain: the capability appears in `command.ges` or it does not exist,
so this is two declarations and their gesture wiring, plus the
clipboard seam the shell owns.

**Resolved 2026-08-13** in exactly that shape, plus the honesty the
sentences needed.  `copy`, `cut` and `paste` are `Stated` commands
with their chords in the key column; each becomes an order the window
answers with **the same door the chords use** — `keys::press_with` on
the same `Key::Copy`/`Cut`/`Paste` — because two implementations of
what copying means is how they come to mean different things.  The
state mirror grew two fields, whether a selection exists and whether
the clipboard holds anything, so the refusals answer instantly and
honestly: "nothing selected", "nothing to paste" — "copied" over
nothing would be the lying switch `listen` was already cured of.  An
old window reporting seven fields still lands; the two newest ride at
the end.

### F115. **[resolved]** A bank added by an audition could not be listened to

Henri's report (2026-08-13, `test/sessions/F115-frommidi.ges` and its
transcript): start on a bankless synth, audition in a `voices` bank
with a `FromMIDI` instance, and `listen lead` answers `` `lead` would
not switch `` — three times in the transcript, because there is
nothing to learn from trying again.

The allocators followed the **disk**.  `_allocators()` read
`self.source()` while everything around it deliberately carries the
text being started — an audition never writes the file, so the
restart it forces (16 control channels into a player with room for 1)
rebuilt the engine from the audition and the note plumbing from the
disk: the engine played the bank, `_load_from_midi` offered it, and
`Notes` was `None`, so `Workbench.listen` declined silently and the
session's honest fallback said "would not switch".  The same omission
`restart` itself documents one layer up, where it once brought back
the program on disk.

Two fixes, because the Python driver has no fixed control block and
therefore never restarts: `_start_notes`/`_allocators` now take the
text they are starting (`_start` passes it), and an apply calls
`_refresh_notes(text)` — same bank set, keep the allocators and their
held voices; a changed bank set rebuilds them, which is what puts
something behind a new bank's switch.  `test_session_live.py::
test_a_bank_added_by_an_audition_can_be_listened_to` replays the
report's three facts and fails in 33 s on the old code.

### F116. **[resolved]** Every click was eaten while the command list was open

Henri's report (2026-08-13): "I can't click on things while command
menu is open."  The palette captured every left press while open — a
click on a row picked it, and a click anywhere else did nothing at
all, leaving the whole window dead to the mouse.

Resolved the way every menu on earth behaves: a click the panel does
not cover closes the list — through the same `hide()` Escape takes,
so the model's question ends too — and then **falls through to land
on whatever it was aimed at**: a knob, a bank box, a piano key, a
line.  A click inside the panel but on no row (padding, the query
row) stays the panel's.  The hit-test is `Palette::covers`, computed
from `panel_box` — the same arithmetic `frame` draws with, so the
panel that is drawn and the panel that is hit cannot disagree
(`covers_agrees_with_what_is_drawn`).

### F117. **[resolved]** Tab did not complete paths in the file dialog

Henri's report (2026-08-13): people expect Tab to complete on a file
dialog, and it did nothing — the key translated, reached
`Palette::key`, and fell through the match.

Resolved as every shell taught: Tab completes the query to the row
the cursor is on — a plain row becomes the text, a directory
completes to its own walk and re-lists — and nothing runs, because
taking the answer is still Return's.  Bound for every asked argument,
not only `Path`: completion is never wrong, and it simply has nothing
to do when the model offered no rows.  Pinned by
`tab_completes_the_path_under_the_cursor`.

### F118. **[resolved]** The list sat over a freshly opened file and caught the first keystrokes

Henri's report (2026-08-13): after `open bottleneck.ges` runs, the
finished call reads in the table — backspace steps back into the
question and Escape leaves, both right — but a plain key or Return
lands in the *palette*, when what anyone wants after opening a file
is to type into it.  Return on a finished call means *again*, which
is right for `find`'s walk and meaningless for `open`.

Resolved with the say-when-you-are-done the vocabulary already had:
`do_open` sends the `close` order on success, exactly as `template`
and `symbol` do — the model says when a command is finished with its
dialog, rather than the view keeping a table of which commands
repeat.  The next key you press types into the file you just opened.

### F119. **[resolved]** The caret anchored the scroll

Henri's report (2026-08-13): wheel the view away from the caret and
the scroll glitches — it keeps snapping back to keep the caret on
screen.  The wanted behaviour: a scroll runs free and the caret may
leave the screen; a caret move or an edit re-follows.

The scroll itself was already free — `keys::scroll` moves the top and
follows nothing.  The anchor was the **furniture handler**: every
arriving description re-ran `follow`, and descriptions arrive
whenever the model has news — the transport readout, while a piece
plays, has news every beat.  So the snap-back ticked with the music,
which is why it read as glitching rather than as a rule.

The `follow` there exists for one legitimate case — a content box
reflowing above the caret must not push the line you are typing off
screen — so it now runs only when the granted layout actually changed
(`foot_rows` or the box table).  A description that changes only the
status, the transport or the knob values leaves the scroll where the
hand put it.

### F120. **[resolved]** Opening a `.wav` quit the whole editor

Henri's report (2026-08-13): open a `.wav` from the dialog and the
editor exits.  The switch read the file's bytes *in the gesture
loop*, the UTF-8 decode raised, and the loop's `finally` closed the
window — a quit over a click.

Two layers, because a crash-shaped hole deserves a belt.  `do_open`
refuses a file that is not text with a sentence — "cannot open
take.wav: not a text file" — sniffing a chunk with its tail dropped,
so a UTF-8 character split at the chunk edge cannot fail an honest
text file.  And the loop builds the new `Workbench` *before retiring
the old one*, inside a try: whatever still gets through, the old
instrument plays on and the status says why, instead of the window
dying over it.

**The second face, from Henri's transcript**
(`test/sessions/F120-wav-session.ges`): his `blip.wav`
"opened" anyway — because it never existed at the path the dialog
resolved (`/home/cheery/gestate/blip.wav`; the real one lives in
`examples/audio/`), so the *new-file* branch started a STARTER synth
named `blip.wav`, sine and all, and the sniff — guarded by
`exists()` — never ran.  A started file is text, so a name wearing
one of the binary suffixes this toolchain itself produces (`.wav`,
`.mid`, `.clap`, `.png`, `.so`) is a miss, not a request — refused
with "no file blip.wav — and a new .wav would not be text".  Only
those refuse: an editor that would not start `notes.txt` would be
refusing somebody's notes over another file's format (Henri's own
softening of the first cut, which demanded `.ges`).

### F121. **[resolved]** A template inserted while scrolled away appeared behind the list

Henri's report (2026-08-13): leave the caret, scroll away, `template
voices` — the template is not in the view.  It was: `follow` brought
the caret's row to the *top* of the window, which is exactly where
the palette's panel stands, so the inserted text "appeared" behind
the list, invisibly.

`View::follow_past` is `follow` with the top rows treated as covered:
the window passes the panel's `shadow_rows` while the list is open,
so an ordered edit lands at the first row a person can actually see.

**And the second half, from Henri's template transcript**
(`test/sessions/F121-template-session.ges`): his
template landed at row zero — `edit "0:0:…"` — where there is nothing
to scroll past and `follow_past` saturates, which the first cut waved
off with "the panel covers what it covers".  It was his actual usage.
So **the panel moves instead of the text**, and the rule is
Henri's, refined against the running build: **the equator decides
the panel, the span decides the scroll.**  When the list opens, a
caret in the window's upper half sends the panel low.  When an
ordered insert lands, the span it put in decides both at once —
pasted above the equator, the panel goes low and the span's *first*
line stands on the screen's first row; pasted below, the panel stays
high and the span's *last* line stands on the screen's last row —
either way the person reads what the command just did, on the half
the panel is not.  Decided at those two moments and never per
keystroke, so the panel does not dance under a typing hand.  One
flag read by `panel_box`, which drawing, hit-testing (`row_at`,
`covers`) and the shadow all read — the one-arithmetic refactor from
the click fix is what made the flip a dozen lines — and
`shadow_rows` answers zero while low, so `follow_past` and the flip
cannot fight over the same caret.  (The first cut flipped on the
caret's own row and scrolled only the caret into view — which put
the template's *end* behind the newly-low panel; the span rule is
what reads right.)

### F122. **[resolved]** A typed path was walked twice

From the tail of Henri's template transcript
(`test/sessions/F121-template-session.ges`, 2026-08-13):
`transcript "../../template-session.ges"` from a file in
`examples/audio/` answered `[Errno 13] Permission denied:
'/home/template-session.ges'` — three levels up instead of two.

`_where` prepends the question's walked directory to the answer,
which is right for a **picked row** — rows carry names relative to
the walk — and wrong for a **typed query**, which is the whole path
already: the walk in the query and the walk prepended compose, and
`../..` became `../../../..`.  The tell is exact: an answer that *is*
the query was typed, an answer that differs was picked.  `_where` now
skips the walk for the former, and the transcript's own last step is
the regression test's shape.

### F123. **[resolved]** A finished `open` re-runs from a different directory

`test/sessions/F123-blip-session.ges` (2026-08-13): walk to `examples/audio/`, pick
`blip.wav` — refused rightly ("cannot open blip.wav: not a text
file") — then Return on the finished call:

    open "blip.wav"    #= cannot open blip.wav: not a text file
    open "blip.wav"    #= no file blip.wav — and a new .wav would not be text

Two different answers to one call, because the *question's walk* was
cleared between them: the first resolved `blip.wav` against
`examples/audio/`, the second against the file's own directory, found
nothing, and fell into the new-file branch.  Return-again on a
finished call should mean **the same call** — same resolved path —
not the same words resolved from wherever the state now stands.  The
shape of the fix: a finished call keeps the resolved path (or the
walk it was resolved under), rather than re-deriving it from
`asking` that has since been shut.

**Resolved 2026-08-13, verified by hand and by the specimen's own
replay.**  The window sent `Asked` the moment a command ran, so the
model forgot its walk while the palette still showed the finished
call — the two sides of the wire disagreed about whether the question
stood.  Both now forget together, when the list closes; a command
that takes nothing closed the list already and says so.  Two
companions ride along: `_where` takes the verb whose question may
lend its walk, so a standing question cannot contaminate another
command's resolution, and the replay's `_reask` leaves the question
standing — the live state — instead of restoring `None`, which had
the replay reproducing the very bug the specimen was recorded to
show.  Replaying `test/sessions/F123-blip-session.ges` now reports
exactly one moved answer: the second `open`, agreeing with the
first.

### F124. **[resolved]** The directory-watch tests flake under machine load

`test_a_file_that_arrives_shows_up_without_touching_the_query` and
`test_the_cache_still_watches_the_directory_the_walk_reached` failed
roughly ten times on 2026-08-13, every occurrence with a compiler or
test run in parallel, and passed alone every single time.  Both tests
sleep `Session.OUTSIDE_EVERY * 1.5` of wall-clock and then assert the
listing noticed the world move, so the suspicion is the obvious one —
a margin that load erodes — but ten observations of *which* tests and
*when* is not yet one observation of *why*, and the fix should not be
a bigger number chosen by hope.  Worth one session with the cache's
clock in hand; until then, a red on either of these two under load is
this entry, not a regression.

**2026-08-14: it is not load, or not only** — the arrival test now
fails *deterministically* in a full `test_session.py` run (three runs
in a row, machine otherwise quiet, EPP on performance) and passes
alone every time, on a tree with no dialog changes (verified at
commit `bce7ecc` via stash).  A deterministic order-dependence is a
much better specimen than a flake: something an earlier test leaves
behind — module state, a shared clock, an mtime the tmp dirs inherit
— survives into `_outside`'s key.  The session this entry asks for
now has a reproduction that holds still.

**Resolved the same evening, and it was none of those.**  The token
log said the second stat returned the *identical* mtime_ns after the
write — and a directory whose mtime does not move when a file lands
in it is the kernel's **coarse clock**: file stamps advance a tick at
a time, measured at 1–20 ms a granule on this machine (801 writes,
37 distinct directory mtimes).  The test's setup and its arriving
file fit inside one granule when the suite ran warm; alone, the cold
start spread them across two.  And the 2026-08-13 correlation with
parallel compiles inverts into evidence: load *stretches* the
granules, it was never eroding a margin.  The fix is the rule make,
git and ninja keep ("racily clean"): a stamp younger than
`Session.MTIME_SETTLES` is not a fact yet — the look rides the
token, so the listing is re-read once per `OUTSIDE_EVERY` until the
stamp has safely aged, and then the cache is a cache again.  Held by
`test_a_granule_hot_directory_is_not_believed`; the two old flakers
pass three consecutive full-suite runs.

### F125. **[resolved]** A phantom new file read as saved

Henri's exploration transcript
(`test/sessions/F125-exploration-session.ges`, 2026-08-13): he went
looking for the lantern, walked to `examples/gui/` — where it is not;
it lives in `examples/audio/` — and somewhere in the backtracking a
bare `lantern.ges` resolved against `test/sessions/`, did not exist,
and the new-file branch started a STARTER synth wearing the name.
Lawful at every step; bewildering in sum: `canvas` answered "this
file draws nothing" about a file he believed was the lantern, and
nothing anywhere said otherwise.

The recording gap hid the walk (the log restarts on a switch — the
roadmap item this transcript re-evidences), and the *durable* tell
was missing because of F113's own fix: `load` marks the text saved,
right for a file that came off the disk and wrong for one that does
not exist — the phantom read as written-down while "saving creates
it" was still true.  `load_written(text, false)` — `ged_load_new`,
`Editor.load_new` — is the second half of that door: a file being
started loads *unsaved*, so **a phantom wears the `[+]` from birth**,
and the first save settles it.  The loop picks the door by
`exists()`.

### F126. **[resolved]** The crossfade resolved the leaving engine's nodes against the live graph

Found by Henri jogging `+ lead * 0.1` in and out of the F105
specimen's `sound` — "it appears to not build the graph correctly
now" — and reproduced headless the same hour: commenting the bank
out shrinks sixteen control sources to one, the install crossfades,
and the whole audio thread dies with `IndexError: list index out of
range`.

`Live._blend` handed one `control` callable to both engines, and
`Workbench.control` resolves a node id through `live.engine.graph` —
the *live* graph, while the *leaving* engine's ids belong to its own.
A shrink indexed past the end; worse, a shifted id would have read
the wrong channel silently.  Pre-existing on every install whose node
table moved; the shrink was merely the first arrangement dramatic
enough to crash.  `_blend` now translates the leaving graph's nodes
to the live graph's ids by channel name — the identity a control
actually has — and a channel the new graph no longer knows reads
zero, because the engine holding it has forty milliseconds to live.

A companion rode along: the margin's `wired` treated an *empty*
channel set as "no graph to ask", so a fully disconnected bank kept
wearing its count — `_graph_channels` now answers `None` for
unavailable and an honest empty set for a graph with nothing but its
clock.  `test_commenting_a_bank_out_of_sound_survives_and_says_so`
jogs the comment both ways and fails in thirteen seconds on the old
blend.  Henri's stress jog (`test/sessions/F126-lol-session.ges`)
interleaves the toggles with `listen`/`deafen` churn — the corner it
cast: the switch may be thrown on a disconnected bank, and now the
sentence says so rather than promising sound ("lead hears the
keyboard — though it is disconnected").

### F127. **[resolved]** A literal applied to arguments answers with an instance at a function type

`test/sessions/F127-weird-issues-session.ges` (2026-08-13, the tail):
the typo `sound = 0.0 sine freq * …` — a number *applied* to two
arguments — answers

    not applied: No instance for Floating ((Sig Float -> Sig Float) -> Sig Float -> Sig Float)

which is inference telling the truth in its own language: the literal
wants `Floating` at whatever type the application forces, and that
type is a function's.  The human fact is one sentence — `0.0` is
applied to arguments, and a number takes none — and the message
carries neither it nor a position nor the `while checking` breadcrumb
on its *first* line, which is all the status bar shows.  The shape of
the fix is F105's report lesson one door down: when a `Num`/`Floating`
constraint lands on an arrow type and the expression's head is a
literal, say what happened in the author's terms, with the span of
the application.

**Resolved 2026-08-14, in that exact shape.**  Two halves.
`constraint.applied_number`: a `Num`/`Floating` predicate at an arrow
type can only mean a literal forced to a function's type, so the
author's sentence — *"a number is applied to 2 arguments, and a
number takes none — is an operator missing after the literal?"* —
leads the message, and the instance-speak keeps the second line,
where the content box shows it and the status bar need not.  And
`pipeline._discharge` solves constraints **by owner** instead of
flattened — the flat list had discarded which declaration each
constraint came from, which is why this one error had no home — so
`infer._blame` rides every constraint refusal with ``while checking
`name` (at L:C)``, and the workbench's position mapping turns that
into the file's own line: the box anchors under the typo itself
(`typo.ges:5`).  Held by
`test_a_number_applied_to_arguments_says_so_first`; the examples
suite passes whole through the regrouped solve.

### F128. **[resolved]** The text sniff refused `duet.ges`

Henri, returning after goodnight: "duet.ges doesn't open in
workbench.  That's... irony" — the flagship example, refused as "not
a text file" by F120's own fix, hours after a diary entry criticising
it for other reasons.

The sniff read 4096 bytes and dropped the last four before decoding,
so a UTF-8 character split at the chunk's edge could not fail an
honest file — except a fixed drop does not *remove* a boundary, it
**moves** it, and `duet.ges`'s box-drawing section headers put a `─`
straddling byte 4092 exactly.  The honest test was always *where*
the decode fails: a real binary fails in its first bytes, an honest
text file only at the cut, so a failure inside the final three bytes
is the chunk's fault and not the file's.  The regression fixture is
a file with a multibyte character built onto the boundary — and
`duet.ges` itself, so the irony cannot recur.

### F129. **[resolved]** An exactly-named directory loses to a fuzzy file

Henri, 2026-08-14, in the file dialog: typing `test` selects
`pytest.ini` rather than `test/` — a directory whose name **is** the
query, beaten by a file that merely contains it.  The palette's rule
already knows better ("a name match beats a prose match"); the path
listing needs the same law: an exact name — directory or file —
outranks a substring hit, and a directory named exactly what was
typed is almost certainly where the person is going.  The fix lives
where the ranking lives, in the model (`session.py`'s choice ranking
for `Path`), not in the view.

### F130. **[resolved]** A file you can name is a file the dialog cannot find

`lantern-session.ges` (Henri's transcript, 2026-08-14 — the new
base-text header and `#!` notes pinned it in three steps): from an
unwritten `untitled.ges`, `open` with the query `lantern.ges`
answered **0 rows** — the walk lists one directory, and lantern lives
two down in `examples/audio/` — and Return then resolved the typed
name against the walk's directory, found nothing, and started a
phantom.  Three times, because nothing ever said where lantern
actually was.

F125's half stands (the phantom loads unsaved, `[+]` from birth); the
missing half is *finding*: a query that matches nothing in this
directory should be offered matches from below it — a bounded
recursive walk, ranked by depth then name — so typing a name you know
reaches the file wherever it sits.  The refusal shape to keep: a
query with `/` in it stays a path being typed, and the deep matches
are rows to *pick*, never a silent rewrite of what was typed.

**Henri's follow-up, same day**: the query only *looked* like
`lantern.ges` — pressing Tab "spindles the path into something else
that only looks like lantern.ges on the screen".  So the Tab
completion (F117's) rewrote the query into a spelling that displays
the same but resolves differently — which is exactly how a session
transcript records `open "lantern.ges"` and the dialog answers 0
rows.  To pin: reproduce Tab on a query in the open dialog and diff
what the box *shows* against what `wants`/resolution actually
receives; suspect the walk prefix folded into the query (or a row's
bare name completed against the wrong walk), F122's typed-vs-picked
seam one key further in.

**Resolved 2026-08-14, all three faces.**  The spindle was
`palette.rs`'s Tab writing a row's *bare* name over the whole query —
`examples/audio/lan` + Tab showed `lantern.ges` and resolved at the
root; completion now keeps the query's own head, the same split
`_listing` reads (test: `tab_keeps_the_walk_it_completes_under`).
The finding half is `Session._below`: a query matching nothing in
the walk's directory is offered matches from beneath it,
breadth-first so near beats deep, bounded in depth/reads/rows so the
dialog answers at a keystroke's pace, with what a build writes
(`target`, `__pycache__`) not descended.  Deep rows wear their path
from the walk, so what is picked is exactly what is shown and
`_where` resolves it like any bare row; a deep directory is a step
like any other.  F129's ranking rode along: exact, prefix, substring,
directories first at each rank.


### F131. **[resolved]** An apply drops the notes it crosses

Henri, probing `nightdrive.ges` (2026-08-14, kept as
`test/sessions/F131-nightdrive-session.ges`):
"it loses sound.. particularly the pad. when I'm probing."  The scope
was the flashlight, not the fault — measured through the pad's own
scope window on the real C host, every apply behaves the same,
including a comment-only edit:

    baseline        [0.2583, 0.2814, 0.1408, 0.2868]
    after trivial   [0.0,    0.3171, 0.145,  0.2624, …]
    after re-apply  [0.0,    0.0002, 0.2776, 0.2052, …]

The swap drops the notes that are *held* across it: a resumed
performer replays no onset that lies in the past, so a note sounding
at the seam comes back gateless and stays silent until its channel's
next onset.  Bass and lead re-onset within half a beat and nobody
hears the hole; the pad holds four-beat chords behind a slow attack,
so it dies audibly and swells back — and probing is applying over and
over, which made the dying constant.  The scope itself is clean:
identity verified bit-exact offline (reference and native), and the
pad breathes through a single audition.

The fix lives in the resume: a note whose onset is before the seam
and whose off is after it is still *sounding*, and the resumed
performer (or the migration around it) must re-emit its gate — the
"answers the take gave" machinery already knows the decisions, so the
note is reconstructible; what is missing is the re-emission.  Worth
checking the static-schedule path for the same hole with long notes
while in there.

**Resolved 2026-08-14, by inheritance rather than re-emission** — the
old performer already knows everything the reconstruction would have
recomputed.  `LazyPerformer.inherit(old)` carries, per bank whose
channel layout still matches exactly: the allocator's voices with
their true onsets (`state`/`restore`), the gates and payloads the
engine is reading this instant (`values`), the releases still owed
(the off entries of `_played` keys), the key counter (so a carried
release can never name a new note), and — the second act — **the
position**, because a fresh performer seeks on its first read and a
seek releases what sounds before silently replaying a past the
resumed stream does not contain: the first cut of this fix was wiped
one block after it landed, and the dip in the measurements said so.
Verified on the diagnosing setup itself: nightdrive on the C host,
comment-only apply and scope-toggling re-apply, the pad's window
never reading silence again.  The static-schedule path never had the
hole — `value_at` is a total function of the schedule, past onsets
included.  Held by `test_a_rebuild_inherits_what_was_sounding`.


### F132. **[resolved]** A content box near the foot renders over the status bar

Henri, 2026-08-14 (`fixme.incoming.txt`): a scope's box on a line
near the bottom of the screen paints over the bar.  The slots walk
hands out bands from `top` downward and nothing clips the last band
to `text_h` — the box's panel and points are drawn wherever the slot
says, and past the text area that is the bar's ground.  The fix
belongs in one place, not two: either `View::slots` stops granting
band height past `text_h`, or every box painter clips to it — and
the slots table is the one-walk-every-reader invariant, so the walk
is where the clip should live.  Check the trouble boxes for the same
overflow while there; they share the machinery and probably the bug.

**Resolved 2026-08-14 — and the entry's own fix-shape was half
wrong.**  The layout's hang past the fold is *deliberate*
(`top_showing`: the caret's promise is its own line, and clipping
the walk would break the follow), so the clip lives in the painters:
the trouble box clamps its panel and rows to `text_h`
(`view.rs` frame_with), and the scope bands skip or shrink past the
fold (`window.rs` paint_scopes).  Both trouble and scope boxes had
the bug, as suspected.  Held by `a_box_at_the_fold_stops_at_the_fold`.

### F133. **[resolved]** `what scope` draws its page outside the window when the panel is low

Henri, 2026-08-14 (`fixme.incoming.txt`): asking `what` for `scope`
with the caret in the upper half — the panel goes low (the equator
rule) — draws the reference page past the window's bottom edge.  The
page rows ride under the list inside the panel's own frame
(`palette.rs`), and the panel placed in the lower half has less room
below the query than the page assumes; the rows need clamping to the
panel's granted box, with "…" or a shortened page rather than pixels
nobody can see.  The equator placement is right; the page's height
accounting is what has not heard of it.

**Resolved 2026-08-14: the page goes where the room is.**  Below the
panel when below holds it, above when the equator sent the panel low
— the placement rule's other half, which the page had never heard of
— and when neither side holds the whole page, as many lines as fit
with the last row counting the rest (`… N more`), the full page one
`doc/ref/` away.  Held by `a_page_stays_inside_the_window`, which
also pins the counted elision.

### F134. **[missing]** `now : Sig Float` — the current time in seconds, to the substrate

Henri, 2026-08-14 (`fixme.incoming.txt`): a substrate that wants
clock time has no signal that says it.  `elapsed` is the sample
clock's (`audio.ges`: `map (n => toFloat n / sampleRate) ticks`) and
nothing fires it on the canvas side; the canvas's own clock is one
`Tick` a frame (`gui.py` `tick`), and "a program that wants seconds
divides by it" — by a rate the program has no name for.  So an
animating substrate counts frames and guesses.  The ask is one name
meaning seconds on both sides: on the audio side `now` is `elapsed`
under the name a reader expects, on the canvas side it is the frame
count over the view's rate — the wall clock the two substrates
share, spelled once where both preludes can reach it.

### F135. **[partly resolved]** Long features work in silence — progress belongs in the statusline

Henri, 2026-08-14 (`fixme.incoming.txt`): a friend attempting a
20-minute piece made it plain — some features need progress bars,
and the statusline is where one could live.  The CLI half landed the
same day (commit `streaming with stall detection`): `audioperform
-o` wraps the control clock in `_progress` — a tty position line
rewritten in place, a stall said the moment the transcript confesses
one, a named suspicion when ten seconds of forcing produce nothing.
What remains is the UI half, and the wire for it already exists:
`session.said`'s newest sentence rides the furniture string as
`status\t…` (`session.py`), and the shell draws it every frame
(`furniture.rs`).  A long render or a stalling performer inside the
workbench should speak the same sentences `_progress` already
composes, down the same wire — no new machinery, just a second
consumer for words that exist.  The specimen that motivated all of
it: `specimens/sauna_specimen.ges`.
