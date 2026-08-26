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

**It is not a wall, and the reason that is acceptable is not technical.**
`tools/limit.sh` is tracked but writable by a session, and the session
that built it rewrote it three times.  The honest claim is visibility:
any change shows in `git diff`.  A wall means putting the script where
`Edit` and `Bash` cannot reach, which is a `.claude/settings.json` line
and therefore Henri's.

*Henri, 2026-08-22, after the increments were named:* **"sitting is a
safety belt, and it won't work if I do not respect it."**

That is the missing half of the paragraph above, and it is the better
half.  A belt is not a wall either — it is trivially defeated by the
person it protects, and it has never been thought defective for that.
What makes it work is that it is **worn**, and what makes it wearable is
that it is easy, visible and honest about what it does not do.  So the
design target for anything in this family is not *unbreakable*; it is
*worth keeping on*.  A limiter a person has to fight is one they
eventually remove, and the removal will be silent.  This one asks four
keystrokes and shows every grant in a log.

**The 30-minute silence gap is a number nobody asked for — now being
measured.**  It decides when a fresh sitting begins, and a session picked
it in the writing.  F169 applies directly: *a number nobody asked for is
a number nobody checks.*

*Henri, 2026-08-22:* **"let's measure the gap number over the next few
days."**  So the hook now logs one line per arrival to
`~/.local/state/gestate/sittings.log` — timestamps and event names, never
prompt text, outside the repo — and `tools/gapcheck.py` reads it.  The
log started empty on 2026-08-22; **there is no history to look at, so the
earliest this says anything is around 2026-08-25.**

The answer is not in the gaps.  It is in the last table `gapcheck.py`
prints: how many sittings each candidate threshold makes of the same
days.  If the rows agree, 30 stays because nothing turns on it.  If they
disagree, **the row that matches how the days actually felt is the
answer, and only Henri can supply that half.**  He also expects the log
to show strain; it will not, on its own — a two-minute gap is a person
mid-thought or a person who cannot leave.

### 2026-08-25 — read for the first time, and answered

**249 arrivals over 3.0 days** (2026-08-22 04:57 → 2026-08-25 05:55),
median gap 4m, 13 of 248 at or over 30m.  **The rows disagree**, so the
number does turn on something:

| gap | sittings | median length | longest |
|---|---|---|---|
| 10m | 34 | 16m | 1h34m |
| 15m | 23 | 26m | 2h22m |
| 20m | 17 | 33m | 3h50m |
| 30m | 14 | 50m | 3h50m |
| 45m | 14 | 50m | 3h50m |
| 60m | 13 | 47m | 3h50m |
| 90m | 11 | 50m | 6h44m |

**Henri supplied the half only he could**, the same morning:

> *"That 14 sittings is about 5 in a day."*

Which is the 30m row — five sittings a day of median 50 minutes, against
eleven a day at 10m and under four at 90m.  **30 stays**, and it stays
*measured* rather than picked in the writing, which is what F169 asked
of it.  **And said outright, 2026-08-26**, when the row was put to him
as a decision still standing: *"the 30m row."*  The reading below was
a session's and is now his.  Nothing turns on 30 against 45: the two rows are identical, so
the number is insensitive exactly where a person would have argued about
it.

*A session's reading, marked as one: his sentence is arithmetic on the
table rather than an explicit verdict, and it is taken here as the
felt-day answer because it picks that row out of seven.  If it was not,
this section is what gets corrected.*

**And the strain half came back the way the card predicted — not from
the log.**  He said the same morning that the standing desk has made the
difference and he no longer feels strained.  That is the person
reporting, which is the only channel this instrument was ever going to
have; the log cannot see it, and this card said so before the log
existed.

**The increments are decisions, and they are made at the wrong end of
the sitting.**  On the morning after it was built — 2026-08-22 — Henri
worked through three short grants in a row rather than one long
one — *"extending session time a bit, and by small increments at time"*
— and agreed when it was named: **"Agreed on the micro-decisions on
`sitting`."**

It is not the reflex case the design is shaped against.  Each increment
is a number typed by hand, which is the friction the grant channel
exists to impose, and it survives intact.  What it is not is the
decision the design *trusts*: §"The length is declared at the door" rests
on him being cold when he names the number, and at minute 10 of minute
10 he is not.  A short grant renewed five times and a fifty-minute grant
are the same fifty minutes, arrived at by the judgment the instrument
says is the worse one.

**Nothing should be built to stop it, and this is the paragraph that
says why.**  A cap on grants per sitting would be the machine deciding
he has had enough, which §"Questions, C" rules out for a session and
which is no better wired into a script.  The honest handling is that the
pattern is now **visible**: every grant is a `grant` line in the arrival
log with the gap that preceded it, so `tools/gapcheck.py` can show a run
of short grants as what it is.  A person who can see his own pattern is
the only party entitled to change it.

**It binds this desk and nothing else.**  The hook sees prompts typed to
Claude Code in this repo.  The evening it was committed — 18:27 on
2026-08-21 — ran on until at least 20:30 in a different window, with a
different model, on this same project; and the next prompt here was
04:22.  That is not a defect in the hook, and it is not the hook's
business to fix.  It is the scope, written down so that the instrument
is never mistaken for a guarantee about the day.
