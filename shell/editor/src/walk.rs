//! The walked canvas's payload, read — not yet walked.
//!
//! `spec/workbench.md` §"The canvas walks over crust": the model hands
//! this window a compiled substrate to animate for itself — the
//! serialized G-machine program, the entry to force, the `Sub`
//! constructor tags (a tag is a position in that program's own table,
//! so it cannot be derived, only carried), and the declared channels
//! with the values as they stand.  This module is the reading of it,
//! and only the reading: what walks it comes later, and keeping the
//! two apart is what lets the reading be tested without a machine.
//!
//! **Lenient about everything but what makes walking possible** — the
//! furniture's rule, for the furniture's reason: this is a place two
//! languages meet, and the failure it must not have is the window
//! going blank because the model said something new.  An unknown
//! header verb is skipped, so the model may learn a word before this
//! window reads it; but a payload with no program, no entry or a tag
//! table of the wrong size refuses whole, because walking half a
//! canvas draws somebody's artwork wrong rather than not at all.

/// How many constructor tags the walk needs: `gestate_panel`'s
/// `SubTags` twelve, then `Cons` and `Nil` — not `Sub` constructors,
/// but what a `Label`'s `String` is made of.  The same fourteen
/// `export._SUB_CONS` counts, in the same order, and the count is the
/// check: a table of another size is another program's idea of `Sub`.
pub const TAGS: usize = 14;

/// A canvas this window has been handed to walk.
#[derive(Clone, PartialEq, Debug)]
pub struct Walk {
    /// The global to force — `main`, bound to the file's `substrate`.
    pub entry: String,
    /// The constructor tags, `TAGS` of them, `SubTags` order.
    pub tags: Vec<i64>,
    /// Every declared channel in declaration order, with the value it
    /// currently holds when one has been written — so a rebuild does
    /// not snap a fader back to its default.
    pub chans: Vec<(String, Option<f64>)>,
    /// The serialized program, verbatim — `crust.serialize`'s text.
    pub program: String,
}

impl Walk {
    /// Read a payload, or decide there is nothing to walk.
    ///
    /// `None` for the empty payload — the model taking the canvas
    /// back — and for one this build cannot walk whole.  The caller
    /// treats both the same way: nothing walks, and the window is
    /// still a window.
    pub fn read(text: &str) -> Option<Walk> {
        let mut entry = String::new();
        let mut tags: Vec<i64> = Vec::new();
        let mut chans: Vec<(String, Option<f64>)> = Vec::new();
        let mut lines = text.lines();
        for line in lines.by_ref() {
            let p: Vec<&str> = line.split('\t').collect();
            match p.first().copied().unwrap_or("") {
                "entry" => entry = p.get(1).copied().unwrap_or("").into(),
                "tags" => {
                    tags = p.get(1).copied().unwrap_or("")
                        .split_whitespace()
                        .filter_map(|t| t.parse().ok())
                        .collect();
                }
                "chan" => {
                    let Some(name) = p.get(1) else { continue };
                    if name.is_empty() {
                        continue;
                    }
                    chans.push(((*name).into(),
                                p.get(2).and_then(|v| v.parse().ok())));
                }
                // The program is everything after this line, verbatim
                // — it is another format's text, and reading it is the
                // machine's business, not this parser's.
                "program" => break,
                // An unknown verb is skipped, not refused: the model
                // may learn a word before this window reads it.
                _ => {}
            }
        }
        let program: String = lines.collect::<Vec<_>>().join("\n");
        if entry.is_empty() || tags.len() != TAGS || program.is_empty() {
            return None;
        }
        Some(Walk { entry, tags, chans, program })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SOME: &str = "entry\tmain\n\
        tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\n\
        chan\tdragged\t0.75\n\
        chan\tuntouched\n\
        program\n\
        crust 1\n\
        block\n\
        I PushInt 3";

    #[test]
    fn a_payload_reads_back_as_what_was_said() {
        let w = Walk::read(SOME).expect("a canvas to walk");
        assert_eq!(w.entry, "main");
        assert_eq!(w.tags.len(), TAGS);
        assert_eq!(w.chans,
                   vec![("dragged".into(), Some(0.75)),
                        ("untouched".into(), None)]);
        assert!(w.program.starts_with("crust 1"));
        assert!(w.program.ends_with("I PushInt 3"),
                "the program did not cross verbatim");
    }

    #[test]
    fn an_empty_payload_is_the_canvas_taken_back() {
        assert_eq!(Walk::read(""), None);
    }

    #[test]
    fn half_a_canvas_refuses_whole() {
        // Walking with a truncated tag table would draw the artwork
        // wrong rather than not at all.
        let short = SOME.replace("tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14",
                                 "tags\t1 2 3");
        assert_eq!(Walk::read(&short), None);
        // And no program is nothing to walk, whatever the header says.
        let headless = "entry\tmain\n\
            tags\t1 2 3 4 5 6 7 8 9 10 11 12 13 14\nprogram\n";
        assert_eq!(Walk::read(headless), None);
    }

    #[test]
    fn an_unknown_verb_loses_a_word_and_not_the_canvas() {
        let extra = SOME.replace("chan\tdragged\t0.75",
                                 "reading\tpeak\t0.5\nchan\tdragged\t0.75");
        let w = Walk::read(&extra).expect("still walks");
        assert_eq!(w.chans.len(), 2);
    }
}
