# gemba-follow — the walk should behave like something you are inside

    status   open — not yet elaborated
    because  "when the editor is in gemba, it should update the view
             after a watched file is being edited.  And gemba should be
             possible to interrupt by any action, and when typing gemba
             again it'd resume to whatever you shown last time.  When
             gemba is online, it should show [gemba] on the screen."
    asked    Henri, 2026-08-18, after using the first walk
    see      board/done/gemba.md — the walk itself
             gestate/gemba.py, gestate/session.py `_travel`
             gestate/session.py `_outside` — the mtime instinct already built
             board/done/command-categories.md — `[command]` is the precedent
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
