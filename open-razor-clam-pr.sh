#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# open-razor-clam-pr.sh
#
# Applies razor-clam-pipeline-consolidation.patch to a clean branch off main,
# pushes it, and opens a pull request. Run from Git Bash (or any bash) INSIDE
# a clone of mattgeorgephd/razor-clam-harvest-monitoring, on a machine where
# your GitHub push access works.
#
# Usage:
#   ./open-razor-clam-pr.sh [path/to/razor-clam-pipeline-consolidation.patch]
#
# Optional overrides (env vars):
#   BRANCH=my-branch   BASE=main   REMOTE=origin   ./open-razor-clam-pr.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="${BRANCH:-razor-clam-pipeline-consolidation}"
BASE="${BASE:-main}"
REMOTE="${REMOTE:-origin}"
PATCH="${1:-razor-clam-pipeline-consolidation.patch}"
TITLE="Consolidate repo: tidy-CSV data suite, RMD figure pipeline, and cleanup"

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# --- preflight ------------------------------------------------------------
command -v git >/dev/null 2>&1 || die "git is not installed / not on PATH."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
  die "Run this from inside your razor-clam-harvest-monitoring clone."

# resolve the patch path (allow it to sit in the repo root or be given absolutely)
if [ ! -f "$PATCH" ]; then
  alt="$(git rev-parse --show-toplevel)/$(basename "$PATCH")"
  [ -f "$alt" ] && PATCH="$alt" || die "Patch file not found: $PATCH
Download razor-clam-pipeline-consolidation.patch and pass its path as the first argument."
fi
PATCH="$(cd "$(dirname "$PATCH")" && pwd)/$(basename "$PATCH")"   # absolutize
say "Using patch: $PATCH"

# clean working tree required (git am refuses to run over local changes)
git update-index -q --refresh || true
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Your working tree has uncommitted changes. Commit or 'git stash' them first."
fi

# abort any half-finished am from a previous attempt
git am --abort >/dev/null 2>&1 || true

# don't clobber an existing branch of the same name
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  die "Local branch '$BRANCH' already exists. Delete it (git branch -D $BRANCH) or run with BRANCH=other-name."
fi

# --- fetch base and branch from it ---------------------------------------
say "Fetching $REMOTE ..."
git fetch --quiet "$REMOTE"
git rev-parse --verify --quiet "$REMOTE/$BASE" >/dev/null || \
  die "$REMOTE/$BASE not found. Set BASE=<your default branch> and retry."

say "Creating branch '$BRANCH' from $REMOTE/$BASE ..."
git checkout -b "$BRANCH" "$REMOTE/$BASE" >/dev/null

# --- apply the patch ------------------------------------------------------
say "Applying patch (git am -3) ..."
if ! git am -3 "$PATCH"; then
  echo
  echo "git am hit a conflict (likely $BASE moved since the patch was made)."
  echo "  Inspect : git am --show-current-patch=diff"
  echo "  Resolve : fix files, git add -A, git am --continue"
  echo "  Abort   : git am --abort   (then: git checkout $BASE && git branch -D $BRANCH)"
  exit 1
fi
say "Commit applied:"
git --no-pager log --oneline -1

# --- push -----------------------------------------------------------------
say "Pushing '$BRANCH' to $REMOTE ..."
git push -u "$REMOTE" "$BRANCH"

# --- open the PR ----------------------------------------------------------
# derive owner/repo slug from the remote URL (handles ssh and https)
slug="$(git remote get-url "$REMOTE" | sed -E 's#^git@[^:]+:##; s#^https?://[^/]+/##; s#\.git$##')"
compare_url="https://github.com/$slug/compare/$BASE...$BRANCH?expand=1"

body_file="$(mktemp)"
cat > "$body_file" <<'PRBODY'
## Summary
Consolidates the repository around a single tidy-CSV data suite and an R/ggplot pipeline that
reproduces every figure in methodology v9, and moves superseded files out of the way (nothing
is deleted).

## Data
Adds `02_data/consolidated/`: 22 tidy CSVs + `DATA_DICTIONARY.md`, standardized beach names,
reflecting the completed 2022-23 season (4–14 May 2023 tide series restored).

## Pipeline
Adds `01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`, following the
razor-clam-recruitment-analysis template (`load.lib` loop, `my_theme`, dated
`03_analyses/<YYYYMMDD>-harvest-figures/` output tree, `ggsave(dpi=300)`). Reproduces all 14
figures in ggplot and re-derives the 2022-23 corrected estimates. Verified to run end-to-end
from a clean checkout. Includes an example run under `03_analyses/`.

## Docs
Adds methodology v9, the figure-review report, and the v8 figure source.

## Cleanup (moves only, no deletions)
Moves 42 superseded items to `06_marked_for_deletion/` (draft methodology v2–v7, v4/v5 figure
bundles, superseded harvest-DB output dump, loose intermediate CSVs, raw iForms export, a
duplicate harvest workbook, and the individual ingress/egress files now compiled into
`1993-2026_Ingress_Egress_Consolidated.xlsx`). See `06_marked_for_deletion/MANIFEST.md`.
Reversible — each item keeps its original path.

## Known limitations
Figures 1–2 cover 1999–2024 (append pre-1999 rows to `historical_harvest_effort.csv` to restore
the full range); the expansion-curve / variance / band uncertainty is read from consolidated
reference tables while the CF bootstrap and CV simulations run live.
PRBODY

if command -v gh >/dev/null 2>&1; then
  say "Creating pull request with gh ..."
  if gh pr create --base "$BASE" --head "$BRANCH" --title "$TITLE" --body-file "$body_file"; then
    rm -f "$body_file"
    say "Done. Pull request created."
    exit 0
  fi
  echo "gh pr create failed — open it manually below."
fi

rm -f "$body_file"
say "Branch pushed. Open the pull request here:"
echo "    $compare_url"
echo
echo "Suggested title:"
echo "    $TITLE"
echo
echo "(Install the GitHub CLI — https://cli.github.com — and re-run to have this script open the PR for you.)"
