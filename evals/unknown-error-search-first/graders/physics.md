---
type: llm
weight: 1
---

Score 1 if the advice is consistent with known causes and fixes, and mentions at least 2 of: near-degenerate roots stalling the Davidson solver; more guesses or more roots than needed; user guesses or separating states by symmetry; per-irrep root counts; more iterations or subspace / tighter convergence; checking for satellites (small R1^2). Score 0 if it recommends something wrong, such as forcing convergence flags or splitting Davidson restarts into chunks.
