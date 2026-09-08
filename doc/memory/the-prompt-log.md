---
name: the-prompt-log
description: "~/.claude/history.jsonl holds every prompt Henri typed, back to 2026-08-03 — five days before git's first commit; it is the one corpus here no session wrote, it is outside the tree, and the transcripts beside it were a rolling 30-day window until 2026-09-08"
metadata:
  type: reference
---

**Where it is, and what it holds.**  `~/.claude/history.jsonl` — one
JSON object per prompt: `display` (the text), `timestamp` (epoch ms),
`project` (the cwd), `sessionId`.  On 2026-09-08 it held **2,943
gestate prompts over 37 days and 106 sessions, from 2026-08-03 09:11**.
Prompt text only: no responses, no tool calls, and **no reasoning** —
thinking blocks survive in the transcripts carrying a signature and no
words, so what a session considered and dropped is recorded nowhere.

**Why it is worth knowing about.**  Everything else here passed through
a session's hands — the journal is a session's account, a card is a
session's elaboration, a memory is a session's compression, and even
Henri's quoted words are in the tree because a session chose which
sentence to keep.  This file is raw and was conditioned by nothing.  It
is the first source available for checking a claim about this project's
history **that a session did not author**.

**What it is not.**  It is still Henri, so it carries his blind spots
and cannot say the tree is pointed the wrong way — it does not fill the
external slot `spec/roles/reviewer.md` leaves open.  It holds no
responses, so it settles nothing about what a session did.  And a
reading of it is a session's reading like any other: the corpus is
outside session authorship, the interpretation never is.
[[the-evaluation-loop]], [[do-not-overclaim]].

**It is outside the tree and a clone does not get it.**  A tool in
`tools/` that read it would be a tool that does nothing for a stranger,
which is why there is none.  The readers live in `~/misc/`:
`prompts2md.py` (prompts to markdown, by day) and `transcript2md.py`
(one session transcript to markdown).  [[research-that-leaves-a-command]].

**The transcripts beside it were expiring.**  `~/.claude/projects/`
deletes anything older than `cleanupPeriodDays`, unset means the default,
and on 2026-09-08 exactly 31 days were present with one leaving every
morning — **19 sessions had already gone.**  `~/.claude/settings.json`
now carries `"cleanupPeriodDays": 3650`, and `~/misc/claude-archive/`
holds a copy that does not depend on that surviving a reinstall;
`refresh.sh` there is additive and idempotent.

**And what may be taken from it.**  It holds material that is his and
private — health, family, livelihood, named third parties — so a
session reading it takes the line it came for and no colour beside it;
`doc/consent.md` is the register for names and consent given for one
purpose is not consent for this one.  [[private-is-private]].

Companion: [[day-one-was-not-day-one]], which this record moves five days
earlier.
