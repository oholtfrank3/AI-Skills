---
name: pyopencap
description: Projected complex absorbing potential (CAP) calculations with OpenCAP / pyopencap - resonance positions and widths (shape resonances, ICD/ETMD, autoionization) from a set of real Q-Chem (or PySCF/OpenMolcas/Psi4) states, eta trajectories, first-order corrected energies, and when to use direct CAP-EOM-CCSD instead. Use when setting up, debugging or judging any pyopencap / projected-CAP calculation.
---

# Projected CAP with pyopencap (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

**What it does.** Run an ordinary (real) calculation for N states. pyopencap then builds the CAP matrix in that N-state space and diagonalizes H₀ − iηW over a range of η. This is cheap per η, but the answer is only as good as the N states you gave it.

Docs, API calls, starter calculations (N₂⁻ shape resonance from the official tutorial) and forum issues are in `troubleshooting` → `references/pyopencap.md`.

## 0. Should you use it?

- **Good fit:** shape resonances and other cases where a modest number of states spans the decay channel, and validated starter cases exist (N₂⁻ ²Πg).
- **Poor fit so far: interatomic decay (ICD/ETMD) with meV-or-smaller widths.** On Ar–water it did not work (§3). For those, direct CAP-EOM-CCSD in Q-Chem (`eom-cc` §5) is the group's working route.
- **Validate before using it on a new kind of system.** Reproduce the N₂⁻ tutorial numbers, then a dimer with a published width, before the real system.

## 1. Group setup (Q-Chem 6.3.1 → pyopencap 1.2.8)

- **Q-Chem side:** `METHOD EOM-CCSD`, `IP_STATES N` (or EE/EA), `CC_TRANS_PROP TRUE` (state-to-state transition densities), `GUI 2` (writes the `.fchk`), and `EOM_DAVIDSON_CONVERGENCE 7`. The group input also had `COMPLEX_CCMAN TRUE`, `PROJ_CAP 3` and `EOM_SHIFT 1075`. Why `EOM_SHIFT` was needed is not documented, so check before copying it.
- **pyopencap side:** `System` from `qchem_fchk`, `es_dict` with `package qchem` and `method eom`, reading `qchem.out` (H₀) and `qchem.fchk` (densities). Then `compute_projected_cap()` → `get_projected_cap()` → `CAPHamiltonian` → η trajectory.
- **CAP:** a box CAP (`Radial_precision 14`, `angular_points 590`, box sizes per system). Voronoi CAPs were not tried, but the literature finds them more robust for clusters.
- **Count your states.** The group script counted `EOMIP transition` blocks in `qchem.out` to get N. Check that this matches what you asked for.

## 2. Pitfalls we hit

- **Check the `.fchk` before running pyopencap.** The job script renamed the fchk at the end, so a killed job left a 446-byte stub and pyopencap failed much later. Check the file size first.
- **Scratch is huge and I/O-bound.** Runs with transition densities between many states filled the shared project scratch (`libxm xm_allocator_write: pwrite`). Use node-local per-job `QCSCRATCH` on local NVMe (`pace-slurm` §3).
- **Cost grows fast with N.** 5 states took 19 min and 10 states 35 min. 50 states did not finish in 48 h, and a 150-state job was killed after 36 h at state pair 124/126. Measure the scaling at small N before planning a convergence study.
- **Identify roots by ownership** (Löwdin/Mulliken weight on each fragment), never by energy ranking. Drop η-trajectory points where the tracked root switches.
- **Im(E) = −Γ/2.** Report Γ = −2 Im(E), and say whether it comes from the uncorrected or the first-order corrected trajectory.

## 3. What happened on Ar–water (Oct 2026)

- **System:** 3 Ar + water (aug-cc-pVDZ, 248 basis functions + 14 ghost centres), EOM-IP-CCSD states.
- **5 and 10 states:**
  - uncorrected Γ was 5.2–32 meV, against 0.1–0.35 meV from direct CAP-EOM-CCSD for the same donors;
  - corrected Γ was about 0 ± 0.014 meV, some values negative, with root switches.
- **20 or more states:** never completed (scratch and walltime). So convergence in N was **never tested**. Do not say it "failed to converge in N".
- **A water-dimer validation** exists (`pyopencap/water/`) but has no written outcome, and there was no Ar₂ test.
- **Complex basis functions (CBF)** also failed on Ar₃:
  - both stationary points had negative widths;
  - two published exponent sets differed 61× in width (1.17× in the paper's NeAr check);
  - the method could not tell a channel-closed donor from open ones.
- **Reading this:** at small N the projected space does not contain the decay continuum, and a sub-meV width is swamped by the CAP perturbation itself. This is our interpretation, not a published result (see the reference file, "When projected CAP struggles").

## 4. Not known yet

- The η range used in the group runs.
- Whether N ≥ 20 converges. A probe with node-local scratch was pending on Oct 21, 2026 (roots_020_v2).
- AO-ordering checks for the Q-Chem fchk path (`check_overlap_mat`).
