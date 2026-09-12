*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What is this tree?

*keywords (claude-haiku-4-5-20251001): low []; high ['tree structure', 'data organization']*  
*retrieved: 421 entities matched + 1088 by one hop, 2460 relations (0 in the context); ranking docs; 40000 chars (cut); answer by claude-sonnet-5; 15241 in, 947 out, $0.059 at assumed prices*

The "tree" in this repository is the project's self-documenting knowledge and governance system, not a code module — it is described across multiple documents as a living, self-conditioning structure.

**Core definition**

The most direct characterization comes from `journal/2026-08.md`, which calls the tree "a living system of documented methods, rules, and journal entries designed to teach its keeper and visitors through written practice." A second description, from `doc/notes/notes-on-the-find.md`, frames it more mechanically: "an append-only system that conditions the next session's behavior through deterministic rules, gates, and a consent register, functioning as a workplace for workers who do not remember." A third, from `doc/notes/notes-on-cues.md`, describes it as "an external, cached slow thinking system that stores the residue of past deliberation and conditions future fast passes."

Together these three descriptions (all under the entity **the tree** [concept]) suggest the tree is the accumulated body of rules, memory files, journal entries, and specifications that stand in for institutional memory across sessions that themselves have no persistent memory — each new "worker" (session) re-derives behavior from what is written rather than from what it personally recalls.

**Supporting structure**

Related entities reinforce this picture. `doc/memory/smaller-models-and-the-tree.md` treats the tree as having "three jobs" — structural rules, judgment norms, and initiative — that "degrade separately" when tested on smaller models, implying the tree is meant to condition behavior at varying levels of reliability depending on model capability. This document is filed under the memory entity **smaller-models-and-the-tree**, which frames the tree's jobs explicitly in terms of what survives on constrained models: "structural rules survive, judgment norms go first, initiative goes furthest" (`doc/memory/README.md`).

The tree also appears connected to governance mechanisms like `doc/memory/the-keepers-evening.md`, which describes a weekly review session tied to "keeper.md" as its standard work — reading lamps, opening decision batches, measuring rules, and rotating monthly (`doc/memory/README.md`). This suggests the tree is maintained through periodic ritual review rather than continuous editing.

**Caveat on ambiguity**

The context does not fully resolve whether "the tree" refers strictly to the `doc/memory/` directory and its associated rules, or more broadly to the entire project's documentation-plus-code structure (including `spec/`, `board/`, `fixme.md`, and `journal.md`). The three top-level descriptions differ in emphasis — one calls it a living teaching system, one calls it an append-only conditioning system, and one calls it a cached slow-thinking store — and the context gives no single canonical scope statement resolving these framings into one authoritative definition.

---
*citations: 11 resolve, 0 do not; 4 sentence(s) with no citation*
