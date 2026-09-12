# graphrag-union.md — the seventh sheet, before the question's own words have been kept

*Written 2026-09-12 for `card:graphrag-c.md`, after the sixth sheet
found the vocabulary prompt makes the keyword step prefer the tree's
most-cited names over the question's own rare word.  `tools/prereg.sh
doc/trial/graphrag-union.md` must pass before a call.*

**The one thing this tests.**  The keyword prompt with the vocabulary
gains one sentence: the question's own specific words — a noun it
uses that names a thing, however rare — are always kept as low
keywords, beside whatever names from the lists fit.  *Secretion*
stays a keyword because the question said it; *the tree* is added
because the vocabulary knows it.  Nothing else changes: the themes
ranking, the split budget, the models, the budget, the answer
prompt.

**question:** does keeping the question's own words let the query
reach the hand answers the sixth sheet's arms missed, without losing
the question the vocabulary had won?

**decision:** the arm is `--keywords union --ranking themes`, on the
api.  Judged by the hand answers: if the arm shares **at least as
many** documents with the hand answer as the sixth sheet's B on two
of the three notes questions, **cites the notes page itself on at
least two of three** where B cited one, and on *What is this tree?*
shares at least three documents with `journal.md` §"The specimen, the
find, and the name" as B did — then union + themes + split becomes
`query`'s default, closing the second to sixth sheets' open lines,
with his reading of invention on the four answers still owed and
able to overturn it as the sixth sheet says.  If it fails the
notes-page condition, keeping the words was not enough, and the next
thing is the keyword model itself — Sonnet for the keyword call,
Q2's other half.  If it fails the tree question, the union is a
trade like the third sheet's and the sheet says so.

**control:** the sixth sheet's B arm, `doc/trial/graphrag-hand/b-q*.md`,
and for the tree question the fifth sheet's B, `doc/trial/graphrag-themes/b-q3.md`
— same ranking, same budget, same models, same answer prompt, same
backend, unchanged; the arm differs in the keyword prompt's one
sentence, and therefore in the keywords and everything after them,
which is what a keyword-step sheet must accept.  Mechanical judge as
the sixth sheet's: shared documents with the hand answer by the same
regular expression, the notes page cited or not, citations
resolving, sentences uncited.  The person is Henri.

**n:** 3

The tree question is run as a fourth, a regression check and not a
sample; the three notes questions are the samples.

**prediction, before the run** (the session's): the low keywords for
the secretion question include *secretion* and for the reviews
question *reviewer* or *review*; the arm cites the notes page on
secretion and reviews, shares two to four documents with each hand
answer, holds drift at one or two, and holds the tree question at
three.  Cost about $0.35.

**what is not decided here:** the answer's length, the budget, the
`doc/memory/` empty-key defect, the keyword model, and the month's
count.

## After the run — 2026-09-12, nothing above this line edited

The four answers are `doc/trial/graphrag-union/q1.md`–`q3.md` and
`tree.md`, written by the shell from the tool's output.

| | drift, of 11 | secretion, of 9 | reviews, of 7 | tree, of 13 |
|---|---|---|---|---|
| low keywords, the question's own words kept | *keeper*, *the tree*, six memory names | *the tree*, **secretion** | **reviewing guest**, **reviews**, **reviewer**, *project* | *the tree* |
| shared with the hand answer — B (sixth / fifth sheet) | 1 | 0 | 1 | 3 |
| shared with the hand answer — union | **3** | 0 | **2** | **3** |
| cites the notes page itself — B / union | yes / yes | no / **yes** | no / no | — |
| citations resolve / not; uncited — union | 13 / 1 (`~/tend`); 2 | 5 / 0; 4 | 5 / 0; 3 | 9 / 0; 6 |

**The decision line, read as written.**  At least as many as B on
two of three: **three of three** — 3 against 1, a tie at 0, 2 against
1.  The notes page cited on two of three where B cited one: **yes**,
drift and secretion.  The tree question at three: **three.**  All
three conditions hold, so **union + themes + split becomes `query`'s
default**, the second to sixth sheets' open lines close on it, and
his reading of invention on the four answers is still owed and can
overturn it, as the sixth sheet said and this one repeated.  The
first of seven sheets to decide.

**One thing about the judge, fixed under the sheet and said.**  The
secretion answer cites its notes page as `notes-on-secretion.md`, a
bare basename, which is how the tree itself accepts a citation when
the name is unique (`tools/backlinks.py`), and the tool's checker
counted it as not resolving.  The checker now applies the tree's
rule, with a test; the file was regenerated from the cache and its
footer reads 5 resolve, 0 do not.  The decision above was reached
counting the page as cited before the checker changed, because the
sheet's condition is *cites the notes page itself* and the page was
cited; the checker's opinion was never the condition.

**What the run did not fix.**  Secretion still shares no document
with its hand answer beyond the page itself, and the reviews answer
did not cite its page; the words reached the door and not the room.
Two to four sentences an answer still carry no citation.  Those are
the next sheets' questions if there are any, and the card names
what comes before them: the month.

**Predictions.**  *Secretion* and *reviewer* among the low keywords:
yes, both, and *reviewing guest* too.  The notes page cited on
secretion and reviews: secretion yes, reviews no.  Two to four
shared on each: 3, 0, 2 — one of three inside the range.  Drift held
at one or two: three.  The tree at three: three.  Cost about $0.35:
$0.33.

**His reading of the four** goes below when he gives it.
