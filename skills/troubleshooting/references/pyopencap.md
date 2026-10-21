# OpenCAP / pyopencap (projected CAP): troubleshooting reference

Last researched: 2026-10-21

**How to use this file:** find your symptom under "Known issues and fixes", check the cause against your output, apply the fix, and reproduce a starter calculation before you trust any production width.

---

## Official documentation

**Code and docs.** The repository is <https://github.com/gayverjr/opencap>, and the Python API docs are at <https://gayverjropencap.readthedocs.io/en/latest/>. C++ Doxygen docs are at <https://gayverjr.github.io/opencap/>. The useful doc pages are `getting_started.html`, `theory.html`, `keywords.html`, `analysis/analysis.html`, `custom_cap_and_grid.html` and `interfaces/{QChem,pyscf,OpenMolcas,psi4,Columbus}.html`.

**Install.** Run `pip install pyopencap`. Wheels cover Python 3.9 and later on most Linux and macOS systems. A source build (`pip install .`) needs C++17, CMake 3.12 or later, HDF5 1.10 or later and Eigen 3.3 or later. There is also a command-line program, run as `opencap input.in`, with `$system` and `$projected_cap` blocks (see `examples/opencap/*.in`).

**Papers to cite or read.**
- J. R. Gayvert, K. B. Bravaya, "Projected CAP-EOM-CCSD method for electronic resonances", *J. Chem. Phys.* **156**, 094108 (2022). This is the method paper.
- Gayvert and Bravaya, "Application of Box and Voronoi CAPs for Metastable Electronic States in Molecular Clusters", *J. Phys. Chem. A* **126**, 5070 (2022). It finds Voronoi CAPs generally more robust for clusters, with box CAPs fine for localized resonances. I saw this only in search snippets; the full text returned 403.
- Gayvert and Bravaya, "OpenCAP: An open-source framework…", *J. Phys. Chem. A* (2023). A Bravaya CV lists it as submitted; final publication is unverified.
- Background papers: Riss and Meyer, *J. Phys. B* **26**, 4503 (1993), for the CAP method and the first-order correction; Sommerfeld and Santra, *IJQC* **82**, 218 (2001), for projected CAP/CI; and Sajeev et al., *J. Chem. Phys.* **131**, 211102 (2009), for the continuum-remover CAP (CR-CAP).

**What projected CAP does.** The program runs an ordinary real (CAP-free) calculation for N states. It then builds the CAP matrix W in that N-state basis from state densities and transition densities, and diagonalizes H0 − iηW for a list of η values. The expensive electronic-structure step runs once. The price is a new parameter: the number of states in the subspace. The real-calculation orbitals and states never see the CAP; it only mixes them afterwards (developer comment in issue #52).

**Workflow and key calls.**
1. Build the system: `s = pyopencap.System(sys_dict)`. `"molecule"` is one of `qchem_fchk`, `molden`, `rassi_h5` or `read` (inline). Check AO ordering with `s.check_overlap_mat(S, "pyscf"|"psi4"|...)`.
2. Build the CAP: `pc = pyopencap.CAP(s, cap_dict, nstates)`. **All dictionary values must be strings** (`"2.76"`, not `2.76`).
3. Load the data. For Q-Chem or OpenMolcas files, use `pc.read_data(es_dict)` and then `H0 = pc.get_H()`. For PySCF or Psi4 densities in memory, call `pc.add_tdm(dm_ao, i, j, "pyscf")` for every pair (i, j); you supply H0 yourself.
4. Project: `pc.compute_projected_cap()`, then `W = pc.get_projected_cap()`. Without recomputing anything, `pc.compute_ao_cap(new_cap_dict)` followed by `compute_projected_cap()` re-projects with a new onset.
5. Analyze:
   - `from pyopencap.analysis import CAPHamiltonian`, then `CAPH = CAPHamiltonian(H0=H0, W=W)`. `CAPHamiltonian(pc=pc)` and `CAPHamiltonian(output="file.out", irrep="B2g")` also work; the latter reads Q-Chem PROJ_CAP=3 output.
   - `CAPH.run_trajectory(eta_list, cap_lambda=0.0, include_states=[...] or exclude_states=[...])`.
   - `traj = CAPH.track_state(k, tracking="overlap"|"energy")`.
   - `traj.find_eta_opt(corrected=False|True, start_idx=10, end_idx=-1, ref_energy=E_neutral, units="eV")` returns `(E_res − iΓ/2, η_opt)`.
   - Diagnostics: `traj.energies_ev(ref_energy, corrected=True)`, `traj.get_logarithmic_velocities(corrected=...)` and `CAPH.export("x.out")`.

**CAP keywords (`cap_dict`).**
- `cap_type` is `box`, `voronoi` or `custom` (a Python function of x, y, z and weights).
- Box onsets `cap_x`, `cap_y` and `cap_z` are in **bohr**. The Voronoi cutoff `r_cut` is also in bohr.
- `radial_precision` defaults to 14 and `angular_points` to 590 (Lebedev).
- `thresh` (default 7) drops GTOs with exponents below 1e-thresh. Lower it if you get grid-allocation errors.
- `do_numerical`: box CAP integrals are analytic by default; Voronoi and custom CAPs are integrated numerically.

**Electronic-structure keywords (`es_dict`, `read_data`).**
- `method` is `eom`, `tddft` or `ms-caspt2`/`xms-caspt2`.
- `package` is `qchem` or `openmolcas`.
- File keys are `qchem_output` with `qchem_fchk`, or `molcas_output` with `rassi_h5`; `h0_file` supplies a custom H0.

**Q-Chem side.**
- **To export densities for pyopencap:** `GUI = 2` in `$rem`.
- **Native projected CAP (Q-Chem 5.4 or later):** `COMPLEX_CCMAN = 1` plus a `$complex_ccman` block with `PROJ_CAP 3`, `CAP_TYPE` (0 spherical, 1 cuboid, 2 smooth Voronoi), `CAP_X/Y/Z` (in units of 1e-3 bohr), `CAP_ETA` (in units of 1e-5 au) and `PROJ_PROP 1` for first-order corrections.
- **EOM types:** Q-Chem's manual says projected CAP is **currently EE/EA only**, not IP. See the [Q-Chem 6.3 manual](https://manual.q-chem.com/6.3/sub_cc_cs_cap.html).

**Interfaces.**
- **PySCF:** officially FCI, ADC (via adcc) and TDA-TDDFT. EOM-EA-CCSD exists only as a repository example. Other methods are "use at your own risk".
- **OpenMolcas:** (X)MS-CASPT2 and NEVPT2.
- **Psi4:** FCI and ADC.
- **Columbus:** MRCI.

**First-order correction.** The corrected energy is U = E − η dE/dη (Riss and Meyer). It removes the leading CAP perturbation and usually shifts η_opt larger and the width smaller. Report which one you used and show both.

**Choosing η.** Pick the stationary point of the trajectory, where the logarithmic velocity |η dE/dη| is at a minimum. `start_idx` skips the trivially small-η region. When the trajectory has more than one minimum, a small real `cap_lambda` (CR-CAP) can remove the unphysical one.

---

## Starter calculations

**1. N2⁻ ²Πg shape resonance, Q-Chem EOM-EA-CCSD with pyopencap (official tutorial).** Source: `examples/analysis/N2/QChemTutorial.ipynb` and `ref_outputs/` in the repository.
- **Setup:** N2 with r = 1.0975 Å along z, plus a ghost atom at the centre. The basis is aug-cc-pVTZ on N and 3s3p3d diffuse shells on the ghost. The Q-Chem input uses `EA_STATES` 5 in the B2g irrep and `GUI=2`.
- **CAP:** box with `cap_x = cap_y = 2.76` and `cap_z = 4.88` bohr, 5 states, η from 0 to 0.05 au in 101 steps, and `track_state(1, tracking="energy")`. The reference energy is the CCSD neutral, −109.36195558 Eh.
- **Expected uncorrected result:** 2.638 − 0.196i eV, so the position is about 2.64 eV and Γ is about 0.39 eV, at η_opt = 0.0075.
- **Expected corrected result:** 2.597 − 0.117i eV, so Γ is about 0.23 eV, at η_opt = 0.0165.
- **CAP-EA-ADC(2) from the same tutorial:** uncorrected 2.510 − 0.194i eV and corrected 2.465 − 0.140i eV.
- **Experimental fit for comparison:** about 2.32 eV and Γ about 0.41 eV (quoted in Gyamfi and Jagau). CAP-EOM-CCSD positions sit roughly 0.3 eV high. That is a method error, not a setup error.
- **Most common mistake:** reading Im(E) as Γ. It is −Γ/2, so double it. The second most common is forgetting `ref_energy`, which gives total energies instead of attachment energies.

**2. Same system, onset rule of thumb.** The 2.76/2.76/4.88 bohr box comes from the spatial extent ⟨x²⟩, ⟨y²⟩, ⟨z²⟩ of the neutral ground state (Thodika and Matsika, below). Re-derive the onset for your own molecule from a ground-state ⟨R²⟩ calculation; do not copy N2's numbers.

**3. H2 doubly excited ¹Σg⁺ (Feshbach) state, Psi4 FCI (official tutorial).** Source: `examples/analysis/H2/Psi4H2.ipynb`.
- **Setup:** custom basis with ghost He centres, 15 FCI roots, densities passed via `add_tdm` (both (i, j) and the transposed (j, i)).
- **CAP:** box with `cap_x = cap_y = 6.0` and `cap_z = 6.7` bohr, η from 0 to 0.1 in 201 steps, overlap tracking of state 1.
- **Expected uncorrected result:** 13.236 − 0.152i eV, so Γ is about 0.30 eV, at η = 0.011.
- **Expected corrected result:** 13.229 − 0.058i eV, so Γ is about 0.12 eV, at η = 0.031.
- **Most common mistake:** forgetting the (j, i) transpose, or skipping `check_overlap_mat`, which silently gives a W in the wrong AO order.

**4. N2⁻ with projected CAP-MRCI (literature benchmark).** Thodika and Matsika, "Projected Complex Absorbing Potential Multi-reference Configuration Interaction Approach for Shape and Feshbach Resonances" ([NSF PAR author copy](https://par.nsf.gov/servlets/purl/10376097); published in *JCTC* 2022, citation unverified).
- **Setup:** MRCIS(5,8), box 2.76/2.76/4.88 bohr.
- **Results by basis:** aug-cc-pVTZ+gh[3s3p3d] gives a corrected result of 3.00 eV and Γ = 0.31 eV. Across bases, positions and widths spread by about 0.1 eV.
- **Most common mistake:** quoting one basis without testing the diffuse set.

---

## Known issues and fixes

**Width far too small (or too large) and changes with N.** Cause: too few states in the projection subspace. In N2⁻ with projected CAP-EOM-EA-CCSD, 2 states gave positions within 0.02 eV of full CAP but widths too low by up to 0.07 eV; 5 states cut the width error below 0.02 eV, and 9 states agreed within 0.005 eV. For HCOOH⁻, even 6 states left errors of 0.11–0.22 eV in Γ. Fix: increase `nstates` until both the position and **Γ** stop moving, and plot Γ against N. Source: Gyamfi and Jagau, [arXiv:2312.15798](https://arxiv.org/abs/2312.15798) (Dec 2023), Tables 1–4.

**Results swing with CAP onset or with η.** Cause: optimizing η at a fixed onset depends strongly on the onset chosen, and the logarithmic velocity can have up to four minima in CAP-EOM-EA-CCSD. Fix: scan the onset as well as η (`compute_ao_cap` with a new dict is cheap in projected CAP). Report the global minimum, or fix η and optimize the onset (Gyamfi and Jagau's criterion). Same source.

**Two stabilization points on one trajectory.** Cause: an unphysical stationary point. Fix: rerun with a small `cap_lambda` (CR-CAP), positive or negative, and raise it until one point disappears. Do not push λ too far. Sources: the Thodika and Matsika paper above (Fig. 5) and the OpenCAP theory page.

**Large uncorrected/corrected gap; corrected Γ much smaller.** Cause: the CAP perturbation is a large part of Im(E). At large onset, Im(E) is almost entirely ⟨iηW⟩, which means the "width" is CAP absorption, not decay. Fix: compare `energies_ev(corrected=True)` with the uncorrected values. If the deperturbed width is close to zero, the stationary point is not a resonance. Source: Gyamfi and Jagau, Sec. 4.2.

**Wrong or noisy W; "Verified overlap matrix" missing.** Cause: AO ordering or normalization differs between your code and OpenCAP. This is common with inline PySCF input and cartesian d/f/g functions. Fix: load the system from a Molden file, call `check_overlap_mat`, and for cartesian functions run `compute_ao_cap` → `renormalize_cap(S, "pyscf")` → `compute_projected_cap`. Source: [PySCF interface docs](https://gayverjropencap.readthedocs.io/en/latest/interfaces/pyscf.html).

**`pip install pyopencap` builds from source and fails (Python 3.12).** Cause: no wheel for that Python version at the time. The developer uploaded new wheels on 2025-04-26. Fix: upgrade pip and retry, or use Python 3.10–3.11. Source: [issue #56](https://github.com/gayverjr/opencap/issues/56) (Apr 2025, closed).

**PySCF `eomea_ccsd.py` example fails in `spatial2spin_ea` with a shape mismatch, e.g. (112,) vs (0,224).** Cause: the example appended r1/r2 amplitudes together, which breaks with PySCF 2.5. Fix: convert r1 and r2 (and l1/l2) to spin-orbital form separately, as posted in the thread. Source: [issue #52](https://github.com/gayverjr/opencap/issues/52) (Apr 2024, closed Oct 2024).

**Need the CAP-modified orbitals or a picture of the resonance.** Cause: projected CAP never changes the orbitals; it only mixes real states. Fix: analyze the dominant real EOM states in the mixed eigenvector. If you need orbitals, use a full CAP that starts at HF (e.g. Q-Chem CAP-EOM). For Feshbach (2p-1h) resonances, the developer recommends multireference methods via OpenMolcas or Columbus. Source: issue #52, developer reply on 2024-04-13.

**OpenMolcas parser fails on Heff.** Cause: the output has no "diagonal energies shifted" line. Fix: supply your own `h0_file`, or add that line. Extended MS-CASPT2 variants once needed a fix to the rotation-matrix parser. Sources: issues [#29](https://github.com/gayverjr/opencap/issues/29) and [#31](https://github.com/gayverjr/opencap/issues/31) (Jun 2021, closed).

**Parser chokes on Fortran `D` exponents (1.0D-03).** Fixed in March 2022; upgrade if you are on an old build. Source: [issue #36](https://github.com/gayverjr/opencap/issues/36).

**Grid allocation errors, or numerical integration dies.** Fix: lower `thresh` to drop very diffuse GTOs, or reduce `angular_points` or `radial_precision`. Box CAPs default to analytic integrals, so this mainly affects Voronoi and custom CAPs. Sources: [keywords page](https://gayverjropencap.readthedocs.io/en/latest/keywords.html) and [issue #32](https://github.com/gayverjr/opencap/issues/32) (2021).

**Q-Chem PROJ_CAP=3 rejected for EOM-IP.** Cause: Q-Chem implements projected CAP for EE/EA only. Fix: use full CAP-EOM-IP-CCSD in Q-Chem. Alternatively, export IP densities with `GUI=2` and project them in pyopencap; whether that route works is unverified. Source: Q-Chem 6.3 manual, §7.10.9.

**Unit slips.** Q-Chem `CAP_X 2760` means 2.76 bohr and `CAP_ETA 10` means 1e-4 au. pyopencap takes bohr and au directly (`"2.76"`, and η lists such as `linspace(0, 5000, 101)*1e-5`). Mixing the two conventions gives onsets or η values that are off by a factor of 1000. Source: Q-Chem manual and the OpenCAP tutorial.

**Wrong state tracked.** Cause: `track_state(k)` follows root k from η = 0. Energy tracking can jump between roots at avoided crossings. Fix: use `tracking="overlap"`, plot the whole η trajectory in the complex plane, and confirm the tracked root is the one with resonance character at η = 0.

---

## When projected CAP struggles

**Group case (Ar–water ICD/ETMD).** Projected-CAP widths came out 10²–10⁴ times larger than direct CAP-EOM-CCSD widths and did not converge with the number of states. That pattern fits the mechanisms below. No source I found studies projected CAP for ICD/ETMD directly, so treat the mechanism links as **interpretation (unverified)**.

**1. The subspace may not contain the decay channel.** Projected CAP can only mix the states you computed. An ICD/ETMD resonance is an inner-valence hole that decays into two-hole-one-particle (2h1p) continua. The lowest N EOM roots are often other bound or Rydberg-like states, not a discretized version of that continuum, so the width depends on whichever pseudo-continuum states happen to be included and keeps jumping as N grows. For N2⁻, 9 states were enough; for HCOOH⁻, even 6 were not (Gyamfi and Jagau). For higher-lying resonances, the parameters can vary strongly with subspace size (Thodika and Matsika, introduction). **Check:** whether the included roots have the right symmetry and 2h1p character, and whether Γ converges when you go to 20–40 states. Use `include_states` to test which roots carry the width.

**2. A meV width is smaller than the CAP perturbation.** When Γ is a few meV, the η⟨W⟩ term from diffuse pseudo-continuum states in the subspace can be orders of magnitude larger. The trajectory then stabilizes on CAP absorption, not decay. **Check:** compute the deperturbed or corrected width. If the uncorrected Γ is far larger than the corrected one, or the corrected one is close to zero, the number is not a decay width (Gyamfi and Jagau, Sec. 4.2).

**3. Only total widths.** CAP gives only total widths, not ICD vs ETMD partial widths. A projection-operator or Wigner–Weisskopf method is needed for partials (2016 J. Chem. Phys. helium-trimer paper, from search snippets; unverified).

**4. Q-Chem has no projected CAP for IP.** ICD starts from an ionized state, but Q-Chem's PROJ_CAP is EE/EA only.

**Literature numbers for interatomic decay.** From [arXiv:2305.10186](https://arxiv.org/abs/2305.10186) (2023, complex-basis-function EOM-IP-CCSD for ICD):
- **Ne2 at 3.2 Å:** CAP-EOM-CCSD 7.2 meV, CAP-ADC(2) 7.1 meV, CAP-CI 10.3 meV; experiment 3.3–6.6 meV.
- **NeAr at 3.5 Å:** CAP-EOM-CCSD 37.4 meV against 15.4–18.0 meV (CBF) and 17–22 meV (Fano-ADC). So even full CAP-EOM-CCSD can be about twice too large for heteronuclear ICD.
- **Small widths in general:** CBF is considered reliable down to about 5 meV, and Ne2 widths are very sensitive to the diffuse exponents. Feshbach–Fano EOM-CCSD fails to give the R⁻⁶ distance dependence.

**Remedies, in order of effort.**
1. **Converge `nstates` in large steps** (5, 10, 20, 40) and plot Γ against N. If Γ never plateaus, stop using projected CAP for this state.
2. **Scan the onset as well as η**; compare a box CAP with a Voronoi CAP (Voronoi is better for clusters, per Gayvert and Bravaya 2022); and try CR-CAP λ to remove false stationary points.
3. **Use full (non-projected) CAP-EOM-CCSD** (Q-Chem `COMPLEX_CCMAN`, CS_HF and CS_CCSD true), which the group already found consistent. Optimize the onset as well, and report corrected widths.
4. **Cross-check with a method that does not use a CAP onset:** complex-basis-function EOM-IP-CCSD (Q-Chem `COMPLEX_EXPONENTS`) or Fano-ADC with Stieltjes imaging.
5. **Sanity-check the physics:** an ICD width should follow roughly R⁻⁶ with distance. If the computed widths do not, they are artifacts.

---

## Open questions / could not verify

- Final journal reference for the OpenCAP software paper (J. Phys. Chem. A, 2023): seen only as "submitted" on a CV.
- Journal citations for Gyamfi and Jagau (arXiv:2312.15798) and for the authors and journal of arXiv:2305.10186; I read the arXiv texts only.
- Whether pyopencap gives sensible W from Q-Chem EOM-IP-CCSD densities (`GUI=2`). Neither the docs nor the issues cover IP.
- I found no published study of projected CAP specifically for ICD/ETMD or Ar–water systems. The mechanism analysis above is inference.
- The full text of the Gayvert and Bravaya clusters paper (JPCA 126, 5070) returned 403. The Voronoi recommendation comes from abstract and search snippets.
- `find_eta_opt` default arguments, and whether `check_overlap_mat` or `check_overlap_matrix` is the current name (the docs use both).
