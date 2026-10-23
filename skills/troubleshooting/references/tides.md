# TiDES and real-time TDDFT: troubleshooting reference

Last researched: 2026-10-20

**How to use this file:** find the symptom in "Known issues" or "Group lessons", check the cause against your output, apply the fix, and confirm it with the starter calculations before you trust a production run. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official sources

**Paper.** M. C. Rohan, V. A. Suarez, M. Clothier, J. S. Kretchmer, "TiDES: A time-dependent electronic structure code for real-time electron and spin dynamics", *J. Chem. Phys.* **164**, 234117 (2026), published online June 2026. DOI [10.1063/5.0336359](https://doi.org/10.1063/5.0336359) ([article page](https://pubs.aip.org/jcp/article/164/23/234117/3395791/TiDES-A-time-dependent-electronic-structure-code)). The group's [publications page](https://kretchmergroup.chemistry.gatech.edu/publications/) lists the same record.

**Public code and documentation exist.** The repository is at <https://github.com/jskretchmer/TIDES> under Apache-2.0, linked from the group's [software page](https://kretchmergroup.chemistry.gatech.edu/software/). It contains a README tutorial, `function_documentation.pdf`, `examples/` and `Example_Workbook.ipynb`. There is no separate documentation website, and I found no PyPI package; you install it from GitHub.

**What TiDES is.** TiDES is a pure-Python layer on top of PySCF. It supports RT-TDHF and RT-TDDFT in restricted, unrestricted and generalized (GHF/GKS) form. It also has Ehrenfest dynamics, a molecular-orbital CAP (MOCAP), static magnetic fields, spin-orbit coupling and X2C through PySCF, and custom potentials and observables.

**Install.** Run `pip install git+https://github.com/jskretchmer/TIDES`. PySCF is a dependency. The README recommends an optimized BLAS (for example, scipy from conda) and warns that the default BLAS is slow.

**Workflow (README).**
1. Build a `gto.Mole`.
2. Converge a PySCF SCF (RHF/UHF/GHF/RKS/UKS/GKS).
3. Wrap it in `rt_scf.RT_SCF(mf, timestep, max_time)`, or use `rt_ehrenfest.RT_Ehrenfest(mf, timestep, max_time, Ne_step, N_step)` for moving nuclei.
4. Switch on observables.
5. Add potentials.
6. Call `kernel()`.

**Key options (README summary).**
- **Units:** `timestep` and `max_time` are in atomic units (1 fs is about 41.34 au), and the time step is fixed for the whole run.
- **Output control:** `frequency` sets how often observables print (default every step). `verbosity` uses PySCF levels 0–9, default 3. Observables print only above 2, nuclear velocities above 3 and forces above 4.
- **Propagator (`rt_scf.prop`):** `magnus_interpol` is the default and tolerates larger steps. `magnus_step` (MMUT) is mainly for reproducing older work, and `rk4` is also available.
- **Ehrenfest steps:** `Ne_step` is the number of electronic steps per nuclear position/velocity update (default 10). `N_step` is the number of nuclear updates per force evaluation (default 10).
- **Observables:** energy, dipole, quadrupole, charge, Mulliken and Hirshfeld atom charges, magnetization (including Hirshfeld), `mo_occ`, and nuclei (Ehrenfest only; writes `trajectory.xyz`).
- **Fields:** `rt_vapp.ElectricField('delta', [kx, ky, kz])` gives a delta kick. Other pulse types follow NWChem's conventions, but their parameters are not documented in the README (unverified).
- **CAP:** `rt_cap.MOCAP(expconst, emin, prefac=1, maxval=100)` applies imaginary damping to MOs above `emin`. It follows Lopata & Govind 2013 ([10.1021/ct400569s](https://doi.org/10.1021/ct400569s)).
- **Spectra:** `rt_spec.abs_spec(time, dipole, damping)` returns x/y/z oscillator-strength spectra in Ha; multiply by 27.2114 for eV.
- **Restart:** setting `rt_scf.chkfile` writes the current time and MO coefficients. To restart, point to an existing file, but **you must re-declare every propagation parameter, field and potential**, because none of them are stored.

**Examples in the repo.**
- **General examples in `examples/`:** water UV-Vis (RHF, RKS, GKS-X2C1e), Water_MOCAP, Water_ResonantExcitation, Li and TCNE charge transfer (NOSCF start), H2, H2 two-component and NaCl Ehrenfest, H in a B field, D3BJ and VV10 dispersion, Chkfile, custom/blank potentials and observables, and Multithreading_SLURM.
- **`examples/ExamplesFromOriginalTiDESPaper/`:** UV-Vis, XAS, ChargeMigration, ICD, SpinDynamics, Ehrenfest and X2C1e. These are the paper's inputs.

**Paper examples (parameters as reported in the paper).**

| Example | Level | dt (au) | Total (au) | Field | Damping |
|---|---|---|---|---|---|
| Benzene UV-Vis | B3LYP/6-31G* | 0.2 | 5000 | delta 1e-4, separate x/y/z runs | exp, τ = 250 |
| C/O K-edge XAS (paper text says both CO and CO2) | B3LYP/Sapporo-QZP-2012-diffuse | 0.02 | 2000 | delta 0.01 | exp, τ = 250 |
| Ethylene-chain charge migration | CAM-B3LYP/6-31G*, 3 Å stacking | not stated | ~12 fs | HOMO hole on molecule A via NOSCF | – |
| Water-dimer ICD | LC-PBE* (ω = 0.516)/aug-cc-pVDZ-type, MOCAP | – | ~20 fs | 2a1 inner-valence hole | – |
| Li3 spin precession | RT-GHF/3-21G, static B field | – | ~1.8 ps period | – | – |
| Cl2 Ehrenfest | UKS-B3LYP/6-31G(*) | 0.5 | – | 0–3 eV vibrational energy | – |

**Validation in the paper.**
- The benzene spectrum is checked against PySCF LR-TDDFT sticks, and the XAS spectrum is checked against NWChem.
- Cl2 Ehrenfest conserves total energy to about 0.1 meV with 6-31G and 0.01 meV with 6-31G*.
- The authors name a systematic Ehrenfest error, missing moving-basis (Pulay-type) terms, that a smaller dt does not remove.

**GPU.** Neither the README nor the readable parts of the paper mention GPU support (unverified). The group ran TiDES jobs on the PACE `gpu-v100` partition (see Group lessons), but the notes do not say whether TiDES itself used the GPU.

---

## Starter calculations

**1. Water UV-Vis, RHF (repo `Water_RHF_UV-Vis` / `Multithreading_SLURM`).**
- **Setup:** RHF/6-31G, dt = 1.0 au, max_time = 1000 au, delta kick 1e-4.
- **Expected result:** runs in seconds to minutes on 1–2 cores (README). Peaks should line up with LR-TDHF excitation energies from PySCF (`mf.TDHF()`), since this is the weak-field limit.
- **Resources:** 1 node, 2 CPUs, 16 GB, 1 h (the repo's Slurm header).
- **Most common mistake:** setting `MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` after `import pyscf`, when BLAS has already initialised. The repo script does this. Export them in the Slurm script, or set them before any import.

**2. Benzene UV-Vis vs LR-TDDFT (paper, `ExamplesFromOriginalTiDESPaper/UV-Vis`).**
- **Setup:** B3LYP/6-31G*, dt = 0.2 au, 5000 au per run, three runs (x, y, z kicks of 1e-4), τ = 250 au damping.
- **Expected result:** the RT peak positions match PySCF `TDDFT` roots, and the bright π→π* band sits at the LR-TDDFT value. The resolution is about 2π/5000 au ≈ 0.03 eV, and the τ = 250 broadening gives FWHM ≈ 2/τ ≈ 0.2 eV.
- **Resources:** 25,000 steps per direction on CPU. Hours per run (unverified); run the three directions as three jobs.
- **Most common mistake:** kicking all three directions in one run and calling the trace the isotropic spectrum. That works for small symmetric cases but not in general. Also, forgetting to divide by the kick strength gives intensities off by 1e4.

**3. Linear-regime and time-step check (do this before any new system).**
- **Setup:** repeat starter 1 or 2 with kick 1e-4 and 5e-5, then with dt and dt/2.
- **Expected result:** after dividing by κ, the spectra overlay. If a peak moves or a new peak appears with the larger kick, you are no longer in the linear regime.
- **Most common mistake:** reusing the 1e-4 valence kick for core edges. The paper used 1e-2 for XAS with dt = 0.02. Choose the kick for each problem and test it.

**4. Hole (charge-migration) dynamics with NOSCF (repo `Li_ChargeTransfer` / `TCNE_ChargeTransfer`, paper ethylene).**
- **Setup:** build fragment orbitals with `basis_utils.noscfbasis`, remove an electron from one fragment's HOMO, propagate 10–20 fs, and track Hirshfeld or `mo_occ`.
- **Expected result:** the hole oscillates between fragments. The oscillation slows as the separation grows (NWChem docs).
- **Most common mistake:** reading the energy relative to the SCF ground state. The NOSCF state is not an eigenstate, and the NWChem docs warn it carries an undetermined excess energy. Also, using a global hybrid or GGA here exaggerates self-interaction error; use a range-separated hybrid (see K4).

---

## Group lessons (from local notes)

Paths are relative to `/Users/owenhf/Documents/pace_snapshot_2026-10-04/`. All of these come from the Ar/H2O hole-dynamics project: CAM-B3LYP/aug-cc-pVDZ RT-TDDFT and Ehrenfest in TiDES.

**G1. Four TiDES bugs, found and fixed.** The bugs were density scrambling, CAP normalization, double printing of output, and stale checkpoints (`CALCULATIONS_LIST_with_values.md:1022`).
- If you see oddly jumping populations, a CAP that removes the wrong amount of charge, duplicated output lines, or a restart that resumes from the wrong state, first check that your TiDES copy includes these fixes.
- The notes do not record commit hashes or which version introduced the fixes (unverified).

**G2. First-force-after-restart bug in Ehrenfest.** After a restart from checkpoint, the first nuclear force was wrong. This caused a spurious water dissociation in earlier runs. It was fixed in all 10 of the group's driver scripts before the runs resumed on Oct 7 (`CALCULATIONS_LIST_with_values.md:1003`; `PROJECT_STATUS_2026-10-07.md:102`).
- **Lesson:** after any Ehrenfest restart, compare the geometry, velocities, energy and forces of the first post-restart steps with the last pre-restart steps. A jump means the restart is broken, not that the physics is real.
- The chkfile stores only the time and MO coefficients (README), so the nuclear state must be restored by the driver.

**G3. Walltime and segmented restarts.** The Ehrenfest jobs ran on V100 GPUs in 48 h segments and hit TIMEOUT repeatedly (`writing_materials/agent_messages/msg1_to_tides.txt:8`; `PROJECT_STATUS_2026-10-07.md:103-105`). The working procedure (`NEXT_SESSION_HANDOFF.md:194`) is:
1. Confirm that the `.out` tail shows TIMEOUT.
2. Rename the output to `<name>_segN.out` so it is not overwritten.
3. Resubmit the same `.spy` script, which reloads `Restart.chkfile`.

At about 200–280 fs per 48 h segment (`CALCULATIONS_LIST_with_values.md:1005-1009`), picosecond dynamics need many segments. Plan for this, or use a cheaper model.

**G4. Self-interaction self-trapping of the hole.**
- In frozen-nuclei Ar4·H2O RT-TDDFT runs (~2.1–2.2 ps), the hole stayed on its starting site in one geometry and split 50/50 in another. This was read as self-interaction self-trapping, not physics (`CALCULATIONS_LIST_with_values.md:1020`).
- In Ehrenfest runs, TDDFT "tends to self-trap" and disagreed with the DIM model in the opposite direction (`CALCULATIONS_LIST_with_values.md:1016`).

**G5. Water collapse onto Ar in Ehrenfest.**
- Earlier Ehrenfest runs collapsed, with O–Ar shrinking to 0.5–1.5 Å. This was attributed to self-interaction over-attraction (`CALCULATIONS_LIST_with_values.md:1021`; `writing_materials/DIM_METHODS_JUSTIFICATION.md:40`).
- **Caveats:**
  - CASSCF-Ehrenfest, which has no DFT self-interaction, also collapsed (`CALCULATIONS_LIST_with_values.md:882`).
  - G2 shows that at least one water dissociation was caused by the restart bug.
- So do not blame SIE alone. Rule out restart and force errors first.

**G6. TD-CASCI as an SIE-free reference.**
- **Setup:** frozen-nuclei TD-CASCI on the same cluster, CAS(37,19)/cc-pVDZ, 10 ps (`CALCULATIONS_LIST_with_values.md:873-881`).
- **Result:** hole sharing between two sites (periods of 50–78 fs) with no permanent transfer, which is qualitatively different from the RT-TDDFT trapping.
- **Use:** run this or a similar wavefunction check whenever RT-TDDFT shows a localized or trapped hole.

**G7. Hirshfeld charges are not hole populations.**
- No-CAP Hirshfeld charges showed the launch-site hole "refilling" by 0.17–0.19 e within ~200 fs, and the water gaining electrons. That gain is polarization, not hole capture (`CALCULATIONS_LIST_with_values.md:1011-1016`).
- Hirshfeld mixes 3s-hole transfer with 3p polarization. The fix was to project onto the relevant orbitals, using 2 − n_K(t) for the 3s orbital on site K (`CALCULATIONS_LIST_with_values.md:1017`).

**G8. Energy drift as a health check.** The healthy production runs drifted by 2–5 × 10⁻⁴ Ha over ~200 fs (`CALCULATIONS_LIST_with_values.md:1014`). Treat much larger drift, or a sudden jump, as a sign of a bug, a restart problem or a time step that is too large.

**G9. Group precedent for CAP RT-TDDFT.** Wang, …, Orlando & Kretchmer, JPCL **15**, 7806 (2024) modelled ICD with non-Hermitian RT-TDDFT ([PMC11299181](https://pmc.ncbi.nlm.nih.gov/articles/PMC11299181/); local summary `writing_materials/LIT_decay_in_hole_dynamics_2026-10-07.md:13,30`).
- **Setup:** NWChem, LC-PBE*, aug-cc-pVDZ on the trigger and d-aug-cc-pVDZ on the target; the CAP values are in the paper's SI.
- **Caveats the authors report:** charge-loss features depend on the CAP parameters; the final charge saturated near 1.6 rather than 2; the method failed for Ne–H2O and Ne–Ar (vdW-bound systems).

---

## Known issues and fixes (general RT-TDDFT)

**K1. Spectrum has aliased or garbage high-energy peaks.**
- **Cause:** the time step is too large for the highest frequency present.
- **Fix:** keep dt below π/ω_max, and ideally about a tenth of that.
  - Magnus with dt ≤ 0.2 au is fine for valence spectra.
  - Core edges need about 0.01–0.02 au (NWChem used 0.01; TiDES XAS used 0.02).
  - Confirm by halving dt. [NWChem RT-TDDFT](https://nwchemgit.github.io/RT-TDDFT.html); TiDES paper.

**K2. Energy blows up or the density loses idempotency.**
- **Cause:** an unstable propagator (Euler, or RK4 with a large dt).
- **Fix:** use a Magnus propagator (TiDES default `magnus_interpol`); keep RK4 for debugging only. [NWChem](https://nwchemgit.github.io/RT-TDDFT.html); TiDES README.

**K3. Peaks shift or extra peaks appear when you change the kick.**
- **Cause:** the response has left the linear regime.
- **Fix:** use a weak kick (1e-4 au, about 0.05 V/nm, for valence), rerun with a smaller kick, and divide the dipole by κ. In the weak-field limit, RT and LR spectra should coincide. [NWChem](https://nwchemgit.github.io/RT-TDDFT.html)

**K4. Peaks are too broad to resolve, or have sinc ripples and negative lobes.**
- **Cause:** total time T is too short, there is too little damping before the FFT, or there is zero-padding without damping.
- **Fixes:**
  - Resolution is about 2π/T.
  - Multiply the dipole by exp(−t/τ), giving Lorentzians of FWHM ≈ 2/τ, and make sure the signal has decayed by t = T.
  - Damp properly if you zero-pad.
- [NWChem](https://nwchemgit.github.io/RT-TDDFT.html); TiDES paper used τ = 250 au with T = 2000–5000 au.

**K5. Pulse run shows a broad low-energy artifact.**
- **Cause:** the pulse envelope is not zero at t = 0 (windowing).
- **Fix:** centre a Gaussian pulse far enough out that the field is about 1e-8 of its maximum at t = 0. [NWChem](https://nwchemgit.github.io/RT-TDDFT.html)

**K6. Absorption peaks drift during strongly driven or resonant dynamics.**
- **Cause:** adiabatic xc functionals produce spurious time-dependent resonance positions away from the ground state. Exact dynamics change peak intensities, not positions.
- **Fix:** treat strongly driven RT-TDDFT populations qualitatively, check against a wavefunction method (TD-CI/TD-CASCI; see G6), and expect charge transfer to be incomplete.
- [Provorse, Habenicht & Isborn, JCTC 11, 4791 (2015)](https://sites.ucmerced.edu/cisborn/publications/peak-shifting-real-time-time-dependent-density-functional-theory); [Luo, Fuks & Maitra, arXiv:1605.05800](https://ar5iv.labs.arxiv.org/html/1605.05800)

**K7. Charge transfer from a prepared hole does not complete, or stalls.**
- **Cause:** a missing exact-condition in adiabatic functionals; it also happens with self-interaction-corrected LSD.
- **Fix:** do not interpret incomplete transfer as physics without a wavefunction check. Use exact exchange or a range-separated hybrid. [Luo, Fuks & Maitra](https://ar5iv.labs.arxiv.org/html/1605.05800)

**K8. Hole delocalizes too fast, or self-traps or splits unphysically.**
- **Cause:** self-interaction/delocalization error.
- **Fix:** use long-range-corrected or tuned range-separated hybrids (CAM-B3LYP, LC-PBE*), which is standard practice for RT charge dynamics. Then validate against TD-CASCI/EOM (G4, G6).
- [Wang et al. JPCL 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11299181/); [APS 2024 abstract](https://meetings-archive.aps.org/mar/2024/d39/1) (search summary)

**K9. Errors depend on system size in RT-TDHF/TDDFT.**
- **Cause:** density-evolution errors away from the ground state are size dependent, and they are largest for small systems.
- **Fix:** do not extrapolate model-system failures blindly; test at the size you care about. [Ranka & Isborn 2023 (chemRxiv)](https://chemrxiv.org/engage/chemrxiv/article-details/63c07a50d19cc537ad03b1c1) (read via search summary only, unverified)

**K10. Spurious high-energy features, or charge piling up in diffuse functions above the ionization threshold.**
- **Cause:** a finite Gaussian basis cannot represent the continuum, so ionized density reflects back.
- **Fix:** add an MO-based CAP (TiDES `MOCAP`; NWChem example: emin 0.5 Ha, expconst 1.0, prefac 1.0, maxval 100 Ha). Compare the dipole with and without the CAP.
- [Lopata & Govind JCTC 9, 4939 (2013)](https://repository.lsu.edu/chemistry_pubs/718); [NWChem](https://nwchemgit.github.io/RT-TDDFT.html)

**K11. CAP results change with the CAP parameters.**
- **Cause:** the CAP is an empirical boundary; charge loss depends on emin and the damping.
- **Fixes:**
  - Scan emin and expconst.
  - Report observables that are insensitive to them, for example sums over occupied MOs up to the original HOMO.
  - Note that the total charge may saturate below the expected value.
- [Wang et al. JPCL 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11299181/)

**K12. XAS spectrum contaminated by continuum transitions.**
- **Cause:** the broadband kick excites valence-to-continuum transitions that overlap the edge.
- **Fixes:**
  - Use a core-capable diffuse basis (TiDES paper: Sapporo-QZP-2012-diffuse).
  - Use a small dt (0.01–0.02 au).
  - Add a CAP to remove basis-set artifacts.
  - Compare with a reference code.
- TiDES paper; [Lopata & Govind 2013](https://repository.lsu.edu/chemistry_pubs/718)

**K13. Rydberg or diffuse states are missing or far too high.**
- **Cause:** the basis has no diffuse functions. RT-TDDFT inherits the basis and functional of the ground state.
- **Fix:** use augmented basis sets (aug-, d-aug-; the ICD work used d-aug-cc-pVDZ on the acceptor). Then check convergence against LR-TDDFT in the same basis. [NWChem](https://nwchemgit.github.io/RT-TDDFT.html); [Wang et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11299181/)

**K14. Charge-migration run starts with odd energy or unphysical oscillations.**
- **Cause:** the NOSCF or "hole by hand" initial state is not an eigenstate, so it carries extra energy. The sudden-ionization assumption can also fail for realistic pulses.
- **Fix:** report the initial-state energy, compare more than one preparation (NOSCF vs constrained DFT), and avoid over-interpreting the first femtoseconds.
- [NWChem](https://nwchemgit.github.io/RT-TDDFT.html); [epjb 2018 TD-DFTB caffeine (search summary)](https://epjb.epj.org/articles/epjb/abs/2018/07/b180223/b180223.html) (unverified)

**K15. Ehrenfest gives an average of two channels instead of branching.**
- **Cause:** a mean-field force with no decoherence or branching. It also does not satisfy detailed balance, so it overheats electrons at long times.
- **Fix:** use it for short times or nearly parallel states. For branching processes, use surface hopping or Ehrenfest with decoherence (CSDM), as the group did with SHARC.
- [Holstein-model Ehrenfest study, arXiv:2203.07245](https://arxiv.org/pdf/2203.07245) (search summary); [Shu & Truhlar 2024](https://arxiv.org/html/2311.16995v2) (search summary)

**K16. Ehrenfest energy drift does not improve with a smaller dt.**
- **Cause:** the moving-basis (Pulay) terms are missing from the Gaussian-basis Ehrenfest forces. This error is systematic, not numerical.
- **Fix:** use a larger, more complete basis (the drift dropped about 10× from 6-31G to 6-31G* in the paper). Check energy conservation against BOMD at low energy. TiDES paper (Cl2 section).

**K17. Ehrenfest run is slow, or MTS factors are too large.**
- **Cause:** the `Ne_step`/`N_step` multiple-time-step factors (default 10 × 10) are too aggressive for light atoms or fast motion.
- **Fix:** reduce them and check energy conservation; the paper used dt = 0.5 au for Cl2. TiDES README and paper. Safe values for H-containing systems are unverified.

**K18. Calculation very slow on CPU.**
- **Cause:** PySCF is linked to the reference BLAS, or the thread environment variables were set too late.
- **Fix:** use conda scipy or MKL, and export `MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` (= `SLURM_CPUS_PER_TASK`) with `OMP_NUM_THREADS=1` in the job script. [TiDES README](https://github.com/jskretchmer/TIDES); repo `examples/Multithreading_SLURM`

---

## Open questions / could not verify

- **GPU:** whether TiDES has native GPU support (for example, through gpu4pyscf or CuPy), and what exactly ran on the V100 nodes in the group's jobs. Neither the README nor the readable parts of the paper mention GPUs.
- **Fixes in the public repo:** whether the four bug fixes in G1 and the restart-force fix in G2 are merged into the public `main` branch, or live only in the group's local drivers. Check `git log` before relying on them.
- **Field parameters:** pulse types other than `delta` (Gaussian, CW, Hann); their argument names are not documented in the README.
- **Damping argument:** the units and meaning of the `abs_spec` damping argument (assumed τ in au, as in the paper).
- **Missing paper details:** the ethylene time step and part of the paper's middle section (about 25 kB was not read). The XAS molecule is named inconsistently (CO vs CO2) in the paper text.
- **Ehrenfest restarts:** whether the chkfile stores nuclear positions and velocities. The README says only the time and MO coefficients, so the drivers must restore them.
- **Missing source types:** no Matter Modeling SE or PySCF forum threads on RT-TDDFT turned up in the searches. K9, K14 and K15 rely on search summaries rather than full reads.
- **Timing:** the time per run for the benzene benchmark on PACE CPU nodes has not been measured.
