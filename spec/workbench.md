# workbench.md — the editor, rebuilt for somebody else

*Companion to `spec/editor.md` (widgets derived from types),
`spec/substrate.md` (the canvas in the same window) and
`spec/liveaudio.md` (the engine the editing rides on).  What it
replaced is `gestate/audiopygame.py` whole, and `audioeditor.py`'s
`tkinter` view — `Workbench` and `Keyboard`, the model half of that
file, stay for good.*

**The rewrite is built.**  `python -m gestate.workbench` is the only
window now, and the two editors this file argued against are gone
(`journal.md` §"The editor becomes the editor").  The argument is kept
because it is the reasoning the built thing answers to.

Two editors existed and both worked.  `audioeditor` was a `tkinter`
view; `audiopygame` a modal pygame view with a canvas tab.  Between
them they were **6132 lines**, they duplicated every decision, and one
drew text with a system font while the other drew it with pygame's.

They were also, both of them, tools built by their author for their
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
unnecessary.  The estimate here was *under three hundred lines, and if
it is not then something below is wrong* — and it is ~2,900 lines
today, so the estimate deserves an honest accounting rather than
deletion.  What was wrong was the count of commands, not the shape:
the vocabulary grew 29 → 49 verbs (`fits`, templates, exports, the
symbol grid, transcripts, copy/cut/paste…), and a transition per verb
with its refusals spelled out is exactly what each line buys.  The shape held —
no toolkit, every command a transition returning a sentence — and the
line count is the vocabulary's, which is the one part that was always
going to grow.

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
    file     : the file's name, and whether it is written down
    paint    : what colour a visible line's tokens are (the model's lexer)
    hole     : what every `_` on a line wants, joined and ordered
    knobs    : [(name, row, value, min, max, kind, wired)]
    banks    : [(name, row, held, voices, listening, wired)]
    away     : (row, words) — a score line a listened bank displaced
    perform  : what a played note would do, and who would hear it
    transport: playing, position in beats, loop span
    commands : [(name, usage, key, summary, argument types)]
    choices  : [(text, note, …)] — what the asked-for argument could be
    page     : a reference page to read in the window

(The list above is `furniture.rs`'s vocabulary as built; an unknown
verb is skipped, not refused, so the model may learn a word before the
window draws it.)

This is `shell/panel`'s pattern exactly — a descriptor in, a display
list out, one painter — and it is the reason the plugin panel and the
editor will look like one application rather than two.  A `knob` at
`row` is drawn in the margin at that row: the placement rule survives
the move, because the row is a fact the model already has from
`audiospans`.

**`wired` is the graph's answer beside the text's declaration**, for
knobs and banks alike: the text declares, the graph says whether the
sound reaches it.  A knob the sound never reads wears a cross; a bank
the mix dropped reads **disconnected** where its count would be — and
at every score line that writes it — in
the warm colour rather than the red — a choice being tried, not a
fault — because keys played into a bank nobody can hear is an evening
spent deciding whether the synth is broken, unless the margin says
so.

**Layered away is the score's word.**  A bank whose switch is on is
MIDI's — `listen` answers "the score no longer drives it" — so every
score line that writes `voices.<bank>` is silently displaced, and the
margin says **layered away** at the line itself, in the same warm
colour: the person can *see* the note that is not sounding, and words
beside it are the difference between a choice being tried and an
evening deciding the synth is broken.  Comment mentions do not count
(`duet.ges` has one *suggesting* `voices.lead`, and a suggestion does
not play); the lines are cached at rebuild, because the poll is two
milliseconds and a text scan is not.

Gestures come back the same way, flat and few:

    command(name, args)        a command was chosen, with what it takes
    filter(query)              the list is showing this much of a query
    wants(name, nth, query)    what could the nth argument of this be?
    asked()                    done asking
    turn(name, value)          a knob was dragged
    note(midi, on)             a key was played
    struck(char, code, on)     a key while the piano holds the keyboard
    touch(kind, x, y)          a hand on the canvas: press, drag or release
    edited()                   the text changed
    state(zoom, rungs, undos, redos, saved, top, rows)
                               where the window's own state is

(`boxtouch` was reserved by §"Content boxes" B3 and is retired
unspoken — §"The canvas walks over crust" owns the story; `touched`
and `reading` are reserved there the same way.)

**The argument types are what let the view ask.**  Twenty-five of the
forty-nine commands take something, and picking one of those is not
running it — the list becomes a question about its first argument, and
the prompt is the usage line with what has been given standing where its
placeholder was: `loop 4 <int>`.  A `Named` argument gets the names,
ranked, from the model; a `Path` gets what is in the directory; an `Int`
or a `Text` is typed, because offering a list of numbers would be a menu
of guesses.  Backspace on an empty
argument steps back one, and then out of the question into the list you
came from — picking the wrong command is the ordinary mistake here.

Which names a query means is ranked *in the model*, by the same rule
that ranks commands, and for the same reason: it is a decision, and a
decision belongs in one place.

**`Path` is its own type so that the list can appear.**  It is the same
rule `Named` follows — the type is what lets the view ask — and a path
qualifies because it has a small, knowable set of next steps.  Three
things fall out of it, and each was learned by getting it wrong first:

* **A directory is a step, not an answer.**  Choosing one makes the
  query walk into it and asks again, which is what a file dialog does;
  choosing a *file* is the answer.  The whole new query comes from the
  model, because it is path arithmetic and the view has no business
  doing any.
* **`..` is a path, not a word.**  Its row reads `../` at every depth
  and the query it makes is what stacks, so going up and then down into
  another directory is a walk rather than a fresh start.
* **The file you are in is marked, not selected.**  The cursor opens
  there and the query stays blank, so the list shows where you are and
  the first letter typed is a new name rather than an edit of the old.
* **A space is content, and Tab completes** — the key laws are
  §"The list, and the laws it keeps" (F111, F117); they were learned
  in this box first, against a listing whose first row is `../`.

`steal` reuses all of it to take a name, with what is already there
shown greyed and refused: overwriting is not something a name box should
do by accident, and a `steal` that could would be a delete wearing a
friendlier word.  The greying is a courtesy; the check in the command is
the guarantee.

**Opening the list ends whatever it was asking**, on both sides of the
wire.  `hide` cleared every scrap of the last question and `show`
cleared none of it — twice: once inside the palette, where backspace
stopped backspacing, and once across the boundary, where a reopened
`open` was handed the directory you had walked into instead of the one
you are in.  A pair like that has to be read together to notice.

**`state` is a mirror, not a request.**  Undo and the zoom live on the
window's thread, and `undo` has to answer *"undone"* or *"nothing to
undo"* the instant it runs; it cannot wait a frame to find out which.
So the window volunteers its counts whenever they move and the model
answers from its copy.  The alternative — a synchronous call into the
rope from another thread — is the one thing this boundary exists to
prevent.

The mirror carries nine facts, and each is there because a command's
sentence needs it: the zoom rung and the ladder's length (`zoomIn` at
the top says so), the undo and redo depths, whether the text is what
was last written (`[+]`, and the unsaved warning), the first visible
row and the visible row count (colouring paints exactly the rows on
screen), and — the two newest, riding at the end so a window built
before them still lands — whether a selection exists and whether the
clipboard holds anything, which is what lets `copy` over nothing
answer "nothing selected" instead of a sentence that lies.

Orders go the other way, for the same reason:

    zoom(steps)   undo()   redo()   goto(line)   insert(text)
    show(canvas | source)   warn(text)   copy()   cut()   paste()

`warn` says its words in red beside the caret that is active and
flashes the `[+]` — §"The list, and the laws it keeps" owns the full
contract.  `copy`, `cut` and `paste` go through **the same door the
chords use** (`keys::press_with` on the same `Key`), because two
implementations of what copying means is how they come to mean
different things; their honest refusals — "nothing selected",
"nothing to paste" — answer from the state mirror, which is why the
mirror carries those two facts.

**The canvas has a channel of its own**, beside the description rather
than inside it.  A substrate animates — anything reading `peak` redraws
every frame — while the furniture next to it changes when a command
runs; carrying them together would push every knob and command line
across the boundary sixty times a second to move one dot.  The shapes
are `gui.py`'s own display list, read into `gestate_panel::list::Item`
and painted by **the same painter the plugin panel uses**: a second one
would be a second set of rounding decisions, and the two windows would
disagree about somebody's artwork.

Asking for a canvas that has not compiled yet is the ordinary case, not
an error — `start` builds it on its own thread — so `canvas` says it is
opening and opens anyway; the picture fills in when it arrives.  Only a
file with no `substrate` at all is told it draws nothing.

**And the canvas is an input device**, which no walk over the model's
furniture will discover: a touch target is declared inside the program
(`onTouchY cutoff (rect …)`, `spec/substrate.md`), so the view cannot
know where one is and must not learn to.  It sends every press, drag
and release on the canvas as `touch(kind, x, y)` in the canvas's own
coordinates — origin at the middle of the pane, exactly where the view
put it when painting, so one offset serves both directions — and the
model's substrate does the hit-testing, the grabbing and the clamping,
because the element's extent lives there.  A press wins the pointer
only after the chrome has refused it: a knob painted over the canvas
is still a knob.  This paragraph exists because the first revision of
this spec inventoried the boundary from the furniture alone and lost
canvas input entirely — fixme.md F101, `journal.md` "The canvas lost
its hands".

A command that is about the window leaves one of these and the window
obeys it on its next frame.

**Nothing in that list is a pointer into the other side's memory**, and
nothing needs to be freed by the wrong language.  That is not
minimalism for its own sake: the boundary is where two runtimes'
lifetimes meet, and every richer thing offered there is a
use-after-free waiting for a rebuild.

---

## The list, and the laws it keeps

The palette is the interface's one moving part, and every law below
was paid for by a defect a person found using it — the F-number in
parentheses is the receipt.  They are gathered here because a law
that lives only in the code it fixed is a law the next feature
breaks.

**The lifecycle.**  `Ctrl-K` opens the list filtering commands;
picking one that takes arguments turns the list into a question about
its first (`wants`), whose choices the model ranks; accepting the
last argument runs the command and the call stands *finished* — still
open, showing what ran.  Escape leaves from anywhere.  Backspace is
undo-the-last-keystroke everywhere: it edits the query, and on an
empty query steps back one argument, and then out of the question
into the list — picking the wrong command is the ordinary mistake.

**What the keys mean in the box.**  Space picks and moves on, because
that is how a command line reads — *except* where a space is content:
in a `Text`, which must search for two words, and in a `Path` (F111),
where the accept-the-pick semantics met a listing whose first row is
`../` and nobody had picked it, and a proposed path one Return from
being taken was wiped by the walk.  Tab completes to the row the
cursor is on — a plain row becomes the text, a directory completes to
its own walk and re-lists, as every shell taught — and nothing runs,
because taking the answer is Return's alone (F117).

**A finished call repeats on Return, and walks on arrows only if it
declared a walk.**  `find`/`findBack` are a pair, so Down is the next
match and Up the one before; a call with *no* reverse answers nothing
to an arrow, because `seek 0` re-firing under a hand reaching for
history is an accidental Return (F107).  And **a command that is done
says so**: `open`, `template`, `symbol` and `transcript` send `close`
when their act is complete, because Return-again is right for a walk
and wrong for a second copy of the same code, a second file switch, a
second transcript — and the keystrokes after opening a file are aimed
at the file (F118).  The model says when it is finished, rather than
the view keeping a table of which commands repeat.

**A click outside the list closes it, and still lands** (F116).  The
panel owns the pointer only where it is drawn: a press on a row picks
it, a press on the padding is the panel's, and a press the panel does
not cover closes the list through the door Escape takes — the model's
question ends with it — and then falls through to the knob, key or
line it was aimed at.

**One arithmetic, four readers.**  `panel_box` says where the panel
is; drawing (`frame`), click-mapping (`row_at`), the outside test
(`covers`) and the shadow (`shadow_rows`) all read it.  A menu drawn
by one arithmetic and clicked by another answers somewhere other than
where it is, which is the bug that makes it feel haunted — and it is
what made the flip below a dozen lines.

**The equator decides the panel; the span decides the scroll**
(F121, and the rule is Henri's, refined against the running build).
When the list opens, a caret in the window's upper half sends the
panel to the lower half.  When an ordered insert lands — a template,
a `fits` fill — the span it put in decides both at once: pasted above
the equator, the panel goes low and the span's *first* line stands on
the screen's first row; pasted below, the panel stays high and the
span's *last* line stands on the screen's last row.  Either way the
person reads what the command just did, on the half the panel is not.
Decided at those two moments and never per keystroke, so the panel
does not dance under a typing hand.  For every other ordered motion,
`follow_past` scrolls the caret past the top panel's `shadow_rows` —
which answer zero while the panel is low, so the two mechanisms
cannot fight over one caret.

**A warning stands beside the caret that is active** — the query
box's while the list is up, the document's otherwise, because words
beside a caret nobody is at are said to an empty chair.  The window
says them in red and flashes the `[+]` behind a same-width blank (the
bar must not re-wrap mid-blink); one said into the list stays **as
long as the user is there** — until the list closes — while one said
with no list up fades in a couple of seconds; the flash settles
either way, since a blink that never ends is a blink nobody can read
past.  `open` on unsaved changes is the caller, the moment it is
picked — see the next section for why it warns rather than gates.

---

## Files — opening, switching, refusing

One window, one file at a time; opening another replaces the
instrument under the same rope and view, which is what makes `open` a
command rather than a second program.  The laws, in the order a
person meets them:

**The dialog walks, and resolution knows how the answer was made**
(F122).  A picked row is bare — rows carry names relative to the walk
— so the walk is prepended; a typed query is the whole path already,
and prepending walked it twice: `transcript ../../x.ges` from
`examples/audio/` landed in `/home/`.  The tell is exact: an answer
that *is* the query was typed, one that differs was picked.  (What a
*finished* call re-runs against is F123, open: the walk it resolved
under is cleared by then, and Return-again currently re-derives the
path from wherever the state stands.)

**What refuses, and what starts.**  A file that exists but is not
text refuses with a sentence — the sniff decodes a chunk with its
tail dropped, so a UTF-8 character split at the edge cannot fail an
honest file (F120: a `.wav` used to take the whole editor down, the
decode raising in the gesture loop).  A name nobody has used is a
file being started, not a mistake — the first save creates it —
*except* a missing name wearing one of the binary suffixes this
toolchain itself produces (`.wav`, `.mid`, `.midi`, `.clap`, `.png`,
`.so`), which is a miss, not a request: F120's second face started a
STARTER synth *named* `blip.wav`.  Only those refuse; an editor that
would not start `notes.txt` would be refusing somebody's notes over
another file's format.

**A file that is not a program opens inert.**  `.txt` and `.md` — the
suffix is the one fact known before the file is read, which is what
answers "what says a file is plain" (`roadmap.md` §"Small improvements
queued from use") — compile nothing, ask for no sound card, and take
the syntax off: prose coloured by a program's lexer would be wrong
twice over.  Saving is all applying means there, and `apply` answers
*"saving"*, because *"applying"* would promise a rebuild that is not
coming.  The description says `inert` and the window wears **[inert]**
where the transport would stand, in the warm colour — a mode being
stated, not a fault, the same register as "layered away" — and `play`
says why nothing will: *"nothing plays — the file is inert"*.  The
knobs and the play button going away must never read as breakage,
which is the whole reason the mode has a word on screen.  A `.txt`
being *started* begins empty rather than wearing the STARTER synth:
notes are not born a program.

**Unsaved changes warn; they do not gate** (F113, three refinements
deep).  The barrier below makes discarded edits truly unrecoverable,
so picking `open` while unsaved says *warning: unsaved changes* at
once and holds it up while the question is open — and a person who
chooses a file past that has decided: the switch proceeds, and the
warning dies with the old document.  They got their warning.

**A different file is a different past** (F113).  The switch goes
through the `load` door: text and both histories replaced together,
marked saved because it came off the disk — undo in the new file must
never resurrect the old file's content under the new file's name,
which is one save from overwriting one file with another.  `set_text`
is the other door and *commits*: `fmt` stays one undo away, which is
the only thing that makes a format safe to press.  Two doors, because
one operation with a flag is how the wrong one gets picked.

**The switch is immediate; the teardown is not the loop's** (F109).
The old `(bench, starter, quitting)` goes to a retirement thread; the
new instrument is built *before* the old one is retired and inside a
try, so a file that will not read leaves the old instrument playing
and the status saying why (F120's belt).  The new instrument's own
thread waits on the retirement before asking for the sound card —
the ordering the old in-loop join was really buying — and a start
overtaken by yet another file while waiting its turn never begins.
The quit path stays synchronous and joins the retirement first,
because a daemon thread still inside a teardown when the process ends
is the segfault `Workbench.stop` carries a comment about.  And the
note plumbing follows the text being started, not the disk (F115): an
audition deliberately never writes a file, so allocators built from
the disk left a freshly added bank with nothing behind its switch.

---

## The window's own conduct

Facts the window owns because they are facts about frames, keys and
the platform — the model has none of the three.

**Autorepeat is made detectable** (F106).  X11's default synthesizes
a release+press pair per repeat of a held key, and a fake release
re-arms every guard — the piano machine-gunned with two guards
standing.  `XkbSetDetectableAutoRepeat` on the window's own display
(per-client, so it must be that connection) makes the server send
press, press, …, release: the stream the guards were written for.
Held arrows and letters still repeat — repeats still arrive, only the
fake releases stop.  `GESTATE_EDITOR_KEYS=1` prints what the server
answered, so a fix on this seam can never again pretend to be in the
room.

**The window is named, and wears its face.**  `WM_CLASS=gestate` —
which baseview never sets, and without which a desktop cannot match
the window to anything — and `_NET_WM_ICON`, drawn rather than
shipped: one period of a sine in the caret's blue on the editor's
ground, generated at three sizes from the palette constants in the
same crate, so the icon and the window cannot drift apart.  `python
-m gestate.workbench --desktop` writes the `.desktop` entry and the
same sine as hicolor PNGs, with `StartupWMClass` matching the class
the window declares; run it again after moving the repository or the
venv, because `Exec` pins both.

**The caret does not anchor the scroll** (F119).  Descriptions arrive
whenever the model has news — the transport readout, while a piece
plays, has news every beat — and following the caret on every arrival
snapped a wheeled-away view back in time with the music.  `follow`
runs on a furniture arrival only when the granted *layout* changed (a
content box, the bar growing): the one case it protects, a box
reflowing above the caret pushing the line you are typing off screen.
A scroll is not a request to be returned; only a caret move, an edit,
or a changed layout is.

---

## The transcript is the recording, and the recording is the report

`gestate/sessionlog.py`.  Recording is always on, in memory; the
`transcript` command writes it down; `python -m gestate.sessionlog
<file>` replays it against a fresh editor on the same file and
reports **every answer that moved** — the answers are the diff, and a
replay that says something else is the report.

The format earns its keep three ways in one file: each line is a
command and what it answered (acceptance 2, made durable); text edits
ride as diffs; and `#!` notes carry everything the editor said
unprompted — a player restarting, a build refusing — which is how
F115 was pinned ("restarting the player" two lines above "would not
switch") and how F103's next occurrence is armed.  One afternoon of
2026-08-13 caught three defects in two transcripts, one of them in a
transcript recorded to verify a different fix; the manual (§11) now
teaches users to reach for it first.

Two survivals it did not have at first, both paid for by a transcript
that failed to hold its story:

**The recording survives a file switch.**  A switch used to build a
bare `Session`, so the log restarted with the instrument — Henri's
`its-good-now` transcript answered "nothing has happened yet" one
step after a switch, and the story that *led to* the switch is
exactly the part a reproduction loses.  `_carry` hands the log to the
next session; a `#!` note marks the seam, and the swap itself rides
as one ordinary edit step (`Log.was` is deliberately left holding the
old file's lines), so a replayed command on the far side of the
switch runs against the right text.  The header keeps naming the file
the recording *began* on, which is what the replay opens.

**The header says which text it began on.**  `#: began <fingerprint>`
always — the file can move on under its name, and the replay says
*"the file has moved"* instead of drifting mysteriously (a warning,
not a refusal: `--against` still names a copy as it was).  And when
the file was never on disk — the unsaved `untitled.ges` that used to
replay against nothing — the text itself rides in the header as `#.`
rows, and the replay starts from it.

---

## The piano

The one piece of chrome that is also an instrument, and the seam that
taught F101's lesson twice — so its contract is written here rather
than living in one host's code.  `spec/commands.md` §"Performing" owns
the argument that this is **not a mode**: `pianoOff`/`pianoOn`/
`pianoStep` say what a played *note* does (goes nowhere; sounds; sounds
and is written at the caret), and **focus** says where notes come from.
What is below is the rest of the contract.

**Two roads in, one meaning.**  A typed key crosses as `struck(char,
code, on)`; a drawn key or a controller crosses as `note(midi, on)`.
Which letter is which note is **the model's fact** (`Keyboard`'s
tracker layout — `zsxd…` one octave, `q2w3…` the octave above), because
a window that knew the mapping would be a second one to keep in step.
The window sends what was pressed; the model says what it means.  Both
roads meet at the same door every scheduled note goes through
(`audiomidi.Notes.feed`): a note is the same thing whether a schedule
or a hand decided it.

**A release ends the note the press began.**  `struck` carries the
physical keycode precisely so releases match presses: recompute the
note from the character and an octave moved mid-hold releases the wrong
one, and X11 delivers releases with an empty `char` often enough to
matter.  The same rule is why `octave` lets go of everything it holds —
the key that would release a carried note has just changed pitch.

**Auto-repeat is not a second press.**  X11 streams presses while a key
is held, and each one would be another note on a voice already
sounding.  Each side swallows repeats at its own seam — the shell
tracks which keycodes are down and the model refuses a `press` of a
note already held — because either side alone leaves the other's
callers exposed.  (F106 is the defect against this law.)

**Losing the keyboard lets go of every key.**  Escape, a click into the
text, and opening the list (`Ctrl-K` reaches past the piano because it
holds Control) all hand the keyboard back — and each one releases
whatever the piano was holding, because a release delivered to wherever
focus went is a voice that is never handed back.

**A stepped note is a text edit.**  It goes through `insert`, the same
door as typing, so `spec/editor.md`'s rule holds with no special case:
undo is text undo, the file is the one truth.  The written note ends
with its separator, so two steps are two notes rather than one number
growing digits.  (F108 is the defect against that sentence.)

**Drawn honestly, or not at all.**  The band sits above the status line
and takes its room from the document, never covering it; the label row
is inside the band.  Two octaves of keys, black drawn over white — and
hit-tested in drawing order, black first, so the answer agrees with
what somebody sees.  A piano nobody is listening to is drawn dead, every
key grey: a bank only takes a note if its payload has a `FromMIDI`
instance *and* its switch is on, and neither is visible in the text, so
a live-looking piano that plays nothing is an evening spent deciding
whether the synth is broken.  A held key is drawn down and **says its
MIDI number on the key**, grey, only while down — the note that is
sounding is otherwise a fact you reconstruct by counting octaves.  The
corner says what a played note would do, and when the piano has the
keyboard it says so and shows it (`[the keys play]`, a lit strip),
because a focus is only not a mode while you can see where it is.

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

## The canvas walks over crust — the vocabulary first

*The move is `roadmap.md` §"The canvas walks over crust"; this section
is its boundary, written before any window learns a verb of it —
F101's law, applied prospectively for once.  The machinery it names is
built and tested: `shell/panel/src/substrate.rs` walks the same
compiled structure the reference machine walks, `interact.rs` owns the
grab, and `tests/substrate_parity.rs` pins both against `gui.py` — on
lantern itself.*

**Built, in the order written** (2026-08-14, the same day): the model
speaks `touched` first; the payload door (`Substrate.payload()`,
`ged_set_walk`, `walk::Walk`); the window walking it
(`walk::Walker` over `gestate_panel::canvas::Canvas` — the CLAP
plugin's own driver — animating at the window's frame rate, 240
drawn/0 idle against the loop's best 38 Hz); then `reading`
(`observe` returns what it wrote, `ged_set_readings`,
`Walker::hear`), which is what retired the model's per-frame walk:
while a crossed canvas shows, the gesture loop's whole frame is one
`observe` and a string compare.  A canvas that cannot cross —
outside crust's pure core — keeps the shapes wire exactly as it was.

**The principle: coordinates never cross the wire; meanings do.**
Today the window sends `touch(kind, x, y)` and the model's substrate
does the hit-testing, because the element's extent lives there.  When
the window walks the substrate, the extent lives *in the window* — so
the hit-testing, the grab and the clamp happen where the picture is,
exactly as the plugin panel already does, and what crosses is what the
gesture *meant*:

    touched <name> <value>       the canvas wrote a channel

`name` is the channel's declared name — the program named it once, and
nothing is routed by anything else.  `value` is what the attachment's
own rule produced: the fraction of the element's extent, already
clamped there, exactly the number `gui._gesture_value` defines.  The
window never invents a value; it runs the same rule the reference
machine runs, and the parity fixtures are what keep "the same rule"
true.

**The model's half of a `touched`** is what `Workbench.touch` already
does after its walk, minus the walk: the value goes where `control`
finds it by name, so the sound follows; and the reference substrate is
kept in step through `Substrate.write`, so the model's picture — the
one tests and headless runs see — agrees with the one on screen.

**Three dividends, and they are why the verb is shaped this way:**

* **The transcript finally records the canvas.**  `touch(kind, x, y)`
  never entered the recording, because a coordinate is meaningless
  without the walk that interprets it — the known replay gap.  A
  `touched` is a fact about the program (`touched "warmthChan" 0.62`),
  recordable like any command and replayable against the reference
  machine by name.
* **`boxtouch` retires before it was ever spoken.**  B3 reserved
  `boxtouch <id> <kind> <x> <y>` for the shapes-wire world, where a
  box's coordinates needed a box to belong to.  A box under crust is
  more of the same walk, in the same program's channel namespace, so a
  touch in a box is a `touched` like any other — no id, no
  coordinates, no second vocabulary.  Reserving before speaking is
  what made this retirement free, which is F101's law earning its
  keep twice.
* **A press that lands on nothing crosses as nothing.**  The window
  knows, so the wire stops carrying the misses.

**The other direction: readings.**  `observe()` writes the
instrument's facts — `peak`, `rms`, `position`, the bands — into the
substrate; the window's walk needs them instead.  They cross as

    reading <name> <value>

on the canvas's own channel, beside the description — the same
argument that put the picture there: readings move every frame, and
the furniture does not.

**The payload.**  What the window must be handed to walk at all is
exactly `gestate-clap`'s `engine::Substrate`, at runtime instead of
compiled in: the serialized G-machine program (`crust.serialize`
writes it today), the entry, the `Sub` constructor tags — a tag is a
position in this program's own table and cannot be derived, only
carried — and the declared channel names in written order, with the
values as they currently stand, so a rebuild does not snap every fader
back to its default.  It crosses on its own channel, not as furniture:
it is kilobytes with newlines in it, and it changes on rebuild, not on
keystrokes.

**What stays where it is.**  `show(canvas|source)` and the `canvas`
command are unchanged — when the canvas exists is still the model's
answer.  `gui.py` remains the meaning: `touches()` stays the oracle,
headless runs and `audioperform` still walk the reference machine, and
the parity fixtures are the bridge's load test.  The Python substrate
stops ticking per frame while a window walks — that is the point —
but it does not stop existing, because a machine with no reference is
a machine whose bugs are definitions.

**Seam tests before the window speaks** — the order F101 demands:
`touched` handled in `session.act` and exercised by tests before any
Rust sends it (an unknown gesture already answers "no gesture", so an
old model meeting a new window loses a fader drag, not the editor);
`reading` is the model's own word going the other way, and its shape
is pinned by a test when its channel exists.  In the transcript,
consecutive `touched` on one channel coalesce to where the slide
ended — the dialog's rule, for the same reason: a step per motion
event would push the run-up to the bug off the top of the recording
that exists to hold it.

## Content boxes — the rows grow a height

The margin proved the idea sideways: a knob beside its own declaration
is content anchored to source.  This is the same idea grown downward —
content that interleaves with the text, occupying room *between* lines
(`roadmap.md` §"Content boxes" is the argument; this section is the
contract).  **The mechanism is built and this section was written from
it** — `view.rs`'s row table, held by the "Content boxes" tests in
`tests/view.rs` — which is the reverse of this file's usual order and
deliberate: the slots table was small enough to design in code, and
what follows is what the code decided.

### The row table

A row is a **band**: its line of text, then sometimes a content box —
extra height the view granted under it.  `View::slots` walks the bands
from `top` and answers where every visible row sits; `top_showing` is
the same walk run backward for scrolling.

> **One walk, every reader.**  Layout (`frame_with`), hit-testing
> (`hit`, `knob_hit`, `bank_hit`), scrolling (`follow`, `clamp`, the
> wheel, the page keys), `caret_at` and the `top`/`rows` mirror the
> model colours by all read the same table.  That is the whole
> invariant, and it is why a box under line 12 cannot make a click on
> line 13 land anywhere but line 13.

This is "layout arithmetic is shared by drawing and hit-testing" —
already a rule this file keeps — surviving rows that are no longer one
height.

### The decisions, each with its reason

* **The table lives on the `View`, set from the description** — the
  `piano`/`aside` precedent: a furniture-derived layout fact.  The
  rope, the undo and the caret never learn of it, because **a box is
  never text**.
* **Heights are in cells**, so a zoom scales a box with the text it
  annotates.
* **`top` stays a row index.**  Scrolling is by rows, a box travels
  with its line, and the wheel never lands half a box.
* **The view says how tall, deterministically.**  The height of a box
  is a function of the description and the view's own width — the
  label precedent: the box is written down and the content fits it.
  There is no negotiation protocol; content that needs more room asks
  by *describing* more, which changes the table on the next
  description.  (This was the roadmap's open question, and it is now
  decided this way round.)
* **A click inside a box answers the box's anchor line** — a caret has
  to land where a person can see the sense of it — until B3 gives
  boxes hands of their own.
* **The margin answers only in text bands.**  A pointer inside a box
  must not turn the knob it happens to sit under.
* **`follow` guarantees the caret's text band**, not its box: the
  promise is the line you are typing on.
* **`View::rows` is capacity, not layout** — equal to `slots().len()`
  exactly when no boxes exist, and no drawing or hit-testing may read
  it.

Nothing grants a height yet, so a window without boxes pays nothing
and behaves byte-identically to before the table existed — the tests
pin that equivalence explicitly.

### What each stage owes, before it is built

* **B1 — the complaint moves in.**  The `trouble` under its line as a
  read-only box, exercising anchoring, scroll and follow with content
  that already crosses.  What the wire owes first: the *whole*
  complaint — today the model sends only the first line
  (`session.furniture`), and a one-line box proves nothing.  Several
  `trouble` rows per line, stacked by the view, keeps an old window
  drawing the first and losing nothing.  **Acceptance**: a two-line
  error under line 12 pushes line 13 down; the caret, a click on line
  13 and `goto 13` agree about where it went; the box follows its line
  through edits above it.
* **B2 — a box is a picture.**  A `box <id> <line> <rows>` furniture
  verb (unknown verbs are skipped, so an old window loses boxes, not
  the file), and the picture channel grows *sections*: a `box <id>`
  line switches the target, the unnamed leading section stays the
  whole-window canvas.  One painter, offset and clipped to the band —
  a box is a canvas with a row for an anchor, and deliberately not a
  second content system.
* **B3 — a box can be touched.**  The gesture was reserved here
  before any window learned it — F101's lesson as law: `boxtouch
  <id> <kind> <x> <y>`, coordinates in the box's own pixels.  **Then
  the reservation paid off by being cancelled**: under §"The canvas
  walks over crust" a box is more of the same walk in the same
  program's channel namespace, so a touch in a box is a `touched`
  like any other — no id, no coordinates, no second vocabulary.
  Nothing to retire from any window, because no window ever spoke it.
* **B4 — the score editors.**  Bound by the widget rule above: a box
  is a view over a span of source, every gesture on it is a text edit,
  undo is text undo.  The door that exists is whole-document `replace`
  — one commit, one undo entry — and a finer `patch` order is earned
  only if caret preservation across a splice turns out to matter in
  the hand.

Still open, and to be answered before B4: what a chancy score shows (a
seed-labelled take is the candidate); whether every musical gesture is
a span rewrite (`fmt` being idempotent may be the whole answer); and
the third focus — a box that owns the keyboard appears in
`command.ges` or it does not exist.

---

## Errors belong at the line

When this was written, the compiler's complaint was one line in a
status bar, with the rest available if you knew to ask
(`Workbench.trouble`).  A stranger does not know to ask.  This is now
built as stated below.

**The complaint is drawn at the row it names**, in the margin, in the
colour the panel already uses for a warning — and the status line says
how many there are.  The whole text is one command away.  A failed build
does not stop the sound: `audiolive`'s rule — *a synth that does not
compile must not stop the one that is playing* — is a promise the editor
should be visibly keeping, so the transport keeps running and the
message sits beside the line that caused it.

Where this goes next is B1 above: the message stops trailing the line
sideways and becomes a content box *under* it, whole rather than
first-line-only.

### The status bar may grow — to five lines, and no further

*Built* (`view.rs` `BAR_MOST`, granted in `grant`, drawn in `foot`;
held by the bar tests in `tests/view.rs`).  A status bar is one line
because most answers are one sentence, and one line is why every
message had to be truncated to its first.  The bar grows downward,
**at most five rows**, taking the room from the document the way the
piano does.  Five is a cap, not a target, and anything longer belongs
to the content box under its line or to the transcript — the same
argument as `BOX_MOST`, one floor down.

What the code decided, writing it:

* **Everything wraps to the window's columns** — the status sentence,
  the bar's complaints, and the content boxes' rows alike.  The first
  build stacked pre-split lines and let long ones run off the right
  edge, and Henri saw it within minutes: *wrapping* is what "may grow"
  meant.  Width-dependence means the view re-grants on resize and
  zoom, not only on a description.
* **What fills the extra rows is the complaints about line 0** — the
  unanchorable ones (a clang failure with no position, an internal
  invariant, a refusal with no witness in the file).  An anchored
  complaint gets a box; an unanchored one gets the bar; the split is
  complete and nothing is homeless.
* **The bar does not repeat the status sentence.**  The model's status
  is often `not playing: <first line>`; a row the sentence already
  contains is growth without information, and is skipped.
* **One list, two readers**: `bar_lines` is counted by `grant` and
  drawn by `foot`, so the bar's height and its content cannot
  disagree — the boxes' slots-table rule, one floor down.
* The view grants deterministically from the description; the model
  still does not know the bar exists.

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
  them would have been deleting the fix.  (Since then the `tkinter`
  `Editor` went too — `audioeditor.py` says where and what it cost —
  and `Workbench` and `Keyboard` remain, as promised.)
* **No reference browser.**  It was 10 methods of chrome over a
  generated index, and `doc/ref/index.md` is a better place to read one.
  Its ranking rule and its index live on (above).  What `what` finds is
  now shown *in* the window — the `page` furniture verb — which is a
  page to read, not a browser to operate; the refusal stands.
* **No file switching, at first** — and the *at first* has arrived: an
  `open` command with a `Path` argument, the file list as its choices.
  Still one window, one file at a time; opening one replaces the
  instrument under the same rope and view, which is what makes it a
  command rather than a second program.
* **No syntax colouring, at first** — arrived too, and on the stated
  terms: the model tokenises with the real lexer and sends `paint`
  rows for visible lines, so there is one lexer and one truth
  (`spec/comments.md` is why that clause was load-bearing).
* **No vim layer, at first.**  See above: additive, and over the same
  command list.  Still not built, still additive when wanted.

Each of these was *at first* rather than *never*, and each was a
deliberate refusal to carry a feature across a rewrite before the
thing it hangs on worked.  Three of the five have since arrived, each
after the thing it hangs on did — which is the order the refusal was
for.

---

## Costs, stated

* **The ABI grows.**  It carried one string and a version when this
  was written; it now carries the furniture description, the picture,
  the orders and a dozen gestures.  That is more surface to keep in
  step between two languages, and the mitigation held: all of it is
  flat data with no lifetimes, and `tests/furniture.rs` drives the
  boundary with no hand on the keyboard.
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
8. The scroll runs free while a piece plays; a caret move, an edit or
   a changed layout re-follows, and nothing else does.
9. An ordered insert is read where it landed: first line on the first
   row or last line on the last, by the equator, with the panel on
   the other half.
10. A session transcript replays against a fresh editor and reports
    every answer that moved — and a held piano key sounds once.
