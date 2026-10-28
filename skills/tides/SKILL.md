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
- **Old scripts may not import.** A source restructure (commit `f7e0419`) moved modules into subpackages, so scripts written before it fail with `ImportError`. Use e.g. `from tides.methods import rt_scf, rt_ehrenfest` and `from tides.utils import rt_utils`; the full list is in `references/tides.md` K21.
- **Delete old checkpoints before a fresh run.** TiDES silently restarts from any `tides.chk` or `Restart.chkfile` in the run folder (K19).

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
- **Don't trust atom-vs-mirror-atom differences.** PySCF's DFT grid is not symmetrized (`symmetrized grids: False` in the log); in a mirror-symmetric cluster two mirror atoms differed 2× after hundreds of fs. Trust large, consistent trends only (K27).
- **Pick controls that can answer the question.** An isolated Ar⁺ 3s hole cannot refill in adiabatic TDDFT for symmetry reasons, so "no refill in the isolated atom" says nothing about refilling in a cluster.

## 4. Ehrenfest dynamics

- **Mean field averages over channels.** With no decoherence or branching it cannot describe a hole choosing between outcomes. For that, use surface hopping or CSDM (`sharc` skill).
- **Water collapsed onto Ar** (O–Ar → 0.5–1.5 Å) in CAM-B3LYP Ehrenfest. This was blamed on self-interaction error, but CASSCF-Ehrenfest also collapsed, and one water dissociation came from the restart bug (§5). **Rule out restart and force errors first.**
- **Energy drift that does not shrink with a smaller time step** comes from missing moving-basis (Pulay) terms. Use a larger basis (6-31G → 6-31G* cut the drift ~10× in the paper).
- **Multiple time steps:** `Ne_step` and `N_step` (default 10 × 10) can be too aggressive for light atoms. Reduce them and check energy conservation.
- **Health check:** healthy group runs drifted by 2–5 × 10⁻⁴ Ha over ~200 fs. A sudden jump means a bug or a broken restart, not physics.
- **Density scrambles the moment nuclei move** (fractional `mo_occ`, energy runs away at the first nuclear step): `update_mol` did not refresh `orth_inv`. Set `rt.orth_inv = numpy.linalg.inv(rt.orth)` after every `update_mol` (K20).
- **Patch forces before you build `RT_Ehrenfest`.** Its constructor computes forces once, so a force patch (frozen atoms, D3) installed afterwards misses that first call.
- **Check the simulated temperature against the experiment** before reading anything into nuclear motion (one group run sampled 13 K velocities for a 30 K experiment).

## 5. Checkpoints, restarts and bugs the group fixed

- `rt_scf.chkfile` stores **the time and MO coefficients** (and, in the group's checkout, Ehrenfest positions, velocities and forces). It does not store settings: on restart you must re-declare every propagation parameter, field and potential.
- **First-force-after-restart bug (fixed in the group drivers, Oct 2026):** the first nuclear force after a restart was wrong (2.9 instead of 0.007 Ha/Bohr at the same time step), and it caused a spurious water dissociation. Fix: recompute `rt_mf.nuc.force = ehrenfest_force.get_force(rt_mf)` right after `rt_utils.excite(...)` and before `kernel()` (K22). After any restart, compare geometry, velocities, energy and forces across the restart point. A jump means the restart is broken.
- **Don't re-sample velocities on restart.** Drivers that called `sample_vel` unconditionally reset the nuclear kinetic energy at every resubmission. Guard it with `if not os.path.exists('Restart.chkfile'):` (K23).
- **Re-apply the hole after a restart.** The chkfile restores the evolved orbitals but resets occupations to neutral, so call `excite(...)` again (K19).
- **Four further bugs were found and fixed:** density scrambling, CAP normalization, double printing and stale checkpoints. If you see jumping populations, a CAP removing the wrong amount of charge, duplicated output lines, or a restart resuming from the wrong state, check that your copy has the fixes.
- **Before plotting, check row counts:** `parse_output(f)['time'].shape[0]` must equal the row count of each observable. Exactly 2× means the double-printing bug is back (K24).
- **Print at a fixed time stride** (e.g. every 2 fs), not `nstep//200`: a stride that grows with run length aliases the signal, and a longer run reported a *smaller* maximum.
- **Starting from your own density?** Assign it to `rt_mf.den_ao` and check it. One group script built the density but never assigned it, so the run silently started from the ground state.
- **Segmented runs on PACE:** the Ehrenfest jobs advanced only ~200–280 fs per 48 h segment. Before resubmitting, confirm the `.out` tail shows TIMEOUT, rename it to `<name>_segN.out`, then resubmit the same script (it reloads `Restart.chkfile`). Picosecond dynamics need many segments, so plan for that or use a cheaper model.

## 6. CAP (MOCAP)

- `rt_cap.MOCAP(expconst, emin, prefac=1, maxval=100)` damps MOs above `emin` (Lopata & Govind 2013). Use it when ionized density would otherwise reflect off the finite basis.
- **CAP results depend on its parameters.** Scan `emin` and `expconst`, and report observables that are insensitive to them. The group's ICD precedent (Wang et al., JPCL 15, 7806 (2024)) saw final charges saturate near 1.6 instead of 2, and the method failed for vdW-bound Ne–H₂O and Ne–Ar.
- **Count how many virtuals sit above `emin`** before you run. In a dense Ar cluster an `emin` just above the LUMO damped 99 % of the virtuals; raising it from ~1.2 to ~4 eV above the LUMO left 94 % damped and barely changed the charge loss.
- **MOCAP never renormalizes the density,** and Ehrenfest forces are built from the shrinking density. Treat CAP + Ehrenfest forces with care (K25).

## 7. Running on PACE

- **Set BLAS threads before Python starts:** export `MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` = `$SLURM_CPUS_PER_TASK` and `OMP_NUM_THREADS=1` in the job script. Setting them after `import pyscf` has no effect, and the repo's own example does it too late. Use an optimized BLAS (conda scipy or MKL).
- **GPUs:** the group's TiDES checkout has a GPU wrapper, `wrap_gpu_mf` in `src/tides/utils/rt_gpu.py` (it may not be in the public jskretchmer/TIDES repo yet; unverified). Converge a gpu4pyscf SCF, wrap it, and pass the result to TiDES like a normal `mf`:
  ```python
  from gpu4pyscf import dft as gpu_dft
  from tides.methods import rt_scf
  from tides.utils.rt_gpu import wrap_gpu_mf
  mf_gpu = gpu_dft.uks.UKS(mol).density_fit(); mf_gpu.xc = 'CAMB3LYP'; mf_gpu.kernel()
  mf = wrap_gpu_mf(mf_gpu)          # Fock build and energy now run on the GPU
  rt_mf = rt_scf.RT_SCF(mf, timestep, max_time, prop='ep_pc')
  ```
  Install `cupy-cuda12x` and `gpu4pyscf-cuda12x` (match your CUDA). In the group's test (water dimer, CAM-B3LYP/aug-cc-pVDZ) one V100 took 462 ms/step against 1910 ms/step for the fastest CPU setting (12 threads), about 4×. Job lines: `--partition=gpu-v100 --gres=gpu:V100:1` and `module load cuda/12.6.1`. For Ehrenfest and D3 there are extra steps (K26).
- **Turn ms/step into fs per hour** before promising a run length: fs/h = (3600 / seconds per step) × dt(au) / 41.34.
- Resources and submission: `pace-slurm`. Propose the job and wait for an OK.

## 8. Not verified yet

- Whether the group's bug fixes (§5), the import restructure and `wrap_gpu_mf` are in the public `main` branch.
- Argument names for pulse shapes other than `delta`.
- Units of the `abs_spec` damping argument (assumed τ in au).
- Run time of the benzene benchmark on PACE CPU nodes.
