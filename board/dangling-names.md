# dangling-names — a name the tree cites and nothing defines

    status   blocked
    blocked  on a decision that is Henri's — which of three shapes, or
             none.  Asked 2026-08-21, and he asked for time to think.
    because  the A3 rule was cited by name four times and defined
             nowhere, and no check in this tree could have found it
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
