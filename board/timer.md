# timer — see when the day has been too long

    status   open
    because  nine days at thirty commits a day, and nothing said so
    asked    Henri, 2026-08-16
    see      spec/summary.md (the sentence that asked for it)
             GESTATE_EDITOR_TIME, GESTATE_BUILD_TIME — the precedent

## The ask

> timer: see in gestate when I've been too long on it.

## Found by looking, before it was taken

This one has a caller and it is the person reading it.  `spec/summary.md`
ends: *"the pace itself was never instrumented; every other cost in this
project has an oracle, this one did not."*  This is that oracle, and it
was asked for the same day the sentence was written.

The parts are precedented — `GESTATE_EDITOR_TIME` and
`GESTATE_BUILD_TIME` already measure and report, and the status bar
already carries multiple lines.  What is not decided is the part that
matters:

* **What counts as "too long", and what counts as a break?**  Elapsed
  since the workbench opened is easy and wrong — it counts a lunch
  break.  Keystroke-active time is closer.
* **What does it do when it fires?**
* **Does it persist across sessions?**  Nine days at thirty commits a day
  is not one long session; it is many, and a per-session timer would have
  said nothing about it.

Claude's inclination: session-elapsed plus idle detection, shown in the
status bar, persisted to a small file so the **day's** total is what it
reports.  The day is the unit that went wrong, not the sitting.

## Questions

**Answered, 2026-08-16 evening — the status line, and nothing else.**  A
quiet amber in the multiline status bar carrying the **day's** total, not
the sitting's.  Ignorable by design.  Escalation was offered and
declined, which is the right call for a program that would otherwise
interrupt its author mid-take.

Still open, and cheap to decide when the work starts: what counts as a
break (the idle threshold), and where the day's total is persisted.
