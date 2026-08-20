---
name: henri-working-style
description: "How Henri likes work done on gestate (docs, machinery, pacing)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a1462242-2c42-465a-b030-147d44823d59
  modified: 2026-08-17T16:06:13.266Z
---

Henri's preferences, from the guides/patches session (2026-08-09):

**Why:** Each was a mid-task correction.

- Docs/teaching material should be *explorative* — shu-ha-ri without
  naming it: a working form, specific "try:" variations with predicted
  outcomes, then open-ended departures. Lesson code carries the
  variation points in comments.
- **How to apply:** structure any guide/lesson as follow → vary → depart.
- Before writing new machinery, look for existing machinery ("there
  exists that already, you just need to use it") — e.g. the fade used
  `render_block_mix_f32`; host.c is audiopygame's, audiolive keeps its
  own drivers.
- Compiler/infra fixes go *after* content is written, as separate tasks.
- Henri runs the full test suite himself (it's ~22 min); run targeted
  test files only, don't launch the whole suite unasked.
- Lesson/example files live in the repo (examples/<tier>/), not in
  scratchpad.

From the burger-button session (2026-08-14), stated as the interface's
philosophy after iterating on the ≡ button: **no noise in the
interface, while still giving it all it needs.** Confirmed by the
corrections that led there: no grey ground behind the button (glyph
alone), exactly one character cell of footprint, faint colour until
active, half a cell of air so it doesn't lean on the edge.
**How to apply:** when adding workbench chrome, start from the minimum
mark that carries the affordance and let Henri ask for more, not less;
size and place in cell units so zoom preserves the design.

**Corrected 2026-08-17 by evidence, not by opinion.** A stranger (his
friend, no explanation) never found that button. Measured: 24 lit
pixels, 2.3:1 against the ground, drawn inside the document's own first
row — and the first screen even said "top right". So *the minimum mark
did not carry the affordance*, and "let him ask for more" cannot be the
whole rule when the person who would ask is the one who cannot see it.
The philosophy stands; what it now also needs is a person put in front
of it. `card:button.md`, `fixme.md` F150.

**He writes short on purpose, and knows it** (2026-08-17): *"I like
succinct style and value brief but elaborated text. You may have noticed
I communicate very briefly and sometimes err on saying too little."*
**Why:** brevity is the preference, not carelessness — and his shortest
asks have been the highest-signal ones. *"Just try take `Sig Floa` and
see how the message doesn't land"* was a whole defect (F152); *"I don't
notice which chatter you mean"* was a request for evidence, not an
explanation.
**How to apply:** when an ask is underspecified, **go and look before
asking** — reproduce it, photograph it, measure it — and ask only when
two readings would lead to materially different work (the packaging
card's `because` was worth asking; the chatter was not). And match him:
dense and elaborated, never padded. Long is fine when every line earns
it; throat-clearing is not.

**Work set-based, not point-based** (2026-08-17, his ask; written up in
`manifesto.md` §"Set-based, not point-based").
**Why:** he deliberately withheld the obvious fix — *"I intentionally
didn't say directly that the button should be made bigger, because it's
not necessarily the whole answer to it, or correct answer."* A model's
fluency **is** premature convergence: one well-argued answer arrives
already defended, and he can only review what was offered.
**How to apply:** on any design-shaped ask, give several answers with
*what evidence would eliminate each*, not one recommendation with
alternatives listed politely underneath. Then act immediately on
whatever every alternative agrees about (that is where the two F150
defects came from) and leave the rest open for the measurement. See
[[test-what-a-person-would-do]] — the two are the same discipline
pointed at design and at verification.

**And at this stage, an opinion is not a reason to change anything.**
*Henri, 2026-08-18*, after proposing that the `Ctrl-K` hint dim rather
than disappear and then withdrawing it himself: *"It's just my opinion
and we don't react on those anymore at this point of project's
timeline."*

**Why:** the fix he was proposing to change had passed a live test
minutes earlier — the stranger used the key and called it *kätevä* —
and the proposal rested on a guess about a difficulty nobody had
observed.  He caught it before I had to.

**How to apply:** when he floats an idea, ask what problem it solves and
whether anybody has met it.  If the answer is "it came to mind", record
it if it is cheap and move on; do **not** build it, and do not mint a
card for it.  This is the same rule as [[gestate-board-goal]]'s *stop
proposing cards*, arriving from his side of the table — and the
symmetric obligation is mine: my opinions do not get to drive work
either, which is what the measurement discipline is for.

