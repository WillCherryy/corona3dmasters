# Plan: collision data for N2 and CO (bounding approach)

Status: plan only; nothing run. Decided by the user on 16 Nov 2026 (logbook A64). Interpretation and writing are the user's own.

## 1. The problem
The original model uses the O-H data (Zhang et al. 2009) for all four partners (O, N2, CO, CO2). Bop and Gacesa (2026) provide H-CO2 (and D-CO2) data only. There are no H-N2 or H-CO data in hand (no literature search for them has been done yet). N2 and CO are molecules, O is an atom, CO2 is a linear triatomic molecule; neither O nor CO2 is a validated stand-in for N2 and CO.

## 2. Decision
Do not pick one stand-in. Use the two as BOUNDS, run both, show the spread as an uncertainty, and argue qualitatively (molecular structure of N2, CO, CO2 and atomic behaviour of O, and what this implies for collision behaviour) where the true behaviour is likely to lie. High-level discussion.

## 3. Cases (relative to how CO2 is treated; repeat for each treatment of CO2: elastic-only now, "total" and inelastic later)
| Case | O | N2 and CO | CO2 | Files |
|---|---|---|---|---|
| L: N2/CO atom-like | O-H | O-H (as in the original) | H-CO2 | existing: `N2_Mars_HotH.cfg`, `CO_Mars_HotH.cfg`; main configs `corona3d_2020_HCO2elastic.cfg` (LSA), the HSA equivalent. These are the `hco2elfix_lsa_N` and `hco2elfix_hsa_N` runs (in progress). |
| M: N2/CO molecule-like | O-H | H-CO2 (same data as CO2) | H-CO2 | NEW: `inputs/N2_Mars_HotH_HCO2elastic.cfg` and `inputs/CO_Mars_HotH_HCO2elastic.cfg` (copy of `CO2_Mars_HotH_HCO2elastic.cfg` with `type N2` / `type CO`, own `ref_dens` and own `total_sigma_default` as in the current N2/CO configs; `num_diff_energies 3`); NEW main configs with `bg_part2_config` and `bg_part3_config` pointing to them (LSA and HSA copies of `corona3d_2020_HCO2elastic.cfg`). |
The species masses come from the particle classes (N2 = CO = 28), only cross sections and angle distributions come from the config files, so case M keeps the true N2/CO masses and changes only the data. Caveat: CO2-based angle distributions embed the CO2 reduced mass and potential; using them with N2/CO is an approximation, which is the point of a bound.
A full atom-like reference for the whole set (all four gases O-H) already exists: `baseline_N`, `hsa_baseline_N`.

## 4. Runs
- Labels: `hco2elfix_ncoco2_lsa_N` and `hco2elfix_ncoco2_hsa_N` (N = 1-10), 100,000 particles, seedless, `run_sim2.sh`, fixed code (executable md5 6236607e...), same method as the other sets (four at a time).
- Prerequisites: the four new files committed on the `test` branch (run_sim2.sh refuses untracked configs and a dirty tree); the current batches finished and backed up (do not touch `~/corona3dmasters/src` while they run).
- Add the rows to docs/RUN_SETS.md when launched.

## 5. Analysis (specification to be set by the user)
Candidates: total loss rate per case with run-to-run SD (10 runs), the difference between case L and case M against the run-to-run scatter (about 0.5 %), the same relative to the all-O-H baselines; uncertainty graph(s) showing the bound spread. If the spread is within the scatter the choice does not matter for the result; if larger, quote it as a model uncertainty.

## 6. Facts for the qualitative discussion (to be verified before citing)
- Number-density shares of N2 + CO in the model's own input files (`inputs/Mars/bg_densities_*_Fox2015.csv`): LSA: N2 + CO about 3 % at 100 km, 5 % at 131 km, 10 % at 160 km, 14 % at 179 km, 16.5 % at 201 km, 14.5 % at 221 km, 8.7 % at 251 km; HSA: 4.4 %, 7.6 %, 12.6 %, 17.4 %, 20.2 %, 20.9 %, 17.5 % at 100, 130, 159, 180, 199, 221, 249 km. O dominates above about 200 km (LSA: 51 % at 201 km; 88 % at 251 km). CO2 is 95-96 % at 100 km and falls below 15 % by 220 km (LSA).
- Mass factor for the energy a projectile loses in an elastic collision, f = 4 m1 m2 / (m1 + m2)^2 (maximum fraction of the energy, hard-sphere-like): H-O 0.223, H-N2 and H-CO 0.134, H-CO2 0.0875.
- Rotational constants (from memory, to be checked against a spectroscopic reference such as the NIST Chemistry WebBook before citing): N2 about 1.998 cm-1, CO about 1.931 cm-1, CO2 0.390 cm-1: about 5 times sparser rotational ladder for N2 and CO, so about half as many levels open at 1 eV; N2 homonuclear (even j only), CO2 even j only, CO all j.
- O ground state O(3P) has fine-structure levels (about 19.6 and 28.1 meV) and excited electronic states O(1D) 1.97 eV and O(1S) 4.19 eV (energies from memory, to be checked); no rotation or vibration; in the original model H-O is treated as elastic only.
- Bop and Gacesa data limits: docs/CALCULATIONS_Bop_Gacesa_data.md sections 11, 15, 16.

## 7. Open points
1. Energy range: the H-CO2 tables end at 5 eV, the O-H tables at 10 eV, and hot H from the 7.31 eV channel is born above 5 eV. `Interpolator::linterp` returns the last tabulated value outside the table, so above 5 eV the cross section is held at its 5 eV value and the angle distribution is the 5 eV one (nearest energy). State this in the write-up; it applies to all H-CO2 runs and case M.
2. No literature search for H-N2 and H-CO collision data yet; if suitable data exist they would replace the bounding approach (or add a third case).
3. The bound approach brackets the data uncertainty only; it says nothing about the missing inelastic channels (treated separately: state-resolved inelastic plan).
