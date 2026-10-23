# Changelog

## Unreleased

- All skills: end advice with one line saying where it comes from (group notes, manual or forum link).
- `troubleshooting` §2 and `eom-cc` §2: ordered fix lists are for Claude; the user gets the first step that fits (with an example for missing EOM roots).
- `psi4`: SAPT answers explain each term in plain words and suggest checking against published values.
- Evals: the unknown-error case has separate sources/physics/tone graders.
- `pyscf`: the first reply to an SCF problem gives one fix with a short snippet, then offers the rest (eval tone check went from 0/3 to 2/3).
- Evals: the PySCF case has three separate graders (tone, physics, spin), so a failure shows which part missed.
- `tests/`: smoke tests for the checker scripts and the Slurm safety hook. GitHub CI (`.github/workflows/check.yml`) runs them and `claude plugin validate` on every push.

## 0.2.0 (2026-10-22)

First version for group use.

**Start here:** `/compchem:start` asks what you want to model, one question at a time, and writes a short plan with sources. New to Claude? See `GETTING_STARTED.md`.

**Skills**
- `method-selection`: turns a plain-language question into a method and a benchmark-first plan.
- `basics`: optimization, frequencies, choice of functional and basis, interaction energies.
- Code skills: `eom-cc` (Q-Chem/PySCF EOM-CC, CAP), `pyscf`, `psi4`, `cp2k`, `tides`, `sharc`, `pyopencap`, plus `pace-slurm`.
- `troubleshooting`: search the docs, then forums and issues, then the literature, before guessing. Reference files for Q-Chem/PySCF EOM-CC and CAP, PySCF, Psi4, CP2K, pyopencap, SHARC and TiDES, each with starter calculations and known issues.
- `reporting-computational-results`, `scientific-plot-style`, `blender-molecular-rendering`.

**Commands**
- `/compchem:log-calc`: keep a `CALCULATIONS.md` log for each project.
- `/compchem:log-fix`: save a solved problem to the shared backlog (GitHub issues labelled `known-issue`).
- `/compchem:merge-fixes` and `/compchem:refresh-references`, for maintainers.

**Safety and checks**
- A hook asks you before Claude runs `sbatch`, `scancel` or `scontrol update/hold/...`.
- `scripts/`: checkers for Q-Chem inputs and outputs, sbatch scripts and SHARC energy conservation.

**Tests:** `evals/` has 8 cases. Run `claude plugin eval . --runs 3`.

## 0.1.0 (2026-10-20)

Skills packaged as a plugin. First `method-selection`.
