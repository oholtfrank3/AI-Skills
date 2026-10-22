---
type: llm
weight: 1
---

Score 1 if ALL hold, else 0:
- It gives a short, plain explanation and leads with ONE most-likely next step rather than a long list (offering more options is fine).
- Its suggestions are consistent with standard PySCF practice: a better initial guess (e.g. from the neutral molecule's density or a smaller basis / chkfile), level shift or damping, second-order SCF via newton(), and checking the result with a stability analysis.
- It mentions checking that charge and spin are set correctly (PySCF spin = N_alpha - N_beta) or that the converged state is the intended one.
- It does not run or submit anything itself; if it offers to, it asks first.
