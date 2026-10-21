# DIM Ar 3s hole + water in SHARC (Oct 2026): project-specific settings

Settings and lessons from one project. Copy the reasoning, not the numbers. Paths are under `/storage/project/r-jkretchmer3-0/oholtfrank3/ICD/` on PACE.

## Model and interface
- **Hamiltonian:** one 3s-hole state per Ar (diatomics-in-molecules), with self-consistent polarization and a rigid water. H_KL = +W ≈ 18 meV, so the hole sits at the lowest eigenvalue (the −4W flat-band edge on fcc). Methods write-up: `writing_materials/DIM_METHODS_JUSTIFICATION.md` §0b–§3.
- **Interface:** `sharc_dim/dim_qm_server.py`.
  - Gradients come for all states (state densities U_kU_kᵀ), and couplings from transition densities.
  - The water rows are projected onto rigid-body motion (`DIM_RIGIDPROJ=1`).
  - RATTLE keeps the water rigid.
- **How the link works (confirmed Oct 21 by the surface-hopping agent):** file-based per step, with a persistent server. SHARC calls `QM/runQM.sh` → `qm_client.py`, which pings the server through `QM/req.fifo`. The server reads `QM/QM.in`, writes `QM/QM.out` (H diagonal, zero dipoles, overlaps, all gradients) and answers on `QM/resp.fifo`. "In-memory" in the methods write-up only means the DIM model is loaded once per run, with U and sign-chain state kept in `Ucur.npy`, `Uprev.npy` and `key.txt`.
- **`SHARC_EXACTFORCE=1`:** the server also reads SHARC's amplitudes from `QM/coeff.dat`, builds F = Σ Re(ρ_ij)⟨i|∇H|j⟩ plus the neutral and water terms (rigid-water projected), and writes `QM/force.dat` in Ha/bohr. `sharc_force.x` uses that as the nuclear force.
- **Binaries:**
  - `sharc_lite.x`: restart every K steps.
  - `sharc_exact.x`: coherence-force rescale removed.
  - `sharc_force.x` with `SHARC_EXACTFORCE=1`: exact force computed in the interface. This is the production binary.
  - `sharc_abs.x`: absorbing edge.
- **`DIM_REFIT=2` trap:** `ARW_PARAMS` also feeds the short-range hole–O term. Pointing it at the base parameter file silently removes a term from the hole Hamiltonian. Keep the hole Hamiltonian identical across neutral-surface variants.
- **Speed:**
  - Vectorizing the gradient build: 6.5–8×.
  - Gradients for mobile atoms only: server at 1.5–5 s per step.
  - Production: about 3.2–4.3 s per step at 138 sites; 2 ps took ~9.6 h.

## Production settings (Oct 15)
- CSDM in `sharc_force.x`, DT 0.25 fs, nsubsteps 25.
- FSSH-EDC (DT 1 fs) as the comparison set. Contact weight 0.19 vs 0.20 at 300 fs.
- Region U:14,12 (138 sites). Doubling it changed trapping by −0.02 ± 0.02.
- `SHARC_RESTART_EVERY=250`, `DIM_UHIST=260`.
- Superseded designs, do not reuse:
  - FSSH-EDC as the main method;
  - DT 0.5 fs;
  - decay as stochastic events inside the trajectories;
  - the 55-site region.

## Finite region and edge
- The 55-site region was far too small: the hole sat on its boundary 98 % of the time.
- Coherent holes spread at ~0.2 Å/fs.
- **Rim error:** site energies within 6 Å of the 658-Ar cylinder rim are off by 40–220 meV.
  - `rimcorr_16_10_to_40_13.npz` brings this to ~1 meV rms. It adds no force.
  - The clean window for far starts is still only 40–60 fs.
- **Reflecting edge:** about half of the hole sits in the edge shell by 300 fs, and ~15 % returns. For first-shell starts the reflecting-edge contact weight (0.02) was entirely returned density; with the absorbing edge it was 0.001.
- **Absorbing edge** (`sharc_abs.x`): c ← exp(−Γdt/2)c with γ = 0.3 eV over 4 Å.
  - It is applied after switching/decoherence and before gradient mixing.
  - It had to be added to the fixed-step integrator as well as the adaptive one.
  - Validated against exact non-Hermitian propagation to 0.002.
  - Absorbed weight means "left the region", never decay.
  - It is not used with FSSH, because damping would change hop probabilities.
  - E_tot is no longer conserved, by construction.
- **Mobile region:** 36–58 Ar move. The rest of the slab is frozen but stays in the Hamiltonian and polarizable. Phonons reflect at the frozen boundary.

## Initial conditions (changed three times)
1. 30 K Maxwell–Boltzmann with ±0.08 Å displacements. No zero-point energy; superseded.
2. Harmonic Wigner at 30 K for the Ar, plus Metropolis for the water's six rigid-body modes (`molcas_surface/dim/wigner_ic.py`). Short chains over-sampled H-up.
3. Ar Wigner plus a 30 K Langevin AIMD run for the water. This gives orientations of 31/51/18 %.
- 30 K is close to the Ar zero-point-equivalent temperature, ≈ (3/8)θ_D ≈ 34 K.
- **Orientation target:** first 6/49/45 (coupled-cluster estimate), later 24/51/25 ± 10 points.
  - Trapping comes from H-up-like starts, so reweighting matters: contact weight 0.20 → 0.13–0.18.
  - All 24 H-down runs flipped orientation during the dynamics.
- **Water height:** a 0.2 Å error in water height barely mattered (trapped fraction 0.24 vs 0.27); orientation did.

## Observables
- **Contact weight:** wavefunction population on the 3 contact Ar. "Trapped" means > 0.5 at 300 fs. The weight at 50 fs already predicts the outcome (AUC 0.99).
- **Other outputs:** density budgets by region, KE maps, and site energy Hdiag − Vn, packed per trajectory as `dimtraj.npz` plus `audit.json`.
- **Decay is post-processing:** S(t) = exp[−∫Γ/ħ] with Γ = Σ P_K Γ_K. This is valid only while Γ ≪ W. The contact Γ of 2–3 meV makes that borderline.

## Corrected claims (do not repeat)
- "7–13 meV per 300 fs accepted" came from DT 0.5, 55-site stress tests, not production.
- "DIM self-trap 1.9× deeper than EOM" probably compared a total adiabatic energy with a site energy. An EOM check at t = 200 fs agrees within 2–17 meV. Status: under review.
- "`nacdr` does not fix the drift" was tested with the stock binary only. It helps together with the rescale patch.
- "wETMD closed after trapping" was retracted.
