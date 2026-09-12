# graphrag-themes.md — the fifth sheet, before the theme channel has been ranked by its own evidence

*Written 2026-09-12 for `card:graphrag-c.md`, after the fourth sheet
measured what fills the context under the split ranking: about fifty
entities, forty-five of them from the theme channel ranked by
document count, so the hubs, and no hop at all.  `tools/prereg.sh
doc/trial/graphrag-themes.md` must pass before a call.*

**The two things this tests, as two arms.**  Today an entity reached
through the theme channel — one of its relations carries a tag the
question's themes share a token with — is ranked among its peers by
how many documents name it, which is a measure of being a hub and
not of being about the question.  And a relation is ranked by how
many theme tokens it shares, then strength, so a row tagged
*reference* and one tagged *prior art* tie when the question asked
for both, and *reference* is on 900 rows.

- **Arm A, entities by evidence:** an entity reached by theme is
  ranked by **how many of its relations carry the question's tags**,
  then by document count.  Relations as in the split ranking.
- **Arm B, A plus rarity:** a relation is ranked by the **rarity of
  the tags it shares** — the sum over shared tokens of log(rows ÷
  rows carrying that token) — then strength, so *prior art* outranks
  *reference*; and an entity's evidence is the same rarity-weighted
  sum over its relations rather than a count, so a hub with thirty
  *reference* rows does not outrank a citation with three *prior art*
  rows.  *Made precise while writing the test, before any call.*

Both keep the split budget, the vocabulary keywords, everything
else.  Vocabulary rather than bare because under vocabulary q3 held
and q2 fell through this channel, which is the failure the sheet is
about; bare's q3 fails at the keyword step, which no ranking reaches.

**question:** does ranking the theme channel by its own evidence let
the vocabulary keywords hold all three questions at once?

**decision:** if either arm has q2 naming at least **three of the
five** prior-art names, q3 citing at least **7 of 14** of its first
answer's documents, and q1 at least **4 of 8**, that arm with the
split budget and the vocabulary keywords becomes `query`'s default
together, closing the second, third and fourth sheets' open lines.
If both arms do, B is the default, the sheet having predicted it.
If neither does, the theme channel's ranking was not the cause
either, both stay options, and the next thing is the budget itself —
40,000 characters was a number a session picked, and `fixme.md` F169
says what that is worth.

**control:** the third sheet's arm, `doc/trial/graphrag-keywords/vocab-q*.md`
— split budget, vocabulary keywords, the same cached keyword replies,
the same models, budget, answer prompt, and the api — so each arm
differs from it in the ranking of the theme channel alone, and B
differs from A in the relation ranking alone.  Judges as before,
mechanical and Henri.

**n:** 3

**prediction, before the run** (the session's): A lifts q2 to two or
three and holds q3 at nine and q1 at six; B lifts q2 to four or five
because the *Citation for …* rows share the rare tag *prior art* and
rise above the *reference* rows, and holds the other two.  B decides.
Cost about $0.50; the keyword calls are cached.

**what is not decided here:** the budget, the answer's length, the
`doc/memory/` empty-key defect, and the month's count.

## After the run — 2026-09-12, nothing above this line edited

The arms' answers are `doc/trial/graphrag-themes/a-q*.md` and
`b-q*.md`, written by the shell from the tool's output.

| | control: split + vocabulary | A: entities by evidence | B: A + rarity |
|---|---|---|---|
| q2 prior-art names of five | 0 | 0 | **5** |
| q2 distinct documents; citations; uncited | 13; 12; 1 | 12; 11; 2 | 14; 13; 2 |
| q3 documents kept of the first answer's 14 | 9 | 6 | 6 |
| q1 documents kept of the first answer's 8 | 6 | 4 | 3 |
| relations in the context, q1 / q2 / q3 | 112 / 111 / 141 | 111 / 111 / 141 | 113 / 111 / 141 |

**The decision line, read as written.**  A fails q2 and q3.  B names
five of five on q2 and keeps 6 of 14 on q3 and 3 of 8 on q1, both
under the line.  **Not decided.**  Both stay options, both defaults
stay, and by the sheet's own fallback the next thing is the budget.

**What B's q2 is, mechanically.**  The richest answer to that
question in five sheets: the five ingredient citations, *jidoka* and
*genba* from the Toyota Production System in the manifesto and the
August journal, Alhanen's dialogue, set-based design, Garnet, Amulet,
Eve and Pad++ from the GUI memories, Datafun's monomorphic
sublanguage, and his own three tools — 13 citations resolving, two
sentences uncited.  Rarity did what the sheet said: *prior art* rows
rose over *reference* rows.

**A finding about the judge, not about the arms, and it is the
sheet's real result.**  The line asked each arm to keep the *first
answers'* documents, and the first answers came from a context
ranked by document count — so *keeping their documents* rewards
citing hubs.  Measured against the hand answer instead (`journal.md`
§"The specimen, the find, and the name", 13 documents), which the
line did not name and which is therefore information here and not a
verdict:

| q1 / q3 | documents cited | shared with the hand answer | of them hubs |
|---|---|---|---|
| first trial | 8 / 14 | 4 / 3 | 4 / 8 |
| control, split + vocabulary | 16 / 15 | 5 / 4 | 3 / 7 |
| A | 12 / 10 | 4 / 2 | 3 / 4 |
| B | 10 / 9 | 3 / 3 | 3 / 5 |

Every arm shares three to five documents with the hand answer on
each question, and the first trial's fourteen on q3 were eight hubs.
The number the line used cannot separate the arms, because it was
built from the thing the arms were meant to fix.  A sixth sheet
would keep the same three questions and judge q1 and q3 against the
hand answers' documents, which exist and were written first; that
is a change to the sheet and not to the tool, and it is written here
before any such sheet so that it cannot be read as chosen after.

**Predictions.**  A lifts q2 to two or three: no, none.  B lifts q2
to four or five: **five.**  B holds q3 at nine and q1 at six: no, six
and three.  B decides: no.  Cost about $0.50: about $0.50.

**His reading** goes below when he gives it.
