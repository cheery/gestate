//! **Random edits against a naive model, to prune bugs out of the rope.**
//!
//! The parity fixture beside this one replays *one* recorded session and
//! is the check that the port agrees with `balanced.py`.  This is the
//! other kind: thousands of sessions nobody recorded, each checked
//! against a `String` that cannot be wrong because it does nothing
//! clever.
//!
//! Three things are asserted after **every** edit, and each catches a
//! different class of fault:
//!
//! * **The text.**  Catches an edit that wrote the wrong characters —
//!   the failure a person would eventually see.
//! * **The summaries.**  `length` and `newlines` are the only reason
//!   the descents are fast, and a wrong one is a wrong *answer* rather
//!   than a slow one: `row` names the wrong line and nothing crashes.
//! * **The shape.**  A rope that loses its balance still gives the
//!   right text, just more slowly — so nothing but a test that looks at
//!   the tree can tell.  This is the class the fixture found in the
//!   reference implementation, where four thousand random edits left
//!   nodes four levels out.
//!
//! No dependency: the generator is sixty-four bits of splitmix and the
//! seed is printed with any failure, so a red run is reproducible by
//! reading the message.

use gestate_editor::rope::Rope;

/// splitmix64 — one multiply-xor round, which is all a fuzzer that
/// picks positions needs.
struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    fn below(&mut self, n: usize) -> usize {
        if n == 0 { 0 } else { (self.next() % n as u64) as usize }
    }

    fn upto(&mut self, n: usize) -> usize {
        self.below(n + 1)
    }
}

/// **Deliberately awkward.**  Multi-byte characters, so a port that
/// confused characters with bytes fails on the first line rather than
/// on somebody's accented variable name; newlines both common and
/// clustered, because `row` and `rowpos` are the interesting
/// descents; and a tab, because it is the character an editor is most
/// likely to mishandle later.
const ALPHABET: &[char] = &[
    'a', 'b', 'c', 'd', 'e', ' ', ' ', '\n', '\n', '\n',
    '\t', 'å', 'ä', 'ö', '日', '本', '🎹',
];

fn word(rng: &mut Rng, n: usize) -> String {
    (0..n).map(|_| ALPHABET[rng.below(ALPHABET.len())]).collect()
}

/// The model: a `Vec<char>`, because positions are characters and a
/// `String` would invite the very confusion being tested for.
struct Model(Vec<char>);

impl Model {
    fn text(&self) -> String {
        self.0.iter().collect()
    }

    fn row_of(&self, pos: usize) -> usize {
        self.0[..pos].iter().filter(|c| **c == '\n').count()
    }

    fn rowpos(&self, row: usize) -> usize {
        if row == 0 {
            return 0;
        }
        let mut seen = 0;
        for (i, c) in self.0.iter().enumerate() {
            if *c == '\n' {
                seen += 1;
                if seen == row {
                    return i + 1;
                }
            }
        }
        self.0.len()
    }
}

/// One session: `steps` edits, everything checked after each.
fn session(seed: u64, steps: usize, bulk: usize) {
    let mut rng = Rng(seed);
    let mut r = Rope::new();
    let mut m = Model(Vec::new());

    for step in 0..steps {
        let at = format!("seed {seed}, step {step}");
        let n = m.0.len();
        // Biased to grow: a short document never rotates, and rotation
        // is the half of an AVL that can be wrong invisibly.
        if n > 30 && rng.below(100) < 35 {
            let a = rng.below(n);
            let b = a + rng.upto((n - a).min(bulk));
            r = r.erase(a, b).unwrap_or_else(|e| panic!("{at}: erase {a} {b}: {e:?}"));
            m.0.drain(a..b);
        } else {
            let pos = rng.upto(n);
            let k = 1 + rng.below(bulk);
            let s = word(&mut rng, k);
            r = r.insert(pos, &s).unwrap_or_else(|e| panic!("{at}: insert: {e:?}"));
            let tail: Vec<char> = m.0.split_off(pos);
            m.0.extend(s.chars());
            m.0.extend(tail);
        }

        assert_eq!(r.len(), m.0.len(), "{at}: length");
        assert_eq!(r.newlines(),
                   m.0.iter().filter(|c| **c == '\n').count(), "{at}: newlines");
        assert!(r.is_sound(), "{at}: the tree lost its invariant");
        assert_eq!(r.text(), m.text(), "{at}: the text");

        // The queries, on a few positions rather than all of them —
        // every step is already O(n) in the model and this keeps a
        // thousand sessions bearable.
        for _ in 0..3 {
            let p = rng.upto(m.0.len());
            assert_eq!(r.row(p).unwrap_or_else(|e| panic!("{at}: row {p}: {e:?}")),
                       m.row_of(p), "{at}: row of {p}");
            let row = rng.upto(r.rows() - 1);
            assert_eq!(r.rowpos(row).unwrap_or_else(|e| panic!("{at}: rowpos: {e:?}")),
                       m.rowpos(row), "{at}: rowpos of {row}");
            let a = rng.upto(m.0.len());
            let b = a + rng.upto(m.0.len() - a);
            assert_eq!(r.read(a, b).unwrap_or_else(|e| panic!("{at}: read: {e:?}")),
                       m.0[a..b].iter().collect::<String>(),
                       "{at}: read {a}..{b}");
        }
    }
}

#[test]
fn small_edits_hold_up() {
    for seed in 0..120u64 {
        session(seed, 60, 6);
    }
}

/// **Bulk edits are the interesting case**, and the one the reference
/// gets wrong: a single `erase` can take most of a subtree away and a
/// single `insert` can graft several levels on, so a node comes back
/// with children many levels apart.  One rotation cannot fix that.
#[test]
fn bulk_edits_keep_the_tree_balanced() {
    for seed in 1000..1060u64 {
        session(seed, 80, 200);
    }
}

/// **The soak.**  Ignored by default because it takes minutes; run it
/// when the rope changes, which is what it is for:
///
/// ```text
/// cargo test -p gestate-editor --release -- --ignored --nocapture
/// ```
///
/// Six thousand sessions, mixed sizes, every invariant after every
/// edit.  The suite above is the part fast enough to run always; this
/// is the part that finds the thing the suite would take a year to
/// stumble on.
#[test]
#[ignore]
fn the_soak() {
    for seed in 0..3000u64 {
        session(seed, 40, 5);
    }
    for seed in 100_000..102_000u64 {
        session(seed, 50, 60);
    }
    for seed in 900_000..901_000u64 {
        session(seed, 30, 500);
    }
    println!("6000 sessions, no disagreement");
}

/// A range that is not a range, and positions past the end, are
/// **refused** rather than quietly doing something.
///
/// `balanced.py` raises `IndexError`; this returns `Err`, and the
/// difference matters only in that neither of them guesses.  An editor
/// that clamped silently would turn a cursor bug into a text bug.
#[test]
fn nonsense_is_refused() {
    let r = Rope::from_str("hello
world");
    assert!(r.insert(r.len() + 1, "x").is_err(), "past the end");
    assert!(r.erase(0, r.len() + 1).is_err(), "erasing past the end");
    assert!(r.row(r.len() + 1).is_err(), "the row of nowhere");
    assert!(r.rowpos(r.rows()).is_err(), "a row that does not exist");
    // At the very end is not past it.
    assert!(r.insert(r.len(), "!").is_ok());
    assert!(r.erase(r.len(), r.len()).is_ok());
    assert_eq!(r.row(r.len()), Ok(1));
}

/// The depth actually stays logarithmic, which is the only reason any
/// of this is a tree.
#[test]
fn the_depth_stays_logarithmic() {
    let mut rng = Rng(99);
    let mut r = Rope::new();
    for _ in 0..3000 {
        let pos = rng.upto(r.len());
        let k = 1 + rng.below(20);
        r = r.insert(pos, &word(&mut rng, k)).unwrap();
    }
    assert!(r.len() > 20_000, "only {} characters", r.len());
    // Segments hold at most `SPLIT` characters after a split, so there
    // are at least len/8 of them; an AVL over k nodes is under
    // 1.44·log2(k+2) deep.  Generous, and still far under a list.
    let k = (r.len() / 8) as f64;
    let bound = (1.44 * (k + 2.0).log2()).ceil() as u32 + 1;
    assert!(r.depth() <= bound,
            "{} characters, depth {} — the bound is {bound}",
            r.len(), r.depth());
}

/// The edges nobody types but every off-by-one lives at.
#[test]
fn the_empty_and_the_edges() {
    let e = Rope::new();
    assert_eq!(e.len(), 0);
    assert_eq!(e.rows(), 1, "an empty document still has a line to sit on");
    assert_eq!(e.text(), "");
    assert_eq!(e.row(0), Ok(0));
    assert_eq!(e.rowpos(0), Ok(0));
    assert_eq!(e.read(0, 0), Ok(String::new()));
    assert!(e.erase(0, 0).is_ok());
    assert!(e.insert(0, "").is_ok(), "inserting nothing is not an error");
    assert!(e.insert(1, "x").is_err(), "past the end of an empty rope");

    let r = Rope::from_str("ab\ncd\n");
    assert_eq!(r.rows(), 3, "a trailing newline opens a line");
    assert_eq!(r.line(0), Ok("ab".into()));
    assert_eq!(r.line(1), Ok("cd".into()));
    assert_eq!(r.line(2), Ok("".into()), "the empty last line");
    assert_eq!(r.row(0), Ok(0));
    assert_eq!(r.row(3), Ok(1), "just past the first newline");
    assert_eq!(r.rowpos(1), Ok(3));

    // Erasing everything, in one go and one character at a time.
    assert_eq!(r.erase(0, r.len()).unwrap().text(), "");
    let mut one = r.clone();
    while one.len() > 0 {
        one = one.erase(0, 1).unwrap();
        assert!(one.is_sound());
    }
    assert!(one.is_empty(), "erasing every character leaves nothing");

    // A persistent tree keeps the version it was asked from.
    let after = r.insert(0, "zz").unwrap();
    assert_eq!(r.text(), "ab\ncd\n", "the older document moved");
    assert_eq!(after.text(), "zzab\ncd\n");
}

/// Multi-byte characters are characters, not bytes.
#[test]
fn positions_count_characters() {
    let r = Rope::from_str("日本🎹ab");
    assert_eq!(r.len(), 5, "five characters, thirteen bytes");
    assert_eq!(r.read(0, 2), Ok("日本".into()));
    assert_eq!(r.read(2, 3), Ok("🎹".into()));
    let cut = r.erase(1, 3).unwrap();
    assert_eq!(cut.text(), "日ab");
    let put = r.insert(3, "—").unwrap();
    assert_eq!(put.text(), "日本🎹—ab");
}

/// Every row's range agrees with the text it is supposed to name.
#[test]
fn every_row_names_its_own_line() {
    let mut rng = Rng(4242);
    let mut r = Rope::new();
    for _ in 0..300 {
        let pos = rng.upto(r.len());
        let k = 1 + rng.below(12);
        r = r.insert(pos, &word(&mut rng, k)).unwrap();
    }
    let text = r.text();
    let want: Vec<&str> = text.split('\n').collect();
    assert_eq!(r.rows(), want.len(), "row count");
    for (i, line) in want.iter().enumerate() {
        assert_eq!(&r.line(i).unwrap(), line, "row {i}");
        let (a, b) = r.row_range(i).unwrap();
        assert_eq!(r.row(a).unwrap(), i, "the start of row {i} is on row {i}");
        assert_eq!(b - a, line.chars().count(), "row {i} width");
    }
}

/// **A loaded file is a tree, not a segment.**
///
/// The structural version of a measured fault: loading as one segment
/// made every `rowpos` a linear scan, and drawing fifty lines at row
/// 199,000 of a five-megabyte file took *1.5 seconds*.  Chunking on the
/// way in fixed it — 118 µs — but a timing test is a flaky test, so
/// what is pinned here is the shape that made the timing possible.
#[test]
fn a_loaded_document_is_already_balanced() {
    let text: String = (0..40_000).map(|i| format!("line {i}\n")).collect();
    let r = Rope::from_str(&text);
    assert_eq!(r.text(), text);
    assert_eq!(r.rows(), 40_001);
    assert!(r.is_sound(), "a freshly loaded document is unbalanced");
    // Segments hold at most 128 characters, so this is a few thousand
    // nodes and must be a few dozen levels at the very worst.
    let nodes = (r.len() as f64 / 128.0).max(1.0);
    let bound = (1.44 * (nodes + 2.0).log2()).ceil() as u32 + 2;
    assert!(r.depth() <= bound,
            "{} characters loaded to depth {} — the bound is {bound}",
            r.len(), r.depth());
    // And the far end is reachable without walking there.
    assert_eq!(r.rowpos(39_999).unwrap(),
               text.char_indices().filter(|(_, c)| *c == '\n').nth(39_998)
                   .map(|(i, _)| i + 1).unwrap());
}

/// A big paste is an insert too, and must not build one long segment.
#[test]
fn a_big_paste_is_chunked_like_a_load() {
    let mut r = Rope::from_str("head\ntail");
    let big: String = (0..5_000).map(|i| format!("{i} ")).collect();
    r = r.insert(5, &big).unwrap();
    assert!(r.is_sound());
    assert!(r.text().starts_with("head\n0 1 2 "));
    assert!(r.text().ends_with("4999 tail"));
    let nodes = (r.len() as f64 / 128.0).max(1.0);
    let bound = (1.44 * (nodes + 2.0).log2()).ceil() as u32 + 2;
    assert!(r.depth() <= bound, "pasted to depth {}", r.depth());
}
