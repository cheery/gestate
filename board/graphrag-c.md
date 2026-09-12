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
             arXiv 2410.05779 — LightRAG (Guo, Xia, Yu, Ao, Huang, 2024),
             the shape the query layer takes since 2026-09-12

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
2. ~~**`communities`**~~ and 3. ~~**`summarise`**~~ — *struck
   2026-09-12*, §"LightRAG instead of summaries" below.  Communities
   were there to be summarised; with no summaries nothing on the build
   path needs them, and `tools/communities.py` stays what it was, a
   lamp over the citation graph.
4. **`query`** — the global search, in LightRAG's shape: one small
   call turns the question into keywords at two levels, the specific
   ones matched to entity names, the abstract ones to the keywords on
   relations; one hop of neighbours; one generation call over the
   matched descriptions, each pointing at its document.  The answer is
   printed with the sentence *this is a model's reading of a model's
   extraction* on it, and is never written into the tree by the tool.
   **Decided to be built and tried, 2026-09-11, by him** — see the
   plan's order above; the shape changed on 2026-09-12, the reasons
   did not.

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

## LightRAG instead of summaries — 2026-09-12

**Henri, the morning after the first run stopped:** *"I have to say
it's really heavy to initialise.  I wonder whether this paper
[arXiv 2410.05779] would help us make a lighter solution that's be
easier to keep up to date."*  And on the session's reading of it:
*"ok.  Lets do them."*

**What the paper is.**  LightRAG (Guo, Xia, Yu, Ao, Huang, 2024):
the same extraction as GraphRAG — chunks, one call per chunk, entities
and relations with descriptions, merged by name — and then it stops.
No communities, no community summaries, no map-reduce at query time.
A query is one small call that turns the question into keywords, a
match of those against entity names (low level) and against keywords
carried on relations (high level), one hop of neighbours, and one
generation call over the matched descriptions.  A new document is
unioned into the graph and nothing is regenerated.  The paper's own
cost section says the indexing overhead is GraphRAG's; the saving is
after extraction, and it is structural.

**What it lightens here, and what it does not.**  The heaviness he
felt is extraction on the CLI backend — 8 k tokens of the CLI's own
context per call and about 10 k output tokens a chunk, most of it
thinking — and the paper changes none of that; the backend would
(the session's estimate for the remaining 486 chunks: about 3 h and
10 M subscription tokens on the CLI, about 1 h and $8 at assumed
prices on the API).  What it removes is the one piece of the plan
that was not incremental: summaries regenerated whenever a
community's member set moved, and Louvain moves members on every
rerun, so that lamp would have been lit most weeks.  The tree already
had the rest of LightRAG without meaning to — the chunk-hash cache is
its incremental update, `merged()` its deduplication, the entity
descriptions its profiling, `lookup` its low-level retrieval, the
chunk-to-file link the pointer a finder needs (and the paper's own
ablation, *-Origin*, found the original text adds nothing to the
answer, which suits a graph that is never a source).

**What the paper does not earn.**  Its quality claims are an LLM
judge scoring answers from the same model, the loop
`doc/memory/the-evaluation-loop.md` refuses; against GraphRAG the
overall win rate is 52–54 % on three corpora and 49.6 % on the fourth,
which is parity.  The cost argument needs no judge.  And the thing
communities buy that keyword matching cannot is a whole-corpus view:
*what is this tree* has no keyword to match, and it is one of the
three questions in the trial below.

**What changed, the same morning, the session's work:**

- The prompt asks for `keywords` on every relation — one to three
  short phrases at the level a question would use — and
  `PROMPT_VERSION` is `2026-09-12a`.  Bumped while 49 of 535 chunks
  were paid for, which is when a bump costs least: the 49 are
  re-extracted, the per-call cache keeps their old replies, and the
  old store is set aside as `extract-haiku-cli.2026-09-11a.json`
  rather than carried, because a record without keywords is not what
  the prompt now produces.  `test/test_graphrag.py` holds both.
- Build steps 2 and 3 are struck; `query` is LightRAG's dual-level
  retrieval.  Keyword matching is string and token matching against
  a few thousand names until a real question defeats it — Q3's
  default stands.
- The trial in the plan's step 3 keeps its sheet, its control and its
  kill rule; only the arm under test changed.

**The trigger for summaries after all:** the dual-level query fails
the kill rule on the whole-corpus question specifically.  That is the
only question communities answer better by construction, and one
failure there is a reason to build them, not two failures elsewhere.

**The extraction is restarted by him, in his own terminal**, after
the new prompt was watched to work in the sitting: four chunks on the
CLI backend, 2026-09-12 morning — `fixme.md` and `README.md` gave 33
and 36 entities, 0.959 grounded, 60 relations and every one carrying
one or two theme keywords of the kind asked for (*specification
compliance*, *native code generation*), no parse error.  The old store
was set aside as `extract-haiku-cli.2026-09-11a.json` on the first
call, as designed.  Two numbers from those calls, for the reader who
restarts it: 112–132 s a call and 16–22 k output tokens for a 12 k-char
chunk, so the remaining 531 chunks are about four hours at four
workers and about 10 M output tokens from the subscription pot.  The
CLI's per-call overhead read 4.4 k tokens on one call and 0 on the
next where the evening before read 8 k on every call; observed, not
explained.

    python tools/graphrag.py extract --backend cli --workers 4 2>&1 | tee -a ~/.cache/gestate/graphrag/extract-haiku-cli.log
    python tools/graphrag.py stop        # finishes the calls in flight and leaves; rerun the same command to continue
    python tools/graphrag.py check       # how many chunks a run would still call

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

**His prediction, before any of it has run — 2026-09-11, late:**
*"Minä uskon että kohdat 1 ja 2 tuottavat jotakin todellista.  Tämä
tuntuu samalta kuin se backlinks -työkalu.  Käyttämällä sitä selviää
mitä arvoa sillä on."*  Written here so the result can be read
against it: `card:backlinks.md` was the same shape — built on a
`because` in a session's own words, proved by a lamp that counted
use, and the first evening's count was the number that settled it.

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

~~**Communities are recomputed, never stored** — seconds, from the
store.  **Summaries are regenerated per community when its member set
changes**: each page under `doc/graph/` carries the commit, the model
and a hash of its members, and a lamp — not a gate — lists the pages
whose members have moved since.~~  *Struck 2026-09-12: there are no
summaries to regenerate, which was the point of §"LightRAG instead of
summaries"; the store is the graph, and a changed chunk changes only
its own records.*  **It runs by hand and on a cadence**:
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
2. **Which model for the query's two calls?**  *reframed on 2026-09-12;
   there is no summary step.*  Default: Haiku for the keyword call, it
   is a list of phrases; Sonnet for the generation call, because the
   judgment is there and it is one call a question.  *Open.*
3. **Embeddings for keyword matching, or strings?**  *reframed on
   2026-09-12.*  The paper matches through a vector database; the
   default here is string and token matching against a few thousand
   names and relation keywords, no embeddings, until a real question
   in the trial is defeated by a synonym.  *Open, with that trigger.*

## What would kill it

The backlinks lamp's own measure, applied here: if no session follows a
`doc/graph/` page in a month of the pages existing, the layer is a
document alive once and comes out.  The `--check` of `tools/graphrag.py`
will print that count when there are pages to count.
