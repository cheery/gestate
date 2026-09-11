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

## `extract` is running — started 2026-09-11, evening

Henri: *"ajetaan extract cli-taustalla. neljä rinnakkain, kyllä."*
The cli backend — `claude -p` with the key unset so the subscription
pays in usage, `--effort low`, four workers — over 260 documents in
533 chunks, 1.14 M tokens of text plus about 8.6 k tokens of the
CLI's own context per call.  Log and store are outside the tree:
`~/.cache/gestate/graphrag/extract-haiku-cli.log` and
`extract-haiku-cli.json`; the pid is in `extract.pid` beside them.
The store is rewritten every 25 chunks, so an interrupted run resumes
from the per-call cache for nothing.  What it cost and what it found
go below when it ends.

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
4. **`query`** — the global search: map over the summaries, reduce
   once; the answer is printed with the sentence *this is a model's
   reading of a model's summaries* on it, and is never written into
   the tree by the tool.  **Decided to be built and tried, 2026-09-11,
   by him** — see the plan's order above.

## The first run was stopped by the sitting limit, and the tool cached the stop — 2026-09-11, 21:01

At 20:48 the sitting limit — `tools/limit.sh --hook`, a
UserPromptSubmit hook in this checkout's `.claude/settings.json` —
began refusing every headless `claude -p` the extraction made, because
a `claude -p` started in the project directory inherits the project's
hooks.  Each refusal came back in 1.5 s with zero tokens and the hook's
message as the result, and `_call_cli` accepted it as a reply and
cached it: **276 chunks were marked extracted with no extraction in
them**, and `check` counted them as current.  Found at 21:01 by a
count that could not be true — 310 chunks in 17 minutes at 93 s a
call — and by reading one cached reply.  Three repairs, all in the
tool: the subprocess runs with the cache directory as its working
directory, outside every hook; a reply with no output tokens or no
object in it is a failure to retry and never a thing to cache; the
tool writes its own pid, because the scheduled kill at 21:00 took the
`nohup` shell and left the run going.  The 276 were purged from the
cache by hand; 71 real extractions stand, 462 remain for tomorrow.

*The sitting limit did what it is for — a person's hours are the
person's — and it is the mechanism that stopped a batch job nobody
had told it about.  `doc/memory/headless-claude-inherits-the-hooks.md`.*

## How the graph proves its value — the plan, 2026-09-11

**The principle: the graph is a finder, never a source.**  The door
stays.  What the graph finds is written into the tree citing the
document the graph pointed at, never the graph; the journal entry says
*found by the graph*.  So the graph's value shows in the tree only
indirectly — memories, cards and corrections whose `see` line points
at a document and whose story names the graph — and that can be
counted: how many a month.  `card:backlinks.md` proved its value the
same way, by a lamp that counted follows, not by feeling useful.

**Four ways, cheapest first, and the order they are tried:**

1. **Subjects nobody named — no model, the evening `extract` ends.**
   `entities --top 50`: the entities the most documents name, against
   the memory index, the cards and the specs.  A subject in twenty
   documents with no name in the tree is `card:GraphRAG.md`'s *rule
   stated twice* at the level of subjects rather than files.  One such
   that Henri recognises as real is a caller, before any summary.
2. **Contradictions across documents — no model.**  One entity,
   descriptions that disagree between documents of different dates:
   the pilot's own *2000-line cap* against *2500-line cap* is the shape,
   and there the tree knows the change.  What the gates cannot see is
   a claim changed in one file and left standing in another.  A list
   for the keeper's evening; the number is *how many real*.
3. **The global-question trial — sheet first, after summaries.**  The
   three questions answered by hand on 2026-09-11 (what was found, the
   neighbours, what the tree is), put to the graph.  Control: the
   afternoon's method, a session with grep and the memory index,
   timed.  Judge in two halves: mechanical — every claim in the answer
   cites a document and the citation resolves, the tree's own rule —
   and Henri's blind reading of which answer found what the other did
   not and which invented.  n = 3.  Kill: if the graph adds nothing the
   hand-read found in the same time in two of three, the query layer
   comes out and `lookup` stays.
4. **A cue at the moment — last.**  `doc/notes/notes-on-cues.md`'s
   constraint: a cue must reach the context.  The backlinks hook's cut
   line, *… and 139 more*, could carry a subject's name from the
   store, deterministically; the measure is the one the hook already
   has, whether the line is followed.  Last because it touches a hook
   that works.

**In order, once `extract` has run:** communities (free,
`tools/communities.py` is there); then 1 and 2 in one evening without
a model; **then the summaries and the global search, and 3 with a
sheet — regardless of what 1 and 2 found.**  *A session wrote this
paragraph first as a gate — summaries only if 1 and 2 yielded
something — and Henri struck it the same night, 2026-09-11: "Onko
siinä kortissa nyt sitten merkattuna että etenemme myös siihen
'global search' vaiheeseen jotta voimme kokeilla sitä?"  His reason
is the card's: "Saamme selville onko graphrag hyödyllinen meille vain
kokeilemalla.  Ja näin me kokeilemme."*  So the global search is
built and tried; what 1 and 2 find goes into its sheet as the
baseline, not as a condition on it.  The cost is the summaries,
about forty Sonnet calls, a dollar at list or the same in usage.

**The loop, said aloud.**  A session judging the graph's answers is a
product of the same tree and of the same model family as the
extractor.  So in 3 the judge is Henri's blind reading and the
mechanical citation check, never a session's opinion of the answer's
quality (`doc/memory/the-evaluation-loop.md`).

## Keeping it current, once it is here

**Extraction is incremental by construction.**  Every call is cached
by model, backend, prompt version, ceiling and the chunk's own text
(`cache_path_for`), so `extract` after a week of commits calls only
the chunks whose text changed and pays only for those — a few cents a
day at list — and `graphrag check` says without calling anything how
many chunks a run would call.  A prompt change re-extracts everything,
and `PROMPT_VERSION` is bumped by hand for that reason: it is a $30
decision, not a tidy-up.  A renamed file re-extracts once, because the
path is in the prompt; the journal's monthly rotation is one such.

**Communities are recomputed, never stored** — seconds, from the
store.  **Summaries are regenerated per community when its member set
changes**: each page under `doc/graph/` carries the commit, the model
and a hash of its members, and a lamp — not a gate — lists the pages
whose members have moved since.  **It runs by hand and on a cadence**:
the keeper's evening, `keeper.md`, is the natural place, and never the
commit hook, because it costs money and minutes.  A page behind its
members is a lamp lit, the same standing as the atlas's stamp
(`doc/memory/gestate-atlas.md`), and the graph is allowed to be a week
stale — what it is not allowed to be is stale without saying so.

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
