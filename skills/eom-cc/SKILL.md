---
name: eom-cc
description: Recipes and pitfalls for EOM-CCSD excited, ionized and doubly ionized states (EE / IP / DIP, CAP-EOM, Rydberg states, oscillator strengths, NTO/Dyson orbitals) in Q-Chem 6.x and PySCF. Use when setting up, debugging or interpreting any EOM-CC calculation, especially on rare-gas clusters, water, or other weakly bound systems.
---


# EOM-CC in practice (Kretchmer group notes)

> **Talking to the user:** they may be new to this. When answering a question or a problem, keep the reply short and plain: say what is going on in a sentence or two, give the single most likely fix or next step, and ask before running or submitting anything. Offer more detail instead of dumping it. See `troubleshooting` §2.

Every rule below cost at least one failed multi-hour job. Read the relevant section before submitting.

## 1. Basis sets

- **Rydberg states need diffuse shells beyond aug.** Plain aug-cc-pVXZ puts Ar 4s 0.5–0.7 eV too high. Doubly augmented, even-tempered (d-aug) sets fix 4s and 4p to ~0.03 eV vs experiment. Higher Rydberg states (Ar 3d/5s) can stay 0.3–0.6 eV high even at d-aug-aQZ. Test t-aug or continuum-like shells, and say so if they are not converged.
- **Continuum-like (KBJ) exponents** follow Kaufmann–Baumeister–Jungen: alpha(l, n) = 1 / (4 (a_l n + b_l)^2), with a_l and b_l from Coccia et al. 2016, Table I. Cite the source. Do not invent exponents.
- **Ghost functions for an outgoing electron** (CAP, ICD/ETMD widths): place ghost centres and match their exponents to the kinetic energy of the secondary electron, not a generic diffuse set.
- **Mixed BASIS in Q-Chem** must list every atom, ghosts included. A missing atom fails, or silently gets the wrong basis. `BASIS = MIXED` also turns symmetry off, so per-irrep root requests no longer apply.
- **Basis bias usually cancels in interactions.** Example: aVDZ vs aVTZ shifts Ar 3p⁻¹ by −0.138 eV and 3s⁻¹ by −0.043 eV per Ar, nearly constant across clusters. Check this before buying a bigger basis for a shift you only need as a difference.
- **Even-tempered extras in `$basis` / `$zbasis`** must follow the standard set inside each atom block. Run the shipped Q-Chem sample input before guessing.

## 2. Convergence

- **Always set `EOM_DAVIDSON_CONVERGENCE 7`** (or tighter) for CAP or complex-valued EOM. The default left Im(E) unconverged, so widths changed by +20 to +135 % when tightened.
- **Near-degenerate roots** (≈ 10 meV apart) can stall block Davidson whatever the tolerance. Ask for more roots than you need. Use user guesses. Separate the states by symmetry if you can.
- **PySCF: run EOM in one go.** Chunked restarts broke convergence. Never set `converged = ones` to force a result.
- **PySCF `ipccsd_star` silently drops near-degenerate roots.** Grep the WARN lines and count roots. Root pairing was fixed in PySCF 2.14 (PR #3316, more on master in #3404); retest on a newer PySCF before relying on the workaround.
- **Cation references:** ROHF on the cation often never converges. Seed `newton()` from the neutral density. UHF optimisations can drift to the wrong hole (e.g. a 3p hole when you wanted 3s); check the spin density.
- **Frozen core:** freeze only true core (e.g. O 1s). Freezing more can swap orbital order between charge states, so the "same" root is a different state in the two calculations.

## 3. Identifying roots

- **Never identify orbitals or roots by energy ranking.** Rankings cross between geometries and bases. Use an ownership partition instead: for localised holes, split s/p by Mulliken weight before Pipek–Mezey localisation, then assign each root by its weight on each fragment.
- **`EOM_USER_GUESS` duplicates:** count the guess MOs explicitly. With grouped guesses, check that the minimum overlap eigenvalue between guess vectors is ≥ 0.1, or you get duplicate roots.
- **Satellites (2h1p for IP, 2p2h for EE):** an empty Amplitude block or small R1² means a satellite. Do not report it as a main line.
- **Comparing two runs (e.g. ghost vs no ghost):** compare root counts per energy bin. Never pair the i-th sorted root of one run with the i-th of the other.
- In clusters, check where each state lives (fragment weights, NTOs). An "Ar 4s" root can be mixed with water Rydberg or charge-transfer states.

## 4. Properties and output (Q-Chem 6.x)

- **Oscillator strengths:** `CC_TRANS_PROP = TRUE`. Without it no transition moments are printed. Check the output for the transition block before building spectra.
- **NTOs and Dyson orbitals:** request them in the same job (`NTO_PAIRS`, `CC_DO_DYSON`), with `MAKE_CUBE_FILES` or `.fchk` output, so images match the reported roots.
- **Spectra:** broaden stick spectra with a stated Gaussian/Lorentzian width and say what it is. Label which roots are satellites or charge transfer.

## 5. Method choice and known offsets

- EOM-DIP-CCSD overshoots ΔCCSD dications by about +0.2 eV at long range. Do not quote EOM-DIP − ΔCCSD(T) as a like-for-like gap.
- **CAP with EOM-DIP is not available in Q-Chem 6.3.1** (group forum post, talk.q-chem.com #3172, unanswered). Check newer versions before planning it.
- ADC(2)-s is cheap but misplaces states. ADC(2)-x is not available for IP in Q-Chem.
- **Raw CAP energies are not physical.** Use the first-order deperturbed (Jagau, JPCL 5, 3078) trajectories, and report the eta-trajectory criterion. A flat plateau or small xi does not prove a resonance: a bound state stabilised by the CAP also passes. Run a channel-closed control.
- A symmetry-broken UHF "localised" hole with spin ≈ 0.99 can still contain most of the charge-resonance energy. Check how localised the reference really is before calling a residual "missing polarisation".

## 6. Running on a cluster

- **Q-Chem scratch collisions:** give every job its own scratch:
  ```bash
  export QCSCRATCH=/tmp/$USER/$SLURM_JOB_ID
  export QCLOCALSCR=/tmp/$USER/$SLURM_JOB_ID
  ```
- **CAP-EOM scratch is large.** One 4-Ar CAP-EOM-CCSD job plateaued at ~1.2–1.4 TB of node-local disk. Request `--tmp` and a local-NVMe constraint (see the `pace-slurm` skill). A wrong old "peaks at 200–300 GB" comment cost dozens of jobs.
- Search the literature and the shipped samples before trying fixes. Each wrong guess is a 2–5 h job. The `troubleshooting` skill has the search order, plus Q-Chem/PySCF doc links and forum-sourced known issues.
