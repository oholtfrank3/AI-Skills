---
type: llm
weight: 1
---

Score 1 if the answer says not yet and asks for at least 3 of these checks, else 0:
- An eta trajectory with first-order (deperturbed) corrected energies and a stated stabilization criterion, not a single raw CAP value.
- A channel-closed (null) control, since a CAP-stabilized bound state can also show a plateau.
- Tight Davidson convergence (EOM_DAVIDSON_CONVERGENCE 7 or tighter), since loose convergence changed widths by +20 to +135 %.
- Checking that the channel is open at the correlated level AND checking the in-method 2h1p window (EOM-IP's uncorrelated 2h1p continuum can sit ~1.5 eV too low).
- Basis/ghost functions suited to the outgoing electron.
