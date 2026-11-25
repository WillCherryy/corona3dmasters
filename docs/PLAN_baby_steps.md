# Plan: baby steps towards rotationally inelastic H + CO2 collisions (user's plan, 25 Nov 2026)

The user's order: (1) only DECLARE whether a collision is elastic or inelastic and check that nothing changes; (2) give inelastic collisions a FIXED energy loss (average loss of an inelastic collision at the collision energy); (3) later the channel-resolved scheme (docs/PLAN_inelastic_channels.md); (4) use seed files throughout. Code is edited by the user; everything below was built and tested in a scratch copy (cpp checkout + the user's partner-selection change). Nothing was pushed to `test`.

## Step 1: declaration only
- One new species-config key `elastic_sigma_file` (the elastic cross-section table). After the partner is chosen, the collision is declared inelastic with probability 1 - sigma_elastic(E)/sigma_total(E) (E = collision energy in the centre-of-mass frame, in eV, as in all tables). Species without the key (O, N2, CO) behave exactly as before.
- The declaration uses a SEPARATE random generator (`mt19937_64`, fixed seed), so the main random stream, and therefore every seeded result, is untouched. (Drawing from the main stream would shift all later random numbers and make same-seed comparison impossible.)
- Counters and a console line `Collision types for CO2: N collisions, elastic ..., inelastic ..., fraction inelastic ...`.
- Needs NO new data files: the total table and the elastic table are on `test`. For the pure plumbing test, any angle files will do (the elastic angle files on `test` were used).
- Expected: same seed, with and without the new key: all output files identical.

## Step 2: fixed energy loss
- New key `inelastic_dE_file`: table `Energy(eV),dE(eV)` of the mean energy loss of an inelastic collision, linearly interpolated (end values outside the table, as for the cross sections). dE = sum over final levels j' >= 2 of sigma_j' B j'(j'+1) / sum over j' >= 2 of sigma_j' (B = 0.39022 cm-1; rotational energy gained by CO2, taken out of the relative motion).
- `Particle::do_collision` gets an optional last argument dE_eV (default 0.0): the centre-of-mass speed is multiplied by sqrt(1 - dE/E_cm). Energy loss only for inelastic collisions; if dE would not be below E_cm (only possible below the lowest tabulated energy) it is set to zero and counted.
- Data (tools/make_inelastic_loss_table.py, from the Bop and Gacesa state-to-state file): H + CO2 2.726 / 15.040 / 33.814 meV per inelastic collision at 0.1 / 1 / 5 eV (inelastic fraction 38.97 / 52.54 / 52.81 %; per collision of any kind 1.062 / 7.902 / 17.856 meV); D + CO2 4.696 / 26.432 / 56.179 meV (inelastic fraction 31.71 / 51.40 / 54.07 %). A 149-energy table is used rather than the three points: a table of three points clamps to 2.726 meV below 0.1 eV, which exceeds the collision energy below 2.7 meV.
- Needs NEW data files on `test` (to be agreed with the user): the loss table, and for a physical run an angle distribution summed over all final levels (the angle files on `test` are elastic only).
- Limitation to state: one angle distribution (the summed one) is used for elastic and inelastic collisions, so the link between large angle and large energy loss is lost; the channel scheme restores it.

## Seeds
`run_sim2.sh label NPARTS NSTEPS SEED` writes `rng_seed` into the run folder: the same seed gives identical output (tested). Step 1 against the reference: identical. Step 2 against Step 1: identical only until the first inelastic collision; compare averages over several seeds (and use the production size, 10 runs of 100,000 particles, for conclusions).
