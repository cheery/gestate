# panel.md — the plugin's own window

*Written 2026-08-11, at Henri's request, to be shot at.  Companions:
`spec/export.md` (the shell this grows a face on), `spec/substrate.md`
(the canvas it makes room for), and `spec/crust.md` (the port the
canvas waits on).*

*Status, 2026-08-11: **panel one is built.**  `shell/panel/` is the
crate — display list, software painter, 3×5 font, the two panels, the
gesture machine — all dependency-free and green at 20 tests, plus a
`window` feature carrying `baseview` and `softbuffer`.  `shell/clap`
grew `clap.gui`, the parameter-gesture events and the host's params
extension in `abi.rs`, a `gui` module implementing the vtable, and the
drain into `out_events` in both `process` and `flush`.  Acceptance 1
holds where it is easiest to check: `cargo tree -p gestate-clap` with
default features is **one line**.  `cargo run -p gestate-panel
--example shot` writes the panel as a PPM, and `--example live`
(with `--features window`) opens it standalone with a sink that prints
the gestures.  **Not yet verified: the parented window at run time** —
it compiles and links, and nobody has watched a DAW embed it.*

An exported gestate synth has knobs a DAW can draw and note banks a
keyboard can play, and no way to look at either.  The host draws a
generic parameter list — names and sliders in whatever order the
descriptor happened to list them — and nothing at all for the note
side.  A player who presses a key that no bank accepts hears silence
and has no way to learn why.

This file designs the plugin's own window, and it takes the smallest
first bite deliberately:

> **Panel one draws what the descriptor already knows.  It needs no
> G-machine, no substrate, and no new export.**

## Why that bite, and why first

`spec/substrate.md` ends by drawing a line: a `clap.gui` panel is a
substrate, a substrate is *interpreted by design*, so the panel needs
the G-machine inside the shell.  That is true of the canvas and false
of the chrome, and the difference is worth the whole stage.

Everything the first panel draws is **static data the exporter already
writes**:

| what | where it lives today |
|---|---|
| a knob's name, kind, range, default | `Control { chan, kind, init_bits, knob, min, max }` |
| which controls are knobs at all | `Control.knob` — already separates a parameter from a `voices` channel |
| a bank's name and voice count | `Bank { name, voices, .. }` |
| which notes a bank accepts | `NoteTable.ok` — 128 keys × `levels` velocities, already emitted |
| the payload a note carries | `NoteTable { fields, data }` |

So panel one is a *reader of `descriptor.rs`*.  `crust` learning
`SigCons` and `SigHead` is a real cost with a real design question
behind it (`spec/crust.md`: the collector is a semispace copy, and a
signal cell is a mutable identity — the two have to be introduced to
each other), and none of it is owed before a plugin has a face.

**The rule applies in the usual direction.**  A caller exists: an
exported instrument that cannot show its own knobs.  A second caller
exists and is sharper: a bank whose `FromMIDI` declines a key is
silent, and silence is this project's named failure mode.

## The two panels

### Knobs

One fader per `Control` where `knob` is true, in descriptor order,
each drawn with its channel name, its current value as text, and a
track showing where in `min .. max` it sits.  Drag changes it.

Two rules decide the rest.

**A knob is a parameter, not a slot.**  The editor's knob writes a
control channel because the editor *is* the host.  A plugin is not:
the DAW owns the parameter, its automation lane, its undo, and its own
generic view of it.  A panel that wrote the control slot behind the
host's back would show one value while the host showed another, and
the first automation pass would overwrite the drag with no
explanation.  So a drag emits, to the host:

    CLAP_EVENT_PARAM_GESTURE_BEGIN   (on mouse down)
    CLAP_EVENT_PARAM_VALUE           (per change)
    CLAP_EVENT_PARAM_GESTURE_END     (on mouse up)

and the *host* writes the slot through the path that already exists.
The gestures are not decoration: they are what makes a drag one undo
step and one automation-write region rather than four hundred.

**The panel never reads the audio thread.**  It reads the parameter
values the plugin already keeps for `params_get_value`, which is the
same discipline `spec/substrate.md` S5 states for `peak` — written
once a frame from the view, never from the audio thread.

### Note routing

Per bank, in descriptor order: the bank's name, its voice count, and
**the acceptance strip** — 128 columns, one per key, showing whether
this bank's `FromMIDI` instance accepted that key at all, and at which
velocities.

**The strip scales to the window** rather than owning a fixed cell
width: each key's edges come from the proportion, so the band ends
exactly where the pane does — no overflow when a host narrows the
panel, no gutter when it widens it.  A fresh window opens wide enough
for about five pixels a key, and **that five does not scale with the
text**: a hundred and twenty-eight keys is a picture, not a label, and
tying it to the font would double the window's width to make the
letters bigger, which is not what anyone asking for bigger letters
means.

**And it is labelled, because it could not otherwise be read.**  Keys
of the same state merge into one band — the right way to show "this
stretch answers" — but that leaves a five-pixel key invisible inside a
sixty-pixel octave, and someone counting the blocks between octave
marks counts eleven and concludes there are eleven keys.  The MIDI
number under each mark is what turns the picture into a ruler, and the
caption beside the bank name (`KEYS 48-83`) says the span in words.

This is the panel that earns its place, because it makes a *silence*
visible.  `NoteTable.ok[k * levels + l]` is already exported; nothing
else in the system can show it to a player, and the player's question
— "why did that key do nothing?" — has no other answer.  A bank with
`table: None` takes the structural `(key, velocity)` default and
accepts everything; the panel says so in words rather than drawing a
strip that is uniformly true, because a wall of one colour looks like
a bug.

**And the routing matrix, which is the half you can change.**  Under
each bank's strip is a row of sixteen cells, one per MIDI channel,
showing which channels feed this bank — the shell's `Instance.routing`,
whose cells are *already* stepped parameters (`params_get_info` numbers
them `controls.len() + bank*16 + channel`, grouped under `routing` so a
DAW's generic UI draws the same matrix).  Clicking a cell flips it.

A cell is a **`Toggle`**, not a fader: its value comes from the model
rather than from where in the cell you landed, so a click opens and
closes its own gesture — `BEGIN`, one `VALUE`, `END` — instead of
leaving one hanging until the mouse comes up.  Giving toggles and
faders one shape would mean a checkbox you have to drag.

**Two rules the matrix grew from playing it.**

*Scored banks take no MIDI by default.*  The old default was the plain
diagonal — channel *n* plays bank *n* — which routes the player's notes
into the voices the piece is using, so the piece falls silent and the
player hears only themselves.  `export.scored_banks` answers which
banks the score writes (by parsed mention, so it answers for an
unfolding piece too), and the channels go to the ones it does not.
That is the **two-bank law** the listening pieces are built on — an
arpeggiator cannot listen to the bank it writes — made the default
rather than left to a player to discover.

With one floor: when the piece owns *every* bank there is no free one
to give the channels to, and a plugin that refuses every note is
indistinguishable from a broken one.  `fmpoly` is a piano with a demo
score.  So the diagonal stands there, and the switch below is how a
player hands a bank over instead.

*Un-ticking a channel releases what it is holding.*  Routing is read at
note-**on**, so a cell switched off while a key is down would otherwise
leave the note sounding until the player happened to let go — a control
that looks dead, because the only way to hear it is to stop playing.
The bank releases the voices that channel put there, and nothing else:
notes from other channels, and the score's own notes, are not that
cell's business.  Ticking *on* is still felt at the next note-on,
deliberately — a held note jumping banks mid-sustain is a worse
surprise than waiting for the next key.

## Who plays this bank

A bank is a set of voices, and two things can want them: the piece and
the player's hands.  The routing matrix is the hands' half.  The other
half is one stepped parameter per bank — `<bank> from score` — drawn in
the panel as a `SCORE` switch beside the channel cells, and grouped
under its own parameter module so a DAW draws the two as two panels.

The four states are the point: score on and MIDI off is a piece
playing itself, MIDI on and score off is an instrument, both is
doubling, neither is silence.  Switching the score off does **not**
stop the piece advancing — the cursor keeps its place, so switching it
back on rejoins where the music is rather than where it was left.

Two things the panel says in colour, because the parameters cannot:

* **The channel cells mute when the score plays the bank.**  Not
  disabled — a ticked channel still layers hands over the piece, which
  people want — but the question "who is playing this" has an answer,
  and a matrix that looked identical either way made the reader work it
  out from the switch beside it.
* **The switch goes red when the score never writes that bank.**
  Turning it on is not an error and is certainly not what the presser
  meant: nothing will ever come out of it.  The panel says so rather
  than refusing the click.

**What is still not editable here: which keys a bank accepts.**  That
is the program's own `FromMIDI` instance, and the way to change it is
to change the program — the same answer `spec/editor.md` gives for
everything else, and for the same reason: a second model would drift.
Routing is different because the plugin *already* owns it as
parameters; the panel is drawing a control that exists, not inventing
one.

## One painter, two sources

The design decision that keeps this from becoming a system that has to
be thrown away when the canvas lands.

`gestate/gui.py`'s `_walk` already reduces a `Sub` to a **display
list** and a **hit list**, and they are very small:

    ("rect", x, y, w, h, colour)
    ("dot",  cx, cy, r, colour)

    { axis, chan, region }

That is the entire host-facing drawing vocabulary of the substrate: no
paths, no gradients, no clipping, no anti-aliasing requirement.  Ten
`Sub` constructors, of which `Row`, `Column`, `Pad` and `Sized` are
layout the *language* performs — the host accumulates a centre point
and nothing else.

*(Since written, an eleventh and a third item: `Label w h s c`, and*

    ("text", x, y, string, colour, scale)

*— see §"What the substrate demanded".  The list said "no text" and
that was true of the substrate rather than of the list, since panel one
had been drawing its own names through the very same item all along.
What the canvas gained is the right to say one, in a **box it
declares**; the scale in the item is fitted from that box by
arithmetic both hosts perform, so the sentence that still holds is the
one that matters — nothing here measures a glyph.)*

So the shell grows **a painter against that vocabulary**, and panel
one emits that vocabulary from the descriptor.  When the canvas
arrives it is a *second producer of the same list*, not a second
renderer:

    descriptor  ──┐
                  ├─→  display list  ──→  painter  ──→  pixels
    Sub (later) ──┘

**This is why no widget toolkit is used.**  `Sub` *is* a widget tree.
A retained toolkit — iced, vizia — would insist on owning a second
one, and `spec/editor.md` names that exact disease in its first
paragraph: the GUI owns a model, the code owns another, and they drift
until one corrupts the other.  The panel is immune for the same reason
the editor is: it refuses to have the second model.  An immediate-mode
toolkit (egui) does not retain a tree, but it does own layout, styling
and a GPU backend, all to draw rectangles the language already placed.

The cost, stated: panel one's widgets are laid out in Rust, so a knob
row's *arrangement* is host-side where a `Sub`'s is program-side.  That
is chrome, and chrome is the host's to arrange — but if a knob panel
later becomes a real `Sub`, the painter beneath it does not change.

## Windowing: baseview

`baseview` is windowing for audio plugin GUIs and nothing else: it
parents a child window into an `HWND`, an `NSView` or an X11 window
and delivers events.  It brings no widgets, no layout and no renderer,
which is exactly the shape of the hole.

**And no pixels either**, which is worth stating because it decides the
next dependency.  `WindowHandler` is `on_frame`/`resized`/`on_event`
and nothing draws; what `WindowContext` gives you is
`HasWindowHandle` + `HasDisplayHandle` (raw-window-handle 0.6) and, if
you turn on its `opengl` feature, a bare `GlContext` whose whole API is
`get_proc_address` and `swap_buffers`.  So the choice is: drive OpenGL
by hand to blit one texture, or hand the window handle to
`softbuffer`, which presents a CPU framebuffer and is on the same
raw-window-handle version.

**`softbuffer`, and the painter stays ours.**  A GL path would mean
loading function pointers and carrying a shader to draw rectangles that
a software rasterizer fills in a few lines — and it would make the
panel's output depend on a driver, which is the wrong property for a
thing that is supposed to be checkable against a committed image.  The
display list is rects and dots on a small window at frame rate; a CPU
rasterizer is the honest tool, and it is the one that keeps acceptance
test 3 meaningful.

**It is a dependency, and `shell/README.md` says the shell has none.**
That stance is load-bearing — `abi.rs` hand-declares CLAP so the shell
builds offline and owns every line it ships, and `PyO3` was declined
for the same reason.  Platform windowing is where the stance stops
paying: three window systems, each with its own event model and its
own decades of edge cases, is not a subset anyone should hand-declare
to save a dependency.

So the cost is **isolated rather than absorbed**:

* the panel is its own crate, `shell/panel/`, and it is where every
  dependency lives;
* `shell/clap` takes it **only under a `gui` feature**, so the
  engine-only build stays exactly as dependency-free and
  offline-buildable as it is today, and that is what CI keeps
  building;
* the painter and the display list are in the panel crate with no
  `baseview` in their signatures, so they are testable without a
  window and a different windowing choice later costs one module.

## Text, and the font that ships with it

Panel one has names to draw — channels, banks, values — and the
painter has no text primitive because `Sub` has none.  So text is
**host-side chrome**, drawn by the panel crate and invisible to the
display-list vocabulary the substrate shares.

The font is **a 3×5 bitmap, hand-authored, in the crate**.  Not a font
file, not a rasterizer, not a dependency: a table of glyphs for the
characters a descriptor can contain, drawn as filled cells at an
integer scale.  A channel name is an identifier and a bank name is an
identifier, so the alphabet a panel must render is small and known.
That is the same reasoning `abi.rs` uses about CLAP — declare the
subset you need and own it — applied to the one place where a general
solution would cost a font stack to draw sixteen labels.

At scale 2 a 3×5 glyph is 6×10 pixels, which is legible and is what
the panel uses; the scale is a parameter, so a host that reports a
2× display gets 4 and nothing else changes.

## Zoom, and scrolling

Two things a fixed layout cannot do, and one rule that keeps them
honest.

**Zoom is a percentage, not a multiplier.**  `SCALE_MIN` to
`SCALE_MAX` in steps of 25, because doubling is too coarse a thing to
offer as the only step — going from readable to twice-readable skips
every size a person actually wants.  The layout scales smoothly with
the percentage; the *font* still lands on whole cells, because it is a
bitmap and a fractional glyph would blur the one thing this painter
does exactly.  So text climbs in its own steps inside a continuously
growing frame.  The panel opens at 150: at 100 the small captions are
three pixels tall, which is a diagram of text rather than text.

**Every dimension comes from one number** (`Metrics`).  Making the
text bigger without making the boxes bigger is how a label ends up on
top of a number; deriving both from the zoom means the only way to get
it wrong is to write a constant that ignores it.  The one deliberate
exception is the key width above, and it is commented as one.

**The name column is measured, not declared.**  Everything in it goes
through the same `font::width` the painter uses, so it is exactly as
wide as the widest thing in it — a fixed column scaled by the font is
how a window ends up twice as wide as its content.

**Changing the zoom does not resize the window.**  How big the window
is belongs to the host and to the person dragging its corner; a panel
that grew itself every time you enlarged the text would fight both.
Content that no longer fits **scrolls**.

**Scrolling is an offset on the layout, not a second pass.**  Every
item and every hit region is placed from the same running `y`, so
subtracting the scroll once at the top moves the picture and what
listens by exactly the same amount.  A hit test that forgot the offset
would write the parameter belonging to whatever *used* to be under the
pointer — the classic scrolling-UI defect, and unreachable when there
is only one `y` to be wrong about.

The bar is drawn over the content and outside the display list,
because it is a fact about the *window* rather than about the model —
nothing in a `Sub` will ever produce one.  It is draggable and wide
enough to grab: a four-pixel bar is a decoration you have to aim at.

## What the ABI has to grow

`abi.rs` declares `clap.params`, `clap.state`, `clap.note-ports` and
`clap.audio-ports`.  Three things are missing and all three are for
this:

1. **`clap.gui`** — `is_api_supported`, `get_preferred_api`, `create`,
   `destroy`, `set_scale`, `get_size`, `can_resize`,
   `get_resize_hints`, `adjust_size`, `set_size`, `set_parent`,
   `show`, `hide`.  The window API strings (`"x11"`, `"win32"`,
   `"cocoa"`), the `clap_window` union and `clap_gui_resize_hints`.

   **The panel resizes, freely and in both directions.**  Width gives
   the faders a longer throw; height shows more of the list.  Nothing
   scales, so there is no aspect ratio to preserve and
   `get_resize_hints` says so.  `adjust_size` clamps to a floor rather
   than snapping to a grid — below it the labels and the strips start
   overlapping, and a host asking for 40×20 should be told the truth
   rather than handed a window with nothing legible in it.  Once a
   window exists it owns its size, so `get_size` reports what the host
   resized *to* rather than what the descriptor first wanted.
2. **The host's params extension** — `request_flush`, so a drag that
   happens while the plugin is not processing still reaches the host.
3. **An output event path.**  The plugin today never writes
   `out_events`.  A GUI that moves a knob must, and that is the queue
   the gestures and values go down.

The plugin also has to read *host* extensions for the first time —
`plugin_get_extension` is the only extension traffic in `lib.rs`
today, and it is the plugin's own.

## Threads, stated

CLAP is explicit about which thread may do what, and a panel is the
first part of this shell where more than one is involved.

* The window and every drawing call are **main-thread**.
* Parameter changes from the GUI are queued on the main thread and
  drained into `out_events` in `process`/`flush`, which is the audio
  thread.  The queue between them is the only shared mutable thing the
  panel adds, and it is single-producer single-consumer.
* Nothing in the panel touches the engine state, the control buffer or
  the score cursor.  It reads parameter values it already owns and
  writes events.  **A panel bug must not be able to make a sound
  wrong** — that is the property worth keeping, and keeping it costs
  nothing here because the panel has no legitimate reason to touch
  either.

## What the substrate demanded, when its turn came

*(Since written: it came.  `shell/panel/src/canvas.rs` runs a program's
own picture in the plugin window, on the second tab, and the answers
below are marked where they were settled.  What follows is the list as
it was written, because being right about which questions would matter
is the part worth keeping.)*

**The toolbar**, which none of this predicted and all of it needed: a
window with two sources needs somewhere to say which one you are
looking at.  `CONTROLS | CANVAS`, and the names are this document's own
— §"One painter, two sources" already called them that.  Naming them
after where they sit (front, behind) would have named the *window's
arrangement* rather than what is on each side, and the arrangement is
the part most likely to change.

Beside them, **the seed**: `SEED [01234] [RNG]`.  It is a plugin
parameter like any other, so the host saves it, automates it and shows
it — and pressing `RNG` is one whole gesture on it, `BEGIN`, one value,
`END`, exactly as a drag is.  It is *not* a fader, and the reason is
worth stating because the obvious design is the wrong one: every value
a drag passed through would be a different piece, and the plugin
answers a new seed by re-rooting its stream, so a one-second drag asks
for sixty re-roots of a score, fifty-nine of them thrown away.  One
press, one take.

**And the number is a field you can type in**, which is the one place
this panel takes the keyboard.  §"Threads" and the event handler both
say keys go back to the host — a DAW lets you play the piano while a
plugin window has focus, and a panel that captured them would take the
instrument's own keyboard away.  The exception lasts exactly as long as
somebody is typing into a five-character box: `Panel::is_editing` gates
it, every key the field does not want goes back to the host even while
it is open, and `Escape` closes it.

The editor is deliberately tiny — digits, backspace, enter, escape, and
a caret.  No selection, no cursor to move, no clipboard: the field holds
at most five characters, and each of those would be a thing to get right
for nobody.  Three rules earn their keep, and each is a way of not
losing somebody's work quietly: a press *elsewhere* commits rather than
discards, because typing a number and then reaching for a fader means
the number; an **empty** field commits nothing, because backspacing to
blank and pressing enter must not silently select take zero; and
pressing `RNG` closes the field, because rolling and typing are two ways
of saying the same thing and a caret left blinking over a number it no
longer describes is a lie.

Recorded here because the panel is what turns these from questions
into requirements.

* **Text.**  *(Settled, and it was the next thing built.)*  `Sub` has no
  label, and the panels have names to draw.
  The editor's withdrawal turned on the language being unable to
  measure text — but `gui.ges` states its own rule directly above the
  datatype: *"The extent is declared, never measured."*  A label with
  a **declared** box is consistent with that rule; the language
  reserves a box and the host draws glyphs into it.  The editor needed
  text *layout* — cursor positions, wrapping, hit-testing between
  characters.  A label needs a box.  That is the whole difference, and
  it is why `Label String` under `Sized w h` is admissible where an
  editor was not.  Panel one draws its text host-side and does not
  settle this; a canvas that wants a legend does.
* **`TouchX`/`TouchY` versus the spec's `onDrag`.**  *(Reconciled, in
  `spec/substrate.md`, when `Label` arrived — which is what this entry
  said would force it.)*  The built
  vocabulary attaches a `Chan Float` on one axis; `spec/substrate.md`
  §"Attachment" still describes `onDrag : Chan Point -> Sub -> Sub`.
  Panel one's knob rows are horizontal, so they are `TouchX` and the
  panels do not force the question — but the spec and the datatype
  should be reconciled before a third element arrives and picks one by
  accident.
* **A knob that is a `Sub` writes a channel; a knob in a plugin is a
  parameter.**  *(Settled, and it was the interesting one.)*  If a
  knob panel ever becomes a real substrate, the shell has to map "this
  channel is a knob" to "this is parameter *i*" and route the write
  through the host.  `Control.knob` is already that flag, which is the
  pleasant part; the unpleasant part is that a `Sub` writing a channel
  is the substrate's whole mechanism, so the mapping belongs in the
  shell rather than in the language.

  It does, and it is called the **bridge**: `export.substrate_of` pairs
  every declared channel that is *also* a control source with the slot
  the graph reads it from, and a knob's slot is its parameter id.  So a
  touch on a canvas fader produces two things — the channel write that
  moves the picture, and the `Change` that moves the sound — and they
  are one gesture, so the DAW gets one undo step.  The reverse
  direction matters as much and was nearly missed: a host moving a
  bridged parameter (a lane playing back, the DAW's own generic panel)
  writes the channel too, or the canvas is a display that is right only
  while you are the one touching it.

  **The bridge is keyed by name, not by channel id**, and that is the
  correction this cost.  An id is allocated when a declaration is first
  forced, so it is a fact about what the *host* does: forcing the
  declarations first gives `cutoff` id 0, letting the program reach it
  gives id 2, and both are correct readings of one file.  Sending ids
  meant two languages had to make the same choice about that, with
  nothing checking — and they did not.  Names cross; the shell forces
  them in the order given and keeps whatever ids it is handed.  Nothing
  has to agree because nothing is being guessed.

* **Where the origin is.**  *(Settled, painfully.)*  `gui.py`'s
  `_flatten` walks from `cx = cy = 0`: a substrate's centre sits at the
  window's **corner** and the program places itself from there —
  `substrate.ges` opens with `moveXY 120 140` for exactly that reason.
  Centring the picture in the pane looked more sensible and was wrong;
  it added half a window to an offset the program had already applied,
  and the first screenshot had the fader in the bottom-right corner.
  The rule is that the two hosts agree tree for tree, and the origin is
  part of the tree's meaning.

## Acceptance

1. A plugin with the `gui` feature off is byte-for-byte the plugin
   that ships today: same exports, same extensions, no dependencies,
   builds offline.
2. The display list a knob panel produces is a pure function of the
   descriptor, and is tested as one — no window, no baseview.
3. The painter is deterministic and clipped: the same display list
   gives the same pixels, a span running off the edge touches no other
   row, and a circle stays inside its radius.  **A committed golden
   image is not in yet** — `--example shot` is how the pixels get
   somewhere they could be compared, and the layout is currently
   checked by looking rather than by a hash.  That is the weakest
   clause on this list and the honest place to strengthen it first.
4. A drag emits exactly one `GESTURE_BEGIN`, one or more
   `PARAM_VALUE`, and one `GESTURE_END`, in that order, per gesture.
5. A key the bank's `FromMIDI` declines is visibly declined in the
   note panel, and the same key is silent when played.  The panel and
   the engine agree because they read the same table.
6. Nothing the panel does changes a rendered sample: the export parity
   suite passes with the feature on and the panel open.
