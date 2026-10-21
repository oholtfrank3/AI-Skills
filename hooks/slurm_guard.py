#!/usr/bin/env python3
"""PreToolUse hook: make Claude ask the user before any Slurm command that
submits, cancels or changes jobs (pace-slurm skill §0). Read-only commands
(squeue, sacct, sinfo, `sbatch --test-only`) pass through untouched."""
import json
import re
import sys

RISKY = re.compile(
    r"(?<![\w-])("
    r"sbatch(?![^;&|\n]*--test-only)"
    r"|scancel"
    r"|scontrol\s+(update|hold|release|requeue|requeuehold|suspend|resume|top|delete)"
    r")(?![\w-])"
)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if data.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command", "")
m = RISKY.search(cmd)
if not m:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": (
            f"compchem safety check: this runs `{m.group(1).split()[0]}`, which "
            "submits, cancels or changes cluster jobs. Check the job script, "
            "resources and job IDs before approving."
        ),
    }
}))
