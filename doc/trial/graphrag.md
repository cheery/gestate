# graphrag.md — the sheet, before the run

*Written 2026-09-11, before `tools/communities.py` existed, for
`card:GraphRAG.md` day one, step 1.  `tools/prereg.sh doc/trial/graphrag.md`
must pass before the run.*

**question:** does a partition computed from the tree's own citation
graph match the partition the tree drew by hand — its top-level
directories (with the board's shelves as one), and the atlas's lanes
for `gestate/*.py`?

**decision:** if the computed partition's agreement with the
directories is 0.8 NMI or above, the graph has no structure the hand
does not already see, and `card:GraphRAG.md` closes on that with the
number.  If it is below 0.8 and above the null, the disagreement list
goes to Henri as a lamp, the card's `## Done` records the number and
where the list went, and the query-instrument trigger on the card
stays as written.  If it is not above the null, the citation graph
carries no community structure at all and the card closes on *nothing
to partition*.

**control:** a degree-preserving rewiring of the same graph
(configuration-model swaps, seeded), partitioned the same way and
scored against the same directories — what chance gives for a graph
of this size and degree sequence.  The real graph's score must exceed
the null's maximum over its draws to count as above chance.

**n:** 20

Twenty seeds of the algorithm on the real graph for stability, and
twenty rewired null graphs.

**prediction, before the run:** NMI against the directories between
the null's maximum and 0.8; the disagreement list under twenty
entries; the atlas-lane comparison weaker than the directory one,
because the citation graph over code is sparse.

**what counts as a node:** one node per file, `card:` and `[[…]]`
resolved to the file they name, F-numbers to `fixme.md` (the card's Q2
default).  **Edges:** every citation the backlinks index holds, written
and in-passing alike, undirected, unweighted; a second run on written
citations only is reported as a robustness line, not as the result.

**algorithm:** Louvain in pure Python, seeded, not Leiden — no graph
library is in the checkout and the graph is small; the difference
(Leiden guarantees connected communities) is named beside the result,
and a Leiden run through `tools/toolbox.sh --graphrag` (`python-igraph`,
`leidenalg`) can replace it later on the same edge list.

## After the run — 2026-09-11, nothing above this line edited

NMI against the directories 0.311, null maximum 0.180: the second
branch of the decision.  Predictions: between the null and 0.8 — yes;
under twenty disagreements — yes, eleven; atlas lanes weaker than the
directories — **no**, 0.503 against 0.311.  The numbers and the reading
are `journal.md` §"The citations cluster by subject, and the
directories are sorted by kind".
