*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What is this tree?

*keywords (claude-haiku-4-5-20251001): low []; high ['tree structure', 'data organization']*  
*retrieved: 421 entities matched + 1088 by one hop, 2460 relations (138 in the context); ranking split; 40002 chars (cut); answer by claude-sonnet-5; 15716 in, 1186 out, $0.064 at assumed prices*

# What is "the tree"?

The context uses "the tree" as a recurring, somewhat metaphorical term for the gestate project's living body of documents, rules, and working practices — not a single file, but the whole self-describing structure the project is built from.

## As a living structure that must be maintained

Henri is credited with the insight that "the tree must be treated well or it withers," a call made on 2026-08-24, which is preserved as a memory document titled `The tree withers` (`doc/memory/README.md`). This memory pairs with related requirements — such as making small edits to pages and saying things out loud — for keeping the tree alive, and it is described as having an implementation counterpart in a separate `~/tend` workspace-tree repository that applies the same maintenance principles (`doc/memory/README.md`).

## As the source of practice and conditioning

Kaizen is described as "the four-question practice that turns talk into a tree through dialogue where both halves are written" (`doc/teaching/keepers-first-week.md`), suggesting that the tree is what emerges from disciplined, recorded dialogue rather than being a fixed artifact — it grows through practice.

Separately, an internal reviewer is said to be "conditioned by the tree's ru[les]" (relation description is cut off in context, `doc/notes/notes-on-corrections.md` region), implying the tree functions as the normative structure that shapes how review and judgment happen within the project.

## As a structure with distinguishable jobs, tested for degradation

A memory document, `doc/memory/smaller-models-and-the-tree.md`, treats the tree analytically, identifying "three jobs" — structural rules, judgment norms, and initiative — and studying how these degrade separately when smaller language models are conditioned by the tree's material. This document reports that "structural rules survive, judgment norms go first, initiative goes furthest," based on measurements on 9B and 1B models (`doc/memory/README.md`, `doc/memory/smaller-models-and-the-tree.md`). This framing treats "the tree" as the body of rules, norms, and behavioral conditioning that a session or model absorbs, with different parts of that conditioning proving more or less robust under model scaling.

## Relation to GraphRAG and self-description

One note observes that "the tree is GraphRAG turned inside out, with hand-written graphs, community summaries, and local retrieval mechanisms already in place" (`doc/notes/notes-on-the-find.md`), suggesting the tree is understood as an organically-grown, hand-authored analog to the kind of knowledge-graph/retrieval system that GraphRAG formalizes — cards, journals, specs, and memory files functioning together as a graph of citations and summaries that a session can traverse.

## Summary

Taken together, the context does not present "the tree" as one single named document; rather it is the project's overall living structure — documents, cards, memory files, rules, and practices (kaizen, review, conditioning) — that must be actively tended (`doc/memory/README.md`), that embodies distinguishable layers of rules/norms/initiative whose robustness has been measured under model degradation (`doc/memory/smaller-models-and-the-tree.md`), and that resembles, in organic and hand-built form, a knowledge graph such as GraphRAG (`doc/notes/notes-on-the-find.md`). The context does not give a single canonical definition beyond these testimonies, so the tree is best understood as the project's whole self-maintaining, citation-linked body of work rather than any one file.

---
*citations: 5 resolve, 1 do not — ~/tend; 3 sentence(s) with no citation*
