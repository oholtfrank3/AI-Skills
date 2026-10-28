# TiDES and real-time TDDFT: troubleshooting reference

Last researched: 2026-10-23 (GPU wrapper and group bug list added from the group's TiDES checkout and ICD session notes)

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

**GPU.** The README and the readable parts of the paper do not mention GPUs, but the group's TiDES checkout has a GPU wrapper: `wrap_gpu_mf` in `src/tides/utils/rt_gpu.py`. The group's notes say it was added in commit `336f340` (June 2026, with no example); the latest commit touching the file in the checkout is the restructure `f7e0419`. The checkout's remote is a private fork, so whether the public jskretchmer/TIDES repo has it is unverified. What the file's docstring and code say:
- It takes a **converged** gpu4pyscf SCF object (raises `RuntimeError` if not converged, `TypeError` if it is not a gpu4pyscf object, `ImportError` without cupy/gpu4pyscf) and returns a CPU PySCF object whose `get_fock` and `energy_tot` run on the GPU. That object is "a drop-in replacement" for the `scf` argument of `RT_SCF` / `RT_Ehrenfest`.
- Docstring example: `mf_gpu = gpu_dft.uks.UKS(mol).density_fit()`, `mf_gpu.xc = 'CAMB3LYP'`, `mf_gpu.kernel()`, `mf = wrap_gpu_mf(mf_gpu)`, then `rt_scf.RT_SCF(mf, timestep, max_time, prop='ep_pc', ...)`.
- Install: `pip install cupy-cuda12x` and `pip install gpu4pyscf-cuda12x` (cuda11x variants for CUDA 11).
- Complex densities are split into real and imaginary parts; the XC term is evaluated only on the real part (code comment: "standard approximation").
- Only UKS/UHF GPU workflows are tested (code comment); RKS is included but not tested.
- The CPU copy is density-fitted (`.density_fit()`) whatever the GPU object used.

Group measurement (water dimer, CAM-B3LYP/aug-cc-pVDZ, `ep_pc`, dt 0.5 au, 200 steps): one V100 462 ms/step; CPU 1/2/4/8/12/16 threads 4359/2872/2240/2030/1910/2100 ms/step, so 12 threads was the best CPU setting (16 was slower) and the GPU was ~4.1× faster. Slurm lines used: `--partition=gpu-v100`, `--gres=gpu:V100:1`, `module load cuda/12.6.1`. Ehrenfest and D3 need extra steps (K26).

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
- Details of each bug are in K19–K25 below. Not every fix has a recorded commit hash (unverified).

**G2. First-force-after-restart bug in Ehrenfest.** After a restart from checkpoint, the first nuclear force was wrong. This caused a spurious water dissociation in earlier runs. It was fixed in all 10 of the group's driver scripts before the runs resumed on Oct 7 (`CALCULATIONS_LIST_with_values.md:1003`; `PROJECT_STATUS_2026-10-07.md:102`).
- **Lesson:** after any Ehrenfest restart, compare the geometry, velocities, energy and forces of the first post-restart steps with the last pre-restart steps. A jump means the restart is broken, not that the physics is real.
- The README says the chkfile stores only the time and MO coefficients, but in the group's checkout Ehrenfest chkfiles also hold `Position`, `Velocity` and `Force` sections, which `RT_Ehrenfest.__init__` restores. Mechanism and fix: K22; related velocity bug: K23.

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

**G10. Controls, sampling and timing (group lessons, 2026).**
- **Isolated-atom control:** an isolated Ar⁺ 3s hole cannot refill in adiabatic TDDFT, because the spherical 3s⁻¹ determinant does not couple different l. The control showed only ~1 % breathing, so it cannot separate real refilling from a mean-field artifact.
- **Output stride:** a print stride of `nstep//200` sampled a 10 ps run every 50 fs and a 1 ps run every 5 fs, and the longer run reported a smaller maximum. The conclusion reversed with a fixed 2 fs stride.
- **Initial density:** a script built a custom initial density, checked its electron count, but never assigned it to `rt_mf.den_ao`, so the run started from the ground state. Assign it and print its trace and a population after setup.
- **Temperature:** one Ehrenfest set sampled velocities at 13 K for a 30 K experiment. Check the sampled temperature against the experiment before interpreting nuclear motion.
- **Timing:** quote ms/step together with dt; fs per wall-hour = (3600 / seconds per step) × dt(au) / 41.34.

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

### TiDES code issues found by the group (2026)

These come from the group's Ar/water hole-dynamics runs on the group's checkout (branch `devel_hackathon`). Line numbers and function names are from that checkout and may differ in yours. Whether each fix is in the public repo is unverified; check `git log` and the source.

**K19. A "fresh" run starts from an old state, or restart crashes with `UnboundLocalError: 'b1'`.**
- **Cause:** `RT_SCF.__init__` defaults `chkfile` to `'tides.chk'` and, if that file (or the named `Restart.chkfile`) exists in the run folder, restarts from it automatically. A stale chkfile from another run silently replaces your initial state. In `restart_from_chkfile` (`src/tides/utils/rt_utils.py`) the `ep_pc` branch had two bugs: `mo_beta` was read to the end of the file (past the `Position`/`Velocity`/`Force` sections that Ehrenfest writes) instead of stopping at `Position`, and `b1` was never assigned on that path.
- **Fix:** delete `Restart.chkfile`, `tides.chk` and `chkfiles/` before any fresh run. On restart the evolved MO coefficients come back but occupations reset to neutral, so re-apply `rt_utils.excite(...)` (this part is intended). If an Ehrenfest `ep_pc` restart crashes while parsing `mo_beta`, bound the read at the `Position (AU):` line and guard the `b1` use.
- **Source:** group ICD session notes, Sep 2026.

**K20. Density scrambles as soon as the nuclei move (Ehrenfest).**
- **Symptom:** `mo_occ` turns fractional and the energy diverges at the first nuclear step. Not seen in the shipped 2-atom NaCl example.
- **Cause:** `RT_Ehrenfest.update_mol` sets a new (symmetric) `orth` but never updates `orth_inv`, which `RT_SCF.__init__` cached from a different (canonical) orthogonalization. The two rotations no longer invert each other.
- **Fix:** after every `update_mol`, set `rt.orth_inv = numpy.linalg.inv(rt.orth)`, and fix the stale one left by `__init__`. With this, energy was conserved to ~1e-10 Ha (CPU) and ~4e-5 Ha (GPU) on a 4-Ar + H2O test.
- **Source:** group session notes. A bare CPU 6-31G test ruled out the integrator, GPU wrapper, basis and dt.

**K21. `ImportError` from scripts that used to work.**
- **Cause:** commit `f7e0419` ("massive restructure") moved modules into `src/tides/{methods,potentials,nuclear,propagators,observables,utils,decoherence}/`. `tides/__init__.py` re-exports only the top-level classes (`RT_SCF`, `RT_Ehrenfest`, `RT_CAS_RAS`, `MOCAP`, `ElectricField`, `static_bfield`).
- **Fix:** use the new paths: `from tides.methods import rt_scf, rt_ehrenfest, rt_cas_ras`; `from tides.utils import rt_utils, basis_utils`; `from tides.utils.rt_gpu import wrap_gpu_mf`; `from tides.potentials.rt_cap import MOCAP`; `from tides.potentials.rt_vapp import ElectricField`; `from tides.nuclear import ehrenfest_force, rt_nuclei`; `from tides.propagators import rt_integrators`. Analysis modules moved to `tides.analysis.*` (e.g. `tides.analysis.parse_rt`, `tides.analysis.rt_spec`).
- **Two API changes:** custom observables `[compute_fn, print_fn]` now each take one argument (`rt_obj`; read `rt_obj.den_ao` inside). And `RT_Ehrenfest.__init__` calls `ehrenfest_force.get_force(self)` and `update_mol()` once itself, so a patch of `get_force` (frozen atoms, D3) must be installed **before** constructing `RT_Ehrenfest`.
- **Source:** group session notes, checked against the checkout's source.

**K22. Huge force on the first step after an Ehrenfest restart.**
- **Symptom:** at the same simulated time, a hydrogen force was 0.0069 Ha/Bohr before the restart and ~2.9 Ha/Bohr after it; a water then dissociated.
- **Cause:** `RT_Ehrenfest.__init__` builds the density with the still-neutral occupations, then computes forces (the source has a reminder comment to update forces after `excite()`). On a fresh start this is harmless; on a restart the orbitals are the evolved, hole-bearing ones, so the neutral-occupation density is unphysical. The driver's later `excite()` fixes the density but not `nuc.force`, and the first velocity update uses the stale force.
- **Fix:** right after `rt_utils.excite(rt_mf, ...)` and before `rt_mf.kernel()`, add `rt_mf.nuc.force = ehrenfest_force.get_force(rt_mf)`.
- **Source:** group session notes, Sep 30 – Oct 2 2026 (applied to all 10 group drivers).

**K23. Nuclear kinetic energy drops back to its starting value at every restart.**
- **Cause:** `RT_Ehrenfest.__init__` restores positions, velocities and forces from `Restart.chkfile`, but the drivers then called `nuc.sample_vel(...)` unconditionally, overwriting the restored velocities with a new thermal sample.
- **Fix:** `_RESTARTING = os.path.exists('Restart.chkfile')`, and sample only `if not _RESTARTING:`. After the next restart, check that the kinetic energy does not jump.
- **Source:** group session notes, Oct 9 2026.

**K24. Workup scripts crash or misalign; observables have exactly twice as many rows as `time`.**
- **Cause:** from commit `336f340` until a fix on 2026-09-02, `get_observables` (`src/tides/observables/rt_observables.py`) called each print function inside its loop, and `update_output` printed again. The paper's figures predate this.
- **Fix:** delete the `function[1](rt_obj)` call from the loop. After any run check `parse_output(f)['time'].shape[0] == parse_output(f)[key].shape[0]`.
- **Source:** group session notes, Sep 2 2026.

**K25. CAP + Ehrenfest: charge drains and forces may go wrong.**
- **Cause:** `MOCAP` adds an anti-Hermitian term to the Fock matrix and nothing renormalizes the density afterwards (the only trace computed is recorded as the charge observable). `ehrenfest_force.py` builds forces from that shrinking, complex density with no correction. A propagator fix for the non-Hermitian Fock exists (commit `f409900`), but not a force fix. A CAP-off control also collapsed, so the CAP may not be the only problem.
- **Also:** check how many virtuals lie above `emin`. In a 17-atom Ar/water cluster, `emin = 0.0477 Ha` damped 99 % of 216 virtuals; `emin = 0.15 Ha` excluded only ~13 more and charge loss at 6.65 fs barely changed (0.042 vs 0.046 e).
- **Fix:** none in the code yet. Track Tr(P·S) and key distances over time, and compare with CAP-off and frozen-nuclei runs before trusting CAP-Ehrenfest geometries.
- **Source:** group session notes, Sep 23–30 2026.

**K26. GPU wrapper with Ehrenfest or D3 dispersion.**
- **Ehrenfest:** `wrap_gpu_mf` keeps the GPU SCF object built at t = 0, so call `mf_gpu.reset(current_mol)` in the same `update_mol` hook as the K20 fix.
- **D3:** setting `mf.disp = 'd3bj'` does nothing here. TiDES's `ehrenfest_force.py` uses its own complex-density gradient, not PySCF's `Gradients.kernel()`, and `wrap_gpu_mf` replaces `energy_tot`. The group added D3 by hand with `pyscf.dispersion.dftd3.DFTD3Dispersion` at the current geometry, as a force term in `ehrenfest_force.get_force` (patched before constructing `RT_Ehrenfest`, K21) and as an energy term on `mf.energy_tot`. Test the D3 call on an Ar dimer first.
- **Source:** group session notes, Sep 24 2026; `rt_gpu.py` in the group checkout.

**K27. Mirror-image atoms behave differently in a symmetric cluster.**
- **Cause:** PySCF's DFT quadrature grid is not symmetrized (the log prints `symmetrized grids: False`). Small grid asymmetries grow over hundreds of fs of nonlinear propagation: two mirror-equivalent atoms differed by more than 2× (−0.063 vs −0.147 e) with frozen nuclei.
- **Fix:** trust only large, consistent trends; don't compare one atom with its mirror partner. Whether a finer grid removes it is untested.
- **Source:** group session notes, Sep 2026.

---

## Open questions / could not verify

- **GPU:** whether `wrap_gpu_mf` (`src/tides/utils/rt_gpu.py`) is in the public repo, and whether RKS/RHF GPU runs work (the code says only UKS/UHF are tested).
- **Fixes in the public repo:** whether the fixes in G1, G2 and K19–K24 are merged into the public `main` branch, or live only in the group's checkout and drivers. Check `git log` before relying on them.
- **Field parameters:** pulse types other than `delta` (Gaussian, CW, Hann); their argument names are not documented in the README.
- **Damping argument:** the units and meaning of the `abs_spec` damping argument (assumed τ in au, as in the paper).
- **Missing paper details:** the ethylene time step and part of the paper's middle section (about 25 kB was not read). The XAS molecule is named inconsistently (CO vs CO2) in the paper text.
- **Ehrenfest restarts:** the README says the chkfile stores only the time and MO coefficients; the group's checkout also writes and restores positions, velocities and forces (K19, K23). Which version introduced this is unverified.
- **Missing source types:** no Matter Modeling SE or PySCF forum threads on RT-TDDFT turned up in the searches. K9, K14 and K15 rely on search summaries rather than full reads.
- **Timing:** the time per run for the benzene benchmark on PACE CPU nodes has not been measured.
