# relational-model — the format is a relation, so hold it to what relations learned

    status   open
    because  "What I am seeing is a data format.  I have wanted a
             relational data format." — Henri, 2026-09-10, looking at
             examples/audio/arc.notes and untitled.desk.  And, the same
             hour: "Since we do a relational format, lets do it
             properly."  The format already is one — `gestate/facts.ges`
             says a document is facts with a key per kind — and nobody
             has yet held it to what fifty years of relational practice
             paid to learn.  Rediscovering those lessons costs the months
             the method is trying to compress; reading them costs a day.
    asked    Henri, 2026-09-10 — "write these scars into a
             card:relational-model.md and create that card … I will
             continue this discussion later."  Then: "actually, write
             everything you told me into that card."
    see      gestate/facts.ges — a document is facts, declared in the language
             gestate/notes.ges — the three kinds a `.notes` has, and their keys
             gestate/notes.py — the parser, where every integrity rule lives today
             doc/notes/notes-on-the-model.md §"The relational model as the candidate"
                 — his 09:45 line and the four failure modes
             card:gui-is-difficult.md §"The document, decided" — where a
                 document became facts, 2026-09-09
             doc/memory/identity-is-the-models-key.md — a note's identity is
                 its content, the natural-key decision
             doc/memory/henri-prior-tools.md — mide's UI was datalog
             spec/data.md — Datafun with seminaïve evaluation, the
                 incremental engine the tree already runs
             vision.md §"What gestate won't be" — *plain files you can read
                 without it*, which is what a text relation is for
             card:gex-sheet.md §"Added 2026-09-10" — the same rules carried
                 to the sheet, where the schema travels in the file

## What this is, what it is not, and when it runs

**A reading of the `.notes` and `.desk` formats as relations**, against
the lessons relational practice paid for — Codd's model, what SQL did
to it, and the assert/retract branch (Datalog, Datomic, *Out of the Tar
Pit*) that matches what Henri said he wanted.  The output is the list of
scars below: each is a lesson somebody else paid for, the place it
lands in this format, and what practice did about it.

**It is not a proposal to adopt a database**, an ORM, or the
entity-attribute-value shape — the last is named below as the thing to
refuse.  It is not a rewrite of the format; several of the scars are
already paid, and the card says which.  And it does not decide
anything: the decisions are his and are listed under §"Questions" with
a default and a trigger each, shaped so that a one-word answer lands.

**When it runs:** the format runs every time a `.notes` is parsed,
written, retuned, asserted into or retracted from, and every time the
roll draws one.  The scars land at those moments, and two of them land
only when a *second* writer or reader appears — which is the moment
relational practice says they always land.

**What done would look like.**  Every scar in the table has one of
three marks: *paid* with the place it is paid, *refused* with his word
and a date, or *built* with the test that holds it.  Eight scars, and
today the marks stand at

    paid 0 · refused 0 · built 0 · open 8

— the six already-paid lessons in §"Already paid" are not counted,
because they need no decision.

## The ask

Henri, 2026-09-10, opening the sitting:

> I am looking at examples/audio/arc.notes and untitled.desk right now.
> What I am seeing is a data format.  I have wanted a relational data
> format.  Could you recall what you know about relational model and
> it's implementation in practice?

After the recall (kept below in §"The relational model, recalled"):

> I recall, and searched for what guest fable told me: "Self-reliance
> on concepts is fine; self-reliance on lessons is expensive.  'Try
> things out' is in the vision and rebuilding a concept yourself is how
> you actually learn it — I won't argue against that.  But your own
> board method says measure the claim against the tree, and the
> equivalent here is: read why Nix chose content addressing, why EROS
> persistence resurrected bugs, why every powerbox looks the same —
> then build your own anyway.  Reading their post-mortems costs a day.
> Rediscovering them costs the months you're trying to compress.
> Borrow the scars, not the code."  .. so.  What lessons there are
> about relational data that we could apply in our format?

Then:

> write these scars into a card:relational-model.md and create that
> card.  Since we do a relational format, lets do it properly.  I will
> continue this discussion later.

> actually, write everything you told me into that card.

He continued the same day, in the evening.  On the five questions he
asked what the practice says, and where the declaration and its seven
constraints travel; then:

> I think the data should be normalized for use, is this a reasonable
> request?  I mean.  Sure..  The data can be displayed like it's shown
> in the file, today.  But it should reach the reader of that data
> normalized.

> yes. it goes to the card..  Also, show me how things would change in
> gestate/notes.ges and arc.notes if we did what we plan here?

Q6 and §"The sketch" are that evening's.

## The two files, read as relations

`arc.notes` is three kinds of fact.  `note` is a relation with a
natural key — `section bar voice at key` — and named attributes, 291
rows on his piece.  `section` is a relation headed by its name, with
one attribute that is a list.  `bpm` is a relation with an empty key,
which the model calls a nullary-key relation and everybody else calls
a global; `facts.ges` says *an empty key means at most one record*.
`untitled.desk` is four of those and nothing else — one tuple, no
identity.

The declaration in `notes.ges` already carries what Codd called the
structure: kinds, fields, domains (`Word | Number | Names`), keys, and
an order the file is written in.  What it does not carry is named in
scar 2.

## The scars

Each one: the lesson as practice paid for it, where it lands here, and
what practice did.  Numbers are from `examples/audio/arc.notes` on
2026-09-10 and the commands that produce them are beside them.

| # | the scar | where it lands | practice's fix | mark |
|---|---|---|---|---|
| 1 | a rename is a set edit | voice and section names are natural keys referenced by value from every note; the one-field-one-line law cannot rename one | one command, many lines, one log entry, one undo | open |
| 2 | integrity kept in the application is lost at the rewrite | seven rules live only in `notes.py`; the declaration has `Among` for *sort by a reference* and nothing for *the reference must resolve* | foreign keys and checks in the schema | open |
| 3 | content-keyed identity is git's rename-detection scar | a key-field edit renames the thing it edited; two snapshots cannot tell *moved* from *deleted and created* | the command carries the before and after keys; never derive continuity from two files | open |
| 4 | a list in a value has nowhere to hang a second fact | `voices melody,upper,…` works with one reader; a voice's colour, instrument or mute has no row to sit on | a `voice` kind, headed by name, with section and rank | open |
| 5 | the second writer skips the constraints | every write ends in the parser today, because the canonical rewrite parses the text back | keep it a rule in one sentence: no write path that does not reparse | open |
| 6 | schema change is the largest operational pain | adding a `May` field is free; renaming a field or changing a key rewrites every file that exists; `.desk` carries no declaration beside it | never rename, never reuse a name for a new meaning; only add and deprecate | open |
| 7 | the generic record defeats the types, the checks and the eye | the temptation to let `note` carry arbitrary pairs when a new attribute is wanted | one kind, one line, named fields — and refuse EAV in text | open |
| 8 | row-at-a-time is how a set edit becomes thirty undo steps | the one primitive read today rewrites one field of one line | a command is a predicate and an update, applied and logged and undone as one | open |

### 1. A rename is a set edit, and the format has no set edit

Voice names and section names are natural keys, referenced by value
from every note that uses them.  SQL has cascade-on-update for exactly
this, and nobody uses it, because keys are not supposed to change —
and then people rename anyway, and the rename is a script.  The
one-field-one-line law (`spec/north_star.md`) cannot rename the melody
voice: the name is in the section's list and in every note.

    grep -c "voice melody" examples/audio/arc.notes     → 123
    grep -c "section A "  examples/audio/arc.notes     → 89

Practice's answer is not a surrogate id.  It is a rename that is one
command, many lines, one log entry and one undo.  The same shape covers
transpose-a-selection, and scar 8 is what happens without it.

### 2. Integrity kept in the application is lost at the rewrite

Codd made integrity one third of the model and SQL put foreign keys in
the schema.  Every system that kept them in application code instead
got orphan rows the day a second writer appeared.  The tree's stated
direction is that `notes.ges` becomes the one source and `notes.py`
stops being what runs (`card:gui-is-difficult.md` §"The document,
decided").  Today these rules live only in the parser, in `_note`:

- a note's `section` must name a section of this file
- its `voice` must be one of that section's `voices`
- `bar` is within the section's `bars`
- `at` is within the bar, which is `beats × 96` ticks
- `len` is at least one tick
- `key` is a MIDI key number, 0–127
- `vel` is one of the named levels, and `spell` must agree with `key`

The declaration has `Among "section" "section"` for *order a note by
where its section stands* and nothing that says *a note's section must
exist*.  When the Python stops running, those seven rules need a place
to have been declared, or `test/test_facts.py`'s parity is the only
thing that remembers them — and a parity test against a parser that is
gone holds nothing.

### 3. Content-keyed identity is git's rename-detection scar

A note's identity is its content (`doc/memory/identity-is-the-models-key.md`),
so an edit to a key field changes the name of the thing it edited.
Two snapshots of the file cannot tell a moved note from a deleted note
plus a new one; git meets the same problem with content-addressed blobs
and answers it with a similarity heuristic, which is the cost of
content addressing.  The place a note's continuity actually exists is
the command that moved it.  So undo, *selection follows the moved
note*, and any reference to a note from outside the file must carry the
before-key and the after-key, and never be derived from two files.

The tree already has the log (`sessionlog.py`); the scar is the
temptation to reconstruct from the files instead.  And prose attached
by adjacency (F200) is a second identity by *position*: it rides along
only because the writer moves it, and a reader that sorts without the
writer's rule strands it.

### 4. A list in a value has nowhere to hang a second fact

`voices melody,upper,middle,lower,bass` breaks first normal form on
purpose and it works, because the format has one reader and that reader
knows the list.  The comma-separated column is the most cited relational
anti-pattern for a reason that has nothing to do with purity: it is fine
right up until the second attribute.  The day the roll wants a voice's
colour, instrument or mute flag, there is no row to put it on.  The
relational form is a `voice` kind, headed by its name, with its section
and its rank — and `Along` already knows how to order a note along such
a thing.  Same for `manner accent,staccato`, at a smaller cost, since
nothing hangs off a manner.

### 5. The second writer skips the constraints

Every relational shop got its bad rows from the batch job that bypassed
validation.  Today every write path in `notes.py` ends in the parser:
`retune` rewrites bytes and then `canonical` parses the text back and
refuses what the parser refuses.  That is the rule to keep, in one
sentence, wherever a new writer is built — the roll, a `.ges` program,
a shell script: **nothing writes a `.notes` that does not read it
back.**

### 6. Schema change is the largest operational pain

Named fields and `May` buy most of the fix: a new optional field costs
nothing and every old reader ignores it.  Renaming a field, or changing
a key, is a rewrite of every file that exists, and the tree's own files
are the small part — his pieces are the large part.  The rule protobuf
and Datomic both arrived at is: never rename, never reuse a name for a
different meaning, only add and deprecate.  A `.notes` has its
declaration beside it, in the `.ges` that includes it, so a reader that
has moved on can still tell what an old file meant.  A `.desk` carries
no declaration anywhere; its reader is the only thing that knows what
`line`, `column`, `zoom` and `seed` mean.

### 7. Do not go generic

The entity-attribute-value shape is where a relational design goes when
it wants to stop declaring kinds: a `fact subject attribute value` line
that can say anything.  In SQL it is the anti-pattern that defeats the
optimizer and the type system; in a text file it defeats the eye as
well.  Datomic gets away with exactly this shape by keeping four sorted
indexes over the datoms and never showing a person the raw store.  One
kind, one line, named fields is the right middle for a file a person
reads, and the temptation to refuse is letting `note` carry arbitrary
pairs the day a new attribute is wanted — that day is scar 4's, and its
answer is a new kind.

### 8. Set-based, not row-at-a-time

The oldest performance scar in relational practice — *row by agonising
row* — is also an undo scar: a transpose of a selection done as thirty
single-field edits is thirty log lines and thirty undo steps.  The
relational form is one statement, `update note set key = key + 2 where
section = A and voice = melody`.  A command is a predicate and an
update, applied as one unit, logged as one line, undone as one.  The
one primitive read today, `retune`, is one field of one line; whether
a set form exists elsewhere was not checked this sitting, and
`scorebox.transposed` is the first place to look.

## Already paid

Six lessons the format has already paid for, named so that nobody
re-learns them:

- **Restrict, not cascade.**  Retracting a section a note still names is
  refused in the parser's own words, and nothing is written.  Every
  database made this choice after cascade deletes lost somebody's rows.
- **Absent is silent, not false.**  A section without `key` or `mode`
  makes `outside` say nothing rather than guess.  SQL's three-valued
  logic is the scar this avoids: a check that reads a null and quietly
  drops the row.
- **A canonical order, so a diff is a fact diff.**  The file is written
  sorted by its declared order; Dolt's finding is that with a key a diff
  is a row diff and merges are tractable, and without one it is text.
- **The bag does not leak.**  A doubled note is allowed in the file and
  refused at the gesture; retraction by key takes both, so no reader
  keyed by a dict silently loses one while the renderer plays it.
- **History outside the record.**  No `created_at`, no audit table; git
  and the session log carry time.  Every relational application that
  bolted timestamps onto rows later wished it had event-sourced.
- **Constraints in one parser, and the writer reparses.**  Scar 5, paid
  today; listed there because it has to be paid again by every writer.

And one that is decided rather than paid: **natural keys**, with the
eyes open.  A note is what it says, not a number; the cost is scar 3,
and the tree took it on 2026-09-08.

## Questions

Each shaped with a default and a trigger, so that a one-word answer
lands — `doc/memory/decisions-arrive-shaped.md`.  None answered yet;
he said he would continue.

**Q1 — rename.**  Is a voice or section rename a command the format
owes, or do names never change?  *Default:* a set command, one log
line, one undo, refused when the new name is taken.  *Trigger:* the
first time he renames a voice in a piece by hand and counts the lines.

**Q2 — where the seven rules live.**  When `notes.ges` is the one
source, do the referential and range rules go into the declaration (a
`Refers` beside `Among`, a range on a `Number` field), or stay in code
held by a parity test?  *Default:* the reference rules into the
declaration, since `Among` already names the same reference; the range
rules stay code until a second kind needs them.  *Trigger:* the commit
that makes the parser read `notes.ges` instead of its own tables.

**Q3 — voice as a kind.**  A `voice` record with section and rank, or
the list until it hurts?  *Default:* the list, until the second
per-voice attribute is wanted.  *Trigger:* the first per-voice fact —
colour, instrument, mute — that has nowhere to go.

**Q4 — the `.desk` declaration.**  Does a `.desk` get a kinds
declaration, and where does it live?  *Default:* leave it; four bare
singletons and one reader.  *Trigger:* a second reader of a `.desk`, or
a fifth line.

**Q5 — the set form.**  Is there a set-shaped edit already, and if not
is it the notes editor's data path or this card's?  *Default:* look
first (`scorebox.transposed`), and if absent it belongs to
`card:notes-editor.md`'s data path, with this card holding the shape.
*Trigger:* the first multi-note gesture the roll gets.

*Looked, the same evening.*  There is none.  `scorebox.transposed`
(`gestate/scorebox.py:1025`) replaces one atom's characters, byte-exact,
and `notes.retune` is one field of one line.  So the default's second
half stands: the data path is the editor's, the shape is here.  Two
things practice adds to the shape.  A uniform transpose keeps every
note's place in the sort, because `key` is the last sort field, so a
set transpose is still byte-exact with no reflow; a set time-move
reorders lines and is not.  And the log entry carries the row images,
before and after per note, grouped as one — never the predicate.
Statement-based logs were MySQL's scar, non-deterministic on replay;
row-based is the one that survived.  That is scar 3's before-key and
after-key, arrived at from the other side.

**Q6 — normalized for use.**  His ask, 2026-09-10 evening, quoted in
§"The ask": the file stays as it is shown, and the data reaches a
reader normalized.  It has a name in practice — ANSI/SPARC's three
schemas, 1975: the external form for the eye and for git, the
conceptual form a program queries, the physical form underneath — and
nobody has argued for the opposite since.  Measured against Codd's
information principle, what a reader gets today (`notes.NotesFile`)
carries facts four ways the model forbids: **by nesting** (a section's
voices are a tuple inside the record), **by encoding** (manners are a
bitmask), **by position** (every record carries its line number as a
field), **by adjacency** (prose rides on the record below it, F200).
*Default:* yes — the relations of §The sketch below, derived from the file
at every read, the file staying the one source; the line number and
the prose become a derived index and a keyed relation, dropped and
rebuilt at every write.  Held the way `declare-parity-derive` says:
declared, held to `NotesFile` on `arc.notes`, and then the record
classes become a view over them or go.  *Trigger:* already met, by his word the same evening, quoted in
§The ask: it goes to the card.  *What it moves:* Q3 half dissolves, the
reader gets a `voice` relation with a rank before the file needs a
new kind; Q2 gets its home, since a reference rule over relations is a
subset test and one line of Datafun; Q5's command is an update on a
relation, projected back onto the file by the writer.  *Two
cautions:* a reader usually wants the joined form — the performer
wants an absolute tick — and that is a view, derived and never stored;
and the file must stay the source, because the day the relations are
the source and the file is a print, git stops being the history.

## The sketch — what changes where

His ask: *show me how things would change in gestate/notes.ges and
arc.notes if we did what we plan here.*  "What we plan" is the
defaults of Q1–Q6 as they stand; where a trigger would change the
picture it is shown after.  This is a sketch in the tree's own
vocabulary (`facts.ges`' forms and the comprehension syntax of
`examples/gui/patchbay.ges`), not a design: the names are placeholders
and the language is his.

### `examples/audio/arc.notes` — zero lines change

That is the point of Q6, and it is worth saying as a number:

    0 of 322 lines change

The file is the external form and it stays.  Its named fields on every
line are the denormalization that makes it readable with no schema
beside it, and that is kept on purpose.  Two events would touch it:

- **Q1 fires** (a voice is renamed): 124 lines change and the schema
  does not — `grep -c "voice melody"` is 123 and the section list is
  one more.  The command that does it is one log entry and one undo.
- **Q3 fires** (a second per-voice fact, say an instrument): the
  section line keeps its list, because the list is the ordering
  relation and practice never found a better one, and a `voice` kind
  arrives beside it carrying the attributes —

      section A  key D  mode lydian  bars 8  beats 4  voices melody,upper,middle,lower,bass
      voice melody  section A  instrument piano
      voice bass    section A  instrument contrabass

  A voice line naming a voice its section's list does not hold is a
  reference rule, derived the same way as the note's.

### `gestate/notes.ges` — three additions, and where the seven rules go

The kinds stay as declared.  What is added is the answer to Q2 and
Q6, in three parts, each held by `test/test_facts.py`'s parity against
`notes.py` on `arc.notes` while both exist.

**1. Domains** (`facts.ges` gains two value forms; three of the seven
rules move here).  A field that is really a key number or a dynamic
says so, and the refusal is derivable from the domain rather than
written in the parser:

    # facts.ges
    Value := Word | Number | Names | Range Int Int | OneOf (List Text)

    # notes.ges
    levels : List Text
    levels = "ppp" :: "pp" :: "p" :: "mp" :: "mf" :: "f" :: "ff" :: "fff" :: Nil

    manners : List Text
    manners = "staccato" :: "accent" :: "portamento" :: Nil

    noteFields = Field "section" Word Must
        :: Field "bar" Number Must
        :: Field "at" Number Must
        :: Field "len" (Range 1 4294967295) Must        -- rule: len ≥ 1
        :: Field "voice" Word Must
        :: Field "key" (Range 0 127) Must               -- rule: a MIDI key
        :: Field "spell" Word May
        :: Field "vel" (OneOf levels) Must              -- rule: a named level
        :: Field "manner" Names May                     -- OneOf manners, each
        :: Nil

**2. References** (two of the seven; nothing is added).  The two
reference rules are already in the file, read the other way: `Among
"section" "section"` cannot order a note by where its section stands
unless the section exists, and `Along "voice" "section" "voices"`
cannot order a voice along a list it is not in.  So the reference
rules are *derived* from the sort declaration —

    # facts.ges: a sort that names another record is a reference it requires
    refersOf : Kind -> List Refer
    refersOf (Kind _ _ _ _ sorts) =
        for (s in sorts) (case s of
            Among field kind      -> {Refer field kind}
            Along field kind list -> {Within field kind list}
            By _                  -> {})

— and the check that this derivation agrees with `notes.py`'s two
refusals is the parity test's next row.  Practice's warning about
implicit constraints is noted: a sort leaking meaning is exactly the
row-order scar.  The answer is that the derivation is written down,
in the declaration language, and enumerated for checking, which is
what makes it explicit.

**3. What a reader gets** (Q6; and the last two rules, which no schema
holds, become rules over it).  One derivation from a kind: the key
plus every `Must` word-or-number field is the base relation; each
`May` field is a relation of its own, so absence is no row; each
`Names` field is a relation with a rank.  Written out for `.notes`, so
a reader can see what the derivation says:

    #: What a reader gets.  Nothing here is carried by nesting, encoding,
    #: position or adjacency; the file is the source and these are read
    #: from it every time.
    type NoteKey = (Text, Int, Text, Int, Int)        -- section bar voice at key

    note    : Set (NoteKey, Int, Text)                -- len vel
    spell   : Set (NoteKey, Text)                     -- absent is no row
    manner  : Set (NoteKey, Text)                     -- one row per manner
    section : Set (Text, Int, Int)                    -- name bars beats
    tonic   : Set (Text, Text)                        -- section key, when said
    mode    : Set (Text, Text)                        -- section mode, when said
    voice   : Set (Text, Int, Text)                   -- section rank name
    bpm     : Set Int                                 -- at most one

    #: Not the model — the index.  Dropped at every write and rebuilt at
    #: the next read; the byte-exact writer looks a key up here.
    line    : Set (NoteKey, Int)
    prose   : Set (NoteKey, Text)                     -- keyed, not adjacent

The two cross-row rules, and the one that needs a function, are what
SQL called assertions and never implemented; here they are one
comprehension each over the relations above, and the set they produce
is what the parser refuses today in words:

    overBars  = {k | (k, _, _) in note, (s, b, _, _, _) = k,
                     (s', bars, _) in section, s == s', b > bars}
    pastBar   = {k | (k, _, _) in note, (s, _, _, t, _) = k,
                     (s', _, beats) in section, s == s', t >= beats * 96}
    misspelt  = {k | (k, sp) in spell, (_, _, _, _, key) = k,
                     not (spells sp key)}

    refused   = overBars \/ pastBar \/ misspelt

**The number that says the declaration holds:** `refused` is empty on
`arc.notes`, and every fixture `test_drawnscores.py` refuses today puts
its key in it.  That is the parity row for these three, and the day
`notes.py` stops running it is the only thing that remembers them.

**Where the seven rules end up**, against scar 2's list:

| rule | today | after |
|---|---|---|
| `section` names a section | `_note` | derived from `Among` |
| `voice` is in that section's `voices` | `_note` | derived from `Along` |
| `bar` within the section's `bars` | `_note` | `overBars`, a rule |
| `at` within the bar | `_note` | `pastBar`, a rule |
| `len` at least one | `_note` | domain `Range 1 …` |
| `key` 0–127 | `_note` | domain `Range 0 127` |
| `vel` named; `spell` agrees with `key` | `_note`, `Note.__post_init__` | domain `OneOf levels`; `misspelt`, a rule |

### `untitled.desk` — one line, when Q4's trigger moves

Q6's derivation is one rule over kinds, and a rule checked against one
document is checked against a witness.  A `desk.ges` of four `Bare`
singletons is the second document, and it is four lines:

    deskKinds = Kind "line" (Bare "line") (Field "line" Number Must :: Nil) Nil Nil
    :: Kind "column" (Bare "column") (Field "column" Number Must :: Nil) Nil Nil
    :: Kind "zoom" (Bare "zoom") (Field "zoom" Number Must :: Nil) Nil Nil
    :: Kind "seed" (Bare "seed") (Field "seed" Number Must :: Nil) Nil Nil :: Nil

The `.desk` file itself does not change either.

## Extended to `.gex` — 2026-09-10

His ask, the same evening: *"I'd want this to be extended to
card:gex-sheet.md and in that case the .gex could carry the schema
along it, so that .gex files can stand on their own.  Would that be
reasonable?"*  It is, and the reason is the opposite of §"Where the
schema travels" above, so the rule is worth one sentence here:

**The schema travels in the file when it is the document's own, and
in the catalog when it is shared.**  A `.notes` shares its kinds with
every piece, so `notes.ges` is its catalog and a copy per piece is one
fact stored thirty times.  A sheet's columns are the user's, so each
sheet is its own schema and the declaration has nowhere else to live.
Database versus Avro, by the same criterion.  The form is Codd's
fourth rule — the catalog as relations, in the same grammar as the
data — with `kind` and `field` as the two bootstrap kinds `facts.ges`
fixes, which is Datomic's schema-as-datoms.  And read relationally, a
sheet is kinds with fields and a formula column is a view, not a
relation from address to expression, which is scar 7's shape.  The
whole of it is on `card:gex-sheet.md` §"Added 2026-09-10", with the
one decision it creates: carried or beside, never both.

## The relational model, recalled

What was said in the sitting before the scars, kept whole because he
asked for everything.  It is background, not work: the scars above are
what to act on.

### The model, as Codd stated it

Codd's 1970 paper has three parts, and practice usually remembers only
the first.

- **Structure.**  A relation is a set of tuples over named attributes,
  each drawn from a domain.  Sets, so no duplicates and no order.
  Values only, so no pointers.  Two facts are related by sharing a
  value, never by a link.
- **Integrity.**  A key identifies a tuple.  A foreign key is a value
  that must exist as a key elsewhere.  Everything else about integrity
  is a constraint you write down.
- **Manipulation.**  The algebra: select, project, join, union,
  difference, rename.  It is closed, so a query's result is a relation
  and can be queried again.  Views are stored queries.

The rule under all three is the **information principle**: all
information is carried as values in relations, and nothing is carried by
order, by position, by nesting, or by structure the schema does not
name.  His argument was against the navigational databases of the time,
where the program walked pointers.  Data independence was the prize —
the program says what, the engine decides how, and the physical layout
can change without the program changing.

Normal forms are the quality taxonomy that comes with it.  First normal
form forbids a list inside a value.  Second and third say every
attribute depends on the key, the whole key, and nothing but the key.
Their purpose is update anomalies: a fact stored twice can diverge, and
a fact that lives only as an attribute of another vanishes when that
other is deleted.  Date's sixth normal form takes it to the end — every
non-key attribute gets its own relation, and optional attributes
disappear because absence is just no row.

### What practice did to it

SQL is not the relational model, and the divergence is the whole story
of the practice.

- **Bags, not sets.**  Duplicates are allowed.  Column order and row
  order leak into meaning; every application that relied on row order
  without saying so broke when the plan changed.
- **Nulls.**  Three-valued logic, the wart Codd himself added and Date
  and Darwen spent the *Third Manifesto* arguing out.
- **No relation-valued attributes** in most engines, so nesting is faked
  with joins or with a list in a string — which is `voices`.

Under the language the engineering is stable and well understood.  The
relation is logical.  The storage is a heap plus indexes, usually
B-trees, and **an index is a derived structure that can be dropped and
rebuilt** — the same lesson the tree wrote as *identity is the model's
key, never the picture's index*.  A query parses to the algebra, an
optimizer picks join order and access paths by estimated cost
(Selinger, 1979, still the shape of every one), and the plan runs
against the indexes.  Transactions add isolation, and multiversion
concurrency gives a reader a consistent snapshot.  Most of the code in a
database is optimizer and storage; the model itself fits on a page, and
at a few thousand rows a scan beats every index.

History is what plain SQL leaves out: an update is in place and the old
value is gone.  Temporal extensions and the 2011 SQL standard put it
back with valid-time and transaction-time columns.

### The branch that matches what he is doing

Assert and retract as the two verbs comes from a different line than
SQL, and it is the line worth recalling.

- **Datalog.**  Base relations plus rules that derive more relations.
  Seminaïve evaluation makes recursion cheap by only working on what
  changed, and the tree already has it in Datafun (`spec/data.md`).
  Retraction is the hard part: delete-and-rederive (Gupta, Mumick,
  Subrahmanian, 1993) handles recursive rules, derivation counting
  handles the non-recursive case exactly, and differential dataflow
  (McSherry) and DBSP (Budiu et al., 2022) are the modern answer —
  incremental maintenance for arbitrary queries with a theory under it.
  This is failure mode 3 of `doc/notes/notes-on-the-model.md`, and the
  card there found the tree had already answered it at both ends.
- **Datomic.**  The nearest existing thing to his sentence.  A fact is
  a datom of entity, attribute, value, transaction, and a flag for
  assert or retract.  The database is an immutable value, time is a
  dimension, and the query language is Datalog.  It works where the EAV
  pattern in SQL fails because it keeps four sorted indexes over the
  datoms (EAVT, AEVT, AVET, VAET) and has no optimizer to defeat.  Its
  schema is per attribute, which is sixth normal form arrived at from
  the other side.
- ***Out of the Tar Pit.***  Moseley and Marks, 2006.  Essential state
  is relations, derived state is pure functions of it, and everything
  else is accidental and kept out.  It is almost exactly his 09:45 line
  in the notes on the model.
- **Eve, LogicBlox, Bloom.**  Eve tried the UI as a query over a record
  store and stopped in 2018; its lessons were performance under
  interaction and where transient state lives, the first two failure
  modes the notes already list.  LogicBlox shipped whole business
  applications as relations with incremental maintenance.  Bloom is the
  distributed version and gives the CALM result — monotone programs need
  no coordination.
- **Dolt.**  Git for tables.  Its finding is the one behind the sorted
  notes file: with a primary key a diff is a row diff and merges are
  tractable; without one it is a text diff.
- **mide.**  His own: `staves.ui` did a draggable staff as datalog
  rules, in 55 lines — `doc/memory/mide-staves-ui.md` — and the reading
  there was *take the property, not the rule language*.

### Where the model bites on these two files

The five places named in the first reply; the scars above are the
lessons behind them.

- **The list in a value.**  The section's voice list breaks first
  normal form on purpose.  The relational alternative is a voice
  relation with a rank attribute, and the tree already has that
  ordering idea as `Along`.  (Scar 4.)
- **Natural keys move.**  A note's identity is voice, tick, key, so
  moving a note changes its identity.  Surrogate ids are stable and
  meaningless.  This is the oldest argument in the field, and the tree
  took the natural side with its eyes open.  (Scar 3.)
- **Optional attributes.**  `manner` and `spell` are nulls.  Sixth
  normal form says make each a relation of its own, one row per accent.
  `May` is the pragmatic middle, and `outside`'s silence on an absent
  `mode` is the null rule done right.
- **Stored derived facts.**  A section's `bars` is derivable from its
  notes — unless it is a declaration that the section is eight bars even
  when bar eight is empty, which is what the parser treats it as.
  Declared and derived are different facts; here it is declared, and
  the parser holds notes to it, which is the right side of the line.
  `spell` is the other case: an authorial choice the key constrains, so
  it is a declared fact with a check, not a cache.
- **No history.**  The file has none, same as SQL.  Git and the session
  log carry it outside the relation, which is what event sourcing does
  too.
