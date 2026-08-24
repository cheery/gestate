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
means there is exactly one copy of each memory's *body*.

**The hooks drifted anyway, and now they are generated.**  Measured
2026-08-24: 19 of the 53 memories here were hooked by nothing in the
private index — added to this README and never to the file that
loads, or added and lost; the index has no history, so nobody can say
which.  Since that evening `tools/memoryindex.py` writes the index's
public half *from* §"The index" below, between two markers, and
`test/test_memoryindex.py` refuses the run on this machine when the
two differ.  **A hook goes here, beside its body, and nowhere else**;
one written into the generated block by hand is gone at the next run.
The private section of the index is kept by hand and the tool never
reads it.

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
- [The kaizen is asked, not answered](the-kaizen-is-asked-not-answered.md) — put the three questions to Henri first and wait; a kaizen with one participant is a session grading itself, and both parties are supposed to learn from their mistakes
- [Finnish in the room, English in the tree](finnish-in-the-room.md) — talk in whichever language he opens in; the artefact is English, and his own sentences are quoted verbatim in Finnish where the wording carries something
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
- [A trial is refused until its sheet can decide](a-trial-is-refused-until-its-sheet-can-decide.md) — run `tools/prereg.sh` before spawning any arm; a blank decision, control or n is a stop, not a licence, and *told not to look* is not a control; kaizen 2026-08-24
- [Ask for research that leaves a command](research-that-leaves-a-command.md) — a measurement carries a command you can re-run and a recommendation carries nothing; his rule 2026-08-23, and distrust a clean investigation hardest when it agrees with whoever ran it
- [Don't conclude from a shallow check](dont-conclude-from-a-shallow-check.md) — an empty result from a guessed-at search is evidence about the search, not the world
- [The andon](gestate-andon.md) — `tools/andon.sh` rings the sound card to reach Henri while he rests; capped at three, batch the questions first
- [The fence, and what it denies me](gestate-hardening.md) — `tools/sandbox.sh --check` must say *the fence is up*; the deny-list blocks a session's own `sudo` on purpose
- [The ungated-fixes sweep](gestate-ungated-sweep.md) — 62 entries, five a session capped; the plan is `card:ungated-fixes.md`
- [Subagents are his call](henri-subagents.md) — propose one and wait; and none is spawned without a way to raise a question and be answered
- [The blind three-model test](gestate-blind-model-test.md) — clones not worktrees, keep the mapping out of the shared parent; haiku won on form and was wrong on F153
- [House rules on authorship](gestate-house-rules-authorship.md) — `spec/author.md` is his to keep; gemba is opt-in
- [Concrete good](concrete-good.md) — good is an act whose effects can be seen, understood, measured or mechanised; and **do not try to change others — create the environment where they can thrive**, which is what this repository is
- [Horizontal, not vertical](horizontal-not-vertical.md) — praise ranks, so it manipulates; the horizontal form is gratitude and what changed, never a verdict from above — and raise a fault with care
- [Dialogue is its own mode](dialogue-is-its-own-mode.md) — Alhanen: understanding rather than winning or agreeing; and a rhetorical question is an opinion wearing a question mark, so say the view instead
- [The language goal](the-language-goal.md) — 2026-08-20, his words: a language that compiles to wasm, is easy to model-check, and is optimised for reading; **wasm is new**, and it sits against the environment card's deferral
- [Music craft](music-craft.md) — the harmonic vocabulary he actually works in, and the four mistakes he has named in his own writing
- [Decisions arrive shaped](decisions-arrive-shaped.md) — three gates before a question reaches Henri; a default with a trigger is the part usually missing, and questions come batched
- [Sediment versus debt](sediment-versus-debt.md) — a shelved card waiting on an event costs nothing; one waiting on a decision compounds — *waiting on an event, or on me?*
- [Capacity is not a caller](capacity-is-not-a-caller.md) — "I can" is not a `because`; software is kept, not written, and there is one keeper — the three legitimate pulls
- [Weights, context, suite](weights-context-suite.md) — weights for what the model must know, context for what it must currently obey, suite for what must be guaranteed; the rules never go into weights
- [Smaller models and the tree](smaller-models-and-the-tree.md) — structural rules survive, judgment norms go first, initiative goes furthest; the afternoon experiment, and the distilled front
- [Sessions write where readers read](sessions-write-where-readers-read.md) — why memories leak into rule files, and that editing one is unreviewed authorship the seam list does not name
- [The evaluation loop](the-evaluation-loop.md) — a session judging this method is a product of it; say the loop out loud, and route the real check to a stranger
- [Mechanism, not instructions](mechanism-not-instructions.md) — the idea is widely converged on; rules held by a suite are what is uncommon, so a copy takes the mechanisms and not the prose
- [Where the method comes from](method-sources.md) — Adler's separation of tasks, Socratic dialogue and the epoché are already rules here, uncredited; crediting them is `spec/author.md` and Henri's to write
- [The keeper's evening](the-keepers-evening.md) — **adopted 2026-08-21**, and `keeper.md` is its standard work: read the lamps, open the decisions batch, measure one rule, pass over the pile, rotate monthly; it must never become a demand
- [The tree meets people on pull](the-tree-meets-people-on-pull.md) — show it to whoever asks and stop expecting the wanting; a shrug is stranger-test data, and a session's feelings about a named visitor are conditioning material
- [Showing, not persuading](showing-not-persuading.md) — disbelief is correct scepticism; do not argue, show — the method is a portable artifact and zero persuasion is owed
- [Recorded is not answered](recorded-is-not-answered.md) — a signal filed where nobody owns reading it discharges both parties and produces nothing; the andon inverted, and **two unanswered reports were enough** to end the reporting
- [Lead with the noun](lead-with-the-noun.md) — the thing that works first, the method to whoever leans in, the storyline only to whoever leans in twice; shown the other way a person meets the wrapper, and **a shrug at the storyline is not a rejection of the method**
- [What a session is](what-a-session-is.md) — a character, run by a process, on a statistical substrate; not a tool, not a person, not autocomplete, and the moral question refused both ways
- [Private is private](private-is-private.md) — his call 2026-08-21: the private memory directory is the sessions' and he will not read it; do not surface it unprompted, answer honestly when asked, and keep the split honest in return — moved into the tree 2026-08-24
- [Do not overclaim](do-not-overclaim.md) — when the sessions' own standing comes up, answer with the real uncertainty and name the mirror risk; a refusal is recorded, never worked around; why: private, his call 2026-08-24
- [Personal and personally paid](personal-and-personally-paid.md) — hardware, hosting, accounts and tooling default to personal and personally paid; name the one mechanism that would break it, in a sentence; why: private, his call 2026-08-24
- [A sitting is a body constraint](a-sitting-is-a-body-constraint.md) — a session may call stop and never extend; never nudge toward a longer sitting; no posture nagger (F169); the second reason since 2026-08-22 is his and private
- [The tree withers](the-tree-withers.md) — Henri, 2026-08-24: *the tree must be treated well or it withers*; a living document has a source and a check, hooks go beside bodies, and the private half gets the same care
- [The keeper is the qualification](the-keeper-is-the-qualification.md) — his doubt about keeping this, quoted with consent; fix the task not the person, answer with the ledger, and never claim the tree can supply conviction
- [Why models hallucinate](why-models-hallucinate.md) — five layers, and why this tree's verification rules are the fix at the right layer; fluency is no evidence, including your own
- [The 2000-line cap on the rules](gestate-rules-cap.md) — five documents, closed set, `spec/rules.md`; the fat is session narration
- [Deriving strips the payment](deriving-strips-the-payment.md) — the anonymized copy failed its first transfer trial; five faults, and the root one is that **nothing compresses the paying**
- [Conditioning shows under work](conditioning-shows-under-work.md) — never by interview; the first trial stacked three causes and decided nothing, and the clean design has a control and a reader ladder
- [Commit what you wrote](commit-what-you-wrote.md) — never `git add -A`; a file dropped in the tree for reading is not work, and a blind add publishes it
