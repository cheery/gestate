---
name: the-language-goal
description: "Henri's short-term goal, 2026-08-20, in his own notes: a language that compiles to wasm, is easy to model-check and to study, and is optimised for reading — with later tunings for UI code, concurrency, live coding and mathematical code; and since 2026-09-15 the direction beyond it, a general-purpose multi-staged language, where each stage is a moment more type information arrives — the capability, not an ecosystem"
metadata:
  type: project
---

**Stated in his own notes, 2026-08-20**, and not derivable from the
repository, which is why it is written here:

> *"Tavoite lyhyellä ajalla voisi olla että mulla olisi koossa kieli
> joka kääntyy wasmiin ja jota on helppo mallintarkistaa ja tutkia.
> Optimoitu lukemista varten."*

A short-term goal of **a language that compiles to wasm, is easy to
model-check and to examine, and is optimised for reading.**  Then, as
things that would be nice rather than needed: tunings for interface
code, for concurrency, for live coding, and for mathematical code.

**Why this is worth having written down:** three of its four properties
are already vision lines wearing other clothes — *optimised for reading*
is `vision.md`'s cognitive-weight argument, *easy to model-check* is
*won't ever be untested* pushed upstream into the language, and the four
tunings are the domains gestate already lives in.  What is **new** is
**wasm as the target**, which nothing in the tree says.

**And it sits against a deferral.**  `card:work-environment-ai.md`
defers the language deliberately — the environment needs none of it,
gestate already has a language, and the LP-IR paper it cites becomes
relevant only at an OS phase, if ever.  That deferral was written
without this goal on the table.  **Not a contradiction to resolve by
guessing**: the card defers *a new language for the environment*, and
this is a goal about *the* language.  Whether they are the same object
is Henri's to say.

**How to apply:** do not act on this — it is a stated direction, not a
card, and by [[capacity-is-not-a-caller]] a direction is not yet a
`because`.  Do notice it when the two touch: if the environment work
starts pulling a language after it, this note is the reason to stop and
ask rather than to design one.

## The direction beyond it — 2026-09-15, his words

Asked at the end of a rest day, before sleep, out of the staging work
on `card:strict-forms.md`:

> *"could gestate become a general purpose programming language?  This
> staging -thing has been making me to think... each stage is simply a
> moment when we discover more type information about the task at hand
> and benefit from that somehow.  There is perhaps no reason that a
> multi-staged type-principled language would lose to language like
> python is.  it's other way around although I see that is a research
> grade question."*

And on what is wanted from it:

> *"I don't want to write an ecosystem that pairs with python.  Instead
> what I want is the capability to go into that direction.  I trust
> that the ecosystem builds itself when there is the reason for it to
> do so."*

**What was said back, and he took as the shape of it.**  Three things
the direction decomposes into, and he wants all three, *"but I think
that right now"* — so only the third is done, and it is this section:

1. **The theory.**  His sentence needs more than MetaOCaml or Zig give:
   stage n+1 must be able to read the types stage n *inferred*, as
   values.  That is the reflection Kiselyov & Imai regret lacking, and
   the direction `card:strict-forms.md` §"Read — 2026-09-14" declined
   with *no caller yet*.  This direction is the caller, named; not yet
   pulled.  The precise research question: a stage's inferred types
   reified into the next stage's data, sound, and HM-inferable within
   each stage, the model-checker still seeing the last stage only.
   That last property is why this route is preferred over full
   dependent types for the goals above.
2. **The self-hosting test.**  *General purpose* is a test, not a
   property, and the tree holds one: ten Python files write `.ges`
   text in f-strings, because the host is Python.  The naive thing is
   to write one host — the reactive layer, or the score box — in
   gestate, and read off what it lacked as a list.  A guess, unmeasured:
   modules first (the card already notes the stage restriction has
   nowhere to land without them), then mutable state, then strings.
3. **The direction, written down** — here.

**What it is not.**  Not a card, and not a `because` — the rule of
§"How to apply" above stands unchanged.  Python is already multi-stage
(a JIT specialising, a dataframe typed when its file is read); what
this direction claims is only that stages an author *writes* can be
checked and stages that *happen* cannot.  Where staged languages have
lost is reading — a second syntax for the second stage — and
*optimised for reading* above is the ruler that decides it; the `$(e)`
splice already in the tree is the first bet.  Ecosystem is most of why
Python wins and is explicitly not to be built.

**How to apply, added:** when a language decision on a live card has
two answers and one of them keeps the general-purpose door open at no
cost to the three properties above, that is the tiebreak, and say so
on the card.  When it would cost one of them, it is his to weigh, and
this section is what to cite when putting it to him.
