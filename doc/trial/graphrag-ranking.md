# graphrag-ranking.md — the second sheet, before the ranking has run

*Written 2026-09-12 for `card:graphrag-c.md`, after
`doc/trial/graphrag-global.md` decided the query stays and named its
first finding: on the neighbours question the store held the five
prior-art names and the ranking cut them out.  `tools/prereg.sh
doc/trial/graphrag-ranking.md` must pass before a call.*

**The measurement the sheet is built on**, made before writing it:
for all three questions the context handed to the answer call was
cut at 40,000 characters *inside the entities section* — the full
retrieval was 435,000, 1,308,000 and 627,000 characters, and the
relations section, the high-level channel the dual-level design
exists for, began at 233,000, 635,000 and 369,000.  So no answer of
the first trial saw a single relation.  On q2 the five prior-art
names were in the full context, reached by one hop, and none was in
the cut; one, *Ford*, was, by the accident of a hub naming it.

**question:** does a ranking that splits the budget between entities
and relations, and puts matched entities before hopped ones, bring
the prior-art names into q2's answer without losing what q1 and q3
found?

**decision:** if q2's answer under the new ranking names at least
**three of the five** prior-art names the store holds (*Toyota Kata*
or *Rother*, *Nygard*, *Martraire*, *Poppendieck*, *Ford Parsons Kua*
or *fitness functions*), and q1 and q3 each keep at least half of
the distinct documents their first answers cited, and Henri's reading
finds no invention, the split ranking becomes `query`'s default and
the first trial's answers stand as the record of the old one.  If q2
names fewer than three, the ranking is not the cause the sheet
named, the option stays an option, and the next sheet looks at the
keyword step instead.  Losing more than half of q1's or q3's
documents is a *not decided*, whatever q2 does.

**control:** the three answers of the first trial,
`doc/trial/graphrag-global/q1.md`–`q3.md`, unchanged: the same
questions, the same keyword step and its cached keywords, the same
models, the same 40,000-character budget, the same answer prompt.
Only the ranking and the split differ, so the two runs differ in one
thing.  The mechanical judge is a grep for the five names, the
citation count the tool prints, and the count of sentences with no
citation; the person is Henri, reading the new q2 against the old
and the hand answer, and he is not blind, for the reason the first
sheet gives.

**n:** 3

**prediction, before the run** (the session's): q2 names four of the
five, because they are one hop from entities the high keywords match
and the relations they hang on now fit; q1 and q3 each keep at least
two thirds of their documents and cite more, because the relations
carry documents the entities section did not; cost within a cent of
the first run's, the context being the same size.

**what is not decided here:** whether 40,000 characters is the right
budget, whether the keyword step should know the tree's vocabulary,
and whether the query is worth keeping — the month's count.

## After the run — 2026-09-12, nothing above this line edited

**A third arm, added before any call and said here.**  Building the
split ranking's test found a defect in retrieval itself: a relation
matched by theme marked only the endpoint it was first seen from, so
the other endpoint was never a matched entity and never got its hop.
The fix applies to both rankings, so the arms would have differed in
two things.  The old ranking was therefore run again with the fix, as
a third arm, and the six new answers are under
`doc/trial/graphrag-ranking/` as `docs-q*.md` and `split-q*.md`; the
first trial's three stand unchanged as the record of the old code.

| | old, first trial | docs + fix | split + fix |
|---|---|---|---|
| q2: prior-art names of five | **0** | 0 | **5** |
| q2: citations resolve / not; uncited | 6 / 0; 2 | 3 / 0; 2 | 12 / 0; 1 |
| q1: distinct documents cited | 8 | 4 | 11 |
| q3: distinct documents cited | 14 | 9 | 6 |
| q3: citations resolve / not | 19 / 0 | 11 / 0 | 5 / 1 (`~/tend`, a real place outside the tree) |
| relations in the context, q1 / q2 / q3 | 0 / 0 / 0 | 0 / 0 / 0 | 132 / 121 / 138 |

**The decision line, read as written.**  q2 names **five of five**,
above the three the line asks and the four predicted.  q1 keeps 11
of 8, more than it had.  **q3 keeps 6 of 14, under half — so the
sheet's own rule says *not decided*, whatever q2 did.**  The split
ranking stays an option and the default stays as it was.

**Why q3 lost, mechanical.**  Its keyword step read *What is this
tree?* as *tree structure, data organization* (the first sheet's
finding 2), and the split ranking did what it is for: it gave half
the budget to relations tagged with those themes, which are about
the language's data structures, and the entity list that had carried
the tree's three definitions by document count was halved.  The
ranking was right and the keywords were wrong, and a ranking cannot
be judged through a keyword step that misreads one of the three
questions.  **The next sheet is the keyword step**, and q3 is its
test case; this sheet is rerun after it, with the same three arms.

**The fix alone made things worse**, which the third arm was there to
show: docs + fix cites fewer documents than the old code on all three,
because the fix widened matching — 312 entities on q1 against 126 —
and under a ranking by document count more hubs crowded the cut.
The fix is correct and stays, with its test; the ranking it needs is
the one this sheet could not yet decide.

**Predictions.**  q2 four of five: five.  q1 and q3 keep two thirds
and cite more: q1 yes, q3 no.  Cost within a cent: yes, $0.07–0.10
each.

**Not tuned**, again: the split is as the sheet described it, and the
`~/tend` citation the checker refuses is left as the checker's
finding, not the answer's.

**His reading of the new q2 against the old and the hand answer** is
the person's half, and goes below when he gives it.
