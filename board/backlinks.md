# backlinks — what I am reading is cited by things I cannot see

    status   open
    because  "When I open a memory file, an instrument, or a spec
             section, nothing tells me who cites it.  The tree's own
             record says this is where sessions actually fail.  A
             session that does not know an instrument exists rebuilds
             it, and 19 of 53 memory hooks were once missing from the
             index.  Those are retrieval failures, and they are the
             kind a 'cited by' index fixes cheaply, since the citation
             walker already parses every reference."
             — Claude, 2026-09-04, in the reply Henri opened the card
             from
    asked    Henri, 2026-09-04 — "Lets open the card for backlink tool,
             I think it's something you could actually use, and there's
             a because for it already, in your words."
    see      test/test_citations.py — the walker that already parses
             every citation, in one direction
             tools/memoryindex.py — the precedent: a generated block, a
             gate that refuses the page when it is behind its source
             tools/dangling.py — the *other* direction, a name cited and
             never defined; not this
             doc/instruments.md §"The standing rule: build the missing one, now"
             doc/memory/gestate-instruments.md — the rule as a memory
             doc/memory/the-tree-withers.md — a living document has a
             source and a check
             doc/memory/gestate-board-goal.md — stop proposing cards;
             this one is the session's own broken workflow, which the
             board README names as the kind a session should write

## The ask

Henri, 2026-09-04, after a conversation about Project Xanadu:

> Lets open the card for backlink tool, I think it's something you could
> actually use, and there's a because for it already, in your words.

## What this is, what it is not, and when it runs

**A backlink is the answer to "who cites this?"**  Every citation in the
tree runs one way: the citing file knows its target, the target knows
nothing.  A session reads a target — a memory body, a card, a spec
passage, a defect entry — and cannot see the three places that lean on
it, the card that was written because of it, or the test that names it.

It is **not** `tools/dangling.py`, which asks the opposite question: a
name the tree leans on that nothing defines.  It is not a search
engine, not retrieval over embeddings, and not a change to how anything
is cited — the notations stay exactly as they are, because the claim is
that they already carry the whole graph and only the reading direction
is missing.

**When it runs** is the open question (Q1 below).  Either at read time,
as a block a session sees because it is in the file it opened, or on
demand, as a command whose existence the session has to know about —
and the second is the failure the card is about.

## Found by looking, 2026-09-04

**The graph is already there, and it is large.**  Counted by a
throwaway script over the same file set `test_citations.py` walks,
with its own two regexes plus `[[name]]` memory links and F-numbers:

| what is cited | how | distinct targets | edges |
|---|---|---|---|
| a passage | `file.md §"heading"` | 108 | 258 |
| a card | a `card:` id | 39 (all of them) | — |
| a memory | `[[name]]` | 81 | — |
| a defect | `F123` | 200 | — |

Every one of those edges is read from the citing side only.

**Who is cited by nobody**, the session's measurement, and **labelled a
proxy**: it counts targets with zero inbound links, which is not the
failure the `because` names.  The failure happens at read time, when a
target *has* citers and the reader cannot see them, and that cannot be
counted after the fact.

| kind | total | cited by nobody outside the index and itself |
|---|---|---|
| memory bodies in `doc/memory/` | 72 | 13 |
| cards, all three shelves | 39 | 3 |
| tools in `tools/` | 40 | 0 |

The thirteen memories are not a defect in themselves — a memory that is
only hooked from the index is doing its job.  What the number says is
that the index is the *only* way in for a fifth of them, and the index
was found with 19 of 53 hooks missing on 2026-08-24, which is what
`tools/memoryindex.py` was built to end.

**Every precedent this needs is in the tree.**

- `test/test_citations.py` already finds every `§"…"` and `card:`
  citation and resolves its target.  The inverse index is the same
  walk with the pairs turned around.
- `tools/memoryindex.py` is the shape for a generated block: two
  markers, a source, a `--check` that exits 1, and a gate.  The atlas
  and `doc/method.md`'s table are the same move.
- `doc/instruments.md` §"The standing rule: build the missing one, now"
  says a missing capability is built when the need arises.  The need
  arose in a conversation, not while working, so this is a card and
  not a build — and it is the kind of card the board README says a
  session should write: its own broken workflow.

**Where the idea came from**, for the record and not as authority.
Ted Nelson's Xanadu wanted bidirectional links from 1965 on and never
shipped them; two pages Henri found on 2026-09-04 — gwern.net/xanadu
and zed.dev/blog/agentic-xanadu — read that failure two ways, and the
one piece both agree survived is the backlink.  This tree already runs
the rest of Xanadu's data model by hand: permanent ids (`card:`,
F-numbers, `§"…"`), never-overwrite (git and the append-only journal),
provenance in prose (dated answers in the asker's words).  The backlink
is the piece it does not have.

## Readings, each with what would kill it

1. **A generated "cited by" block in every memory body and card.**
   Seen at the moment of reading, by any reader, with no command to
   know about.  *Killed if* the churn is unbearable: every new citation
   anywhere rewrites the target's block, so a commit touching one card
   touches three files, and `git log` on a memory body fills with
   index noise.  Mitigable by putting the block at the foot and keeping
   its format stable, but not removable.
2. **One generated page, `doc/backlinks.md` or similar**, the inverse
   index for the whole tree, gated like the atlas.  No churn in the
   bodies.  *Killed if* nobody opens it — it has the same
   discoverability problem as a command, one hop better because it is
   a file `ls` shows.
3. **A command, `tools/backlinks.py <target>`**, on demand.  Cheapest
   to build, no generated content, no gate.  *Killed by the card's own
   `because`*: a session has to know the instrument exists to run it,
   and the instruments memory is what carries that knowledge, which
   makes the fix depend on the thing it fixes.
4. **The block in memory bodies only, and the command for the rest.**
   Memory bodies are the case with evidence (13 reachable only through
   the index; the 19-of-53 finding); spec passages and F-numbers are
   cited from code and tests, where a foot block cannot go.  *Killed
   if* the churn from reading 1 turns out to bite even at 72 files.

The session's default is **reading 4**, with the trigger that decides
it: if, after a fortnight, `git log --stat doc/memory/` shows the
generated foot rewritten in more than a third of the commits that
touch that directory, the block moves out to reading 2.

## Questions

Each carries a default and the trigger that would change it, so a
one-line answer settles it and silence leaves the default standing.

**Q1 — where does the answer appear?**  Readings 1–4 above.  Default:
reading 4.  *Henri:* —

**Q2 — what counts as a citer?**  The default is everything the walker
already parses plus the two it does not: `§"…"` passages, `card:` ids,
`[[name]]` memory links, F-numbers, and a tool's filename named in
prose or code.  A plain markdown link is not counted, because the tree
uses those for navigation, not citation.  *Henri:* —

**Q3 — is the generated block a gate?**  Default: yes, the same as
`tools/memoryindex.py --check` — a body whose block is behind the tree
refuses the commit, because a "cited by" list that is wrong is worse
than none (`doc/memory/the-tree-withers.md`).  Trigger to make it a
report instead: the gate goes red on a commit that did not touch a
citation, twice.  *Henri:* —

**Q4 — does it belong further up the priority?**  It arrives last, as
every new card does.  The argument for higher: it costs about a day
and changes how every card above it is worked.  The argument against:
none of the cards above it wait on it.  *Henri:* —

## Day one

The first sitting builds the command (reading 3) whatever Q1 says,
because every other reading is a view over it: `tools/backlinks.py
<target>` prints every file that cites the target, with the line, for
all five citer kinds.  It validates against a known answer the way
`dangling.py` does — `card:ungated-fixes.md` is cited from a known set
of files, and the command must print exactly those.  Then the block,
if Q1 keeps the default, and its gate.

Then the check that the card is about, which no test can hold: the
next time a session rebuilds an instrument that existed, or misses a
memory it was standing next to, ask whether a backlink was in front of
it at the time.  That is the only measurement of the `because`, and it
runs on the next failure, not on this build.

## What the suite can hold

The gate on the generated block, if Q3 keeps the default, and the
known-answer validation of the command.  It cannot hold the thing the
card exists for — whether a session *looked* — and saying so here is
the same honesty `board/README.md` §"What the suite can hold, and what
it cannot" asks of every card.
