---
name: reporting-computational-results
description: Checklist to run BEFORE telling the user any number or conclusion from a calculation, simulation or job. Use for status updates, "how did the runs go", "what did we get", progress reports, results tables, summaries, morning/overnight reports, comparing a model with a benchmark or experiment, claiming something is converged, faster or different, quoting timings or queue estimates, and drafting slides or write-ups. Covers quantum chemistry (EOM-CC, CCSD(T), DFT, CAP), dynamics (surface hopping, AIMD, MD) and any HPC job output.
---

# Before you report a number

Run this checklist before every status update or results message, short ones included. Each item is a mistake that has already happened in our group. The example shows what it looked like.

## 1. Did I check it, or am I remembering it?
Read the number from the output, log or file just before you report it. Do not rely on what you said earlier in the conversation.
> Said a 100-trajectory set ran for 2 ps. It ran for 300 fs; the 2 ps runs were a different set from a week before.

If a job failed, a step was skipped or something is not checked yet, say so plainly.

- **No negatives from a broken look.** If a query errored, came back unexpectedly empty, or the output was truncated, say "could not check" and rerun it. Do not report "none found".
- **Read the method and basis from the input file**, never from a directory or file name.
- **"Running, no crashes" is not "working".** Before saying a run works, compare its first-step (step-0) or absolute energies with a trusted reference.
  > Weeks of dynamics were reported as running fine; the step-0 site energies spread over 3.5 eV where the EOM-CC reference gave at most 0.5 eV.

## 2. Is every number labelled?
Give the source of every value: model (e.g. DIM), ab initio level and basis (EOM-CCSD/d-aug-aQZ), experiment with a reference, **ESTIMATE**, or **PRELIMINARY** (pilot, small n, unconverged). Give units and the zero of energy (vertical/adiabatic, which asymptote). Never quote values the PI has retired.

## 3. Are the two things I'm comparing the same quantity?
Before putting two numbers side by side, check that they have the same state definition (diabatic vs adiabatic, localised vs delocalised), the same geometry, the same reference and the same treatment of basis/counterpoise.
> EOM-DIP was compared with ΔCCSD(T) as "the gap". EOM-DIP sits ~0.2 eV above ΔCCSD by construction.
> A diabatic model energy was compared with a symmetry-broken reference that was only partly localised, and the residual was called "missing polarisation".

## 4. Does the summary actually show the effect?
Means that look alike can hide a sharp threshold. If you claim two groups differ, show binned rates or distributions, and give the threshold.
> A trapped vs not-trapped table of mean forces looked "pretty much the same" to the PI. Binned, the trapping fraction went from 10 % to 90 % across 0.15–0.20 eV/Å.

## 5. Is it a continuous answer forced into a yes/no?
Report the quantity (distance, energy, rate), not a verdict.
> Said an error "decides whether the channel is open". The channel is always open; the error shifts the distance at which it opens.

## 6. Statistics: n, error, and where the spread comes from
- Every fraction gets n and an error bar: `0.51 ± 0.05 (n = 100)`, binomial sqrt(p(1−p)/n). State the category definition (e.g. "trapped = contact weight > 0.5 at 300 fs").
- Deterministic methods (e.g. CSDM) give identical results from identical initial conditions. Spread comes only from distinct seeds or geometries.
- Compare variants paired by seed when you can. When reweighting a biased sample, name the weights.
- Never present one frame, trajectory or geometry as typical without its spread.

## 7. Does the evidence prove what I'm claiming?
- A diagnostic that a known-negative case also passes proves nothing.
  > A flat CAP plateau and a small xi were taken as proof of a width. A channel-closed control state with zero true width passed both tests.
- Before interpreting a new analysis, run it on a case with a known answer (a known null) and check it gets that answer. Do not tune or explain away noise until it matches a published value.
- If your own analysis script says the code is wrong, check the script first, units especially.
  > A gradient was reported as "confirmed unreliable". The diagnostic script had a bohr/Å conversion the wrong way round; the gradient was fine.
- Look up a mechanism in the literature before explaining or arguing for it, and check it against the energy scales: kT at 20 K is about 1.7 meV and cannot close a 0.5 eV gap.
- Report what is robust. If the absolute value depends on settings but a difference or ordering does not (e.g. open vs closed), lead with that.
- Timing: do not quote per-step speed or projected runtime from 1–2 steps (warm-up), and include queue wait when saying when results land.
- Convergence: name the test and give the size of the change ("2× region: −0.02 ± 0.02").

## 8. Is the method published?
Cite a paper for every non-standard choice. No ad hoc fitted terms without precedent; if an existing term is fitted, say so where its results are used. Mark literature claims you have not checked in the paper itself as **UNVERIFIED**.

## 9. Format
- Status table against the deliverables first, then one block per topic: result → evidence → caveat → next step / ETA.
- Full numbers and paths go in the calculation list; keep the message readable.
- If an earlier message was wrong, correct it explicitly ("Earlier I said X; it is Y").
- Drafts only: the researcher writes final write-ups and slides, and nothing is sent on their behalf.

## 10. Working habits
- **Do not reopen a result the user or PI has accepted** unless you have new evidence; say what the evidence is. Figures use the accepted numbers.
- **Do not call a calculation infeasible from wall time alone.** Check the real limits (on PACE, `pace-slurm` §1) and whether it can checkpoint or be split.
- **Ask before deleting anything**, scratch included. Say exactly what would be deleted (paths, size) and wait for a yes for that deletion.
