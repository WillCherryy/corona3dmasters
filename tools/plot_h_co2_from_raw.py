#!/usr/bin/env python3
"""H + CO2 elastic against inelastic collisions, made DIRECTLY from the files supplied with
Bop and Gacesa (2026) (Zenodo 10.5281/zenodo.17549249):

  E0.10-DCS.txt, E1.00-DCS.txt, E5.00-DCS.txt   27 blocks each, one per final CO2 rotational level j' = 0, 2, ..., 52
                                                (angle in degrees, differential cross section in Angstrom^2 per steradian)
  H-CO2_total_and_elastic_CS.out                energy (cm-1), total and elastic cross sections (Angstrom^2)

Writes two figures (PNG and PDF) and a table of numbers:
  <prefix>_overview   : angle distributions, cross sections, share of collisions, share of momentum transfer
  <prefix>_by_level   : cross section by final rotational level, and how much of the momentum transfer each level carries
  <prefix>_numbers.csv

Usage: python3 plot_h_co2_from_raw.py [directory with the raw files] [output prefix]
"""
import sys, os, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

raw = sys.argv[1] if len(sys.argv) > 1 else "data/raw/Bop_Gacesa_2026/H-CO2"
prefix = sys.argv[2] if len(sys.argv) > 2 else "docs/figures/h_co2_raw"
os.makedirs(os.path.dirname(prefix) or ".", exist_ok=True)

BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#444444"
A2 = 1e-16                                   # Angstrom^2 -> cm^2
CM1_TO_EV = 1.0 / 8065.541
B_ROT = 0.39022 * CM1_TO_EV                  # CO2 rotational constant (approximate), eV
M_H, M_CO2 = 1.00794, 44.0095                # amu
F_RECOIL = 4 * M_H * M_CO2 / (M_H + M_CO2) ** 2
ENERGIES = [("E0.10-DCS.txt", 0.1), ("E1.00-DCS.txt", 1.0), ("E5.00-DCS.txt", 5.0)]


def read_blocks(path):
    """Return {final j': (angle_deg, dcs_cm2_per_sr)} for one DCS file."""
    out, cur = {}, None
    for line in open(path):
        if line.startswith("#"):
            m = re.search(r"LEV\(F\),J\(F\) =\s*\d+\s+(\d+)", line)
            cur = int(m.group(1)); out[cur] = []
        elif line.strip():
            a, d = line.split()[:2]
            out[cur].append((float(a), float(d) * A2))
    return {j: (np.array(v)[:, 0], np.array(v)[:, 1]) for j, v in out.items()}


def integrate(angle_deg, dcs, weight=None):
    """2 pi * integral of dcs * sin(theta) * weight dtheta, trapezoid rule plus the strip below the first angle."""
    th = np.radians(angle_deg)
    w = np.ones_like(th) if weight is None else weight(th)
    f = dcs * np.sin(th) * w
    body = np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(th))
    A = np.vstack([np.ones(5), th[:5] ** 2]).T            # D ~ a + b theta^2 near zero
    a, b = np.linalg.lstsq(A, dcs[:5], rcond=None)[0]
    tt = np.linspace(0, th[0], 2001)
    g = (a + b * tt ** 2) * np.sin(tt) * (np.ones_like(tt) if weight is None else weight(tt))
    strip = np.sum(0.5 * (g[1:] + g[:-1]) * np.diff(tt))
    return 2 * np.pi * (body + strip)


# ---- cross sections against energy (authors' tables) -------------------------------------------------
rows = [l.split() for l in open(os.path.join(raw, "H-CO2_total_and_elastic_CS.out")).read().splitlines()[1:] if l.strip()]
E_tab = np.array([float(r[0]) for r in rows]) * CM1_TO_EV
S_tot = np.array([float(r[2]) for r in rows]) * A2
S_el = np.array([float(r[3]) for r in rows]) * A2

# ---- per energy: blocks, integrals ------------------------------------------------------------------
res = []
for fname, e in ENERGIES:
    blocks = read_blocks(os.path.join(raw, fname))
    js = sorted(blocks)
    ang = blocks[0][0]
    d_el = blocks[0][1]
    d_in = sum(blocks[j][1] for j in js if j > 0)
    d_tot = d_el + d_in
    sig = {j: integrate(ang, blocks[j][1]) for j in js}
    mt = {j: integrate(ang, blocks[j][1], lambda t: 1 - np.cos(t)) for j in js}
    sig_sum = sum(sig.values()); mt_sum = sum(mt.values())
    tab_tot = np.interp(e, E_tab, S_tot); tab_el = np.interp(e, E_tab, S_el)
    e_rot = {j: B_ROT * j * (j + 1) for j in js}
    mean_rot = sum(sig[j] * e_rot[j] for j in js) / sig_sum                     # eV per collision, to rotation
    mean_1mc = mt_sum / sig_sum
    e_lab = e * (M_H + M_CO2) / M_CO2                                           # lab energy of the H atom
    mean_recoil = 0.5 * F_RECOIL * mean_1mc * e_lab                             # eV per collision, to recoil
    res.append(dict(E=e, js=js, ang=ang, d_el=d_el, d_in=d_in, d_tot=d_tot, sig=sig, mt=mt, sig_sum=sig_sum, mt_sum=mt_sum,
                    tab_tot=tab_tot, tab_el=tab_el, mean_rot=mean_rot, mean_recoil=mean_recoil, mean_1mc=mean_1mc))

with open(prefix + "_numbers.csv", "w") as f:
    f.write("E_eV,sigma_elastic_table_cm2,sigma_total_table_cm2,sigma_sum_levels_cm2,sum_over_total_table,"
            "elastic_share_collisions,elastic_share_momentum,mean_1-cos_total,mean_rotational_energy_eV,mean_recoil_energy_eV\n")
    for r in res:
        f.write(f"{r['E']},{r['tab_el']:.4e},{r['tab_tot']:.4e},{r['sig_sum']:.4e},{r['sig_sum']/r['tab_tot']:.4f},"
                f"{r['sig'][0]/r['sig_sum']:.4f},{r['mt'][0]/r['mt_sum']:.4f},{r['mean_1mc']:.4f},{r['mean_rot']:.5f},{r['mean_recoil']:.5f}\n")

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})

# ---- figure 1: overview ----------------------------------------------------------------------------
fig = plt.figure(figsize=(13, 8.2))
gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.28, top=0.88)
for k, r in enumerate(res):
    ax = fig.add_subplot(gs[0, k])
    lo = np.min(r["d_tot"][r["d_tot"] > 0]) * 0.5
    me, mi = r["d_el"] > lo, r["d_in"] > lo
    l_tot, = ax.plot(r["ang"], r["d_tot"], color=GREY, lw=1.6, ls="--")
    l_el, = ax.plot(r["ang"][me], r["d_el"][me], color=BLUE, lw=2.0)
    l_in, = ax.plot(r["ang"][mi], r["d_in"][mi], color=ORANGE, lw=2.0)
    ax.axvline(2.0, color="#999999", lw=0.9, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.1, 180); ax.set_ylim(lo, r["d_tot"].max() * 3)
    ax.set_xticks([0.1, 1, 10, 100]); ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.set_xlabel("scattering angle (degrees)")
    if k == 0:
        ax.set_ylabel(r"$d\sigma/d\Omega$ (cm$^2$ sr$^{-1}$)"); handles = [l_el, l_in, l_tot]
    ax.set_title(f"{r['E']:g} eV", fontsize=11, fontweight="bold")
    ax.text(2.2, r["d_tot"].max() * 1.6, r"$2^\circ$", color="#777777", fontsize=8.5, va="top")
fig.legend(handles, ["elastic ($j'=0$)", "inelastic (sum of all $j'>0$)", "total (sum of all $j'$)"],
           loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=3, frameon=False, fontsize=10)

ax = fig.add_subplot(gs[1, 0])
ax.loglog(E_tab, S_tot, color=GREY, lw=1.6, ls="--", label="total")
ax.loglog(E_tab, S_el, color=BLUE, lw=2.0, label="elastic")
ax.loglog(E_tab, S_tot - S_el, color=ORANGE, lw=2.0, label="inelastic (total $-$ elastic)")
for r in res: ax.axvline(r["E"], color="#999999", lw=0.8, ls=":")
ax.set_xlabel("collision energy (eV)"); ax.set_ylabel(r"cross section (cm$^2$)")
ax.set_title("Cross sections", fontsize=11, fontweight="bold"); ax.legend(frameon=False, fontsize=8.5)

labels = [f"{r['E']:g} eV" for r in res]; x = np.arange(3)
ax = fig.add_subplot(gs[1, 1])
el_c = np.array([r["tab_el"] / r["tab_tot"] for r in res]) * 100
ax.bar(x, el_c, color=BLUE, width=0.6, label="elastic"); ax.bar(x, 100 - el_c, bottom=el_c, color=ORANGE, width=0.6, label="inelastic")
for i, v in enumerate(el_c):
    ax.text(i, v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
    ax.text(i, v + (100 - v) / 2, f"{100 - v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 100); ax.grid(False)
ax.set_ylabel("share of all collisions (%)"); ax.set_title("How often", fontsize=11, fontweight="bold")
ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

ax = fig.add_subplot(gs[1, 2])
el_m = np.array([r["mt"][0] / r["mt_sum"] for r in res]) * 100
ax.bar(x, el_m, color=BLUE, width=0.6); ax.bar(x, 100 - el_m, bottom=el_m, color=ORANGE, width=0.6)
for i, v in enumerate(el_m):
    ax.text(i, 100 - (100 - v) / 2, f"{100 - v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
    ax.text(i, v + 3.5, f"{v:.1f}%", ha="center", va="bottom", color=BLUE, fontweight="bold", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 112); ax.set_yticks([0, 25, 50, 75, 100]); ax.grid(False)
ax.set_ylabel("share of momentum transfer (%)"); ax.set_title("How much deflection", fontsize=11, fontweight="bold")
fig.suptitle("H + CO$_2$: elastic against rotationally inelastic collisions "
             "(Bop and Gacesa 2026 data, CO$_2$ initially in $j=0$)", fontsize=12.5, y=1.025)
fig.text(0.5, -0.015,
         "Angle panels: elastic = block $j'=0$, inelastic = sum of the blocks $j'=2$ to 52. Cross sections against energy and "
         "'how often': the authors' total and elastic tables.\n"
         "'How much deflection': $\\sigma_{mt}=2\\pi\\int(1-\\cos\\theta)(d\\sigma/d\\Omega)\\sin\\theta\\,d\\theta$ summed over levels $j'=0$ to 52 "
         "(the data stop at 52). Dotted line: $2^\\circ$, the edge of the forward peak.",
         ha="center", va="top", fontsize=8.5, color="#555555")
fig.savefig(prefix + "_overview.png", dpi=200, bbox_inches="tight"); fig.savefig(prefix + "_overview.pdf", bbox_inches="tight")
plt.close(fig)

# ---- figure 2: by final rotational level -------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(13, 7.4), gridspec_kw=dict(hspace=0.42, wspace=0.28))
for k, r in enumerate(res):
    js = np.array(r["js"]); s = np.array([r["sig"][j] for j in js])
    ax = axes[0, k]
    ax.bar(js, s, width=1.7, color=[BLUE if j == 0 else ORANGE for j in js])
    s = np.clip(s, 1e-25, None)
    ax.bar(js, s, width=1.7, color=[BLUE if j == 0 else ORANGE for j in js])
    ax.set_yscale("log"); ax.set_xlim(-2, 54); ax.set_ylim(s.min() * 0.5, s.max() * 2.5)
    ax.set_xlabel("final rotational level $j'$"); ax.set_title(f"{r['E']:g} eV", fontsize=11, fontweight="bold")
    if k == 0: ax.set_ylabel(r"cross section $\sigma_{j'}$ (cm$^2$)")
    ax.text(0.97, 0.93, f"elastic: {s[0]/s.sum():.0%} of collisions\n$j'=2$: {s[1]/s.sum():.0%}", transform=ax.transAxes,
            ha="right", va="top", fontsize=9)
    ax = axes[1, k]
    mtv = np.array([r["mt"][j] for j in js]); cum_mt = np.cumsum(mtv) / mtv.sum(); cum_s = np.cumsum(s) / s.sum()
    ax.step(js, cum_s * 100, where="post", color=GREY, lw=1.8, label="collisions")
    ax.step(js, cum_mt * 100, where="post", color=ORANGE, lw=2.0, label="momentum transfer")
    ax.set_xlim(-2, 54); ax.set_ylim(0, 102); ax.set_xlabel("final rotational level $j'$ (cumulative up to)")
    if k == 0: ax.set_ylabel("cumulative share (%)"); ax.legend(frameon=False, fontsize=8.5, loc="center right", bbox_to_anchor=(1.0, 0.45))
    j90 = int(js[np.argmax(cum_mt >= 0.9)])
    ax.axhline(90, color="#999999", lw=0.8, ls=":")
    ax.text(53, 6, f"90% of momentum transfer\nreached by $j'$ = {j90}", ha="right", va="bottom", fontsize=8.5)
fig.suptitle("H + CO$_2$: collisions by final rotational level of CO$_2$ (blue = elastic, orange = inelastic)", fontsize=12.5, y=0.98)
fig.savefig(prefix + "_by_level.png", dpi=200, bbox_inches="tight"); fig.savefig(prefix + "_by_level.pdf", bbox_inches="tight")
plt.close(fig)

# ---- figure 3: energy given to rotation against energy lost to recoil, per collision -------------------
fig, ax = plt.subplots(figsize=(6.4, 4.6))
x = np.arange(3); wd = 0.36
rot = np.array([r["mean_rot"] for r in res]) * 1000; rec = np.array([r["mean_recoil"] for r in res]) * 1000
b1 = ax.bar(x - wd / 2, rec, wd, color=BLUE, label="recoil (elastic kinematics, mean over all collisions)")
b2 = ax.bar(x + wd / 2, rot, wd, color=ORANGE, label="rotational excitation of CO$_2$")
for xi, v in zip(x - wd / 2, rec): ax.text(xi, v * 1.04, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
for xi, v in zip(x + wd / 2, rot): ax.text(xi, v * 1.04, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([f"{r['E']:g} eV" for r in res]); ax.set_ylabel("mean energy lost by the H atom per collision (meV)")
ax.set_ylim(0, max(rec.max(), rot.max()) * 1.25); ax.grid(axis="x", visible=False)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax.set_title("H + CO$_2$: energy per collision, rotation against recoil", fontsize=11, fontweight="bold")
fig.text(0.5, -0.02, "Rotation: $\\sum_{j'}\\sigma_{j'}\\,B\\,j'(j'+1)/\\sum_{j'}\\sigma_{j'}$ with $B\\approx0.39$ cm$^{-1}$. "
         "Recoil: $(f/2)\\langle1-\\cos\\theta\\rangle E_{lab}$, $f=0.0875$. Estimates.", ha="center", va="top", fontsize=8, color="#555555")
fig.savefig(prefix + "_energy_per_collision.png", dpi=200, bbox_inches="tight"); fig.savefig(prefix + "_energy_per_collision.pdf", bbox_inches="tight")
plt.close(fig)

print("wrote", prefix + "_overview/_by_level/_energy_per_collision (.png/.pdf) and", prefix + "_numbers.csv")
for r in res:
    js = np.array(r["js"]); mtv = np.array([r["mt"][j] for j in js]); cum = np.cumsum(mtv) / mtv.sum()
    print(f"{r['E']:>4g} eV: sum over levels / authors' total = {r['sig_sum']/r['tab_tot']:.3f}; elastic = {r['sig'][0]/r['sig_sum']:.1%} of collisions, "
          f"{r['mt'][0]/r['mt_sum']:.1%} of momentum transfer; 90% of momentum transfer by j' = {int(js[np.argmax(cum>=0.9)])}; "
          f"mean energy to rotation {r['mean_rot']*1000:.1f} meV per collision, mean recoil loss {r['mean_recoil']*1000:.1f} meV")
