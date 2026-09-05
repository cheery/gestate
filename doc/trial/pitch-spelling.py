"""The fixture for `doc/trial/pitch-spelling.md` — eight files, twice each.

    python doc/trial/pitch-spelling.py

Seeded, so it reproduces the exact sixteen files the arms of 2026-09-05
read.  Kept rather than the fixture itself, because a generator is the
command a result should carry and 2,304 lines of scratch are not
(`doc/memory/research-that-leaves-a-command.md`).

**Ground truth is checked two ways** — what this planted, and what
`notes.outside()` says of the same file — and that check earned itself on
its first run: the generator claimed twelve faults per file and the lamp
saw six, because raising a degree by a semitone often lands on another
note of the same mode.  Half the planted faults were not faults.
"""
import json, random, sys
sys.path.insert(0, "/home/cheery/gestate")
from gestate.notes import _MODES, _PITCH_CLASS, LEVELS, parse, outside

HERE = "/tmp/claude-1000/-home-cheery-gestate/39422cdc-b79d-4012-b9de-2ab77cf7e2e2/scratchpad/trial"
NATURAL = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
LETTERS = "cdefgab"
MODES = ["ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"]
KEYS = ["C", "D", "E", "F", "G", "A", "Bb", "Eb"]
VOICES = ["lead", "middle", "bass"]


def spell(letter, key, _unused):
    """`gis4`, `g4`, `es4` — the letter, its accidental, its octave.

    The octave is the **letter's**, found by asking which one puts the
    accidental within a semitone or two.  That is the rule real notation
    uses, and the only one that keeps `ces5` below `c5` rather than
    beside it.
    """
    for octave in range(-1, 10):
        delta = key - (NATURAL[letter] + (octave + 1) * 12)
        if -2 <= delta <= 2:
            mark = {-2: "eses", -1: "es", 0: "", 1: "is", 2: "isis"}[delta]
            return f"{letter}{mark}{octave}"
    raise AssertionError(f"no octave puts {letter} within reach of {key}")


def scale(tonic, mode):
    """`[(midi offset, letter)]` for one octave of the mode.

    The letters walk the alphabet from the tonic's, one per degree, which
    is what makes an altered degree keep its letter and change only its
    accidental — `gis` becoming `g` is the whole tell this trial is about.
    """
    root = LETTERS.index(tonic[0].lower())
    return [(step, LETTERS[(root + i) % 7])
            for i, step in enumerate(_MODES[mode])]


def one_file(seed):
    rng = random.Random(seed)
    keys = rng.sample(KEYS, 3)
    modes = rng.sample(MODES, 3)
    sections, rows, planted = [], [], []
    for name, key, mode in zip("ABC", keys, modes):
        sections.append(f"section {name}  key {key}  mode {mode}  bars 4  "
                        f"beats 4  voices " + ",".join(VOICES))
        degrees = scale(key, mode)
        base = _PITCH_CLASS[key]
        notes = []
        for bar in range(1, 5):
            for voice, octv in zip(VOICES, (5, 4, 3)):
                for at in (0, 96, 192, 288):
                    i = rng.randrange(len(degrees))
                    step, letter = degrees[i]
                    notes.append([name, bar, at, voice,
                                  base + step + (octv + 1) * 12, letter, octv,
                                  rng.choice(LEVELS), False])
        # **An alteration is only a fault if it leaves the mode**, and
        # half of them do not: raise the third of a major scale and you
        # land on the fourth.  Found by the two-way ground-truth check
        # on the first run — the generator claimed twelve faults and
        # `notes.outside` saw six, which is what that check is for.
        inside = set(_MODES[mode])
        wanted, spots = rng.randint(3, 5), list(range(len(notes)))
        rng.shuffle(spots)
        for spot in spots:
            if wanted == 0:
                break
            for step in rng.sample((-1, 1), 2):
                if (notes[spot][4] + step - base) % 12 not in inside:
                    notes[spot][4] += step
                    notes[spot][8] = True
                    wanted -= 1
                    break
        assert wanted == 0, "could not plant enough faults in this section"
        rows += notes
    return sections, rows


def render(sections, rows, named):
    out = list(sections) + [""]
    at_bar, lines, truth = None, [], []
    for sec, bar, at, voice, key, letter, octv, vel, bad in rows:
        if (sec, bar) != at_bar:
            out.append("")
            at_bar = (sec, bar)
        pitch = spell(letter, key, octv) if named else str(key)
        out.append(f"note  section {sec}  bar {bar}  at {at}  len 96  "
                   f"voice {voice}  key {pitch}  vel {vel}")
        if bad:
            truth.append(len(out))
    return "\n".join(out) + "\n", truth


made = []
for i in range(8):
    sections, rows = one_file(1000 + i)
    numbers, t1 = render(sections, rows, named=False)
    names, t2 = render(sections, rows, named=True)
    assert t1 == t2, "the two spellings must plant faults on the same lines"
    open(f"{HERE}/f{i}-numbers.notes", "w").write(numbers)
    open(f"{HERE}/f{i}-names.notes", "w").write(names)
    lamp = sorted(n.line for n, _ in outside(parse(numbers, f"f{i}")))
    assert lamp == sorted(t1), f"file {i}: generator {sorted(t1)} vs lamp {lamp}"
    made.append({"file": i, "truth": sorted(t1), "notes": len(rows)})
json.dump(made, open(f"{HERE}/truth.json", "w"), indent=1)
print(f"8 files, {made[0]['notes']} notes each, "
      f"{sum(len(m['truth']) for m in made)} planted faults")
print("ground truth agrees two ways: generator == notes.outside()")
