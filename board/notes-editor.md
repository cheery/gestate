# notes-editor — a note moves, and you hear it before the hand has left the mouse

    status   doing — 2026-09-06
    because  "Reaper note movement reacts immediately and I can hear the
             change immediately.  Also there's richer set of tools.  The
             reaper midi interface is not perfect either, but it's what
             I've been using with little friction.  I'd like an interface
             **better** than reaper's midi interface." — Henri, 2026-09-06,
             showing ~/misc/reaper-midi.png, ~/misc/gestate-notes.png and
             ~/misc/reaper-score.png side by side.  Measured the same
             hour: a moved note takes 5 s to redraw and 5 s to hear here,
             and the next block in Reaper.
    asked    Henri, 2026-09-06 — "1. yes" to the data path first
    see      card:drawn-scores.md — rung 5, the roll this card starts from;
             its ladder is built and this is one league up
             spec/drawnscores.md — the format and the view as they stand
             vision.md §"Ease of use and efficiency" — *a piece written in
             gestate is played by instruments written in gestate, and both
             can be edited while they sound*
             fixme.md F204 — one press writes one attachment; both axes
             in one drag waits on its repair
             doc/memory/henri-prior-tools.md — oscillseq: everything has a
             command under it

## What this is, what it is not, and when it runs

**The `.notes` editor, fully featured** — his phrase from 2026-09-05 —
and the league it has to be in is named by a program he uses with
little friction.  It runs in the window, on a `.notes` opened alone or
included; the roll, the page and the drag are `card:drawn-scores.md`'s
and stay.  **It is not Reaper rebuilt**: `vision.md` refuses borrowing
another system's vocabulary to get power cheaply, and *better* means
what Reaper cannot do — instruments edited while they sound, a section
grid the file declares, marks that name an intention, a file a session
can edit as text, the bars tool's degrees beside the notes.  It is not
the score view: *"I'd like something unique there that doesn't exist
yet … it's kind of a pie in the sky right now"* — his to discuss, later.

## The postcondition

Move a note and hear it before the hand has left the mouse, with the
picture following the hand — on the piece he writes, not a toy.

## Why it is a league, not a polish — measured 2026-09-06

| step | Reaper | gestate, `arc.notes` |
|---|---|---|
| read the file | data | 10 ms |
| redraw the roll after a move | next frame | 5.0 s one section, 6.2 s the page |
| hear the move | next audio block | 5.3 s, the whole build |
| move in both axes | one drag | two gestures — column, then rail |

**The cause is structural.**  The format made the notes data on disk,
and the expansion hands them back to the compiler as source: a moved
note is a changed program, recompiled through LLVM, and the roll is
drawn by running the score through the same compiler.  Reaper moves a
record and the player reads it on the next block.

## The slices, in order

1. **The roll drawn from the parsed file.**  A note is a line, so the
   picture is a table lookup — milliseconds, not a compile.  The
   compiled road stays for a `.ges` roll, where a note may be anything.
   **Held to the compiled road by a test**: the same `Roll`, event for
   event, on `arc.notes`.
2. **The score swapped under the running instrument.**  The instrument
   does not change when a note moves, so the synth compile is paid
   once; a `.notes` edit reaches the performer as a new event list.
   The dynamic performer streams events already, and the keyboard
   plays live through the running instrument already.  *What could
   kill it:* the two-machine parity rule, if a swapped score must stay
   sample-identical with the compiled road under every edit — Q1.
3. **Both axes in one drag** — F204's first repair, in the walk.  ***Built 2026-09-06, the second sitting*** — §"One hand, both axes".
4. **The tools he reaches for**, his list, 2026-09-06 — *multi-select and move as a group built the same day, §"Select several, carry them as one"*: *"I do transpose
   them, adjust onset/offset, drag and select multiple and move them
   around, resize the clip, resize selection, select bpm by tapping."*
   Transpose is built; onset is the rail; offset is a length drag;
   multi-select, move as a group, resize a selection, and the clip are
   commands over the `selected` noun; tapping a tempo needs a place to
   write one — Q2 and Q3.
5. **The score view** — not this card; his to open.

## Questions

1. **Parity.**  `spec/verification.md` holds the compiled and the
   dynamic road to each other.  Does a score swapped live have to be
   sample-identical with a fresh build of the same file, or is *the
   same events at the same ticks* the property?  *Session's
   recommendation, suspected: the events, checked by the same
   `_events` comparison `test_drawnscores.py` already makes; the
   samples are the instrument's and it did not change.*  Default: the
   events.
2. **Where a tapped tempo lives.**  **Answered, Henri, 2026-09-06:**
   *"tempo could still live in .ges, but allow tapping it.  bit like
   how mkKnob creates sliders that can be edited.  .notes could also
   have bpm marking, but it's not used if .ges has one."*  So: the
   `.ges`'s `bpm` is the tempo when it has one, and tapping edits that
   line the way a knob's drag writes its number back; a `.notes` may
   carry a `bpm` record, read only when no `.ges` says.
3. **What "the clip" is in a `.notes`.**  **Answered, Henri,
   2026-09-06:** *"yes, section resize is sufficient."*  Resizing the
   clip is an edit to the section record's `bars`.

*Q1 was not answered and its default stands: the events.*

## Slice 1, landed — 2026-09-06

**The roll is read off the file.**  `scorebox.notes_rolls` answers the
page's asks from the parsed records — bar, tick, length, key, level,
manners — with the same `Roll` the compiled road makes, leaf for leaf,
so every gesture reads it unchanged; `NotesKind.rolls` is the
registration and the bench takes it.  Held to the compiled road on
onset, offset, leaf and key, and to the *file* on loudness and manner,
because the compiled road gets those wrong for a note-file note:
`fixme.md` **F206**, found by the parity test — every note read as a
bare key, velocity 64 and no manner, so the accent's mark never drew
over a `.notes` note, on the including piece either.

| | before | after |
|---|---|---|
| the rolls of the page, three sections | 6.2 s | **93 ms** |
| the page shown, rolls and picture | ≈ 10 s | 3.0 s |

**What the 3 s still is:** the picture.  The roll's program is
generated text compiled by the G-machine on every rebuild, and that
compile is now the whole cost of a redraw.  A picture that takes its
notes as *data* — one compiled program, the note list arriving the way
readings do — is the next slice on the picture side; slice 2, the
score swapped under the instrument, is the sound side.  Both are the
same idea: compile once, then move records.

## Slice 2, landed — 2026-09-06

**The engine compiles the wrapper's synth half and the notes reach the
performer as records.**  `notes.wrapper(notes=False)` is the engine's
text — the same voices and channels, no `include`, a score that rests
on every bank — and a note edit leaves it byte-identical, so the bench
keeps the engine playing (*kept engine — nothing it reads moved*) and
only the records under it change.  `NotesKind.events` bakes the piece
off the parsed file in the shape `perform_voices` answers, held to it
on `arc.notes` event for event and schedule for schedule.  And the
score is loaded before the picture, so the sound no longer waits for a
compile it did not need.

| one moved note, `arc.notes`, the instrument running | before | after |
|---|---|---|
| the new score installed — the note audible on the next block | 6.3 s | **0.6 s** |
| the audition reported done, picture and all | 6.3 s | 3.6 s |
| the front end, whole build | 3.95 s ×2 | 2.0 s ×1, the picture's |

**What the 3 s still is:** the picture, and only the picture — its
generated program's front end (2.0 s) and compile (0.9–1.3 s).  Slice 3
on the picture side is the same idea as this one: the roll compiled
once, the notes arriving as readings.  Found on the way: **F207**, a
program that declares banks and assigns none fails a kind check at a
prelude line.

## Slice 3, landed — 2026-09-06

**The roll is compiled once and the notes arrive as a reading.**  A
live roll's program names no note: the rows cross on a `Chan (List
Float)` the way a scope's trace does — seven numbers a note, written
to the reference views at the build and sent to the window as a
`trace` whenever they change — so a moved note recompiles nothing and
the front end's cache answers the unchanged text.  Two things had to
hold still for that: the columns tile the roll whether or not a note
is under them (an empty one refuses by name), and the scale is the
file's, one pitch axis for every section, so the text changes only
when a note leaves the range.  Held to the baked road rectangle for
rectangle.

| one moved note, `arc.notes`, the instrument running | this morning | after slice 2 | now |
|---|---|---|---|
| the new score installed — the note audible on the next block | 6.3 s | 0.6 s | **0.6 s** |
| the audition reported done, picture and all | 6.3 s | 3.6 s | **1.1 s** |
| the page rebuilt after a move, headless | ≈ 6 s | 3.0 s | **0.7 s** |

**What is left of the second**, said for the next sitting: the score's
0.4–0.6 s is `schedule_voices` over 291 notes plus the bank lookup,
and the picture's 0.4 s is the views re-serialised and the rows
written into three reference machines in Python.  Neither is a
compile any more.  Before the hand has left the mouse is the
postcondition and it is not met yet; what stands between is now
bookkeeping, not architecture.

## The editing scale, landed — 2026-09-06, the second sitting

**Henri:** *"I'd like us to continue the drawn-scores.. make it more
like what it's supposed to be."*  Read against the three screenshots
this card was written from: the roll was still the score box's glance,
384 by 116 in the middle of the window, a note three pixels tall.

**A `.notes` page is drawn at an editing scale now** — eight pixels a
semitone, thirty-two a beat, a keyboard down the side with the octaves
named, the bars numbered along the ruler, beat and bar lines, the
black-key rows striped, each section captioned with its name and mode.
The `.ges` box beside a line is unchanged to the pixel.  One
arithmetic still, at two scales, so every gesture reads the new picture
unchanged.  `spec/drawnscores.md` §"The fifth slice, built" is the
contract and the numbers; driven and photographed
(`test/driven/20260906-141355-notes-page-editing-scale`): a whole-bar
note taken by the hand, carried three semitones with the picture
following, dropped, and the file changed by one line.

**Where this sits in the slices above:** between 3 and 4 — it is not a
tool, it is the surface the tools need; a hand cannot take a
three-pixel note and a person cannot tell which one it took.  Slice 4's
list stands, and F204 — both axes in one drag — is the decision put to
him with a default at the sitting's start: repair the walk so a pad is
what `spec/substrate.md` says, and the rail retires to being the ruler.

## One hand, both axes — 2026-09-06, the second sitting

**Henri:** *"go with the default, repair the walk."*  Slice 3, built:
a press grabs the deepest attachment and every one around it, in both
machines, so a pad is what the substrate spec said and a note's column
sits inside a body that is the hand for time.  One drag carries a note
in pitch and in time; the rail is a ruler now.  `spec/drawnscores.md`
§"The sixth slice, built" is the contract; F204 is resolved with its
gates named.  Driven and photographed
(`test/driven/20260906-145334-notes-both-axes-one-drag`): one line of
the copy changed in both fields.

**What the window taught that the bench could not:** the first driven
run moved the key and not the tick, because a replacement through
`ged_set_text` lands on the window's next frame and the second command
read the text from before the first.  The view answers its own
replacement until the document takes it now.  Slice 4's list is what
is left: multi-select, move as a group, resize, the clip, the tapped
tempo.

## Select several, carry them as one — 2026-09-06

**Henri:** *"take the next slice, multi-select and move as a group."*
A press on empty roll sweeps a band, and its release runs `select`; a
hand on any note of the group carries them all, and its release runs
`carry` — one rewrite of every selected line, one undo entry, one
rebuild.  Nothing new crosses the wire: the picture reads the group
and the band as list readings, the way it reads a live roll's rows.
`spec/drawnscores.md` §"The seventh slice, built" is the contract,
driven and photographed first time
(`test/driven/20260906-154518-notes-band-select-and-carry`): six lines
of the copy, each two semitones up.
What made it possible was a rule the roll had been missing: a press
farther than three semitones from any note is empty roll, where
before it took the nearest note at any distance.

**Left of slice 4:** resize a note or the selection, resize the
section, tap a tempo.  And what this slice does not do: a group is
spent with its commit rather than kept, as Reaper keeps it; and a
click on a group keeps the group where a click elsewhere selects one.
