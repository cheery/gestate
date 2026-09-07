# transport-modes — the synth being on, and the score playing, as two switches

    status   done — 2026-09-07
    because  "we need separate states for synthetizer being on, and for
             when it's playing score." — Henri, 2026-09-07, recalling
             oscillseq's playback states
    asked    Henri, 2026-09-07 — "implement three transport states,
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

## Names — `silent`, `sounding`, `playing`

**And the word is *states*, not *modes*** — Henri, 2026-09-07, after
the collision with `vision.md`'s *gestate won't grow modes* was put to
him: *"rename them to states, modes is the wrong word."*  Renamed in
the spec, the module (`gestate/transportstate.py`), the wire's field
and the tests the same afternoon; this card keeps its filename, which
is its id.


**Henri, 2026-09-07:** *"the names you gave 'silent' 'sounding'
'playing' are excellent."*  Set 1 below, chosen.  And the verbs are
the window's own three — **Henri, 2026-09-07:** *"'stop' goes to
silence, 'play' goes to playing, 'audition' goes to 'sounding'..
'sounding' should show as some state of it's own in the bar."*  So no
new word joins `command.ges`; `spec/transport.md` sentences 4 and 5
carry it.  The other two sets stay here as the argument.


oscillseq had four; he asked for three and better words than
OFFLINE / ACTIVE / PLAYING.  Three sets, each with what would kill it:

| | synth down, card free | synth up, clock held | score running |
|---|---|---|---|
| **1. what the ears get** *(chosen)* | `silent` | `sounding` | `playing` |
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
   statechart by nature.  **Answered, Henri, 2026-09-07:** *"Yes, try
   the model languages on the transport card first.  One problem is
   that it's not an isolated case.  But maybe that's ok."*  The
   not-isolated part is §"Not isolated" of `spec/transport.md`: the
   model names its neighbours and owns none of them.
5. **Five decisions the model forced**, `spec/transport.md` §5.
   **Answered, Henri, 2026-09-07:** *"I think these are good
   choices"* — with two fixed by him: `stop` lands in *silent*, not
   *sounding*, and `audition` lands in *sounding*.  Left as the
   session's defaults: `play` from silent is one word and its toggle
   lands in sounding; `audition` while playing keeps playing; the
   keyboard is two axes; `inert` is fixed.
6. **The bar.**  His: *"'sounding' should show as some state of it's
   own in the bar."*  The furniture's `playing` boolean becomes the
   state on the wire — the landing, §6 of the spec.

## Done — 2026-09-07

Landed the same afternoon, `spec/transport.md` §6: the C host holds
the score's position while the engine's clock runs on, both transports
carry `advancing` and `clock`, the workbench has `state`, `set_mode`,
`sound` and `stop(keep=True)`, the three verbs run `step`, and the bar
draws ▶, ‖ and ■.  **The postcondition, both halves, held by tests**:
`test_a_key_pressed_while_sounding_is_heard` and
`test_silent_frees_the_card_and_sound_brings_the_instrument_back` in
`test/test_audioeditor.py`.  **The bar, photographed** — five shots in
`test/driven/20260907-143215-transport-modes/`: opened ▶, after `play`
‖ *sounding at 9.2*, after `stop` ■ *silent* with the readout kept,
after `play` from silent ▶ with the beat moving, after `audition` from
silent ‖.  The story is `journal.md` §"The three modes, landed".

## Day one — 2026-09-07

Q4 was yes, so: `spec/transport.md` says the model in sentences, as a
type in the tree's own spelling, as eight invariants and as a
statechart; `gestate/transportstate.py` is the type in Python with
`step` written out; `test/test_transport_model.py` holds the two
spellings to each other by name and walks all thirty steps.  `Transport`
is untouched.  What lands next, when he says, is §6 of the spec: the
boolean becomes the state, two verbs join `command.ges`, and the status
line names the state.
