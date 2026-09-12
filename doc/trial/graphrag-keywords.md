# graphrag-keywords.md — the third sheet, before the keyword step has run with a vocabulary

*Written 2026-09-12 for `card:graphrag-c.md`, after
`doc/trial/graphrag-ranking.md` came out not decided because the
keyword step read *What is this tree?* as *tree structure, data
organization*.  `tools/prereg.sh doc/trial/graphrag-keywords.md`
must pass before a call.*

**The finding this tests**, the first sheet's second: the keyword
step is a model reading the question with no idea what the tree
calls things.  *The tree* is the repository's own name for itself,
*the keeper* is a role, *a sitting* is a unit of time, and none of
that is in the question's words.  LightRAG's keyword step has the
same blindness and the paper does not address it; the store does,
because every entity name and every relation keyword in it is the
tree's own vocabulary, extracted from the tree.

**question:** does handing the keyword step the store's vocabulary —
the entity names most documents name and the relation keywords most
relations carry, chosen deterministically from the store — make it
read the three questions in the tree's words, so that q3 keeps its
documents under the split ranking?

**decision:** with vocabulary keywords and the split ranking, if q3
cites at least **7 of the 14** distinct documents its first answer
cited, q2 still names at least three of the five prior-art names, and
q1 keeps at least half of its 8, then the vocabulary prompt becomes
the keyword step's default **and** the ranking sheet's own condition
is met on the rerun it asked for, so the split ranking becomes the
default with it — his reading of invention still owed on both.  If
q3 stays under 7, the keyword step was not the cause, both stay
options, and the next thing to look at is the budget, which this
sheet does not touch.  q2 falling under three, whatever q3 does, is
*not decided*.

**control:** the split-ranking answers of the second sheet,
`doc/trial/graphrag-ranking/split-q1.md`–`split-q3.md`, unchanged:
same ranking, same models, same 40,000 characters, same answer
prompt, same backend — the arm runs on the api like the control,
although the tool's default is the cli since this morning, so that
the two runs differ in **one** thing, the keyword step's system
prompt; the cli path is proven separately and is what the tool uses
from here.  Mechanical judge: the count of distinct documents cited,
the five-name grep on q2, citations resolving and sentences without
one, and — new — whether every high keyword the step produced is a
tag that exists in the store.  The person is Henri, not blind.

**n:** 3

**prediction, before the run** (the session's): q3's low keywords
name the tree by a name the store has — *gestate*, *the tree*,
*vision.md* — and its high keywords are all tags in the store; q3
keeps at least 9 of 14; q2 keeps five of five; q1 keeps its 11.  The
keyword call costs the same within a cent, the vocabulary adding
about 3,000 tokens of input to a Haiku call.

**what is not decided here:** the 40,000-character budget, the
two-per-entity description cap, and the month's count.

## After the run — 2026-09-12, nothing above this line edited

The arm's three answers are `doc/trial/graphrag-keywords/vocab-q1.md`–
`vocab-q3.md`, written by the shell from the tool's output.  The
vocabulary handed to the keyword step was 150 names and 100 tags,
4,698 characters, about 1,200 tokens.

| | control: split + bare keywords | arm: split + vocabulary |
|---|---|---|
| q3 keywords | low `[]`; high *tree structure, data organization* | low *the tree*; high *definition, reference* — both tags in the store |
| q3 distinct documents; of the first answer's 14 | 6; 4 | **15; 9** |
| q1 distinct documents; of the first answer's 8 | 11; 6 | 16; 6 |
| q2 prior-art names of five | **5** | **0** |
| q2 keywords, low | *tree, mechanisms, methods, prior art* | five documents: `doc/memory/henri-prior-tools.md`, `method-sources`, `spec/north_star.md`, `manifesto.md`, `vision.md` |
| citations resolve / not; uncited, q1 / q2 / q3 | 10/0;5 · 12/0;1 · 5/1;3 | 15/0;5 · 12/0;1 · 15/1;3 |

**The decision line, read as written.**  q3 keeps **9 of 14**, above
the 7 asked and at the 9 predicted; q1 keeps 6 of 8.  **q2 names none
of the five**, where the control named all five — and the sheet said
q2 under three is *not decided, whatever q3 does*.  So: **not
decided**, the vocabulary prompt stays an option, the ranking sheet's
rerun is not satisfied, and both defaults stay as they were.

**Why q2 fell, mechanical.**  The vocabulary did what it was asked:
it made the keyword step name things the store has.  For q2 it named
five *documents* as the low keywords, the ones nearest *prior art*,
and every one of them is a hub — `manifesto.md` and `vision.md` are
among the ten most-cited entities in the tree.  Under the split
ranking a low-matched entity comes first, so five hubs and their hops
filled the entity half, and the relations half, ranked by shared
theme tokens, no longer reached the *Citation for Toyota Kata* rows
that the bare keyword *prior art*, matched as an entity name, had
pulled in directly.  The vocabulary steered the specific channel
toward the least specific things in it.

**The pattern across three sheets, said once.**  Each sheet fixed the
question it was written for and broke another: the split fixed q2 and
lost q3; the vocabulary fixed q3 and lost q2.  What the three runs
agree on is not the keyword step or the ranking but **what a
document-type entity does in the specific channel**: the most-cited
documents are hubs, a hub as a low keyword pulls hundreds of hops,
and 40,000 characters cannot hold a hub's neighbourhood and a
specific answer at once.  A fourth sheet would test one thing — a
low-keyword match on a document entity contributes the document and
not its hops — with the same three questions and the same judges.
That is a prediction to write, not a change to make tonight.

**Predictions.**  q3 names the tree by a stored name: yes, *the tree*.
All high keywords tags in the store: q3 two of two, q2 four of five,
q1 not counted.  q3 at least 9 of 14: yes, 9.  q2 five of five:
**no, none.**  q1 keeps 11: 16.  Cost within a cent: yes.

**His reading** goes below when he gives it; the person's half is
still the *invents* question, and it stands owed on all three sheets.
