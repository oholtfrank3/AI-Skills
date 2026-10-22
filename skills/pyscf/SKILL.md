---
name: pyscf
description: Writing, running and debugging PySCF 2.x scripts - molecule setup (basis, charge, spin), HF/DFT and SCF convergence problems, open-shell and wrong-spin-state issues, stability analysis, CASSCF/CASCI active spaces, MP2/CCSD(T), TDDFT, geometry optimization and frequencies, dispersion, properties and orbital output, and making PySCF fast and safe on Slurm (threads, memory, scratch). Use for any PySCF script or error; for EOM-CC use eom-cc, for real-time dynamics use tides.
---

# PySCF in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. Ask before running or submitting anything. See `troubleshooting` §2.

Sources, starter calculations with reference energies, and dated known issues are in the `troubleshooting` skill, `references/pyscf.md`. Check it before guessing a fix. EOM-CC details: `eom-cc` and `references/qchem-pyscf-eomcc-cap.md`. Real-time TDDFT: `tides`.

## 1. When PySCF is the right tool

- **Good fit:** scripted or custom workflows (loops over geometries, custom Hamiltonians, orbital surgery), CASSCF/CASCI, CCSD(T) and EOM-CC on small-to-medium systems, anything TiDES builds on, and GPU DFT through gpu4pyscf.
- **Consider Q-Chem instead:** large production DFT, CAP-EOM, or features PySCF lacks (check `method-selection`).
- **Start from the closest file in `github.com/pyscf/pyscf/examples`.** The examples are the real documentation. Run it unchanged first.
- **Record the version** (`pyscf.__version__`); defaults change between releases (e.g. B3LYP changed in 2.3).

## 2. Setup and performance

- **Set threads before Python starts**, in the Slurm script: `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` (and `MKL_NUM_THREADS`/`OPENBLAS_NUM_THREADS` to match). Setting `os.environ` after `import pyscf` or numpy does nothing. Inside Python use `lib.num_threads(n)`.
- **One consistent install.** Mixed pip wheels can load two OpenMP runtimes and give silently wrong numbers (issues #2448, #2606). Prefer one conda-forge env, or one clean pip env.
- **Memory:** every object defaults to `max_memory = 4000` MB, whatever the node has. Set `mf.max_memory` (and `mycc.max_memory`) to ~80 % of the Slurm allocation, or export `PYSCF_MAX_MEMORY`. It is a soft limit: CCSD(T) can overshoot.
- **Scratch:** export `PYSCF_TMPDIR=/tmp/$USER/$SLURM_JOB_ID` (node-local disk) and request `--tmp`. Sizes and node classes: `pace-slurm` §3.
- **Always set `mf.chkfile`** to a named file next to your results. Without it the chkfile is a temporary file and is deleted on success.
- **Large systems:** `.density_fit()` for HF/DFT (small, systematic error ~1e-5 Eh per molecule in Starter 1).
- Resources and submission: `pace-slurm`. Propose the job and wait for an OK.

## 3. Core recipes

- **Molecule:** `mol = gto.M(atom=..., basis='cc-pvdz', charge=0, spin=0)`. **`spin` = 2S = N_alpha − N_beta**, not the multiplicity: doublet 1, triplet 2. Coordinates in Å.
- **SCF/DFT:** `mf = mol.RHF().run()`, `mol.UHF()`, `mol.ROHF()`, `mol.KS(xc='wb97x-v')`. Always set `xc` (default is LDA). Use `mf.grids.level = 4`–5 for frequencies and weak interactions.
- **Dispersion:** `pip install pyscf-dispersion`, then `mol.KS(xc='b3lyp-d3bj')` or `'wb97x-d4'`. Check that a dispersion energy is printed.
- **Optimization:** `pip install geometric`; `from pyscf.geomopt.geometric_solver import optimize; mol_eq = optimize(mf)`.
- **Frequencies:** at the optimized geometry, same level and grid: `h = mf.Hessian().kernel()`, then `pyscf.hessian.thermo.harmonic_analysis` and `thermo.thermo`.
- **Correlation:** `mp.MP2(mf)`, `cc.CCSD(mf, frozen=n).run()`, `.ccsd_t()`. Freeze only true core.
- **Excited states:** `mf.TDA().run(nstates=5)` or `mf.TDDFT()`; `td.e` is in Hartree; `td.oscillator_strength()`, `td.analyze()`.
- **Output:** `mf.dip_moment()`, `mf.mulliken_pop()`, `mf.analyze()`, `tools.molden.from_scf(mf, 'x.molden')`, `tools.cubegen.orbital(...)`.
- **Extensions:** dispersion, properties (NMR, EPR, polarizabilities), pyscf-forge (newer methods), gpu4pyscf (`.to_gpu()`). If an import fails, the extension is not installed.

## 4. SCF convergence playbook (in order)

**This list is for you, not for the user.** In the first reply, pick the single step that best fits what they told you and give it in a few lines of code, plus a one-line charge/spin check if the system is open-shell. Then say in one line what comes next if it fails, and offer the rest. Example for "my UHF radical cation won't converge":

> Most often this is a poor starting guess. Start the cation from the neutral molecule's converged density and use the second-order solver:
> ```python
> dm0 = mol_neutral.RHF().run().make_rdm1()
> mf = mol.UHF().newton(); mf.kernel(dm0=(dm0/2, dm0/2))
> ```
> Also check `spin=1` (it's the number of unpaired electrons, not the multiplicity). If it still won't converge, I'd add a level shift next. Want the full list, or help checking the result with a stability analysis?

1. **Read the log** (`mol.verbose = 4`): oscillating energy, a small HOMO–LUMO gap, or `WARN: HOMO ... >= LUMO`?
2. **Better guess:** `mf.init_guess = 'atom'` or `'huckel'`, or a converged density from a simpler case: `mf.kernel(dm0)`, or `scf.hf.from_chk(mol, 'other.chk')` (also works across bases and geometries).
3. **Damping/DIIS:** `mf.damp = 0.5; mf.diis_start_cycle = 5`, larger `mf.diis_space`, or `mf.DIIS = scf.ADIIS`.
4. **Level shift:** `mf.level_shift = 0.2`–0.5 for small gaps. It changes virtual energies, so remove it for the final orbitals and properties.
5. **Second-order:** `mf = mf.newton()` from the best orbitals so far. Converges hard cases but may land on a saddle point.
6. **Stability, always, for open shells and anything that needed steps 3–5:** `mo1, _, stable, _ = mf.stability(return_status=True)`; if unstable, restart from `mf.make_rdm1(mo1, mf.mo_occ)` and repeat (`examples/scf/17-stability.py`). Use `external=True` to test RHF→UHF.
7. **Still stuck:** fractional occupation or smearing, a smaller basis first, or check the geometry and charge/spin. Search the issues before more test jobs (`troubleshooting` §1).

## 5. Open-shell and spin pitfalls

- **Check ⟨S²⟩** (`mf.spin_square()`). For a triplet expect ~2.0; much larger means spin contamination. O2/cc-pVDZ UHF gives 2.033.
- **Broken-symmetry singlets need a broken guess:** `mf.init_guess_breaksym = 'mix'` or edit the alpha/beta guess densities (`examples/scf/32-break_spin_symm.py`). Otherwise UHF stays RHF-like.
- **ΔSCF finds the lowest state of each occupation.** To hold an excited hole or electron use MOM (`scf.addons.mom_occ`); for genuinely excited ion states use EOM (`eom-cc`).
- **Same input, different answer between runs** with several threads: multithreaded sums are not bit-reproducible and degenerate open shells break symmetry either way. Compare energies, run stability, keep the lowest stable state.
- **ROHF vs UHF:** ROHF is spin-pure but often harder to converge; UHF is easier but can drift to another state. Check the spin density on each fragment.

## 6. CASSCF/CASCI

- **Choose the active space on purpose:** look at the orbitals first. `mc.sort_mo([...])` uses **1-based** indices. AVAS (`avas.avas(mf, ['Fe 3d'])`) or MP2/UHF natural orbitals are good automatic starts.
- **Every active orbital should be fractionally occupied** (natural occupations ~0.02–1.98). A fully occupied or empty active orbital makes CASSCF stall (issue #2493).
- **Watch for drifting active spaces** along a scan: carry orbitals point to point with `mcscf.project_init_guess` and check the energy curve is smooth.
- **Near-degenerate states:** state-average (`mc.state_average_([0.5, 0.5])`). The printed energy is the average; run CASCI on the final orbitals for each state.
- **Spin contamination in the CI:** `mc.fix_spin_(ss=...)`.
- `nelecas=(na, nb)` sets the open-shell active electrons.

## 7. Group lessons (Kretchmer group, from local notes)

These come from the Ar/water hole project. Sources (file:line) are in `references/pyscf.md`.

- **Identify orbitals and holes by ownership, not by energy ranking.** Localize s-like and p-like blocks separately (split by Mulliken s vs p weight); Pipek–Mezey over the whole valence block gave sp hybrids.
- **Assign sites one-to-one and check every site appears once.** An argmax assignment silently dropped one site.
- **A cation ROHF that will not converge:** seed `newton()` from the neutral density. A UHF cation can converge to the wrong hole (3p instead of 3s): check the spin density.
- **"99 % localized" Mulliken spin can still hide partial delocalization.**
- **CCSD(T) can die out of memory in (T) after a day, with no checkpoint.** Save CCSD amplitudes and size memory for (T) first.
- **Put the basis in checkpoint names** (or one directory per job): aDZ and aTZ files overwrote each other.
- **Never force convergence flags or chunk Davidson restarts** (`eom-cc` §2).
- **For hole dynamics, check RT-TDDFT against TD-CASCI** (`tides` §3).

## 8. Not verified yet

- Water B3LYP optimization and frequencies (Starter 2) were not run locally.
- Which PySCF release includes the geomeTRIC TS fix and the level-shift + stability fix.
- Best out-of-core and memory settings for large UCCSD(T) on PACE.
- Whether gpu4pyscf runs on the group's PACE GPU nodes, and its speed-up there.
