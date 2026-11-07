#!/bin/bash
# Run ONCE, after all 20 hco2el runs have finished. Only reads run data and writes new files:
# reconstructs settings into each hco2el folder, prints fingerprints, makes a dated archive.
cd ~/corona3dmasters/src/runs || exit 1
if [ "$(pgrep -c corona3d_2020)" -ne 0 ]; then echo "Runs are still going. Stop: run this after they finish."; exit 1; fi
for s in hco2el_lsa hco2el_hsa; do echo "$s finished: $(grep -c "^${s}_[0-9]" summary.csv)/10"; done
for d in hco2el_*; do
  [ -d "$d" ] || continue
  cp -L "$d/Hot_H.cfg" "$d/reconstructed_Hot_H.cfg"
  grep '^bg_part._config' "$d/corona3d_2020.cfg" | awk '{print $2}' | while read f; do cp "../$f" "$d/reconstructed_$(basename "$f")"; done
  echo "reconstructed $(date +%F) from the live files in src; Hot_H.cfg link target: $(readlink "$d/Hot_H.cfg")" > "$d/reconstructed_settings_note.txt"
done
echo "--- main-config fingerprints (expect two groups of 10) ---"
for d in hco2el_*; do echo "$(grep -v '^output_dir' "$d/corona3d_2020.cfg" | md5sum | cut -c1-8) $d"; done | sort
echo "--- Hot_H fingerprints: the two files, then counts per fingerprint (expect 10 + 10) ---"
md5sum ../Hot_H.cfg ../Hot_H_HSA.cfg
md5sum hco2el_*/Hot_H.cfg | awk '{print $1}' | sort | uniq -c
echo "--- run folders whose code_changes.patch is NOT empty (expect none) ---"
for f in hco2el_*/code_changes.patch; do [ -s "$f" ] && echo "$f"; done
mkdir -p ~/backups
tar czf ~/backups/runs_hco2el_$(date +%F).tgz hco2el_* summary.csv
ls -lh ~/backups
