# GraphRAG — does the tree's hand-drawn map match where its citations cluster

    status   doing — 2026-09-11, run; waits on Henri reading the list
    because  a global question about the tree is answered by a session
             reading fifteen files chosen by hooks — a map-reduce done
             by hand — and the local neighbourhood is already larger
             than a session reads: the backlinks hook fired 694 times
             in fourteen days, 618 of them cut at twenty (89 %), and
             159 of 682 were followed.  Whether the tree's hand-made
             partition — its directories, the atlas sheets, the memory
             index — matches where its citations actually cluster has
             never been measured.  *The session's measurement,
             2026-09-11, from `tools/backlinks.py --check`; Henri's own
             `because` is asked for below.*
    asked    Henri, 2026-09-11 — "Muuten.. Miten GraphRAG liittyy tähän?
             Voisiko sitä soveltaa puuhun?" and, given the answer,
             "laadi kortti jolla tehdään kyseinen tutkimus.
             card:GraphRAG.md"
    see      doc/notes/notes-on-the-find.md — the conversation, and the
             answer this card is the measured half of
             doc/notes/notes-on-cues.md §"Can an introspective index be built?"
             — *plausible list, not an inventory; do not build that*
             tools/backlinks.py — the citation graph already walked
             test/test_citations.py — the walker that parses every edge
             doc/memory/research-that-leaves-a-command.md — why this is a
             command and not a report
             doc/memory/a-trial-is-refused-until-its-sheet-can-decide.md
             — the sheet comes before the run

## What this is, what it is not, and when it runs

**A measurement, once.**  Take the citation graph the tree already
has — `card:` citations, `[[memory]]` links, `§"…"` citations,
F-numbers, file paths — as nodes and edges, partition it by a
community algorithm, and compare the partition to the one the tree
drew by hand.  One command, a seed, a number, and a list of the
places where the two disagree.

**It is not GraphRAG built into the tree.**  No LLM-extracted graph
(the tree's graph is a contract, checked by `test_citations.py`), and
no LLM-written community summaries committed as pages — a derived
page with no source and no check is a document that was alive once,
`doc/method.md` §"The tree withers if it is not treated well".  The
graph is the tree's own and the partition is computed, not written.

**It is not a query instrument either**, yet.  A tool that answers a
global question over the journal, the ledger and the memories by
map-reduce has no caller today but conversations like the one this
came from; `doc/memory/capacity-is-not-a-caller.md`.  Its trigger is
written below so it is not proposed again as new.

**It runs from a session's shell, fenced, and touches nothing.**  The
output is a page under `doc/` only if the result decides something;
otherwise the numbers go to the journal with the command that
produced them.

## The postcondition, before anything is built

After this, a person can say in one number whether the tree's
hand-drawn map matches where its citations actually cluster, and can
point at every place it does not, by running one command.

## Found by looking, 2026-09-11

- **The graph is already walked twice.**  `test/test_citations.py`
  parses every citation kind to check it resolves; `tools/backlinks.py`
  inverts the same walk.  The nodes and edges are one function away
  from either; nothing new has to parse markdown.
- **No graph library in the checkout.**  Checked 2026-09-11 in
  `.venv`: no `networkx`, no `igraph`, no `leidenalg`.  Leiden proper
  needs `leidenalg` + `igraph`; `networkx` carries Louvain.  The graph
  is small — a few hundred nodes at most — so a pure-Python Louvain
  or label propagation, seeded, is within a morning and adds nothing
  to `doc/install.md`.  Which of the two is a day-one decision, and
  the difference (Leiden guarantees connected communities, Louvain
  does not) is named in the result either way.
- **The hand-made partition is three things, not one.**  The
  directories (`board/`, `doc/memory/`, `spec/`, `tools/`, `test/`,
  `gestate/`); the five atlas sheets (`python -m gestate.atlas`); and
  the memory index, which is **flat** — `doc/memory/README.md` §"The
  index" is one list of 88 hooks with no sections, so it partitions
  nothing and cannot be compared.  Compare against the first two.
- **The comparison has a standard form.**  Normalised mutual
  information or adjusted Rand index between two partitions of the
  same node set; both are a few lines and need no library.
- **The interesting output is the disagreement list**, not the score:
  a computed community that straddles two directories is a subject the
  tree has not named; a memory alone in its community is either an
  orphan or the one place a rule lives; two memories always in one
  community with nothing else are the *rule stated twice* candidate
  `doc/method.md` lists among the ways files rot.  Each is a lamp for
  a person, never a gate.

## Questions

1. **Is the `because` above yours?**  It is the session's measurement
   of a symptom.  If the problem you had in mind was different — a
   global question you wanted answered, a map you distrust — say it
   and it replaces the header.  *Open, 2026-09-11.*
2. **What counts as a node?**  Files only, or also cards, memories and
   F-numbers as their own nodes even where they are files?  Default:
   one node per file, with `card:`, `[[…]]` and F-numbers resolved to
   the file they name, so the partition is over things a person opens.
   *Open; the default runs unless you say otherwise.*
3. **Does the atlas count as a hand partition?**  Its five sheets are
   generated from the tree; they are a partition somebody chose, but
   the choice was a session's.  Default: yes, labelled as such.
   *Open.*

## The run, 2026-09-11 — steps 1–3 done, step 4 is his

`doc/trial/graphrag.md` passed `tools/prereg.sh`; `tools/communities.py`
ran in six seconds; `journal.md` §"The citations cluster by subject,
and the directories are sorted by kind" has the numbers and the
commands.  The decision line: **NMI 0.311 against the directories,
null maximum 0.180, threshold 0.8** — the sheet's second branch.

**The one sentence:** every disagreement is a community straddling
directories the same way — spec, module, tests, examples together.
The citations cluster by *subject*; the directories sort by *kind*.
The atlas's lanes, the one hand map drawn by subject, matched best
(NMI 0.503 over the modules), against the sheet's prediction.

**For him to read** — the lamp, not a verdict:

- the eleven straddling communities, printed by the tool; the largest
  is `test 42, gestate 30, examples 30, spec 11`;
- two memory pairs alone in their community in the written-only run:
  `gui-command-language-first` + `identity-is-the-models-key`, and
  `gestate-salvage-week` + `henri-prior-tools` — one subject in two
  files each, or a rule stated twice; his call.

**What was not built:** Leiden (no library; `--graphrag` in
`tools/toolbox.sh` would be `python-igraph` + `leidenalg`), and the
query instrument, whose trigger below is unchanged.

## Day one

1. Write the sheet first — `tools/prereg.sh` — with the prediction
   stated before the run: *the computed partition matches the
   directories at better than chance and worse than 0.8 NMI, and the
   disagreement list has under twenty entries.*  A blank prediction is
   a stop.
2. Extract nodes and edges from the walker `test_citations.py` already
   has; write them out as a plain edge list so the next step is
   re-runnable without the tree.
3. Partition, seeded.  Compare to directories and to the atlas.
   Print the score and the disagreement list.
4. Read the list with Henri.  What it names is his to decide; the
   card's `## Done` records the number and where the list went.

**Trigger for the second half, written so it is not re-proposed:** a
query instrument over the journal and the ledger is built when a
session answers the *third* global question by reading fifteen files.
Two have happened, both on 2026-09-11, both on this page's
conversation.

**Kill condition for the whole idea:** if the computed communities
match the directories closely — NMI above 0.8, say — the graph has no
structure the hand does not already see, and GraphRAG has nothing to
add here.  That is a good result and the card closes on it.
