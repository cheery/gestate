# graphrag-pilot.md — the sheet, before the run

*Written 2026-09-11 for `card:graphrag-c.md` day one, before
`tools/graphrag.py` had made a call.  `tools/prereg.sh doc/trial/graphrag-pilot.md`
must pass first.*

**question:** can the cheap model do the extraction pass — does Haiku
find what Sonnet finds in the same ten files, without inventing what
the text does not contain?

**decision:** if Haiku's grounded-entity fraction is within 0.05 of
Sonnet's and its entity overlap with Sonnet (Jaccard over normalised
names) is 0.5 or above, the extraction pass over the documents runs on
Haiku; otherwise on Sonnet, with the batch API if the estimate exceeds
the credit.  Either way the summaries stay on Sonnet (the card's Q2).
If *both* models ground under 0.8, the prompt is wrong and no pass
runs until it is fixed.

**control:** the same ten files, the same prompt, the same
`max_tokens` and temperature 0, to both models in the same run; and a
mechanical judge — an entity counts as grounded when its name, or
every word of it, occurs in the source text case-insensitively — so
neither model is scored by a reader who can see which is which.

**n:** 10

Ten files, chosen before the run for kind and size (each under 24 kB
so no file is truncated): three memories, two cards, two specs, the
method page, one notes page, the keeper's page.  The list is in
`tools/graphrag.py` as `PILOT`.

**prediction, before the run:** Haiku grounds within 0.05 of Sonnet,
finds 10–30 % fewer entities, overlaps 0.4–0.6, and costs about a
third; both ground above 0.8.  Cost for the whole pilot under $0.50.

**what is not decided here:** anything about the quality of a summary
or an answer — that is the build's own trial, later, with a sheet of
its own.

## After the run — 2026-09-11, nothing above this line edited

**The decision line:** Haiku grounded **1.000**, Sonnet **0.975** —
within 0.05; entity-name overlap Jaccard mean **0.625**, minimum
0.319 — above 0.5.  **The extraction pass runs on Haiku.**  Both
ground above 0.8, so the prompt stands.

**Predictions, four of five right.**  Grounding within 0.05: yes.
Haiku 10–30 % fewer entities: yes, 195 against 244, 20 % fewer.
Overlap 0.4–0.6: slightly above, 0.625.  Cost about a third: **less** —
$0.128 against $0.741 at the assumed prices, a sixth, because Sonnet
writes twice the output tokens for the same file (44,453 against
21,623).  Pilot under $0.50: **no** — $0.87 for the run that counts,
and about $1.50 in all, because the first run had to be thrown away.

**What the first run found, and it is the pilot's second result.**
At an output ceiling of 4,096 tokens Sonnet was cut off on 7 of the
10 files and every cut reply was unparseable JSON; Haiku fit all ten
under it.  The ceiling is 16,384 now and a reply that still hits it
is printed as TRUNCATED rather than scored as empty — the first run
scored seven Sonnet files as *0 entities*, which was the harness and
not the model.

**Where the arms differ, and the sheet said they would not.**  Sonnet 5
refuses `temperature` (HTTP 400, *deprecated for this model*), so it
ran at the API's default and Haiku at 0.  Haiku's numbers are
reproducible from the cache; Sonnet's would move on a rerun.

**Ungrounded names, all six, all Sonnet's, and read one by one:**
three are re-spellings the judge is right to refuse and a reader would
forgive — *the 2500-line cap* and *the 2000-line cap* where the text
writes *2,500* and *2,000*, and *8000-line journal budget* the same
way — and `card:the-first-jam.md` naming itself by its shelf path,
which its own text does not contain.  **Two are inventions**, both in
`the-first-jam`: *Comment-splits-equation item* and *Drive
scale-surprise item*, labels Sonnet coined for two of the card's
numbered items.  Haiku coined none.  So the judge found the one thing
it was built to find, twice, on the dearer model.  *(The judge itself
was wrong once first: a name that is exactly a stripped prefix,
`doc/memory/`, normalised to nothing and counted as invented for both
arms; fixed before these numbers, and the fix moved Haiku from 0.990
to 1.000 and Sonnet from 0.963 to 0.975.)*

Raw outputs, one JSON per arm per file, and `summary.json`: this
directory's `graphrag-pilot/`.  Rerun: `python tools/graphrag.py pilot`
— cached, so free.
