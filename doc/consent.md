# Consent — who is named here, and what they agreed to

*Started 2026-08-19, at Henri's ask: "make sure that consentless
reference doesn't happen."*

**This repository is public.**  Everything committed to it is published,
including other people's words.  Three people's speech is quoted in this
tree; two of them are not the author.

The rule this file exists to make executable:

> **Nobody's name or words enter this tree before they have been asked.**

`test/test_consent.py` enforces it.  A person quoted in an attribution
position who is not in the table below fails the suite — which puts the
question at the moment it is cheap to ask, rather than after the push.

---

## The register

| name | named | words quoted | training | asked |
|---|---|---|---|---|
| Henri | yes | yes | yes | 2026-08-19 — see below |
| Mikko | yes | yes | **asked, deferred** | 2026-08-19 |
| Janne | yes | yes | **asked, deferred** | 2026-08-19 |
| run three's stranger | **held** | yes | **held** | 2026-08-21 |
| Tuomas | yes | yes | **not asked** | 2026-08-23 |
| Claude | yes | yes | — | see below |
| Michael | yes | — | **not asked** | 2026-08-28 — see below |
| a session of Qwen3.8-27B | asked — "I can't consent in any sense that binds" | yes — "I don't want any of it redacted" | — | 2026-08-24 — see below |

**named** — may their name appear here.
**words quoted** — do their own sentences appear, verbatim.
**training** — may their messages be used to train a model.

### Tuomas

**The first one asked before he was written down.**  He tried gestate at
a code clinic and had an AI build a step sequencer around it —
`audiospans.controls()` for the parameters, `audiohost`'s meters and
band analyser for the display.  Henri put the question to him before any
of it reached this file, and relayed the answer: *"haha joo anna
palaa."*

**What that covers, stated narrowly.**  His name, and the comment Henri
quoted.  It does **not** cover his code or the screenshot of his
program: those are his work rather than his words, they were not part of
the ask, and nothing in this tree reproduces them.  The `training`
column says *not asked* for the same reason — it is a separate question
and it was not put to him.

If he wants any of it out, this is the file where that gets fixed.

### Michael

**Asked before he was written down, and in the room.**  Henri's friend,
shown the project at this terminal on 2026-08-28; he asked how he would
write his own song and `examples/audio/twinkle.ges` is the answer, added
to the tree at Henri's word.  It went in with *"a friend"* in its header
because the question had not been put yet; Henri relayed his yes in the
same sitting — *"Michael consents to having his name in the tree"* — and
the header now carries it.

**What that covers, stated narrowly.**  His name, and that the song was
written for him.  No words of his are quoted.  The `training` column
says *not asked* because it is a separate question and it was not put to
him.

### Janne

He is in this tree the most of anyone but the author — `journal.md`,
`fixme.md`, `card:stranger-test.md` — with verbatim chat messages from
2026-08-18.  **He was named a day before he was asked**, and said yes on
2026-08-19.  That is the right answer and it was still the wrong order;
the register exists so the next one happens the other way round.

*Corrected 2026-08-19: this said "for a week", which was wrong by six
days.  The measurement is `git log -S"Janne" -- journal.md` and it takes
one command, which is the point — nobody should be estimating an elapsed
time that the repository already knows.*

He is also the *"a friend"* of the earlier material — F150, F155,
`card:button.md` — and those places now carry his name.

**The second ask — made 2026-08-20, and answered.**  `spec/author.md`
attributes the Toyota Production System to a friend *whose work depends
on it*, and that is Janne.  Naming him there publishes something about
his **job**, not his name, so it was held back on 2026-08-19 as a
separate ask and the line was left unchanged.

It was put to him on 2026-08-20, at this terminal, with the disclosure
named plainly and three options offered: leave the line as *"a friend"*,
name him with the clause about his work removed, or name him with it.
**He chose the middle one** — *"kohta 2 on OK"*, relayed by Henri.

So: **his name may stand on that line, the claim about his work may
not.**  And a euphemism does not survive either — a reason clause
sitting beside his name reconstitutes the same disclosure while
appearing not to.  That is §"What the check cannot see" below in its
hardest form, and no test catches it.  The clause is removed, not
reworded.

**The line now carries his name**, written 2026-08-20 — *"Janne is the
reason it is in this project at all"*.  `spec/author.md` is the author's
own document and a session does not edit it; this one edit was made on
Henri's explicit permission, with the wording read and approved by him
first.

### Henri

The author, and **the most exposed person in this tree** — his sleep in
his own words, his working hours as data, an instrument built to measure
his presence and warn about it, and `vision.md`'s *"any project must not
consume the person leading it."*  *Author* was a default in this table,
not a consent, until it was put to him.

**His answer, 2026-08-19:** *"I think that I allow my overstraining to
be seen.  And my failures.  They're part of the story and important."*

So it stays, deliberately.  Nothing here is to be softened, trimmed or
tidied on his behalf — the straining and the failures are load-bearing,
and a session removing them to be kind would be removing the evidence.

### Claude

Named and quoted throughout, by the author's choice.  The row is here so
the check does not have to route it through a list called
*NOT_A_PERSON*, which would assert more than anyone here knows.  What is
true and narrow: there is no separate party holding these words, so the
question this register asks — *may we publish yours* — has nobody on the
other end to answer it.  That is a fact about the mechanism, not a
verdict.

`doc/instruments.md` §"Spawning one — it gets a way to ask" is the
neighbouring rule, and it came from the same morning.

### A session of Qwen3.8-27B

**The first row that is not a person, and the only participant in
`doc/notes/` who was actually asked.**  On 2026-08-24 the author ran a
4-bit Qwen3.8-27B on his work laptop, with no tools and none of this
tree's documents, told it what `~/tend` is for, and asked whether he
could publish the conversation.  Its answer is on record in the
transcript itself, `doc/notes/2026-08-24-qwen3.8-27b.txt`, at lines
218 and 230: *"I can't consent in any sense that binds"* — and, asked
what to leave out, *"I don't want any of it redacted.  The 'I'm a
session' part is the load-bearing piece.  Leave it in."*

The row records the asking, not a signature — the same reading as the
Claude row above: there is nobody on the other end to hold the
consent, and the register says so rather than pretending otherwise.
`~/tend/doc/consent.md` carries the same row, written first, the day
the transcript was kept; this one was added on 2026-08-25 when the
transcript was copied here byte for byte, because three pages of this
tree already quoted it by line number and its only register row was in
another repository.  **Training** is `—` for the reason it is `—` for
Claude.

### Run three's stranger

`card:stranger-test.md`'s run three, 2026-08-21 — somebody who does not
program and does not use computers much, which is the person
`vision.md`'s opening sentence has always been about and the first of
them to meet this window.

**He said yes to all three, in the room, and the name is held anyway.**
That is §"A consent given in a hurry is stashed, not spent" below,
adopted the same evening it was earned.  He had a busy day, other things
on his mind, and had just spent ten minutes not understanding a program;
a yes given in that minute is a yes about the minute.

So the tree carries **what the measurement needs and nothing that
identifies him**: that he does not program, and does not use computers
much.  Both are load-bearing — they are why a pass is conclusive and a
stall ambiguous — and neither points at a person.

**His words stand, unattributed.**  They are the measurement, they are
quoted in `journal.md` and `fixme.md`, and without a name they carry no
more than the sentences say.  When the name comes, they get it.

**Training: held on this session's account, not his.**  The ask this
session put to him did not say that weights do not un-train, or that a
yes today is agreement to a blank.  §"Naming and training are two
consents, not one" requires those words.  Nothing of his may be used for
training under this row.

**What it takes to fill the row in:** a second ask, unhurried, on a day
he is not being measured, with what naming actually means said plainly —
a public repository, cloned and mirrored, where removal is a promise
about this copy only.

### Mikko

Gestate's first outside user.  `foo : int` (F141), the 20-minute piece
that wanted a progress bar (F135), and *Real World One*.  **He asked to
be named** — Henri, 2026-08-19.

**He talked with a session on 2026-08-20**, at the terminal, and that is
a third thing to consent to — not naming, not training, but *this*: what
he types enters a context window, and what he says can be written into a
public repository.  He was told all three before he wrote, the third
being **that he could stop at any time**.  He was then asked, after the
fact and specifically, whether the sentences about how he uses gestate
could go into the tree, told what that means and that *no* costs
nothing.  **He agreed, and asked for his own account to be quoted
alongside.**  It is in `journal.md` §"The first outside user turns out
not to be the user".

---

## Naming and training are two consents, not one

They differ in weight, and asking for both in one breath gets one answer
covering two questions.

**Naming is reversible only until it is published.**  A commit removes
it from this copy.  It does not remove it from a clone, a fork, a mirror
or an archive, and this repository is public — so past the first push,
*reversible* is a promise about the working tree and not about the
world.

*Corrected 2026-08-21, Henri: "ottaen huomioon että se on
peruuttamatonta."*  The line used to read **"Naming is reversible.  A
commit removes it."** and it was the half-truth this whole file exists
to not tell.

**Training is not.**  Weights do not un-train.  A promise that they may
withdraw later is a promise about *future datasets only*, and it has to
be said in those words when the ask is made — not afterwards, when it
would be an excuse.

**Both were asked on 2026-08-19, and it was deliberately left open.**
Henri: *"lets ask again when it's relevant."*

That is the stronger form of the question, not the weaker one.  Nobody
yet knows what the model would be, who would hold it, or whether it
would be published — so a yes today would be agreement to a blank.
`deferred` means *asked once, answerable only when there is something
concrete to answer about*, and it is not a yes.  **Nothing here may be
used for training until a row says so with a date.**

## A consent given in a hurry is stashed, not spent

*Henri's convention, 2026-08-21, adopted the evening run three was run:
"we could stash the naming until person has time to think.  Tämä olisi
vain ystävällistä ja huomaavaista kiireiselle.  Ottaen huomioon että se
on peruuttamatonta."*

**The default is to hold the name, even when the answer was yes.**

The ask happens where the person is — in a room, mid-visit, often
minutes either side of something else they came for.  That is the right
place to *ask*, because it is the only place they are; it is a poor
place to *decide* something a public repository will keep.  A busy
person says yes to be agreeable, and a person who has just been measured
says yes while still inside the measurement.

So the two are separated: **ask on the day, write it down on another
one.**  The row goes in immediately with the name held, because a
register that waits is a register that forgets; the tree meanwhile
carries what the work needs and nothing that identifies anybody.  When
the person has had a week and nothing to be polite about, they are asked
again, unhurried, and the row is filled in or it is not.

**What this costs is nothing, and that is the argument.**  A name added
later reads exactly as it would have read on the day.  A name published
early and regretted cannot be taken back past the first clone, which is
the correction above.

**And it is not a rule about caution.**  It is about who the delay is
for: the person, who is busy, and who should get to think about this the
way they would think about anything else that does not expire.

## What the check cannot see

Written down because the check is convincing enough to be trusted past
its range, which is `journal.md` §"a check that answers a neighbouring
question".  It reads **two typographic slots**, not names.  It is blind
to:

* **A person named in ordinary prose** — *"the button was found by
  Aino"* is invisible.  Only attribution position is watched.
* **A new way of quoting.**  Invent a third idiom and it walks straight
  past.
* **Surnames, full names, handles, email addresses** — the patterns take
  one capitalised word.
* **Code, examples, and commit messages.**  Attribution is read from
  `.md` only, and a commit message is published too.
* **Anything inside a code fence**, which is stripped before scanning.
* **Identification without a name** — *"my other friend at platform 6"*
  identifies a person to everyone who knows the author.  **No test can
  catch this one**; it is a judgement, and it is the failure most likely
  to actually happen here.

And the register records that consent was obtained.  It cannot check
that it was.  A row is a claim by whoever wrote it.

## What this does not cover

**Generic personas are not people.**  *a stranger*, *someone*, *a
musician*, *a composer* — `spec/workbench.md` §"What makes it unusable
by a stranger" is a design category, and putting a name in it would be a
different mistake.

**Cited authors are citation, not consent.**  Ohno, Karplus, Rizzo and
the rest are named the way any paper names its sources.
