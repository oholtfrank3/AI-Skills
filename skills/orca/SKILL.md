---
name: orca
description: Setting up and running ORCA 6.x (free for academics) - academic download and OpenMPI install, input anatomy (! keyword line, %blocks, * xyz charge mult), %maxcore and %pal on Slurm (--ntasks, full path to orca, node-local scratch), DFT with RIJCOSX and D3BJ/D4, geometry optimizations and frequencies, DLPNO-CCSD(T) with TightPNO and /C auxiliary basis sets, TDDFT, EOM-CCSD (EE/IP/EA), STEOM-CCSD and bt-PNO / DLPNO-STEOM excited states, and common ORCA errors. Use whenever someone wants to use ORCA, writes or debugs an ORCA input or output, or asks for DLPNO-CCSD(T) or STEOM on a large molecule.
---

# ORCA in practice (documented practice)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

**This is general, documented practice, not group experience.** No ORCA runs are recorded in the group's notes, so everything here comes from the ORCA 6.1 manual, the official ORCA tutorials and HPC-centre guides. Sources, reference numbers and the known-issues list are in the `troubleshooting` skill, `references/orca.md`. Check that file before guessing at a fix. For choosing a functional or basis in general, see `basics`; for which method fits a question, `method-selection`.

## 1. When ORCA is the right tool

- **Use ORCA for:** DLPNO-CCSD(T) energies of molecules too big for canonical CCSD(T) (reaction, conformer and interaction energies); fast hybrid DFT with RIJCOSX; excited states of medium and large molecules with STEOM-CCSD, bt-PNO-STEOM-CCSD or DLPNO-STEOM-CCSD; TDDFT; a wide set of spectroscopy properties.
- **Prefer Q-Chem** for EOM-CC with CAPs, DIP states and the group's established excited-state workflows (`eom-cc`). **Prefer Psi4** for SAPT and automatic counterpoise (`psi4`), **PySCF** for custom Python methods and TiDES, **CP2K** for periodic systems. If unsure, use `method-selection`.
- ORCA has EE-, IP- and EA-EOM-CCSD, but not the DIP/CAP machinery the group uses in Q-Chem.

## 2. Getting ORCA and running it on PACE

- **Licence and download:** free for academic use. Register on the ORCA forum (orcaforum.kofo.mpg.de), accept the licence there, and download the Linux x86-64 installer. Current version at the time of writing: **6.1.1** (Dec 2025). Write the version into every log.
- **On PACE:** check `module avail orca` first. If there is no module, install the academic binary in your home or project space (ask before installing anything, `pace-slurm` §0). Nobody in the group has done this yet.
- **OpenMPI must match** the version ORCA was built with (the 6.1 Linux installer name ends in `openmpi416`, and the tutorials name OpenMPI 4.1.6 for ORCA 6). Load or build that version, then put both the OpenMPI and the ORCA folders on `PATH` and `LD_LIBRARY_PATH` in the job script.
- **Call ORCA by its full path** for parallel runs (`$ORCADIR/orca job.inp > job.out`). Never start it with `mpirun` or `srun`: ORCA launches its own MPI processes.
- **Cores:** `%pal nprocs N end` in the input (`! PAL4` works only for PAL2–8, 16, 32, 64). ORCA uses MPI processes, so ask Slurm for `--ntasks=N --cpus-per-task=1` with the same N. Extra `-c` cores sit idle.
- **Memory:** `%maxcore` is **MB per process**, not the total. Keep `maxcore × nprocs` at about 75 % of the memory Slurm gives you, because ORCA goes above `%maxcore`. Example: 8 processes with `--mem-per-cpu=4G` pairs with `%maxcore 3000`. How PACE routes `--ntasks` jobs to partitions is not checked (unverified): run `sbatch --test-only` (`pace-slurm` §2).
- **Scratch:** ORCA writes its temporary files in the working directory. Copy the input to node-local `$TMPDIR`, run there, and copy the outputs you need (`.out`, `.gbw`, `.xyz`, `.hess`, `.engrad`) back at the end. One directory per job. Node-local scratch details are in `pace-slurm` §3. Run `scripts/check_sbatch.py`, propose the script and wait for an OK. A template is in `examples/orca/`.

## 3. Input anatomy

```
! B3LYP D4 def2-TZVP TightSCF        # simple keywords
%pal nprocs 8 end
%maxcore 3000                         # no "end" after %maxcore
* xyz 0 1                             # charge, multiplicity; Ångström
O  0.000  0.000  0.063
...
*
```

- `!` lines: method, basis, job type (`OPT`, `FREQ`), convergence presets. Case does not matter; file names do.
- `%name ... end` blocks hold detailed options (`%scf`, `%geom`, `%tddft`, `%mdci`).
- Geometry from a file: `* xyzfile 0 1 start.xyz` (no closing `*`).
- Old files with the same base name are read automatically (AutoStart). Use a clean directory per job, or `! NoAutoStart`.

## 4. Core recipes

- **DFT:** hybrids use RIJCOSX by default (`def2/J` fitting basis is picked automatically). Add dispersion: `D4` (manual's recommendation) or `D3BJ`. Do not add D3/D4 to VV10 functionals such as ωB97M-V.
- **Optimize + frequencies:** `! B3LYP D4 def2-SVP OPT FREQ`. Look for the `HURRAY` line, then check for imaginary modes. Small imaginary modes: `TightOpt`, a finer grid (`DefGrid3`), or displace along the mode and reoptimize.
- **DLPNO-CCSD(T):** `! DLPNO-CCSD(T) cc-pVTZ cc-pVTZ/C TightPNO TightSCF`. Always give the matching `/C` auxiliary basis (or `AutoAux`). `NormalPNO` is the default (general thermochemistry); `TightPNO` for weak interactions and conformers. `DLPNO-CCSD(T1)` (iterative triples) is more accurate when the HOMO–LUMO gap is small. Check the T1 diagnostic (above 0.02 is a warning sign). Open shell: UHF reference; it costs about twice as much.
- **TDDFT:** `%tddft nroots 10 end`. TDA is the default; `TDA false` for full TDDFT, `triplets true` for triplets, `IRoot n` to optimize state n.
- **EOM-CCSD:** `! EOM-CCSD cc-pVDZ TightSCF` with `%mdci nroots 9 end`; `! IP-EOM-CCSD` / `! EA-EOM-CCSD` for ionized and attached states (UHF: `DoAlpha` or `DoBeta`). Oscillator strengths use a linear approximation by default.
- **STEOM-CCSD:** `! STEOM-CCSD def2-TZVP def2-TZVP/C TightSCF` with `%mdci nroots 10 end`. Each root prints a "Percentage Active Character": trust roots above 98 %; below that, ask for more roots. For larger molecules, `bt-PNO-STEOM-CCSD` with `TightPNO` (manual: within 0.01 eV of canonical EOM-CCSD; full keyword line unverified), or `STEOM-DLPNO-CCSD` (closed shell only, 96 % rule, one core only in 6.1).
- **First run:** reproduce a starter calculation from `references/orca.md` (water HF/def2-SVP = −75.959334985643 Eh, or the DLPNO-CCSD(T) water example in `examples/orca/`) on the same machine.

## 5. Pitfalls

- `mpirun orca ...` or a bare `orca` in a parallel job: "FATAL ERROR ENCOUNTERED" or "has to be called with full pathname".
- Wrong OpenMPI version on `PATH` (missing `libmpi.so.*`, or the run dies at the first parallel module).
- Reading `%maxcore` as the total memory: Slurm kills the job with no ORCA error.
- `%pal nprocs` larger than `--ntasks` (MPI "not enough slots") or `-c N` with one task (cores idle).
- Leftover `.gbw` files from another geometry or ORCA version (AutoStart; "Input geometry does not match").
- Running in shared storage: slow, and a full disk can fail silently.
- Comparing energies from different ORCA versions: grids and defaults changed in ORCA 6.
- Before quoting any number, use `reporting-computational-results`.

## 6. Not verified yet

- Whether PACE has an ORCA module, and a tested sbatch script on PACE.
- How PACE's job-submit routing treats `--ntasks` with `--mem-per-cpu`.
- The exact `bt-PNO-STEOM-CCSD` input line and its auxiliary-basis needs.
- Timings and the best process count per node on PACE (manual: RI-DFT scales to about 16 processes).
