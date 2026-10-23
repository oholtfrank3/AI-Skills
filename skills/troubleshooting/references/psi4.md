# Psi4 (1.9+): troubleshooting reference

Last researched: 2026-10-22

**How to use this file:** find your symptom in "Known issues and fixes", check the cause against your output file, apply the fix, and run a starter calculation on the same machine before trusting production. This is documented practice from the manual and forum, not group experience. The short version lives in `skills/psi4/SKILL.md`. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official documentation

**Manual.** <https://psicode.org/psi4manual/master/> (the "master" pages are a development build, 1.12a1.dev at time of reading). Versioned copies exist, e.g. `.../psi4manual/1.11.x/`. Check `psi4 --version` and read the matching manual when an option seems missing.

**Install (conda).** <https://psicode.org/psi4manual/master/build_obtaining.html>; current instructions at <https://psicode.org/installs/latest>.
- Since v1.8 the binaries live on **conda-forge**, not the old `psi4` channel. Release build, in a fresh environment:
  `conda create -n p4env psi4 -c conda-forge/label/libint_dev -c conda-forge`
- Binaries exist for Linux, Mac (Intel and Apple Silicon) and Windows/WSL. Threaded BLAS and OpenMP come with the binaries.
- Always `conda create` a new env rather than `conda install` into an old one (Known issues #9, #10).

**Two ways to run.** <https://psicode.org/psi4manual/master/psiapi.html>, <https://psicode.org/psi4manual/master/psithoninput.html>
- **Psithon:** an input file (`molecule {...}`, `set ...`, `energy(...)`) run as `psi4 -i input.dat -o output.dat -n 8`.
- **PsiAPI:** plain Python, `import psi4`, `psi4.geometry("""...""")`, `psi4.set_options({...})`, `psi4.set_memory('8 GB')`, `psi4.set_num_threads(8)`, `psi4.set_output_file('out.dat', False)`, `psi4.energy(...)`.
- Commands run in order: a `set` placed after `energy()` does not affect it. `set ccenergy print 3` scopes an option to one module.
- Results: `E = energy(...)`; `E, wfn = energy(..., return_wfn=True)`; `variable('MP2 TOTAL ENERGY')`; `print_variables()`. Variables are cleared at the start of each new `energy()`/`optimize()` call.

**Memory, threads, scratch.** <https://psicode.org/psi4manual/master/external.html>
- **Memory:** `memory 8 GB` (psithon) or `psi4.set_memory('8 GB')`. Default is only 500 MiB. It is the **total** for the job, not per thread. Real usage is slightly higher than the setting, so request more from Slurm than you give Psi4.
- **Threads:** `psi4 -n N` for psithon; `psi4.set_num_threads(N)` for PsiAPI (the `-n` flag does not exist there). Per the manual, `OMP_NUM_THREADS`/`MKL_NUM_THREADS` no longer control Psi4 threading (since 1.1). Psi4 is **single-node only** (OpenMP + threaded BLAS, no MPI).
- **Scratch:** `export PSI_SCRATCH=/local/disk` before running. Default `/tmp` is often too small, and network drives are slow. In an input: `psi4_io.set_default_path('/path')`. `psi4 -m` keeps scratch files. Avoid `~/.psi4rc` (manual discourages it; PsiAPI ignores it).

**Methods and drivers (manual pages).**
- **SCF/DFT:** <https://psicode.org/psi4manual/master/scf.html>, <https://psicode.org/psi4manual/master/dft.html>. `scf_type df` is the default for HF/DFT energies. `reference rhf|uhf|rohf|cuhf`. DFT via `energy('b3lyp-d3bj')`, `energy('wb97x-d')` etc.
- **Optimize / frequencies:** `optimize('scf')`, `frequency('scf')` (alias `frequencies`). Optimizer is optking; `optimize(..., engine='geometric')` uses geomeTRIC.
- **CC:** `energy('ccsd(t)')` (ccenergy; also DF/CD variants via fnocc/dfocc), EOM-CC in cceom (`energy('eom-ccsd')` with `roots_per_irrep`).
- **DLPNO-CCSD(T):** <https://psicode.org/psi4manual/master/dlpnocc.html>. `energy('dlpno-ccsd(t)')`, closed-shell RHF only, C1 only. `pno_convergence loose|normal|tight|very_tight`; the page recommends `tight` for non-covalent work. Rough limit on a 32 GB desktop: ~80–100 atoms with a polarized DZ basis. First release containing it: not checked (unverified, appears in 1.11.x docs).
- **SAPT:** <https://psicode.org/psi4manual/master/sapt.html>. `sapt0` (prints sSAPT0 too), `ssapt0`, `sapt2`, `sapt2+`, `sapt2+(3)`, `sapt2+3`, plus `(ccd)`, `dmp2`, `-ct` variants; `sapt(dft)`; `fisapt0` / F-SAPT for intramolecular and functional-group partitions; SAPT0-D (`sapt0-d3mbj`). Two fragments separated by `--`. Recommended basis for SAPT0 is **jun-cc-pVDZ**; the manual advises against aug-cc-pVTZ with SAPT0. Only SAPT0 supports open-shell monomers (UHF/ROHF). Closed-shell SAPT always uses density fitting.
- **Counterpoise / n-body:** <https://psicode.org/psi4manual/master/nbody.html>. `energy('ccsd(t)', bsse_type='cp')`; `bsse_type` can be `cp`, `nocp`, `vmfc` or a list (first one is returned). Default return is the **interaction energy**; `return_total_data=True` gives totals. Variables `CP-CORRECTED INTERACTION ENERGY`, `NOCP-CORRECTED INTERACTION ENERGY`. Since v1.10 the n-body code lives in the QCManyBody package (may need a separate install in some envs).
- **CBS:** <https://psicode.org/psi4manual/master/cbs.html>. `energy('mp2/cc-pv[tq]z')`; `energy('mp2/cc-pv[tq]z + D:ccsd(t)/cc-pvdz')`; or `energy('cbs', corl_wfn='mp2', corl_basis='aug-cc-pv[tq]z', delta_wfn='ccsd(t)', delta_basis='aug-cc-pv[dt]z')`. Defaults: SCF `scf_xtpl_helgaker_3` (3 bases) or `_2` (2 bases); correlation `corl_xtpl_helgaker_2`. Zeta levels must be consecutive. `set basis` has no effect inside `cbs()`.
- **Dispersion add-ons:** <https://psicode.org/psi4manual/master/dftd3.html>. `-d3`/`-d3bj` need **s-dftd3** (Python module, conda `simple-dftd3`/`dftd3-python`); `-d4` needs `dftd4`/`dftd4-python`; gCP needs `gcp-correction`. Classic `dftd3` is not used from v1.10. Check with `qcengine info`.
- **Wavefunction files:** `psi4.fchk(wfn, 'out.fchk')` (1.4+), `psi4.molden(wfn, 'out.molden')`, `wfn.to_file('wfn.npy')`. For MP2/CCSD, `energy()` leaves the HF density in `wfn`; use a gradient call if you need the correlated density.
- **Other interfaces:** QCSchema/QCEngine (`qcengine` runs Psi4 as a backend), MDI for coupling to MD drivers (unverified details).

---

## Starter calculations

**1. Water SCF and optimization + frequencies (PsiAPI tutorial).** <https://psicode.org/psi4manual/master/psiapi.html>
- **Input:** Z-matrix `O / H 1 0.96 / H 1 0.96 2 104.5`, `basis cc-pvdz`, `energy('scf')`; then `optimize('scf')` and `frequency('scf')`.
- **Expected:** E(SCF) = −76.0266327349 Eh (DF). Optimized E = −76.0270327294 Eh in 3 steps. Frequencies 1775.65, 4113.38, 4212.18 cm⁻¹ (±0.1 roundoff).
- **Resources:** 1 core, 500 MB, seconds.
- **Common mistake:** comparing a DF number with a `scf_type pk` number; they differ in the ~1e-6 Eh range. Also forgetting `set reference uhf` for open-shell systems.

**2. Water CCSD/6-31G** optimization (test `cc1`).** <https://github.com/psi4/psi4/blob/master/tests/cc1/input.dat>
- **Input:** `O / H 1 0.97 / H 1 0.97 2 103.0`, `set basis 6-31G**`, `optimize('ccsd')` (all-electron).
- **Expected:** E(SCF) = −76.0229427 Eh, CCSD correlation = −0.2082357 Eh, total = −76.2311784 Eh.
- **Resources:** 1–2 cores, < 1 GB, about a minute.
- **Common mistake:** setting `freeze_core true` and then comparing to an all-electron reference.

**3. SAPT0 ethene···ethyne (tutorial §IV and test `sapt1`).**
- **Tutorial (jun-cc-pVDZ, DF, freeze_core):** total SAPT0 = −0.0022356 Eh (≈ −1.40 kcal/mol); Elst10,r ≈ −2.12 and Disp20 ≈ −1.21 kcal/mol. <https://psicode.org/psi4manual/master/psiapi.html>
- **Test `sapt1` (cc-pVDZ, `df_basis_elst cc-pvdz-ri`, `d_convergence 11`):** Elst −0.00359915, Exch +0.00362911, Ind −0.00083137, Disp −0.00150542, total −0.00230683 Eh. <https://github.com/psi4/psi4/blob/master/tests/sapt1/input.dat>
- **Resources:** 1–4 cores, 1–2 GB, under a minute.
- **Common mistake:** expecting the two to agree; they use different basis sets and fitting bases. Match the basis and `df_basis_elst` before comparing (the `df_basis_elst` default changed to JKFIT in v1.6).

**4. Counterpoise-corrected Ne₂ CCSD(T)/aug-cc-pVDZ (tutorial §V).** <https://psicode.org/psi4manual/master/psiapi.html>
- **Input:** `Ne / -- / Ne 1 R`, `set basis aug-cc-pvdz`, `set freeze_core true`, `energy('ccsd(t)', bsse_type='cp')`, scan R.
- **Expected (kcal/mol):** +0.7586 at 2.5 Å, +0.0160 at 3.0 Å, −0.0162 at 4.0 Å.
- **Resources:** 1–4 cores, ~1 GB, minutes for the scan.
- **Common mistake:** reading the returned number as a total energy (it is the interaction energy in Eh) or forgetting the `--` separator, so no fragments are defined.

**Larger checks (published).** SAPT2+3/aug-cc-pVDZ water dimer from the SAPT manual page: SAPT0 total −5.387 kcal/mol, SAPT2+3 total −4.506 kcal/mol (Elst −8.198, Exch +8.420, Ind −2.456, Disp −2.272). Use the geometry printed on that page.

---

## Known issues and fixes

1. **SCF "Iterations did not converge" on a difficult dimer.** Cause: oscillating SCF. Fix, in order: `damping_percentage 20` (raise to 30–40), `basis_guess true`, `soscf true` with larger `soscf_max_iter`. Put these in `set scf {...}` or globally, **not** in a `set sapt` block, and give `damping_percentage` as a float. <https://forum.psicode.org/t/iterations-do-not-converge/984> (2018-07).
2. **SCF still fails after raising `maxiter`.** Cause: often a broken geometry (misplaced H), or stagnation, not too few iterations. Fix: check the Cartesian geometry first; use `set scf maxiter 200` only after damping/SOSCF; `stability_analysis follow` (UHF only) for wrong solutions. <https://forum.psicode.org/t/about-calculations-that-do-not-converge/1804>, <https://forum.psicode.org/t/how-can-i-change-max-iteration-in-energy-method/1238> (read via search summaries only; unverified detail). SCF aids: <https://psicode.org/psi4manual/master/scf.html>.
3. **"Fatal Error: PSIO Error".** Cause: scratch disk full, usually because `PSI_SCRATCH` was unset and Psi4 wrote to a small `/tmp`. Fix: set `PSI_SCRATCH` to a large local disk; check `df -h` on that path during the run. <https://forum.psicode.org/t/scratch-is-full/430> (2017-03), <https://psicode.org/psi4manual/master/external.html>.
4. **PSIO error or crazy energies in SAPT with Z-matrix input.** Cause: Z-matrix geometry with fragments behaved badly; switching to Cartesians fixed it. The manual also warns Z-matrices can give wrong SAPT answers for symmetric systems. Fix: always give SAPT dimers in Cartesians, with `symmetry c1`, `no_reorient`, `no_com`. <https://forum.psicode.org/t/sapt-psio-error-scratch-to-blame/1609> (2019-11).
5. **Open-shell SAPT: "This is a RHF SAPT constructor".** Cause: only SAPT0 is open-shell, and the input must set an open-shell reference and per-fragment charge/multiplicity. Fix: `reference rohf` (or uhf), charge/mult on each fragment, `energy('sapt0')`. Higher SAPT levels and SAPT(DFT) are closed-shell only. <https://forum.psicode.org/t/open-shell-sapt0-computation/437> (2017-03), SAPT manual.
6. **Job OOM-killed by Slurm.** Cause: Slurm memory limit equal to (or below) Psi4's `memory`; Psi4 uses slightly more than its setting. Also a user thought they had set 16 GB but the script said 1000 MB. Fix: give Psi4 ~85–95 % of the Slurm allocation; print the memory line in the output header and check it. <https://forum.psicode.org/t/process-killed-when-running-calculation-on-molecule-with-148-atoms-using-wb97m-d3bj-def2-tzvppd/3073> (2024-05).
7. **More threads made it slower / threads ignored.** Cause: oversubscription (more threads than allocated cores), or using `set_num_threads` in psithon. Psi4's speed comes from threaded BLAS; maintainers say >16 threads is rarely worth it. Fix: psithon `psi4 -n $SLURM_CPUS_PER_TASK`; PsiAPI `psi4.set_num_threads(...)`; never more than allocated cores. <https://forum.psicode.org/t/confusion-about-threading/1293> (2019-03), #6 above.
8. **Two Slurm nodes requested, job uses one.** Cause: Psi4 has no inter-node parallelism and no MPI; `mpirun` does nothing useful. Fix: request one node (`--nodes=1`); for many small jobs, run several `psi4 -n k` processes inside one allocation. <https://forum.psicode.org/t/need-help-running-psi4-on-multiple-nodes-with-slurm-and-openmpi/3160> (2024-09), #7.
9. **`import psi4` fails: "BaseSettings has been moved to pydantic-settings".** Cause: installing from the old `psi4` channel pulled mismatched dependencies. Fix: install from conda-forge in a fresh env. <https://forum.psicode.org/t/dependency-error-when-installing-psi4-in-a-fresh-conda-environment/3041> (2024-04).
10. **`PackagesNotFoundError: psi4` or unsolvable env.** Cause: old conda (classic solver), or `conda install` into an existing env. Fix: update conda (libmamba solver) and `conda create -n p4env psi4 -c conda-forge`. Same thread as #9 (2024-05).
11. **"requires libint 2.7.3dev1.*, which does not exist".** Cause: dev build needs the libint dev label. Fix: `conda create -n p4env psi4/label/dev::psi4 -c conda-forge/label/libint_dev -c conda-forge`. <https://forum.psicode.org/t/where-is-psi4-dev-located/3193> (2024-10).
12. **"Program s-dftd3 is registered with QCEngine, but cannot be found" (`-d3bj` fails).** Cause: Psi4 needs the s-dftd3 **Python module** importable, not only the executable. Fix: install `dftd3-python`/`simple-dftd3` from conda-forge into the same env (or a matching wheel); confirm with `qcengine info`. A stale `dftd3` earlier on `PATH` can also break it. <https://forum.psicode.org/t/s-dftd3-for-psi4/2785> (2023-05), <https://psicode.org/psi4manual/master/dftd3.html>.
13. **Classic `-d3` names rejected in v1.10+ (UpgradeHelper error).** (unverified: from search snippets) Cause: classic DFTD3 removed. Fix: use the replacement syntax the error message prints. <https://psicode.org/psi4manual/master/dftd3.html>.
14. **Second `optimize()` in a loop starts at iteration N+1 and fails.** Cause: optking state left over after hitting `geom_maxiter` (suspected bug). Fix: `optimize(..., engine='geometric')`, or the standalone optking package; one optimization per process. <https://forum.psicode.org/t/psi4-optimize-do-not-finished-properly-when-the-calculation-is-ended-by-geom-maxiter/2500> (2022-06).
15. **Optimization of ion pairs or floppy complexes never converges.** No confirmed fix on the forum. Try a better starting geometry, `engine='geometric'`, and check that the SCF converges at every step. <https://forum.psicode.org/t/convergence-error-caught-could-not-converge-geometry-optimization-in-500-iterations/2687> (title read via search only; unverified).
16. **Large DFT optimization drops to one thread.** Open, unanswered (2026-06). If seen, check the output's thread line and the module running (some steps are not threaded). <https://forum.psicode.org/t/large-molecule-dropping-to-single-threaded-processing/3510>.
17. **SAPT numbers shift slightly versus an old paper.** Cause: documented default changes (frozen core pre-2011; `NAT_ORBS` true since 2016; E(30)ind term added 2020; dMP2 frozen-core 2021; `df_basis_elst` JKFIT since v1.6; SAPT(DFT) exch-disp scaling 2022). Fix: match version and these options before comparing. SAPT manual page.
18. **CP returns a small number, not a total energy.** By design: `bsse_type` returns the interaction energy in Eh. Use `return_total_data=True` or read `CP-CORRECTED TOTAL ENERGY`. nbody manual page.
19. **Correlated density missing from fchk/molden.** (unverified: from search snippets) Cause: `energy('mp2')`/`energy('ccsd')` do not build the correlated density. Fix: use `gradient(...)` (or `properties`) before writing. fchk manual, <https://psicode.org/psi4manual/1.4.0/fchk.html>.

---

## Open questions / could not verify

- First Psi4 release that ships DLPNO-CCSD(T) (seen in 1.11.x docs).
- Whether QCManyBody must be installed separately with the current conda-forge psi4 (manual box is ambiguous).
- Exact pydantic/QCElemental versions that work with 1.9.x; only "v1 or v2 both work" per a maintainer.
- Tested Slurm script on PACE: none yet. Psi4 timings on PACE nodes are unknown.
- No published S22 CP value reproduced here; the S22 reference data in Psi4's database (`database('...', 'S22')`) was not checked.
- MDI/pymdi coupling details not read.
