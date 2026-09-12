*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What are the method's neighbours — the prior art each of the tree's mechanisms already has a name in?

*keywords (claude-haiku-4-5-20251001, vocab): low ['doc/memory/henri-prior-tools.md', 'method-sources', 'spec/north_star.md', 'manifesto.md', 'vision.md']; high ['prior art', 'design principle', 'reference', 'related concept', 'methodology']; 4 of 5 high keywords are tags in the store*  
*retrieved: 962 entities matched + 1546 by one hop, 5434 relations (111 in the context); ranking themes, hop from all; 40002 chars (cut); answer by claude-sonnet-5; 16919 in, 1571 out, $0.070 at assumed prices*

# The Method's Neighbours: Prior Art Behind the Tree's Mechanisms

The context identifies a document, **method-sources**, as the memory intended to hold the tree's prior art: it records "Adler's separation of tasks, Socratic dialogue and the epoché" as rules already operating in the tree without being credited, with the crediting work assigned to `spec/author.md` and to Henri (`doc/memory/README.md`). A companion note confirms this is unfinished business — "Henri's sources should be written" (`doc/notes/notes-on-the-find.md`), and `doc/notes/notes-on-the-find.md` itself proposes that a paragraph on prior art might belong in method-sources rather than `spec/author.md` (`doc/notes/notes-on-the-find.md`).

Beyond that named ledger, the context traces specific mechanisms to specific ancestors:

**Manufacturing method.** The manifesto's rule that systems must report when wrong is identified with *jidoka* from the Toyota Production System (`journal/2026-08.md`), and *genba* (going to the actual place) is named as the TPS principle behind the project's emphasis on direct observation (`manifesto.md`). More broadly, TPS is described as the frame for treating the model as a high-throughput process step, invoking jidoka, poka-yoke, kanban, and gemba together (`journal.md`), and as a manufacturing methodology stressing action, observation of failures, and iterative correction (`manifesto.md`).

**Design method.** "Set-based design" is explicitly opposed to "point-based design," using propagation instead of chronological backtracking, per the manifesto (`manifesto.md`).

**Dialogue and epistemics.** *Dialogue-is-its-own-mode* is credited to Alhanen's principle that understanding, not winning, is the goal, with a rhetorical question characterized as "an opinion wearing a question mark" (`doc/memory/README.md`); testimony ties this to "Alhanen's Dialogi and henri's reading notes" (`doc/testimony.md`). *Horizontal-not-vertical* (praise as gratitude, not verdict) is traced to an argument through "Adler's reading notes 'kehuminen on manipulaatiota'" (`doc/testimony.md`).

**GUI/interaction lineage.** For `mide-staves-ui`, Garnet and Amulet are named as prior art on constraint-based interactors and their breakage, while Eve is cited as closest in ambition though discontinued (`doc/memory/mide-staves-ui.md`). `card:gex-sheet.md` cites Pad++ as prior work on zooming interfaces (`card:gui-is-difficult.md`). `card:gui-is-difficult.md` derives a rule "G never" from parametric CAD precedent governing identity decisions (`doc/notes/notes-on-gui.md`).

**Compiler/language lineage.** `subgrammar.py`'s monomorphic Datafun sublanguage is described as following a prior boundary-drawing effort comparable to the audio fragment work (`journal/2026-08.md`).

**Literature cited as ingredients.** `doc/notes/notes-on-the-find.md` names several works as ingredients of the tree: Ford, Parsons & Kua 2017 on fitness functions; Nygard 2011 on Architecture Decision Records; Martraire 2019 on Living Documentation; Rother 2009 on Toyota Kata; and Poppendieck 2003 and Anderson 2010, without further gloss (`doc/notes/notes-on-the-find.md`).

**Henri's own prior tools.** Separately from external prior art, `doc/memory/henri-prior-tools.md` records Henri's own earlier tools — oscillseq (over scsynth), mide (UI as datalog), and xylem (constraints and Knuth–Plass) — as internal precedents that already answered questions the tree now faces, including oscillseq's (pitch, accidental) pair representation reused in `arc.notes` (`doc/memory/README.md`, `journal.md`) and oscillseq's four transport states simplified into `card:transport-modes.md`'s three (`card:transport-modes.md`).

The context does not present a single unified list beyond these; it shows method-sources as the designated but still-incomplete place where this scattered prior art was meant to be gathered.

---
*citations: 13 resolve, 0 do not; 2 sentence(s) with no citation*
