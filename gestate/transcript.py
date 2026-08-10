"""What a performance decided beyond its notes — and enough to replay it.

`spec/dynamicscore.md` stage three: **the transcript records the world
and the seed; everything else is arithmetic.**  Today the world half is
stalls and drops (the performance's own confessions) and the seed; when
`probe` lands, its readings join them, beat-stamped, and replay answers
probes from here instead of from the world.  The oracle this format
exists for: *a live performance equals its own replay, change for
change* — which is what keeps stage three improvisation rather than
anecdote.

The header names what the events assume: the source (by hash — the
transcript of one program replays only that program), the rate and
block (delivery boundaries are block arithmetic), and the seed (one
integer, never the draws — they are derivable, and "one number replays
the whole night" is the property being defended).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


class TranscriptError(Exception):
    pass


#: Bump when the shape of the header or the events changes.
#:
#: **2** — a reading carries the **position key** its question was
#: stamped with (`spec/ariadne.md`): `("reading", beat, port, values,
#: key)`.  The key rides last so the first four fields read exactly as
#: schema 1 did, and a schema-1 log still replays — by arrival order,
#: which is all it ever knew.
_SCHEMA = 2


@dataclass
class Transcript:
    """One performance's log: a header of assumptions, then what happened.

    `events` is beat-stamped tuples in arrival order — `("stall", beat)`,
    `("dropped", beat, bank)`, and, when the world reaches the score,
    `("reading", beat, chan, value)`.  `LazyPerformer` appends to this
    very list as it plays; nothing is transcribed after the fact.
    """

    source_sha: str = ""
    rate: int = 0
    block: int = 0
    seed: int = 0
    events: list = field(default_factory=list)

    @staticmethod
    def sha_of(source: str) -> str:
        return hashlib.sha256(source.encode()).hexdigest()[:32]

    # -- keeping it ----------------------------------------------------------

    def save(self, path) -> None:
        doc = {"schema": _SCHEMA, "source": self.source_sha,
               "rate": self.rate, "block": self.block, "seed": self.seed,
               "events": [list(e) for e in self.events]}
        with open(path, "w") as f:
            json.dump(doc, f, indent=None, separators=(",", ":"))
            f.write("\n")

    @classmethod
    def load(cls, path) -> "Transcript":
        with open(path) as f:
            doc = json.load(f)
        if doc.get("schema") not in (1, _SCHEMA):
            raise TranscriptError(
                f"this transcript is schema {doc.get('schema')!r} and this "
                f"reader is {_SCHEMA}; it was kept, so a reader for it can "
                f"be too")
        return cls(source_sha=doc["source"], rate=doc["rate"],
                   block=doc["block"], seed=doc["seed"],
                   events=[tuple(e) for e in doc["events"]])

    # -- holding a performance to it ------------------------------------------

    def reader_of(self):
        """Replay's world: each question answered by **where it stands**.

        A reading is keyed by its position key — stamped by the sower,
        so it survives the cut a rejoin makes — which is what lets a
        replay begin anywhere.  Order-keying was the whole mechanism
        once, and it holds only from the top: a rebuild mid-piece
        resumes *by descent*, skipping the prefix it never walks, so
        the k-th question of a rejoin is not the k-th of the take.
        The queue survives as the fallback, for a schema-1 log and for
        a question the thread never heard; running past what was
        recorded reads as silence, exactly as an unplugged port does.
        """
        from collections import defaultdict, deque

        by_key: dict = {}
        queues = defaultdict(deque)
        for entry in self.events:
            if entry[0] != "reading":
                continue
            queues[entry[2]].append(list(entry[3]))
            if len(entry) > 4:
                by_key[entry[4]] = list(entry[3])

        def reader(port, key=None):
            if key is not None and key in by_key:
                return list(by_key[key])
            q = queues.get(port)
            return list(q.popleft()) if q else []

        return reader

    def belongs_to(self, source: str) -> bool:
        """Is this the transcript of `source`?  A replay must ask first:
        feeding one program another's log is not a replay, it is a
        collage, and it should be refused by name."""
        return self.source_sha == self.sha_of(source)
