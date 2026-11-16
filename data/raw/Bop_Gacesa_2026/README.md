# Raw H + CO2 collision data (Bop and Gacesa 2026), as received

Source: C. T. Bop and M. Gacesa (2026), MNRAS 552, 1-8, doi:10.1093/mnras/stag1696. Data release: Zenodo, doi:10.5281/zenodo.17549249
(Bop and Gacesa 2025a, "Superthermal kinetic energy transfer via CO2 collisions with H and D: elastic and inelastic cross-sections").
Licence of the Zenodo record: CC BY 4.0 (checked on the record, 16 Nov 2026), so redistribution is allowed with attribution: cite the paper and the dataset. The record holds one file, `Archive.zip` (135,546,983 bytes, md5 `e1ebc4637a175a5bd142a6512697e551`); the files here are copies of files inside it.

These files are UNMODIFIED copies of the files received (checksums in `MD5SUMS.txt`; verified byte for byte against the originals inside the Zenodo `Archive.zip`, entry A52). Original location of the user's copies:
`D:\MASTERS\Archive\H-CO2` (cross sections) and `D:\MASTERS\Archive\H-CO2\H-CO2_DCS` (angle distributions).

## Contents of `H-CO2/`

| File | Content |
|---|---|
| `E0.10-DCS.txt`, `E1.00-DCS.txt`, `E5.00-DCS.txt` | differential cross sections at collision energies 0.1, 1 and 5 eV (centre-of-mass frame; the energy is in the file name). 27 blocks of 1,800 rows, one block per FINAL rotational level j' = 0, 2, 4, ..., 52 of CO2 (initial level j = 0). Each block starts with a header line `# DFFCSO. ACCUM LEV(I),J(I) = 1 0 LEV(F),J(F) = <level> <j'> , M = 0, WEIGHTED BY 1.00000`. Columns: scattering angle (degrees, 0.1 to 180 in steps of 0.1), differential cross section (Angstrom^2 per steradian). Block 1 (final j' = 0) is the ELASTIC channel; blocks 2 to 27 are rotationally inelastic. |
| `H-CO2_state-to-state_CS.res` | cross sections out of the ground state (and other initial levels) into EVERY final level, for each of the 149 energies (437,000 rows). Columns: energy (cm^-1), final level index jf (final j' = 2 x jf), initial level index ji, cross section (Angstrom^2). Needed for the levels above j' = 52 that the angle files do not contain (2.8% of the collisions at 5 eV). 22 MB. |
| `H-CO2_total_and_elastic_CS.out` | 149 energies from 8.07 to 40,328 cm^-1 (0.001 to 5 eV). Columns: energy (cm^-1), j, total cross section (Angstrom^2, all final states), elastic cross section (Angstrom^2). |

## How they are used in the model

The converted files in `src/inputs/collisions/H-CO2/` were made from these (Angstrom^2 to cm^2: x 1e-16; cm^-1 to eV: / 8065.541). Elastic-only runs use block 1 and the elastic cross section; the "total" variant uses the sum over all blocks and the total cross section. See `LOGBOOK_changes.md` (entries A7, A8, A13, A24, A28, A52, A53).

## Figures made from these files

`docs/figures/h_co2/` (made by `tools/plot_h_co2_figures.py`).
