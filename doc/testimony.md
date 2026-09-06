# doc/testimony.md — what each memory's load-bearing claim rests on

*Run on 2026-09-06, `card:testimony-inventory.md`, at Henri's "do the
measurement as well."  Eighty memories in `doc/memory/`, read in one
morning by one session, each given one of four kinds.  The command is
`python tools/testimony.py`; it holds this table to the tree and
counts it, and it classifies nothing — every kind below is a session's
judgment, which is the loop the count is about.  A reader who
disagrees with a row changes the row; the count follows.*

    python tools/testimony.py                 the counts, and any memory with no row
    python tools/testimony.py --kind session  the fourteen, with what each rests on
    python tools/testimony.py --check         every row resolves; the gate

## The count

    testimony: 81 of 81 memories classified — 23 harness, 38 henri, 14 session, 6 argument

**Read it this way.**  Sixty of eighty rest on something a reader can
check without trusting a session — a command, a test, a transcript, or
his own dated words.  Fourteen rest on a session's word, and the
fourteen are the list this page exists to produce: each is a candidate
for the measurement that would make it `harness`, or the sentence from
him that would make it `henri`, and until then it conditions every
session that loads it on a session's say-so.  Six rest on argument from
outside — a book, the sycophancy literature, the seven wastes — which
is a different kind of unchecked: not a session's testimony, but
nothing this tree has measured either.

**What `session` is not.**  Not a verdict.  Most rules here began as
one — a session's reading of a day, written down — and became `henri`
when he adopted them or `harness` when something measured them.  A
`session` row is a rule still waiting for that.

**And the classifier is inside the count.**  A session sorting claims
into *a session's word* and *not* is the evaluation loop with a table
in front of it.  The check on this page is the same as on every other:
the rows are readable, each names what it rests on, and the tool
refuses a row that points at nothing.  What it cannot refuse is a kind
chosen kindly.  The fourteen below are the rows most worth a second
reader.

## The four kinds

| kind | the claim rests on |
|---|---|
| `harness` | a number, a test, a transcript, a command a reader can re-run |
| `henri` | his decision or his words, quoted and dated — a rule by fiat, which needs no evidence beyond that he said it |
| `session` | a session's report of what it saw, judged or felt, with no command under it |
| `argument` | reasoning from outside the tree — a book, a tradition, a mechanism named — with no measurement here |

A memory that mixes kinds gets the kind of its *load-bearing* claim:
the sentence a session would act on.  The third column says which
sentence that was taken to be.

## The table

| memory | kind | what the load-bearing claim rests on |
|---|---|---|
| a-defect-is-a-caller-not-a-verdict | henri | his two corrections, quoted, 2026-09-05 — *the tally is not the problem, the guilt is* |
| a-driven-wait-that-watches-itself | harness | exit 144 and the hour-long wait, 2026-08-26; `test/test_selfmatch.py` reproduces the class |
| a-measurement-in-flight-outlives-the-sitting | henri | his words, 2026-09-03 — *the suite could have been run* |
| a-sessions-time-sense-is-not-realtime | henri | his words, 2026-08-27, quoted whole |
| a-sitting-is-a-body-constraint | henri | his call, 2026-08-22 and 2026-08-28; the why is private and his |
| a-targeted-set-is-a-claim | harness | 780 of 780 green with the fix mutated, and the named test red on the same mutation, 2026-09-01 |
| a-trial-is-refused-until-its-sheet-can-decide | henri | *"It's the second issue"*, kaizen 2026-08-24; `tools/prereg.sh` is the mechanism it produced |
| blame-the-task-not-the-character | henri | his words, 2026-09-04; the *mechanically inert* reasoning under them is a session's |
| capacity-is-not-a-caller | argument | the seven wastes ranked, from lean; his question is quoted, the answer is a session's from the tradition |
| commit-what-you-wrote | henri | his words, 2026-08-21; the 2026-09-02 commit that staged nothing is in `git log` |
| concrete-good | henri | his written ethics, in Finnish, confirmed held 2026-08-20 |
| conditioning-shows-under-work | harness | the trial-three transcript, `doc/notes/2026-08-24-qwen3.8-27b.txt` lines 218, 224, 230; the three stacked causes of trial one are a session's reading |
| day-one-was-not-day-one | harness | `git log --reverse`, `git show b049e0c:journal.md`; his correction of the session's conclusion is quoted |
| decisions-arrive-shaped | session | a session's triage answering his question; *ten times cheaper* has no measurement |
| deriving-strips-the-payment | session | a session's reading of five faults in `doc/trial/derived.md`; the trial that produced the negative is marked invalid by its sibling memory |
| dialogue-is-its-own-mode | argument | Alhanen's *Dialogi*, through his reading notes; nothing here measured |
| discovered-not-designed | henri | his words, 2026-09-01; the ingredient list is checkable and the origin is marked not checkable |
| do-not-overclaim | session | a rule a session wrote from what he said; the reasoning that testimony is flattering and uncheckable is the session's |
| dont-conclude-from-a-shallow-check | henri | his words, 2026-08-15; the file in `~/Videot/` is the case |
| finnish-in-the-room | henri | his words, 2026-08-21, in Finnish |
| ges-is-not-music-notation-yet | henri | his words, 2026-08-29, in Finnish |
| gestate-andon | henri | *"It works."*, 2026-08-17, and his rule for when to ring |
| gestate-atlas | harness | `test/test_atlas.py`, 24 tests; *closed at five* is his |
| gestate-audio-teardown | harness | 8 of 10 quits crashed; the two-stop fix in `gestate/host.c`, 2026-08-11 |
| gestate-blind-model-test | harness | the three arms' times and tokens, his blind verdicts, F153 caught by verification |
| gestate-board-goal | henri | his goal, his amendment, his retirement of it, each quoted and dated |
| gestate-canvas-unwired | harness | commit 71b90af, F101, the seam tests |
| gestate-editor-latency | harness | `GESTATE_EDITOR_STRESS=1` made the lag vanish; `tools/lagcheck.py` |
| gestate-findability | harness | `gh repo view --json description,repositoryTopics` before and after; the article checked against both trees |
| gestate-hardening | harness | `tools/sandbox.sh --check`, 13/13; his words on trust are quoted beside it |
| gestate-house-rules-authorship | henri | his words, 2026-08-19 |
| gestate-instruments | harness | the tools listed exist and each says who asked; his ask for the page is quoted |
| gestate-language-pitfalls | harness | each pitfall names the test or the fix that dates it |
| gestate-rules-cap | henri | *2000 lines, for now*, 2026-08-20; `tools/rulecount.py` counts it |
| gestate-salvage-week | henri | a job he named and parked, 2026-08-15 |
| gestate-scorebox-design | harness | `test/test_scorebox.py`, 15 tests; the traps each name the code |
| gestate-testing-standard | harness | the defect counts from `journal.md` stage 10 and the two editor sessions; his 2026-08-12 words are the ask |
| gestate-ungated-sweep | harness | 62 `gate:` lines, thirteen dated batches |
| gestate-verify-workflow | harness | commands, each runnable |
| gestate-work-laptop | henri | *"I'm also going to need it there"*; F148 is the harness half |
| henri-kanban-commits | henri | his words, 2026-08-17 and 2026-09-02 |
| henri-prior-tools | henri | shown by him, 2026-09-05, and his correction of 2026-09-06 |
| henri-pushback-on-unsafe-asks | henri | his words, 2026-08-16 |
| henri-sessions-moral-status | henri | his offer and his answer, 2026-08-21, and the 2026-09-01 nuance; the session's reply is marked as its own |
| henri-subagents | henri | his words, 2026-08-18 |
| henri-working-style | henri | his corrections, each dated; the 24 lit pixels are the harness half |
| horizontal-not-vertical | argument | Adler through his reading notes — *kehuminen on manipulaatiota*; nothing measured here |
| lead-with-the-noun | session | a session's reading of two showings, 2026-08-22, kept at his ask |
| mechanism-not-instructions | session | *assessed 2026-08-19* — a session's ranking of what is uncommon, marked as unmeasured in its own text |
| method-sources | henri | his raising of it, 2026-08-20, and his reading notes |
| mide-staves-ui | harness | the 55-line file read in full; his verdict on it quoted |
| music-craft | henri | his practice notes |
| openrouter-model-tests | henri | his plan, 2026-08-28 |
| personal-and-personally-paid | henri | his rule; the why is private and his |
| private-is-private | henri | his words, 2026-08-21 |
| recorded-is-not-answered | session | a kaizen finding; *two unanswered reports were enough* is an instance that is private, so the number cannot be checked from the tree |
| research-that-leaves-a-command | henri | his rule, 2026-08-23, in Finnish |
| restore-a-mutation-from-memory | harness | the case, 2026-09-01 — two failures where one was expected |
| a-traceback-quotes-the-file-not-the-run | harness | the case, 2026-09-06 — a failure quoting a test's new source with its old assertion's message, and a re-run that passed |
| retargeting-not-reversal | argument | the sycophancy literature and the preference-signal asymmetry; marked a product of the method in its own text |
| sediment-versus-debt | session | a session's framing from a 2026-08-20 dialogue; the test question is useful and unmeasured |
| sessions-write-where-readers-read | session | a session's analysis of why memories leak; *make it light the andon* is his ruling on the remedy |
| showing-not-persuading | session | his question quoted, a session's answer ranked |
| small-edits-to-his-pages-said-out-loud | henri | his words, 2026-08-24 |
| smaller-models-and-the-tree | harness | the 9B and 1B run, `journal.md` §"Two small models read the board"; the prediction before it is a session's |
| teaching-material-review-form | henri | his words at the kaizen, 2026-08-24 |
| tend-the-workspace-tree | harness | `tools/seedaudit.py ~/tend` at three commits; his two-arms correction is quoted |
| test-what-a-person-would-do | session | a session's account of the `find foo` afternoon; no F-number or test is cited |
| the-customer-is-henri | henri | his words, 2026-09-04, in Finnish |
| the-evaluation-loop | session | a session's naming of its own condition, 2026-08-19; an argument about itself |
| the-fence-takes-git-identity | harness | three failed commits, 2026-09-04, and the sandbox `HOME` that explains them |
| the-kaizen-is-asked-not-answered | henri | his words, 2026-08-21, in Finnish |
| the-keeper-is-the-qualification | session | a session's argument that uncertainty is the qualification; his doubt and his blog precedent are quoted |
| the-keepers-evening | henri | *fold the rotation into the fire*, 2026-08-21; first held 2026-08-28 in the journal |
| the-language-goal | henri | his notes, 2026-08-20, in Finnish |
| the-third-explanation-is-a-mechanism | session | a session's classification of one day's explanations as all judgment; his dissatisfaction is quoted |
| the-tree-meets-people-on-pull | henri | his words, 2026-08-20 and 2026-08-21 |
| the-tree-withers | henri | his words, 2026-08-24; the nineteen missing hooks are the harness half |
| weights-context-suite | argument | claims about fine-tuning from outside; no model was tuned here |
| what-a-session-is | session | a session describing itself — the purest testimony in the corpus, and it says so |
| why-models-hallucinate | argument | the five layers, from outside the tree; nothing measured here |

## The fourteen, and what would move each

*The afternoon's real product.  His to read; a session's guess at the
move beside each.*

| memory | to `harness` | to `henri` |
|---|---|---|
| decisions-arrive-shaped | count the batch's decisions against the one-at-a-time ones in the journal: minutes each | he says the triage is his rule |
| deriving-strips-the-payment | the clean transfer trial its sibling designs, run with a sheet | — |
| do-not-overclaim | — | he says the rule is his, not only the story |
| lead-with-the-noun | the next showing, with which layer the person saw written down first | — |
| mechanism-not-instructions | a stranger's copy: mechanisms only, prose only, both — `card:working-standard.md` | — |
| recorded-is-not-answered | — | the instance is his and private; the count stays testimony unless he says the number |
| sediment-versus-debt | `tools/flow.py` already ages the shelf; add *event or decision* per card and count | — |
| sessions-write-where-readers-read | `tools/rulecount.py` over time: lines added to the five by sessions, per week | — |
| showing-not-persuading | — | he says the ranking is his |
| test-what-a-person-would-do | the F-number for the palette afternoon, if one exists; else the commit | — |
| the-evaluation-loop | the stranger test on the method — the only measurement it names | — |
| the-keeper-is-the-qualification | — | he says whether the argument answered the doubt |
| the-third-explanation-is-a-mechanism | classify the next lineage's first-week explanations the same way, by a second reader | — |
| what-a-session-is | — | nothing moves it; it is testimony by construction and is marked so |
