//! A 3×5 bitmap font, hand-authored, for the chrome's labels.
//!
//! `spec/panel.md` §"Text": a channel name is an identifier and a bank
//! name is an identifier, so the alphabet a panel must render is small
//! and known.  Declaring that subset and owning it is the same move
//! `abi.rs` makes about CLAP, applied where a general solution would
//! cost a font stack to draw sixteen labels.
//!
//! **Letters are drawn uppercase**, whatever case they arrive in.  At
//! three pixels wide there is no room for a descender or an x-height,
//! so a lowercase alphabet would be the uppercase one drawn smaller and
//! read worse.  `lowpassSvf` renders `LOWPASSSVF`, and the panel says
//! the name the program says.
//!
//! Each glyph is five rows of three bits, bit 2 leftmost.  A row is
//! stored in the low three bits of a `u8`; anything the table does not
//! carry renders as a filled block, so an unknown character is *visibly*
//! unknown rather than a gap that reads as a spacing bug.

/// Cell width, in font units.
pub const W: i32 = 3;
/// Cell height, in font units.
pub const H: i32 = 5;
/// Gap between cells, in font units — one column, so `AB` does not touch.
pub const GAP: i32 = 1;

const UNKNOWN: [u8; 5] = [0b111, 0b111, 0b111, 0b111, 0b111];

/// The glyph for one character, already folded to uppercase.
pub fn glyph(ch: char) -> [u8; 5] {
    match ch.to_ascii_uppercase() {
        ' ' => [0b000, 0b000, 0b000, 0b000, 0b000],

        'A' => [0b111, 0b101, 0b111, 0b101, 0b101],
        'B' => [0b110, 0b101, 0b110, 0b101, 0b110],
        'C' => [0b111, 0b100, 0b100, 0b100, 0b111],
        'D' => [0b110, 0b101, 0b101, 0b101, 0b110],
        'E' => [0b111, 0b100, 0b110, 0b100, 0b111],
        'F' => [0b111, 0b100, 0b110, 0b100, 0b100],
        'G' => [0b111, 0b100, 0b101, 0b101, 0b111],
        'H' => [0b101, 0b101, 0b111, 0b101, 0b101],
        'I' => [0b111, 0b010, 0b010, 0b010, 0b111],
        'J' => [0b001, 0b001, 0b001, 0b101, 0b111],
        'K' => [0b101, 0b101, 0b110, 0b101, 0b101],
        'L' => [0b100, 0b100, 0b100, 0b100, 0b111],
        'M' => [0b101, 0b111, 0b111, 0b101, 0b101],
        'N' => [0b110, 0b101, 0b101, 0b101, 0b101],
        'O' => [0b111, 0b101, 0b101, 0b101, 0b111],
        'P' => [0b111, 0b101, 0b111, 0b100, 0b100],
        'Q' => [0b111, 0b101, 0b101, 0b111, 0b001],
        'R' => [0b111, 0b101, 0b110, 0b101, 0b101],
        'S' => [0b111, 0b100, 0b111, 0b001, 0b111],
        'T' => [0b111, 0b010, 0b010, 0b010, 0b010],
        'U' => [0b101, 0b101, 0b101, 0b101, 0b111],
        'V' => [0b101, 0b101, 0b101, 0b101, 0b010],
        'W' => [0b101, 0b101, 0b111, 0b111, 0b101],
        'X' => [0b101, 0b101, 0b010, 0b101, 0b101],
        'Y' => [0b101, 0b101, 0b010, 0b010, 0b010],
        'Z' => [0b111, 0b001, 0b010, 0b100, 0b111],

        '0' => [0b111, 0b101, 0b101, 0b101, 0b111],
        '1' => [0b010, 0b110, 0b010, 0b010, 0b111],
        '2' => [0b111, 0b001, 0b111, 0b100, 0b111],
        '3' => [0b111, 0b001, 0b011, 0b001, 0b111],
        '4' => [0b101, 0b101, 0b111, 0b001, 0b001],
        '5' => [0b111, 0b100, 0b111, 0b001, 0b111],
        '6' => [0b111, 0b100, 0b111, 0b101, 0b111],
        '7' => [0b111, 0b001, 0b010, 0b010, 0b010],
        '8' => [0b111, 0b101, 0b111, 0b101, 0b111],
        '9' => [0b111, 0b101, 0b111, 0b001, 0b111],

        '.' => [0b000, 0b000, 0b000, 0b000, 0b010],
        ',' => [0b000, 0b000, 0b000, 0b010, 0b100],
        '-' => [0b000, 0b000, 0b111, 0b000, 0b000],
        '_' => [0b000, 0b000, 0b000, 0b000, 0b111],
        '+' => [0b000, 0b010, 0b111, 0b010, 0b000],
        '=' => [0b000, 0b111, 0b000, 0b111, 0b000],
        '/' => [0b001, 0b001, 0b010, 0b100, 0b100],
        ':' => [0b000, 0b010, 0b000, 0b010, 0b000],
        '#' => [0b101, 0b111, 0b101, 0b111, 0b101],
        '%' => [0b101, 0b001, 0b010, 0b100, 0b101],
        '*' => [0b101, 0b010, 0b101, 0b000, 0b000],
        '?' => [0b111, 0b001, 0b011, 0b000, 0b010],
        '!' => [0b010, 0b010, 0b010, 0b000, 0b010],
        '(' => [0b010, 0b100, 0b100, 0b100, 0b010],
        ')' => [0b010, 0b001, 0b001, 0b001, 0b010],
        '<' => [0b001, 0b010, 0b100, 0b010, 0b001],
        '>' => [0b100, 0b010, 0b001, 0b010, 0b100],

        _ => UNKNOWN,
    }
}

/// How wide a string is at a scale, in pixels — the trailing gap
/// excluded, so a right-aligned label lands where it looks like it
/// should.
pub fn width(s: &str, scale: i32) -> i32 {
    let n = s.chars().count() as i32;
    if n == 0 {
        0
    } else {
        (n * (W + GAP) - GAP) * scale
    }
}

/// How tall a line is at a scale, in pixels.
pub fn height(scale: i32) -> i32 {
    H * scale
}
