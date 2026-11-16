#!/usr/bin/env python3
"""
How much does the initial rotational level of CO2 matter? Uses the full state-to-state matrix in
<S>-CO2_state-to-state_CS.res (columns: energy cm-1, final index jf, initial index ji, cross section Angstrom^2;
level j = 2 x index, the basis being the 71 even levels j = 0, 2, ..., 140).

For each initial level: total cross section, elastic share (j -> j), mean change of rotational energy per collision.
Also Boltzmann averages over initial levels (even j only, weights (2j+1) exp(-B j(j+1)/kT)), assuming the cross sections
are averaged over the magnetic sublevels in the usual way (not checked against the paper).
Only integral cross sections: angle distributions exist only for initial j = 0.

    py initial_j_dependence.py --data "D:\\MASTERS\\Archive\\H-CO2" --system H
"""
import argparse
import collections
import sys
from pathlib import Path
import numpy as np

B, KB, CM1_PER_EV = 0.39022, 0.695035, 8065.541          # cm-1, cm-1 per K, cm-1 per eV
ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--system", choices=["H", "D"], default="H")
a = ap.parse_args()
path = next((p for p in sorted(Path(a.data).rglob("*state-to-state*.res"))), None)
if path is None:
    sys.exit("state-to-state .res file not found")
targets = {0.1: 806.5541, 1.0: 8065.541, 5.0: 40327.705}
S = {e: collections.defaultdict(dict) for e in targets}
for line in open(path):
    if line.startswith("#"):
        continue
    t = line.split(); E = float(t[0])
    for e, c in targets.items():
        if abs(E - c) < 0.02:
            S[e][int(t[2])][int(t[1])] = float(t[3])
Ej = lambda idx: B * (2 * idx) * (2 * idx + 1)                 # cm-1
print(f"{a.system} + CO2, file {path.name}: {len(S[1.0])} initial levels")
for e in targets:
    M = S[e]; rows = {}
    for ji in sorted(M):
        tot = sum(M[ji].values()); el = M[ji].get(ji, 0.0)
        dE = sum(v * (Ej(jf) - Ej(ji)) for jf, v in M[ji].items()) / tot / CM1_PER_EV * 1000
        rows[ji] = (tot, el / tot, dE)
    print(f"\n-- {e} eV: initial j | total (A^2) | elastic share | mean change of rotational energy (meV)")
    for ji in (0, 1, 2, 3, 5, 8, 10, 15, 20, 30):
        if ji in rows:
            print(f"   j={2 * ji:3d}: {rows[ji][0]:8.2f}  {rows[ji][1] * 100:5.1f}%  {rows[ji][2]:+7.2f}")
    idx = np.array(sorted(M))
    for T in (150, 200, 300):
        w = np.array([(4 * i + 1) * np.exp(-Ej(i) / (KB * T)) for i in idx]); w /= w.sum()
        tot = sum(w[k] * rows[i][0] for k, i in enumerate(idx))
        el = sum(w[k] * rows[i][0] * rows[i][1] for k, i in enumerate(idx))
        dE = sum(w[k] * rows[i][0] * rows[i][2] for k, i in enumerate(idx)) / tot
        print(f"   thermal {T} K: total {tot:.2f} ({100 * (tot / rows[0][0] - 1):+.1f}% vs j=0), elastic share {100 * el / tot:.1f}% "
              f"(j=0: {rows[0][1] * 100:.1f}%), mean dE_rot {dE:+.2f} meV (j=0: {rows[0][2]:+.2f})")
