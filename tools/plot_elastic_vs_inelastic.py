#!/usr/bin/env python3
"""Elastic against inelastic H + CO2 collisions at 0.1, 1 and 5 eV.

Reads the converted files in src/inputs/collisions/H-CO2 (summed over final rotational levels = "total",
and the elastic-only files = final level j' = 0), and writes a figure and a table of the numbers.

Inelastic = total minus elastic. Cross sections as a function of energy use the authors' own total and
elastic tables; the angle distributions use the files summed over final levels j' = 0, 2, ..., 52
(the supplied data stop at j' = 52, which makes the summed integral about 3 to 4 per cent smaller than the
authors' total at 4 to 5 eV).

Usage: python3 plot_elastic_vs_inelastic.py [path to src/inputs/collisions/H-CO2] [output prefix]
"""
import sys, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = sys.argv[1] if len(sys.argv) > 1 else "src/inputs/collisions/H-CO2"
out = sys.argv[2] if len(sys.argv) > 2 else "docs/figures/h_co2_elastic_vs_inelastic"
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#444444"
ENERGIES = [("0.1", 0.1), ("1", 1.0), ("5", 5.0)]


def load(path):
    rows = []
    for line in open(path):
        if line[:1].isdigit():
            rows.append([float(x) for x in line.split(",")[:2]])
    return np.array(rows)


sig_tot = load(os.path.join(base, "total_cross_section_H_CO2.csv"))
sig_el = load(os.path.join(base, "elastic_only", "total_cross_section_H_CO2_elastic.csv"))
dcs = {}
for tag, e in ENERGIES:
    tot = load(os.path.join(base, f"diff_cross_section_H_CO2_{tag}eV.csv"))
    el = load(os.path.join(base, "elastic_only", f"diff_cross_section_H_CO2_elastic_{tag}eV.csv"))
    assert np.allclose(tot[:, 0], el[:, 0])
    dcs[tag] = (tot[:, 0], el[:, 1], tot[:, 1] - el[:, 1], tot[:, 1])   # angle, elastic, inelastic, total

# ---- numbers -------------------------------------------------------------------------------------------
table = []
for tag, e in ENERGIES:
    ang, d_el, d_in, d_tot = dcs[tag]
    th = np.radians(ang)
    w = np.sin(th)
    # uniform angle grid: sums are proportional to the angle integrals
    s_el_dcs = np.sum(d_el * w); s_in_dcs = np.sum(d_in * w)
    mt_el = np.sum(d_el * w * (1 - np.cos(th))); mt_in = np.sum(d_in * w * (1 - np.cos(th)))
    el_tab = np.interp(e, sig_el[:, 0], sig_el[:, 1]); tot_tab = np.interp(e, sig_tot[:, 0], sig_tot[:, 1])
    table.append(dict(E=e,
                      sigma_el=el_tab, sigma_tot=tot_tab, sigma_in=tot_tab - el_tab,
                      frac_el_collisions=el_tab / tot_tab,
                      frac_el_momentum=mt_el / (mt_el + mt_in),
                      mean_1mcos_el=mt_el / s_el_dcs, mean_1mcos_in=mt_in / s_in_dcs,
                      mean_1mcos_tot=(mt_el + mt_in) / (s_el_dcs + s_in_dcs)))

with open(out + "_numbers.csv", "w") as f:
    f.write("E_eV,sigma_elastic_cm2,sigma_total_cm2,sigma_inelastic_cm2,elastic_share_of_collisions,"
            "elastic_share_of_momentum_transfer,mean_1-cos_elastic,mean_1-cos_inelastic,mean_1-cos_total\n")
    for r in table:
        f.write(f"{r['E']},{r['sigma_el']:.4e},{r['sigma_tot']:.4e},{r['sigma_in']:.4e},"
                f"{r['frac_el_collisions']:.4f},{r['frac_el_momentum']:.4f},"
                f"{r['mean_1mcos_el']:.4f},{r['mean_1mcos_in']:.4f},{r['mean_1mcos_tot']:.4f}\n")

# ---- figure --------------------------------------------------------------------------------------------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 100})
fig = plt.figure(figsize=(13, 8.2))
gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.28, top=0.88)

# top row: differential cross sections (log angle axis: the forward peak is only a few degrees wide)
for k, (tag, e) in enumerate(ENERGIES):
    ax = fig.add_subplot(gs[0, k])
    ang, d_el, d_in, d_tot = dcs[tag]
    lo = np.min(d_tot[d_tot > 0]) * 0.5
    mask_el = d_el > lo
    mask_in = d_in > lo
    l_tot, = ax.plot(ang, d_tot, color=GREY, lw=1.6, ls="--")
    l_el, = ax.plot(ang[mask_el], d_el[mask_el], color=BLUE, lw=2.0)
    l_in, = ax.plot(ang[mask_in], d_in[mask_in], color=ORANGE, lw=2.0)
    ax.axvline(2.0, color="#999999", lw=0.9, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.1, 180); ax.set_ylim(lo, d_tot.max() * 3)
    ax.set_xticks([0.1, 1, 10, 100]); ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.set_xlabel("scattering angle (degrees)")
    if k == 0:
        ax.set_ylabel(r"$d\sigma/d\Omega$ (cm$^2$ sr$^{-1}$)")
        handles = [l_el, l_in, l_tot]
    ax.set_title(f"{e:g} eV", fontsize=11, fontweight="bold")
    ax.text(2.2, d_tot.max() * 1.6, r"$2^\circ$", color="#777777", fontsize=8.5, va="top")
fig.legend(handles, ["elastic ($j'=0$)", "inelastic (all $j'>0$)", "total (all final states)"],
           loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=3, frameon=False, fontsize=10)

# bottom-left: cross sections against energy (authors' tables)
ax = fig.add_subplot(gs[1, 0])
inel = np.interp(sig_tot[:, 0], sig_el[:, 0], sig_el[:, 1])
ax.loglog(sig_tot[:, 0], sig_tot[:, 1], color=GREY, lw=1.6, ls="--", label="total")
ax.loglog(sig_el[:, 0], sig_el[:, 1], color=BLUE, lw=2.0, label="elastic")
ax.loglog(sig_tot[:, 0], sig_tot[:, 1] - inel, color=ORANGE, lw=2.0, label="inelastic (total $-$ elastic)")
for r in table:
    ax.axvline(r["E"], color="#999999", lw=0.8, ls=":")
ax.set_xlabel("collision energy (eV)"); ax.set_ylabel(r"cross section (cm$^2$)")
ax.set_title("Cross sections", fontsize=11, fontweight="bold")
ax.legend(frameon=False, fontsize=8.5)

# bottom-middle: share of collisions
labels = [f"{r['E']:g} eV" for r in table]
x = np.arange(len(table))
ax = fig.add_subplot(gs[1, 1])
el_c = np.array([r["frac_el_collisions"] for r in table]) * 100
ax.bar(x, el_c, color=BLUE, label="elastic", width=0.6)
ax.bar(x, 100 - el_c, bottom=el_c, color=ORANGE, label="inelastic", width=0.6)
for i, v in enumerate(el_c):
    ax.text(i, v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
    ax.text(i, v + (100 - v) / 2, f"{100 - v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 100); ax.grid(False)
ax.set_ylabel("share of all collisions (%)")
ax.set_title("How often", fontsize=11, fontweight="bold")
ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

# bottom-right: share of momentum transfer
ax = fig.add_subplot(gs[1, 2])
el_m = np.array([r["frac_el_momentum"] for r in table]) * 100
ax.bar(x, el_m, color=BLUE, width=0.6)
ax.bar(x, 100 - el_m, bottom=el_m, color=ORANGE, width=0.6)
for i, v in enumerate(el_m):
    ax.text(i, 100 - (100 - v) / 2, f"{100 - v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
    ax.text(i, min(v, 100) + 3.5, f"{v:.1f}%", ha="center", va="bottom", color=BLUE, fontweight="bold", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 112); ax.set_yticks([0, 25, 50, 75, 100]); ax.grid(False)
ax.set_ylabel("share of momentum transfer (%)")
ax.set_title("How much deflection", fontsize=11, fontweight="bold")

fig.suptitle("H + CO$_2$: elastic against rotationally inelastic collisions "
             "(Bop and Gacesa 2026 data, CO$_2$ initially in $j=0$)", fontsize=12.5, y=1.025)
fig.text(0.5, -0.015,
         "Inelastic = total minus elastic. Momentum transfer: $\\sigma_{mt}=2\\pi\\int(1-\\cos\\theta)\\,(d\\sigma/d\\Omega)\\sin\\theta\\,d\\theta$, "
         "from the angle distributions summed over final levels $j'=0$ to 52.\n"
         "The data stop at $j'=52$, so the inelastic part is about 3 to 4 per cent low at 4 to 5 eV. "
         "Dotted line: $2^\\circ$, the edge of the forward peak.",
         ha="center", va="top", fontsize=8.5, color="#555555")
fig.savefig(out + ".png", dpi=200, bbox_inches="tight")
fig.savefig(out + ".pdf", bbox_inches="tight")
print("wrote", out + ".png", out + ".pdf", out + "_numbers.csv")
for r in table:
    print(f"{r['E']:>4g} eV: elastic {r['frac_el_collisions']:.1%} of collisions, but {r['frac_el_momentum']:.1%} of momentum transfer; "
          f"mean(1-cos): elastic {r['mean_1mcos_el']:.4f}, inelastic {r['mean_1mcos_in']:.3f}, total {r['mean_1mcos_tot']:.3f}")
