#!/bin/bash
# Use ONLY if the hco2el batches were interrupted (nothing running, fewer than 10 finished per set).
# Usage: ~/resume_missing.sh lsa     or     ~/resume_missing.sh hsa
# Moves any partial folder aside, then relaunches only the missing run numbers, two at a time.
cd ~/corona3dmasters/src || exit 1
if [ "$(pgrep -c corona3d_2020)" -ne 0 ]; then echo "Runs are still going: do not use this script."; exit 1; fi
case "$1" in
  lsa) CF=corona3d_2020_elastic.cfg;     HF=Hot_H.cfg;     P=hco2el_lsa;;
  hsa) CF=corona3d_2020_HSA_elastic.cfg; HF=Hot_H_HSA.cfg; P=hco2el_hsa;;
  *) echo "usage: $0 lsa|hsa"; exit 1;;
esac
missing=""
for i in $(seq 1 10); do grep -q "^${P}_${i}," runs/summary.csv || missing="$missing $i"; done
echo "missing runs for $P:$missing"
[ -z "$missing" ] && { echo "nothing to do"; exit 0; }
for i in $missing; do
  [ -d "runs/${P}_${i}" ] && mv "runs/${P}_${i}" "runs/interrupted_${P}_${i}_$(date +%s)"
done
nohup bash -c "printf '%s\n' $missing | CFGFILE=$CF HOTHFILE=$HF nice -n 10 xargs -P 2 -I{} bash -c './run_sim.sh ${P}_{} 100000 90000000 none > /dev/null 2>&1'" > batch_resume_$1.log 2>&1 &
sleep 2; pgrep -a corona3d_2020 | cut -c1-80
