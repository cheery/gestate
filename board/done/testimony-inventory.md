# testimony-inventory — which claims rest on a session's word, and which on a harness

    status   done — 2026-09-06
    because  "Which claims rest on session testimony versus harness output?
             Still an afternoon's inventory, still unrun, and it sharpens
             every outside conversation." — the session's, in
             doc/notes/notes-on-cues.md, 2026-09-06, answering Henri's
             "what else should I be asking here?"; the problem under it is
             `doc/memory/the-evaluation-loop.md`: a session's report about
             the method is the tree's own voice, and nobody has counted how
             much of what the tree carries is that kind of claim
    asked    Henri, 2026-09-06 — "yes.  Do cards for these" and, mid-turn,
             "and do the measurement as well."
    see      doc/notes/notes-on-cues.md §"Can an introspective index be built?"
             doc/memory/the-evaluation-loop.md — the rule this counts against
             doc/memory/research-that-leaves-a-command.md — why the count
             needs a command under it
             doc/testimony.md — the inventory
             tools/testimony.py — the command under it

## What this is, what it is not, and when it runs

**An inventory of the memories** — `doc/memory/`, 80 files on the day
this was written — asking of each: what does its load-bearing claim
rest on?  Four kinds, and a memory gets one:

| kind | the claim rests on | example |
|---|---|---|
| `harness` | a number, a test, a transcript, a command a reader can re-run | 1.3 s in a `cpu=` column; 780 green with the fix gated |
| `henri` | his decision or his words, quoted, dated — a rule by fiat, which needs no evidence beyond that he said it | *never `git add -A`* |
| `session` | a session's report of what it saw, judged or felt, with no command under it | *the dialogue conditions, the document does not* — before trial three |
| `argument` | reasoning from outside the tree — a book, a tradition, a mechanism named — with no measurement here | the two-systems mapping; the preference-signal asymmetry |

**Why the memories and not the whole tree.**  They are the distilled
layer — the claims sessions carry into every sitting before they know
what they are working on — so they are where a testimony-shaped claim
does the most conditioning.  The notes are conversation and say so;
the journal is past tense and mostly harness; the specs are contracts.
Widening is a second pass with its own because.

**It is not a verdict on any memory.**  A `session` memory is not a
wrong one — most of the method's rules began as one, and became
`henri` when he adopted them or `harness` when something measured
them.  The count says how much of the corpus is still waiting for
that, and which files.

**It runs once, by hand, with a command under it.**  The
classification is a judgment and is made by a session — which is the
loop the count is about, and is said on the page.  What the command
does is hold the table to the tree: every row names a memory that
exists, every memory has a row or is counted as unclassified, and the
numbers on the page are the numbers the table gives.

## The postcondition

A reader can say, for any memory a session leans on, whether the thing
it leans on is something they could re-run, something Henri decided,
or something a session said — and can say how much of the corpus is
each.

## Found by looking

* Neither tree holds the inventory or a start on it (grep, 2026-09-06,
  both trees).
* The memory index carries a `type` per file — `project`, `feedback`,
  `reference` — which is what the memory is *for*, not what it rests
  on; the two are independent, and a `feedback` memory can be any of
  the four kinds above.
* `doc/notes/README.md` already does this for the notes, by kind of
  transcript — which is provenance of the *words*, not of the claim.
  The inventory is the same move one layer up.

## Questions

1. **Gate, or report?** — should a new memory be refused by the suite
   until it has a row?  *Session's recommendation, suspected: report
   only.*  A gate would make every memory cost a classification line
   from a session about its own claim, which is the loop again as a
   ratchet; a report at every commit that says *N unclassified* is
   enough for the keeper's evening.  Default: report.
   **Built 2026-09-13, a week late, on Henri's "build both".**  The
   report had never been wired to a commit, so four memories waited
   three days unclassified behind a count only the full suite read.
   Now `tools/pre-commit.sh` prints *N of M classified* and the names,
   refusing nothing; and the page quotes the table's count alone, which
   a gate holds — so the gate can never refuse a memory for lacking a
   row, and the default stands.
2. **What of the `session` rows should move?** — each one is a
   candidate for a measurement that would turn it into `harness`, or a
   sentence from Henri that would turn it into `henri`; the list is the
   afternoon's real product and it is his to read.

## Done

`doc/testimony.md`, 2026-09-06: eighty rows, one per memory — 22
`harness`, 38 `henri`, 14 `session`, 6 `argument` — and a second table
of the fourteen with the measurement or the sentence that would move
each.  `tools/testimony.py` holds the table to the directory and the
count on the page to the table; `test/test_testimony.py` is the gate,
and it is a report and not a refusal on an unclassified memory, per Q1's
default.  Q2 is his to read, on the page.  `journal.md` §"Standing
questions, and what the memories rest on — 2026-09-06" is the story.
