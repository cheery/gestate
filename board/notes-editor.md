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
3. **Both axes in one drag** — F204's first repair, in the walk.
4. **The tools he reaches for**, his list, 2026-09-06: *"I do transpose
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
2. **Where a tapped tempo lives.**  A `.notes` says bars and beats and
   nothing about how fast; the wrapper says 100.  A file-level record
   (`tempo 92`), the section record, or the including `.ges`?  Default:
   a file-level record, one line, because the file is the source and
   the wrapper is a projection.
3. **What "the clip" is in a `.notes`.**  Reaper's clip is the item on
   the track; here the nearest thing is the section's `bars`.  Resizing
   it would be a change to the section record.  *His to say.*

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
