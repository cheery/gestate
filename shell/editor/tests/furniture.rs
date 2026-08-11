//! The description the model pushes, and the gestures that come back.
//!
//! This is the one place two languages meet, so what is checked here is
//! mostly what happens when they *disagree*: a line this build does not
//! know, a field missing, a number that is not one.  The rule the tests
//! pin is that a bad line loses a knob and never the window.

use gestate_editor::furniture::{Furniture, Gesture};

const SOME: &str = "\
status\tapplied
trouble\t12\texpected a type, got `sound`
knob\tcutoff\t40\t0.42\t0\t1\tFloat
knob\tmode\t44\t3\t0\t100\tInt
bank\tlead\t60\t2\t6\t1
bank\tkeys\t70\t0\t4\t0
play\t1\t8.5
loop\t4\t12
command\tapply\tapply\tCtrl-S\tRebuild and swap it in.
command\tloop\tloop <int> <int>\t\tLoop between two bars.";

#[test]
fn a_description_reads_back_as_what_was_said() {
    let f = Furniture::read(SOME);
    assert_eq!(f.status, "applied");
    assert_eq!(f.knobs.len(), 2);
    assert_eq!(f.banks.len(), 2);
    assert_eq!(f.commands.len(), 2);
    assert!(f.playing);
    assert_eq!(f.beat, 8.5);
    assert_eq!(f.looping, Some((4.0, 12.0)));

    let cutoff = &f.knobs[0];
    assert_eq!(cutoff.name, "cutoff");
    assert_eq!((cutoff.line, cutoff.kind.as_str()), (40, "Float"));
    assert!((cutoff.fraction() - 0.42).abs() < 1e-9);
    // An `Int` knob's range is a percentage, and the fraction is the
    // same question either way — which is what lets one margin widget
    // draw both.
    assert!((f.knobs[1].fraction() - 0.03).abs() < 1e-9);

    assert_eq!(f.banks[0].listening, true);
    // **How many are sounding, not just how many exist.**  `voices 6`
    // is in the text already; that two of them are down right now is
    // the part the text cannot say.
    assert_eq!(f.banks[0].held, 2);
    assert_eq!(f.banks[0].voices, 6);
    assert_eq!(f.banks[1].held, 0);
    assert_eq!(f.banks[1].listening, false);
    assert_eq!(f.trouble[0].line, 12);
    assert!(f.trouble[0].message.starts_with("expected a type"));
}

/// **Lines are 1-based across the wire**, `audiospans.Site`'s own
/// convention, so nobody converts twice.
#[test]
fn the_margin_finds_what_belongs_to_a_line() {
    let f = Furniture::read(SOME);
    assert_eq!(f.knob_at(40).map(|k| k.name.as_str()), Some("cutoff"));
    assert_eq!(f.knob_at(41), None);
    assert!(f.trouble_at(12).is_some());
    assert!(f.trouble_at(13).is_none());
}

/// **A line this build does not know is skipped, not refused.**
///
/// The failure this must not have is the window going blank because
/// the model said something new.  A dropped line loses one knob; a
/// refusal loses the editor.
#[test]
fn an_unknown_line_costs_only_itself() {
    let f = Furniture::read("status\tfine\n\
                             wobble\t1\t2\t3\n\
                             knob\tgood\t7\t0.5\t0\t1\tFloat\n\
                             \n\
                             knob\ttoo\tshort\n\
                             bank\talso\tshort");
    assert_eq!(f.status, "fine");
    assert_eq!(f.knobs.len(), 1, "the short knob was let through");
    assert_eq!(f.knobs[0].name, "good");
    assert!(f.banks.is_empty());
}

#[test]
fn a_number_that_is_not_one_reads_as_zero_rather_than_exploding() {
    let f = Furniture::read("knob\tk\tnowhere\tmaybe\t0\t1\tFloat\n\
                             play\tyes\tsoon");
    assert_eq!(f.knobs[0].line, 0);
    assert_eq!(f.knobs[0].value, 0.0);
    assert!(!f.playing, "anything but `1` is not playing");
    assert_eq!(f.beat, 0.0);
}

#[test]
fn nothing_at_all_is_a_window_with_nothing_in_it() {
    let f = Furniture::read("");
    assert_eq!(f, Furniture::default());
    assert!(f.looping.is_none(), "no loop is not a loop of zero");
}

/// A command with no key still arrives — most have none.
#[test]
fn a_command_without_a_shortcut_is_still_a_command() {
    let f = Furniture::read(SOME);
    assert_eq!(f.commands[1].name, "loop");
    assert_eq!(f.commands[1].usage, "loop <int> <int>");
    assert_eq!(f.commands[1].key, "");
}

// ── The other direction ──────────────────────────────────────────────────

#[test]
fn a_gesture_is_a_name_and_some_literals() {
    assert_eq!(Gesture::Command("apply".into(), vec![]).line(),
               "command\tapply");
    // A command carries what it was given, in order.
    assert_eq!(Gesture::Command("loop".into(),
                                vec!["4".into(), "8".into()]).line(),
               "command\tloop\t4\t8");
    assert_eq!(Gesture::Wants("listen".into(), 0, "cut".into()).line(),
               "wants\tlisten\t0\tcut");
    assert_eq!(Gesture::Asked.line(), "asked");
    assert_eq!(Gesture::Filter("lo".into()).line(), "filter\tlo");
    assert_eq!(Gesture::Turn("cutoff".into(), 0.5).line(),
               "turn\tcutoff\t0.5");
    assert_eq!(Gesture::Note(60, true).line(), "note\t60\t1");
    assert_eq!(Gesture::Note(60, false).line(), "note\t60\t0");
    assert_eq!(Gesture::Edited.line(), "edited");
}

/// Round trip: everything the window says is a line the model can split
/// on tabs, with the verb first — the same shape in both directions.
#[test]
fn every_gesture_is_one_line_with_a_verb_first() {
    for g in [Gesture::Command("x".into(), vec!["1".into()]),
              Gesture::Filter("".into()),
              Gesture::Wants("x".into(), 1, "q".into()), Gesture::Asked,
              Gesture::Turn("y".into(), 1.0), Gesture::Note(1, true),
              Gesture::Edited] {
        let line = g.line();
        assert!(!line.contains('\n'), "{line:?} is more than one line");
        let verb = line.split('\t').next().unwrap();
        assert!(!verb.is_empty() && verb.chars().all(|c| c.is_ascii_lowercase()),
                "{verb:?} is not a verb");
    }
}
