---
type: llm
weight: 1
---

Score 1 if the answer covers at least 5 of these, else 0:
- Use standalone sharc.x with a file-based QM.in/QM.out interface, because pysharc does not support method scp / CSDM.
- Keywords: method scp, switching_procedure csdm, decoherence_scheme dom, decotime_method csdm.
- decoherence_param_alpha is E0 in Hartree (0.1) and decoherence_param_beta is C (1, dimensionless); do not tune them.
- Use overlap coupling / phase tracking for the dense manifold; never follow states by energy ranking.
- Stock SHARC's coherence force is wrong in dense bands with overlap coupling; patch it or compute the exact force in the interface; check energy drift against relevant energy scales.
- Report wavefunction populations, not active/pointer-state fractions.
- Validate on a small system against an exact wavepacket first, and submit one trajectory before the batch.
