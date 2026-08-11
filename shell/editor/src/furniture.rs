//! What the model tells the window — `spec/workbench.md`'s
//! *"the chrome is a description"*.
//!
//! The view owns the window, so the view draws everything; the model
//! cannot reach a canvas and must not learn to.  So the model publishes
//! a description of the furniture and the window draws it, which is
//! `shell/panel`'s pattern exactly — a descriptor in, a display list
//! out, one painter — and the reason the editor and the plugin panel
//! will look like one application rather than two.
//!
//! **Flat lines, tab-separated, with a verb first.**  The same shape
//! `crust`'s program format and the session trace already use, and for
//! the same reasons: it is readable in a terminal when something is
//! wrong, it needs no library on either side, and **nothing in it is a
//! pointer into the other side's heap** — which is not minimalism for
//! its own sake but the rule about where two runtimes' lifetimes meet.
//!
//! ```text
//! status  <sentence>
//! trouble <line>  <message>
//! knob    <name>  <line>  <value>  <lo>  <hi>  <kind>
//! bank    <name>  <line>  <voices>  <listening>
//! play    <0|1>   <beat>
//! loop    <from>  <to>
//! command <name>  <usage>  <key>  <summary>
//! ```
//!
//! An unknown verb is **skipped, not refused**: the model may learn to
//! say something this build does not draw yet, and a window that
//! refused to render because of one unfamiliar line would be a version
//! mismatch that looks like a crash.

/// One parameter, at the line that declares it.
#[derive(Clone, PartialEq, Debug)]
pub struct Knob {
    pub name: String,
    /// The line it was declared on, counting from **one** —
    /// `audiospans.Site`'s own convention, kept across the wire so
    /// nobody converts twice.
    pub line: usize,
    pub value: f64,
    pub lo: f64,
    pub hi: f64,
    /// `"Int"` or `"Float"` — what the channel carries.
    pub kind: String,
}

impl Knob {
    /// Where the value sits in its own range, 0…1.
    pub fn fraction(&self) -> f64 {
        let span = self.hi - self.lo;
        if span.abs() < f64::EPSILON {
            0.0
        } else {
            ((self.value - self.lo) / span).clamp(0.0, 1.0)
        }
    }
}

/// One `voices` bank, at its declaration.
#[derive(Clone, PartialEq, Debug)]
pub struct Bank {
    pub name: String,
    pub line: usize,
    pub voices: usize,
    pub listening: bool,
}

/// What the compiler had to say, and where.
#[derive(Clone, PartialEq, Debug)]
pub struct Trouble {
    /// The line it names, or `0` for a complaint about nowhere.
    pub line: usize,
    pub message: String,
}

#[derive(Clone, PartialEq, Debug, Default)]
pub struct Furniture {
    pub status: String,
    pub trouble: Vec<Trouble>,
    pub knobs: Vec<Knob>,
    pub banks: Vec<Bank>,
    pub playing: bool,
    pub beat: f64,
    /// The loop, in beats, when there is one.
    pub looping: Option<(f64, f64)>,
    pub commands: Vec<crate::palette::Entry>,
}

fn num<T: std::str::FromStr + Default>(s: Option<&&str>) -> T {
    s.and_then(|v| v.parse().ok()).unwrap_or_default()
}

impl Furniture {
    /// Read a description.  **Never fails**: a line it cannot make
    /// sense of is dropped and the rest is kept.
    ///
    /// That is deliberate rather than lax.  This is the one place two
    /// languages meet, and the failure it must not have is *the window
    /// going blank because the model said something new*.  A dropped
    /// line loses one knob; a refusal loses the editor.
    pub fn read(text: &str) -> Furniture {
        let mut f = Furniture::default();
        for line in text.lines() {
            let p: Vec<&str> = line.split('\t').collect();
            match p.first().copied().unwrap_or("") {
                "status" => f.status = p.get(1).copied().unwrap_or("").into(),
                "trouble" => f.trouble.push(Trouble {
                    line: num(p.get(1)),
                    message: p.get(2).copied().unwrap_or("").into(),
                }),
                "knob" if p.len() >= 7 => f.knobs.push(Knob {
                    name: p[1].into(),
                    line: num(p.get(2)),
                    value: num(p.get(3)),
                    lo: num(p.get(4)),
                    hi: num(p.get(5)),
                    kind: p[6].into(),
                }),
                "bank" if p.len() >= 5 => f.banks.push(Bank {
                    name: p[1].into(),
                    line: num(p.get(2)),
                    voices: num(p.get(3)),
                    listening: p[4] == "1",
                }),
                "play" => {
                    f.playing = p.get(1).copied() == Some("1");
                    f.beat = num(p.get(2));
                }
                "loop" if p.len() >= 3 => {
                    f.looping = Some((num(p.get(1)), num(p.get(2))));
                }
                "command" if p.len() >= 5 => {
                    f.commands.push(crate::palette::Entry {
                        name: p[1].into(),
                        usage: p[2].into(),
                        key: p[3].into(),
                        summary: p[4].into(),
                    });
                }
                // Unknown, or too short to mean anything.  Skipped.
                _ => {}
            }
        }
        f
    }

    /// The knob declared on a line, if any — what the margin draws.
    pub fn knob_at(&self, line: usize) -> Option<&Knob> {
        self.knobs.iter().find(|k| k.line == line)
    }

    /// And the complaint about a line, if any.
    pub fn trouble_at(&self, line: usize) -> Option<&Trouble> {
        self.trouble.iter().find(|t| t.line == line)
    }
}

/// What the window has to say back.
///
/// **Names and literals, and nothing else** — the same rule the
/// furniture keeps in the other direction.  `Gesture` is written as one
/// tab-separated line and drained by the model when it next looks.
#[derive(Clone, PartialEq, Debug)]
pub enum Gesture {
    /// A command was chosen.
    Command(String),
    /// The palette is showing this query and wants the entries for it.
    ///
    /// **The ranking is the model's**, so the view asks rather than
    /// sorting: which commands a query means is a decision, and it has
    /// one home (`gestate/session.py`).
    Filter(String),
    /// A knob was dragged, to a value in its own range.
    Turn(String, f64),
    /// A note was played or released.
    Note(i32, bool),
    /// The text changed.
    Edited,
}

impl Gesture {
    pub fn line(&self) -> String {
        match self {
            Gesture::Command(n) => format!("command\t{n}"),
            Gesture::Filter(q) => format!("filter\t{q}"),
            Gesture::Turn(n, v) => format!("turn\t{n}\t{v}"),
            Gesture::Note(m, on) => {
                format!("note\t{m}\t{}", if *on { 1 } else { 0 })
            }
            Gesture::Edited => "edited".to_string(),
        }
    }
}
