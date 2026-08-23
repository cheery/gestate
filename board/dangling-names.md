# dangling-names — a name the tree cites and nothing defines

    status   blocked
    blocked  on a decision that is Henri's — which of three shapes, or
             none.  Asked 2026-08-21, and he asked for time to think.
    because  the A3 rule was written on 2026-08-18 and cited three days
             later under a name it did not carry; citation and
             definition shared no word, so grep could not join them and
             no check in this tree could have found it
    asked    Henri, 2026-08-21
    see      board/README.md §"One sheet, then depth" — where the A3
             rule actually lives, and now says so
             fixme.md F166 — two card citations rotted where the
             checker could not look
             doc/consent.md §"What the check cannot see" — the same
             honesty about a check's range, written for a register

## What this is about

**A named concept** — *the A3 rule*, *the earning test*, *the corner*,
*the way in*.  A phrase the tree uses as though it were defined
somewhere, in prose, with no id.

**What it is not:** a search problem.  `card:` ids, F-numbers, D-numbers
and `§"heading"` references are all checked already, and they are
checked because they have a **syntax**.  A named concept has none.

**When it bites:** when the citation and the definition use different
words.  Then there is no string in common and grep cannot help at all —
which is not a limitation of grep, it is the whole of the defect.

## The ask

*Henri, 2026-08-21, on being shown that the A3 rule had no home:*

> **"Olisikohan meidän syytä kehitellä tähänkin ratkaisu? git historiaa
> ei kukaan lue, ja grep on grep."**

## Found by looking

**The case that started it.**  `board/README.md` §"One sheet, then
depth" carries the rule, in Henri's own words, dated 2026-08-18.  Four
other places cite it as **"the A3 rule"** — `journal.md` for a visitors'
front page, `doc/notes/notes-on-deciding.md` for a decision brought to
the author, `notes-on-models-and-liveness.md` for the method itself,
`notes-on-the-return.md` in a list of the vocabulary.

Citation and definition had **not one word in common**.  It was found
because Henri asked where the rule was, which is a person noticing that
a name he expected to resolve did not.  That is not a repeatable
instrument.

**The size is not known, and one attempt to measure it failed.**  The
tree cites about thirty *"the X rule"* phrases.  A crude check —
does the phrase appear in a heading or a bolded lead — resolved three
of ten and said nothing for six.  **That result is evidence about the
regex, not about the tree**; the six may well be defined in prose.
Sizing this properly is part of the work, not a thing already done.

**Why it cannot be checked today.**  Every reference this tree verifies
has a shape a machine can pick out of prose.  Grep can find a word; it
cannot tell a *citation* from a *definition*, and it fails outright on a
vocabulary mismatch.  So the fix is not a better search — it is an
**address**, which is the move that already worked three times here.

## The decision

*Written as this tree's own decision contract —
`doc/notes/notes-on-deciding.md`, which is itself the A3 rule applied to
the author's attention.*

**The question:** how is a named concept made findable and checkable?

| | what | cost | what it buys |
|---|---|---|---|
| **A** | nothing; name it in the body when somebody notices | zero | 2026-08-21's fix, repeated by accident |
| **B** | `doc/terms.md` and a gate: one line per name → where it is defined | one page, one test | a cited name cannot rot silently |
| **C** | an id of its own, `rule:a3`, like `card:` and the F-numbers | a notation, a checker, and every existing citation edited | the machinery that already keeps cards honest |
| **D** | a gate that flags a name **cited in two or more documents and asserted in none** | one test, no notation, no list to maintain | it caught the real case, and stopped flagging it once fixed — see below |

**Default with a trigger:** undecided is **A**, and nothing breaks.  The
cost of deferring is one more such name, found by a person asking.

**Reversibility:** B is one file and one test, deleted in a minute.  **C
is not** — a notation spreads through the corpus and unpicking it is
larger than laying it down.

**Recommendation, marked as suspected: B, narrowed** — a glossary not of
every name but only of those **cited from more than one document**.
That is exactly the set where grep fails and where no reader holds the
mapping in their head; a name used inside one document is fine as prose,
because the reader is already standing in the definition.

**And the gate's range has to be stated where it is written.**  It can
check that a name **on the list** reaches its definition.  It cannot
notice a name that never reached the list — the same blind spot
`doc/consent.md` records about itself: *the register records that
consent was obtained; it cannot check that it was.*

## Questions

**Which shape — A, B or C?**  Henri, 2026-08-21: *"palataan asiaan kun
olen miettinyt sitä rauhassa."*  Open.

**If B: what counts as a name?**  The narrowing above says *cited from
more than one document*, which is checkable but is a proposal, not an
answer.

**Does the same hole exist for things that are not rules?**  *The
corner*, *the way in*, *the earning test* are all cited across documents
in exactly this way, and none of them was looked at while writing this.


---

## Measured, 2026-08-21

*Henri asked whether C could be investigated rather than chosen.  It
can, three ways, and running the first two produced a fourth option.*

### C has already been run once here

`card:` **is** option C, built in August, and `board/README.md` records
what it cost: *"Sixteen cards moved in the ten days this board existed,
and every one of those moves was a tree-wide rewrite that the suite
caught **after** the fact."*  F-numbers and D-numbers are the same move.
Three precedents, all of them working, and the price of the migration is
written down.  That is the cheapest study of C available and it needs
nobody's afternoon.

### The census — 88 candidates, 14 that cross documents

Names of the shape *the X rule / test / convention*, generic English
filtered out: **88** in the corpus, **14** cited from more than one
document.  Small enough that any of the three options is tractable, and
that is the number the decision was missing.

### The A3 case is a naming drift, not a forgetting

`git log -S` dates it exactly:

| | |
|---|---|
| **2026-08-18** | the rule is written, in Henri's words, as §"One sheet, then depth" |
| **2026-08-21** | it starts being cited as *"the A3 rule"* — three days later, in two commits |

Nobody renamed anything and nobody forgot to define it.  **A second
vocabulary grew over an existing rule** — the lean one this project
borrows from (`doc/notes/notes-on-the-return.md` lists *andon, gemba,
kaizen, A3* together), and the definition never learned the new name.

That predicts recurrence: any rule this project writes in its own words
may later be recognised as a known practice and start being cited by
**that** name instead.  It is not a lapse to be more careful about.

### Option D, and it validates

A gate needs no glossary and no notation if it can detect the shape
directly.  The A3 signature is a name that is **only ever referred to
and never asserted** — no heading carries it, no bolded lead, no
sentence of the form *the X rule is / says / means / restricts*.

Run against the tree at `5f42f68`, before the rule was named:

    EPÄILTY  placement rule    3 documents
    EPÄILTY  A3 rule           2 documents
    EPÄILTY  fixtype rule      2
    EPÄILTY  application rule  2
    EPÄILTY  transport rule    2
    EPÄILTY  drop rule         2

**It flags A3.**  Run against the tree now, with `**This is the A3
rule**` in place, A3 is gone and the other five remain.  So it detects
the real case and it responds to the real fix, which is the whole of
what a gate has to do.

**Five suspects are left**, few enough to hand-check rather than
automate away.

### What D cannot do, and it must be written beside it

* **It sees one shape.**  *the X rule / test / convention* only.  *The
  corner*, *the way in*, *the earning test* — the same class, invisible
  to this regex.
* **False negatives are silent.**  A rule asserted in a sentence the
  pattern does not cover reads as healthy.
* **It is a heuristic over English**, so it will accuse honest text, and
  the answer to an accusation has to be cheap or the gate gets muted.

### Two bugs in this measurement, recorded because a number without them is not a number

1. **The census excluded `A3` from its own motivating case.**  The name
   pattern required a lowercase first letter.  The one name the work
   existed for was not in the first run at all.
2. **`\*\*[^*]*` crossed newlines**, so any `**` earlier in a file made
   every later name read as *asserted*.  The first detector run reported
   one suspect where there are six; the result looked clean and was an
   artefact.

Both were found by checking the detector against a case whose answer was
already known — which is the only reason either was found.

---

## The five, and how to check them — a work order

*Written 2026-08-21 for a session that has not seen the rest of this
card's argument.  **Read only the section you are working and the files
it names.**  The reason this goes to a fresh session is that the
detector above was designed by a session that would then be scoring its
own idea; the evidence is worth more from somebody with no stake in it.*

### What you are doing

Five names are cited across documents and, as far as one heuristic can
tell, never asserted anywhere.  **Find out whether that is true of each
one.**  Nothing else.

### Do not

* **Do not fix anything.**  No new sentences, no definitions, no edits
  to `spec/`.  If a rule turns out to have no home, writing its missing
  sentence is a design decision and it belongs to Henri.
* **Do not decide whether the gate should exist.**  That is a separate
  question with a criterion Henri has not set yet, deliberately.
* **Do not aggregate.**  Report five verdicts, not a score.

### The five, and every site

    placement rule    spec/workbench.md:390 · board/README.md:433 · fixme.md:3825
    fixtype rule      fixme.md:789 · journal/2026-08.md:887
    application rule  fixme.md:883 · journal/2026-08.md:3697
    drop rule         spec/sown.md:21 · spec/dynamicscore.md:284
    transport rule    spec/dynamicscore.md:172 · journal/2026-08.md:4309

### For each name

1. Read the **section** each site sits in, not the line.  A grep line is
   not enough to judge this and the temptation to judge from one is the
   main way this goes wrong.
2. Write down **what you found first**, with `file:line`, and assign the
   verdict after.  The note is what Henri audits; the verdict alone is
   something he would have to take on trust.
3. One of three verdicts:

    | verdict | means |
    |---|---|
    | **genuine** | no sentence anywhere says what this rule *is*; it is only ever leaned on |
    | **asserted** | a sentence does say what it is, and the detector missed the shape — **quote that sentence** |
    | **not a term** | ordinary English the harvester over-collected |

### One confound, found while writing this

**`journal/2026-08.md` quotes other documents verbatim.**  Three of the
five have exactly one `fixme.md` or `spec/` site plus one journal site,
and the journal line may be *the same sentence quoted*, not an
independent use.  Check whether the two hits are one sentence appearing
twice.  If they are, the name never crossed a document boundary at all
and the harvester's "two documents" was an artefact.

This is a fact about the corpus and not a hint about any of the five.

### What to hand back

Five entries, each: the name, the verdict, the evidence with `file:line`,
and the quoted sentence where the verdict is **asserted**.  Append them
below this section under `## The five, checked` with the date.

### If you have a question

Ask it.  Henri is at another console and is the channel — a session
working this without a way to raise a question and be answered is the
arrangement this project has already ruled out.

## The five, checked — 2026-08-21

*Checked by a second session, from the work order above and the files it
names.  **Disclosure:** the work order asked the checker to read only its
own section; this session read the whole card before reaching that
instruction.  It is recorded because the point of a fresh reader is that
it has no stake in the detector, and a reader who has seen the detector's
argument is a weaker instrument than the one asked for.  Nothing below is
fixed, decided or aggregated.*

**One thing has to be said before the five, because it changes how they
read.**  The work order's site list is **incomplete for three of the
five**, and the four missing sites all existed at `5f42f68` when the
census ran.  See §"A third measurement bug" below.

---

### 1. `placement rule` — **genuine**, and the name covers two different rules

**What I found first.**  The three listed sites are not talking about one
rule.

*Sense A — a knob sits in the margin at the row of its own declaration:*

- `spec/workbench.md:390` — "A `knob` at `row` is drawn in the margin at
  that row: the placement rule survives the move".
- `journal/2026-08.md:5535` — "the knob's placement rule grown a height"
  (**not in the work order's list**).

*Sense B — the palette panel and its reference page go where the room is,
decided by the equator:*

- `board/README.md:433` — "`palette.rs:1175` had the placement rule
  built".  `palette.rs:1175` is the page-beside-the-panel code, and
  `card:peep-window.md` names the same address at line 50, as *"that
  placement"* — the F133 rule, not the knob's.
- `fixme.md:3825` — inside **F133**, which is about the palette panel:
  "the placement rule's other half, which the page had never heard of".

**No sentence anywhere says what "the placement rule" is.**  Both senses
*are* asserted — each under a different name:

- Sense A, `spec/liveaudio.md:941`: "**a knob beside every line that
  declares one** — placed by `audiospans`, not listed in a panel, which is
  what the placement was built for".  Also `spec/substrate.md:502`
  ("**Knobs are drawn rather than placed.**") and `spec/editor.md:91`
  ("the editor lays the widget in the margin beside the declaration").
- Sense B, `spec/workbench.md:624`: "**The equator decides the panel; the
  span decides the scroll**" — asserted, bolded, and named **the
  equator**.  `fixme.md:3814` and `:3820` call it *the equator rule* and
  *the equator placement* in the same entry that calls it *the placement
  rule* five lines later.

**Verdict: genuine.**  The name has no home; two homes exist under other
words.  This is the A3 signature exactly — a second vocabulary grown over
an existing rule — and here it has gone one step further, because the
second vocabulary is now covering **two** rules with one name.

---

### 2. `fixtype rule` — **not a term**

**What I found first.**  The two sites are one sentence written twice.

- `fixme.md:789` (F49) — "That matters beyond arithmetic: the fixtype rule
  takes `Cyclic n` for a finite type, and a `Cyclic 4` holding 6 would
  make `fix` promise a termination it could not deliver."
- `journal/2026-08.md:887` (the F49 entry) — "That is not just wrong
  arithmetic: the fixtype rule takes `Cyclic n` for a finite type, so a
  `Cyclic 4` holding 6 would make `fix` promise a termination it could not
  deliver."

Same clause, one connective changed.  **The work order's confound holds
here**: the name never crossed a document boundary.  A third instance of
the same phrase sits in code — `gestate/elaborate.py:627`, "would not be
the finite type the fixtype rule takes it for."

**And it is not a name.**  `fixtype` is a defined formal term with a
grammar and a checker; *"the fixtype rule"* is ordinary technical English
for the subgrammar rule at `fix`, the way `journal/2026-08.md:104` writes
it in the plural — "eqtype/semilattice/fixtype rules" — as one row of a
pipeline diagram.  The thing it leans on is asserted in five places:

> `spec/syntax.md:647` — "`fix` takes a `Box (L ~> L)` where `L` is a
> **fixtype**: a set of *finite* eqtypes"

> `gestate/subgrammar.py:102` — "A fixtype is a set of finite eqtypes, or
> a tuple of those."

Also `spec/errata.md:80` (the grammar), `spec/errata.md:97`, and
`doc/manual.md:550` ("**The type must be a *fixtype*** — a semilattice
with no infinite…").

**Verdict: not a term.**  The harvester collected an adjective, and the
one boundary it crossed was a quotation of itself.

---

### 3. `application rule` — **not a term**

**What I found first.**  Same confound, same shape.

- `fixme.md:883` (F30) — "`unify` is symmetric, but its message is not —
  it says "expected `b`, got `a`" — and the application rule in `infer.py`
  called it `(expected, actual)`."
- `journal/2026-08.md:3697` (the F30 entry) — "`unify` is symmetric but its
  message is not, and the application rule called it `(expected,
  actual)`."

One sentence, twice, minus the `in infer.py`.  **The confound holds.**

**And there are two more sites the list does not have, for a *different*
rule** — the ϕ/δ transform's row for `e f`:

- `fixme.md:154` — "the application rule in the same table settles it"
- `spec/data.md:175` — "Both halves are the ordinary application rule"

That one is **asserted, with an address given in the citation itself**:

> `spec/data.md:171` — "| `e f` | `ϕe ϕf` | `δe [ϕf] δf` | ϕ is ordinary
> `EAp`. δ is `EAp(EAp(δe, box(ϕf)), δf)` …"

`fixme.md:154`'s *"in the same table"* points straight at §I.4's codegen
table.  So the corpus has two unrelated "application rules" — the typing
rule at `gestate/infer.py:422`, and §I.4's transform row — and both are
ordinary English for *the rule for applications*, of the same kind as *the
lambda rule* or *the case rule*.

**Verdict: not a term.**

---

### 4. `drop rule` — **genuine**, and the definition is 90 lines above one of its own citations

**What I found first.**  The two sites are, again, one sentence:

- `spec/sown.md:21` — "Content beyond the declared span is clipped, and
  said so, in the drop rule's own vocabulary: a section that outruns its
  box rejoins nothing."
- `spec/dynamicscore.md:284` — "Content a decision produces beyond its
  declared span is clipped, and said so, in the drop rule's own
  vocabulary: a section that outruns its box rejoins nothing."

Three words inserted, otherwise identical.  Both landed 2026-08-10
(`89e325a`/`9aa8dce` into `dynamicscore.md`, `82d8fde` into `sown.md`).
**This is the confound in a form the work order did not anticipate** — not
a journal quoting a spec, but one spec file copying a sentence into
another.  The name still only ever occurs inside that one sentence.

**The rule is stated, unnamed, in the same file as one of the citations**,
ninety lines above it:

> `spec/dynamicscore.md:193` — "if production resumes, events whose beats
> have passed are **dropped, and said so** — a section that lost its place
> rejoins at the current bar, it does not play the missed bars fast."

The shared word *rejoins* is what ties the citation to it.  And the same
file names that mechanism **twice more, differently**:
`spec/dynamicscore.md:14` calls it **drop-and-report**;
`spec/dynamicscore.md:47` calls it **the stall-and-drop rules**.

**Verdict: genuine** — three names for one mechanism, and the definition
carries none of them.

**Where this verdict is contestable, stated rather than hidden.**  The
work order's `asserted` reads *"a sentence does say what this rule is"*,
and `:193` does.  Its `genuine` reads *"no sentence anywhere says what
this rule is"*, and that is false here.  I have called it genuine because
the A3 precedent turns on the **name**, not the content: the A3 rule was
written on 2026-08-18 and still flagged, and the fix was to attach the
name to the existing sentence, not to write a new one.  If the criterion
is the content, this is `asserted` and the sentence above is the quote.
**The two readings disagree on this name and on `placement rule`, and the
work order does not say which one it means.**

---

### 5. `transport rule` — **asserted**

**What I found first.**  The listed sites are both citations —

- `spec/dynamicscore.md:172` — "the allocator exists, the Rust allocator
  exists, the transport rule exists"

— but a **third site the work order does not list** is a definition, and
it names the rule in the same sentence:

> `spec/export.md:22` — "Self-playing synths export today
> (`dubgate.clap`, `violin.clap`), under one transport rule for every
> plugin: **it plays while the transport runs, or while a note does.**"

Present at `5f42f68`, at that same line number.  The three sentences after
it give the rest — silence while the timeline is stopped, the rising edge
rewinding to the top, knobs surviving the rewind, a ringing voice keeping
the render alive.

**And the second listed site asserts it too**, in a parenthesis:

> `journal/2026-08.md:4309` — "*rewind is free*, which became the
> transport rule (stop is silence, play is the piece from its top, two
> plays are one performance)."

**Verdict: asserted.**  The detector missed it twice.  In `export.md` the
determiner is **"one transport rule"**, not *"the"*, and the assertion
follows the name rather than carrying it; in the journal the assertion is
in round brackets, not bold.

---

### A third measurement bug — the site list undercounts documents

Four sites are missing from the work order's list, all present at
`5f42f68`:

    placement rule     journal/2026-08.md:5535   "the knob's placement rule"
    application rule   spec/data.md:175          "the ordinary application rule"
    application rule   fixme.md:154              "the application rule in the same table"
    transport rule     spec/export.md:22         "one transport rule for every plugin"

Three of the four share one shape: **something stands between the article
and the name** — a possessive (`the knob's …`), an adjective (`the
ordinary …`), or a different determiner (`one …`).  A harvester matching
roughly *"the ⟨word⟩ rule"* sees none of them.  `fixme.md:154` is the
exception and would be a plain match; I do not know why it is absent.

**Why this is the bug that matters.**  The two bugs already recorded on
this card cost the census a name and a run.  This one attacks the
**criterion**.  "Cited from more than one document" is the proposed
narrowing for B and the trigger for D — and it is computed from a site
list that cannot see a name with an adjective in front of it.
`transport rule` was scored on two documents and has three; the third is
the one holding the definition, which is why it was flagged at all.  A
census that misses the defining site systematically over-reports
`EPÄILTY`.

I did not fix the harvester, and I have not re-run any census; this is
what four hand-checked names showed, found the same way the first two bugs
were — by checking against cases whose answers were already known.

### Tally, for reading, not for scoring

    placement rule     genuine       (two rules under one name; both asserted elsewhere, unnamed)
    fixtype rule       not a term    (+ confound: one sentence, twice)
    application rule   not a term    (+ confound: one sentence, twice)
    drop rule          genuine       (+ confound: one sentence copied between two specs)
    transport rule     asserted      (spec/export.md:22, and again in the journal)

**Three of the five confirm the work order's confound**, and a fourth
found it in a form it did not predict.  Of the five names the detector
flagged, **one** — `placement rule` — is the A3 case again without
qualification.

### Two questions back

1. **Does a verdict turn on the name or on the content?**  `drop rule` and
   `placement rule` land differently under the two readings, and the A3
   precedent says the name.  Worth writing into the verdict table before
   this is run again.
2. **Should `not a term` be a verdict at all, or a harvester bug?**
   `fixtype rule` and `application rule` are the same defect — a real
   defined noun with *rule* after it — and a harvester that knew the
   corpus's own defined terms would not have collected either.

---

## The two new suspects, checked — 2026-08-23

*`tools/dangling.py` — the rewritten detector, `card:` above — flags
three names at HEAD.  `placement rule` is the one already checked and
still genuine.  `layout rule` and `number rule` are new, and this is
them.*

**Disclosure, and it is the same weakness the 2026-08-21 checker
recorded.**  The work order asks for a reader with no stake in the
detector.  This session wrote the detector, so it is the weaker
instrument on purpose-of-design grounds, and the verdicts below should
be read as a first pass rather than the independent check the work order
asks for.  Nothing here is fixed.

---

### 6. `layout rule` — **asserted**, and it is not the A3 case

**What I found first.**  The two sites lean on *different properties* of
one rule, and neither states it.

- `gestate/typecheck.py:1038` — *"`session.py` already reads
  declarations this way for `goto`, the language's layout rule
  guarantees a declaration starts at the left margin"*.  The property
  leaned on: **a toplevel declaration begins at column 0.**
- `shell/editor/src/window.rs:573` — *"the layout rule counts columns
  and a tab's width is the renderer's choice, so a tab-indented file
  means something other than it looks"*.  The property leaned on:
  **layout is measured in columns**, and tabs are therefore unsafe.

**The rule is asserted**, in `spec/syntax.md:756`, under the heading
`### Layout`:

> The offside rule: a block of declarations introduced continue as long
> as subsequent lines (ignoring blank lines) are indented at least as
> far as the first declaration's column.

**Verdict: asserted.**  The detector missed it because the phrase in the
heading is `Layout` and the phrase in the citations is `layout rule` —
one word apart.

**And that is the finding worth more than the verdict.**  The A3 case
turned on citation and definition having **not one word in common**.
Here they share *layout*, and any reader who greps the citation lands on
the definition in one hop.  So `layout rule` is not the defect this card
exists for, and a criterion that flags it is flagging the wrong shape.
See §"What the two new names say about the criterion".

**Two things found while checking it, recorded and not fixed.**  Both
are about the *content*, not the name, and neither belongs to this card:

1. **`spec/syntax.md` §"Layout" never says a toplevel declaration
   starts at column 0.**  It says continuation lines must be indented
   strictly farther than the beginning line, and every example begins at
   the margin — but `gestate/typecheck.py:1029`'s `_defined_lines`
   depends on the margin literally, testing `line[:1].isalpha()`.  The
   property it calls a guarantee is implied by examples.
2. **Tabs are not mentioned in `spec/syntax.md` at all** outside a
   string-escape example at `:78`, and not in `gestate/syntax/tokenize.py`.
   `window.rs:573` argues from a language property the spec does not
   state, and supplies its own evidence for it — *"no `.ges` in the tree
   contains one"*.

---

### 7. `number rule` — **not a term**, and the confound again

**What I found first.**  The two sites are one sentence written twice.

- `fixme.md:724` (F43) — *"Recorded rather than fixed: stopping the
  number rule after a `.`-projection is a lexical change nothing yet
  needs."*
- `test/test_projection.py:91` — *"the alternative would be to stop the
  number rule at a digit that follows a `.`-projection, which is a
  lexical change nothing yet needs."*

The register entry and the test docstring for the same finding, one
derived from the other.  **Same confound as `fixtype rule` and
`application rule`** — the name never crossed a document boundary.

**And it is not a name.**  It is ordinary technical English for the
lexer's rule for numbers, the same shape as `fixtype rule` and
`application rule` before it.  The thing it leans on is asserted in
`spec/syntax.md:48`, under `### Lexical format`:

> Numbers are grouped together, may contain underscore for clarity …
> and may be followed by decimals and exponential notation … So 2e-2 is
> one number, while 2e - 2 is the number 2e minus 2.

`gestate/syntax/tokenize.py:253`'s `_read_number` is the implementation.

**Verdict: not a term.**

**A fourth measurement bug, and it is in the new detector.**  The
confound fold did not catch this pair.  `tools/dangling.py`'s `_dedup`
compares a ±150-character window at similarity ≥ 0.70, and these two
sentences agree on their tail — *"a lexical change nothing yet needs"* —
while their lead-ins differ enough to drop under the threshold.  So the
fold has false negatives, and this is one, found the same way the first
three bugs were: by checking against a case whose answer was already
known.  **It is not fixed**, because moving the threshold to catch this
pair is exactly the move that would start folding independent uses, and
choosing that trade needs the criterion below settled first.

---

### What the two new names say about the criterion

Question 1 on this card asks whether a verdict turns on **the name** or
**the content**.  Both new names land the same way under both readings —
asserted, not a term — so neither settles it.  But together with
`layout rule` they suggest the question is framed one notch too coarsely.

**The A3 case was not *content missing* and it was not *name missing*.
It was that citation and definition had no word in common**, so no
search starting from the citation could reach the definition.  That is a
property of the *pair*, not of either half:

| | citation says | definition says | shares a word | reachable by grep |
|---|---|---|---|---|
| `A3 rule` (before the fix) | *the A3 rule* | §"One sheet, then depth" | no | **no** |
| `layout rule` | *the layout rule* | §"Layout" | yes | yes |
| `number rule` | *the number rule* | *"Numbers are grouped together"* | yes | yes |
| `drop rule` | *the drop rule* | *"dropped, and said so"* | yes | yes |
| `placement rule` | *the placement rule* | §"…the equator decides the panel" | **no** | **no** |

Read that way the corpus has produced **two** instances of the defect —
`A3 rule`, fixed, and `placement rule`, open — and every other name the
detector has ever flagged is reachable in one hop.

**This is a proposal and not an answer.**  It is a third reading, it was
written by the session that wrote the detector, and adopting it would
narrow the gate's job from *is this asserted* to *can a reader get from
the citation to the definition*.  That second question is harder to
compute and much closer to the thing that actually went wrong.

---

## The third reading, measured and withdrawn — 2026-08-23

*The section above proposes reachability — *can a reader get from the
citation to the definition* — as a better criterion than either name or
content.  Henri asked whether there was a good argument for either.
Measuring it withdrew the proposal and strengthened the case for **A**.*

### Reachability does not survive its own test

Operationalised the obvious way — **does the name's distinctive word
appear in any heading or bold lead in the corpus** — and run at
`5f42f68`, the revision where the answer is known:

    a3           reachable (3)
         doc/instruments.md:296   `python -m gestate.atlas` — the five A3 sheets
    placement    reachable (6)
         gestate/audioeditor.py:1899  losing them to a placement error would take

**Both founding cases come back clean.**  `A3` resolves — to paper size,
from the atlas.  `placement` resolves — to audio placement.  The word is
there and the sense is wrong, and a reader following it lands in another
document entirely.

**And that collision is probably the cause rather than a coincidence.**
`A3` already meant something here before the lean sense arrived, so the
new name was laid over an occupied word.  Any cheap version of this
criterion has to tell two senses of one word apart, which is the thing
regexes cannot do; the expensive version needs to know which sentence is
the definition, which is the thing that is not known.  **Withdrawn.**

### The argument for the *name* reading, which does hold

1. **The founding case only exists under it.**  At `5f42f68`
   `board/README.md` §"One sheet, then depth" carried the rule in full,
   in Henri's words, dated 2026-08-18.  Under the content reading there
   was **no defect on 2026-08-21**.  A criterion that clears the case
   this card was made for is not this card's criterion.
2. **This card already said so**, in §"What this is about", written
   before the question was asked: *"when the citation and the definition
   use different words … there is no string in common."*  The
   name/content question drifted away from the card's own scope during
   the checking.
3. **The remedy is a session's to make.**  Attaching a name to an
   existing sentence is an edit; writing a rule that does not exist is a
   design decision, and the work order above already assigns that to
   Henri.  A check whose remedy always needs the author is a check that
   sits red.

### And the content question is real, but it is already registered

Two content gaps turned up while checking `layout rule` — the unstated
column-0 guarantee and the unmentioned tabs.  Genuine, and no name-based
check would find either.  But `spec/errata.md` opens by recording *"what
the spec says (**or fails to say**)"*, and `fixme.md` already holds this
exact shape: `fixme.md:3191`, *"`spec/editor.md` requires text undo and
says nothing about file boundaries, so the spec needs the sentence too,
whichever way it goes"* — which Henri answered on 2026-08-13.

**Content-missing has two registers and a working precedent for reaching
him.  Name-missing has none, which is why this card exists.**  That
asymmetry is the argument, and it argues for keeping the two apart
rather than for merging them into one criterion.

### What that leaves

Knowing which question to ask does not make the heuristic better at
asking it: the only computable proxy is still *asserted nowhere*, at one
clean hit in five.  Two instances in the corpus's whole history — `A3
rule`, fixed, and `placement rule`, open.

**Suspected, and it is Henri's call:** that is an argument for **A**,
with `tools/dangling.py` standing where option A had nothing — a sweep
that can be run on purpose rather than a gate that runs itself.  B's
glossary would carry fourteen entries against two historical defects.
