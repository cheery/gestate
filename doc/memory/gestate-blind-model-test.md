---
name: gestate-blind-model-test
description: "How the 2026-08-19 blind three-model comparison was run on gestate, what broke in the setup, and what Henri concluded"
metadata: 
  node_type: memory
  type: project
  originSessionId: fc5bc40b-d263-41f1-811d-646208f57f50
  modified: 2026-08-19T03:48:13.922Z
---

2026-08-19, at Henri's ask: three cold `general-purpose` agents (haiku,
sonnet, opus) worked batch 1 of `card:ungated-fixes.md` from an identical
thin prompt — *your root is this checkout, start with `board/README.md`,
then work `card:ungated-fixes.md`* — and he judged the fifteen verdicts
blind before the models were revealed.

**Setup rules that matter for the next one:**

* **Local `git clone`, not worktrees.** Worktrees share one `.git`, so
  `git worktree list` names the siblings and the blind breaks on the
  first command that asks. A clone of this repo is ~64M.
* **Keep the model mapping outside the clones' shared parent.** I did
  not, and one arm read `map.txt`, looked into both siblings, and had to
  be discarded and re-run. It volunteered this in its own report.
* **Give each clone a parent directory containing nothing else.**
* Wall-clock and cost leak the model — withhold until he has called it.
* He is the blind judge; I am the unblinded experimenter. Warn him not
  to read the spawn calls, which name the models.

**The result, which inverted his expectation** (he expected sonnet to
pass, haiku to fail, opus to be fine):

* He would have committed **haiku's** — 5m17s, 76k tokens, and the only
  arm that obeyed the card's *one line per entry* rule. The other two
  wrote paragraphs into `fixme.md`, which `board/README.md` says belong
  to the journal.
* But haiku's F153 verdict was **wrong**, and my verification pass caught
  it. **He picked on form; form and accuracy came apart.**
* Opus was the only arm that ran mutations (found `NOFENCE=1` itself) and
  took 38m37s. Sonnet caught F153 and got F161 wrong the other way.

**The standing lesson:** his own rule — *he reviews, I do not decide
alone* — paid on the first batch. He picked the arm, I disagreed with one
of five, and the commit carries four of its lines and one of mine.

**His feedback afterwards, 2026-08-19:** *"this judgement was hard for
me. next time, if we repeat this test, I'd like more visual indication
and some aid in judgement."*

**Why it was hard, and it is my fault not his:** the sheet rendered each
arm's raw markdown, so *one line vs. paragraphs* was the loudest thing on
the page and accuracy was invisible — checking it needed five test bodies
read. He judged what was visible, and form and accuracy came apart.

**All four are BUILT — `tools/blind.py`, 2026-08-19 evening.**  Do not
rebuild them; run the tool.  It computes agreement first, runs the three
mechanical checks per citation (file exists / contains the cited name /
mentions the F-number), shuffles arms to A/B/C printing the mapping only
to the terminal, never collects wall-clock or cost, and puts prose
behind a disclosure.  The setup rules above are now in
`doc/instruments.md` §"Running a blind comparison" too, so they no
longer live only here.  Seven tests in `test/test_blind.py`, including
that the sheet cannot leak an arm's name.

The four requirements it was built from:

1. **Agreement first.** Mark each entry unanimous or split *before* he
   reads. Today 3 of 5 were unanimous; he only had to judge 2.
2. **Citations as bare tokens in a table**, so identical ones line up and
   the differences pop. The prose is justification, not the comparison.
3. **Mechanical pre-checks done for him** — does the cited test exist,
   does it name the F-number, does the suite run its file. Facts, not
   opinions, so they do not bias the judging.
4. **Normalise length** — one-line verdict shown, prose behind a
   disclosure.

**Do not** pre-mark which arm I think is right. That destroys the
independent read his review exists to provide.

See [[henri-subagents]], [[gestate-ungated-sweep]],
[[dont-conclude-from-a-shallow-check]].
