---
name: a-build-is-not-an-instrument-until-it-has-failed
description: "cargo build -p gestate-editor prints Compiling and Finished while compiling none of window.rs, which sits behind the off-by-default `window` feature — before trusting any build as evidence, break the file on purpose and watch it go red"
metadata:
  type: feedback
---

**`cargo build -p gestate-editor` does not compile `shell/editor/src/window.rs`.**
It is behind `#[cfg(feature = "window")]` and the crate's default
features are empty, so the build prints *Compiling gestate-editor* and
*Finished*, exits 0, and has type-checked none of the file you just
edited.  The honest spellings are `--features window` (the lib) or
`--features capi` (what a host loads); the release library a driven run
photographs is a third command again —
`cargo build --release --features capi --target-dir shell/editor/target`,
which `gestate/editor.py` runs for itself and `tools/driven.py`
documents, because the root's `target/` holds a **different** file.

**Why:** 2026-09-11, building the sideways carry.  A green build was
read as *the window code compiles*; then an edit stopped changing the
output and twenty minutes went into whether cargo's freshness tracking
had broken.  It had not.  What settled it was appending

    fn __probe() { let _: i32 = "no"; }

to the file and watching the build stay green — at which point the
feature flag was obvious and had been all along.  A green from a
command that never read the file is the same failure as
[[dont-conclude-from-a-shallow-check]]'s empty search result: evidence
about the instrument, reported as evidence about the world.

**How to apply:** the first time a build, a test selection or a grep is
going to carry a conclusion, **make it fail on purpose once.**  Break
the file, run the command, see red, put the file back — and put the
file back in a command that is not the fenced one, or the backup is
gone ([[the-fence-takes-git-identity]]).  Thirty seconds, and it is the
difference between an instrument and a habit.  The same move is already
the tree's rule for a repair: [[a-targeted-set-is-a-claim]] says a
batch's chosen test files are a claim about coverage and can be false.
Related: [[gestate-instruments]], [[gestate-testing-standard]].
