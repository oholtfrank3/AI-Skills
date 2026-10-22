# AI-Skills

Claude Code skills used by the Kretchmer group, packaged as the `compchem` plugin.

## Install

In Claude Code (2.1.275 or later):

```
/plugin install compchem --marketplace oholtfrank3/AI-Skills
```

Older versions: `/plugin marketplace add oholtfrank3/AI-Skills`, then `/plugin install compchem@kretchmer-ai-skills`.

To use a single skill without the plugin, copy its folder from `skills/` into `~/.claude/skills/`.

## Getting started

New to Claude? Read [GETTING_STARTED.md](GETTING_STARTED.md) first: installing Claude Code, installing this plugin, and connecting to PACE safely.

Type `/compchem:start` and describe what you want to model, or what went wrong, in your own words.

| Command | What it does |
|---|---|
| `/compchem:start` | The front door: Claude asks what you want to model and guides you to a plan. |
| `/compchem:log-calc` | Record a calculation (planned, running, finished, failed) in the project's `CALCULATIONS.md` log. |
| `/compchem:log-fix` | After a problem is solved, save the fix to the group's shared backlog (a GitHub issue). |
| `/compchem:merge-fixes` | For maintainers: fold the reported fixes into the skills. |

**Safety:** the plugin includes a hook that makes Claude ask you before any Slurm command that submits, cancels or changes jobs (`sbatch`, `scancel`, `scontrol update/hold/…`). Read-only commands such as `squeue` and `sbatch --test-only` run without asking.

## Contributing fixes

Solved a problem? Run `/compchem:log-fix` in the session where you fixed it, or open a "Known issue / fix" issue on GitHub. Maintainers merge these into the skills regularly.

## Skills

| Skill | Use it for |
|---|---|
| `method-selection` | Turning "I want to model X in system Y" into a calculation plan: method, benchmarks, cost, known traps. Start here. |
| `basics` | Routine calculations: geometry optimization, frequencies, choosing a functional and basis, interaction energies and counterpoise. |
| `pyscf` | PySCF scripts: SCF/DFT convergence, spin and charge, CASSCF, geometry optimization, performance on PACE. |
| `psi4` | Psi4: SAPT energy decomposition, counterpoise and n-body, CBS extrapolation, running on PACE. |
| `eom-cc` | EOM-CCSD EE / IP / DIP and CAP-EOM in Q-Chem and PySCF. |
| `sharc` | Surface hopping, Ehrenfest and CSDM dynamics in SHARC: settings, energy conservation, restarts, ensembles on PACE. |
| `tides` | Real-time TDDFT, hole dynamics and Ehrenfest runs in TiDES: spectra, restarts, known bugs, PACE. |
| `pyopencap` | Projected CAP widths with OpenCAP/pyopencap: setup from Q-Chem, pitfalls, and where it has not worked. |
| `troubleshooting` | When something fails or is unfamiliar: search docs, forums and literature first. Per-code doc links, starter test calculations and known issues. |
| `pace-slurm` | Submitting and diagnosing jobs on PACE Phoenix. |
| `reporting-computational-results` | A checklist Claude runs before telling you any number or conclusion from a calculation: status updates, results tables, convergence and comparison claims. |
| `scientific-plot-style` | Group figure style (matplotlib). |
| `blender-molecular-rendering` | Publication renders of molecules and clusters in Blender. |

## Checker scripts

`scripts/check_qchem_output.py` checks that a Q-Chem job really finished (the "Thank you very much" line plus a clean `.err`) and that the requested EOM roots are all there, flagging satellites and unconverged roots. `scripts/check_sharc_lis.py` checks SHARC energy drift against the kinetic energy and flags jumps.

`scripts/check_qchem_input.py` and `scripts/check_sbatch.py` catch mistakes that have already cost the group jobs: incomplete mixed-basis lists, loose Davidson convergence for CAP, scratch on shared storage, missing accounts, embers preemption and partition routing. Claude runs them before proposing a job, and you can run them yourself: `python3 scripts/check_sbatch.py job.sbatch`.

Planned: more codes the group uses (e.g. OpenMolcas/CASSCF), contributed by the people who run them.

## Testing the plugin

`evals/` holds test questions with grading checklists. Run `claude plugin eval . --runs 3` from the repo root to compare answers with and without the plugin. Run it after editing a skill.
