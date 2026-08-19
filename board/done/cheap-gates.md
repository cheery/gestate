# cheap-gates — the seventeen-second checks only ran when somebody had twenty-five minutes

    status   done — 2026-08-19
    because  "no full suite run happened until just now" — a whole day
             of work went unverified because the only way to run the
             gates is to start a 25-minute pass, and when the pass
             finally ran it died at a gate in seventeen seconds on a
             breakage that had been in the tree for hours
    asked    Claude, 2026-08-18, at Henri's ask — "Write cards for
             fixing these issues in your workflow.  Describe them in
             good detail so that next time you can fix them."
    see      tools/suite.py:65 — `GATES`, and the comment saying they take seconds
             board/README.md §"The suite is a serial gate, and a session can invalidate its own run"
             test/report.md — the run that proved it (not committed)
             fixme.md F160 — the atlas lanes that were missing all day

## The ask

From the day's kaizen, in my own words:

> The full suite hadn't run all day, against a tree where I'd touched
> `host.c`, `session.py`, `workbench.py`, `view.rs`, `furniture.rs` and
> `audioeditor.py`.  The board's rule is one full run per shift and I
> let it slide while iterating.

And Henri's answer when it finally ran and failed at the gate, with
half an hour left in his day:

> the suite cannot run yet.  I need to go in 30 minutes and there's no
> buffer left if I wait for suite.  I will run it before I start next
> session.

Which is the cost landing on the wrong person: the gate broke inside a
session's own work and was handed to the author as a chore.

## Found by looking, before it was taken

**The gates already know they are cheap.**  `tools/suite.py:65` lists
seven of them with a comment saying so — the board contract, the
citations, the atlas, `doc/ref/`, the complaints page, and the two
example rosters.  The whole set ran in **17 seconds** on 2026-08-18 and
caught a real breakage.  Its own comment records that one of them
*"cost a whole re-run"* when it was not run first, which is why they
were hoisted to the front of the suite in the first place.

**But the front of the suite is still the suite.**  `tools/suite.py`
has `--unfenced` and passes extra arguments to pytest; it has no mode
that runs the gates *and stops*.  A session that wants the seventeen
seconds has to either start a twenty-five-minute pass it must then
protect from its own edits, or hand-copy the seven paths out of the
source into a `pytest` command — which I did, some days, from memory,
and which drifts the moment the list grows.

**What the missing mode would have caught, today.**  Five modules
landed (`complaints.py`, `desk.py`, `gemba.py`, `history.py`,
`pops.py`).  `test_atlas.py::test_every_module_has_a_lane` fails the
moment the first one is committed.  Run at that commit it costs
seconds and names the file; run at the end of the day it is a red
gate blocking the only verification pass of the shift, on a tree with
six subsystems' worth of changes in it, handed to Henri.

The gates are also *exactly* the checks a working session breaks — they
are about the documents the work edits, not about the code's behaviour.
That is what makes them worth running on a cadence measured in commits
rather than shifts.

### The shape the fix should take

* **`python tools/suite.py --gates`**: run the seven, print the same
  header block, stop.  No fence dance if it does not need one, no
  report file to conflict with a real run's — or a clearly-marked one
  (`test/report.md` says at the top what it was).  Seconds.
* **Run it where a commit is made.**  One card, one commit is this
  board's unit of work, and the gates are the checks that a card's
  edits break.  Whether that is a `pre-commit` hook, a line in
  `board/README.md` §"Finishing one", or both, is the question below.
* **Do not touch the shift rule.**  One full run per shift, tree
  frozen, stays — the gates are not a substitute for it and this card
  should not read as one.  What changes is that the full run stops
  being the *first* time anything is checked.

**And a smaller thing worth folding in**: `tools/suite.py` prints
*"a gate failed, so the long pass never started; fix it and run
again"*, which is right, but the report's `Ran outside the fence` row
then reads `none — stopped at the gates` and the totals read
`2 failed, 109 passed` — a number that looks like a suite result and
is not.  Somebody reading `test/report.md` cold could take that as the
tree being in good shape.  The report should say, in the totals, that
this was a gate run and nothing else happened.

## The postcondition

*A first draft, for Henri to correct:*

**A breakage that takes seconds to detect is never discovered by the
author of the project on the following morning.**

## Questions — answered 2026-08-19

**A git hook, or a rule in the board?**  *Both, and the hook first.*
Henri, opening the session: *"lets start and implement the cheap-gates.
It could be a git hook."*  The card's leaning was the other way — build
`--gates`, put it in §"Finishing one", and wait for evidence that the
hook was needed — and it was wrong for a reason it had not seen.  It had
counted the twelve seconds as the hook's cost.  Henri, once it was
running:

> as a git hook it also gives some time to think before committing.  I
> think it's a quality assurance.

Which is the same twelve seconds read as the benefit.  A commit is the
*end of a card* on this board and there was nothing at all between
deciding to make one and having made it.

The objection the card raised — that it fires on his commits too — is
answered by `tools/pre-commit.sh --uninstall`, named in the failure
message itself, rather than by making the hook clever about who is
committing.  It cannot know.

**Should `--gates` write `test/report.md` at all?**  *No: a separate
`test/gates.md`.*  The card offered three options and the separate file
is the one that survives the board's own two-writers rule — a gate run
happens per commit and a full run per shift, so sharing one filename
means the shift's evidence is destroyed by the next commit and the
reader cannot tell which run wrote the page.  Both the labelled-totals
option and the separate file were taken, in the end: `test/gates.md`
says *this is not a suite run* in its title, its first paragraph and its
totals line.  Three times, because the risk of a cheap check is that a
green page reads like an expensive one.

## The questions as they stood

**A git hook, or a rule in the board?**  A hook is a real control and
holds for a session that forgets; it also fires on Henri's own commits,
where a red gate would block work he did not cause, and this project
has been careful about not moving burden onto him.  A `--no-verify`
escape exists but is exactly the kind of thing that gets typed
reflexively.  Leaning: build `--gates` first, put it in
§"Finishing one", and let a few days of evidence say whether the hook
is needed.  Worth one line of Henri's opinion, since a hook would land
in his working directory too.

**Should `--gates` write `test/report.md` at all?**  A gate run and a
full run competing for one file is a small version of this board's own
two-writers rule.  Options: a separate `test/gates.md`, a clearly
labelled totals line, or nothing on disk at all.

## Done — 2026-08-19

**`python tools/suite.py --gates`.**  The eight gates, fenced, then
stop: **12 seconds** measured, against the 25-minute pass they were
trapped behind.  It shares every line above the stop with a full run —
the same fence proof, the same `GATES` dict, the same streaming — so the
list of gates has exactly one home and cannot drift from the
hand-copied one this card records a session running from memory.

**`test/gates.md`, and never `test/report.md`.**  Gitignored, like the
report, plus one reason of its own: a per-commit page would put a
machine-local diff into every commit.

**The totals fix the card asked for, in both places.**  A full run that
stops at the gates now reads `2 failed, 109 passed — the gates alone;
the suite never started`, and the gate page says the same on its own
face.

**`tools/pre-commit.sh`** — `--install`, `--check`, `--uninstall`, and
bare to run the gates now.  It writes a shim into `.git/hooks/`
(untracked, so once per checkout) rather than a symlink, so it survives
the tree being moved and works from a worktree; it refuses to overwrite
a `pre-commit` it did not write. **Installed in this checkout on
2026-08-19.**  Proved by breaking a citation deliberately and watching
the commit be refused with the gate named.

**Six tests in `test/test_suite_runner.py`** — the labelling of the
page, that a gate run does not touch the suite's report, that a red gate
reaches both the page and the exit code, that the eight paths have one
home, and an install/uninstall round trip in a throwaway repository plus
the refusal to clobber somebody else's hook.

**Written into `doc/instruments.md`** beside the suite, and into
`board/README.md` — §"Finishing one" gains the gates as step 4, and the
serial-gate section gains the third cadence: *targeted runs per card,
the gates per commit, one full pass per shift with the tree frozen.*

**What this does not change.**  Nothing in the gate set tests behaviour.
The full run is still the only thing that says gestate works, and it is
still one per shift against a frozen tree.
