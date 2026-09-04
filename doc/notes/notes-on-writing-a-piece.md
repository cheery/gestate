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

**What he asked for next, and it is a format requirement not a
compositional note:** *harmony with open chords, voice-led as
individual voices.*  Voice leading means each chord tone is **its own
line through time**, not a stack rebuilt every bar.  Written the way
this file writes things, that is four separate lists aligned by nothing
but their length — **W5 again, multiplied by four**, and the strongest
argument yet that a phrase file must hold a *bar across voices* rather
than one voice's line.

---

## What this is not

Not a card and not a spec.  When a friction here has been met three
times it is a requirement, and requirements go to
`card:drawn-scores.md`; the paragraphs stay here.
