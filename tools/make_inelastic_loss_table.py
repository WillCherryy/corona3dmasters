#!/usr/bin/env python3
"""
Mean energy loss of an INELASTIC H(D) + CO2 collision against collision energy, from the Bop and Gacesa (2026) state-to-state file
(initial CO2 level j = 0; the energy column equals the collision energy for j = 0):

    dE(E) = sum over final levels j' >= 2 of sigma_j'(E) B j'(j'+1)  /  sum over j' >= 2 of sigma_j'(E)        (eV)

B = 0.39022 cm-1 (rigid rotor), the rotational energy gained by CO2 (taken out of the relative motion). Needs numpy only.
Writes, O-H folder style (two '#' lines, then 'Energy(eV),dE(eV)'):
  inelastic_energy_loss_<S>_CO2.csv       all 149 energies (use this one: it also covers energies below 0.1 eV)
  inelastic_energy_loss_<S>_CO2_3pt.csv   only 0.1, 1 and 5 eV (a table of three points is unsafe below about 3 meV, where the loss
                                          would exceed the collision energy)

    py make_inelastic_loss_table.py --system H --data "D:\\MASTERS\\Archive\\H-CO2" --out "src\\inputs\\collisions\\H-CO2"
"""
import argparse
import collections
import sys
from pathlib import Path

B, CM = 0.39022, 8065.541
ap = argparse.ArgumentParser()
ap.add_argument("--system", choices=["H", "D"], default="H")
ap.add_argument("--data", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
S = a.system
res = next((p for p in sorted(Path(a.data).rglob(f"{S}-CO2_state-to-state*.res"))), None)
if res is None:
    sys.exit("state-to-state .res file not found")
rows = collections.defaultdict(dict)
for line in open(res):
    if line.startswith("#"):
        continue
    t = line.split()
    if int(t[2]) == 0:
        rows[float(t[0])][2 * int(t[1])] = float(t[3])
E = sorted(rows)
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
data = []
for k in E:
    inel = {j: v for j, v in rows[k].items() if j > 0}
    dE = sum(v * B * j * (j + 1) for j, v in inel.items()) / sum(inel.values()) / CM        # eV
    data.append((k / CM, dE))
hdr = (f"#{S}-CO2 mean energy loss per inelastic collision from Bop and Gacesa 2026 (rotational energy gained by CO2, CO2 initially in j = 0; B = {B} cm-1)\n"
       "#Energy(eV),dE(eV)\n")
with open(out / f"inelastic_energy_loss_{S}_CO2.csv", "w", newline="") as f:
    f.write(hdr)
    for e, d in data:
        f.write(f"{e:.6f},{d:.6E}\n")
with open(out / f"inelastic_energy_loss_{S}_CO2_3pt.csv", "w", newline="") as f:
    f.write(hdr)
    for target in (0.1, 1.0, 5.0):
        e, d = min(data, key=lambda x: abs(x[0] - target))
        f.write(f"{target:.6f},{d:.6E}\n")
        print(f"{target} eV: {d * 1000:.3f} meV per inelastic collision")
print("wrote", out / f"inelastic_energy_loss_{S}_CO2.csv", "and the 3-point version;", len(data), "energies; the loss is below the collision energy at all of them:", all(d < e for e, d in data))
