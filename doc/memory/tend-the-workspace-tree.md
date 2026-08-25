---
name: tend-the-workspace-tree
description: "~/tend, started 2026-08-24 at Henri's word, is the second tree run by this method and the first the audit was pointed at — the workspace over Linux where sessions and programs get a budget, a grant and a lifecycle; he decides whether to keep it"
metadata:
  type: project
---

**`~/tend` exists since 2026-08-24.**  Henri: *"lets try it, and let me
decide whether to keep it."*  Then: *"tend it is, start it."*  A
separate repository, not a directory of this one, and the reason is
`card:work-environment-ai.md`'s own line: *the enforcement boundary
must live outside the session's write access or it is decoration.*  A
gestate session can edit anything in gestate, including its fence; it
cannot edit `~/tend`, and that is the point of the place.

**What it is for.**  The workspace half of his next-project notes — the
eight lines that need a runtime and no kernel: pull-launch, a state
network, config recorded on the node, loud errors, crash-not-hang,
designed for AI use.  The OS half (three lines) and the language half
(gestate's own milestone, [[the-language-goal]]) are not it.  The
open decision on the card was taken on the week's evidence: **sessions
first** — every measured defect that week was session-shaped.

**Day one, measured — and the trajectory, not the snapshot, is the
fact.**  `python tools/seedaudit.py ~/tend` at three points of
2026-08-24: **2 of 10** pieces at the first commit (`bbf559b`, 07:16),
**4** by 07:39, **6** by the last commit of the day — unbacked 1 → 3 →
2, unkept promises 3 → 2 → 1.  Re-measure any past point with
`git -C ~/tend archive <sha> | tar -x -C /tmp/x && python
tools/seedaudit.py /tmp/x`.  Still exit 1, still red on purpose: the
audit says what is unmet and a piece arrives when something needs it.
What travelled on day one: `test/test_board.py` whole, named as
borrowed, and the card with its `because`; by evening also the sitting
limit, the pre-commit hook, `toolbox.sh`, and `kaizen.sh` — which Henri
corrected four times in an hour.  What did not: any prose.

**Two things the audit's foreign run found that its home run cannot.**
Its one remaining "unkept promise" against tend is `doc/instruments.md`
— *a document tend never promised* — which is gestate's `CAPPED` list
encoding this tree's accidents as another tree's requirements, exactly
as tend's own shelved `rules-and-memory` card predicted before it
was run.  And `tools/leash.sh` names two different things in the two trees:
the restraint-integrity check here, the per-invocation budget runner
there.  A mechanism travelling under that name will find it taken.

**2026-08-25 — the fence card, written from outside.**  Re-running the
audit found one absence on no card, and `~/tend/board/README.md`'s claim
that every absence was carded was false by that one.  Henri asked for tend's `fence`
card and it was written *by a gestate session* — the card
says so in its own first section, because a session from outside the
boundary writing the card about the boundary is worth recording, and
the only thing that made it legitimate was that he opened it in words
for one named thing.  The card splits the piece: the **integrity half**
has a caller today (the deny-list is the whole restraint and nothing
reads it back — gestate answers this with `tools/leash.sh` on
`SessionStart`), the **blast-radius half** does not (nothing there runs
foreign code yet, so `manifesto.md` rule 1 says not yet).  What it owes
first is a measurement, not a build: try to edit the deny-list from
inside a tend session by each route and write down which ones the
harness stops.

**How to apply.**  `~/tend` has its own board and its own
`AGENTS.md`; a session there reads *that* README.  Its suite cannot be
run from a gestate session — the fence binds only this repository —
so Henri runs it, or a session started in `~/tend` does.  Whether it
is kept is his; do not build in it from here beyond what he asks.  The
gestate copy of the card stays in `board/later/` and points there.
See [[the-tree-meets-people-on-pull]], [[deriving-strips-the-payment]].
