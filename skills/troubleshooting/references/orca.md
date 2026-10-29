# ORCA (6.x): troubleshooting reference

Last researched: 2026-10-28

**How to use this file:** find your symptom in "Known issues and fixes", check the cause against your output file, apply the fix, and run a starter calculation on the same machine before trusting production. This is documented practice from the ORCA manual, the official tutorials and HPC-centre guides, not group experience. The short version lives in `skills/orca/SKILL.md`. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official documentation

**Version.** Latest release found: **ORCA 6.1.1** (2 Dec 2025, a bug-fix release of 6.1.0, which came out 17 Jun 2025). The forum front page and the 6.1 change log list nothing newer (checked 2026-10-28). The developers aim for roughly one release a year, so check for a newer one. Read the manual matching `orca` output's header.

**Manual.** <https://www.faccts.de/docs/orca/6.1/manual/> (also mirrored at <https://orca-manual.mpi-muelheim.mpg.de/>, labelled 6.1.1). ORCA 6.0 manual: <https://www.faccts.de/docs/orca/6.0/manual/>. Detailed change log: <https://www.faccts.de/docs/orca/6.1/manual/contents/appendix/detailedchangelog.html>.

**Tutorials.** <https://www.faccts.de/docs/orca/6.1/tutorials/> (first steps, parallel runs, memory, common install issues, single points, optimizations, frequencies, UV/Vis).

**Forum.** <https://orcaforum.kofo.mpg.de/> (official; registration needed for downloads). Its threads were not reachable by web search or its own search page from here, so no forum thread is cited below. Search it by hand with the exact error text.

**Unofficial but useful.** ORCA Input Library (R. Bjornsson): <https://sites.google.com/site/orcainputlibrary/> (setting up ORCA, Slurm script, SCF convergence; written for 6.0; the page says the official docs win when they disagree).

**Licence and install.** <https://www.faccts.de/orca/>, <https://www.faccts.de/docs/orca/6.1/manual/contents/quickstartguide/installation.html>
- Free for academic and personal use; commercial licences through FACCTs. Academic installers come from the forum (registration required).
- Linux/macOS installer is a `.run` file, e.g. `orca_6_1_0_linux_x86-64_shared_openmpi416.run`. The installer adds ORCA to `PATH`.
- Parallel runs need OpenMPI. Tutorial: the recommended version for ORCA 6 is 4.1.6; install the version named on the download page. OpenMPI can be built in your home directory.
- Set `PATH` and `LD_LIBRARY_PATH` for both ORCA and OpenMPI (ORCA is dynamically linked).
- PACE: no ORCA module is known (unverified). Check `module avail orca`; otherwise install the academic binary in home or project space after an OK.

**Input structure.** <https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/input.html>
- `!` simple keyword lines; `%block ... end`; geometry between `* xyz charge mult` and `*`, or `* xyzfile charge mult file.xyz` (no closing `*`), or a `%coords` block. Comments start with `#`.
- Case-insensitive, except file names. Single-value settings such as `%maxcore 3000` take no `end`.
- AutoStart reads an existing `basename.gbw` as the guess. `! NoAutoStart` turns it off.

**Memory.** Same page, §2.1.3; tutorial <https://www.faccts.de/docs/orca/6.1/tutorials/first_steps/memory.html>
- `%maxcore` = MB **per process** for the main work arrays. Default 4096 MB in 6.1 (raised to 4 GB in 6.1.0); the manual suggests at least 8 GB for coupled-cluster methods.
- ORCA can use more than `%maxcore`. Manual troubleshooting: keep `maxcore × nprocs` ≤ 0.75 × available memory (the input page says 75–80 %, the tutorial about 80 %).
- If the estimate is between 1× and 2× `%maxcore`, ORCA warns and continues; above 2× it aborts.

**Parallel runs.** <https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/parallel.html>, tutorial <https://www.faccts.de/docs/orca/6.1/tutorials/first_steps/parallel.html>
- `%pal nprocs N end`, or `! PALn` for n = 2–8, 16, 32, 64 only (`PAL12` is rejected).
- Call ORCA with its **full path**; never start the driver with `mpirun`. Extra MPI options go in quotes after the input name, e.g. `"--bind-to none"`.
- Use local, non-NFS scratch, fresh for each run.
- Suggested process counts: RI-DFT up to about 16; hybrid DFT and HF somewhat more; coupled cluster scales to at least 8, try 16.

**Slurm practice (HPC-centre guides).** LRZ <https://doku.lrz.de/spaces/UniARZHPCKB/pages/392035529/ORCA> (ORCA 6), TalTech <https://docs.hpc.taltech.ee/chemistry/orca.html> (ORCA 5.0.4), ORCA Input Library Slurm script.
- `--ntasks` must equal `nprocs` (LRZ: "absolutely crucial"); `--cpus-per-task` > 1 gives no speed-up because ORCA is MPI-only.
- Do not launch ORCA with `srun` (LRZ: job failure).
- Copy inputs to node-local scratch, run there by full path, copy back `.gbw`, `.engrad`, `.xyz`, `.hess` and the output.
- With group parallelism, `nprocs_group` must divide `--ntasks` and `--ntasks-per-node` (LRZ).

**RI / RIJCOSX.** <https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/RI.html>
- RIJCOSX is the default for hybrid DFT since ORCA 5 (`! NoCOSX` turns it off); HF does not use it by default. Default fitting basis `def2/J`. RIJDX (RI-J) is the default for non-hybrid functionals.
- Correlated RI methods need a `/C` basis (`def2-TZVP/C`, `cc-pVTZ/C`) or `! AutoAux`.
- COSX grid trouble (erratic SCF, "megahartree" jumps, Cholesky failure of the numerical overlap): increase the grid.

**Dispersion.** <https://www.faccts.de/docs/orca/6.1/manual/contents/modelchemistries/dispersioncorrections.html>
- `! D4` (generally recommended), `! D3BJ` (preferred over `! D3ZERO`). VV10 functionals (e.g. ωB97M-V) must not get an extra D3/D4.

**Geometry optimizations and frequencies.** Tutorials <https://www.faccts.de/docs/orca/6.1/tutorials/prop/geoopt.html>, <https://www.faccts.de/docs/orca/6.1/tutorials/prop/freq.html>
- `OPT`, `OPT FREQ`, `TightOpt`, `VeryTightOpt`, `NumGrad` (methods without gradients), `NumFreq` (6N displacements, restart with `%freq restart true end` and the `.hess` file).
- Default criteria printed: TolE 5e-6 Eh, TolMAXG 3e-4, TolRMSG 1e-4 Eh/bohr, TolMAXD 4e-3, TolRMSD 2e-3 bohr, MaxIter 50.
- Converged only when the output prints `HURRAY`.

**DLPNO-CCSD(T).** MDCI chapter <https://www.faccts.de/docs/orca/6.1/manual/contents/modelchemistries/mdci.html>
- `! DLPNO-CCSD(T) cc-pVTZ cc-pVTZ/C` (semi-canonical triples, "T0"); `! DLPNO-CCSD(T1)` (iterative triples; better when the HOMO–LUMO gap is small).
- `LoosePNO` (rapid estimates), `NormalPNO` (default, general thermochemistry), `TightPNO` (weak interactions, conformational equilibria).
- A fitting basis is required. Frozen core is the default for coupled cluster.
- Open shell: UHF/ROHF/UKS reference, QROs are used, about 2× the cost. Not meant for spin-polarized (broken-symmetry) cases.
- Check the T1 diagnostic (tutorial rule of thumb: above 0.02, do not trust the result).

**Excited states.**
- TDDFT: <https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/tddft.html>. `%tddft nroots N end` (same as `%cis`); TDA on by default, `TDA false` for full TDDFT; `triplets true`; `IRoot` for gradients; RIJCOSX carries over from the SCF.
- EOM-CCSD: <https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/eom.html>. `! EOM-CCSD` (= EE), `! IP-EOM-CCSD`, `! EA-EOM-CCSD`; `%mdci nroots` (default 9). UHF supported for EE/IP/EA (`DoAlpha`/`DoBeta` for IP/EA), but no UHF transition moments. Exact transition moments need `DoLeft true` and `DoTDM true`. Large jobs: `KCOpt KC_AOBLAS`, `DoCOSXEOM true`, `DoAOX3e true`.
- STEOM-CCSD: <https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/steom.html>. Active space chosen automatically from CIS natural orbitals (`OThresh`/`VThresh` 0.001). Roots with "Percentage Active Character" above 98 count as converged. `DoTriplet true` for triplets (RHF).
- bt-PNO-EOM/STEOM: <https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/dleom.html>. With TightPNO, within 0.01 eV of canonical EOM-CCSD. RHF, UHF (QROs) and ROHF. For RHF set `DLPNOLINEAR true` and `NEWDOMAINS true` in `%mdci`. Keyword `bt-PNO-STEOM-CCSD` per the 6.0 manual (read via search summary; full input line unverified).
- DLPNO-STEOM-CCSD: <https://www.faccts.de/docs/orca/6.1/manual/contents/spectroscopyproperties/dlpno-steom.html>. `! STEOM-DLPNO-CCSD def2-TZVP AutoAux TightSCF` (TightSCF required, TightPNO recommended). Closed shell only. Roots converged at ≥ 96 % active character. 6.1 change log: DLPNO IP-EOM/STEOM runs on one core only; canonical and bt-PNO versions run on several.

**SCF convergence.** <https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/scf.html>
- AutoTRAH is on by default (switches to TRAH when convergence struggles; RHF/RKS/UHF/UKS). Other tools: `SlowConv`, `VerySlowConv`, `KDIIS`, SOSCF, damping, level shift, `SmearTemp`. Converge a cheaper calculation first and read its orbitals.
- Post-HF and excited-state runs stop on an unconverged SCF by default (`ConvForced`); properties and numerical derivatives are never computed on unconverged orbitals. 6.1.0 also stops when MDCI equations do not converge.

---

## Starter calculations

All from the ORCA 6.1 tutorial "Single point energies" (<https://www.faccts.de/docs/orca/6.1/tutorials/prop/single_point.html>). The page does not say which exact ORCA version printed the numbers. Geometry (Å):

```
O  -3.56626  1.77639  0.00000
H  -2.59626  1.77639  0.00000
H  -3.88959  1.36040 -0.81444
```

**1. Water HF/def2-SVP.**
- **Input:** `! HF DEF2-SVP`, `* xyz 0 1`.
- **Expected:** FINAL SINGLE POINT ENERGY −75.959334985643 Eh.
- **Resources:** 1 core, seconds.
- **Common mistake:** a different geometry (the "Hello water" tutorial uses another one) or a different ORCA version's defaults; differences in the 1e-6 range are not a broken install.

**2. Water B3LYP/def2-SVP.**
- **Input:** `! B3LYP DEF2-SVP` (RIJCOSX on by default).
- **Expected:** −76.320253532344 Eh.
- **Common mistake:** comparing with another program, or with an ORCA 5 number (integration grids changed in ORCA 6; TS §1.7.10).

**3. Water DLPNO-CCSD(T)/cc-pVTZ** (also `examples/orca/water_dlpno_ccsdt.inp`).
- **Input:** `! DLPNO-CCSD(T) cc-pVTZ cc-pVTZ/C` (NormalPNO default).
- **Expected:** E(0) −76.055469392, E(CORR)(corrected) −0.268039017, E(TOT) −76.323508409, T1 diagnostic 0.006597252, FINAL SINGLE POINT ENERGY −76.330949256808 Eh. The gap of 0.0074 Eh between E(TOT) and the final energy is presumably the (T) triples term, printed after E(TOT) (unverified; the tutorial does not say).
- **Resources:** 1–4 cores, about 1 GB per core, under a minute (unverified).
- **Common mistake:** adding `TightPNO` or `TightSCF` and then comparing with these numbers; leaving out the `/C` basis ("needs an AuxC basis").

**Larger checks.** Acetic acid B3LYP-D4/def2-SVP frequencies (frequency tutorial): C=O stretch 1869.95 cm⁻¹, C–H stretch 3126.68 cm⁻¹; the tutorial's first run also shows an imaginary −83.22 cm⁻¹ methyl rotation from a not fully converged optimization, a good example of what to fix.

---

## Known issues and fixes

Sources are the ORCA 6.1 manual's troubleshooting chapter (<https://www.faccts.de/docs/orca/6.1/manual/contents/quickstartguide/troubleshooting.html>, "TS" below), the tutorials and HPC-centre guides. Dates are the date read (2026-10-28) unless the source has its own.

1. **"ERROR (ORCA_MAIN): For parallel runs ORCA has to be called with full pathname".** Cause: parallel job started as plain `orca`. Fix: `$ORCADIR/orca job.inp > job.out`. TS §1.7.1.
2. **"FATAL ERROR ENCOUNTERED" / "I/O OPERATION FAILED", maybe with an mpirun/prterun message.** Cause: the driver was started with `mpirun` (or `srun`). Fix: run the driver serially by full path; set `%pal nprocs`. TS §1.7.1; LRZ guide (srun → job failure).
3. **"UNRECOGNIZED OR DUPLICATED KEYWORD(S) IN SIMPLE INPUT LINE" with `PAL12` etc.** Cause: `PALn` exists only for 2–8, 16, 32, 64. Fix: `%pal nprocs 12 end`. TS §1.7.4.
4. **Parallel modules die at start: missing `libmpi.so.*`, "mpirun: command not found", or ORCA quits at the first parallel step.** Cause: OpenMPI not on `PATH`/`LD_LIBRARY_PATH` inside the job, or a different OpenMPI than ORCA was built with. Fix: load/build the matching version (4.1.6 for ORCA 6 per the tutorial), export both variables in the job script, print `which mpirun` before the run. ORCA Input Library "Setting up ORCA"; older mailing-list cases (ORCA 4.x) via search summaries only (unverified).
5. **Open MPI "There are not enough slots available".** Cause: `nprocs` larger than the Slurm `--ntasks`. Fix: `--ntasks` = `nprocs`, `--cpus-per-task=1`; do not paper over it with `--oversubscribe`. LRZ guide; general Open MPI/Slurm reports (search summaries; no ORCA forum thread found).
6. **Job slow, only a few cores busy.** Cause: `-c N` with one task; ORCA does not thread. Fix: `--ntasks=N -c 1`. LRZ guide.
7. **"Please increase MaxCore" or "OUT OF MEMORY ERROR!" (possibly a segfault from mpirun).** Cause: `%maxcore` too small for the step. Fix: raise `%maxcore` (MB per process), keeping `maxcore × nprocs` ≤ 0.75 × memory; use fewer processes if needed. TS §1.7.5.
8. **Job killed with no ORCA error; Slurm says out of memory or time limit.** Cause: `%maxcore` read as total memory, or no headroom (ORCA exceeds `%maxcore`). Fix: lower `%maxcore` or raise `--mem-per-cpu`; check `sacct` MaxRSS. TS §1.7.3; TalTech guide (cgroup OOM message).
9. **"Error TMatrixContainers::AddMatrix - Failed to add ..." or "Failed to set FilePointer".** Cause: disk full; can also fail silently. Fix: run in node-local scratch with enough space (`--tmp`, `pace-slurm` §3). TS §1.7.6.
10. **"ERROR: RI-MP2 needs an AuxC basis but none was defined!" / "Aux/C requested but not available in SHARK".** Cause: correlated RI or DLPNO method without a `/C` basis. Fix: add `cc-pVTZ/C`, `def2-TZVP/C`, or `AutoAux` (AutoAux can bring linear dependence). TS §1.7.4.
11. **"Error: RI is on but the HF exchange must be handled somehow".** Fix: add `RIJCOSX`, `RIJDX` or `RIJK`. TS §1.7.4.
12. **"WARNING! Potentially linear dependencies in the auxiliary basis" / "Diagonalization failed with error code: -5".** Cause: diffuse basis or `AutoAux`. Fix: check the small overlap eigenvalues in the output; see the manual's linear-dependence section. TS §1.7.7.
13. **"Input geometry does not match current geometry" or "No orbitals were found in the gbw file".** Cause: AutoStart reading an old `.gbw` with the same base name; or `MORead` pointing at the job's own `.gbw`. Fix: clean directory or `! NoAutoStart`; copy the old `.gbw` to a new name for `MORead`. TS §1.7.12; tutorial "Solving common issues" (old files break new runs).
14. **"Your GBWFile is either corrupt or from a different ORCA version!".** Fix: `! Rescue MORead` (with `NoIter` to regenerate a file for plotting). TS §1.7.11.
15. **"ERROR: expect a '$', '!', '%', '*' or '[' in the input".** Cause: `end` after `%maxcore`/`%moinp`, missing `!`/`*`, comment without `#`. TS §1.7.4. Related: "non-ASCII character(s) found" (6.0.1+) from pasted curly quotes or dashes.
16. **SCF does not converge / TRAH starts.** Fix order: check geometry, charge, multiplicity; `SlowConv` (transition metals); converge a GGA/small-basis run first and read its orbitals; damping, level shift, `KDIIS`, SOSCF; `SmearTemp` as a last resort. `SlowConv` may land in a local minimum near the guess. TS §1.7.13; SCF chapter.
17. **Optimization never prints HURRAY, or imaginary modes after OPT FREQ.** Fix: restart from the last `.xyz` with more cycles; `TightOpt`, finer grid (`DefGrid3`), tighter SCF; displace along the imaginary mode and reoptimize; `COPT` for Cartesian steps. TS §1.7.14; geometry and frequency tutorials.
18. **Energies differ from ORCA 5 or another code.** Cause: ORCA 6 changed integration grids and defaults; ORCA uses pure d/f functions. Fix: match settings before calling it a disagreement. TS §1.7.10.
19. **STEOM roots flagged "the state may have not converged with respect to active space".** Cause: active character below 98 % (96 % for DLPNO-STEOM). Fix: ask for more roots; for DLPNO-STEOM tighten `TCutPNOSingles` (1e-12 or 5e-12). STEOM and DLPNO-STEOM manual pages.
20. **Large T1 diagnostic in DLPNO-CCSD(T).** Above 0.02 the single-reference result is doubtful (tutorial); check with `%mdci DoSDiagnostic true end` and consider a multireference method. TS §1.7.15.

---

## Open questions / could not verify

- ORCA forum threads: not reachable from here (search engines do not index them, the forum search returned no results). Known issues above come from the manual, tutorials and HPC-centre guides instead.
- Whether PACE has an ORCA module; how PACE's job-submit routing treats `--ntasks` + `--mem-per-cpu`; a tested sbatch on PACE.
- Exact OpenMPI version for 6.1.1 (the 6.1.0 installer name says 4.1.6).
- The full `bt-PNO-STEOM-CCSD` simple-input line and whether it needs `/C` and `TightPNO` explicitly.
- Which ORCA version produced the tutorial reference energies, and what the E(TOT)/final-energy gap in Starter 3 is.
- Runtimes for the starter calculations on PACE: expected values to be recorded on first run.
