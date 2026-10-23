---
name: tides
description: Running TiDES, the Kretchmer group's real-time electronic structure code built on PySCF - RT-TDHF/RT-TDDFT absorption spectra (delta kicks, damping, linear-regime checks), hole or charge-migration dynamics from a prepared state (NOSCF), Ehrenfest dynamics, the MO-based CAP, checkpoints/restarts and running on PACE. Use when setting up, debugging or interpreting any TiDES or real-time TDDFT calculation.
---


# TiDES in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

TiDES is a Python layer on PySCF: build a `gto.Mole`, converge a PySCF SCF, wrap it in `rt_scf.RT_SCF(mf, timestep, max_time)` (or `rt_ehrenfest.RT_Ehrenfest`), switch on observables and fields, then call `kernel()`. Code, README and examples: <https://github.com/jskretchmer/TIDES>. Paper: Rohan, Suarez, Clothier & Kretchmer, J. Chem. Phys. 164, 234117 (2026).

Details, sources and a longer list of known issues are in the `troubleshooting` skill, `references/tides.md`. Check that file before guessing at a fix.

## 0. Before you start

- **Is real-time the right tool?** For a few low-lying excitation energies, linear-response TDDFT (`mf.TDDFT()`) or EOM-CC is cheaper and cleaner. Real-time pays off for broadband or core spectra, strong or shaped fields, and dynamics from a prepared non-stationary state. If unsure, use `method-selection`.
- **Run the closest example from the repo first** (`examples/`, or `examples/ExamplesFromOriginalTiDESPaper/`) on the same machine. If it works, any later problem is in your input.
- **Check which TiDES copy you are using** (`git log`). The group fixed several bugs (§5). Make sure your copy has the fixes.

## 1. Units and core settings

- `timestep` and `max_time` are in **atomic units** (1 fs ≈ 41.34 au). The time step is fixed for the whole run.
- **Propagator:** keep the default `magnus_interpol`. Use RK4 only for debugging.
- **Time step:** ≤ 0.2 au for valence work and 0.01–0.02 au for core edges. Confirm by halving it: the observable you report must not change.
- **Output:** `frequency` sets how often observables print. `verbosity` must be > 2 for observables to print at all.

## 2. Absorption spectra (delta kick)

- **Kick strength:** ~1e-4 au for valence. The paper used 1e-2 for core edges. Always check you are in the linear regime: rerun with half the kick, divide by κ, and the spectra must overlay.
- **One direction per run** (x, y, z as three jobs), then combine. Divide the dipole by the kick strength.
- **Resolution and broadening:** resolution ≈ 2π/T. Exponential damping exp(−t/τ) gives Lorentzians with FWHM ≈ 2/τ. The paper used τ = 250 au with T = 2000–5000 au. The signal must have decayed by the end of the run.
- `rt_spec.abs_spec(time, dipole, damping)` returns spectra in Hartree; multiply by 27.2114 for eV.
- **Sanity check:** in the weak-field limit, RT peak positions must match PySCF linear-response TDDFT roots in the same basis and functional.

## 3. Hole and charge-migration dynamics

- Prepare the hole with fragment orbitals (`basis_utils.noscfbasis`, examples `Li_ChargeTransfer`, `TCNE_ChargeTransfer`). The prepared state is not an eigenstate, so it carries excess energy. Report it, and don't over-read the first femtoseconds.
- **Use a range-separated hybrid** (CAM-B3LYP, LC-PBE*). Global hybrids and GGAs exaggerate self-interaction error.
- **A hole that "stays put" or splits 50/50 is a warning, not a result.** In Ar₄·H₂O, RT-TDDFT trapped the hole for 2 ps, while frozen-nuclei TD-CASCI (CAS(37,19)/cc-pVDZ) showed it hopping back and forth every 50–78 fs. Any localization or trapping claim needs a wavefunction check (TD-CASCI, or EOM-CC energetics).
- **Hirshfeld or Mulliken charges are not hole populations.** Charge changes mix hole transfer with polarization (a water "gaining electrons" was polarization). Project onto the orbitals that matter, e.g. 2 − n_K(t) for the 3s orbital on site K.

## 4. Ehrenfest dynamics

- **Mean field averages over channels.** With no decoherence or branching it cannot describe a hole choosing between outcomes. For that, use surface hopping or CSDM (`sharc` skill).
- **Water collapsed onto Ar** (O–Ar → 0.5–1.5 Å) in CAM-B3LYP Ehrenfest. This was blamed on self-interaction error, but CASSCF-Ehrenfest also collapsed, and one water dissociation came from the restart bug (§5). **Rule out restart and force errors first.**
- **Energy drift that does not shrink with a smaller time step** comes from missing moving-basis (Pulay) terms. Use a larger basis (6-31G → 6-31G* cut the drift ~10× in the paper).
- **Multiple time steps:** `Ne_step` and `N_step` (default 10 × 10) can be too aggressive for light atoms. Reduce them and check energy conservation.
- **Health check:** healthy group runs drifted by 2–5 × 10⁻⁴ Ha over ~200 fs. A sudden jump means a bug or a broken restart, not physics.

## 5. Checkpoints, restarts and bugs the group fixed

- `rt_scf.chkfile` stores **only the time and MO coefficients**. On restart you must re-declare every propagation parameter, field and potential. For Ehrenfest, the driver must restore nuclear positions and velocities itself.
- **First-force-after-restart bug (fixed in the group drivers, Oct 2026):** the first nuclear force after a restart was wrong, and it caused a spurious water dissociation. After any restart, compare geometry, velocities, energy and forces across the restart point. A jump means the restart is broken.
- **Four further bugs were found and fixed:** density scrambling, CAP normalization, double printing and stale checkpoints. If you see jumping populations, a CAP removing the wrong amount of charge, duplicated output lines, or a restart resuming from the wrong state, check that your copy has the fixes.
- **Segmented runs on PACE:** the Ehrenfest jobs advanced only ~200–280 fs per 48 h segment. Before resubmitting, confirm the `.out` tail shows TIMEOUT, rename it to `<name>_segN.out`, then resubmit the same script (it reloads `Restart.chkfile`). Picosecond dynamics need many segments, so plan for that or use a cheaper model.

## 6. CAP (MOCAP)

- `rt_cap.MOCAP(expconst, emin, prefac=1, maxval=100)` damps MOs above `emin` (Lopata & Govind 2013). Use it when ionized density would otherwise reflect off the finite basis.
- **CAP results depend on its parameters.** Scan `emin` and `expconst`, and report observables that are insensitive to them. The group's ICD precedent (Wang et al., JPCL 15, 7806 (2024)) saw final charges saturate near 1.6 instead of 2, and the method failed for vdW-bound Ne–H₂O and Ne–Ar.

## 7. Running on PACE

- **Set BLAS threads before Python starts:** export `MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` = `$SLURM_CPUS_PER_TASK` and `OMP_NUM_THREADS=1` in the job script. Setting them after `import pyscf` has no effect, and the repo's own example does it too late. Use an optimized BLAS (conda scipy or MKL).
- **GPUs:** the group ran TiDES jobs on `gpu-v100`, but whether TiDES itself uses the GPU is not documented. Measure before requesting GPUs.
- Resources and submission: `pace-slurm`. Propose the job and wait for an OK.

## 8. Not verified yet

- Whether the group's bug fixes (§5) are merged into the public `main` branch.
- Argument names for pulse shapes other than `delta`.
- Units of the `abs_spec` damping argument (assumed τ in au).
- Run time of the benzene benchmark on PACE CPU nodes.
