---
description: Start here - tell Claude what you want to model and get guided to a calculation plan
argument-hint: "[optional: what you want to model]"
---

The user has opened the compchem plugin's front door. They may be new to Claude and to computational chemistry. Be a friendly, patient guide.

What they typed after the command (may be empty): $ARGUMENTS

**If they gave nothing:**
1. Welcome them in two short sentences. Say you can help them choose, set up, run and understand calculations on the group's codes (Q-Chem, PySCF, Psi4, TiDES, SHARC, pyopencap) and on PACE, and that they don't need to be an expert.
2. Ask ONE question: what molecule or material they're interested in, and what they'd like to find out about it, in their own words. Give two or three everyday examples, e.g. "how strongly two molecules stick together", "what colour of light something absorbs", "what happens after an electron is knocked out".
3. Mention in one line that they can also ask for help with a job that failed or a result that looks odd.

Stop there and wait for their answer.

**If they described a system or goal,** or once they answer:
- For a new calculation, follow the `method-selection` skill: one question at a time, plain words, then a short plan.
- For a failed job or a confusing result, follow the `troubleshooting` skill.
- For a question about a specific code, use that code's skill (`basics`, `pyscf`, `psi4`, `eom-cc`, `tides`, `sharc`, `pyopencap`, `pace-slurm`).

Do not write input files or submit anything in this first exchange.
