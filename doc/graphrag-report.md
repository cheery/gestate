# A subject graph over a working tree — what was built, what it found, what held

*A report for a reader outside the project, written 2026-09-12 by the
session that did the work, at Henri Tuhola's ask.  Everything here
has a file behind it in the repository; where a number is given, the
command that reproduces it is given too.  The reader should know the
loop before reading: a session judging a method it is part of is a
product of that method, so quality is reported as a person's reading,
labelled, and never as the session's opinion.*

## The setting

The repository is gestate, an audio programming environment, and
around its code a second thing has grown since August 2026: a tree
of documents — specifications, a board of cards, a journal, a memory
directory, trial sheets — kept by one person and worked by AI
sessions that do not remember one another.  The tree conditions each
session through rules held by a test suite rather than by prose.  By
September it held **261 documents, 1.15 million tokens of text**, and
a global question about it — *what has been found here, what are the
method's neighbours, what is this tree* — took a session with grep and
the memory index an afternoon to answer, reading fifteen files chosen
by hooks.

The question was whether a graph extracted from the documents by a
model could answer such questions faster and find what a hand-read
misses, without becoming a second source of truth.  That last clause
is the design constraint: **the graph is a finder, never a source.**
Nothing outside its directory may cite it, a test refuses the commit
that does, and what the graph finds is written into the tree citing
the document it pointed at.

## Two papers, and what each was worth

Microsoft's GraphRAG (Edge et al., 2024) was the starting point: entity
extraction, communities, community summaries, a map-reduce over the
summaries at query time.  Its initialisation was heavy and its
summaries go stale whenever a community's membership moves, which
Louvain does on every rerun.

**LightRAG** (Guo, Xia, Yu, Ao, Huang, arXiv 2410.05779) keeps the
extraction and drops everything after it: no communities, no
summaries; a query is one small call for keywords at two levels — the
specific things the question names, and its themes — matched to
entity names and to keywords carried on relations, one hop, and one
generation call.  New documents are unioned in and nothing is
regenerated.  This was adopted.  What the paper does not address, and
what cost the most time here, is that its keyword step is a model
reading the question with no knowledge of the corpus's own
vocabulary.  Its quality claims rest on a model judging a model and
its win rate against GraphRAG is near parity; the cost argument is
structural and held.

**KET-RAG** (Huang, Zhang, Xiao, KDD 2025, arXiv 2502.09304) extracts
only the central fraction of a corpus, ranked by PageRank on a
chunk-similarity graph, and shows that a keyword-to-chunk graph with
no model beats GraphRAG on local retrieval coverage at a hundredth of
the cost.  Its evidence is exact-match on multi-hop question sets,
stronger than a judge.  Two things were taken: the order — the
extraction runs the most central documents first, by PageRank over
the tree's own citation graph, so a run stopped by a budget leaves
out the periphery and not the end of the alphabet — and the support
for keeping the local move deterministic.  The fraction was not
taken, because a global question needs the whole corpus.

## What was built

One Python file, standard library only, 1,583 lines with 368 of
tests: `tools/graphrag.py`.  The pieces, in the order they earned a
caller:

| piece | what it is | model? |
|---|---|---|
| `extract` | every document chunked at ~3,000 tokens, one call per chunk, reply cached by model, prompt version and chunk text; a changed chunk is the only thing a rerun pays for | Haiku 4.5 |
| `lookup` | one subject across every document: its descriptions merged by normalised name, its relations, its documents | no |
| `subjects` | subjects named in six or more documents that no filename, heading or memory hook titles | no |
| `contradictions` | one subject, descriptions quoting a number with a unit in two or more documents where no two agree, each dated by last commit | no |
| `cue` | for the file just read, the subjects it shares with two to twelve other documents the citers list did not show; appended to the repository's existing "who cites this" hook | no |
| `lamp` | at commit: how stale the graph is; for each changed document its contradictions; for each new document the subjects it names that already live elsewhere | no |
| `query` | LightRAG's dual-level search: keywords, two-level match, one hop, one answer, every claim citing a document, citations counted | Haiku + Sonnet 5 |

Two backends share one cache: the Anthropic API, and `claude -p` on a
subscription.  The first run went through the API for speed; every
call since has gone through the subscription, and a reply is found
from either.

## The extraction, by the numbers

| | |
|---|---|
| chunks | 535, of 261 documents |
| entities, raw / merged by name | 14,657 / 5,591 |
| grounded — the entity's name occurs in its chunk | 0.990 |
| relations, every one carrying theme keywords | 11,399 |
| tokens in / out | 1.48 M / 1.62 M |
| time, six workers | 65 minutes |
| cost at $1 / $5 per million | **$9.57** |
| replies that were not valid JSON | 6 of 535, all salvaged object by object |
| the incremental update, tested the same hour | a card edited under the run: one call |

A pilot the day before — ten files, Haiku against Sonnet, a
pre-registered sheet — had chosen Haiku for extraction: grounded
1.000 against 0.975, entity overlap 0.625, a sixth of the price, and
both invented names in the pilot were Sonnet's.

    python tools/graphrag.py check          # how much of the tree the graph has read; no call
    python tools/graphrag.py extract        # the increments, on the subscription

## What the deterministic reads found on the first morning

These need no model at query time and were right first time.

- **`subjects`**: 10 of 89 well-cited subjects have no title anywhere.
  Six are the language's identifiers, defined in code the graph does
  not read.  One is real: **Toyota Production System**, named in
  seven documents and titled in none — the method's source, which
  the tree had already filed as the author's to credit.  The graph
  found a thing the tree knew and had not written down, which is the
  shape the tool was built for.
- **`contradictions`**: 15 pairs.  The one the pilot had used as its
  example — the rules cap at 2000 lines in one file and 2500 in
  another — came out by arithmetic.  Seven are line counts quoted
  about documents that have since grown.  One checked and found not
  real: a dated quotation, which is what that page is for.
- **`lookup Rizzo`**: six documents' descriptions of one calculus
  merged into a paragraph no single file holds — its source paper,
  its role in the language, its type formers going into another
  system, a name collision noted in the journal.  The author's
  reading: *"it feels like some sort of brains at this point."*

## The query, and seven sheets in one day

Every arm ran behind a pre-registered sheet — question, decision,
control, n, prediction — checked by `tools/prereg.sh` before a call,
and read as written afterwards.  Three global questions with hand
answers already on the tree were the samples; the mechanical judge
was citations resolving and sentences without one; the person was
the author, not blind.

| sheet | the one thing tested | result |
|---|---|---|
| 1 | does the query add anything to an afternoon's hand answer | 32 of 32 citations resolve; two of three added, none invented, by his reading — **the query stays** |
| 2 | half the budget to relations, matched entities first | five of five prior-art names where the old ranking had none; q3 lost documents; not decided |
| 3 | the corpus's own vocabulary handed to the keyword step | *what is this tree* read as *the tree* at last; the neighbours question fell to none; not decided |
| 4 | hub documents kept from hopping | byte-identical contexts: **no hop had ever reached the context**; not decided |
| 5 | the theme channel ranked by evidence and tag rarity | five of five again, the richest answer of the day; the judge was found to reward hubs; not decided |
| 6 | three new questions judged by their hand answers | a winner and a loser and a tie; the vocabulary drops the question's own rare word; not decided |
| 7 | the question's own words kept beside the vocabulary | shares at least as many with the hand answer on three of three, cites the notes page on two — **decided; the defaults** |

What the seven agree on, and what a reader building the same thing
should take:

1. **The store held what every question needed, every time.**  Each
   failure was retrieval — the keyword step, the ranking, the budget —
   never the graph.
2. **Without a split budget, the second level of a dual-level design
   is retrieved and thrown away.**  The first trial's answers saw
   entities only, ranked by document count: the hubs.
3. **A corpus has a vocabulary and the keyword step does not know it.**
   Handing it the store's most-cited names fixed *the tree* and broke
   *secretion*, because a rare word is exactly the right keyword and
   exactly what a most-cited list lacks.  Keeping the question's own
   words beside the list was the one change that held.
4. **Hubs enter through the theme channel by document count**, not
   through hops.  Ranking that channel by how many of an entity's
   relations carry the question's tags, weighted by tag rarity, gave
   the best specific answers.
5. **A sheet's judge must not be built from the mechanism under
   test.**  Keeping the first trial's documents rewarded hubs.  A hand
   answer written first, for other reasons, is the judge that worked.
   And a sheet over data that already exists is post-hoc; the sixth
   took new questions whose hand answers the tree already held.

Cost of the seven: about $2.50.  The author's readings across them:
*spot on*; *more informative, maybe too dense*; *naming real things
while drawing conclusions that do not entirely hold*; *B slightly
better than A, though it depended on what was asked*.

    python tools/graphrag.py query "How does TPS manifest inside this project?"

## How it sits in the work

By the evening the author's direction was that the graph should be
internalised rather than queried: *"rather than run queries separately
so much or write down what it answers."*  What arrives on its own:

- **On every read**, the repository's existing hook that answers
  *who cites this file* now ends with the graph's line — *this file
  shares X with A, B* — offering routes the citers list did not show.
- **At every commit**, a lamp: how many chunks the graph has not read,
  a changed document's contradictions, a new document's subjects
  already at home elsewhere.  Half a second, no call, never refuses.

Each line is a fire in a log, and a follow is counted — a later read
of an offered file, a later change to a named document — so a line
nobody follows in a month comes out.  The honest floor is zero and
both counts started that evening.

## What is not claimed

- Nothing the graph says is evidence.  An extraction is a model's
  reading of a file; an answer is a model's reading of an extraction.
  The door rule is mechanical for that reason.
- The entity typing is loose: dates typed as events, code identifiers
  as concepts, a word like *wait* as a subject.  Two exclusions were
  added and no more; the follow counts decide the rest.
- An emotion is not an entity.  Asked what emotions the tree holds,
  the graph answered thin, because the extraction prompt asked for
  the entities and relations of a software project; a grep for plain
  words found doubt in 24 files and trust in 29.  The first found
  limit of the store, and the first thing a later prompt version
  changes.
- This is not seed material for a new project.  A small tree answers
  a global question with grep in a minute; the trigger for building
  this is the afternoon by hand, and what transfers before that is
  the shape — a derived layer nothing cites, a door held by a test,
  lamps with follow counts, a sheet before any arm — not the tool.

## Where to read further

The card `card:graphrag-c.md` carries the arc in order with the
author's words dated; the sheets are `doc/trial/graphrag-*.md`; the
closed measurement that preceded it is `card:GraphRAG.md`; the
journal entries are dated 2026-09-11 and 2026-09-12.  The tool's
docstring is its manual.
