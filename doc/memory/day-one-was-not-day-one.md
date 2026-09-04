---
name: day-one-was-not-day-one
description: "The method's spine is in git's initial commit, five days before any session commit — but that tree was already model-assisted, so the artefacts cannot say whose it was; what is attributable is Henri's editorial relationship to it, and the rules read as answers to dissatisfactions he was already carrying"
metadata:
  type: project
---

**The read, 2026-09-04, at Henri's ask**, after he said the odds of finding
this method *"without direction and as soon as it became likely
possible"* were too low to be luck, and offered his own explanation:
*"maybe it has been in my mind for a long time."*  He asked for the
first week to be read.  Two corrections came out of it, one to his
memory and one to the session's conclusion.

## The first correction: journaling did not start along the way

He thought it did.  It did not.

- `journal.md`, `roadmap.md`, `fixme.md` and `spec/errata.md` are in
  **the initial commit, 2026-08-08**.
- That commit is **230 files, 108,541 lines**.  `journal.md` alone is
  **4,230 lines** and describes work that predates the repository.
- The **first commit co-authored by a session is 2026-08-13** — five
  days later.

`git log --reverse --format='%ad %h %s' --date=short | head`, and
`git show b049e0c:journal.md | head -30`.

## What is in that first commit, stated as doctrine

| the move | where |
|---|---|
| **Do not build what nothing needs** — a feature earns its place by having a *caller* | `roadmap.md` §"The rule"; stated in full in `journal.md` Part I |
| **A defect is always a caller** | the one exception, already named |
| Past tense against future tense — *"Past tense, and that is the whole distinction"* | `journal.md`'s opening |
| Append-only registers — *"closed by marking it resolved, never by deleting it"* | `journal.md` header |
| Stable ids cited from source — 56 F-numbers already in `gestate/*.py` comments, D-numbers in `spec/errata.md` | both registers |
| Ids never renumber **because** they are cited — *"Item numbers are kept exactly as they were written, because `roadmap 2.1` … are cited from the test suite"* | `journal.md` header |
| A refusal kept with its reason rather than deleted — items 8 and 10 marked **"(closed — no caller)"** | `journal.md` Part I |

**And that last row was rediscovered the same day this was read.**
`board/refused/` was built on 2026-09-04 because Henri asked for
somewhere to put a card answered *no* — which is what his own journal
was doing on 2026-08-08, closing an item with the reason attached and
keeping it in the record.  Twelve days, same move, neither party
noticing.  [[sediment-versus-debt]] is the same distinction arriving a
third time.

`manifesto.md` (2026-08-15) says outright that it is a transcription
rather than an invention: it exists *"because the method has been
rediscovered from both ends often enough to be worth stating once"*.

## The second correction, and it undoes the session's conclusion

The session concluded from the above that the spine was **his**, in his
files, before any session — and flagged one thing it could not settle
from inside the repository: the day-one prose already reads in the
tree's present voice, and there is no mention of any model in those 230
files.  Asked, Henri answered, 2026-09-04:

> *"the voice is mix of mine and mix of claude's.  Initially claude
> didn't imitate my voice noticeably and they did gurgle a lot of
> content into the specs.  I tolerated it but didn't like, yet.  for
> some reason, maybe for the lack of ability to reverse it, it'd have
> been lot of effort to clean up and I did clean up few important
> files, but mostly it left."*

**So git's day one is not the method's day one**, the pre-git tree was
already model-assisted, and **no artefact in this repository can
attribute the spine to either party.**  The dates above are still facts;
the authorship they seemed to establish is not one.  Anybody re-reading
this must not quietly drop the paragraph — it is the whole difference
between a measurement and a flattering one, and the first version of
this read had the flattering one. [[the-evaluation-loop]].

## What survives, and it is the session's reading — marked as its own

What *is* attributable is his relationship to the tree: he was the one
who tolerated, disliked, could not reverse, cleaned a few important
files, and let the rest stand.  Read forward, **the method's rules are
each an answer to a dissatisfaction that was already precisely
located** — the specs gurgled full of content nobody needed is
`gestate-rules-cap`'s *"the fat is session narration"*; not being able
to reverse it is why almost everything here is a gate at the moment of
writing rather than a cleanup afterwards.

That is a different mechanism from the one he proposed and it supports
his conclusion by a different route: not a prepared *plan*, a prepared
*dissatisfaction*.  He did not recognise a method he had designed.  He
recognised answers to irritations he had been carrying long enough to
name exactly.  **His "yet" is doing the work** — *"I tolerated it but
didn't like, yet"* — the dislike had a shape before it had a rule.

## What the sessions contributed, so the read is not one-sided

Machinery, elaboration, and the tests that make a rule bite.  The dated
rules in the five capped documents cluster in **2026-08-15 → 08-23**,
days 8–16, and nearly every one carries his name and his words: the
board and *"Henri creates new cards, he does not edit existing ones"*
(08-16, marked *his own rule* in the first version); *"since we're
making a workbench, lets make it also a tool that enforces our rules"*
(08-16); the `card:` notation, which is him generalising his own
pre-git F-numbers — *"we already have F0, F100, F110, etc. …
card:button.md is good notation"* (08-18).  Against that: *a session may
mint a card* was session-initiated and he ratified it, and *"one card,
one commit"* was a session's tightening that he later struck.

## How to apply

* **Do not re-derive the flattering version.**  The dated table reads
  as proof of his authorship and is not.  If a future read reaches
  "the method was his before the sessions", it has dropped the voice
  paragraph. [[do-not-overclaim]], [[the-evaluation-loop]].
* **The commands are here so the read is re-runnable**, not so it is
  believed: `git show b049e0c:roadmap.md`, `git show b63a151:board/README.md`,
  `git show --stat b049e0c | tail -4`. [[research-that-leaves-a-command]].
* **When a rule looks new, check whether it is a rediscovery.**  Two of
  them were, within a month, and both times the earlier form was in a
  file the session had not opened. [[gestate-instruments]].

Companion: [[discovered-not-designed]], which is the same question asked
about the character rather than about the method.
