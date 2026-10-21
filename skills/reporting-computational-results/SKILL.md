---
name: reporting-computational-results
description: Rules for reporting numbers from quantum-chemistry and dynamics calculations to a PI or in a write-up (level-of-theory labels, like-for-like comparisons, statistics, convergence evidence, honest status). Use whenever summarising results, writing a status update or report, building a results table, or comparing a model to a benchmark or experiment.
---

# Reporting computational results (Kretchmer group notes)

The goal: a reader can tell from each number **what produced it, how sure we are, and what it is being compared to**, without asking.

## 1. Label every number
- Tag each value with its source: **model** (e.g. DIM), **ab initio level** (EOM-CCSD/d-aug-aQZ, CCSD(T)/CBS), **experiment** (with the reference), **ESTIMATE** (back-of-envelope), **PRELIMINARY** (small n, unconverged, pilot).
- Give units and the reference zero (vertical vs adiabatic, relative to which asymptote).
- Do not quote a number the PI has retired. Keep a short list of retired values in the project notes.

## 2. Compare like with like
- Before putting two numbers side by side, check that they are **the same quantity**: same geometry, same state (diabatic vs adiabatic, vertical vs relaxed), same reference energy, same basis or counterpoise treatment. If not, say what differs, or don't compare.
- Compare runs **paired by seed or initial condition** when you can (e.g. the same 100 initial conditions in two box sizes). Paired differences have much smaller error than two independent fractions.
- When reweighting (e.g. from an orientation-biased sample to the full distribution), say what the weights are and give the result for each weight set if they differ.

## 3. Statistics
- Every fraction or average gets an error bar **and n**: `0.51 ± 0.05 (n = 100)`. For fractions use the binomial error sqrt(p(1−p)/n).
- Deterministic methods (e.g. CSDM from identical initial conditions) give no statistics from repeats. Statistics come only from distinct initial conditions. Say so.
- Never quote a single frame, single trajectory or single geometry as typical without its spread.
- If a "clear difference" between groups is claimed, show it: binned rates or a distribution plot, not just two means that look similar.
- State the cut or definition used for categories (e.g. "trapped = contact weight > 0.5 at 300 fs").

## 4. Convergence evidence
- For each production setting, report the test that shows it is converged (region size, basis, timestep, number of roots), with the size of the change: "2× region changes the trapped fraction by −0.02 ± 0.02".
- When something is not converged, say by how much and in which direction (e.g. "3d/5s 0.3–0.6 eV high vs experiment").
- Prefer continuous quantities to binary verdicts. Report a threshold *distance* or *energy* (e.g. "channel opens at ≥ 8.3 Å"), not "open/closed".

## 5. Methods: literature first, no ad hoc fits
- Methods should follow published, preferably fit-free, approaches. Cite the paper for every non-standard choice (basis exponents, CAP analysis, model terms).
- Do not add fitted correction terms without precedent. If an existing term is fitted, say so where its results are used.
- If a literature claim has not been checked against the paper itself, mark it **UNVERIFIED**.

## 6. Honest status
- Report outcomes faithfully. Failed jobs, skipped steps and things not yet checked get stated plainly, with the reason.
- Don't overclaim. Separate "what the data show" from "interpretation" and from "next test that would decide it".
- Say what is running, when it is expected to land (including queue wait), and what result would change the conclusion.
- Correct earlier mistakes explicitly in the next report ("Earlier I said X; it is Y because Z").

## 7. Format
- Lead with a short status table against the deliverables (status, risk), then one section per line of work: result → evidence → caveat → next step.
- Put full numbers and file paths in a separate calculation list. Keep the report readable.
- Figures: one message per figure (what to look at), axes with units, colour-blind-safe palette, n on the figure.
- Drafts only: the researcher writes the final write-ups and slides. Never send them on their behalf.
