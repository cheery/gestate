# gui-is-difficult — the ideas a GUI framework for gestate is built from, and the one that comes first

    status   doing
    because  "I think that GUI programming is extremely difficult.  For
             several reasons and one of them is that it's very visual.  I
             think I haven't solved it satisfactorily and it shows up
             every time when there's any kind of UI to make." — Henri,
             2026-09-07, after a gemba walk of the previous day's score
             box work.  "It's time to write a GUI framework for gestate.
             It's a difficult subject, so I am needed again to design
             critical parts of it."
    asked    Henri, 2026-09-07 — "Write these down… I think I want these
             all in."
    see      card:notes-editor.md — the day that showed it: 130 hands a
             box, an 85,000-character page, a five-second redraw
             card:drawn-scores.md — the roll this framework has to carry
             spec/substrate.md §"S3 — attachment, and the walk" — the pad
             the spec promised and the press that wrote one (F204)
             spec/north_star.md §"The vocabulary" — a gesture names what
             the file and the picture agree on
             doc/memory/henri-prior-tools.md — oscillseq, mide, xylem:
             each already answered one of these once
             doc/memory/gui-command-language-first.md — the rule below,
             as a memory
             vision.md §"Gestate as a generic working platform" and
             §"Ease of use and efficiency" — the sentences this binds
             to, §"What the vision says" below

## What this is, what it is not, and when it runs

**A framework for the windows gestate draws** — the workbench's boxes,
the roll, the faders, whatever the score view becomes — built from a
short list of ideas each of which removes one reason GUI work is hard.
It is **not** a widget toolkit borrowed from elsewhere; `vision.md`
refuses borrowing another system's vocabulary to get power cheaply.
It is not the substrate, which stands and which most of the ideas
below are already partly true of.  And it is **not a session's to
design**: the critical parts are Henri's, by his own sentence, and
day one of this card is a dialogue, not code.

## What the vision says — Henri, 2026-09-07

*"btw.  The GUI framework binds to several sentences we have at the
vision.md."*  Read for them, the same afternoon:

- *"a very good user interface for everyday work: Gestate gestates.
  It's like emacs or vim in that sense, except that it's a visual
  system along the text."* — the framework is how that sentence gets
  built, and `card:gex-sheet.md` and `card:markdown-reader.md` are its
  first two everyday clients.
- *"open a file, hear it, change it, and hear the change without being
  told anything first"* and *"both can be edited while they sound"* —
  ideas 6 and 9, the postcondition with a number on it.
- *"It's so much ceremony, to get a simple thing done!  … poor tooling
  leads to poor results."* — the `because` of this card, in the
  vision's words before they were his of that morning.
- *"Gestate won't do anything unexpected silently."* — idea 7, the
  window that inspects itself; and the walk's stop 5, a press that
  returned an empty string.
- *"Broad platforms are historically terrible at the stranger test …
  the ease of use is preferred."* — the tension every everyday client
  is measured against before it lands.
- **And one that cut the other way:** *"Gestate won't grow modes.
  (there is one mode: typing)."*  The transport's three states were
  first written as *modes*, in the card, the spec and the module.
  **Henri, 2026-09-07:** *"rename them to states, modes is the wrong
  word."*  Renamed the same afternoon; `card:transport-modes.md` keeps
  its filename, which is its id.

## The one that comes first, and must be stressed

**The command language and a clear model, before any picture.**
Henri, 2026-09-07: *"One thing I find important, that you already
listed: it's the command language and clear model before the GUI.
That's so important it must be stressed."*

Every gesture has a command under it, the command runs headless, the
transcript replays, and the picture is a way of issuing commands and
seeing the model — never the place the model lives.  The strongest
working examples: Tcl before Tk, where the toolkit was a command
language's front; Blender, where every button is a Python operator and
hovering shows its name; Emacs, where a key is a command with a
docstring; Plan 9's acme, where the text on screen *is* the command
line; AutoCAD's command line under every menu; Reaper's actions list;
and his own oscillseq, *everything has a command under it*.  This tree
has it most fully of all the ideas below — `transpose`, `carry`,
`select`, `bars`, `tempo` are what a drag runs when it lets go — and
it is the reason yesterday's rewrite of the hands cost the tests and
not the commands.

**Why it comes first.**  It is the only one of the ideas that makes
the others testable.  A picture as a function of state needs a state
to be a function of; hit-testing needs something to name what was
hit; a photograph as a test needs a command to have produced the
picture; a window that inspects itself needs a model to report.  Build
the picture first and the model is whatever the picture happens to
hold, which is the widget tree, which is the bug.

## Why it is hard — four things at once

1. **The oracle is an eye**, and an eye is not in the suite.
2. **Geometry is continuous** while code is discrete.
3. **A gesture is state spread across time**, from press to release.
4. **Two machines must agree**: the one that draws and the one that
   decides what a press hit.

Each idea below removes one of these.  Nobody has removed all four; the
best toolkits combine four or five of the ideas and still ship the
kind of defect F204 was.

## The ideas, each with why it is great and where the tree stands

*Session's list, 2026-09-07, from Henri's ask for "the best ideas for
building graphical user interfaces and why they're great ideas".*

1. **The picture is a function of the state, recomputed whole.**
   Immediate mode (Muratori, Dear ImGui), Elm, React.  Kills the
   retained widget tree that must be kept in sync with the model,
   where most GUI bugs live.  *Here:* the G-machine draws the roll
   from the file.  Yesterday's five seconds was this idea paid for the
   wrong way, through a recompile instead of a redraw.  *Its own hard
   part:* identity — which drawn thing is the same thing as last
   frame; F136's *244 of 291 notes jumped to a line not theirs* was an
   identity defect.
2. **Hit-testing derived from the same data that drew.**  The display
   list carries regions; a press asks the list.  What is visible is
   what is pressable, by construction.  Sketchpad, 1963.  *Here:*
   `Display::grabbed` and `gui._grabbed`, held to each other by
   parity; F204 was the hit side disagreeing with the draw side's
   spec, and the parity test is what caught it.
3. **A gesture writes nothing until it commits, and commits as a
   command.**  Press, drag, release as a state machine; the release
   runs a text command.  Undo is one entry, the transcript replays,
   the headless test drives the command not the mouse.  *Here:* most
   complete — §"The one that comes first".
4. **A tiny layout algebra.**  Over, Beside, Sized, Shift; box and
   glue; flexbox.  Composition without a class per widget; TeX showed
   the algebra plus one optimiser does a whole domain.  *Cost:*
   absolute arithmetic leaks in for what the algebra did not foresee
   — the roll's `Shift` sums.
5. **Constraints for the relationships the algebra cannot compose.**
   Cassowary, Auto Layout, xylem.  "This end stays at that end" is
   stated once and holds under resize.  *Cost:* an overconstrained
   system is worse to debug than arithmetic, so toolkits confine it to
   layout and keep it out of behaviour.
6. **Direct manipulation stated as four checkable properties.**
   Shneiderman: the object continuously visible; physical actions
   instead of syntax; operations rapid, incremental and reversible;
   the effect immediately visible.  Great because each is testable.
   *Here:* `card:notes-editor.md`'s postcondition is the fourth with
   a number on it.
7. **The window inspects itself.**  Morphic's halos, a browser's
   inspect element, Sketchpad's pick.  Press a thing and see its
   rect, its source line, its state; ask a pixel why it did not hit.
   The visual is the hard part and this makes the visual queryable.
   *Here:* half — a press says which line wrote the note.  The other
   half is missing, and the walk that produced this card could go
   through the code and not through the window.  **The session's
   candidate for the seam to open first.**
8. **A photograph is a test.**  Snapshot tests; `tools/driven.py`.
   The only honest oracle for visual is a picture, and a stored one
   compared is that oracle without the person.  Brittle, so hold few
   and hold structure elsewhere — the item-identical hit-table test is
   the structural form.
9. **One loop, one frame, inputs coalesced.**  The game loop.  Latency
   is a property of the loop, not the widgets.  *Here:*
   `doc/memory/gestate-editor-latency.md`, learned the hard way.
10. **Data, not generated program text.**  A picture is data produced
    by a program, and the program's size must not grow with the note
    count.  The page's 85,000 characters was codegen standing in for
    data; yesterday's 8,000 is the idea arriving.

## More from the session's memory, unsorted — to be questioned

*Offered 2026-09-07 at Henri's ask, "whatever you can find about GUI
development in your mind".  Each is a thing the session believes it
knows; none has been measured against this tree.  Strike freely.*

- **Modes are the enemy** (Tesler, Raskin's *Humane Interface*): a
  mode error is the user acting on a state they cannot see.  Raskin's
  quasimode — a mode held only while a key is down — is the honest
  form; Vim is the counterexample that works by making the mode the
  whole discipline.
- **Gesture recognisers as explicit state machines** (UIKit:
  possible, began, changed, ended, cancelled, failed) with declared
  exclusion between them.  The roll's press/band/resize/ruler are
  four recognisers written as `if` ladders today.
- **Statecharts** (Harel) for reactive systems — hierarchy and
  orthogonal regions, drawn.  The gesture machine above is one.
- **Identity by position versus identity by key** (React keys,
  SwiftUI's structural identity): the unsolved part of idea 1, and
  what provenance is.
- **The accessibility tree as the second proof a model exists**: if
  the UI cannot be walked by a screen reader, its structure was never
  named.
- **Gulf of execution and gulf of evaluation** (Norman): "very visual"
  is the evaluation gulf — the person cannot see what state the thing
  is in.  Affordances and feedback are the two repairs.
- **Fitts's law** — target size and distance predict acquisition
  time; edges and corners are infinitely tall.  An eight-pixel note
  end is a Fitts target.
- **The command palette** (Sublime, VS Code) and Emacs's
  `describe-key` — discoverability of a command language without a
  menu tree.  The natural front of idea 3.
- **Text as the interface** (Oberon, acme, Lilypond, TidalCycles,
  trackers like Renoise): a family where the model is a text and the
  picture is optional.  Gestate's `.notes` is already in it.
- **Zooming interfaces** (Pad++, Bederson): one continuous surface
  instead of windows.  A roll at the editing scale and the page at
  the compact one are two zoom levels written by hand.
- **Bidirectional editing / lenses** (Sketch-n-Sketch): edit the
  picture and the source changes, edit the source and the picture
  changes, both held to each other.  `transposed` writing the file
  back is one direction of a lens.
- **Damage rectangles versus full redraw**; double buffering; vsync
  — the mechanics under idea 9, and mostly settled.
- **Excel** as the most successful direct-manipulation programming
  environment ever shipped, and why: the model is a grid of formulas,
  the picture *is* the model, and every cell shows its value and can
  show its formula.
- **Xerox Star and the Canon Cat** — the two designs that started
  from a model of the *work* rather than of the screen.
- **Tufte's data-ink and small multiples**; Bertin's *Semiology*;
  Wilkinson's grammar (already read at the score box) — for the
  picture's *content*, not its plumbing.
- **Music-specific rooms:** Sibelius/Dorico (notation as a model with
  engraving rules), Ableton's clip grid, Bitwig, Max/MSP's patcher,
  SuperCollider's GUI as a language afterthought — each is a
  different answer to *what is the model*.

## The models — a taxonomy, a language, and what gestate has — 2026-09-07

Henri asked, before reading the card: *"Is there some taxonomy or
modeling language for models specifically?  And what is gestate's
model aside the rope that contains the text?"*  The session's answer,
and his decision under it.

**Two kinds of taxonomy.**  One classifies *which model is meant*:
Norman's designer's model, user's mental model and system image;
Cooper's implementation, represented and mental models, with the rule
that the represented one sits nearer the mental one than the
implementation.  That taxonomy is why *very visual* is hard — the
system image is the only channel the other two meet through.  The
other kind is a language for writing a model, each buying one
property:

| language | it makes you say | the property |
|---|---|---|
| algebraic data types | the shapes a value may take | illegal states unrepresentable |
| relational model, Datalog | a set of relations | normal forms as a quality taxonomy; mide did UI this way |
| Object-Role Modeling (Halpin) | facts as sentences — *a Note sounds a Key at a Tick* | the model is checked in prose before any schema |
| Alloy (Jackson) | relations plus invariants | a bounded checker finds the counterexample |
| TLA+, Event-B | a state machine with invariants over time | behaviour, not only structure |
| statecharts (Harel) | hierarchical states, orthogonal regions | the gesture machine, drawn |
| domain-driven design (Evans) | entity, value object, aggregate, event | identity is named — the GUI's own hard problem |
| event sourcing | the model is the log of commands | replay for free; `sessionlog.py` already is this |
| lenses (Foster, Pierce) | a view that writes back, with laws | the picture-to-file direction held honest |
| denotational design (Elliott) | a meaning the implementation is held to | the `Sig` lineage |
| Naked Objects, Ecore | the UI derived from the model | model-first at its strongest; its generic UIs are dull |

**The session's recommendation:** four of them together — ORM-style
sentences to *say* the model, ADTs to *write* it, Alloy-style
invariants to *check* it, a statechart for the gestures.  Alloy fits
`doc/memory/the-language-goal.md`, easy to model-check.

**Henri, 2026-09-07:** *"I accept your recommendation and would like
to try it somewhere before we apply it to gestate."*  So the four are
tried on something small first; where, is Q5.

**Gestate's model beside the rope: seven, and none named as the
model.**  Read off the tree, not guessed (`Session`, `Workbench`,
`Window`, `Roll`, `sessionlog`, `shell/editor`):

1. **The rope and cursor**, Rust — the text, and the only thing with
   a persistence story; every edit returns a new one.
2. **The program** — the parsed, typed tree and the running G-machine
   with its channels and signals; the channels are the wire between
   the picture and everything else.
3. **The instrument** — what `doc/manual.md` already calls *the
   editor's model*: engine, rebuild worker, transport, keyboard, and
   parameters keyed by name rather than node id, a decision about
   identity.
4. **The score** — the `Roll`: a six-column relation, onset, offset,
   leaf, key, velocity, manner, its leaves carrying provenance to a
   line.  For a `.notes` the parsed records are the model on disk and
   the roll is derived.
5. **The gesture state** — holding, the rail's grab, the band, the
   resize, the ruler, the taps, the selection, the group: a statechart
   written as tuples and `if` ladders on the `Session`.
6. **The command log** — `sessionlog.py`, *a session is a list of
   commands*: the model over time.
7. **The view state** — undo and redo, selection, scroll, zoom, in
   `Window`.

The honest reading: gestate chose the text as the source of truth on
purpose and everything else is a projection — the acme and Lilypond
family, and defensible.  The costs are yesterday's: every projection
is a cache to recompute (the five seconds), item 5 has no model at
all, only variables, and nothing names which of the seven a command
edits — `transpose` edits the text and `select` edits the `Session`
and both look alike on the command line.

## Statecharts, executable and per subsystem — the session's draft, 2026-09-07

Henri: *"I agree they belong into the GUI framework.  Actually, they
might belong as executable statecharts.  Can you come up with
gestate-shaped syntax/grammar for statecharts?  One that captures your
last point, that they must be per subsystem."*  Then: *"Yes, write it
into the GUI card."*

**The grammar is the one the language has, plus a four-line library.**
A chart is a value — an initial state, a transition table, the entry
actions — and the per-subsystem rule is a type, not a sentence:

```
Step s     := Stay | Go s (List Command)
Chart s e  := Chart s (s -> e -> Step s) (s -> List Command)

run    : Chart s e -> Chan e -> Sig s
beside : Chart a e -> Chart b f -> Chart (a, b) (Or e f)
Or a b := L a | R b
```

Three things this fixes without a keyword.  A chart's step is a
function of its own state and its own event and nothing else, so it
cannot read the world or another chart's state — that is the
per-subsystem law, enforced by `step`'s type.  Its actions are
`Command`s, so every arrow lands in `Session.run` like a keystroke,
the transcript records it, and run-to-completion is what that choke
point already does.  And a chart is data, so one value is executed,
drawn, and enumerated for checking.

**The transport, as it would be written** — hierarchy is a nested
constructor, history is a payload, events carry what the arrow needs
so the chart never asks:

```
State  := Silent Parked | Up Score
Score  := Sounding | Playing
Parked := Parked Int
Verb   := Play | Stop Int | Audition | Seek Int

transport : Chart State Verb
transport = Chart (Up Playing) step enter

step : State -> Verb -> Step State
step (Silent (Parked at)) Play      = Go (Up Playing)  [sound, seek at]
step (Silent p)           Audition  = Go (Up Sounding) [sound]
step (Silent p)           (Stop _)  = Stay
step (Up _)               (Stop at) = Go (Silent (Parked at)) [hush]
step (Up Playing)         Play      = Go (Up Sounding) []
step (Up Sounding)        Play      = Go (Up Playing)  []
step (Up s)               Audition  = Go (Up s)        []
step s                    (Seek _)  = Stay

enter : State -> List Command
enter (Up Sounding) = [allOff]
enter _             = []
```

The one `stop` arrow from `Up _` is Harel's outer transition, drawn
once instead of twice.  Sounding's release of the score's held notes
is an entry action on the state — where `Workbench.set_state` does it
by hand today.

**A gesture, the other subsystem** — press, drag, release, cancel the
escape from anywhere:

```
Hand  := Idle | Pressed At | Dragging At At
Touch := Down At | Move At | Up At | Cancel

hand : Chart Hand Touch
hand = Chart Idle step enter

step Idle           (Down p) = Go (Pressed p)    []
step (Pressed p)    (Move q) = Go (Dragging p q) [preview p q]
step (Dragging p _) (Move q) = Go (Dragging p q) [preview p q]
step (Pressed p)    (Up _)   = Go Idle           [reveal p]
step (Dragging p q) (Up _)   = Go Idle           [commit p q]
step _              Cancel   = Go Idle           [unpreview]
```

The roll's four hands are four of these and the ruler's a fifth, where
today they are tuples and `if` ladders on the `Session` (model 5 of
the seven above).

**Regions.**  The keyboard's off/on/step switch is its own chart and
the pair is one line, `beside transport hands`: the product type is
the orthogonal region, and neither side can reach into the other
because `step`'s type does not let it.

**What the checker gets for free.**  The state and event types are
finite, so a chart is enumerated the way `test/test_transport_model.py`
did it: reachability, dead states, and the pair with no arrow.  The
catch-all `step s _ = Stay` silences that last check; *session's
suggestion:* allow it, and have the check print which pairs fell
through it — a lamp, not a refusal.

**Where it lands.**  A chart lives in the file of its subsystem —
`transport.ges`, `roll.ges` — and the editor loads it the way it loads
`command.ges`, evaluated by the reference G-machine.
`gestate/transportstate.py`'s `step` becomes the first chart, and the
bar draws ‖ from `head transport`.  The window drawing its own charts
is idea 7 arriving by a side door.

**Not covered.**  Timers — Harel's *after 2s* — are an event from a
clock channel and stay outside the core.  A chart for the whole window
is refused by construction: there is no state type for it to be over,
only products of the subsystems' own.

**His reading of the whole list, same afternoon:** *"I think that
we've got ingredients together.  I liked all of the things you digged
up, starting from 'modes are the enemy'.  Most of them I think are
good.  But some of them probably won't belong together.  I think we'll
see what we can get."*

## Two more from Henri — 2026-09-07, evening

**Zooming.**  *"It could be a zooming interface.  That makes sense for
a pianoroll and sheet."*  From the second list above (Pad++,
Bederson): the roll at the editing scale and the page at the compact
one are two zoom levels written by hand today, and the sheet
(`card:gex-sheet.md`) would be a third surface.  *Here:* the text
view already zooms by rungs (`Window.zoom_rungs`) and the desk
remembers the rung; the roll does not zoom, it has two fixed scales.
A requirement on the framework, not a slice.

**Start where you left.**  *"There is one requirement I want that is
not stated: It's that the program would start into the state where it
left from, most of the time.  Some exception occur, but that should be
the thing."*

*Measured the same evening:* stated once already, and half built.
`card:persistent-workbench-state.md`, done 2026-08-18 from his
*"as if that state was a document in itself"*: `<piece>.desk` beside
the file holds the caret, the zoom, the seed, the loop, the octave and
the knob values, and `~/.config/gestate/desk` which piece you were
last in; a bare launch reopens it.  **And the exception is already
decided there** — `gestate/desk.py` §"What is never restored": *a
transport that was playing, and a build*, because a window that
reopened playing would be a stale instrument wearing a current
document.  So *most of the time* is the desk, and *some exceptions*
is that section, and both were his words in August.

What the new states sharpen: the transport now has three, and the
desk writes none of them.  A window that closed *silent* and reopens
*playing* takes the sound card the person had freed on purpose.  That
is Q6 below.

**And for the framework it is one law**: every subsystem's chart
state, minus its named exceptions, is written to the desk at close and
restored at open — Harel's deep history at the window's level, built
from each chart's own history payload rather than from a chart of the
whole window, which §"Statecharts" refuses.  A chart that cannot say
which of its states survive a close is not finished.

**Bidirectional editing, secondary.**  *"bidirectional editing could
be useful.. but make that a secondary goal that is satisfied only if
it's possible."*  From the second list (Sketch-n-Sketch, lenses): edit
the picture and the source changes, edit the source and the picture
changes, held to each other by law.  *Here:* one direction is built
and byte-exact — `transposed`, `carry`, `resize` and `bars` write the
file back from a gesture — and the other is the ordinary rebuild.  So
the goal is not *whether* but *how far*: which edits to the picture
have an exact source edit under them, and which do not (a note whose
pitch is a bound variable, `spec/north_star.md` §"What it edits, and
how the atom is found" — *written elsewhere*, declined).  **Secondary,
his word: the framework never bends its model to reach it, and where
a lens has no exact write-back the picture says so rather than
guessing one.**

## Questions

*The session collected these on 2026-09-07; they are Henri's to answer.  He said he would ask
several of his own, and those go here too, dated, with the answers in
his words.*

1. **What is the model?**  Before any picture: the nouns a command
   line names.  Today they are the roll's events, the selection, the
   group, the section, the tempo.  Is that the model of the framework,
   or one client of it?
2. **What is the framework's own command language?**  The workbench
   has `Ctrl-K`; the roll has its verbs.  Does the framework own the
   verbs, or only the way a gesture reaches one?
3. **Which of the four hard things does he want removed first?**  The
   session's candidate is the eye (idea 7, the window inspecting
   itself); his may differ, and the card is ordered by his answer.
5. **Where is the trial?**  Henri wants the four-language
   recommendation tried *"somewhere before we apply it to gestate"*.
   A candidate the session can name: the transport's three modes,
   `card:transport-modes.md` — small, a statechart by nature, and an
   invariant or two worth checking.  **Answered, Henri,
   2026-09-07:** *"Yes, try the model languages on the transport card
   first."*  Done the same day — `spec/transport.md`; what the
   languages found is its §5.
6. **Does the transport's state survive a close?**  Today none does,
   by the desk's own rule.  With three states, *silent* is the one
   worth keeping: a person who freed the sound card and reopens the
   file did not ask for it back.  *Session's default: restore
   `silent` only; `sounding` and `playing` reopen as today, playing.*
   His to strike.
4. **Day one.**  What does a session do on the first sitting after
   the design?  If the answer needs a decision only he can make, this
   is a decision wearing a card, and it says so here rather than
   queueing.

## What a session does now

Ask, and write the answers in.  Not code.  Henri: *"I am needed again
to design critical parts of it.  Also, I'd like us to explore more."*
