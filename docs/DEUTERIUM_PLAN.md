# Plan: adding deuterium (D) to corona3d_2020

Status: design only. No code has been written. Written 7 Nov 2026 from a read of the source (`Particle_H.*`, `Distribution_Hot_H.cpp`, `main.cpp`, `Background_Species.cpp`, `Atmosphere.cpp`).

## 1. What the model does with a particle type (as read from the code)

- A species is a class (`Particle_H`, `Particle_O`, `Particle_N2`, `Particle_CO`, `Particle_CO2`) that only holds a mass and a name.
- `main.cpp::set_particle_type` builds the tracked particle from `part_type` in `corona3d_2020.cfg`; `Background_Species::set_particle_type` builds the background species from the species configs. Both are `if (type == "H") ... else if ...` chains.
- Hot atoms are produced by a distribution class chosen with `dist_type` (`Hot_H`, `Hot_O`, `MB`, `Import`). `Distribution_Hot_H` reads `Hot_H.cfg`, samples a birth altitude from the HCO+ DR rate (HCOplus_DR_rate_coeff * (Te/300)^-1.25 * [e] * [HCO+] from the profile files, so the rate depends on the temperature profile too), picks one of two electronic channels (23%: 1.3 eV, 77%: 7.31 eV, with CO vibrational structure) and sets the H speed from momentum conservation with CO: `v = sqrt(2 Ei / (m_H + m_H^2 / m_CO))`.
- Collision kinematics use `get_mass()` of the tracked particle and the partner, so a heavier test particle is handled by the existing collision code. What the code does NOT know is D-specific scattering: the cross sections (`total_sigma_file`) and the angular distributions (`energyN_file`) come from the species config files.
- The escape test uses the local escape speed, which does not depend on mass.

## 2. Changes needed

1. `Particle_D.hpp/.cpp`: copy of `Particle_H`, mass 2.01410178 amu, name "D".
2. `main.cpp` and `Background_Species.cpp`: add a `"D"` branch (and `#include "Particle_D.hpp"`); `dist_type "Hot_D"` branch in `main.cpp`.
3. `Distribution_Hot_D.hpp/.cpp`: copy of `Distribution_Hot_H` with
   - `m_D` in place of `m_H` in the speed formula (a D from the 7.31 eV channel carries Ei * m_CO/(m_CO+m_D) = 6.82 eV, against 7.06 eV for H, with m_CO = 28.0101 amu);
   - the parent ion DCO+ and its density: either a new profile file or the HCO+ profile scaled by a D/H ratio read from a new `Hot_D.cfg` parameter;
   - the dissociative recombination rate coefficient and branching ratios for DCO+ (initially assumed equal to HCO+; any isotope effect is an explicit assumption to state).
4. `makefile`: add the new object files.
5. New configs: `corona3d_2020_D.cfg` (`part_type D`, `dist_type Hot_D`) and D species configs (`O_Mars_HotD.cfg` etc.).

## 3. Scientific inputs to decide (not code)

- D/H ratio for the parent ion at each altitude (source and justification needed; Mars D/H is enhanced relative to Earth, and differs between the lower atmosphere and the exobase).
- D-O, D-N2, D-CO collision data (Zhang-style elastic, as for H) and D-CO2 data (Bop and Gacesa give H + CO2 only). First pass: use the H data for all four partners as an explicit stand-in, labelled `dproxy_*`, then replace partner by partner so each change is attributable.
- Whether D-D, H-D self-collisions matter (see logbook B10).

## 4. Validation plan

- V1 (regression): build D with the mass temporarily set to 1.00794 amu and DCO+ := HCO+; a seeded run must be bit-identical to the same-seed H run (same method as the build test of 6 Nov 2026). This proves the plumbing.
- V2: check the energy partition numerically (6.82 eV for D from the 7.31 eV channel, 7.06 eV for H) and that speeds match.
- V3: short D runs against the proxy data, then 10 runs each at LSA and HSA, analysed like the H sets.

## 5. Process rules

- Do the work in a SEPARATE copy or branch (for example `~/corona3d_D` and branch `deuterium`), never in `~/corona3dmasters/src` while runs are active: rebuilding replaces the executable that queued runs start from.
- Give the D executable a different name; record its md5 in `run_info.txt`.
- Every change goes in the logbook with the reason, the check, and the result.
