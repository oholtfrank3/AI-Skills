# PACE / Slurm details (group observations)

Back-up detail for `pace-slurm/SKILL.md`. Numbers come from the group's 2026 CAP-EOM-CCSD campaigns on Phoenix; re-measure for your own jobs. Every `scontrol` change still needs the user's OK first (SKILL §0).

## 1. Changing a job after submission
- **Running jobs:** users cannot raise `TimeLimit` (Slurm refuses it for non-operators), and `--tmp` cannot be changed. The only route is cancel and resubmit, which loses the queue age. Ask first.
- **Pending jobs** can be edited in place and keep their job ID and queue position:
  ```bash
  scontrol update jobid=<ID> TimeLimit=20:00:00
  scontrol update jobid=<ID> MinMemoryNode=368640            # MB (= 360G)
  scontrol update jobid=<ID> MinTmpDiskNode=1024000          # MB; shows as 1000G
  scontrol update jobid=<ID> Features=localNVMe
  ```
  Give `MinTmpDiskNode` in MB (`MinTmpDiskNode=1000` means 1000 MB, not 1000 GB). That a `G` suffix is rejected is a group observation, unverified.
- **Do not change the core count in place.** `scontrol update NumCPUs=24` left `MinCPUsNode` and CPUs-per-task out of step, and the jobs showed `BadConstraints`. Cancel and resubmit from a corrected script.
- Applying `Features=localNVMe` only affects where pending jobs start; Slurm does not move running jobs.

## 2. Diagnosing exit 134 / `double free or corruption`
Signature: `libxm: xm_allocator_write: pwrite` (repeated) then `double free or corruption (!prev)`, exit 134, often at the same elapsed time across jobs. The double free is a downstream symptom of a failed scratch write.

```bash
grep -c xm_allocator_write */*.err                          # write failures? -> disk, not chemistry
squeue -u $USER -h -t RUNNING -o '%N' | sort | uniq -c | awk '$1>1'   # two jobs sharing a node?
sacct -u $USER -X -o JobName%20,State,Elapsed,ExitCode     # same Elapsed across jobs = shared resource
```
- In the group's case a 357-job batch without `-save` (24 cores, whole cpu-medium node) all converged, while a 152-job batch with `-save` (16 cores, routed to cpu-large where two jobs packed per node) lost 46. Jobs on the same node died within a second of each other.
- `-save` keeps the whole scratch directory, so use grows until the disk is full. Pass it only to the jobs that need the saved files. If you use it, do not delete scratch in a `trap` (see `eom-cc` §6).
- Per-job scratch paths prevent name collisions but do not add disk space.
- Before acting on a plausible mechanism, run a control that changes one thing. This failure was blamed on linear dependence, CAP-wall placement, ghost overlap and a scratch-path collision before the control found it.

## 3. Node classes and scratch sizes (cpu-medium, 2026)
- `localNVMe` nodes: about 1.36 TB and 1.66 TB of `/tmp`. `localSAS` nodes: up to 7.6 TB but slow under heavy random I/O (81 % vs 7 % timeouts for the same CAP-EOM jobs, same CPUs).
- Requests above about 1350–1400G never started for the group: the 1.6–1.7 TB nodes appear in `sinfo` and pass `--test-only` but were never allocated to this account (group observation; may be account-specific). If a job needs more scratch than that, give the program more memory so it spills less.

## 4. More shell and scripting traps
- **`conda run` buffers stdout**, even with `python -u`, and nested `conda run` lost a script's prints entirely. Use `conda activate <env>` then `python -u`, or `conda run --no-capture-output`.
- **Bash reads `08` and `09` as invalid octal** in arithmetic (`$((08))` fails). Strip leading zeros (`$((10#$x))`).
- **Parsing the PACE epilog:** a regex like `mem=[0-9]+` matches inside `vmem=0` first and returns 0. Anchor on `,mem=`.
- **`squeue` time formats** are `MM:SS` under an hour and `D-HH:MM:SS` above a day; convert to seconds before sorting or comparing, never sort the text.
- **Do not use the agent session's own local `/tmp` scratch folder as a Slurm working directory.** It exists only on the machine the session runs on, so the job cannot see it. Use project storage.
- **A watcher that reads job IDs from a file** silently tracked the wrong jobs after the file vanished on a session restart (an empty `-j ""` falls back to defaults). Check the ID list is non-empty.
- **Big files:** read multi-GB outputs (`.fchk`, transition-density files) inside a batch job with enough `--mem`, never on the login node.
