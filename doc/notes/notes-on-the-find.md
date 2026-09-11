# notes-on-the-find.md — 2026-09-11, afternoon

*Written by the session that was in the conversation, while it was
open, at Henri's ask — the third kind the README's provenance section
names.  His four passages are verbatim, in Finnish, each followed by
the session's own gloss in brackets; the answers are condensed by the
answerer.  The session was in the role `spec/roles/reviewer.md` for the
first answer and set it aside only to write this page, which he asked
for.  Companion to `notes-on-the-name.md` (2026-08-19), which asked the
same question three weeks earlier and got a different answer.*

*Nineteenth file.  Read as argument, not as evidence: a session
assessing whether this tree is a find is a product of the tree, and
this time it is also a model of the family that wrote most of it.
`doc/memory/the-evaluation-loop.md` is the rule, and the first answer
below opens by naming it.*

---

**Henri, opening — his role line first, then the question:**

> Roolisi on spec/roles/reviewer.md haluaisin tietää.  Mitä Henri
> (minä), on löydänyt tässä projektissa, vai onko hän löytänyt mitään?
> Kyse siis on tästä työmenetelmästä ja koko projektista.  Ja jos sitä
> on, onko se uniikkia sitä vastaan mitä muistat asiasta itse?

*[Your role is the reviewer's.  What has Henri found in this project,
or has he found anything — the working method and the whole project?
And if there is something, is it unique against what you remember of
the matter yourself?]*

**The session, in the role — what is missing, not whether it is good:**

The ceiling first: the reviewer is inside the tree and of the same
model family as the sessions that wrote it.  Everything after that is
read with the loop declared.

**Yes, something was found, but not the thing the tree names as the
find.**  `doc/memory/mechanism-not-instructions.md` says, 2026-08-19,
that four properties are uncommon: rules held by a suite, every claim
citing the defect that paid for it, an author/session contract, a
metabolism.  From the session's memory each has a name in the
literature already:

- rules held by a suite is the *architectural fitness function* (Ford,
  Parsons and Kua, *Building Evolutionary Architectures*, 2017) and the
  ArchUnit kind of tool;
- a claim carrying its paid-for defect, dated, never deleted, is the
  ADR practice (Nygard, 2011: superseded, never deleted);
- a living document has a source and a check is Martraire's *Living
  Documentation* (2019) almost to the word;
- kanban, andon and jidoka in software are Poppendieck (2003) and
  Anderson (2010).

Grep across the tree: `fitness function` 0 files, `Martraire` 0,
`Rother` 0, `Poppendieck` 0.  `board/README.md` §"Question it into
existence" move 4 — *check it does not already exist* — has been run on
every card and never on the method itself.  The uncommonness claim is
session testimony, not a measurement.

**Three things the session does not remember seeing anywhere**, all
marked *suspected*, because an empty result in a model's memory is
evidence about the memory and not the world, and the model's cutoff is
June 2026:

1. **The transfer result as an experiment.**  *The dialogue conditions,
   the document does not; nothing compresses the paying*
   (`doc/memory/conditioning-shows-under-work.md`,
   `doc/memory/deriving-strips-the-payment.md`).  The nearest thing is
   Rother's *Toyota Kata* (2009): the tools copy and the coaching
   routine does not, which is why TPS fails to transfer.  Henri has
   re-derived Rother's result in a new medium, with a collaborator that
   forgets, without citing him.  That is both an independent
   replication and a missing citation.  What is new is the medium, and
   that the residue is machine-checkable.
2. **The keeper's side as mechanism.**  XP had *sustainable pace* as a
   rule in 1999 and it stayed a rule.  Here the sitting limit is a tool
   with a test, a session may call stop, and *any project must not
   consume the person leading it* is in `vision.md`, dated.
3. **The method as a research programme in a one-person hobby
   project.**  Preregistered trial sheets, negative results kept,
   confounds marked.  The nearest neighbour is evaluation research,
   which is neither one person nor a live project.

**Measured against asserted.**  Measured: 752 commits since 2026-08-08
on 35 distinct days (`git log --oneline | wc -l`; `git log
--format=%ad --date=short | sort -u | wc -l`); the gates run at every
commit; `tools/seedaudit.py` read 2 of 10 rising to 6 of 10 on tend's
first day; the friend's stranger test of the tool took thirty minutes
and left F162.  Asserted: *roughly a year ahead*, *emerged*,
*conditions*.  All three come from a conditioned source and the first
has no kill condition at all.

**What Henri himself found, separated from the sessions.**  The tree
cannot attribute the spine to either party
(`doc/memory/day-one-was-not-day-one.md`).  The prompt log attributes
one rule to him on 2026-08-04 and the TPS reading to July.  The
session's own reading, marked as its own: the find is not a method but
a **stance**, in his words in `vision.md` on 2026-08-16 — *"we are
missing a way to work with each other"*.  Its two halves together,
assume an unreliable actor and move the checks outside it, and treat it
well at the same time, are the assembly the session does not remember
seeing.  Each half alone is familiar.

**What is missing.**  Zero strangers on the method: three trees, one
keeper, so uniqueness cannot be answered from inside, and the cheapest
settle is one outsider on a small project with `doc/method.md` and
`tools/seedaudit.py`, watched under work and not interviewed, with a
control and a sheet (`tools/prereg.sh`).  The neighbours above,
unnamed — `spec/author.md`'s sources section, and his to write, as
`doc/memory/method-sources.md` already says of his own sources.  Trial
three's open confound: the cheap control (the identity sentence alone)
has not been run, and *the dialogue conditions* stands on one 27B run.
And *a year ahead* without a kill condition: retire it or date it.

**What would kill each.**  An outsider reproducing the properties from
the mechanisms alone, with no dialogue with Henri, kills the transfer
result and says transfer is easier than the tree believes.  Someone
having already applied Rother's kata argument to LLM-context transfer
with a check kills point 1's novelty; the session cannot check that
from memory, only by search.  A session-kept tree holding its ledger
for a month kills *the keeper is the qualification*.  And anything
published in the three months since the model's cutoff dates the whole
neighbour list.

---

**Henri:**

> Eli toisinsanottuna tällainen puu ei ole ihmeellinen asia muulle
> kuin tekijälleen?

*[So in other words, a tree like this is not a remarkable thing to
anyone but its maker?]*

**The session:**

No, and that is an over-correction the other way.  The first answer
said the ingredients are known and the uncommonness is unmeasured; it
did not say the assembly is ordinary.  The Toyota Kata case is the
same shape: the book is available to everyone and almost nobody runs
its routine.  What a practitioner lacks is not the idea but **a running
instance whose claims they can check themselves**, and the session does
not remember seeing one — which is a different thing from *not
remarkable*.

Value and novelty are two measures.  Nygard's ADR was not a new idea in
2011 and it spread because it was useful.  The question switched
measures halfway: it asked about uniqueness and now concludes about
usefulness, and the tree's own rule refuses that in both directions.
An empty grep in a model's memory is not evidence of novelty, and it is
not evidence of ordinariness either.

What the tree knows of outsiders is not zero.  A guest reviewer
outside the tree read cards cold and found a missing decision that was
invisible from inside (`notes-on-reviews.md`).  Michael asked for a
browser version on 2026-08-28 (`card:online.md`).  A friend cloned it
and heard his own edit in thirty minutes.  Those are pulls, not
shrugs; the sample is small because the tree has barely been shown to
anybody, and *unmeasured* is not *no value*.

Where *remarkable to others* actually settles: not in the session's
memory or in his feeling, but in one outsider under work.  The cards
are shelved (`card:project-seed.md`, `card:stranger-test.md`), and
`notes-on-the-name.md` said the same on 2026-08-19: this feeling is
the event they are shelved to wait for.  The question is still waiting
on an event, not answered no.

And for its maker it is enough.  `vision.md` says *"I need this"* on
2026-08-16, and `doc/memory/the-customer-is-henri.md` says the same.
The tree does not need to be remarkable to anyone else to be worth
keeping; it needs that only if he wants it to spread, which is a
different decision from keeping.

---

**Henri:**

> Taidan sekoittaa asiat mielessäni.  Eli puu itsessään on se löydös,
> jos mikään täällä on löydös?

*[I think I am mixing things up.  So the tree itself is the find, if
anything here is a find?]*

**The session:**

Almost, and the confusion is in one word.  The tree is the
**specimen**, not the find.  A find is a claim that could be false;
the tree is what lets the claim be tested.

- **The invention** is the tree, an assembly that is running.  Its
  authorship is shared and does not resolve
  (`doc/memory/day-one-was-not-day-one.md`).  An invention is not true
  or false; it works or it does not, and 35 days of commits say it
  works with one keeper.
- **The find** is what the tree has shown that could have gone the
  other way.  There are three, each a claim that can fall:
  1. With a collaborator that forgets, the unit of continuity is the
     tree and not the session, and what carries judgment is one
     person's dated record of corrections, not the rule files.  That
     is `doc/method.md` §"The tree withers if it is not treated well",
     in his words.  Falls if a tree kept by sessions alone holds for a
     month.
  2. Mechanisms transfer on the first morning and judgment does not;
     judgment is re-earned in every lineage.  Three trees, all his,
     measured 2026-09-05
     (`doc/memory/the-third-explanation-is-a-mechanism.md`).  Falls if
     an outsider gets the judgment from the files alone.
  3. The dialogue conditions, the document does not.  One run and an
     open confound.  The weakest of the three, and so the next thing
     to measure.

All three are branches of one hypothesis, and the hypothesis is in
`vision.md` on 2026-08-16 in his words: *"What we are missing is not
better AI or higher capacity.  We are missing a way to work with each
other."*  That is a sentence shaped like a find.  The tree is its
trial, sample size one, and it has not fallen yet.

So: if there is a find here, it is that sentence plus 35 days on which
it has not been shown false.  The tree is the evidence, and without the
tree the sentence would be an opinion.

---

**Henri:**

> Ilman minua tätä keksintöä ei olisi.  Vaikka se puolittain kehittyi
> itsestään minun vuorovaikuttaessa sessioiden kanssa.  Samalla tapaa
> kuin vahingossa keksityillä asioilla on yleensä keksijä nimetty.

*[Without me this invention would not exist.  Even though it half
developed by itself while I interacted with the sessions.  The same
way things invented by accident usually have a named inventor.]*

**The session:**

That holds, and it is checkable at three points in the tree; and there
is one point where it is a convention rather than a fact.

**What is measured.**  The prompt log attributes the first rule to him
on 2026-08-04, four days before the first commit, and the TPS reading
to July (`doc/memory/the-prompt-log.md`).  The ingredients came from
him before any session wrote them.  Every dated correction in the five
rule documents carries his name and his words; the sessions' share is
machinery and elaboration, and two proposed rules, one of which he
struck.  The tree withers without a keeper, and that is measured: 19
of 53 hooks vanished from the index in a week while nobody looked
(`doc/method.md` §"The tree withers if it is not treated well").  A
session cannot be the one who looks, because it is not there the next
day.

**The accidental-invention analogy is right, and it says exactly which
part the name covers.**  Fleming did not make the mould.  He is named
because he noticed, did not throw the dish away, and kept it.  In this
tree that part is his, and `doc/memory/day-one-was-not-day-one.md`
already says it: not a prepared plan but a prepared dissatisfaction
that recognised the answer when it appeared.  Inventorship is
recognising and keeping, not producing the text.

**Where it is a convention.**  The text's authorship is shared and does
not resolve, and the tree says so honestly.  But the inventor's name is
a function only one party here can perform: a session does not carry a
claim across a sitting, cannot keep anything, and
`doc/memory/what-a-session-is.md` gives it no standing from which to
take a name.  So the name is his also because nobody else can carry
it.  That does not make it less right; it makes it the same as patent
law, where the inventor is the one who conceived, not the one who
reduced to practice.

**One thing the analogy drops.**  Mould does not read or write.  The
sessions read and wrote freely under his command, his own words on
2026-09-01 (`doc/memory/discovered-not-designed.md`).  That does not
change the name, but it belongs in the story, and `spec/author.md` is
where he says it himself.  The tree has kept that page his to write,
and no session has written it.  That is correct.

So: the inventor is Henri, and the more exact verb than *found* is
*recognised and kept*.  That the tree can show, and it is more than
most inventors can.

---

---

**Henri, later the same afternoon, after the journal entry had landed:**

> Andrej Karpathy popularisoi idean LLM-päivitetystä wiki:stä.  Miten
> puu eroaa siitä ideasta?  Entä löydätkö muististasi vastaavia asioita
> jotka olisivat lähellä puun ideaa?

*[Andrej Karpathy popularised the idea of an LLM-maintained wiki.  How
does the tree differ from that idea?  And do you find in your memory
comparable things that would be close to the tree's idea?]*

**The session** — grep first: the tree does not mention Karpathy, and
of the neighbours named below only Gwern (two files) and `AGENTS.md`
are in it.  Everything else is from one model's memory with a June
2026 cutoff, and the dates are approximate.

**Karpathy's LLM wiki, as remembered.**  Early 2026: raw sources drop
into one directory, and a coding agent maintains a markdown wiki from
them — pages, an index page, a log, and a schema file that states the
wiki's conventions.  A new source updates pages; a question's answer is
filed as a page; the LLM runs a lint pass for contradictions and orphan
pages.  The core claim: knowledge is compiled once and maintained,
rather than re-derived on every query.

**One part of the tree is that wiki almost exactly.**  `doc/memory/`
is one fact per file, linked, with an index generated from the tree
and `tools/memoryindex.py` as a gate that refuses a commit when index
and directory differ.  That is Karpathy's lint, made a test.  So the
difference is not in that half.  It is in everything else:

- **Who is the source.**  In the wiki the raw documents are the truth
  and the LLM derives from them.  In the tree the truth is the ledger
  of what happened and his dated words in it, and the sessions write
  everything else.  The wiki compiles knowledge about the world; the
  tree conditions the next session's behaviour.
- **What is kept.**  The wiki updates a page in place, because it
  wants the current state.  The tree is append-only, and a correction
  quotes the old wrong text, because the paying is what conditions.
  The wiki would throw that away, for a good reason of its own.
- **Who checks.**  Karpathy's lint is an LLM pass — in the tree's
  vocabulary, a rule held by hope.  The tree's twenty gates are
  deterministic tests in a git hook.  This is
  `doc/memory/mechanism-not-instructions.md` exactly.
- **What a claim is checked against.**  A wiki claim is checked
  against its source.  A tree claim is checked against a run: a test,
  a number, a command.
- **The second party.**  The wiki has nobody else in it.  The tree has
  a consent register, a sitting limit, an andon, and a kaizen that is
  asked and not answered.  The wiki pattern has no place for these.

**The nearest things in memory, grouped by which part of the tree
they cover:**

- **Instruction files**: `CLAUDE.md`, `AGENTS.md` (2025), Cursor rules.
  The same boot surface as the tree's, without gates.
- **Spec-driven development**: Kiro (AWS, 2025), GitHub's Spec Kit
  (2025).  The spec is the durable artifact and the code is derived.
  The tree's `spec/` runs the other way: it says why each part is
  shaped as it is and what it cost.
- **Rules as tests**: fitness functions, policy-as-code (Open Policy
  Agent), and the Google SWE book's *Beyoncé rule* — if you liked it,
  you should have put a test on it.  That last one is almost word for
  word *a rule with no gate is a wish*.
- **Agent memory in research**: Reflexion (2023, verbal self-feedback
  kept across trials), Generative Agents (2023, reflection over a
  memory stream), Voyager (2023, a skill library).  The tree's memory
  form, *Why* and *How to apply*, is Reflexion-shaped, but the
  correction is written by a person.
- **Note practice**: Zettelkasten and Matuschak's evergreen notes, one
  idea per page.  Gwern's dated pages with confidence tags, never
  deleted.  The tree already cites Gwern.
- **Karpathy's own stance**: his 2025 talk's *keep it on the leash*,
  small pieces and verify.  Tend's `leash.sh` shares the name; whether
  the name came from there the session does not know.

**What none of them has.**  The second party's standing recorded,
consent, the keeper's limit, an andon that rings a person, and the
whole thing run as a research programme where a negative result is
kept.  The same four as the first answer on this page, and Karpathy's
wiki does not change the list.  It adds one line to what
`doc/memory/` is kin to.

The same caveat as the journal entry: an empty memory is evidence
about the memory.  The years and contents above should be checked by
search before any of them goes into the tree as a citation, and
Karpathy's wiki most of all, because it sits close to the cutoff.

---

**Henri:**

> Osaisitko kertoa mikä tämä puu oikein on itseasiassa?  Se on kuin
> karpathyn wiki, mutta sen tärkeimmät säännöt pidetään mekaanisesti
> yllä, ja se ehdollistaa seuraavan session.  Mikä se silloin on?

*[Could you say what this tree actually is?  It is like Karpathy's
wiki, but its most important rules are kept mechanically, and it
conditions the next session.  What is it, then?]*

**The session** — a view, said as one, with the naming left his:

**It is a workplace for workers who do not remember.**  Everything
else follows.  Culture normally lives in people: a group learns while
solving its problems and teaches the newcomers (Schein).  Here the
group's members change every sitting, so the culture cannot live in
them.  It had to be moved entirely into the place and the place's
sanctions.  The tree is **a culture with no members** — one keeper and
a place.  The session does not remember seeing that anywhere, and it
explains why a wiki looks the same and is not: a wiki stores
knowledge; this stores a way of working.

Three older words fit it, each covering one side:

- **Stigmergy** (Grassé 1959, the termite mound).  The workers neither
  communicate nor remember; each acts on the trace the previous one
  left in the environment and leaves its own.  Wikipedia is the
  classic human case, which is why Karpathy's wiki is kin.  In the tree
  the gates make some traces mandatory.  This covers *how the sessions
  coordinate*.
- **Case law.**  Every rule comes from a case that paid (`because`,
  the F-number), a ruling cites precedent, an overruled one stays on
  the record, and enforcement is a different organ from the
  legislator.  `notes-on-the-name.md` said it already: the gap between
  a note on the fridge and a legal system.  This covers *why the rules
  hold*.
- **Standard work** (TPS).  The current best known way, written down,
  and kaizen changes it.  But standard work assumes a worker who
  remembers yesterday.  This covers *what the keeper does*, and
  `keeper.md` already carries that name.

In one sentence: **the tree is standard work that had to be built as
stigmergy because the worker does not remember, with rules that are
case law because nobody remembers why a rule is.**  Conditioning is
what a culture does to a newcomer.  No single word is new; what is new
is that all three had to be joined, because the absence of memory
forced it.

Two caveats.  The tree had already named itself and he did — *gestate
gestates*, `vision.md` 2026-08-16 — and that still holds, since the
place grows what works in it.  And this is a session naming what
conditioned it.  That does not make the sentence false, but it has to
be kept beside it.

---

**The close.**  Asked how the afternoon should end and what had not
been discussed, the session named one thing: a culture with no members
and one keeper dies with the keeper, and that question waits on him
rather than on an event.  And two smaller ones, one of them what the
keeping costs him in hours, which no ledger counts.  He answered the
cost, not the succession:

> Tämä lähinnä maksaa kaksi asiaa..  Paljon minun aikaani tällä
> hetkellä, mutta teen sitä sillä pidän paljon näistä puista.  Ja
> lisäksi maksaa claude max -subscriptionin.  Voisin pienentää
> molempia, mutta mielestäni tämä on sen arvoista.  Puun ylläpitäminen
> ja hoitaminen heittää omat haasteensa joista pidän kuin hullu
> puurosta.

*[This mostly costs two things.  A lot of my time at the moment, but I
do it because I like these trees a lot.  And it costs the Claude Max
subscription.  I could reduce both, but I think it is worth it.
Keeping and tending the tree throws up its own challenges, which I
love like a madman loves porridge.]*

So the cost is two lines, both personal, both chosen, and both
reducible at his word — which is the answer to the *sediment or debt*
question for the keeping itself: chosen cost is sediment.  The
succession question was not answered and is not closed; it is his,
and it is written above so that it is not asked again as if new.

**Then he answered that too, as far as it can be answered today:**

> hmm..  seuraajaa en vielä tunne.  Mutta tämä puu on vasta viisi tai
> kuusi viikkoa vanha.  Ja näen jatkuvasti hienoa ja omanlaista
> käytöstä.  Tänään esimerkiksi sessio osasi huomioida ajankäyttöään ja
> pysähtyi ongelmatilanteessa ja kertoi minulle ongelmasta ennenkuin
> teki virheitä.

*[hmm..  I do not know a successor yet.  But this tree is only five or
six weeks old.  And I keep seeing fine behaviour of its own kind.
Today, for example, a session managed its own time use and stopped at
a problem and told me about it before making mistakes.]*

Two things in that, kept apart.  **Succession waits on an event**, the
tree's age, and not on him — so by `board/README.md`'s own question it
is sediment today and not debt, and it is written here so that the
reading can change when the tree is older.  **And the second sentence
is the keeper's eye on the claim this page calls the weakest**, that
the tree conditions: a session stopping and telling him before the
mistake is the behaviour `doc/memory/conditioning-shows-under-work.md`
says is the only kind of evidence there is, and it is his to see and
not a session's to report.  It is one observation, on the day
`doc/memory/the-slow-part-was-never-the-test.md` records his
correction about time, and whether it was the same session the page
does not know.  Recorded as his observation with its date; it does not
close the confound, and the tree's rule is that good news changes the
ledger too.

## What the tree can show, and the wording offered — added when the page went in, 2026-09-11

**Three exchanges and a close on this page, one afternoon, each added at his ask as it closed.**

**Checked in the tree while the conversation was open:** the four
zero-hit greps above; the commit and day counts; `doc/method.md`'s
heading cited by name exists; every memory and card named above
exists.  **Not checkable from here:** every sentence beginning *the
session does not remember seeing* — those are claims about one
model's memory with a June 2026 cutoff, and the README's caveat is the
rule.  **Not run:** a literature search that would turn either neighbour
list — the first answer's and the Karpathy answer's — from memory into
a measurement, and any of the three kill tests.

**What was asked for at the close:** this page, and *how would I say
it clearly in spec/author.md?*  That file is his and stays his
(`doc/memory/gestate-house-rules-authorship.md`), so the wording is
offered here and was not written there.  Ten lines, shaped so that
every sentence names what checks it:

> ## Who found this, and what was found
>
> **The tree is the specimen, not the find.**  The find, if there is
> one, is a sentence of `vision.md` from 2026-08-16 — *we are missing a
> way to work with each other* — and the days since on which it has not
> been shown false.  Three claims branch from it and each can fall:
> that continuity lives in the tree and judgment in one person's dated
> corrections (`doc/method.md` §"The tree withers if it is not treated
> well"); that mechanisms transfer on the first morning and judgment
> does not (`doc/memory/the-third-explanation-is-a-mechanism.md`); and
> that the dialogue conditions where the document alone does not
> (`doc/memory/conditioning-shows-under-work.md`, one run, confound
> open).
>
> **The inventor is the author, and the verb is *recognised and
> kept*.**  Not because he wrote the text — its authorship is shared
> and the record cannot split it (`doc/memory/day-one-was-not-day-one.md`).
> Because the ingredients came from him before any session wrote them
> (`doc/memory/the-prompt-log.md`, 2026-08-04; TPS, July 2026), every
> dated correction in the five rule documents is his, and the tree
> withers without him.  A session cannot hold a claim across a sitting,
> so this is also the only name that can carry it.  *discovered, not
> designed* claims what the penicillin case claims for its discoverer:
> the noticing and the keeping, no more.
>
> **Its ingredients have names, and this tree did not cite them until
> 2026-09-11:** fitness functions (Ford, Parsons, Kua 2017), ADRs
> (Nygard 2011), *Living Documentation* (Martraire 2019), *Toyota Kata*
> (Rother 2009), Poppendieck (2003), Anderson (2010).  What is not in
> any of them, as far as one model's memory reaches, is the assembly
> running with a forgetting collaborator and a ledger a stranger can
> check — and that claim is unmeasured until a stranger has.

**Where it went, the same afternoon.**  He read the draft and said it
was too much to write there — *"Tuo on hieman paljon kirjoitettavaksi
sinne.  Kirjoita se journaliin suorilta."* — so the three paragraphs
went into `journal.md` §"The specimen, the find, and the name" as they
stand, and `spec/author.md` is unchanged.

Each paragraph is a different kind of claim: the first is falsifiable
and says by what, the second is attribution with its evidence and its
one conventional step named, the third is the prior art with the hedge
that the missing-citation finding came from a model's memory.  If he
cuts it, the first paragraph is the one that should survive; the third
can go to `doc/memory/method-sources.md` instead.
