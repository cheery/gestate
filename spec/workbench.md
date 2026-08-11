# workbench.md — the editor, rebuilt for somebody else

*Companion to `spec/editor.md` (widgets derived from types),
`spec/substrate.md` (the canvas in the same window) and
`spec/liveaudio.md` (the engine the editing rides on).  What it
replaces is `gestate/audioeditor.py` and `gestate/audiopygame.py`.*

Two editors exist and both work.  `audioeditor` is a `tkinter` view;
`audiopygame` is a modal pygame view with a canvas tab.  Between them
they are **6132 lines**, they duplicate every decision, and one of them
draws text with a system font while the other draws it with pygame's.

They are also, both of them, tools built by their author for their
author.  That is not a criticism of how they were made — it is what a
tool that grew alongside the thing it edits looks like, and the growing
is why the good ideas below exist at all.  It is a statement about who
can pick one up:

> **The brief for this rewrite is one sentence: somebody who has never
> read this repository should be able to open a file, hear it, change
> it, and hear the change — without being told anything first.**

Everything below is either an idea kept because it earns its place, or a
change made because that sentence is not true today.

---

## What is kept, and why each one earns it

These are the parts worth carrying forward unchanged in spirit.  They
were not obvious, they are not standard, and several are better than
what commercial tools do.

**The model imports no toolkit.**  `Workbench` owns the playing
instrument, the rebuild worker, the transport, the parameters and the
keyboard, and it can be driven with no window in the room.  That single
line of discipline is why the editor has tests at all, and it is why
this rewrite is possible: the model is already separable, so what
changes is the view.  It stays.

**Knobs are placed, not listed.**  `audiospans` knows which line each
control source was declared on, so a parameter is drawn *beside its own
declaration* rather than in a panel you have to read against the code.
Almost nothing does this.  It stays, and `spec/editor.md` generalises it
from knobs to a type→widget table.

**Parameters are keyed by name, not by node id.**  An edit renumbers
nodes; a knob remembered by id jumps to a different parameter the moment
you add a line above it.  The name is what the person turning it thinks
they are turning.  It stays.

**Applying an edit never blocks.**  A rebuild is hundreds of
milliseconds and a GUI callback that waits for one is a frozen window.
`apply` returns at once and the answer arrives later as a message.  It
stays.

**Every action says what it did.**  Each `Pane` method returns a short
string — that string is what the status line shows *and* what a test
asserts on.  "An action that reports nothing is one nobody can check" is
exactly right and is a rule other projects should steal.  It stays, and
gets a second job below.

**The keyboard has no path of its own.**  A typed key becomes a message
and goes where a real controller's notes go; the engine cannot tell
them apart.  It stays.

**Layout arithmetic is shared by drawing and hit-testing.**  Where a
knob is painted and where a click lands come from one function, so they
cannot drift, and both can be checked without a window.  It stays.

---

## What makes it unusable by a stranger

Named plainly, because a rewrite that does not know what it is fixing
will re-grow it.

**1. The modes.**  `text`, `command` and `canvas`, with `Esc` outward
and `Return` inward; piano mode and step-piano mode on top of those;
and four dialogs (search, reference, file choice, holes) that are modes
in all but name.  `audiopygame`'s own docstring spends three bullet
points defending the design — *"a mode you cannot see is worse than one
you choose"* — and the defence is sound.  It is also the tell: a
feature that needs three paragraphs before anyone can use the space bar
is a feature that has failed a stranger, however well argued.

**2. Single-letter commands with nothing to read.**  From command mode:
`s` applies, `p` opens the piano, `P` opens it in step mode, `?`
identifies the word under the cursor, `o` loops, `O` loops everything,
`[` and `]` move the loop ends, `/` searches, `n` and `N` step through
matches.  Every one is a good binding *once you know it*.  There is
nowhere in the window that says so.

**3. One class holding everything.**  `Pane` has **101 methods**;
`Workbench` has 66.  Search, the reference browser, file switching,
holes, knobs, the piano, loops, undo, dialogs and the transport are all
in one object.  Nothing can be understood without understanding most of
it.

**4. Two views drifting.**  Two editors, two painters, two sets of
bindings, one model.  A fix goes into whichever one the author was using
that day.

---

## The shape

Three pieces, one direction of dependency, and no piece knows what is
above it.

```
   Workbench  ──── the model.  No toolkit, no window, fully testable.
       │           An instrument, a rebuild worker, a transport,
       │           parameters, a keyboard, and a list of commands.
       ▼
   Session    ──── what a gesture means.  No toolkit either.
       │           Turns a command name, a click or a note into a
       │           change to the model, and returns a sentence.
       ▼
   shell/editor ── the view.  Owns the window, the rope, the loop.
                   Draws text, chrome and widgets; sends gestures back.
```

`shell/editor` is built (`journal.md`, this session): a persistent rope
in Rust, a public-domain bitmap font, a window that owns its own event
loop, and a C ABI whose boundary carries a *version* rather than a
document — so a keystroke never crosses a language boundary and the
model is told only that something happened.

`Session` is what `Pane` was, minus everything a command list makes
unnecessary.  The estimate is under three hundred lines, and if it is not
then something below is wrong.

---

## No modes.  A command list instead.

**This is the change that answers the brief, and everything else is
detail.**

There is one mode: you are typing.  Every other thing the editor can do
is a **command with a name**, and there is a list of them you can open,
filter and read.

    Ctrl-K            open the list
    (type to filter)  "loop", "play", "piano", "bank" …
    Return            do it

The list is not a menu the view maintains.  **The model supplies it** —
`Workbench.commands()` returns `(name, summary, key)` triples — so a
capability cannot exist without appearing in the list, and the view has
no table of its own to fall out of step.  That is `reference.py`
deriving pages from sources and `internals.py` deriving faces, applied
to the one part of the editor a person has to discover.

Keys are **shortcuts onto commands**, never a separate vocabulary.
`Ctrl-S` is the `apply` command; the list shows `apply · Ctrl-S`, so
pressing the key once teaches the name and reading the name once teaches
the key.  A command with no key is reachable; a key with no command
cannot exist.

Three consequences worth stating because they are the point:

* **Nothing is undiscoverable.**  The answer to "what can this do" is a
  keystroke, and the answer is complete by construction.
* **The ABI does not grow a verb per feature.**  The view sends
  `command(name)`; adding a capability is a row in the model.
* **The tests get simpler.**  A command is a name and a sentence;
  driving the editor in a test is a list of names, which reads as
  documentation.

What is *not* claimed: that modal editing is bad.  `audiopygame`'s
argument — that the old `tkinter` editor was already modal without
saying so — is correct, and vim's model is a good one for people who
have chosen it.  The claim is narrower: **a modal editor cannot be the
first thing a stranger meets**, and this is the first thing.  A vim
binding layer over the same command list is a later, additive change.

---

## A command is a transition

The list is the discoverable face of something smaller: a **command
language**, in which every command is one transition of the model.

    command : (Workbench, args) -> (Workbench', sentence)

The sentence is the one `Pane`'s methods already return — *"applied"*,
*"looping bars 4-8"*, *"no such bank"* — and it now has three readers
instead of one: the status line, the test, and the transcript.

**Four things fall out of that shape, and they are the reason to state
it rather than merely to have it.**

*Undo is the model's, not the widget's.*  A transition on a small,
copyable state is undone by keeping the state before it.  The rope is
already persistent, so the expensive half is a pointer; what is left is
a handful of numbers.  `spec/editor.md` requires text undo and forbids
widgets keeping their own history — this is how that requirement is
met rather than merely obeyed.

*A session is a list of commands.*  Recording, replaying and testing
stop being three mechanisms and become one.  That is
`spec/verification.md`'s session transcript, one floor up: the same
argument `spec/dynamicscore.md` makes about a performance — *decisions
are a pure function of the world, therefore a transcript of arrivals
replays it exactly* — applies to editing, because a transition over a
named file is a pure function of what it was handed.

*A test reads as documentation.*  Acceptance 2 asks that the editor be
drivable with a list of names in and a list of sentences out.  With
transitions that is not a testing affordance bolted on, it is the
ordinary way to run the thing.

*The boundary carries names and arguments, and nothing else.*  No
handles, no callbacks, no pointers into the other side's heap.

### Composition, and exactly three forms of it

Commands compose, because a musician's gesture is rarely one thing —
but a command language that composes freely becomes a programming
language, and this project has already refused that shape once.

**Sequence.**  `a ; b` — do this, then that.  A macro, a transcript and
an undo group are all this and nothing else, which is why one
implementation serves all three.  A key bound to a phrase is a sequence
with a name: `loop-to-here` is `set-loop(end := position)`, and the
binding is sugar over the phrase rather than a fourth kind of thing.

**Arguments, typed.**  A command takes an `Int`, a `Name`, a `Span`, a
`Note` or nothing.  This is where `loop 4 8`, `transpose +12` and
`set cutoff 0.42` live, and it is what lets the list stay short: one
`loop` with arguments rather than `o`, `O`, `[` and `]`.  The types are
what let the view *ask* — a command wanting a `Name` gets a filtered
list of names, for free, from the same machinery the command list is.

**The selection as an implicit argument.**  A command that takes a
`Span` and is given none uses the selection.  That is vim's `verb noun`
grammar with the noun made *visible* and built by ordinary means —
shift-arrows, a drag — rather than by a second vocabulary you have to
know before the first verb does anything.

### The language is gestate, restricted

**There is already a suitable language for commands, and it is the one
being edited.**

An editor with a command language of its own would be inventing a
second syntax to parse, a second set of errors to report, a second set
of types to check and a second thing to document — beside a language
that has all four and is in the window.  `spec/dynamicscore.md` ruled
on that shape once already, in its own register: *"No live-coding text
protocol.  Editing the source is the live coding … a second textual
surface would be a second truth."*

So a command is a gestate expression, and the restriction is a
**sublanguage**, which is a kind of thing this project already builds.
`spec/liveaudio.md` counts the precedent while introducing the audio
fragment: *"There is precedent for exactly this move, twice: the
monomorphic Datafun sublanguage and `[: Void :]` as the scores the MIDI
backend will accept.  This is the third."*  This is the fourth.

It comes in the same two parts the others do.

**A type, for the vocabulary.**  `Command`, with the editor's verbs as
ordinary declarations returning one — `loop : Int -> Int -> Command`,
`apply : Command` — and sequencing by the `do` notation
(`spec/monad.md`) that already exists.  This is `[: Void :]`'s trick:
the restriction that a score be *performable* is carried by its type
rather than by a check beside it, and `Command`'s vocabulary is carried
the same way.

**A check after inference, for the restriction.**  The type admits
`case`, recursion and a lambda; the sublanguage must not.  So a check
in the shape `gestate/subgrammar.py` names what it wants and *reports
why, not merely that* — which is `spec/liveaudio.md`'s own requirement
of the fragment check, and the difference between a refusal you can act
on and one you can only obey.

What the check permits is exactly:

    command  ::= name literal…            an application spine
               | do { command ; … }       sequence

**And that is the same restriction `spec/editor.md` already states**,
one level up.  The literal rule there — *widgets attach to declarations
whose body is one literal, or one constructor of literals*, checkable
as "a `VNum`, or a `VApp` spine of a constructor over `VNum`s" — is an
application spine over literals.  A command is an application spine
over literals.  The widget rule restricts what a widget may *edit*; the
command rule restricts what a command may *be*; both are the same shape
and both are decidable from the AST.  That the two arrived from
opposite ends and met is the reason to believe the shape is the right
one.

Three dividends, none of which a bespoke grammar would have given:

* **The transcript is a gestate program.**  A recorded session is a
  file you can read, edit, diff and re-run, in the language you were
  already editing — not a log format with a parser of its own.
* **The command list derives itself.**  Commands are declarations with
  types and doc comments, so `reference.py`'s machinery — which already
  turns exactly that into `doc/ref/` — produces the palette.  A
  capability cannot exist without a name, a type and a sentence,
  because that is what declaring one *is*.
* **The types tell the view what to ask for.**  A command wanting a
  `Name` gets a filtered list of names for nothing, because the
  argument's type is known before it is asked for.

---

## The chrome is a description

The view owns the window, so the view draws everything.  The model
cannot reach a canvas and must not learn to.  So the model publishes a
**description of the furniture**, once per change, and the view draws
it:

    status   : one sentence — what just happened
    trouble  : the compiler's complaint, and the row it belongs to
    knobs    : [(name, row, value, min, max, kind)]
    banks    : [(name, row, voices, listening)]
    transport: playing, position in beats, loop span
    commands : [(name, summary, key, argument types)]
    choices  : [(text, note)] — what the argument being asked for could be

This is `shell/panel`'s pattern exactly — a descriptor in, a display
list out, one painter — and it is the reason the plugin panel and the
editor will look like one application rather than two.  A `knob` at
`row` is drawn in the margin at that row: the placement rule survives
the move, because the row is a fact the model already has from
`audiospans`.

Gestures come back the same way, flat and few:

    command(name, args)        a command was chosen, with what it takes
    filter(query)              the list is showing this much of a query
    wants(name, nth, query)    what could the nth argument of this be?
    asked()                    done asking
    turn(name, value)          a knob was dragged
    note(midi, on)             a key was played
    edited()                   the text changed
    state(zoom, rungs, undos, redos)   where the window's own state is

**The argument types are what let the view ask.**  Eleven of the
twenty-nine commands take something, and picking one of those is not
running it — the list becomes a question about its first argument, and
the prompt is the usage line with what has been given standing where its
placeholder was: `loop 4 <int>`.  A `Named` argument gets the names,
ranked, from the model; an `Int` or a `Text` is typed, because offering
a list of numbers would be a menu of guesses.  Backspace on an empty
argument steps back one, and then out of the question into the list you
came from — picking the wrong command is the ordinary mistake here.

Which names a query means is ranked *in the model*, by the same rule
that ranks commands, and for the same reason: it is a decision, and a
decision belongs in one place.

**`state` is a mirror, not a request.**  Undo and the zoom live on the
window's thread, and `undo` has to answer *"undone"* or *"nothing to
undo"* the instant it runs; it cannot wait a frame to find out which.
So the window volunteers its counts whenever they move and the model
answers from its copy.  The alternative — a synchronous call into the
rope from another thread — is the one thing this boundary exists to
prevent.

Orders go the other way, for the same reason:

    zoom(steps)   undo()   redo()   goto(line)   insert(text)

A command that is about the window leaves one of these and the window
obeys it on its next frame.

**Nothing in that list is a pointer into the other side's memory**, and
nothing needs to be freed by the wrong language.  That is not
minimalism for its own sake: the boundary is where two runtimes'
lifetimes meet, and every richer thing offered there is a
use-after-free waiting for a rebuild.

---

## Widgets, and the rule that keeps them honest

`spec/editor.md` is the design and stands unchanged.  Its rule is the
load-bearing one:

> **A widget is a view over a span of source.  Dragging it is a text
> edit.  There is nothing else.**

So a knob drag rewrites the declaration and republishes, exactly as a
keystroke save does; undo is *text* undo, because the moment a widget
keeps its own history the second model is back.  The literal rule —
widgets attach only to declarations whose body is one literal, or one
constructor of literals — is what stops the editor growing cleverness
case by case.

The one thing this file adds: **the control-rate knob keeps its
channel**, and every other widget goes through the text.  That is not an
inconsistency, it is what control rate is *for*; a knob turned while a
chord rings must not recompile the graph under it.

---

## Errors belong at the line

Today the compiler's complaint is one line in a status bar, with the
rest available if you know to ask (`Workbench.trouble`).  A stranger
does not know to ask.

**The complaint is drawn at the row it names**, in the margin, in the
colour the panel already uses for a warning — and the status line says
how many there are.  The whole text is one command away.  A failed build
does not stop the sound: `audiolive`'s rule — *a synth that does not
compile must not stop the one that is playing* — is a promise the editor
should be visibly keeping, so the transport keeps running and the
message sits beside the line that caused it.

---

## What is deliberately not here

* **No second editor.**  `balanced.py` and `audiopygame` are already
  gone — 3458 lines and the 151 tests that held them, plus the rope's
  own 3, which the Rust port supersedes with a replayed-edit parity
  fixture and six thousand randomized sessions.  `audioeditor`'s
  `tkinter` `Editor` stays until this one works, so there is a working
  editor throughout; `Workbench` and `Keyboard` stay for good, being the
  half that was always right.

  Two things were lifted out on the way rather than deleted with the
  file, and the distinction is worth stating because it is the test for
  what a rewrite may throw away: **a screen of chrome may go, a decision
  may not.**  The reference browser's *ranking* — a name match beats a
  prose match — is now the palette's filter.  `_library_entries`, which
  put the language's own forms first because they are in none of the
  library files and searching `wait` therefore returned nothing, is now
  `reference.all_entries`.  Both had a bug fixed in them once; deleting
  them would have been deleting the fix.
* **No reference browser.**  It was 10 methods of chrome over a
  generated index, and `doc/ref/index.md` is a better place to read one.
  Its ranking rule and its index live on (above).  A `reference` command
  that opens the page is enough until somebody wants more.
* **No file switching, at first.**  One window, one file.  Two windows
  is what a window manager is for, and `Pane.switch`/`steal`/`choose` is
  three modes' worth of machinery for a thing the desktop already does.
* **No syntax colouring, at first.**  It is genuinely wanted and it is
  genuinely a separate project: it needs the parser to survive a broken
  file, which it does not have to today.  Named so it is a decision
  rather than an oversight.
* **No vim layer, at first.**  See above: additive, and over the same
  command list.

Each of these is *at first* rather than *never*, and each is a
deliberate refusal to carry a feature across a rewrite before the thing
it hangs on works.

---

## Costs, stated

* **The ABI grows.**  It carries one string and a version today; it will
  carry the furniture description and four gestures.  That is more
  surface to keep in step between two languages, and the mitigation is
  that all of it is flat data with no lifetimes — plus a test that
  drives the whole editor through the ABI with no hand on the keyboard.
* **The command list is a second place a capability is written down.**
  Kept honest by being *the only* place: if the view can invoke it, it
  is in the list, because the view has no other way to invoke anything.
* **Two languages in one tool.**  A contributor now needs Python for the
  model and Rust for the view.  The seam is narrow and typed and the
  model — where the music lives — is entirely Python, which is where a
  person who wants to change what the editor *does* will be working.
* **The tkinter editor's users lose it.**  There is one, and he asked
  for this.

---

## Acceptance

1. A person who has not read this repository can open a file, play it,
   turn a knob, edit a line, apply it and hear the change — using only
   what the window tells them.  Checked by asking one.
2. `Workbench` and `Session` import no toolkit, and the whole editor can
   be driven in a test with no window: a list of command names in, a
   list of sentences out.
3. Every capability appears in `commands()`, and every key is a shortcut
   onto one.  A test asserts the second: no binding names an action the
   list does not.
4. A knob drag and the same edit typed produce identical source, byte
   for byte, comments included (`spec/editor.md`'s property).
5. A build that fails leaves the sound playing and puts the message
   beside the line that caused it.
6. The editor draws a 250,000-character file at the frame rate it draws
   an empty one — held by `shell/editor`'s own measurements, and the
   reason the rope is a tree.
7. Nothing in the boundary is a pointer into the other side's heap.
