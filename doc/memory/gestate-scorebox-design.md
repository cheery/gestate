---
name: gestate-scorebox-design
description: B4 read-only score box — built 2026-08-14; how it works and what building it taught
metadata: 
  node_type: memory
  type: project
  originSessionId: a39d6278-e714-4d78-bf76-0de8ee9cf3fd
  modified: 2026-08-14T15:30:37.612Z
---

**Built 2026-08-14** (spec/scorebox.md written first, then revised
from the code; roadmap B4 points at it).  `notes <expr>` stands a
roll on that line: `gestate/scorebox.py` is the mind,
`test/test_scorebox.py` the acceptance (15 tests).

How it works:
- Ask rewrites to a **comment** in `audiovoices._sinks` (not a hidden
  def like `canvas <expr>` — the compiler has no use for it).
  `scorebox.ask_of` is the single rule both scans use.
- **Provenance in the view**: descend the expression's parse tree,
  wrapping each written leaf in `tagAll k` (music.ges) so one
  `spreadTo` walk yields events tagged with their leaf.
- `Notable a` (audio.ges): `noteKey`/`noteVel`; `instance Notable Int`
  for bare notes; pieces add two lines.
- Roll → a **generated substrate program**, so the window walks it as
  an ordinary canvas box; furniture emits `canvas <line> __notes_k__`.
  A press writes `__nb_c<box>_<k>__`; `session.touched` maps it to a
  line and calls `view.goto` (read-only: nothing is written).

Traps hit (all cost real time — check these first next time):
- **Never slice source by span.** `VPrefix` carries a *defaulted*
  span; slicing swallowed the file. Use `fmt.format.Formatter._fmt_val`
  to print a node back; take the *line* from atom spans (VWord/VConId/
  VNum/VStr) only.
- `>>=`, `'` (pure) and `++` are **class methods**: an unannotated
  generated def collects dictionaries and becomes arity-2, then
  "Unwinding global with too few args". Anchor with a signed helper
  (`tagAll`) or `at 0 (...)`.
- **F136** (found here, in fixme.md): a lambda with a *tuple pattern*
  parameter dispatches a constrained call to the wrong instance,
  silently. `map (e => f e)` + `case` works; `map ((a,b) => …)` does not.
- An assigned part is `[: Void :]` — no payload to read. The box
  generates **unassigned twins** (`voices.B e` → `' e`), transitively,
  because the modern idiom assigns inside parts (undertow).
- The descent reads *expanded* text, where `voices.bass` is
  `voicesBass`.
- Generated pictures: no unary minus (write `(0 - 192)`); nested
  `Over` per note overflows the parser (use a list + recursion like
  scoped.ges); canvas entry needs `Sig Sub`, so `!(...)`.
- A program may declare its own `notes` — asks must exclude
  declarations.

Related: [[gestate-next-session]], [[gestate-verify-workflow]],
[[gestate-language-pitfalls]]
