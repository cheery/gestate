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
| Claude | yes | yes | — | see below |

**named** — may their name appear here.
**words quoted** — do their own sentences appear, verbatim.
**training** — may their messages be used to train a model.

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

**Naming is reversible.**  A commit removes it.

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
