# gemba-follow — the walk should behave like something you are inside

    status   done — 2026-08-18
    because  "when the editor is in gemba, it should update the view
             after a watched file is being edited.  And gemba should be
             possible to interrupt by any action, and when typing gemba
             again it'd resume to whatever you shown last time.  When
             gemba is online, it should show [gemba] on the screen."
    asked    Henri, 2026-08-18, after using the first walk
    see      card:gemba.md — the walk itself
             gestate/gemba.py, gestate/session.py `_travel`
             gestate/session.py `_outside` — the mtime instinct already built
             card:command-categories.md — `[command]` is the precedent
               for a word in the corner

## The ask

Four things, in his words:

> I think that when the editor is in gemba, it should update the view
> after a watched file is being edited.  And gemba should be possible to
> interrupt by any action, and when typing gemba again it'd resume to
> whatever you shown last time.  When gemba is online, it should show
> `[gemba]` on the screen.

## What each one is, before it is taken

1. **The view follows the file.**  A session that is *working* on the
   file you are being shown will change it under you, and a walk that
   showed the version from when it arrived is showing a report again.
   `Session._outside` already keys a directory question on its mtime at
   `OUTSIDE_EVERY`, which is the instinct; what is missing is a reload
   of the file being watched.

2. **Any action interrupts.**  Being led somewhere is only tolerable if
   stepping off is free — and *free* means not having to know a command
   for it.  A keystroke, a click, a scroll: whatever you do next, the
   walk stops following.

3. **And `gemba` again resumes where it left off.**  Which is what makes
   interrupting cheap rather than a decision: you can look at something,
   and come back to the walk at the item you were on, not at the end of
   a queue that ran while you were reading.

4. **`[gemba]` on the screen while it is on.**  `[command]` in the
   corner is the precedent, brackets and all — this window's way of
   saying *chrome, not content*.  A mode you cannot see is a mode you
   will be surprised by, which is the whole of `fixme.md` F150 one floor
   over.

**Not started.**  Henri: *"Implement once done with our pop issue"*, so
this waits on `fixme.md` F147.

## Done

*2026-08-18.  `journal.md` §"Four things the first walk asked for" tells
the story.*

All four, and each verified on a driven window rather than argued for.

1. **The view follows the file.**  `_refollow` re-reads the watched file
   when its mtime moves — only while following, only when the buffer is
   saved, one `stat` a pass.  The status line says *"changed under the
   walk"*, because a file rewriting itself under you with no explanation
   is a haunting.
2. **Any action interrupts** — and the interesting half is that *most
   actions never reach the model at all*.  `act` hears edits, commands
   and played notes, and hears nothing about an arrow key: a caret move
   is the window's own state.  So the model **looks** instead of waiting
   to be told (`_stepped_off`, one atomic read of `caret()` a pass), and
   the walk stops the moment you are somewhere other than where it put
   you.
3. **`gemba` again resumes.**  The queue stands still while nothing is
   showing it, and coming back gives the item you left its dwell over
   again — without that, stepping away for a minute and returning
   replaces what you left in the same breath.
4. **`[gemba]` in the corner**, in the brackets this window already uses
   for chrome, beside `[inert]`.  True from the moment you subscribe,
   because *a session may move this window* is true then, and the box
   only exists once something has been said.

### Three things the driven window found that the tests could not

**Using the list is not an action.**  Picking `gemba` sends `filter`
while you type it, `command gemba` when you take it and `shut` when the
list closes — so treating the list as an interruption ended the walk in
the same breath it began, and `[gemba]` never appeared at all.  The rule
that came out of it is better than *any gesture*: an interrupt is
something you do to the **document or the instrument**, and the list is
how you reach the walk.

**The ask-line and the command were the same switch**, so the line
re-subscribed on every pass of the loop and no keystroke could stop it.
Separated, each says what it is for: the line means *show me, here*,
following means *take me to it*.

**And following the file ended the walk that was following it.**  A
reload moves the caret to the top, and `_stepped_off` reads a moved
caret as *you* moving — so the shot meant to show the reload showed the
file unreloaded, because the step-off had already fired.  The reload
puts the caret back where the walk had it.

*None of the three was visible from the source, and all three passed a
green suite.*  `spec/verification.md` §"The defect is in the seam, and
the test is in the module" is the rule they belong to.

## And then it cut off — 2026-08-18, an hour later

*Henri, watching one walk for two minutes: "the gemba walk cuts off.
I'd like you to check it on real editor.  Insert command `[gemba]`, wait
for 2 minutes and watch where it is."*

It did.  The first stop arrived and nothing after it.  **Three causes,
stacked**, and the first two were found by reading and the third only by
asking the running window.

1. **The step-off did not check which file you were in.**  A walk that
   moves to another file leaves the caret at line 1 of the new one while
   the walk still names the old place — so the next pass read a
   mismatch and called it you moving.
2. **The walk's own step looked like typing.**  Loading a document makes
   the window report an `edited`, which was in the interrupt set, so
   every move interrupted the walk that made it.
3. **And the caret had not arrived yet.**  An order is obeyed on the
   window's *next* frame, so the check read the caret before the walk's
   own `goto` had landed.  `GESTATE_WALK_WHY=1` said it in one line —
   `[walk] ended by the caret: 2 != 132` — after three careful readings
   of the source had found the first two and missed this.

Arrival is witnessed before departure can mean anything now.  The
two-minute walk holds: stop after stop, `[gemba]` lit, box under the
line.

**The lesson is the one this file already carries, sharpened**: the
model and the window do not share a clock.  Everything the model *asks*
for lands a frame later, and any check that compares what it asked for
against what it sees will be wrong exactly once per request — which is
often enough to break a feature and rare enough to survive a suite.
