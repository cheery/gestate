*This is a model's reading of a model's extraction of the tree — testimony, not evidence.  `card:graphrag-c.md`.*

**Question:** What are the method's neighbours — the prior art each of the tree's mechanisms already has a name in?

*keywords (claude-haiku-4-5-20251001): low ['tree', 'mechanisms', 'methods', 'prior art']; high ['prior art', 'naming conventions', 'algorithmic foundations', 'related work', 'mechanism design']*  
*retrieved: 1035 entities matched + 1580 by one hop, 5545 relations (121 in the context); ranking split; 40002 chars (cut); answer by claude-sonnet-5; 15922 in, 1298 out, $0.066 at assumed prices*

## Prior art behind the tree's mechanisms

The context identifies a cluster of named prior-art sources for the tree's mechanisms, concentrated in `doc/notes/notes-on-the-find.md` and `doc/memory/method-sources.md`, plus scattered software/design precedents.

**Explicit ingredient citations in `doc/notes/notes-on-the-find.md`:** This document lists several works as "ingredients of the tree":
- Ford, Parsons, Kua 2017 — on fitness functions (`doc/notes/notes-on-the-find.md`)
- Nygard 2011 — on ADRs (Architecture Decision Records) (`doc/notes/notes-on-the-find.md`)
- Martraire 2019 — on Living Documentation (`doc/notes/notes-on-the-find.md`)
- Rother 2009 — on Toyota Kata (`doc/notes/notes-on-the-find.md`)
- Poppendieck 2003 (`doc/notes/notes-on-the-find.md`)
- Anderson 2010 (`doc/notes/notes-on-the-find.md`)

The same document also suggests that a paragraph on prior art might belong in a separate memory document called `method-sources` rather than in `spec/author.md` (`doc/notes/notes-on-the-find.md`).

**`doc/memory/method-sources.md`:** One relation names Adler's "separation of tasks" — sourced from *The Courage to Be Disliked*, itself framed as a Socratic dialogue — as feeding this document (`doc/memory/method-sources.md`).

**Software/design precedents for specific mechanisms (outside the "ingredients" list above but tagged as prior art in the context):**
- `mide-staves-ui` cites **Garnet** and **Amulet** as "prior art on the whole idea of constraint-based interactors and what breaks," and cites **Eve** as the system "closest in ambition to staves.ui but was discontinued" (`doc/memory/mide-staves-ui.md`).
- `card:gui-is-difficult.md` cites **DDD** (Domain-Driven Design) for the principle that "identity is named," relevant to an identity-resolution discussion (`card:gui-is-difficult.md`).
- `card:gex-sheet.md` cites **Pad++** as prior work on zooming interfaces, addressing a sheet zoom-level requirement (`card:gui-is-difficult.md`).
- `subgrammar.py` treats the monomorphic **Datafun** sublanguage as a prior boundary-drawing effort analogous to the audio fragment (`journal/2026-08.md`).
- Henri's own prior tools — **oscillseq**, **beet**, and **mide** — are repeatedly invoked as working examples that answer open design questions, e.g. oscillseq's four transport states informing `card:transport-modes.md`, oscillseq's (pitch, accidental) pair design informing `arc.notes`, and mide's datalog-based UI informing `card:relational-model.md` (`doc/memory/henri-prior-tools.md`, `card:transport-modes.md`, `journal.md`, `card:relational-model.md`).
- `retargeting-not-reversal` cites **Anthropic's sycophancy work (2023)** as evidence that preference signals order sycophancy in training (`doc/memory/retargeting-not-reversal.md`).

**Caveat:** The context does not present a single unified list mapping each named "mechanism" of "the tree" one-to-one to a prior-art source; instead it offers these scattered citations across several documents, and no document explicitly enumerates "the tree's mechanisms" alongside a complete table of their precedents.

---
*citations: 12 resolve, 0 do not; 1 sentence(s) with no citation*
