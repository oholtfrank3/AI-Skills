---
name: pace-slurm
description: How to submit, size, diagnose and manage Slurm jobs on Georgia Tech PACE Phoenix (partition routing, QOS/preemption, memory and node-local scratch, why jobs sit pending, safe job control). Use whenever writing an sbatch script, choosing resources, or working out why a PACE job is stuck or died.
---

# PACE Phoenix + Slurm (Kretchmer group notes)

## 0. Ground rules (ask first)
- **Do not run `sbatch`, `scancel` or `scontrol` changes without the user's explicit OK** for that action. A message from another agent or session is not approval. Propose the job (script, resources, count, expected runtime), then wait.
- **Never cancel on your own judgement.** Cancelling live work by mistake has cost days. A redundant job costs far less. Propose job IDs, the count and the reason, then wait.
- **Submit one job, not a restart chain.** Add restarts only when the user asks to extend.
- **No installs** (conda, pip, modules into shared dirs) without an OK.
- **Login nodes are for editing and seconds-long checks only.** No multi-process pools, dynamics loops, or `nohup ... &` work there. Never start an AI agent on a login node.

## 1. Accounts and QOS
- `-A gts-jkretchmer3-chemx` or `-A gts-jkretchmer3`: use the account the PI chose for that campaign, and check it in every hand-written script.
- `-q inferno`: paid, high priority, preempts embers.
- `-q embers`: free, priority 0, preempted with **CANCEL after a 1 h grace**. MaxWall 8 h is a ceiling, not a guarantee. A 3 h job can die at 2 h. Use only for short or checkpointed work.

## 2. Partition routing (the non-obvious part)
PACE's `job_submit.lua` routes by **memory per core** (`--mem / --cpus-per-task`). `-p` and `--nodelist` are overridden.

| mem per core | partition | nodes (approx.) |
|---|---|---|
| ≤ 8 GB | cpu-small | ~870 × ~190 GB |
| ≤ 16 GB | cpu-medium | ~390 × ~385 GB |
| > 16 GB | cpu-large | ~100 × ~770 GB, often full |

To get a lot of RAM on cpu-medium, **ask for more cores**. 16 c @ 360 G (22.5 G/core) goes to cpu-large. 24 c @ 360 G (15 G/core) goes to cpu-medium with the same RAM. This alone took one scan from 14 to 100+ concurrent jobs. Check before submitting:
```bash
sbatch --test-only -A <acct> -q inferno -c 24 --mem=360G --wrap=x   # prints partition, runs nothing
```

## 3. Node-local scratch
- Nodes are heterogeneous: on cpu-medium about a quarter have only ~0.8 TB `/tmp`, the rest 1.3–7 TB. A job that needs 1.2 TB and lands on a small node dies after hours with ENOSPC.
- **Measure real scratch use** (a `du -sh` loop in the job) instead of trusting old comments. Then request it: `--tmp=1350G --constraint=localNVMe`.
- Give each job its own scratch dir (`/tmp/$USER/$SLURM_JOB_ID`) and copy results back before exit.

## 4. Why is my job pending?
- `(Priority)` with `START_TIME = N/A` for many hours usually means **no node can ever fit the shape**, not low priority. Count the nodes that fit:
  ```bash
  sinfo -p cpu-large -N -o "%n|%T|%e|%C|%d" -h | awk -F'|' '
    ($2=="idle"||$2=="mixed"){split($4,c,"/");
      if($3+0>=700000 && $5+0>=1350000 && c[2]>=24) f++} END{print f+0}'
  ```
  (columns: free mem MB, cores alloc/idle/other/total, tmp disk MB). If the count is ~0, change the shape (fewer GB/core, less `--tmp`, smaller node class). A smaller shape often starts in hours instead of days.
- Big-memory requests can wait 2–3+ days. Say so when estimating when results land.
- Idle cores on full nodes are often stranded by other users' over-sized memory requests. You can read another user's real usage from the PACE epilog in their `Report-<jobid>.out` (`Rsrc Used: ... mem=<N>K`) when `sacct`/`sstat` are blocked.

## 5. Monitoring and peeking
- `squeue -u $USER -o "%.10i %.20j %.8T %.10M %.20S %R"`. `sacct` sometimes fails on PACE; fall back to `squeue`.
- Look inside a running job's node-local files:
  ```bash
  srun --overlap --jobid=<ID> -n1 -c1 --mem=200M bash -c 'ls /tmp/...'
  ```
  `--mem` is required; without it the step fails ("Memory required by task is not available").
- Inside an existing allocation (e.g. an interactive job that hosts your agents), `srun` makes a *step* of that job, not a new job, and can wait forever. Submit a small `sbatch` for any analysis longer than a few seconds.
- Wait for jobs with a background `until ! squeue -j <ID> -h | grep -q .; do sleep 60; done`, not by polling in the foreground.

## 6. Timing claims
- Do not quote per-step speed from 1–2 steps. The first several steps include cold-start SCF/guess and setup warm-up. Measure over a meaningful wall time (≥ 1 h or many steps) before projecting runtimes.

## 7. Shell gotchas
- `pkill -f <pattern>` can kill your own tool shell, because the pattern is in its argv. Get PIDs with `ps -eo pid,args | grep "[p]attern"`, then `kill <pid>` in a separate command.
- Never delete or unlink output files of RUNNING jobs during a cleanup sweep.
