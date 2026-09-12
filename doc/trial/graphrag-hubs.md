# graphrag-hubs.md — the fourth sheet, before a hub has been kept from hopping

*Written 2026-09-12 for `card:graphrag-c.md`, after three sheets each
fixed one question and broke another, and agreed on one cause.
`tools/prereg.sh doc/trial/graphrag-hubs.md` must pass before a call.*

**The one thing this tests.**  A document is an entity in this graph
like any other, and the most-cited documents are hubs: `manifesto.md`
has relations to hundreds of things.  When a low keyword matches a
document, the retrieval hops from it — up to twelve of its strongest
relations, each bringing its far entity and its descriptions — and
one hub's neighbourhood is most of a 40,000-character budget.  The
third sheet's q2 named five hub documents as low keywords and lost
all five prior-art names to their hops.  The change: **a low-keyword
match on a document-type entity contributes the document and its
descriptions, and does not hop.**  Subjects, people, tools and the
rest hop as before; relations matched by theme are untouched.

**question:** does keeping hub documents from hopping let one setting
of the query hold all three questions at once — q2's names, q3's
documents, q1's documents — where each earlier sheet held two?

**decision:** two arms, both with the split ranking and hubs kept
from hopping: bare keywords, and vocabulary keywords.  If **either
arm** has q2 naming at least three of the five prior-art names *and*
q3 citing at least 7 of its first answer's 14 documents *and* q1 at
least 4 of its 8, that arm's three settings become `query`'s default
together, and the second and third sheets' open conditions are closed
by it.  If both arms satisfy all three, the bare one is the default,
being the cheaper call.  If neither does, hubs' hops were not the
whole cause, the option stays an option, and the next sheet is the
relation ranking — common tags such as *reference* and *methodology*
outrank nothing today, and a rare tag should.

**control:** the two split-ranking runs already on the tree — bare
keywords, `doc/trial/graphrag-ranking/split-q*.md`, and vocabulary
keywords, `doc/trial/graphrag-keywords/vocab-q*.md` — each against
its arm with the same keywords, the same cached keyword replies, the
same models, budget and answer prompt, on the api as they were, so
each pair differs in the hop rule alone.  Mechanical judge as before:
distinct documents cited against the first answers, the five-name
grep on q2, citations resolving and sentences without one.  The
person is Henri, not blind.

**n:** 3

**prediction, before the run** (the session's): the bare arm keeps
q2's five and q1's six and does not move q3, whose bare keywords
match no document, so it fails on q3 at 4 of 14.  The vocabulary arm
keeps q3's nine and lifts q2 from none to two or three, not five,
because the relations half under its keywords is crowded by rows
tagged *reference* and *methodology*, which the hop rule does not
touch.  So the likeliest outcome is **not decided with a lesson**:
hubs' hops were half the cause and the relation ranking is the other
half.  Cost about $0.50 in all.

**what is not decided here:** the relation ranking, the budget, the
answer's length, and the month's count.

## After the run — 2026-09-12, nothing above this line edited

**Both arms produced contexts byte-identical to their controls**, so
both answer calls were served from the cache and the six files under
`doc/trial/graphrag-hubs/` are the controls' answers again.  Checked
by rebuilding the four contexts with each hop rule and comparing.

**The decision line, read as written.**  Neither arm moved any
number, so neither satisfies the three conditions; **not decided**,
the option stays an option, and by the sheet's own fallback the next
sheet is the relation ranking.  The prediction was *not decided with
a lesson*, and the lesson is not the one predicted.

**The lesson, mechanical.**  Under the split ranking, **no hop entity
has ever reached the context** — not in this sheet, not in the second
or the third.  What fills the entity half is the theme channel: about
a thousand entities matched because one of their relations carries a
theme tag, ranked within their group by how many documents name them,
and the first forty-five of those are the tree's hubs — twenty to
twenty-eight of the fifty entities in every cut are typed *document*.
Whether a hub hops is moot when its hop never fits.  The hubs enter
through the *high* channel, and by document count.

| cut of 40,000 chars | entities in it: low / high / hop | typed document | relations in it |
|---|---|---|---|
| q1, bare keywords | 1 / 49 / 0 | 20 | 132 of 2,187 |
| q2, bare | 8 / 45 / 0 | 22 | 121 of 5,545 |
| q2, vocabulary | 5 / 45 / 0 | 24 | 111 of 5,319 |
| q3, vocabulary | 1 / 53 / 0 | 28 | 141 of 2,732 |

So the fifth sheet, if there is one, tests the theme channel's own
ranking: an entity reached by theme ranked by **how many of its
relations carry the question's tags**, not by how many documents name
it; and a relation ranked by the rarity of the tag it shares, so that
*prior art* outranks *reference*.  One thing each, one sheet each,
with the same three questions and the same judges.

**One defect found on the way**, in the store and not the query: an
entity named `doc/memory/` normalises to the empty key — `norm`
strips that prefix — and sits in twenty documents under no name.
Noted for the tool; not fixed under a running sheet.

**Predictions.**  Bare arm holds q2 and q1 and not q3: it held
everything, exactly.  Vocabulary arm lifts q2 to two or three: no,
none, nothing moved.  Cost about $0.50: **$0**, every answer cached.
