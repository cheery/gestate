# doc/memory/ — what a session carries across, kept where you can read it

*Moved into the tree 2026-08-20, at Henri's ask: "go with 2, split by
kind."*  Until that morning this corpus lived in
`~/.claude/projects/-home-cheery-gestate/memory/` — 28 files, 2,386
lines, unversioned, on one machine, and the author had never read it.
It was larger than the five capped method documents put together.

**One fact per file, and the filename is the id.**  Same property as a
card and an F-number: `[[gestate-atlas]]` resolves, and keeps resolving,
because the name does not move when the content changes.

---

## The split, and what it is a split about

**A memory that is about the work lives here.  A memory that is about
the person stays private.**

| kind | where | why |
|---|---|---|
| `project` | this directory | the work's own state — it belongs to the tree that has the work in it |
| `feedback` | this directory | how the work is to be done; it is method, and the standard copies it |
| `reference` | this directory | pointers outward, useful to anybody |
| `user` | private only | who the author is, how he rests, what he is paid for — the repository is public |

Three files were held back on the day of the move and are named here so
that holding them back is a decision rather than an omission:

* `henri-cofounder-separation.md` — `user`, by the rule above.
* `gestate-janne-and-mikko.md` — `project`, but it is about two people
  who consented to being named and not to this.  `doc/consent.md` is the
  register and it is the author's call, not a session's.
* `gestate-next-session.md` — 747 lines, a third of the whole corpus.
  It is a running log rather than a fact, and it carries the same two
  names.  It comes in when it is split into memories.

## Why the bodies are here and the hooks are not

The private `MEMORY.md` index is loaded into **every** session before it
knows what it is working on — the same cost the five method documents
have and the reason they are capped (`spec/rules.md`).  The bodies are
not: they are read when something makes them relevant.

So the index keeps its one-line hooks and points here, and the bodies
live in the tree.  That is `spec/`'s property, deliberately: **a
directory costs nothing until you open the file you needed.**  It also
means there is exactly one copy of each memory, which is the only
version of this that cannot drift.

## Writing one

Frontmatter, then the fact:

    ---
    name: <the filename, without .md>
    description: <one line — this is what recall reads>
    metadata:
      type: project | feedback | reference
    ---

For `feedback` and `project`, follow the fact with **Why:** and **How to
apply:**.  Convert relative dates to absolute — *"last Tuesday"* rots
and `2026-08-18` does not.  Link with `[[name]]`; a link to a memory
that does not exist yet is fine, and marks one worth writing.

`test/test_memory.py` is the gate: frontmatter present, `name` matching
the filename, a type that belongs in a public tree, and every file
indexed below exactly once.

**Henri writes here too.**  This directory is not a session's scratch
space — it is the shared one, and a memory he writes outranks one a
session inferred.

---

## The index

- [The instruments a session has](gestate-instruments.md) — `doc/instruments.md`: gemba, the andon, the wrist clock, `suite.py --gates` and the pre-commit hook; build a missing capability the moment the need arises, and a number nobody asked for is a number nobody checks (F169)
- [Gestate verify workflow](gestate-verify-workflow.md) — fast LLVM render path, `audioperform -o`, headless LazyPerformer harness for dynamic scores, control-sweep clamping
- [Gestate language pitfalls](gestate-language-pitfalls.md) — sown clips to ONE beat, `!` binding, fragment rules; OPEN: clipped cycle-of-rests diverges the stream walk
- [Test what a person would do](test-what-a-person-would-do.md) — try the naive thing before declaring it done; a harness built from the implementation cannot find a missing affordance
- [Henri's working style](henri-working-style.md) — explorative docs, reuse existing machinery, targeted tests; he writes short on purpose, so go and look before asking; and work set-based
- [The work laptop](gestate-work-laptop.md) — gestate on Ubuntu 26.04 since 2026-08-17; a fresh install is the only honest read of `doc/install.md`
- [The board goal, and the shelved-on-arrival exception](gestate-board-goal.md) — four fewer, zero new, stop proposing cards; a card Henri owns may arrive straight into `board/later/`
- [The atlas: five generated A3 sheets](gestate-atlas.md) — `python -m gestate.atlas`; two wire poka-yokes, the stamp rule, and the set is CLOSED at five
- [Segfault on quit: the two-stop audio teardown](gestate-audio-teardown.md) — a held sound card blocks the fade, so `halt` + `snd_pcm_drop`; never free the host while its thread lives
- [Editor lag: the one-behind bug and how to measure it](gestate-editor-latency.md) — idle frames must still present; `GESTATE_EDITOR_TIME`, `tools/lagcheck.py`, XTEST via ctypes
- [The canvas lost its callers](gestate-canvas-unwired.md) — `observe`/`touch` orphaned by the pygame deletion; `elapsed` is dead on the canvas
- [Test properly from now on](gestate-testing-standard.md) — where gestate's tests are strong, where every defect actually comes from, and what to do about it
- [Push back on unsafe asks](henri-pushback-on-unsafe-asks.md) — hold, name the risk, commit when the evidence lands
- [Kanban commits](henri-kanban-commits.md) — Henri gives the title when he wants a commit; Claude writes the body and co-authors; never commit unprompted
- [B4 score box, built](gestate-scorebox-design.md) — `notes <expr>` roll shipped 2026-08-14; never slice by span, class-method dicts, F136
- [Salvage week](gestate-salvage-week.md) — Henri's earlier music projects, read for what survives translation
- [Don't conclude from a shallow check](dont-conclude-from-a-shallow-check.md) — an empty result from a guessed-at search is evidence about the search, not the world
- [The andon](gestate-andon.md) — `tools/andon.sh` rings the sound card to reach Henri while he rests; capped at three, batch the questions first
- [The fence, and what it denies me](gestate-hardening.md) — `tools/sandbox.sh --check` must say *the fence is up*; the deny-list blocks a session's own `sudo` on purpose
- [The ungated-fixes sweep](gestate-ungated-sweep.md) — 62 entries, five a session capped; the plan is `card:ungated-fixes.md`
- [Subagents are his call](henri-subagents.md) — propose one and wait; and none is spawned without a way to raise a question and be answered
- [The blind three-model test](gestate-blind-model-test.md) — clones not worktrees, keep the mapping out of the shared parent; haiku won on form and was wrong on F153
- [House rules on authorship](gestate-house-rules-authorship.md) — `spec/author.md` is his to keep; gemba is opt-in
- [Decisions arrive shaped](decisions-arrive-shaped.md) — three gates before a question reaches Henri; a default with a trigger is the part usually missing, and questions come batched
- [Sediment versus debt](sediment-versus-debt.md) — a shelved card waiting on an event costs nothing; one waiting on a decision compounds — *waiting on an event, or on me?*
- [Capacity is not a caller](capacity-is-not-a-caller.md) — "I can" is not a `because`; software is kept, not written, and there is one keeper — the three legitimate pulls
- [Weights, context, suite](weights-context-suite.md) — weights for what the model must know, context for what it must currently obey, suite for what must be guaranteed; the rules never go into weights
- [Smaller models and the tree](smaller-models-and-the-tree.md) — structural rules survive, judgment norms go first, initiative goes furthest; the afternoon experiment, and the distilled front
- [Sessions write where readers read](sessions-write-where-readers-read.md) — why memories leak into rule files, and that editing one is unreviewed authorship the seam list does not name
- [The evaluation loop](the-evaluation-loop.md) — a session judging this method is a product of it; say the loop out loud, and route the real check to a stranger
- [Mechanism, not instructions](mechanism-not-instructions.md) — the idea is widely converged on; rules held by a suite are what is uncommon, so a copy takes the mechanisms and not the prose
- [Where the method comes from](method-sources.md) — Adler's separation of tasks, Socratic dialogue and the epoché are already rules here, uncredited; crediting them is `spec/author.md` and Henri's to write
- [The keeper's evening](the-keepers-evening.md) — **proposed, not adopted**: one evening a week, measure one rule, compact one file, refresh one date; and it must never become a demand
- [Why models hallucinate](why-models-hallucinate.md) — five layers, and why this tree's verification rules are the fix at the right layer; fluency is no evidence, including your own
- [The 2000-line cap on the rules](gestate-rules-cap.md) — five documents, closed set, `spec/rules.md`; the fat is session narration
