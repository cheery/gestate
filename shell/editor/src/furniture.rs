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
    /// How many of its voices are sounding right now.
    pub held: usize,
    /// How many it has.
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
    /// What a played note would do — `off`, `on` or `step`.
    pub performing: String,
    /// The banks that would hear one.  **Empty means nobody**, and the
    /// keyboard is drawn dead: a control that does nothing and looks
    /// exactly like one that works is how an evening goes into deciding
    /// whether the synth is broken.
    pub heard: Vec<String>,
    /// Which notes are down.
    pub held: Vec<i32>,
    /// Which octave the drawn keyboard starts at.
    pub octave: i32,
    /// Whether the description mentioned a transport at all.
    ///
    /// **Not the same as a stopped one.**  A model that has said
    /// nothing about time has no position to show, and a readout of
    /// `1.1` invented for it would be a fact the window made up.
    pub has_transport: bool,
    /// The loop, in beats, when there is one.
    pub looping: Option<(f64, f64)>,
    pub commands: Vec<crate::palette::Entry>,
    /// What the argument being asked for could be, when one is.
    pub choices: Vec<crate::palette::Choice>,
    /// A page to read — what `what` found in the reference.
    pub page: Vec<String>,
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
                "bank" if p.len() >= 6 => f.banks.push(Bank {
                    name: p[1].into(),
                    line: num(p.get(2)),
                    held: num(p.get(3)),
                    voices: num(p.get(4)),
                    listening: p[5] == "1",
                }),
                "perform" if p.len() >= 2 => {
                    f.performing = p[1].into();
                    f.heard = p.get(2).copied().unwrap_or("")
                        .split(',').filter(|b| !b.is_empty())
                        .map(str::to_string).collect();
                    f.held = p.get(3).copied().unwrap_or("")
                        .split(',').filter_map(|n| n.parse().ok()).collect();
                    f.octave = p.get(4).and_then(|o| o.parse().ok())
                        .unwrap_or(4);
                }
                "play" => {
                    f.playing = p.get(1).copied() == Some("1");
                    f.beat = num(p.get(2));
                    f.has_transport = true;
                }
                "loop" if p.len() >= 3 => {
                    f.looping = Some((num(p.get(1)), num(p.get(2))));
                }
                "command" if p.len() >= 5 => {
                    // **The types are how the view knows to ask.**  An
                    // older model that does not send them describes a
                    // command that takes nothing, which is what it
                    // always meant here before.
                    let args = p.get(5).copied().unwrap_or("");
                    f.commands.push(crate::palette::Entry {
                        name: p[1].into(),
                        usage: p[2].into(),
                        key: p[3].into(),
                        summary: p[4].into(),
                        args: args.split(',').filter(|a| !a.is_empty())
                            .map(str::to_string).collect(),
                        reverse: p.get(6).copied().unwrap_or("").into(),
                    });
                }
                "page" => f.page.push(p.get(1).copied().unwrap_or("").into()),
                "choice" if p.len() >= 2 => {
                    f.choices.push(crate::palette::Choice {
                        text: p[1].into(),
                        note: p.get(2).copied().unwrap_or("").into(),
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

    /// And the bank declared on a line.
    pub fn bank_at(&self, line: usize) -> Option<&Bank> {
        self.banks.iter().find(|b| b.line == line)
    }

    /// Whether a keyboard should be drawn at all.
    pub fn performing(&self) -> bool {
        !self.performing.is_empty() && self.performing != "off"
    }

    /// And the complaint about a line, if any.
    pub fn trouble_at(&self, line: usize) -> Option<&Trouble> {
        self.trouble.iter().find(|t| t.line == line)
    }
}

/// What the model asks the window to do.
///
/// **The half of the wire the description cannot carry.**  Furniture
/// says what things *are* — this says what to do about them, because
/// undo, zoom and the caret are the window's own state and a command
/// like `zoomIn` has no other way to reach them.
///
/// Names and arguments, like everything else that crosses here.  An
/// order the window does not know is **skipped, not refused**, for the
/// reason an unknown furniture verb is.
///
/// ```text
/// zoom    <steps>     up the ladder; 0 goes back to where it started
/// undo
/// redo
/// goto    <line>      counting from one
/// insert  <text>
/// ```
#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Order {
    /// Steps up the ladder, or home when zero.
    Zoom(i32),
    Undo,
    Redo,
    /// Put the caret at the start of a line, counting from one.
    Goto(usize),
    /// Type this, as if it had been typed.
    Insert(String),
}

impl Order {
    /// Read one line.  `None` for anything this build does not know.
    pub fn read(line: &str) -> Option<Order> {
        let p: Vec<&str> = line.split('\t').collect();
        let arg = |i: usize| p.get(i).copied().unwrap_or("");
        match *p.first()? {
            "zoom" => Some(Order::Zoom(arg(1).parse().ok()?)),
            "undo" => Some(Order::Undo),
            "redo" => Some(Order::Redo),
            "goto" => Some(Order::Goto(arg(1).parse().ok()?)),
            // **Not trimmed and not rejected when empty**: what is being
            // inserted is somebody's text, and deciding it is not worth
            // inserting is not this layer's decision to make.
            "insert" => Some(Order::Insert(arg(1).into())),
            _ => None,
        }
    }
}

/// What the window has to say back.
///
/// **Names and literals, and nothing else** — the same rule the
/// furniture keeps in the other direction.  `Gesture` is written as one
/// tab-separated line and drained by the model when it next looks.
#[derive(Clone, PartialEq, Debug)]
pub enum Gesture {
    /// A command was chosen, with the arguments it asked for.
    Command(String, Vec<String>),
    /// The window is asking what a command's `at`th argument could be,
    /// and showing this much of a query.
    ///
    /// **The types let the view ask, and the model answers** — which of
    /// several names a query means is a decision, and it has the same
    /// one home the command ranking does.
    Wants(String, usize, String),
    /// Done asking; nothing is being offered now.
    Asked,
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
    /// A key was struck while the piano had the keyboard — the
    /// character it makes, the physical key it came from, and whether
    /// it went down.
    ///
    /// **Both, because they answer different questions.**  The
    /// character is which note it is, which follows the layout; the
    /// physical key is *which key is down*, which does not — so a
    /// release matches its press even if a modifier changed what the
    /// letter would be.
    Struck(String, String, bool),
    /// The text changed.
    Edited,
    /// Where the window's own state stands: the zoom rung and how many
    /// rungs there are, then how deep undo and redo go.
    ///
    /// **A mirror, so the model can answer without asking.**  `undo`
    /// has to say either *"undone"* or *"nothing to undo"* the moment it
    /// runs, and it cannot wait a frame to find out which — so the
    /// window volunteers the counts whenever they change and the model
    /// answers from its copy.  The alternative is a synchronous call
    /// into the rope from another thread, which is the one thing this
    /// boundary exists to prevent.
    State { zoom: usize, rungs: usize, undos: usize, redos: usize },
}

impl Gesture {
    pub fn line(&self) -> String {
        match self {
            Gesture::Command(n, args) => {
                let mut line = format!("command\t{n}");
                for a in args {
                    line.push('\t');
                    line.push_str(a);
                }
                line
            }
            Gesture::Wants(n, at, q) => format!("wants\t{n}\t{at}\t{q}"),
            Gesture::Asked => "asked".to_string(),
            Gesture::Filter(q) => format!("filter\t{q}"),
            Gesture::Turn(n, v) => format!("turn\t{n}\t{v}"),
            Gesture::Note(m, on) => {
                format!("note\t{m}\t{}", if *on { 1 } else { 0 })
            }
            Gesture::Struck(c, code, on) => {
                format!("struck\t{c}\t{code}\t{}", if *on { 1 } else { 0 })
            }
            Gesture::Edited => "edited".to_string(),
            Gesture::State { zoom, rungs, undos, redos } => {
                format!("state\t{zoom}\t{rungs}\t{undos}\t{redos}")
            }
        }
    }
}

#[cfg(test)]
mod order_tests {
    use super::*;

    #[test]
    fn orders_read_back_as_what_they_say() {
        assert_eq!(Order::read("zoom\t1"), Some(Order::Zoom(1)));
        assert_eq!(Order::read("zoom\t-1"), Some(Order::Zoom(-1)));
        assert_eq!(Order::read("undo"), Some(Order::Undo));
        assert_eq!(Order::read("goto\t42"), Some(Order::Goto(42)));
        assert_eq!(Order::read("insert\tC4"),
                   Some(Order::Insert("C4".into())));
    }

    /// An order this build does not know is skipped, not refused — the
    /// model may learn to say something before the window learns to do
    /// it, and a version mismatch must not look like a crash.
    #[test]
    fn an_unknown_order_is_skipped() {
        assert_eq!(Order::read("teleport\t3"), None);
        assert_eq!(Order::read(""), None);
        assert_eq!(Order::read("zoom\tsideways"), None);
    }

    #[test]
    fn the_state_gesture_says_all_four_numbers() {
        let g = Gesture::State { zoom: 4, rungs: 9, undos: 2, redos: 0 };
        assert_eq!(g.line(), "state\t4\t9\t2\t0");
    }
}
