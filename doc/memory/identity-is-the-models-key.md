---
name: identity-is-the-models-key
description: "Henri, 2026-09-08: a note's identity is its content and the file sorts to its agreed order — identity is the model's key, never the picture's index; and a reference declares its kind: a thing, a place, or a set (Kale)"
metadata:
  type: project
---

**Identity is the model's key, never the picture's index.**  Henri,
2026-09-08, closing `card:gui-is-difficult.md` Q7: *"nuotti saisi
lajittua siihen järjestykseen mikä on tiedostolle sovittu."*  So a
`.notes` file is a table — a note's identity is (voice, tick, key),
every gesture writes the file in its own order (`notes.canonical`),
and the session's selection is a set of keys (`Session.held`) looked
up in the roll of the moment, never an index kept across a rebuild.
The same morning: *"laita transkription transpose-osoitteeseen ääni"*
— `transpose`, `mark` and `resize` name a note as box, voice, tick,
key.

**Why:** the tree answered identity three ways in three layers and
they disagreed — the file was values, the commands were keys one
field short (seven unison doublings on `arc.notes` a hand could not
transpose), the session was positions patched by spending the
selection at each commit.  Measured before deciding: for `key` and
`len` the canonical write and the in-place rewrite are byte-identical
on 291 of 291 notes; for `at` they are the same lines in canonical
order.  And Coblenz et al., *Kale* (arXiv 2608.26345), measured the
alternative: people cannot predict a reference that is rewritten
under structural change (7 of 15), and Kale's source turned out to be
*a session-held object with the visible position re-derived from it*
— reading E — never a persisted id.

**How to apply:**
- A reference declares its kind, and there are three — **a thing**
  (a key the model carries), **a place** (a coordinate in the
  geometry), **a set** (a query re-run) — and the framework never
  converts one kind to another silently.  On the roll: a selection is
  things, a band is a set, the rail is a place.  On a sheet
  (`card:gex-sheet.md`): `Col[0]`, `Col[+1]`, and a Datafun `for`.
- Carrying marks through edits is a mechanism inside a command that
  knows what it moved, never a rule shown to a person.  A typed edit
  the editor did not make drops a thing-reference and says so;
  reconciliation by similarity (G) is never used.
- A command that moves a thing answers where it put it, so the
  selection follows (`_follow`, `_settle`, on the bench's `rebuilt`
  hooks).  Two edits to one note at one release are one command
  (F211: after the first, the second's address is stale).
- Hold objects, not `id()`s, across a rebuild — a rebuilt roll landed
  at the freed address once.

The morning's chart rule sits beside it: *the chart holds the time,
the host holds the geometry* (`gestate/gesture.ges`,
`gestate/hand.ges`); the host looks and the event carries what it
found.  Related: [[gui-command-language-first]],
[[test-what-a-person-would-do]] — F211 was found by trying the naive
thing on the note the existing test had not chosen.
