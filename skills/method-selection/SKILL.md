---
name: method-selection
description: Turn a plain-language description of a chemical system and process ("how fast does the hole in Ar₂ decay?", "what is the UV spectrum of this cluster?", "does the charge move to the water?") into a calculation plan - which method and code (EOM-CC, CAP-EOM, pyopencap, TiDES RT-TDDFT/Ehrenfest, SHARC surface hopping, model Hamiltonians), which benchmarks to run first, the expected cost and the known failure modes. Use at the start of any new calculation or project, whenever someone is unsure which method to use, or when a non-expert describes what they want to model.
---

# Choosing a method (Kretchmer group notes)

The user may not be an expert. Do not jump to an input file. Find out what they actually want to know, pick the cheapest method that can answer it, and plan the benchmark that proves it works before the production run.

The examples below mostly come from one project (Ar 3s holes and ICD/ETMD at an Ar(111)–water interface). `references/worked-example-ar-water.md` shows how that project's choices were made. Treat a lesson from there as a warning to check, not as a general law.

## 1. Have a conversation, not a questionnaire

Assume the person may be new to Claude, to running jobs, and possibly to computational chemistry. A wall of options is overwhelming. Talk to them the way a helpful senior grad student would at a whiteboard.

**How each message should look:**
- **One question per message**, or two if they are tightly linked. Keep the message to a few short sentences.
- **Plain words first.** Say "how strongly the two molecules stick together" before "binding energy". Introduce a technical term only when the user needs it, and explain it in one clause.
- **Offer 2–3 concrete choices** in everyday terms, plus "not sure". When one choice is the usual starting point, say so, so "not sure" is easy to answer.
- **Do not preview the method,** the cost or the traps while you are still asking. Do not explain how each answer would change the plan.
- **Start from what they said.** Briefly reflect it back ("Two benzene rings next to each other, got it.") before the next question.
- **Infer what you can** from the system and their wording, and skip those questions. Fill in sensible defaults and mention them later, in the plan.

**What you need to find out, roughly in this order** (stop once the picture is clear):
1. **What they want to learn.** Ask about the physical question in plain terms: how strongly things stick, what colour of light it absorbs, what happens after an electron is knocked out, how something moves over time. This sets the process and the observable.
2. **Which state or situation**, if it is still ambiguous after (1): ground state, after absorbing light, after ionization.
3. **What answer would satisfy them:** one number, a comparison between a few arrangements, a curve, a spectrum, or a movie in time.
4. **How accurate it needs to be:** "a rough trend for a group meeting" vs "a number to compare with an experiment or a paper".
5. **Practicalities, at the end:** do they have structures, do they have a PACE allocation, and when do they need it. If they don't know, offer to work it out with them.

For the expert vocabulary behind these questions, see the internal checklist below. Use it to steer the conversation; never show it to the user as a list.

<details><summary>Internal checklist (do not paste to the user)</summary>

- System: atoms/molecules, size, charge and spin, environment (gas / cluster / surface / solution), geometry available?
- Process: excitation, ionization, double ionization, decay of a metastable state (ICD, ETMD, Auger, autoionization, shape resonance), charge or hole migration, nuclear motion after excitation, a static property.
- Observable: energy, spectrum, width Γ / lifetime τ, populations vs time, branching ratios, kinetic-energy distribution.
- Timescale: attoseconds / femtoseconds / picoseconds / static.
- Accuracy: trend (~0.1–0.3 eV or ~0.3 kcal/mol) vs comparison with experiment (triples, basis extrapolation, error bars).
- Budget: core- or GPU-hours, deadline.

</details>

**When the picture is clear,** restate it in two or three plain sentences ("So you'd like to know how strongly two benzene rings stick together in a few common arrangements, roughly, for a group meeting next week. Is that right?"). Get a yes before planning.

**Example of a good first reply** to "I want to look at the energetics of the benzene dimer":

> Nice system. Benzene dimers are a classic test case. To point you the right way: are you mostly interested in **how strongly the two rings stick together** (and which way of stacking them is most stable), or in what happens when the dimer **absorbs light or loses an electron**? If you're not sure, the first one is the usual place to start.

## 2. Process → method

| Question | First choice | Cheaper / screening | Higher-level check | Skill |
|---|---|---|---|---|
| Vertical excitation energies, UV-Vis, Rydberg states | EOM-EE-CCSD (Q-Chem) | TDDFT (range-separated functional), ADC(2) | a triples-corrected EOM method (check what Q-Chem / PySCF offers for EE) | `eom-cc` |
| Ionization energies, hole states | EOM-IP-CCSD | ΔSCF, ADC(2) | EOM-IP-CCSD*, ΔCCSD(T), focal-point basis extrapolation | `eom-cc` |
| Dications, two-hole final states | EOM-DIP-CCSD | ΔSCF / ΔMP2 | ΔCCSD(T) (for the lowest state per symmetry) | `eom-cc` |
| Is a decay channel open? | compare hole energy vs final-state energy, both at the **correlated** level | — | triples + basis-extrapolated ends of the channel | `eom-cc` |
| Decay width Γ / lifetime (ICD, ETMD, Auger, resonances) | CAP-EOM-CCSD (Q-Chem) with η trajectories | Fermi-golden-rule / virtual-photon estimates for trends | Fano-ADC + Stieltjes (not on PACE) | `eom-cc` §5; `pyopencap` |
| Electron dynamics, attosecond charge migration, field-driven response | RT-TDDFT in TiDES | — | TD-CASCI (no self-interaction error) | `tides` |
| Electrons + nuclei, fs–ps, few-atom system | surface hopping (SHARC) on ab initio states | Ehrenfest (TiDES) | multiple decoherence schemes; FSSH vs CSDM | `sharc` |
| Hole/charge transport in a large cluster, surface or solid | model Hamiltonian (e.g. DIM) parametrized and validated on EOM-CC, dynamics in SHARC | static site-energy map from EOM-IP clusters | blind validation points the model never saw | `sharc` |

A skill marked **pending** does not exist yet. For those codes, tell the user that the plan needs review by someone who runs that code. Do not fill the gap with generic advice presented as group practice.

## 3. Traps to raise while choosing (each one has already cost us weeks)

- **The EOM-IP 2h1p continuum sits too low.** In CAP-EOM-IP-CCSD the discretized final states (2h1p) are uncorrelated. On Ar–water they sat ~1.5 eV below the correlated EOM-DIP threshold, so channels that are closed at the correlated level are open inside the method. Before trusting a width, check the in-method 2h1p window (`EOM_SHIFT` near the hole, ~30 IP states) as well as the EOM-DIP threshold, and say which channels are open at which level.
- **Inner-valence holes have large method errors.** EOM-IP-CCSD put the Ar 3s⁻¹ hole ~0.6 eV above experiment, while the outer-valence dication was much better. Errors at the two ends of a channel do not cancel. Plan triples/basis corrections for both ends, or anchor to experimental fragment IPs.
- **Mean-field dynamics with DFT can self-trap or collapse.** CAM-B3LYP RT-TDDFT/Ehrenfest localized the Ar hole artificially (self-interaction error) and pulled the water onto the Ar (O–Ar → 0.5–1.5 Å). If the question is *whether* a charge moves, a DFT mean-field answer of "it stays" is not evidence. Plan an SIE-free check (TD-CASCI) or use a model Hamiltonian validated against EOM-CC.
- **FSSH is internally inconsistent for delocalized carriers.** Active-state fractions disagreed with wavefunction populations by 2–3× for delocalized holes even with decoherence. Coherent switching with decay of mixing (CSDM) removed the split. Compare both before trusting populations.
- **Projected CAP (pyopencap) did not work on Ar–water.** With 5–10 EOM-IP states the uncorrected widths were 5–32 meV against 0.1–0.35 meV from direct CAP-EOM, the corrected widths were ~0 ± 0.014 meV with root switches, and runs with ≥ 20 states never finished (scratch and walltime). Budget for convergence in the number of states before choosing it. Validate any projected-CAP set-up on a dimer with a known width before using it on the real system.
- **Raw CAP numbers prove nothing on their own.** A CAP-stabilized bound state can also give a flat η plateau. Always plan a channel-closed (null) control.
- **Small basis sets miss polarization.** cc-pVDZ captured 35 % of the Ar polarizability, aug-cc-pVDZ 88 %, aug-cc-pVTZ 97 %. Check the property you need (polarizability, Rydberg spacing), not just the total energy.

## 4. Build the plan bottom-up

1. **Smallest system that has the physics** (a dimer, a trimer, the molecule + one partner). Run the method there first and compare to literature or a higher level.
2. **Method ladder on that small system:** cheap → production method → one higher-level check. The production method is acceptable when it reproduces the check on the quantity you need (e.g. a coupling to ~1 meV, an ordering, a ratio), not on the total energy.
3. **Convergence of what you report:** basis, cluster size / shells, number of roots, CAP strength η, trajectory count. One knob at a time.
4. **Only then the production system.** Estimate cost from the benchmark timings and memory/scratch (`pace-slurm` for resources, `eom-cc` §6 for CAP scratch).
5. **Decide up front what result would mean "the method failed"** and what you would run instead.

## 5. Output: the plan

Write the full plan to `PLAN_<short-name>.md` in the user's working directory. **In chat, keep it short:** say in two or three plain sentences what you suggest running first and why, roughly how long it will take, and point them to the file for details. Then ask one question, usually "Does that sound right, or should we change anything?" Walk through the details only if they ask.

The plan file should include:

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
