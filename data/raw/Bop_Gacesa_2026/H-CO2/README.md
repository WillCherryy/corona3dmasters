# Raw H + CO2 collision data (Bop and Gacesa 2026), as received

Source: C. T. Bop and M. Gacesa (2026), MNRAS 552, 1-8, doi:10.1093/mnras/stag1696.
Data: Bop, C. T. and Gacesa, M. (2025), Zenodo, doi:10.5281/zenodo.17549249, licence CC BY 4.0 (cite when using).
Checked byte for byte (MD5) on 2026-11-16 against the originals inside Archive.zip (md5 e1ebc4637a175a5bd142a6512697e551):
- H-CO2_total_and_elastic_CS.out = Archive/H-CO2/H-CO2_total_and_elastic_CS.out
- E0.10-DCS.txt, E1.00-DCS.txt, E5.00-DCS.txt = DCS_CO2-H/ inside Archive/H-CO2/H-CO2_DCS.zip

E*-DCS.txt: 27 blocks of 1,800 rows, one per final CO2 rotational level j' = 0, 2, ..., 52 (initial j = 0); columns angle (degrees) and differential cross section (Angstrom^2 per steradian); block 1 (j' = 0) is the elastic channel.
H-CO2_total_and_elastic_CS.out: energy (cm^-1), j, total and elastic cross sections (Angstrom^2).
The same archive also holds D + CO2 (Archive/D-CO2/) and 150 collision energies per isotope.
Figures: tools/plot_h_co2_figures.py makes them; results in docs/figures/h_co2/.
