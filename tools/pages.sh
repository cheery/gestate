#!/usr/bin/env bash
#: asked-by: Henri, 2026-08-29 - "R2 ja keeper.md -sivulle ohje ajaa tools/pages.sh silloin tällöin. Tämän sivuston ei tarvitse olla tuore koko ajan."
#
# pages.sh — the pieces as a site, onto the `gh-pages` branch.
#
#     tools/pages.sh              # generate, commit to gh-pages, push
#     tools/pages.sh --no-push    # the same, and leave the push to you
#
# `card:online.md` question 8, his pick: a branch this script fills and
# he pushes now and then, rather than a workflow that keeps the site
# fresh — *"tämän sivuston ei tarvitse olla tuore koko ajan."*  So the
# site is as fresh as the last run, `keeper.md` says when to run it,
# and nothing outside this tree builds anything.
#
# The branch is written without touching the working tree or the
# index: the generated directory becomes a tree object through a
# temporary index, that tree a commit on top of the branch's last, and
# the branch ref moves.  `git add -A` here adds the *generated* site,
# not the project (`doc/memory/commit-what-you-wrote.md` is about the
# latter).  Pages is set once, by hand, in the repository's settings:
# source "Deploy from a branch", branch `gh-pages`, folder `/`.

set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
push=1
case "${1:-}" in
    "") ;;
    --no-push) push=0 ;;
    --help|-h) awk 'NR>2 && /^#/ { sub(/^# ?/, ""); print; next } NR>2 { exit }' \
                   "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "pages: unknown argument \`$1\`" >&2; exit 2 ;;
esac

py="$here/.venv/bin/python"; [ -x "$py" ] || py=$(command -v python3)
out=$(mktemp -d -t gestate-pages.XXXXXX)
# The temporary index lives *outside* the generated directory: inside
# it, its own `.index.lock` was added to the site on the first run.
scratch=$(mktemp -d -t gestate-pages-index.XXXXXX)
trap 'rm -rf "$out" "$scratch"' EXIT

echo "generating examples/audio → $out"
(cd "$here" && "$py" -m gestate.online examples/audio -o "$out")

source_commit=$(git -C "$here" rev-parse --short HEAD)
export GIT_INDEX_FILE="$scratch/index"
git -C "$here" --work-tree="$out" add -A
tree=$(git -C "$here" write-tree)
unset GIT_INDEX_FILE
parent=()
if git -C "$here" show-ref --verify --quiet refs/heads/gh-pages; then
    parent=(-p "$(git -C "$here" rev-parse refs/heads/gh-pages)")
    if [ "$(git -C "$here" rev-parse "refs/heads/gh-pages^{tree}")" = "$tree" ]; then
        echo "gh-pages already holds this site (from $source_commit or an identical tree); nothing to commit."
        exit 0
    fi
fi
commit=$(git -C "$here" commit-tree "$tree" "${parent[@]}" \
             -m "pages: the pieces, generated from $source_commit")
git -C "$here" update-ref refs/heads/gh-pages "$commit"
echo "gh-pages → $(git -C "$here" rev-parse --short "$commit") (from $source_commit)"

if [ "$push" = 1 ]; then
    git -C "$here" push origin gh-pages
else
    echo "not pushed; when you are ready:  git push origin gh-pages"
fi
