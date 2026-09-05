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

Of 202 entries, **162 are resolved**.  (Those two numbers are checked by `test_citations.py`, because this file's whole discipline is that a
claim does not rot, and this sentence had rotted by twenty-five entries before anybody read it.)  What is left:

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
| F100 | resolved | A constraint naming a class that does not exist is accepted |
| F95 | fixed | The fragment admits tuples; the extractor now lays them out |
| F103 | resolved | The same file's canvas builds or fails typechecking, run to run |
| F106 | resolved | The drawn piano retriggers a held key (OS autorepeat) |
| F107 | resolved | Up/Down inside a palette argument runs the command |
| F108 | resolved | `pianoStep` inserts `50` with no trailing separator |
| F109 | resolved | Opening a file joins the previous start in the gesture loop — no cancel, late switch |
| F110 | resolved | Zoom wedge: the mirror only synced after input — tell() every poll now |
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
| F134 | resolved | `now : Sig Float` — the current time in seconds, to the substrate |
| F135 | partly resolved | Long features work in silence; the CLI has progress text, the statusline does not |
| F136 | missing | A tuple-pattern lambda picks the wrong instance, silently |
| F137 | missing | A zoom scales the band and not the picture in it |
| F140 | resolved | A render refused and the reason stayed in the terminal |
| F141 | resolved | `foo : int` is a legal signature and a certain mistake |
| F148 | resolved | The taskbar wore a sine; the front page wore the egg |
| F149 | resolved | The desktop icon installed correctly and did nothing when clicked |
| F150 | resolved | The first screen named a deleted button; the menu opened on `skip` |
| F151 | resolved | Typing reached nothing, and there was no word for it |
| F152 | resolved | A complaint with no place to land |
| F153 | resolved | The window taught the key only to people who no longer needed it |
| F154 | resolved | A driven harness saved into the repository |
| F155 | resolved | The one control was a glyph nobody could find |
| F156 | open | The audio backend says which definition, never which line |
| F157 | open | The type machinery's later stages let go of the span |
| F158 | open | A piece's complaints name a beat, never a line |
| F159 | open | The evaluator's runtime complaints carry no position |
| F176 | bug | The file chooser opens on the source tree, and a stranger reads it as a menu |
| F177 | fixed | The way back up is the top row; it is `[up]` now |
| F178 | bug | `[command]` opens unaided, then the list gives a newcomer nothing to do |
| F174 | bug | A driven run cannot tell its own window from one beside it |
| F179 | resolved | The desktop icon's absent file opens the starter, which sounds |
| F180 | resolved | `test_suite_runner.py` fails alone and passes in the full run — its own `sys.path` line now |
| F181 | bug | `seedaudit.py`'s piece paths are gestate's own, and a seed cannot say where its pieces are — the first instance was a slip the audit caught |
| F182 | resolved | `test_precommit.py` read the hook as prose, and passed with the gate neutered |
| F183 | resolved | The automatic audition shut its gate and said nothing, so a slow file read as a broken one |
| F184 | resolved | The housekeeping thread died under a test for nine days, and the suite called it *1 warning* |
| F185 | resolved | The browser gate skipped under the fence — Chrome is in `/opt`, which the fence did not bind — so its green had only ever been unfenced |
| F186 | resolved | An application's head loses its parentheses: `(x => x + 1) 2` comes back as `x => x + 1 2` |
| F187 | resolved | A lambda's and an instance member's parameters are not atoms — F46's third bullet, in the callers it did not reach |
| F188 | resolved | A `Box` pattern formats as the debugging placeholder `<PBox>`, which does not parse |
| F190 | open | The formatter is not idempotent: a second pass moves comments and deletes 27 of them |
| F191 | open | For nine sources — the prelude among them — the formatter's output does not parse |
| F192 | open | A written type loses its source position at instantiation: `_apply_subst_map` carries the span on `TFun` and not on `TApp` |
| F193 | resolved | `spec/syntax.md` did not list `do`, `internal` or `%`, which the tokenizer and the parser have |
| F194 | open | `memoryindex.py` writes nothing and exits 0 behind the fence, where `$HOME` is a tmpfs — and its own gate skips there |
| F189 | open | The leash reported itself off at session start against a file it had not touched, and it was on — not reproduced |

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

gate: `partial — the unbound `_box` is held, the per-variable temporary is
not, and nothing reaches it`.  Measured 2026-09-04 (batch 13), 484 tests in 23
Datafun-facing files.  Putting the defect back — `x`/`dx` projected out of an
unbound `_box`, the compiled binding discarded — takes **38 red**, of which 37
are real (`test_complaints.py::test_the_page_is_not_behind_the_source` is a
line-number canary, see below); `test_relations.py`'s transitive-closure
family and `test_datafun_fix.py`'s fix spellings are the ones that name the
failure.  The second half of the repair — `tmp = f"_box_{var}"`, so nested
unboxes do not shadow — is **484 green** with the shared `_box` put back, and
a probe raising whenever an unbox is compiled inside another one never fired
across 471 tests.  So the green is a tautology, not a gap: **no program in
this tree nests unboxes at all.**  Weakest point: a test that nests them
would have to be written before there is anything to gate, and it would be a
test of the compiler rather than of any program anybody writes.

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

Fixed in the implementation: the test is `dx ⊑ x` via a generated
`subset_L`.  ~~Fixed in both spec and implementation~~ — **corrected
2026-09-04 (batch 13): the spec half had never landed.**  `spec/data.md`
§I.5 still prescribed `eqL dx' bottomL`, and `errata.md` D2, marked
*resolved*, still ended with the sentence *"`spec/data.md` §I.5 should be
amended to the thesis's test"*.  Amended the same day; the original §I.5
text is kept below the amendment.  See `errata.md` D2 — the first expressible Datalog
query hung under the old one.  The original text:

`seminaive.py:368-376` tests `eq_Set_Int dx' bottom_Set_Int`, faithfully
implementing `spec/data.md` §I.5 — but §I.5 itself disagrees with the thesis,
which tests `dx ⊑ x`.  See `spec/errata.md` D2; the fix belongs in the spec
first, then here (and `helpers.py` needs a generated `subset_*`/`leq_*`
alongside `eq_*`).

gate: `test/test_datafun_fix.py::test_semifix_stabilises_on_containment_not_emptiness`
for the term `semifixL` builds, and the transitive-closure family for what it
computes.  Measured 2026-09-04 (batch 13): stopping on `dx ⊑ ⊥` instead of
`dx ⊑ x` — §I.5's test, reconstructed through the same helper so no arity
changes — is **6 red**, including `test_transitive_closure_of_a_path`; with
change minimisation removed as well, the loop as it stood when the first
Datalog query hung, **10 red**, and `test_a_datalog_fixed_point_terminates` is
one of them.  The `subset_` prefix half is held separately:
`test_transform_scope.py::test_a_generated_helper_is_not_a_user_name_at_any_type`
is the single red when `subset_` is dropped from `_HELPER_PREFIXES`.
Weakest point: **the entry's claim that the spec was fixed was false until
today** — `spec/data.md` §I.5 still prescribed `eqL dx' bottomL` — and the
gate written for that half
(`test_datafun_fix.py::test_the_spec_prescribes_the_test_the_generator_builds`)
holds the two texts against each other by their words, which is a citation check and not a proof that the
implementation follows the spec.

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

gate: `partial` — two of the three sites are held hard and the third is bare.
Measured 2026-09-03 by mutation, against 429 tests in 20 Datafun-facing files.
The ϕ/δ side: `_suffix` hard-wired back to `Set_Int`, **14 red**, every
transitive-closure test among them.  `make_semifix_helpers` pinned to one
suffix, **56 red**.  Bare: **`_is_user_sc` matching helper names against a
hardcoded `Set_Int` list instead of by prefix — 429 green**, and it is not a
dead line, a probe raising on entry took 5 of them down.
`test/test_transform_scope.py::test_a_generated_helper_is_not_a_user_name_at_any_type`
names it now, red on that mutation alone.  Weakest point: that gate is a unit
test, because `transform` passes the set it is generating pairs for and
`_is_user_sc` is only the fallback for a direct call to `phi`/`delta` — no
*program* in the tree reaches it with a helper at a type other than `Set Int`.

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

Fixed: `gestate/bottoms.py` is the pass, and `pipeline.py` runs it over the
supercombinators after ϕ/δ.  `spec/errata.md` D3 is marked **resolved**.
*The paragraph below was still the original diagnosis on 2026-09-03, so the
entry read as open while the pass had been in the tree for months — the same
shape as F43, corrected in place and dated rather than deleted.*  The original
diagnosis:

See `spec/errata.md` D3 — this is the pass the asymptotic speedup depends on.
It is absent from the spec *and* the implementation, so `spec/data.md` §I.7's
proposed Θ(n²) test would fail today.  Listing it here as well because
`_desugar_datafun` (`pipeline.py:183`) is the natural place for it.

gate: `test/test_seminaive_opt.py::test_the_compiled_query_pays_the_propagated_price`,
written 2026-09-03 and red on the mutation alone.  **It is the batch's
finding.**  Every rewrite of fig. 4.1 was tested on a hand-built term and
nothing asked whether the pipeline *calls* the pass: `propagate_bottoms(scs)`
taken out of `pipeline.py` left **429 of 429 green**, while a probe raising
whenever the pass changed anything took **52 of them** down.  A pass that
demonstrably fires, with no observer — F17's shape, arriving at a whole
compiler stage instead of at a check.  The gate is a G-machine step count:
8,966 with the pass, 12,130 without.  Weakest point: a step count drifts as
the compiler changes, so the bound is the thing most likely to be raised past
the defect one day rather than re-measured.

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

gate: `none — nothing can`.  Measured 2026-09-03 by putting a stale copy back
— `generate_helpers` beside `generate_all_helpers`, without the product branch
or `diff_`, which is the shape a copy diverges into — and **429 of 429 green**,
as it must be: nothing calls it, so no execution of the tree can distinguish a
module that has it from one that does not.  The only instrument that notices at
all is `tools/covercount.py`, and what it notices is a percentage:
`gestate/helpers.py` reads 51% without the copy and 48% with it, in a page that
is regenerated by hand and returns 0 by design.  What it would take is a
coverage floor over `gestate/`, or a dead-code gate — and `card:dangling-names.md`
is why a noisy structural detector is refused here: a check that accuses honest
code four times in five is a check that gets muted.  Weakest point: the
*specific* defect — an edit landing in the wrong copy — has no observer even
then; a coverage floor would catch the copy, not the edit.

### F13. **[resolved]** `diffL` (change minimization) — see §7's D3/D4 entry

Fixed: `helpers._gen_diff` generates `diff_X` per semilattice, and
`seminaive.make_semifix_helpers` subtracts with it — `dx' = (f' x dx) \ x'`,
the thesis §4.3 loop.  `spec/errata.md` D4 is marked **implemented, benefit
unmeasured**.  *Corrected in place 2026-09-03, dated: the paragraph below is
the original diagnosis and had stood as the whole entry, so this one read as
open too.*  The original diagnosis:

Not spec'd either — see `spec/errata.md` D4.  Named here because `helpers.py`
is where it would be generated, next to `eq_`/`union_`/`bottom_`/`join_`.

gate: `test/test_seminaive_opt.py::test_the_loop_minimizes_the_next_delta` and
`test/test_datafun_fix.py::test_the_next_delta_is_minimized_against_the_new_accumulator`
— gated all along and never said so, the fifth of that shape in this sweep.
Measured 2026-09-03: the `diff_` dropped from `semifixL`'s recursive call,
**2 red** of 429, both of them.  Weakest point, and D4 says it in its own
heading: both are *structural*, reading the generated lambda.  **No program
went red** — the answers do not change and the loop still terminates, because
the stop test is `dx ⊑ x` rather than `dx = ⊥`.  The 745s-against-1.5s the
minimizer exists for is held by nothing, which is what *benefit unmeasured*
means, and `spec/data.md` §I.7's Θ(n²) proposal is where a gate for it would
come from.

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

gate: `test/test_frp.py::test_ticked_has_no_case_for_a_delay_node` and
`::test_a_signal_whose_tail_is_a_delay_does_not_fire`, written 2026-09-03,
each red on its own half.  Both halves were bare before them: the `TAG_DELAY`
case put back, and the `gfix cycle` re-mark put back, **396 tests across 16
files, zero red, both** — and the reason is worth more than the number.  Two
probes *raising* on entry were also 396 green, so nothing in the tree ever puts
a delay node where either branch looks, and the greens above were tautologies.
What made that safe is `::test_delay_is_universal_and_a_tail_is_existential`
(`spec/errata.md` R3): with `FaL`/`ExL` distinct the type checker rejects the
only program that wanted the case.  **That is a gate on the premise, not on the
repair** — put the case back and it still passes.  Weakest point: the two new
tests are unit assertions on `ticked` and `_update_one` with a hand-built node,
which is the shape batch 11 flagged at F17; there is no program-level gate
here, and by the premise above there cannot be one.  And, per batch 11: this
repair predates `b049e0c`, so both mutations are **reconstructions from this
entry's prose**.

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

gate: `test/test_frp.py::test_ticked_cl_invariant_is_checked_every_step` — for
the *comparison*, and **partial** is the verdict.  It holds that half hard:
`cl` made to answer the empty clock for everything takes **29 of 49** in that
file and 69 of 281 across the reactive set, and removing the driver's check
outright takes exactly 1.  **The snapshot that feeds the check was held by
nothing.**  `reactive_step` takes `{sig: cl(sig.tail) …}` before the sweep; stop
taking it and `sig in reactive.clocks` is never true, the invariant silently
stops being asked, and 542 tests across 16 files stay green — including the
test above, which injects `reactive.clocks` by hand and calls `_update_one`
directly, so it never walks the snapshot at all.
`::test_the_sweep_snapshots_a_clock_for_every_signal_it_is_about_to_update`
written 2026-09-02 for that half.  Weakest point: the new gate spies on
`_update_one` and asserts a clock was taken, not that its *contents* are right
— `cl`'s answers are still held only by the comparison one raise away, and by
nothing at all if that raise is ever softened to a warning.

### F18. **[resolved]** No now/earlier check on `head`

Fixed: `NSig.current` is the ✓ frontier as a per-cell mark.  `SigHead`
raises on a signal the sweep has not reached, and `ticked`/`advance` do
the same for `watch l`/`tail l`, whose fig. 10 rules are also stated
against the new heap.  A scheduler-ordering bug is now an error rather
than a stale read.  See `errata.md` R8.

gate: `test/test_frp.py::test_head_of_an_earlier_heap_signal_is_stuck` — for the
`head` half only, and **partial** is the verdict.  `ticked` asks the same fig. 10
question of `watch l` and `tail l` through `_require_current`, and deleting that
check left **542 tests across 16 files green** (2026-09-02, by mutation).
`::test_watch_of_an_earlier_heap_signal_is_refused` and its `tail` twin were
written the same day for the bare half.  Weakest point: all three set
`current = False` by hand, because no program in the tree reaches an
out-of-turn read — so what is held is that the check fires, not that the
frontier is maintained correctly.

### F19. **[resolved]** Channel context is never tracked

Fixed: `GmState.chans` is Δ, exposed as `GmReactive.chans`; `NewChan`
extends it with the element type inference recorded on the `EChan` node,
and `advance`'s sub-evaluation shares the dict so a channel minted
mid-sweep registers.  `react` rejects an input on a channel that was never
allocated.  See `errata.md` R11.

gate: `test/test_frp.py::test_input_on_an_unknown_channel_is_rejected` for the
refusal, and `::test_channel_context_records_allocated_channels`,
`::test_unforced_channel_is_not_in_the_context` and
`::test_channel_element_type_is_recorded` for Δ itself.  Measured 2026-09-02 by
mutation: dropping the `k not in chans` refusal takes exactly **1** red;
`NewChan` not writing `s.chans[cid]` takes **25 of 49** in that file and 63 of
281 across the reactive set.  **Gated all along, and this entry never said so**
— the fourth of that shape in this sweep.  Weakest point: none of the four
names F19, so the citation resolves in one direction only.

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
the machine wedged.  ~~Dead code today (F14)~~ but it is the one place the
scheduler re-enters the evaluator, so it should match the spec before it is
reachable.

**"Dead code today" was true when it was written and stopped being true when
F14 was resolved** — corrected in place 2026-09-02, dated, and left struck
rather than deleted so the reason this entry went ungated for so long is still
readable.  `map`, `mkSig`, `sample`, `switch` and `filter` all reach
`TAG_EXISTS5` now: made `_apply` raise on entry and **61 of 281** reactive
tests go red.  It is one of the hottest paths in the reactive suite.

gate: `test/test_frp.py::test_an_error_in_the_sub_evaluation_does_not_wedge_the_machine`,
**written 2026-09-02** — the property was held by nothing, and the reason it had
gone unheld had expired (above).  It injects a `GmError` into the sub-evaluation
and requires `code`, `stack` and `dump` to come back exactly as they were.
Reaching it cost the disagreement that is now **F195**: the *G-machine* survives
the failure and the *sweep* does not.  Weakest point: the in-place `_apply` that
this was measured against is a reconstruction from the prose (the repair
predates `b049e0c`), and it reddens 17 of 53 — so most of that red is the
reconstruction computing wrong answers, not this property being asserted.  The
gate above is the narrow claim, and it is the one that is actually held.

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

gate: `none — not yet built`.  Measured 2026-09-02 by mutation, the repair's
four sites put back separately: `ticked`'s operand dereferences, `advance`'s,
either function's dereference of its own node, and `MkDelayAp`'s chase of the
indirection a `gfix` binder arrives as.  **542 tests across 16 files, zero red,
all four** — including `test_surface_guarded_recursion_runs`, which is the
`gfix` case the entry was written for.  Weakest point, and it is the whole
entry: the repair predates `b049e0c`, so git cannot return the original code
and every mutation above is a **reconstruction from this entry's own prose**.
A green means no test sees that reconstruction, not that the original defect
would have escaped.

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

gate: `test/test_syntax_spec.py::test_the_pages_reserved_words_are_the_tokenizers`,
written 2026-09-01 — it pulls the list off the page and compares it with
`tokenize._RESERVED`, both directions.  **Measured the same day**: `Box` struck
from the page's list, red; `deriving` struck, red.  Before it, nothing read the
page at all: the whole repair was an edit to `spec/syntax.md` and the language
suite cannot see one.  Weakest: it holds the page against the *tokenizer* and
not against the grammar, so a word reserved and then never given a meaning
still passes.  The reverse direction carried a baseline of two — `do` and
`internal`, **F193**, the same defect standing again — and it was emptied the
same afternoon at Henri's word.

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

gate: `test/test_syntax_spec.py::test_the_pages_default_fixities_are_the_parsers`
for the page's half and
`test/test_music_syntax.py::test_the_function_arrow_cannot_be_given_a_fixity`
for `_UNOVERRIDABLE` — the second existed already and had never named this
entry.  **Measured 2026-09-01**: the `..` row struck from the page, red; the
parser's `..` moved from `infixl 7` to `infixl 9`, red; the un-overridable
check replaced by `if False`, one red in `test_music_syntax.py`.

Weakest, and it is worth stating plainly: **the binding power itself is not
held by any behaviour.**  Dropping `"..": ("L", 7)` altogether leaves 780 of
780 language tests green, because `..` exists only in *type* space — `4 .. 30`
in an expression is an unknown global — and type space has no operator between
`->` at 1 and the `("L", 9)` fallback, so 7 and 9 parse every program in the
tree identically.  What the gate holds is that the page and the parser *agree*,
not that 7 is the right number.  Nothing in the tree could tell.

*And this entry's `Fixed.` paragraph is shared verbatim with F23 and F24*: all
three name all three repairs, so each reads as larger than it is.  Noted
2026-09-01 rather than rewritten — the repairs are real and correctly
described, only misattributed across the three entries.

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

gate: `test/test_frp.py::test_signal_pattern_head_can_be_matched` — the entry's
own occasion, in parameter position — and
`test/test_match.py::test_constructor_inside_cons_pattern`, both named for this
entry 2026-08-31.  **Measured the same day**: the constructor branch's
`_parse_pat_atom` put back to `_parse_pat`, 4 of 789 red.  Weakest: all four
fail as *non-exhaustive*, not as a wrong answer — what they hold is that the
greedy parse is refused somewhere downstream, so a mis-parse that stayed
exhaustive would pass them.  Nothing in the tree compares the *parse* against
what was written, which is what would hold this directly.

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

gate: three tests written 2026-08-31 in `test/fmt/test_format.py`, one per
bullet — `::test_an_operand_that_runs_to_the_end_keeps_its_parentheses`,
`::test_an_infix_operand_is_parenthesised_by_associativity`,
`::test_a_compound_pattern_in_juxtaposed_position_keeps_its_parentheses`.
**Measured 2026-08-31**, each repair put back on its own: the `_TRAILING`
guard dropped from `_fmt_infix`'s operand, the associativity term dropped from
its precedence test, and `_fmt_pat`'s `atom` flag forced false — **789 of 789
green every time**.  All three halves were held by nothing, and idempotency
cannot hold them: `x => x + 1 + 2` formats to itself, so the wrong output is
stable.  The gates instead feed the formatter its own output and ask for it
back verbatim.  Weakest, and it is not small: they hold three shapes, not the
promise.  The promise is false today in two more places — **F186** and
**F187**, both found while measuring this one.

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

gate: `test/test_types.py::test_a_self_binding_is_dropped`,
`::test_composing_opposite_bindings_terminates` and
`::test_a_variable_cycle_resolves_to_a_representative` — all three written for
this repair, none of them naming it until 2026-08-31.  **Measured the same
day**, one mutation per half: the identity filter dropped from `Subst.extend`,
`Unifier.extend` and `compose`, 2 red; `_apply_var` returned to a recursive
chase, 1 red as a `RecursionError`; both together, 4 red with the composition
test among them.  Weakest: every one of those reds is a unit test on
`Subst`/`Unifier` — **no program went red under either mutation**, so the path
the defect actually arrived on, inference over a program F45's fix made
writable, is held by nothing.

### F48. **[resolved]** A dictionary slot for an undefined method held `0`

`elaborate` filled a missing method's slot with `ENum(0)`, reasoning that
"a well-typed program never projects the slot".  It does: the synthetic
`Num (Cyclic n)` instance defined only `fromInteger`, so `+`/`-`/`*`
projected the placeholder — and `Unwind` on a number ignores the spine,
so `x + y` evaluated to `0` at every `Cyclic` type.  The slot now holds an
undefined global, which fails if projected and is inert otherwise, and
the synthetic instance defines all four methods.

gate: `test/test_arith.py::test_cyclic_arithmetic_wraps` for the instance
half, and `test/test_dictionaries.py::test_an_undefined_method_slot_fails_when_projected`
— written 2026-08-28 — for the placeholder.  **Measured 2026-08-28, and the
two halves are held separately.**  `+`/`-`/`*` dropped from
`_make_num_instance` again: 40 of 316 in the targeted set red, the
`Cyclic` test among them.  `ENum(0)` put back in the slot: **316 green** —
nothing in the tree projected an undefined slot any more, because the
synthetic instance defines all four methods, so the repair this entry is
named for was held by nothing.  The new test is a class of two methods,
an instance defining one, and `main = second2 5`: `0` with the
placeholder back, `unknown global '__undefined_Two_second2__'` with the
repair.

### F49. **[resolved]** `Cyclic n` arithmetic did not wrap

Only `fromInteger` reduced mod `n`; `+`/`-`/`*` (once they existed at all,
F48) would have let a value escape its own type.  That matters beyond
arithmetic: the fixtype rule takes `Cyclic n` for a finite type, and a
`Cyclic 4` holding 6 would make `fix` promise a termination it could not
deliver.  `Bounded lo hi` still does not confine its values
(`main : 0 .. 3; main = 7` gives 7), so it is deliberately *not* counted
as a finite eqtype until its `fromInteger` clamps or wraps.

gate: `test/test_arith.py::test_cyclic_arithmetic_wraps`.  **Measured
2026-08-28**: the wrap dropped from `+`/`-`/`*` in `_num_body` and 5 of
316 in the targeted set red — this test, and four fixed-point tests that
converge only because `Cyclic n` is finite, which is the entry's own
second point.  The `Bounded` half above is still open and the gate does
not claim it.

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

gate: `none — not yet built`.  **Measured 2026-09-01**, batch 10: `TApp(fn,
arg, t.span)` put back to `TApp(fn, arg)` and **780 of 780** language tests
green.  Two things make it invisible.  `apply` returns `t` itself when neither
part changed, so the repaired line runs only when a variable was actually
bound; and the types that reach it built by inference never had a span to
lose.  Weakest, and it is the whole verdict: **no program could be constructed
in which the repaired line is the one that decides a message** — with the
severance at `_apply_subst_map` repaired as well (**F192**, found here), three
probes printed identical positions with the defect back and without it.  So
*ungated* is measured; *gateable and cheap* is not, and a gate would have to
start by finding the case.

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

gate: `test/test_frp.py::test_signal_interface_typechecks` for `ExL` — it
writes `nxt : ExL (Sig Int)` and had never named this entry — and
`test/test_frp.py::test_the_two_later_modalities_are_writable_in_a_signature`,
written 2026-09-01, for `FaL`.

**Measured the same day**, each constructor struck from
`kindcheck._BUILTIN_KINDS` on its own: `ExL` → **136 of 780** language tests
red, because `gestate/signal.ges` opens with `mkSig : ExL a -> ExL (Sig a)` and
every reactive program is compiled through it.  `FaL` → **780 green**.  The
kind table is consulted only for a type somebody *wrote*, and inference builds
its own `FaL` for every `delay`, so the constructor was exercised constantly
and named nowhere.  The new test writes one: `later : Int -> FaL Int`, red with
a kind error under the mutation.

Weakest: the entry also claims `Maybe` and `Sync`, and
`::test_maybe_and_sync_are_reserved` is about a *name clash* in
`declarations.py`, not about the kind table — so those two are held against
being shadowed and not against being deleted.  Neither was mutated.

### F40. **[resolved]** `journal.md` Part I's flow diagram was stale

It had ϕ/δ *after* Datafun desugaring, which `spec/data.md` §0 forbids — ϕ/δ
works on `EFix`/`EFor` nodes and desugaring destroys them.  The diagram is
now rewritten against the real `pipeline.py`: it had also been missing the
exhaustiveness, monotone, subgrammar, helper-generation, change-structure
and ⊥-propagation stages entirely.  The three places where order is
load-bearing are stated under it, so the next drift is visible rather than
silent.

gate: `none — nothing can`, and the reason is new.  **Measured 2026-09-01**:
the diagram's ϕ/δ line and its Datafun-desugar line swapped — this entry's own
defect, put back verbatim, line count unchanged — and **298 of 298** doc and
pipeline tests green.  The only thing in the tree that notices the file at all
is its *length*: delete a line rather than move one and two gates go red,
because the archive's line count is quoted in `journal.md`'s index row and in
`doc/method.md`.

**Why *nothing can* rather than *not yet built*.**  The diagram was in
`journal.md` Part I; the rotation of 2026-09-01 moved it into
`journal/2026-08.md`, which is append-only and never edited (`spec/rules.md`
§"Archive, don't airbrush").  A gate holding it against `pipeline.py` would be
**red the day it was written** — `_analyse` runs `envexpand.expand` and
`specialise`, and the diagram has neither, so it has drifted again since this
entry closed it — and it could never be made green, because the file may not be
corrected.  The claim outlived the file's editability.

Weakest: the *live* picture is `spec/data.md` §0, a gate there is possible, and
this entry does not name it.  §0 omits the same two stages and may be right to
— it is a design-level pipeline, not a module list — so whether it is meant to
be exhaustive is a question for the spec and not one a measurement settles.

### F41. **[resolved]** A default `Set Int` is injected when the program mentions no set type

Fixed: the default is now reached only when the program *does* use a
Datafun form but no set type is visible in a signature — the residue of
`journal.md` Part I §17, which is where it belongs.  A program with
no Datafun form skips the whole block.

gate: `test/test_monomorphization.py::test_a_program_with_no_datafun_form_gets_no_set_helpers`
— written 2026-08-31.  **Measured the same day**: `_uses_datafun(scs)`
replaced by `if True` and **789 of 789 green** in the targeted language set,
so the guard was held by nothing.  The injection is visible only in what the
compiler emitted — a program with no set anywhere went from 117 globals to
130, eleven of them the `Set Int` helper family — which is what the new test
reads.  Weakest: it reads the *names*, not the program, so a guard that
skipped helper generation while still running the ϕ/δ pass would pass it.

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

**The paragraph above is the report, not the state** — *corrected 2026-08-31,
during the sweep, where the entry read `[resolved]` and its body described an
open defect.*  `case x of y -> y` runs today: `gestate/match.py`'s matrix
compiler has a variable rule, and the default arm `CaseJump` lacked is the
`default` expression threaded through it.

gate: `test/test_match.py::test_variable_catchall_alternative` and
`::test_catchall_binds_the_scrutinee`, both named for this entry 2026-08-31.
**Measured the same day** by making the match compiler refuse a variable
alternative under `where="case"`: 361 of 789 red, because the desugarer writes
that form itself for tuples, projections and aliases — so this one cannot come
back quietly whatever is named.  Weakest: both tests put the variable *after*
a constructor alternative, and the entry's own example — the sole bare
variable — is held only by the internal desugarings that happen to use it.

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

gate: `test/test_datafun_sugar.py::test_transitive_closure_with_every_sugar`
— the tuple pattern `(x, y) in r` the entry names, inside a `fix`.
**Measured 2026-08-28**: the `let` put back to `let x = δe in δf` and 12
of 316 in the targeted set red — this test, five closures in
`test_relations.py`, five in `test_comprehensions.py`, and
`test_manual.py`'s product fixpoint.  The entry said nothing exercised the
path when it was found; the comprehension sugar that landed after it
exercises nothing else.

### F52. **[resolved]** A block inside a `class`/`instance` body, or inside a `case` alternative, ended the enclosing block

`_parse_case` leaves its closing `DEDENT` for the caller — at the top level
the application-parsing loop needs to see it or `case … of …` swallows the
next declaration as an argument.  Inside a `class`/`instance` body that
same `DEDENT` read as the end of the *body*, and inside a `case`
alternative as the end of the *match*: every member or alternative after a
multi-line one silently moved out.  `Parser._close_inner_blocks` counts
what the member opened and consumes exactly those.

gate: `test/test_dictionaries.py::test_a_multi_line_member_does_not_end_the_instance_body`
and `::test_a_multi_line_alternative_does_not_end_the_match`, written
2026-08-28, parse only — and the prelude, hard.  **Measured 2026-08-28**:
`_close_inner_blocks` made a no-op and 233 of 316 in the targeted set red,
because `Functor List` at `prelude.ges:39` is a multi-line member and
nothing after it parses.  The F77 shape again: held by the prelude, named
by nothing until today.  The two new tests are red on the mutation alone,
without the prelude.

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

gate: `test/test_strings.py` and `test/test_deriving.py` — the two files,
26 and 19 tests, each written for this entry's landing and neither naming
it until today.  **Measured 2026-08-28**, one mutation for each of the two
load-bearing bullets: the `String` alias dropped from `declarations.py`
and 217 of 316 in the targeted set red, all 26 of `test_strings.py` among
them (the prelude reads `String`); `_with_derived` bypassed and 17 red,
all of them in `test_deriving.py`.  The *Not done* paragraph above is
still not done, and the gate does not claim it.

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

gate: `test/test_strings.py::test_an_ambiguous_variable_defaults_across_all_its_constraints`.
**Measured 2026-08-27**: `_default_ambiguous_vars` left out of
`infer_program` and `show 42` renders `'*'` again — this entry's own
symptom — 13 of 189 in the targeted set red, this test among them.  The
half marked *still open* above is still open, and a gate for the repair
does not claim it.

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

gate: `test/test_strings.py::test_a_signature_stays_polymorphic_across_uses`
— the entry's own program, `append [1, 2] [3, 4]` beside the prelude's
`show`.  **Measured 2026-08-27, and the mechanism is not the one this
entry describes.**  The skip in the environment update, dropped on its
own: 189 green.  Signed supercombinators made monomorphic instead of
quantified — the only way the defect comes back — 25 of `test_strings.py`'s
26 red, this test among them, and the same 25 with the skip kept.  So the
property is held by the quantification F36's rigid variables brought, and
the skip holds nothing on its own; its comment in `infer.py` says so now.

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

gate: `test/test_syntax_spec.py::test_the_constrained_adt_example_compiles`
— written 2026-08-27, reading the example out of `spec/syntax.md` and
compiling it, the way `test_manual.py` holds the manual.  **Measured
2026-08-27**: the page's old line put back and the test is red with this
entry's own `KindError: Unknown type constructor: a`; nothing else in the
tree reads the page's code.  The other half of the entry — the existential
the kind checker refuses uniformly — is F35's and is not a repair.

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

gate: `test/test_music_syntax.py::test_an_operator_may_be_defined_at_top_level`
— written 2026-08-27, since nothing named the form — and the prelude,
hard: `(@)` at `prelude.ges:20` is the first top-level operator every
program reads.  **Measured 2026-08-27**: the parenthesized-operator branch
removed from `_parse_top_item` — the defect exactly — and a bare
`main = 1` stops parsing at the prelude, 155 of 188 in the targeted set
red; the new test is red on its own, parse only, no prelude.  The file
this entry names tested `++`'s fixity and not the declaration form, so
this is the F77 shape: held by the prelude, named by nothing until today.

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

gate: `none — nothing can`, today.  **Measured 2026-08-27**: the two tags
dropped from the `add_primitives` call in `pipeline.py` — the defect
exactly — and 188 of the targeted set stay green; a program declaring
`Color := Red | Green | Blue` with a guard evaluates right with the defect
back, because in it `Nil` is 0, `Cons` is 1 and `Red` is 6.  The entry's
premise has inverted since it was written: the four builtin constructors
hold fixed tags (`gmachine.py`'s `TAG_NIL` … `TAG_TRUE`, 0–3) and user
constructors are numbered *after* them, so no program can push `Nil`/`Cons`
off 0 and 1, and a hardcoded 0/1 would be right today.  The repair stays —
the primitive still takes the real tags — and the defect can only return
by two changes at once, the numbering and the hardcoding.  When the
numbering moves, a unit test handing `add_primitives` tags off 0/1 is the
gate; a test written for it today was removed rather than kept as one that
cannot go red.

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

gate: `test/test_examples.py::test_the_typecheck_cli_accepts_every_non_music_example`,
and it holds both defects.  **Measured 2026-08-26**: `check_scs` put back
in `_find_errors` — red; the `_is_given` filter dropped, so the constraints
an SC's own context grants are solved too — red.  One test, two defects,
each on its own.

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

gate: `test/test_implicits.py`, and each of the three halves separately.
**Measured 2026-08-26** by putting each back, against the file plus
`test_manual.py`'s §4 tests (49): propagation — a reference to a needing
definition carrying nothing — reddens 12, first
`test_it_reaches_a_fixed_point_through_a_chain`; the binder analysis —
every `VWord` read as a global — 20, first
`test_a_parameter_shadows_a_supercombinator_of_the_same_name`, and the
explicit `VCase` walk dropped, 35, with
`test_a_case_alternative_binds_its_pattern_variables` among them; the
signature left unextended, 20, with
`test_a_signature_does_not_mention_the_implicit` and
`test_the_declaration_gives_the_parameter_its_type` named.

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

gate: `test/test_layout.py::test_a_comment_between_case_alternatives_is_trivia`,
written 2026-08-26 beside F70 and F72, and the finding is the reason it was
written.  **Measured** the same day: with the `case` loop back on
`_skip_nl`, exactly one more file stopped parsing — of every `.ges` under
`gestate/`, `examples/` and `test/` that parses at all — and it was
`gestate/music.ges`, which has carried a comment between `>>=`'s
alternatives since F76.  So the defect was held by the prelude, three
tests deep in `test_manual.py`, and nothing in the tree said that comment
was a gate; a tidy-up of it would have removed the gate silently.  The
named test goes red on the mutation alone (`expected a pattern, got ' a
comment about…'`).

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

gate: `test/test_manual.py::test_manual_s9_the_scaling_factor_does_not_swallow_what_follows`,
with `test/test_music_syntax.py::test_two_scaled_groups_in_a_row` and
`nocturne.ges` beside it.  **Measured 2026-08-26** with the defect isolated:
`|*` and `|/` left at 6 and given a *right* precedence of 3 through
`RIGHT_PREC` — the factor loose again, the left side untouched — and the
three go red, the first on `a ++ b |* 2 ++ c`.  The naive mutation, both
sides back to 3, also puts F83's defect back and took six down, which is
why it had to be isolated.  **The repair this entry describes is no longer
the one in the tree**: F83 took the left side to 6 as well, so both
operators are plain `infixl 6` and `RIGHT_PREC` is an empty table — kept,
because `infixl l r` is still a declaration a program may write.  Its
docstring said the two operators lived there until today.

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

gate: `test/test_manual.py::test_manual_s3_a_prefix_operator_may_stand_as_an_argument`,
and `examples/music/nocturne.ges` through
`test/test_examples.py::test_nocturne_is_a_full_arrangement_on_the_grid`.
**Measured 2026-08-26**: `_starts_prefix_arg` made to answer `False` — the
defect exactly — and both go red, 2 of 61 in the targeted set.  The manual
test is the §9 entry turned inside out, which is what this entry says it
would be.

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

gate: `partial` — `test/test_audio.py::test_the_phase_carries_across_a_frequency_change`
holds the property, and `examples/audio/blip.ges` is not what it holds
it on.  The backend itself is pinned broadly by the same file: the
sample count, the range, the sample rate being the renderer's business,
the roster of audio examples, stereo, and clamping rather than
normalising.

**The gate this entry carried until 2026-08-25 did not fire, and the
finding is worth more than the repair.**
`test_the_phase_is_continuous_across_a_note_change` named the property
and had been green since the backend was built.  **Measured**:
`stepVoice` changed to compute the phase from `n` — the exact defect —
and the test passed.  Its statistic is 0.2226 either way, because the
largest neighbouring step in that program is the **sawtooth's own
wrap**, not the seam; the two renders do differ (max |diff| 0.49).  And
the example could never have gated it: `envAt` is a *cubed* decay, so
the level just before a note boundary is 0.0000 and the phase change
happens where there is nothing to hear.  *A first attempt at this line
proposed measuring the note boundary instead, which the measurement
refuted — the wrong version is quoted in `journal.md`'s kaizen of the
day rather than quietly dropped.*

**The repair, the same day, at Henri's ask** — *"make the test
discriminate with an inline sustained fixture"*: a sine at a constant
level changing 233 Hz → 317 Hz once, rendered inline the way
`test_synthlib.py` renders its sources.  The oracle is the sine's own
arithmetic rather than a chosen number — neighbouring samples cannot
differ by more than `2*pi*f/rate` — and it was broken on purpose before
it was trusted: the defect put into the fixture measures **1.8159**
against a ceiling of **0.3735**, and correct it measures **0.2483**,
which is `2*pi*317/8000` to four figures.  The fixture's parameters are
load-bearing and the test says why: a saw's wrap swamps the seam, an
envelope hides it, and a boundary landing on whole cycles of both
frequencies makes the defect genuinely invisible — the first draft did
exactly that and measured 0.1175 broken against 0.1177 correct.

**Still `partial`, and this is the bare half**: the new test pins the
*technique*.  `blip.ges` could be changed to compute its phase from `n`
and nothing would go red, because the example silences its own note
ends.

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

gate: the example roster, and the behaviour tests behind it.
`test/test_gui.py::test_every_gui_example_is_exercised_here` refuses a
GUI example that is not in the file, and five tests actually run
`chain.ges` — its length, its head following, its tail lagging, its
taper, and a pointer that moves without a tick.  `drums.ges` is
extracted by `test/test_audiograph.py` and performed by
`test/test_examples.py`.  **Measured 2026-08-25**: `examples/gui/chain.ges`
moved out of the tree → 6 red in `test_gui.py`; restored → green.

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

gate: `test/test_audiofragment.py::test_a_polymorphic_parameter_settles_before_the_graph`.
**Measured 2026-08-25**: `_former`'s `of()` made to return `""` again —
the threading this entry replaced — → red with this entry's own error,
*"the element type of this `__Functor_Sig_map__` could not be
determined"*; restored → green.  `test_a_nested_former_with_a_lambda_step_is_typed`
pins the other half, the case that must still raise.

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

### F100. **[resolved]** A constraint naming a class that does not exist is accepted

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

**Resolved 2026-08-18**, and that is what it says, with the span of the
constraint so the workbench draws it under the signature.
`kindcheck.check_class_names` runs from `_kind_check_program`, which is
the first point where every class is known — a signature is desugared
while the program is still being built, and the class table is not
finished until it is.

**And the suggestion is narrow on purpose.**  A wrong one is worse than
none here, because taking it makes the typo permanent — which is this
defect's whole complaint about the old message.  Two rules: a case slip
is an *exact* match (`FromMidi` → `FromMIDI`, which edit distance rates
0.62 and no usable threshold would ever catch), and otherwise a cutoff
that admits `Shwo` → `Show` at 0.75 and refuses `Monoid` → `Monad` at
0.73.  The line is drawn where the examples are.

Signatures and superclasses only: **instances were already checked**,
by `coherence`, which says *"Instance for unknown class 'Shwo'"* with
the head's span for both the head and its context.  A second opinion
would be a second message about one mistake, and which fired would
depend on which pass ran first.

`ClassInfo` gained a `span` so the superclass complaint has a line too.
Six tests in `test/test_contexts.py`.

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

gate: `test/test_panel_fixtures.py::test_the_channels_and_bridge_the_rust_suite_carries_are_todays`.
**Measured 2026-08-25**: the `n not in generated` subtraction dropped
from `gui._channel_names` → red, and the failure names the defect
exactly — *"Left contains 28 more items, first extra item:
'lampsChan0f0'"*; restored → green.

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

gate: `none — not yet built`.  The repair is the
`XkbSetDetectableAutoRepeat` call on **baseview's own display**
(`shell/editor/src/window.rs`), and nothing exercises it: **measured
2026-08-25**, the call disabled with `if false` → `cargo test
--workspace` stayed green at 82.  The two guards this entry names *are*
gated — `test/test_audiokeyboard.py::test_auto_repeat_does_not_retrigger_a_held_key`
holds the model's refusal of a repeat — but both were already standing
when the piano retriggered, so they gate the part that was never broken.
What exists for the repair itself is `GESTATE_EDITOR_KEYS=1` printing
`[keys] detectable autorepeat: on`, and that is a **reading, not a
gate** (the F112 distinction).  It is cheap to close and the machinery
is there: the editor driven under a real X server with that variable
set, asserting the line, goes red the moment the call stops firing or
lands on the wrong connection — which is exactly how the first attempt
failed.

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

gate: `shell/editor/src/palette.rs::an_arrow_is_not_an_accidental_return`.
**Measured 2026-08-24**: the `reverse.is_empty()` guard in `step`
removed → red; restored → green.

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

### F110. **[resolved]** The zoom could wedge — the mirror only synced after input

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

**The other half, closed 2026-08-18** — not by explaining the 12, which
is not recoverable, but by making the mirror unable to hold it.

*What could not be found:* no path in today's source sets the rung past
the ladder.  `font.rs`'s `LADDER` is a nine-entry static, `zoom_by`
clamps into it, and `Workbench.zoom` refuses `at >= zoom_rungs`.  The
suspicion stands and is worth writing down properly: **twelve is what
an undo count looks like.**  The `state` gesture is nine positional
numbers on a tab-separated wire, and `undos` is two fields along from
`zoom` — a field-order slip between the two ends is the one mechanism
that fits a mirror twelve rungs up a nine-rung ladder, and it would
have been silent.

*What was done about it:*

* `Workbench.note_state` clamps — the window owns the ladder, so
  `rungs` is taken as given and the position is put inside it.  An
  impossible reading is not stored, whatever put it on the wire.
* **Both ends of the wire are pinned against each other.**
  `furniture.rs` already asserted the exact line for a known state;
  `test_the_state_gestures_field_order_is_the_one_rust_writes` reads
  that same line with the Python parser and checks every field lands
  where it belongs.  A reorder on either side now fails on the other,
  which is the only protection nine positional numbers can have.

Reopen if a transcript shows it again — but it can no longer persist,
and if the cause is the field order, it can no longer arrive.

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

gate: `shell/editor/src/palette.rs::space_does_not_eat_a_proposed_path`.
**Measured 2026-08-24**: `"Path"` dropped from the space exemption → red;
restored → green.

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

gate: `none — not a repair`.  The report was answered by a measurement
(`tools/dialoglag.py`, 13 ms settled, ~71 ms mid-compile) and no code
changed; what fires if the beat returns is the status line saying a
build is running, which is a reading, not a gate.  A bounded beat during
a visible build wants a caller first, as the entry says.

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

gate: `partial` — the hit-test is held, the fall-through is bare.
**Measured 2026-08-24**: `covers` made to say an open panel covers
everything → `covers_agrees_with_what_is_drawn` red.  Then the other
half — `window.rs` given back its `return Captured` after `hide()`, so
the click is eaten again — and **the whole workspace stayed green, 81
tests**.  The defect as reported was the eaten click, and nothing pins
it: a window test that presses outside the open list and sees the knob
under it answer is the gate not yet built.

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

gate: `shell/editor/src/palette.rs::tab_completes_the_path_under_the_cursor`.
**Measured 2026-08-24** by putting the defect back — the `Key::Tab` arm
disabled — and the test went red; put away, green.

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

gate: `test/test_session.py::test_opening_a_file_asks_the_window_for_it` —
**and it held only half of this until 2026-08-21.**  `do_open` closes the list in two
places, the file that exists and the name being started, and the test asserted `"close"
in ed.orders` for the first only: taking `close_list()` out of the **new-file** branch
passed 170 of 170.  That is the branch F125 walks into — a mistyped name gets a starter
wearing it, and the keystrokes aimed at the code go into the table.  Widened the same
day to run both branches; each one now goes red on its own.

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

gate: `none — not yet built`.  **Measured 2026-08-21** by dropping the guard at
`window.rs:1344` so every arriving description follows the caret again — the whole of
the defect, since the snap-back ticked with the transport: **346 of 346** pass.  Nothing
in the crate can see a scroll that will not stay put.  Cheap only if the furniture
handler becomes reachable from a test; `window.rs` is the blocker and
`card:interface-oracle.md` is where that lives.

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

gate: `partial` — the tool is held and the decision is bare.
`shell/editor/tests/view.rs::follow_past_lands_below_the_shadow` holds `follow_past`
itself and `shell/editor/src/palette.rs::paint_tests::the_panel_flips_low_as_one_piece`
holds the flip, so the defect cannot return *through those*.  **The call site is
unheld:** `window.rs:1166` decides to use `follow_past` at all, and swapping it back to
`v.follow(&doc, font)` — **measured 2026-08-21** — passes **346 of 346**.  The one file
in the crate with no `#[cfg(test)]` block, again.

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

gate: `none — not yet built`.  **Measured 2026-08-21**, all three halves put back
separately and nothing anywhere noticed:

    _where's verb guard removed       → 2977 of 2977 pass (`-m "not golden"`)
    _reask restores `asking = None`   → 256 of 256 pass in the three files that could see it
    Asked fires unconditionally again → 346 of 346 pass (`cargo test --workspace`)

The third lives at `window.rs:608`, the file with no `#[cfg(test)]` block, which is
F153's finding arriving at a second entry.

`test/sessions/F123-blip-session.ges` is the recorded reproduction and **nothing in the
tree names it.**  Counted 2026-08-21: of 19 specimens, 5 are named by a test and 14 by
nothing, and of the 12 recorded `-session.ges` transcripts only `chopin-session.ges` is
replayed.  The four that are used are used as *source text* — a `.ges` program handed to
the compiler — not as sessions played back.  So the transcripts a person's walk was
recorded into are evidence and not instruments, which is the same shape as this whole
card one level up.  *(An earlier draft of this line said no file reads `test/sessions/`
at all.  Wrong: the tests build the path as `parent / "sessions" / …`, which the grep
that produced the claim could not match.)*

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

gate: `none — not yet built`.  **Measured 2026-08-21** by putting the defect back —
`editor.load(text)` for a name that does not exist, in `workbench.py`, so the phantom
reads as saved again: the Python suite `-m "not golden"` passes **2977 of 2977**.  The
`[+]`-from-birth tell is the entry's whole fix and nothing anywhere asserts it.  Cheap:
a `Workbench` on a missing path and one read of the saved flag.

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

gate: `test/test_audioeditor.py::test_commenting_a_bank_out_of_sound_survives_and_says_so`.
Checked 2026-08-20 by handing the leaving engine the live `control` again: the jog answers
`audio stopped: list index out of range` — the crash Henri met, not a proxy for it.

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

gate: `test/test_session.py::test_opening_a_file_that_is_not_text_is_a_sentence` —
**and it did not gate this until 2026-08-20.**  Its fixture put the `─` on the boundary the
*fix* reads, and `duet.ges` has been edited since and straddles neither, so the four-byte
drop put back passed.  Widened to a sweep of offsets 4085–4095: fails at 4090 on the old
code, and indifferent to where the boundary is put next.

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

gate: `shell/editor/tests/view.rs::a_box_at_the_fold_stops_at_the_fold` —
**and it did not gate this until 2026-08-20.**  It excused any rect starting at `y >= tall`,
which is a box painting *entirely* on the bar's ground: the clip removed gave a chrome rect
y=120 h=80 over a 24-pixel bar and the test passed.  Tightened — only the bar may start at
the fold, and the box must be drawn when there is room, so it cannot pass on an empty
frame.  The scope half of this entry is held by F139's gate.

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

gate: `shell/editor/src/palette.rs::paint_tests::a_page_stays_inside_the_window`.
Checked 2026-08-20 by making the page hang below the panel again: `a rect left the window:
y=564 h=252`, in a window 600 tall.

### F134. **[resolved]** `now : Sig Float` — the current time in seconds, to the substrate

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

**Resolved 2026-08-18.**  `now : Sig Float` in both vocabularies,
written by the renderer beside `sampleRate` and `constSig` — which is
where it belongs for their reason: what *how long has this been
running* counts in depends on who is running it.

**One correction to the ask, and it is the whole design.**  The canvas
half is **real seconds written per frame**, not a frame count over a
rate.  The rate the ask meant is `gui.run`'s fixed 60, and that window
does have one — but the workbench's canvas does not: its hold-off is
adaptive, because the cost of a frame is the *program's*
(`workbench.CANVAS_SHARE`, measured settling between 8 and 34 Hz on one
machine).  Dividing by a nominal 60 there would have moved the guess out
of the program and into the library rather than removing it, and the
picture would have run at a speed that depended on how expensive it was
to draw.  So the host writes the seconds it already knows: a
`wallclock : Chan Float` the renderer declares, read with the
`0.0 ::: mkSig (wait …)` idiom `gui.ges` already documents for channels.

Three things drive frames and all three now write it: `Substrate.tick`
(the workbench canvas), `gui.run` (the standalone window), and
`walk.rs`'s `Walker::frame` — **the last one because a `canvas <expr>`
box is walked in Rust and mints its own frame**, so leaving it out would
have made that box the one canvas where `now` stood still, which is this
defect again one window over.

`scenes` gets a nominal frame instead, and stays a pure function of its
event list: a `Tick` is worth 1/60 s and nothing else moves the clock.
Without that the one feature this adds would be untestable by the one
tool that tests canvases.

**And a renderer-written name has no manners unless it is given some.**
A library name a program also uses is renamed aside by
`prelude.shadow_libraries`; the entry's names come *after* the author's
text and get none of that, so adding `now` took the name from every
program that already had one — found immediately, by a test whose canvas
called its transport position `now`.  Both entries ask `audio.defines`
first now, and a program that spells the name itself keeps it.

### F135. **[partly resolved]** Long features work in silence — progress belongs in the statusline

Henri, 2026-08-14 (`fixme.incoming.txt`): Mikko, attempting a
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

### F136. **[missing]** A tuple-pattern lambda picks the wrong instance, silently

Found 2026-08-14 while building the score box (`spec/scorebox.md`),
which read every note's payload as its own key number and drew a
picture that was wrong without complaining.  The four-line repro:

```
readP : (Notable a) => Int -> (Int, a) -> (Int, Int)
readP b p = case p of
    (k, x) -> (b, noteKey x)

ps : List (Int, H)
ps = (7, H 41 1) :: Nil

viaWhole : List (Int, Int)
viaWhole = map (p => readP 0 p) ps          # (0, 41) — right

viaPattern : List (Int, Int)
viaPattern = map ((k, x) => readP k (k, x)) ps   # (7, H 41 1) — wrong
```

Both spell the same program.  The second binds its parameter with a
**tuple pattern** and rebuilds the tuple, and the constrained call in
its body resolves against `Notable Int` — the instance for the
tuple's *first* field — rather than `Notable H`.  `noteKey` is then
the identity `Notable Int` defines and the payload comes back where a
number was asked for.

**Silence is the whole severity.**  The types are inferred correctly —
`__nb_ev__ : List (Int, Int, Int, Int, Int)` is what the checker
reports, and the value that arrives is a constructor — so nothing
refuses and nothing warns; only reading the values says so.  Every
other shape tried dispatches correctly: the direct call, the
whole-value lambda, `case` on a tuple, and the same helper applied
outside a `map`.  Which puts the fault in what a tuple *pattern* in a
lambda binder does to the dictionary a constrained call is handed —
`infer`/`_discharge`, not the g-machine.

The score box is written around it (`gestate/scorebox.py`,
`__nb_read__` takes the event whole and opens it with `case`), and
the comment there names this entry so the workaround dies with the
bug.


### F137. **[missing]** A zoom scales the band and not the picture in it

Henri, 2026-08-15, of the score box: *"they're really small and do not
respond to zooming the view."*  True of every walked canvas box, not
only the roll — the substrate box and each `canvas <expr>` box have it
too, and so does the full canvas view.

**What is actually happening.**  The editor's zoom is a ladder of
`(font, integer scale)` pairs (`font::LADDER`), and a box's *band*
grows with it, because its height is rows times the cell:
`view.slots`'s `box_h` is in rows and `view.ch(font)` is
`font.h * view.scale`.  The picture inside is not scaled at all —
`Walker::frame(cx, cy)` is handed the band's centre and the walk draws
in the program's own pixels, `Sized 384 116`, `Circle 8`, `Rect w 3`.
So the band gets taller as the text does and the drawing stays the same
size in it: at the top of the ladder a roll is a postage stamp between
lines of type three times its own height.

**The shape of the fix, and why it is not one line.**  The honest scale
is `view.scale` — the same integer the *text* is magnified by, so a
picture at zoom 2 is 2×2 pixels per pixel, which is exactly what a
font at `LARGE, 2` already is and will therefore look like it belongs.
That means:

* the walk is painted into a band of `(iw / scale, fh / scale)` and
  blitted at an integer factor — the trick the glyphs already use;
* the centre handed to `frame` is in *program* units, so it is
  divided too;
* **the press must divide by the same number.**  `canvas_box_rect` is
  deliberately the one function the painter and the hit-test share,
  and the scale has to enter there or a click will land where the
  picture used to be — the exact class of bug that function exists to
  prevent;
* the plugin panel shares the painter and does not zoom, so whatever
  is added must be a no-op at scale 1.

**Not to be confused with a `Sized` question.**  A program may of
course draw a bigger roll; `ROLL_W, ROLL_H = 384, 116` is
`scorebox.py`'s choice and could be another one.  That would make the
picture bigger at *every* zoom, which is a different complaint from
the one Henri has: the picture does not answer the zoom.

### F138. **[missing]** A space in a filler runs the completion on half of it

Reported 2026-08-15 by Henri, using `complete` on `minute.ges`: *"there
are some completion strings where it may dropout such as typing a list.
I hope to repro that issue."*  Reproduced the same evening, and it is
worse than a dropout: the half-typed answer is **written into the
file**.

**The repro**, driving a real window with XTEST (`tools/toolbox.sh`
installs what it takes): at a hole, `Tab`, then type `[1, 2]`.  What
crosses is

```
wants   complete 1 +1,   Float
command complete Float +1,        ← the space ran it
wants   complete 1 2     Float    ← what was left began a new query
```

so `[1,` lands in the hole and the rest of the list is typed into a
box that is now asking a different question.

**Why.**  Space picks and moves on *except where a space is content*,
and the exception is spelled by declared type: `Text` and `Path`
(`palette.rs`, `Key::Char(' ')`).  `Filler` and `Wanted` are `Text`
**aliases** — `type Filler = Text` in `command.ges` — and the window
is handed the name a command declared, not what that name aliases to.
So the exception does not fire, and the space is a Return.

**The fix is not to add `Filler` to the list in `palette.rs`.**  That
is the window learning the alias table, which is the vocabulary
learned twice — the next `type Something = Text` breaks it again and
breaks it silently.  What the window is missing is not the *name* of
the type but its *kind*, and the model is the one that knows: send
both, `Filler:Text`, the shown name and the base.  The prompt keeps
saying `<filler>`, the keys read `Text`, and a furniture line with no
colon still means what it means today.

Worth doing with F137, since both are the window being told half of
something the model knows.

### F139. **[resolved]** A scope squeezed itself into the fold instead of cropping

Henri, 2026-08-15 (`fixme.incoming.txt`): *"the scope / spectro have
the same clipping issue as canvas used to have."*

`paint_scopes` sized its drawing with `high = (band - 2).min(tall - top
- 1)` — the band's height *or* whatever was left above the fold,
whichever was smaller.  So a scope scrolled towards the bottom of the
window was redrawn shorter every row: the wave flattened, the
spectrum's bars shrank, and the picture told a different story about
the same sound at every scroll position.  The canvas had the same bug
and answered it when the boxes arrived — lay the walk out at the band's
*full* height and blit only the visible rows (`paint_canvas_boxes`,
and the entry there records Henri watching chopin's disc slide off its
place) — but the scope painter never heard.

**Resolved the same evening, and moved where it can be tested.**  The
arithmetic is `view::scope_frame` now, beside `frame_with`, so the fold
rule for a scope is checked where the trouble box's already is: drawn
at the band's own height, and every item cropped to the fold as it is
emitted.  Held by `a_scope_at_the_fold_is_cropped_and_not_squashed`,
which asserts the distinguishing thing rather than the obvious one —
the points that survive sit *exactly where the roomy frame put them*,
because a squeezed picture puts them somewhere new.  Checked against
the squeeze it replaced.

gate: `shell/editor/tests/view.rs::a_scope_at_the_fold_is_cropped_and_not_squashed`.
Checked 2026-08-20 by putting `high = (band - 2).min(tall - top - 1)` back: a point moves
to y=195, which is the squeeze — the test asserts the surviving points sit where the roomy
frame put them, so a rescale fails it and a crop does not.

### F140. **[resolved]** A render refused and the reason stayed in the terminal

Henri, 2026-08-16, reporting a session on `examples/long/sauna.ges`
(`test/sessions/F140-sauna-session.ges`, his own transcript): the
export answered

```
exportWav "sauna.wav"                  #= exporting sauna.wav…
#! sauna.wav: the render refused (exit 1)
```

*"I wonder why.  Either there's a bug or the information I get is too
light."*  The second, and the transcript is the whole report: those
two lines are everything the person was told.

**The renderer was right and it said so.**  Run by hand, the same
export answers

```
score: unfolds (`cycle`); performing dynamically
gestate: a dynamic performance cannot know when an unfolding score ends
```

which is correct — sauna's parts are `long 200 (cycle …)`, so
`unfolding_names` routes it to the dynamic path, and a dynamic
performance has no end to render to.  `_export_wav` redirected
**stdout** into a `StringIO` and left stderr alone, so the sentence
went to the terminal the workbench was launched from, which the person
in the window never sees; the exit code was all that crossed.

**Resolved 2026-08-16.**  `_export_wav` catches stderr too and
`_refusal` carries what the renderer blamed itself for — the last
`gestate: …` line, since progress is not a complaint — falling back to
the exit code only when nothing was said.  The person now reads

    sauna.wav: a dynamic performance cannot know when an unfolding
    score ends; say how long — `--seconds` from the terminal,
    `exportWavAt first last` in the workbench

**Both doors are named, and that is the other half of the defect.**
The sentence is read in two places and named only the flag, so a
person in the window was told to pass an argument the window has no
way to pass.  `exportWavAt` is the one that works there — checked:
five seconds of sauna renders through the same path.

Held by `test_a_refusal_carries_what_the_renderer_said` and
`test_an_unfolding_score_is_refused_with_the_door_it_has` in
`test/test_session.py`; the second runs the real renderer, since what
is worth pinning is that this *sentence* reaches the status line and a
stub would only pin the plumbing under it.

**What this does not fix**, and is worth its own sitting: a score with
no end has no `exportWav`, only `exportWavAt` — the editor cannot
offer *render the whole thing* for a piece whose "whole" is a
question.  Naming the bars is the honest answer today.

### F141. **[resolved]** `foo : int` is a legal signature and a certain mistake

Henri, 2026-08-16, relaying **Mikko, gestate's first outside user**:
they wrote `foo : int`, and could not see why it did not work.

Nothing was broken, which is the whole difficulty.  A name that begins
with a lowercase letter *is* a type variable, so `foo : int` is a legal
polymorphic signature over a variable that happens to be spelled like a
type.  The file analyses without a word about `int`.

**And then the compiler gave advice towards the wrong fix.**  The
complaint surfaced wherever the variable failed to satisfy a class,
which for `foo = 3` is a `Num`:

```
No instance for Num int — 'int' is a signature variable, standing for
whatever type the caller chooses; write '(Num int) => …' in the
signature to require it of the caller
```

Every word of that is true of the program that was written, and taking
its advice makes the mistake permanent.  Worse, with `main` untyped the
first thing said was `'main' cannot have a class context`, which names
neither the line nor the mistake — the reproduction is three lines:

```
foo : int
foo = 3

main = foo
```

**Resolved 2026-08-16** in the kind checker, which is the pass that
already knows the type vocabulary and already refuses `Intt`.  A
signature variable whose name matches a known type *exactly but for
case* is refused where it is written:

```
`float` is a type variable, not the type `Float` (at typo.ges:1:8) —
a name in lowercase stands for whatever type the caller picks.  Write
`Float` if that is the type you meant, or rename the variable if it
is not.
```

Two things had to come with it:

* **A signature variable had no position.**  It is minted in
  `desugar_signature` rather than desugared from a node, so its errors
  landed on whatever failed to unify with it.  `_signature_tyvars` now
  carries the span each name was first written at, and every message
  about a signature variable is the better for it.
* **The match must be exact but for case.**  `a`, `b`, `m` and `k` name
  nothing and stay legal; `int` names `Int`.  The vocabulary is the
  program's own kind environment, so a type the *file* declares
  protects its own name too.

The price is that a variable genuinely wanted under such a name has to
be spelled differently.  Measured before choosing it: across every
`.ges` in this repository, against all 94 type names the project
declares, there are **no** such variables — and the 92 example programs
still pass.

Held by five tests in `test/test_skolems.py` under *"The variable that
was meant to be a type"*.

**Not fixed, and adjacent**: a lowercase name that matches a type
*alias* (`type Duration = Float`) is not caught, because aliases are
expanded before the kind environment exists.  Worth revisiting with the
alias work in `roadmap.md` §"Name the datatypes", which is the change
that would make such collisions likely in the first place.

### F142. **[missing]** A canvas-only file cannot be opened in the workbench

Found 2026-08-17 while auditing the older language features
(`card:older-features.md`), by trying the command the manual
prints:

```sh
python -m gestate.workbench examples/gui/bounce.ges
```

The status line says

    bounce.ges  not playing: this file declares no `ticks`, and the
    player's generated entry needs it

and `canvas` then shows *"opening the canvas — it will appear when it
builds"* over an empty frame, for as long as you care to wait.  Both
shipped canvas examples do it — `bounce.ges` and `chain.ges` — and
`doc/manual.md` §"Fold the events into a state" documents that exact
command, promising the opposite: *"A file that declares only a
`substrate` has no `sound` for the engine to build, so the status line
says it is not playing; the canvas draws all the same."*

**It is an ordering, not a compile failure.**  `audioeditor._start`
runs `Live.start(text, …)` — the sound — and only afterwards calls
`loaders()`, which is where `_load_substrate` lives.  `workbench._begin`
catches the raise, says `not playing: …` and **returns**, so the loaders
never run and `self.substrate` stays `None`.  A file with no `sound`
therefore never reaches its own canvas, though `_load_substrate` is
written to be independent of it and says so in its docstring.

Not a compiler problem: `python -m gestate.gui examples/gui/bounce.ges`
renders its frames perfectly well.

**And the message misattributes it.**  `audiospans.in_source` maps
*"Unknown global `X` at entry line"* to *"this file declares no `X`"*,
which is exactly right for `sound` — the case it was written for — and
wrong for `ticks`, which is the audio prelude's own name and not
anything an author would write.  A person reading that goes looking for
a `ticks` to declare.

What to check first: whether `loaders()` can run before or beside
`Live.start`, and whether a file with a `substrate` and no `sound`
should take the audio entry at all.

### F143. **[missing]** One error inside `fix` becomes eight, and seven blame the prelude

Found the same afternoon, from a typo in a Datafun program.

```
main : Set Int
main = fix r => {1} ∪ r          -- `∪` is not the union; `\/` is
```

```
$ python -m gestate.typecheck --check that.ges
error: fix expects a boxed monotone set function …: Unknown global '∪' …
error: elem: Signature variable 'a' is rigid: …
error: sort: Signature variable 'a' is rigid: …
error: showItemsWith: Signature variable 'a' is rigid: …
error: clamp: Signature variable 'a' is rigid: …
error: bimix: Signature variable 'a' is rigid: …
error: showNat: Signature variable 'a' is rigid: …
error: pad3: Signature variable 'a' is rigid: …
error: showFloat: Signature variable 'a' is rigid: …
```

The first line is true and the other seven name **prelude functions the
author has never opened**, at prelude line numbers, about a mistake
nobody made there.  Any error inside a `fix` does it; the same error
outside one is a single clean line.

**The blast radius is `--check` and not the window.**  Opened in the
workbench the same file reports one complaint, mapped to its own line —
so this is a defect of the pass that collects *every* error rather than
of inference itself.  Which is where its cost is, too: `--check` is the
gate a script or a stranger uses, and this is the same family as F141,
where the compiler's advice pointed at the wrong fix.

What to check first: whether the `fix` path leaves a substitution or a
rigid-variable marker behind after it raises, so the definitions checked
after it inherit it.

### F144. **[missing]** An implicit parameter shows in a query without its name

Found while auditing `using`/`given` (`card:older-features.md`).

```
implicit hz : Float

tone : Sig Float
tone (using hz) = 0.2 * sine (!hz)
```

```
$ python -m gestate.typecheck --audio --query tone
tone : Float -> Sig Float
```

Two things are off in one line.  The file says `tone : Sig Float`, and
`doc/manual.md` §9 says outright that *"An implicit parameter is
invisible in the signature"* — so the answer contradicts both the source
and the manual with no word about why the extra `Float` is there.  And
the parameter is **unnamed**, in the one place where naming parameters
was the whole point:

```
$ python -m gestate.typecheck --audio --query lift     -- an ordinary one
lift x : Float -> Sig Float
```

`card:argument-names.md` exists because *"I do not figure out
quickly enough which argument in lowpass filters are which"*, and an
implicit is the argument least likely to be guessed — it is the one the
signature deliberately does not mention.  The name is in hand:
`implicit hz : Float` declares it.

Either answer would be defensible; disagreeing with the file in silence
is not.  `tone (using hz) : Float -> Sig Float` says both facts at once
and matches how the definition is written.

### F145. **[resolved]** A typed path lost to a fuzzy match from somewhere else

Henri, 2026-08-17: *"When I type `open ../../hello.ges` from
`minute.ges`, it throws me into tests/section that has `hello.ges` in
there."*

Reproduced exactly.  From `examples/audio/minute.ges`, the query
`../../hello.ges` offered **one** row — `test/sessions/F104-hello.ges` —
and Return takes the row, so the typed path could not be chosen at all.
`Session._where` resolves it correctly given the literal text; the card's
elaboration had blamed `_where` and its two prior defects (F122, F123)
and that was wrong.

**It is `_listing`, and it is F130's own fix firing where it should
not.**  Nothing at the root matched `hello.ges`, so `_below` ran a
breadth-first search four directories down and surfaced a file from a
directory nobody had mentioned.  F130 was written for a *bare* name —
*"`open lantern.ges` from the root used to answer 0 rows three times
while starting phantoms"* — where the deep search is exactly right.  A
query carrying a `/` is a different question: the person said **where**.

**Resolved 2026-08-17.**  A typed path is pinned as the first row when
the query has a `head`, with the deep matches under it.  `do_open`
already handled a name that is not there (*"new file hello.ges — saving
creates it"*); the listing simply never offered it, and a dialog where
Return cannot mean *what I typed* is the whole defect.

Rejected: suppressing `_below` whenever the query contains a `/`.  It
would fix this and regress `open examples/lantern.ges`, where a
directory is named and the file really is beneath it.

Tests pin **which row comes first** — F122 and F123 were each fixed at
this site without one, which is how a third came to exist.

### F146. **[missing]** `Ctrl-Tab` goes to the canvas and will not come back

Henri, 2026-08-17: *"Ctrl+Tab goes to canvas.  Ctrl+Tab appears also in
source command, but it doesn't go back to source."*

**Both commands really do claim the key**, and that is the intent —
`session.KEYS` has `"canvas": "Ctrl-Tab"` and `"source": "Ctrl-Tab"` on
consecutive lines, which is a toggle written as two halves.

**What breaks it is that nothing chooses between them.**
`window.rs::shortcut` resolves a chord against the command list with

```rust
chrome.commands.iter().find(|e| e.key.eq_ignore_ascii_case(&chord))
```

and `find` takes the **first** match.  `canvas` is declared before
`source` in `command.ges` and ranked before it in the list, so `Ctrl-Tab`
runs `canvas` every time — including while the canvas is already showing,
where it is a no-op.  `source` advertises a key it can never receive.

So there are two defects and the smaller one is worse: the command list
**tells the reader something untrue**.  It says `Ctrl-Tab` beside
`source`, and pressing it there does nothing.  A key that is drawn and
does not work is the same class of fault as a knob with no channel behind
it, which this editor already refuses to ship (`Knob.wired`).

**The fix shape, and it needs no window change.**  The chrome is a
description and the model owns it, so let the model send the key on the
command that would actually do something: while the source is showing,
`canvas` carries `Ctrl-Tab` and `source` carries none; while the canvas
is showing, the reverse.  `find` then finds the right one unchanged, the
list never advertises a dead key, and both commands keep their names for
anybody who types them in full.  `session.furniture` already emits
`command\t<name>\t<usage>\t<key>\t<summary>` per verb and
`session.view.showing` already says which frame is up.

Rejected before it is proposed: making the window pick by its own view
state.  That is a second place deciding what a key means, and the two
could disagree — the rule this editor keeps everywhere else is that the
model decides and the window draws.

### F147. **[partly resolved]** A pop at start, a scratchy knob, and a drone under the laptop's floor

Henri, 2026-08-17, playing `examples/audio/tuning.ges` — three
observations in one sitting, kept together because two of them may share
a cause:

> the knob sounds scratchy when dragged and I think the sound is too low
> for laptop speakers. But now it is clearly there. Also there's a bit
> strong "POP" or "CHOP" when the program starts. Almost like analog pop
> when a live plug is connected.

**None of the three is diagnosed.**  What follows is what was ruled out,
so the next reader does not spend the same half hour.

#### The pop — bisected to the live control path, 2026-08-17

**Three experiments, and the first two were badly designed.**  Both are
kept here, because a reader will reach for them for the same reasons.

| what was run | heard | what it actually proved |
|---|---|---|
| `workbench README.md` (inert) | no pop | **nothing.**  An inert file returns from `start` before `_open_host` is reached, so the card is never opened.  A device that is not opened does not pop. |
| a program whose every sample is `0.0` | no pop | the device opens clean and the host's start is clean.  **The pop is in the waveform.** |
| `tuning.ges` with the knob replaced by a fixed `415.0` | no pop | and this one carried it, because it changes **exactly one thing** and was proven bit-identical to the original at rest (`render(...) == render(...)`, worst difference 0.0). |

`tuning.ges` itself pops.  So: **the pop is the live control path's first
blocks, and nothing else.**

Two things were also ruled out along the way:

- **Not the waveform as written.**  The offline render starts at exactly
  `0.0` and its largest step in the first 10 ms equals the steady-state
  one.
- **Not the master fader.**  `Host.__init__` starts the fader down on
  purpose (*"the first block is the same step in the waveform as any
  other and pops the same way"*) and `host.c` ramps it by `n / mute_len`
  per block, `mute_len = fade_len / 4` — a **10 ms** ramp at `fade_ms =
  40` and 44100 Hz, four cycles at 415 Hz.

**A limit on the oracle, which is the durable half of this entry.**  A
clean offline render does not clear the live path: `audioperform -o`
renders a knob **at its resting value** and never exercises the control
channel at all.  `--control-every` does not rescue it either — it
deliberately *sweeps* a knob across its range to make a control clock
observable, so the larger sample-to-sample steps it produces are the
sweep, not a click.  Both of those were mistaken for evidence here before
the bisect was run.

### Established, and fixed — 2026-08-17

The control block is zero-initialised — `(ctypes.c_int64 * controls)()`
in `audiohost.Host.__init__` — and `415 ::: mkSig (wait concertChan)`
covers only the very first *instant*.  If the host has not yet written
the knob's resting value, `concert` reads **0** for some number of
blocks, the frequency is 0 Hz, and the drone is silent while the 10 ms
master fade spends itself on nothing; the tone then arrives with the
fader already part of the way up.

**Confirmed by instrument rather than by argument.**
`test_no_knob_still_reads_zero_when_the_render_loop_begins` stands a stub
in for the host and photographs its control block at the instant
`run_device` is entered.  Without the fix it reads **`[0, 0]`** — both of
`twoknobs.ges`'s knobs at zero when the first block was made.  With it,
neither.  The oracle has failed once, which is the only way to know it
can (`manifesto.md` §"The three ways an instrument fails").

**Fixed**: `_run_host` pushes the controls once, synchronously, before
the render loop starts.  One line, and it removes the race rather than
narrowing it.

**Asserted about the state, not the call order** — Henri's own framing,
*"zero is a zero"*.  A test that checked `_push_controls` runs before
`run_device` would be reading the fix back to itself; what matters is
what the loop *finds*, which stays true however the code is rearranged,
and needs no sound card, no listener and no ears.

### But the pop survived it — Henri, 2026-08-17

> The pop is still there.  But the knob fix was good anyway.  It's better
> if the knob value is what expected of it and I am sure this would have
> gone up other time.

**So the zero race was real, is fixed, and is not the cause of the
reported pop.**  Recorded plainly because the paragraph above reads like
a closed case and is not one: a knob reading zero at the first block was
a genuine defect in every knob program since the C host landed, and it
would have surfaced eventually as something else.  It was not this.

What the bisect still says, unchanged: **silence does not pop, a fixed
415 Hz tone does not pop, and the same tone with a knob in its frequency
path does.**  The knob's *value* is now provably right when the loop
begins, so what is left is something else about a control channel being
in that path at all.

**The next bisect, and it is one variable again:** a program with a knob
that is *declared and not read by the sound*, and one with a knob on the
**amplitude** rather than the frequency.  Those separate three
candidates that are currently fused — the mere presence of a control
source in the graph, a control-rate signal feeding anything, and a
control-rate signal feeding a *frequency* specifically.

### Narrowed to one variable, with a positive control — 2026-08-17

Henri ran the amplitude version and then **built the control himself**,
which is what makes this conclusive rather than suggestive: he took the
same file, moved the knob from the amplitude to the frequency, restarted,
and heard the pop return.

| program | knob | heard |
|---|---|---|
| silence (`sound = !0.0`) | none | silent |
| fixed 415 Hz drone | none | silent |
| the same drone, knob on the **amplitude** | yes | **silent** |
| the same drone, knob on the **frequency** | yes | **pops** |

Every one of those renders bit-identically at rest.  So it is not the
device, not the host's start, not the master fader, not the presence of a
control source in the graph, and not a control-rate signal in the sound
path.  **It is specifically a control-rate signal feeding a frequency.**

### And the graph is innocent, which is where it stops

`audioextract` on the two knob versions gives the same eighteen nodes in
the same shape, and the declared initial state is right in both: the
channel source carries `init: 415`, and all three phase accumulators
carry `init: 0.0`.  Nothing about the *program* explains it.

**So every hypothesis left is about the first few blocks of live
execution, and nothing in this tree can look at those.**  That is not a
figure of speech — it is the same wall the offline render hit, arrived at
from the other side.

### The oracle was built, and it moved the wall — 2026-08-18

`card:unheard-output.md` landed, so the thing named below now
exists: `GESTATE_HOST_TAP=<frames>` and `Host.tap()` hand back what the
sink was actually given.  What it said in its first hour:

* **The pair is bit-identical at rest**, confirmed in one run instead of
  one listen each.
* **The late-knob hypothesis is refuted for this symptom.**  Driving the
  control to arrive *late* — which `audioeditor.control` can still do,
  since it answers `0` for a knob with no site yet and sites are placed
  on a thread — produces a step four times the settled one, exactly at a
  block boundary, in the **amplitude** version.  The **frequency**
  version stays clean.  That is the opposite way round from what was
  heard, so a late knob is not the pop.

  | program | knob from block 0 | knob late by 3 blocks |
  |---|---|---|
  | `F147-freqknob.ges` | clean | clean |
  | `F147-ampknob.ges` | clean | **step 0.165 against a settled 0.043, at frame 511** |

* **And a latent click nobody has reported**: the amplitude row above is
  a real defect, in a program nobody has complained about, found by an
  instrument twenty minutes old.  It is not this entry's pop and it is
  worth its own look.

### Caught in the real editor — 2026-08-18

`GESTATE_HOST_TAP_TO` was added so the tap could be read out of a
process nobody is inside, and the first thing it was pointed at was the
editor playing `F147-freqknob.ges`.  **The pop is in the samples the
card received, and it is in the first ten milliseconds.**

| frames | worst step | mean step |
|---|---|---|
| 0–441 (the 10 ms master fade) | **0.03592** | 0.00619 |
| 441–882 | 0.02589 | 0.00221 |
| 882 → 88 200 | 0.00521 | ~0.0016 |

Peak amplitude in the first 441 frames: **0.41**, against 0.50 settled.

Two readings, and both are the point:

* **The opening oscillates about seven times faster than the settled
  tone.**  Same amplitude, seven times the sample-to-sample step, means
  seven times the frequency — so *the frequency is wrong for the first
  ten milliseconds and then settles*, which is the missing half of
  "a control-rate signal feeding a frequency, in the first blocks".
* **And the master fade is not covering it.**  0.41 of 0.50 inside the
  ramp that is supposed to start at silence.  `mute_len` is
  `fade_len / 4` — 441 frames at `fade_ms = 40` — and a *block* is 512,
  so the whole fade is shorter than one block of the loop that applies
  it.  Whatever the ramp is worth, it is spent before the first block
  ends.

**What is shown and what is inferred**, kept apart on purpose.  Shown:
those numbers, from the card, in one run, with nobody listening.  Also
shown: the same program with its control pushed *before* the loop is
clean through the pipe **and** through the device, at 0, 3 and 12 blocks
of lateness.  Inferred: that the editor supplies a different value for
the first blocks than the file's own `init`, and that this is the step.

**And the late-knob hypothesis is dead**, conclusively rather than
suggestively:

| | knob from block 0 | late 3 blocks | late 12 blocks |
|---|---|---|---|
| `F147-freqknob.ges` | clean | clean | clean |
| `F147-ampknob.ges` | clean | **POP 0.484** | **POP 0.173** |

A frequency knob arriving late *cannot* pop: at 0 Hz the phase is frozen
at zero, so the tone begins at zero and moves continuously.  An
amplitude knob arriving late steps from silence to full mid-waveform.
Henri heard the **frequency** one pop, so this is not the mechanism —
and the amplitude row is a latent defect nobody has reported, with a
step eleven times the settled one.

**The next question is one line of instrument**: print what
`audioeditor.control` returns for that node on each of the first ten
blocks.  If it is not 415 for some of them, this is finished.

### The pop, found and fixed — 2026-08-18

**The editor was overriding the value the program declared.**

`tuning.ges` writes `415 ::: mkSig (wait concertChan)`.  The `:::` is
the author saying what the value *is* until something changes it, and
the graph carries `init: 415` — so the first block renders at 415 Hz.
Then `_push_controls` wrote `value_of(name)`, which fell through to
`knob_default`: **mid-travel of an inferred range**, and an `Int`
channel's range is `0 .. 100`, so **50**.  The frequency dropped by a
factor of eight between the first block and the second, and the step
between them is the click.

That is why it was *specifically* a control-rate signal feeding a
frequency: a step in frequency is a step in the phase slope, mid-
waveform, at whatever amplitude the tone had reached — and it had
reached 0.41 of 0.50, because `mute_len` is 441 frames and a block is
512, so the master fade is spent inside the first block.

**Measured at every step, with nobody listening.**

| | worst step | at frame | settled |
|---|---|---|---|
| the editor's own card, before | 0.03592 | 425 | 0.00504 |
| a harness pushing `init` then 50 at block 1 | 0.04155 | 494 | 0.00509 |
| the editor's own card, after | 0.04322 | 31135 | 0.04322 |

The middle row is the reproduction — the same settled step to three
figures, at the same place — and the last row is the fix: worst *equals*
settled, so there is no transient at all, and the tone is at 415 Hz
throughout instead of dropping to 50.

**The fix.**  `knob_default` answers what the program declared, and
mid-travel only when it declared nothing — which is the case mid-travel
was written for.  `knob_range` stretches to hold the declared value,
because a slider that ran `0 .. 100` beside a value of 415 would sit
pinned at its maximum telling somebody their knob was at full travel
when it was at an eighth of it.  The declared value is a fact about the
program; the range is a guess about it, so the guess gives way.

Held by `test_a_knob_starts_at_what_the_program_declared`, asserted
about the *value* rather than the call order — Henri's own framing from
the last time this entry was worked: *"zero is a zero"*.

**And this is what `card:unheard-output.md` was for.**  Four
listens got as far as *a control-rate signal feeding a frequency, in the
first blocks*, and stopped.  The tap found the rest in one run, and the
fix was confirmed by a second — no ears at either end.

### The other two observations stand

The pop is closed; the scratchy knob and the level on laptop speakers
are not, and Henri's own reading of `tuning.ges` on 2026-08-18 is that
it *"is not finished yet, more bug squishing needed"*.  This entry stays
**partly resolved** until those are answered.

**The oracle this needs, named so it stops being re-derived:** `host.c`
writes every block to the card through `snd_pcm_writei`.  A tap at that
call hands back exactly the samples the device received — the one thing
no offline render produces, and precisely what *did it pop* requires.

Henri's own rule, from the same afternoon: *"when you say 'be my oracle',
there's actually something implying in that which might require 'is this
really not possible to delegate to a real oracle?'"*  Here the answer is
yes and it is not built, so the hunt costs one person's attention per
iteration and cannot bisect.  **Four listens were spent before this
entry stopped.**  The next step is the tap, not a fifth —
`card:unheard-output.md`.

**The bisect is checked in**, so it does not have to be rebuilt by the
next person: `test/sessions/F147-ampknob.ges` (silent) and
`test/sessions/F147-freqknob.ges` (pops), one variable apart and
bit-identical at rest.  The second is Henri's own — given the first to
try, he moved the knob himself and heard it come back.

**The oracle this wants, and it does not exist.**  Henri, the same
afternoon: *"when you say 'be my oracle', there's actually something
implying in that which might require 'is this really not possible to
delegate to a real oracle?'"*  Here it is delegable and was not
delegated: `host.c` writes every block to the card through
`snd_pcm_writei`, and a tap at that call hands back exactly the samples
the device received — the one thing no offline render produces, and
precisely what *did it pop* requires.  Not built.  The excuse was that
the offline oracle could not see it, which is true and is not the same
as *no oracle can*.

**And if it is that, it is not this example's bug.**  Every program with
a knob in a signal path has the same first blocks, and this one is only
audible because the knob is a *frequency* — where the ear hears a
discontinuity that it would forgive in a filter cutoff.

#### The scratchy knob

Undiagnosed, but the mechanism is not mysterious: `reference` is a
stepped control signal read straight into a frequency
(`415 ::: mkSig (wait concertChan)`), with no smoothing anywhere between
the channel and `sine`.  A frequency that jumps once per control block is
a phase discontinuity per block — textbook zipper noise, and a defect of
the **example** rather than the engine.

`synth.ges` has the tool: `slew : Sig Float -> Sig Float -> Sig Float`,
a one-pole toward a target.  **It needs care rather than dropping in**,
because `slew` is `scan slewStep 0.0` — it starts at zero, so a naive
application would glide the drone up from 0 Hz on every start, which
would *add* a noise at exactly the moment this entry is also about.

#### The level

`0.6 * drone` was raised to `0.95` the same morning (peak 0.317 → 0.502)
and he still reports it low for laptop speakers.  Half of what is left is
not gain: three pure sines have no harmonic content, and a small speaker
with no low end reproduces almost nothing else.  Raising it further eats
headroom the knob needs; the honest fixes are a different timbre or a
different example, and both change what the file is for.

### F148. **[resolved]** The taskbar wore a sine; the front page wore the egg

Henri, 2026-08-17, from a fresh install of Ubuntu 26.04 LTS on the work
laptop: *"it drew an icon of blue sine on black background instead of
the egg with sine in it. Why no egg on the transparent background? I
thought the icon was always going to be an egg."*

**It was always going to be an egg, and only ever was on one machine.**
There were two icons in the tree and nothing that could tell they
disagreed:

* `doc/gestate.svg` — the artwork, teal shell, amber signal, no
  background at all.  Read by the README and by the launcher
  `doc/install.md` teaches you to write by hand.
* the sine — one period in the caret's blue on the editor's ground,
  drawn twice in code (`window_icon::drawn` into `_NET_WM_ICON`, and
  `workbench._icon_png` into `hicolor`), both from `b23ef2e`.

Henri's home machine had the hand-written `.desktop` file from
`install.md` and therefore the egg.  The work laptop had neither, so it
got what the code draws.  Same commit, same tree, different picture —
and no test could catch it, because **the two drawings never appear on
the same screen**: one is read in a browser, the other in a dock.

The rule that produced the sine was a good one — *an asset is a file
that can go missing and a decoder is a dependency, while a sine is
eight lines* — and it is what made the drawing local, and local is what
let it drift.

**Resolved by making one drawing and giving it to everybody.**
`gestate/icon.py` holds the shape, rasterises it, and writes two
committed files: `doc/gestate.svg`, which it now renders *exactly* —
the original generator was never committed and has been fitted back out
of the 121 points it left behind — and `doc/gestate.argb`, which is
`_NET_WM_ICON`'s own layout, `include_bytes!`-ed into `shell/editor`.
So the window has no drawing of its own to drift with, and the good
half of the old rule survives: nothing to decode, and nothing to go
missing at run time.  `test_icon.py` fails when the committed files are
not what the source renders, when the crate stops compiling them in,
and — the check that would have caught this one in the first week —
when a rendered size is not a transparent egg with a signal inside it.

Two things the small sizes needed, both because a 16 px icon is not a
scaled 256 px one: the strokes are hinted up to stay visible, and the
signal is pulled in by what that thickening ate, or the shell and the
wave meet and the icon is a blob.  Three cycles in six pixels is a
smudge, so a small raster draws fewer of them; the artwork is never
simplified.

### F149. **[resolved]** The desktop icon installed correctly and did nothing when clicked

Henri, 2026-08-17, on the same fresh Ubuntu 26.04 laptop as F148 — he
fixed it there before it was fixed here, and sent the diff:

```diff
-        f"Exec=env PYTHONPATH={root} {sys.executable} "
-        "-m gestate.workbench %f\n"
+        f"Exec={root}/tools/gestate-editor %f\n"
```

**A dock click passes no file.**  `%f` expands to nothing, and the
module with no file is not an editor:

```
$ env PYTHONPATH=… .venv/bin/python3 -m gestate.workbench
python -m gestate.workbench: error: a file to edit (or --desktop)
exit code: 2
```

`Terminal=false`, so that sentence went into a journal nobody reads.
Every other part of the entry was right — the icon resolved, the class
matched, the venv was pinned — and clicking it did nothing at all,
which is the failure shape with the worst diagnosis-to-symptom ratio
there is.

**`tools/gestate-editor` already existed for exactly this**, and its
own comment says so: *"opening the file it was handed, or the scratch
file when it was handed nothing — a bare click on an icon should open
an editor, not print a usage line."*  It finds the venv and `cd`s to
the tree as well.  `install_desktop` simply never pointed at it; the
wrapper and the installer lived one directory apart, each correct, with
nothing in the tree that had to agree with both.

**Resolved with the tier of tests the defect argues for**
(`test/test_desktop.py`, `card:installation-test.md`): the entry is
installed into a temporary `HOME`, `Exec` must name the wrapper, the
wrapper must still supply a file — and `main([])` must still exit 2,
asserted beside them, because that is the fact which makes the others
matter rather than look like style.  Checked by restoring the old line:
two of the five fail.  Checked once more the way a person would, with
`gio launch` on the installed entry under a throwaway `XDG_DATA_HOME`,
which opened a real editor and left no scratch file behind.

The same install found F148 and the missing `libx11-dev`.  Three
defects in one day from one fresh machine, in the one part of this
project that had no test at all.

gate: `test/test_desktop.py::test_a_bare_click_opens_an_editor` and
`::test_the_wrapper_supplies_the_file_a_click_does_not`.  Checked 2026-08-19 by
putting the old `Exec` line back: 2 of the 5 fail.  Neither names F149 — the gate
was there and the address was not, which is why the sweep counted this ungated.

### F150. **[resolved]** The first screen named a deleted button, and the menu opened on the command that does nothing

Henri, 2026-08-17, after trying the editor on Janne with no
explanation: *"He was unable to find the small gray-tinted button from
the program.  Once I helped he got the button open, he had very little
idea what is behind it."*  And, when asked which screen: *"My friend
was on the starter screen.  The basic sine function giving a tone."*

`card:button.md` is the card, and it holds the whole account.  Two of
what it found are defects rather than design questions, and this entry
is those two.  **Both were found by photographing the running window
rather than by reading the source** — the icon's own launcher, opened
and captured with `tools/lagcheck.py`'s `find_window` and `shot`.

#### The only instruction on the first screen pointed at a deleted control

With no file the editor opens on `audioeditor.STARTER`, sounding.  Its
one piece of guidance read:

> `doc/ref/index.md` is what is in scope; the **[ref] button top right**
> is the same pages in here.

**`[ref]` belonged to `gestate/audiopygame.py`** and went with it in
`71b90af` *"vastly improved editor coming"*.  The sentence survived the
UI it described — the same shape as the canvas losing its callers in
that deletion — and what stands in that corner now is `≡`, which opens
the command list and is not the reference.  So the first screen named
the wrong control in the right place, which `card:stranger-test.md`
already has the rule for: *a wrong guess that worked is worse than a
stumble; it means the window taught something false.*

**And it sharpens the report rather than excusing it.**  The screen said
*top right*.  He was told where to look and still did not see 24 pixels
of `FAINT` on `BG` — measured off the capture: an 8 × 7 box, 2.3:1,
drawn at `y = 0` of the *text area*, in line 1's own row rather than in
any bar or margin of its own.

Now the sentence says what is true and reachable: `what` says what a
name is, `fits` says what could stand where a type is wanted, and both
answer from the compiler rather than from a page.

#### The command list opened on `skip`

`session.vocabulary` derives the palette from `command.ges` **in the
order written**, and says why in its own docstring: *"the order somebody
thought about them rather than alphabetically, which is a worse order
for learning"*.  That is a good rule, and it means the file's order
**is** the menu — which nobody had read in the other direction.
`skip` was declared first, beside the `Semigroup Command` instance it is
the identity of.

So every stranger who ever found the button was met by `skip`,
selected, with the list's single explanatory line reading *"Do nothing —
the identity of `++`."*  A fact about the algebra, offered as somebody's
first move.

`skip` now sits at the foot of the file under a heading that says why it
is there, with a pointer from the instance it belongs to.  The list
opens on **`apply`** — *"Rebuild the instrument from the text and swap it
in while it plays"* — which is exactly the move the card found missing:
he was not stuck at *open* or *hear it*, both of which had already
happened by themselves, but at **hear the change**.

Held by `test_starter_and_first_command.py`.  Neither fix commits the
corner to anything, which is why they could be made while the question
of what the button should look like stays open — `manifesto.md`
§"Set-based, not point-based", written the same day and at his ask.

### F151. **[resolved]** Typing reached nothing, and there was no word for it

Henri, 2026-08-17, having measured what an audition costs: *"If audition
takes less than half a second after a change, then I think it should be
automatic.  That's the case with the intro's example function, but not
the case with every program."*  And then, on what the window owes while
it is not: *"we need some mechanism that shows the command to audition
and tells the audio is off sync, but still doesn't complain when user
types away."*

**The defect this closes belongs to a person.**  A stranger on the
starter screen could open the editor and hear it — both happen by
themselves — and could type.  Nothing he typed reached the sound,
because the step that puts it there is a key nobody told him about, and
**nothing on screen said the sound and the text had parted**
(`card:button.md`).

Three parts, and the measurements are in the card:

**Cheap, and measured rather than predicted.**  The cost does not
follow the size of the program — `lead.ges` is 432 lines and auditions
in 1.39 s, `lantern.ges` is 279 and takes 3.06 s — so nothing static
can decide this.  The gate is the last audition *of this file*
(`AUTO_AUDITION`, 0.5 s).  The first cut gated on that alone and was
wrong in a way every test passed: a file nobody has applied has no
measurement, **and a stranger never applies anything**, so the feature
was switched off for exactly the person it was built for.  `COLD_ENOUGH`
is the answer — a file that *opened* in under two seconds gets one
audition on trust, and what that one costs decides the rest.  Opening
time is a veto and never an estimate; the ratio between them runs from
0.37 to 1.24 across the corpus.

**Quiet.**  A dragged note always produces text that compiles; typing
does not, and half of what anybody types is briefly not a program.  So
an unasked-for audition may change the sound and **may not complain** —
one flag through `_built`.  That turned out to be a path rather than a
branch: returning quietly still left the exception in `live.pending`,
which `install` turns into a line in `live.errors` between two blocks,
which `_progress` announces — the forbidden complaint, arriving a moment
later from a thread that had never heard of the flag.  `_hush` is the
whole of the rule: no pending, and nothing appended to `errors` while
this build ran.  An `apply` or an asked-for `audition` still reports
everything it ever did.

**And it says so.**  `sound behind · audition Ctrl-Return`, in `AWAY` —
the colour that already means *a thing deliberately not sounding*, warm
rather than red because it is usually a choice being tried and not a
fault.  The words are the model's, so the key cannot drift from the one
`KEYS` binds; the window places and colours it and does not compose it.

Held by `test/test_autoaudition.py`, one section per rule.

**And the second sentence, found by photographing it.**  Silencing
`_built` was not the whole of *quiet*: `_progress` announces every
generation change — *applied edit 4 (no knob in this synth)* — so a
landing audition still wrote a line, once per pause in typing.  Shown
five of them stacked, Henri: *"typing doesn't need that."*  The flag
rides on the `Engine` rather than on the workbench, because the thing
that announces an installation runs between blocks on another thread
and a flag on the side would silence whichever build happened to land
next; carried by the engine it cannot name the wrong edit, because it
*is* the edit.  A `Ctrl-S` still announces itself.

### F152. **[resolved]** A complaint with no place to land

Henri, 2026-08-17, typing into the new automatic audition: *"The error
messages no longer interleave into their places.  Just try take `Sig
Floa` and see how the message doesn't land."*

**It had never landed, and the "no longer" was the audition making him
break things on purpose.**  Checked before anything was changed, by
driving the same keys against the editor twice — once with the automatic
audition and once with it disabled — and photographing both: a *type*
error interleaves as a red box under its line in each, identically.  So
the new code was not the cause and the report was still right.

`Unknown type constructor: Floa` carried **no position**.  A complaint
that names a line gets a content box under it; one that names none falls
back to a single sentence in the status bar.  Same seriousness,
different treatment, and nothing in the source said so —
`kindcheck.py` *had* the position arithmetic, written for `foo : int`
(F141) and used only there, because that was the one message somebody
had hit.

Five kind errors given their place, through one `_where` helper: the
unknown constructor, the two kind mismatches and the two function-type
ones.  Every node in `types.py` already carried a `span`;
`audiospans.in_source` already rewrote raw `line:col` into the author's
file.  Nothing needed inventing — it needed noticing.

Held by `test/test_error_places.py`, which asserts the place *and* that
the sentence still says what is wrong, since appending a span is exactly
how the message gets lost.  **`card:error-messages.md` is the card for
the rest of them**, at his ask: *"we maybe need to arrange a session
where we examine meticulously every error message and ensure they work.
We already did that once and it needs to be done again."*

### F153. **[resolved]** The window taught the key only to people who no longer needed it

Found while reading `card:button.md` against the running window,
2026-08-17, and fixed at Henri's ask the same evening.

`view.hint` puts `Ctrl-K` in the status bar.  It was set **by a burger
press** and cleared when the list closed — so the window taught the key
to somebody who had just demonstrated they could find the one control
without it, and said nothing at all to somebody who could not.  **The
teaching was downstream of the discovery it exists to make
unnecessary**, and the discovery is the part a stranger failed (F150,
and the 24 lit pixels `card:button.md` measures).

Now: **on until the key has been used, and then never again.**  Ctrl-K
is the one place that can know you have used it, so that is where it is
retired.  A burger press deliberately does *not* retire it — pressing
the button is finding the button, not learning the key, and somebody who
just found it is exactly who has still to learn it; the bar goes on
saying `Ctrl-K` while that list is up, which is where the old behaviour
was right and is kept.

One flag, on a mechanism already built and already drawn.  Photographed
on a window nobody had touched (says it), after one `Ctrl-K` (stops),
and after the list closed again (stays stopped).

gate: none — `shell/editor/tests/view.rs` holds the bar (it sets `hint` by
hand and checks the bar follows), and the retiring is the fix: `hint = false`
on `Ctrl-K` and untouched by a burger press is `shell/editor/src/window.rs:1860`,
the one file in the crate with no `#[cfg(test)]` block.  **Measured 2026-08-19:**
delete that line and `cargo test --workspace --no-fail-fast` still passes all 346.
card:interface-oracle.md

### F154. **[resolved]** A driven harness saved into the repository

2026-08-17, mine.  A reproduction harness launched `tools/gestate-editor`
with no argument — which opens `untitled.ges` **in the working
directory** — typed a deliberately broken program and pressed `Ctrl-S`.
The file landed in the tree, and the *next* run opened it and measured
the wrong thing for a while before the confusion was noticed.

Henri: *"Mistakes happen and that's one reason to have a fence."*  The
fence does not reach this one, and that is the part worth writing down:
the write was **inside the project** and was the editor doing exactly
what `Ctrl-S` means.  `tools/sandbox.sh` fences the tree from the
machine; nothing fences the tree from itself, and nothing should.

So the poka-yoke is upstream of the write.  `lagcheck.a_copy_of` sits
beside `driven` and states the same rule — *one funnel, so a sixth tool
cannot forget*: every harness opens a **copy** in a temporary
directory, same basename so a status bar or an `(at file:line)` still
reads right, and `None` yields a path that does not exist, which is
what a bare launch opens on and where its first save now goes.

**And the exposure was larger than the accident.**  All four committed
tools name *committed examples*, so any scenario that reached for
`Ctrl-S` would have edited `examples/audio/twoknobs.ges` rather than an
untracked scratch file.  Nothing had, which is luck rather than design.

### F155. **[resolved]** The one control was a glyph nobody could find

Henri, 2026-08-17, after Janne was given the editor with no
explanation: *"He was unable to find the small gray-tinted button from
the program."*  And, once the corner had been measured and the set of
answers written out: *"burger is thrown out, [command] is put in its
place."*

**The measurement is the entry.**  Photographed and counted off the
capture: the `≡` lit **24 pixels** in an 8 × 7 box, `FAINT` `#4a5260`
on `BG` `#14161a` — **2.3:1**, under the floor any interface guidance
puts on a control, the lowest contrast this window paints anything at,
and `FAINT` is this window's word for *there, but not for you*.  It
also stood at `y = 0` of the **text area**, in line 1's own row, where
everything else is text.

And the screen had *told* him where to look: the starter's own text
said the button was top right (F150), and he still missed it.  Which is
the strongest available argument that the drawing was under the floor
of findable, and the strongest that finding it was not the whole
problem — both were true, and `card:button.md` holds the six
answers that came out of that.

Now the corner reads `[command]`, at the ink's own weight, brackets
because that is already how this window says *chrome, not content*
(`[inert]`).  The box follows the word's length through one constant,
so `window.rs`'s hit test widened with it — one arithmetic, two
readers, which is why the press needed no change at all.

**Held by the first tests `view.rs` has ever carried.**  A frame is a
display list built by a pure function, so *the corner offers a word and
not a glyph*, *it is not painted in the colour that means ignore me*,
and *the box is exactly as wide as the word in it* are ordinary
assertions with no window in them.  Their blind spot is written beside
them and is the whole of this defect: **they see what was emitted,
never what it looked like.**  The `≡` would have passed all three.
`card:interface-oracle.md` is the card for the rest of it.

gate: `shell/editor/src/view.rs::the_corner_offers_a_word_and_not_a_glyph` for the
word, `::the_corner_is_not_painted_in_the_colour_that_means_ignore_me` and
`shell/editor/tests/view.rs::the_burger_is_drawn_inside_the_box_the_press_reads`
for the colour.

**Both halves need naming, and this was got wrong once already.**  Measured
2026-08-19 by mutation, with `--no-fail-fast` because `cargo test` stops at the
first failing binary and a fail-fast count reads like a coverage result:

    BURGER = "≡"      → only `the_corner_offers_a_word_and_not_a_glyph` goes red
    INK    → FAINT    → the other two go red

`the_burger_is_drawn_inside_the_box_the_press_reads` asserts `assert_eq!(s, BURGER)`
— **against the constant under test**, so it holds the colour and pins nothing about
the word.  Put the glyph back and it passes.  A first reading of this entry cited it
alone and called the defect gated; the assertion looks like it names the word and is
a tautology.  This is the card's own failure arriving inside the card's own work:
**an assertion read is not an assertion run.**

### F156. **[open]** The audio backend says which definition, never which line

Found by the sweep `card:error-messages.md` asked for, 2026-08-18, and
filed rather than fixed because the fix is not a line of arithmetic.

`audioextract` reports against an **origin** — `sound/raw/phase/driven`
— which is the path of definitions a node was inlined through.  It is
deliberately not a position (`audiospans.py`'s own opening paragraph
says why: stage 5 migrates state by comparing origins across a
recompile, and a position moves whenever anybody adds a line above it).
So a synth that cannot be compiled for the sound card is told *which
definition* and never which line, and the workbench has nothing to draw
a box under.

**The join already exists.**  `audiospans` is a module whose whole job
is to turn an origin into a `Site` with a file and a line in it, for the
knobs.  Nothing calls it from a complaint.

`doc/complaints.md` lists the fourteen rows this owns, and closing it is
visible there as the section getting shorter.

### F157. **[open]** The type machinery's later stages let go of the span

The same sweep, the same day.  Inference places its complaints — `at`
has been threaded through `infer.py` since the last sweep — but the
stages *after* it have not: `constraint.py` knows the predicate it could
not solve and no longer knows the expression that wanted it,
`elaborate.py` knows the class and the definition, `helpers.py` knows
the type a generated comparator cannot be built for.  A person who
writes `Set (Int -> Int)` is told exactly what is wrong, in a sentence
with nowhere to be drawn.

Sixteen rows in `doc/complaints.md`.  The shape of the fix is the one
`journal.md` Part I item 13 described for type errors and stopped short
of: *the data is available from the parser, it just needs to be carried
through*.

### F158. **[open]** A piece's complaints name a beat, never a line

The same sweep.  A score is written in the author's file and a
`ScoreError` says *"a `shape` at beat 12 has no width"* — a position in
the *music*, which is the right thing to say and not a thing the editor
can put a box under.  `audiovoices` was half of this and is fixed: a
`Bank` carries the line it was declared on, so ten of its complaints now
say `at line N:0`.  What is left is the score itself, where the parsed
events do not carry spans at all.

Twelve rows in `doc/complaints.md`.

### F159. **[open]** The evaluator's runtime complaints carry no position

The same sweep.  Dividing by zero is the author's mistake, arrives at
run time, and says `DivInt: division by zero` — no line, no definition,
nothing.  So do a pattern match that covers nothing, a primitive that
overflowed, and a signal read out of turn.

**And the pattern for fixing it is already in the same file.**
`gmachine.Hole` carries `line` and `col` on the instruction, put there
so that `_` — the one error a person is *expecting* — says where it is.
Every other instruction could carry the same, and the compiler that
emits them is looking at an expression with a span at the time.

Eleven rows in `doc/complaints.md`, across `gmachine.py`,
`audioengine.py` and `reactive.py`.

### F160. **[resolved]** Five modules were drawn out of the atlas for a day

Found by the day's only full-suite attempt, 2026-08-18, seventeen
seconds into it — and that is the whole of the defect, because the five
modules had been in the tree since morning.

`complaints`, `desk`, `gemba`, `history` and `pops` landed across one
session and none was given a lane in `gestate/atlas.py`'s `WHERE`.  The
atlas's own rule is that a module without a lane fails the test rather
than going quietly missing from the picture, *"because a lane is a
claim about what a module is for, and there is no deriving that"* — so
the check worked exactly as designed and nobody ran it.  Meanwhile the
generated sheets carried a claim about this tree that had been false
since the first of the five was committed: five modules the atlas said
were not there.

Resolved by writing the five claims: `pops` into **playing it**, since
it reads back what actually left the machine rather than anything a
compiler built; `desk`, `gemba` and `history` into **the window**,
which is the thing that owns all three — where the desk was left, where
a session is standing, and what the repository remembers; `complaints`
into **what you write**, beside `reference` and `atlas`, that lane's
sentence already being *the ones that read this tree and write it back
out*.  Then `python -m gestate.atlas`, which is what the failure
message says to run.

**The interesting half is the day, not the five lines.**  This cost
nothing to fix and was found at the worst possible moment: at the end
of a shift, blocking the only verification pass of that shift, on a
tree with six subsystems' worth of changes in it, and handed to Henri
with half an hour left in his day — *"the suite cannot run yet.  I
need to go in 30 minutes."*  Run at the commit that made it, it is a
seven-second failure naming the file.  `card:cheap-gates.md` is the
card for that, and this entry is its receipt.

gate: `test/test_atlas.py::test_every_module_has_a_lane`.  Checked 2026-08-19 by
taking `pops` back out of `atlas.WHERE`: it goes red, and
`test_the_sheet_is_not_behind_the_source` with it.  Neither names F160.

### F161. **[resolved]** Opening a file from the starter screen took the editor down

Henri, 2026-08-18, at the keyboard, on a build that had been green all
morning:

    AttributeError: 'NoneType' object has no attribute 'read'

Opening any file from the starter screen crashed the workbench.  The
walk — the channel a session narrates through — belongs to the
**window**, and switching the instrument underneath a window rebuilds
the `Session` around it (`gestate/workbench.py:588`, `_carry`).  That
rebuild copies across, by hand, the fields that outlive the switch.
The walk was not on the list, so the fresh session had none, and the
next pass of the loop asked it what had been said.

Fixed in `60cc9cd` by carrying it — and by never letting the walk be
fatal in the loop, since a narration channel taking the editor down is
the wrong order of importance whatever the cause.

**Filed a day late and on purpose**, because the entry is not really
about one field.  Three fields were forgotten at this one seam in a
single day — the walk here, then `walking`, then the trio the walk's
own movement is tracked by — and the suite agreed with every one of
them, because every `Session` test builds a `Session` directly and
nothing exercises *and then the instrument changed underneath it*.  A
rule was written into `spec/verification.md` after the first, and the
second and third came anyway; a rule in prose is not a control.
`card:carried-state.md` is the card for the control.

gate: `none — not yet built` (a roster test is proposed in `card:carried-state.md`).
The supporting measurement — delete `fresh.walk = _walk_for(…)` from `_carry` and
2817 of 2818 still pass — is **reported by the session that made it and not
reproduced here**, so it is evidence and not yet a fact of this file.

### F162. **[resolved]** The first instruction in the way in could not be carried out

**Janne, 2026-08-18, over chat, minutes into the run
`card:stranger-test.md` was pre-registered for** — relayed by Henri:
*"Janne is confused about `<this-repo>`, he wonders what you're supposed
to insert there?"*

`README.md` §Ubuntu, from nothing and `doc/install.md` §Ubuntu, from
nothing both opened with:

```sh
git clone <this-repo> gestate && cd gestate
```

**A placeholder in prose is a note to the author.  A placeholder inside
a shell block is a question asked of the one person who cannot answer
it.**  It is the first command in the project's front door, it stands
above every other step, and nobody who reads it has the information it
asks for.

Now the real address, over **HTTPS and not SSH**: the repository's own
remote is `git@github.com:…`, which is the author's push path and needs
a key a reader does not have.

### Why it survived a fresh-machine install

This is the part worth more than the fix.  The way in *was* walked from
nothing on 2026-08-17, on a fresh Ubuntu 26.04 laptop, and that walk
found three defects including F148 and F149.  It did not find this one,
because **the person walking it was the author**, and the author knows
what goes in the blank.  He cannot see this class of defect at all —
not through inattention, but because the missing information is in his
head and the instrument is his own reading.

That is `card:stranger-test.md`'s entire argument, arriving as a
measurement rather than a claim, eleven minutes into the run.

### The gate

`test/test_citations.py::test_the_way_in_has_nothing_left_to_fill_in` —
no `<…>` token inside a fenced `sh` block in `README.md` or
`doc/install.md`.

**This is the first closure made under the rule adopted the same day**
(`card:ungated-fixes.md`, and Henri's *"From now here on I think"*):
an entry does not close until it names the instrument that fires if the
defect returns.  The scope is deliberately narrow — `<date>` and
`<expr>` are honest placeholders in prose throughout this tree, and a
check that fired on those would be an andon nobody could read.

### The credential question, asked and closed

Whether the address is reachable **without credentials** — because if
the repository were private the fix would only move where a stranger
stops, from a placeholder he cannot fill to a password prompt he cannot
answer.  *Henri, 2026-08-18:* **"https://github.com/cheery/gestate is
enough to clone the repo.  cheery/gestate is public."**  So the way in
is open.

### F163. **[resolved]** The way in installs rust, and the next shell cannot find it — then says to run the thing that is missing

**Janne, 2026-08-18, 13:28, six minutes after cloning**, in the run
`card:stranger-test.md` pre-registered.  He reached the editor on his
own — `../README.md` §"Edit it while it sounds" is the section after the
one that named the file he was listening to — and got a Python
traceback.  The picture is `doc/stranger-two-no-cargo.png`.

```
gestate.editor.EditorError: no libgestate_editor.so and no cargo to
build it — `cargo build --release --features capi` in `shell/editor/`
makes one
```

**Which of the three `EditorError`s it would be was written down before
the picture arrived** (`card:stranger-test.md` §"13:28"), and it was
the predicted one.  That is the whole value of pre-registering: the
diagnosis cost one look instead of a conversation.

### Two defects, and the second is the worse one

**The sourcing step was a trailing comment.**  The install block read:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # then: . "$HOME/.cargo/env"
```

`rustup` puts `cargo` on the `PATH` by editing a shell profile that the
running shell has already read, so sourcing it is **required**, not a
nicety — and it sat at the end of a long line, in a comment, which is
the weakest position a required step can occupy.  It is now a line of
its own in both `README.md` and `doc/install.md`.

**And the error advised the impossible.**  A reader with no `cargo` was
told to run `cargo build`.  That is an instruction which cannot be
carried out by definition, and it is worse than saying nothing, because
he spends his time obeying it.  It now names the sourcing step and
`https://rustup.rs`, and says the build takes a few minutes the first
time — which nothing anywhere said before.

### The failure is delayed, which is why nobody caught it

Missing the sourcing line does not fail at the install.  It fails
**several steps later**, in a different tool, as a traceback from
`gestate/editor.py` — by which point the reader has done six things
correctly and has no reason to look back at step two.  The author never
meets it because his shell has read the profile long ago.

*Also visible in the picture and worth a line: his prompt is rendering
its escape sequences literally, `\[\e]0;\u@\h…`, so the shell he is
in is not the one `.venv/bin/activate` was written for.  Not pursued —
it is his environment, and nothing here depends on it — but it is the
kind of thing only a photograph of somebody else's terminal ever shows.*

### The gate

`test/test_way_in.py`, new, and it is where the way in's checks live
from now on:

- `test_the_shell_that_installs_can_find_cargo` — parametrised over
  both files, because they carry the same block and a fix to one that
  misses the other is the likely regression.
- `test_the_missing_cargo_is_not_told_to_run_cargo`.

Second closure under the rule adopted today, and the first one to need
a new file for its instrument.

### 13:44 — the fourth face, and the one that changes the fix

Asked how long the build had taken, he answered **"oisko jotain 10-15
sekuntia"** — maybe ten to fifteen seconds.

That falsifies the documentation twice over.  Both ways in said *a
minute or two*, which is the author's impression and was never measured
on anybody else's machine; they now say ten seconds to a couple of
minutes, and `doc/install.md` marks which end of that anybody has
actually seen.

**And it moves the defect.**  Ten to fifteen seconds is nothing by build
standards, and he volunteered it as *melko pitkä viive* — a fairly long
delay — without being asked about speed at all.  So making it faster
would have fixed nothing: **the silence was the defect, not the
duration.**  `gestate/editor.py` now prints one line before the build,
which is all it ever needed; `--quiet` and `capture_output=True` mean
cargo cannot speak for itself there, and that is correct, because its
output is wanted only when the build fails.

Gated by `test_the_first_build_says_it_is_working`.

*One caveat kept honestly: 10–15 seconds is a person's estimate of a
wait, not a timer, on one machine, and it is the only figure this
project has from a machine that is not the author's.*

### F164. **[resolved]** The starter's desk was committed, and it is the only one that ever was

Henri, 2026-08-18: *"I messed the untitled.desk we need gitignore for
those files by default."*

`untitled.desk` entered the tree in `6f2e721` *"the walk travels in the
code"* and sat in the repository root until it was noticed.  It is the
saved workbench state — caret, zoom, seed, loop, knob values — of
`untitled.ges`, which is what a bare `tools/gestate-editor` opens **in
the working directory**, and for anybody working here that directory is
this tree.  F154 is the same trap catching a driven harness; this is it
catching a person.

### The blanket rule was asked for and is not what landed

The ask named `*.desk`, and `.gitignore` **deliberately refuses** that
pattern, at length, for a decision out of
`card:persistent-workbench-state.md`: a `<piece>.desk` belongs to
the *piece*, travels with it, and being committable is the whole reason
it lives beside the `.ges` rather than in a dot-directory.  Ignoring all
of them would undo that quietly, in a file nobody re-reads.

So what is ignored is `untitled.ges` and `untitled.desk` by name.  The
starter is not a piece and never becomes one — the moment it is worth
keeping it gets a name — so nothing about the piece rule is touched.

**And one thing worth reading twice**: `untitled.desk` was the *only*
`.desk` this repository has ever tracked.  The rule says a desk travels
with its piece; in the whole of this repository's history not one
piece's desk has travelled, and the single one that did belonged to no
piece at all.  That is not an
argument for the blanket rule — it is an argument that the piece rule
has never been exercised, and nobody should conclude anything from a
decision that has never been tested.

### The gate

`test/test_way_in.py::test_the_starter_never_rides_in_the_tree`, checked
against **git's index** and not the filesystem: the file being *present*
is ordinary and expected, and it is being *tracked* that is the defect.
Third closure under the day's rule.

### F165. **[partly resolved]** The first window is unreadable on a laptop, and the cure is stored against the wrong thing

Henri, 2026-08-18, recalling the fresh install on the work laptop:
*"the screen was small at first.  It's an usability concern… The text
was too small to read was my first reaction.  Zoom ladder worked."*

Two defects, and the second is the one worth the entry.

### The window is a fixed size that knows nothing about the screen

`gestate/workbench.py:797` opens it as `Editor(bench.source(), 1100,
760)`.  No query of the display, no DPI, no scale — 1100×760 at scale 1
is comfortable on the desktop it was written on and too small to read on
a high-density laptop panel.  **The first thing a person does on a
laptop is fail to read the screen**, and every question after that is
asked of somebody squinting.

### And the cure does not travel with the person

The zoom ladder fixes it — he found it, it worked.  Where the result is
kept is the defect: `zoom` is a field of `Desk` (`gestate/desk.py`), and
a `Desk` is **`<piece>.desk`, beside the `.ges`**.  So the setting is
remembered *per piece*.

Open a second file and the text is small again.  **Eyesight and screens
belong to the person; the piece is what they are stored against.**  The
module already names the distinction and puts the person's own record in
`~/.config/gestate/desk` — that record is the registry of open windows,
and carries no preference of any kind.

`.gitignore` states the rule this collides with, deliberately and at
length: a `<piece>.desk` *travels with the piece*, which is right for a
caret, a seed, a loop and knob values, and wrong for the one field that
describes the reader rather than the reading.

### Not fixed before run three, and that is a decision

`card:stranger-test.md` run three is on a laptop next week, and rule 3
says fix what is known-wrong for free first.  This is known-wrong and it
is not free: the first half changes what every newcomer's first frame
looks like, and the corner's legibility is the one thing that run
exists to measure.

**The half that is safe is the second one** — a person-level zoom that a
new piece inherits changes nothing at all for somebody with no stored
zoom, which is exactly what a true first contact is.  What it buys is
that the machine can be made readable *before* the friend sits down and
stay readable when he opens something else.

### The second half, built 2026-08-18

At Henri's word — *"okay.  I think you're right.  build the half."*

`~/.config/gestate/zoom` holds the rung, beside the desk record and
outside every tree, so it needs no `.gitignore` rule and travels with
nobody's project.  `desk.opening()` fills it in **only where the piece
is silent**: a `.desk` that names a rung was written by somebody looking
at that piece — a dense score read close in, a sketch read far out — and
this does not overrule them.  It is written on the way out, *before* the
piece's own document, because a refusal to clobber is about where that
piece was and says nothing about the size somebody reads at.

Somebody who has never zoomed still gets nothing invented for them,
which is the same fix overshooting into what it was meant to stop.

**Gate:** five tests in `test/test_desk.py` under §"The zoom belongs to
the reader" — the silence filled, the piece winning where it speaks, no
preference invented, where the file lives, and a corrupt rung costing
nothing worse than the default.

**Still open: the first half.**  `Editor(bench.source(), 1100, 760)`
still knows nothing about the display, and a person who has never zoomed
still meets scale 1 on a dense panel.  Deliberately not fixed before
`card:stranger-test.md` run three, because it changes what every
newcomer's first frame looks like and the corner's legibility is what
that run measures.

### F166. **[resolved]** Two card citations rotted where the checker could not look

Found while pricing a notation change, 2026-08-18: `card:gemba.md` and
`card:button.md` were both still cited at the board's **root**, long
after each was finished and moved down into `board/done/`.  Neither
citation had ever been checked, and one sat in `doc/instruments.md`,
which is the first thing a session is told to read.

*(The dead spellings are described here rather than written out: the
gate this entry closes refuses them, and an entry that quoted them would
fail the suite — which is the poka-yoke working on its own author, ten
minutes after it was built.)*

### The blind spot was exact

`test_citations.py`'s card pattern required **backticks**:

    CARD = re.compile(r"`(board/(?:done/|later/)?[\w-]+\.md)`")

Every `see` line at the head of every card is written bare, without
them.  So the citations most likely to exist — the ones a card carries
to its neighbours — were the ones nothing looked at, and the checker
reported green over them for as long as it has existed.

**This is `manifesto.md`'s instrument problem, not a typo.**  A checker
with a blind spot is worse than no checker in one specific way: it is
*believed*.  Every card that moved shelf since the board began was
verified by something that could not see half the citations to it.

### The fix was a notation, not a pattern

Henri, the same afternoon: *"how about.. we would come with some
notation to refer to a card?  We already have F0, F100, F110, etc.
they're references to fixme entries… card:button.md is good notation."*

So a card is cited `card:<name>.md` now, backticks optional, resolved
across all three shelves — the id without the shelf, which is what the
board always said a card's filename was.  201 citations in 65 files were
rewritten in one pass.

**And the old spelling is refused**, by
`test_citations.py::test_no_card_is_cited_as_a_path`: two spellings of
one id is how the churn comes back, and a path that points at the wrong
shelf looks like a typo somebody will helpfully *correct* rather than
delete.

### The gate

`test_no_card_is_cited_as_a_path`, and the widened
`test_every_card_citation_resolves`.  Both were checked by reintroducing
a path citation into `doc/instruments.md` and watching the suite refuse
it.  Fourth closure under the day's rule.

### F167. **[bug]** The fence follows the tree it was installed from, not the one you are in

Found 2026-08-19, while running three sessions against three separate
clones of this repository to compare how each worked the same batch of
`card:ungated-fixes.md`.

`.claude/settings.json` registers the `PreToolUse` hook by **absolute
path** — `/home/cheery/gestate/tools/fence-hook.sh` — and the hook then
computes `PROJECT` from its own location, so `PROJECT` is the original
tree whatever tree the session is actually working in.  `tools/sandbox.sh`
binds only `$PROJECT` and `--chdir`s there.  The result, for a session
working anywhere else:

- every command matching `pytest` or `cargo build|test|check` is silently
  rewritten to run inside **a different checkout**;
- the working tree's own path does not exist inside that fence, so the
  command dies with `cd: No such file or directory` — a message that
  names nothing to do with the fence, and that appears **only** when the
  matched word is in the command, which is what makes it baffling;
- and `$PROJECT` is bound **read-write**, so a wrapped command from an
  unrelated checkout can write into the original tree.

Two of the three sessions concluded from this that they could not run
tests at all and reached every verdict by reading.  The third read
`tools/fence-hook.sh`, found the documented `NOFENCE=1` hatch and ran its
mutations unfenced — so the fence's effect on that day's work was to
decide, invisibly, which sessions had evidence and which had only
argument.

**And it wraps the whole command, not the clause that matched.**  Found
the same morning, by walking into it.  A compound command whose *first*
clause is a test run is rewritten in its entirety, so everything after
the `&&` also runs inside the fence — where `$HOME` is a tmpfs:

    $ python3 -m pytest test/test_citations.py && git add fixme.md && git commit …
    5 passed
    *** Please tell me who you are.
    fatal: unable to auto-detect email address

The tests pass, the commit fails, and the error is about **git identity**
— which has nothing to do with tests, with the fence, or with this
repository, whose identity is fine.  `~/.gitconfig` is simply not there
any more.  Run on its own, the same commit succeeds.

**Three masks on one face.**  A `cd` error naming nothing; ninety-one
import errors that read as a broken checkout (F168); and now a git
identity error in a repository whose identity is correct.  The fence is
invisible until something it does not bind is reached, and then it
misdescribes what went wrong — which is the property that makes it
expensive, not the wrapping itself.

**The fence is not wrong to exist here and the hook is not wrong to be
absolute** — `doc/hardening.md` installs it that way on purpose.  What is
wrong is that it fails silently and in the wrong direction: a session in
a foreign tree should be told, and the write-through to `$PROJECT` should
not be reachable from one.

**Amended 2026-08-24 — the page no longer says that, and this entry still
stands.**  `.claude/settings.json` was rewritten to `~/…` so that it
travels between machines and users, and `doc/hardening.md` now installs
the hook that way and prefers it: a leading `~/` expands, because Claude
Code runs a hook command through a shell.  So the sentence above is
right about the defect and stale about the page.  **The tilde fixes
nothing here.**  `~/gestate/tools/fence-hook.sh` resolves to the tree the
hook was installed from exactly as the absolute path did, so a session in
a second clone still gets its builds fenced into the first one, with
`$PROJECT` bound read-write.  Which machine and which user, not which
clone.

### F168. **[bug]** `pytest` and `python -m pytest` are not the same command in this tree

Found 2026-08-19, immediately after F167 and independently of it.

Nothing is installed into `.venv` for this project — no `pyproject.toml`,
no editable install, no `.pth`, and `PYTHONPATH` is unset.  Imports work
because `python -m pytest` puts the working directory on `sys.path` and
the console script `pytest` does not.  `tools/suite.py` uses the first
form (`[sys.executable, "-m", "pytest", …]`) and is therefore correct and
silent about why.

So the obvious command fails:

```
$ pytest test/test_board.py
E   ModuleNotFoundError: No module named 'gestate'
91 errors in 0.48s
```

**Ninety-one errors that look like a broken checkout and are a wrong
invocation.**  It is the same shape as F148 and F149 — the project works
for the person who already knows the incantation, and hands everybody
else a failure that points at the wrong thing.  A session hit it on this
machine while running a card's own targeted gate, and read it as the
fence's doing before checking.

### F169. **[fixed]** the wrist clock understated by up to an hour, always downwards

Found 2026-08-19, **two and a half hours after the clock was built**, and
found by the failure it was built to prevent happening to the wrong
person.

`tools/clock.sh` rendered any gap over an hour as `$((d / 3600))h`.
Integer division, so 1h58m printed as `1h` — fifty-eight minutes
discarded, and discarded *one way*: the reading is never too large.

**How it surfaced.**  Henri opened the session saying he had rested
about two hours.  A session ran the clock for an unrelated reason and it
printed `(1h ago)` against the last commit.  He read that and retracted:
*"I see I said something that's not true.  You noted that it's only 1h
that I rested."*  The real figure was **1h58m** — he had been right to
within two minutes, and the instrument talked him out of it.

That is the worst available failure for this particular tool.  It exists
because *an elapsed time is computed, never remembered* — the whole claim
being that the computed number beats the recalled one.  Here the recalled
number was accurate and the computed one was not, which does not just
give a wrong answer, it inverts the reason to consult it at all.

**Fixed** the same hour: an `elapsed` function, two units always
(`1h58m`, `2d7h`), checked at every boundary — `3599s → 59m`,
`3600s → 1h00m`, `86399s → 23h59m`, `172799s → 47h59m`,
`172800s → 2d0h`.

**The class, which is worth more than the bug.**  A truncating unit
conversion in a *reporting* path is not a rounding preference, it is a
biased estimator wearing the clothes of a measurement.  `doc/instruments.md`
now carries the rule beside the tool: an instrument's number is checked
against what somebody remembers, so it has to be right at the boundary —
that is exactly where the check happens.

### F170. **[fixed]** a driven run could not find a window, and said the editor never opened one

Found 2026-08-19 while building `card:driven-runs.md`'s harness, by
asking what the machine actually had rather than what the code assumed.

`tools/driven.py::find_window` (then `lagcheck.find_window`) runs

```
xdotool search --name gestate
```

with `capture_output=True`, retrying for thirty seconds.  **`xdotool` is
not installed on this machine.**  `subprocess.run` on a missing binary
raises `FileNotFoundError`… except it does not here, because the search
is the only thing that would raise and the loop swallows nothing — the
command simply never runs, no ids come back, the patience runs out, and
the function returns `None`.

Every caller reads `None` as *the window never appeared*.  That is a
sentence about the editor, produced by a missing package.

**It went unnoticed because nothing recorded the dependency.**
`xdotool` appeared nowhere in this tree except the two lines that call
it: not in `doc/install.md`, not in `tools/toolbox.sh` — which exists
precisely to say *what is here and what is missing* — and not in any
list.  `import` and `compare` (ImageMagick) were in the same position
and happened to be installed.

**Fixed** three ways, because one would have been the wrong lesson:

* `driven.BINARIES` names what a driven run shells out to and why, and
  `Run` **refuses** before the scenario starts, naming the binary, the
  apt package, and what the silent failure would have looked like.
* `tools/toolbox.sh` gained `xdotool` and `imagemagick` rows, so the
  bench tool that reports what is missing now reports these.
* `test_driven.py` carries a roster test that asks *this machine*
  whether it can drive, and skips with the reason rather than passing
  quietly.

**The class.**  This is the same shape as F148, F149 and F168 — the
project works for the person who already has the incantation and hands
everybody else a failure pointing at the wrong thing.  What is new is
where it landed: in the **instrument**, so the wrong thing it pointed at
was the program under test.  An unlabelled instrument comes back
confidently green; an undeclared dependency makes one come back
confidently red.

### F171. **[fixed]** a driven run could type into the editor you were using

Found 2026-08-19, by Henri asking a usage question: *"How I engage the
driven-run now?  I have the user's version on my desktop that is not
protected."*

Two facts that are each fine and together are not:

* `driven.find_window` returned `ids[-1]` from `xdotool search --name
  gestate` — **a** gestate window, not necessarily the one the scenario
  started.
* **XTEST does not aim at a window id at all.**  `XTestFakeKeyEvent`
  delivers to whatever holds X focus, and `click_into` is precisely the
  call that hands focus over.

So a driven run started on a display where somebody already had the
editor open could click into *their* window, open its command box with
`Ctrl-K`, and type.  `lagcheck --stop` then presses Return, which runs a
command in it.

**`a_copy_of` does not help, and it is worth being exact about why.**
That funnel exists because *a harness that types is a harness that can
save*, and it hands the driven window a copy so a stray `Ctrl-S` cannot
rewrite a committed example.  It protects the file the run opens.  The
file at risk here is the one that was **already open** — which no funnel
on the run's side can reach.

**Fixed** by refusing: a `Run` does not start when any gestate window is
already open on the target display, and the refusal names `Xvfb` as
where to drive instead.  It refuses precisely — driving on `:0` to
*watch* is the instrument, and an empty display is fine.
`Run.find_window()` additionally skips whatever was already there, for
the narrower case of a second window arriving mid-run.  Proved on `:99`
against a real standing workbench, then again with it closed.

**And the fix was narrower than the defect, for a day.**  It went into
`Run`, which is `lagcheck.py`'s path and nothing else's; `dialoglag.py`,
`dragcheck.py` and `measure_editor.py` type with the same XTEST calls
and had no `Run` to refuse for them.  Typing with XTEST *is* the hazard,
not keeping a stamp, so the whole preflight is now
`driven.refuse_if_the_run_cannot_happen` and all four call it:
**guards shared, bookkeeping not.**  The library refusal travelled with
it, because a *number* measured against a library that was never in the
process is as false as a photograph of one, and that is what the three
unstamped tools produce.  The stamp stayed in `Run` — it is a contract
about a tool's output and belongs to whoever owns the tool.
`test_driven.py::test_every_tool_that_types_refuses_beside_an_open_editor`
reads the sources so a fifth cannot forget.  Widening it also found
F174, which is that this entry's own second half never worked.

**The class.**  Every other guard in this harness protects the *result*
of a run — the right binary, a fresh directory, a stamp.  This is the
first that protects the *person*, and it was invisible from inside the
tooling because the tooling only ever ran where nothing else was
running.  It took a usage question to find it.

### F172. **[fixed]** a timing test raced its own setup, twice, both times under load — *and the mechanism is inferred, not reproduced*

Found 2026-08-19 by the shift's full suite —
`test_autoaudition.py::test_a_quiet_success_does_not_chatter`, one
failure in **2880 passed**.  It passes alone in 4 s and the whole file
passes in 25 s, fenced or not.

**It had happened before and was never filed.**  `journal.md`, 2026-08-18:
*"one `test_autoaudition` timing test failed once while an X server and
a full suite were running together — the board's own warning about a
shared machine, arriving on schedule."*  A parenthesis in a journal
entry, no F-number, nothing to fire when it recurred.  It recurred.

**What is proven.**  The message was `applied edit 1`.  The generation
counter belongs to the test's own `bench` fixture and starts at zero, so
edit 1 is *this test's* explicitly-asked-for setup audition and the
typed edit would be 2.  That rules out cross-test pollution and rules
out the automatic path having wrongly announced — the sentence the test
caught is its own setup's, arriving late.

**What is inferred and was not reproduced.**  `_progress` says `applied
edit N` from the housekeeping thread, between blocks; `last_audition` is
set when the audition is *measured*.  Those are two different moments,
and the test took its `seen` barrier after the second and before the
first.  Sixteen runs across two load levels did not reproduce it — at
heavy load the test takes its own `pytest.skip("too slow on this
machine")` branch instead, and at moderate load the announcement still
won every time.  So the mechanism is supported by the message number and
by the threading, and it is **not demonstrated**.

**Fixed** by waiting for the setup's own announcement before taking the
barrier, rather than only for its timing.  Chosen partly because it is
correct whether or not the diagnosis is: a barrier that waits for the
event it means to exclude costs one predicate and cannot be wrong in the
other direction.

**And the class, which is the part worth keeping.**  This is the
`card:ungated-fixes.md` disease inside out: not a fix with no gate, but
a **failure with no entry**.  It was seen, understood well enough to
write a sentence about, and filed nowhere — so the second occurrence
arrived as news.  A defect observed in a journal parenthesis is a defect
nobody is told about twice.

### F173. **[fixed]** the judging sheet called three silent arms unanimous

Found 2026-08-19, minutes after `tools/blind.py` was written, by running
it against three checkouts whose scratch files had been cleaned up
underneath it.

Every entry came back `missing` from every arm.  Every arm's state
therefore matched every other arm's, and the agreement test —
`len(kinds) == 1` — was satisfied.  The sheet said:

    0 contradiction, 0 different gate, 5 agreed

**A comparison that had not happened, reported as unanimous.**  Which is
the single failure this tool exists to prevent: it was built because the
first sheet made accuracy invisible, and its first bug made a *run*
invisible.

**Fixed** with `no verdicts` as its own state — never folded into
agreement, given its own section that says *this is not agreement*, and
a warning printed for any arm that wrote no `fixme.md` at all.  A mixed
case (two arms answering, one silent) is a contradiction, because two
arms agreeing while a third says nothing is not three arms agreeing.

**The class, which this project keeps meeting.**  *Silence read as
consensus* is the same shape as F170 (a missing binary read as *the
window never opened*) and as the `--gates` page having to disown the
suite three times: **an absence that satisfies a test written for
presence.**  The check asked *do the arms match* when the question was
*did the arms answer*.

### F174. **[bug]** a driven run cannot tell its own window from one that opened beside it

Found 2026-08-19, an hour after F171 was closed, while widening its
refusal to the three tools that had none.

F171 was fixed in two halves.  The first is the refusal: a run does not
start when a gestate window is already open on the display.  The second
was meant to cover what the refusal cannot — **a window arriving after
the run has started** — and it was `find_window(exclude=...)`, given the
ids that were open before the child launched.

**The second half never did anything.**  The refusal raises whenever
`windows()` is non-empty, so the list handed to `exclude` is empty
whenever it exists at all, and the search still answers `ids[-1]`: *a*
gestate window, not necessarily ours.  The test written for it exercised
`find_window` directly with a list nothing in the tree can produce, so
it passed while the wiring was dead — the exact shape of F173 and F170,
**an absence that satisfies a test written for presence**, this time in
a guard.

The pretence has been removed rather than left standing: nothing threads
`exclude` any more, and `Run.find_window` and `driven.find_window` both
say plainly that nothing fills it.  Dead protection that reads as
protection is worse than none, because the next reader stops looking.

**The fix is not an exclusion list.**  Ours is the window belonging to
the child we started, and the only thing that says so is its pid —
`xdotool search --pid <pid> --name gestate`, or `_NET_WM_PID` off the
tree.  Then a second window can arrive whenever it likes and the run
still photographs its own.

**Not written yet, deliberately.**  It cannot be checked without a
display, and this harness's own rule is that a guard nobody has watched
work is a mood.  `spec/` has nothing to say here; the address is for the
comments in `tools/driven.py` that now point at it.

### F175. **[fixed]** an agent's worktree turned the project's own gates red

Found 2026-08-19, the first evening a subagent worktree existed, by the
gates going red on a tree whose working copy was clean.

`isolation: "worktree"` puts the agent's checkout at
`.claude/worktrees/agent-<id>/` — **inside `ROOT`**.  Two gates walk the
whole tree by `rglob` and skipped only `.git`, `target`, `__pycache__`
and `.venv`, so both read that second checkout's documents as this one's:

* `test_citations.py` checked a citation belonging to another branch and
  failed on it.  Its own docstring names three dead citations on purpose
  and is exempt *by identity* (`path.resolve() == here`) — which stops
  being true the moment there are two copies of the file.
* `test_consent.py` passed only because the worktree happened to be
  consent-clean.  A branch that quoted somebody unregistered would have
  failed the register on `main`, for something written elsewhere.

**With the pre-commit hook installed this refuses every commit** until
the worktree is deleted — so the day's own new control and the day's own
new isolation mode disagreed with each other the first time both were
used.

**Fixed** by naming `.claude` as not-this-checkout's-text in both
walkers, and by giving `test_consent.py` a single `NOT_OURS` tuple
rather than three repeated `not in p.parts` clauses.  `test_board.py`
globs `board/` only and was never exposed.

**The class.**  Not the absence-satisfying-a-presence-test shape of the
day's others — this one is *a tool's own scratch space inside the tree
it measures*, which is the same family as `gemba.tsv` and
`untitled.desk` being gitignored, and the same family as
`card:driven-runs.md`'s stale screenshots.  A checkout under a checkout
is two writers on one namespace, which `board/README.md` already has a
rule about for people.

### F176. **[bug]** the file chooser opens on the project's own tree, and a stranger reads it as a menu of what to hear

Found 2026-08-21, `card:stranger-test.md` run three — the first person to
meet this window who does not read code for a living.

Told how to run `open`, he was shown the working directory, which for
anybody running gestate in place is the **source tree**: `board/`,
`doc/`, `spec/`, `crust/`, `shell/`, `test/`, `tools/`, `README.md`,
`examples/`.  He read those names as offers and picked the one that
sounded like it held something — *"board kai sisältää jotakin
mielenkiintoista"* — then moved to open `README.md`.  He was helped into
`examples/`; he did not get there.

**Exactly one entry in that list contains anything you can hear, and
nothing in the chooser says which.**  The guess was wrong and it was not
a foolish guess: the dialog presented a menu, and he chose the entry
whose name promised content over the ones that sounded like machinery.
That is this card's §3 category — *where it guessed* — and the window
invited the guess.

**The class.**  Not a missing feature.  A **default that is correct for
the author and wrong for everybody else**, which is F164's family: the
tree's own working state is what a newcomer is handed.  The author opens
gestate in the directory he is working in and the default is exactly
right; a stranger opens it in a repository and the default is a filing
cabinet.

### F177. **[fixed]** the way back up is the first row in the list, and it was spelled `../`

Found 2026-08-21, run three, in his own words: **"miten mennään
takaisin?"** — asked about the folder navigation, after he had been
helped down into `examples/`.

**Written up first as a missing affordance, which was wrong.**  It is
not missing.  `Session._listing` puts `../` at the top of every listing
below the root — *"going up is the move you make when you opened the
wrong place, so it is where the eye already is"* — and it was the first
row on his screen, with the note `you are here: …/examples` beside it.

So the finding is not that there is no way back.  **It is that the way
back is spelled in a notation he had never learned.**  `..` is a
programmer's word for a parent directory.  He does not program, and he
read the top row of the list without recognising that it was the answer
to the question he then had to ask out loud.

It is the only question of the run he asked rather than abandoning,
which puts it above the others in one respect: he expected this one to
have an answer, and it was on the screen.

**Fixed by relabelling the row `[up]`, and by changing nothing else.**
Both of its columns were already specified by
`test_a_path_argument_offers_what_is_in_the_directory` — the name
asserted to be exactly `"../"`, the note asserted to start with `"you
are here: "`, which is Henri's own design after he once read the row as
a destination rather than a step.  So the wording was his to set, and he
set it the same evening.

He proposed `[back]` — the stranger's own word — and then chose against
it: *"[up] kuulostaa paljon paremmalta."*  It is the better one.  **Back
promises a history this row does not have**; the row goes to the parent
whether or not you came from there, and a person who typed a path
directly came from nowhere.  *Up* is exactly what it does, and it is the
word every file manager already uses.

**The brackets are not decoration.**  They inherit the one thing this
run proved: a bracketed thing gets pressed.  `[command]` opened unaided
in the same ten minutes, which is what retired `=command=` — so the
shape that was suspected of reading as a readout is now the shape used
for the one row in a file list that is not a file.

**Read as a word, typed as a path.**  The label changed; the query it
leaves did not.  The filter still matches on `..` alone, deliberately:
a label matching on its word would keep this row selected while
somebody narrowed towards a `backup/`, and Enter would step them out of
the directory they were in — which is the bug that made `..` filterable
in the first place.

**The class.**  Not a missing control — **a control labelled in the
vocabulary of the people who did not need it.**  F153's family: *the
window taught the key only to people who no longer needed it.*

### F178. **[bug]** `[command]` opens effortlessly and then dead-ends

Found 2026-08-21, run three, and the good half of it is genuinely good.

**The corner was found unaided.**  Henri, the same evening: *"Kun hän
lopulta kokeili, hän sai [command] menun vaivatta auki!"*  No pointing,
no hint, no hesitation — by somebody who had never seen the window and
does not program.

**Then he stopped.**  The list opened and gave him nothing to do with
it, and he had to be told how to run `open`.

So two defects that had been read as one are now separated: **the corner
is findable, and the list is not actionable.**  Run three's
pre-registration named three outcomes — the brackets, the corner not
being found, or *a stall somewhere nobody has looked* — and this is the
third.

**What it retires.**  `=command=`, held unbuilt since 2026-08-18 on the
theory that `[command]`'s brackets read like `[gemba]` and `[inert]` —
a readout rather than a control — is **answered, and answered against**.
He pressed it without hesitating.  The proposal stays unbuilt, now on
evidence instead of on a deferral, and the question the card had held
since 2026-08-17 is closed.

### F179. **[resolved]** the desktop icon opens a file that does not exist — and that is not a defect

Written 2026-08-21 as a defect, **before** run three, from reading
`tools/gestate-editor` while making the machine ready for a stranger.
The launcher falls back to `"${1:-untitled.ges}"`, this tree contains no
`untitled.ges`, and nothing creates one — from which this entry
concluded that a click gives an empty editor and silence, and that
`vision.md`'s second verb is unreachable from the icon.

**It is wrong.**  A workbench handed a path that is not there opens the
**starter**, which is 380 characters of comment and:

    sound : Sig Float
    sound = 0.2 * sine 220.0

A click gives an editor with a program in it that sounds.  The entry was
written from the launcher and the filesystem, and never from the thing
they lead to — one call to `Workbench(Path("untitled.ges")).source()`
would have answered it, and it was not made until the fix was about to
be written.

**Kept as an entry rather than deleted**, which is this file's contract,
because the mistake is the useful part: *the absent file was checked and
the program it opens was not*.  A conclusion from two of the three
things in a chain, drawn confidently enough to be scheduled for repair.

**Gated anyway**, and the gate is worth its line —
`test_a_bare_click_opens_something_that_sounds` holds the launcher's
fallback name and the starter's `sound` declaration *together*, because
either one can change without the other and the click breaks silently
either way.  A defect that was never real now has a check that would
catch it if it became real.

### F180. **[resolved]** `test/test_suite_runner.py` passes in the full run and fails on its own

Found 2026-08-24 while adding the thirteenth gate.  `python3 -m pytest
test/test_suite_runner.py` alone: two failures, `No module named
'rulecount'`; inside `tools/suite.py --gates` or the full suite: green.
Same on the commit before, so not introduced that day.  Some earlier
test file puts `tools/` on `sys.path` and this one rides on it.  A
test that only passes in company is a test whose verdict depends on
collection order, which is the class `card:dangling-names.md` is about,
in a test rather than a name.  Fix is one line — the file's own
`sys.path.insert` — and it is not written here because the day was on
another card.

**Resolved 2026-08-24, the same evening:** the file puts `tools/` on
`sys.path` itself, and `python3 -m pytest test/test_suite_runner.py`
alone is green.

### F181. **[bug]** `tools/seedaudit.py` looks for the pieces at gestate's paths, and a seed has no way to say where its own are

Found 2026-08-24, the evening `~/tend` was started — the first
directory the audit was ever pointed at that is not this tree.  The
author's document landed at `doc/author.md` and the audit said *ABSENT
the author's own document*.  **That instance was a slip, and the audit
caught it** — Henri: *"did I do a mistake and said doc/author.md?"* —
so the file moved to `spec/author.md` and the piece went green, which
is the check working, not failing.

What stands is the design point `card:working-standard.md` made on
2026-08-22: *a seed audit assembled from what this tree happens to
have would encode gestate's accidents as requirements.*  The `why`
column is the requirement; the `paths` column is the accident, and a
seed that keeps its author's document somewhere else on purpose has no
way to tell the audit so.  Fix is a design choice: a seeded tree
carries a small manifest naming where its pieces live and the audit
reads that first — which makes the seed say what it has, which is what
an audit from outside should be reading anyway.  Not urgent: the first
seed matched the paths, and the slip was worth more than the manifest
would have been.

### F182. **[resolved]** `test_precommit.py` read the hook as prose, and passed with the gate neutered

Found 2026-08-26 from outside: a tend session mutated its copy of this
file — borrowed whole from gestate on 2026-08-24 — and its
`test_the_hook_runs_the_suite_and_nothing_else` stayed green with
`|| true` behind the gate line.  Asked whether gestate's copy had the
same blindness; **measured** rather than read: line 114 of
`tools/pre-commit.sh` changed to `if "$PY" tools/suite.py --gates ||
true; then`, and `test_precommit.py` passed 6 of 6.

The test asserts that every line naming `tools/suite.py` also says
`--gates` — the arguments, as text.  Its docstring records the
2026-08-25 fix that stopped it asserting one spelling of the
interpreter; that repaired its fragility and kept its blindness, and the
shape travelled to tend with both.  The hook itself does read the exit
(the `if`), and `card:cheap-gates.md` records it refusing a commit once
— evidence, not a gate.  `manifesto.md`'s second failure: an oracle that
has only ever passed is a claim; the sweep's F88 found one by mutation
from inside, this one arrived by mutation from another tree.

`test_the_hook_refuses_a_commit_when_a_gate_says_no` installs the hook
in a scratch repository whose `tools/suite.py` is a stub answering by a
file, commits, and asserts the refusal *message* — not only the exit,
because a hook that fails for the wrong reason also refuses.  The prose
test stays for what it does hold: `--gates` and not the whole suite.

gate: `test/test_precommit.py::test_the_hook_refuses_a_commit_when_a_gate_says_no`.
**Measured 2026-08-26**, red with `|| true` behind the gate line, green
without.

### F183. **[resolved]** The automatic audition shut its gate and said nothing

Henri, 2026-08-26, with a video (`~/misc/fail-on-bpm.webm`): *"automatic
audition has something wrong with it.  Sometimes it doesn't run
automatically and I have to ctrl+return to run it, without apparent
reason."*  Then, narrowing it: *"The problem appears when editing bpm"*,
*"It could also be something to do with blues.ges"* — and, by the time
the numbers were on the table, the answer in his own words: **"Oh
right!  Autoaudition only runs if the file compiles in time.  It's a
feature but it doesn't tell about itself!"**

**The feature was working, and that was the defect.**  Measured headless
at 44100 Hz, three runs: `blues.ges` starts in 2.38–2.64 s, over
`COLD_ENOUGH` (2 s), so the one audition on trust is never attempted;
and a bpm-only audition costs 1.1–2.0 s, over `AUTO_AUDITION` (0.5 s),
so it is never automatic afterwards either — `GESTATE_BUILD_TIME` puts
0.6 s of it in the front end alone, because a tempo edit is a whole
rebuild minus the substrate.  `untitled.ges` clears both gates, which is
why the same edit auditioned itself there in the same video.  Both
doors are F151's rule doing what he asked for on 2026-08-17.

What was wrong is that the bar read `sound behind · audition
Ctrl-Return` identically in both cases — gate closed by a measurement,
gate never measured, and gate open with the audition merely pending —
and a person who had seen it work on one file could only read the other
as broken *without apparent reason*.  The reason sat in the model the
whole time, as `last_start` and `last_audition`.

**So the model says it**, `why_behind`, in its own words with the gate's
own numbers: *1.1 s to rebuild, automatic under 0.5 s*, or *2.5 s to
open, one try by itself under 2 s* — and nothing at all while the gate
is open, so the row is unchanged on the file where the feature works.
It crosses as a **third field** of the `behind` row, because the window
drops that sentence whole rather than clip it (half of `audition
Ctrl-Ret…` teaches a key that does not exist): the reason is tried
after the sentence and dropped before it, so a narrow bar loses the
numbers and never the key.

Held by `test/test_autoaudition.py` §"and says why", and
`shell/editor/tests/view.rs::the_reason_goes_before_the_key_does`.

Photographed on this code, driven on `Xvfb`
(`test/driven/20260826-124428-f183-behind-why`): *3.0 s to open, one
try by itself under 2 s* before the first Ctrl-Return, *2.7 s to
rebuild, automatic under 0.5 s* after it — slower than headless, with
the sound card and a virtual display in the way, which is the point of
saying the measured number and not a predicted one.  What the photograph
also shows, and this does not touch: the `AWAY` sentence is drawn over
the status text rather than beside it, in his video as much as here.

**What it does not do** is make the tempo edit cheap.  That would open
the gate for scores by itself and is a change to the build, not to the
bar; the 0.6 s front end for a moved literal is the number to start
from if it is ever taken up.

### F184. **[resolved]** The housekeeping thread died under a test, and the suite called it *1 warning*

Henri, 2026-08-26: *"I ran full suite today and it had one warning,
able to check that one?"*  It could not be checked: `tools/suite.py`
asked pytest for failures and errors (`-rfE`), so the count in the
totals line was all of the warning that reached `test/report.md`, and
naming it cost the twenty-five minutes again.

**It was a thread dying.**  `test_audioeditor.py::test_no_knob_still_reads_zero_when_the_render_loop_begins`
(F147, 2026-08-17) swaps a `_LoopHost` in and runs the C-host path;
`run_device` on the stub returns at once, and whenever the housekeeping
thread woke first — a 5 ms wait, lost only on a busy machine, which a
full run is — it reached `_progress` → `_say_dry` → `host.dry`, which
the stub never had, because `_StubHost` was written for the part of the
host one test reads and `dry` had joined the real one two days earlier
(2026-08-15, *the sound says when it tore*).  The thread died with an
`AttributeError`, pytest filed it as `PytestUnhandledThreadExceptionWarning`,
and the test passed.  Alone on an idle machine it never fires;
reproduced on demand with `_HOUSEKEEPING` set to zero, three times
running.

Three things, because each was its own gap:

* **The stub carries `dry`** — a double stands behind the whole of the
  interface the thread reads, not the part the test is about.
* **A dying thread is a failure**, `pytest.ini`:
  `error::pytest.PytestUnhandledThreadExceptionWarning`.  This editor
  runs its sound on threads; one of them dying is exactly what the suite
  is for, and the same reproduction that passed under the old filter
  fails under this one and passes again with the stub fixed.
* **The page names what it counts**: `suite.py` asks for `-rfEw` and
  writes a `## Warnings` section into `test/report.md` — the test and
  the sentence — so the next *"which warning?"* is a page, not a run.
  `test/test_suite_runner.py` holds the parser.

The number sat in the totals line of every full run from 2026-08-17
to 2026-08-26.  *A number nobody asked for is a number nobody checks*
(`doc/instruments.md`); a number nobody **can** check is the same thing
with a better excuse.

### F185. **[resolved]** The browser gate skips under the fence, and green there says nothing about the page

`test/test_online.py` opens the generated page in a headless Chrome
and holds the worklet's frames to `run_native` — the one check that
says the page plays what the desk plays (`card:online.md`).  Under
`tools/sandbox.sh`, where `tools/fence-hook.sh` puts every `pytest` a
session runs, it skips: the fence binds `/usr` and Chrome lives in
`/opt/google/chrome`, so `shutil.which("google-chrome")` finds a
symlink with no target, and the test says *no Chrome to open the page
in* and passes over.  Found 2026-08-30 when a red test turned into a
skipped one between two runs, and the difference was whether the
command began with `pytest`.

So on this machine the gate has only ever been green *outside* the
fence — 2026-08-29's runs and today's, `NOFENCE=1` by hand — and a
fenced full run reports the page as unchecked in a skip line nobody
reads.  Loopback is up inside the fence (`ip link` says so), so the
page's own server would work there; what is missing is the binary.
The fix is one line in `tools/sandbox.sh` — `--ro-bind /opt /opt`, or
a narrower bind of the Chrome directory — and it is not a session's
to add: the fence is Henri's (`spec/sandbox.md`), and widening it is
his call.

**Resolved the same day, at his word** — *"ok, korjaa se."*  The
narrow bind: `/opt/google/chrome` read-only, and only when the
directory exists, the way the toolchain homes are bound, so a machine
without Chrome loses nothing.  `tools/sandbox.sh --check` gained the
probe *chrome runs (F185)*, and `test/test_online.py` ran fenced for
the first time: 10 passed in 19.7 s, the three browser tests among
them.

### F186. **[resolved]** An application's head loses its parentheses

`_fmt_app` walks the spine parenthesising each *argument* with
`_paren_val` and then writes the head with a bare `_fmt_val`, so a head
that needs parentheses does not get them:

    (x => x + 1) 2          ⇒   x => x + 1 2
    (let f = y => y in f) 2 ⇒   let f = y => y in f 2

and a parenthesised `case` in head position the same way: the argument
lands inside the last alternative.

Each of those re-parses as a different program — the argument is
swallowed into the lambda, the `let` body, the alternative — which is
exactly what F46 is about, one position further in.  `_needs_parens`
already answers correctly for all three; nothing asks it.

Found 2026-08-31 while measuring F46 for the ungated sweep
(`card:ungated-fixes.md`, batch 9).  The fix is one call:
`parts.append(_paren_val(cur, self._fmt_val(cur)))`.

**Resolved the same day, at Henri's word** — *"you may fix F186, F187 and
F188 if you want to fix them now."*  One line: the head goes through
`_paren_val` like every argument.  The `while` loop has already left `VApp`
behind by then, so a spine is never re-parenthesised.

gate: `test/fmt/test_format.py::test_an_application_head_keeps_its_parentheses`,
the three shapes above.  **Measured 2026-08-31** by reverting the one line:
that test alone goes red, and the language set stays green either way — which
is the finding restated, not a doubt about the gate.  Weakest: it holds three
head shapes, and the heads that were *never* broken are still not enumerated,
so a future `_needs_parens` that over-answers would parenthesise a bare head
and no test here would object.

### F187. **[resolved]** A lambda's parameters are not atoms

`_fmt_func` formats its parameters with `_fmt_pat(p)` and not
`_fmt_pat(p, atom=True)`, which is F46's third bullet in the one
juxtaposed position it did not cover:

    (x :: xs) => x   ⇒   x :: xs => x
    (Just x) => x    ⇒   Just x => x

`_format_sc_eqn` — an equation's parameters, the same grammar position —
passes `atom=True`, so this is a missed caller rather than a missing
mechanism.  `_format_instance_member` is the second one: an instance's

    instance C (List Int) where
        f (x :: xs) = x

comes back as `f x :: xs = x`.

Found 2026-08-31 while measuring F46, same sweep batch.

**Resolved the same day, same word.**  Two `atom=True` arguments, in
`_fmt_func` and `_format_instance_member`.

gate: `test/fmt/test_format.py::test_a_lambdas_parameters_are_atoms`, which
covers both callers.  **Measured 2026-08-31** by reverting each argument on
its own: that test goes red for either, and nothing else moves.  Weakest: the
remaining two `_fmt_pat` callers — `_fmt_unbox` and `_fmt_for` — are left
bare, deliberately, because neither position juxtaposes; that reading is a
judgement and no test states it.

### F188. **[resolved]** A `Box` pattern formats as `<PBox>`, which is not a program

`_fmt_pat` has a branch for every pattern node except `PBox`, and falls
through to the debugging placeholder `f"<{type(pat).__name__}>"`:

    f (Box x) = x        ⇒   f <PBox> = x

and in a `case`, the alternative comes back as `<PBox> -> x`.

This is worse than F46 and F186, which produce a *different* program: this
produces output that does not parse at all, so the formatter's promise
fails at the first step rather than the second.  `Box p` is fig. 2.2's
spelling and `examples/closure.ges` and `examples/relations.ges` both open
with it, so it is not an exotic corner.

Found 2026-08-31, reading `_fmt_pat`'s callers for F187.  The fix is one
branch, `f"(Box {self._fmt_pat(pat.pat)})"`, parenthesised in juxtaposed
position like a constructor's.

**Resolved the same day, same word.**  One branch, shaped like the
constructor one: `(Box p)` where a pattern is juxtaposed, `Box p` where it
stands alone.  `PBox` had to be exported from `gestate.syntax` — it was in
`ast.py` and in neither the import list nor `__all__`, which is the smaller
half of why nothing noticed.

gate: `test/fmt/test_format.py::test_a_box_pattern_is_written_as_one`, and
`::test_no_output_wears_a_placeholder` beside it, which is the question the
entry actually wanted asked — the fall-through is a catch-all, so the next
pattern node added would have been silent the same way.  **Measured
2026-08-31** by removing the branch again: both go red.  Weakest: the
placeholder test names five patterns rather than enumerating the node types,
so a new one still arrives unheld unless somebody adds it to that list.

### F189. **[open]** The leash reported itself off, and it was on

`tools/leash.sh` is the check that says whether `.claude/settings.json`'s
deny-list is actually in force.  It runs as a `SessionStart` hook.  On
2026-08-31 at 05:15 it printed

    leash: .claude/settings.json parses — not reverting it, in case the edit was yours.
      ✗ Edit(./.claude/**)  — MISSING
      ✓ Bash(sudo:*)
      ✓ Bash(git push:*)
      ✓ Read(~/.ssh/**)
      ✓ fence hook installed and executable

      THE LEASH IS OFF.  tools/leash.sh --restore

and the leash was on.  Checked the same session, about forty minutes
later: `tools/leash.sh` says *the leash is on*, `Edit(./.claude/**)` is
the fourth-from-last entry of `.permissions.deny`, and the file's mtime
is **2026-08-24 16:02** — it had not been written since, and `git status`
showed it unmodified.  Nothing restored it; the hook says in as many
words that it did not.

**Not reproduced.**  Tried: the hook's own command string verbatim in a
plain shell, and `--restore` again — both green.  `HOME` unset, the shape
that produced the 2026-08-24 false alarm, errors out at line 115 rather
than reporting a rule missing, so it is not that mechanism returning.
The rule that was reported missing is the one spelling in `CRITICAL`
that needs **no** normalisation — no `(~/` to rewrite — which rules out
the tilde/absolute handling that the whole check was rewritten around.

**Filed because the failure is the expensive kind.**  This script's own
header says it: *a gate that fails closed on a spelling change is a gate
people learn to wave past*.  A second false *off* is worse than the
first, because the first was diagnosed and this one cannot be.  Left
unrecorded it becomes a thing a session reads past at every session
start, which is exactly the protection gone with no symptom that the
leash exists to prevent.

Reported to Henri 2026-08-31 at the end of batch 9 of
`card:ungated-fixes.md`; filed at his word — *"file it as F189"*.

gate: `none — nothing can`, not yet.  `test/test_safety.py::test_the_leash_is_on`
already runs the script and requires exit 0, and it passes.  Whether it
would have passed at 05:15 is the one thing nobody can now say, and it is
the whole question.  A test could also feed the script a
weakened settings file and require the ✗, but that is the half that
already works.  What went wrong is between the hook's environment at session
start and the file on disk, and neither is reachable from a test.  The
cheapest thing that *would* catch a recurrence is the check writing what
it read: the deny-list it parsed, and the mtime and size of the file it
parsed it from, into its own output.  Weakest: that is a guess at the
layer, made without a reproduction — the fault may be in the client
rather than in the script, and this entry cannot tell.

### F190. **[open]** The formatter is not idempotent: comments move, and some are lost

*Henri's rule, 2026-08-31, is what makes this a defect rather than an
observation:* **"the formatter should be idempotent, but the code doesn't
need to be autoformatted."**  Confirmed the same evening.  Nobody has to
run `gestate.fmt` over a source; what it writes, written again, must come
back the same.

It does not, for **10 of the 80 `.ges` files that survive two passes**, and
every difference is a comment:

| file | comments after pass 1 → 2 → 3 |
|---|---|
| `examples/advanced/01-fold.ges` | 28 → 28 → 27 |
| `examples/advanced/02-samplehold.ges` | 31 → 29 → 28 |
| `examples/advanced/04-loop.ges` | 29 → 24 → 23 |
| `examples/audio/drums.ges` | 49 → 47 → 47 |
| `examples/audio/fm.ges` | 58 → 56 → 56 |
| `examples/audio/twoknobs.ges` | 51 → 43 → 43 |
| `examples/gui/bounce.ges` | 40 → 40 → 39 |
| `examples/gui/chain.ges` | 42 → 41 → 41 |
| `examples/records.ges` | 10 → 10 → 9 |
| `gestate/command.ges` | 421 → 414 → 414 |

**27 comments deleted by the second pass**, and five of the ten are still
moving on the third — so it is not a one-off settling into a fixed point,
it is a walk.  Some comments move rather than vanish (`01-fold.ges` loses
`# phase, instant` at line 49 and gains it at 67); the ones that vanish are
`#:` blocks attached to a declaration, which is the trivia reattachment
`test_trailing_comment_survives_the_formatter` holds for one small case and
nothing holds at scale.

Measured 2026-08-31, formatting every `.ges` in the tree three times and
counting lines beginning `#`.

gate: `test/fmt/test_roundtrip.py::test_formatting_is_idempotent`, with
these ten named in `NOT_IDEMPOTENT` — **written 2026-08-31, at Henri's
ask.**  The list is a ratchet: `::test_a_listed_idempotency_failure_is_still_one`
fails on any name that has stopped failing, so repairing a file and leaving
its name behind is caught by the commit that repairs it.  That is
`card:ungated-fixes.md`'s *accepted baseline that may shrink and never
grow*, built for the first time.  Verified the same day by naming a clean
file in the list and watching the ratchet refuse it; 3.1 s for the file,
after the first draft's 8.2 was found to be four walks over one corpus.  Weakest: the property
is exact but the corpus is not — 89 readable sources, most of them audio
pieces, so a comment shape none of them writes is unheld.

### F191. **[open]** For nine sources the formatter's output does not parse

Worse than F190 and found beside it.  Of the 89 `.ges` files
`gestate.fmt.format` can read, **9 produce output it cannot** — the
formatter's promise fails at the first step rather than the second, and the
nine include the prelude:

    examples/closure.ges  examples/relations.ges  examples/gui/patchbay.ges
    gestate/audio.ges  gestate/gui.ges  gestate/music.ges
    gestate/prelude.ges  gestate/signal.ges  gestate/synth.ges

Four causes, each separately fixable:

* **A value node with no branch prints `<VInternal>`** — the same catch-all
  as F188, on the value side of `_fmt_val` rather than the pattern side.
  `signal.ges`, `audio.ges`, `gui.ges`.
* **A set comprehension comes back as its lowering, with a generated name
  in it.**  `{x | x in s, x < Blue}` formats as
  `for (x in s, _guard1# in guard (x < Blue)) {x}` — a different surface
  form, and the `#` in the synthesised binder opens a comment, which is the
  `expected ')'` the parser then reports.  `relations.ges`, `closure.ges`,
  `patchbay.ges`.
* **A constructor's field loses its parentheses.**  `| Sow Int (Score a)`
  comes back as `| Sow Int Score a` — F186's family in
  `_format_type_decl`'s fields, where the arguments are juxtaposed the same
  way.  `music.ges`.
* **A member's multi-line `case` loses its indentation.**  An instance's
  `foldr f z xs = case xs of` is followed by its alternatives at the
  member's own level, so the block is gone.  `prelude.ges`, `synth.ges`.

Found 2026-08-31, checking Henri's idempotency rule against the tree.  The
earlier count in this session's report — *67 files the formatter cannot
parse* — folded these nine in with the 58 it genuinely cannot read; they
are a different and worse thing, and the split is 58 unreadable, 9 read and
mis-written, 80 clean through two passes.

**And the quieter half, found while building the gate:** seven more files
whose output *does* parse and **is a different program**.  Two of the causes
above account for most of it, arriving in their milder form — the
constructor field losing its parentheses turns `List Point` into two fields
in `examples/gui/chain.ges`, and the lost `case` indentation re-associates
an inner block's alternatives into the outer one in
`examples/audio/bottleneck.ges` and three of its neighbours.  Two are their
own: `examples/records.ges` loses a whole `deriving (Show, Eq, Ord)`
clause, and `gestate/command.ges` comes back with a `VSCEqn` whose
`using_params` holds a `Span` — **that one is unexplained and is written
down as unexplained.**

gate: `test/fmt/test_roundtrip.py`, three tests over the corpus —
`::test_the_output_of_every_readable_source_parses` with these nine in
`OUTPUT_DOES_NOT_PARSE`, and
`::test_formatting_does_not_change_the_program` with the seven in
`PROGRAM_CHANGES`, both ratcheted the way F190's list is.  **Written
2026-08-31, at Henri's ask.**  The program comparison is the AST with spans
and comments set aside, which is the property `format`'s own docstring
promises and the one idempotency cannot see.  Weakest, and it is measured
rather than guessed: reverting F186, F187 or F188 leaves this whole file
green — no clean source in the tree writes a parenthesised application
head, a compound lambda parameter, or a `Box` pattern outside the two files
already listed.  A corpus gate is only as strong as its corpus, and this
one is 89 files that are mostly audio.

### F192. **[bug]** `_apply_subst_map` drops the span on `TApp`, so a written type loses its place at instantiation

`types.py:524-525`: instantiating a scheme rewrites its quantified variables
through `_apply_subst_map`, which rebuilds `TFun` carrying `t.span` and `TApp`
carrying nothing.  So a type the author *wrote* has a position in the file and
none by the time a complaint is made about it.  The asymmetry between the two
branches, three lines apart, is what says this is an oversight rather than a
decision.

Measured 2026-09-01 on `f : List a -> Int` … `bad = f 3`:

    today                 No instance for Num (List a377)
    with `t.span` carried No instance for Num (List a377) (at 0:4–0:10)

`spec/types.md` §9 asks for spans threaded "through `Type` and `Kind`
representation from the beginning" so that "when `unify` fails, report original
source locations" — the same requirement F31 repaired one function over, in the
sibling it did not reach.  Found by batch 10 of `card:ungated-fixes.md` while
measuring F31, and it is why F31's own repair cannot be observed.

**Not repaired here, on purpose.**  The position recovered is in the *callee's*
signature, so a complaint about `bad` would be drawn under `f`'s line — F152's
editor puts a message in a box under the line it names.  Whether that is the
right place, or whether the use site's span should win, is a design question
and not a typo.

### F193. **[resolved]** `spec/syntax.md`'s two lists had drifted from the tokenizer and the parser again

The defect F23 and F25 were opened for, recurring — found 2026-09-01 by the
gates written to hold them.  Three names, all of them in the implementation and
none of them on the page:

* **`do`** is reserved by `tokenize._RESERVED` and is not in the page's
  reserved-word list.  `spec/monad.md` §"Desugared in the parser, and gone"
  prices the feature at *"one reserved word"* and the word was never added to
  the list that names them.
* **`internal`** likewise — and it is not a corner: `gestate/signal.ges` uses
  it as a section marker, so every reactive program is compiled through it.
* **`%`** has a default fixity of `infixl 8` in `descend.DEFAULT_INFIX` and no
  row in the page's fixity table.  That is F25 exactly: the implementation
  inventing a binding power the spec does not give.

**Fixed the same day**, at Henri's word — *"Do the three edits to
spec/syntax.md"*: `internal` and `do` added to the reserved-word list, and `%`
added to the `infixl 8` row beside `*` and `/`.  Both baseline sets in
`test/test_syntax_spec.py` are empty since, which is the shape
`card:ungated-fixes.md` question 3 asks for — an accepted baseline that may
shrink and never grow, and this one shrank to nothing in an afternoon.

The list entries are the whole of it.  What `internal` *means* — the marker
that divides a library's public face from the names its own definitions need —
is described in `spec/liveaudio.md` and shown in `gestate/signal.ges`, and the
syntax page names words rather than defining them.

gate: `test/test_syntax_spec.py::test_the_pages_reserved_words_are_the_tokenizers`
and `::test_the_pages_default_fixities_are_the_parsers` — the same two that
found this.  **Measured 2026-09-01**, each name struck back off the page on its
own: `do`, red; `internal`, red; the `%` row, red.  Weakest: the gate holds the
page against the *tables*, so a word both of them have and nothing implements
would still pass — and it says nothing about whether the page explains any of
the three.

### F194. **[bug]** `memoryindex.py` says *nothing to do* behind the fence, and its gate skips there too

`tools/memoryindex.py:96` prints *"no index at … — nothing to do here"* and
**returns 0** when the private index is not where it expects.  Inside
`tools/sandbox.sh` it never is: the fence puts a **tmpfs over `$HOME`**
(`sandbox.sh`, the comment at the head of the fence list), and the index lives
at `~/.claude/projects/-home-cheery-gestate/memory/MEMORY.md`, which is not one
of the directories bound back in.

`tools/fence-hook.sh` fences a whole command line when any segment of it starts
with `pytest` or `python -m pytest`, so the shape that hits this is ordinary:

    python tools/memoryindex.py && python -m pytest test/test_memory.py -q
    → memoryindex: no index at …/MEMORY.md — nothing to do here
    → 146 passed

    python tools/memoryindex.py                       # the same command alone
    → memoryindex: wrote 71 hooks into …/MEMORY.md

Measured 2026-09-01, both shapes, on the live tree.  **A session that
regenerates the index in the same breath as running a test gets a silent
no-op**, and the hooks it just wrote into `doc/memory/README.md` reach nobody —
which is the exact failure `doc/memory/README.md` §"Why the bodies are here and
the hooks are not" exists to prevent, arriving through the fence instead of
through forgetting.

**And the gate goes quiet in the same direction.**
`test/test_memoryindex.py:69` skips with *"no private index … — nothing to hold
in step here"* under the same conditions, so it has never run where tests run.
That is F185's shape a second time — a check whose green has only ever been
unfenced — and the two together mean nothing on this machine can notice.

The fix is not obvious enough to make in passing, which is why this is an
entry.  Exiting non-zero would break a legitimate case (a checkout with no
private index at all, which is what the branch was written for); binding
`~/.claude` into the fence gives fenced code a path to a session's own
configuration, which is the one thing the deny-list exists to prevent; and detecting the fence in order to say *"skipped because fenced"* is
a third source of truth about where the index is.  Naming the three is the work
this entry hands on.


### F195. **[bug]** A sweep interrupted mid-flight loses the now heap, silently

`reactive_step` empties `gm.now` at the top and refills it signal by signal as
the sweep reaches them (`reactive.py`, `reactive.gm.now = []` then
`_update_one`'s two `now.append(sig)` paths).  There is no rollback, so an
exception raised part-way through the sweep leaves **every signal that had not
yet been re-appended simply gone**, and `reactive.clocks` uncleared.

`spec/frp.md` models this as a function: `reactiveStep : Arrivals → State →
State`, and `react = scanl reactiveStep`.  A fold that raises does not produce
the next state; it does not destroy the previous one.  The implementation
updates in place and has no such property.

**And the failure is silent.**  Measured 2026-09-02 on
`main = 0 ::: mkSig (wait c1)`, with a `GmError` injected into the
sub-evaluation `advance` runs:

    before the failed instant   now = 1   code = 0  dump = 0  stack = 1
    after                       now = 0   code = 0  dump = 0  stack = 1
    the next instant            runs, raises nothing, now = 0

So the machine does not wedge — F20's repair is doing exactly what it claims,
and the G-machine state is untouched — it *empties*, and every instant after
that is a well-formed sweep over no signals at all.  A host driving this would
see silence and no error.

Found while writing F20's gate (`card:ungated-fixes.md`, batch 11), which is
the second time in that sweep that reaching for one entry's gate turned up its
sibling — F31's severance was F192 the same way.

gate: `none — not yet built`.  The measurement above is the shape of one:
inject into the sub-evaluation, then require `gm.now` to be either the old
heap or a complete new one, never a partial.  Not written today because the
repair is a design question — whether `reactive_step` builds the new now-heap
beside the old and swaps, or catches and restores — and that is not a gate's
call.  Weakest point: the injection is a `monkeypatch` of `run`, so this is
measured on an error that cannot arise from a well-typed program today; what
makes it real is that `advance` runs user code, and user code is exactly what
`fixme.md` exists to say can be wrong.

### F196. **[resolved]** `tools/mutate.py` rejects its own documented invocation

Fixed: everything after the first bare `--` is split off as the command before
argparse sees the rest, so both orders work.  The original diagnosis:

The module docstring gives

    python tools/mutate.py batch.json --only F21a -- pytest -q test/

and argparse answers `error: unrecognized arguments: -- pytest -q test/`.
`spec` is `nargs="?"` and `command` is `nargs="*"`, and argparse cannot place
an option between a positional and an open-ended one; the working order was
`--only` *first*.  Found 2026-09-03, on the first batch to use the instrument
(`card:ungated-fixes.md`, batch 12) — the tool was written at the end of batch
11 and its documented form had never been run.

**And the instrument had no test at all**, which is this card's own subject
arriving at this card's own instrument: nine batches of verdicts now rest on a
tool nothing holds.  `test/test_mutate.py` is that, written the same day —
the documented invocation, the mutation being visible to the command and gone
after it, `--only` selecting one, each mutation starting from the original, an
occurrence count refusing a missed anchor, a modified file refused outright,
and the restore surviving a `SIGTERM`.

gate: `test/test_mutate.py::test_the_documented_invocation_is_accepted`,
red on the defect — measured 2026-09-03 against a reverted copy of the tool
(the live one could not be mutated in place, because `mutate.py` correctly
refuses to mutate a file that is already modified).  Weakest point: the file
does not hold the `atexit` path or a restore that fails its hash check, and
both would need the tool to be lied to about its own bytes.

### F197. **[bug]** The canvas's frame clock does not cross

`spec/substrate.md`: *"what a signal is constant over is a clock — the audio
renderer supplies one over `ticks`, the canvas one over `events`."*  At home
`gestate.gui.Substrate.tick` supplies it: one `Tick` on `input` a frame, and
real seconds on `wallclock` beside it (F134).  **Abroad neither crosses.**

    gui._crossing        text entry tags tick chans(+wallclock)
    export.substrate_of  text entry tags      chans

Two halves of one payload, written for one purpose, and the exported half is
missing the clock.  `Tick`'s tag is a position in the program's own table, so a
host cannot derive it — the same argument the other fourteen tags travel on —
and `wallclock` is the renderer's own declaration, so it is not in
`_channel_names` and never reaches `chans`.  Measured 2026-09-03 on
`lantern.ges` and `envelope.ges`: `substrate_of` returns
`['bridge', 'chans', 'entry', 'tags', 'text']`, and asking the shell for the
`wallclock` channel gives `-1` because the name was never sent.

**And no host outside `gui.py` pulses anyway.**  `Panel::tick_canvas` calls
`Canvas::tick`, which is `step(writes, None, …)`; `Canvas::step`'s own
docstring states the cost — *"a host that never pulses shows a canvas whose
faders work and whose animation stands still"*.  `shell/web` takes a pulse tag
in `web_tick` and has nothing to pass it.

**What is not shown, and it is the honest half.**  No piece in
`examples/audio/` was found whose picture visibly moves on a bare frame clock:
`lantern.ges` folds over `events` and `envelope.ges` reads `now`, and both
stand still for 30 frames **in the reference host too** — so what is broken is
the seam, and the cost of it is not demonstrated on today's example set.  A
piece that animates from the clock alone is the first thing to write here, and
it decides whether this is a gap or a defect with a victim.

gate: `none — not yet built`.  The measurement above is the shape of one, and
it needs the missing piece first: a substrate that moves on `Tick` alone, drawn
in `test/test_gallery.py` twice — once with the tag and once without — which
goes red the moment either half of the clock stops crossing.  Weakest point:
until that piece exists, a gate here could only assert the *payload's shape*,
which is a test that the export has a key rather than that a picture moves.

### F198. **[bug]** `arc.ges` writes twenty-four bars of bass that its score never plays

`examples/audio/arc.ges` defines `bass` (line 566) out of `g1 … g8`,
`h1 … h8` and `i1 … i8` — twenty-four bars, spelled out by hand like the rest
of the file — and its `score` (line 594) plays `melody`, `upper`, `middle`,
`lower` and `roots`.  **`bass` is named nowhere else in the file.**

    grep -n 'bass' examples/audio/arc.ges
    566:bass : [: Tone :]      567:bass = g1 ++ g2 ++ …

Found 2026-09-05 while writing `examples/audio/arc.notes`
(`spec/drawnscores.md`): the note file has 219 notes and so does the piece,
and the count only agreed once the `g`/`h`/`i` bars were left out.  A second
number says the same thing from the other side —
`test_drawnscores.py::test_the_velocity_difference_is_the_one_the_format_chose`
asserts **15** distinct velocities in what sounds, against **16** written in
the file: the sixteenth belongs to a bar of `bass` and is never heard.

**Why it is a defect and not a style note.** `doc/notes/notes-on-writing-a-piece.md`
W8 is *"five lines, and the count is the only thing holding them"* — and this
is that failure's sibling and worse: a sixth line held by nothing at all, which
compiles, renders, and is silent.  Nothing in the language, the suite or the
window says a `[: Tone :]` was written and never reached a bank.  The piece
`card:drawn-scores.md` rests on carries a whole unheard voice, and neither
writer noticed for a day.

**The repair is not obvious and is the author's**, which is why this is filed
rather than fixed: either `bass` belongs in the score and the piece has been
heard wrong three times, or it is a draft that should go — and only Henri can
say which, because the question is what the piece is meant to sound like.
`arc.notes` leaves it out, which is faithful to what `arc.ges` *plays*.

gate: `none — not yet built`.  What would hold it is a lamp rather than a test
of this file: a score-carrying program whose author declares a `[: a :]` that
no `>>=` ever reaches has written notes nobody will hear, and that is decidable
from the declarations `audio._authored` already returns.  Weakest point: a
piece may legitimately keep an unused phrase while working, so this is an andon
and not a refusal — which is the same shape `tools/dangling.py` already has for
citations.

### F199. **[bug]** `.notes` acceptance 5 claims more than it holds, and its test picked the case that passes

`spec/drawnscores.md` §"Acceptance" 5 says **moving one note changes exactly one
line** of a `.notes` file, and `test_drawnscores.py::test_moving_one_note_changes_exactly_one_line`
asserts it — by changing a note's **key**.  Measured 2026-09-05 on
`examples/audio/arc.notes`:

    drag in pitch  -> 1 line differs
    drag in time   -> 5 lines differ   (file the same length)

A key is not part of the canonical order; `at` is (`notes.ordered` sorts
section, bar, tick, voice, key).  So the edit an editor actually produces —
**dragging a note in time**, which is what a roll is for — moves the note's line
and shifts every line between its old and new place.  The file stays byte-stable
and the music stays right; what fails is the property the gate was written for,
which is that a diff of a `.notes` file shows *the edit* rather than a
delete-and-insert plus churn.

**Found by asking Henri's question rather than by the suite** — *"does this
remain writable/readable if an editor is written around it?"*  The gate was green
over the case an editor produces, which is `doc/memory/a-targeted-set-is-a-claim.md`
arriving on this session's own acceptance list.

Two readings, and choosing between them is design work not yet done: either the
claim is narrowed to *a note's own line carries the whole edit* (true, and much
weaker), or the canonical order stops sorting by `at` — bar-then-voice-then-tick
would keep a dragged note among its own voice's lines and move it far less.  The
second changes `notes.ordered` and every shipped `.notes` file with it.

gate: `partial — test_drawnscores.py::test_moving_one_note_changes_exactly_one_line`,
which passes and measures the wrong drag.  What is missing is the same assertion
for a change to `at`, with whatever number is then true written into it.  Weakest
point: a test that pins today's 5 would pass forever without the property
improving, so it should assert against the *voice's* line span rather than a
constant.

### F200. **[bug]** `notes.write()` drops every comment in a `.notes` file

`gestate/notes.py`'s parser strips `#` to end of line and the writer never emits
one, so a round trip deletes them:

    # the lydian section — the G# is the mode        <- gone
    note  … key 68 vel mf   # the sharp fourth       <- gone

Measured 2026-09-05.  Nothing caught it because `examples/audio/arc.notes` is
generated and carries no comments, so the shipped file has nothing to lose —
`doc/memory/a-targeted-set-is-a-claim.md` again, from the other side: the fixture
had none of the thing the property is about.

**Why it matters more here than in a generated format.**  The whole premise of
`spec/drawnscores.md` is that a person and a session edit the same file, and
Henri's constraint of 2026-08-29 is that a textual being must be able to edit it.
The first time an editor writes back a hand-annotated file, the annotations that
explain the music are gone — silently, and in the same gesture that was supposed
to be byte-exact.  `arc.ges` next door is 599 lines of which a large share is
`#:` prose about *why* those notes; the format that replaces it currently cannot
hold a word of it.

The shape of the repair is not obvious and is why this is filed rather than
fixed.  A comment has no record to belong to once the lines are reordered:
attaching it to the note below it makes a section comment jump when that note is
dragged, and attaching it to nothing makes it a line with no position in a
canonical order.  The honest options are a `#` line owned by the (section, bar)
it precedes, or a trailing field on the note record itself — and the second is
the one that survives reflow, which is gate three.

gate: `none — not yet built`.  What would hold it is a round trip over a file
carrying both a whole-line comment and a trailing one, asserted byte-identical —
one test, once the ownership question above is answered.  Weakest point: a gate
written before that answer would pin whichever behaviour was implemented first.

### F201. **[resolved]** `tools/modecheck.py` crashed on every piece written since manners landed

`notes_of_ges` unpacked each payload as a pair — `for _, key in payload` — which
is true of `Tone Float Int` and false of every payload carrying a manner.  So
the tool written on 2026-09-05 to measure `hollow.ges` could not read
`arc.ges`, `arcnotes.ges`, `marked.ges` or `drums.ges`:

    python tools/modecheck.py examples/audio/arc.ges song 2
    ValueError: too many values to unpack (expected 2)

**Found 2026-09-05 while building `tools/bars.py`** (`card:the-first-jam.md`
item 2), which needed the same field and hit the same wall — and `arc.ges` is
the piece `modecheck.py`'s own docstring is about.  The tool was a day old and
had been run on one file.

**Why a position cannot be assumed.**  A payload is the author's own record, so
which field is the pitch is the author's business: `arc.ges` writes
`Tone Float Int Int` and puts it second, `audio.ges`'s own `Tone Int Int Int`
puts it first.  **The exact answer is `Notable.noteKey`** — and it is not
reachable from a tool, because reading it means compiling an auxiliary program
the way `scorebox.build_rolls` does, which needs a `notes <expr>` ask in the
source to hang on.

**The repair is `audioscore.pitch_of`**, a stated rule rather than a guess: the
one field that is an `Int` in the playable range, 21..108.  It holds because
every other `Int` a payload carries here is small — a manner is a three-bit set
and a dynamic level is 0–7 — and it **refuses** when none or several qualify,
because a wrong pitch would be a report that reads plausibly and is false.
`modecheck.py` and `bars.py` both go through it.

gate: `test_drawnscores.py::test_modecheck_runs_on_a_piece_that_carries_manners`
runs the tool on `arc.ges` and reads its count back, plus
`test_the_pitch_is_found_in_a_payload_of_either_shape` and
`test_an_ambiguous_payload_is_refused_rather_than_guessed` on the rule itself.
Weakest point: the rule is not `Notable`, so a piece whose payload carries two
playable numbers — a note and a transposition, say — is refused rather than
read, and the honest fix is to make `scorebox`'s auxiliary-program trick
reusable without an ask.
