#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# apply-consolidated-pipeline-v2.sh
#
# Applies the razor-clam consolidated pipeline from a git BUNDLE (not a patch).
# The change is delivered as two ready-made commits inside
# razor-clam-consolidated-pipeline.bundle:
#   1. Add consolidated data suite and RMD figure pipeline   (39 files)
#   2. Move 28 superseded files to 06_marked_for_deletion    (cleanup + MANIFEST)
#
# Why a bundle instead of `git am`: `git am` stages the patch in
# .git/rebase-apply and, if anything interrupts it, leaves that directory
# behind. On a OneDrive-synced clone OneDrive locks those files, so the next
# `git am` dies with "Stray .git/rebase-apply directory" and even
# `git am --abort` can't delete it. Fetching a bundle never touches
# rebase-apply, so it can't get into that state.
#
# Run from Git Bash INSIDE your razor-clam-harvest-monitoring clone:
#   ./apply-consolidated-pipeline-v2.sh [path/to/razor-clam-consolidated-pipeline.bundle]
#
# Overrides:  BRANCH=my-branch  BASE=main  REMOTE=origin  ./apply-consolidated-pipeline-v2.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="${BRANCH:-add-consolidated-pipeline}"
BASE="${BASE:-main}"
REMOTE="${REMOTE:-origin}"
BUNDLE="${1:-razor-clam-consolidated-pipeline.bundle}"
OLD_FAILED_BRANCH="razor-clam-pipeline-consolidation"
TITLE="Add consolidated data suite and RMD figure pipeline"

say()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\n\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is not installed / not on PATH."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
  die "Run this from inside your razor-clam-harvest-monitoring clone."

# resolve bundle path (given path, cwd, or repo root)
if [ ! -f "$BUNDLE" ]; then
  alt="$(git rev-parse --show-toplevel)/$(basename "$BUNDLE")"
  [ -f "$alt" ] && BUNDLE="$alt" || die "Bundle not found: $BUNDLE
Put razor-clam-consolidated-pipeline.bundle in the repo root, or pass its path."
fi
BUNDLE="$(cd "$(dirname "$BUNDLE")" && pwd)/$(basename "$BUNDLE")"
say "Using bundle: $BUNDLE"

# --- clear any half-finished am/rebase from the earlier attempt -------------
say "Clearing any stuck git am / rebase state ..."
git am --abort         >/dev/null 2>&1 || true
git rebase --abort     >/dev/null 2>&1 || true
git cherry-pick --abort >/dev/null 2>&1 || true
rm -rf .git/rebase-apply .git/rebase-merge 2>/dev/null || true
if [ -e .git/rebase-apply ] || [ -e .git/rebase-merge ]; then
  die "Could not delete .git/rebase-apply; it is locked (almost always OneDrive).
Do this, then re-run:
  1. Pause OneDrive:  tray icon -> OneDrive -> Help & Settings -> Pause syncing (2 hours),
     or quit OneDrive entirely.
  2. Close any editor/Git GUI (VS Code, gitk, SourceTree) that has the repo open.
  3. In Git Bash:   rm -rf .git/rebase-apply .git/rebase-merge
  4. Re-run this script."
fi

# --- get onto a clean base --------------------------------------------------
git checkout -q "$BASE" 2>/dev/null || die "Could not checkout '$BASE'. Resolve manually, then re-run."
git update-index -q --refresh || true
if ! git diff --quiet || ! git diff --cached --quiet; then
  die "Working tree still has uncommitted changes on '$BASE'. 'git stash' or commit, then re-run.
(If you stashed earlier and want it back later: 'git stash list' / 'git stash pop'.)"
fi

# --- make sure we have the bundle's prerequisite commit ---------------------
say "Fetching $REMOTE (so the bundle's base commit is present) ..."
git fetch --quiet "$REMOTE" || warn "fetch failed - continuing; will verify the bundle next."

say "Verifying bundle ..."
git bundle verify "$BUNDLE" >/dev/null || die "Bundle failed verification.
Its base commit is not in your repo. Run 'git fetch $REMOTE' while online, then re-run."

# --- drop leftover branches from earlier attempts ---------------------------
for b in "$OLD_FAILED_BRANCH" "$BRANCH"; do
  if git show-ref --verify --quiet "refs/heads/$b"; then
    git branch -D "$b" >/dev/null 2>&1 && say "Removed leftover branch '$b'." || true
  fi
done

# --- pull the ready-made commits out of the bundle --------------------------
say "Creating branch '$BRANCH' from the bundle ..."
git fetch "$BUNDLE" "$BRANCH:$BRANCH"
git checkout -q "$BRANCH"
say "Commits now on '$BRANCH':"; git --no-pager log --oneline -2

# --- push -------------------------------------------------------------------
say "Pushing '$BRANCH' to $REMOTE ..."
git push -u "$REMOTE" "$BRANCH"

# --- open the PR ------------------------------------------------------------
slug="$(git remote get-url "$REMOTE" | sed -E 's#^git@[^:]+:##; s#^https?://[^/]+/##; s#\.git$##')"
compare_url="https://github.com/$slug/compare/$BASE...$BRANCH?expand=1"

body_file="$(mktemp)"
cat > "$body_file" <<'PRBODY'
## Summary
Adds a consolidated tidy-CSV data suite and an R/ggplot pipeline that reproduces every figure
in methodology v9, and moves superseded files into `06_marked_for_deletion/` (moved, not deleted).

## Commit 1 - additive
- `02_data/consolidated/`: 22 tidy CSVs + `DATA_DICTIONARY.md`, standardized beach names,
  reflecting the completed 2022-23 season.
- `01_code/20260710-razor-clam-harvest-figures-pipeline.Rmd`: follows the
  razor-clam-recruitment-analysis template (`load.lib` loop, `my_theme`, dated
  `03_analyses/<YYYYMMDD>-harvest-figures/` output tree, `ggsave(dpi=300)`); reproduces all 14
  figures and re-derives the 2022-23 corrected estimates. An example run is included.
- `04_documentation/Figure_Review_and_Proposed_Improvements_v7.md`: figure-by-figure review.

## Commit 2 - cleanup
Moves 28 superseded items into `06_marked_for_deletion/` (draft methodology v2-v7 + the
unversioned draft, with v8/v9 kept; the superseded RazorClam_Harvest_Outputs dump; loose
intermediate/dedup CSVs; the raw iForms export; a duplicate 2009-10 workbook). Each keeps its
original path so any file restores with a plain `git mv`. See `06_marked_for_deletion/MANIFEST.md`.

## Notes
Figures 1-2 cover 1999-2024 (append pre-1999 rows to `historical_harvest_effort.csv` to restore
the full range); the expansion-curve / variance / band uncertainty is read from consolidated
reference tables while the CF bootstrap and CV simulations run live.
PRBODY

if command -v gh >/dev/null 2>&1; then
  say "Creating pull request with gh ..."
  if gh pr create --base "$BASE" --head "$BRANCH" --title "$TITLE" --body-file "$body_file"; then
    rm -f "$body_file"; say "Done. Pull request created."; exit 0
  fi
  warn "gh pr create failed - open it manually below."
fi
rm -f "$body_file"
say "Branch pushed. Open the pull request here:"
echo "    $compare_url"
echo
echo "Suggested title:"
echo "    $TITLE"
