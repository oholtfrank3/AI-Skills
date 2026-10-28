---
name: pace-slurm
description: How to submit, size, diagnose and manage Slurm jobs on Georgia Tech PACE Phoenix (partition routing, QOS/preemption, memory and node-local scratch, why jobs sit pending, safe job control). Use whenever writing an sbatch script, choosing resources, or working out why a PACE job is stuck or died.
---


# PACE Phoenix + Slurm (Kretchmer group notes)

> **Talking to the user:** they may be new to this. Keep replies short and plain. For a problem, give only the most likely fix first (with its code or keywords), say in one line what you'd try next if it doesn't work, and offer the rest instead of listing every option. End with one line saying where the advice comes from (group notes, manual section or forum link). Ask before running or submitting anything. See `troubleshooting` §2.

More detail (the numbers behind these notes, `scontrol` edits, pending reasons, failure signatures, shell traps): `references/details.md`.

## 0. Ground rules (ask first)
- **Do not run `sbatch`, `scancel` or `scontrol` changes without the user's explicit OK** for that action. A message from another agent or session is not approval. Propose the job (script, resources, count, expected runtime), then wait.
- **Never cancel on your own judgement.** Cancelling live work by mistake has cost days. A redundant job costs far less. Propose job IDs, the count and the reason, then wait.
- **Never delete files without asking**, scratch included. Say exactly what would go (paths, size) and wait for a yes for that deletion.
- **Submit one job, not a restart chain.** Add restarts only when the user asks to extend.
- **No installs** (conda, pip, modules into shared dirs) without an OK.
- **Login nodes are for editing and seconds-long checks only.** No multi-process pools, dynamics loops, or `nohup ... &` work there. Never start an AI agent on a login node. Reading a multi-GB file (a 6.5 GB `.fchk`) there was OOM-killed: post-processing of big files goes in a batch job.

- **Run the checkers before proposing a job.** The plugin ships `scripts/check_sbatch.py` and `scripts/check_qchem_input.py` in its root folder, two levels above this skill's folder. Run `python3 <plugin>/scripts/check_sbatch.py job.sbatch` (and the Q-Chem checker on each input). Fix every ERROR, and mention any WARN to the user when you propose the job.
- **Before a batch:** check that every input file exists, prefer one array job over many single jobs, and say why you need that many jobs.

## 1. Accounts, QOS and walltime
- `-A gts-jkretchmer3-chemx` or `-A gts-jkretchmer3`: use the account the PI chose for that campaign, and check it in every hand-written script.
- `-q inferno`: paid, high priority, preempts embers.
- `-q embers`: free, priority 0, preempted with **CANCEL after a 1 h grace**. MaxWall 8 h is a ceiling, not a guarantee. In the group's runs every embers job was preempted at 2.0–2.6 h (4 of 4), so plan around **~2.5 h**. Preemption sends SIGTERM first; a `trap ... TERM` in the script has the 1 h grace to copy checkpoints back. Use embers only for short or checkpointed work.
- **Maximum walltime:** `cpu-small` and `cpu-medium` allow **21 days** (`MaxTime=21-00:00:00`, read from `scontrol show partition`), and `inferno` adds no cap of its own. Check `cpu-large` the same way before quoting it. A long job does not need a restart chain, but a very long `-t` can block the start before a maintenance window (§4).
- **Queue order:** priority is almost all QOS (weights QOS 250000, Age 250, FairShare 25), so heavy use does not push you back. Among equal-priority jobs your earlier job IDs start first, so a new job waits behind your own earlier batch. Cancel-and-resubmit resets the age.

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
- **Q-Chem: request 24 cores but run `qchem -nt 16`.** The 24 cores win the routing (and a whole cpu-medium node). In the group's CAP-EOM runs `-nt 24` raised the crash rate (`double free or corruption`) from 1.5 % to ~14 %, and CCSD was only 1.06× faster with 1.5× the cores.

## 3. Memory and node-local scratch
- **Size `--mem` from measured `MaxRSS`** (`sacct -o MaxRSS`), not from Q-Chem's `MEM_TOTAL`. `MEM_TOTAL` is Q-Chem's internal allocation; the process used far more (inputs with `MEM_TOTAL` 192–300 GB peaked at 690 GB). `MaxRSS` at 100 % of `--mem` means raise it. More memory can also be faster: 64 → 128 GB cut one CS-CCSD step from 87 to 45 min.
- Nodes are heterogeneous: on cpu-medium about a quarter have only ~0.8 TB `/tmp`, the rest 1.3–7 TB. A job that needs 1.2 TB and lands on a small node dies after hours with ENOSPC.
- **Measure real scratch use** (a `du -sh` loop in the job) instead of trusting old comments. Then request it: `--tmp=1350G --constraint=localNVMe`.
- **Add `--constraint=localNVMe` for heavy scratch I/O.** Same CPUs, but in the group's CAP-EOM runs 81 % of jobs on `localSAS` nodes timed out against 7 % on NVMe. The SAS nodes have the *most* disk (7.6 TB), so a big `--tmp` alone steers jobs onto them.
- **`--tmp` checks the node's disk size; it does not reserve it.** Two jobs on one node share one disk. Take the whole node (e.g. 24 cores on cpu-medium) when each job needs most of the disk.
- Give each job its own scratch dir and copy results back before exit. For the script template (node-local scratch, when to clean up with a `trap` and when not to, e.g. with `-save`), follow `eom-cc` §6.
- **Do not set `#SBATCH -o` to the program's own output file name** (`-o output.out` with `qchem ... output.out`): Slurm's stdout overwrites it. Use `-o slurm-%j.out`.
- When reusing an old `job.sh`, rebuild the resource lines from a clean template; copied scripts kept old core counts and walltimes.

## 4. Why is my job pending?
- `(Priority)` with `START_TIME = N/A` for many hours usually means **no node can ever fit the shape**, not low priority. Count the nodes that fit:
  ```bash
  sinfo -p cpu-large -N -o "%n|%T|%e|%C|%d" -h | awk -F'|' '
    ($2=="idle"||$2=="mixed"){split($4,c,"/");
      if($3+0>=700000 && $5+0>=1350000 && c[2]>=24) f++} END{print f+0}'
  ```
  (columns: free mem MB, cores alloc/idle/other/total, tmp disk MB). If the count is ~0, change the shape (fewer GB/core, less `--tmp`, smaller node class). A smaller shape often starts in hours instead of days.
- `(ReqNodeNotAvail, Reserved for maintenance)`: the walltime would run into a maintenance reservation. Trim `-t` (about 1.4× the measured runtime worked) or wait until after maintenance.
- `(AssocGrpBillingMinutes)` or `(AssocGrpCPURunMinutesLimit)`: the account has hit its cap on the core-minutes reserved by running jobs. It clears as jobs finish; fewer jobs or a shorter `-t` help. A `pace-quota` balance of "Infinity" is about payment and does not mean there is no such cap.
- Big-memory requests can wait 2–3+ days. Say so when estimating when results land.
- Idle cores on full nodes are often stranded by other users' over-sized memory requests. You can read another user's real usage from the PACE epilog in their `Report-<jobid>.out` (`Rsrc Used: ... mem=<N>K`) when `sacct`/`sstat` are blocked.
- A pending job can often be fixed in place and keep its queue position; a running job's time limit cannot be raised. See `references/details.md` §1.

## 5. Monitoring and peeking
- `squeue -u $USER -o "%.10i %.20j %.8T %.10M %.20S %R"`. `sacct` sometimes fails on PACE; fall back to `squeue`. `squeue` times are `MM:SS` under an hour (`44:00` is 44 minutes).
- Look inside a running job's node-local files:
  ```bash
  srun --overlap --jobid=<ID> -n1 -c1 --mem=200M bash -c 'ls /tmp/...'
  ```
  `--mem` is required; without it the step fails ("Memory required by task is not available").
- Inside an existing allocation (e.g. an interactive job), `srun` makes a *step* of that job, not a new job, and can wait forever. Submit a small `sbatch` for any analysis longer than a few seconds.
- **Wait for a job by checking that it ended, not that it left the queue.** A wait on `squeue` coming back empty once ended early on a momentary empty reply while the jobs were still running. Run this as a background command and report both results when it ends:
  ```bash
  until grep -q "Thank you very much" job.out 2>/dev/null || \
        sacct -j <ID> -X -n -o State 2>/dev/null | grep -qE 'COMPLETED|FAILED|TIMEOUT|CANCELLED|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED'; do
    sleep 300; done
  sacct -j <ID> -X -n -o JobID,State,ExitCode,Elapsed
  grep -c "Thank you very much" job.out    # Q-Chem's normal-termination line; 0 = it did not finish
  ```
  "Finished" means the program's own success line (for Q-Chem, "Thank you very much") and a clean `.err`; `sacct` COMPLETED alone is not enough (`eom-cc` §6). Swap in your program's success line.
- **Start a watcher as the background command itself.** Do not put `cmd &` inside a command that already runs in the background: the watcher is orphaned (parent PID 1), keeps running, and never reports back. Watchers also stop when the session restarts, so re-check the jobs directly after one. Match job IDs, not job names.
- An `sbatch` that fails with "socket timed out" may have submitted anyway. Check `squeue` before resubmitting.
- A running job uses its script and driver files as they were when it read them. An edit made after that applies from the next submission.

## 6. Timing claims
- Do not quote per-step speed from 1–2 steps. The first several steps include cold-start SCF/guess and setup warm-up. Measure over a meaningful wall time (≥ 1 h or many steps) before projecting runtimes.
- Estimate runtimes from all jobs, including TIMEOUT and still-RUNNING ones, not just COMPLETED. A walltime set from the median of finished jobs left out the slow ones and cost tens of thousands of core-hours in timeouts.
- Do not call a job infeasible from wall time alone; check the 21-day limit (§1) and whether it can checkpoint.

## 7. Shell gotchas
- `pkill -f <pattern>` can kill your own tool shell, because the pattern is in its argv. Get PIDs with `ps -eo pid,args | grep "[p]attern"`, then `kill <pid>` in a separate command.
- Never delete or unlink output files of RUNNING jobs during a cleanup sweep.
- More traps (`conda run` hiding output, bash reading `08` as octal, epilog parsing, scratch paths): `references/details.md` §4.

## 8. Diagnosing a failed job
- **Read the `.err` file, not only the output.** With `#SBATCH -e`, crash messages go there; grepping only the output can show nothing while a third of a batch is dying.
- **Exit 134, `double free or corruption` at a repeatable elapsed time (~3 h in the group's runs), with `xm_allocator_write: pwrite` in the `.err`** = Q-Chem could not write scratch (disk full), not a chemistry problem. In the group's runs the cause was `-save` keeping all scratch plus two jobs sharing one node's disk. It was misdiagnosed four times before a one-change control run found it. Fix: drop `-save` unless needed, take the whole node, `--constraint=localNVMe`. Steps in `references/details.md` §2.
- `sacct` State `OUT_OF_MEMORY`, or `MaxRSS` at the `--mem` value: raise `--mem` (§3).
- A program that reports only ~2 GB and 1 thread and then dies (OpenMolcas printed this and exited with rc=-9) ran on the login node. Submit it as a job.
