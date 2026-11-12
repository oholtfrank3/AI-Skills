---
name: di-dim
description: Exciton DIM (Di-DIM, diabatized diatomics-in-molecules) for a neutral Rydberg exciton moving through rare-gas clusters, surfaces and solids (e.g. the Ar 3p5 4s exciton and Ar2* excimers) - which excited states per atom, computing the Ar2* pair curves including the 4p partner states, diabatizing the 4s/4p mixing and choosing the criterion with a small EOM-CC benchmark, the Q-Chem symmetry trap for d-aug dimer scans, molecules near an exciton, validation numbers and exciton dynamics. Use when someone models excitons, excimers or Rydberg states in a large rare-gas system, or when an exciton DIM overbinds Ar3*. For holes (positive charges) use dim.
---

# Exciton DIM / Di-DIM (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Answer in one short paragraph of plain prose, about 90 words (never more than 120; count them): no headings, no bullet or numbered lists, no tables. Start with the single most likely answer, give one reason in plain words, name one concrete next step, ask at most one question, and end by offering more ("I can go through …"). Explain every specialist term, symbol and unit in a few words when you first use it (Ar₂*, diabatize, meV); don't name methods by acronym in a first reply. Don't quote numbers you can't source; leave out side tips (basis-set traps, code bugs) until the user gets there. End with one short line saying where the advice comes from. Ask before running or submitting anything.

**Everything below and in `references/` is for you, not for the user.** Read what you need, then answer in the short form. Two model first replies:

> *"Plain DIM on the 4s curves binds Ar₃* far too strongly. What am I missing?"*
> Most likely the 4s/4p mixing. When two excited argon atoms (Ar₂*) come close, the state you call "4s" takes on some 4p character, so its curve is deeper than a pure 4s pair. A model with only 4s states on each atom can't hand that extra binding on to a third atom correctly, so the trimer overbinds. The fix is to compute the matching 4p curves too and separate the two characters (diabatize, the Di-DIM idea), choosing how with a small accurate calculation on Ar₃*. Do you have the 4p curves? I can go through that check next.
> *Source: group exciton DIM notes; Dhiman & Gervais, Chem. Phys. Lett. 2026.*

> *"Can I model an argon exciton on a surface the same way as our Ar⁺ hole model?"*
> Partly. The idea is the same (one set of states per atom, energies built from two-atom curves), but an exciton is a neutral excited atom, so each atom needs twelve excited states (the triplet and singlet 4s levels) instead of one or six, and the charge-induced polarization of the hole model doesn't apply. The first step is the Ar₂* curves (two argon atoms sharing one excitation), including the nearby 4p states, because their mixing is what makes or breaks the model. Do you have those curves? I can go through the full build next.
> *Source: group exciton DIM notes (Di-DIM).*

## Where the details are

| Topic | File |
|---|---|
| Basis, pair curves with 4p partners, diabatization and its benchmark, numerics, molecules near an exciton, validation checklist and reference values, dynamics | `references/recipe.md` |
| Shared DIM machinery (pair-curve rotation for p-type states, numerics, finite regions, initial conditions, CSDM) | `dim` skill, `references/building.md` |
| SHARC settings | `sharc` skill |
| EOM-EE-CCSD reference calculations | `eom-cc` skill |
| The group's exciton code and current results | private `compchem-group` plugin (`dim-group-code`) |

## Facts you'll need most often

- Basis for 3p⁵4s: three p-hole orientations × {triplet, singlet} = 12 spin states per excited atom; H = Σ_pairs H_AB − (M − 2) Σ_A H_A.
- Plain adiabatic DIM on 4s curves alone overbound Ar₃* (700–1300 cm⁻¹ against CASPT2 340, HPP 290, Di-DIM 160 cm⁻¹).
- Compute the 4p Σ partners with the 4s curves (EOM-EE-CCSD, doubly augmented basis), then diabatize the s/p Σ_g mixing. Choose the criterion by a linear-Ar₃* EOM benchmark, never by matching a published Dₑ.
- No ion-induced polarization for a neutral exciton; say so, because surface excimers carry a dipole the model lacks.
- Q-Chem can silently drop Ar₂ d-aug jobs to C1 at R ≥ 3.5 Å and miss the lowest state; PySCF symmetry-projected EOM-EE is the workaround.

Sources: Dhiman & Gervais, Chem. Phys. Lett. (2026), doi:10.1016/j.cplett.2026.142825 (Di-DIM); Dhiman, Douady & Gervais, Mol. Phys. 120, e2049905 (2022); Kuntz & Valldorf, Z. Phys. D 8, 195 (1988); group exciton DIM notes (Nov 2026, PRELIMINARY).
