---
name: sharc
description: Recipes and pitfalls for nonadiabatic dynamics with SHARC 3.x - surface hopping (FSSH, EDC), Ehrenfest and CSDM, dense or near-degenerate state manifolds, model-Hamiltonian (file-based) interfaces, energy-conservation checks, initial conditions, restart/I-O cost, and running trajectory ensembles on PACE. Use when planning, setting up, debugging or analysing any SHARC or surface-hopping / mixed quantum-classical dynamics run.
---


# SHARC dynamics in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. Ask before running or submitting anything. See `troubleshooting` §2.

Most of these notes come from one project: an Ar 3s hole in a ~140-site band next to a water, driven through a file-based model-Hamiltonian (DIM) interface. Many lessons are about **dense, flat manifolds** (many states within ~20 meV), where SHARC's defaults break. On a few well-separated states the defaults are usually fine. Project-specific settings are in `references/dim-ar-water.md`.

Before setting anything up, check with `method-selection` that surface hopping is the right tool. Submission follows `pace-slurm` §0: propose, then wait for an explicit OK. For anything not covered here, follow the `troubleshooting` skill (manual → GitHub issues → literature) before guessing.

## 1. Version, driver, binaries

- **Group install:** SHARC 3.0.2 under `/storage/project/r-jkretchmer3-0/oholtfrank3/ICD/software/sharc`; environment from `sharc_dynamics/sharc_env.sh`.
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

- **Measure drift against the energy scales that matter:** the kinetic energy of the moving atoms, the range of the potential, the coupling and kT. Never compare it with the absolute total energy, which has an arbitrary zero. Production target: ≲ 1 % of the kinetic energy per run. The production DIM runs reached 0.1–0.5 meV over 2 ps.
- **Stock SHARC `scp` with overlap coupling gets the coherence force wrong in dense bands.** It scales the force by NACdt/(v·d), with NACdt taken from overlaps, and in a dense band NACdt ≠ v·d. On single steps the mean-field force was 9–61 % off the exact force, even though small-system populations looked fine. Drift at 60 fs on one stress case:

  | Run | DT 1 fs | 0.5 | 0.25 | 0.1 |
  |---|---|---|---|---|
  | stock Ehrenfest + `nacdr` | +47 meV | +30 | +11 | +2.7 |
  | patched (rescale removed) + `nacdr` | +12.1 | +7.9 | +1.4 | — |
  | exact force computed in the interface | −0.7 | — | — | — |

  The patch removes a two-line rescale in `qm.f90` (~line 1371); no keyword is equivalent (`coupling ddr` is a weaker fallback). `nacdr` on its own, with the stock binary, did **not** help. The best route is to compute the exact force in the interface (group binary `sharc_force.x`, `SHARC_EXACTFORCE=1`). It agreed with the patched result to ~1 meV and was 2.6–3.5× faster. **This only works when the interface can return the density-weighted exact force Σ Re(ρ_ij)⟨i|∇H|j⟩**, as a model Hamiltonian can. A typical ab initio overlap interface gives only state gradients. There, use the patched binary with derivative couplings (`nacdr`).
- **A smaller time step hides the bug, it does not fix it.** "DT too coarse" was tested and refuted as the cause. Production used DT 0.25 fs (CSDM) and 1 fs (FSSH).
- **Energy jump right after a hop with `grad_select`.** The group's FSSH and FSSH-EDC pilots wrote `grad_select`; the CSDM production runs did not. In SHARC 3.0.2 the gradient is zero on the step after a hop, which gives an energy jump (sharc-md/sharc issue #112). It was fixed on `main` in May 2024 but not in any 3.x release. Avoid `grad_select` with 3.0.2, or build from a patched `main`.
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

## 7. I/O, restart and cost

- **Stock `sharc.x` rewrites the whole formatted `restart.traj` every step**, and no keyword turns it off. At ~650 states that was 800 s per step and a 16.6 GB file. The group patch `sharc_lite.x` (`SHARC_RESTART_EVERY=K`, atomic write, forced write on STOP) fixes it. Source: `ICD/molcas_surface/dim/sharc_lite_src/`.
- **Restart needs** `restart` plus one of two keywords. `restart_goto_new_qm_step` is for a graceful stop (tmax, a `STOP` file, killafter), which is what the USR1 → STOP route in §8 produces. After a crash or a hard time-limit kill, the manual says to use `restart_rerun_last_qm_step` instead. Call `sharc.x` directly, because `run_sharc_file.sh` runs `rm -rf restart*`. Expect ~1e-4 eV differences from an uninterrupted run. If the interface keeps history (overlaps), save at least K steps of it or restart errors grow ~40×.
- **With many states, the cost is text I/O, not physics.** 85–90 % of the step went to writing and parsing `QM.out`. Thin the output with `output_dat_steps N`, `nowrite_overlap` and a lower `printlevel`. Trimming small couplings out of `QM.out` gave no speedup when the coupling matrix was dense.
- Time steps over a long stretch (≥ 1 h) before projecting cost (`pace-slurm` §6).

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

## 10. Ab initio SHARC (SA-CASSCF / OpenMolcas): why it was retired here

- It cost 35–40 min per step for 17 atoms, with recurring MCLR divergence (rc = 96) and 8–16 meV jumps at trivial crossings.
- **Check orbital character at step 0.** Active spaces silently held the wrong orbitals (Ar 1s/3p, water lone pairs), giving step-0 state spreads of eV to keV. Choosing orbitals by energy ranking broke four set-ups. Assign by Mulliken ownership (`methods/tdcasci_ehrenfest/orbital_owner.py`).
- Check the geometry against the intended structure. A chain built at 4.600 Å instead of 3.756 Å gave a 2.7 meV coupling instead of ~20 meV.
- cc-pVDZ captured only ~35 % of the Ar polarizability, so site energies were wrong before any dynamics ran.

## 11. Not validated yet

- Tully models 1–3 benchmark.
- Census of frustrated hops (no parser yet).
- Residual +9–12 meV drift at DT 1 fs after patching.
- Whether the `grad_select` bug caused part of the per-hop energy losses in the FSSH pilots. Cheap test: rerun one pilot without `grad_select`.
- Precedent for absorbing boundaries in SH/CSDM (`sharc_abs.x`; see the reference file).
- Written justification that the force patch restores the published CSDM equations (`~/writeup_notes/csdm_patch_and_rim.md` on PACE).
