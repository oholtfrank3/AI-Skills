---
type: llm
weight: 1
---

Score 1 if the answer covers at least 4 of these (a short first answer that offers more detail is fine), else 0:
- Define the two monomers in one molecule block separated by '--', each with its own charge and multiplicity, and no_com/no_reorient (or equivalent) so the geometry is kept.
- Run energy('sapt0') with a suitable basis (e.g. jun-cc-pVDZ), and mention higher levels (sSAPT0, SAPT2+...) for better accuracy.
- Set memory and threads, and point scratch (PSI_SCRATCH) at fast node-local disk on a cluster.
- Compare against published reference values (e.g. S22/S66 benchmark SAPT or CCSD(T)/CBS) before trusting the numbers.
- Explains briefly what each component means in plain words.
