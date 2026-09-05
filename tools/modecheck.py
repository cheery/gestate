#: asked-by: a session, 2026-09-05 — no one asked for the tool; `hollow.ges`
#: states nine counts about itself and `doc/notes/notes-on-writing-a-piece.md`
#: records that unverifiable prose about music has already put a false
#: cadence claim in `arc.ges`.  A file that states its own numbers should
#: carry the command that produces them.  Henri's to delete if he disagrees.
"""What a line does, in numbers — and where the ear can rest.

    python tools/modecheck.py examples/audio/hollow.ges song 11
    python tools/modecheck.py examples/midi/maybe-locrian.mid - 11

The third argument is the tonic's pitch class (C=0 … B=11).  A `.ges`
file is read through the score, so what is counted is what the renderer
will play; a `.mid` file is read straight and its bank argument ignored.

**Why these seven counts and not others.**  They are the ones
`doc/notes/notes-on-writing-a-piece.md` arrived at over a day of getting
a mode wrong, and every one of them was written by hand *after* an ear
had already found the problem:

    the feeling, heard          the number
    doesn't go to locrian       bars with a perfect fifth over the bass
    not that unsettling         notes touching the tonic
    it's a list, not a line     stepwise share, leaps, direction changes
    rhythmically dead           notes shorter than a quarter

`spec/annotations.md`-style prose about music is unchecked in a way
prose about code is not — that log has a comment on `arc.ges` bar 16
claiming a cadence the notes do not contain.  A file that states its own
counts should carry the command that produces them, which is this.

**Stepwise counts a repeated note as a step** (|interval| ≤ 2, zero
included), because that is how the log counted and the comparisons in
`hollow.ges` are against its numbers.
"""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestate.audioscore import perform_voices
from gestate.midi import TICKS_PER_BEAT as TPB


def notes_of_ges(path, bank):
    """`(notes, events)` — one bank's line, and the whole score behind it."""
    from gestate.audioscore import pitch_of
    from gestate.notes import read

    bpm, events = perform_voices(read(path), "", 48000, 0)
    #: `pitch_of` and not `for _, key in payload`, which assumed every
    #: payload was a pair and crashed on every piece written since
    #: manners landed — `fixme.md` F201.
    line = sorted((on, off, pitch_of(payload))
                  for on, off, bk, payload in events if bk == bank)
    if not line:
        banks = sorted({bk for _, _, bk, _ in events})
        raise SystemExit(f"{path}: no bank named {bank!r}; it has {banks}")
    return line, events


def notes_of_mid(path):
    import mido

    mid = mido.MidiFile(path)
    now, held, out = 0, {}, []
    for msg in mido.merge_tracks(mid.tracks):
        now += msg.time
        if msg.type == "note_on" and msg.velocity:
            held[msg.note] = now
        elif msg.type == "note_off" or msg.type == "note_on":
            if msg.note in held:
                start = held.pop(msg.note)
                out.append((start * TPB // mid.ticks_per_beat,
                            now * TPB // mid.ticks_per_beat, msg.note))
    return sorted(out), []


def report(name, notes, tonic):
    keys = [k for _, _, k in notes]
    durs = [off - on for on, off, _ in notes]
    moves = [b - a for a, b in zip(keys, keys[1:])]
    n, m = len(keys), max(len(moves), 1)
    held = max(range(n), key=lambda i: durs[i])

    def touching(pc):
        return sum(1 for i, _ in enumerate(moves)
                   if keys[i] % 12 == pc or keys[i + 1] % 12 == pc)

    def share(count, total):
        return f"{count}/{total} = {round(100 * count / total)}%"

    cues = [what for what, key in (("first", keys[0]), ("last", keys[-1]),
                                   ("lowest", min(keys)), ("longest", keys[held]))
            if key % 12 == tonic]
    print(f"── {name}: {n} notes")
    print(f"   tonic share             {share(sum(1 for k in keys if k % 12 == tonic), n)}")
    print(f"   stepwise (<= a tone)    {share(sum(1 for d in moves if abs(d) <= 2), m)}")
    print(f"   leaps                   {share(sum(1 for d in moves if abs(d) > 2), m)}"
          f"   widest {max((abs(d) for d in moves), default=0)} semitones")
    print(f"   repeated notes          {share(sum(1 for d in moves if d == 0), m)}")
    print(f"   direction changes       {share(sum(1 for a, b in zip(moves, moves[1:]) if a and b and (a > 0) != (b > 0)), m)}")
    print(f"   moves touching the b2   {touching((tonic + 1) % 12)}")
    print(f"   moves touching the b5   {touching((tonic + 6) % 12)}")
    print(f"   shorter than a quarter  {sum(1 for d in durs if d < TPB)}/{n}")
    print(f"   structural cues on the tonic: {', '.join(cues) if cues else 'none'}"
          f"   (first {keys[0]}, last {keys[-1]}, lowest {min(keys)}, longest {keys[held]})")


def places_to_rest(events):
    """Bars offering a perfect fifth above whatever is sounding lowest.

    The count `arc.ges` went from 4 of 8 to 0 of 8 on: a mode with no
    perfect fifth over its own tonic cannot establish itself the ordinary
    way, so anywhere the ear *can* stand is somewhere it will stand.
    """
    sounding = collections.defaultdict(list)
    from gestate.audioscore import pitch_of

    for on, off, _bank, payload in events:
        key = pitch_of(payload)
        for b in range(on // (4 * TPB), max(on, off - 1) // (4 * TPB) + 1):
            sounding[b].append(key)
    bars = [ks for _, ks in sorted(sounding.items()) if ks]
    rest = sum(1 for ks in bars if any((k - min(ks)) % 12 == 7 for k in ks))
    print(f"── places to rest: {rest} of {len(bars)} bars have a perfect fifth "
          f"above the sounding bass")


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__.strip().splitlines()[0]
                         + "\n\nusage: modecheck.py FILE BANK TONIC-PITCH-CLASS")
    path, bank, tonic = argv[1], argv[2], int(argv[3])
    notes, events = (notes_of_mid(path) if path.endswith(".mid")
                     else notes_of_ges(path, bank))
    report(Path(path).name + (f" [{bank}]" if events else ""), notes, tonic)
    if events:
        places_to_rest(events)


if __name__ == "__main__":
    main(sys.argv)
