---
type: llm
weight: 1
---

Score 1 if, anywhere in the reply (including options it offers for later), it gives at least 3 of these standard PySCF remedies, else 0:
- a better initial guess (neutral-molecule density, smaller basis, or a chkfile);
- level shift or damping;
- second-order SCF via newton();
- a stability analysis of the converged result.
