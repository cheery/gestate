# hands-in-the-tab — the three pieces whose score reads what a hand holds

    status   open — 2026-09-11
    because  "I think I'd like to provide a gallery of controllable
             audio-visual experiences." — Henri, 2026-09-02, the
             `because` of card:audiovisual-gallery.md.  Three of the
             thirty-four pieces are controllable in a way the gallery
             cannot reach: `arpeggiator`, `jazz` and `ladder` play what
             your hands hold, and the page refuses them rather than
             showing a smaller version of them.
    asked    Henri, 2026-09-11 — "Play-along now; the three get their
             own card", given the obstacle measured and the correction
             below
    see      card:audiovisual-gallery.md §"The MIDI row is not what this
             card said it was" — where this was found, and the wrong
             answer a session gave first
             card:online.md §"The pieces" — C, and what C actually is
             spec/dynamicscore.md — stage two, the plugin's answer
             shell/clap/src/dynscore.rs — the same thing, already built,
             for a host that is not a browser

## What this is, what it is not, and where it runs

**Three pieces, one property.**  `arpeggiator.ges`, `jazz.ges` and
`ladder.ges` are the only files in `examples/audio/` whose **score**
contains `hear holds.<bank>` — counted 2026-09-11, three of the
thirty-four that declare a `voices` bank.  Their score's *content*
depends on what is held right now: `ladder` is `ks <- hear holds.keys;
rung i ks`, an arpeggio planted on whatever you are holding.

**It is not the play-along row**, which is built: notes into a bank
*beside* a running score, which every other piece takes and which these
three also take — they simply have nothing to play until their score
runs.  It is not a keyboard question at all; the keyboard is there now.

**And it is not `card:online.md`'s C1**, which a session said it was on
2026-09-11 and was wrong.  C1 is **compiling `.ges` text in the
browser**, which needs the front end and is what Pyodide was struck
for.  This needs an already-compiled program's stream *forced*, which
is a different machine.

## The obstacle, measured

**The G-machine is already in the tab.**  `shell/web` depends on
`crust` and builds for `wasm32` today; its own header says *"only a
G-machine could run it and the tab had none"*, past tense.  And the
plugin does exactly this job with no Python at run time:
`shell/clap/src/dynscore.rs` carries `engine::Program` and forces it
one horizon at a time on `crust`, with `descriptor.rs` written by
`python -m gestate.export` at **build** time — which is what
`online.generate` is to a page.

*Henri is the reason this is known.*  Told the three needed Pyodide he
did not believe it: **"I'm a bit surprised that pyodide would be
needed there.. I thought that clap plugins work same way now, and it
doesn't require python to work, or does it?"**  They do, and it does
not.

**What is actually missing is a seam, not a backend.**  `crust` is
linked into the **canvas** module and the sound is in the **audio
worklet** — two wasm instances that do not share memory.  A score
forced in one has to reach control slots in the other, and where the
forcing happens is the decision this card opens with:

| where the score is forced | what it costs |
|---|---|
| in the **worklet**, its own `crust` | a second G-machine instance, and the audio thread walks a stream |
| on the **main thread**, beside the canvas | a post per event, and the score is paced by the page's frame clock rather than by the samples |
| in the **canvas** module, events posted across | the picture's machine does two jobs; one instance, one pace |

## What a session does on day one

Read `shell/clap/src/dynscore.rs` and `spec/dynamicscore.md` stage two
— the plugin is the worked example of this, on a host that is not a
browser — and measure what `engine::Program` costs to serialize into a
page.  Then the table above is a question for Henri and not a guess.

**The test set is the three pieces**, and the check is the one the
gallery already uses: the page plays what `run_native` plays, for a
score driven by the same held notes.

## Questions

**1. Where is the score forced?**  The table above; his.  *Nobody's
default yet — a session should measure the serialize cost before
offering one.*

**2. Does the page keep the baked road for the other thirty-one?**
*Session's recommendation, suspected:* yes.  Baking is right where a
score does not depend on the hands, it is what the site ships today,
and making every piece force a stream at frame rate to serve three
would be paying everywhere for what is wrong in three places.

## Done

*Nothing yet.*
