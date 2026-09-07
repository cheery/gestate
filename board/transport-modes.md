# transport-modes — the synth being on, and the score playing, as two switches

    status   open
    because  "we need separate modes for synthetizer being on, and for
             when it's playing score." — Henri, 2026-09-07, recalling
             oscillseq's playback states
    asked    Henri, 2026-09-07 — "implement three transport modes,
             OFFLINE, ACTIVE, PLAYING (come up with better names for
             these) on the gestate.  Write a card from that."
    see      doc/memory/henri-prior-tools.md — oscillseq: OFFLINE /
             ONLINE / FABRIC / PLAYING, *parts restartable while sound
             continues*; "gestate's live audio has the same problem and
             no such name for it"
             spec/annotations.md — a gesture sounding what it did:
             built, **playing only**
             card:notes-editor.md — hear the move before the hand has
             left the mouse
             card:gui-is-difficult.md Q5 — a candidate for trying the
             model languages first

## What this is, what it is not, and when it runs

**The workbench's transport, given three states instead of two.**
Today a program file opens with the engine built and the sound card
taken, and the transport is either *playing* or *stopped*.  This card
splits *stopped* in two: the instrument up and audible under the hands
with the score's clock held, and the instrument down with the card
released.  It is not a change to the engine, the rebuild or the
performer, and it is not `performing` off/on/step, which says where
the *keyboard's* notes go and stays a separate switch unless Q3 folds
it in.  It runs whenever a `.ges` or `.notes` is open.

## The postcondition

A note moved with the score stopped is heard; and a file can be
edited with the synth off and the sound card free.

## Measured against the tree, 2026-09-07 — the session's reading

| today | where |
|---|---|
| a program file takes the sound card on open | `Workbench.__init__`, `Live.start` |
| the transport has two states, `playing` true or false | `Transport.playing`, `HostTransport` |
| stopped fills silence and does not call the engine, so the keyboard is silent too | `Transport.fill` — *"a stopped transport is stopped, not playing nothing"* |
| a dragged note sounds only while playing | `spec/annotations.md`: *built, playing only* |
| the only "engine off" state is `inert`, and it is by file suffix | `Workbench.inert`, `INERT` |

So *synth on, score off* does not exist, and *synth off* exists only
for files that are not programs.  Both halves of the `because` are
measured true.  *Suspected, not measured:* that holding the card while
editing is what makes the machine crackle for the person at the desk
(`board/README.md` §"What the first full day of this taught", *the
machine is shared*).

## Names — the session's proposal, his to pick

oscillseq had four; he asked for three and better words than
OFFLINE / ACTIVE / PLAYING.  Three sets, each with what would kill it:

| | synth down, card free | synth up, clock held | score running |
|---|---|---|---|
| **1. what the ears get** *(recommended)* | `silent` | `sounding` | `playing` |
| 2. what the machine is | `down` | `up` | `running` |
| 3. a musician's day | `off` | `tuning` | `playing` |

Set 1 names each state by what you hear, and `playing` is already the
command and the status word.  *What kills it:* `sounding` with the
hands off is silence too, so it names a capability rather than a
state.  Set 2 is exact and borrowed from servers; it says nothing
musical.  Set 3 reads best aloud and `tuning` claims an activity that
may not be happening.  The tree's own words are taken: `inert` means
a non-program file, `live` is the engine class, `active` is
elsewhere.

## Questions

1. **Where does `stop` land** — `sounding` or `silent`?  *Session's
   default:* `sounding`, because stopping the score to move a note is
   the everyday case and releasing the card is the rare one; a second
   word brings the synth down.
2. **Where does opening a file land?**  Today it takes the card at
   once.  *Default:* as today, `sounding`, so nothing a person does
   now changes; `silent` on open would need a reason.
3. **Is `performing` off/on/step a fourth axis or folded in?**  It
   says where the keyboard's notes go.  *Default:* left alone; it is
   about writing, not about sound.
4. **Does the trial of the model languages happen here?**
   `card:gui-is-difficult.md` Q5 — this card is small and is a
   statechart by nature: three states, the commands as transitions,
   and invariants worth checking — *the card is never held in
   `silent`*, *the clock never moves outside `playing`*.  His to say.

## What a session does on day one

If Q4 is yes: write the three states as sentences, then as a type,
then the invariants, and check them before touching `Transport`.  If
no: a three-valued state on the transport read by `fill`, `stop`
landing on `sounding`, a new command for the third state, and the
status line saying which of the three the window is in.
