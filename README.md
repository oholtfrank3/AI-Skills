# AI-Skills

Claude Code skills used by the Kretchmer group, packaged as the `compchem` plugin.

## Install

In Claude Code (2.1.275 or later):

```
/plugin install compchem --marketplace oholtfrank3/AI-Skills
```

Older versions: `/plugin marketplace add oholtfrank3/AI-Skills`, then `/plugin install compchem@kretchmer-ai-skills`.

To use a single skill without the plugin, copy its folder from `skills/` into `~/.claude/skills/`.

## Skills

| Skill | Use it for |
|---|---|
| `method-selection` | Turning "I want to model X in system Y" into a calculation plan: method, benchmarks, cost, known traps. Start here. |
| `eom-cc` | EOM-CCSD EE / IP / DIP and CAP-EOM in Q-Chem and PySCF. |
| `pace-slurm` | Submitting and diagnosing jobs on PACE Phoenix. |
| `reporting-computational-results` | Reporting numbers to a PI or in a write-up. |
| `scientific-plot-style` | Group figure style (matplotlib). |
| `blender-molecular-rendering` | Publication renders of molecules and clusters in Blender. |

Planned: `tides`, `pyopencap`, `sharc`, plus a planner agent and input-checking scripts.
