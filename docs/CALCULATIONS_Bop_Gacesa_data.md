# Calculations performed on the Bop and Gacesa (2026) H + CO2 and D + CO2 data

Record of every calculation made on these data, with the formulas, the inputs and the checks. All of it is done by `tools/plot_h_co2_figures.py` (functions named below); nothing else touches the data. Status of each number: DIRECT (read from the files, units converted), CALCULATED (an integral or sum of file values, no assumption), ESTIMATED (needs an assumption; stated). Last updated 16 Nov 2026 (logbook A53-A58).

## 0. Data and verification
- Source: C. T. Bop and M. Gacesa (2026), MNRAS 552, 1-8, doi:10.1093/mnras/stag1696; data Zenodo doi:10.5281/zenodo.17549249 (CC BY 4.0), file Archive.zip, md5 `e1ebc4637a175a5bd142a6512697e551`.
- Files used per system S = H or D (initial CO2 level j = 0 only):
  - `S-CO2_total_and_elastic_CS.out`: 149 energies, 8.07 to 40,328 cm-1 (0.001 to 5 eV); columns energy (cm-1), j, total and elastic cross section (Angstrom^2).
  - `E0.10-DCS.txt`, `E1.00-DCS.txt`, `E5.00-DCS.txt`: 27 blocks of 1,800 rows (angle 0.1 to 180 degrees in steps of 0.1; DCS in Angstrom^2 per sr), one block per final level j' = 0, 2, ..., 52; block j' = 0 is the elastic channel.
  - `S-CO2_state-to-state_CS.res`: cross section into every final level (columns energy cm-1, jf, ji, Angstrom^2; j' = 2 x jf), up to j' = 140 at 5 eV.
- Verification (done in the cloud and on the user's PC): every file used is byte-identical (MD5) to the original in Archive.zip. DCS files sit inside `Archive/S-CO2/S-CO2_DCS.zip`. MD5s are in `data/raw/Bop_Gacesa_2026/*/MD5SUMS.txt`.

## 1. Conversions (read_blocks, read_state_to_state, load_all)
- Angstrom^2 -> cm^2: x 1e-16. Energy cm-1 -> eV: / 8065.541.
- The three energies 0.1, 1, 5 eV are grid points of the tables (806.5541, 8065.541, 40327.705 cm-1). State-to-state rows are matched to them within 0.02 cm-1, and only rows with ji = 0 are used.
- Level j' = 2 x jf.

## 2. Cross sections against energy (panel "Cross sections against energy"; DIRECT)
Total and elastic columns of the table; inelastic = total - elastic. Energies 0.001 to 5 eV.

## 3. Elastic share of collisions ("How often"; DIRECT)
share_el = sigma_el / sigma_tot from the table (values at 0.1, 1, 5 eV are table rows, interpolation not needed). This uses every final level because the authors' total includes all of them. Check: the sum of the state-to-state cross sections over every level equals the table total (ratio 1.00000 for H and D at all three energies).

## 4. Cross section by final level (DIRECT)
sigma_j' straight from the state-to-state file (ji = 0), all levels (23 / 57 / 71 levels for H at 0.1 / 1 / 5 eV; 23 / 61 / 71 for D). Bar heights in cm^2. The label "elastic x %" = sigma_0 / (sum of all levels); "j' = 2: y %" likewise.

## 5. Angle integrals (integrate; CALCULATED)
For each level block, sigma = 2 pi integral DCS(theta) sin(theta) dtheta over 0 to 180 degrees:
- trapezoid rule on the 1,800 tabulated points (0.1 to 180 degrees);
- the strip 0 to 0.1 degrees: DCS fitted as a + b theta^2 by least squares to the first 5 points, integrated with 2,001 trapezoids.
Check against the authors' state-to-state values, max relative deviation over levels with sigma > 1e-4 x elastic: H 0.01 / 0.06 / 0.24 %, D 0.03 / 0.14 / 0.54 % (0.1 / 1 / 5 eV).

## 6. Momentum transfer (CALCULATED where all levels are in the angle files; otherwise ESTIMATED)
- Per level: sigma_mt,j' = 2 pi integral DCS sin(theta) (1 - cos theta) dtheta (same integration as section 5). Mean (1 - cos theta) per level: m1(j') = sigma_mt,j' / sigma_j' (using the angle integral of sigma_j').
- Total over levels present in the angle files (j' <= 52): MT52 = sum of sigma_mt,j'. Elastic share of momentum transfer = sigma_mt,0 / MT_total.
- Levels above j' = 52 (missing: H 5 eV 2.82 % of collisions; D 1 eV 1.47 %, D 5 eV 6.49 %; H at 0.1 eV and D at 0.1 eV none; H at 1 eV 0.0027 %, below the 0.1 % threshold at which the script starts estimating, so treated as none): their cross section is known from the state-to-state file (missing = sum over j' > 52 of sigma_j'), but their angles are not. Their momentum transfer is MISSING x c, where c is the mean (1 - cos theta) of those levels:
  - central ESTIMATE: c = mean of m1 of the five highest levels present (H 5 eV 0.509; D 1 eV 1.356; D 5 eV 0.329);
  - HARD BOUNDS (no assumption): c between 0 and 2, because 0 <= 1 - cos theta <= 2.
- Finding (A57): m1 rises with j' (H 5 eV: 0.006 at j' = 0, 0.12 at 12, 0.32 at 24, 0.51 at 48, 0.59 at 52), so the flat estimate is probably low; alternative extrapolations gave c = 0.84 (H 5 eV linear), 0.59 (D 5 eV linear), 1.0 (isotropic-like). Elastic share of momentum transfer is 1.9-3.1 % (H 5 eV), 1.75-2.0 % (D 1 eV), 1.3-3.8 % (D 5 eV) for ANY c.
- Integration cross-check: the momentum-transfer integral of selected 5 eV levels (j' = 0, 2, 20, 52) agrees between trapezoid and Simpson to better than 3e-6.

## 7. Cumulative shares and j90 (panel "Cumulative share")
Cumulative sums over j' of sigma_j' (collisions; state-to-state, all levels) and of sigma_mt,j' (angle files, j' <= 52) divided by the total. j90 is the first level at which the cumulative momentum transfer reaches 90 %. Where levels are missing, the dashed continuation above j' = 52 uses c = c_mid (ESTIMATE) times the state-to-state cross sections, and the total includes MISSING x c_mid; j90 is then "> 52" for H 5 eV and D 5 eV (D 1 eV reaches 90 % at j' = 52).

## 8. Rotational energy per collision (CALCULATED, rigid rotor)
E_rot(j') = B j'(j'+1), B = 0.39022 cm-1 (CO2 ground-state rotational constant, approximate; centrifugal distortion neglected, about 0.7 % at j' = 140). Initial level j = 0 so the energy gained equals E_rot(j'). Mean per collision = sum sigma_j' E_rot(j') / sum sigma_j' over EVERY level from the state-to-state file (H 1.06 / 7.90 / 17.86 meV; D 1.49 / 13.59 / 30.37 meV at 0.1 / 1 / 5 eV).

## 9. Recoil energy per collision (ESTIMATED approximation)
For elastic scattering of a mass m1 on a stationary mass m2 = 44.0095 amu, the projectile loses (f/2)(1 - cos theta_cm) E_lab with f = 4 m1 m2 / (m1 + m2)^2 (H, m1 = 1.00794: f = 0.08755; D, m1 = 2.01410178: f = 0.16739) and E_lab = E (m1 + m2) / m2 (E is the centre-of-mass energy: stated in the paper, section 3.1). The mean over collisions = (f/2) E_lab x MT_total / (sum of sigma_j'). This applies elastic kinematics to inelastic events, so it is an approximation. The figure bar uses c_mid; the whisker uses c = 0 (floor) and c = 2 (maximum).

## 10. Results (own calculation; E in eV)
| quantity | H 0.1 | H 1 | H 5 | D 0.1 | D 1 | D 5 |
|---|---|---|---|---|---|---|
| sigma_el (cm^2) | 5.28e-15 | 2.61e-15 | 2.25e-15 | 7.94e-15 | 2.93e-15 | 2.29e-15 |
| sigma_tot (cm^2) | 8.65e-15 | 5.50e-15 | 4.76e-15 | 1.162e-14 | 6.02e-15 | 4.99e-15 |
| elastic share of collisions | 61.0 % | 47.5 % | 47.2 % | 68.3 % | 48.6 % | 45.9 % |
| j' = 2 share of collisions | 10.1 % | 10.7 % | 11.2 % | 6.9 % | 9.3 % | 10.4 % |
| collisions in levels above 52 | 0 | 0.003 % | 2.8 % | 0 | 1.5 % | 6.5 % |
| elastic share of momentum transfer | 4.8 % | 2.2 % | 2.7 % (1.9-3.1) | 3.7 % | 1.8 % (1.75-2.0) | 2.8 % (1.3-3.8) |
| j90 | 12 | 40 | > 52 | 18 | 52 | > 52 |
| rotation (meV) | 1.1 | 7.9 | 17.9 | 1.5 | 13.6 | 30.4 |
| recoil, central (floor to max) (meV) | 1.2 | 10.3 | 22.8 (19.6-32.2) | 1.8 | 17.8 (16.0-18.6) | 38.1 (28.8-85.6) |
Values in the CSVs: `docs/figures/h_co2/h_co2_numbers.csv`, `docs/figures/d_co2/d_co2_numbers.csv`.

## 11. Not done, and what the paper settled
- No interpolation between energies, no thermal average over initial j (the data are initial j = 0 only), no use of these data in the Monte Carlo model yet.
- Settled by the paper (read 16 Nov 2026):
  - Energies are centre-of-mass (section 3.1). The recoil formula uses this correctly.
  - The calculation is jz-conserving coupled states (CS) with a rigid-rotor CO2: rotational excitation only. No vibrational excitation, no electronic excitation, no reaction; the authors say the data are "not intended for modelling rovibrational excitation, vibrational heating, or CO2 dissociation" and note that experiments show vibrational excitation is a competing channel at eV energies (section 2.2). "Inelastic" in these data therefore means rotationally inelastic only.
  - The rotational basis is 71 even-j levels, j = 0, 2, ..., 140: the cap at j' = 140 is the basis size. Transitions above 140 are said to contribute negligibly. Convergence is guaranteed only for state-to-state cross sections above 0.01 Angstrom^2 (1e-18 cm^2); weaker ones are said to contribute less than 0.23 % of the total, and converging them would need about j = 350. This explains the alternation of sigma_j' at 5 eV: it starts where sigma_j' falls below 0.01 Angstrom^2 (j' about 110 for H), i.e. in the region the authors do not claim is converged (A55 explained, A59). The dotted line at 0.01 Angstrom^2 is now drawn on the by-level graphs.
  - Accuracy: CS agrees with close coupling to about 7 % for the momentum-transfer cross sections, but the CS/CC comparison in the paper (Fig. 4) covers only energies up to 3000 cm-1 (0.37 eV); at 1-5 eV the quoted accuracy rests on the general statement that CC agrees with laboratory data to about 10 %.
- Still open: no D-O (Zhang et al. 2009) tables yet; cause of residual differences between CS and CC at 1-5 eV not tested.

## 13. Cross-checks against the paper (16 Nov 2026)
| Paper | This analysis of the data files | Result |
|---|---|---|
| Fig. 2: total H-CO2 about 87 / 55 / 47.5 A^2, D-CO2 about 116 / 60 / 50 A^2 at 0.1 / 1 / 5 eV; elastic H about 53 / 26 / 22.5, D about 79 / 29 / 23 | table values 86.5 / 55.0 / 47.6 (H), 116.2 / 60.2 / 49.9 (D); elastic 52.8 / 26.1 / 22.5 (H), 79.4 / 29.3 / 22.9 (D) | agree (read from the figure) |
| Fig. 4: momentum-transfer cross section at 800 cm-1 (0.1 eV), H, j = 0: total about 24 A^2, elastic about 1.2-1.5 A^2 | sigma_mt total 24.0 A^2, elastic 1.16 A^2 (4.8 %) | agree: independent check of the (1 - cos theta) integrals and of the elastic share of momentum transfer at 0.1 eV |
| "less than 0.23 % of total from transitions below 0.01 A^2" | collisions in levels with sigma < 0.01 A^2: H 0.004 / 0.018 / 0.209 %, D 0.001 / 0.020 / 0.000 % | consistent |
| "elastic scattering accounts for 40-55 % of the total cross section across the full energy range" | elastic share 61.0 / 47.5 / 47.2 % (H), 68.3 / 48.6 / 45.9 % (D) at 0.1 / 1 / 5 eV; about 77 % at 0.001 eV | their sentence is looser than their own Fig. 2, which our numbers match; quote the numbers, not the sentence |
| "forward peak (theta < about 2 degrees) contributes more than 90 % of the integral cross section" | share of the total (j' <= 52) cross section below 2 degrees: H 16 / 35 / 46 %, D 32 / 44 / 51 %; 90 % is reached by 98 / 84 / 43 degrees (H) and 83 / 74 / 33 degrees (D); for the elastic channel alone 90 % lies within 9.4 / 4.5 / 2.2 degrees (H) and 6.6 / 3.0 / 1.5 degrees (D); more than 94 % of the momentum transfer comes from theta > 20 degrees | NOT reproduced for the total cross section; the DCS is strongly forward-peaked in magnitude, but the integral is not dominated by theta < 2 degrees. Do not repeat the sentence; consider asking the authors what it means |
## 12. History of corrections
First figures (14-15 Nov) had errors that were found by checking against the state-to-state file and replaced (A53): by-level elastic share used the truncated total (49 % at 5 eV, correct 47.2 %); 5 eV rotational energy 9.6 meV (correct 17.9); "90 % by j' = 46" invalid; elastic momentum share 3.1 % (about 2.7 %). A57: the 0.5-1.5 x range on the estimates was not a rigorous bound; replaced by the hard bounds above (this version).
