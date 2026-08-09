//! Link the exported graph in, when there is one.
//!
//! `python -m gestate.export` compiles a graph to a static archive
//! (`libgraph.a`) in a directory of its own making and points
//! `GESTATE_GRAPH_DIR` at it before invoking cargo with
//! `--features engine`.  Without the feature this script does nothing
//! and the shell builds as the empty factory.

fn main() {
    println!("cargo:rerun-if-env-changed=GESTATE_GRAPH_DIR");
    if std::env::var_os("CARGO_FEATURE_ENGINE").is_none() {
        return;
    }
    let dir = std::env::var("GESTATE_GRAPH_DIR").expect(
        "the `engine` feature needs GESTATE_GRAPH_DIR pointing at the \
         directory `python -m gestate.export` wrote `libgraph.a` into",
    );
    println!("cargo:rustc-link-search=native={dir}");
    println!("cargo:rustc-link-lib=static=graph");
    // `llvm.floor.f64` at -O0 becomes a libm call; `audiollvm.build`
    // records the segfault that taught it `-lm`, and static linking
    // changes nothing about that lesson.
    println!("cargo:rustc-link-lib=m");
}
