# unseen-flare — the sound stuttered and I could not find out whether the program noticed

    status   open
    because  The audio is crackling without running audition now.  But I
             haven't seen the mechanism flare that is supposed to catch
             that.  It's likely in hardware like we predicted.
    asked    Henri, 2026-08-17 (Claude wrote the card at his ask)
    see      gestate/host.c — `snd_pcm_recover`, where the count is made
             gestate/audiohost.py — `Host.dry`, `Host.worst_us`
             gestate/audioeditor.py — `_say_dry`, `DRY_EVERY`
             tools/stutter.py — the only thing that reads the counters
             journal.md §"And what a session costs the machine"
             card:timer.md — the same shape, one row down

## The ask

> The audio is crackling without running audition now.  But I haven't
> seen the mechanism flare that is supposed to catch that.  It's likely
> in hardware like we predicted.

**The `because` is the sentence before the conclusion, not the
conclusion.**  He reached for hardware, reasonably, and the reason he
had to reach at all is the card: *nothing he could look at told him
whether the program had noticed.*

## Found by looking, 2026-08-17

**The mechanism is there and it does run.**  Every part of it was
checked rather than assumed:

- `host.c` recovers from every underrun through `snd_pcm_recover` and
  counts it; `audiohost.Host.dry` reads that count, and `worst_us` the
  longest block a render took.
- `audioeditor._say_dry` compares the count against the last one it
  mentioned and says *"the card ran dry N× — something took the
  machine"*.
- It is called from `_progress`, which the housekeeping thread runs
  **every five milliseconds** while the C host plays.
- The C host is built and present on this machine (`has_device` → True).

So the flare fires.  **It just does not last.**

### Why it was not seen

`_say_dry` calls `self.say(...)`, and the status line holds **one
sentence**: whatever was said most recently.  `DRY_EVERY = 2.0` further
limits it to one mention every two seconds — right, because a line per
dropped block would be the status bar stuttering about the sound
stuttering.  Between them:

> **A crackle that happens while you are reading code, or that is
> followed by any other sentence at all, leaves nothing behind.**

Which means the observation *"I haven't seen it flare"* cannot
distinguish **it did not happen** from **it happened and was
overwritten** — and that is the whole defect.  An instrument that cannot
be interrogated after the fact is one you have to be watching at the
instant, which is the thing nobody is doing while working.

**The count is durable and the telling is not.**  `Host.dry` is a running
total for the life of the host; only `tools/stutter.py` ever reads it,
and that is a bisect harness run outside the editor.

### And the cause this time was almost certainly not hardware

Recorded so the next reader does not repeat the search: between 04:44 and
05:22 that day this machine was running a full fenced test suite, `cargo`,
two X servers and twelve stray polling shells — a session's own
footprint, which is exactly *"something took the machine"*.  The
recorded first check for judder (`powerprofilesctl get`, from 08-14) was
run and came back `performance`, cores at 2.7–2.9 GHz, so the known cause
was ruled out with evidence.  Hardware remains possible and is not yet
supported by anything.

## Questions

**Answered, 2026-08-17: a mark in the tally row, and it must survive a
restart.**  His words, and both halves are recorded below with what they
cost.

Three shapes were offered:

1. **A mark in the tally row.**  That row already exists, is already
   glanceable, and already speaks `spec/rocks.md`'s vocabulary of marks
   that grow with a quantity.  Cheapest by far — but it puts two
   unrelated meanings on one row, which `spec/rocks.md` itself warns
   about.
2. **Its own quiet row**, beside the tally, present only once the count
   is non-zero.  Costs a line of the bar on a bad day and nothing on a
   good one.
3. **A command that answers** — `dry`, say — so the question *"did it
   flare?"* has somewhere to be asked hours later.  The status line
   stays transient, and the fact stops being lost, because a fact you
   can *ask for* does not need to be shown.

He picked **the first**, and the objection to it dissolves on a second
look.  `spec/rocks.md` warns against two meanings on one channel, and
this is not two meanings: the row already carries **the person** and
**the project**, and a dry count is a third party to the same question —
**the machine**.

    you 6h12m ▪ [▪▪◆▲▲ ◆]   project 5 ▪ [◆▪▲▲▲▲▪]   dry 43 ◆

Three answerers, one question: *how has the day been.*

### Surviving a restart — answered, and not blocked

The count lives on the C host and dies with it, so a rebuild resets it
and *"has this been happening all morning?"* is unanswerable without a
record.  **Henri, 2026-08-17: yes, it should survive.**

He added: *"I think this is blocked by the persistent-workbench-state.md"*
— and it is not, which is worth writing down rather than agreeing to.

`card:timer.md` built the durable home this morning:
`presence.state_path()` (`$XDG_STATE_HOME/gestate/`) and `presence.tsv`,
**already a per-day record of how the day went**, already written and
reloaded, already tolerant of a line it cannot parse.  A dry count is one
more column on a line that already exists.

`card:persistent-workbench-state.md` is a different question — *editor*
state, the caret and the zoom and the transport — and its own open
decision is where that goes, *"beside the `.ges` file, in the project, or
in the user's home"*.  Nothing here waits on that answer.

**What the two cards share is a directory, not a dependency**, and
`presence.state_path()`'s docstring already names the hazard: the other
card should *take that function rather than inventing a second home*.
The risk is two files, not the wrong order.

## What the work is

1. A `dry` column on `presence.tsv`'s per-day line, fed from
   `Host.dry` — the file's reader already skips a line it cannot make
   sense of, so an old record loads unharmed.
2. A third field in the tally row, on the same marks, appearing only
   once the count is non-zero — a `dry 0` every day is the always-on
   mark `spec/rocks.md` refuses.
3. The threshold picked from outside the data, as the timer's was.
   Nobody knows yet what an ordinary number of underruns in a day is;
   **measure a quiet day first**, because a scale fitted to a day when a
   test suite was running would call a healthy machine loud.
4. **Then** the question he actually asked — is it hardware? — becomes
   answerable, because there will be a number to compare across a quiet
   machine and a busy one.  Today there was not, and that is why the
   answer was a guess.

## Seen once, 2026-08-17 evening — and that is the card

While the full suite had the machine, the flare fired and Henri caught
it:

> the card ran dry flared. And I didn't notice except on that message.

**Observed rather than reasoned, and it confirms both halves at once.**
The mechanism works — `host.c` counted the underruns, `_say_dry` said so,
and the sentence reached the status line.  And it lasted exactly as long
as the next thing the editor had to say, so the only reason it was seen
is that he happened to be looking at the bar in that second.

He was not hunting it.  He had been told an hour earlier that a suite run
would take the machine, so he knew what the crackle was — and the
instrument that was supposed to tell him told him once, by luck.

With the fix this card asks for — a mark in the tally row, surviving a
restart — it would simply have been there when he looked.  That is the
whole difference between an instrument you must be watching and one you
can interrogate.

**And the cause was a session's own footprint**, for the third time that
day: a full `tools/suite.py` run, on the machine he was listening on.
`journal.md` §"And what a session costs the machine".

## What landed, 2026-08-18 — steps 1 and 2

**The count is durable and the row carries it.**

* `Day` has a `dry` column; `presence.tsv` gains a sixth field, and a
  five-field line from before it loads unharmed with a zero.
* `Presence.ran_dry()` records it **every pass**, not only when
  something is said — the sentence is rationed to one every
  `DRY_EVERY` seconds and the record must not be.  It deliberately does
  not move the hand: crediting somebody's `worked` for an afternoon the
  sound spent tearing is the lie this instrument exists not to tell.
* The row says `dry 43` once the count is non-zero and says nothing on a
  quiet day.
* `Workbench.dry_since_kept()` keeps a **second watermark**, because one
  running total now has two readers moving at different times.  A total
  that goes *down* is a rebuilt host and not a count going backwards —
  the case that would otherwise have lost every underrun after the first
  rebuild, silently.

Tested in `test/test_presence.py` §"The machine's half of the row" and
`test/test_audioeditor.py` — including the rebuild, which is the half a
sentence could never have fixed.

## What is left, and what it waits on

**No mark beside the number yet, and that is step 3 unchanged**: the
threshold is picked from outside the data, and nobody knows what an
ordinary number of underruns in a day is.  **A quiet day has to be
measured first** — today was not one; the machine carried a thirty-minute
fenced suite while its owner sat listening to it.  A scale fitted to
today would call a healthy machine loud.

So the number stands bare until there is a quiet day to compare it
against, and step 4 — *is it hardware?* — becomes answerable only then,
because it needs two numbers and today there is one.

**And the first thing it will measure is a session.**  Three times in
this card the cause was a session's own footprint.  That does not make
the instrument less worth having: it turns *what a session costs the
person listening* from an anecdote into a column.
