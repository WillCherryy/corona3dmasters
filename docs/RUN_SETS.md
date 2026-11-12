# Run sets: what each label prefix means (12 Nov 2026)

One line per set. "Old code" = executable MD5 `c0c22499...` (partner chosen by density only); "fixed code" = MD5 `6236607e...` (partner chosen by sigma n, commit `cfb928e`). Run folders are in `~/corona3dmasters/src/runs/` unless stated.

| Label prefix | What it is | Code | Atmosphere | CO2 data (other gases: O-H) | Particles | Status / use |
|---|---|---|---|---|---|---|
| `baseline_1` to `baseline_10` | original model | old | LSA | O-H stand-in | 100,000, seedless | finished; the LSA reference set |
| `hsa_baseline_1` to `hsa_baseline_10` | original model | old | HSA | O-H stand-in | 100,000, seedless | finished; the HSA reference set |
| `hco2el_*_old_code` (labels `hco2el_lsa_N`, `hco2el_hsa_N` in `summary.csv`) | elastic-only H-CO2 | OLD (density-only partner choice, biased) | LSA and HSA | H-CO2 elastic only | 100,000, seedless | superseded by `hco2elfix`; keep as the "before" record; check which finished |
| `hco2elfix_lsa_1` to `_10` | elastic-only H-CO2, corrected | FIXED | LSA | H-CO2 elastic only | 100,000, seedless | launched with `run_sim2.sh` (confirm date) |
| `hco2elfix_hsa_1` to `_10` | elastic-only H-CO2, corrected | FIXED | HSA | H-CO2 elastic only | 100,000, seedless | launched with `run_sim2.sh` (confirm date) |
| `seed123_a`, `seed123_b` | reproducibility pair | old | LSA | O-H | 100,000, seed 123 | identical outputs; test only |
| `smoke_*`, `smoketest_*`, `hsa_smoke`, `smoke_hco2el_*`, `smoke2_*`, `chk_*`, `timing_test`, `analysis_smoketest` | small tests | various | various | various | 300 to 1,000 | tests; EXCLUDE from analysis |
| `~/pair_old/runs/*`, `~/pair_new/runs/*` (other folders) | old-versus-fixed tests A and B | old and fixed | LSA | equal constant sigma (`eqsig_*`) or O-H (`base_1`, `base_2`) | 300 and 5,000 | tests; archived separately |

Planned, not yet run: elastic H-CO2 summed over final states ("total") with the fixed code; state-resolved inelastic H-CO2; deuterium (needs the O-D tables and new code).

To list every run folder with its start time, particles, config, commit, executable fingerprint and status, run `~/run_register.sh` (from `tools/run_register.sh`).
