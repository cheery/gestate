---
name: headless-claude-inherits-the-hooks
description: "A headless `claude -p` started in this checkout inherits .claude/settings.json's hooks — the sitting limit refused 276 extraction calls on 2026-09-11 and the tool cached the refusals as replies; run batch calls with a working directory outside the project, and never cache a reply with no tokens in it"
metadata:
  type: project
---

**A `claude -p` is a session, and the tree treats it as one.**  On
2026-09-11 `tools/graphrag.py extract` ran four headless Haiku calls
at a time from a session's shell in `~/gestate`.  At 20:48 the sitting
limit — `tools/limit.sh --hook` on `UserPromptSubmit` in
`.claude/settings.json` — decided the sitting that started at 20:17
was over, and from then on every call came back in 1.5 seconds, zero
tokens, with the hook's message as its result.  The tool took that
for a reply and cached it.  276 chunks were marked extracted; none
was.

**Found by a number that could not be true**: 310 chunks in 17
minutes at 93 seconds a call.  [[a-run-silent-for-a-minute]] from the
other side — a run *too fast* is telling you about the harness first.

**Why:** the fence and the hooks are keyed to the working directory,
not to the person at the keyboard.  A batch job started inside the
project is inside the fence's world, and the sitting limit is right
to stop it: a person's hours are the person's, and nobody had told it
this was not a person.  The defect was the tool's — it accepted a
refusal as an answer.

**How to apply:**

- A batch `claude -p` runs with `cwd` outside the project — the tool's
  cache directory — so no project hook reaches it.  The API key stays
  unset so the subscription pays ([[personal-and-personally-paid]]).
- A reply is a reply only if the model was asked: output tokens above
  zero and an object in the text.  Anything else is retried, then
  fails out loud, and is **never cached** — a cached refusal is a
  chunk the graph will never see again.
- A tool that is meant to be killed writes its own pid.  `$!` behind
  `nohup` named the shell, and the scheduled kill took the shell.
- `python tools/graphrag.py check` says how many chunks a run would
  call; if it says *current* after a run that was too fast, read one
  cached reply before believing it.

Related: [[a-sitting-is-a-body-constraint]], [[gestate-hardening]],
[[a-build-is-not-an-instrument-until-it-has-failed]].
