#!/usr/bin/env python3
"""
Make the input files for the channel-resolved (rotationally inelastic) CO2 collisions from the Bop and Gacesa (2026) data.
Needs numpy only.

Writes, into the output folder (default inputs/collisions/<S>-CO2/channels):
  state_to_state_cross_section_<S>_CO2.csv
      '#' comment lines, then   dE_eV,<energy loss of channel 1>,...,<channel N>   then one row per collision energy:
      E_eV,<cross section channel 1>,...,<channel N>    (cm^2; initial CO2 level j = 0; channel c = final level j' = 2(c-1))
      N = 71 channels (j' = 0, 2, ..., 140); channel 1 is the elastic one (energy loss 0).
  diff_cross_section_<S>_CO2_state_to_state_<E>eV.csv     (one per requested energy)
      '#' comment lines, then angle (degrees),<dsigma/dOmega channel 1>,...,<channel N>   (cm^2 per steradian, 1800 angles)

Energy loss of channel j' = rotational energy of CO2, B j'(j'+1), rigid rotor, B = 0.39022 cm-1 (the highest open level at the lowest
energies of the authors' file brackets B between 0.3841 and 0.4033 cm-1).

Angle distributions exist in the authors' files only for j' <= 52. For the other channels (assumption, chosen with --high-j-shape):
  last       the angle distribution of j' = 52, scaled to the channel's cross section (mean 1 - cos(theta) about 0.6 at 5 eV for H)
  isotropic  constant in the centre-of-mass angle (mean 1 - cos(theta) = 1)
Blocks without signal (channels closed at that energy) get the shape of the highest channel that has one, scaled to a negligible cross
section (1e-30 cm^2), so that the cumulative table is always valid. Because the code uses the angle file of the NEAREST tabulated energy,
a channel that opens between two tabulated energies uses that placeholder shape there: add more energies (--energies) to reduce this.

Example (PowerShell):
  py make_channel_files.py --system H --data "D:\\MASTERS\\Archive\\H-CO2" --out "src\\inputs\\collisions\\H-CO2\\channels"
  py make_channel_files.py --system D --data "D:\\MASTERS\\Archive\\D-CO2" --out "src\\inputs\\collisions\\D-CO2\\channels" --energies 0.1 1 5
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

A2_TO_CM2 = 1e-16
CM1_PER_EV = 8065.541
B_ROT = 0.39022                      # cm-1
N_CHANNELS = 71                      # j' = 0, 2, ..., 140
J_MAX_ANGLES = 52                    # angle files stop here


def find_one(folder, stem, suffixes):
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file() and stem.lower() in p.name.lower() and p.suffix.lower() in suffixes:
            return p
    sys.exit(f"Could not find a file containing '{stem}' under {folder}")


def dcs_source(folder, e_ev):
    """text of the angle file for collision energy e_ev (loose file E<e>-DCS.txt, or inside a zip with DCS in its name)"""
    pat = re.compile(r"^E(\d+\.\d+)-DCS\.txt$", re.I)
    for p in sorted(Path(folder).rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".txt" and pat.match(p.name) and abs(float(pat.match(p.name).group(1)) - e_ev) < 1e-9:
            return open(p).read()
        if p.suffix.lower() == ".zip" and "DCS" in p.name.upper():
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    m = pat.match(Path(n).name)
                    if m and abs(float(m.group(1)) - e_ev) < 1e-9:
                        return z.read(n).decode("ascii", "replace")
    sys.exit(f"Angle file for {e_ev} eV not found under {folder} (need E<energy>-DCS.txt or the DCS zip)")


def read_blocks(text):
    lines = text.splitlines()
    heads = [i for i, l in enumerate(lines) if l.startswith("#")]
    out = {}
    for k, a in enumerate(heads):
        b = heads[k + 1] if k + 1 < len(heads) else len(lines)
        m = re.search(r"LEV\(F\),J\(F\) =\s*\d+\s+(\d+)", lines[a])
        arr = np.array(" ".join(lines[a + 1:b]).split(), dtype=float).reshape(-1, 2)
        out[int(m.group(1))] = (arr[:, 0], arr[:, 1] * A2_TO_CM2)
    return out


def integral(angle_deg, dcs):
    """2 pi integral dcs sin(theta) dtheta (trapezoid; the strip below the first angle is neglected: small for the shape only)"""
    th = np.radians(angle_deg)
    f = dcs * np.sin(th)
    return 2 * np.pi * np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(th))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", choices=["H", "D"], default="H")
    ap.add_argument("--data", required=True, help="folder with the raw files (cross-section table, state-to-state .res, angle files or DCS zip)")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--energies", type=float, nargs="+", default=[0.1, 1.0, 5.0], help="collision energies (eV) of the angle files")
    ap.add_argument("--high-j-shape", choices=["last", "isotropic"], default="last")
    a = ap.parse_args()
    S = a.system
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # ---- cross section of every channel at every energy (state-to-state file, initial level j = 0) ----
    res = find_one(a.data, f"{S}-CO2_state-to-state", {".res"})
    sig, e_exact = {}, {}
    for line in open(res):
        if line.startswith("#"):
            continue
        t = line.split()
        if int(t[2]) == 0:
            key = round(float(t[0]), 3)            # key for grouping the rows of one energy; the energy itself is kept unrounded
            e_exact.setdefault(key, float(t[0]))
            sig.setdefault(key, np.zeros(N_CHANNELS))[int(t[1])] = float(t[3]) * A2_TO_CM2
    e_cm1 = np.array([e_exact[k] for k in sorted(sig)])
    sig = {e_exact[k]: sig[k] for k in sig}
    e_ev = e_cm1 / CM1_PER_EV
    table = np.array([sig[k] for k in e_cm1])                       # [energy, channel], cm^2
    d_e = np.array([B_ROT * (2 * c) * (2 * c + 1) / CM1_PER_EV for c in range(N_CHANNELS)])   # eV

    # consistency with the authors' total cross section
    tab = [l.split() for l in open(find_one(a.data, f"{S}-CO2_total_and_elastic_CS", {".out", ".txt", ".dat"})).read().splitlines()[1:] if l.strip()]
    tot_auth = np.array([float(r[2]) for r in tab]) * A2_TO_CM2
    dev = np.max(np.abs(table.sum(axis=1) / tot_auth - 1))
    print(f"{len(e_ev)} energies; sum over channels against the authors' total cross section: max deviation {dev:.2e}")

    with open(out / f"state_to_state_cross_section_{S}_CO2.csv", "w") as f:
        f.write(f"#{S}-CO2 state-to-state collision cross sections from Bop and Gacesa 2026 (CO2 initially in level j = 0)\n")
        f.write(f"#Energy(eV),sigma(cm^2) for each final level j' = 0, 2, ..., 140 (columns 2 to 72, channel c = j' = 2(c-1)); row 'dE_eV': rotational energy gained by CO2 (eV), B j'(j'+1), B = {B_ROT} cm-1\n")
        f.write("dE_eV," + ",".join(f"{x:.8e}" for x in d_e) + "\n")
        for i in range(len(e_ev)):
            f.write(f"{e_ev[i]:.8e}," + ",".join(f"{x:.8e}" for x in table[i]) + "\n")
    print("wrote", out / f"state_to_state_cross_section_{S}_CO2.csv")

    # ---- angle distributions per channel at the requested energies ----
    for e in a.energies:
        blocks = read_blocks(dcs_source(a.data, e))
        ang = blocks[0][0]
        k = int(np.argmin(np.abs(e_ev - e)))
        s_e = table[k]                                               # channel cross sections at this energy
        cols = [None] * N_CHANNELS
        notes = []
        for c in range(N_CHANNELS):
            jp = 2 * c
            if jp <= J_MAX_ANGLES and jp in blocks and np.sum(blocks[jp][1]) > 0:
                cols[c] = blocks[jp][1].copy()
        have = [c for c in range(N_CHANNELS) if cols[c] is not None]
        last = have[-1]
        for c in range(N_CHANNELS):
            jp = 2 * c
            if cols[c] is not None:
                continue                                              # real angle distribution from the source
            # no usable angle data: j' > 52, or a block without signal (channel closed at this energy)
            if jp > J_MAX_ANGLES and a.high_j_shape == "isotropic" and s_e[c] > 0:
                shape = np.ones_like(ang)
            else:
                shape = blocks[2 * last][1].copy()                     # shape of the highest channel with a signal
            target = s_e[c] if s_e[c] > 0 else 1e-30
            cols[c] = shape * target / integral(ang, shape)
        assumed = [2 * c for c in range(N_CHANNELS) if 2 * c > J_MAX_ANGLES and s_e[c] > 0]
        name = out / f"diff_cross_section_{S}_CO2_state_to_state_{e:g}eV.csv"
        with open(name, "w") as f:
            f.write(f"#{e:g}eV differential cross sections (cm^2 per steradian) for {S}-CO2 state-to-state collisions from Bop and Gacesa 2026 (CO2 j = 0 -> j' = 0, 2, ..., 140)\n")
            f.write(f"#angle(deg),sigma(cm^2) for each final level j' (columns 2 to 72; no angle data in the source above j' = {J_MAX_ANGLES}: shape assumption '{a.high_j_shape}'; channels with no signal at this energy: placeholder shape, cross section 1e-30)\n")
            for i in range(len(ang)):
                f.write(f"{ang[i]:.2f}," + ",".join(f"{cols[c][i]:.6e}" for c in range(N_CHANNELS)) + "\n")
        n_open = int(np.sum(s_e > 0))
        print(f"wrote {name.name}: {n_open} open channels at the nearest tabulated energy ({e_ev[k]:.4g} eV); "
              f"{len(assumed)} open channels above j' = {J_MAX_ANGLES} use the '{a.high_j_shape}' assumption "
              f"({100 * s_e[[c for c in range(N_CHANNELS) if 2 * c > J_MAX_ANGLES]].sum() / s_e.sum():.2f} % of the collisions)")


if __name__ == "__main__":
    main()
