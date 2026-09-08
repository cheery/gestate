# spec/roles/ — the briefs a session takes for one sitting

**A role is context, not a rule.**  It is a page a session is handed
at the start of a message — *"your role is spec/roles/reviewer.md,
\<request\>"* — that says what kind of reader it is today and what
that reader owes.  Nothing here is held by a gate, nothing is read
before work unasked, and the five rule documents (`spec/rules.md`)
stand whatever role is on: a role narrows what a session does with the
rules, it never loosens them.

**Why a directory and not a memory or a rule.**  `doc/memory/` is what
earlier sessions carried across and is loaded whole;
`doc/memory/weights-context-suite.md` says weights are for what a
model must know, context for what it must *currently* obey, suite for
what must be guaranteed.  A role is the middle kind and only for the
sitting that asked for it — the reviewer's brief loaded into a
building session would make it approve of its own work less and build
nothing, which is the wrong reader for that sitting.  So roles sit
apart, named, and cost nothing until one is asked for.

**How one is asked for.**  The invocation is the whole mechanism:

    your role is spec/roles/reviewer.md, what is missing from card:X?

The path first, because it is the thing that changes the session; the
request after, in the role's own terms.  A role page says at its top
what it is for and at its bottom what it cannot do, because a role
that hides its ceiling is worse than none.

## The roles

| role | what it is for | since |
|---|---|---|
| [reviewer.md](reviewer.md) | the second reader of an artifact its author can no longer see cold — *what is missing*, never *is this good*; reads and says, does not write | 2026-09-08 |

## Where they came from

The first was drafted outside the tree, by a guest session, from
thirteen reviews of this project's artifacts, at Henri's ask
(2026-09-08: *"How could I get you, a reviewing guest into my
project, as a permanent member within the claude code perhaps, called
when needed?"*).  `doc/notes/notes-on-reviews.md` is that conversation
and says which part of those reviews transfers to a role inside the
tree and which does not — the part that does not is the load-bearing
one, and every role page here inherits that ceiling.  **Untested
here:** no session has yet been handed this brief and had its review
measured; the first time one is, this line should say what came of it.

**Where it sits — his words on 2026-09-08:** *"roles are additional prompts for
sessions, initiated by 'your role is <path>, <request>', perhaps the
current place is spec/"*.  A directory of `spec/`, so the roles are
collected rather than scattered and so `spec/rules.md`'s cap, which
counts five named files, is not touched.  His to move.
