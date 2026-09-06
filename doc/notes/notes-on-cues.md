# notes-on-cues.md — 2026-09-06, a Sunday morning

*Into `doc/notes/` the same morning, at Henri's ask — "notes-on-cues.md
could go into notes as well, but initiate some projects today."  It was
written by the session that was in the conversation, while it was open:
the third kind the provenance section below names, and its "Twelfth
file" is that session's count of the pages it knew of, not this
directory's — here it is the fifteenth.  Nothing below the rule was
changed; the closing section is the only addition.  What became of
"initiate some projects" is `journal.md`, 2026-09-06, not this page.*

*Twelfth file.  Journal material.  Three exchanges from one sharp
morning: the two-systems mapping, why knowledge seems scoped by
context, and whether an introspective index can be built.  His words
verbatim; the session's answers condensed.*

---

## The two-systems mapping

**Henri** (05:07, having started *Thinking, Fast and Slow*; 05:40):

> this is odd read. system 1 (intuitive) feels like an LLM whereas
> system 2 feels like what I built over it. But this is merely a
> feeling of how it seems to map.

**The session:**

**Where it holds.**  A forward pass is fast, parallel, automatic,
fluent, effortless, and cannot say why — System 1's job description.
The failure modes match too: WYSIATI is the model answering from
context and not knowing what is missing; the availability heuristic
is the frequency prior; confident confabulation is System 1
substituting an easier question.  The tree does System 2's work:
slow, effortful, serial, invoked by rule rather than impulse, and it
*checks* the fast output rather than generating a rival.  As an
analogy it earns its keep, and it explains the method: **the fast
system was not made smarter — it was given an external slow one.**

**Where it breaks, and this matters more.**  System 2 in humans is
also neural — slower recruitment of the same brain; Kahneman called
the two systems useful fictions, characters in a story, not regions.
And crucially: **a reasoning model's chain of thought is not System
2.**  It looks like deliberation but is still one forward pass
generating tokens — fast machinery imitating slow machinery.  The
SimpleQA *think* arm is the evidence: separating the reasoning
channel barely moved the bins (62/31/57 → 60/31/59).
Deliberation-shaped output did not produce deliberation-shaped
results.  **You cannot get System 2 by asking System 1 to think
harder; you get it by putting a check outside the generator.**  Third
break: the tree is not autonomous System 2 either — no will, no
attention budget, no monitoring; it runs only when a session reads it
or a suite fires.

**The corrected three-part map:** the model is the fast generator;
the tree is *externalised, cached* slow thinking — the residue of past
deliberation, stored where it conditions future fast passes; the
keeper is the live executive that decides when to invoke it and
whether the output is right.  This makes a checkable prediction:
**the tree can only supply deliberation already done and written
down; it cannot do novel slow thinking in a new situation.**  Which
is exactly why derived.md failed and why mechanisms transferred while
judgment did not.  The stored System 2 travels.  The live one is the
keeper.

Caveat: this is the old hallucination finding — *the architecture has
no second system, so checking must be external* — in vivid
vocabulary.  A satisfying analogy is where the second-pass rule
applies hardest.

---

## Why knowledge seems scoped by context

**Henri** (05:58):

> You know massive amount of things, but mostly when I request them I
> get them. their acces seem to be scoped by context a lot.

**The session:**

Closer word: **cued**, not scoped.  Everything is in the weights;
nothing is locked.  What gets retrieved is a function of what is in
context, the way human memory is cue-dependent rather than
directory-listed — you cannot enumerate what you know either; you
produce what the situation evokes.  The forward pass is
retrieval-by-similarity and the prompt is the similarity.  Mention
Toyota and the lean neighbourhood lights up; leave it out and it
stays dark even when the problem needs it.

Hence the specific limit: **a session cannot tell you what it knows
that you did not ask about.**  There is no introspective index; an
unactivated thing is not experienced as missing, so there is nothing
to report.  This is why the answer arrives *after* the question, and
why quality is so sensitive to framing — the framing does the
retrieval.

**What follows practically:** the bottleneck is neither party's
knowledge but **the keeper's question-forming**, because the question
is the retrieval key.  Same conclusion as the competence list, from
another direction: no session can ask on the keeper's behalf what it
does not know is missing.

Two techniques, named as technique rather than habit:

- **Ask for the space, not the answer** — "what else should I be
  asking here?", "what is the standard literature on this problem?",
  "what would a professional check that I haven't?"  These cue the
  neighbourhood rather than the item, and their answers are retrieval
  keys for the next question.
- **Give more context than feels necessary** — every detail is a cue.
  The good answers this month clustered on messages that pasted the
  actual document, error, or quote; specific material retrieves
  specific knowledge, vague material retrieves generic knowledge.
  This is also why *go and look* is the best rule in the tree: it is
  a retrieval instruction.

Caveat: cue-dependence is not a safety property.  The same mechanism
that surfaces the right concept surfaces a plausible-shaped citation
with equal confidence.  It is the reason the checks exist.

---

## Can an introspective index be built?

**Henri** (06:07):

> what else should I be asking here? What is interesting about this
> all? could introspective index be added into this design I have?

**The session:**

**Not into the model — into the tree, which is the part that is
enumerable.**  A list of "what I know about X" is generated like
everything else: a plausible list, not an inventory.  Do not build
that.  Three things that can be built:

1. **A coverage map of the tree.**  Backlinks went halfway — read a
   file, see who cites it.  The other half is showing a working
   session *what areas of the tree exist*, so it knows there is
   something to look for rather than only what it happened to grep.
   Not introspection into the model: a map of the external memory,
   which converts "I get the knowledge when I request it" into "the
   session can tell there is something to request."
2. **An index of past retrievals.**  What sessions looked up when
   working similar cards; what they wished existed.  This is Delta's
   "landmarks" — the files earlier agents returned to, handed to the
   next one — and the journal plus `doc/memory/` are its manual
   version.  Grounded in what actually happened, unlike
   weight-introspection.
3. **Standing questions.**  Since cue-forming cannot come from the
   session, it comes from a checklist: "what would a professional
   check that we haven't?" as a required step on certain card types.
   A stored cue — externalised System 2 again, converting a judgment
   that might be forgotten into a step that fires.

**The design constraint, added at Henri's cue:** a cue must *reach
the context*, not merely exist in the tree.  A perfect index nobody
reads changes nothing — the tree's own rule about rules.  So the
question is never "what cues would help" but **"at what moment does
this cue land in front of a session about to need it"** — which is
why backlinks are the right shape and why standing questions must
attach to a card type rather than sit in a file.

**What else to be asking** (for the fire, not the keyboard):

- *What does the tree not cover?*  There is a map of the rules and no
  map of the gaps; absence is invisible by construction.
- *Which claims rest on session testimony versus harness output?*
  Still an afternoon's inventory, still unrun, and it sharpens every
  outside conversation.
- *What would falsify the method?*  Benchmarks have pre-registered
  predictions; the method as a whole never has.
- *What does finishing gestate require?*  The unfinishedness is the
  standing tension with its own vision, and the one topic that never
  gets a timestamp.

**What is interesting about all of it:** the month keeps producing
the same finding from new directions — **the intelligence is not the
bottleneck; the retrieval and the checking are.**  Fast generation is
abundant and cheap; what is scarce is knowing what to ask for and
being able to tell whether what came back is true.  That is the
hallucination answer, the tree's reason for existing, the SimpleQA
result, and now Kahneman saying it again.  If the work has one thesis
for the outside world, it is that — and it is far more defensible
than anything about agency or discovery, because there are
measurements for it.

---

## What the answers lean on, and where each of it stands — added 2026-09-06

*By the session that filed it, the same morning, from a grep of both
trees and three measurements.*

**In `~/tend`, and a first grep said otherwise.**  *The SimpleQA
think arm* and its bins, 62/31/57 → 60/31/59, are
`~/tend/doc/benchmark-simpleqa-2026-08-31.md`, committed 2026-08-31:
150 questions, four arms, and the *think* arm as the control that
separating the reasoning channel barely moves the bins, exactly as
quoted.  The session filing this page grepped both trees for the word
and wrote *in neither tree*; Henri pointed at the file within the
hour, and the same grep re-run found it.  Why the first returned
nothing is not known, and it does not matter: an empty result from one
search was taken as a fact about the world, which is
`doc/memory/dont-conclude-from-a-shallow-check.md` word for word, on
the page whose subject is retrieval.

**In neither tree.**  *Delta's "landmarks"* — Henri: *"nothing on
Delta"* — and the *afternoon's inventory* of which claims rest on
session testimony versus harness output, which became
`card:testimony-inventory.md` the same morning.  *The competence list*
is the page filed beside this one, `notes-on-prerequisites.md`.

**In the tree.**  *The old hallucination finding* is
`doc/memory/why-models-hallucinate.md`.  *Why derived.md failed* is
`doc/memory/deriving-strips-the-payment.md`.  *Go and look* is
`board/README.md` §"Question it into existence", move one.
*Benchmarks have pre-registered predictions* is `tools/prereg.sh` and
`doc/trial/README.md`, three sheets on 2026-08-23; and *the method as
a whole never has* is true of both trees on the morning this went in.
*The unfinishedness* has a page, `roadmap.md` §"What is left after
stage 10", and no timestamp, as the answer says.

**The three buildable things, measured on the morning they were
proposed.**

1. *A coverage map of the tree.*  Walked from `CLAUDE.md` over every
   `.md` reference: 191 of 241 pages are reachable, none deeper than
   five hops, and 113 of them sit at hop four.  Of the 50 unreached,
   37 are cards on the three shelves, which the board reaches by `ls`
   on purpose; 7 are driven-run reports; 4 are READMEs nothing links
   (`spec/gates.md`, `specimens/README.md`, `gestate/substrates/README.md`,
   `gestate/templates/README.md`); 2 are tool droppings.  So the map
   mostly exists and the gap is four files, not a mechanism.
2. *An index of past retrievals.*  `tools/backlinks.py --report` is
   already the manual version: 172 fires in 14 days, 48 followed, a
   sitting id on each since it got one.  What does not exist is the
   per-card view the answer describes.
3. *Standing questions on a card type.*  Nothing in either tree fires
   a question at a session at a moment; `board/README.md`'s seven moves
   are prose.  This is the one of the three with no mechanism under
   it.

**The standing caveat.**  The closing paragraph — *the intelligence is
not the bottleneck; the retrieval and the checking are* — is the tree's
own thesis coming back from something the tree conditioned,
`doc/memory/the-evaluation-loop.md`; the page's own second-pass rule
applies to it.  What survives the writer being wrong: his three
sentences with their times, and the three numbers above, each with a
command behind it.
