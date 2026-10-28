---
name: sharc
description: Recipes and pitfalls for nonadiabatic dynamics with SHARC 3.x - surface hopping (FSSH, EDC), Ehrenfest and CSDM, dense or near-degenerate state manifolds, model-Hamiltonian (file-based) interfaces, energy-conservation checks, initial conditions, restart/I-O cost, and running trajectory ensembles on PACE. Use when planning, setting up, debugging or analysing any SHARC or surface-hopping / mixed quantum-classical dynamics run.
---


# SHARC dynamics in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

Most of these notes come from one project: an Ar 3s hole in a ~140-site band next to a water, driven through a file-based model-Hamiltonian (DIM) interface. Many lessons are about **dense, flat manifolds** (many states within ~20 meV), where SHARC's defaults break. On a few well-separated states the defaults are usually fine. Project-specific settings are in `references/dim-ar-water.md`.

Before setting anything up, check with `method-selection` that surface hopping is the right tool. Submission follows `pace-slurm` §0: propose, then wait for an explicit OK. For anything not covered here, follow the `troubleshooting` skill (manual → GitHub issues → literature) before guessing.

## 1. Version, driver, binaries

- **Group install:** SHARC 3.0.2 under `/storage/project/r-jkretchmer3-0/oholtfrank3/software/sharc` (built 2026-08-30; the SA-CASSCF and DIM runs both used it); environment from `ICD/sharc_dynamics/sharc_env.sh`. The build notes do not say whether the source was the 3.0.2 release or a later `main` checkout, which matters for §4's `grad_select` bug: check `git log` in the source tree if it is a clone.
- **In SHARC 3.x, pysharc only does surface hopping.** It refuses `method scp` (Ehrenfest/CSDM). SHARC 4.1 (separate `sharc4` repo) does support SCP and CSDM in its `driver.py`, so recheck this if the group upgrades. For mean-field or CSDM use standalone `sharc.x` with a file-based `QM.in`/`QM.out` interface (template: `SHARC_Analytical.py`).
- **Never patch the installed tree.** Build each patch in a copy of the source as a separately named binary and keep the `.patch` next to it. Record the md5 of the binary and the interface in every run directory.

## 2. Choosing the algorithm

| Use | Keywords (SHARC 3.0.2) | Notes |
|---|---|---|
| FSSH, literature standard | `surf sharc`, hopping `standard`, `ekincorrect parallel_diff`, no decoherence | Variant: `decoherence_scheme edc`, `decoherence_param 0.1`. `parallel_vel` only as a comparison. |
| CSDM (coherent switching with decay of mixing) | `method scp`, `switching_procedure csdm`, `decoherence_scheme dom`, `decotime_method csdm`, `decoherence_param_alpha 0.1`, `decoherence_param_beta 1.0` | Needs standalone `sharc.x`. See §4 for the force patch. |
| Ehrenfest | `method scp`, switching off, decoherence none | Use as a control only (see below). |

Check each keyword against the manual of the SHARC version you run.

- **Report wavefunction populations, never FSSH active-state fractions.** For delocalized carriers they disagreed by 2–3×, even with EDC. In one test the active state stayed on a site in 8/8 runs while the wavefunction did in 1/8. If FSSH and wavefunction populations disagree, FSSH is internally inconsistent there. CSDM has no such split.
- **Pure Ehrenfest blew up in a dense manifold.** It gave drifts of 15 and 73 meV, and one run reached ~60 eV. Keep it as a control on a few seeds.
- **CSDM parameters: use Truhlar's values (E0 = 0.1 Eh, C = 1) and do not tune them.** E0 = 0.05 or 0.02 Eh changed a 60 fs population from 0.08 to 0.72–0.75 and did not fix drift.
- **Naming trap:** `decoherence_param_alpha` = E0 in Hartree, and `decoherence_param_beta` = C, which is dimensionless. The log prints "Hartree" for beta anyway.
- **Know what CSDM does in your manifold.** τ_iK = (C + E0/T_s)/|E_i − E_K|, where T_s is the kinetic energy along the decoherence direction (mostly the nuclear momentum), so in practice T_s ≈ the *total* nuclear kinetic energy, not kT/2. At ~0.4 eV kinetic energy that gives 46 fs for a 300 meV gap and ~770 fs for an 18 meV gap. Inside a band with ~20 meV spacings, CSDM therefore behaves almost like Ehrenfest. SHARC prints the rates only at `printlevel` > 4, in F9.4 format, so small gaps print as 0.0000. Fit T_s from the large-gap rates.
- **CSDM is deterministic.** Identical initial conditions reproduce results to 3 decimals, so statistics come only from distinct initial geometries.
- **Pointer-state changes are not hops.** In one run the CSDM pointer changed in 32 of 50 intervals. Do not report it as a hop count.

## 3. Dense or near-degenerate manifolds

- Propagate with **overlap coupling** (local diabatization) and phase tracking. Do not use NAC-based hopping.
- Follow states by eigenvector overlap (assignment and sign), never by energy ranking. Check how many states get reassigned (0 in 26k frames is what a healthy run looks like).
- Do not rescale velocities along d_ab near degeneracies, because d ∝ 1/ΔE diverges. If you supply `nacdr`, do not zero or cap it; floor the gap at ~1e-9 Eh.
- **Constraints plus `parallel_diff`:** with a rigid fragment (RATTLE), up to 0.23 eV of the hop correction went into motion the constraint then removed. The symptoms were 12–35 meV lost per hop and "Scaling factor −233" in the log. Fix: project the gradients onto the allowed rigid-body motion *before* SHARC sees them. That brought the energy change over 80 fs from −48.8 to −0.70 meV.

## 4. Energy conservation (the largest time sink)

- **Check every trajectory with** `python3 <plugin>/scripts/check_sharc_lis.py output.lis` (in the plugin's `scripts/` folder). It reports drift as a percentage of the mean kinetic energy and flags single-step jumps; use `--absorbing` for absorbing-edge runs.
- **Measure drift against the energy scales that matter:** the kinetic energy of the moving atoms, the range of the potential, the coupling and kT. Never compare it with the absolute total energy, which has an arbitrary zero. Production target: ≲ 1 % of the kinetic energy per run. The production DIM runs reached 0.1–0.5 meV over 2 ps.
- **Stock SHARC `scp` with overlap coupling gets the coherence force wrong in dense bands.** It scales the force by NACdt/(v·d), with NACdt taken from overlaps, and in a dense band NACdt ≠ v·d. On single steps the mean-field force was 9–61 % off the exact force, even though small-system populations looked fine. Drift at 60 fs on one stress case:

  | Run | DT 1 fs | 0.5 | 0.25 | 0.1 |
  |---|---|---|---|---|
  | stock Ehrenfest + `nacdr` | +47 meV | +30 | +11 | +2.7 |
  | patched (rescale removed) + `nacdr` | +12.1 | +7.9 | +1.4 | — |
  | exact force computed in the interface | −0.7 | — | — | — |

  The patch removes a two-line rescale in `qm.f90` (~line 1371); no keyword is equivalent (`coupling ddr` is a weaker fallback). `nacdr` on its own, with the stock binary, did **not** help. The best route is to compute the exact force in the interface (group binary `sharc_force.x`, `SHARC_EXACTFORCE=1`). It agreed with the patched result to ~1 meV and was 2.6–3.5× faster. **This only works when the interface can return the density-weighted exact force Σ Re(ρ_ij)⟨i|∇H|j⟩**, as a model Hamiltonian can. A typical ab initio overlap interface gives only state gradients. There, use the patched binary with derivative couplings (`nacdr`).
- **A smaller time step hides the bug, it does not fix it.** "DT too coarse" was tested and refuted as the cause. Production used DT 0.25 fs (CSDM) and 1 fs (FSSH).
- **`grad_select` can leave a zero gradient right after a hop.** In SHARC 3.0–3.0.2, when `grad_select` is on, the gradient fetched after a hop is not processed, so the next step has an energy jump (sharc-md/sharc issue #112). It was fixed on `main` (commit bc0c242, May 2024), not in any 3.x release. It only matters on steps with a real hop to a different state; `grad_all` is unaffected.
  - **What the group ran:** the DIM FSSH/FSSH-EDC pilots and the SA-CASSCF/OpenMolcas production runs all used `grad_select` (SA-CASSCF: `eselect 0.2`, later `0.001`, i.e. one gradient per step); the DIM CSDM runs did not. The SA-CASSCF runs showed 8–16 meV energy jumps exactly one step after state switches (all 56 jumps > 1 meV in one ensemble). That matches #112's symptom but was never diagnosed; trivial crossings between far-apart sites are the other candidate.
  - **What to do:** with a 3.0.2 release build, use `grad_all` for anything you will report, or rebuild from `main`. If cost forces `grad_select`, rerun a few trajectories with `grad_all` and compare the per-hop energy change.
- **`output.lis` prints `****` in the Epot/Etot columns when the absolute energy is large** (e.g. −59372 eV for an Ar cluster with an ab initio interface). That is a Fortran field overflow, not a blow-up. Rebuild Etot from `output.dat` (or run `data_extractor.x` and read `output_data/energy.out`). `check_sharc_lis.py` warns when it sees this.
- **`diagnostics.py` defaults are loose** (a 0.2 eV energy window). Set the thresholds to your own tolerance (§4) instead of trusting its pass/fail.
- **A misspelled keyword is silently ignored.** Check the echo of the input in `output.log`.
- **Keep `nsubsteps` at 25.** 5 or 10 saved no time and made drift worse.
- **Always look for single-step jumps**, not just end-to-end drift. One unexplained 97 meV jump and one 657 meV outlier were never diagnosed.

## 5. Validate before production

- Run a small system against an exact wavepacket first. The group test was Ar₃⁺: 300 trajectories × 300 fs, with a worst population error of 0.056 (0.01–0.02 up to 100 fs) and energy conserved to 3×10⁻⁴ eV. This validates the implementation, not the choice of decoherence scheme.
- Unit-test the interface Hamiltonian on a case you can do by hand. Example: an equilateral s-hole trimer must give eigenvalues 0, 0, 3W.
- Compare FSSH(-EDC) with CSDM on the same seeds for the observable you report.

## 6. Initial conditions

- **Wigner sampling of the neutral, then a vertical transition**, keeping positions and velocities. Harmonic Wigner is fine for stiff modes. For soft, anharmonic modes with several near-degenerate minima (e.g. a molecule rotating on a surface, barrier ~2 meV), sample classically (Metropolis or a thermostatted MD run) on the true surface instead.
- **Metropolis chains remember their starting point.** Short chains started from one minimum over-sampled it (40/37/23 % vs 32/50/19 %). Use a long burn-in or draw from one long chain, and check the sampled distribution against a reference.
- **Classical 30 K Maxwell–Boltzmann has no zero-point energy.** Wigner widened one contact distance 2.5× and the site-energy spread 4–5×.
- **Check the initial electronic state.** Make sure SHARC does not re-pick the state by energy. When FSSH draws the active adiabat from |⟨k|initial⟩|², 9–12 % of draws landed on states mostly located elsewhere. Flag those trajectories and report them separately rather than dropping them.
- If the ensemble's distribution differs from the target (e.g. orientations), **reweight** the observables and report both raw and reweighted values.
- **Start a localized hole with `coeff external`, not `state N mch`.** An eigenstate is stationary, so a run started in one cannot show transfer (one ensemble's populations stayed frozen to 3 decimals for 300 fs). Write the hole as a superposition of eigenstates in a `coeff` file and set `state N` to the largest component. Check that projecting t = 0 returns the prepared hole.
- **Flat modes:** exclude near-free rotations (e.g. water on a symmetric Ar patch) from harmonic Wigner sampling with `wigner.py -L 50` (cm⁻¹ cutoff).
- **Geometry:** never optimize a vdW lattice with HF or MP2 (HF has no dispersion; an Ar–Ar distance built wrong gave 7.5× too small a coupling). Use the experimental fcc Ar distance, 3.756 Å, and print nearest-neighbour distances before launching.
- **Free clusters expand under Wigner zero-point energy** when the vdW well is shallow (Ar–Ar 3.75 → 4.28 Å over 600 fs). Hop rates from such runs are lower bounds.
- **Start a molecule at the method's own bond lengths.** Water at O–H 0.960 Å instead of the method's 0.9466 Å rang the O–H stretch and leaked 1–2 meV per step.
- **Frozen atoms need three changes:** zero gradient in the interface, zero initial velocity in `veloc`, and `atommask external` so hops do not re-accelerate them. SHARC ignores `atommask` with `ekincorrect parallel_nac`/`parallel_diff` (and the p- variants) and with `decoherence_scheme afssh`.

## 7. I/O, restart and cost

- **Stock `sharc.x` rewrites the whole formatted `restart.traj` every step**, and no keyword turns it off. At ~650 states that was 800 s per step and a 16.6 GB file. The group patch `sharc_lite.x` (`SHARC_RESTART_EVERY=K`, atomic write, forced write on STOP) fixes it. Source: `ICD/molcas_surface/dim/sharc_lite_src/`.
- **Restart needs** `restart` plus one of two keywords. `restart_goto_new_qm_step` is for a graceful stop (tmax, a `STOP` file, killafter), which is what the USR1 → STOP route in §8 produces. After a crash or a hard time-limit kill, the manual says to use `restart_rerun_last_qm_step` instead. Call `sharc.x` directly, because `run_sharc_file.sh` runs `rm -rf restart*`. Expect ~1e-4 eV differences from an uninterrupted run. If the interface keeps history (overlaps), save at least K steps of it or restart errors grow ~40×.
- **With many states, the cost is text I/O, not physics.** 85–90 % of the step went to writing and parsing `QM.out`. Thin the output with `output_dat_steps N`, `nowrite_overlap` and a lower `printlevel`. Trimming small couplings out of `QM.out` gave no speedup when the coupling matrix was dense.
- Time steps over a long stretch (≥ 1 h) before projecting cost (`pace-slurm` §6).
- **Killing `sharc.x` and starting it again restarts from t = 0** unless `input` has `restart` plus one of the two keywords above. Restart files on disk are not enough. Test the restart route on a cheap model before relying on it.
- **What is re-read when:** `input` is read once at start; `QM/*.resources` and the template are re-read every QM step, so interface settings can be changed in a running trajectory.
- **`ctrl%nsteps` is overwritten inside the time loop** (set to the current step), so patches must take the last step from `tmax`/`stepsize`.
- **`output.log` is appended, not overwritten**, so it can still hold crash text from before a restart. Judge progress by the step count in `output.lis`.

## 8. Ensembles on PACE

- **One Slurm job per trajectory.** Example shape: `-c 4 --mem=8G --tmp=20G` on cpu-medium. Write to node-local scratch and pack results (~8 GB raw `output.dat` per 2 ps became a ~160 MB npz).
- **Submit one trajectory first.** Check it for crashes, drift and the population trace before sending the batch. Send a cost estimate before any batch over ~5 node-days.
- `sbatch --export VAR=a,b` splits the value at the comma; 26 jobs failed at setup this way. Put defaults inside the script.
- Ask Slurm for `--signal=USR1@1800` and touch `STOP` on that signal, so SHARC writes a clean restart before the time limit.

## 9. Statistics and analysis

- Error bars on fractions are binomial (51/100 → 0.51 ± 0.05). n = 30 gives about ±0.09.
- Compare methods or settings **paired by seed** (same initial conditions).
- Recompute the kinetic energy from stored velocities and check that Σ|c|² = 1 when packing outputs.
- Check units after every transfer or parser change. One set of energies was 27.2× too large because the Hamiltonian was already in eV.
- **Count site hops, not raw "Surface Hop" lines.** With spin multiplets, each state appears once per Ms component, and the exactly degenerate copies switch constantly. Fold MCH indices onto sites with `((mch - 1) % nsite) + 1` and count changes (one ensemble: 44,677 raw events → 88 real hops). Report the full i → j census, not just a total.
- **`output.dat` coefficients are in the diagonal (diag) basis.** Transform to MCH with the `U matrix` block (c_MCH = U c_diag) before projecting onto sites; reading diag as MCH silently gives plausible but wrong populations. Check that t = 0 returns the prepared hole.

## 10. Ab initio SHARC (SA-CASSCF / OpenMolcas): why it was retired here

The details and settings are in `references/sa-casscf-openmolcas.md`; OpenMolcas errors are in `troubleshooting/references/openmolcas.md`.

- **Decisive reason: finite clusters gave wrong site energies.** Clusters small enough to afford gave ~50 meV offsets between sites that should be equivalent, larger than the ~20 meV 3s coupling, so the hole stayed stuck. Edge atoms have fewer neighbours to polarize, and polarization is long-ranged, so an 18-Ar buffer did not fix it. The group moved to a model Hamiltonian (DIM) built from ab initio pieces.
- **Cost:** 35–40 min per step for 17 atoms, and 8–16 meV jumps one step after state switches (§4).
- **Check orbital character at step 0.** Active spaces silently held the wrong orbitals (Ar 1s/3p, water lone pairs), giving step-0 state spreads of eV to keV. Choosing by energy ranking broke four set-ups, and choosing by Mulliken ownership alone also failed: a core 1s orbital is 100 % on its atom, so it won and gave a 3.2 keV collapse. **Pick by ownership inside an energy window:** occupied, ε in the valence window of the orbital you want (Ar 3s: −2.2 to −0.9 Ha), > 50 % on one atom. Print ε and shell for every pick and stop if |ε| > 5 Ha or ε > 0.
- **Launch gate:** compare the step-0 site-energy spread and the absolute state-averaged energy with a trusted single point (EOM-IP-CCSD at the same geometry and contact distance) before launching. A small spread alone does not prove the right hole.
- **MCLR rc = 96 had a structural cause.** Final diagnosis: core or doubly occupied orbitals in the active space (occupation exactly 2.0). With a clean 3s active space MCLR converged and the analytic gradient matched finite differences to 0.1–0.9 %. Loosening thresholds or raising iterations never helped.
- Check the geometry against the intended structure. A chain built at 4.600 Å instead of 3.756 Å gave a 2.7 meV coupling instead of ~20 meV.
- cc-pVDZ captured only ~35 % of the Ar polarizability, so site energies were wrong before any dynamics ran.

## 11. Not validated yet

- Tully models 1–3 benchmark.
- Census of frustrated hops (no parser yet).
- Residual +9–12 meV drift at DT 1 fs after patching.
- Whether the `grad_select` bug (#112) caused the per-hop energy losses in the DIM FSSH pilots or the 8–16 meV post-switch jumps in the SA-CASSCF runs, and whether the group build includes the fix. Cheap test: rerun one trajectory with `grad_all` from the same initial conditions.
- Precedent for absorbing boundaries in SH/CSDM (`sharc_abs.x`; see the reference file).
- Written justification that the force patch restores the published CSDM equations (`~/writeup_notes/csdm_patch_and_rim.md` on PACE).
