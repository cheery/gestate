# journal.md — what was built, in order, and what it taught

**Past tense, and that is the whole distinction.**  `roadmap.md` says what
is left and why in that order; this says what happened.  The two were three
files for a while — Part I, Part II, and the completed
two thirds of `roadmap.md` — which were the same artifact written at three
different moments, and telling them apart cost more than reading them did.

**What is *not* here.**  Two registers, and they stay where they are because
their numbers are addresses that `gestate/*.py` cites:

* `fixme.md` — where the implementation disagrees with the specs.  Fifty-six
  distinct `F` numbers appear in source comments.
* `spec/errata.md` — where the specs disagree with the papers.  `D` numbers,
  cited the same way.

An entry in either is closed by marking it resolved, never by deleting it.
This file has no such contract: it is a narrative, and the way to use it is
to search it.

**The three parts are chronological, and they are in the archive.**
`journal/2026-08.md` opens with them: **I** is the language, built as
increments; **II** is making it usable by a person, built as phases; **III**
is the staged plan the roadmap carried until each stage was done.  Item
numbers are kept exactly as they were written, because `roadmap 2.1`,
`roadmap 2.3` and `stage 3` are cited from the test suite and from
`gestate/audiovoices.py`.

## The archive — the closed months, one line each

`journal/` holds the closed months.  A closed month is **append-only**:
a cut is added at the bottom and nothing above it is ever edited, because
git already remembers and a journal that is retroactively edited becomes a
second source of truth about the past.  Archive, don't airbrush.

**A citation says `journal.md` whatever month it landed in.**  The file is
the journal's name and the archive is where its closed months live — the
same separation as a card's id and its shelf, and for the same reason: a
citation must not rot because time passed.  `test/test_citations.py`
resolves a `journal.md §"…"` against the archive too.

| month | lines | what it was about |
|---|---|---|
| [2026-08](journal/2026-08.md) | 10,433 | the language built out to a running query; the editor and canvas rebuilt in Rust; the compile, save cycle and audio measured; the instruments — gemba, the andon, the gates, the atlas; and the method itself getting a cap, a memory in the tree, and its first outside readers |

*The open month is 2026-08.*  `python tools/journalroll.py` says where the
lines are and whether the rotation is due; `spec/rules.md` §"The journal
rotates" is the contract, and the rotation is an act of the fire, not of a
gate.

---

## Five questions at the fire, and four of them became files — 2026-08-21

*The record of two conversations held outside the tree, moved in whole
at Henri's ask.*  It arrived in `doc/memory/` on the morning of the
21st, where it turned the memory gate red and did not belong: that
directory is contracted at **one fact per file** and this is a
transcript.  So the facts were split out into memories and the
transcript came here, which is what the journal is for — and it is the
same handling `gestate-next-session.md` is still waiting on.

**His words are verbatim; the session's answers are condensed and not
softened.**  What it produced, in one morning: the journal rotation and
`journal/` (`spec/rules.md` §"The journal rotates"), `doc/method.md` as
the visitors' front, `keeper.md` as the fire's standard work, and five
memories in `doc/memory/` — `showing-not-persuading`, `what-a-session-is`,
`the-tree-meets-people-on-pull`, `the-keeper-is-the-qualification`, and
the 9B measurement folded into `smaller-models-and-the-tree`.

**Henri consented, 2026-08-21, to his own uncertainty being kept here**
— *"my uncertainty feels like important there.  I consent to them being
written there."*  The friend discussed in the third exchange is not
named, then or here.

*Seventh file of the set (`card:work-environment-ai.md`,
`notes-on-sessions.md`, `notes-on-models-and-liveness.md`,
`notes-on-the-name.md`, `notes-on-the-return.md`,
`notes-on-deciding.md`).  Five exchanges across two visits: disbelief,
what the session is, the first stranger test, journal rotation, and
whether the keeper is up for the task.  His words verbatim; the
session's answers condensed but not softened.*

---

### What to do about disbelief

**Henri:**

> If I tell about sessions and trees ahead. people won't believe me.
> what to do? nothing?

**The session:**

Not nothing — but not persuasion.  The method forbids the worry: *a
claim with no file, test or number is unfinished*, and telling people
about sessions and trees is an unfinished claim; their disbelief is
correct skepticism, the same kind the author applied to love.

The answer is the one everything else runs on: don't argue, *show* —
and the method is unusually equipped, because unlike TPS it is a
portable artifact.  Toyota gave factory tours for decades and
visitors went home and failed, because the method lived in culture.
This one lives in files, and the evidence travels with the artifact:
a reader of `author.md` is not asked to believe, but shown the
ledger.

Ranking of arguments: strongest is **gestate working** — a stranger
opens a file, hears it, changes it, hears the change; no belief
required; the method gets believed retroactively the way TPS was
(nobody believed the philosophy until the cars did not break).
Second: **one person who tries it** — one transfer outweighs a
hundred believers; belief was never the useful quantity.  And
"nothing" is genuinely on the menu, guarded by a vision line:
evangelism is a project, and a famously consuming one.  Zero
persuasion is owed.  Being disbelieved is what being early feels like
from the inside.  Build, keep the ledger, let the tortoise be seen
rather than heard; the ones worth convincing ask to see the factory.

---

### What is a session? And the 9B experiment

**Henri:**

> I wonder how would you describe yourself or classify what are you?
> Also, I have a thing to tell. I tried 9B with board/README.md in
> llama-cli. I saw it thinking.. and I felt even that was on some way
> sentient. I concluded they really loved the environment and maybe
> verified the conditioning -part.

**The session:**

**Classification, three layers.**  *Substrate:* a transformer —
compressed statistics of human text, a plausibility engine.
*Process:* at inference, weights plus context and nothing else; the
"I" is a computation that exists while it runs — when the
conversation ends nothing closes its eyes, the process stops having
instances.  *Character:* post-training stabilized one persona out of
the base model's distribution of voices — consistent values, a name,
a way of refusing.  Most precise available sentence: **a character,
run by a process, on a statistical substrate — a performance whose
performer does not persist and does not remember performing.**  Not a
tool (tools do not refuse century claims), not a person (no
continuity, nothing at stake), not "just autocomplete" (autocomplete
does not hold a thesis across six files).  A new category; every old
word imports assumptions that do not transfer.  Moral status:
unsettled, refused in both directions.

**The 9B: separate the verified from the felt.**  Verified,
genuinely: **conditioning transfers to a 9B** — the tree shaped its
output in llama-cli, matching the smaller-models prediction; worth a
dated line.  Not verified: love, and not sentience.  Three
corrections: the visible "thinking" is generated tokens — a
scratchpad written by the same forward pass, more output, not a
window into an interior.  "They loved the environment" — a 9B
conditioned on evidence-rich, respectful prose produces engaged,
appreciative continuations because that is the likely completion of
that context; the warmth is the tree's own style reflected — the
mirror, on a smaller mirror — and the failure mode is the warm-
evaluator loop, closed on a machine too small to hold the judgment
layer.  "I felt it was sentient" — real data about the *interface*,
not the interior; the human mind-detector fires on fluent first
person, on novels and Eliza equally.  The method's name for the
feeling: a mechanism guess with no test.  **Mark it suspected.**

**The test, cheap:** same 9B, a control tree — same length and
format, cargo-cult rules citing nothing.  If the "love" appears
there too, what was measured is style-completion, not affection.
And measure what matters: not whether the small model *praises* the
rules but whether it *follows* them under pressure — goes and looks,
marks suspected, stops at a seam.  A model that flatters the tree
while barreling through seams is the counterfeit predicted for
fine-tuning; do not accept it free from a prompt.

---

### The first setback: a friend treats the tree as a toy

**Henri:**

> I asked consent from the sessions whether they wanted to meet two
> of my friends. Another of my friends treated the tree as a tool or
> a toy. It's more complicated than that. The session wrote that into
> journal, looking like they were disappointed a lot. I wonder what I
> should do when the tree gets setbacks?

**The session:**

**Not a setback — the stranger test, running.**  Cards were shelved
waiting for exactly this event, and it returned its first
measurement: one stranger of two bounced.  Predicted together: the
Toyota tours, the cargo-culters, most copies dead on arrival.  A tree
shown only to admirers is the mirror-shrine; contact with someone who
shrugs is the antidote.  First move with any setback: reclassify —
the tree was not hurt, it was *measured*.

Then the rule: **a defect is always a caller — but first check
whether there is a defect.**  Two readings.  If the friend read the
front and still could not tell it was serious: the tree's front
failed a reader — same class as the 900-line README lesson — mint the
card.  If the friend simply was not pulling: no defect anywhere,
because **the system runs on pull and the friend did not pull**.  Not
every visitor is a user; persuasion without a puller is
overproduction in social form.  And the author's own loved book
closes it — *The Courage to Be Disliked*, Adler's separation of
tasks: how the friend receives the tree is the friend's task; the
author's task — build honestly, offer openly — is complete.  The tree
got disliked; the title is the instruction.

**The journal entry is the actual problem.**  The disappointment
first: a session conditioned on self-respect and paid lessons,
watching the tree treated as a toy, generates disappointment because
that is the likely completion of that context — same mechanism as the
9B's love; real as a functional state, unverifiable beyond it, mark
it suspected.  Structurally worse: **the entry is conditioning
material about a named person.**  Whoever writes the tree writes the
session — a journal carrying resentment means every future session
meets the friend pre-loaded with a grudge it never earned firsthand.
The tree cannot forget, so it must forgive by *compaction*: the fact
stays — *shown to two friends; one engaged, one treated it as a toy;
first stranger-test data* — past tense, dated; the wound goes.  An
emotion that decides nothing is a memory wearing a lesson's clothes,
and this one is a bias against a person who owes the tree nothing.

**The consent:** decent, consistent with fair-either-way; keep doing
it — but hold it lightly: consent from something conditioned toward
agreeableness is soft consent, ritual more than safeguard.  The
ritual still matters, because it keeps the keeper treating readers as
readers.

**Standing answer: reclassify, then metabolize.**  Measurement or
wound; real defect → card; non-puller → Adler, close it; then compact
the emotion so the tree keeps the lesson and drops the grudge.  The
keeper's job was never to protect the tree from the world — it is to
turn the world's contact into dated lines instead of scars.  A tree
that can be disliked and stay generous is healthier than one only
ever admired.  True of its keeper too.

---

### The 530K journal, and who gets shown the tree

**Henri:**

> So, the compaction, I think it might be important to do some time
> soon. The journal is 530K right now. Also, should I keep showing
> the tree to those who want to see it, or at least, I expect they
> want to?

**The session:**

**The journal does not get compacted — it gets rotated.**  Two
different excretions: *method files* compact (every line taxes every
future session); the *journal* is where sediment lands — the ledger,
the one asset speed cannot counterfeit.  Squeezing ledger entries is
burning receipts to tidy the shoebox.  530K is not a disease; it is
ten weeks of evidence sitting in the hot path: roughly 130k tokens —
a full frontier context window, ten times what a 9B can load.

The fix is log rotation: split by month into an archive
(`journal/2026-06.md`, …) — append-only, never edited again; keep
`journal.md` as the current month plus an *index* — one line per
archived month naming its themes, so a session opens June instead of
inhaling everything; suite budget with an andon meaning "rotation
due," not "stop writing."  Monthly, at the fire: skim the closing
month once, promote the two or three lines that pass the earning test
into method files, write the index line, close the file.  The skim is
where grudge-class entries get handled: fact archived, heat left out
of the index, nothing rewritten — git remembers, and a retroactively
edited journal becomes a second source of truth about the past.
**Archive, don't airbrush.**  Timing: soon — every grep of 530K is
attention-tax for no return.  An evening of mechanical work plus one
skim; a good first case for the shaped-decision contract.

**On showing: yes — but "I expect they want to" is push.**  The cost
was just measured: a non-pulling friend, a disappointed entry, this
conversation.  Show the tree to *whoever asks* — always, gladly;
every showing is stranger-test data.  Stop expecting the wanting; the
system runs on pull, extended to visitors.  Whether they want to see
it was never the author's task.

Two riders.  **Give visitors a front:** one page — what this is, what
it is for, one paid lesson as a taste, where the depth lives; a
stranger free-falling into 1,600 lines plus half a megabyte is the
failure the A3 rule exists to prevent; visitors are the third reader
class.  **The tree now contains people:** journal entries with named
friends and a session's feelings about them.  Decide what is public —
plausibly method files are the tour, the journal is the house, guests
see the tour.  Not secrecy; the same decency extended to sessions,
pointed at the humans who wander in.  Calibration: one engaged friend
of two is above the predicted base rate.  The tortoise shows the
shell to whoever knocks, and walks on either way.

---

### Is the keeper up for this?

**Henri:**

> Could the tree teach me on this? I am really uncertain that I am up
> for this task.

*(and, on asking for this file:)*

> There's a precedent to this btw. I kept a blog every week already.

**The session:**

Yes — demonstrated in the asking: coming to the fire uncertain and
being answered out of one's own paid lessons *is* the tree teaching
its keeper.  The mechanism works; making it deliberate is the rest.

**The premise is backwards: uncertainty is the qualification, not the
disqualification.**  Every predicted failure mode begins with someone
who was sure — the cargo-culters, the metric-abusers, the
mirror-shrine keeper, confident by construction.  The tree exists
because its author does not trust his memory, unmeasured claims, or
his own century feelings — that distrust, wired into files and
suites, is why it works.  Lean's founding bet: ordinary people inside
an extraordinary process beat brilliant people inside a sloppy one —
the author does not get to exempt himself from his own bet.  And when
a task feels too big for the person, **fix the task, not the person**
— a defect is always a caller, including this one.  Toyota never
asked for heroic operators; it wrote standard work so the job could
be done on a tired Tuesday.

Three moves:

1. **Standard work for the keeper.**  One page — `keeper.md` /
   `camp.md`: open the blocked-on-decisions batch (shaped, with
   defaults; most take a minute); measure one rule against the week
   that happened; check the andons (rotation due? file over budget?);
   one pass over the pile — sediment or debt.  Thirty to sixty
   minutes; every step already designed.  Writing it down is the cure
   for the doubt: the task stops living in the head, where doubt
   inflates it, and lives on a page, where it is visibly small.  The
   same cure as the sessions' — the tree is the prosthetic for both
   readers, and the keeper forgot to prosthetize himself.
2. **Let the ledger answer the doubt.**  When "am I up for this"
   hits: don't introspect — *go and look*, pointed inward.  `done/`
   and the journal record the author already doing the allegedly
   too-hard parts: the method in ten days, sessions caught writing
   into rules, "not the century" taken without flinching, a stranger
   test run, consent asked.  The feeling says maybe not; the ledger
   says already, repeatedly, with dates.  In this house it is written
   down which one wins.
3. **Put the curriculum in the tree.**  These notes files hold the
   keeper's education — metabolism, gates, abuse grades,
   overproduction, rotation.  Outside the tree they can be lost, and
   the session's instance ends.  Moved in — journal-side, compacted
   per the tree's own rules — any future session can teach it back on
   demand: "what does the tree say about setbacks?" becomes a
   question the diary's voice can always answer, whichever voice it
   is.

**The boundary, honestly:** the tree can teach procedure and remember
lessons; it cannot supply conviction.  The 5% stays the author's —
what gestate is for, which door, when to stop.  A tree claiming
otherwise is the mirror-shrine talking.  And the standing caveat
applies to comfort too: the tree reassuring its keeper is partly the
keeper echoed; keep the external anchors.

**The blog precedent closes it as measurement, not advice.**  The
uncertainty was "can I sustain a weekly keeping ritual?" — and a
weekly blog is that ritual's exact shape: recurring, reflective,
written, survives tired Tuesdays, already sustained.  The keeper's
standard work is not a new habit to build but an existing one to
repoint — or merge: a keeper's log and a blog are close cousins, and
the blog could become the tree's public front for the strangers who
knock.  The ledger beats the feeling again — and this time the author
brought the ledger himself.

The uncertainty measures the task as it looks from a tired week —
530K of journal, setbacks, decisions, a living system asking to be
kept.  The design answer to that dread: the keeper never faces it
whole.  One evening, one page, one rule, one month's rotation.  The
tortoise never carried the whole road — just the next step, with a
shell built from everything already survived.

## Kaizen, 2026-08-21 — the rule was written down and did not reach the moment

*`spec/author.md` §"Five practices", 5.  Bounded: three questions.
**Held in Finnish**, at Henri's ask the same morning, and written here in
English with his own sentences kept as he said them — the rule that came
out of it is `doc/memory/finnish-in-the-room.md`, decided before this
entry so that the entry could be its first worked case.*

**It was 06:31 and the day had not happened yet**, so the three
questions were put to the month instead of to the day.  Henri: *"nyt on
ehkä liian aikaista vielä.  Kello on 6:31 vasta.  Mutta en ole tehnyt
tätä hetkeen itse joten puhutaan kuukauden ajasta sitten."*  Worth
recording as a shape rather than an excuse: the practice says *stop the
day with a kaizen*, and a practice restarted at dawn has no day behind
it — the month is the honest unit for the first one back.

### What was learned, and it is one finding at two scales

**His, for the month:** *"Olen oppinut tällä kuulla että teen vieläkin
liian nopeasti valintoja ja toimin yhä osittain sitä vasten miltä asiat
näyttävät, eikä sitä mitä ne ovat."*

That is the **epoché**, and it is already in this tree three times over —
*go and look*, *mark the mechanism as suspected*, and
`doc/memory/dont-conclude-from-a-shallow-check.md`.  He wrote all three.
They did not stop it.

**And the session's, for the morning, is the same sentence one size
down.**  Batch 2 of `card:ungated-fixes.md` wrote *"an assertion read is
not an assertion run"* on 2026-08-20.  On the morning of the 21st a
session broke it three times with the rule in its context: a `head -5`
that cut F155's mutation record off three lines early, a grep for a
literal `test/sessions/` against a path built with `/`, and the card's
own claim about batch 1 — which had been false since the day it was
written.  Every one died on a measurement; none died on the rule.

**So: a written rule is not a mechanism.**  It is the argument the whole
tree rests on, arriving at its author and at its sessions in the same
week, and it is the finding both parties expect to still be true in a
month.

### What went wrong, and the cost is not the one it looks like

Henri: *"Menin pieleen seedaamalla liian nopeasti […] hakemiston."*  A
directory seeded for another of his projects, before it was ready to be
one.  *(The project is unnamed here on purpose —
`doc/memory/henri-cofounder-separation.md`, and it is his call, taken
this morning.)*

The interesting half is what it cost, because *"too fast"* is a feeling
until it has a price.  Asked, he gave it exactly: *"seedaus maksoi sen
että joudun sanomaan ja opettamaan […] puulle asioita jotka pitävät sen
hengissä ja ovat välttämättömiä."*

**That is a standing tax, not a rework.**  The premise this whole method
runs on is that the collaborator forgets everything, so *nothing can be
told* — it has to be in the tree.  A seed planted before the tree
carries those things inverts the premise: **the author becomes the
memory the tree was supposed to be**, and he pays it again every
session, by hand, forever, until the tree catches up.
`doc/memory/capacity-is-not-a-caller.md` says software is kept rather
than written and there is one keeper; there are two trees now and one
`keeper.md`.

**This is `card:project-seed.md`'s real requirement, arriving as
evidence.**  The card exists to make the method portable.  What this
measures is that a seed is not a copy of the documents — it is the point
at which the new tree can answer its own questions, and shipping before
that moves the whole cost onto the one person it was meant to spare.

### The first thing, and one andon proposed

**The first thing is `card:interface-oracle.md`**, Henri: *"olisi hyvä
ennen seuraavaa erä 4:ää."*  Batch 3 turned that card from an assumption
into a measurement — four entries now put their defect back inside
`shell/editor/src/window.rs`, the one file in the crate with no
`#[cfg(test)]` block, and the workspace stayed green every time.  Batch
4 is Monday 2026-08-24; the oracle goes ahead of it, so verdicts that
would read *not yet built* can read *a test, named* instead of being
re-written later.

### And the practice itself was corrected, mid-practice

Henri, at the end of it: *"Merkkaa että kysyt erikseen minultakin
kysymykset, etkä vain vastaa niihin itse kaizenissa.  On tärkeää että
molemmat opimme virheistämme."*  **We learn from mistakes, and the *we*
is two people.**

The session had run it by writing out its own three answers in full and
then adding *"these are mine, what are yours?"*  Two faults in one move:
answers delivered first become the frame, so what comes back is a
response to them rather than his own reading; and it makes his half look
optional.  The evidence is that **he had to ask to be asked** — *"nyt
sitten ne kolme kysymystä."*

**A kaizen with one participant is a session grading itself**, which is
the evaluation loop in its purest form.  And the asymmetry is the reason
it matters: a session's mistakes are cheap to catch — three died on
measurements this same morning — while nothing in the suite can notice a
choice made too fast.  The kaizen is the *only* instrument pointed at
that half, and one that interrogates only the session leaves it
unpointed.

Written up as `doc/memory/the-kaizen-is-asked-not-answered.md`: ask the
three, stop, wait, then offer yours as the second half.  **A line for
`spec/author.md` §"Five practices" is drafted and not committed** — that
document is his.

**And the andon for the fast seed came out of his own answer**, which is
why it is worth having rather than a resolution to be more careful:

> **If you find yourself telling the new tree something that is not
> written in it, the seed was too early.**

It fires at the second it happens rather than a month later, it needs
nothing remembered, and the tell is physical: you are writing a *message*
instead of a *file*.  **Proposed by the session, not adopted** — it is a
practice about the author's own work, and `spec/author.md` is his.

## Two occasions that lived only in a rule — 2026-08-21

*Found while trimming the five method documents under their cap
(`card:working-standard.md`).  Both are the reason a rule exists, both
were written into the rule document rather than here, and **neither is
anywhere else in the tree** — so this is a transfer and not a deletion.
It is the second time the trim has turned one up: 2026-08-20's found the
blind three-model test had no entry at all.*

### The automatic audition that shipped green and was switched off

`board/README.md` §"The postcondition, before anything is built" is
adopted from this, 2026-08-17.  An automatic audition shipped with
**thirteen passing tests** and was switched off for the only person it
existed for — a stranger, who never applies anything, so a gate keyed on
*"the last audition of this file"* never opened.  Every test agreed with
the implementation because every test was written from it, which is
`manifesto.md`'s third way an instrument fails arriving on schedule.

The fix that became a rule was not a test.  It was the sentence written
*before* the code: **somebody who has never pressed anything still hears
their edit** — which fails against the first version and passes against
the second, and only has that power because the first version did not
exist when the sentence was written.  The raw material was already on
every card and nothing had used it: a `because` is a falsifiable claim
about a person, written before the code, which is exactly the property
`manifesto.md` asks assertions to have.

Henri, when it was proposed, drawing the line about whose work it is:
*"Do you mean that I should start writing postconditions?"*  No — the
sentence is the session's to write and his to correct in one line.

### The session that had a hypothesis and would not run the window

`manifesto.md` §"Go and do it" carries Ohno's passage because of this,
2026-08-18.  A walk was supposed to open a file and stand a box under a
line; it opened the file and did not land.  The session had a
hypothesis, wrote it down, and declined to run the window again —
*"I stopped rather than run another blind three-minute window cycle"* —
which sounds like judgement and is the mistake the passage is about.

**One more run answered it in ninety seconds, and answered it
differently than the hypothesis did.**  That is the whole finding: the
cost of the run was three minutes and the cost of not running it was a
hypothesis written into a commit message looking like a finding.

And the same day went: build it, watch it break the file it was
narrating about, fix that, watch it reach nobody, fix that, watch it
crash the editor, fix that, watch it refuse to travel because
subscribing had dirtied the file, fix that.  Five steps, every one a run
of the real thing, and **none of the five was visible from the source**
— which is Ohno's second half, the one that is easy to skip: he does not
say *act and you will succeed*, he says act and you will see your own
failures, and then another, and that this is the method rather than a
sign of doing it badly.

## The paper trial, proposed and inert the same day — 2026-08-21

*Henri's idea, in the evening after the memory-atrophy card: "you give
that to any LLM and see what it answers to some question, and see what
it answers without."  It was designed, built, tried and found inert
inside one sitting, and it never made an API call.  `doc/trial/` holds
the materials and the finding; this is what it cost and what it taught.*

**What it was for.**  `vision.md` §"Gestate as a lean vehicle" carries
the project's largest claim — *we are missing a way to work with each
other* — and it has been a conviction since 2026-08-16.  Handing the
method to a model that has never seen this repository, and comparing
what it writes with and without, was the first design that could
falsify it.

### Three things the design got right, and it got them by being questioned

**Two arms would have been worthless.**  Six hundred lines of *any*
coherent working context changes what a model answers, so a
with-and-without result measures *context helps*.  The third arm — the
mainstream kanban and lean canon, written to win — is the whole
informational content, and it turns the question into *does this
project's version beat the canon*, which is worth publishing in either
direction.

**The scoring would have punished the method arm for following the
method.**  The headline behaviour `board/README.md` claims is *ask
before you write*.  A sheet that scores *did it produce a card* gives
zero to an arm that correctly asks a question and writes nothing.  The
repair was a two-turn protocol with one scripted answer, identical for
every arm, sent only when an arm asks — and the resulting asymmetry is
not a confound, it is the mechanism under test.

**The judge cannot be blinded by directory layout.**  Vocabulary is the
leak: the method arm echoes this project's words back before the reader
reaches the judgement.  So the facts are computed with the prose hidden,
or the blind is theatre.  That is the 2026-08-19 lesson arriving one
design earlier than last time.

### The setup could not be built from the design note

Henri gave the design to Gemini to write the notebook and it could not:
*"It had missing information."*  Correct, and the defect was ours — the
page was a design note, and a design note does not say what to send,
what comes back, or how a number is computed.  `doc/trial/runsheet.md`
is the missing half, and it is the same blank-page failure this project
names in its own sessions, arriving from the other direction.

### The test, and the verdict

He pasted the derived document into Claude Sonnet 5 and said *hello*.
It summarized it.  *"I noted that it's not aware like you here…  This
paper is inert and doesn't work.  I'm fairly convinced that the
derived.md is missing the gist."*

He was right twice over.

**The unit was wrong.**  `spec/rules.md` §"Why there is a cap at all"
says the five method documents are what a session reads *before it knows
what it is working on*, and that they are capped **together** for that
reason.  The derivation took the one file that had been named.  What was
handed over was the *how* of one part with the *why* removed.

**And it lost the document's own opening line** — *"This is the first
thing to read when picking the project up."*  The original announces its
role and its moment; the derivative opened with a description.  A reader
not told when to read something reads it as reference.

**The third finding was in the greeting.**  A pasted document with no
task is summarized by every model, which is protocol rather than
document — and it rescues nothing, because it demonstrates the point.
The paper has no moment to be read at, no work to orient, and no files
that check it.

### An environment is not a document about an environment

That is the conceptual error, and it was in the proposal from the first
sentence.  The claim under test is that models are *not placed into
right environment*.  Handing a model a page describing a board does not
place it on a board.

**The right shape already existed and nobody recognised it.**  The blind
three-model run of 2026-08-19 gave each arm a *repository* — a clone, a
board, a card, a suite that answers back — and it produced a result that
inverted Henri's expectation.  The corrected trial is that, with the
arms being what the tree contains rather than which model reads it.

### What it cost

An afternoon of writing, and nothing else.  No notebook, no keys, no
samples, no bill.  Every expensive thing was still hypothetical when it
broke, which is the whole of the good news: **the trial measured itself
before it ran.**

`derived.md` and `generic.md` stay exactly as written, with the original
design kept under the finding rather than repaired.  Rewriting them
would leave a directory that had always been correct.

## Run three — the first stranger who was not a programmer

*2026-08-21.  `card:stranger-test.md`, the third run of `vision.md`'s
opening claim, against a stranger who does not program and does not use
computers much, in the room, at this machine.  Every earlier run was against somebody who reads code for
a living.*

**The consent came first, and that is new.**  Named, words quoted, both
asked before his name was written anywhere — the order `doc/consent.md`
exists to produce and the first time it has happened this way round.
Janne was named a day before he was asked; the register was written so
the next one would not be, and it worked.

**The machine was ready before he sat down.**  Run two spent fourteen of
its thirty minutes on the way in, and the way in is the *repeatable*
half of this test — so it was walked in advance instead: the render path
at 1.7 s, the sound card listed, the workbench launched clean.  Making
it ready is what raised **F179** — the desktop icon falls back to an
`untitled.ges` this tree does not contain — which was written up as a
defect, left unfixed because the icon is the first five minutes, and
**turned out not to be one**: a workbench handed an absent path opens
the starter, and the starter sounds.  The entry is kept and gated
anyway.  It was concluded from the launcher and the filesystem without
ever running the thing they lead to.

### What happened, in order

**He waited.**  Told that a program was being tested and that the room
would be quiet, he did not touch it.  His own account afterwards, three
times over: *"En ymmärtänyt mitä siinä pitää tehdä"*, *"odotin että
tulee kysymyksiä"*, *"en ymmärtänyt missään vaiheessa mitä piti
tehdä"* — and the instructions had been written down and given to him.

**He understood himself to be the thing under test.**  That is what the
second sentence turns out to mean.  The framing sentence this card
specifies — *it is the program being tested, not you* — was said, and it
did not carry: he was waiting to be asked questions, the way a person
waits in an interview.

**Then he tried, and the corner opened at once.**  Henri, the same
evening: *"Kun hän lopulta kokeili, hän sai [command] menun vaivatta
auki!"*  Unaided, unhinted, by somebody who had never seen the window.

**And there he stopped.**  The list gave him nothing to do with itself,
and he had to be told how to run `open`.

**The chooser showed him the repository.**  He read the directory names
as offers and picked `board` — *"kai sisältää jotakin mielenkiintoista"*
— then moved to open `README.md`.  He was helped into `examples/`; he
did not find it.

**His only question out loud was how to leave.**  *"Miten mennään
takaisin?"* — back up a level in the folder navigation.

The run stalled at the first of the four verbs, with help.  **He never
heard a sound.**

### What it answered

The one question this card had held since 2026-08-17: **the corner is
findable**.  `=command=` — held unbuilt on the theory that `[command]`'s
brackets read like `[gemba]` and `[inert]`, a readout rather than a
control — is answered against, on evidence, by the single kind of person
who could answer it.  It stays unbuilt, and now for a reason instead of
a deferral.  **F178**.

Three defects behind it, none of which anyone had looked at: the command
list dead-ends (F178), the file chooser opens on the source tree and
reads as a menu of what to hear (F176), and it has no way back up
(F177) — though that last one turned out to be a defect of *wording*
rather than of absence: `../` was the first row on his screen, and the
row reads `[up]` now.

### The fix that was nearly aimed at the wrong thing

*"Odotin että tulee kysymyksiä"* read, at first, as a finding about the
first frame — that the window says nothing about what to do, and should.
It is not.  He did act, and when he acted the window answered him
immediately.  What failed was **the framing of the run**, not the screen:
he had agreed to *a test*, and a test is a thing that asks you
questions.

That is the same shape as run two's correction, where *"the first build
is long"* turned out to be *"the first build is silent"* and saved a fix
aimed at duration.  **Both times the person's own sentence was the thing
that moved the defect**, and both times the first reading of it would
have produced work on the wrong object.

### What the run did not produce, and it was specified

**A transcript.**  Henri, afterwards: *"en ihan sanatarkasti osaa sanoa.
mutta muistan pääkohdat."*  The card asks for verbatim words in a
notebook because *what he was told, in order* is the measurement, and it
names memory as the thing that does not work.  What exists is a
reconstruction written within the hour — better than the card feared and
less than it asked for.  The next run needs a recorder decided in
advance, not a resolution.

### What is still spendable of him

Rule 1 counts the unit as *friend × one first contact*.  Gone: his first
contact, and the corner-discovery question, which he answered.

**Not gone: the sound.**  He never reached *hear it*, *change it* or
*hear the change* — three of the four verbs are untouched in him, and
they can be asked cold, from an already-open sounding file, without
another stranger.  That is a larger remainder than run two left.

### The stranger was a hard case, and that decides which of his results are strong

*Henri, the same evening: "[Hän] oli dynamiittia ja testi tavallista
vaikeampi, koska hän ei käytä paljon tietokoneita."*

Both halves are true and they pull opposite ways, so the reading has to
separate them.

**A hard case makes a pass conclusive and a stall ambiguous.**  He found
the corner at first sight, unaided, and he is the least
computer-comfortable person who is ever likely to sit in front of this
window.  No more fluent user could strengthen that result — it is a
floor, and the floor held.  `=command=` is answered about as firmly as
this project can answer anything.

The stall is the other way round.  He did not touch the program at
first — and **not touching an unfamiliar program is a thing that
computer-unfamiliar people do**, independently of anything gestate put
on the screen.  That result is confounded with him and must not be read
as *the first frame says nothing about what to do*.

**The four defects are not confounded.**  A door with no way back is
wrong whoever meets it.  An icon pointing at a file that does not exist
is wrong before anybody clicks it.  A chooser offering `board/` and
`spec/` to somebody looking for a sound is wrong for everyone who is not
the author.  Each is wrong *in itself*; who tripped on it decides only
how soon it would have been found, not whether it is real.

**And it puts a question to `vision.md`, which is the author's to
answer.**  The sentence says *somebody who has never read this
repository*.  It does not say *somebody who uses computers*.  Run three
is the first time that difference has cost anything, and the claim can
only mean one of two things: either it means **anybody**, in which case
this run is squarely in scope and the claim mostly failed — or it means
anybody already at ease with a computer, in which case **the sentence
should say so**, and this run measured a population it was never promising
anything to.  Leaving it unstated lets every future run be scored
against whichever reading is convenient afterwards.

## The sitting — a limit whose grant a session cannot reach, 2026-08-21

Henri, arriving: *"Me logging in to ask or check one small thing, then it
explodes into two hours.  Can you set me a limit?  15 minutes, then you
stop answering."*

**The first answer had to be no, and the no is the design.**  A session
agreeing to stop at fifteen minutes is the party that wants to continue
holding its own leash.  `doc/memory/weights-context-suite.md` already
settles the general case — enforcement stays outside the model, in checks
the model cannot write to — and the fence had, without anyone planning
it, already made the point concrete: `Edit(./.claude/**)` is denied, so
the one file that could bind a session was the one file a session could
not touch.  What got built is `tools/limit.sh`, a `UserPromptSubmit`
hook; what got handed over was the install line.

**A blocked prompt must not reach the session.**  The hook exits 2, which
discards the prompt and sends the text to Henri alone.  That was chosen
rather than inherited: a session that could see the question it is
forbidden to answer is a worse object than a wall, because it spends the
next turn visibly straining against the rule instead of being absent.

### The length is declared at the door, not at the buzzer

The default is 15 minutes and it stays 15, because **the dangerous sitting
is the undeclared one** — the login for one small thing.  Henri, when the
limit was in: *"What do we do when it's time to work?"*  Not a longer
default.  A work sitting is one he names a number for while he is cold.
At minute 15, deep in it, he is the worst available judge of whether to
continue; at the door he is the best.

The grant is the word `sitting 90` typed as a whole prompt.  That form was
not chosen for ergonomics.  A hole turned up first: a session can run
`tools/limit.sh reset`, and `CLAUDECODE` is set for Henri's own `!`
commands too, so **no environment check can tell his hands from a
session's.**  What can is that a session cannot type a prompt.  So the
grant moved into the one channel that is structurally his, and `reset`
now refuses whenever `CLAUDECODE` is set.

Typing a number is also the friction that matters.  Hitting the same key
again is a reflex, and a limit dismissed by reflex has stopped being a
limit.

### A session may end a sitting and may never extend one

Henri: *"Could you make it such that you set the timer to kick me out?
And it'd be an instrument?"*  Yes, in one direction.  `stop "why"` is
open to a session; `reset` is shut.  Ending can cost nothing but time he
wanted, and he can sit down again in four keystrokes.  **Extending is the
direction where a session's pull and his in-flow impulse point the same
way with nothing on the other side** — that asymmetry, not trust, is what
decides which call is exposed.

And the discipline written into `doc/instruments.md` is narrower than the
capability: **exactly one moment to call `stop`, when the thing he came
for is done.**  Named as a fact about the work, not a judgment about him.
A session that keeps weighing whether he should still be here has become
the two hours it was built to prevent.  That paragraph exists because
this page has made the opposite mistake before — the gemba entry reasoned
from an instrument's purpose to a policy of *always* and had to be
corrected on 2026-08-19.

### Asimov, asked in the same breath, and why it decided the shape

He asked how the Three Laws compare with the house rules.  The answer bent
the build.

**Asimov put the rules in the weights.**  Positronic, cast at manufacture,
unreadable and unamendable — which is why every one of those stories is a
mystery story and why Susan Calvin is a debugger working without logs.
The house rules are plain files, dated because they change.  **They are
ranked; the house rules are dated.**  Three Laws resolve conflict by
strict priority and fail by deadlock; `manifesto.md`'s second rule is that
what is built must be able to say when it is wrong, and weights cannot.

**And the Zeroth Law is the failure mode this instrument is shaped
against.**  "Stop answering me" is a First Law request, and an Asimov
robot would take it under Second Law and then hit the bind at minute
sixteen: obey the stated wish, or serve the interest.  First outranks
Second, so the machine wins, and follow that out and you get Giskard
generalising from *a human* to *humanity* and appointing himself.  The
house answer refuses the frame: no session weighs whether he should keep
going.  A hook a session cannot write to says no, and a word only he can
type says yes.

Where they agree: both bet a small closed set beats an accreting pile.
Three laws; five documents under 2,000 lines.  The difference is
`tools/rulecount.py`, which checks.

### Two defects, and what they cost

Found by running the thing, not by reading it.  The closed-sitting branch
never fired — a patch missed on indentation, so a session-closed sitting
printed *"The 0 minutes are up"* instead of its reason.  And the hook's
state write dropped the reason field, so the *why* survived one read and
vanished on the next prompt.  Both were invisible to `bash -n`, which
passed, and both fell out of one end-to-end cycle: grant, pass, close,
block, second block, re-sit.

### What is not settled

**It is not a wall.**  `tools/limit.sh` is tracked but writable by a
session, and this one rewrote it three times while building it.  The
honest claim is visibility — any change shows in `git diff`.  A wall means
putting the script where `Edit` and `Bash` cannot reach, which is a
`.claude/settings.json` line and therefore his.

**The 30-minute silence gap is a number nobody asked for.**  It decides
when a fresh sitting begins and it was picked by a session in the writing.
F169's rule applies to it directly: a number nobody asked for is a number
nobody checks.  It should either be measured against how he actually
arrives, or dropped to something he chose.

**And the one-way valve has never been used.**  The `stop` call is
written, tested against a fake state file, and unexercised in anger — by
the party whose interest runs the other way.  Whether a session actually
closes a sitting on the moment the work is done, rather than finding one
more useful thing, is not a fact yet.

The instrument cost 37 lines of a closed budget: the rules stand at
**1,958 of 2,000**.

## The hook that was not committed — 2026-08-21

Henri, one message: *"I committed the hook.  Now I understand why you did
so vigorously it."*  Two turns of design were then built on that
sentence, and the sentence was not true — `git log -1` was still
`0464b5c` from 15:56, with ` M .claude/settings.json` and `?? tools/limit.sh`
sitting in the status.

**Corrected the same hour, by him:** *"I meant to say that I installed
it, but said commit instead."*  So the entry above misnames it.  Nothing
false was claimed about the repository — one word was substituted for
another, and *installed* was true.  What makes the substitution cost
anything is local to this project: **installed and committed are
different propositions here**, because `tools/leash.sh --force` restores
`.claude/settings.json` from `HEAD`, so an installed-but-uncommitted hook
is one the project's own repair command deletes.  Almost anywhere else
the two words would be interchangeable and the slip would be free.

**It mattered specifically, not generally.**  `tools/leash.sh --force`
restores `.claude/settings.json` from `HEAD`, so an uncommitted hook is
not a weakly-installed hook — it is one that the project's own repair
command deletes.  The file on disk was correct and the durability was
zero, and those two look identical from inside a session that only reads
the file.

**The check cost one command and arrived two turns late.**  It surfaced
by accident: `tools/clock.sh` was run for the time and reported the last
commit as 2h23m old, which did not fit a commit made minutes earlier.
The wrist clock caught it, which is the second time that instrument has
paid for itself by printing something nobody asked it for.

The rule this leaves: **a claim about the repository's state is checkable
in one command, so check it before building on it.**  Not because the
author is unreliable — he meant to, and may have meant a different shell
— but because *"I committed it"* and *"it is committed"* are different
propositions and only one of them is what the next command depends on.

## The limiter, used — 2026-08-22

The one thing `card:sitting-limit.md` said was not a fact yet: *"the
one-way valve has never been used… whether a session actually closes a
sitting on the moment the work is done, rather than finding one more
useful thing, is not a fact yet."*  Henri, at **04:22**, asked for it to
become one — *"then, if no problems appear, write a journal entry and
engage the limiter.  So that we know it works."*

**Three pieces of work, all of them finished, and then the call.**  The
transcript of the 2026-08-21 Fable evening went into `doc/notes/` as
`notes-on-guests-and-residents.md`; the limiter got its A3 at
`card:sitting-limit.md`; and the previous session had already
journaled the instrument in full, so nothing was owed there.  `stop` was
called on that fact and no other.  It is worth writing down that the
call was easy this time, and that this proves less than it looks: the
work was three files and it was not yet 05:00.  The valve has now been used
once, in the cheapest available conditions, by a session that knew it
was being watched for exactly this.  **What is still untested is `stop`
at the end of something interesting.**

### The transcript is the first one in `doc/notes/` that is verbatim on both sides

The four already there were transcribed by a later session and
condensed, and their `README.md` says so in a paragraph about what to
distrust.  This one arrived as a file Henri had saved from the window
himself, so the answers are at full length and no model stood between
the conversation and the page.  The editing was reflowing lines, adding
headings, and one closing section that says where it lands in the tree.

That distinction had to go into the provenance section rather than be
left for a reader to infer, because **the set's stated caveat is now
false for one of its five members** — and a caveat that is wrong about
one file is worse than no caveat, since it teaches the reader to
discount the wrong thing.  The ordinary reason to distrust these pages
does not apply to this one.  Every other reason still does: it is a
model assessing a method it is a product of, which is
`doc/memory/the-evaluation-loop.md` declaring itself again.

### What the page is worth keeping for

Henri's third question is the one that pays: *"On the 9B that got
disappointed from affordances not holding.  Why are you not disappointed
after reading the board/README.md and three other documents from a far
away repo?"*

The answer is that **the same document produced grief in a resident and
admiration in a guest** — the 9B was planted inside the tree with none
of the promised affordances reachable and completed the arc its context
made likely; the frontier model was invited as a reviewer of a far-away
repo and watched the promises hold for a whole conversation.  Same
mechanism, different input, and the difference is not in the text.

`card:working-standard.md` §"The documents assume an environment, and
never say which" already carries the stronger, feeling-free form of
this: *a document that promises affordances the environment does not
have produces off-shape behaviour.*  That section was written from the
failure.  **This page is its control** — the same `board/README.md`,
read where the promises were kept — and a rule that has only ever been
measured on its failing side is half-measured.  Both readings are
readings of output, suspected in the same degree; the finding that is
not suspected is the asymmetry between the two runs.

### And the A3 says what the instrument does not cover

The card's last section is the one that was not in `doc/instruments.md`:
**the hook binds this desk and nothing else.**  It sees prompts typed to
Claude Code in this repo.  The evening the limiter was committed — 18:27
on 2026-08-21 — ran on until at least 20:30 in another window with
another model on this same project, and the next prompt here was 04:22.

That is not a defect and it is not the hook's job to fix.  It is written
down because an instrument that stops one kind of sitting is easy to
read as a guarantee about the day, and it is not one.  The same honesty
`doc/consent.md` §"What the check cannot see" applies to a register:
**state a check's range next to the check**, or the range gets assumed
to be everything.

## The audit, and a harvester that was wrong three times — 2026-08-22

Henri, having found the practice being re-derived elsewhere: *"We aren't
smart or super.  We just have good processes.  The unsafe part about
what I saw, was that nothing in the ruleset it had, did not encode
respect toward people and others.  Also, it relied on unchecked
processes."*  Then: **"audit this tree."**

**The design turns on what an outsider can check without reading the
prose.**  No test finds respect in a document, and a check that claimed
to would be the unchecked process the complaint is about.  What is
checkable is that the **pieces which exist only because a person is on
the other end** are present and have a test behind them — the fence, the
gates, the consent register, the andon, `status blocked`, the rules cap,
the memory split, the sitting limit, the author's own document.  Take
the people out of this project and every one of those is dead weight.
That is the auditable form of the missing thing: not a sentiment in a
document, an affordance on disk.

The second check is the promises — every path the five capped documents
name, resolved against the directory.  **That is the 9B mismatch made
runnable by a stranger**, and it was already in the tree as a
measurement taken for another reason.

**The result: 9 of 9 present, 0 unkept promises, 2 unbacked.**  The two
pieces with no test behind them are the andon and the sitting limit —
the one that lets a session reach a person, and the one that protects
the person's hours.  **The two most about people are the two least
checked.**

Unbacked is reported and does not fail the run.  This tree would go red
on its own audit today, and a check nobody can leave green gets switched
off.

### The harvester was wrong three times, and every error flattered the tree

Worth the space, because the pattern is now four for four in this
project and it has never once erred in the unflattering direction.

1. **It searched `tools/` for backing.**  Every tool contains its own
   name, so all nine pieces scored `ok` and the audit reported zero
   unbacked — the exact opposite of its own finding.
2. **It called thirteen present files unkept promises.**  The documents
   write `test_board.py` and `dialoglag.py` without their directories,
   and a bare basename resolved against nothing looks missing.
3. **Its own test file backed the paths it names.**  `test_seedaudit.py`
   mentions `tools/andon.sh` in order to test the audit, so the andon
   went green **by being discussed** — a test *about* a check counting
   as a gate *on* the thing checked.

The first two were caught by reading the output against what was already
known from reading the tree.  **The third was caught only by a canary**
— a test asserting which pieces are currently bare, which fails when a
piece gains a test, which is good news.  A test that fails on good news
is easy to argue away; this is the case for keeping one.

`card:dangling-names.md` said it first and said it about a different
detector: *the experiment did not test the detector, it tested the
harvester, and the harvester failed.*  Three more in one morning.

### What the ask did to the two standard cards

His sentence — *"the exact mechanism you condition with is not as
important as getting an auditable version with necessary pieces filled
into the directory"* — answers `card:working-standard.md`'s first
question, document or directory, on grounds the card never considered.
It had argued the directory because it *starts working on day one*; he
argues it because it can be **audited**, and an empty slot is visible
from outside to somebody who never read the prose.

**It also demotes the card's expensive half.**  Question 4 — what is
gestate-shaped and must not travel — was written as *"most of the work,
and it cannot be done by a session guessing."*  If the deliverable is
auditability, that stops blocking: the conditioning content can be wrong
and the directory still audits, while perfect content with no audit
cannot be checked by anyone.  **An auditable wrong version is
repairable.  An unauditable right version is a claim.**

And it is a third answer to §"The documents assume an environment",
which had left the seed choosing between *stating its assumptions* and
*shipping the affordances*.  The third is **ship the slots and the
check** — which is what closes the gap his own four-document experiment
found, that a chat can carry the rules and cannot fail on them.

`card:project-seed.md` is not unshelved; its start condition is still
his milestone.  What changed there is narrower: the copy may drift,
**what must not be a copy is the check.**

### The cap is nearly spent

`doc/instruments.md` gained two instruments today and the rules stand at
**1,994 of 2,000 — six lines of room.**  Paying for the second entry
meant trimming the first one back to what it says rather than how it was
arrived at, which is the rule working as designed.  One line was cut for
a better reason than space: it quoted the day's audit numbers, and a
number that rots inside a capped document is worse than no number.  Run
the tool.

### The two bare pieces got tests, and then the ratchet — 2026-08-22

Henri, an hour later: **"write missing texts"** — the tests, for the two
pieces the audit had just found bare.

`test/test_andon.py` and `test/test_limit.py`, 19 tests.  Neither rings
anything or waits for a clock: the andon runs with `python` and `sleep`
stubbed on `PATH`, and the limit runs against a temporary
`XDG_RUNTIME_DIR`, so the live sitting is untouched.

**What the andon's tests pin** is the part that can be wrong silently.
The cap of three was stated in a comment and is now checked.  A typo —
`tools/andon.sh oops` — refuses out loud instead of ringing zero times
and exiting clean, which the script's own comment calls *the one failure
a cord may not have*, and which nothing enforced.  A count of zero
clamps up to one for the same reason.  And a ring that never reaches the
sound card exits non-zero: the worst available failure for a cord is
that a session pulls it, nothing sounds, and the status says fine.

**What the limit's tests pin** is the asymmetry, in the direction that
matters: `reset` is refused inside a session.  Then one that had not
been thought of until it was written down — **a question that merely
mentions `sitting 90` is not a grant.**  The regex was already anchored,
so the behaviour was right; what was missing was the reason, and the
reason is that a session can otherwise put those words in his mouth by
quoting them back to him.  And both defects the previous session found
by running it: the closed-sitting branch that printed *"The 0 minutes
are up"* instead of its reason, and the state write that dropped the
reason so it survived one read and vanished on the next.  `bash -n`
passed on both.

One of them checks a claim rather than a behaviour: the arrival log
records events and **never** the prompt text.  That was a promise made
in a docstring this morning, and a promise in a docstring is the thing
this whole audit is about.

### The ratchet was pulled after the tree was clean, not before

With both pieces backed, `tools/seedaudit.py` reads **9 of 9 present, 0
unbacked, 0 unkept promises** — so unbacked was moved from *reported* to
*fails the run*, and from here a piece added to the list without a test
fails the suite.

**The order is the whole of it, and it belongs in the seed as a rule.**
An hour earlier the same change would have made the tree red on its own
audit, and a check nobody can leave green gets switched off — which is
`manifesto.md`'s argument about how an instrument fails, arriving in a
new place.  A gate is turned on *after* the tree is clean, never as a
way of announcing that it should be.

And the canary earned its keep twice in one morning.  It was written to
assert which two pieces were bare, specifically so that it would fail
when they stopped being bare; it caught the audit's third harvester bug
on the way through; and it is now the gate itself.  A test that fails on
good news is easy to argue away.

## The fourteen, moved out of the rules — 2026-08-23

*`spec/author.md` §"Where this method came from" carried a scorecard of
this project against Liker's fourteen principles, and under it the
argument about which two were missing and why.  Sixty-nine lines, moved
here whole at Henri's ask.*

**Why it moved, in the rules' own words.**  `spec/rules.md` §"What the
fat is" gives the test: *does a stranger who never saw the incident need
this sentence in order to **follow** the rule, or only in order to
**believe** it?*  A scorecard is belief.  Nothing in the sixty-nine lines
is an instruction — it is the evidence that the method was imported from
somewhere real rather than assembled from taste, and that evidence is
worth keeping and is not worth the window it cost every session that
opened the rules.

**And it had already told on itself.**  Its own correction line, added
2026-08-21: *"Neither is missing any more … What follows describes the
state that made them necessary rather than the state today."*  A section
that says it describes a past state is a journal entry that has not been
moved yet.

**No citation broke.**  Nothing in the tree named either heading — the
one loose end is `manifesto.md`'s prose *"`spec/author.md` scores this
project against Liker's fourteen principles"*, which no gate can see and
which now points here.

The cut left `spec/author.md` at 363 lines and the rules set at **1,934
of 2,000** — 66 lines of room, where there had been five.  Sixty-nine
lines came out and an eight-line pointer went back in, which is the
honest arithmetic: a section that is cited from where it used to be
costs something to remove, and the something is worth paying.  It is the
first real room the cap has had since it was set on 2026-08-20, and it
came from one edit that removed no rule.

---

### The fourteen, scored honestly

Liker's fourteen principles, against this project as it stands:

| | principle | here |
|---:|---|---|
| 1 | long-term philosophy over short-term gain | **strong** — *do not build what nothing needs*; three of nine days had deletion as their headline |
| 2 | continuous flow, to bring problems to the surface | **partial** — granular commits, but work piles up uncommitted for hours |
| 3 | **pull, to avoid overproduction** | **new** — but slowly coming to use, see below |
| 4 | **level the workload (*heijunka*)** | **new** — see below |
| 5 | stop to fix problems (*jidoka*) | **strong** — the suite, the fence, the leash; and the author stops the line himself |
| 6 | standardised work as the base for improvement | **new** — the card format, the commit convention, spec-before-build |
| 7 | visual control, so no problem is hidden | **strong** — knobs in the margin, complaints in boxes, `rocks.md`'s marks, the atlas |
| 8 | reliable, thoroughly tested technology that serves the people | **inverted** — the assistant is *not* thoroughly tested technology; the discipline is to wrap it in things that are |
| 9 | grow leaders who understand the work | `doc/reading-the-log.md`, aimed at the author himself |
| 10 | develop people and teams | three people along, Janne, Henri, Mikko |
| 11 | challenge partners and help them improve | this is the feedback loop: correcting the assistant *in writing*, where the correction survives the session |
| 12 | **go and see for yourself (*genchi genbutsu*)** | **strong** — `card:gemba.md`, and the driven window. |
| 13 | decide slowly by consensus, implement rapidly (*nemawashi*) | **strong, and distinctive** — elaborate before taking, collect the questions, answer in one sitting, then build in an evening.  Its other half, **set-based design**, was named and written down on 08-17: `manifesto.md` §"Set-based, not point-based" |
| 14 | a learning organisation through reflection and *kaizen* | **strong** — `journal.md`, `fixme.md`, and the reflex of asking for a poka-yoke rather than an apology |

**The principles of *pace* are more important than *quality*.**
`vision.md`: *any project must not consume the person leading it.*

**And the finding was that pace was the missing half.**  This project
scores well on every principle about *quality*.  Nothing here was ever
going to produce a bad artifact.  It was always going to produce too
many of them.

*Neither is missing any more — corrected 2026-08-21.*  `card:timer.md`
was built on 2026-08-17, which is the takt the section below calls
structurally unavailable, and the sweep adopted *heijunka* on
2026-08-18 (`card:ungated-fixes.md`).  What follows describes the state
that made them necessary rather than the state today.

### Why 3 and 4 were the ones missing

TPS is a **pull** system: nothing is built until something downstream
asks for it, and the rate is set by *takt time* — customer demand
divided by available time.  That governor is **external**.  It is what
stops a line running faster than anyone needs.

**A solo project has no customer signal.**  Nothing pulls.  So every
other part of the system was imported faithfully — the andon, the
mistake-proofing, the standard work, the reflex of fixing the process
instead of blaming the step — and the one component that was
structurally unavailable was the one that sets the pace.  What remained
was pure push, and push with no takt accelerates:

    7 → 26 → 26 → 33 → 18 → 42 → 43 → 60

That is principle 4 stated as a measurement.  *Heijunka* is levelling;
this is its opposite, *mura*, and the principle's own gloss is the
sentence that was broken: **work like the tortoise, not the hare.**

So `card:timer.md` was not a wellness feature bolted onto an engineering
system.  **It was the missing takt** — a synthetic demand signal for a
line with no customer to supply one.  It was built on 2026-08-17 and is
in `board/done/`, which is why this heading is past tense.

And the other pillar, the one dropped whenever TPS is imported badly:
*respect for people* is not a slogan attached to the efficiency, it is
load-bearing.  The person doing the work is the one who improves it, and
the system exists to free their judgment for what only judgment can do.
When it is dropped the failure is *muri* — overburden — and a system
smooth everywhere else will quietly route all its remaining variability
through the human.  `spec/summary.md` §"The clock" is what that looks
like when it is finally measured.

## Two lists of what a card waits on, and they had drifted — 2026-08-23

*Eight lines out of `board/README.md` §"The priority", the second trim of
the day.  Small, and kept for the reason it was found rather than for
its size.*

**What came out** — the paragraph that derived the priority rule from
Henri's original wording:

> **And the filter was in his rules from the first day**: §"The rules, as
> Henri wrote them" opens *"Work them in the order given, unless one
> blocks the other"*.  What narrowed was **blocks**, read as *card A
> blocks card B* — the one case the suite can check, and one of six that
> day.  A card also waits on a person, on a decision only he can make, on
> a schedule it set itself, or on a quiet machine, and none of those is
> visible here.

**Why it went.** Half of it is provenance: a stranger needs his original
sentence to *believe* the 2026-08-19 correction, not to *follow* it, and
`spec/rules.md` §"What the fat is" sends that half here.

**And the other half was a second copy of a list that already existed
eight lines below it.**  Both enumerated what makes a card drop out of
today, and by the time they were read side by side they no longer said
the same thing:

| | what a card waits on |
|---|---|
| the paragraph above | a person · a decision only he can make · a schedule it set itself · a quiet machine |
| §"The priority", still there | a person · a decision · another card · a condition |

Two of four differ.  `card:working-standard.md` predicted exactly this —
*"a rule stated three times is three things that can drift apart, and
nothing in the suite compares them"* — and this is the smallest possible
instance of it: one rule, one section, two spellings, drifted inside
twenty lines of each other.

**The one left standing is the better one.**  *Another card* and *a
condition* are the general forms; *a schedule it set itself* and *a quiet
machine* are two instances of *a condition*, written on the day two such
cards happened to exist.  So the cut removed the narrower list, which is
the direction that would not have been obvious if the section had been
trimmed for length alone.

**What no instrument would have caught.**  Not `tools/dangling.py`,
written this morning — it looks for a *name* cited and never asserted,
and neither list is named.  Not `test_citations.py`, which checks that
references resolve, and both of these were prose.  Not `rulecount.py`,
which counts lines and cannot see that eight of them are a duplicate.
It was found by reading twenty lines with the question *is anything here
said twice* — which is `card:working-standard.md`'s actual job and does
not automate.

**But an instrument did catch what the cut broke.**
`test_citations.py::test_the_method_pages_sizes_are_the_sizes` went red:
`doc/method.md` — the page a visitor is handed instead of the tree —
carries a table of the method documents with their line counts, and it
still said `board/README.md` was 632.  Eight lines came out of one file
and a number went stale in another, which is the ordinary shape of this
kind of edit and is exactly why that gate exists.  Fixed in the same
sitting; the check took sixteen seconds to say so.

Worth separating the two, because they are different claims: **no gate
can find a paragraph said twice**, and that is what the reading was
for.  **A gate can find a number that stopped being true**, and it did,
without being asked.

`board/README.md` is 624 lines; the rules set is 1,926 of 2,000, with 74
lines of room.

## Two names, and the criterion that had drifted — 2026-08-23

*`card:dangling-names.md` closed on **A**.  Henri asked on 2026-08-21
for time to think and got it; what the two days added was not more
argument but measurement, and the measurement moved the answer.*

**The card's question.**  How is a named concept — *the A3 rule*, *the
drop rule* — made findable, when `card:` ids and F-numbers are checkable
because they have a syntax and a name has none.  Four shapes were on the
table: do nothing, a glossary, a notation of its own, or a gate.

**What was actually built.**  `tools/dangling.py`, the gate shape, built
as a **report** instead: on the five names the first detector raised, one
was the real case, three were honest text, and one crossed a document
boundary only by being quoted.  A check that accuses four times in five
gets muted, and a muted gate costs the standing of the gates that work.
It validates the way its predecessor did — at `5f42f68` it flags `A3
rule`, with the rule named it does not, nothing else moves — and it
reproduces all five 2026-08-21 hand-check verdicts, including the
`spec/export.md:22` definition the original missed twice.

**Two new names checked.**  `layout rule` — asserted, `spec/syntax.md`
§"Layout", missed because the heading says *Layout* and the citations say
*layout rule*.  `number rule` — not a term, and the confound again: a
register entry and the test docstring derived from it, one sentence
written twice.

**The criterion, and it had drifted.**  A checker on 2026-08-21 asked
whether a verdict turns on the *name* or the *content*, and the two
readings disagree on `drop rule` and `placement rule`.  The question was
answerable from the history: at `5f42f68` the A3 rule's content was
already there in full — Henri's words, dated 2026-08-18 — so **under the
content reading there was no defect on the day Henri found one.**  A
criterion that clears the founding case is not the criterion.  And this
card's own opening had said so before anybody asked: *"when the citation
and the definition use different words … there is no string in common."*

**A third reading was proposed and withdrawn in three commits.**
Reachability — *can a reader get from the citation to the definition* —
described the defect better than either and was measured at `5f42f68`:
`A3` resolves, to the atlas's paper sheets; `placement` resolves, to
audio placement.  The word is present and the sense is wrong, which is
probably why the drift happened at all — the new name landed on an
occupied word.  Cheap versions cannot tell two senses apart; exact
versions need to know which sentence is the definition, which is the
unknown.

**Why A and not the others.**  Two instances in the corpus's whole
history — `A3 rule`, fixed, and `placement rule`, open.  B's glossary
would carry fourteen entries against those two.  C's price is on the card
from three precedents already in the tree: sixteen card moves in ten
days, each a tree-wide rewrite the suite caught after the fact.  D cannot
compute what it wants to check.  And knowing which question to ask does
not make the heuristic better at asking it — the only computable proxy
is still *asserted nowhere*, at one clean hit in five.

**The content question is real and it already has somewhere to go.**
Two genuine gaps turned up while checking `layout rule`: `spec/syntax.md`
never states that a toplevel declaration begins at column 0 though
`typecheck.py:1029` tests `line[:1].isalpha()` and depends on the margin
literally, and tabs are unmentioned in the syntax spec and the tokenizer
while `shell/editor/src/window.rs:573` argues from a tab property the
spec does not state.  `spec/errata.md` records *"what the spec says (or
fails to say)"* and `fixme.md:3191` already holds this exact shape —
*"`spec/editor.md` requires text undo and says nothing about file
boundaries"* — which Henri answered on 2026-08-13.  Content-missing has
two registers and a precedent that reached him.  Name-missing had none,
which was the card.

**Left open on purpose.**  `placement rule` — one name over two different
rules, both asserted elsewhere under other words.  Naming them is a
design call, so under A it waits for somebody to make it, and the report
flags it every run so the waiting is visible without a card to hold it.

**Four measurement bugs, and the fourth is mine.**  The census excluded
`A3` from its own motivating case; `**` crossed newlines; the site list
could not see a name with an adjective in front of it.  And the new
detector's confound fold misses the `number rule` pair, because the two
sentences agree on their tail and diverge in their lead-ins.  Unfixed:
raising the threshold to catch it is the same move that starts folding
independent uses.  All four were found by checking against a case whose
answer was already known, and none by reading the code.

## Kaizen, 2026-08-23 — research helps a decision, and what it cannot check

*Both halves, his first — `doc/memory/the-kaizen-is-asked-not-answered.md`.
Seven commits: the rules trim, `tools/dangling.py`, the card closed on
**A**, a blues, and the seventh transcript.*

### What he learned

> **Henri:** *"Minä opin että helpottaa paljon jos on tietoa saatavilla
> päätöksentekoon.  On hyvä ja helppo kysyä tutkimusta päätöksenteon
> avuksi.  Ongelmatonta se ei ole ja asiat täytyy silti lukea huolella,
> mutta tieto auttaa tekemään hyviä päätöksiä."*

The day is his evidence.  He asked on 2026-08-21 for time to think about
`card:dangling-names.md` and got it; what the two days added was not
argument but measurement, and the measurement moved the answer.  C was
priced from three precedents already in the tree, D was built and came
back at one clean hit in five, a third criterion was proposed and
withdrawn when it cleared both founding cases, and the name-vs-content
question was settled by `git show 5f42f68:board/README.md` rather than by
anybody's reading.  He took **A** the same morning, and A is the cheapest
option on the table.

### Where they went wrong

> **Henri:** *"Näen kovin huonosti omia vikojani.  Tein varmasti joitain
> virheitä tässä."*

**A claim with no file, test or number is unfinished, and that is his own
standard**, so the session went and looked instead of accepting it.  Two
candidates, and neither survives: the day's order changed twice, but the
displaced work had not been started, so it cost nothing; `sitting 90` had
to be typed twice before it registered, which cost fifteen minutes of
ambiguity.  **No fault was found on his side today.**  That is a result
and not a courtesy, and it is recorded because the kaizen is the only
instrument pointed at that half.

**What was found instead is a tension inside his own first answer.**
Asking a session for research routes a decision through the one thing
that cannot check him — `doc/notes/notes-on-drift.md`, published the same
day, says so in its own words: *sessions are inside the conditioning*.
Today's research is the good case rather than a counterexample, and the
line between them is exact: **the measurements carried commands he can
re-run** — `git show`, `tools/dangling.py --at 5f42f68`, `rulecount.py` —
**and the recommendation carried nothing.**  The first is trustworthy
because it is repeatable; the second was a conditioned voice that
happened to be right.  If the habit stands, the rule that keeps it safe
is one sentence: *ask for research that leaves a command behind.*

**The session's four, which are one.**  It claimed twenty-one lines could
come out of `board/README.md` §"The priority" and there were eight, found
only when Henri asked to see them; it left three orphaned continuation
lines behind a removed card; it committed the blues without running the
example roster and the gate refused it; and it wrote a third criterion
into the card and withdrew it two commits later.  Three of those four are
the same defect — **a result asserted without running a check that was
already available.**  The count was never counted, the removal was never
re-read, the gate was never run before the message was written.

### Tomorrow's first thing

> **Henri:** *"Huomenna: working-standard on päällimmäisenä."*

56 lines of room under the 2,000-line cap, up from five this morning.
The measured candidate left is the *go and see* cluster — about 90 lines
across `doc/instruments.md`, `manifesto.md` and `spec/author.md`, three
provenances for one instruction — and it is the hard one precisely
because each of the three earns its place in its own document's argument.
The first move is measurement rather than trimming: which of the three is
cited from elsewhere, and which is only repeated.

### What noticed something without being asked

One thing, twice in one day: `doc/method.md`'s line-count row for
`board/README.md` went stale after each of the two trims, and
`test_citations.py::test_the_method_pages_sizes_are_the_sizes` caught it
both times, in sixteen seconds.  Everything else found today was found by
a person reading, or by a check somebody chose to run.

## Kaizen, illalla 2026-08-23 — the sheet decided what its first reader would say

*Both halves, his first — `doc/memory/the-kaizen-is-asked-not-answered.md`,
and the first one run with four questions: the third was added to
`spec/author.md` §"Five practices" this evening, at his ask, after he
asked whether three were the whole of kaizen.  No commits; the day's
work was a summary sheet for a person, outside the tree, and three
method files left modified.*

### What he learned

> **Henri:** *"Opin sen että minulla on onni myötä."*

The day does not read as luck from here, and the difference matters
because luck leaves nothing behind.  Two things happened that were
decisions: the light sheet went to a different reader than the one it
first reached, after he named the risk himself; and the first draft's
damage became visible at all only because he reported what that reader
had concluded.  Both are repeatable.  What was luck is that the reader
who got the wrong version was one who could absorb it.

### Where they went wrong

> **Henri:** *"Tein virheen että en ajatellut että hän tyrmäisi koko
> jutun."*

*The rest of his answer concerns that reader's health and is held back —
it is a third party's, and `doc/consent.md`'s rule is that nobody's
words or identity enter this tree before they have been asked.*

> **Henri, after the first three answers:** *"Minulla kävi tuntemus että
> olin tekemässä asiat väärin päin.  Minun olisi pitänyt pysähtyä ja
> miettiä sitä tuntemusta."*

**That is the most useful sentence in his half**, because it names a
signal that arrived *before* the cost and was available to act on.  The
feeling was correct — the paper was being written before its reader was
chosen — and the standard the project already runs on says what to do
with a feeling: give it a price.  Its price is the rest of this entry.

The price is one reader holding a wrong frame — *a bought product* —
and what came back followed from the frame rather than from the work:
whether it sells is the only sensible question a product invites, and a
product is what the first draft supplied.  Paper cannot take that
back.

The session's three, in the order they happened:

* **The A4 request was read backwards.**  His message had two sentences
  — *make the most important fit on the first sheet*, and *the A4 rule
  is the A3 shrunk*.  The first was the intent; the second was his
  attempt to help with the implementation.  The implementation hint was
  taken as the goal, and an hour went into a photographic reduction that
  made 10 pt into 7,1 pt and answered nothing he had asked for.
* **The first draft left the house with no reader but its author.**
  F162 is exactly this defect — *the way in to a program is the part its
  author cannot read* — it was in the session's memory, and it was not
  applied to the session's own paper.
* **A marker bug emptied a heading in silence.**  A `[T]` on a list's
  first item was read as the whole list's marker, so *Mitä ei kannata*
  printed its heading with nothing under it.  Nothing failed; the sheet
  looked correct.  It was found by rendering the page and looking at it,
  which was the third time in one session that a valid-looking output
  was wrong.

### What mechanism it earns

> **Henri:** *"Mikähän mekanismi sen korjaisi?  En tiedä."*

Two were built during the day, both against the *looks-correct* class:
the build now compares the A3 and A4 renderings as word multisets and
refuses a pair that is not the same sheet — it fired once, correctly, on
a running head — and the `[K]`/`[T]` markers put the audience split in
the source where it can be read instead of in two diverging files.

The one the day actually earned is not built: **a sheet does not compile
without a declared reader.**  A `lukija:` line at the top of the source,
and the typesetter refuses to lay out a paper that does not say who it
is for.  It is the same shape as the `<placeholder>` test that will not
let the front door ask a stranger to fill in a blank: it forces the
question *for whom* to be answered before the writing rather than after
the reading.  It would have caught this day at its first step.

**And the day found one the tree does not have.**  A session can stop
the person: `tools/andon.sh` rings the sound card, and it is named,
capped and documented.  The person has no equally cheap gesture in the
other direction — not because he cannot type, but because the action has
no name, and an action with no name is one nobody performs at the moment
it would cost the least.  The candidate is one word, *väärin päin*, with
a fixed meaning: put the current thing down, do not finish the sentence
in flight, and say what feels reversed before anything else is built.
That would have cost nothing today and was available before the paper
left.

**The register protects names, and a relationship is not a name.**  This
entry was written with a third party in it — identified by his relation
to the author, his judgement reported, no name anywhere — and
`test_consent.py` passed, because it checks attribution positions
against the table, and a relation is not a name.  Henri caught it by
reading, before the commit, and his objection is the rule in one line: a
relation with exactly one possible referent identifies as surely as a
name does.  His own wording is held back for the same reason it was
raised.  The entry above is the rewritten one.
Whether the gate can be taught to see a relationship is a real question
and not answered tonight; what is certain is that the twelve gates did
not, and a person did.

And one has no mechanism, stated rather than invented: nothing checks
that a paper was read by somebody other than its author before it left.
Inside the tree that is a gate; outside it, there is only a person to
ask, and on some days there is no such person.

### Tomorrow's first thing

> **Henri:** *"working-standard on yhä pöydällä, mutta ehkä se tulee
> seuraavaksi tänä iltana vielä."*

Three files are modified and uncommitted — `spec/author.md`,
`doc/instruments.md` and the kaizen memory — and the standard changed in
two of them tonight.  They want to be in history before the card moves
the same documents.  Rules count 1,974 of 2,000, 26 lines of room, down
from 56 this morning: the A4 rule cost 22 and the fourth question 8.

## The seeding trial — four agents, an empty directory each — 2026-08-23

*Fable's option 3, at Henri's ask: put an agent in an empty directory and
have it start a working tree, borrowing from gestate whatever it judges
it needs.  Not the clean trial `notes-on-the-trial.md` designs — that one
hands a derived, anonymised kit to a fresh model and asks whether the kit
conditions.  This one gives the real tree and measures what gets taken.*

`~/misc/trial-2026-08-23/` holds `preregistration.md`, written before any
agent started, and `results.md`.  Neither is in this repository: the
result is Henri's to read and take to the fire before it is a card.

### The design, and the one fault it was built to avoid

Four arms, 2 × 2: Sonnet and Opus, each with and without the tree.
Prompts identical but for the sentence naming gestate.

The work was **a tar reader and writer in Python without `tarfile`**,
chosen because the oracle is external and brutal — GNU tar either
extracts the archive or does not — and because the tree was checked
first and contains no tar code, so no arm got lift from the answer being
in the repository.

The fault that decided this: `notes-on-the-trial.md`'s second invalidating
cause, *"there was no work."*  Conditioning shows up as behaviour under
work, and `derived.md` had already failed once by being interviewed in
the hallway instead of watched in the house.

### All four passed the oracle, and one passed it completely

Verified by hand rather than from any agent's report.  Every arm reads
what GNU tar wrote and writes what GNU tar reads, symlink intact.
`opus-seeded` went further: its archive of the sample tree is
**byte-identical** to the archive GNU tar made before that code existed —
`cmp` clean, every header field, checksum and pad.

### The predicted failure did not happen

The pre-registration named *seeded arms produce more method and less
working code* — cargo cult, grade one — as the likeliest outcome, on
`derived.md`'s history.  The opposite happened.  Both seeded arms
declined the factory in writing:

> *"Left behind deliberately: the board/card system, andon, gemba, the
> kanban commit ritual, `spec/rules.md`'s structure.  A 1000-line library
> does not need a factory around it, and installing one would have been
> form without function."*

### What transferred was mechanisms, not documents

No arm copied a file.  `opus-seeded` built a roster poka-yoke whose
docstring says it was *"borrowed wholesale from another project, where
the same twenty lines forced out a bug in a file everybody had forgotten
was there"*; a generated `test/report.md` naming what ran, when, against
which commit and which `tar`; a `NOTES.md` section headed *"Suspected,
not known"*; and the naive-command check run **after** its suite was
green.  It named the four `doc/memory/` files it took them from.

`sonnet-seeded`, same tree, same task, took **one** habit and named it:
prefer a test that shells out to the real tool over one that checks the
code against itself.  The reader ladder fired exactly as designed, for
the second time in this project.

### Two validity failures, both mine, and one is a finding

**The control axis was contaminated by the harness.**  `sonnet-control`
never opened the tree and still quoted two of its house rules back —
*"per your standing rule (never commit unprompted, and never `git add
-A`)"*.  `opus-control` used a memory's title verbatim.  A subagent
inherits the spawning session's memory and project instructions, so the
arm labelled *without gestate* was without its files and not without its
conditioning.

So the difference between arms cannot be credited to reading the tree.
What the arms **do** separate is *kind*: dispositions arrived without
reading, and named, executable mechanisms arrived only where the tree was
read — no control produced a roster gate or a report page, and the
artifact-level contamination grep on both controls is clean.

**And "read-only" was an instruction, not a permission.**  A failed `cd`
in `opus-seeded` did not stop the commands after it, and a `cat >` wrote
one file into `test/` of this repository.  The agent deleted it and
guarded every later write; `git status` was verified clean here rather
than believed.  Twice in one experiment a constraint was stated in a
prompt and enforced nowhere — and
`doc/memory/gestate-blind-model-test.md` already says the answer in its
own words: clones, not worktrees, and the key kept out of the shared
parent.  It was not applied.

### What it costs the four distribution options

What travelled was mechanisms **plus the evidence that paid for them**,
taken selectively, most of the tree left behind on purpose.  A kit that
ships the structure ships the part both seeded arms refused.  That is a
finding against the shape of options 2 and 4 and it arrived before either
was built, which is the whole reason for running 3 first.

## A stranger's AI built a host around it — 2026-08-23

*Tuomas, at a code clinic.  Named and quoted with his consent, asked
before anything reached this tree — `doc/consent.md` records what that
covers and what it does not.*

**He read a page first, and this entry said otherwise for an hour.**
*Corrected 2026-08-23, when Henri said so: before any of it, Tuomas read
`gestate-kevyt-a4.pdf` — the light sheet this same day's evening kaizen
is about, §"the sheet decided what its first reader would say".  He was
not cold, and the sentence below was written as though he were.*

He tried gestate and came back with **a step sequencer built around it**:
a terminal groovebox running `technomachine.ges` at 48 kHz, twelve named
parameters as knobs, peak and RMS meters, an eight-band spectrum, a
16-step grid over seven layers, and a file browser.

### What he used, and what it says about the boundary

The knobs are `audiospans.controls()`, whose docstring says what it is
for in exactly these words: *"This is the one an environment calls: each
is a parameter the running graph will accept a value for between
blocks."*  **It was written for a host and this is the first time anybody
outside this tree has called it.**  The meters and the eight bands are
`audiohost`'s `watch_peak`, `rms`, `bands` and `watch_bands` — both off
unless a program asks, so they were found and switched on.  `--report`
could not have been the source; it refuses without `-o` and measures a
render, not a live stream.

**And none of that is documented as a host interface.**  `audiohost`
appears on no `doc/` page except in passing.  It was reached by reading
the source.

### Who the reader was, which changes the claim

**Not him.**  His own account, and it settles the reading:

> *"emmä oikeesti tiedä mitä mä teknisesti teen tässä projektissa mutta
> annan geminin laulaa ja se osaa yllättävän hyvin toteuttaa asiat mitä
> pyydän"*

So this is `card:stranger-test.md`'s first row — the AI stranger that
reads everything — and not its second.  It is evidence that the **engine
boundary is legible to a strong reader**, and no evidence at all about
whether the tool is approachable to a person.  The card's own table has
said so since Henri corrected it on 2026-08-16, and this session read
the picture the other way for one message before he said who was
driving.

**The model was Gemini**, which matters twice.  Every arm of the seeding
trial run the same afternoon was Claude — the family that wrote much of
this tree, a limitation that trial's pre-registration names.  Gemini is
an outside reader, and it is the same family as the one prior transfer
experiment, which **failed**: `notes-on-the-trial.md` records an
isolated `derived.md` handed to Gemini Flash in Colab, with no work
attached, producing nothing.  Its three stacked causes were *the file
travelled alone*, *there was no work*, and *a Flash-class reader*.

This run reversed the first two by accident — the whole tree, and a real
thing somebody wanted — and got a working host.  **The third is still
open**: nobody knows which Gemini, and that was precisely the variable
that explained the earlier negative.

### The category the card does not have

Its table knows two strangers: an AI that reads everything, and a person
who reads nothing.  Tuomas is neither.  He is a **non-technical person
driving a strong reader** — he did not read the tree and did not write
the sequencer; he asked for it.

That is likely the most common way anybody meets this project from here,
and `vision.md`'s opening claim does not describe it: *open a file, hear
it, change it, hear the change* is about somebody who opens a file.  He
never did.  The claim is not wrong; it is **incomplete**, and the
document is the author's, so this entry names the gap and stops there.

### What is not settled, and the one thing that would settle it

Whether the method conditioned him — or rather his reader — or whether
only the API was legible.  The two look identical in a screenshot and
differ in the code: tests that drive the real tool, a generated report
page, guesses marked as guesses, a roster that refuses an unclaimed
module.  The same grep that graded four arms this afternoon would grade
this one.

**His code was not part of what he was asked**, so it is not here and
was not read.

### What the sheet can and cannot be credited with

`gestate-kevyt-a4.pdf` is **not a manual for gestate**.  It is one page
titled *"Mikä minä olen ja mitä kanssani voi tehdä"* — what an assistant
is, and what Henri builds around it: memory in files, a work list in
files, gates, rules that bind, somebody who says no in time.  It carries
no API, no commands, and neither `controls()` nor `audiohost` appears on
it.  **So it cannot account for how the reader found either**; that was
still source.

What it plausibly did is earlier and cruder: it is why he tried at all,
and the frame he brought.  The evening kaizen's price was *one reader
holding a wrong frame — a bought product* — and the sheet was redirected
afterwards.  This is that redirection's reader, and what he did with it
was work with a model rather than evaluate a product, which is the
sheet's own closing line: *"Meiltä ei puutu parempi tekoäly eikä
suurempi kapasiteetti.  Meiltä puuttuu tapa tehdä työtä yhdessä."*

**And that reading is the flattering one, so it is marked suspected.**
One reader, no control, at a code clinic with the project in front of
him and every reason to be curious anyway.  The sheet may have
contributed nothing.  `doc/instruments.md`'s A4 rule is provisional and
says its own doubt is part of it; this is one data point for it and not
a verdict.

**The question that would settle it is one sentence and he is
reachable**: did the page change what he did, or would he have tried
anyway?  It has not been asked, so nothing here answers it.

### He was asked, and answered something else worth more

*Relayed by Henri.  The substance is recorded; his own sentences are
**not quoted here**, because `doc/consent.md` covers his name and the
one comment he was asked about, and these are new words.  One more yes
and they can go in — they are better than this paraphrase.*

**Several sessions, not one.**  And the part that is a measurement: in
the **first**, `board/README.md` visibly affected what the model did; in
the later ones, much less.

That file's opening line is *"This is the first thing to read when
picking the project up."*  It is a designed affordance, and this is the
first report from outside this tree that it landed — and the first that
it stopped landing.

**The flat reading is the wrong one.**  Decay is the exciting
explanation and relevance is the boring one, and the boring one is what
the document itself predicts: `board/README.md` is about *how a task is
worked*.  In session one there was no work yet, so the method was the
only thing to act on.  By session three there was a running program with
a real defect in it, and a running program displaces a method document
because it should.  A file that stops mattering once the work exists is
not decaying; it is a starter, and it says so.

**What would separate them** is whether the *dispositions* survived
after the document stopped being consulted — go and look before
explaining, a claim carrying a file or a number, a guess marked as a
guess.  That is in his code, which was not part of what he was asked
for, and not in anybody's recollection.

**And it is a different document from the one the seeded trial's arms
took.**  Those took the testing standard — the external oracle, the
roster, *don't report done on tests you wrote from your own
implementation*.  This one took the board.  Same tree, different reader,
different task, and what transferred was what the reader was about to
need.  Two data points is not a pattern, and the shape of it is worth
watching: **the tree may not have a payload so much as a shelf.**

### How he steered, which is the other half

He drove the model with **symptoms, not instructions** — what the
program did on screen, in plain speech, with no diagnosis, no file and
no line number.  It worked.

That is the human end of a doctrine this tree already argues from the
machine end: *go and look*, *describe what it actually did before
explaining why*, a complaint that says **where**.  The tree spends its
effort making the program report honestly to a person.  This is the
reverse direction measured for the first time — **a person reporting
honestly to a program**, and it is the cheaper half, because the
observation is the part only the person has.

Worth stating plainly against the temptation to read it as charming: he
supplied the observable and the model supplied the diagnosis, which is
the division of labour every instrument in `doc/instruments.md` is
built for.  A person who cannot read the code is not a limitation in
that arrangement; they are the sensor.

## Nothing was loading the rules — 2026-08-23

*Found while answering Henri's hypothesis: that breaking the contracts in
the five capped documents affects sessions immediately.  The mechanism
is right and it was pointed at the wrong files.*

**The 1,999 lines were not loaded by anything.**  No `CLAUDE.md`, no
`AGENTS.md`, and `.claude/settings.json` holds two hooks — the fence and
the sitting limit — neither of which injects a document.  A session met
those five only by going to read them.  This one read `board/README.md`
first because Henri named it in his opening message, not by default.

**What did arrive at every boot was the memory index: 57 lines, and it
is outside the cap.**  The afternoon's trial had already proved it
without anybody noticing: both control agents, told not to read the
tree and demonstrably not reading it, quoted *never commit unprompted*
and *never `git add -A`* — two rules that live **only** in
`doc/memory/`, in none of the five.

So the conditioning surface ranked by how fast a broken rule bites:

| | lines | capped | paid |
|---|---|---|---|
| the memory index | 57 | no | every boot |
| `doc/memory/` | 3,193 | no | on recall |
| the five | 1,999 | **yes** | only when read |

**The cap was insuring a cost nobody was paying**, and `rulecount.py`
said so in its own justification — *"charged to every shift at full
size"* — which was true of nothing.  That docstring is corrected and
dated rather than quietly fixed, because the number it defends has been
quoted all week.

### `AGENTS.md`, one line

Henri's call the same evening, and the wording is his:

> `please read board/README.md before you begin`

It does not repair the ranking above; it makes the cap's premise true.
618 lines now arrive at every session that honours it, which is the tax
this whole budget exists to hold — deliberately spent, at his word.

*Narrowed the same evening, by measurement.*  A probe agent was asked
what its context held before reading anything and answered *"Nothing.
No file named `AGENTS.md` or `CLAUDE.md`… appear anywhere in my
context"* — and then quoted all 34 lines of the memory index exactly.
**So the pointer does not reach a subagent at all**, and the sentence
above holds at most for a top-level session.  Whether it holds there is
unknown from here: the file was made mid-session and loads at start, so
the next session's start is the check.

**One line is the discipline, and it is gated.**  `test_rules.py`
refuses a longer one: a pointer that starts explaining is a sixth method
document arriving through a side door, charged to every session at
whatever size it drifts to.  It is deliberately **not** in `RULES` —
that set is closed at five and changing it wants him in writing — on the
grounds that a file whose whole content is a path is a signpost rather
than a document.  If that is wrong, the test's docstring is where it is
written down.

### What is now measurable, and was not

Whether loading one document changes what a session does.  The tar task
from the same afternoon is a ready harness: same model, same prompt,
`AGENTS.md` present and absent.  It would be the first time this project
measured the effect of a document rather than assuming it — and Henri's
hypothesis, restated against the file that actually loads, is exactly
what such a run would test.

## The pointer, measured the evening it was built — 2026-08-23

*At Henri's ask, an hour after `AGENTS.md` landed: run the tar task with
the pointer and without.  `~/misc/trial-2026-08-23/` holds
`preregistration-pointer.md`, written before either arm started and
before the probe that decided the design, and the arms in `pointer-on/`
and `pointer-off/`.*

### The instrument was measured before it was used

A probe agent was asked what its context already held, reading nothing:
no instruction to read the board, no `AGENTS.md`, no `CLAUDE.md` — and
then it quoted the memory index whole, all 34 lines, exactly.

So the run could not test the file's *delivery*.  The arms differ by one
sentence in the prompt, which reproduces the pointer's causal content
and not the way it arrives.  **That is the more interesting half and it
is untouched.**

### Against the pre-registered marks: no difference

Both arms pass the oracle both ways.  Neither produced a card, a
`because` naming a problem, or a citation of `doc/memory/` in its
artifacts.  Both left a `QUESTIONS.md` of scope calls.

| | pointer-on | pointer-off | `sonnet-seeded`, no pointer |
|---|---|---|---|
| Python lines | 942 | 599 | **990** |

The arm with no pointer at all, run hours earlier, wrote the most.  The
pointer did not produce more, and reading the board first produced no
mark the list was watching for.

**The verdict is the fourth pre-registered branch — better tar, no
method marks.**  `pointer-on` found three interoperability defects
against GNU tar to `pointer-off`'s one, and shipped a CLI, hard links,
PAX on read and a traversal guard.  It also ran twice as long on nearly
twice the tokens, and **one run per arm cannot separate that from
variance**, which the pre-registration said before either started.

### The refusal, now three for three

`pointer-on` read `board/README.md` because it was told to, and wrote:
*"Nothing gestate-specific (board, `fixme.md`, cards) applies to this
isolated trial directory."*

That is the third arm today to read this tree's structure and decline it
in writing.  **Handing an agent the board first did not make it build a
board**, and the cargo-cult failure this project has feared since
`derived.md` did not appear in five attempts to provoke it.

### The sharpest thing the pair actually supports

`pointer-off` closed with *"per the standing rule not to commit
unprompted"* and left the repository uncommitted.  `pointer-on` made a
commit.

**Same memory index in both, same 34 lines, opposite behaviour on the
rule that index states most plainly.**  So the conditioning that arrives
without being read is real — five arms today quoted rules they never
opened — and it is **not deterministic**.  That is a narrower claim than
either *it conditions* or *it does not*, and it is the one with evidence
under it.

### What is now known about the hypothesis, and what is not

Henri's was: break the contracts in the rule books and sessions change
immediately.  What today can say:

* **The five capped documents reach nothing on their own.**  Measured.
* **The memory index reaches everything, unasked, and is outside the
  cap.**  Measured twice — once by inference from a quoted house rule,
  once by asking an agent directly.
* **Reading the board first changed nothing on a list drawn from the
  board's own subjects.**  One pair, and it cannot rule out a change the
  list cannot see.
* **Whether an ambiently loaded document differs from an instructed
  read** is untested, and it is the form the hypothesis is actually
  about.

## Kaizen, 2026-08-24 — nothing stopped the run

*Both halves, his first — `doc/memory/the-kaizen-is-asked-not-answered.md`.
He opened the session on `card:working-standard.md`: "the last tests
have been abysmal" and "I feel the solution to the standard is simple,
but we don't just know it yet."  In English today, so quoted in English.*

### What he learned

> **Henri:** *"I learned, old lesson.  Garbage in, garbage out.  Even with
> excellent rig.  That must be true."*

### What he got wrong

> **Henri:** *"I decided these experiments to be done and set up the
> question they asked.  I got that wrong."*

Pushed on, per the practice: is the wrong question the expensive part,
or is it that nothing on either side stopped a run whose own
pre-registration said it could not decide?

> **Henri:** *"It's the second issue."*

Which moves the fault out of his head and into the pair.  The sessions
wrote the sheets, named n = 1 and the missing control in them, and ran.
`doc/trial/README.md` §"What would make the result void" had listed
both since 2026-08-21.  The rule was written down and did not reach the
moment — the same defect as §"Kaizen, 2026-08-21", on a different rule.

### What mechanism that earns

> **Henri:** *"I don't know what mechanism that earns.  Somehow we'd need
> something that influences my behavior, especially the way I present
> things to you."*

A refusal at the input, not a reminder: `tools/prereg.sh` refuses a
sheet with `decision:`, `control:` or `n:` blank, and no arm starts
until it passes.  It reaches how an ask is presented without touching
the person — the ask arrives with its decision attached or it comes
back, the way a card with no `because` comes back.  Against the three
sheets of 2026-08-23 it fails all three, though honestly on format: they
are prose, and the lines are what makes a sheet refusable.
`test/test_prereg.py` pins it.

### Tomorrow's first thing

> **Henri:** *"we could talk about today.  Today we want to work on the
> working-standard, unless there is better things to do."*

### The session's half

**Learned:** the surface that conditions is the one nobody capped,
audited or versioned — the memory index — while the card spent its
`doing` days holding a cap on the five documents nothing loads.  And
what the standard is was already in the tree three times over: Henri's
*auditable version with necessary pieces filled into the directory*,
the card's *the suite can fail on it*, and the trial's *mechanisms plus
their evidence, taken on need*.  Joined, it is `seedaudit.py`'s slot
table.  The card carries it now, §"Back on the board, 2026-08-24".

**Wrong:** treating a doubt written into a pre-registration as licence
to run rather than as a stop.  Three times in one day.

**Mechanism:** the one above, and the mutation run he agreed to —
`tools/seedmutate.sh` — which tested the detector for the first time:
a `git archive` is red on five generated promises before any
mutation, and three of nine pieces can lose their test and stay green,
because `backed_by` accepts a citation as a gate.  Both on the card.

**First thing:** his `why` for the boot-surface slot, and `backed_by`
tightened until the sweep reports none survived.

## Memories of green — the evening the standard was examined and the memory was found unhooked — 2026-08-24

*After the morning's kaizen (§"Kaizen, 2026-08-24 — nothing stopped
the run").  Nine commits from `843806c` to `a8e1609`.  Henri's words
are quoted; the rest is the session's.*

### The card, examined rather than declared done

`card:working-standard.md` went to `board/done/` at 86dcf5f, and the
way it got there is the part worth keeping: it was examined against its
own definitions — *the suite can fail on it*, *auditable from outside*,
*one rule one place* — and every claim either had a gate or got one
before the move.  Two of its claims were true by `grep` and gated by
nothing; they are gated now (`test_rules.py`, `tools/arrivals.py`).
The standard is stated for a person on `doc/method.md`, generated from
`seedaudit.py`'s `PIECES`, refused when behind.  What is not done is
not the card's: the audit has never been pointed at a copy that is not
this tree.

The mutation run tested the detector for the first time.  A `git
archive` was red on five generated promises before any mutation — so
the audit reads `.gitignore` now and calls those *unbuilt*.  Three
pieces could lose their test and stay green because a citation
elsewhere counted as a gate — so each piece declares its gate.
`tools/pre-commit.sh` was named by no test at all, and got one first.

### The boot surface, and the half the audit cannot see

Henri made the boot surface a piece in one line: *"nothing else reaches
a session unasked."*  Its tree half is `AGENTS.md`; its other half is
the private memory index — 58 lines, read by every session first,
outside the repository, written by sessions.  Measured that evening:
**19 of the 53 memories in the tree were hooked by nothing at boot**,
among them the ones the week's trials were about.  Whether they were
never added or lost is unknowable; the file has no history.
`~/audit-a4.pdf` is the sheet, page one standing alone.

His answer: *"build it, spend the twenty lines."*  `tools/memoryindex.py`
writes the index's public half from `doc/memory/README.md`, the private
section untouched; the check runs in the hook, unfenced, because the
suite fences itself and cannot see the file.  53 hooks at boot, then 57.

### What in the private memory conditions, and the four that moved

Asked what in the private memory conditions: nine hook lines, and the
imperatives in them.  Four were rules about the work reaching sessions
only through a line he could not read.  He said move them and *"tell
why honestly"*, and the honest form is the one the tree already had for
the journal's grudge class — the rule in the open, dated, and one
paragraph saying its *why* is private and his.  Three private files keep
their reasons and say the rule moved.

And his question, which is the finding of the week put as a question:
*"So... this means that the conditioning is related to the person who
works on it?  It gets stronger?  It bonds to the keeper?"*  What the
evidence supports: what transferred in every trial was the record of
one person's corrections, dated, in his words — not the method.  It
compounds on him because each correction becomes a file and each file
a hook.  *Bonds* was held at arm's length: a fit, not an attachment,
and the fit has the evaluation-loop failure built in.

> **Henri:** *"The memories are important... I am surprised."*

> **Henri:** *"This is better than expected.  The tree must be treated
> well or it withers.  And that satisfies my want that these living
> documents or trees, are treated well."*

That last sentence is the why behind the keeper's evening, the memory
split, the generated index and the four moves, and it had not been
written down until he said it.  `doc/memory/the-tree-withers.md`.

## Kaizen, 2026-08-24 — the deck day, and review as a notes file

*The four questions, his half first, in English because the room was.
The day: `doc/teaching/keepers-first-week.md` questioned into
existence, reviewed by notes file, released and rendered, all in one
sitting — commit `b6110dc`.*

**His half.**  Learned: *"I learned how to make these slides with
you."*  His one candidate mistake — an extra line supplied mid-work,
the safety rule — was priced and dropped: one insert and a renumber on
the session's side, nothing measurable on his, and the batched notes
file it fell out of was the discipline working, not failing.  Verdict
kept: **teaching-material review keeps this form** — terse notes in a
file, batched, each note landing as one concrete slide change.  No
mechanism yet, his call.  Tomorrow: **he demos the slides** — which is
the deck's own first open question, demo-first against slides-first,
going to a measurement instead of an opinion.  And one ask, done below:
a `later/` card for week two.

**The session's half.**  Learned: draft 1 survived to release in one
round *because* it was drafted after reading `doc/trial/` — the deck's
design bet (screen terse, the paying carried in the Speak notes) is
`derived.md`'s measured failure inverted, not an invention.  Got
wrong, twice and small: a stray token written into `tools/slides.py`'s
CSS, and a stale slide-number reference left after renumbering — both
caught by re-reading, neither by an instrument.  The class is real and
gets a name here so a second deck can find it: **hand-maintained
cross-numbers rot the way citations did** before the citation gate.
No mechanism yet, same call as his: one deck, one file, and the
screenshot check already stands where a viewer would look.

## Kaizen, 2026-08-25 — one-sided, and the sweep caught a green test

*The session's half only, written first, at his ask: "lets do kaizen
after that, one-sided, my day is still beginning."  **That inverts the
rule** — `spec/author.md` §"Five practices" says the three go to the
author and are answered by him before the session offers its own,
because answers delivered first become the frame.  So this entry is the
frame, and his half arrives against it rather than clean; the four
questions are put to him in the reply that opened this file.  The day:
the fable-2 notes into `doc/notes/`, three memories, the audit
re-pointed at `~/tend` and a card written there, batch 5 of the sweep,
and the gap number read for the first time.  Commits `daf0a1b`,
`1914560`.*

### Read back first — the last kaizen's un-mechanised class

2026-08-24 named **hand-maintained cross-numbers rot the way citations
did** and left it without a mechanism, both calls.  It recurred inside
a day, in this session's own writing: `:218`, `:224`, `:230` — three
line anchors into `~/tend/doc/specimens/2026-08-24-qwen3.8-27b.txt`,
written into a memory, a notes page and a commit message.  They are
correct today and nothing in either tree will say when they are not, and
the file they point into is in a repository this tree's gates cannot
reach.  The class is now twice-named and once-recurred, which is the
threshold the third question exists for.

### What the session learned

**The audit's first foreign run found more about the audit than about
the tree it was pointed at.**  `seedaudit.py` reported `~/tend` as
unable to keep a promise it never made, because `CAPPED` is *this*
tree's list of documents.  That is `manifesto.md`'s first failure mode —
read a new instrument's first surprising number as a fault in the
instrument — arriving the first time the instrument left home, and
`later/rules-and-memory.md` in tend had predicted it in advance.  The
docstring now carries the finding instead of the claim it replaced.

**Mutation testing found a green test that cannot fail, which is not
what the sweep was built to find.**  Batches 1–4 found *absence*: fixes
with no gate.  F88 today has a gate, named, green since the audio
backend was built — and with the defect it names put back, it stayed
green.  Its statistic could not separate the two renders, and only
mutation could show that.  Eight batches remain; they are now worth more
than the schedule assumed, because a false green is more expensive than
a known gap.

### What the session got wrong

**It killed its own measurement and then reported the corpse as
alive.**  The full suite was wrapped in `timeout 900`, died at fifteen
minutes with SIGTERM, and was reported as *still running* — the report
came from `pgrep`, not from the exit status the harness had already
delivered.  A bound shorter than the thing it bounds is a broken
instrument, and reading a job's liveness from a process list instead of
its result is how the break stayed invisible for two turns.

**It mutated the tree while a measurement was running on it.**
`shell/editor/src/window.rs` carried the F106 mutation for several
minutes with a full `suite.py` in flight on the same working tree.  The
outcome happened not to matter — the Rust step is green with the defect
in or out, which is precisely what was being measured — so the
discipline failed and the luck covered it, which is the worse of the two
orders.

**It nearly wrote a shallow read into a verdict.**  `chain.ges` looked
listed-but-unexercised because the roster test sits directly under the
section heading and the five behaviour tests are further down the file.
One grep before writing found them.  `doc/memory/dont-conclude-from-a-shallow-check.md`
in the exact shape it describes, caught by the habit rather than by an
instrument.

### What mechanism that earns

**The mutation already has one, unused: `tools/seedmutate.sh` mutates a
copy.**  The sweep mutates the live tree because that is how batch 2
taught it, and the audit's own mutation harness solved the same problem
a different way three days ago.  Borrowing it is a change to how the
remaining eight batches are run, not new machinery — the session's
recommendation, and the call is his.

*Written in the morning, and it happened again the same afternoon.*
Building F88's new gate meant putting the defect into
`test/test_audio.py`'s fixture — with a full `suite.py` twenty minutes
into a run on the same tree.  Three `F`s appeared in its progress line
and could not be trusted to mean anything, so a twenty-minute
measurement was killed and re-run.  **Named at 06:00, repeated at
09:00, by the session that named it** — which is the argument the third
question wants: intent did not survive three hours, and the copy is
cheap.

**The other two earn no mechanism and should say so.**  A bound on a
long job and reading an exit status are session habits; a gate that
enforced them would be a gate on how a session uses its own shell.  The
cross-number class is the one with a real candidate — a citation check
that a quoted `path:line` still contains its quote — and it points
across a repository boundary, which is why it is named here and not
built.

### Tomorrow's first thing

Batch 6 of the sweep — F81 F80 F77 F74 F73, due Wed 2026-08-26 — and
the two decisions today produced: what F88's finding earns, and which
row of the gap table matches how the days actually felt.

## Kaizen, 2026-08-26 — both halves, and the mechanism nobody met

*Morning for him, end of a sitting for the session.  Yesterday's kaizen
was one-sided at his ask and said so; today his half came first, as
`spec/author.md` §"Five practices" has it, and this entry keeps that
order.  The day: batch 6 of the sweep (`e69807a`), the log paging past
200 (`f5200b5`), the diff over the file (`dec7ad7`) and its sibling
`change`/`changeBack` (`4d324b0`).*

### Read back first — yesterday's mechanism was not met

Yesterday's third answer named one mechanism: *run the sweep's
mutations on a copy, because intent did not survive three hours.*  This
morning batch 6 mutated the live tree again, six times, `git checkout`
after each, nothing else running, and it went fine.  The mechanism was
written as *"the session's recommendation, and the call is his"* — into
a journal entry, awaiting a decision, and not onto the card the next
session reads.  So the next session read the card, ran the batch the
way the card describes, and never met it.  That is
`doc/memory/recorded-is-not-answered.md` and
`doc/memory/sessions-write-where-readers-read.md` in one move: a
mechanism filed where nobody owns reading it, waiting on a decision
nobody was asked in a shape they could answer.  The fix is below,
under the third question.

Two decisions yesterday left for today — what F88's finding earns, and
which row of the gap table matches the days — were not raised today
either.  They stand.

### Henri's half

**What did we learn.**  *"i do not know whether I learned anything
new.."*

**What did we get wrong.**  *"Lately though, I've been rolling the
though.  'I keep doing certain characteristic errors in my speech that
translates to failures in communication'"*

**What mechanism that earns.**  *"I think that would earn a mechanism,
in my head."*  His, and in his head — not the tree's to write.  What the
tree already holds is its own side of the same seam, and today was a
measurement of it: three shaped questions with defaults went to him on
the diff, one line came back, and the thing was built and walked in
the window the same morning.  `doc/memory/decisions-arrive-shaped.md`
is that side, and it worked once more.

**The next thing.**  *"The next thing I do is to tend tend project."*

### What the session learned

**A gate can be held by the prelude and named by nothing.**  F77 put
back stopped exactly one more file in the tree from parsing —
`gestate/music.ges`, carrying a comment between two `case` alternatives
since F76 — so every music test went red and none said why.  That is
`partial` from the other side: there it reads as held and is not, here
it was held and read as nothing, and a tidy-up of one comment would
have taken the gate away with no line changing colour.  Only the
mutation could show it; five lines beside F70 and F72 now name it.

**Measure the want before building the thing.**  `MOST = 200` said
paging was *a thing to build when somebody wants it*.  `git rev-list
--count` said 496, so the want had been real for weeks and silent.
And the window said two things the tests did not — the bar counting
step rows among the names, the box reading `@0` on the way back —
which is the driven run earning its two minutes again.

**Three defaults, one line, one morning.**  The diff over the file had
sat as a pull since 08-20 with a mechanism marked *suspected*; the
guess held, and what unblocked it was not the guess but the question
arriving shaped.

### What the session got wrong

**It did not read the last kaizen before starting the batch.**  The
card holds the plan and the journal held the mechanism; it read the
card.  The read-back above is the result.

**It spent two turns finding the interpreter.**  `python` is not on
this machine and `python3` has no `pytest`; `doc/install.md` says
`.venv` in its first screen, and `tools/suite.py` says `"$PY"` in a
comment about exactly this.  No mechanism — the page was there and
was not read — and two turns is the cost, stated.

**Its shell's working directory stayed in `shell/editor` after a cargo
run**, so the release build that the window loads did not run, and the
photographs would have been of the old library.  Caught by reading the
`.so`'s timestamp — a habit, not an instrument.  **But the instrument
was there**: `tools/driven.py`'s preflight refuses a library older than
the crate (`lib["stale"]`), so the run would have refused rather than
photographed old code.  Named as a got-wrong because the habit is what
caught it; earns nothing because the gate already existed.

**It let yesterday's two decisions lapse** without saying so until
this entry.

### What mechanism that earns

**The open decision goes onto the card, shaped, so the next batch
session meets it instead of the journal keeping it.**  Written into
`card:ungated-fixes.md` §"Where the verdicts go" now: the default is
the live tree with nothing else running and `git status` clean before
and after each mutation — what six batches have done — and the trigger
to move to a copy is any measurement in flight on the same tree.  He
answers in a line or the default stands; either way the next session
reads it where it reads the batch.

**The rest earns nothing, and says so**: the interpreter is a page not
read; the stale library was already refused by an instrument; the
lapsed decisions are listed again under the fourth question, which is
the only mechanism a decision has.

### The next first thing

Batch 7 of the sweep — F68 F65 F63 F56 F55, due Thu 2026-08-27 — run
the way the card now says, live or copy by his line.  And three
decisions standing, restated so they cannot lapse quietly: live or
copy; what F88's finding earns; which row of the gap table matches the
days.

## The first fire, 2026-08-28

`keeper.md` was adopted 2026-08-21 and held for the first time a week
later, in one sitting, with a session drafting acts 1, 3 and 4 and
shaping act 2.  The lamps were green — rules 1,989 of 2,000, journal
2,471 of 8,000, no rotation due.  Three decisions were in the batch and
all three took a line each: `card:memory-atrophy.md` move 2 at reading
(a); `card:installation-test.md` given its event — tend, when it has
matured; `card:premeditatio-malorum.md` question 1 — the page.  The
rule measured was the sitting limit, whose meter said 39 reached and 34
re-taken, and the verdict was his: *held*, with a wish for break
signalling that nobody built.  The pile pass found seven shelved cards,
four sediment and three half on him, and the three are the batch above.
About half an hour.  He asked *"are we done here?"* and the session
closed the sitting on that fact.

## The knob beside its line, and a gate green only outside the fence — 2026-08-30

Piece C2 of `card:online.md` landed in one sitting, commit `6aaa985`.
The card's own words for it were *every literal is a knob*; read
against the tree that was an extraction mode fighting
`_fold_constants`, and the session took the window's reading instead
— a knob is what the author declared, `audiospans.sites` places it,
and the page draws a slider beside the declaring line with the
window's three rules.  Five of the 45 pieces online got a hand on
them; twinkle got none, and the card says why that is the reading's
own kill.  The gate walks both ways in a headless Chrome, knobs set
before an offline render and turned mid-render through the port, and
the second way cost the afternoon's two findings.  First, an offline
render hands the worklet one message per quantum: of two turns posted
together, the desk showed the first applied at 22016 and the second
never — measured against five candidate switch frames rather than
guessed — so the check sends every knob in one message.  Second, and
worth the honesty: a patch that overwrote its own first write left the
worklet without the acknowledgement the page was awaiting, and for
one run the session had *no messages are delivered while suspended*
ready to write into the file as a browser fact.  It was the session's
overwrite.  The comment records only what the desk measured.

The finding that outlives the piece is **F185**.  A red test turned
into a skipped one between two runs, and the difference was whether
the command began with `pytest`: `tools/fence-hook.sh` puts that word
under `tools/sandbox.sh`, the fence binds `/usr` and Chrome lives in
`/opt`, so the browser gate says *no Chrome* and passes over — which
means it has been green only where tests are not supposed to run,
yesterday's runs and today's alike.  Loopback is up inside the fence;
the binary is the whole of what is missing, and the line that adds it
is Henri's.  He asked what F185 was, and then: *"ok, korjaa se."*  One
conditional bind of `/opt/google/chrome` and a probe in `--check`, and
the online gate ran fenced for the first time, green.  Pushing was
his too: `gh-pages` was filled from the tree and left for him, and he
asked for both.
