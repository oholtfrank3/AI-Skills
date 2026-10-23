---
name: psi4
description: Setting up and running Psi4 (free, open-source quantum chemistry) - conda install, psithon vs Python (PsiAPI) inputs, memory/threads/PSI_SCRATCH, SCF/DFT, optimizations and frequencies, SAPT (SAPT0, sSAPT0, SAPT2+, F-SAPT), counterpoise and n-body interaction energies (bsse_type), CBS extrapolation, DLPNO-CCSD(T), and running Psi4 on a Slurm cluster such as PACE. Use whenever someone wants to use Psi4 or asks how to do SAPT, counterpoise or CBS with it.
---

# Psi4 in practice (documented practice)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

**This is general, documented practice, not group experience.** The group has used Psi4 very little, so everything here comes from the Psi4 manual and forum. Sources, reference numbers and a longer list of known issues are in the `troubleshooting` skill, `references/psi4.md`. Check that file before guessing at a fix. For choosing a functional or basis, or what counterpoise means, see `basics` (§2–3); this skill only covers how to do it in Psi4.

## 1. When Psi4 is the right tool

- **Use Psi4 for:** SAPT energy decomposition (SAPT0 to SAPT2+3, F-SAPT for parts of one molecule), automatic counterpoise / many-body interaction energies (`bsse_type`), and CBS extrapolations or focal-point schemes in one line. It is free, open source and installs with conda, so it also suits laptops and teaching.
- **Prefer Q-Chem** for EOM-CC excited states, CAPs and the group's established workflows (`eom-cc`). **Prefer PySCF** for custom Python methods and for TiDES (`tides`). If unsure, use `method-selection`.
- Psi4 runs on **one node only** (threads, no MPI). Very large jobs need a different code or a cheaper method.

## 2. Install and run on a cluster

- **Install** in a fresh conda env from conda-forge (not the old `psi4` channel):
  `conda create -n p4env psi4 -c conda-forge/label/libint_dev -c conda-forge`
  Add dispersion packages if you use `-d3bj` or `-d4` (`dftd3-python`/`simple-dftd3`, `dftd4-python` from conda-forge), then check with `qcengine info`.
- **Two input styles.** Psithon: an input file run as `psi4 -i in.dat -o out.dat -n 8`. PsiAPI: a Python script with `import psi4`. Pick one; do not mix their thread settings.
- **Threads:** psithon `psi4 -n $SLURM_CPUS_PER_TASK`; PsiAPI `psi4.set_num_threads(n)`. Never more threads than cores you were given. Speed comes from threaded BLAS, so beyond ~16 threads gains are usually small.
- **Memory:** `memory 8 GB` (psithon) or `psi4.set_memory('8 GB')`. The default is only 500 MiB. It is the total for the job. Give Psi4 about 85–90 % of what you request from Slurm, because real use is a bit higher than the setting.
- **Scratch:** `export PSI_SCRATCH=` a node-local directory before Psi4 starts. The default `/tmp` can fill up ("PSIO Error"), and network disks are slow. Use one scratch directory per job.
- **Slurm:** one node, `--ntasks=1 --cpus-per-task=N`. Sizing, partitions, node-local scratch and job control are in `pace-slurm`. Propose the job script and wait for an OK.

## 3. Core recipes (psithon)

Start every input with `memory ...` and a `molecule {...}` block (Ångström by default). Run the cheap version first.

- **SCF / DFT single point:** `set basis def2-tzvp` then `energy('wb97x-d')` or `energy('b3lyp-d3bj')`. Open shell: `set reference uhf` (and charge/multiplicity on the first molecule line).
- **Optimize + frequencies:** `optimize('b3lyp-d3bj')` then `frequency('b3lyp-d3bj')` at the same level. If optking struggles, try `optimize(..., engine='geometric')`.
- **Counterpoise interaction energy:** split the fragments with `--` in the molecule block, then `energy('mp2', bsse_type=['cp', 'nocp'])`. The return value is the **interaction energy in Hartree** (first `bsse_type` in the list); both are stored as variables (`CP-CORRECTED INTERACTION ENERGY`).
- **SAPT:** two fragments separated by `--`, Cartesian coordinates, `symmetry c1`, `no_reorient`, `no_com`. `set basis jun-cc-pvdz` then `energy('sapt0')` (sSAPT0 is printed too). Higher levels: `energy('sapt2+')`, usually with aug-cc-pVDZ. Only SAPT0 handles open-shell fragments (`reference rohf` or `uhf`). For functional groups within one molecule use F-SAPT (`fisapt0`). When answering, give one plain line per term: electrostatics (the charge clouds attracting or repelling), exchange (Pauli repulsion where they overlap), induction (each molecule polarizing the other), dispersion (correlated electron motion, the van der Waals attraction). Also suggest checking a known system against published SAPT values (e.g. S22/S66) before trusting new numbers.
- **CBS:** `energy('mp2/aug-cc-pv[tq]z + D:ccsd(t)/aug-cc-pvdz')`. Basis sets in brackets must be consecutive zeta levels. Combining it with `bsse_type='cp'` should give a CP-corrected CBS interaction energy (unverified; test on a small dimer first).
- **CCSD(T) / DLPNO:** `energy('ccsd(t)')` for small systems; `energy('dlpno-ccsd(t)')` with `set pno_convergence tight` for larger closed-shell systems (RHF, C1 only).
- **Orbitals for viewing:** `E, wfn = energy('scf', return_wfn=True)` then `fchk(wfn, 'out.fchk')` or `molden(wfn, 'out.molden')`.
- **First run:** reproduce a starter calculation from `references/psi4.md` (e.g. water SCF/cc-pVDZ = −76.02663 Eh, or the SAPT0 ethene···ethyne test) on the same machine.

## 4. Pitfalls

- **Forgetting `memory`:** the 500 MiB default makes large jobs slow or fail.
- **Unset `PSI_SCRATCH`:** "Fatal Error: PSIO Error" usually means the scratch disk filled up.
- **Oversubscribing threads** or using `mpirun`: slower, not faster.
- **SCF not converging:** check the geometry first, then `damping_percentage 20.0`, `basis_guess true`, `soscf true` in `set scf {...}`. Raising `maxiter` alone rarely helps.
- **SAPT with Z-matrix input** can give wrong energies or crash. Use Cartesians.
- **Missing dispersion package:** `-d3bj` fails with "s-dftd3 ... cannot be found" unless the Python module is in the same env.
- **Mixing up returned numbers:** with `bsse_type`, `energy()` returns an interaction energy, not a total energy.
- **Comparing with old papers:** SAPT and DF defaults changed over versions; match version and options before calling something a disagreement.
- **`set` after `energy()`** has no effect on that calculation; commands run in order.
- Before quoting any number, use `reporting-computational-results`.

## 5. Not verified yet

- No Psi4 run has been tested on PACE: timings, the best thread count per node, and a working sbatch template are unknown.
- Whether QCManyBody must be installed separately with the current conda-forge build.
- The first release containing DLPNO-CCSD(T).
- Psi4 versions installed on PACE (if any) versus a user conda env.
