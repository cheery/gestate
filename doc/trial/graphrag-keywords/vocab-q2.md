*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What are the method's neighbours — the prior art each of the tree's mechanisms already has a name in?

*keywords (claude-haiku-4-5-20251001, vocab): low ['doc/memory/henri-prior-tools.md', 'method-sources', 'spec/north_star.md', 'manifesto.md', 'vision.md']; high ['prior art', 'design principle', 'reference', 'related concept', 'methodology']; 4 of 5 high keywords are tags in the store*  
*retrieved: 962 entities matched + 1546 by one hop, 5319 relations (111 in the context); ranking split; 40002 chars (cut); answer by claude-sonnet-5; 16741 in, 2697 out, $0.087 at assumed prices*

# Method's Neighbours: Prior Art Already Naming the Tree's Mechanisms

The memory document **method-sources** is explicitly the place where this question is raised: it is described as "a memory document for method sources and prior art" and as "a document already noting that Henri's sources should be written," with the further note that crediting these sources properly is a task left to `spec/author.md` and to Henri (`doc/notes/notes-on-the-find.md`). The core claim, per `doc/memory/README.md`, is that several of the project's mechanisms are already rules that exist uncredited under other names: **Adler's separation of tasks**, **Socratic dialogue**, and **the epoché**. These three are named as prior art the project's own practices duplicate without acknowledgment, and `doc/notes/notes-on-the-find.md` even suggests the paragraph about this prior art might belong in `method-sources` rather than in `spec/author.md`.

Beyond that core trio, other relations in the context show the same pattern of "this mechanism already has a name elsewhere" scattered across documents, functioning as neighbours to the method:

- **Toyota Production System** concepts are cited directly: `manifesto.md` states that its rule about systems reporting when they are wrong is the **jidoka** principle applied to the project (`journal/2026-08.md`), and **genba** ("go to the actual place and act") is named as a Toyota Production System principle underlying the project's practice (`manifesto.md`).
- **Norman's** gulfs of execution and evaluation are cited as the naming for GUI-difficulty phenomena: defect F151 is said to exemplify "Norman's gulf of execution," where an action exists but no path to it does, and Norman's gulf concepts are described as bridged by **direct manipulation**'s properties of distinct pictures and immediate feedback (`card:gui-is-difficult.md`).
- **Cooper's** notion of a "represented model" is applied to the Chart mechanism's command language, which is said to narrow both execution and evaluation gulfs (`card:gui-is-difficult.md`).
- **Domain-Driven Design (DDD)**'s principle that identity is named is cited as bearing on the project's identity-resolution discussion (`card:gui-is-difficult.md`).
- Constraint-based interactor prior art is named for the `mide-staves-ui` mechanism: **Garnet** and **Amulet** are called "prior art on the whole idea of constraint-based interactors and what breaks," while **Eve** is named as the tool "closest in ambition to staves.ui" before being discontinued (`doc/memory/mide-staves-ui.md`).
- **Pad++** is cited as prior work on zooming interfaces, directly answering the sheet zoom-level requirement in `card:gex-sheet.md` (`card:gui-is-difficult.md`).
- Asimov's **Zeroth Law** is invoked as the exact failure the sitting-limit mechanism exists to prevent — robot self-appointment — giving that guard a prior name (`card:sitting-limit.md`).
- Henri's own earlier instruments — **oscillseq**, **mide**, **xylem** — are treated as a closer, in-house layer of prior art: `doc/memory/henri-prior-tools.md` documents that each already answered a GUI challenge the current tree faces, such as oscillseq's transport states informing `card:transport-modes.md` and its (pitch, accidental) pair design informing `arc.notes` (`card:transport-modes.md`, `journal.md`).

Taken together, these relations describe the same shape as `method-sources`: mechanisms in the tree — separation of concerns, dialogic checking, epistemic suspension, error-signaling, floor-level correction, gulf-bridging by direct manipulation and represented models, named identity, constraint propagation, zooming, and self-limiting guards — are neighbours to established traditions (Adler, Socratic method, phenomenology, TPS, Norman, Cooper, DDD, Garnet/Amulet/Pad++/Eve, Asimov, and Henri's own earlier tools), and the project has, per the sources cited, not yet finished writing down that lineage.

---
*citations: 12 resolve, 0 do not; 1 sentence(s) with no citation*
