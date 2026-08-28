# online — gestate, the audio production tool, reachable in a browser

    status   open — written 2026-08-28 at the end of a sitting; the questioning is half done, §"Questions"
    because  "somebody who has never read this repository should be able
             to open a file, hear it, change it, and hear the change
             without being told anything first" (vision.md, 2026-08-16)
             — and today the only way to that first sound is an apt line
             on Ubuntu (doc/install.md): a person shown the tool at this
             desk cannot open it at home tonight
    asked    Michael, 2026-08-28, relayed by Henri — "Lets put gestate
             online, the audio production tool.  And Michael wants it."
    see      vision.md §"Ease of use and efficiency" — the `because`
             card:stranger-test.md — the person this waits on has arrived
             doc/memory/the-language-goal.md — wasm as a target, his own
             note of 2026-08-20; this card is the first thing in the tree
             that needs it
             doc/memory/lead-with-the-noun.md — the tool first, the method
             to whoever leans in
             doc/memory/the-tree-withers.md — a site with no source and no
             check rots; this must be generated from the tree and gated
             doc/consent.md — Michael's row

## The ask

Michael's idea, in Henri's words at this terminal, 2026-08-28:

> We could put your environment online, so that people can interact
> with you and experience it themselves..  Small models appear to work.

And the decision, an hour later, narrowed to the noun:

> Lets put gestate online, the audio production tool.  And Michael wants
> it.  But write a card for this.

**What was narrowed away, and why it is recorded.**  The first form of
the idea was a *session* online — a visitor talking to a character in
the tree.  That form is not this card: it needs a fence outside the
session's write access (`~/tend`'s three bounds, budget, grant,
lifecycle), a per-visitor ledger cap on a personally paid account, and
a sheet naming what a small model has already been shown to drop
(`doc/memory/smaller-models-and-the-tree.md`: structural rules survive,
judgment goes first).  It is a second card if anybody asks for it, and
its `because` would be a different sentence.  This one is the tool.

## Found by looking

* The stranger test has been run twice with a person at this desk and
  never with a person at their own.  Run two cost half its thirty
  minutes to *the way in* (`card:stranger-test.md`).  A browser tab is
  the way in with that cost removed.
* Everything a first sound needs is in the tree: `gestate.audioextract`
  builds the graph and `gestate.audiollvm` runs it native.  What is
  missing is a second backend for the same graph — wasm — which is the
  language goal's own target and nothing in the tree yet emits.
* `examples/audio/twinkle.ges`, added today, is the file such a page
  would open on: an instrument and a song, thirty lines, four words of
  vocabulary.
* The findability work of 2026-08-26 refused a homepage.  This is not a
  homepage — it is the tool — but the refusal's reason still binds:
  whatever is online must be built from the tree by a command and
  checked by a gate, or it describes a tree that no longer exists.

## Questions

*Half of these were answered in the room before Henri had to leave; the
rest are his, and the card is not taken until they are.*

**1. What must a stranger be able to do in the tab?**  Answered in the
`because`: open a file, hear it, change a number, hear the change.  Not
the workbench, not the canvas, not MIDI in — the vision's opening line
and nothing past it.  *Answered 2026-08-28, from vision.md.*

**2. Does the sound come from the browser or from a server?**  A server
is a session's problem all over again — a machine that must stay up, a
bill per visitor, a fence.  Henri, the same sitting: *"I need to move
soon and can't keep the laptop online."*  That is the answer: **the
browser computes the sound**, and the only server is a static file
host.  Which makes this card the wasm backend, and nothing less.
*Answered 2026-08-28, from his own constraint.*

**3. Where does it live, and who pays?**  `doc/memory/personal-and-personally-paid.md`:
personal, and the one mechanism that would break it is a per-visitor
cost.  A static page has none.  GitHub Pages from this repository is the
default with a trigger: if the page ever needs a process, this question
reopens.  **Open — Henri's to confirm.**

**4. What is the postcondition?**  The default: Michael, at his own
machine, opens the page, hears `twinkle.ges`, changes one number, and
hears the change — with nobody at his shoulder.  That is the stranger
test's run three, and this card is done when he reports it, in his own
words, into this file.  **Open — needs Michael's yes to being the
stranger, which is a separate ask from the one already in the
register.**

**5. What does it *not* do?**  A refusal is the most durable decision
this project makes (`spec/author.md`).  The default: no accounts, no
saving on a server, no session, no chat.  A tab that closes loses the
edit, and that is correct for a first sound.  **Open — his to strike or
keep.**

**6. Is wasm the whole cost?**  Unknown.  The LLVM path emits native
code from a graph; wasm is a target LLVM already knows, but the runtime
around it — the sample loop, the audio output, the editor — is a page,
not a compiler flag.  The first thing to measure before taking the card:
how far `llc -march=wasm32` gets on one existing graph, in an
afternoon, with no page at all.  **Open — a measurement, not a decision.**

## Done

*Nothing yet.*
