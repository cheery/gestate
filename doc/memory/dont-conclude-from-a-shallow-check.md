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

---

## The third failure mode, 2026-09-11: an oracle that cannot see its subject

Building the sideways carry for a `.notes` page
([[gestate-editor-latency]]'s neighbour — the driven window is the
instrument), two oracles in a row answered *no, it did not move* about
a page that had, and both answered without hedging.

* **Did the page's ground move between two photographs?**  The ground
  is 2078 pixels wide in a 1100-pixel window at every scroll, so it is
  cut at both edges and its bounding box reads `(0, 192, 1098, 566)`
  whatever the page does.  The oracle was measuring the *window*, and
  reported it as the page.
* **Did the whole window differ after forty more scroll events, to
  check the carry stops at the end?**  It does stop; the status bar
  carries a clock, so the window always differs, and the report said
  the page had run past its own last bar.

**Why this is the photograph's version of the first two:** a picture
oracle feels like the real world in a way a grep does not, so its
negative carries more authority than either.  Both were caught only
because a third reading — the pixels differenced inside the roll's own
band — disagreed, and because the *file* could be asked a question the
picture could not: a press took the note at bar 14, which nothing in
the run could reach unless the page had carried, and one line of the
file changed.

**How to apply:** before believing a driven run's negative, ask **what
in the picture would have to change for this to read differently**.  If
the answer is *nothing visible* — the thing is clipped, off-screen, or
the same colour as its neighbour — the oracle is blind and the run has
said nothing.  Prefer a signal that is *absent* in one state and
present in the other (the keyboard strip was at x 1 or gone entirely),
and where a gesture writes a file, let the file be the oracle: it
cannot be blind.  Related:
[[a-build-is-not-an-instrument-until-it-has-failed]],
[[test-what-a-person-would-do]].

---

## Seven in one day, and the rule they all wanted — 2026-09-11

The third failure mode above was written in the morning of 2026-09-11.
By that evening it had happened seven times in one sitting, always the
same way, and the count is the useful part: this is not a slip, it is
the **default** way an oracle gets written.

| the question asked | what it could not see |
|---|---|
| did the page's *ground* move? | it is wider than the window at every scroll |
| did the *window* differ? | the status bar has a clock |
| does `bench.state` move? | the probe had pinned it to a constant |
| did `sound` take? does `sounding_on` list it? | whether `Workbench.control` ever reads it |
| is the *keyboard* taller after a zoom? | magnifying about a corner pushed it off screen |
| does the picture differ two seconds later? | the playhead moves by itself |
| was a note written to the file? | whether the roll still drew any |

**The shape.**  Six of the seven measured a thing that was *true* and
upstream, beside, or later than the thing that decides.  Nothing lied;
the reading was simply not about the subject.  The seventh is worse and
worth its own line: the evidence was **in a photograph already taken**
and the assertion was made on something else in the same run.

**The two rules that would have caught all seven**, and they are cheap
enough to apply every time:

1. **Make the thing you are measuring the only thing that can move.**
   Stop the transport, crop to the band, close the clock, choose a
   signal that is *absent* in one state and *present* in the other —
   not one that merely changes.
2. **Ask what reads this, and did *that* change.**  A write, a return
   value, a data structure and a file are four ways of asking a
   question that is too early.  `Workbench.control` is what makes a
   sound; the drawn picture is what a person sees.  Assert on the
   consumer.

And when a negative comes back, before believing it: **what would have
to be different for this to read the other way?**  If the answer is
*nothing visible*, the oracle is blind and the run has said nothing.

Related: [[a-build-is-not-an-instrument-until-it-has-failed]],
[[test-what-a-person-would-do]], [[the-slow-part-was-never-the-test]].
