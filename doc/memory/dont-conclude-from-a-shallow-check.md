---
name: dont-conclude-from-a-shallow-check
description: "Henri's correction — verify before concluding; a guessed-at check that comes back empty is not evidence of absence"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cebbf1e2-5452-42ec-90ea-75af1454a293
  modified: 2026-08-16T11:04:03.512Z
---

Henri, 2026-08-15: *"You're sometimes really quick to make conclusions
that do not hold. That's why I still have to ask a question to solve
problems."*

The occasion: looking for `editing.webm`, I ran `ls ~/*.webm
~/Videos/*.webm`, got nothing, and announced the file was gone — then
re-encoded a 106 MB **lossy gif** three times because I believed my own
negative. His machine is Finnish: the file was in
`~/Videot/Näyttötallennevideot/`. One `find ~ -name "editing.webm"`
would have found it in a second.

**Why:** an empty result from a check I invented is evidence about the
*check*, not about the world — and acting on it wastes the expensive
kind of effort, because everything built downstream inherits the wrong
premise. His whole method (see [[test-what-a-person-would-do]]) is that
the question has to be asked of the thing itself.

**How to apply:** before saying *"there is no X"*, ask whether the
search could have missed it — guessed paths, English names on a
Finnish machine, one grep pattern, one directory. Prefer `find`/`rg`
over a guessed path. Where a negative result would change the plan,
say what was actually checked (*"no `*.webm` under `~` or
`~/Videos`"*) rather than the conclusion, and let him correct the
search cheaply. This is the same discipline as
[[gestate-testing-standard]], pointed at my own claims instead of the
code's.

---

## The second failure mode, 2026-08-16: a check that answers the *neighbouring* question

Three in one afternoon, during the hardening work ([[gestate-hardening]]):

* `systemctl is-enabled ufw` → `enabled`. That reports whether the
  **unit starts at boot**, not whether the firewall is up. `ufw status
  verbose` said `inactive`, and had all along. I raised "port 25 is
  exposed" on good evidence, **withdrew it** on the strength of the
  wrong command, then had to reinstate it. *The withdrawal was the
  error.*
* `systemd-run --user -p ProtectHome=tmpfs -p PrivateNetwork=yes …`
  started fine, and I reported "eight of eight supported". It had
  **parsed** every property and **applied** none — `cat ~/.ssh/id_rsa`
  printed the key inside the supposed sandbox. The probe tested a
  parser, not a fence.
* `apt remove kdeconnect` closes port 1717. Port 1716 belongs to
  **GSConnect** — a different program with a similar name.

**Why this one is worse than the empty-search case:** a shallow search
returns nothing and at least *feels* inconclusive. A neighbouring check
returns a confident green. It carries the authority of a real
verification while answering a question nobody asked.

**How to apply:** verify with a **different command than the one that
did the work**, and prefer one that observes the *effect* rather than
the *configuration*. Not "did systemd accept the flag" but "read the
key inside the sandbox". Not "is the unit enabled" but "is the firewall
filtering". When a check must grade something that could have escaped,
run it from **outside** the thing being graded — the escape probe in
`tools/sandbox.sh --check` looks for the leaked file from the host, not
from within the sandbox. And when I withdraw an earlier finding, hold
the withdrawal to the same standard as the finding: I was right the
first time and talked myself out of it.
