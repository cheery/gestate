# open-path-bug — a typed path lands in the wrong directory

    status   done — 2026-08-17
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

## Reproduced, 2026-08-17 — and it is not `_where`

`test/sessions/F104-hello.ges` turned out to be an ordinary `.ges` file
rather than a session log, so the reproduction was rebuilt from the
report itself.  From `examples/audio/minute.ges`:

```python
act(it, "wants\topen\t0\t../../hello.ges")
[t for t, *_ in it.choices()]      → ['test/sessions/F104-hello.ges']
it.run("open", "../../hello.ges")  → 'new file hello.ges — saving creates it'
win.wanted                         → '/home/cheery/gestate/hello.ges'
```

**`_where` is innocent, and so is the elaboration's guess above.**  Given
the literal text it resolves `../../hello.ges` correctly, to the repo
root.  What is wrong is the *listing*: it offers exactly one row, a file
from a directory nobody mentioned, and Return takes the row.

The mechanism is `Session._listing`'s last clause and it is **F130's own
fix firing where it should not**:

- `head = "../.."`, `stem = "hello.ges"`, `where` = the repo root.
- Nothing at the root matches `hello.ges`, so `out` is empty — the `..`
  row is filtered out too, because `".."` does not contain `"hello.ges"`.
- `if low and not out:` → `_below` runs a breadth-first search four
  directories down and surfaces `test/sessions/F104-hello.ges`.

F130 was written for a **bare** name — *"`open lantern.ges` from the root
used to answer 0 rows three times while starting phantoms"* — and there
the deep search is exactly right.  Here the person spelled the path out,
and the deep hit did not merely rank badly: it was the *only* row, so
Return could not mean the thing that was typed.

## What the work is

**The typed path must always be an answer.**  `do_open` already handles
a name that is not there — it says *"new file hello.ges — saving creates
it"* — so the fact is known; it is the listing that never offers it, and
a dialog where Return cannot mean *what I typed* is the whole defect.
Deep matches stay, below it, so F130 keeps its fix.

Rejected: suppressing `_below` whenever the query contains a `/`.  It
would fix this case and regress `open examples/lantern.ges`, where the
person named a directory and the file really is under it.

The fix wants a test that pins **which row comes first for a typed
path** — F122 and F123 were each fixed without one, which is how a third
came to exist at this site.

## Done

`gestate/session.py` `_listing`: when a query carries a `/` and nothing
in the directory it names matches, **the typed path itself is the first
row**, and F130's deep matches keep their place under it.  `fixme.md`
F145; four tests in `test/test_session.py`, the load-bearing one pinning
*which row comes first*.

**The elaboration's mechanism guess was wrong** — `_where` was innocent
— and that is now a rule in `board/README.md` §"What the first full day
of this taught": the durable half of an elaboration is the located parts
and the question, and a mechanism guess should say it is a guess.

`journal.md` §"A typed path is always an answer".
