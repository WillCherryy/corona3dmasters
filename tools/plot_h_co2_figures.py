#!/usr/bin/env python3
"""
H + CO2 elastic against inelastic collisions: figures made directly from the Bop and Gacesa (2026) files.
Needs only Python 3 with numpy and matplotlib.
Output: h_co2_ALL.png (everything in one picture), separate/<name>.png (13 pictures), h_co2_numbers.csv
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#444444"
A2_TO_CM2 = 1e-16
CM1_TO_EV = 1.0 / 8065.541
B_ROT_EV = 0.39022 * CM1_TO_EV
M_H, M_CO2 = 1.00794, 44.0095
F_RECOIL = 4 * M_H * M_CO2 / (M_H + M_CO2) ** 2
ENERGY_FILES = [("E0.10-DCS", 0.1), ("E1.00-DCS", 1.0), ("E5.00-DCS", 5.0)]

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})


def find_file(folder, stem, suffixes):
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file() and stem.lower() in p.name.lower() and p.suffix.lower() in suffixes:
            return p
    sys.exit(f"Could not find a file containing '{stem}' under {folder}")


def read_blocks(path):
    out, cur = {}, None
    for line in open(path):
        if line.startswith("#"):
            m = re.search(r"LEV\(F\),J\(F\) =\s*\d+\s+(\d+)", line)
            cur = int(m.group(1)); out[cur] = []
        elif line.strip():
            a, d = line.split()[:2]
            out[cur].append((float(a), float(d) * A2_TO_CM2))
    return {j: (np.array(v)[:, 0], np.array(v)[:, 1]) for j, v in out.items()}


def integrate(angle_deg, dcs, weight=None):
    th = np.radians(angle_deg)
    w = np.ones_like(th) if weight is None else weight(th)
    f = dcs * np.sin(th) * w
    body = np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(th))
    a, b = np.linalg.lstsq(np.vstack([np.ones(5), th[:5] ** 2]).T, dcs[:5], rcond=None)[0]
    tt = np.linspace(0, th[0], 2001)
    g = (a + b * tt ** 2) * np.sin(tt) * (np.ones_like(tt) if weight is None else weight(tt))
    return 2 * np.pi * (body + np.sum(0.5 * (g[1:] + g[:-1]) * np.diff(tt)))


def load_all(folder):
    cs_path = find_file(folder, "total_and_elastic_CS", {".out", ".txt", ".dat"})
    rows = [l.split() for l in open(cs_path).read().splitlines()[1:] if l.strip()]
    E_tab = np.array([float(r[0]) for r in rows]) * CM1_TO_EV
    S_tot = np.array([float(r[2]) for r in rows]) * A2_TO_CM2
    S_el = np.array([float(r[3]) for r in rows]) * A2_TO_CM2
    res = []
    for stem, e in ENERGY_FILES:
        blocks = read_blocks(find_file(folder, stem, {".txt", ".dat", ".out"}))
        js = sorted(blocks)
        ang = blocks[0][0]
        d_el = blocks[0][1]
        d_in = sum(blocks[j][1] for j in js if j > 0)
        sig = {j: integrate(ang, blocks[j][1]) for j in js}
        mt = {j: integrate(ang, blocks[j][1], lambda t: 1 - np.cos(t)) for j in js}
        sig_sum, mt_sum = sum(sig.values()), sum(mt.values())
        tab_tot, tab_el = np.interp(e, E_tab, S_tot), np.interp(e, E_tab, S_el)
        mean_rot = sum(sig[j] * B_ROT_EV * j * (j + 1) for j in js) / sig_sum
        mean_recoil = 0.5 * F_RECOIL * (mt_sum / sig_sum) * e * (M_H + M_CO2) / M_CO2
        cum = np.cumsum([mt[j] for j in js]) / mt_sum
        res.append(dict(E=e, js=np.array(js), ang=ang, d_el=d_el, d_in=d_in, d_tot=d_el + d_in, sig=sig, mt=mt,
                        sig_sum=sig_sum, mt_sum=mt_sum, tab_tot=tab_tot, tab_el=tab_el,
                        mean_rot=mean_rot, mean_recoil=mean_recoil, j90=int(js[int(np.argmax(cum >= 0.9))]),
                        cum_mt=cum, cum_sig=np.cumsum([sig[j] for j in js]) / sig_sum))
    return E_tab, S_tot, S_el, res


def panel_dcs(ax, r, legend=False, ylabel=True):
    lo = np.min(r["d_tot"][r["d_tot"] > 0]) * 0.5
    me, mi = r["d_el"] > lo, r["d_in"] > lo
    ax.plot(r["ang"], r["d_tot"], color=GREY, lw=1.6, ls="--", label="total (sum of all $j'$)")
    ax.plot(r["ang"][me], r["d_el"][me], color=BLUE, lw=2.0, label="elastic ($j'=0$)")
    ax.plot(r["ang"][mi], r["d_in"][mi], color=ORANGE, lw=2.0, label="inelastic (sum of $j'>0$)")
    ax.axvline(2.0, color="#999999", lw=0.9, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.1, 180); ax.set_ylim(lo, r["d_tot"].max() * 3)
    ax.set_xticks([0.1, 1, 10, 100]); ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.set_xlabel("scattering angle (degrees)")
    if ylabel:
        ax.set_ylabel(r"$d\sigma/d\Omega$ (cm$^2$ sr$^{-1}$)")
    ax.set_title(f"Angle distribution at {r['E']:g} eV", fontsize=11, fontweight="bold")
    ax.text(2.2, r["d_tot"].max() * 1.6, r"$2^\circ$", color="#777777", fontsize=8.5, va="top")
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="upper right")


def panel_xsec(ax, E_tab, S_tot, S_el, res):
    ax.loglog(E_tab, S_tot, color=GREY, lw=1.6, ls="--", label="total")
    ax.loglog(E_tab, S_el, color=BLUE, lw=2.0, label="elastic")
    ax.loglog(E_tab, S_tot - S_el, color=ORANGE, lw=2.0, label="inelastic (total $-$ elastic)")
    for r in res:
        ax.axvline(r["E"], color="#999999", lw=0.8, ls=":")
    ax.set_xlabel("collision energy (eV)"); ax.set_ylabel(r"cross section (cm$^2$)")
    ax.set_title("Cross sections against energy", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5)


def _share_bars(ax, el_pct, ylabel, title, legend):
    x = np.arange(len(el_pct))
    ax.bar(x, el_pct, color=BLUE, width=0.6, label="elastic")
    ax.bar(x, 100 - el_pct, bottom=el_pct, color=ORANGE, width=0.6, label="inelastic")
    for i, v in enumerate(el_pct):
        if v > 12:
            ax.text(i, v / 2, f"{v:.0f}%", ha="center", va="center", color="white", fontweight="bold")
        else:
            ax.text(i, v + 3.5, f"{v:.1f}%", ha="center", va="bottom", color=BLUE, fontweight="bold", fontsize=9)
        ax.text(i, v + (100 - v) / 2 if v <= 88 else 100 - 4, f"{100 - v:.0f}%", ha="center", va="center",
                color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(["0.1 eV", "1 eV", "5 eV"]); ax.set_ylim(0, 100); ax.grid(False)
    ax.set_ylabel(ylabel); ax.set_title(title, fontsize=11, fontweight="bold")
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)


def panel_share_collisions(ax, res, legend=True):
    el = np.array([r["tab_el"] / r["tab_tot"] for r in res]) * 100
    _share_bars(ax, el, "share of all collisions (%)", "How often (collisions)", legend)


def panel_share_momentum(ax, res, legend=False):
    el = np.array([r["mt"][0] / r["mt_sum"] for r in res]) * 100
    _share_bars(ax, el, "share of momentum transfer (%)", "How much deflection (momentum transfer)", legend)


def panel_levels_bar(ax, r, ylabel=True):
    s = np.clip(np.array([r["sig"][j] for j in r["js"]]), 1e-25, None)
    ax.bar(r["js"], s, width=1.7, color=[BLUE if j == 0 else ORANGE for j in r["js"]])
    ax.set_yscale("log"); ax.set_xlim(-2, 54); ax.set_ylim(s.min() * 0.5, s.max() * 2.5)
    ax.set_xlabel("final rotational level $j'$")
    if ylabel:
        ax.set_ylabel(r"cross section $\sigma_{j'}$ (cm$^2$)")
    ax.set_title(f"Cross section by final level at {r['E']:g} eV", fontsize=11, fontweight="bold")
    ax.text(0.97, 0.93, f"elastic: {s[0] / s.sum():.0%} of collisions\n$j'=2$: {s[1] / s.sum():.0%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=9)


def panel_levels_cum(ax, r, legend=False, ylabel=True):
    ax.step(r["js"], r["cum_sig"] * 100, where="post", color=GREY, lw=1.8, label="collisions")
    ax.step(r["js"], r["cum_mt"] * 100, where="post", color=ORANGE, lw=2.0, label="momentum transfer")
    ax.axhline(90, color="#999999", lw=0.8, ls=":")
    ax.set_xlim(-2, 54); ax.set_ylim(0, 102); ax.set_xlabel("final rotational level $j'$ (cumulative up to)")
    if ylabel:
        ax.set_ylabel("cumulative share (%)")
    ax.set_title(f"Cumulative share at {r['E']:g} eV", fontsize=11, fontweight="bold")
    ax.text(53, 6, f"90% of momentum transfer\nreached by $j'$ = {r['j90']}", ha="right", va="bottom", fontsize=8.5)
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="center right", bbox_to_anchor=(1.0, 0.45))


def panel_energy(ax, res):
    x = np.arange(len(res)); wd = 0.36
    rot = np.array([r["mean_rot"] for r in res]) * 1000
    rec = np.array([r["mean_recoil"] for r in res]) * 1000
    ax.bar(x - wd / 2, rec, wd, color=BLUE, label="recoil (elastic kinematics)")
    ax.bar(x + wd / 2, rot, wd, color=ORANGE, label="rotational excitation of CO$_2$")
    for xi, v in zip(x - wd / 2, rec):
        ax.text(xi, v * 1.03, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    for xi, v in zip(x + wd / 2, rot):
        ax.text(xi, v * 1.03, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([f"{r['E']:g} eV" for r in res])
    ax.set_ylabel("mean energy lost per collision (meV)"); ax.set_ylim(0, max(rec.max(), rot.max()) * 1.3)
    ax.grid(axis="x", visible=False); ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("Energy per collision: rotation against recoil", fontsize=11, fontweight="bold")


def panel_table(ax, res):
    ax.axis("off")
    lines = ["Key numbers (own calculation from the raw files)", ""]
    lines.append(f"{'energy':>8}  {'elastic share of':>29}  {'90% of momentum':>16}  {'rotation / recoil':>18}")
    lines.append(f"{'':>8}  {'collisions':>12} {'momentum':>12}  {'reached by j':>16}  {'(meV per collision)':>18}")
    for r in res:
        lines.append(f"{r['E']:>6g}eV  {r['sig'][0] / r['sig_sum']:>11.1%} {r['mt'][0] / r['mt_sum']:>12.1%}  "
                     f"{r['j90']:>16d}  {r['mean_rot'] * 1000:>8.1f} / {r['mean_recoil'] * 1000:<8.1f}")
    lines += ["", "Inelastic = rotationally inelastic, sum over final levels j' = 2 to 52 (CO2 initially in j = 0).",
              "Momentum transfer = 2 pi int (1 - cos theta) (d sigma / d Omega) sin theta d theta.",
              "Rotation: sum_j' sigma_j' B j'(j'+1) / sum sigma_j', B = 0.39 cm-1 (approx.).",
              "Recoil: (f/2) <1 - cos theta> E_lab, f = 0.0875. Both are estimates."]
    ax.text(0.0, 1.0, "\n".join(lines), transform=ax.transAxes, va="top", ha="left", family="monospace", fontsize=8.6)


def save(fig, path, pdf):
    fig.savefig(str(path) + ".png", dpi=200, bbox_inches="tight")
    if pdf:
        fig.savefig(str(path) + ".pdf", bbox_inches="tight")
    plt.close(fig)


def make_combined(out, E_tab, S_tot, S_el, res, pdf):
    fig = plt.figure(figsize=(14, 22))
    gs = fig.add_gridspec(5, 3, hspace=0.55, wspace=0.3, top=0.955)
    for k, r in enumerate(res):
        panel_dcs(fig.add_subplot(gs[0, k]), r, legend=(k == 0), ylabel=(k == 0))
    panel_xsec(fig.add_subplot(gs[1, 0]), E_tab, S_tot, S_el, res)
    panel_share_collisions(fig.add_subplot(gs[1, 1]), res)
    panel_share_momentum(fig.add_subplot(gs[1, 2]), res)
    for k, r in enumerate(res):
        panel_levels_bar(fig.add_subplot(gs[2, k]), r, ylabel=(k == 0))
    for k, r in enumerate(res):
        panel_levels_cum(fig.add_subplot(gs[3, k]), r, legend=(k == 0), ylabel=(k == 0))
    panel_energy(fig.add_subplot(gs[4, 0]), res)
    panel_table(fig.add_subplot(gs[4, 1:]), res)
    fig.suptitle("H + CO$_2$: elastic against rotationally inelastic collisions "
                 "(Bop and Gacesa 2026 data, CO$_2$ initially in $j=0$)", fontsize=14, y=0.985)
    save(fig, out / "h_co2_ALL", pdf)


def make_separate(out, E_tab, S_tot, S_el, res, pdf):
    sep = out / "separate"
    sep.mkdir(parents=True, exist_ok=True)
    names = []

    def one(name, draw, size=(6.4, 4.8)):
        fig, ax = plt.subplots(figsize=size)
        draw(ax)
        save(fig, sep / name, pdf)
        names.append(name)

    for r in res:
        one(f"01_angle_distribution_{r['E']:g}eV", lambda ax, r=r: panel_dcs(ax, r, legend=True))
    one("02_cross_sections_vs_energy", lambda ax: panel_xsec(ax, E_tab, S_tot, S_el, res))
    one("03_share_of_collisions", lambda ax: panel_share_collisions(ax, res))
    one("04_share_of_momentum_transfer", lambda ax: panel_share_momentum(ax, res, legend=True))
    for r in res:
        one(f"05_cross_section_by_level_{r['E']:g}eV", lambda ax, r=r: panel_levels_bar(ax, r))
    for r in res:
        one(f"06_cumulative_share_{r['E']:g}eV", lambda ax, r=r: panel_levels_cum(ax, r, legend=True))
    one("07_energy_per_collision", lambda ax: panel_energy(ax, res))
    return names


def write_numbers(out, res):
    with open(out / "h_co2_numbers.csv", "w") as f:
        f.write("E_eV,sigma_elastic_table_cm2,sigma_total_table_cm2,sum_of_levels_cm2,sum_over_total_table,"
                "elastic_share_collisions,elastic_share_momentum,mean_1-cos,j_for_90pct_momentum,"
                "mean_rotational_energy_meV,mean_recoil_energy_meV\n")
        for r in res:
            f.write(f"{r['E']},{r['tab_el']:.4e},{r['tab_tot']:.4e},{r['sig_sum']:.4e},{r['sig_sum'] / r['tab_tot']:.4f},"
                    f"{r['sig'][0] / r['sig_sum']:.4f},{r['mt'][0] / r['mt_sum']:.4f},{r['mt_sum'] / r['sig_sum']:.4f},"
                    f"{r['j90']},{r['mean_rot'] * 1000:.3f},{r['mean_recoil'] * 1000:.3f}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=".", help="folder containing (or above) the raw files")
    ap.add_argument("--out", default="h_co2_figures", help="output folder")
    ap.add_argument("--mode", choices=["all", "combined", "separate"], default="all",
                    help="combined = one PNG with every panel; separate = one PNG per panel; all = both (default)")
    ap.add_argument("--pdf", action="store_true", help="also write PDF versions")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    E_tab, S_tot, S_el, res = load_all(a.data)
    write_numbers(out, res)
    if a.mode in ("all", "combined"):
        make_combined(out, E_tab, S_tot, S_el, res, a.pdf)
        print("wrote", out / "h_co2_ALL.png")
    if a.mode in ("all", "separate"):
        names = make_separate(out, E_tab, S_tot, S_el, res, a.pdf)
        print(f"wrote {len(names)} separate figures in", out / "separate")
    print("wrote", out / "h_co2_numbers.csv")
    for r in res:
        print(f"{r['E']:>4g} eV: elastic {r['sig'][0] / r['sig_sum']:.1%} of collisions, "
              f"{r['mt'][0] / r['mt_sum']:.1%} of momentum transfer; 90% of momentum transfer by j' = {r['j90']}; "
              f"rotation {r['mean_rot'] * 1000:.1f} meV against recoil {r['mean_recoil'] * 1000:.1f} meV per collision")


if __name__ == "__main__":
    main()