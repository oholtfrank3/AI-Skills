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
- **Poor fit so far: interatomic decay (ICD/ETMD) with meV-or-smaller widths.** On Ar–water it did not work (§3). For those, direct CAP-EOM-CCSD in Q-Chem (`eom-cc` §5a) is the group's working route.
- **Validate before using it on a new kind of system.** Reproduce the N₂⁻ tutorial numbers, then a dimer with a published width, before the real system.

## 1. Group setup (Q-Chem 6.3.1 → pyopencap 1.2.8)

- **Q-Chem side:** `METHOD EOM-CCSD`, `IP_STATES N` (or EE/EA), `GUI 2` (writes the `.fchk`), `COMPLEX_CCMAN TRUE` with a `$complex_ccman` block containing `PROJ_CAP 3`, and `EOM_DAVIDSON_CONVERGENCE 7`. With `GUI 2` + `PROJ_CAP 3`, Q-Chem writes every state density and state-to-state transition density to the `.fchk` (6.3 manual p. 583). The group's working runs did not set `CC_TRANS_PROP`: a 30-state EOM-IP run wrote 60 state-density and 1740 transition-density blocks without it. The manual says option 3 works for any EOM-CC model with state-to-state transition properties, and EOM-IP worked.
- **Aim the roots with `EOM_SHIFT`, not `EOM_USER_GUESS`.** Without a shift, 30 roots covered only 12.6–28.2 eV (outer-valence holes plus a dense band of 2h1p satellites, ~66 roots/eV) and never reached the Ar 3s holes at 29.3–29.7 eV. `EOM_SHIFT` is in 10⁻³ Eh (millihartree), so `1085` ≈ 29.5 eV, the middle of that manifold. `EOM_USER_GUESS` cannot be used here: with `IP_STATES 8` it printed only 1 state, and pyopencap needs all N states and their densities.
- **pyopencap side:** `System` from `qchem_fchk`, `es_dict` with `package qchem` and `method eom`, reading `qchem.out` (H₀) and `qchem.fchk` (densities). Then `compute_projected_cap()` → `get_projected_cap()` → `CAPHamiltonian` → η trajectory.
- **CAP:** a box CAP (`Radial_precision 14`, `angular_points 590`, box sizes per system). Voronoi CAPs were not tried, but the literature finds them more robust for clusters.
- **Count your states.** The group script counted `EOMIP transition` blocks in `qchem.out` to get N. Check that this matches what you asked for.

## 2. Pitfalls we hit

- **Check the `.fchk` before running pyopencap.** The job script renamed the fchk at the end, so a killed job left a 446-byte stub and pyopencap failed much later. Check the file size first.
- **Scratch is huge and I/O-bound.** Runs with transition densities between many states filled the shared project scratch (`libxm xm_allocator_write: pwrite`). Use node-local per-job `QCSCRATCH` on local NVMe (`pace-slurm` §3).
- **Cost grows fast with N.** 5 states took 19 min and 10 states 35 min (small system). On 4 Ar + water (472 basis functions) 30 states took 15 h 13 min and a 6–6.5 GB `.fchk`. A 50-state job converged its roots in ~30 h but was cancelled by mistake while writing transition densities (90 of 2450 pairs done), and a 150-state job was killed after 36 h at state pair 124/126. The number of transition densities grows as N², so measure the scaling at small N before planning a convergence study. Read a multi-GB `.fchk` in a batch job, not on the login node.
- **Identify roots by ownership** (Löwdin/Mulliken weight on each fragment), never by energy ranking. Drop η-trajectory points where the tracked root switches.
- **Im(E) = −Γ/2.** Report Γ = −2 Im(E), and say whether it comes from the uncorrected or the first-order corrected trajectory. If you work with ionization or attachment energies printed by Q-Chem as (Re, Im), Im is positive for a decaying state and Γ = +2 Im.
- **Nearest-energy assignment fails in dense manifolds.** Greedy nearest-energy assignment gave two roots 2 meV apart to donors whose reference energies differ by 0.14 eV. Reference energies to the neutral CCSD energy, not to the lowest cation root (that put every root 12.6 eV low).

## 3. What happened on Ar–water (Oct 2026)

- **System:** 3 Ar + water (aug-cc-pVDZ, 248 basis functions + 14 ghost centres), EOM-IP-CCSD states.
- **5 and 10 states:**
  - uncorrected Γ was 5.2–32 meV, against 0.1–0.35 meV from direct CAP-EOM-CCSD for the same donors;
  - corrected Γ was about 0 ± 0.014 meV, some values negative, with root switches.
- **30 states (4 Ar + water, 472 basis functions with ghosts, `EOM_SHIFT 1085`):** the run completed. Taking subspaces of 10–30 of those states, Γ came out 30–1400 meV against 0.12–0.31 meV from direct CAP-EOM-CCSD for the same donors (98× to 11751× too large), and it was **not converged in N**: one donor went 1422 → 1275 → 65 meV, another doubled between N = 25 and 30.
- **50 states:** all roots converged, but the job was cancelled by mistake before the densities were written, so there is no N = 50 result.
- **A water-dimer validation** exists (`pyopencap/water/`) but has no written outcome, and there was no Ar₂ test.
- **Complex basis functions (CBF)** also failed on Ar₃:
  - both stationary points had negative widths;
  - two published exponent sets differed 61× in width (1.17× in the paper's NeAr check);
  - the method could not tell a channel-closed donor from open ones.
- **Reading this:** up to N = 30 the projected space does not contain the decay continuum, and a sub-meV width is swamped by the CAP perturbation itself. This is our interpretation, not a published result (see the reference file, "When projected CAP struggles").

## 4. Not known yet

- The η range used in the group runs.
- Whether N well beyond 30 converges on a cluster. Up to N = 30 it did not. A probe with node-local scratch was pending on Oct 21, 2026 (roots_020_v2).
- AO-ordering checks for the Q-Chem fchk path (`check_overlap_mat`).
