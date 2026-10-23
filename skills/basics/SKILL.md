---
name: basics
description: Everyday electronic-structure calculations a newcomer usually needs first - geometry optimization, vibrational frequencies, choosing a DFT functional and basis set, interaction/binding energies of complexes (counterpoise, dispersion, CCSD(T), SAPT), and reaction or conformer energies, in Q-Chem or PySCF. Use for any routine ground-state calculation, or when someone asks which functional or basis set to use.
---

# Everyday calculations (standard practice)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

This skill is general textbook practice, not group lessons: the group's own experience is in the specialist skills. Check keyword names against the manual of the installed version (`troubleshooting`), and run the cheap version of any calculation first.

## 1. The usual order of work

1. **Structure.** Use a published or database structure if one exists (benchmark sets such as S22/S66 for noncovalent complexes, or crystal structures). Otherwise build one and optimize it.
2. **Optimize** with a reliable, cheap method: a dispersion-corrected hybrid DFT functional and a triple-ζ basis (§2).
3. **Frequencies at the same level.** All real frequencies means a minimum; one imaginary frequency means a transition state. Small imaginary modes (< ~50 cm⁻¹) in floppy complexes are often grid or convergence noise: tighten the grid and convergence and re-optimize.
4. **Energies.** Use single points at a higher level on the optimized structure when the question needs it (§3).

## 2. Choosing a functional and basis

- **Functional:** use a modern dispersion-corrected hybrid. ωB97X-D, ωB97M-V or B3LYP-D3(BJ) are well tested. These come from large benchmark studies (GMTKN55, Goerigk et al. 2017; Mardirossian & Head-Gordon 2017). Plain B3LYP without dispersion fails for stacked or vdW-bound systems.
- **Charge transfer, Rydberg or excited states:** use a range-separated hybrid (ωB97X-D, CAM-B3LYP), and see `eom-cc` or `tides`.
- **Basis:** def2-SVP for quick tests, def2-TZVP for production DFT. Add diffuse functions (aug-, or def2-TZVPD) for anions, weak interactions, polarizabilities and Rydberg states.
- **Integration grid:** use a fine grid for frequencies and weak interactions (e.g. Q-Chem SG-2 or SG-3, or PySCF `grids.level` 4–5).
- Say which functional, dispersion correction and basis you used whenever you report a number (`reporting-computational-results`).

## 3. Interaction (binding) energies of complexes

- **Definition:** E_int = E(AB) − E(A) − E(B), at the complex geometry for the interaction energy, or with relaxed monomers for the binding energy. Say which one you report.
- **Counterpoise (Boys–Bernardi):** compute the monomers in the full dimer basis (ghost atoms) to remove basis-set superposition error. This matters most with small basis sets. With large, diffuse basis sets, report both raw and counterpoise-corrected values, or their average.
- **Accuracy ladder:** DFT-D (~0.3–1 kcal/mol for good functionals on S66-type sets) → MP2 (overbinds π stacking) → CCSD(T)/CBS, the reference standard. Get CCSD(T)/CBS by extrapolating from aug-cc-pVTZ/QZ correlation energies, or with a focal-point scheme. DLPNO-CCSD(T) and similar local methods make larger complexes affordable.
- **Why it binds:** SAPT (e.g. SAPT0/jun-cc-pVDZ, or Q-Chem XSAPT) splits the interaction into electrostatics, exchange, induction and dispersion.
- **Benzene dimer** is the classic example. Compare the parallel-displaced, T-shaped and sandwich arrangements with the S22/S66 CCSD(T)/CBS reference values before trusting your own numbers.

## 4. Reaction, conformer and relative energies

- Use the same method and basis for every species in a comparison.
- Add zero-point energy (from the frequencies) for 0 K energies, and thermal corrections for enthalpies and free energies. Low-frequency modes (< ~100 cm⁻¹) make entropies unreliable; quasi-harmonic corrections are common.
- For spin states, transition metals or bond breaking, check for multireference character (spin contamination ⟨S²⟩, T1 diagnostic) before trusting single-reference results, and ask someone who has done those systems.

## 5. Q-Chem and PySCF quick reference

For details see the `pyscf` and `psi4` skills. Psi4 is the easiest route to SAPT and to automatic counterpoise / CBS (`nbody`, `cbs`).

- **Q-Chem:** `JOBTYPE opt`, `freq` or `sp`; `METHOD wB97X-D`; `BASIS def2-TZVP`. For counterpoise, put the fragments in `$molecule` separated by `--` and use `JOBTYPE bsse`. For SAPT, use `JOBTYPE xsapt`.
- **PySCF:** `dft.RKS(mol).set(xc='wb97x-d')` (dispersion through the `dftd3`/`dftd4` interfaces). Geometry optimization uses `pyscf.geomopt` with geomeTRIC or PyBerny. For counterpoise, build the monomer `Mole` with ghost atoms (`ghost-` prefix or `X-` atoms).
- Before submitting, run the plugin's checkers (`pace-slurm` §0).

## 6. Common mistakes

- Comparing energies from different functionals, bases or grids.
- Optimizing without dispersion, which leaves weak complexes falling apart or wrongly stacked.
- Skipping frequencies, so you never confirm the structure is a minimum.
- Reporting an interaction energy without saying whether it is counterpoise-corrected, or whether monomers were relaxed.
- Using a minimal or double-ζ basis without diffuse functions for anions or weak interactions.
