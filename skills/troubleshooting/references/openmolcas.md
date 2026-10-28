# OpenMolcas (RASSCF / MCLR / SLAPAF / MRCI): troubleshooting reference

Last researched: 2026-10-23

**How to use this file:** find your symptom in "Known issues and fixes", check the cause against your log (search for `Stop Module:` first), apply the fix, and rerun a small test before trusting production. SHARC-with-OpenMolcas lessons live in `skills/sharc/SKILL.md` §10 and `skills/sharc/references/sa-casscf-openmolcas.md`. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

Most entries come from one group project (Ar clusters with a water, one-hole SA-CASSCF, Sep–Oct 2026, a 26.x development build of OpenMolcas). Line numbers in source files refer to that build and may move. Items marked (unverified) were seen once and not double-checked.

---

## Official documentation

- **Manual (Sphinx):** <https://molcas.gitlab.io/OpenMolcas/sphinx/>. Module pages sit under `users.guide/programs/`, e.g. MCLR: <https://molcas.gitlab.io/OpenMolcas/sphinx/users.guide/programs/mclr.html>.
- **Issue tracker:** <https://gitlab.com/Molcas/OpenMolcas/-/issues>. Search with the exact error text in quotes.
- **Forum:** <https://molcasforum.univie.ac.at> (current). The old MOLCAS message board (<https://www.molcas.org/molcas/wwwboard/>) still has useful threads, e.g. the one unanswered MCLR "Increase Iter." report (messages/1497.html).
- **Source:** the answer to "is this a limit or a bug?" was usually in the source (`src/rasscf/`, `src/molcas_ci_util/`, `Tools/pymolcas/`). Grep it before guessing.

**Version and build check:** `pymolcas --banner` prints the version and whether `Parallel` and OpenMP are on; `ldd` on a module binary shows which BLAS it links.

---

## Known issues and fixes

### Input and keywords

1. **More than 16 `Alter` pairs fails with `Fortran runtime error: End of record`.** Cause: `MAXALTER = 16` is a compile-time constant (`src/molcas_ci_util/rasscf_global.F90`); the friendly "too many orbital pairs" message is never reached. Fix: raise `MAXALTER` in the source and rebuild into a new prefix (see #22), or reduce the pairs. Source: group experience, 2026-09-07 (19-site active space).
2. **`ITERATIONS` above 200 is silently clamped.** The log says `Reset to maximum, new MAXIT= 200` (`mxIter = 200` in `rasdim.F90`). The keyword is `ITERATIONS=N,M`; `ITER` is not recognized for this and is silently ignored (it is echoed in the input, with no effect). Fix: check the log for "Reset to maximum"; if 200 macro-iterations do not converge, fix the guess or the active space instead. Source: group experience, 2026-09-15.
3. **A `>>> DOWHILE` loop stops after 50 iterations.** Cause: the pymolcas driver caps loops at `MOLCAS_MAXITER` (default 50, `Tools/pymolcas/abstract_flow.py`), independent of SLAPAF's own `ITERations`. It prints the same "Convergence problem" banner as a real failure. Fix: `export MOLCAS_MAXITER=300` before `pymolcas`. Source: group experience, 2026-09-10.
4. **Atom labels longer than 4 characters break the input** (`-->ARHU<-- is not a proper string to define an element` for `ARHUB`). Fix: use short labels such as `AR1`–`AR10`. Source: group experience, 2026-09-16.
5. **`Data not defined: FMM` (`_RC_INTERNAL_ERROR_`)** from `&SCF`/`&RASSCF`. Cause: no `&SEWARD` run before them in that input. Fix: add `&SEWARD`. Source: group experience, 2026-09-16.
6. **`&SCF` orbital-file keyword is `FILE`, not `FILEORB`.** `FILEorb` belongs to `&LOCALISATION`. Check the manual page of the module you are writing for. Source: group experience, 2026-09-15.
7. **GUGA (MRCI chain) fails with zero active orbitals.** Fix: put one orbital (e.g. the 3s) in the active space. Ghost-atom syntax for counterpoise was also wrong at first in the same work; check it against the manual (unverified which form failed). Source: group experience, 2026-10-02/05.

### Orbitals and active spaces

8. **The active orbitals you want are not contiguous.** `Inactive`/`RAS2` take orbitals by position. Fix: keep `Inactive` set by the electron count and swap the wanted orbitals into place with `Alter` (`n`, then `sym orb_from orb_to` per pair). Identify the swap targets by AO composition, never by index or energy rank. Source: group experience, early Sep 2026 (Ar4 chain).
9. **SA-CASSCF orbital optimization pulls the active space onto the wrong orbitals** (e.g. Ar 3s → O 2p / Ar 3p mixtures). `Alter` only fixes the starting guess; Super-CI is free to rotate afterwards. Fix: `SUPS` (supersymmetry) groups forbid rotations between groups while still optimizing. Use **one orbital per group**: one shared group let active orbitals swap among themselves. `SUPS` is an orbital-rotation restriction, not point-group symmetry. Source: group experience, 2026-09-08 to 09-15.
10. **`SUPS` labels land on the wrong orbitals.** In an `&RASSCF` call that also has `Alter`, `SUPS` takes the **pre-Alter** indices (the code swaps the labels with the orbitals). In a later call with `Lumorb` and no `Alter`, use the **post-Alter** (final) indices. Fix: check the "Supersymmetry vector for symmetry species" printout in every call, and diff it between the first and a later DOWHILE iteration. Also watch for "Supersymmetry may have failed... check orbital order". Source: group experience, 2026-09-08 and 09-24.
11. **Orbital indices change between runs with identical input.** Canonical SCF orbitals among near-degenerate valence orbitals did not come out in a reproducible order across separate runs. Fix: identify orbitals by composition inside each job, not from a separate probe run. Source: group experience, 2026-09-09.
12. **Clean single-atom orbitals:** neutral RHF followed by `&LOCALISATION` (Pipek–Mezey) gave clean single-atom Ar 3s orbitals. Localize only the occupied valence window you need, then select by ownership *and* orbital energy (a core orbital is 100 % on its atom). Source: group experience, 2026-09-28/29.
13. **Map SA-CASSCF roots to sites by per-root natural occupations**, not by root order. Source: group experience, 2026-09 (unverified as a general rule).
14. **Over 256 orbitals, the orbital printout has no AO coefficient rows.** `PriMO` switches to a compact format above 256 basis functions, with no warning, so composition scripts return nothing. Fix: in `&SCF` or `&RASSCF` add `PRLS` / `3` and `PROR` / `2 100.0 3` (the final 3 forces the long format). Check for real AO rows before trusting a parser. Source: group experience, 2026-09-09.

### Convergence

15. **"Convergence problem": find which module stopped.** RASSCF and MCLR print the same banner. Read the `--- Stop Module: <name> ... /rc=... ---` line. Several "MCLR failures" were really RASSCF failures. Source: group experience, 2026-09-14.
16. **MCLR `No convergence for perturbation no: 1. Increase Iter.` (rc = 96).** The message is misleading: 1000 PCG iterations failed the same way. Read the PCG trace: if `Res(kappa)` grows (here ~30×, "perturbation might diverge"), the solve is diverging. Cause found: active orbitals at occupation exactly 2.0, here core orbitals that had slipped into the active space; OpenMolcas also warns "Elements in the E^[2] matrix small". Fix: clean the active space (no core or doubly occupied orbitals). With a clean space MCLR converged and the analytic gradient matched finite differences to 0.1–0.9 %. Source: group experience, 2026-09-25 to 09-29.
17. **`MCLR module cannot handle frozen orbitals!`** Cause: `FROZEN` in `&RASSCF` with analytic gradients. Fix: drop `FROZEN`, or use numerical gradients (`&ALASKA` `NUMErical`). Source: group experience, 2026-09-14.
18. **Analytic gradient with `CIONLY` is wrong (~25 % off finite differences).** The response terms assume optimized orbitals. Fix: `&ALASKA` `NUMErical`, or full RASSCF. Source: group experience, 2026-09-06.
19. **RASSCF would not converge for a one-hole active space at an unrelaxed geometry.** What worked: `LevShft` ≥ 1.0 *and* a relaxed geometry together; neither alone was enough. Source: group experience, 2026-09-14 (one system).
20. **SLAPAF oscillates on weakly bound (vdW) clusters.** What helped: `Cartesian` with `MAXStep = 0.1`. Before blaming the optimizer, check #3. CASSCF has no dispersion, so vdW geometries need an added correction (e.g. D3) or experimental distances. Source: group experience, 2026-09-09/11.

### Files, scratch and the driver

21. **A copied orbital file is ignored and a fresh guess is used** (`INPORB -> <project>.GssOrb` in the log). Also, `>>COPY <relative path> INPORB` fails with "Source ... is neither a file nor a directory" because relative paths resolve against WorkDir, not the submit directory. Fix: absolute paths in `>>COPY`, and check the `INPORB ->` line. Source: group experience, 2026-09-09.
22. **`Lumorb` with a `.UhfOrb` file: `IUHF does not match`.** RASSCF wants a restricted-format orbital file. Fix: convert first or start from a restricted file. Source: group experience, 2026-09-09.
23. **`Stale file handle` on `TEMP01`/`TEMP02`.** Cause: two jobs with `MOLCAS_WORKDIR=PWD` sharing one directory. Fix: one directory (and WorkDir) per job. A reused directory also fed a stale `INPORB` that collapsed a cation to the wrong hole; use fresh directories and an explicit `>>COPY $Project.ScfOrb INPORB`. Source: group experience, 2026-09-11 and 2026-10-04.
24. **pymolcas runs the wrong tree when started inside a source checkout.** It looks for `.molcashome` in the current directory and its parents. Fix: `pymolcas --not-here`. `configure-cmake` needs `.molcashome` in the source root (`touch .molcashome` in a clone). Source: group experience, 2026-09-04 and 09-13.
25. **SEWARD prints `2.0 GB of memory, 1 thread`, then `rc=-9`.** The job ran on the login node, not under Slurm. Fix: submit it. Source: group experience, 2026-09-14.
26. **Scratch fills up with `.OrdInt` files** (two-electron integrals; 950 GB in one archive). SEWARD rewrites them every run, so they can be deleted after a run finishes (ask first). Source: group experience, 2026-09-29.

### Build and performance

27. **The stock build may be serial with no optimized BLAS** (`Parallel: OFF`, no OpenMP, internal linear algebra). `-nt 8` then does nothing. Rebuilding with MKL ILP64 (`configure-cmake --compiler gnu --opt normal --omp --mkl $MKLROOT`) gave ~3.3× on RASSCF+MCLR+ALASKA, all from MKL; threads added nothing for small systems. Source: group experience, 2026-09-13.
28. **Never rebuild into a live install prefix.** Running jobs load modules from it. Build into a new prefix and switch paths. A reused build script nearly overwrote the production install. Source: group experience, 2026-09-15.

### Multireference correlation (MRCI)

29. **Counterpoise from separate monomer MRCI runs is not size-consistent** (+0.9 to +1.7 eV "interaction" at 15 Å). Fix: reference the curve to the same dimer at large R, and use monomer runs only for the R-dependent BSSE. Source: group experience, 2026-10-04.
30. **Flag MRCI points with a large +Q spread or a low reference weight.** Neutral-RHF orbitals with full-valence references gave a 3s reference weight of 0.78 and a 3.3 eV +Q correction, and couplings 2–3× too large. Working thresholds: +Q spread > 1 mHa between comparable states, or reference weight < 0.4 (unverified; set your own). Source: group experience, 2026-10-04.

---

## Group lessons

- **Search the log, not your memory of the input:** "Reset to maximum", "Supersymmetry vector", `INPORB ->`, `Stop Module:` and the PCG trace each exposed a silent problem.
- **Check orbital character at every step that can change it** (seed, after RASSCF, after a restart). A plausible energy spread can still be the wrong hole; compare the absolute energy with a clean reference.
- **Many limits are compile-time constants or driver defaults** (`MAXALTER`, `mxIter`, `MOLCAS_MAXITER`, the 256-orbital print switch). When a fix "does nothing", look for a hidden cap first.
- **Before launching dynamics on SA-CASSCF, compare step-0 site energies with EOM-IP-CCSD** at the same geometry (`skills/sharc/SKILL.md` §10).
