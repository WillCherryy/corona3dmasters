#!/bin/bash
# Read-only status report for the corona3d runs. Usage: ~/check_runs.sh
cd ~/corona3dmasters/src || exit 1
echo "=== $(date) ==="
echo "Ubuntu up since: $(uptime -s)   (should be BEFORE your batches started)"
n=$(pgrep -c corona3d_2020)
echo "model processes running: $n"
for p in $(pgrep corona3d_2020); do
  r=$(readlink /proc/$p/cwd)
  age=$(( ( $(date +%s) - $(stat -c %Y "$r/console.out") ) / 60 ))
  line=$(tail -c 400 "$r/console.out" | tr '\r' '\n' | grep . | tail -n 1 | cut -c1-100)
  flag=""; [ "$age" -gt 20 ] && flag="   <-- NO OUTPUT FOR ${age} MIN: CHECK"
  echo "  $(basename "$r") (running $(ps -o etime= -p "$p" | tr -d ' ')): $line$flag"
done
for s in baseline hsa_baseline hco2el_lsa hco2el_hsa; do
  echo "finished $s: $(grep -c "^${s}_[0-9]" runs/summary.csv) / 10"
done
echo "batch logs (should be empty):"; cat batch_hco2el_lsa.log batch_hco2el_hsa.log 2>/dev/null | head -n 5
echo "backup loop running: $(pgrep -f sync_runs.sh | wc -l)   last pass: $(cat ~/sync_last.txt 2>/dev/null)"
df -h ~ | tail -n 1
if [ "$n" -eq 0 ]; then
  echo "NOTHING RUNNING. If a hco2el count above is below 10, runs were interrupted: use ~/resume_missing.sh"
fi
