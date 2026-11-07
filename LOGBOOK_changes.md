# corona3d_2020 project logbook: changes made and planned

Format per entry: WHAT changed, WHY, GOAL, HOW CHECKED, STATUS. "Physics" = whether the model's results can change.
Dates marked (approx.) were not recorded at the time; fill in from your own notes.

## A. Changes already made

### A1. Build environment (Windows, WSL2 Ubuntu)
- WHAT: installed build-essential, git, libeigen3-dev; added symlink `Vtally.hpp` (Linux is case-sensitive, the source file is `VTally`-style); added symlink `/opt/local/include/eigen3 -> /usr/include/eigen3` so the existing include path finds Eigen (no source edit).
- WHY: the code was written for macOS-style paths. GOAL: compile and run unchanged source.
- PHYSICS: none. CHECKED: model builds; baseline loss rate about 1.3e25 s^-1, consistent with Gregory et al. (2023).

### A2. The single code error: `vel_infile` typo (commit da5756b on `cpp`)
- WHAT: parameter-check typo for `vel_infile` in `main.cpp` corrected.
- WHY: the check used a misspelled name. GOAL: remove the one known error. PHYSICS: none for normal runs.

### A3. Run and logging scripts (`run_sim.sh`, `run_batch.sh`, `status.sh`, `analyse.py`, `timeseries.py`, `plot_xsec.py`, `verify_runs.py`)
- WHAT: scripts in `src/` (untracked, excluded via `.git/info/exclude`). Each run gets its own folder `runs/<label>/` containing a copy of `corona3d_2020.cfg`, symlinks to `Hot_H.cfg` and `Hot_O.cfg`, `run_info.txt` (date, commit, particles, steps, seed), the model output, and one row in the summary CSV.
- WHY: reproducible, loggable runs. GOAL: every result traceable to its settings. PHYSICS: none (scripts only call the unchanged executable).

### A4. Seed handling in `run_sim.sh`
- WHAT: seed argument `none` leaves the model clock-seeded; a number is written to `rng_seed` in the run folder.
- WHY: supervisor advised no seeds for production runs; seed 123 is available for reproducibility tests. GOAL: seeded and seedless runs clearly labelled (`seed` column and `run_info.txt`).
- PHYSICS: none. NOTE: the seed of a seedless run cannot be recovered.

### A5. Baseline set `baseline_1` to `baseline_10`
- SETTINGS: low solar activity (LSA), 100,000 particles, step cap 90,000,000, seedless, HCO+ dissociative recombination source, original O-H based cross sections for all gases.
- CHECKED (4 Nov 2026): `grep` of every run folder's `corona3d_2020.cfg` shows `MarsTempLSA_Fox2015` and `bg_densities_LSA_Fox2015` for all ten.

### A6. Accidental HSA edit of `corona3d_2020.cfg` (reverted 4 Nov 2026)
- WHAT: a few days earlier, the tracked file `src/corona3d_2020.cfg` was edited to HSA for temperature and neutral densities (not `Hot_H.cfg`). This was not intended as the baseline.
- IMPACT: baselines 1 to 10 all ran before the edit (verified in A5). `corona3d_2020_elastic.cfg` had been copied from the edited file and was rebuilt.
- FIX: `git restore corona3d_2020.cfg` (run from `src/`; the first attempt failed because it was run from the wrong directory). Verified: `grep` shows LSA again; `git status` clean for that file.
- LESSON: never edit the original configs; make `_<name>` copies.

### A7. H-CO2 collision data, my branch `claude/exciting-keller-mu4f4t` (NOT merged into `cpp`; sensitivity use only)
- WHAT: new files only: total (summed over j' = 0..52) cross-section and angle tables for H + CO2 from Bop and Gacesa (2026), an elastic-only subfolder, README, four configs. No existing file modified.
- WHY: replace the O-H stand-in for CO2. STATUS: not used in any run so far.

### A8. H-CO2 elastic-only data, user's branch `test`
- WHAT (user): added `total_cross_section_H_CO2_elastic.csv` and `diff_cross_sections_H_CO2_{0.1,1,5}ev.csv` (identical in value to the elastic-only files in A7).
- WHY: treat only elastic collisions, consistent with Zhang et al. (2009) for O-H, N2, CO. CAVEAT TO STATE IN THE THESIS: for a molecule, elastic-only omits rotationally inelastic collisions (about half the collisions and almost all the momentum transfer, so the escape rate is expected to be much higher than with the total data); it is an approximation.
- WHAT (4 Nov 2026): put `#` at the start of line 1 of each of the four files (the loader skips only lines starting with `#`; the originals' header lines would have crashed `stod`); created `src/inputs/CO2_Mars_HotH_elastic.cfg` (changes: `total_sigma_file`, `num_diff_energies` 4 to 3, `energy4`/`energy4_file` removed, three angle paths) and `src/corona3d_2020_elastic.cfg` (changes: `bg_part4_config` only).
- CHECKED: `diff` against the originals shows only those lines. STATUS: staged, not yet committed; not yet run.

### A9. High solar activity (HSA) setup (4 Nov 2026)
Created copies; no original file changed.
1. `src/corona3d_2020_HSA.cfg`: copy of `corona3d_2020.cfg` with
   - `temp_profile` MarsTempLSA_Fox2015.csv -> MarsTempHSA_Fox2015.csv
   - `neutral_densities` bg_densities_LSA_Fox2015.csv -> bg_densities_HSA_Fox2015.csv
2. `src/Hot_H_HSA.cfg`: copy of `Hot_H.cfg` with the five active "Mars config 1" lines switched LSA -> HSA (identical to the file's own commented "Mars config 2" block): temperature, H, H+ (eroded), HCO+ (eroded), electron (eroded) profiles.
3. `run_sim.sh` (backup `run_sim.sh.bak2`): three edits so two optional environment variables select the configs; default behaviour is unchanged.
   - line 12: `"$SRC/${CFGFILE:-corona3d_2020.cfg}"`
   - line 14: `ln -s "$SRC/${HOTHFILE:-Hot_H.cfg}" Hot_H.cfg`
   - added line 19: `echo "config ${CFGFILE:-corona3d_2020.cfg} hoth ${HOTHFILE:-Hot_H.cfg}" >> run_info.txt`
- WHY: the executable reads `corona3d_2020.cfg` and `Hot_H.cfg` by fixed names from the run folder, and HSA needs both changed together (an HSA atmosphere with LSA hydrogen/ion profiles would be an inconsistent mix).
- GOAL: ten HSA baselines directly comparable with the ten LSA baselines.
- CHECKED: (i) search of every active config line for solar-dependent data: only these seven files; the C++ code has no hard-coded LSA/HSA paths; cross-section files and rate coefficients are not solar dependent; (ii) `diff` shows 2 changed lines (main cfg) and 5 (Hot_H); (iii) smoke run `hsa_smoke` (1,000 particles, commit dc2dc61): `run_info.txt` shows `config corona3d_2020_HSA.cfg hoth Hot_H_HSA.cfg`; the run folder's configs show HSA temperature, neutral densities and H profile.
- KNOWN MINOR POINT: HSA profiles begin at 80.4-80.7 km, slightly above the 80 km model bottom; the interpolator holds the lowest tabulated value below the range (no zero or crash); particles are removed at 80 km anyway. Mention in methods.
- PHYSICS: only the atmosphere changes; model code unchanged.

### A10. HSA baselines `hsa_baseline_1` to `_10` (completed 6 Nov 2026)
- SETTINGS: HSA via `corona3d_2020_HSA.cfg` and `Hot_H_HSA.cfg`, 100,000 particles, step cap 90,000,000, seedless, original O-H cross sections, commit `bae680c` on branch `test`.
- HISTORY: first launch on 5 Nov was interrupted at 13:58 when Ubuntu (WSL) went down (restart at 16:02); no results saved, partial folders kept as `runs/interrupted_hsa_1/2`; relaunched as two batches of two (runs 1-5 and 6-10); measured memory about 60 MB per run.
- STATUS: all ten finished; verification (`verify_runs.py hsa_baseline`) and analysis (`analyse.py hsa_baseline`) outputs to be recorded here.

### A11. Combined HSA + H-CO2 elastic config (6 Nov 2026)
- WHAT: `src/corona3d_2020_HSA_elastic.cfg` = copy of `corona3d_2020_HSA.cfg` with `bg_part4_config` changed to `./inputs/CO2_Mars_HotH_elastic.cfg`. Checked by `diff` against the HSA config (one line) and against `corona3d_2020_elastic.cfg` (two HSA lines). Committed on `test` as `4e20248`; push to GitHub still pending.
- WHY: H-CO2 elastic runs are needed at both solar activities. No C++ file differs between `cpp` and `test` on GitHub (checked 6 Nov 2026), so all runs use the same executable behaviour; only data files and configs differ.

### A12. H-CO2 elastic smoke tests (6 Nov 2026, in progress)
- `smoke_hco2el_lsa` and `smoke_hco2el_hsa`, 1,000 particles each; checks: runs complete, `bg_part4_config` correct in each run folder, escape fraction higher than the O-H baseline (expected, elastic-only), no file-not-found messages.
- Production sets after the smoke tests: `hco2el_lsa_1..10` and `hco2el_hsa_1..10`, 100,000 particles, seedless, launched from an open Ubuntu window (not through a one-line `wsl bash -c`, which can end background jobs).

### A13. What the H-CO2 data files contain (checked 6 Nov 2026 on the 5 eV file, `E5.00-DCS.txt`)
- Each source file holds 27 blocks of 1,800 rows (angle 0.1 to 180 degrees, differential cross section in Angstrom^2 per steradian). The header line of each block gives the initial and final CO2 rotational state: `LEV(I),J(I)` = 1, 0 (CO2 starts in j = 0 in every block) and `LEV(F),J(F)` = the final state.
- Block 1 (`LEV(F),J(F) = 1 0`, final j' = 0): ELASTIC. CO2 stays in its starting rotational state; no energy goes into rotation.
- Blocks 2 to 27 (final j' = 2, 4, ..., 52): ROTATIONALLY INELASTIC. The H atom spins CO2 up and loses energy; only even j' occur (symmetry of CO2). These are generally deflected through larger angles.
- User's `test` branch files = block 1 only, converted Angstrom^2 -> cm^2 (x 1e-16). Verified row by row against the source: 1,800 rows, identical angles, maximum relative difference 2e-16.
- Integrated cross sections at 5 eV: elastic (j' = 0) 2.21e-15 cm^2; j' = 2: 5.3e-16; j' = 10: 1.2e-16; j' = 20: 7.8e-17; j' = 52: 1.5e-17; sum over all 27 blocks 4.58e-15. Elastic is therefore about 48% of all collisions at 5 eV.
- Angular character (own trapezoid integration of the tables; mean of 1 - cos(theta), proportional to momentum transfer): O-H (Zhang) 0.33 at 1 eV and 0.20 at 5 eV; H-CO2 elastic only 0.011 and 0.006; H-CO2 total (all blocks) 0.23 and 0.09. The elastic-only scattering is almost entirely straight-ahead, so energy lost per collision with CO2 falls from about 1.5% (O-H angles with CO2 mass) to under 0.1% at 1 eV.
- DECISION (user, 6 Nov 2026): run elastic-only H-CO2 now, because the existing O-H, N2 and CO data are also elastic (Zhang et al. 2009). Integrating the inelastic channels (sum over blocks, the "total" variant, files already available on branch `claude/exciting-keller-mu4f4t`) is a planned next step after the other results are verified. In the thesis, describe the result as the elastic-channel approximation and give the 48% figure; note that the elastic-only escape rate is expected to be an upper bound for CO2.

### A14. H-CO2 elastic smoke results (6 Nov 2026, commit 4e20248, 1,000 particles each, seedless)
- LSA: 586 escaped (58.6%), loss rate 3.62e25 s^-1, global 1.235e26 s^-1 (O-H baseline: 21.4%, 1.32e25). HSA: 301 escaped (30.1%), loss rate 1.55e25 s^-1, global 1.027e26 s^-1 (O-H baseline about 13%, about 6.8e24). Loss-rate identity holds in both. Config lines verified in the run folders (elastic CO2 file; LSA / HSA temperature).
- Escape rate rises by about 2.7 (LSA) and 2.3 (HSA) relative to the O-H baselines; counting noise about +/-4% and +/-6%. Explained by the forward-peaked elastic scattering above; O, N2 and CO still use O-H data in both baseline and H-CO2 runs.

### A15. What each run records, and the gaps (assessed 6 Nov 2026, while the `hco2el_*` sets run)
- IN each `runs/<label>/` folder: `console.out` (live status and final tallies), `output/` (model output files, e.g. the escape energy distributions, densities, vtally), `run_info.txt` (date, commit, particles, steps, seed, config file names), a real copy of `corona3d_2020.cfg`, symlinks `Hot_H.cfg` and `Hot_O.cfg`, `rng_seed` for seeded runs; plus one row in `runs/summary.csv`.
- NOT stored per run (gaps): (1) the CO2/O/N2/CO species configs and the data files are read by path from the live `src/inputs/`, and `Hot_H.cfg` is a symlink to the live file, so they are only recoverable from the recorded git commit and only if the working tree was clean (check `git status` before each batch; never edit a file in place after runs have used it); (2) `run_sim.sh` and the analysis scripts are untracked and not under version control; (3) the compiled executable is not recorded (the source is identical across `cpp` and `test`, no .cpp/.hpp differs); (4) the commit hashes `bae680c` and `4e20248` exist only in the local clone until the push to GitHub succeeds (token setup pending).
- PLANNED FIXES (after the current batches finish; do not edit the live files mid-batch): commit the scripts into the repo (e.g. a `tools/` folder on `test`); make `run_sim.sh` also write `git status --porcelain` and an md5 checksum of the executable and of each config used into `run_info.txt`, and copy `Hot_H.cfg` into the run folder instead of linking it; push all commits to GitHub.
- The run folders, summary CSV and outputs are plain text, so Python analysis and plotting work from them directly (existing `analyse.py`, `timeseries.py`, `verify_runs.py`).

### A16. Code and executable verification (6 Nov 2026)
- SOURCE vs ORIGINAL: `origin/cpp` = the authors' code (last upstream commit `9a49879`, B. Gregory, Sept 2023) plus ONE commit of ours, `da5756b` (17 Oct 2026): `main.cpp`, `"vel_infle"` -> `"vel_infile"`. `git diff 9a49879 origin/cpp` shows only that line. `test` differs from `cpp` only by added H-CO2 data files (no .cpp/.hpp/makefile change).
- EXECUTABLE: `src/corona3d_2020` built 17 Oct 2026 16:27 +0100 (about 3 h after the fix commit), before all runs (first baseline 24 Oct); not rebuilt since. One executable produced every run.
- `Particle.hpp` HISTORY: edited early to repoint the Eigen include path; that edit was lost on 21 Oct by `git reset --hard origin/cpp` (file time stamp 21 Oct 21:48, after the build); the Eigen problem was then solved with a symlink `/opt/local/include/eigen3 -> /usr/include/eigen3` (no source edit). The committed `Particle.hpp` is the authors' original.
- RUN-TIME SOURCE STATE: every run folder has `code_changes.patch` written by `git -C "$SRC" diff` (line 20 of `run_sim.sh`). All are 0 bytes for baselines 1-10, `hsa_baseline_1` and `hco2el_lsa_1` (others to be checked): no tracked file (code, config or data) had unstaged changes when the run started. Blind spots: staged-but-uncommitted changes and untracked files (planned fix: `git diff HEAD` plus `git status --porcelain`).
- BUILD EQUIVALENCE TEST: copies `~/check_old` (the 17 Oct executable) and `~/check_new` (rebuilt from the current source), identical `src` otherwise, each made a throwaway git repo (the script needs `git rev-parse`; without it `set -e` aborted the first attempt before the model started, so the first "IDENTICAL" was two empty folders and was discarded). Test: 1,000 particles, seed 123, LSA, original O-H data. RESULT: both give 201 day and 36 night escapes, global rate 1.2352e26, loss rate 1.46371e25; `diff -rq` of the whole `output/` folders (EDF and other files) prints IDENTICAL. The executables differ in 21,712 bytes (7.7%), but the behaviour is bit-identical, so the 17 Oct program matches a fresh build of today's source.
- CONCLUSION: the model used for all runs is the authors' code with the one typo fix; no unrecorded code difference remains.

### A17. Backup of run data (6-7 Nov 2026)
- `runs/` (about 442 MB at the time) mirrored to the personal OneDrive folder `/mnt/c/Users/will/OneDrive/corona3d_backups/runs/` by `~/sync_runs.sh`, an hourly `rsync -rt --no-links` loop started with `nohup` from an Ubuntu window (stops if Ubuntu restarts; restart with the same `nohup` line; check with `pgrep -f sync_runs.sh` and `~/sync_last.txt`).
- Symbolic links in run folders (`Hot_H.cfg`, `Hot_O.cfg`, `inputs`) are skipped on purpose (OneDrive cannot store them); the config used by each run is named in its `run_info.txt`, and the actual files are in the snapshot archive `~/snapshots` and in git.
- Copies of runs still in progress are partial until the run finishes; later hourly passes update them. The backup never deletes files.
- Dated `.tgz` archives per milestone are an additional option (see `~/backups`).

### A18. Settings reconstruction in finished run folders (7 Nov 2026)
- WHY: `Hot_H.cfg` and `Hot_O.cfg` in each run folder are symlinks to the live files in `src` (`ln -s` in `run_sim.sh`), so a run folder does not itself contain the `Hot_H.cfg` it used. (`Hot_O.cfg` is never read in a hot-H run: `dist_type Hot_H` makes `main.cpp` construct only `Distribution_Hot_H`, which opens `Hot_H.cfg`.) The model needs the exact file name `Hot_H.cfg`, so an HSA run's link is named `Hot_H.cfg` but points to `Hot_H_HSA.cfg`; the variant name is recorded in `run_info.txt` (`hoth Hot_H_HSA.cfg`) and by the link target.
- CHECK (7 Nov 2026): `grep "^temp_prof_filename" runs/*/Hot_H.cfg` shows LSA for all `baseline_N` and `hco2el_lsa_N` and HSA for all `hsa_baseline_N` and `hco2el_hsa_N` (24 folders at that time). A whole-file checksum comparison (expect exactly two distinct `Hot_H.cfg` fingerprints, equal to those of `Hot_H.cfg` and `Hot_H_HSA.cfg`) is to be recorded here.
- ACTION: for `baseline_1..10` and `hsa_baseline_1..10`, copied the link target to `reconstructed_Hot_H.cfg`, the four species configs named in `corona3d_2020.cfg` to `reconstructed_<name>.cfg`, and wrote `reconstructed_settings_note.txt` (source: live files in `src`, unchanged per git history and empty `code_changes.patch`). Also saved a collection in `~/run_configs/` (per-run `corona3d_2020.cfg` and `Hot_H.cfg`, `manifest.txt`, `checksums.txt`). The `hco2el_*` runs get the same treatment after they finish.
- PLANNED (after the `hco2el` batches finish, B6b): `run_sim.sh` copies `Hot_H.cfg`, `Hot_O.cfg` and the species configs into each run folder at launch instead of linking, and writes checksums of the executable and all configs plus `git status --porcelain` into `run_info.txt`.

### A19. Tools and deuterium design saved in the repository (7 Nov 2026, branch `claude/exciting-keller-mu4f4t`)
- `tools/check_runs.sh` (read-only status: processes, progress, stalled-run flag, finished counts per set, batch logs, backup loop), `tools/after_finish.sh` (run once after all `hco2el` runs finish: reconstruct settings, fingerprints, empty-patch check, dated archive), `tools/resume_missing.sh lsa|hsa` (only after an interruption: relaunch just the missing run numbers). `bash -n` syntax-checked; not yet run on the user's machine.
- `docs/DEUTERIUM_PLAN.md`: design for adding D (new `Particle_D`, `Distribution_Hot_D`, `D` branches in `main.cpp` and `Background_Species.cpp`, makefile, configs; D/H and cross-section inputs to decide; regression test V1 with D mass set to H mass must reproduce the seeded H run bit for bit; work in a separate copy/branch, never rebuild in `src` while runs are active).
- CORRECTION to A18 wording: the HCO+ DR rate coefficient (2.0e-7) is a constant in `Hot_H.cfg`, but `Distribution_Hot_H.cpp` multiplies it by (Te/300)^-1.25 using the electron temperature from the temperature profile, so the DR rate depends on solar activity through the profile files (already switched to HSA); no extra setting needed.

## B. Planned changes (in order; update status as done)

| # | Step | Reason / goal | Status |
|---|---|---|---|
| B1 | Commit the new config files (`_HSA`, `_elastic`, data header fixes) on `test` and push | the commit hash in `run_info.txt` should identify the exact settings used | committed locally 4 Nov 2026 as `bae680c` (8 files); push failed (GitHub needs a personal access token, not a password), push pending |
| B2 | Review `hsa_smoke` loss rate (same order as LSA ~1.3e25 s^-1) | sanity check before long runs | done 4 Nov 2026: smoke run 131/1000 escaped (13.1%, about +/-9% counting error), loss 6.72e24 s^-1, global 1.027e26 s^-1; LSA baseline_10: 21.4% escaped, loss 1.319e25, global 1.235e26; loss-rate identity holds in both; HSA lower escape is plausible (denser/hotter thermosphere), not yet checked against literature |
| B3 | 10 x `hsa_baseline_N`, seedless, 100,000 particles | HSA reference set | first launch interrupted 5 Nov 2026: runs 1 and 2 stopped at 13:58 with about 4,300 of 100,000 particles still active (about 95% through); WSL had restarted at 16:02; no results saved (the model has no checkpoints); partial folders to be moved to `runs/interrupted_hsa_*`; relaunch pending after power/sleep settings are rechecked |
| B4 | H-CO2 (elastic-only, Zhang-consistent) at LSA: 10 runs, labelled `hco2el_lsa_N`, via `CFGFILE=corona3d_2020_elastic.cfg` | effect of the new CO2 data at low solar activity | launched 6 Nov 2026 (commit 4e20248), user's decision to run elastic-only first |
| B5 | H-CO2 elastic-only at HSA: 10 runs, `hco2el_hsa_N`, via `corona3d_2020_HSA_elastic.cfg` and `Hot_H_HSA.cfg` (created and checked by `diff`, A11) | effect at high solar activity | launched 6 Nov 2026 together with B4 |
| B6 | H-CO2 total (summed over j', inelastic channels included) at LSA and HSA | next step after verification of the other results (user, 6 Nov 2026); shows the size of the elastic-only approximation | planned |
| B6b | Reproducibility upgrades to `run_sim.sh` and version-controlling the scripts (see A15) | every run fully reconstructable from its folder plus git | planned, after the current batches |
| B6c | Push local commits (`bae680c`, `4e20248`, later ones) to GitHub `test` | the commits named in `run_info.txt` become traceable online | pending (token) |
| B7 | D as a particle type: mass 2, production from the parent ion, escape energy 0.26 eV at 100 km; code changes designed together before editing | start of deuterium work | not started |
| B8 | D baselines at LSA and HSA (10 runs each). First pass: all four partners use H data as proxies (labelled `dproxy_*`), then replace partner by partner | attributable changes | not started |
| B9 | D-O, D-N2, D-CO data (Zhang-style) and D-CO2 data (Bop and Gacesa give H + CO2 only; needs separate data or a stated approximation) | new cross sections | not started, D-CO2 open question |
| B10 | Self-collisions not in the model now: H-H and H-D (test H or D atoms colliding with background H/D, i.e. hydrogen-hydrogen elastic scattering). Code check (6 Nov 2026): `Background_Species::set_particle_type` already accepts type `H`, and `corona3d_2020.cfg` lists H as a possible background species, but there is no `H_Mars_HotH.cfg`, no H-H cross-section data, and the neutral-density CSV has no H column (column order must match the species order). A D background species would need a new particle class (`Particle_D`) and a type `D` in `main.cpp` and `Background_Species.cpp`. | completeness of the exobase collision physics for the H and D isotopes | not started; needs data (H-H, H-D cross sections), a species config, and a density column; decide scientific importance first |
| B11 | Inelastic H-CO2 channels (sum over final states j', the "total" variant) at LSA and HSA, then compare with the elastic-only results | quantify the elastic-only approximation; follows verification of the elastic results and the baselines | planned after B4-B5 are analysed |

### Comparison with Gregory et al. (2023) (to complete by user from the paper)
- Our HCO+ DR loss rates: LSA baseline_10 1.32e25 s^-1 (about 9.1e6 cm^-2 s^-1 over 4 pi R^2 with R = 3.39e8 cm); HSA about 6.8e24 s^-1 (about 4.7e6 cm^-2 s^-1) from the first finished runs (5 Nov 2026, not yet the full set).
- Web summary of the paper: total nonthermal escape is 39% (LSA) and 27% (HSA) of thermal escape, HCO+ DR 30-50% of nonthermal; thermal flux 8.7e7 to 1.1e8 cm^-2 s^-1. These are ratios to thermal, so they are not directly the quantity above. Compare against the paper's own HCO+ DR escape flux for LSA and HSA (table/figure), then record the numbers here.
- Escape probability tables for both cases are in `src/model_output_data/escape_probabilities_{LSA,HSA}.csv` (probability against altitude for five energies) and can be compared with our own HSA results.

## C. Housekeeping
- Stray untracked files `src/hot_h.cfg`, `src/hot_o.cfg`, `src/hot_o.cfg.save` (lowercase, probably created by accident): inspect with `ls -l`, do not commit.
- Keep `smoke`/test runs out of analyses (different label prefix).
