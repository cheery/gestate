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
