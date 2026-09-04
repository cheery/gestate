# backlinks — what I am reading is cited by things I cannot see

    status   done — 2026-09-04, opened, reasoned, built, installed by Henri and seen firing in one sitting — §"Done"
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

**When it runs** is the open question (Q1 below), and the answer has
to be *at read time*, because on demand means a command whose existence
the session has to know about, which is the failure the card is about.
At read time can mean a block in the file or a hook on the reader, and
§"Q1, reasoned" is the choice between them.

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

**Q1 — where does the answer appear?**  Readings 1–4 above.  Default
was reading 4.  *Henri, 2026-09-04:* "Defaults are fine, except that
'where the answer appears', can you reason why that choice of
generating it would be the correct approach?"  The reasoning is
§"Q1, reasoned" below, and it moved the default to reading 5.  Still
his to settle; silence leaves reading 5 standing.

**Q2 — what counts as a citer?**  The default is everything the walker
already parses plus the two it does not: `§"…"` passages, `card:` ids,
`[[name]]` memory links, F-numbers, and a tool's filename named in
prose or code.  A plain markdown link is not counted, because the tree
uses those for navigation, not citation.  *Henri, 2026-09-04:*
"Defaults are fine."  Settled.

**Q3 — is the generated block a gate?**  Default: yes, the same as
`tools/memoryindex.py --check` — a body whose block is behind the tree
refuses the commit, because a "cited by" list that is wrong is worse
than none (`doc/memory/the-tree-withers.md`).  Trigger to make it a
report instead: the gate goes red on a commit that did not touch a
citation, twice.  *Henri, 2026-09-04:* "Defaults are fine."
Settled.

**Q4 — does it belong further up the priority?**  It arrives last, as
every new card does.  The argument for higher: it costs about a day
and changes how every card above it is worked.  The argument against:
none of the cards above it wait on it.  *Henri, 2026-09-04:*
"Defaults are fine."  It stays ninth.

## Q1, reasoned — 2026-09-04

Henri asked why generating the answer into the files would be the
correct approach, and the honest answer is that the default was chosen
by precedent and does not survive being reasoned through.

**What the `because` needs is delivery at read time.**  A session that
does not know a thing exists cannot run a command for it or open a
page about it; the only moment the information is useful is when the
session is reading the target, so it has to arrive then, unasked.
That rules out readings 2 and 3 as the primary delivery, and it is the
whole of the argument for a generated foot.

**But the foot reaches the wrong end of the failure.**  Trace the
failure the card names: a session rebuilds an instrument it did not
know about.  It did not know because it never opened the memory that
names it.  A "cited by" foot on that memory helps nobody who is not
already there.  What would have helped is the backlink on the thing the
session *was* reading — `gestate/host.c`, a spec passage, a test —
saying *this is cited by `doc/memory/gestate-audio-teardown.md` and
`card:unseen-flare.md`*.  The discovery runs from source and spec
toward memory and card, and those are exactly the targets reading 4
served with a command only, because a foot cannot go into a `.py`.

**Two ways to deliver at read time, then.**  Put it in the file, or
put it in the reader.

| | generated foot in the file | a hook on the reader's `Read` |
|---|---|---|
| reaches | memory bodies and cards | every file, source and spec included |
| fresh | at the last regeneration; the gate makes it fresh at commit and stale between | always, computed from the working tree |
| churn | 128 of the 556 commits since 2026-08-05 added a memory or card citation, median two targets each — a quarter of all commits would rewrite foot blocks in files the work did not touch | none |
| who sees it | any reader, in any editor, on GitHub, in another harness | a Claude Code session, and nothing else |
| the suite can hold | that the block is in step with the tree | that the hook is installed and the command gives the known answer; not that it fired |
| two writers on one file | the generator and Henri both write memory bodies | the file is untouched |

The churn row is measured, and the command that measured it is in the
journal for the day.  The measurement is an upper bound on the foot's
rewrites and a fair one: every such commit would carry a median of
two generated files it did not otherwise touch, in a tree whose rule is
*commit what you wrote*.

**Reading 5, and it becomes the default: the command, and a `Read`
hook that calls it.**  `tools/backlinks.py <path>` stays the thing in
the tree, validated against a known answer; `.claude/settings.json`
gains a post-read hook that runs it on the file just read and hands the
citers back as context, silent when there are none.  The fence hook
already lives there, so the shape has a precedent in this tree too.
*Killed if* the hook cannot return context to the session — that is
the first thing day one checks — or if it is too slow to run on every
read, which sets the budget: the whole walk under a tenth of a second,
or an index cached against the tree's state.

**What reading 5 gives up, said plainly.**  Henri reading a memory
body in his editor sees nothing, and an arm run in another harness sees
nothing.  Neither is the reader the `because` names.  The trigger that
brings the foot back is either of them turning out to be: he asks for
it, or a trial arm is run outside Claude Code and the citers are
wanted there.  When that happens the foot is reading 1 over the same
command, and its gate is the memory index's.

## Day one

The first sitting builds the command whatever Q1 says, because every
other reading is a view over it: `tools/backlinks.py <target>` prints
every file that cites the target, with the line, for all five citer
kinds.  It validates against a known answer the way `dangling.py` does
— `card:ungated-fixes.md` is cited from a known set of files, and the
command must print exactly those.  Then, before anything else, the
check that decides reading 5: can a post-read hook hand text back into
the session's context at all.  If yes, the hook, with a test that it
is installed and a stopwatch on the walk.  If no, reading 5 is dead and
the foot is the default again.

Then the check that the card is about, which no test can hold: the
next time a session rebuilds an instrument that existed, or misses a
memory it was standing next to, ask whether a backlink was in front of
it at the time.  That is the only measurement of the `because`, and it
runs on the next failure, not on this build.

## Day one, done — 2026-09-04

**The check that decided reading 5 came back yes.**  Claude Code's hook
reference, read the same morning: for a `PostToolUse` hook,
*"`additionalContext` is a string that Claude Code adds to the model as
a system message after the tool response"* — and plain stdout is *not*
shown for that event, which is why the hook prints JSON and nothing
else.  So the hook is alive and the foot stays unbuilt.

**What landed.**

- `tools/backlinks.py` — the command, over the five citer kinds;
  `--hook`, `--check`, `--install`, `--time`.  A cache under
  `$XDG_CACHE_HOME` keyed by each file's size and mtime.
- `test/test_backlinks.py` — one small tree per citer kind with a
  citer known in advance, the hook contract by subprocess, the cache's
  rescan-only-what-moved, a known answer in this tree, and the budget.
- `doc/instruments.md` §"`tools/backlinks.py` — who cites this?" and a
  line in the instruments memory — the file this card says a session
  fails to reach, so it now names the thing that would have shown it.
- `tools/pre-commit.sh` — a lamp that says whether the hook is
  installed and never refuses a commit, because the install is behind
  the leash and a red a session cannot clear gets muted.

**Three defects the known answers found and reading did not**, which
is the argument for validating that way: a card naming its own id was
counted as its own citer; a line naming a card by id *and* by basename
came back as two citations; and a target reached through a symlinked
directory did not resolve.  All three fixed the same hour.

**The budget, measured.**  `python tools/backlinks.py --time`:

| walk | cost |
|---|---|
| cold, cache dropped, 692 files | 2.2 s |
| warm, in process | 20 ms |
| one hook call, wall clock, interpreter included | 76 ms |

The first version walked the tree twice and warmed at 83–179 ms, over
the tenth of a second; one scandir pass that keeps the stat brought it
to 20.  The test holds the warm walk under a quarter second, loose
enough that a loaded machine does not make it lie.

**What is left, and whose.**  The install is Henri's — three lines
under `"hooks"` in `.claude/settings.json`, printed by
`python tools/backlinks.py --install`; the pre-commit lamp says when it
is in.  And the measurement of the `because` runs on the next failure,
not on this build: the next time a session rebuilds an instrument or
misses a memory it was standing next to, ask whether a backlink was in
front of it.

## What the suite can hold

The known-answer validation of the command; that the hook is installed,
the way the fence hook is checked; and the gate on the generated block
if the foot ever comes back under Q3's answer.  It cannot hold the thing the
card exists for — whether a session *looked* — and saying so here is
the same honesty `board/README.md` §"What the suite can hold, and what
it cannot" asks of every card.

## Done — 2026-09-04

Henri installed the hook with the `jq` line the session tested on a
copy, and the next `Read` in the same session — five lines of
`gestate/host.c` — came back with the citers behind it: 58 places, the
first twenty shown, `card:unseen-flare.md` and
`doc/memory/gestate-audio-teardown.md` among them, which are the card
and the memory the `because` said a reader could not see.  The lamp
says *installed*.

**The same afternoon, two more of his asks landed on the tool** and
one card: the rows come ranked — *"Not all citations are equal"* — and
the hook logs every fire so the pre-commit lamp can trip when the cut
at twenty has become the rule.  What it trips to is
`card:backlinks-ranges.md`, shelved on arrival with the fix designed:
answer for the passage being read, not the file.

What stays open is not work: the measurement of the `because` runs on
the next failure — the next time a session rebuilds an instrument or
misses a memory it was standing next to, ask whether a backlink was in
front of it.  And the foot over the same command waits on its trigger,
a reader who is not a Claude Code session.

Journal: `journal.md` §"Backlinks, day one".

## The number that says whether it earns its place — 2026-09-04

**The question this card left open, asked back the next morning.**
*Henri:* **"I think the new 'cited by' reading tool needs a number that
verifies whether it earns its place.  But I don't know what that number
would be."**  The card had said the only measurement of the `because`
runs on the next failure — the next time a session rebuilds an
instrument it did not know about.  That is true and it is not enough:
it waits on a failure nobody can schedule, and until one arrives the
tool is unjudged.

**Three candidates were offered, in a chain, and he took the third.**

1. *Coverage* — does it fire at all.  At the time: 2 fires ever, one of
   them a minute old.  The denominator lives in the transcripts.
2. *Novelty* — of the names shown, how many were new to the sitting.
3. **The attributed follow** — the share of fires whose citer list was
   followed.  *"lets do yes to --earned .. you have earned it."*

**A follow is a fire on a file an earlier fire *in the same sitting*
offered and the reader had not already opened.**  Which is what makes
it cheap: a follow is *another fire*, so the whole measurement is
inside the log and needs no transcript, no second instrument and no
new plumbing beyond two fields.  The log went from four columns to six
— the sitting, and the paths actually put in front of the reader, which
is the rows that survived the cut at twenty and not the whole citer
list.  Four-column lines from the first day still parse, cannot take
part in a follow, and are **counted and named** rather than dropped, so
the rate is never quietly divided by the smaller denominator.

**Four things it must not count**, each one a way to inflate the single
number the tool is judged on, and each one a test:

* across sittings — a name offered yesterday cannot explain a file
  opened today;
* backwards — being told afterwards that `a` cites `b` describes a
  journey already made;
* a re-read — a file opened *before* it was offered was on the reader's
  own path;
* a name that was cut — an offer nobody saw.

**And what it cannot do, said rather than implied.**  A follow is
correlation.  The session may have been going to that file anyway, from
the task or a grep or an earlier sitting, and no number in this log
rules that out.  What the log establishes is order and direction: the
name was offered before it was opened, by the one instrument that shows
a target its citers.

**The floor is zero and no threshold above it was picked** — F169, a
number nobody asked for is a number nobody checks.  Zero follows over
thirty fires means decoration with a context bill, and the lamp says to
take the hook out.  `--check` now names **two causes apart**, because
one lamp with one sentence for two reasons is how an andon gets muted.

At the time of writing: 12 fires, all of them from before the sitting
id, so the number has no data yet and says so.  The warm walk is
unchanged at 23 ms.  And the whole entry in `doc/instruments.md` was
paid for by compressing what was already there — the five capped
documents sat at exactly 2,000 before it and exactly 2,000 after.

## The first measurement, the same evening — 2026-09-04

Henri asked whether the hook had worked.  The log had one line.  The
session that built it read through `cat` and `sed -n` in the shell for
the rest of the evening — this environment tells a session to prefer
the shell for reading — and a `PostToolUse` hook on `Read` does not see
a shell command.  So the hook fired once on a real read, and every
backlink the session could have used went unshown.

The mechanism is fine and the reader reads another way.  Two fixes,
neither built tonight, both cheap: a hook on `Bash` that finds tree
paths in a `cat`/`sed`/`head` command and answers for them, or the
session using `Read` for the tree's own documents.  The second costs
nothing and is a sentence in the rules; the first is a second matcher
over the same command.  He chose the second the same evening —
the sentence is in `doc/instruments.md` beside the tool, `sed` still
allowed — and the fire log is what says whether it worked.

