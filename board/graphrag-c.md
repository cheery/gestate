# graphrag-c — a subject graph over the tree, self-referential until it earns a citer

    status   open — 2026-09-11
    because  a global question about the tree — what has been found, what
             does the journal say about X — is answered by a session reading
             fifteen files chosen by hooks, a map-reduce done by hand; and
             `card:GraphRAG.md`'s run showed the citations cluster by
             *subject* where the directories sort by *kind*, so the map a
             global question needs is one the tree does not draw.  *The
             session's reading; his decision is the `asked` line.*
    asked    Henri, 2026-09-11 — "ok. Tehdään C, ja järjestetään se siten
             että graafi on toistaiseksi vain itseviittaava, eikä siihen
             viitata vielä ulkopuolelta.  Ja ajetaan pilotti."
    see      card:GraphRAG.md — the measurement this follows, and its trigger
             for this card, overridden by his decision above
             doc/notes/notes-on-the-find.md — the conversation: what C is,
             what it requires, and why the graph must not become evidence
             doc/trial/graphrag-pilot.md — the pilot's sheet, before the run
             tools/graphrag.py — the tool
             test/test_graphrag.py — the gate that keeps the graph
             self-referential
             doc/memory/the-evaluation-loop.md — why nothing the graph says
             is evidence

## What this is, what it is not, and when it runs

**A derived layer, in one directory, that nothing outside it cites.**
GraphRAG proper (Edge et al., 2024) on the tree's documents: entities
and relations extracted by a model, communities over them, a written
summary per community, and a global query answered by map-reduce over
the summaries.  Everything it produces lives under `doc/graph/`, with a
stamp saying which commit and which model produced it.

**It is not evidence, and the gate says so mechanically.**  No file
outside `doc/graph/` may cite a file inside it other than
`doc/graph/README.md` — the door — and `test/test_graphrag.py`
refuses the commit that does.  A summary is a model's testimony about
the tree; a global answer over summaries is testimony squared
(`doc/memory/the-evaluation-loop.md`).  The day something outside
needs to cite in is the day this card's successor is written, with the
`because` that earned it.

**It is reversible by construction.**  `git rm -r doc/graph/`, the
tool, the test and this card, and the tree is as it was: no word in the
five rule documents, no new vocabulary, no spec contract.  The cache of
model outputs lives outside the repository (`~/.cache/gestate/graphrag/`),
keyed by file hash and model id, so a rerun costs only what changed.

**When it runs:** by hand, from a session's shell, with the API key in
the environment; never at commit, never in the suite.  The suite holds
only the door rule and the tool's own mechanics.

## The pilot, first — day one

Ten files, two models, one prompt.  `doc/trial/graphrag-pilot.md` is
the sheet and passes `tools/prereg.sh` before a call is made.  What
the pilot decides: which model does the extraction pass over 1.4 M
tokens of documents — Haiku, at roughly a third of Sonnet's price, or
Sonnet.  What it measures, mechanically: entities and relations found;
the fraction of entity names that occur in the source text
(*grounding* — an entity the text does not contain is invented);
overlap between the two models' entity sets; tokens and cost from the
API's own usage figures.  What it leaves to Henri: reading one file's
two extractions side by side.

## The pilot ran — 2026-09-11, the same evening

`doc/trial/graphrag-pilot.md` §"After the run" has the numbers.  The
decision: **extraction on Haiku** — grounded 1.000 against Sonnet's
0.975, overlap 0.625, a sixth of the cost, and the two invented names
in the pilot were both Sonnet's.  Two things the sheet did
not predict: Sonnet needs a 16k output ceiling or it is cut off and
scored as empty, and Sonnet 5 refuses `temperature`, so the arms ran
at different settings.  Total spent about $1.50 of the $14, at
assumed prices.  Henri read one file's two extractions side by side
the same evening — his reading is below when he gives it.

## The build, after the pilot — in the order the pieces earn a caller

1. **`extract`** — every document under `doc/`, `spec/`, `board/`,
   the root and the journal, chunked, one call per chunk, cached.
   Code (`gestate/`, `test/`, `shell/`) is left out on day one: the
   atlas already maps it by subject and it is more than half the
   tokens.
2. **`communities`** — over the entity graph, reusing
   `tools/communities.py`'s Louvain, levels exposed.
3. **`summarise`** — one page per community per level under
   `doc/graph/`, stamped with commit and model, regenerated when the
   community's members change; a lamp, not a gate, says when a page is
   behind.
4. **`query`** — map over the summaries, reduce once; the answer is
   printed with the sentence *this is a model's reading of a model's
   summaries* on it, and is never written into the tree by the tool.

## Questions

1. **Cache in the repository or outside?**  Outside keeps the tree
   clean and makes a fresh clone pay again; inside makes the extraction
   a committed specimen, several megabytes that rot.  Default: outside,
   and the pages under `doc/graph/` are what is committed.  *Open.*
2. **Which model for summaries and the reduce step?**  Default: Sonnet,
   because there is judgment in a summary and forty calls cost about a
   dollar.  The pilot may change the extraction model, not this.
   *Open.*
3. **Embeddings for local search, or backlinks?**  Default: none —
   backlinks already does the local move deterministically.  *Open,
   and not before the global query works.*

## What would kill it

The backlinks lamp's own measure, applied here: if no session follows a
`doc/graph/` page in a month of the pages existing, the layer is a
document alive once and comes out.  The `--check` of `tools/graphrag.py`
will print that count when there are pages to count.
