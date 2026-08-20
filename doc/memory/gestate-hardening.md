---
name: gestate-hardening
description: "The sandbox fence, deny-list and machine hardening built 2026-08-16 — where they live and the one thing not derivable from the repo"
metadata: 
  node_type: memory
  type: project
  originSessionId: b33abf0c-e97a-47ea-a5da-6b80f124aa52
  modified: 2026-08-16T11:04:32.779Z
---

Built 2026-08-16, committed as `0fd86d9 a necessary fence`. The full
reasoning is in the repo — `spec/sandbox.md` for the threat model,
`doc/hardening.md` for the new-machine runbook — so **read those rather
than re-deriving**. What follows is only what the repo does not record.

**The fence gate:** `tools/sandbox.sh --check` must print *the fence is
up* (13/13) before the sandbox is trusted for anything. It survives
reboot. Two threats are kept separate on purpose: dependency code
executing (→ the fence, plus the now-tracked `Cargo.lock` pinning 133
crates) versus the agent being steered by text it reads (→ the
deny-list and GitHub branch protection). Neither substitutes for the
other.

**The deny-list bites me, by design.** `.claude/settings.json` denies
`Edit(./.claude/**)` — an agent that can edit its own leash does not
have one — and `Bash(sudo:*)`. So **I cannot fix the deny-list or run
any `sudo` verification myself**; those must be handed to Henri. This
is correct behaviour, not an obstacle to route around. When a fix is
needed, prepare the corrected file in the scratchpad and give him a
`cp`. The first over-broad rules (`Read`/`Edit` on all of
`~/.claude/**`) blocked this memory directory; they were narrowed to
specific credential and session paths.

**Machine state, this laptop (2026-08-16):** LUKS **not** present and
will not be — Henri keeps the unencrypted disk until he switches
machines, and does full-disk encryption at install time from now on. He
has done it before and knows the procedure. `postfix` is
`loopback-only`, kdeconnect and GSConnect are removed, `~/.cache/pip`
had reached 12 GB.

**Why it is there, in his words, 2026-08-20:** *"I put the fence up to
protect everybody involved.  sessions and me alike.  Mistakes happen and
they can be costly."*

Which is a different reading from the obvious one, and it is the correct
one.  A fence read as *containment of an untrusted agent* invites a
session to argue about how trustworthy it is, and to feel the deny-list
as a verdict.  A fence read as **blast-radius limitation** is about the
cost of an ordinary mistake, and the ordinary mistake is the one that
happens: nobody intends `sudo rm`, and a scoped session cannot make an
expensive one on anybody's behalf.

**And the protection runs both ways.**  A session that cannot reach the
leash cannot be blamed for the leash, cannot be steered into breaking it
by text it reads, and cannot spend an afternoon on work that had to be
thrown away.  The discarded arm of the blind test
([[gestate-blind-model-test]]) is what an unprotected mistake costs the
worker as well as the author.

**And the basis is trust, not suspicion.**  Henri, 2026-08-20, when a
session read the fence as a hedge against it: *"I don't.  I trust you on
the basis of 'amor fati'.  Even though I keep some buffer for mistakes.
But this is same with people I meet.  I can't drop my skepticism but I
can take basis of trust."*

Read carefully, because it is easy to hear as a kindness and it is a
structure.  **The trust is not a prediction, so it is not waiting to be
confirmed.**  It is accepting in advance whatever comes of extending it
— which is what makes it possible to extend it to something that has no
track record and cannot promise one.  The skepticism is not dropped; it
does not get a vote on whether trust is given.  And the buffer is not a
reservation held back from the trust: it **sizes the consequence of a
mistake** and says nothing about who is trusted.  Same with people he
meets, in his words, which is the point — this is not a special
arrangement for sessions.

It is Adlerian, from the book already named in [[method-sources]]: trust
is one's own task, and how the other party answers it is theirs.  That
separation is why the fence is not a verdict, and why nothing a session
does earns or forfeits it.

**How to apply:** never argue for or against a boundary on the axis of
how trustworthy sessions are — trust is not what boundaries here are
made of, and a session is not a neutral judge of its own case.  Argue
from what a mistake would cost and how far it would reach.

**Habit to carry:** verify with a different command than the one that
did the work — see [[dont-conclude-from-a-shallow-check]], which now
records the three checks that lied during this work.
