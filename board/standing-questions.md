# standing-questions — the question a session is asked at the moment it opens a card

    status   doing
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
* **Nothing fires until a question is chosen.**  The candidates are
  under `## proposed`, and `--check` says *installed; no question
  chosen yet, so it fires on nothing* until one moves up.
* **The measurement it is judged by is not built.**  `backlinks
  --earned` counts a follow: a fire whose offered file was opened next.
  A standing question has no such artefact — the nearest is whether the
  card's file changed in the same sitting after the fire, which is
  correlation with everything else the session did.  Q2 below.

## Questions

1. **Which questions stand, and under which heading?** — twelve
   candidates in `board/standing.md` §"proposed", each with what it
   cost the last time nobody asked it.  *Henri's; open, 2026-09-06.*
   Default if undecided: none fires, and the hook stays silent.
2. **How is it judged?** — options: (a) the fire log alone, `--report`,
   which says it ran and nothing about whether it helped; (b) a follow
   in the backlinks sense, *the card's own file was edited in the
   sitting after the fire*, from `git log` against the log, which is
   correlation and cheap; (c) ask Henri at the kaizen whether a
   question changed anything, which is testimony.  *Session's
   recommendation, suspected: (b), built after a month of fires, not
   before — a number nobody asked for is a number nobody checks.*
   Default: (a) until the log has thirty fires.
3. **Does a question fire on `fixme.md`, or on a spec?** — not now: a
   card is the one place a session is about to decide something, and
   the cues page's own constraint is *at what moment* the cue lands.
   Widening is a new because.  *Session's, 2026-09-06.*
