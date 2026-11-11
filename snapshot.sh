#!/usr/bin/env bash
# Refresh the copies that live outside this folder, then stage everything for a commit.
# Run it before each commit:  ./snapshot.sh && git commit -m "..." && git push
#   scratch/two-hosts/  <- ns-3.49/scratch/two-hosts/   (the simulation scenario; the ns-3 tree itself is not in the repo)
#   HARNESS_SPEC.md     <- ~/ADRS/openevolve/HARNESS_SPEC.md   (the build specification)
set -euo pipefail
cd "$(dirname "$0")"
rm -rf scratch/two-hosts   # an exact copy: a file renamed or removed in the ns-3 tree must not stay behind here
mkdir -p scratch/two-hosts
cp -p ns-3.49/scratch/two-hosts/* scratch/two-hosts/
cp -p "$HOME/ADRS/openevolve/HARNESS_SPEC.md" HARNESS_SPEC.md
git add -A
git status --short
