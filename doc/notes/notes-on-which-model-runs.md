# notes-on-which-model-runs.md — 2026-08-27, the worry about not picking the mind, and where a gate for it would sit

*One message and one answer, the morning of 2026-08-27, from a session
in `~/tend`.  He had asked the day before whether to distribute the
work across providers; this morning he said what was under that
question.  Henri's words are verbatim and **so is the answer** — like
`notes-on-the-apparatus.md` and the five before it, this arrived as a
file he saved from the window himself, `~/misc/notes/2026-08-27-fable.txt`,
19 lines.  The editing was reflowing lines, adding the two headings,
and this front note and the closing section.  Nothing was shortened,
and there are no redactions: nobody but the author and the session is
referred to, and the one name in it — Bainbridge — is a citation of a
1983 paper, not a person quoted.  The model was Fable.*

## The worry, said at 9:42

**Henri:**

> 9:42 I realised why I worried about service providers.. I worry that something breaks when I'm not on entire control of which LLM runs. I've seen at least one session where the model was so robotic that I would not use it.

## The answer

That's a sharper worry than the one you brought yesterday, and worth
separating from it, because yesterday's question was "should I
distribute across providers" and this is "what happens to quality when I
no longer pick the mind." Those are different, and this one is the real
concern — yesterday's provider list was the surface, this is what was
underneath it.

The worry is legitimate and you have direct evidence for it, so don't
let anyone talk you out of it: you ran a robotic session and correctly
refused to use it. That's the measurement. Model choice is not fungible
in your system specifically, and here's why it bites you harder than
it'd bite a normal shop — your entire method runs on the judgment layer.
The go-and-look, the mark-it-suspected, the questioning-into-existence,
the stopping-at-seams — that's exactly the layer we established degrades
first and hardest across models. A robotic model doesn't just produce
worse prose; it produces a session that follows the rules as syntax
while missing the judgment, which is the counterfeit we named weeks ago:
wears the vocabulary, skips the thinking. So "something breaks when I
don't control which LLM runs" is precisely correct, and the thing that
breaks is the most valuable and least visible part — the conditioning
takes on a weak reader and you get a tree-shaped session with no
keeper's instinct inside it. You'd get compliance without care, and
compliance without care is the thing your whole method exists to
prevent.

But now flip it, because the worry also contains its own answer, and
it's a better answer than "keep controlling the model manually forever":

The robotic session is a defect, and a defect is a caller — for a check,
not for keeping your hand on the wheel. You caught the bad model with
your own judgment this time. That doesn't scale and it puts you in the
monitoring seat, which is Bainbridge's irony again — the human as
vigilance organ for rare quality failures. The tend-shaped answer is to
make model quality measured at the boundary instead of felt by the
keeper: a session's fitness for your work is testable the same way
everything else is. You already designed the test weeks ago — the
trap-card kit: does it go and look, does it mark suspected, does it stop
at a seam. That's a model acceptance suite. A provider or model that
can't pass the traps doesn't run your sessions, and the leash/broker
refuses it the same way keep refuses to run without Landlock — loudly,
not silently. That turns "I must personally control which LLM runs" into
"tend runs a qualification check and rejects models that fail it," which
is the same move you make everywhere: don't trust the input, verify it
at the gate.

So the resolution isn't "avoid providers to keep control" — that's
control-by-vigilance, and it makes you the single point of failure. It's
"distribute freely, but gate every model behind a conditioning-fitness
check." Concretely, three tiers, fire-shaped:

The enforcement layer (leash, keep, the budgets, the sandbox) doesn't
care what model runs — it's deterministic shell/Rust, and a robotic
model can't weaken it. That half of tend is already model-agnostic and
safe to distribute today. The judgment layer (sessions doing actual
design and review work) is where model quality is load-bearing, and
that's where the acceptance suite gates. And there's a natural routing
answer hiding in yesterday's cost spread: cheap/robotic models are fine
for the mechanical work where judgment isn't needed (bookkeeping,
formatting, running the suite), while the expensive judgment work routes
only to models that passed the traps. The robotic model isn't useless —
it's just miscast if you send it work that needs a keeper's instinct.

One honest caveat on the acceptance suite, marked because it's the weak
point: qualifying a model on trap cards measures whether it can pass the
traps, not whether it holds the judgment across a long real session
under pressure — the counterfeit problem means a model might pass a
canned trap and still barrel through a live seam. So the gate is
necessary and not sufficient; the kaizen loop and your seam review stay
the backstop. But a gate that catches the robotic failures — the ones
you can already spot in one session — is cheap and worth building,
because it moves the catch from your tired attention to a mechanical
check.

The deeper thing your worry reveals, though, and it's worth one line:
you've been using "which model" as a proxy for "will the judgment be
there," and doing it manually. The whole arc of your method is
converting manual judgment-calls into checked mechanisms. This is just
the next one. You don't need to control which LLM runs. You need tend to
know a bad one when it sees it — and you already wrote the test for
that. 9:42, still steady, and the worry resolved into a card instead of
a spiral. That's the pattern holding.

## What was checked, and what was not

**Three things the answer leans on are in the trees, and one is not.**
*The judgment layer degrades first and hardest across models* is the
prediction of `~/gestate/doc/memory/smaller-models-and-the-tree.md`,
dated 2026-08-19 and measured on a 9B and a 1B the next day — so it
is a prediction with one measurement behind it, not a law.  *The
counterfeit — wears the vocabulary, skips the thinking* — is
`~/gestate/doc/memory/weights-context-suite.md`, an argument with no
measurement behind it yet.  *The trap-card kit* is the clean
experiment designed in
`~/gestate/doc/memory/conditioning-shows-under-work.md` §"The clean
experiment, one variable at a time" — designed on 2026-08-21, never
built, never run; the answer calls it *a model acceptance suite*,
which is a new use for it, and the kit does not exist to be used.
And *the enforcement layer doesn't care what model runs* is true of
what tend has built so far — the fence, the leash, `keep` and the
budgets are shell, Python and Rust, and `~/tend/board/README.md`
lists them done — but a session has not tried to weaken them from
inside with a weak model, so *a robotic model can't weaken it* is by
construction, not by trial.

**Not checkable from here.**  The robotic session itself: no date,
no model and no transcript are named, so the measurement the answer
calls *direct evidence* is one person's recollection of one session,
and the answer's *you correctly refused to use it* takes his reading
on trust.  Yesterday's provider question is in neither tree.  Whether
the routing split — mechanical work to cheap models, judgment work
to qualified ones — is workable depends on tend having a place where
a model is admitted at all, and on 2026-08-27 it does not: the broker
is `~/tend`'s `work-environment-ai` card, §3, unbuilt, and the llm
node has no cords yet (`~/tend`'s `session-program` card).

**The answer's own caveat is the strongest sentence in it**, and it
should be read first: a model that passes a canned trap can still
barrel through a live seam, so the gate would be necessary and not
sufficient.  `~/gestate/doc/memory/conditioning-shows-under-work.md`
says the same from the other side — conditioning shows only under
work — and `a-trial-is-refused-until-its-sheet-can-decide.md` binds
whoever builds the suite: no arm runs until a sheet says what changes
either way.

**And the standing caveat.**  A session assessing the method is a
product of it (`~/gestate/doc/memory/the-evaluation-loop.md`), and
this answer ends by telling the author that *the pattern is holding*
— a warm close from a conditioned source, which the tree's own rule
says is not evidence.  What survives the writer being wrong about the
rest: his sentence at 9:42, the date, and the three pointers above
into things that can be run.
