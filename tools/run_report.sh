#!/bin/bash
# Read-only report of what each run used and what it gave: commit, branch, executable fingerprint, config files, fingerprints of the
# data files named by the species configs (including the channel files), the final tallies, the channel statistics and the summary row.
# Usage: ~/run_report.sh label [label ...]        (RUNS=<folder> to use another runs folder; default ~/corona3dmasters/src/runs)
RUNS=${RUNS:-$HOME/corona3dmasters/src/runs}
for L in "$@"; do
  d=$RUNS/$L
  echo "===================== $L"
  [ -d "$d" ] || { echo "no such run folder: $d"; continue; }
  cat "$d/run_info.txt"
  echo "--- uncommitted code changes at launch (expect 0 bytes and 0 entries): $(wc -c < "$d/code_changes.patch") bytes, $(wc -l < "$d/git_status.txt") entries"
  echo "--- species configs and the data files they name (md5, first 8 characters):"
  grep -E '^bg_part[0-9]+_config' "$d/corona3d_2020.cfg" | awk '{print $2}' | while read f; do
    echo "  $f   [$(md5sum "$d/$f" | cut -c1-8)]"
    grep -E '^(total_sigma_file|channel_file|energy[0-9]+_file)[[:space:]]' "$d/$f" | awk '{print $2}' | while read g; do
      if [ -f "$d/$g" ]; then echo "    $(md5sum "$d/$g" | cut -c1-8)  $g"; else echo "    MISSING $g"; fi
    done
  done
  echo "--- results:"
  grep -E "^Number of collisions|^Number of day side escaped|^Number of night side escaped|^Global production rate|^Total loss rate|^Channel statistics|^Collisions per channel" "$d/console.out"
  grep "^$L," "$RUNS/summary.csv"
done
