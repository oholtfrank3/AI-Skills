# SHARC 3.x / pySHARC: troubleshooting reference

Last researched: 2026-10-21

**How to use this file:** find your symptom in "Known issues and fixes", check the cause against your `output.log`/`QM.err`, apply the fix, and rerun a starter calculation before trusting production. Group-specific lessons live in `skills/sharc/SKILL.md`; this file adds the official docs, source checks and public issues. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official documentation

**Versions (check which one you run).** The group install is SHARC 3.0.2. Upstream has moved on.
- SHARC 3.0.0 (2023-04-14), 3.0.1 (2023-05-04), 3.0.2 (2024-02-16, "strict bugfix"): <https://github.com/sharc-md/sharc/releases>. Zenodo record for 3.0: <https://zenodo.org/records/7828641>.
- The `main` branch of `sharc-md/sharc` has ~79 commits after 3.0.2, including real bug fixes that were never released as 3.0.3 (see Known issues #1, #7, #12).
- SHARC 4.0 (2025-05-23) through 4.1 (2026-06-26) live in a new repo, <https://github.com/sharc-md/sharc4>. The developer says the old repo's issue tracker is no longer active (sharc#205, 2026-07-14).

**Manuals and tutorial.**
- SHARC 3.0 manual (PDF): <https://sharc-md.org/wp-content/uploads/2023/04/SHARC_Manual.pdf>. Note: `doc/SHARC_Manual.pdf` inside the 3.0 git repo is still the **2.1.1** manual. Use the website PDF.
- SHARC 4.1 manual: HTML at <https://sharc-md.org/?page_id=1454>, PDF at <https://sharc-md.org/wp-content/uploads/2026/06/SHARC_Manual.pdf>.
- Tutorial (4.x, CH2NH2+ with OpenMolcas): <https://sharc-md.org/wp-content/uploads/2026/07/SHARC_Tutorial.pdf>, page <https://sharc-md.org/?page_id=52>.
- Method reviews: Mai, Marquetand, González, *WIREs Comput. Mol. Sci.* 8, e1370 (2018), DOI 10.1002/wcms.1370 (<https://pmc.ncbi.nlm.nih.gov/articles/PMC6220962/>). For the Minnesota additions (CSDM, SCP, curvature-driven), see Shu & Truhlar, JCTC 2024, DOI 10.1021/acs.jctc.4c00424 (cited from the sharc-md.org publication list; I did not read it).

**Workflow (3.0 manual ch. 3, 7).** `wigner.py` (sample from a Molden frequency file; `-t` for finite temperature) → `setup_init.py` (single points at each initial condition) → `excite.py` (choose initial states by energy window/oscillator strength) → `setup_traj.py` (writes `input`, `run.sh`, `QM/runQM.sh` for each `TRAJ_xxxxx`) → run → `diagnostics.py` → `populations.py` / `transition.py` / `make_fit.py`. Every interactive script writes a `KEYSTROKES.*` file; keep it, because the developers ask for it when you report a bug.

**Main `input` keywords (SHARC 3.0 table 4.1; defaults in brackets).** Input is case-insensitive, `#` starts a comment, keyword order does not matter. The parser looks only for the keywords it knows, so a misspelled keyword is silently ignored (checked in `input.F90`; I found no "unknown keyword" check for keyword names). Typos in keyword *values* do stop the run.
- **Time:** `stepsize` [0.5 fs], `nsubsteps` [25], `tmax` or `nsteps`, `killafter` [-1 = never]. setup_traj recommends 0.5 fs and 25 substeps. The 4.1 manual example uses 0.1 fs for CSDM.
- **States:** `nstates` (per multiplicity, ground state included), `actstates`, `state <n> mch|diag` (no default; run exits without it), `coeff auto|external`, `ezero` (Hartree, **never set automatically**).
- **Method:** `method tsh|scp` (also accepts `ehrenfest` and `csdm`, which map to scp). `surf sharc|diagonal` (default) or `mch`. `coupling overlap|ddr(nacdr)|ddt|ktdc`. `eeom` (propagator: ld is the default for overlap+tsh, npi for overlap+scp).
- **Hopping:** `hopping_procedure sharc|standard` (default) `|gfsh|off`, `no_hops`, `time_uncertainty`, `force_hop_to_gs <dE>`.
- **Hop energy fix-up:** `ekincorrect none|parallel_vel|parallel_pvel|parallel_nac|parallel_diff|parallel_pnac|parallel_enac|parallel_penac`. With `none`, hops are never frustrated and energy is not conserved. setup_traj's default is `parallel_vel`.
- **Frustrated hops:** `reflect_frustrated none` (setup_traj default) `|parallel_*|delV_*` (the delV variants reflect only if the ∇V criterion says so).
- **Decoherence (TSH):** `decoherence_scheme none|edc|afssh`. `decoherence_param` is the EDC constant C in Hartree [0.1]. Bare `decoherence` means EDC for TSH and DoM for SCP. Without any decoherence keyword, decoherence is **off** and stderr warns.
- **SCP/CSDM:** `decoherence_scheme dom` (SCP only) sets α = 0.1 and β = 1.0. `switching_procedure csdm|scdm|ndm|off` (code default csdm). `decotime_method csdm|scdm|edc|sd|fp1|fp2` (code default csdm). `decoherence_param_alpha` (Hartree) and `decoherence_param_beta` (unitless). `neom ddr|gdiff` (gdiff is the default with overlap/ktdc). `nac_projection` (default). `pointer_basis diag|mch`.
- **Gradients:** `gradcorrect` (adds NAC terms when transforming gradients to the diagonal basis), `grad_select`/`nac_select` with `eselect` [0.5 eV], `select_directly`.
- **Phases:** `track_phase` (default) / `notrack_phase` (faster in pysharc; check the results still agree).
- **Restart:** `restart` plus **either** `restart_goto_new_qm_step` (after a graceful stop: tmax, STOP file, killafter) **or** `restart_rerun_last_qm_step` (after a crash or kill). With neither, the run errors. `rngseed` [10997279].
- **Output:** `printlevel` (diagnostics.py needs ≥ 2), `output_dat_steps` (1, 3 or 5 arguments), `write_grad/nacdr/overlap`, `output_format ascii|netcdf` (NetCDF only works in pysharc).
- **Constraints:** `rattle` with `rattlefile`, `atommask external` (affects EDC and `parallel_vel`).

**pySHARC (3.0 manual §3.4; `input.F90`).** In 3.x it is mainly `pysharc_lvc.py`, which runs the LVC interface in memory and avoids file I/O. In the 3.0.2 source, pysharc **stops** on: SCP/Ehrenfest, DoM decoherence (CSDM/SCDM), `time_uncertainty`, adaptive/BSH integrators, ZPE correction and Army Ants. In 4.x, `driver.py` replaces pysharc and supports SCP/Ehrenfest, CSDM, time uncertainty and curvature-driven dynamics (4.1 manual §1.1.1).

**Interfaces in 3.0 (`setup_traj.py`).** MOLPRO, COLUMBUS, Analytical, MOLCAS (OpenMolcas), AMS-ADF, RICC2 (Turbomole), LVC, GAUSSIAN, ORCA, BAGEL, PYSCF. Most TD-DFT interfaces need WFoverlap for `coupling overlap`. 4.x adds hybrid interfaces (QMMM, NUMDIFF, ECI, FALLBACK…) and renames some (TURBOMOLE replaces RICC2).

**Analysis tools.**
- **`data_extractor.x`:** turns `output.dat` into `output_data/`. `-s`/`-xs` is enough for most uses.
- **`diagnostics.py`:** interactive. It checks files, status, energy and population, then writes `DONT_ANALYZE` into trajectories that fail after your T_mu threshold. Its defaults (tutorial) are etot_window 0.2 eV, etot_step 0.1 eV, epot_step/ekin_step 0.7 eV and hop_energy 1.0 eV. These are loose; tighten them to your own energy scale.
- **`populations.py`:** modes 1–3 count active states (classical). Modes 7–9 sum |c|² (quantum). Modes 12–15 transform to MCH. It skips trajectories containing `CRASHED`, `RUNNING` or `DONT_ANALYZE`.
- **`transition.py`:** counts hops.

---

## Starter calculations

**1. Analytical IBr model (test `Analytical_overlap`, no QM code).**
- **System:** IBr diatomic, 3 states, analytical Hamiltonian in `QM/Analytical.template` (variables bound to Cartesian coordinates, atomic units).
- **Settings:** `state 3 mch`, 0.5 fs, 25 substeps, 10 fs, `coupling overlap`, `ekincorrect parallel_vel`, EDC 0.1, `grad_select nac_select eselect 0.5`.
- **Run:** `$SHARC/tests.py` (choose Analytical_overlap), or run `run.sh` in `$SHARC/../tests/INPUT/Analytical_overlap`.
- **Expected:** the run matches `tests/RESULTS/Analytical_overlap/output.lis`. It stays in state 3, with Etot 2.3895 → 2.3889 eV (≈ −0.6 meV over 10 fs).
- **Common mistake:** writing the template's matrices in eV or as full matrices. They must be lower triangles in atomic units.

**2. SO2 LVC model with pySHARC (test `LVC_pysharc`).**
- **System:** SO2, 4 singlets + 3 triplets (`actstates 3 0 3`), LVC parameters in `QM/LVC.template`, driver `pysharc_lvc.py input`.
- **Settings:** `state 2 mch`, 0.5 fs, 25 substeps, 30 fs, overlap, EDC, `ekincorrect parallel_vel`, `notrack_phase`, `output_format ascii`.
- **Expected:** the run matches `tests/RESULTS/LVC_pysharc/output.lis`. It stays in diag state 5 / MCH state 2, and Etot goes 5.4906 → 5.4714 eV. Note that even the reference run drifts ~19 meV in 30 fs.
- **Common mistakes:** a missing `PYTHONPATH` (pysharc not found: `No module named 'sharc'`, sharc#171). In SHARC 4 with gfortran, the LVC input is not read (sharc4#22, sharc#206).

**3. Tutorial: CH2NH2+ with SA-CASSCF(6,4)/cc-pVDZ, OpenMolcas (tutorial ch. 2 and 5).**
- **System:** 4 singlets + 3 triplets, starting on the bright ππ* state (S2).
- **Steps:** optimisation and frequencies → `wigner.py` → `setup_init.py` → `excite.py` → `setup_traj.py`. The tutorial uses 100 fs and 0.5 fs steps with 25 substeps, `parallel_vel`, no reflection, EDC 0.1 and `eselect 0.1`, for about 9–12 trajectories.
- **Single-trajectory shortcut:** tutorial ch. 5 uses `veloc random 0.1`, `tmax 25`, `coupling overlap`, `decoherence_scheme edc`, `grad_select`, `select_directly`.
- **Expected:** a qualitatively similar population plot. The tutorial deliberately produces a few bad trajectories (energy jumps from active-space switches) for diagnostics.py to flag.
- **Not a mistake:** your results will not match the tutorial figures, because random-number streams differ across Python/Fortran versions (developer reply in sharc4#13, <https://github.com/sharc-md/sharc4/issues/13>, 2025-08-05).

**4. Tully model 1 via the Analytical interface (group TODO, unverified).**
- **Setup:** encode Tully's single avoided crossing as a 1D two-state template, using x of one atom with a large mass.
- **Expected:** compare transmission/reflection probabilities against Tully, *J. Chem. Phys.* 93, 1061 (1990), across momenta. I did not find a SHARC-provided Tully input or reference numbers.
- **Common mistake:** using random velocities instead of a fixed initial momentum, and too few trajectories per momentum (≥ 1000 for ±0.015).

---

## Known issues and fixes

1. **Zero gradient right after a hop, then an energy jump one step later** (SHARC 3.0–3.0.2, with `grad_select`). Cause: the post-hop gradient was fetched but not processed. Fix: commit bc0c242 on `main` (2024-05-03), which is **after** the 3.0.2 release. Rebuild from `main` or use `grad_all`. After a hop, the dipole in `output.lis` can still read zero for TD-DFT/ADC(2). <https://github.com/sharc-md/sharc/issues/112> (2024-05-01).
2. **Populations stay flat even though hops occur (tutorial, OpenMolcas).** Cause: `runQM.sh` was effectively called twice per step, so the overlaps compared a step with itself (unit overlap matrix). Separately, a "DM element not found / too few matrix elements" RASSI error is a known OpenMolcas-version problem. Fix: use the interface version that matches your OpenMolcas and check that overlap matrices are not identity. <https://github.com/sharc-md/sharc/issues/181> (2025-04-22); the developer points to #131 for the RASSI error (not read).
3. **diagnostics.py reports "Missing steps" at the restart time.** Cause: a diagnostics.py bug in handling the two restart keywords; the trajectory data is fine. Fix: use diagnostics.py from `main`, or remove the duplicated step from `output.log`. Use `restart_rerun_last_qm_step` after a wall-time kill. <https://github.com/sharc-md/sharc/issues/90> (2023-12-04). The same bug came back in SHARC 4.0.2: <https://github.com/sharc-md/sharc4/issues/29> (2026-07-03).
4. **A trajectory accidentally run twice at once cannot be restarted** (SHARC 3). Cause: two drivers wrote to the same restart files and savedir, and the result is not recoverable. SHARC 4 refuses to start if restart files exist without `restart`. Fix: guard job submission (one job per `TRAJ`) and rerun the trajectory. <https://github.com/sharc-md/sharc/issues/195> (2025-11-06).
5. **`excite.py`/`initconds` show huge kinetic energy for a linear molecule.** Cause: wigner.py's removal of translation/rotation fails for linear molecules and inflates the velocities. Fix: `wigner.py --keep_trans_rot`. The Ekin printed by excite.py is informational only. <https://github.com/sharc-md/sharc/issues/169> (2024-12-12).
6. **Choosing a temperature for initial velocities.** `veloc random E` gives E eV per atom in random directions, which is not thermal. Fix: use `wigner.py -t T` for rigid molecules, or ground-state MD (with a Langevin thermostat in SHARC 4) for floppy ones. <https://github.com/sharc-md/sharc/issues/194> (2025-10-08).
7. **Segfault in `qm.f90`/`NAC_processing` for large systems (~1400 atoms).** Cause: large (3N)² stack arrays. Fix: `ulimit -s unlimited` in `run.sh`. On `main` after May/Oct 2024, these arrays are allocated only if NAC projection is used. <https://github.com/sharc-md/sharc/issues/97> (2024-02-02).
8. **WFoverlap fails on determinant strings over 2000 orbitals.** Fix: the limit was raised to 4000 on `sharc3preview`/`main` (2024-03); rebuild. <https://github.com/sharc-md/sharc/issues/105> (2024-03-14).
9. **Single-state (adiabatic) MD with ORCA crashes after the first call.** Cause: the overlap step fails with one state. Fix: add `nooverlap` to QM.in and use `coupling ktdc` (the coupling choice does nothing with one state). `nstates` counts the ground state. <https://github.com/sharc-md/sharc/issues/176> (2025-03-04).
10. **`No module named 'sharc'` or `module 'sharc' has no attribute 'setup_sharc'` with pysharc.** Cause: `PYTHONPATH` does not contain `$SHARC/../pysharc`, or a mixed install (3.0.2 env with 2.1 binaries). Fix: source `sharcvars.sh` from the same install, then check `ldd` on `pysharc/sharc/sharc*.so`. <https://github.com/sharc-md/sharc/issues/171> (2025-01-06).
11. **SHARC 4 driver ignores the input (charge/format errors in output.log) with gfortran builds.** Cause: a known gfortran optimisation issue. Fix: lower the optimisation flags as described in sharc4#3 (linked by the developer, not read), or build with ifx. <https://github.com/sharc-md/sharc4/issues/22> (2026-02-18); <https://github.com/sharc-md/sharc/issues/206> (2026-08-07).
12. **ORCA interface fails after a restart with `KeyError: 'nbsuse'`, or "Could not find Orca version".** Cause: the ORCA job failed (often the file system or a missing module on the node), not SHARC. Fix: check the last `ORCA.out` and the module/env on the compute node, then restart. <https://github.com/sharc-md/sharc/issues/195>.
13. **Ensemble result changes with diagnostics.py thresholds.** Cause: excluding trajectories systematically (e.g. those that crash in one region) biases populations. Fix: inspect flagged trajectories by hand and report how many you excluded and why. <https://github.com/sharc-md/sharc/issues/129> (2024-07-02).
14. **Very slow OpenMolcas steps in SHARC 4.** Cause: the new MOLCAS interface forces tight RASSCF thresholds when gradients are requested. Fix: edit the interface to use the template `rasscf_thrs`, drop PRWF/PRSD, and use node-local scratch. <https://github.com/sharc-md/sharc4/issues/18> (2025-09-11).
15. **Total population not normalised in `output.lis`.** Reported after mixing `sharc.x` and scripts from different versions; no resolution was posted. Check that driver and scripts come from one install. <https://github.com/sharc-md/sharc/issues/201> (2026-02-01, open).
16. **Trivial crossings and random phases (review, 2018).** Symptoms: spurious hops and population sloshing between multiplet components. Fix: use `coupling overlap` (local diabatization) with phase tracking on, and check overlap matrices for sign flips. Uncorrected FSSH is overcoherent, so use EDC or AFSSH. When nothing better is available, `parallel_vel` is the usual fallback; rescaling along the NAC is the rigorous choice. Mai et al. 2018, <https://pmc.ncbi.nlm.nih.gov/articles/PMC6220962/>.

---

## Confirms / contradicts group notes

Checked against the 3.0 manual and the `v3.0.2` / `main` source (`source/input.F90`, `qm.f90`, `driver.f90`, `decoherence_dom.f90`, `interface.F90`).

- **pysharc refuses scp/CSDM: confirmed for 3.x.** In `input.F90`, pysharc builds stop on `method scp`, on DoM decoherence, and also on time_uncertainty, adaptive integrators, ZPE correction and Army Ants. **Outdated for SHARC 4:** `driver.py` supports SCP/Ehrenfest and CSDM. Qualify SKILL.md §1 as "3.x only".
- **Coherence-force rescale in qm.f90: confirmed.** In `v3.0.2` `qm.f90` line 1371, the nonadiabatic SCP force term is ΔE·ρ·NACdt / (v·G) · G, where G is the NAC or effective-NAC direction set by `neom` (gdiff by default with overlap). With overlap coupling, NACdt comes from the overlaps, so the ratio is not 1. No keyword removes it. I did not check whether 4.x changed it.
- **restart.traj every step: confirmed for `sharc.x`.** In `driver.f90`, `write_restart_traj` opens the file with `status='replace'` every step, unconditionally. **Nuance:** in pysharc, `output_format netcdf` (the pysharc default) skips `restart.traj` and `output.xyz` except at the end. SKILL.md's "no keyword turns it off" holds for `sharc.x` only.
- **decoherence_param_alpha / beta: confirmed.** α = E0 in Hartree and β = C, unitless; both are read only when `decoherence_scheme dom`, which presets 0.1/1.0. The log does print "Hartree" after beta (label bug in `input.F90`). Printed decoherence "times" are actually rates (1/τ) in F9.4, at `printlevel > 4`, as SKILL.md says. **Nuance:** the CSDM code uses E_s, the kinetic energy projected on the s-vector (s = p_vib + (p·d̂)d̂, mass-weighted), not the total kinetic energy. "T_s ≈ total KE" is an approximation, and fitting T_s from large-gap rates is the right empirical check.
- **restart_goto_new_qm_step: partly contradicts.** The manual says `goto_new` is for **graceful** stops (tmax, STOP file, killafter). After a crash or a queue time-limit kill, use `restart_rerun_last_qm_step`. SKILL.md §7 says restart "needs `restart_goto_new_qm_step`". That is right only for the USR1→STOP path; say so explicitly.
- **CSDM keyword names: confirmed.** `switching_procedure csdm`, `decoherence_scheme dom` and `decotime_method csdm` are all parsed in 3.0.2 (and csdm is already the code default for both switching and decotime). `decotime_method` is **missing from the 3.0 manual table**; it is documented only in the 4.1 manual. `method csdm` and `method ehrenfest` are accepted aliases of `scp`.
- **New for the group: zero-gradient-after-hop bug (#112).** It is present in 3.0.2 when `grad_select` is used and fixed only on `main`. Check whether the group's FSSH runs used `grad_select`. The +9–12 meV residual drift (SKILL.md §11) is probably unrelated (unverified).
- **diagnostics.py defaults (0.2 eV window)** are much looser than the group's ≲1 % of kinetic energy target. Keep the group target.

## Open questions / could not verify

- Whether SHARC 4.x `qm.f90` still has the NACdt/(v·G) rescale (sharc4 source not checked).
- Whether the diagnostics.py restart fix from Dec 2023 (#90) is inside the 3.0.2 tarball (committed before the release, but not confirmed).
- No public SHARC mailing list or Matter Modeling SE threads found; GitHub issues are the de facto support channel.
- No official SHARC Tully-model inputs or reference results found; the Shu & Truhlar 2024 JCTC perspective was not read.
- Exact meaning of `compatibility 1` versus decoherence random numbers was not tested.
