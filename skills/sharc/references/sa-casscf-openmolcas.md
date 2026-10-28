# SHARC + OpenMolcas SA-CASSCF (Sep 2026): project-specific settings and lessons

Settings and lessons from one project: an Ar 3s hole (one hole spread over N Ar sites, SA-CASSCF(2N−1, N)/cc-pVDZ) next to a water, run through `SHARC_MOLCAS.py` with SHARC 3.0.2. The route was retired in favour of a model Hamiltonian (`dim-ar-water.md`; reasons in `SKILL.md` §10). Copy the reasoning, not the numbers. OpenMolcas errors and keywords are in `troubleshooting/references/openmolcas.md`.

## Active space

- **Choose active orbitals by ownership inside an energy window.** Localize the neutral RHF orbitals (Pipek–Mezey in `&LOCALISATION` gave clean single-atom 3s orbitals), keep only occupied orbitals with ε in the 3s window (−2.2 to −0.9 Ha for Ar) and > 50 % on one atom, then pick by atom. Print ε and shell for every pick; stop if |ε| > 5 Ha (core) or ε > 0 (virtual). Ownership alone picked Ar 1s orbitals (100 % on the atom) and gave a 3.2 keV collapse.
- **Check the seed orbitals, not just the result.** Seeds taken from a cation UHF held Ar 3p and water lone pairs (s-fraction 0.00); the state-averaged energy was ~20 eV *below* the clean 3s solution, and SUPSYM then faithfully kept the wrong space. Check the s-fraction of every active orbital in the seed.
- **Super-CI orbital optimization drifts the active space** toward O 2p / Ar 3p mixtures. ALTER only fixes the starting guess. `SUPS` (one orbital per group) kept the active orbitals 100 % Ar while still relaxing them. Index rules are in the OpenMolcas reference.
- **Map roots to sites by the per-root natural occupations** (the site with occupation ~1.0), not by root order.
- **CIONLY (frozen orbitals) was a workaround, not a fix.** It needs numerical gradients (the analytic CIONLY gradient was 25 % off), and it gave implausible energies for some roots.

## Gradients and cost

- **Analytic gradients (RASSCF + MCLR + ALASKA) with SUPSYM are correct** once the active space is clean: they matched central finite differences to 0.1–0.9 %.
- **SHARC's numerical gradients were wrong under SUPSYM** (~37 % too large on the water atoms). `SHARC_MOLCAS.py` starts each displacement from the converged central-point orbitals (`JobIph.master`), not the seed, and with SUPSYM the energy depends on the starting orbitals. Use analytic gradients here.
- **Cores:** with one gradient per step (`grad_select`, `eselect 0.001`), 8 cores cost ~605 s per step for 17 atoms, 16 cores ~580 s, 4 cores ~975 s, 2 cores ~1800 s. Use 8. `eselect 0.2` computed ~5 gradients per step (~45 % slower). Watch the `grad_select` bug in `SKILL.md` §4.
- **Step 0 is slow** because all gradients are requested before there is an active state. Quote a per-step cost only after hours of steps.
- **No dispersion in CASSCF.** The group added D3 in the interface (all atoms, including the hole atom). It held the lattice geometry together; it did not fix the site-energy gaps (unverified for gaps).

## Interface patches (group copy of `SHARC_MOLCAS.py`)

- The shared copy's template parser used substring matching, so a line starting with `supsym_anagrad` also matched `supsym` and erased the SUPSYM list. The private copy (`molcas_surface/SHARC_MOLCAS_split.py`) fixes it.
- Once that path ran, the `supsym_anagrad` branch crashed with a `KeyError` on `gradmode`, because it never set one (fixed: `gradmode = 1`).
- Other patches: a `cionly` template keyword, forced numerical gradients under CIONLY, a `frozen_atoms` keyword, a D3 hook, and a fix for a stray `*` in the RASSI dipole search string (`getcidm()`), which made every dipole lookup fail with "too few matrix elements".
- `MOLCAS.template`/`MOLCAS.resources` and the seed `MOLCAS.<m>.RasOrb.init` go in each trajectory's `QM/` directory, with `always_orb_init` set.

## Validation that caught the real problems

- **Step-0 site-energy spread versus EOM-IP-CCSD at the same contact distance.** Plausible ensembles had 0.6–0.9 eV; broken ones 3.5–3.8 eV or keV. Moving the water O from 2.5 to 3.5 Å (the EOM placement) halved the spread, so compare like with like.
- **Absolute state-averaged energy versus a clean single point.** Runs with a "good" 0.6 eV spread sat 0.66–0.73 Ha below the clean 3s reference: they were 3p holes.
- **Mirror-equivalent sites should come out degenerate.** Splits of 1.2 eV between mirror pairs exposed a broken SUPS index.
- **Save U with the interface's sign convention for every frame** if you will project onto sites later (unverified as a separate failure; the diag/MCH trap in `SKILL.md` §9 is verified).
