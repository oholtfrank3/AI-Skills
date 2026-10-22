#!/usr/bin/env python3
"""Check a Slurm batch script for PACE Phoenix pitfalls (pace-slurm skill).

Usage: python3 check_sbatch.py job.sbatch [more.sbatch ...]
Exit code 1 if any ERROR was found. Reads #SBATCH lines and the script body;
it does not contact Slurm. For partition routing, also run
`sbatch --test-only ...` on PACE.
"""
import re
import sys


def parse_mem_gb(s):
    m = re.match(r"^(\d+(?:\.\d+)?)([KMGT]?)B?$", s.strip(), re.I)
    if not m:
        return None
    v, u = float(m.group(1)), m.group(2).upper() or "M"
    return v * {"K": 1 / 1048576, "M": 1 / 1024, "G": 1, "T": 1024}[u]


def parse_time_h(s):
    s = s.strip()
    d = 0
    if "-" in s:
        d, s = s.split("-", 1)
        d = int(d)
    parts = [int(p) for p in s.split(":") if p.isdigit()]
    if not parts:
        return None
    if len(parts) == 1:
        h = parts[0] / 60 if d == 0 else parts[0]  # "MM" alone, or "D-HH"
    elif len(parts) == 2:
        h = parts[0] / 60 + parts[1] / 3600 if d == 0 else parts[0] + parts[1] / 60
    else:
        h = parts[0] + parts[1] / 60 + parts[2] / 3600
    return d * 24 + h


def opts(text):
    o = {}
    for line in text.splitlines():
        if not line.startswith("#SBATCH"):
            continue
        for tok in re.findall(r"(--?[\w-]+)(?:[ =]([^\s]+))?", line[7:]):
            key, v = tok
            o[{"-A": "--account", "-q": "--qos", "-c": "--cpus-per-task", "-t": "--time",
               "-p": "--partition", "-N": "--nodes", "-n": "--ntasks", "-C": "--constraint"}.get(key, key)] = v
    return o


def check(path):
    text = open(path, errors="replace").read()
    o = opts(text)
    body = "\n".join(l for l in text.splitlines() if not l.startswith("#"))
    found = []
    add = lambda lvl, msg, ref: found.append((lvl, msg, ref))

    if "--account" not in o:
        add("ERROR", "no -A/--account: use the account the PI chose for this campaign", "pace-slurm §1")
    qos = o.get("--qos", "")
    t = parse_time_h(o["--time"]) if "--time" in o else None
    if "--time" not in o:
        add("WARN", "no -t/--time: the default walltime may be far too short or too long", "pace-slurm")
    if qos == "embers" and t and t > 1:
        add("WARN", f"embers QOS with {t:.1f} h walltime: embers jobs can be preempted (cancelled after a "
                    "1 h grace), so use it only for short or checkpointed work", "pace-slurm §1")

    cpus = int(o.get("--cpus-per-task") or 1)
    mem = parse_mem_gb(o["--mem"]) if o.get("--mem") else None
    if mem:
        per = mem / cpus
        part = "cpu-small" if per <= 8 else "cpu-medium" if per <= 16 else "cpu-large"
        add("INFO", f"{mem:.0f} GB over {cpus} cores = {per:.1f} GB/core -> routed to {part}", "pace-slurm §2")
        if part == "cpu-large":
            add("WARN", "cpu-large nodes are few and often full; more cores at <= 16 GB/core lands on "
                        "cpu-medium with the same RAM", "pace-slurm §2")
    if "--partition" in o:
        add("INFO", "-p/--partition is overridden on PACE: routing is by memory per core", "pace-slurm §2")

    uses_qchem = re.search(r"\bqchem\b", body) is not None
    if uses_qchem:
        if not re.search(r"QCSCRATCH=\S*(SLURM_JOB_ID|SLURM_JOBID)", body):
            add("ERROR", "Q-Chem job without a per-job QCSCRATCH (e.g. /tmp/$USER/$SLURM_JOB_ID): scratch "
                         "collisions and full shared storage have killed jobs", "eom-cc §6, pace-slurm §3")
        if re.search(r"QCSCRATCH=\S*(/storage|/project|~/|\$HOME)", body):
            add("WARN", "QCSCRATCH on shared storage: libxm is I/O-bound and filled shared scratch; use "
                        "node-local /tmp", "pyopencap §2")
        if "--tmp" not in o:
            add("WARN", "Q-Chem job without --tmp: large EOM/CAP jobs need TB of node-local disk "
                        "(--tmp=... --constraint=localNVMe); measure real use", "pace-slurm §3")
    if re.search(r"--export[ =][^\n]*=[^\n,]*,", text):
        add("WARN", "--export value containing a comma: Slurm splits it at the comma", "sharc §8")
    if re.search(r"\bsbatch\b.*--dependency", body):
        add("INFO", "the script submits a follow-up job (restart chain): the group submits one job and "
                    "extends only on request", "pace-slurm §0")
    return found


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    bad = False
    for path in argv[1:]:
        try:
            found = check(path)
        except OSError as e:
            print(f"{path}: cannot read ({e})")
            bad = True
            continue
        if not any(l != "INFO" for l, _, _ in found):
            print(f"{path}: OK (no known problems found)")
        for level, msg, ref in found:
            print(f"{path}: {level}: {msg}  [{ref}]")
            bad |= level == "ERROR"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
