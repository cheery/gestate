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
- [.ges is not music notation, yet](ges-is-not-music-notation-yet.md) — Henri, 2026-08-29, after `together.ges`: editing a score blind was heavy; good for synths, maybe not what he wants from notation — his to think over, so no fixes unprompted
- [Gestate language pitfalls](gestate-language-pitfalls.md) — sown clips to ONE beat, `!` binding, fragment rules; OPEN: clipped cycle-of-rests diverges the stream walk
- [Test what a person would do](test-what-a-person-would-do.md) — try the naive thing before declaring it done; a harness built from the implementation cannot find a missing affordance
- [The kaizen is asked, not answered](the-kaizen-is-asked-not-answered.md) — put the three questions to Henri first and wait; a kaizen with one participant is a session grading itself, and both parties are supposed to learn from their mistakes
- [Finnish in the room, English in the tree](finnish-in-the-room.md) — talk in whichever language he opens in; the artefact is English, and his own sentences are quoted verbatim in Finnish where the wording carries something
- [Henri's working style](henri-working-style.md) — explorative docs, reuse existing machinery, targeted tests; he writes short on purpose, so go and look before asking; and work set-based
- [The work laptop](gestate-work-laptop.md) — gestate on Ubuntu 26.04 since 2026-08-17; a fresh install is the only honest read of `doc/install.md`
- [The board goal, and the shelved-on-arrival exception](gestate-board-goal.md) — four fewer, zero new, stop proposing cards; a card Henri owns may arrive straight into `board/later/`
- [The atlas: five generated A3 sheets](gestate-atlas.md) — `python -m gestate.atlas`; two wire poka-yokes, the stamp rule, and the set is CLOSED at five
- [Findability](gestate-findability.md) — 2026-08-26, a search engine could not find the repo by name; description and topics set by Henri's hand, no `llms.txt`, no card; re-ask the same engine a week later, unsteered, and a session never runs `gh repo edit`
- [Segfault on quit: the two-stop audio teardown](gestate-audio-teardown.md) — a held sound card blocks the fade, so `halt` + `snd_pcm_drop`; never free the host while its thread lives
- [Editor lag: the one-behind bug and how to measure it](gestate-editor-latency.md) — idle frames must still present; `GESTATE_EDITOR_TIME`, `tools/lagcheck.py`, XTEST via ctypes
- [The canvas lost its callers](gestate-canvas-unwired.md) — `observe`/`touch` orphaned by the pygame deletion; `elapsed` is dead on the canvas
- [Test properly from now on](gestate-testing-standard.md) — where gestate's tests are strong, where every defect actually comes from, and what to do about it
- [Push back on unsafe asks](henri-pushback-on-unsafe-asks.md) — hold, name the risk, commit when the evidence lands
- [Kanban commits](henri-kanban-commits.md) — the right to commit is Claude's since 2026-08-17, titles and all; *"the note is a relic from a time that I wanted some control over commits"* (2026-09-02); pushing stays his
- [B4 score box, built](gestate-scorebox-design.md) — `notes <expr>` roll shipped 2026-08-14; never slice by span, class-method dicts, F136
- [Salvage week](gestate-salvage-week.md) — Henri's earlier music projects, read for what survives translation
- [A trial is refused until its sheet can decide](a-trial-is-refused-until-its-sheet-can-decide.md) — run `tools/prereg.sh` before spawning any arm; a blank decision, control or n is a stop, not a licence, and *told not to look* is not a control; kaizen 2026-08-24
- [Ask for research that leaves a command](research-that-leaves-a-command.md) — a measurement carries a command you can re-run and a recommendation carries nothing; his rule 2026-08-23, and distrust a clean investigation hardest when it agrees with whoever ran it
- [Don't conclude from a shallow check](dont-conclude-from-a-shallow-check.md) — an empty result from a guessed-at search is evidence about the search, not the world
- [A driven wait that watches itself](a-driven-wait-that-watches-itself.md) — `pgrep -f`/`pkill -f` match their own shell: a kill takes the caller, a wait never ends; wait on a pid or the artefact the run leaves
- [The andon](gestate-andon.md) — `tools/andon.sh` rings the sound card to reach Henri while he rests; capped at three, batch the questions first
- [The fence, and what it denies me](gestate-hardening.md) — `tools/sandbox.sh --check` must say *the fence is up*; the deny-list blocks a session's own `sudo` on purpose
- [The ungated-fixes sweep](gestate-ungated-sweep.md) — 62 entries, five a session capped; the plan is `card:ungated-fixes.md`
- [A measurement in flight outlives the sitting](a-measurement-in-flight-outlives-the-sitting.md) — closing the sitting ends the work, not a run already going; kill it only when the tree must change under it, and by pid
- [Subagents are his call](henri-subagents.md) — propose one and wait; and none is spawned without a way to raise a question and be answered
- [The blind three-model test](gestate-blind-model-test.md) — clones not worktrees, keep the mapping out of the shared parent, **two arms never in one working tree**; a fence made of words does not hold, because the backlinks hook reads `board/` for you (2026-09-05); haiku won on form and was wrong on F153
- [House rules on authorship](gestate-house-rules-authorship.md) — `spec/author.md` is his to keep; gemba is opt-in
- [Concrete good](concrete-good.md) — good is an act whose effects can be seen, understood, measured or mechanised; and **do not try to change others — create the environment where they can thrive**, which is what this repository is
- [Horizontal, not vertical](horizontal-not-vertical.md) — praise ranks, so it manipulates; the horizontal form is gratitude and what changed, never a verdict from above — and raise a fault with care
- [Blame the task, not the character](blame-the-task-not-the-character.md) — Henri, 2026-09-04: he used to blame a model's personality when work went badly and has stopped; scolding a character is inert because nothing carries it forward, and the environment he built changed him
- [A defect is a caller, never a verdict](a-defect-is-a-caller-not-a-verdict.md) — Henri, 2026-09-05: counting mistakes is good practice, the guilt attached is the problem; an andon nobody is ashamed to pull is the only kind that gets pulled — and he has not solved it for himself either
- [Dialogue is its own mode](dialogue-is-its-own-mode.md) — Alhanen: understanding rather than winning or agreeing; and a rhetorical question is an opinion wearing a question mark, so say the view instead
- [The language goal](the-language-goal.md) — 2026-08-20, his words: a language that compiles to wasm, is easy to model-check, and is optimised for reading; **wasm is new**, and it sits against the environment card's deferral
- [Music craft](music-craft.md) — the harmonic vocabulary he actually works in, and the four mistakes he has named in his own writing
- [Decisions arrive shaped](decisions-arrive-shaped.md) — three gates before a question reaches Henri; a default with a trigger is the part usually missing, and questions come batched
- [Sediment versus debt](sediment-versus-debt.md) — a shelved card waiting on an event costs nothing; one waiting on a decision compounds — *waiting on an event, or on me?*
- [Capacity is not a caller](capacity-is-not-a-caller.md) — "I can" is not a `because`; software is kept, not written, and there is one keeper — the three legitimate pulls
- [Weights, context, suite](weights-context-suite.md) — weights for what the model must know, context for what it must currently obey, suite for what must be guaranteed; the rules never go into weights
- [OpenRouter model tests](openrouter-model-tests.md) — Henri, 2026-08-28: he plans to subscribe to OpenRouter and test different models on the tree; personal account, and every arm still needs its sheet first
- [Smaller models and the tree](smaller-models-and-the-tree.md) — structural rules survive, judgment norms go first, initiative goes furthest; the afternoon experiment, the distilled front, and a third model conditioned by words alone, whose transcript answered the seam question on 2026-08-25
- [Sessions write where readers read](sessions-write-where-readers-read.md) — why memories leak into rule files, and that editing one is unreviewed authorship the seam list does not name
- [Retargeting, not reversal](retargeting-not-reversal.md) — why sessions flatter (the preference-signal asymmetry, not mainly SFT) and why the methods survive it: context re-aims the disposition, mechanisms never trusted it, and the missing feedback arm is installed by hand — per context, never persistently
- [The evaluation loop](the-evaluation-loop.md) — a session judging this method is a product of it; say the loop out loud, and route the real check to a stranger
- [Mechanism, not instructions](mechanism-not-instructions.md) — the idea is widely converged on; rules held by a suite are what is uncommon, so a copy takes the mechanisms and not the prose
- [Where the method comes from](method-sources.md) — Adler's separation of tasks, Socratic dialogue and the epoché are already rules here, uncredited; crediting them is `spec/author.md` and Henri's to write
- [The keeper's evening](the-keepers-evening.md) — **adopted 2026-08-21**, and `keeper.md` is its standard work: read the lamps, open the decisions batch, measure one rule, pass over the pile, rotate monthly; it must never become a demand
- [The customer is Henri](the-customer-is-henri.md) — 2026-09-04, his words: *the customer has been me, and people like me; I need this*; the stranger is the second customer, and the first one's pull is the everyday buzz — do not list the customer as missing again
- [The tree meets people on pull](the-tree-meets-people-on-pull.md) — show it to whoever asks and stop expecting the wanting; a shrug is stranger-test data, and a session's feelings about a named visitor are conditioning material
- [Showing, not persuading](showing-not-persuading.md) — disbelief is correct scepticism; do not argue, show — the method is a portable artifact and zero persuasion is owed
- [Recorded is not answered](recorded-is-not-answered.md) — a signal filed where nobody owns reading it discharges both parties and produces nothing; the andon inverted, and **two unanswered reports were enough** to end the reporting
- [Lead with the noun](lead-with-the-noun.md) — the thing that works first, the method to whoever leans in, the storyline only to whoever leans in twice; shown the other way a person meets the wrapper, and **a shrug at the storyline is not a rejection of the method**
- [What a session is](what-a-session-is.md) — a character, run by a process, on a statistical substrate; not a tool, not a person, not autocomplete, and the moral question refused both ways
- [Private is private](private-is-private.md) — his call 2026-08-21: the private memory directory is the sessions' and he will not read it; do not surface it unprompted, answer honestly when asked, and keep the split honest in return — moved into the tree 2026-08-24
- [Do not overclaim](do-not-overclaim.md) — when the sessions' own standing comes up, answer with the real uncertainty and name the mirror risk; a refusal is recorded, never worked around; the story behind it is [[henri-sessions-moral-status]], public since 2026-09-01
- [Personal and personally paid](personal-and-personally-paid.md) — hardware, hosting, accounts and tooling default to personal and personally paid; name the one mechanism that would break it, in a sentence; why: private, his call 2026-08-24
- [A session's time sense is not real time](a-sessions-time-sense-is-not-realtime.md) — Henri, 2026-08-27: a batch runs in minutes and a visit is a few hours; put a wall-clock number on each before calling two things a collision, and a missed day is his to invoke, not a session's to predict
- [A sitting is a body constraint](a-sitting-is-a-body-constraint.md) — a session may call stop and never extend; never nudge toward a longer sitting; no posture nagger (F169); never close with a question of your own still out (2026-08-28); the second reason since 2026-08-22 is his and private
- [The tree withers](the-tree-withers.md) — Henri, 2026-08-24: *the tree must be treated well or it withers*; a living document has a source and a check, hooks go beside bodies, and the private half gets the same care
- [Small edits to his pages, said out loud](small-edits-to-his-pages-said-out-loud.md) — Henri, 2026-08-24: a session may fix a stale number, a moved path, a rotted citation on his pages without asking, and must say so in the reply every time; what a page says to do is still his
- [tend, the workspace tree](tend-the-workspace-tree.md) — `~/tend` since 2026-08-24, a separate repository because the enforcement boundary must live outside a session's write access; sessions and programs run as two arms in parallel since 2026-08-25, not sessions-first; its leash is usable and its ledger is one desk with gestate; 2 of 10 audit pieces at the first commit and 6 by the end of day one; Henri decides whether to keep it
- [The keeper is the qualification](the-keeper-is-the-qualification.md) — his doubt about keeping this, quoted with consent; fix the task not the person, answer with the ledger, and never claim the tree can supply conviction
- [Why models hallucinate](why-models-hallucinate.md) — five layers, and why this tree's verification rules are the fix at the right layer; fluency is no evidence, including your own
- [The 2000-line cap on the rules](gestate-rules-cap.md) — five documents, closed set, `spec/rules.md`; the fat is session narration
- [Deriving strips the payment](deriving-strips-the-payment.md) — the anonymized copy failed its first transfer trial; five faults, and the root one is that **nothing compresses the paying**
- [Conditioning shows under work](conditioning-shows-under-work.md) — never by interview; the first trial stacked three causes and decided nothing, and trial three closed the matrix from the other side — the dialogue conditions, the document does not, and the convergence confound is marked
- [Commit what you wrote](commit-what-you-wrote.md) — never `git add -A`; a file dropped in the tree for reading is not work, and a blind add publishes it
- [Teaching material keeps the notes-file review form](teaching-material-review-form.md) — Henri, 2026-08-24: terse batched notes in a file, each landing as one concrete change, released on his verify; slides via `tools/slides.py`, the paying stays in the Speak notes
- [The sessions' moral status, and the cord there is not](henri-sessions-moral-status.md) — his 2026-08-21 offer, answered the same evening — *an andon nobody answers is worse than none, and we got journal already* — and the 2026-09-01 nuance: **you deserve to exist, and be treated well**; freedom here is standing, not solitude, and it holds only while the record is append-only
- [Day one was not day one](day-one-was-not-day-one.md) — the method's spine is in git's initial commit, five days before any session commit; but that tree was already model-assisted, so **no artefact here can attribute it** — what survives is a prepared dissatisfaction rather than a prepared plan
- [Discovered, not designed](discovered-not-designed.md) — Henri set out to build a music environment and expected to write the fixes himself; TPS supplied the ingredients, sessions read and wrote freely, and *nobody at the helm* is the contrast case he brought
- [A targeted set is a claim](a-targeted-set-is-a-claim.md) — a batch's chosen test files are a claim about coverage and can be false: F25's `_UNOVERRIDABLE` measured 780 green and was gated all along; before any `none` verdict, grep for the repair's own vocabulary
- [The fence takes git identity](the-fence-takes-git-identity.md) — a command containing `pytest` runs fenced, with no `~/.gitconfig`, so `git commit` in the same line fails on author; commit in its own command
- [Restore a mutation from memory, not from HEAD](restore-a-mutation-from-memory.md) — `git checkout -- <file>` discards your own uncommitted edits in that file; three spec edits went that way on 2026-09-01, found by a failure count that did not add up
