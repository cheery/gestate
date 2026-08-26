---
name: gestate-findability
description: "2026-08-26: a search engine could not find the repository by name; the GitHub description and topics were set that day by Henri's hand, and the only measurement is to ask the same engine again a week later, unsteered"
metadata:
  type: project
---

**The occasion.**  Henri had Google's search engine write an article on
gestate and tend (`~/gestate_ja_tend.md`); it could not find the
repository by name and had to be steered, and what it wrote about tend
was invented — `keeper.md` attributed to tend, "vibe coding", a
"child project".  Checked against both trees: the gestate half held,
the tend half did not.

**What was found.**  `cheery/gestate`'s GitHub description still read
*"Functional programming language implementation in python"* — from
before there was sound — and neither repository had a single topic.
`~/tend` had no README at all, so a crawler had one line to read there.

**What was done, 2026-08-26, by Henri's own hand** (a session's
`gh repo edit` is blocked by the harness, and it should be — it is
outward-facing): gestate's description is now the README's own first
sentence plus the nouns, with topics `live-coding audio music synthesis
llvm functional-language python rust`; tend's description was already
right and got `claude-code agents documentation workspace`.  A README
was written for tend and left uncommitted for his verify.  The article
was rewritten against the trees, in Finnish and English, with a PDF of
each — `~/gestate_ja_tend_korjattu.*`, `~/gestate_and_tend.*` — and
Henri read the Finnish one and called it fine.

**What was refused, and why.**  No `llms.txt`, no homepage, no card:
Google is not known to read `llms.txt`, a site is a living document
with no source and no check ([[the-tree-withers]]), and the tree owes
no persuasion ([[showing-not-persuading]], [[the-tree-meets-people-on-pull]]).
The name itself is a common English verb; that is not fixable.

**How to apply.**  Read the metadata before proposing anything:
`gh repo view cheery/gestate --json description,repositoryTopics`.
The measurement is the same question to the same engine about a week
after 2026-08-26, *unsteered*: found by name means the metadata was
enough; not found means age and inbound links, which nothing in the
tree helps.  A session never runs `gh repo edit`; it hands Henri the
one-line command.  See [[lead-with-the-noun]], [[research-that-leaves-a-command]].
