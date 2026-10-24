H + CO2 collision data for the corona3d model
=============================================

Source
------
Bop, C. T. and Gacesa, M. (2026), Quantum scattering of hot H/D on CO2: cross-sections and rate
coefficients for planetary atmospheres and their evolution, MNRAS 552, 1-8, doi 10.1093/mnras/stag1696.
Data: doi 10.5281/zenodo.17549249.

The data are for CO2 starting in its lowest rotational level (j = 0), collision energies 0.001 to 5 eV
(centre-of-mass frame). The model code needs two kinds of table, described below.

Files
-----
total_cross_section_H_CO2_total.csv      sigma(E), total (elastic + rotationally inelastic)
total_cross_section_H_CO2_elastic.csv    sigma(E), elastic only (CO2 stays in j = 0)
    Columns: energy in eV, cross section in cm^2. 149 energies, 0.001 to 5 eV, in increasing order.
    The model uses this to compute how likely a collision is at the collision energy
    (collision probability per timestep = 1 - exp(-sigma n v dt)).

diff_cross_section_H_CO2_total_<E>eV.csv    differential cross section, summed over all final CO2 rotational levels
diff_cross_section_H_CO2_elastic_<E>eV.csv  differential cross section, elastic only
    Columns: scattering angle in degrees (0.1 to 180 in uniform 0.1 degree steps), cross section in cm^2/sr.
    One file per collision energy E = 0.1, 0.34, 1, 4, 4.6, 5 eV. The model uses these to draw the scattering
    angle after a collision (the nearest listed energy is used; there is no interpolation in energy).
    The very large values at small angles are the forward peak: most collisions deflect the H atom only slightly.

Variants
--------
total    Every collision is counted and the angle is drawn from the summed distribution. The model treats every
         collision as elastic, so the small energy given to CO2 rotation is not removed from the H atom.
elastic  Only collisions that leave CO2 in its initial rotational level are counted. Cleaner physically but the
         collision rate is roughly half the total.

Conversions made
----------------
energy cm-1 -> eV: divide by 8065.541 (the conversion used for the source energy grid)
cross section Angstrom^2 -> cm^2: multiply by 1e-16
total DCS = sum over final levels j' = 0, 2, ..., 52 (the supplied angle files stop at j' = 52; at 4-5 eV this is
about 3.5% below the total in the sigma(E) table, which is why sigma(E) is taken from the table, not from the angle files)

Notes
-----
- Above 5 eV the data stop. The model holds sigma at its 5 eV value and uses the 5 eV angle table.
- Configs that use these files: inputs/CO2_Mars_HotH_HCO2total.cfg and inputs/CO2_Mars_HotH_HCO2elastic.cfg
  (the original inputs/CO2_Mars_HotH.cfg, which uses the O-H data, is unchanged).
