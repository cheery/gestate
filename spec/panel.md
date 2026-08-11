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

This is the panel that earns its place, because it makes a *silence*
visible.  `NoteTable.ok[k * levels + l]` is already exported; nothing
else in the system can show it to a player, and the player's question
— "why did that key do nothing?" — has no other answer.  A bank with
`table: None` takes the structural `(key, velocity)` default and
accepts everything; the panel says so in words rather than drawing a
strip that is uniformly true, because a wall of one colour looks like
a bug.

**Not a routing editor.**  Nothing here rebinds a bank to a key range.
Which bank listens is the program's own `FromMIDI` instance, and the
way to change it is to change the program — the same answer
`spec/editor.md` gives for everything else, and for the same reason:
a second model would drift.

## One painter, two sources

The design decision that keeps this from becoming a system that has to
be thrown away when the canvas lands.

`gestate/gui.py`'s `_walk` already reduces a `Sub` to a **display
list** and a **hit list**, and they are very small:

    ("rect", x, y, w, h, colour)
    ("dot",  cx, cy, r, colour)

    { axis, chan, region }

That is the entire host-facing drawing vocabulary of the substrate: no
text, no paths, no gradients, no clipping, no anti-aliasing
requirement.  Ten `Sub` constructors, of which `Row`, `Column`, `Pad`
and `Sized` are layout the *language* performs — the host accumulates
a centre point and nothing else.

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

## What the ABI has to grow

`abi.rs` declares `clap.params`, `clap.state`, `clap.note-ports` and
`clap.audio-ports`.  Three things are missing and all three are for
this:

1. **`clap.gui`** — `is_api_supported`, `get_preferred_api`, `create`,
   `destroy`, `set_scale`, `get_size`, `can_resize`, `set_parent`,
   `show`, `hide`.  The window API strings (`"x11"`, `"win32"`,
   `"cocoa"`) and the `clap_window` union.
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

## What the substrate will demand, when its turn comes

Recorded here because the panel is what turns these from questions
into requirements.

* **Text.**  `Sub` has no label, and the panels have names to draw.
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
* **`TouchX`/`TouchY` versus the spec's `onDrag`.**  The built
  vocabulary attaches a `Chan Float` on one axis; `spec/substrate.md`
  §"Attachment" still describes `onDrag : Chan Point -> Sub -> Sub`.
  Panel one's knob rows are horizontal, so they are `TouchX` and the
  panels do not force the question — but the spec and the datatype
  should be reconciled before a third element arrives and picks one by
  accident.
* **A knob that is a `Sub` writes a channel; a knob in a plugin is a
  parameter.**  If a knob panel ever becomes a real substrate, the
  shell has to map "this channel is a knob" to "this is parameter *i*"
  and route the write through the host.  `Control.knob` is already
  that flag, which is the pleasant part; the unpleasant part is that a
  `Sub` writing a channel is the substrate's whole mechanism, so the
  mapping belongs in the shell rather than in the language.

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
