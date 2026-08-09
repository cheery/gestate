# The editor — widgets derived from types, source as the only truth

*Written as a design; `mkKnob` is the built seed it generalises.
Companion to `spec/substrate.md` (the canvas) and `spec/liveaudio.md`
(the live engine the editing rides on).*

Every patcher UI ever shipped has the same disease: the GUI owns a
model, the code owns another, and they drift until one corrupts the
other.  This design is immune by refusing to have the second model:

> **A widget is a view over a span of source.  Dragging it is a text
> edit.  There is nothing else.**

The program stays the one truth — the same rule that keeps the graph
"exactly what the source says" for stage 5 — and everything below is
the consequence of taking it seriously.

## The seed that already works

`mkKnob` is the proof of concept in the tree: a declaration the
editors draw a control beside, whose value reaches the engine as a
control channel.  What is missing is not the mechanism but the
*generalisation*: the knob is one blessed form, recognised by name.
The editor this file designs recognises declarations by **inferred
type**, which the pipeline already computes and `audiospans` can
already anchor to the author's line.

## The dispatch: type → widget

Derived, not maintained — in the spirit of `reference.py` deriving
pages and `internals.py` deriving faces, the one hand-written thing
is a small table from type to widget, and everything it draws comes
from the program:

| type of the declaration | widget |
|---|---|
| `Float` (literal body) | drag-number, scroll to nudge |
| `Sig Float` via `mkKnob` | the knob, as today |
| `Adsr` | four handles on a drawn envelope |
| `List Envelope` | breakpoint editor — `sendPat`, `fiddleLine`, drawn and draggable |
| `Seed` | a reroll die |
| `Patch` / `modulates` wiring | the FM routing matrix as a grid |
| `Wave` (`spec/sampling.md`) | waveform with a playhead |

Each row earns its place the same way: the value is *data a musician
has a hand-shape for*, and the text form, while honest, is not that
shape.  A type with no row gets no widget and loses nothing — the
text was always the interface.

## The literal rule

**Widgets attach to declarations whose body is one literal, or one
constructor of literals.  Everything else is text.**

The moment a widget edits `220.0 + 2600.0 * env`, it must own an
interpretation of the arithmetic, and the second model is back with
its drift.  The rule is checkable from the AST — a `VNum`, or a
`VApp` spine of a constructor over `VNum`s — so the editor cannot
grow cleverness case by case; a program *invites* a widget by
factoring a value out to a declaration, which is the refactoring the
courses teach anyway, and declining the invitation is deleting the
declaration back into its use site.

## Why the edits are safe while it sounds

A widget drag is the best case stage 5 was designed for.  Node
origins are paths of definitions, so **editing a folded-in constant
does not move a node**: dragging the cutoff keeps the filter's
memory, dragging the `Adsr` keeps every oscillator's phase, and
`migrate` needs no special case because a widget edit is
indistinguishable from the same edit typed.  The knob already
exploits this; the table above just gives more types the same ride.

Two recent pieces slot in as if placed:

* **Comments survive.**  A widget rewrites its declaration through
  the formatter, and since `spec/comments.md` landed, the trivia
  beside the declaration is reattached, not eaten.  A tool that
  deletes the comment explaining a value while *adjusting* that value
  would be the old footgun wearing a nicer shirt.
* **The editor is testable as text.**  Because a drag *is* an edit,
  the widget layer needs no UI oracle: `spec/verification.md`'s
  transcripts carry it as `edit` events, and a property pins the
  contract — *widget edit and typed edit of the same literal produce
  identical source*, byte for byte, comments included.

## The pane, concretely

`audiopygame` draws source on one side already.  Per declaration
whose type has a row and whose body passes the literal rule, the
editor lays the widget in the margin beside the declaration — where
the knob goes today, where the `[ref]` pane points — and a drag:

1. formats the new literal into the declaration's span,
2. republishes, exactly as a keystroke save does,
3. lets stage 5 migrate the running state.

No hidden channel to the engine: a control-rate `mkKnob` keeps its
channel (that is what control rate is *for*), and every other widget
goes through the same door as typing, at edit rate, which a drag is
comfortably slower than — the engine recompiles per keystroke today.

## Costs, stated

* Writing literals back well is real work: number formatting that
  does not smear `0.5` into `0.5000001`, spans that survive the edit
  they cause (`audiospans` moves positions already; now it moves them
  *because of us*), and the formatter touching one declaration
  without reflowing the file.
* The type→widget table is a second place a type's meaning lives —
  kept honest by being data in one module, beside nothing, the way
  `reference.py`'s extras table is.
* Undo must be text undo.  The moment widgets keep their own history
  the second model is back; a drag is one edit, and the editor's
  existing undo owns it.
* pygame draws more shapes.  The envelope and matrix widgets are
  each a screen of drawing code with no design decisions in them —
  the decisions are all above, which is where this file wants them.
