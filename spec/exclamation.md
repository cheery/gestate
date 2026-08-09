# The meaning of `!(f x)` — a root cause analysis

The complaint: people read `!(f x)` as "take the *computed value* `f x`
and make it a constant signal" — `constSig (f x)` — but Gestate desugars
it to `mapSig f x`, exactly as if the parentheses were not there.  The
claim under analysis was that this cannot be repaired.

An earlier draft of this file endorsed that claim.  It is wrong, and the
five whys below now trace both threads honestly: why the implementation
conflates the two spellings, and why the "necessity" the code and one
test assert is contingent on an implementation choice, not on the
grammar.  (The journal has precedent for this kind of correction: "the
earlier entry claiming otherwise was wrong.")

## The five whys

**1. Why does `!(f x)` mean `mapSig f x` and not `constSig (f x)`?**

Because `_lift_spine` (`desugar.py:101`) finds the `!` marker by
unwinding the application spine, and it unwinds *through* the marker's
operand as well: `!(f x y)` arrives as a marker whose operand is already
a spine, and the walk collects the arguments from it just as it collects
them from `(!f) x y`.  Both spellings produce the same `(head, args)`
pair, so both reach the same case of `_desugar_lift`.

**2. Why does desugar unwind through the operand instead of treating a
parenthesised operand as a single value?**

Because it cannot tell the difference.  This is checkable directly:

    main = !f x    ⇒  VOpPhrase(['!', VApp(f, x)])
    main = !(f x)  ⇒  VOpPhrase(['!', VApp(f, x)])

The two parse trees are identical except for source spans.  Desugar is
not choosing to conflate them; it is handed the conflation.

**3. Why are the trees identical — where did the parentheses go?**

They were consumed by the parser and left nothing behind, through the
meeting of two mechanisms:

* At phrase-head position, `!` is routed through the operator-phrase
  machinery, and `_parse_app_expr` (`parse.py:770`) folds consecutive
  atoms into left-nested `VApp` nodes *before* fixity resolution, so
  the `f x` in `!f x` is already a single atom when the phrase
  `['!', atom]` is formed.
* A parenthesised expression parses to the inner expression's own node.
  There is no `VParen` wrapper; `(e)` is `e`.

So both spellings become `!` next to the same `VApp` atom, inside the
parser, before the fixity table is even built.

**4. Why is `!` routed through the operator-phrase machinery at all?**

Implementation economy.  `!` sits in `DEFAULT_PREFIX` at precedence 9
(`descend.py:84`), and riding the ordinary fixity machinery buys its
behaviour for free: precedence interaction (`!a * b` is `(!a) * b`),
and — via `_PREFIX_ONLY_OPS` — argument-position use, where `g !f x`
parses as `g (!f) x`.  The price is that at head position the operand
is a *post-folding phrase atom*, so the marker's intended head-binding
("`!f x y` reads as `(!f) x y`") has to be reconstructed downstream by
the spine walk in desugar.  The parenthesised synonym `!(f x y)` ≡
`!f x y` fell out of that reconstruction, was then documented as a
courtesy ("the parentheses an eye may prefer"), and finally locked in
by `test_the_marker_may_take_the_parenthesised_application`, whose
docstring promotes the accident to a necessity.

**5. Why was the lift-the-application reading the one the design
protected?**

Because `!` was never conceived as "the constSig operator".  It is
idiom brackets in one character — McBride's `(| f x y |)` — and the
journal records the author using it exactly so: "the same one-character
lift every voice already uses on its payload (`!hzOf s`)".  Under the
bracket mental model, `!(f x)` *is* a bracket around an application,
and the machine's reading is the intended one; `constSig` is merely the
zero-argument case.  The people who trip over `!(f x)` are reading `!`
as an ordinary prefix function instead.  The design chose the bracket
model, implemented it on the cheap (why 4), and the cheap implementation
then made the two models *indistinguishable in the tree* — which got
mistaken for their being indistinguishable in principle.

## Root cause

`!` has head-binding semantics ("marks the head, takes the spine") but
is parsed with phrase-binding machinery that folds the spine into one
atom first.  The gap between the two is bridged after the fact by
desugar's spine walk, and the bridge is exactly where `!(f x)`'s
intended meaning is lost: the walk cannot see parentheses that the
parser never recorded.  The conflation is a property of *this routing*,
not of the language's grammar.

## The repair that exists

The earlier draft claimed no repair was possible without breaking
`(e) ≡ e`, the declarable-fixity architecture, or the written-not-
inferred lift.  All three defences assumed `!` must remain a phrase
operator at head position.  It need not — **the parser already contains
the alternative**, applied today in argument position: bind `!` to
exactly one atom.

Do the same at phrase-head position and the trees diverge with no
paren node anywhere:

    !f x     ⇒  VApp(VPrefix(!, f), x)      — lift: mapSig f x
    !(f x)   ⇒  VPrefix(!, VApp(f, x))      — constant: constSig (f x)

`(e) ≡ e` is untouched: the parentheses carry no meaning of their own,
they merely change which atom follows `!` — precisely as they change
which atom follows `f` in `f g x` versus `f (g x)`.  Desugar keeps its
spine walk for the outer applications and drops the inner unwind loop
(`desugar.py:130-133`).  The rule becomes uniform — **`!` binds the
next atom; outer application supplies the lifted arguments**:

    !x         ⇒  constSig x               (unchanged)
    !f x y     ⇒  zipSig f x y             (unchanged)
    !(f x)     ⇒  constSig (f x)           (the human reading)
    !(f x) y   ⇒  mapSig (f x) y           (computed head, then lift)
    !(a * b)   ⇒  constSig (a * b)         (unchanged)

and the old sharp edge — `!(a * b)` constant but `!(f x)` a lift —
disappears outright, because the rule no longer depends on whether the
operand happens to be an application spine.

## What the repair costs

Real, but small, and worth stating precisely:

* **`!` leaves the declarable-fixity system** and becomes grammar, like
  `->`.  This formalises an existing fact rather than creating a new
  one: desugar already matches `op == "!"` by name regardless of any
  declared fixity, so a user's `prefix 3 !` today would change the
  parse while the spine walk kept its own opinion — `!` is already
  special; it is just not honest about it.

* **Existing `!(application)` spellings change meaning.**  The codebase
  has a handful: `!(negate 40.0)`, `!(clamp 0.0 1.0 4.0)`,
  `!(negate 500.0)` in tests, `!(toFloat n)` in `doc/ref/signal.md`.
  Every one of them *intends* a constant of a computed value — the
  authors reached for the reading this repair grants — and the journal's
  measurement ("the constant folds out however it is written; identical
  graph, 7 nodes") says their compiled output would not change.  The one
  genuine casualty is the test that asserts the synonym, which would be
  deleted along with the claim it enshrines.

* **Stage-5 origin stability**: a node's origin is the source that wrote
  it, and this change re-derives some origins (`!(f x)` builds a
  different node than before).  A one-time migration concern on live
  sessions, not an ongoing one; the lift stays written, never inferred.

## The repair landed (2026-08-09)

The decision was made and the change is in:

* **Parser** — `parse._marks_head`: a `!` whose next token starts an
  atom binds that atom, at head position exactly as in argument
  position.  `_parse_segment` stops collecting it as a phrase prefix;
  `_parse_app_expr` takes it as the head.  `'` and `|<` keep their
  phrase behaviour — the rule is `!`'s alone.
* **Desugar** — `_lift_spine` no longer unwinds *through* the marker's
  operand: the operand is one value, and the applications *around* the
  marker are the lifted arguments.  `!x` ⇒ `constSig x`, `!f x y` ⇒
  `zipSig f x y`, `!(f x)` ⇒ `constSig (f x)`, `!(f x) y` ⇒
  `mapSig (f x) y`.
* **`constSig` went internal with it.**  With `!(f x)` writable, the
  name had no remaining job in a program, so `internals.py` now refuses
  it from author text the way it refuses a library's machinery
  (`RENDERER_PRIVATE`), pointing at `!`.  The renderer still defines it
  — it is the node the marker builds, over whichever clock is running —
  and the libraries' `Floating`/`Num` instances still build on it.
* The old necessity claim was deleted where it stood: `_lift_spine`'s
  docstring, `doc/ref/language.md` (regenerated from `reference.py`),
  and `test_the_marker_may_take_the_parenthesised_application`, replaced
  by `test_the_marker_takes_one_atom` and
  `test_the_marker_lifts_a_computed_head`.  Every `constSig` in
  `examples/` and the tests now spells its constant with `!`.
