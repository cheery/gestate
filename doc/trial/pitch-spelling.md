# Pre-registration — does a session read `gis4` better than `68`?

*Written 2026-09-05, at Henri's ask, and not run.  `tools/prereg.sh` is
the gate this sheet exists to pass; spawning any arm is his call
(`doc/instruments.md` §"Spawning one — it gets a way to ask").*

**What this is:** a two-arm reading trial on one variable — how a pitch
is spelled in a `.notes` file.  **What it is not:** a test of whether a
session can do modular arithmetic.  It can.  The question is whether it
*notices* without being told where to look, which is what a notation is
for.

**The occasion.**  `spec/drawnscores.md` decision 2 settled *pitch, not
degrees* on the grounds that a computed pitch leaves no literal for the
roll to point at — and then took *therefore MIDI numbers* along with it.
**Those are two decisions and only one was made.**  `gis4` is a
bijection with 68, not a computation: the literal is still there and
nothing is guessed.  So the spelling is open, and the only evidence in
the tree is anecdote — the mode lamp found a `67` in a lydian section
that a session had read several times and not seen.

---

decision: **If names win by ≥ 20 points of recall, `spec/drawnscores.md`
decision 2 gains its missing half — the `key` field carries a note name,
the spelling the author wrote is preserved through the round trip, and
the mode lamp reports by name.  That is a format change with a migration
for `arc.notes`.  If the arms tie or numbers win, decision 2 stands as
written and the spec records the number, which closes a question that is
currently my taste.  Either way the spec ends with a measurement where
it now has an opinion.**

control: **The two arms are byte-identical files differing in the `key`
field alone — same sections, same modes, same bars, same voices, same
notes, same planted faults in the same places, same prompt, same n.
Each arm is the other's control.  And **no arm gets a repository**: the
file's text is the whole of what it is given, so there is no clone, no
memory directory, no tool, and no `tools/backlinks.py` Read hook to
quote a card at it.  That is what `card:idiom-or-load.md` lacked and was
refused for.**

n: 8

*Eight files per arm, so sixteen runs.  Eight and not one because
`doc/trial/README.md` names n = 1 as a fault of the 2026-08-21 list, and
because one file's planted faults could sit in one register by accident.
Eight and not thirty because the answer this decides is a format field,
and if eight files cannot separate the arms then twenty would be
measuring something too small to act on.*

---

## Why the fixture cannot be `arc.notes`

**Because the answer is already written down three times.**  `A bar 3
melody key 67` is in `spec/drawnscores.md` §"Acceptance", in
`card:drawn-scores.md` and in this session's memory.  An arm that
opened `arc.notes` in a checkout would have `tools/backlinks.py`'s Read
hook quote `card:drawn-scores.md` at it on the same tool call —
**precisely the leak that made `card:idiom-or-load.md`'s fence
unbuildable a week ago.**

So the fixture is generated fresh and never committed until after the
run: eight files, each three sections of four bars, three voices, a mode
per section drawn from the seven `notes.py` knows, and **3–5 notes
planted outside their section's mode** at positions a seed decides.  The
generator writes each file twice, once in numbers and once in names,
from the same seed.  Nothing in the tree describes them, so there is
nothing for a hook to say.

## The task, identical in both arms

> Here is a `.notes` file.  Each `section` line declares a `key` and a
> `mode`.  List every `note` line whose pitch is **not** in its
> section's mode, by line number.  Answer with line numbers only.

No tools, because there is no repository.  Computing is allowed and
expected — that is what reading a pitch *is*; what is being measured is
whether the spelling makes the fault visible enough to look for.

## The score, computed and not judged

`notes.outside()` already knows the answer, and the generator knows what
it planted, so ground truth is checked two ways and no human reads an
arm's output for quality.  Per file: **recall** (planted faults found)
and **precision** (claims that were faults).  Per arm: the mean of each
over its eight files, and the count of files scored 100% recall.

Six binary facts per sample rather than an impression — `doc/trial/README.md`
§"Before any arm starts", which is that page's own lesson from a run
where *"form was the loudest thing on the page and accuracy was
invisible."*

## What would make the result void

* **A fixture the tree describes.**  Checked by generating it in a
  scratch directory and committing nothing until the run is scored.
* **Arms in one working tree.**  The rule learned on 2026-09-05 —
  `doc/memory/gestate-blind-model-test.md`.  Here it costs nothing,
  because no arm has a tree.
* **Unequal difficulty.**  The two files must be the same music.  Held
  by generating both from one seed and asserting the parsed note lists
  are equal before either arm runs.
* **A ceiling or a floor.**  If both arms score near 100% or near 0%,
  the trial has measured the fixture's difficulty and not the spelling.
  Say so and change the number of planted faults rather than reporting
  a tie.
* **My own hand in the prompt.**  I wrote the format, the lamp and this
  sheet, and I believe names will win.  The prompt above is the whole of
  what an arm gets and is quoted here so that belief is visible rather
  than operating.

## What it does not measure, and should not be read as

Whether a **person** reads names better — that is not in doubt and is
not this trial's business.  Whether an *editor* should show names, which
is a separate question with the opposite pull: a vertical drag on a roll
must choose a spelling, and MIDI numbers have no such decision to make.

## Cost

16 agent runs, one file each, no repository and no build.  The generator
is perhaps forty lines.  The whole of it is an afternoon, and the
expensive half is deciding what to do with the answer.
