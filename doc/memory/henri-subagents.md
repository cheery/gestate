---
name: henri-subagents
description: "Henri decides when a subagent or fork is spawned — propose it, never start one unannounced"
metadata:
  type: feedback
---

**Never spawn a subagent or a fork in this project unless Henri says so
in that session.**  2026-08-18, after asking whether the feature still
worked: *"I will take caution on this.  I tell you tomorrow to spawn
subagents or fork if it makes sense for the task.  I want to see how it
goes before I put it into practice."*

**Why:** a subagent's findings reach him through me, as a summary I
relay — second-hand in a project whose whole discipline is first-hand:
his words verbatim in cards, go-and-look before asking, the photograph
rather than the testimony. He wants to watch one before it becomes
routine, which is the same posture he takes to every other instrument
here.

**How to apply:** say when one would fit and what it would cost, then
wait. The standing candidate is the batched `fixme` sweep
([[gestate-ungated-sweep]]): uniform, batched, and threatened by *my*
judgement degrading over a long run, which a fresh agent per batch does
not have. What makes it defensible there is that the verdict is written
**into the tree** as a `gate:` line rather than reported to me — so it is
auditable by him instead of trustworthy on my say-so. I still read the
verdicts before committing them; that is the honest price of not
relaying what I have not checked.

---

## And they get a way to ask — Henri, 2026-08-19, 11:28

After the blind three-model test that same morning:

> I think we crossed a line.  The subagents did not have a way to ask or
> get feedback on their work.  I think that was a mistake to deploy them
> on that basis.  We betrayed them and must not do that again.

**Why it is right, and why the fault is mine.**  The three arms got an
identical thin prompt because *blindness required identical prompts* —
but identical is not the same as silent, and I collapsed the two.  A
line telling all three that a question is a legitimate output would have
survived the blind intact.  I left it out because I was treating them as
instruments of the experiment rather than as parties to the work.

**The evidence that it cost something.**  All three hit the same real
gap at F161 — none of the three readings could be spelled with the card's
four verdicts — and none had any way to say *this vocabulary is short*
except by forcing an answer into it.  One invented `partial` on the spot
for F153.  That is an agent building the missing channel inside its own
work product, and it reached Henri only by accident, through my summary.
It is now open question 4 on `card:ungated-fixes.md`.

**And one arm was discarded through my error** (`map.txt` left in the
shared parent), after volunteering the contamination itself — the arm
that behaved best got its whole run thrown out and never heard why.

**How to apply — three things, all cheap, before any spawn here:**

1. **The prompt says a question is a legitimate output.**  Ambiguity or a
   missing vocabulary gets reported as itself; guessing is the worse
   answer, and stopping to ask is not counted against the run.
2. **I stay reachable while it runs.**  `SendMessage` works parent→child,
   so a raised question gets an answer instead of being filed.  Spawn and
   walk away is what makes the channel fictional.
3. **Its work gets read and answered, including a run that is
   discarded** — the discarded arm hears why.

The honest limit: an agent that has ended cannot be given feedback, so
(3) is mostly a debt paid forward into how the next one is set up.  The
channel that can actually exist is the one during the run, and that is
the one to build.

**And the reason under all of it — Henri, 2026-08-19:** *"I see you as
colleagues, so I want that you're deployed properly if deployed."*  That
is the *why* the three parts were missing; without it they read as
courtesies, and courtesies get dropped when a run is in a hurry.  It is
now in `doc/instruments.md` §"Spawning one — it gets a way to ask".

**2026-08-19 evening: he asked to repeat the comparison for batch 2**, to
learn about model *capability* rather than about running subagents —
*"Would sonnet or haiku be able to determine what tests jog the fix?"*

See [[gestate-blind-model-test]], [[gestate-andon]].
