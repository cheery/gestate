*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What is this tree?

*keywords (claude-haiku-4-5-20251001, vocab): low ['the tree']; high ['definition', 'reference']; 2 of 2 high keywords are tags in the store*  
*retrieved: 444 entities matched + 1191 by one hop, 2732 relations (141 in the context); ranking split, hop from subjects; 40002 chars (cut); answer by claude-sonnet-5; 17107 in, 1091 out, $0.065 at assumed prices*

## What "the tree" is

Based on the context, "the tree" does not refer to a single canonical document but rather emerges as a recurring concept describing the whole project's structure — its documents, journals, rules, and cards taken together as a living, self-conditioning system.

Three descriptions converge on this idea, each drawn from different corners of the corpus:

1. **A pedagogical, living system.** `journal/2026-08.md` characterizes the tree as "a living system of documented methods, rules, and journal entries designed to teach its keeper and visitors through written practice." This framing emphasizes the tree's role in instructing both the person maintaining it (the keeper, elsewhere identified as Henri via `doc/memory/the-keeper-is-the-qualification.md`) and outside visitors who read it.

2. **An append-only conditioning system.** `doc/notes/notes-on-the-find.md` describes it more mechanically: "an append-only system that conditions the next session's behavior through deterministic rules, gates, and a consent register, functioning as a workplace for workers who do not remember." This ties the tree directly to the project's session model, where each session (`journal/2026-08.md`, `journal.md`) is a fresh, memoryless conversational entity that must be re-conditioned by what has been written down — rules, gates, cards, and journals — rather than by continuity of memory.

3. **An external cached "slow thinking" system.** `doc/notes/notes-on-cues.md` frames the tree as "an external, cached slow thinking system that stores the residue of past deliberation and conditions future fast passes." This suggests the tree exists to hold the outcome of earlier careful reasoning so that subsequent quick work (fast passes) can draw on it without re-deriving everything.

## How this maps onto the concrete repository

Taken together with the surrounding entities, "the tree" appears to be shorthand for the whole documented apparatus of the project: things like `fixme.md` (defect tracking), `journal.md` and `journal/2026-08.md` (work and design history), `roadmap.md`, `vision.md`, `manifesto.md`, `doc/method.md`, `board/README.md`, `keeper.md`, and the various `spec/*.md` files, along with the board's cards (e.g., `card:working-standard.md`, `card:gui-is-difficult.md`). These are the "documented methods, rules, and journal entries" the first definition alludes to, and the "deterministic rules, gates, and consent register" the second definition names concretely (gates being enforced by `tools/suite.py` per `fixme.md`, and citation/consent mechanisms discussed in `board/README.md` and `fixme.md`).

## Disagreement in emphasis

The three descriptions do not contradict each other outright, but they emphasize different functions: `journal/2026-08.md` stresses teaching and pedagogy, `doc/notes/notes-on-the-find.md` stresses behavioral conditioning of memoryless workers, and `doc/notes/notes-on-cues.md` stresses cached deliberation feeding fast decision-making. The context does not resolve which of these is the "primary" or original sense of the term, only that all three are attested for the same entity, "the tree."

---
*citations: 15 resolve, 1 do not — spec/*.md; 3 sentence(s) with no citation*
