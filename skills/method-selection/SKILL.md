---
name: method-selection
description: Turn a plain-language description of a chemical system and process ("how fast does the hole in Ar₂ decay?", "what is the UV spectrum of this cluster?", "does the charge move to the water?") into a calculation plan - which method and code (EOM-CC, CAP-EOM, pyopencap, TiDES RT-TDDFT/Ehrenfest, SHARC surface hopping, model Hamiltonians), which benchmarks to run first, the expected cost and the known failure modes. Use at the start of any new calculation or project, whenever someone is unsure which method to use, or when a non-expert describes what they want to model.
---

# Choosing a method (Kretchmer group notes)

The user may not be an expert. Do not jump to an input file. Find out what they actually want to know, pick the cheapest method that can answer it, and plan the benchmark that proves it works before the production run.

The examples below mostly come from one project (Ar 3s holes and ICD/ETMD at an Ar(111)–water interface). `references/worked-example-ar-water.md` shows how that project's choices were made. Treat a lesson from there as a warning to check, not as a general law.

## 1. Interview first (ask, then summarise back)

Ask only what you cannot infer. Group the questions into a single message. Do not ask them one at a time.

1. **System:** atoms/molecules, size, charge and spin, gas phase / cluster / surface / solution. Is there a geometry file?
2. **Process:** what happens physically. Pick one of: absorption/excitation, ionization, double ionization, decay of a metastable state (ICD, ETMD, Auger, autoionization, shape resonance), charge or hole migration, nuclear motion after excitation, a property at fixed geometry.
3. **Observable:** the number that answers the question. Examples: an energy (eV), a spectrum, a width Γ / lifetime τ, populations vs time, branching ratios, a kinetic-energy distribution.
4. **Timescale:** attoseconds (electrons only) / femtoseconds (electrons + light nuclei) / picoseconds (nuclei matter) / static.
5. **Accuracy needed:** a trend or ordering (~0.1–0.3 eV is fine), or a number to compare with experiment (needs triples or a focal-point correction and an error bar)?
6. **Budget and deadline:** core-hours or GPU-hours available, and when the answer is needed.

Then write back a 3–5 line restatement: "You want X for system Y, observed as Z, to accuracy W." Get a yes before planning.

## 2. Process → method

| Question | First choice | Cheaper / screening | Higher-level check | Skill |
|---|---|---|---|---|
| Vertical excitation energies, UV-Vis, Rydberg states | EOM-EE-CCSD (Q-Chem) | TDDFT (range-separated functional), ADC(2) | a triples-corrected EOM method (check what Q-Chem / PySCF offers for EE) | `eom-cc` |
| Ionization energies, hole states | EOM-IP-CCSD | ΔSCF, ADC(2) | EOM-IP-CCSD*, ΔCCSD(T), focal-point basis extrapolation | `eom-cc` |
| Dications, two-hole final states | EOM-DIP-CCSD | ΔSCF / ΔMP2 | ΔCCSD(T) (for the lowest state per symmetry) | `eom-cc` |
| Is a decay channel open? | compare hole energy vs final-state energy, both at the **correlated** level | — | triples + basis-extrapolated ends of the channel | `eom-cc` |
| Decay width Γ / lifetime (ICD, ETMD, Auger, resonances) | CAP-EOM-CCSD (Q-Chem) with η trajectories | Fermi-golden-rule / virtual-photon estimates for trends | Fano-ADC + Stieltjes (not on PACE) | `eom-cc` §5; `pyopencap` (pending) |
| Electron dynamics, attosecond charge migration, field-driven response | RT-TDDFT in TiDES | — | TD-CASCI (no self-interaction error) | `tides` (pending) |
| Electrons + nuclei, fs–ps, few-atom system | surface hopping (SHARC) on ab initio states | Ehrenfest (TiDES) | multiple decoherence schemes; FSSH vs CSDM | `sharc` (pending) |
| Hole/charge transport in a large cluster, surface or solid | model Hamiltonian (e.g. DIM) parametrized and validated on EOM-CC, dynamics in SHARC | static site-energy map from EOM-IP clusters | blind validation points the model never saw | `sharc` (pending) |

A skill marked **pending** does not exist yet. For those codes, tell the user that the plan needs review by someone who runs that code. Do not fill the gap with generic advice presented as group practice.

## 3. Traps to raise while choosing (each one has already cost us weeks)

- **The EOM-IP 2h1p continuum sits too low.** In CAP-EOM-IP-CCSD the discretized final states (2h1p) are uncorrelated. On Ar–water they sat ~1.5 eV below the correlated EOM-DIP threshold, so channels that are closed at the correlated level are open inside the method. Before trusting a width, check the in-method 2h1p window (`EOM_SHIFT` near the hole, ~30 IP states) as well as the EOM-DIP threshold, and say which channels are open at which level.
- **Inner-valence holes have large method errors.** EOM-IP-CCSD put the Ar 3s⁻¹ hole ~0.6 eV above experiment, while the outer-valence dication was much better. Errors at the two ends of a channel do not cancel. Plan triples/basis corrections for both ends, or anchor to experimental fragment IPs.
- **Mean-field dynamics with DFT can self-trap or collapse.** CAM-B3LYP RT-TDDFT/Ehrenfest localized the Ar hole artificially (self-interaction error) and pulled the water onto the Ar (O–Ar → 0.5–1.5 Å). If the question is *whether* a charge moves, a DFT mean-field answer of "it stays" is not evidence. Plan an SIE-free check (TD-CASCI) or use a model Hamiltonian validated against EOM-CC.
- **FSSH is internally inconsistent for delocalized carriers.** Active-state fractions disagreed with wavefunction populations by 2–3× for delocalized holes even with decoherence. Coherent switching with decay of mixing (CSDM) removed the split. Compare both before trusting populations.
- **Projected CAP (pyopencap) failed on Ar–water.** It gave widths 10²–10⁴× the direct CAP-EOM result and did not converge in the number of states. Validate any projected-CAP set-up on a dimer with a known width before using it on the real system.
- **Raw CAP numbers prove nothing on their own.** A CAP-stabilized bound state can also give a flat η plateau. Always plan a channel-closed (null) control.
- **Small basis sets miss polarization.** cc-pVDZ captured 35 % of the Ar polarizability, aug-cc-pVDZ 88 %, aug-cc-pVTZ 97 %. Check the property you need (polarizability, Rydberg spacing), not just the total energy.

## 4. Build the plan bottom-up

1. **Smallest system that has the physics** (a dimer, a trimer, the molecule + one partner). Run the method there first and compare to literature or a higher level.
2. **Method ladder on that small system:** cheap → production method → one higher-level check. The production method is acceptable when it reproduces the check on the quantity you need (e.g. a coupling to ~1 meV, an ordering, a ratio), not on the total energy.
3. **Convergence of what you report:** basis, cluster size / shells, number of roots, CAP strength η, trajectory count. One knob at a time.
4. **Only then the production system.** Estimate cost from the benchmark timings and memory/scratch (`pace-slurm` for resources, `eom-cc` §6 for CAP scratch).
5. **Decide up front what result would mean "the method failed"** and what you would run instead.

## 5. Output: the plan

Write the plan to `PLAN_<short-name>.md` in the user's working directory and summarise it in chat. Include:

- **Question:** the restatement agreed in §1.
- **Method and code**, plus one sentence on why it fits this process and observable, and what it cannot capture.
- **Benchmarks first:** system, method ladder, what counts as passing.
- **Production runs:** system(s), settings, number of jobs, estimated core-/GPU-hours and wall time.
- **Known risks** from §3 that apply, and how each is checked.
- **Fallback** if a benchmark fails.
- **Who should review it** (any pending-skill code; anything needing a lot of allocation).

Do not write inputs or submit anything until the user approves the plan. Submission always follows `pace-slurm` §0: propose the job, then wait for an explicit OK.

## 6. When to stop and bring in a person

- The process is not in the §2 table, or needs a code the group does not run.
- The cheapest credible plan costs more than the user's budget.
- Benchmarks disagree with each other by more than the effect the user wants to measure.
- The user wants a number for a paper and the method's known error is the same size as the effect.
