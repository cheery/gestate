# templates — what the language can do, ready to paste

One file, one idea.  The editor's `template` command lists these by
name, shows the first sentence of the header, and inserts **the body
with every comment taken off** — because the documentation is here to
help you choose, and once you have chosen it is somebody else's prose
sitting in your file.

The rule, in full:

* **The header is the description.**  Full-line `#:` comments at the top,
  before the first declaration.  The first sentence is what the palette
  shows; the rest is the page you can read before choosing.
* **The body is what you get.**  Everything from the first declaration
  on, with full-line comments removed and blank runs collapsed.
* **Comments must be full lines.**  A trailing `# like this` is left
  alone, because deciding whether a `#` inside a string is a comment
  needs the tokenizer, and a template is not worth a second front end.
  If a template wants a note kept, it puts it at the end of a line.

`test_templates.py` builds every one of them against a synth skeleton,
so a template that stops compiling is a failing test rather than a stale
file — the promise `examples/README.md` already makes for the examples.

Adding one is adding a file.  Nothing lists them but the directory.
