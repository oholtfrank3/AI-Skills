---
name: dim
description: Building, validating and running diatomics-in-molecules (DIM) model Hamiltonians for a hole (a positive charge) moving through many weakly bound atoms (rare-gas clusters, surfaces and solids, optionally with a molecule such as water) - site basis for s-holes, p-holes with spin-orbit, pair curves and the sign of the hopping term, many-body (Thole) polarization, adding a molecule, blind validation against EOM-CC, analytic gradients, and running the model in SHARC with CSDM (finite hole region, reflecting vs absorbing edges, initial conditions, decay as post-processing). Use when someone wants hole or charge dynamics in a system too large for ab initio dynamics, or is writing, debugging or checking a hole DIM code. For neutral excitons (Rydberg states, excimers) use di-dim.
---

# DIM model Hamiltonians (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Answer in one short paragraph of plain prose, about 90 words (never more than 120; count them): no headings, no bullet or numbered lists, no tables. Say the single most likely answer or next step, give one reason, ask at most one question, and offer the rest ("I can go through the full build / the validation checklist"). Leave out side tips (basis-set traps, code bugs, other caveats) and comparisons with other models until the user gets there. Explain every specialist term, symbol and unit in a few words when you first use it (e.g. Kr₂⁺, meV), because the user may be new; don't name methods by acronym (EOM-CC, CSDM) in a first reply. In a first reply about building a hole model, always include the polarization point (all atoms together, not pair by pair): it is the step people miss. End with one short line saying where the advice comes from. Ask before running or submitting anything.

**Everything below and in `references/` is for you, not for the user.** Read what you need, then answer in the short form. A model first reply:

> *"How would I build a DIM model for a hole in a few hundred Kr atoms, and how do I know it's right?"*
> DIM gives each atom one state ("the hole is here") and builds all energies from two-atom calculations, so hundreds of atoms are cheap. First, compute energy-versus-distance curves for Kr₂⁺ (two Kr atoms sharing one charge), with spin-orbit coupling (a spin splitting, large in Kr); their gap sets how fast the hole hops. The common mistake is polarization: let all atoms respond together, not pair by pair. It's right when it matches accurate calculations on small clusters you didn't fit to, within a few meV (thousandths of an eV). Do you have Kr₂⁺ curves yet? I can go through the full build or the checks.
> *Source: group DIM notes (Kuntz & Valldorf 1988).*

For a neutral exciton (an excited, not ionized, atom moving through the solid) use the `di-dim` skill instead.

## Where the details are

| Topic | File |
|---|---|
| When DIM fits, building H (site basis, pair curves, sign of W, p-holes, polarization), adding a molecule, numerics, dynamics, pitfalls | `references/building.md` |
| Excitons (Di-DIM) | `di-dim` skill |
| Validation checklist with the Ar 3s-hole numbers | `references/validation.md` |
| SHARC settings and the CSDM force patch | `sharc` skill, and `sharc/references/dim-ar-water.md` for this model |
| Ab initio reference calculations (EOM-IP/EE-CCSD) | `eom-cc` skill |
| The group's DIM code, parameters and current results | private `compchem-group` plugin (`dim-group-code`) |

## Facts you'll need most often

- Hopping W = ½(V_g − V_u) from the ion-dimer curves for an s-hole; for rare-gas holes W > 0 and the hole sits at the **lowest** eigenvalue. For p-holes the sign follows orbital parity (the Σ and Π blocks are ½(V_u − V_g)): see `references/building.md`. A dimer can't catch a sign error; an equilateral trimer can.
- Polarization must be many-body (self-consistent Thole induced dipoles, experimental α), with the induction tail removed from the pair curves. Pairwise induction put Ar surface sites 40–60 % too high.
- Validate blind against EOM-CC on small clusters (aim 1–5 meV), plus one large-system number (Ar: bulk polarization of one localized charge ≈ 1.0 eV, from 2p core ionization).
- In dynamics, report wavefunction populations, and both a reflecting and an absorbing edge.

Sources: Ellison, JACS 85, 3540 (1963); Kuntz & Valldorf, Z. Phys. D 8, 195 (1988); Bonhommeau, Halberstadt & Buck, Int. Rev. Phys. Chem. 26, 353 (2007); Zhu, Nangia, Jasper & Truhlar, JCP 121, 7658 (2004) (CSDM); group validation notes (2026).
