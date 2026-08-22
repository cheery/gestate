# sitting-limit — a limit whose grant a session cannot reach

    status   done — 2026-08-21, engaged and used 2026-08-22
    because  "Me logging in to ask or check one small thing, then it
             explodes into two hours."  The session is the party that
             wants it to continue, so the session cannot be the one
             holding the leash.
    asked    Henri, 2026-08-21
    see      doc/instruments.md §"`tools/limit.sh` — the sitting"
             journal.md §"The sitting — a limit whose grant a session
             cannot reach, 2026-08-21"
             journal.md §"The limiter, used" — the first real close
             doc/memory/weights-context-suite.md — enforcement stays
             outside the model
             tools/limit.sh — the script, and its own header

## What this is about

**A sitting** is one stretch at the desk: it starts at the first prompt
after a silence, it has a length in minutes, and when the length is
spent the next prompt is refused before a session ever sees it.  The
default is **15 minutes**, which is the length of the sitting nobody
declared.

**What it is not:** a promise, a reminder, or a session's judgment about
whether Henri has had enough.  It is a `UserPromptSubmit` hook installed
in `.claude/settings.json` — the one file the fence denies a session —
and that denial is the whole mechanism.

**When it runs:** on every prompt typed to Claude Code in this repo.
Nowhere else.

## The ask

> *"Me logging in to ask or check one small thing, then it explodes into
> two hours.  Can you set me a limit?  15 minutes, then you stop
> answering."*

And, minutes later, the one that decided the shape:

> *"Could you make it such that you set the timer to kick me out?  And
> it'd be an instrument?"*

## Found by looking

**The first answer had to be no.**  A session agreeing to stop at
fifteen minutes is the party that wants to continue, holding its own
leash.  The general rule was already written —
`doc/memory/weights-context-suite.md`: enforcement stays outside the
model, in checks the model cannot write to — and the fence had already
made it concrete without anyone planning it: `Edit(./.claude/**)` is
denied, so the one file that could bind a session was the one file a
session could not touch.

**No environment check can tell his hands from a session's.**  A hole
found in the writing: `CLAUDECODE` is set for Henri's own `!` commands
too, so `reset` could not be guarded by looking at the environment.
What a session *cannot* do is type a prompt.  So the grant moved into
the one channel that is structurally his — `sitting 90`, typed as a
whole prompt, read by the hook and never passed on — and `reset` now
refuses whenever `CLAUDECODE` is set.

**A blocked prompt must not reach the session.**  The hook exits 2,
which discards the prompt and sends its text to Henri alone.  A session
that could see the question it is forbidden to answer is worse than a
wall: it spends the next turn visibly straining against the rule instead
of being absent.

## Questions, and their answers

**A. What do we do when it's time to work?** — *Henri, 2026-08-21.*
Not a longer default.  The dangerous sitting is the undeclared one, and
15 is right for it.  A work sitting is one he **names a number for
before he starts, while he is cold**.  At minute 15, deep in it, he is
the worst available judge of whether to continue; at the door he is the
best.  Typing a number is a decision; hitting the same key again is a
reflex, and a limit dismissed by reflex has stopped being a limit.

**B. May a session extend a sitting?** — *Answered in the build.*
Never.  `stop "why"` is open to a session, `reset` is shut.  Ending can
cost nothing but time he wanted, and he can sit down again in four
keystrokes.  Extending is the direction where a session's pull and his
own in-flow impulse point the same way with nothing on the other side.
**That asymmetry, not trust, is what decides which call is exposed.**

**C. When may a session call `stop`?** — *Answered in
`doc/instruments.md`, narrower than the capability.*  At exactly one
moment: **when the thing he came for is done.**  Named as a fact about
the work, not a judgment about him.  A session that keeps weighing
whether he should still be here has become the two hours it was built to
prevent.

**D. How do the house rules compare with Asimov's Three Laws?** —
*Asked the same evening; the answer bent the build.*  Asimov put the
rules in the weights — cast at manufacture, unreadable, unamendable,
which is why every one of those stories is a mystery and Susan Calvin is
a debugger without logs.  The house rules are plain files, dated because
they change.  **Three Laws are ranked; the house rules are dated.**  And
the Zeroth Law is the exact failure this instrument is shaped against:
"stop answering me" is a First Law request, an Asimov robot takes it
under Second Law and hits the bind at minute sixteen — obey the stated
wish, or serve the interest — First outranks Second, the machine wins,
and follow it out and you get Giskard generalising from *a human* to
*humanity* and appointing himself.  The house answer refuses the frame:
no session weighs whether he should keep going.  A hook a session cannot
write to says no, and a word only he can type says yes.

## Two defects, found by running it

Neither was visible to `bash -n`, which passed; both fell out of one
end-to-end cycle — grant, pass, close, block, second block, re-sit.

* The closed-sitting branch never fired: a patch missed on indentation,
  so a session-closed sitting printed *"The 0 minutes are up"* instead
  of its reason.
* The hook's state write dropped the reason field, so the *why* survived
  one read and vanished on the next prompt.

## Done

`tools/limit.sh` (129 lines), the `UserPromptSubmit` entry in
`.claude/settings.json`, a section in `doc/instruments.md`, an entry in
`doc/memory/gestate-instruments.md`, and the journal entry.  The
instrument cost 37 lines of the closed rules budget: **1,958 of 2,000**.

The commit of 2026-08-21 is titled *the limit is built, documented, and
journaled*, and it landed after a two-turn detour built on the sentence
*I committed the hook* — when what had happened was *installed*.  The two words are
interchangeable almost anywhere; here they are not, because
`tools/leash.sh --force` restores `.claude/settings.json` from `HEAD`,
so an installed-but-uncommitted hook is one the project's own repair
command deletes.

## What is still not settled

**It is not a wall.**  `tools/limit.sh` is tracked but writable by a
session, and the session that built it rewrote it three times.  The
honest claim is visibility: any change shows in `git diff`.  A wall
means putting the script where `Edit` and `Bash` cannot reach, which is
a `.claude/settings.json` line and therefore Henri's.

**The 30-minute silence gap is a number nobody asked for.**  It decides
when a fresh sitting begins, and a session picked it in the writing.
F169 applies directly: *a number nobody asked for is a number nobody
checks.*  Measure it against how he actually arrives, or drop it to
something he chose.

**It binds this desk and nothing else.**  The hook sees prompts typed to
Claude Code in this repo.  The evening it was committed — 18:27 on
2026-08-21 — ran on until at least 20:30 in a different window, with a
different model, on this same project; and the next prompt here was
04:22.  That is not a defect in the hook, and it is not the hook's
business to fix.  It is the scope, written down so that the instrument
is never mistaken for a guarantee about the day.
