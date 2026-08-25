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

**Corrected by Henri on 2026-08-25:** *"They is working on both sessions
and programs first -approach in parallel until we find out which one is
working solution."*  So it is no longer a decision that was taken; it is
**two arms running at once**, and the choice waits on evidence from
both.  Which is set-based rather than point-based — `manifesto.md`
§"Set-based, not point-based" — and it means a session here must not
quote *sessions first* as settled, or write it into a card's `because`.

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

**2026-08-25 — the first mechanism to travel the other way.**  Tend
built `test/test_selfmatch.py` from *this* tree's 2026-08-18 post-mortem
— a `pgrep -f` matching its own command line — and at Henri's ask it came
back as gestate's `test/test_selfmatch.py`, gate fifteen.  So the traffic
is not one-way: a defect here paid for a mechanism there, and the
mechanism returned once it existed.  What travelled was the file, named
as borrowed; the prose stayed put, the same rule as the other direction.
The occasion was a third instance of the same bug, in a session's own
shell that morning, which is also why the gate's own docstring says what
it cannot reach: a pattern typed into a shell rather than written into
the tree.

**2026-08-25 — the leash is usable, and the ledger is one desk.**
`~/tend/tools/leash.sh` runs one invocation under a wall and CPU budget
and appends a line to `~/.local/state/tend/leash.log`.  A gestate
session's first outside use of it was the full suite beside a working
tend session: `-t 3600 -c 200`, two of the four cores, 3464 passed and
27 skipped.  **The log is shared** — the same one-desk arrangement the
sitting limit's twins already have on this machine, so *when* the
machine was busy and *what* asked for it is answerable from one file
whichever tree asked.

*How to use it from here, confirmed by tend the same day:* **shell
discipline, not a `tools/` import** — nothing in gestate may depend on
`~/tend`, or a fresh clone on another machine is broken (`vision.md`);
**a copy with a header if it earns one**, the way `tools/limit.sh`
travelled, with the twin-maintenance debt written on it; and **the hook
is Henri's**, because hook config is enforcement.  A leash a session
chooses to invoke is an instrument and not a fence, and what makes it
worth invoking is the ledger rather than the restraint.

*Tend has a card for the enforcing half — `grant`, opened 2026-08-25 —
and this session's three incidents of that morning are its caller: a
`timeout` shorter than the job it bounded, a killed suite whose fenced
`pytest` survived as an orphan, and readings taken under that load and
written into a document as a correction.  When `grant` is worked the
first run is a gestate build under the leash, and that ledger line is
the demonstration owed.*

**One defect in it, found and then confirmed from here.**  The ledger's
`cpu=` column read **1.3 s** for a 1504-second CPU-bound suite.  Tend
fixed the first cause the same day (`367c531`, scope mode reads the
cgroup's own `CPUUsageNSec` instead of `times`) and asked gestate for
the confirming run, because a scope cannot be made inside `bwrap` and a
fenced tend session always degrades to plain.

**It still reads `?`, deterministically** — three runs of a known load,
two children burning 12 s of CPU each under `-c 200`: wall 12, 13, 12 s,
exit 0, budget applied, `cpu=?s` every time.  Re-run it with
`~/tend/tools/leash.sh -t 120 -c 200 -- sh burn.sh`.

**And the cause is not the one the fix assumed.**  Measured on systemd
255 (255.4-1ubuntu8.17): `systemctl --user show <unit> -p CPUUsageNSec
--value` gives `[not set]` once the payload has exited — for a scope
*and* for a `--wait` service, while the unit still exists.  Reading
before the stop is not the missing piece; the counter is gone by then.

**What does carry it is the journal, and only for a service.**  A
`--wait` service's resources record has `CPU_USAGE_NSEC = 24034252000`
— 24.03 s for 12 s of wall on two cores, the arithmetic exactly — plus
the memory peak, and it is a structured field under a stable
`MESSAGE_ID=ae8f7b866b0347b9af31fe1c80b127c0`, so nothing has to parse
`"24.034s"`.  A **scope**, stopped and then read, has no resources
record at all.  So moving from `--scope` to a `--wait` service is right,
for a different reason than the race that was suspected — and the
orphan-reaping the scope was chosen for survives, because a service is a
cgroup too.  *Trap, paid for: `--wait` with `RemainAfterExit=yes` never
returns.*

**Until tend lands it: do not quote a `cpu=` figure from a `scope` line
in the shared log.**  A `plain` line's figure is `times` and is correct
there.

**How to apply.**  `~/tend` has its own board and its own
`AGENTS.md`; a session there reads *that* README.  Its suite cannot be
run from a gestate session — the fence binds only this repository —
so Henri runs it, or a session started in `~/tend` does.  Whether it
is kept is his; do not build in it from here beyond what he asks.  The
gestate copy of the card stays in `board/later/` and points there.
See [[the-tree-meets-people-on-pull]], [[deriving-strips-the-payment]].
