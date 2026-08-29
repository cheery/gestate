# card-grain — how big a card is, and what waiting inside `doing` costs

    status   shelved — 2026-08-29
    because  "ymmärrän että kortit lähinnä varmistavat että työ tulee
             tehdyksi.  En ole paljoa katsonut kuinka isoja rupeamia
             kortit edustavat.  Mielestäni nykymalli on toiminut." — and
             the session's observation the same hour, marked as its own:
             a card can sit in `doing` for weeks waiting on a person
             while its work is finished and gated, and the list does not
             shrink when gated pieces land inside a card, so the signal
             his kanban sentence was built to give — progress read off
             the list — goes quiet exactly when the most work is done
    asked    Henri, 2026-08-29 — "Mutta mietitään noita 4 ja 5 asioita
             uudelleen..  voisit tehdä niistä kortin board/later
             -hakemistoon."  (The session wrote it, from that
             conversation.)
    see      board/README.md §"Finishing one" — where "one card, one
             commit" stood and was struck the same day
             board/README.md §"The priority" — "sediment or debt, and it
             is one question", written for later/ and asked here of doing
             card:online.md — the case: pieces A and B landed and gated
             on 2026-08-29, the card open until a stranger reports
             card:stranger-test.md — the card the report actually belongs to

## What this is, what it is not, when it runs

This is about the **grain of a card** — the size of the work one file
stands for — and about the word `doing` when the work is done and the
card is not.  It is not about the priority list's order, which is his,
and not about `later/`, whose sediment-or-debt question it borrows.
It runs when he reads the board and asks what the board is telling him;
it is shelved because he has just said the current model has worked,
and a card that reopens a working model needs evidence, not a session's
unease.

## The ask

His words, 2026-08-29, in order.  First, on being handed the two
observations below:

> hmm... no ymmärrän että kortit lähinnä varmistavat että työ tulee
> tehdyksi.  En ole paljoa katsonut kuinka isoja rupeamia kortit
> edustavat.  Mielestäni nykymalli on toiminut.

Then, a minute later:

> Mutta mietitään noita 4 ja 5 asioita uudelleen..  voisit tehdä niistä
> kortin board/later -hakemistoon.

So: the model stands, and the two observations are kept where they can
be thought about again.  Neither is a proposal.

## Found by looking, 2026-08-29

**The rule that was struck was false the whole time it stood.**  "One
card, one commit" was a session's reading of his sentence *"You take
each out from this section once the commit has landed"* — a
synchronisation rule read as a size rule.  Counted by name in commit
messages (rough: a name like `gemba` matches more than its card):

    for f in board/done/*.md; do n=$(basename $f .md);
      echo "$(git log --format=%s%n%b | grep -c -E "\b$n\b|card:$n\.md") $n"; done | sort -rn

17 of 21 finished cards are named in more than one commit; `gemba` in
47, `working-standard` 17, `timer` 16, `button` 14.  The tree was
already working in pieces; only the sentence said otherwise.  Same
shape as the "order" claim measured false on 2026-08-19 — a session
completes a short sentence of his into a rule, and the completion is
more exact than the sentence was.

**Observation 4 — `doing` that is waiting.**  `card:online.md` landed
two pieces with their own gates on 2026-08-29 and stays `doing` until
Michael reports from his own machine, which no session can hurry.  In
kanban, work in progress is limited because it costs; a card waiting on
a person costs nothing and looks identical.  `board/README.md` already
asks this of `later/` — *waiting on an event, or on me?* — and does
not ask it of `doing`.  The session's view, marked as the session's:
the tool was done when its gates were green and he had heard it; the
stranger's report is `card:stranger-test.md`'s run three, a card that
already exists, and a card whose finish waits on another card may be
two cards.

**Observation 5 — pieces are cards the list cannot see.**  *Four fewer,
none new* presses toward big cards holding A, B, C inside, and
`ls board/*.md` counts none of them.  His sentence's original job was
that he sees progress by the list shrinking without reading commits;
on 2026-08-29 the list did not shrink while two gated things landed.
The session's view: the status line is where the state belongs
(`doing — pieces A and B landed`), because the list is priority and not
order — but that means progress is read from cards, not from the list,
which is a different reading than the sentence gave him.

## What a session does on day one, if this is ever taken

Measure before proposing.  For every finished card, the days between
its first `status doing` and its move to `done/`, and how many of those
days the card's `blocked`/`## Questions` say it waited on a person or
an event rather than on work:

    git log --date=short --format='%ad %h' -p -- board/ | grep -E '^[0-9]{4}-|^\+    status'

If waiting-in-`doing` is rare, observation 4 is one card's story and
this card closes with the number.  If pieces-inside-cards is the common
grain, observation 5 is a fact about the board and the question becomes
whether he wants to read progress from the list or from the cards —
his to answer, and the card's front should carry both readings with
what would kill each.

## Shelved

Waits on an **event**, not on him: `card:online.md` closing is the
first full data point for observation 4 (how long a finished tool sat
in `doing` for a report), and the next card that lands gated pieces
without the list moving is the second for observation 5.  Two such
cases and this is worth the measurement above; until then it is one
afternoon's unease, and he has said the model works.  He reopens it by
saying so.

## Done

*Nothing — shelved on arrival.*
