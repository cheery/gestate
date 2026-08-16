# older-features — where do `using`/`given` and Datafun actually work?

    status   open
    because  using/given has never been used anywhere, and we went to
             FRP so hard that we forgot about Datafun
    asked    Henri, 2026-08-16
    see      doc/manual.md §9, test/test_datafun_sugar.py,
             test/test_relations.py, test/test_implicits.py
             roadmap.md §"Take the older language features through the
             workbench"

## The ask

> verify the older language features still work in workbench

## Found by looking, before it was taken

A sweep, and its difficulty is entirely in what "verify" means.  The
suite already covers the language; what it does not cover is *a person
using the feature through the window*, which is the gap
`test-what-a-person-would-do` was written about and how F138 was found.
`tools/toolbox.sh` and the XTEST harness are the machinery for driving a
real window.

The roadmap's own argument for it: a feature that only its own tests
exercise is a feature nobody has run in a year, and this project has
twice learned what that hides — the `Guard Bool` bottom the F64 check
found, and the canvas whose callers the editor's withdrawal had quietly
orphaned.

## Questions

**Q (Claude).**  Which features, and how far?  "Older language features"
could mean the twenty in `doc/manual.md`, or the ones with no window
test, or a specific list you have in mind.

**Henri, 2026-08-16:**

> I mainly have my concerns about using/given that has not been used
> anywhere yet!  I think it was important when we made it, and I think
> there's a time for it.  Note that I contradict project's rules there
> because it had no imminent use.  Let's allow it to be, but I want to
> know where it works currently.
>
> Another one is the whole Datafun implementation.  We went to FRP so
> hard that we forgot about these features!  Do not remove them, but
> analyse where they work right now.

**Answered, 2026-08-16 evening — a page, plus one worked example each.**
`using`/`given` and the Datafun surface get an audit page (does it
typecheck, does it run, is it reachable from the workbench, what is the
smallest program that exercises it) **and a small runnable `.ges` in
`examples/` per feature**.  Which is the interesting part: those
features have never had a caller, and Henri named that himself when he
added the card — *"I contradict project's rules there because it had no
imminent use."*  An example is the caller arriving late.  **Nothing is
removed.**

## What the work is

1. An audit page — the four questions above, answered per feature, with
   the smallest program that exercises each.
2. A small runnable example in `examples/` per feature, written *in the
   workbench* the way a person picking the project up would: through the
   command list, the save cycle, the completion, a content box.
3. The oracle is the environment itself.  Anything that cannot be typed
   there, or that the sidebar cannot infer, or that the fragment refuses
   in a way no message explains, is the finding — and what it produces
   is `fixme.md` entries.  **If it produces none, that is worth knowing
   too**, and costs an afternoon.
