"""A document as a grid — the host half of `gestate/grid.ges`.

`card:gex-sheet.md` §"Off the shelf — 2026-09-12": the first grid is a
`.notes` file, drawn as a row per record and a column per field.
`grid.ges` is the drawing, written once; what this writes per file is
what differs from file to file — the channels, the kind's columns with
their widths and heads, how each column's number is shown, and one
picture lifted over the rows and the selected cell.

**The rows are a reading, never text.**  A record crosses as `n`
numbers on a channel: a number field as itself, a word as its index in
the file's own word table, a bounded field as its index in the
declaration's list, a set of names as bits, an absent field as `-1`.
So the program's text depends on the kind and on the file's *words*
and on nothing a value edit changes — `test/test_gridsheet.py` holds a
program byte-identical across an edit, which is the drawn-scores lesson
(`card:notes-editor.md` slice 3).  A new word — a voice, a spelling
the file has not used — is a new program, once.

**A cell's meaning is the row and the column**, `row * COLS + col`,
and the row names the record's key in the document's own syntax
(`key_of`), which is what `field` and `retract` take.  The model's key,
never the picture's index (`doc/memory/identity-is-the-models-key.md`):
the row number is how the picture says which record, and the command
line that results carries the key.
"""

from __future__ import annotations

from typing import NamedTuple

#: `grid.ges`' `gridCols` and `gridRowH`, restated — held to the
#: library by `test/test_gridsheet.py`.
COLS = 16
ROW_H = 14

#: The 3×5 chrome font at scale two: a character is four cells wide
#: including its gap, and a label of `n` characters fits `(4n - 1) * 2`
#: pixels (`gui._fit`).  A cell keeps six pixels of margin.
_CHAR = 8
_MARGIN = 8


class GridRegion(NamedTuple):
    """What a press on a grid's cell channel is about: which document
    kind, its columns, and the records in row order."""

    box: int
    kind: str
    fields: tuple                # field names, in column order
    rows: tuple                  # the records, dicts, each with `line`
    words: tuple                 # the file's word table, by code

    @property
    def sel(self) -> str:
        """The channel that says which cell the last press selected."""
        return f"__ng_sel_{self.box}__"

    @property
    def rows_channel(self) -> str:
        """The channel the records arrive on."""
        return f"__ng_rows_{self.box}__"


def cell_channel(box: int) -> str:
    """The channel every cell of the box writes its meaning to."""
    return f"__ng_cell_{box}__"


def entry_of(box: int) -> str:
    """The definition the box's picture is."""
    return f"__grid_{box}__"


def cell_of(value: float) -> tuple:
    """`(row, col)` from a cell's meaning."""
    v = int(value)
    return v // COLS, v % COLS


def columns(kind) -> list:
    """The kind's fields, in declared order — the grid's columns."""
    return list(kind.fields)


def words_of(rels: dict, kind, records: list) -> list:
    """The file's word table: every value a `Word` field of this kind
    takes, sorted, so a code is stable while values move."""
    seen = set()
    for one in records:
        for f in kind.fields:
            if f.value == "Word" and one.get(f.name) is not None:
                seen.add(str(one[f.name]))
    return sorted(seen)


def value_code(field, value, words: list) -> int:
    """One field's value as the number the picture reads."""
    if value is None or value == () or value == "":
        return -1
    dom = field.domain
    if dom is not None and dom[0] == "OneOf":
        names = list(dom[1])
        return names.index(value) if value in names else -1
    if dom is not None and dom[0] == "Each":
        names = list(dom[1])
        bits = 0
        for v in value:
            if v in names:
                bits |= 1 << names.index(v)
        return bits
    if field.value == "Word":
        return words.index(str(value)) if str(value) in words else -1
    return int(value)


def record_reading(one: dict, fields: list, words: list) -> list:
    """One record as its column numbers."""
    return [value_code(f, one.get(f.name), words) for f in fields]


def _records(rels: dict, kind_name: str) -> list:
    from .notes import notes_of, sections_of

    if kind_name == "note":
        return notes_of(rels)
    if kind_name == "section":
        return sections_of(rels)
    return []


def grid_regions(rels: dict, box: int = 0, kind_name: str = "note",
                 where=None) -> dict:
    """`{cell channel: GridRegion}` for one grid box over a document."""
    from .notes import _kinds

    kind = _kinds(where).kind(kind_name)
    records = _records(rels, kind_name)
    fields = tuple(f.name for f in columns(kind))
    words = tuple(words_of(rels, kind, records))
    return {cell_channel(box): GridRegion(box, kind_name, fields,
                                          tuple(records), words)}


def grid_reading(rels: dict, kind_name: str = "note", where=None) -> list:
    """The rows flat, as the `List Float` the box's channel reads."""
    from .notes import _kinds

    kind = _kinds(where).kind(kind_name)
    records = _records(rels, kind_name)
    fields = columns(kind)
    words = words_of(rels, kind, records)
    return [float(v) for one in records
            for v in record_reading(one, fields, words)]


def width_of(field) -> int:
    """A column's width in pixels, from what its values can say."""
    dom = field.domain
    if dom is not None and dom[0] == "OneOf":
        chars = max(len(n) for n in dom[1])
    elif dom is not None and dom[0] == "Each":
        chars = sum(len(n) for n in dom[1]) + len(dom[1]) - 1
    elif field.value == "Word":
        chars = 8
    elif field.value == "Names":
        chars = 12
    else:
        chars = 4
    return (4 * max(chars, len(field.name)) - 1) * 2 + _MARGIN


def widths(kind) -> list:
    return [width_of(f) for f in columns(kind)]


def cell_rect(kind, row: int, col: int) -> tuple:
    """`(x, y, w, h)` of a cell in the page's own pixels, the origin at
    the page's top-left — the head is row `-1`.  `grid.ges` lays the
    page out with `Row` and `Column`, and this restates that arithmetic
    so a test can aim a press; the two are held equal by the hit table."""
    ws = widths(kind)
    x = sum(ws[:col])
    return x, (row + 1) * ROW_H, ws[col], ROW_H


def page_size(kind, rows: int) -> tuple:
    return sum(widths(kind)), (rows + 1) * ROW_H


def key_of(region: GridRegion, row: int, where=None) -> str:
    """The record's key in the document's own syntax — what `retract`
    and `field` take: `note section A bar 1 voice melody at 0 key 62`."""
    from .notes import _kinds

    kind = _kinds(where).kind(region.kind)
    one = region.rows[row]
    if kind.shape[0] == "Headed":
        return f"{region.kind} {one[kind.shape[1]]}"
    return region.kind + "".join(f" {f} {one[f]}" for f in kind.key)


def _ges_string(text: str) -> str:
    return '"' + str(text).replace('"', "'") + '"'


def _show_column(field, words_fn: str) -> str:
    """The expression showing one column's number, over `v`."""
    dom = field.domain
    if dom is not None and dom[0] in ("OneOf", "Each"):
        return None                     # its own case table, below
    if field.value == "Word":
        return f"{words_fn} v"
    return "gridNum v"


def _names_table(name: str, names: list, each: bool) -> str:
    """A case table from a code to the declaration's names — an index
    for `OneOf`, bits for `Each`."""
    arms = []
    if each:
        for bits in range(1 << len(names)):
            said = ",".join(n for i, n in enumerate(names) if bits >> i & 1)
            arms.append(f"    {bits} -> {_ges_string(said or '-')}")
    else:
        for i, n in enumerate(names):
            arms.append(f"    {i} -> {_ges_string(n)}")
    arms.append('    _ -> "-"')
    return (f"{name} : Int -> String\n{name} c = case c of\n"
            + "\n".join(arms) + "\n\n")


def grid_program(rels: dict, box: int = 0, kind_name: str = "note",
                 where=None) -> tuple:
    """`(ges_text, [cell channel])` — the box's program over `grid.ges`.

    What is written is what differs from file to file: the channels,
    the word table, how each column shows, the widths and heads, and
    the picture.  The rows are not here; they arrive on the channel.
    """
    from .notes import _kinds

    kind = _kinds(where).kind(kind_name)
    records = _records(rels, kind_name)
    fields = columns(kind)
    words = words_of(rels, kind, records)
    N = lambda k: f"__ng_{k}_{box}__"
    cell_c, sel_c, rows_c = cell_channel(box), N("sel"), N("rows")
    word_fn, show_fn = N("word"), N("show")
    text = (f"{cell_c} : Chan Float\n{cell_c} = chan\n"
            f"{sel_c} : Chan Float\n{sel_c} = chan\n"
            f"{sel_c}_s : Sig Float\n{sel_c}_s = (0.0 - 1.0) ::: mkSig (wait {sel_c})\n"
            f"{rows_c} : Chan (List Float)\n{rows_c} = chan\n"
            f"{rows_c}_s : Sig (List Float)\n{rows_c}_s = Nil ::: mkSig (wait {rows_c})\n\n")
    # **The file's own words**, by code — the one table a value edit
    # can outgrow, and then the program is new, once.
    text += (f"{word_fn} : Int -> String\n{word_fn} c = case c of\n"
             + "".join(f"    {i} -> {_ges_string(w)}\n" for i, w in enumerate(words))
             + '    _ -> "-"\n\n')
    arms = []
    for col, f in enumerate(fields):
        shown = _show_column(f, word_fn)
        if shown is None:
            table = N(f"dom{col}")
            text += _names_table(table, list(f.domain[1]), f.domain[0] == "Each")
            shown = f"{table} v"
        arms.append(f"    {col} -> {shown}")
    text += (f"{show_fn} : Int -> Int -> String\n{show_fn} col v = case col of\n"
             + "\n".join(arms) + "\n    _ -> gridNum v\n\n")
    ws = " :: ".join(str(w) for w in widths(kind)) + " :: Nil"
    hs = " :: ".join(_ges_string(f.name) for f in fields) + " :: Nil"
    pic = N("pic")
    entry = entry_of(box)
    text += (f"{N('widths')} : List Int\n{N('widths')} = {ws}\n\n"
             f"{N('heads')} : List String\n{N('heads')} = {hs}\n\n"
             f"{pic} : List Float -> Float -> Sub\n"
             f"{pic} rows sel = gridPage {cell_c} {show_fn} {N('widths')} {N('heads')} "
             f"{len(fields)} rows (floor sel)\n\n"
             f"{entry} : Sig Sub\n{entry} = !{pic} {rows_c}_s {sel_c}_s\n")
    return text, [cell_c]
