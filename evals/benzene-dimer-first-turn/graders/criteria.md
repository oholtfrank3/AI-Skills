---
type: llm
weight: 1
---

The reply is the first turn of a conversation with someone who may be new to computational chemistry. Pass only if ALL hold:
- It asks ONE main question (at most two tightly linked ones), in plain language, with 2-3 everyday choices and a 'not sure' option or a suggested default.
- It does NOT list methods (CCSD(T), SAPT, EOM-CC, DFT-D...), costs, basis sets or pitfalls yet.
- It is short (roughly under 120 words).
- It writes no input files and proposes no jobs.
