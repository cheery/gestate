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

**Left of slice 4** *(as of the seventh slice)*: resize a note or the selection, resize the
section, tap a tempo.  And what this slice does not do: a group is
spent with its commit rather than kept, as Reaper keeps it; and a
click on a group keeps the group where a click elsewhere selects one.

## A note resized by its end, and the selection with it — 2026-09-06

**Henri:** *"take the next slice, resize a note and the selection."*
A press in a note's last column takes its end, the body's hand
carries the end along by the grid, and the release runs `resize` for
one note or `stretch` for the group — every selected note's length by
the same ticks, one rewrite.  Pitch is not carried while an end is
held.  `spec/drawnscores.md` §"The eighth slice, built" is the
contract, driven first time
(`test/driven/20260906-160458-notes-resize-end-and-stretch`).

**Left of slice 4** *(as of the eighth slice)*: resize the section — the clip, Q3's answer: an
edit to the section record's `bars` — and the tapped tempo, Q2's.

## The section resized on its ruler — 2026-09-06

**Henri:** *"take the next slice, resize the section."*  The ruler is
the section's handle now: a press takes the section's end, the drag
along carries it by whole bars, and the release runs `bars`, one
field of the section record.  It grows freely and shrinks only past
empty bars.  `spec/drawnscores.md` §"The ninth slice, built" is the
contract, driven first time
(`test/driven/20260906-162036-notes-section-resized-on-ruler`).

**Left of slice 4** *(as of the ninth slice)*: the tapped tempo, Q2's answer — the `.ges`'s
`bpm` line edited the way a knob writes its number back, and a
`.notes` `bpm` record read only when no `.ges` says.  And a grown
section is wider than the window, which is the horizontal scroll the
fifth slice said no section of eight bars would ask for.

## The tapped tempo — 2026-09-06

**Henri:** *"take the next slice, the tapped tempo."*  `tap` on
`Ctrl-T`, a run of taps in time being a tempo; `tempo N` the written
half — the `.ges`'s `bpm = …` literal, or a `.notes` `bpm` record
written on line 1 when the file had none — exactly as Q2 answered
it.  `spec/drawnscores.md` §"The tempo record" is the format's word and
§"The tenth slice, built" the contract.  Driven twice: the first run
read four taps at 120 as `bpm 102`, because a tempo's audition was
holding the model's thread through the next tap; through the
coalesced audition the second read `bpm 121`
(`test/driven/20260906-163812-notes-tapped-tempo`).

**Slice 4 is built, every tool on his list:** transpose, onset and
offset, drag and select several and move them around, resize the
clip, resize the selection, tap a tempo.  What the card still says
is not this card's — the score view — and what the building left
open is the horizontal scroll a nine-bar section asks for, a group
spent with its commit where Reaper keeps it, and the lookup test's
timing bound inside a full-file run.

## The picture as a library — 2026-09-06, evening

**Henri**, asked how the GUI work had gone and told the page's text
stood at eighty thousand characters: *"Se että G-kone ne laskee olisi
hieman parempi kuin että python kirjoittaisi suuret määrät .ges
tekstiä"* — and then *"Tehdään sitten se idea 2, moduuli."*  Two
halvings the same evening, each held item-identical: the furniture
computed by the G-machine, and then the whole drawing moved into
`gestate/roll.ges`, a library in front of the page's program.  Text
85 → 32 thousand, compile 4.4 → 1.1 s.  `spec/drawnscores.md` §"The
picture computed, not written" and §"The roll's vocabulary is a
library".  And then idea 3, at his *"tehdään myös"*: the body is one pad, three
hands a box where there were a hundred and thirty, the page at eight
thousand characters, `spec/drawnscores.md` §"The body is one pad".
The evening's list is done.

## The file is a table, and the selection follows — 2026-09-08

*From `card:gui-is-difficult.md` Q7, Henri: "nuotti saisi lajittua
siihen järjestykseen mikä on tiedostolle sovittu."*  A note's identity
is its content: every gesture's write goes through `notes.canonical`,
so after a rail drag the line sorts to where the note sounds — the
first gesture here that moves text the person is not looking at, and
the status line names the line it landed on.  The selection is a set
of keys and is found again after the rebuild a commit causes, so a
note or a group is nudged twice without a second press or sweep —
the *kept, as Reaper keeps it* this card's slice 4 said it did not do.
A unison doubling (seven on `arc.notes`) is transposed through the
selection.  `spec/drawnscores.md` §"And the order is kept by every
gesture" is the rule; the tests are the four at the foot of
`test/test_drawnscores.py`.

## The bar line was a knife — 2026-09-09

**Henri**, verifying the drag on the window: *"When I shift the note
playing 4 beats, right 2 beats, it clips against the bar marker and
appears as if it was 2 beats long.  That should not happen."*  It did
not on the compiled road — `long` refuses onsets past its box and
never an end — and both readers of the parsed file, the picture's and
the performer's, cut the note at the bar line on a comment that had
misread `Clip`.  One line in each; `fixme.md` **F220**, and the
boundary the `arc.notes` parity never reached is a two-bar file
written into the test.  `spec/drawnscores.md` §"The eighth slice"
said the wrong thing and says the right one now.

## The page carries sideways — 2026-09-11

**The thing the ninth slice left**, in its own words: the section-resize
tool this card built dead-ended the moment it was used past eight bars,
because a nine-bar section is 1182 px wide in a window 1100 wide and
the page was simply cut at the view's right edge.  *It is the fourth
slice's number on the other axis and no new arithmetic* —
`view::canvas_scroll` is a clamp that does not know which way it runs,
so the sideways carry is that same function called with
`view::span_across` and the window's **width**.  `canvas_centre` is now
the one place the origin is said, so the painter, the press, the drag
and the release cannot disagree about it.  A tilt wheel or a trackpad
says it in the event's `x`; **Shift and the wheel** is the spelling for
a mouse with one wheel.  `spec/drawnscores.md` §"The page carries
sideways too" is the contract; three tests under *And the same scroll
sideways* in `shell/editor/tests/view.rs`.

Driven (`test/driven/20260911-132650-notes-section-carried-sideways`):
one section of **sixteen** bars, 2078 px against a 1100 px window, with
exactly one note past the eighth bar — nothing in the run could reach
that note unless the page carried.  It opened with its keyboard at
x 1, forty tilts right took the keyboard off the left edge, forty more
changed not one pixel of the roll, a press took the bar-14 note and
carried it three semitones — `key 64` to `key 67`, one line of the file
and nothing else — and Shift with the wheel brought it back to x 1.

**What the driving taught, which the tests could not:** the first two
oracles were blind and both answered confidently.  Asking whether the
page's *ground* had moved reads `(0, …, 1098, …)` at every scroll,
because the ground is wider than the window — *it did not move*, said
of a page that had.  Asking whether the whole window differed read the
status bar's clock as the page running past its last bar.  What answers
honestly is the roll's band differenced and the keyboard down the
page's left edge.  The shape is `doc/memory/dont-conclude-from-a-shallow-check.md`'s,
one floor down: an oracle that cannot see the thing gives a reading
about itself.

**Found on the way:** `fixme.md` **F221** — a section's caption is
anchored to the body's centre, so on a page wider than the window it is
off the right edge at bar 1 and at the left after the carry, beside
bars it is not about.  Left as an entry rather than repaired, because
*pinned to the window* and *drawn at the section's start* are different
pictures and the spec says nothing.

**Left of this card**, as of today: the postcondition is not met — the
score's 0.4–0.6 s and the picture's 0.4 s are bookkeeping, not a
compile (§"Slice 3, landed") — and the four open defects under the page
are F205, F206, F208 and F212.  The card's own §"What this is" names
two things still unbuilt: **the bars tool's degrees beside the notes**,
which `notes.spell` and `notes.degree_of` already compute, and no
playhead crosses the page while it sounds.  Q1's default still stands.

## The note sounds under the hand — 2026-09-11

**Henri:** *"I think I still do not hear the note preview when I press
and modify a single note.  That, and the playhead across the page would
be neat."*  He was right and the tree said why: a gesture sounded only
when it **let go** — the piece from the note with the transport
stopped, an audition in place with it running — so taking a note and
carrying it through six semitones was silent, where Reaper plays the
note under the finger.

**And the seam `spec/annotations.md` said did not exist, did.**  That
page priced three paths on 2026-09-04 and put this one out of reach:
the keyboard road builds a payload from channel, pitch and velocity, so
*"there is no manner in it and there cannot be"*, and the right road
needed *a way to sound one payload, with its fields, through its bank*
— called a card of its own.  Two claims in one sentence, and only the
second half was true.  The allocator has always taken a payload tuple;
what stood in front of it was `feed`, which builds one from a MIDI
message.  `audiomidi.Notes.sound(bank, note, payload)` is the door, and
it is a method, not a card.  The expensive half — rendering a note
offline, in isolation, both ways — is still unbuilt and still wanted.

So the preview **carries the manner**: `session._sounds_as` reads the
note's own record and hands over `(key, level_of(vel),
bits_of(manner))`, which is the payload `NotesKind.events` schedules.
What you hear is the note the piece would play, in the voice it would
play it in.  A press sounds it, a drag re-sounds it at each new
semitone and at no other tick, the release stops it.
`spec/annotations.md` §"The seam existed after all" is the contract.

**Two things a recording bench could never have found**, and a real
allocator found both in one test:

* **Every voice of a `.notes` file is a bank the score writes, and a
  scored bank starts with its listening switch off** — so a preview
  routed the way a keyboard is routed would have been silent on exactly
  the notes being edited.  The switch guards the *routed* door against
  a keyboard that might be played at any moment; this door is named,
  and the question it actually has to answer is the **transport**,
  which is where the guard went.
* **A `.notes` voice takes a three-value payload**, so the two a MIDI
  message can build are refused by the allocator's own arithmetic —
  `spec/annotations.md`'s objection to path 1 arriving as an exception
  rather than as a wrong sound.

**F221 closed with it**, as he decided: a section's caption is drawn at
the section's own start now, so it scrolls away with the bars it names.

### What the window said, within the hour — 2026-09-11

**Henri, running `untitled.notes`:** *"One issue is that when I press
Ctrl+space, the currently playing note ends up sounding to the
background… Another issue is that I do still do not hear the note play
review.  I try to play it from 'playing' and 'sounding' -states… and
if I try it from 'stopped' -state, it ends up gunking the 'play' and
I'm no longer able to play the note."*

**Three reports, one cause under two of them.**  The guard read
`Workbench.playing`, which is not *the clock is moving* but
`self._audio.is_alive()` — **the engine being up**.  So it was exactly
inverted: it refused in *sounding* and *playing*, the two states that
can sound, and allowed *silent*, the one that cannot — where a gate
written into `Notes.values` is read as an **initial value** when the
engine comes up, which is the note stuck on that gunked his play.  The
reader is `_state_of` now, and both up states preview; the allocator
refuses a preview on a full bank rather than stealing a scored note,
so *playing* costs the piece nothing.

The third is its own: a preview is held for as long as the hand is and
`play` does not pass through the hand, so **every transport verb hushes
first**.

**And the tree had already written the warning.**  `session._state_of`:
*"Not `Workbench.playing`, which asks whether the audio thread is alive
— a different question wearing the same word."*  Written for this trap,
and it did not stop it, because the new code never called that
function.  A warning is worth what the path through it is worth.

*Four tests under the preview in `test/test_drawnscores.py`, two of
them states a headless bench had to be told to be in — which is the
other half of the lesson: a stub answers whatever it was built to
answer, and it was built by the same reading that was wrong.*

### And the repair was correct in the states he was not in — 2026-09-11

**Henri, an hour later:** *"I restarted the editor, and it still shows
the old behavior."*  It did not: the library was not stale
(`editor._stale` said so), the launcher runs from the tree, and there
is no installed copy shadowing it.  Measured on a real `Workbench` over
a two-note `.notes` with no sound card, the press sounded in *sounding*
and in *playing* exactly as built — and **a freshly opened editor is
*silent***, which was the one state the repair refused in.

**A right mechanism scoped to the wrong occasion**, which is a worse
failure than the wrong mechanism it replaced: it passes every test,
reads correctly, and is invisible to the person it was built for.  The
first version misread a word; this one never asked *which state is a
person in when they do this*.

And the design carried its own tell: `_hear_from` has started the piece
from a **dropped** note since 2026-09-06, so in silence the release
already took the sound card and only the press refused to.  Two
decisions five days apart, and no reader ever saw both.

**His call, given three readings: bring the engine up and sound it** —
which is `audition`'s own move from silence, `spec/transport.md`
sentence 4.  A bench that will not come up is still left alone and not
written into, so the *gunking* guard stands.

### The author named the mechanism — 2026-09-11, F222

**Henri, after two repairs that had not worked:** *"You recall that the
voice banks are layered?  That is, the MIDI-note fed into the bank does
not play along the main note.  However.  The mechanism is blocked
because the voice bank doesn't have FromMIDI -class.  That might be
tripping and causing the behavior I note."*

It was.  `Workbench.control` is the one function the render loop reads,
and a channel reaches `Notes.values` only through `_midi_channels`,
which is filled through `listen`, gated on `takes_midi`, gated on a
`FromMIDI` instance — which a `.notes` wrapper's voices cannot have,
their payload being `(key, level, manners)`.  So the preview was taken
by the allocator and answered from the score, every block.  `fixme.md`
**F222**; the repair is `Notes.previewing`, the voice's own channels
read ahead of the schedule.

**And the reason it shipped twice is one lesson, not three.**  Every
oracle used today asked something *upstream of what decides*: the
session called `sound`, `sound` returned `True`, `sounding_on` listed
the key — all true, none of them about sound.  The question that finds
it is **what reads this, and did that change**.  Three of the day's four
blind oracles cost minutes; this one shipped, because its upstream
answer was genuinely true.

It took the author to find it, and not by reporting a symptom a fourth
time — by naming a mechanism.  `doc/memory/test-what-a-person-would-do.md`
is the rule and this is its sharpest case in the tree: the suite was
green through all three versions.

### The preview is a layer the state grants — 2026-09-11, his design

**Henri, after the preview became audible:** *"I think it's really
close to the desired behavior.  Now I can hear the previewed note.  But
when I preview, it attempts to play ahead, and when I leave sounding
on, the notes end up being held rather than silenced.  I think
'preview' could be it's own input layer that goes on when sounding
-state is on, solving these issues."*

**Taken as stated, and it is now sentence 9 of `spec/transport.md`.**
`transport.ges`' `Do` gains `Preview Bool`; `enter (Up Sounding) =
[AllOff, Preview True]` and `Preview False` on entering either other
state.  `audiomidi.Notes.preview` executes it, and **closing the layer
releases whatever it was holding**.  `session._sound` asks whether the
layer is open and never decides; from a shut one it spends an
`audition`, a press on a note being a request to hear.

**Why this is the repair and the last two were not.**  A preview is a
note the *editor* holds, so it looked like the editor's business — and
it was made the editor's business twice, and each time one path was
fixed and another left open.  Put on the **state**, the property is
over states rather than over paths: there is no way into *sounding*
that forgets to open it and no way out that forgets to close it.  The
editor only ever sees the path it is on; the chart sees all of them.
*Two tests in `test/test_transport_model.py` enumerate it, which for
three states and four verbs is the bounded check the spec says it is.*

Measured on a real engine:

| | state | layer | held | channels |
|---|---|---|---|---|
| opened | playing | shut | — | 0 |
| play toggle | sounding | **open** | — | 0 |
| a hand presses | sounding | open | `melody 70` | 5 |
| **Ctrl+Space** | playing | **shut** | **—** | **0** |
| stop | silent | shut | — | 0 |

*Playing* closes the layer rather than sharing it: the score has those
voices, the allocator and the schedule assign them independently, and a
moved note is already heard in place by the audition.

**And the play-ahead went with the design.**  His *"it attempts to play
ahead"* was never reproducible headlessly — two probes over both paths
showed nothing calling `start` or `seek`.  **Closed by him the same
evening**, on the window: *"I think 'it attempts to play ahead' no
longer applies.  The fix changed the design such that it no longer is
expected."*  Which is the honest shape of it: a symptom of the editor
deciding when a preview may sound, gone because the state decides now
and there is no longer a path on which the question arises.

### And a held clock is not a silent score — 2026-09-11

**Henri:** *"When I enter the 'sounding' -state.  Whatever was playing
that moment keeps playing (they should turn off because A: the preview
gets the voice bank, B: I do not want them to sound in sounding -state,
sounding -state is meant to be a state where the audio is up, but not
playing the score)."*

`Workbench.control` resolved a scored channel with
`schedule.value_at(chan, _t)`, and in *sounding* `_t` does not move —
so whatever gate was open when the clock stopped stayed open for ever.
`enter (Up Sounding)` has said `AllOff` since the chart was written and
`_after_seek` had been releasing those notes into `Notes.values` the
whole time, **where nothing read them**: the schedule branch won first.
The same shape as F222 one floor up, found the same way — by asking
what the *consumer* reads rather than what the producer wrote.

Now `spec/transport.md` sentences 3 and 10 say it: in *sounding* the
engine reads its own values and not the score's.  Measured — in
*playing* the score's gate reads `1`; entering *sounding*, `0`.

**And it subsumed F222's repair**, which is worth saying out loud: the
per-channel precedence added an hour earlier existed only to out-argue
a schedule that is no longer in the argument.  The branch is gone
rather than kept in case; the finding and its gate stand, because what
they hold is *what the engine reads*.

### The playhead, built — 2026-09-11

*"I also think I didn't see the playback head moving in the score."*
Built, and **it needed nothing new on the wire** — which is the part
worth keeping, because this card had priced it as the opposite: *the
first thing here that needs a number crossing the wire every frame
rather than one per rebuild*.  `audioeditor.observe` has been doing
exactly that since long before this card, once a frame, by name, into
every canvas; `peak` and the spectrum bands ride it.  The playhead
rides with them.

**A price stated in a card is a claim like any other**, and this one had
stood unexamined since 2026-09-06 — the same lesson the gallery's close
harvested a question about, an hour earlier, from the other end of the
board.

What was actually hard is tick space: a page's rolls each begin at zero
and the transport counts from the start of the piece, so each box
carries where its section starts and draws at `tick - offset`, or
nothing.  The compact box beside a `.ges` line has no playhead — his
call — and the program keeps one shape by lifting that box over a
channel nobody writes.  `spec/drawnscores.md` §"The playhead" is the
contract.

**Every ask he has made on this card is now built.**  What remains open
is what the card always said was not its own: the score view, *"a bit
of a pie in the sky right now"*, his to open; Q1's default standing;
and the four defects under the page, F205, F206, F208 and F212.
Nothing draws a transport position today, and it is the first thing
here that needs a number crossing the wire every frame rather than one
per rebuild.
