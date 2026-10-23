---
name: cp2k
description: Setting up, converging and running CP2K (Quickstep GPW DFT) - input anatomy (GLOBAL, FORCE_EVAL/DFT, SUBSYS, MOTION), MOLOPT basis + GTH pseudopotential pairing, CUTOFF/REL_CUTOFF convergence, periodic vs isolated systems (Poisson solvers, cell size), SCF problems (OT, smearing for metals, Cholesky failures), hybrids with ADMM, geometry/cell optimization, AIMD (thermostats, timestep, restarts, energy drift), real-time propagation/Ehrenfest and TDDFPT, and running cp2k.psmp on a Slurm cluster such as PACE. Use whenever someone writes or debugs a CP2K input or output, or wants periodic / condensed-phase DFT or AIMD.
---

# CP2K in practice (documented practice)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

**This is general, documented practice, not group experience.** No CP2K notes were found in the group's records, so everything here comes from the CP2K manual, official howtos/exercises and the cp2k-user mailing list. Sources, reference numbers and ~20 known issues are in the `troubleshooting` skill, `references/cp2k.md`. Check that file before guessing at a fix. For choosing a functional or basis in general, see `basics` / `method-selection`.

## 1. When CP2K is the right tool

- **Use CP2K for:** condensed phase and periodic systems (liquids, solids, surfaces, interfaces), AIMD of hundreds of atoms, QM/MM, and real-time / Ehrenfest dynamics in periodic cells. Gaussian + plane-wave (GPW) makes large GGA calculations cheap and scales to many nodes.
- **Prefer Q-Chem** for EOM-CC, CAPs and the group's established excited-state workflows (`eom-cc`); **PySCF** for custom Python methods and TiDES (`tides`); **Psi4** for SAPT / counterpoise / CBS on gas-phase clusters (`psi4`). Small isolated molecules with accurate energetics are usually easier in those codes. If unsure, use `method-selection`.
- CP2K's correlated wavefunction methods and all-electron work exist (GAPW, RI-MP2/RPA) but are not covered here.

## 2. Input anatomy (one file, nested `&SECTION ... &END SECTION`)

- `&GLOBAL`: `PROJECT name` (prefix of every output file), `RUN_TYPE` (`ENERGY`, `ENERGY_FORCE`, `GEO_OPT`, `CELL_OPT`, `MD`, `RT_PROPAGATION`), `PRINT_LEVEL LOW|MEDIUM`.
- `&FORCE_EVAL` → `METHOD Quickstep`, then:
  - `&DFT`: `BASIS_SET_FILE_NAME BASIS_MOLOPT`, `POTENTIAL_FILE_NAME GTH_POTENTIALS`, `CHARGE`, `MULTIPLICITY`, `UKS` (open shell); `&QS EPS_DEFAULT 1e-10`; `&MGRID CUTOFF / REL_CUTOFF`; `&XC` (functional, `&VDW_POTENTIAL` for D3); `&SCF`; `&POISSON`.
  - `&SUBSYS`: `&CELL` (`ABC`, `PERIODIC`), `&COORD` or `&TOPOLOGY COORD_FILE_NAME x.xyz`, and one `&KIND` per element: `BASIS_SET DZVP-MOLOPT-GTH`, `POTENTIAL GTH-PBE-q6`.
- `&MOTION`: `&GEO_OPT`, `&CELL_OPT`, `&MD`, `&PRINT` (trajectory, restart frequency).
- **Pairing rule:** the pseudopotential must match the **functional** (`GTH-PBE-*` for PBE) and the basis's **valence count** (`qN`). UZH sets (`BASIS_MOLOPT_UZH` + `POTENTIAL_UZH`) are the manual's preferred start for new production work.
- **D3:** `&XC/&VDW_POTENTIAL`, `DISPERSION_FUNCTIONAL PAIR_POTENTIAL` (newer alias `POTENTIAL_TYPE`, unverified), `&PAIR_POTENTIAL TYPE DFTD3`, `REFERENCE_FUNCTIONAL PBE`, `PARAMETER_FILE_NAME dftd3.dat`, `R_CUTOFF 16` (keyword spelling: check your version's input reference).
- `cp2k.psmp -i x.inp -o x.out`: `-o` **appends**; delete the old output first.

## 3. Convergence checks you must do

1. **CUTOFF and REL_CUTOFF** for each new system/basis: scan `CUTOFF` at fixed `REL_CUTOFF 60`, then `REL_CUTOFF` at the chosen `CUTOFF` (official howto, Starter 1 in the reference). Raise them together. Target ~1e-6 Ha/atom or better on energies; check forces too for MD/optimizations.
2. **Cell / vacuum for isolated or slab systems:** `PERIODIC NONE` in **both** `&CELL` and `&POISSON`; MT solver needs a cell ≥ 2× the density extent, WAVELET a few Å per side. Grow only the non-periodic directions until energies/forces stop changing.
3. **Basis:** DZVP-MOLOPT for screening; check key results with TZV2P-MOLOPT (or UZH TZ). Use `-SR` variants in dense systems to avoid ill-conditioning.
4. **Metals:** also converge smearing temperature and k-points (or supercell size).

## 4. SCF playbook (in order)

1. Check the structure, `CHARGE`, `MULTIPLICITY`, `UKS`. Odd electron count needs `UKS`.
2. **Insulators/molecules/water:** OT + outer loop:
   `&OT MINIMIZER DIIS PRECONDITIONER FULL_SINGLE_INVERSE &END` (or `FULL_ALL`), `MAX_SCF 20–30`, `&OUTER_SCF MAX_SCF 10 EPS_SCF` (same as inner) `&END`.
3. **Metals / small gap:** diagonalization + smearing, not classic OT:
   `&DIAGONALIZATION ALGORITHM STANDARD`, `ADDED_MOS` (enough empty bands), `&SMEAR METHOD FERMI_DIRAC ELECTRONIC_TEMPERATURE 300–1000`, `&MIXING METHOD BROYDEN_MIXING ALPHA 0.1–0.2 NBROYDEN 8`.
4. Better guess: `SCF_GUESS RESTART` + `WFN_RESTART_FILE_NAME` from a cheaper converged run (e.g. GGA before hybrid).
5. Tighten `EPS_DEFAULT` (1e-12) or raise the cutoff; noisy integrals hurt convergence.
6. "Cholesky decomposition failed": smaller / `-SR` basis, lower `EPS_DEFAULT`, other preconditioner.
7. Since 2024.1 an unconverged SCF aborts the run. `IGNORE_CONVERGENCE_FAILURE` only as a last resort, and say so when reporting.

**Hybrids:** `&HF FRACTION 0.25` + `&AUXILIARY_DENSITY_MATRIX_METHOD` + an `AUX_FIT` basis per kind; `&HF/&MEMORY MAX_MEMORY` is MB **per MPI rank**. With diagonalization/smearing use `ADMM_PURIFICATION_METHOD NONE`.

## 5. AIMD recipe

1. Optimize (or pre-equilibrate with a force field) so no atoms are too close.
2. **NVT equilibration:** `ENSEMBLE NVT`, `&THERMOSTAT TYPE CSVR`, `&CSVR TIMECON 100` (50 for fast heating), `TIMESTEP 0.5` fs (H-rich; up to ~1 fs otherwise), `&QS EXTRAPOLATION ASPC EXTRAPOLATION_ORDER 3`, `EPS_SCF 1e-6` or tighter. Heat in stages if far from target.
3. **Production:** NVT with gentler `TIMECON` (≥200 fs), or NVE for dynamics/spectra. Discard the equilibration part (the school exercise discards ~1/3).
4. **Restarts:** `&MOTION/&PRINT/&RESTART` every N steps with `BACKUP_COPIES 3`. Continue with `&EXT_RESTART RESTART_FILE_NAME project-1.restart` + `SCF_GUESS RESTART`. Without `&EXT_RESTART` the run starts over.
5. **Check in `project-1.ener`:** col. 4 temperature fluctuates around the target; col. 6 (conserved quantity) has no drift. Test the timestep with a short NVE run first. Drift → tighter SCF, higher cutoff, smaller timestep.

**Real-time / Ehrenfest (briefly):** `RUN_TYPE RT_PROPAGATION` (or Ehrenfest run type), `&DFT/&REAL_TIME_PROPAGATION` with `INITIAL_WFN SCF_WFN`, `MAT_EXP`, `EPS_ITER`; attosecond timesteps; length gauge only for isolated systems, velocity gauge for periodic. **TDDFPT:** `&PROPERTIES/&TDDFPT NSTATES n`, ADMM for hybrids. Details and references in `references/cp2k.md`.

## 6. Running on a cluster

- `cp2k.psmp` = MPI + OpenMP (use this), `cp2k.ssmp` = one node, OpenMP only.
- **Always** `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`; ranks × threads = cores allocated. Unset threads oversubscribe and can make runs many times slower. Start with 2–4 threads per rank and time a few MD steps or SCF cycles.
- Fewer ranks with more threads uses less memory. A job killed with no message is usually out of memory; for hybrids lower `MAX_MEMORY` or use fewer ranks.
- `srun cp2k.psmp -i x.inp -o x.out` with the MPI module CP2K was built with (repeated "Number of processes 1" lines = wrong MPI).
- Set `WALLTIME` in `&GLOBAL` a bit under the Slurm limit so CP2K writes restart files cleanly.
- Partitions, memory, scratch, job arrays and why jobs pend: see `pace-slurm`. Propose the sbatch script and wait for an OK.

## 7. Pitfalls

- Pseudopotential from a different functional or `qN` than the basis.
- `PERIODIC NONE` in `&CELL` but not `&POISSON` (or vice versa); `&CELL` defaults to periodic XYZ.
- Reusing cutoffs from another system; raising `CUTOFF` without `REL_CUTOFF`.
- Smearing with classic OT; forgetting `ADDED_MOS` with smearing; quoting total energy instead of free energy with smearing.
- Charged periodic cells: energy depends on cell size; compare only like with like.
- Tight GEO_OPT / frequencies at low cutoff (egg-box noise).
- Reading an appended `-o` output, or a `.wfn` from a different basis/version.
- Before quoting any number, use `reporting-computational-results`.

## 8. Group lessons

**None yet.** A search of the group's notes (2026-10-22) found no CP2K mentions. Add lessons here, marked as group experience, as they come up.

## 9. Not verified yet

- CP2K module(s) and versions on PACE, best ranks × threads per node, and a tested sbatch: unknown.
- Exact Ehrenfest run-type name and RTP propagator / delta-pulse keywords in the installed version.
- Whether the installed release supports direct OT with smearing.
- Typical converged cutoff for water with MOLOPT (often quoted 300–400+ Ry; must be checked per system).
