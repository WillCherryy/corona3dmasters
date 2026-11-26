#!/bin/bash
# Back up all corona3d runs to OneDrive (from Ubuntu/WSL), verify the copy, and check the finished runs. Read-only for the runs.
# Usage: bash ~/backup_to_onedrive.sh            (auto-detects the OneDrive folder)
#        ODIR="/mnt/c/Users/will/OneDrive - Some Name" bash ~/backup_to_onedrive.sh     (to choose it yourself)
SRC=$HOME/corona3dmasters/src

echo "=================== 0. WHICH ONEDRIVE FOLDER?"
if [ -z "$ODIR" ]; then
  for v in OneDrive OneDriveCommercial OneDriveConsumer; do
    w=$(cmd.exe /c "echo %$v%" 2>/dev/null | tr -d '\r')
    if [ -n "$w" ] && [ "$w" != "%$v%" ]; then echo "  Windows says %$v% = $w"; [ -z "$ODIR" ] && [ "$v" = OneDrive ] && ODIR=$(wslpath "$w" 2>/dev/null); fi
  done
fi
echo "  OneDrive-like folders under /mnt/c/Users:"; ls -d /mnt/c/Users/*/OneDrive* 2>/dev/null | sed 's/^/    /'
if [ -z "$ODIR" ] || [ ! -d "$ODIR" ]; then
  echo "  NO USABLE ONEDRIVE FOLDER FOUND (ODIR='$ODIR'). Pick one of the folders listed above (it must be the one Windows Explorer shows as OneDrive) and run again with ODIR=\"...\" bash ~/backup_to_onedrive.sh"
  exit 1
fi
echo "  USING: $ODIR"
echo "  what the old hourly sync script was copying to:"; grep -n "mnt/c" ~/sync_runs.sh 2>/dev/null | sed 's/^/    /' || echo "    (no ~/sync_runs.sh)"

echo; echo "=================== 1. WHAT IS TO BE BACKED UP"
cd "$SRC" || exit 1
echo "  runs folders: $(ls runs | wc -l), total size $(du -sh runs | cut -f1); disk free in Ubuntu: $(df -h ~ | tail -n 1 | awk '{print $4}')"

echo; echo "=================== 2. KEEP THE EXECUTABLE THAT MADE EVERY SET SO FAR"
if [ "$(md5sum corona3d_2020 | cut -c1-8)" = "6236607e" ]; then
  [ -f ~/corona3d_2020_hco2elfix_6236607e ] || cp corona3d_2020 ~/corona3d_2020_hco2elfix_6236607e
  echo "  saved as ~/corona3d_2020_hco2elfix_6236607e (md5 $(md5sum ~/corona3d_2020_hco2elfix_6236607e | cut -c1-8))"
else
  echo "  executable md5 is $(md5sum corona3d_2020 | cut -c1-8), not 6236607e: NOT copied (check before relying on it)"
fi

echo; echo "=================== 3. ARCHIVE AND COPY TO ONEDRIVE, WITH CHECKSUMS"
mkdir -p ~/backups; STAMP=$(date +%F_%H%M)
tar czf ~/backups/corona3d_all_runs_$STAMP.tgz -C "$SRC" runs
HELP=$(cd ~ && ls *.sh corona3d_2020_hco2elfix_6236607e 2>/dev/null)
[ -n "$HELP" ] && tar czf ~/backups/corona3d_helpers_$STAMP.tgz -C ~ $HELP
echo "  archive entries: $(tar tzf ~/backups/corona3d_all_runs_$STAMP.tgz | grep -c 'console.out') run folders with a console.out"
DEST="$ODIR/corona3d_backups"; mkdir -p "$DEST"
cp ~/backups/corona3d_*_$STAMP.tgz "$DEST"/
( cd ~/backups && sha256sum corona3d_*_$STAMP.tgz ) > "$DEST/SHA256_$STAMP.txt"
echo "  checksum check of the copies in OneDrive:"; ( cd "$DEST" && sha256sum -c "SHA256_$STAMP.txt" | sed 's/^/    /' )
echo "  files now in $DEST:"; ls -lh "$DEST" | tail -n +2 | sed 's/^/    /'
echo "  Windows path of that folder: $(wslpath -w "$DEST" 2>/dev/null)"

echo; echo "=================== 4. ARE THE FINISHED RUNS WHAT THEY SHOULD BE?"
cd "$SRC/runs"
echo "  commit, executable, config (expect 2 lines of 10: commit e7e1556, exe 6236607e):"
for d in hco2elfix_*; do echo "$(grep '^commit ' $d/run_info.txt | cut -d' ' -f2) $(grep '^executable_md5' $d/run_info.txt | cut -c16-23) $(grep '^config' $d/run_info.txt)"; done | sort | uniq -c | sed 's/^/    /'
echo "  uncommitted changes at launch (expect nothing):"; for f in hco2elfix_*/code_changes.patch hco2elfix_*/git_status.txt; do [ -s "$f" ] && echo "    NOT EMPTY: $f"; done
echo "  settings identical within each set (expect 10 per set):"
for s in lsa hsa; do echo "    $s"; for d in hco2elfix_${s}_*; do grep -v '^output_dir' $d/corona3d_2020.cfg | md5sum | cut -c1-8; done | sort | uniq -c | sed 's/^/      /'; done
echo "  particles / steps / seed (expect 100000 for all 20, seed none):"; for d in hco2elfix_*; do grep '^particles' $d/run_info.txt; done | sort | uniq -c | sed 's/^/    /'

echo; echo "=================== 5. FIRST LOOK AT THE NUMBERS (no interpretation)"
for s in baseline hco2elfix_lsa hsa_baseline hco2elfix_hsa; do
  grep "^${s}_[0-9]" summary.csv | awk -F, -v s=$s '{n++; x=$8; sum+=x; sq+=x*x} END{m=sum/n; sd=sqrt((sq-n*m*m)/(n-1)); printf "  %-16s n=%d  mean total loss rate %.4e  SD %.2e (%.2f%%)\n", s, n, m, sd, 100*sd/m}'
done
echo "  (baselines should read about 1.3142e25 LSA and 6.8168e24 HSA; a difference only matters if it exceeds the run-to-run scatter, about 0.5 %)"
