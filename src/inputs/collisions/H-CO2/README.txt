H + CO2 collision data for the corona3d model
=============================================

Source: Bop and Gacesa (2026), MNRAS 552, 1-8, doi 10.1093/mnras/stag1696. Data: doi 10.5281/zenodo.17549249.
CO2 starts in its lowest rotational level (j = 0); collision energies 0.001 to 5 eV (centre-of-mass frame).

These files follow the same layout as the existing O-H files in ../O-H (comma-separated, two columns, '#' header lines):

  total_cross_section_H_CO2.csv          energy (eV), cross section (cm^2). Total = all collisions (elastic plus
                                         rotationally inelastic). 149 energies, 0.001 to 5 eV. Counterpart of
                                         ../O-H/total_cross_section_O_H_elastic.csv
  diff_cross_section_H_CO2_<E>eV.csv     scattering angle (degrees, 0.1 to 180 in 0.1 steps), differential cross
                                         section (cm^2 per steradian; the header uses the same "sigma(cm^2)" label
                                         as the O-H files), summed over all final CO2 rotational levels.
                                         Counterpart of ../O-H/diff_cross_section_O_H_<E>eV.csv. E = 0.1, 1, 5 eV.

Sub-folders
  extra_energies/   the same kind of angle files at 0.34, 4 and 4.6 eV, for a later finer-energy test
  elastic_only/     the elastic-only variant (CO2 stays in j = 0): a sigma(E) file and angle files at 0.1, 1, 5 eV.
                    Only for a sensitivity test: it leaves out about half the collisions and almost all the
                    momentum transfer, so it gives a much larger escape rate than the total variant.

Conversions: energy cm-1 -> eV (divide by 8065.541); Angstrom^2 -> cm^2 (x 1e-16).
The angle files sum the final levels j' = 0, 2, ..., 52 (the supplied data stop at j' = 52); sigma(E) is taken from
the authors' own total table, which is about 3.5% higher than that sum at 4-5 eV.
Above 5 eV the data stop: the model holds sigma at its 5 eV value and uses the 5 eV angle file.

Configs: inputs/CO2_Mars_HotH_HCO2total.cfg and inputs/CO2_Mars_HotH_HCO2elastic.cfg use these files. The original
inputs/CO2_Mars_HotH.cfg (O-H data) is unchanged.
