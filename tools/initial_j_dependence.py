#!/usr/bin/env python3
"""
How much does the initial rotational level of CO2 matter? Uses the full state-to-state matrix in <S>-CO2_state-to-state_CS.res
(columns: energy cm-1, final index jf, initial index ji, cross section Angstrom^2; level j = 2 x index, 71 even levels j = 0..140).

IMPORTANT (corrected 19 Nov 2026): the energy column is the TOTAL energy relative to the ground rotational level j = 0 (the paper: 'scattering
calculations were performed for total energies'; at low energies the initial and final levels present are exactly the levels with B j(j+1) <= E).
For the initial level j the COLLISION (kinetic) energy is E_total - B j(j+1). Initial levels must therefore be compared at the same COLLISION
energy, by interpolating each initial level's curves at E_total = E_collision + B j(j+1). (An earlier version of this script compared at the same
total energy and so overstated the dependence at 0.1 eV.)

For each initial level: total cross section, elastic share (j -> j), mean change of rotational energy per collision; and Boltzmann averages
(even j only, weights (2j+1) exp(-B j(j+1)/kT)). Only integral cross sections: angle distributions exist only for initial j = 0.
The file stops at 5 eV total energy, so for initial levels j > 0 the 5 eV point is the largest available collision energy (5 eV minus B j(j+1)).

    py initial_j_dependence.py --data "D:\\MASTERS\\Archive\\H-CO2" --system H
"""
import argparse
import collections
import sys
from pathlib import Path
import numpy as np

B, KB, CM1_PER_EV = 0.39022, 0.695035, 8065.541
ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--system", choices=["H", "D"], default="H")
a = ap.parse_args()
path = next((p for p in sorted(Path(a.data).rglob("*state-to-state*.res"))), None)
if path is None:
    sys.exit("state-to-state .res file not found")
Erot = lambda idx: B * (2 * idx) * (2 * idx + 1)                        # cm-1
R = collections.defaultdict(lambda: collections.defaultdict(dict))
for line in open(path):
    if line.startswith("#"):
        continue
    t = line.split()
    R[int(t[2])][round(float(t[0]), 3)][int(t[1])] = float(t[3])
C = {}
for ji, byE in R.items():
    Es = sorted(byE)
    Ec = np.array([e - Erot(ji) for e in Es])                          # collision energy of each row
    tot = np.array([sum(byE[e].values()) for e in Es])
    el = np.array([byE[e].get(ji, 0.0) for e in Es])
    dE = np.array([sum(v * (Erot(jf) - Erot(ji)) for jf, v in byE[e].items()) / sum(byE[e].values()) for e in Es])
    C[ji] = (Ec, tot, el, dE)


def at(ji, ec):
    Ec, tot, el, dE = C[ji]
    if ec < Ec.min():
        return None
    ec = min(ec, Ec.max())
    return np.interp(ec, Ec, tot), np.interp(ec, Ec, el), np.interp(ec, Ec, dE), ec


print(f"{a.system} + CO2, file {path.name}: {len(C)} initial levels; comparison at the same COLLISION energy")
for ev in (0.1, 1.0, 5.0):
    ec = ev * CM1_PER_EV
    print(f"\n-- collision energy {ev} eV: initial j | total (A^2) | elastic share | mean change of rotational energy (meV)")
    for ji in (0, 1, 2, 3, 5, 8, 10, 15, 20, 30):
        r = at(ji, ec) if ji in C else None
        if r is None:
            continue
        note = "" if abs(r[3] - ec) < 1e-6 else f"   (largest available collision energy {r[3] / CM1_PER_EV:.3f} eV)"
        print(f"   j={2 * ji:3d}: {r[0]:8.2f}  {100 * r[1] / r[0]:5.1f}%  {r[2] / CM1_PER_EV * 1000:+7.2f}{note}")
    r0 = at(0, ec)
    for T in (150, 200, 300):
        idx = [ji for ji in C if at(ji, ec) is not None and Erot(ji) < 2500]
        w = np.array([(4 * ji + 1) * np.exp(-Erot(ji) / (KB * T)) for ji in idx]); w /= w.sum()
        vals = [at(ji, ec) for ji in idx]
        tot = sum(w[k] * vals[k][0] for k in range(len(idx))); el = sum(w[k] * vals[k][1] for k in range(len(idx)))
        dE = sum(w[k] * vals[k][0] * vals[k][2] for k in range(len(idx))) / tot
        print(f"   thermal {T} K: total {tot:.2f} ({100 * (tot / r0[0] - 1):+.1f}% vs j=0), elastic share {100 * el / tot:.1f}% "
              f"(j=0: {100 * r0[1] / r0[0]:.1f}%), mean dE_rot {dE / CM1_PER_EV * 1000:+.2f} meV (j=0: {r0[2] / CM1_PER_EV * 1000:+.2f})")
