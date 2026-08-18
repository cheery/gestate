# carried-state — a rule in prose did not hold the seam it was written for

    status   open
    because  "I wrote the seam rule into spec/verification.md at midday
             and then broke it three more times the same day" — the same
             function, `workbench._carry`, dropped a new field twice and
             crashed the editor in Henri's hands both times, and the
             suite agreed with it every time
    asked    Claude, 2026-08-18, at Henri's ask — "Write cards for
             fixing these issues in your workflow.  Describe them in
             good detail so that next time you can fix them."
    see      spec/verification.md §"The defect is in the seam, and the test is in the module"
             gestate/workbench.py:588 — `_carry`, the seam that broke
             gestate/session.py — the fields it has to carry
             test/test_atlas.py — the roster shape this should copy
             fixme.md F161 — the crash Henri hit, and why it is filed a day late
             card:interface-oracle.md — the same argument for the window

## The ask

From the day's kaizen, in my own words:

> Writing a rule down did not change my behaviour.  At lunchtime I wrote
> `spec/verification.md` §"The defect is in the seam" — *when you add a
> kind of thing, go read what already has an opinion about it.*  Then I
> broke it three more times, twice in `_carry`, the same function.  A
> principle in a file is not a control.

Henri had asked for the cards after the verdict, and named this one
worth having: *"I liked that you created a new card.  It was
necessary."*

## Found by looking, before it was taken

**The seam is `Session` ↔ `workbench._carry`.**  A `Session` is the
model; `_carry` builds a *fresh* one when the instrument under the
window changes, and copies across only the fields that belong to the
window rather than to the instrument.  Every field it forgets is a
silent reset, and the reset surfaces somewhere far away.

Three times on 2026-08-18:

| field added | how it failed | who found it |
|---|---|---|
| `session.walk` | `AttributeError: 'NoneType' object has no attribute 'read'` — the loop asks the walk what has been said, a bare `Session` has none | **Henri**, opening a file from the starter screen |
| `session.walking` | a walk opened a file and then stood still, because opening un-subscribed the window it had just moved | Henri, watching a walk stop |
| `_walked` / `_moving` / `_arrived` | the walk's own `goto` read as typing and ended the walk | me, only after `GESTATE_WALK_WHY=1` |

`_carry` is now correct — and its docstring is three paragraphs of
apology explaining each field, which is the shape of a function that
has been patched by incident rather than held by a check.  Nothing
stops the fourth one.

**The suite passed all three times.**  Every `Session` test builds a
`Session` directly; nothing in the tree ever exercises "and then the
instrument changed underneath it".  That is `manifesto.md`'s third way
an instrument fails: the tests were written from the implementation, so
they agree with it.

### The shape the fix should take, and why this shape

**This project already has the pattern and it works: a roster test.**
`test/test_atlas.py::test_every_module_has_a_lane` asserts a directory
is *exactly* a listed set, so a new module cannot arrive unnoticed —
it fails the moment the file lands, names the thing that is missing,
and is a gate, so it fails in seconds rather than at the end of a
25-minute pass.  Today it did exactly that for five new modules.

The same shape here, roughly:

```python
CARRIED = {"view", "log", "walk", "walking", "_walked", "_moving", "_arrived"}
KEPT_BY_THE_INSTRUMENT = {"bench", "editor", "playing", "build", ...}  # deliberate

def test_every_session_field_is_decided():
    fields = {k for k in vars(Session(bench=_a_bench())) if not k.startswith("__")}
    undecided = fields - CARRIED - KEPT_BY_THE_INSTRUMENT
    assert not undecided, (
        "these fields are neither carried across a switch nor listed as "
        f"deliberately dropped: {sorted(undecided)}")
```

Two properties matter more than the exact code:

* **The second set is as important as the first.**  A field that
  *should* reset is a decision, and writing it down is what makes the
  test a decision record rather than a copy of `_carry`.  A test that
  only asserts "`_carry` copies what `_carry` copies" is worth nothing.
* **It has to fail at the moment the field is added**, not when
  somebody switches instruments in a scenario.  That means it belongs
  in `tools/suite.py`'s `GATES`, next to the other rosters.

**And `_carry` is one instance of a general shape.**  Before taking
this, look for the siblings — the places where one object is rebuilt
from another and the copy list is written by hand:

- `workbench._carry` (`gestate/workbench.py:588`) — known
- `desk.of` / `desk.restore` — the desk file is a hand-written field
  list too, and a field added to `Desk` that nobody writes is the same
  defect with a slower fuse
- the furniture line in `session.py` and its parser in
  `shell/editor/src/furniture.rs` — a field added on one side and not
  the other, which is the *window's* version of this and is what
  `card:interface-oracle.md` is for
- `Session.__init__` ↔ whatever `test/` builds by hand

## The postcondition

*To be stated before building, per this board's rule.  A first draft,
for Henri to correct or ignore:*

**A field added to the session cannot reach a person's window without
somebody having decided, in writing, what happens to it when the
instrument changes.**

Note that this is one of the cases the board warns about: it is hard to
write without naming a function, which is the signal that this change
is not user-facing.  It is not — it is a control on the people who
build, and its user-facing claim is only the negative one: *the editor
does not crash when you open a file from the starter screen.*

## Questions

**Is a roster test the right instrument here, or is the real fix to
stop rebuilding the session at all?**  `_carry` exists because a switch
builds a new `Session`.  A window that kept one `Session` and swapped
the instrument *inside* it would have no seam to forget.  That is a
bigger change and might be the honest one — the roster makes the
current design safe, it does not make it right.  Worth ten minutes of
looking before writing the test, and worth asking Henri, because it is
a design question and not a testing one.

**Should this generalise into a checked practice, or stay three
tests?**  The tempting version is a decorator or a registry that makes
forgetting impossible by construction.  The cheap version is three
roster tests in three files.  Cheap first, on the evidence: the rosters
that already exist earn their keep and cost nothing to read.
