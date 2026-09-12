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

**Then he chose the API for the first run and the CLI for the
increments, the same morning:** *"I'd want to use api backend with
haiku and 6 workers, then later, do the incremental updates with cli.
Is that possible?  I still have about 14$ available and Haiku is
1$/5$ per MTok."*  It was not, as the tool stood: the cache and the
store were both keyed by backend, so the CLI would have seen none of
the API's replies and re-extracted everything.  So the session rekeyed
them — a reply is keyed by model, prompt version, ceiling and text,
the store is one file per arm, `extract-haiku.json`, and each reply
and record says which backend made it — and gave `extract` a
`--budget` in dollars at the assumed prices, the same stop as `stop`
pulled by the price table.  Watched in the sitting: two chunks fresh
on the API at 2 s a call, then the same two on the CLI, both
*(cached)*.  The estimate for the whole tree on the API: about
1.3 M tokens in and 1.3 M out, about $8 at his prices; the run prints
its own projection after ten fresh calls, and `--budget 12` leaves
$2 of the $14 as slack.  Six workers may meet the account's
rate limit; a refused call is retried three times, 30/90/240 s apart,
and then the run dies with everything so far in the cache, so the
same command continues it.

**The run — 2026-09-12, 05:27 to 06:32, his terminal.**  535 chunks,
533 fresh calls on the API in 65.5 min at six workers; two rate-limit
retries, both recovered; no truncation; six replies that were not
JSON, all six salvaged object by object by the parser written while
the run was going, so no chunk is empty.  Then the same command once
more: one fresh call, because this card had been edited under the
run, which is the incremental update doing its job on the first day.

| | |
|---|---|
| entities, raw / merged by name | 14,657 / 5,591 |
| grounded — the name occurs in the chunk | 0.990 |
| relations, all carrying keywords | 11,399 |
| tokens in / out | 1.48 M / 1.62 M |
| cost at his prices, $1 / $5 per M | **$9.57** of the $14 |

The estimate after ten calls read $15 more, from `fixme.md`'s dense
chunks; the estimate by remaining text at the halfway mark read
$9.50; the ordering front-loaded the cost, as it was meant to.

**And the order is centrality, not the alphabet — 2026-09-12, before
the run.**  He brought KET-RAG (Huang, Zhang, Xiao, KDD 2025, arXiv
2502.09304): rank the chunks by PageRank and give the model only the
central fraction.  Local search only, and the fraction would blind the
global question, so the fraction is not taken; the order is.  *"ok.
lets do it before I start."*  `jobs()` sorts documents by PageRank in
the tree's own citation graph, `tools/communities.py`'s, built from
the backlinks index in a third of a second: `fixme.md`, the journal,
`doc/memory/README.md`, `doc/instruments.md` first, `CLAUDE.md` last.
A run that completes is the same graph whatever the order; a run the
budget stops has left out the periphery.  The paper's other finding
— a keyword-to-chunk graph with no model beat GraphRAG on local
coverage at a hundredth of the cost — is outside support for Q3's
default and changes nothing.

    python tools/graphrag.py extract --backend api --workers 6 --budget 12 2>&1 | tee -a ~/.cache/gestate/graphrag/extract-haiku.log
    python tools/graphrag.py extract --backend cli --workers 4          # the increments, later: only the chunks whose text changed are called
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

**Items 1 and 2 ran — 2026-09-12, the morning the graph was whole.**
Henri: *"ok. Lets do the items 1 and 2."*  Two commands, no model,
each a list for a person and a count, `test/test_graphrag.py` holds
the shape of both:

- **`subjects`** — item 1.  A subject is an entity typed concept,
  rule, event or project (a document, tool, card, memory or defect
  has a home by construction); a *home* is a filename, a markdown
  heading or a memory-index hook, normalised.  **10 of 89** subjects
  in six or more documents have no home: `GESTATE_BUILD_TIME`,
  `GESTATE_EDITOR_TIME`, `render_block`, `~/tend`, the event
  `2026-08-13`, **Toyota Production System**, `Sig`, `SigHead`,
  `Workbench.control`, `export.substrate_of`.  The session's reading,
  marked as such: six are the language's own identifiers and are
  named where they are defined, in code the extraction does not read;
  `~/tend` has a memory whose hook the matcher missed; the event is
  a date.  Toyota Production System is the one: named in five
  documents by grep, seven by the graph, titled nowhere — the method's
  source, and `doc/memory/method-sources.md` already says crediting it
  is `spec/author.md` and his to write.  So item 1's first real find
  is a thing the tree knew and had filed under somebody, and the graph
  found it anyway, which is the shape the plan wanted.
- **`contradictions`** — item 2.  For one entity, descriptions that
  quote a number *with a unit* in two or more documents where no two
  agree; bare counts are excluded, they disagree everywhere and mean
  nothing.  Each document is dated by its last commit, newest last.
  **15 pairs.**  The pilot's own example is in the list, found by
  arithmetic: `spec/rules.md` at 2000 lines in the August journal
  and 2500 in the spec since 2026-09-06.  Seven of the fifteen are
  line counts quoted about a document that has since grown or been
  rotated — `spec/summary.md` still says the journal is 6,948 lines,
  from 2026-08-19; it is 2,967 after the rotation — which is the
  *stale number* class `doc/memory/small-edits-to-his-pages-said-out-loud.md`
  covers.  One checked and found not real: `doc/testimony.md`'s
  *2000 lines* is a dated quotation of what he said on 2026-08-20,
  which is what that page is for.  The rest are his to read; the
  number the plan asked for, *how many real*, is his count.

His prediction above said 1 and 2 would produce something real.  On
the session's reading, each produced one.

**Item 3 ran — 2026-09-12, the same morning.**  Henri: *"ok. lets
proceed, what do we have next?"*  The sheet first,
`doc/trial/graphrag-global.md`, passed `tools/prereg.sh` before a
call; then `query`, LightRAG's shape in the tool — Haiku turns the
question into keywords at two levels, the specific ones matched to
entity names and the themes to the keywords on relations, one hop,
and one Sonnet call over a context cut at 40,000 characters, every
line of which carries its document; the tool prints and never
writes, the shell put the three answers under
`doc/trial/graphrag-global/`.  The mechanical half is on the sheet:
32 of 32 citations resolve, two to four sentences per answer carry
none, under $0.10 and under a minute each against an afternoon by
hand.  Three findings about the tool before any reading of quality,
all on the sheet: on the neighbours question **the store knew and the
query did not find** — the five prior-art names are in the store,
and a ranking by document count cut them out under 514 matched
entities; the keyword step does not know the tree's vocabulary; and
the first answer cited a card by shelf path, which the citation gate
refused, so the tool now rewrites shelf paths to ids.  **His reading, the
same morning:** *"These three files graphrag-global seem pretty good
and spot on."*  On the sheet: *spot on* settles the *invents* half,
none of three; the *adds* half is settled against the query for q2 by
its own answer, and for q1 and q3 he read them against the hand
answers the same morning: *"The graph found a different perspective,
and maybe some things not apparent in the hands answers.  I think
they're both valuable."*  **Two of three added, none invented: the
query stays**, the sheet's decision line taken as written, his
*maybe* kept.  Nothing was tuned before it.  Next by the plan: item 4,
the cue at the moment; and a second sheet for the ranking that cut
the prior-art names out of q2.

**Item 4 built — 2026-09-12, the same morning.**  Henri: *"ok. lets
do the item 4 next."*  `tools/graphrag.py cue <path>`: for the file
just read, the subjects it names that two to twelve *other* documents
also name, the most specific first, and for each up to two of those
documents the citers list did not show — offered as citation keys, a
card by its id.  Dates and code identifiers typed as concepts are
left out; a hub named by seventy documents is a route to nowhere and
is out by the bound.  Deterministic, from the store, 0.17 s, no
model.  The backlinks hook appends the line under its own cut line —
`graph_cue` in `tools/backlinks.py`, never fatal, never on a test
tree — and logs the graph's offers in a seventh field, so **the
measure is the hook's own**: a later fire on a key the graph offered
and backlinks had not is the graph's follow, and `tools/backlinks.py
--earned` prints *graph cue: N of M fires that carried one were
followed* apart from backlinks' own number.  Zero over a real number
of fires is the same verdict it is for backlinks: decoration with a
context bill, and the line comes out.

*What the first cues look like, the session's reading:* `spec/frp.md`
shares *sigcons* with `spec/crust.md` and *sample* with
`spec/sampling.md` — routes the fifty citers did not show;
`doc/method.md` shares *wait* with the manual, which is a word and
not a subject; a memory page mostly gets nothing, its subjects being
named by one document or by thirty.  The quality of a cue is the
store's entity typing, which is loose (`subjects` above says the
same), and no rule here was tuned past the two exclusions named.
The number decides.

**The second sheet ran — 2026-09-12, the same morning.**  Henri: *"ok.
lets do the second sheet for the ranking."*  `doc/trial/graphrag-ranking.md`,
prereg first.  The measurement it was built on sharpened the first
sheet's finding: in all three answers of the first trial the context
was cut inside the entities section and **no relation ever reached
the answer** — the dual-level design's second level had been
retrieved and thrown away.  A `--ranking split` option halves the
budget between entities and relations and puts matched entities
before hopped ones; building its test found a retrieval defect,
both ends of a theme-matched relation now count as matched, so the
old ranking was rerun with the fix as a third arm.  On the
neighbours question the split answer names **five of five** prior-art
names where the old named none, 12 citations, one uncited sentence.
But q3 kept 6 of its 14 documents, under the half the sheet demanded,
so **the sheet says not decided and the default stays**; the cause
is visible and mechanical — the keyword step read *what is this
tree* as *tree structure*, and the split ranking faithfully spent
half the budget on the language's data structures.  **Next sheet:
the keyword step**, with q3 as its case, and this sheet rerun after
it.  A decision shaped for him meanwhile: the default stays `docs`
until the keyword sheet runs, and if he would rather have the split
now on the strength of q2 alone, that is one word and the sheet
records it as his call over its own line.

**The tool's calls are the subscription's from here — 2026-09-12,
mid-morning.**  Henri: *"the api backend was good for bootstrapping
this thing, but I'd like it to use cli otherwise."*  `query` defaults
to the cli now, the cli accepts a prose reply where an extraction
needed an object, and a cached reply is found either way; proven on
one fresh question, 22 s for both calls, 11 citations resolving.  The
trials' arms ran on the api by their sheets' word, so that each
differed from its control in one thing.  About **$10.50 of the $14**
went on the whole morning: the graph, three trials, and the pilot's
$1.50 the day before.

**The third sheet ran — the keyword step, and not decided either.**
`doc/trial/graphrag-keywords.md`: the keyword step is handed the
store's own vocabulary, 150 names and 100 tags, deterministic.  It
read *what is this tree* as *the tree* and q3 kept 9 of its 14
documents, above the line — and q2 fell from five prior-art names to
none, because the vocabulary steered the specific channel to five
hub documents, whose hops filled the half.  Read as written: **not
decided**, both options stay options, both defaults stay.  What the
three sheets agree on, on the sheet: a document-type entity as a low
keyword is a hub, and 40,000 characters cannot hold a hub's
neighbourhood and a specific answer at once.  A fourth sheet would
test that one thing.  His readings so far: the three first answers
*spot on*; the split *more informative, maybe too dense*.

**The fourth sheet ran — hubs kept from hopping — and changed
nothing, which is its result.**  Henri: *"graphrag-keywords seem a
bit like doing conclusions that I think do not hold entirely.  But
otherwise it's naming real things and subjects across the tree.
So.. lets do that fourth sheet."*  `doc/trial/graphrag-hubs.md`: a
document matched by a low keyword contributes itself and does not
hop.  Both arms' contexts came out byte-identical to their controls
and every answer was served from the cache, $0.  The lesson is
mechanical and it corrects three sheets' shared assumption: **under
the split ranking no hop entity has ever reached the context**; the
entity half is filled by the theme channel, a thousand entities
ranked within their group by document count, and the top forty-five
are the hubs.  A fifth sheet would rank the theme channel's entities
by how many of their relations carry the question's tags, and its
relations by the rarity of the shared tag.  Four sheets, four
not-decideds read as written, and each one narrowed where the cause
is; the defaults are still the first morning's.  His reading of the
vocabulary answers is on the third sheet: conclusions past what the
things support, over things that are real.

**The fifth sheet ran — the theme channel ranked by its own evidence.**
Henri: *"lets do the fifth sheet.  This is worthwhile to do, and I'm
still sharp."*  `doc/trial/graphrag-themes.md`, two arms under the
vocabulary keywords: entities by how many of their relations carry
the question's tags, and that plus relations by the rarity of the
shared tag.  Writing the test found two more defects in retrieval —
the relation dedupe collapsed every row between one pair in one
file to a single row, and the entity evidence had to be
rarity-weighted or a hub's thirty *reference* rows beat a citation's
three — both fixed with tests before any call.  Arm B names **five
of five** prior-art names on q2, the richest answer to that question
in five sheets, and drops q1 and q3 under the line; A fails two.
**Not decided**, read as written.  The sheet's real result is about
its judge: *keeping the first answers' documents* was the line, and
the first answers came from the hub-ranked context, so the number
rewards hubs and cannot separate the arms; against the hand answer's
thirteen documents every arm shares three to five.  A sixth sheet
would keep the questions and judge q1 and q3 against the hand
answers, written first — a change to the sheet, not the tool, and
written down before it so it cannot be read as chosen after.
About **$11.50 of the $14** spent in all.

**The sixth sheet ran — three new questions, judged by their hand
answers.**  Henri: *"ok. do the sixth sheet.  I think the B answers
seemed slightly better than the A answers.  Though, it depended on
what was asked."*  `doc/trial/graphrag-hand.md`: the three earlier
questions could not be re-judged, their arms' answers already
existing, so three notes pages became the hand answers — drift,
secretion, reviews — and the two surviving retrievals were put to
them.  Each arm won one and they tied one; the line asked for a
winner; **not decided**.  What the run found: neither arm reached
the secretion page or the reviews page, because the vocabulary
prompt made the keyword step prefer the tree's most-cited names over
the question's own rare word — *secretion* is in no top-150 list,
and rare is what made it the right keyword.  The seventh sheet
would keep the question's own words beside the vocabulary; the
hand-answer judge is kept.  **Six sheets in one day**, every one
read as written, none decided, and the map of the query is now
drawn: the split budget is needed or no relation reaches the answer;
rarity in the theme channel gives the richest specific answer;
vocabulary wins a question in the tree's words and loses one in its
own; the store holds what every question needed.  The defaults are
still the first morning's, and changing them is one word of his over
the sheets' lines, recorded as such.  About **$12 of the $14** spent.

**The seventh sheet decided — 2026-09-12, evening.**  Henri: *"ok.
lets do the seventh sheet."*  `doc/trial/graphrag-union.md`: one
sentence in the keyword prompt, the question's own specific words
always kept as low keywords beside the vocabulary's names.  Against
the sixth sheet's hand answers the arm shared at least as many
documents as B on three of three — 3 against 1, a tie, 2 against 1 —
cited the notes page on drift and secretion where B cited one, and
held the tree question at three; *secretion*, *reviewing guest* and
*reviewer* were its keywords.  All three conditions of the line held,
so **`query`'s defaults are now union keywords and the themes ranking
over the split budget**, the second to sixth sheets' open lines
close on it, and the earlier settings stay as options and as the
record.  His reading of invention on the four answers is owed and
can overturn it.  Under the sheet the checker learned the tree's own
rule, a unique basename resolves, with the reason on the sheet.
What the seventh did not fix is on it too: the words reach the door
and not always the room, and two to six sentences an answer still
carry no citation.  **Seven sheets in one day, one decided**, and
about $12.50 of the $14 spent.  What comes before any eighth is the
month: finds written into the tree with the graph as the finder, and
the cue's follow count on the backlinks lamp.

## In use — what shows up in the work from now on, 2026-09-12

Henri: *"tell me how we put this new tool into use?  What do we
setup such that it shows up in the work from now on?"*  Three things
arrive on their own and two are by hand.

- **On every read, the cue.**  The backlinks hook already fires on
  every `Read` and every shell command that reads a file, and since
  this morning its answer ends with the graph's line — *this file
  shares X with A, B* — with no setup beyond the hook that is
  installed.  Its follow count prints with `tools/backlinks.py
  --earned`.
- **At every commit, the lamp.**  `tools/pre-commit.sh` prints
  `graphrag check`'s first line beside the backlinks, flow and
  standing lamps: how many chunks the graph has not read, half a
  second, no call, never refuses.  Added today.
- **On the bench, the report.**  `tools/toolbox.sh` reports whether
  `claude` is on PATH, which is what the tool needs now; the key is
  optional.  Its entry was rewritten today from the api-first text.
- **By hand, the increments** — `python tools/graphrag.py extract`
  on the cli when the lamp's number says so; only changed chunks are
  called.  The natural place is the keeper's evening, step 1, *read
  the lamps*: `keeper.md` is his page, so the line is offered here and
  not written there — *when the graphrag lamp says more than a
  handful, run extract; then `subjects` and `contradictions` once, and
  read them*.
- **By hand, the questions** — `python tools/graphrag.py query
  "<question>"` from any shell in the checkout, 20–60 s on the
  subscription, printed and never written; `lookup <name>` for one
  subject across the tree in a second.  The rule stands: what the
  graph finds goes into the tree citing the document, never the
  graph, and the journal says *found by the graph*.

*The first question put to it in use, the same evening, his: "How
does TPS manifest inside this project?" — eleven citations resolving,
none uncited, jidoka, poka-yoke, kaizen, gemba and kanban each traced
to a file; reproduced from the cache by the same command.*

**The first reading, against the prediction — 2026-09-12, at chunk
357 of 535, the api run still going.**  Henri, having tried `lookup`
and `entities` on the half-built store while it ran: *"It feels like
some sort of brains at this point, or what I imagine brains would be.
It may very well be that this was worth it."*  Recorded here as what
a first look felt like, beside his prediction above; what settles it
is still the count the plan names — finds written into the tree with
the graph as the finder — and that count is zero until the first one.

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
