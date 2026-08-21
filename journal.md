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
