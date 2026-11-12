#!/bin/bash
# Read-only: one line per run folder, so you can see what every run is.
# Usage: ~/run_register.sh [path to a runs folder]   (default: ~/corona3dmasters/src/runs)
RUNS=${1:-$HOME/corona3dmasters/src/runs}
cd "$RUNS" || exit 1
RUNNING=$(for p in $(pgrep corona3d_2020); do readlink /proc/$p/cwd; done)
printf "%-30s %-15s %-8s %-6s %-34s %-16s %-8s %-9s %s\n" label started particles seed config hoth commit exe status
for d in */; do
  d=${d%/}; f=$d/run_info.txt
  [ -f "$f" ] || continue
  start=$(sed -n 1p "$f" | awk '{print $2,$3,$4}')
  np=$(grep '^particles' "$f" | awk '{print $2}')
  seed=$(grep '^particles' "$f" | awk '{print $6}')
  cfg=$(grep '^config' "$f" | awk '{print $2}'); hoth=$(grep '^config' "$f" | awk '{print $4}')
  com=$(grep '^commit ' "$f" | awk '{print $2}')
  exe=$(grep '^executable_md5' "$f" | awk '{print substr($2,1,8)}')
  base=${d%_old_code}
  if echo "$RUNNING" | grep -qx "$RUNS/$d"; then st="RUNNING"
  elif grep -q "^$base," summary.csv 2>/dev/null; then st="finished"
  else st="no result"; fi
  printf "%-30s %-15s %-8s %-6s %-34s %-16s %-8s %-9s %s\n" "$d" "$start" "$np" "$seed" "${cfg:--}" "${hoth:--}" "${com:--}" "${exe:--}" "$st"
done
