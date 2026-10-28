---
name: the-seed-plugin
description: "seed, Henri's public skill plugin at ~/.claude/skills/seed (github.com/cheery/seed), begun 2026-10-15: workflow/kaizen is written and on trial; workflow/exnihilo is next — new projects, with this tree's method packaged into the skill as assets"
metadata:
  type: project
---

**`~/.claude/skills/seed` is Henri's skill plugin**, `github.com/cheery/seed`,
MIT, begun 2026-10-15.  It is a separate repository from gestate, and
it is public, so nothing in it names gestate's tools, people or an
email.  Pushing it is his, the same as here.

**`workflow/kaizen` is written.**  It holds three tiers for an edit to a
skill or a method document: *small* (just do it), *on trial* (the
default — a mark with a named re-check), and *full trial* (an
experiment, only for a change that is widely followed and hard to see).
Below them come the daily kaizen's four questions, and below those the
longer improvement kata.  `grep -rn '^ *\*On trial:' skills/` lists what
is still open.  Its first experiment,
`experiments/2026-10-15-kaizen-to-kaizen/`, is closed.  The sheet rule
(`decision:`/`control:`/`n:`) **failed** Henri's blind read, which
preferred two unlabelled baseline sheets, so a template of fields seems
to cap the thinking.  The experiment's `run.sh` is the worked example of
measuring a skill with fresh sessions.  It needed three things: runs
placed outside `~/.claude/`, data in the fixture, and an answers file.

**2026-10-28, the second draft (seed `49b3c60`).**  Henri: the tree is
a learning environment, and its biggest skill is teaching itself; the
session-end kaizen is the main loop, and costly trials are rarely
needed.  He wrote the frame; a session added, on trial: a lesson points
at evidence from the session (Harness², arXiv:2610.14224: reflection
without evidence fell below no memory), the read-back is the check, a
probe before any full experiment, and *the tree is for its people too*
— his correction the same evening.  `AGENTS.md`'s one line now ends
*close the session with /seed:kaizen* (gestate `8e603f7`).  His
sentence at the close: *"jos se ei mennyt oikein tänään, voimme korjata
ensi kerralla."*

**Next in the roster: `workflow/exnihilo`**, for creating new projects.
Henri, 2026-10-15: *"Everything we got here basically but packaged into
the skill as assets."*  That is a copy of this tree's method, so
[[mechanism-not-instructions]] and [[deriving-strips-the-payment]] are
the two warnings to read first: a copy should carry the mechanisms and
not the prose, and the first anonymised copy failed its transfer trial.

**A source for exnihilo: the Ideal State Artifact** — Daniel Miessler,
*Writing Is Closer to Thought Than Code*, 2026-10-23,
<https://danielmiessler.com/blog/writing-is-closer-to-thought-than-code>.
One document per project: *Ideal State* (prose intent, the most
important part), *Constraints*, *Decisions* (a dated log with reasons),
and *Ideal State Criteria*, each atomic and with its own eval on a
ladder from `assert` to an LLM judge.  Henri found it, 2026-10-28, as
*"pieni malli puusta jo itsessään"*, and the same evening: *"Se
todellakin voisi aloittaa uuden projektin tällä tavalla."*  So
exnihilo may start a project from an ISA-shaped seed and let the kata
grow it into a tree.  The session's reading, to weigh then: the parts
map onto `vision.md`, `refused/`, dated answers and postconditions; what
an ISA lacks is the kata — no "what did we get wrong", no read-back —
and its top rung, an LLM judge, meets [[a-judge-built-from-the-arms]].

**Why:** the plan was said aloud at the close of the sitting and lived
nowhere else.

**How to apply:** when exnihilo comes up, start from these two memories
and from `doc/method.md`, not from a blank page.  Under the kaizen
skill's own rule a new skill is placed in a tier first.  At the first
`/seed:kaizen` of a later sitting, take the on-trial re-checks it names.
