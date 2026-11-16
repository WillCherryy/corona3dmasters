"""H + CO2 elastic against inelastic collisions: figures from the Bop and Gacesa (2026) files. Needs numpy and matplotlib."""
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
JMAX_FILES = 52

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25})

def find_file(folder, stem, suffixes, required=True):
    for p in sorted(Path(folder).rglob("*")):
        if p.is_file() and stem.lower() in p.name.lower() and p.suffix.lower() in suffixes:
            return p
    if required:
        sys.exit(f"Could not find a file containing '{stem}' under {folder}")
    return None

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

def read_state_to_state(path, energies_ev):
    targets = {e: e / CM1_TO_EV for e in energies_ev}
    out = {e: {} for e in energies_ev}
    for line in open(path):
        if line.startswith("#"):
            continue
        a = line.split()
        if int(a[2]) != 0:
            continue
        E = float(a[0])
        for e, t in targets.items():
            if abs(E - t) < 0.02:
                out[e][2 * int(a[1])] = float(a[3]) * A2_TO_CM2
    return out

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
    s2s_path = find_file(folder, "state-to-state", {".res"}, required=False)
    s2s = read_state_to_state(s2s_path, [e for _, e in ENERGY_FILES]) if s2s_path else None
    if s2s is None:
        print("WARNING: H-CO2_state-to-state_CS.res not found: levels above j' = 52 are missing, so the 5 eV cross-section "
              "shares, rotational energy and momentum transfer are incomplete.", file=sys.stderr)
    res = []
    for stem, e in ENERGY_FILES:
        blocks = read_blocks(find_file(folder, stem, {".txt", ".dat", ".out"}))
        js = sorted(blocks)
        ang = blocks[0][0]
        d_el = blocks[0][1]
        d_in = sum(blocks[j][1] for j in js if j > 0)
        sig_dcs = {j: integrate(ang, blocks[j][1]) for j in js}
        mt = {j: integrate(ang, blocks[j][1], lambda t: 1 - np.cos(t)) for j in js}
        tab_tot, tab_el = float(np.interp(e, E_tab, S_tot)), float(np.interp(e, E_tab, S_el))

        sig_all = dict(s2s[e]) if s2s is not None else dict(sig_dcs)
        levels = np.array(sorted(sig_all))
        sig_lv = np.array([sig_all[j] for j in levels])
        sig_total_levels = float(sig_lv.sum())
        sig_52 = float(sum(sig_all[j] for j in levels if j <= JMAX_FILES))
        missing = max(sig_total_levels - sig_52, 0.0)

        m1 = {j: mt[j] / sig_dcs[j] for j in js if sig_dcs[j] > 1e-4 * sig_dcs[0]}
        top = sorted(m1)[-5:]
        c_mid = float(np.mean([m1[j] for j in top])) if missing > 0.001 * sig_total_levels else 0.0
        mt52 = sum(mt.values())
        mt_tot = {k: mt52 + missing * c for k, c in (("lo", 0.5 * c_mid), ("mid", c_mid), ("hi", 1.5 * c_mid))}
        e_lab = e * (M_H + M_CO2) / M_CO2
        recoil = {k: 0.5 * F_RECOIL * (mt_tot[k] / sig_total_levels) * e_lab for k in mt_tot}
        mean_rot = float(sum(sig_all[j] * B_ROT_EV * j * (j + 1) for j in levels) / sig_total_levels)
        cum_mt = np.cumsum([mt[j] for j in js]) / mt_tot["mid"]
        reached = np.where(cum_mt >= 0.9)[0]
        res.append(dict(E=e, js=np.array(js), ang=ang, d_el=d_el, d_in=d_in, d_tot=d_el + d_in,
                        sig_dcs=sig_dcs, mt=mt, levels=levels, sig_lv=sig_lv, sig_total_levels=sig_total_levels,
                        tab_tot=tab_tot, tab_el=tab_el, missing=missing, missing_frac=missing / sig_total_levels, c_mid=c_mid,
                        share_el_coll=tab_el / tab_tot,
                        share_el_mt={k: mt[0] / mt_tot[k] for k in mt_tot}, mt_tot=mt_tot,
                        mean_rot=mean_rot, recoil=recoil,
                        j90=(int(js[reached[0]]) if len(reached) else None),
                        cum_mt=cum_mt, cum_sig=np.cumsum(sig_lv) / sig_total_levels,
                        has_s2s=s2s is not None,
                        dev_dcs_vs_s2s=(max(abs(sig_dcs[j] / sig_all[j] - 1) for j in js if j in sig_all and sig_all[j] > 1e-4 * sig_all[0])
                                        if s2s is not None else float("nan"))))
    return E_tab, S_tot, S_el, res

def panel_dcs(ax, r, legend=False, ylabel=True):
    lo = np.min(r["d_tot"][r["d_tot"] > 0]) * 0.5
    me, mi = r["d_el"] > lo, r["d_in"] > lo
    ax.plot(r["ang"], r["d_tot"], color=GREY, lw=1.6, ls="--", label="total (sum of $j'\\leq52$)")
    ax.plot(r["ang"][me], r["d_el"][me], color=BLUE, lw=2.0, label="elastic ($j'=0$)")
    ax.plot(r["ang"][mi], r["d_in"][mi], color=ORANGE, lw=2.0, label="inelastic (sum of $2\\leq j'\\leq52$)")
    ax.axvline(2.0, color="#999999", lw=0.9, ls=":")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(0.1, 180); ax.set_ylim(lo, r["d_tot"].max() * 3)
    ax.set_xticks([0.1, 1, 10, 100]); ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.set_xlabel("scattering angle (degrees)")
    if ylabel:
        ax.set_ylabel(r"$d\sigma/d\Omega$ (cm$^2$ sr$^{-1}$)")
    ax.set_title(f"Angle distribution at {r['E']:g} eV", fontsize=11, fontweight="bold")
    ax.text(2.2, r["d_tot"].max() * 1.6, r"$2^\circ$", color="#777777", fontsize=8.5, va="top")
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="center left", bbox_to_anchor=(0.02, 0.58))

def panel_xsec(ax, E_tab, S_tot, S_el, res):
    ax.loglog(E_tab, S_tot, color=GREY, lw=1.6, ls="--", label="total")
    ax.loglog(E_tab, S_el, color=BLUE, lw=2.0, label="elastic")
    ax.loglog(E_tab, S_tot - S_el, color=ORANGE, lw=2.0, label="inelastic (total $-$ elastic)")
    for r in res:
        ax.axvline(r["E"], color="#999999", lw=0.8, ls=":")
    ax.set_xlabel("collision energy (eV)"); ax.set_ylabel(r"cross section (cm$^2$)")
    ax.set_title("Cross sections against energy", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5)

def _share_bars(ax, el_pct, ylabel, title, legend, flags=None):
    x = np.arange(len(el_pct))
    ax.bar(x, el_pct, color=BLUE, width=0.6, label="elastic")
    ax.bar(x, 100 - el_pct, bottom=el_pct, color=ORANGE, width=0.6, label="inelastic")
    for i, v in enumerate(el_pct):
        star = "*" if flags is not None and flags[i] else ""
        if v > 12:
            ax.text(i, v / 2, f"{v:.0f}%{star}", ha="center", va="center", color="white", fontweight="bold")
        else:
            ax.text(i, v + 3.5, f"{v:.1f}%{star}", ha="center", va="bottom", color=BLUE, fontweight="bold", fontsize=9)
        ax.text(i, v + (100 - v) / 2 if v <= 88 else 100 - 4, f"{100 - v:.0f}%", ha="center", va="center",
                color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(["0.1 eV", "1 eV", "5 eV"]); ax.set_ylim(0, 100); ax.grid(False)
    ax.set_ylabel(ylabel); ax.set_title(title, fontsize=11, fontweight="bold")
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

def panel_share_collisions(ax, res, legend=True):
    el = np.array([r["share_el_coll"] for r in res]) * 100
    _share_bars(ax, el, "share of all collisions (%)", "How often (collisions)", legend)

def panel_share_momentum(ax, res, legend=False):
    el = np.array([r["share_el_mt"]["mid"] for r in res]) * 100
    flags = [r["missing_frac"] > 0.005 for r in res]
    _share_bars(ax, el, "share of momentum transfer (%)", "How much deflection (momentum transfer)", legend, flags)
    if any(flags):
        r5 = [r for r in res if r["missing_frac"] > 0.005][-1]
        ax.text(0.5, -0.2, f"* {r5['E']:g} eV: levels above $j'=52$ ({r5['missing_frac']:.1%} of collisions) are not in the angle files;\n"
                f"momentum transfer estimated, elastic share {r5['share_el_mt']['hi']:.1%} to {r5['share_el_mt']['lo']:.1%}",
                transform=ax.transAxes, ha="center", va="top", fontsize=8, color="#555555")

def panel_levels_bar(ax, r, ylabel=True):
    keep = r["sig_lv"] > 1e-8 * r["sig_lv"][0]
    lv, s = r["levels"][keep], r["sig_lv"][keep]
    ax.bar(lv, s, width=1.7, color=[BLUE if j == 0 else ORANGE for j in lv])
    ax.set_yscale("log"); ax.set_xlim(-2, lv.max() + 2); ax.set_ylim(s.min() * 0.5, s.max() * 2.5)
    ax.set_xlabel("final rotational level $j'$")
    if ylabel:
        ax.set_ylabel(r"cross section $\sigma_{j'}$ (cm$^2$)")
    ax.set_title(f"Cross section by final level at {r['E']:g} eV", fontsize=11, fontweight="bold")
    tot = r["sig_total_levels"]
    ax.text(0.97, 0.93, f"elastic: {r['sig_lv'][0] / tot:.1%} of all collisions\n$j'=2$: {r['sig_lv'][1] / tot:.1%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=9)

def panel_levels_cum(ax, r, legend=False, ylabel=True):
    ax.step(r["levels"], r["cum_sig"] * 100, where="post", color=GREY, lw=1.8, label="collisions")
    ax.step(r["js"], r["cum_mt"] * 100, where="post", color=ORANGE, lw=2.0, label="momentum transfer")
    if r["missing"] > 0:
        hi_lv = r["levels"][r["levels"] > JMAX_FILES]
        est = np.cumsum(r["sig_lv"][r["levels"] > JMAX_FILES] * r["c_mid"]) / r["mt_tot"]["mid"] + r["cum_mt"][-1]
        ax.step(np.r_[JMAX_FILES, hi_lv], np.r_[r["cum_mt"][-1], est] * 100, where="post", color=ORANGE, lw=2.0, ls="--",
                label="momentum transfer (estimated)")
    ax.axhline(90, color="#999999", lw=0.8, ls=":")
    ax.set_xlim(-2, r["levels"].max() + 2); ax.set_ylim(0, 102)
    ax.set_xlabel("final rotational level $j'$ (cumulative up to)")
    if ylabel:
        ax.set_ylabel("cumulative share (%)")
    ax.set_title(f"Cumulative share at {r['E']:g} eV", fontsize=11, fontweight="bold")
    if r["j90"] is not None:
        note = f"90% of momentum transfer\nreached by $j'$ = {r['j90']}"
    else:
        note = (f"momentum transfer: {r['cum_mt'][-1] * 100:.0f}% reached by $j'=52$;\nthe rest is in levels above 52 "
                f"(estimate:\nmean $1-\\cos\\theta$ = {r['c_mid']:.2f} there)")
    ax.text(0.97, 0.05, note, transform=ax.transAxes, ha="right", va="bottom", fontsize=8.3)
    if legend:
        ax.legend(frameon=False, fontsize=8.5, loc="center right", bbox_to_anchor=(1.0, 0.45))

def panel_energy(ax, res):
    x = np.arange(len(res)); wd = 0.36
    rot = np.array([r["mean_rot"] for r in res]) * 1000
    rec = np.array([r["recoil"]["mid"] for r in res]) * 1000
    lo = np.array([r["recoil"]["lo"] for r in res]) * 1000
    hi = np.array([r["recoil"]["hi"] for r in res]) * 1000
    ax.bar(x - wd / 2, rec, wd, color=BLUE, label="recoil (elastic kinematics)",
           yerr=[rec - lo, hi - rec], error_kw=dict(ecolor="#222222", lw=1, capsize=3))
    ax.bar(x + wd / 2, rot, wd, color=ORANGE, label="rotational excitation of CO$_2$")
    for xi, v, h in zip(x - wd / 2, rec, hi):
        ax.text(xi + 0.03, h * 1.03 + 0.2, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    for xi, v in zip(x + wd / 2, rot):
        ax.text(xi, v * 1.03 + 0.2, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([f"{r['E']:g} eV" for r in res])
    ax.set_ylabel("mean energy lost per collision (meV)"); ax.set_ylim(0, max(hi.max(), rot.max()) * 1.3)
    ax.grid(axis="x", visible=False); ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("Energy per collision: rotation against recoil", fontsize=11, fontweight="bold")

def panel_table(ax, res):
    ax.axis("off")
    lines = ["Key numbers (own calculation from the raw files)", ""]
    lines.append(f"{'energy':>8}  {'elastic share of':>27}  {'90% of momentum':>16}  {'rotation / recoil':>18}")
    lines.append(f"{'':>8}  {'collisions':>12} {'momentum':>12}  {'reached by j':>16}  {'(meV per collision)':>18}")
    for r in res:
        j90 = f"{r['j90']}" if r["j90"] is not None else ">52"
        star = "*" if r["missing_frac"] > 0.005 else " "
        lines.append(f"{r['E']:>6g}eV  {r['share_el_coll']:>11.1%} {r['share_el_mt']['mid']:>11.1%}{star}  "
                     f"{j90:>16}  {r['mean_rot'] * 1000:>8.1f} / {r['recoil']['mid'] * 1000:<8.1f}")
    lines += ["", "* the angle files stop at j' = 52; at 5 eV the levels above hold "
              f"{res[-1]['missing_frac']:.1%} of the collisions.",
              "  Their momentum transfer is estimated (mean 1-cos theta of the top levels present, range 0.5x to 1.5x).",
              "Elastic share of collisions: authors' elastic / total tables (every level).",
              "Rotation: sum_j' sigma_j' B j'(j'+1) / sum sigma_j' over every level, B = 0.39 cm-1 (approx.).",
              "Recoil: (f/2) <1 - cos theta> E_lab, f = 0.0875 (bar: range of the estimate). Both are estimates."]
    ax.text(0.0, 1.0, "\n".join(lines), transform=ax.transAxes, va="top", ha="left", family="monospace", fontsize=8.4)

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

def make_summary(out, E_tab, S_tot, S_el, res, pdf):
    fig = plt.figure(figsize=(15.5, 9.6))
    gs = fig.add_gridspec(2, 3, hspace=0.5, wspace=0.32)
    panel_xsec(fig.add_subplot(gs[0, 0]), E_tab, S_tot, S_el, res)
    panel_share_collisions(fig.add_subplot(gs[0, 1]), res)
    panel_share_momentum(fig.add_subplot(gs[0, 2]), res)
    for k, r in enumerate(res):
        panel_levels_bar(fig.add_subplot(gs[1, k]), r, ylabel=(k == 0))
    fig.suptitle("H + CO$_2$: elastic against rotationally inelastic collisions "
                 "(Bop and Gacesa 2026 data, CO$_2$ initially in $j=0$)", fontsize=12.5, y=0.97)
    save(fig, out / "h_co2_SUMMARY", pdf)

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
        f.write("E_eV,sigma_elastic_table_cm2,sigma_total_table_cm2,sum_over_all_levels_cm2,fraction_in_levels_above_52,"
                "elastic_share_of_collisions,elastic_share_of_momentum_central,elastic_share_of_momentum_low_assumption,"
                "elastic_share_of_momentum_high_assumption,j_for_90pct_momentum,mean_rotational_energy_meV,"
                "mean_recoil_energy_meV_central,mean_recoil_energy_meV_low,mean_recoil_energy_meV_high,"
                "max_deviation_angle_integral_vs_state_to_state\n")
        for r in res:
            j90 = r["j90"] if r["j90"] is not None else ">52"
            f.write(f"{r['E']},{r['tab_el']:.4e},{r['tab_tot']:.4e},{r['sig_total_levels']:.4e},{r['missing_frac']:.4f},"
                    f"{r['share_el_coll']:.4f},{r['share_el_mt']['mid']:.4f},{r['share_el_mt']['hi']:.4f},{r['share_el_mt']['lo']:.4f},"
                    f"{j90},{r['mean_rot'] * 1000:.3f},{r['recoil']['mid'] * 1000:.3f},{r['recoil']['lo'] * 1000:.3f},"
                    f"{r['recoil']['hi'] * 1000:.3f},{r['dev_dcs_vs_s2s']:.4f}\n")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=".", help="folder containing (or above) the raw files")
    ap.add_argument("--out", default="h_co2_figures", help="output folder")
    ap.add_argument("--mode", choices=["all", "combined", "separate"], default="all",
                    help="combined = one PNG with every panel (plus the 3-panel summary); separate = one PNG per panel; all = both (default)")
    ap.add_argument("--pdf", action="store_true", help="also write PDF versions")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    E_tab, S_tot, S_el, res = load_all(a.data)
    write_numbers(out, res)
    if a.mode in ("all", "combined"):
        make_combined(out, E_tab, S_tot, S_el, res, a.pdf)
        make_summary(out, E_tab, S_tot, S_el, res, a.pdf)
        print("wrote", out / "h_co2_ALL.png", "and", out / "h_co2_SUMMARY.png")
    if a.mode in ("all", "separate"):
        names = make_separate(out, E_tab, S_tot, S_el, res, a.pdf)
        print(f"wrote {len(names)} separate figures in", out / "separate")
    print("wrote", out / "h_co2_numbers.csv")
    for r in res:
        j90 = r["j90"] if r["j90"] is not None else ">52"
        print(f"{r['E']:>4g} eV: elastic {r['share_el_coll']:.1%} of all collisions; elastic share of momentum transfer "
              f"{r['share_el_mt']['mid']:.1%} (range {r['share_el_mt']['hi']:.1%}-{r['share_el_mt']['lo']:.1%}); "
              f"90% of momentum transfer by j' = {j90}; rotation {r['mean_rot'] * 1000:.1f} meV against recoil "
              f"{r['recoil']['mid'] * 1000:.1f} meV per collision; levels above 52: {r['missing_frac']:.1%} of collisions; "
              f"angle integrals vs state-to-state: max deviation {r['dev_dcs_vs_s2s']:.2%}")

if __name__ == "__main__":
    main()