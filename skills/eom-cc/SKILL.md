---
name: eom-cc
description: Recipes and pitfalls for EOM-CCSD excited, ionized and doubly ionized states (EE / IP / DIP, CAP-EOM, Rydberg states, oscillator strengths, NTO/Dyson orbitals) in Q-Chem 6.x and PySCF. Use when setting up, debugging or interpreting any EOM-CC calculation, especially on rare-gas clusters, water, or other weakly bound systems.
---


# EOM-CC in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

Every rule below cost at least one failed multi-hour job. Read the relevant section before submitting.

## 1. Basis sets

- **Rydberg states need diffuse shells beyond aug.** Plain aug-cc-pVXZ puts Ar 4s 0.5–0.7 eV too high. Doubly augmented, even-tempered (d-aug) sets fix 4s and 4p to ~0.03 eV vs experiment. Higher Rydberg states (Ar 3d/5s) can stay 0.3–0.6 eV high even at d-aug-aQZ. Test t-aug or continuum-like shells, and say so if they are not converged.
- **Continuum-like (KBJ) exponents** follow Kaufmann–Baumeister–Jungen: alpha(l, n) = 1 / (4 (a_l n + b_l)^2), with a_l and b_l from Coccia et al. 2016, Table I. Cite the source. Do not invent exponents.
- **Ghost functions for an outgoing electron** (CAP, ICD/ETMD widths): place ghost centres and match their exponents to the kinetic energy of the secondary electron, not a generic diffuse set.
- **Mixed BASIS in Q-Chem** must list every atom, ghosts included. A missing atom fails, or silently gets the wrong basis. `BASIS = MIXED` also turns symmetry off, so per-irrep root requests no longer apply.
- **Basis bias usually cancels in interactions.** Example: aVDZ vs aVTZ shifts Ar 3p⁻¹ by −0.138 eV and 3s⁻¹ by −0.043 eV per Ar, nearly constant across clusters. Check this before buying a bigger basis for a shift you only need as a difference.
- **Even-tempered extras in `$basis` / `$zbasis`** must follow the standard set inside each atom block. Run the shipped Q-Chem sample input before guessing.

## 2. Convergence

**Missing or unconverged roots, first reply.** The developers' order (`troubleshooting` → `references/qchem-pyscf-eomcc-cap.md`) is a list for you, not for the user. Give step 1 only, with its `$rem` lines. Say in one line what comes next, and offer to run `scripts/check_qchem_output.py` on their output:

> The solver didn't find starting points for all your states, so some never settled. First try more guesses, solved cheaply in the singles space first:
> ```
> EOM_NGUESS_SINGLES   12   ! about 3x the roots you asked for
> EOM_PRECONV_SINGLES  1
> ```
> If that doesn't do it, I'd give the solver more iterations next. Want me to run the group's output checker on your .out file first? It shows which roots failed.
> Source: Q-Chem forum, "How to troubleshoot EOM calculations" (talk.q-chem #59).

- **Always set `EOM_DAVIDSON_CONVERGENCE 7`** (or tighter) for CAP or complex-valued EOM. The default left Im(E) unconverged, so widths changed by +20 to +135 % when tightened.
- **Near-degenerate roots** (≈ 10 meV apart) can stall block Davidson whatever the tolerance. Ask for more roots than you need. Use user guesses. Separate the states by symmetry if you can. When roots drifted between states in a dense manifold, the group's fix was more iterations and vectors (`EOM_DAVIDSON_MAX_ITER 600`, `EOM_DAVIDSON_MAXVECTORS 5000`), not a new guess. Re-derive `$eom_user_guess` whenever the cluster changes.
- **Check that every root converged, at every η.** Q-Chem still prints Re/Im energies for roots that did not converge. Grep for `Max Davidson iteration exhausted` and check the converged-root count. A group "plateau" built from unconverged points moved from 39 to 45 meV once converged (`EOM_DAVIDSON_MAX_ITER` default is 30). Tightening is cheap: the Davidson step was only a few % of a CAP-EOM job; the complex CCSD dominates.
- **PySCF: run EOM in one go.** Chunked restarts broke convergence. Never set `converged = ones` to force a result.
- **PySCF `ipccsd_star` silently drops near-degenerate roots.** Grep the WARN lines and count roots. Root pairing was fixed in PySCF 2.14 (PR #3316, more on master in #3404); retest on a newer PySCF before relying on the workaround.
- **Cation references:** ROHF on the cation often never converges. Seed `newton()` from the neutral density. UHF optimisations can drift to the wrong hole (e.g. a 3p hole when you wanted 3s); check the spin density.
- **Frozen core:** freeze only true core (e.g. O 1s). Freezing more can swap orbital order between charge states, so the "same" root is a different state in the two calculations. Example: freezing 2 orbitals per water froze O 2s in the neutral but an Ar 3s in the cation. The Q-Chem keyword is `N_FROZEN_CORE` (`CC_FROZEN_CORE` does not exist and crashes the job).

## 3. Identifying roots

- **Never identify orbitals or roots by energy ranking.** Rankings cross between geometries and bases. Use an ownership partition instead: for localised holes, split s/p by Mulliken weight before Pipek–Mezey localisation, then assign each root by its weight on each fragment.
- **`EOM_USER_GUESS` duplicates:** count the guess MOs explicitly. With grouped guesses, check that the minimum overlap eigenvalue between guess vectors is ≥ 0.1, or you get duplicate roots.
- **Satellites (2h1p for IP, 2p2h for EE):** an empty Amplitude block or small R1² means a satellite. Do not report it as a main line.
- **Comparing two runs (e.g. ghost vs no ghost):** compare root counts per energy bin. Never pair the i-th sorted root of one run with the i-th of the other (that gave fake +0.7 eV shifts). Roots that do not move when ghosts are added are bound states or satellites; pseudo-continuum roots appear only with the ghosts.
- **Open or closed channel: fix the final-state definition first.** Filter out delocalized DIP roots before calling a channel open (in one cluster this changed "41 of 41 open" to 38 open, 3 closed). Use the same definition across cluster sizes, and never compare "the lowest k roots" between runs that cover different parts of the manifold.
- In clusters, check where each state lives (fragment weights, NTOs). An "Ar 4s" root can be mixed with water Rydberg or charge-transfer states.

## 4. Properties and output (Q-Chem 6.x)

- **Oscillator strengths:** `CC_TRANS_PROP = TRUE`. Without it no transition moments are printed. Check the output for the transition block before building spectra.
- **NTOs and Dyson orbitals:** request them in the same job (`NTO_PAIRS`, `CC_DO_DYSON`), with `MAKE_CUBE_FILES` or `.fchk` output, so images match the reported roots.
- **Spectra:** broaden stick spectra with a stated Gaussian/Lorentzian width and say what it is. Label which roots are satellites or charge transfer.

## 5. Method choice and known offsets

- EOM-DIP-CCSD overshoots ΔCCSD dications by about +0.2 eV at long range. Do not quote EOM-DIP − ΔCCSD(T) as a like-for-like gap.
- **CAP with EOM-DIP is not available in Q-Chem 6.3.1** (group forum post, talk.q-chem.com #3172, unanswered). Check newer versions before planning it.
- **Targeting DIP states:** `EOM_USER_GUESS` together with `DIP_STATES` crashed (double free) at the DIP stage; use `EOM_SHIFT` instead (units of 10⁻³ Eh, so `1085` ≈ 29.5 eV). IP→DIP Dyson orbitals come from `CC_DO_2P_DYSON`, which works in 6.3.1 but is not in the manual. There is no two-particle density export (`CC_EOM_PROP_TE` gives one-particle traces only).
- ADC(2)-s is cheap but misplaces states. ADC(2)-x is not available for IP in Q-Chem.
- **Raw CAP energies are not physical, and no single diagnostic proves a width.** Report both the raw and the first-order corrected (Jagau, JPCL 5, 3078) trajectories. If two systems swap order between raw and corrected, they are equal within method error. A flat plateau, a small ξ and a "sensible" deperturbed width are all passed by a channel-closed state whose true width is zero. What holds up is a **matched null**: the same cage, box and η grid on a state whose channel is closed. Quote the open/closed separation. Setup and checks are in §5a.
- A symmetry-broken UHF "localised" hole with spin ≈ 0.99 can still contain most of the charge-resonance energy. Check how localised the reference really is before calling a residual "missing polarisation".

## 5a. CAP-EOM-CCSD in Q-Chem: setup and checks

Details, numbers and sources for each point are in `troubleshooting` → `references/qchem-pyscf-eomcc-cap.md`, "CAP setup and analysis (group runs)".

- **Keep the molecule where the box is.** The `CAP_TYPE 1` box is centred on the origin of the input frame. Centre the molecule on the origin and stop Q-Chem from reorienting it (the group used `SYMMETRY false`, `SYM_IGNORE TRUE`, `CC_SYMMETRY false`). Translating the molecule moves the CAP, which makes a clean placement test.
- **`COMPLEX_CCMAN` always needs a `$complex_ccman` block**, and it does not work with FNO. Both stop the job within seconds.
- **Box size:** put the wall just outside the molecule's density, not outside the basis-function tails. Scale `CAP_X/Y/Z` together and quote the smallest gap between an atom and the wall, per axis, for every geometry. Run at least three box sizes.
- **Wall vs ghost shells:** put each wall in a gap between ghost shells, at least ~2.7 bohr from the shells on both sides.
- **Cheap early checks:** a first-order correction printed as ≈ (0, 0), or no converged roots at any η, means the CAP is not reaching the state (wall too far out). A negative width that grows with η means the wall is cutting into bound density.
- **One donor (root) per CAP job.** Tracking four near-degenerate roots in one job biased widths low and gave negative-width points.
- **η grid:** start near 0.001, find each donor's own window, and compare boxes each at its own best η. A sparse log grid can fake a common η_opt.
- **Choosing η_opt for narrow (sub-meV) widths:** use the flattest Γ plateau, not the minimum of η|dE/dη|. Drop root switches first.
- **Read Γ from the 8-decimal "Ionization energies for CS/CAP-EOM-IP states" block**, not the 4-decimal summary (it rounds widths to ~0.2 meV). Q-Chem prints the IE as (Re, Im) with Im > 0 for a decaying state, so Γ = +2 Im(IE); from total energies, Γ = −2 Im(E). τ (fs) × Γ (meV) = 658.2.
- **ξ (Gyamfi–Jagau) must be referenced to the neutral**, or a root switch can score best. A small ξ never proves a width (above).
- **No cube or density output in η scans.** It roughly doubled run time in the group's scans. Make pictures in one separate job.
- **A real CAP (`CAP_RE_ETA`, CR-CAP) can remove a bound-state artefact.** Use positive values of order 1 a.u. (the group used 0.5–2). Never negative: that created a state bound inside the absorber, at an IP of 3758 eV.
- **Never use an empirical null "floor" as a hard cutoff** for whether to run or report a donor. Compare to a matched null in the same cage.

## 6. Running on a cluster

- **Check inputs with the plugin's checker before submitting:** `python3 <plugin>/scripts/check_qchem_input.py job.in` (the `scripts/` folder is two levels above this skill's folder). After the job, run `scripts/check_qchem_output.py job.out`. It checks that the job really finished (the "Thank you very much" line plus a clean `.err`; never trust `sacct` COMPLETED), that every requested root is there, and flags satellites and unconverged roots. The input checker catches incomplete mixed-basis lists, loose Davidson convergence for CAP, CAP with EOM-DIP, `COMPLEX_CCMAN` without its `$complex_ccman` block, FNO with `COMPLEX_CCMAN`, a CAP box the molecule may be rotated out of, and `EOM_USER_GUESS` combined with DIP states or projected CAP.

- **Q-Chem scratch collisions:** give every job its own scratch:
  ```bash
  export QCSCRATCH=/tmp/$USER/$SLURM_JOB_ID
  export QCLOCALSCR=/tmp/$USER/$SLURM_JOB_ID
  ```
- **CAP-EOM scratch is large.** One 4-Ar CAP-EOM-CCSD job plateaued at ~1.2–1.4 TB of node-local disk. Request `--tmp` and a local-NVMe constraint (see the `pace-slurm` skill). A wrong old "peaks at 200–300 GB" comment cost dozens of jobs.
- **Large CAP / EOM jobs: scratch on the node's own disk, deleted when the job ends.** Template (sizes from the group's 4-Ar CAP runs; measure your own first):
  ```bash
  #SBATCH -c 24 --mem=360G --tmp=1350G --constraint=localNVMe
  export QCSCRATCH=$TMPDIR/qchem_$SLURM_JOB_ID      # node-local disk reserved by --tmp
  export QCLOCALSCR=$QCSCRATCH
  mkdir -p $QCSCRATCH
  trap 'rm -rf "$QCSCRATCH"' EXIT                    # clean up on normal exit
  qchem -nt 16 job.in job.out                        # 16 threads, see pace-slurm
  ```
  Nothing large touches shared scratch or project storage, and only the small outputs are kept. The trade-off is that **an interrupted point cannot be restarted**: plan to rerun it from the start. A timeout or OOM kill can skip the `trap`, so the node's job-local disk is the backstop (that PACE wipes it at job end is not confirmed in PACE's docs).
- **When you need the scratch afterwards** (restarts with `-save`, the `.fchk` and densities for pyopencap, long runs that may hit the wall): leave out the `trap`, and copy the files you need back to project storage at the end of the script. A `trap` on such a job deleted the savedir on a wall-clock kill. Node-local disk is wiped once the node is reallocated, so copy promptly.
- Search the literature and the shipped samples before trying fixes. Each wrong guess is a 2–5 h job. The `troubleshooting` skill has the search order, plus Q-Chem/PySCF doc links and forum-sourced known issues.
