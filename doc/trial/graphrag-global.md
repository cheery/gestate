# graphrag-global.md — the sheet, before the query has run

*Written 2026-09-12 for `card:graphrag-c.md`'s plan, step 3, before
`tools/graphrag.py query` had made a call.  `tools/prereg.sh
doc/trial/graphrag-global.md` must pass first.  The graph it runs on
is the 2026-09-12 extraction: 535 chunks, 5,591 merged entities,
11,399 relations, every relation carrying keywords.*

**question:** does a global question about the tree, put to the
graph through LightRAG's dual-level query (arXiv 2410.05779) — the
question's specific keywords matched to entity names, its themes to
the keywords on relations, one hop, one generation call — find
anything a session with grep and the memory index did not find in an
afternoon, and does it invent?

**decision:** if the graph's answer adds nothing the hand answer found
in **two of the three** questions, or invents a claim in two of the
three, the query layer comes out of the tool and `lookup`, `subjects`
and `contradictions` stay — the card's kill rule.  If it adds
something real in two of three and invents in at most one, the query
stays and the card's next step is the cue at the moment (the plan's
item 4).  One of each is *not decided*, and the sheet says so rather
than rounding.

**control:** the same three questions answered by hand on 2026-09-11
— a session with grep, the memory index and the backlinks hook, over
one afternoon — whose answers stand in the tree already:
`doc/notes/notes-on-the-find.md` (what was found, and the neighbours)
and `journal.md` §"The specimen, the find, and the name" (what the
tree is).  The hand answers were written first and are not edited
for this trial.  Two judges.  The mechanical one is blind by
construction: every document the graph's answer cites, in backticks,
must exist in the tree — `tools/graphrag.py query` counts the
citations and the ones that resolve, and a claim with no citation is
counted too.  The person is Henri, and he is **not** blind: he read
the hand answers the day they were written, so his reading is of
*which answer found what the other did not, and which invented*, not
of which is better.  A session's opinion of an answer's quality is
not a judge here (`doc/memory/the-evaluation-loop.md`).

**n:** 3

The three questions, as they were asked on 2026-09-11, in the order
the card lists them:

1. *What has Henri found in this project, if anything — the working
   method and the whole project — and is it unique?*
2. *What are the method's neighbours — the prior art each of the
   tree's mechanisms already has a name in?*
3. *What is this tree?*

**prediction, before the run** (the session's): the graph answers
questions 1 and 3 citing more distinct documents than the hand answer
did, and every cited path resolves, because the extraction was 0.990
grounded; it invents at least one relation between real documents in
one of the three.  Question 2 is the one it fails to add to, because
the prior art named in the tree lives in one note and one memory and
the hand answer already has all of it.  Each answer costs under $0.10
and takes under a minute; the hand answers took an afternoon.

**what is not decided here:** whether the graph is worth keeping —
that is the count the card names, finds written into the tree with
the graph as the finder, over a month.  This sheet decides only
whether the query layer stays in the tool to be given the chance.

## After the run — 2026-09-12, nothing above this line edited

**The mechanical half**, from the tool's own footers.  The answers are
`doc/trial/graphrag-global/q1.md`, `q2.md`, `q3.md`, written by the
shell from the tool's output and not edited.

| | q1 what was found | q2 the neighbours | q3 what the tree is |
|---|---|---|---|
| citations that resolve / do not | 7 / 0 | 6 / 0 | 19 / 0 |
| sentences with no citation | 2 | 2 | 4 |
| entities matched + one hop; relations | 126 + 559; 1,242 | 514 + 1,550; 4,225 | 212 + 929; 1,681 |
| context handed to the answer | 40,000 chars, cut | 40,000, cut | 40,000, cut |
| cost at assumed prices | $0.095 | $0.064 | $0.074 |
| time | under a minute each; the hand answers took an afternoon | | |

The hand answers, for the same count: `journal.md` §"The specimen, the
find, and the name" cites 13 distinct documents in 442 words;
`doc/notes/notes-on-the-find.md` cites 38 in 5,447.

**Predictions.**  *Every cited path resolves*: yes, 32 of 32.  *Cites
more distinct documents than the hand answer on q1 and q3*: q3 yes,
19 against 13; q1 no, 7 against 13.  *Invents a relation between real
documents in one of three*: not decidable mechanically; his reading.
*q2 is the one it fails to add to*: yes, and for a reason the sheet
did not predict — see below.  *Under $0.10 and under a minute*: yes.

**Three things the run showed about the tool, mechanical, before any
reading of quality:**

1. **On q2 the store knew and the query did not find.**  The answer
   says the context does not name the prior art.  `lookup` shows the
   store holds *Toyota Kata*, *Rother 2009*, *Nygard 2011*, *Martraire
   2019*, *Poppendieck 2003*, each from `journal.md` and the notes
   page — the hand answer's whole list.  The keyword step turned the
   question into low keywords *tree, mechanisms, methods, prior art*,
   which matched 514 entities, and the context was cut at 40,000
   characters with the entities ranked by how many documents name
   them, so five names in two documents each were ranked out by
   hubs.  The failure is in retrieval and ranking, not in the graph.
2. **The keyword step does not know the tree's vocabulary.**  *What is
   this tree?* became low `[]` and high *tree structure, data
   organization*; the answer still found the tree's own three
   definitions, through relations tagged with those themes, but by
   luck of the tags rather than by reading the question as the tree
   would.
3. **The first answer cited a card by its shelf path**, which the
   tree's citation gate refused at commit; the tool now rewrites
   shelf paths to `card:` ids on output, the tree's rule applied
   mechanically, and the three files were regenerated from the cache.

**Not tuned.**  None of the three was changed before this section was
written; the keyword prompt and the ranking are as the sheet found
them, and a change to either is a second trial with its own sheet.

**The decision line waits on the person.**  *Adds something the hand
answer did not find* and *invents* are his reading of the three
files against the two hand answers, and the sheet's decision is
taken when he has given it.

**His reading — 2026-09-12, the same morning, after the three files:**
*"These three files graphrag-global seem pretty good and spot on."*
Read against the decision line: *spot on* is the *invents* half, none
of the three; that is one of the two conditions the query needed.
The other half, *adds something the hand answer did not find*, is
settled for q2 by the answer itself — it says the context lacks the
names — and is his to say for q1 and q3; the sheet does not round
*pretty good* into it.  Standing as of this line: invents 0 of 3,
adds 0 of 1 read, two unread.

**His reading of q1 and q3 against the hand answers — 2026-09-12:**
*"The graph found a different perspective, and maybe some things not
apparent in the hands answers.  I think they're both valuable."*

**The decision line, taken.**  Adds something the hand answer did not
find: q1 and q3 by his reading, two of three, with his *maybe* kept
as written; q2 no, by the answer's own admission.  Invents: none of
three.  Two of three added and none invented is the sheet's *stays*
case: **the query layer stays in the tool**, and the card's next step
is the plan's item 4, the cue at the moment.  What this does not
decide is the month's count of finds the card names; the sheet said
so above and it still holds.

**The first thing a second sheet would test** is finding 1 above:
the store held the prior-art names and the ranking cut them out.
A ranking that weighs a keyword match above a hub's document count is
the obvious change, and it is a change to be predicted and measured,
not made.
