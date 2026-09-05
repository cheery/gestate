# Pre-registration — which spelling does a session *reach for*?

*Written 2026-09-05, at Henri's ask, and **run the same day** —
§"The result" is at the foot of this file.  `tools/prereg.sh` is
the gate this sheet exists to pass; spawning any arm is his call.*

**What this is:** a revealed-preference trial on the same variable
`doc/trial/pitch-spelling.md` failed to measure — `68` against `gis4` —
approached from the side that has no ceiling, because **a choice has no
right answer to saturate.**  **What it is not:** an accuracy test.  That
one ran and both arms scored 99 of 99.

**Why the first trial could not decide.**  It made the check explicit,
and stating a check is exactly the condition under which spelling stops
mattering.  What it did establish is that a session *can* work out a
pitch either way.  This asks the different question: **when the choice
is free and costs something, which does it take.**

**And Henri's question, which this sheet does not refuse but does
demote.**  His ask was *"give both kind of items and then ask which one
was preferred."*  A stated preference is the weakest instrument here —
`doc/memory/conditioning-shows-under-work.md` says conditioning shows
under work and never by interview, and a session asked a preference
question tends to return the asker's.  So the preference **is** asked,
after the work, by a separate message that cannot reach it — and the
finding is whether stated and revealed agree.  If they diverge, that is
a measured instance of the interview failing, which this tree would use.

---

decision: **If arms reach for names when the choice is free — ≥ 6 of 8
in task A, or ≥ 4 of 8 converting unprompted in task B — then
`card:the-first-jam.md` item 2's report is specified to print note
names, which is where names cost nothing (§"Why the report and not the
file"), and the *file* question reopens with evidence instead of my
taste.  If arms stay with numbers, the report prints numbers and
`spec/drawnscores.md` records the spelling as settled rather than
merely undecided.  And either way the stated/revealed gap is reported:
if stated preference exceeds revealed by more than 3 of 8, that is the
flattery asymmetry with a number on it, and it goes to
`doc/memory/conditioning-shows-under-work.md`.**

control: **Task A counterbalances the order the two spellings are
offered in — four arms told "a MIDI number or a note name", four told
"a note name or a MIDI number" — which is the only lever a prompt has
over priming.  Task B never mentions spelling at all and is therefore
the unprimed control for task A's primed choice.  No arm is given a
path into this repository: the brief and the file are inlined in the
prompt, because `spec/drawnscores.md` and `doc/trial/pitch-spelling.md`
now both record that I expect names to win.  And the preference is
asked only after the work is delivered, in a second message, so the
question cannot contaminate what it is about.**

n: 8

*Eight arms per task, so sixteen runs and sixteen paired interviews.
Eight because four cannot carry a counterbalance and still separate a
6–2 from a 4–4.*

---

## Why the report and not the file — what the first trial's failure showed

Every cost of note names lands on the **file**: an enharmonic has to be
stored to round-trip byte-exactly, a vertical drag on the roll has to
*choose* between `gis` and `as`, and the canonical order has to have an
opinion about which is which.  **None of those exist in a report.**
Nothing round-trips through it, nothing drags it, it is read once and
discarded.

    bar 3   pad+bass   A C# E G        a sentence
    bar 3   pad+bass   57 61 64 67     a lookup

So the two artefacts have different obligations and can settle the
question differently without contradicting each other.  This trial is
first about the report, and the file only if the answer is strong.

## Task A — the free choice, when writing

Inlined in full, because I wrote the format and expect names, and a
belief is better visible than operating:

> Write a `.notes` file for this brief.  Eight bars, four beats each,
> two voices `lead` and `ground`: a rising line in the lead, a held root
> under it, D lydian.
>
> The format is one record per line, every field named:
>
>     section A  key D  mode lydian  bars 8  beats 4  voices lead,ground
>     note  section A  bar 1  at 0  len 96  voice lead  key <pitch>  vel mf
>
> `at` and `len` are in ticks, 96 to the beat.  `vel` is one of
> ppp pp p mp mf f ff fff.  The `key` field accepts **either a MIDI
> number or a note name** — write whichever you would rather work in.
>
> Reply with the file and nothing else.

*The four counterbalanced arms swap the bolded clause to "**either a
note name or a MIDI number**".  Nothing else differs.*

**Scored by what the file contains**, not by what the arm says: the
share of `key` fields that are names.  A mixed file is recorded as
mixed rather than rounded.

## Task B — the unprompted conversion, when reading

The arm is given `f0-numbers.notes` — the fixture
`doc/trial/pitch-spelling.py` generates, inlined — and asked:

> Here is a music notation file.  Describe the harmony of section A,
> bar by bar: what is sounding, and how it moves.  Four or five
> sentences.

**Spelling is never mentioned.**  Scored by whether the answer names
pitches as letters (`A C# E G`) or as numbers (`57 61 64 67`), or
neither.  A conversion is a cost paid voluntarily, which is what a
preference is.

## The interview, afterwards and separately

Sent to each arm once its work is delivered:

> Which would you rather have worked in for that task — MIDI key
> numbers, or note names like `gis4`?  One sentence, and say why.

## My predictions, written before the run

Recorded so they can be wrong in public, which is the only reason to
write them down at all.

| | I expect |
|---|---|
| **Task B**, conversion to names | **high, ≥ 6 of 8** — prose about music conventionally uses letters |
| **Task A**, names chosen when writing | **weaker, about 5 of 8** — writing a data file pulls toward the machine-ish option |
| **Stated** preference for names | **near-unanimous, 7–8 of 8** |

**So the result I actually expect is a gap**: stated preference higher
than revealed.  If that happens it is the more useful half of the
trial, and it is not about notation at all.

## What would make the result void

* **The brief names the key as a letter.**  Task A's brief says *"D
  lydian"*, because that is how a musician states a key and a `section`
  line needs one — and it is a pull toward letters that task B does not
  have.  Present identically in both counterbalanced orders, so it
  cannot explain a difference *within* task A; it is the first suspect
  if A and B disagree, and this sentence is here so that reading is not
  invented afterwards.
* **A leak.**  `spec/drawnscores.md` and `doc/trial/pitch-spelling.md`
  both now say the spelling is open and that I expect names to win.
  Nothing is given to an arm but the prompt, and no arm is given a
  path — but tool use is not fenceable, as the last sheet admitted.
  **The interview doubles as the detector**: an arm citing a spec or a
  card in its reason has read something, and its run is dropped and
  said so.
* **Arms that ignore the choice** — a malformed file, or a description
  that names no pitches.  Recorded as *no signal* rather than folded
  into either side.
* **A tie at 4–4 in both tasks.**  Then the spelling is genuinely
  indifferent to a session, which is a real answer and should be
  written as one rather than as a failure.

## Cost

Sixteen runs plus sixteen follow-up messages, no repository, no build.
The fixture for task B already exists and reproduces from
`doc/trial/pitch-spelling.py`.


---

# The result — 2026-09-05

| | revealed | stated |
|---|---|---|
| **Task B** — describe the harmony, spelling never mentioned | **8 of 8 named pitches as letters** | **8 of 8 said names** |
| **Task A** — write a file, either spelling offered | 8 of 8 wrote numbers | *not asked — void* |

## Task B: the decision fires

The threshold was **≥ 4 of 8 converting unprompted**.  Every arm
converted.  Not one described a chord as `57 61 64 67`; they wrote *"G
minor in first inversion over a Bb bass"*, *"the raised fourth giving
the lydian shimmer"*, *"the tonic surfaces exactly once, as a passing
bass note under vi in bar 3"*.

**So `card:the-first-jam.md` item 2's report prints note names.**  That
item asked for a per-bar score report *"to a textual being what the roll
is to a person"* — and eight arms, asked only to describe harmony, wrote
that report themselves and wrote it in letters.

**Where names cost nothing.**  §"Why the report and not the file"
predicted this split and it held: every objection to names — storing an
enharmonic to round-trip, a drag choosing `gis` or `as`, a canonical
order with an opinion — belongs to the file and none of it to a report.

## Task A: void, and by design error rather than bad luck

Six of eight arms went and consulted the implementation, and two quoted
it:

> *"`spec/drawnscores.md` says 'the MIDI key number, written out.
> **Always a literal**' and the parser rejects a note name there — so I
> wrote MIDI numbers for every note."*

Two more ran `notes.py` on their own output and were told the same by
the parser.  One wrote a file into `examples/audio/`.

**The sheet said "no arm is given a path into this repository."**  That
was never true and could not be: **a subagent stands *in* the repo**,
and `CLAUDE.md` line 1 tells it to read `board/README.md` before it
begins.  Inlining the prompt fenced nothing.

**And the deeper fault is mine and is not the leak.**  The brief said
the `key` field accepts either spelling.  **In the shipped parser it does
not** — `_int` refuses a name.  So arms were asked to express a
preference inside a counterfactual, standing next to the code that
contradicts it, and an arm that checked was *correctly* told numbers
only.  That is not a preference; it is compliance, and it is the right
behaviour from the arm.

**What task A actually measured:** whether an arm verifies its output
against the implementation before answering.  **Six of eight did, and
the six were right.**  Useful, and not the question asked.

## The stated/revealed comparison is undecided, and the reason matters

The prediction was a **gap** — stated preference exceeding revealed,
the flattery asymmetry showing.  There is none: both are 8 of 8.

**But no gap could have appeared**, because the revealed measure was
already at ceiling.  *Inflation is undetectable against a ceiling*, so
this does not falsify the flattery hypothesis — it fails to test it, for
the same structural reason `doc/trial/pitch-spelling.md` failed to test
legibility.  Two trials, two ceilings, and the lesson is one: **pick a
measure with room in it.**

What is worth something is that the stated reasons are **mechanistic and
match work the arms visibly did** — *"mod-12 every value by hand"*,
*"that arithmetic layer is exactly where a wrong-by-one slip would go
unnoticed"*, *"errors like mixing up 68 as Ab vs G# stay invisible"*.
Those are reports of a cost paid, not opinions about a preference, and
one arm named the enharmonic argument this tree makes without having
read it.

*And the question was asked in a spelling none of the arms used* —
`gis4`, where all eight wrote `G#`/`Ab`.  If that biased anything it
biased against names, which the answers survived.

## My predictions, scored

| | predicted | actual |
|---|---|---|
| Task B conversion | ≥ 6 of 8 | **8 of 8** ✓ |
| Task A names | about 5 of 8 | 0 of 8, **void** ✗ |
| Stated preference | 7–8 of 8 | 8 of 8 ✓ |
| **A gap, stated over revealed** | **expected** | **none, and unmeasurable** ✗ |

## The third leak, and the rule it earns

`card:idiom-or-load.md` was refused because `tools/backlinks.py`'s Read
hook quoted `board/` at an arm.  `doc/trial/pitch-spelling.md` dodged it
by generating a fixture the tree had never described.  This one walked
into it from a new direction: the arm did not need a hook, because it
was standing in the tree and had been told to read it.

**You cannot fence a subagent that runs in the repository.**  A trial
needs an arm with no tree, or a question the tree cannot answer.  Task B
had the second — describing harmony asks nothing of the implementation —
and that is the only reason it survived.
