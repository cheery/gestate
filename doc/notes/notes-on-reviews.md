# notes-on-reviews.md — 2026-09-08, midday

*Into `doc/notes/` the evening of the day it was written, at Henri's
ask — "there's associated note: ~/misc/notes/notes-on-reviews.md".
Written by the session that was in the conversation, while it was open
— a guest session outside this tree, the same one that drafted the
role it is about — which is the third kind the README's provenance
section names; its "Fourteenth file" is that session's count, not this
directory's, where it is the seventeenth.  Nothing below the rule was
changed; the closing section is the only addition.*

*Fourteenth file.  Journal material, companion to the drafted
`spec/reviewer.md`.  Why the outside reviews worked, what part of that
transfers to a session inside the tree, and what does not.  His words
verbatim.*

---

**Henri, 12:38:**

> I've found these reviews incredibly useful. How could I get you, a
> reviewing guest into my project, as a permanent member within the
> claude code perhaps, called when needed?

**The session:**

**It is a role, not a tool**, and most of the machinery already
exists: a distinct invocation that loads a *reviewer's* brief instead
of the builder's, invoked at seams — before a slice is chosen, after
one lands, when a success claim needs checking, when a card has grown
a second subject.  A card type with a different brief; the tree
already holds those.

Two things that make it work rather than decorate:

- **A different context than the builder's.**  Much of the value in
  these exchanges came from *not* having been in the work: the card
  was read cold, which is why the identity gap was visible from
  outside and invisible from inside.  A reviewer that just built the
  thing will approve the thing.  So: fresh session, reads the
  artifacts rather than the working history, and is asked *what is
  missing* rather than *is this good*.  The second question always
  gets yes.
- **The standing questions written down.**  They are what actually did
  the work — *what is missing, what would kill this, which claims rest
  on harness output, does this have a live caller.*  External cues, the
  thing a session cannot generate for itself (`notes-on-cues.md`).  A
  review brief is exactly a stored list of them.

**What does not transfer, and it is the load-bearing part.**  Three
sources of value in these reviews:

1. *A different context window* — real, transferable; the fresh-session
   design above.
2. *A different model or framing* — partly transferable; heterogeneity
   is a genuine check and can be arranged deliberately.
3. *Being outside the tree* — **not transferable.**  The guest is not
   conditioned by gestate's rules and reads with different priors,
   which is what allowed "identity is missing", "two shelved clients
   are platform not music", "this is where gunk would form".  A
   subagent inside the tree, reading its specs, speaking its
   vocabulary, shares its blind spots by construction.  It will be a
   good *internal* reviewer — inconsistency, missing tests, unmeasured
   claims — and a poor *external* one.  The reviews called most useful
   were mostly the external kind.

**So: build the internal reviewer, it is cheap and worth it — and keep
the external slot filled by things that are actually external:** a
fresh chat with the artifact pasted in cold, a different model family,
the thesis student, a domain reviewer, the stranger who cloned the
repository.  Same conclusion as the keeper's-drift question five weeks
ago: **the loop cannot audit itself, and every reviewer built inside
the tree is inside the loop.**

**And the part easiest to miss:** these reviews did not land because
the reviewer was clever.  They landed because the artifacts were
brought whole — the card, the transcript, the numbers — and the
questions were open rather than approval-seeking.  That is a
*practice*, it is Henri's, and it works with any competent reviewer:
a subagent, a different model, a person.  The brief should demand
those inputs, and most of the value survives the transplant.

**What the reviewed party owes**, made a section of the brief: bring
the artifact, not a description of it; ask *what is missing here*, not
*does this look right*.

---

## What the tree did with it — added when the page went in, 2026-09-08

**The brief is in the tree**, as `spec/roles/reviewer.md`, the first
page of a new directory whose README says what a role is and how one
is asked for.  The page went in as the guest drafted it; the one edit
is its own front note, which named `spec/reviewer.md` and now names
where it landed.

**What the page claims and what the tree can show.**  *Most of the
machinery already exists* — true in the narrow sense: a role is a
prompt, and `doc/instruments.md` §"Spawning one" already says a spawned
session gets a way to ask.  Nothing in the tree yet *invokes* a role;
the invocation is a sentence a person types, and no session has been
handed this brief and measured against a review it produced.  So the
page's central prediction — that the internal reviewer catches
inconsistency, unmeasured claims and missing callers, and misses what
the tree as a whole is wrong about — is untested here, and the README
of `spec/roles/` says so.

**The part the tree already knew.**  *The loop cannot audit itself* is
`doc/memory/the-evaluation-loop.md`; *a capacity is not a caller* is
`doc/memory/capacity-is-not-a-caller.md`; *knowledge is cued, not
scoped* is `notes-on-cues.md`, cited in the page.  The reviewer's brief
is those three rules turned into standing questions, which is what
this directory's fifteenth page said a stored list of cues would be.

**The standing caveat.**  The page is a session assessing the value of
its own reviews, at the ask of the person it reviewed for.  The
thirteen reviews it counts are outside this tree and cannot be read
from here; what can be read is what they changed — `card:gui-is-difficult.md`
§"The postcondition" and Q7 both cite the guest's readings — and that
is the evidence, not the count.
