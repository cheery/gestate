# commands.md — the vocabulary

*`spec/workbench.md` says what a command **is** — a transition, in a
sublanguage of gestate, with a list you can read.  This says what the
commands **are**, and why each one has the type it has.  The list that
runs is `gestate/command.ges`; this is the design it answers to.*

---

## `Named a` — a name, and what it names

Almost every command is about something the program declared: a knob, a
bank, a definition.  The obvious type for that is a string, and a string
is wrong.

    set : Named a -> a -> Command

**The value's type follows the parameter.**  An `Int` knob takes an
`Int`, a `Float` knob a `Float`, and asking for the wrong one is a type
error rather than a sentence somebody has to compose at run time.  The
first draft of `command.ges` had `set : Name -> Float -> Command`, and
the cost of that is visible in what it forced: a lookup of the knob's
range, a clamp, and a hand-written `no parameter \`x\`` — three
refusals, all of which the checker does for free once the name carries
its type.

It also gives the view something to ask with.  A command wanting a
`Named a` is a command wanting *a name that exists*, so the palette
offers the ones that do, and it knows that from the type without being
told separately.

**The consequence: a command is typechecked against the file being
edited.**  `cutoff` is declared in the author's program, not in
`command.ges`, so resolving `set cutoff 0.42` means inference over the
file in the window.  That is not a new cost — the workbench compiles
that file on every `apply` — and it is what makes the palette's
completions the program's own names rather than a list somebody
maintains.

### Why the name and the type are both needed

`audio.ges` records the exact gap this fills, about `FromMIDI`:

> Two banks may carry the same payload — `duet.ges`'s `lead` and `bass`
> both carry `Pitched` — so they share this instance and **nothing in
> the type could tell them apart**.  Which of them listens is the
> environment's switch, not the program's.

`Named Pitched` is inhabited by both `lead` and `bass`.  The **type**
says what kind of thing may be named; the **name** says which one.
Neither alone is enough, which is why this is one type rather than a
string beside a constraint.

**It is a phantom type**, and that is the whole implementation:

    Named a := TheName Text

The value is the name; `a` is what the editor found at the declaration.
Nothing in `command.ges` constructs one, because only the editor can —
only it has the program in the window and its inferred types.  A command
written in the palette names a declaration in the file.

*(Named `Identity a` when it was proposed, and renamed here for one
reason only: `Identity` is a well-known functor elsewhere and means
something else.  The project's own sense of the word — "held by
identity, not re-read", "node identity is structural", *which
particular one* — is exactly right for this, so the rename is about
outside readers and nothing else.  It is a one-word change back.)*

---

## Two constraints, because there are two roads in

A controller sends notes and it sends knob turns, and those arrive by
different roads and mean different things.  The classes say which
commands each road can reach.

**`FromMIDI`** — already in `audio.ges`, already the thing a bank's
payload implements:

    class FromMIDI a where
        noteOn : Int -> Int -> Int -> Maybe a

`Maybe`, because a bank may decline a key: that is the whole of the
note-strip the plugin panel draws.

**`FromCC`** — new, and the counterpart for parameters:

    class FromCC a where
        fromCC : Int -> a

**No `Maybe`**, and the asymmetry is the point.  A key may be outside a
bank's range and a bank must be able to say so; a controller's 0…127
always means *somewhere* in a knob's travel, and a knob that could
decline a position would be a knob with holes in it.

The instances are the two things a control channel carries: `Int`
knobs, which the examples read as a percentage, and `Float` knobs,
which are already fractions.  A future knob over some other type gets
one row and no new machinery — which is the whole reason this is a
class and not two cases in the editor.

---

## The commands

### The instrument

    apply     : Command                 Ctrl-S
    audition  : Command                 Ctrl-Return

The two that make this an instrument rather than a text editor.  `apply`
rebuilds and swaps in *while it plays*, so an oscillator keeps its phase
and a filter its memory (`spec/liveaudio.md` stage 5), and saves.
`audition` does the same without saving, because **hearing a change and
committing to it are different decisions** and an editor that conflates
them makes you save things you were only trying.

### The transport

    play      : Command                 Space
    stop      : Command
    seek      : Int -> Command

`play` toggles and `stop` does not, which is two commands where one
would nearly do.  A toggle is what you want under your thumb while
working; an unconditional stop is what you want when you have lost track
of the state and simply want silence.  They answer different questions.

**Bars count from one.**  A transport counts beats from zero and a
musician counts bars from one; the conversion lives in one function so
nothing else has to know it.

### The loop

    loop      : Int -> Int -> Command
    loopAll   : Command
    loopOff   : Command

Where the list pays for itself most visibly.  `audiopygame` spent four
keys here — `o`, `O`, `[`, `]` — and you had to know all four.  One
`loop` with arguments and two conveniences says the same thing and reads
itself.

### Parameters

    set       : Named a -> a -> Command
    learn     : FromCC a => Named a -> Command

`learn` binds the next controller that moves.  Its constraint is
`FromCC` and **not** `FromMIDI`: a CC is a 7-bit number arriving on the
controller road, and a note payload is something else entirely.  The
first draft had `FromMIDI` here and it was simply the wrong class.

### Notes

    listen    : FromMIDI a => Named a -> Command
    deafen    : FromMIDI a => Named a -> Command
    octave    : Int -> Command

Two wrappers over one representation rather than `listen : Named a ->
Bool -> Command`, because a palette that asks you to type `true` is a
palette nobody enjoys.

The constraint is doing real work: a bank whose payload has no
`FromMIDI` instance *cannot* hear a keyboard, and today that is a
runtime refusal.  With the class it is not offered.

### Performing

    performOff  : Command
    performOn   : Command
    performStep : Command

What a **played note** does: nothing, sound, or sound and be written at
the cursor.  Three wrappers over one three-valued setting, the way
`listen`/`deafen` are two over one boolean — a palette that asks you to
type a constructor is a palette nobody enjoys.

**This is not a mode of the editor**, and that distinction is the whole
reason it is admissible where `audiopygame`'s `P` was the thing this
design is trying not to have.  It changes what happens to a *note*, not
what a *key* means.  The letters still type.  Nothing about the text
becomes unreachable, and there is no `Esc` to remember.

Two things follow, and both are checks that it is the right shape:

*Where the computer keyboard goes is **focus**, not a mode.*
`audiopygame` reached the same answer and said so — *"focus is the whole
of that mode: the letters are bound to the piano rather than globally,
so they can never reach the source text"* — but then also had a mode,
which is the part to drop.  Focus is a thing every window already has
and every person already understands: click the drawn piano and it has
the keyboard, click the text and the text does.  So `performStep` says
what a note *does*, and focus says where notes *come from*, and neither
has to know about the other.

*A note written in step is a **text edit**.*  It goes through the same
door as typing, which means `spec/editor.md`'s rule holds without a
special case — undo is text undo, the score is the one truth, and there
is no second model recording what was played.  That is the same
consistency the widget rule buys: a dragged knob and a typed number are
indistinguishable afterwards, and so are a stepped note and a typed one.

### Chance

    seed      : Int -> Command
    reroll    : Command

A chancy piece is a family of takes and the seed says which one — the
same thing the plugin panel puts beside its `RNG` button, in the window
where the piece is being written.  Both, because they are different
gestures: **rolling** is what you press while looking for a take,
**typing a seed** is what you do once you have found one worth keeping.

### The text

    undo      : Command                 Ctrl-Z
    redo      : Command                 Ctrl-Y
    find      : String -> Command       Ctrl-F
    goto      : Named a -> Command
    what      : Named a -> Command

**`find` and `goto` are two commands, not one.**  `find` searches text —
arbitrary text — and the moment it matters most is when you are looking
for something that is *not* a name yet: a typo you are fixing, half a
word, a fragment of a comment.  Typing it as `Named a` would remove the
tool exactly where it is wanted.  `goto` jumps to a declaration, which
in a language made of declarations is arguably the more useful of the
two.  Conflating them loses both.

`what` says what a name is and what type it has — the compiler
answering, rather than a documentation lookup.  Its argument follows
`spec/workbench.md`'s third composition rule: **a command wanting
something and given nothing uses the selection**, so `what` with the
cursor on a name is `what` of that name.

Undo is *text* undo and belongs to whatever holds the text
(`spec/editor.md`); these commands ask, they do not implement.

### The window

    canvas    : Command                 Ctrl-Tab
    source    : Command                 Ctrl-Tab
    zoomIn    : Command                 Ctrl-+
    zoomOut   : Command                 Ctrl--
    quit      : Command                 Ctrl-Q

`canvas` and `source` share a key because it is one toggle, and are two
names because the palette should be able to say which direction you are
going.

---

## Composition

`spec/workbench.md` allows three forms and this is where the first one
gets its algebra.

**`Command` is a semigroup**, and `andThen` is `++`:

    instance Semigroup Command where
        (++) a b = Then a b

    skip : Command

So a macro, a transcript and an undo group are each a fold of a list of
commands, and the laws a reader needs are ones they already know.
`skip` is the identity; the prelude has `Semigroup` but no `Monoid`
class, so the identity is a named value rather than a method — worth a
`Monoid` if a second type ever wants one, and not worth it for this
alone.

**`repeat` is deliberately not here yet.**  It would be *n* copies over
a semigroup, which is a prelude operation rather than an editor one —
and until there are commands where doing a thing *n* times differs from
doing it once, it helps nothing.  `repeat 4 play` is a toggle flipped
four times, which is nothing.  The commands where it would earn its
place are **motions**, and motions belong to whatever owns the cursor.
When they arrive, `repeat` comes with them, from the prelude.

---

## What is not here, and why

* **No `save`.**  `apply` saves; `audition` does not.  Saving without
  rebuilding has no meaning for a live instrument, and offering it would
  invite a state where the file and the sound disagree.
* **No bank or routing commands.**  The plugin panel draws the
  note-routing matrix as a grid and that is chrome, not a verb — the
  editor should draw it the same way.  `listen`/`deafen` exist because
  *which bank hears the keyboard* is a decision, and a decision is a
  command; the grid is a picture of the decisions.
* **No file switching, no reference browser, no vim layer** —
  `spec/workbench.md` §"What is deliberately not here" has these and the
  reasons.

---

## The names

camelCase, because that is what gestate uses everywhere else.
`loopAll` reads slightly oddly in a palette where `loop all` would be
more natural, and consistency with the language wins: these are
declarations in a `.ges` file, and a reader who has seen `mkSig` and
`lowpassSvf` should not have to learn a second convention to read the
editor's.

---

---

## One gap, found while writing this

A constraint may name a class that does not exist:

    f : (Nonsuch a) => a -> C          -- accepted

Nothing resolves the name where the signature is written, so a typo —
`FromMidi`, `FormCC` — is a constraint that constrains nothing,
silently.  **Use sites are checked**, which is why this is small rather
than serious: `listen` on a bank whose payload has no `FromMIDI`
instance really is refused, `No instance for FromMIDI Int`, which is the
whole point of putting it in the type.  What is missing is the check
that the class in the signature is a class at all.  `fixme.md` F100.

---

## Acceptance

1. Every command in `gestate/command.ges` has a type, a sentence and a
   handler; nothing is implemented that is not declared, and nothing
   declared is unimplemented.  Held by `test_session.py`.
2. A command's arguments come from its type, so the palette can offer
   the right thing without a second table.
3. `set` on a knob of the wrong type does not typecheck — the refusal is
   the checker's, not a sentence.
4. Every key names a command.
5. `find` accepts text that is not a name; `goto` accepts only names.
