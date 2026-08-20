---
name: gestate-work-laptop
description: Henri installed gestate on his work laptop (Ubuntu 26.04 LTS) on 2026-08-17 — a second machine that now exercises the install path
metadata: 
  node_type: memory
  type: project
  originSessionId: b6183261-d60e-4c47-af63-3802f13606e7
  modified: 2026-08-17T13:13:06.595Z
---

As of 2026-08-17 gestate runs on **two** machines: the home laptop and a
work laptop freshly installed with **Ubuntu 26.04 LTS**. *"I'm also
going to need it there."*

**Why:** the second machine is the only thing that has ever tested
`doc/install.md` as written, rather than the accumulated state of the
home machine. It found F148 (the taskbar's icon) within a day, because
the home machine had a hand-written `.desktop` file nobody remembered
writing and the new one had nothing.

**How to apply:** when something looks wrong "only on the new laptop",
suspect undeclared local state on the home machine before suspecting
the distro — ask what `~/.local/share` holds there. And treat a fresh
install as the honest reading of the install docs: it is worth more
than a re-read of them. See [[gestate-verify-workflow]]; the
personal/work boundary in [[henri-cofounder-separation]] is his call
and he has made it.
