# PySCF 2.x (general use): troubleshooting reference

Last researched: 2026-10-22

**How to use this file:** find your symptom under "Known issues and fixes", check the cause against your output, apply the fix, and run a starter calculation before you trust a production run. The everyday rules are in `skills/pyscf/SKILL.md`. EOM-CC in PySCF is covered in `qchem-pyscf-eomcc-cap.md` and `skills/eom-cc/SKILL.md`, and is not repeated here. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

**Versions:** the latest tagged release is **v2.14.0** (`pyscf/__init__.py` on master, 2026-10-22). Check yours with `python -c "import pyscf; print(pyscf.__version__)"`. Defaults and APIs change between releases, so always quote the version.

---

## Official documentation

**User guide index:** <https://pyscf.org/user.html>. **Examples:** <https://github.com/pyscf/pyscf/tree/master/examples> (`scf/`, `dft/`, `mcscf/`, `geomopt/`, `hessian/`, ...). The examples are the best documentation: most pages point to them.

**Molecule (`gto.M` / `gto.Mole`):**
- **Charge and spin:** `charge` is the net charge. `spin` is **2S = N_alpha − N_beta** (number of unpaired electrons), not the multiplicity. Triplet O2 is `spin=2`, a doublet cation is `spin=1`. The SCF guide's Cr example uses `spin=6` for a septet.
- **Units:** coordinates are Ångström by default (`unit='Bohr'` to change). Energies are in Hartree.
- **Ghost atoms:** `ghost-O` or `X-O` labels carry basis functions without nucleus or electrons (counterpoise; `examples/geomopt/11-with_ghost_atom.py`).
- **Command-line parsing:** building a `Mole` parses `sys.argv` by default (see issue #470 below).

**SCF guide:** <https://pyscf.org/user/scf.html>
- **Classes:** `scf.RHF/UHF/ROHF/GHF` and `dft.RKS/UKS/ROKS/GKS` (or `mol.RHF()`, `mol.KS(xc=...)`). ROHF gives an S² eigenfunction; UHF can be spin-contaminated; GHF for broken-symmetry or spin–orbit cases.
- **Initial guess (`mf.init_guess`):** `'minao'` (default), `'atom'`, `'huckel'`, `'vsap'` (DFT only), `'1e'` (last resort), `'chk'`. Or pass a density matrix: `mf.kernel(dm0)`.
- **Convergence tools:** DIIS by default (`mf.diis_space`, `mf.diis_start_cycle`; `mf.DIIS = scf.ADIIS` or `scf.EDIIS`, see `examples/scf/24-tune_diis.py`), damping (`mf.damp`), level shift (`mf.level_shift`; `examples/scf/03-level_shift.py`, and `scf.addons.dynamic_level_shift_` in `52-...`), fractional occupation (`54-...`), and the second-order solver `mf.newton()` (CIAH; `22-newton.py`, `12-fast_newton.py`).
- **Stability:** `mo1, _, stable, _ = mf.stability(return_status=True)`; `external=True` adds RHF→UHF and UHF→GHF checks. Restart from `mf.make_rdm1(mo1, mf.mo_occ)` until stable (`examples/scf/17-stability.py`, which ships a loop for this).
- **Breaking spin symmetry (UHF/UKS):** `mf.init_guess_breaksym = 'mix'` rotates the alpha and beta HOMO/LUMO by ±45° (`examples/scf/32-break_spin_symm.py`); or edit the alpha/beta guess densities by hand.
- **ΔSCF / MOM:** `scf.addons.mom_occ(mf, mo0, occ)` holds a chosen occupation (`examples/scf/50-mom-deltaSCF.py`).
- **Restarts:** set `mf.chkfile = 'name.chk'`. Restart with `mf.init_guess = 'chk'`, or `dm = scf.hf.from_chk(mol, 'name.chk')`, which also projects onto a new basis or geometry (`14-restart.py`). If you do not set `chkfile`, a temporary one in the scratch dir is deleted after a successful run.
- **Linear dependence:** `scf.addons.remove_linear_dep_(mf)` for large diffuse bases (`42-remove_linear_dep.py`).
- **Density fitting:** `mf.density_fit()` (optionally `auxbasis=`); `examples/scf/20-density_fitting.py`.

**DFT:** `xc` strings follow libxc names (`'b3lyp'`, `'pbe0'`, `'wb97x-v'`, `'camb3lyp'`). The default `xc` is `'LDA,VWN'`, so always set it. Grids: `mf.grids.level` (0–9, default 3; Treutler–Ahlrichs radial, Becke partition, NWChem pruning; `examples/dft/11-grid_scheme.py`). Since v2.3 `b3lyp` uses the VWN-RPA form, as in Gaussian (issue #1480).

**Dispersion:** `pip install pyscf-dispersion`, then put the correction in the xc string: `mol.KS(xc='b3lyp-d3bj')`, `'wb97x-d4'`, `'b3lyp-d4'` (`examples/dft/16-dft_d3.py`). This sets `mf.disp`, `xc` and `nlc` together. Some names are blacklisted (e.g. `wb97x-d3`, `wb97x-d`) and raise an error (see #3399).

**Memory, threads and scratch (`pyscf/lib/parameters.py`, `lib/misc.py` on master):**
- **`max_memory`** defaults to **4000 MB** for every object. Change it per object (`mf.max_memory = 50000`), with the environment variable `PYSCF_MAX_MEMORY`, or `MAX_MEMORY` in `~/.pyscf_conf.py`. It is a soft target: some steps exceed it.
- **Scratch:** `TMPDIR` from the environment, overridden by `PYSCF_TMPDIR`. Point it at node-local disk.
- **Threads:** OpenMP and BLAS read `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS` **once, when the library loads**. Changing `os.environ` after `import pyscf` does nothing. Use `lib.num_threads(n)` inside Python, or export the variables before Python starts.
- **Config file:** `.pyscf_conf.py` in `$HOME` or the working directory, or the path in `PYSCF_CONFIG_FILE` (<https://pyscf.org/user/using.html>).

**Geometry optimization:** `from pyscf.geomopt.geometric_solver import optimize; mol_eq = optimize(mf)` or `mf.Gradients().optimizer(solver='geomeTRIC').kernel()`. Needs `pip install geometric` (PyBerny: `pip install pyberny`, `solver='berny'`). Convergence keys (`convergence_energy`, `convergence_grms`, `convergence_gmax`, `convergence_drms`, `convergence_dmax`) are passed as keyword arguments (`examples/geomopt/01-geomeTRIC.py`). Excited states, CASSCF, CCSD(T) and solvent examples are in the same folder.

**Frequencies and thermochemistry:** `h = mf.Hessian().kernel()`; `from pyscf.hessian import thermo`; `freq = thermo.harmonic_analysis(mol, h)`; `thermo.thermo(mf, freq['freq_au'], 298.15, 101325)` returns ZPE, H, G and more. The master example also shows quasi-RRHO options (`qrrho=True`); check that your version has them (`examples/hessian/10-thermochemistry.py`).

**MCSCF guide:** <https://pyscf.org/user/mcscf.html>
- **Set up:** `mcscf.CASSCF(mf, ncas, nelecas)`; `nelecas` can be a tuple `(nalpha, nbeta)` for open shells. CASCI: `mcscf.CASCI`. UHF-based: `mcscf.UCASSCF` (`60-uhf_based_ucasscf.py`).
- **Choosing orbitals:** by default the active space is the orbitals around the Fermi level. `mc.sort_mo([...])` takes **1-based** indices (`base=0` to change). `mcscf.sort_mo_by_irrep` picks per irrep. MP2 or UHF natural orbitals (`mcscf.addons.make_natural_orbitals`) are a good start. AVAS: `ncas, nelecas, orbs = avas.avas(mf, ['Fe 3d', 'C 2pz'])` (`43-avas.py`); also `dmet_cas` and APC (`80-apc.py`).
- **Frozen orbitals:** `mc.frozen = n` or a 0-based list. Not the same as the FCI solver's `frozen`.
- **Spin:** `mc.fix_spin_(ss=...)` is an energy penalty against spin contamination in the CI solver.
- **State averaging:** `mc.state_average_([0.5, 0.5])`. The printed `e_tot` is the average; run a CASCI with the final orbitals for individual energies (`15-state_average.py`). Mixed spin/symmetry: `mcscf.state_average_mix_` (`41-state_average.py`).
- **Reusing orbitals:** `mcscf.project_init_guess(mc, mo_old[, mol_old])` maps orbitals from another geometry or basis (`14-project_init_guess.py`).

**Correlated methods:** `mp.MP2(mf)`, `cc.CCSD(mf, frozen=n)`, `mycc.ccsd_t()`. Restarts and EOM: see `qchem-pyscf-eomcc-cap.md`.

**TDDFT/TDA:** `td = mf.TDA().run(nstates=5)` or `mf.TDDFT()`; `td.e` in Hartree; `td.oscillator_strength()`; `td.analyze()`. TDDFT with a hybrid on a UKS reference works; use TDA when TDDFT gives instabilities.

**Properties and output:** `mf.dip_moment()` (Debye), `mf.mulliken_pop()`, `mf.analyze()` (Meta-Löwdin populations by default), `lo.PipekMezey/Boys/ER` localisation, `tools.molden.from_scf(mf, 'x.molden')`, `tools.cubegen.orbital/density`. NMR, EPR, polarizabilities and the older `prop.freq` live in the **pyscf-properties** extension.

**Extensions:** <https://pyscf.org/user/extensions.html>. `pip install pyscf[name]` or `pip install pyscf-<name>` for: `dispersion`, `properties`, `semiempirical`, `dmrgscf`, `shciscf`, `qsdopt` and others. New methods land in **pyscf-forge** (`pip install pyscf-forge`). Extensions are not on conda; with conda, set `PYSCF_EXT_PATH`. The PySCF team does not support extensions; issues go to each extension's repository.

**GPU:** **gpu4pyscf** (<https://github.com/pyscf/gpu4pyscf>): `pip install gpu4pyscf-cuda12x` (+ `cutensor-cu12`), Volta (V100) or newer. Move an object with `.to_gpu()`, e.g. `mol.RKS(xc='b3lyp').density_fit().to_gpu()`. Covers mainly SCF/DFT energies, gradients and Hessians; check its feature list before planning.

**PBC (brief):** `pyscf.pbc` (`pbc.gto.Cell`, `pbc.scf.KRHF`, k-points). Separate examples in `examples/pbc/`. Not covered in this file.

---

## Starter calculations

Values computed locally on 2026-10-22 with PySCF 2.9.0 (macOS, 1 thread), default `conv_tol`. They should agree to ~1e-6 Eh with any 2.x version on any machine. Geometries in Å.

**1. Water RHF and correlation, cc-pVDZ** — `O 0 0 0; H 0 -0.757 0.587; H 0 0.757 0.587` (the geometry in most PySCF examples).
- **Expected:** RHF −76.026766 Eh; with `.density_fit()` −76.026745 (DF error ~2e-5 Eh); MP2 corr −0.204020; CCSD corr −0.213343; (T) −0.003060; dipole 2.06 D.
- **B3LYP (VWN-RPA, grid level 3):** −76.420378 Eh. `xc='b3lyp5'` (VWN5 form) gives −76.383224, 0.037 Eh higher. If you get that number, check for `B3LYP_WITH_VWN5` in a config file.
- **Most common mistake:** comparing with another code that used VWN5 B3LYP, Cartesian d functions, or a different geometry.

**2. Water B3LYP geometry optimization (geomeTRIC)**
- **Input:** `optimize(dft.RKS(mol, xc='b3lyp'))` from the geometry above, then `thermo.harmonic_analysis` on `mf.Hessian().kernel()` at the new geometry.
- **Expected:** converges in a few steps to r(OH) ≈ 0.97 Å and HOH ≈ 103° with cc-pVDZ, and three real frequencies (unverified; not run here because geomeTRIC was not installed locally).
- **Most common mistake:** running frequencies at the starting geometry (gives imaginary modes, issue #1310), or forgetting `pip install geometric` (issue #1849).

**3. N2 CASSCF(6,6)/cc-pVDZ at R = 1.098 Å, with `symmetry=True`**
- **Expected:** RHF −108.954087 Eh; CASSCF(6,6) −109.090054 Eh (default orbital selection: the three bonding and three antibonding 2p orbitals).
- **For a curve:** scan R and feed each point the previous point's orbitals with `mcscf.project_init_guess`. Watch that the active orbitals stay the same 2p set at long R.
- **Most common mistake:** an active space that silently changes between points (energy jumps on the curve).

**4. O2 triplet UHF/ROHF with a stability check, cc-pVDZ, R = 1.2075 Å, `spin=2`**
- **Expected:** UHF −149.627758 Eh, ⟨S²⟩ = 2.033 (exact 2.000), stable to internal rotations; ROHF −149.608084 Eh.
- **Check:** `mf.stability(return_status=True)` should report stable. The singlet guess (`spin=0`) gives a higher, wrong state.
- **Most common mistake:** setting `spin=3` thinking "triplet" (fails: "Electron number 16 and spin 3 are not consistent").

---

## Group lessons (from local notes)

Read-only notes in `/Users/owenhf/Documents/pace_snapshot_2026-10-04` (path below is relative to it). Only lessons useful beyond the Ar/water project are kept.

- **Pipek–Mezey over a whole valence block mixes s and p.** In fcc Ar it returned sp hybrids, so no orbital was "the 3s". Split the canonical orbitals into s-like and p-like blocks by summed Mulliken s vs p weight (not an energy cutoff), then localise each block separately. (`writing_materials/ar_h2o/WRITEUP_STATUS.md:96-101`)
- **Localisation is ill-conditioned for symmetric, degenerate clusters** (triangle, tetrahedron). Use energies only, not per-site labels, there. (`CALCULATIONS_LIST_with_values.md:131`)
- **Assign sites one-to-one and check every site appears once.** An `argmax` over atoms let two holes claim the same Ar, so one site vanished from the results. (`writing_materials/agent_messages/HANDOFF_energetics.md:37`)
- **ΔSCF only reaches the lowest state of each spin/occupation.** A UHF Ar⁺ 3s hole collapsed to 3p. Hold holes with MOM (`scf.addons.mom_occ`) and check the spin density; for higher states use EOM. (`CALCULATIONS_LIST_with_values.md:209-211, 317`)
- **"99 % localised" Mulliken spin can hide real delocalisation.** A ΔCCSD hole that read 99 % localised had still relaxed part-way to the band edge. (`CALCULATIONS_LIST_with_values.md:672`)
- **(T) has no checkpoint and can run out of memory after a day.** Five UCCSD(T) jobs died OUT_OF_MEMORY in (T) after 23–39 h. Save CCSD amplitudes, size memory for (T) before submitting, and use out-of-core settings for large UCCSD. (`writing_materials/agent_messages/HANDOFF_energetics.md:28`; `SUMMARY.md:191`)
- **Put the basis in checkpoint file names, or use one directory per job.** aDZ and aTZ checkpoints with the same name overwrote each other. (`HANDOFF_energetics.md:31`)
- **UCCSD stopped at the default 50 cycles.** The energy error was only ~0.3 meV, but say so in the methods, or raise `max_cycle`. (`HANDOFF_energetics.md:29`)
- **Never hide failures.** A script forced `converged = ones`, and chunked Davidson restarts swapped roots. Check every convergence flag. (`HANDOFF_energetics.md:43`; details in `eom-cc` §2)
- **Cation ROHF that will not converge:** seed `newton()` from the neutral density; and check which hole a UHF cation landed in (`eom-cc` §2).
- **BLAS threads set inside the script came too late** (TiDES example): export them in the job script (`tides` §7).
- **Use a wavefunction reference for hole dynamics.** Frozen-nuclei TD-CASCI (CAS(37,19)/cc-pVDZ) showed oscillation where RT-TDDFT showed trapping. (`CALCULATIONS_LIST_with_values.md:873-882`; `tides` §3)

---

## Known issues and fixes

### SCF convergence and wrong states

- **SOSCF (`newton()`) converged, but stability analysis says unstable.** *Cause:* second-order SCF finds a stationary point, not necessarily a minimum. *Fix:* always run `mf.stability()` after `newton()` and follow the unstable direction. [pyscf #2421, 2024-09-16](https://github.com/pyscf/pyscf/issues/2421)
- **Same open-shell input gives two different converged answers from run to run (Ce³⁺, ECP).** *Cause:* multithreaded sums are not bit-reproducible, and degenerate open-shell atoms can break symmetry either way. *Fix:* `OMP_NUM_THREADS=1` for reproducibility tests; compare energies and run stability analysis; pick the lowest stable state. Even 1 thread does not guarantee the same symmetry breaking (maintainer). [pyscf #2832, 2025-05-31](https://github.com/pyscf/pyscf/issues/2832); see also [#201, 2018-07-02](https://github.com/pyscf/pyscf/issues/201)
- **MO coefficients differ between runs with several threads, energy the same.** *Cause:* degenerate orbitals can mix arbitrarily; threads add rounding noise. *Fix:* compare densities or energies, not raw orbital coefficients of degenerate sets. [pyscf #2323, 2024-07-15](https://github.com/pyscf/pyscf/issues/2323)
- **Stability analysis crashes after `dynamic_level_shift_` (ROKS cation).** *Cause:* the level-shift wrapper interfered with `stability()`. The issue is closed; the fix was not read here. *Fix:* update PySCF, or rebuild a plain SCF object from the converged orbitals before calling `stability()` (unverified workaround). [pyscf #3063, 2025-12-03](https://github.com/pyscf/pyscf/issues/3063)
- **GHF fails to converge for a closed-shell molecule where RHF converges.** *Cause:* the default GHF guess from RHF deliberately breaks spin symmetry (`breaksym=True`). *Fix:* start GHF from converged RHF/UHF orbitals; the default change is still under discussion (open). [pyscf #3057, 2025-11-21](https://github.com/pyscf/pyscf/issues/3057)
- **HF convergence on Apple-silicon Macs differs from Linux for H4/STO-3G.** *Cause:* unclear (BLAS build suspected); open. *Fix:* do production runs on PACE Linux; treat odd Mac-only behaviour with suspicion. [pyscf #1561, 2023-01-05](https://github.com/pyscf/pyscf/issues/1561)
- **ROKS H atom does not give −0.5 Eh / HOMO −0.5 Eh.** *Cause:* a finite basis, plus B3LYP self-interaction; ROKS also has several definitions. *Fix:* expect DFT orbital energies not to equal IPs; use UHF for one-electron checks. [Matter Modeling SE #12543, 2024-03-09](https://mattermodeling.stackexchange.com/questions/12543/why-is-my-hydrogen-energy-not-equal-to-0-5-hartrees)

### DFT functionals, grids and dispersion

- **B3LYP energies differ from older PySCF or from Turbomole/GAMESS (water/cc-pVDZ: 0.037 Eh).** *Cause:* since v2.3, `b3lyp` uses VWN-RPA (Gaussian convention), after issue #1480. *Fix:* compare like with like; `xc='b3lyp5'`, or `B3LYP_WITH_VWN5 = True` in `.pyscf_conf.py`, gives the VWN5 form. [pyscf #1480, 2022-10-21](https://github.com/pyscf/pyscf/issues/1480)
- **`b97_3c` runs silently with no dispersion; `b97-3c` raises an error.** *Cause:* the dispersion guard matches the exact xc spelling. *Fix:* use documented spellings, and check `mf.disp` and the printed dispersion energy. Open. [pyscf #3399, 2026-08-14](https://github.com/pyscf/pyscf/issues/3399)
- **DFT analytic Hessian not translationally invariant; spurious imaginary modes.** *Cause:* the grid-response term was never implemented on CPU (`grid_response` was ignored). *Fix:* use a finer grid (`grids.level` 5+) for frequencies, project out translations/rotations, or use gpu4pyscf, which has the term. A related error estimate was added in PR #3502. [pyscf #3437, 2026-09-07](https://github.com/pyscf/pyscf/issues/3437)
- **Negative frequencies from the example water input.** *Cause:* the geometry was not optimised at that level. *Fix:* optimise first with the same functional, basis and grid. [pyscf #1310, 2022-07-01](https://github.com/pyscf/pyscf/issues/1310)
- **Open-shell geometry optimisation with D3/D4 via `dftd3.pyscf` failed.** *Cause:* a bug in the simple-dftd3/dftd4 PySCF wrappers. *Fix:* update them, or use the `pyscf-dispersion` route (`xc='b3lyp-d3bj'`). [pyscf #1986, 2023-12-03](https://github.com/pyscf/pyscf/issues/1986)

### Performance, threads and memory

- **Wrong DFT gradients with MKL at some `OMP_NUM_THREADS` values.** *Cause:* conflicting threading libraries (MKL's own threads vs PySCF's libgomp). *Fix:* `ldd pyscf/lib/libnp_helper.so` should show only libgomp and libpthread; install everything from one source (conda-forge or a clean pip env). [pyscf #2606, 2025-01-13](https://github.com/pyscf/pyscf/issues/2606)
- **First SCF inside geomeTRIC fails only with 16 threads.** *Cause:* conflicting OpenMP runtimes from pip wheels, causing silent numerical corruption. *Fix:* same as above; maintainers suggest conda-forge or a source build. [pyscf #2448, 2024-10-08](https://github.com/pyscf/pyscf/issues/2448)
- **Setting `max_memory` breaks a script that has its own command-line options (or pytest).** *Cause:* `Mole` parses `sys.argv`. *Fix:* `mol.build(parse_arg=False)` (open since 2019). [pyscf #470, 2019-12-18](https://github.com/pyscf/pyscf/issues/470)
- **EOM ignored `max_memory`; wrong IPs at low memory in big bases:** see `qchem-pyscf-eomcc-cap.md` (#3000, #629).

### Geometry optimisation

- **`ImportError` when calling the geomeTRIC optimiser.** *Cause:* geomeTRIC is a separate package. *Fix:* `pip install geometric` (or `pyberny`). [pyscf #1849, 2023-09-04](https://github.com/pyscf/pyscf/issues/1849)
- **TS optimisation: numerical Hessian steps counted as optimisation steps; error passing `hessian`.** Fixed in the geomeTRIC interface update (PR #2855, 2025). *Fix:* use PySCF ≥ 2.10 (unverified exact version) for TS searches. [pyscf #2811](https://github.com/pyscf/pyscf/issues/2811), [#2812, 2025-05-18](https://github.com/pyscf/pyscf/issues/2812)

### CASSCF

- **CASSCF stalls (no step, never converges) for high-spin Mn (6o,7e).** *Cause:* one active orbital is fully occupied, so rotations with inactive orbitals are redundant; the wavefunction is effectively single-determinant. *Fix:* choose an active space where every orbital has fractional occupation (check natural occupations ~0.02–1.98). [pyscf #2493, 2024-10-30](https://github.com/pyscf/pyscf/issues/2493)
- **CASSCF energy jumps up mid-optimisation (DMRG solver).** *Cause:* suspected solver restart from a stale wavefunction; open. *Fix:* save orbitals each iteration (`callback`), restart from the last good set, and compare with a smaller exact-CI active space. [pyscf #683, 2020-08-19](https://github.com/pyscf/pyscf/issues/683)
- **Wrong orbitals in the active space after `sort_mo`.** *Cause:* indices are 1-based by default. *Fix:* pass `base=0` for 0-based lists; print the chosen orbitals' character before running (MCSCF guide).

---

## Open questions / could not verify

- Starter 2 geometry and frequencies were not run (geomeTRIC not installed locally).
- Exact release that contains the geomeTRIC TS fix (#2855) and the level-shift/stability fix (#3063).
- Whether `thermo.thermo(..., qrrho=True)` is in v2.14.0 or only on master.
- A Matter Modeling SE search found no threads on SCF convergence in PySCF specifically; the forum list above is GitHub-heavy.
- The best memory settings for large UCCSD(T) in PySCF (out-of-core options, `max_memory` vs node RAM) were not researched; the group's fix is recorded only as "out-of-core UCCSD".
