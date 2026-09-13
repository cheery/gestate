# standing-questions — the question a session is asked at the moment it opens a card

    status   done — 2026-09-13
    because  "You know massive amount of things, but mostly when I request
             them I get them.  their acces seem to be scoped by context a
             lot." — Henri, 2026-09-06, 05:58.  So a session cannot tell
             him what it knows that he did not ask about, the question is
             the retrieval key, and the question-forming is the keeper's
             bottleneck; and nothing in either tree fires a question at a
             session at a moment — `board/README.md`'s seven moves are
             prose.  (The second half is the session's, measured 2026-09-06.)
    asked    Henri, 2026-09-06 — "Do cards for these, and implement standing
             questions immediately, but come up with some good standing
             questions and let me choose among them."
    see      doc/notes/notes-on-cues.md §"Can an introspective index be built?"
             board/standing.md — the questions, and the candidates
             tools/standing.py — the hook that asks them
             test/test_standing.py — the landing, tested
             card:backlinks.md — the hook this is shaped after, and its
             measure of being used

## What this is, what it is not, and when it runs

**A stored cue.**  A question written down once, by Henri, that lands
in front of a session at the moment it opens a card — as context, from
a `PostToolUse` hook on `Read` and `Bash`, the same way the citers of a
file arrive.  The card's shelf is the type the question attaches to,
which is the one type the board has.  Three per card per sitting, at
most, and never twice for the same card in one sitting.

**It is not a checklist.**  Nothing checks that a question was
answered, and nothing can — `board/README.md` §"Question it into
existence" already says no check can tell whether a question was
asked.  What the question buys is that a session goes and looks for
something it would not have known to look for; the answer shows in
the card, or does not.

**It is not the questioning itself.**  The seven moves stay where they
are.  This is the mechanism that makes one or two of them happen on a
clock instead of when somebody remembers.

**And a session proposes, and does not promote.**  `board/standing.md`
§"proposed" is where a candidate waits.  The reason is the cues page's
own: the question-forming is the part that cannot come from the
session, so a session choosing its own standing questions is the
session grading itself.

## The postcondition

A session opening a card is asked, before it has decided anything, the
question the keeper would have asked — and the card shows that it was
answered.

## Found by looking

* **The hook shape exists twice already**: `tools/bars.py` on `Read`,
  `tools/backlinks.py` on `Read|Bash`, both with `--hook`, `--check`,
  `--install`, a log and a lamp.  `tools/standing.py` is the third of
  that kind and borrows the shell parsing outright.
* **The install line is Henri's to add.**  `.claude/settings.json` is
  denied to a session by the leash, so the hook is built and tested
  and does nothing until he pastes `python tools/standing.py --install`'s
  lines in — the same as the two before it.
* **Chosen and installed the same morning.**  Five questions stand —
  three for a live card, one each for shelved and refused — and
  `--check` said *installed* at 07:40 on 2026-09-06, the settings line
  pasted by Henri before the choosing was even reported.
* **The measurement it is judged by is not built.**  `backlinks
  --earned` counts a follow: a fire whose offered file was opened next.
  A standing question has no such artefact — the nearest is whether the
  card's file changed in the same sitting after the fire, which is
  correlation with everything else the session did.  Q2 below.

## Questions

1. **Which questions stand, and under which heading?** — twelve
   candidates under the questions file's `proposed` heading, each with
   what it cost the last time nobody asked it.  **Answered, Henri,
   2026-09-06:** *"Your proposals are good, pick those."* — the
   session's own pick of 1, 3 and 4 for a live card, *event or Henri*
   for a shelved one, and the refusal check for a refused one; the
   other seven wait for the fire.
2. **How is it judged?** — options: (a) the fire log alone, `--report`,
   which says it ran and nothing about whether it helped; (b) a follow
   in the backlinks sense, *the card's own file was edited in the
   sitting after the fire*, from `git log` against the log, which is
   correlation and cheap; (c) ask Henri at the kaizen whether a
   question changed anything, which is testimony.  *Session's
   recommendation, suspected: (b), built after a month of fires, not
   before — a number nobody asked for is a number nobody checks.*
   Default: (a) until the log has thirty fires.
   **Reached unnoticed, and answered, Henri, 2026-09-13.**  The log
   stood at 32 fires over 14 sittings when `tools/flow.py` named this
   card untouched for seven days, and the two triggers disagreed —
   thirty fires, or a month (2026-10-06).  Put to him as close, build
   (b) now, or shelve to the month; his answer: *"(a)"* — close it.
   The judge stays (a), the log; (b) is a card of its own if the
   number is ever wanted.
3. **Does a question fire on `fixme.md`, or on a spec?** — not now: a
   card is the one place a session is about to decide something, and
   the cues page's own constraint is *at what moment* the cue lands.
   Widening is a new because.  *Session's, 2026-09-06.*
4. **Where may a question come from?** — *A guest session, relayed by
   Henri the same morning, on the design as first built:* **"you're
   asking the fast system to generate its own cue.  The standing
   question exists precisely because a session can't know what it
   isn't thinking of.  If the session invents the question, it invents
   it from the same activated context that produced its answer — so it
   will generate a question it can already answer, and then answer it,
   and the whole thing reads like diligence while retrieving nothing
   new."*  Its fix, taken: **keep the idea, change the source** — the
   questions come from Henri or are *harvested* in hindsight at the
   close of a card (*"what question would have helped at the start of
   this?"*), which is not invention but evidence; and answering is
   never mandatory — *"consider it, act if it changes anything, say
   nothing if it doesn't"*.  Built the same morning: the hook line
   carries that clause, and `tools/standing.py --check` at every
   commit that moves a card to `done/` asks the harvest question.
   What it changes about the twelve: they were written by a session
   from the tree's record, not from the card in hand — hindsight of a
   kind — but in one morning, an hour downstream of the idea, so the
   seven not chosen sit under `proposed` for the fire rather than
   being struck or promoted.  *Its meta-note stands as the standing
   caveat on this whole card: fire material, not keyboard material.*

## Done — 2026-09-13

**The mechanism landed on 2026-09-06 and has stood since.**  Five
questions chosen by Henri, the hook installed on his side, 32 fires in
the fourteen days after; `tools/standing.py --check` is the lamp and
`test/test_standing.py` the gate.  The harvest at a card's close works:
four cards closed and four questions came back to `board/standing.md`
§"proposed", dated, each with what it cost.

**What it does not finish:** promotion.  Eleven questions wait under
`proposed` — seven from the first choosing, four harvested — and
choosing among them is his, at the fire, not a card's.  The follow
count, Q2 (b), was not built.  `journal.md` §"The standing questions
closed on their own trigger" is the story.
