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
             doc/notes/notes-on-gui.md — the card read from outside,
             2026-09-07 to 2026-09-08: identity named as the missing
             decision before the morning that decided it, and the
             postcondition's sentence at 10:49
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

## The postcondition — Henri, 2026-09-08

Written a day after the card opened and after two slices had landed,
which `board/README.md` §"The postcondition" says is late; the slices
each carried their own, and this is the card's.  The sentence it
started from, his: *"The vision I have is that GUI development, even,
or especially, for tricky things to edit, would be an easy task for a
session."*  Verbalised with a guest session the same day:

> **GUI development where a session does all the mechanical work —
> model, commands, charts, identity, tests — and the keeper spends two
> minutes with his hands on it to check the feel.**

Names no function, and puts the number where the vision's sentence had
none: not on the session's side, where *easy* cannot be measured, but
on the keeper's — the time his hands are on a slice before he can say
whether it feels right.  A slice that needs more of him than that is a
slice where the mechanical work leaked back to the person, which is the
`because` of this card in one line.  **Nothing measures it yet:** the
two slices landed below record what was built and what held them, and
not how long his hands were on either before he could say — the number
this card's done would be, and the only instrument for it is a clock
beside him at the next slice's gemba walk.

**First hands on it — Henri, 2026-09-08, evening**, on the inspector,
unclocked: *"I did the inspector test.. I think that I should write
some GUI myself, or with some help from session, and see whether I
understand how the inspector maps into the picture."*  Not a number
and not a verdict: what two minutes produced was the next test.  The
postcondition says a session does the mechanical work and the keeper
checks the feel; the check he reached for is to write a small GUI in
the framework himself, with the inspector as the way of finding out
what the picture is doing.  That is the stranger test run by the
author, and the thing it measures is whether the mapping from press to
picture to line can be understood by someone who did not build it that
day.  What a session does for it: nothing in advance — an explanation
handed over first would answer the test for him — and stays reachable
while he writes, and records what he stumbled on.

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

**Damage rectangles, secondary on the same basis.**  *"and damage
rectangles make sense as well, on same basis."*  From the second list:
repaint only the region that changed, instead of the frame.  *Here:*
the window keeps one `dirty` flag and repaints whole when it is set,
and presents every frame regardless, because presenting is what
drains X and the one-behind bug lived in an idle frame that did not
(`doc/memory/gestate-editor-latency.md`); the description is compared
whole and sent only when it differs, which is the same idea one layer
up, at the wire.  A region-level dirty is the framework's, if the
picture-as-data (idea 10) makes a diff of two display lists cheap —
*and never at the cost of idea 9's rule that an idle frame still
presents.*

**The two gulfs — elaborated at his ask, 2026-09-07, evening.**
Norman, *The Design of Everyday Things* (1988), after Hutchins, Hollan
and Norman (1985).  A person has a goal and the system has a state,
and two distances lie between them, one each way.

*The gulf of execution* is the distance from what the person wants to
what the system lets them do — form the intention, choose an action,
specify it in the system's terms, perform it.  Wide when the person
knows what they want and cannot find how to say it.  *Here:*
`card:button.md`, F151 — a stranger could type and nothing typed
reached the sound; the action existed, the path did not.

*The gulf of evaluation* is the distance from what the system did to
the person knowing it — perceive the state, interpret it, compare it
to the intention.  Wide when the thing changed and the person cannot
tell, or did not and they think it did.  **"Very visual", this
morning, is this gulf by another name.**  *Here:* the dragged note
drawn where it used to be (`spec/north_star.md` acceptance 2); the
transport before this afternoon, engine up and score held wearing the
same square as stopped.

*Why the pair is useful:* every fix falls on one side, and the side
says what kind of fix it is.  Execution-side repairs are affordances,
constraints and mappings — the thing shows what can be done to it,
refuses what cannot, the control lies where the effect is; *every
gesture has a command under it* is an execution-side property and the
palette its front.  Evaluation-side repairs are feedback and a visible
system image — the effect at once, where the person is looking, in
terms they can compare to what they meant; direct manipulation's
fourth property, the status line naming the state, the three glyphs.

*What binds it to this card:* both gulfs are bridged by the same thing,
the conceptual model — Cooper's represented model, §"The models".  A
model the person can hold predicts both what to do and what will show,
which is why the command language and the model come first: they
narrow both gulfs at once, where a picture built first narrows the
evaluation side only, and only for the pictures somebody thought to
draw.

*The checks:* the execution gulf is the stranger test — a person with
a goal, the count of steps, the point where they stop.  The evaluation
gulf is the roster from direct manipulation's first property — every
state the model can be in has a distinct picture, and a person shown
the picture can say the state.  Neither is a unit test; both are cheap
because the model is finite.

## Questions

*The session collected these on 2026-09-07; they are Henri's to answer.  He said he would ask
several of his own, and those go here too, dated, with the answers in
his words.*

1. **What is the model?**  Before any picture: the nouns a command
   line names.  Today they are the roll's events, the selection, the
   group, the section, the tempo.  Is that the model of the framework,
   or one client of it?
   **Henri, 2026-09-07, evening:** *"I think it could be a mix of
   algebraic types and relations.. what do you think about that?"*
   *Session's view:* the right pair, and the tree already works that
   way unsaid — the `Roll` is a six-column relation and a note is found
   by a lookup on tick and key; a `.notes` file is a table, a row a
   line; the display list is a relation of items with regions and a
   press is a query over it; the transport's state is a sum type.  The
   rule that falls out: **types for the few, relations for the many.**
   A state, a hand, a verb want a sum type, so illegal states are
   unrepresentable; notes, cells, hits and knobs want a relation, so
   identity is a key — address, tick and key — and not a position in a
   list, which is idea 1's hard problem answered by construction.  And
   the language has the query half: Datafun with seminaive evaluation
   (`spec/data.md`).  If the picture is a query over the model's
   relations, two of the secondary goals fall out of one machinery —
   the derivative of the query is the damage rectangle, and a lens from
   a row to the line that wrote it is the bidirectional edit, exact
   where a row has one source line.  **What would kill it:** seminaive
   evaluation is built for growth, and a deleted note, a cleared cell,
   a shrinking selection are retractions; `spec/data.md` names
   non-monotone constructs as a scope class and says nothing about
   retracting a fact.  *Measured first, before the mix is written as
   the model.*  Otherwise: not answered as a whole until he says so.

   **Measured, 2026-09-07, evening — `python tools/retraction.py`**,
   one program compiled once, a relation of `n` rows built at run
   time, a picture-shaped `for` over it, then the same with one row
   gone; and a transitive closure through `fix`, where ϕ/δ runs:

   | rows | picture | one gone | ratio |
   |---|---|---|---|
   | 100 | 665 ms | 634 ms | 0.95 |
   | 300 | 6.2 s | 6.7 s | 1.09 |
   | 600 | 27.0 s | 27.1 s | 1.00 |

   | chain | closure | one gone | ratio |
   |---|---|---|---|
   | 8 | 375 ms | 88 ms | 0.23 |
   | 16 | 4.2 s | 1.2 s | 0.28 |
   | 24 | 19.8 s | 5.3 s | 0.27 |

   **Two findings, and the second is the one that decides.**  *There
   is no retraction*: every evaluation is whole, ϕ/δ lives inside
   `fix`, and a row gone costs the same as the row kept (ratio 1.0);
   the closure's 0.27 is the chain breaking in the middle, not
   incrementality.  *And the constant factor rules the idea out
   today*: 665 ms for a hundred rows is eight frames, and the growth
   is quadratic (×9 from 100 to 300, ×4.4 from 300 to 600 — *suspected*
   a linear set union under `\/` and `for`, not measured).  `roll.ges`
   draws hundreds of notes in the same G-machine at 80 ms a frame by
   walking a list, so the machine is not the ceiling; the set
   representation is.  **So: types for the few, relations for the
   many, still — as the model on disk and the Python lookup, which the
   `Roll` and `.notes` already are.  The picture as a Datafun query
   over those relations is not available at this speed, and the
   derivative-as-damage-rectangle idea waits on a set that unions in
   better than linear time, or on `crust` running the same query.**
   His call whether that is worth a card; nothing is minted.
   **It was — `card:relations-at-frame-rate.md`, done the same
   evening:** a `for` and a set literal merge pairwise now, the query
   alone is 33 ms over a hundred rows on the reference machine and 8
   ms on crust, 14 ms over six hundred there.  And his plan, closing
   it: *"Planning to run on crust everything that can run there."*  So
   the relations half of the model is back on the table: a picture
   may be a query, on crust.
   **Henri, 2026-09-08, evening:** *"Yes.  I think picture could be a
   query.  What would kill this decision and is it reversible?"*
   Taken as the model's second half, then, with the answer to his
   question written here so the decision carries its own retirement:

   *What would kill it, each with the observation that does:*
   - **The frame.**  Every evaluation is whole (ratio 1.0 above, no
     retraction), so the whole roll must re-evaluate inside a frame:
     14 ms at six hundred rows on crust, against 16.7 ms at 60 Hz.
     Killed by the stacked roll of `arcnotes.ges` — 291 notes, five
     voices, ruler, selection, band, held preview — not drawing under
     a frame on crust as a query.  The generated program draws it at
     80 ms a frame on the reference machine today, so the bar to clear
     is the window's, not the reference's.
   - **Identity in a set.**  A query answers a set, and a set has no
     duplicates; two notes drawing one rectangle collapse to one row
     and the hit table names one of them.  Killed by a picture row
     whose key is its geometry — the rows must carry (voice, tick,
     key), Q7's answer, and the doubled-address test must still pass.
   - **Arithmetic the query cannot say.**  The roll's `Shift` sums,
     the label's `_fit`, the grid's snapping.  Killed by one element of
     the present roll that the query language cannot draw without a
     helper written outside it.
   - **The two machines.**  The query runs on crust in the window and
     on the reference machine headless; the parity fixtures must hold
     for a query-built picture.  Killed by a fixture that passes for
     the generated program and fails for the query.

   *Reversible — while it is one client's inside.*  The `notes` box
   already generates its program; generating a query instead changes
   the generator and nothing else — the wire, the hit tables, the
   chart, the identity keys, the tests all stand — and the generator
   can be put back in an afternoon.  **It stops being reversible the
   day a person writes a picture as a query**, because then the query
   language is what people know and it hardens.  So the order is: the
   roll's own picture as a query first, measured against the four
   above; the language a person writes in stays open until his own
   GUI (§"The postcondition", *first hands on it*) says what he wants
   to write.

   **Kill condition 1, measured the same evening — `python
   tools/queryframe.py`, and `--box` for one roll.**  The rows the
   picture draws today, `(i, x, y, w, tone, dim, mark)` a note, as a set
   of 7-tuples; the picture as a `for` over them unioned with a join
   against a five-note selection; forced whole, beside the generated
   program's frame for the same rolls:

   | rows | the query, reference | the query, crust | today's program, reference |
   |---|---|---|---|
   | 88 — the stacked roll of line 127 | 103 ms | 11.8 ms | 3.4 ms (97 items) |
   | 152 — the page's three rolls | 339 ms | 21.9 ms | 5.8 ms (171 items) |

   Of the reference's 339 ms: rows 54, every note 124, the join 102 —
   a five-row selection joined as a nested `for` costs as much as the
   whole roll.  Of crust's 22 ms: rows 5, every note 12.  Today's
   program on crust is unmeasured; the earlier card put crust at
   thirteen times the reference, which would make the walk under half
   a millisecond against the query's twenty-two.

   **So the first kill condition fires for the reading it was written
   against** — *the picture as a query re-evaluated every frame*: 22 ms
   against a 16.7 ms frame at the page's size, and forty-odd times the
   walk.  Two things survive it, and they are the shape of the slice
   now:

   - **A picture recomputed on change, not per frame.**  Twenty-two
     milliseconds at a press, a commit or a rebuild is a cost nobody
     feels; the rows relation itself is a CAF and recurs only when the
     notes change.  What must stay per frame is the hand's preview —
     the held note's shift, the band, the ruler's end — a handful of
     rows over channels, exactly what the generated program computes
     per frame today.  So: **two layers** — the notes as a query on
     change, the hand as a signal per frame — and the postcondition's
     *the frame is no slower* is measured on the drag, where it bites.
   - **A lookup, not a join, for membership.**  *Is this note
     selected* is a key lookup; a set that is a sorted list can answer
     it in log n by a merge against the selection, and the nested
     `for` answers it in n·k singletons and merges.  Either a
     `member` the language provides or a merge-join the generator
     writes; the 102 ms says which shape the query must not take.

   *What would kill the survivor:* a drag whose commit, through the
   on-change query, is felt — the postcondition's number, his hands on
   a moving note, against the 60 ms the notes editor's own
   postcondition set.  *Reversibility unchanged:* the generator, and
   nothing a person writes.
2. **What is the framework's own command language?**  The workbench
   has `Ctrl-K`; the roll has its verbs.  Does the framework own the
   verbs, or only the way a gesture reaches one?
   **Henri, 2026-09-07, evening — half-open on purpose:** *"depends on
   implementation a lot.. I think verbs should be possible to define by
   the GUI itself, but framework should provide some verbs as well."*
   So two sources of verbs, and the seam between them is what the first
   slice is chosen to find: a chart's actions name verbs, and the
   transport's chart names `sound`, `hush`, `seek`, `allOff` — which of
   those the framework provides and which the transport's own file
   declares is answered by building it, not here.
   **Settled by the second chart, 2026-09-07, evening** —
   `gestate/hands.ges`, the piano's off/on/step beside the transport.
   A second file cannot share the first's action type (no imports), so
   `beside` demands none: the product is the state, `Or` the events,
   and `Or` the actions, each side's tagged with whose it is.  The
   framework owns the seams — `Step`, `Chart`, `Or`, `initial`,
   `advance`, `beside` — and **no verbs**; a subsystem's verbs are its
   own action type, executed by its host; the palette's commands are
   its events.  Two rules a second file taught: a chart's functions
   carry its name, and its constructors must not repeat another's or
   the library's.  And a mistake the composition caught: the product
   ran both sides' entry actions on every step; Harel's rule is the
   side that moved, and the library says so now.
3. **Which of the four hard things does he want removed first?**  The
   session's candidate is the eye (idea 7, the window inspecting
   itself); his may differ, and the card is ordered by his answer.
   **Henri, 2026-09-08, evening:** *"the inspection tools should
   probably go higher."*  The eye, then — with a *probably* on it, so
   §"What is next" puts it first and leaves it his to strike.
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
   file did not ask for it back.  *Session's default was: restore
   `silent` only.*  **Answered, Henri, 2026-09-07:** *"I think that's
   answered already, it should not."*  So no transport state survives
   a close, as `gestate/desk.py` §"What is never restored" says; the
   session's default is struck.
4. **Day one.**  What does a session do on the first sitting after
   the design?  If the answer needs a decision only he can make, this
   is a decision wearing a card, and it says so here rather than
   queueing.
   **Answered by the day itself, 2026-09-07 to 08:** the dialogue
   first, then a slice he chose (*"okay, do the chart library slice"*),
   then two he scheduled (the probe, the second chart) and one for the
   morning after (a gesture as a chart).  Each slice ends in a
   question that is his — §"Landed — 2026-09-08" closes on one.

7. **Identity: by position or by key?**  Henri, 2026-09-08, morning,
   after a guest session raised it: *"Mielestäni meidän kannattaisi
   katsoa 'identity by position vs identity by key' ja miettiä se asia
   seuraavaksi, tehdä siitä jonkin sortin päätös."*  Idea 1's own hard
   part — which drawn thing is the same thing after the picture is
   recomputed — and DDD's *identity is named*.

   **Measured first, 2026-09-08 — the tree answers it three ways in
   three layers, and they disagree.**
   - *The file is values.*  A `.notes` row's identity is its content:
     `notes.doubled` (2026-09-05, his *"the middle one"*) treats two
     identical lines as one place said twice, allowed in the file and
     refused at the gesture.  `spec/drawnscores.md`: a drag in time,
     velocity or manner *"does not change which note it is"*; a drag
     in pitch does, and drops the spelling.
   - *The commands are keys, one field short.*  `transpose <col> tick
     key key'`, `move`, `resize`, `select` address a note by (tick,
     key), so the transcript replays by content.  But the address has
     no **voice**: on `arc.notes`, 7 (tick, key) pairs are shared
     between two voices, and the first chord tried this morning
     answered *"62 sounds 2 times at tick 0, so which note is meant"*
     — a unison doubling cannot be transposed by hand today.
   - *The session is positions.*  `selected`, `group`, `holding`,
     `resizing` hold an index into `roll.events` (17 positional reads
     in `session.py`, 7 in `scorebox.py`).  The rebuild renumbers, so
     `move`, `carry` and `stretch` **spend the selection** on commit —
     and a person who nudges a group twice sweeps it twice.
     `transpose` does not spend it; safe on `arc.notes` because it has
     no chord within one voice (0 of 291 notes), latent otherwise.
   - *The `.ges` roll is the line.*  A `.ges` note is (leaf line, the
     atom whose value is its key) — `spec/north_star.md`'s measured
     rule — and a generated note (`chancy`) has no identity to edit.
   - *The instrument chose names once already.*  Parameters are keyed
     by name, not node id (`doc/manual.md`), which is why the desk can
     restore a knob across a rebuild.

   **Readings, each with what kills it.**
   - **A. Position, spent at every commit** (today, made consistent).
     Cheapest.  *Killed by* `card:notes-editor.md`'s postcondition:
     editing is many nudges of the same notes, and a selection that
     dies at each one is not Reaper's league.
   - **B. The key — (voice, tick, key), the row's content.**  The file
     already says it; the commands nearly do.  Selection and group
     held as keys and re-found after the rebuild; a command answers
     where it put the note, so the selection follows it.  *Killed by*
     the `.ges` roll, where a note has no row, and by two identical
     rows being one identity — which the file already accepts.
   - **C. The line — identity is where it is written.**  `.notes` row =
     line, `.ges` note = line + atom, carried across edits the way
     `move_marks` carries holes.  *Killed by* every insertion above
     moving every line below — a selection held as lines is
     transformed by every edit — and by included files' lines against
     the buffer's.
   - **D. An id column in the file.**  *Killed by* the format's own
     argument: he writes the lines by hand, and an id is ceremony that
     goes stale under copy and paste.

   **Session's recommendation:** B for the `.notes` model, with the
   voice added to the command address (which is also the fix for the
   7 refusals), and C kept for the `.ges` roll, where it is already
   the measured rule.  The framework's law then reads: *identity is
   the model's key, never the picture's index* — an index crosses the
   wire only inside one build, as `previewing` already does — which is
   Q1's *types for the few, relations for the many* with the key
   filled in.  **Three questions his to answer:** is a doubled line
   one note said twice or two notes (B assumes one, as `doubled`
   decided); does the selection follow the note a command moved, or
   stay at the place (session's default: follows, as in Reaper); and
   does the voice belong in the address.  *Open.*

   **Henri, same morning:** *"En osaa sanoa tähän yhtikäs mitään.
   Mietin että kenties se on B mikä on tässä järkevä vaihtoehto.  Tämä
   on yksi vaikeimmista kysymyksistä GUI-käyttöliittymissä.  Voisitko
   miettiä vielä lisää että mitä muita ratkaisuja meillä tähän olisi?
   Vai ovatko nämä kaikki mitä on keksitty?"*

   **The wider map — session, 2026-09-08.**  A to D are one family:
   *a reference, and what it points at*.  Every system that regenerates
   a picture from a source has answered with one of three moves, or a
   mix — **carry identity in the source** (A–D), **maintain it through
   the edits**, or **recover it by matching** — and the families the
   four missed are the last two and one that has no reference at all:
   - **E. Object identity in a live model, the text its
     serialisation.**  Reaper's: a note is an object and *selected* is
     a flag on it, so nothing points at anything and the question
     dissolves.  Here: `.notes` parses to records and *writing the
     shipped file back is a no-op* already holds, so a gesture could
     edit the record and write the file, and the record survives.
     *Killed by* the second writer — a keystroke in the buffer
     re-parses and the objects die — so it holds for gestures only and
     typed edits need G.
   - **F. Marks carried through edits.**  The text editor's answer
     (Emacs markers, OT, Excel rewriting `A3` when a row is inserted
     above it): a reference is a position that the *edit machinery
     moves*.  The tree does this already — `move_marks` carries holes
     through edits — and every command here is a text edit.  C done
     honestly.  *Killed by* nothing structural; it costs a mark per
     reference and holds only through edits the editor made.
   - **G. Reconciliation — no identity, a matcher per frame.**  React
     without keys, git's rename detection: identity is recovered by
     similarity after the fact.  *Killed by* being wrong silently, which
     is F136's class of defect.  Useful only where nothing better
     exists — typed edits — and then a stale selection should be
     dropped rather than guessed.
   - **H. Path identity.**  SwiftUI's structural identity, Dear ImGui's
     ID stack, a musician's *the third note of the melody in bar 5*:
     a position, but inside a hierarchy, so renumbering is local.
     The roll's index already is (bar, voice, ordinal).  *Killed by* a
     note moved across the hierarchy — out of its bar.
   - **I. Selection as a predicate, not a set.**  The band kept as a
     query in the file's own ticks and keys, re-run after every
     rebuild; Excel's range.  *Killed by* a note nudged out of the
     band leaving the selection — right for *a region I am working
     on*, wrong for *these notes*.
   - **J. Creation identity — the command that made it.**  CRDTs:
     (author, sequence) at birth, never rewritten; here the transcript
     is that (`sessionlog`).  *Killed by* the file, which carries no
     birth, so it dies with the session unless written (D again).

   **What the field says about the shape.**  The best-known unsolved
   instance is parametric CAD's *persistent naming* problem — which
   face is "the same face" after the model is regenerated from its
   history — open since the 1990s, and its lesson is exact for a roll
   regenerated from a file: the systems that tried to recover identity
   by matching (G) are the ones still broken; the ones that work carry
   a name in the source or maintain it through the operations.
   Databases' natural-versus-surrogate-key argument is B against D and
   has never closed, because it is a trade and not a fact.  MIDI has
   no note identity at all, and every DAW is E on top of it.

   **The refined recommendation, still his to take:** B as the name
   the source carries (voice, tick, key — the file already made notes
   values); **F for the session**, so a reference follows the note
   through the command that moved it, exactly and without a matcher —
   the command knows where it put the note; and **G never**, so an
   edit the editor did not make drops the selection and says so.  E is
   the cheap road to F for `.notes` and is worth measuring before F is
   written by hand.  *Open.*

   **Henri, later the same morning:** *"tätä tarvitsisi varmaankin
   mittailla tai tutkia.  Ajatellaan laajempaa tilannetta, ei
   pelkästään nuotteja.  Esimerkiksi onhan meillä myöhemmin myös excel
   taulukon solut.."* — and a paper: Coblenz et al., *Kale: A
   Transformation-Safe Spreadsheet System*, arXiv 2608.26345, 2026-08-26
   (UCSD; source and replication package on GitHub, `ucsd-salad/Kale`).

   **What Kale is, read 2026-09-08.**  This question, in a spreadsheet,
   with numbers.  Their name for it is *reference instability*: does
   `B2` in a formula mean the *data* that was in B2 or the *geometry*
   of B2?  Excel answers by rewriting references when rows move — F
   above, marks carried through edits — and the paper's first finding
   is that people cannot predict that rewriting: 7 of 15 answers right
   about what happens to a range when a row is inserted, and in the
   task study 50–83 % of Sheets users left a broken formula behind on
   four of the five risks.  Kale's answer is to make **the reference
   say which identity it means**: `Col[0]` is *the thing* — resolved
   at parse time to a **row id the system assigns and the user never
   sees**, so it follows the row through insert, sort and move;
   `Col[+1]` is *the place* — an offset, geometry, and stays put; a
   whole column or row is the third form; a rectangle `B2:C3` is
   refused because it is a place pretending to be a set of things.
   Names move with cells on sort.  Result: four of seven risk
   instances at 0 % against over 50 % in Sheets; and two Kale users hit
   a *new* error on the sort task — they moved rows expecting the
   place and got the thing — which is exactly question 2 above
   (*follows the note, or stays at the place?*) with the answer that
   neither is right until the reference says.  Not evaluated:
   *queries* — `AVERAGE(Salary[Experience > 10])`, reading I — the form
   the tree has and Kale did not.

   **What it changes on this card.**  Two things.
   - *The kinds are three, not two, and the reference declares its
     kind.*  A reference is to **a thing** (a key the model carries —
     B; Kale's hidden row id is B where the file can carry one),
     **a place** (a coordinate in the geometry — H, the rail's tick),
     or **a set** (a query re-run — I).  Kale's errors, Excel's and
     the CAD problem all come from one kind being silently taken for
     another, and the framework's law is then *a reference names its
     kind and is never converted to another kind without saying so*.
     On the roll: a selection is things, a band is a set (re-run after
     every rebuild, so a note nudged out leaves it — right, because the
     band was a region), the rail is a place.  On the sheet
     (`card:gex-sheet.md`, *its first client with identity by
     address*): `Col[0]`, `Col[+1]`, and a Datafun `for` as the range —
     the query Kale left for future work is the form this tree already
     compiles.
   - *F is a mechanism, not a semantics.*  Carrying marks through edits
     is right inside a command that knows what it moved, and wrong as
     a rule shown to a person: the 47 % is the number.  So a typed edit
     the editor did not make drops a *thing* reference and says so
     (G never), and a *set* reference simply re-runs.

   **What to measure or read next, his to pick:** (1) Kale's source, for
   how a row id persists and what sort does to a name — an afternoon's
   reading; (2) the seven shared (tick, key) pairs on `arc.notes` and
   the 0 within-voice chords, on his other `.notes` files, so the key
   (voice, tick, key) is measured on more than one piece; (3) E against
   F on `.notes` — whether the record survives a gesture edit with the
   byte-exact write, which is a half-day and decides the session's
   half; (4) `card:gex-sheet.md` Q-list gains *which reference kinds a
   `.gex` formula has*, answered by Kale's three plus the query.
   *Open.*

   **Henri:** *"Nämä kaikki voisi tehdä järjestyksessä."*  Done the same
   morning, 2026-09-08, in order:

   **(1) Kale's source, read** (`~/Kale`, 7,250 lines of TypeScript over
   AG Grid).  The hidden id is AG Grid's row-node id, **held for the
   session and never written**: the widget model persists values only.
   A formula is stored as text, `Col[3]`; at parse time the grammar
   action resolves `[3]` to the *displayed* row's node id and keeps it
   in the parse tree; after every structural change (`onModelUpdated`
   → `recalculate`) a string visitor regenerates every formula's text
   from the id — `Col[3]` becomes `Col[5]` because the row it means is
   now fifth.  **So Kale is E, not D**: the object is the identity and
   the visible position is a projection re-derived from it.  Names are
   a field on the cell object, so they follow the row for free.  The
   query form is in the code (`Salary[Experience > 10]`, a `QUERY`
   value): a boolean vector filtered against a column by *index in
   iteration order* — positional inside one evaluation, which is fine.
   Two things the paper does not say: `[0]` means the first *displayed*
   row, so a filter changes what an absolute reference resolves to
   when it is typed; and a formula typed before its row exists is an
   error, not a dangling reference.

   **(2) The key, measured on every `.notes` in the tree — which is
   two.**  `arc.notes`: 291 notes, 0 chords within one voice, 7 (tick,
   key) pairs shared across voices, 0 doubled.  `untitled.notes`: 4
   notes, nothing shared.  The measurement rests on one real piece and
   says: the voice belongs in the address, and the within-voice case is
   untested by any file he has written.

   **(3) E against F on `.notes`, byte for byte.**  For every note of
   `arc.notes` and of the annotated fixture, each of `key`, `len`, `at`
   changed once by F (`notes.retune`, the line rewritten in place) and
   by E (the record edited, `notes.write` canonical):

   | field | E == F | differs | the difference |
   |---|---|---|---|
   | key | 291 | 0 | — |
   | len | 291 | 0 | — |
   | at | 120 | 171 | the same lines, in canonical order |

   And **nothing live calls `notes.write`** — every gesture is `retune`,
   so a file edited by rail drags leaves canonical order and nothing
   puts it back; *writing this file again is a no-op* is a test
   property, not a live one.  So the two are not the same thing wearing
   two mechanisms: **F keeps the line where it was written (identity
   C, the file remembers where you put the note); E re-sorts it to
   where it sounds (identity B, the file is a table)**, and the choice
   is visible in the file after the first move in time.  Cost of E
   otherwise: none — the record survives, and the write is exact on
   every comment.  *His to choose, and the question is now sharp: after
   a rail drag, does the line stay or does it sort?*

   **(4)** `card:gex-sheet.md` carries the reference-kind question and
   Kale's answer.

   **Answered, Henri, 2026-09-08:** *"nuotti saisi lajittua siihen
   järjestykseen mikä on tiedostolle sovittu."*  So the file is a
   table: after a move in time the line sorts to where it sounds, in
   the canonical order `notes.write` already defines.  That settles the
   pair — **B for the file** (a note's identity is its content, (voice,
   tick, key); a doubled line is one note said twice, as `doubled`
   decided) and **E for the session** (the parsed records are the live
   model, a gesture edits a record and writes the file canonically, and
   the record survives its own edit, so the selection follows the note
   a command moved).  Questions 1 and 2 of Q7 fall with it; question 3,
   the voice in the address, is the first thing the slice fixes.  *Not
   built yet — the slice is his to schedule:* every `.notes` gesture
   through parse → edit → `write` instead of `retune`; `selected` and
   `group` held as (voice, tick, key) or as the records themselves, and
   never as an index; `transpose`, `move`, `resize` taking the voice.
   What it changes visibly: a rail drag reorders lines in the buffer,
   and the buffer's line for a note is no longer where it was typed.
   What stays: byte-exact on every other line and every comment
   (measured, 291 of 291).

   **Built, 2026-09-08, midday** — *"ota se."*  Postcondition, written
   first: *after a note is moved or transposed on the roll, the file's
   lines are in the file's agreed order and the note stays selected, so
   the next drag moves the same note, on his piece.*  Landed as three
   things.  `notes.canonical` and one seam, `Session._write_included`:
   every gesture's write goes through it, so the buffer is a table
   after every commit (`retune` unchanged — the field, then the order).
   The selection is a set of keys, `Session.held`, written by the press
   and by `select`; a commit records where it sent the notes
   (`_follow`, `pending`) and the bench's new `rebuilt` hooks fire
   `_settle` after every `_load_substrate`, which finds the keys in the
   new roll — the voice read from the file only where (tick, key) is
   two notes — outlines them, or drops them when they find nothing.  A
   typed `transpose` or `resize` on a doubled address takes the
   selected note (`_note_named`), and refuses with *press the one you
   mean first* when nothing is.  Held by four new tests in
   `test/test_drawnscores.py` (the file sorts, the selection follows
   through two moves, a group is carried twice, a unison doubling is
   transposed) and 163 unchanged ones, three of which changed their
   last line from *spent with the commit* to *held by key*.  **One thing
   found on the way:** comparing the old roll to the new by `id()`
   failed once — a rebuilt roll landed at the freed address — so the
   old roll object is held instead.  **Half of question 3 stays open:**
   the transcript's `transpose` address still has no voice; the
   tiebreak is the selection, and a replay carries the press that made
   it.  Adding the voice to the command is an arity change to four
   verbs, his to ask for.

   **Asked for and done, 2026-09-08, afternoon** — *"laita transkription
   transpose-osoitteeseen ääni."*  The three verbs that share the
   address — `transpose`, `mark`, `resize` — take it as their second
   argument: *the box, the voice, the tick, the key*, coarse to fine.
   The voice is the `.notes` voice, or the bank a `.ges` note was
   assigned to, or `-` for neither; a named voice decides a doubling
   with no press, a wrong one refuses and says who does sound there
   (*no bass sounds 62 at tick 0 — melody and middle do*), and `-` on
   a doubling falls back to the selection or refuses.  A drag spells
   the voice into the transcript itself, read from the file at the
   release.  No tracked transcript held the old shape; eleven test
   calls gained an argument and `doc/ref/commands.md` regenerated.
   **Question 3 is closed.**

## The first slice — proposed 2026-09-07, evening; his to take or strike

Henri: *"what should be the first slice here?  Are we ready to decide
that?  Right now it's bunch of good ideas.. And I think that's where we
should start sculpting it from.  With some questions left half-open."*

**Ready to decide the slice, not the model** — so the slice is the
piece that needs no more model than is already accepted (the sum-type
half of Q1, and the transport's, tried and landed), and that turns the
next half-open question into a thing that can be built and measured.

**Proposed: the chart library, executable, with the transport as its
first chart.**  `chart.ges` — `Step`, `Chart`, `run`, `beside`, the
four lines of §"Statecharts" — loaded by the editor the way
`command.ges` is, evaluated by the reference G-machine; the transport
written in it, replacing `gestate/transportstate.py`'s `step`; the
session's `play`, `stop` and `audition` sending events to it and
running the commands it answers with.  Why this one:

- It is framework and not client — the first piece that every later
  chart, the gestures included, sits on.
- It is already measured: twelve model tests, three bench tests and
  five photographs hold the transport, so a port that changes
  behaviour is caught the same hour.
- It forces Q2 at the seam his answer points at: the chart names verbs
  the framework provides and verbs the transport's file declares, and
  the slice has to say which is which to compile.
- It is small enough to be wrong cheaply.  *What kills it:* if wiring
  chart events into `Session.run` and chart actions back out costs more
  than the library itself, the four lines were the easy half and the
  card should say so.

**Alongside, not blocking — the measurement Q1 waits on:** whether the
tree's Datafun retracts a fact or recomputes, a number on a relation
of a few hundred rows with one row removed.  Half a sitting, and it
decides the relations half of the model before anything is drawn on
it.

**Second, when the first is in:** idea 7's instrument — press a thing
and the window says its region, its channel and the line that wrote
it — because it is the seam "very visual" points at, it is cheap on
today's hit table, and it is what a session walks with instead of
walking code.

*Not chosen first:* a gesture as a chart (the roll's four hands),
because it needs the chart library and touches the notes-editor's
live work; the grid over `.notes`, shelved on this card's own
completion; anything drawn.

### Landed — 2026-09-07, evening

*"okay, do the chart library slice, and the measurement.  Lets see
where we get from here."*  `gestate/chart.ges` is the library, six
declarations; `gestate/transport.ges` the first chart; `gestate/charts.py`
compiles the two once and applies `advance` per event — 0.2 s, then
twenty microseconds a step, measured; `Workbench.transition` executes
the `Do`s and every verb of the session goes through it.  Held by the
fifteen model tests, now through the chart, three bench tests, the
session tests and the gates.  `spec/transport.md` §2 and §6 say the
rest.

**Three things the language said back.**  `Score` was taken by
`music.ges`, so the transport's inner type is `Awake`; a type must be
declared before the type that names it, so a chart file reads
bottom-up; and `where` is not a form, so `beside`'s helpers are top
level.  None cost more than a minute; all three are worth knowing
before a second chart is written.

**What it found about Q2.**  The framework provides *no verbs*: its
six names are structure — `Step`, `Chart`, `Or`, `initial`, `advance`,
`beside`.  The subsystem declares its own action type (`Do`) and its
own event type (`Verb`), and the events are the palette's commands
already, so the transcript records the cause and the chart replays
from it.  So "verbs defined by the GUI itself" is the `Do` type, one
per chart, executed by the chart's host; "the framework provides some
verbs" is, so far, none — the first place it would is `beside`, where
two subsystems' `Do`s must be one type, and that is the question the
second chart will ask.

**The killer named in advance did not fire.**  Wiring events into
`Session.run` and actions back out is `transition`, `_act` and
`_settle`, fifty lines, less than the library's prose.

### Scheduled — Henri, 2026-09-07, evening

*"schedule gesture as a chart for 2026-09-08 (tomorrow morning), lets
do the 1. and 2. today."*  So: **2026-09-08, morning — a gesture as a
chart**, the roll's press, drag and release as §"Statecharts"' `hand`,
replacing one of the four `if` ladders on the `Session`.  Tonight: the
probe (idea 7 as a command), and the second chart beside the transport
to settle `beside`'s action type.

### Landed — 2026-09-08, morning: the ruler is a chart

`gestate/gesture.ges` is the `hand` of §"Statecharts", written as the
third chart — `Idle | Pressed Int | Dragging Int Int`, the wire's own
`Touched Int | Released | Cancel` as its events, and five acts the
host does: `Take`, `Preview`, `Reveal`, `Commit`, `Unpreview`.  Nine
arrows, no catch-all.  `Session._ruler_event` asks it for every touch
and release on a ruler and `_ruler_act` does the acts; the `if` ladder
that was `_ruler_touched` and the ruler's branch of `released` is
gone, and `sizing` is the chart's state with the section's bars beside
it.  Held by the drawn-scores tests that already fed a press, a drag
and a release through the real hit table (unchanged, all 163 green),
and by `test/test_gesture_model.py`, which walks every state and touch
and holds the entry action, the click/commit split and that no hand
is held forever.  Compile 0.13 s, paid when a roll with a ruler is
built; a step under 100 µs.

**What it found — the one rule that made the ruler fit, and will
decide the other three.**  *The chart holds the time, the host holds
the geometry.*  A gesture is state spread across time (hard thing 3),
and that is all the chart knows: whether a touch is the press or the
drag, whether a release is a click or a commit.  Where the hand is
arrives as an `Int` on the event, and what a bar is, where the end is
drawn and the `bars` line at the end stay in the host.  So the same
chart serves any hand on any one thing, and *let go where it took
hold* is decided twice — by the chart in ticks (`Reveal`) and by the
host in bars (a `Commit` that lands on the bars the section has does
nothing) — because the chart cannot know a grid.  **Ratio:** the
chart is 12 lines of arrows and the host 60 lines of acts, so for the
ruler the chart bought a checked skeleton and not less code; what it
bought is that the skeleton is the same one for the next hand.

**And the events are the wire's words, not the draft's.**  The draft
had `Down | Move | Up`; the window does not know which `touched` is
the press, and the chart is the right place to decide that, so the
event is `Touched` and `Idle` is what makes it a press.  `Up` was
taken by the transport anyway — the constructor rule from `hands.ges`
again.

**What the next hand asks, and it is his.**  The note hand — press,
band, end — is three recognisers deciding at the press by geometry:
a note under the point, nothing under it, the note's last eight
pixels.  A chart's event must carry that decision (`Down (Hit)`, with
`Note n | Empty | End n`) or the three stay one ladder in the host,
and the pad's two channels (rail first, pitch a moment later) make
one press two events — which `beside` does not express, since the
two halves are one gesture and not two regions.  So the second
gesture chart needs one design decision before it is written: **does
the hit-test's answer ride on the event, so the chart branches on
it, or does the host pick which of three charts to feed?**  Session's
default: the former, one chart over `Hit`, because a chart the
checker cannot see the branches of is the ladder wearing a type.
`Cancel` is in the chart and no wire sends it; today nothing can
abandon a drag short of letting go.

### Landed — 2026-09-08, evening: the note hand is a chart

*"A."*  `gestate/hand.ges`, the fourth chart and the second gesture:
eight states, four touches, eleven acts, thirty-two arrows, no
catch-all.  The hit-test's answer rides on the event — `Pitch key
(OnNote n | OnEnd n | OnRoll)` — and the pad's two touches are two
events with a state between them, `Railed t`, since the rail speaks
first.  `Session._note_touched` turns a touch into `Rail tick` or
`Pitch key hit`, `_hand_event` asks the chart, `_hand_act` does the
acts; the four `if` ladders that were `_pitch_touched`, `_rail_touched`,
the band and the end, and the long ladder in `released`, are gone.
Held by `test/test_hand_model.py` (every state and touch, the rail
first, an end carries no pitch, no hand held forever) and by the
drawn-scores tests unchanged — 181 green — plus the suites that reach
into the hand (299 more).

**What it found.**
- *The four fields became readings.*  `holding`, `holding_x`, `banding`
  and `resizing` were tuples the ladders kept in step by hand; they are
  properties of `hand` now — the same facts, derived — and twelve test
  sites that asked them read the same answers.  Kale's trick, on the
  session's own state: the thing is held, the old shape is projected.
- *F211, and it was the morning's.*  A diagonal drag was two commands
  at the release, and after the morning's canonical write the second's
  address named a line that had moved.  The chart made the fix the
  obvious one: `Carry` is one act, so it is one command — `carry` on
  the group of one — and the transcript holds one line for one
  gesture.  Found by trying the naive thing on a note whose move
  reorders the file; the existing test's note did not.
- *Ratio:* 32 lines of arrows, about 200 of host — most of it the
  geometry and the commands that were there before, now sorted by act
  instead of by channel.  The chart bought the checker's walk over 48
  pairs and the split that made F211 disappear.
- *Cancel is still unsent.*  `Abort` is in the chart with `Drop` under
  it, and no wire sends it; the third gesture chart will want the
  escape key first.

**What the next hand asks — nothing of his.**  The three remaining
hands (the keyboard's, the fader's, the caret's) are one-thing hands
and `gesture.ges` serves them; the roll's was the hard one and it is
done.  The open thread on this card is idea 1's other half, the
picture as a query on crust; idea 7's window side landed the same
evening.

### Landed — 2026-09-08, evening: the window inspects itself

*"Lets go for the Idea 7, should we?"*  Postcondition, written first:
*with a key held, pressing anything in the window shows in the window
what it is and which line made it, and a press on nothing shows what
it missed, so you check the picture without reading the code.*

**The wire first**, `spec/workbench.md` §"The window inspects itself"
— F101's order: **Ctrl-press** crosses as `pointed <name> <value>`,
the same name and clamped fraction a `touched` carries, as a question:
nothing grabbed, nothing written, no `released`, the hand chart never
hears of it.  (*Pointed*, because `asked` was already the list's word
for *done asking* — found by the first seam test returning nothing.)
The model answers `told <name> <text>` by name; **the region never
crosses** — the window outlines the attachment from its own hit table
this frame and puts the model's words at the press, so if the two
machines ever disagree about *where*, the halo sits beside the wrong
rectangle and a person sees it.  A miss is the window's own: a cross,
*nothing here*, the nearest attachment named with its distance.

**One reader for the command and the picture.**  `describe_touch` in
`session.py` is the words; `probe x y` and a `pointed` both go through
it, held by `test_ask_is_the_press_without_the_grab` (the two say the
same for one point, by construction) — and `Substrate.ask` /
`touch point x y` is the reference half, so a session without a window
inspects the same picture headless.  The window half: `Canvas::ask`
and `regions` in the panel crate, `Walker::ask` / `regions` in the
editor's, `Pointing` in `window.rs` with the clip-aware paint, cleared
by the next press or Escape.  Held by four Python tests in
`test/test_drawnscores.py`, three Rust tests (the order reads back,
the gesture's line, the walker asks and holds nothing), the atlas's
wire gate, and **a stamped driven run**,
`test/driven/20260908-132518-inspector/` — three photographs, read.

**Two things found on the way.**  *`fixme.md` F212*: a note from an
included `.notes` is named by a bare line of the expanded program
(*written at line 246*, for a 158-line file) and the caret goes
nowhere — an older gap in the click path, which the photograph made
visible.  And the pad's extent is the whole band, taller than the roll
it draws, so the halo's top and bottom edges are clipped and only the
sides show — the window's truth about where the pad is, and worth
knowing before anyone reads the sides as a defect.

**Two things for his hands** — not questions to answer here, things
to feel: whether Ctrl is the right key to hold, and whether a miss
naming the channel as the program named it (`__nb_rail_2__`) is a
help or a leak of a mechanism into a person's view.  **The
postcondition's number is still unmeasured** — nobody has timed two
minutes on this — and this is the slice to time it on, because
inspecting is what the two minutes are spent doing.

## What is next — 2026-09-08, evening; his to reorder

Asked the same evening — *"What's the next on line for gui-is-difficult?
Though, note that the inspection tools should probably go higher."*
Before that sentence the card's own tail put the open threads in
this order: idea 1's other half, idea 7's window side, the three
remaining hands.  After it:

1. **The inspection tools — idea 7's window side.**  **Landed the
   same evening**, §"Landed — 2026-09-08, evening: the window inspects
   itself" above.  The kill condition did not fire: the words come from
   one reader and the region from the window's own hit table, so the
   two machines are shown side by side rather than reconciled.  What
   is left of it is his: the key, the miss's wording, and the two
   minutes.
2. **Idea 1's other half — the picture as a query on crust**, so that
   what the window shows is derivable from the model by a command,
   headless, and the inspector above is a rendering of that query and
   not a second reader.  **Decided 2026-09-08, evening — Q1: *"Yes.  I
   think picture could be a query."***  Its slice: the `notes` box's
   generator emits a query over the notes relation instead of a
   program, measured against the four kill conditions in Q1, the roll
   of `arcnotes.ges` line 127 as the piece; nothing a person writes
   changes yet.  **Measured before building** (Q1, *kill condition 1*):
   a query re-evaluated every frame does not fit the frame at the
   page's size; the slice is therefore **two layers** — the notes as a
   query on change, the hand's preview as a signal per frame — with
   membership as a lookup and not a join.
3. **His own GUI, small, written by him** — the postcondition's first
   real check, his words under §"The postcondition".  A session stays
   reachable and writes down what he stumbled on; it does not go first.
4. **The three remaining hands** through `gesture.ges` — the
   keyboard's, the fader's, the caret's.  Mechanical, no question of
   his in them, and the escape key first.
5. **Q7's open half** — the verbs on a doubled address — waits on him
   asking for it, per the midday note.

*Not on the list:* the grid over `.notes`, anything drawn from
scratch, and the two shelved clients, for the reasons §"The first
slice" gave and the notes page's warning against building for the
queue.

## What a session does now

Ask, and write the answers in.  Not code.  Henri: *"I am needed again
to design critical parts of it.  Also, I'd like us to explore more."*
