---
name: a-capitalised-word-before-a-date-is-a-person
description: "The consent gate reads any capitalised word directly before a date as a person being quoted — a bold *Since* and a date refused a commit twice on 2026-09-18; put a lowercase word before the date"
metadata:
  type: project
---

**The fact.**  `test/test_consent.py` finds attributions with two
patterns, and `DATED` is *a capitalised word, an optional comma, a
date* — the shape of `Henri, 2026-09-04`.  So a sentence that opens
with a bold *Since* or *Built* and the date straight after reads as a
person named Since, and the gate refuses the commit with *quoted in the tree
and not in doc/consent.md: Since*.  It happened twice in one day,
2026-09-18, in `doc/memory/gestate-language-pitfalls.md`, each time
found by the commit hook after a two-minute gate run.

**Why:** the gate cannot tell a verb from a name, and it is right to err
towards asking — a real name slipping past would be the expensive
mistake.  The test keeps an explicit allow-list of bold lead-ins that
are not anybody; adding to it is the honest fix when a word recurs, and
rewording is the cheap one.

**How to apply:** when writing a dated sentence into the tree, put a
lowercase word between the capital and the date — *and since*, then the
date; *built*, then the date — or run `python -m pytest
test/test_consent.py -q` before the commit hook does.  A refusal naming
a word that is not a person is this, not a consent problem.
