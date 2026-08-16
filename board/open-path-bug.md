# open-path-bug — a typed path lands in the wrong directory

    status   open
    because  typing `open ../../hello.ges` throws me somewhere I did not
             ask for
    asked    Henri, 2026-08-16
    see      gestate/session.py `Session._where` (~line 1083)
             fixme.md F122, F123 — the same site, twice before
             test/sessions/F104-hello.ges — Henri's session file

## The ask

> bug: When I type `open ../../hello.ges` from `minute.ges`, it throws me
> into tests/section that has `hello.ges` in there.

## Found by looking, before it was taken

The mechanism is `Session._where`, and it has been the site of this class
of bug twice already — F122 (a typed path walked twice) and F123 (a
command inheriting another command's walk).  It resolves a typed path
against `here / walked / path`, where `walked` is borrowed from a
standing question only when `path != q`.  A typed `../../hello.ges`
should take the `path == q` branch and get no walk at all, so either the
equality is not holding or the standing question is not the one assumed.

## Questions

**Q (Claude), and it was blocking.**  Where are `hello.ges` and the
`tests/section` directory?  Neither is in the repository, so the
reproduction needs your actual layout — the directory you were in, and
what is above it.

**Henri, 2026-08-16:**

> I look for it.  I think I mistyped there.  I think I removed the
> session file.  Let me know if you need an another one.
>
> Here it is: `./test/sessions/F104-hello.ges`

**So it is no longer blocked.**  The session file is the reproduction;
replay it (`python -m gestate.sessionlog test/sessions/F104-hello.ges`)
and the walk that produced the wrong directory is in the log.

## What the work is

Replay the session, find which of the two branches `_where` took and
why, fix it, and file the F-number.  Given the site's history, the fix
wants a test that pins *which* branch a typed path takes — F122 and F123
were each fixed without one, which is how the third came to exist.
