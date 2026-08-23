# who-asked — every tool says who wanted it, and the suite refuses one that does not

    status   open
    because  a stranger's one-line question produced an instrument the
             same afternoon, and nothing in the tree would have caught
             the next one — the register that would is impossible to
             gate, and the artifact it produces is not
    asked    Henri, 2026-08-23 — "tätä varten voi tehdä kortin ... tee
             siitä portti kun suite on ajettu"
    see      tools/asked.py — the register and the command
             test/test_provenance.py — the gate and the ratchet
             spec/verification.md §"Coverage, and the question it cannot answer"
             doc/instruments.md §"The other standing rule: a number nobody asked for is a number nobody checks"

## Where this came from

2026-08-23.  Somebody outside the project asked Henri *"ihan
mielenkiinnosta, miten verifioit että kaikki koodi on testattua?"* and
he could not answer.  Going and looking found that nobody here had ever
measured it: 3,065 tests, roster poka-yokes refusing an untested *file*,
two engines held sample-for-sample — and no instrument that could name a
*line* no test had run.  `tools/covercount.py` existed by that evening.

**One sentence from a stranger produced a capability, and the tree had
no way to notice that this had happened.**  It is the second time: F162,
the placeholder in the front door that survived the author's own
fresh-laptop walk, came the same way.  Two in a fortnight, both cheap,
both invisible to every instrument on the bench.

## Why the obvious version is a trap

The obvious build is a register of questions from outside.  It fails,
and the reason is worth keeping because it rules out a whole family of
ideas: **nothing can enumerate the set of questions nobody asked yet.**
Every gate that holds on this board has the shape *this directory is
exactly this list* — and a list that cannot be enumerated cannot be
gated, so it fills once, ages, and becomes a diary.  `2e605b3`: *a
kaizen that asks for no mechanism is a diary.*

## What is enumerable

`tools/`.  Every tool exists because somebody wanted something, and who
that was is plain on the day it is written and a journal dig a
fortnight later.  So the stamp goes **on the artifact**, the way
`test_every_complaint_has_a_verdict` puts the verdict beside the `raise`
rather than in a file somebody sweeps:

    #: asked-by: Henri, 2026-08-23 — "tee siitä portti kun suite on ajettu"

Five verdicts, no default: `Henri`, `outside`, `a session`, `the tree`,
`unrecorded`.  A person's ask must quote the words.

**`a session` and `unrecorded` are legal, and that is the design.**  A
stamp that could only say *somebody asked* is a stamp every future
session writes and nobody means.  What the register is for is the shape
of the distribution — how much of this bench came from outside pressure,
how much from Henri, how much a session built because it could.  F169
generalised: *a number nobody asked for is a number nobody checks*, so
**a tool nobody asked for is a tool nobody runs.**

## The ratchet, which is the honest half

Every tool could be stamped `unrecorded` in ten minutes and the gate
would pass.  So the count is written into `test_provenance.py` and
checked both ways: it may fall, it may not rise, and it falls only when
somebody does the dig for one more tool.  Same discipline as `fixme.md`'s
header counting its own resolved entries.

## What is left, and what would settle each

The first pass stamped what the record already says — a commit body
quoting Henri, a docstring naming the ask, a card whose `asked` line
already carries the words.  **27 tools: 15 Henri, 1 outside, 11
unrecorded, 0 unstamped.**

Two things in that distribution are worth reading before the list.

**Nothing is stamped `a session`** — not because no session ever built
something on its own initiative, but because the record does not say so
for a single tool.  `unrecorded` and `a session` are different claims
and the first pass refused to turn one into the other.

**Ten of the eleven are from 2026-08-11 to 08-16**, the first week, before
any of this was written down.  The eleventh, `gapcheck.py` on 08-22, is
the one worth looking at first, because it is recent enough that the
answer is still in the journal.

    lagcheck.py  pcf.py  dialoglag.py  measure_canvas.py
    measure_editor.py  jukebox.py  stutter.py  toolbox.sh
    dragcheck.py  leash.sh  gapcheck.py

Each is one journal read away — `journal/2026-08.md` around the adding
commit, which `git log --diff-filter=A -- tools/<name>` names. The number
in `test_provenance.py` comes down as they land, one edit each.

## What this card does not claim

It does not catch the next stranger's question.  Nothing can.  What it
does is make the *provenance of capability* a checked property instead
of a thing a session happens to mention — so that a bench where nobody
asked for anything is visible as such, on a command, in one screen.
