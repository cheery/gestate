---
name: the-language-goal
description: "Henri's short-term goal, 2026-08-20, in his own notes: a language that compiles to wasm, is easy to model-check and to study, and is optimised for reading — with later tunings for UI code, concurrency, live coding and mathematical code"
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
