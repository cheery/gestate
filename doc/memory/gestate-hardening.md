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

**Habit to carry:** verify with a different command than the one that
did the work — see [[dont-conclude-from-a-shallow-check]], which now
records the three checks that lied during this work.
