# graphrag-hand.md — the sixth sheet, before three new questions have been put to the graph

*Written 2026-09-12 for `card:graphrag-c.md`, after the fifth sheet
found its judge was built from the thing the arms were meant to fix.
`tools/prereg.sh doc/trial/graphrag-hand.md` must pass before a call.*

**Why new questions.**  The fifth sheet said the next judge should be
the hand answers' documents.  For the three questions used so far,
every arm's answer already exists on the tree and its overlap with
the hand answer has already been computed, so a sheet over them now
would predict numbers already seen.  A sheet needs data that does
not exist yet.  The tree holds hand answers to other questions: each
page under `doc/notes/` is a question Henri asked and a session
answered by hand, with citations, written first and not for this.
Three of them, chosen for being global — about the tree, not about
one file — and for being on different subjects:

1. *What keeps a keeper in check — what stops the person who keeps
   this tree from drifting, and what would spread the method?*
   Hand answer: `doc/notes/notes-on-drift.md`, 11 documents cited.
2. *What is the tree's secretion for, and how is it done well?*
   Hand answer: `doc/notes/notes-on-secretion.md`, 9 documents.
3. *Why did the reviewing guest's reviews work, and how would one
   keep a reviewer in the project?*  Hand answer:
   `doc/notes/notes-on-reviews.md`, 7 documents.

The graph has read those pages — they are documents in the store —
so an answer may cite the page itself; that is a finder pointing at
the right door and counts as one shared document like any other.

**question:** with the hand answer as the judge, which of the two
retrievals that survived the earlier sheets finds more of what a
hand-read found — the split budget with vocabulary keywords, or
that with the theme channel ranked by rarity?

**decision:** two arms, both vocabulary keywords, both the split
budget, both on the api: **control** = `--ranking split`, **B** =
`--ranking themes`.  Per question, the count of distinct documents
the answer cites that the hand answer also cites.  The arm that
shares **at least as many** as the other on **two of the three**
questions, with no citation failing to resolve except the checker's
known false positives (`~/tend`, `spec/*.md`), becomes `query`'s
default with the vocabulary keywords and the split budget; if the
counts tie on two or more questions, B is the default, on his
reading of the fifth sheet's answers — *"the B answers seemed
slightly better than the A answers.  Though, it depended on what was
asked"* — and on its five of five.  Henri's reading of invention on
the three new answers of the winning arm is still owed before the
default is committed; a reading of *invents* on two of three
overturns the count, and the sheet says so now.

**control:** the two arms differ in the theme channel's ranking
alone: same three questions, same keyword step and its cached
replies, same models, same 40,000 characters, same answer prompt,
same backend.  The hand answers were written on 2026-08-21,
2026-08-23 and 2026-09-05, by sessions that did not know a graph
would be built, and are not edited.  The mechanical judge is the
shared-document count, computed by the same regular expression over
both texts; the person is Henri, who has read all three pages.

**n:** 3

**prediction, before the run** (the session's): B shares at least as
many as the control on two of three, by one to three documents each;
both cite the notes page itself on at least two of three; both cite
`doc/method.md` or `manifesto.md` on all three, hubs being what the
theme channel still carries; total cost about $0.50.

**what is not decided here:** the budget, the answer's length, the
`doc/memory/` empty-key defect, the month's count, and whether the
docs ranking of the first trial should have been an arm — it was
not, because two sheets and his readings have already placed the
split above it.

## After the run — 2026-09-12, nothing above this line edited

The six answers are `doc/trial/graphrag-hand/control-q*.md` and
`b-q*.md`, written by the shell from the tool's output.

| shared with the hand answer | q1 drift, of 11 | q2 secretion, of 9 | q3 reviews, of 7 |
|---|---|---|---|
| control, split + vocabulary | 2 | 0 | 0 |
| B, themes + vocabulary | 1 | 0 | 1 |
| cites the notes page itself | control yes, B yes | neither | neither |
| citations resolve / not; uncited — control | 14/0; 3 | 6/0; 8 | 6/0; 3 |
| citations resolve / not; uncited — B | 7/0; 7 | 5/0; 4 | 11/0; 3 |

**The decision line, read as written.**  Each arm shares at least as
many as the other on two of three — the control on q1 and the tie,
B on q3 and the tie — so the line's condition holds for both, and
its tie-break asks for two ties and there is one.  **Not decided**;
the line was written for a winner and a loser and got one each.
Both defaults stay.

**What the run found instead, mechanical.**  Neither arm reached the
hand answer on the secretion question or the reviews question: zero
and zero, zero and one, and neither cited the notes page that is the
hand answer, though both pages are in the store.  The keyword step
is why, and it is the vocabulary prompt's cost, the mirror of its
gain on the third sheet.  Asked about *secretion*, it produced low
keywords *the tree, the-tree-meets-people-on-pull, the-tree-withers,
spec/north_star.md, board/README.md, doc/method.md* — six names from
the vocabulary and not the question's own word, which is in no list
of the 150 most-cited names because it is rare, and rare is what
makes it the right keyword.  Asked about the *reviewing guest*, the
same: the keeper's pages and the rules, not *reviewer*.  The answer
to q2 then opens by saying the context does not use the word.  Told
to prefer the tree's names, the model preferred them over the
question.  The bare prompt would have kept *secretion*; the third
sheet showed bare loses *the tree*.  The seventh sheet, if there is
one, tests the union: the question's own rare words kept as low
keywords beside the vocabulary's names — one line in the prompt,
and a prediction that q2 and q3 here reach their notes pages.

**The judge worked.**  Shared-with-the-hand-answer separated poor
from poor honestly, at zero to two of seven to eleven, where the
first-answer judge had rewarded hubs.  Kept for the seventh.

**Predictions.**  B at least as many on two of three: yes, by the
letter, and so was the control.  Both cite the notes page on two of
three: no, one of three each.  Both cite `doc/method.md` or
`manifesto.md` on all three: no — control once, B never; the theme
channel under rarity carries fewer hubs than predicted.  Cost about
$0.50: $0.46.

**His reading of these six** goes below when he gives it, and his
reading of the fifth sheet's arms stands above: *"the B answers
seemed slightly better than the A answers.  Though, it depended on
what was asked."*
