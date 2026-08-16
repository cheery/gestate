# argument-names — which argument is which

    status   done — 2026-08-16
    because  I do not figure out quickly enough which argument in
             lowpass filters are which
    asked    Henri, 2026-08-16
    see      journal.md §"The names were in the source all along"
             roadmap.md §"Which argument is which"
             gestate/reference.py — `Entry.params`, `named()`

## The ask

Written as a fix rather than as a problem, which is the card that taught
the board to insist on a `because`:

> name datatypes eg. `type Duration = Float`, `type Pitch = Int`

The problem behind it only came out in the answer to Question C, below.

## Found by looking, before it was taken

**Mostly already built, and the interesting part is what is not.**
`type Duration = Float` parses and checks today — `test/test_type_alias.py`
has twenty tests, and `spec/types.md` §6 says aliases are expanded
eagerly before the unifier.  Confirmed by running it:

    type Pitch = Int
    type Duration = Float
    bad : Pitch -> Duration
    bad p = p          -- correctly rejected: Int vs Float

But they are **structural**, so this is *accepted*:

    type Pitch = Int
    type Steps = Int
    mix : Pitch -> Steps
    mix p = p          -- accepted; both expand to Int

A nominal type would reject that.  `spec/types.md` §10.6 already names
the pair — *"non-recursive type alias expansion **and nominal data
types**"* — so the second half is specified and unbuilt.

*Found on the way and not part of this card:* `wait d = d + 1.0` under
`type Duration = Float` fails with `expected Float, got ExL a`, which
looks like the defaulting gap (F32) rather than anything to do with
aliases.  Worth a defect number if it reproduces without the alias.

## Questions

**Q (Claude).**  Aliases are built.  Do you want **nominal** types where
`Pitch` and `Steps` are distinct despite both being `Int`, or is the
alias behaviour what you meant and the card is already done?

**Henri, 2026-08-16:**

> I do not know yet.  The types should not get on the way.  I think that
> they should be documentation.  Hey maybe they could be
> semi-structured:
>
>     type Duration = Float
>     type Length   = Float
>
>     f : Duration -> Float
>     x : Length
>     f x         <-- error
>     f (cast x)  <-- ok.
>
> But I'm not sure, get back to me if this is bad idea due to some reason
> that you find.
>
> Honestly the implementation you show looks good though.  I only
> included this as today's task, because I do not figure out quickly
> enought which argument in lowpass filters are which?

**Answered, 2026-08-16 evening — parameter names first, nominal types
later.**  Grounded by looking at the real signatures, which is what
changed the question:

    lowpass        : Sig Float -> Sig Float -> Sig Float               -- k,  s
    lowpassOnePole : Sig Float -> Sig Float -> Sig Float               -- hz, s
    lowpassSvf     : Sig Float -> Sig Float -> Sig Float -> Sig Float  -- hz, res, s
    lowpassLadder  : Sig Float -> Sig Float -> Sig Float -> Sig Float  -- hz, res, s

**The types carry no information at all.**  The names carry every bit of
it and lived only in the source, and the first argument means a
*coefficient* in `lowpass` and *hertz* in `lowpassOnePole` — the same
position meaning different things between neighbours.  So the reported
problem is a visibility problem, not a type problem, and a nominal type
would not have helped: `Hz` and `Coefficient` are both `Sig Float`, and
what a reader needs is which one *this* function wants.

Henri's `cast` idea stays on the roadmap as the deeper fix, unbuilt
until it has a caller of its own.

## Done

`reference.Entry.params` reads the argument names off the definition's
own head — the line the reference parser had been skipping on purpose —
and `reference.named()` is the single reader that puts them on a
signature.  They now show in `doc/ref/` (regenerated), in the editor's
`what` and its page, and in `typecheck --query`:

    lowpassSvf hz res s : Sig Float -> Sig Float -> Sig Float -> Sig Float

350 of the 399 library values and operators have names; the 49 without
are primitives and definitions that take a pattern, and those report
**no** names rather than half, because half a list read positionally is
worse than none.  Two tests in `test/test_reference.py`.

No language change, which is the point.
