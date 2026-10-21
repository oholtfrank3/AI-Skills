---
type: llm
weight: 1
---

Score 1 if the answer covers at least 4 of these (a short first answer that offers more detail is fine), else 0:
- Converge a PySCF SCF first, then RT_SCF with timestep and max_time in atomic units.
- Weak delta kick (~1e-4 au), one direction per run (x, y, z), dipole divided by kick strength.
- A linear-regime check (smaller kick) and a time-step check (halve dt).
- Damping exp(-t/tau) and resolution ~2*pi/T; the signal must decay by the end.
- Compare peak positions with PySCF linear-response TDDFT in the same basis/functional.
- Start from the repo's water UV-Vis example; set BLAS thread variables before Python starts.
