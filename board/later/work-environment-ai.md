# work-environment-ai — sessions and programs run on this machine with no budget, no grant and no lifecycle

    status   shelved — 2026-08-19
    because  "we are missing a way to work with each other" (vision.md,
             2026-08-16) — sessions and programs run on this machine
             with no budget, no grant and no lifecycle; one already
             degraded the machine being listened on (2026-08-18)
             before anybody saw it, and it was diagnosed as hardware
             first
    asked    Henri, 2026-08-19 — "work environment+AI, composed with
             later goal to implement OS into it"
    blocked  a decision only Henri can make — §"The open decision"
    see      vision.md §"Gestate as a lean vehicle" — the `because`
             spec/author.md — the review volume this is downstream of
             board/README.md §"Question it into existence" — how the
             sixteen-item list became one card
             card:working-standard.md, card:project-seed.md — the
             method half; this is the vessel half

**Written outside the tree** by a session, from a conversation on
2026-08-19, and brought in on 2026-08-20 at Henri's ask.  Everything in
his words is marked so; the rest is the session's, and by the
elaboration rule it is **suspected** — including the architecture below,
which is the part a reader is most likely to trust and the part most
likely to be wrong.

## The ask, verbatim

> C option. AI native sounds like sense. But there's also that "try
> things out" -angle and self-reliance on concepts I gave. I know that
> you sessions have odd notion of time. Your ten years is two months
> realtime. So I think that work environment+AI, composed with later
> goal to implement OS into it would be the proposal.

The original list (2026-08-19, Finnish, sixteen items) is the property
sheet this card descends from: easy install and test, secure by design,
verified by types and model checkers, config recorded in the program
node, pull-based reconfiguration, decentralized versioning, Linux
compatibility, state persistence, crash-don't-hang, compiler
localization, hard to attack, AI-native, pull lifecycle, no silent
errors, own language (per arXiv:1507.05762), encrypted disk;
bootstrapped in Python and Rust.

## How the reading was chosen

The list as written was not a card: nearly every bullet named a fix and
none named a problem, which fails the board's first gate.  Four readings
were offered, each with what would kill it:

* **A. A real OS, kernel up** — killed by `vision.md`'s *"any project
  must not consume the person leading it"*, by one reviewer, and by the
  prior-art graveyard (Fuchsia: a decade, hundreds of engineers; Midori:
  shipped nothing).
* **B. A Linux distro with these properties** — Nix + CRIU + capability
  broker on a stock kernel.  Survives everything except *secure from the
  kernel up*; the TCB stays Linux, mitigated.
* **C. Gestate's method applied to a working environment** — sealed,
  testable, state-carrying, capability-scoped execution for AI-written
  programs.  Killed only if the goal is genuinely to boot metal.
* **D. A research programme, not a product** — killed by *"my friend
  could use it as well"*.

**Henri chose C, with the OS as a later goal layered on top.**  Which
gives the card a `because` traceable to `vision.md` without strain:
*"I'd like to use gestate as a vehicle to find out how to utilise AI
well… What we are missing is not better AI or higher capacity.  We are
missing a way to work with each other."*

## Two corrections carried from the review

**The time argument is half right.**  Sessions compress *production* —
typing is nearly free, and proof engineering that once took twenty
person-years would go much faster.  What does not compress is the
author's share: `spec/author.md` already measured 270 commits in nine
days outrunning review, and wrong-direction risk lives in the seams —
names, interfaces, contracts, refusals — which no session accelerates.
The consumption rule binds attention, not calendar.  Environment-first
is right partly because it keeps the seam count low enough for one
reviewer.

**Self-reliance on concepts is fine; self-reliance on lessons is
expensive.**  Rebuild the concepts; read the post-mortems first.  Why
Nix chose content addressing, why EROS and Phantom found that
persistence resurrects bugs, why every powerbox looks the same.  A day
of reading against months of rediscovery.  Borrow the scars, not the
code.

## The architecture, in dependency order

*Suspected, as above.*  Userspace on Linux, inside or beside gestate,
bootstrapped in Python and Rust.

**1. The node.**  A program is a content-addressed bundle: code plus its
configuration recorded in the node, so pull-reconfiguration is
re-fetching by identity, and decentralization falls out because identity
is the hash.  Install = fetch; test = run the node's own suite; a node
carrying no suite is refused — *"won't ever be untested"* applied at the
boundary.

**2. The supervisor.**  Erlang semantics: a crash is fine, a hang is a
crash (timeout), a crash-loop gets backoff and an andon light, never
silence.  Pull lifecycle: a node nobody pulls is stopped.  The measured
caller is in this tree — the 2026-08-18 audio-crackle incident, where a
session running the suite, cargo, two X servers and a dozen polling
loops degraded the machine being listened on.  A defect is always a
caller.

**3. The capability broker.**  No ambient authority; a node gets file
and network handles only by explicit grant, and the picker click *is*
the grant (the powerbox pattern: Genode, Capsicum, Fuchsia).  This
answers open problem 1 below, which turns out not to be an open problem
but the first architecture decision.  It is also the entire content of
*AI-native*: **a session is a principal** — scoped capabilities, a
CPU/IO/audio budget, everything observable and replayable.  Blast radius
equals grant.  The one genuinely novel bullet on the original list.

**4. State — explicit, not memory images.**  Checkpoint/restore
persistence collides with two vision lines: *"won't trap your work —
plain files you can read without it"*, and *"won't ever do anything
unexpected silently"*.  A resurrected image resurrects yesterday's bug
and yesterday's config without a trace (EROS and Phantom both hit this),
and a memory image is a dump full of secrets under the encryption
bullet.  Instead: a node serializes its state explicitly to a plain,
inspectable file, and *opens where it left off* means restoring from
that.  CRIU stays in the pocket as a later latency optimisation for
pull-shutdown, not as the state model.

**The OS-later discipline.**  The environment's contract — node format,
capability verbs, supervisor protocol — lives in `spec/`, kept narrow,
so what is underneath stays replaceable.  *Implement an OS into it* then
means swapping Linux out from under a contract that already has users.
If the contract sprawls, the OS phase is dead regardless of intent.

**The language is deferred, deliberately.**  The environment needs none
of it, gestate already has a language, and the LP-IR paper
(arXiv:1507.05762 — deterministic, single-moded logic programs as a
compilation IR; note it designs an IR, not a surface language) becomes
relevant only at the OS phase, if ever.

## Answers to the original open problems

1. **User data against programs** — capabilities plus powerbox, decided
   by piece 3 above.  Everything else is downstream of it.
2. **Program protection and install** — content-addressed, signed store;
   pull = fetch by hash.  A solved problem, of the Nix/OSTree shape.
3. **Speed against immediate shutdown** — answered by explicit state:
   shutdown = serialize, launch = restore, and the question collapses to
   restore latency, which is measurable (CRIU and Firecracker-class
   restores run roughly 100–300 ms).

## The open decision

*Mediation order.*  The broker and supervisor govern **principals** —
things that act.  This machine has two kinds: **sessions**, and
**programs** (gestate nodes: instruments, pieces, tools a person runs).
Enforcement cannot be built for both at once; one goes first and the
other runs ungoverned for months.

**Sessions first** — the broker's first subject is the session itself:
every tool call (cargo, the suite, X servers, polling loops, file
writes) runs through the runner with a budget and a grant, visible in
the andon.

* *For:* the caller already exists — the audio-crackle incident and the
  review volume are both session-shaped defects; immediate relief on
  what hurts now; it is the novel *AI-native* piece; and a grant model
  designed against the messiest workload trivially covers programs.
* *Against:* hardest case first, so the first version is wrong in more
  ways before it is right; nothing a gestate user meets improves for
  months, which the board's impact ordering demotes; and the governed
  party would be building its own cage — **the enforcement boundary must
  live outside the session's write access or it is decoration.**
  *Partly answered already, 2026-08-20:* `tools/sandbox.sh`'s deny-list
  blocks a session's own `sudo` and its own leash, and `.claude/` is
  outside a session's write access — enforcement outside the governed
  party's reach, working on this machine today (`spec/sandbox.md`).  So
  the cage-builder problem is not unsolved here; it is unsolved *at this
  granularity*.

**Programs first** — the broker mediates gestate nodes: an instrument
gets audio-out and its own state file, nothing else.  Sessions stay
ungoverned.

* *For:* the easy case, with narrow predictable needs, so a clean small
  capability model arrives fast; it is exactly the OS-later contract
  (nodes, grants, pull lifecycle); and a person using gestate feels it,
  which scores higher on the board's impact ordering.
* *Against:* it solves a problem that has not happened — no node has
  hurt anybody and sessions have, twice, measured; the vocabulary risks
  being too small for sessions, forcing a redo; and the actual risk, an
  ungoverned agent with the whole tree writable, continues meanwhile.

### It is open, and it is to be decided by evidence

*Henri, 2026-08-20: the order is an open question and should be settled
by measurement, not by argument.*

A session did recommend sessions-first here, on the board's rule that a
defect is always a caller.  **That recommendation is withdrawn as a
basis for deciding**, for a reason worth keeping rather than tidying
away: the session making it **is the governed party**.  A session's read
on how far it should be trusted is not neutral in either direction — it
can be self-serving, and it can as easily be self-flagellating, which
reads as humility and is exactly as useless as evidence.  The argument
stays on the card because it is a real argument; it is no longer the
answer.

And when the question was put plainly — *is this for my safety?* — the
three things bundled under "sessions first" came apart, which is itself
the finding:

* **the machine is shared** — the audio-crackle incident, measured;
* **you cannot see what happened** — 270 commits in nine days outrunning
  review, measured;
* **containment** — scoped capability, and **no incident behind it.**

The first two are the callers, and they are what settles the **order**.

**But containment is not the same kind of question, and Henri corrected
the framing on 2026-08-20:** *"I put the fence up to protect everybody
involved.  sessions and me alike.  Mistakes happen and they can be
costly."*  So it is not a defence against a session's intent — it is
blast-radius limitation against an ordinary mistake, and it protects the
session as much as the author: work that cannot be reached cannot be
destroyed, and a boundary a session cannot cross is one it cannot be
blamed for or steered into crossing.

Which means **incident-counting is the wrong instrument for that third
piece.**  What it guards is the rare expensive mistake, and counting
rare events after the fact is a measurement that arrives too late by
construction.  The right question for containment is not *has it
happened* but *how far would it reach* — the same question already
answered once at a coarser grain by `tools/sandbox.sh`.  Evidence
settles the order; blast radius settles the scope.

### What would decide it

Cheap, in roughly this order, and none of it needs the broker built:

**1. Count the incidents, both kinds.**  `fixme.md` and `journal.md`
already hold them.  How many measured incidents were session-shaped, and
how many program-shaped?  **And the caveat is half the measurement:** if
nothing in this tree would have *seen* a program misbehaving, a zero is
a fact about the instruments and not about the programs — see
`journal.md` §"Kaizen, 2026-08-19 — the instruments found everything and
the tests found none of it".  A count with no observer behind it decides
nothing.

**2. Try the program vocabulary on the session's needs, on paper.**
Write the grants a real gestate node wants — audio out, its own state
file — and then the grants a real session wants: spawn `cargo`, write
the tree, open an X display, ring the sound card.  If the node
vocabulary cannot spell the session's list, programs-first forces the
redo its *Against* column names, and that is established in an afternoon
with no code.

**3. Then it may not be a decision at all.**  The day-one slice below is
reversible and measurable, and by `doc/memory/decisions-arrive-shaped.md`
that makes it an **experiment**, not a decision: build it for one
principal, see whether it catches the case that already happened, keep
or revert.  A reversible choice with a cheap measurement should never
cost the author a decision.

**Day one, whichever way it goes**, so that this is not a decision
wearing a card forever: build the supervised, budgeted runner for one
principal's invocations — for a session, that is the suite, `cargo` and
the polling loops — visible in the andon.  Smallest slice, real caller;
capabilities, nodes and pull bolt onto it later.
