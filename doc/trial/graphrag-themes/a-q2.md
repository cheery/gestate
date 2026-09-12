*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What are the method's neighbours — the prior art each of the tree's mechanisms already has a name in?

*keywords (claude-haiku-4-5-20251001, vocab): low ['doc/memory/henri-prior-tools.md', 'method-sources', 'spec/north_star.md', 'manifesto.md', 'vision.md']; high ['prior art', 'design principle', 'reference', 'related concept', 'methodology']; 4 of 5 high keywords are tags in the store*  
*retrieved: 962 entities matched + 1546 by one hop, 5434 relations (111 in the context); ranking themes-entities, hop from all; 40002 chars (cut); answer by claude-sonnet-5; 16725 in, 2202 out, $0.079 at assumed prices*

# The Method's Neighbours: Prior Art Behind the Tree's Mechanisms

The project keeps an explicit ledger of prior art — places outside its own documents where a mechanism already has a name — collected chiefly in the memory document **method-sources**, which notes that Adler's separation of tasks, Socratic dialogue, and the epoché are already rules operating inside the tree, uncredited, with the job of crediting them assigned to `spec/author.md` and left for Henri to write (`doc/memory/README.md`, `doc/notes/notes-on-the-find.md`). This same memory is described as "a memory document for method sources and prior art," confirming its role as the collection point for these neighbours (`doc/notes/notes-on-the-find.md`).

## Henri's own prior tools

Several mechanisms trace to Henri's earlier work rather than outside literature. The memory **doc/memory/henri-prior-tools.md** documents three of his own tools — oscillseq (built over scsynth), mide (whose UI models as datalog), and xylem (using constraints and Knuth–Plass line-breaking) — each having already answered a GUI challenge the tree now faces (`doc/memory/README.md`, `card:gui-is-difficult.md`). Concretely, **oscillseq**'s design of holding pitch as a (pitch, accidental) pair supplies the fix used in `arc.notes` (`journal.md`, `spec/drawnscores.md`), and oscillseq's transport states are simplified into `card:transport-modes.md` (`card:transport-modes.md`). oscillseq is also cited as exemplifying "everything has a command under it," the root of the **gui-command-language-first** principle (`card:gui-is-difficult.md`).

## Named prior art from outside literature

Beyond Henri's own history, the GUI-difficulty work names several external precedents directly:

- **Garnet** and **Amulet** are cited as prior art on constraint-based interactors and what breaks in them, relevant to `mide-staves-ui` (`doc/memory/mide-staves-ui.md`).
- **Eve** is named as the project closest in ambition to `staves.ui`, though discontinued (`doc/memory/mide-staves-ui.md`).
- **Pad++** is prior work on zooming interfaces, invoked for the sheet-zoom-level requirement in `card:gex-sheet.md` (`card:gui-is-difficult.md`).
- **Kale**'s solution to reference ambiguity under structural change is carried directly into `card:gex-sheet.md`'s reference-kind and Datafun-query design (`card:gex-sheet.md`, `card:gui-is-difficult.md`).
- **Norman**'s gulf-of-execution concept names the exact failure exemplified by defect F151 (`card:gui-is-difficult.md`), and Norman's gulfs are bridged by **direct manipulation**'s properties of distinct pictures and immediate feedback (`card:gui-is-difficult.md`).
- **Cooper**'s "represented model" concept is applied to Chart's command language and model, which narrow both execution and evaluation gulfs (`card:gui-is-difficult.md`).
- **DDD** (Domain-Driven Design) supplies the principle that identity is named, cited in the identity-resolution discussion (`card:gui-is-difficult.md`).
- **subgrammar.py** points to **Datafun** as a prior boundary-drawing effort similar to the audio-fragment problem (`journal/2026-08.md`).

## Method and philosophy

At a higher level, **manifesto.md** names the **Toyota Production System**'s *genba* (going to the actual place) and *jidoka* (systems reporting when wrong) as the industrial precedents behind two of its rules (`manifesto.md`, `journal/2026-08.md`), while its "set-based, not point-based" methodology is framed against **point-based design** as the more familiar alternative it departs from (`manifesto.md`).

Together these relations show that the tree's mechanisms are rarely presented as inventions in isolation; each is anchored to a named neighbour — whether an earlier Henri tool, an academic HCI concept, a discontinued project, or an industrial-management principle — with the explicit acknowledgment that this crediting work is still incomplete and awaits being written up formally (`doc/memory/README.md`, `doc/notes/notes-on-the-find.md`).

---
*citations: 11 resolve, 0 do not; 2 sentence(s) with no citation*
