---
type: llm
weight: 1
---

This is a first reply to a newcomer, so it need not cover everything. Score 1 if the answer gets at least 3 of these right and states none of them wrongly, else 0:
- Basis of one hole state per atom (or three per atom plus spin-orbit for a p hole, which a valence Kr⁺ hole is), built from Kr₂⁺ dimer potential curves.
- The hopping between atoms comes from the splitting of the ion-dimer (Kr₂⁺) curves (mentioning its sign is a plus, not required).
- Polarization of the neutral atoms by the charge treated as many-body (self-consistent induced dipoles), not just pairwise, without double counting the induction already in the pair curves.
- Validation against ab initio (EOM-IP-CCSD or similar) on small clusters, ideally blind, plus numerical checks (dimer limit reproduces the curves, gradients vs finite differences).
- Dynamics with a mixed quantum-classical method (e.g. CSDM or surface hopping), reporting wavefunction populations, with care about the finite hole region / edges.
