---
description: Record a calculation (planned, submitted, finished or failed) in the project's CALCULATIONS.md log
argument-hint: "[optional: which calculation, e.g. 'the water EOM-IP job']"
---

Keep a running log of the project's calculations in `CALCULATIONS.md`, in the project folder (the current folder, unless the user keeps the log elsewhere). This is the group's habit: anyone, including a future Claude session, should be able to see what was run, with which settings, where the files are, and what came out. Extra text from the user (may be empty): $ARGUMENTS

1. **Find or create the log.** If `CALCULATIONS.md` (or the project's existing log, e.g. `CALCULATIONS_LIST*.md`) exists, read its conventions and follow them. If not, create it with this header and tell the user in one line:
   ```markdown
   # <Project name>: calculations log
   **Conventions:** energies in eV unless stated; times in local time; "superseded" entries stay, struck through, with the reason.
   Last updated <date>.

   ## Contents
   ```
   Add a section per topic (e.g. "Benchmarks", "Production", "Failed / superseded") as entries appear.

2. **Write one entry per calculation or batch,** from what actually happened in this session. Check the files and outputs; never fill a field from memory or guesswork:
   ```markdown
   ### <short name> — <status: planned | submitted | running | finished | failed | superseded>  (<date>)
   - **Question:** what this calculation answers, in one line.
   - **System / method:** e.g. H₂O, EOM-IP-CCSD/aug-cc-pVTZ, Q-Chem 6.3.1.
   - **Key settings:** the few that matter (states, convergence, CAP eta range, timestep, cutoff…).
   - **Where:** cluster path of inputs/outputs; job ID(s); resources (cores, memory, walltime, core-h used).
   - **Result:** numbers with units and level of theory; or the failure and its cause.
   - **Checks:** what was verified (e.g. `check_qchem_output.py` OK, roots 30/30, drift 0.13 % of Ekin, compared with <reference>).
   - **Next / open:** what this changes or what still needs doing.
   ```
   For a finished job, run the matching checker first (`scripts/check_qchem_output.py`, `scripts/check_sharc_lis.py`) and record its verdict. Report numbers following `reporting-computational-results`.

3. **Update, don't duplicate.** When a submitted job finishes or fails, update its existing entry (status, result, checks) instead of adding a new one. When a result is replaced, mark the old entry superseded and say why.

4. **Update the "Last updated" line,** then show the user the new or changed entry in a few lines. Do not commit or share the log unless they ask.
