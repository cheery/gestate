# The language

The forms the *compiler* provides.  Nothing declares these — they are not functions in a library but shapes the desugaring knows, so unlike every other page here this one is written rather than generated.  Their types are `infer.py`'s rules.

`FaL` and `ExL` are the two later modalities — written that way here and everywhere a *type* is spelled, because the circled quantifiers the papers use are a combining mark and garble in a monospace font.  `doc/manual.md` §6 is what they mean and why a signal needs both.

## Channels

### `chan`

```
chan : Chan a
```

A fresh channel.  Its identity *is* the declaration: two `chan`s are two channels, and a name bound to one is how anything else reaches it.

### `wait`

```
wait : Chan a -> ExL a
```

The next thing to arrive on a channel.  `0.0 ::: mkSig (wait c)` is a signal fed by one — a value now, and whatever comes next later.  This is the first line of nearly every canvas program.

### `never`

```
never : ExL a
```

An arrival that never comes.  The unit of `sync`, and what a signal that only ever holds one value waits on.

## Signals

### `head`

```
head : Sig a -> a
```

What a signal holds *now*.

### `tail`

```
tail : Sig a -> ExL (Sig a)
```

The rest of it, once one more instant has passed.  `scan` is written with this and `:::`.

### `(:::)`

```
(:::) : a -> ExL (Sig a) -> Sig a
```

A value now and a signal later, which is what a signal *is*.  The one constructor; everything else builds it.

## Later

### `delay`

```
delay : a -> FaL a
```

Something available from the next instant on.  Guarded recursion's guard: a recursive occurrence under one is productive by construction.

### `(<*>)`

```
(<*>) : FaL (a -> b) -> FaL a -> FaL b
```

Apply, later.  Rizzo's ⊛.

### `(<@>)`

```
(<@>) : FaL (a -> b) -> ExL a -> ExL b
```

Apply a delayed function to an arrival.  Rizzo's ⑤ — and the asymmetry is the point: what a `Sig` consumes is ExL and what `gfix` binds is FaL, so this is where the two meet.

### `gfix`

```
gfix : (FaL a -> a) -> a
```

Guarded recursion.  `gfix q => …` binds `q` to the whole expression *one instant later*, so it can only be consumed through `<*>` or `<@>` — which is the guard, in the type.

## Clocks

### `sync`

```
sync : ExL a -> ExL b -> ExL (Sync a b)
```

Whichever arrives first, or both — `SyncLeft`, `SyncRight`, `SyncBoth`.  The two need not agree in type: combining unlike clocks is what it is for.

### `watch`

```
watch : Sig (Maybe a) -> ExL a
```

The next instant at which a signal holds a `Just`.  A signal turned back into an arrival.

## Lifting

### `(!)`

```
(!) : (a -> … -> z) -> Sig a -> … -> Sig z
```

Where an ordinary function meets signals.  `!f x y z` pairs its arguments up through `Both` and takes them apart again, so it lifts over **any number** of them — there is no three-signal former and none is needed.

## The renderer's own

### `ticks`

```
ticks : Sig Int
```

The instant number, one per sample.  The clock everything at audio rate is a function of, and the argument `map` is usually given.

### `sampleRate`

```
sampleRate : Float
```

How many instants there are in a second.  The *renderer's* answer, not the program's: the same synth renders at any rate, and which one is a property of the file being written.

### `constSig`

```
constSig : a -> Sig a
```

The same value at every instant.  What it is constant *over* is whichever clock is running — `ticks` for a synth, the event stream for a canvas — which is why the renderer supplies it and no library can.

### `beat`

```
beat : Sig Float
```

**What beat it is** — at audio rate, for a synth moving in time with the music rather than with the second.  In scope wherever the program states a `bpm`, score or no score: a drone on a grid needs a tempo and no notes.  A program that states none gets `Unknown global 'beat'`, which is the truth — there is nothing to answer with.  Not available under a `tempo` envelope yet: the beat clock is piecewise quadratic there and reading it needs a segment search the audio fragment refuses.

### `elapsed`

```
elapsed : Sig Float
```

How long the program has been running, in **seconds**.  The clock a piece with no tempo has, and what an `Envelope` is usually read against — `on <points> elapsed`.  Defined in `audio.ges` rather than supplied, but it belongs beside `beat`: they are the two answers to "how far in are we".

## Why these are not in a library

`wait c` is not a call — the desugaring turns it into an `EWait` node, and inference gives that node a type directly.  There is no `wait` to declare and nothing for the generator to read, which is why every page here listed the libraries and none listed the language.

The practical consequence: **`python -m gestate.typecheck --query wait` has nothing to say about it either.**  This page is the answer to that question.

