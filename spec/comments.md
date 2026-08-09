# Comments are semantic, and the compiler was never told — a root cause analysis

The footgun: a trailing comment on an expression breaks the program, and
the error blames something the author wrote correctly.

    x = 5  # gain            ⇒  DesugarError: Unsupported expression form: VComment
    x = Just 5  # the note   ⇒  Constructor Just applied to 2 args, but arity is 1
    x = True  # for now      ⇒  Constructor True applied to 1 args, but arity is 0

Meanwhile `T := A Int  # fine`, comments between declarations, and
comments between a data type's alternatives all work — so from the
outside the rule looks arbitrary, which is what makes it a footgun
rather than a restriction: there is no rule to learn, only sites to
memorise.  (The guide-writing sessions hit it three separate times.)
The interior case is broken too:

    x = (f
        # pick the base value
        5)                    ⇒  Unsupported expression form: VComment

## The five whys

**1. Why does a trailing comment break the equation?**

Because it parses as an *argument*.  `_can_start_atom`
(`syntax/parse.py`) counts `COMMENT` among the tokens that may start an
atom, `_parse_atom` builds a `VComment` value from it, and the
application loop in `_parse_app_expr` then applies the expression to
its own comment: `x = 5  # gain` is the tree `VApp(VNum 5, VComment)`.
The three error messages above are one defect wearing three costumes —
what the phantom argument lands on decides which lie is told.  A plain
head falls through desugar's dispatch ("Unsupported expression form");
a constructor head fails the arity check, which then accuses the
constructor.

**2. Why does the parser read a comment as an atom?**

Because comments are *values* in this AST.  `VComment` exists so that
`gestate fmt` can round-trip a file through parse → print without
deleting anybody's comments: at declaration level a comment is a module
item the formatter buffers and reprints, and inside an expression the
only slot the grammar offers is the atom, so that is where it was put.
The formatter can indeed print the poisoned application back out — 
`_fmt_app` renders `VApp(5, #gain)` as `5 #gain` — which is exactly why
the encoding looked workable from the formatter's side of the fence.

**3. Why does a comment-as-argument reach desugar instead of being
stripped?**

Because one parse serves two consumers with opposite needs and the
tree is handed to both unchanged.  The formatter needs comments kept;
the compiler needs them gone; nothing between parse and desugar strips
`VComment` for the compiling consumer.  `descend.py` imports the class
and does nothing with it — the fixity resolver walks straight past —
and desugar has no case for it, so the node sails until it hits
whatever check happens to be standing.  The failure surfaces two
stages after the decision that caused it, which is why the message
cannot name the comment.

**4. Why is there no stripping pass — why is every site on its own?**

Because comments are **tokens**, not trivia.  The tokenizer promotes
them into the same stream as code, and from that moment every grammar
position must decide what a comment means *there*.  The parser
contains at least seven ad-hoc skip sites — between top-level items,
in front of an `INDENT`, between a data type's alternatives, between
`let` bindings — and one *accept* site, the atom.  The sites somebody
remembered are the ones that work; the forgotten ones are precisely
the recorded bug list (equation body, case-alternative body).  The
expression grammar even disagrees with itself: `_is_postfix_op`'s
lookahead treats `COMMENT` as *end of expression*, three hundred lines
before `_can_start_atom` treats it as *more expression*.  A design
that requires N scattered decisions to agree will eventually ship with
N−k of them made.

**5. Why were comments made tokens in the first place?**

Because in gestate a comment is data, not noise — this is deliberate
and mostly right.  `#:` doc comments become the `doc/ref` pages;
`# ── section ──` headings structure the reference, and `internals.py`
uses them to say what neighbourhood a private name lives in; the
editor surfaces comments; the formatter must preserve them.  Comments
are semantic here in a way they are not in most languages.  But look
at where each consumer actually reads from: `reference.py` and
`internals.py` read the **raw text** with regexes, never the AST; the
formatter reads the AST but has not one test that round-trips an
expression-level comment; the compiler wishes they were not there at
all.  The token representation was chosen to honour "comments are
data" — and then every consumer that treats them as data bypassed it,
while the one consumer that treats them as noise pays for it at every
grammar position.

## Root cause

Comments in gestate have two natures — **data to the tools, trivia to
the compiler** — and were given one representation, in the code's own
token stream, which forces every stage that doesn't want them to opt
*out* at every site rather than letting the one stage that wants them
opt *in*.  Each forgotten opt-out is a live footgun; the failure
surfaces stages later than the cause; and the error names whatever the
phantom node collided with, never the comment.  The `!(f x)` analysis
(`spec/exclamation.md`) found a necessity claim that wasn't necessary;
this is the opposite shape: a *generality* — comments may stand
anywhere an atom may — that was never true, tested, or wanted.

## What repair would look like

Stated for the record rather than done, since the right depth is a
judgement call:

* **The honest minimum** — desugar (and the constructor-arity check)
  recognise `VComment` and say so: "a comment cannot be an argument;
  the parser read this trailing comment as one."  Cost: nothing.
  Gain: the lie becomes a truth, but the program still doesn't
  compile, so the footgun keeps its trigger and loses only its
  misdirection.

* **The real fix** — the expression grammar stops accepting `COMMENT`
  as an atom and skips it in the application loop, the same reading
  the postfix lookahead already commits to (comment = end of nothing,
  boundary of anything).  `x = 5  # gain` then compiles, as every
  author since the first guide has assumed it would.  Cost: an
  expression-interior comment no longer reaches the formatter's tree.
  That trade is currently free — the compile pipeline rejects every
  such program today, so there is no working file the formatter would
  newly mistreat, and fmt's comment coverage tests only the
  declaration level.

* **The principled fix** — comments become *trivia attached to
  tokens* (collected by the lexer, carried on spans), the AST carries
  none, and the formatter reads the token stream it already had to
  trust for layout.  This is what "two natures, two channels" looks
  like fully done; it is also a formatter rewrite, and nothing else in
  the pipeline would notice the difference.

The middle option deletes the footgun for the price of a parser branch
and honours every consumer that actually exists.  The first can ride
along with it as the error message for whatever site the next
refactoring forgets.
