# Pre-registration — does a session read `gis4` better than `68`?

*Written 2026-09-05, at Henri's ask, and **run the same day** —
§"The result" is at the foot of this file.  `tools/prereg.sh` is
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

## Two things this cannot fence, said before the run

**1. Tool use is not fenceable, and it does not have to be.**  An arm
could compute the answer instead of reading it — the mode tables are in
`gestate/notes.py` and `outside()` would hand it over.  There is no
`tools` argument on the spawner, so *told not to compute* would be the
same empty fence `card:idiom-or-load.md` was refused for.

What saves the trial is that the exposure is **equal across arms**: a
computing arm scores near 100% whichever spelling it was given, so tool
use does not favour one and it is caught by the ceiling condition below
rather than hidden by it.  The prompt asks for reading and the score
does not trust the asking.

**2. The names arm is not a valid `.notes` file.**  Today's parser wants
`key` to be a whole number, so the fixture's `key gis4` would be
refused.  That is the point — the trial exists to decide whether the
field should accept a name — but it means the arms are reading a
*proposed* format and not a shipped one, and a result cannot be quoted
as being about the format as it stands.

## The spelling, and the fork left open

Letters with `is` for a sharp and `es` for a flat — `gis4`, `es4` — the
convention Henri named (*"c4, cis4"*).  **`b` is B natural and `bes` is
B flat**, which is *not* the German convention he writes in, where `h`
is B natural and `b` is B flat.  Left that way deliberately: `h` is the
one genuinely ambiguous letter, introducing it would confound legibility
with an unfamiliar convention, and which way it goes is his and is not
answered.  Recorded so the choice is visible rather than assumed.

**A note is spelled by its degree in the declared mode**, so an altered
degree keeps its letter and changes only its accidental — `gis4`
becoming `g4`.  That is what an accidental *is*, and it is the whole
tell the names arm is being offered.  A fixture that spelled by nearest
convenience would have tested arbitrary names rather than names.

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


---

# The result — 2026-09-05: void, and the premise was wrong

**Both arms returned the ground truth exactly.**

| arm | files | planted | found | false | recall | precision |
|---|---|---|---|---|---|---|
| numbers | 8 | 99 | 99 | 0 | **100%** | **100%** |
| names | 8 | 99 | 99 | 0 | **100%** | **100%** |

2,304 note lines read across sixteen runs, one tool call each — the
`Read` — so nothing was computed with a script.  Every arm scored 8 of 8
files at 100% recall.

**Void by this sheet's own ceiling condition**, which said: *if both arms
score near 100%, the trial has measured the fixture's difficulty and not
the spelling.*  So `decision:` does not fire.  `spec/drawnscores.md`
decision 2 stands unchanged — **and not because numbers won.**  The
instrument could not speak.

## The premise was wrong, and that is what this cost bought

The hypothesis rested on two things from this tree:

* the mode lamp found a `67` in a section declared D lydian that a
  session had read several times and not seen;
* a session wrote twenty-four bars of `arc.ges` in which every harmonic
  interval was a perfect fifth, and never noticed.

**In both, nobody was asked to check.**  Given the question explicitly —
the mode on the line above, the task stated — a session is exact, 99 out
of 99, in either spelling.  So the failure those anecdotes record was
never legibility.  **It was that the question was never posed.**

That is the same sentence `doc/notes/notes-on-writing-a-piece.md`
already closed with — *"what did move it was measurement, every time and
always too late"* — and it points somewhere other than the format.  A
`.notes` file does not need note names to make a wrong degree findable.
It needs the check to run.

## And the remedy this sheet pre-registered was also wrong

It said: *change the number of planted faults rather than reporting a
tie.*  More faults is more of the same arithmetic at the same accuracy;
it would not move the ceiling.  What the sheet should have foreseen is
that **stating the check is exactly the condition under which spelling
stops mattering** — and the trial the two anecdotes are really about is
the *implicit* one: would a session notice unprompted, while doing
something else.

That is a much harder thing to build, and it is not designed here.  The
obvious shapes all fail the same way: any task that mentions the mode
poses the question, and any task that does not gives an arm no reason to
look at pitch at all.  Recorded as unsolved rather than left as an
exercise.

## What it did establish, which is worth keeping

**A session asked to check a `.notes` file against its declared modes is
exact.**  Sixteen for sixteen, no false positives.  So the value of
`notes.outside()` is not that it can do something a session cannot — it
is that **it runs without being asked**, which is the whole of what a
lamp is for, and an argument for wiring it into something automatic
rather than for changing the format.

## Cost

Sixteen runs, about 800,000 subagent tokens, forty minutes end to end
including the fixture.  The generator is `doc/trial/pitch-spelling.py`
and reproduces the exact files the arms read.
