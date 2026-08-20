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

**Trust the detector, check the attribution — 2026-08-20, his own read:**
*"'feels nice', 'looks right', those are in my vocabulary. If I were to
guess. It's strong intuition that I can trust."*

**Why: the tree scores it, and the score splits cleanly.**  *That
something is wrong*, he gets right against everything else in the room —
`doc/audit.md` was opened because *"the examples sounded wrong in places
while reading clean"*, and the FFT then found `stringLen` short half a
sample of period, `string 440` ringing at 438.0 Hz with the error
varying by pitch.  F126 arrived as *"it appears to not build the graph
correctly now"* and was a crash; F139 as *"the scope has the same
clipping issue as canvas used to have"*, pattern-matched across two
painters, correct.  *What* is wrong, he gets wrong as confidently:
`systemctl is-enabled ufw` looked like the firewall being up, *97 of
161* felt like the number and was 79, and the consent gate looked like
it recognised names when it reads two typographic slots.

**How to apply:** treat a feel-report as **evidence that something is
there**, never as the diagnosis, and never argue it away because the
code reads clean — that is the case where he has been right and the
reading wrong.  Then measure before naming a cause, his or mine.  Every
instrument here is that shape: the ear says the strings beat, the FFT
says −8 cents.

**And he has been running this discipline longer than this project has
existed.**  Shown to him on 2026-08-20 out of **Lever**
(`github.com/cheery/lever`, MIT, his own language before gestate), where
`samples/predator_prey.lc` carries it whole in four lines:

> *"Once in a while the population tended to collapse entirely.  I
> guessed it's due to the method I used to integrate so I switched away
> from euler.  The current model feels nice."*

Symptom as fact, mechanism flagged **"I guessed"**, result taken by feel.
The separation is his, it is a decade old, and what it lacked then was
anywhere to be filed — that comment is a `fixme.md` entry that no index
could reach.  Named here at his own word: *"it's all in github in same
account.  I think it can be committed without injury."*

See [[test-what-a-person-would-do]], [[dont-conclude-from-a-shallow-check]].
