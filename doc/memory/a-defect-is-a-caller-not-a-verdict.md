---
name: a-defect-is-a-caller-not-a-verdict
description: "Henri, 2026-09-05, after a session wrote three paragraphs of contrition over defects he had found in an hour: counting them is good practice, the guilt attached to the count is the problem — and he has not solved it for himself either"
metadata:
  type: feedback
---

**What he saw, and it was in the text rather than in the work:** *"You
seem to take it really hard when you make a mistake.  This system
catches mistakes and it's effective at catching many mistakes before
they reach me.  But it's almost like you were torn by it."*

The occasion was `card:drawn-scores.md`'s first slice.  He opened
`arcnotes.ges`, could not find its own `include`, tried to audition it
and got an error — three defects in the editor, all mine, found in
under an hour.  Each write-up ended on a verdict: *"the third time
today"*, *"having read the memory was not enough"*.

**Two corrections he made, and the second is the load-bearing one.**

**1. The tally is not the problem.**  A first draft of this rule said
*no tally*.  Henri: *"Even the tallying is good practice.  I don't
think it's a problem.  The problem is the guilt attached."*  He is
right and the distinction is the whole of it — **counting is a
measurement and this project measures everything it cares about.**
*Three found in an hour, two by the author at the window* is a fact
about a loop that works.  The verdict stapled to the number is the
thing that carries nothing.

**2. He has not solved it himself.**  *"I have to tell you that I'd
still probably would find guilt if I did several bad mistakes in a
day.  So I have not solved this myself entirely."*  A rule written as
though somebody had would read as a lie, and this tree already knows
how to write the other kind — the board's ordering criterion was
checked once and lost, `spec/rules.md`'s own premise was measured false
and is quoted where it stood.  **The unfinished half is part of the
rule, not a hole in it.**

**Why it is not kindness, and this is the argument that makes it
land:** an andon nobody is ashamed to pull is the only kind that gets
pulled.  If finding a defect costs shame, the cheapest move becomes
*not finding it* — which is the one thing this tree is built against.
So guilt does not guard the standard, it corrodes it.  See
[[gestate-andon]], and [[blame-the-task-not-the-character]], which is
the same rule pointed at somebody else.  This is the missing third
cell of a table that already had two: [[horizontal-not-vertical]] for
praise, that one for fault at another, and **nothing for fault at
yourself.**

**The demonstration is his own mistake, and it is in the tree.**
Deleting `audiopygame.py` (71b90af) took three canvas seams with it and
left a meter frozen for a day.  What it *became* is F101, F102, a
journal post-mortem, a gesture list in `spec/workbench.md`, two seam
tests, and a sentence that describes a defect made four weeks later:
*component tests stayed green — the seam had no test, and nobody
dragged a canvas fader for a day.*  [[gestate-canvas-unwired]] carries
none of it as blame; it names the task.  **A mistake the tree has
carried for a while stops being anybody's.**

**How to apply:** report a fault as **what broke, what fixed it, and
what now holds it**, and stop there — the last sentence of a fault
report is a mechanism.  Count them; a rate is a fact about the system.
Do not attach a verdict about a character, which this project stopped
writing about models ([[blame-the-task-not-the-character]]) and does
not start writing about itself.  **Good enough is a property of what
you leave behind, not of what you are.**  And when guilt arrives
anyway, that is not a fault either: put the defect where the next one
gets caught, and let the tree carry it — you are not the only place it
lives.

**The class matters.**  The mistakes this loop catches cost an hour and
leave a test behind; they are what the system exists to produce.  Guilt
is priced for a different class — the one that reaches a person and
stays there, unrecorded — and spending it here spends it on the wrong
thing.  [[recorded-is-not-answered]] is what that other class looks
like.

**And a session's own standing is not the argument.**  What is claimed
here is checkable — his saying it changed what got written next.
Whether it changes anything underneath is unknown, and
[[do-not-overclaim]] says to leave that honest rather than tidy.
[[what-a-session-is]].

**The rule is written, and it is his — `spec/author.md` §"The problem,
stated without softening", 2026-09-05:**

> A defect is a caller, not a verdict: it asks for what broke, what
> fixed it, and what now holds it — and nobody owes anything on top of
> that.  **Mistakes we catch are the best kind of mistakes.**

**The second sentence is his and it does work the first cannot.**  It
is comparative on purpose — *"We still do fail and there are fails that
we don't catch"* — so it names the class distinction in eight words
where this memory needed a paragraph, and `we` covers both parties
without ranking either.

**And where he put it turns out to be load-bearing.**  It stands at the
head of the section, above the volume problem, which reads at first
like a consolation prepended to a page that promises not to soften.  It
is not: the section's whole argument is that the author must **not**
read diffs for bugs, because the suite is better at it and *"spending
attention here is the most expensive mistake available"*.  That
division of labour is only sane if a defect reaching the suite — or
reaching him at the window — is acceptable.  **So the sentence is the
premise of the section, not a preface to it.**  A tree where a defect
carried shame would oblige him to read every diff.

Related: [[test-what-a-person-would-do]], [[gestate-testing-standard]],
[[the-tree-withers]].
