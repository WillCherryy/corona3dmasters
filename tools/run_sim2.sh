#!/bin/bash
# usage: ./run_sim2.sh LABEL NPARTS NSTEPS SEED
# Same interface and summary file as run_sim.sh, but every run folder is self-contained and fully recorded:
#  - real copies (not links) of inputs/, Hot_H.cfg, Hot_O.cfg and the chosen main config, made read-only
#  - the model reads ONLY these copies, so the settings stored in the folder are exactly the settings used
#  - commit (short and full), branch, executable checksum, host, git status and the full diff against HEAD
#  - a checksum list of every copied file (settings_md5.txt)
# It refuses to start if tracked files differ from the last commit, or if the chosen config files or
# any file in inputs/ are not tracked by git (set ALLOW_DIRTY=1 to override).
# Optional environment variables: CFGFILE (main config), HOTHFILE (Hot_H config), ALLOW_DIRTY.
set -e
set -o pipefail
LABEL=$1; NP=$2; NS=$3; SEED=$4
SRC=$(cd "$(dirname "$0")" && pwd)
CFG=${CFGFILE:-corona3d_2020.cfg}
HOTH=${HOTHFILE:-Hot_H.cfg}
RUN=$SRC/runs/$LABEL
if [ -e "$RUN" ]; then echo "$RUN already exists; choose a new label"; exit 1; fi
if [ "${ALLOW_DIRTY:-0}" != "1" ]; then
  if ! git -C "$SRC" diff HEAD --quiet; then
    echo "Tracked files differ from the last commit. Commit first (or ALLOW_DIRTY=1):"
    git -C "$SRC" status --short --untracked-files=no
    exit 1
  fi
  for f in "$CFG" "$HOTH" Hot_O.cfg; do
    git -C "$SRC" ls-files --error-unmatch -- "$f" > /dev/null 2>&1 || { echo "$f is not tracked by git: add and commit it first (or ALLOW_DIRTY=1)"; exit 1; }
  done
  UNTRACKED=$(git -C "$SRC" status --porcelain --untracked-files=all -- inputs)
  if [ -n "$UNTRACKED" ]; then echo "Untracked files in inputs/ (add and commit them first, or ALLOW_DIRTY=1):"; echo "$UNTRACKED"; exit 1; fi
fi
mkdir -p "$RUN/output"
cd "$RUN"
sed -e "s/^num_testparts[[:space:]].*/num_testparts   $NP/" \
    -e "s/^timesteps[[:space:]].*/timesteps       $NS/" \
    "$SRC/$CFG" > corona3d_2020.cfg
cp "$SRC/$CFG" "config_source_$CFG"
cp -r "$SRC/inputs" inputs
cp "$SRC/$HOTH" Hot_H.cfg
cp "$SRC/Hot_O.cfg" Hot_O.cfg
if [ "$SEED" != "none" ]; then echo "$SEED" > rng_seed; fi
COMMIT=$(git -C "$SRC" rev-parse --short HEAD)
{ date; echo "commit $COMMIT"; echo "particles $NP steps $NS seed $SEED"; } > run_info.txt
echo "config $CFG hoth $HOTH" >> run_info.txt
echo "commit_full $(git -C "$SRC" rev-parse HEAD)" >> run_info.txt
echo "branch $(git -C "$SRC" rev-parse --abbrev-ref HEAD)" >> run_info.txt
echo "executable_md5 $(md5sum "$SRC/corona3d_2020" | cut -d' ' -f1)" >> run_info.txt
echo "host $(hostname) $(uname -sr)" >> run_info.txt
git -C "$SRC" diff HEAD > code_changes.patch
git -C "$SRC" status --porcelain --untracked-files=no > git_status.txt
find . -type f \( -name '*.cfg' -o -path './inputs/*' \) | sort | xargs md5sum > settings_md5.txt
find inputs -type f -exec chmod a-w {} +
chmod a-w corona3d_2020.cfg Hot_H.cfg Hot_O.cfg "config_source_$CFG"
"$SRC/corona3d_2020" | tee console.out
get() { grep "$1" console.out | tail -1 | awk '{print $NF}'; }
SUM=$SRC/runs/summary.csv
[ -f "$SUM" ] || echo "label,seed,nparts,nsteps,day_escaped,night_escaped,global_rate,total_loss_rate,commit" > "$SUM"
echo "$LABEL,$SEED,$NP,$NS,$(get 'Number of day side escaped'),$(get 'Number of night side escaped'),$(get 'Global production rate'),$(get 'Total loss rate'),$COMMIT" >> "$SUM"
echo "Saved to $RUN"
