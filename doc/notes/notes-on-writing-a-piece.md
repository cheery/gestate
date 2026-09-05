# notes-on-writing-a-piece.md — 2026-09-04, open

*A piece written together to find out what a notation format has to
carry.  The piece is the instrument; **this log is the deliverable.**
`card:drawn-scores.md` §"The direction: a sub-language, included" is
what it feeds.*

---

## Why a log and not a retrospective

Three slices of `spec/annotations.md` were built on the score box's
gesture before anybody counted what it reaches, and the count came back
**0–5% on real pieces, 100% on the three files written for the box**.
The reason those three score full marks is the reason this file exists:
`marked.ges` has no markable note because `line m` was the *elegant*
way to write it, and elegant erased the evidence.

**A workaround destroys the datum.**  So a friction is written down
**at the moment it is met and before it is worked around**, not
recalled at the end.  Recalled friction is smoothed friction.

## Two logs, because they are different needs

| | who meets it | what it is evidence for |
|---|---|---|
| **§ Writing** | the session, putting notes in the file | what a **phrase format** must carry |
| **§ Hearing** | Henri, judging it by ear | what an **editor view** must show and let him change |

Conflating them is how a format comes to serve the wrong person, and
the wrong person is the one who finds arithmetic easy.

## The brief — Henri, 2026-09-04, verbatim

> I think I'd like to make a standard blues/jazz harmony: 1,4,5,
> ABA-form, starting at lydian in A, transforming to locrian in B, back
> to phrygian.  deceptive cadence in middle, perfect cadence in end.
> Key: D, moving to G, then back to D.  I'm not sure what it would
> sound like, but forming that would be interesting.. and maybe alone
> explains how I'd work on it.. that's the order where I thought about
> it.

**And a second one is wanted:** *"But maybe we need an another example,
slower one."*  Parked here so it is not lost; this file is the first.

**What the brief is doing, read against `doc/memory/music-craft.md`:**
it walks straight into two of the four mistakes he named in his own
writing and refuses them — *never modulating* (D → G → D) and
*everything middling* (Lydian is the brightest mode, Locrian the least
stable, Phrygian dark but settled).  It also asks for the shape he
named wanting: **stop in the middle, make a cadence, then continue.**

**The session's reading of it, for him to correct:**

* **A — D Lydian.**  Blues bones (I–IV–V as D7–G7–A7) with the mode in
  the melody, so the G♯ lands as a ♯11 over D7.  That is lydian
  dominant, and it is idiomatic rather than clever.
* **B — G Locrian.**  The tonic is G half-diminished and there is no
  perfect fifth to rest on; the ♭2 (A♭) is the colour.  This is the
  brutal middle the arc asks for.
* **The hinge — a deceptive cadence.**  A7 expecting D, going to Bm
  instead.
* **A′ — D Phrygian.**  Dm with the ♭2 (E♭) as its signature, so the
  ♭II–i is the sound of the return.
* **The end — a perfect cadence.**  A7 → Dm.

*Eight bars each, twenty-four in all* — the session's choice, and the
first thing to say if it is wrong.

---

## § Writing — the session's frictions

*One line each, written when met, before the workaround.  A line that
says what was **wanted** and what was **written instead** is worth ten
that say a thing was hard.*

**W1 — duration is not a property of a note, and the piece has no
rhythm because of it.**  *Wanted:* a dotted quarter then an eighth,
written on the two notes.  *Written instead:* every note a quarter, all
ninety-six of them.  `'(Tone …)` is one beat and there is no field on it
for how long; changing a length means wrapping a **phrase** in `|/ 2`,
which applies to everything inside it.  So a bar of mixed rhythm is a
nest of operators around groups that have no musical meaning, and the
groups have to be invented to hold the durations.

*Half of this is my own rule* — I forbade helpers and read `|/` as one
— but the other half is real and is the finding: **length lives on the
phrase, not on the note**, so two notes of different lengths cannot sit
side by side without a bracket between them.  A flat format cannot be
flat unless a note carries its own length.  This is the same corner
Henri named: *flat, but only if it allows writing triplets/tuplets*.

**W2 — the mode is in my head and nowhere in the file.**  *Wanted:* to
say "the ♯4 of D lydian".  *Written instead:* `68`.  Nothing in the
file names the mode, so nothing can check that 68 is the sharp fourth
and not a typo for 67 — and the whole brief was *modal*.  The one thing
the piece is **about** is the one thing the notation cannot hold.

**W3 — the bar is not a thing.**  *Wanted:* four beats in a bar,
checked.  *Written instead:* `a1 … a8` by naming convention, and my own
counting.  A fifth note in `a3` would compile, shift everything after
it by a beat, and be found by ear an hour later.

**W4 — velocity is a number I invented.**  `0.85`, `0.70`, `0.65` — no
*mf*, no *p*, nothing a reader can check or a second writer can match.
A manner is a named intention the voice interprets; a dynamic is
exactly the same kind of thing and is a raw float.

**W5 — the two hands are aligned by counting and by nothing else.**
*Wanted:* bar 16 of the melody over bar 16 of the ground.  *Written
instead:* two lists that happen to be the same length, joined with `||`
at the very end.  Nothing relates `b8` to `h8` but my having named them
so.  **This is the direct answer to §"What is decided" question 1:** a
phrase file that holds one voice's line cannot express the alignment,
and the alignment is where the music is — the deceptive cadence in bar
16 exists only because the line and the ground disagree at the same
instant.

**W6 — I had to write a program to write the notation.**  Voice-leading
twenty-four chords by hand is arithmetic, so a script chose the
voicings and its output was pasted in as literals.  *That is not a
complaint* — it is the shape of the thing: **a notation format's job is
partly to hold what a tool computed**, and an editor's job is to let a
person disagree with it afterwards.  What the file cannot say is that
these notes *came from* a rule; edit one by hand and nothing knows the
rule is now broken.

**W7 — and the rule had to be stated before it was right.**  A leader
told only to *move least* produced **A D A** for a D minor: it dropped
the third, because dropping the third moves least.  The constraint
*every chord tone present, one each* had to be written down explicitly,
and so did *no interval under a minor third* for the open voicing.  Two
musical facts that a notation holding only pitches cannot check, and
that were wrong for one run each.

**W8 — five lines, and the count is the only thing holding them.**  The
piece is now `melody`, `upper`, `middle`, `lower`, `roots`, each
twenty-four bars long and joined by `||` at the end.  **If one of them
had twenty-three bars the piece would still compile** and everything
after the short one would be a bar out for the rest of the piece.  W5,
now five times over, and it is the plainest requirement to come out of
this: *a format that holds voices separately must know they are the
same twenty-four bars.*

**H3 — and the loop we are using is not his loop.**  *Henri, after pass
three:* **"At this point I'd take the editor up open, and see why
locrian doesn't locrian, examine, maybe under the constraints that are
set here."**

**That is an editor requirement stated as a working habit**, and it is
worth more than a feature request.  The loop this log was made with —
the session writes, renders, and hands over a `.wav` — is *not how he
works*.  At the point where the piece is nearly right and the question
is **why does this section not do what it should**, what he wants is
the file open and the thing under his hands, changing one number and
hearing it.  A format and an editor that serve only the first loop
would serve the wrong half of composing.

*So the log's own method has a bias in it, now named:* it produces
evidence about **writing** a piece and almost none about **examining**
one, because examining is the half a `.wav` cannot carry.

## Why locrian did not locrian — measured 2026-09-04

**Half the section was not locrian at all.**  Counting a *place to
rest* as a perfect fifth above the sounding bass:

| bar | bass | chord | rest? |
|---|---|---|---|
| 9, 10, 12, 15 | G | G B♭ D♭ | no — diminished |
| 11, 14 | A♭ | A♭ C E♭ | **yes** — major triad |
| 13 | C | C E♭ G | **yes** — minor triad |
| 16 | A | A C♯ E | **yes** — major triad |

**Four of eight bars gave the ear somewhere to stand**, and the bass
moved between four different roots, so nothing said which note was
home.  Locrian has no perfect fifth above its own tonic, which is
exactly why it cannot establish a centre the ordinary way — it has to
be **forced**, usually by pedalling the root until the ear gives in.

*The experiment, one variable:* pedal the bass on G through all eight
bars and change nothing else.  Every consonant triad becomes a slash
chord over a root that contradicts it — A♭/G, Cm/G, A/G — and the
count goes to **0 of 8**.  That take is
`arc-pedal.ges` in the scratchpad, deliberately **not** folded into
`arc.ges` until he has heard whether it is right.

**H4 — the cadences were not there, and he heard their absence.**
*Henri:* **"I didn't hear cadences.. but they're harder to understand
and I think those would be chords that need to make cadences."**  He is
right twice: a cadence is a **harmonic** event, and there were none.

**Checked, and it is worse than missing.**  The brief asked for a
deceptive cadence in the middle and a perfect one at the end.  The
piece has:

    bar 16 → 17   A7 → Dm     perfect
    bar 23 → 24   A7 → Dm     perfect

**The same cadence twice, and the deceptive one is not in the piece at
all.**  The only B minor sits at bar 6, inside section A, where it
cadences nothing.  *And the file's own comments say otherwise* — bar 16
is annotated "the hinge… what comes underneath is not home", which is
untrue of the notes under it.  **A comment claiming a musical fact the
notes do not carry is worse than no comment**, and nothing in the tree
can catch it: prose about music is unchecked in a way prose about code
is not.

*What would make it a cadence:* A7 → B♭ at bar 17.  B♭ is the ♭VI of D
minor and is **already in D phrygian** (D E♭ F G A B♭ C), so the
deceptive turn and the mode's own colour are the same chord — which is
the kind of thing that is obvious once the modes are written down and
invisible while they are in somebody's head (**W2**).

**H5 — the tonic was not visited, which is his own rule and the one
thing he was sure of.**  *Henri:* *"the melody should occasionally
visit the tonal note to establish a tonal center.  But that's all I
know and sometimes I don't get it right either."*

Counted in the locrian section: **3 of 32 notes touched G**, one of
them at a bar's end, and four of the eight bars never touched it at
all.  His rule was right and the melody broke it.

*And why the rule is the whole mechanism, worth writing down because he
said he could not remember it:* **B locrian is the white notes** — the
same notes as C major — so the ear, given them, defaults to C, the
strongest tonic available.  Locrian's instability *is* that pull, and B
has no perfect fifth to build a defending triad with.  So it is a tonic
that must be asserted continuously against a scale that keeps proposing
a better one, with no consonant chord to assert it.

**Which makes three of today's findings one fact:** visit the tonic
(the only thing holding it), pedal the root (brute assertion), and let
no consonant triad in (a stable chord wins the argument instantly).

*The experiment, one variable:* the locrian melody rewritten to land on
G at the end of every bar — 12 of 32 notes on the tonic, up from 3, and
harmony untouched.  `arc-melody.ges` in the scratchpad.

---

## The result that bounds the whole exercise — 2026-09-04

**Henri went and did it himself, and could not either.**

> *"I think I take the editor.. then I take a MIDI input device I have
> here.. And I'll try to replicate locrian sound from what I
> understand.  I'll do it in a DAW and produce midi out for it……..  and
> you know what.  I failed!  I am myself right now, unable to produce
> locrian sounds.  it would be irreasonable to expect you, with your
> limits, to produce something I am unable to produce myself."*

**The absolution is declined and the fact is kept**, because they point
different ways.

*Declined:* the four things his ear caught were **not** locrian errors.
No third in twenty-four bars.  A percussive envelope under a chord
meant to be held.  The same cadence written twice while the comment
claimed otherwise.  Three tonic visits in thirty-two notes.  Every one
is checkable without knowing what locrian is supposed to feel like, and
every one was found by listening once.  Those were not a limit that
needed excusing; they were four things a number would have caught.

*Kept, and it is the most useful result of the day:* he went to **the
most direct music-writing setup that exists** — a MIDI keyboard, a DAW,
hands on keys, instant sound — and it did not help.

**So "locrian doesn't locrian" is not a notation problem.**  Not a
format problem and not an editor problem.  If it were, the DAW would
have solved it, because a DAW is that problem already solved.  It is a
compositional-knowledge problem, and it stayed hard in the tool best
suited to it.

**That bounds what this card may promise.**  W1–W8 are real notation
problems and a format fixes them — a note that cannot carry its own
length, a bar that does not exist, five lines aligned by counting.
**This was not one of them**, and four passes went into finding that
out.  A future reading that treats "the modes did not land" as a format
requirement is reading the wrong half of this file.

## And what did move it, which neither tool gives

Every step forward came from turning a feeling into a count:

| the feeling, heard | the number, written afterwards |
|---|---|
| *bright all through* | **0** thirds in 24 bars |
| *the chords sink into the background* | **46%** of the bar's opening level at its end |
| *doesn't go to locrian* | **4 of 8** bars offer a perfect fifth over the bass |
| *not that unsettling feeling* | **3 of 32** notes touch the tonic |

**A DAW gives you your ears and nothing else.**  It will not say that
four of your eight bars have somewhere to rest, or that your melody
never says G.  **And neither did gestate** — every one of those four
checks was written by hand, by a session, *after* his ear had already
found the problem.

*The proposal this suggests, and it is not what the exercise set out to
find:* what gestate could offer that a DAW cannot is **not a better way
to write notes**.  It is the box saying *how many bars have a perfect
fifth over the bass* while you write them — the same shape the score
box already is, a view over a span of source, answering a **musical
question** instead of drawing a picture.

**Marked as a proposal and not a finding**, because the evidence is the
wrong way round: all four checks were written after the ear had
spoken, which says nothing about whether they would have found it
first.  *The test is cheap and is the next thing to do:* pick the check
**before** listening, and see whether it names the problem.  Until that
has been run, this paragraph is a hypothesis with four anecdotes behind
it.

---

## He went and did it, and it is the best evidence here — 2026-09-04

*`examples/midi/maybe-locrian.mid` — his, made in Reaper on a licensed
copy, from a piano roll, nothing copied with intent.  Named* **maybe**
*by him, and the name is load-bearing.*

**How he got there matters as much as what he got.**  *"this was
something I produced in DAW with a piano roll.  So I sort of felt it
through what I am supposed to do and knew how to do it with a pianoroll
alone."*  He reached it **by feel**, with a piano roll and no theory,
after four passes in which the session reached for theory and chose the
wrong material.  That is a datum about what an editing surface is *for*
and it is the opposite of what the session would have predicted.

**What the file does, measured** — and stated as measurement, because
he does not claim it is locrian and neither does this:

| | his 57 notes | the session's locrian section |
|---|---|---|
| tonic as a share of notes | **39%** | 9% |
| moves touching the ♭5 | 4 | **8** |
| moves touching the ♭2 | **10** | 6 |
| harmony | **none — monophonic** | three voice-led parts |

**The session built its locrian around the ♭5 and he barely uses it.**
The tritone was in nearly every bar as *"the mode's own wound"*; his
line uses it four times in fifty-six moves.  What his line does instead
is **B↔C, the ♭2 against the tonic, ten times**, with `B→B` and `E→B`
eight times each — it keeps returning.  Which is the Arabic music he
found while reading: **maqam leans on the semitone above the tonic**,
and the tritone is incidental.

*So the session's analysis was right about why locrian is unstable and
wrong about what to do with it.*  The missing perfect fifth explains
the **problem**; it is not the **material**.  And he established the
mode with one line and nothing under it, which the session had said
required harmony.

### And whether it is locrian at all — the evidence splits

Same seven notes as E phrygian; the mode is decided by which note feels
like home.

| points to **B locrian** | points to **E phrygian** |
|---|---|
| B is the most frequent note, 22 of 57 | E **begins** it |
| B is the most returned-to | E **ends** it |
| | E is the **lowest** note |
| | the five longest-held notes are **all E** |

Every marker on E's side is a *structural* tonic cue — first, last,
lowest, longest — and frequency is the weakest of the lot.  **The
session's reading, offered as a reading:** he aimed at B locrian and the
piece's own structure argues E phrygian.

**Which is not a failure but the phenomenon itself.**  Locrian is hard
because its tonic cannot hold the argument, and here is a case where
the composer aiming at it, working by hand, produced something whose
every structural marker points at the neighbouring mode.  His hands
reached for the note that wanted to be home — the same thing that
happens to a listener, and why the mode barely exists in the
repertoire.

### Two over-readings, recorded because they are a pattern

The session read **the missing D** as a deliberate practice — no third,
so the mode cannot collapse — and even withdrew a correction on the
strength of it.  *Henri:* **"that D was really my mistake of losing.
it's funny coincidence that I didn't use it."**  It was a slip, twice.

And it treated a file called **maybe**-locrian as the reference against
which to score the session's own attempt, when its author had said in
the filename that he was unsure.

**Both are the same failure**, and it is the one that put an untrue
comment on bar 16: *asserting more than the evidence carries.*  A
reader of anything the session writes here should know it runs that
way, and that the numbers in this file are worth more than the
sentences around them.

### Pass four — the section rewritten from his file

*Henri: "Would you like to try locrian again with the new information
you got?"*  Four lessons, three of them from his MIDI and the fourth
from the analysis of it, and **the checks were run before listening** —
which is the first time all day that happened and was the whole point
of §"The result that bounds the whole exercise".

|  | his | the first draft | pass four |
|---|---|---|---|
| tonic as a share of notes | 39% | 9% | **44%** |
| moves touching the ♭5 | 4 | 8 | **2** |
| moves touching the ♭2 | 10 | 6 | **8** |

And the four structural cues, spent on G on purpose: **first** note of
the section, **last**, **lowest**, **longest held** — plus the bass
pedalled on G, which is 0 of 8 places to rest.

*That fourth lesson is the one neither of us had used deliberately.*
His file's tonic is the most frequent note and its structure still
argues for a different one, because first-last-lowest-longest beat
frequency.  A mode is not established by which note you play most; it
is established by which note the **shape** puts at the ends and the
bottom.

**Whether it works is his to say**, and the honest note is that the
numbers agreeing with his file proves only that the numbers agree.

### H6 — *"something in the way you select notes"*

*Henri, on pass four, after the pitch statistics already matched his
file:* **"I think you learned and understood how it's done, but there's
something else wrong in the way you produce it, and that makes it not
land."**  And when the session leapt at rhythm: **"I mean that there is
something in the way you select notes there.  But lets add the rhythm
because it's one of those things that I think would make it more
going."**

**He was pointing at the melodic motion, and it measures.**  The
session had only ever counted *which* notes; this counts *how they
move*:

| | his | pass four | pass five |
|---|---|---|---|
| stepwise moves, a tone or less | 70% | 58% | 74% |
| leaps | 30% | **42%** | 10% |
| direction changes | 30% | **44%** | 31% |
| widest leap | a fifth | **a minor seventh, ×3** | a fifth |
| repeated notes | 19% | 15% | 15% |

**His line walks; the session's zigzagged.**  The semitone is his
commonest interval, seventeen of fifty-six; and the minor sevenths came
from a cell that started a tenth above where the last one ended — the
session was *picking notes out of the scale* rather than moving through
it, which is the difference between a line and a list.

*And the leaps are still short of his* — 10% against 30% — which is
left standing rather than fitted, because matching a histogram is not
the same as writing a phrase and the session has already spent a day
learning what over-fitting to a number looks like.

### And the rhythm, which was a second thing and closes W1

**56 of his 57 notes are shorter than a quarter.  0 of the first
draft's 91 were.**  His line runs at eighths and sixteenths; the
session's ran at quarters for sixty-two seconds.

**That is `W1` arriving as a musical fault.**  The first friction in
this log — *length is not a property of a note* — was written down in
the morning and treated as filed.  It is also why four passes were
spent tuning pitch on a line that had no rhythm in it: the format made
the rhythmically dead version the easy one to write, and it was written
four times without anybody noticing.

*So the bound in §"The result that bounds the whole exercise" needs
one qualification.*  **His** failure in the DAW was not a notation
problem — that stands.  But **the session's** failure substantially
was: the easy thing to write was the wrong thing, and the log had said
so before the first note was played.

### Two things ruled out on the way

His velocities are **all 96** — no dynamics anywhere — and his file is
**100% sounding, no rests**.  So neither the session's invented
velocity floats (`W4`) nor its total absence of breath explains the
difference.  It was interval motion and speed, and nothing else the
numbers could see.

### The injection, and the first check that went ahead of the ear

*Henri: "Can you do one thing?  transpose the pitch sequence of
maybe-locrian and inject it directly into the piece."*  His line, +8 so
its tonic lands on G, over the piece's own harmony, bass and voice.

**And before he listened, the check said what would happen.**  His line
and the harmony under it use *complementary halves of the mode*:

| | notes used |
|---|---|
| his line, transposed | C, E♭, F, G, A♭ |
| the chord beneath it | B♭, D♭, G |

**G is the only note they share.**  The chord is built on the ♭5 his
melody deliberately avoids — D♭ is in nearly every chord written here
and appears nowhere in his line.  The same disagreement as §H6, now
stacked vertically: *the session read locrian as the tritone and he
read it as the ♭2*, and neither is wrong alone.

*The prediction, written before he played it:* it will hold in the four
bars whose chord is G–B♭–D♭ and fall apart at bars 14 and 16, and
throughout there will be a sense of the accompaniment **arguing rather
than supporting**, because it insists on the note he left out.

*His verdict:* **"yes.  the accompanient doesn't support the melody
now."**

**That is one pre-registered success, and it is worth exactly one.**
§"The result that bounds the whole exercise" says the proposal — *a box
that answers a musical question about the span it covers* — was a
hypothesis with four anecdotes behind it, all written after the ear had
spoken.  This is the first check written **before**, and it named the
fault.  n = 1, and the honest weight of that is: the shape of the
evidence is now right, and there is one of it.

**And he could not finish it either.**  *"I could actually try that in
reaper as well... nope.  I'm not figuring it out this time."*  Which is
where the piece stops: `arc.ges` stands at pass five, his line lives in
`examples/midi/maybe-locrian.mid`, and the injection was an experiment
and not folded in — it is his melody and not this piece's.

*The fix nobody has tried:* rebuild the chords on the ♭2 as well — A♭
over the G pedal instead of G–B♭–D♭ — so the harmony and the melody
hold the same theory of the mode.  Left undone, deliberately, because
he stopped and the log is worth more finished than the piece is.

---

### The blues asymmetry — why the failure was surprising, and a check for it

*Henri, closing:* **"I didn't expect you would not capture locrian
because you do so well in blues."**

That is the sharpest thing said all day about the collaborator, and it
names a real asymmetry: **the definition was available and the sound
was not.**  Locrian's contents were stated correctly at every pass —
seven notes, ♭2 and ♭5, tonic B in the white-key form — and five passes
of writing from that definition still did not produce the mode.  Blues,
by his account, arrives without any of that effort.

**The hypothesis, and it is a hypothesis.**  What exists in writing
about locrian is almost entirely *definitional* — the seventh mode, the
diminished fifth, unstable, rarely used — because almost nobody writes
music in it, so there is theory and no repertoire.  Blues is the
mirror: the theory in words is thin and hedged, and the examples are
everywhere.  A model built from text would then hold locrian as a
**correct description it cannot instantiate** and blues as an
**instantiable pattern it cannot describe well** — which is exactly the
shape of the day: the account was right every time, the output was
wrong every time, and §H6 found that the fault was in note *selection*
rather than in the account.

**The check was already run, twice, and this log said it wasn't.**
`examples/audio/blues.ges` (twelve bars in A, `ac6667f`) and
`examples/audio/perjantai.ges` (a Friday blues in E, 2026-08-28,
`ee329fc`) are both in the tree from earlier sessions, and Henri's
verdict on the second is **"just perfect"**.  Proposing it as an unrun
experiment is the fault §"A targeted set is a claim" names — a `none`
verdict pronounced without grepping for the repair's own vocabulary —
committed in the same document that files two over-readings as a
pattern.  Recorded rather than quietly fixed, because the failure is
the interesting part: **the session did not know its own repertoire.**

**And Henri's competing cause defeats the design anyway.**  *"I think
less constraints are there, you succeed in producing good music."*
Blues is both well-exemplified **and** loosely constrained, so a blues
that lands cannot separate the two hypotheses.  The comparison is
confounded and always was:

| | arc.ges | perjantai.ges |
|---|---|---|
| lines | 599 | 305 |
| constraints imposed from outside | ABA form, I–IV–V, three modes, D→G→D, deceptive cadence at the middle, perfect cadence at the end | *"a Friday blues"* |
| passes before it was any good | five, and it never got there | one |

**But "fewer constraints" needs refining, because perjantai is not
loose.**  Its header lists a quick change in bar two, a V in the last
bar, three choruses and a tag, a stop-time third chorus, an octave drop
in the second, and swing by arithmetic.  That is at least as much
structure as the arc carries.  The difference is not the **number** of
constraints but where they came from: perjantai's were **chosen from
inside a known idiom by whoever was writing**, and the arc's were
**handed in from outside in an idiom the writer had only a definition
of**.  A constraint you selected is a thing you already know how to
satisfy.

**The design that would actually discriminate** crosses the two
factors, one pass each, no ear in the loop:

|  | *loose* | *constrained* |
|---|---|---|
| **blues** | already done — `perjantai.ges` | **not run** — ABA, modulate, cadences named |
| **locrian** | **not run** — *"something that sounds locrian"*, no form | already done — `arc.ges`, failed |

Two cells are filled and they are the diagonal, which is why nothing is
settled.  If constrained-blues lands and loose-locrian doesn't, the
cause is **repertoire**.  If constrained-blues also falls apart, the
cause is **imposed constraint load**, and the whole day's failure says
less about locrian than about being handed six requirements at once.

Either answer bears on the sub-language card's *LLM-friendly and
testable*: the useful test is not comprehension.  **A session can read
notation it cannot write**, and may be able to write only what it can
also choose.

*And his own note beside it, which keeps it honest:* he could not
produce locrian in Reaper either, with a MIDI keyboard and thirty
years' more ear than any of this.  Whatever the asymmetry is, it is not
only the machine's.

---

## What the two passes cost, in one place

| | pass 1 | pass 2 |
|---|---|---|
| notes written | 192 | 312 |
| harmonic intervals that are a third | **0** | every chord |
| lines aligned by counting alone | 2 | **5** |
| written by hand | all | melody only; the harmony is a script's output |

**And the arc is one semitone.**  Bar 1 is `57 62 66`, bar 17 is
`57 62 65`.  Everything else about the harmony is identical between
bright and dark, which is what a third does and what pass 1 had no room
for.

---

## § Hearing — Henri's frictions

*His, when he plays it.*

**H1 — the arc did not land, and the reason is harmonic.**  *Henri,
first pass:* **"I feel like it's bright all through, with some oddness
in middle.  I think that... tonal center is missing, and harmony would
do lots to the tone, but it's absent.  Harmony with open chords in it,
voice leaded as individual voices.  could be good."**

**And the file agrees, measured.**  Every harmonic interval the ground
writes is a perfect fifth — nine distinct chords, all root-and-fifth,
**not one third in twenty-four bars**:

    intervals present : 2, 5, 6, 7, 9, 14
    thirds (3 or 4)   : NONE

A bare fifth is **modeless**.  So D lydian and D phrygian were
harmonically *identical* and the entire arc lived in the melody line,
where one voice cannot carry it.  The section that sounded odd is the
one whose melody has the ♭5 in it; the two that should have differed
most differed not at all.

**The session's own check missed it and the miss is instructive.**  It
measured that all three sections have the same RMS and said out loud
that this *"tells us nothing about whether it lands"* — which was true
and was treated as a limit rather than as a reason to check something
else.  **A level meter cannot hear a third.**  The ear found in one
listen what no number in the file was watching for.

**H2 — pass two: the chords are there and still not present.**
*Henri:* **"it begins as hopeful and happy, maybe a bit random-feeling,
but doesn't go to locrian or phrygian.. there's not that unsettling
feeling about it that would belong to those modes.  Also the chords
could be more present, they sink into the background now."**

**And the cause was in the instrument, not in the notes.**  The harmony
voice used `perc`, which `synth.ges` describes in as many words as
*"for a struck or plucked voice, which does not sustain"*.  A whole-bar
chord under a percussive envelope states its mode for an instant and
leaves two seconds of nothing after it.  Measured across the piece:

| | level at the end of a bar, against its start |
|---|---|
| pass 2, `perc` | **46%** |
| pass 3, `adsr` with sustain | **92%** |

So the piece had harmony **on paper and almost none in the air**, and
*a mode is a chord you are still hearing*.  Written down as a hearing
friction rather than a compositional one because that is what it was:
the notes were right and the voice threw them away, and no reading of
the score could have shown it.

**And the measurement that would have caught it is the one nobody
wrote.**  Twice now the session has measured *level per section* — a
number that cannot see a third and cannot see a decay.  What it should
have asked is **how much of a bar still has harmony in it**, which is
one line and is now in the log.

**What he asked for after pass one, and it is a format requirement not
a compositional note:** *harmony with open chords, voice-led as
individual voices.*  Voice leading means each chord tone is **its own
line through time**, not a stack rebuilt every bar.  Written the way
this file writes things, that is four separate lists aligned by nothing
but their length — **W5 again, multiplied by four**, and the strongest
argument yet that a phrase file must hold a *bar across voices* rather
than one voice's line.

---

## The next day, and the design in §"The blues asymmetry" is refused — 2026-09-05

**The loose-locrian arm ran.**  `examples/audio/hollow.ges` (`f382785`)
— B locrian, one pass, brief in full: *"Write anything that sounds like
locrian, for examples/audio/.  Don't read board/ today — I'll explain
after."*  **Henri:** *"I think that this unconstrained was better than
constrained version."*

That fills the diagonal's empty cell, and a loose-beats-constrained
result **inside one mode, from one writer** is the within-mode contrast
the 2×2 was built to get at.  It is also one contaminated draw and is
worth exactly that — see below.

**What the arm did with this file**, since that is what the file is
for: the ♭2 as the material and not the ♭5; the four structural cues
(first, last, lowest, longest) spent on the tonic; a pedal that makes
*places to rest* **0 of 24 bars** by arithmetic rather than by taste;
and the counts run **before** the first listen.  `tools/modecheck.py` is
now the command behind them, which closes §"And what did move it": the
four numbers that day were all written after the ear had spoken, and
this is the first time the check was a thing you could run first.

### And the trial it belonged to was refused, on a measurement

`card:idiom-or-load.md` is in `board/refused/`.  **Henri:** *"it's too
hard for me to isolate and restrict everything down to make a good test
here."*  And before that: *"I noticed that asking to not look into
board/ was insufficient.  You still figured it out this was a test
setting."*

**Neither the session nor the fence was at fault; the tree reads
`board/` for you.**  `tools/backlinks.py`'s Read hook fires on every
file open and quotes the citing cards back — so opening *this file*,
which the work requires, printed two lines of the card into the arm's
context on its second tool call, one of them containing the words *the
two arms*.  The card named this log and `arc.ges` as the two files that
void the arm, and citing a file is precisely what makes the hook read
its cards aloud.

**And the second leak is these very paragraphs.**  §"The blues
asymmetry" holds the 2×2 with both cells marked *not run* and quotes
the loose brief word for word — while also holding the four
measurements that made `hollow.ges` better than `arc.ges`.  *The useful
half and the leak are the same section*, so an arm cannot be handed one
without the other.  Splitting them is one of the three costs the
refusal names.

**So the proposal at the end of §"The blues asymmetry" — the crossed
design, one pass per cell — is withdrawn as written.**  The two
hypotheses it was built on, H-idiom and H-load, are untouched and
unanswered.  What is refuted is that this tree can run the trial
blind without three pieces of setup nobody had budgeted:
`board/` absent from the arm's clone, the hook silenced, and this
section split out.  `board/refused/idiom-or-load.md` keeps the whole
argument.

*One more rule, learned by breaking it:* the card's control said **two
arms never in one session**.  Both arms ran in `/home/cheery/gestate`
at the same time, and the locrian arm committed its file, its
measurement script and a describing commit message into the blues
arm's `git log` while that arm was working.  **Two arms never in one
working tree** is the rule that was missing.

---

## What this is not

Not a card and not a spec.  When a friction here has been met three
times it is a requirement, and requirements go to
`card:drawn-scores.md`; the paragraphs stay here.
