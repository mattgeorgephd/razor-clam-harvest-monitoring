#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# apply-consolidated-pipeline.sh
#
# Applies razor-clam-consolidated-pipeline.patch (purely additive: consolidated
# data suite + RMD pipeline + figure-review report + example run) to a fresh
# branch off your CURRENT main, pushes it, and opens a pull request.
#
# Safe to run after the earlier attempt failed: it first aborts any in-progress
# git am and cleans up the empty branch that attempt left behind.
#
# Run from Git Bash INSIDE your razor-clam-harvest-monitoring clone:
#   ./apply-consolidated-pipeline.sh [path/to/razor-clam-consolidated-pipeline.patch]
#
# Optional overrides:  BRANCH=my-branch  BASE=main  REMOTE=origin  ./apply-consolidated-pipeline.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="${BRANCH:-add-consolidated-pipeline}"
BASE="${BASE:-main}"
REMOTE="${REMOTE:-origin}"
PATCH="${1:-razor-clam-consolidated-pipeline.patch}"
OLD_FAILED_BRANCH="razor-clam-pipeline-consolidation"   # from the earlier attempt
TITLE="Add consolidated data suite and RMD figure pipeline"

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\n\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is not installed / not on PATH."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
  die "Run this from inside your razor-clam-harvest-monitoring clone."

# resolve patch path (repo root or given path)
if [ ! -f "$PATCH" ]; then
  alt="$(git rev-parse --show-toplevel)/$(basename "$PATCH")"
  [ -f "$alt" ] && PATCH="$alt" || die "Patch not found: $PATCH
Download razor-clam-consolidated-pipeline.patch and pass its path as the first argument."
fi
PATCH="$(cd "$(dirname "$PATCH")" && pwd)/$(basename "$PATCH")"
say "Using patch: $PATCH"

# --- recover from the earlier failed attempt ------------------------------
say "Cleaning up any half-finished git am from the earlier run ..."
git am --abort >/dev/null 2>&1 || true

# get onto a real branch and off the failed one
git checkout -q "$BASE" 2>/dev/null || true

# working tree must be clean now
git update-index -q --refresh || true
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Working tree still has uncommitted changes. 'git stash' or commit them, then re-run."
fi

# --- fetch current base ---------------------------------------------------
say "Fetching $REMOTE ..."
git fetch --quiet "$REMOTE"
git rev-parse --verify --quiet "$REMOTE/$BASE" >/dev/null || \
  die "$REMOTE/$BASE not found. Set BASE=<your default branch> and retry."

# delete the empty branch the failed attempt created (only if it's just sitting at base)
if git show-ref --verify --quiet "refs/heads/$OLD_FAILED_BRANCH"; then
  if [ "$(git rev-parse "$OLD_FAILED_BRANCH")" = "$(git rev-parse "$REMOTE/$BASE")" ]; then
    git branch -D "$OLD_FAILED_BRANCH" >/dev/null 2>&1 || true
    say "Removed the empty '$OLD_FAILED_BRANCH' branch from the earlier attempt."
  fi
fi

# don't clobber an existing branch of the new name
git show-ref --verify --quiet "refs/heads/$BRANCH" && \
  die "Branch '$BRANCH' already exists. Delete it (git branch -D $BRANCH) or run with BRANCH=other-name."

say "Creating branch '$BRANCH' from $REMOTE/$BASE ..."
git checkout -q -b "$BRANCH" "$REMOTE/$BASE"

# --- apply (additive, so this should be conflict-free) --------------------
say "Applying patch ..."
if ! git am -3 "$PATCH"; then
  echo
  echo "  Inspect : git am --show-current-patch=diff"
  echo "  Abort   : git am --abort   (then: git checkout $BASE && git branch -D $BRANCH)"
  die "git am failed unexpectedly for an additive patch — send me the output above."
fi
say "Commit applied:"; git --no-pager log --oneline -1

# --- push -----------------------------------------------------------------
say "Pushing '$BRANCH' to $REMOTE ..."
git push -u "$REMOTE" "$BRANCH"

# --- open the PR ----------------------------------------------------------
slug="$(git remote get-url "$REMOTE" | sed -E 's#^git@[^:]+:##; s#^https?://[^/]+/##; s#\.git$##')"
compare_url="https://github.com/$slug/compare/$BASE...$BRANCH?expand=1"

body_file="$(mktemp)"
cat > "$body_file" <<'PRBODY'
## Summary
Adds a consolidated tidy-CSV data suite and an R/ggplot pipeline that reproduces every figure
in methodology v9. Purely additive — no existing files are moved or deleted.

## Data
`02_data/consolidated/`: 22 tidy CSVs + `DATA_DICTIONARY.md`, standardized beach names,
reflecting the completed 2022-23 season (4–14 May 2023 tide series restored).

## Pipeline
`01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`, following the
razor-clam-recruitment-analysis template (`load.lib` loop, `my_theme`, dated
`03_analyses/<YYYYMMDD>-harvest-figures/` output tree, `ggsave(dpi=300)`). Reproduces all 14
figures in ggplot and re-derives the 2022-23 corrected estimates. Verified to run end-to-end
from a clean checkout; an example run is included under `03_analyses/`.

## Docs
`04_documentation/Figure_Review_and_Proposed_Improvements_v7.md`: figure-by-figure review.

## Notes
Figures 1–2 cover 1999–2024 (append pre-1999 rows to `historical_harvest_effort.csv` to restore
the full range); the expansion-curve / variance / band uncertainty is read from consolidated
reference tables while the CF bootstrap and CV simulations run live.
PRBODY

if command -v gh >/dev/null 2>&1; then
  say "Creating pull request with gh ..."
  if gh pr create --base "$BASE" --head "$BRANCH" --title "$TITLE" --body-file "$body_file"; then
    rm -f "$body_file"; say "Done. Pull request created."; exit 0
  fi
  echo "gh pr create failed — open it manually below."
fi
rm -f "$body_file"
say "Branch pushed. Open the pull request here:"
echo "    $compare_url"
echo
echo "Suggested title:"
echo "    $TITLE"
