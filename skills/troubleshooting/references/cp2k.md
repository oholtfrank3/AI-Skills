# CP2K (2024.x–2026.x): troubleshooting reference

Last researched: 2026-10-22

**How to use this file:** find your symptom in "Known issues and fixes", check the cause against your output file, apply the fix, and run a starter calculation on the same machine before trusting production. This is documented practice from the manual, howtos and mailing list, not group experience. The short version lives in `skills/cp2k/SKILL.md`. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official documentation

**Manual (methods + input reference).** <https://manual.cp2k.org/trunk/index.html> is the development manual; versioned copies exist (latest release at time of reading: 2026.2, <https://manual.cp2k.org/cp2k-2026_2-branch/index.html>; 2024.2 input reference: <https://manual.cp2k.org/cp2k-2024_2-branch/CP2K_INPUT.html>). Check `cp2k.psmp --version` and read the matching manual: keywords move between releases. Many old cp2k.org howtos now redirect into the manual.

**Input anatomy.** <https://www.cp2k.org/howto:static_calculation> (8-atom Si, written for CP2K 2.4 but still the clearest walk-through).
- `&GLOBAL`: `PROJECT` (prefix for all output files), `RUN_TYPE` (`ENERGY`, `ENERGY_FORCE`, `GEO_OPT`, `CELL_OPT`, `MD`, `RT_PROPAGATION`, ...), `PRINT_LEVEL`.
- `&FORCE_EVAL`: `METHOD Quickstep` (GPW DFT). Inside: `&DFT` (`BASIS_SET_FILE_NAME`, `POTENTIAL_FILE_NAME`, `CHARGE`, `MULTIPLICITY`, `UKS`, `&QS`, `&MGRID`, `&XC`, `&SCF`, `&POISSON`) and `&SUBSYS` (`&CELL`, `&COORD` or `&TOPOLOGY`, one `&KIND` per element with `BASIS_SET` and `POTENTIAL`).
- `&MOTION`: `&GEO_OPT`, `&CELL_OPT`, `&MD`, `&PRINT` (trajectory, restart frequency).
- `-o out` **appends** to an existing file; delete old output first.

**GPW and the grid.** <https://manual.cp2k.org/trunk/methods/dft/gpw.html>, cutoff howto <https://manual.cp2k.org/trunk/methods/dft/cutoff.html>.
- Orbitals are Gaussians; the density is put on multigrids (`NGRIDS`, default 4). `CUTOFF` (Ry) sets the finest grid; `REL_CUTOFF` (Ry) decides which grid each Gaussian goes on. Raising `CUTOFF` without `REL_CUTOFF` can push Gaussians onto coarse grids and hurt accuracy; raise them together.
- Converge both for every new system/basis (Starter 1). AIMD can use slightly looser grids than final property runs, but too loose gives noisy forces and drift (MD page).

**Basis sets and pseudopotentials.** <https://manual.cp2k.org/trunk/methods/dft/basis_sets.html>
- Typical GPW choice: `DZVP-MOLOPT-GTH` or `TZV2P-MOLOPT-GTH` (`BASIS_MOLOPT`), `-SR` variants are less diffuse and cheaper for condensed phase. The manual now calls the **UZH protocol** (`BASIS_MOLOPT_UZH` + `POTENTIAL_UZH`) the preferred start for new production inputs.
- The pseudopotential must match the **functional** (`GTH-PBE-q6` for PBE, `GTH-BLYP-q6` for BLYP, `GTH-HYB-*` for hybrids in UZH) and the basis's **valence count** (`qN` = number of valence electrons). Example: O with `DZVP-MOLOPT-GTH` + `GTH-PBE-q6`.
- Extra roles: `BASIS_SET AUX_FIT ...` (ADMM), `RI_AUX` (RI methods).

**SCF.** <https://manual.cp2k.org/trunk/methods/dft/convergence.html>, OT <https://manual.cp2k.org/trunk/methods/dft/orbital_transformation.html>
- **Insulators / molecules / water:** OT (`&OT`, `MINIMIZER CG` default, or `DIIS`; `PRECONDITIONER FULL_SINGLE_INVERSE` or `FULL_ALL`) with `&OUTER_SCF`. Manual: inner `MAX_SCF` ~16–32, outer `MAX_SCF` ~8–16.
- **Metals / small gap:** `&DIAGONALIZATION` + `&SMEAR` (Fermi-Dirac) + `ADDED_MOS` + `&MIXING BROYDEN_MIXING`. Classic OT cannot use smearing; newer releases allow direct OT with smearing only with `ROTATION` + `ENERGIES` (OT page; check your version).
- Since **2024.1** an unconverged SCF **aborts** by default (`IGNORE_CONVERGENCE_FAILURE` exists; manual warns results may be wrong).
- `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME` to start from a converged (cheaper) wavefunction.

**Electrostatics / periodicity.** <https://manual.cp2k.org/trunk/methods/dft/electrostatics/index.html>
- `&CELL PERIODIC` and `&POISSON PERIODIC` should match. Bulk: `PERIODIC XYZ`, solver `PERIODIC`.
- Isolated molecule: `PERIODIC NONE` in both, `POISSON_SOLVER MT` (cell ≥ 2× the density extent; MT "can return completely wrong results" otherwise), or `WAVELET` (needs less vacuum), or `MULTIPOLE`. A cell is always required, even with `PERIODIC NONE`.
- Slabs: `PERIODIC XY` with `ANALYTIC` or `IMPLICIT` (or a 2D-capable solver).
- Charged periodic cells get a uniform neutralizing background; energies depend on cell size. Compare only runs with the same convention.

**Hybrids and ADMM.** <https://manual.cp2k.org/trunk/methods/dft/hartree-fock/admm.html>
- `&XC/&HF` (e.g. `FRACTION 0.25`) plus `&AUXILIARY_DENSITY_MATRIX_METHOD` (`ADMM_TYPE ADMM2/ADMMS/...`, `EXCH_CORRECTION_FUNC PBEX` for PBE-based hybrids) and an `AUX_FIT` basis per kind from `BASIS_ADMM_MOLOPT` / `BASIS_ADMM_UZH` (or the older `BASIS_ADMM` file with `cFIT3` / `admm-dzp`; unverified naming per element).
- `&HF/&MEMORY MAX_MEMORY` is **MB per MPI rank** for stored integrals; `&SCREENING EPS_SCHWARZ`; periodic hybrids need `&INTERACTION_POTENTIAL` (`TRUNCATED`, `CUTOFF_RADIUS` < half the shortest cell length, `T_C_G_DATA t_c_g.dat`) (unverified detail: from the input reference, not re-read).
- Start a hybrid from a converged GGA wavefunction (`SCF_GUESS RESTART`).

**MD / AIMD.** <https://manual.cp2k.org/trunk/methods/sampling/molecular_dynamics.html>
- `ENSEMBLE NVE | NVT | NPT_I | NPT_F | LANGEVIN`. Thermostat: **CSVR** recommended for equilibration and production; `TIMECON` ~50 fs (fast heating), 100 fs (default choice), ≥200 fs (gentle production). Avoid `TEMP_TOL` rescaling for production.
- Timestep 0.5–1.0 fs with light atoms (smaller for hot or H-rich systems). Validate with a short NVE run.
- `&QS EXTRAPOLATION ASPC`, `EXTRAPOLATION_ORDER 3` (default family, good start).
- `project-1.ener` columns: step, time [fs], E_kin, temp [K], E_pot, E_tot (conserved quantity for NVT), time/step.
- Restarts: CP2K writes `project-1.restart` (full input with current positions/velocities/thermostat) and `project-RESTART.wfn`. Continue with `&EXT_RESTART RESTART_FILE_NAME project-1.restart` (or run the `.restart` file directly) and `SCF_GUESS RESTART` (unverified exact defaults; see the restarting guide in the manual).

**Real-time propagation / Ehrenfest.** <https://manual.cp2k.org/trunk/methods/sampling/ehrenfest.html>
- `RUN_TYPE RT_PROPAGATION` (fixed nuclei) or `EHRENFEST_DYN` (moving nuclei; name from the input reference, unverified on this page). `&DFT/&REAL_TIME_PROPAGATION`: `INITIAL_WFN SCF_WFN | RESTART_WFN | RT_RESTART`, `MAT_EXP` (`ARNOLDI`, `TAYLOR`, `PADE`, ...), `EPS_ITER` (1e-11 in the example), `MAX_ITER`.
- Timestep must resolve electrons: attoseconds (example 0.00078 fs). Fields via `&EFIELD`; length gauge only for isolated systems, velocity gauge for periodic. Dipoles via `&PRINT/&MOMENTS`.
- TDDFPT (linear response): <https://manual.cp2k.org/trunk/methods/properties/optical/tddft.html> (not read in detail).

**QM/MM.** <https://manual.cp2k.org/trunk/methods/qm_mm/index.html> (`METHOD QMMM`, built-in force field or GROMACS coupling; not read in detail).

**Running in parallel.** <https://manual.cp2k.org/trunk/getting-started/troubleshooting.html>
- `cp2k.psmp` = MPI + OpenMP; `cp2k.ssmp` = OpenMP only (single node); `popt` = pure MPI (older builds).
- Always set `OMP_NUM_THREADS` explicitly; ranks × threads = cores you were given. Fewer ranks with more threads lowers memory.
- Killed with no message usually = out of memory: use fewer ranks / more threads, lower HFX `MAX_MEMORY`.
- Repeated identical output lines (`DBCSR| MPI: Number of processes 1` many times) = wrong `mpirun` for the binary; check `which mpirun`, `ldd cp2k.psmp`.

---

## Starter calculations

**1. Cutoff convergence, 8-atom bulk Si (official howto).** <https://manual.cp2k.org/trunk/methods/dft/cutoff.html> (old URL <https://www.cp2k.org/howto:converging_cutoff> redirects, 2024-05).
- **Input:** cubic Si8, a = 5.4306975 Å, `SZV-GTH-PADE` + `GTH-PADE-q4`, PADE LDA, `NGRIDS 4`, `RUN_TYPE ENERGY`. Scan `CUTOFF` 50–500 Ry at `REL_CUTOFF 60`, then `REL_CUTOFF` 10–100 Ry at `CUTOFF 250`. The howto uses `MAX_SCF 1` (same guess each run, so only the grid changes).
- **Expected:** E ≈ −32.38045548 Ha once converged; changes < 1e-8 Ha for `CUTOFF ≥ 250`, `REL_CUTOFF ≥ 60`. Recommended `CUTOFF 250`, `REL_CUTOFF 60`. Also read the "Gaussians per grid" counts: no grid should be empty, and the finest grid should hold few Gaussians.
- **Resources:** 1–2 cores, seconds per point.
- **Common mistake:** treating these numbers as universal. Every new element/basis/pseudopotential needs its own scan (water with MOLOPT typically ends up at 300–400+ Ry, unverified as a general rule). Also scanning `CUTOFF` while leaving `REL_CUTOFF` too low.

**2. Static energy of Si8 with DZVP (official howto).** <https://www.cp2k.org/howto:static_calculation> (written for CP2K 2.4).
- **Input:** as above but `DZVP-GTH-PADE`, `CUTOFF 300`, `REL_CUTOFF 60`, `EPS_DEFAULT 1e-10`, diagonalization + Broyden mixing (`ALPHA 0.4`), `EPS_SCF 1e-7`, `RUN_TYPE ENERGY_FORCE`.
- **Expected:** converges in ~10 SCF steps; total energy ≈ −31.2978852 Ha; forces ~1e-8 au; integrated density 32 electrons. With Fermi-Dirac 300 K + `ADDED_MOS 10`: free energy ≈ −31.2978870 Ha.
- **Common mistake:** `-o` appends to an old output, so you read the wrong energy. With smearing, forgetting `ADDED_MOS`.

**3. Single water molecule: energy and geometry optimization (manual + exercise).** <https://manual.cp2k.org/trunk/getting-started/first-calculation.html>, <https://www.cp2k.org/exercises:common:geo_opt> (2024-02).
- **Input:** H2O in a 10 Å cube, `PERIODIC NONE` in both `&CELL` and `&POISSON` (`PSOLVER MT` in the manual, `WAVELET` in the exercise), PBE, `DZVP-MOLOPT-GTH`, `GTH-PBE-q6` (O) / `GTH-PBE-q1` (H), `CUTOFF 400`, `REL_CUTOFF 50`, `EPS_SCF 1e-6`. For the optimization: `RUN_TYPE GEO_OPT`, `&MOTION/&GEO_OPT OPTIMIZER BFGS`, `&CENTER_COORDINATES`.
- **Expected:** the manual gives no reference energy. Exercise (WAVELET, its own settings): step-1 energy −14.9417142787 Ha (unverified for other settings). Default GEO_OPT criteria: max step 3e-3, RMS step 1.5e-3, max gradient 4.5e-4, RMS gradient 3e-4 (bohr / Ha/bohr); all four must be met. Result in `H2O-pos-1.xyz` (last frame).
- **Resources:** 1–4 cores, under a minute.
- **Common mistake:** setting `PERIODIC NONE` in only one of `&CELL`/`&POISSON`, or a cell that is too small for MT (needs ≥ 2× the density extent; 10 Å is borderline for MT, fine for WAVELET). Run a frequency calculation before calling it a minimum.

**4. Bulk liquid water AIMD, 64 H2O (CP2K school exercise).** <https://www.cp2k.org/_export/raw/exercises:2015_pitt:aimd>
- **Input:** 64 H2O, cubic 12.42 Å, PBE + D3 (`&VDW_POTENTIAL` with `DISPERSION_FUNCTIONAL PAIR_POTENTIAL`, `&PAIR_POTENTIAL TYPE DFTD3`, `REFERENCE_FUNCTIONAL PBE`, `PARAMETER_FILE_NAME dftd3.dat`, `R_CUTOFF 16`), DZVP-GTH, `CUTOFF 400`, `EPS_DEFAULT 1e-10`, `EXTRAPOLATION ASPC`, OT (`MINIMIZER DIIS`, `PRECONDITIONER FULL_SINGLE_INVERSE`, `MAX_SCF 30`, `EPS_SCF 1e-6`) with `OUTER_SCF` (`MAX_SCF 10`, same `EPS_SCF`). `ENSEMBLE NVT`, 300 K, `TIMESTEP 0.5`, GLE thermostat (CSVR is the manual's general recommendation). Restart file every step, `BACKUP_COPIES 3`.
- **Expected:** first step 300 K, E_pot ≈ −1102.63 Ha, conserved ≈ −1102.36 Ha; ~70 s for step 1 then ~11.6 s/step on the school machine. Conserved quantity (col. 6 of `.ener`) must not drift; temperature and E_pot fluctuate around a mean. Discard ~1/3 as equilibration. Properties need tens of ps.
- **Resources:** one node; hours for a few ps.
- **Common mistake:** restarting without `&EXT_RESTART` (run starts from scratch); inner and outer `EPS_SCF` mismatched; using DZVP-GTH for production (the exercise says use TZV2P-type); judging drift with loose `EPS_SCF`.

**Optional: TDDFPT acetone (manual).** <https://manual.cp2k.org/trunk/methods/properties/optical/tddft.html>. PBE0/ADMM, 14 Å box, `PERIODIC NONE`, wavelet, `DZVP-MOLOPT-PBE0-GTH` + `admm-dzp`. Full kernel: S1 dark at 4.67815 eV; state 4 at 9.70094 eV, f = 0.118663.

---

## Group lessons (from local notes)

**None found.** A search of `/Users/owenhf/Documents/pace_snapshot_2026-10-04` (all `*.md`, `writing_materials/agent_messages/*`, and every text file) for "cp2k"/"CP2K" returned no hits (2026-10-22). Everything in this file is documented practice.

---

## Known issues and fixes

1. **"SCF run NOT converged", run aborts (2024.1+).** Cause: since 2024.1 an unconverged SCF stops the job by default. Fix: check structure, `CHARGE`, `MULTIPLICITY`, `UKS` first; then OT + `OUTER_SCF` (inner 16–32, outer 8–16), better guess (`SCF_GUESS RESTART` from a cheaper run). `IGNORE_CONVERGENCE_FAILURE` only as a last resort. <https://manual.cp2k.org/trunk/methods/dft/convergence.html>.
2. **SCF energy oscillates (metal, small gap) with diagonalization.** Fix: Fermi-Dirac smearing with a higher `ELECTRONIC_TEMPERATURE` (300 K default may be too low), lower Broyden `ALPHA` (~0.1), tighter `EPS_DEFAULT`. Developer note: smearing is not compatible with (classic) OT. <https://lists.cp2k.org/archives/cp2k-user/2025-November/022037.html> (2025-11).
3. **Metal surface will not converge with diagonalization + smearing.** Fix that worked: more `ADDED_MOS` (500 for the Rh slab), `BROYDEN_MIXING ALPHA 0.1 BETA 1.5 NBROYDEN 8`, `SCF_GUESS RESTART`; `WINDOW_SIZE` is not a Fermi-Dirac keyword. <https://groups.google.com/g/cp2k/c/MXYYuJmf1s0> (2009-12; old but the recipe is still standard).
4. **Smearing requested together with OT.** Cause: classic OT uses fixed occupations. Fix: use `&DIAGONALIZATION` + `&MIXING` with `&SMEAR`, or (newer releases) direct OT with `ROTATION` + `ENERGIES` + `ADDED_MOS AUTO`. #2 thread; <https://manual.cp2k.org/trunk/methods/dft/orbital_transformation.html>.
5. **"Cholesky decomposition failed" (OT preconditioner).** (unverified: from search summaries) Cause: overlap matrix near singular, usually a too large / too diffuse basis (TZ+, def2 with diffuse functions) in a dense system. Fix: `-SR` MOLOPT basis or smaller basis; lower `EPS_DEFAULT` (e.g. 1e-12) or `EPS_PGF_ORB`; try another `PRECONDITIONER`. <https://www.cp2k.org/faq:cholesky_decomp_failed> (2020-08), <https://lists.cp2k.org/archives/cp2k-user/2019-October/012348.html> (2019-10, read via search summary).
6. **"Basis-set and pseudo-potential ... optimized for different valence electron numbers".** (unverified: from search summaries) Cause: `qN` of the potential does not match the basis (e.g. Pt `GTH-PBE-q10` with a q18 MOLOPT basis). Fix: use the matching potential (here q18) or a basis built for that q. <https://lists.cp2k.org/archives/cp2k-user/2023-May/018798.html> (2023-05; maintainer reply read via search summary only).
7. **"Potential ... not found" although the element is in the file.** (unverified: from search summaries) Cause: name typo, wrong `POTENTIAL_FILE_NAME`, or data directory not found. Fix: check exact spelling (`GTH-PBE-q6`), set `CP2K_DATA_DIR` or copy the file next to the input. Also pair the functional: `GTH-PBE` for PBE, `GTH-BLYP` for BLYP. (Search summary of a 2026-07 Google Groups thread; unverified.)
8. **Isolated molecule gives odd energies, or run hangs after a "too close" warning.** Cause: `&CELL PERIODIC` defaults to XYZ, so the molecule was periodic, and the cell was tiny. Fix: `PERIODIC NONE` in both `&CELL` and `&POISSON`, `POISSON_SOLVER MT`, cell ≈ 2× the molecule in every direction (a cell is always required). <https://lists.cp2k.org/archives/cp2k-user/2022-July/017157.html> (2022-07), electrostatics page.
9. **MT solver results are wrong / change with box size.** Cause: density extends past half the cell. Fix: enlarge the cell (≥ 2× density extent) or use `WAVELET` (needs a few Å of vacuum per side). Check density decays at the boundary. Electrostatics manual page.
10. **Charged system energies change with cell size.** Cause: periodic solver adds a neutralizing background; finite-size error decays slowly. For slabs/wires with net charge there is no clean limit. Fix: compare only runs with the same cell and convention; use a 0D solver for isolated ions. Electrostatics manual page.
11. **Energy changes when a molecule is translated; GEO_OPT or frequencies will not converge tightly.** Cause: egg-box (grid ripple) effect of GPW. Fix: raise `CUTOFF` (and `REL_CUTOFF`); tighten `EPS_DEFAULT`/`EPS_SCF`. MD is less affected because forces are consistent with the ripples. <https://lists.cp2k.org/archives/cp2k-user/2022-June/016994.html> (2022-06).
12. **Hybrid (HFX) job dies early with no message, or is extremely slow.** Cause: `&HF/&MEMORY MAX_MEMORY` is MB **per MPI rank**; too high crashes the node, too low recomputes integrals every step. Fix: set `MAX_MEMORY` to fit (node memory / ranks minus room for the rest of CP2K); aim for 0 integrals "calculated on the fly" in the output; restart from converged PBE wfn; `SCREEN_ON_INITIAL_P T`; `ulimit -s unlimited`. <https://lists.cp2k.org/archives/cp2k-user/2020-November/014359.html> (2020-11).
13. **Warning "Kohn-Sham matrix not 100% occupied" (hybrids).** Fix suggested: lower `EPS_PGF_ORB` and `EPS_FILTER_MATRIX`. Same thread as #12.
14. **ADMM with diagonalization/smearing fails or forces missing.** Cause: default purification (`MO_DIAG`) works only with OT. Fix: `ADMM_PURIFICATION_METHOD NONE` with non-OT SCF. Do not compare energies across different ADMM variants. <https://lists.cp2k.org/archives/cp2k-user/2015-March/006198.html> (2015-03; check current version, newer `ADMM_TYPE` options exist).
15. **psmp run much slower with more ranks, odd timings.** Cause: `OMP_NUM_THREADS` unset, so each MPI rank spawns one thread per core (oversubscription). Fix: always export `OMP_NUM_THREADS`, ranks × threads = cores, bind ranks. <https://lists.cp2k.org/archives/cp2k-user/2019-March/011429.html> (2019-03).
16. **Same lines printed many times; "Number of processes 1".** Cause: `mpirun` from a different MPI than CP2K was built with. Fix: `which mpirun`, `ldd cp2k.psmp`, load the matching module. <https://manual.cp2k.org/trunk/getting-started/troubleshooting.html>.
17. **Job killed, no error (not HFX).** Cause: usually out of memory. Fix: fewer MPI ranks with more OpenMP threads; if diagonalization crashes, try `PREFERRED_DIAG_LIBRARY SCALAPACK` (ELPA bugs). Same troubleshooting page.
18. **MD "restart" starts from step 0 with new velocities.** Cause: no `&EXT_RESTART`. Fix: `&EXT_RESTART` with `RESTART_FILE_NAME project-1.restart` (defaults restore positions, velocities, thermostat, counters) plus `SCF_GUESS RESTART`. <https://www.cp2k.org/_export/raw/exercises:2015_pitt:aimd>, <https://manual.cp2k.org/trunk/methods/restarting.html>.
19. **Wavefunction restart rejected ("number of MOs do not match") or ignored.** (unverified: from search summaries) Cause: `.wfn` from a different basis/system/settings or CP2K version (files are binary and version-specific). Fix: restart only with identical basis, functional, atoms; otherwise start from `ATOMIC`. Restarting page; <https://lists.cp2k.org/archives/cp2k-user/2015-August/006822.html> (2015-08, read via search summary).
20. **AIMD conserved quantity drifts.** Cause: loose `EPS_SCF`/`EPS_DEFAULT`, too-low cutoff (noisy forces), or timestep too large for H. Fix: tighten SCF, raise cutoff, `TIMESTEP 0.5`, test in NVE; tune `EXTRAPOLATION_ORDER`. MD manual page; Pitt AIMD exercise.

---

## Open questions / could not verify

- No CP2K run has been tested on PACE: module name/version, best ranks × threads per node, and a working sbatch are unknown.
- No official reference total energy for the single-water example (manual gives none); Starter 3 numbers are exercise-specific.
- Exact `EHRENFEST_DYN` run-type name and RTP `PROPAGATOR` / delta-pulse keywords: from memory of the input reference, not re-read.
- HFX `INTERACTION_POTENTIAL TRUNCATED` / `CUTOFF_RADIUS` rule (< half cell) and `t_c_g.dat`: standard practice, not re-read this session.
- Whether direct OT with smearing (`ROTATION` + `ENERGIES`) is in 2024/2025 releases or only newer ones.
- Matter Modeling SE: search returned no CP2K threads; not covered.
- QM/MM and k-points: pages listed but not read.
