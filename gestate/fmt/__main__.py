"""CLI entry point for the Gestate autoformatter.

Usage::

    python -m gestate.fmt < file.ges          # stdin → stdout
    python -m gestate.fmt file.ges            # file   → stdout
    python -m gestate.fmt file.ges -o out.ges # file   → file
    python -m gestate.fmt -c "expr"           # inline code → stdout
"""

from __future__ import annotations

import argparse
import sys

from .format import format as fmt_source


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gestate.fmt",
        description="Format Gestate source code.",
    )
    ap.add_argument("file", nargs="?", help="Input file (reads stdin if omitted)")
    ap.add_argument("-o", "--output", dest="output", metavar="FILE",
                    help="Write output to FILE instead of stdout")
    ap.add_argument("-c", dest="code", metavar="CODE",
                    help="Format an inline code string")
    args = ap.parse_args(argv)

    try:
        if args.code is not None:
            result = fmt_source(args.code)
        elif args.file:
            with open(args.file) as f:
                result = fmt_source(f.read())
        else:
            result = fmt_source(sys.stdin.read())

        if args.output:
            with open(args.output, "w") as f:
                f.write(result)
                if not result.endswith("\n"):
                    f.write("\n")
        else:
            sys.stdout.write(result)
            if not result.endswith("\n"):
                sys.stdout.write("\n")
    except Exception as e:
        print(f"gestate.fmt: error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
