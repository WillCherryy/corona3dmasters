# Reading guide: elastic and inelastic collisions in the hot-H model, and the H-CO2 assumption

Written 8 Nov 2026. Quotations from Gregory et al. (2023a) and Bop and Gacesa (2026) were read from the PDFs supplied by the user. References marked [V] had their full citation checked in a reference list of those papers; references marked [U] are standard textbooks or papers cited by name in them whose details I did not read, so check each before citing.

## 1. The question in one paragraph

Gregory et al. (2023a) track hot H atoms through CO2, N2, CO and O using **elastic** collisions only, with the O-H cross sections of Zhang et al. (2009) for all four gases, and justify neglecting inelastic collisions by the claim that they are unimportant at the energies involved. Bop and Gacesa (2026) computed H/D + CO2 state-to-state cross sections and find that the elastic channel is only 40 to 55% of the total, that the scattering is strongly forward-peaked, and that the large-angle scattering sits in the rotationally inelastic channels. The question is whether, and in which sense, "inelastic collisions are unimportant" holds for H + CO2.

## 2. The physics you need (with the formulas used in this project)

**Centre-of-mass picture.** For a projectile of mass $m_1$ hitting a target of mass $m_2$, a single elastic collision can transfer at most the fraction

$$ f = \frac{4 m_1 m_2}{(m_1+m_2)^2} $$

of the projectile's energy (for a target initially at rest). Values for H: O 0.223, N2 0.134, CO 0.134, CO2 0.088. For D: O 0.397, N2 and CO 0.250, CO2 0.167.

**Cross sections.** With $d\sigma/d\Omega$ the differential cross section,

$$ \sigma = 2\pi\int_0^\pi \frac{d\sigma}{d\Omega}\sin\theta\,d\theta, \qquad \sigma_{mt} = 2\pi\int_0^\pi (1-\cos\theta)\frac{d\sigma}{d\Omega}\sin\theta\,d\theta . $$

$\sigma$ sets how often collisions happen; $\sigma_{mt}$ (momentum transfer) sets how much direction and energy they change. The mean fractional energy loss per elastic collision is

$$ \left\langle \frac{\Delta E}{E}\right\rangle = \frac{f}{2}\,\frac{\sigma_{mt}}{\sigma}. $$

**Illustration with this project's numbers (1 eV, H on CO2, f = 0.088; own calculation, mean $1-\cos\theta$ as the model samples it):** O-H tables used as the CO2 stand-in 0.218 gives about 0.96% per collision; H-CO2 elastic channel only 0.011 gives about 0.05%; H-CO2 summed over all final states 0.231 gives about 1.0%. At 5 eV the values are 0.135, 0.006 and 0.090. So per collision, the stand-in and the summed data thermalise similarly, while the elastic channel alone barely does. (The sampled values differ from the true table integrals because the model ignores the spacing of the tabulated angles; see logbook A26.)

**Rotational inelasticity of CO2.** A linear rotor has levels $E_j = B\,j(j+1)$ with $B \approx 0.39\ \mathrm{cm^{-1}}$ (approximate): about 0.3 meV for $j=2$, 5 meV for $j=10$, 0.13 eV for $j=52$. Energy given to rotation is therefore small per event for low $j'$. The reason it still matters is that these channels carry the large-angle scattering: they are the collisions where the atom meets the anisotropic repulsive wall of the molecule.

**Pairing rule for the model.** The cross section and the angle distribution must describe the same set of outcomes: elastic $\sigma$ with the $j'=0$ distribution, or total $\sigma$ with the sum over final states. Total $\sigma$ with the elastic angles counts inelastic collisions but scatters them forward, which is inconsistent. For atom-atom O-H, total and elastic are the same thing.

**Escape probability picture (Gregory et al. 2023a, Section 3).** They fit $p = A\,e^{-bN\sigma}$ with $N$ the overhead column density and $\sigma$ the total O-H cross section, interpret $A \approx 0.5 + 0.5\alpha$ where $\alpha$ is the albedo (atoms initially heading down that are turned around and escape; they find $\alpha$ = 0.83 at 5 eV and 0.63 at 0.2 eV) and $b$ as a transparency coefficient ("a single collision is not necessarily sufficient to thermalize"). They quote about 26 collisions to thermalise a 5 eV H and about 8 for 0.2 eV (citing Krasnopolsky 2010). Both $\alpha$ and $b$ depend on how strongly a collision deflects and slows the atom, which is exactly what changes between the O-H stand-in and the H-CO2 data.

## 3. Gregory et al.'s justification, step by step

Quoted from the paper:
1. Model description: particles "collide elastically with neutral background species (CO, CO2, N2, and O). We use the total and differential O-H cross sections of Zhang et al. (2009), without modification, for collisions with all four background species due to a lack of availability of more specific data."
2. Main text: "We neglect inelastic collisions as they are unimportant relative to elastic collisions at the low energies relevant to H scattering through an atmosphere predominantly composed of much heavier species (Lichtenegger et al., 2006)."
3. Limitations: "The lack of inelastic collisions may result in some overestimation of particle energies and therefore escape. However, inelastic channels are insignificant for atom-atom collisions at these energies (Lewkow & Kharchenko, 2014), and we follow the assumptions of similar hot H Monte Carlo modeling, which suggests that inelastic atom-molecule collisions are also unimportant at energies below 8 eV (Lammer et al., 2006; Lichtenegger et al., 2006)."
4. On the stand-in: "we opt instead to use unscaled O-H cross sections for collisions of H with all background species until dedicated cross sections for each collision pair are generated ... This assumption likely affects our results the most, and we will update our model to use the relevant cross sections as they become available."

So the argument has three legs: (i) atom-atom inelasticity is negligible (true for O-H, there is nothing to excite); (ii) earlier hot-H Monte Carlo work argues the same for atom-molecule collisions below 8 eV; (iii) practicality, with the authors stating the limitation and its likely importance.

## 4. Why it may not hold for H + CO2 (what the new data say)

1. **The premise "inelastic is small relative to elastic" is not satisfied for the cross section.** Bop and Gacesa: elastic is 40 to 55% of the total across the whole energy range; at 5 eV the first inelastic series ($j'=2$) alone is about 12% of the total (own integration of the supplied file), and the elastic channel is 48%.
2. **The angular structure is channel dependent.** Forward peak ($\theta \lesssim 2^\circ$) more than 90% of the integral cross section; the elastic part exceeds 80% below $2^\circ$ but falls below about 5% at $180^\circ$. So deleting the inelastic channels removes the large-angle scattering, not just a bit of energy loss.
3. **The energy argument and the direction argument are different.** The energy absorbed by rotation per event is mostly small (section 2), which supports the paper's energy claim; the problem is that the paper's phrase also removes the collisions' deflection, which matters for turning atoms around (the albedo $\alpha$ above).
4. **The stand-in is not obviously wrong in size.** The O-H total cross section at 5 eV (3.9e-15 cm2) is close to the H-CO2 total (4.8e-15). The paper's warning of factors of 30 to 45 concerns mass-scaling O-CO2 or C-CO2 data, a different shortcut. With the code's sampled angles, the H-CO2 summed variant and the O-H stand-in give similar momentum transfer per collision at 1 eV. So the true effect of the stand-in could be modest; the elastic-only variant is the extreme case.
5. **What the elastic-only runs measure.** Escape rises by about 2.3 times in the HSA runs because CO2, the dominant gas in the lowest layers, is almost transparent to the atom. This is a sensitivity result (the cost of the "elastic only" reading for a molecule), not a prediction.
6. **What a fully correct treatment would need.** State-to-state kinematics in which the relative speed after the collision is reduced by the energy given to rotation. The model has only elastic kinematics, so the summed variant is an approximation: right angles and frequency, energy loss to rotation neglected (small for most channels).

## 5. Reading list

### 5.1 The two papers at the centre
- Gregory, B. S., Elliott, R. D., Deighan, J., Gröller, H., Chaffin, M. S. (2023a). HCO+ dissociative recombination: a significant driver of nonthermal hydrogen loss at Mars. J. Geophys. Res. Planets 128, e2022JE007576. doi:10.1029/2022JE007576 [V]. Read Section 2 (the model), Section 3 (the escape probability and albedo), and the limitations paragraph.
- Gregory, B. S., Chaffin, M. S., Elliott, R. D., Deighan, J., Gröller, H., Cangi, E. (2023b). Nonthermal hydrogen loss at Mars: contributions of photochemical mechanisms to escape and identification of key processes. J. Geophys. Res. Planets 128, e2023JE007802. [V]. Source of the escape probability tables in `src/model_output_data/`.
- Bop, C. T. and Gacesa, M. (2026). H/D-CO2 superthermal collisions (title as in the running head; check). MNRAS 552, 1-8. doi:10.1093/mnras/stag1696 [V]. Read the abstract, Section 3.1 to 3.3 (total and elastic cross sections, forward peak, momentum transfer, rate coefficients) and the discussion of atmospheric implications.
- Bop, C. T. and Gacesa, M. (2025a), Zenodo dataset "Superthermal kinetic energy transfer via CO2 collisions with H and D: elastic and inelastic cross-sections", doi:10.5281/zenodo.17549249 [V]; and Bop and Gacesa (2025b), MNRAS 544, L45 [V, title not read].

### 5.2 The justification chain in Gregory et al.
- Lichtenegger, H. et al. (2006). Effects of low energetic neutral atoms on Martian and Venusian dayside exospheric temperature estimations. Space Sci. Rev. 126, 469-501. doi:10.1007/s11214-006-9082-1 [V]. READ (8 Nov 2026, text search of the PDF): the only collision statement is one paragraph in the Mars hot-H section: the Monte Carlo model of Lammer et al. (2000) is used and hot H atoms (0.1 to 8 eV from photochemical reactions) "are assumed to become eventually thermalized by a series of elastic hard sphere collisions with the background gases such as CO2 or O, while inelastic collisions are negligibly small at these low energies". It gives no cross sections and no calculation or reference for that statement, so it is an assumption, and the 8 eV is the top of its hot-H energy range. Lammer, Stumptner, Bauer (2000), Planet. Space Sci. 48, 1473 [V, not read], is the Monte Carlo model it uses.
- Lammer, H. et al. (2006). Loss of hydrogen and oxygen from the upper atmosphere of Venus. Planet. Space Sci. 54, 1445-1456. doi:10.1016/j.pss.2006.04.022 [V]. Same question for Venus.
- Lewkow, N. R. and Kharchenko, V. (2014). Precipitation of energetic neutral atoms and induced non-thermal escape fluxes from the Martian atmosphere. Astrophys. J. 790, 98. doi:10.1088/0004-637X/790/2/98 [V]. The scaled H-N2, H-CO and H-CO2 cross sections and the atom-atom inelasticity statement.
- Krasnopolsky, V. A. (2010). Solar activity variations of thermospheric temperatures on Mars and a problem of CO in the lower atmosphere. Icarus 207, 638-647 [V]. The source of the "about 26 collisions to thermalise" figure.
- Zhang, P., Kharchenko, V., Jamieson, M. J., Dalgarno, A. (2009). Energy relaxation in collisions of hydrogen and deuterium with oxygen atoms. J. Geophys. Res. 114, A07101. doi:10.1029/2009JA014055 [V]. The O-H (and, from the title, O-D) cross sections used; check the tables, the angular grid and the energies.
- Hodges, R. R. Jr. (1994). Monte Carlo simulation of the terrestrial hydrogen exosphere. J. Geophys. Res. 99, 23229-23247 [V]. The hot-H and exosphere Monte Carlo methodology.
- Gröller, H., Lichtenegger, H., Lammer, H., Shematovich, V. I. (2014). Hot oxygen and carbon escape from the Martian atmosphere. Planet. Space Sci. 98, 93-105 [V]. A related Monte Carlo treatment of collisions.

### 5.3 CO2 versus O, and heavy-target scattering
- Gacesa, M., Lillis, R. J., Zahnle, K. J. (2020). O(3P) + CO2 scattering cross-sections at superthermal collision energies for planetary aeronomy. MNRAS 491, 5650-5659. doi:10.1093/mnras/stz3366 [V]. The same method for O + CO2, which Gregory et al. cite as the reason for caution.
- Gacesa, M. (2024), MNRAS 528, 2621 and Gacesa and Kharchenko (2014), J. Chem. Phys. 141, 164324 [V as citations; titles and subjects not read]: both are cited in Bop and Gacesa; check what they cover before relying on them.
- Bop and Gacesa mention experiments on collisions of translationally hot H atoms with CO2. The Flynn-group papers in their reference list are probably those: Kreutz and Flynn (1990), J. Chem. Phys. 93, 452; Khan, Kreutz, Flynn, Weston (1990), J. Chem. Phys. 92, 4876; Kreutz, Khan, Flynn (1990), J. Chem. Phys. 92, 347 [V as citations; titles not read, so confirm which paper the sentence refers to].

### 5.4 Quantum scattering methods behind the data
- Alexander, M. H. and Manolopoulos, D. E. (1987). J. Chem. Phys. 86, 2044 [V] (the log-derivative-Airy propagator used by Bop and Gacesa).
- McGuire, P. and Kouri, D. J. (1974). J. Chem. Phys. 60, 2488 [V] (the coupled-states approximation, which Bop and Gacesa benchmark to within 7% against close-coupling).
- Hutson, J. M. and Green, S. (1994). MOLSCAT computer code, version 14 [V].
- Textbooks [U]: M. S. Child, *Molecular Collision Theory* (elastic and inelastic scattering, rotational excitation, forward diffraction peaks, the coupled-states approximation); R. D. Levine and R. B. Bernstein, *Molecular Reaction Dynamics and Chemical Reactivity*; L. D. Landau and E. M. Lifshitz, *Quantum Mechanics*, scattering chapters (cross sections, diffraction at high energy).

### 5.5 Atmospheric context and escape theory
- Schunk, R. W. and Nagy, A. F. (2009). *Ionospheres*, 2nd edn., Cambridge University Press [V]. Collision frequencies, momentum transfer cross sections and energy relaxation.
- Hunten, D. M. (1973). J. Atmos. Sci. 30, 1481 [V]. Escape from planetary atmospheres.
- Chamberlain, J. W. and Hunten, D. M., *Theory of Planetary Atmospheres* [U]. Exobase, escape and Monte Carlo background.
- Fox, J. L. (2015). The chemistry of protonated species in the Martian ionosphere. Icarus 252, 366-392 [V]. The profiles and the HCO+ chemistry used by the model.

## 6. Suggested reading order and what to extract

1. Gregory 2023a, Sections 2 and 3 and the limitations paragraph: write the model's collision rules and every stated assumption in your own words.
2. Bop and Gacesa 2026: extract the elastic fraction against energy, the forward-peak statement, $\sigma_{mt}/\sigma$, and what they conclude for atmospheric models.
3. Lichtenegger 2006 and Lammer 2006: write down exactly what "unimportant" means in each (energy loss? cross section? at which energies, for which molecules?) and which cross sections they used.
4. Lewkow and Kharchenko 2014: what they say about H + N2, CO, CO2 inelasticity.
5. Textbook chapters on rotational excitation and forward diffraction scattering.
6. Zhang 2009 tables (needed anyway for the D work).

## 7. Questions to answer in the thesis

- In the earlier work, did "unimportant" refer to energy loss per collision, to cross section, or to the outcome (escape rate)? Is the claim supported for CO2, a rotor with an anisotropic potential?
- How large is the rotational energy loss per collision from the state-to-state data (sum over $j'$ of $\sigma_{j'}\,\Delta E_{j'}$ against the elastic recoil loss)? This can be computed directly from the files.
- Do the summed-variant and elastic-only escape rates bracket the O-H baseline, and where does the baseline sit?
- How do the answers change for D, whose mass ratio and cross sections differ (Bop and Gacesa: up to 35% larger below 0.1 eV)?
