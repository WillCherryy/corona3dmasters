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

## B. Planned changes (in order; update status as done)

| # | Step | Reason / goal | Status |
|---|---|---|---|
| B1 | Commit the new config files (`_HSA`, `_elastic`, data header fixes) on `test` and push | the commit hash in `run_info.txt` should identify the exact settings used | committed locally 4 Nov 2026 as `bae680c` (8 files); push failed (GitHub needs a personal access token, not a password), push pending |
| B2 | Review `hsa_smoke` loss rate (same order as LSA ~1.3e25 s^-1) | sanity check before long runs | done 4 Nov 2026: smoke run 131/1000 escaped (13.1%, about +/-9% counting error), loss 6.72e24 s^-1, global 1.027e26 s^-1; LSA baseline_10: 21.4% escaped, loss 1.319e25, global 1.235e26; loss-rate identity holds in both; HSA lower escape is plausible (denser/hotter thermosphere), not yet checked against literature |
| B3 | 10 x `hsa_baseline_N`, seedless, 100,000 particles | HSA reference set | pending |
| B4 | H-CO2 elastic at LSA (10 runs) and HSA (10 runs), via `CFGFILE=corona3d_2020_elastic.cfg` (HSA needs a combined HSA + elastic cfg, to be created and diffed first) | effect of the new CO2 data | pending |
| B5 | Optional: H-CO2 total (summed) variant as a sensitivity | shows size of the elastic-only approximation | pending, user decision |
| B6 | D as a particle type: mass 2, production from the parent ion, escape energy 0.26 eV at 100 km | needs C++ changes (design together first) | not started |
| B7 | D-O, D-N2, D-CO data (Zhang-style) | new cross sections | not started |
| B8 | D-CO2 data | Bop and Gacesa give H + CO2 only; D-CO2 needs its own data or a stated approximation | not started, open question |

## C. Housekeeping
- Stray untracked files `src/hot_h.cfg`, `src/hot_o.cfg`, `src/hot_o.cfg.save` (lowercase, probably created by accident): inspect with `ls -l`, do not commit.
- Keep `smoke`/test runs out of analyses (different label prefix).
