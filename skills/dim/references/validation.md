# DIM validation checklist with reference numbers

From the group's Ar 3s-hole model (validated) and the checklist written for the Ar 3p-hole extension (2026). Exciton checks: `di-dim`. Status marks: ✅ passed in the group's model · ⚠️ bracket or pending · ❌ not done. Use the same marks for your own model.

| # | Check | How | Ar 3s-hole result | Status |
|---|---|---|---|---|
| 1 | Pair curves | MRCI-ACPF/aug-cc-pVTZ ion dimer g/u curves; compare Rₑ, Dₑ, atomic limits | W(3.756 Å) = 18.0–18.2 meV | ✅ |
| 2 | Dimer limit | DIM of two atoms reproduces the input curves exactly | exact | ✅ |
| 3 | Site energies vs EOM-IP-CCSD | 9 bare + 12 molecule clusters, aug-cc-pVDZ | 1–5 meV | ✅ |
| 4 | Blind coupling test | W from DIM vs EOM on a new geometry | +4.1 / −3.6 / +6.4 meV | ✅ |
| 5 | Diabaticity | state reassignments over trajectory frames | 0 in 26k frames | ✅ |
| 6 | Gradients | analytic vs finite difference | max 1.6e-6 eV/Å (3p code) | ✅ |
| 7 | One-charge polarization | bulk value vs experiment (Ar 2p core-ion relaxation, Wurth et al., PRB 47, 6697 (1993)) | 0.96–1.0 eV vs ≈ 1.0 eV | ✅ |
| 8 | Two-charge screening | DIM vs ΔMP2 second-shell dication shift | ratio 1.00 ± 0.08 | ✅ |
| 9 | Surface penalty | DIM vs EOM for top-layer vs subsurface sites | 95/113 vs 94/109 meV (pairwise 154/193) | ✅ |
| 10 | Molecule shifts, blind | several distances and orientations, incl. a sign flip | MAE 4.5, max 7.2 meV; H-down +165 vs +173 | ✅ |
| 11 | Short-range molecule terms | counterpoise-corrected dimer scans, ab initio pair term | final-state pair term rms 2.9 meV; hole side still fitted | ⚠️ |
| 12 | Molecule on the surface | equilibrium height and orientation vs CCSD(T) | height 3.78 vs 3.55 Å; orientations within ±10 points | ⚠️ |
| 13 | Triples | EOM-CCSD vs (T) offsets | ×1–1.3 bracket | ⚠️ |
| 14 | Slab size | polarization vs a larger slab, per-site correction table | converged to ~0.04 eV | ⚠️ (document) |
| 15 | Integration | DT convergence; drift over 2 ps vs kinetic energy, potential range, W, kT | 0.1–0.5 meV per 2 ps (~0.1 % of moving energy) | ✅ |
| 16 | Edges | reflecting and absorbing edge, absorber vs exact non-Hermitian propagation | both reported | ✅ |
| 17 | Mobile region | enlarge and compare the observable | proposed | ❌ |
| 18 | Initial conditions | Wigner vs classical-harmonic; orientation populations vs independent estimate | orientation bias found, reweighted | ⚠️ |
| 19 | Statistics | n per set, ± errors, like-for-like comparisons with experiment | per set | ✅ |

## Extra checks for p-holes

- Atomic spin-orbit limit: Ar⁺ ²P₃/₂–²P₁/₂ 0.177 eV. A CASSCF+RASSI-AMFI test gave 0.155 eV (−12 %), so check the SO source.
- Linear symmetric Ar₃⁺ minimum against higher-level theory.
- Ar₂⁺ spectroscopic constants (Rₑ, Dₑ) for all Hund's case (c) states.

## Literature

- **DIM:** Ellison, JACS 85, 3540 (1963); Kuntz & Valldorf, Z. Phys. D 8, 195 (1988); Amarouche, Durand & Malrieu, JCP 88, 1010 (1988) (Xe_n⁺); Doltsinis et al. (1999) on three-body non-additivity in Ar_n⁺ (check the reference).
- **DIM + surface hopping:** Bonhommeau, Halberstadt & Buck, Int. Rev. Phys. Chem. 26, 353 (2007); Sisourat, JCP 139, 074111 (2013) (DIM + Fano widths + surface hopping).
- **Site-basis carrier dynamics in solids:** Spencer, Gajdos & Blumberger, JCP 145, 064102 (2016) (FOB-SH); Carof, Giannini & Blumberger, JCP 147, 214113 (2017).
- **CSDM:** Zhu, Nangia, Jasper & Truhlar, JCP 121, 7658 (2004).
- **Polarization:** Thole, Chem. Phys. 59, 341 (1981); Ren & Ponder, JPCB 107, 5933 (2003) (a = 0.39).
- **Decay distance laws:** Hofierka, Sisourat, Jahnke & Cederbaum, JCTC 21, 12026 (2025).
